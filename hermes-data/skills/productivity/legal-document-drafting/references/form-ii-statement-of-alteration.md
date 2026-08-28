# Form II — Statement of Alteration in Firm Name or Place of Business (Karnataka)

## When to Use

When the user asks you to prepare **Form II** under **Rule 3** of the Karnataka Partnership (Registration of Firms) Rules, 1995 and **Section 60(1)** of the Indian Partnership Act, 1932 — for changing the **name of the firm** or the **location of the principal place of business** (or both).

Do NOT confuse with **Form 2** (Sec 63(1), Rule 10 — notice of change in constitution) or **Form 3** (Sec 63(2), Rule 11 — name change under constitution change). See `form-2-notice-of-change.md` for those.

| Form | Section | Rule | Purpose |
|------|---------|------|---------|
| **Form II** | S.60(1) | Rule 3 | Alteration of firm name OR principal place of business |
| **Form 2** | S.63(1) | Rule 10 | Notice of change in constitution (PSR, partner changes, capital) |
| **Form 3** | S.63(2) | Rule 11 | Name change under constitution change (filed alongside Form 2) |

## Form Structure

Form II is simpler than Form 2. It has:

### 1. Header / Intro Paragraph
```
Statement of alteration in the firm or in the location of the 
principal place of business, presented or forwarded to the 
Registrar of Firms for filing by
[M/s. FIRM NAME]
(Now known as M/s. NEW FIRM NAME)     ← add this line for name changes
```

### 2. Partner Declaration (Prefatory)
```
We, the undersigned, being the partners of the firm *
[M/s. FIRM NAME]
hereby supply the following particulars in pursuance of 
section 60(1) of the Indian Partnership Act, 1932.
```

### 3. Principal Place of Business

The blank template has a text label `"Principal place of Business. ………………"` followed by **Table 2 (Place of Business)**. Both coexist:
- The text label stays as-is (or cleaned up to `"Principal place of Business:"`)
- Table 2 holds the actual address values (Previous place | New place)

Do NOT rely on the text line alone — the Registrar uses the table columns. See Tables section below.

### 4. Tables

**Table 1 — Name of the Firm (2 columns × 4 rows)**
| Row | Col 0 | Col 1 |
|-----|-------|-------|
| 0 | Name of the Firm | Name of the Firm |
| 1 | Previous Name | New Name |
| 2-3 | (previous name) | (new name) |

**Table 2 — Place of Business (2 columns × 2 rows)**
| Row | Col 0 | Col 1 |
|-----|-------|-------|
| 0 | Previous place | New place |
| 1 | (address) | (address) |

If the address hasn't changed, enter the same address in both columns.

### 5. Station & Date
```
Station: [City]    Signature of the partners or their Specially authorised agent.
Date: [DD.MM.YYYY]
```

### 6. Partner Declaration Blocks (up to 7)

Each block follows this pattern across **3 paragraphs**:

**Line 1 (Name + Occupation):**
```
I    [Partner Name]    [Occupation/Designation]    son    of
```
The first tab after the name is for **occupation/designation** (e.g. "Partner", "Director of M/s...", "Merchant"), NOT the father's name.

**Line 2 (Father + Age + Declaration):**
```
[Father's full name], aged about [age] years, [Description/Title of Partner] Do hereby declare that the above statement
is true and correct to the best of my knowledge and belief.
```

**Line 3 (Date + Witness):**
```
Date: [DD.MM.YYYY]    Witness    Signature
```

**Example — Individual Partner:**
```
Line 1: I    Mr. Ashok Kumar    Partner    son    of
Line 2: Mr. Ram Kumar, aged about 55 years, Partner of the said firm. Do hereby declare that the above statement
        is true and correct to the best of my knowledge and belief.
Line 3: Date: 27.07.2026    Witness    Signature
```

**Example — Company as Partner (represented by Director):**
```
Line 1: I    Mr. Nishant Dinesh Ranka    Director of M/s DRA Realty Pvt Ltd    son    of
Line 2: Shri Dinesh Ranka, aged about 45 years, the Managing Partner of the said firm. Do hereby declare that the
        above statement is true and correct to the best of my knowledge and belief.
Line 3: Date: 27.07.2026    Witness    Signature
```

Only fill as many blocks as there are partners. Leave the rest blank/empty.

## Data Sources

| Field | Source Document |
|-------|----------------|
| Previous firm name | Registration Certificate / Form C / Partnership Deed |
| New firm name | Deed of Reconstitution or user instruction |
| Registered address | Registration Certificate / Partnership Deed / Enterprise Data |
| Partner names | Deed of Reconstitution (identify all continuing partners) |
| Partner father's name | Deed of Reconstitution (if stated) or leave as `[Not stated]` |
| Partner age | Deed of Reconstitution (as "aged about X years") |
| Corporate partner rep | Deed of Reconstitution (e.g. "represented by Mr. X, Director") |
| Date of signing | Today's date, or the date the deed was executed |

## Filling the Form (python-docx technique)

The uploaded form is typically a .docx with fill-in placeholders. The most reliable approach is **paragraph-index-based assignment** rather than searching for placeholder patterns.

### Step 1: Print all paragraphs to find indices
```python
from docx import Document
doc = Document('form.docx')
for i, p in enumerate(doc.paragraphs):
    print(f"[{i}] '{p.text}'")
```

### Step 2: Assign directly by index
```python
doc.paragraphs[6].text = "M/s. OLD FIRM NAME"
doc.paragraphs[7].text = "(Now known as M/s. NEW FIRM NAME)"
doc.paragraphs[10].text = "M/s. OLD FIRM NAME"
doc.paragraphs[19].text = "Station: Bengaluru\tSignature of the partners..."
doc.paragraphs[20].text = "Date: 27.07.2026\t"
```

### Step 3: Fill tables by row/column index
```python
t = doc.tables[0]
t.rows[1].cells[0].text = old_name
t.rows[1].cells[1].text = new_name

t = doc.tables[1]
t.rows[1].cells[0].text = address
t.rows[1].cells[1].text = address  # same if unchanged
```

### Step 4: Fill partner declaration blocks
Each partner has 3 sequential paragraphs:
- First: `I\t[Name]\t[Occupation/Designation]\tson\tof`  (occupation between name and "son of")
- Second: `[Father's full name], aged about [age] years, [Description/Title] Do hereby declare...`
- Third: `Date:\tWitness\tSignature`

```python
# Partner 1 — Individual partner
doc.paragraphs[22].text = f"I\t{name1}\t{occupation/designation}\tson\tof"
doc.paragraphs[23].text = f"{father1}, aged about {age} years, {desc} Do hereby declare..."
doc.paragraphs[25].text = "Date:\tWitness\tSignature"

# Partner 2 (starts ~6 paragraphs after Partner 1's signature line)
doc.paragraphs[28].text = f"I\t{name2}\t{occ2}\tson\tof"
doc.paragraphs[29].text = f"{father2}, aged about {age} years, {desc2} Do hereby declare..."
doc.paragraphs[30].text = "Date:\tWitness\tSignature"
```

### Step 5: Clear unused blocks
```python
for i in range(last_used + 1, len(doc.paragraphs)):
    doc.paragraphs[i].text = ""
```

### Step 6: Upload as Google Doc
```python
output = io.BytesIO()
doc.save(output)
output.seek(0)

media = MediaIoBaseUpload(output, 
    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    resumable=True)

uploaded = drive_service.files().create(
    body={'name': filename, 'parents': [FOLDER_ID], 
          'mimeType': 'application/vnd.google-apps.document'},
    media_body=media
).execute()
```

## Pitfalls

- **❗ Never do global text replacement on "…………" patterns.** The dot placeholder pattern appears in EVERY field — firm name, address, partner name, father's name, date. Replacing all dots globally will corrupt the entire form. Always use paragraph-index-based assignment.
- **❗ Paragraph indices shift if the template changes.** The indices above (6, 7, 10, etc.) are for a specific blank Form II. If a different template is uploaded, print all paragraphs first and identify the correct indices.
- **❗ Corporate partners — declaration format matters.** When a partner is a **company** (e.g. DRA Realty Pvt Ltd), the declaration uses the DIRECTOR's personal name in the "I" field — NOT the company name. Example:
  - ✅ Correct: `I    Mr. Nishant Dinesh Ranka    Director of M/s DRA Realty Pvt Ltd    son    of`
  - ❌ Wrong: `I    M/s DRA Realty Pvt Ltd (represented by Mr. Nishant Ranka)    ...    son    of`
  
  The occupation/designation field (between name and "son of") should state their role in the company. The description on line 2 should state their role in the partnership (e.g. "the Managing Partner of the said firm").
  
- **❗ The occupation/designation field is NOT the father's name.** The template has this structure:
  ```
  I    [Name]    [Occupation/Designation]    son    of
  [Father's full name], aged about [age] years, [Description] Do hereby declare...
  ```
  The field between [Name] and "son of" takes the person's occupation/role (e.g. "Partner", "Director of M/s X"), NOT their father's name. The father's name goes on the next line.
- **Father's name:** For individual partners, fill from the Deed of Reconstitution if available. If not available, leave blank or use `[Not stated]` — the Registrar will accept it.
- **Principal place vs registered address:** These are usually the same address. If the place of business has changed, fill the new address in Table 2's "New place" column.
- **Date format:** Use DD.MM.YYYY format (standard for Indian government forms).
- **Filename convention:** Prefix with YYYY.MM.DD (e.g. `2026.07.27_FormII_Change_of_Firm_Name_OLD_to_NEW`).
- **Only fill needed blocks:** The form has 7 declaration blocks. Only fill 1–2 for the actual partners. Leave remaining blocks empty, otherwise the Registrar may think there are more partners.

## Related References

- `form-2-notice-of-change.md` — Form 2 (Sec 63(1)) for reconstitution/changes in constitution
- `covering-letter-deed-registration.md` — Covering letter to District Registrar (separate process)
- `reconstitution-deed-drafting-pattern.md` — Drafting the Deed of Reconstitution
- `edit-docx-in-drive.md` — Alternative .docx editing via XML manipulation (for more complex edits)
- `karnataka-partnership-registration-forms.md` — Form A / Form C registration certificates
