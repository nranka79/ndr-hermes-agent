# KML "could not fetch image" — diagnostic recipe (Aug 2026)

## Symptom

Google My Maps / Google Earth / Google Earth Pro opens a generated KML and
errors per style:

> Error in the document. The element references an image
> 'https://transcribe.ahfl.in/kml-icons/shapes/star.png' that could not be
> fetched. This could be due to a temporary network issue, or the image may
> no longer be available or accessible.

The errors list the icons actually USED by placemarks in that KML — a
sub-per-style failure (usually 12 of 18, one per used icon category), NOT a
"one broken file" situation.

## Critical diagnosis step: the icons being listed ≠ the icons being down

The KML generator self-hosts icons at `https://transcribe.ahfl.in/kml-icons/`
(nginx on the VPS host, `/opt/hermes/kml-icons/` — NOTE: files live on the
HOST, not inside the Hermes container; `find / -name kml-icons` in the
container returns nothing, and there's no nginx config in the container —
curl still gets 200 because the host serves them). Before touching anything:

1. **Direct fetch from the VPS**: `curl -s -o /dev/null -w "%{http_code}" -m 15 <icon-url>` — expect 200.
2. **External vantage point** (proves public reachability, not just local):
   `curl -s -o /dev/null -w "%{http_code}" -m 20 "https://r.jina.ai/https://transcribe.ahfl.in/kml-icons/shapes/star.png"` — expect 200 (jina renders/reads the image; a 200 with image content proves public fetch works).
   Also try the Google Translate proxy as a second external path:
   `curl -s -o /dev/null -w "%{http_code}" -m 20 "https://transcribe-ahfl-in.translate.goog/kml-icons/shapes/star.png?_x_tr_sl=auto&_x_tr_tl=en"` — expect 200.
3. **DNS from Google/Cloudflare resolvers** (raw UDP query, not the local resolver):
   ```python
   import socket, struct, random
   def dns_query(domain, server='8.8.8.8'):
       tid = random.randint(0, 65535)
       header = struct.pack('>HHHHHH', tid, 0x0100, 1, 0, 0, 0)
       q = b''.join(bytes([len(p)]) + p.encode() for p in domain.split('.')) + b'\x00'
       packet = header + q + struct.pack('>HH', 1, 1)
       s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.settimeout(5)
       s.sendto(packet, (server, 53)); data, _ = s.recvfrom(512)
       ancount = struct.unpack('>H', data[6:8])[0]
       idx = 12
       while data[idx] != 0: idx += data[idx] + 1
       idx += 5; ips = []
       for _ in range(ancount):
           idx += 2; rtype, rclass, ttl, rdlen = struct.unpack('>HHIH', data[idx:idx+10]); idx += 10
           if rtype == 1 and rdlen == 4: ips.append('.'.join(str(b) for b in data[idx:idx+4]))
           idx += rdlen
       return ips
   ```
   Expect `['91.99.219.247']` from both 8.8.8.8 and 1.1.1.1.
4. **TLS sanity**: `echo | timeout 15 openssl s_client -connect transcribe.ahfl.in:443 -servername transcribe.ahfl.in 2>/dev/null | grep -E "s:|i:|verify"` — expect a valid Let's Encrypt chain (CN=transcribe.ahfl.in → YE2 → Root YE → ISRG Root X2). Also test `--tlsv1.2` (old fetchers) and HEAD — both 200.

## If all checks pass → the server is NOT down; the error is on Google's side

The real-world cause (Aug 2026): transient network blip between Google's
fetcher and the host at import time, OR Google My Maps caching a failed
fetch. The fix is **re-import the KML**, not rebuild the icons:

1. Open the map in Google My Maps / Google Earth.
2. Delete the current layer.
3. Re-add the KML from the same Drive link (file id preserved via `files().update()`).
4. Icons render; the KML itself carries the current data.

## If re-import still fails

Move the icons to Google Drive public links (upload the 18 PNGs, make them
"anyone with link" readable, use the `lh3.googleusercontent.com` URLs in
`kml_generator.py`'s ICON_BASE) — that eliminates Google-side fetch issues
entirely. Update the skill's ICON_BASE note if you do this.

## What NOT to do

- Do NOT conclude "icons are broken" from the KML error alone — the error is
  Google's fetcher reporting, not a filesystem check.
- Do NOT regenerate/rewrite the KML to "fix" icons — if the URLs in the KML
  are the same working URLs, a re-import fixes the cache, not the file.
- Do NOT put this under "browser tools don't work" — 99acres/MagicBricks
  captcha/403 the VPS datacenter IP and Tavily "Failed to fetch url"s on
  binary images; that's a fetch-infrastructure quirk, and the r.jina.ai path
  above is the reliable external probe for images.
