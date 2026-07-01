#!/usr/bin/env python3
"""Drive analysis fix -- fills missing Description column in ranka_oasis_file_list_v5.csv"""
import csv, io, os, sys, time
from pathlib import Path

TOKEN_PATH = Path("/data/hermes/users/7449813913/gws_token.json")
CSV_PATH   = Path("/data/hermes/users/7449813913/ranka_oasis_file_list_v5.csv")
MODEL      = "anthropic/claude-sonnet-4-6"
DESC_COL   = "Description (AI - verify)"

GDOC_MIME_MAP = {
    "application/vnd.google-apps.document":     "text/plain",
    "application/vnd.google-apps.spreadsheet":  "text/csv",
    "application/vnd.google-apps.presentation": "text/plain",
    "application/vnd.google-apps.form":         "text/plain",
}

TYPE_TO_MIME = {
    "document":     "application/vnd.google-apps.document",
    "spreadsheet":  "application/vnd.google-apps.spreadsheet",
    "sheet":        "application/vnd.google-apps.spreadsheet",
    "presentation": "application/vnd.google-apps.presentation",
    "prompt":       "application/vnd.google-apps.document",
}

SKIP_TYPES = {"folder", "map", "earth"}


def get_drive():
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    creds = Credentials.from_authorized_user_file(TOKEN_PATH)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_PATH.write_text(creds.to_json())
    return build("drive", "v3", credentials=creds)


def export_gdoc(svc, file_id, mime_type):
    from googleapiclient.http import MediaIoBaseDownload
    export_mime = GDOC_MIME_MAP.get(mime_type, "text/plain")
    req = svc.files().export_media(fileId=file_id, mimeType=export_mime)
    buf = io.BytesIO()
    dl = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        _, done = dl.next_chunk()
    return buf.getvalue().decode("utf-8", errors="replace")


def download_binary(svc, file_id):
    from googleapiclient.http import MediaIoBaseDownload
    req = svc.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    dl = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        _, done = dl.next_chunk()
    return buf.getvalue()


def extract_pdf_text(data):
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        texts = []
        for page in reader.pages[:8]:
            t = page.extract_text()
            if t:
                texts.append(t)
        return "\n".join(texts)
    except Exception as e:
        return f"[PDF extraction failed: {e}]"


def get_real_mime(svc, file_id):
    """Always fetch actual MIME from Drive — CSV Type column is unreliable for binary Office files."""
    meta = svc.files().get(fileId=file_id, fields="mimeType,name,size").execute()
    return meta.get("mimeType", ""), meta.get("name", ""), int(meta.get("size", 0) or 0)


def extract_office_text(data, file_name):
    """Best-effort text from .docx / .xlsx / .pptx using zipfile+xml."""
    import zipfile, re
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            text_parts = []
            for name in z.namelist():
                if re.search(r'(word/document|xl/shared|ppt/slides/slide\d)', name):
                    xml = z.read(name).decode("utf-8", errors="ignore")
                    # strip XML tags
                    plain = re.sub(r'<[^>]+>', ' ', xml)
                    plain = re.sub(r'\s+', ' ', plain).strip()
                    if plain:
                        text_parts.append(plain)
            return " ".join(text_parts)[:8000]
    except Exception:
        return data.decode("utf-8", errors="ignore")[:8000]


def get_content(svc, file_id, raw_type, file_name):
    # Always resolve actual MIME from Drive — CSV labels are unreliable
    try:
        actual_mime, drive_name, size = get_real_mime(svc, file_id)
    except Exception:
        actual_mime, drive_name, size = "", file_name, 0

    effective_name = drive_name or file_name

    # Google native editors format → export as text
    if actual_mime in GDOC_MIME_MAP:
        text = export_gdoc(svc, file_id, actual_mime)
        return text[:8000] if text else ""

    # Zero-size file → skip
    if size == 0:
        return ""

    # Binary download for everything else
    data = download_binary(svc, file_id)
    if not data:
        return ""

    fname = effective_name.lower()
    if fname.endswith(".pdf") or actual_mime == "application/pdf":
        return extract_pdf_text(data)[:8000]

    try:
        return data.decode("utf-8", errors="ignore")[:8000]
    except Exception:
        return "[binary content, could not extract text]"


def analyze_with_ai(content, file_name, file_type):
    import httpx
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set")

    prompt = (
        f"Document name: {file_name}\nType: {file_type}\n\n"
        f"Content (excerpt):\n{content[:5500]}\n\n"
        "Write a concise 2-3 sentence description of what this document is "
        "and what it contains. Only the description, no preamble."
    )
    resp = httpx.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": MODEL, "messages": [{"role": "user", "content": prompt}], "max_tokens": 220},
        timeout=45,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def save_csv(rows, fieldnames):
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def needs_analysis(row):
    desc = row.get(DESC_COL, "").strip()
    return (
        not desc
        or desc in ("?", "pending")
        or "not locally available" in desc
        or desc.startswith("[File")
        or "content ERR" in desc
    )


def main():
    print("=== Drive Analysis Fix ===")
    key = os.environ.get("OPENROUTER_API_KEY", "")
    print(f"OpenRouter key: {'SET (' + key[:12] + '...)' if key else 'NOT SET'}")
    if not key:
        sys.exit(1)

    svc = get_drive()
    print("Drive service: OK")

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    fieldnames = list(rows[0].keys())

    todo = [r for r in rows if needs_analysis(r)]
    print(f"Total rows: {len(rows)} | Need analysis: {len(todo)}\n")

    updated = 0
    skipped = 0
    failed  = 0

    for i, row in enumerate(todo, 1):
        file_id   = row.get("File ID", "").strip()
        file_name = row.get("File Name", "").strip()
        raw_type  = row.get("Type", "").strip()
        no        = row.get("No", "")

        prefix = f"[{i}/{len(todo)}] #{no}"

        if raw_type in SKIP_TYPES:
            print(f"{prefix} SKIP ({raw_type}): {file_name[:50]}")
            skipped += 1
            continue

        if not file_id:
            print(f"{prefix} SKIP no file ID: {file_name[:50]}")
            skipped += 1
            continue

        print(f"{prefix} {file_name[:55]} ({raw_type})", end="", flush=True)

        # Resolve shortcuts
        actual_id   = file_id
        actual_type = raw_type
        if raw_type == "shortcut":
            try:
                meta = svc.files().get(fileId=file_id, fields="shortcutDetails").execute()
                sc = meta.get("shortcutDetails", {})
                actual_id   = sc.get("targetId", file_id)
                target_mime = sc.get("targetMimeType", "")
                if target_mime == "application/vnd.google-apps.folder":
                    print(f" -> shortcut->folder, skip")
                    skipped += 1
                    continue
                actual_type = target_mime
                print(f" -> shortcut->{actual_id[:16]}", end="", flush=True)
            except Exception as e:
                print(f" -> shortcut resolve ERR: {e}")
                failed += 1
                continue

        # Get content
        try:
            content = get_content(svc, actual_id, actual_type, file_name)
        except Exception as e:
            print(f" -> content ERR: {e}")
            failed += 1
            continue

        if len(content.strip()) < 30:
            print(f" -> too short ({len(content)} chars), skip")
            skipped += 1
            continue

        print(f" -> {len(content)} chars", end="", flush=True)

        # AI analysis
        try:
            desc = analyze_with_ai(content, file_name, raw_type)
        except Exception as e:
            print(f" -> AI ERR: {e}")
            failed += 1
            continue

        # Update row in list
        for r in rows:
            if r.get("File ID") == row.get("File ID"):
                r[DESC_COL] = desc
                break
        updated += 1
        print(f"\n  OK: {desc[:100]}")

        if updated % 5 == 0:
            save_csv(rows, fieldnames)
            print(f"  [checkpoint: {updated} updates saved]")

        time.sleep(0.3)

    save_csv(rows, fieldnames)
    print(f"\n=== Done === updated={updated} skipped={skipped} failed={failed}")
    print(f"CSV: {CSV_PATH}")


if __name__ == "__main__":
    main()
