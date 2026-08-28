# Public Data Source APIs

Quick-reference for public APIs that return structured data without authentication.

## Wikipedia API

**Endpoint:** `https://en.wikipedia.org/w/api.php`

**Required headers:** Must include `User-Agent` or request fails with 403 Forbidden.

```python
import urllib.request, json

url = 'https://en.wikipedia.org/w/api.php?action=query&titles=Indian_Railways&prop=extracts&exintro=true&format=json'
req = urllib.request.Request(url, headers={'User-Agent': 'HermesAgent/1.0 (research)'})
r = urllib.request.urlopen(req, timeout=10)
data = json.loads(r.read().decode())
```

**Common parameters:**
- `action=parse` — full page parsed (includes wikitext)
- `action=query` — structured data from page
- `prop=extracts&exintro=true` — lead paragraph only
- `prop=wikitext` — raw wikitext
- `section=N` — specific section

**Page structure from `action=query&prop=extracts`:**
```python
pages = data['query']['pages']
for pid, p in pages.items():
    print(p['extract'])  # HTML fragment
```

## wttr.in (Weather)

**Endpoint:** `https://wttr.in/{location}?format=j1`

No API key. Returns JSON with current conditions and forecast.

```python
import urllib.request, json
url = f'https://wttr.in/Bangalore,India?format=j1'
req = urllib.request.Request(url, headers={'User-Agent': 'HermesAgent/1.0'})
data = json.loads(urllib.request.urlopen(req).read().decode())
current = data['current_condition'][0]
print(current['temp_C'], current['weatherDesc'][0]['value'])
```

## Have I Been Pwned API

Requires an API key. Returns 401 without one.

```python
url = 'https://haveibeenpwned.com/api/v3/breachedaccount/{email}?truncateResponse=false'
# Header:hibp-api-key: YOUR_API_KEY
```

No workaround without a key.

## When to use vs ddgs

| Source | Use when |
|--------|----------|
| Wikipedia API | Structured facts, lead paragraphs, wikitext |
| wttr.in | Current weather, forecast |
| HIBP | Breach lookups (requires API key) |
| ddgs | General web search, news, headlines |
