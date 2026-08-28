# MOU Party & Schedule Restructure (Dev-Cum-Sale / Land Aggregation)

When the user asks to remove parties, re-allocate schedules, and record
in-progress land transfers in an existing MOU (e.g. the Doddasane farm-plot
Dev-Cum-Sale MOU), use this workflow. It is the "restructure" sibling of
`editing-existing-mou-documents.md` (single-clause edits) — this one changes
the deal's party/schedule backbone.

## 1. Resolve ambiguous party-removal instructions BEFORE editing

Users often dictate party lists loosely. Example from a real session:
"remove first party 1,3,4 and second party 3" — but the follow-on explanation
made clear First Party No. 1 STAYS (he is the landowner of Sy 68/1 and is
buying 68/2); the actual removals were First Party No. 3 & No. 4 and Second
Party No. 3.

- Read the WHOLE instruction before touching the doc; the explanation usually
  disambiguates the list.
- If a party is described with an ongoing role (landowner, buyer, transferor),
  they stay.
- **Flag the interpretation in your final summary** ("you said 1,3,4 — I read
  that as 3&4 only since FP1 stays as the 68/1 owner; say the word if you
  meant otherwise"). Do NOT silently pick.

## 2. Touch ALL of these when removing a party (miss one = broken doc)

1. **Party definition block** — delete the numbered paragraph.
2. **Collective definition** — rewrite the "All the above First Party No. X,
   No. Y ... shall hereinafter be collectively referred to" paragraph to list
   only remaining parties.
3. **Schedule headers** — reassign ownership labels, e.g.
   `(Survey No. 28/P120 - Land belonging to FIRST PARTY NO. 2)`.
4. **Signature / witness block** — delete the removed party's signature lines
   AND their number line ("3. ____", "4. ____"). These are separate paragraphs
   near "LANDOWNERS (FIRST PARTY)" / "SECOND PARTY".

Also sweep for stale references (Recital A aggregate ownership, Clause 9
warranties, Clause 11 lien scope) — update only what the user asked; flag
inconsistencies you notice rather than silently changing them.

## 3. Record in-progress title flow as NEW RECITALS (H, I, J, K...)

When land is moving around at execution time, capture each fact as a numbered
recital before "NOW, THEREFORE". Pattern per transfer:

- **Pending purchase**: "FP1 is the current landowner of Sy 68/1 and is in the
  process of purchasing Sy 68/2 from its current owner (name and details to be
  shared later), whereupon he shall become the absolute owner of both."
- **Family release**: "Schedules 'C' and 'D' shall be transferred or released
  in favour of FP2 by the other family members who are the current joint
  owners thereof."
- **Road / access status**: distinguish what is ALREADY done ("has already been
  relinquished to the Grama Panchayat as a public road") from what transfers
  LATER ("shall transfer or relinquish to the THIRD PARTY or to the Project
  upon the complete development and sale of the Project to the buyers").
- **Regulatory condition precedent** (e.g. Grama Thana / gamathana extension):
  state current status (plots under limits), the pending application (Panchayat
  applied to extend limits to 250m), the approving authority (e.g. BIAPPA),
  the buyer benefit (20% plot usage for G+2), and who is responsible (FP + SP)
  before the developer markets/sells. Mark it as "the essence of this
  transaction and a condition precedent."

Update the matching OPERATIVE clauses too — here: Clause 2 heading became
"CONDITIONS PRECEDENT (OBLIGATIONS OF THE FIRST PARTY AND SECOND PARTY)",
Clause 2.1 intro "jointly satisfying", the Grama Thana bullet expanded with the
250m/BIAPPA/20%/G+2 detail, and Clauses 4.2.1/4.2.2 rewritten for the road
facts. Also note the TBD-purchase means Schedule B header now says
"FIRST PARTY NO. 1" even though the current owner's name is unknown — that's
the agreed treatment; do not invent the name.

## 4. Three-batch Docs API edit pattern (safe, no index math)

Do NOT mix deletion + insertion index math in one batch. Sequence:

- **Batch A — deleteContentRange** for removed paragraphs, ordered HIGHEST
  index first. Each delete range must span paragraph start → start of the next
  KEPT paragraph (paragraph endIndex includes the trailing \n, so delete up to
  the next block's startIndex to remove whole paragraphs including blanks).
  Verify each boundary prints the expected first-70-chars before applying.
- **Batch B — replaceAllText** (matchCase=True) for all text swaps: collective
  definitions, schedule headers, clause text. No indices involved; also fixes
  stray typos when the search string includes them (e.g. the Schedule B header
  had a duplicated "(Survey No. 68/2 - (Survey No. 68/2 - ..." — replacing the
  full string fixed both the ownership and the duplication).
- **Batch C — insertText** for new recitals, at the re-fetched startIndex of
  the anchor paragraph ("NOW, THEREFORE, IT IS MUTUALLY AGREED..."). Re-fetch
  the doc between batches — indices shift after A and B.

## 5. Verify like a reviewer

- Re-fetch and dump ALL paragraphs (startIndex/endIndex + text).
- Check parties section reads cleanly (1,2 then collective; 1,2 then
  collective), recitals H+ present, schedule headers reassigned.
- grep the dump for removed names (`MURALI|SUBRAMANYAIAH|NAVEEN|NO\. 3|NO\. 4`)
  — zero hits confirms the sweep.
- Check the signature block lost only the removed parties' lines.

## Reference session

- 20260731 — Doddasane (next to Airport) Term Sheet 9A FarmPlots RevShare,
  Dev-Cum-Sale MOU. Doc: `1vXpNnHl7IjboIA6CSwrW4U08Mo-Coj_TfdP0aGkMyJ4`.
- Removed FP3 (Murali C), FP4 (Subramanyaiah), SP3 (Naveen Kumar); Schedule B
  (68/2) → FP1 (purchasing, name TBD); Schedules C (28/P120) & D (28/P110) →
  FP2 (family release); recitals H–K added; Clause 2 + 4.2 updated.
- Note: user dictated "BIAPPA" — flagged that the authority may be "BIAAPA"
  (Bangalore International Airport Area Planning Authority); used user's exact
  spelling and asked before "correcting" it in a legal doc.
