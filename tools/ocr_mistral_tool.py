#!/usr/bin/env python3
"""
Mistral OCR 4 tool — extract text from PDFs and images using Mistral AI's OCR 4 API.
Supports 100+ languages, handwritten text, complex layouts, and returns markdown.
"""

import json
import logging
import os

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MISTRAL_OCR_URL = "https://api.mistral.ai/v1/ocr"
MISTRAL_MODEL = "mistral-ocr-latest"
MAX_FILE_SIZE_MB = 20
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif", ".webp"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_mime_type(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    mime_map = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
        ".bmp": "image/bmp",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    return mime_map.get(ext, "application/octet-stream")


def _encode_file_base64(file_path: str) -> str:
    import base64
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _image_to_base64_data_uri(img, fmt: str = "JPEG") -> str:
    import base64
    import io
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    mime = "image/jpeg" if fmt == "JPEG" else "image/png"
    return f"data:{mime};base64,{b64}"


def _parse_page_range(spec: str) -> list[int]:
    parts = [p.strip() for p in spec.split(",")]
    result: list[int] = []
    for part in parts:
        if not part:
            continue
        if "-" in part:
            try:
                start_s, end_s = part.split("-", 1)
                start, end = int(start_s.strip()), int(end_s.strip())
                result.extend(range(start, end + 1))
            except ValueError:
                continue
        else:
            try:
                result.append(int(part))
            except ValueError:
                continue
    return sorted(set(r for r in result if r > 0))


def _call_mistral_ocr(payload: dict, api_key: str, timeout: float = 120.0) -> dict:
    import httpx
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=timeout) as client:
        resp = client.post(MISTRAL_OCR_URL, json=payload, headers=headers)
    if resp.status_code != 200:
        try:
            detail = json.dumps(resp.json(), indent=2)
        except Exception:
            detail = resp.text
        raise RuntimeError(f"Mistral OCR API error {resp.status_code}: {detail}")
    return resp.json()


def _call_mistral_ocr_page(image_data_uri: str, api_key: str) -> dict:
    payload = {
        "model": MISTRAL_MODEL,
        "document": {"type": "image_url", "image_url": image_data_uri},
    }
    return _call_mistral_ocr(payload, api_key, timeout=60.0)


def _merge_results(results: list[dict]) -> dict:
    all_pages: list[dict] = []
    total_usage: dict = {}
    page_offset = 0
    for res in results:
        pages = res.get("pages", [])
        for p in pages:
            p["index"] = page_offset + p.get("index", 0)
            all_pages.append(p)
        page_offset += len(pages)
        usage = res.get("usage", {})
        for k, v in usage.items():
            total_usage[k] = total_usage.get(k, 0) + v
    return {"pages": all_pages, "usage": total_usage}


def _pages_to_markdown(result: dict) -> str:
    lines = []
    for page in result.get("pages", []):
        idx = page.get("index", 0) + 1
        md = page.get("markdown", "")
        lines.append(f"--- Page {idx} ---\n{md}")
    return "\n\n".join(lines)


# ---------------------------------------------------------------------------
# OCR strategies
# ---------------------------------------------------------------------------


def _ocr_pdf_pages(file_path: str, api_key: str, pages_spec: str) -> dict:
    """
    Convert PDF pages to images and send each to Mistral OCR.
    """
    try:
        from pdf2image import convert_from_path
        from pypdf import PdfReader
    except ImportError:
        raise ImportError("pdf2image and pypdf are required for PDF OCR. Run: pip install pdf2image pypdf")

    total_pages = len(PdfReader(file_path).pages)

    if pages_spec and pages_spec.lower() != "all":
        page_numbers = _parse_page_range(pages_spec)
        page_numbers = [p for p in page_numbers if 1 <= p <= total_pages]
        if not page_numbers:
            return {"error": f"No valid pages in spec '{pages_spec}' (PDF has {total_pages} pages)"}
    else:
        page_numbers = list(range(1, total_pages + 1))

    first = min(page_numbers)
    last = max(page_numbers)
    images = convert_from_path(file_path, dpi=150, first_page=first, last_page=last)
    page_map = {first + i: images[i] for i in range(len(images))}

    results = []
    for pn in page_numbers:
        img = page_map.get(pn)
        if img is None:
            continue
        data_uri = _image_to_base64_data_uri(img)
        try:
            result = _call_mistral_ocr_page(data_uri, api_key)
            results.append(result)
        except Exception as e:
            logger.warning("Mistral OCR failed on page %d: %s", pn, e)
            results.append({
                "pages": [{"index": 0, "markdown": f"*[OCR failed on page {pn}: {e}]*"}],
                "usage": {},
            })

    merged = _merge_results(results)

    merged["total_pages_in_pdf"] = total_pages
    merged["pages_processed"] = len(page_numbers)

    return merged


def _ocr_single_file(file_path: str, api_key: str) -> dict:
    """
    Send a single image file to Mistral OCR.
    """
    b64 = _encode_file_base64(file_path)
    mime = _get_mime_type(file_path)
    data_uri = f"data:{mime};base64,{b64}"
    return _call_mistral_ocr_page(data_uri, api_key)


# ---------------------------------------------------------------------------
# Availability check
# ---------------------------------------------------------------------------


def _check_mistral_ocr_available() -> bool:
    return bool(os.environ.get("MISTRAL_API_KEY"))


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_OCR_MISTRAL_SCHEMA = {
    "name": "ocr_mistral",
    "description": (
        "Extract text from PDFs and images using Mistral OCR 4. "
        "Supports 100+ languages (including Kannada, Tamil, Hindi), "
        "handwritten text, and complex layouts. Returns markdown text."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the PDF or image file to OCR.",
            },
            "pages": {
                "type": "string",
                "description": (
                    "Page range for PDFs, e.g. '1-5', '1,3,5', or 'all'. "
                    "Default: 'all'. Ignored for image files."
                ),
            },
            "include_raw": {
                "type": "boolean",
                "description": (
                    "If true, include the full raw OCR result (with image refs, "
                    "dimensions, usage stats) in the output. Default: false."
                ),
            },
        },
        "required": ["file_path"],
    },
}


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------


def _handle_ocr_mistral(args: dict, **kw) -> str:
    file_path = args.get("file_path", "").strip()
    pages_spec = args.get("pages", "all")
    include_raw = args.get("include_raw", False)

    if not file_path or not os.path.exists(file_path):
        return json.dumps({"error": f"File not found: {file_path}"})

    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        return json.dumps({"error": "MISTRAL_API_KEY environment variable is not set"})

    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        return json.dumps({
            "error": f"File too large ({file_size_mb:.1f} MB). Maximum: {MAX_FILE_SIZE_MB} MB."
        })

    ext = os.path.splitext(file_path)[1].lower()

    try:
        if ext == ".pdf":
            result = _ocr_pdf_pages(file_path, api_key, pages_spec)
            if "error" in result:
                return json.dumps(result)
        elif ext in SUPPORTED_IMAGE_EXTENSIONS:
            result = _ocr_single_file(file_path, api_key)
        else:
            return json.dumps({
                "error": f"Unsupported file format: {ext}. "
                f"Supported: .pdf, {', '.join(sorted(SUPPORTED_IMAGE_EXTENSIONS))}"
            })

        markdown_text = _pages_to_markdown(result)

        output = {
            "success": True,
            "text": markdown_text,
            "pages_processed": len(result.get("pages", [])),
        }

        if ext == ".pdf":
            output["total_pages_in_pdf"] = result.get("total_pages_in_pdf", 0)

        if include_raw:
            output["raw_result"] = result

        return json.dumps(output)

    except ImportError as e:
        return json.dumps({"error": f"Missing dependency: {e}"})
    except Exception as e:
        logger.exception("ocr_mistral failed")
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

from tools.registry import registry  # noqa: E402

registry.register(
    name="ocr_mistral",
    toolset="documents",
    schema=_OCR_MISTRAL_SCHEMA,
    handler=_handle_ocr_mistral,
    check_fn=_check_mistral_ocr_available,
    requires_env=["MISTRAL_API_KEY"],
    is_async=False,
    description=_OCR_MISTRAL_SCHEMA["description"],
    emoji="📝",
)
