# Requisition List → Survey-wise Checklist Sheet → Threaded Email

Recurring DRA land-matter workflow: an advocate emails a Word-document "requisition list"
(list of documents to be procured per survey number, usually assigned to a colleague).
User asks to convert the whole doc into a spreadsheet checklist (Survey Number | Document),
file it in the project folder, and email the assigned colleague with the original email
forwarded and the sheet link.

Validated 2026-08-25: Katenahalli (Riverstone) "Version 2 - Rahul - List of Documents
Required" 24-table docx → 46-row checklist → filed → threaded draft to Vinod Kumar Das
(CC Aamir).

## 1. Finding the right email when the name search fails

Voice transcription garbles both the person and the place:
- "Prasannakumar Advocate" → **Prasanna Swaminathan** (prasannaswaminathan91@gmail.com),
  the title-due-diligence advocate for Katenahalli/Riverstone (also author of "Status of
  Ongoing Assignments", "List of Documents Reviewed - Sy. No. 302", Sy. No. 38-6 title report).
- "Katnalli"/"Katenalli"/"Katenhalli"/"Kathnalli" → **Katenahalli** Village, Somenahalli
  Hobli, Gudibande Taluk, Chikkaballapur District (= the "Riverstone" project family, Sy. 114/1 etc.).
- "Rahul" (in this doc-procurement context) = **Vinod Kumar Das**, vkdas@draas.com.
  The docx tables say "To be procured by: Rahul" — Rahul is the colleague, not a separate contact.

Gmail search reality: `from:prasannakumar` and `Katnalli` return 0 hits; the message came to
NDR as a **forward from Aamir Khan** (aamirkhan@icloud.com) with subject
"Fwd: Katenahalli Properties - List of Docs to be Collected - Mr. Rahul".
Working queries: `'Rahul documents'`, `'list of documents to be collected'`,
`subject:(Katenahalli Properties)`. The thread may be a single-message forward; read the
forwarded body to recover the ORIGINAL sender/date/Cc (Prasanna → Aamir, Cc Syed Muqhtadir
Hussain legal.smhussain@gmail.com + Keerthi Jallipalli).

## 2. Parsing the docx requisition tables

No python-docx needed — lxml on `word/document.xml` is enough. Walk `body` children IN ORDER;
each table sits under a preceding "DESCRIPTION OF THE SCHEDULE PROPERTY:" paragraph that
names the survey number(s). Algorithm:
- On a paragraph containing 'SCHEDULE PROPERTY' or starting 'All that piece and parcel',
  start a new survey context and collect `Sy. No. <n>` matches.
- Continuation paragraphs ('Sy. No. 125/3 measuring …;') extend the CURRENT context — a
  single block can list MULTIPLE survey numbers (125/2,3,4,5) and one table applies to all
  of them. Accumulate, do not overwrite; dedupe preserving order.
- For each `w:tbl`, skip rows until the header (contains 'Sl. No'), then each data row is a
  document. Document text is cell index 1; procured-by is cell index 2.
- Emit ONE row per survey number for multi-survey blocks (125/2..125/5 each get the nil
  tenancy row) so the checklist is tickable survey-wise.
- Keep the verbatim doc text even when it looks wrong (120/1 and 122/1 tables both cite
  "in respect of Sy. No. 120/2") — do not editorialise the advocate's list.

## 3. Building + filing the spreadsheet

- Check Drive FIRST for an existing tracker (name contains '<project>'). There was a July
  "Katenahalli - Rahul Document Requisition Tracker" (owned by vkdas, folder "Katenahalli
  Legal Documents") with a partial/older list. The V2 doc supersedes; create a NEW sheet
  with the convention name rather than clobbering the colleague's file.
- Name: `YYYYMMDD_Katenahalli_Rahul_Document_Requisition_Checklist`, parents = project legal
  folder (canAddChildren check — folder owned by vkdas was writable).
- Columns: `Sl No | Survey Number | Document Required | To be Procured by | Priority | Status (Obtained?)`.
  Priority blocks (user-named parcels) sorted FIRST and highlighted amber via
  `repeatCell` backgroundColor; freeze header row; autoResizeDimensions.
- Sharing: assigned colleague = writer (vkdas@draas.com). Email CC'd participants often have
  NON-Google addresses — see icloud pitfall below. Verify with `permissions().list()` after.

## 4. icloud / non-Google invite pitfall

`permissions().create(emailAddress='aamirkhan@icloud.com')` → HttpError 400
`invalidSharingRequest`: "As there is no Google Account associated with this email address,
you must tick the 'Notify people' box to invite this recipient."
Fix: grant `{'type':'anyone','role':'reader','allowFileDiscovery':False}` instead (the link
goes in the email body anyway), or use the recipient's Google-linked address
(khan.hussain.aamir@gmail.com is Aamir's Google account even though he sends from icloud).

## 5. The email: threaded reply, forward + attach + link

Draft (DRAFT only, never auto-send) on the SAME thread the email arrived in:
- To = assigned colleague (verified from Gmail `from:vkdas@draas.com` history), Cc = who
  forwarded it to you. Subject `Re: Fwd: <original>`.
- In-Reply-To/References = REAL Message-ID — fetch via
  `messages().get(format='metadata', metadataHeaders=['Message-ID'])`, NOT regex on raw
  (see email-drafter SKILL.md pitfall).
- Body: converted the Word doc into a checklist spreadsheet (link), use it survey-wise;
  **priority parcels first, then the rest**; ask colleague to urgently confirm timeline and
  cost (cost discussed with NDR).
- Include the original "---------- Forwarded message ---------" block verbatim and ATTACH the
  original docx (EmailMessage.add_attachment; draft_reply_create does NOT support attachments).
- Verify: `drafts().list()` contains it, threadId matches source, labelIds contains DRAFT,
  attachment present in payload parts.