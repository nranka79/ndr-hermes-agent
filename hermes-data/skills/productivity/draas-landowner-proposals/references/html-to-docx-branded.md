# HTML → Branded DOCX (DRA navy/gold) via pandoc

Use when the user wants a Word-editable version of a WeasyPrint HTML proposal ("generate in docx", "for alignment"). A clean structural DOCX (standard Word styles, no print CSS) is the right default — the user aligns/restyles in Word. Offer navy/gold branding as a second pass.

## 1. Install pandoc (static binary — no apt on this host)

```bash
uname -m   # aarch64 on this host!
# MUST download the arm64 build — amd64 gives "Exec format error"
curl -sL -o /tmp/pandoc.tar.gz https://github.com/jgm/pandoc/releases/download/3.1.11/pandoc-3.1.11-linux-arm64.tar.gz
tar -xzf /tmp/pandoc.tar.gz -C /tmp
/tmp/pandoc-3.1.11/bin/pandoc --version
```

## 2. Plain conversion (alignment-first)

```bash
/tmp/pandoc-3.1.11/bin/pandoc proposal.html -f html -t docx -o proposal.docx
```

Pandoc maps h1–h4 → real Word Heading styles, tables → Word tables, and embeds local `<img>` files into `word/media/`. It ignores the print CSS (page breaks, colors) — that's expected and fine for alignment.

## 3. Branded version (navy headings + gold accents + navy table headers)

Three steps — build a reference doc, convert with it, post-process tables:

**a) Reference doc** (patches `word/styles.xml`):
```bash
/tmp/pandoc-3.1.11/bin/pandoc --print-default-data-file reference.docx > /tmp/ref_base.docx
# unzip → patch styles.xml with lxml → rezip as /tmp/ref_branded.docx
```
For each style with styleId `Title`, `Heading1`–`Heading4`:
- `<w:rPr>` color → `1F3864` (navy), size per level (Title 30, H1 28, H2 26, H3 24, H4 22)
- Title/H1/H2: add `<w:pBdr><w:bottom w:val="single" w:sz="12" w:space="4" w:color="C9A227"/></w:pBdr>` (gold rule)

**b) Convert**:
```bash
pandoc proposal.html -f html -t docx --reference-doc=/tmp/ref_branded.docx -o out.docx
```

**c) Post-process `word/document.xml`** (lxml): for every `<w:tbl>`, take the first `<w:tr>` and for each `<w:tc>`:
- tcPr → `<w:shd w:val="clear" w:color="auto" w:fill="1F3864"/>`
- every run → ensure `<w:b/>` and `<w:color w:val="FFFFFF"/>`
Then give the table a gold top border + light inner borders (`tblBorders`: top C9A227 sz12, others BFBFBF sz4–6).

A complete working script (all three steps + verification) lived at `/opt/data/brand_docx.py` (Jul 2026) — reproduce with modifications.

## 4. Verify

```bash
unzip -o -q out.docx -d /tmp/dvf
python3 - <<'PY'
import re
xml = open('/tmp/dvf/word/document.xml', encoding='utf-8').read()
text = re.sub(r'<[^>]+>', ' ', xml); text = re.sub(r'\s+', ' ', text)
for c in ['ndr@draas.com', 'some-removed-section']:
    print(c, '->', 'FOUND' if c.lower() in text.lower() else 'absent')
print('tables:', xml.count('<w:tbl>'), '| images in media:', __import__('os').listdir('/tmp/dvf/word/media'))
PY
```

Pitfalls:
- **arm64 vs amd64 pandoc** — wrong arch = "cannot execute binary file: Exec format error" (silent, confusing).
- **The branding script is hardcoded to one project** (`/opt/data/brand_docx.py` pins the 15-acre HTML + output paths). For a new proposal, COPY the script and patch the `html =` / `out =` paths (e.g. `brand_bidadi_docx.py`) — don't rewrite it from scratch, and don't run it unchanged or it will overwrite the previous proposal's DOCX.
- Searching for literal `12% + 1.5%` fails when the HTML words it as "12% of realised revenue + 1.5% performance bonus" — grep with looser fragments.
- "DIN" substring false-positives: matches inside "Branding/funding/regarding" — always check context, not just presence.
- Re-run the full pipeline (convert + post-process) after every HTML edit; pandoc output is a snapshot, not live.
