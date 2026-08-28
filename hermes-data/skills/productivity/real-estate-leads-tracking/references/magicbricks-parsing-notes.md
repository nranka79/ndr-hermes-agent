# MagicBricks Lead Parsing — Field Extraction Notes

Verified per-field patterns from June 2026 lead extraction (88 leads from DRA Ranka Udaya campaign).

## Subject line

Formats observed:

- `Buyer has contacted you on MagicBricks for - <Property Type> for sale in <Location>` (earlier)
- `Hot Lead - Buyer has contacted you on MagicBricks for - <Property Type> for sale in <Location>` (as of June 2026)

The "Hot Lead -" prefix is a recent MagicBricks addition. Both formats are genuine leads.

Examples observed:
- `Buyer has contacted you on MagicBricks for - Residential Plot for sale in Sarjapura`
- `Buyer has contacted you on MagicBricks for - Residential Plot for sale in Bagalur Sarjapur Road`
- `Buyer has contacted you on MagicBricks for - Residential Plot for sale in Bagalur`
- `Buyer has contacted you on MagicBricks for - Residential Plot for sale in Bangalore`

```python
import re
m = re.search(r"for - (.+)$", subject)
property_type = m.group(1).strip() if m else subject
```

## Buyer email

Email is the most stable identifier. Format: standard RFC email. MagicBricks embeds it in the HTML body after "Email:" in a bold span.

**⚠️ MagicBricks sends HTML-only emails** — there is no `text/plain` alternative. You must extract the HTML body from the Gmail message first:

```python
def get_html_body(meta):
    """Extract HTML body from Gmail message parts recursively."""
    def _extract(payload):
        if payload.get('mimeType') == 'text/html' and payload['body'].get('data'):
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='replace')
        if 'parts' in payload:
            for p in payload['parts']:
                result = _extract(p)
                if result:
                    return result
        return ''
    return _extract(meta['payload'])
```

**HTML-specific regex (preferred):**
```python
m_email = re.search(r"Email:.*?font-weight:bold[^>]*>([^<]+@[^<]+)", html, re.DOTALL)
email = m_email.group(1).strip() if m_email else ''
```

**Fallback (catch stray plaintext emails):**
```python
m_email = re.search(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", html)
```

## Buyer phone

10-digit Indian mobile. Appears in the HTML body after "Mobile:" in a bold span. Always extract the last 10 digits.

**HTML-specific regex (preferred — extracts from the labelled "Mobile:" cell):**
```python
m_phone = re.search(r"Mobile:.*?font-weight:bold[^>]*>\s*(\d{10})", html, re.DOTALL)
phone = m_phone.group(1).strip() if m_phone else ''
```

**⚠️ Nested-span variant (verified Aug 2026):** Some MagicBricks emails wrap the phone in an *extra* span before the digits, with a `(Verified)` suffix:
```html
<span style="color:#333333; font-weight:bold"> <span style="text-decoration:underline;">7411152429</span> <span style="font-weight:normal">(Verified)</span></span>
```
The strict regex above returns EMPTY for these (there is no `font-weight:bold>` immediately before the digits). Fix — use the **loose label-anchored pattern** as the primary for phone:

```python
# PRIMARY (verified 185/185 leads, Aug 2026 — catches both plain and nested-span variants)
m_phone = re.search(r"Mobile:.*?(\d{10})", html, re.DOTALL)
phone = m_phone.group(1).strip() if m_phone else ''
```

Same for email — the nested span can sit between `Email:` and the address, so anchor on the label and take the first RFC-style address after it:

```python
# PRIMARY (verified Aug 2026)
m_email = re.search(r"Email:.*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", html, re.DOTALL)
email = m_email.group(1).strip() if m_email else ''
```

⚠️ The loose phone pattern is safe BECAUSE it anchors on the `Mobile:` label — it will not accidentally match the property owner's phone in the footer. Only the unlabelled fallback regex risks that.

**Fallback (for any plaintext context):**
```python
m_phone = re.search(r"(?:\+91[\s-]?)?(\d{10})", html.replace(" ", ""))
phone = m_phone.group(1) if m_phone else ''
```

⚠️ MagicBricks also includes the **property owner's own phone** in the email footer (e.g. `9900029200` for Bharat). The HTML regex `Mobile:.*?(\d{10})` only matches the **buyer's mobile** because it anchors on the "Mobile:" label. The fallback regex may catch the owner's number too — filter via SELF_LEAD_BLOCKLIST.

## Buyer name

**✅ Present in HTML body — extract from "Sender's Name:"**

Contrary to earlier claims, MagicBricks *does* include the buyer's name in the email body. The name is in an HTML table cell labelled "Sender's Name:" followed by a `<span style="font-weight:bold; color:#333333;">Name</span>`.

The old approach (strip HTML → regex plaintext) missed the name because it appears as labelled text within a table structure, not as free text. **You must parse the HTML directly.**

```python
import re
m_name = re.search(r"Sender's Name:.*?font-weight:bold[^>]*>([^<]+)", html, re.DOTALL)
name = m_name.group(1).strip() if m_name else ''
```

Observed names from June 2026 extraction (29 leads, 5–14 Jun): Neha, karthi, Satish Battula, varun goel, Keshava, Ambreen, prathima, Priya K, Chitra, Praveen, Subbu, Eshwar Birur, Kamal, Mnatarajan, Ramamurthy C, Kirankant Sahu, TARA, Aman, Ela, Poornima.

## Project (from URL in body)

The email body usually contains a MagicBricks property URL like:
- `https://www.magicbricks.com/propertyDetails/...-in-sarjapura-bangalore`
- `https://www.magicbricks.com/owner's-property/...`

Extracting the project from the URL is unreliable. Better to use the **subject line's location** (`Sarjapura`, `Bagalur Sarjapur Road`, `Bagalur`, `Bangalore`) and cross-reference with the user's active project list.

## Date

`Date:` header follows RFC 2822:
```
Wed, 27 May 2026 13:30:18 +0530
```

Use `email.utils.parsedate_to_datetime` for parsing — handles all locales:

```python
from email.utils import parsedate_to_datetime
d = parsedate_to_datetime(date_header)
d_str = d.strftime("%d %b %H:%M")  # for display
```

## Lead ID

MagicBricks sometimes includes a `Lead ID` in the body, but it's inconsistent. Don't rely on it as a unique key — the email is the better key.

## Spotted patterns to filter

These are NOT real leads — filter them before delivering:

- **`khanbt@gmail.com` + phone `9900029200`** — matches Bharat's own sales number. Test/internal lead. Filter with a known-buyer blocklist.
- **`aaaa@gmail.com`** + random phone — placeholder email. Definitely spam.
- **`+91XXXXXXXXXX` phone but `?` email** — sometimes the email parsing fails. Fall back to phone as dedup key.

## Property ID mapping

The Property ID (extracted from `Property, ID XXXXXXX` in the HTML body) maps to specific MagicBricks listings. Observed June 2026:

| ID | Location | Count in 10 days |
|---|---|---|
| 84675109 | Sarjapura (Residential Plot) | 15+ |
| 84608849 | Bagalur Sarjapur Road | 8 |
| 84674513 | Bagalur | 3 |
| 84675709 | Bagalur | 1 |
| 84837979 | Bagalur | 1 |
| 84653835 | Bangalore (generic) | 3 |

Same buyer inquiring about multiple IDs = interested in multiple locations, not a duplicate. Same buyer + same ID within 48h = likely duplicate.

## "Hot Lead -" subject prefix

As of June 2026, some MagicBricks lead emails now carry a **"Hot Lead -"** prefix before the standard subject:

- `Hot Lead - Buyer has contacted you on MagicBricks for - …`
- `Buyer has contacted you on MagicBricks for - …` (no prefix)

Both are genuine leads. Filter by substring `Buyer has contacted you` to catch both:

```python
if 'Buyer has contacted you' in subject:
    prop_type = subject.replace('Hot Lead - ', '').replace('Buyer has contacted you on Magicbricks for - ', '').strip()
```

## Sample deduped output (excerpt)

```
#   Date          Email                          Phone       Property
1   31 May 21:50  ratnabyalihal@gmail.com        7760125000  Residential Plot for sale in Sarjapura
2   31 May 11:34  nagendra.sastry@yahoo.com      9900575551  Residential Plot for sale in Sarjapura
3   31 May 00:46  shrisanth@gmail.com            9916492782  Residential Plot for sale in Sarjapura
4   30 May 20:38  mahisap2020@gmail.com          9886919320  Residential Plot for sale in Sarjapura
```

## Common dedup outcomes

From 88 raw MagicBricks leads in 30 days → 57 unique by email → ~50-55 after spam filter and Bharat's own number removed.

Same buyer often submits 2-3 inquiries for different properties (Sarjapura + Bagalur + Sarjapur Road) — these are NOT duplicates, they're the same buyer interested in multiple locations. The "unique by email" count is the meaningful one.
