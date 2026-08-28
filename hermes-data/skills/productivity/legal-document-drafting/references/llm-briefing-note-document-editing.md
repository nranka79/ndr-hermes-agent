# LLM Briefing Note for Document Editing

**Pattern:** When the user wants to hand off a document editing task to another LLM (e.g., "give me a briefing note I can give another LLM to examine the lease deed and make all corrections"), create a structured `.md` briefing note that another LLM can consume independently.

## Structure of a Briefing Note

```
# Briefing Note — [Document Name]

## 1. Parties
Complete entity-level data for all parties (verified from official sources):
- Names, PAN, CIN, GST, Aadhaar, registered addresses, DOB, father's name
- Include verification source for each: "from PAN card", "from ITR", "from Aadhaar"

## 2. Property / Subject Matter Description
Description of the property or subject of the document.

## 3. Agreed Terms
Key agreed terms in table format. Capture all values, never "TBD" or "as discussed".

## 4. Corrections to Make
Table with three columns:
| Field | Current (Wrong) | Correct |

Cover ALL corrections:
- Entity name corrections
- PAN/Aadhaar/CIN/GST
- Person name / father's name
- Structural issues (parties reversed, wrong lease term, missing clauses)

## 5. Document Access — LIVE LINKS
**CRITICAL section** — this is how the receiving LLM finds and edits the document.

### PRIMARY: The Document to Edit
> **Open and edit directly:** [link to Google Doc]
>
> Description of what's in it (e.g., "Latest version with all corrections marked in purple")

### Other Files (Reference Only)
Table of reference documents with links and notes about each.

## 6. Email History Summary
Chronological table of key emails:
| # | Date | From | Summary |

Include enough context so the receiving LLM understands the negotiation arc without reading the raw emails.

## 7. Current Status
| Item | Status |
|------|--------|
| Commercial terms | Agreed / In progress |
| Corrections | Status |
| Review blockers | What's pending |

## 8. Other Open Items
List of other clauses or issues the receiving LLM should address that weren't covered in the main corrections table.

## Formatting Rules
- Use markdown tables for structured data
- Use bold for emphasis
- Use `> blockquote` for the primary document link (makes it visually prominent)
- Keep file size under 50KB (aim for ~10-15KB)
- No inline CSS or HTML — plain markdown only
