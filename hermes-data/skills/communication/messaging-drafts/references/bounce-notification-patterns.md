# Bounce Notification Patterns — ndr@draas.com

## What they are
Gmail generates `Delivery Status Notification` emails from `mailer-daemon@googlemail.com` whenever a sent message fails to deliver. Each failed delivery attempt can spawn multiple identical bounce emails (one per retry), so a single bad address can produce 5–15 identical notifications.

## Common failure patterns seen

### 1. Invalid domain (typo in domain)
- `rahul.vinod.kumar@example.com` — `example.com` doesn't exist
- Sends 1–2 bounce emails per send attempt

### 2. Address not found (valid domain, invalid user)
- `roshiniranka3@gmail.com` — address doesn't exist
- Sends multiple identical bounces in rapid succession (13 seen in one session)
- Likely a typo of `roshiniranka@gmail.com`

### 3. @findingform.design — former employees
These people appear to have left Finding Form Design Studio:
- `ar.amrutha@findingform.design` — Amrutha Bimal Kumar (resigned May 5, 2026)
- `priyadharshini@findingform.design`
- `sinchana@findingform.design`
- `anest@findingform.design`
Each generates Delay then Failure notifications over 24–48 hours as Gmail retries.

## Handling
- **Trash immediately** — they carry no actionable info once the failure is confirmed
- **Daily cron** at 11am recommended to keep inbox clean
- **Before sending to old @findingform.design contacts**, verify current email addresses

## Query for cleanup
```
from:mailer-daemon@googlemail.com subject:"Delivery Status Notification" in:inbox
```
Trash all results — no need to inspect individually.
