# Ranka99 / DR Villa (R99 / L&T South City) — Drive Folder Map & File Inventory

## Property aliases (NDR uses interchangeably)
- **DR Villa** / DRVLA / Dinesh Ranka Villa / "Dineshwaka Villa" — a ~1 acre 6 guntas villa property, a villa built within the larger **L&T South City** ("South City") development by **Dinesh Ranka** (the "R99" / "Ranka99" project).
- Per NDR, property relates to **Survey No 96 & 97** (verify — user said "96 and 97 only I think").
- The villa itself is the DR Villa; the larger project = Ranka99 / R99 / L&T South City. DKA = architect (D&KA). From HardDrive = older legal set.

## Folder chain (all under My Drive → Parked Properties, owner ndr@draas.com)

```
My Drive
└── Parked Properties (1_J-gi0ZsaitGCZVbDAUWyboW5Ak12qiX)
    └── R99 (0B1Oc8cSaJXPGM1ZwaENYN2Z1YkE)                     — 15 files: IRR calc, BDA asks, R99 revised plan, road/FAR
        ├── Floor Plans PDF (0B1Oc8cSaJXPGdTAtdEFjR3ZjNTg)     — 28 files
        ├── Survey Of LTSouth City 7OCT08 (13n4zL0_GsH4mug2kliPpqNFfIfAK8N8w) — 6: DR Villa Approved Plan.pdf, DR Villa Plans.pdf, DR Villa Full Plan Scan.jpg, DINESH-RANKA.dwg
        └── Ranka99 (1_JeqyxYTNpzM2S5W16y5RiZAYl9an6Jk)        — 38: DR VILLA ORIGINAL TAX PAID RECEIPT, BBMP Khata, DR Villa RnD of Land Rates
            ├── DR Villa Drawings (10dLbl0jTCyL67IAyShJcON9YP72-q0KI)
            │   └── DR Villa Drawings (1yxHrLbl5yhAt2KNOikBTNgL6Jt-TTCSR) — 16 DWGs: SITEPLAN, SOUTH CITY FINAL, L&T COMB, 007-A sheets
            ├── SouthCity Legal (1wF0d_ebM2ZpaOmKFgxcSS9dWuCsYWFYV) — 28: OCs, Dev Agreement 1995, Relinquishment Deed 2006, WP 15590/2015
            ├── DKA (1VjtbVJMFD-GAYvDW_DrioWaYrYAr-pcV)
            │   ├── Ranka South City Floor Plans 28DEC11 (1yddZuVTqvLfdCzULqjk96BCrVPiar9oB) — 10
            │   ├── Ranka South City Sanction Drawings 25APR11 (1_fcrp2EBA6fMe8MOS3OxkyAjsUUl-pVE) — 2
            │   └── Ranka Zeva Final Plans (14BVQIVmpmVWKVnDPwhpgNZCuTljUEaqi) — 36
            ├── Survey Of LTSouth City 7OCT08 (1G8aUNzwGbnJQTG2tsZJCBDC1qpdWTY4w) — 3
            ├── Elevation & Visuals (1AsKiKfLGC5021JAPryUrUwZVxJ2lBdun) — 5
            └── PUSH Deliverables (1oFQfU-i-fHVyIy3_chyZVpeFbQXqC4bR) — MARKETING WEB ASSETS: skip unless user asks
                ├── Content Delivered 24DEC13 (1iUy6fQ4IrfEp04JWTSfELeRmfaPsUA-g) — 18 subdirs, fonts/jpg/links
                ├── Content Delivered 6FEB14 (1355uWBjLEkCixXftR08jR2bWUAcIetpx)
                └── R99 Content Redelivered 1DEC14 (1oKEwtLog1z5IjI-_wMtuhkoddiITrI4F)
    └── R99 > Ranka99 Legal (0B1Oc8cSaJXPGeXdNWWc4dXVhdVU)     — 27: DR Villa Re-Sanction Exec Summary, One-Pager, opinions (Uday Holla, JSA), WP 54408-2015, boundary drawings, R99 Summary for Girish Rao
        └── From HardDrive (1hO92TtODBT0gQWmXoebEapBtWm7JFLb4) — 35: NOCs (HAL, AAI, DSK, Fire, BWSSB, KEB), khata, HC orders, DKA invoices
            └── SouthCity Legal (192r_WkRfpAP0zgxiccdeJ2bZtQZKO_Nq) — 9: fire NOCs, OCs, Modified DP 1998/2005
```

Related but OUTSIDE Parked Properties:
- **My Drive root** — strand-alone DR Villa docs: `19920915 Sale Deed DR Villa.pdf`, `20001216 DR Villa Rectification Deed.pdf`, `20251025 Ltr NDR2AxisBank for DR Villa Documents`, `DR Villa e-Khata Translated English.pdf`, `DRA VILLA DRAFT e-khatha.pdf`, `DRA VILLA KHATHA ENDEX original copy.pdf` (plus 2–3 duplicate copies).
- **My Drive > L&T South City** (1fz3Ju7UCPYFEtZT8qSJvesLg81f-G-EK, owner architect.blr@draas.com) — L&T SOUTH CITY Villa.dwg / .pdf.
- **My Drive > BusDev** (16P6CTecntuUompI9HmQ8RT9vCJIxftI2) — DR Mandate DR2Ravi DR Villa 17DEC18, DR Villa DR2Ravi Authorization for Marketing 15DEC18 (only 2 DR-Villa files; the folder is a big general bucket — don't grant folder-wide access for DR Villa).

## File-inventory → HTML table technique (NDR's format preference, 2026-09-10)
When NDR asks "list every file with link + exact folder + full folder chain" (usually to then pick which items to share with a viewer like VKDAS for 90 days):
1. **Walk the surgical subtree only** (R99 + Ranka99 + Ranka99 Legal + From HardDrive + L&T South City + BusDev named hits + root named hits). Do NOT walk full Parked Properties/BusDev — 1,300–1,500 unrelated files.
2. **Exclude PUSH Deliverables** marketing branches (fonts/jpg/links/Work subfolders) — ~550 files of web assets; they're marketing, not legal/planning docs.
3. Build **full folder chain per file** by walking `parents` upward to My Drive root (`0AFOc8cSaJXPGUk9PVA`); PREFIX "My Drive".
4. Generate a **single self-contained HTML table** (sticky header, chain-group rows, open-links, pale-yellow highlight rows whose name matches DR Villa|R99|Ranka99|South.?City|Dinesh). 271 files / 19 chain groups on 10-Sep.
5. Deliver: (a) Drive upload with `YYYYMMDD_Entity_Description.html` name, (b) Telegram copy — the gateway drops `.html`, so send the same bytes as `*.html.txt` with `MEDIA:...` so NDR can open it; never claim either as a real send.
6. Ask which rows/folders to grant — do not pre-grant.

## Reusable scripts
- Local data pattern: `walk()` recursion + `chain()` parent-walk + HTML table builder — see `/tmp/drvilla_docs.pkl` / `DR_Villa_R99_File_Inventory.html` from 2026-09-10 for a working example.