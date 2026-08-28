# Web Research Fallback Ladder

When `web_search` / `web_extract` fail or rate-limit (Firecrawl backend outages/credit exhaustion, 429s), switch to this ladder instead of retrying the same tool. Order by reliability/cost:

1. **Wikipedia/Wikidata API (curl or urllib)** — most reliable fallback for facts and statuses (metro lines, expressways, suburban rail, tech parks, airports). Pattern: `https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=1&exintro=1&format=json&titles=<Title>`; add `prop=coordinates&titles=A|B|C` for coords; `exintro` for the summary only, or fetch full text and slice the section you need. Include a browser-like User-Agent.
2. **OSM/Nominatim + Overpass API** — geocoding and POI discovery (see mymaps-kml-delivery.md for the full ladder). Free, no key.
3. **Direct curl of target sites** — broker blogs, project pages, news articles: `curl -sL -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ... Chrome/125.0" <url>` then strip tags with regex (`re.sub(r'<[^>]+>', ' ', html)`). WordPress blogs and PDFs (pdftotext) usually work. Realty/broker pages are often the ONLY place rent/capital figures are published.
4. **Real browser (browser_navigate)** for search engines and JS-heavy pages:
   - DuckDuckGo web search in the browser gives readable snippets — but it CAPTCHAs after ~2–3 queries per session ("select all squares containing a duck"); pace queries.
   - Bing in the browser works; extract results via browser_console JS (`document.querySelectorAll('#b_results > li')` → title/url/snippet). Bing misparses quoted/or-ed queries — use plain keyword phrasing.
   - Google Maps works in the browser for place verification (limited view without login, but place cards + plus codes render).
5. **Beware blocked curl paths**: Mojeek 403, SearXNG instances mostly down/429, DDG lite/html returns a homepage shell when rate-limited, Bing CAPTCHAs curl. Don't burn time — jump to the browser.
6. **PDF notices**: auction/statutory PDFs (anaarc.com etc.) — `curl -sL -A <UA>` then `pdftotext -layout`. Some PDFs are image-only → OCR.

## Verifying subagent output
Subagents in `delegate_task` share the same web backend — when it's down, their "research" degrades to training-knowledge estimates (they say so explicitly, but the numbers look plausible). Treat subagent summaries as hypotheses, never verified facts. Spot-check every number that enters a deliverable, and flag anything you could not verify (source + status in the doc).
