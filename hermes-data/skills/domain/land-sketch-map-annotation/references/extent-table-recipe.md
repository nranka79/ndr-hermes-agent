# Extent Table Recipe — PyMuPDF

Ships with every Byadarahalli-style map annotation for Prakash (final approved format, 2026-08-17: label markers only on the map + this companion table). Two sections (SALE DEEDS / AGREEMENT TO SELL), per-section TOTAL, GRAND TOTAL.

## Data model

- Extents come from deeds/RTCs/partition deed (satvik due-diligence, Aug 2026). Source of truth per survey: `Extents_By_Survey` tab of the Satvik spreadsheet, cross-checked with RTCs.
- **1 Acre = 40 Guntas** — user-mandated arithmetic rule.
- Store as `(acres, guntas)` tuples; guntas can be fractional (41/17 = 0-05.08G, 180 = 2-0.5).
- Kharab: 221/2 = 3A 38G incl 0-38G kharab; 181 = 4A 00G incl 0-06G kharab. Grand net = gross − 1A 04G (44 guntas). Always state gross in the table, note kharab in REMARKS, give net as a note line below.
- P-series (45/P3, 45/P5, 45/P7) extents come from the map sketch's own labels (2-00, 4-00, 4-00) — they are pending-registration parcels per partition deed.
- 175/9 = 0-27G per partition deed/RTC (sale deed said 0-25 — deed was the error).

## Working code (pymupdf)

```python
import pymupdf
doc = pymupdf.open()
page = doc.new_page(width=595.28, height=842)  # A4 portrait

def text(s, x, y, size=10, color=(0,0,0), font="helv"):
    page.insert_text(pymupdf.Point(x, y), s, fontsize=size, fontname=font, color=color)

def to_g(t):  # (a,g) -> guntas
    return t[0]*40 + t[1]

def fmt_g(g):
    a = int(g // 40); gg = g - a*40
    gg = int(gg) if gg == int(gg) else round(gg, 2)
    return f"{a}A {gg}G"

RED = (0.85, 0.0, 0.05); BLUE = (0.0, 0.2, 0.95)

def draw_table(title, rows, total_text, color, y, col_w=(150, 90, 260)):
    # title bar
    page.draw_rect(pymupdf.Rect(40, y, 555, y+22), color=color, fill=color, width=0.5)
    text(title, 48, y+15, 11, (1,1,1)); y += 22
    # header
    page.draw_rect(pymupdf.Rect(40, y, 555, y+18), color=(0.2,0.2,0.2), fill=(0.9,0.9,0.9), width=0.5)
    text("SL NO", 48, y+13, 9); text("SURVEY NO.", 110, y+13, 9)
    text("EXTENT", 40+col_w[0]+col_w[1]-60, y+13, 9)
    text("REMARKS", 40+col_w[0]+col_w[1]+30, y+13, 9)
    y += 18
    for i, (lbl, ext, note) in enumerate(rows, 1):
        if i % 2 == 0:
            page.draw_rect(pymupdf.Rect(40, y, 555, y+15), fill=(0.96,0.96,0.96), width=0.3)
        text(str(i), 48, y+11, 9); text(lbl, 110, y+11, 9)
        text(ext, 40+col_w[0]+col_w[1]-60, y+11, 9, color)
        text(note, 40+col_w[0]+col_w[1]+30, y+11, 8, (0.35,0.35,0.35))
        y += 15
    page.draw_rect(pymupdf.Rect(40, y, 555, y+18), color=color, fill=color, width=0.5)
    text("TOTAL", 110, y+13, 10, (1,1,1))
    text(total_text, 40+col_w[0]+col_w[1]-60, y+13, 10, (1,1,1))
    return y + 18
```

- Layout notes: title bar red for sale deeds, blue for agreements (echoes the map legend). Row banding on even rows. `fontname="helv"` ONLY (helv-bold can throw in some builds). 22-row + 9-row tables fit one A4 portrait page.
- Deliver: PDF (archive) + PNG at dpi=200 (Telegram inline).

## Known-good totals (Byadarahalli, Aug 2026)

- SALE DEEDS (22 parcels): **24A 14.08G** gross (net of kharab 23A 10.08G)
- AGREEMENTS (9 parcels): **18A 13G**
- GRAND TOTAL: **42A 27.08G** gross (net 41A 23.08G)

## Pitfalls

- Don't list 41/11 (sale deed 0-20G) — it is not drawn on the Byadarahalli sketch, so it belongs in the spreadsheet totals but NOT the map table.
- Totals must be recomputed whenever a category expands (P-series added 10 acres to agreements: 45/P3 2-00 + 45/P5 4-00 + 45/P7 4-00 = 10A). The Aug totals above include them.
- If the user later asks to add this table to the Satvik spreadsheet, do NOT overwrite existing tabs — add a new tab (`add-new-tabs` rule from the Aug 14 session).