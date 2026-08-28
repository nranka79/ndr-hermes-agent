# Medical Document Folder Organization

## Structure

For each family member's medical folder, maintain this hierarchy:

```
[Patient] Medical/
├── Prescriptions, Reports, Advisories, Test Results, Lab Forms  (root)
└── Invoices and Bills/  (subfolder)
```

## Document Classification Decision Tree

When receiving scanned medical documents from a visit:

```
Is the document a financial instrument (payment/price)?
  YES → Is it a pharmacy/OP tax invoice with payment details?
          YES → Move to "Invoices and Bills" subfolder
  NO  → Is it a laboratory requisition form?
          YES → Keep in root (clinical request, not financial)
  NO  → Is it a prescription (drug name + dosage + schedule)?
          YES → Keep in root
  NO  → Is it a test report (PFT, blood work, X-ray, ultrasound)?
          YES → Keep in root
  NO  → Is it a doctor's consultation note/advisory/OPD history?
          YES → Keep in root
  NO  → Is it an OP bill / cash memo / payment receipt?
          YES → Move to "Invoices and Bills"
```

## Invoice/Bill Identification

| Filename contains | Classification |
|---|---|
| `Invoice`, `Bill`, `OPBill`, `Receipt`, `Cash Memo` | Move to Invoices |
| `Prescription`, `Rx`, `Drug` | Keep in root |
| `PFT`, `Pulmonary`, `Test`, `X-ray`, `Ultrasound`, `CBC`, `CRP`, `IgE` | Keep in root |
| `HealthCheck`, `FollowUp`, `FirstVisit`, `Consultation`, `History` | Keep in root |
| `LaboratoryRequisitionForm`, `LabReq`, `Requisition` | Keep in root (clinical, not financial) |

## ⚠️ Consultation Advice vs Lab Requisition Distinction

A document listing tests (Hb%, CBC, PT/INR, etc.) with a doctor's name and OP consultation header IS a **Consultation Advice** — not a "lab prescription" or "lab requisition." The doctor examined the patient and wrote these orders as part of the consultation. Label it `_ConsultationAdvice_` in the filename, not `_LabTests_` or `_LabPrescription_`.

Only standalone lab forms (no doctor name, pre-printed hospital form with checkboxes, no consultation fee line) are "Lab Requisitions."

**Rule of thumb:** If the document has a doctor name + "OP CONSULTATION" in the billing, it's a Consultation Advice. Names it as such.

## What Goes Where (Quick Reference)

**Stays in root:** Prescription, PFT / Test Report, Doctor Note, Health Check Record, Medical Summary, Lab Requisition Forms, OPD History & Findings, Consultation Notes

**Move to Invoices and Bills:** OP Bill / Cash Memo, Pharmacy Tax Invoice, Payment Receipt, Laboratory/Diagnostic Bill

## Sending to / Moving Files Between Folders

```python
# Upload new file to main folder
drive.files().create(body={'name': filename, 'parents': [medical_folder_id]}, media_body=media, fields='id, name, webViewLink')

# Create subfolder
folder = drive.files().create(body={'name': 'Invoices and Bills', 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_id]}, fields='id, name')

# Move existing file to subfolder
drive.files().update(fileId=file_id, addParents=invoice_folder_id, removeParents=medical_folder_id, fields='id, name')

# Check contents
contents = drive.files().list(q=f"'{folder_id}' in parents", pageSize=50, fields='files(id, name, mimeType)')
```

## Known Hospital Short Codes

| Hospital | Short Code in Filename | Address | Key Doctors |
|----------|------------------------|---------|-------------|
| Manipal Hospital Millers Road | `ManipalHospital` | Millers Rd, Vasanthnagar, BLR | Dr. Vasunethra Kasargod (pulmonologist), Dr. Satish KS (pulmonologist) |
| Manipal Hospital HAL / Old Airport Road | `ManipalHospital` | 98 HAL Old Airport Rd, Kodihalli, BLR-17 | Dr. Srikanta J T (interventional pulmonologist, ex-Aster CMI). Helpline: 1800-103-4286 |
| Bhagwan Mahaveer Jain Hospital (BMJ) | `BMJHospital` | #17 Millers Rd, Vasanthnagar, BLR-52 | Dr. Bharat Reddy / Dr. Y. Bharath Reddy (pediatric pulmonologist, also at Shishu Hospital). Dr. Nishant Hiremath (emergency). GSTIN: 29AAATBO895L1ZC |
| Aster Hospital | `AsterHospital` | Various locations | Dr. Priyanka (pulmonologist), Dr. Kavitha Bhat (pediatrician) |
| Shishu Children's Hospital | `ShishuHospital` | #30 1st Main Rd, Near Banaswadi PS, BLR-43 | Dr. Y. Bharath Reddy (pediatric pulmonologist). Phone: 080-4247-2424 |
| Rubix Lung Care | `RubixLungCare` | (Nishant's known location) | Dr. Rohan Naick (pulmonologist). Location: https://maps.app.goo.gl/n93KELYWzaX4H6Mw5 |

## NDR / KDR Naming Prefix Conventions (Nishant & Kanta Ranka)

For NDR and KDR, the existing folder contents follow a consistent prefix convention:

| Prefix | Meaning | Example |
|--------|---------|---------|
| `NDR P` | Prescription / Appointment card | `20161122 NDR P Dr Sharath Kumar GopalMedicalCenter` |
| `NDR R` | Report / Result (lab, imaging, audiology) | `20190703 NDR R Ultrasound Abdomen VikramHospital` |
| `NDR A` | Advice / Consultation note | `20190308 NDR A Dr. Sunil Dwivedi VikramHospital` |
| `NDR Receipt` / `NDR Bill` | Invoice / Payment receipt | `20161122 NDR Receipt Dr. Sharath Consultation` |
| `KDR P` | Prescription / Appointment | `20161122 KDR P Dr. Sharath Kumar GopalMedicalCenter` |
| `KDR R` | Report / Result | `20170208 KDR R ECG Dr. Sunil Dwivedi VikramHospital` |
| `KDR A` | Advice / Consultation note | `20190305 KDR A Dr. Sunil Dwivedi VikramHospital` |
| `KDR Bill` | Invoice / Payment receipt | `20160616 KDR Bill Vit D3 Test R.V.Metropolis` |

**For new-style (prefix-date) filenames** use descriptor segments instead:

| Patient | Document Type | Filename Pattern |
|---------|--------------|------------------|
| NDR | Audiological Evaluation | `20260709_NDR_AudiologicalEvaluation_Trustwell.pdf` |
| NDR | Consultation Advice | `20260709_NDR_DrHaldipur_ConsultationAdvice_Trustwell.pdf` |
| NDR | OP Consultation Invoice | `20260709_NDR_OPConsultation_Invoice_Trustwell.pdf` |
| NDR | PTA (test) Invoice | `20260709_NDR_PTA_Invoice_Trustwell.pdf` |
| KDR | Wax Removal + PTA Invoice | `20260709_KDR_WaxRemoval_PTA_Invoice_Trustwell.pdf` |

## Folder Name: "Invoices" vs "Invoices and Bills"

For NDR and KDR Medical folders, the user prefers the subfolder to be named **"Invoices"** (short form). Other family members may use "Invoices and Bills" — follow the existing convention for each patient.

## Naming Convention

```
YYYYMMDD_Patient_HospitalShortCode_Description.pdf
```

```

Examples:
- `20260612_Ruhaan_BMJHospital_LaboratoryRequisitionForm.pdf`
- `20260612_Ruhaan_BMJHospital_Prescription.pdf`
- `20260612_Ruhaan_BMJHospital_PharmacyInvoice_Duolin_TusqDX_Predmet.pdf`
- `20260612_Ruhaan_BMJHospital_OPDCashMemo_XRay_GRBS_Nebulisation.pdf`
- `20260612_Ruhaan_BMJHospital_OPDCashMemo_CRP_CBC_IgE_VitaminD.pdf`
- `20240717_Ruhaan_ManipalHospital_PFT_DrSatishKS_PulmonaryFunction.pdf`
- `20240529_Ruhaan_ManipalHospital_SkinPrickTest_SPT_HDM_Allergy.pdf`
- `20260610_Ruhaan_ManipalHospital_MillersRoad_PharmacyInvoice_Levolin_Budecort.pdf`

## Family Calendar Attendee Emails (Medical)

When creating calendar events for medical appointments:

| Person | Email | 
|--------|-------|
| Nishant Ranka | ndr@draas.com |
| Roshni Ranka (wife) | rnr@draas.com |
| Ruhaan Ranka (elder son) | pebblyshark69@gmail.com |
| Rivaan Ranka (younger son) | rankarivaan@gmail.com |
