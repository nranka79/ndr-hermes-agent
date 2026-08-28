# Multi-Account Targeted Thread Search

**When the user says:** "Can you check that email thread about [topic/entity]" — but the entity name is vague, voice-mangled, or they don't remember which account it was sent from.

**Example trigger:** "We had sent an email to India Law about some matter coming up in Chennai highcourt."

## Workflow

### Phase 1 — Generate Query Variations

Don't assume the user's description is accurate, especially via voice:

| Voice/phonetic input | Likely real entity | Why |
|---|---|---|
| "India Law" | **IndusLaw** | /ɪndɪə lɔː/ vs /ɪndəs lɔː/ — common STT mangling of "Indus" (as in IndusLaw / CMS IndusLaw) |
| "Geo" (in finance/telecom context) | **Jio** | Both pronounced /dʒiːoʊ/ in Indian English |
| "Manipal Hospital" | **Manipal Hospitals** (plural) | Medical entity names commonly drop/append 's' |
| "Saveganapalli" | **Sevaganapalli** or **Savaganapalli** | Kannada place names have multiple accepted spellings |

**Build query variants for each account:**

```python
# Start broad, then narrow
queries = [
    "india law",                    # phonetic match
    "induslaw OR cms-induslaw",     # actual entity
    "india legal",                  # another variant
    "chennai highcourt OR chennai high court",  # court name
    "CMA 742 OR CMA/742",           # case number (if known)
]
```

### Phase 2 — Search All Three Accounts

Always search **all** of Nishant's accounts simultaneously (parallel queries for speed):

```python
from tools.gws_auth import build_service

accounts = [
    ("DRAAS",   "google-draas"),
    ("AHFL",    "google-ahfl"),
    ("Personal","google-gmail"),
]

for label, svc_name in accounts:
    service = build_service("gmail", "v1", service_name=svc_name)
    for q in queries:
        result = service.users().messages().list(userId="me", q=q, maxResults=10).execute()
        # check result.get("messages", [])
```

**Key rule:** Always enumerate all 3 accounts before saying "not found." The user's memory of which account they used is often wrong.

### Phase 3 — Identify the Right Thread

Look for signals that identify the right thread:

| Signal | What to look for |
|--------|-----------------|
| **Law firm domain** | `@cms-induslaw.com`, `@induslaw.com` — confirmed real Indian law firm |
| **Case number format** | `CMA No. 742 of 2026`, `CMA/742/2026`, `CMA 742/2026` |
| **Party names** | Named individuals + company names in subject |
| **Project/land name** | Sevaganapalli / Savaganapalli / Saveganapalli — any variant |
| **Court reference** | "High Court of Judicature at Madras" / "Chennai High Court" |
| **Nishant role in case** | D4/D5, "Respondent", "Appellant" in subject |

**Discard false positives:**
- Newsletters (Economic Times, ETRealty, YourStory) — high keyword overlap
- Old threads from a different case (e.g., 2020 Westbury matter also mentions court)
- Generic "India" or "law" mentions from news feeds

### Phase 4 — Group by Thread and Reconstruct Timeline

Group matching messages by `threadId`, then fetch the full thread:

```python
thread_ids = {}
for msg in msgs:
    m = service.users().messages().get(
        userId="me", id=msg["id"],
        format="metadata",
        metadataHeaders=["From","To","Subject","Date","Message-ID"]
    ).execute()
    tid = m["threadId"]
    thread_ids.setdefault(tid, []).append(m)
```

For the most relevant thread(s), get the full content:

```python
thread = service.users().threads().get(userId="me", id=tid, format="full").execute()
for msg in thread["messages"]:
    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
    # Extract plain text body from nested MIME
    body = extract_plain_text(msg["payload"])
```

**MIME body extraction helper:**

```python
import base64

def extract_plain_text(payload):
    """Recursively extract text/plain from nested MIME parts."""
    if payload.get("mimeType") == "text/plain" and "data" in payload.get("body", {}):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
    if "parts" in payload:
        for part in payload["parts"]:
            result = extract_plain_text(part)
            if result:
                return result
    return ""
```

### Phase 5 — Build the Timeline for the User

Present chronologically:

```
## Case: CMA No. 742/2026 — Madras High Court

**Parties:** S. Pawan Kumar (Appellant) vs Sreenivasa Krishnappa & Ors.
**Our clients:** D4 = Saveganapalli Land Partners, D5 = Nishant Ranka
**Law firm:** CMS IndusLaw (Chennai) — G Vivekanand (Partner), Apsaraa Sridhar (Assoc.)

### Timeline
| Date | Event |
|------|-------|
| Jun 2 | You sent detailed briefing + supporting docs to Vivek |
| Jun 2 | Vivek accidentally forwarded your email back (wrong forward) |
| Jun 3 | You replied "Email has no body" — Vivek: "Sorry wrong forward" |
| Jun 4 | Apsaraa sent Engagement Letter, Requisition List, Vakalatnama |
| Jun 19 | Apsaraa reported court papers served (PDF attached, 7.8 MB) |
| ⬜ | **No response from you since Jun 19** |

### Key Facts
- [2-3 bullet summary of the case substance]
```

## Pitfalls

| Pitfall | Fix |
|---------|-----|
| **Voice-mangled entity names** — The user says "India Law" but means "IndusLaw" | Search phonetic variants AND actual domain names. Always check `@cms-induslaw.com` when the user mentions "India" and "law firm" together. |
| **Scattered threads** — The engagement letter, requisition list, and vakalatnama are all separate threads, not one conversation | Group by date range + subject keywords, then manually reconstruct the timeline. Apsaraa sends separate emails for each document in the same minute. |
| **Empty body on forwarded messages** — Gmail's thread view shows the original in the body but forwarding truncates or strips attachments | Read the ORIGINAL message directly (the sent email, not the forward). The forwarded copy often has no body. |
| **Token expired mid-search** — Three accounts mean 3x token refresh risk | Do a pre-flight identity check on the first account. If it fails, generate auth URLs for ALL three before starting. |
| **Attachment-only emails** — Some emails (engagement letter, reporting letter) have body text only in PDF attachments, not inline | Try the `text/plain` part first (often has a short cover message). The substantive content is in the PDF. |
| **Old court-match false positive** — 2020 Westbury transaction emails also mention court, settlement, etc. | Check dates and case numbers. If no case number matches, it's probably a different matter. |
| **Duplicate "via" forwards** — Emails forwarded through `@draas.com` aliases duplicate content | Check Date header age vs inbox receipt date. Skip emails where sender contains " via ". |
