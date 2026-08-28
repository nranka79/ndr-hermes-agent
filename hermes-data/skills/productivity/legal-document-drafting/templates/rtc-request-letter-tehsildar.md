# RTC Request Letter — Tehsildar (Karnataka)

Starter letter for requesting certified RTC (Record of Rights, Tenancy and Crops) extracts for a historical period from the Tehsildar. Copy, fill placeholders, regenerate as .docx.

## Structure (proven order)
- Applicant header (centered): FULL NAME (alias if used), address line, phone
- Date
- To: The Tehsildar, <Taluk>, <District>, Karnataka
- Subject (bold, one line): Request for issuance of RTC (Record of Rights, Tenancy and Crops) extracts from the year <start> to <end> in respect of Survey No(s) <X> of <Village> Village, <Hobli>, <Taluk>, <District> – Reg.
- Body: applicant identity (S/o [Father's Name], R/o [address]), the request, purpose (verification of title / legal & property documentation)
- Land details block (bold labels): Village, Hobli, Taluk, District, Survey No(s)
- Enclosures: Aadhaar / photo ID, latest RTC copy if available, other supporting docs
- Fee undertaking: "I shall pay the requisite fee as prescribed by the Department"
- Closing: Thanking you, Yours faithfully, signature line + printed name + phone

## Example subject
"Request for issuance of RTC (Record of Rights, Tenancy and Crops) extracts from the year 1960 to 2002 in respect of Survey No. 2 and Survey No. 2/1 of Pattandur Agrahara Village, K.R. Puram Hobli, Bangalore East Taluk, Bangalore Urban District – Reg."

## Pitfalls
- Address the correct revenue officer: Tehsildar of the taluk containing the village/hobli; confirm whether the RTC office sits at the hobli town or the taluk HQ before despatch.
- Historical/manual-period RTCs (pre-computerization) take longer and can incur search fees per year per survey number — the fee undertaking line covers this.
- Write both years fully ("from the year 1960 to 2002"), never an ambiguous range.
- Fill the [Father's Name] / [Address] placeholders before printing — flagged to the user, not silently left.

## Word-file generation
- python-docx, Times New Roman 12pt, centered applicant header, bold Subject.
- Descriptive filename: `RTC_Request_Letter_<Applicant>.docx` under /data/hermes/.
- Deliver via MEDIA:<path> and list what was filled / what placeholders remain.
