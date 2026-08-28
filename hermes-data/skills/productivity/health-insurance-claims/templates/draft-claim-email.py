#!/opt/hermes/.venv/bin/python3
"""
Template: Draft an insurance claim reimbursement email with HTML body and attachments.

This template generates a rich HTML email with styled tables — not plain text.
Copy this file, edit the CONFIG section at the top, then run it.

Requires: uv pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
"""
import sys, base64, os
sys.path.insert(0, '/opt/hermes')
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from tools.gws_auth import build_service

# ===== CONFIGURE HERE =====
TO_EMAIL = "claims@mediassistindia.com"
CC_EMAIL = "customercare@mediassistindia.com"
SUBJECT = "Reimbursement Claim — [Patient] — Policy [Number]"

PATIENT = {
    "name": "Kanta D. Ranka (Mother of Policyholder)",
    "dob": "21-06-1958",
    "age": "68 Years",
    "policy_no": "LLA0016946000107/LLA1/Elite",
    "insurer": "Royal Sundaram General Insurance Co. Ltd",
    "sum_insured": "Rs. 1,50,00,000 (1.5 Crores)",
    "pan": "AHVPR5168E",
    "bank": "Kotak Mahindra Bank — A/c 4447921904",
    "ifsc": "KKBK0008059",
    "phone": "+91 98800 55634",
    "email": "kdr@draas.com",
}

HOSPITAL = {
    "name": "Trustwell Hospitals Pvt Ltd, Bengaluru",
    "procedure": "Right Tympanotomy with CO2 Laser Stapedotomy",
    "diagnosis": "Otosclerosis",
    "surgeon": "Dr. Deepak Haldipur (ENT Surgeon)",
    "admission": "15/07/2026 08:30 Hrs",
    "discharge": "16/07/2026 14:00 Hrs",
    "room": "Single Occupancy (Private)",
}

# Expense items — list of (date, provider, bill_no, description, amount_rs)
EXPENSES = [
    ("09/07/2026", "Trustwell Hospitals", "OPB12630777",
     "Microscopic Wax Removal (B/L) + Pure Tone Audiometry", 2740),
    ("09/07/2026", "Trustwell Hospitals", "OPB12630717",
     "Pre-op Lab Tests + Echo-2D + X-ray Chest + OP Consultation", 15730),
    ("09/07/2026", "Trustwell Hospitals", "OPB12630833",
     "Anaesthesiology OP Consultation", 700),
    ("11/07/2026", "Manipal Hospital", "MHM260CS0047177",
     "Blood Tests (D-Dimer, ANA-IF, Anti-CCP, HAMS)", 9840),
    ("11/07/2026", "Manipal Hospital", "MHM260CS0047124",
     "CT Angiography Pulmonary", 16000),
    ("10/07/2026", "Manipal Hospital", "—",
     "Pulmonary Function Test (PFT) & DLCO", 7100),
]

SENDER_NAME = "Nishant Ranka"
SENDER_MOBILE = "+91 98800 55634"
SENDER_EMAIL = "ndr@draas.com"
# ===== END CONFIGURATION =====


def build_html_body():
    """Build a rich HTML email body with styled tables."""
    total = sum(e[4] for e in EXPENSES)
    trustwell_total = sum(e[4] for e in EXPENSES if "Trustwell" in e[1])
    manipal_total = sum(e[4] for e in EXPENSES if "Manipal" in e[1])

    rows_html = ""
    for i, (date, provider, bill_no, desc, amt) in enumerate(EXPENSES, 1):
        rows_html += f"""<tr>
  <td style="text-align:center;padding:3px 5px;border:1px solid #ccc;">{i}</td>
  <td style="text-align:center;padding:3px 5px;border:1px solid #ccc;">{bill_no}</td>
  <td style="text-align:center;padding:3px 5px;border:1px solid #ccc;">{date}</td>
  <td style="padding:3px 5px;border:1px solid #ccc;">{provider}</td>
  <td style="padding:3px 5px;border:1px solid #ccc;">{desc}</td>
  <td style="text-align:right;padding:3px 5px;border:1px solid #ccc;">{amt:,}.00</td>
</tr>
"""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8">
<style>
  body {{ font-family: Arial, sans-serif; font-size: 10pt; color: #222; }}
  .header {{ background: #1a3a5c; color: #fff; padding: 14px 20px; }}
  .header h1 {{ margin: 0; font-size: 13pt; }}
  .section-title {{ font-size: 10pt; font-weight: bold; color: #1a3a5c; border-bottom: 2px solid #1a3a5c; margin: 12px 0 6px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 9pt; }}
  th {{ background: #e8edf2; border: 1px solid #ccc; padding: 5px 7px; }}
  td {{ border: 1px solid #ccc; padding: 4px 7px; }}
  .grand-total {{ background: #1a3a5c; color: #fff; font-weight: bold; }}
  .footer {{ border-top: 2px solid #1a3a5c; margin-top: 16px; padding-top: 10px; }}
</style></head>
<body>

<div class="header">
  <h1>Reimbursement Claim</h1>
  <p>Policy: {PATIENT['policy_no']} | Sum Insured: {PATIENT['sum_insured']}</p>
  <p>{HOSPITAL['procedure']} — {HOSPITAL['name']}</p>
</div>

<div class="section-title">PATIENT DETAILS</div>
<table>
  <tr><td><b>Policy Holder</b></td><td>{PATIENT['name']}</td></tr>
  <tr><td><b>Policy No.</b></td><td>{PATIENT['policy_no']}</td></tr>
  <tr><td><b>Sum Insured</b></td><td>{PATIENT['sum_insured']}</td></tr>
  <tr><td><b>Age / DOB</b></td><td>{PATIENT['age']} / {PATIENT['dob']}</td></tr>
  <tr><td><b>PAN</b></td><td>{PATIENT['pan']}</td></tr>
  <tr><td><b>Bank</b></td><td>{PATIENT['bank']} (IFSC: {PATIENT['ifsc']})</td></tr>
</table>

<div class="section-title">HOSPITALIZATION</div>
<table>
  <tr><td><b>Hospital</b></td><td>{HOSPITAL['name']}</td></tr>
  <tr><td><b>Admission</b></td><td>{HOSPITAL['admission']}</td></tr>
  <tr><td><b>Discharge</b></td><td>{HOSPITAL['discharge']}</td></tr>
  <tr><td><b>Procedure</b></td><td>{HOSPITAL['procedure']}</td></tr>
  <tr><td><b>Surgeon</b></td><td>{HOSPITAL['surgeon']}</td></tr>
</table>

<div class="section-title">PRE-HOSPITALIZATION EXPENSES CLAIMED</div>
<table>
  <thead><tr>
    <th>#</th><th>Bill No.</th><th>Date</th><th>Hospital</th><th>Particulars</th><th>Amount (Rs.)</th>
  </tr></thead>
  <tbody>
{rows_html}
    <tr><td colspan="4"></td><td style="text-align:right;"><b>Trustwell Subtotal</b></td><td style="text-align:right;">{trustwell_total:,}.00</td></tr>
    <tr><td colspan="4"></td><td style="text-align:right;"><b>Manipal Subtotal</b></td><td style="text-align:right;">{manipal_total:,}.00</td></tr>
    <tr class="grand-total">
      <td colspan="5" style="text-align:right;">TOTAL CLAIMED</td>
      <td style="text-align:right;">{total:,}.00</td>
    </tr>
  </tbody>
</table>

<p style="font-size:8.5pt;color:#666;">Hospitalization (main surgery bill) settled separately by hospital with TPA.</p>

<div class="footer">
  <p>Please process the reimbursement at the earliest.</p>
  <p>Thank you,<br><b>{SENDER_NAME}</b><br>{SENDER_EMAIL} | {SENDER_MOBILE}</p>
</div>

</body></html>"""
    return html


def create_draft():
    gmail = build_service('gmail', 'v1', service_name='google-draas')

    msg = MIMEMultipart('mixed')
    msg['To'] = TO_EMAIL
    msg['Cc'] = CC_EMAIL
    msg['From'] = SENDER_EMAIL
    msg['Subject'] = SUBJECT

    msg_alt = MIMEMultipart('alternative')
    msg_alt.attach(MIMEText(build_html_body(), 'html'))
    msg.attach(msg_alt)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    draft = gmail.users().drafts().create(
        userId='me',
        body={'message': {'raw': raw}}
    ).execute()
    print(f"Draft created: {draft['id']}")
    return draft['id']


if __name__ == "__main__":
    create_draft()
