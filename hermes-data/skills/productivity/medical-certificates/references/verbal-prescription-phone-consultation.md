# Verbal Prescription from Phone Consultation — Record & File Workflow

**Trigger:** A doctor provides treatment advice over the phone (introduced by a mutual contact). The user needs this advice documented as a formal prescription record on Drive, along with the pharmacy invoice for the medicines purchased, and the doctor's contact saved to both Google Contacts and the DRAAS contacts sheet.

## Workflow (5 phases)

### Phase 1 — Extract Doctor Contact from Visiting Card Image

When the user shares a photo/scan of a visiting card:

1. Run OCR (tesseract) to extract name, phone, organization, specialty
2. Try multiple PSM modes if initial OCR is garbled (especially Indian names)
3. Confirm with the user: "Dr. [Name], [Specialty] at [Hospital] — correct?"
4. Get the correct spelling — voice transcriptions of Indian medical names are unreliable

**Known contact (Jun 2026):** Dr. Rohan Naick (also transcribed as Rohan Naik/Ron Nayak)
- Phone: +91 99720 14077
- Hospital: Sparsh Hospital
- Specialty: Pulmonologist
- Introduced by: Dr. Karthik (Plastic Surgeon, Sparsh Hospital), friend of Manohar Singh

### Phase 2 — Extract Medication Details from Pharmacy Invoice

When the user shares a pharmacy invoice (Adobe Scan PDF):

1. OCR the PDF with `ocrmypdf --force-ocr` then `pdftotext`
2. Extract: Patient name, medicines (name, strength, quantity, price), hospital pharmacy name, date, doctor name on invoice
3. Note: The invoice may be under a different doctor's name (e.g., Dr. Satish KS) than the doctor providing the phone advice (e.g., Dr. Rohan Naick) — this is fine, the invoice is just proof of purchase

**Example (Jun 2026):**
- LEVOLIN 0.63 MG/2.5 ML RESPULES (Levosalbutamol) × 6 — Rs. 121.05
- BUDECORT 0.5 MG/2 ML RESPULES (Budesonide) × 6 — Rs. 127.10
- Total: Rs. 176 — Manipal Hospital Millers Road Pharmacy

### Phase 3 — Create Verbal Prescription Document on Drive

Build a Google Doc with a structured record of the phone consultation:

```
VERBAL PRESCRIPTION — TELEPHONIC CONSULTATION

Patient: [Name], DOB: [DOB], Age: [Age]
Date: [Date of consultation]

Consulting Doctor: Dr. [Full Name]
                   [Specialty]
                   [Hospital]

Introduced by: [Name of introducer], [context]
Contact: [Phone number]

CONSULTATION NOTES
[Brief description of the problem discussed]

DOCTOR'S ADVICE
1. [Medication 1] — [dose], [how to administer]
2. [Medication 2] — [dose], [how to administer]
3. [Follow-up plan] — [condition for escalation]

MEDICINES USED
- [Drug name] x [qty] — [source/pharmacy]

CONTEXT — BACKGROUND
[Relevant medical history, regular physician, current meds]
```

1. Create the doc via Google Docs API
2. Move to the patient's medical folder on Drive
3. Name per convention: `YYYYMMDD_Patient_VerbalPrescription_DrLastName_Hospital_Topic`

### Phase 4 — Upload Invoice to Patient Medical Folder

Upload the pharmacy invoice PDF to the same Drive folder with a descriptive name:
`YYYYMMDD_HospitalPharmacy_Invoice_DrugDescriptions_DrLastName.pdf`

Check for duplicates before uploading.

### Phase 5 — Save Doctor Contact to Both Systems

**A) Google Contacts (People API):**

Do NOT include a `labels` field — People API rejects it with "Invalid JSON payload: Unknown name 'labels'".

```python
people = build('people', 'v1', credentials=creds)
contact = {
    'names': [{'givenName': 'Rohan', 'familyName': 'Naick', 'displayName': 'Dr. Rohan Naick'}],
    'phoneNumbers': [{'value': '+919972014077', 'type': 'mobile'}],
    'organizations': [{'name': 'Sparsh Hospital', 'title': 'Pulmonologist'}],
    'biographies': [{
        'value': 'Introduced by Dr. Karthik (Plastic Surgeon, Sparsh Hospital), friend of Manohar Singh.',
        'contentType': 'TEXT_PLAIN'
    }]
}
created = people.people().createContact(body=contact).execute()
```

**B) DRAAS Contacts Sheet (Google Sheets):**

Use `append` (not `update`) to automatically extend the sheet grid. Column mapping:
- A: First Name, C: Last Name, G: Name Prefix (Dr.)
- J: File As, K: Organization Name, L: Organization Title
- O: Notes (consultation context), Q: Labels (* myContacts)
- R: Phone 1 Label (Mobile), S: Phone 1 Value

## Back-to-Back Nebulization Protocol (Dr. Rohan Naick, Jun 2026)

For Ruhaan's asthma exacerbation where LEVOLIN MDI 2 puffs are not lasting:

1. Neb Levolin 0.63mg (Levosalbutamol — bronchodilator) — one full respule
2. Immediately followed by: Neb Budecort 0.5mg (Budesonide — corticosteroid)
3. Back-to-back (one after the other, NOT mixed in the same chamber)
4. Rationale: Levolin opens the airways first; Budecort penetrates deeper into now-open airways
5. If still not settled by next day — Chest X-ray

## Drive Medical Folder Reference

| Patient | Folder Name | Folder ID |
|---------|-------------|-----------|
| Ruhaan Ranka | Ruhaan Medical | 0B1Oc8cSaJXPGaEhnaDg1Wjl0Q0k |
