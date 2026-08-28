# KrisFlyer Enrollment — Why Automation Fails

## Session Context (May 2026, Nishant Ranka)

User asked to enroll 4 family members in Singapore Airlines KrisFlyer:
- Nishant Ranka — `ndr@ahfl.in`
- Roshini Ranka — `rmurjani@gmail.com`
- Ruhaan Ranka — (his own email)
- Rivaan Ranka — (his own email)

The browser automation repeatedly hit bot detection walls on singaporeair.com and was unable to even load the enrollment form.

## Why KrisFlyer Enrollment Cannot Be Automated

1. **Email OTP verification required** — Singapore Airlines sends a verification email to the applicant. The link must be clicked from the same browser session or the enrollment is abandoned.

2. **SMS OTP required** — After email verification, an SMS is sent to the applicant's registered mobile number. The code must be entered within a short time window.

3. **Bot detection is aggressive** — Singapore Airlines deploys advanced bot detection (CDN-level, JavaScript fingerprinting, browser honeypots). Headless browser automation consistently triggers 403/redirect loops, landing on the US homepage regardless of locale.

4. **Account creation is per-person** — Each family member needs their own KrisFlyer account. You cannot create a "family" account and add members — you create individual accounts, then link family members under a "Family" grouping later.

5. **Parent/guardian required for minors** — Ruhaan and Rivaan are minors. KrisFlyer may require a parent/guardian to co-sign or the child account must be linked to an adult account. Check current policy.

## What to Tell the User

**Step-by-step enrollment for each adult (Nishant and Roshini):**

1. Go to: `https://www.singaporeair.com/in/enroll`
2. Select "India" as country/region
3. Fill: Title, First name, Last name, Date of birth, Nationality, Passport number, Country of issue
4. Fill: Email address, Mobile number (India +91), Address
5. Create a password
6. Submit → check email for verification link → click it
7. Check SMS for OTP → enter it
8. Account activated

**For kids (Ruhaan and Rivaan):**
- After adults are enrolled, go to KrisFlyer dashboard → "Manage Family"
- Add child as family member
- Miles earned by children can be pooled under the parent account

## Retro-Credit Claim URLs

While completing enrollment, simultaneously claim past flights:

**Malaysia Airlines retro-credit (DVAZVS, May 9 2026):**
- URL: `https://www.singaporeair.com/in/en/claim-miles`
- Select "Malaysia Airlines" → enter PNR DVAZVS

**Air India retro-credit (JBUV4Z, May 21 2024):**
- URL: `https://www.singaporeair.com/in/en/claim-miles`
- Select "Air India" → enter PNR JBUV4Z

**JAL miles (claim separately, JAL Mileage Bank):**
- URL: `https://www.jal.co.jp/jmb/en/`
- Or: `https://www.jal.com/en/jalmileagebank/`
- JAL is Oneworld — cannot credit to KrisFlyer. Must claim into JAL Mileage Bank separately.
- Claim window: 12 months from flight date

## Key References

- Singapore Airlines KrisFlyer: https://www.singaporeair.com/in/en/ppsclub/krisflyer/
- JAL Mileage Bank: https://www.jal.co.jp/jmb/en/
- Malaysia Airlines Enrich: https://www.malaysiaairlines.com/enrich