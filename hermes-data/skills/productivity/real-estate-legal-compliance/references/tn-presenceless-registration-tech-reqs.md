# TN Presence-Less Registration (STAR 3.0) — Technical Requirements

## Overview

Tamil Nadu's STAR 3.0 (Simplified and Transparent Administration of Registration) Sprint 1, launched Jan 2026 by CM Stalin, enables presence-less property document registration. Made mandatory for first-sale plots/flats from Aug 17, 2026. Portal: **TNREGINET** (tnreginet.gov.in).

## Key Documents & Sources

- The Hindu (Jul 24, 2026) — explainer article
- New Indian Express (Jan 22, 2026) — launch coverage
- India Today (Aug 18, 2026) — mandatory first-sale coverage
- Mathrubhumi English (Aug 18, 2026)
- usthadian.com (Feb 7, 2026) — UPSC current affairs summary
- Official TNREGINET Android app (com.tnreginet.tnigrs, Tamilnadu Registration Dept)

## How It Works

Entirely web-based for document upload, payment, deed creation, and processing. BUT the Aadhaar biometric authentication requires a **local software component** — the UIDAI RD Service.

## Critical: UIDAI RD Service

UIDAI's **RD Service (Registered Device Service)** is required to interface the biometric scanner with the browser.

- A Windows **background service** that runs on your PC
- Communicates with the USB fingerprint/iris scanner
- Talks to UIDAI's authentication server on the backend
- The web application (TNREGINET) sends commands to this local service via a localhost API
- **This service is Windows-only.** UIDAI does not provide an RD Service for macOS, Linux, or ChromeOS

## Device Compatibility Matrix

| Device | Works? | Why |
|--------|--------|-----|
| Windows PC + biometric scanner | Yes | RD Service runs natively; standard setup for volume registrations |
| Chromebook | No | ChromeOS cannot run Windows background services |
| Linux (Ubuntu, etc.) | No | No official RD Service from UIDAI |
| Android phone + browser | Partial | Portal works, OTP authentication works, but the mobile app doesn't support full registration yet |
| Android phone + biometric scanner | No (currently) | Would need RD Service Android SDK in the TNREGINET app — not yet implemented |
| iPad/iPhone | Partial | Portal works in Safari, no RD Service integration |
| Android tablet + browser | Partial | Same as Android phone |

## Mobile Alternatives

### Option 1: Aadhaar OTP (Easiest, No Extra Hardware)

The TNREGINET portal supports Aadhaar OTP-based authentication on mobile browsers. The buyer/seller receives an OTP on their Aadhaar-linked mobile number. No biometric scanner needed.

This is the simplest path for occasional registrations from a phone or tablet.

### Option 2: AadhaarFaceRD App

UIDAI's AadhaarFaceRD app (Android) uses the phone's front camera for liveness detection + face matching against Aadhaar records. TNREGINET could potentially integrate with this, but currently the mobile app doesn't support registration at all.

### Option 3: Full Biometric on Android (Not Yet Available)

Would require:
- Android with USB-OTG support
- UIDAI-certified USB fingerprint scanner (Mantra/Morpho/Startek) with USB-C/OTG connector, OR Bluetooth biometric device
- RD Service Android SDK (distributed to registered AUAs only — not publicly downloadable)

## Current TNREGINET Mobile App Status

The official app (com.tnreginet.tnigrs, updated Mar 6, 2026):
- **Supports:** Document status search, EC search, birth/death registration search
- **Does NOT support:** Actual property registration
- Developer's own statement (May 5, 2026): *"Current functionality in mobile app supports various search functionality alone and for registration need to use portal. Additional features will be coming to mobile in future."*

## Practical Registration Workflow (Desktop)

1. Create login credentials on TNREGINET portal
2. Upload sale documents online (scanned PDFs)
3. Parties (buyer, seller, witnesses) log in remotely from their respective locations
4. Aadhaar authentication via fingerprint/iris scan (via RD Service + scanner) OR Aadhaar OTP
5. Webcam photo capture of all parties
6. Digital payment via online/UPI
7. Sub-Registrar verifies and digitally signs
8. Registered document delivered electronically to user's login dashboard + WhatsApp
9. Entire process same-day, 24x7

## What the Desktop Quotation Includes

A quotation for "Sevagana Palli" desktop setup typically includes:
- Windows PC (must run the RD Service)
- UIDAI Level 1 biometric device (USB fingerprint scanner — Mantra/Morpho/Startek brands)
- Webcam (for photographing executants + witnesses)
- Iris scanner (bundled in some quotes; Level 1 = fingerprint only by default)

## Bottom Line

For developer-scale volume registrations, the Windows desktop + biometric scanner setup is correct. For occasional mobile use, Aadhaar OTP via the mobile browser works today. Full mobile biometric support requires the TNREGINET app to be updated with RD Service SDK — currently pending.
