# Document Receipt, Naming, and Filing — DRAAS Property Closings

When the user (Bharat / Nishant / Roshini) drops property documents into the chat (PDFs, scans, photos) and asks to file them in Drive, follow this workflow. The drafting side of this skill covers *creating* documents; this reference covers *receiving* them from counterparties and filing them under the right project.

## When this applies

Triggers: "file this under...", "add to 914 folder", "save it in R&R", "name this document", "here are the documents from Ravi", "I am sharing few documents". The user is the orchestrator — they send files in batches, often with the destination folder name in the voice message but misspelled (e.g. "Ranca" → "Ranka", "R&R" → R&R is short for Embassy Habitat or another project, confirm before assuming).

## The 5-step workflow

### 1. Read content BEFORE naming (no exceptions)

Never trust the upload filename — it is almost always the uploader's raw label ("khata new pid.pdf", "662.pdf", "Adobe Scan 04 Jun 2026.pdf"). Filenames lie; content does not. Use the text-extraction ladder:

**Ladder (try in order, stop at first success):**

```bash
# Step A — text-based PDFs (90%+ of the time, instant)
pdftotext -layout "<file>" -

# Step B — scanned/image PDFs (text layer is empty, get < 50 chars back)
# Render page 1 at 100 dpi and ask the vision model
pdftoppm -r 100 -f 1 -l 1 -jpeg "<file>" /tmp/doc_p1
# Then: vision_analyze image_url="/tmp/doc_p1-01.jpg" question="What is this document? Type, parties, property details, document number, date."

# For multi-page scanned docs (e.g. 21-page absolute sale deed), page 1 is enough to identify type, parties, doc no. Read the rest only if needed.
```

**Decision rule:** `pdftotext` returns > 100 chars of usable text → use it directly. Returns near-empty → jump to `pdftoppm + vision_analyze` for page 1. Do not waste time rendering all pages.

### 2. Propose names using DOCUMENT date, not upload date

The file naming convention (confirmed by user) is:

```
YYYYMMDD Project Entity DocumentType
```

**Critical pitfall:** The date in the filename should be the **document's own date** (registration date, execution date, receipt date, or transaction date), NOT the date the user sent it. Old documents get shared all the time (e.g. a May-2026 discharge deed shared on June 4, 2026 → use `20260530` in the filename, not `20260604`). The folder name is the only place where today/share date is appropriate.

**Always state the date choice in the proposal** so the user can override: "Date used: 20260530 (discharge date). If you want today's date 20260604 since Ravi shared it today, let me know."

### 3. Propose names + WAIT for explicit approval

Do NOT rename or upload until the user confirms. Bharat's rule: always propose a name, get explicit go-ahead, then file. This prevents misidentifications (e.g. confusing a Khata certificate with a Khata extract) from polluting the Drive.

**Proposal format that works:**

```
| # | Original filename | Proposed new name | Doc details |
|---|---|---|---|
| 1 | khata new pid.pdf | 20260604_914EH_RavikumarKNaik_KhataCertificate_BBMP_PID59141.pdf | BBMP Khata, PID 59/141, Ravi Kumar K Naik |
| 2 | vijaya bank discharge .pdf | 20260530_914EH_RavikumarKNaik_BankOfBarodaVijayaBank_LoanDischarge_Deed926-27.pdf | Bank of Baroda (erstwhile Vijaya Bank) Discharge Deed 926/26-27 |
```

Plus a "Confirm before I proceed:" line listing:
1. Filenames ok?
2. Folder name + location ok?

### 4. Find / create the destination folder via Drive search

**Project folder locations (June 2026 snapshot — confirm before assuming hierarchy has not changed):**

| Project | Folder path | Folder ID |
|---|---|---|
| 914 Embassy Habitat (Ravi Kumar K Naik → Roshini Ranka) | `Embassy Habitat Legal Documents` → `914 Embassy Habitat Title Documents` | `1Rz1_I6pcdnzJvzBUZZDfzPoRB_CwLrnR` → `1rvnnl3168-YrvGQcUsD71aSYoVpmcChH` |
| 914 EH Sale Agreements (subfolder) | directly under Drive root | `1usmf8DrYX-1cH9Pv-7wBlLF3ihudu-FU` |
| Ranka Oasis | Drive root | `0ABYJXvUewWijUk9PVA` (parent) |
| Ranka Udaya (Thindlu Land Partners) | search "Ranka Udaya" — separate folder | — |

**To find folders, use the gws-auth-helper-bug-workaround pattern from the gws-automation skill.** Direct `from_authorized_user_file` works; the bundled `gws_auth.build_service` helper is broken in google-auth ≥ 2.x. Always include `supportsAllDrives=True, includeItemsFromAllDrives=True` on Drive queries.

**New-folder naming convention:** `YYYYMMDD Project Entity SubContext` — e.g. `20260604 914 EH Ravi — R&R` for documents received from Ravi Kumar on June 4, 2026 for the 914 Embassy Habitat R&R process. Confirm with the user which existing folder to put the new one under; do not assume.

### 5. Upload via Drive API, then verify

```python
# For binary PDFs:
file_metadata = {
    "name": "<new_filename>",
    "parents": ["<folder_id>"]
}
media = MediaFileUpload("/path/to/local.pdf", mimetype="application/pdf", resumable=True)
created = drive.files().create(
    body=file_metadata, media_body=media, fields="id,name,webViewLink",
    supportsAllDrives=True
).execute()
# Verify: list the folder, confirm the file shows up
drive.files().list(q=f"'{folder_id}' in parents and name = '<new_filename>'", ...).execute()
```

**Always re-list the folder after upload** to confirm the file is present at the right path. The `create` response is not proof — Drive can silently reject or place incorrectly.

## Common document types for DRAAS property closings

| Document type | What to look for in content | Typical naming suffix |
|---|---|---|
| Absolute Sale Deed | "Deed of Absolute Sale", buyer + seller names, schedule of property, doc no. | `AbsoluteSaleDeed_DocNo<XXX>-<YY-ZZ>.pdf` |
| Sale Deed | Similar to Absolute Sale Deed but older format | `SaleDeed_DocNo<XXX>-<YY-ZZ>.pdf` |
| Khata Certificate / Extract | BBMP, PID number, owner name, property address | `KhataCertificate_BBMP_PID<XXX>.pdf` or `KhataExtract_BBMP_PID<XXX>.pdf` |
| Property Tax Receipt | BBMP, tax year, owner name, flat no. | `PropertyTaxReceipt_<YYYY-YY>.pdf` |
| Loan Discharge / Reconveyance | "Discharge", "Reconveyance", bank name, loan account no., "no dues" | `<BankName>_LoanDischarge_Deed<XXX>.pdf` or `Re-conveyance.pdf` |
| EC (Encumbrance Certificate) | "Encumbrance Certificate", period covered, PID/survey no. | `EC_<from>-<to>.pdf` |
| RTC (Record of Rights) | "RTC", survey no., owner name, period | `RTC_<survey_no>.pdf` |
| Partition Deed | "Partition Deed", parties, survey no., doc no. | `PartitionDeed_DocNo<XXX>.pdf` |
| Gift Deed | "Gift Deed", donor + donee, property | `GiftDeed_DocNo<XXX>.pdf` |
| Rectification Deed | "Rectification Deed", original deed being rectified | `RectificationDeed_DocNo<XXX>.pdf` |
| Relinquishment Deed | "Relinquishment Deed", parties, property | `RelinquishmentDeed_DocNo<XXX>.pdf` |
| DD (Demand Draft) | Bank name, DD no., amount, payee, date | `<BankName>_DD_<amount>_<payee>.pdf` |
| AOS (Agreement to Sell) | "Agreement to Sell", buyer + seller, advance, sale consideration | `AgreementToSell_<parties>.pdf` |
| BESCOM Transfer Authorisation | BESCOM letter, RR no., owner | `BESCOM_TransferAuth_RR<XXX>.pdf` |
| Mortgage Memorandum (Deposit of Title Deeds) | "Memorandum relating to deposit of title deed", mortgagor, bank, facility amount, date of deposit | `<BankName>_MortgageMemo_Deposit<DDMMYYYY>.pdf` or `<BankName>_LoanAccount<XXX>_MortgageMemo.pdf` |
| Master Originals Handover Receipt | "Master Originals Handover Receipt", buyer + seller, itemised list of originals handed over, signed at sub-registrar | `MasterOriginalsHandoverReceipt_<SellerSurname>To<BuyerSurname>_<DDMMYYYY>.pdf` |
| Khata Transfer / Mutation | "Khata Transfer" or "Mutation", old PID → new PID | `KhataTransfer_<oldPID>-<newPID>.pdf` |

## Pitfalls

- **⚠️ Telegram document uploads can land in a CRON session (silent loss).** Telegram delivers all media to whichever session is currently active — including cron-managed sessions like "Hourly AOS and DD Collection Reminders." A cron session does NOT process document uploads; it just records them and moves on. If the user says "I sent PDFs last evening around 6:25 PM" and you have no record of them in the current session, the uploads went to the cron that was active at that time. **Recovery recipe** (`state.db` is at `/data/hermes/state.db`):
  ```bash
  python3 -c "
  import sqlite3, datetime, re
  conn = sqlite3.connect('/data/hermes/state.db')
  cur = conn.cursor()
  cur.execute('''
    SELECT session_id, timestamp, content
    FROM messages
    WHERE content LIKE '%document_cache%' AND role='user'
    AND timestamp BETWEEN <unix_start> AND <unix_end>
    ORDER BY timestamp
  ''')
  for sid, ts, c in cur.fetchall():
      ts_str = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
      m = re.search(r'doc_[a-f0-9]+_([^\\.]+\.pdf)', c)
      print(f'[{ts_str}] {sid} -> {m.group(1) if m else chr(63)}')
  "
  ```
  Convert IST to UTC for the timestamp range (IST = UTC+5:30, so 6:25 PM IST = 12:55 UTC; range = `[unix(2026-06-04 12:00 UTC), unix(2026-06-04 14:00 UTC)]`). The file path will be `/data/hermes/document_cache/doc_<hash>_<filename>.pdf` — the file is still on disk even though the cron session never read it.

- **Misspelled project names in voice messages.** "Ranca" → "Ranka", "Habitat" can be misheard as "Habitat" (correct) but also "Habitate", "Habitate". When in doubt, search Drive for the project keyword and confirm with the user before creating a folder.
- **"R&R" is not always Risk & Reward.** In Embassy Habitat context it often means "R&R" the buyer's pending process step, not a standard acronym. Confirm the meaning before creating a folder named after it.
- **Empty PDFs that look real.** Scanned Indian registered documents (sale deeds, discharge deeds) often have only the Department of Stamps header as text. If `pdftotext` returns mostly the registration header and no body, treat as scanned → `pdftoppm + vision_analyze`. A 21-page absolute sale deed with 0 body text is normal for the scanned-original format.
- **The user often sends a batch with no clear order.** Voice messages give partial instructions ("R&R folder", "from Ravi"). State what you're assuming for each file in the proposal — don't ask 5 separate questions, ask once with a table and a "confirm all or tell me what to change" line.
- **Don't file into a folder just because the filename suggests it.** Read the content first. A file named "vijaya bank discharge.pdf" might actually be SBI's discharge if the user re-saved it. The content is ground truth.
- **The folder ID may be a shortcut, not the real folder.** Use `drive.files().get(fileId, fields='shortcutDetails')` if listing children returns nothing — the parent might be a `.shortcut` target.
- **Always re-list the folder after upload.** Drive `create` can silently succeed but place the file in the wrong parent (especially when nested shortcuts are involved).

## What this reference does NOT cover

- Drafting new legal documents (sale deeds, agreements, etc.) — that's the main `legal-document-drafting` skill body.
- Sending documents to counterparties via WhatsApp/email — that's `messaging-drafts`.
- Counterparty / contact lookup for property matters — that's the user's memory and the shared contacts sheet.
