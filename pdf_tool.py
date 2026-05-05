#!/usr/bin/env python3
"""
PDF Tool — full document processing: extract, convert, OCR, merge, split,
rotate, compress, image-extract.

Registered as: pdf_tool
Toolset: documents

Operations:
  extract_pages      — extract pages from a PDF as a new PDF
  to_images          — convert PDF pages to image files (returns a .zip)
  extract_page_image — convert a single page to an image file (not zip)
  images_to_pdf      — combine one or more images (or a .zip of images) into a PDF
  read_text          — extract plain text (ONLY call when user explicitly asks)
  ocr                — run OCRmyPDF on a scanned PDF (makes it searchable)
  merge              — merge multiple PDFs into one
  split              — split a PDF into one file per page (or by range)
  rotate             — rotate pages in a PDF
  compress           — compress/optimise a PDF with Ghostscript

Dependencies:
  pypdf       — PDF split/merge/rotate (pure Python, always available)
  pdf2image   — PDF → images (requires poppler-utils system package)
  Pillow      — image saving and images→PDF
  ocrmypdf    — OCR wrapper (requires ocrmypdf + tesseract system packages)
  ghostscript — compression (requires ghostscript system package)

Output files are written to /tmp/ and the path is returned for the agent
to send back to the user via send_document / drive upload.
"""

import io
import json
import logging
import os
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_page_spec(spec: str, total_pages: int) -> list[int]:
    """
    Parse a page spec string into a list of 0-based page indices.

    Spec examples:
      "all"       → all pages
      "1"         → page 1 only
      "1,3,5"     → pages 1, 3, 5
      "2-5"       → pages 2, 3, 4, 5
      "1,3-5,8"   → pages 1, 3, 4, 5, 8

    Page numbers in the spec are 1-based (human-friendly).
    Returns sorted unique 0-based indices.
    """
    spec = (spec or "all").strip().lower()
    if spec == "all":
        return list(range(total_pages))

    indices = set()
    for part in re.split(r"[,\s]+", spec):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, _, hi = part.partition("-")
            lo_i = max(1, int(lo.strip()))
            hi_i = min(total_pages, int(hi.strip()))
            indices.update(range(lo_i - 1, hi_i))
        else:
            n = int(part)
            if 1 <= n <= total_pages:
                indices.add(n - 1)
    return sorted(indices)


def _safe_output_path(suffix: str) -> str:
    """Return a temp file path with the given suffix."""
    fd, path = tempfile.mkstemp(suffix=suffix, dir="/tmp")
    os.close(fd)
    return path


def _collect_image_paths(source: str) -> list[str]:
    """
    Given a path that is either:
      - a single image file
      - a directory of images
      - a .zip file containing images
    Return a sorted list of image file paths.
    """
    IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}

    if source.endswith(".zip"):
        extract_dir = tempfile.mkdtemp(prefix="img_zip_", dir="/tmp")
        with zipfile.ZipFile(source) as zf:
            zf.extractall(extract_dir)
        paths = sorted(
            str(p) for p in Path(extract_dir).rglob("*")
            if p.suffix.lower() in IMAGE_EXTS
        )
        return paths

    p = Path(source)
    if p.is_dir():
        return sorted(str(f) for f in p.iterdir() if f.suffix.lower() in IMAGE_EXTS)

    if p.suffix.lower() in IMAGE_EXTS:
        return [source]

    return []


# ---------------------------------------------------------------------------
# Operations
# ---------------------------------------------------------------------------

def _extract_pages(args: dict) -> str:
    """
    Extract pages from a PDF and save as a new PDF.

    Required: file_path
    Optional: pages (default "all"), output_name
    """
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        return json.dumps({"error": "pypdf not installed. Run: pip install pypdf"})

    file_path = args.get("file_path", "").strip()
    pages_spec = args.get("pages", "all")
    output_name = args.get("output_name", "")

    if not file_path or not os.path.exists(file_path):
        return json.dumps({"error": f"File not found: {file_path}"})

    try:
        reader = PdfReader(file_path)
        total = len(reader.pages)
        indices = _parse_page_spec(pages_spec, total)

        if not indices:
            return json.dumps({"error": f"No valid pages in spec '{pages_spec}' (PDF has {total} pages)"})

        writer = PdfWriter()
        for i in indices:
            writer.add_page(reader.pages[i])

        if not output_name:
            base = Path(file_path).stem
            output_name = f"{base}_pages_{pages_spec.replace(',', '-').replace(' ', '')}.pdf"

        out_path = os.path.join("/tmp", output_name)
        with open(out_path, "wb") as f:
            writer.write(f)

        return json.dumps({
            "success": True,
            "output_path": out_path,
            "pages_extracted": len(indices),
            "total_pages": total,
            "page_spec": pages_spec,
        })
    except Exception as e:
        logger.exception("pdf_tool extract_pages failed")
        return json.dumps({"error": str(e)})


def _to_images(args: dict) -> str:
    """
    Convert PDF pages to images and return them as a .zip file.

    Required: file_path
    Optional: pages (default "all"), format ("jpg" or "png", default "jpg"),
              dpi (default 150), output_name
    """
    file_path = args.get("file_path", "").strip()
    pages_spec = args.get("pages", "all")
    fmt = args.get("format", "jpg").lower().strip(".")
    dpi = int(args.get("dpi", 150))
    output_name = args.get("output_name", "")

    if fmt not in ("jpg", "jpeg", "png"):
        fmt = "jpg"
    pil_fmt = "JPEG" if fmt in ("jpg", "jpeg") else "PNG"
    ext = ".jpg" if pil_fmt == "JPEG" else ".png"

    if not file_path or not os.path.exists(file_path):
        return json.dumps({"error": f"File not found: {file_path}"})

    try:
        from pdf2image import convert_from_path
    except ImportError:
        return json.dumps({"error": "pdf2image not installed. Run: pip install pdf2image (also needs poppler-utils)"})

    try:
        from pypdf import PdfReader
        total = len(PdfReader(file_path).pages)
        indices = _parse_page_spec(pages_spec, total)
        if not indices:
            return json.dumps({"error": f"No valid pages in spec '{pages_spec}' (PDF has {total} pages)"})

        # Convert only requested pages (1-based for pdf2image)
        first_page = min(indices) + 1
        last_page = max(indices) + 1
        images = convert_from_path(file_path, dpi=dpi, first_page=first_page, last_page=last_page)

        # Filter to exactly the requested indices within the slice
        slice_offset = first_page - 1
        filtered = [images[i - slice_offset] for i in indices if (i - slice_offset) < len(images)]

        if not output_name:
            base = Path(file_path).stem
            output_name = f"{base}_pages_{pages_spec.replace(',', '-').replace(' ', '')}.zip"

        zip_path = os.path.join("/tmp", output_name)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for idx, img in zip(indices, filtered):
                buf = io.BytesIO()
                img.save(buf, format=pil_fmt)
                zf.writestr(f"page_{idx + 1:04d}{ext}", buf.getvalue())

        return json.dumps({
            "success": True,
            "output_path": zip_path,
            "pages_converted": len(filtered),
            "format": fmt,
            "dpi": dpi,
        })
    except Exception as e:
        logger.exception("pdf_tool to_images failed")
        return json.dumps({"error": str(e)})


def _extract_page_image(args: dict) -> str:
    """
    Convert a single PDF page to a single image file (not a zip).

    Required: file_path, page (1-based integer)
    Optional: format ("jpg" or "png", default "jpg"), dpi (default 150), output_name
    """
    file_path = args.get("file_path", "").strip()
    page_num = args.get("page")
    fmt = (args.get("format") or "jpg").lower().strip(".")
    dpi = int(args.get("dpi", 150))
    output_name = args.get("output_name", "")

    if not file_path or not os.path.exists(file_path):
        return json.dumps({"error": f"File not found: {file_path}"})
    if page_num is None:
        return json.dumps({"error": "page (1-based integer) is required"})

    page_num = int(page_num)
    if fmt not in ("jpg", "jpeg", "png"):
        fmt = "jpg"
    pil_fmt = "JPEG" if fmt in ("jpg", "jpeg") else "PNG"
    ext = ".jpg" if pil_fmt == "JPEG" else ".png"

    try:
        from pdf2image import convert_from_path
        from pypdf import PdfReader

        total = len(PdfReader(file_path).pages)
        if page_num < 1 or page_num > total:
            return json.dumps({"error": f"Page {page_num} out of range (PDF has {total} pages)"})

        images = convert_from_path(file_path, dpi=dpi, first_page=page_num, last_page=page_num)
        if not images:
            return json.dumps({"error": f"Could not render page {page_num}"})

        if not output_name:
            base = Path(file_path).stem
            output_name = f"{base}_page_{page_num:04d}{ext}"

        out_path = os.path.join("/tmp", output_name)
        images[0].save(out_path, format=pil_fmt)

        return json.dumps({
            "success": True,
            "output_path": out_path,
            "page": page_num,
            "format": fmt,
            "dpi": dpi,
        })
    except ImportError:
        return json.dumps({"error": "pdf2image not installed. Run: pip install pdf2image (also needs poppler-utils)"})
    except Exception as e:
        logger.exception("pdf_tool extract_page_image failed")
        return json.dumps({"error": str(e)})


def _images_to_pdf(args: dict) -> str:
    """
    Combine one or more images (or a .zip of images) into a single PDF.

    Required: file_path  (single image, directory, or .zip of images)
    Optional: output_name
              file_paths (list of image paths — alternative to single file_path)
    """
    try:
        from PIL import Image
    except ImportError:
        return json.dumps({"error": "Pillow not installed. Run: pip install Pillow"})

    # Support either file_path (single/zip) or file_paths (list)
    file_paths_arg = args.get("file_paths") or []
    file_path = args.get("file_path", "").strip()
    output_name = args.get("output_name", "")

    if file_paths_arg:
        image_paths = sorted(file_paths_arg)
    elif file_path:
        image_paths = _collect_image_paths(file_path)
    else:
        return json.dumps({"error": "file_path or file_paths is required"})

    if not image_paths:
        return json.dumps({"error": "No image files found at the given path(s)"})

    try:
        images = []
        for p in image_paths:
            img = Image.open(p).convert("RGB")
            images.append(img)

        if not output_name:
            output_name = "combined.pdf"

        out_path = os.path.join("/tmp", output_name)
        if len(images) == 1:
            images[0].save(out_path, format="PDF")
        else:
            images[0].save(out_path, format="PDF", save_all=True, append_images=images[1:])

        return json.dumps({
            "success": True,
            "output_path": out_path,
            "pages": len(images),
            "source_files": len(image_paths),
        })
    except Exception as e:
        logger.exception("pdf_tool images_to_pdf failed")
        return json.dumps({"error": str(e)})


def _read_text(args: dict) -> str:
    """
    Extract plain text from a PDF.
    ONLY call this when the user explicitly asks to read/summarize/translate the PDF.

    Required: file_path
    Optional: pages (default "all")
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        return json.dumps({"error": "pypdf not installed. Run: pip install pypdf"})

    file_path = args.get("file_path", "").strip()
    pages_spec = args.get("pages", "all")

    if not file_path or not os.path.exists(file_path):
        return json.dumps({"error": f"File not found: {file_path}"})

    try:
        reader = PdfReader(file_path)
        total = len(reader.pages)
        indices = _parse_page_spec(pages_spec, total)

        parts = []
        for i in indices:
            text = reader.pages[i].extract_text() or ""
            if text.strip():
                parts.append(f"--- Page {i + 1} ---\n{text.strip()}")

        if not parts:
            return json.dumps({
                "success": True,
                "text": "",
                "note": "No extractable text found. The PDF may be scanned/image-based — use the ocr operation instead.",
                "pages_read": len(indices),
                "total_pages": total,
            })

        return json.dumps({
            "success": True,
            "text": "\n\n".join(parts),
            "pages_read": len(indices),
            "total_pages": total,
        })
    except Exception as e:
        logger.exception("pdf_tool read_text failed")
        return json.dumps({"error": str(e)})


def _ocr(args: dict) -> str:
    """
    Run OCR on a scanned PDF using ocrmypdf. Makes the PDF text-searchable.

    Required: file_path
    Optional: output_name, language (default "eng", use "eng+hin" for multilingual),
              deskew (bool, default True), rotate_pages (bool, default True)
    """
    file_path = args.get("file_path", "").strip()
    output_name = args.get("output_name", "")
    language = args.get("language", "eng")
    deskew = args.get("deskew", True)
    rotate_pages = args.get("rotate_pages", True)

    if not file_path or not os.path.exists(file_path):
        return json.dumps({"error": f"File not found: {file_path}"})

    if not output_name:
        base = Path(file_path).stem
        output_name = f"{base}_ocr.pdf"

    out_path = os.path.join("/tmp", output_name)

    cmd = ["ocrmypdf", "-l", language]
    if deskew:
        cmd.append("--deskew")
    if rotate_pages:
        cmd.append("--rotate-pages")
    cmd += ["--output-type", "pdf", file_path, out_path]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode not in (0, 6):
            # exit code 6 = already has OCR text (non-fatal)
            return json.dumps({
                "error": f"ocrmypdf failed (exit {result.returncode}): {result.stderr.strip()}"
            })

        already_ocr = result.returncode == 6
        if already_ocr and not os.path.exists(out_path):
            # ocrmypdf skipped writing; copy input as output
            import shutil
            shutil.copy2(file_path, out_path)

        size_kb = round(os.path.getsize(out_path) / 1024, 1)
        return json.dumps({
            "success": True,
            "output_path": out_path,
            "language": language,
            "already_had_text": already_ocr,
            "size_kb": size_kb,
        })
    except FileNotFoundError:
        return json.dumps({"error": "ocrmypdf not found. Install: apt-get install ocrmypdf tesseract-ocr"})
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "OCR timed out (>300s). Try a smaller PDF."})
    except Exception as e:
        logger.exception("pdf_tool ocr failed")
        return json.dumps({"error": str(e)})


def _merge(args: dict) -> str:
    """
    Merge multiple PDFs into a single PDF.

    Required: file_paths (list of PDF paths, in order)
    Optional: output_name
    """
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        return json.dumps({"error": "pypdf not installed. Run: pip install pypdf"})

    file_paths = args.get("file_paths") or []
    output_name = args.get("output_name", "merged.pdf")

    if not file_paths or len(file_paths) < 2:
        return json.dumps({"error": "file_paths must be a list of at least 2 PDF paths"})

    missing = [p for p in file_paths if not os.path.exists(p)]
    if missing:
        return json.dumps({"error": f"Files not found: {missing}"})

    try:
        writer = PdfWriter()
        total_pages = 0
        for fp in file_paths:
            reader = PdfReader(fp)
            for page in reader.pages:
                writer.add_page(page)
            total_pages += len(reader.pages)

        out_path = os.path.join("/tmp", output_name)
        with open(out_path, "wb") as f:
            writer.write(f)

        return json.dumps({
            "success": True,
            "output_path": out_path,
            "source_files": len(file_paths),
            "total_pages": total_pages,
        })
    except Exception as e:
        logger.exception("pdf_tool merge failed")
        return json.dumps({"error": str(e)})


def _split(args: dict) -> str:
    """
    Split a PDF into individual page PDFs (or by range).

    Default: one file per page. Each output is named <stem>_page_NNNN.pdf.
    Returns a .zip of all output files.

    Required: file_path
    Optional: pages (default "all"), output_name (for the zip)
    """
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        return json.dumps({"error": "pypdf not installed. Run: pip install pypdf"})

    file_path = args.get("file_path", "").strip()
    pages_spec = args.get("pages", "all")
    output_name = args.get("output_name", "")

    if not file_path or not os.path.exists(file_path):
        return json.dumps({"error": f"File not found: {file_path}"})

    try:
        reader = PdfReader(file_path)
        total = len(reader.pages)
        indices = _parse_page_spec(pages_spec, total)

        if not indices:
            return json.dumps({"error": f"No valid pages in spec '{pages_spec}' (PDF has {total} pages)"})

        base = Path(file_path).stem
        if not output_name:
            output_name = f"{base}_split.zip"

        zip_path = os.path.join("/tmp", output_name)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for i in indices:
                writer = PdfWriter()
                writer.add_page(reader.pages[i])
                buf = io.BytesIO()
                writer.write(buf)
                zf.writestr(f"{base}_page_{i + 1:04d}.pdf", buf.getvalue())

        return json.dumps({
            "success": True,
            "output_path": zip_path,
            "pages_split": len(indices),
            "total_pages": total,
        })
    except Exception as e:
        logger.exception("pdf_tool split failed")
        return json.dumps({"error": str(e)})


def _rotate(args: dict) -> str:
    """
    Rotate pages in a PDF.

    Required: file_path, degrees (90, 180, or 270)
    Optional: pages (default "all"), output_name
    """
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        return json.dumps({"error": "pypdf not installed. Run: pip install pypdf"})

    file_path = args.get("file_path", "").strip()
    degrees = int(args.get("degrees", 0))
    pages_spec = args.get("pages", "all")
    output_name = args.get("output_name", "")

    if not file_path or not os.path.exists(file_path):
        return json.dumps({"error": f"File not found: {file_path}"})
    if degrees not in (90, 180, 270):
        return json.dumps({"error": "degrees must be 90, 180, or 270"})

    try:
        reader = PdfReader(file_path)
        total = len(reader.pages)
        rotate_indices = set(_parse_page_spec(pages_spec, total))

        writer = PdfWriter()
        for i, page in enumerate(reader.pages):
            if i in rotate_indices:
                page.rotate(degrees)
            writer.add_page(page)

        if not output_name:
            base = Path(file_path).stem
            output_name = f"{base}_rotated_{degrees}.pdf"

        out_path = os.path.join("/tmp", output_name)
        with open(out_path, "wb") as f:
            writer.write(f)

        return json.dumps({
            "success": True,
            "output_path": out_path,
            "pages_rotated": len(rotate_indices),
            "degrees": degrees,
            "total_pages": total,
        })
    except Exception as e:
        logger.exception("pdf_tool rotate failed")
        return json.dumps({"error": str(e)})


def _compress(args: dict) -> str:
    """
    Compress/optimise a PDF using Ghostscript.

    Required: file_path
    Optional: quality ("screen"|"ebook"|"printer"|"prepress", default "ebook"),
              output_name
    """
    QUALITY_MAP = {
        "screen":   "/screen",    # 72 dpi — smallest, screen only
        "ebook":    "/ebook",     # 150 dpi — good balance
        "printer":  "/printer",   # 300 dpi — print quality
        "prepress": "/prepress",  # 300 dpi+ — high-end prepress
    }

    file_path = args.get("file_path", "").strip()
    quality = (args.get("quality") or "ebook").lower()
    output_name = args.get("output_name", "")

    if not file_path or not os.path.exists(file_path):
        return json.dumps({"error": f"File not found: {file_path}"})
    if quality not in QUALITY_MAP:
        return json.dumps({"error": f"quality must be one of: {', '.join(QUALITY_MAP)}"})

    if not output_name:
        base = Path(file_path).stem
        output_name = f"{base}_compressed.pdf"

    out_path = os.path.join("/tmp", output_name)
    in_size = os.path.getsize(file_path)

    cmd = [
        "gs",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS={QUALITY_MAP[quality]}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={out_path}",
        file_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            return json.dumps({
                "error": f"ghostscript failed (exit {result.returncode}): {result.stderr.strip()}"
            })

        out_size = os.path.getsize(out_path)
        reduction_pct = round((1 - out_size / in_size) * 100, 1) if in_size else 0

        return json.dumps({
            "success": True,
            "output_path": out_path,
            "quality": quality,
            "original_size_kb": round(in_size / 1024, 1),
            "compressed_size_kb": round(out_size / 1024, 1),
            "reduction_pct": reduction_pct,
        })
    except FileNotFoundError:
        return json.dumps({"error": "ghostscript (gs) not found. Install: apt-get install ghostscript"})
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Compression timed out (>300s). Try a smaller PDF."})
    except Exception as e:
        logger.exception("pdf_tool compress failed")
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

_OPERATIONS = {
    "extract_pages":      _extract_pages,
    "to_images":          _to_images,
    "extract_page_image": _extract_page_image,
    "images_to_pdf":      _images_to_pdf,
    "read_text":          _read_text,
    "ocr":                _ocr,
    "merge":              _merge,
    "split":              _split,
    "rotate":             _rotate,
    "compress":           _compress,
}


def _handle_pdf_tool(args: dict, **kwargs) -> str:
    operation = (args.get("operation") or "").strip()
    handler = _OPERATIONS.get(operation)
    if not handler:
        return json.dumps({
            "error": f"Unknown operation '{operation}'. Valid: {', '.join(_OPERATIONS)}"
        })
    try:
        return handler(args)
    except Exception as e:
        logger.exception("pdf_tool operation=%s failed", operation)
        return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_PDF_TOOL_SCHEMA = {
    "name": "pdf_tool",
    "description": (
        "Full PDF processing: extract pages, convert to images, OCR scanned PDFs, "
        "merge, split, rotate, compress, and combine images into PDFs.\n\n"
        "IMPORTANT: Only call read_text when the user explicitly asks to read, "
        "summarize, translate, or extract content from a PDF. "
        "Do NOT auto-read files.\n\n"
        "Operations:\n"
        "  extract_pages      — extract pages from a PDF into a new PDF\n"
        "  to_images          — convert PDF pages to images, returned as a .zip\n"
        "  extract_page_image — convert a single page to one image file (not zip)\n"
        "  images_to_pdf      — combine image files (or a .zip of images) into one PDF\n"
        "  read_text          — extract plain text (explicit user request only)\n"
        "  ocr                — OCR a scanned PDF via ocrmypdf (deskew, rotate, multilingual)\n"
        "  merge              — merge multiple PDFs into one\n"
        "  split              — split PDF into one-file-per-page, returned as a .zip\n"
        "  rotate             — rotate pages by 90/180/270 degrees\n"
        "  compress           — compress/optimise with Ghostscript\n\n"
        "Output is a file path in /tmp/. Send it back to the user with send_document "
        "or upload to Drive."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": list(_OPERATIONS.keys()),
                "description": "Operation to perform.",
            },
            "file_path": {
                "type": "string",
                "description": (
                    "Path to the input file (PDF, image, or .zip of images). "
                    "Use the path from the context note injected when the user sent the file."
                ),
            },
            "file_paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "List of file paths. For merge: list of PDFs to merge (in order). "
                    "For images_to_pdf: list of image paths."
                ),
            },
            "pages": {
                "type": "string",
                "description": (
                    "Page spec for extract_pages, to_images, split, rotate, read_text. "
                    "Examples: 'all', '1', '1,3,5', '2-5', '1,3-5,8'. "
                    "Page numbers are 1-based. Default: 'all'."
                ),
            },
            "page": {
                "type": "integer",
                "description": "Single page number (1-based) for extract_page_image.",
            },
            "format": {
                "type": "string",
                "enum": ["jpg", "png"],
                "description": "Image format for to_images and extract_page_image (default: jpg).",
            },
            "dpi": {
                "type": "integer",
                "description": "Resolution for image operations (default: 150). Use 300 for print quality.",
            },
            "language": {
                "type": "string",
                "description": (
                    "OCR language(s) for the ocr operation. "
                    "Examples: 'eng', 'hin', 'eng+hin'. Default: 'eng'."
                ),
            },
            "deskew": {
                "type": "boolean",
                "description": "For ocr: automatically deskew crooked pages (default: true).",
            },
            "rotate_pages": {
                "type": "boolean",
                "description": "For ocr: automatically rotate pages to correct orientation (default: true).",
            },
            "degrees": {
                "type": "integer",
                "enum": [90, 180, 270],
                "description": "Rotation degrees for the rotate operation.",
            },
            "quality": {
                "type": "string",
                "enum": ["screen", "ebook", "printer", "prepress"],
                "description": (
                    "Compression quality for compress. "
                    "screen=smallest/72dpi, ebook=balanced/150dpi (default), "
                    "printer=300dpi, prepress=high-end."
                ),
            },
            "output_name": {
                "type": "string",
                "description": "Output filename (optional). A sensible default is used if omitted.",
            },
        },
        "required": ["operation"],
    },
}


# ---------------------------------------------------------------------------
# Availability check
# ---------------------------------------------------------------------------

def _check_pdf_tool_available() -> bool:
    try:
        import pypdf  # noqa: F401
        return True
    except ImportError:
        return False


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

from tools.registry import registry  # noqa: E402

registry.register(
    name="pdf_tool",
    toolset="documents",
    schema=_PDF_TOOL_SCHEMA,
    handler=_handle_pdf_tool,
    check_fn=_check_pdf_tool_available,
    is_async=False,
    description=_PDF_TOOL_SCHEMA["description"],
    emoji="📄",
)
