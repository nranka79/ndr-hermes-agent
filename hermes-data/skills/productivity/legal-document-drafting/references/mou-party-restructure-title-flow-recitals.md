# MOU Party Restructure & Title-Flow Recitals (Live Google Doc)

**Trigger:** User asks to remove/reassign parties in an existing MOU ("remove first party X", "only Y will be first party"), re-map Schedules to remaining parties, and/or fold a scanned legal opinion's title flow into the MOU as recitals + condition precedents.

Validated on the Doddasane (Devanahalli) Dev-Cum-Sale MOU, Jul 2026 — three surgical rounds on one live Docs file.

## Workflow

1. **Dump the doc with indices first.** Walk `body.content`, print `[startIndex-endIndex] text` per paragraph. This is the index map — never edit blind.
2. **Verify anchors before editing.** Search for exact substrings (party labels, schedule headers, clause headings) and confirm they exist exactly once before touching them.
3. **Three-batch pattern** (see `references/google-docs-api-edit-pitfalls.md` for the underlying index rules):
   - Batch A: `deleteContentRange` for paragraph removals, ordered **highest index first** (party blocks, stray blanks, signature lines).
   - Batch B: `replaceAllText` with `matchCase: True` for label/header/text swaps — no index math.
   - Batch C: re-fetch doc, recompute insertion index (e.g. start of "NOW, THEREFORE"), then `insertText`. Recitals end with `\n`, blank lines as `\n\n`.
4. **Verify after every round** — re-dump and diff the affected region; grep for leftovers of removed labels (`FIRST PARTY NO\.|SECOND PARTY NO\.`).
5. **Single-party consolidation** (when only one First Party remains):
   - Delete the removed party paragraph + its signature line.
   - Renumber survivor (2 → 1) and replace the collective-definition paragraph with a single-party definition ON the survivor's line: `(Hereinafter referred to as the "Landowner" or the "FIRST PARTY", which expression shall unless repugnant to the context mean and include his respective legal heirs, executors, administrators, and permitted assigns);`
   - Sweep ALL downstream references: Recital A subject (plural→singular), recitals mentioning "FIRST PARTY NO. 2", all four Schedule headers, any clause body (e.g. 4.2.2), signature labels.
   - `replaceAllText` can also fix adjacent typos in the same pass (e.g. duplicated `(Survey No. 68/2 - (Survey No. 68/2 -` header → single).
6. **Legal-opinion title flow → recitals:**
   - OCR the scanned opinion: render pages with pymupdf (`get_pixmap(dpi=200)`) then `vision_analyze` each PNG (Kannada RTCs OCR unreliably for names — do NOT fabricate owner names; keep "name to be shared later" and say so).
   - Extract the chain: origin deeds (doc no/date), inheritance/mutation events, consolidation sale deeds in favour of the party, mutation extracts confirming them, subsisting mortgage deeds (bank + doc nos), EC periods, and the opinion's conclusion.
   - Draft ONE recital per fact-block, in the doc's style (`L. \tThe FIRST PARTY has acquired...`): title flow / subsisting mortgage / legal-opinion confirmation / adjacent-survey purchase plan.
   - Add the mortgage discharge as a new bullet under Clause 2.1 Conditions Precedent (release certs/NOCs + registered release deeds before alienation).
7. **Don't touch Schedule boundary descriptions** unless asked — "NORTH BY: Survey No. 26, Land belonging to Narasimhaiah" is a boundary of adjoining land, not a party reference.

## Pitfalls

- **Voice-dictated party lists are ambiguous.** "Remove first party 1,3,4 and second party 3" contradicted the explanatory text ("first party no 1 is the current landowner..."). Treat the EXPLANATION as the tiebreaker, state your interpretation explicitly in the summary, and expect a follow-up correction ("first party no 1 also removed, only no 2 will be first party"). Each follow-up is a NEW surgical round, not a redo — re-dump, re-anchor, re-apply.
- **403 "caller does not have permission" is usually the wrong session identity**, not a doc-permission problem. Use the session's real `HERMES_SESSION_USER_ID` (check `echo $HERMES_SESSION_USER_ID`, e.g. `ndr-[REDACTED-TID]`); guessing a slug (e.g. `sales1_blr`) returns 403. The vault's "canonical_uid" fallback warning is informational, not the cause.
- **Vault socket path in env may be stale.** If `gws_resolve_account` reports the socket unreachable, locate the live socket with `find / -name vault.sock` (this deployment: `/run/gws-vault/vault.sock`) and prefix every command: `GWS_VAULT_SOCKET=/run/gws-vault/vault.sock HERMES_SESSION_USER_ID=<real-id> python3 ...`. Don't conclude the vault daemon is down.
- **Run the edit script via `terminal()` heredoc/file, not `execute_code`** — sandbox strips vault env vars (see `references/editing-existing-mou-documents.md`).
- **Batch order matters**: deletes first (highest index first), then text replaces, then re-fetch + insert. Never mix index ops with stale indices.
