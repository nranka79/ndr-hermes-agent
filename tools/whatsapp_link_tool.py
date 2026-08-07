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

  Percent: a literal '%' must be encoded EXACTLY once as %25. urllib's
  quote() does this natively; never pre-replace '%' manually before quoting
  or it gets double-encoded (%25 → %2525) and WhatsApp displays a literal
  "%25" instead of "%".

  Length: Telegram caps a single message at 4096 UTF-16 code units. When the
  generated URL would exceed that, the message text is split into parts and
  the tool returns one wa.me URL per part (see the "parts" key). Each part is
  sized so the worst-case single-message delivery form — the MarkdownV2
  inline link [display_text](url) — stays under the cap, so Telegram's own
  message splitter never cuts a link in half.

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

# ── Telegram message-length limits ─────────────────────────────────────────
# Single message cap per the Bot API: 4096 characters, measured in UTF-16
# code units (emoji and other non-BMP chars count as 2).
_TELEGRAM_MAX_MESSAGE_LENGTH = 4096
# Headroom kept below the cap so MarkdownV2 escapes and adapter-side markers
# never push a part over the limit.
_TELEGRAM_SPLIT_RESERVE = 10


def _escape_telegram_mdv2(text: str) -> str:
    """Escape all 18 MarkdownV2-reserved characters with a backslash prefix."""
    return _TELEGRAM_MDV2_RESERVED.sub(r'\\\1', text)


def _utf16_len(s: str) -> int:
    """Count UTF-16 code units in *s*.

    Telegram measures its 4096-character message limit in UTF-16 code units,
    not Unicode code points. Characters outside the Basic Multilingual Plane
    (emoji, CJK Extension B, …) encode as surrogate pairs and count as two.
    """
    return len(s.encode("utf-16-le")) // 2


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
        "unavailable, tell the user rather than improvising an encoding.\n\n"
        "LONG MESSAGES: if the encoded URL would exceed Telegram's "
        "single-message limit (4096 characters), the tool splits the message "
        "into parts and returns a 'parts' array (one wa.me URL per part) "
        "plus 'split': true. Deliver EACH part as its own separate Telegram "
        "message — never combine multiple parts into one message, or "
        "Telegram's own splitter will cut the link in half."
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
                    "Omit to create a link that just opens the chat. "
                    "Long text is automatically split into multiple links "
                    "(see 'parts' in the response) when a single link would "
                    "exceed Telegram's 4096-character message limit."
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

    Encoding order (critical):

    1. RFC 3986 percent-encode every non-unreserved character with
       ``urllib.parse.quote`` (unreserved: A‑Z a‑z 0‑9 ‑ . _ ~).  quote()
       encodes a literal ``%`` as ``%25`` natively — do NOT pre-replace
       ``%`` manually before quoting, or it is encoded twice (``%25`` →
       ``%2525``) and WhatsApp displays a literal ``%25``.
    2. ``%26`` (standard &) → ``%EF%BC%86`` (fullwidth ＆)
    3. ``%23`` (standard #) → ``%EF%BC%83`` (fullwidth ＃) — prevents
       intermediary layers from decoding it back to a literal '#' and
       truncating the message at a URL-fragment boundary (see module
       docstring).

    The fullwidth escapes contain no ``%26``/``%23`` substrings, so the
    replacements never cascade; a literal ``%26``/``%23`` in the source text
    encodes to ``%2526``/``%2523`` and is left untouched.

    Returns the percent-encoded string ready for use in ``wa.me/?text=…``.
    """
    encoded = urllib.parse.quote(text, safe="~")
    encoded = encoded.replace("%26", "%EF%BC%86")
    encoded = encoded.replace("%23", "%EF%BC%83")
    return encoded


def _part_fits(part_text: str, base_url: str) -> bool:
    """Return whether *part_text* can be delivered as one Telegram message.

    Robust budget: the worst-case single-message form is the MarkdownV2
    inline link ``[display_text](url)``. Its total UTF-16 length (display
    text + encoded URL + 3 markup chars) must stay under Telegram's 4096-
    unit cap minus the reserve. That guarantees the part survives no matter
    how the agent delivers it — as the display link or as the bare URL —
    without Telegram's own 4096 splitter ever cutting it in half.
    """
    url = f"{base_url}?text={_encode_wa_text(part_text)}"
    display = _escape_telegram_mdv2(part_text)
    link_len = _utf16_len(display) + _utf16_len(url) + 3  # "[text](url)"
    return (
        _utf16_len(part_text) <= _TELEGRAM_MAX_MESSAGE_LENGTH
        and _utf16_len(url) <= _TELEGRAM_MAX_MESSAGE_LENGTH
        and link_len <= _TELEGRAM_MAX_MESSAGE_LENGTH - _TELEGRAM_SPLIT_RESERVE
    )


# Split points, most desirable first: newline, sentence end, word space.
_SPLIT_BOUNDARY_MARKERS = ("\n", "。", ". ", " ")


def _prefer_split_boundary(text: str, safe_len: int) -> int:
    """Return the largest split point ≤ *safe_len* on a natural boundary.

    Prefers a newline, then a sentence/word boundary, so multi-part messages
    don't cut mid-sentence. Falls back to *safe_len* itself.
    """
    for marker in _SPLIT_BOUNDARY_MARKERS:
        idx = text.rfind(marker, 0, safe_len)
        if idx >= 0:
            return idx + len(marker)
    return safe_len


def _split_wa_text(text: str, base_url: str) -> list:
    """Split *text* into parts, each deliverable as one Telegram message.

    Greedy loop: take the largest prefix that passes :func:`_part_fits`
    (binary search — the encoded length grows monotonically with the prefix
    length), then back off to the nearest natural boundary for readability.
    Only backs off when the rest genuinely cannot fit whole — a message that
    fits entirely is never split. Always terminates: a single character fits
    in every case (worst case a literal ``&`` → ``%EF%BC%86`` = 6 encoded
    chars), so ``best >= 1``.
    """
    parts = []
    rest = text
    while rest:
        lo, hi = 1, len(rest)
        best = 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if _part_fits(rest[:mid], base_url):
                best = mid
                lo = mid + 1
            else:
                hi = mid - 1
        if best == len(rest):
            parts.append(rest)
            break
        cut = _prefer_split_boundary(rest, best)
        parts.append(rest[:cut])
        rest = rest[cut:]
    return parts


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

    result = {
        "phone": phone_digits or None,
        "text": text_raw or None,
    }

    if not text_raw:
        result["url"] = base
        return json.dumps(result)

    def _build_part(part_text: str) -> dict:
        url = f"{base}?text={_encode_wa_text(part_text)}"
        part = {"text": part_text, "url": url}
        if platform == "telegram":
            display_text = _escape_telegram_mdv2(part_text)
            # In the URL portion of a markdown link, only ')' and '\' need escaping
            encoded_for_tg_url = url.replace("\\", "\\\\").replace(")", "\\)")
            part["display_text"] = display_text
            part["display_link"] = (
                f"[{display_text}]({encoded_for_tg_url})"
            )
        return part

    parts = [_build_part(part_text) for part_text in _split_wa_text(text_raw, base)]

    result["url"] = parts[0]["url"]

    if len(parts) > 1:
        result["parts"] = parts
        result["split"] = True
        result["message_count"] = len(parts)
        result["split_reason"] = (
            "The wa.me URL exceeds Telegram's single-message limit of "
            f"{_TELEGRAM_MAX_MESSAGE_LENGTH} characters. Each part is a "
            "complete link and must be delivered as its own separate "
            "Telegram message."
        )

    if platform == "telegram":
        result["display_text"] = parts[0]["display_text"]
        result["display_link"] = parts[0]["display_link"]

    return json.dumps(result)


registry.register(
    name="whatsapp_link",
    toolset="messaging",
    schema=WHATSAPP_LINK_SCHEMA,
    handler=whatsapp_link_tool,
    emoji="🔗",
)
