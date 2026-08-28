# Drive Search — Failed Passport Lookup (Kanta Ranka, Jun 2026)

## What failed
Task: Find Kanta Ranka's Indian passport PDF and US visa page.
Searched: `name contains 'Kanta'`, `name contains 'passport'`, Personal folder + subfolders (Travel, World of Visa, Family, New Passports).

**Files found:**
- `BLR-AMD-ZDE7QK-KANTA-RANKA.pdf` → AkasaAir boarding pass (28 APR 2025)
- `TNDV3Z_MRS KANTA RANKA.pdf` → Lufthansa/Air Canada flight itinerary (Jun 2018)
- `UTY7GG_MRS KANTA DINESH RANKA.pdf` → Lufthansa flight itinerary (Dec 2018–Feb 2019)
- `Malaysia ENTRI Note_KANTA DINESH_RANKA.pdf` → Malaysia ENTRI note
- `New Passports/` folder → contains NDR, RNR, Rivaan, Ruhaan passports — **no Kanta Ranka entry**

**Conclusion:** Kanta Ranka's passport scan is NOT in Drive under any variant of "Kanta" / "passport" / "KANTA" naming. It may be:
- Under a different person's folder (e.g. Dinesh Ranka's files)
- Named with Hindi script or a family member's name
- In a physical folder not yet digitized
- Stored somewhere other than Drive

## Pattern for future passport/visa searches
When searching for a family member's passport:
1. Try `fullText contains 'passport'` (not just name search) — catches OCR'd content
2. Try searching the **spouse's folder** (e.g. Dinesh Ranka if Kanta is his wife)
3. Try `name contains 'Travel'` in parents — frequent misfiling
4. Ask user for exact filename if Drive search exhausts all options
5. Check both `mimeType='application/pdf'` and Google Doc exports (passports sometimes stored as `.docx` scans)

## WhatsApp wa.me link encoding (confirmed fix)
Standard `&` (`%26`) in the `text` URL param breaks WhatsApp mobile WebView — it treats `&` as URL parameter separator and truncates the message.

**Fix:** Use FULL-WIDTH ampersand `＆` (U+FF06) inside the message body, which does NOT trigger URL param parsing on WhatsApp mobile.

```python
from urllib.parse import quote

message = "Thanks ＆ regards"  # FULL-WIDTH ampersand, not &

# WRONG — truncates on WhatsApp mobile
encoded = quote(message)  # %26 → & breaks the link

# RIGHT — full-width ampersand survives WhatsApp mobile WebView
# The link opens pre-filled with the full message intact
wa_link = f"https://wa.me/919844017643?text={encoded}"
```

Phone number format for wa.me: raw 10 digits, no +, no spaces, no dashes — e.g. `919844017643`.
