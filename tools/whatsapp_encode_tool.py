#!/usr/bin/env python3
"""
WhatsApp Encode Tool — generates wa.me deep-link URLs with properly
percent-encoded message text for WhatsApp click-to-chat links.

Registered as: whatsapp_encode
Toolset: messaging

Never do URL encoding manually in a skill or tool call — Python's
urllib.parse.quote handles all edge cases (newlines, asterisks,
underscores, unicode, ampersands) that LLM-generated encoding gets wrong.

Default country code: +91 (India). Numbers without a leading + get +91 prepended.
"""

import json
import logging
import re
from urllib.parse import quote

logger = logging.getLogger(__name__)


def _normalize_phone(phone: str) -> str:
    """
    Normalise a phone number to E.164 format.
    - Strip spaces, dashes, parentheses, dots
    - If starts with +: keep as-is (already has country code)
    - If starts with 0: strip leading 0 and prepend +91
    - Otherwise: prepend +91 (India default)
    Returns digits-only string with leading + (e.g. "+919876543210").
    """
    if not phone:
        return ""
    stripped = re.sub(r"[\s\-().+]", "", phone)
    original = phone.strip()

    if original.startswith("+"):
        # already has country code — keep digits only, restore +
        return "+" + stripped
    elif stripped.startswith("0"):
        # local format with leading 0 (e.g. 09876543210)
        return "+91" + stripped[1:]
    else:
        return "+91" + stripped


def _handle_whatsapp_encode(args: dict, **kwargs) -> str:
    message = (args.get("message") or "").strip()
    phone   = (args.get("phone") or "").strip()
    mode    = (args.get("mode") or "link").strip().lower()

    if not message:
        return json.dumps({"success": False, "error": "message is required"})

    # Percent-encode everything — safe='' means no characters are left unencoded
    encoded_text = quote(message, safe="")

    result = {"encoded_text": encoded_text}

    if phone:
        normalized = _normalize_phone(phone)
        # Strip leading + for wa.me URL (wa.me uses digits only after the slash)
        phone_digits = normalized.lstrip("+")
        url = f"https://wa.me/{phone_digits}?text={encoded_text}"
        result["url"] = url
        result["phone_normalized"] = normalized
        result["note"] = "Click this link on a mobile device to open WhatsApp with the message pre-filled."
    else:
        result["url"] = f"https://wa.me/?text={encoded_text}"
        result["note"] = (
            "No phone number provided. Use this link for group messages, "
            "or replace the phone number manually: https://wa.me/PHONENUMBER?text=..."
        )

    if mode == "text_only":
        return json.dumps({"encoded_text": encoded_text})

    return json.dumps(result)


_SCHEMA = {
    "name": "whatsapp_encode",
    "description": (
        "Generate a wa.me WhatsApp deep-link URL with the message text properly "
        "URL-encoded. ALWAYS use this tool — never encode WhatsApp URLs manually. "
        "Handles all special characters: newlines, asterisks (*bold*), underscores "
        "(_italic_), ampersands, quotes, slashes, Unicode. "
        "Default country code: +91 (India) for numbers without a country prefix. "
        "Use mode='text_only' when you only need the encoded text (e.g., for group links)."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": (
                    "The full WhatsApp message text to encode, including any "
                    "*bold*, _italic_, or numbered list formatting. "
                    "Pass the final approved draft exactly as it should appear."
                ),
            },
            "phone": {
                "type": "string",
                "description": (
                    "Recipient's phone number. Can be in any format: "
                    "+91 98765 43210, 9876543210, 09876543210, +919876543210. "
                    "Omit for group messages (link works without a number)."
                ),
            },
            "mode": {
                "type": "string",
                "enum": ["link", "text_only"],
                "description": (
                    "link (default): return the full wa.me URL. "
                    "text_only: return only the encoded text portion."
                ),
            },
        },
        "required": ["message"],
    },
}


from tools.registry import registry  # noqa: E402

registry.register(
    name="whatsapp_encode",
    toolset="messaging",
    schema=_SCHEMA,
    handler=_handle_whatsapp_encode,
    check_fn=lambda: True,
    requires_env=[],
    is_async=False,
    description=_SCHEMA["description"],
    emoji="💬",
)
