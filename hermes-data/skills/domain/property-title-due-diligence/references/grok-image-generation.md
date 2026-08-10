# Grok Image Generation (grok-imagine-image) — how to actually run it

For "generate images with Grok / xAI" requests. The key is the OAuth token,
not an API key.

## Token location (learned the hard way Aug 2026)

- The xAI OAuth access token lives in the runtime data home auth.json:
  `/data/hermes/auth.json` on this box (user pointed: "there should be an
  oauth token… in /opt/hermes/hermes-data/auth.json mostly" — on THIS VPS the
  runtime home is /data/hermes, so the file is /data/hermes/auth.json; the
  /opt/hermes tree is the source repo).
- File is mode 0600, owned by hermes. Contains xai-oauth access token.
- shell `env` will NOT show it — it is not exported as XAI_API_KEY.
- It is NOT a provider API key; do not waste time searching .env for it.

## Working invocation

- Image model name: `grok-imagine-image` (1280x720 output, perfect 16:9 for
  deck images).
- Routes that worked:
  - hermes image_gen configured to xai/grok-imagine-image (uses the OAuth
    token from auth.json under the hood), or
  - direct xAI API call using the access token as Bearer.
- Do NOT hand-build a wa.me-style fallback or fake results — if the token is
  missing, tell the user to check console.x.ai.

## Workflow that produced a verified deck

1. Generate per-slide images one batch at a time (13-14 images for a 21-slide
   deck: hero + definition/process/aim/effects/case/prevention per threat +
   comparison).
2. Download all results, verify dimensions (PIL) — 1280x720 expected.
3. Spot-check key images with vision (OCR on hero art is fine — decorative
   binary-code glyphs are OK, garbled TEXT is not).
4. Embed into python-pptx deck (dark navy theme), confirm via unzip of the
   .pptx that media is embedded.
5. Deliver: zip + individual Drive links (with svc.about() identity check
   first — see gws-account-identity-investigation.md).

## Pitfall

If generation "works" but the images look generic (not Grok), verify the model
name actually routed to xai/grok-imagine-image and the token is the live xai
OAuth one — not a different image provider's key that happened to be configured.
