# Ranka Udaya Marketing Collateral Inventory (Oct 2026)

Where the real estate marketing visuals live — verified 2026-10-08 while hunting for the
"blue-collar housing" (RG / Rental Guarantee) built-up render.

## What "blue-collar housing" means for Ranka Udaya

- NDR's term for the **RG (Rental Guarantee) model**: invest ₹1.2 Cr (1,200 sq.ft. plot +
  2,400 sq.ft. BUA), DRA builds **8 × 1-BHK rental homes**, guaranteed **₹60,000/month for
  5 years (+5% p.a.)**, RERA TNRERA/30/LO/0642/2026, HNTDA approved.
- Ask = "the brochure that shows the visual of the built-up" → the **RG insert ad** is the
  one that carries a real 3D render of the building block (beige facade, balconies,
  terracotta entrance wall, gated, golden hour). NOT the main project brochure.

## File inventory (ndr@draas.com / google-draas)

| File | Location | Renders? | Notes |
|---|---|---|---|
| `RankaUdaya_RG_Insert_6Oct.pdf` (47 MB) | Drive: `Ranka_Udaya_RG scheme_Creatives` (gsingh@draas.com) `1avbxSE0DQtFNFD3zas-1qvDbueNg8AI0` | ✅ full-page built-up render in top half | THE visual. Local copy: `/opt/data/rg_email_assets/rg_insert.pdf` |
| `Ranka_Udaya_RG_Ads_6Oct.pdf` (23 MB) | same folder `1ZHwXUpgqncRVcMqQ0uM53Nl6o0lDrnIG` | ❌ lifestyle couple photo, no render | 2-page ad set |
| `Ranka_Udaya_RG_video.mp4` (37 MB) | same folder `160v9a81LqgoCafxQ5sbhAsl7O4C9j5dP` | ✅ same block in motion | |
| `Ranka Udaya Brochure.pdf.pdf` (29.6 MB, 8pp) | Drive `Ranka Udaya` root; local `/opt/data/rg_email_assets/ranka_udaya_brochure.pdf` | ❌ plot brochure — master plan, lifestyle, no unit render | p5 = master plan, p7 = back cover |
| `Ranka_Udaya_Rental_Guarantee_Investment_Proposal_v1.2_Oct2026.pdf` (132 KB, 22pp) | `Ranka Udaya Marketing and Content` | ❌ text-only | |
| `Ranka_Udaya_RG_Sales_Proposal_2026-09-25` (65pp) | `Ranka Udaya Marketing and Content` (psingh@draas.com) | ❌ text-only | |
| `20260921_*` PNG kit (brochure cover, flyer, hoarding, Meta sizes) | `Ranka Udaya Marketing and Content` (ndr@draas.com) | kit only | print/digital masters 21-Sep-26 |
| `RankaUdaya_SiteOffice_Approved_Render_20260914.png` | same Marketing folder | site office only | |

Folder IDs (drive_search with `'<id>' in parents`):
- `Ranka Udaya` root: `1sdDX5htwSKF2SSe_re-jjYb-8SsFCk8Z`
- `Ranka Udaya Marketing and Content` (NDR): `1fRYtiqclzInfz2rVZHFNziou9KSEg77B`
- `Ranka Udaya Marketing and Content` (Prakash): `1mJDRREzrXhg5y7fGxcZrUpyMQjVGe6Y5`
- `Ranka_Udaya_RG scheme_Creatives` (Gowri): `1CM6cO7IWhqBP_DF8ZxPDCVJmihwfu_I0`

## Technique: scan a PDF for "does it carry a render?"

When asked "which brochure shows the built-up look", don't trust filenames/sizes — render and look:

```python
import fitz
doc = fitz.open(pdf_path)
for i, page in enumerate(doc):
    print(i, len(page.get_images(full=True)))   # 0 images = no render, text-only
    page.get_pixmap(dpi=60).save(f'/tmp/pg{i:02d}.png')
# then vision_analyze each PNG asking "is there a 3D render of a building?"
```

Pitfalls:
- `vision_analyze` on a render-heavy ad often returns only OCR of the text block; pass
  `also_describe_visually: true` to force a description of the imagery.
- A 29 MB brochure can still be render-free (plot brochure). A text-only proposal has
  `images=0` on every page — skip rendering entirely.
- Local cache `/opt/data/rg_email_assets/` mirrors most creatives used in the Oct-26
  HOSTIA draft campaigns — faster than Drive download for the same files.