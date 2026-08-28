# Common Voice Transcription Corrections — DRA Real Estate Domain

NDR uses voice input extensively. These are known transcription errors in the real estate context.

## Project / Developer Names

| Voice Input (wrong) | Correct |
|---------------------|---------|
| Rovala | Row Villa |
| Goodridge | Godrej |
| Saukaya / Saukya | Soukya (Road) |
| Roor | Soukya Road |
| Flow Plan | Floor Plan |
| Tars | Towers |
| Southin | Assudani |
| Vivo BIO | Vivo X Fold |
| Ro Vila | Row Villa |
| Riyaga | Riya Gawri |
| Manthir | Mantri Infotech |
| Hirebat / Mavi | Mahaveer Hospital |
| Kuwait | Huawei |
| Narsem / Narsama | Narasimha (Raju) |
| Giri | Jaychandra Raju (Giri) |

## Location Corrections

| Voice Input (wrong) | Correct |
|---------------------|---------|
| Byadaralli | Byadarahalli |
| Lepakshi | Lepakshi (correct, but often mispronounced) |
| Dundi | Dundi (correct) |

## How to handle

1. **Never repeat the voice error back to the user.** Use the corrected form directly.
2. When the user says a name that could be voice-transcription-corrupted, run it through `entity_resolver` first — it handles phonetic variants, aliases, and partial matches.
3. If the user corrects a name you used incorrectly, save the correction via `noun_learner(action='learn_correction', misspelling=..., correct=...)`.
4. For common first-name-only queries (e.g., "Rajesh"), use contact_resolver with context (project name) to disambiguate. Voice often drops the surname.

## When to apply

Apply these corrections silently — without announcing you're doing so — in:
- Search queries for entity_resolver / contact_resolver
- Search queries for web_search / portal searches
- File and folder names
- Any output to the user