#!/usr/bin/env python3
"""Batch import leads from Google Sheet to Kelsa Pipeline 10.

Usage:
  python3 /data/hermes/scripts/batch_import_leads.py <chunk_file.json> <output_results.json>

Chunk file format:
  {
    "chunk": [rows...],       # Array of lead rows (same order as sheet rows)
    "start_index": 0,         # Global row index offset (0-based)
    "total": 661,             # Total leads across all chunks
    "source_config": {        # Pipeline 10 field values
      "source": "I Am Here Software Labs",
      "sourcedetails": "Meta",
      "channel": "DigitalAds",
      "project": "Ranka udaya"
    },
    "chunk_id": 0
  }

Each row: ["date", "investment", "visit_pref", "name", "phone", "email",
           "city", "status", "remarks", "next_followup"]

Output: JSON with 'results' array, 'stats' dict, progress info.
Sheet rows with empty names are skipped.

Author: Hermes Agent
Created: 2026-07-22
"""

import sys, os, json, re, asyncio, time
from datetime import datetime

os.environ.setdefault('GWS_VAULT_SOCKET', '/run/gws-vault/vault.sock')
sys.path.insert(0, '/opt/hermes')

from tools.kelsa_auth import get_valid_access_token
import httpx
from mcp.client.streamable_http import streamable_http_client
from mcp import ClientSession


# --- Helpers ---

def get_kelsa_phone(phone_raw: str) -> str:
    """Normalize phone to 91XXXXXXXXXX format (12 digits, no + prefix)."""
    if not phone_raw:
        return '91__________'  # placeholder for missing
    cleaned = re.sub(r'[\s\-\.\(\)]', '', phone_raw).strip()
    if cleaned.startswith('+'):
        cleaned = cleaned[1:]
    if cleaned.startswith('91') and len(cleaned) >= 12:
        return cleaned
    elif not cleaned.isdigit():
        return ''
    elif len(cleaned) == 10:
        return '91' + cleaned
    elif cleaned.startswith('0'):
        return '91' + cleaned[1:]
    else:
        return '91' + cleaned[-10:]


def parse_investment(raw: str) -> int | None:
    """Parse '₹ 50 L+' to 5000000, '₹ 1 CR & Above' to 10000000, etc."""
    if not raw or not raw.strip():
        return None
    raw = raw.replace('₹', '').replace(',', '').strip()
    if 'CR' in raw.upper():
        m = re.search(r'(\d+(?:\.\d+)?)', raw)
        return int(float(m.group(1)) * 10000000) if m else None
    elif 'L' in raw:
        m = re.search(r'(\d+(?:\.\d+)?)', raw)
        return int(float(m.group(1)) * 100000) if m else None
    return None


async def process_lead(session, row: list, sheet_row: int, sc: dict) -> dict:
    """Process one row. Returns {sheet_row, name, phone, status, kelsa_url, lead_id, detail}."""
    name = (row[3] or '').strip() if len(row) > 3 else ''
    phone_raw = (row[4] or '').strip() if len(row) > 4 else ''
    email = (row[5] or '').strip() if len(row) > 5 else ''
    date_str = (row[0] or '').strip() if len(row) > 0 and row[0] else ''
    inv_raw = (row[1] or '').strip() if len(row) > 1 and row[1] else ''
    visit_pref = (row[2] or '').strip() if len(row) > 2 and row[2] else ''
    remarks = (row[8] or '').strip() if len(row) > 8 and row[8] else ''

    if not name:
        return dict(sheet_row=sheet_row, name='', phone=phone_raw,
                     status='Failed', kelsa_url='', lead_id=0,
                     detail='No name')

    phone_kelsa = get_kelsa_phone(phone_raw)
    phone_10 = phone_kelsa[-10:]
    budget = parse_investment(inv_raw)

    # --- Step 1: Duplicate check ---
    try:
        sr = await session.call_tool('search_leads', arguments={
            'pipeline_id': 10, 'query': phone_10, 'per_page': 3
        })
        txt = sr.content[0].text if sr.content else ''
    except Exception:
        txt = ''

    cm = re.search(r'(\d+) result', txt)
    if cm and int(cm.group(1)) > 0:
        ids = re.findall(r'\[#(\d+)\]', txt)
        lid = int(ids[0]) if ids else 0
        url = f'https://app.kelsa.io/5/leads/{lid}' if lid else ''
        return dict(sheet_row=sheet_row, name=name, phone=phone_kelsa,
                     status='Already Exists', kelsa_url=url, lead_id=lid,
                     detail='Duplicate: already in Pipeline 10')

    # --- Step 2: Create contact ---
    cf = {'name': name}
    if phone_kelsa and phone_kelsa != '91__________':
        cf['phone'] = phone_kelsa
    if email:
        cf['email'] = email

    try:
        cr = await session.call_tool('create_lead', arguments={
            'pipeline_id': 3429,
            'field_values': {'cf_contact': cf}
        })
        ctxt = cr.content[0].text if cr.content else ''
    except Exception as e:
        return dict(sheet_row=sheet_row, name=name, phone=phone_raw,
                     status='Failed', kelsa_url='', lead_id=0,
                     detail=f'Contact creation error: {str(e)[:150]}')

    cid_m = re.search(r'ID: (\d+)', ctxt)
    contact_id = int(cid_m.group(1)) if cid_m else None
    if not contact_id:
        try:
            sc2 = await session.call_tool('search_leads', arguments={
                'pipeline_id': 3429, 'query': phone_10, 'per_page': 1
            })
            sc2t = sc2.content[0].text if sc2.content else ''
            cid_m2 = re.search(r'\[#(\d+)\]', sc2t)
            contact_id = int(cid_m2.group(1)) if cid_m2 else None
        except Exception:
            pass

    if not contact_id:
        return dict(sheet_row=sheet_row, name=name, phone=phone_raw,
                     status='Failed', kelsa_url='', lead_id=0,
                     detail=f'No contact ID: {ctxt[:200]}')

    await asyncio.sleep(1.5)

    # --- Step 3: Create lead ---
    lf = {
        'cf_contact1': {'id': contact_id},
        'cf_source': sc['source'],
        'cf_sourcedetails': sc['sourcedetails'],
        'cf_campaign': sc['channel'],
        'cf_project': sc['project']
    }
    if budget:
        lf['cf_max_budget'] = budget
    if visit_pref and visit_pref != 'I need more details first':
        lf['cf_requirements'] = visit_pref

    try:
        lr = await session.call_tool('create_lead', arguments={
            'pipeline_id': 10, 'field_values': lf
        })
        lt = lr.content[0].text if lr.content else ''
    except Exception as e:
        return dict(sheet_row=sheet_row, name=name, phone=phone_kelsa,
                     status='Failed', kelsa_url='', lead_id=0,
                     detail=f'Lead creation error: {str(e)[:150]}')

    # --- Resolve lead ID ---
    dm = re.search(r'draft ID: (\d+)', lt)
    draft_id = int(dm.group(1)) if dm else None
    lead_id = None

    if draft_id:
        await asyncio.sleep(2)
        try:
            dr = await session.call_tool('get_draft_status', arguments={'draft_id': draft_id})
            drt = dr.content[0].text if dr.content else ''
            lm2 = re.search(r'ID: (\d+)', drt)
            if lm2:
                lead_id = int(lm2.group(1))
        except Exception:
            pass

    if not lead_id:
        await asyncio.sleep(2)
        try:
            sr3 = await session.call_tool('search_leads', arguments={
                'pipeline_id': 10, 'query': phone_10, 'per_page': 1
            })
            sr3t = sr3.content[0].text if sr3.content else ''
            ids3 = re.findall(r'\[#(\d+)\]', sr3t)
            if ids3:
                lead_id = int(ids3[0])
        except Exception:
            pass

    if not lead_id:
        return dict(sheet_row=sheet_row, name=name, phone=phone_kelsa,
                     status='Failed', kelsa_url='', lead_id=0,
                     detail=f'Draft not materialized: {lt[:200]}')

    url = f'https://app.kelsa.io/5/leads?current_item_id={lead_id}'

    # --- Step 4: Date note ---
    if date_str:
        n1 = f"Contact received on {date_str}. Uploaded to system on 22/07/2026."
        try:
            await session.call_tool('add_note', arguments={'lead_id': lead_id, 'text': n1})
        except Exception:
            pass
        await asyncio.sleep(0.3)

    # --- Step 5: Remarks note ---
    if remarks and remarks.upper() not in ('NA', 'N/A', 'NONE', ''):
        try:
            await session.call_tool('add_note', arguments={
                'lead_id': lead_id, 'text': f"Remarks: {remarks}"
            })
        except Exception:
            pass
        await asyncio.sleep(0.3)

    return dict(sheet_row=sheet_row, name=name, phone=phone_kelsa,
                 status='Added', kelsa_url=url, lead_id=lead_id,
                 detail=f'Created lead #{lead_id}')


async def main():
    if len(sys.argv) < 3:
        print("Usage: batch_import_leads.py <chunk_file.json> <output.json>")
        sys.exit(1)

    chunk_file, output_file = sys.argv[1], sys.argv[2]

    with open(chunk_file) as f:
        cd = json.load(f)

    rows = cd['chunk']
    start = cd.get('start_index', 0)
    sc = cd.get('source_config', {
        'source': 'I Am Here Software Labs',
        'sourcedetails': 'Meta',
        'channel': 'DigitalAds',
        'project': 'Ranka udaya'
    })

    print(f"Processing {len(rows)} leads (chunk offset={start})...")

    token = get_valid_access_token('7449813913')
    results, stats = [], {'Added': 0, 'Already Exists': 0, 'Failed': 0}

    http_client = httpx.AsyncClient(
        headers={'Authorization': f'Bearer {token}'},
        timeout=httpx.Timeout(30.0, connect=10.0)
    )

    try:
        async with streamable_http_client('https://kelsa.io/mcp', http_client=http_client) as streams:
            rs, ws, _ = streams
            async with ClientSession(rs, ws) as session:
                await session.initialize()
                btime = time.time()
                for i, row in enumerate(rows):
                    srow = start + i + 3  # sheet row (3 = first data row)
                    r = await process_lead(session, row, srow, sc)
                    results.append(r)
                    stats[r['status']] = stats.get(r['status'], 0) + 1

                    elapsed = time.time() - btime
                    rate = (i + 1) / elapsed if elapsed > 0 else 0
                    icon = {'Added': '✅', 'Already Exists': '⏭️', 'Failed': '❌'}[r['status']]
                    print(f"{icon} [{i+1}/{len(rows)}] Row {srow} | {r['name'][:25]:25s} | "
                          f"{r['status']:15s} | {r.get('detail', '')[:60]}")

                    if (i + 1) % 10 == 0:
                        with open(output_file, 'w') as f:
                            json.dump({'results': results, 'stats': stats, 'progress': f'{i+1}/{len(rows)}'}, f)

                print(f"\n{'='*60}")
                print(f"Chunk done | {time.time()-btime:.0f}s | "
                      f"Stats: ✅ {stats.get('Added',0)} | ⏭️ {stats.get('Already Exists',0)} | ❌ {stats.get('Failed',0)}")
    finally:
        await http_client.aclose()

    with open(output_file, 'w') as f:
        json.dump({'results': results, 'stats': stats, 'completed': True}, f, indent=2)


if __name__ == '__main__':
    asyncio.run(main())
