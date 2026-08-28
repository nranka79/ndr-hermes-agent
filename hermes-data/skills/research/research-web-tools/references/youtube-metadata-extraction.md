# YouTube Metadata Extraction (when browser & transcript API are blocked)

When the browser tool is unavailable AND `youtube_transcript_api` returns `RequestBlocked` (common from cloud/VPS IPs), use YouTube's **oEmbed API** as a zero-dependency fallback to get the video title, author, and description.

## oEmbed API

```bash
curl -s "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=VIDEO_ID&format=json"
```

Returns JSON with:
- `title` — video title
- `author_name` — channel name
- `author_url` — channel URL
- `thumbnail_url` — thumbnail image
- `html` — embed iframe HTML
- `type` — "video"

### Example output
```json
{
  "title": "How People Pay $1,200 for Business Class (While You Pay $8,000)",
  "author_name": "Flight Checklist",
  "author_url": "https://www.youtube.com/@FlightChecklist",
  "thumbnail_url": "https://i.ytimg.com/vi/B7UhvLionTw/hqdefault.jpg",
  "type": "video"
}
```

## Getting the Full Description

If oEmbed only returns a short description or none, scrape the YouTube page HTML with curl and parse `ytInitialData`:

```bash
curl -sL "https://www.youtube.com/watch?v=VIDEO_ID" -H "User-Agent: Mozilla/5.0" | \
  python3 -c "
import sys, re, json
html = sys.stdin.read()
match = re.search(r'ytInitialData\s*=\s*({.*?});', html, re.DOTALL)
if match:
    data = json.loads(match.group(1))
    try:
        panels = data['contents']['twoColumnWatchNextResults']['results']['results']['contents']
        for item in panels:
            if 'videoSecondaryInfoRenderer' in item:
                sec = item['videoSecondaryInfoRenderer']
                if 'attributedDescription' in sec:
                    text = sec['attributedDescription'].get('content', '')
                    # Split into lines
                    lines = [l.strip() for l in text.split('\\n') if l.strip()]
                    for l in lines:
                        print(l)
                break
    except:
        pass
"
```

## Getting Video Chapters/Timestamps

From `ytInitialData`:
```python
try:
    chapters = data['playerOverlays']['playerOverlayRenderer']['decoratedPlayerBarRenderer']['decoratedPlayerBarRenderer']['playerBar']['chapteredPlayerBarRenderer']['chapters']
    for ch in chapters:
        title = ch['chapterRenderer']['title']['simpleText']
        time_ms = ch['chapterRenderer']['timeRangeStartMillis']
        mins = time_ms // 60000
        secs = (time_ms % 60000) // 1000
        print(f'{mins:02d}:{secs:02d} - {title}')
except:
    pass
```

## Limitations

- oEmbed gives title + author only — no transcript, no full description, no comments
- The ytInitialData scrape gives **description text** but NOT captions/subtitles
- YouTube may serve different HTML to bots vs browsers; the HTML parsing approach can break if YouTube changes their page structure
- The `youtube_transcript_api` library (v1.2.4+) uses a new API class — instantiate with `YouTubeTranscriptApi()`, then call `.fetch(video_id)`:
  ```python
  from youtube_transcript_api import YouTubeTranscriptApi
  api = YouTubeTranscriptApi()
  transcript = api.fetch(video_id)  # NOT get_transcript()
  ```
  But note: most cloud VPS IPs are blocked by YouTube for this API.

## When to Use Each Approach

| Tool | Available | Content |
|------|-----------|---------|
| `youtube_transcript_api` | Only from non-cloud IPs | Full transcript text |
| `browser_navigate` + browser tools | Only when Camofox browser is running | Full page including transcript, comments |
| `curl + oEmbed` | **Always** (the fallback) | Title, author, thumbnail, basic info |
| `curl + ytInitialData scrape` | **Always** | Video description, chapters, some metadata |

**Recommendation:** Try the transcript API first. If it throws `RequestBlocked`, fall back to `curl + oEmbed` for title/author, then `curl + ytInitialData scrape` for the description.
