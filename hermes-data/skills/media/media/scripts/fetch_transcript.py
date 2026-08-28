#!/usr/bin/env python3
"""Fetch YouTube transcript and output as JSON, plain text, or with timestamps.

Usage:
    python3 scripts/fetch_transcript.py "https://youtube.com/watch?v=VIDEO_ID"
    python3 scripts/fetch_transcript.py "URL" --text-only
    python3 scripts/fetch_transcript.py "URL" --timestamps
    python3 scripts/fetch_transcript.py "URL" --language en,hi
"""

import sys, json, re, argparse
from youtube_transcript_api import YouTubeTranscriptApi

def extract_video_id(url: str) -> str:
    patterns = [
        r'(?:v=|/v/|youtu\.be/|/embed/|/shorts/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$',
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    raise ValueError(f"Cannot extract video ID from: {url}")

def main():
    parser = argparse.ArgumentParser(description='Fetch YouTube transcript')
    parser.add_argument('url', help='YouTube URL or video ID')
    parser.add_argument('--text-only', action='store_true', help='Output plain text only')
    parser.add_argument('--timestamps', action='store_true', help='Include timestamps')
    parser.add_argument('--language', default='en', help='Language code(s), comma-separated')
    args = parser.parse_args()

    video_id = extract_video_id(args.url)
    languages = [l.strip() for l in args.language.split(',')]

    api = YouTubeTranscriptApi()
    transcript = api.fetch(video_id, languages=languages)

    result = []
    for entry in transcript:
        result.append({
            'start': entry.start,
            'duration': entry.duration,
            'text': entry.text,
        })

    if args.text_only:
        print(' '.join(e['text'] for e in result))
    elif args.timestamps:
        for e in result:
            mins = int(e['start'] // 60)
            secs = int(e['start'] % 60)
            print(f"{mins:02d}:{secs:02d}  {e['text']}")
    else:
        print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
