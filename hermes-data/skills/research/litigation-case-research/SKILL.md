---
name: litigation-case-research
description: Research a litigation/transaction matter for Nishant (DRAAS) and produce a one-pager status brief — locate prior work via session_search, pull Drive matter folders, extract court-order PDFs verbatim, map every forum (civil, commercial, NCLT, HC, ancillary), and deliver a structured HTML one-pager to Drive TMP. Use for "research the X matter", "create a one-pager/briefing note for case X", "where does this case stand".
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [research, litigation, legal, one-pager, briefing-note, drive, court-orders, html-report]
---

# Litigation / Transaction Case Research & One-Pager

Use when the user asks to research a legal matter or produce a one-pager / briefing note on where a case stands. Recurring for DRAAS: Vani Vilas (Nippon × Veracious), OS 7/2025 (Pavan Kumar, Krishnagiri), Meteorite vs WHPL (Hosur), landowner disputes, etc. Most matters have months of prior work — ALWAYS harvest it before starting fresh.

## Workflow

1. **session_search FIRST** (query = party names + project names + case numbers, e.g. "Nippon", "Vani Vilas OR Veracious OR Reliance Capital"). These matters have been worked across many sessions; prior sessions contain extracted facts, file IDs, and already-built summaries. Re-using them is faster and more accurate than re-reading every PDF. Note: session_search misses multi-word queries — fall back to sqlite LIKE on /data/hermes/state.db per memory.
2. **Load the matter folder on Drive** (`gws_resolve_account` → `google-draas` for ndr@draas.com). Typical structure for a DRAAS matter: root folder with sub-folders `NDR Notes/`, `Transaction Documents/`, `Legal Data/` (with `Enforcement Suit/`, `NCLT/`, `HC/`, `Criminal/`, `Contempt/`), `Property Documents/`, `Sanction Plans and NOCs/`, `JDA/`.
3. **Read NDR Notes markdown FIRST** — they are the user's own synthesis (Facts Compilation, Comprehensive Legal Analysis, order summaries). They give 90% of the picture in seconds. Read via `drive.files().get_media(fileId=...)` then decode utf-8.
4. **For court orders, extract text with pdftotext -layout** (download via MediaIoBaseDownload → `/tmp/xxx.pdf` → `pdftotext -layout`). The operative **ORDER paragraph must be quoted verbatim** — stay/injunction wording is the crux and paraphrasing loses precision (e.g. IA 66: "restrained from further assigning, selling, transferring their rights under the Debenture Trust Deed and Mortgage Deed dtd.10.03.2016 to any third party in any manner till the disposal of the suit").
5. **Map EVERY forum** — the same matter typically runs in parallel: commercial suit (Com.OS, Commercial Court CCH-xx), original suit (O.S., City Civil), NCLT (liquidation + avoidance IAs), Karnataka HC writs, criminal/contempt. Table per forum with: case no, relief, filed by, order date, outcome tag.
6. **Build the HTML one-pager** with the house structure below, upload to **TMP folder** (Drive id `18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`), set **anyone-with-link reader** permission so it renders in browser without login, share the webViewLink.
7. **Offer next steps**: PDF export, Google Doc copy, or filing into the matter folder after user review (NDR convention: new artifacts go to TMP first, then into the matter folder only after approval).
8. **"What happened at the hearing / case status / next date" checks** — the national eCourts v6 portal (`services.ecourts.gov.in/ecourtindia_v6`) covers **district courts only**; the Karnataka High Court is NOT in its state→district→complex flow (its High Courts page routes to the HC's own portal: `karnatakajudiciary.kar.nic.in` / `judiciary.karnataka.gov.in`, which may be down/unreachable). When the HC portal is down, do NOT stop — run the fallback chain (Google News RSS via curl, Deccan Herald search API, Bing News in browser). Exact recipes and query formats: `references/court-case-status-lookup.md`.
9. **"Did they ever mention/plead X?" — full-record sweep.** When the question is whether a party ever spoke about a specific legal point (partnership deed on record, registration, s.69 IPA challenge, annexure produced), sweep the ENTIRE matter folder, not just the orders:
   - Download all PDFs + docx from the matter folder → `pdftotext -layout` → flag scans (empty text) → OCR scans with tesseract in background (`pdftoppm -r 150 -gray -png` + `tesseract` per page; see `draas-drive-organization` skill) → grep corpus for the term + variants (`partnership|registered|registration|section 69|annexure|deed`)
   - **Plaint assertions ≠ record contents.** A plaint saying "copy produced at Annexure A" does NOT prove the annexure is physically in the filed bundle — check the plaint PDF's actual pages (often ends at verification/schedules with no annexures attached) and the Document Index spreadsheets. Report the gap: asserted but not on record.
   - **Opposing party's own filings can concede the point** — e.g. defendants' objection affirming "plaintiff is a Partnership Firm registered under the provisions of Indian Partnership Act 1932" removes any s.69 maintainability fight. Always check what the other side admitted before flagging a risk.
   - **Firm-name mismatch is a live exposure for partnership suits** — the deed on Drive may name the firm differently ("Ranka Raj Venture") from the suit plaintiff ("Ranka Raj Properties"); check deed name clause vs plaint cause title vs MOU party description, and note who signed the MOU (managing partner) vs who verified the plaint (partner).
   - Case-specific map: `references/os553-rrp-khimji-case-map.md`

## House one-pager structure (NDR's preferred format)

- **Header**: navy/blue gradient, title, sub (parties + deal type), meta (location, date, CONFIDENTIAL)
- **1. Thirty-Second Summary** — green card; lead with the deal (amounts, security, co-obligors), then the critical development (stay order / latest ruling) highlighted
- **2. Parties** table (role + details)
- **3. Financing & Security** — KPI grid (face value, actual subscription, maturity, coupon/IRR, suit claim, S.66 liability) + bullet structure of security documents
- **4. The Project** table (land, JDA, units, mortgaged vs sold, remaining inventory)
- **5. The Dispute** — 3 cards: each side's case + court's interim position so far
- **6. Litigation Map** — one subsection per forum, tables with outcome tags (win green / loss red / neutral grey)
- **7. Where Things Stand** — KPI grid + Leverage Analysis (green strengths card, amber risks card) + settlement track bullets
- **8. Key Contacts** table (name, role, phone/email)
- **9. Document Trail** table (category → key docs)
- **Open Items** red card at the end
- Footer: prepared by Hermes for Nishant Ranka, date, sources, "for internal strategy use — not legal advice"

Style rules: ₹ notation (not Rs.), data tables + chronology over prose, dark-themed cards OK for HTML. Telegram delivery: brief bullets, lead with the answer + Drive link.

## Deliverable variant: short status brief (WhatsApp / compact HTML)

NDR sometimes wants a *short* status of all cases (not the full one-pager) — trigger phrases: "short write up of all the cases", "status of all cases", "presented as a WhatsApp message or in HTML format". When that fires:

1. **Reuse, don't rebuild** — locate the latest full one-pager in Drive TMP (`18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`) or the matter's NDR Notes; the short brief is a condensation of it, not fresh research.
2. **Structure for WhatsApp**: one section per forum (Main suit → key IAs → NCLT → HC → ancillary), each with case no + relief + order date + outcome. Lead with the main case and the legal basis (e.g. "enforced as mortgagee under TPA ss.58/67/69 via O.34 CPC — NOT SARFAESI, because AIFs/debenture holders aren't banks/FIs"). Bold via `*text*` (WhatsApp markdown).
3. **Also emit a compact HTML** version (same house styling, status tags) and attach it via `MEDIA:` — the user often wants both; deliver both in one message.
4. State the **net position** at the end (leverage + risks + settlement track) — same content as one-pager §7 but 2 cards, not a grid.

## Pitfalls

- **Voice transcriptions corrupt legal terms** — verify against documents before writing them into briefs. Observed: "EIF, registered fund, semi-registered fund" → actually **AIF (SEBI-registered Alternative Investment Fund)**; "Alala Sindhra" → Allalasandra; "jck_1960" → jayck_1960. When unsure, write the correct legal term from the source docs and note the correction.
- **eCourts browser session drops to an empty page between turns** — a solved captcha dies with it. Refill the whole cascade first, extract the captcha LAST, and submit immediately on the user's answer (see `references/court-case-status-lookup.md` "Browser session drops"). Verify the on-screen captcha still matches what the user solved before submitting (md5 compare).
- **Captcha solving: hand the image to NDR immediately, don't OCR-loop.** NDR's explicit preference (2026-08-12): *"just give me the image and let me solve the OCR"*. When vision is unavailable, send the upscaled captcha via MEDIA: and ask — OCR (tesseract) is unreliable on eCourts captchas even after multiple preprocessing passes.
- **Certified orders are the source of truth** for operative directions. Quote the ORDER paragraph verbatim.
- **Same matter = many case numbers** (O.S., Com.OS, NCLT CP, IAs, WPs). Don't conflate them; the IAs carry the real action (injunction/stay/attachment).
- **Prior sessions contain file IDs** — grab them from session_search results instead of re-searching Drive.
- NDR's TMP-first convention applies to new artifacts; don't file straight into the matter folder.
- Upload HTML as `text/html` mimetype so it opens as a rendered page in browser; anyoneWithLink permission avoids login friction when sharing.
- Amounts compound: quote principal O/S and the current claimed total separately (interest accrual is often the real pressure point).

## Reference files
- `references/vani-vilas-nippon-case-map.md` — full Drive file IDs, certified-order IDs, forum/status table, core facts, contacts and settlement track for the Nippon × Veracious "Vani Vilas" matter. Load this before any fresh work on that matter (search NDR Notes / Legal Data first, then this map).
- `references/court-case-status-lookup.md` — case-status / hearing-outcome lookup for Indian courts when portals are down: Google News RSS via curl (no key, no captcha), Deccan Herald search API (full-text stories), eCourts v6 form automation via browser_console (verified code chain for Karnataka→Bengaluru→City Civil, compound complex-value pitfall, fillCaseType sequence, session-bound captcha extraction + user-solves-captcha flow), and which engines captcha-block server-side.
- `references/wp-38186-2025-cantonment-pil.md` — case map for the RLDA/Bagmane Cantonment biodiversity-heritage PIL (W.P. 38186/2025): parties, bench, Dec-2025 interim restraint order, timeline, and 30-Jul-2026 hearing status.
- `references/serenity-hillview-assudani-matter.md` — GBJT land (Sy 93/2 Hurulagurki) transaction-cum-litigation map: O.S. 4595/2026 (s.92 CPC, leave order only, adjourned 01.09.2026), the 15.08.2026 legal opinion to Sri Assudani by Adv. Vinod Kumar (title/sale-authority/reversion/11E/stamp-duty findings), Drive Legal-folder IDs, follow-up-questions file id, people (Assudani, Adv. Vinod Kumar vinod@advocatev.in, Nishant Prakash Zara), and the 26-Aug-2026 meeting. Voice-correction anchor: "Southin lawyer" = Assudani's lawyer.
