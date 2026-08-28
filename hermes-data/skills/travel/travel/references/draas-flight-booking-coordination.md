# DRAAS Flight Booking Coordination Workflow

Email Bharat Hawaldar (sales1.blr@drahomes.in) with flight booking requests, CC Roshini (rnr@draas.com) for cross-checking.

## When to Use

- User wants flights researched, narrowed down, and booking arranged
- Bharat Hawaldar is the designated booker
- Roshini (Nishant's wife) cross-checks passenger details
- Multiple passengers may travel on different flights/times

## Workflow Steps

### 1. Research Flight Options

Use `references/flight-schedule-via-schema-jsonld.md` for ixigo JSON-LD extraction — works without a browser, returns all direct flights with airline, flight number, departure/arrival times, and duration.

For **outbound (BLR→DEL)**: arrive by user's stated meeting time minus travel-from-airport time
For **return (DEL→BLR)**: depart within user's preferred evening window (6-8 PM typical)

Typical direct BLR↔DEL schedules (from ixigo data):

| Flight | Route | Time | Notes |
|--------|-------|------|-------|
| 6E809 | BLR 12:00 → DEL 14:10 | IndiGo | Good for 4 PM meetings |
| AI2406 | BLR 11:00 → DEL 13:20 | Air India | Early arrival option |
| 6E811 | DEL 18:20 → BLR 20:30 | IndiGo | Early return (~6 PM) |
| 6E861 | DEL 19:30 → BLR 21:45 | IndiGo | Later return (~7:30 PM) |

### 2. Narrow Down with User

Present options filtered by time constraints. User selects specific flights from what you present.

### 3. Compile Passenger Details

Use Google People API to pull contact info:
```python
from tools.gws_auth import build_service
people = build_service('people', 'v1')
results = people.people().searchContacts(query='NAME', readMask='names,phoneNumbers,emailAddresses').execute()
```

**Important:** The People API only searches "My Contacts" in Google Contacts. It does NOT search phone-synced contacts (iOS/Android local contacts, SIM contacts, etc.). If a search returns nothing, the contact may exist on the user's phone but not in Google — ask the user for the number.

Known DRAAS passengers:
- **Nishant Ranka**: ndr@draas.com | 9880055634
- **Roshini (Roshni Murjani/Ranka)**: rnr@draas.com | +91 98450 26390
- **Charitra Murjani**: charitra_murjani@yahoo.com | +91 96201 11672
- **Roshini's maiden name**: Murjani (if traveling as "Roshni Murjani", use Roshini Ranka's details)
- **Roshini is CC'd** on every booking email to cross-check details

For any passenger whose number you don't have, generate a **wa.me link without a phone parameter** — the user clicks it, WhatsApp opens, and they pick the contact from their phone's address book. Use `whatsapp_link(text="message")` with no phone argument.

### 4. Multi-Passenger Split Pattern

This session introduced a common pattern: **same outbound flight for all, different return flights**.

| Scenario | Outbound | Return |
|----------|----------|--------|
| Lead (Nishant) | Shared flight with all | Earlier flight (has meeting/commitment) |
| Companions (Charitra, Roshni) | Shared flight with lead | Later flight (no urgency) |

This happens when the lead needs to return early for a commitment while companions stay longer. The email must state the booking urgency split explicitly.

### 5. Build the Email

**Recipients:**
- **To:** sales1.blr@drahomes.in (Bharat Hawaldar)
- **CC:** rnr@draas.com (Roshini)

**Structure:**

```
Subject: Flight Bookings — [Passengers] — [Dates]

Hi Bharat,

Please arrange the following IndiGo flight bookings:

### 🛫 OUTBOUND — [Date] — [Route]
Flight: [Airline] [Flight#] → Dep: [Time] [Origin] | Arr: [Time] [Dest]

TABLE with columns: Passenger | Name (as on ID) | Phone | Email
- Use blue header (#2E86C1) for outbound section
- Use red header (#E74C3C) for return section
- Gmail strips <style> blocks — use inline CSS (style attribute) and HTML bgcolor on <th> elements

### 🛬 RETURN — [Date] — [Route]
Flight 1: [Flight#] → Dep/Arr times — [Passenger name]
Flight 2: [Flight#] → Dep/Arr times — [Passenger names]

> Book [lead]'s outbound IMMEDIATELY — confirmed meeting.
> For other passengers, wait until Roshini cross-checks and confirms, then proceed on priority.
> Confirm once done with PNR details.

---

P.S. Roshini — Please cross-check all passenger details and confirm back to Bharat. Thanks!
```

**HTML email pattern (confirmed working):**
```python
html_body = """<div style="font-family: Arial, sans-serif;">
<h3 style="color: #2E86C1;">🛫 OUTBOUND ...</h3>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse;">
<tr style="background: #2E86C1; color: white;"><th>...</th></tr>
<tr><td>...</td></tr>
</table>
...
</div>"""

msg = MIMEText(html_body, 'html')
msg['To'] = 'sales1.blr@drahomes.in'
msg['Cc'] = 'rnr@draas.com'
msg['Subject'] = '...'
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
result = gmail.users().messages().send(userId='me', body={'raw': raw}).execute()
```

### 6. Priority Rules (Critical)

- **Lead's flights (Nishant)**: Always book immediately — confirmed meetings take priority
- **Other passengers (Charitra, Roshni)**: Wait for Roshini to confirm details before proceeding
- State this split explicitly in the email — Bharat needs clear instructions on what to book now vs. wait
- The P.S. addressed to Roshini at the bottom of the email serves as both her instruction and a visible marker that she needs to act

### 7. Send via Gmail

```python
from tools.gws_auth import build_service
from email.mime.text import MIMEText
import base64

gmail = build_service('gmail', 'v1')

msg = MIMEText(html_body, 'html')
msg['To'] = 'sales1.blr@drahomes.in'
msg['Cc'] = 'rnr@draas.com'
msg['Subject'] = 'Flight Bookings — Nishant / Charitra / Roshni — 1-2 July'

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
result = gmail.users().messages().send(userId='me', body={'raw': raw}).execute()
```

**Important:** Send directly (not as draft) after user approval. The user profile says "confirm draft first" — once confirmed, send immediately.

## Pitfalls

- **People API returns 0 connections** if the OAuth scope doesn't include `contacts.readonly` or the person isn't in "My Contacts". Fall back to asking the user.
- **Roshni Murjani = Roshini Ranka** (maiden name Murjani). Save this to memory permanently.
- **Missing phone numbers** — Nishant's phone (9880055634) and Roshini's (+919845026390) should be in memory. Other passengers you'll need to search Contacts API.
- **Email HTML tables** — use inline `<table>` with inline CSS colors since Gmail strips `<style>` blocks. Use `bgcolor` attribute instead of `background` CSS for table headers.
- **Threading** — subsequent booking updates should reply in the same thread using `threadId`.
