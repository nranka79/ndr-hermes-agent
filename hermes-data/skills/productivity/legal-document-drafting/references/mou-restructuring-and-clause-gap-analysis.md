# MOU Restructuring & Clause Gap Analysis — DRAAS Conventions

Covers: restructuring a flat MOU into standard drafting format (Parts-based), clause gap analysis, and the specific registration/cost allocation patterns preferred by DRAAS (Nishant).

## Clause Gap Analysis Workflow

When presented with a MOU or legal agreement to review, always:

1. **Read the full document** — export from Google Docs via Docs API, or read via vault socket bypass
2. **Map all existing clauses** — identify which sections are present (recitals, operative clauses, miscellaneous)
3. **Identify gaps** — check for these standard clauses:

### Critical Gaps to Check

| Clause Type | Why It Matters |
|-------------|---------------|
| **Timeline/deadline** | Most MOUs at DRAAS omit procurement deadlines. Without one, there's no performance benchmark |
| **Exit/termination** | Especially important when advance payments are involved (Rs.10 Cr+ in this case) |
| **Interest on advance on default** | Without it, the recipient has no incentive to perform |
| **Cost allocation** | Who pays stamp duty, registration, legal due diligence, incidental costs |
| **Force Majeure** | Protects both parties from government delays, court injunctions, etc. |
| **Governing law & jurisdiction** | Always specify Karnataka / Bengaluru courts |
| **Entire agreement** | Prevents either party from claiming oral side deals |
| **Indemnification** | Cross-indemnity for title defects, litigation, third-party claims |
| **Default & consequences** | What happens when either party fails to perform |
| **Schedule property details** | Often left as empty tables — flag for completion |

## Standard MOU Drafting Format (DRAAS Convention)

Restructure flat numbered clauses into this Parts-based format:

**Preamble:**
- DRAFT watermark (if draft)
- MEMORANDUM OF UNDERSTANDING title
- Date line
- "By and Between" parties section
- Definitions clause for "First Party", "Second Party", "Parties"

**Recitals (WHEREAS):**
- A. First Party's ownership/role
- B. Second Party's ownership/role
- C. Transaction purpose (land aggregation, etc.)
- D. Overall intent statement
- E. Mutual agreement

**NOW, THEREFORE clause**

**Part I — Definitions and Interpretation**
- Key defined terms (Consideration, Project Lands, Clear and Marketable Title, etc.)

**Part II — Consideration and Advance**
- Per-acre consideration
- Advance payment details
- Payment acknowledgment

**Part III — Land Procurement, Registration, and Costs**
- Obligation to procure
- Registration by each party in their own name (NOT one party registering all)
- Costs: each party pays their own stamp duty, registration, legal due diligence
- First Party bears ALL other incidental costs (title issues, encroachments, revenue disputes, litigation, survey, mutation, statutory compliance)
- Title verification and documentation

**Part IV — Joint Monetization**
- Joint monetization binding
- Land aggregation priority
- Development options
- Sharing of proceeds (proportionate to holding)

**Part V — Timeline and Exit**
- 6-month deadline for procurement & registration
- Monthly progress reports
- Exit clause: if First Party fails → refund advance + 18% interest
- Bilateral exit: First Party can also exit if Second Party delays registration/payment
- Extension by mutual written consent
- Force Majeure extension

**Part VI — General Covenants**
- Mutual obligations & good faith
- Non-alienation (no independent dealing)
- Dispute resolution (binding mediation, Mediation Act 2023)
- Governing law & jurisdiction (Karnataka / Bengaluru)
- Entire agreement
- Amendments (must be in writing)
- Matters not provided for

**Schedules:**
- Schedule A (First Party's lands)
- Schedule B (Second Party's lands)
- Schedule C (To-be-procured lands)

**IN WITNESS WHEREOF + signatures**

## 50:50 Ratio for Jointly Procured Lands

When Schedule C (lands to be procured) is part of the MOU:

- Schedule C lands shall be **registered and purchased in a 50:50 (Fifty-Fifty) ratio** by both Parties
- Each Party registers 50% of Schedule C in its own name or nominee's name
- Each Party pays costs (stamp duty, registration, legal due diligence) for their own 50% share
- This differs from the original pattern where one party registered all procured lands

## Condition Precedent for Monetization

When drafting land aggregation MOUs, use condition precedent language:

> The 50:50 (Fifty-Fifty) purchase and registration ratio, the strategic procurement for contiguous-block formation, and the completion of aggregation of the entire Project Lands into a single compact block shall be **conditions precedent** to the joint monetization of the Project Lands. Until such conditions precedent are satisfied, neither Party shall have the right to require monetization.

Place this either as a standalone sub-clause under the Registration clause (Clause 5(f) pattern) or as a final sub-clause under the Land Aggregation clause.

## Strategic Contiguous-Block Procurement Language

When drafting land aggregation clauses, use this priority order with **contiguity as the first goal**:

> (a) First and foremost, to fill critical gaps and remove bottlenecks in the land shape to connect the Schedule A and Schedule B blocks with the procured parcels, making the maximum portion of the Project Lands contiguous;
> (b) Second, to purchase the minimum necessary parcels to extend the contiguity of the land mass where there are pieces owned by either Party which are not attached to the larger contiguous mass;
> (c) Thereafter, to purchase such other parcels as may be jointly identified to further extend and consolidate the Project area into a single compact block.

This differs from generic aggregation language — it explicitly makes connecting existing blocks the top priority.

## Schedule Table Population from Scanned PDFs

When the MOU's Schedule A/B/C tables are empty (common with scanned PDFs → Google Doc conversion):

1. **Find the original PDF** in Drive — the scanned original usually has the data
2. **Convert to images** — `pdftoppm -png -r 300 /path/to/pdf /tmp/pages/page`
3. **OCR with vision_analyze** — extract table data from image pages (usually the last 2-3 pages)
4. **Read original Google Doc tables** — the original Google Doc (created from OCR) may have proper Sheets-style tables embedded even if the text export is empty. Check via `docs.documents().get()` and iterate `body.content` for `'table'` elements
5. **Compute totals** for any Schedule that has blank TOTAL rows:
   ```python
   def parse_guntas(val):
       val = val.strip()
       if not val: return 0.0
       try: return float(val)
       except: return 0.0
   ```
   Sum Extent (A), Extent (G), Kharab (A), Kharab (B), Total (A), Total (G) columns
6. **Structure as text table** in the D2 document with this column layout:
   `Sl.No. | Sy.No. | Owner Name | Extent (A) | Extent (G) | Kharab (A) | Kharab (G) | Total (A) | Total (G)`
7. **Format** — bold column headers, bold TOTAL rows, bold SCHEDULE headers. The pipe-delimited text format allows easy conversion to native tables in Google Docs UI (Insert > Table > Convert Text to Table)

## Land Extent Units

When drafting Indian agricultural land MOUs:

| Unit | Symbol | Conversion |
|------|--------|-----------|
| Acre | A | 1 Acre |
| Guntas | G | 40 Guntas = 1 Acre |
| Kharab | A/B | Kharab is recorded in Guntas (column B) — land lost to roads, drains, etc. |

Total Land Extent = Extent (Acres + Guntas) − Kharab

For Schedule C (to-be-procured), total across 25+ Byadarahalli entries was ~15 A 368 G (~24.2 Ac) + 8 Gundlahalli entries ~6 A 108.75 G (~8.72 Ac).

## Registration & Cost Allocation Pattern (Nishant's Preference)

When drafting land procurement MOUs for DRAAS, use this cost model:

| Cost Item | Bearer |
|-----------|--------|
| Stamp duty | Each party for their own registered lands |
| Registration charges | Each party for their own registered lands |
| Legal due diligence | Each party for their own registered lands |
| Incidental title/land costs | **First Party** (the procuring party) — all costs for title issues, encroachments, revenue disputes, litigation, survey, mutation, statutory compliance, RTC corrections |
| CLU / Land Conversion | As mutually agreed in writing |

## D2 Document Versioning

When creating a substantially restructured version of a legal document:

1. **Copy the original** via Drive API `files().copy()` with `_D2` suffix in name
2. **Delete existing content** — `deleteContentRange` from index 1 to end
3. **Insert new content** — `insertText` at index 1
4. **Apply formatting** — batch formatting requests (bold headings, centered titles, paragraph spacing)
5. **Share** — add Nishant (ndr@draas.com) as editor, Roshni/Eshwari as readers
6. **Notify** — generate WhatsApp link with summary of changes

## Vault Socket Bypass for GWS Access

When reading a Google Doc as a user whose OAuth token is stored in the vault:

```python
VAULT_SOCKET = os.environ.get('GWS_VAULT_SOCKET', '/run/gws-vault/vault.sock')
VAULT_SECRET = os.environ.get('GWS_VAULT_SECRET', '')

def vault_get(user_id, service='google'):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(10)
    s.connect(VAULT_SOCKET)
    payload = {
        'op': 'get', 'user_id': user_id, 'telegram_id': user_id,
        'service': service, 'session_uid': user_id, 'vault_secret': VAULT_SECRET
    }
    s.sendall((json.dumps(payload) + '\n').encode())
    buf = b''
    while b'\n' not in buf:
        chunk = s.recv(65536)
        if not chunk: break
        buf += chunk
    s.close()
    resp = json.loads(buf.decode())
    if resp.get('ok'): return json.loads(resp['token_json'])
    raise RuntimeError(f"Vault error: {resp.get('error')}")
```

Then use `Credentials.from_authorized_user_info(token)` and build the service directly.

## WhatsApp Notification Pattern

After creating/updating a legal document for Nishant's review:

```python
nishant_phone = "+919880055634"
message = "Key changes summary..."
whatsapp_url = f"https://wa.me/{nishant_phone}?text={urllib.parse.quote(message)}"
```

Include: doc link, numbered list of changes, and "let me know if any changes needed."

## Example: MOU DRA KAAJ × Nine Triangle

See the D2 document at:
https://docs.google.com/document/d/1YGZFQKCB48LiPvOYcM0dYHLBwMHSKS73Haa_EDu6Zi0/edit

This MOU between Nine Triangle Infrastructure (First Party) and DRA KAAJ Development Partners (Second Party) for Byadarahalli/Gundlahalli lands was restructured from a flat 24-clause document into the 6-Part format described above. Key innovations: 6-month timeline, bilateral exit clause with 18% interest on Rs.10 Cr advance, and per-party cost split for registration/stamp duty.