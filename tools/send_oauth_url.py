"""
Send an OAuth authorization link to the user via the current session's channel.

The URL is computed by ``tools.gws_auth.get_auth_url()`` (server-side) and
delivered through the right primitive for the current channel:

  * **Telegram** — inline-keyboard button (URL carried byte-for-byte)
  * **CLI**      — printed to stderr between banner separators
  * **Open WebUI / default markdown** — returned as a markdown link in JSON
                                      with an explicit "use as-is" instruction
  * **Anything else** — returned as a markdown link in JSON

The LLM never sees or constructs the URL. The tool's return value is a
status object (success, message_id, delivery channel) — no secrets, no URLs,
no client_ids. The LLM describes the action in prose and references the
button/link by its delivery channel.

Why this exists
---------------
Small/fast LLMs (e.g. deepseek-v4-flash) silently truncate long, structured
URLs when transcribing them into chat prose — e.g. dropping ``google.`` from
``apps.googleusercontent.com`` — and the broken URL then 401s at Google's
auth server with ``Error 401: invalid_client``. Encapsulating delivery in
a tool removes the transcription step for channels that support buttons
(Telegram) and the "print to terminal" pattern (CLI), and reduces the
transcription surface for markdown-only channels (Open WebUI) by giving
the LLM a pre-formatted markdown link to embed verbatim.

Broader principle
-----------------
Per the Hermes ``AGENTS.md`` Hetzner briefing, the LLM must NEVER construct
URLs, tokens, or any other "fact/figure" that comes from a system source of
truth (code, env, config, files, infrastructure). Such data is either
computed inside a tool (and the tool returns a status, not the data) or
the LLM tells the user the data isn't available and asks for it. This tool
is the canonical implementation for OAuth URLs; the same pattern should
be applied to other data surfaces (file URLs, n8n webhook URLs, etc.)
incrementally.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys

from tools.registry import registry

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Session / channel detection
# ---------------------------------------------------------------------------

def _detect_session() -> tuple[str, str]:
    """Return ``(platform, chat_id)`` for the current session.

    Falls back to ``("", "")`` for CLI / cron / test contexts where no
    session context is set. Uses ``gateway.session_context`` so concurrent
    gateway tasks don't see each other's session vars.
    """
    try:
        from gateway.session_context import get_session_env
        platform = get_session_env("HERMES_SESSION_PLATFORM", "").lower().strip()
        chat_id = get_session_env("HERMES_SESSION_CHAT_ID", "").strip()
        return platform, chat_id
    except Exception:
        return "", ""


def _session_user_id() -> str:
    """Return the raw channel id of the session user, from session context ONLY.

    This is the identity that ends up in the OAuth ``state`` parameter and
    therefore decides WHOSE vault entry the token is stored under. It is
    deliberately not a tool parameter: on 2026-07-13 the model passed another
    user's telegram id here (it read it from the AGENTS.md user table), which
    filed psingh's Google token under ndr's vault uid and overwrote ndr's
    token. Session context is the only trustworthy source.

    Uses ``get_gws_identity_env`` so cron jobs (which clear
    ``HERMES_SESSION_USER_ID``) still resolve to the job owner's id.
    """
    try:
        from gateway.session_context import get_gws_identity_env
        return get_gws_identity_env().strip()
    except Exception:
        return os.environ.get("HERMES_SESSION_USER_ID", "").strip()


# ---------------------------------------------------------------------------
# Per-channel delivery
# ---------------------------------------------------------------------------

def _deliver_telegram_button(chat_id: str, url: str, label: str,
                             login_hint: str | None, service_name: str | None) -> dict:
    """Send the URL as a Telegram inline-keyboard button.

    The URL is never returned to the caller — it's only ever embedded in
    the ``InlineKeyboardButton.url`` field, which Telegram carries
    byte-for-byte to the user.
    """
    from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not bot_token:
        return {"success": False, "delivery": "telegram_button",
                "error": "TELEGRAM_BOT_TOKEN not set"}

    bot = Bot(token=bot_token)
    text = (
        f"Click the button below to authorize your Google account"
        f"{f' ({login_hint})' if login_hint else ''}.\n\n"
        f"This grants Hermes the scopes it needs to manage Gmail, Calendar, "
        f"Drive, Contacts, Tasks, Docs, and Sheets. You can revoke access "
        f"any time from your Google account settings."
    )
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(label, url=url)]])

    async def _send():
        try:
            msg = await bot.send_message(
                chat_id=int(chat_id),
                text=text,
                reply_markup=keyboard,
                disable_web_page_preview=True,
            )
            return msg.message_id
        finally:
            await bot.close()

    try:
        message_id = asyncio.run(_send())
    except Exception as e:
        logger.warning("send_oauth_url telegram delivery failed: %s", e)
        return {"success": False, "delivery": "telegram_button", "error": str(e)}

    return {
        "success": True,
        "delivery": "telegram_button",
        "message_id": message_id,
        "service": service_name,
    }


def _deliver_cli_print(url: str, label: str, login_hint: str | None,
                       service_name: str | None) -> dict:
    """Print the URL to stderr between banner separators.

    The user reads it from their terminal and copy-pastes into a browser.
    The LLM doesn't see this print — only the JSON status return value.
    """
    account = f" ({login_hint})" if login_hint else ""
    sep = "=" * 72
    sys.stderr.write(
        f"\n{sep}\n"
        f"OAuth Authorization Required — {label}{account}\n"
        f"{sep}\n"
        f"Open this URL in a browser to authorize:\n\n"
        f"  {url}\n\n"
        f"{sep}\n\n"
    )
    sys.stderr.flush()
    return {
        "success": True,
        "delivery": "cli_printed",
        "service": service_name,
    }


def _deliver_markdown_link(url: str, label: str, login_hint: str | None,
                           service_name: str | None) -> dict:
    """Build a pre-formatted markdown link the LLM can embed verbatim.

    For channels that don't have a button primitive (Open WebUI today,
    any markdown-rendering chat surface). The URL is returned in JSON
    because the LLM has to embed it in chat text — the framework renders
    the link. The risk: the LLM might transcribe the URL wrong. We
    mitigate by returning a pre-formatted link the LLM should embed
    verbatim, with an explicit "do not retype" instruction. A future
    "URL safety net" in the gateway/API-server layer could verify the
    link is intact before rendering.
    """
    return {
        "success": True,
        "delivery": "markdown_link",
        "service": service_name,
        "markdown_link": f"[{label}]({url})",
        "_instruction": (
            "Embed the `markdown_link` value VERBATIM in your response. "
            "Do NOT re-type, re-format, or paraphrase the URL — small chat "
            "models have been observed to silently truncate substrings "
            "like 'google.' from OAuth client_ids. If you need to reference "
            "the action in prose, do it without including the URL."
        ),
    }


# ---------------------------------------------------------------------------
# Public tool entry point
# ---------------------------------------------------------------------------

def check_requirements() -> bool:
    return all([
        os.environ.get("HERMES_OAUTH_CLIENT_ID"),
        os.environ.get("HERMES_OAUTH_CLIENT_SECRET"),
    ])


def send_oauth_url(
    login_hint: str | None = None,
    service_name: str | None = None,
    label: str = "Authorize Google account",
    task_id: str | None = None,
) -> str:
    """Compute the OAuth URL and deliver it via the current session's channel.

    The URL is computed server-side and never returned to the caller.
    The return value is a status object: ``success``, ``delivery``,
    ``message_id`` (Telegram), and ``service`` — no URLs, no client_ids.

    The authorizing user's identity is taken from the session context ONLY
    (see :func:`_session_user_id`) — there is deliberately no ``telegram_id``
    parameter, so the model can never file a token under another user's
    vault entry.

    Args:
        login_hint:   Optional email to pre-fill in Google's login form.
        service_name: Optional vault service name (e.g. ``"google-draas"``)
                      — for tracking only. The actual vault key is auto-
                      detected from the id_token email at callback time.
        label:        Button / link label shown to the user.
    """
    from tools import gws_auth

    # 0) Resolve the authorizing user from the session — never from the model.
    user_id = _session_user_id()
    if not user_id:
        return json.dumps({
            "success": False,
            "error": (
                "No session user context (HERMES_SESSION_USER_ID / cron owner "
                "not set) — cannot determine who is authorizing. OAuth links "
                "can only be sent from a user session."
            ),
        })

    # 1) Compute the URL server-side. The URL never leaves this function
    #    except via the channel-specific delivery (button / print / JSON).
    url = gws_auth.get_auth_url(login_hint=login_hint)

    # 2) Detect the current session's channel and deliver accordingly.
    platform, chat_id = _detect_session()

    if platform == "telegram" and chat_id:
        result = _deliver_telegram_button(
            chat_id, url, label, login_hint, service_name
        )
    elif platform == "cli":
        result = _deliver_cli_print(url, label, login_hint, service_name)
    else:
        # Open WebUI and any markdown-rendering channel: return a pre-
        # formatted markdown link. Document the truncation risk in the
        # returned JSON so the LLM is warned.
        result = _deliver_markdown_link(url, label, login_hint, service_name)

    return json.dumps(result)


registry.register(
    name="send_oauth_url",
    toolset="oauth",
    schema={
        "name": "send_oauth_url",
        "description": (
            "Send a GOOGLE WORKSPACE OAuth authorization link to the user via "
            "the current session's channel (Telegram button, CLI print, or Open "
            "WebUI markdown link). This tool is GOOGLE-ONLY -- it always builds "
            "the link via tools.gws_auth, regardless of the `label` you pass; "
            "passing a non-Google label does NOT change which service gets "
            "authorized, it only mislabels the button. For any other OAuth "
            "integration (e.g. Kelsa CRM -> use kelsa_login), call that "
            "integration's own dedicated login tool instead of this one. "
            "DO NOT write OAuth URLs in your own prose — the URL is generated "
            "inside this tool and delivered via a button, terminal print, or "
            "pre-formatted markdown link. The tool returns a status object "
            "with the delivery channel; you do not get the URL. For markdown "
            "channels, embed the returned `markdown_link` VERBATIM — do not "
            "re-type or paraphrase it, because small chat models have been "
            "observed to silently truncate substrings like 'google.' from "
            "OAuth client_ids. Describe the action in prose ('I sent you a "
            "button / link to authorize ndr@draas.com') without revealing the URL. "
            "The authorizing user is ALWAYS the current session user — the "
            "tool reads the identity from the session itself and there is no "
            "way (and no need) to pass a user or telegram id."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "login_hint": {
                    "type": "string",
                    "description": (
                        "Optional email to pre-fill in the OAuth provider's "
                        "login form (e.g. 'ndr@draas.com')."
                    ),
                },
                "service_name": {
                    "type": "string",
                    "description": (
                        "Optional vault service name (e.g. 'google-draas') "
                        "— for your own tracking only; the actual vault key "
                        "is auto-detected from the id_token email at callback time."
                    ),
                },
                "label": {
                    "type": "string",
                    "description": (
                        "Optional button / link label shown to the user. "
                        "Defaults to 'Authorize Google account'."
                    ),
                },
            },
            "required": [],
        },
    },
    # NOTE: args may still contain a stray "telegram_id" from an older model
    # transcript — it is intentionally ignored; identity comes from the
    # session inside send_oauth_url().
    handler=lambda args, **kw: send_oauth_url(
        login_hint=args.get("login_hint"),
        service_name=args.get("service_name"),
        label=args.get("label", "Authorize Google account"),
        task_id=kw.get("task_id"),
    ),
    check_fn=check_requirements,
    requires_env=[
        "HERMES_OAUTH_CLIENT_ID",
        "HERMES_OAUTH_CLIENT_SECRET",
    ],
)
