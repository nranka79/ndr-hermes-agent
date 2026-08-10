# Verifying scan orientation deterministically (tesseract OSD beats vision OCR)

Symptom: user uploads a scanned government document that is rotated 90° and asks you to "fix the effect" / file it upright. Getting the rotation direction wrong produces a sideways PDF in the permanent record.

## Why not vision_analyze
- On Kannada (and most non-Latin) scans, vision_analyze's OCR path mangles text in BOTH orientations ("qpenaoge" etc.) — useless as an orientation signal.
- The LLM-backed visual description often claims "text is horizontal, left-to-right" for ANY rotation, because the model mentally auto-corrects. Ambiguous and unreliable for this one question.

## The deterministic method (tesseract OSD)
1. Make all candidate rotations with PIL (PIL `rotate()` is CCW-positive: `rotate(90)` = CCW, `rotate(-90)` = CW, `expand=True` keeps full page):
   - rot_A = rotate(-90)  # CW
   - rot_B = rotate(90)   # CCW
   - rot_C = rotate(180)
2. Run OSD on each: `tesseract <img> - --psm 0 2>/dev/null | grep -i rotate`
3. The upright image reports `Orientation in degrees: 0 / Rotate: 0` (highest confidence).
   - In the 2026-08-05 Gunjur PTCL endorsement case: original & rot_A → 180, rot_B → **0 (upright)**, rot_C → 270. Correct file = `rotate(90, expand=True)`.
4. Convert the chosen rotation to PDF (`PIL.Image.save(buf, format="PDF", resolution=150.0)`) and upload via Drive `MediaIoBaseUpload`.

## Pitfalls
- `tesseract --psm 0` prints OSD to stderr — redirect `2>/dev/null` or grep both streams.
- OSD confidence is low on noisy photos; still decisive vs vision guesswork. If OSD itself fails, fall back to comparing line-structure of OCR output (upright text yields line-shaped OCR rows; rotated yields column-shaped garble) — weaker signal, use as last resort.
- Only tesseract's `eng`+`osd` language packs are installed; that's fine, OSD does not need the document's language.
