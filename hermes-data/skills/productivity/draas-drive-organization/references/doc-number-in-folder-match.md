# Doc-number-in-folder matching (registration docs vs Drive folder)

Recurring DRAAS request: the user pastes a list of registration document
numbers (`434/1976 ... 9188/2025 ... 5804/2026`) and asks "are these in the
<folder>" — e.g. the Oasis - print folder check (2026-08-13, 52 docs vs
`1sG1KlY-higI7vhoafHmyarS_qIWkspEW`). The naive approach (strict
`NNNN/YYYY` regex over filenames) matches only ~40% of real files. This is
the robust workflow.

## Steps

1. **Resolve the folder by name, disambiguated.** `name contains 'OASIS'`
   matched 15 folders; `name contains 'PRINT'` matched exactly 1 ("Oasis -
   print"). Use the most distinctive word from the user's folder name, then
   verify `parents` before walking. Never assume the first name hit is the
   target.

2. **RE-WALK the folder; never trust a stored count.** A previous session's
   "891 files" for the same folder id turned out to include subfolder copies
   later consolidated (Oasis-print live tree = 303 files / 5 subfolders).
   Recursive walk with `files().list(q="'<id>' in parents", pageSize=1000)`
   + nextPageToken, depth-capped, error-tracked. Report the count you just
   produced.

3. **Extract doc numbers from filenames with a tolerant matcher.** Real
   filename forms that break a strict regex:
   - Separators: `5268/1980`, `5268_1980`, `6921-2004`, "No.1287 of 1999",
     "No.2542 of 2006", "No 21785(2024)", "No.2334/1981"
   - 2-digit year: `no.3320/16` = 3320/2016
   - Date-prefix year: `16102023 Sale deed 21201` = 21201/2023 (year is in
     the leading 8 digits; NO year token after the number)
   - Far-apart tokens: "2025 Gift Deed No 9196" (number and year separated
     by words — heuristic: exactly one big number + exactly one year token
     in the name → pair them)
   - Typos: "No 12988 0f 2017" ('0f')
   - Protect `/` in filenames: replace `/` with ` / ` before regexing.
   - Then dump the full filename list and REVIEW manually — automated
     matchers still miss date-prefix years and typo forms.

4. **Drive-wide search for the misses, then check `parents`.** A
   `name contains '<number>'` search returns files living in OTHER folders
   (ALL Legal Files, Saveganapalli Legal Docs, Gifts Deeds - Govt, Certified
   Copies Shared, Ranka Oasis - Banking). For each hit, `files().get(...,
   fields='parents')` and resolve the parent folder name. Report THREE
   buckets to the user:
   - in the target folder (with file paths)
   - in Drive but NOT in this folder (name the actual folder)
   - not found anywhere in Drive

5. **Flag near-matches; don't claim them.** Same number, different year AND
   different deed (1706/1980 sale deed in folder vs 1706/1986 settlement in
   ALL Legal Files). Year-label mismatch ("Copy of 2026 Gift Deed No 9188"
   vs EC doc 9188/2025). Same-date different-doc traps (19345/2023 vs
   19344/19346/19356/2023; 4515 vs 4512; 12569 POA vs 12669 release). Report
   "present but titled X" / "same number, different doc" — never a clean YES.

## Result shape (2026-08-13 worked example)

35/52 in folder, 2 elsewhere in Drive, 15 missing. User accepted this
three-bucket format and was offered (but did not yet request) a DocMatrix
status tab.

## Sheet-append variant

If the user wants it persisted, the established pattern (see tn-ec-parsing
"Post-delivery audit #2") is a NEW tab, columns Sl No | Document No. | Type
| Transaction date | Appears in ECs | In Drive Folder? (YES/NO) | Drive File
Name | Drive Link, YES green / NO red, never touching existing tabs.
