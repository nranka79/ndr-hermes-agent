# TN "Petitioner Use" Land in Sanctioned Layouts (மனுதாரர் பயன்பாட்டிற்கு)

Verified 2026-09-14 on the Palm Paradise by Westbury layout (HNTDA planning permission
RCVT4YY2/2024/TCP, Sevaganapalli Panchayat final approval, TNRERA record TN/30/Layout/2758/2024).

## What the label means

On a Tamil Nadu sanctioned layout drawing you will see parcels labelled "PETITIONER USE 1",
"PETITIONER USE 2" (Tamil: மனுதாரர் பயன்பாட்டிற்கு — manudhaarar payanpattukku, "for the
petitioner's use"), often right at the layout entrance by the approach road.

- **"Petitioner"** = the person/entity who FILED the layout application (the "petition") with
  the planning authority (HNTDA / DTCP) under the Tamil Nadu Town & Country Planning Act 1971
  and TNCDBR 2019. It is the applicant, not a court petitioner — in the Palm Paradise case the
  petitioner is M/s Westbury Hospitality Pvt Ltd (letter address: 6, GPR Towers, Park Road,
  Bangalore-560051).
- **"Petitioner use land"** = land INSIDE the approved layout that the petitioner KEEPS for its
  own use. It is NOT part of the saleable plot inventory and NOT transferred to the local body.

## Where every layout category goes (the gifting discipline)

In a TN sanctioned layout, every square metre is assigned a destination, and the planning
permission letter (HNTDA/DTCP) is explicit about it:

| Category on plan | Destination | Mechanism |
|---|---|---|
| Saleable residential plots | sold to buyers | sale deeds |
| Roads + road splay | local body | GIFT DEED (mandatory) |
| OSR / park / open space | local body | GIFT DEED |
| Public purpose sites | local body | GIFT DEED |
| TANGEDCO site | electricity board | GIFT DEED |
| **Petitioner use** | **stays with petitioner** | **not sold, not gifted** |

The HNTDA letter literally states the applicant "was directed to handover the portion of land
earmarked for roads, public purposes meant for local body and TANGEDCO" and cites the gift
deeds filed (e.g. doc 3966/2024 & 3969/2024). The Ranipet DTCP letter uses identical standard
language — this is state-wide boilerplate, not a project quirk.

## Why petitioner-use parcels exist

- **Existing structures:** the land may carry a house/farmhouse/well that could not be plotted,
  so it is carved out of the plotted scheme and retained.
- **Developer reserve:** the developer keeps the parcel deliberately — commonly the road
  frontage at the entrance (sales office, own building, future commercial).
- **Landowner's JDA share:** under a JDA the landowner's retained share may be shown as
  petitioner-use parcels (or as named owner-use plots).

## Cross-check with the RERA inventory

TNRERA plot-split disclosures use their own vocabulary: e.g. Palm Paradise =
106 regular plots + 41 EWS plots + **2 owner-use plots**. The "owner-use" plots in the RERA
inventory are the same parcels the drawing labels "Petitioner Use 1/2". Always cross-check the
plan labels vs the RERA plot split before explaining to the user.

## Due-diligence implications

- Plot buyers get NO rights over petitioner-use land — it is not common area, not an amenity,
  not OSR. The residents' association does not hold it.
- It remains with the petitioner (and/or the landowner's share per JDA) and can be used or sold
  separately later.
- Entrance-frontage petitioner-use land = the developer kept the valuable road-facing parcel
  out of the plotted scheme — worth flagging to a buyer.
- **Verify the JDA**: does the landowner's retained share coincide with the petitioner-use
  parcels? If yes, clean ownership boundary. If not, confirm the petitioner's own claim — this
  is a classic future-dispute seam.

## OCR notes that made this readable

- Tesseract ships with only eng+osd. One-time setup for Tamil:
  `curl -L -o ~/.local/share/tessdata/tam.traineddata https://github.com/tesseract-ocr/tessdata/raw/main/tam.traineddata`
  then `export TESSDATA_PREFIX=~/.local/share/tessdata` (system tessdata dir not writable).
- HNTDA/local-body approval letters OCR cleanly with `tesseract -l eng+tam --psm 6` at
  130-200 dpi (English header + Tamil body).
- Large plan drawings: `pdftoppm -png -r 300`, then grid-tile 3x3/4x4 + legend-area crop,
  grayscale + contrast 2.0-2.5, OCR each tile with BOTH eng and tam.
- The drawing's title block (often page 1 of the approved plan) carries the land-use schedule
  (road area, layout area, local-body/public-purpose %, park %, TANGEDCO %) — read it before
  the geometry.