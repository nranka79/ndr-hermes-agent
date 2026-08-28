# Indian Legal Case Research

**When to use this:** The user asks you to research a specific Indian court case or find case numbers, judgments, or news about a legal proceeding — typically involving real estate, FAR/FSI, property disputes, or regulatory matters in Karnataka/Bangalore courts.

## Key Sources (Free / No API Key)

| Source | URL | What It Has | Search Tips |
|--------|-----|-------------|-------------|
| **CDJ Law Journal** | https://cdjlawjournal.com/ | Full text of High Court judgments with case numbers, parties, legal provisions cited | Use `view_judgment1.php?id=<id>` if you have the judgment ID |
| **Karnataka HC Judgment Portal** | https://judiciary.karnataka.gov.in/ | PDFs of Karnataka High Court orders and judgments | Direct URL pattern: `/common_folder/judgment//<Case%20Name>.pdf` |
| **Google News RSS** | `https://news.google.com/rss/search?q=<query>&hl=en-IN&gl=IN&ceid=IN:en` | News articles about the case | Add `&tbm=nws` for news-only; use time filters for recent orders |
| **eCourt India** | https://services.ecourts.gov.in/ | Case status, cause lists, orders by case number | Requires knowing the case number first |
| **DuckDuckGo HTML** | `https://html.duckduckgo.com/html/?q=<query>` | Search results without JS | Works when JS-heavy sites (Google) block scraping |
| **LiveLaw / Bar & Bench** | https://www.livelaw.in/, https://www.barandbench.com/ | Legal news, judgment summaries, case analysis | Search by case topic or judge name |
| **LinkedIn** | https://www.linkedin.com/ | Industry commentary and case summaries shared by professionals | Search for case name + "linkedin" to find posts |

## Finding Case Numbers

When the user describes a case (e.g. "Premium FAR case in Karnataka High Court") but doesn't have the case number:

1. **Search legal news first** — CDJ Law Journal, LiveLaw, Bar & Bench often publish judgment summaries with case numbers embedded
2. **Search Google News RSS** with key terms (judge name + subject matter):
   ```
   https://news.google.com/rss/search?q=%22M.I.+Arun%22+%22Premium+FAR%22&hl=en-IN&gl=IN&ceid=IN:en
   ```
3. **Look for writ petition / writ appeal numbers** in the judgment text — they appear as:
   - `W.P. No. XXXXX/2025` (Writ Petition)
   - `W.A. No. XXXX/2025` (Writ Appeal — Division Bench)
   - `SLP (C) No. XXXXX/2026` (Supreme Court Special Leave Petition)
4. **Cross-reference** the case number across multiple sources (CDJ, news articles, LinkedIn) to confirm accuracy

## Case Number Naming Convention (Karnataka High Court)

| Abbreviation | Full Form | Bench |
|-------------|-----------|-------|
| **W.P.** | Writ Petition | Single Judge (original jurisdiction) |
| **W.A.** | Writ Appeal | Division Bench (appeal from single judge) |
| **SLP (C)** | Special Leave Petition (Civil) | Supreme Court |
| **C.A.** | Civil Appeal | Supreme Court |
| **CRM** | Criminal Petition | Single Judge |

## Worked Example — Premium FAR Case (June 2026)

**User's description:** "Case about Premium FAR in Bangalore, went to Supreme Court which directed it to a double bench of the High Court, the double bench dismissed the appeal yesterday"

**Research steps taken:**
1. Searched Google News RSS for `"Premium FAR" Karnataka` → found articles about single judge order
2. Searched CDJ Law Journal → found full judgment text with case numbers:
   - **W.P. No. 11201/2025** (Writ Petition No. 11201 of 2025)
   - **W.P. No. 6347/2025** (Writ Petition No. 6347 of 2025)
3. Searched Karnataka HC judgment portal for writ appeal numbers → found **WA 1983 of 2025**
4. Searched Google News for division bench order → unable to find specific news article (order was too recent — day after issuance)

**Key lesson for recent orders:** When a case is decided on the same day or the day before the user asks, it may not yet appear in news articles. Check:
- LinkedIn posts from legal professionals involved
- Direct petition on the High Court's cause list / judgment website
- Real estate industry WhatsApp groups / newsletters (user may have received it there)

## Common Indian Legal Research Pitfalls

### Google / Bing block scraping
Both Google and Bing news pages use heavy JavaScript rendering. Prefer:
- DuckDuckGo HTML search (`html.duckduckgo.com/html/?q=...`)
- Google News RSS feed (`news.google.com/rss/search?q=...`)
- Direct site search on specific news portals

### Judgment PDFs need exact URLs
The Karnataka HC judgment portal serves PDFs from predictable URLs but filenames are complex. If you find a URL once, save it — re-finding the same PDF is hard without the exact link.

### Case numbers differ between benches
A single judge W.P. number and its Division Bench W.A. number are completely different — you cannot derive one from the other. To find the appeal number, search for the outcome of the appeal (e.g. "Writ Appeal against W.P. 11201/2025") or look for the appeal in news articles about the higher court's decision.
