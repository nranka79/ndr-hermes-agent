# Practo Booking — Example Session (Jun 2026)

## Doctor
- **Name:** Dr. Srikanta J T
- **Specialty:** Lead Consultant — Pediatric Interventional Pulmonology, Allergy and Sleep Medicine
- **Qualification:** MBBS, DCH, DNB, Fellowship In Paediatric Pulmonology
- **Experience:** 20 yrs (16 yrs as specialist)
- **Rating:** 96% (55 patients)

## Locations & Schedule
| Location | Days | Time | Fee |
|----------|------|------|-----|
| Manipal Hospital Yelahanka | Mon, Wed, Fri | 10:00 AM - 04:00 PM | ₹1,200 |
| Manipal Hospital Sarjapur Road | Tue, Thu | 04:00 PM - 06:00 PM | ₹900 |

## Practo Links
- **Profile page:** https://www.practo.com/bangalore/doctor/dr-srikanta-j-t-pulmonologist
- **Doctor ID:** 1967981 (extracted from profile URL path)
- **Direct booking URL:** https://www.practo.com/appointment/dr-srikanta-j-t-pulmonologist/1967981/book

## Booking Flow Walkthrough
1. Navigation to profile page — shows doctor info, two locations (Yelahanka + Sarjapur Road) with separate "Book Appointment" buttons
2. Clicking the Yelahanka "Book Appointment" button did NOT navigate (SPA issue) — had to use direct booking URL
3. Direct booking URL lands on mobile number entry screen
4. Entered `9880055634` first → got "Not a valid mobile number. National number Eg: (201) 555-0123 International number Eg: +15107488230"
5. Re-entered as `+919880055634` → accepted, OTP sent
6. OTP form appeared in iframe from accounts.practo.com
7. reCAPTCHA challenge appeared after OTP send (fire hydrant images)

## What Went Well
- Direct booking URL bypassed the SPA button issue
- +91 prefix resolved the mobile number validation

## What to Do Differently Next Time
- Use direct booking URL from the start (skip clicking "Book Appointment" on profile page)
- Always enter mobile with +91 prefix
- Share live browser URL when CAPTCHA appears so user can take over

## Browser Use Cloud Session (Live URL Lesson — 28 Jun 2026)

After the initial Practo booking via basic browser, switched to Browser Use Cloud for better interactive site handling. This was a separate run that demonstrated a critical tool-usage lesson.

### Critical User Correction
- User asked "Send me browser use url" after I shared the direct Practo page URL
- The Practo URL returned 404 when opened — Practo's SPA booking pages are session-bound
- CORRECT: share the `live_url` field from `browser_use_cloud`'s function return, not the page URL via browser_console
- The user cannot open a session-bound Practo URL in their own browser — only the browser_use_cloud live URL works

### What happened in this session
1. browser_use_cloud navigated to Practo booking page
2. Mobile +9198XXXXXX34 entered, OTP sent, user shared 6-digit OTP
3. Date selected: Mon 29 Jun, time: 3:30 PM, location: Manipal Yelahanka
4. Booking confirmed — request ID #1967981-3543942 received
5. User then wanted Tue 30 Jun 3 PM instead at Yelahanka
6. Dr. Srikanta is at Sarjapur Road on Tuesdays (Yelahanka is Mon/Wed/Fri) — flagged this in the chat message
7. Provided complete copy-paste message block for Manipal chat window with all patient details

### Patient data extraction for chat message
- Manipal Patient ID **7603646** found in PFT PDF text dump (field "ID" next to patient name)
- Ruhaan's DOB: 23 May 2012, Age: 14 (from ruhaan_ranka_medical_summary.json)
- Clinical context pulled from the medical dossiers and JSON summaries
- All assembled into one copy-paste block with careful schedule-conflict flagging
