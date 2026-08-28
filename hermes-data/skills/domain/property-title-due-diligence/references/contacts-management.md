# DRAAS Employee Contacts & Account-Switch Ops

## Contacts master sheet — CRITICAL STRUCTURE (gotcha)
- Sheet: **NDR DRAAS Google contacts.csv**, ID `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`
- **4,222 rows × 93 columns.** Fetch the FULL range (`A1:CO4222`) — a `A1:Z1000` or `A1:AS1000` fetch silently MISSES rows beyond 1000 and email/phone columns beyond 26. Searching only the first 1000 rows returns "not found" for employees added later (Neha was row 4218).
- Column layout (1-indexed): name = 1-3; Org = 11, Title = 12, Dept = 13; Notes = 15; **E-mail 1 Label=18, Value=19; E-mail 2 Label=20, Value=21; E-mail 3=22/23; E-mail 4=24/25; E-mail 5=26/27**; Phone 1 Label=28, Value=29; Phone 2=30/31; Address City=43, Region=45.
- Label convention: work email row has E-mail 1 Label = `Work`; private = `Personal`. Keep both; the work account is canonical (see below).
- Known rows: Sai Neha Vaddadi (Content Creator, DRA Realty, reports to Gowri Singh, part of content@draas.com) = row 4218 — work `nvaddadi@draas.com`, personal `esotericarts.ani@gmail.com`, +91 7899398273, Bangalore/Karnataka.

## Google Contacts (People API) update pattern
- Search: `people.people().searchContacts(query="<name>", readMask="names,emailAddresses,phoneNumbers,memberships,metadata")` — returns `people/<id>` resourceName.
- Update (must pass etag from a prior get/update): `people.people().updateContact(resourceName=..., updatePersonFields="emailAddresses", body={"etag": person.get("etag"), "emailAddresses": [{"value": ..., "type": "work"}, {"value": ..., "type": "personal"}]})`.
- Gotcha: the same email can exist twice with casing variants (`nVaddadi@draas.com` vs `nvaddadi@draas.com`) — one typed, one untyped. Normalize to ONE canonical lowercase value with `type: work`; the untyped duplicate gets dropped by the update.
- Sheets updates: `spreadsheets().values().update(... valueInputOption="USER_ENTERED")` with a single-cell range like `S4218`.

## Drive permission swap when an employee's canonical account changes
1. Add new account: `permissions().create(fileId, body={"type":"user","role":"reader","emailAddress": "<work>"}, sendNotificationEmail=True)`.
2. List permissions, find the old private account's permissionId, `permissions().delete(fileId, permissionId, supportsAllDrives=True)`.
3. Verify final list — always re-list after the swap; confirm old gone, new present, owner intact.
4. Update contacts sheet + Google Contacts (mark work as `type: work`) in the same pass.

## Canonical-account rule (user preference)
When the user says "whenever we talk of <Name> use <work account>": save to **user-profile memory** as a declarative fact ("Neha Vaddadi — WORK ACCT = nvaddadi@draas.com (use this for Neha)"). Always address/email that person at the work account afterwards; keep the private address only as secondary. Also update the WhatsApp/phone behavior: messaging still routes to their mobile number, which is unchanged.

## WhatsApp-number resolution via People API (2026-08-06)
When a user asks for a WhatsApp message to someone and you don't have the number in the
contacts sheet, search the **People API by email address** first — it returns phoneNumbers
with a `type` field, including `'Wapp'` (WhatsApp) vs `'mobile'` vs `'home'`:

```python
people = build_service('people', 'v1', service_name='google-draas')
res = people.people().searchContacts(
    query='sunderp_2002@hotmail.com', pageSize=10,
    readMask='names,phoneNumbers,emailAddresses').execute()
# phoneNumbers[].value + phoneNumbers[].type  -> '+919820435939' type 'Wapp'
```

- Query by the person's email (most precise) or full name; the readMask MUST include
  `phoneNumbers` or they come back empty.
- Prefer the number typed `'Wapp'` for WhatsApp links; fall back to `'mobile'`.
- Cross-check the main contacts sheet (id `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`)
  only if People API comes up empty.
- Sundar/Sunder Padmanabhan (Ranka Northstar landowner, Site 4, ~11.43% share):
  sunderp_2002@hotmail.com, WhatsApp +91 98204 35939, mobile +91 93226 50429,
  home +91 22 2521 6549, ICICI Chembur A/c 623901252409 IFSC ICIC0006239.

## Email draft fallback (when gws_skill_bridge is blocked)
`gws_skill_bridge.draft_create` fails if the skills dir is root-owned (`PermissionError ... skills/productivity/google-workspace/scripts/google_api.py`). Fallback — Gmail API directly, DRAFT ONLY (never send):
```python
from email.mime.text import MIMEText
import base64
gmail = gws_auth.build_service('gmail', 'v1', service_name='google-draas')
msg = MIMEText(body); msg["To"]=...; msg["From"]=...; msg["Subject"]=...
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
draft = gmail.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
```
Report the draft id; user reviews and sends from Drafts.
