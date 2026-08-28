# BBMP Memorandum — Parent PID/Khata Bifurcation Draft Workflow

## When to Use

- Vinod (or another DRAAS user) uploads a BBMP Memorandum template (`.docx` or `.pdf`) requesting bifurcation of a parent PID/Khata into individual e-PIDs/e-Khatas
- User says "analyze this document and reviewing all related documents regarding this and make it appropriate draft and mention in draft column and row wise"
- User says "fill the all respective area in draft which is left" after being shown a partially-filled table — means search harder, don't leave blanks
- User provides a legal template with blanks and expects you to fill it by researching related documents on Drive

## Context

The BBMP Memorandum is addressed to the Assistant Revenue Officer (ARO) of a BBMP Ward, requesting:

1. Bifurcation of existing parent PID/Khata
2. Allotment of separate e-PID Numbers for each apartment unit
3. Issuance of individual e-Khatas in the developer's name

It is submitted by **M/s. DRA Developers & Projects Private Limited** (represented by its Director **Mr. Piyush Ranka**).

## Known Company Data (from Drive documents)

| Field | Value | Source |
|---|---|---|
| **Company Name** | M/s. DRA Developers & Projects Private Limited | 89th Board Minutes PDF |
| **CIN** | U70102KA2007PTC042299 | 89th Board Minutes PDF |
| **Registered Office** | No. 4, Ranka Chambers, No. 31, Cunningham Road, Bangalore - 560 052 | Fire NOC (confirmed by user Jun 2026) |
| **Directors** | Nishant Dinesh Ranka (DIN: 00298854), Piyush Ranka (DIN: 09081772), Sanjeev Ranka (DIN: 00298753) | 89th Board Minutes PDF |
| **Authorised Signatory (template)** | Mr. Piyush Ranka, Director & Authorised Signatory | Template itself |

**Source document:** The 89th Board Meeting Minutes of DRA Developers & Projects Pvt Ltd (dated 05-Mar-2024) is a text-searchable PDF stored on Vinod's Drive. Extract the registered office address and CIN from the first page header of the PDF using pdfminer via the Hermes venv.

## User Preference — Vinod's "Fill the Blanks" Expectation

When Vinod says "fill the all respective area in draft which is left" after being presented with a template analysis, he means:

- **Do NOT leave blanks with notes** — "To be filled per project" or "Needs confirmation" should be the exception, not the default
- **Search Drive aggressively** for related documents that contain the missing data: area statements, plan sanctions, khata certificates, tax receipts, board minutes
- **Present what you found** and what you couldn't find in separate groups
- **Use the Draft column to show actual proposed content** for every field where a related doc exists, even if the project match isn't 100% certain — flag uncertainty in the Remarks column, not by leaving the Draft column blank
- **Distinguish confirmed vs uncertain data visually** in the Draft column (e.g., **bold** for data confirmed from a specific source document, *italic* for educated guesses, plain for template text)

The Draft column should read like a filled document, not a to-do list.

### Template Structure

The standard template has these sections:

| Section | Key Fields (Blanks) |
|---------|---------------------|
| **To** (Addressee) | ARO Ward No, BBMP Zone |
| **Subject** | (Pre-filled — about bifurcation) |
| **Para 1** — Parent Property | Survey No, Khata No, PID No, Property Address, Original Owner name |
| **Para 2** — Development | Project Name, Number of apartment units |
| **Property Particulars** | Project Name, Address, Survey No(s), Khata No, Existing Parent PID |
| **Schedule of Apartment Units** | Table: Flat No, Floor, Super Built-up Area (Sq.Ft.), UDS (Sq.Ft.), New e-PID |
| **Prayer** | 5 standard prayers (a–e) — typically left as-is |
| **Enclosures** | 11 standard items — verify list |
| **Signature** | Mr. Piyush Ranka, Director & Authorised Signatory |

## Workflow

### Step 1: Extract the Document Text

The template is typically a `.docx` file. Read paragraphs and tables:

```bash
python3 << 'PYEOF'
from docx import Document
doc = Document('/path/to/file.docx')

# Read all paragraphs
for i, para in enumerate(doc.paragraphs):
    if para.text.strip():
        print(f'P{i}: [{para.style.name}] {para.text}')

# Read all tables
for ti, table in enumerate(doc.tables):
    for ri, row in enumerate(table.rows):
        cells = [cell.text.strip() for cell in row.cells]
        print(f'  Row {ri}: {cells}')
PYEOF
```

### Step 2: Search Drive for Project Documents

Search Vinod's Drive (via `tools.gws_auth.build_service("drive", "v3")`) for documents related to the developer/project mentioned in the template:

```python
import sys
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service

drive = build_service("drive", "v3")

# Search for project-related folders
results = drive.files().list(
    q="mimeType='application/vnd.google-apps.folder' and (name contains 'ProjectName' or name contains 'ShortCode')",
    fields='files(id, name)',
    pageSize=50
).execute()

# Search for specific documents with matching data
results = drive.files().list(
    q="name contains 'Area Statement' or name contains 'Khata' or name contains 'PID'",
    fields='files(id, name)',
    pageSize=50
).execute()
```

**Documents to look for:**
- **Area Statement** — Contains unit-wise flat numbers, floors, super built-up area, UDS — needed for the Schedule table. May be a **Google Sheet** (not just PDF/Excel). Use `gws_auth.build_service("sheets", "v4")` to read Sheet contents.
- **Khata Certificate** — Contains existing Khata No, PID/ePID
- **Plan Sanction / Building Permit** — Contains Survey No, project name, number of units
- **Property Tax Receipt** — Contains PID/ePID, Khata No
- **Certificate of Incorporation** — For registered office address of the company
- **Commencement Certificate** — For project address, survey numbers
- **Board Meeting Minutes** — For registered office address, CIN, director names (these are often text-searchable PDFs)

### Step 3: Identify Which Project

The template may not specify which project it's for. Common DRA Developers projects to check:

| Project | Developer | Known Data |
|---------|-----------|------------|
| **Ranka Iris** | DRA Developers & Projects Pvt Ltd | CC issued, OC in progress, multiple apartment units. Sy 17/1 & 17/2, Domlur |
| **Ranka Amber** | Land: Raghunathan Iyer (GPA: DRA Realty) | 20 units, Whitefield. Sy 4/124, PID 7057785976 |
| **BuxRanka** | DRA entity | Different legal folder set |

Check the template's address/Survey No blanks and project name for clues. If unclear, ask the user.

### Step 4: Present as "Draft Column" Table

The user specifically asked to "mention in draft column and row wise". Create a structured table with these columns:

| # | Section | Field | Template Content | **Draft / Proposed Content** | Source / Remarks |
|---|---------|-------|-----------------|------------------------------|------------------|

**Row-by-row coverage:**

Each blank in the template gets its own row. For each:
- **#** — sequential number
- **Section** — which part of the document (addressee, P1, Property Particulars, Schedule, etc.)
- **Field** — the specific field name (Survey No, Khata No, Project Name, etc.)
- **Template Content** — what the template currently shows (blank line, or pre-filled text)
- **Draft / Proposed Content** — YOUR proposed fill, pulled from related Drive documents. Do NOT leave empty or with generic placeholders if a related doc exists
- **Source / Remarks** — which document on Drive provides the data, or "Not found — ask user"

**Visual distinction in Draft column:**
- `**Bold**` = confirmed data from a specific source document
- `*Italic*` = educated guess / needs user confirmation
- Plain text = standard text from template, no change needed

**Example rows:**

| # | Section | Field | Template Content | Draft / Proposed Content | Source / Remarks |
|---|---|---|---|---|---|
| 1 | Subject | Subject Line | Request for bifurcation... | **As is — no change** | Standard text |
| 2 | P1(1) | Survey No | \_\_\_\_\_\_\_\_\_\_\_\_\_\_ | **17/1 & 17/2** | Ranka Iris Plan Sanction |
| 3 | Schedule | Flat No 1 | ______ | **101** | From Area Statement |
| 4 | Schedule | SBA Flat 1 | ______ | **1,250 sq.ft.** | From Area Statement |

### Step 5: Fill Gaps from Related Drive Documents

**CRITICAL — Vinod's preference:** When he says "fill the blanks", he expects you to search Drive for actual data to fill each field. Do NOT default to generic placeholders like "To be filled per project". Go through this checklist for each blank field:

1. ✅ **Check Area Statement** (Google Sheet or Excel) — for unit schedule (flat numbers, floors, SBA, UDS)
2. ✅ **Check Plan Sanction / Building Permit** — for Survey No, project name, total units, property address
3. ✅ **Check Khata Certificate / e-Khata** — for existing Khata No, PID/ePID
4. ✅ **Check Property Tax Receipt** — for PID/ePID, Khata No, Ward No
5. ✅ **Check Company documents** (CoI, Board Minutes) — for registered office address, CIN, directors
6. ✅ **Check BBMP covering letters** — for project address, Sanction Plan No, LP No

Only after ALL these searches come up empty should you use:
- `Not found on Drive — ask user` for truly missing data
- `**To be filled per project**` only as a last resort

#### Extracting Data from Scanned OC/BBMP PDFs

BBMP certificates (OC, CC, Building Permits) are often **scanned images** inside PDFs — pdfminer will return no text. Use this two-step workflow:

1. **Convert PDF pages to images** using `pdftoppm` (available at `/usr/bin/pdftoppm`):
   ```bash
   pdftoppm -png -f 1 -l 3 -r 200 /path/to/document.pdf /tmp/output_prefix
   ```
   This creates `/tmp/output_prefix-1.png`, `/tmp/output_prefix-2.png`, etc.

2. **Use vision_analyze on the images** to extract text:
   ```
   vision_analyze(image_url="/tmp/output_prefix-1.png",
       question="Extract all text... I need: project name, address, PID, number of units, floor breakdown...")
   ```

**Pitfall:** `pdftoppm` creates one PNG per page. For multi-page docs (OC certificates are often 3-4 pages), convert the first 2-3 pages to get the full schedule. The first page has the header/issuance details; page 2 has the unit schedule table.

**Pitfall:** vision_analyze cannot read PDFs directly — it requires image files. Do NOT pass a `.pdf` path as image_url; it will fail with "Only real image files are supported."

This technique was used successfully to extract the Ranka Iris OC (3 pages, 2.6MB scanned PDF) — got the full 17-row floor schedule with built-up areas.

### Step 6: Deliver to User

Present the complete table to the user with a clear summary of:
- ✅ What you were able to fill from Drive documents
- ❌ What remains blank and why
- 📁 Which Drive folders/docs you searched
- 💡 What additional documents would help complete the draft

### Step 7: Generate the Filled DOCX

Once the user confirms the project and fills in missing data, generate two deliverables:

1. **The filled Memorandum** (the main application document)
2. **A covering letter** (to accompany the submission, referencing the memorandum as enclosure)

### Step 7a: Generate the Filled Memorandum DOCX

**Approach:** DRAAS BBMP Memorandum DOCX templates typically have all body content in a single paragraph (paragraph index 1, P1) with `\n` line breaks for structure. The heading "MEMORANDUM" is a separate paragraph (P0) with large bold formatting.

```python
from docx import Document

doc = Document('/path/to/template.docx')

# Build the complete body text with \n for line breaks
filled_text = """To

The Assistant Revenue Officer (ARO)
Ward No. 112
Bruhat Bengaluru Mahanagara Palike (BBMP)
Central City Corporation Zone
Bengaluru.
..."

# Replace the body paragraph content
body_para = doc.paragraphs[1]  # P1 = body content
for run in body_para.runs:
    run.text = ''
if body_para.runs:
    body_para.runs[0].text = filled_text
else:
    body_para.add_run(filled_text)

doc.save('/path/to/BBMP_Memorandum_FILLED.docx')
```

**CRITICAL — Ampersand in company names causes shell issues:** The company name "DRA Developers & Projects" contains an `&` character. If the Python script is run inline via `terminal(command="python3 -c '...'")`, the shell interprets `&` as a background command operator, causing syntax errors or silent failures.

**Fix — use AND instead of &, or write script to file first:**
- Option A (simpler): Replace `&` with `and` in the text — "DRA Developers and Projects Private Limited". This is acceptable for Indian legal documents where `&` and `and` are interchangeable in company names.
- Option B: Write the Python script to a `.py` file first using `write_file`, then run it via `terminal(command="python3 /path/to/script.py")`. The `write_file` tool does NOT interpret `&` as a shell operator.
- Option C: Use `execute_code` instead of `terminal` — the Python sandbox doesn't go through a shell parser.

**Verify:** After generation, always check the output by re-reading the DOCX with python-docx and printing key paragraphs to confirm the filled data is present.

### Step 7b: Generate the Covering Letter

After the memorandum is filled, the user may ask to "make it request covering letter format". Create a separate covering letter DOCX that:

1. **Dates and addresses** the same officer (ARO, Ward, Zone)
2. **References** the Sanction Plan No, OC No, Fire NOC as prior correspondence
3. **Briefly states** that the accompanying Memorandum is being submitted for bifurcation
4. **Requests** consideration and processing
5. **Lists the enclosures** (Memorandum + supporting docs)
6. **Signs off** with the same signatory (Mr. Piyush Ranka)

**Covering letter structure:**

```
Date: ____/____/2026

To,
The Assistant Revenue Officer (ARO)
Ward No. ___
BBMP ___ Zone
Bengaluru.

Through:
The Revenue Inspector
Ward No. ___, BBMP, Bengaluru.

From:
M/s. DRA Developers and Projects Private Limited
No. 4, Ranka Chambers, No. 31, Cunningham Road
Bangalore - 560 052

Sub: [Subject line with "covering letter" suffix]

Ref: 1. Building Plan Sanction No. ______, dated ______
      2. Occupancy Certificate No. ______, dated ______
      3. Fire Clearance No. ______, dated ______

Respected Sir/Madam,

[Brief body stating submission of the accompanying Memorandum]

We request your good office to kindly consider the accompanying Memorandum
and pass necessary orders for bifurcation...

Thanking you,

Yours faithfully,

_________________________
Mr. Piyush Ranka (DIN: 09081772)
Director & Authorised Signatory

Enclosures:
1. Memorandum (Original Submission)
2. [List supporting documents]
```

**Implementation:** Use `python-docx` to create a fresh document (not modifying the template). Set font to Times New Roman 12pt. Use `new_doc.add_paragraph()` with manual line-by-line construction. The covering letter should be saved as a separate file named `PROJECT_Covering_Letter.docx`.

**Pitfall — The covering letter replaces the memorandum body with a short summary:** The covering letter is NOT the memorandum. It's a 1-page letter saying "Please find enclosed the Memorandum requesting...". The full memorandum with the schedule table, property particulars, and prayer is attached as Enclosure 1. Don't repeat the entire memorandum content in the letter.

**Pitfall — Enclosures reference the EC compilation:** If you've compiled multiple ECs into a merged PDF, reference it as "Encumbrance Certificate (comprehensive — covering YYYY to YYYY)" rather than listing individual EC files.

## Concrete Worked Examples (from Drive search)

### Example: Ranka Iris Project Data (Verified Jun 2026)

When the user confirmed the memorandum is for **Ranka Iris**, the following data was assembled from 6+ Drive documents:

#### From Property Tax Receipts (2023-24, 2024-25)

| Field | Value | Source File |
|---|---|---|
| **Owner** | M/s DRA Developers & Projects Pvt Ltd, Rep by its Director Mr. Manish Ranka | `Tax Paid Receipt Ranka Iris FY2015-16.pdf` |
| **Property Address** | Site No. 37-37A-38, Domlur 2nd Stage, Sy No 17/1 & 17/2 | Tax Receipt 2024-25 |
| **Old PID / Khatha No / Survey No** | **72-30-37-37A-38** | Tax Receipt 2024-25 |
| **Ward** | **112 - Domlur** | Tax Receipt 2024-25 |
| **SAS Base Application No** | 431206201 | Tax Receipt 2024-25 |

**⚠️ Owner name on tax receipts includes "Mr. Manish Ranka" as Director** — this confirms the template's statement that the parent property stands in his name. The Manish Ranka connection is verified from the original BBMP tax records.

#### From Occupancy Certificate (ACTP/BCCC/OC/001/2026-27, dated 04.06.2026)

| Field | Value |
|---|---|
| **Building Configuration** | **3 Basement + Ground Floor + 13 Upper Floors (3BF+GF+13UF)** |
| **Total Residential Units per OC** | **12** — one per floor from 2nd to 13th |
| **Total Residential Units per User** | **13 (1001-1013)** — user confirmed 13 units, likely including one on 1st floor / converted amenity space |
| **Total Built-up Area (residential)** | 5,234.88 sqm (total across all levels) |
| **Sanction Plan No.** | BBMP/Addl.Dir/JD North/0037/2013-14 |
| **BBMP Zone** | **Central City Corporation** (not North Zone — BBMP reorganization) |
| **Ward** | 112 (Old No. 72), Central City Corporation |
| **Occupancy Certificate Date** | 04 June 2026 |
| **Fire Clearance** | KSFES/CC/069/2026 dated 17-02-2026 |

**⚠️ OC vs user-confirmed unit count:** The OC certificate says 12 residential units (2nd–13th floor, one per floor). However, when asked about flat numbers, the user confirmed **13 units (1001 to 1013)**. The extra unit (1001) is likely on the 1st floor or an additional space. Always defer to the user's actual unit numbering — the OC may omit count the first-floor unit if it was categorised as common area at sanction time but later converted. Present the OC data but confirm the final unit list with the user.

**Building Floor-wise Breakdown (from OC Schedule):**

| Floor | Built-up Area (sqm) | Usage |
|---|---|---|
| Basement-1 | 454.91 | 9 Car Parking, Lifts, Lobbies |
| Basement-2 | 454.91 | 10 Car Parking, Lifts, Lobbies |
| Basement-3 | 454.91 | 11 Car Parking, Electrical, Store, DG Yard, OTS |
| Ground Floor | 170.10 | Entrance Lobby, Toilet, Store, Electrical Room |
| First Floor | 279.96 | Gym, Multipurpose Hall, Pantry |
| **2nd–13th Floor** | **~279.96–281.52 each** | **1 Residential Unit per floor** |
| Terrace | 51.21 | Lift Machine Rooms, Staircase Head Rooms, OHT |

**Proposed Unit Schedule — confirmed by user (Jun 2026):** 

| Sl.No. | Floor | Flat No. | Built-up Area (sq.ft.) | UDS | New e-PID |
|---|---|---|---|---|---|
| 1 | 1st | 1001 | — | — | To be allotted |
| 2 | 2nd | 1002 | ~3,030 (281.52 sqm) | — | To be allotted |
| 3 | 3rd | 1003 | ~3,013 (279.96 sqm) | — | To be allotted |
| 4 | 4th | 1004 | ~3,030 (281.52 sqm) | — | To be allotted |
| 5 | 5th | 1005 | ~3,013 (279.96 sqm) | — | To be allotted |
| 6 | 6th | 1006 | ~3,030 (281.52 sqm) | — | To be allotted |
| 7 | 7th | 1007 | ~3,013 (279.96 sqm) | — | To be allotted |
| 8 | 8th | 1008 | ~3,030 (281.52 sqm) | — | To be allotted |
| 9 | 9th | 1009 | ~3,013 (279.96 sqm) | — | To be allotted |
| 10 | 10th | 1010 | ~3,030 (281.52 sqm) | — | To be allotted |
| 11 | 11th | 1011 | ~3,013 (279.96 sqm) | — | To be allotted |
| 12 | 12th | 1012 | ~3,030 (281.52 sqm) | — | To be allotted |
| 13 | 13th | 1013 | ~3,013 (279.96 sqm) | — | To be allotted |

**Flat numbering scheme note:** Ranka Iris uses the 1000-series scheme (1001–1013), NOT floor-based numbering (201, 301...). The flat number encodes the tower/series rather than the floor number. 1002 = 2nd floor, 1013 = 13th floor, 1001 = 1st floor (or ground/amenity converted). This is a DRAAS-specific convention that differs from Ranka Amber's floor-based scheme (101–105 = GF, 201–205 = 1st).

#### From Fire NOC (KSFES/CC/069/2026, dated 17-02-2026)

| Field | Value |
|---|---|
| **PID No.** | **72-30-37A-38** (slightly different format — hyphens removed in OC version) |
| **Site No.** | 37, 37A & 38 |
| **Sy No.** | 17/1 & 17/2 |
| **Applicant Address** | M/s DRA Developers & Projects Pvt Ltd, **No. 4, Ranka Chambers**, No. 31, Cunningham Road, Bangalore - 560 052 |

**⚠️ Address discrepancy — RESOLVED (Jun 2026):** The Fire NOC says "No. 4, Ranka Chambers" while the 89th Board Minutes (05-Mar-2024) say "No. 2, 2nd Floor, Ranka Chambers". Both are at No. 31 Cunningham Road. When asked, the user confirmed **No. 4 Ranka Chambers** is the correct address. The Fire NOC (2026 document) is more current than the Board Minutes (2024) for this field.

#### From 89th Board Meeting Minutes (05-Mar-2024)

| Field | Value |
|---|---|
| **Registered Office** | **No. 2, 2nd Floor, Ranka Chambers, No. 31, Cunningham Road, Bangalore - 560 052** |
| **CIN** | U70102KA2007PTC042299 |
| **Directors Present** | Nishant Dinesh Ranka (00298854), Piyush Ranka (09081772), Sanjeev Ranka (00298753) |
| **Template Signatory** | **Mr. Piyush Ranka (DIN: 09081772)** — confirmed as a Director |

### Example: Ranka Amber Project Data (Different Entity — Do Not Conflate)

| Field | Value | Source |
|---|---|---|
| **PID / Khata** | 7057785976 | Sanction Plan |
| **Survey No.** | 4/124 (Plot 1-B) | Sanction Plan |
| **Location** | D'Silva Layout, Pattandur Agrahara, K.R. Puram Hobli | Sanction Plan |
| **Ward** | 083, Mahadevapura Zone | Sanction Plan |
| **Units** | 20 (Stilt + GF + 3F, 5/floor) | Area Statement Sheet |
| **Flat Numbers** | 101-105 (GF), 201-205 (1st), 301-305 (2nd), 401-405 (3rd) | Area Statement Sheet |
| **Owner** | Raghunathan Iyer & Farida R Iyer (NOT DRA Developers) | Sanction Plan |
| **GPA Holder** | DRA Realty Pvt Ltd (Nishant Ranka) — NOT DRA Developers & Projects | Sanction Plan |

**Critical:** Ranka Amber is owned by Raghunathan Iyer with DRA Realty as GPA holder. The BBMP Memorandum template is for DRA Developers & Projects Pvt Ltd (Piyush Ranka). These are different legal entities. Do NOT use Ranka Amber data in a DRA Developers & Projects Pvt Ltd memorandum unless the user explicitly confirms the connection.

## Pitfalls

1. **Multiple projects, one template** — The template says "DRA Developers & Projects Pvt Ltd" but doesn't specify which project. Don't guess — present options from Drive data and ask.

2. **RnR vs DRA Developers** — The BBMP Memorandum is for M/s. DRA Developers & Projects Pvt Ltd (represented by Piyush Ranka), NOT for Roshini/Nishant Ranka personally. Keep the entity name exact.

3. **Manish Ranka reference** — The template says the parent Khata stands in the name of "Mr. Manish Ranka, Director of M/s. DRA Developers & Projects Private Limited". Confirm this is correct for the specific project — Manish may not be the recorded owner for every project. For Ranka Iris, it was confirmed via tax receipts (owner: "M/s DRA Developers... rep by its Director Mr. MANISH RANKA").

4. **e-PID ≠ old PID** — The e-PID is a 10-digit number assigned through improvement charge payment or plan sanction, NOT the old manual PID format. See `references/bbmp-pid-formats.md` for the distinction.

5. **Schedule table** — The template has exactly 13 rows for units. If the project has a different number of units, adjust. Get the exact unit list from the Area Statement or Approved Plan.

6. **Enclosures list is standard** — The 11-enclosure list in the template is standard for this application. No need to change unless the user specifically asks.

7. **OC unit count vs user-confirmed count** — The OC certificate may state one unit count (e.g., 12 from 2nd–13th floor) while the user confirms a different count (e.g., 13, including unit 1001 on 1st floor). Always defer to the user's actual unit numbering. The OC may omit a first-floor unit if categorised as common/amenity space at sanction time but later designated as a residential unit. Present both in the draft and flag the discrepancy.

8. **Flat numbering scheme differs per project** — Do NOT assume floor-based flat numbers (201, 301...). Ranka Iris uses the 1000-series scheme (1001, 1002... 1013) where the flat number encodes the tower/series, not just the floor. Ranka Amber uses floor-based numbering (101-105 = GF, 201-205 = 1st). Wait for user confirmation before finalising the schedule.

9. **Registered office address: Board Minutes vs Fire NOC** — The 89th Board Minutes (Mar 2024) say "No. 2, 2nd Floor" but the Fire NOC (Feb 2026) says "No. 4, Ranka Chambers". The user confirmed **No. 4 Ranka Chambers** is correct. When documents conflict, prefer the more recent source and confirm with the user.

10. **The `&` in company names breaks inline terminal scripts** — The `&` character in "DRA Developers & Projects" is interpreted by the shell as a background operator when the Python script is run inline via `terminal(command="...")`. Always either (a) replace `&` with `and`, (b) write the script to a `.py` file first, or (c) use `execute_code` instead of `terminal`.

11. **Kannada e-Khata PDFs** — If searching for existing Khata data, note that e-Khata PDFs from BBMP e-Aasthi are in Kannada with CID-encoded text. Key English fields (address, owner name, doc number, area) are still readable with pdfminer. See `references/e-khata-filing-workflow.md` for extraction notes.

12. **No gws_sa for Vinod's Drive** — Never use `gws_sa.build_service()` for Drive access. Always use `tools.gws_auth.build_service("drive", "v3")` with the Hermes venv path.
