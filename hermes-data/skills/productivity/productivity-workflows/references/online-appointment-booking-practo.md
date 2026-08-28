# Online Doctor Appointment Booking via Browser (Practo / Hospital Portals)

Multi-step browser workflow for booking a clinic appointment on Practo or a hospital's own website.

## The Booking Pattern

The process ALWAYS ends with entering the user's mobile number for OTP verification. You cannot complete the booking without their number. Present a clear summary of available slots first, then ask for the number.

**Before starting, confirm with the user:**
1. Which doctor / clinic / location?
2. Preferred date and time (or range)
3. Patient name (if not the user)
4. Mobile number (for OTP) — Indian numbers need +91 prefix

## Canonical Practo Flow

### Step 1 — Navigate to doctor profile
```
browser_navigate(url="https://www.practo.com/bangalore/doctor/dr-<slug>")
```

### Step 2 — Click Book Appointment for the desired clinic
The profile page lists each clinic location separately (e.g., Yelahanka, Sarjapur Road). Each has its own "Book Appointment" button.

- Yelahanka (Mon, Wed, Fri) — different ref from Sarjapur Road (Tue, Thu)
- Click the right one: `browser_click(ref="e<ref>")`
- This opens a "Pick a time slot" sidebar on the right of the page

### Step 3 — Navigate date picker to desired date
The sidebar shows a horizontal date strip with left/right arrow buttons. Dates visible initially: Today, Tomorrow, and the next couple of days.

- Click right arrow to advance dates: `browser_click(ref="e<right-arrow-ref>")`
- Each click advances 1-3 days. After 1-2 clicks, a "Next availability on <desired-date>" button appears
- **Click that button** — it is a clickable button, not just informational text
- Use `browser_vision(annotate=True, question="Show me the date picker arrow refs")` to find refs each time

**Important:** The left and right arrow refs change between page loads. Never hardcode them.

### Step 4 — Select a time slot
After clicking the date, the sidebar shows available slots for that day.

- Morning and afternoon sections
- Scroll down within the sidebar to see all slots: `browser_scroll(direction="down")`
- Use `browser_vision(annotate=True)` to find the ref for the desired time
- Click it: `browser_click(ref="e<ref>")`
- **Note:** The doctor's listed clinic hours (e.g. 10 AM - 4 PM) may be wider than the slots Practo shows. The latest bookable slot may be earlier (e.g. 2:30 PM when clinic closes at 4 PM). Always scroll to check all available slots.
- Page transitions to a mobile number entry screen

### Step 5 — Enter mobile number (USER INPUT REQUIRED)
The booking page shows:
- Date, time, doctor name, hospital confirmed
- A text box: "Enter your mobile number"
- "Continue" button (disabled until number entered)
- "You will receive an OTP shortly"

**CRITICAL — Indian mobile number format:**
- Practo's validator may reject bare 10-digit numbers like `9880055634`
- Always use **+91 prefix**: `+919880055634`
- The form is inside an iframe — the browser_click/type tools still work with ref IDs from the snapshot

**You cannot proceed past this point without the user's mobile number.** Stop and ask if you don't have it.

### Step 6 — CAPTCHA challenge (AUTOMATION BLOCKER)
After clicking "Send OTP", Practo presents a **Google reCAPTCHA** image challenge (e.g. "Select all images with a fire hydrant").

**This is a hard blocker for automated agents:**
- The reCAPTCHA is inside a cross-origin iframe that browser_click/type cannot access
- The agent cannot solve image-based reCAPTCHA challenges
- **Action:** Get the current page URL from `browser_console(expression="window.location.href")` and share it with the user so they can take over

### Step 7 — User completes booking (MANUAL)
After CAPTCHA + OTP verification, the user clicks "Continue to request" to confirm the appointment.

## Manipal Hospital Website Flow

### Special: Welcome Modal
Manipal Hospitals shows a "Welcome to manipalhospitals" modal popup:
- "You're on Our Indian Website. Visit the Global site for International patient services"
- Click "Continue Here" to dismiss and use the Indian site
- The button ref changes per load — use `browser_vision` to find it

### Booking Widget
The doctor profile page at `manipalhospitals.com/<location>/doctors/...` has:
- Location combobox (usually pre-set to the right location)
- Speciality combobox
- "Schedule Appointment" button
- After clicking, a booking interface opens with:
  - "Physical Hospital Visit" / "Video Consultation" radio buttons
  - Horizontal date scroll with many date tiles
  - "Next Available Slot" button
  - "Request Call Back" button
- The booking widget is less user-friendly than Practo's — consider falling back to Practo.

## When Automation Hits a Wall

At any point the browser-based agent cannot proceed, **share the current browser page URL** with the user so they can take over:

```
browser_console(expression="window.location.href")
# Returns the current URL → share with user
```

**Important:** Share the live session URL from the Hermes browser, NOT a raw Practo URL. Practo booking URLs contain session tokens and may 404 if opened in a new session without the browser state.

Common blockers:
| Blocker | Action |
|---------|--------|
| Google reCAPTCHA image challenge | Share current browser URL, ask user to solve CAPTCHA and OTP |
| Login/signup required mid-flow | Share URL, user can log into their account |
| Payment/confirmation screen | Share URL, user completes confirmation |
| Cross-origin iframe that tools can't reach | Share URL so user can interact directly |

## Key Pitfalls

| Pitfall | How to handle |
|---------|---------------|
| Browser refs change between loads | Always re-capture with `browser_vision(annotate=True)` before clicking |
| Sidebar time slots may be truncated | Use `browser_scroll(direction="down")` to reveal later slots |
| Date picker needs multiple arrow clicks | Each click advances only 1-3 days. Click repeatedly until desired date appears |
| "Next availability" button text changes | The ref and text vary (Mon 29 Jun vs Wed 1 Jul). Don't hardcode — capture and identify each time |
| Indian mobile number rejected without +91 | Always use `+919xxxxxxxxx` format, not bare 10 digits |
| reCAPTCHA blocks OTP sending | This is a hard automation blocker. Hand off to user via browser URL |
| Manipal modal on first visit | Always dismiss "Continue Here" before clicking Schedule Appointment |
| Same-day booking shows "No Slots Available" | Check for the next available date |
| Doctor's hours vs bookable slots | Listed hours (e.g. 10-4) may not all be bookable online. Scroll to see the full range |
| Practo URL shared externally 404s | Share the live Hermes browser session URL, not the raw Practo URL, because booking state is session-dependent |

## When to Use Practo vs Hospital Website

**Prefer Practo when:**
- The doctor has a Practo profile with online booking
- You need to see available time slots clearly
- Quick booking without account creation needed

**Prefer hospital website when:**
- Practo doesn't have the doctor listed for online booking
- The user specifically asks for the hospital's own portal
- The hospital site has a simpler flow (rare)
