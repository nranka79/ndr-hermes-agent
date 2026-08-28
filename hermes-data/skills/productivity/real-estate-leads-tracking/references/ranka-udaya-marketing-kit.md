# Ranka Udaya — Marketing Kit

Pre-baked assets for Ranka Udaya, Sarjapur, Bangalore. Use when generating on-demand WhatsApp outreach for fresh leads.

## Project

- **Name:** Ranka Udaya
- **Type:** Premium residential plots
- **Location:** Sarjapur, Bangalore
- **Budget range:** Plots from ~₹48 Lac (as seen in leads)

## Digital Assets

- **Digital Tour (drone view):** https://digitour.housing.com/droneview/ranka_udaya
- **Google Maps Location:** https://maps.app.goo.gl/8umNL84oo3CMnw9z5
  - *Note:* The Maps pin shows "70 Estate" as the label — still use this link. The user knows and accepts this.
- **Uploaded marketing image:** User shares during session via Telegram; forward as separate WhatsApp photo

## Key Selling Points (as dictated by Bharat Hawaldar, Jun 2026)

1. **🌳 250+ acres greenery & golf course**
   - Surrounded by open greens, golf course — pure air, open spaces, peaceful living
   - Key differentiator from other Sarjapur projects

2. **🏭 Exide factory next door — investment gold**
   - Next to Exide factory with 3,000+ employees working there
   - Huge rental demand — "no tension about tenants" if investing
   - Key selling point for investment buyers

3. **🏗️ Sarjapur-Attibele corridor — rapid development**
   - Booming corridor with multiple apartments, villas, and plotted developments
   - Infrastructure and residential projects coming up all around
   - Good for both end-use and investment

## Message Template (initial touch — fresh lead)

```
Hi {Name}, thanks for your interest in Ranka Udaya plots, Sarjapur.

Premium residential plots in a prime location:

🌳 250+ acres greenery & golf course - pure, open living
🏭 Next to Exide factory (3,000+ employees) - excellent rental demand, no tension about tenants
🏗️ Sarjapur-Attibele corridor - booming with apartments, villas & plotted developments

📍 https://maps.app.goo.gl/8umNL84oo3CMnw9z5
🚁 https://digitour.housing.com/droneview/ranka_udaya

Budgets from competitive range. Want a site visit?

Best,
Bharat | DRAAS Realty
```

## Delivery Pattern

1. **If user expects simple wa.me link:** Generate wa.me link with full encoded message (use `urllib.parse.quote(msg, safe='')`) and present as clickable markdown link
2. **If user wants image "connected" to the workflow:** Build the HTML tool from `templates/wa-link-sender.html`:
   - Copy the marketing image alongside the HTML
   - Replace `{{PROJECT_NAME}}`, `{{IMAGE_FILENAME}}`, `{{MESSAGE_TEXT}}` with project values
   - Deliver both files to the user
3. Tell user: "Open the HTML on your phone → long-press image to save → enter number → tap send → attach image from gallery"
4. If user reports truncation, re-encode with `safe=''` and re-verify
