# Partnership Deed — Land Contribution from Partition Deed, No Schedule (DRAAS pattern)

Verified 2026-08-11 on R3N KAAJ Development Partners v3 (Byadarahalli). Recurring deal type:
a landowner partner (e.g. Ashok Kumar) contributes land sourced from a **Registered Partition
Cum Settlement Deed** executed on dissolution of a prior firm (e.g. M/s Satvik Developers,
16 Jan 2024, Doc No. SRJ-1-10373-2023-24); a corporate partner (DRA Realty) contributes by
causing the other erstwhile partner (e.g. C.R. Nagendra) to execute a registered Sale Deed in
favour of the Firm.

## Client instruction (Prakash)
"Partner 2 contributing lands from his partition cum settlement deed after dissolution of X,
contributed by executing contribution deeds in favour of this firm; WITHOUT Schedule of
properties; keep all standard clauses. Partner 1 will do as per his contribution mentioned in
this deed." → Produce a NEW deed version, original untouched, same Drive folder.

## Structure
Recitals:
- B: Partner 2 was partner of prior firm; firm dissolved; assets partitioned vide the Partition
  Cum Settlement Deed (date + Doc No.); lands (~42 acres, village/hobli/taluk) allotted to him.
  Include explicit sentence: "survey-wise particulars, extents and boundaries ... are as
  contained in the said Partition Deed and in the respective sale deeds, agreements of sale and
  general powers of attorney referred to therein, and are not reproduced in this Deed."
- C: other erstwhile partner allocated other lands (survey numbers can be listed in recital).
- D: monetary allocation deployed by Partner 2 to Partner 1 (e.g. ₹5.5 Cr) acknowledged as
  Partner 1's contribution toward structural cost / asset pooling.

Clauses:
- 2.1 Definitions: Byadarahalli Lands / Nagendra Lands / Contribution Deed / Partition Deed —
  all defined BY REFERENCE to the partition deed; never a survey schedule.
- 2.2(d) Interpretation: partition-deed reference clause (REPLACES the "all schedules attached
  form part of this deed" clause when no schedules exist).
- 4.1 Partner 2 brings lands into stock-in-trade (Sec 14 IPA 1932) and "shall execute and get
  registered one or more Contribution Deeds in favour of the Firm"; this deed = binding
  intention, the Contribution Deed perfects vesting.
- 4.2 Partner 1 guarantees/covenants to cause the third party (C.R. Nagendra) to execute a
  registered Sale Deed / absolute conveyance in favour of the Firm.
- 4.5 (NEW, explicit): "No Schedule of Properties" — parties deliberately annex no schedule;
  particulars as per Partition Deed + contribution/sale deeds, which prevail for registration,
  mutation, and capital accounting.
- 5 Capital: valuations stay (₹ per acre / lumpsum); conditions precedent incl. Sec 281 IT Act
  permission for the partner AND the dissolved firm, GST original documents return, 24-month
  legal-clearance safeguard (excluded parcels revert at partner's cost).
- Keep unchanged: P&L ratio (51/49), Brand Fee %, revenue-waterfall priorities, sole managing
  partner, joint-approval thresholds, title warranties + indemnity + adjustment, non-compete,
  succession / deed of adherence / expulsion, RERA compliance, LLP conversion, governing law +
  arbitration, signature + witness blocks. Execution date left blank.

## Doc workflow
1. Read source: `call("docs_get", doc_id=...)` — response may be dict OR JSON string; guard
   with `json.loads()`.
2. Title: `YYYYMMDD_DEED_OF_PARTNERSHIP_<FIRM>_<PROJECT>_v<N>[_NoSchedule]`.
3. Create: `call("docs_create", title=..., body=...)` — `body=`, NOT `content=`.
4. Same folder as original: `drive.files().update(fileId, addParents=<parent>,
   removeParents="root", fields="id,parents")`.
5. Verify by re-reading: assert no "SCHEDULE" string; check partition Doc No., "Contribution
   Deed", valuations, P&L ratio, "IN WITNESS WHEREOF".
6. If create response lost: `drive.files().list(q=f"name = '{title}' and trashed = false")`.
7. Deliver the doc link in a code block (Telegram breaks long URLs).
