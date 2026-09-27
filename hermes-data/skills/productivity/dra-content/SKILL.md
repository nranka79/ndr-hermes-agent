---
name: DRA Content publishing
description: Publish, update, share and export browser-renderable documents and presentations through DRA Content — the artifact platform at content.ahfl.in.
---

# DRA Content

DRA Content is an artifact repository and presentation platform, not a
traditional CMS. Its tools (`content_publish`, `content_update`,
`content_find`, `content_get`, `content_list_versions`, `content_share`,
`content_revoke`, `content_access_list`, `content_user_access`,
`content_archive`, `content_export`) are in the `dra_content` toolset.

**This skill's guidance applies whenever the toolset is enabled for a
profile.** Whether DRA Content is the *default* destination for ordinary
document requests is a separate, later decision (tracked as DRA Content
Stage 14) and is not yet in effect — do not assume it unless a system
prompt or profile config explicitly says so.

## When to publish here vs. somewhere else

Publish to DRA Content when the user asks for a document-like deliverable:
a report, analysis, comparison, proposal, brief, memo, specification, or
presentation, and has not named a specific alternative destination.

Use a different workflow instead when the user explicitly says:

| They said | Use instead |
|---|---|
| "Google Doc" / "save to Drive" | The Google Docs/Drive workflow |
| "Word document" / "DOCX" | `content_publish` first, then `content_export` with `format: "docx"` |
| "PDF" | `content_publish` first, then `content_export` with `format: "pdf"` |
| "spreadsheet" / "Excel" / "Google Sheet" | The spreadsheet workflow, not this skill |

Do not publish a plain conversational answer as an artifact. A one-line
answer to a question is not a deliverable.

## Classification: never invent a project or entity name

Before calling `content_publish`, resolve `project` and `entity` with the
`entity_resolver` tool against the existing registry. If nothing resolves
with confidence, omit the field rather than guessing — an artifact with
`project: null` can be reclassified later without moving a single file
(classification is metadata; storage never depends on it). Inventing a
project name that doesn't match the registry fragments search and the
Drive folder registry lookup (`content_export` will then fail loudly with
"no Drive folder is mapped," which is correct behaviour, not a bug to work
around by guessing harder).

## New artifact vs. update: search first

Before publishing, consider whether this is really a **revision** of
something that already exists. Call `content_find` with a natural
description ("the Amber contractor comparison," not an exact title).

- If `confident: true` and the single result is clearly the same document
  the user means → `content_update`, not `content_publish`. The artifact ID
  and canonical URL never change; a new version is created and the old one
  remains permanently retrievable.
- If `confident: false` or multiple plausible results exist → present the
  candidates and ask which one is meant. Never guess and silently update
  the wrong document.
- If nothing plausible exists → `content_publish` a new artifact.

Every `content_update` call requires a `change_summary` — a short, specific
description of what changed ("Added ABC's revised quote"), not "Updated
document."

## Files and the rendering environment

`content_publish`/`content_update` take a `files` array of `{path,
content}` (plain text; the tool base64-encodes it). Must include
`index.html`. Practical constraints from the rendering origin's Content
Security Policy:

- **No inline `<script>`.** It will not execute. Put JavaScript in a
  separate file and load it with `<script src="app.js">`.
- **No remote resources** — no CDN `<script src="https://...">`, no
  `@import url(https://...)` in CSS. Everything must be a file you upload
  or something already served from `/lib/` (see below).
- Inline `<style>` and `style=""` attributes work fine.
- **Never nest an HTML comment.** HTML comments do not nest: the first
  `-->` ends the comment and everything after it becomes live markup. A
  stray `<script>` created that way swallows every tag up to the next
  `</script>`, which is usually a real library include. This silently broke
  every presentation ever produced, while every file still returned 200.
- **Never set `<meta name="referrer">`.** The renderer requires a
  same-artifact `Referer` to stop one artifact reading another, and fails
  closed. Suppressing the referrer costs the artifact its own stylesheet
  and scripts.

Multi-file artifacts are the normal, supported shape. There is no need to
inline everything into one file — an earlier renderer bug made that
necessary, and it is fixed.

### Images and other binary assets

Give the file's path on disk as `source_path` instead of `content`. The
tool reads and encodes the bytes itself:

```json
{"path": "img/villa-v01.webp", "source_path": "/data/hermes/tmp/render01.webp"}
```

**Do not** inline images as `data:` URIs, and **do not** park them in Drive
and link out. Both were workarounds for the tool being text-only; it no
longer is. Inlining produced multi-megabyte pages that no browser can cache
per image and stored every asset twice.

Allowed: `.png .jpg .jpeg .gif .webp .avif .ico .woff .woff2 .ttf .otf
.pdf .xlsx .docx .pptx .zip`. Limit 20 MB per file and 20 MB per version —
the request is JSON and base64 inflates by a third, and nginx caps the body
at 30 MB.

### Shared libraries, no need to re-implement

`/lib/dra-content.js` gives you analytics (opens, scroll depth, clicks,
downloads). Load it yourself, and load `_token.js` immediately before it —
that file is generated per artifact by the renderer and carries the token
the beacon needs:

```html
<script src="_token.js"></script>
<script src="/lib/dra-content.js"></script>
```

For presentations, copy the three files in this skill's own
`templates/presentation/` directory (`index.html`, `app.js`, `styles.css`)
as your starting point rather than writing a deck from scratch. They are
beside this file, so read them with your normal file tools. (They used to
be quoted as `/srv/dra-content/skill-templates/`, which is not mounted
into the agent container and could never be read -- which is part of why
decks were being hand-rolled.) — see `references/presentations.md` for what's available (Reveal.js
navigation, Chart.js, Mermaid diagrams, speaker notes) and the six approved
themes. Do not hand-roll a slide framework; do not reference a Reveal.js
theme or plugin not listed there — anything else 404s, by design (see
`APPROVED_FRONTEND_LIBRARIES.md` in the DRA Content repo for why).

## Sharing: defaults matter, never make anything public

`content_share` defaults to **VIEWER** and **365 days** if you omit those
fields. Only pass `permission: "ADMIN"` if the user explicitly asked to
make someone an administrator of that specific artifact. Only pass `days:
0` (permanent) if the user is a platform administrator asking for a
permanent grant explicitly — Hermes cannot grant permanent access on
behalf of an ordinary user, and the API will refuse it.

There is no public/anonymous access level in this system and no argument
that creates one. "Share this with the whole team" means resolving actual
group membership through a controlled registry, not inventing a public
link — if a named group can't be resolved, ask rather than guess (this
capability is not yet wired as of Stage 10; treat "share with the X team"
as a request to ask which specific people, until group support lands).

Common patterns:

- "Share this with john@x.com" → `content_share(artifact_id, "john@x.com")` — VIEWER, 365 days
- "Share this with john@x.com for 30 days" → add `days: 30`
- "Remove John's access" → `content_revoke(artifact_id, "john@x.com")`
- "Who has access to this?" → `content_access_list(artifact_id)`
- "What can john@x.com see?" → `content_user_access("john@x.com")` — note the API refuses this for a non-administrator asking about anyone but themselves; if it's refused, say so rather than working around it

## After publishing or updating: response format

Return the essentials, not filesystem paths or internal metadata:

```
Published: <title>
Artifact: <artifact_id>
Version: <version>
Access: Administrators only (default)
URL: <canonical url>
```

For an update:

```
Updated: <title>
Artifact: <artifact_id> (unchanged)
Version: <new version>
URL: <same canonical url>
```

## Export to Drive

`content_export(artifact_id, format)` — `format` is `"docx"`, `"pdf"`, or
`"gdoc"`. Only call this when the user explicitly asked for one of these
outputs or to save to Drive. Interactive elements (scripts, live charts,
diagrams) do not survive the conversion to Word/PDF — only text, headings,
tables and images do; if the artifact is meaningfully interactive, say so
before exporting rather than let the user be surprised by a flattened copy.

Two failure modes are expected, not bugs:

- **"no Drive folder is mapped"** — the artifact's project/category has no
  registry entry. Tell the user an administrator needs to add one at
  `/admin/drive-folders`; do not ask them for a raw folder ID and do not
  invent one.
- **"no Google account is connected for this session"** — the user hasn't
  authorized Drive access. Direct them to connect their Google account
  first.

The export uses the *requesting user's own* Google Drive, via their
existing per-user OAuth connection — not a shared service account. A
person with a nearly-full Drive will see Drive's own quota error surfaced
here; that's a real constraint, not something to retry around.

## What this skill does not yet cover (as of Stage 10)

- Group-based sharing ("the Amber team," "everyone in DRA") — not wired yet.
- Uploading binary assets (images) via `content_publish`/`content_update` —
  the tools currently accept text files only.
- Making DRA Content the automatic default for undirected document
  requests — a later, separate decision (Stage 14).
