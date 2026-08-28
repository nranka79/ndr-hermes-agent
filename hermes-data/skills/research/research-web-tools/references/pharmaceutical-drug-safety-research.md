# Pharmaceutical Drug Safety & Monitoring Research

Research a drug's adverse effects, organ toxicity, monitoring requirements, and dose adjustment criteria from authoritative medical sources using browser tools.

## When to Use

- User asks about side effects, monitoring tests, or safety of a specific drug
- Drug is newly prescribed and the user wants to know what tests to run before dose escalation
- Combination therapy (e.g., immunotherapy + targeted agent) with additive toxicity concerns

## Source Hierarchy

| Priority | Source | URL Pattern | What it covers |
|----------|--------|-------------|----------------|
| 1 | **Drugs.com Professional Monograph** (ASHP) | `https://www.drugs.com/monograph/<drug>.html` | Full prescribing info: dosing, ADRs, monitoring, drug interactions. Search first via `https://www.drugs.com/search.php?searchterm=<drug>` |
| 2 | **NCI Drug Dictionary** | `https://www.cancer.gov/about-cancer/treatment/drugs/<drug>` | Cancer drug-specific info, FDA approval, combination therapy uses |
| 3 | **DailyMed (FDA Label)** | Search via `https://dailymed.nlm.nih.gov/dailymed/` | Official FDA prescribing label — legal source of truth |
| 4 | **MedlinePlus** | `https://medlineplus.gov/druginfo/meds/<id>.html` | Consumer-friendly summary. Find the ID by searching medlineplus.gov |
| 5 | **PubMed / ClinicalTrials.gov** | Via E-utilities API | Published trial results for specific adverse event data |

## Browser Research Workflow

### Step 1: Discover the correct drug name
The user may mispronounce or mistype the drug name (e.g., "azitinib" → **axitinib**). Before researching, confirm:
- Check the user's description: "Keytruda" = pembrolizumab, "Kitrudra" = the user's mispronunciation of Keytruda
- Use the NCI page as a quick check for the correct spelling and indication

### Step 2: Navigate to Drugs.com monograph
```
browser_navigate(url="https://www.drugs.com/search.php?searchterm=<drug>")
```
Then click the "Full prescribing information" link or "Monograph" link from results.

### Step 3: Extract structured data via browser_console
Use JS expressions targeting specific HTML sections:

```javascript
// Get pretreatment screening requirements
JSON.stringify(Array.from(document.querySelectorAll('h4'))
  .filter(h => h.textContent.includes('Pretreatment'))
  .map(h => {
    let ul = h.nextElementSibling;
    while(ul && ul.tagName !== 'UL') ul = ul.nextElementSibling;
    return ul ? Array.from(ul.querySelectorAll('li')).map(li => li.textContent.trim()) : [];
  }).flat())

// Get patient monitoring requirements
JSON.stringify(Array.from(document.querySelectorAll('h4'))
  .filter(h => h.textContent.includes('Patient Monitoring'))
  .map(h => {
    let ul = h.nextElementSibling;
    while(ul && ul.tagName !== 'UL') ul = ul.nextElementSibling;
    return ul ? Array.from(ul.querySelectorAll('li')).map(li => li.textContent.trim()) : [];
  }).flat())

// Get warning/precaution sections
JSON.stringify(Array.from(document.querySelectorAll('h2, h3, h4'))
  .filter(h => h.textContent.match(/(Hypertension|Hepatic|Renal|Cardiac|Hemorrhage|Thyroid|Proteinuria|Thromboembolic|GI perforation|Wound|RPLS)/i))
  .map(h => {
    let els = []; let el = h.nextElementSibling; let count = 0;
    while(el && count < 15) {
      if(el.tagName === 'UL' || el.tagName === 'OL')
        els.push(...Array.from(el.querySelectorAll('li')).map(li => li.textContent.trim()));
      else if(el.tagName === 'P') els.push(el.textContent.trim());
      else if(['H2','H3','H4'].includes(el.tagName)) break;
      el = el.nextElementSibling; count++;
    }
    return {heading: h.textContent.trim(), items: els};
  }).filter(h => h.items.length > 0))
```

### Step 4: Get the main content body for dosing and comprehensive info
```javascript
document.querySelector('main').textContent.substring(0, 15000)
```

### Step 5: Get dosing / dose escalation criteria
Search the extracted text for "dosage", "dose escalation", "increase dosage" sections. Key info to extract:
- Starting dose
- Dose escalation criteria (which adverse effects preclude escalation)
- Dose reduction tables for toxicity
- Timing intervals for escalation (2 weeks, 6 weeks, etc.)

## Key Sections to Extract from Any Monograph

| Section | What to look for |
|---------|-----------------|
| **Pretreatment Screening** | Baseline labs, BP, LVEF, thyroid, proteinuria, pregnancy |
| **Patient Monitoring** | Frequency of LFTs, BP, thyroid, urine protein, LVEF |
| **Dosage** | Starting dose, escalation schedule, timing, max dose |
| **Warnings/Precautions** | Organ-specific toxicities with severity and management |
| **Common Adverse Effects** | ≥20% incidence — establishes monitoring priorities |
| **Drug Interactions** | CYP450 modulators — critical for dose adjustment |

## Compiling the Output

Present findings in this structure:

### Organs & Systems Affected
Table format: System | Effect | Monitoring Method

### Recommended Test Panel
- **Baseline**: tests to run before starting (LFT, RFT, BP, thyroid, echo, urine protein)
- **Ongoing**: tests at specific intervals (weekly LFT, daily BP, monthly TSH)

### Dose Escalation Criteria
- What conditions must be met (no grade >2 AEs, controlled BP, no antihypertensives)
- Timeline for escalation intervals

### Combination Therapy Considerations
When the drug is used with an immunotherapy (pembrolizumab, nivolumab, avelumab):
- Hepatotoxicity risk increases — more frequent LFT monitoring
- Immune-related AE profile adds to drug-specific AE profile
- Different escalation intervals may apply

## Pitfalls

- **Drug name misspellings**: The user may say "azitinib" for axitinib, "Keytruda" for pembrolizumab. Always cross-check with the NCI or Drugs.com search results.
- **Split decisions**: The official label's dosing section may recommend 7mg and 10mg, but the doctor's plan may include 15mg — note this as "above labeled dose, must be under specialist supervision."
- **Combination-specific guidance**: AE monitoring differs significantly between monotherapy and combination therapy. Always check which regimen the label covers.
- **Browser truncation**: Large monographs exceed the browser snapshot limit. Use browser_console JS extraction to get targeted data instead of trying to snapshot the whole page.
- **CYP interactions**: Many TKIs (including axitinib) are CYP3A4 substrates. Common concomitant meds (azole antifungals, rifampin, grapefruit) can dramatically alter drug levels. Always flag this.
