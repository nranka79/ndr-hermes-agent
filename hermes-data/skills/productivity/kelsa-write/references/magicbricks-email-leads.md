# MagicBricks Email → Kelsa Lead Extraction

**Use case:** Extract buyer enquiries from MagicBricks portal emails and add them as leads in Pipeline 10.

**Email subject format:** `Buyer has contacted you on Magicbricks for - Residential Plot for sale in [location]`

**Sender:** `MagicBricks <info@magicbricks.com>` → lands in `sales1.blr@draas.com` inbox (Bharat's account).

## Email HTML Structure

The body is HTML with this text pattern (extracted by stripping tags):

```
Sender's Name:
[Name]
(Individual)

Mobile:
[10-digit phone]

Email:
[email@example.com]

Message:
I am interested in your property. Please get in touch with me.
```

The extraction script at `scripts/extract_magicbricks.py` finds these fields by scanning text lines after stripping HTML. It looks for exact line matches: `"Sender's Name"`, `"Mobile:"`, `"Email:"`.

## Duplicate Handling

MagicBricks sends a separate email per enquiry. The same person may enquire multiple times. Dedup by **last 10 digits of phone number** — the first occurrence is kept, subsequent ones are skipped.

## Source Mapping

| Kelsa Field | Value |
|-------------|-------|
| Source (`cf_source`) | `Magicbricks` |
| SourceDetails (`cf_sourcedetails`) | `MagicBricks` |
| Channel (`cf_campaign`) | `Portals` |

Portal emails are NOT for the Ranka Udaya project specifically — they may reference different properties. Set the project field to `Ranka udaya` unless the user specifies otherwise. If the user says "check the emails and copy leads" without naming a project, default to Ranka udaya.

## Batch Workflow

```
1. Extract:  python3 scripts/extract_magicbricks.py --max 200 --output /tmp/mb_chunk.json
2. Import:   python3 /data/hermes/scripts/batch_import_leads.py /tmp/mb_chunk.json /tmp/mb_results.json
3. Update Sheet (optional): read results, write columns J+K via sheets_update
```

## Observed Volume

| Batch | Emails | Unique Leads | Added | Already Exists | Failed |
|-------|--------|-------------|-------|----------------|--------|
| Jul 2026 (13-23) | 200 | 136 | 70 | 56 | 10 |

Approx 65% new / 35% existing for MagicBricks enquiries. Throughput is ~0.4 leads/sec due to full create flow on most new leads.

## Known Issues

- **Short names** (Arjun, Rakesh, Mano) — prone to ghost contact conflicts in Pipeline 3429, same as standard sheet import. Marked as Failed, need manual cleanup.
- **"MB User"** — MagicBricks sometimes sends the name as "MB User" when the buyer's name is hidden. Create the lead as-is but flag it for the user.
- **Email-less enquiries** — Some enquiries arrive without an email address (field is empty). Still create the lead with just name + phone.
- **Same phone, different name** — Dedup is by phone only. If the same phone appears with a different name, the second is skipped (likely the same person).
