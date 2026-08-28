# Product / Software UI Screenshot Research

When the user wants to SEE what a software product, app, or website UI looks
like — "what does ServiceNow's ticketing screen look like", "show me the
dashboard", "can you get me screenshots".

## Why this exists

Tavily/web_search returns text. The user often wants VISUAL reference — what
a UI actually looks like, what fields a form has, how the screen is laid out.
This is NOT a text-search task. Use Bing Image Search as the primary vehicle.

## Tool ladder

1. **Bing Images** (primary — works from VPS datacenter IP)
2. **Google Images** (fallback — captcha-blocked from VPS, verified 2026-08-26)

## Bing Image Search workflow (verified working)

### Step 1: Navigate
```python
browser_navigate(url="https://www.bing.com/images/search?q=ServiceNow+incident+ticket+detail+form+interface+screenshot")
```

Query tips:
- Include product name + what you want to see (e.g. "ServiceNow incident ticket form")
- Add terms like: "interface screenshot", "dashboard view", "ticket detail", "UI"
- Keep it specific — "ServiceNow IT ticketing interface" not just "ServiceNow"

### Step 2: Evaluate results
Call `browser_vision` to see what's on the page. The overlay shows a grid of
thumbnails. Available result types:
- **Full ticket form** — multi-field detail view with caller, category, priority, assignment
- **List/table view** — all tickets in tabular format with columns
- **Dashboard** — charts, widgets, KPIs
- **Self-service portal** — user-facing submission form
- **Configuration screen** — admin/settings view

### Step 3: Open a result
The first thumbnail is auto-selected into the overlay pane. If you need a
different one, scroll down and click another image result's ref.

### Step 4: Capture the screenshot
```python
browser_vision(question="Show me the full ServiceNow ticket form that's currently open")
```
The `screenshot_path` in the response gives you the local file path.

### Step 5: Deliver to user
Include `MEDIA:/path/to/screenshot.png` in your response so the platform
sends it as a native image attachment.

### Step 6: Cycle to next result
Use the "Next image result" button (ref @e232 in the snapshot) to cycle
through the search results without going back to the grid:
```python
browser_click(ref="@e232")
```

## Pitfalls

- **Google Images throws captcha** from the VPS — do not retry more than once.
  Bing Images works (verified 2026-08-26).
- **Bing's carousel suggestions** (top row) are text labels, not images —
  don't click them. Click actual image thumbnails in the main grid.
- **Multiple image results per grid cell** — Bing shows 3 images stacked in
  one cell labelled "Image result for ...". The first click opens the first;
  there's no straightforward way to cycle the stacked ones.
- **Image overlay might not show the full image** — Bing sometimes serves a
  cropped preview. `browser_vision` on the overlay still captures the visible
  portion, which is usually sufficient for UI layout reference.
- **Don't fabricate screenshots** — never describe a UI from memory. Always
  fetch real images. If no results return, tell the user.
- **Browser screenshot quality** — the browser viewport is ~1265×720. For
  dense dashboard UIs, consider taking multiple screenshots of different
  sections.

## Example queries

```
ServiceNow incident ticket detail form interface screenshot
ServiceNow ITSM dashboard view
Jira ticketing system interface screenshot  
Zendesk ticket form view
Salesforce service console screenshot
```