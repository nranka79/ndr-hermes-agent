# Evolving Clinical Findings During an Active Episode

Clinical findings reported in the initial dossier may change as the episode progresses. This reference documents the pattern from a real case (Ruhaan Ranka, Jun 2026) where "no GERD symptoms" was reported on Day 1 but significant acidity/burping emerged on Day 6.

## The pattern

| Phase | What happened | What to do |
|-------|--------------|------------|
| Initial Q&A | User says "no GERD, no heartburn, no reflux" | Document in dossier as "No GERD symptoms reported at time of creation" — qualify with a date |
| Days later | User reports new symptoms (acidity, burping, stomach growling) | Treat as a **correction**, not a contradiction. Update the Medical Facts Sheet first, then the Google Doc |
| Follow-up email | Specialist has been sent the original dossier | Send a brief follow-up email acknowledging the new finding. Keep it short — the specialist needs the delta, not the full dossier again |

## Updating the Medical Facts Sheet

Add new rows at the bottom with:

| Date | Category | Fact | Source/Rationale |
|------|----------|------|-----------------|
| `{date} (night)` | `CORRECTION — {finding}` | "Contrary to earlier report of 'no X,' Ruhaan now has Y." | Parent report + timestamp. Explicitly note it supersedes the earlier statement. |

Key: Always use the word "CORRECTION" in the Category column so it's visually distinct from initial entries.

## Updating the Google Doc via Docs API

```python
from gws_auth import build_service
docs = build_service('docs', 'v1', telegram_id='USER_TG_ID')

doc = docs.documents().get(documentId=DOC_ID).execute()
content = doc['body']['content']
end_idx = content[-1]['endIndex'] - 1  # Insert at the very end

update_text = "\n\n--- UPDATE {date} ---\n{Update content}"

req = [{'insertText': {'location': {'index': end_idx}, 'text': update_text}}]
docs.documents().batchUpdate(documentId=DOC_ID, body={'requests': req}).execute()
```

## Follow-up email template

```
To: [recipient]
CC: [same CCs as original]
Subject: Update re: [patient] — [new finding] ([date])

Dear [name],

An important update to the dossier I sent earlier.

UPDATE — [date]: Contrary to the earlier report of "X," [patient] has now developed [new symptoms]. We've given [intervention].

Clinical relevance: This finding changes the differential — [explanation].

The Medical Facts Sheet and Google Doc dossier have been updated.

Thanks,
[signer]
```

## Special case: medication side effects mistaken for clinical findings

Not every new symptom during an episode is a *disease progression* — it may be a **medication side effect**. This pattern repeated in the Ruhaan case:

| Timing | Symptom reported | Initial assumption | Actual cause |
|--------|-----------------|-------------------|--------------|
| Day 6 evening | Acidity, burping, stomach growling | "New GERD symptoms" — added to dossier as clinical finding | Azithromycin (AZEE 500mg) taken on empty stomach hours earlier. Antacid was taken in the morning; no food after the dose. |

### Detection pattern

When a new GI symptom appears mid-episode, always ask:
- Was a **new medication** started in the last 24-48 hours? (Azithromycin, other macrolides, NSAIDs, metformin, etc.)
- Was it taken on an **empty stomach**?
- Was the last **antacid dose** several hours before?

If yes → update as medication side effect, NOT as a clinical finding.

### Correction workflow

1. **Medical Facts Sheet**: Add a correction row with "CORRECTION — {symptom} Likely {drug} Side Effect" in the Category column
2. **Google Doc**: Append a correction note to the earlier update, explaining the true cause
3. **Follow-up email**: Send a brief correction to recipients, clarifying it's not clinically significant
4. **Clinical relevance**: A medication side effect does NOT need to be factored into the differential diagnosis

### Key documentation rule

When updating the sheet:
```
CORRECT — not a new clinical finding: This was a side effect of {drug} taken on empty stomach.
```
This prevents the symptom from being misinterpreted by a consulting specialist as evidence of a comorbid condition.

## Key principle

Never say "the dossier was wrong" — say "the clinical picture has evolved." A patient can truthfully deny symptoms on Day 1 and develop them on Day 6. The dossier is a snapshot, not a permanent diagnosis. But also: not every change represents a new diagnosis — some are iatrogenic (medication side effects) and should be documented as such to avoid misleading the consulting specialist.
