# Document Scanner Pipeline - Implementation Plan

## Project Overview
Build a single Python package that processes images/PDFs into enhanced, OCR'd PDFs with correct orientation, perspective, and skew correction.

**Input:** Single image, multiple images, single PDF, or multiple PDFs
**Output:** Single PDF with all pages enhanced, oriented, and OCR'd

---

## Phase 1: Architecture & Feasibility

### ✅ Confirmed Feasibility
All required functionality is available via open-source libraries that run standalone in Python. No cloud APIs or proprietary software needed.

### Technology Stack

| Layer | Library | Purpose | Python Only |
|-------|---------|---------|-------------|
| **PDF Extraction** | PyMuPDF (fitz) | Fast PDF→image conversion | ✅ Yes |
| **Image I/O** | Pillow (PIL) | Load/save images | ✅ Yes |
| **Core CV** | OpenCV (cv2) | Border detection, perspective transform | ✅ Yes |
| **Advanced CV** | scikit-image | Morphological ops, advanced filtering | ✅ Yes |
| **Deskewing** | deskew | Detect/correct text rotation | ✅ Yes |
| **OCR** | pytesseract + Tesseract | Character recognition | ⚠️ Tesseract binary needed |
| **PDF Output** | PyPDF2 + reportlab | Create PDF with text layer | ✅ Yes |

**Tesseract Status:** Open-source OCR engine (available for Windows/Linux/Mac)

### Dependencies List

```
opencv-python>=4.8.0
Pillow>=10.0.0
scikit-image>=0.21.0
PyMuPDF>=1.23.0
deskew>=1.2.0
pytesseract>=0.3.10
PyPDF2>=3.15.0
reportlab>=4.0.0
numpy>=1.24.0
scipy>=1.10.0
```

---

## Phase 2: Detailed Processing Pipeline

### Input Handling
```
Raw Input (Images/PDF)
  ↓
Normalize to Image List (PIL.Image)
  ├─ If PDF → extract each page via PyMuPDF
  ├─ If single image → load via Pillow
  └─ If multiple images → load all via Pillow
```

### Per-Image Processing

```
1. ORIENTATION CORRECTION
   Input: Raw image
   - Convert to grayscale
   - Detect if text is rotated (0°, 90°, 180°, 270°)
   - Option A: Use deskew for fine-grained angle detection
   - Option B: Use OpenCV Hough transforms + edge analysis
   - Apply cv2.rotate() for 90° increments, cv2.warpAffine() for fine rotation
   Output: Correctly oriented image

2. PERSPECTIVE CORRECTION (Document Boundary Detection)
   Input: Oriented image
   - Convert to grayscale
   - Apply Gaussian blur (noise reduction)
   - Apply Canny edge detection
   - Find contours via cv2.findContours()
   - Approximate largest contour to quadrilateral
   - Calculate perspective transform matrix (cv2.getPerspectiveTransform)
   - Warp image (cv2.warpPerspective)
   Output: Top-down rectangular document

3. SKEW DETECTION & CORRECTION (Fine-grained)
   Input: Perspective-corrected image
   - Use deskew.determine_skew() to get rotation angle
   - If angle > 0.5°: apply cv2.warpAffine() to correct
   Output: Straight text alignment

4. PRECISE CROPPING
   Input: Deskewed image
   - Convert to grayscale, apply threshold
   - Find white/content boundaries
   - Crop to content area only (remove blank margins)
   Output: Tightly cropped document

5. IMAGE ENHANCEMENT FOR OCR
   Input: Cropped image
   - Apply Gaussian blur for noise reduction
   - Use cv2.adaptiveThreshold() to create binary image
   - Apply morphological operations (dilation/erosion) to enhance characters
   - Increase contrast (CLAHE - Contrast Limited Adaptive Histogram Equalization)
   Output: High-contrast, binary-ready image

6. OCR EXTRACTION
   Input: Enhanced image
   - Pass to pytesseract/Tesseract
   - Extract text with bounding boxes
   - Get confidence scores
   Output: Text + metadata (location, confidence)
```

### PDF Assembly
```
For each processed image:
  1. Add enhanced image as background layer
  2. Add OCR text as searchable text layer (invisible but indexed)
  3. Maintain proper page numbering
  4. Compile to single PDF
```

---

## Phase 3: API Design

### Main Function Signature
```python
def process_document(
    input_paths: Union[str, List[str]],  # File paths or bytes
    output_pdf: str,                      # Output PDF path
    enhance_quality: bool = True,         # Enable image enhancement
    ocr_enabled: bool = True,             # Enable OCR
    deskew: bool = True,                  # Correct text rotation
    perspective_correction: bool = True,  # Correct 3D distortion
    target_dpi: int = 300,                # Upscale small images
    debug: bool = False                   # Save intermediate images
) -> Dict[str, Any]:
    """
    Process document image(s)/PDF(s) into enhanced PDF with OCR.

    Returns:
        {
            'success': bool,
            'pages_processed': int,
            'ocr_text': str,
            'warnings': List[str],
            'output_path': str
        }
    """
```

---

## Phase 4: Implementation Structure

```
document_scanner/
├── __init__.py
├── core.py                 # Main processing pipeline
├── pdf_handler.py          # PDF extraction & assembly
├── image_processor.py      # OpenCV operations
├── ocr_engine.py           # Tesseract integration
├── enhancement.py          # Image enhancement techniques
├── utils.py                # Helpers (validation, logging)
├── config.py               # Constants, parameters
└── tests/
    ├── test_orientation.py
    ├── test_perspective.py
    ├── test_ocr.py
    └── fixtures/
        ├── sample_straight.jpg
        ├── sample_rotated.jpg
        ├── sample_skewed.jpg
        ├── sample_perspective.jpg
        └── sample_multipage.pdf
```

---

## Phase 5: Testing Strategy

### Unit Tests
- **Orientation:** Rotated images (90°, 180°, 270°)
- **Perspective:** Images taken at angles
- **Skew:** Text tilted 15-45°
- **OCR:** Text recognition accuracy
- **PDF Assembly:** Multi-page PDF creation

### Integration Tests
- Single image → PDF
- Multiple images → PDF
- PDF → Enhanced PDF
- Mixed inputs (images + PDFs)

### Test Images to Create
1. **Straight document** (baseline)
2. **Rotated 90°** (common phone photo)
3. **Skewed text** (document placed at angle)
4. **Perspective distortion** (shot from corner)
5. **Multi-page PDF** (3+ pages)

---

## Phase 6: Optimization Considerations

### Performance
- Parallel processing for multi-page documents
- Image downsampling for processing (then upsample for final PDF)
- Caching of transformed images
- Memory-efficient PDF assembly

### Reliability
- Fallback if perspective detection fails (use cropping only)
- Adaptive enhancement (detect image quality, adjust parameters)
- Error recovery (skip bad pages, log warnings)
- Confidence thresholds for OCR

### Quality
- Configurable enhancement levels (draft/normal/high-quality)
- DPI scaling for small/low-res input
- Text layer validation before PDF assembly

---

## Phase 7: Deliverables

### Package Output
1. **Installable Python package** (`pip install document-scanner`)
2. **CLI tool** (`document-scanner input.pdf --output output.pdf`)
3. **Python API** (importable for agent systems)
4. **Configuration file** (tunable parameters)
5. **Test suite** with sample documents
6. **Documentation** (README, API docs, examples)

---

## Timeline & Steps

| Phase | Task | Complexity | Duration |
|-------|------|-----------|----------|
| 1 | Setup project structure, install deps | Low | 5 min |
| 2 | PDF extraction + image I/O | Low | 10 min |
| 3 | Orientation detection & correction | Medium | 15 min |
| 4 | Perspective correction | Medium | 20 min |
| 5 | Deskewing | Low | 10 min |
| 6 | Image enhancement pipeline | Medium | 15 min |
| 7 | OCR integration | Low | 10 min |
| 8 | PDF assembly with text layer | Medium | 15 min |
| 9 | Testing + validation | Medium | 20 min |
| 10 | Documentation + CLI | Low | 10 min |

**Estimated Total:** ~2 hours for complete working system

---

## Next Steps

1. ✅ Review this plan (you are here)
2. Setup project structure and dependencies
3. Implement core processing pipeline
4. Create test images with known issues
5. Test each stage independently
6. Assemble into single package
7. Create comprehensive test suite
