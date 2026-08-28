---
name: dra-brand-html-teaser
description: >
  Build a brand-styled, image-rich HTML email teaser for a DRA land / brownfield
  / Lloyd-platform deal — the kind of visually-rendered one-pager ndr sends to
  family members, prospective investors, and counterparties. Bridges data from
  the Kelsa land-proposal pipeline (source of truth) and a Gmail draft (delivery
  surface, via the email-drafter skill). Use when ndr says "build a teaser",
  "prepare a teaser email", "visually rendered HTML", "presentable teaser",
  "DRA homes brand", "Lloyd-platform pitch", "brownfield teaser", or asks for
  an HTML email body that uses the DRA homes color palette, fonts, and logo.
  Distinct from email-drafter (basic plain-text / simple HTML drafts) and from
  kelsa-land-proposal (data entry into the Kelsa record).
metadata:
  hermes:
    tags:
      - real-estate
      - draas
      - dra-homes
      - email
      - teaser
      - html
      - brand
related_skills:
  - kelsa-land-proposal
  - email-drafter
  - personal-messaging
---

# DRA Brand HTML Teaser

## When to use this skill

ndr wants a **visually rendered, brand-styled HTML email body** that introduces
a real-estate opportunity — typically to a family member, an investor, or a
counterparty. The deliverable is the **HTML body of a Gmail draft** (not a
PDF, not a Deck, not a Drive Doc). The body must look like a one-pager: logo,
hero, key numbers, optional image gallery, CTA, footer — all in the DRA homes
brand.

Triggers:
- "build a teaser", "prepare a teaser email", "presentable teaser"
- "visually rendered HTML", "HTML email body with images"
- "DRA homes brand", "Lloyd-platform pitch", "brownfield teaser"
- Voice messages that mention: "nice presentable teaser", "DRA homes colors
  and templates and fonts", "hyperlink images straight from S3", "rendered
  HTML in the email body"

When the user wants a **plain text** or **simple HTML** email instead, defer
to `email-drafter`. When the user wants the source data entered into Kelsa
first, defer to `kelsa-land-proposal`. When the user wants a printed PDF, use
this skill's output as a base and then convert.

## Workflow

### Step 1 — Confirm the deal and brand

Ask the user to confirm (or extract from prior context):

1. **Project name** (Skylark Zenith, Thylagere 10-acre, etc.)
2. **Deal type** (Brownfield / Villa / Apartment / Commercial / Lloyd-platform
   pitch)
3. **Recipient** (and which family / investor cohort)
4. **Which brand**: DRA homes (default — `drahomes.in` palette), DRAAS
   (investor / darker), or a hybrid (dark surface + gold accent — common for
   Lloyd-platform pitches)
5. **Sender account**: by default `ndr@draas.com` (DRAAS is the work identity
   even for DRA-homes-brand teasers; the recipient's `@drahomes.in` domain
   does not change the sender — see Step 5 below)

If the deal is in Kelsa, pull the project name, location, and any images
from the existing Kelsa record (see "Data sources" below).

### Step 2 — Pull data + images

Three sources, in order of preference:

1. **Kelsa land-proposal record** (most likely). The lead has
   `cf_land_location`, `cf_land_size_sqft`, `cf_expected_total_built_up_area_in_sqft`,
   `cf_offer_type`, `cf_product_type`, `cf_proposal_notes`, and the
   attachment fields `cf_land_pics` (multi-file images/videos) and
   `cf_offer_document` (the IM/PPTX). The S3 image URLs are exactly the
   pattern `https://kelsa-clients-production.s3.ap-south-1.amazonaws.com/uploads/accounts/5/pipelines/519/files/<uuid>/<filename>`
   — copy them straight from the lead page or from a successful
   `kelsa_call_tool(get_lead)` call.

2. **Drive folder** (if the deal pre-dates Kelsa). Look in the relevant
   `Skylark <Project>`, `Brownfield`, or `Lloyd Platform` folder. Image
   files (`image/jpeg`, `image/png`, `image/webp`) and layout plans go in
   the gallery.

3. **Voice-note facts** (always present, often the only source for size,
   floor count, parking, location context, micro-market details). Capture
   verbatim: 64,000 sqft across four floor plates, near metro / hospital,
   electronic city, brownfield, etc.

When the Kelsa MCP is down (Pitfall 20 in kelsa-land-proposal) and the user
has shared the lead URL, **ask the user to paste the image URLs** rather than
blocking on the MCP. Right-click each image on the Kelsa lead page → "Copy
image address" → paste back.

### Step 3 — Choose template variant

Three variants live in `templates/`:

- `teaser-deal.html.j2` — Brownfield / commercial deal (Skylark Zenith shape:
  hero with project name + 1-line tagline, opportunity body, key-numbers
  stat grid, 3–6 image gallery, CTA, footer)
- `teaser-land.html.j2` — Raw land deal (Thylagere 10-acre shape: hero,
  location, size + price, JV/GD structure, team context, CTA)
- `teaser-lloyd-platform.html.j2` — DRA Lloyds platform pitch (darker palette,
  cross-deal stat block: AUM / pipeline / deployed / IRR, single hero
  "Platform Overview" + multiple project cards)

Pick based on the deal type. For ad-hoc shapes, edit the closest template.

### Step 4 — Build the HTML

```python
import os
from pathlib import Path
from jinja2 import Template

# Use the brand reference (dra-homes-brand.md has the full palette + base CSS)
base_css = open(
    "/data/hermes/skills/productivity/kelsa-land-proposal/references/dra-homes-brand.md"
).read()  # actually load from references/dra-brand-teaser/baseline.html

template_str = open(
    "/data/hermes/skills/productivity/dra-brand-html-teaser/templates/teaser-deal.html.j2"
).read()
html = Template(template_str).render(
    project_name="Skylark Zenith",
    tagline="~64K Sqft Ready-Made Commercial Building — Hosur Road",
    location="Sy. No. 41/C, Hosur Main Road, Near Hosa Metro",
    opportunity_body=(
        "Brownfield commercial building, ready for refurbishment and "
        "lease-out. Bank + owners selling as-is for outright purchase. "
        "G+6 with three basements, ~64,112 sqft leasable across four "
        "floor plates, with adequate parking. Micro-market is hot: "
        "opposite an existing hospital, on the Electronic City main road, "
        "next to the Hosa Road metro and just before the Cloverleaf "
        "flyover. Ground floor can be leased to a hospital / showroom; "
        "upper floors to office tenants."
    ),
    stats=[
        ("64K", "Sqft leasable"),
        ("4", "Floor plates"),
        ("∞", "Adequate parking"),
    ],
    images=[
        "https://kelsa-clients-production.s3.ap-south-1.amazonaws.com/uploads/accounts/5/pipelines/519/files/<uuid1>/site_photo_1.jpg",
        "https://kelsa-clients-production.s3.ap-south-1.amazonaws.com/uploads/accounts/5/pipelines/519/files/<uuid2>/site_photo_2.jpg",
        # ...
    ],
    cta_link="mailto:ndr@draas.com?subject=Skylark%20Zenith%20%E2%80%94%20Interest",
    cta_label="Let's Discuss",
)
```

### Step 5 — Pick the sender account (HARD rule)

**Default sender: `ndr@draas.com`.** This applies even when the recipient's
email is at `@drahomes.in` (e.g. brother-in-law `drr@drahomes.in`).
DRAAS is the work identity; the DRA homes brand is the visual identity. The
two are different.

Switch the sender to `nishantranka@gmail.com` ONLY when the user explicitly
says so ("send from my personal account", "from my Gmail"). Otherwise
`ndr@draas.com` is correct.

When in doubt about the recipient's address, use the `gws_resolve_account`
tool to confirm the recipient's account, not to determine the sender.

### Step 6 — Create the Gmail draft

Hand the rendered HTML to the `email-drafter` skill workflow. Pass `html=True`
to `draft_create` so the recipient sees rendered HTML, not raw literal
markup. Confirm with the user before any actual send (the email-drafter
skill already enforces draft-only for ndr — never autonomously send).

```python
from tools.gws_skill_bridge import call
result = call("draft_create",
    service_name="google-draas",
    to="drr@drahomes.in",
    subject="Opportunity: Skylark Zenith — ~64K Sqft Brownfield Commercial, Hosur Road",
    body=html,
    html=True)   # <-- required
```

**NEVER** use `gmail_send` / `gmail_reply` — those are hard-blocked for ndr.
The teaser is ALWAYS a draft for the human to review and send.

## Brand reference

The full DRA homes palette, fonts, logo URLs, and an inline-style baseline
HTML recipe live in
`/data/hermes/skills/productivity/kelsa-land-proposal/references/dra-homes-brand.md`.
That file is shared between this skill and `kelsa-land-proposal` (source
record). The shared file keeps the palette in one place — update it there,
not here.

If the brand reference is missing, regenerate it by `curl https://drahomes.in`
and extracting the dominant `color:` values from the inline `<style>` block
(see the kelsa-land-proposal "Brand & visual identity" references section for
the exact regex set).

## Pitfalls

1. **`html=True` is required when calling `draft_create` with HTML body.** Without
   it, the bridge wraps in `MIMEText(..., "plain")` and the recipient sees
   the entire `<!doctype>...<table>...` literal. This is the most common
   bug in this skill. Always pass `html=True`.

2. **Gmail clips HTML over 102KB.** The DRA homes brand CSS imports a
   Google Fonts stylesheet at the top — that's 1–2KB. With 6 images and a
   full stat grid, teasers typically land at 40–70KB. If you exceed 80KB,
   strip the `@import` and inline only the font names (clients fall back to
   system sans-serif gracefully).

3. **Outlook ignores `<style>` in `<head>`.** The teaser templates put
   critical styles inline on each element so they survive Outlook's
   rendering. The header/footer `<style>` block is for Gmail and web; the
   inline styles are the safety net.

4. **Do NOT base64-embed images.** Use absolute S3 URLs. Base64 inflates
   the body past Gmail's clip threshold and makes the draft uneditable.

5. **Do NOT promise to retry the MCP "one more time" when it's down.** When
   the Kelsa MCP rejects integer args (Pitfall 20 in kelsa-land-proposal),
   switch immediately to the lead-URL fallback: ask the user to paste the
   image URLs. Retrying wastes user time and erodes trust.

6. **Image URLs from Kelsa S3 are private bucket — they WILL render in the
   recipient's email client if the recipient's Kelsa session is logged in on
   the same browser**, but they will NOT render in arbitrary email clients
   (Gmail web, Outlook, Apple Mail). If the recipient is external, prefer
   uploading the images to a public surface (Drive, then `uc?export=view`
   link) and using those URLs in the teaser. Detect external recipients by
   checking the email domain: anything not ending in `@draas.com`,
   `@drahomes.in`, `@truliv.in`, `@draaadithya.in`, or a known DRA-group
   domain is external.

7. **The teaser is always a draft.** Even when the user says "just send it",
   create the draft and tell them to review + send. This is the same
   safety rule as email-drafter — `gmail_send` is hard-blocked for ndr.

8. *(removed — merged into Pitfall 9a below)*

9. **When the Kelsa MCP + browser backend are both offline, ship the teaser
   anyway with a Google Maps link instead of S3 images.** Don't block on
   site photos if the rest of the deliverable is ready. The skill template
   already supports omitting the `images` array (the `{% if images %}` block
   hides the gallery cleanly), and the location strip can carry a
   `<a href="https://maps.google.com/?q=<location>">Open in Google Maps</a>`
   button that the recipient can click to see exactly where the property is.
   This was the working path for the 2026-07-14 Skylark Zenith teaser.
   **9a. Kelsa share links (`kelsa.io/s/<slug>`) are NOT lead IDs.** When
   the user pastes a share link like `https://kelsa.io/s/xzgeeka4te`, you
   cannot extract the underlying lead_id from the slug. The full lead URL
   is the one with `current_item_id=<digits>` — e.g.
   `https://kelsa.io/519/leads?current_view=list&current_item_id=53692993&...`.
   The share slug works in the browser but is useless for the MCP. Ask the
   user for the full URL or the lead ID, not the share link. Confirmed in
   the 2026-07-14 Skylark Zenith session.

   **9b. Stat grid is a hard 3-up loop.** `teaser-deal.html.j2` renders
   `stats` as `<td width="33%">` cells in a single row of three. Passing
   4 or more entries would overflow the template (the for-loop emits them
   all into one row). For 4+ stats, manually wrap in a second table row or
   pick the three most important. For 1-2 stats, leave the third cell
   empty (the template does not pad).

   **9c. Empty `images=[]` gracefully drops the Site Visuals section.**
   The `{% if images %}` guard means a teaser with no images renders
   cleanly without an empty gallery header. Use this as the fallback when
   image sourcing is blocked — stage the teaser without photos, then
   re-render with `images=[...]` and recreate the draft once URLs arrive.
   `draft_create` always creates a NEW draft; there is no in-place update
   for Gmail drafts from this bridge, so re-render to the same local HTML
   file and recreate the draft, telling the user the old draft can be
   deleted.

## Linked files

- `templates/teaser-deal.html.j2` — brownfield / commercial deal variant
- `templates/teaser-land.html.j2` — raw land variant
- `templates/teaser-lloyd-platform.html.j2` — DRA Lloyds platform pitch
- `references/cta-recipes.md` — common CTA link / label patterns
- `references/image-fallback-chains.md` — when S3 is private, where to mirror

The full DRA homes brand palette + baseline CSS lives in the
kelsa-land-proposal skill's `references/dra-homes-brand.md` (shared,
class-level asset).
