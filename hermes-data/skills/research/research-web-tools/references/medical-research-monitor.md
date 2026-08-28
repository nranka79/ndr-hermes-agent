---
name: medical-research-monitor
description: "Weekly cron-based medical literature scanning with source tracking spreadsheet and cumulative recommendations document. Designed for ongoing monitoring of a specific patient's condition across clinical trials, PubMed, Reddit, regulatory agencies, and patient organizations."
version: 1.0.0
author: Hermes Agent
license: MIT
---

# Medical Research Monitoring System

A reusable pattern for setting up a **weekly automated research scan** for a specific patient's medical condition. The system tracks sources in a Google Sheet, scans them each run, auto-discovers new sources, and accumulates evidence-backed recommendations in a growing document.

## Architecture

```
Source Tracker Sheet (Google Sheets)
    │
    ├── 18–30+ seed sources (ClinicalTrials.gov, PubMed, Reddit, FDA, etc.)
    ├── Columns: Name, URL, Category, Description, Date Added, Last Scanned, Active
    ├── Auto-grows as new sources discovered during scans
    └── Each run reads Active sources, updates Last Scanned
            │
            ▼
    Cron Job (every 7 days)
            │
            ├── 1. Read all active sources from sheet
            ├── 2. Scan each source for content from last 7 days
            ├── 3. Auto-discover new sources → add to sheet
            ├── 4. Check cumulative recommendations doc for duplicates
            ├── 5. Append NEW unique recommendations (with full citations)
            └── 6. Deliver briefing to Telegram
                    │
                    ▼
    Recommendations Doc (Google Doc in medical folder)
            │
            ├── Clinical baseline section (patient context)
            ├── Editable recommendation entries with:
            │   • Title · Action · Clinical reasoning · Source citation · Track · Date
            └── Grows week-over-week without duplicates
```

## When to Use

- A user has a family member with a chronic condition requiring ongoing literature surveillance
- They want to track clinical trials, new treatments, and research breakthroughs relevant to a specific patient profile
- They want a system that self-improves (discovers new sources as it runs)
- They want cumulative recommendations they can discuss with their doctor

## Setup Pattern

### 1. Create the Source Tracker Sheet

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3')
sheets = build_service('sheets', 'v4')

# Create sheet in the patient's medical folder
file_meta = {
    'name': '[Condition] Research — Source Tracker',
    'parents': [MEDICAL_FOLDER_ID],
    'mimeType': 'application/vnd.google-apps.spreadsheet'
}
ss = drive.files().create(body=file_meta, fields='id, name, webViewLink').execute()
ss_id = ss['id']
```

Columns: `Sl.No | Source Name | URL | Category | Description | Date Added | Last Scanned | Active`

### 2. Seed with Initial Sources

Always include these categories:
- **Clinical Trial Registries:** ClinicalTrials.gov, WHO ICTRP
- **Medical Journal Databases:** PubMed, Lancet Respiratory, ATS Journals, ERJ, JACI, Cochrane
- **Guidelines:** GINA, relevant specialty guidelines
- **Regulatory:** FDA, EMA
- **Patient Forums:** Reddit (relevant subreddits)
- **Patient Organizations:** Condition-specific foundations
- **Professional Societies:** Relevant medical academies
- **News Aggregators:** Google News feeds for the condition
- **Genetic Databases** (if relevant): ClinVar, OMIM, HGMD
- **Variant-Specific Sources** (if genomic finding): ClinVar entry, dedicated foundation

### 3. Create the Cumulative Recommendations Doc

Seed with recommendations derived from the patient's existing clinical data:

```python
media = MediaFileUpload('/tmp/recommendations.txt', mimetype='text/plain')
file_meta = {
    'name': f'{Patient Name} — Research-Backed Recommendations (Cumulative)',
    'parents': [MEDICAL_FOLDER_ID],
    'mimeType': 'application/vnd.google-apps.document'
}
uploaded = drive.files().create(body=file_meta, media_body=media, fields='id').execute()
doc_id = uploaded['id']
```

Each recommendation entry format:
```
## [Sl.No]. [Title]

Recommendation: [Actionable recommendation specific to the patient]

Clinical Reasoning: [Why this applies — connect to specific test results]

Source: [Full citation with journal, authors, year, PubMed ID/URL]

Track: [Condition or Variant Name] | Date Found: YYYY-MM-DD | Status: Active
---
```

### 4. Create the Cron Job

```python
cronjob(action='create',
    name='weekly-[condition]-research-scan',
    schedule='every 7 days',
    skills=['research-web-tools'],
    enabled_toolsets=['web','browser','search','terminal','file'],
    prompt='''...'''
)
```

### 5. Cron Job Prompt Structure

The prompt must be **self-contained** (no conversation context available in cron mode). Required elements:

1. **Patient profile** — Include age, diagnosis, key test results, current medications, relevant genetics
2. **Source tracker sheet ID** — Tell it where to read sources from
3. **Recommendations doc ID** — Tell it where to append new findings
4. **Mandatory workflow:**
   - Read the source tracker → get all active sources
   - Scan each source for content from last 7 days
   - During scanning: watch for new sources → add to sheet
   - After scanning: read recommendations doc → check for duplicates → append new ones
   - Update "Last Scanned" column for each source
   - Deliver the briefing
5. **Specific focus areas** — What to search for within each source
6. **Delivery format** — Structured briefing sections

### 6. Handling Two-Track Monitoring (e.g., Asthma + Genetic Variant)

For patients with both a primary condition AND a genetic variant of uncertain significance (VUS) requiring surveillance:

- Add variant-specific sources to the tracker (ClinVar entry, OMIM entry, dedicated foundation)
- Include variant details in the patient profile
- Add a separate section in the briefing for variant status (even "no change" is reported)
- Flag variant reclassification as HIGH PRIORITY

## Calendar Medication Events Pattern

When creating recurring medication calendar events for a treatment course, include prominent food-timing instructions:

```
🍽 FOOD TIMING: TAKE AFTER FOOD (breakfast)
```

Place this as the **first line** of the event description, followed by medication details. This ensures it's the first thing visible when opening the event.

Food timing rules:
- **Predmet/Methylprednisolone (steroid):** Take AFTER food (prevents gastritis)
- **Rabeprazole/PPIs:** Take BEFORE food on empty stomach (30 min before breakfast)
- **Bilastine/antihistamines:** Take BEFORE food on empty stomach (at bedtime)
- **Inhaled medications (Foracort, Forapril, Levolin):** No food restriction — but gargle after use

## Evidence-Based Cascade Analysis

When a user proposes a hypothesis about their child's symptom pattern (e.g., "school → viral → immune overreaction → asthma attack"), use this research methodology:

1. **Deconstruct the hypothesis** into testable sub-claims
2. **Research each sub-claim** independently across:
   - PubMed/Google Scholar for published studies
   - Condition-specific clinical guidelines
   - Patient forums (Reddit, condition-specific communities)
   - Regulatory and patient organization resources
3. **For each sub-claim, find:**
   - Supporting evidence (studies, citations, confidence score)
   - Refuting evidence or nuances
   - Reddit/patient sentiment
4. **Compile overall assessment** with confidence score and clinical recommendations
5. **Present analysis** as: Thesis Validation → Arguments For → Arguments Against → Refined Mechanism → Clinical Implications → Conclusion

## Source Categories

| Category | Examples | Update Frequency |
|----------|----------|-----------------|
| Clinical Trial Registry | ClinicalTrials.gov, WHO ICTRP | Continuous |
| Medical Journal | PubMed, JACI, Lancet Resp, ERJ, ATS | Weekly |
| Guidelines | GINA, AAAAI, ATS/ERS | Annual + updates |
| Regulatory | FDA, EMA | Continuous |
| Patient Forum | Reddit (r/asthma, r/Allergy) | Daily |
| Patient Organization | Condition-specific foundations | Weekly |
| Genetic Database | ClinVar, OMIM, HGMD | As updated |
| News Aggregator | Google News, medical news sites | Daily |
| Professional Society | AAAAI, ATS, ERS | Conference-driven |
