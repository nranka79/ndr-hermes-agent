# KDR Medical Filing Conventions

**Domain reference for clinical-dossier skill** — Governs where and how KDR (Kanta D. Ranka) medical documents are filed on Google Drive.

## Folder Structure

```
KDR Medical/                          (ID: 0B1Oc8cSaJXPGUUtVbTJHb0Y3V2s)
├── (medical records go here root)     — Consultation advices, discharge summaries, lab reports, scans
└── Invoices/                          (ID: 1jNhEYEe1i2bEdcvQ2Lg9GG2XH4b9mpnu)
    └── — Payment receipts, bill copies
```

### Rules
- **Consultation advice / medical notes / prescriptions** → root of `KDR Medical/`
- **Invoices / payment receipts** → `KDR Medical/Invoices/`

## Naming Convention

Standard format for KDR medical documents:

### Consultation Advice / Medical Reports
```
YYYYMMDD_KDR_Description_Hospital.pdf
```
Examples:
```
20260725_KDR_Trustwell_Haldipur_Consultation_Advice.pdf
20260709_KDR_DrHaldipur_ConsultationAdvice_Trustwell.pdf
20260716_KDR_DischargeSummary_Stapedotomy_Trustwell_DrHaldipur.pdf
20230606_KDR_AudiologicalEvaluation_Trustwell_DrHaldipur.pdf
```

### Invoices
```
YYYYMMDD_KDR_Description_Hospital_RsAmount.pdf
```
Example:
```
20260725_KDR_Trustwell_Haldipur_Consultation_Invoice_Rs700.pdf
```

## Drive Permissions

After uploading any file to KDR Medical, set `anyoneWithLink` reader permission:
```python
service.permissions().create(
    fileId=FILE_ID,
    body={'type': 'anyone', 'role': 'reader'}
).execute()
```

## Folder IDs Quick Reference

| Folder | Drive ID |
|--------|----------|
| KDR Medical (root) | `0B1Oc8cSaJXPGUUtVbTJHb0Y3V2s` |
| KDR Medical > Invoices | `1jNhEYEe1i2bEdcvQ2Lg9GG2XH4b9mpnu` |

## Post-Consultation Admin Flow

After a KDR consultation:
1. Upload advice to KDR Medical root
2. Upload invoice to KDR Medical > Invoices
3. Extract medication schedule (trust the user's description)
4. Create calendar follow-up with guests: Nishant (ndr@draas.com), KDR (kdr@draas.com), Bharat Hawaldar (sales1.blr@drahomes.in)
5. WhatsApp medication message to KDR's number (+919900133634)

## Contact Quick Reference

| Person | Phone | Email | Role |
|--------|-------|-------|------|
| Kanta Ranka (KDR) | +91 99001 33634 | kdr@draas.com | Patient |
| Nishant Ranka (NDR) | +91 98800 55634 | ndr@draas.com | Primary contact |
| Bharat Hawaldar | +91 99000 29200 | sales1.blr@drahomes.in | Care coordinator |
| Dr. Deepak Haldipur | 080-45666789 | — | ENT, Trustwell Hospitals |
