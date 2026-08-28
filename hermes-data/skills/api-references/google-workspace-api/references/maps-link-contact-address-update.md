# Maps link → address resolution + Contact address update (worked 2026-08-14)

NDR asked to add a Google Maps short link "as part of the address" of two
Google contacts (Nagarajappa JDTP North, Nachiketh Gowda ADTP), resolving the
link into a full address first. Full pattern below — reusable for any
"add this maps link + address to contact X" request.

## 1. Resolve the maps.app.goo.gl short link — no browser needed

The redirect chain lands on a `/maps/place/<Place+Name>,+<Full+Address>`
URL, and **the full resolved address is literally in the URL path**:

```bash
curl -sIL -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" \
  "https://maps.app.goo.gl/fhi3HXTrdbczCyNi7" 2>&1 \
  | grep -iE "^(HTTP|location)"
# → location: https://www.google.com/maps/place/Varsha+Ambulunce+Service,
#   16th+E+Cross+Rd,+CQAL+Layout,+Sahakar+Nagar,+Bengaluru,+Karnataka+560092/...
```

Decode `+` → spaces for the human-readable address. The `data=` payload also
carries the place id (`0x…:0x…`) but do NOT try to decode lat/lon from the
hex feature id — the naive high/low-32-bit split gives garbage
(observed: 100.1265, 50.9001 for a Bengaluru pin). The URL path is the
authoritative address.

**Flag pin-vs-description mismatches.** The pin may resolve to a landmark
near the place the user described, not the place itself (observed: NDR
described the BBMP Bangalore One centre; the pin resolved to "Varsha
Ambulance Service" — same ward, different building). Add the user's exact
link as instructed, but tell them what the pin actually resolves to and
offer to swap if they meant a different pin. Do NOT silently substitute
your own maps link for the one they gave.

## 2. Update the contact — People API across ALL vault accounts

Contacts are not all in google-draas. **Search every account**
(google-draas, google-ahfl, google-gmail). Observed: Nagarajappa JDTP North
exists ONLY in google-ahfl (phone-added government contact); Nachiketh Gowda
in google-draas.

```python
import os, sys, json
os.environ.setdefault('GWS_VAULT_SOCKET', '/run/gws-vault/vault.sock')
os.environ.setdefault('GWS_VAULT_TOKEN_DIR', '/run/gws-vault/tokens')
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service

MAPS_LINK = "https://maps.app.goo.gl/fhi3HXTrdbczCyNi7"
NEW_ADDRESS = {
    "streetAddress": "Varsha Ambulance Service, 16th E Cross Rd, CQAL Layout, Sahakar Nagar",
    "extendedAddress": "Google Maps: " + MAPS_LINK,  # link renders INSIDE the address block
    "city": "Bengaluru", "region": "Karnataka",
    "postalCode": "560092", "country": "India", "countryCode": "IN",
    "type": "work",
}

def find(svc, q):
    return svc.people().searchContacts(query=q, readMask='names,addresses').execute().get('results', [])

def update_address(svc, resource_name, new_addr):
    cur = svc.people().get(resourceName=resource_name, personFields='names,addresses').execute()
    existing = cur.get('addresses', [])
    if any('maps.app.goo.gl/fhi3HXTrdbczCyNi7' in json.dumps(a) for a in existing):
        return {'status': 'already-present'}          # idempotent
    body = {'etag': cur.get('etag'), 'addresses': existing + [new_addr]}  # PRESERVE existing
    return svc.people().updateContact(
        resourceName=resource_name,
        updatePersonFields='addresses',               # WRITE mask = query param
        body=body).execute()

# per account:
svc = build_service('people', 'v1', service_name='google-ahfl')   # try each account
# → people/c9172357950956921719  (Nagarajappa Jdtp North)
# → people/c797745761185814004   (Nachiketh Gowda, google-draas)
```

Key points (all verified live):
- `updateContact` with `updatePersonFields='addresses'` **replaces the whole
  addresses array** — re-send existing addresses or you drop them (see
  SKILL.md pitfall #3).
- `etag` is required; fetch it in the same `get` you use to read existing
  addresses.
- **Put the maps link in `extendedAddress`** — Google renders the
  formattedValue as streetAddress → extendedAddress → city/region/postal →
  country, so the link shows up inside the address block.
- Idempotency: skip the write if the link is already in any address.
- Verify by read-back `get` and show the returned `formattedValue` to the
  user; it should contain the link line.
