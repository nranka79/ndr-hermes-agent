# Rovila preliminary info run — 2026-08-12

## What happened
NDR asked for "preliminary RERA information" on 5+ Rovila (row
house/row villa) projects including The Roots by SVAM, land < 4,000 sq m
(upper 4,500), using the K-RERA site. He also flagged that the earlier
305-file The Roots download contained Mana Verdant docs from a
DIFFERENT project.

## Identity resolution (important)
- The Roots by SVAM Realty = `PRM/KA/RERA/1250/303/PR/090925/008075`
  (promoter SRK INFRA PROJECTS PVT LTD, project THE ROOTS, Devanahalli,
  subtype Row Houses, land 21,168 sq m — exceeds band, kept on request).
- `PRM/KA/RERA/1251/446/PR/041225/008303` = MANA VERDANT TERRACES
  (Mana Projects) — DIFFERENT project, excluded.
- THE ROOTS BY ELEGANCE INFRA (Anekal, Plotted) and AAKRUTHI ROOTS &
  RAYS (Plotted) are also different projects.
- Dedupe: Trifecta Verde Resplandor RH Ph-2 + Ph-3 = one project;
  Villa Phase 1A/1B/1C = one family.

## Final dataset (6 distinct projects)
1. The Roots — Row Houses — 21,168 sq m — flag over band
2. Ashish Narayana Row House — Row Houses — 1,480 sq m — in band
3. Ashish ANR Row House — Row Houses — 3,475 sq m — in band
4. Trifecta Verde(en) Resplandor RH — Row Houses — 6,330/7,284 — one project
5. Sattva La Vita — Villa — 12,140 sq m
6. Villa Phase 1A/1B/1C Devanahalli — Villa — 3,264/3,563/4,278 — one family

## Where things live
- Local: `/opt/data/rera_rowvilla_plans/` (scripts + prelim/ + datasets)
- Drive folder: "Rovila RERA Prelim (2026-08)"
  https://drive.google.com/drive/folders/178pFGIFzFvflgOTpB6Hri0N_5SKBs9bC
- Sheet: "Rovila RERA Preliminary Info (2026-08-12)"
  https://docs.google.com/spreadsheets/d/1Jlqh7kBlyUWxMpmxpDY1z7ot5A8mBSLQuJBNsPZPHIU
- Skill: `domain/rera-preliminary-info`

## Site notes hit this run
- FAR field on legacy pages can show non-ratio values (e.g. 2023.26) —
  keep site value, flag.
- Subtype field absent on legacy (pre-2020) pages — infer from name.
- Unit inventory rows: [SlNo, floorNo, UnitNo, UnitType, CarpetArea,...].
- Header block (project name/reg no) is a col-md-12 or container div
  containing both "Project Name" and "Registration Number".
