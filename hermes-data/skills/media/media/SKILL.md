---
name: media
description: "Media umbrella — Spotify (play, search, queue, playlists), YouTube (transcripts to summaries/threads/blogs), GIF search (Tenor), audio spectrograms/features (mel/MFCC/chroma), and Suno-like song generation from lyrics."
umbrella: media
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Media, Spotify, YouTube, GIF, Audio, Spectrograms, Music, Song Generation]
---

# Media — Umbrella

Covers music streaming, video content extraction, GIF search, audio analysis, and AI song generation.

## Decision Tree

```
What media task?
├── Play/search/queue music on Spotify
│   └── → Spotify (references/spotify.md)
│         Play, search, queue, playlists, devices.
├── Extract/understand YouTube video content
│   └── → YouTube Content (references/youtube.md)
│         Transcripts → summaries, threads, blogs.
├── Search/download GIFs
│   └── → GIF Search (references/gif-search.md)
│         Tenor via curl + jq.
├── Analyze audio (spectrograms, MFCC, chroma)
│   └── → Songsee (references/songsee.md)
│         mel spectrogram, MFCC, chroma features.
└── Generate music/songs from lyrics
    └── → Heartmula (references/heartmula.md)
          Suno-like song generation from lyrics + tags.
```

## Sub-Skill Reference

| Skill | When to Use | Key API/Method |
|-------|-------------|---------------|
| `references/spotify.md` | Spotify playback control | spotify-cli or API |
| `references/youtube.md` | YouTube transcript → text | youtube-transcript-api |
| `references/gif-search.md` | GIF search/download | Tenor API |
| `references/songsee.md` | Audio feature analysis | librosa |
| `references/heartmula.md` | AI song generation | Suno-like prompts |

## Absorbed Skills

- `spotify` → `references/spotify.md`
- `youtube-content` → `references/youtube.md`
- `gif-search` → `references/gif-search.md`
- `songsee` → `references/songsee.md`
- `heartmula` → `references/heartmula.md`

## Quick Reference

### Spotify
```bash
spotify play "song name"
spotify search "query"
spotify queue "song"
```

### YouTube Transcript
```python
from youtube_transcript_api import YouTubeTranscriptApi
api = YouTubeTranscriptApi()
transcript = api.fetch(video_id, languages=['en'])
```

### GIF Search
```bash
curl -s "https://tenor.googleapis.com/v2/search?q=reaction" | jq .
```

## Resources

- **Spotify**: https://developer.spotify.com
- **YouTube Transcript API**: https://github.com/jdepoix/youtube-transcript-api
- **Tenor GIF**: https://tenor.com/gifapi
- **librosa**: https://librosa.org