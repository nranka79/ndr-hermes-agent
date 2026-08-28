# Drive Document Routing — Identifying the Right Folder for an Incoming Document

When the user sends a PDF and says "analyze it, file it in the right folder, confirm the name," the workflow has four steps, each with a non-obvious failure mode.

## 1. Extract the subject first (vision_analyze over rendered pages)

For PDFs whose final destination is unclear, do NOT start with `fitz.get_text()`. The user's memory already says: "Document review: always read PDF via pdf2image+vision_analyze before naming." Vision returns:
- Document type / publication (Karnataka Gazette, Sale Deed, FIR, etc.)
- Date (publication date or document content date)
- Issuing authority / sender
- Subject matter + key entities
- Quoted legal text (sections, regulation numbers)

For a government gazette or regulatory amendment, this gives you: notification number, gazette number, date, ministry/department, full title of the proposed regulation, and the deadline for objections. That single extracted subject is your search seed for Step 2.

The user's working filename convention is `YYYYMMDD Project Entity DocumentType` — and the date in the filename = doc content date, NOT upload date. The folder may use today's date.

## 2. Search Drive for peer files / parent folder

The right destination folder usually has a name that does NOT match the document's subject. Example: a Karnataka RMP-2015 zonal regulations amendment gazette filed in `R&D Bangalore/` — the folder name says nothing about RMP, but it already contains a related `20260401_BBMP_GBA_Draft_Building_ByeLaws_2026_Deviation_Condonation_Fees.pdf`. **The peer file is the signal, not the folder name.**

Strategy:
1. Extract key entities from the vision output (department code, regulation reference, location).
2. Run multiple `name contains` queries against Drive to find peer files: `BBMP`, `GBA`, `RMP`, `UDD`, `Karnataka`, `R&D`, `Research`, `Government`, `LPA`, `Zonal`, etc.
3. Dedupe by file/folder ID across all queries.
4. For each candidate parent folder, list its contents. If a peer file has a similar subject (same agency, same regulation family, same jurisdiction), that folder is your destination.

The user's Drive is large and lightly-organised. Many important folders have generic names (`R&D Bangalore`, `Engineering`, `Legal`) and are recognisable only by their contents, not their titles.

## 3. Confirm with the user BEFORE renaming/uploading

User memory is explicit: "Propose name to user and wait for approval — do NOT rename/upload until confirmed." Always:
- Show the document's subject summary
- Show the candidate folder (full path: list parent chain via recursive `parents[0]` lookup)
- Show the candidate filename
- Wait for an explicit go-ahead

### Naming convention: Project vs Location distinction

The filename format `YYYYMMDD Project Entity DocumentType` uses "Project" for the **project name** (e.g. `Ranka Udaya`, `Ranka Amber`). When the document is about a **geographic location** (city/area) rather than a named project, use `{Location} Property` instead of `{Location} Project`:

| Document subject | WRONG | RIGHT |
|---|---|---|
| Term sheet for land in Ooty | `20260606 Ooty Project Term Sheet.pdf` | `20260606 Ooty Property - Term Sheet.pdf` |
| Sale deed for a Hosur property | `20260315 Hosur Project Sale Deed.pdf` | `20260315 Hosur Property - Sale Deed.pdf` |

Similarly, folder names should reflect location: `Ooty Property Documents` not `Cool Property Documents` — descriptive folder names prevent confusion when multiple projects share a location.

**Tell-tale:** If the document's subject mentions a city/town name without a branded project name (e.g. "Ooty", "Hosur", "Bagalur", "Sarjapura"), it's location-based → use "Property" not "Project". If it mentions a branded project name (e.g. "Ranka Udaya", "Ranka Amber", "Ranka Oasis"), use the project name directly.

## 4. PITFALL — venv requirement for Drive API calls

`/usr/bin/python3` does NOT have `googleapiclient` installed. Any Drive/Gmail/Docs script must be run with the hermes venv python:

```bash
# WRONG — ModuleNotFoundError: No module named 'googleapiclient'
python3 /tmp/script.py

# RIGHT
/opt/hermes/.venv/bin/python3 /tmp/script.py
```

Also: the script must run with `HOME=/data/hermes/users/<telegram_id>` set, otherwise the gws_auth helper can't find the per-user OAuth token. Combined command:

```bash
HOME=/data/hermes/users/<telegram_id> /opt/hermes/.venv/bin/python3 /tmp/script.py
```

## 5. PITFALL — vision_analyze on text-based PDFs can return a prompt echo

Per the file-reading matrix in SKILL.md, `vision_analyze` on a text-based PDF may return a rephrasing of the prompt rather than the actual content. For documents where the text layer exists, use the `pdftoppm + vision` path only when:
- The PDF is a scan / image-based / has a non-extractable text layer
- The vision response is needed for spatial understanding (legal tables, stamp text, handwriting)

For pure text extraction of gazettes, modern regulatory filings, and other clean PDFs, `fitz.open(path).get_text()` is instant and reliable. For an unknown document, render the first 2-3 pages to PNG (use `pdftoppm` at 150 DPI) and feed them to `vision_analyze` to get the subject-level summary, which is what you need for routing. Don't waste a fitz call if the routing decision needs structured output (notification numbers, dates, references) that vision extracts more reliably.

## 6. Recursive path lookup pattern

To show the user a full path like `DRA Projects/Ranka Oasis/Master Plan`, walk the parents chain:

```python
def get_path(fid, depth=0, max_depth=8):
    f = drive.files().get(fileId=fid, fields='id,name,parents', supportsAllDrives=True).execute()
    name = f.get('name', '?')
    if depth >= max_depth or not f.get('parents'):
        return name
    return get_path(f['parents'][0], depth+1, max_depth) + '/' + name
```

Folder IDs often look like `1zccbQKIFhCC1OssqQzFcrXLW44eajHPU` (My Drive) or short `0AFOc8cSaJXPGUk9PVA` (shared drive root) — both are valid; the recursive lookup handles them uniformly.

## 7. Reference: DRAAS regulatory / R&D folder anchors (June 2026)

Some known destinations in the user's Drive for regulatory / government documents:

| Folder | ID | Use for |
|---|---|---|
| R&D Bangalore | `1cE9dYYoIYp58_Tk3fG2ZWXlOwXOA9K0L` | Karnataka BBMP/GBA/UBD government drafts, regulatory research, gazette notifications |
| Legal (root) | `0B1Oc8cSaJXPGMEJneG14SnZBeTQ` | RTI applications, court notices, Rame Gowda issue, partnership firm docs |
| Engineering (root) | `0B1Oc8cSaJXPGRFc0SWNTVmJXZFU` | Building byelaws, construction standards, methodology, work orders |
| NDR Notes | `1A5hIQeTDXfF_zRhCVExPB9rtW43MUCkq` | NDR-personal working notes, KBMP / planning queries |
| NDR Tenders | `1oC45ftuaAY5gvcNE1fSG6OK_OpFlPlhr` | Government tenders, RFPs |
| BDA Notices | `1y22xvaf5kib1K9ZaS0uQ5nC33XBA6V8u` | BDA-specific notifications |
| WHPL FIR Madras HC Court Orders | `1_4hKrCYlvJRHCR96XcnfEk9xgNDuZEDb` | WHPL litigation |

If a government / regulatory PDF arrives, scan these first. Peer files (other gazettes, BBMP/GBA drafts, RTI replies) inside the candidate folder are the strongest signal.
