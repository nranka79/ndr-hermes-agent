# Gunjur Village — Strategic Land Co. Investment Opportunity

## Deal Overview

- **Property:** 6.25 acres (6 acres 10 guntas) in Gunjur Village, East Bangalore
- **Minimum investment:** ₹4.60 Cr per acre (all-inclusive: purchase + CLU + registration + legal DD)
- **Target exit:** ~24 months from purchase registration
- **Dual exit pathway:** Grade A developer (Option A, recommended) or Ranka brand (Option B)

---

## Two Exit Options

| | Option A — Grade A Developer | Option B — Ranka Brand |
|---|---|---|
| Plot price | ₹6,500/sq.ft | ₹5,000/sq.ft |
| Investor share | 55% | 65% |
| Total receipts | ₹8.90 Cr/acre | ₹8.00 Cr/acre |
| Multiple | 1.93× | 1.74× |
| Expected IRR | ~55% | ~44% |
| Monthly cash flow (M13-24) | ₹72 L/month | ₹64 L/month |
| Non-refundable token (M12) | ₹30 L | ₹30 L |
| Recommended | ✓ Yes | — |

**Note:** Both tokens are non-refundable deposits paid at plot launch (Month 12).

---

## Cash Flow Table (per acre)

| Period | Event | Amount |
|---|---|---|
| Month 0 | Investment (land purchase + charges) | −₹4.60 Cr |
| Month 12 | Non-refundable token (at plot launch) | +₹30 L |
| Months 13–24 | Monthly sales proceeds — Grade A (₹72 L/mo) / Ranka (₹64 L/mo) | +₹8–9 Cr total |
| Total | Within 24 months | ₹8–8.9 Cr |

---

## LLP / Partnership Structure

Q&A content for the Structure card (inserted after "What You Are Investing In", before "Current Status"):

### Q1: How does the collective investment work — what structure are investors part of?
**A:** A new **partnership / LLP** is established in which all investors collectively hold the property. Simultaneously with the land registration, investors enter into a **Joint Development Agreement (JDA)** with DRA — assignable to the Ranka family's existing partnership company (the 10+ year JV vehicle with the grade-A developer). The JDA terms offered to this LLP are identical to those offered to the Ranka family for their larger land parcel.

### Q2: Who develops the land — and how is it linked to the Ranka family's larger project?
**A:** The JDA is assignable to the Ranka family's partnership company — the same 10+ year old JV vehicle with the grade-A developer that is already developing the Ranka family's own adjacent land parcel. The JDA for this 6.25 acres will be assigned under the **same terms and conditions** as the Ranka family's own larger land parcel, and the project will be developed as **one combined, unified development** alongside the Ranka family's land.

### Q3: What does the Ranka family contribute at the time of registration?
**A:** At the time of land registration, the Ranka family immediately contributes **₹5 lakh per acre** as skin in the game. This demonstrates alignment of interest and reinforces investor security from day one.

### Q4: When is the balance of the land cost paid?
**A:** The **remaining balance** of the land cost is paid at the time of change of land use (CLU) and conversion — not at registration. All expenses related to CLU and conversion are borne by the partnership / LLP itself.

### Q5: How are investors protected throughout this process?
**A:** The land asset is held in the **partnership / LLP's name** from day one. Investors are not exposed to any capital beyond their committed investment — there are no additional capital calls, and the land title sits with the partnership vehicle throughout the lifecycle of the investment.

**Callout note:** The Ranka family has a 10+ year old partnership company with a grade-A developer, responsible for multiple completed projects. The JDA for this piece of land will be assigned to that same vehicle under the same terms and conditions — giving investors the same backstop and institutional rigour as the Ranka family's own larger land parcel.

---

## Current Status (DD checklist)

- ✅ Land owners identified & negotiated
- ✅ Token amount paid
- ✅ Term sheets signed
- ✅ Legal due diligence ongoing
- ✅ Title crystal clear
- ✅ CLU conversion in progress (Ranka family — simultaneous with their larger parcel)
- ✅ Grade-A JV in place (10+ years, multiple projects)
- ✅ Independent state highway access confirmed

---

## Timeline

| Milestone | Timing |
|---|---|
| Land purchase registration + CLU initiation | Month 0 |
| CLU + conversion approved + plot launch + ₹30L token | Month 12 |
| Full sales closure + final proceeds | Month 24 |

BMRDA plot sanction expected within ~12 months from purchase. Joint development launch simultaneous with approvals.

---

## HTML File Naming Convention

`Gunjur_Investment_Opportunity_QA.html` (v1, v2, v3 suffixes for versions)
Final v3: `1oPbtsVOvpahQL5FYErV_dInxl_mv1vlf` (Proposals folder ID: `0B1Oc8cSaJXPGNTRDWDhTUXZxeVU`)

---

## HTML File Naming Convention

`Gunjur_Investment_Opportunity_QA.html` (v1, v2, v3, v4 suffixes for versions)
Latest: `Gunjur_Investment_Opportunity_QA_v4.html` → Drive ID `1oPbtsVOvpahQL5FYErV_dInxl_mv1vlf`
Proposals folder ID: `0B1Oc8cSaJXPGNTRDWDhTUXZxeVU`

---

## Pitfalls Encountered in Session

1. **"Ranca" misspelling** — Correct spelling is **"Ranka"** throughout. Always verify.
2. **Grade A cash flow wrong** — Was ₹25L/month (= 3 Cr/12). Correct: ₹72L/month (= (8.9 Cr − 30 L)/12). Root cause: misread "8.6 Cr" share as total; actual Grade A total receipts = ₹8.9 Cr/acre at 55%.
3. **CTA bar** — Must be removed for PDF-conversion documents.
4. **PDF embed** — Do NOT embed base64 PDF in HTML for print-to-PDF documents. Made file 3.4 MB. HTML IS the document; do not embed a PDF reference inside it.
5. **Drive file not updating** — `files.update()` with wrong `parents` field causes 404. Use `files.delete()` + `files.create()` for clean version replacement.
6. **First card bleeds to page 2** — Tighten sizing: h1 ≤28px, amount ≤36px, padding 20px 22px, gap 10px. Referred to as "first-card-one-page rule." See Playwright section above for why CSS alone does NOT guarantee a 1-page first card.
7. **Option ordering** — Grade A = Option A (recommended, higher IRR), Ranka = Option B. Do not reverse without being asked.
8. **Playwright scrollHeight != visual page count** — A first card whose content ends at y=424pt (50% of A4 page) STILL generates a 5-page PDF because Playwright computes total pages from body scrollHeight at 1280 viewport. Only content reduction or card splitting fixes this — not CSS tuning.
9. **System deps for Playwright** — On a fresh install, run `playwright install-deps chromium` before `playwright install chromium`. Without deps, Chromium launches but PDF generation silently fails or produces corrupted output.
