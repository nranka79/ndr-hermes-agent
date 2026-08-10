# Phone-Safe Delivery of Plans/PDFs to Bharat (Telegram mobile)

Problem observed (Aug 2026): a proper vector PDF (A2 master plan with circled plots, ~850 KB)
delivered as a Telegram document was NOT clickable / would not open on Bharat's phone. He reported
"not able to open" then "not able to click on it". This is a Telegram-mobile document-preview
limitation, not a corrupt file (file itself validated fine: 1 page, PyMuPDF opens it).

## Working delivery pattern (use both every time)
1. **PNG photo via MEDIA:** — send the rendered image (e.g. the marked plan PNG) directly in chat.
   Photos always open on tap on Telegram mobile and are zoomable. This is the instant-wins path.
2. **PDF + PNG to Google Drive** with a shareable link — the reliable way to open a big PDF on a phone:
   - `HERMES_SESSION_USER_ID=sales1_blr` (Bharat's GWS session), `service_name='google-draas'`
     via `tools.gws_auth.build_service('drive', 'v3', ...)`.
   - Upload into the project's existing Drive folder (find it first: `name contains 'Oasis'`,
     then match parents). For Oasis plans: `Plot 119 Legal Set` 1lVlRlVKzHc4ID4H7e_ec3toSSfiYeo1w
     (where the old `Oasis Master Plan 18.07.26.pdf` lives).
   - Set `permissions().create(role='reader', type='anyone')` so the link opens without login.
   - Send BOTH links (PDF + PNG); PNG gives instant view, PDF for printing/archiving.
3. Give Bharat the links as plain markdown URLs in chat — he cannot use Telegram inline buttons.

## Notes
- Telegram inline document preview for large/A2 PDFs is unreliable on mobile; don't re-send the same
  PDF a third time expecting a different result — switch to photo + Drive link.
- A rasterized "image-in-PDF" version is WORSE — if asked for PDF, draw vector circles on the
  original PDF instead (see master-plan-annotation.md) or just deliver PNG + Drive.
- Verify the file after any rewrite (PyMuPDF open + page_count + rect) before claiming success.
