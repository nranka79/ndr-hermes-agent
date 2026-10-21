# Jiraaf DD pack — round-2 re-send (2026-10-08)

## The ask pattern (NDR verbatim shape)

> "the formatting I want is something similar to an earlier email, 'Ranka deal documents — giraaf dd pack',
> which I had sent to Prakash Singh, Roshni, Nishant Prakash, Bharat and Sartak … but the content is from my
> October 7th email to Prakash of Giraaf, Nishant Prakash and Sarthak. Then present only Section 9 and
> Section 10 to me after updating, I'll review, then do a fresh email in the same thread as Nishant Prakash."

He identifies the two source mails by **Cc list + approximate time**, never by message ID. Recover both from
Gmail. Assume the styling of the newer mail is LOST (it usually gets sent as flat text after he re-pastes),
which is exactly why he is asking for the older one's formatting.

## The two sources (verified — headers + HTML parts read back)

| Role | Message | Thread | To | Cc | HTML fingerprint |
|---|---|---|---|---|---|
| **Formatting source** | `1a10cbe0fd0bebc8` — 5 Oct 21:15, "Re: Ranka Deal Documents — Jiraaf DD pack: draft reply for your review" | `1a10c8bafc62632f` | Prakash Singh | Roshini Ranka, Nishant Prakash Zara, Bharat Hawaldar, Sarthak Sharma | 39,859 B · no `<style>` block · Calibri · palette `#0b57d0` `#e8f0fe` `#fff8c5` · 13 × `<h3>` · 9 tables · contains the **FOR PRAKASH** yellow box → DELETE that box |
| **Content source** | `1a116ee0ea90db0d` — 7 Oct 20:44, "Re: Fwd: Ranka Deal Documents" | `1a10c71519ac4760` | Nishant prakash | Prakash (jiraaf), Nishant Prakash Zara, Sarthak Sharma | 19,053 B · 12 × `<h2>` · no colours, no font-family — the styled version did not survive sending |

The Cc list is the identifying feature — the Oct-5 mail's Cc (Roshini / Nishant Prakash / Bharat / Sarthak) is
what NDR is describing. Do not guess from the subject line; both carry "Ranka Deal Documents".

**Round-2 recipient set (NDR's explicit instruction):** To **Nishant Prakash** (nishantprakash@theyelloweye.com);
Cc **Prakash Singh** (psingh@draas.com) + **Sarthak Sharma** (admin3.blr@draas.com) — and nobody else: not
Roshini/Bharat, not the Jiraaf team. Jiraaf people are already on the thread (Prakash M's 8-Oct reply-all added
Vineet + Kanishk; he "recalled" his 8-Oct 07:21 forward).

## Extracting an email's real HTML part

The bridge tools (`gws_gmail_get`, `gws_gmail_thread_get`) return only the `text/plain` rendering. Literal
markdown asterisks (`*Project*`, `*Total cost incurred*`) in that body do **not** prove the mail went out as
plain text — every point-by-point DD mail shows them. Never judge formatting from the bridge body.

```python
# /opt/hermes/.venv/bin/python3 ; sys.path.insert(0, "/opt/hermes")
from tools.gws_auth import build_service
svc = build_service("gmail", "v1", service_name="google-draas")
m = svc.users().messages().get(userId="me", id=mid, format="full").execute()
hdrs = {h["name"].lower(): h["value"] for h in m["payload"]["headers"]}
# cc / reply-to / message-id live in hdrs — the bridge's `to` field shows To only
# walk m["payload"]["parts"] recursively; where mimeType == "text/html":
#   base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", "replace")
```

Fingerprint fields that reliably distinguish two versions of the "same" mail: byte length, md5, sorted unique
`#rrggbb` colours, `font-family`, presence of a `<style>` block, `<table>`/`<h2>`/`<h3>` counts, and marker
strings ("FOR PRAKASH", "Open folder 07", "Sub-folders 01").

Reusable scripts written this session: `/opt/data/ro_check.py` (headers + part sizes + html/text byte counts),
`/opt/data/ro_dump_html.py` (dump both HTML parts + fingerprint table). Saved HTML:
`/tmp/roasis/sent_oct5.html` (formatting template) and `/tmp/roasis/sent_oct7.html` (content).
**/tmp is ephemeral** — if these are gone, re-extract from the message IDs above.

## Section 9 — figure history (publish only the latest set NDR has confirmed)

| Date | Source | Figures | Status |
|---|---|---|---|
| 5 Oct | first draft | structure & infra 52.09, finishing 20.30 → future cost **134.86**; DRA free-sale 132.22 → revenue **204.83** | superseded |
| 6 Oct | Sarthak, msg `1a111891b339fdd7` | structure & infra **48.09 cr** (48,08,70,000), finishing **18.74 cr** (18,74,25,000), DRA free-sale **139.74 cr** (1,39,74,00,000) → future cost **122.09**, revenue **212.35** | what went out 7 Oct |
| 8 Oct | Sarthak, msg `1a11b6b49f6ec53b` | structure & infra **57.48 cr** (574,827,997), finishing **24.65 cr** (246,471,833), HR & corporate **12.90 cr** (129,000,000); BUA **2,94,780 sqft** → Jiraaf saleable 97,279 / DRA 1,97,505; inflows Jiraaf saleable **95.12 cr** (951,222,967), DRA free-sale **181.10 cr** (1,811,008,432), clubhouse **5.50 cr** (55,000,000) | **newest — supersedes; confirm with NDR before publishing** |

## Section 10 — the one open discrepancy

7-Oct mail says **15 plots with villas**; the investor referral register on file shows **13** agreements
(₹12.53 cr contracted, 36,450 sqft); the cash-flow model carries a "14 investor villas" line. Section 10 in the
round-2 mail is meant to resolve it — take NDR's number, never silently pick one.

## Protocol NDR expects for this class of re-send

1. **Confirm understanding before doing anything** — name the thread, the exact recipient set, the formatting
   source and the content source, and list which sections change vs stay.
2. Apply **only** the sections he supplied new data for, then show back **only those sections** for review.
3. After his ok, create the draft **in-thread** (reply) and **delete any stale draft on the same thread**.
4. Draft only — never send. Flag anything that contradicts (e.g. newer figures than the ones he quoted).

---

# Round 3 — apply the 8-Oct figures, drop Section 10 (2026-10-09)

NDR reviewed the round-2 draft, confirmed the formatting/content split was right, then gave two
changes: **take the numbers from Sarthak's 8-Oct mail**, and **delete Section 10 entirely**. He
asked to be shown back **only the changed sections** before the draft was built — then, in the same
turn, said "prepare the draft and let me know", so the correct move was to do both: create the draft
AND paste the changed sections into the reply.

## Structural change — Section 10 removed, 10/11 renumber

The MIS block ("Investor allotments booked / Rate at which allotted / Villa sizes allotted /
Contracted value / Received to date / Plots allotted / Total deliverable") is **deleted**. Sections
after it move up: **10 = Expected timelines**, **11 = Approval status**. Final shape = Project
snapshot + 11 sections. Renumbering is not cosmetic — assert the old heading is gone and the new
numbers exist before handing over.

Also drop from "Points to note" any bullet that referenced the deleted section (the old amber box
had an *"MIS — no live MIS. The booking register is as set out at point 10"* line; the 7-Oct content
source had already dropped it — use the 7-Oct list, not the 5-Oct one).

## Section 9 as applied (round-3 mail)

- **(a) Cost incurred to date** — unchanged, total **18.62 cr**. Pre-sales receipts note 9.76 cr.
- **(b) Estimated future cost** — structure & infra **57.48** (Rs 57,48,27,997) · finishing **24.65**
  (Rs 24,64,71,833) · sales & marketing 14.03 · HR & corporate **12.90** (Rs 12,90,00,000) ·
  clubhouse 10.00 · investor villa + model villa 8.70 · layout dev 4.34 · liaisoning payout +
  transaction fee 4.17 · marketing office 1.00 · Jiraaf S&M 3.41 → **total 140.68**
- **(c) Built-up area** — NEW block: total **2,94,784** sqft · Jiraaf saleable **97,279** ·
  DRA free-sale **1,97,505**
- **(d) Projected revenue** — DRA free-sale **181.10** (Rs 1,81,10,08,432) · Jiraaf inventory
  **95.12** (Rs 95,12,22,967) · clubhouse **5.50** (Rs 5,50,00,000) → **total 281.72** ·
  Jiraaf transaction consideration 35.34 shown as a separate row below the total

## The reconciliation finding — the email does NOT tie to the live model

Read the model, don't sum the email. `1SubaopapjqfAVGbEoIYzaG-kftb50jkbga-XsDWuYU4` (tabs
`Assumptions` / `Dated_Cash_Flow` / `12Qtr_Cash_Flow`; the `Jiraaf_IRR` tab is stripped before
external sharing), read with `valueRenderOption='UNFORMATTED_VALUE'` on 2026-10-09:

| Line | Round-3 mail | Live model | Note |
|---|---|---|---|
| Construction — structure & infra | 57.48 | **-574,827,996.6** → 57.48 | ties |
| Construction — finishing | 24.65 | **-246,471,833.3** → 24.65 | ties |
| HR & corporate overhead | 12.90 | **-126,825,255.95** → **12.68** | Sarthak's 12.90 ≠ model; model is 4% of total inflows (Assumptions B68) |
| Sales & marketing | 14.03 | DRA own 9.51 + external 19.34 = **28.85** | mail row is stale |
| Investor villa + model villa | 8.70 | mock villa 1.00 (14-villa rows are 0) | mail row is stale |
| Jiraaf S&M | 3.41 | **4.76** | mail row is stale |
| **TOTAL future cost** | **140.68** | `TOTAL OUTFLOWS (B)` = **-1,489,261,374.06** → **148.93** | the gap is the four rows above |
| Total built-up area | 2,94,780 (Sarthak) | **294,783.59** → 2,94,784 = 97,279 + 1,97,504.59 | 4 sqft; used the model total so the table adds up |
| Construction rate | "Rs 3,250/sqft" (mail) | Assumptions B47 = **3,000/sqft** | mail footnote stale |
| Pre-launch price | "Rs 7,500" (mail) | Assumptions B22 = **8,000** | mail footnote stale |

**Rule:** update only what NDR asked for, recompute the printed total arithmetically so the table
is internally consistent, then hand him the delta table above. Do NOT silently rewrite the untouched
rows and do NOT quietly drop a stale footnote — show it and offer to fix. He decides.

Also worth knowing the model's own internal inconsistencies (don't quote these to a lender):
Assumptions B5 total villas = 108 while its note says 111; `12Qtr` villa counts sum to 110
(73 DRA + 37 Jiraaf); B7's note says "111 × 2,550 = 2,83,050" against an actual 294,783.59.

## Round-3 recipient set

To **Nishant Prakash** (nishantprakash@theyelloweye.com); Cc **Prakash Singh** (psingh@draas.com) +
**Sarthak Sharma** (admin3.blr@draas.com). Explicitly NOT Roshini/Bharat, NOT the Jiraaf team, NOT
nishantprakash1@gmail.com. NDR narrows the audience on each round — read his latest instruction, not
the previous round's set.

## Pre-draft checks that caught real problems

1. **Resolve every link in the built HTML** — `files().get(fileId=..., fields='id,name,mimeType,trashed',
   supportsAllDrives=True)` per unique folder/file ID. All 10 resolved; a 404 after a cleanup pass is
   the signal that a folder you deleted is still linked somewhere.
2. **Assert banned content is absent** — no folder-07/08 IDs, no spreadsheet ID (`1Subaopapjqf…`),
   no `6157` / Harish / mortgage / affidavit / petition / notice strings. Run this as an assertion
   block, and print counts of the key new figures so you can see substitution actually happened.
3. **Check the thread for stale drafts before creating the new one** — `drafts().list` and match each
   draft's `threadId` against the target. The round-2 draft had already been SENT by NDR (it is the
   7-Oct content source, `1a116ee0ea90db0d`), so this thread held exactly one draft afterwards.
