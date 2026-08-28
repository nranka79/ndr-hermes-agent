# Bima Bharosa Complaint Drafting — IRDAI Insurance Grievance

Draft a complaint for filing on the IRDAI Bima Bharosa portal (https://bimabharosa.irdai.gov.in). This is the regulatory route for insurance grievances — faster than consumer court.

## When to use

- User has an insurance grievance (claim repudiation, revival rejection, policy servicing issue)
- User asks to file a complaint with IRDAI or "Bima Bharosa"
- User wants complaint text drafted for regulatory escalation
- User is preparing multiple parallel remedies (IRDAI + Ombudsman + Consumer Forum)

## Portal Constraints

| Constraint | Value | Detail |
|------------|-------|--------|
| **Complaint Description** | Max **4,000 characters** | Including spaces, newlines, and punctuation |
| **Restricted characters** | `< > { } [ ] & ^ \| # ~ % $` | Avoid these entirely |
| **Attachment** | Single PDF | Case analysis document, evidence compilation, or correspondence summary |
| **Complaint Type** | Various | See below for options |

### Common Complaint Types

| Option | When to Use |
|--------|------------|
| **Malpractice or Unfair Business Practice** | Arbitrary revival rejection, wrongful lapse, moving goalposts, violation of TAT |
| **Claim Repudiation** | When a death/maturity claim is denied |
| **Delay in Claim Settlement** | When the insurer delays beyond regulatory timelines |
| **Policy Servicing** | Non-receipt of policy documents, address change issues |
| **Mis-selling** | When policy was sold with wrong features/benefits |

For Nishant's Bajaj Life case: **"Malpractice or Unfair Business Practice"** is correct. The issue is not a claim — it's the insurer's conduct during the revival process.

## Complaint Structure (Insurance Revival / Unfair Practice)

### 1. Header Block

```
Policy No: [POLICY_NUMBER]
Insurer: [INSURER_NAME]
Policyholder: [NAME]
Sum Assured: Rs. [AMOUNT] ([WORDS])
Annual Premium: Rs. [AMOUNT]
Policy Issued: [DATE]
```

### 2. Body — Narrative (~3,000 chars)

Open with the policyholder's standing (how many years of faithful premium payment). Then describe the sequence of events that led to the grievance:

**Key elements to include:**
- When and how the policy was first taken
- The insurer's act that caused the problem (premium reversal without notice, delayed response, moving goalposts)
- How long the insurer took (compare with regulatory TAT — IRDAI mandates 7 days for revival decisions)
- The final rejection and its stated reason
- Why that reason is invalid under law

**Legal points to weave in (concisely):**
- Section 45 of Insurance Act, 1938 — bars questioning a policy after 3 years
- IRDAI PPI Regulations, 2024 — 7-day TAT for revival decisions
- Revival is restoration of original contract, not a new policy — financial re-underwriting is impermissible
- Judicial precedent (Rekha Jain v. Bajaj Allianz — Delhi State Consumer Commission; Avinash Bhosle v. ICICI Prudential — NCDRC 2021)

### 3. Relief Requested (what IRDAI should order)

Numbered list (5 items max):

1. Reverse the arbitrary rejection and confirm revival on original terms
2. Restore policy to continuous force
3. Pay interest on reversed premium
4. Take regulatory action against the insurer for TAT violations
5. Award compensation for mental agony

### 4. Final Statement

State that evidence attachments are provided. Express trust in IRDAI's process.

## Attachment — What to Attach

The best attachment is a PDF of the **Case Analysis** document (if one was previously created). Include:
- Full timeline of events
- All IRDAI violations with regulatory citations
- Evidence list (what was provided and when)
- Legal argument summary

If no case analysis exists, create a **one-page summary PDF** covering:
- Policy details
- 5-bullet chronology
- Legal grounds for complaint
- Documents on record

**Avoid:** Attaching raw emails, bank statements, or WhatsApp screenshots as the primary attachment — they are too detailed for the IRDAI officer to parse. The case analysis/summary is the primary document; supporting evidence can be referenced.

## Example (based on Bajaj Life revival rejection)

```
BIMA BHAROSA COMPLAINT
Policy No: 0444146783
Insurer: Bajaj Life Insurance Limited
Policyholder: Nishant Ranka
Sum Assured: Rs. 3,00,00,000 (Three Crores)
Annual Premium: Rs. 73,066
Policy Issued: March 2021

I have been a Bajaj Life policyholder for over 5 years. My policy lapsed 
not due to any fault of mine, but because Bajaj Life unilaterally reversed 
my paid premium of Rs. 73,066 on 12 May 2025 without any prior notice, 
demand, or explanation. I discovered this lapse only in March 2026 when 
I contacted them on a routine matter. No letter, SMS, or email was sent 
to me between May 2025 and March 2026 informing me of the reversal or 
the lapse.

I submitted a revival request in April 2026. Despite submitting every 
document requested and providing bank statements, medical reports, 
Form 16s, salary slips, and income proofs, Bajaj Life kept demanding 
fresh documents for over 90 days, each time with new requirements. They 
directed me to email an address that bounced, but never provided a working 
alternative or even acknowledged the bounce.

On 18 July 2026, Bajaj Life finally responded rejecting my revival request 
citing insufficient financial documents as the reason. My annual income is 
Rs. 1.2 Crores as evidenced by Form 16s and salary slips already submitted. 
The sum assured is Rs. 3 Crores...

This rejection is legally unsustainable because:
...
```

## After Filing

After the complaint is filed on Bima Bharosa:
1. Note the **complaint reference number** for tracking
2. IRDAI typically responds within 30 days
3. If no satisfactory response, escalate to **Insurance Ombudsman** (Bengaluru)
4. Parallel consumer forum filing under the Consumer Protection Act, 2019 may also be considered

## Related Skills/References

- `document-dossier-compilation` — Evidence compilation for insurance/legal cases
- `email-drafter` → references `insurance-legal-response-email.md` — Legal email to insurer citing same violations
