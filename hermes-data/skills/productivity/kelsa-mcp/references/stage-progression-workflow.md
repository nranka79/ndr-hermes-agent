# Pipeline 10 Stage Progression & Prerequisites

## Sequential Stage IDs

Pipeline 10 (DRA Sales Leads) follows a **strict sequential progression**. You cannot jump stages.

| Current Stage | Allowed Target | Stage ID | Notes |
|--------------|---------------|----------|-------|
| Cold | Warm | 2 | Requires `cf_requirements` field populated |
| Warm | PSC | 281 | Requires "Confirm Inquiry" task completed |
| PSC | SSV | 6 | Requires `cf_interested_in_site_visit_` = True |
| SSV | Hot | 3 | Requires site visit completed |
| Hot | Converted | 4 | Requires booking/offer process |

**Error when jumping:** `"The record cannot jump to \"SSV\" from its current stage. Allowed targets: PSC (ID: 281)."`

## Typical Cold → Warm → SSV Workflow

When moving leads from Cold to SSV (e.g., from a campaign response sheet):

1. **Cold → Warm (stage_id: 2)**
   - Before moving, ensure `cf_requirements` is populated via `update_lead` with `field_values`
   - Then call `move_stage(lead_id, stage_id=2)`
   - Wait for draft to complete via `get_draft_status`

2. **Warm → PSC (stage_id: 281)**
   - Direct `move_stage(lead_id, stage_id=281)` — prerequisites are typically already met
   - If it fails, check `list_lead_tasks` and `get_lead` for outstanding prerequisites

3. **PSC → SSV (stage_id: 6)**
   - **Critical prerequisite:** `cf_interested_in_site_visit_` checkbox must be set to `True`
   - First call `update_lead(lead_id, field_values={"cf_interested_in_site_visit_": True})`
   - Wait for draft to complete
   - Then call `move_stage(lead_id, stage_id=6)`

## `update_lead` with `field_values`

The `update_lead` tool accepts custom fields via the `field_values` object parameter, NOT as top-level keyword arguments:

```python
# ✅ CORRECT
update_lead(lead_id=53882891, field_values={"cf_requirements": "Interested in Ranka Udaya"})

# ❌ WRONG — returns "unknown keyword: :cf_requirements"
update_lead(lead_id=53882891, cf_requirements="Interested in Ranka Udaya")
```

## Async Draft Processing

Both `update_lead` and `move_stage` return draft IDs. Always verify completion:

```python
import re, time

# Get draft ID from response
draft_match = re.search(r'draft ID: (\d+)', response_text)
if draft_match:
    draft_id = int(draft_match.group(1))
    # Poll until complete or failed
    for _ in range(10):
        time.sleep(1.5)
        status = get_draft_status(draft_id=draft_id)
        if "completed" in status: break
        elif "failed" in status: raise Exception("Draft failed")
```
