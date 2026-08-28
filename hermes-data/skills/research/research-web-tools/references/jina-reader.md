# Jina Reader — Web Access & Search Proxy

Jina Reader (`https://r.jina.ai/URL`) converts any web page to clean Markdown. Installed as part of Agent Reach. No auth needed.

## Why use it

- **No browser required** — bypasses JS-heavy sites that block `curl`
- **Clean Markdown output** — strips ads, nav, paywalls (where accessible)
- **Search proxy** — can read search engine results pages from DuckDuckGo Lite, Google, Bing
- **Access login-gated sites partially** — public profiles on X/Twitter, LinkedIn, Reddit work (but search results and logged-in content do not)

## Basic usage

```bash
# Read any URL as clean Markdown
curl -s "https://r.jina.ai/https://example.com/page"

# With custom headers
curl -s "https://r.jina.ai/https://example.com" -H "Accept: text/plain"
```

## Search proxy (when no `web_search` tool is available)

DuckDuckGo Lite (`lite.duckduckgo.com/lite/`) returns HTML with no JS:

```bash
# Web search
curl -s "https://r.jina.ai/https://lite.duckduckgo.com/lite/?q=site:example.com+keyword"

# Site-specific search
curl -s "https://r.jina.ai/https://lite.duckduckgo.com/lite/?q=site:github.com+NousResearch"

# Boolean search
curl -s "https://r.jina.ai/https://lite.duckduckgo.com/lite/?q=%22exact+phrase%22+OR+keyword"
```

## Reading public social profiles (no login required)

```bash
# X/Twitter profile (public posts visible)
curl -s "https://r.jina.ai/https://x.com/username"

# Single tweet / post
curl -s "https://r.jina.ai/https://x.com/username/status/123456789"

# Reddit thread
curl -s "https://r.jina.ai/https://www.reddit.com/r/subreddit/comments/xyz/"

# GitHub releases
curl -s "https://r.jina.ai/https://github.com/org/repo/releases"
```

## Limitations

| Goal | Works? | Notes |
|------|--------|-------|
| Public web pages | ✅ | Clean Markdown |
| Public Twitter profiles | ✅ | Recent posts only |
| Twitter search results | ❌ | Requires login redirect |
| Google search | ❌ | Returns 429/CAPTCHA |
| DuckDuckGo Lite | ✅ | No JS, works reliably |
| GitHub (public) | ✅ | Releases, READMEs, issues |
| Google News RSS | ✅ | Atom/RSS feeds work |
| YouTube (oEmbed info) | ✅ | Title, author, metadata |
| YouTube (full page) | ⚠️ | Mixed results |

## Pitfalls

- **Rate limited URLs** may return 429 — retry with delay or use a different source
- **Twitter search** always redirects to login — use public profile URLs instead, or configure Twitter CLI cookies (`agent-reach configure twitter-cookies`)
- **Google search** blocks Jina's IP range — use DuckDuckGo Lite or Bing instead
- Some sites detect the reader and serve truncated content — fall back to browser tools or a direct curl with user-agent
