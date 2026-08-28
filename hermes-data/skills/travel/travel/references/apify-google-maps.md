# Apify Google Maps — Absorbed from research/apify-google-maps

## What This Reference Covers

Search Google Maps for businesses, offices, shops, or places using Apify. Returns name, address, phone, rating, reviews, hours, website, and Google Maps URL.

**Skill status:** Absorbed into `travel` umbrella (2026-05-29). Original at `research/apify-google-maps/`.

## When to Use

"Find architects in Bengaluru", "nearby places", "business listings", "contact info for a place", "coffee shops near Connaught Place"

## API Pattern

```bash
curl -s -X POST \
  "https://api.apify.com/v2/acts/apify~google-maps-scraper/run-sync-get-dataset-items?token=$APIFY_API_KEY&timeout=120" \
  -H "Content-Type: application/json" \
  -d '{"searchStringsArray":["<QUERY>"],"maxCrawledPlacesPerSearch":20,"language":"en"}'
```

**Request body:**
```json
{
  "searchStringsArray": ["<query>"],
  "maxCrawledPlacesPerSearch": 20,
  "language": "en",
  "countryCode": "in"
}
```

## Query Examples

| User request | searchStringsArray |
|---|---|
| "Find architects in Bengaluru" | `["architects in Bengaluru"]` |
| "Coffee shops near Connaught Place Delhi" | `["coffee shops near Connaught Place Delhi"]` |
| "Real estate agents in Gurgaon" | `["real estate agents Gurgaon"]` |

## Response Fields

- `title` — business name
- `address` — full address
- `phone` — phone number
- `website` — website URL
- `totalScore` — rating (0–5)
- `reviewsCount` — number of reviews
- `openingHours` — array of day/hour pairs
- `categoryName` — business category
- `url` — Google Maps URL

## Notes

- `countryCode: "in"` for India — change if user specifies other country
- Sync endpoint times out at 300s max; use async run + poll for large results
- If `APIFY_API_KEY` is empty → tell user: "APIFY_API_KEY not configured in Hermes environment"
