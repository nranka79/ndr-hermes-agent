# Google News RSS Behavior — Employment Generator Tracker

## How Google News RSS ages

Google News RSS does NOT guarantee articles from the last 48 hours. In practice:
- Feeds typically contain articles from the last 2–7 days at most
- Most recent articles are often 3–5 days old even on a "fresh" fetch
- Some queries return articles from weeks or months ago (Google's index is broad)
- The `lastBuildDate` in the channel header tells you when Google last refreshed the feed

**Implication:** The 48h filter will often return 0 matches. This is normal. The skill should run every day regardless — it catches announcements when they exist and produces no rows when none exist.

## PubDate format and parsing

Google News pubDate format: `'Sat, 30 May 2026 04:45:06 GMT'`

Python parsing:
```python
from datetime import datetime, timezone, timedelta
pub_dt = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %Z')
pub_dt = pub_dt.replace(tzinfo=timezone.utc)
```

Common failure: forgetting `.replace(tzinfo=timezone.utc)` — naive datetime objects don't compare correctly with timezone-aware datetimes.

## XML parsing gotchas

1. **Root tag**: RSS with a `<channel>` inside — parse `root.find('channel')` first
2. **Items**: `channel.findall('item')` not `root.findall('item')`
3. **Description field**: Contains HTML entities and `<a href>` tags — strip with `re.sub(r'<[^>]+>', '', description)`
4. **Missing pubDate**: Items without a pubDate silently fail the `strptime` — wrap in try/except, log failures

## Verifying a feed before running at scale

Before any production run, print the 5 most recent article dates:
```python
articles = sorted(articles, key=lambda x: x['pub_dt'], reverse=True)
for a in articles[:5]:
    print(f"  {a['pub_dt'].strftime('%Y-%m-%d %H:%M')} UTC: {a['title'][:70]}")
```

This immediately tells you whether the 48h window will match anything.

## Testing RSS fetch locally

```bash
curl -s -L "https://news.google.com/rss/search?q=GCC+Bangalore+Chennai+2026&hl=en-IN&gl=IN&ceid=IN:en" -o /tmp/test.xml
python3 -c "
import xml.etree.ElementTree as ET
tree = ET.parse('/tmp/test.xml')
root = tree.getroot()
ch = root.find('channel')
print('lastBuildDate:', ch.findtext('lastBuildDate'))
items = ch.findall('item')
print('total items:', len(items))
for item in items[:3]:
    print(' pubDate:', item.findtext('pubDate'), '|', item.findtext('title')[:60])
"
```

## RSS feed URLs

Google News RSS accepts query parameters:
- `q=<search terms>` — URL-encoded search query
- `hl=en-IN` — language
- `gl=IN` — geolocation
- `ceid=IN:en` — country/language code

Example:
```
https://news.google.com/rss/search?q=GCC+OR+new+factory+Bangalore+Chennai+2026&hl=en-IN&gl=IN&ceid=IN:en
```

## What to do when all three feeds return 0 within 48h

This is the expected outcome most days. Do not:
- Rethink the query
- Try different RSS endpoints
- Increase the time window beyond 48h (the skill specifies 48h)

Do:
- Log the run (lastBuildDate + counts)
- Continue to next scheduled run
- If 2+ consecutive weeks show 0 matches, check whether the search queries still match current news phrasing (e.g., "GCC" vs "global capability centre" vs "captive centre")