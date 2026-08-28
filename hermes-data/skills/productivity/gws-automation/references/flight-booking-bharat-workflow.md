# Flight Booking — Bharat Hawaldar Workflow

Recurring DRAAS workflow: Nishant requests flight bookings coordinated by Bharat Hawaldar (Pre-Sales) with Roshini cross-checking passenger details.

## Trigger

User asks to find flights and send booking instructions to Bharat via email.

## Workflow Steps

### 1. Decode Route & Dates from Voice

Voice transcriptions often garble names/numbers. Confirm these before searching:
- **Departure city** → "Bangalore" / BLR (always BLR for Nishant)
- **Destination city** → confirm city/airport code
- **Dates** → Departure and return dates
- **Time constraints** → Meeting time at destination, buffer from airport (typically 30 min)

### 2. Source Flight Schedules

Preferred sources (tried in order):
- **Google Flights** via browser (best for live pricing)
- **ixigo.com** — try `curl` to scrape schema.org/JSON-LD data embedded in flight schedule pages (works for static schedules even when JS-rendered pages fail)
- **Skyscanner** / MakeMyTrip for price ranges

**Extracting schedules from ixigo:**
```python
curl -sL "https://www.ixigo.com/flight-schedule/bangalore-new-delhi-blr-del" \
  -H "User-Agent: Mozilla/5.0" | python3 -c "
import sys, re, json
html = sys.stdin.read()
blocks = re.findall(r'<script[^>]*type=\\\"application/ld\+json\\\"[^>]*>(.*?)</script>', html, re.DOTALL)
for block in blocks:
    data = json.loads(block.strip())
    if isinstance(data, dict) and data.get('@type') == 'Flight':
        print(f\"{data.get('flightNumber','')} | Dep: {data.get('departureTime','')} | Arr: {data.get('arrivalTime','')} | Dur: {data.get('estimatedFlightDuration','')}\")
"
```

This gets you actual flight numbers, departure/arrival times, and duration for direct flights. Filter by:
- Direct (non-stop) flights only — single flight number, duration ~2-3h for domestic
- Arrival before meeting time minus airport transit buffer

### 3. Narrow By Constraints

| Constraint | Typical value |
|------------|--------------|
| Airport → venue transit | 30 min |
| Meeting buffer before start | At least arrive 30 min prior |
| Return departure window | User specified (e.g. 6-8 PM, not past 8 PM) |
| Airline preference | IndiGo (cheapest), Air India (full-service) |

### 4. Coordinate Multiple Passengers

For group bookings with split return flights (common pattern):
- All passengers outbound together on same flight
- Return: Nishant on earlier flight, Charitra+Roshni on later flight
- Always verify: Roshni (rnr@draas.com) is also known as Roshni Murjani (maiden name)

### 5. Gather Passenger Details

Source: Google Contacts (People API) + Memory

| Detail | Source |
|--------|--------|
| Name (as on ID) | Google Contacts search |
| Phone | Canonical form from People API |
| Email | Google Contacts |

Search People API:
```python
people = build_service('people', 'v1')
results = people.people().searchContacts(query='Name', readMask='names,phoneNumbers,emailAddresses').execute()
```

### 6. Email Format

**To:** sales1.blr@drahomes.in (Bharat Hawaldar)
**CC:** rnr@draas.com (Roshini for cross-check)
**Subject:** Flight Bookings — [Passenger Names] — [Dates]

**Body structure:**
1. Outbound table (flight, date, time, passengers with phone/email)
2. Return table (split by passenger if different flights)
3. Action items (book immediately vs wait for confirmation)
4. P.S. to Roshini to cross-check

**HTML table template** for tables in email:
```html
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse;">
<tr style="background: #2E86C1; color: white;">
  <th>Passenger</th><th>Phone</th><th>Email</th>
</tr>
<tr>
  <td>Nishant Ranka</td><td>9880055634</td><td>ndr@draas.com</td>
</tr>
</table>
```

### 7. Urgency Rules

| Condition | Action |
|-----------|--------|
| Outbound trip for confirmed meeting | **Book immediately** — mark in bold |
| Return / companion bookings | Wait for Roshini cross-check confirmation |
| Once confirmed by Roshini | Proceed on priority |

### 8. Pitfalls

- **Voice transcription errors for names:** "Roshni Murjani" = Roshini Ranka (rnr@draas.com), maiden name Murjani. Always map to known contacts.
- **Gmail send-from:** `build_service()` uses the token of the session user. Verify `gmail.users().getProfile(userId='me').execute()` to confirm sender address before sending — you may be sending as Prakash instead of Nishant.
- **email.mime attachments:** For HTML emails, use `MIMEText(html_body, 'html')` — proper HTML tables render correctly in Gmail.
- **PDFs for certificate info:** CCD/debenture certificate PDFs may be scanned images. Use `pdftotext -layout` to extract text; if empty, they are scanned and need vision/OCR.
- **Attachments via Gmail API:** attachment data in `body.data` is base64url-encoded. Use `base64.urlsafe_b64decode()`. For inline images (image001.png etc.), these are usually decorative signatures — ignore them.

## Related

- `references/ccd-payment-certificate-reconciliation.md` — For extracting CCD/payment data from email threads and Drive spreadsheets
- `references/people-api-contacts.md` — Google People API search patterns
- `references/email-draft-save-pattern.md` — Sending via Gmail API vs saving as draft
