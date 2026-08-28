# X/Twitter Post Media & Full Text Without Auth (Syndication API)

The public syndication endpoint returns a tweet's full text and media URLs with
NO authentication — no OAuth, no xurl, no API key. Works for most public
tweets (verified Aug 2026). Ideal for retrieving route-map / infographic images
embedded in news-adjacent posts (metro maps, charts, posters).

## Endpoint

```
https://cdn.syndication.twimg.com/tweet-result?id=<TWEET_ID>&token=a&lang=en
```

- `<TWEET_ID>` = the numeric id from the tweet URL (`/status/<id>`).
- Returns JSON: `text` (full text, newlines intact), `mediaDetails[]` with
  `media_url_https` = direct `pbs.twimg.com/media/...` image URLs, plus user,
  date, etc.

## Usage

```bash
curl -s "https://cdn.syndication.twimg.com/tweet-result?id=2051697722705707072&token=a&lang=en" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('text')); [print(m.get('media_url_https')) for m in (d.get('mediaDetails') or [])]"
```

In Python:
```python
import json, urllib.request
url = f"https://cdn.syndication.twimg.com/tweet-result?id={tid}&token=a&lang=en"
data = json.loads(urllib.request.urlopen(url, timeout=30).read().decode())
for m in (data.get("mediaDetails") or []):
    print(m.get("media_url_https"))
```

The `pbs.twimg.com` media URLs are directly downloadable (plain GET, no auth)
and stable.

## Pitfalls
- Some tweets (very recent, or with restricted visibility) return an error or
  empty `mediaDetails` — fall back to the browser or the user.
- The `token` param can be any value; `a` works.
- This returns a single tweet, not timelines or search — use it to resolve
  specific post IDs you already know (e.g. from x_search results or URLs in
  articles).

## When to use
- User asks for "the images doing the rounds" on a news topic — search X first
  (x_search), collect tweet IDs from results, then fetch media via syndication.
- A tweet URL appears in a news article or skill reference; you need its image.
