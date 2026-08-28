# RERA Recovery Notice Translation — Worked Example

This reference file details a worked example of extracting, translating, and structuring a Kannada Tahsildar Final Notice / Recovery Notice for the Mirabilis project (KPDL) on behalf of Nishant Ranka (June 2026).

## The Source Document: Tahsildar Recovery Notice

On June 4, 2026, the user uploaded a PDF file (`Adobe Scan 04 Jun 2026.pdf`). Under inspection:
- It was a single-page document.
- It was pre-processed as a scanned PDF with low-accuracy OCR text overlay.
- Visual inspection via `vision_analyze` on page 1 rendered as JPEG confirmed it was a formal **Final Notice (ಅಂತಿಮ ನೋಟೀಸು)** issued by the **Special Tahsildar, Bengaluru East Taluk (K.R. Puram)** under the **Revenue Department, Government of Karnataka**.

### Key Extracted Facts

- **Subject Entity:** M/s Kolte Patil Developers Pvt Ltd (KPDL) / Mirabilis Project (Sy. No. 71, Horamavu Agara Village, Bengaluru East Taluk).
- **Secondary Addressee (Co-Recipient):** Mr. Dinesh D. Ranka, No. 4, Ranka Chambers, 31, Cunningham Road, Bengaluru - 560052.
- **RERA Complainant / Decree Holder:** Sabyasachi Behera.
- **Underlying Orders:**
  1. RERA Secretary Order: `ರೇರಾ/ಬೆಂ/6093/2023-24`, dated `23.05.2024`.
  2. Deputy Commissioner's Memorandum: `ಸ.ನಂ.ಎ.ಎ./ಡಿ.ಆರ್./ಸಿ.ಆರ್./51/2024-25`, dated `01.06.2024`.
  3. Original Attachment Orders: Attachment Order No. 37 (dated `18.09.2024`) and Notice No. 40 (dated `04.12.2024`).
- **Outstanding Arrears Amount:** **₹ 26,63,278/-** (Rupees Twenty-Six Lakhs, Sixty-Three Thousand, Two Hundred Seventy-Eight only).
- **Union Bank of India Collection Account:**
  - **Account No:** `520101080940037`
  - **IFSC Code:** `UBIN0901440`
  - **Branch:** S.C Road Branch, Bengaluru.
- **Timeline for Payment:** 10 days from notice receipt.
- **Consequences of non-payment:** Immediate **attachment of personal movable and immovable assets** belonging to the defaulters and their families, followed by **public auction**.

---

## The Workflow for Scanned Document Translation & Filing

When handling an official Indian legal document (e.g., Tahsildar recovery notice, Sale Deed, Partition Deed, High Court or RERA order):

1. **Locate the correct folder first:**
   - Run `drive.files().list(q="mimeType = 'application/vnd.google-apps.folder' and (name contains 'Project' or name contains 'Legal')")`.
   - Disambiguate similar folders. For example, for the "Mirabilis" project, we found `CRM Docs`, `Legal`, `Agreements` inside the parent directory. Inside the `Legal` folder, there was a specific folder `RERA Complaints & Orders` (ID: `1gWWGKOucWyDk7G8KOzQqIuQ3q5K895T0`) that already housed final orders for other complainants (`Parthachauhan` and `Aniketh Salunke`). Always respect existing filing categorizations before uploading!

2. **Render Scanned PDF to JPEG:**
   - Use `fitz` (PyMuPDF) in Python to render the PDF page directly to a local `/tmp/*.jpg` image file:
     ```python
     doc = fitz.open(pdf_path)
     page = doc[0]
     pix = page.get_pixmap(dpi=150)
     pix.save("/tmp/page_img.jpg")
     doc.close()
     ```
   - This eliminates external reliance on `pdf2image` and local `poppler` binaries, which can easily fail on container architectures or mismatch library dependencies.

3. **Verify Visually via `vision_analyze`:**
   - Send the rendered JPEG to `vision_analyze` with a target transcription prompt, asking to identify:
     - Document Type (Notice, Sale Deed, Order).
     - Authorizing/issuing authority name.
     - Subject matter of the dispute.
     - Case reference numbers and critical dates.
     - Specific monetary amounts and banking information.

4. **Typeset the English Translation as a PDF:**
   - Rather than sending a raw unstructured Markdown text summary to the user, programmatically compose a beautifully formatted PDF translating all the official seals, titles, body copy, and signature lines.
   - Use `reportlab` to lay out a clean corporate/legal translation document.
   - Build a flow of paragraphs and spacers using `SimpleDocTemplate` and custom `ParagraphStyle` structures.

5. **Apply Standard Naming Conventions:**
   - Target format: `YYYYMMDD Project Entity DocumentType`.
   - For this example:
     - Original: `20260601 Mirabilis KPDL Tahsildar Recovery Notice SabyasachiBehera_original.pdf`
     - English: `20260601 Mirabilis KPDL Tahsildar Recovery Notice SabyasachiBehera_English.pdf`
   - Ask the user for explicit approval on the target folder and proposed names before running any Drive uploading tool calls.
