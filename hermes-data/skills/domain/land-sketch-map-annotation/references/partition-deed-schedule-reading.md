# Partition Cum Settlement Deed — Partner-wise Survey Allocation

Worked example: Satvik Developers Partition Cum Settlement Deed, SRJ/10373/2023-24,
executed 16-Jan-2024, Bangalore. Parties: Ashok Kumar (Partner No.1, 90% share) and
C.R. Nagendra (Partner No.2, 10% share). Document in Drive folder shared for the
DRA KAAJ / Byadarahalli deal (filename `20240116_SatvikDevelopers_PartitionCumSettlementDeed_SRJ10373_AshokKumar_CRNagendra.pdf`, ID `1DwEIquGrI8fBMz2Qet5kB5tb306NdK-v`; duplicate `Partition Deed No10373-2023-24 ( Satvik)_260619_110317.pdf` same size = same doc).

## Answer for the Byadarahalli session (survey nos allocated to C.R. Nagendra)

**Schedule "C" (Partner No. 2 = Mr. C.R. Nagendra) — only 2 items:**
- Item 1: Sy No. 221/2 (old Sy 18 & 221) — 03A 38G of kharab — Byadarahalli, Kundana Hobli, Devanahalli Taluk
- Item 2: Sy No. 176/2 (old Sy 18 & 176) — 01A 20G — Byadarahalli, Kundana Hobli, Devanahalli Taluk
- Total: 05A 18G.

**Everything else → Partner No.1 (Ashok Kumar):**
- Schedule "B" (20 items): Byadarahalli sale-deed parcels 181, 41/11, 219/5, 219/6, 41/14,
  175/4, 175/6, 175/1, 175/9, 175/5, 180, 184/5, 174/3, 219/4, 219/7, 41/17, plus 118/2
  (Muthanallur Amanikere), 7/3, 7/9 (Samanahalli), 185 (Gunjur).
- Clause III: ALL rights under agreements for sale / GPA / JDA → Partner 1; plus survey
  nos. 209/1–209/4, 210 (litigation pending) and 111/1, 42/1, 47/2 (mutation pending).
- Clause IV: all sale deeds / agreements pending registration → Partner 1.

## Deed anatomy (standard Karnataka firm-partner partition)

- Recitals: firm acquired parcels under sale deeds "described in Items No. 1 to Item No. 22
  in the Schedule A" → Schedule A is the FIRM's full acquired list (22 items in this deed).
- Body clauses settle Schedule B → Partner 1, Schedule C → Partner 2, "full and final
  settlement of all his rights, title and interest in the Schedule A Property".
- **Clause III is the trap:** ATS/GPA/JDA rights and pending-litigation / pending-mutation
  parcels are carved to Partner 1 even though they're NOT in Schedule B's item list.
  When asked "what did X get", always read the body clauses, not just the schedules.

## OCR + verification recipe (worked)

1. `pdftotext -layout` → 0 lines (scanned). OCR: `ocrmypdf --skip-text --deskew --jobs 4`.
   PITFALL: `--force-ocr --skip-text` together is REJECTED ("Choose only one of
   --force-ocr, --skip-text, --redo-ocr") — use `--skip-text` alone for fully scanned deeds.
2. `pdftotext -layout` on OCR'd copy → grep party name (8 "Nagendra" hits: recitals,
   presenter, stamp pages only) → the allocation answer is in the SCHEDULE section, not body.
3. Search `SCHEDULE` headings; OCR mangles heading letters/partner names (read "SCHEDULE"
   where the real heading is "SCHEDULE - C" with "Partner No. 2 i.e. Mr. C.R. Nagendra").
   NEVER trust OCR heading letter — render pages and vision-verify.
4. `pdftoppm -png -r 100 -f 25 -l 32` → `vision_analyze` each candidate page: "which
   schedule/partner? list every survey no + extent". This deed: pages 25–29 = Schedule B
   (Ashok), page 30 = Schedule C (Nagendra), then witness page + SRO receipt pages.
5. Confirm the schedule END: after Schedule C Item 2 came "IN WITNESS WHEREOF" → item list
   is complete; don't assume hidden later items.

## Cross-check with map work

- 221/2 and 176/2 were already marked as sale-deed parcels on the Byadarahalli map; the
  deed confirms them as C.R. Nagendra's share post-firm-dissolution — the map legend
  (deed type) and schedule (owner) are different axes; keep both consistent in delivery.