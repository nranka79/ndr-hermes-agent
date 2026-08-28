# Maps Link → Contact Address Update (People API)

Workflow for "add this Google Maps link as part of [person]'s address, and resolve it to a full address" (NDR pattern, Aug 2026 — done for Nagarajappa JDTP North + Nachiketh Gowda ADTP).

## Step 1 — Resolve the maps short link (no API key needed)

```bash
curl -sIL -A "Mozilla/5.0" "https://maps.app.goo.gl/<code>"
```

The final `location:` URL carries the resolved place in its path:
`/maps/place/<Name+Street,+Area,+City,+State+Pin>/data=...`
URL-decode it — that IS the full address (e.g. "Varsha Ambulance Service, 16th E Cross Rd, CQAL Layout, Sahakar Nagar, Bengaluru, Karnataka 560092").

**Do NOT try to derive lat/lon from the `!1s0x...:0x...` place-id hex.** The naive 64-bit split (high 32 = lat ×1e7, low 32 = lon ×1e7) gives wrong coordinates (observed: a Bengaluru pin decoded to 100.12/50.90). The `/place/` path is the reliable address source. Use Nominatim reverse only as a neighbourhood sanity check with a guessed area coord:

```bash
curl -s -A "DRAAS-Hermes/1.0 (ndr@draas.com)" "https://nominatim.openstreetmap.org/reverse?lat=13.0644&lon=77.5812&format=json&zoom=18"
```

## Step 2 — Find the contact (search BOTH accounts)

`searchContacts` is per-account. Some DRA contacts live ONLY in `google-ahfl` (e.g. "Nagarajappa Jdtp North" +91 98449 16825), others only in `google-draas` (e.g. "Nachiketh Gowda" +91 85480 07007). Search both, or use `personal-messaging`'s `find_contact.py` which does.

## Step 3 — Update the address (append, keep etag)

```python
cur = svc.people().get(resourceName=rn, personFields='names,addresses').execute()
etag = cur.get('etag')
existing = cur.get('addresses', [])
# idempotency: skip if any existing address JSON already contains the maps link
new_addr = {
    "streetAddress": "Varsha Ambulance Service, 16th E Cross Rd, CQAL Layout, Sahakar Nagar",
    "extendedAddress": "Google Maps: https://maps.app.goo.gl/<code>",  # link rides here
    "city": "Bengaluru", "region": "Karnataka",
    "postalCode": "560092", "country": "India", "countryCode": "IN",
    "type": "work",
}
res = svc.people().updateContact(resourceName=rn, updatePersonFields='addresses',
        body={'etag': etag, 'addresses': existing + [new_addr]}).execute()
```

- `formattedValue` is auto-derived — don't set it yourself.
- Verify by re-`get()` and print `formattedValue`; Google renders it as streetAddress → extendedAddress (the maps link) → city/region/postalCode → country.
- To change the address later, find the existing address by the maps-link string in its JSON (idempotency check doubles as the finder).
