# My Golden Pass — Research Findings (May 2026)

> Boutique investment migration and Golden Visa advisory firm.
> Offices in Mumbai (India), Dubai (UAE), and Lisbon (Portugal).

## Verified Contact Details

| Field | Value |
|---|---|
| **Phone / WhatsApp** | +91 8097984460 (raw: 918097984460) |
| **Email** | info@mygoldenpass.com |
| **Website** | https://mygoldenpass.com |
| **Mumbai Address** | Zee Nayak, MG Road, Vile Parle East, Mumbai — 400057 |

## Firm Profile

- **Type:** Boutique Investment Advisory & Golden Visa Consultancy
- **Specialization:** Citizenship by Investment (CBI), Golden Visa programs, Investment Migration
- **India office:** Mumbai (MG Road)
- **Other offices:** Dubai, Lisbon
- **Model:** 100% free consultation (website states "100% Free consultation!")

## WhatsApp Encoding

Full-width ampersand `＆` (U+FF06) = `%EF%BC%86` inside message body.
Phone: raw 10 digits, no +, no spaces, no dashes.

**wa.me link:**
```
https://wa.me/918097984460?text=Hi%20Team%2C%0A%0AI%20am%20Nishant%20Ranka%20%E2%80%94%20Founder%20%EF%BC%86%20CEO%20of%20O3%20Infotech%20(Kelsa.io)%20and%20Director%20at%20DRA%20Group%2C%20based%20in%20Bangalore.%20I%20have%20sent%20a%20detailed%20email%20to%20your%20team%20outlining%20my%20profile%20and%20UAE%20Golden%20Visa%20requirements.%0A%0ANoted%20your%20Mumbai%20office%20(MG%20Road%2C%20Vile%20Parle%20East).%20Happy%20to%20visit%20or%20connect%20via%20WhatsApp%20at%20your%20convenience.%0A%0ALooking%20forward%20to%20your%20guidance.%0A%0ARegards%2C%0ANishant%20Ranka%0A%2B91%2098450%2026390%0Andr%40draas.com
```

## Email Template

**To:** info@mygoldenpass.com
**CC:** ndr@draas.com
**Subject:** UAE Golden Visa Eligibility Inquiry — O3 Infotech / DRA Group Founder

> Dear Team,
>
> I am Nishant Ranka, Founder and CEO of O3 Infotech (Kelsa.io — enterprise SaaS platform, ~INR 3 Crore ARR, 50+ enterprise clients) and Director at DRA Group (infrastructure and real estate, ~INR 2,000 Crore turnover, offices in Bangalore and Chennai).
>
> My background: M.Eng CS, Stevens Institute of Technology, USA · Prior at Deutsche Bank ($200M project) and Burgiss · Founded IRCA (sold to Origo Sino India)
>
> Looking to explore UAE Golden Visa eligibility under entrepreneur / exceptional talent categories. I note your Mumbai office on MG Road, Vile Parle East — I can visit or travel to Dubai if needed.
>
> Requesting: (1) Eligibility assessment (2) Documentation requirements (3) Processing timeline (4) Fee structure
>
> Best regards,
> Nishant Ranka · ndr@draas.com · +91 98450 26390

## Discovery Notes

- Found via DuckDuckGo HTML search for "UAE Golden Visa advisory India Bangalore Mumbai"
- Site uses NitroPack (performance plugin) — initial curl returned empty; `--compressed` flag + Chrome UA succeeded
- Contact phone found in JSON-LD structured data (schema.org `ContactPoint` object)
- Mumbai address found in JSON-LD `PostalAddress` object
- `/contact/` redirects to `/contact-us/` (301 redirect) — always follow redirects