# JV ratio field quirk — cf_expected_jv_ratio_for_developer (observed 2026-08-26)

On DRA Land Proposal (pipeline 519), `cf_expected_jv_ratio_for_developer` is
**auto-computed and cannot be set manually**, and its displayed value is NOT
`100 - landowner_ratio`.

Observed values:
- Landowner 50 (JV 50:50) → developer shows **-49** (#54543893, Bairashettihalli)
- Landowner 40 (JD 40:60) → developer shows **-39** (#54958394, Chandapura GPR Grande)

Pattern: `displayed_developer = 1 - landowner_ratio`. `update_lead` with the
correct value (60) completes its draft but the stored/displayed value never
changes — the field is a pipeline formula artifact.

## What to do
- Set only `cf_expected_jv_ratio` (landowner %).
- Document the intended split in `cf_proposal_notes` (e.g. "Ratio 40% landowner
  : 60% builder").
- Do NOT attempt to "fix" the developer figure — every JV/JD lead in the
  pipeline shows this negative artifact.