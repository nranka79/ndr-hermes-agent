# Kannada Registered-Deed → English Translation Pipeline

Verified 2026-08-20 on a 13-page scanned Kannada **General Power of Attorney**
(GPA DNH-4-01083-2022-23, Sy.223 Byadarahalli) → clean English HTML+CSS + PDF.

## 1. Drive download (auth required)

A raw curl on a private/shared Drive file returns a Google sign-in HTML page, not
the PDF. Use the authenticated account.

```python
import sys, io, os
from googleapiclient.http import MediaIoBaseDownload
sys.path.insert(0, "/opt/hermes")
from tools.gws_auth import build_service

svc = build_service("drive", "v3", service_name="google-draas")
meta = svc.files().get(fileId=FILE_ID, fields="id,name,mimeType,size").execute()
# non-Google-native file: get_media (binary). Google-apps file: files().export PDF.
request = svc.files().get_media(fileId=FILE_ID)
fh = io.FileIO(OUT, "wb")
dl = MediaIoBaseDownload(fh, request)
done = False
while not done:
    status, done = dl.next_chunk()
```

Run via `terminal()` (needs vault socket + `HERMES_SESSION_USER_ID`), not
`execute_code`. Probe with `open(path,'rb').read(10)` → expect `b'%PDF'`.

## 2. Detect scanned vs text layer

```python
import pymupdf
doc = pymupdf.open(pdf)
for i, page in enumerate(doc):
    t = page.get_text()
    print(i+1, len(t), len(page.get_images()))
```

Garbled Kannada text layer (`len` in the tens-to-hundreds) across all pages ⇒
scanned → render+OCR. (Some pages are registration cover sheets; some have images.)

## 3. Render pages to PNG

```python
pix = page.get_pixmap(dpi=200)   # ~1500x2200 for A4 — good for tesseract
pix.save(f'page_{i+1:02d}.png')
```

## 4. OCR with Tesseract Kannada (KEY — beats vision_analyze)

**Finding:** `vision_analyze` returned garbled/mangled Kannada on dense scanned
legal text (the LLM OCR folds dense Kannada into mojibake — mixed cover-sheet
headers + body). Tesseract `-l kan --psm 6` returned clean, readable Kannada.

If `tesseract --list-langs` lacks `kan`, download to a LOCAL dir (system tessdata
is read-only) and prefix every call:

```bash
mkdir -p /tmp/tessdata
cp /usr/share/tesseract-ocr/5/tessdata/eng.traineddata /tmp/tessdata/
curl -sL https://github.com/tesseract-ocr/tessdata_fast/raw/main/kan.traineddata -o /tmp/tessdata/kan.traineddata
export TESSDATA_PREFIX=/tmp/tessdata
for i in 01 02 03; do
  echo "===== PAGE $i ====="
  tesseract page_$i.png stdout -l kan --psm 6 2>/dev/null
done > gpa_kannada_ocr.txt
```

`-l kan` alone is fine for Kannada-heavy bodies (Aadhaar/survey/extent numbers
survive). Use `-l kan+eng` only for genuinely mixed pages (registration
"Document Sheet" covers).

## Variant: Court orders (Sub-Divisional Officer / Revenue)

See `references/kannada-court-order-translation.md` for the distinct structure
of a **quasi-judicial order** (case number, presiding officer, Petitioner vs
Respondent, Subject/Reference, fact-finding → ORDER with numbered directions,
pronouncement date).

Key differences from the GPA/deed pipeline:

- **vision_analyze CAN work** for ≤3-page structured Kannada documents (court
  orders, certificates, TSIR) — the existing rule "vision garbles Kannada"
  applies to dense multi-page deeds, NOT to short structured documents. Prompt
  with "Look at this image carefully — read it visually, extract every word."
  Use `google/gemini-2.0-flash` (not 2.5-flash which returned garbled text in
  one test).
- **Filter template-artifact dates.** Printed header fields like `09-05-2003`
  or `09-05-2030` are decades-old form templates, NOT real dates. The real
  date is in the pronouncement clause.
- **Order section is critical** — present the appeal result + numbered directions
  prominently, as that is the binding legal outcome.

## 5. Translate faithfully, keep the original structure

For a GPA specifically:
- **Verify party direction.** OCR: `ನಿಮಗೆ` ("to you") marks the donee;
  `ಮಾರಾಟಗಾರರು` (sellers) are usually the grantors. In Sy.223 the grantors
  (ChikkAnjinamma / Manjula B.M. / B.M. Manu, heirs of late V. Mariyappa) grant
  the GPA to C.R. Nagendra (Partner, M/s Satvik Developers). Cross-check against
  any prior documentation of the same instrument (memory / earlier sessions had
  this GPA as "in favour of C.R. Nagendra for ₹1.62 Cr").
- Numbered power clauses (`ol` with CSS `counter()`), Schedule of Property with
  East/West/North/South boundaries, title recital (Tehsildar Order → mutation),
  stamp-certificate, signature block.
- Include a translation note that the registered Kannada original prevails.

## 5b. CRITICAL — identify the ACTUAL document type from content, not the filename/request

Verified 2026-08-20: a file titled *"Sy No 223 Agreement deed with non possession
12781-22-23 dtd 11-01-2023"* was handed to the agent as "a Kannada GPA, translate it."
The Kannada content identified it as a
**ಸ್ವಾಧೀನರಹಿತ ಶುದ್ಧಕ್ರಯದ ಮುಂಗಡ ಕರಾರುಪತ್ರ = Agreement to Sell (absolute sale, WITHOUT
possession)**, Reg. **DNH-1-12781-2022-23** — NOT a GPA. So:

1. **Read the first OCR page's title line before translating anything.** Distinctive
   Kannada instrument names to recognise:
   - ಜನರಲ್ ಪವರ್ ಆಫ್ ಅಟಾರ್ನಿ ಯಾ ಸರ್ವೆ ಸಾಮಾನ್ಯ ಅಧಿಕಾರ ಪತ್ರ = **General Power of Attorney**
   - ಸ್ವಾಧೀನರಹಿತ ಶುದ್ಧಕ್ರಯದ ಮುಂಗಡ ಕರಾರುಪತ್ರ = **Agreement to Sell (non-possession)**
   - (also ಶುದ್ಧಕ್ರಯದ ಮುಂಗಡ ಕರಾರುಪತ್ರ = agreement to sell; ಕ್ರಯಪತ್ರ = sale deed;
     ಭಾಗ ಪತ್ರ = partition deed)
2. **Translate it faithfully as what it actually is** — do NOT force the requested
   label onto it. Title the document by its real instrument type.
3. **Flag the discrepancy to the user** clearly ("This is NOT a GPA — it's an
   Agreement to Sell"), because they may be holding the wrong file or expecting the
   wrong rights. Don't silently relabel or silently comply.

### Agreement-to-Sell (non-possession) — structure that differs from a GPA

Besides the usual parties / recital-of-title (Tehsildar Order → mutation) / Schedule
of Property, an Agreement-to-Sell translation must capture:

- **Total sale consideration** (total) and **advance/earnest actually received** (total),
  then a **balance payable at registration** figure. Cross-check arithmetic: for
  Sy.223, advance ₹1,00,00,000 (One Crore) + balance ₹62,00,000 = ₹1,62,00,000 total.
- **Advance-payment schedule table** — render as an HTML table (Sl / Date / Amount /
  Mode+DD-no+bank+branch / in-favour-of). Sy.223: 5 DDs (IDFC Bank Jeevanbheema Nagar),
  two of which go to non-party **Sri Muniraju** (former agreement-holder, towards
  cancellation).
- **Cancellation recital of a prior agreement** — the sellers had earlier agreed to
  sell to Sri Rajanna @ Muniraju (Reg. DNH-1-01343-2013-14), later cancelled; the
  name-change (e-Stamping/notary) and cancellation deed numbers must be transcribed
  even when partially illegible (leave `…` placeholders rather than guessing).
- **Non-possession clause:** sellers retain physical possession; title documents
  handed to buyer. Name the document "without possession" accordingly.
- **Conditions / covenants:** default remedies (buyer-fails → refund advance +
  cancel; seller-fails → buyer can deposit balance in court, obtain order, get
  possession + full authority to register in his name), warranty of no prior
  sale/gift/mortgage/GPA/will, and **consent parties** (e.g. Muniraju + Smt. Savitha R.,
  wife of 3rd seller) who attest.

Reuse the same HTML+CSS scaffold as the GPA (header, meta-table, parties,
clauses, schedule box, sig-box) — just swap the clause list and add the payment
table. The `counter()`-numbered clauses work the same.

## 6. Build HTML+CSS and verify with WeasyPrint

```bash
uv pip install --python /tmp/myvenv/bin/python weasyprint
/tmp/myvenv/bin/python -c "
import weasyprint
weasyprint.HTML('GPA_English.html').write_pdf('GPA_English.pdf')
"
# verify via pymupdf -> page PNGs -> vision_analyze (header, meta table,
# clause counters, schedule box render cleanly)
```

Deliver both `.html` (the requested artifact) and `.pdf`. A `.docx` can be offered
as a follow-up.

## Pitfalls
- Direct curl on private Drive = sign-in page, not PDF — always go through
  `build_service`.
- vision_analyze garbles dense Kannada — use tesseract `kan`; reserve vision for
  verifying the RENDERED English output, not for reading Kannada.
- Kannada `.traineddata` is not preinstalled; fetch to `/tmp/tessdata`.
- WeasyPrint is not in the main venv — install into any scratch venv with `uv`.
