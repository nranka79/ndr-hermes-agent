# Pre-Sales System — Technical Architecture Discussion (21 Aug 2026)

Captured during an architecture-briefing session for the Pre-Sales Lead Management &
Lifecycle System PRD (`/data/hermes/projects/pre-sales-system/`). NDR walked through
his mental model of the system and asked how the proposed architecture realizes it.
This is the agreed design to fold into the formal PRD when it's built.

## The proposed architecture (layered)

- **Layer 1 — Channel/Conversational adapters:** WhatsApp Business API via a BSP
  (Exotel or Ozontel — DRAAS has existing relationships with BOTH; decision needed on
  which + current WhatsApp API setup status). Agentic voice calling via **Sarvam AI**
  (multilingual STT/TTS — Hindi/Kannada critical); open-source fallbacks Whisper (STT)
  / Piper·Coqui (TTS); live pipeline via **LiveKit Agents**. **TRAI/DND-compliance**
  layer: scrub every outbound call against the National DND registry before dialing.
  Email via Gmail/Workspace; SMS via a DLT-registered gateway.
- **Layer 2 — Agent orchestration (the brain):** **LangGraph** (stateful agent
  framework) for the bucket state-machine, human-in-the-loop interrupts, and durable
  per-lead graph persistence. LLM routing via **OpenRouter** (already in use) + optionally
  self-host vLLM/Ollama for volume cost control. Grounding via RAGFlow/LlamaIndex.
- **Layer 3 — Data & context (memory):** **PostgreSQL + pgvector** = single source of
  truth (leads, buckets, append-only event history, workflow state, embeddings). **Redis**
  for cache/queue. **Temporal** (durable workflows) for the FOLLOW-UP CADENCE state machine
  (retry 12h→24h→48h→96h→weekly, reminders, offer-expiry) + human-task escalation.
  **MinIO/S3** for media/content. Kafka only if real-time scale is later needed.
- **Layer 4 — CRM & content:** extend **Kelsa** (existing system-of-record for pipeline),
  build orchestration on top via Kelsa API/MCP — do NOT replace. The **project/area catalog
  lives in Kelsa** (source of truth) but is **replicated locally** (filesystem or pgvector)
  and **synced from Kelsa weekly** (daily if needed) to keep lead-handling calls off Kelsa —
  the catalog (project status, RERA clearance/number, etc.) is largely static, so the
  lead-handling path resolves against the fast local replica, never live Kelsa lookups.
  Content/bait/offer banks
  in a headless CMS (**Strapi / Directus**) so the content team manages tagged content.
- **Layer 5 — Feedback / analytics / agent-training loop:** **Superset / Metabase** (BI),
  LLM post-conversation analysis feeding (a) AI self-improvement context and (b) a
  **persona-testing agent** (role-plays a buyer to test human agents). Observability via
  OpenTelemetry + **Grafana/Prometheus/Loki**.

## The two-engine mental model (KEY insight NDR needed)

**Timing = Temporal (the clock + state-transition engine). Decision-making = LangGraph/LLM
(the brain).** They are separate and talk to each other:
- Temporal creates the "in 15 min do X" cron/reminder, durably (survives restart — a
  24h/48h back-off never gets lost).
- Each time Temporal's timer fires, it wakes the lead's LangGraph agent, which reads full
  context, decides WHAT to send (content bait vs news vs 3D map vs offer), drafts, sends,
  and returns a structured decision. Temporal uses that decision to set the NEXT timer.

So NDR's "15 min later the LLM looks at it and says send a 3D visual map" = `Temporal timer
fires → LangGraph agent reasons → sends → Temporal schedules next timer`.

## The "worker" pattern (how enrichment / bucket-classify / recommend workers work)

Each worker = **(system prompt/skill) + (fixed toolset) + (input/output JSON schema)**,
exposed as ONE callable unit. Two clean packaging options:
- **LangGraph sub-graphs** — reusable sub-agent with own tools + own system prompt; called
  like a function; returns schema-validated output. Most seamless since LangGraph chosen.
- **MCP servers (Model Context Protocol)** — the real enabler for "different workers, fired
  off with inputs, clear skill + tools, API-callable, structured output." Build ONE MCP
  server per worker (enrichment server, bucket-classifier server, content-recommender
  server); orchestrator calls them over MCP like functions. Hermes itself uses this model.

**Social-enrichment worker spec:**
- Input: `{phone, email, name, company?}`
- Skill/prompt: how to search X/Twitter, LinkedIn, Instagram, web; infer role from job title,
  city, financial background from employer, interests.
- Tools: X API, web search, LinkedIn lookup, aggregators.
- Output JSON: `{verified_name, role, company, location, social_links[], interests[],
  financial_signals[], family_signals[], tags[]}` → merged into lead profile, feeding bait
  selection + subtle profiling (§3.6).

## Bucket workflows: NOT step lists — state machines; mid-flow entry

A lead moved into a new bucket has history and must NOT restart at step 1. A bucket workflow
is a **state machine that computes its next action from the lead's actual state**, not a
fixed step counter. Example non-responder bucket: `reach out → wait 5 min → no response →
bait (LLM-chosen) → wait 1 hr → second bait → wait 24h → back-off bait/offer → wait 48h → …`.

When the lead responds, a classifier re-evaluates → moves to high-interest bucket, but the
new bucket STARTS from accumulated state (what's already been sent, declared interest,
requested brochure, weekend timing) — skipping straight to the appropriate next action.
The *state* (history) is separate from the *workflow* (rules); state never resets.

## "Per-lead graph state" explained with a journey (Ramesh)

The graph state is a SINGLE durable object that travels with the lead — a notebook every
step reads/writes. It IS the 360° context.
1. Intake (Meta ad form). State init: `{lead_id, source: meta_ad, phone, email, intent:[Proj X], enriched:{}, history:[], events:[intake], bucket: pending}`.
2. Enrichment worker fills `enriched:{role: engineer, financial_signal:yes, interests:[IRR]}`; event appended.
3. Initial reach-out (Temporal) → WhatsApp template; event appended.
4. No response → Temporal 15-min timer → LangGraph "re-evaluate" → content bait sent; bucket = non-responder.
5. Still silent → baits at 1h/24h/48h (Temporal timer each → LangGraph decision → send → append). State holds full send-history.
6. Ramesh responds ("share brochure, maybe visit this weekend"). Response-classifier node → bucket = high-interest. **State NOT reset.** Site-visit workflow reads `{already_sent:[greeting,5 baits], interests:[IRR], asked_for:brochure, timing:weekend}` → starts MID-WAY: brochure + weekend site-visit + pre-visit pack, no re-greeting.
7. Every later event (visit, feedback, objection, offer) appends to the SAME state object. A human agent taking over reads this one object = complete context.

That single persistent state object is why: bucket changes don't lose history; workflows can
enter mid-flow; "one AI agent with full context" is literally true (agent context = state).

## Reusable open-source stack summary
| Concern | Choice |
|---|---|
| Agent orchestration | LangGraph |
| Durable workflows / cadence | Temporal |
| DB + vectors | PostgreSQL + pgvector |
| Cache/queue | Redis |
| Content/bait CMS | Strapi / Directus |
| Voice ASR/TTS | Sarvam AI + Whisper/Piper |
| Live voice pipeline | LiveKit Agents |
| Analytics/BI | Superset / Metabase |
| Observability | OpenTelemetry + Grafana |
| LLM routing | OpenRouter (+ self-host vLLM) |
| Pipeline record | Kelsa (extend, don't replace) |
| WhatsApp | Exotel or Ozontel (BSP) |

## Two decisions pending for NDR
1. CRM: extend Kelsa (recommended) vs purpose-built core (Twenty/Erxes only if Kelsa API limiting).
2. WhatsApp BSP: Exotel vs Ozontel (both have DRAAS relationships).
