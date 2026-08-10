# Plot Allotment & Voice-Note Verification (Ranka Oasis)

Session-derived pitfalls for allotment work sourced from voice notes + master inventory.

## Pitfall: voice-note plot numbers get garbled — cross-check against master inventory
Bharat's voice notes frequently drop digits or swap numbers ("plot 20 which is 1580").
The MASTER inventory is the source of truth, NOT the voice note:
- User said "plot 20 = 1580 sqft" → master says Plot 20 = 2,440.79 sqft; the 1,580 sqft
  plot in the red-marked set is **Plot 120** (1,581.53 sqft). The voice note dropped the "1".
- ALWAYS verify any plot number + area cited in a WhatsApp/email draft against the
  master inventory sheet (ID 1jHjOIUQSMVwVQewFES2d77D9SaHK2DcUbbTBvwwRH8o) before sending.
- Flag discrepancies to Bharat explicitly BEFORE finalizing the draft ("you said X but
  master shows Y — confirming I used Y").

## Master inventory structure
- Tab name has a TRAILING SPACE ("Reading with exact name:" bug — use exact tab name).
- Headers are on row 2 (row 1 is a merged group header "Dimensions in M" etc.).
- Columns: Plot #, Facing, Corner, Shape, E/W/N/S (m), Area sqm, E/W/N/S (ft), Area sft,
  East by / West by / North by / South by (neighbours), then Grove/Vista/Reserve FSI columns.
- Red-marked allotment set (from allotment PDF, pixel-verified): 22, 92, 105-106, 107-108,
  109-110, 117, 118, 119, 120 (9 plots). Plot 22 = 1517.71 sft, Plot 120 = 1581.53 sft.

## Allotment change narrative (what Bharat says when requesting approval)
"Earlier we chose 95&96 (combined, ~1,290 sft) and 93&94 (combined, ~1,370 sft) but they
didn't match the ~1,500 sft target, so we included Plot 120 (1,580 sft) and Plot 22
(~1,500 sft, perfect fit)." — reuse this framing in the WhatsApp approval message.

## Drive share-to-anyone pattern (Bharat's account)
- Auth: HERMES_SESSION_USER_ID=sales1_blr HERMES_HOME=/opt/hermes python3
- Service name that WORKS for sales1.blr@draas.com in the vault: **google-draas**
  (probe: gws_auth.load_credentials('google-draas') succeeds; 'google' / 'google-sales1'
  fail with VaultNoTokenError under user sales1.blr-8717455402)
- To copy an existing shared Google Sheet into Bharat's Drive and make it public:
  1. service = gws_auth.build_service('drive', 'v3', service_name='google-draas')
  2. files().copy(fileId=SOURCE_ID, body={'name': ...}) → new file owned by sales1.blr
  3. permissions().create(fileId=fid, body={'type':'anyone','role':'reader'})
  4. Verify content: curl "https://docs.google.com/spreadsheets/d/<ID>/export?format=csv"
     (public export works once anyone-with-link is set)
- Public CSV export also works on shared sheets WITHOUT auth — good way to inspect a
  sheet Bharat drops as a link before touching the API.
