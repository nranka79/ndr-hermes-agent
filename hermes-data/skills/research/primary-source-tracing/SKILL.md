---
name: primary-source-tracing
description: "When the user asks 'what's the source of this', 'who actually said that', 'give me the original report', 'cite the primary', or 'trace this back' — chase a secondhand news claim, social-media post, or industry figure back to the underlying primary research, regulator filing, government notification, or original publication. Reconcile multiple competing datasets from different research firms (Knight Frank, Anarock, JLL, Colliers, CREDAI, NAREDCO, etc.) that often publish near-identical headlines with different numbers in the same week. Navigate registration-walled PDFs and gated reports. Use whenever the user wants the original document underlying a news article, or wants the data chain (newspaper X cited research firm Y, which used data source Z)."
version: 0.1.0
metadata:
  hermes:
    tags: [research, sourcing, citation, due-diligence, fact-check, india, real-estate, market-research]
---

# Primary-Source Tracing

A general-purpose workflow for chasing a secondhand claim back to its primary source, reconciling conflicting industry-research datasets, and navigating gated PDFs.

## When this skill applies

- User says "what's the source of this", "who actually said that", "give me the original report", "cite the primary", "trace this back to", "what was the data source of this article"
- User quotes a number and asks which research firm / government body / regulator published it
- Two or more news outlets cover the same story with different numbers (very common in Indian real-estate: Knight Frank H1 2026 vs Anarock Q2 2026 vs JLL vs Colliers all publishing in the same week with overlapping but non-identical datasets)
- The headline says "according to a report" or "as per a study" with no clear citation
- The user wants the underlying PDF and you only have a news article

## Core workflow (5 phases)

### 1. Identify the unit of analysis

Pin down what the user actually wants:
- The article itself (URL, title, author, publication, date)
- The data/research firm that produced the numbers (Knight Frank, Anarock, JLL, Colliers, CREDAI, NAREDCO, IBEF, RBI, SEBI, MCA, MoHUA, etc.)
- The original primary document (PDF report, gazette notification, order, circular, filing)
- The data source the research firm itself relied on (RERA registration data, stamp-duty registrations, broker data, builder disclosures, etc.)

Ask the user only if ambiguous. Often the user wants all of the above — give them the whole chain.

### 2. Extract the source attribution from the article

- Pull the article (Google News RSS, direct URL, or archive.org)
- Look for these attribution phrases and the entity right after them: "according to", "as per", "data from", "report by", "released by", "compiled by", "citing", "based on", "said a report", "showed"
- For Indian real-estate, the typical firm → headline relationship looks like:
  - Knight Frank → 8-city H1/H2/Y-end reports, premium/luxury, India Real Estate series
  - Anarock → 7-city quarterly reports, often Q2 with "West Asia conflict" or "affordability" angle
  - JLL → residential + office, often mid-year / mid-quarter
  - Colliers → H1/H2, often luxury/ultra-luxury
  - CREDAI / NAREDCO → industry-body reports, sentiment indices
  - PropTiger / Magicbricks → portal-level data
  - Liases Foras / ICRIER / NCAER → academic-style deep dives
  - RBI, SEBI, MCA, MoHUA, NITI Aayog → government

### 3. Find the primary document

Try in this order:

1. **The publisher's own research portal** (often gated, e.g. `https://www.knightfrank.co.in/research/...`). Look for the report detail page first, then try a form POST. Gated PDFs are common; you usually cannot programmatically download them without a real-user registration flow — say so and offer to register on the user's behalf with their work email.
2. **Publisher's global site** (e.g. `knightfrank.com/research`) — sometimes has the same report, sometimes not
3. **Publisher's CDN**: many consulting firms host reports at predictable paths like `content.knightfrank.com/research/<id>/images/...` — pull the page HTML and grep for `.pdf`, `data-kf-ajax-form`, `<iframe>`, or thumbnail image URLs to confirm the report exists
4. **archive.org / Wayback Machine** — check `web.archive.org/web/2026/<url>`; often not yet snapshotted for a brand-new release
5. **Indian government / regulator open-data portals**:
   - data.gov.in, opencity.in, datawraps.com
   - RERA: each state has its own portal (e.g. MahaRERA, UP-RERA, HRERA, K-RERA, TN-RERA)
   - Stamp-duty / registration: state Inspector General of Registrations (IGR)
6. **Press release coverage** (moneycontrol.com, business-standard.com, economictimes.indiatimes.com, fortunindia.com, housing.com, 99acres, magicbricks blog) — these often quote the report and link to the publisher's gated page
7. **Secondary articles from multiple outlets** — if you can confirm 2–3 outlets independently cite the same firm + same numbers + same week, you've established the chain even without the PDF

### 4. Reconcile conflicting datasets (Indian real-estate pattern)

This is the most common failure mode. In a typical week, two or more firms publish overlapping-but-different numbers:

- **Different time windows**: H1 (Jan–Jun) vs Q2 (Apr–Jun) vs FY (Apr–Mar). An article saying "down 6%" (Q2) and another saying "up 1%" (H1) are both correct because they cover different windows.
- **Different city baskets**: 7 cities (Anarock default) vs 8 cities (Knight Frank default — adds Ahmedabad). Mumbai 47,355 may not exist in a 7-city report.
- **Different metrics**: "units sold" vs "property registrations" (Mumbai has both; the 80,000+ registrations figure is IGR stamp-duty data, not developer sales).
- **Different segment definitions**: "luxury" means ₹10 cr+ in some reports, ₹20 cr+ in others. Knight Frank splits ₹20–50 cr and >₹50 cr separately.

**Always surface the reconciliation explicitly in your reply** — present a table with [Outlet | Headline | Data source | Time window | City count] so the user can see at a glance why two headlines say different things about the same week.

### 5. Cite the chain, not just the article

Format the final answer as a chain:

```
Outlet:    "Housing Sales Fall 6% In 7 Major Cities" — NDTV, 8 Jul 2026
   https://www.ndtv.com/...
      ↓ cites
Data firm: Anarock, Q2 2026 report (7 cities)
   https://www.fortuneindia.com/business/.../128100  (Fortune India coverage)
      ↓ underlying PDF gated at
Primary:   Anarock Q2 2026 — registration wall, requires email
```

Then the *parallel* chain for the 1.71-lakh story using Knight Frank H1 2026. Then a side-by-side reconciliation table. The user is usually a senior person who wants the chain, not a rephrase.

## Pitfalls

- **Don't fabricate reconciliation** — if you can't reconcile two numbers, say so and show both. Indian real-estate datasets are notoriously inconsistent; pretending they align is worse than flagging the gap.
- **Don't open the gated PDF if the user hasn't authorised it.** PDF gates on Knight Frank / JLL / Colliers / Anarock are registration forms. If you fill them with synthetic data the firm may send a marketing email to the address. Always ask before registering on the user's behalf.
- **DDG HTML search is broken / empty in this environment** — returns the lite shell page with no results. Use `news.google.com/rss/search?q=...&hl=en-IN&gl=IN&ceid=IN:en` (Google News RSS) as the workhorse. It works without keys, gives dated items, and is parseable.
- **Outlets return 403 to scripted clients** — NDTV, HT, The Hindu, TOI, Fortune India all return 403 to Python `urllib` with default UA. The reliable approach is: Google News RSS for headline + outlet + date + link, then `outlookmoney.com`, `moneycontrol.com`, `constructionweekonline.in`, `thehawk.in`, `expressnews.asia` which are usually open. Outbrain-hosted rewrites (e.g. CBMi... redirect URLs) don't resolve directly.
- **A single Google News RSS link does NOT give you the article text.** The CBMi... URLs are Web Light rewrites. To get article text: search Google News with multiple queries, find the cleanest outlet, hit it directly. Outlook Money and the firm's own research portal are usually the most open.
- **The 7-city vs 8-city difference is the #1 cause of confusing Indian real-estate headlines** — always check how many cities each dataset covers before comparing numbers.
- **Knight Frank India H1/H2/Y-end reports are gated, not mirrored.** They do not appear on `knightfrank.com`. The detail page has a thumbnail + download modal. POSTing to the form returns 200 but no direct PDF URL — the form handler is server-side session-validated.
- **"As per a report" without naming the firm = go back to step 2.** Don't guess. If you can't find the firm, say so.

## What this skill does NOT do

- It does not generate citations for a paper you're writing — that's `research-paper-writing`.
- It does not surface arXiv / academic papers — that's `arxiv`.
- It does not monitor feeds over time — that's `blogwatcher`.
- It does not crawl X/Twitter — use `xurl` for that, but note that without a configured X API account you only get the public web shell, which is usually empty.

## Related skills

- `regulatory-complaint-escalation` — uses this skill's source-tracing pattern to identify which regulator/ombudsman to cite in an escalation email
- `google-workspace` — for filing the cited document into Drive / drafting the email
- `xurl` — for verifying what Twitter is saying about the same story
