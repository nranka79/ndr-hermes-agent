# BBC RSS Feeds

BBC publishes free RSS feeds — no API key, no scraping, no rate limiting.

## Endpoints

| Feed | URL |
|------|-----|
| Top Stories | `https://feeds.bbci.co.uk/news/rss.xml` |
| World | `https://feeds.bbci.co.uk/news/world/rss.xml` |
| UK | `https://feeds.bbci.co.uk/news/uk/rss.xml` |
| Business | `https://feeds.bbci.co.uk/news/business/rss.xml` |
| Technology | `https://feeds.bbci.co.uk/news/technology/rss.xml` |
| Science | `https://feeds.bbci.co.uk/news/science_and_environment/rss.xml` |
| Entertainment | `https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml` |

General pattern: `https://feeds.bbci.co.uk/news/[section]/rss.xml`

## Python: Extract Headlines

```python
import urllib.request, xml.etree.ElementTree as ET

req = urllib.request.Request(feed_url, headers={'User-Agent': 'Mozilla/5.0'})
xml_content = urllib.request.urlopen(req).read().decode('utf-8')
root = ET.fromstring(xml_content)
for item in root.findall('.//item'):
    title = item.find('title')
    if title is not None:
        print(title.text)
```

## When to use vs ddgs

- **BBC RSS**: Best for current headlines from a specific outlet. Reliable, no install needed.
- **ddgs.news()**: Best for cross-outlet aggregation, trending stories, or when you need a specific narrative angle. Poor at returning homepage lead headlines for broad queries like "BBC News".
