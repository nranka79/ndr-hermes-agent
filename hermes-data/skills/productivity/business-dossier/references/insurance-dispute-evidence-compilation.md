# Insurance Dispute — Evidence Compilation & Legal Brief

Pattern for investigating an insurance/policy dispute from Gmail threads, cataloguing evidence, running parallel legal analysis, and producing a comprehensive HTML legal brief.

## When to Use

- User asks to "understand the email chain" about an insurance policy dispute
- Task involves: analyze email chain → identify evidence → research legal framework → compile into a document for IRDAI/consumer forum filing
- The deliverable is a structured HTML document (not a Google Doc) with timeline, evidence inventory, violation analysis, and legal strategy

## Workflow

### Phase 1: Gmail Investigation

1. **Search by policy number first** — insurance threads are easier to find by policy/claim number than by company name:
   ```python
   from tools.gws_skill_bridge import call
   import json
   
   resp = call('gmail_search', service_name='google-draas',
       query='0444146783',  # policy number
       max=50)
   results = json.loads(resp)
   ```

2. **Identify the main thread** — look for the longest-running thread (most messages, widest date range). That's the chronological spine.

3. **Get the full thread content** — use `gmail_thread_get` to grab all messages:
   ```python
   resp = call('gmail_thread_get', service_name='google-draas',
       thread_id='19f5261e7bac02a5')
   ```

4. **Extract full MIME bodies for complex emails** — when `gmail_get` returns empty body (multipart with attachments), use `build_service` directly with `format='full'`:
   ```python
   from tools.gws_auth import build_service
   import base64
   
   gmail = build_service('gmail', 'v1', service_name='google-draas')
   
   def extract_all_text(payload):
       text = ''
       if payload.get('body', {}).get('data'):
           data = payload['body']['data']
           text += base64.urlsafe_b64decode(data + '===').decode('utf-8', errors='replace')
       if payload.get('parts'):
           for part in payload['parts']:
               text += extract_all_text(part)
       return text
   
   msg = gmail.users().messages().get(userId='me', id='MESSAGE_ID', format='full').execute()
   full_body = extract_all_text(msg['payload'])
   ```

5. **Search for related historical emails** — policy bond, renewal confirmations, reversal notifications:
   - Search by policy number alone
   - Search for "Renewal Payment Confirmation" + policy number
   - Search for "Policy Bond" + entity name

### Phase 2: Evidence Cataloguing

Build a structured evidence inventory table. For each key email, record:

| Field | Example |
|-------|---------|
| **Message ID** | `19764731da15443f` |
| **Date** | `Thu, 12 Jun 2025 19:32:19 +0530` |
| **From** | `online@bajajallianz.co.in` |
| **Subject** | `Renewal Payment Confirmation for Policy No: 0444146783` |
| **Significance** | Key contradiction: sent 1 month AFTER reversal |
| **Status** | `On record` / `Submitted` / `Bounced` / `KEY` |

Categorise evidence into:
- **In possession** (bank statements, medical reports, policy bonds, email confirmations)
- **Requested but not provided** (TMT reports, corrected MER, functional email address)
- **Procedural failures** (bounced emails, missed TATs, no lapse notice)

### Phase 3: Parallel Legal Research

Use two models simultaneously: the main model for factual analysis + OpenRouter GPT-4o for legal framework:

```python
from hermes_tools import call_openrouter_model

legal_analysis = call_openrouter_model(
    user_trigger_phrase='use openrouter gpt to analyze [case]',
    model='openai/gpt-4o',
    prompt=f'''You are a legal analyst specializing in Indian insurance law.
    Analyze this case: [timeline + violations + policy details].
    Cover: IRDAI PPI Regulations 2024, Insurance Act Sec 45,
    Consumer Protection Act 2019, Insurance Ombudsman Rules 2017,
    step-by-step legal strategy, evidence needed, precedents,
    30-day action plan, risk assessment.'''
)
```

Key areas to cover in the legal analysis prompt:
- **IRDAI PPI Regulations 2024** — specific violation mapping
- **Insurance Act 1938, Section 45** — policy incontestability after 2 years
- **Consumer Protection Act 2019** — deficiency of service (Sec 2(11)) + unfair trade practice (Sec 2(47))
- **Insurance Ombudsman Rules 2017** — jurisdiction, procedure, award limits
- **Step-by-step strategy** — Bima Bharosa → Ombudsman → Consumer Forum (determine correct forum based on sum assured)
- **30-day action plan** — what to file, when, with which evidence

### Phase 4: Build the HTML Legal Brief

Create a self-contained HTML document. Required sections:

1. **Executive Summary** — 3-4 paragraphs covering: policy details, core issue (insurer's unilateral act causing lapse), current status, recommended action
2. **Status Dashboard** — key numbers as cards (years paid, total premium, days stalled, sum assured at risk)
3. **Complete Chronological Timeline** — table grouped by phases (policy in force → the reversal → revival stall → decline)
4. **Evidence Inventory** — two tables: documents in possession (with Gmail message IDs) + documents requested but not provided
5. **Legal Violations** — one card per violation, each with: regulation cited, what happened, why it's a violation
6. **Legal Framework** — relevant provisions (Section 45, CPA 2019, IRDAI PPI Regs) with application to the case
7. **Legal Strategy** — three parallel tracks: IRDAI Bima Bharosa → Insurance Ombudsman → State Consumer Commission
8. **30-Day Action Plan** — days 1-7 (emergency), 8-14 (counsel + docs), 15-30 (filings)
9. **Key Arguments & Defenses** — strongest arguments + likely insurer defenses with counter-arguments
10. **Risk Assessment** — SWOT analysis + outcome scenarios with probabilities

### Phase 5: Upload to Drive TMP

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

drive = build_service('drive', 'v3', service_name='google-draas')

# Find TMP folder
results = drive.files().list(
    q="name='TMP' and mimeType='application/vnd.google-apps.folder' and trashed=false",
    spaces='drive', fields='files(id, name)'
).execute()
tmp_id = results['files'][0]['id']

# Upload
media = MediaFileUpload(local_path, mimetype='text/html', resumable=True)
uploaded = drive.files().create(
    media_body=media,
    body={'name': filename, 'parents': [tmp_id], 'mimeType': 'text/html'},
    fields='id,name,webViewLink'
).execute()
```

## Pitfalls

- **`gmail_get` may return empty bodies for multipart emails** — the bridge's `gmail_get` only extracts inline text. For emails with complex MIME structures (HTML+attachments), use `build_service` + `format='full'` with recursive MIME part extraction.
- **`draft_create` needs `html=True` for HTML content** — without it, the HTML code renders as raw text in Gmail compose view (see email-drafter skill).
- **Gmail message IDs are stable across the session** — you can reference them in the HTML document as evidence identifiers.
- **Bounced email receipts are evidence too** — they prove the insurer provided a non-functional communication channel. Save the NDR (Non-Delivery Report) message IDs.
- **Search across all accounts** — insurance correspondence may be in an alternate account (e.g., ndr@drahomes.in for Bajaj Life but ndr@draas.com for the formal complaint). Use multi-account search.
- **The "Renewal Payment Confirmation" after reversal is a critical contradiction** — this email, sent by the insurer's own system after the reversal date, proves the system accepted the payment. It's the strongest single piece of documentary evidence.
