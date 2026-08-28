# Reference Website Extraction — Absorbed into website-design-reproduction

This skill (`reference-website-extraction`) has been absorbed into `website-design-reproduction`. Both cover the same workflow: extract assets and content from a live website, then package them into a comprehensive coding agent prompt.

## Unique Content Preserved

### Cross-portal extraction (beyond Framer)

The `reference-website-extraction` skill handled websites of all platforms, not just Framer sites. Key techniques:

#### HTML asset extraction (general)
```python
import re
urls = re.findall(r'src="(https?://[^"]+\.(png|jpg|jpeg|webp|avif|svg))"', html)
# Deduplicate by base URL
```

#### Content categorization
```python
lines = [l.strip() for l in re.sub(r'<[^>]+>', '\n', clean_html).split('\n') if l.strip()]
# Headings: <60 chars → section titles
# Body copy: >60 chars → paragraph content
# Stats/numbers: metric values, prices
```

#### Design DNA extraction
- Typography (Google Fonts / @font-face)
- Colour palette (CSS custom properties)
- Layout architecture (section ordering)
- Visual style (warm/cool, premium/earthy)
- Animation patterns (GSAP, ScrollTrigger)

### Password-protected PDF statements

For extracting password-protected bank statements from Gmail (different workflow — see `gws-automation` for the bank-statement-password pattern).

### Annual vs monthly statement disambiguation
Always check subject line date range — the most recent email may be a year-end annual summary, not a monthly statement.

## Related Gmail/Drive references
- `gws-automation` skill — for extracting PDF attachments from Gmail (when bank statements are involved)

**Archived into `website-design-reproduction` on 2026-06-12.**
