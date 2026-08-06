# WhatsApp Message for Accounts Group

A repeatable pattern when Nishant asks: "Create a message from my accounts group explaining the DDs/payments needed" — a structured WhatsApp message for the internal accounting/finance team explaining what payments to prepare, from which project, which company, and what purpose.

## Trigger phrases

- "Create a message from my accounts group explaining..."
- "Send a message to the accounts group about..."
- "WhatsApp message for the accounting team..."
- "Draft a message for the accounts team..."

## Two distinct patterns

1. **DD Instructions (outbound from accounts)** — the accounts team prepares DDs for authorities. Message is FROM the accounts group, impersonal, signs `— Accounts Dept`.
2. **Payment instruction to accounts (from Nishant)** — Nishant tells the accounts group to pay an individual/vendor immediately, often from a **personal account** (Kanta Ranka, Nishant Ranka) rather than a company. Message is from Nishant, direct, includes full payee bank details + expense breakup. See "Payment instruction pattern" below.

## The structure (Pattern 1 — DD Instructions)

```
**Accounts Group — [Project]: [Purpose] — DD Instructions**

Project: **[Project Name]** ([Location])
Company: **[Company Entity Name]**

Please prepare the following Demand Drafts:

**① [Authority/Body] — [Purpose]**
Payable at: [Location / counter details]
| Particulars | Amount (₹) |
|---|---|
| Item 1 | X,XXX |
| Item 2 | X,XXX |
| **Total** | **X,XXX** |

**② [Second authority if applicable] — [Purpose]**
*(Amount TBC — update when available)*

**Purpose:** [One-line description of what this payment is for]

Please book entries under **[Company Entity Name] — [Project Name]**.

— Accounts Dept
```

## The format rules (Pattern 1)

- **Header** in bold: `**Accounts Group — [Project]: [Purpose] — DD Instructions**`
- **Project + Company** on separate lines in bold markdown
- **DDs as a numbered list** (①, ②) — one per authority/bank
- **Table for amount breakdowns** (Particulars | Amount) — Telegram converts these to row-group bullets automatically, which is fine
- **Total row** in bold
- **Accounting entry instruction** at the bottom — which company + project to book under
- **Sign-off:** `— Accounts Dept` (impersonal, not a person's name)

## Payment instruction pattern (Pattern 2)

When Nishant says "create a message for the accounts group: we need to pay this gentleman immediately, from the account of Kanta Ranka" (or any personal account):

```
Accounts team,

Please make the following payment immediately — to be debited from **[Person's] account**.

**Payee:** [Full name, S/o ..., address]
**Bank details:**
- Bank: [SBI / etc.]
- A/c No: [number]
- IFSC: [code]

**Purpose:** [what the money is for — e.g. repairs at the house in Sardi, Rajasthan]

**Expense breakup (₹):**
- [Item]: [amount]
- ...
- **Total: [amount]**
```

Key rules for Pattern 2:

- **Recipient is the accounts GROUP chat, not Eshwari.** "Accounts Guru" / "accounts group" = a group where Eshwari + many other accounts team members are present. Do NOT address it to Eshwari alone. (Corrected 2026-08-01.)
- **Full payee bank details go in the message** — name, S/o, address, bank, account number, IFSC. Extract these from the passbook/account photo via OCR; present in English even if the original is Hindi.
- **Expense breakup translated to English.** The handwritten ledger may be in Hindi (वर्ती, बरीचा, नालका...). Translate item names to English equivalents (Varti, Baricha, Naalka, Bokar, Store, Bhaj Tempo, Lock + Kadi) and keep amounts in ₹.
- **Flag arithmetic discrepancies before sending.** If the line items you can read don't sum to the stated total (e.g. items sum ₹14,760 but total is ₹20,160), tell the user about the gap and ask them to verify with the payee before the message goes to the group. Do NOT silently ship a message whose breakup doesn't add up.
- **"Share both the images and the exact amount right now"** — when the user says they will send images/amount before you compose, WAIT for those inputs; confirm the recipient and context, but hold the draft until the data arrives.
- **Immediate/urgent framing** when the user says "pay immediately" — lead with "Please make the following payment immediately".

## Data sources for the message

Before writing, find the actual amount and purpose data:

1. **If the user has a demand challan/letter** — find it on Drive (search by project name + "demand", "BESCOM", "BWSSB", "challan", "fee")
2. **If the user references an email** — search their inbox for the relevant thread (e.g. "BESCOM Power Supply Update - Ranka Iris", "BWSSB Road Cutting Permission")
3. **If the user references a Kelsa record** — follow the standard Kelsa search to find the PO/invoice and extract amounts
4. **If amounts are unclear** — say so in the draft with a `(amount TBC — confirm)` note

## Key entity names

Nishant uses specific company entities for different projects. Cross-check the project against these:

| Project context | Company entity |
|---|---|
| Ranka Iris (Domlur) | DRA Developers and Projects Private Limited |
| DRA Thindlu Land Partners | DRA Thindlu Land Partners |
| General DRA Group work | DRA Developers and Projects Private Limited |
| Ranka Oasis (TN) | Check project docs |
| Serenity Hillview | Check project docs |

When the user names a different entity, use it verbatim.

## Personal accounts in payment instructions

Payments can be debited from personal accounts, not just companies:

- **Nishant Ranka** — exists in Kelsa Companies Master (ID 26054620) and as `nishant ranka` in the Petty Cash "Account to be debited" dropdown (7 prior uses). Valid payment source.
- **Kanta Ranka** — as of 2026-08-01 NOT in Companies Master and NOT in the dropdown. If a payment must come from her account, either add her to Kelsa first or tell the accounts group it's a manual Kanta Ranka debit outside Kelsa.
- **Dinesh Ranka** — also a valid dropdown value (21 prior uses).

## Pitfalls

- **Pattern 1 is FROM the accounts group**, not from Nishant. Use impersonal language. Sign off as `— Accounts Dept`, not Nishant's name.
- **Pattern 2 is FROM Nishant TO the accounts group.** Direct, first-person ("I need this paid..."), no pleasantries — it's an instruction, not a request.
- **Always include the company/personal entity.** The accounts team needs to know which legal entity (or whose account) to book the entry under.
- **Break down lump sums into line items** when available (e.g. MMD Deposit ₹3,14,120 + Supervisory Charges ₹1,49,055 = Total ₹4,68,255). This lets accounts cross-verify against the original challan.
- **If you don't have exact amounts**, mark them as `(TBC)` in the draft and flag it — don't fabricate numbers.
- **Include payment instructions** (where to pay, DD in favour of whom, payable at which office) when available from the challan.
- **Don't hardcode the recipient as Eshwari** — the accounts group includes her plus other members.
