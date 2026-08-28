# Google Flights — Browser Automation Patterns

## Overview

Google Flights (`www.google.com/travel/flights`) is the most reliable aggregator for browser automation. It renders fully client-side (React/JS) so the accessibility tree is rich but element refs change between snapshots.

**Status: ✅ Reliable** — No bot detection blocks observed.

## Form Interaction Pattern (Critical)

Google Flights uses a multi-dialog form. The sequence is:

### Step-by-Step

1. **Open Google Flights**
   ```
   browser_navigate(url="https://www.google.com/travel/flights?hl=en&curr=INR")
   ```

2. **Set origin** — Click "Where from?" combobox → type in dialog → select option
   ```
   browser_click(ref="e78")          # "Where from?" combobox
   browser_type(ref=<dialog_combobox>, text="Bengaluru")
   # Dialog opens with listbox — click the city option
   browser_click(ref=<city_option>)  # e.g. "Bengaluru, Karnataka, India"
   ```

3. **Set destination** — Click "Where to?" combobox → type in dialog → select option
   ```
   browser_click(ref="e79")          # "Where to?" combobox
   browser_type(ref=<dialog_combobox>, text="Varanasi")
   browser_click(ref=<city_option>)
   ```

4. **Set departure date** — Click Departure textbox → type date → press Escape to close calendar
   ```
   browser_click(ref="e78")          # Departure textbox (different ref from form fields)
   browser_type(ref=<date_textbox>, text="Mon, May 18")
   # Calendar dialog opens — date cell for "May 18" auto-selected
   browser_press(key="Escape")        # Close calendar without clicking anything
   ```

5. **Search**
   ```
   browser_click(ref=<Search_button>)  # "Search" button
   ```

### Key Ref Patterns (from session)
- Initial load: `e78` = Where from, `e79` = Where to, `e80` = Departure, `e32` = Search
- After setting origin: `e87` = Where from, `e78` = Where to, `e79` = Departure, `e32` = Search
- Dialog open: `e3` = dialog combobox, `e4` = first option, `e5` = second option
- Date picker: `e78` = Departure textbox in dialog, `e9` = selected date cell

**Ref instability**: Element refs (e78, e79, etc.) change between page states. Never hardcode a ref from one snapshot and expect it to work in the next. Always re-snapshot to get current refs.

## Reading Results

### Snapshot → DOM → Result Count

```
browser_snapshot()
```
Look for: `alert "X results returned."` → exact count in one line.

### Element Counting (when snapshot is truncated)

For pages with expandable flight cards, the accessibility tree truncates but the DOM may have more items. Use console:
```
browser_console(expression="document.querySelectorAll('li.list-item').length")
```
Returns integer count. From BLR→VNS session: 8 list items but alert said "4 results" — each flight appears as 2 list items (outbound + return pairing).

## Price Calendar View (Hidden Gem)

When you click the Departure date field, the calendar shows **price per day in each cell**:
```
"gridcell 'Monday, May 18, 2026, departure date. , 17019 Indian rupees'"
```
This lets you scout cheapest dates without a full search. Use `browser_snapshot(full=true)` to see all calendar rows.

## Key Findings

| Pattern | Behavior |
|---------|---------|
| `browser_snapshot()` | Shows 87 element max, truncates long lists |
| `browser_snapshot(full=true)` | Returns full tree but still truncates nested iframes |
| `browser_console` | Works for counting DOM elements invisible in snapshot |
| `browser_scroll` | Scrolls the viewport, not the full page — may need multiple scrolls |
| `dialog` elements | Auto-dismiss on selection — no Escape needed after clicking an option |
| Return date | Both outbound + return must be set — clicking Search with same date = same-day return |
| Round trip toggle | In search form — `combobox "Change ticket type. Round trip"` |

## Live URL Sharing

Every `browser_navigate` and `browser_snapshot` response includes:
```
"live_url": "https://.browser-use.com/agent/<session_id>"
```
**Always share the live_url with the user** so they can watch the session or take over manually.

## Airlines Filter — Known Failure Mode

**Problem**: `departureTime=09%3A00%2C14%3A00` URL param does NOT filter results.

**Fix**: Use browser UI — click "Times" filter button → use sliders (0–24 scale, set earliest to ~9 for 9 AM cutoff). Confirm filter is active by checking for filter pills below search bar.

## Vision Analysis Failure

`browser_vision` uses `google/gemini-2.0-flash` which returns:
```
{'error': {'message': 'google/gemini-2.0-flash is not a valid model ID', 'code': 400}}
```

Use direct API fallback (see travel/SKILL.md → Vision / Image Analysis section) or rely on `browser_snapshot` text content which is reliable.

## Console Errors — When to Check

Run `browser_console()`:
- After any navigation
- After clicking anything that triggers a JS update
- Before scrolling (to establish baseline)

Silent JS errors are high-value findings even when the page appears to work correctly.