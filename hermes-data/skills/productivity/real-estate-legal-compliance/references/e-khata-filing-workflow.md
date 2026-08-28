# e-Khata & Property Document Filing Workflow (Vinod)

## When to Use
- Vinod uploads a property document (e-Khata, sale deed, EC, tax receipt, NOC, etc.) and asks you to file it on Drive
- Any request to "put this in the right folder" with naming convention + approval + WhatsApp notification

## Workflow

### Phase 1: Extract Document Metadata

From the uploaded document (PDF/image), extract:

| Field | Source | Example |
|---|---|---|
| **Doc Date** | Document content (NOT upload date) | 05-JUN-2026 |
| **Property Code** | Project shorthand (e.g., 914EH for Embassy Habitat 914) | 914EH |
| **Owner/Seller Name** | From document content | RoshiniRanka / RavikumarKNaik |
| **Doc Type** | Document category | E-Khata, SaleDeed, EC, BESCOM_Bill |
| **Doc/Reg Number** | Registered number if applicable | GNR-1-00662-2026-27 |
| **Survey No** | If mentioned | 59/141 |
| **Area** | Built-up / total area | 72.6 sqm / 103.7 sqm |

**Note on Kannada e-Khata PDFs:** These are Kannada-language documents from the BBMP e-Aasthi portal. pdfminer extraction yields garbled text (CID-encoded Kannada glyphs not mapped). Key English fields are still readable (address, owner name, doc number, total area, built-up area). Extract what you can and present the rest as-is — the user knows the document and will confirm details.

**Verified extraction (Jun 2026):** 914 Embassy Habitat e-Khata (Form A, Doc GNR-1-00662-2026-27) — successfully extracted: owner Roshini Ranka, Flat No 914, Survey 59/141, total area 103.7 sqm/1116 sqft, built-up 72.6 sqm/781 sqft, address Embassy Habitat Apartment Palace Road. The Kannada text is CID-encoded but English numbers, names, and addresses render correctly.

### Phase 2: Determine Filename

**Convention (confirmed by Nishant):** `YYYYMMDD_Keywords_DocNumber.pdf`

For 914 Embassy Habitat specifically, the established pattern from existing files:

```
YYYYMMDD_914EH_Owner_DescriptiveKeywords.pdf
```

e.g.:
- `20260603_914EH_RavikumarKNaik_RoshniRanka_AbsoluteSaleDeed_DocNo662-26-27.pdf`
- `20260604_914EH_RavikumarKNaik_KhataCertificate_BBMP_PID59141.pdf`
- `20160801_914EH_RavikumarKNaik_BBMP_KhathaExtract.pdf`
- `20260605_914EH_RoshiniRanka_E-Khata_GNR-1-00662-2026-27.pdf` (proposed for new e-Khata)

**Rules:**
- Date = document content date (execution/registration date), NOT upload timestamp
- Owner name in CamelCase, no spaces
- Descriptive keywords separated by underscores
- Include doc/reg number at end when available
- Extension preserves original (.pdf, .jpg)

### Phase 3: Find the Right Drive Folder

**Known 914 Embassy Habitat folder hierarchy (Vinod's Drive, under "Personal"):**

```
Personal (root)
└── 914 EH Sale Agreements
    ├── 20260604 914 EH Ravi — R&R        ← Pre-registration docs (Ravikumar → Roshni)
    ├── E914 - Post Registration           ← Post-registration docs (applications, new e-Khata)
    ├── Notice Sent Acknowledgement Copy GPO
    └── Notice Annexures

Embassy Habitat Legal Documents
    ├── 914 Embassy Habitat Title Documents  ← Historical title docs, ECs
    ├── Discharge Vijaya Bank
    ├── Ravi 2 RNR Closure Documents
    ├── RNR DOCUMENTS
    ├── Sunanda Rathod Legal Report
    ├── Flat Owner Documents
    └── Embassy Habitat Title Document Index (Sheet)
```

**Verification note (Jun 2026):** This hierarchy was confirmed via actual Drive API `files().list()` queries. All folder IDs in the 914 EH structure are valid under Vinod's Drive (Personal → 914 EH Sale Agreements → subfolders). The "Embassy Habitat Legal Documents" tree is a separate top-level folder. Document counts per folder: 20260604 914 EH Ravi — R&R (19 files), E914 - Post Registration (3 files), 914 Embassy Habitat Title Documents (44 files).

**Classification guide:**
| Document Type | Likely Folder |
|---|---|
| Pre-registration docs (old khata, loan docs, seller docs) | `20260604 914 EH Ravi — R&R` |
| New e-Khata in buyer's name | `E914 - Post Registration` |
| ECs (encumbrance certificates) | `914 Embassy Habitat Title Documents` |
| Legal reports, opinions | `Embassy Habitat Legal Documents` |
| Sale deed copies, agreements | `914 EH Sale Agreements` (root) |
| Notices sent to seller | `Notice Sent Acknowledgement Copy GPO` |
| WhatsApp/email correspondence | `Notice Annexures` |

**Pitfall — Multiple Drive folders for same property:** Documents for 914 Embassy Habitat are spread across TWO top-level trees: one under "Personal → 914 EH Sale Agreements" (transaction-specific), another under "Embassy Habitat Legal Documents" (permanent title docs). Choose based on document lifecycle stage.

### Phase 4: Present for Approval

**Always present BOTH filename + folder path to Vinod before uploading.** His working style demands confirmation before any Drive write. Format:

```
**Document extracted:**
- Type: E-Khata
- Property: Flat No. 914, Embassy Habitat
- Owner: Roshini Ranka (W/o Nishant Ranka)
- Doc Date: 05-JUN-2026
- Doc No: GNR-1-00662-2026-27

**Proposed filename:**
20260605_914EH_RoshiniRanka_E-Khata_GNR-1-00662-2026-27.pdf

**Proposed folder:**
Personal → 914 EH Sale Agreements → E914 - Post Registration
```

Wait for his confirmation. Do NOT proceed without it.

### Phase 5: Upload to Drive

Once approved, upload using the gws_auth Drive service:

```python
from googleapiclient.http import MediaFileUpload
drive = build_service("drive", "v3")

media = MediaFileUpload(
    "/data/hermes/document_cache/<cached_filename>",
    mimetype="application/pdf",
    resumable=True
)
file_meta = {
    "name": "20260605_914EH_RoshiniRanka_E-Khata_GNR-1-00662-2026-27.pdf",
    "parents": ["<folder_id>"]
}
uploaded = drive.files().create(body=file_meta, media_body=media, fields="id, webViewLink").execute()
link = uploaded.get("webViewLink")
```

**Important:** The Hermes venv at `/opt/hermes/.venv/bin/python3` must be used with `sys.path.insert(0, '/opt/hermes')` before importing `tools.gws_auth`. System Python cannot import the tools package.

### Phase 6: Generate WhatsApp Notification for Nishant

After upload, create a WhatsApp message draft that Vinod can click-and-send to Nishant. Format:

```
📄 *Document Uploaded — 914 Embassy Habitat*

*Document:* E-Khata (Form A)
*Flat No:* 914, Embassy Habitat
*Owner:* Roshini Ranka
*Doc Date:* 05-JUN-2026
*Doc No:* GNR-1-00662-2026-27

*Drive Link:* <drive_link>

*File Name:* 20260605_914EH_RoshiniRanka_E-Khata_GNR-1-00662-2026-27.pdf
```

Use `whatsapp_link` tool to generate the wa.me deep link with pre-filled message.

**WhatsApp link construction rules (from memory):**
- Use `api.whatsapp.com/send` (not `wa.me`)
- Bold caption on the message
- No "Nishant here" signature
- For long messages: use HTML format
- AMPERSAND: Use Fullwidth ＆ (U+FF06, URL=%EF%BC%86). NEVER %26 or standard & — breaks Android WA link parser. Use `and` word where possible.

**Final deliverable to Vinod:**
1. ✅ Upload confirmation (file uploaded to X folder)
2. ✅ Drive share link
3. ✅ WhatsApp click-to-send link for Nishant
4. ✅ Brief summary of what was done
