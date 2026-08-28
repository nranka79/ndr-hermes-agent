# Offer Letter — Verification Checklist (31-check pattern, Sai Neha Vaddadi build Jun 2026)

Run this checklist on every new offer letter doc BEFORE presenting to the user. Catches the most common errors (lingering previous-candidate name, missing compensation lines, misspelled reporting manager, etc.) in 5 seconds and avoids embarrassing the user.

## The pattern (Python)

```python
import sys
sys.path.insert(0, '/data/hermes')
from tools.gws_auth import build_service

docs = build_service('docs', 'v1')
NEW_ID = '<new_doc_id>'

doc = docs.documents().get(documentId=NEW_ID).execute()
body_text = ""
for element in doc['body']['content']:
    if 'paragraph' in element:
        for run in element['paragraph']['elements']:
            if 'textRun' in run:
                body_text += run['textRun']['content']

# Adjust these checks per role / candidate
checks = [
    # === Candidate-specific (must be present) ===
    ("<Full Name>" in body_text, "Contains '<Full Name>'"),
    # === Candidate-specific (must NOT be present, common STT errors) ===
    ("<wrong_name_1>" not in body_text, "No '<wrong_name_1>' references"),
    # === Compensation lines (33+4+3 = 40k pattern) ===
    ("33,000" in body_text, "Contains Base 33,000"),
    ("4,000" in body_text, "Contains Attendance 4,000"),
    ("3,000" in body_text, "Contains Performance 3,000"),
    ("40,000" in body_text, "Contains Total 40,000"),
    # === Office hours (9:30-10:00 / 6:30-7:00 with 2x30-min break) ===
    ("9:30 am" in body_text, "Contains sign-in window 9:30 am"),
    ("10:00 am" in body_text, "Contains sign-in window 10:00 am"),
    ("6:30 pm" in body_text, "Contains sign-out window 6:30 pm"),
    ("7:00 pm" in body_text, "Contains sign-out window 7:00 pm"),
    # === Personalisation (resume-anchored) ===
    ("<degree>" in body_text, "Personalisation: <degree>"),
    ("<university>" in body_text, "Personalisation: <university>"),
    ("<last_employer>" in body_text, "Personalisation: <last_employer>"),
    ("<tool_1>" in body_text, "Personalisation: <tool_1>"),
    # === Mandatory clauses ===
    ("Gowri Singh" in body_text, "Contains Gowri Singh (reporting manager)"),
    ("Gauri" not in body_text, "No 'Gauri' misspelling"),
    ("Roshini Ranka" in body_text, "Contains Roshini Ranka (signatory)"),
    ("Nishant Ranka" in body_text, "Contains Nishant Ranka (signatory)"),
    ("Bharat H" in body_text, "Contains Bharat H (HR) reference"),
    ("sales1.blr@draas.com" in body_text, "Contains Bharat H's email"),
    ("end of the probationary period" in body_text, "KPI matrix by end of probation"),
    ("twenty (20) such Saturdays" in body_text, "Saturdays max 20/year"),
    ("vegetarianism" in body_text, "Code of conduct: vegetarianism"),
    ("Performance Pay" in body_text, "Performance Pay Earned/Payable/Paid section"),
    # === Letterhead & company ===
    ("DRA REALTY PRIVATE LIMITED" in body_text, "Letterhead entity"),
    ("U70100KA2011PTC058105" in body_text, "CIN present"),
    ("29AAPCS9730H1ZO" in body_text, "GSTIN present"),
    ("Prism Greystone" in body_text or "prism greystone" in body_text, "Work location Prism Greystone"),
    # === HR policy handling ===
    ("2026 DRA HR Policy" in body_text, "HR policy sent separately"),
    # === Date & addressing ===
    ("03 June 2026" in body_text, "Date in header"),
    ("Dear Ms." in body_text, "Salutation 'Dear Ms.'"),
]

passed = 0
for ok, label in checks:
    icon = "PASS" if ok else "FAIL"
    print(f"  {icon}  {label}")
    if ok:
        passed += 1

print(f"\nPassed: {passed}/{len(checks)}")
if passed < len(checks):
    print("Fix failing checks before presenting to user")
```

## Why each category of check exists

| Category | What it catches |
|---|---|
| Candidate-specific present | Wrong candidate name left in by stale `replaceAllText` swap |
| Candidate-specific absent | Previous-candidate name lingering (Pooja->Neha bug from Jun 2026) |
| Compensation lines | Missing components, wrong values, INR formatting issues |
| Office hours | Single time instead of window, "10:00 am fixed" (HR Policy default) vs "9:30-10:00" (user override) |
| Personalisation | Generic opening that didn't anchor on resume, or wrong company/tool |
| Mandatory clauses | Missed reporting manager, signatory, HR email, probation language, vegetarianism |
| Letterhead & company | Wrong CIN/GSTIN (multiple DRA entities — easy to mix up) |
| HR policy handling | "Attached" instead of "sent separately" — a recurring correction |
| Date & addressing | Wrong date, missing salutation, wrong title (Mr./Ms.) |

## Variations by role

- **Probation extension letters** — different checks (no compensation lines; reference to original offer letter; 3-month extension format)
- **Appointment letters** — same compensation + clause checks, but different signatory (sometimes Bharat instead of Roshini+Nishant)
- **Joining letters** — minimal checks; mainly date, candidate name, role, location, reporting manager
- **HR policy revisions** — section-by-section, no compensation

## Visual & Formatting Checks (add to main checklist for all formatted .docx builds)

```python
# After building via python-docx, verify formatting
from docx import Document
doc = Document('/path/to/output.docx')

tables = doc.tables
print(f"Tables found: {len(tables)}")

# Check compensation table has header row
comp_table = None
for t in tables:
    for row in t.rows:
        if any('base' in c.text.lower() or 'pay' in c.text.lower() or 'component' in c.text.lower() for c in row.cells):
            comp_table = t
            break

if comp_table:
    print("PASS — Compensation table found")
    # Check bold on key terms in left column
    for row in comp_table.rows[1:]:  # skip header
        left_cell = row.cells[0]
        if any(run.bold for para in left_cell.paragraphs for run in para.runs):
            print(f"  PASS — '{left_cell.text[:20]}' has bold key term")
        else:
            print(f"  WARN — '{left_cell.text[:20]}' key term NOT bold")
else:
    print("FAIL — No compensation table found (check sections)")

# Check section headers are bold
for para in doc.paragraphs:
    if para.style and 'heading' in para.style.name.lower():
        if any(run.bold for run in para.runs):
            print(f"PASS — Section header '{para.text[:40]}' is bold")
        else:
            print(f"WARN — Section header '{para.text[:40]}' NOT bold")
```

## When to add new checks

Add a new check to this list whenever:
- The user catches an error in a new offer letter doc that wasn't caught by the existing checks
- A new clause is added to the standard offer letter template (e.g. if a "non-compete" clause is added in 2027, add a check for it)
- A new mandatory entity is added (e.g. if DRA opens a TruBuild subsidiary, add a check for the TruBuild CIN)

## Result from the Sai Neha Vaddadi build (Jun 2026)

```
Passed: 31/31
```

No fixups needed — the doc was presented to the user immediately after the check pass.
