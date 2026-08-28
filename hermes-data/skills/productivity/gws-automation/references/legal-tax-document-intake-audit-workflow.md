# Legal/Tax Document Intake + Gmail Audit Workflow

**Class:** Workflow — User shares a Drive link to a legal/tax document (ITAT notice, demand notice, court order, etc.) → analyze → rename → file → check Gmail for related correspondence → trace who's handling it → report full picture.

**Trigger:** User shares a Drive link to a legal/tax document and asks you to "check my email" / "find out if this is being handled" / "see what's been sent about this" — typically mentioning specific people by name.

## Workflow

### Phase 1 — Read the document from Drive

Get the file ID from the shared Drive link (the trailing ID after `/d/` and before `/view`) and rename it per DRAAS convention:

Format: `YYYYMMDD_TaxpayerName_DocumentType_Details.pdf`

Key elements to extract from the notice:
- **Issuing authority** (NFAC, ITAT, CIT(A), ITO, etc.)
- **PAN** of the taxpayer
- **Assessment Year(s)**
- **Section** (u/s 250, 143, 148, etc.)
- **Notice ID** (e.g. `1068145049(1)`)
- **Nature** (Set Aside, Hearing, Demand, etc.)
- **Response deadline** if any

Example: `20240829_Dinesh_Ranka_ITAT_SetAside_Notice_AY2011-12.pdf`

### Phase 2 — Drive operations

1. **Check if already in correct folder** — use `drive.files().get()` on the file to see its parents
2. **Search for target folder** by name with `drive.files().list(q="name='...' and mimeType='application/vnd.google-apps.folder'")`
3. **Suggest name + folder** to user, confirm before executing
4. **Rename** with `drive.files().update(fileId=..., body={'name': '...'})`
5. **Check for duplicates** — query same folder by PAN substring or notice ID
6. **If duplicate exists**, flag it for user decision (don't delete unilaterally)

### Phase 3 — Gmail audit: find related correspondence

Search across multiple queries using the PAN, taxpayer name, notice ID, assessment year, and section number:

```python
queries = [
    "PAN_ABHPR8430M",
    "Dinesh Ranka ITAT",
    "1068145049",
    'subject:"Hearing Notice" subject:"Set Aside"',
    "section 250 AY 2011-12",
]
```

For each query, get message metadata (Date, From, To, Subject) to find relevant threads.

### Phase 4 — Name resolution

The user may refer to people phonetically or by short names. Cross-reference what the user says with email addresses found in Gmail:

| User says | May be |
|-----------|--------|
| "Genita" | **Jinita** Chatterjee (Advocate) |
| "Parthasarathi sir" / "Partha sir" | **Parthasarathi** Srinivasan (parthalawyer@gmail.com) |
| "Ishwari" / "Eshwari" | **Eshwari** Chamundeshwari (echamundeshwari@draas.com) — DRAAS Accounts |

Always check CC and To fields of emails found — the people involved may be CC'd on threads even if not the primary recipient.

### Phase 5 — Build the timeline

Fetch full bodies (not just metadata) for the key messages in the thread. Extract:

1. **Original receipt** — when was the first notice in this series received?
2. **Forwarding chain** — who forwarded it to whom? (Dharmesh → Nishant → others)
3. **Response evidence** — was a response filed? (Look for e-filing acknowledgements, `communication@cpc.incometax.gov.in`, "successfully submitted" emails)
4. **Who was engaged** — Khushroo, Bhagya, Jinita, Parthasarathi — who did what?
5. **Current handler** — who is actively managing it now?
6. **Status/Outcome** — was the matter resolved, is it pending, is it remitted?

Format for reporting to user:
```
📅 Timeline:
| Date | Event |
| Jan 2024 | Notice received → engaged Parthasarathi & Associates |
| Aug 2024 | This notice received → response filed Sep 2024 |
| Dec 2025 | ITAT Order passed → [key outcomes] |
| Today | Current status: [handled by X, next step is Y] |
```

### Phase 6 — Determine conclusion

[existing content...]

### Phase 7 — Draft follow-up email on same thread

After reporting the timeline and conclusion, the user often asks you to draft a follow-up email that replies to the same thread. This is the complete sequence:

1. **Identify the latest message in the thread** to reply to:
   ```python
   thread = gmail.users().threads().get(userId='me', id=thread_id).execute()
   latest_msg = thread['messages'][-1]
   ```

2. **Get the parent Message-ID** for threading headers:
   ```python
   parent = gmail.users().messages().get(
       userId='me', id=latest_msg['id'],
       format='metadata',
       metadataHeaders=['Message-ID']
   ).execute()
   parent_msg_id = {h['name']: h['value'] for h in parent['payload']['headers']}['Message-ID']
   ```

3. **Build the MIME message** with proper threading headers:
   ```python
   msg = MIMEMultipart('alternative')
   msg['From'] = 'Nishant Ranka <ndr@drahomes.in>'
   msg['To'] = 'primary@example.com, secondary@example.com'
   msg['Cc'] = 'cc1@example.com, cc2@example.com'
   msg['Subject'] = 'Re: [Original Subject]'
   msg['In-Reply-To'] = parent_msg_id
   msg['References'] = parent_msg_id
   ```

4. **Include both plain text and HTML** alternatives:
   ```python
   msg.attach(MIMEText(text_body, 'plain'))
   msg.attach(MIMEText(html_body, 'html'))
   raw = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
   ```

5. **Save as draft** with the thread ID:
   ```python
   draft = gmail.users().drafts().create(
       userId='me',
       body={'message': {'raw': raw, 'threadId': thread_id}}
   ).execute()
   ```

6. **Confirm to the user** — the draft is in their Gmail Drafts folder for review.

#### Email content structure for tax/legal follow-ups

- **Status follow-up on pending items** — reference the last known action point
- **Specific numbered questions** (refund status, finality of order, remitted matters)
- **Tag specific people** with @mentions in the body for action items
- **Politely note** any unfulfilled prior requests (e.g., "Arun Sir had requested you meet with the order copy")

#### Address mapping for Nishant's circle

| User says | Actual email |
|-----------|-------------|
| Parthasarathi Sir / Jinita | parthalawyer@gmail.com (shared) |
| Arunkumar / Arun Sir | arunkumarms1158@gmail.com |
| Manish / MDR | mdr@draas.com |
| Mamta / Manta | mamatadr@gmail.com |
| Khushroo / Kushru | khushroo@draas.com |
| Ro / Roshini | rnr@draas.com |
| Bhagya | admin2.blr@drahomes.in |

> ⚠️ **Nishant sends from ndr@drahomes.in** — confirmed preference for all outbound email.

Answer these questions explicitly:
- **Is this being handled?** Yes/No + by whom
- **Has it already been responded to?** Check for filed responses
- **Is anyone else involved?** List all people on the thread
- **What's the current status?** Pending, resolved, remitted, awaiting next hearing
- **Does the user need to do anything?** Follow up with counsel, upload documents, etc.

## Pitfalls

- **"Genita" ≠ "Genita"** — search for "Jinita" and "Jinita" as well. The advocate's name is Jinita Chatterjee.
- **Separate threads for same PAN** — tax demand notices (outstanding demands) and ITAT hearing notices are different matters. Don't confuse them even if they share a PAN.
- **Multiple AYs** — the same PAN may have notices for different assessment years (2011-12, 2013-14, 2007, 2021). Keep the AY you're investigating straight.
- **Users forwarding to each other** — the forwards chain (Dharmesh → Nishant → Bhagya → Jinita) is how the document moved. Trace it fully.
- **Auto-generated responses** — `communication@cpc.incometax.gov.in` sends automated "successfully submitted" acknowledgements. These are proof of filing, not human correspondence.
- **Name mismatch in email** — Nishant uses both `ndr@draas.com` and `ndr@drahomes.in`. Search both.

## Verified session

**18 Jun 2026 — Dinesh Ranka ITAT Set-Aside Notice (AY 2011-12):**
- Notice ID: 1068145049(1), dated 29 Aug 2024
- PAN: ABHPR8430M
- Already in DR ITAT folder on Drive
- Gmail traced back to Jan 2024 → ongoing handling by Jinita Chatterjee / Parthasarathi & Associates
- Multiple rounds of response filed (Sep 2024, Oct 2024, Aug 2025)
- ITAT Order passed Dec 2025: Capital gains allowed, bad debts upheld, professional charges remitted to CIT(A)
- Eshwari emailed separately about a different matter (tax demand notice for outstanding demands ₹11.3L + ₹42K)
