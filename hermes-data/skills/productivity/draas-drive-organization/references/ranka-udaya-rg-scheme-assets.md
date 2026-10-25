# Ranka Udaya — RG (Rental Guarantee) scheme & marketing asset map (verified 08-Oct-2026)

## The "blue-collar housing" product = RG model

When NDR says "Ranka Udaya blue-collar housing scheme / 8 × 1-bedroom unit inventory / render of the built-up", he means the **RG (Rental Guarantee) scheme**:

- **8 × 1-BHK rental homes** on a 2,400 sq.ft. BUA (1,200 sq.ft. plot + 2,400 sq.ft. built-up), ₹1.2 Cr all-in, **₹60,000/month guaranteed rent, 5 years, +5% yearly** ("You own. DRA builds. You earn."). RERA TNRERA/30/LO/0642/2026, HNTDA approved. Site off Sarjapur–Attibele Rd, Chirchugunapalli, Hosur TN.
- Do NOT confuse with the plotted-development story (38 plots, ₹48L plot price) — that's the *other* brochure.

## Where the built-up render lives (the key answer)

- **✅ THE visual NDR wants = `RankaUdaya_RG_Insert_6Oct.pdf`** (47 MB): the top half is a golden-hour **3D render of the 8×1-BHK block** (beige facade, balconies, terracotta entrance wall, gated). Folder `Ranka_Udaya_RG scheme_Creatives` (`1CM6cO7IWhqBP_DF8ZxPDCVJmihwfu_I0`, owner gsingh@draas.com), file id `1avbxSE0DQtFNFD3zas-1qvDbueNg8AI0`. Same folder: `Ranka_Udaya_RG_Ads_6Oct.pdf` (2-page ad set — uses a lifestyle couple photo, NOT the render) and `Ranka_Udaya_RG_video.mp4` (block in motion).
- **The main `Ranka Udaya Brochure.pdf.pdf`** (29.6 MB, 8 pages, multiple copies on Drive) is the PLOT/market brochure — master plan + lifestyle shots, **no built-up render**. Do not hand it over when NDR asks for the unit visual.
- `Ranka_Udaya_Rental_Guarantee_Investment_Proposal_v1.2_Oct2026.pdf` (22 pp) and `Ranka_Udaya_RG_Sales_Proposal` (65 pp) are text-only.
- Local cached email assets (used for the HOSTIA draft campaign): `/opt/data/rg_email_assets/` — `rg_insert_email.jpg` (the render ad, md5 c5c66ca12f, cid rg_ad), `rg_insert.pdf`, `rg_ads.pdf`, `ranka_udaya_brochure.pdf`.

## Extraction recipe

```python
import fitz
doc = fitz.open('rg_insert.pdf')
pix = doc[0].get_pixmap(dpi=150, clip=fitz.Rect(0, 0, page.rect.width, page.rect.height*0.45))  # render hero
```
Vision-analyze with `also_describe_visually=True` — the text-only OCR path will NOT describe whether a render is present.