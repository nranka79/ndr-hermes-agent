#!/usr/bin/env python3
"""Build a tenant->beneficiary-firm NOC (registered-office / sub-lease form) as .docx.

A4, Times New Roman 12, 3 pages (letter + schedule annexure). Copy this file and edit
the CONFIG block only. See references/noc-consent-letters-and-sublease.md for the
sibling-firm mirror workflow and the Clause-9(d)-style sublet-restriction flag.

Verified end-to-end Sep 2026: O3 Infotech -> DRA KAAJ and -> R3N KAAJ NOCs at
Prizm Greystone, Cunningham Road, Bengaluru.
"""
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

# ---------------- CONFIG: edit per NOC --------------------------------------
OUT = "/tmp/<Issuer>_NOC_Sublease_<BENEFICIARY>.docx"
TITLE = "NO OBJECTION CERTIFICATE"
SUBTITLE = "(Under the Indian Partnership Act, 1932)"

ISSUER_NAME = "M/s. O3 Infotech Private Limited"
ISSUER_ID = ("a company incorporated under the Companies Act, 2013, having CIN <CIN>, "
             "PAN <PAN>, and its registered office at <Regd Off>, represented herein by "
             "its Director, <Name> (hereinafter referred to as \u201c<Short>\u201d, which "
             "expression shall include its successors and assigns)")
ISSUER_SIG_BLOCK = [("For M/s. <Issuer>", False), ("_____________________________", False),
                    ("Authorised Signatory", False), ("Name: <Signatory>", False),
                    ("Designation: Director", False), ("(Company Seal)", False)]

BENEFICIARY = "M/s. <Firm Name>"
BENEFICIARY_RECITAL = ("a partnership firm constituted under the Indian Partnership Act, 1932 "
                       "and established on <DD Month YYYY>, having its partners <Partners>, "
                       "intends to establish / shift its Registered Office \u2013 Principal Place "
                       "of Business at the Scheduled Premises.")

PRE = "Unit No. 204, 205 & 206, 2nd Floor, Prizm Greystone, Cunningham Road, Bengaluru \u2013 560 052"
RESULTS_IN_INFRA = "<Issuer> is the Lessee and is in lawful possession of the commercial premises " \
    "bearing <Schedule ref> under a Lease Deed dated <DD Month YYYY> (the \u201cLease Deed\u201d) " \
    "executed with <Lessor name>, PAN <Lessor PAN> (<the \u201cLessor\u201d>)."
LEASE_TERM = "The Lease Deed is for a term of <N> years commencing from <Start> and expiring on <End>, and is valid and subsisting as on date."

SCHEDULE_ROWS = [
    ("Unit No.", "<204, 205 & 206>"),
    ("Floor", "<Second Floor>"),
    ("Building", "<\u201cPrizm Greystone\u201d, Commercial Building>"),
    ("Address", "<addr>"),
    ("Extent", "<approx sqft>"),
    ("Car Parks", "<n> mechanical car parks in the basement"),
    ("Municipal Nos.", "<PID numbers>"),
    ("Occupancy", "Held under Lease Deed dated <date> executed between <Lessor> (Lessor) and <Issuer> (Lessee)."),
]
# ----------------------------------------------------------------------------

doc = Document()
for section in doc.sections:
    section.page_width = Cm(21.0); section.page_height = Cm(29.7)
    section.top_margin = Cm(2.54); section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(2.54); section.right_margin = Cm(2.54)

st = doc.styles['Normal']; st.font.name = 'Times New Roman'; st.font.size = Pt(12)
C, R, J = WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.RIGHT, WD_ALIGN_PARAGRAPH.JUSTIFY

def para(text, align=None, bold=False, italic=False, after=6, before=0):
    p = doc.add_paragraph()
    if align is not None: p.alignment = align
    r = p.add_run(text); r.bold = bold; r.italic = italic
    p.paragraph_format.space_after = Pt(after); p.paragraph_format.space_before = Pt(before)
    return p

para(TITLE, align=C, bold=True, after=2)
para(SUBTITLE, align=C, italic=True, after=12)
para("Date: ____________, 2026", align=R, after=2)
para("Place: Bengaluru", align=R, after=12)
para("TO WHOMSOEVER IT MAY CONCERN /", bold=True, after=0)
para("THE REGISTRAR OF FIRMS, KARNATAKA / ANY STATUTORY AUTHORITY", bold=True, after=12)
para(f"Re: No Objection for use, occupation and sub-lease of premises at {PRE} by {BENEFICIARY} "
     "as its Registered Office / Principal Place of Business.", align=J, after=12)
para(f"We, {ISSUER_NAME}, {ISSUER_ID}, do hereby issue this No Objection Certificate as follows:", align=J, after=12)

para("WHEREAS", bold=True, after=4)
para("1. " + RESULTS_IN_INFRA + " (hereinafter referred to as the \u201cScheduled Premises\u201d).", align=J, after=6)
para("2. " + LEASE_TERM, align=J, after=6)
para("3. " + BENEFICIARY + ", " + BENEFICIARY_RECITAL, align=J, after=6)
para("4. <Issuer>, being the Lessee in possession of the Scheduled Premises, is competent and has "
     "the authority to grant this No Objection for the use, occupation and sub-lease of the "
     "Scheduled Premises, subject to the terms of the Lease Deed.", align=J, after=12)

para("NOW THIS NO OBJECTION CERTIFICATE WITNESSETH AS UNDER:", align=J, bold=True, after=8)
clauses = [
 ("A.", f"<Issuer> hereby gives its full, unconditional and irrevocable No Objection and consent to {BENEFICIARY} to use, occupy and/or sub-lease the Scheduled Premises, or any part thereof, as its Registered Office / Principal Place of Business, and for all incidental purposes."),
 ("B.", f"<Issuer> confirms that it has no objection to the name of {BENEFICIARY} being registered / recorded at the Scheduled Premises with the Registrar of Firms, Karnataka, or any other department, authority or agency."),
 ("C.", "<Issuer> confirms that as on the date of this Certificate, there is no subsisting encumbrance, dispute, litigation or third-party claim affecting its right to grant the aforesaid No Objection in respect of the Scheduled Premises."),
 ("D.", f"This No Objection Certificate is issued to enable {BENEFICIARY} to submit the same to the Registrar of Firms, Karnataka, or to any other department / statutory authority, in support of the registration of its Registered Office / Principal Place of Business at the Scheduled Premises."),
 ("E.", "This Certificate is issued without prejudice to the rights and obligations of <Issuer> under the Lease Deed, and is limited to the purpose stated hereinabove."),
 ("F.", "Any intimation, notice or document in connection with the aforesaid use / occupation / sub-lease of the Scheduled Premises may be addressed to <Issuer> at its registered office mentioned hereinabove."),
]
for letter, text in clauses:
    para(f"{letter} {text}", align=J, after=6)

para("We request the Registrar of Firms, Karnataka and all concerned authorities to accept this No "
     "Objection Certificate and to act accordingly.", align=J, after=12)
para("Yours faithfully,", align=J, after=18)
for t, b in ISSUER_SIG_BLOCK:
    para(t, align=J, bold=b, after=2)
para("", after=0)

doc.add_page_break()
para("SCHEDULE OF THE PREMISES", bold=True, align=J, after=8)
para("All that piece and parcel of the commercial premises being:", align=J, after=6)
for k, v in SCHEDULE_ROWS:
    para(f"{k} {v}", align=J, after=6)
para(f"Note: This Schedule forms part of the No Objection Certificate issued by {ISSUER_NAME} in "
     f"favour of {BENEFICIARY}.", italic=True, align=J, after=6)

doc.save(OUT)
print("Saved:", OUT)