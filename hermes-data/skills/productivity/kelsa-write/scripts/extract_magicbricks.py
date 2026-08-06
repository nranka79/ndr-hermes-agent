#!/usr/bin/env python3
"""Extract unique leads from MagicBricks emails in Bharat's Gmail.

Parses HTML email bodies to extract Sender Name / Mobile / Email,
deduplicates by phone number, and outputs a JSON chunk file ready for
batch_import_leads.py.

Usage:
  python3 /data/hermes/skills/productivity/kelsa-write/scripts/extract_magicbricks.py [--max 200] [--output /tmp/mb_chunk.json]

Output:
  JSON chunk file consumable by batch_import_leads.py with source_config
  already set to: Magicbricks / MagicBricks / Portals / Ranka udaya

See also: references/magicbricks-email-leads.md
"""

import sys, os, json, re

os.environ.setdefault('GWS_VAULT_SOCKET', '/run/gws-vault/vault.sock')
sys.path.insert(0, '/opt/hermes')

from tools import gws_skill_bridge


def extract_contact(body: str) -> tuple:
    """Parse MagicBricks HTML email. Returns (name, phone, email)."""
    text = re.sub(r'<[^>]+>', '\n', body)
    text = re.sub(r'&nbsp;|&rsquo;|&amp;', ' ', text)

    lines = [l.strip() for l in text.split('\n') if l.strip()]
    name = phone = email_addr = ''

    for i, line in enumerate(lines):
        if "Sender's Name" in line and i + 1 < len(lines):
            name = lines[i + 1].replace('(Individual)', '').replace('(Company)', '').strip()
        elif line in ('Mobile:', 'Phone:') and i + 1 < len(lines):
            phone = re.sub(r'[^0-9]', '', lines[i + 1])
        elif line == 'Email:' and i + 1 < len(lines):
            email_addr = lines[i + 1].strip()

    return name, phone, email_addr


def get_kelsa_phone(phone_raw: str) -> str:
    """Normalize phone to 91XXXXXXXXXX format, no + prefix."""
    cleaned = re.sub(r'[\s\-\.\(\)]', '', phone_raw).strip()
    if cleaned.startswith('+'):
        cleaned = cleaned[1:]
    if cleaned.startswith('91') and len(cleaned) == 12:
        return cleaned
    elif len(cleaned) == 10:
        return '91' + cleaned
    elif cleaned.startswith('0'):
        return '91' + cleaned[1:]
    return cleaned


def main():
    max_emails = 200
    output_path = '/tmp/chunk_magicbricks.json'

    # Parse --max and --output from argv
    for i, arg in enumerate(sys.argv):
        if arg == '--max' and i + 1 < len(sys.argv):
            max_emails = int(sys.argv[i + 1])
        if arg == '--output' and i + 1 < len(sys.argv):
            output_path = sys.argv[i + 1]

    print(f"Searching up to {max_emails} MagicBricks emails...")
    result = gws_skill_bridge.call("gmail_search",
        service_name="google-draas",
        query="from:(info@magicbricks.com) buyer contacted you",
        max=max_emails)
    emails = json.loads(result)
    print(f"Found {len(emails)} emails")

    seen_phones = set()
    rows = []

    for i, email in enumerate(emails):
        if (i + 1) % 30 == 0:
            print(f"  parsed {i+1}/{len(emails)}...")

        msg = gws_skill_bridge.call("gmail_get",
            service_name="google-draas",
            message_id=email['id'])
        body = json.loads(msg).get('body', '')
        name, phone_raw, email_addr = extract_contact(body)
        phone = get_kelsa_phone(phone_raw)
        phone10 = phone[-10:] if len(phone) >= 10 else phone

        if name and phone10 and phone10 not in seen_phones and len(phone10) == 10:
            seen_phones.add(phone10)
            rows.append([
                email['date'][:10],      # col A: date
                '',                       # col B: investment
                '',                       # col C: visit pref
                name,                     # col D: full name
                phone,                    # col E: phone (91XXXXXXXXXX)
                email_addr,               # col F: email
                '',                       # col G: city
                '',                       # col H: status
                '',                       # col I: remarks
                ''                        # col J: next followup
            ])

    print(f"\nExtracted {len(rows)} unique leads")

    chunk = {
        'chunk': rows,
        'start_index': 0,
        'total': len(rows),
        'source_config': {
            'source': 'Magicbricks',
            'sourcedetails': 'MagicBricks',
            'channel': 'Portals',
            'project': 'Ranka udaya'
        },
        'chunk_id': 'magicbricks'
    }

    with open(output_path, 'w') as f:
        json.dump(chunk, f, indent=2)

    print(f"Chunk saved to {output_path}")
    print(f"Then run: python3 /data/hermes/scripts/batch_import_leads.py {output_path} /tmp/mb_results.json")


if __name__ == '__main__':
    main()
