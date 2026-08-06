# Single-Lead Import to Pipeline 10 (verified 2026-07-31)

Use when the user gives ONE contact (phone + optional name/email/budget) from a
tracker sheet and asks to add it to Kelsa **DRA Sales Leads (Pipeline 10)**.

## Prerequisites
- Working Kelsa token. In cron/auto sessions use:
  `HERMES_SESSION_USER_ID=7449813913 GWS_VAULT_SOCKET=/run/gws-vault/vault.sock`
  (ndr-7449813913 holds `mcp-kelsa-read`). See SKILL.md identity pitfall.
- Connect pattern (terminal only, not execute_code):
  ```python
  from tools.kelsa_auth import get_valid_access_token
  from tools.kelsa_tool import _connect_and_run
  from tools.mcp_tool import _ensure_mcp_loop, _run_on_mcp_loop
  token = get_valid_access_token()
  # _ensure_mcp_loop(); _run_on_mcp_loop(op(), timeout=60)
  ```

## Steps (all verified)
0. **Read the tracker sheet (Google Sheets)** — the lead details live in the
   "I Am Here Software Labs" / Meta tracker sheet
   (`1yaUwSos6DO56Oni2iiVJ0L26K-rRn7wzYsHKweNxUB0`). ALWAYS pass the explicit
   service name:
   ```python
   from tools.gws_auth import build_service
   sheets = build_service("sheets", "v4", service_name="google-draas")
   ```
   ⚠️ **Pitfall (verified 2026-07-31):** calling `build_service("sheets", "v4")`
   WITHOUT `service_name="google-draas"` raises
   `VaultNoTokenError: No google token for user sales1.blr-8717455402` — even
   though the token EXISTS under `google-draas`. The default service_name is
   `"google"`, which Bharat's identity doesn't hold. The error is misleading;
   the fix is simply passing `service_name="google-draas"`.
   ⚠️ **Tab names are month-based and contain spaces/pipes** — do NOT assume
   `Sheet1` (that range errors with "Unable to parse range"). Enumerate tabs
   first via `sheets.spreadsheets().get(...)`, then read the month tab, e.g.
   `range="'Ranka Udaya | July'!A1:Z2000"` (single-quote the tab name). Verified
   tabs (Jul 2026): `Dashboard`, `Ranka Udaya | July` (live portal tab), `Ranka
   Udaya - Meta`. Header of live tab: Lead ID, Lead Date, site-visit pref,
   investment, Full name, Email, Phone number, City, Status, Next Followup,
   Notes, Last Synced, Sync Status — phone is in column G (index 6). The raw
   Meta tab has a different header order (date, budget, pref, name, phone,
   email, city) — phone at index 4.
1. **Dedup** — search contacts pipeline 3429 by phone (`8861926482` style, last
   10 digits) and by full `91XXXXXXXXXX`; also search Pipeline 10 by phone
   (returns 0 even when the lead exists — phone is master-linked, so contact
   search is the reliable dedup).
2. **Create contact (3429)** — compound field quirk: phone inside `cf_contact`
   breaks name parsing ("Name can't be blank"). Use:
   `field_values = {"cf_contact": {"name": ..., "email": ...}, "cf_contact_phone": "91XXXXXXXXXX"}`
   Extract `ID: (\d+)` from the response (e.g. 54205836).
3. **Create lead (Pipeline 10)** — reference the contact by id:
   ```python
   field_values = {
     "cf_contact1": {"id": CONTACT_ID},
     "cf_source": "I Am Here Software Labs",   # Meta source
     "cf_sourcedetails": "Meta",
     "cf_campaign": "DigitalAds",
     "cf_project": "Ranka udaya",
     "cf_max_budget": 5000000,                 # ₹50L+ → 5000000
     "cf_requirements": "I need more details first",
   }
   ```
   Returns draft ID → poll `get_draft_status(draft_id)` until completed, then
   read the real lead ID (or `search_leads` Pipeline 10 by phone).
4. **Progress to SSV — sequential only, no jumps.** Stage IDs:
   Warm=**2**, PSC=**281**, SSV=**6**. From Cold you may only move to Warm, then
   PSC, then SSV. Each `move_stage` is async (returns draft ID) — check
   `get_draft_status` before issuing the next.
5. **SSV requires `cf_interested_in_site_visit_` = true.** If the move fails
   with "Required fields not present: Interested in Site Visit?", first
   `update_lead(lead_id, field_values={"cf_interested_in_site_visit_": True})`,
   wait for the draft, then retry the SSV move.
6. **Add note** — `add_note(lead_id, text=...)` with the follow-up context
   (e.g. "asked for details, interested in visiting the site, will keep us
   posted, requested details on WhatsApp again").
7. **WhatsApp follow-up** — generate the wa.me link with the `whatsapp_link`
   tool (never hand-encode). The user sends it themselves; Hermes never sends.

## Hard constraints
- **Never modify the tracker spreadsheet** (user's most important constraint).
- Everything is draft-first: the WhatsApp link is for the user to send.
- Lead/contact show "created by <token owner>" (e.g. Nishant Ranka) — expected
  artifact of using the shared token, not an error.

## Source config (Ranka Udaya Meta leads)
`cf_source="I Am Here Software Labs"`, `cf_sourcedetails="Meta"`,
`cf_campaign="DigitalAds"`, `cf_project="Ranka udaya"` — matches
`/data/hermes/scripts/batch_import_leads.py`.
