# Sales Inventory Coordination — WhatsApp + Email to Sales Team

## When to use

The user asks you to communicate specific plot/unit inventory availability to a sales team member (Prakash, Bharat, etc.) with:
- Reference to a shared Google Sheet (inventory / plot distribution)
- List of which plots/units are available for a specific investor group
- Supporting documents (layout PDF, brochure, masterplan)
- Wants both WhatsApp and email delivery

## Canonical example (Serenity Hillview — CM Plots, Jun 2026)

**Context:** Nishant asked to tell Prakash Singh about Charitra Murjani (CM) plots available for investors.

**Sheet:** Serenity Hillview Plotal Inventory Data (`1fISQfFbf2NoN5UTex1ju_Lu_yvYMZG0MV8vPYkgbGMw`)
**Tab:** Plot Distribution (or Copy of Plot Distribution)
**Column filter:** "Reconstitution Distribution" = "CM" (Charitra Murjani)
**Supporting docs:** Residential Layout PDF, Brochure, Masterplan

**What was sent:**
- WhatsApp HTML card with green button (pre-filled message, sheet link, PDF links, plot list)
- Email to psingh@draas.com with same content

## Workflow

### 1. Identify the inventory subset

Ask or check:
- Which sheet / tab holds the plot/unit allocation?
- Which column identifies investor groups? (e.g. "Reconstitution Distribution", "Allocation", "Investor")
- What value marks the target group? (e.g. "CM" for Charitra Murjani)
- How many plots match? List them out.

### 2. Gather supporting documents from Drive

Search Drive for:
- Layout plan PDF
- Brochure
- Masterplan
- Any project-specific docs the user has previously uploaded

Build the Drive links into the message.

### 3. Build the WhatsApp message

Structure:
```
Hi [Name],

Re: [Project] — [Investor Group] Plots Available for [Purpose]

Please open the [Sheet Name] and navigate to the [Tab Name] tab.

📊 Sheet Link: [URL]

In the [Column Name] column, look for plots marked [Code] — these are [Investor Group] plots. Approximately [N] plots are marked [Code]:
• Plot [X]
• Plot [Y]
...

These are the ones we can offer to potential [buyers/investors] right now — meant for allotment and sale.

📐 Reference Layout Plan: [URL]
📑 Brochure: [URL]
🗺️ Masterplan: [URL]

Let me know if you need any clarifications.
```

### 4. Generate the HTML card

Since the message includes 3+ links and a plot list, the URL-encoded length will exceed ~4,096 chars. Always generate an HTML card with a green "Send to [Name] on WhatsApp" button.

Save to `/tmp/whatsapp-{contact}-{project}.html` and **ALWAYS deliver via MEDIA**: `send_message(message="... MEDIA:/tmp/whatsapp-{contact}-{project}.html")`

### 5. Send email as follow-up

After the WhatsApp HTML card, send a detailed email to the same person:
- Same content, formatted for email (not just URL-encoded)
- Include all links as clickable hyperlinks
- Consider CC if the user asks

## Pitfalls

- **/tmp not accessible to user:** Always pair file creation with MEDIA delivery. Don't assume they can access the filesystem.
- **Too many links breaks WhatsApp URL:** When sharing 3+ documents + a sheet + plot list, the wa.me URL becomes too long. Always use HTML card fallback.
- **Sheet tab navigation:** The user's sales team may not know which tab. Spell it out: "Plot Distribution tab (or Copy of Plot Distribution)" — include both common names.
- **Plot number confusion:** List the plots explicitly. Don't just say "approximately N plots" — the sales person needs to know exactly which ones to offer.
