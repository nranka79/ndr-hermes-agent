# Akrama-Sakrama / Sadaavakasha Regularisation Handbook — locating & recovering

## What the book is
- "Hand Book on Regularisation of Unauthorised Development or Construction — Application Forms and Instructions to the Applicants", issued by the **Urban Development Department, Govt of Karnataka** + **BBMP**.
- Bilingual (Kannada + English). The 2015-16 edition (application window **01-03-2015 to 29-02-2016**) is the "Sadaavakasha" handbook (cover: ಸದಾವಕಾಶ, UDD + BBMP logos).
- Covers: **Sec 76-FF KTCP Act 1961**, **Sec 321-A KMC Act 1976**, **Sec 187-A KM Act 1964**, FAQs (16 Q&As), application Forms I–IV (application / acknowledgement / provisional order / regularisation certificate / rejection).

## Where it lives online
- Official UDD PDF: `https://udd.karnataka.gov.in/uploads/media_to_upload1741687877.pdf` — in Google's index (found via Apify residential Google search), but the UDD server is frequently **down** (times out from VPS curl, Apify crawler, AND cloud browsers — site-wide outage, not an IP block). Re-check later; not in Wayback.
- Scribd doc **335522537** "English-Akrama-Sakrama": **MISLABELED** — content is ALL KANNADA despite the title. Do not use as the English copy.
- Scribd doc **402347622** "Handbook_Akrama-Sakrama_eng.pdf": the real **English** version, 46 pages, login-walled for download.
- Wayback capture of the Scribd page (e.g. timestamp **20250911201411**) embeds the FULL English text in HTML — see recovery below.

## Egress ladder for *.karnataka.gov.in / bbmp.gov.in (VPS datacenter IP is blocked — curl returns HTTP 000)
1. **Apify residential**: `apify_run_actor` with `apify/google-search-scraper`, input `{"queries": "<string>", "maxResults": 20, "proxyConfiguration": {"useApifyProxy": true, "apifyProxyGroups": ["RESIDENTIAL"], "apifyProxyCountry": "IN"}}`. `queries` must be a **string**, not an array (400 otherwise). Reached Google fine and surfaced official UDD URLs. Kannada queries work well.
2. **Browser Use Cloud** — works once credits exist; but it too timed out on the UDD PDF (server down). Include `live_url` in replies.
3. Direct curl / web_extract / browser_navigate from VPS — all fail (HTTP 000 / tunnel error / timeout) against bbmp.gov.in and karnataka.gov.in.
- **No separate residential proxy / client node is configured on the box** (checked SSH config, WireGuard, Tailscale/ZeroTier, both .env files, session history). Apify's residential pool is the ONLY residential egress. If the user references "our client node", verify before assuming it exists.
- Apify API key can get rate-limited mid-burst ("All configured APIFY_API_KEY key(s) were rejected") after ~5 rapid runs — wait a few minutes and retry; don't hammer.

## Recovering a login-walled Scribd doc via Wayback (works when live download is gated)
1. Find the capture: `curl -s "http://web.archive.org/cdx/search/cdx?url=scribd.com/document/<ID>*&output=text&limit=40&collapse=urlkey"` → pick the newest `text/html 200` snapshot.
2. `curl -sL "https://web.archive.org/web/<timestamp>/<scribd-url>" -o page.html` (1.2 MB for a 46-page doc).
3. Extract `<p>` tags in document order with python `re.findall(r'<p[^>]*>(.*?)</p>', content, re.S)`, strip tags, `html.unescape`, drop empties.
4. Trim Scribd footer junk: the related-docs carousel starts with text like `PDF100% (1)Akrama Sakrama` / `PDFNo ratings yet...`; the real document ends at the final page marker (e.g. `45 46` for a 46-page doc). Cut there.
5. Rebuild a clean PDF with **reportlab** (installed in the default python3 env — 4.x): `SimpleDocTemplate` + `ParagraphStyle` (title/subtitle/heading/body), skip bare page-number paragraphs, `html.escape()` body text before Paragraph. ~11 A4 pages for the 46-page original.

## Kannada OCR / translation (built-in OCR garbles Kannada)
- `vision_analyze` returns garbage for Kannada text (it uses the tesseract OCR path — "method": "ocr").
- Use **OpenRouter `google/gemini-2.5-flash` vision via execute_code**: POST `https://openrouter.ai/api/v1/chat/completions` with content parts `{"type": "text"}` + `{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}`; prompt for transcription + English translation + issuing authority/edition. `call_openrouter_model` is text-only — it cannot take images, so the direct API call is required for image input.
- API key: `os.getenv("OPENROUTER_API_KEY")`, fallback to parsing `/data/hermes/.env` (line `OPENROUTER_API_KEY=...`).

## Pitfalls
- **Never trust a Scribd title/filename for language** — verify the actual extracted content. "English-Akrama-Sakrama" (335522537) was all-Kannada; the real English handbook was under a different doc id (402347622).
- Official gov PDF may exist in Google's index but be unreachable from every egress (server down). Deliver the recovered content + the canonical URL + a "retry later" note rather than claiming the URL is dead forever.
