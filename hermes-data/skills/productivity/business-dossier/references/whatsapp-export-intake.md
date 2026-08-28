# WhatsApp Chat Export Intake — Dossier Source Material

**Trigger:** User shares a WhatsApp chat export as a zip (`WhatsApp Chat with <name>.zip` — chat text file + media) and asks you to analyze it as source material for a dossier, investment review, follow-up audit, or relationship timeline. Common with investor contacts, brokers, elders, and team members (Nishant regularly exports chats for context — e.g. Rajiv Dadlani / Lilac Capital, Jul 2026).

## What's inside a WhatsApp export zip

- `WhatsApp Chat with <Name>.txt` — the FULL conversation, plain text, chronologically ordered
- `IMG-YYYYMMDD-WA####.jpg` — photos/screenshots
- `STK-YYYYMMDD-WA####.webp` — stickers (noise, skip)
- `VID-...`, `AUD-...` — media
- PDFs / decks / documents shared in-chat (e.g. `Truliv Pitch 2023 Dec version 2.pdf`, `SpaceFields - Deep Tech - Invt Opportunity.pdf`, `Markytics.ai - Invt Deck.pdf`)

## Intake workflow

1. **Extract** to a scratch dir (keep a stable path for reuse across turns):
   ```bash
   mkdir -p /data/hermes/<matter>_work/whatsapp
   unzip -o -q "<zip>" -d /data/hermes/<matter>_work/whatsapp
   find <dir> -type f | wc -l   # quick inventory
   ```

2. **Read the .txt ENTIRELY** — it is the primary source. 500-600 lines is typical for a 2-3 year chat. Parse the format:
   - `dd/mm/yyyy, HH:MM - <Name>: <message>` — each line is a message
   - `IMG-...jpg (file attached)` — media marker, followed by a caption line
   - `Your security code with <Name> changed` — device change, ignore
   - Blank/missing messages = media without caption

3. **Extract business facts, not chat chit-chat:**
   - Projections and numbers (capture BOTH sides of any correction — e.g. Nishant sent "FY25 ₹80Cr", Rajiv corrected to "₹85Cr"; the corrected version is authoritative)
   - Commitments and timelines (fundraise rounds, investor updates promised, meeting dates)
   - Exit asks / sale requests (who asked, when, what route — secondary sale, existing investors, IPO/acq)
   - Contact identifiers: **email addresses stated in-chat** (e.g. `rajadadlani@hotmail.com` confirmed in-chat) → use as Gmail search terms
   - Entity name variants (Lilac, Lilac Ventures, Lilac Hospitality, Lilac Capital — all one investment)
   - **The legal entity name often differs from the chat's colloquial name.** Chat says "Lilac"; the actual company is **"Lilac Insights"** (Lilac Insights Pvt Ltd, CIN U85191MH2011PTC217513) — revealed by Gmail subject lines ("Lilac Insights - Investor Update - ..."). Find it by running the Gmail sweep with the chat name AND checking subjects; then re-run with the legal name — it will return the most hits. Never file under the colloquial name only.
   - Relationship state changes (condolences, hospital visits) — only when they explain gaps in follow-ups

4. **Classify media:**
   - PDFs → decks/reports: read, file into the dossier folder
   - IMG screenshots → often stock tips, charts, receipts: vision_analyze only if referenced in a decision
   - STK → skip
   - Keep a media index in the dossier (date + sender + subject if identifiable)

5. **Cross-reference with Gmail/Drive** — the chat is the *index*; the emails are the *documents*:
   - Search Gmail: `from:<email-from-chat>`, entity names, "investor update", "share purchase", "SPA"
   - Expect 20+ emails over years for an active investment; download every attachment
   - Match chat claims against email evidence (e.g. chat says "sending investor update this week" → find that update email)
   - **Gmail sweep filtering (verified Jul 2026):** broad queries (`SPA`, `share purchase agreement`, `investor update`) hit the 200-result cap with UNRELATED mail (Ranka project SPAs, transaction alerts). Don't try to read 680 raw hits. Instead: run all queries, dedupe by message ID, then **filter to entity-relevant only** — subject OR from contains the entity name (`lilac`), or from the counterparty email (`rajadadlani`). That collapsed 680 → 95 relevant emails. Then fetch full messages only for the filtered set.
   - **Attachment dedupe by byte size:** the same PDF (SSA, SHA, investor update) arrives via multiple emails (forwards to co-investors). Download all, then dedupe by file size before uploading — e.g. four copies of `SSA_211220` at exactly 6,437,884 bytes = one document. Keep one, note the duplicate sources.
   - **Email-only updates exist:** some investor updates have NO PDF attachment (e.g. Q1 FY2026 — Rajiv's cover email only). Save the email body as a `.txt` correspondence file so the update isn't lost from the archive.

6. **Folder convention (personal financial investment):** `Personal / <Investment Name>` with subfolders `01_Investor_Updates_Reports`, `02_Legal_SPA_Shareholding`, `03_Correspondence`, `04_Analysis`. Name files `YYYYMMDD_Description.pdf`. Add a `WhatsApp_Media` subfolder if the user wants the raw export preserved.

7. **Consolidate pre-existing Drive files (user follow-up, Jul 2026):** after building the tree and uploading, run a Drive sweep (`name contains '<entity>'`, `fullText contains '<entity>'`) to find files that ALREADY live elsewhere on Drive (root, other folders like `DRA Partners Fund 1`). The user expects ONE home for the investment. Pattern:
   - Move the originals into the appropriate new subfolder (`files().update(addParents=..., removeParents=...)`) — preserves original created/modified dates
   - Rename them to match the `YYYYMMDD_Description` convention
   - **Delete your freshly-uploaded duplicates** of those same docs (keep the originals, they carry the history)
   - Verify the final tree by listing each subfolder

## Pitfalls

- **Numbers in chat are often wrong on first pass** — the counterparty usually corrects them. Always prefer the latest/corrected figures and note the correction explicitly.
- **Chat ≠ complete record** — phone calls happen between messages (e.g. "Pls call Me back bro"). Flag gaps where a decision was made off-chat.
- **Don't dump the whole chat into the dossier** — extract facts and file media; keep the raw .txt in the scratch/work dir, not Drive.
- **Stickers and personal photos are noise** — skip unless the user asks to preserve the full export.
- **The zip may arrive via the document_cache path** (`/data/hermes/document_cache/doc_<hash>_<name>.zip`) — unzip from there, don't move it.
- **Google Docs API: sequential insertText at index 1 REVERSES the document.** When building the deep-dive doc section-by-section, inserting each section at `index: 1` prepends it — the final doc reads bottom-to-top. Fix: track a running `idx` starting at 1 and use `idx = end` (after each inserted section) as the next insert point, i.e. append sequentially. Verify by reading the doc back before delivering. (Hit on the Jul 2026 Lilac deep-dive doc — rebuilt once.)
- **Unrelated deal pitches inside the chat** — Rajiv pitches his own deals (Yarn Bazaar, SpaceFields, Markytics, stock tips) inside the same chat. Keep them OUT of the investment's folder; only the chat text about the target investment goes in.

## Verified example — Lilac Insights / Rajiv Dadlani (Jul 2026, executed end-to-end)

- Export: 518-line chat (22 Jun 2023 – 16 Apr 2026) + 25 media files (4 PDFs, rest IMG/STK)
- Key facts extracted: exit sought since Apr 2024; corrected projections FY25 ₹85Cr / FY26 ₹125Cr / FY27 ₹200Cr; exit at 5-7x top-line revenue via IPO/acquisition; founder ₹8Cr share-loan infusion; Rajiv's email `rajadadlani@hotmail.com` confirmed in-chat
- **Legal entity: Lilac Insights Pvt Ltd** (CIN U85191MH2011PTC217513) — colloquially "Lilac" / "Lilac Capital" in chat; all 19 investor update PDFs (Sep 2020–Jul 2026) are titled "Lilac Insights - Investor Update - ...". Search the legal name, not the chat name.
- Investment vehicle: DRA Partners 1 — ₹1,00,01,600 for 1,316 CCPS @ ₹7,600 (Oct 2020 confirmation letter); cohort ~₹47.52 Cr at ~₹159 Cr post-money (Dec 2020 SSA)
- Gmail sweep: 680 raw hits across queries → filtered to 95 entity-relevant → 41 unique docs uploaded (19 updates, 13 legal, 8 correspondence, 1 earlier analysis) + deep-dive Google Doc
- Delivered tree: `Personal / Lilac Capital` → `01_Investor_Updates_Reports`, `02_Legal_SPA_Shareholding`, `03_Correspondence`, `04_Analysis`; 5 pre-existing scattered Drive files moved in and deduped
- The chat revealed Rajiv also pitches unrelated deals (Truliv 2023, SpaceFields May 2025, Markytics Apr 2026) — keep those OUT of the Lilac folder
- The chat revealed Rajiv also pitches unrelated deals (Truliv 2023, SpaceFields May 2025, Markytics Apr 2026) — keep those OUT of the Lilac folder. IMG attachments checked with vision (Apr 2024 academy promo, Aug 2024 IPO-investor list) were also non-Lilac — the chat .txt is the only Lilac-relevant artifact in the export
- **Workflow rule (Nishant, Jul 2026):** for this class of task the user requires **plan approval before processing** — recon (read chat fully, classify media, check vault/token state) → present plan (folder tree, search terms, deliverable, open questions) → wait for explicit go-ahead → only then sweep Gmail/Drive and build. Also surface the OAuth prerequisite up front (`send_oauth_url`) so re-authorization can happen in parallel with plan approval
