# Website Contact Form Filling — Dark Store Outreach (Jul 2026)

**Campaign:** Gandhinagar Mamata Apartments — Dark Store / Warehouse Outreach  
**Coordinator:** Prakash Singh (psingh@draas.com, +91 97399 32078)  
**Property:** No. 14, Mamatha Apartments, 3rd Cross, 4th Main Road, Gandhinagar, BLR – 560009  
**Space:** ~7,200 sq.ft. (Basement 3,200 + GF double-height 2,000–4,000)

---

## ✅ Forms Successfully Submitted

### 1. Swiggy Instamart — "Rent Your Property" (Google Form)

- **URL:** https://docs.google.com/forms/d/e/1FAIpQLSftnUKOA73mxg15M0LyNnBYk2CvW56I7UJkfAJTQOJR-H_kQQ/viewform
- **Found via:** swiggy.com/instamart-partner → "Rent Your Property" tab
- **Requirements listed:** Min 2,000 sq.ft., high ceilings, truck access, 20+ bike parking, 20 kVA, 2 washrooms
- **Fields filled:** Name (Prakash Singh), Contact (9739932078), Identity (Consultant), City (Bangalore), Locality (Gandhinagar), Lat (12.977716), Lng (77.577864), Address (full), Pin Code (560009), Sq.ft. (7200), Floor (Ground), Rental (left blank)
- **Technique used:** JS console for radio button selection + submit. Fields showed `[disabled]` in accessibility tree but were interactive. Used `browser_console` to verify the phone field value after typing — the `+91` prefix was NOT visible in the field but JS console confirmed the actual value was correct 10 digits.
- **Verified phone value after typing:** `console.log(document.querySelector('input[aria-labelledby="i9"]')?.value)` — returned "9739932078"
- **Status:** ✅ Submitted successfully (showed "Submit another response")

### 2. Delhivery — B2B Enterprises Contact Form

- **URL:** https://www.delhivery.com/solutions/b2b-enterprises
- **Found via:** Main site → Solutions → B2B Enterprises → scroll to "Contact Us" form
- **Fields:** Name, Company Name, Email, Phone Number
- **Note:** No message/textarea field available
- **Status:** ✅ Submitted

### 3. StoreSpace — Contact Us Form

- **URL:** https://storespace.in/contact-us/
- **Found via:** Main nav → Contact Us
- **Fields:** Name, Designation, Company Name, Phone Number, Official Email Id, Product Category (filled "Warehousing / Dark Store Space")
- **CMS:** WordPress with Elementor
- **Technique:** JS console `document.querySelector('#form-field-name').value = '...'` — direct value assignment
- **Status:** ✅ Submitted (button showed "Sending…" then page changed)

### 4. LoadShare Networks — General Enquiry Form

- **URL:** https://loadshare.net/contact
- **Structure:** Accordion-based. Click "General Enquiry" section to expand the form. Also has separate accordions for: First Mile & Last Mile, Line Haul, Warehousing, Partner
- **Fields:** Full Name (Prakash Singh), Work Email (psingh@draas.com), Company (DRA Group), Phone (9739932078 cleaned), Vertical (Ecommerce default), How can we help? (message about Gandhinagar dark store space)
- **⚠️ Phone pitfall:** First attempt with "+919739932078" resulted in "919739932" (stripped +, missing last 3 digits). Fixed by entering just "9739932078".
- **Key technique:** The accordion for "General Enquiry" was collapsed initially. Used `browser_console` with JS to click the accordion header element (`document.querySelector('...').click()`) before the form fields appeared in the DOM. Always check the page structure first with `browser_snapshot` then verify with `browser_console(expression='document.querySelectorAll(\"input, textarea\").length')` to confirm fields exist before trying to fill.
- **Status:** ✅ Submitted (button showed "Sending…" temporarily)

---

## ❌ No Form Found — Alternative Channels Documented

### Xpressbees
- **Checked:** xpressbees.com/contact-us, various nav pages
- **Result:** No generic contact form. Only franchise partner flows (for running a courier booking counter) and cargo fleet partner signup. Neither fits property outreach.
- **Alternative:** Email customercare@xpressbees.com or call +91 (020) 4911 6100

### Pikndel
- **Checked:** pikndel.com, "Partner With Us" dialog
- **Result:** Modal form after clicking "Partner With Us" has: Name, Company Name, Phone, Email, **Current daily order volume** (irrelevant for property owners)
- **Alternative:** Skip — this is for ecommerce brands, not property outreach. Use LinkedIn.

### Flipkart (including Flipkart Minutes)
- **Checked:** flipkart.com/* various paths, partner.flipkart.com, seller.flipkart.com
- **Result:** Flipkart Minutes is invite-only for existing sellers. No public form for warehouse partnerships.
- **Alternative:** Email partnerservices@flipkart.com or call 044-45614700 / 044-67415800

### Apollo Pharmacy
- **Checked:** apollopharmacy.in/contact-us
- **Result:** Only email addresses listed. No contact form.
- **Emails found:**
  - Corporate inquiries: customerservice@apollopharmacy.org
  - Brand listing: brandlisting@apollopharmacy.org
  - Online orders: contactusnow@apollopharmacy.org

### Licious
- **Checked:** licious.in/contact-us (404 page), footer
- **Result:** No contact form. Only phone + email in footer.
- **Alternative:** Email talktous@licious.com or call 1800-4190-786

### PharmEasy
- **Checked:** pharmeasy.in/contact-us (blank page)
- **Result:** No working contact form.
- **Alternative:** LinkedIn — Gaurav Chandak (Regional Manager Supply Chain East+South)

### Navata SCS
- **Checked:** navatascs.com/contact (bot detection blocked access)
- **Alternative:** Try info@navatascs.com or general LinkedIn outreach

### WareIQ
- **Checked:** wareiq.com/contact (blocked by Cloudflare)
- **Alternative:** Try hello@wareiq.com or LinkedIn

---

## 📋 General Company Emails Found (for Wave 2 Referral Emails)

| Company | Email | Source |
|---------|-------|--------|
| **Blinkit** | info@blinkit.com | Footer of website |
| **BigBasket** | customerservice@bigbasket.com | Contact Us page |
| **Shadowfax** | hello@shadowfax.in | Known address (Wave 1 already drafted with PDF) |
| **Zepto (CEO)** | aadit@zeptonow.com | — |

---

## Browser Form-Filling Technique Summary

### The core pattern for each site:
1. `browser_navigate(url)` — go to the contact page
2. `browser_snapshot` — identify field ref IDs from accessibility tree
3. `browser_type(ref, text)` — fill standard text fields
4. `browser_click(ref)` — interact with buttons, radio toggles
5. `browser_console(expression=...)` — JS for stubborn elements
6. `browser_snapshot` — verify submission state

### JS console techniques used:

```javascript
// List all form inputs with their attributes
document.querySelectorAll('input:not([type="hidden"])')
// → inspect .name, .id, .placeholder, .type

// Click by ARIA role (for Google Forms radio buttons)
document.querySelector('div[role="radio"][aria-label="Consultant"]').click()

// Click Google Forms submit button
document.querySelector('span:has(> .NPEfkd)').click()

// Fill fields by ID directly (Elementor/WordPress)
document.querySelector('#form-field-name').value = 'Prakash Singh'

// Find submit button by text content
Array.from(document.querySelectorAll('button, div[role="button"], input[type="submit"]'))
  .find(el => el.textContent.trim() === 'Submit' || el.textContent.trim() === 'Send' || el.textContent.trim() === 'Talk to sales')
  ?.click()

// Extract all email addresses from page
document.body.innerText.match(/[\w.+-]+@[\w-]+\.[\w.]+/g)
```

### Priority for filling forms:
1. **Sites with property-specific forms** (e.g., Swiggy's "Rent Your Property") — highest value, submit immediately
2. **Logistics/3PL companies** with "Contact Us" or "Partner With Us" forms — submit with warehouse space message
3. **E-commerce/brand websites** — generally don't have property-relevant forms; use LinkedIn instead
