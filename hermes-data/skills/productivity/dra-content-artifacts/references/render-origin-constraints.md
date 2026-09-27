# DRA Content render-origin constraints — measured analysis

Session: 2026-09-27. The Ranka Oasis × Godrej Florenne façade re-skin comparator
(DRA-ART-2026-000024). Recorded because the failure is silent and expensive: a
published artifact passed every HTTP-level check and rendered as **unstyled HTML
with broken images**.

## The exact headers the render origin sends

Shell page (`https://content.ahfl.in/a/<id>`):

```
content-security-policy: default-src 'self'; script-src 'none'; style-src 'self';
  frame-src https://view.content.ahfl.in; img-src 'self' data:; form-action 'self';
  object-src 'none'; base-uri 'none'; frame-ancestors 'none'
x-frame-options: DENY
```

Artifact document (`https://view.content.ahfl.in/r/<signed-token>/index.html`) —
**this is the one that governs the artifact**:

```
content-security-policy: default-src 'none'; script-src 'self';
  style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self';
  media-src 'self'; connect-src 'self' https://content.ahfl.in;
  form-action 'none'; base-uri 'none'; object-src 'none';
  frame-ancestors https://content.ahfl.in;
  sandbox allow-scripts allow-popups allow-downloads allow-modals
cross-origin-resource-policy: same-site
x-content-type-options: nosniff
cache-control: private, max-age=600
```

The shell embeds the artifact as:

```html
<iframe src="https://view.content.ahfl.in/r/<token>/index.html"
        sandbox="allow-scripts allow-popups allow-downloads allow-modals"
        referrerpolicy="no-referrer"></iframe>
```

Note both the CSP `sandbox` **directive** and the iframe `sandbox` **attribute**
form the same set. Both omit `allow-same-origin`.

## Why everything external is blocked

`sandbox` without `allow-same-origin` puts the document in an **opaque origin**.
Subresource requests originating from an opaque-origin document cannot be
same-site with anything, so `Cross-Origin-Resource-Policy: same-site` rejects
them. `img-src 'self'` / `style-src 'self'` / `script-src 'self'` then cannot
match either, because `'self'` resolves to nothing for an opaque origin.

The trap: **the CSP alone is not fatal.** Reproducing only the CSP locally
(inline `<style>` green, external `ext.css` background applied, external
`ext.js` set `JS_RAN`, `data:` image decoded 2×2) showed external CSS, external
JS and data URIs ALL working. Adding just `Cross-Origin-Resource-Policy: same-site`
flipped external CSS and external JS to blocked in the same harness. So the header
to test for is CORP, and a CSP-only probe gives a dangerously optimistic answer.

## Reproduced failure transcript

Harness serving the real build under CSP + `CORP: same-site`:

```
externalCSS_bg:          rgba(0, 0, 0, 0)   <- ext.css NOT applied (blocked)
inlineCSS_fontFamily:    monospace          <- inline <style> works
js_ran:                  JS_DID_NOT_RUN     <- external JS blocked
img_data_naturalWidth:   2                  <- data: URI works
img_self_naturalWidth:   0                  <- self-hosted image blocked
```

Live artifact, same signature: white background, default serif text, broken-image
icons with alt text showing, table rendered with headers and **no rows**,
thumbnail strip, headings and images all missing — every element that depended on
the external `app.js` or `styles.css` was absent while the static HTML survived.

## Per-mechanism workaround

| Blocked | Use instead |
|---|---|
| external stylesheet | one inline `<style>` block in `index.html` |
| external script | **nothing** — JS is impossible; redesign as CSS-only |
| self-hosted image | inline `data:image/webp;base64,…` |
| external font | system font stack (`-apple-system, "Segoe UI", Inter, Roboto, …`) |
| JS-driven tabs/carousel | hidden `input[type=radio]` + `:checked ~` sibling rules |
| JS-driven filtering | CSS `:checked` hiding, or repeated static sections |
| `fetch` / `localStorage` | not available; precompute and inline |

## Size math that keeps the file manageable

A 30-item comparator with full images and thumbnails:

- full-size view: 880 px wide WebP q74 → ~60 KB each → ×30 ≈ 1.8 MB
- thumbnails: **190 px q58 generated separately** → ~4 KB each → ×30 ≈ 130 KB
- 2 base images: 1200 px q82 → ~225 KB
- 2 contact sheets: 1150 px q72 → ~220 KB
- **single `index.html` total ≈ 2.9 MB** (base64 inflates ~33 % over raw bytes)

Reusing the full-size data URI for the thumbnail strip doubled the file to
4.86 MB for no benefit — the single biggest avoidable cost. Generate real thumbs.

Payload to content-api was 3.64 MB and POSTed fine; keep the client timeout
generous.

## Verification recipe

```bash
# 1. shell -> iframe capability URL (no login needed for the iframe itself)
IFRAME=$(curl -s "$DRA_CONTENT_API_URL/a/$ART" \
  -H "Authorization: Bearer $TOKEN" -H "X-DRA-On-Behalf-Of: ndr@draas.com" \
  | grep -oE 'src="https://view\.content\.ahfl\.in/r/[^"]+"' | sed 's/^src="//;s/"$//')

# 2. served bytes must equal the local build
curl -s "$IFRAME" -o served.html && md5sum served.html local/index.html

# 3. confirm the headers your design depends on
curl -s -i "$IFRAME" | grep -iE 'content-security-policy|cross-origin-resource-policy'
```

Then load `$IFRAME` in a browser and actually look at it. `browser_console`
reported **zero** JS errors and **zero** console messages on the broken page —
CSP/CORP blocks are not surfaced there, so a clean console is not evidence of a
working page. A screenshot (or `browser_vision`) is.

## Access model observed

Default ACL on a newly published artifact granted **ADMIN** to both the creating
actor (`ndr@draas.com`) and `rnr@draas.com`, with `expires_at: null`. So the
owner can open the artifact without any extra `content_share` call — do not
claim you need to share with the requester before they can see their own
artifact.
