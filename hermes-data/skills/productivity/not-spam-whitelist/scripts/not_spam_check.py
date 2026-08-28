#!/usr/bin/env python3
"""
Daily not-spam whitelist check — standalone script for the cron job.

Reads whitelist rules from the DRAAS Not-Spam Whitelist sheet (google-draas account),
fetches up to 200 spam messages from the same account, checks each against rules,
and moves matching messages to INBOX (removes SPAM label).

Usage: python3 /opt/hermes/.../scripts/not_spam_check.py

Works from the trusted process (terminal with sys.path including /opt/hermes).
Do NOT run from execute_code sandbox — gws_auth's sandbox RPC stub may not
have gws_fetch_token available (2026-08-28: ImportError observed).
"""

import sys
import os
import re
import json

sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service

SHEET_ID = "1w8_R0JzfHP1PIdPoCFpqdhDh9TFU0qPqbt3V2vfDyw0"
WHITELIST_RANGE = "Whitelist!A:I"


def get_whitelist(sheets_svc):
    rows = sheets_svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range=WHITELIST_RANGE
    ).execute().get('values', [])
    rules = []
    for row in rows[1:]:  # skip header
        rules.append({
            'rule_type': (row[0] or '').strip().lower() if len(row) > 0 else '',
            'col_c': (row[2] or '').strip() if len(row) > 2 else '',
            'col_e': (row[4] or '').strip() if len(row) > 4 else '',
        })
    return [r for r in rules if r['rule_type']]


def get_spam_messages(gmail_svc, max_msgs=200):
    result = gmail_svc.users().messages().list(
        userId='me', q='in:spam', maxResults=max_msgs
    ).execute()
    messages = result.get('messages', [])
    if not messages:
        return []
    full_msgs = []
    for msg in messages:
        detail = gmail_svc.users().messages().get(
            userId='me', id=msg['id'], format='metadata',
            metadataHeaders=['From', 'Subject', 'To', 'Date']
        ).execute()
        headers = {h['name']: h['value'] for h in detail.get('payload', {}).get('headers', [])}
        full_msgs.append({
            'id': msg['id'],
            'from': headers.get('From', ''),
            'subject': headers.get('Subject', ''),
        })
    return full_msgs


def check_whitelist(msg, rules):
    sender = msg['from']
    subject = msg['subject']
    email_match = re.search(r'<([^>]+)>', sender)
    sender_email = email_match.group(1) if email_match else sender
    sender_domain = sender_email.split('@')[1] if '@' in sender_email else ''

    matches = []
    if '@draas.com' in sender_email.lower():
        matches.append(f"Internal (draas.com): {sender_email}")

    for rule in rules:
        rt = rule['rule_type']
        if rt == 'exact_from':
            target = rule['col_c']
            if target and sender_email.lower() == target.lower():
                matches.append(f"exact_from: {sender_email} = {target}")
        elif rt == 'domain_from':
            domain = rule['col_c']
            if domain and sender_email.lower().endswith(domain.lower()):
                matches.append(f"domain_from: {sender_email} ends with {domain}")
        elif rt == 'subject_contains':
            for kw in [k.strip() for k in rule['col_e'].split(',') if k.strip()]:
                if kw.lower() in subject.lower():
                    matches.append(f"subject_contains: '{kw}' in '{subject}'")
                    break
        elif rt == 'combined':
            domain = rule['col_c']
            domain_match = domain and sender_email.lower().endswith(domain.lower())
            kw_match = any(
                kw.strip().lower() in subject.lower()
                for kw in rule['col_e'].split(',') if kw.strip()
            ) if rule['col_e'] else False
            if domain_match and kw_match:
                matches.append(f"combined: {sender_email} + subject match")
    return matches


def move_to_inbox(gmail_svc, msg_id):
    gmail_svc.users().messages().modify(
        userId='me', id=msg_id,
        body={'removeLabelIds': ['SPAM'], 'addLabelIds': ['INBOX']}
    ).execute()


def main():
    # Use google-draas (ndr@draas.com) — owns the sheet and the primary inbox
    svc_name = 'google-draas'
    sheets = build_service('sheets', 'v4', service_name=svc_name)
    gmail = build_service('gmail', 'v1', service_name=svc_name)

    rules = get_whitelist(sheets)
    print(f"Rules loaded: {len(rules)}")

    spam_msgs = get_spam_messages(gmail, 200)
    print(f"Spam checked: {len(spam_msgs)}")

    moved = 0
    for msg in spam_msgs:
        matches = check_whitelist(msg, rules)
        if matches:
            move_to_inbox(gmail, msg['id'])
            moved += 1
            print(f"  MOVED: {msg['from'][:50]} | {msg['subject'][:60]}")

    print(f"\nMoved to inbox: {moved}")
    return moved


if __name__ == '__main__':
    main()