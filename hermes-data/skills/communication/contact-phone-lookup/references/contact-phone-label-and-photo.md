# Contact Phone Labels & Profile Photos (People API)

Session-validated Aug 2026 (Puneeth Gill contact update). Covers the two
features the standard dual-flow references don't: custom phone labels and
profile photo upload from a screenshot.

## Pitfall — People API phone labels are enum-only (no customType)

`PhoneNumber` in People API has NO `customType` field. Attempting

```python
{'value': '+1 516 288-8100', 'type': 'custom', 'customType': 'USA'}
```

fails with:

```
HttpError 400 ... Invalid JSON payload received. Unknown name "customType"
at 'person.phone_numbers[0]': Cannot find field.
```

**Allowed `type` values for phoneNumbers:** home, work, mobile, homeFax,
workFax, otherFax, pager, workMobile, workPager, main, googleVoice, other.

**Where custom labels CAN live:** the NDR DRAAS contacts sheet (cols 27-38
are free text — "IND", "USA", "Wapp" all work there; the sheet already uses
free-text labels like "Wapp" elsewhere).

**Session example:** user asked to add a US number labeled "USA" and rename
the existing Indian number's label to "IND". Google Contacts got both numbers
as `type=mobile`; the sheet row got `Phone 1 - Label = IND` and
`Phone 2 - Label = USA`. Report the asymmetry to the user when they ask for
custom labels — don't silently downgrade.

## Setting / replacing a profile photo

```python
import base64
with open('/tmp/avatar.png', 'rb') as f:
    photo_b64 = base64.b64encode(f.read()).decode()
people.people().updateContactPhoto(
    resourceName='people/...',
    body={'photoBytes': photo_b64}
).execute()
```

**The response is sparse** — `resourceName` and `photos` often come back
`None`. That is NOT a failure. Verify by re-fetching:

```python
chk = people.people().get(resourceName=..., personFields='photos').execute()
print(chk['photos'][0]['url'])  # compare to the pre-update URL
```

A changed `url` (e.g. `AGPWSu-...` → `AG6tpzE-...`) means the photo was
replaced. The old photo URL remains valid for a while (cache), so always
compare the URL string, not availability.

## Cropping a circular avatar out of a phone screenshot (no vision model)

Phone "Call info" screenshots (575x1280 portrait) have the avatar circle
centered horizontally at top. Detect it with PIL pixel scanning:

```python
from PIL import Image
im = Image.open('screenshot.jpg').convert('RGB')
w, h = im.size
cx = w // 2

def is_avatar_px(px):
    r, g, b = px
    return r < 245 or g < 245 or b < 245   # non-white

# vertical extent at center column = circle top/bottom
ys = [y for y in range(50, 600) if is_avatar_px(im.getpixel((cx, y)))]
top, bot = ys[0], ys[-1]

# horizontal extent per row gives left/right edges; widest row ≈ diameter
for y in range(top, bot, 30):
    xs = [x for x in range(w) if is_avatar_px(im.getpixel((x, y)))]

# center & diameter from the widest row
cy = (top + bot) // 2
diam = xs[-1] - xs[0]  # from the widest scanned row
m = 10  # margin so the circle isn't clipped
crop = im.crop((cx - diam//2 - m, cy - diam//2 - m,
                cx + diam//2 + m, cy + diam//2 + m))
crop.save('/tmp/avatar.png')
```

**Sanity checks before upload:**
- Corners of the crop should be near-white (outside the circle).
- Center pixel should be skin-tone/photo content, not flat UI color.
- A real photo shows varied colors down the center column (hair → skin →
  clothes); an initials avatar is flat color with white text (would also OCR
  as "PG" / "~PG" etc. — in that case there's no photo to extract).

## Reading phone numbers from the same screenshot

`tesseract <img> stdout` on the 575x1280 screenshot read
`+1 (516) 288-8100` cleanly in one pass (tesseract binary at /usr/bin/tesseract).
If digits are garbled, crop to the number row, upscale 2-3x, and re-OCR —
same guidance as the letterhead 300-DPI rule in the main SKILL.md.
