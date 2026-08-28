#!/usr/bin/env python3
"""
scrape_docs.py — fetch + strip-tag + keyword-sweep a vendor's marketing & dev pages.

Drop-in helper for the vendor-product-research skill. Use when browser_navigate
fails (e.g. Camofox down) or when you only need documentation-grade text
(marketing pages, developer docs, OpenAPI/Redocly HTML).

Usage:
    python3 scrape_docs.py <out_dir> <url1> [url2 ...] [--keys k1,k2,...]

Example:
    python3 scrape_docs.py /tmp/td \
        https://www.truein.com/ \
        https://www.truein.com/integrations \
        https://www.truein.com/manpower-staffing-industry-attendance-software \
        --keys device,register,enroll,template,cloud,sync,multiple,kiosk,API,CRM,webhook,FTP,push,offline

For each URL the script:
  1. fetches HTML with a real browser User-Agent
  2. writes the raw HTML to <out_dir>/<safe_url>.html
  3. strips <script>, <style>, all tags, collapses whitespace
  4. prints the first 3000 chars of clean text
  5. for each keyword, prints one context snippet (±150/-200 chars around the match)

No LLM calls. Output is plain text ready to drop into a vendor report.
"""
import os
import re
import sys
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
DEFAULT_KEYS = "device,register,enroll,template,cloud,sync,multiple,single,Kiosk,kiosk,face,server,API,CRM,webhook,FTP,push,offline,OAuth,token,client_credentials,Subscription-key,access_key_id,secret_access_key"


def safe_name(url: str) -> str:
    name = re.sub(r"^https?://", "", url)
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    return name[:180]


def fetch(url: str, out_dir: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read()
    # try utf-8 then fall back
    try:
        html = raw.decode("utf-8")
    except UnicodeDecodeError:
        html = raw.decode("latin-1", errors="replace")
    path = os.path.join(out_dir, safe_name(url) + ".html")
    with open(path, "w") as f:
        f.write(html)
    return html


def clean(html: str) -> str:
    t = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    t = re.sub(r"<style[^>]*>.*?</style>", "", t, flags=re.DOTALL)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def sweep(text: str, keys):
    for k in keys:
        for m in re.finditer(rf"\b{re.escape(k)}\b", text, re.IGNORECASE):
            s = max(0, m.start() - 150)
            e = min(len(text), m.end() + 200)
            yield k, text[s:e]


def main(argv):
    if len(argv) < 3:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    out_dir = argv[1]
    os.makedirs(out_dir, exist_ok=True)
    args = list(argv[2:])
    keys = DEFAULT_KEYS.split(",")
    if "--keys" in args:
        i = args.index("--keys")
        keys = [k.strip() for k in args[i + 1].split(",") if k.strip()]
        args = args[:i] + args[i + 2:]
    for url in args:
        try:
            html = fetch(url, out_dir)
        except Exception as ex:
            print(f"FAIL  {url}  {ex}", file=sys.stderr)
            continue
        text = clean(html)
        print(f"\n========== {url}  ({len(text)} chars) ==========")
        print(text[:3000])
        print(f"\n----- keyword sweep ({', '.join(keys)}) -----")
        seen = set()
        for k, snip in sweep(text, keys):
            tag = (k, snip[:80])
            if tag in seen:
                continue
            seen.add(tag)
            print(f"--- [{k}] ---")
            print(snip)
            print()
        print()


if __name__ == "__main__":
    main(sys.argv)
