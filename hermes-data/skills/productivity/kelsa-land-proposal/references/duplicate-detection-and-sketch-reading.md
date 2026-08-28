# Duplicate detection & sketch reading — DRA Land Proposals (session 2026-08-25)

Three recipes from the Avati/Gobaragunte duplicate-detection pass. Read together with
the "Finding an existing proposal" section of the main SKILL.md.

## 1. Place-name map links (no coordinates in resolved URL)

Some `maps.app.goo.gl` links resolve to a Google Maps PLACE page, not a coordinate page:
`https://www.google.com/maps/place/Street+No.+1,+Avati,+Karnataka+562164/data=!4m2!...`
— no `@lat,lng`, no `q=lat,lng`, no `3d..!4d..` to extract.

**Fix: Nominatim `/search`** (NOT `/reverse` — you have no coords yet):

```bash
curl -s -G "https://nominatim.openstreetmap.org/search" -H "User-Agent: hermes-draas/1.0" \
  --data-urlencode "q=Street No. 1, Avati, 562164" \
  --data-urlencode "format=jsonv2" \
  --data-urlencode "limit=3"
# observed: 13.2974815 77.7242766 | Avati, Devanahalli taluku, Bengaluru North, Karnataka, 562164
```

Include the pincode in `q` when the place page shows one — it disambiguates.

## 2. Parcel-match tolerance: same village, ~1.4 km apart, SAME land

When comparing the new proposal's pin against an existing lead's `cf_location_google_maplink`:

- **Do NOT reject a match on pin distance alone.** Observed 2026-08-25: new Avati pin
  (13.2975,77.7243) vs Aamir lead #54040844 pin (13.2849,77.7235) — ~1.4 km apart in the
  same block — and it was the SAME parcel.
- Combine evidence sources instead: village names match, Sy Nos match (lead vs sketch),
  sketch filename matches, deal extent roughly matches.
- Real negative example still holding: Thylagere 10A (13.3216,77.6789) vs Nandi-backside
  (13.3297,77.6007) are genuinely different properties despite similar names — different
  villages + no Sy No overlap.

## 3. Same land re-proposed by a different broker — NDR's confirmed workflow

Pattern (recurring): land first brought by broker A (Aamir Khan), months later re-offered
by broker B (Rupa Gangadharapal). NDR suspects the match and asks "is this already in Kelsa?"

**Deliverable: an evidence bundle + a choice, not a silent duplicate:**

1. Search the pipeline: `cf_proposal_source:<broker A>` to enumerate their leads, plus
   size/location keyword variants.
2. When a candidate surfaces, pull `get_lead` for full detail (Sy Nos, villages, map link, sketch).
3. Present to NDR: villages + Sy Nos match, pin coordinates of both links + distance,
   sketch filename overlap, then the differences (extent, deal type, rate, proposer).
4. **Let NDR choose** update-existing vs create-new.

**Confirmed preference 2026-08-25:** NDR chose **add_note on the existing lead**
(#54040844, Aamir Khan's 20A Avati/Outright). The note carried:
- new proposer name + relationship/backer ("very well known to Mr. V.K. Reddy")
- owner's ask (₹7 Cr/acre) and NDR's counter (₹6 Cr/acre, immediate outright, 20A parcel)
- title flags (15A unregistered agreement; sketch total 27A10G vs offer 22A — reconcile before diligence)

Never create a duplicate record from memory; never merge records without asking.

## 4. Kannada-labeled survey sketches (AutoCAD PDFs)

Karnataka land sketches are usually AutoCAD-created PDFs with a KANNADA title block.
`pdfinfo` shows `Creator: AutoCAD 2016 ... (LMS Tech)`; the drawing is graphical, but
**`pdftotext` DOES extract the title-block text layer** (Kannada glyphs + numerals) —
try it BEFORE rasterizing/OCR:

- ಗ್ರಾಮ (graama) = village · ಹೋಬಳಿ (hobli) = hobli · ತಾಲೂಕು (taluk) = taluk
- ಸ.ನ. (sa.na.) = survey number · ಒಟ್ಟು (ottu) = total · ಎಕರೆ (ekare) = acres · ಗುಂಟೆ (gunte) = guntas

Worked example "AVATHI GOBARAGUNTE SKECTH 10-09-2024 FINAL-(1).pdf":
- Villages: ಅವತಿ (Avathi) + ಗೊಬ್ಬರಗುಂಟೆ (Gobaragunte), hobli ಕಸಬ (Kasaba), taluk ದೇವನಹಳ್ಳಿ (Devanahalli)
- Sy Nos: Avathi 93/1–14, 96/1–14; Gobaragunte 113, 114, 115, 116, 123, 124
- Total: 27 ಎಕರೆ 10 ಗುಂಟೆ (27A 10G)

These Sy Nos matched the existing Aamir lead's `cf_sy_nos` (93/1-17, 96/1-17, 113-116,
123, 124) almost exactly → strong same-parcel proof.

**Cross-check sketch total vs offer extent:** sketch says 27A 10G but the offer was
"22A = 7A registered + 15A unregistered". Extent mismatch = flag for reconciliation
before diligence (and the unregistered portion is itself a title-risk item).