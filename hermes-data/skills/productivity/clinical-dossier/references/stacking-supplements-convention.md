# Stacking Supplements Convention — Appending Deep Analysis to Existing Dossiers

**Principle:** When supplementary analysis (clinical trials deep analysis, off-label drug research, cost estimates) is requested after the main dossier is delivered, **append it to the existing dossier** rather than creating a separate supplement document. The user's exact phrasing is "stack it at the end of this report itself."

## Why

- Single source of truth — one document, one version, one link to share
- No confusion about which doc has the latest analysis
- Family members and specialists see everything in context
- The dossier becomes progressively richer as analysis deepens

## When to Append vs Rebuild

| Scenario | Approach | Tool |
|----------|----------|------|
| Adding plain-text sections (section headers, bullet lists, numbered tables, structured analysis) | Append via `batchUpdate(insertText)` at end | Docs API |
| Full formatting overhaul (colored tables, styled callout boxes, alternating rows) | Rebuild from HTML import | Drive HTML import |
| Structural changes throughout (fixing broken links, deduplicating, rewriting sections) | Rebuild from HTML import | Drive HTML import |
| User says "stack it at the end" specifically | Append via batchUpdate | Docs API |

## Appendix: Inserting at Document End

The Docs API `insertText` requires an index **less than** the segment's endIndex:

```python
doc = docs.documents().get(documentId=DOC_ID).execute()
last_element = doc['body']['content'][-1]
end_index = last_element['endIndex']  # e.g., 13266
# Valid insert range: 0 to end_index - 1
insert_position = end_index - 1
docs.documents().batchUpdate(
    documentId=DOC_ID,
    body={'requests': [{
        'insertText': {
            'location': {'index': insert_position},
            'text': '\n\nSECTION N — New Content\n...'
        }
    }]}
).execute()
```

## When a Supplement Doc Was Already Created

If you accidentally created a separate supplement doc before the user asked to "stack it at the end":

1. Read the supplement content
2. Append it to the main dossier via batchUpdate(insertText)
3. Rename the supplement doc: `{original_name}_OBSOLETE_merged_into_main`
4. Update the main doc title to reflect the new version (e.g., v1.1 → v1.2_Complete)
5. Inform the user: "[supplement] content has been merged into the main dossier at Section N. The separate supplement doc has been renamed as obsolete."

## Version Management

- Increment the version in the **document title** (not the body) to reflect the addition
- Old versions remain in the Drive folder (not deleted) so the user can trace what changed
- Log the version increment clearly to the user: "I've appended the analysis as Section 11 and updated the doc to v1.2_Complete"
- The title format: `YYYYMMDD_PatientName_Diagnosis_Dossier_vX.Y_State`

## Sharing After Stacking

After appending, ensure sharing is updated:
- Confirm the main dossier still has correct editor/reader permissions
- The supplement doc (if renamed to obsolete) doesn't need active sharing — but leave it accessible so the user can reference it
- When sharing with family members, note the version change: "v1.2 now has the full deep analysis stacked at the end"
