"""WhatsApp deep-link generator.

Produces wa.me URLs that open WhatsApp on the user's phone with an optional
recipient and/or pre-filled message text.

Special encoding rule: literal '&' in the message text is encoded as
%EF%BC%86 (UTF-8 bytes for U+FF06 FULLWIDTH AMPERSAND ＆) rather than the
standard %26.  This prevents the ampersand from being misinterpreted as a
query-parameter separator by WhatsApp's URL parser while still surviving
round-trips through browsers and messaging apps that normalise %26 back to '&'.
"""

import json
import re
import urllib.parse

from tools.registry import registry, tool_error

WHATSAPP_LINK_SCHEMA = {
    "name": "whatsapp_link",
    "description": (
        "Generate a wa.me deep link that opens WhatsApp with an optional "
        "pre-filled message and/or recipient phone number.\n\n"
        "IMPORTANT: Use this tool EVERY TIME you need to create a WhatsApp "
        "link. Never construct wa.me URLs manually."
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
        },
        "required": [],
    },
}


def _sanitize_phone(phone: str) -> str:
    """Strip everything except digits from a phone number string."""
    return re.sub(r"\D", "", phone)


def _encode_wa_text(text: str) -> str:
    """Percent-encode text for a wa.me ?text= query parameter.

    Encodes all characters that need escaping, then replaces the standard
    %26 (ASCII ampersand) with %EF%BC%86 (fullwidth ampersand U+FF06) so
    the '&' character is never parsed as a query-string delimiter by
    WhatsApp's URL handler.
    """
    encoded = urllib.parse.quote(text, safe="")
    return encoded.replace("%26", "%EF%BC%86")


def whatsapp_link_tool(args, **kw):
    phone_raw = (args.get("phone") or "").strip()
    text_raw = (args.get("text") or "").strip()

    if not phone_raw and not text_raw:
        return tool_error("At least one of 'phone' or 'text' must be provided.")

    phone_digits = _sanitize_phone(phone_raw) if phone_raw else ""

    base = f"https://wa.me/{phone_digits}" if phone_digits else "https://wa.me/"

    if text_raw:
        url = f"{base}?text={_encode_wa_text(text_raw)}"
    else:
        url = base

    return json.dumps({"url": url, "phone": phone_digits or None, "text": text_raw or None})


registry.register(
    name="whatsapp_link",
    toolset="messaging",
    schema=WHATSAPP_LINK_SCHEMA,
    handler=whatsapp_link_tool,
    emoji="🔗",
)
