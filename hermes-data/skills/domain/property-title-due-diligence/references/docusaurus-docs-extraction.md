# Docusaurus Docs Extraction via llms-full.txt

When web_extract/Tavily fails (credits/432) on a Docusaurus-hosted docs site (e.g. hermes-agent.nousresearch.com/docs, many OSS projects), the site ships a full markdown dump that curl can grab directly — no browser, no extraction API.

## Recipe (proven Aug 2026 on Hermes docs)
1. `curl -sL <docs-url> -o page.html` — Docusaurus is server-rendered; the HTML contains asset links.
2. Find the LLM dump link:
   `grep -o '/docs/assets/files/llms[-a-z]*-[a-z0-9]*\.txt' page.html | sort -u`
   → typically `llms-full-<hash>.txt` (complete docs, ~3.5MB for Hermes) and `llms-<hash>.txt` (outline).
3. `curl -sL "https://site/docs/assets/files/llms-full-<hash>.txt" -o llms-full.txt`
4. Map structure fast: `grep -n "^# \|^## " llms-full.txt` → section line numbers.
5. Extract slices: `sed -n 'A,Bp' llms-full.txt`.

## Why it works
Docusaurus v3.10+ generates LLM-readable dumps (`llms.txt` / `llms-full.txt` conventions). The full dump is one markdown file — faster, complete, and free of the LLM-summarization truncation that web_extract applies to pages >5000 chars.

## Notes
- The site's `/docs/assets/files/llms-*.txt` hash changes per docs build — always re-derive from the HTML, don't hardcode.
- This beats browser navigation for docs research (no JS, no bot walls, no OOM).
- The bundled `hermes-agent` skill is protected/blocked in some profiles; the docs site + this dump is the authoritative fallback for "how do I configure Hermes" questions.
