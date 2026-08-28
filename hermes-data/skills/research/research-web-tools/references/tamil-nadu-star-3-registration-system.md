# Tamil Nadu STAR 3.0 / Presence-less Registration System — Technical Setup Requirements

Researched 2026-08-27 via Jina+DDG (Tavily unavailable). Updated 2026-08-28 via direct browser (tnreginet.gov.in portal, Google Play Store, UIDAI website). Sources: The Hindu, Verified.RealEstate, Daga Developers, WiseIndia, VNCT Global, Mantra official RD installation guide, tnreginet.gov.in portal (User Manual + FAQ + Help Videos sections), Google Play Store (com.tnreginet.tnigrs).

## What It Is

STAR 3.0 (Simplified and Transparent Administration of Registration) = TNREGINET 3.0. Launched Aug 17, 2026. Mandatory for first sale of flats/plots and government deeds. Resale transactions still need physical SRO visits.

The portal is at https://tnreginet.gov.in — web-based UI accessible from any OS browser.

## Portal Accessibility from VPS

**Updated 2026-08-28: tnreginet.gov.in IS reachable from the Hermes VPS** via browser tools (browser_navigate). The portal loads fully in English and Tamil, with all sections (User Manual, FAQ, Help Videos, services) accessible. No geo-blocking from datacenter IP. Previous session (2026-08-27) reported unreachable, likely a transient DNS/network issue.

## Critical: Windows ONLY. Chromebook/Linux/macOS will NOT work.

The biometric capture system requires a **Mantra RD Service (Registered Device Service)** — a Windows background process that:

- Runs as a Windows Service (Control Panel > Administrative Tools > Services)
- Listens on localhost ports 8003 (MFS100), 11100 (MFS110), 11101 (MIS100V2 iris)
- Communicates with Mantra Management Server at https://aadhaardevice.com
- Bridges the USB fingerprint/iris hardware to the browser via local HTTP

The browser calls `http://localhost:11100/...` when the web portal requests biometric capture. No equivalent RD Service exists for Linux, macOS, or ChromeOS.

## Is It Web-Based or Installed Software?

**Both.** The UI is web-based (TNREGINET portal in any browser), but biometric capture requires two installed Windows components:

1. **Device drivers** for Mantra MFS100, MFS110, MIS100V2 — standard `.exe` installers
2. **Mantra RD Service** — Windows service that auto-starts and sits in the system tray

The web portal + local RD Service interaction flow:
- User fills deed details on web portal
- Clicks "capture biometric" → browser sends HTTP request to localhost:11100/11101
- RD Service triggers the USB hardware, captures fingerprint/iris
- Data sent directly to UIDAI servers for verification
- No biometric data passes through the web portal server — it's device→RD Service→UIDAI direct

## Required Hardware (UIDAI-Approved Models)

These are the ONLY devices listed in the official Mantra installation guide:

| Device | Model | Purpose | ~Price (2026) |
|--------|-------|---------|---------------|
| Fingerprint Scanner | Mantra MFS100 | Optical fingerprint L0 device | Rs 2,900 |
| Fingerprint Scanner | Mantra MFS110 | Capacitive fingerprint L1 registered device | Rs 2,500 |
| IRIS Scanner | Mantra MIS100V2 | Iris scanner for parties/witnesses who can't give fingerprints | Rs 3,100 |
| Webcam | Any compatible (Logitech C922 Pro recommended) | Live photo capture during authentication | Rs 9,900 |

All MUST be UIDAI-compliant registered devices. The MFS110 and MIS100V2 register with Mantra's management server on first connection (unplug/re-plug cycle).

## Recommended Desktop Spec

Minimum: Windows 10/11 Pro, 8GB+ RAM, 256GB+ SSD, web browser (Chrome/Firefox/Edge).
The quoted Lenovo M70T Gen6 (Ultra 5, 32GB, 512GB NVMe, Win 11 Pro) is more than adequate.

Browser configuration needed (Chromium-based browsers when HTTP is used — not needed for HTTPS):
```
chrome://flags/#block-insecure-private-network-requests → Disable
```

## Aadhaar OTP Authentication Alternative (Confirmed from Portal FAQ)

The portal's FAQ (Q.11) and news articles confirm that TWO authentication methods are available:

1. **Biometric** (fingerprint/iris) — requires Windows + RD Service + USB scanner
2. **Aadhaar OTP** — an OTP sent to the Aadhaar-linked mobile number of each party. No biometric hardware needed. The party receives the OTP on their own phone and enters it into the web portal.

The biometric path is the standard for builder/developer bulk registrations. The OTP path works for individual parties who cannot provide fingerprints. For builders doing volume registrations, the biometric setup (Windows + scanner) is still the practical choice since you control the entire process in your office.

FAQ Q.11: "If fingerprint verification fails, authentication can be completed using an Iris Scanner."
FAQ Q.12: "Up to three times. If verification fails after three attempts for any reason, the document can be registered using the conventional physical registration method."

## TNREGINET Mobile App — Confirmed: Registration NOT Supported

The official TNREGINET Android app (com.tnreginet.tnigrs, 100K+ downloads, last updated Mar 6, 2026) is a **search-only tool**. The government's own response to user reviews:

> "Current functionality in mobile app supports various search functionality alone and for registration need to use portal. Additional features will be coming to mobile in future."

The app supports: EC search, token availability, guideline value, society/partnership firm/chit fund search, document status, stamp vendor search, building value calculator. It does NOT support: document upload, Aadhaar authentication, biometric capture, payment, or any registration workflow.

The "mobile phone" alternative reported in news articles refers to the **OTP authentication method** on a mobile browser, not the mobile app. The builder still does the document upload/data entry on a laptop/desktop browser.

## Daily Webex Training for Builders

The portal prominently displays:
"Presenceless Registration process - Online meeting is being conducted on daily basis for Banks, Builders & Promoters from 02.00-03.00 PM on all working days."

Link: https://igr.webex.com/igr/j.php?MTID=mcedac14f848a67e8be1042143f6a5cd2

TCS (Tata Consultancy Services) runs the portal and conducts daily orientation. Highly recommended for builders setting up the system — join the Webex session (2-3 PM, every working day).

## TCS Software Helpline

Portal displays: "Software queries: 1800 102 5174"
Complaints/Clarifications: 9498452110 / 9498452120 / 9498452130

## 4 PDF User Manuals Available on Portal

The User Manual > Document Registration-Presenceless section contains 4 downloadable PDFs:

1. Presenceless Mortgage deed (1.22 MB)
2. Presenceless Sale deed Creation (2.12 MB)
3. Presenceless Deposit of Title deed creation (0.93 MB)
4. Presenceless Deed of Receipt (0.6 MB)

Download links are JavaScript-based: `viewAttachment_9(mpgId, 'viewAttach')` — triggered via onclick on the portal. The mpgId values are: 872182817 (mortgage), 872182778 (sale deed), 872182579 (deposit of title deed), 872182580 (deed of receipt). To download via terminal: `curl "https://tnreginet.gov.in/portal/Upload?flag=viewAttach&attachmentNameHidden=9&mpgId=<mpgId>" -L` (may need session cookies).

## Step-by-Step Process from Portal (5 Steps)

The portal homepage displays the registration flow as:

1. Entry party, property details to submission
2. Aadhaar authentication and Photo capture
3. Online Payment
4. Submission for Registration
5. Registration with Digital signature and digital return

## Applicable Deed Types

From the portal homepage: "Applicable for the following deed"
- First Sale of Plot (with consecutive Deposit of Title Deed)
- First Sale of Flat (with consecutive Deposit of Title Deed)

## Who This Applies To

Phase 1 (Aug 17, 2026 onward) — mandatory for:
- Builders/developers doing first sale of apartments/flats
- Land promoters doing first sale of plots
- Government authorities executing sale deeds
- Banks/financial institutions registering linked mortgage documents

NOT applicable to resale transactions between individuals — those still need physical SRO visits.

## Post-Registration

- Registered deed available for download from citizen login for 60 days (free)
- Print in COLOUR on legal-size paper — colour print = "Original" deed
- Also pushed to registered mobile via WhatsApp
- After 60 days, only B&W certified copies available

## Sources

- The Hindu explainer (2026-07-24): https://www.thehindu.com/news/national/tamil-nadu/what-is-tamil-nadus-new-presence-less-property-registration-service-explained/article71261434.ece
- Verified.RealEstate pre-requisites: https://community.verified.realestate/article/presence-less-property-registration-in-tamil-nadu-first-sale-of-flats-plots-and-government-deeds/
- Verified.RealEstate mandate notice: https://community.verified.realestate/article/mandatory-e-registration-for-first-plot-and-apartment-sales-starting-august-17-2026/
- Daga Developers step-by-step: https://www.dagadevelopers.com/blog/-tamil-nadu-s-presence-less-land-registration-register-property-without-visiting-the-office-2026-guide-
- WiseIndia STAR 3.0 guide: https://wiseindia.in/star-3-0-tamil-nadu-property-registration-guide/
- Mantra RD Installation Guide (official): https://verified.realestate/tn-land-law/registration/tn-registration-pdfs-mantra-installation-guide-2026-v10-1-ad617e