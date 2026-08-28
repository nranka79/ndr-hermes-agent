---
name: healthcare-appointment-booking
description: Browser-based appointment booking with Indian hospitals and clinic aggregators — handling modals, regional prompts, accessibility tree gaps, and fallback flows. Complements the curl/directory-based search in india-local-services-search.md.
version: 1.0.0
---

# Healthcare Appointment Booking (Indian Hospitals)

When booking a doctor appointment for a user, use this layered approach.

## Layer 1 — Search for the Doctor

### DuckDuckGo over Google

Google search pages often trigger a bot-detection CAPTCHA when accessed via headless browser (`browser_navigate`). DuckDuckGo works reliably for initial discovery:

```
browser_navigate(url="https://duckduckgo.com/?q=Dr+Name+speciality+Hospital+City+appointment")
```

DuckDuckGo returns clean HTML with the doctor's Manipal/Practo/etc. profile links in the search results.

### Verify the Doctor's Profile

From DuckDuckGo results, click through to the hospital's doctor profile page. Key info to extract:
- Full name, qualifications, speciality
- Hospital location(s) and consultation days/timings
- Consultation fee
- Direct booking link

## Layer 2 — Hospital Website Booking Flow

Many Indian hospital websites (Manipal, Apollo, etc.) have a booking widget that goes through these steps:

### Regional Selection Modal

When "Schedule Appointment" is clicked, a modal with a world map may appear saying "You're on Our Indian Website" with "Continue Here" / "Go to Manipal Hospitals Global" buttons.

**Problem**: These modal buttons often do NOT appear in the browser accessibility tree snapshot (`browser_snapshot`), so they can't be referenced via `browser_click(ref="...")`.

**Solution**: Use `browser_console` to execute JavaScript that finds and clicks the element:

```python
# Step 1: Find the button
browser_console(
    expression="Array.from(document.querySelectorAll('button')).filter(b => b.textContent.includes('Continue Here')).map((b,i) => ({index: i, text: b.textContent.trim()}))"
)

# Step 2: Click it
browser_console(
    expression="Array.from(document.querySelectorAll('button')).filter(b => b.textContent.includes('Continue Here'))[0].click()"
)
```

### Post-Modal Booking Widget

After dismissing the regional modal, the booking widget still shows a "Schedule Appointment" button that may not redirect to a booking form on first click. The modal reappears if the cookie/localStorage selection wasn't persisted.

**Workaround**: Use the `browser_console` JS technique above to click "Continue Here" first, THEN click "Schedule Appointment" via `browser_click`.

### When Hospital Website Fails

If the hospital's own booking flow is blocked by:
- Recurring modals that won't dismiss
- Complex multi-step JS widgets that don't render in headless browser
- CAPTCHA challenges

**Fall back to Practo** (Layer 3).

## Layer 3 — Practo (Preferred Aggregator)

Practo is the most reliable booking aggregator for Indian hospital appointments in headless browser mode.

### URL Pattern

```
https://www.practo.com/<city>/doctor/dr-<name>-<speciality>
```

Navigate directly to the Practo profile page for the doctor.

### What Practo Shows

- Doctor's full profile with qualifications, experience, rating
- For each hospital location:
  - Consultation days (e.g., "Mon, Wed, Fri")
  - Time slots (e.g., "10:00 AM - 04:00 PM")
  - Fee (e.g., "Rs. 1,200")
  - "Book Appointment" button
- Patient reviews and ratings

### Booking via Practo

1. Click the "Book Appointment" button for the desired location
2. A "Pick a time slot" sidebar/popup opens with:
   - Date selector: "Today", "Tomorrow", plus specific dates
   - Shows slot count per date (e.g., "30 Slots Available")
   - Slots marked as available or unavailable
3. Click on an available date/time slot
4. A booking confirmation page loads (left panel: appointment summary; right panel: login/OTP form)
5. Complete phone verification (see "Practo OTP/Login Flow" below)

### Date Navigation in the Sidebar

The date picker uses a paginated carousel — not all dates are visible at once.

**Layout**: Typically 4 date buttons visible at a time, with left and right arrow buttons to paginate.

**References in the accessibility tree**:
- The right arrow is usually one of the last clickable refs in the sidebar (e.g., `ref=e56` or `ref=e90`)
- Date buttons are at `y=426` or `y=501` in vision annotations, arranged horizontally

**Navigation sequence** (for a doctor available Mon/Wed/Fri):
- Initial state shows: "Today", "Tomorrow", "Tue, 30 Jun" (and maybe "Wed, 1 Jul" if paginated)
- First right-arrow click → scrolls to show next batch of dates
- Second right-arrow click → reveals "Wed, 1 Jul" as the "Next availability" button
- Click "Next availability on Wed, 1 Jul" to reveal time slots for that date

**Visual verification**: Use `browser_vision(annotate=True)` after each arrow click to confirm the new date appeared before clicking it.

### Time Slot Discovery Beyond What's Visible

Practo's sidebar often says "30 Slots Available" but the visible portion only shows the first 8-10 slots (up to ~2:30 PM). To discover ALL available slots, use `browser_console` with a JavaScript expression:

```javascript
Array.from(document.querySelectorAll('[class*="slot"]'))
  .map(el => el.textContent.trim())
  .filter(t => t.match(/\d/))
```

This reveals the full slot list including slots hidden by sidebar truncation. For example, the vision snapshot might show slots only up to 02:30 PM, but the JS extraction reveals 03:30 PM is also available.

### The Booking Confirmation Page

After selecting a date/time slot, Practo navigates to a booking confirmation page with a URL pattern like:

```
https://www.practo.com/appointment/dr-<name>/<doctor_id>/book?type=request_appointment&doctor_id=<id>&appointment_time=<ISO-encoded>&prepaid=false&amount=<fee>&...
```

**Left Panel**: Appointment summary showing:
- Doctor name, qualifications, specialty
- Hospital name and address
- Date and time confirmed
- "Change Date & Time" link
- "Get Directions" link
- "Go back to my results" link

**Right Panel**: Login/OTP verification form (inside an iframe)

### Practo OTP/Login Flow

The right panel contains a form inside an iframe with these stages:

**Stage 1 — Mobile Number Entry**
- Input field labeled "Mobile Number" (placeholder: "Mobile Number")
- "Send OTP" button
- The form validates the number format — Indian numbers may need to be entered as 10 digits only (9880055634) or in international format (+919880055634)
- If validation fails, an edit icon (pencil) appears next to the number

**Stage 2 — reCAPTCHA Challenge**
- When "Send OTP" is clicked, a Google reCAPTCHA challenge appears
- Typically an image-selection challenge ("Select all images with bicycles")
- The reCAPTCHA is in a cross-origin iframe and CANNOT be solved programmatically
- **This is a hard blocker** — inform the user and share the booking URL for them to take over

**Stage 3 — OTP Entry**
- After the CAPTCHA is solved, a 6-digit OTP is sent via SMS to the provided mobile number
- Input field: "Please enter the 6 digit OTP here to verify"
- Options: "Get via call" or "Resend OTP" links
- "Continue to request" button to submit

**Stage 4 — Booking Confirmation**
- After OTP verification, the booking is submitted
- A confirmation screen appears with appointment details

### Handling the Iframe

The OTP form lives inside an iframe. The `browser_*` tools (click, type) work across iframe boundaries for elements captured in the snapshot/vision annotations — you can directly interact with elements inside the iframe using their ref IDs.

**Note**: Practo requires phone verification for completing the booking. The browser automation can pre-fill the form up to the reCAPTCHA stage, which is a hard blocker requiring human intervention.

### Available Slot Patterns

- **Same-day slots**: Usually filled by the time you search
- **Next-day slots**: May show availability depending on the doctor's schedule
- **Future dates**: More likely to have open slots

Cross-reference the doctor's weekly schedule (shown on the profile) with the date picker to confirm the right location.

## Layer 4 — Filling Patient Details

When booking, you'll need from the user:
- Patient name (and age/DOB for child patients)
- Phone number
- Email address
- Preferred date and time

**IMPORTANT**: Always present the available options to the user BEFORE committing to a booking. Use `clarify` to ask:
```
Which date and time works best? Available: [options]
```

Do NOT automatically book without user confirmation of date/time.

## browser_console + JS for Hidden Elements

This is the key technique when the accessibility tree doesn't capture all interactive elements (common with modals, overlays, custom dropdowns, and captcha walls).

### Find Elements Not in the Accessibility Tree

```javascript
// Count all buttons on the page
document.querySelectorAll('button').length

// Find buttons by text content
Array.from(document.querySelectorAll('button'))
  .filter(b => b.textContent.includes('Continue Here'))
  .map((b,i) => ({index: i, text: b.textContent.trim(), classes: b.className}))

// Find by class name
document.querySelectorAll('.booking-btn')

// Find modal/dialog elements
document.querySelectorAll('[role="dialog"], [role="modal"], .modal, .popup')
```

### Click Hidden Elements

```javascript
// Click first matching button
Array.from(document.querySelectorAll('button'))
  .filter(b => b.textContent.includes('Continue Here'))[0].click()

// More specific: click by unique text
document.evaluate("//button[contains(text(),'Continue Here')]", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue?.click()
```

### Verify State After JS Click

Use `browser_vision` to visually confirm the state changed after a JS click, since the accessibility tree may not reflect it immediately.

## Summary Workflow

1. DuckDuckGo → find doctor profile
2. Try hospital website → handle regional modal via browser_console JS
3. If blocked → Practo as fallback
4. Show user the availability (days, timings, fees, next open slot)
5. Confirm date/time with user before proceeding
6. Fill booking form up to the point where user credentials/verification are needed

## Pitfalls

- **reCAPTCHA is a hard blocker.** Google's cross-origin reCAPTCHA challenge inside an iframe cannot be solved programmatically. When it appears (after clicking "Send OTP"), hand the booking URL to the user and ask them to complete the CAPTCHA and OTP flow.
- **Mobile number format varies.** Some Practo forms accept 10-digit Indian numbers (9880055634), others require international format (+919880055634). If validation fails with a warning, use the edit icon to retry with the other format.
- **Sidebar scrolling ≠ page scrolling.** `browser_scroll` scrolls the main page, not the internal booking sidebar. The sidebar's scrollable area may not respond to `browser_scroll`. Use `browser_console` JS (`document.querySelectorAll('[class*="slot"]')`) to extract all options instead of relying on scrolling to reveal them.
- **Date pagination may wrap.** Clicking the right arrow multiple times cycles through date batches. Use `browser_vision(annotate=True)` after each click to confirm you've landed on the correct date before proceeding.
- **Practo may require login.** If the user isn't logged into Practo, a "Login / Signup" button appears in the header. The booking flow works without logging in via phone OTP verification, so the login header element can be ignored.
- **Modal buttons missing from accessibility tree.** Hospital website modals (regional selection popups) often don't appear in `browser_snapshot`. Use `browser_console` with JavaScript (`.querySelectorAll('button')` → text match → `.click()`) as documented in the JS Hidden Elements section above.

## Related

- `references/india-local-services-search.md` — curl/directory-based search for Indian services (mentions Practo, JustDial)
- `references/duckduckgo-full.md` — DuckDuckGo search patterns
