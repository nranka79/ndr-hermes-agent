# Capturing a Google Maps Location Snapshot (Headless, No Browser Tool)

Use when the user asks to "add a Google Map view / snapshot of the location to the deck" — a red-pin map image for a location slide. This produces a clean map image without the interactive browser tool, which may be unavailable or misconfigured (e.g. `browser.engine: auto` rejected by agent-browser).

## What you need

- Headless chromium shell installed by Playwright: `/opt/hermes/.playwright/chromium_headless_shell-<ver>/chrome-linux/headless_shell` (check `ls /opt/hermes/.playwright/`)
- Python `playwright` + `pillow` — install into a scratch venv if the main venv lacks them:
  ```bash
  python3 -m venv /tmp/pptxenv
  /tmp/pptxenv/bin/pip install -q playwright pillow
  ```

## Key technique: consent-cookie bypass

Google shows an EU consent wall (often German, "Bevor Sie zu Google weitergehen") for headless/datacenter IPs. Plain `--screenshot` on the headless shell captures the consent page, not the map. Fix: seed the `CONSENT` + `SOCS` cookies **before** navigation and drive with Playwright so the page gets real render time:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(
        executable_path='/opt/hermes/.playwright/chromium_headless_shell-1234/chrome-linux/headless_shell',
        args=['--no-sandbox', '--disable-dev-shm-usage', '--lang=en-US'])
    ctx = b.new_context(viewport={'width': 1600, 'height': 1000}, locale='en-US')
    ctx.add_cookies([
        {'name': 'CONSENT', 'value': 'YES+cb.20240101-01-p0.en+FX+100', 'domain': '.google.com', 'path': '/'},
        {'name': 'SOCS', 'value': 'CAISHAgBEhJnd3NfMjAyMzAxMDEtMF9HQzIBBGgBEg', 'domain': '.google.com', 'path': '/'},
    ])
    pg = ctx.new_page()
    # q=<lat>,<lng> drops a RED PIN at the parcel; &z=16 is a good parcel zoom; &hl=en for English
    pg.goto('https://www.google.com/maps?q=13.3216384,77.6789048&z=16&hl=en', timeout=45000)
    pg.wait_for_timeout(15000)          # let tiles render
    pg.screenshot(path='/tmp/map_pin.png')
    print("title:", pg.title())          # '13°19'17.9"N ... - Google Maps' ⇒ pin loaded
    b.close()
```

- If the consent page still appears, click through: `pg.locator('button:has-text("Accept all")').first.click(timeout=3000)` then wait ~8s. (SOCS cookie usually prevents this.)
- Verify with `vision_analyze` on the PNG: "Is there a red pin at the center showing coordinates? Is it a clean map view?" — the coordinates string in the page title is a good machine-readable success signal.
- `page.title()` for the `q=` URL returns the coordinate DMS (`13°19'17.9"N 77°40'44.1"E`) — a reliable success check without vision.

## URL formats

| Goal | URL |
|---|---|
| Red pin + info card (plus code) | `https://www.google.com/maps?q=13.3216384,77.6789048&z=16&hl=en` |
| Embed (no consent, but must be in iframe) | `https://maps.google.com/maps?q=<lat>,<lng>&z=16&output=embed` — only works inside an iframe; direct screenshot gives "must be used in an iframe" |
| Raw coordinate view | `https://www.google.com/maps/@13.3216384,77.6789048,16z` — no pin, may hit consent wall |

## Cropping UI chrome for the slide

The raw screenshot has the left info card (place name, plus code, Directions/Save buttons), top search bar, and bottom attribution. Crop to the map area before embedding:

```python
from PIL import Image
img = Image.open('/tmp/map_pin.png')
w, h = img.size
# Drop left panel (~470px), top search (~110px), bottom attribution (~70px) — tune per screenshot
crop = img.crop((470, 110, w, h - 70))
crop.save('/tmp/map_clean.png')
```

Verify the crop with `vision_analyze` — the goal is a clean map with the red pin and roads, no UI panels.

## Embedding in the deck

- Add as a new slide via the PPTX round-trip (see `references/edit-existing-google-slides-pptx.md` → "Adding a New Content Slide"), with title "GOOGLE MAP LOCATION — <Area>", subtitle with coordinates / plus code, the image, and a clickable "Open location: Google Maps" hyperlink (see `references/python-pptx-hyperlinks.md`).
- Plus code from the map info card (e.g. `8MCH+MH2 Thylagere, Karnataka`) is a nice subtitle detail — it confirms the pin landed exactly on the parcel.
- Also add the map link text on the deck's overview slide ("📍 Google Maps Location — View on Google Maps") — the user explicitly wants the clickable link there, not just the image.

## Pitfalls

- **`--screenshot` on the bare headless shell** hits the consent wall or renders a blank beige page — use Playwright + cookies instead.
- **Embed endpoint alone** errors with "The Google Maps Embed API must be used in an iframe" — wrap in an HTML iframe page, but tiles still may not render headless; prefer the `q=` URL with Playwright.
- **Don't ship a consent page.** Always `vision_analyze` the final PNG before embedding; a 100KB-ish screenshot is often the consent page, a 250KB+ one is usually the real map.
- **Browser tool engine errors** (`Unknown engine 'auto'. Supported engines: chrome, lightpanda`) mean the agent-browser config/daemon is misconfigured — the engine is cached at process start, so a config.yaml edit (`hermes config set browser.engine chrome`) won't take effect mid-session. This Playwright-direct path is the reliable fallback; don't burn turns retrying the browser tool.
