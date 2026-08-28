# RERA Case Evidence: Gmail Retrieval from Legal Document References

**Trigger:** User shares numbered evidence references (e.g., `#4 — 20.08.2020 — Email issued by X stating...`) from a RERA/consumer case document annexure and asks you to find the actual emails.

## Core Pattern

Legal evidence annexures in RERA/consumer cases list documents by:
- **#** — reference number in the evidence list
- **Date** — when the email was sent
- **Description** — who sent it and what it said

Your job: map each reference back to the real email in Gmail to confirm existence, extract the actual content, identify the sender, and fill gaps (underscores `____` or blanks `_`) in the description.

## Step-by-Step Workflow

### 1. Identify the Complainant and Project

The evidence description usually names the complainant or their email. Extract the **complainant email** and **project name** immediately.

Gmail search pattern:
```
from:complainant@email.com after:YYYY/MM/DD before:YYYY/MM/DD
```

But complainants often have **partial** or **indirect** email involvement — they may not email your user directly. Instead, RERA sends notices that name the complainant.

**Better search — find the RERA complaint number first:**
```
complaintsrerakar@ OR complaintsrerakar2@ OR peaceabhi@gmail.com
```
Look for emails from `complaintsrerakar2@gmail.com` (KRERA RERAKAR cell) — these name the complainant in the email body.

### 2. Extract the RERA Complaint Number

RERA notices contain the complaint number in the subject:
```
CMP/200812/0005887
```

Once you have the complaint number, search the full thread:
```
CMP/200812/0005887
```

This returns all RERA hearing notices, written submissions, judgments, and internal forwards related to that specific case.

### 3. Trace Each Evidence Reference

For each evidence entry:

| Reference Field | How to Resolve |
|----------------|---------------|
| **Date** | Search emails ±2 days of that date using the complaint number or project name |
| **Sender (blank \_)** | Check the response email — the builder's legal team (Nagendra Prasad, Shodhan Lokhande @ koltepatil.com) or the RERA authority |
| **Description** | Read the email body — the actual wording may differ slightly from the evidence list (garbled OCR, paraphrasing) |

### 4. Reconcile Garbled Text

Evidence descriptions from legal documents often have OCR/transcription errors:

| Garbled | Likely Correct |
|---------|---------------|
| `sngas`, `sng`, `snag` | **snags** (defects/rectification items in construction) |
| `OC` | **Occupation Certificate** |
| `registration` | **Sale deed registration** (not RERA registration) |
| `PLS` | **Palm Lakeside** (project) |
| `WHPL` | **Westbury Hospitality Pvt Ltd** |

### 5. When the Email Is Not in the Primary Account

The specific evidence email may not be in your user's inbox because:
- The builder (Kolte Patil, etc.) emailed the RERA authority directly, CC'ing the complainant — your user (the co-promoter/land owner) is not on the thread
- The email was sent as a formal written submission, not as a regular email
- Only RERA notices and forwarded copies land in your user's inbox

**Check these sources:**
1. **ndr@drahomes.in** — older forwards may live here
2. **RERA system emails** (`info.rera@karnataka.gov.in`) — contain summons, hearing dates, judgments
3. **Complainant's replies** — if the complainant forwarded or CC'd your user
4. **Attachment PDFs** — the evidence document itself may be attached to a RERA judgment/orders email

### 6. Filling the Blank (`_`) Fields

When the evidence list has `Email issued by ____` or `by _`, the sender is typically one of:

| Context | Likely Sender |
|---------|--------------|
| RERA hearing notice | `Palakshappa K <palakshappa.k@ka.gov.in>` (Secretary, K-RERA) |
| Builder stating apartment ready | `Nagendra Prasad <nagendra.prasad@koltepatil.com>` (Kolte Patil Legal) |
| Builder about OC/registration | `Nagendra Prasad <nagendra.prasad@koltepatil.com>` or `Shodhan Lokhande <Shodhan.Lokhande@koltepatil.com>` |
| RERA orders/judgment | `info.rera@karnataka.gov.in` (system generated) or `deputysecretaryds@gmail.com` |

## Real Example: Abhishek Kumar v. Kolte Patil — Mirabilis (CMP/200812/0005887)

**Evidence #4:** `20.08.2020 — Email issued by ____ stating that after clearing sngas the apartment was ready for occupation`

- Garbled: `sngas` → `snags`
- Sender: Nagendra Prasad (Kolte Patil) — email date may be 5 Aug 2020 (not 20th), sent as written submission to RERA
- Not in Nishant's Gmail directly — it was sent by KP to RERA, not CC'd to him

**Evidence #10:** `28.06.2022 — Email issued by _ informing the complainant that OC was received in 2019 itself and despite lapse of almost 2 years the Complainant has failed to come forward for registration hence not entitled to the delay compensation as claimed for`

- This is the builder's (Kolte Patil's) legal response to the RERA hearing on 27 June 2022
- Sent by Nagendra Prasad / Shodhan Lokhande to RERA
- Not directly in Nishant's inbox despite being about his project (Mirabilis land owner share)

## Pitfalls

### Cross-Thread Contamination
Multiple RERA complaints often share the same hearing email thread. Check the specific complaint number, not just the subject line. Complaints 5887, 6093, 3667, 4932, etc. may appear in the same RERA email — the body distinguishes them.

### Complainant Name Confusion
The evidence list may name a complainant that differs from other cases in the same thread (Kolte Patil handled multiple Mirabilis complaints simultaneously — Arvind Gaur for complaint 4932, Abhishek Kumar for 5887). Always confirm the complainant from the RERA notice body, not the email subject or thread context.

### First Email May Be a Forward
The earliest email you find may be Nishant forwarding a RERA notice to the team. The actual source (RERA system email) is inside the forward chain. Always expand forwarded messages to get the original date and sender.

### Date Discrepancies
The evidence list date may differ from the actual email date by a few days (the document was prepared on the 20th, but the email was sent on the 5th). Check ±5 days.

### "Failed to Come Forward for Registration" = Builder's Defence
This phrase is the builder's standard argument that the complainant delayed registration (sale deed), not that they missed a RERA filing deadline. The builder uses this to argue delay compensation should stop from OC issuance date.