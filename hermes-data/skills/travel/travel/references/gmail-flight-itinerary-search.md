# Gmail-Based Flight Itinerary Search

Alternative to Drive-based travel document retrieval. Use when the user asks "check my email for my flight" — the itinerary email may be in Gmail rather than a Drive folder.

## When to use
- User says "check my email for my flight", "what time is my flight", "find my flight booking"
- User asks about a flight without specifying a Drive folder — the itinerary email is the first place to look
- Domestic Indian flights (IndiGo, Air India, SpiceJet) often only send email itineraries — no Drive PDF

## Search strategy

### 1. Search Gmail with airline-specific queries

```python
from tools.gws_auth import build_service

svc = build_service('gmail', 'v1')

# Search by airline name + recent date range
query = '(subject:IndiGo OR subject:"6E" OR subject:e-ticket OR subject:flight OR subject:booking) after:YYYY/MM/DD'
results = svc.users().messages().list(
    userId='me',
    q=query,
    maxResults=10
).execute()
```

### 2. Fetch full email body to extract flight details

```python
for msg in results.get('messages', []):
    m = svc.users().messages().get(
        userId='me', id=msg['id'],
        format='full'
    ).execute()
    
    headers = {h['name']: h['value'] for h in m['payload']['headers']}
    print(f"Subject: {headers.get('Subject', 'N/A')}")
    print(f"From: {headers.get('From', 'N/A')}")
    print(f"Date: {headers.get('Date', 'N/A')}")
    
    # Extract plain text body
    import base64
    parts = [m['payload']]
    while parts:
        part = parts.pop(0)
        if 'parts' in part:
            parts.extend(part['parts'])
        if part.get('mimeType') == 'text/plain' and 'data' in part.get('body', {}):
            text = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
            print(text[:2000])  # First 2K chars
```

### 3. Common search queries per airline

| Airline | Search Query |
|---------|-------------|
| IndiGo | `subject:"Your IndiGo Itinerary" OR subject:"IndiGo" OR subject:"6E"` |
| Air India | `subject:"Air India" OR subject:"AI" OR subject:e-ticket` |
| SpiceJet | `subject:"SpiceJet" OR subject:"SG"` |
| Vistara | `subject:"Vistara" OR subject:"UK"` |
| Akasa Air | `subject:"Akasa" OR subject:"QP"` |
| Malaysia Airlines | `subject:"Malaysia Airlines" OR subject:"MH"` |
| Singapore Airlines | `subject:"Singapore Airlines" OR subject:"SQ"` |
| Any booking | `subject:"booking" OR subject:"confirmation" OR subject:"itinerary" OR subject:"e-ticket"` |

### 4. Key fields to extract from email body

- **PNR / Booking Reference** — alphanumeric code (e.g. ZCJD2D for IndiGo)
- **Flight number** — e.g. 6E 830
- **Date and time** — departure, arrival
- **From/To terminals** — e.g. Bengaluru T1 → Delhi T1
- **Aircraft type** — e.g. A321
- **Check-in/bag drop deadline** — usually 60 min before departure
- **Passenger name**
- **Payment/status** — CONFIRMED vs PAYMENT PENDING

### 5. Presenting the result to the user

Present a clean summary table:

```
Flight: 6E 830 (Airbus A321)
Route:  Bengaluru (T1) → Delhi (T1)
Date:   02 Jul 2026
Departs: 09:30 | Arrives: 12:30
Bag drop closes: 08:30
PNR:    ZCJD2D
Status: CONFIRMED
```

## Pitfalls

- **Duplicate emails:** Airlines often send two emails — one "payment pending" and one "confirmed." The confirmed one has the latest details. Pick the one with latest timestamp and CONFIRMED status.
- **IndiGo subject formats:** IndiGo sends under various subjects: "Your IndiGo Itinerary - XXXXXX", "Important Travel Information for Your Upcoming Flight", "Got a flight to catch?" — search broadly then filter.
- **Session user mismatch:** Terminal subprocesses may have stale `HERMES_SESSION_USER_ID`. Pass `telegram_id` explicitly: `build_service('gmail', 'v1', telegram_id='ndr')`.
- **Date search syntax:** Use `after:YYYY/MM/DD` format, NOT `after:Nd ago` (silently returns nothing).
