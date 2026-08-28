# Article Filtering Patterns — Employment Generator Tracker

All raw RSS results must pass a **two-stage filter** before extraction:
1. **Exclusion check** — skip political, negative, irrelevant, and non-employment articles
2. **Positive indicator check** — must contain at least one category-relevant keyword

## Stage 1 — Exclusion Patterns

Articles matching these patterns are skipped entirely (unless they also match a strong positive employment indicator — see note at end).

### Political / dispute / negative
```
\bdispute\b, \bCauvery\b, \belection\b, \bvoter\b, \bDMK\b
\bfight\b, \brow\b, \bprotests?\b, \bagitati\b, \bcontrovers\b
\bscrap\b, \bcancel\b, \bcancelling\b, \bscrapped\b
\bpoll\s+bond\b, \bcorruption\b, \bscam\b
```

### Audit / investigation / irregularities
```
\bCAG\b, \baudit\b, \birregularities\b, \bmisappropriation\b, \bembezzlement\b
```

### Crime / accident
```
\bmurder\b, \baccident\b, \bcollision\b, \bcriminal\b, \barrest\b, \bencounter\b, \bviolence\b
```

### Weather / disaster
```
\bflood\b, \bdrought\b, \bcyclone\b, \bearthquake\b
```

### Religion
```
\btemple\b, \bmosque\b, \bprayer\b, \breligious\b, \bchurch\b
```

### Education / sports (not employment-related)
```
\badmission\b, \bexam\b, \bresult\b, \bdegree\b, \bsyllabus\b
\bcricket\b, \bIPL\b, \bmatch\b, \btournament\b
```

### Opinion / editorial
```
\bpolitical\s+analysis\b, \bopinion\b, \beditorial\b, \bcolumn\b
```

### Health (not hospital expansions)
```
\bhospital\b(?!\s+expansion|\s+new), \bdisease\b, \bpandemic\b
```

## Stage 2 — Positive Indicators

Articles must also contain at least one positive indicator for their category.

### Employment positive indicators
```
\bnew\s+(factory|plant|manufacturing|facility|campus|office|unit)
\b(expansion|inaugurat|opened|launch|commission)
\binvestment\b, \bGCC\b, \bglobal capability centre\b
\bcreate\s+\d+, \bemploy\s+\d+, \bjob\b, \bworkforce\b
\bIT park\b, \btech park\b, \bSEZ\b
\bset\s+up\b, \bestablish
\bback\s+office\b, \bBPO\b
```

### Infrastructure positive indicators
```
\bnew\s+(road|highway|bridge|flyover|metro|railway|rail)
\b(inaugurat|opened|launch|commission|awarded|approved)
\bexpansions?\b, \bextension\b
\bfreight\s+corridor\b, \blogistics\s+(park|hub)
\bindustrial\s+corridor\b, \bport\b, \bairport\b
\bpower\s+(plant|project|station)\b, \brenewable\s+energy\b
\bwater\s+(project|supply|treatment)\b
```

### Policy positive indicators
```
\b(industrial|investment)\s+policy\b, \bSEZ\b
\benvironmental\s+(clearance|approval)\b
\bpollution\s+(board|consent|clearance)\b
\bKIADB\b, \bTIDCO\b, \bGuidance\b
\bland\s+acquisition\b, \bincentive\b, \bsubsidy\b
\b(approved|notified|notificatio)\b
```

## Important exception — exclusion vs positive indicator conflict

When an article matches BOTH an exclusion pattern AND a strong positive indicator (e.g., "Tamil Nadu may scrap Rs 2K-crore ECR elevated corridor project" — matches "scrap" exclusion but also "elevated corridor" positive), **defer to positive indicator** if the positive match is more specific to the category.

Rule of thumb: if the article is clearly about an infrastructure project (even if reporting its cancellation or controversy), it's not generating employment — exclude it. If the article has strong employment/investment keywords alongside marginal political mentions, keep it.

## Geography matching pattern

Simple substring match against the geography list in `references/employment-generator-geographies.md`. Key locations to match:

| Mention | Tag as |
|---------|--------|
| "Karnataka" | Karnataka (fallback) |
| "Bangalore" / "Bengaluru" | Map to sub-region (North/South/East) |
| "Electronic City" | Bangalore South |
| "Whitefield" | Bangalore East |
| "Devanahalli" | Bangalore North |
| "Hosur" | Krishnagiri District, TN |
| "Sriperumbudur" | Chennai Periphery |
| "Hindupur" | Andhra Pradesh Border |

If a geography mention is found anywhere in the title+description, the article passes the geography gate. No advanced NER needed.

## Article dedup across queries (same-run)

The same article often appears in multiple RSS queries. Dedup by:
1. **Link** — exact RSS link match (most reliable)
2. **Normalized title** — strip all non-alphanumeric, lowercase, take first 60 chars. If two articles have the same normalized title, they're the same story.

This prevents the same story from being counted as 2-3 entries when it matches multiple queries.
