# Portal Complaint / Form Submission — Content Formatting

When the user asks you to draft content for an online government or regulatory portal (IRDAI Bima Bharosa, consumer forums, ombudsman, etc.):

## Critical Rules

### 1. Strip ALL email formatting
The portal textarea expects **just the body content**. Remove everything that looks like an email:
- ❌ "To," "CC:", "Subject:" lines
- ❌ "Dear Sir/Madam," salutation
- ❌ "Yours faithfully," / "Best regards," sign-off
- ❌ "Date:" and "Policyholder:" signature block
- ❌ Address blocks of the recipient

**Keep only:** the complaint narrative, numbered grievances, relief sought, declaration (minimal).

### 2. Character limit — always verify the unit
Portals nearly always limit by **characters**, not words. Ask or check:
- Bima Bharosa (IRDAI): 4,000 character limit
- If the user says "4,000 words" — confirm whether it's words or characters before writing

### 3. Forbidden characters
Common special chars blocked by portal textareas:
```
~ ! @ # $ ^ & ; " ' [ ]
```
Workarounds:
- Replace `@` with `(at)` — e.g. `ndr(at)draas.com`
- Replace `'` (apostrophes) by rephrasing — e.g. `the surveyor's report` → `the surveyor report`
- Remove `"` straight quotes entirely or use unicode alternatives
- Remove `;` — use a new line or period instead
- Remove `&` — write `and`

### 4. Build a copy-able deliverable
Since portal textareas don't have file uploads for plain text:
- Create a **standalone HTML page** with:
  - The complaint text in a `<pre>` or styled `<div>`
  - A **Copy All** button using `navigator.clipboard.writeText()`
  - A **live character counter** showing current vs limit (red when over)
  - Clean, readable styling
- Deliver via `MEDIA:<path>` so the user opens it in a browser
- Do NOT deliver as a Gmail draft — the user needs to paste into a portal

### 5. Structure for clarity within char limit
- Use numbered sections (1., 2., 3.) — saves chars over headings
- Use bold for key terms (claim number, dates)
- Be concise: IRDAI portals have strict limits; every character counts
- Put a reference summary box at the bottom with all key numbers (policy, claim, vehicle)

## When the user has attachments to upload alongside
The portal may accept file uploads. Recommend:
1. **Email thread saved as single PDF** (Gmail → Print → Save as PDF) — this one file contains all evidence
2. Only add separate files if the email chain doesn't already contain them

## Pitfalls
- The user's first instinct may be "write it like an email" — do NOT do this for portal content
- Always verify char count with `len(text)` (Python), not word count
- Forbidden chars differ per portal — ask the user if they have a list, or infer from common patterns
- HTML entities (`&amp;`, `&lt;`) will be rejected by the portal if they contain forbidden base chars — strip these too
