# DRA Homes — Brand Reference for Teasers / IMs / Pitch Decks

Extracted from `https://drahomes.in` on 2026-07-14. Use when building HTML email
teasers, PPTX decks, or one-pagers branded as **DRA homes / DRA group**. The
Kelsa land-proposal pipeline often surfaces as the source of these teasers
(investor outreach, brother-in-law intros, Lloyd-platform pitches).

## Logo
- Color (on light):  `https://drahomes.in/images/dra-logo.svg`
- White (on dark):   `https://drahomes.in/images/dra-logo-w.svg`
- Both render cleanly inline in HTML email at ~140–180px width.

## Color palette
| Role        | Hex        | Notes |
|-------------|------------|-------|
| Primary     | `#FDB913`  | Main amber/gold — use for headlines, CTAs, dividers |
| Primary alt | `#f9ba2f`  | Slightly more orange variant of the same gold |
| Primary alt | `#f9bb31`  | Hover / darker variant of the primary |
| Dark        | `#1d1f22`  | Body / header backgrounds |
| Dark alt    | `#272727`  | Slightly lighter dark |
| Dark alt    | `#363435`  | Card backgrounds on dark |
| Text body   | `#6b6b6b`  | Paragraph text on light backgrounds |
| Text muted  | `#888`     | Captions, helper text |
| Link        | `#c1880a`  | Inline link color on light bg |
| Light gray  | `#f5f5f5`  | Section dividers, card backgrounds |
| White       | `#ffffff`  | Default content surface |

## Typography
- **Body / paragraphs:** `Roboto, sans-serif` (Google Fonts; import in HTML)
- **Headlines / display:** `Poppins, sans-serif` (Google Fonts; weights 600/700/800)
- **Web font import** (drop into `<style>`):
  ```css
  @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Poppins:wght@500;600;700;800&display=swap');
  ```
- Base body font-size on site: `18px / 25px line-height` — for email, scale down to `15–16px / 22px` to keep the teaser compact.

## Layout conventions
- Container max-width on site: `1350px` (use `600–640px` for email body)
- Top header bar: dark (`#272727`) with gold hover (`#f9bb31`)
- Nav links: uppercase, letter-spacing 7px, Roboto 600
- Buttons / CTAs: solid gold pill with black text

## HTML email teaser recipe (working baseline)

```html
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Poppins:wght@500;600;700;800&display=swap');
    body { margin:0; padding:0; background:#f5f5f5; font-family:Roboto,sans-serif; color:#6b6b6b; }
    .wrap { max-width:640px; margin:0 auto; background:#ffffff; }
    .header { background:#1d1f22; padding:24px 32px; text-align:center; }
    .header img { height:48px; }
    .hero { background:linear-gradient(135deg,#1d1f22 0%, #363435 100%); color:#fff; padding:48px 32px; text-align:center; }
    .hero h1 { font-family:Poppins,sans-serif; font-weight:700; font-size:32px; margin:0 0 12px; color:#FDB913; letter-spacing:1px; }
    .hero p { font-size:15px; color:#d6d2d2; margin:0; line-height:22px; }
    .section { padding:32px; }
    .section h2 { font-family:Poppins,sans-serif; font-weight:600; font-size:18px; color:#1d1f22; margin:0 0 16px; border-bottom:2px solid #FDB913; padding-bottom:8px; }
    .stat-grid { display:table; width:100%; border-collapse:collapse; }
    .stat { display:table-cell; width:33%; text-align:center; padding:16px 8px; background:#f9f9f9; border:1px solid #eee; }
    .stat-num { font-family:Poppins,sans-serif; font-weight:700; font-size:24px; color:#FDB913; }
    .stat-lbl { font-size:11px; color:#888; text-transform:uppercase; letter-spacing:1px; margin-top:4px; }
    .cta { display:inline-block; background:#FDB913; color:#1d1f22; padding:14px 32px; text-decoration:none; font-family:Poppins,sans-serif; font-weight:600; font-size:14px; letter-spacing:1px; text-transform:uppercase; }
    .footer { background:#272727; color:#888; padding:24px 32px; text-align:center; font-size:12px; }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="header"><img src="https://drahomes.in/images/dra-logo-w.svg" alt="DRA Homes"></div>
    <div class="hero">
      <h1>{{PROJECT_NAME}}</h1>
      <p>{{TAGLINE}}</p>
    </div>
    <div class="section">
      <h2>The Opportunity</h2>
      <p>{{BODY}}</p>
    </div>
    <div class="section" style="background:#f5f5f5;">
      <h2>Key Numbers</h2>
      <div class="stat-grid">
        <div class="stat"><div class="stat-num">64K</div><div class="stat-lbl">Sqft across 4 floors</div></div>
        <div class="stat"><div class="stat-num">&infin;</div><div class="stat-lbl">Adequate parking</div></div>
        <div class="stat"><div class="stat-num">&star;</div><div class="stat-lbl">Hot micro-market</div></div>
      </div>
    </div>
    <div class="section" style="text-align:center;">
      <a class="cta" href="mailto:{{SENDER}}?subject={{SUBJECT}}">Let's Discuss</a>
    </div>
    <div class="footer">
      DRA Group &middot; Chennai &middot; Bangalore<br>
      <a href="https://drahomes.in" style="color:#FDB913;">drahomes.in</a>
    </div>
  </div>
</body>
</html>
```

## Send-from account rule (nrd@, 2026-07-13)

DRA-group / DRAAPPL / DRAAS / Truliv director work **always sends from
`ndr@draas.com`**, even when the recipient is at `@drahomes.in` (e.g. brother-in-law
`drr@drahomes.in`). The brand is DRA homes, but the work identity is DRAAS. Do not
file the teaser into the personal `nishantranka@gmail.com` account just because the
recipient's domain is "homes". Ask the user which account to send from only if the
recipient is **not** a DRA-group entity AND the user did not specify.

## Pitfalls

- **DRA has TWO visual brands.** `drahomes.in` (Chennai, residential) is the
  default look above. The investor / DRAAS brand is darker and more corporate.
  When pitching a Lloyd-platform / institutional investor, prefer the
  `drahomes.in` palette as a baseline but lean toward the darker `#1d1f22` /
  `#272727` surfaces with gold accents — closer to a pitch deck than a
  residential brochure.
- **Gmail clips HTML >102KB.** Keep teasers under 100KB. Embed images via
  absolute URL, not base64, to stay under the cap.
- **Outlook ignores `<style>` blocks in `<head>`.** The recipe above uses
  inline styles where it matters. Test by sending to yourself first.
- **Web font `@import` does not work in every email client.** Roboto / Poppins
  fall back to the user's system sans-serif gracefully — design with that
  fallback in mind (slightly tighter line-heights).
