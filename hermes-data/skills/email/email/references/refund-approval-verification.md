# Refund/Approval Verification — Redsol / Serenity Hillview Example

## Scenario

Bharat Hawaldar emailed Nishant requesting approval to refund ₹20L to investor **Sharat Kumar Immadisetti** (listed as "Sarath Kumar"), claiming:

| Item | Email's figure |
|------|---------------|
| Redsoul Ledger | ₹6,00,000 |
| Manohar Ledger | ₹79,00,100 |
| Total in ledgers | ₹85,00,100 |
| Amount payable | ~₹65,00,000 |
| Excess (refund requested) | ₹20,00,000 |

The email said Sarath had made two extra ₹10L transfers on 7-Jul-2026 to the Manohar account by mistake.

## Step 1 — Identify the project and entity structure

Searching Gmail, Drive, Contacts, and Sheets revealed:

- **Redsol Farmers Collective** = a general partnership owning 6A 28G in Sy.93/2, Hurulagurki, Devanahalli
- Partners: Charitra Murjani (60%), Manjunath Manohar Singh (13%), Bhavesh Bafna (13.5%), Ajnabha Prakash (6%), Sravanthi Gali (2.5%), **Mamidibathula Naga Venkata Sasidhar (2.5%)**, **Gadhamsetty Madhusudana Rao (2.5%)**
- The brand name for the project is **Serenity Hillview** (farm plots)
- "Manohar" in the email = Manjunath Manohar Singh (Second Partner, Designated Managing Partner — collected investor funds in his personal ICICI account as an interim arrangement per the partnership deed)
- "Sashi Madhu" = **Sasidhar** (Mamidibathula Naga Venkata Sasidhar, Partner 6) + **Madhu** (Gadhamsetty Madhusudana Rao, Partner 7)
- The project sells individual farm plots (each ~5,246 sqft registerable) within the 6.75A layout

## Step 2 — Cross-reference Sarath's plot details

**Payment Tracker** (`Serenity Hill View - Payment Tracker`, first sheet):

| Plot | Investor | Redsoul | Manohar | Total | Balance |
|------|----------|---------|---------|-------|---------|
| 31 | Sharat Kumar Immadisetti | ₹6,00,000 | ₹59,00,000 | ₹65,00,000 | ₹0 |

**Plot and Client Info** (third sheet of the same spreadsheet, Row 32):

| Field | Value |
|-------|-------|
| Plot No | 31 |
| Registerable Area | 5,246.22 sqft |
| UDS | 1,459.66 sqft |
| Total (incl. UDS) | 6,705.88 sqft |
| Reconstitution Distribution | CM (meaning: plot was reconstituted — sizes changed) |
| Applicant | Sarat Kumar Immadisetti (single) |
| Category | SM |

**Manohar ICICI Bank Book** (`RedSol Farmers collective -Manohar Singh ICICI (2)`, the "Manohar account" sheet):

- Sarath Kumar's payments in the Manohar ledger: ₹100 + ₹57,00,000 + ₹2,00,000 = **₹59,00,100**
- Plus the two extra ₹10L payments on 7-Jul: total Manohar = ₹59,00,100 + ₹20,00,000 = ₹79,00,100 ✓ matches the email

## Step 3 — Identify the open questions

Cross-referencing exposed what the email DID NOT answer:

1. **"Amount payable" is unsourced.** The email says "~₹65,00,000 payable" but no rate or area is stated. Deriving it:
   - If rate = ₹1,150/sqft (Nishant's assumption): 5,246 × 1,150 = **₹60,33,153** — does not match ₹65L
   - If rate is whatever makes 5,246 sqft × rate = ₹65L: **₹1,239/sqft** — plausible but unconfirmed
   - Farm Plots Economics sheet says sale rate: **₹1,102/sqft** (not ₹1,150)

2. **Plot sizes were reconstituted** (column "Reconstitution Distribution" = CM for Plot 31). Everyone's final contribution changes when plot sizes change — the ₹65L may have been based on old plot dimensions or a different UDS loading percentage.

3. **The ₹65L may include development cost, not just land.** The email quoted "amount payable" without breaking into land + development + markup.

## Step 4 — Present to the user

The right response is NOT a draft approval — it's:

> "I traced the numbers. Here's what I found:
> - Plot 31 = 5,246 sqft registerable area ✓
> - Payments: ₹6L to Redsoul + ₹59L to Manohar (+ ₹20L extra) = ₹85L total ✓
> - Email says ₹65L payable — **I can't find where this figure comes from.** At ₹1,150/sqft × 5,246 sqft = ₹60.3L. At ₹1,100/sqft = ₹57.7L. Neither matches ₹65L.
> - Plot was reconstituted — the old area/rate may not be the current basis.
>
> Can you confirm:
> 1. The exact rate per sqft for Sarath's plot?
> 2. The current (final) registerable area after reconstitution?
> 3. Whether ₹65L includes land only or land + development?
> 4. Shall I check with Sashi & Madhu to confirm rate + area before we compute the refund?"

## Step 4a — Find the revised plot area (Bhuvanesh's computation)

This session revealed a multi-layer spreadsheet architecture. Navigate in this order:

1. **Partnership Deed** (`Redsol Farmers Collective Partnership Deed` Google Doc) — identifies entity structure, partners, capital contributions, land parcel details
2. **Manohar ICICI Bank Book** (`RedSol Farmers collective -Manohar Singh ICICI (2)` Sheet) — raw transaction log, each payment dated and referenced
3. **Payment Tracker** (`Serenity Hill View - Payment Tracker` Sheet, first sheet) — investor-by-investor summary (plot, Redsoul amount, Manohar amount, total, balance)
4. **Plot and Client Info** (third sheet of Payment Tracker) — plot dimensions, area breakdown, reconstitution status, applicant names
5. **Plot Inventory Data** (`Serenity Hillview Plotal Inventory Data` Sheet, ID `1fISQfFbf2NoN5UTex1ju_Lu_yvYMZG0MV8vPYkgbGMw`) — the central reconciliation sheet with multiple tabs:
   - **Plot Details**: original GFC-approved plan (left columns) vs Sinchana's survey update (SS1 columns at right, 38.35% UDS loading)
   - **BK - Plot Update**: Bhuvanesh Krishnan's own computation (33.04% UDS loading) — the architect's independent assessment
   - **Final Plot Distribution Sheet**: comprehensive with reconstitution distribution column
   - **Comparison Old v/s New**: side-by-side delta showing old (30.36% UDS) vs new (33.04% UDS) for every plot

For **Plot 31 (Sharat Kumar)** specifically, from the Comparison sheet:

| Metric | Old (Final Distribution) | New (Bhuvanesh BK) |
|--------|------------------------|-------------------|
| Registerable Area | 5,246.22 sqft | 5,242.58 sqft |
| UDS | 1,592.52 sqft | 1,732.37 sqft |
| UDS Loading % | 30.36% | 33.04% |
| **Total Area** | 6,838.74 sqft | **6,974.95 sqft** |

Note: Sinchana's survey (SS1) shows yet another version at 38.35% UDS loading with total = 7,174.29 sqft — this was the draft sent to Bhuvanesh for sign-off (email dated 12-Jul-2026). The project had not received a final signed-off version from Bhuvanesh as of this session.

## Step 5 — The calculation the user wants

Nishant's instruction for computing the refund amount:

**Step A — Derive the implicit rate on registerable area**
```
Rate = ₹65,00,000 ÷ 5,246.22 sqft = ₹1,238.98/sqft
```

**Step B — Apply to the revised total area**
```
New Payable = Revised Total Area × ₹1,238.98
```

The "revised total area" here means **registerable + UDS area** from the most current source (Bhuvanesh BK: 6,974.95 sqft).

**Step C — Compute excess**
```
Total Paid (Redsoul ₹6L + Manohar ₹79,00,100) = ₹85,00,100
Excess = ₹85,00,100 − New Payable
```

⚠️ **Caveat:** If the rate (₹1,238.98/sqft) was originally applied to registerable area only, applying it to the total area (registerable + UDS) inflates the payable. This can result in new payable > total paid, meaning no refund is due. Nishant understands this and will decide the correct basis.

**⚠️ CRITICAL CORRECTION (applied in session 17-Jul-2026): The rate applies to TOTAL area (registerable + UDS), NOT registerable alone.** Nishant explicitly corrected this. When you present the two approaches (A = rate on registerable only vs B = rate on total area), do NOT ask which is correct — he has already confirmed B. The correct computation:

```python
# CORRECT approach:
old_total_area = reg_area + uds_area  # e.g. 5,246.22 + 1,459.66 = 6,705.88
rate = agreed_price / old_total_area   # e.g. ₹65L / 6,705.88 = ₹969.30/sqft
new_payable = new_total_area * rate    # e.g. 6,974.95 × ₹969.30 = ₹67,60,809
refund = total_paid - new_payable      # e.g. ₹85,00,100 - ₹67,60,809 = ₹17,39,291
```

The final draft email should state this clearly: "Key clarification: the rate applies to the total area (registerable + UDS), not just the registerable area." Then show the full working.

## Finding CC addresses for the draft

When the user says to CC someone (e.g., "Manohar Singh" or "redsoul.co"), do NOT rely on Google Contacts alone — the person may not be in the user's address book with the correct email. Instead:

1. **Search existing email threads** for that person's domain or name in Gmail first:
   ```python
   results = gmail.users().messages().list(userId='me', q='redsoul.co.in', maxResults=5).execute()
   ```
2. Check recent threads where the user and that person are both participants — the `Cc:` header from a recent thread is the most reliable source.
3. Only fall back to Google Contacts search if Gmail yields nothing.

For this session: Manohar Singh's email was found as `msingh@redsoul.co.in` in recent Ranka Amber email threads, not in Google Contacts (which only had his @ircaindia.com addresses).

## Step 6 — Verification sequence (per Nishant's instruction)

When a financial response needs calculating before drafting, follow this exact sequence:

1. **Confirm with Nishant first** — present the plot area, rate, and your understanding of the calculation. Do not proceed without his nod.
2. **Then confirm with intermediaries** (Sashi + Madhu, or whoever is the channel partner) — get the rate and final area confirmed in writing.
3. **Then confirm with the customer** — share the computation with the investor and get their acceptance.
4. **Only then compute** the exact excess/refundable amount.
5. **Finally draft the response** to the original email (Bharat or whoever sent the request).

This sequence prevents the common mistake of drafting an approval response and then having to re-do it because the basis changed at step 2 or 3.

## Key takeaway

Never draft an approval response to a data-heavy email without independently verifying every number against source records. The email author is well-intentioned but may be working from stale assumptions. Source Sheets are ground truth.

When multiple sets of plot area data exist (architect's GFC plan, surveyor's physical measurement, architect's independent re-computation), explicitly identify WHICH version you used and flag that no final signed-off version existed at the time of the request.
