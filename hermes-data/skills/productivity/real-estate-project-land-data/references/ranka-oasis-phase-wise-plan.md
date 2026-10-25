# Phase-wise Plan / Land-Bank Demarcation Map (Ranka Oasis — Sevaganapalli)

Worked 2026-10-03. Trigger: *"is there any phase-wise divided plan for Ranka Oasis — extract phase one, phase two, phase three."*

This is a **Phase 1 / Phase 2 land-bank demarcation**, distinct from:
- Karnataka **Stage 1–4** land-record tables (see `land-record-table-4stage-extraction.md`), and
- DTCP **layout phasing in the approval** (only Phase 1 is in the approved layout).

## Source artefacts

| Artefact | ID / location |
|---|---|
| `Sevaganapalli Layout Phase 1 & 2.png` — **the phase demarcation map** | `1g7fEqHcISIEIV0g0ZnzD5blgT5RM4aWr`, parent folder `1wlm6pCmDxyO4v8dLPlpwhvpmhCvtiUfH` |
| `Sevaganapalli Layout (Phase 1 & Phase 2). 31.05 copy.png` — earlier copy | in Drive tree (`drive_oasis_tree.json`) |
| DTCP Layout Plan 13.01.2026 | `1amC6dV377hiYneKaChQ5UNlM_9sMy9-U` (Approvals folder `17pqfdNEW6leLDVfPGH62oNJ0bhFl5Id1`) |
| DTCP + Panchayat Layout Planning Sanction 30.03.2026 | `1QZ2UvZs8mL96-GfzLLLbAanG6gUTlKZ1` |
| English translation of the DTCP approval (HTML) | `1pFnV7jT5ofWWgHbORF15OvhZ-BzcGB-F` |
| ⚠ `20241212 Writeup 4 Vivek Saveganapalli Ranka Oasis Phasing Explanation` — the **written** phase-wise note | `1swLF9-qiQfSHpItf1V1V_-uTDd7LJd0AAGoJyBcVtBY` — **NDR-private, not accessible** (see below) |

## Extraction method that worked

1. `gws_drive_list(query="name contains 'Oasis'")` + `"name contains 'Phase'"` to find candidates — the phase map surfaces only under a `Phase` query, not under `Oasis`.
2. Download the PNG through the Drive API (`files().get_media`).
3. `vision_analyze(..., also_describe_visually=true)` with an explicit phase question. The first (OCR-only) pass returned the notes-box text but scrambled the geography; the **second call with `also_describe_visually=true`** returned the phase-by-phase survey listing and the relative positions. Ask both questions at once:
   - *"Where on the map are the PHASE-1 and PHASE-2 regions relative to each other? Which survey numbers sit inside each phase? How do the annotation lines point from the notes box?"*

## The phase split (as read from the map)

- **PHASE 1** — *already owned*, **4 acres 47 cents**. Southern / lower-central block; this is the land the DTCP-approved layout (Plots 1–130) sits on.
  Survey nos.: `166/3A, 166/3B, 166/3C, 166/3D, 166/3E1, 166/3E2, 166/3F` (+ `167/1H`, `167/1I` at the boundary).
  No Kaaldhari / Bandidhari.
- **PHASE 2** — wraps Phase 1 on **West, North and East**, in five colour-coded buckets:

  | Bucket | Extent | Survey numbers |
  |---|---|---|
  | Already owned | 1 ac 97 c | 158/1C1, 158/1C2, 158/1C9B, 158/2D |
  | Token paid | 1 ac 24 c | 167/2B, 167/2C; 166/1B series; 1C3, 1C5, 1C6, 1C8, 1C9A |
  | Exchange land | 64.41 c | 168/1A |
  | To be acquired | 2+ ac | 166/1, 168/1B |
  | A2S done | 95.09 c | 177/1B series (western strip); 167/1H & 167/1I transitional |

- **Between the phases** — a village road runs through; it becomes part of the layout road itself, so the phases are not physically severed.
- **Map header total** (survey nos. 158/1C1, 1C2, 1C9B, 2; 166/3A–3F, 3E1, 3E2; 167/1I, 1H, 2D; 1B2, 1B3): **~10 acres**. The project holding as recorded elsewhere is **~12.74 ac** across 158/166/167/168/176/177 — the 10 ac is the *phase-demarcated core*, the balance sits in surrounding surveys. State both, don't merge.
- **Allocation logic (from the 12-Dec-2024 investor meeting doc):** collateral plots for investor allocations are taken from **Phase 2**, so Phase 1 cash flows stay with development.

## Approvals that reference the phases

- DTCP Layout No. **03/2026 & 02/2026 dt 13.01.2026** (Roc. RJDVYJD1/2026/TCP)
- Sevaganapalli Panchayat Planning Permission **03/2025 dt 30.03.2026**; Road Pattern dt 17.12.2025
- 19 survey numbers in the sanction letter: 158/1C9A, 158/1C9B, 166/1, 166/2B2, 166/3A, 166/3B, 166/3C, 166/3D, 166/3E1, 166/3E2, 166/3F, 167/2C, 167/2D, 167/1G, 168/1B, 176/1B2D, 176/2B4A, 177/1A1A, 177/1A1B

## Pitfalls

- **The phase demarcation is COLOUR-CODED ONLY — there are NO annotation arrows** from the legend box to the map polygons. The phase split must be read by matching legend swatches to plotted survey polygons. Say so in the deliverable; it is a real confidence caveat.
- **Do NOT infer phases from the DTCP approval.** The approval covers only the Phase 1 layout; Phase 2 land is largely *outside* the sanctioned 19 surveys. The two lists legitimately differ (see `approved-layout-vs-tsr-classification.md`).
- **A written phase-wise doc may exist but be unreachable.** `20241212 Writeup 4 Vivek … Phasing Explanation` is owned by NDR: `docs().get(documentId=…)` → **403 "The caller does not have permission"** and `permissions().list()` → **404**. That is a genuine no-access verdict from the session user's own token. Per the standing DWD rule, do **not** switch to `gws_dwd_*` — the user did not name another person's account. Report it and tell the user to ask NDR for access. Do not spend further calls probing it.
- The phase map is a **land-acquisition** view (~10 ac) and the DTCP print an **approval** view (30,416 sq.m / 130 plots) — present them as two different scopes.
- Extents and survey mappings read from a coloured legend should be confirmed against the original print before external use — include that note.

## Delivery shape that worked

Single `.docx` (python-docx build → `/opt/data/.venv/bin/python`) uploaded to the phase map's own Drive folder, with the phase map PNG and the DTCP layout PDF attached alongside via `MEDIA:`. `.docx` is a supported artifact type for this user; `.html` is not. Body: At-a-glance table → Phase 1 → Phase 2 (bucket table) → between-the-phases → total extent & approved layout → approvals → notes/caveats.