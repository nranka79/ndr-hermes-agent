# GBA / BBMP Officer Contact Directory (Karnataka gov contacts)

Verified 2026-08-24. Use when NDR needs phone/email of a GBA (Greater Bengaluru
Authority, the successor to BBMP), BBMP, or Karnataka gov officer — Special
Commissioners, JDTPs, Chief Commissioners, etc.

## Primary source: official GBA HOD contact list PDF (works, no login)

```
https://updates.bbmpgov.in/v1/api/file/417944643347-HODs%20Contact%20list_08-12-2025.pdf
```

- Download with `curl -skL` — the site's TLS cert is invalid (common for
  *.bbmpgov.in / *.karnataka.gov.in), so plain curl fails with exit 60; `-k`
  fixes it. Jina reader also fails on gba.karnataka.gov.in for the same cert
  reason.
- The PDF is a **text layer** PDF — `pdftotext` extracts everything. No OCR needed.
- Layout quirk: pdftotext output interleaves email/contact columns in a
  non-obvious order. Map by SL.NO: officers 1–5 are Chief Commissioner then the
  four Special Commissioners; the contact numbers at the end of the file are in
  the same order (1 = Chief Commissioner 94480 67345, 2 = Special Commissioner
  (Revenue & IT) 94481 94915, etc.). Emails column: comm@bbmp.gov.in,
  spcomm-rev@bbmp.gov.in, Bbmpsplcomhealth@gmail.com, scfinbbmp@gmail.com,
  scfeccm2024@gmail.com in SL order 1–5.
- Keep a local copy under `/data/hermes/projects/` if the gov server is down
  later; re-fetch yearly (list is "As On Date"-stamped, e.g. 08-12-2025).

## Verified entry — Munish Moudgil

| Field | Value |
|---|---|
| Name | **Munish Moudgil, IAS** (NOT "Mudgal"/"Muthgal" — M-O-U-D-G-I-L; voice dictation frequently garbles it) |
| Designation | Special Commissioner (Revenue & IT), Greater Bengaluru Authority (GBA) |
| Mobile | +91 94481 94915 |
| Email | spcomm-rev@bbmp.gov.in |
| Batch / bg | 1998-batch Karnataka cadre IAS; IIT Bombay (Electrical, 1991–96); earlier Commissioner of Survey Settlement & Land Records (till Feb 2025), Special Commissioner (Revenue) BBMP since Oct 2023, DC Ramanagara 2008–09 |
| Also | LinkedIn "Munish Moudgil – Govt of Karnataka" (Special Commissioner (Revenue & IT), GBA); note Dec 2025 news: GBA Employees Association called a strike against him (TV9) — relevant context if NDR deals with him |

RocketReach independently lists his numbers as +91 80 2221 XXXX, +91 94480 8XXXX,
+91 94481 9XXXX — the 94481 9XXXX mask matches the official 94481 94915.
Any "080-2727 3777" / Ramanagara-era contacts floating around are from his
2008–09 DC posting — ignore.

## Other key GBA officers (same list, 08-12-2025)

- **Chief Commissioner / Administrator to 5 City Corporations:** Sri Maheshwar Rao M, IAS — comm@bbmp.gov.in — 94480 67345
- **Special Commissioner (Health & Education, Elections):** Sri Suralkar Vikas Kishor, IAS — Bbmpsplcomhealth@gmail.com — 94485 49197
- **Special Commissioner (Admin, Finance) & CFO:** Dr. Harish Kumar K, IAS — scfinbbmp@gmail.com — 94806 83000
- **Special Commissioner (FECC, Disaster Mgmt, PR & Coordination):** Sri Ramachandran, IAS — scfeccm2024@gmail.com — 77605 04651

## Lookup recipe (when the PDF doesn't have the person)

1. Tavily/Apify are NOT used for this (NDR standing directive) — Go direct:
   Google News RSS first (`news.google.com/rss/search?q=%22Name%22+BBMP`) for
   recent postings; Wikipedia API; then **DDG-via-Jina**
   (`curl https://r.jina.ai/https://html.duckduckgo.com/html/?q=...`) which
   WORKS from the VPS datacenter IP (verified 2026-08-24; plain DDG and
   google.com are blocked).
2. The DDG hit "GBA HOD Contact list" PDF at updates.bbmpgov.in is the
   authoritative answer — fetch, pdftotext, map columns.
3. Name spellings: KAS/IAS names in news are often mangled by voice dictation
   ("Mudgal" vs "Moudgil"). Fix the spelling from the official list BEFORE
   reporting back.
4. Cross-check mobile against RocketReach's masked pattern (first 5 digits)
   — confirms which of several listed numbers is the live line.
5. Old posting-era contacts (e.g. Ramanagara DC profile on bengalurusouth.nic.in)
   are stale — flag as such, don't deliver as current.