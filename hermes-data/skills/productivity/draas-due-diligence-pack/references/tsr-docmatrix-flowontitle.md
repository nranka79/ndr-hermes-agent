# TSR → DocMatrix: PART_V_FlowOnTitle rebuild (worked example, 2026-08-10)

Spreadsheet: `20260809 Ranka Oasis - Survey-wise Legal Documents Matrix`
Sheets id: `1eVqckk3cCWdN06RNGISTP99WSz-aToCmGcNPIIqaicc` (service `google-draas`)

## 14 family groups (row-block order used in the rebuild)

1. **F1. Lakshmana Reddy family** — 158/1A1 → 158/1A1A + 158/1A1B (also 167/1A, 168/1A via same Partition 7512/2009)
2. **F2. Yella Reddy pool** — 158/1B2, 1B3, 1B4, 1C3, 1C4, 1C5, 1C6, 1C9A, 167/2C, 167/1E
3. **F3. Billa Reddy** — 158/1B5, 167/2B (NOT acquired)
4. **F4. Krishna Reddy** — 158/1C1
5. **F5. Lakshamma → Gowramma** — 158/1C2
6. **F6. Rukhmani → Ravindra** — 158/1C7 (NOT acquired)
7. **F7. Pappi (Pedda) → Ramachandra** — 158/1C9B → 159/1C9B
8. **F8. Nanjunda / Nagi Reddy** — 166/3A, 3B, 3C, 3E1, 3E2
9. **F9. Butta → Venkataramanappa** — 166/3D
10. **F10. Lakshamma → Gowramma → Umadevi → Venkataswami** — 166/3F
11. **F11. Guvva Reddy** — 167/1H, 167/2D (167/1E → Yella pool)
12. **F12. Nanjunda** — 167/1D + 167/1I
13. **F13. Lakshmana → Purushotham** — 168/1A (⚠️ patta error 1008/2191)
14. **F14. Lakshmaiaya → Murali Gopal → Clover → Kencha → Venkatamma** — 176/1B2D, 176/2B4A, 177/1A1B

## Exact 19-column schema

```
A Family / Origin Group
B Survey No (stage)
C Flow Tree            (box-drawing: ┌── origin / ├── sub / │ ├── txn / └── txn)
D #                    (TSR txn number)
E Date
F Event / Document Type
G Doc No / Registration
H Party From (owned what)
I Party To (received what)
J Extent (Ac)
K Patta No
L Transaction Summary  (who owned → transferred/sold → to whom, with ⚠️ flags)
M Deed Link
N FMB Sketch
O UDR A-Register
P Adangal
Q EC
R Patta/Chitta
S Status               (✅ ACQUIRED / ✅ DRA REALTY / ❌ NOT DRA / ⚠️ / UDR / 📄)
```

Row roles:
- **ORIGIN row**: `B = '<survey> (ORIGIN)'`, `C = '┌── <survey>'`, Event = UDR / Original, holds original pattadar + patta + extent.
- **SURVEY HEADER row**: `F = 'SURVEY HEADER'`, holds current owner (col H), extent (J), current patta (K), and the five revenue-doc links in N–R. Bold + light-gray background.
- **Transaction rows**: `C` carries the tree prefix (`│   ├── Partition 7512/2009`), each with deed link in M, status in S.

## Formatting recipe (Sheets API batchUpdate)

- Header row 0: navy bg `(0.13,0.24,0.42)`, white bold text — text color must be inside `textFormat.foregroundColor`.
- Family first-occurrence rows: light pastel per family (F1/F4/F5/F7/F14 bluish, F2/F8–F12 greenish, F3/F6 reddish, F13 amber), bold.
- Status column (S): green `(0.80,0.93,0.80)` for ACQUIRED/DRA REALTY, red `(0.98,0.85,0.85)` for NOT DRA, amber `(1.0,0.92,0.70)` for ⚠️/ERROR.
- `frozenRowCount: 1`; column widths A≈260, B≈130, C≈220, L/M≈300, N–S≈110; wrap on H–M.
- Batch 100 requests per call, `time.sleep(1)` between.

## MISSING_DOCUMENTS sheet (38 rows, 2026-08-10)

Columns: `S.No | Survey No(s) | Document / Item Missing | Why Required | Source / Basis | Priority | Status / Action Needed`.

Gap groups used:
1. **DC/LHC not furnished** (Pappi Reddy, Munnusamy, Krishna Reddy, Guvva, Venkataramanappa, Hanumanthappa, Nagi Reddy, Lakshmana Reddy, Kamalammal; illegible Yellamma DC) — HIGH/MEDIUM.
2. **Revenue docs**: UDR Register (village), Village Map, per-subdivision FMBs (158/166/167/168/176/177) — MEDIUM.
3. **ECs**: essentially all surveys lack full-chain EC except 166/3F & 167/1A — HIGH.
4. **Patta errors**: 168/1A (1008/2191 wrong names), 177/1A1B (patta shows 1A1A) — HIGH.
5. **Extent discrepancies**: 158/1A1B (0.50 vs 0.51), 158/1C9B (0.72 vs 0.69), 176/1B2D (0.16 vs 0.03) — HIGH/MEDIUM.
6. **Share gaps**: 158/1B3 balance 1/3rd, 158/1C5 Narayana Reddy heirs — HIGH/MEDIUM.
7. **Missing deeds**: GPA 1720/1995 (Sale 176/1995) — HIGH.
8. **Zero-file surveys**: 158/1C4, 1C5, 1C6, 1C7, 176/1B2D, 176/2B4A, 177/1A1B need complete doc sets — HIGH.

## Build workflow (sequence that worked)

1. `session_search` for prior FlowOnTitle context; read current sheets (PART_V, PART_I, survey sheets, FLOW_CHARTS, SUMMARY).
2. Backup old flat version → new sheet `PART_V_Flat_Backup` (addSheet + values.update).
3. Extract per-survey unique file links from all 34 `Sy_*` sheets; classify by filename (fmb/adangal/udr/ec/patta/deed); fall back to PART I FMB series bundles where survey sheets are thin.
4. Assemble 19-col rows in Python (two-part script: families 1–7 then 8–14, insert 167/1A block that was initially missed), JSON dump, verify column counts.
5. Clear + write PART_V_FlowOnTitle; create MISSING_DOCUMENTS sheet; write both.
6. Format both sheets; update SUMMARY notes with rebuild date and row counts.
7. Verify by reading back: 171 rows, 34 survey headers, 14 families, per-survey link columns populated.
