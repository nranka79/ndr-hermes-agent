# Team Task Delegation — WhatsApp (High-Level) + Email (Full Document Backing)

## Trigger

User says: "I need to send Vinod to check with the authorities about [project]." Or any task where a team member needs detailed instructions backed by project documents, and the user wants:
- A **concise WhatsApp** with the action items / questions only
- A **rich email** with full project details, document links, past approvals, and CCs

## Pattern

```
┌─────────────────────────────────────────────┐
│ 1. SEARCH DRIVE — all project name variants │
│ 2. CONSOLIDATE — master reference Google Doc│
│ 3. WHATSAPP — 5 clear action items, no links│
│ 4. EMAIL — full detail, every doc link, CCs │
└─────────────────────────────────────────────┘
```

## Step 1: Comprehensive Drive Search

Search across **every name variant** the project might be stored under:

- Full project name: `Ranka North Star`
- Alternate spellings: `Allalsandra`, `Allalasandra`
- Short name: `Northstar`, `North Star`
- Survey number: `Sy No 591`
- Entity name: `DRA Ranka Holdings`, `DRA Realty`

For each variant, search:
- `name contains '<variant>'` — find folders and files by name
- `fullText contains '<variant>'` — find files mentioning it in content

Also check:
- **Property Document Index sheets** — may have a structured index of all legal docs
- **Allalsandra - Extracted Document Index** — Vinod or team may have created one
- **Area Statement sheets** — for unit/FAR/floor details
- **Old Sanction Plan folders** — may be a separate subfolder

## Step 2: Create Master Reference Google Doc

Create a **single Google Doc** (under one of the project's ndr-owned folders) that consolidates:

```
Project Overview
  - Name, location, developer, architect, land area, FAR claims, road width

Previous Approvals & NOCs
  - BBMP plan sanction (LP number, date)
  - Fire NOC (date, file link)
  - Commencement Certificate
  - Tax paid receipts
  - Old sanction plans folder

Land Details
  - Survey numbers, original site details
  - Sale deeds, JDAs, addendums
  - Total land vs current sanction extent

Latest Architectural Drawings
  - Pre-DCR submission drawing (PDF + DWG links)
  - Location in approval drawings folder

All Drive Folders (consolidated list with links)

Key Documents Summary Table (document → link)

Approval Queries (full context for each question)
  - Query 1: Fire norms — height & setback issue
  - Query 2: Plan modification vs fresh sanction
  - Query 3: FAR claim
  - Query 4: Expired NOCs
  - Query 5: Land bifurcation
```

Place this Doc in a consolidated folder owned by Nishant (ndr@draas.com) so permissions aren't an issue.

## Step 3: WhatsApp Message (High-Level)

**Format:** Short, action-oriented, 5 numbered questions max. No document links. Reference that the email has full details.

**Structure:**
```
[Name], need you to visit the authorities and get clarity on [project] at [location]. 
Detailed email with all documents and reference links has been sent to you with [CCs].

Key questions for the authorities:

1. [QUESTION 1 — one line]
2. [QUESTION 2 — one line]
3. [QUESTION 3 — one line]
4. [QUESTION 4 — one line]
5. [QUESTION 5 — one line]

Email has all the details including links to [key docs].
```

**Key rule:** The WhatsApp must be **self-standing as an action list** — the recipient should know exactly what they need to do just from reading it. The email is for when they need the supporting details.

## Step 4: Email (Rich, Full Details)

**To:** The person doing the fieldwork
**Cc:** Relevant stakeholders who need visibility (Prakash Singh for legal/approvals, Bharat Hawaldar for sales)
**Subject:** `[Project], [Location] — Detailed [Task] for Authority Visit`

**Structure:**

```
URGENT & CRITICAL

[Name],

Please find below the complete details for your visit to the authorities regarding [Project].

========================================
MASTER REFERENCE DOCUMENT
========================================
I have created a comprehensive reference document consolidating all links and details:
[Google Doc link]

========================================
PROJECT OVERVIEW
========================================
- Project name, location, developer, architect
- Total land, current sanction, remaining
- FAR claim, road width, building height

========================================
DETAILS FOR EACH QUERY
========================================

---------- QUERY 1: [TOPIC] ----------
CURRENT SITUATION:
[What the situation is]
QUESTION TO AUTHORITIES:
[What to ask]
REFERENCE DOCUMENTS:
[Document description: Drive link]

---------- QUERY 2-5: (same pattern) ----------

========================================
KEY DOCUMENT LINKS (CONSOLIDATED)
========================================
[Document name]: [Drive link]

========================================
SUMMARY OF QUESTIONS
========================================
Q1—Q5 in brief.

[Signature]
```

**CC rules:**
- **Prakash Singh (psingh@draas.com)** — for any approval/legal/authority-related task
- **Bharat Hawaldar (sales1.blr@draas.com)** — for project milestones, sales coordination
- Add others based on query scope

## Common Query Types for Authority Visits (Bangalore)

These are the typical questions that come up when visiting BBMP, BDA, or fire department:

1. **Fire Norms** — New draft norms (up to 21m no Fire NOC) vs current setback requirements; ramp/split-level terrain issues
2. **Plan Modification vs Fresh Sanction** — Prior-approved plan seeking remodification; can revenue department be bypassed?
3. **FAR Claims** — Enhanced FAR (base + amalgamation benefit) under modified sanction vs new sanction
4. **Expired NOCs** — Plan sanction subject to renewal by CC stage
5. **Land Bifurcation** — Kata bifurcation timing (before or after plan sanction)

## Pitfalls

1. **Project name spelling varies** — Drive stores projects under different name variants. Search ALL of them: full name, alternate spellings, short forms, acronyms. Example: "Allalsandra" not "Alal Sandra" (user will correct this).
2. **Old sanction plans may be in a separate folder** — Not always in the main project folder. Check for dedicated "Old sanction Plan" folders.
3. **Document ownership matters** — Files owned by sales1.blr@draas.com or vkdas@draas.com may not be movable by ndr@draas.com. Create new docs in ndr-owned folders.
4. **Email as draft, not send** — Per Nishant's preference, create as Gmail draft for review unless explicitly told to send.
5. **WhatsApp must be actionable standalone** — Don't pack it with document links. The email carries the reference material.
6. **Check for existing document index sheets** — Vinod or team may have already created a structured index. Use it to save time but verify it's current.
