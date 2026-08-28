# India Commercial Lease-Deed Review — lock-in, termination, eviction

Workflow for "analyze this lease agreement, what's the lock-in, when can we evict X".
Verified on the Millers Road / India Chai (SilverTip Foods) deed, 2026-08-17.

## What to extract from every commercial lease deed

1. **Parties** — identify all lessors (often 4 co-owners, sometimes via GPA holder) and the
   exact lessee entity. The operating brand (e.g. "India Chai") is usually NOT the lessee —
   the registered company (e.g. M/s SilverTip Foods Pvt Ltd) is. Name the company in any reply.
2. **Demised premises** — municipal number, built-up area, floor portion, car parks.
3. **Rent & split** — monthly rent, percentage split across co-owners, payment terms
   (advance by 10th, 18% p.a. on delay), TDS obligations.
4. **Security deposit** — amount, NEFT reference numbers, refund mechanics (simultaneous
   with vacant possession; 18% interest if refund delayed).
5. **Lock-in clause** — typically "X years from lease commencement". Lock-in expiry is the
   earliest possible eviction date. During lock-in the LESSEE who voluntarily vacates pays
   rent for the unexpired period as compensation.
6. **Termination clause** — the default/breach route: rent outstanding for N consecutive
   months OR breach of terms → written notice → cure period (e.g. 15 days) → written
   termination → possession, subject to SD refund.
7. **Re-delivery clause** — notice the lessee must give (e.g. 2 months) to vacate on expiry
   or earlier determination; condition of premises (normal wear and tear accepted).
8. **Sub-letting bar** — usually strict: no sublet/assign/parting with possession/inducting
   partners / changing use without written consent. Breach = fast termination ground.

## Answer framework: "when can we evict?"

- **Lock-in is the hard floor.** Once expired, no compensation obligation blocks eviction.
- **Breach/default route (fastest):** pay-rent-outstanding-for-N-months or sublet/use-change
  breach → notice → cure → termination. Check the arrears situation first.
- **No-fault route:** if tenancy is "month to month", serve notice under Sec 106 Transfer of
  Property Act (typically 15 days–1 month, aligned to tenancy period), then file for
  possession if not vacated. Registered long-term deeds may read month-to-month post-lock-in.
- Always quote the clause numbers (e.g. Clause 20.2, Clause 19, Clause 6) — the user's team
  acts on citations to the physical deed, not paraphrase.

## Scanned-deed OCR pitfalls

- Downloaded scans are usually **image PDFs with partial embedded text**: pymupdf
  (`import pymupdf`/fitz) gets the typed clauses but Kannada/form text garbles and some pages
  return zero text (pure scans). Page-count check: `print(len(doc))` per file.
- The lease term *length* is often the most OCR-garbled clause — do NOT invent it. If a page
  is illegible, say so and offer to re-verify visually (render page → vision) before
  concluding on term/renewal.
- Attachments download fine via `messages().attachments().get()` for typical sizes
  (<1 MB; very large scans may hit the known truncation issue — fall back to Drive search).