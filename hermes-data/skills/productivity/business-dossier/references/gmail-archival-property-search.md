# Gmail Archival Search for Property/Entity Research

Worked example from the Bin Mangala / Binnamangala Indiranagar property research (Jul 2026).

## The Challenge

A property may exist in Gmail under **multiple spelling variants** across 5-15+ years of correspondence. A single exact-match query captures only a fraction of the relevant emails.

## Name Variants Discovery

For the Bin Mangala property, the same village was spelled in emails as:
- **Binnamangala** (most common in legal docs)
- **Bin Mangala** (with a space — spoken form)
- **Binmangala** (no space, no double n)
- **Birmangala** (phonetic variant — 'r' replaces 'n')
- **Indiranagar property** (referenced by locality when name wasn't used)

**Search strategy:** Search ALL variants in parallel:
```python
queries = [
    '"Binnamangala"',
    '"Bin Mangala"',
    'Binmangala',
    'Birmangala',
    '"Indiranagar property"'
]
```

## Entity Name Variants

For the partnership entity "ARYA Developers", related searches should include:
- The exact entity name: `"Arya Developers"`
- Related legal entities: `"Arya Developers" AND (partnership OR reconstitution OR JDA)`
- The partner names: search by family surname (Ranka) + project name (Indiranagar)

## Email Date Range Strategy

For archival research spanning 10+ years:
1. **Search without date filters first** to get total count
2. **If >50 results, paginate** with `pageToken` to get all messages
3. **Fetch metadata only** (`format='metadata'` with `metadataHeaders=['From','To','Subject','Date','Cc']`) — avoids downloading large bodies for every message
4. **Sort by parsed date** after collecting all results
5. **Fetch bodies** only for the most informative emails (identified from subjects after sorting)

## Key Signals in Email Subjects

When processing a large set of historical emails for property research, watch for subject-line patterns that indicate substantive content vs routine/admin:

| Signal | Contains | Priority |
|--------|----------|----------|
| Legal opinion | "opinion", "legal", "title opinion" | HIGH |
| Agreement | "JDA", "agreement", "supplementary", "POA", "release deed" | HIGH |
| Regulatory | "NoC", "BDA", "BBMP", "approval" | HIGH |
| Partnership | "reconstitution", "partnership", "release" | HIGH |
| Financial | "tax computation", "advance tax", "sale deed" | HIGH |
| Correspondence | "letter to", "to the land owners" | HIGH |
| Discovery | "list of documents", "information" | MEDIUM |
| Routine | "bank balance", "trial balance", "bank statement" | LOW — skip unless financial data needed |
| Misc | "ITR intimation", "KYC", "re-KYC" | LOW |

**Important:** The routine financial emails (bank balances, trial balances from Manjula Rani from 2013-2015) are noise for a property timeline. Filter them out by ignoring subjects matching `"^bank"`, `"^cash & bank"`, `"^trial balance"`, `"ITR"` unless the research specifically needs financial data.

## Session User ID Verification

Before searching Gmail for a property, verify you're authenticated as the right user:

```python
gmail = build_service('gmail', 'v1')
profile = gmail.users().getProfile(userId='me').execute()
authed_user = profile.get('emailAddress')
# Confirm: ndr@draas.com for Nishant, psingh@draas.com for Prakash, etc.
```

Without this check, you may silently search the wrong person's inbox and report "no emails found."

## Data Compilation Strategy

After collecting all emails and Drive files:
1. **Build a chronological array** of all events from email dates + file modified dates
2. **Group into logical phases** (Origin → Due Diligence → Agreements → Reconstitution → Tax)
3. **Identify the key people** from To/Cc headers across the most substantive emails
4. **Cross-reference** email content with Drive documents (legal opinions in Drive were often mentioned in email threads)

## Results from the Worked Example

- Searched across **4 name variants** for the property + **1 entity name**
- Found **50+ Binnamangala emails** + **193 Arya Developers emails** (many overlapping)
- Filtered out ~140 routine bank balance emails from the 193 total
- Identified **6 Drive files** for Binnamangala + **15 Drive files** for Arya Developers
- Compiled **20+ unique timeline events** across 2004-2025
- Identified **13 key people** (partners, lawyers, accountants, landowners)
