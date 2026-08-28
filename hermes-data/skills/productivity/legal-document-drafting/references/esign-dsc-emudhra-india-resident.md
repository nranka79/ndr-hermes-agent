# eMudhra Class 3 DSC — Indian Resident Application Guide

**When to use this:** A co-owner/spouse/relative in India needs a Class 3 DSC (Digital Signature Certificate) so their authorized representative can E-sign property documents on their behalf. Covers the full walkthrough from application to signing — specific to eMudhra (esign.emudhra.com / certinext.emudhra.com).

## Why a separate DSC is needed

Aadhaar OTP eSign is **personal** — the digital certificate shows the Aadhaar holder's identity only. The system does NOT support a "representative capacity" mode. So if Raghu needs to sign for himself AND on Farida's behalf, Aadhaar OTP will show Raghu's identity for both signatures → rejected by the sub-registrar.

**Solution:** Farida gets her own Class 3 DSC (signing only). Raghu installs Farida's DSC on his computer and signs "under SPA" on her behalf. Raghu signs himself via Aadhaar OTP.

## Certified Authority: eMudhra

| Detail | Value |
|--------|-------|
| **Website** | emudhra.com |
| **DSC Portal** | certinext.emudhra.com |
| **eSign Portal** | esign.emudhra.com |
| **CCA Licensed** | Yes — India's largest CA |
| **Certificate Type** | Class 3 Individual Signature (Signing only) |

## Documents Required (Indian Resident)

- ✅ **Aadhaar Card** (both sides)
- ✅ **PAN Card**
- ✅ **Passport-size photograph** (white background, smartphone photo acceptable)
- ✅ **Address proof** (Aadhaar itself serves this, or utility bill)
- ✅ **Mobile number** (for OTP verification during process)
- ✅ **Email address**

## Step-by-Step Process

### Step 1 — Apply online
1. Go to: **https://certinext.emudhra.com/** or **https://esign.emudhra.com/**
2. Select **Class 3 Individual DSC (Signing only)** — NOT encryption (cheaper, faster)
3. Choose validity (typically 1 or 2 years)
4. Select standard (₹1,500–₹3,000, 24–48 hrs) or urgent/same-day (₹4,000–₹6,000, 2–4 hrs)

### Step 2 — Fill application
- Enter applicant's name (exactly as on Aadhaar/PAN)
- Date of birth, email, mobile number
- Certificate type: Class 3 Individual Signature

### Step 3 — Upload documents
- Upload scanned copies or clear smartphone photos of:
  - Aadhaar Card (front & back)
  - PAN Card
  - Passport-size photograph
  - Address proof

### Step 4 — Make payment
- Online: credit/debit card, net banking, UPI
- If applicant's card fails, someone else can pay on their behalf

### Step 5 — Video-Based Identification (VBI) call (5–10 min)
- After submission, a VBI call is scheduled (immediate for same-day priority)
- Platform: WhatsApp, Zoom, or eMudhra's own portal
- Applicant needs to:
  - Show **original Aadhaar + PAN card next to face** on camera
  - Verbally confirm: name, DOB, purpose of DSC application
  - State intent: applying for Class 3 DSC for digital signing
- CA rep records the entire call → legally valid audit trail

### Step 6 — Receive DSC
- After successful VBI + document verification → DSC issued
- **Email received with:**
  - Download link for the `.pfx` (or `.p12`) file
  - Password to open the file
- Save the .pfx file and password securely

### Step 7 — Install DSC on a computer
- Download the `.pfx` file to a Windows or Mac computer
- Double-click → Certificate Import Wizard opens
- Enter the password from email
- DSC is installed in the system certificate store
- (eMudhra also provides a one-click installer tool)

### Step 8 — E-sign the document
- Once DSC is installed, open the document signing portal
- Select the installed DSC certificate
- Enter the DSC password
- Document is digitally signed

**Alternative (with SPA):** Export the `.pfx` file + share password with authorized representative → they install on their computer → sign "for and on behalf of [Owner] under SPA dated [Date]". Legally valid because SPA authorizes the representative and DSC tracks to the certificate owner.

## Cost Summary

| Category | Price (₹) | Timeline |
|----------|-----------|----------|
| Standard Class 3 DSC | 1,500 – 3,000 | 24–48 hours |
| Urgent/Same-day DSC | 4,000 – 6,000 | 2–4 hours |

## Signing Workflow (Ranka Amber Example)

| Person | Method | How |
|--------|--------|-----|
| **Farida** (co-owner) | Class 3 DSC via eMudhra | Raghu helps Farida apply online + VBI call |
| **Farida's signature** | DSC installed on Raghu's PC | Raghu signs "under SPA" using Farida's DSC |
| **Raghu** (self) | Aadhaar OTP eSign | Raghu signs personally via Aadhaar OTP |
| **Nishant** (other party) | Aadhaar OTP eSign | Signs from his end |

## What does NOT work

| Scenario | Why |
|----------|-----|
| Raghu uses Aadhaar OTP to sign for Farida | Certificate shows Raghu's identity → rejected |
| Double Aadhaar OTP for two people | Sub-registrar flags duplicate signatures |
