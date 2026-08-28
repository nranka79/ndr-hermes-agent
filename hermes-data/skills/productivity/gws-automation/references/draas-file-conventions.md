# DRAAS File & Drive Conventions

## File Naming
Format: `YYYYMMDD_Project_DocumentType_Author.ext`
- Date = content/creation date, not upload date
- When the document's content date isn't known (unnamed renders, generic scans, CAD exports), use Drive's `createdTime` metadata as the date prefix
- If the filename already carries a date (e.g. `FINAL_MM_07-05-2026.dwg`), leave it alone — it already follows a convention even if not in YYYYMMDD format
- Project short name (e.g. RankaOasis, RankaIris)
- Document type (e.g. MarketingOffice_3DRenders, Renders_GPTEnhanced)
- Author/variant (e.g. Bhuvanesh, GPTEnhanced)

Example: \`20260616_RankaOasis_MarketingOffice_3DRenders_Bhuvanesh.pdf\`

## Drive Folder Consolidation
When design/marketing/collateral files are scattered across multiple Drive locations:
1. Scan all relevant folders for the project
2. Propose one umbrella folder per project: \`ProjectName — Design & Marketing\`
3. Structure child folders by type: Marketing Office Renders/, Villa Renders/, Entrance Concepts/, Brochures/, Site Photos/, Master Plans & Floor Plans/, References/
4. Get user confirmation before moving files (can break existing links)
5. Move files using drive.files().update(fileId=id, addParents=newParentId, removeParents=oldParentId)

## Drive Permissions
Grant editor access to collaborators:
- drive.permissions().create(fileId=folderId, body={'type': 'user', 'role': 'writer', 'emailAddress': user.email}).execute()
- Common DRAAS collaborators: Gowri Singh (gsingh@draas.com), Roshini Ranka (rnr@draas.com)
- Set on parent folder so it propagates to sub-items

## Personal Folder Hierarchy

Nishant's Drive root has a **Personal** folder for individual/family documents. When placing personal financial documents:

1. **Create/use a `Finance` subfolder** inside `Personal/` for bank statements, investment docs, tax records
2. **Name format:** `YYYYMMDD-YYYYMMDD_Account_Type_Desc` (e.g. `20250102-20260714_Kotak_9880055634_Statement`)
3. **Share** with Roshni (rnr@draas.com) as writer for family financial visibility
4. **Generate a WhatsApp message** with the Drive link when sharing — use the `whatsapp_link` tool with Roshni's phone (9845026390 appended to 91)

**Known subfolders under Personal:** `Finance`, `Gift Deed`, `Research`, `Travel`, `Family`, `RNR`, `Ruhaan`, `Rivaan`, `Invitations`, `World of Visa`, `DDR`

**Do NOT** place personal finance docs under business folders (DRA Group, individual project folders) — they belong in Personal > Finance specifically.

## WhatsApp Message Delivery
When user asks to send a message via WhatsApp:
1. Draft message in WhatsApp markdown format
2. Present inside a code fence for direct copy-paste into WhatsApp Web
3. WhatsApp formatting: *bold*, _italic_, ~strikethrough~, ||spoiler||, \`inline code\`, raw URLs
4. No triple backticks inside WhatsApp content itself
5. Use raw URLs, not [text](url) markdown links
