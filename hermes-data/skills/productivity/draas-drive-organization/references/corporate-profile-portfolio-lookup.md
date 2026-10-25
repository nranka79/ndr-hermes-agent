# Locating the latest corporate profile / portfolio PDF (and verifying it)

Trigger: NDR asks for "the latest corporate profile", "company/DRA profile", "the portfolio",
the large PDF that covers both Bangalore and Chennai projects — "it's in drive or email, we've
shared it with people".

## Core search lessons

1. **NDR uses "profile" and "portfolio" interchangeably.** The genuinely latest file on
   google-draas is named **DRA Portfolio Updated.pdf** — it contains NO "profile" token.
   Search `name contains 'profile'` AND `name contains 'portfolio'`, both with a
   `modifiedTime > <12mo cutoff>` window. Also try `'credentials'`, `'brand'`, `'brochure'`
   for related but distinct collateral.
2. **"Made in the last 12 months" ≈ modifiedTime, not createdTime** — old files get re-saved
   with new modifiedTime (DRA Profile-1.pdf, created 2019, modified 2026-02-02). Check BOTH;
   a file with a 2026 modifiedTime can still be stale content (vintage 2019 project lists).
3. **fullText combos confirm content, they don't find marketing PDFs.** Queries like
   `fullText contains 'Ranka Oasis' and fullText contains 'Northstar' and mimeType='application/pdf'`
   surface project legal/technical PDFs (JDAs, NOCs, ECs), not the corporate deck. Use them only
   to rule out/confirm candidates once you have IDs.
4. **Large image-heavy PDFs have near-zero text layer** (pdftotext returns a few hundred chars
   or nothing). Do NOT conclude "no Northstar/Oasis/Chennai" from a short text dump — the pages
   are raster. Verify with the OCR keyword sweep below.
5. Check Gmail attachment names too (`filename:pdf profile newer_than:13m`, subject: profile)
   — the file may have been emailed rather than filed. For this corpus it was on Drive under
   the 'portfolio' name.

## Known DRA corporate-deck corpus (google-draas, as of 2026-09-02)

| File | Size/pages | Modified | ID | Coverage |
|---|---|---|---|---|
| **DRA Portfolio Updated.pdf** ⭐ LATEST | 131.2 MB / 65pp | 2026-03-21 | `1reK--vnC_hht_fiIUsFNOnl9XGDlQWkH` | North Star (Yelahanka), Oasis (Sarjapur–Hosur, Sevaganapalli), Udaya (Chichuraganapalli), Amber (Whitefield), Serenity; Chennai: Inara (Navallur OMR), Skylantis (OMR), Harmony (Navalur), Truliv, Tuxedo (Velachery), Pristine Pavilion |
| DRA Portfolio Sep 25.pdf | 114.4 MB / 52pp | 2025-09-09 | `1d8AVewMwO1gdftMQhQSLGsIkFRERA1D7` | Previous version (same projects minus some) |
| DRA Profile-1.pdf | 2.3 MB | 2026-02-02 (content ~2019) | `1wjcW0A4rHCRHNzvz4jgR2QDn96GXjpLS` | OLD — North Star + Chennai (Tuxedo, Pristine, 90 Degrees, Ascot, Navallur) but NO Oasis/Udaya; financials vintage 2017-18 |
| 20250627 DRA Corporate Profile Content | Google Doc | 2025-12-23 | `152md41BWggNmo6baaLOh_eL8uVIzmxJG9lg4z6rG23A` | DRA Homes brand content source (North Star, no Oasis) — text version of a profile, not the deck |
| DRA corporate profile.pdf | 55.5 MB | 2025-02-11 (created 2024-03-16) | `1JZJbnCbs8850g9wLdPuBTBplqtgSiLOm` | Older scanned deck |
| DRA BLR Corporate Profile V2.pdf | 52.9 MB | 2023-09-26 | `1DdLWlBYEy2_fE5d-HBslzaV3oFLdkD3M` | Old |

When in doubt between two candidates, the tie-breaker NDR uses: "has Ranka Northstar AND Ranka
Oasis AND (maybe) Udaya under Bangalore projects AND the Chennai projects". DRA Portfolio
Updated.pdf is the only one that satisfies all of that.

## OCR keyword sweep (image-heavy PDF verification)

Worked pattern for "does this deck contain project X / Chennai section":
render all pages at 90 dpi → tesseract each → report per-page keyword hits.

**Pitfall — pdftoppm output naming:** rendering per-page with `-f N -l N` writes a file whose
exact name you should NOT assume (not `pgNNN.png` in all pdftoppm versions). Reliable pattern:
render the WHOLE doc in one call (`pdftoppm -r 90 -png <pdf> <outdir>/pg`) then
`sorted(glob(f"{outdir}/pg-*.png"))` — default output is `<prefix>-<NN>.png`. A broken first
attempt here crashed on `os.remove` of a guessed filename before a single OCR ran.

Run via `scripts/ocr-keyword-sweep.py` (re-runnable, ~2–4 min for 65pp at 90 dpi):

```bash
/opt/hermes/.venv/bin/python3 /data/hermes/skills/productivity/draas-drive-organization/scripts/ocr-keyword-sweep.py <file.pdf> <outdir> [kw1 kw2 ...]
```

Default keywords = Bangalore/Chennai project names (northstar, oasis, udaya, amber, inara,
skylantis, harmony, tuxedo, pristine, truliv, omr, velachery, chennai, bangalore…). 90 dpi is
enough for marketing headline/body text; only go higher for tiny print.

## Time-limited share workflow (companion)

Once the file is found, NDR's standard circulate-and-restrict flow: grant `anyone` reader +
named editor (Roshini: rnr@draas.com) → WhatsApp deep-link to the circulator telling them they
have editor access and to share the Drive LINK (not download-forward) → schedule the
restriction row (+15 days) in the Next Agent Action sheet, NOT a fresh cron (see
next-agent-action skill, item 6). Drive `permissions().create` for `anyone`/user works even
when the file owner is another draas account (observed owner sales1.blr@draas.com); always
verify with `permissions().list` afterwards.
