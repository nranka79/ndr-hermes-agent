# Kannada OCR Keyword Patterns for Karnataka Land Documents

Extracted from OCR on ~25 test files from the Ramanagar (Lakshmipura/Bomvachanahalli) project. These keywords reliably identify document types in scanned Kannada PDFs.

## Setup

```bash
# Download Kannada traineddata (non-root directory)
python3 -c "import urllib.request; urllib.request.urlretrieve('https://github.com/tesseract-ocr/tessdata/raw/main/kan.traineddata', '/opt/data/kan.traineddata')"
cp /usr/share/tesseract-ocr/5/tessdata/eng.traineddata /opt/data/
cp /usr/share/tesseract-ocr/5/tessdata/hin.traineddata /opt/data/
export TESSDATA_PREFIX=/opt/data
```

## Keyword to Document Type Mapping

| Kannada Keyword | Transliteration | English Equivalent | Document Type | Req# |
|---|---|---|---|---|
| ಮ್ಯುಟೇಶನ್ / ಮ್ಯೂಟೇಶನ್ | Myuteshan | Mutation | Mutation Register (MR) | 8 |
| ಎನ್‌ಕಂಬರ್ / ಎನ್ಕಂಬರೆನ್ಸ್ | Enkambar | Encumbrance | Encumbrance Certificate (EC) | 9 |
| ಪಹಿವಾಟು / ಪಹಣಿ | Pahivatu / Pahani | Pahani/Pahani | RTC (Record of Rights) | 1 |
| ಖರೀದಿ | Kharidi | Purchase | Sale Deed | 5 |
| ಮಾರಾಟ | Maarata | Sale | Sale Deed | 5 |
| ರಿಜಿಸ್ಟ್ರಾರ್ / ಸಬ್‌ರಿಜಿಸ್ಟ್ರಾರ್ | Registrar / Sub-Registrar | Sub-Registrar | Sale Deed / GPA | 5,6 |
| ಅನುದಾನ / ಗ್ರಾಂಟ್ | Anudana / Grant | Grant | Grant / Title Deed | 3 |
| ಸಾಗುವಳಿ | Saguvali | Cultivation (Grant) | Saguvali Chit (Title Deed) | 3 |
| ತಿಪ್ಪಣಿ / ಟಿಪ್ಪಣಿ | Tippani | Notes/Field Notes | Tippani Book | 19 |
| ಹಿಸ್ಸಾ | Hissa | Portion/Division | Hissa Atlas / Hissa Tippani | 18,20 |
| ನಕ್ಷೆ | Nakshe | Map | Village Map / Survey Map | 22 |
| ಕಾರ್ಡಾ / ಕಾರ್ಡ | Karda | Card/Record | Karda (Field Measurement) | 23 |
| ವರ್ಗೀಕರಣ | Vargeekarana | Classification | Land Classification | 11 |
| ತಹಶೀಲ್ದಾರ್ / ತಹಸೀಲ್ದಾರ್ | Tahasildar | Tahsildar | Tahsildar Endorsement | 12 |
| ಕಂದಾಯ | Kandaya | Revenue | Revenue Document | 8 |
| ಆದೇಶ | Aadesha | Order | Government/AC Order | — |
| ನಕಲು | Nakalu | Copy | Certified Copy | — |
| ಖರಾಬ್ | Kharab | Waste/Degraded | Kharab Details | 21 |

## Extent Extraction from Kannada Deeds (verified Aug 2026, Byadarahalli Sy 223 docs)

Kannada registered deeds (Agreement Deed, GPA) state the property clause with a
**repeatable phrase pattern** — OCR-able with `-l kan+eng`:

- ಸರ್ವೆ ನಂಬರ್ ಹಳೇದು 18, ಹೊಸದು 223 ರಲ್ಲಿರುವ = Survey No. Old 18, New 223
- 02-00 (ಎರಡು ಎಕರೆ) ಖುಷ್ಕಿ ಜಮೀನು = **02-00 (two acres) dry land** ← extent + class
- 02-00 (ಎರಡು ಎಕರೆ) — extent format is Acres-Guntas like English deeds
- ಷೆಡ್ಯೂಲ್ ಜಮೀನು = Schedule Property; ಪೂರಾ ಸ್ವತ್ತಿನ ಪೈಕಿ = "out of the whole property" (GPA)
- ಪೋಡಿ = phodi (subdivision); ಪಹಣಿ = pahani/RTC; ಮ್ಯುಟೇಶನ್ = mutation

**Extraction pattern**: when OCR finds `ಸರ್ವೆ ನಂಬರ್` (survey number) with `ಹಳೇದು X, ಹೊಸದು Y` (old X, new Y) and a `NN-NN (ಎರಡು/ಮೂರು/ನಾಲ್ಕು ಎಕರೆ)` extent token, that is the schedule property. Kannada numerals may render as `02-00` (digits) — match `\d{1,2}-\d{2}\s*\(`. The `(ಎರಡು ಎಕರೆ)` parenthetical = "two acres" confirms the numeric reading. Report the old→new survey mapping alongside the extent.

## Classification Priority

Use English patterns FIRST (faster), then Kannada patterns as fallback:

```python
def classify_ocr_text(text):
    t = text
    # English patterns (fast)
    if re.search(r'MUTATION', t): return ('MR', 8)
    if re.search(r'ENCUMBRANCE', t): return ('EC', 9)
    if re.search(r'RTC|PAHIVAT|PAHANI', t) and 'MUTATION' not in t: return ('RTC', 1)
    if re.search(r'SALE\s*DEED', t): return ('Sale Deed', 5)
    if re.search(r'GRANT|SAGUVALI', t): return ('Grant', 3)
    if re.search(r'TIPPANI', t): return ('Tippani', 19)
    if re.search(r'HISSA', t): return ('Hissa', 18)
    if re.search(r'KARDA', t): return ('Karda', 23)
    if re.search(r'TEHSILDAR', t): return ('Tehsildar', 12)
    
    # Kannada patterns (slower but catches more)
    if re.search(r'ಮ್ಯುಟೇಶನ್|ಮ್ಯೂಟೇಶನ್', t): return ('MR', 8)
    if re.search(r'ಎನ್‌ಕಂಬರ್', t): return ('EC', 9)
    if re.search(r'ಪಹಿವಾಟು|ಪಹಣಿ', t): return ('RTC', 1)
    if re.search(r'ತಿಪ್ಪಣಿ|ಟಿಪ್ಪಣಿ', t): return ('Tippani', 19)
    if re.search(r'ಹಿಸ್ಸಾ', t): return ('Hissa', 18)
    if re.search(r'ತಹಶೀಲ್ದಾರ್|ತಹಸೀಲ್ದಾರ್', t): return ('Tehsildar', 12)
    if re.search(r'ಕಂದಾಯ', t): return ('Revenue', 8)
    
    return ('Unidentified', None)
```

## Documents Found via OCR in the Ramanagar Project

| Document Type | Count Found | Notes |
|---|---|---|
| Mutation Register (MR) | ~5 | Kannada "మ్యుటేಶన్" on first page, year range visible |
| RTC | ~8 | Kannada "ಪಹಿವಾಟು" header |
| Village Map | ~4 | Kannada "ನಕ್ಷೆ" identified |
| Unidentified | ~39 | OCR failed (low quality scan, Kannada text at 200 DPI) |

## Performance Notes

- **200 DPI:** ~5-10s per page, ~40% identification rate on Kannada docs
- **250 DPI:** ~8-15s per page, ~60% identification rate
- **300 DPI:** ~15-25s per page, ~70% identification rate (diminishing returns)
- **Small files (<2 MB):** Typically single-page MR documents, OCR completes in 3-5s
- **Large files (>15 MB):** Multi-page EC or Sale Deed, may take >60s per file

## File Size Heuristics (without OCR)

For timestamp-named files where OCR is too slow, these heuristics suggest document type based on size:

| File Size | Likely Document Type | Notes |
|---|---|---|
| < 500 KB | Single-page RTC or Form | Usually 1 page of text |
| 500 KB - 2 MB | Single-page MR or EC | More common for MR entries |
| 2 MB - 10 MB | Multi-page EC or Sale Deed | 5-15 pages |
| > 10 MB | Multi-page Sale Deed or scanned bundle | 20+ pages |
