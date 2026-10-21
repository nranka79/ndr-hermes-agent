# Structural Condition Assessment & Facade Refit — reading the evidence, and answering "is the frame OK?"

**When to use.** NDR is refurbishing a standing RCC building and asks whether the structure is
sound enough for the proposed works. Triggers: "analyse the structural report", "is the structure
good enough", "do we need to do anything else", "we're only taking away the extensions / chajjas
and putting a modern facade". Also covers the **scoping** of a non-destructive test (NDT) package
and reviewing the vendor's quotation.

Precedent: **Millers Road (Akbar Hussain office building)** — India Chai office building, ~20-yr-old
RCC, G+4, ~2,600 sq ft per floor plate, lease to Akbar Hussain / AH India. Facade reference image
comes from the neighbouring India Chai building. Tracked as **P-136** (Anbu, façade costing) and
**P-211** (NDR, structural condition assessment) in `NDR_Master_Task_Tracker`.

---

## 1. Two vendors, two scopes — never merge them

| Vendor | Who | Scope | Artefact |
|---|---|---|---|
| **Nova Spaces** | Zakir Kalami `zaak@novaspaces.in`, cc hannan@ / imran@novaspaces.in | Full asset upgradation proposal (façade + structural repairs + MEP + lifts + fire) | "DRA Asset Upgradation Proposal", 10 Aug 2026 (`Ranka_Asset Upgrade_Proposal.pdf`) |
| **Nordstar Novaspaces** | Kiran Kumar | **Structural testing only** (NDT package) | Quotation → NDR's revised-scope email 31 Aug 2026 |

The Nova Spaces proposal reached NDR twice: direct (10 Aug) and forwarded via **Aamir Khan**
`khan.hussain.aamir@gmail.com` (19 Aug). Nova Spaces is the *refurbishment* vendor; Nordstar is the
*testing* vendor. A similar name is not the same firm.

## 2. The Stage-1 NDT scope NDR approved (31 Aug 2026 email)

Sent to Aamir Khan, addressed "Dear Mr. Kiran Kumar / Team", cc Anbarasan `pm2.blr@draas.com`.
Subject: *Proposed Structural Tests for India Chai Office Building*. The objective as stated: establish
the present condition of the ~20-yr-old RCC structure, **particularly deformation/deflection, visible
deterioration and concrete quality**.

**In scope:**
1. **Visual structural condition survey** — all accessible RCC members (columns, beams, slabs), all
   floors; cracks/distress, spalling, exposed reinforcement/rust, water damage, other distress.
   Photographic + video documentation with **identifiable locations**.
2. **High-accuracy 3D laser / geometric deformation survey** — terrestrial laser scanning, point
   cloud, supplemented by total station / precision levelling. Outputs: slab/floor sagging and
   differential levels, beam deflection, column inclination/deviation from vertical. Vendor must
   specify **equipment make/model and expected accuracy** (order of a few mm).
3. **Rebound hammer** — systematic coverage of all accessible columns and beams, all floors,
   **per applicable IS procedure**, results **mapped member-by-member**. Not one reading in the middle.
4. **Targeted UPV** — *conditional only*. "Not required as a blanket test at all locations." Undertaken
   selectively where rebound results or visual inspection flag an area needing further investigation
   of internal condition/uniformity.

**Explicitly NOT proposed at Stage 1 (with reasons — reproduce these):**
- **Rebar scanning** — not routine; may be done later, and **always before any core is extracted**.
- **Concrete core testing** — not routine; only if visual/NDT findings require actual in-situ strength.
  Any core in a beam/column/member must be **preceded by rebar scanning and approval of the core location**.
- **Soil SBC** — not proposed: the structure has stood and been in use ~20 years, which is itself the
  evidence that the foundation is adequate. Reconsider only if condition assessment reveals a
  foundation/settlement concern.
- **STAAD / ETABS analysis** — not part of initial condition assessment; separate stage if findings warrant.

**Vendor must quote:** methodology per test, applicable IS standard and procedure, equipment make/model,
quantities/basis of testing, deliverables/reporting, commercials — **plus separate per-unit rates for the
conditional UPV, rebar scanning and core testing** so they can be triggered later without renegotiation.

Rationale worth keeping: the sequence is **visual + laser first, then rebound, with UPV / rebar / cores
conditional on findings.** This prevents a fixed-price blanket NDT package being bought before anyone
knows where the problems are — which is exactly what the original vendor quotation (18 rebound, 18 UPV,
15 rebar scans, 4 cores, 2 soil SBC) did.

## 3. Answering "do we need more testing, or is this good enough?" — the load-path reasoning

The question splits into a part that **does not depend on the report** and a part that does.

### 3a. Removing external projections is NOT a structural risk to the frame

**Key insight to state plainly:** cutting away the **chajjas / window canopies / sunshades and all
external extensions** *removes dead load* from the beams and columns. It never makes the frame worse.
There is no load path that the chajja *carries* — it is a cantilever hanging *off* the frame. So
"will the building still stand after we take the projections off?" is not the real question.

**The real risks are these two, and neither is "the frame is weak":**

1. **Slab/beam edge where the cantilever steel is anchored.** The chajja's top reinforcement is
   anchored into the slab or beam edge. Cut it carelessly and you expose the top steel at the
   anchorage zone, which then carbonates and corrodes. This is a **durability / repair-detail**
   problem, not a strength-of-frame problem. Mitigate by: locating the rebar before cutting (which is
   why rebar scanning is *conditional-but-before-cutting*), cutting back to the correct line, and
   properly treating/sealing the exposed edge.
2. **New façade's wind loading being hung off the existing frame.** Structural glazing, aluminium
   cladding and aluminium railings impose wind load on whatever they are fixed to. That needs proper
   design of the fixing and its connection back to the frame — **not simply bolted on.** This is the
   genuinely new load case the refurbishment introduces, and it is the item that most deserves an
   engineer's signature.

### 3b. What the tests are actually for, then

Given 3a, the testing is **not** a strength test of the frame. It is:
- a **durability** check — confirm the concrete is sound and **not carbonated** precisely where you
  are cutting (rebound hammer mapped member-by-member, plus visual);
- a **condition baseline** — record the existing deformation (slab sag, beam deflection, column
  verticality) so that any movement later is attributable, and so the façade fixing design starts
  from real as-built geometry rather than drawings;
- a **trigger list** — decide which locations warrant UPV / a core.

For a 20-year-old RCC frame that has been continuously occupied, a visual + rebound survey is
usually sufficient to clear a façade-only refit. **What must have an engineer's sign-off is the
façade fixing / wind-load connection, and the slab-edge cutting detail** — not a blanket strength
certificate.

### 3c. What to say when the report does not exist

Do not present adjacent documents as the findings, and do not answer the "reported numbers" question
from principle. Say: no report exists; here is what the structural logic says about the *proposed
works* (3a); here is what the tests would establish (3b); and here is the stage the matter is
actually at (per email + tracker). The absence-verification sweep is in the `email` skill,
`references/email-forensic-thread-lookup.md` § Step 2b.

## 4. Façade costing scope (P-136, Anbu) — what NDR asked for

Facade-only costing, entire front face **+ ~30% on each side face ≈ 1.6× the front surface area**:
- demolition / cutting away existing concrete projections
- debris removal
- touch-up / preparation work
- installation of aluminium railings
- installation of glass façade & aluminium cladding

Look = the neighbouring India Chai building (reference image in the Nova Spaces proposal).
**Open blocker:** Kantesh (20 Aug) asked NDR for **building dimensions** before he can estimate.
That request is outstanding — do not re-ask Anbu for costing without first supplying the dimensions.

## 5. Pitfalls

- **Do not merge Nova Spaces and Nordstar Novaspaces**, and do not treat the Nova Spaces façade
  proposal as evidence about the structure's condition — it is a commercial proposal with a façade
  reference photo, nothing more.
- **Do not analyse a report that does not exist.** Verify first (§ Step 2b of the email reference).
- **Do not accept a blanket NDT package.** The whole point of the revised scope is that UPV, rebar
  scanning and cores are conditional and separately priced.
- **Do not propose soil SBC testing** for a building that has stood 20 years — the standing structure
  is the evidence. It signals you have not understood the brief.
- **Rebar scan before every core. Always.** Cores through reinforcement without locating it first
  damage the member and produce invalid strength data.
- **Outstanding dependency:** Kantesh needs building dimensions from NDR for the façade estimate.
