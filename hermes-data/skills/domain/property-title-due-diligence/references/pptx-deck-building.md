# PPTX Deck Building (general, non-real-estate decks)

Recurring class of work: building PowerPoint decks with python-pptx. Same machinery as the market-research deck, but for any topic (e.g. Aug 2026 Phishing/Pharming/Social Engineering deck — 21 slides, 14 Grok images).

## Environment
- python-pptx 1.0.2 lives in `/opt/data/deck-venv/bin/python`. NOT in /opt/hermes/.venv or system python3 — wrong interpreter throws ModuleNotFoundError.
- No LibreOffice on the VPS: cannot `--convert-to pdf` for visual verification. Verify via zipfile inspection + vision_analyze instead.
- Known-good builder to copy: `/opt/data/build_deck.py` (21-slide deck, dark navy theme, helper functions: new_slide, tb, para, bullets, title_bar, footer, pic, fit_pic, panel).

## Workflow
1. Plan slides first: title, agenda, one slide per required section. Educational/security decks: definition, process, aim, effects, real case, prevention, comparison, takeaways, thank-you.
2. Generate images BEFORE writing the build script using `image_generate`. User prefers Grok (grok-imagine-image) artwork, not locally-drawn PIL diagrams. Batch 4 image_generate calls per message; 10+ images for a full deck.
3. Download returned URLs (imgen.x.ai for Grok) with urllib + User-Agent "Mozilla/5.0". Verify dimensions (1280x720 ideal for 16:9).
4. Build: 16:9 = Inches(13.333) x Inches(7.5), dark navy palette, `fit_pic` for aspect-safe placement.
5. Verify WITHOUT rendering:
   - zipfile.ZipFile(pptx) → confirm ppt/media/ count+sizes, ppt/slides/ count.
   - Extract 1-2 images, vision_analyze for garbled text / broken art.
6. Zip standalone images (deck_images_grok.zip) for the user.
7. Offer to push to Telegram — /mnt uploads folder is not writable on this box.

## Pitfalls
- Do NOT conclude "Grok unavailable" from missing XAI_API_KEY env var. Credentials may be xAI OAuth in auth.json (/data/hermes/auth.json → providers.xai-oauth.tokens.access_token). Definitive probe: call image_generate; cached outputs land in /data/hermes/cache/images/xai_*.jpg.
- Re-check config when user says "try now" after a failed attempt — image_gen config can change mid-session (provider: xai appeared in config.yaml between attempts).
- AI images often contain decorative binary/glyph text OCR reads as gibberish — normal texture, not a defect; confirm visually before regenerating.
- Keep a "Your Pictures Go Here" placeholder slide when user says they'll supply photos.
- Keep assets in /opt/data/deck_assets/, reference with {A} variable in build script.
