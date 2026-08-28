# Gmail API Notes

## Draft with attachment — why attachments API doesn't work on drafts

`users().messages().attachments().create` only works on **sent messages**. It returns `AttributeError: 'Resource' object has no attribute 'create'` because the method simply doesn't exist for drafts.

The workaround: build the full MIME message (including attachment bytes) as a `multipart/mixed`, serialize it with `email.generator.BytesGenerator`, base64-url encode it, and pass it to `drafts.create` with `{"message": {"raw": raw_b64}}`. This is the correct and complete pattern.

## HTML Email with Embedded Document Content + PDF Attachment

For sending professional medical/legal dossiers as email, use this pattern:

```python
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import base64

msg = MIMEMultipart('mixed')
msg['To'] = 'recipient@example.com'
msg['Cc'] = 'cc1@example.com, cc2@example.com'
msg['Subject'] = 'Subject Line'

# Alternative part: HTML body + plain text fallback
alt = MIMEMultipart('alternative')
alt.attach(MIMEText("Plain text fallback", 'plain'))
alt.attach(MIMEText(html_body_string, 'html'))
msg.attach(alt)

# Attach PDF
with open(pdf_path, 'rb') as f:
    attachment = MIMEBase('application', 'pdf')
    attachment.set_payload(f.read())
    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', 'attachment',
                          filename='Document_Name.pdf')
    msg.attach(attachment)

# Send as Gmail draft
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
draft = gmail.users().drafts().create(
    userId='me',
    body={'message': {'raw': raw}}
).execute()
```

**HTML Body best practices for embedded dossier:**
- Use the same CSS styling as the PDF for consistency (navy headers, table styling, colored info boxes)
- Keep links clickable: `<a href="drive_link">Label</a>` — these render in Gmail
- Strip page-level CSS (WeasyPrint `@page` rules break Gmail rendering) — use inline or embedded `<style>` without `@page`
- Embed the dossier content like a landing page: situation → key findings → clinical asks → timeline → report index (see `references/weasyprint-pdf-generation.md` for styling)

## Nested MIME body extraction (long threads)

Gmail threads with 35+ messages (common for financial/legal transaction threads with multiple counterparties) may store body text in deeply nested `parts[]`. A flat `for part in payload['parts']` won't find it. Use recursive extraction:

```python
def extract_body(msg):
    body = ''
    # Try direct body first
    data = msg['payload']['body'].get('data', '')
    if data:
        return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
    
    # Recursively walk parts
    def walk(parts):
        for part in parts:
            if part['mimeType'] == 'text/plain':
                d = part['body'].get('data', '')
                if d:
                    return base64.urlsafe_b64decode(d).decode('utf-8', errors='replace')
            if 'parts' in part:
                result = walk(part['parts'])
                if result:
                    return result
        return ''
    
    return walk(msg['payload'].get('parts', []))
```

Also check for `text/html` if `text/plain` is empty — some senders (newsletters, forwarded Substack content, automated notifications) only include HTML. In that case, strip HTML tags or use BeautifulSoup.

## Identifying financial transaction details from long email threads

When searching for a specific transaction (share purchase, property deal, invoice), the initial confirmation email at the start of the thread usually contains the structured data table. Later messages deal with logistics (KYC, document signing, fund transfer). The pattern:

1. Search Gmail for the transaction keywords (e.g. `'NSE Sale' '450' 'Shares'`)
2. Get the full thread with `format='full'`
3. Find the earliest message with "confirm to sell" / "confirms" / "purchase" in the body — that's usually the deal confirmation with the rate table
4. Parse the table/structured data from that message (buyer, seller, quantity, rate, total consideration, charges)
5. Check later messages for payment instructions (bank account, deadline) to confirm the deal went through

The last message in the thread is NOT necessarily the resolution — check for completion confirmations or follow-up questions about documents.

## MIMEBase vs MIMEApplication for binary attachments

`MIMEBase` requires you to `.set_payload(binary_data)` before calling `encoders.encode_base64()`. If you call `encode_base64` on a `MIMEBase` instance where the payload hasn't been set or has been set to None, it raises `TypeError: expected bytes-like object, not NoneType`.

`MIMEApplication` is purpose-built for binary files (docx, pdf, xlsx, etc.) and avoids this whole class of error. Prefer it.

## Drive get_media vs export

A Drive file stored as a Google Docs/Sheets/Slides native file:
- `get_media()` → 403 "Only files with binary content can be downloaded"
- `export()` → works

A Drive file stored as a binary (.docx, .pdf, .xlsx):
- `export()` → 403 "Export only supports Docs Editors files"
- `get_media()` → works

Always determine the file type first.

## Mamatadr Rathod contacts

Two email addresses found via Google People API:
- `mamatadr@gmail.com` (personal)
- `maadi32@gmail.com` (personal)

Used `mamatadr@gmail.com` for the CC in the Section 66 commitment letter draft sent to drr@draas.com.

## Downloading .docx / .pdf / .xlsx attachments from Gmail messages

Gmail returns message metadata in `payload.parts[]`. Each part that is a real attachment has `filename` set + a `body.attachmentId` (NOT a `body.data` — attachments don't inline-decode like message bodies). To download the bytes:

```python
# 1. Get the message
md = gmail.users().messages().get(userId="me", id=msg_id, format="full").execute()

# 2. Walk parts to find the attachment
for p in md["payload"].get("parts", []):
    if p.get("filename", "").endswith(".docx"):
        att_id = p["body"]["attachmentId"]
        # 3. Fetch the attachment bytes
        data = gmail.users().messages().attachments().get(
            userId="me", messageId=msg_id, id=att_id
        ).execute()
        # 4. The 'data' field is base64url-encoded — decode
        import base64
        raw = base64.urlsafe_b64decode(data["data"])
        with open("/tmp/output.docx", "wb") as f:
            f.write(raw)
```

Common gotchas:
- Use `format="full"` (not `metadata`) — `metadata` strips the `parts` tree and you can't see attachments.
- A blank-subject email with `format="full"` still has the parts tree. Never assume there's no attachment just because subject is empty. Always iterate `parts` and check `p.get("filename")` + `p.get("body", {}).get("attachmentId")`.
- `attachmentId` is the right field to grab. `body.data` will be absent for real attachments even if the part has inline content.
- Filename may not have a clean extension (counterparty often renames to all-caps, adds typos, or uses Unicode). Match on substring or mimeType (`application/vnd.openxmlformats-officedocument.wordprocessingml.document` for .docx, `application/pdf` for .pdf) rather than `endswith()`.
- Counterparty-revised deeds/contracts are often 3–4 MB even when the original draft was 18 KB — that's because the redlined version embeds scanned signature images. Don't be alarmed by the size; `python-docx` reads paragraphs identically.

## Counterparty redlined-contract diff workflow (python-docx + SequenceMatcher)

When a counterparty sends back a redlined .docx version of a deed/contract, the right diff approach is **not** `difflib.unified_diff` on raw text — it produces noise from formatting differences. The reliable workflow:

1. **Extract paragraphs** with `python-docx`, dropping empties:
   ```python
   from docx import Document
   d = Document(path)
   paras = [p.text.strip() for p in d.paragraphs if p.text.strip()]
   ```

2. **Align with `difflib.SequenceMatcher`** on the *list* of paragraphs (it handles inserts/moves correctly; `unified_diff` does not):
   ```python
   from difflib import SequenceMatcher
   sm = SequenceMatcher(None, n_pars, a_pars)
   for tag, i1, i2, j1, j2 in sm.get_opcodes():
       if tag == "equal": continue
       # tag is "replace", "insert", or "delete"
   ```

3. **Counterparty redlines are often produced by literally typing new text *over* the old text in Word's "Track Changes" view with revisions not properly accepted.** A single paragraph may contain both old + new content separated by stale fragments — e.g.:

   `Rs. 2,00,000 (Rupees Two lakhs only)1,75,000/- (Rupees One Lakh Seventy-Five Thousand Only)`

   Surface these inline "fragments" as separate bullet items in the change summary rather than picking one number. The human reviewer needs to see both halves to know what was actually changed (rent increased from 1,75,000 to 2,00,000 in this example).

4. **Group changes by clause number** when presenting to the user (Cl. 2 Tenure, Cl. 4 Rent, Cl. 5 Handover, Cl. 6 SD, etc.) — it's the only way a busy principal can act on the diff without re-reading 30 pages of legal text.

5. **Also extract and quote the email body instructions** — Indian counterparties often write "Pls remove X wherever mentioned" in the email body but their redlined .docx only partially implements the instruction. Both must be presented and conflicts flagged (e.g. "email says REMOVE India Chai name, but the .docx only added 'existing Ground floor Tenant' prefix — which do they actually want?").

## Identifying the right "to" / "from" address for counterparty threads

Indian business counterparties often have a personal-style address (`akber@ahindia.com`) and a separate accounts/admin/PA address (`padirector@ahindia.com`) — both may be on the same thread. The PA/account address usually sends the formal redlined documents and is the one to search for to find the latest redline.

Always search by domain (`ahindia`, `xyz.in`, etc.) rather than by the contact name when the to/from of the original message used a different alias than you expect — e.g. `from:domain.com` returns the full thread including admin/PA forwards. The thread is often 3-4 messages long with the redline on the last admin/PA message, not the most recent personal-address message.
