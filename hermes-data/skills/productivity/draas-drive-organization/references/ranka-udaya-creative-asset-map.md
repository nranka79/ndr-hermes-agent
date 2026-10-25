# Creative-asset location map — Ranka Udaya (verified 2026-10-08)

When NDR asks "find the brochure/render that shows the built-up / units" — the answer is a **Drive location + which PDF carries the visual**. Mapping below avoids re-rendering every candidate PDF.

## Folders

- **Ranka Udaya** root (ndr@draas.com): `1sdDX5htwSKF2SSe_re-jjYb-8SsFCk8Z`
- **Ranka Udaya Marketing and Content** (ndr): `1fRYtiqclzInfz2rVZHFNziou9KSEg77B` — master artwork (Sep-2026): Flyer A4, Brochure cover, site hoarding, Meta/Instagram set, place marker, site-office approved render.
- **Ranka Udaya Marketing and Content** (psingh@): `1mJDRREzrXhg5y7fGxcZrUpyMQjVGe6Y5` — channel-partner forms, rental-guarantee investment proposal.
- **Ranka_Udaya_RG scheme_Creatives** (gsingh@): `1CM6cO7IWhqBP_DF8ZxPDCVJmihwfu_I0` — **RG / blue-collar housing creatives** (the 8×1-BHK rental-guarantee scheme): video, insert, ads.
- **Lead Outreach Materials — Updated Oct 2026**: `1ZDYfaKEvt_8SS8wROwWM3hPwwIb2sAEp`.

## What shows the built-up (the answer to "show me what the units look like")

| Asset | Has the 3D built-up render? | Notes |
|---|---|---|
| `RankaUdaya_RG_Insert_6Oct.pdf` (in RG scheme_Creatives) | ✅ YES — hero is a golden-hour 3D render of the entrance/facade (beige block, balconies, terracotta gate wall, landscaping). This is the "blue-collar housing" visual. | Page contains the 21.2 Cr / 8×1-BHK / ₹60k/mo / 5-yr messaging. 47 MB. |
| `Ranka_Udaya_RG_Ads_6Oct.pdf` (2 pages, same folder) | ❌ NO — uses a lifestyle photo (elderly couple on balcony), not the render | Both pages carry the 21.2 Cr / 8×1-BHK copy but the visual is aspirational. |
| `Ranka_Udaya_RG_video.mp4` (same folder) | ✅ render in motion | 37 MB. |
| `Ranka Udaya Brochure.pdf.pdf` (root, 29.6 MB, 8 pages) | ❌ NO — plot/market brochure: cover, invest, numbers, location, master plan, About DRA, investment summary, back cover | No unit/built-up render. |
| `Ranka_Udaya_Rental_Guarantee_Investment_Proposal_v1.2_Oct2026.pdf` | ❌ text only (22 pp) | Financial/process deck, zero images. |
| `Ranka_Udaya_RG_Sales_Proposal` (65 pp) | ❌ text only | Internal sales-handling deck. |

## Bottom line for the render
The 3D built-up render lives ONLY in the **RG Insert PDF** (and RG video). Extract it with pymupdf on the top ~45% of page 1 (`clip=fitz.Rect(0,0,page.rect.width, page.rect.height*0.45)`) at 150 DPI to get a clean standalone render image. If NDR wants a render-only brochure, that crop is the source.

## Technique used for deciding PDF contents quickly
Render each candidate PDF page to PNG (`fitz.get_pixmap(dpi=60-80)`) and run `vision_analyze` with `also_describe_visually: true` — OCR alone cannot tell a render from a photo; the visual-analyze flag catches "3D architectural render" vs "staged lifestyle photograph".