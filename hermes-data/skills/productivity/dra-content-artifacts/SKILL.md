---
name: dra-content-artifacts
description: 'Publish, update and verify artifacts in the DRA Content system (content.ahfl.in) — interactive HTML comparators, visual studies, reports, dashboards. DRA Content holds WEBSITES: HTML plus the CSS, JavaScript, images, fonts and data such a page renders. Standalone documents (PDF, Word, Excel, PowerPoint) go to Google Drive instead, never here. Carries the routing rule, render-origin constraints, publishing routes, classification and sharing discipline, and the verification recipe. Multi-file artifacts with external CSS, external JavaScript and real image files are SUPPORTED - the opaque-origin/CORP restriction that once forced single self-contained files was a platform bug, fixed 2026-09-27. TRIGGERS — "publish this to our content publishing system", "put this on content.ahfl.in", "create an artifact", "make this an interactive HTML and publish it", "update artifact DRA-ART-...", "share the artifact with X", "the artifact looks broken / unstyled / images are missing", "the published page is blank".'
---

# DRA Content Artifacts (publish / update / verify)

Class-level skill for putting a deliverable into the DRA Content system and
proving it actually renders there. The publishing API is easy; the **render
origin is hostile to normal web pages**, and that is the part that wastes hours
if you do not know it up front.

Sits downstream of whatever produced the content — e.g.
`reference-driven-image-variation` (N variation renders), `html-presentations`,
`business-dossier`, `private-investment-due-diligence`.

## WHAT GOES WHERE (decide this first)

**DRA Content holds websites.** An artifact is a page and everything that page
renders: `index.html` plus its CSS, JavaScript, images, SVG, fonts, and JSON or
CSV data files. If the deliverable is something a browser renders as a page,
it belongs here.

**Google Drive holds documents.** A PDF, Word file, spreadsheet or slide deck is
a document in its own right. Drive already files it, permissions it, and can
edit it. File it there per `draas-drive-organization` and hand over the Drive
link. **Do not also publish it here** - that would put one file under two
independent permission systems, and this one cannot see or enforce Drive's.

| Deliverable | Destination |
|---|---|
| Interactive HTML, comparator, dashboard, visual study | **DRA Content** |
| Reveal.js slide deck (it is an HTML page) | **DRA Content** |
| Report or brief the user wants as a web page | **DRA Content** |
| Google Doc, Google Sheet, Google Slides | **Drive only** |
| `.pdf`, `.docx`, `.xlsx`, `.pptx` | **Drive only** |
| A `.zip` of anything | **Drive only** |

The word "presentation" splits across that line: a **Reveal.js deck is HTML and
belongs here**; a **Google Slides or `.pptx` deck belongs in Drive**. Decide by
format, not by the word the user used.

This is enforced, not merely advised. `content_publish` / `content_update`
reject document extensions with a message naming Drive, and content-api's own
path validation rejects them too - so the direct-API route below cannot be used
to get around it either. If you find yourself wanting an exception, the answer
is a Drive link in the artifact, not the document inside the artifact.

Do not publish a plain conversational answer as an artifact. A one-line answer
to a question is not a deliverable.

## THE ONE RULE THAT DECIDES EVERYTHING

**Build multi-file.** CSS in its own file, JavaScript in its own file, images as
their own files. Inline `<script>` is the only thing still blocked.

> **History, because this file said the exact opposite until 2026-09-27.** The
> renderer used to frame each artifact in an iframe sandboxed without
> `allow-same-origin`, which put it in an *opaque origin*. There, CSP `'self'`
> matches nothing and `Cross-Origin-Resource-Policy: same-site` can never be
> satisfied, so every external subresource was blocked and no artifact could
> load its own CSS or JavaScript. The advice that used to be here - single
> file, inline `<style>`, `data:` images, no JS - was a correct diagnosis of a
> real platform bug and a sound workaround. **The bug is fixed.** The iframe,
> the `sandbox` directive and the CORP header are all gone. Keep applying the
> workaround and you get multi-megabyte pages that cannot be cached per image
> and lose every interaction.

### Measured capability matrix (re-verified 2026-09-27, after the fix)

Artifacts are served as ordinary top-level documents at
`view.content.ahfl.in/d/<slug>/v/<n>/<file>`. No iframe, no sandbox, no CORP.
`content.ahfl.in/a/<id>` still authenticates and checks the ACL, then redirects.

```
Content-Security-Policy: default-src 'none'; script-src 'self';
  style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:;
  font-src 'self' data:; media-src 'self' data: blob:;
  connect-src 'self' https://content.ahfl.in; form-action 'none';
  base-uri 'none'; object-src 'none'; frame-ancestors 'self'
Referrer-Policy: same-origin
```

| Mechanism | Result |
|---|---|
| `<link rel=stylesheet href="styles.css">` | **works** |
| `<script src="app.js">` | **works** |
| `<img src="img/v01.webp">` (real file) | **works** |
| `/lib/*` shared libraries (Reveal.js, Chart.js, Mermaid) | **works** |
| inline `<style>` and `style=""` | works (`style-src` has `'unsafe-inline'`) |
| `<img src="data:...">` | works, but stop doing this for real images |
| inline `<script>` | **BLOCKED** - still no `'unsafe-inline'` in `script-src` |
| `fetch()` to the API origin | works (the analytics beacon) |

Two rules are new, and both fail in ways that look like something else:

- **Never nest an HTML comment.** HTML comments do not nest: the first `-->`
  ends the comment and everything after becomes live markup. A stray `<script>`
  created that way swallows every tag up to the next `</script>`, usually a real
  library include. This exact mistake sat in the deck template and left every
  presentation inert while every file still returned 200.
- **Never set `<meta name="referrer">`.** All artifacts share the render origin,
  so the renderer requires a same-artifact `Referer` to stop one artifact
  reading another, and it fails closed. Suppressing the referrer costs the
  artifact its own stylesheet and scripts.

Consequences to design around, replacing the old ones:

- **JavaScript works.** Build real carousels, tabs, lightboxes and thumbnail
  strips. The pure-CSS `:checked` tricks are no longer necessary.
- **Images are files.** Pass each as
  `{"path": "img/v01.webp", "source_path": "/data/hermes/tmp/.../v01.webp"}` to
  `content_publish` / `content_update`; the tool reads the bytes itself. Do not
  base64 them yourself, do not inline them as `data:` URIs, and do not host them
  in Drive and link out. Still downscale before uploading - 880 px WebP q74 for
  full size, genuinely separate ~190 px thumbs - but now for bandwidth, not to
  keep one HTML file from exploding.
- **Fonts** may be `'self'` or `data:`. Shipping a `.woff2` inside the artifact works.
- **Analytics work.** Load `_token.js` and then `/lib/dra-content.js`, in that order.
- `scripts/csp_probe.py` still measures headers correctly, but the headers it was
  written against have changed. Re-read them from a live response before trusting
  any conclusion drawn from it.
- There is now a real browser test on the server: `ops/browser_smoke.sh` in the
  dra-content repo drives headless Chromium and asserts that subresources
  actually execute.

## Step 1 — Publish

### Small, text-only artifacts → the `content_publish` tool is fine

`content_publish` works for normal text artifacts. It takes file contents as
JSON string arguments.

### Image-bearing artifacts → the tool handles these too, now

**Use `content_publish` / `content_update` with `source_path`.** As of
2026-09-27 the tool uploads binary by reference: you name a file already on
disk and the tool reads and base64-encodes the bytes itself, so nothing large
passes through your context.

```json
{"path": "img/v01.webp", "source_path": "/data/hermes/tmp/renders/v01.webp"}
```

Limits: 20 MB per file, 20 MB per version, and **200 FILES per version**
(the request is JSON, base64 inflates by a third, and nginx caps the body at
30 MB). The file-count cap is the one that bites — an image comparator blows
past it long before it blows past the byte caps.

### The 200-file-per-version cap — pack sprites, do NOT thin the set

content-api rejects a version with more than 200 files:
`HTTP 422 {"detail":"311 files exceeds the limit of 200"}`. It is **not** in the
OpenAPI schema (`VersionCreate.files` declares `minItems: 1` and no `maxItems`)
and there is no repo or container access from here to raise it — treat it as hard.
Probe it cheaply the same way you probe the token: a rejected POST answers in
under a second, so you find out at publish time, not at build time.

Sizing that bites: 28 views x (10 variations + 1 original) + 3 text = **311 files**.
Do NOT solve this by dropping variations or views — that silently changes the
deliverable the user asked for. **Pack each group of images into one sprite
sheet** and render the cells with CSS `background-position`. The 280 variations
become 28 files; every image keeps full quality and full interactivity. Measured
on DRA-ART-2026-000034: 311 files / 11.56 MB -> **59 files / 11.35 MB**
(b64 15.13 MB, inside both caps). Note the byte size barely moved — the blocker
is the COUNT, so pack; do not re-compress to chase a size that was never the
problem.

`scripts/pack_sprite_sheets.py` builds the sheets.
`references/file-count-limit-and-sprites.md` has the geometry, the CSS, the
lightbox pattern and the verification gotcha. Choose this over a contact sheet
(merges images into one picture, loses per-item zoom) and over splitting into two
artifacts (splits the share the user asked for as one link).

The older advice here was to bypass the tool because it refused binary and
could not carry a multi-MB payload. Both are fixed. Prefer the tool.

### Direct content-api route — only when the tool genuinely cannot

`scripts/publish_artifact.py` POSTs to the same endpoint the tool uses. Reach
for it only for something the tool cannot express, not as the default:

```
POST {DRA_CONTENT_API_URL}/api/artifacts
Authorization: Bearer {DRA_CONTENT_SERVICE_TOKEN}     # transport credential
X-DRA-On-Behalf-Of: ndr@draas.com                     # ACL evaluated as this person
Content-Type: application/json

{"title": ..., "files": [{"path": "index.html", "content_b64": "<b64 of UTF-8 text>"}],
 "entry_file": "index.html", "artifact_type": "comparison",
 "project": "Ranka Oasis", "category": "Design", "tags": [...],
 "source_session_id": ..., "change_summary": "Initial version"}
```

Notes that save time:
- `content_b64` is base64 of the file's bytes. Text or binary both work here;
  the same path validation and extension allowlist apply as through the tool,
  so document extensions are rejected on this route as well.
- `X-DRA-On-Behalf-Of` must be the requesting human (`ndr@draas.com`), not the
  service identity, or the ACL will not grant the right person access.
- The creation response returns `human_id` (e.g. `DRA-ART-2026-000024`),
  `current_version` and `url` (`https://content.ahfl.in/a/<human_id>`).
- **Never print the service token.** Read it from the environment only.
- Set a generous client timeout — a 3–4 MB POST is fine but a 20 s default is tight.

### Updates → new version, same ID

`POST /api/artifacts/{human_id}/versions` with the same `files` shape plus
`change_summary`. The artifact ID and canonical URL are stable; the previous
version stays retrievable. Use this rather than publishing a second artifact
when you are fixing a rendering problem on something already shared.

**Publishing a new version does NOT update the title.** After v3 went live the
artifact still read "…(30 variations)" until a separate
`PATCH /api/artifacts/{human_id}` with `{"title": "…"}` fixed it. If your content
changed the headline facts (variation count, scope), PATCH the title too — check the
title after every version push.

**The version record's `checksum` field is NOT the sha256 of the stored file.**
Observed on both v2 and v3 of `DRA-ART-2026-000024`: the published checksum
(`f62003…`) matched neither the local file hash nor b64 / gzip / zlib / path-prefixed
variants. Do not use it for byte-identity. The fields that DID match were
`size_bytes` (4,161,126 == local) and `entry_file`. Verify with size + a real render
of the live page, not the checksum.

### Discovering the API surface

`/api/openapi.json` (with the bearer headers) lists every route —  `/openapi.json`,
`/docs`, `/api/docs` vary. Known route set (2026-09-27): `GET,PATCH
/api/artifacts/{identifier}`, `POST /api/artifacts`, `POST
/api/artifacts/{identifier}/archive|export|export/complete`, `GET,POST
/api/artifacts/{identifier}/permissions`, `DELETE …/permissions/{permission_id}`,
`GET,POST /api/artifacts/{identifier}/versions`. There is **no raw-file-serving
route** (`/files`, `/versions/{n}/file`, `/download` all 404) — the ONLY byte-level
view is the render origin, so Step 2's browser check is not optional. Also probed
and 404 (each returns a 22-byte body — **do not re-probe these**): `/api/artifacts/{id}/content`,
`/api/artifacts/{id}/view`, `/api/artifacts/{id}/versions/{v}`,
`/api/artifacts/{id}/versions/{v}/content`, `/api/versions/{v}`,
`/api/versions/{v}/content`, `/view/{v}`, `/v/{v}`, `/render/{v}`.

## Step 2 — Verify it actually renders (do NOT skip)

Serving 200 proves nothing. The failure mode is a 200 page that is unstyled with
broken images.

1. **Get the iframe URL.** The shell page at `https://content.ahfl.in/a/{id}`
   embeds the artifact in an iframe whose `src` is a signed capability URL on
   `view.content.ahfl.in/r/<token>/index.html`. Fetch the shell and grep it out:
   ```bash
   curl -s "$DRA_CONTENT_API_URL/a/$ART" -H "Authorization: Bearer $TOKEN" \
        -H "X-DRA-On-Behalf-Of: ndr@draas.com" \
     | grep -oE 'src="https://view\.content\.ahfl\.in/r/[^"]+"' | sed 's/^src="//;s/"$//'
   ```
   **Check the STATUS CODE before you grep — the shell route answers in two
   different shapes.** With valid bearer headers it may return the 200 shell
   with the iframe inline (grep works), OR a **302** whose body is EMPTY and
   whose `Location` is a signed capability URL of the form
   `https://view.content.ahfl.in/_open?t=<token>` — grep then finds zero
   `src=` and reads as "this artifact has no iframe". Both shapes were observed
   on the SAME artifact (2026-09-27). Unauthenticated, the route 302s to
   `/auth/login?next=/a/<id>`. So use `curl -i` or
   `-w '%{http_code} %{redirect_url}'`, follow the redirect, and read the
   capability URL out of `Location` when there is no body. Do not hardcode the
   URL shape: `/r/<token>/index.html` and `/_open?t=<token>` are both live.
   **A signed capability URL is frequently NOT fetchable server-side.** A plain
   `urllib.urlopen()` of the `_open?t=…` URL returned **403** — it expects a
   browser cookie jar, and no amount of header-fiddling fixes it. Do not burn
   attempts: hand it to the browser tool, or use the API-metadata fallback
   below and finish with a browser load of `/a/{id}/v/{n}`.
   **API-metadata fallback when the served bytes are unreachable:** `GET
   /api/artifacts/{id}` → `current_version`; `GET /api/artifacts/{id}/versions`
   → per version `size_bytes`, `file_count`, `entry_file`,
   `publication_status`. `size_bytes == len(local_file)` together with
   `file_count: 1` and `entry_file: "index.html"` is strong evidence the
   single-file build is what got stored, and it is the cheapest honest check
   when the render route will not give up its bytes. Pair it with the browser
   render check — never report "live" on metadata alone.
   `scripts/verify_artifact_version.py` performs all of the above in one call.
   **Re-fetch this URL after EVERY version update.** The signed capability URL
   is pinned to the version that was live when it was issued — after a new
   version is pushed, the old URL keeps serving the OLD bytes (an md5 compare
   against the old build looks like a false pass). Observed 2026-09-27: pushed
   v3, loaded the v1 URL, byte-compare matched the OLD local file until the
   shell page was re-grepped for a fresh `src`.
2. **Byte-compare the served page against your local build** (`md5sum` both).
   A mismatch means the wrong version is live.
3. **Load that iframe URL directly in the browser** — it is a capability URL, so
   no SSO login is needed, and the CSP's `sandbox` directive applies to a
   top-level visit too, making it a faithful test. Then check console errors and
   take a screenshot. **Look at it.** In this session the published page passed
   every HTTP check and was visibly unstyled with broken images.
4. **Confirm the mechanisms your design depends on are the allowed kind** —
   inline `<style>` and `data:` images, nothing else.

The artifact page itself sits behind Google SSO for a human, and the default ACL
grants **ADMIN to the creator and to `rnr@draas.com`** — so the owner can open it
without any extra share call. Read permissions back via
`GET /api/artifacts/{id}/permissions` before claiming who can see it.

## Step 3 — Share (only if asked)

`content_share` / `POST /api/artifacts/{id}/permissions`. Defaults matter:
omitting `permission` grants **VIEWER**, omitting `days` grants **365 days**.
Never grant ADMIN unless explicitly asked, and never treat this as a way to make
something public (there is no public/anonymous level).

## Delivering a large image set — the images live in the site, never in Drive

When the site is a comparator over 25–50 renders, the user will still ask
"give me links to the generated images" after it is live. There is one
surface, not two:

- **The site** = the thing to LOOK at (original held fixed, variation beside
  it, per-variation prompt + QA), and it is also where the images actually
  live now — real files (or sprite sheets, past the 200-file cap above), not
  `data:` URIs, uploaded via `source_path`. One link, and it versions in place.
- **A site's own images never go to Drive. Not by default, not on request,
  not as a one-off.** This is not "prefer the site" — it is the only place
  they go. Drive became a parallel asset host only because the publish tool
  used to be unable to carry binary; that limitation is gone, and so is the
  reason. If someone genuinely needs the raw files later, that is a manual
  export done by hand at that time, not a step in publishing — and note that
  if the images were sprite-packed to fit the 200-file cap, the site itself
  is no longer full-resolution; a real export means going back to the
  original working files, not extracting from the sprite sheet. (Drive still
  gets standalone documents in their own right — a source PDF, the master
  prompt file — per the routing rule at the top of this skill; that is
  unaffected.)

**History.** Until 2026-09-29 this section said to upload the originals to a
Drive TMP folder "if the user explicitly asks," with idempotent-upload
mechanics (`MediaFileUpload(resumable=False)`, list-back-and-compare-size)
included right here. Concrete trigger for removing the exception entirely:
the 2026-09-28 AJ Farmhouse delivery plan still proposed a full 308-image
Drive TMP upload alongside the same images already published as real files
in the site — the "optional" wording left room to read it as sometimes
appropriate, and it was. If a Drive upload is ever genuinely warranted for
something that is NOT a site's own images (e.g. the source corpus, per the
section below), the list-back verification pattern above is still the right
one to reuse — it just no longer belongs to this workflow.

**The user's "V2" is not the system's version number.** NDR said "make it a V2
content" meaning *push the next version of that artifact* — the system counted
**v3** (v1 = first publish, v2 = the self-contained fix, v3 = the Set C
extension). Do not argue the numbering and do not silently adopt theirs: push
the version, then state the real number once and plainly ("same ID, same URL,
now version 3"), naming what each earlier version was, so the history stays
legible and the user calibrates their mental count.

## Building the artifact itself

`templates/single_file_artifact.html` is the old no-JS skeleton. It still
renders, but it is a workaround for a bug that no longer exists. Prefer a normal
multi-file build: `index.html` + `styles.css` + `app.js` + `img/*.webp`.

### Presentations (decks) as artifacts

**Use real Reveal.js.** Copy the three files in this skill's own
`templates/presentation/` directory (`index.html`, `app.js`, `styles.css`). Reveal.js, Chart.js and Mermaid are
vendored at `/lib/` on the render origin and all work - verified live on
2026-09-27: slides navigate, Chart.js paints pixels, Mermaid renders an SVG.

The scroll-page pattern below was the no-JS workaround. It is kept as a
reasonable fallback for a text-only deck. DRA-ART-2026-000025 ("The Age of
Discovery", 17 slides, four inline SVG route maps) is built this way and should
be rebuilt as a real deck:

- **Sticky top bar with anchor-link jump nav** (pure HTML, no JS) — numbers 1..N
  linking to `#s1`..`#sN`. This is the "next slide" interaction on a scroll page.
- **Speaker notes = `<details class="notes">` accordions** under each slide.
- **Maps/charts that can be vector should be inline `<svg>` with a `viewBox`,
  not base64 bitmaps** — crisp at any zoom, no payload bloat, and `img-src` has
  `data:` but inline SVG needs nothing. Raster images only when genuinely
  photographic (downscale to ~880 px WebP q74 first, per above).
- Keep each slide bounded (max-width ~1080px, generous padding) and check for
  text overflow — hidden slides still lay out, so overflow bugs are visible in
  a full-page screenshot even though the user scrolls one slide at a time.
- A copy line ("click a slide number to jump, open + SPEAKER NOTES to read
  notes") keeps the page from reading as broken.

Design rules learned the hard way:
- **A deck/lesson artifact can be a full-screen 16:9 scroll deck: one `index.html`,
  every slide a fixed-width card (e.g. 1280x720), sticky numbered anchor-jump
  bar at top, `<details>` for per-slide speaker notes, print CSS with `@page
  size:1280px 720px; margin:0` so "print to PDF" yields one page per slide. No
  JS wired to keyboard/screen is possible — scroll + anchors are the interaction
  model; say so in the page copy.
- **Inline SVG is fully CSP-safe here and far lighter than base64 PNG.** The
  render origin's CSP has no `img-src` restriction on inline `<svg>`, and
  `viewBox`-scaled SVG scales crisply at any size. For maps/charts/diagrams,
  generate inline `<svg>` (same coordinates as the PNG renderer, but text stays
  selectable and the HTML stays ~140 KB instead of megabytes of base64). Verified
  2026-09-27 with route maps (Natural Earth polygons + plate-carree projection).
  Pitfall while writing the generator: remember to project route points through
  the same transform as the base layers — a raw lon/lat-as-pixel route renders
  invisible on a projected frame (caught by browser_vision on the map slide).
- **A CSS-only carousel** = one hidden `<input type="radio" name="grp">` per
  item, placed as the **first children** of a container, then
  `#grp-ITEM:checked ~ .split .slides .s-ITEM{display:block}`. Everything the
  rules target must be a **sibling after** the radios.
- Hide radios with an off-screen class
  (`position:absolute;width:1px;height:1px;opacity:0;pointer-events:none`), not
  `display:none` — keep them reachable via `<label for=...>`.
- Wrap long blocks (prompts, logs, methodology) in `<details>` to keep the page
  scannable.
- **State the platform-imposed interaction model in the page copy** ("click a
  thumbnail to switch"). If the copy promises prev/next buttons you cannot build,
  the page reads as broken rather than as deliberately different.

## Publishing does NOT license deleting the source assets (learned 2026-09-28)

The publish is often followed by *"and now delete everything from Drive so we don't
have dual copies — we're short of storage."* Do NOT treat the artifact as a
replacement for the Drive set. Three checks BEFORE deleting anything:

1. **The artifact is a VIEWER, not an archive.** Images inside an artifact are
   normally packed as sprite sheets at reduced cell size (see the 200-file cap
   above). Delete the Drive originals and the full-resolution set exists nowhere.
   Check whether the local working copy still exists — it frequently does not
   (`/tmp/<project>` is cleared between sessions). If it is gone, Drive IS the
   only copy.
2. **Enumerate the live shares first.** `content_user_access(email)` and
   `GET /api/artifacts/{id}/permissions` show who holds access to artifacts — but
   the DRIVE folders have their own, independent permission system that DRA
   Content cannot see. Before deleting a Drive folder, list its permissions and
   check whether it was shared with an external reviewer. Those links are
   typically already sitting in SENT email — deleting the folder kills the link
   silently, and the reviewer only finds out when they click it.
3. **Name what breaks, then ask.** Do not execute a broad cleanup on a one-line
   instruction. Report: which folders are the only surviving copy, which are
   shared and with whom, and what the safe-to-delete subset is. Offer the
   container-side cleanup (`/opt/data/<project>` working files) as the
   zero-risk option when the user's actual concern is space.

Deleting a superseded intermediate build is fine. Deleting the SOURCE CORPUS or a
folder already shared with an external party is not — surface it and let the user
decide. Publishing and cleanup are separate decisions.

## A lightbox that opens the WRONG image is a KEY-MISMATCH bug (2026-09-28)

Reported as *"when I click on the image it opens right from G1 again — every panel opens the
same first image."* That symptom has one shape: **the lookup key built at click time never
matches any key in the item list, the index stays at its initial `-1`, and the renderer falls
through to item 0.** In a cumulative study the item 0 is the first frame of the first run, which
is exactly why every panel appeared to open "G1".

Two bugs, and you must fix BOTH — fixing only the first still opens the wrong image:

1. **The clicked element did not carry the identity the list was keyed by.** Tiles were tagged
   `kind:sheet:cell`; the lightbox list was keyed `kind:sheet:cell:runId`. No run tile could ever
   match. Fix: tag the tile with its owning group id at build time (`runId`) and build the lookup
   key from the SAME fields on both sides.
2. **The key was not unique across groups.** 20 of the sheet/cell pairs were reused across
   different runs — every run started at `sheet 0, cell 0`. So even a naive fix keying on
   `sheet:cell` alone silently opens whichever group was pushed first. The group id is not
   decoration; it is load-bearing.

```js
// build: carry the owner id on the element
if (runId) t.dataset.run = runId;
// click: include it
var key = kind + ":" + si + ":" + ci + (tile.dataset.run ? ":" + tile.dataset.run : "");
// and never leave the index unset — fall through is what produces the "always image 1" bug
stackIdx = -1;
stack.forEach(function (it, i) { if (it.key === key) stackIdx = i; });
if (stackIdx < 0) stackIdx = 0;
```

**Prove it with a collision count before you publish.** Do not eyeball this — compute it: for
every group, assert `len({(sheet, cell)})` per group is less than the total across groups, i.e.
count how many `(sheet, cell)` pairs appear in MORE THAN ONE group. On this artifact that number
was **20** — that single figure is the proof the group id is required in the key. Then assert
`tiles_with_no_matching_item == 0` with the fix applied.

**Verify on the LIVE page by clicking the LAST tile of several different groups,** not the first —
the first tile of every group is cell 0, which is precisely the tile a broken fallback would
render correctly by accident and mask the bug. Click-through shape that caught it:

```js
['g3','g5','g10','g12'].forEach(function(id){
  close(); openPanel(id);
  var tiles = document.querySelectorAll('#panel-'+id+' .tile');
  tiles[tiles.length-1].click();                       // last, not first
  results.push({run:id, clicked: label, opened: lbLabel.textContent,
                promptHead: promptHead.textContent});
});
```

Each group must open its OWN label and its OWN prompt heading. On the fixed v2 build the four
checks returned the cladding prompt, the night-garden prompt, the bottle-window prompt and the
laterite-portal prompt respectively — four different answers where the broken build gave one.

**Rename/restructure bugs ride shotgun with this one.** The same session found duplicate
reference labels (`"REF · 1"` vs `"REF1"` vs `"REF · 1 lobby jaali"` — one file, three labels)
and a dedupe helper that collapsed them by a key computed inconsistently. If the artifact has a
labelling step, assert unique labels in the payload before publishing, not after a user reports
"the same thing twice".

## Pitfalls

- **Probe that you can actually publish BEFORE you build the payload.** On 2026-09-28 a
  12.1 MB / 311-file artifact (28 view chips × 10 variations, images as `img/*.webp`) was
  fully built and browser-verified before anyone checked the route — and every content call
  then answered `DRA_CONTENT_SERVICE_TOKEN is not configured`, so the deliverable could not
  be published or shared at all that session. One cheap authenticated metadata call at the
  START of the job (`content_get` on any known artifact id) settles it in a second. If it
  comes back unconfigured: **stop building, re-plan around the Drive fallback** (zip of the
  interactive bundle + one labelled contact sheet per view + the master prompt doc, shared
  with the reviewer), and tell the user the publish is pending on config *before* they are
  waiting on a link. When you do report, say plainly that nothing was published — never hand
  over a URL you did not receive from the API.
  **Diagnosing the token absence (2026-09-28) — it is a CONFIG problem, not a service outage.**
  Prove the distinction in four cheap moves before answering the user, because "give me the
  published URL" is a question about system state, not about your memory: (1) any `content_get` /
  `content_find` answers `DRA_CONTENT_SERVICE_TOKEN is not configured`; (2) the variable is absent
  from the process env AND from `/data/hermes/.env` — grep for the NAME only, never print a value;
  (3) `curl -o /dev/null -w '%{http_code}'` the API host — `content-api:8650` answered **302**, so
  the service is UP and only this process's transport credential is missing; (4) `tools/dra_content_client.py`
  shows `_headers()` raises *before* any request when `SERVICE_TOKEN` is empty, which is why every
  call fails with the identical message. Unblock path, cheapest first: the content-api operator mints
  a service token, then `hermes config set DRA_CONTENT_SERVICE_TOKEN <token>` and restart the session
  — a token written only into `.env` is NOT auto-exported into `os.environ` (same trap as any other
  `.env`-only credential). Until then the honest answer is **no URL exists yet, for anyone** — the
  SSO shell page included, since nothing was created to authenticate to. Say that, offer the Drive
  fallback in the same reply, and do not phrase it as a pending publish the user should wait on.
- **`scripts/publish_artifact.py` in this skill is top-level-only and text-only.** It walks
  `os.listdir` (no recursion) and skips anything outside `TEXT_EXT`, so an artifact whose
  images live in `img/` publishes with **zero images and no error**. Two routes for an
  image-bearing multi-file artifact: the `content_publish` tool's `source_path` (one entry
  per image, bytes read from disk so nothing large passes through context), or a
  recursive, binary-aware publisher of your own. For the tool route, stage the build at a
  SHORT path (`/tmp/<slug>/`) — 311 `{"path":…,"source_path":"…"}` entries at full
  `/opt/data/<project>/pub/img/...` length is a needlessly large single call. Watch the
  body cap: 12.1 MB of images ≈ 16 MB base64, comfortably inside the limit; the same set at
  900 px/q76 was 17.4 MB ≈ 23 MB base64 and too close to it. Size the WebP set (e.g.
  640 px q68 for variation grids, 900 px q76 for the hero original) to land the binary
  total near 12 MB.
- **Do not trust the `content_publish` tool description on file layout.** It
  tells you to split CSS/JS into separate files; on this render origin that is
  precisely what breaks. Verify with `scripts/csp_probe.py`.
- **Check `content_find` BEFORE telling the user something is not published.**
  "Where is the presentation / has it been published?" must be answered from
  the system, not from memory of the session. A publish may have happened in an
  earlier turn (or by another session) and the answer is `content_find` + the
  `status:"published"` field — not an assertion that nothing exists. Observed
  wrong: replying "not published yet" when the artifact was already live and
  shared. When status is `published`, also confirm the served bytes match the
  build and the page actually renders (Step 2) before reporting "live".
- **A 200 response is not a rendering pass.** Always pull the iframe URL and look
  at the page. This is the single highest-value check in this skill.
- **Do not build a JS carousel.** There is no JS. Radios + `:checked`, or nothing.
- **Locally verified ≠ live-verified when a stale server holds the port.** When
  serving a build locally to test (`python3 -m http.server`), an OLD server from
  an earlier turn can still own the port — the new one fails to bind and exits
  SILENTLY, and the browser test then exercises the OLD directory (which may be
  the multi-file broken version). The first tell is `curl` BYTE SIZE: if it does
  not match your build's size, you are not looking at your build — do not trust
  the snapshot, because old and new pages share the same headings/title and a
  plausible snapshot proves nothing. Confirm with `ps aux | grep http.server`
  (the `cd` before the process shows which directory it serves) and
  `ss -ltnp | grep <port>`; kill every stale server on that port, start on a
  FRESH port, and re-check byte size + sha256 BEFORE opening the browser.
  Proven 2026-09-27: port 8899 was still held by a 05:02 server serving `pub/`
  (multi-file); the fresh server for `pub2/` (single-file, 3,040,096 B) never
  bound, curl reported the old 10,111 B page, and the browser "passed" against
  the wrong build until the byte check caught it.
- **`getComputedStyle(...).display` lies about CSS-carousel visibility.** A
  pure-CSS carousel's `:checked ~ ...` rule can set `display:block` on TWO
  slides at once — the selected one and one whose selector matches through a
  hidden parent group (observed: `s-V01` and `s-W01` BOTH reported
  `display:block` while only one actually rendered). Check real rendering with
  `getBoundingClientRect().width > 0` (returns 0 for a slide inside a hidden
  container), drive the radio via `document.querySelector('label[for="<id>"]')
  .click()`, then re-read the visible slide AND the `input:checked` id list —
  confirm exactly ONE slide is visibly rendered per group and that switching a
  group radio swaps to the other group's slide.
  **Corollary — check the ANCESTOR panel, not just the slide.** A slide's own
  `display` still reports `block` while its whole `<section class="panel">` is
  `display:none`, so a slide-level check passes on a panel the user cannot see.
  A faithful multi-set check reads THREE things after each click: the group radio
  (`input:checked`), the panel (`#panelC` display), and the slide. Also click the
  **visible `<label for=...>`**, not the hidden radio — a snapshot ref pointing at
  the radio silently no-ops, and refs go stale after the first DOM change, so
  re-snapshot or drive it programmatically.
- **The live render check that actually settles it (pyre-free recipe, 2026-09-27):**
  navigate the browser to the signed `/a/{id}/v/{n}` URL (it lands on
  `view.content.ahfl.in/d/<slug>/v/<n>/index.html` with no SSO), then in one console
  call assert: `brokenImgs = [...document.querySelectorAll('img')]
  .filter(i=>!i.complete||i.naturalWidth===0).length` — **must be 0** — plus the
  panel/tab switching above and that a row from the NEW set exists in the index
  table (`[...document.querySelectorAll('table tbody tr')].some(r=>
  r.textContent.includes('W15'))`). Zero broken images across the full page is the
 single strongest signal that the artifact's own subresources all resolved.
 **Exclude the empty-src placeholder from that count.** A lightbox `<img>` that
 is populated on click ships with `src=""`, and the browser reports it
 `naturalWidth === 0` — a guaranteed false positive that makes a clean page look
 broken. Filter it: `imgs.filter(i => i.src && (!i.complete ||
 i.naturalWidth === 0))`. When a variation is rendered as a sprite cell rather
 than an `<img>`, assert the cells instead: count `.sp`-style elements, require
 `new Set(cells.map(c => getComputedStyle(c).backgroundPosition)).size` to equal
 the number of cells (each cell a distinct `background-position`), and require
 every cell to have `getBoundingClientRect().width > 0` so a cell inside a
 hidden panel cannot pass.
- **Converting a fixed 1280x720 scroll deck into Reveal.js: audit EVERY slide's
  overflow, not just the ones you touched.** The usable Reveal stage is shorter
  than 720px (with `margin:0.04` about 662px) and `overflow:hidden` clips what
  sticks out — a scroll page could simply grow taller, a fixed slide cannot.
  Proven 2026-09-27 on DRA-ART-2026-000025: slide 3's mini-map (`height:300px`
  SVG) pushed the legend 36px past the bottom; the legend's
  `getBoundingClientRect().bottom` (742) vs the section's (706) proved the clip.
  Fix by shrinking the fixed-height child and tightening that slide's table
  padding, then re-audit `scrollHeight - clientHeight` on every slide.
- **The browser screenshot tool re-loads the URL before capturing**, so it
  always captures slide 1 (Reveal with `hash:false` restarts there). That is a
  harness quirk, not a deck bug — do not chase it. Navigation and per-slide
  layout must be verified in the console, where DOM state persists across
  `browser_console` calls; use the screenshot only as a styling sanity check.
- **Baseline the whole page before you attach it**, because `'self'` matches
  nothing: if a design needs a subresource, it needs a `data:` URI or an inline
  block, with no third option.
- **Research the artifact's own project/entity naming from existing artifacts
  before inventing one.** Existing artifacts use `project: "Ranka Amber"` style
  values; match the convention (`content_find` will show you). Note
  `entity_resolver` has been observed to fail with
  `_handle() got an unexpected keyword argument 'task_id'` — fall back to
  `content_find` to learn the naming rather than guessing.
- **Push a fix as a new VERSION, not a new artifact.** If you published something
  that renders badly, the user already has the URL; a second artifact splits the
  history and confuses the share.

## Classification: never invent a project or entity name

Resolve `project` and `entity` with the `entity_resolver` tool against the
existing registry before publishing. If nothing resolves with confidence, omit
the field rather than guessing - an artifact with `project: null` can be
reclassified later without moving a single file, because classification is
metadata and storage never depends on it. Inventing a project name that does
not match the registry fragments search and breaks the Drive folder lookup.

## New artifact vs. update: search first

Before publishing, consider whether this is really a **revision** of something
that already exists. Call `content_find` with a natural description ("the Amber
contractor comparison", not an exact title).

- `confident: true` and the single result is clearly the document meant ->
  `content_update`, not `content_publish`. The artifact ID and canonical URL
  never change; a new version is created and every old one stays retrievable.
- `confident: false`, or several plausible results -> present the candidates and
  ask. Never guess and silently update the wrong document.
- Nothing plausible -> `content_publish` a new artifact.

Every `content_update` needs a specific `change_summary` ("Added ABC's revised
quote"), never "Updated document".

**The user's version number is not the system's.** "Make it a V2" usually means
"push the next version". Do not argue and do not silently adopt their count:
push it, then state the real number once, plainly, naming what each earlier
version was, so the history stays legible.

## After publishing or updating: response format

Return the essentials, not filesystem paths or internal metadata:

```
Published: <title>
Site: <artifact_id>
Version: <version>
Access: Administrators only (default)
URL: <canonical url>
```

For an update, the same shape with `Updated:`, `Site: <id> (unchanged)` and
the same canonical URL.

## Export to Drive

`content_export(artifact_id, format)` - `"docx"`, `"pdf"` or `"gdoc"`. This is
how an artifact becomes a document: publish the website here, then export a
flattened copy to Drive if the user asks for one. Only call it when they
explicitly asked for one of those formats or to save to Drive.

Interactive elements - scripts, live charts, diagrams - **do not survive** the
conversion. Only text, headings, tables and images do. If the artifact is
meaningfully interactive, say so before exporting rather than letting the user
discover a flattened copy.

Two failure modes are expected, not bugs:

- **"no Drive folder is mapped"** - the artifact's project/category has no
  registry entry. Tell the user an administrator must add one at
  `/admin/drive-folders`. Do not ask for a raw folder ID and do not invent one.
- **"no Google account is connected for this session"** - the user has not
  authorized Drive access; direct them to connect it.

The export uses the requesting user's **own** Drive via their per-user OAuth
connection, not a service account. Someone with a nearly-full Drive will see
Drive's own quota error surfaced here. That is a real constraint, not something
to retry around.

## Not yet wired

- **Group sharing** ("the Amber team", "everyone in DRA"). Treat "share with the
  X team" as a request to ask which specific people. There is no public or
  anonymous access level in this system and no argument that creates one; if a
  named group cannot be resolved, ask rather than invent a link.
- **Reading an artifact's files back.** `content_get` returns metadata only, and
  the artifact tree is not mounted into this container, so you cannot read what
  a previous version contained. If you need the old content in order to revise
  it, ask for it to be staged somewhere readable.

## Support files

- `templates/single_file_artifact.html` — minimal known-good single-file
  artifact: inline CSS, no JS, pure-CSS tabs + thumbnail carousel, `data:` URI
  image slots. Copy and extend.
- `scripts/csp_probe.py` — serves a directory under an arbitrary CSP + CORP
  header set so you can determine what a target origin will allow **before**
  publishing megabytes. Stdlib only.
- `scripts/publish_artifact.py` — publish/update an artifact by driving
  content-api directly; handles large and image-bearing payloads the
  `content_publish` tool cannot carry.
- `scripts/verify_artifact_version.py` — one-call version check: reads
  `current_version`, lists every version's `size_bytes` / `file_count` /
  `entry_file`, compares the latest against your local build, then reports which
  SHAPE the `/a/{id}` shell route is answering in (200 + inline iframe, or 302 →
  signed capability URL) and whether that capability URL is fetchable
  server-side. Use it instead of hand-rolling the probe: passing the local
  build path gives you the size-identity verdict in the same output. It does
  NOT replace the browser render check — it tells you the right bytes are
  stored, not that the page draws.
- `references/render-origin-constraints.md` — the full measured analysis: exact
  headers, the sandbox/opaque-origin/CORP interaction, the reproduced failure
  transcript, and the single-file workaround for each blocked mechanism.
- `references/file-count-limit-and-sprites.md` — the 200-file-per-version cap
  (how to detect it, what it rejects) and the sprite-sheet pack that fits an
  N-image comparator under it: cell geometry, the CSS `background-size` /
  `background-position` math, the lightbox sprite layer, and the empty-src
  verification gotcha.
- `scripts/pack_sprite_sheets.py` — generic sprite packer: groups images into
  one sheet per group (`--in-template` / `--out-template` / `--views` / `--vars`
  / `--cols` / `--cell`) and reports the resulting file count and b64 size, so
  you can check the 200-file and 20 MB caps before publishing.
