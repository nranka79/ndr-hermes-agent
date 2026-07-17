"""WhatsApp deep-link generator.

Produces wa.me URLs that open WhatsApp with an optional recipient and/or
pre-filled message text.

Encoding rules (RFC 3986 + WhatsApp-specific workarounds):

  ┌──────────────────────┬─────────────────────┬──────────────────────────┐
  │ Category             │ Characters          │ Treatment                │
  ├──────────────────────┼─────────────────────┼──────────────────────────┤
  │ Unreserved (safe)    │ A-Z a-z 0-9 - . _ ~ │ Left as-is               │
  │ Reserved (sub-delim) │ ! $ & ' ( ) * + , ; │ → %21 %24 %26 %27 %28    │
  │                      │ =                   │   %29 %2A %2B %2C %3B    │
  │                      │                     │   %3D                    │
  │ Reserved (gen-delim) │ : / ? # [ ] @       │ → %3A %2F %3F %23 %5B    │
  │                      │                     │   %5D %40                │
   │ Unsafe               │ space " % < > \\ ^   │ → %20 %22 %25 %3C %3E    │
  │                      │ ` { | }             │   %5C %5E %60 %7B %7C    │
  │                      │                     │   %7D                    │
  │ Non-ASCII            │ unicode, emoji       │ UTF-8 → percent-encoded  │
  │ Newline              │ \\n, \\r\\n           │ → %0A, %0D%0A            │
  └──────────────────────┴─────────────────────┴──────────────────────────┘

  Special workaround: ASCII ampersand (U+0026 &) is encoded as %EF%BC%86
  (UTF-8 bytes for U+FF06 FULLWIDTH AMPERSAND ＆) rather than the standard
  %26.  This prevents the & from being misinterpreted as a query-parameter
  separator by WhatsApp's URL parser when the URL passes through layers
  (browsers, messaging apps, redirects) that decode and re-encode URLs.

  Same workaround, same reason, for ASCII number sign / hash / pound (U+0023
  #): encoded as %EF%BC%83 (UTF-8 bytes for U+FF03 FULLWIDTH NUMBER SIGN
  ＃) instead of the standard %23.  Left as %23, a single decode pass by
  an intermediary (mobile OS link handler, in-app browser, redirect) turns
  it into a literal '#', which gets interpreted as the START OF A URL
  FRAGMENT — everything after it in the message text is silently dropped
  before WhatsApp ever sees it. This is the "message gets cut off at the
  pound sign" bug.

  The platform parameter (telegram) additionally returns a MarkdownV2-escaped
  display_text and a pre-built MarkdownV2-safe inline link so Telegram's
  parser never breaks on reserved characters in the link text.

This is the ONLY sanctioned way to build a wa.me URL. Do not hand-encode one
with urllib.parse or any other method — the encoding rules are easy to get
wrong and this tool is the single source of truth for it.
"""

import json
import re
import urllib.parse

from tools.registry import registry, tool_error

# ── Telegram MarkdownV2 reserved characters ────────────────────────────────
# Per the Telegram Bot API docs, these 18 characters must be escaped with a
# preceding backslash when they appear outside formatting syntax:
#   _ * [ ] ( ) ~ ` > # + - = | { } . !
_TELEGRAM_MDV2_RESERVED = re.compile(r'([_*\[\]()~`>#+\-=|{}.!\\])')


def _escape_telegram_mdv2(text: str) -> str:
    """Escape all 18 MarkdownV2-reserved characters with a backslash prefix."""
    return _TELEGRAM_MDV2_RESERVED.sub(r'\\\1', text)


WHATSAPP_LINK_SCHEMA = {
    "name": "whatsapp_link",
    "description": (
        "Generate a wa.me deep link that opens WhatsApp with an optional "
        "pre-filled message and/or recipient phone number.\n\n"
        "MANDATORY: This is the ONLY sanctioned way to produce a wa.me URL. "
        "You MUST call this tool EVERY TIME you need one — never construct, "
        "hand-encode, or type a wa.me URL manually (including via "
        "execute_code/urllib.parse or any other tool). Manual encoding is "
        "known to break on mobile WhatsApp clients. If this tool is "
        "unavailable, tell the user rather than improvising an encoding."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "phone": {
                "type": "string",
                "description": (
                    "Recipient phone number. Any format is accepted — E.164 "
                    "(+15551234567), local, or with spaces/dashes. "
                    "All non-digit characters are stripped automatically. "
                    "10-digit numbers without a country code automatically "
                    "get ISD 91 (India) prepended. "
                    "Omit to create a link that opens WhatsApp without a "
                    "pre-set recipient."
                ),
            },
            "text": {
                "type": "string",
                "description": (
                    "Message text to pre-fill in the WhatsApp compose box. "
                    "Omit to create a link that just opens the chat."
                ),
            },
            "platform": {
                "type": "string",
                "enum": ["telegram", "whatsapp"],
                "description": (
                    "Target platform. When 'telegram', the response includes "
                    "a display_text (MarkdownV2-escaped) and display_link "
                    "(MarkdownV2-safe inline link) so Telegram's parser never "
                    "breaks on reserved characters in the link text. "
                    "When 'whatsapp' or omitted, only the raw URL is returned."
                ),
            },
        },
        "required": [],
    },
}


def _sanitize_phone(phone: str) -> str:
    """Strip everything except digits from a phone number string."""
    return re.sub(r"\D", "", phone)


def _encode_wa_text(text: str) -> str:
    """Percent-encode *text* for the ``?text=`` query parameter of a wa.me URL.

    Encoding order (critical — % MUST be encoded first):

    1. ``%`` → ``%25``              – prevent double-encoding
    2. RFC 3986 percent-encode all non‑unreserved characters
       (unreserved: A‑Z a‑z 0‑9 ‑ . _ ~)
    3. ``%26`` (standard &) → ``%EF%BC%86`` (fullwidth ＆)
    4. ``%23`` (standard #) → ``%EF%BC%83`` (fullwidth ＃) — prevents
       intermediary layers from decoding it back to a literal '#' and
       truncating the message at a URL-fragment boundary (see module
       docstring).

    Returns the percent-encoded string ready for use in ``wa.me/?text=…``.
    """
    text = text.replace("%", "%25")
    encoded = urllib.parse.quote(text, safe="~")
    encoded = encoded.replace("%26", "%EF%BC%86")
    encoded = encoded.replace("%23", "%EF%BC%83")
    return encoded


def _extract_whatsapp_preview(text: str, max_len: int = 80) -> str:
    """Return a short human-readable preview of *text* for the tool response."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def whatsapp_link_tool(args, **kw):
    phone_raw = (args.get("phone") or "").strip()
    text_raw = (args.get("text") or "").strip()
    platform = (args.get("platform") or "").strip().lower()

    if not phone_raw and not text_raw:
        return tool_error("At least one of 'phone' or 'text' must be provided.")

    phone_digits = _sanitize_phone(phone_raw) if phone_raw else ""
    # Leading trunk "0" + 10-digit local number (common Indian formatting
    # convention, e.g. "098765 43210") — strip the trunk 0 so the bare
    # 10-digit branch below can prepend ISD 91 correctly. Without this, an
    # 11-digit 0-prefixed number passed through untouched, producing a
    # wa.me link with a stray leading zero.
    if phone_digits and len(phone_digits) == 11 and phone_digits.startswith("0"):
        phone_digits = phone_digits[1:]
    # Bare 10-digit number without ISD code — default to ISD 91 (India).
    if phone_digits and len(phone_digits) == 10:
        phone_digits = "91" + phone_digits
    base = f"https://wa.me/{phone_digits}" if phone_digits else "https://wa.me/"
    encoded_text = _encode_wa_text(text_raw) if text_raw else ""
    url = f"{base}?text={encoded_text}" if encoded_text else base

    result = {
        "url": url,
        "phone": phone_digits or None,
        "text": text_raw or None,
    }

    if platform == "telegram" and text_raw:
        display_text = _escape_telegram_mdv2(text_raw)
        # In the URL portion of a markdown link, only ')' and '\' need escaping
        encoded_for_tg_url = encoded_text.replace("\\", "\\\\").replace(")", "\\)")
        result["display_text"] = display_text
        result["display_link"] = (
            f"[{display_text}]({base}?text={encoded_for_tg_url})"
        )

    return json.dumps(result)


registry.register(
    name="whatsapp_link",
    toolset="messaging",
    schema=WHATSAPP_LINK_SCHEMA,
    handler=whatsapp_link_tool,
    emoji="🔗",
)
