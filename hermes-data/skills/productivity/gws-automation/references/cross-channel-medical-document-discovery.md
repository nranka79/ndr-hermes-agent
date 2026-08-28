# Cross-Channel Medical / Prescription Document Discovery

Search for a specific medical document (prescription, pharmacy invoice, clinical note) across **Drive full-text**, **Gmail threads**, and **email attachments** — combining all three data sources and narrowing by user-provided timeframes.

## Workflow (verified Jun 2026 — Ruhaan nebulization prescription search)

### Step 1: Identify the data sources

For DRAAS users, medical records span:
- **Drive folders** — Ruhaan Medical (`0B1Oc8cSaJXPGaEhnaDg1Wjl0Q0k`), Murjani Medical Invoices, Personal folders
- **Gmail** — Hospital emails (manipalhospitals.com, asterhospital.com), pharmacy invoices, forwarded prescriptions from family members
- **Scanned PDFs** — Older prescriptions may be scanned images with no extractable text

## Extended Family Medical Folders (Siblings)

Beyond Nishant's immediate family (NDR, KDR, DR, Ruhaan, Rivaan), the **Personal** folder also contains folders for extended family members:

```
My Drive / Personal /
  ├── NDR Medical
  ├── KDR Docs / KDR Medical
  ├── DR Medical
  ├── SDR Medical
  ├── SMR Medical
  └── Mamta Rathod / MRR / Mamta Rathode /   (Sister: Mamta Ranjeet Rathod)
       └── Medical
```

**Naming variants for Mamta's folder:** The folder may use any of these name forms — `Mamta Rathod`, `MRR`, or `Mamta Rathode`. When searching, enumerate all three variants in the Drive query.

**Common documents in Mamta's Medical folder:**
- Thyrocare blood test reports
- Other diagnostic lab reports
- Prescriptions and consultation notes

### Step 2: Parallel search — Drive full-text + name search

```python
# Broad full-text search (covers OCR'd content in Drive)
q = "fullText contains 'nebul' and trashed=false"
results = drive.files().list(q=q, fields="files(id, name, mimeType, modifiedTime)").execute()

# Narrow by name + content
q2 = "name contains 'Ruhaan' and fullText contains 'nebul'"
```

### Step 3: Gmail timeboxed search

When user says "August or September of last year", translate to date ranges:

```python
query = "from:manipal Ruhaan after:2025/08/01 before:2025/10/01"
results = gmail.users().messages().list(userId="me", q=query).execute()
```

**Key hospital senders for NDR's family:**
| Sender | Domain | Content |
|---|---|---|
| Manipal Hospital | noreply@manipalhospitals.com | OP bills, pharmacy invoices, consultation receipts |
| Aster Hospital | *(various)* | Pulmonology consultations, lab reports |
| Pharmeasy | no-reply@axelia.in | Lab report delivery |
| Thyrocare | reports@thyrocare.com | Lab test reports (Mamta Rathod, KDR, others) |
| Family members | rnr@draas.com, rmurjani@gmail.com | Forwarded prescriptions |

### Step 4: Extract and scan email attachments

Walk the MIME payload tree to find attachments, download via `messages().attachments().get()`, decode with `base64.urlsafe_b64decode()`, save to `/tmp/`, and analyze with `fitz` (PyMuPDF). Search the extracted text for medication keywords.

### Step 5: Cross-reference pharmacy invoices with OP bills

Pharmacy invoices from Manipal Hospital contain **medication details with batch numbers and quantities**, while OP bills show the **doctor and department**. Together they form a complete prescription record:

```
Pharmacy Invoice: FORAPRL 0.5 MG/2 ML RESPULES × 20, MRP ₹1,419.94
OP Bill:           Dr. Vasunethra Kasargod, Respiratory Medicine & Pulmonology
Date:              4 Sep 2025
```

### Common respiratory medication keywords

| Keyword | Medication Form | Type |
|---|---|---|
| `nebul` / `respule` | Budesonide/Formoterol solution | Nebulization |
| `Foracort` | Inhaler (Budesonide+Formoterol) | Maintenance inhaler |
| `Levolin` / `Asthalin` | Inhaler (Salbutamol) | Rescue inhaler |
| `budesonide` | Steroid respule/inhaler | Anti-inflammatory |
| `Montek LC` | Tablet (Montelukast+Levocetirizine) | Anti-allergy |
| `Predmet` / `Methylprednisolone` | Tablet | Acute steroid |
| `SLIT` / `sublingual` | Immunotherapy drops/tablets | Allergy immunotherapy |
| `HDM` / `house dust mite` | Allergen | Common asthma trigger |
| `prick` / `skin prick` | Allergy skin test | Diagnostic |
| `IgE` / `specific IgE` | Blood test | Allergy antibody test |
| `RAST` / `ImmunoCAP` | Blood test | Allergy antibody quantification |

### Skin prick / allergy test search (often not in Drive)

Skin prick test results are often physical printouts handed to the patient at the clinic — NOT emailed or saved to Drive. If the user says "the skin prick test results are already there with us":

1. Search Drive thoroughly with keyword variants: `prick`, `aller`, `IgE`, `skin`, `HDM`, `mite`, `dust`, `slit`, `rasp`, `immuno`, `immunocap`
2. Search Gmail with the same keywords + patient name
3. If both return nothing, the test was likely a physical document handed to the patient. Tell the user it wasn't found digitally — they may need to scan/upload it.

**⚠️ Doctor name transcription trap:** Voice transcriptions of medical names are unreliable. The user's voice said "Dr. Vasundhara Rajya" — the actual doctor's name from the PDF was **Dr. Vasunethra Kasargod** (Respiratory Medicine & Pulmonology, Manipal Hospital Millers Road). Always read the actual document/email to get the correct name, not the voice transcription.

### Step 6: Upload to the correct folder with naming convention

Ruhaan Medical folder ID: `0B1Oc8cSaJXPGaEhnaDg1Wjl0Q0k`

Name per DRAAS convention: `YYYYMMDD_Patient_Hospital_Description.pdf`

### Pitfalls

- **fitz returns empty for scanned prescriptions** — try `pdftoppm` + tesseract or render to PNG + `vision_analyze`
- **Google Docs** need `drive.files().export(fileId, mimeType='text/plain')` not `get_media`
- **Email thread deduplication** — same attachment can appear in forwarded messages multiple times in one thread
- **User provides approximate timeframe** — always translate "August or September of last year" to an explicit date range query relative to current year. Last year = current_year - 1.
