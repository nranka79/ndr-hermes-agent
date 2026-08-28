# Document Intake & Drive Filing Workflow

When a user sends/mentions a document (PDF, image, scan) and asks you to file it appropriately on Drive — not just upload anywhere, but understand what it is first, then name and place it correctly.

## Workflow

### Step 1: Read the document
Use `vision_analyze` (for images/PDF screenshots) or the document's Telegram message context to understand what the document is about. Don't ask the user to explain what they just sent — they expect you to scan it first.

### Step 2: User provides context (if needed)
The user may follow up with a voice message or text explaining what the document is, e.g. "this is the premium FAR single judge order." They are NOT repeating themselves — they are confirming/qualifying what you already read. Listen for:

- The **subject** (what case, notification, property)
- The **jurisdiction/type** (single judge, double bench, Supreme Court)
- The **outcome** (dismissed, upheld, quashed, pending)
- Why it matters (e.g. "TDR value will become less, haphazard development") — this is your context for understanding, not necessarily for the filename

### Step 3: Rename per DRAAS convention
Format: `YYYYMMDD_Project_DocumentType_Author.pdf`

- Date = content date (e.g. judgment date), NOT upload date
- Use meaningful document type, not generic ("Premium_FAR_Order" not "Court_Document")
- Include case number if helpful (e.g. `WA_1983_2025`)
- Keep underscores between segments, no spaces

Example: `20260615_Karnataka_HC_Double_Bench_Premium_FAR_Order_WA_1983_2025.pdf`

### Step 4: Identify the correct Drive folder
For legal/government/regulatory documents, the folder is typically:

- **Main location**: `My Drive → RnD → Bangalore` (for Karnataka-related documents)
- The user may say "mostly under R&D Bangalore" — this is a strong signal that's the target
- If you need to verify, use `drive.files().list()` to search for the folder name
- For Bangalore-specific orders, the `RnD/Bangalore` path is the default

### Step 5: Confirm with the user
Before uploading, tell the user:
- What you renamed it to
- Which folder you found (show the Drive path)
- Ask for confirmation: "Upload to [folder] as [filename]?"

The user said "confirm the folder location, confirm the name and upload" — they want explicit confirmation, not a multi-option suggestion list. Just state what you found and ask yes/no.

### Step 6: Upload
Use `drive.files().create()` with parents set to the folder ID. After upload, verify the file exists with `drive.files().get(fileId=created_id)` and return the link.

## Pitfalls

- **Don't guess the folder.** If you can't find the RnD/Bangalore folder, say so — don't upload to a random folder or root.
- **Don't upload before confirming.** The user explicitly asked for confirmation in this workflow. Skip the "how about this alternative suggestion" step — they know where they want it.
- **Don't over-describe the document.** A short summary is fine, but the user already knows what it is. They want: name + folder location + confirmation, not a re-analysis.
- **Date = judgment date, not today's date.** If the order is dated June 15, 2026, the filename starts with `20260615`. Check the document for the date.
- **Vision-analyzing a PDF** — for PDFs, the document pages may be rendered as images. `vision_analyze` works on these but you may miss metadata. If available, also check the Telegram document's filename (it may contain the original name).

## Extending to Gmail audit

When the user then asks you to "check my email" / "see if this is being handled" / "find related correspondence" for the document you just filed, follow the **legal-tax-document-intake-audit-workflow** reference under this same umbrella. That covers: searching Gmail by PAN/notice ID, tracing the forwarding chain, determining who's handling the matter, and reporting current status.
