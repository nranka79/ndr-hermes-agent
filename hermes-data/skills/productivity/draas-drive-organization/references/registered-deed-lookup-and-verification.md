# Registered Deed Lookup & Verification (by document number)

Trigger: a counterparty — lender, due-diligence firm, bank, auditor, valuer — asks for
"the **MRTG Deed of document number 7049/25**", or any request that names a *registration
number* rather than a file. Deliverable = the correct instrument, **verified**, plus a
covering mail.

Built from the VGRO Finserv → DRA Realty due-diligence request (Oct 2026, Sarthak's mailbox).

## 1. Expand the registry shorthand BEFORE searching Drive

Requests and Encumbrance Certificates use registry shorthand that **never appears in DRAAS
filenames** — files carry the expanded word. A literal search for the abbreviation returns 0
and looks like "the document isn't there".

| Shorthand | Expansion | Drive search term |
|---|---|---|
| MRTG / MTG | Mortgage (Deed of Joint Mortgage / Simple Mortgage) | `name contains 'Mortgage'` |
| SD | Sale Deed | `name contains 'Sale Deed'` |
| GPA / SPA | (Special / General) Power of Attorney | `name contains 'Power of Attorney'` |
| JDA / JV | Joint Development Agreement | `name contains 'JDA'` |
| DTD | Deposit of Title Deeds (equitable mortgage) | `name contains 'DTD'` |
| ATS / AoS | Agreement to Sell / Agreement of Sale | `name contains 'Agreement'` |
| EC | Encumbrance Certificate | `name contains 'EC'` |

Worked example: `name contains 'MRTG'` → **0 results**; `name contains 'Mortgage'` → 48;
`name contains '7049'` → the single right file. Always run the number search too.

## 2. Search by the bare document-number token

`gws_drive_list(query="name contains '7049'")` is the highest-precision search — registration
numbers are unique. Expect:

- **multiple copies** of the same instrument across folders, owned by different people
  (`psingh@`, `sales1.blr@`, `admin3.blr@`), sometimes with suffixes like `(4)`;
- an older, near-identical sibling with no suffix — **same byte size = duplicate, not a
  different version**. Don't present it as an alternative revision.

Pick the copy sitting in the requester's / project's own folder, and **name the duplicates**
in your reply rather than silently choosing one.

## 3. VERIFY the instrument before serving it

Registered copies downloaded from the IGR portals (Karnataka Kaveri, TN Reginet) are
**image-only scans — no text layer**.

```
pdfinfo file.pdf                  # Producer: "Inspector General of Registration" ⇒ IGR scan
pdftotext -f 1 -l 2 file.pdf -    # returns EMPTY on these — expected, not an error
```

Working recipe (poppler + tesseract CLIs are installed system-wide):

```
pdftoppm -r 200 -f 1 -l 2 -png file.pdf pg     # rasterise
tesseract pg-1.png stdout                       # OCR page 1
```

- **Pages 1–2 OCR cleanly** and carry the operative facts: instrument type, "made and executed
  at <place> on this <date>", mortgagor/mortgagee with PAN, property extent and village.
- **The registration stamp header on page 1 is stylised and OCRs unreliably** (`FO4AY 2025`
  for `7049/2025`). Higher DPI, autocontrast, and cropping do **not** fix it — and
  `vision_analyze` on such a crop falls back to its free-OCR path and returns the same
  garbage. Corroborate the number from the **filename + the requester's own reference**
  instead of insisting on the stamp.
- **The last pages are annexures**, not the deed — Aadhaar/ID cards of the SPA holder or
  signatories, witness sheets. Page 1 plus the execution clause is the substance.
- Prefer terminal `pdftoppm`/`tesseract` over in-sandbox Python PDF libraries: `fitz`/`pypdf`
  are not guaranteed inside the `execute_code` sandbox, while the CLIs are always present.

Download from Drive with the sanctioned client only:

```python
import sys; sys.path.insert(0, "/opt/hermes")
from tools.gws_auth import build_service
svc = build_service("drive", "v3", service_name="google-draas")   # resolve via gws_resolve_account
data = svc.files().get_media(fileId=FID).execute()
```

## 4. Check the share surface before sending anything

`files().get(fields="permissions(id,type,role,emailAddress)")` on a registered instrument
routinely shows **`anyoneWithLink` → reader**, often alongside external parties (banks,
valuers, other law firms). A mortgage deed is not a public document.

Flag it explicitly, and prefer either (a) **attaching the PDF** to the mail, or (b) a
**named-user grant**, over handing out an open link.

## 5. Serving it

- Standing preference: **copy the document into a NEW folder** and share the copy links
  rather than forwarding the original item's link.
- Reply **inside the existing request thread**.
- Keep the house shape: `Dear <name>,` → `Greetings!` → what is enclosed → what is still
  being compiled → `Warm regards, / Sarthak Sharma / Accounts Officer / DRA Realty Pvt. Ltd.`
- Always state **what the instrument is** — type, document number, date, parties, property
  extent. A lender cannot file an unlabelled scan.
- If the thread listed several asks, close only the one being served. **Default:** say plainly
  what is still outstanding (with who is compiling it). **Exception — when the user explicitly
  scopes the mail to one item ("just send the deed", "drop the MIS + cost details, I'll send
  those"), DROP the outstanding-items paragraph entirely.** He is handling the rest himself and
  re-narrating it reads as padding. Verified 16-Oct-2026 (Sarthak: *"attach the PDF to the mail
  and just drop this MIS plus Amber cost, that I will give … just send it to Sudheer"* → the
  mail went out as the deed alone).
- **To = the requester only, no Cc**, unless the user names others. The requester's own thread
  Cc list is **not** an automatic reply-all target for a document hand-over — a DD/lender thread
  usually Cc's a whole team, and blasting a mortgage deed to all of them is not what was asked.
- **Rename the attachment to a clean, self-describing filename** before attaching —
  `Mortgage Deed 7049-2025 - Sevaganapalli - 13.10.2025.pdf` — dropping source artefacts like a
  trailing `(4)`, double spaces, and the leading `YYYYMMDD` prefix. A lender files what the
  filename says. Keep the doc number and date IN the name.
- Mechanics for actually creating the threaded reply draft (raw MIME, `threadId`, Drive-sourced
  attachment, verification) → `email-drafter` →
  `references/threaded-draft-relayed-attachments.md`.
