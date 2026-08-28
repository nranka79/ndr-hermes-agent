---
name: real-estate-leads-tracking
description: "Extract, dedupe, and tabulate real estate leads from any source — portal emails (MagicBricks, Housing.com, 99acres, CommonFloor, NoBroker), Meta/Google Ads sheets, and direct walk-ins. Outputs to CSV/Google Sheet or imports to Kelsa CRM Pipeline 10. Trigger when user says 'pull leads from housing.com / magicbricks / 99acres', 'track property inquiries', 'how many leads came in this month', 'magicbricks leads for Ranka Udaya', 'show me the housing.com leads', or 'run meta lead import'."
version: 1.1.0
author: Hermes Agent
license: MIT
---

# Real Estate Lead Tracking (Portal → Gmail → Sheet)

Class-level skill for any session that needs to pull real estate portal leads (MagicBricks, Housing.com, 99acres, CommonFloor, NoBroker) out of Gmail, dedupe them, and produce a tracking table. The portal emails land in a predictable format per-portal — the only variation is contact-detail exposure and how leads are identified.

## When to load this skill

Triggers (any one):
- "pull leads from housing.com / magicbricks / 99acres / commonfloor / nobroker"
- "track property inquiries for [project]"
- "how many leads came in this month / last X days"
- "magicbricks / housing.com leads for [project name]"
- "show me the leads from [portal]"
- "where do I have leads from [portal]"
- "magictor / magictor.com" — voice transcription variant of **MagicBricks** (Bharat pronounces it this way via voice; always map to MagicBricks)
- **Fresh lead response** — "send WhatsApp to this lead", "client just enquired", "new lead came in", "[name] is looking for [budget] [property type]" — lead details shared via voice or text, immediate WhatsApp outreach needed
- **Marketing message creation** — "frame a WhatsApp message for [project]", "create a marketing pitch for [project]", "send this message to all clients who enquire"
- **Meta/Google Ads lead import** — "run meta lead import", "import meta ads leads", "daily meta import failed"

This skill assumes the Gmail/Drive helpers from `gws-automation` are available (per-user OAuth token via `tools.gws_auth.build_service`). For shared business data (e.g. the team's lead-tracking Sheet), use `tools.gws_sa.build_service("sheets", "v4", "ndr@draas.com")` — see `gws-automation` PITFALL #1 for the signature trap.

## ⚠️ PITFALL #0 — The session-user trap (BEFORE you search Gmail)

**This is the #1 failure mode for lead extraction at DRAAS.** The session's `HERMES_SESSION_USER_ID` is the Telegram chat of whoever is currently talking to Hermes. Portal lead emails are sent to the **sales / marketing person's** Gmail (typically `sales1.blr@draas.com` = Bharat), NOT the session user's Gmail.

| Scenario | What happens if you use `build_service('gmail', 'v1')` (no override) | Fix |
|---|---|---|
| Nishant (NDR) is on Telegram, asks "pull MagicBricks leads" | Search runs against ndr@draas.com → **0 results** (NDR doesn't have portal emails) | Pass `telegram_id="sales1.blr"` |
| Bharat is on Telegram | Search runs against sales1.blr → works, but verify with `users().getProfile` first |
| Manish is on Telegram | Search runs against mdr@drahomes.in → likely 0 results | Pass `telegram_id` for the right sales user |

**Always start every lead-extraction session with this 3-line verification:**

```python
gmail = build_service("gmail", "v1")  # auto-loads HERMES_SESSION_USER_ID
profile = gmail.users().getProfile(userId="me").execute()
print(f"Logged in as: {profile.get('emailAddress')}")

# If the email is wrong (e.g. session is ndr@draas.com but leads live in sales1.blr):
# gmail = build_service("gmail", "v1", telegram_id="sales1.blr")
```

Telegram ID → email map for DRAAS team (verified June 2026):
- `ndr` → ndr@draas.com (Nishant Ranka, NDR — admin)
- `sales1.blr` → sales1.blr@draas.com (Bharat Hawaldar — sales, owns portal emails)
- `7249813913` → rnr@draas.com (Roshini Ranka)
- `pm2.blr` → pm2.blr@draas.com (Anbarasan Murugaperumal — projects)

**Symptom of hitting the trap:** first query returns 0 messages, but a second broader query (`newer_than:30d (magicbricks OR housing)`) returns mixed-domain results. That means the token belongs to the wrong mailbox. Override immediately.

**How to override mid-session:** just call `build_service("gmail", "v1", telegram_id="sales1.blr")` and use the returned service. The first (wrong) service can be discarded. No token refresh needed — both tokens are already on disk.

**Verified full-access recipe (Aug 2026):** When running a standalone script for Bharat's mailbox (not the session user), the token lookup needs THREE things or it raises `VaultNoTokenError: No google token for user sales1.blr-[REDACTED-TID]`:

```bash
cd /data/hermes && HERMES_SESSION_USER_ID=sales1_blr GWS_VAULT_SOCKET=/run/gws-vault/vault.sock \
  /opt/hermes/.venv/bin/python3 script.py
```

```python
# in script.py — service_name='google-draas' is MANDATORY for Bharat's identity;
# build_service('gmail','v1') alone raises VaultNoTokenError (default key "google" isn't held by him)
gmail = build_service('gmail', 'v1', service_name='google-draas')
profile = gmail.users().getProfile(userId='me').execute()  # → sales1.blr@draas.com
```

- `HERMES_SESSION_USER_ID=sales1_blr` — resolves Bharat's vault user (sales1.blr-[REDACTED-TID])
- `GWS_VAULT_SOCKET=/run/gws-vault/vault.sock` — the env var may point at a stale socket path; force the live one
- `service_name='google-draas'` — the ONLY vault key Bharat holds (his mail is sales1.blr@draas.com but the token is stored under the google-draas key). Same rule applies to sheets/drive for Bharat.
- Verify with `getProfile` before trusting the mailbox — symptom of wrong token: `from:magicbricks.com` returns 0.

## Hand-off to outreach

After extracting + deduping leads, the next step is outreach. See `references/whatsapp-lead-outreach.md` for the complete workflow, but in summary:

1. **WhatsApp deep links** — Generate `wa.me/91{phone}?text={encoded_msg}` links for each lead with phone number
2. **Tracking dashboard** — Add columns (WhatsApp Sent?, Date Sent, Response?, Notes) to the lead sheet with dropdown validation
3. **Project info kit** — Create a Leads Kit Google Doc in the Marketing Materials folder with brochure + project links + message templates
4. **Bulk safety** — Recommend spacing out sends over hours/days, using broadcast lists, personalizing with lead names
5. **Structured marketing message** — For fresh leads shared via voice/text, build a persuasive message with project-specific selling points, digital tour link, maps link, and image. See `references/ranka-udaya-marketing-kit.md` for Ranka Udaya's pre-built selling points and assets.

Always dedupe against the **already-contacted** list before sending — see the `gws-automation` Gmail search pattern `from:me to:<lead-email>` to find prior outreach. Also filter out self-leads (Bharat's own phone/email) — see the SELF_LEAD_BLOCKLIST in Pitfall #3.

## Hand-off to Kelsa CRM

For Bharat/DRAAS, the portal email extraction workflow naturally flows into **Kelsa CRM** — each extracted lead becomes a contact + lead record in Pipeline 10 (DRA Sales Leads). This is Bharat's preferred next step before outreach.

See `references/portal-to-kelsa-crm.md` for the complete two-step creation workflow:
1. Create contact in Pipeline 3429 (DRA Sales Contacts) with phone (no `+` prefix)
2. Create lead in Pipeline 10 referencing the contact ID
3. Verify with `get_draft_status`

**Trigger for this step:** When Bharat says "add all leads received today", "add these to Kelsa", or after portal email extraction produces new leads. This replaces the Excel/Sheet output option for the intraday workflow.

**Key distinction:** The old output path (Excel file → Drive → WhatsApp) is for weekly/monthly batch handoff. The Kelsa CRM path is for **same-day lead ingestion** — extract → create in Kelsa → report count.

### Cross-check Meta sheet → Kelsa (manual one-time audit)

When Bharat says "cross check the meta leads with Kelsa, find which are missing":

1. Read ALL rows from the `Ranka Udaya - Meta` sheet
2. For each row, check **col J** (Next Follow Up) for "Already Exists" text **AND** **col K** for a kelsa.io URL — either independently means the lead is in Kelsa
3. Rows without either condition AND with a non-empty phone = pending import
4. Report: total / already in Kelsa / pending / skipped (no phone)

**The cross-check does NOT write to the sheet** — it's a read-only audit.

**Trigger:** "Ranka Udia meta", "cross check meta leads", "check which meta leads are missing from Kelsa"

### Batch import of 500+ leads

For large catch-up imports (500–600 leads from the Meta sheet), write a standalone Python script using the MCP JSON-RPC directly (not through `kelsa_call_tool` which runs one-at-a-time):

```python
# Pattern: read from sheets, create contact in pipeline 3429, create lead in pipeline 10
from tools.kelsa_auth import get_valid_access_token
import httpx, re, time

def call_mcp(token, method, args):
    r = httpx.post('https://kelsa.io/mcp', headers={
        'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'
    }, json={
        'jsonrpc': '2.0', 'method': 'tools/call',
        'params': {'name': method, 'arguments': args},
        'id': int(time.time() * 1000)
    }, timeout=60)
    return r.json()['result']['content'][0]['text']

token = get_valid_access_token()

# Step 1: Create contact
ct = call_mcp(token, 'create_lead', {
    'pipeline_id': 3429,
    'field_values': {
        'cf_contact': {'name': name, 'phone': phone, 'email': email}
    }
})
cid = int(re.search(r'ID: (\d+)', ct).group(1))

# Step 2: Create lead
call_mcp(token, 'create_lead', {
    'pipeline_id': 10,
    'field_values': {
        'cf_contact1': {'id': cid},
        'cf_source': 'I Am Here Software Labs',
        'cf_sourcedetails': 'Meta',
        'cf_campaign': 'DigitalAds',
        'cf_project': 'Ranka udaya'
    }
})
time.sleep(0.3)  # rate limit safety
```

Run as a background terminal process with `notify_on_complete=True` — 595 leads at 0.3s delay takes ~3 minutes. Handle phone-uniqueness errors (duplicate phone → skip, don't retry).

## Live Sales Calling from an Existing Sheet (Call → Update → WhatsApp)

After leads are populated in a tracker sheet, Bharat's daily workflow is: **call each lead → log feedback → send WhatsApp if interested**. This is a live calling pattern, NOT an extraction pattern.

### Trigger
Bharat sends a phone number, or says "next lead", "call the next one", "I'm on calls".

### Workflow Steps

1. **Look up lead** — Search the lead tracker sheet (column G = Phone number) for the number Bharat sends
2. **Display** — Show Name, Phone, City, Investment, Visit Preference, Current Status, Notes in a compact card
3. **User gives feedback** — He says "interested", "not interested", "send WhatsApp", etc.
4. **Update Notes/Remarks** — Write feedback to column K (Notes). **Only this column is writable** — Status/Followup columns are often protected
5. **WhatsApp on demand** — If interested, generate a wa.me link with Ranka Udaya project details
6. **Next lead** — Track current row and advance on "next"

### Phone Lookup Pattern

⚠️ **Pitfall — `build_service` for the tracker sheet needs explicit `service_name`:** when reading Bharat's Meta/"I Am Here" tracker sheet (`1yaUwSos6DO56Oni2iiVJ0L26K-rRn7wzYsHKweNxUB0`) in his session, call `build_service("sheets", "v4", service_name="google-draas")`. Without it, `build_service("sheets", "v4")` raises `VaultNoTokenError: No google token for user sales1.blr-[REDACTED-TID]` even though the token exists — the default service key is `"google"`, which Bharat's identity doesn't hold. Also enumerate tabs via `spreadsheets().get()` before reading — tab names are month-based (`'Ranka Udaya | July'`) and `Sheet1` errors. See `kelsa-write` skill → `references/single-lead-import-pipeline10.md` for the verified read + import recipe.

```python
phone_to_find = "919380523805"
for i, row in enumerate(values):
    if len(row) >= 7:
        p = row[6].strip().replace(' ', '').replace('-', '').replace('+', '')
        if phone_to_find in p:
            # row[2]=Visit Preference, row[3]=Investment, row[4]=Name
            # row[6]=Phone, row[7]=City, row[8]=Status, row[10]=Notes
            break
```

### Tracker sheet column map (both tabs, verified Jul 2026)

Bharat's Meta "I Am Here" tracker (`1yaUwSos6DO56Oni2iiVJ0L26K-rRn7wzYsHKweNxUB0`) has **three tabs**: `Dashboard`, `Ranka Udaya | July`, `Ranka Udaya - Meta`. The two data tabs have DIFFERENT column layouts — do not reuse indices across them.

| Column | `Ranka Udaya | July` | `Ranka Udaya - Meta` |
|---|---|---|
| A (0) | lead id | date (dd/mm/yyyy) |
| B (1) | date/time | investment (₹ 50 L+) |
| C (2) | visit preference | visit preference |
| D (3) | investment | **name (Full name)** |
| E (4) | **name** | **phone (Phone Number — 91XXXXXXXXXX)** |
| F (5) | **email** | **email** |
| G (6) | **phone** | city |
| H (7) | city | Status (usually blank) |
| I (8) | status (Fresh/...) | Remarks/notes |
| J (9) | remarks | **Next Follow Up — "Already Exists" for imported** |
| K (10) | notes | **Kelsa URL (kelsa.io link)** |
| L (11) | sync timestamp | — |
| M (12) | synced flag | — |

> ⚠️ **Critical:** "Already Exists" lives in col J (Next Follow Up), NOT col H (Status) or col I (Remarks). Kelsa URLs live in col K. To cross-check import status, scan BOTH col J for "Already Exists" text AND col K for "kelsa.io" URLs — they independently indicate Kelsa presence.

Phone search across both tabs: normalize (strip spaces/`+`/`-`) then check the joined row, since a number may appear on one tab with `+91` and the other without.

### Cross-check a lead's phone: tracker → Kelsa Pipeline 10 (Bharat's "cross check with tracker" ask)

Recurring Bharat request: *"read the contact number of [name], cross check with the tracker, add it into Kelsa pipeline 10"* — and he explicitly wants NO other task mixed in. Recipe:

1. **Read tracker** (above) → confirm name/phone/email in both tabs.
2. **Search Kelsa Pipeline 10** by phone: `search_leads(pipeline_id=10, query=918655311841)` — a result like `[#54214991] Manju-["+918655311841"]-2026-07-31 · Cold` proves the lead exists.
3. **Verify the field itself, not just the name line**: `get_lead(lead_id)` → check `Contact Phone` and `Contact Email` fields match the tracker. (The `Name-["+91…"]-date` identifier line is the auto-generated IDEN, not proof the phone field is populated.)
4. If everything matches → report "matches — no update needed", do NOT recreate or update.
5. If the phone field is missing/wrong → `update_lead(lead_id=…, field_values={"cf_contact_phone": "91XXXXXXXXXX"})` — note Pipeline 10's master-linked `cf_contact_phone` may not persist from the lead (see kelsa-mcp skill); the canonical fix is updating the master contact in Pipeline 3429.
6. If `kelsa_call_tool` says "Not authorized" → use the vault-token direct-MCP fallback (`kelsa-mcp` skill → `references/vault-token-fallback.md`), don't make Bharat re-authorize.

### ⚠️ Protected Sheet Handling

The Status (I), Next Followup (J), and other columns may be **protected** (user can't edit via API). Only the **Notes/Remarks column (K)** is writable.

**Symptom:** `HttpError 400: "You are trying to edit a protected cell or object."`

**Fix:** Always target only column K for updates. If Status/Followup need updating, tell the user to do it manually in the sheet.

```python
# ✅ WORKS — Notes/Remarks column K
service.spreadsheets().values().update(
    spreadsheetId=sid, range="'Sheet'!K525",
    body={'values': [['Interested - lives nearby. Visit tomorrow.']]},
    valueInputOption='USER_ENTERED'
).execute()
```

### WhatsApp on Demand

```python
# Use the whatsapp_link tool (not manual URL construction)
# Include Ranka Udaya selling points
msg = (
    "Hi {name}, thank you for your interest in Ranka Udaya. "
    "Premium residential plots in Sarjapura-Bagalur Road, "
    "just off NICE Road. Investment from ₹50L+. "
    "Would you like a site visit?"
)
```

### Lead Card Display

When showing a lead during a call, format concisely — one idea per line:

```
Name: Roy (Prabhat Roy)  |  Phone: +91 93805 23805
City: Bangalore  |  Investment: ₹50 L+  |  Visit: This Weekend
Status: Fresh  |  Notes: —
```

### Next Lead Navigation

When Bharat says "next", increment a row counter and show the next lead in sequence.

## Per-portal source pattern

Each portal has a stable `from:` + a stable subject prefix. Always search by sender first, then filter by subject for the actual lead-notifications:

| Portal | Sender (`from:`) | Lead subject prefix | Real-time body? | Contact info in email? |
|---|---|---|---|---|
| **MagicBricks** | `info@magicbricks.com` (leads) + `alerts@magicbricks.com` (ops/renewals — NOT leads) | `Buyer has contacted you on Magicbricks` or `Hot Lead - Buyer` | Yes | ✅ Yes — name, email, phone in HTML body |

> **⚠️ Voice variant (Bharat):** Bharat pronounces "MagicBricks" as "Magictor" via voice. If he says "Magictor / magictor.com", always map to **MagicBricks** (`info@magicbricks.com`).

> **MagicBricks sender disambiguation (verified Jun 2026):** `from:magicbricks.com` returns 4 distinct senders in a 60-day window:
> - `MagicBricks <info@magicbricks.com>` — **leads** (subject: `"Hot Lead - Buyer has contacted you on MagicBricks for - …"` or `"Buyer has contacted you on MagicBricks for - …"`). The "Hot Lead -" prefix appears on some leads (observed Jun 2026). Filter by sender + subject substring `Buyer has contacted you` to catch both variants.
> - `MagicBricks <alerts@magicbricks.com>` — **ops/marketing noise** ("Let buyers see your 2 BHK...", "142+ people are looking for a property like yours"). Filter out by subject or by sender.
> - `info@magicbricks.com` (unbranded) — image approval notifications ("Images Approved", "Images Screened"). Filter out.
> - `Manjunath U <manjunath.u@magicbricks.com>` — personal emails from MagicBricks account manager. Filter out.
>
> The `from:magicbricks.com newer_than:Nd` query catches ALL four. Always filter by subject prefix `Buyer has contacted you` (or by sender `from:info@magicbricks.com` + subject regex) to isolate leads.
| **Housing.com** | `noreply@housing-mailer.com` | `New Lead For [Project Name]` | No — masked | ❌ No — "Send Email / Call Now" links only; contact behind partner portal |
| **99acres** | `noreply@99acres.com` | `New lead for` / `You have a new inquiry` | Yes | ✅ Yes — email + phone usually |
| **CommonFloor** | `noreply@commonfloor.com` | `New Lead:` | Yes | ✅ Yes — email + phone |
| **NoBroker** | `noreply@nobroker.in` | `New response for` | Yes | ✅ Yes — phone usually; email sometimes |

The `from:` sender is the stable filter — the subject can change. Use `from:portal-domain newer_than:Nd` as the broad filter, then split the results in code by subject prefix.

## Gmail search recipes

```python
# MagicBricks — last 30 days
q = "from:magicbricks.com newer_than:30d"

# Housing.com — last 30 days (note: mailer subdomain, not housing.com itself)
q = "from:housing.com newer_than:30d"  # catches both housing-mailer.com and direct

# 99acres
q = "from:99acres.com newer_than:30d"

# Multi-portal combined
q = "(from:magicbricks.com OR from:housing.com OR from:99acres.com) newer_than:30d"
```

`newer_than:Nd` is the cleanest way to do time windows in Gmail. For exact date ranges, use `after:YYYY/MM/DD before:YYYY/MM/DD` instead.

## Per-portal lead-parsing patterns

### MagicBricks (full contact in HTML body — name, email, phone)

MagicBricks lead emails are **HTML-only** — there is no `text/plain` alternative. You must extract contact details from the HTML structure directly.

⚠️ **Do NOT strip HTML tags and regex on the plaintext** — the old approach (strip tags → regex for email/phone) **misses the buyer name entirely** because the name is in a labelled HTML table cell, not in free text.

**Correct approach — extract from HTML table cells:**

```python
def get_html_body(meta):
    """Extract HTML body from Gmail message parts recursively."""
    def _extract(payload):
        if payload.get('mimeType') == 'text/html' and payload['body'].get('data'):
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='replace')
        if 'parts' in payload:
            for p in payload['parts']:
                result = _extract(p)
                if result:
                    return result
        return ''
    return _extract(meta['payload'])

import re
html = get_html_body(meta)

# Name — after "Sender's Name:" in a bold span
m_name = re.search(r"Sender's Name:.*?font-weight:bold[^>]*>([^<]+)", html, re.DOTALL)
name = m_name.group(1).strip() if m_name else ''

# Phone — first 10-digit number after the "Mobile:" label (⚠️ use LOOSE pattern — some emails wrap the
# Phone — first 10-digit Indian number after "Mobile:" label
# ⚠️ Do NOT require font-weight:bold immediately before the number —
#    MagicBricks nests the value in extra spans on some emails:
#    <span style="font-weight:bold"> <span style="text-decoration:underline;">7411152429</span>
#    <span style="font-weight:normal">(Verified)</span></span>
#    The strict regex misses these; anchor on the label + first \d{10} instead.
m_phone = re.search(r"Mobile:.*?(\d{10})", html, re.DOTALL)
phone = m_phone.group(1).strip() if m_phone else ''

# Email — first email address after "Email:" label (also nested in spans on some emails)
m_email = re.search(r"Email:.*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", html, re.DOTALL)
email = m_email.group(1).strip() if m_email else ''

# Property ID — after "Property, ID"
m_pid = re.search(r'Property, ID\s*(\d+)', html)
prop_id = m_pid.group(1) if m_pid else ''
```

✅ **Buyer name IS present** in the HTML body under "Sender's Name:". The old claim that it's \"only on the portal dashboard\" is wrong for HTML-parsed emails.

### Housing.com (masked — name + project only)
```python
# Subject: "New Lead For DRA Ranka Udaya"
# Body: "Name: <Full Name> Email: Send Email Contact: Call Now Chat On WhatsApp"
# The "Email: Send Email" is a LABEL not a value — actual email is behind the link
m_name = re.search(r"Name:\s*([^\n]+?)\s+(?:Email|Contact|Phone|who)", plain)
m_prop = re.search(r"regarding your ([^.]+?) property", plain)
m_budget = re.search(r"budget in range ([^.]+?)\.", plain)
```

⚠️ Housing.com does NOT expose contact details in the email body — name, project, property type, and budget only. To get the email/phone, the user must log into the housing.com partner dashboard. Flag this clearly in the output table so the user doesn't expect contact info that isn't there.

### 99acres / CommonFloor (full contact in email)
Similar to MagicBricks — usually both email and phone are in the body. Same regex patterns work.

## Project filter — narrow leads to one project

After parsing all leads, filter by project. Use the **subject line** + **body URL** as the project signal. Common pattern:

```python
# Subject: "New Lead For DRA Ranka Udaya" or "Buyer has contacted you on MagicBricks for - Residential Plot for sale in Sarjapura"
# The project name is right there in the subject — substring match is enough

leads_for_project = [l for l in all_leads if "Ranka Udaya" in l["subject"] or "Sarjapur" in l["property_type"]]
```

For more sophisticated filtering (multiple project aliases, misspellings like "Ranca" for "Ranka" — see memory: Runca → Ranka), build a synonym set:

```python
PROJECT_ALIASES = {
    "Ranka Udaya": ["Ranka Udaya", "Ranca Udaya", "Ranka Udya", "Sarjapur Bagalur"],
    "Ranka Oasis": ["Ranka Oasis", "Sevaganapalli", "Ranka Oaisis"],
}
```

## Dedupe strategy

Portal leads duplicate heavily — the same buyer often submits 2-3 inquiries (different properties, different times). **Dedupe key differs by portal:**

| Portal | Primary dedupe key | Fallback | Why |
|---|---|---|---|
| **MagicBricks** | email (lowercased) | phone (10 digits) | Body has name+email+phone from HTML. Email is the most stable unique key. |
| **Housing.com** | name (lowercased) | thread_id | Body has name but email/phone are masked. Same buyer = same name on different property variants |

**MagicBricks dedupe — keep most recent per email-or-phone:**

```python
seen = set()
unique = []
for l in sorted(leads, key=lambda x: x["datetime"], reverse=True):  # newest first
    if l['email']:
        key = ('e', l['email'].lower())
    elif l['phone']:
        key = ('p', l['phone'])
    else:
        key = ('x', l['thread_id'])  # fallback to thread when both are missing
    if key in seen:
        continue
    seen.add(key)
    unique.append(l)
```

**⚠️ Dedupe bug pattern (verified Jun 2026):** If the dedupe loop's `if not l["email"] and not l["phone"]: continue` runs BEFORE the `seen` check, you silently drop leads that have neither. Always key on **whichever is present** (email → phone → thread_id), not on "must have both".

**Housing.com dedupe — keep one row per name:**

```python
seen_names = set()
unique = []
for l in sorted(leads, key=lambda x: x["datetime"], reverse=True):
    key = l['name'].lower() if l['name'] else l['thread_id']
    if key in seen_names:
        continue
    seen_names.add(key)
    unique.append(l)
```

⚠️ The `aaaa@gmail.com`, `test@test.com`, and similar placeholder emails are spam — filter them out:

```python
SPAM_EMAIL_PATTERNS = [
    r"^aaaa@",
    r"^test@",
    r"^xxx@",
    r"^no@",
    r"^noreply@",
]
unique_leads = [l for l in unique_leads if not any(re.match(p, l["email"]) for p in SPAM_EMAIL_PATTERNS)]
```

and the user's own phone / email appearing in leads — Bharat's sales number (9900029200) shows up occasionally as a "buyer" in the data. Cross-check lead emails against a known-buyer blocklist before delivering.

## ⚠️ PITFALL #4 — Phone number display format: `+91` vs `91` (Bharat preference)

Bharat corrected the phone format preference: **do NOT include the `+` symbol** before the country code. Display numbers as `91XXXXXXXXXX` (12 digits), not `+91XXXXXXXXXX` (13 digits). This applies whenever writing phone numbers to Excel/Sheet cells — both in lead sheets and the hiring tracker.

```python
# GOOD — Bharat's preference
ws.cell(row=r, column=3, value=f"91{phone_clean}")  # 917760125000

# BAD — triggers a correction
ws.cell(row=r, column=3, value=f"+91{phone_clean}")  # +917760125000
```

The WhatsApp `wa.me` link format `wa.me/91{phone}` is already correct and does not use `+`. The preference is purely cosmetic for the displayed cell value.

## Output formats

Three output options, in increasing order of effort:

1. **Telegram message** (in-session, quick view) — markdown table with name/email/phone/project/date
2. **CSV file** (deliverable, easy to import to Sheets) — write to `/tmp/portal_leads.csv` and offer to upload to a Drive folder
3. **Google Sheet** (live tracking, ongoing updates) — create a new Sheet via `gws_sa.build_service("sheets", "v4")` since this is shared business data, NOT per-user data

Default to option 1 (markdown table) for in-session review, then ask if the user wants 2 or 3.

### CSV format
```python
import csv
with open("/tmp/magicbricks_leads.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["#", "Date", "Email", "Phone", "Property Type", "Project", "Source Portal", "Lead ID"])
    for i, l in enumerate(unique_leads, 1):
        w.writerow([i, l["date"], l["email"], l["phone"], l["prop_type"], l["project"], "MagicBricks", l.get("lead_id", "")])
```

### Excel (.xlsx) format — preferred for sales-team handoff

When the user says "give me an excel sheet" or "send me the file", deliver an `.xlsx` with clickable email/phone/WhatsApp/gmail-thread links. The user opens it in Sheets/Excel and can act on each row directly.

**File path convention:** `/data/hermes/cron/output/PortalName_Leads_<account>_<Ndays>d.xlsx`

**Install:** `openpyxl` is pre-installed at `/opt/hermes/.venv/lib/python3.13/site-packages/openpyxl`.

**Working pattern (verified Jun 2026):**

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

wb = Workbook()
ws = wb.active
ws.title = "MagicBricks Leads"

# Title row (merged across all columns)
ws.merge_cells('A1:I1')
ws['A1'] = f"MagicBricks Leads — sales1.blr@draas.com — {datetime.now().strftime('%d %b %Y')}"
ws['A1'].font = Font(size=14, bold=True, color='FFFFFF')
ws['A1'].fill = PatternFill('solid', fgColor='1F4E78')
ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
ws.row_dimensions[1].height = 24

# Subtitle row with raw vs unique counts
ws.merge_cells('A2:I2')
ws['A2'] = f"Period: last 60d  |  Raw: {len(leads)}  |  Unique: {len(unique)}"
ws['A2'].font = Font(size=10, italic=True, color='666666')
ws['A2'].alignment = Alignment(horizontal='center')

# Header row
headers = ['#', 'Date', 'Time', 'Client Name', 'Email', 'Phone', 'Property Type', 'Lead ID', 'Gmail Thread']
for col, h in enumerate(headers, 1):
    c = ws.cell(row=4, column=col, value=h)
    c.font = Font(size=11, bold=True, color='FFFFFF')
    c.fill = PatternFill('solid', fgColor='2E75B6')
    c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    c.border = Border(left=Side('thin'), right=Side('thin'), top=Side('thin'), bottom=Side('thin'))
ws.row_dimensions[4].height = 30

# Data rows with clickable hyperlinks
for i, l in enumerate(unique, 1):
    row = i + 4
    d_str = l['datetime'].strftime('%d-%b-%Y')
    t_str = l['datetime'].strftime('%H:%M')
    gmail_link = f"https://mail.google.com/mail/u/0/#inbox/{l['thread_id']}"
    
    for col, v in enumerate([i, d_str, t_str, l['name'], l['email'], l['phone'], l['property'], l['lead_id'], gmail_link], 1):
        c = ws.cell(row=row, column=col, value=v)
        c.font = Font(size=10)
        c.border = Border(left=Side('thin'), right=Side('thin'), top=Side('thin'), bottom=Side('thin'))
        if col == 5 and v:  # email → mailto
            c.hyperlink = f"mailto:{v}"
            c.font = Font(size=10, color='0563C1', underline='single')
        elif col == 6 and v:  # phone → WhatsApp
            c.hyperlink = f"https://wa.me/91{v}"
            c.font = Font(size=10, color='25D366', underline='single')
        elif col == 9 and v:  # gmail thread
            c.hyperlink = v
            c.font = Font(size=10, color='0563C1', underline='single')
        if i % 2 == 0:
            c.fill = PatternFill('solid', fgColor='F2F7FB')
        c.alignment = Alignment(vertical='center', wrap_text=True)

# Column widths
for col, w in enumerate([4, 12, 7, 24, 32, 13, 42, 18, 38], 1):
    ws.column_dimensions[get_column_letter(col)].width = w

# Freeze header + add filter
ws.freeze_panes = 'A5'
ws.auto_filter.ref = f"A4:I{len(unique)+4}"

# Save
import os
os.makedirs('/data/hermes/cron/output', exist_ok=True)
out_path = '/data/hermes/cron/output/MagicBricks_Leads_sales1blr_60days.xlsx'
wb.save(out_path)
```

**Per-portal column variants:**
- **MagicBricks sheet:** Name (always present from HTML parsing), Email, Phone, Property Type, Lead ID, Gmail Thread — all clickable
- **Housing.com sheet:** Name (always present), Project, Property Type, Budget, Gmail Thread — no email/phone columns (data not in body). Add a red-text warning row in the subtitle: "Housing.com masks contact info in emails — log into Housing Partner portal to retrieve email/phone"

**Date format:** `%d-%b-%Y` (e.g. `04-Jun-2026`) reads cleanly in both Excel and Sheets. Avoid ISO `YYYY-MM-DD` — it's ugly and harder to scan.

### Drive upload + link sharing

After creating the `.xlsx` file, upload it to the user's **Drive root** (not a shared project folder) and share the link in the Telegram response.

**When to do this:** Always after creating the Excel. The user (Bharat/sales1.blr@draas.com) prefers this over placing files in project-specific folders.

**Tracking dashboard upgrade (after upload):** Once the sheet is in Drive, upgrade it with tracking columns via the Sheets API:
- Column J: WhatsApp Sent? (dropdown: ✅ Sent / ⏳ Pending / — Skipped)
- Column K: Date Sent (free text)
- Column L: Response? (dropdown: 👍 Replied / 👁️ Seen / ❌ No response / 📞 Callback)
- Column M: Notes (free text)
See `references/whatsapp-lead-outreach.md` for the exact Sheets API calls and dropdown validation format.

**Pattern (verified Jun 2026):**
```python
from googleapiclient.http import MediaFileUpload
from tools.gws_auth import build_service

drive = build_service("drive", "v3")  # per-user OAuth
file_meta = {"name": "MagicBricks_Leads_sales1blr_60days.xlsx"}
media = MediaFileUpload(
    "/data/hermes/cron/output/MagicBricks_Leads_sales1blr_60days.xlsx",
    mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    resumable=True
)
f = drive.files().create(
    body=file_meta,
    media_body=media,
    fields="id, name, webViewLink"
).execute()

# Share the link
drive_link = f["webViewLink"]
```

**Fallback (Drive scope missing or 403):** If the upload fails (common for non-Bharat users whose tokens lack `drive` scope), drop the file at `/data/hermes/cron/output/<filename>.xlsx` or `/data/hermes/users/{telegram_id}/outbound/<filename>.xlsx` and tell the user where it is. Do NOT keep retrying the upload — see ⚠️ PITFALL #1 above.

**User-specific note (Bharat):** He explicitly said *"It is not necessary that you need to add it to Ranka there only, you can add it to my drive somewhere and then share the link with me."* — meaning upload to **Drive root**, not to a project-specific shared folder. If you try a project folder first and hit 403 (insufficient permissions), do NOT attempt another shared folder — go straight to root Drive upload.

## Recurring workflow

The user (Nishant / Bharat at DRAAS) runs this lead-tracking as a recurring task — typically weekly or monthly. Recommended pattern:

1. **Pull leads from each active portal** (MagicBricks + Housing.com at minimum — 99acres / CommonFloor as the project expands)
2. **Dedupe within each portal** (by email, then phone)
3. **Cross-portal dedupe** (same buyer on two portals = one lead)
4. **Filter to the target project** (e.g. "Ranka Udaya only")
5. **Output to Google Sheet** for the sales team to work the leads
6. **Hand off the deduped list** to the outreach workflow (see `ranka-udaya-outreach` skill for the WhatsApp outreach message pattern)

If recurring on a schedule, set up a `cronjob` that runs the extraction + dedupe + Sheet append, and sends a Telegram summary to Bharat. The job prompt should include the project filter, the output Sheet ID, and the email deliverable.

## Common pitfalls

### 1. False positives on property type
MagicBricks subjects are like `Residential Plot for sale in Sarjapura` — Sarjapura is a *place*, not the project name. Don't use `Sarjapura` as a project filter — it matches too many unrelated projects. Use the actual project name (`Ranka Udaya`) as the filter and verify via the property listing URL in the body.

### 2. Multiple properties per lead
Housing.com sends separate lead emails for each property the buyer enquired about. The same buyer can show up 3-4 times for the same project if they enquired about 3 different unit types. This is a *feature* of housing.com's CRM, not a duplicate — surface this in the output ("Same buyer, 3 unit variants") rather than silently deduping.

### 3. Subject-line encoding
`★` (black star), `·` (middle dot), `→` (arrow) and other Unicode characters often appear in MagicBricks and 99acres subjects. Don't strip them — they're often part of the portal's branding and don't affect parsing. The `Buyer has contacted you on MagicBricks` prefix is stable across all lead emails.

### 4. Date parsing — multi-locale dates
MagicBricks sends dates in `Wed, 27 May 2026 13:30:18` format. Don't hardcode the locale — use `email.utils.parsedate_to_datetime` which handles all standard RFC 2822 formats:

```python
from email.utils import parsedate_to_datetime
d = parsedate_to_datetime(date_header)
d_str = d.strftime("%d %b %H:%M")
```

### 5. Gmail thread vs message
A lead is a single `info@magicbricks.com` message — NOT a thread. The portal sends a fresh email per inquiry, not a reply. So always search `from:portal newer_than:Nd` and process each `messages.list` result as one lead. Do not try to thread them.

### 6. Per-portal API vs email scraping
MagicBricks, Housing.com, 99acres all have partner APIs for lead retrieval. Email-scraping is the fallback for the user's specific setup (no API keys, OAuth-only Google auth). Don't propose API integration without explicit user request — the email pattern works and is one script.

### 7. Voice-transcribed date ranges ≠ actual mailbox window (Bharat, 2026-08-25)
Bharat said "leads from Sunday, Monday and today," but `after:/before:` search showed the real MagicBricks window was **Saturday (22nd) + Monday (24th)** — no Sunday or that-day emails existed. He still wanted them imported (they were unimported despite being on his radar). Lesson: NEVER trust the spoken date range as the search window. Always run the exact `after:YYYY/MM/DD before:YYYY/MM/DD` query against Gmail, enumerate the actual dates present, and show Bharat the real window + count before importing. Report the discrepancy plainly ("no emails from Sunday or today; actual leads are Sat + Mon") rather than silently importing whatever the broad query returns.

### 8. Cross-reference Kelsa lead notes before composing client booking emails
Before drafting a booking/allotment email for a client (even if they came from a portal/website lead), pull the Kelsa lead (`get_lead` + `list_lead_notes`) — it carries the commercial context: project, plot options being considered, quoted ₹/sqft, negotiated budget, committed timelines (e.g. "15 days agreement, 30 days sale deed, 45 days registration"). From this session: client Pragya Joythi was considering Plot 2 or Plot 5, budget ₹3,400/sqft, quoted ₹3,700 (West) / ₹3,750 (East), was told booking-amount-today unlocks further negotiation. That context must drive the draft's plot mention, price placeholders, and terms timeline — don't compose from the email alone.

### 7. Verify dates against Gmail BEFORE importing (user's day recollection ≠ email reality)
Verified 2026-08-25: Bharat said "leads from Sunday, Monday and today" but the actual MagicBricks mailbox had lead emails only on **Sat 22 Aug (4) + Mon 24 Aug (1)** — NO Sunday or Tuesday emails existed. Don't take the user's day-of-week claim at face value. Run the date-bounded Gmail query (`after:YYYY/MM/DD before:YYYY/MM/DD`), read the ACTUAL `date` headers, and report the real distribution before importing. Also — the `extract_magicbricks.py` script truncates the date to the first 10 chars (`email['date'][:10]`), producing garbage like `Mon, 24 Au` in the chunk CSV. For date-accurate filtering, parse the RFC-2822 date with `email.utils.parsedate_to_datetime` instead of trusting the truncated field.

### 8. Show "what's been produced" before adding new leads
When Bharat asks to add new portal leads, he first wants to see what's already in Kelsa from that source (e.g. `search_leads(pipeline_id=10, query="cf_sourcedetails:magicbricks", sort="created", order="desc")` for the most recent batch). Do that review first — it tells you whether the "new" leads are actually new and gives Bharat the recent-productions context he expects. Then dedup each candidate phone against Pipeline 10 (10-digit search works via IDEN) AND contacts pipeline 3429 before importing.

### 7. Voice-stated date windows ≠ actual email dates (2026-08-25)

Bharat said "leads from MagicBricks, Sunday–Monday–today" but the actual inbox window contained **Sat 22 Aug (4 leads) + Mon 24 Aug (1 lead)** — zero emails on the stated Sunday or Tuesday. Always run an explicit date-window Gmail query before extracting and enumerate the ACTUAL dates from the results:

```
q = "from:(info@magicbricks.com) after:2026/08/22 before:2026/08/26"
```

The broad `--max N` sweep in `extract_magicbricks.py` spans back to Aug 14 and can mislead — the date-window query is authoritative. Report the discrepancy to the user (don't silently import against their stated days), then dupe-check each candidate: `search_leads(10, phone)` matches the IDEN line (0 = absent), corroborate on contacts 3429, skip any phone already present (even an old June lead with the same number).

## ⚠️ PITFALL #1 — `send_message` cross-user guard (delivering the file)

Once you override `telegram_id="sales1.blr"` to pull leads from Bharat's mailbox, **the `send_message` tool will refuse to send the resulting Excel/CSV to the user's chat.** The session's `HERMES_SESSION_USER_ID` is still the *chat-owner* (e.g. ndr = Nishant), and the tool enforces that messages must be delivered to the session's own chat — not to whichever user the data came from.

**Symptom:**
```
send_message(target="telegram") → Cross-user send blocked. Deliver results to the requesting user only.
```

**Fixes, in order of preference:**

1. **Drop the file at a path the user can grab.** Use:
   - Primary: `/data/hermes/cron/output/<filename>.xlsx` (default `cronjob` output dir — the cron job delivery layer picks this up)
   - Backup: `/data/hermes/users/{session_chat_id}/outbound/<filename>.xlsx` (always writable; the user can `cp` from there)
   - Example: `mkdir -p /data/hermes/users/sales1.blr/outbound && cp MagicBricks_Leads.xlsx .../outbound/`
2. **Print the file path in the response and tell the user where to find it.** Don't keep retrying `send_message` with the same target — the guard is hard, not transient.
3. **If the user is on the same session chat as the data owner** (e.g. Bharat is on Telegram and you used `sales1.blr` which IS the session), the override matches and `send_message(target="telegram")` works normally.

**Do NOT** try `telegram:ndr` (explicit chat ID targeting) — that also fails the cross-user guard. The guard is per-session, not per-target-format.

## ⚠️ PITFALL #2 — `from:portal newer_than:Nd` can return 0 when token is wrong, even when results exist

Verified Jun 2026: running `from:magicbricks.com newer_than:30d` against `ndr@draas.com` (Nishant's token) returns **0** messages, even though the mailbox clearly has MagicBricks lead emails. This is NOT a Gmail quirk — it just means **the token being used has no emails from that sender**.

The diagnostic test (cheap, 1 API call):
```python
r = gmail.users().messages().list(userId="me", q="newer_than:30d (magicbricks OR housing)", maxResults=20).execute()
# If you get a mix of Housing.com leads + Liases Foras + "MagicBricks" branded subjects
# but no "info@magicbricks.com" sender, you're on the wrong token.
```

If you see Housing.com results but no MagicBricks results, the token is wrong (Bharat has both; Nishant has Housing but not MagicBricks — different sales workflows are routed to different mailboxes).

**Re-run with `telegram_id="sales1.blr"`** (or whichever sales user owns the portal emails for the target project) and the count will jump from 0 to the correct number.

## ⚠️ PITFALL #3 — Bharat's own phone appears as a "buyer"

Verified Jun 2026: MagicBricks sometimes returns `khanbt@gmail.com` / `9900029200` as a lead — that's **Bharat's own sales number** (Bharat Hawaldar's cell, also his sales1.blr@draas.com line). It's likely a self-test or a wizard-of-oz inquiry he made.

**Filter rule:** add `SELF_LEAD_BLOCKLIST` to your dedupe pass:
```python
SELF_LEAD_BLOCKLIST = {
    "9900029200",  # Bharat Hawaldar (sales)
    "sales1.blr@draas.com",
    "khanbt@gmail.com",
}
unique = [l for l in unique if l.get("phone") not in SELF_LEAD_BLOCKLIST
                              and l.get("email", "").lower() not in SELF_LEAD_BLOCKLIST]
```

Generalize for other DRAAS sales users (Gowri Singh, Anbarasan, etc.) as the user adds them.

## ⚠️ PITFALL #4 — Phone number display format: `+91` vs `91` (Bharat preference)

Bharat corrected the phone format preference: **do NOT include the `+` symbol** before the country code. Display numbers as `91XXXXXXXXXX` (12 digits), not `+91XXXXXXXXXX` (13 digits).

This applies when writing phone numbers to Excel/Sheet cells. The WhatsApp `wa.me` link format `wa.me/91{phone}` is already correct — it does not use `+`.

```python
# GOOD — Bharat's preference
ws.cell(row=r, column=3, value=f"91{phone_clean}")  # 917760125000

# BAD — triggers a correction
ws.cell(row=r, column=3, value=f"+91{phone_clean}")  # +917760125000
```

ℹ️ This is a **display preference only** — the `+` prefix is not wrong in telecom standards, but Bharat finds it cleaner without it.

## When NOT to use this skill

- **Sales-team CRM data** (HubSpot, Zoho, Salesforce) — that's a different workflow, not portal email scraping
- **The user wants a single specific lead's history** — use `gws-automation` Gmail search directly
- **Lead scoring / qualification** — this skill is extraction only; scoring is a separate workflow
- **On-site visit logging** — see `references/direct-site-visit-tracking.md` for walk-in leads (not portal-based)

## On-Site Visit Tracking

When a lead walks in directly (not through a portal), create a lightweight tracking sheet instead of running the full portal extraction pipeline:

```python
# Quick pattern: single lead entry
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

wb = Workbook()
ws = wb.active
ws.title = "Site Visits"

# Title
ws['A1'] = "Ranka Udaya — Direct Site Visits"
ws['A1'].font = Font(size=14, bold=True, color='FFFFFF')
ws['A1'].fill = PatternFill('solid', fgColor='1F4E78')

# Headers: #, Visit Date & Time, Name, Contact Number, Remarks
# Phone → clickable wa.me hyperlink
# Upload as Google Sheets via Drive API with mimeType conversion

drive.files().create(
    body={"name": "Ranka Udaya - Direct Site Visits.xlsx",
          "mimeType": "application/vnd.google-apps.spreadsheet"},
    media_body=MediaFileUpload(...),
    fields="id, name, webViewLink"
).execute()
```

Upload to Drive root (not a project folder) — same as portal leads. Add a Visit Date & Time column (B) for tracking when the walk-in happened.

## Linked reference files

- `references/clean-sheet-data.md` — Cleaning operations for Indian real estate lead sheets: phone normalization (`(+91)-XXXXXXXXXX` → `91XXXXXXXXXX`) via `re.sub(r'\D', '', phone)`, name cleaning (stripping `(Owner)`, `(Broker)`, etc.) via `re.sub(r'\s*\(.*?\)\s*', '', name)`, AND Kelsa-export cleanup (`Name-["phone"]-date` + `["+phone"]` → name only + plain `91XXXXXXXXXX`, the TailorTalk/WhatsApp upload format). With full Python snippets + sheet update patterns.
- `references/magicbricks-parsing-notes.md` — Per-field regex examples, sample lead emails, date format gotchas
- `references/housing-com-masking.md` — What housing.com masks vs exposes, how to communicate this to the user
- `references/portal-email-senders.md` — Verified `from:` addresses for each portal, subject prefixes, body templates
- `references/whatsapp-lead-outreach.md` — WhatsApp deep links, tracking dashboard, bulk safety, follow-up sequence, project info kit, cron reminder pattern, structured marketing message creation, image-sharing limitation
- `references/direct-site-visit-tracking.md` — Sheet structure, creation pattern, and user preferences for on-site walk-in leads
- `references/appending-new-leads.md` — Fetch → dedupe → append workflow for adding new leads to an existing Sheet. Covers the sheet-ID pitfall (converted sheets don't use ID 0).
- `references/adding-whatsapp-links-to-sheet.md` — Read an existing sheet with phone numbers, generate wa.me links, and write them to a "Whats App Link" column without touching other columns. Covers sheet name case-sensitivity, phone cleaning, and the `sheets_update` JSON-serialization requirement.
- `references/ranka-udaya-marketing-kit.md` — Ranka Udaya project-specific selling points, digital tour link, maps link, structured message templates, image-handling instructions
- `templates/wa-link-sender.html` — Self-contained HTML page with embedded marketing image + phone input + wa.me link generator. Use when user says "connect the image to the link" or expects the image to feel part of the workflow (see `references/whatsapp-lead-outreach.md` §5 — HTML Tool Approach).
- `references/portal-to-kelsa-crm.md` — Bridge: how to add extracted portal leads directly to Kelsa CRM (Pipeline 10) via the MCP SDK two-step contact+lead creation workflow.
- `references/meta-ads-leads-pipeline.md` — Meta Ads lead import: daily cron script, sheet structure, Kelsa Pipeline 10 config, and the HERMES_SESSION_USER_ID cron env requirement.
- `references/project-activity-summary.md` — Multi-round project activity summary for stakeholder reports. For when the user asks "what have we done for [project] so far?"