# RTC (Bhoomi Form 16) Reading — Karnataka Land Records

When the user shares RTC screenshots/PDFs (Record of Rights, Tenancy and Crop — Kannada Form 16) to verify land ownership, extent, or to reconcile a broker's claimed acreage, use this field map and reconciliation pattern. Verified 2026-08-01 on the Nandi Hills backside villa proposal (Sy 75/76, Rajabhets, Doddaballapur taluk).

## When to use
- User shares "RTC" / "Bhoomi" / "pahani" images for a land parcel
- User asks "who owns this land per the RTC?", "is it single owner?", "does the extent add up to the claimed X acres?"
- Land proposal intake: RTCs are the primary extent/owner verification before entering a Kelsa land proposal

## Field map (Kannada RTC Form 16)

| Section | Kannada label | Meaning | Notes |
|---|---|---|---|
| Header | ತಾಲ್ಲೂಕು / ಹೋಬಳಿ / ಗ್ರಾಮ | Taluk / Hobli / Village | e.g. Doddaballapur / Kasaba / Rajabhets |
| 1 | ಸರ್ವೆ ನಂಬರು | Survey Number | e.g. 75, 76 |
| 2 | ಹಿಸ್ಸಾ | Hissa (sub-division) | May be blank for the whole Sy No |
| 3 | ಖೇತವಾರು ಒಟ್ಟು ವಿಸ್ತೀರ್ಣ | Total extent | Format A.G.G.G = acres.guntas.anekalu (1.28.00.00 = 1 acre 28 guntas; 40 guntas = 1 acre). **Pot Kharab** rows are deductions — the "ಉಳಿದದ್ದು" (remaining) row is the usable extent. |
| 4 | ಕಂದಾಯ | Land revenue assessment | ₹ amounts |
| 5 | ಮಣ್ಣಿನ ಹೆಸರು | Soil type | e.g. ಕೆಂಪು = red |
| 6 | ಪಟ್ಟಾ | Patta type | ಸರ್ಕಾರಿ = Government |
| 9 | ಕಚ್ಚೆ ಅಥವಾ ಸ್ವಾಧೀನದಾರನ ಹೆಸರು | **Holder / occupant name + father's name** | THE ownership field. Same name on every RTC = single owner. "ಬಿನ್" = son of. |
| 10 | ಕಚ್ಚೆ ಅಥವಾ ಸ್ವಾಧೀನತೆಯ ರೀತಿ | Mutation reference | MR H34/2018-2019 + date — the mutation register entry that put the current owner on title |
| 12 | ಸಾಗುವಳಿ ಮತ್ತು ಬೆಳೆ | Cultivator + crop table | **Cultivator names ≠ owner names.** Different people can cultivate (tenants/family) while the holder in section 9 is the recorded owner. |
| Footer | Bhoomi Land ID | Land ID / survey reference | e.g. 6250 8700 0178 — unique per record |
| Watermark | "For Viewing Only" | Non-certified copy | RTCs shared by brokers are usually viewing copies — fine for verification, not registrable proof |

## Key insights

1. **The RTC IS the Bhoomi record.** The Bhoomi portal (landrecords.karnataka.gov.in / bhoomi.karnataka.gov.in) may be unreachable from the server — but an RTC screenshot carries the Land ID and "RTC DIGITALLY SIGNED" stamp, so it IS the authoritative portal output. Owner verification can be done from the user's RTCs directly; no need to re-fetch the portal unless you want a fresher extract.

2. **Extent reconciliation is the core check.** Sum all RTC extents (acres + guntas/40) across every Sy No and hissa the user shares, and compare against the claimed deal acreage. Typical finding: broker claims 10A but RTCs sum to ~5.5-9.9A → what's missing? Present as a per-RTC table:
   ```
   | RTC | Sy No | Extent |
   | 1   | 75    | 1A 28G |
   | 2   | 76    | 2A 02G |
   ```
   Watch for duplicates: the same Sy No + extent appearing twice (once with hissa, once without) may be the same parcel printed twice — flag it rather than double-counting.

3. **Single owner vs multiple.** Read section 9 (holder) on EVERY RTC. All same name → single owner (state it). Different names → multiple owners — list them all. Do NOT infer from section 12 cultivators: Bhagirathi/Bhagya + T.V. Muniraju appearing as cultivators does NOT mean co-ownership; only section 9 names are the recorded owners. Flag cultivator names as "worth clarifying whether they have any claim" when the user wants belt-and-braces.

4. **Mutation reference (MR) tells the title story.** MR H17/2017-2018 dated 24/01/2018 = owner got title via mutation in early 2018. Consistent MR + date across records = clean chain; divergent MRs = worth a deeper look.

## RTC batch OCR → extent extraction (Drive RTCs vs deed extents)

**Trigger:** User asks to cross-check deed extents against RTC records for a batch of surveys (e.g. 25 registered deeds → 95 RTC PDFs on Drive). Verified 2026-08-14 on Satvik Developers Byadarahalli docs.

1. **Find RTCs on Drive:** `files().list(q="fullText contains '<village>' and name contains 'RTC'", pageSize=100)` with pagination — most village RTC bundles are named `Byadarahalli SY No <main>-<hissa> RTC.pdf` (e.g. `219-5`). Build a lookup dict keyed by `main-hissa`; whole-sy-no files (e.g. `223 RTC.pdf`, `180 RTC.pdf`) key as just the number.

2. **Download + OCR:** render page 1 at 200–300 DPI (`pdftoppm -png -r 200`), OCR with Kannada tessdata (`TESSDATA_PREFIX=/tmp/tessdata tesseract img stdout --psm 6 -l kan+eng`) — see `ocr-and-documents` skill §Kannada OCR for the tessdata install. The extent value is in the TOP field band, NOT the crop table: crop `(0, h*0.10, w*0.50, h*0.30)`, upscale 2–3×, then OCR. The raw line reads `ಒಟ್ಟು ವಿಸ್ತೀರ್ಣ 0.27.00.00` (or `1-00.04.00` — OCR often renders the hyphen/dot inconsistently).

3. **Extract extent + holder from the same band:**
   - Extent = `A.G.G.G` (acres.guntas.anekalu): `0.27.00.00` = 0A 27G, `2.05.00.00` = 2A 05G, `1.20.00.00` = 1A 20G, `0.05.08.00` = 0A 05G 08 anekalu. **The 'ಉಳಿದದ್ದು' (remaining) row is the NET usable extent** — use it, not the gross row, when the gross row includes kharab/poramboke deductions.
   - Holder = section 9 name near `ಕಚ್ಚೆ ಅಥವಾ ಸ್ವಾಧೀನದಾರನ ಹೆಸರು` — the recorded owner. OCR renders it as e.g. `ಸಾತ್ವಿಕ್ ಡೆವಲಪರ್ಸ್` (Satvik Developers) / `ಬಿ.ಎಂ.ಮನು` (B.M. Manu) / `ಕೆಂಪಣ್ಣ ಎಸ್ ಹೆಚ್` (Kempanna S H).

4. **Cross-check pattern (deed extent vs RTC extent):** build a status table `Survey | Deed extent | RTC extent | RTC holder | Status | Notes`:
   - ✅ Match — deed extent == RTC extent (most cases when the deal is registered and mutated)
   - ❌ MISMATCH — deed says X, RTC says Y (e.g. Sy 175/9 deed 0-25G vs RTC 0-27G — flag for re-survey/phodi check)
   - ⚠ RTC NOT ON DRIVE — survey has no RTC file in the bundle; needs Bhoomi pull
   - **Holder tells the title story:** RTC holder == Satvik/vendee after registered sale deeds (mutation done); RTC still in vendor name (e.g. `ಬಿ.ಎಂ.ಮನು`, `ಕೆಂಪಣ್ಣ`) when only ATS/GPA executed → mutation pending. This is a quick due-diligence signal per survey.

5. **Splitting hissas:** a deed may cover `Sy 216` but RTCs exist as `216-1` (1A, Kempanna S H) + `216-2` (1A, Ashok Kumar) — the GPA covers one hissa portion. Never assume one RTC per deed survey; check every hissa file.

## WhatsApp discrepancy message pattern

When the broker's claimed acreage doesn't match the RTCs, the user wants a message that:
1. States the claim vs the evidence: "You mentioned 10 acres, but the RTCs you shared (Sy 75/76) — all hissas together total only ~5.55 acres."
2. Asks the missing-piece question: "So what are we missing? Please confirm the full extent and share remaining RTCs / survey numbers."
3. States the owner finding for confirmation: "As per the RTCs the owner is a single person: B.K. Revathi Kumar s/o M. Kempanna. Please confirm he is the single owner and the full extent stands in his name alone."

Tone: polite/cooperative opening ("one clarification"), firm on the discrepancy. This is a diligence challenge to a source, not an accusation.
