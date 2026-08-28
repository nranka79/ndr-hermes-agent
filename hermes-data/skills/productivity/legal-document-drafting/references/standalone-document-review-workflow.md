# Standalone Document Review Workflow

**Use when:** User asks for a review of an existing legal document without referencing an email trail or counterparty draft — they want typos, internal consistency, naming, dates, and formatting checked, then a categorized plan of edits for sign-off.

**Don't confuse with:** `lease-draft-review-email-negotiation-trail.md` — that's a gap analysis comparing a draft against email-agreed terms. This workflow is purely self-review of a single document, where the email-terms incorporation has already happened.

## 1. Get the Document Structure (Don't Rely on Flattened Text)

The `gws_skill_bridge.docs_get` and `gws_skill_bridge.docs_create` ops flatten the body to a single concatenated string — they lose all `startIndex`/`endIndex`/`textStyle` (color, font, bold) and paragraph-style info.

For any review that needs to find colored text, bold runs, heading styles, or paragraph boundaries for editing, **bypass the bridge and use `tools.gws_auth.build_service` directly**:

```python
import os
os.environ['HERMES_SESSION_USER_ID'] = str(telegram_id)
from tools.gws_auth import build_service
docs = build_service('docs', 'v1', service_name='google-draas')
doc = docs.documents().get(documentId=DOC_ID).execute()
```

The full structure is in `doc['body']['content']` — a list of structural blocks (`paragraph`, `table`, `sectionBreak`). Each `paragraph` has `elements[].textRun.textStyle.foregroundColor` and `paragraphStyle.namedStyleType` for full formatting metadata.

The `google-workspace` skill's troubleshooting table documents this exact pitfall — see "docs_get returns body as a single concatenated text string".

## 2. Extract Paragraphs with Index + Style

```python
def extract_paragraphs(doc):
    out = []
    for i, block in enumerate(doc.get('body', {}).get('content', [])):
        if 'paragraph' in block:
            para = block['paragraph']
            style = para.get('paragraphStyle', {}).get('namedStyleType', 'NORMAL_TEXT')
            text = ''.join(e.get('textRun', {}).get('content', '') for e in para.get('elements', []) if 'textRun' in e)
            out.append({'idx': i, 'style': style, 'text': text.rstrip()})
    return out
```

Keep the index — you'll cite it when listing findings to the user (e.g., "Para 53 typo: ground flow").

## 3. Scan for Typos with Regex (Don't Rely on LLM Spot-Checking)

LLMs are good at semantic checks but bad at catching character-level typos like "RENT-FR EE" (extra space), "ground flow" (typo of "Ground Floor"), "in by" (repeated word). Use regex passes:

- **Names** — extract all mentions of each co-owner/party name and verify consistency across the document and any prior emails/counterparty drafts
  ```python
  import re
  for m in re.finditer(r'.{30}Asma.{30}', full_text): print(m.group(0))
  for m in re.finditer(r'.{30}Banu.{30}', full_text): print(m.group(0))
  ```
  If the same person appears as "Asma Hussain" in the body but "Asma Banu" in a separate document (like an email or counterparty's draft), that's a mismatch to flag.

- **Dates** — extract every date and check for inconsistencies:
  - 31st January 2028 vs 1st February 2028 (one is the existing-tenant lease expiry, the other is the actual handover date)
  - 12 June vs 12th June vs 12/06/2026 (format inconsistency)

- **Currency** — `Rs. ` (19x) vs `INR ` (0x) vs `₹` (0x) — pick one and flag drift

- **Apostrophes** — straight `'` (23x) vs curly `'` (0x) — flag drift

- **Dashes** — `-` (102x), `–` (en-dash, 5x), `—` (em-dash, 9x) — flag inconsistent use in same context (e.g., all in dates should be en-dash, all in parenthetical asides should be em-dash)

- **Square feet notation** — `sq.ft` (4x) vs `sq. ft` (0x) vs `square feet` (3x) — pick one

- **Section references** — "Clause 4(d)", "Clause 4(g)" — verify all internal cross-references exist (sometimes a clause number changes during editing and old references get orphaned)

- **"i.e." vs "i.e"** — `i.e.` (7x) vs `i.e ` (0x) — verify consistency

## 4. Check Heading Styles (Common Finding)

Most Google Docs created by hand or imported from .docx have **no `HEADING_1` or `HEADING_2` styles applied** — section titles like "1. OFFER AND ACCEPTANCE", "8. USE OF LEASED PREMISES" are all `NORMAL_TEXT`. This breaks TOC generation and reduces professional appearance.

To detect:
```python
for p in paragraphs:
    if p['style'] != 'NORMAL_TEXT':
        print(f"  Heading found: {p['idx']} [{p['style']}] {p['text'][:80]}")
# If empty list of "look-like headings" is also empty, no headings at all
```

To find paragraphs that LOOK like headings (all-caps, no punctuation) but are `NORMAL_TEXT`:
```python
for p in paragraphs:
    text = p['text'].strip()
    if (text and text.isupper() and 3 < len(text) < 100
        and not any(c in text for c in '.,:;()')
        and p['style'] == 'NORMAL_TEXT'):
        print(f"  Should be a heading: [{p['idx']}] {text[:80]}")
```

## 5. Check Internal Date/Number Consistency

Common bugs from prior editing rounds:
- Schedule-A says "January 2028" but Clause 5.1 says "31st January 2028" but Clause 4(c) references "1st February 2028" — three dates for the same event
- Clause 4(b) says "Rs. 4,00,000/-" but Clause 6.1 says "Rs. 12,00,000/- (i.e. 3 months' rent)" — verify the math: 4L × 3 = 12L ✓, but if the rent changed in a later round, the deposit total may be stale
- Total deposit stated as "Rs. 30,00,000/-" but per-tranche math: 12L + 12L + 6L = 30L ✓ — but verify against the 6.2A apportionment examples
- Renewal escalation clause: 20% discount to market is a verbal agreement but the formula should be specified (does the IPCs' determination get the discount applied to it, or is the IPC instructed to determine the post-discount rate directly?)

## 6. Categorize Findings — CRITICAL / LOGICAL / FORMATTING

Present the findings in 3 tiers to the user. Don't blend them — the user needs to make different decisions at each tier:

- **🔴 CRITICAL** — Typos that change meaning or are visible in the document body ("ground flow", "in by", "RENT-FR EE", name/date mismatches, math that doesn't add up). These are no-brainer fixes.
- **🟡 LOGICAL / CONSISTENCY** — Things that aren't typos but are commercial/legal decisions (e.g., tenant lock-in penalty is harsh, sub-letting restriction on banking could bite group companies, GF delay clause caps rent forever with no termination right). These need user judgment, often with their legal team.
- **🟢 FORMATTING / STRUCTURE** — No `HEADING_2` styles applied, apostrophe consistency, sq.ft notation, section numbering jumps. Cosmetic, no commercial impact.

Then in the proposed-actions section, list:
- **Safe fixes** (the Critical tier) — "Reply 'go ahead' to apply all safe fixes"
- **Needs decision** (the Logical tier) — "Let me know your decision on items X, Y, Z"
- **Cosmetic batch** (the Formatting tier) — "Apply Heading styles + apostrophe standardization + sq.ft standardization — confirm?"

This lets the user approve in one message and you proceed without 5 rounds of "ok, now do the formatting one" back-and-forth.

## 7. Wait for Explicit Sign-Off

**Hard rule:** Do NOT touch the document until the user explicitly approves the plan. Their workflow is review → approve plan → apply. If you start editing while still waiting for sign-off, you waste their time and may make changes they didn't want.

When the user replies, parse their response carefully:
- "go ahead" / "apply" / "yes" → apply the **safe fixes** they specified
- "items 5, 7, 9 keep as is" / "X should stay" → don't touch those specific items
- "also change Y" → fold the additional change into the apply step
- "wait, let me check Z" → hold, do nothing, ask for their decision on Z

## 8. Apply Edits — Use batchUpdate, Not Find-and-Replace

For paragraph-style fixes (apply `HEADING_2` to all section titles), use `Docs API batchUpdate` with `updateParagraphStyle` requests, not find-and-replace. Find-and-replace changes text content, not styles.

For text content fixes (typos like "RENT-FR EE" → "RENT-FREE"), `replaceAllText` is fine and the cleanest.

For colored text → black conversion, walk the document, collect all `textRun` elements with `foregroundColor`, then build a list of `updateTextStyle` requests with `foregroundColor: {color: {rgbColor: {red: 0, green: 0, blue: 0}}}`. Process runs in **reverse index order** so startIndex/endIndex don't shift.

## Pitfalls

- **LLM-only review misses character-level typos.** "RENT-FR EE" and "in by their" will sail past semantic checks. Always run regex passes for known typo patterns.
- **Don't apply changes before sign-off.** The user wants to see the plan first. Even one edit before approval breaks the trust model.
- **Don't mix "safe" and "decision" findings in one batch.** If you lump them together, the user can't approve "all the typos" without also implicitly approving the commercial changes they wanted to think about.
- **The doc's lastModifiedTime may not reflect the user's manual edits.** If they say "I just changed X" but the doc was modified 12 hours ago, the user may have edited in a stale tab. Re-fetch immediately before applying.
- **Bridge vs direct API.** `gws_skill_bridge.docs_get` flattens text — you lose formatting info. For review work, use `gws_auth.build_service` directly. (Same pitfall documented in the `google-workspace` skill's troubleshooting table.)
- **Nishant's color conversion was manual, not via the script.** When the user says "I've changed all the colored text to black manually", the API fetch will confirm no remaining colored runs — but still re-fetch immediately before doing your own edits, since the in-memory cached version may be stale.

## Verified Against

- Millers Road Lease Deed v4 (12 Jul 2026) — user manual edit round: 4 critical typos, 5 logical issues, 6 formatting improvements
- The gap-analysis pattern in `lease-draft-review-email-negotiation-trail.md` is a related but distinct workflow — that one compares against email-agreed terms; this one is purely self-review
- The Ranka Iris sale-deed clause review (BLOCKER / HIGH / MEDIUM severity map, see `ranka-iris-sale-deed-clause-review-patterns.md`) is a similar categorization pattern for sale deeds
