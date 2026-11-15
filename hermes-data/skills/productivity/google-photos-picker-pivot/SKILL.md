---
name: google-photos-picker-pivot
description: "Google Photos current capability: uploading files + creating albums works via tools/gws_skill_bridge.py (photos_upload_file, photos_create_album, photos_picker_*, photos_copy_batch) — vault-backed, no raw token ever leaves the bridge. Reading a user's pre-existing library and API share links are the two things genuinely gone. Load when ndr asks about Google Photos — listing, uploading, migrating, syncing, copying between ndr@draas.com and nishantranka@gmail.com, or reading a shared album link — before suggesting any API or writing any new code."
version: 2.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [google, photos, picker, api, migration, ndr]
---

# Google Photos API — current state and what to use instead

## CORRECTION — verified live 2026-11-15 (this supersedes every "no API" claim below)

NDR was right and this skill was wrong. The Library API is **not** shut down. Google's
31-Mar-2025 change removed only three scopes (`photoslibrary`, `photoslibrary.readonly`,
`photoslibrary.sharing`). These REMAIN and work today:

| Capability | Status |
|---|---|
| Upload photo/video bytes → `uploadToken` | **WORKS** (`photoslibrary.appendonly`) |
| `mediaItems.batchCreate` → item in user's library | **WORKS** |
| `albums.create`, `albums.batchAddMediaItems` | **WORKS** (app-created albums only) |
| `albums.patch`, `mediaItems.patch` (title/description) | WORKS (`edit.appcreateddata`) |
| Read/search the user's EXISTING library | **GONE** (that really is a wall) |
| `albums.share` / `sharedAlbums.*` → API share link | **GONE** — share in the app |

Our OAuth client **already carries** `photoslibrary.appendonly`,
`photoslibrary.readonly.appcreateddata` and `photospicker.mediaitems.readonly`, and the API is
enabled in the Cloud project, on both `google-gmail` and `google-draas`. No re-consent needed.

**Use the bridge — not a standalone script.** `tools/gws_skill_bridge.py` already implements
every Photos capability via `_photos_session()` (a vault-backed `AuthorizedSession`): the OAuth
token is loaded once inside the bridge module and never leaves it as a bare string — same
no-token-reaches-the-LLM design as every other `gws_skill_bridge` operation (Gmail, Drive,
Calendar, ...). This is the single, git-tracked source of truth for Photos access; do not
reintroduce raw `.token`/`.refresh_token` extraction anywhere.

```python
from tools import gws_skill_bridge

# Upload local file(s) into an account's own library, into a named album
# (created if it doesn't exist yet). dry_run=True fetches uploadTokens only
# and creates nothing — zero-footprint proof of access.
gws_skill_bridge.call(
    "photos_upload_file",
    service_name="google-gmail",            # resolve via gws_resolve_account first
    paths=["/data/hermes/tmp/photo1.jpg"],
    album="Prestige Hermitage Unit 2201 — Nov 2026",
    description="Optional human-readable caption, not a filename",
)

# Album only, no files yet:
gws_skill_bridge.call("photos_create_album", service_name="google-gmail", title="...")
```

| Need | Bridge operation |
|---|---|
| Push local file(s) → own library (+ optional album) | `photos_upload_file` |
| Create an album | `photos_create_album` |
| Verify an item Hermes created | `photos_get` |
| User picks existing items in the Photos UI (Picker session) | `photos_picker_create` → `photos_picker_status` → `photos_list`/`photos_inventory` |
| Copy items the user picked, from one of ndr's accounts to another | `photos_upload` (one item) / `photos_copy_batch` (many) |
| Delete a photo/album | **impossible** — no API has ever existed; `photos_trash` raises this explanation on purpose |

Full endpoint/scope reference and the no-token-leak design rationale: `skill_view("google-workspace-api")` → "Google Photos — single-account upload".

## HARD RULE — no ad hoc Photos code outside git

Do not write a new standalone script for Photos work (e.g. against `build_service(...)._http.credentials.token`
or any other raw-token pattern), and do not `skill_manage patch` this file or drop scripts into this
skill's `scripts/` folder to add a capability. That already happened once (2026-11-15) — the script
worked but broke the no-token-to-LLM guarantee every other GWS tool keeps, and the fix lived only on
the server, invisible to git. If a Photos capability is missing, it's a `tools/gws_skill_bridge.py`
change made in the `Hermes_Project` repo (via Claude Code) and deployed — not a live patch here.

## What's still genuinely impossible (the real wall)

1. **Reading/searching the user's existing library.** The Library API only sees items *this app*
   uploaded. There is no "list what's already in nishantranka@gmail.com's Photos" call. The only way
   to reach pre-existing items programmatically is a **Picker session the user drives themselves**
   (`photos_picker_create` → they open the link, pick items, hit Done → `photos_picker_status`/`photos_list`).
2. **API share links.** `albums.share` was removed 2025-03-31 and never came back. Album creation +
   populating it is automatic; generating a shareable link is one manual tap: Photos app → album →
   Share → Create link.
3. **Deletion.** Neither Photos API has ever exposed a trash/delete endpoint, before or after 2025.

## When the user asks to migrate photos between accounts (e.g. ndr@draas.com → nishantranka@gmail.com)

He is right that uploads work — Hermes CAN push files into either account (`photos_upload_file`).
What it cannot do is read the EXISTING library of either account, so there is no automatic "list
account A, copy to B" path unless the items are reachable via a Picker session or a shared-album
link. Ask which situation it actually is:

- **He hands over files directly** (attaches them, or points at a Drive folder / WhatsApp media) →
  fully automatable with `photos_upload_file`.
- **He wants existing library photos swept across** → needs a Picker session (`photos_picker_create`,
  he picks the items himself) or a shared-album link (see "Reading a SHARED album link" below) — there
  is no fully hands-off path for photos the Library API never saw.

## "Take these files and push/upload them to my Google Photos"

Works end-to-end via `photos_upload_file` (verified live 2026-11-15: 1 PNG → album → real `productUrl`).
Files land in the named account's library, in an album the bridge finds-or-creates. The only remaining
manual step is the share link.

**First, verify the media is actually what he says it is** — he names files from memory and is
sometimes wrong (2026-11-14: "video of Ruhaan singing" turned out to be 20s of him sitting on a bed in
a mask, no singing). Sample frames with `ffmpeg -ss 00:00:03 -i <file> -frames:v 1 frame.jpg` at
~quarter-intervals and read them with `vision_analyze` before uploading. If it doesn't match his
description, still identify the most likely intended file, say in one line what you actually sampled,
and offer to swap it — never quietly upload the wrong thing, and never refuse on a guess either.

Then, in order:

1. **Pull the source files at full resolution.** WhatsApp media: `wa_list_chats` → `wa_read_messages`
   for the `mediaId=` → `wa_get_media(mediaId=...)` (saves original bytes under
   `/data/hermes/tmp/wa-media/`). Don't screenshot or re-encode.
2. Resolve the vault key with `gws_resolve_account` (nishantranka@gmail.com → `google-gmail`;
   ndr@draas.com → `google-draas`).
3. `gws_skill_bridge.call("photos_upload_file", service_name=..., paths=[...], album="<Project> <Unit> — <Month Year>")`.
4. Report the `productUrl`(s) and remind him the share link is one manual tap:
   Photos app → album → Share → Create link.

Never offer to "log in and upload it for him" via browser automation — driving his authenticated
Photos session means handling his credentials, which is out of bounds, and it's slower than the
bridge call above anyway.

## Reading a SHARED album link the user provides — browser extraction works (verified 2026-09-16)

When NDR has already created a shared album in the Photos app (`Share → Create link`) and pastes
the `photos.app.goo.gl/...` link in chat, the photos ARE readable for analysis — the "no
programmatic access" wall applies to API browsing, NOT to reading a shared-link page. This is the
happy path after the manual album flow above (NDR: "here's the album, examine the pictures"):

1. `browser_navigate` the short link — it 302s to `photos.google.com/share/...`; the page shows
   photo thumbnails as `div` elements with `background-image` URL styles (no `<img>` tags).
2. Extract full-res URLs with `browser_console` JS:
   ```js
   (() => { const els = document.querySelectorAll('div'); const out = [];
     els.forEach(d => { const bg = d.style && d.style.backgroundImage || '';
       const m = bg.match(/https:\/\/lh3\.googleusercontent\.com\/pw\/[^"?]+/); if (m) out.push(m[0].split('=')[0]); });
     return JSON.stringify([...new Set(out)]); })()
   ```
   Note: the earlier `browser_get_images` tool returns 0 images — the URLs live in
   `background-image` styles, not `img[src]`; the `[style*="background-image"]` selector alone
   also misses some (walk ALL divs + read the style). The extracted `lh3.googleusercontent.com`
   URLs are public for shared albums — no auth needed.
3. Append `=w1600` for a workable hi-res size, download with urllib (`User-Agent`
   header), base64-inline, and feed to the vision model (see vision fallback below if
   `vision_analyze` errors).

### 3a. You do NOT need the browser to fetch the bytes (verified 2026-10-04)

The extracted `lh3.googleusercontent.com/pw/...` URLs are **view_media URLs — scoped to
the share link, public, and directly downloadable with plain `curl`**, no cookies, no
auth, no `browser_navigate`. So the browse is only needed to *extract the URLs once*;
the download loop is ordinary `curl`. A 25-image album pulled in seconds with:

```
while read -r u; do curl -s -L -A "Mozilla/5.0" "$u=w1600" -o "img_$(printf %02d $i).jpg"; done < urls.txt
```

(Note: a raw `get_media`-style Drive fetch of the same file id from a shared album is
NOT needed — the URL already carries the access.) The environmental capture date also
comes back on the file via `DRIVE`-style metadata if the album is mirrored; for a pure
shared album use the DOM labels below.

### 3b. BIND THE CAPTURE DATE TO EACH IMAGE — build filename→date, not just URLs

The naive `background-image` walk returns **only the URL list (unordered, no dates)**.
That is useless for any "is it growing / is it changing over time" analysis, which is
the usual reason a clinician-style album gets shared. **The archive also contains a
counting trap: a VIDEO contributes a thumbnail URL and several photos share one URL**
(verified: 25 items, 26 URLs, one image URL reused 3×, one URL left over for the video).
So URL-position ≠ item-position — never zip the URL list against the date list.

Best route: query the **accessible DOM `aria-label`s**, which carry
`"Photo - Portrait - Jan 28, 2025, 9:06:31 PM"` / `"Video - Portrait - ..."`:

```js
(() => { const out=[];
  document.querySelectorAll('[aria-label]').forEach(el=>{
    const a=el.getAttribute('aria-label')||'';
    if(/^(Photo|Video) - /.test(a)) out.push([a, el.querySelector('[style*="background-image"]')?'has-bg':'']);
  });
  return JSON.stringify(out); })()
```

Then reconcile by **unique URL**: mapping every DOM node → its `background-image` URL
and its nearest `aria-label` **misses the first (lazy-loaded) tile, whose label is empty**
— fall back to the page **snapshot list** (the accessibility tree gives items in order
with dates) and assign by order for that first tile only.

Verify before trusting: count items, count unique URLs, and assert the date span matches
the album footer (the header prints e.g. `Jul 29, 2020 – Oct 4, 2026`).

Pitfall: `browser_navigate`'s snapshot list and the `aria-label`s are the reliable date
source; `browser_get_images` still returns 0 (no `<img>` tags).

### 3c. "I just added another photo — can you see it now?" — CHECK PROPAGATION FIRST

Verified 2026-10-04 (NDR added a groin photo mid-session and asked for it analysed; it was
**not** in the link). A photo uploaded to a shared album is often **not yet visible through
the share link** — the page keeps serving the previous set for a while. A share link is not
a live folder. Do NOT analyse a photo you cannot see, and never let a stale fetch pass as
the new one.

Detection recipe (~5 seconds, run BEFORE answering):

1. Re-fetch with a cache-buster: `<link>?x=$(date +%s)` plus `-H 'Cache-Control: no-cache'`,
   re-extract the `pw/` URLs, count unique URLs, download them.
2. `md5sum` the fresh set and `comm -23` it against the previously saved set —
   **zero new hashes = the album has not changed at all**.
3. Cross-check the **album title's date span** — `og:title` carries it, e.g.
   `Ndr Pvt medical · Jul 29, 2020 – Oct 4, 2026`. If the user says "added today" and the
   span still ends before today, propagation has not happened.

### 3c-i. When the user pushes back ("it IS there — check again") — escalate, don't re-curl

Verified 2026-10-04: after a "not yet propagated" reply NDR insisted twice. **A second
identical complaint means the first check was too weak — escalate the verification, never
re-run the same curl and restate.** Five independent methods, and report the count from
all of them:

1. **Server fetch + item-id diff.** The page carries **`AF1Qip...` item IDs** (27 for a
   25-item album — the header/cover IDs are extra). `grep -oE 'AF1Qip[A-Za-z0-9_-]{20,}'`
   on old vs new HTML and `comm` them. **A brand-new upload always brings a new item ID**,
   so this is the sharpest change detector.
2. **Live residential browser fetch** (`browser_navigate` the short link) — independent of
   the datacenter-IP cache, so it rules out "my fetch is stale but the album updated".
   Compare its title span against the curl one; if both agree, the cache is not the cause.
3. **Definitive live DOM count + labels** — the strongest single check:
   ```js
   (() => { const l=[...document.querySelectorAll('a[aria-label]')]
     .map(a=>a.getAttribute('aria-label')).filter(x=>/^(Photo|Video) - /.test(x));
     return {count:l.length, last:l.slice(-3)}; })()
   ```
4. **Scroll loop then re-count** — forces any lazy-loaded tail tiles to materialise before
   you conclude. Re-query after the loop, not before.
5. **Open the newest item directly** — grab its href from a labelled `a[aria-label]`
   (`/photo/AF1Qip...`), navigate to it, and read the full-res `img[src]`. This shows you
   *what the newest photo actually is*, which is how you catch a **mislabelled earlier
   pass** ("my notes called it a face shot — it's the groin photo and I got the region
   wrong") as opposed to a missing upload.

Report the finding as: *"checked five ways — server fetch, live browser, DOM item count,
scroll-for-lazy-load, and the newest item opened directly — all say <N> items, newest
<timestamp>."* Then ask for a re-share or a direct attachment. **Never analyse a photo you
could not fetch, and never infer its contents.**

Also: **"uploaded" ≠ "added to the shared album."** Adding to a personal library, or to a
*different* album, leaves the shared link unchanged. Say this explicitly as one of the
candidate causes, and give the user a self-test — *"open the album; if its header date
range hasn't moved past <time>, the photo isn't in this album."*

Then **say it plainly and ask for a re-share** ("the album still shows 25 items ending
<date>; the new photo hasn't propagated — re-share the link or send the file directly"),
and proceed with everything else you CAN verify. Never infer the contents of an image you
could not download.

### 3c-ii. PROPAGATION DOES HAPPEN — wait, re-check, do not close the file as "missing" (verified 2026-10-04)

The missing-upload case is usually **temporary, not a dead end**. Same session: NDR added
the groin photo and insisted twice; four checks over ~4 minutes still showed 25 items. A
final check after **~5 minutes** showed **26 items, newest `Oct 4, 2026, 1:20:44 PM`** — the
photo had landed, unchanged link, same album ID. So: never tell the user the photo "isn't
in the album" as a conclusion on a single pass — say *"hasn't propagated yet"*, and **keep
re-checking while you answer the rest**. The user is usually right that they uploaded it.

**The server-side technique that actually retrieves it (use this, not the short link).**
Once a new item exists, `curl` on the `photos.app.goo.gl/...` short link returns only a
**~34 KB JavaScript shell with ZERO `AF1Qip` tokens** — Google changed that response, so
"grep the short link" silently yields 0 and looks like an empty album. Fetch the **resolved
share URL** instead:

```
share=$(curl -sIL -A "Mozilla/5.0" "$SHORT" | grep -i '^location' | tail -1 | tr -d '\r' | awk '{print $2}')
curl -sL -A "Mozilla/5.0" -H "Accept-Language: en-US,en;q=0.9" "$share" -o share.html   # ~1.1 MB
```
On `photos.google.com/share/AF1Qip...?key=...` the payload is complete server-side — no
browser needed — and yields **both** the `AF1Qip` item IDs (diff old-vs-new to find the new
one) **and** the `lh3.googleusercontent.com/pw/...` image URLs with real dimensions in one
fetch. Locate the new item's full-res URL by searching for its token and reading the
surrounding ±600/1500 chars for the `pw/` URL; append `=w2400` and `curl` it directly.
The `share/...?key=...` URL is what `browser_navigate` lands on, so it's the address to
reuse; the memory-cached short-link page is what misleads.

### 3d. A photo whose only caption is a post-resize frame-OFFSET, not a coordinate

The file name / DOM label only carries the **resized frame** the browser served, so a
compute-match of `frameOffsets` between two different resizes is meaningless. For "did the
lesion change?" work, prefer two photos from the **same resize level** or, better, measure
against an in-frame anatomical ruler (iris, nail width) as the scale reference — that is
what made the mole measurement in the 2026-10 skin series reproducible across dates.

### Vision-analysis fallback when `vision_analyze` is down ("no LLM keys configured")

`vision_analyze` can 503 with `{'message': 'no LLM keys configured'}` even when the host has
working model keys — the tool's router isn't configured, the pools are. Verified 2026-09-16 on
10 apartment photos. Do NOT give up or improvise a browser-LLM chain; use the pool key directly:

1. Read `LLM_MULTIMODAL_FREE_POOL` from the environment (JSON list, ~3 entries). Pick the
   `provider == 'gemini'` entry — it carries `base` (OpenAI-compatible endpoint, e.g.
   `https://generativelanguage.googleapis.com/v1beta/openai`), `key`, and `model`
   (e.g. `gemini-3.5-flash`).
2. POST to `base + '/chat/completions'` with `Authorization: Bearer <key>` and an OpenAI-style
   messages payload: content = `{'type':'text','text':prompt}` + one
   `{'type':'image_url','image_url':{'url':'data:image/jpeg;base64,<b64>'}}` per image. Send all
   N photos in ONE call and ask for per-photo + global findings in one prompt (10 photos fit fine).
3. If `GOOGLE_AI_STUDIO_API_KEY` is also present, prefer the pool key anyway for vision — AI
   Studio keys in this install 404 on gemini-2.5 models ("no longer available to new users") and
   403 on 3.x models ("project denied"); the pool entry is the reliable path.
4. Base64 the *downloaded* bytes (data URLs), not raw URLs — the Google endpoint accepts
   inline data URLs reliably for public images too, but local bytes never hit auth walls.

**Batch size — do NOT put a whole album in one call (verified 2026-10-04).** 25 images in
a single request exhausted `max_tokens` and the report **cut off mid-album** (analysis
stopped around image 21). Split into ≤8–10 images per call, or run a **second focused
pass** on the subset that actually matters for the question (the recent dates / the
anatomical region asked about) with a tighter prompt. For a "what changed over time"
question the focused pass is the better spend: per-image detail on the recent shots beats
shallow coverage of everything.

**Where to run it.** Write the script to a file (`/tmp/.../analyze.py`) and run it with
`python3 file.py` via `terminal` rather than inlining it in `execute_code` — the
multimodal pool env var (`LLM_MULTIMODAL_FREE_POOL`) is fully populated in the terminal
environment, and long vision calls benefit from a real timeout. Read the pool with a
tolerant loader (try `LLM_MULTIMODAL_FREE_POOL`, then fallbacks) and pick the
`provider == "gemini"` entry; the pool also carries an `nvidia` llama-vision entry as
backup and Gemini occasionally returns `503 UNAVAILABLE` ("high demand") — **retry, or
fall through the pool**. A 503 is transient, not a broken key.

## "Search my Google Photos for a photo of <person>"

Same wall, different ask. There is NO programmatic browse or search over a Google Photos library — you cannot list, query, or find "photos of Manohar" in someone's account, and Picker isn't a workaround (it needs the user live in a browser session selecting items). Do not promise to search Photos; do not imply it's a temporary limitation.

The practical ladder, in order:
1. **Search Drive — this is the step that actually works, and it works on the FIRST try.** Pull it from there instead of asking:
   - `mimeType contains 'image/' and 'me' in owners and trashed=false` (`orderBy="modifiedTime desc"`, `pageSize=200`) — every image the person owns
   - `mimeType contains 'image/' and (name contains '<surname>' or name contains '<keyword>')`
   - **Look inside company folders, not just a photos folder.** Portrait/ID photos of people get filed into registration, KYC and compliance folders. Verified 2026-10-14: NDR's best high-res headshot was `NDR (1) (2).JPG` (3696x2448) inside `Docs of GST registration (Sevaganapalli)` — a folder of partner PAN/Aadhaar/partnership deeds — sitting next to `Kishan photo.jpg`. His own photo was in no "photos" folder at all.
   - Download with `build_service("drive","v3",service_name=...).files().get_media(fileId=...)`; judge each candidate with one `vision_analyze` call, then pick.
   - Full workflow for turning the result into a profile picture: `professional-portrait-headshots`.
   - Only if Drive comes up empty: ask the user to **attach the image directly in chat**.
2. If it's a person's photo for a deck/profile, place a **monogram placeholder** (initials on a brand-colour oval) meanwhile and swap the real file in when it arrives. Never stock-substitute a real person's photo, and never leave the card blank.
3. Say it plainly once: "I can't reach Google Photos programmatically — send the file and I'll drop it in."

Verified 2026-09-14 (NDR: "Manohar and Nishant are on my Google Photos, search and you'll find them" — not searchable; he then sent the files).
