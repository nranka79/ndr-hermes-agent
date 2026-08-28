# Land Document Read + File (Gunjur Sy40 worked example — 2026-08-05)

Session: user sent photo of a Kannada govt endorsement (SDO Doddaballapur, Ref
L.A.S.C.R(M):11/2026, dated 05-08-2026) re: 18-21 guntas Sy No. 40, Gunjur
village, Tubagere hobli, Doddaballapur taluk; asked to analyze, translate,
confirm meaning, rename, and file in the same folder as the recent filing.

## Workflow that worked (run this sequence)
1. **Read**: for Kannada govt docs, DO NOT use `vision_analyze` free OCR — it
   returned garbage for Kannada (`BNO Avr...` mangled output). The vision-model
   extraction captured at upload (the `[The user sent an image~ ...]` block) was
   complete and clean — use it as the source of truth.
2. **Resolve account**: `gws_resolve_account` (no args) → google-draas
   (ndr@draas.com) owns work property docs. google-gmail token was
   expired/revoked (invalid_grant) — would need send_oauth_url re-auth.
3. **Find folder via precedent**: `files().list(q="name contains 'Gunjur'")` →
   found `20260801_Gunjur_Sy40_PTCL_NIL_Endorsement_SDO_Doddaballapur.pdf` and
   read its `parents` → exact target folder. Verify folder name with
   `files().get`. Folder chain:
   - Current Properties `1ZCV3Kh2nfme4Bqf4hUAPsyI_JtSQDv3R` (on shared drive `0AFOc8cSaJXPGUk9PVA`)
   - > Gunjur Farm `1k8EPOZRD1Tu6WCWuHpmJJ3QqHPmbzBJu`
   - > Doddaballapur legal docs `1v9sf9-816Izr7DcoT4BXJLIX70CNzaHp`
   - > Sy No: 40 documents `1i7ctYo2mM-DwiNUKu8ZRDrKA_CjuluNb`
4. **Name**: mirror sibling convention → `20260805_Gunjur_Sy40_Sec48A_NIL_Endorsement_SDO_Doddaballapur.pdf`
   (uploaded: `1yaInejxAfz8h92DNMnW1h7AWhTahwONA`).
5. **Convert photo → PDF**: PIL `Image.open(src).convert("RGB").save(out, "PDF", resolution=200)`.
6. **Upload + verify**: `build_service("drive","v3",service_name="google-draas")`,
   `MediaFileUpload(...)`, `files().create(body={"name","parents"}, fields="id,name,parents,webViewLink")`,
   then re-`files().get` to confirm. Report webViewLink.

## Environment gotchas (this deployment)
- **Use `/opt/hermes/.venv/bin/python`** with `sys.path.insert(0, "/opt/hermes")`
  for `from tools.gws_auth import build_service`. `/data/hermes/.venv` gives
  `IMPORT_FAILED` — no tools package.
- API keys are not in `execute_code` os.getenv; `/opt/hermes/.env` does not
  exist. Available in shell env: GOOGLE_AI_STUDIO_API_KEY, APIFY_API_KEY,
  OPENCODE_API_KEY, ASSEMBLYAI_API_KEY. No OPENROUTER key — don't promise
  OpenRouter routes without checking `env | cut -d= -f1`.
- Vault warning `canonical_uid: ... no identity mapping ... using raw id as
  fallback key` is benign noise — API works fine after it.
- Stale sibling folders exist post-reorg (`Gunjur Farm Dodballapur legal docs`,
  `Copy Gunjur-Doddaballapur`, both `parents=None`) — ignore unless asked.

## Interpreting endorsements (the user's confirmation question)
- SDO "NIL" endorsement language: "this office examined files/records — no
  acquisition of this land by this authority on record; you may obtain info from
  other acquiring agencies (roads/industry/railway/govt)".
- Confirms: no acquisition by THIS authority. Does NOT itself certify: no
  pending proceedings, no grant applications, no acquisition by OTHER agencies.
  Always state that nuance — user asked exactly this and the distinction matters
  for title checks.

## Direct Gemini vision via GOOGLE_AI_STUDIO_API_KEY
If user asks for a specific Gemini model and the managed vision path is
unavailable:
- POST `https://generativelanguage.googleapis.com/v1beta/models/{gemini-2.5-pro|gemini-2.5-flash}:generateContent?key=<key>`
  with `{"contents":[{"parts":[{"text":...},{"inline_data":{"mime_type":"image/jpeg","data":"<base64>"}}]}],"generationConfig":{"maxOutputTokens":4000}}`
- Observed 2026-08-05: free-tier quota 429 on pro/2.0-flash, 403 permission-denied
  on flash-lite — quota status varies; fall back to the captured upload
  extraction and say so transparently. Never fabricate doc content.
