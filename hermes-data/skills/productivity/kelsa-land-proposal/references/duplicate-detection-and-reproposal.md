# Duplicate detection & re-proposal handling (2026-08-25 session)

## Sketch survey-number matching — the decisive duplicate signal
- Case: NDR received a new broker proposal (Rupa Gangadharapal) for "22A, 7A
  registered + 15A unregistered agreement" at https://maps.app.goo.gl/rWuvVYGoukERMQwb9
  and suspected it was the same land Aamir Khan had proposed earlier.
- Record-name search found nothing; keyword search ("Sarjapur", "22") surfaced
  candidates but not the match.
- `search_leads(pipeline_id=519, query="cf_proposal_source:aamir khan")` →
  #54040844 "20 Acres – Outright Purchase – Avati, Devanahalli" (Proposed, 24 Jul 2026).
- Map pin resolution: `curl -s -L <maps.app.goo.gl> -w "%{url_effective}"` →
  13.2974815,77.7242766 (Avati, 562164). Aamir's lead pin 13.2848638,77.7235458 —
  same village block, ~1.4 km apart → consistent, not contradictory.
- The sketch PDF ("AVATHI GOBARAGUNTE SKETCH 10-09-2024 FINAL") settled it:
  pdftotext on the AutoCAD-generated PDF shows the Kannada title block as
  mojibake (UÁæªÀÄ = village) but the **Sy Nos are legible**: Avathi 93/1-14,
  96/1-14; Gobaragunte 113, 114, 115, 116, 123, 124.
- Lead #54040844 carried the same set: Sy Nos 93/1-17, 96/1-17, 113, 114, 115,
  116, 123, 124; villages Avati & Gombaragutte; taluk Devanahalli →
  CONFIRMED SAME PARCEL.
- **The attachment filename itself often carries the village combo** ("AVATHI
  GOBARAGUNTE") — check it before deep analysis.

## Same land, different broker → NOTE on the existing lead (NDR preference)
- NDR: "add a note to the same existing [lead], now [broker] has proposed the
  same land". Do NOT create a duplicate record.
- Note structure that worked: header `=== <date> — <broker> re-proposed same
  land ===`, then: same-parcel confirmation evidence (pin + sketch), new source
  + relationship context ("very well known to Mr. V.K. Reddy"), owner ask vs
  NDR offer (₹7 Cr/acre ask → ₹6 Cr/acre immediate outright on the 20A =
  ₹120 Cr, ~₹1,377/sqft), extent deltas (22A 7-registered+15-agreement brief
  vs 20A lead vs 27A-10G sketch → reconcile), title flags.
- After the note, OFFER to update the economic fields (cf_expected_rate_per_sqft,
  cf_expected_total_outright_cost_of_land, cf_offer_type) — NDR decides;
  don't auto-write.

## Entry assignment automation may not fire
- get_pipeline shows `set_assignee on entry → 36564 [filter: cf_additional_team_member?]`
  at 'Proposed'. The filter gating means a bare create_lead can come back
  `Assignee: unassigned` (observed #54949682 on 2026-08-25).
- Fix: `update_lead(pipeline_id=519, lead_id=<id>, assignee_id="36564")` →
  poll get_draft_status → confirm "Assignee: Prakash Singh".
- NDR pattern: land proposals go to Prakash Singh; add @mention + briefing in
  a note when he asks for one.

## Voice notes referencing attachments often arrive with NO content
- Twice in one session: NDR's voice note said "based on the below chat
  conversation" / "check the map, sketch attached" but no chat text, no map
  link, no file came through (/mnt/uploads empty, no attached_files block).
- Do NOT guess the land or fabricate a conversation. Check /mnt/uploads first;
  if empty, say plainly nothing arrived and ask for: chat forward / map link /
  essentials (location, extent, deal type).
- Spelling vs the Kelsa dropdown: voice said "Rajesh Thalrecha" but the chat
  signature and the dropdown say "Rajesh Talreja" — use the chat spelling.
  Verify an option exists via `search_leads(query="cf_proposal_source:<name>")`
  (returned records prove the option is live; get_stats truncates at ~50 lines,
  so R–Z source names never appear in its output).