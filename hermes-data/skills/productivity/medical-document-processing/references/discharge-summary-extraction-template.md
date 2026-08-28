# Discharge Summary — Field Extraction Template

Extract these fields from Indian discharge summaries. Use the template below to structure extraction.

## Template

```
## IDENTIFICATION
- Patient Name: 
- DOB / Age / Sex: 
- Hospital: 
- IP / UHID / Reg No: 
- Admission Date: 
- Discharge Date: 
- Consultant(s): 
- Specialty: 

## DIAGNOSIS
- Final Diagnosis: 
- Reason for Admission: 

## PROCEDURE
- Procedure Name: 
- Date of Procedure: 
- Surgeon: 
- Anesthesia: 

## MEDICATIONS (Discharge Medication)
| Medication | Dosage | Frequency | Duration |
|------------|--------|-----------|----------|
| Name + strength | e.g. 250 mg | e.g. 1-0-1 | e.g. 7 days |

## FOLLOW-UP
- Review after: X days
- With: Dr. Name
- Location: Department, Hospital
- Priority appointment? Y/N
- Suggested date range (if given): e.g. (25|26)

## RESTRICTIONS / ADVICE
- [list each restriction]

## EMERGENCY CONTACT
- Hospital: [Name], [Phone]

## INSURANCE / SPONSOR
- Sponsor: 
- Insurance: 
```

## Real Example (from KDR Right Stapedotomy, 15 Jul 2026)

```
## IDENTIFICATION
- Patient Name: Mrs. Kanta Ranka
- DOB / Age / Sex: 21/06/1958 / 68Y / Female
- Hospital: Trustwell Hospitals, JC Road, Bengaluru
- IP / UHID / Reg No: 145304TWH-74537/UHID745
- Admission Date: 15/07/2026 08:34
- Discharge Date: 16/07/2026
- Consultant(s): Dr. Deepak Haldipur, Dr. Akshay
- Specialty: ENT

## DIAGNOSIS
- Final Diagnosis: Right Otosclerosis
- Reason for Admission: Surgical Intervention

## PROCEDURE
- Procedure Name: Right Tympanotomy with CO2 Laser Stapedotomy
- Date of Procedure: 15/07/2026
- Surgeon: Dr. Deepak Haldipur
- Anesthesia: GA (General Anesthesia)

## MEDICATIONS
| Medication | Dosage | Frequency | Duration |
|------------|--------|-----------|----------|
| Tab. Diamox | 250 mg | 1-0-1 | 7 days |
| Tab. Sumo | - | 1-0-1 | 4 days |
| Tab. Stugeron | 25 mg | 1/2-1/2-1 | 10 days |
| Cap. Pantop-D | - | 1-0-0 (before food)| 7 days |

## FOLLOW-UP
- Review after: 10 days
- With: Dr. Deepak Haldipur
- Location: ENT OPD, Trustwell Hospital
- Priority appointment? YES — "with prior appointment"
- Suggested date range: 25-26 July 2026

## RESTRICTIONS
- Avoid violent coughing, sneezing, nose blowing
- Avoid heavy weight lifting
- Avoid sudden head movements
- Avoid valsalva
- No outstation travel x 10 days
- No air travel x 2 months

## EMERGENCY CONTACT
- Hospital: Trustwell Hospitals — 080-45666777

## INSURANCE
- Sponsor: MediAssist Insurance (PVT)
- Patient Mobile: 9880055634
```

## Common Indian Discharge Summary Medications

### Ear Surgery (Stapedotomy / Tympanoplasty)
| Brand | Generic | Class | Purpose |
|-------|---------|-------|---------|
| Diamox | Acetazolamide | Carbonic anhydrase inhibitor | Reduces CSF/inner ear pressure; prevents perilymphatic fistula |
| Sumo | Aceclofenac + Paracetamol ± Serratiopeptidase | NSAID + analgesic | Post-operative pain and inflammation |
| Stugeron | Cinnarizine | Calcium channel blocker / vestibular suppressant | Controls vertigo, dizziness after inner ear surgery |
| Pantop-D | Pantoprazole + Domperidone | PPI + prokinetic | Gastric protection against other meds |
| Emeset | Ondansetron | Antiemetic | Nausea prevention (IV in-hospital) |
| Dexona | Dexamethasone | Corticosteroid | Reduces post-op swelling and inflammation |
| Taxim | Cefotaxime | Cephalosporin antibiotic | Prophylactic antibiotic |
| Esomeprazole | Esomeprazole | PPI | Gastric protection (IV in-hospital) |

### General Surgery (Common)
| Brand | Generic | Class | Purpose |
|-------|---------|-------|---------|
| Augmentin | Amoxicillin + Clavulanic acid | Antibiotic | Post-surgical infection prevention |
| Ultracet | Tramadol + Paracetamol | Opioid + analgesic | Moderate to severe pain |
| Dolo 650 | Paracetamol | Analgesic / antipyretic | Mild pain, fever |
| Rabeprazole / Rantac | Rabeprazole / Ranitidine | PPI / H2 blocker | Gastric protection |
| Clexane | Enoxaparin | LMWH anticoagulant | DVT prophylaxis (post-surgery) |

> **Note:** Indian brand names vary by hospital pharmacy. Always identify by the generic name when possible. When a brand is unknown, search the generic via OpenRouter or classify by context (post-op pain = analgesic, vertigo = vestibular, etc.).
