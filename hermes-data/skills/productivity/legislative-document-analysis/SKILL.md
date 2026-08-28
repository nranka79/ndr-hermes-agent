---
name: legislative-document-analysis
description: "Analyze legal documents — legislation (bills, acts, regulations, notifications) AND court orders (judgments, interim orders, bail orders, quashing petitions) — for specific provisions, operative directions, and actionable answers. Extract targeted text from PDFs by section number, keyword, or party name. For real estate / property / criminal litigation contexts."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [legal, legislation, court-orders, bills, acts, regulations, real-estate, compliance, PDF-extraction, criminal, bail]
    related_skills: [ocr-and-documents, draas-due-diligence-pack, comprehensive-research]
---

# Legal Document Analysis

Analyze legal documents — both **legislation** (bills, acts, regulations, government notifications) and **court orders** (judgments, interim orders, bail orders, quashing petitions) — to answer targeted questions.

---

## Part A: Legislative Document Analysis

Analyze a legislative bill, Act, regulation, or government notification PDF to answer targeted questions about scope, enforcement, governance, and penalties.

### When to Use

- User sends a PDF of a legislative bill / Act and asks specific questions about its provisions
- Questions typically fall into buckets: (1) scope / exemptions — who/what is covered, (2) enforcement — how are obligations enforced, what are the penalties/remedies, (3) governance — management committees, associations, decision-making structures, (4) dispute resolution — where to go, appeals process
- User asks "does this apply to X", "what happens if someone doesn't pay", "how is the committee structured"
- User asks to find a specific provision in a regulatory document ("find the page about NOC applicability for buildings under 30,000 sqft in the Zonal Regulation")

### Workflow

#### Step 0: Locate the document

If the user says the document is "in our drive" or "on Google Drive" — **search Drive first**, don't ask for a link. Use layered queries from broad to narrow:

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3', service_name=RESOLVED_SERVICE)

# Layer 1: Name search (fast, exact filenames)
results = drive.files().list(
    q="name contains 'RMP 2015' or name contains 'Zonal Regulation'",
    pageSize=50,
    fields='files(id, name, mimeType, size, modifiedTime)'
).execute()

# Layer 2: Full-text search (slower, searches PDF content)
results = drive.files().list(
    q="fullText contains 'RMP 2015' and mimeType contains 'pdf'",
    pageSize=30
).execute()

# Layer 3: Parent folder traversal
meta = drive.files().get(fileId=KNOWN_FILE_ID, fields='parents').execute()
siblings = drive.files().list(
    q=f"'{meta['parents'][0]}' in parents and mimeType='application/pdf'",
    pageSize=50
).execute()
```

**Resolve the account first** — always call `gws_resolve_account()` with no args to get the right vault service_name before building the service. Never guess it.

**When full-text search returns too much noise**: narrow with `fullText contains 'term1' and fullText contains 'term2'` (AND is implicit for multi-word, use `and` explicitly).

**Venue tip**: the system Python (`python3`) does NOT have googleapiclient installed. Use `/opt/hermes/.venv/bin/python3` when calling from terminal, or use `execute_code` with `from hermes_tools import terminal`.

#### Step 1: Extract text from the PDF

**If the file is still on Drive**, download it first:

```python
content = drive.files().get_media(fileId=FILE_ID).execute()
with open('/tmp/document.pdf', 'wb') as f:
    f.write(content if isinstance(content, bytes) else content.encode())
```

Then extract text. Use **pdfminer** (pre-installed on Hermes sandboxes, no install needed):

```bash
python3 -c "
from pdfminer.high_level import extract_text
text = extract_text('/path/to/document.pdf')
with open('/tmp/bill_text.txt', 'w') as f:
    f.write(text)
print(f'Extracted {len(text)} chars')
"
```

If pdfminer isn't available or the PDF is scanned/OCR-needed, fall back to the `ocr-and-documents` skill (ocrmypdf + pdftotext pipeline). For text-based PDFs from court websites, **pdftotext** (poppler-utils) is often faster and cleaner than pdfminer — see Part B for the command.

#### Step 2: Identify the document structure

Scan for chapters and section headers:

```python
import re
text_clean = text.replace('\f', '\n')
chapters = re.findall(
    r'(CHAPTER\s+[A-Z]+[^\n]*)\n(.*?)(?=CHAPTER\s+[A-Z]+|$)',
    text_clean, re.DOTALL | re.IGNORECASE
)
for ch_name, ch_content in chapters:
    sections = re.findall(r'(\d+\.\s*[^\n]+)', ch_content)
    print(f"{ch_name.strip()}:")
    for s in sections:
        print(f"  {s}")
```

#### Step 3: Extract specific sections by number

```python
def extract_section(text, section_num):
    pattern = rf'({section_num}\.\s*[A-Z][^\n]*?)\n(.*?)(?=\n\d+\.\s*[A-Z]|\nCHAPTER\s+[A-Z]|\Z)'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip() + '\n' + match.group(2).strip()
    return None
```

#### Step 4: Search for specific provision types

| Question | Keywords / Patterns |
|----------|-------------------|
| **Scope — does this apply to X?** | `apply`, `exempt`, `not apply to`, `plotted development`, `villa`, `single ownership`, `apartment` definition |
| **Enforcement — what happens on non-payment?** | `default`, `recovery of common expenses`, `arrears`, `maintenance charges`, `lien`, `charge`, `penalty`, `interest`, `restrict`, `withhold` |
| **Governance — management structure** | `association`, `executive committee`, `election`, `term`, `bye-laws`, `formation`, `duties`, `powers` |
| **Dispute resolution** | `competent authority`, `appellate`, `dispute`, `bar of jurisdiction`, `appeal` |
| **Penalties** | `penalty`, `contravention`, `fine`, `rectification`, `restoration` |

#### Step 5: Read the relevant section in full

Key things to look for:
- **Scope clauses** (section 1 usually has application and exemptions)
- **"Provided that" clauses** — exceptions to exceptions; the last proviso often contains the most important carve-out
- **Definitions** (section 2) — check how key terms are defined
- **Transitional provisions** — what happens to existing arrangements

#### Step 6: Structure the answer

Organize by the user's actual questions, not the document's structure. Lead with the direct answer (yes/no/applies/doesn't apply), then cite the specific section and provide context.

#### Step 7: File the document after analysis

For **ndr@draas.com** specifically:

- **Regulatory/legislative documents** (bills, acts, notifications, zoning regulations, building bye-laws, planning norms) → **RnD > Bangalore** (NOT TMP)
- **Court orders in pending matters** → existing matter-specific folders (e.g. `WHPL FIR Madras HC Court Orders`). File as named PDFs with case number and date in the filename.
- **General work-in-progress** → TMP folder
- **Compliance notices** → DRA Group/<Entity>/<Type>/ per `dra-compliance-filing.md`

---

## Part B: Court Order Analysis

Court orders (judgments, interim orders, bail orders, quashing petition orders) have a fundamentally different structure from legislation. They are about **specific parties and facts**, not abstract provisions. The user's questions are about **what the court directed**, not what the law generally says.

### When to Use

- User asks about a court order in a pending legal matter — "what does this order say about the FIR?", "can they arrest me?", "can the police file a charge sheet?"
- User references an advocate (e.g. "Solomon", "Solomon Francis") who filed the case
- User mentions specific case types: anticipatory bail, quashing petition (Crl OP), caution petition, FIR
- User has case numbers or dates but not the orders themselves
- User asks about a criminal matter involving FIR, B report, charge sheet, or investigation status

### Locating Court Orders

**Rule: Search Drive FIRST, not the web.**

When the user asks about court orders in their own legal matter:
1. **Search Drive** — the user files their own court orders in organized folders. Use:
   ```python
   drive.files().list(q="name contains 'FIR' or name contains 'CRL' or name contains 'anticipatory bail' or name contains 'quashing' or name contains 'Westbury' or name contains 'Madras HC'", pageSize=30).execute()
   ```
2. **Search by folder** — look for folders named like `WHPL FIR Madras HC Court Orders`, `[Legal]`, or matter-specific names.
3. **Only search the web** (Indian Kanoon, casemine, court websites) if the user says the document is NOT on their Drive or asks you to find it online. The user will explicitly say "find it online" if they want web search — otherwise, always check Drive first.

### Extracting Text from Court Orders

Court orders from Indian High Courts are typically text-based PDFs (not scanned). **pdftotext** (from poppler-utils) is the fastest extraction method — it's pre-installed on most Linux systems:

```bash
pdftotext /path/to/order.pdf /path/to/output.txt
cat /path/to/output.txt
```

If the text layout is messy, try the `-layout` flag:
```bash
pdftotext -layout /path/to/order.pdf /tmp/output.txt
```

If pdftotext returns empty or garbled, the PDF may be scanned/OCR-needed — fall back to the `ocr-and-documents` skill.

### Identifying Key Parts of a Court Order

Indian High Court orders follow a standard structure. Extract these fields:

| Field | What to look for | Example |
|-------|-----------------|---------|
| **Court** | Header | "IN THE HIGH COURT OF JUDICATURE AT MADRAS" |
| **Case number** | CRL OP / WP / Crl A / CMP + number + year | "Crl.O.P.No.34426 of 2025" |
| **Judge** | "CORAM" / "THE HONOURABLE" | "THE HONOURABLE Mr. JUSTICE K. RAJASEKAR" |
| **Date** | "DATED :" line | "DATED : 18.12.2025" |
| **Petitioner(s)** | First party | "Nishant Ranka ... Petitioner" |
| **Respondent(s)** | Opposite party | "State by Inspector of Police, Bagalur Police Station" |
| **Nature of petition** | PRAYER section | "filed under Section 482 of BNSS to enlarge the petitioner on anticipatory bail" |
| **Operative direction** | The ORDER section. This is what matters most — what the court actually directs. | "the respondent police is directed not to arrest the petitioner" / "the investigation shall go on but the final report shall not be filed" |
| **Conditions imposed** | Bail conditions, deposit amounts, reporting requirements | "deposit Rs.7,500/-", "execute a bond for Rs.15,000/-", "report before the respondent police everyday at 10.30 a.m. for three weeks" |

### Analyzing Court Order Directions — Common Patterns

Once you've identified the operative direction, the user's questions typically fall into predictable categories:

#### 1. Anticipatory Bail Orders (Section 438 BNSS / 482 BNSS)

**Key questions:**
- **Can the police arrest the person?** Look for "not to arrest the petitioner" (interim) or bail granted with conditions (final).
- **Can the police investigate?** Anticipatory bail only protects from arrest — it does NOT stay the investigation. Unless the order explicitly says otherwise, investigation can continue.
- **Can the police file a charge sheet?** Anticipatory bail alone does NOT bar filing of final report/charge sheet. The only restriction is on arrest.
- **What are the conditions?** Look for: bond amount, surety, reporting to police, travel restrictions, no evidence tampering.

#### 2. Quashing Petition Orders (Section 528 BNSS / 482 CrPC)

**Key questions:**
- **Is the FIR quashed?** Look for "FIR quashed" (disposed) vs "notice to respondent" (pending, interim stage).
- **What is the interim direction?** Most quashing petitions at notice stage get an interim order. The most common is: *"investigation shall go on but the final report shall not be filed"*.
- **Does "final report" include a B report (closure report)?** Yes — in Indian criminal procedure, "final report" is the umbrella term for both the charge sheet (police find prima facie case) AND the B/closure report (police find no case). Both are "final reports" under Section 173 CrPC / corresponding BNSS provision. If the order bars filing of final report, it bars BOTH.
- **Can the police close the case voluntarily?** No — if the court has restrained filing of final report, the police cannot unilaterally close it by filing a B report either. They must wait for the quashing petition to be decided.
- **What happens if the quashing petition is withdrawn?** The interim direction is ancillary to the petition. Withdrawing the petition makes the interim direction fall away automatically — the police can then file their final report (charge sheet or B report).

#### 3. Interim Orders — Restraint on Filing Final Report

This pattern is common in Madras/Karnataka High Court quashing petitions:

> *"Post the matter after four weeks. In the meanwhile, the investigation shall go on but the final report shall not be filed."*

**What this means:**
- ✅ Investigation CAN continue (collect evidence, record statements, call accused for interrogation)
- ❌ Police CANNOT file a charge sheet (final report alleging guilt)
- ❌ Police CANNOT file a B report / closure report (final report finding no case)
- The police are in a holding pattern — they can work the case but can't conclude it
- This remains in force until the quashing petition is disposed

**If the user asks about withdrawing the quashing petition to allow a B report:**
- The interim restraint is ancillary — it falls when the petition is withdrawn
- The police can then file the B report
- ⚠️ But the complainant can file a protest petition before the Magistrate, which could reopen the case
- ⚠️ Withdrawal means losing the chance to get the FIR quashed entirely
- ⚠️ Only withdraw if (a) the B report is genuinely ready, and (b) the complainant has no strong basis for a protest petition
- "Withdraw with liberty to file afresh" is a common formulation — Solomon would know the Madras HC's recent stance on this

### Presenting the Answer for Court Orders

Structure your response like this:

```
## [Order Type] — Crl OP XXXXX/YYYY (Court Name, Date)

**[Specific direction identified:]** One-line summary.

**Your Questions Answered:**

| Question | Answer |
|----------|--------|
| Can police arrest? | Yes/No — [cite specific direction from order] |
| Can police file charge sheet? | Yes/No — [cite specific direction from order] |
| Can police file B report? | Yes/No — [explain why, reference "final report" definition] |
| What powers do police have? | [list what they can/can't do] |
| Which order deals with status quo? | [identify which order and paragraph] |

**Recommendation (if user asks):** [practical next steps — consult advocate, timing considerations, risks]
```

Use a markdown table for the Q&A section (concise, scannable).

### Pitfalls — Court Orders

- **"Final report" in criminal procedure includes BOTH charge sheet and B/closure report.** This is Section 173 CrPC / corresponding BNSS provision terminology. When an order says "final report shall not be filed", it bars both. Do NOT assume it only means charge sheet.
- **Anticipatory bail ≠ stay on investigation.** Many users conflate the two. Anticipatory bail only protects from arrest. The investigation continues unless separately stayed.
- **Multiple orders in the same case number.** A single CRL OP often has multiple dates — first an interim order (adjournment + protection from arrest), then a final order (bail granted/refused). Read both, as the user usually needs to understand the sequence.
- **Related petition numbers.** A single FIR often spawns multiple petitions: Crl OP X for anticipatory bail (Nishant), Crl OP Y for quashing (Nishant). The CRL OP 3754 from this session was an unrelated petitioner's case filed in the same batch — check the party name, not just the folder name. Always verify the party name in the order matches the user.
- **Court clerk markings.** Indian court PDFs often have handwritten page numbers, stamps ("True Copy"), or the judge's initials ("Vv", "drl", "VKR") at the bottom. These are not part of the order content.
- **Advocate names as clues.** The advocate representing the user (e.g. "Mr. P. Solomon Francis for Petitioner") tells you which filed document belongs to which party. Use this to distinguish the user's documents from co-petitioners'.
- **Delay in FIR registration** (complaint after 7 months in this session) is a common argument in both anticipatory bail and quashing petitions. The court considers delay as a factor favouring the accused.

---

## Part C: Advocate Consultation

After analyzing court orders, the user frequently asks you to draft a WhatsApp message to their advocate (e.g., Solomon Francis) with informed questions grounded in the orders.

### When to consult the advocate

- User says "message Solomon about this case", "ask the advocate", "consult about the court order"
- After you've analyzed orders and the user wants next-step guidance from their lawyer

### Workflow

#### Step 1 — Find the advocate in the order

Advocate names appear in the order header, typically:
> "Mr. P. Solomon Francis for Petitioner"

Use this exact name when searching Google Contacts for the advocate's phone number (see `personal-messaging` skill). The WhatsApp link tool requires the phone number; never hand-encode a wa.me URL.

#### Step 2 — Compose informed questions

Base the questions on what the orders *actually say*, not on general legal knowledge. Structure:

1. **Identify the matter** — case number, court, nature of petition (quashing / anticipatory bail)
2. **State what the interim order says** — quote the operative portion verbatim
3. **Ask specific questions** — yes/no or structured:

Common question patterns:
- "Does 'final report' include a B report?" (clarify scope)
- "If we withdraw the quashing petition, does the restraint on filing final report fall away?"
- "Should we withdraw with liberty to file afresh?"
- "Can we request the police to file B report now, or wait for the quashing petition to be disposed?"
- "What do you suggest as the best course?"

#### Step 3 — Message structure

```
[Case identification]: Crl OP 3753/2026 (Madras HC) — Quashing Petition

[Current status]: Interim order says "investigation shall go on but the final report shall not be filed"

[Questions]:
1. Does "final report" in this context include the B report (closure report)?
2. If the police are ready to file a B report, should we withdraw the quashing petition so the restraint falls away and they can file it?
3. If we withdraw, can we do so with liberty to file afresh?
4. What do you suggest?
```

Keep it concise — the advocate knows the matter.

#### Step 4 — Send via WhatsApp link

Use the `whatsapp_link` tool (from `personal-messaging` skill) to generate a wa.me link with the message pre-filled. Never hand-encode the URL. The user taps the link and sends it themselves.

### Key legal concepts for advocate consultation

These are the concepts non-lawyer users most often misunderstand. Explain them clearly in your analysis AND in the message to the advocate:

- **Final Report is an umbrella term** covering both the charge sheet (police find evidence) AND the B/closure report (police find no case). Section 173 CrPC / corresponding BNSS provision. When an order says "final report shall not be filed," it bars BOTH.
- **Protest Petition**: If police file a B report, the complainant (victim) can file objections. The Magistrate can accept the B report or treat the protest as a private complaint — potentially reopening the case.
- **Withdrawal of quashing petition**: If the quashing petition is withdrawn, the interim directions ancillary to it (including bar on filing final report) automatically fall away. The FIR survives unless quashed. Withdrawal means losing the chance to get the FIR quashed entirely.
- **Caution Petition vs Quashing Petition**: Users may use "caution petition" interchangeably with "quashing petition." In Indian practice, a caution petition is filed to caution the court about pending proceedings; but the user may intend the quashing petition. Check the actual filing type from the order, not the user's terminology.

### Reference files

- `references/westbury-fir-analysis.md` — Full worked example of the Westbury FIR matter: orders found, analysis framework, WhatsApp draft to advocate. Use as a template for similar criminal-matter analysis+consultation tasks.
