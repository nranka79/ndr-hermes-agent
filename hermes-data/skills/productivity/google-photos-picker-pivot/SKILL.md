---
name: google-photos-picker-pivot
description: "Why we don't propose the Google Photos Library API anymore, and which surfaces (Google Picker, Partner sharing) to use instead. Load when ndr asks about Google Photos — listing, migrating, syncing, copying between ndr@draas.com and nishantranka@gmail.com — before suggesting any API or building any tool."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [google, photos, picker, api, migration, ndr]
---

# Google Photos API — current state and what to use instead

## The headline (nishant, 2026-07-12 voice memo)

The Google Photos **Library API** (`mediaItems.*`, `albums.*`, `sharedAlbums.*`) is effectively shut down for new third-party integrations. Google deprecated and then blocked most public access through 2024–2025. Do **not** propose it for new work. It is also the wrong tool for cross-account workflows even when it did work — it only returns items the *authenticated* user owns, and `mediaItems.id` is per-account (no global asset ID joins two accounts).

## What to use instead

Pick by what the user is actually trying to do:

1. **User-driven one-off selection or export from a single account** → **Google Picker API**. Iframe-based UI that lets the user pick items from their own Photos library, returns selected IDs/tokens to the host page. Good for "download these N photos" UX.
2. **Programmatic migration across many items / years** → **Google Photos Partner sharing API** if the org is enrolled (whitelisted). Not generally available — don't assume we have it.
3. **For ndr specifically (DRAAS / personal Google)** — the only safe cross-account move today is: have the user do it in the Photos UI, or write a script that uses Partner sharing if available. There is no public Library API call that does "list items in account A, copy to account B" reliably.

## What NOT to do in future sessions

- Do not add `https://www.googleapis.com/auth/photoslibrary` to `HERMES_GWS_SCOPES` in `/opt/hermes/tools/gws_auth.py`. The Library API is deprecated and adding the scope won't give working access; it'll just make the OAuth consent screen misleading.
- Do not build a `tools/photos_api.py` that wraps `build_service("photoslibrary", "v1")` — it will mostly return 403/410.
- Do not propose hash-matching or cross-account ID joins. They don't work because the IDs are per-account by design.
- Do not paste URLs to `developers.google.com/photos/library` reference pages — they're outdated.

## When the user revisits this topic

If ndr asks "can you migrate the photos from ndr@draas.com to nishantranka@gmail.com" again, the correct first response is: "Library API is shut down; Picker is the user-driven option, Partner sharing is the only programmatic option and requires Google whitelisting. What's the actual goal — one-time bulk move, ongoing sync, or per-year cleanup?" — and stop there until they answer.
