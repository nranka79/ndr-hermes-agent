# WhatsApp Lead Outreach Workflow

After extracting and deduping leads from real estate portals, the next step is outreach. This reference covers:

1. Generating WhatsApp deep links with pre-filled messages
2. Building a tracking dashboard in the lead sheet
3. Bulk messaging safety and best practices
4. Structured marketing message creation (fresh leads / immediate response)
5. Image sharing alongside wa.me links

## 0. Fresh Lead — Immediate Response Pattern

When a lead comes in **via voice or text** (not batch-extracted from Gmail), the workflow is:

```
User shares: Name, Phone, Budget, Requirement
   ↓
Capture details → Identify project (e.g. "Ranka Udaya" for Sarjapur plots)
   ↓
Build structured message with:
  - Greeting + acknowledge enquiry
  - Project name + property type
  - 2-3 key selling points (location, investment upside, development)
  - Digital tour link + maps link
  - CTA (site visit / call back)
   ↓
Generate wa.me link with encoded message
   ↓
Tell user: tap link → WhatsApp opens → send text
            then manually send image(s) as separate photo(s)
```

## 1. WhatsApp Deep Link Generation

Use `wa.me` links with pre-filled messages for each lead. Format:

```
https://wa.me/91{phone}?text={urlencoded_message}
```

### Message encoding

```python
import urllib.parse
message = "Thank you for your enquiry. For Ranka Udaya."
encoded_msg = urllib.parse.quote(message, safe='')  # safe='' encodes ALL chars including parens
link = f"https://wa.me/917760125000?text={encoded_msg}"
```

### CRITICAL: Encode ALL special characters including parentheses

The message text often contains `(` and `)` (e.g. "Next to Exide factory (3,000+ employees)"). If these aren't encoded, they break markdown link syntax when the wa.me URL is wrapped in `[text](url)` format:

- ❌ `[Send](https://wa.me/...?text=...Exide%20factory%20(3,000%2B%20employees)...)` — the `)` after `employees` closes the markdown link early, truncating the rest of the message
- ✅ `urllib.parse.quote(msg, safe='')` encodes `(` → `%28` and `)` → `%29`, so the full URL survives markdown rendering

**Always use `safe=''` when encoding wa.me message text.** The default (`safe='/')` leaves `()~._-` unencoded, which causes the truncation bug above.

**Alternative delivery: plain text / code block.** If markdown link truncation persists, present the wa.me URL as a plain code block instead of a clickable link. The user can copy-paste it into their phone browser.

### Personalization

Add the lead's name to reduce spam flagging:

```python
message = f"Hi {name}, thank you for your enquiry. For Ranka Udaya."
```

### Full generation pattern

```python
import urllib.parse, re

message = "Thank you for your enquiry. For Ranka Udaya."
encoded = urllib.parse.quote(message, safe='')

links = []
for lead in leads:
    phone = lead['phone']
    if phone and re.match(r'^\d{10}$', phone):
        wa_link = f"https://wa.me/91{phone}?text={encoded}"
        links.append({"name": lead['name'], "phone": phone, "wa_link": wa_link})
```

### Output formats for Bharat

**Option A: Text file with all links (wa.me links file)**
```
/data/hermes/users/sales1.blr/outbound/WhatsApp_Lead_Messages_<Project>.txt
```

**Option B: Add WhatsApp column to the Google Sheet**
Use Sheets API to update column I (or J after tracking columns) with HYPERLINK formulas:
```
=HYPERLINK("https://wa.me/91{phone}?text={encoded}", "📱 Chat with {name}")
```

### Bharat's phone number
- Bharat's WhatsApp number: 9900029200 (his personal/corp line)
- This is the number that will appear as sender when he taps a wa.me link on his phone

## 2. Tracking Dashboard Columns

After the lead sheet is created, add tracking columns to the Google Sheet using the Sheets API:

| Column | Header | Type | Values |
|--------|--------|------|--------|
| J | WhatsApp Sent? | Dropdown | ✅ Sent, ⏳ Pending, — Skipped |
| K | Date Sent | Free text | Manual entry |
| L | Response? | Dropdown | 👍 Replied, 👁️ Seen, ❌ No response, 📞 Callback scheduled |
| M | Notes | Free text | Any follow-up notes |

### Dropdown validation via Sheets API

```python
from tools.gws_auth import build_service
sheets = build_service("sheets", "v4")

requests = [
    {
        "setDataValidation": {
            "range": {"sheetId": 0, "startRowIndex": 4, "endRowIndex": 64,
                      "startColumnIndex": 9, "endColumnIndex": 10},
            "rule": {
                "condition": {"type": "ONE_OF_LIST", "values": [
                    {"userEnteredValue": "✅ Sent"},
                    {"userEnteredValue": "⏳ Pending"},
                    {"userEnteredValue": "— Skipped"},
                ]},
                "showCustomUi": True
            }
        }
    },
    {
        "setDataValidation": {
            "range": {"sheetId": 0, "startRowIndex": 4, "endRowIndex": 64,
                      "startColumnIndex": 11, "endColumnIndex": 12},
            "rule": {
                "condition": {"type": "ONE_OF_LIST", "values": [
                    {"userEnteredValue": "👍 Replied"},
                    {"userEnteredValue": "👁️ Seen"},
                    {"userEnteredValue": "❌ No response"},
                    {"userEnteredValue": "📞 Callback scheduled"},
                ]},
                "showCustomUi": True
            }
        }
    },
]
sheets.spreadsheets().batchUpdate(spreadsheetId=SHEET_ID, body={"requests": requests}).execute()
```

### Header formatting

Match existing sheet style (blue background, white bold text, centered):
```python
{
    "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": 3, "endRowIndex": 4,
                  "startColumnIndex": 9, "endColumnIndex": 13},
        "cell": {
            "userEnteredFormat": {
                "backgroundColor": {"red": 0.18, "green": 0.46, "blue": 0.71},
                "textFormat": {"bold": True, "fontSize": 11,
                               "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                "horizontalAlignment": "CENTER",
            }
        },
        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
    }
}
```

## 3. Bulk Messaging Safety

### WhatsApp rate limit risks

| Method | Safe daily volume | Risk |
|--------|------------------|------|
| Manual wa.me links (tap each) | ~20-30/day | Low — natural human pace |
| Broadcast list (1 msg → many) | Up to 256 per list | Medium — if recipients report, can trigger 24-48hr ban |
| WhatsApp Business API | Unlimited | Requires BSP setup (WATI, Interakt, etc.) |

### Best practices for 50+ leads

1. **Space it out** — 5-10 messages per hour, not all at once
2. **Use Broadcast List** — Create a broadcast list in WhatsApp, add leads, send once. Each gets a DM (not a group)
3. **Personalize** — Add lead's name to message. Reduces spam flags significantly
4. **Avoid late hours** — Don't send after 9 PM (triggers complaints + spam flags)
5. **Track responses** — Use the tracking columns to log who replied, who needs follow-up

### Follow-up sequence template

| Step | Timing | Message |
|------|--------|---------|
| 1. Initial touch | Day 1 | "Thank you for your enquiry. For [Project]." |
| 2. Brochure follow-up | Day 2 | "Hi [Name], here's the [Project] brochure — [details]. Would you like to schedule a site visit?" |
| 3. Call to action | Day 4 | "Pre-launch offer on select plots at [Project]. Limited inventory. Share the price list?" |
| 4. Site visit invite | Day 7 | "Visit the site 10 AM - 5 PM any day. Let me know what works." |

## 4. Project Info Kit Creation

When the user wants to send project information to leads, create a **Leads Kit** on Drive:

### Contents

- **Brochure** (PDF from Marketing Materials folder)
- **Master Plan** (PDF)
- **RERA Order** (PDF)
- **Project Profile** (HTML page)
- **Photos** (folder)
- **Leads Tracker** (Google Sheet link)

### Google Doc template

Create a Google Doc in the Marketing Materials folder with:
1. Project overview (location, plot sizes, starting price, developer)
2. Quick links to all materials
3. WhatsApp message templates (initial, brochure follow-up, CTA, site visit)
4. Contact info (Bharat's number + email)

### Drive folder location

For Ranka Udaya: `Ranka Udaya Marketing Materials` folder (ID: `1Exrjm_3UKE_MfvH1yq2wYuSMICfFeNI2`)

## 5. Structured Marketing Message — Fresh Lead Response

When the user passes a lead via voice/text (not from a batch extraction), build a persuasive message on the fly incorporating the project's key selling points. The pattern:

### Message structure

```
Hi {Name}, thanks for your enquiry about {property type} in {location}.

I'd like to introduce you to {Project Name} — {brief descriptor}.

Here's why this stands out:

🌳 {Selling Point 1 — location, greens, surroundings}
🏭 {Selling Point 2 — investment upside, rental demand}
🏗️ {Selling Point 3 — area development, infrastructure}

📍 Location: {maps link}
🚁 Digital Tour: {digital tour link}

{Property type} available from competitive budgets. Would you like a site visit?

Best,
{Bharat Hawaldar | DRAAS Realty}
```

### Project-specific assets

Each project has pre-baked selling points and links stored in a `references/<project>-marketing-kit.md` file. Load that and use the:
- Selling points verbatim or adapt to the lead
- Digital tour link (housing.com drone view)
- Maps location link
- Any uploaded image (user shares during the session)

### Image handling

- wa.me links **cannot carry images** — only URL-encoded text
- After generating the wa.me link, tell the user:
  > "Send the text message via the link above, then send the image as a separate photo from your gallery"
- If the user uploaded an image during the session, reference it as a file path: the user can find it in their Telegram chat and forward it

### Per-lead personalization

For each new lead:
1. Replace `{Name}` and `{Phone}` in the template
2. Re-generate the wa.me link with the new name
3. Keep selling points and links the same (consistent pitch)
4. Optionally adjust emphasis: investment-focused leads get more rental-demand detail; end-user leads get more location/greens detail

## 5. Cron-based Follow-up Reminder

Set up a recurring cron job to remind Bharat to follow up on leads. **Timezone matters** — Bharat is in IST (UTC+5:30), so 10 AM IST = 4:30 AM UTC.

```python
# 10 AM IST = 4:30 AM UTC
cronjob(action='create',
        schedule='30 4 * * 0,1,2',  # Sun/Mon/Tue at 4:30 UTC = 10 AM IST
        prompt='Check the Ranka Udaya leads tracking sheet. Count how many leads show "⏳ Pending" in WhatsApp Sent column. If >5, send a summary to Bharat with the names and numbers of leads pending. Include a reminder to follow up on leads marked "❌ No response" that are >3 days old.',
        name='Ranka Udaya leads follow-up reminder')
```

**Timezone conversion** (cron runs on UTC):
| IST | UTC | Cron expression |
|-----|-----|----------------|
| 10:00 AM | 4:30 AM | `30 4 * * *` |
| 11:00 AM | 5:30 AM | `30 5 * * *` |
| 9:00 AM | 3:30 AM | `30 3 * * *` |

**Day-of-week convention:** Use `0` for Sunday, `1` for Monday, `2` for Tuesday (standard cron weekday numbering). Bharat's preferred reminder pattern (from Jun 2026): Sun, Mon, Tue at 10 AM IST = `30 4 * * 0,1,2`.

## Common Pitfalls

### 1. wa.me link opens browser, not WhatsApp app
On desktop, wa.me links open the web browser first. On mobile, they open WhatsApp directly. Tell the user to open the links on their phone.

### 2. Message truncation in wa.me links — parentheses break markdown links

**Two separate truncation causes:**

**(a) Ampersand (`&`):** WhatsApp webview truncates messages containing `&`. Use full-width ampersand `＆` (U+FF06) encoded as `%EF%BD%86` instead of `%26`. For most lead outreach messages this isn't an issue since standard messages don't contain `&`.

**(b) Parentheses (`(` and `)` ) — markdown link killer:** When the wa.me URL is wrapped in markdown `[text](url)` format, any `)` in the URL acts as the closing delimiter of the markdown link, truncating everything after it. Example trigger: "Exide factory (3,000+ employees)" — the `)` after `employees` closes the markdown link early.

**Fix:** Always use `urllib.parse.quote(msg, safe='')` — the `safe=''` argument forces encoding of parentheses (`(` → `%28`, `)` → `%29`) along with other special chars. Never rely on the default `safe='/'` for wa.me messages.

**Bharat's expectation (critical):** He will notice and call it out immediately if the message is incomplete after tapping the link ("entire message is not covered", "you messing out after greenery"). Verify the full message renders before presenting the link.

### 3. Self-lead filtering
Bharat's own phone (9900029200) and email (sales1.blr@draas.com, khanbt@gmail.com) can appear as leads in MagicBricks data. Filter these out before generating outreach links.

### 4. User preference: Drive root upload
Bharat explicitly said "you can add it to my drive somewhere" — meaning upload to Drive root, not to a specific project folder. If a shared folder upload fails with 403, fall back to root immediately. Do not try another shared folder.

### 5. Images cannot be sent via wa.me links

wa.me links only carry URL-encoded text — no image/attachment support. After the user taps a wa.me link and sends the text message, they MUST manually send the image(s) as a separate WhatsApp photo from their phone gallery. Always instruct: "Send the text via the link → then send the image as a photo separately."

**⚠️ User correction pattern (Bharat, Jul 2026):** When you just say "send the image separately", Bharat pushes back: *"But I don't see the image being connected here. I want you to connect with image as well."* He wants the image to feel **part of the solution**, not an afterthought. The fix is a self-contained HTML page that embeds the image alongside the link generator.

#### HTML Tool Approach — "Connect the image"

Build a single HTML page with the marketing image embedded in it, a phone number input, and the wa.me link generator. The user opens it on their phone, sees the image (can long-press to save), enters the number, and taps to open WhatsApp.

**When to use:**
- User expects a seamless image+text combo ("connect with image")
- User repeatedly sends phone numbers one-by-one (batch mode)
- The project has a single hero image for outreach

**How to build:**

```python
# 1. Copy the marketing image to the same directory as the HTML
import shutil
shutil.copy2("/path/to/image.jpg", "/opt/data/project-welcome.jpg")

# 2. Fill in the template at:
#    real-estate-leads-tracking/templates/wa-link-sender.html
#    Replace {{PROJECT_NAME}}, {{IMAGE_FILENAME}}, {{MESSAGE_TEXT}}
#    with the project-specific values.

# 3. Present both files to the user:
#    - The HTML file (they open in mobile browser)
#    - A direct wa.me link for the current number they're working on
```

**Template: `templates/wa-link-sender.html`**

A self-contained HTML page with:
- **Header** — Project name + "WhatsApp welcome message + image sender"
- **Embedded image** — The marketing image displayed full-width with a "Long-press to save" badge
- **Phone input** — +91 country code pre-filled, 10-digit number input
- **Instruction badge** — "Tap green button → WhatsApp opens → attach image from gallery → send"
- **Message preview** — The full outreach message displayed in a scrollable box
- **Send button** — Green WhatsApp button, disabled until valid 10-digit number entered
- **History** — Sent numbers stored in localStorage with timestamps, clearable

**Workflow for the user:**
1. Open the HTML file on their phone (Chrome/Safari)
2. Long-press the image → Save to Phone
3. Enter client's 10-digit number
4. Tap "Send via WhatsApp"
5. WhatsApp opens with message pre-filled
6. Tap 📎 Attach → Gallery → select the saved image → Send ✈️

**Access the image separately too:** Send the image file itself as a MEDIA: attachment in the Telegram response so the user has it saved there as well.

**Key lesson:** The HTML page makes the image feel "connected" to the workflow because it's right there — not a separate file they have to dig up. The user perception shift is significant.

### 6. Maps link may show a different project name
Google Maps pins may use a different name than the marketing name (e.g. Ranka Udaya's location appears as "70 Estate" on Maps). Present the link as the project location anyway — don't let the Maps label confuse the message. The user will correct this if needed.
