#!/usr/bin/env python3
"""Parse TN REGINET EC PDFs into structured transactions.

Usage: python3 parse_tn_ec.py EC_158.pdf [EC_166.pdf ...]
Output: JSON per input file on stdout (or --out out.json for combined).

Method: pdftotext -bbox (correct Tamil text + x-coordinates). pdfplumber
garbles the Tamil font; pdftotext -layout columns shift between the old
multi-line and compact single-line entry formats. -bbox is the reliable one.

Column zones (page points, landscape A4 ~842x595):
  x<100 Sr No | 100-215 Doc No/Year | 200-310 Dates | 305-412 Nature |
  410-532 Executants (From) | 532-650 Claimants (To) | 650+ Vol/Page |
  Survey lists in schedule blocks at x0>=414.

PITFALLS ENCODED HERE (all hit in real Sevaganapalli parsing, 2026-08):
  * Page tags have NO number attr — count '<page ' occurrences.
  * HARD STOP survey scan at எல்லை விபரங்கள் / Boundary Details — boundary
    text lists neighbor plots (176/285, 176/2B4B, 66/2B2, 165, 159, 158/1C8)
    that are NOT transaction surveys.
  * Modern ('Survey No-Extent') and old ('Survey No./புல எண்') formats need
    separate continuation logic; old-format continuation MUST be gated on
    `not modern` or extent values (50, 69, 19 from "50.0 CENTS") leak in.
  * Do NOT `continue` past the SURVEY NUMBER remark rule (that silently
    dropped 177/1A1A in EC158/9188/2025).
  * Do NOT require "- XX.X CENTS" on the same line as the survey token —
    extent values wrap across bbox lines.
  * Final noise filter drops single-digit / zero-pad / year-like tokens only;
    2-digit standalone values (39, 96, 104, 111, 137, 182, 183-185) are
    valid whole surveys.
"""
import re, subprocess, json, sys

DATE_RE = re.compile(r'\d{1,2}-[A-Za-z]{3}-\d{4}')
DOCNO_RE = re.compile(r'^(\d{1,5})/(\d{4})$')
SR_RE = re.compile(r'^(\d{1,3})$')
SURVEY_EXCL = {'CENTS', 'ACRE'}
# Keywords that mark prose/boundary text in the RIGHT zone of a schedule line
RIGHT_PROSE = ('EAST', 'WEST', 'NORTH', 'SOUTH', 'Road', 'Proposal', 'Sites',
               'Mtr', 'ComesUnder', 'Land in', 'மேற்கு', 'கிழக்கு', 'வடக்கு',
               'தெற்கு', 'Park', 'Boundary', 'Survey No', 'Schedule',
               'Remarks', 'Consideration')


def get_words(pdf_path):
    """pdftotext -bbox -> list of (page, x0, y0, x1, y1, text).
    CRITICAL: page tag is '<page width=...>' with NO number attribute —
    count '<page ' occurrences to track page index. Ignoring pages merges
    words from all pages at the same y into one giant line."""
    out = subprocess.run(['pdftotext', '-bbox', pdf_path, '-'],
                         capture_output=True, text=True).stdout
    words = []
    token_re = re.compile(
        r'<page |<word xMin="([\d.]+)" yMin="([\d.]+)" '
        r'xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>')
    cur_page = 1
    for tm in token_re.finditer(out):
        if tm.group(0).startswith('<page'):
            cur_page += 1
        else:
            words.append((cur_page, float(tm.group(1)), float(tm.group(2)),
                          float(tm.group(3)), float(tm.group(4)), tm.group(5)))
    return words


def group_lines(words):
    """Group words into lines by (page, y0 bucket ~4.5pt).
    A 2.5pt bucket is too fine: Sr No and the first party name on the same
    visual row sit on slightly different baselines and split into two lines."""
    buckets = {}
    for w in words:
        key = (w[0], round(w[2] / 4.5))
        buckets.setdefault(key, []).append(w)
    return [sorted(buckets[k], key=lambda x: x[1]) for k in sorted(buckets)]


def line_text(line):
    return ' '.join(w[5] for w in line)


def zone_text(line, lo, hi):
    return ' '.join(w[5] for w in line if lo <= w[1] < hi).strip()


def split_names(parts):
    joined = re.sub(r'\s+', ' ', ' '.join(parts)).strip()
    joined = re.split(
        r'\s+(?:PR Number|முந்தைய ஆவண எண்|Market Value|Consideration Value)\b',
        joined)[0].strip()
    if not joined:
        return []
    items = re.findall(r'(\d+)\.\s*([^,]+?)(?=\s*\d+\.\s|\s*$)', joined)
    out = []
    for num, name in items:
        name = name.strip()
        if name and name not in ('-',) and not re.fullmatch(r'\d{1,4}', name):
            name = re.sub(r'\s+\d{1,3}$', '', name).strip()  # page-number bleed
            out.append((int(num), name))
    if not items:
        joined = re.sub(r'\s+\d{1,4}$', '', joined).strip()
        return [(None, joined)] if joined else []
    return out


def parse_entry_header(lines, start=0):
    doc_no = None
    dates = []
    nature_parts, exec_parts, claim_parts, vol_parts = [], [], [], []
    for _, ln in lines[start:]:
        txt = line_text(ln)
        if any(k in txt for k in ('Consideration Value', 'Market Value',
                                  'PR Number')):
            break
        for w in ln:
            if 100 <= w[1] < 215:
                m = DOCNO_RE.match(w[5])
                if m and doc_no is None:
                    doc_no = f"{m.group(1)}/{m.group(2)}"
        for w in ln:
            if DATE_RE.fullmatch(w[5]):
                dates.append(w[5])
        nat = [w[5] for w in ln if 305 <= w[1] < 412
               and not SR_RE.match(w[5]) and w[5] != '-']
        if nat:
            nature_parts.append(' '.join(nat))
        ex = zone_text(ln, 410, 532)
        if ex:
            exec_parts.append(ex)
        cl = zone_text(ln, 532, 650)
        if cl:
            claim_parts.append(cl)
        v = zone_text(ln, 650, 1000)
        if v:
            vol_parts.append(v)
    nature = re.sub(r'\s+', ' ', ' '.join(nature_parts)).strip()
    nature = re.sub(r'(PR Number|முந்தைய ஆவண|Market Value|Consideration Value).*$',
                    '', nature).strip()
    return {'doc_no': doc_no, 'dates': dates, 'nature': nature,
            'executants': split_names(exec_parts),
            'claimants': split_names(claim_parts),
            'vol': ' '.join(vol_parts).strip()}


def parse_consideration(lines, start=0):
    cons = mv = pr = None
    for i in range(start, len(lines)):
        if 'Consideration Value' not in line_text(lines[i][1]):
            continue
        for j in range(i + 1, min(i + 4, len(lines))):
            l2 = lines[j][1]
            t2 = line_text(l2)
            if 'Schedule' in t2 and 'Details' in t2:
                break
            if any(k in t2 for k in ('Consideration Value', 'கைமாற்றுத்',
                                     'Market Value', 'சந்தை')):
                continue
            cv = zone_text(l2, 100, 310)
            if cv and not re.search(r'PR Number|முந்தைய|ஆவண|Consideration|'
                                    r'Value|கைமாற்று|Schedule', cv) and cons is None:
                cons = cv
            mv2 = zone_text(l2, 310, 530)
            if mv2 and not re.search(r'PR Number|முந்தைய|ஆவண|Market|Value|'
                                     r'சந்தை|Consideration|கைமாற்று|Schedule',
                                     mv2) and mv is None:
                mv = mv2
            pr2 = zone_text(l2, 530, 1000)
            if pr2 and not re.search(r'PR|Number|முந்தைய|ஆவண|Schedule',
                                     pr2) and pr is None:
                pr = pr2
        break
    return cons, mv, pr


def parse_schedules(lines, start=0):
    """Survey numbers from schedule blocks.

    Rules (all earned the hard way):
      1. HARD STOP at the boundary description (எல்லை / Boundary) — it lists
         NEIGHBOR plots, not transaction surveys.
      2. Modern 'Survey No-Extent' lines: scan ALL NN/NNX tokens; extent
         values wrap across bbox lines so never require '- XX.X CENTS' on
         the same line.
      3. Modern continuation lines: LEFT zone may carry labels (Property
         Type / Village & Street); evaluate the RIGHT zone only.
      4. Old-format continuation ('Survey No.' label): gated `not modern`;
         accept pure survey lists in the right zone; keep standalone whole
         surveys (104, 111, 39) that sit beside slashed tokens.
      5. NEVER `continue` past the SURVEY NUMBER remark rule below.
    """
    surveys = []
    in_sched = False
    modern = False
    for i in range(start, len(lines)):
        txt = line_text(lines[i][1])
        if 'Schedule' in txt and 'Details' in txt:
            in_sched = True
        if 'Number of Entries' in txt:
            break
        if not in_sched:
            continue
        # HARD STOP: boundary description = neighbor-plot references.
        if 'எல்லை' in txt or 'Boundary' in txt:
            break
        # Modern: 'Survey No-Extent/புல எண்-விஸ்தீர்ணம்: ...'
        if 'Survey No-Extent' in txt or ('Survey' in txt and 'புல' in txt
                                         and 'எண்-விஸ்தீர்ணம்' in txt):
            modern = True
            seg = zone_text(lines[i][1], 400, 1000)
            for tok in re.findall(r'\d{1,4}/\d{1,4}[A-Z0-9]*', seg):
                surveys.append(tok)
        # Modern continuation: pure survey/extent list in RIGHT zone only.
        if modern and in_sched:
            right = zone_text(lines[i][1], 400, 1000)
            if right and not any(k in right for k in RIGHT_PROSE):
                toks = re.findall(r'\d{1,4}/\d{1,4}[A-Z0-9]*', right)
                if toks:
                    stripped = re.sub(r'\d{1,4}/\d{1,4}[A-Z0-9]*', '', right)
                    stripped = re.sub(r'[\d.,;\s-]+', '', stripped)
                    stripped = re.sub(r'(CENTS|ACRE|ACRES|SQUARE|FEET|HECT|HEC)',
                                      '', stripped, flags=re.I)
                    if not stripped.strip():
                        for tok in toks:
                            if tok not in SURVEY_EXCL and len(tok) <= 10:
                                surveys.append(tok)
        # Old format: match 'Survey No.' only — Tamil label 'புல எண்' is
        # often on a separate line.
        if ('Survey No.' in txt and 'Extent' not in txt
                and 'Survey No-Extent' not in txt):
            seg = zone_text(lines[i][1], 400, 1000)
            if ':' in seg:
                seg = seg.split(':', 1)[1]
            for tok in re.findall(r'\d{1,4}(?:/\d{1,4}[A-Z0-9]*)?[A-Z]?', seg):
                if tok and tok not in SURVEY_EXCL and len(tok) <= 10 \
                        and (len(tok) <= 3 or '/' in tok):
                    surveys.append(tok)
        # Old-format continuation — GATED on not modern, else extent values
        # (50, 69, 19 from "50.0 CENTS") leak as fake standalone surveys.
        if in_sched and not modern:
            right = zone_text(lines[i][1], 400, 1000)
            if right and not any(k in right for k in
                    ('Village', 'Property', 'Schedule', 'Remarks', 'Survey No',
                     'Consideration', 'SURVEY NUMBER', 'Extent', 'எல்லை',
                     'EAST', 'WEST', 'NORTH', 'SOUTH', 'Road', 'Proposal',
                     'Sites', 'Mtr', 'ComesUnder', 'Land in', 'மேற்கு',
                     'கிழக்கு', 'வடக்கு', 'தெற்கு', 'Park', 'Boundary')):
                toks = re.findall(r'\d{1,4}(?:/\d{1,4}[A-Z0-9]*)?[A-Z]?', right)
                slash_toks = [t for t in toks if '/' in t]
                if slash_toks:
                    rest = re.sub(r'[\d/,.:;\sA-Za-z-]+', '', right)
                    if not rest:  # purely alphanumeric/digit survey list
                        # keep slashed tokens AND standalone whole surveys on
                        # the same line (e.g. '104, 111, 39' beside 102/9...)
                        for tok in toks:
                            if tok not in SURVEY_EXCL and len(tok) <= 10:
                                surveys.append(tok)
        # SURVEY NUMBER remarks (modern gift/settlement deeds). Keep LAST so
        # no earlier rule's continue/break can skip it.
        if 'SURVEY NUMBER' in txt:
            for tok in re.findall(
                    r'SURVEY NUMBER\s*:\s*(\d{1,4}/\d{1,4}[A-Z0-9]*)', txt):
                surveys.append(tok)
    seen, out = set(), []
    for s in surveys:
        # drop single-digit page artifacts, zero padding, and year-like
        # doc-number tokens (e.g. '1/2025' from ROC numbers). 2-digit
        # standalone values (39, 96, 104, 111...) ARE valid whole surveys.
        if re.fullmatch(r'\d', s) or re.fullmatch(r'0{2,4}', s) \
                or re.fullmatch(r'\d{1,4}/\d{4}', s):
            continue
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def parse_ec(pdf_path, ec_label=None):
    lines = group_lines(get_words(pdf_path))
    candidates = []
    for i, ln in enumerate(lines):
        for w in ln:
            if w[1] < 100 and SR_RE.match(w[5]):
                candidates.append((i, int(w[5])))
                break
    # Real entry start: block to next candidate has doc-no word AND
    # 'Consideration Value'.
    real_starts = []
    for ci, (i, sr) in enumerate(candidates):
        j = candidates[ci + 1][0] if ci + 1 < len(candidates) else len(lines)
        blk = lines[i:j]
        blk_txt = ' '.join(line_text(l) for l in blk)
        has_docno = any(100 <= w[1] < 215 and DOCNO_RE.match(w[5])
                        for l in blk for w in l)
        if has_docno and 'Consideration Value' in blk_txt:
            real_starts.append((i, sr))
    seen, filtered = set(), []
    for i, sr in real_starts:
        if sr not in seen:
            seen.add(sr)
            filtered.append((i, sr))
    real_starts = filtered

    recs = []
    for ci, (i, sr) in enumerate(real_starts):
        j = real_starts[ci + 1][0] if ci + 1 < len(real_starts) else len(lines)
        start = i
        # Page-break quirk: first executant can sit on the line ABOVE the
        # Sr marker; prepend it if it has a standalone 'N.' marker at 410-650.
        if i > 0 and any(w[1] >= 410 and w[1] <= 650
                         and re.fullmatch(r'\d+\.', w[5]) for w in lines[i - 1]):
            start = i - 1
        blk = [(idx, ln) for idx, ln in enumerate(lines[start:j], start=start)]
        hdr = parse_entry_header(blk, 0)
        if not hdr['doc_no']:
            continue
        cons, mv, pr = parse_consideration(blk, 0)
        recs.append({
            'ec': ec_label,
            'sr': sr,
            'doc_no': hdr['doc_no'],
            'dates': hdr['dates'],
            'nature': hdr['nature'],
            'executants': hdr['executants'],
            'claimants': hdr['claimants'],
            'consideration': cons,
            'market_value': mv,
            'pr_number': pr,
            'surveys': parse_schedules(blk, 0),
            'vol': hdr['vol'],
        })
    return recs


def master_union(combined):
    """doc_no -> {ecs, surveys-union, entry}. Use for the Master tab: the
    same doc's survey list can differ slightly across ECs due to page-break
    truncation, so union across ECs (e.g. 9188/2025 = 19 surveys from 5 ECs
    where per-EC lists were 11-18)."""
    master = {}
    for label, recs in combined.items():
        for e in recs:
            m = master.setdefault(e['doc_no'],
                                  {'ecs': set(), 'surveys': [], 'seen': set(),
                                   'entry': e})
            m['ecs'].add(label)
            for s in e['surveys']:
                if s not in m['seen']:
                    m['seen'].add(s)
                    m['surveys'].append(s)
    return master


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('pdfs', nargs='+')
    ap.add_argument('--out', default=None)
    args = ap.parse_args()
    combined = {}
    for p in args.pdfs:
        label = re.search(r'EC[_ ]?(\d+)', p)
        label = label.group(1) if label else p
        recs = parse_ec(p, label)
        combined[label] = recs
        print(f'{label}: {len(recs)} entries', file=sys.stderr)
    if args.out:
        with open(args.out, 'w', encoding='utf-8') as f:
            json.dump(combined, f, ensure_ascii=False, indent=1)
    else:
        print(json.dumps(combined, ensure_ascii=False, indent=1))
