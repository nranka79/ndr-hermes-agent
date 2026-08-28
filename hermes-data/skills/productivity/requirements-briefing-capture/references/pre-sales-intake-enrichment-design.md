# Pre-Sales System — Intake, Normalization & Enrichment Design (21 Aug 2026)

Companion to `pre-sales-tech-architecture-2026-08-21.md` (the full layered stack). This file
captures the intake/normalization + enrichment design NDR walked through on 21 Aug 2026, plus
the reusable design heuristics that emerged. Fold into the formal PRD (§2 Lead Intake, §3
enrichment/cadence) when the briefings are done. The live PRD draft holds the worked example
and tables; this is the decision logic.

## Lead intake & normalization pipeline (channel → canonical lead record)

Two DIFFERENT "normalizations" — conflating them is the confusion NDR had:
1. **Channel adapter = transport only, not understanding.** Each inbound channel (WhatsApp BSP,
   Meta/Google ad form, landing page, portal, website chatbot) has a small adapter whose only
   job is to wrap the raw event in a uniform envelope — channel, sender/phone, timestamp,
   campaign/creative attribution. It passes raw content through untouched. This is what
   "normalizes it into one thing, a lead record" means at the plumbing level.
2. **The system that actually reads content = an LLM normalization worker.** A LangGraph
   sub-graph / MCP worker `(extraction skill) + (JSON output schema)`. Free-form message →
   structured fields.

Pipeline: `channel adapter → canonical lead event → LLM normalization worker → deterministic
post-processing → lead record assembly → fire (courtesy message + bucket classify + background
enrichment in parallel)`.

## THE reusable rule of thumb (applies beyond this system)

> **Exact problems → deterministic code. Fuzzy-semantic problems → LLM assist, still bounded
> by a catalog.**

- **Identity dedupe stays fully deterministic.** Phone/email/social handles are EXACT
  identifiers — no language ambiguity, so never LLM. Scan the whole lead DB across those
  identifiers. New → create record. Existing → do NOT fork a new record; **append the new
  message to the existing lead's event tree**, reload full context (past discussions, projects,
  responsiveness) and factor it into bucketing and the reply. This is the event-sourced
  single-state model — dedupe merges, never forks.
- **Project/area name resolution = deterministic-FIRST, LLM-fallback.** Names are a small,
  CLOSED catalog. Deterministic fuzzy-match (Levenshtein/edit-distance, token-set/subsequence
  ratio) handles typos/aliases/partials ("projct 1", "project one", "Rank Oasiss") exactly,
  cheaply, auditably — **for a closed list, code beats LLM.** Escalate to the LLM (handing it
  the full catalog + listing metadata) ONLY on miss / low confidence, or for SEMANTIC mentions
  ("the premium one in Whitefield"). **Always re-validate the LLM's chosen ID against the
  catalog** — reject hallucinated/nonexistent IDs.

## Catalog source & sync — local replica, weekly sync from Kelsa (NDR decision)

- Canonical project/area catalog **lives in Kelsa** (source of truth — already holds project
  master data).
- Lead-handling system does NOT query Kelsa at call/query time. It keeps a **local replica**
  (filesystem or pgvector) synced back from Kelsa **weekly by default** (daily if needed),
  pulling project status, RERA clearance, RERA number, etc.
- **Why weekly:** the catalog is largely static; given call/query volume, don't hit Kelsa for
  it. Deterministic match and LLM fallback both run against the fast local replica, never live
  Kelsa lookups.

## Enrichment latency model (NDR confirmed)

- Enrichment must NEVER delay the first response. Fire the courtesy/initial message immediately,
  run social-media enrichment **asynchronously in the background**, wait for the user's reply;
  by then enrichment feeds a personalized next message.
- Enrichment is **continuous, not one-shot**: refreshed **daily by default**, with **per-lead
  frequency tiering** (hot/engaging leads enriched more often; cold leads once a day). Goal:
  always hold the latest social-engagement signal.
- Enrichment scope is broader than the user's own posts: also real-estate interest, purchase
  activity, **competitor websites/products they're looking at**, engagement with competitor
  content. Feeds profile, bait selection, and subtle profiling.

## Cadence & channel escalation (NDR confirmed)

- **Respond-but-no-reply interval is bucket-dependent and per-bucket titratable** — a tunable
  parameter per bucket, not one global fixed schedule (refines the fixed timing table in §3.3.1).
- **Parallel channel nudging:** WhatsApp = primary re-reach on the bucket cadence. LinkedIn/X/
  email used in PARALLEL but **nudge-only for now** ("we're trying to reach you on WhatsApp — if
  you prefer another channel, we'll engage there") — used to prompt back to WhatsApp and discover
  preferred channel. **Later phase:** start pushing shared content on those channels too (content-
  bait extended to other platforms).

## Open (still to settle at data-layer detail)
- Should the **dedupe identity lookup** (by phone/email/social handles) also use a local replica/
  cache like the catalog, or hit live data (it needs "today" identity)? NDR hasn't decided — flag
  when the data layer is detailed.
