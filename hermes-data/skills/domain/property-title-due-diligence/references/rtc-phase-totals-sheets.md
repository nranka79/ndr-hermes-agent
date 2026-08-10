# RTC Summary Sheet: Phase Totals (Acre:Gunta:Anna arithmetic) + GWS Sheets editing

Scenario: user has a Google Sheet compiling RTC records (Sl No | Survey No | Village |
Landowner | Land Extent (Acre:Gunta) | Kharab A | Kharab B | Total Land Extent | Khata |
Transaction Details) and asks to add "Phase 1 = 20 acres from sl no 1, Phase 2 = 30 acres
after that" style cumulative totals.

## Extent arithmetic (parse → anna → sum → reformat)
- Extent strings look like `3A-11G`, `0A-38G-4An`, `2A-1G-8An` (anna present on some).
- Convert to total anna: 1 Acre = 40 Guntas = 640 anna; 1 Gunta = 16 anna.
  `to_anna = A*640 + G*16 + An`.
- Sum in anna, then format back: `a, rem = divmod(total, 640); g, an = divmod(rem, 16)`;
  append `-{an}An` only when an != 0 (user's sheet keeps anna fractions, e.g. 0A-10G-8An).
- Regex: `r"(\d+)A-(\d+)G(?:-(\d+)An)?"`.
- Phase 1 = rows from Sl 1 until cumulative gross ≥ 20A (800 anna... no: 20A = 20*640 anna).
  Phase 2 = next rows until cumulative reaches Phase1_total + 30A.
  Report BOTH the cumulative-at-cutoff and the phase-block sum; the phase block sum is what
  goes in the sheet.
- Cross-check: Phase1 + Phase2 + remaining rows must equal the grand total exactly.
- This session: P1 (Sl 1-10) 20A-22G gross / 0A-8G KharabA / 20A-14G net;
  P2 (Sl 11-42) 30A-34G gross / 0A-10G-8An KharabA / 30A-23G-8An net.

## Editing the sheet (GWS)
- `gws_skill_bridge.call("sheets_get"/"sheets_update", service_name=..., sheet_id=...,
  range=..., values=JSON-string)` works in normal sessions, but in execute_code the bridge's
  import can fail with `PermissionError: [Errno 13] ... google_api.py` when the sandbox can't
  read the bundled skill file (HERMES_HOME mismatch). Fallback that always works:
  ```python
  from tools.gws_auth import build_service
  svc = build_service("sheets", "v4", service_name="google-draas")  # resolve first!
  svc.spreadsheets().values().get(spreadsheetId=..., range="Sheet1!A1:J200").execute()
  svc.spreadsheets().values().update(spreadsheetId=..., range="Sheet1!A54:J55",
      valueInputOption="USER_ENTERED", body={"values": rows}).execute()
  ```
- Resolve the account with `gws_resolve_account` first — psingh@draas.com → service_name
  `google-draas` (vault key, not the email).
- Totals rows style (user expects): label in col D, values in E–H, bold + yellow highlight.
  Match existing totals. Formatting via batchUpdate repeatCell:
  ```python
  svc.spreadsheets().batchUpdate(spreadsheetId=..., body={"requests":[{"repeatCell":{
    "range":{"sheetId":0,"startRowIndex":53,"endRowIndex":55,
             "startColumnIndex":0,"endColumnIndex":8},
    "cell":{"userEnteredFormat":{"backgroundColor":{"red":1.0,"green":0.95,"blue":0.6},
            "textFormat":{"bold":True}}},
    "fields":"userEnteredFormat.backgroundColor,userEnteredFormat.textFormat.bold"}}]}).execute()
  ```
- Sheet IDs are 1-indexed row ranges in Sheets API; row 1 = header.
- Read-back after write to verify (values().get on the written range).
