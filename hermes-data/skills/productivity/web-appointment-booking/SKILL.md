---
name: web-appointment-booking
description: Book medical/service appointments on Indian healthcare portals (Practo, Manipal Hospital, etc.) — browser navigation, mobile OTP, date/time selection, CAPTCHA handoff, and live URL sharing so the user can take over when automation hits a wall.
category: productivity
tags: [practo, appointment, booking, doctor-appointment, otp, captcha, browser-automation]
---

# Web Appointment Booking

## Overview
Book doctor appointments on Indian healthcare booking platforms (Practo, hospital direct portals). These sites use mobile OTP verification and Google reCAPTCHA — both of which eventually need the user's involvement. The skill covers getting as far as possible before handing off.

## Trigger
User asks to book an appointment with a doctor, hospital, or service provider on a website.

## Pre-Booking — Context Gathering

Before touching the browser, collect:

1. **Doctor name + specialty** — Confirm spelling from prior records, not voice transcription
2. **Hospital + location** — Many doctors practice at multiple branches (e.g., Manipal Yelahanka vs Sarjapur Road)
3. **Preferred date** — Check the user's calendar for existing commitments
4. **Preferred time window** — Account for school pickup, work hours, commute
5. **Patient name** — If different from the user (e.g., child, spouse)
6. **Patient's previous consultation history** — Check the medical folder for prior visits to this doctor (medication list, diagnosis, follow-up notes) so you don't ask questions the records already answer

Check the user's Google Calendar for existing appointments around the desired time to avoid double-booking.

## Finding the Doctor's Booking Page

- **Practo**: Search or navigate directly to `https://www.practo.com/bangalore/doctor/{doctor-slug}`
- **Direct hospital portal**: Search for the hospital's appointment booking page
- Verify the correct location — one doctor may have different booking pages for different branches

## Booking Workflow — Practo

### 1. Navigate to Doctor Profile
Open the doctor's Practo profile page. The URL contains the doctor slug and ID (e.g., `/doctor/dr-srikanta-j-t-pulmonologist/1967981` where `1967981` is the doctor ID).

### 2. Click "Book Appointment"
Click the "Book Appointment" button for the correct hospital location (visible under the location heading in the Info tab).

**SPA fallback**: If the click doesn't trigger navigation (single-page-app behaviour), use the direct booking URL:
```
https://www.practo.com/appointment/{doctor-slug}/{doctor-id}/book
```
This lands directly on the mobile-number entry screen.

### 3. Enter Mobile Number
- **ALWAYS use +91 prefix**: Enter `+9198XXXXXXXX`, not `98XXXXXXXX`
- Without the +91 prefix, Practo shows "Not a valid mobile number" and doesn't send the OTP
- Click "Continue"

### 4. OTP Verification
- Practo sends a 6-digit OTP to the mobile number
- The OTP form loads inside an iframe from `accounts.practo.com`
- Tell the user: "Check your phone for a 6-digit OTP from Practo"
- The user must provide the OTP — you cannot read their SMS
- Enter the OTP into the textbox and click "Continue to booking"

### 5. Select Date and Time
- Use the date navigation arrows (left/right chevrons) to reach the desired date
- The date grid shows available dates; click the one you want
- Time slots appear in a sidebar — scroll down to reveal slots below the fold (the sidebar may only show ~5 slots at a time)
- When 20-30+ slots exist (e.g., 9 AM-4 PM with 30-min intervals), you may need to scroll 6-10 times to reach 3-4 PM slots — scroll aggressively
- If the desired time doesn't appear (e.g., only slots up to 2:45 PM on a 10 AM-4 PM schedule), check the next available date — the doctor may be at a different location with different hours
- If the exact time isn't available, pick the closest available and note the difference to the user
- Click the desired time slot

### 6. Confirm Booking
- After selecting the time, review the appointment summary (doctor, location, date, time, fee)
- Click "Request appointment" or "Confirm" to submit
- Practo will show a request ID (e.g., #1967981-3543942) with status "Pending confirmation from hospital"
- Inform the user of the request ID and that the hospital needs to confirm

### 6a. When the Slot Isn't Available
- If the user's preferred time doesn't appear, check nearby dates at the same location
- If the preferred location doesn't have slots on the desired date, check the doctor's other locations — tell the user about the trade-off
- Keep any existing booking as backup until the new one is confirmed

## CAPTCHA Handling

Practo may present Google reCAPTCHA at the "Send OTP" step:

- reCAPTCHA is inside a cross-origin iframe and **cannot be automated**
- The user sees "Select all images with [object]" (bicycle, fire hydrant, crosswalk, etc.)
- **Action required**: Share the live browser URL and let the user complete the CAPTCHA
- After they complete it, the OTP will be sent to their phone

## Live URL Sharing Pattern

There are TWO browser tools, each with a different URL sharing pattern. Use the right one.

### Basic Browser (browser_navigate / browser_click etc.)
- Runs server-side; the user cannot see it directly
- **Get the URL**: `browser_console(expression='window.location.href')` to read the page URL
- **Share with the user**: Send the URL — the user opens it in their own browser
- Works because the URL is a standard web page the user can access independently
- Use for simple research and single-page snapshots

### Browser Use Cloud (browser_use_cloud tool)
- Runs on a cloud service with live streaming; the user CAN watch it in real time
- **The `live_url` field is already in the function response** — do NOT extract page URL via browser_console
- **Share with the user**: Send the `live_url` from the function return value verbatim
  - CORRECT: "You can watch the browser live here: https://browseruse.browserbase.com/..."
  - WRONG (user correction): Sending the Practo page URL — this returns 404 because Practo's SPA booking pages are session-bound
- **When to share**: Any time the user asks to see what's happening, or when you hit a wall (CAPTCHA, need user input, paused_for_human status)

### Common Pattern (both tools)
1. **Share the URL** (see above for correct source per tool)
2. **State what's been done**: Steps completed so far
3. **State what the user needs to do**: CAPTCHA? Enter OTP? Confirm booking? Select time?
4. **Heads-up on what's next**: "After you enter the OTP, you'll need to select a date/time slot"

## Pitfalls

- **Missing +91 prefix**: Practo rejects `98XXXXXXXX` format. Always enter `+9198XXXXXXXX`
- **OTP in cross-origin iframe**: Reachable via the accessibility snapshot (ref IDs work), but the CAPTCHA inside the iframe is not
- **reCAPTCHA is non-automatable**: Google's challenge widgets are intentionally cross-origin and un-bypassable. Always hand off to the user
- **Time slots hidden below fold**: The Practo sidebar truncates; always scroll down to check for later slots
- **SPA button not navigating**: "Book Appointment" may trigger a JS modal without changing the URL. Use the direct `/appointment/{slug}/{id}/book` URL as a fallback
- **Doctor ID extraction**: The doctor numeric ID is in the profile URL path — e.g., `/doctor/.../1967981` = ID `1967981`
- **Wrong location selected**: A doctor may practice at 2+ branches with different schedules. Confirm the location before entering the booking flow
- **Calendar double-booking**: Always check the user's calendar first so you don't book over an existing appointment

## Post-Booking — Hospital Chat Message

When the user asks for a copy-paste ready message to send via a hospital's online chat window (to request or reschedule an appointment):

### Collect from prior medical records
1. **Patient full name** — from medical records
2. **Age / DOB** — from medical summary
3. **Father/Guardian** — from the user's relationship context
4. **Hospital Patient ID** — Search PFT report PDFs for the "ID" field next to the patient name. Text-extracted PDF output often shows "ID" on the same line as the name. Multiple IDs may exist across tests — use the one that appears consistently across visits.
5. **Phone number** — from user info
6. **Doctor name + specialty** — confirmed from research
7. **Clinical context** — diagnosis, current meds, reason for visit (review/follow-up), items to bring (spacer, mask, inhalers), recent test results
8. **Preferred date/time** + alternate suggestions if schedule conflict exists

### Format (user preference)
- Wrap the entire message in a markdown code fence (```) so it's one block to copy-paste
- Lead with "Hi, I'd like to request an appointment for my [relation]"
- Include ALL fields in a structured readable format — don't make the user fill in blanks
- Flag schedule conflicts explicitly: "I understand Dr. X is at [location] on [day] — if [time] isn't available, suggest the closest alternative"
- Mention any existing Practo booking and request ID if this is a reschedule

### Example structure
```text
Hi, I'd like to request a follow-up/review appointment for my son.

Patient Name: [full name] (Master)
Age: [age] yrs (DOB: [date])
Father: [name]
Hospital Patient ID: [ID from records]
Phone: [phone with +91]

Doctor: Dr. [name] — [specialty]

Preferred Date: [day], [date]
Preferred Time: [time]
Location: [hospital branch]

Type of Visit: Follow-up / Review
Diagnosis: [brief diagnosis]
— Items to bring: [spacer, mask, inhalers]
— Current medication: [key meds]
— Recent results: [key findings]

Note: [scheduling caveats]

Kindly confirm availability. Thank you.
```

## Related Skills

- `medical-certificates` — Post-appointment medical records management (filing prescriptions, updating medical index, creating medication calendar events)
- `gws-automation` — Calendar checks before booking

## Reference Files

- `references/practo-booking-session-example.md` — Full walkthrough of a Practo booking session (Dr. Srikanta J T at Manipal Yelahanka), with URLs, doctor ID, and lessons learned
