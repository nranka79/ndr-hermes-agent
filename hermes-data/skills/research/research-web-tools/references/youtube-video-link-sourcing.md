# Sourcing REAL YouTube Video Links (for embedding instructional videos in deliverables)

**When to use:** The user wants a deliverable (training program, how-to guide, workout plan, tutorial)
that includes YouTube videos demonstrating form/technique, and you must provide REAL, working
watch URLs — never fabricated ones. Works when Tavily is down (HTTP 432) or when NDR's
no-Apify/no-Tavily directive applies. Distinct from `youtube-metadata-extraction.md` (which pulls
metadata from a KNOWN video) — this reference is about FINDING and VERIFYING links for a topic.

## Technique — browser console extraction (verified)

1. Navigate the browser to a YouTube search page:
   `https://www.youtube.com/results?search_query=<url-encoded terms>`
   e.g. `beginner+bodyweight+squat+proper+form`
2. Run this exact JS in the browser console to pull the REAL result links:
   ```js
   Array.from(document.querySelectorAll('a#video-title')).slice(0,8).map(a => ({title: a.textContent.trim(), href: a.href}))
   ```
   (Use `browser_console` with `expression=` set to that snippet.)
3. **CLEAN each href** down to the bare watch URL by stripping tracking params:
   - Strip everything from `&pp=` (YouTube search tracking) onward
   - Strip `&t=<sec>` / `&t=<fmt>` (play-at-timestamp) params too
   - Result form: `https://www.youtube.com/watch?v=<11-char-video-id>`
4. **Verify the IDs are real** — they come straight from YouTube's DOM, so an ID that was
   actually extracted is real. NEVER guess, hand-type, or fabricate a video ID; a wrong ID
   returns a dead page and breaks the deliverable.

## Curation rules (for a polished deliverable)

- **Prefer full-length instructional videos over Shorts.** Many search results for exercises
  ("jump squat", "lateral band walk") return mostly `/shorts/...` — skip those and pick the
  standard-length tutorial that actually teaches form.
- **Populate each category with 1–3 options**, so the user/trainer has a primary and backup.
- **Prefer credible channels** for form-critical/health content: sports-medicine / physio /
  hospital / well-known fitness trainers over random uploaders. E.g. Ohio State Sports Med,
  E3 Rehab, Bupa, Bowflex, NASM-affiliated trainers.
- **Filter for the right audience** when the user says "for kids" / "12-year-old" — search
  `... for kids` / `... for youth athletes` / `... for beginners` to surface age-appropriate, lower-intensity demos.
- **For children's training**, prefer videos that explicitly say for kids / youth / beginners,
  and avoid videos showing heavy or to-failure lifting.

## Pitfall — don't over-delegate without a verification requirement

If you delegate video sourcing to subagents (good for covering many categories in parallel),
INSTRUCT every subagent to use this exact browser+console method and return ONLY cleaned,
actually-extracted URLs. Explicitly forbid fabricating IDs, and require the cleaning step
(strip `&pp`/`&t`). This session ran 3 parallel subagents this way with 100% real results.

## Parallel batch pattern

For a deliverable with many categories (e.g. a 6-category athlete program), split categories
across 2–3 parallel subagents, each restricted to the browser toolset, each returning cleaned
`watch?v=` URLs per category. Keep ≤~8 results per search, 1–3 chosen per exercise. The YouTube
results snapshot does NOT show video URLs in the a11y tree — you MUST use the console
extraction; the `a#video-title` selector is the reliable hook.

## Delivery note

Long lists of links are fine as clean `https://www.youtube.com/watch?v=<ID>` lines; they render
as tappable links in Telegram. Cross-check you stripped all `&pp`/`&t` before delivering so the
links stay clean and shareable.
