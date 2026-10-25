# Canonical NDR project folder IDs (draas.com Drive) — verified Sep/Oct 2026

Use this map when a task says "move/transfer <project> content into the right
folder on NDR's drive". All IDs below are NDR-owned (`ndr@draas.com`) canonical
project homes discovered during the architect.blr multi-project reorg
(2026-09-29/10-01). NEVER invent a new folder (NDR hard rule: no new folders
except under TMP) — if a project has no canonical folder here, flag it.

## Verified canonical destinations (owner = ndr@draas.com)

| Project | Folder | ID |
|---|---|---|
| Ranka Oasis (canonical) | `Ranka Oasis` under Sevaganapalli Land Partners | `1w947jyUeOH-k40qm4rrNwIc2j1BHwUTO` |
| Ranka Oasis / villa designs | `Ranka Oasis / Proposed Villa Designs` (subfolder) | `15spE6YEwuKGDXbnZeCooKElbtZozeU5n` |
| Ranka Udaya / A&E | `Ranka Udaya Architectural and Engineering` (subfolder) | `1cIbeCVsFtXtL9o0BYAEp3XHh6_t0lv2J` |
| Ranka Udaya (canonical) | `Ranka Udaya` under DRA Thindulu Land Partners (DTLP) | `1sdDX5htwSKF2SSe_re-jjYb-8SsFCk8Z` |
| Ranka Iris | `RankaIris` under Current Properties | `0B1Oc8cSaJXPGdy04dWxlbE9JR1k` |
| Ranka Iris / Marketing | `RankaIris / Marketing` | `1LwWw-ZtdPYdtO3C_13A8mqM1Mf9QE6k5` |
| Riverstone | `Riverstone` docs | `1bFjhTOKmDz0iO4QrI8Mtb-Oy54rLo4Md` |
| Palm Paradise TN / Westbury | `20260914_TN_PalmParadise_Westbury_Layout_RnD` (R&D pack owner) | `1JNx9KUmaCMwx-jExF0XBftlcGM-SRt-d` |
| Westbury / PLS (Palm LakeSide) | `Current Properties / Westbury` | `1EHfUdw_pc0OxWqvf-rkLlPreKfGWgeTA` |
| Edwardian Office | `Current Properties / Edwardian Office` | `104DMJyhwr-yNtBdcWFIls9J6tr1Qw8_W` |
| North Star (Allalasandra) | `Current Properties / NorthStar` | `0B1Oc8cSaJXPGflNPVEdodC00T3Q3VjdyZXRBLVI1VmpxZUxMOTZJc1VsQjI3cnhtV3g5azQ` |
| Avillion / Marketing | `AVILLION / Marketing` | `1ifR0K0HBtezzU5w4zRWZO5sCXBxn_9AH` |

## Projects with NO canonical NDR-owned destination folder (verified 2026-09-29)

- **Serenity Hill View** — only sales1.blr-owned and bk@findingform.design-owned
  folders exist (`Serenity Hill View ` 1DDqeC_t8ElmDECYvclYdL808Yp_hgkJn sales1,
  `Serenity Hill View` 1IE7eHHYhpODMDbh8ehVkAVguv9yVrv7Z bk design, drift footage
  folders under sales1). No NDR-owned project folder → FLAG, don't guess.
- **Ranka Palm Lakeside** — folders exist but are sales1-owned
  (`20250315 Ranka Palm lakeside Docs` 1U01_LunGHnus0 / `Ranka Palm Lakeside`
  1dOvbr_rsMHaNIbCbiwuB6c0qV4nSwSva); `Palm Lakeside Site Owners Welfare Society`
  is admin2-owned. No ndr-owned canonical → if PLS moves happen, ask NDR for the
  destination or use Westbury (`1EHfUdw...`) as the company umbrella.
- **Amber / Hillview / Edwardian content in architect.blr** — none found; the
  user expected them but the account had no matching files (report as "none
  found", not "moved").

## Notes

- `Current Properties` (`1ZCV3Kh2nfme4Bqf4hUAPsyI_JtSQDv3R`) holds many legacy
  property folders (80Edifice, RAQ, Stelo, Muthanallur, Westbury, NorthStar,
  RankaIris, Edwardian Office, DRA Thindulu Land Partners). It is NDR-owned.
- `6. Detailed Project Reports` (`16-3z_5FyxRe8EOzUIHewkA1hrYPUBMLr`, parent
  V-Gro pack) contains per-project DPR subfolders (Ranka Oasis / Amber / Udaya
  created 2026-09-21) — these are DPR report copies, NOT the canonical project
  working folders. Do not move working files into DPR folders by mistake.
- Verify any destination id before use: `gws_drive_get` (service_name=google-draas)
  → owners contains ndr@draas.com. Folder ids in this table were owner-verified.