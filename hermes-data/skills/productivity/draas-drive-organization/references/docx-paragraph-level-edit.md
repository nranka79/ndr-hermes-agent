# Editing a Drive .docx by replacing PARAGRAPHS as whole XML units

Use when NDR says "update this Word document" / "re-issue this NOC/draft in <someone else's> name" and the file is a
`.docx` stored on Drive. Verified 2026-09-18 re-issuing the two Prizm Developers NOCs from A.R. Mohammed Abdullah →
Feroz Ahmed (DRA's new landlord for the Prizm Greystone office, #204-206 Cunningham Road).

## Why not simple string replace

The text of one visible paragraph is split across many `<w:r>` runs (bold/italic spans, Word rsid splits).
Replacing a substring inside a run desynchronises formatting. The robust unit of edit is the **whole paragraph**.

## Recipe

1. **Download with `get_media`, not `export_media`** — Drive `.docx` uploads are not Docs Editors files:
   ```python
   from googleapiclient.http import MediaIoBaseDownload
   dl = MediaIoBaseDownload(buf, d.files().get_media(fileId=fid, supportsAllDrives=True))
   ```
   Save a **local backup of the original** before touching anything.

2. **Extract `word/document.xml`** from the zip and split into paragraphs:
   ```python
   paras = re.findall(r'<w:p\b.*?</w:p>|<w:p\b[^>]*/>', xml, re.S)
   ```

3. **Locate targets by their TEXT, never by paragraph index.**
   ```python
   def txt(p): return ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p))
   hits = [(i,p) for i,p in enumerate(paras) if pred(txt(p))]
   assert len(hits) == 1
   ```
   ⚠️ **Paragraph indices drifted between two near-identical sibling documents** — the R3N NOC and the DRA KAAJ NOC
   differed by one empty paragraph before the signature block, so an index-keyed replacement wrote
   `Designation: Owner` into the `Name:` slot and left `Designation: Managing Partner` in place. Content matching
   caught it. Index-keying is only safe if you assert the paragraph's text before replacing.

4. **Rebuild each target paragraph from scratch**, reusing the original `<w:pPr>` and the run-properties templates
   observed in the file. For these NOCs:
   ```
   normal run: <w:rPr><w:sz w:val="22"/><w:szCs w:val="22"/><w:rtl w:val="0"/></w:rPr>
   bold   run: <w:rPr><w:b w:val="1"/><w:bCs w:val="1"/><w:sz w:val="22"/><w:szCs w:val="22"/><w:rtl w:val="0"/></w:rPr>
   ```
   Build runs from a `[(style, text), ...]` list so bold spans on defined terms survive; keep
   `<w:t xml:space="preserve">`. Escape `&` → `&amp;` (the premises clause legitimately contains `&`).

5. **Rezip the WHOLE archive** — iterate `zin.infolist()` and `writestr` every entry, swapping only
   `word/document.xml`. Never re-zip just a subset (`extractall` renames `customXML` → `customXml` and corrupts it;
   here the entry is `customXML/item1.xml`).

6. **Validate before upload:** `zipfile.testzip()` + `xml.etree.ElementTree.fromstring()` on document.xml.

7. **Update in place to preserve the link, permissions and revision history:**
   ```python
   d.files().update(fileId=fid, media_body=MediaFileUpload(path, mimetype=DOCX), fields='id,name,version')
   ```
   Drive bumps `version` (58→59) — the pre-edit text stays recoverable. Then **re-download and re-assert** the
   expected phrases, not just the HTTP 200.

## Pitfalls

- **False-positive residual grep:** after fixing the R3N typo `gnature of Property Owner:` → `Signature of...`,
  grepping for `'gnature of Property'` still matches (it is a substring of `Signature`). Grep for the *fixed*
  string, or use an anchored pattern.
- **Deliberate residuals:** the earlier owner's name must still appear in the historical lease-deed clause
  (`executed by the erstwhile owner ... Mr. A.R. Mohammed Abdullah`). A blanket "no Abdullah anywhere" assertion
  is wrong — assert on the *issuer* clauses instead.
- **Where the ownership chain is unknown, do not invent a transfer.** Neutral wording was used
  ("the said premises having since been transferred to and vested in me") and the exact instrument was flagged
  back to NDR as an assumption to confirm.
- **Aadhaar numbers do not belong on a NOC going to a Registrar** — leave them off even when the ID is the source
  document. Name + residential address + mobile is sufficient identification.
- **Rotating a sideways Aadhaar scan:** `PIL Image.rotate(90, expand=True)` is *anti-clockwise* and was the correct
  direction (confirmed by OCR keyword hit-rate 6/6 vs 0/6 for the clockwise pass). Verify with a row-vs-column
  variance metric on the binarised image, then rebuild the PDF with `img.save(..., save_all=True,
  append_images=[...])`. Aadhaar backs also print the 12-digit number **rotated 90°** along the right edge —
  crop and OCR it separately with `tessedit_char_whitelist=0123456789`.
