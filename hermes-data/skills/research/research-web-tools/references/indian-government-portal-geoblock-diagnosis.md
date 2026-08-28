# Indian Government Portal Geo-block Diagnosis

**Trigger:** User asks to check live status/data on an Indian government portal (RERA, DTCP, eCourts, MCA, GST, land records) and the portal won't load from this server. Example: "check my TN RERA application status live".

## Symptom signature — TCP-level geo-block (vs transient outage)

- `curl` times out at TCP connect on BOTH http and https (`curl: (28) Connection timed out`, HTTP 000) — no server response at all
- Browser: `ERR_TIMED_OUT`, `ERR_TUNNEL_CONNECTION_FAILED`, `ERR_CONNECTION_CLOSED`, or `502 Bad Gateway: Upstream proxy error` when a request does land (their WAF/proxy drops foreign traffic)
- All proxy routes fail too — r.jina.ai, Firecrawl/web_extract, allorigins, corsproxy.io (they also run from foreign datacenter IPs)
- DNS resolves fine — the block is at IP/transport layer, not DNS

## Diagnosis ladder (fast, ~2-3 min)

1. **DNS check:** `getent hosts <domain>` — confirms it resolves (it will; geo-block is at transport layer)
2. **Direct curl, both schemes:**
   ```bash
   curl -sS -m 15 -o /dev/null -w "HTTP %{http_code}\n" https://<domain>/
   curl -sS -m 15 -o /dev/null -w "HTTP %{http_code}\n" http://<domain>/
   ```
   - TCP timeout on both = geo-block/firewall
   - Real HTTP status (4xx/5xx/HTML) = site reachable; different problem (JS-rendered, CAPTCHA) → use `indian-government-scheme-research.md` fallback tiers instead
3. **Browser navigate** — confirms same symptom; an HTTP 502 "Upstream proxy error" on http while https times out is their WAF dropping foreign traffic, NOT "site is down"
4. **Proxy attempts** (Google Translate proxy `<domain-with-dashes>.translate.goog/?_x_tr_sl=auto&_x_tr_tl=en`, allorigins, corsproxy, r.jina.ai) — all fail at TCP level; don't spend more than one round on these
5. **Search engines for the specific ID/name** — Google (often CAPTCHA from this IP), Bing, DDG html: usually empty because application data lives behind the portal's own search, not indexed
6. **Wayback Machine** — often 429 rate-limited; live status pages aren't archived anyway
7. **urlscan.io** (`https://urlscan.io/api/v1/search/?q=domain:<domain>`) — may show old scans proving the portal exists, but never live data

## Decision

- **If every route times out at TCP level → geo-block of non-Indian datacenter IPs.** Do NOT keep retrying the same URL (loop warning). Do NOT claim the portal is down.
- **Hand off to the user:** they are in India and can reach the portal from their phone/browser. Ask them to open the specific page (or send the screenshot they already have) and read out/share the status. Then interpret it for them — don't fabricate a status from memory.
- Offer adjacent help that doesn't need the portal: draft a follow-up email/letter to the authority (contact numbers are usually in search results), interpret their existing screenshot, set up tracking once they share updates.

## Pitfalls

- **Verify the official domain first** — e.g. `www.tnrera.in` is a PARKED domain; the real TN RERA portal is `rera.tn.gov.in`. Web search before deep-diving.
- **A 502 "Upstream proxy error" is not "site down"** — it means the request reached their WAF and was dropped; consistent with geo-blocking.
- **Don't loop.** After one diagnostic pass with identical failing args, stop retrying and switch to the hand-off pattern.
- **Never invent the status.** If you can't reach the portal, report the block honestly and rely on the user's screenshot / manual check.

## Verified example

`rera.tn.gov.in`, 30 Jul 2026 — Ranka Oasis TN RERA application check. All routes blocked (browser https/http, direct curl, translate proxy, allorigins 408, corsproxy 403, r.jina.ai timeout, Google CAPTCHA, Bing empty, DDG empty, Wayback 429, urlscan only Nov-2025 scans). Handed off to user's phone; their screenshot confirmed status "Application yet to verify by Scrutiny Officer".
