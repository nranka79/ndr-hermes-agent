# VIP Post-Meeting Follow-Up — WhatsApp Message

Template and technique for composing a WhatsApp message to a VIP (MLA, elected representative, senior government officer) after an in-person meeting, sharing structured landowner/party data.

## When to Use

- User says "create a WhatsApp message for [MLA name] — thanking him for his time and hospitality today"
- User wants to share landowner names, addresses, unit counts, and built-up areas
- The VIP already knows the context from an in-person meeting — this is a follow-up, not a cold introduction

## Workflow

### 1. Compile Landowner Data

Extract from court filing documents or ownership tables:

| # | Name | Age | Units | % Share | Sq Ft (approx) | Address |
|---|------|-----|-------|---------|----------------|---------|
| 1 | Sunanda Vani | 73 | 12 | 26.7% | 21,672 | Flat C-301, Vani Garden, Puttenahalli |
| 2 | Malathi | 50 | 10 | 22.2% | 18,037 | No.74, Vani Garden, Puttenahalli |
| 3 | Chethana Prasad | 45 | 9 | 20.0% | 16,233 | (from court filing) |
| 4 | Ravi G.V. | 53 | 9 | 20.0% | 16,233 | Flat C-1301/1302, Vani Garden |
| 5 | Nandini Shivaprakash | 54 | 5 | 11.1% | 9,018 | No.74, Vani Garden + RT Nagar |

**Calculate built-up area per owner proportionally:**
```
total_units = 45
total_sqft = 81165
per_owner_sqft = total_sqft * (owner_units / total_units)
```

### 2. Extract Addresses from Court Filing Screen Photos

A key technique: the user can show photos of their screen with the court filing document open, and you extract addresses via OCR/vision.

**Method:**
1. User sends photo of screen showing the court filing (usually an affidavit with party details)
2. Call `vision_analyze` on the image — OCR extracts the text
3. Look for the numbered list of defendants (usually starts from Item 4 or 7)
4. Each entry has: Name, Age, Relationship (S/o, D/o, W/o), Address
5. Multiple photos may be needed to capture all entries — ask the user to scroll and send more

**Address fields to extract:**
- Full name as listed in court filing
- Age
- Parentage / spousal relationship (important — shows family connections)
- Primary residence address (full, with pin code)
- "And also at" secondary address (if listed)
- Note whether the address is within the VIP's jurisdiction (e.g., Yelahanka)

### 3. Compose the Message

**Structure:**
```
Respected Sir,

Thank you very much for your time and hospitality today.

As discussed, here are the details of the [X] [project] landowner families whose units are part of the matter:

1. *[Name]* — [Age] yrs — [X] units ([X]%) — [X] sq ft
   [Address]

2. *[Name]* — [Age] yrs — [X] units ([X]%) — [X] sq ft
   [Address]
...

Total: [X] units, [X] sq ft built-up area.

[X] of the [X] reside at [location] itself — within your jurisdiction.

Happy to share the supporting documents if needed.

Thank you again for your guidance.
```

**Delivery format:** Present as markdown code block (triple backticks, no language tag) for easy selection and copy. No clickable links or deep URLs — the user pastes into their own WhatsApp.

### 4. Tone Rules

| Element | MLA / Elected Rep | Community Elder (Phase 7) |
|---------|-------------------|--------------------------|
| Greeting | `Respected Sir,` | `[Name] Ji, pranam.` |
| Opening | Thank for time + hospitality | Ask about well-being |
| Data style | Structured list with numbers | Brief summary, no tables |
| Legal terms | "units," "sq ft," "loan" | "land," "share," "borrowed" |
| Ask | None (already met and agreed) | Specific ask for introduction |
| Close | Gratitude + offer docs | Deference + looking forward |

## Pitfalls

- **Addresses may span multiple screen photos** — the user can only show what's on their screen. Ask them to scroll down and send more photos if entries are incomplete.
- **Court filing numbering may not be sequential in your data** — the items in the affidavit (Item 4, 5, 6...) may not correspond 1:1 with your ownership table numbering. Cross-reference by name.
- **Landowners are often siblings** — same father (Late G.V. Veerasetty in this case) means they're brothers and sisters. This is important context for the VIP — it's one family, not five separate parties.
- **"And also at" addresses** — some landowners have a secondary address outside the jurisdiction. Note this but lead with their primary (on-site) address.
- **Phone number for the WhatsApp link** — the user's contacts sheet may not have the VIP's number. Ask the user directly rather than searching fruitlessly.
- **Do NOT include court case numbers, section numbers, or legal citations** in the WhatsApp message. The VIP is not a lawyer — use plain language.

## Example Output

```text
Respected Sir,

Thank you very much for your time and hospitality today.

As discussed, here are the details of the 5 Vani Vilas landowner families (children of Late G.V. Veerasetty) whose units are mortgaged under the Rs.57 Cr loan:

1. *Sunanda Vani* — 73 yrs — 12 units (26.7%) — 21,672 sq ft
   Flat C-301, Vani Garden, Near CRPF Gate, Puttenahalli, Yelahanka

2. *Malathi* — 50 yrs — 10 units (22.2%) — 18,037 sq ft
   No.74, Vani Garden, Near CRPF Gate, Puttenahalli, Yelahanka

3. *Chethana Prasad* — 45 yrs — 9 units (20.0%) — 16,233 sq ft

4. *Ravi G.V.* — 53 yrs — 9 units (20.0%) — 16,233 sq ft
   Flat C-1301/1302, Vani Garden, Near CRPF Gate, Puttenahalli, Yelahanka

5. *Nandini Shivaprakash* — 54 yrs — 5 units (11.1%) — 9,018 sq ft
   No.74, Vani Garden, Near CRPF Gate, Puttenahalli, Yelahanka

Total: 45 units, 81,165 sq ft built-up area.

All 4 of the 5 reside at Vani Garden itself — within Yelahanka jurisdiction.

Happy to share the court filing PDFs if needed.

Thank you again for your guidance.
```
