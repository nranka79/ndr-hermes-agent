# Partition Deed Allocation Extraction & A-G Totals

When the user shares a Drive folder / spreadsheet for a dissolved partnership (e.g. Satvik Developers) and asks: "get the exact land extent for sale deeds, agreements, and Land of Ashok / Land of Nagendra after partition deed" — the partition deed is the authoritative allocation instrument.

## Trigger
- "scan the documents and get exact land extent for sale deeds, agreements, Land of X and Land of Y after partition deed"
- "who got what after the partition" / "allocate the firm's lands between the partners"
- Totals requests on land extents ("total again", "TOTAL IS WRONG AGAIN")

## Workflow

1. **Look for Google Docs versions of the instruments FIRST.** The 2026 reconstitution deed / contribution deed / MOU are often native Google Docs with a full text layer — read them via Docs API (`docs.documents().get`) and extract tables via `body.content[].table.tableRows` before OCR'ing any 30+ page scanned deed. The reconstitution deed frequently reproduces the partition deed's schedules verbatim (Schedule A/B/C) — that alone answers the allocation question.

2. **The controlling document is the Partition Cum Settlement Deed** (e.g. SRJ-1-10373-2023-24, 16.01.2024). Structure to expect:
   - Recitals: firm history, list of sale deeds acquired (Schedule A items), agreements (ATS/GPA/JDA), pending registrations, litigation lands
   - Operative clauses: dissolution → partners become co-owners in ratio (commonly 90:10) → Schedule A split into Schedule B (Partner 1) + Schedule C (Partner 2)
   - **Schedule B = all registered sale-deed parcels + ALL agreement rights + ALL pending registrations + ALL litigation/pending-mutation lands** (usually Partner No. 1)
   - **Schedule C = the small remainder** (often kharab-heavy parcels, e.g. 221/2 3A 38G kharab + 176/2 1A 20G = 5A 18G)

3. **Checksum the split**: Schedule B + Schedule C extents MUST equal Schedule A total. If they don't, you misread an item.

4. **Cross-document verification catches stale data:**
   - The partition deed may recite an extent that DIFFERS from the original sale deed — the partition deed is authoritative for allocation purposes (verified: 175/9 = 27G in partition deed vs 25G in the original SD; 27G also matches the RTC — the SD was the error).
   - Later instruments (2026 reconstitution) may re-allocate parcels (verified: 223 went to Ashok in the 2026 partition deed but appears in Nagendra's Schedule C in the 2026 reconstitution deed — flag it, don't silently pick one).

## A-G (Acres-Guntas) Arithmetic — CRITICAL, user-corrected twice

**1 acre = 40 guntas. Carry at >= 40.** 42 guntas = 1A 02G (NOT "0-42" or "42 guntas" in a totals row).

Python helpers to always use (never hand-sum in prose):
```python
def ag_to_guntas(a, g): return a * 40 + g
def guntas_to_ag(g):
    a = int(g // 40)
    gg = round(g - a * 40, 4)
    if gg >= 40: a += 1; gg -= 40
    return a, gg
def ag_to_acres(a, g): return a + g / 40.0
```

### Pitfalls that caused "TOTAL IS WRONG AGAIN" (both fired in one session)
1. **Dropping kharab from the gross.** 221/2 = "3A 00G + 0-38G kharab" means GROSS = 3A 38G (standard Karnataka reading: total extent includes kharab). The old tab listed 221/2 as 3-00G, silently losing 38 guntas. Gross column must include kharab; list kharab separately for the net row.
2. **Decimal column shifted by one row** in the totals tab (41/17 showed 23.852, SALE DEEDS TOTAL showed -1.100). When writing totals to Sheets, always read the tab back and verify each row's A-G label matches its decimal value.
3. **41/17 = 0-05.08G** — fractional guntas are legal (5.08/40 = 0.127 ac); don't round to 5G or 0.125.
4. Recompute totals programmatically, then cross-check by summing raw guntas (`sum(ag_to_guntas(*e))`), then verify the tab read-back.

## Verified example (Satvik Developers, Byadarahalli, Aug 2026)
- Partition Deed No. SRJ-1-10373-2023-24, 32 pp scan → tesseract `-l kan+eng`
- Schedule A (registered SD land): 18A 16.20G = 18.405 ac
- Schedule B (Ashok): 12A 38.20G = 12.955 ac + agreements 8A 27.08G + pending regs 13A 3.12G + litigation lands 8A 31G → 43A 19.40G total
- Schedule C (Nagendra): 5A 18G = 5.450 ac (221/2 3A 38G + 176/2 1A 20G)
- Checksum: B + C = 18A 16.20G = Schedule A ✓
- Downstream: Ashok contributes Byadarahalli lands to DRA KAAJ at ₹3.75 Cr/ac (Contribution Deed 24.06.2026)

## Pitfalls from the documents-sheet follow-up (same deed, Aug 2026)

1. **OCR text layer can drop the schedule-letter suffix.** `pdftotext`/tesseract printed the Schedule C heading as just "SCHEDULE" (line 1640) — the "- C" and partner name sat on wrapped lines that OCR mis-merged. The Schedule B heading on its page rendered fine. Don't trust plain-text page order; **render the page image (`pdftoppm -png -r 150 -f N -l N`) and vision-check the heading letter + partner name before concluding which schedule is which.** In this deed Schedule C physically follows Schedule B + items 17–20 on later pages (PDF pages 25–30), so text-order alone can mislead.

2. **Agreement totals are context-dependent — never quote one number for "agreements".**
   - Documents sheet (rows = registered instruments): 9 agreement/GPA docs → **5 unique parcels** (45/5B, 190/3, 45/6, 223, 216) = **8A 13G**; ATS+GPA for the same survey counts ONCE.
   - Sketch/map extent table: **18A 13G** — the map adds pending-registration parcels 45/P3, 45/P5, 45/P7 (10A total) that have **no documents in the sheet**.
   - Map extent tables can also OMIT parcels that exist as deeds (41/11 0-20G was not drawn on the sketch, so the map sale-deed total was 24A 14.08G vs 24A 34.08G including the 41/11 deed row).
   - Always state which source (documents sheet vs map vs partition deed) a total comes from, and flag the delta.
