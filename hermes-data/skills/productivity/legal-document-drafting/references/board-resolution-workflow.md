# Board Resolution & Covering Letter Workflow

Covers Board Resolutions of DRA Realty Pvt Ltd for partnership reconstitution matters and covering letters to the District Registrar / Registrar of Firms for Karnataka.

## Board Resolution for Reconstitution

### When Needed
- DRA Realty is a partner in the reconstituted firm (Managing Partner)
- The Board must approve: name change, profit ratio change, new property contributions, capital commitments
- The resolution authorises the Director (Mr. Nishant Dinesh Ranka) to execute all documents

### Required Structure

```
╔═══════════════════════════════════════════╗
║        DRA Realty Pvt Ltd                 ║  ← Bold, 18pt, CENTERED
║                                           ║
║  CIN: U70100KA2011PTC058105 | PAN: AAPCS9730H  ← 9pt, centered
║  Registered Office: 201A/202BA, Queens Corner,
║  No.3, Queens Road, Bangalore - 560 001        ← 9pt, centered
║                                           ║
║  ═══════════════════════════════════════  ║  ← Separator line
║                                           ║
║          BOARD RESOLUTION                 ║  ← Bold, 14pt, centered
║   [Passed by the Board of Directors       ║
║            on DD.MM.YYYY]                 ║
║                                           ║
║  RESOLVED THAT [...]                      ║
╚═══════════════════════════════════════════╝
```

### Required Clauses

1. **Managing Partner**: State that DRA Realty Pvt Ltd is the Managing Partner of the reconstituted Firm, represented by its Director Mr. Nishant Dinesh Ranka, who shall operate bank accounts, execute documents, and conduct business affairs.

2. **Change of Firm Name**: Old name → new name, effective date.

3. **Change of Profit-Sharing Ratio**: Old ratio → new ratio (51:49).

4. **Contribution of New Properties**: List Schedule A, B Parts A & B, C — with brief description (full particulars in attached deed).

5. **Capital Contribution**: Total commitment (₹10 Cr), broken into already-contributed vs balance (with conditions precedent).

6. **Authorisation**: Mr. Nishant Dinesh Ranka, Director of the Company and designated representative of the Managing Partner, is authorised to execute and register the Reconstitution Deed, Contribution Deeds, Section 281 applications, and appear before authorities.

7. **RESOLVED FURTHER THAT**: Certified copy to be furnished to authorities.

### CA Attestation (Required)

Add as a separate block at the bottom after signatures:

```
═══════════════════════════════════════════

CA ATTESTATION

Certified that the foregoing is a true and correct copy of the Resolution
passed by the Board of Directors of DRA Realty Pvt Ltd at its meeting held
on ______________ 2026, and the same has been recorded in the Minutes Book
of the Company.

Place: Bangalore
Date: ______________ 2026

_________________________
Chartered Accountant
(Firm Name: ____________________)
Membership No.: ____________________
UDIN: ____________________
FRN: ____________________
```

### Signature Block

```
_________________________              _________________________
Mr. Nishant Dinesh Ranka              Mr. Ashok Kumar
Director, DRA Realty Pvt Ltd          Partner
(Designated Representative of
 the Managing Partner)
```

### Creation Method (Google Doc)

Use HTML-to-Doc import (not Docs API batchUpdate for new docs):

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

drive = build_service('drive', 'v3')

html = """<html>...letterhead+content in styled HTML...</html>"""
with open('/tmp/resolution.html', 'w') as f:
    f.write(html)

media = MediaFileUpload('/tmp/resolution.html', mimetype='text/html')
file_metadata = {
    'name': 'YYYYMMDD_Board_Resolution_Description',
    'mimeType': 'application/vnd.google-apps.document',
    'parents': [TARGET_FOLDER_ID]
}
drive.files().create(body=file_metadata, media_body=media).execute()
```

To update an existing doc (add CA attestation, modify text), use Docs API batchUpdate with insertText/updateTextStyle/deleteContentRange.

### Pitfalls
- Do NOT use numbered lists that depend on auto-numbering — Google Docs HTML import may not preserve them
- The CA Attestation should be inserted AFTER signatures, not before
- Letterhead must be centered (alignment: CENTER, not LEFT)
- Company name = 18pt bold, CIN/Regd Office = 9pt, BOARD RESOLUTION heading = 14pt bold
- For existing .docx files, use get_media to download, edit with python-docx, then update via Drive API
- Use the same parent folder for consistency
- **Docs API batchUpdate indices shift between requests in a batch**: after an early insertText at index N, later requests' indices refer to the EVOLVED doc, not the original — multi-edit batches with precomputed indices mangle the doc. For multi-edit rewrites, REBUILD via HTML import into a new file, verify, delete the corrupted one. See `references/board-resolution-authorized-signatory.md` for the full incident.
- **Authorized Signatory (omnibus) resolutions** (appointing a Director as signatory for all projects/firms where DRA Realty is partner): one resolution + certified copies per entity is standard practice — full structure, verified firm PAN/GSTIN/Firm Regn Nos (Thindlu SJN-F655-2024-25, Sevaganapalli SJN-F490-2023-24), and Northstar caveat (DRA Realty NOT a partner → cannot authorize there) in `references/board-resolution-authorized-signatory.md`.
- Use the same parent folder for consistency

---

## Board Resolution for Authorized Signatory (Omnibus, Multiple Projects)

### When Needed
- The Company (DRA Realty) is itself the executing entity and/or a partner in firms where projects are executed (e.g. Ranka Amber / Udaya / Oasis)
- The Board appoints a Director (Nishant Dinesh Ranka) as AUTHORIZED SIGNATORY for banks, RERA, authorities, and firm signings

### One resolution or one per project? (NDR asked, Aug 2026)
- **STANDARD PRACTICE: ONE omnibus resolution** with a Schedule of all projects/entities, dated once. Banks/authorities accept a certified true copy naming their entity; separate resolutions per entity are only needed if a specific bank/authority insists.
- **Hard flag:** if the Company is NOT a partner in a firm (e.g. RANKA NORTHSTAR → DRA Ranka Holdings = Nishant + Roshni only), the company board resolution grants NO signatory power inside that firm. Exclude it from the Schedule or mark "Company is not a partner"; that firm's signatory authority flows from the firm's own partner resolution.

### Required Structure (follows the reconstitution letterhead)
1. Letterhead: company name 18pt bold centered, CIN/PAN + Registered Office 9pt centered, separator, BOARD RESOLUTION 14pt centered
2. Meeting particulars: date/time, directors present with DINs, quorum, **appointee abstains** → passed by the other director
3. RESOLVED THAT: appointment of Nishant Dinesh Ranka (DIN 00298854) as Authorized Signatory
4. Powers a–i: bank accounts/cheques; documents before RERA/DTCP/BDA/BBMP/revenue/Sub-Registrar; represent Company as partner in the firms; engage professionals; appoint/revoke co-signatories; ROC/IT/GST/Registrar-of-Firms filings; partner meetings + partnership/reconstitution deeds; courts/tribunals; catch-all
5. Schedule table: Project | Executing Entity | Entity Details (include PAN, GSTIN, Firm Regn No. — see `references/dra-firm-registration-details.md`)
6. Validity & ratification: effective date, "singly or jointly per mandates of banks/firms", ratification of prior acts
7. RESOLVED FURTHER: certified copies to authorities/banks/Registrar of Firms/RERA
8. Certified True Copy signed by the OTHER director (Kishan Nair Murjani DIN 05005329)
9. **SPECIMEN SIGNATURE block** for the appointee (banks require it)
10. CA attestation block (per NDR preference)

### Pitfalls
- Resolution date can predate firm registration (Thindlu reg 27 Sep 2024, Sevaganapalli reg 19 Aug 2023 vs a 5.4.2023 resolution) — the ratification clause covers prior acts, but flag the discrepancy to the user if date accuracy matters.
- Firm registration numbers must come from source certs (PAN/GST/Regn-Ack PDFs), never guessed. PAN cards are often image-based PDFs → `pdftoppm -png` + `tesseract` OCR (pdftotext returns empty).

## Covering Letter to District Registrar / Registrar of Firms

### Purpose
A covering letter accompanies the Deed of Reconstitution when submitting it for registration. It explains to the Registrar what is being submitted and why.

### Key Rule: CRISP — No Detailed Schedules
The covering letter is NOT the deed. Do NOT include detailed property tables (survey numbers, extents, boundaries). Those belong in the Deed of Reconstitution. The covering letter should only:
- State which changes have been made
- Declare why original properties are excluded (with reason)
- List the new property names briefly (Schedules A, B, C — no detailed breakdown)

### Structure

| Section | Content |
|---------|---------|
| **Date** | Date of submission |
| **Addressee** | The District Registrar, [Office location] |
| **Subject** | Submission of Deed of Reconstitution — Change of Firm Name and Reconstitution — [Firm name] — [Firm No.] |
| **Introduction** | Who we are, what we're submitting |
| **§1 — Changes** | Three bullet-style items: Name change, Profit ratio change, New property contribution (brief) |
| **§2 — Declaration** | Original Schedules excluded + REASON (title documents did not complete due diligence) |
| **§3 — Request** | Bullet list + request to register |
| **Signatures** | Both partners |

### Reason for Exclusion of Original Properties
Use this exact language:
> "This is on account of the fact that the title documents of the said properties did not complete the due diligence process as per the requirements of the reconstituted Firm."

### Pitfalls
- Do NOT copy the full Schedule tables from the deed into the covering letter — the user will ask you to remove them
- Keep each section to 2-4 sentences max
- The reason for exclusion must appear in BOTH the Declaration section AND the Request bullets

---

## Form 2 (Notice of Change of Firm Name)

### Under the Karnataka Partnership (Registration of Firms) Rules, 1995
Prescribed under Section 63(1) of the Indian Partnership Act, 1932 and Rule 10.

### When Only Name Change is Being Filed
- Tick ONLY the "Change in firm name" checkbox — uncheck ALL others
- Declaration should state "no change in partners"
- Document attachments follow a specific list

### Document Attachment List (Name Change Only)

| # | Document |
|---|----------|
| 1 | Certified copy of the Original Partnership Deed |
| 2 | Copy of Acknowledgement of Partnership Deed Registration |
| 3 | Certified copy of the Deed of Reconstitution of Partnership |
| 4 | Copy of Aadhaar Card of individual partner(s) |
| 5 | Copy of PAN Card of individual partner(s) |
| 6 | Copy of Certificate of Incorporation of corporate partner |
| 7 | Copy of PAN Card of corporate partner |

### Pitfalls
- Do NOT include profit-sharing or property contribution tables if the change is ONLY name change
- The "Nature of Change" checkboxes must be precise — only what actually changed
- Declaration must explicitly note that partners remain the same (no change in constitution beyond name)

---

## Board Resolution — Authorized Signatory (DRA Realty as Corporate Partner)

### When Needed
- DRA Realty appoints a Director (Mr. Nishant Dinesh Ranka, DIN 00298854) as AUTHORIZED SIGNATORY for projects executed by the company itself and by partnership firms where DRA Realty is a partner.
- One OMNIBUS resolution (dated + Schedule of projects/entities) is standard practice — the board decision is a single act; banks/authorities receive certified true copies referencing the Schedule. Do NOT draft one resolution per project unless a bank insists.
- Caveat: a DRA Realty board resolution confers NO authority inside a firm where DRA Realty is NOT a partner (e.g. DRA Ranka Holdings = Nishant + Roshni) — include only as acknowledgment or exclude; firm-level authority needs the firm's own partner resolution.

### Verified Firm Identifiers (from firm-related docs folders, Aug 2026)
| Firm | PAN | GSTIN | Firm Regn No (Karnataka, Shivajinagar) | Regn date |
|------|-----|-------|----------------------------------------|-----------|
| DRA Thindlu Land Partners (RANKA UDAYA) | AAXFD2296G | 29AAXFD2296G1ZS | SJN-F655-2024-25 | 27 Sep 2024 |
| Seveganapalli Land Partners (RANKA OASIS) | AFCFS4430H | 29AFCFS4430H1ZY | SJN-F490-2023-24 | 19 Aug 2023 |
- Both firms registered AFTER 5.4.2023 (resolution date may predate registration — ratification clause covers prior acts).

### Sign-off Practice
- Appointee (Nishant) abstains from voting; resolution passed by the other director, Mr. Kishan Nair Murjani (DIN 05005329), who certifies the Certified True Copy.
- Include: board meeting particulars (directors present, quorum), expanded powers list (bank ops, RERA/DTCP/BDA/BBMP filings, ROC/IT/GST/Registrar of Firms, partner-meeting representation + partnership/reconstitution deeds, courts/tribunals), validity ("singly or jointly", until revoked), ratification, SPECIMEN SIGNATURE block, CA attestation.

### PITFALL — Google Docs batchUpdate with hardcoded indices CORRUPTS the doc
Multi-request batchUpdate (insertText/deleteContentRange at absolute indices) is applied SEQUENTIALLY — after the first insertion shifts all later indices, subsequent requests land in the wrong place (identifiers inserted mid-sentence, specimen block into table header). For substantial edits: REBUILD via fresh HTML import (Drive files().create with text/html) into a new doc, verify via export, then trash the old one. Do NOT attempt index-based batchUpdate surgery.

---

## Authorized Signatory Resolutions (Multiple Projects / Corporate Partner)

For appointing a Director as Authorized Signatory across several projects/entities at once (company itself + partnership firms where the company is a partner), see `references/board-resolution-authorized-signatory.md`. Key points:
- **ONE omnibus resolution** with a Schedule of projects/entities is standard practice — issue certified copies/extracts per entity, do NOT re-pass per firm.
- **Authority caveat**: the company's board resolution only grants power where the company is a party. If the company is NOT a partner in a firm (e.g. DRA Ranka Holdings / Northstar), flag it — authority there flows from the firm itself.
- Firm bank accounts may also want the firm's own partner resolution.
- Includes verified entity data (DINs, CIN/PAN, firm partner compositions) and the build_service service_name gotcha.
