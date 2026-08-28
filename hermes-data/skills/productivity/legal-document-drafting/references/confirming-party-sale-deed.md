# Confirming Party Absolute Sale Deed (Karnataka / Byadarahalli pattern)

Use when the acquisition chain for a survey number involves a prior Agreement
to Sell + GPA held by a third party who is NOT the direct vendor. Two
structural variants exist.

## Variant A: Confirming Party IS the Vendor (via Partition Deed)

The confirming party owns the property (allocated via Partition Deed from a
dissolved firm that originally held the Agreement/GPA) and sells directly:

1. Original owners → Agreement to Sell + irrevocable GPA to a partnership firm
2. Firm dissolved → Partition Cum Settlement Deed allocates rights to one partner
3. That partner (confirming party) now sells to the new purchaser as Vendor

**Party structure:**
- **FIRST PART — Vendors**: The partner as individual owner (through a GPA from
  the original owners, re-vested via Partition Deed)
- **SECOND PART — Confirming Party**: Same person (signed TWICE — once as
  attorney for original owners, once in personal capacity)
- **THIRD PART — Purchaser**: The new buyer

**Operative clause wording:** "acting for himself and as Attorney for and on
behalf of the Vendors" — the confirming party conveys both capacities: as
Vendor through the GPA, and as confirming his own right to sell.

**Consideration:** Single flow — purchaser pays the confirming party. No
settlement with original owners needed; they are merely represented.

## Variant B: Direct Sale by Original Owners with Confirming Party Consent

The original title holders (vendors) sell DIRECTLY to the new purchaser. The
confirming party holds the Agreement to Sell and GPA but **consents** to the
direct sale and extinguishes his rights rather than exercising them:

1. Original owners → Agreement to Sell + irrevocable GPA to the confirming party
2. Confirming party may have had the rights allocated via Partition Deed from
   a dissolved firm
3. **Instead of the confirming party buying then selling**, the vendors sell
   directly to the new purchaser
4. Confirming party's GPA is used to represent the vendors at registration,
   AND he signs in personal capacity to confirm consent

**Party structure:**
- **FIRST PART — Vendors**: The original title holders (signed through their
  constituted attorney — the confirming party — under the GPA)
- **SECOND PART — Confirming Party**: signs in personal capacity to confirm
  consent and that his rights under the Agreement/GPA are fully satisfied
- **THIRD PART — Purchaser**: The new buyer

**Recital sequence for Variant B (lettered WHEREAS clauses):**

```
A. TITLE OF VENDORS — Original owner → succession/legal heirship → current khatedars
B. PRIOR AGREEMENT (if any) — Cancelled agreement details
C. AGREEMENT TO SELL IN FAVOUR OF CONFIRMING PARTY — Vendors → Confirming Party (amount, advance, DD details, reg no, date)
D. GENERAL POWER OF ATTORNEY — Vendors → Satvik Developers / Confirming Party (reg no, irrevocable, coupled with interest)
E. PARTITION DEED (if applicable) — Dissolution of firm, allocation of Agreement/GPA benefit to Confirming Party
F. CONFIRMATION BY CONFIRMING PARTY — Confirming party consents to direct sale, confirms his advance is refunded/settled, rights extinguished
G. AGREEMENT FOR SALE TO PURCHASER — Vendors agree to sell, Purchaser agrees to buy
H. RECEIPT OF CONSIDERATION — Acknowledged
I. POSSESSION — Delivered
```

**Consideration settlement mechanics in Variant B:**

The confirming party's advance under the original Agreement to Sell (e.g.
₹1,00,00,000 out of ₹1,62,00,000) must be addressed. Two patterns:

| Pattern | Wording in Recital F | When to Use |
|---------|---------------------|-------------|
| **Refund** | "...has been duly refunded/settled to his satisfaction and he has no further claim against the Vendors or the Schedule Property in respect thereof" | Confirming party gets his money back (from vendors or purchaser separately) |
| **Adjustment** | "...has been adjusted towards the sale consideration payable by the Purchaser and the Confirming Party confirms that the same stands fully satisfied" | The advance is treated as part of the purchaser's payment to the confirming party |

Default: use **Refund** wording unless the user explicitly says the advance is
being adjusted. The operative clause should make clear the vendors receive
the full consideration from the purchaser, and the confirming party's claim
against the vendors is independently settled.

## Choosing Between Variants

| Factor | Variant A (CP IS Vendor) | Variant B (Direct Sale) |
|--------|-------------------------|------------------------|
| Who holds title | Confirming Party (via Partition Deed) | Original Owners |
| Who gets paid | Confirming Party | Original Owners |
| CP's GPA role | Sign as attorney for original owners | Sign as attorney for original owners AND as confirming party |
| CP's personal role | Signs as Vendor | Signs to consent/confirm |
| Best for | CP has clear ownership via Partition | CP only has Agreement + GPA, title still with original owners |

## Source documents needed (fetch first)

- The Agreement to Sell (register no, CD no, SRO, date, consideration,
  advance paid, payment mode/cheque details)
- The General Power of Attorney (register no, irrevocable + coupled with
  interest wording, powers list)
- The Partition Cum Settlement Deed (register no, date, which Schedule/Item
  allocated the property to the confirming party)
- Any prior agreement that was cancelled (Cancellation Deed) — the prior
  buyer signs as "Consenting Witness" in the new agreement
- Title flow from the agreement itself: original owner → partition among
  sons → phodi → new survey no assignment → death intestate → khata to legal
  heirs (MR numbers)
- Death certificate and legal heirship documents for deceased khatedars

## Fetching Drive PDFs (web_extract fails on Drive links)

Use the Drive API directly, not web_extract. Kannada + English mixed PDFs may
render garbled text via pymupdf `get_text()` — capture key recitals from
English phrases (document numbers, amounts, party names, survey numbers).
For complete verbatim text, use `vision_analyze` on converted page images.

```python
from tools.gws_auth import build_service
service = build_service('drive', 'v3', service_name='google-draas')
meta = service.files().get(fileId=fid, fields="name, mimeType").execute()
data = service.files().get_media(fileId=fid).execute()  # bytes; write to file
```

Then extract text with pymupdf (`import fitz`; page.get_text()) — the
KAVERI/registration-department sheets (Kannada watermarks) still carry clean
English body text in the PDF text layer.

## Recital Structure (Variant A — CP as Vendor)

Use lettered WHEREAS clauses:

```
A. [Title chain for Item 1] — Chain from original grant/proprietor → ... → firm's acquisition
B. [Title chain for Item 2] — Separate chain if different source deed
C. [Partition Deed] — Firm dissolution + allocation to VENDOR
D. [Agreement to Sell] — Consideration, encumbrances, capacity
```

## Pitfalls

- **Spreadsheet doc registers can be WRONG about party names.** The
  Byadarahalli legal docs sheet listed 190/3 vendors as "A. Padma; Ashwini M;
  ... (heirs of Late V.C. Narayanaswamy)" but the actual Agreement PDF names
  Kempamma, Ashwathamma, Durgesha. N, Gowthami. K, Venkatalakshmamma (heirs
  of Late Nanjappa). ALWAYS trust the extracted PDF text over the summary
  spreadsheet. Flag the discrepancy to the user rather than silently
  copying the sheet.
- Never fabricate document numbers, MR numbers, or khata references — every
  recital must come from a source document.
- The confirming party signs TWICE in the testimonium: once as
  "For and on behalf of the VENDORS (Constituted Attorney under GPA
  DNH-...)" and once as "CONFIRMING PARTY" in personal capacity.
- In Variant B, the confirming party signs THREE sections: (1) as Constituted
  Attorney for Vendors, (2) as Confirming Party in personal capacity.
  The testimonium block should have separate signature lines for each role.
- Operative clauses (grant, receipt) must be worded to address both
  capacities. In Variant A: "acting for himself and as Attorney for and on
  behalf of the Vendors". In Variant B: the Vendors convey through their
  Attorney, and the Confirming Party confirms separately in a covenant clause.
- Include the ₹-contribution recital: if a different erstwhile partner of the
  dissolved firm (e.g. Ashok Kumar) paid the original purchase consideration
  (e.g. ₹5.5 Cr), record it in a recital and note it was settled in the
  Partition Deed — do NOT put that partner on the deed as a party.
- Keep the exact KAVERI format of the source deeds: Parties → property intro
  → FLOW OF TITLE (one WHEREAS per link in the chain) → Partition Deed
  recital → AND WHEREAS (authority, intent, consideration) → NOW THIS
  INDENTURE WITNESSETH (2 clauses: sale + receipt) → 13 vendor covenants →
  Schedule with 4 boundaries → Testimonium → witnesses → signatures.
- Agreement to Sell PDFs from KAVERI (Karnataka registration system) are
  bilingual Kannada+English with Kannada watermarks across every page. The
  English text layer often carries only document metadata (reg no, CD, stamp
  duty, challan details), not the full recitals. Key English phrases to look
  for: "Document No.", "C.D. No.", "Rs.", party names in Roman script, survey
  numbers, date stamps. Cross-reference with vision_analyze on the Kannada
  body text where visible.
- The Flow of Title section is a separate standalone section (not part of the
  recitals) that summarises the full chain: original owner → mutation →
  Agreement → GPA → Partition Deed → current sale. It must number each step
  and cite document references. Users (especially Prakash) expect this section
  for verification.

## Deliverable

Upload the draft as a Google Doc (markdown import via Drive API,
`mimeType='application/vnd.google-apps.document'`) to the project's
partnership folder (e.g. "DRA KAAJ Development Partners"). Leave blanks
([●]) for: sale consideration amount, payment mode, execution date,
witness names/addresses, drafting advocate.

When the user confirms the structure is Variant A but you previously drafted
Variant B (or vice versa), update the existing Drive doc rather than creating
a new one — ask first whether to replace or add as a separate version.
