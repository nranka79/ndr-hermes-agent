# Voice-to-Search: Property Document Retrieval

When the user says "open the [property name] [document type] from the drive" via voice memo, the transcription often garbles proper names and document types. This reference codifies the interpretation patterns.

## Common Voice Transcription Errors (DRAAS corpus)

| User says (voice) | Likely means | Pattern |
|---|---|---|
| "Tars" | **Towers** | /tɑrz/ → /taʊərz/ — Indian-English speakers often merge the vowel; the terminal -s picks up a phantom plural or 'rs' reduction |
| "Flow Plan" | **Floor Plan** | /floʊ/ + /plæn/ — "floor" reduced to "flow" in fast speech |
| "Kingfisher Tars" | **Kingfisher Towers** | Property name + the Towers mistranscription |
| "Flow plan for Kingfisher" | **Kingfisher Towers — Floor Plan** | Compound query: property plus doc type |
| "KFT plan" | **Kingfisher Towers — Floor Plan** | KFT = acronym for Kingfisher Towers, "plan" = floor plan |

## Search Strategy

When a voice transcription gives no exact Drive matches:

**Step 1 — Interpret the property name**
- Strip common voice errors: Tars→Towers, Hights→Heights, Gardn→Garden, Valliey→Valley
- Check if the garbled word is a common DRAAS property suffix (Towers, Enclave, Farms, Valley, Heights, Gardens, Villas)
- Search with the corrected name

**Step 2 — Search the project's parent folder, not just by name**
- Property documents often sit in a parent folder (e.g. Kingfisher Towers lives under **PSCP** = Prestige South City Projects)
- Search for distinctive acronyms: KFT (Kingfisher Towers), KFT-5F (Kingfisher Towers 5th Floor), SC (South City)
- List the parent folder contents and scan filenames for the document type

**Step 3 — Interpret the document type**
- "Flow plan" → Floor Plan
- "Flow chart" → Flow Chart / Title Flow
- "Master plan" → Master Plan / Site Plan
- "Layout" → Layout Plan
- "Elevation" → Elevation Drawing
- "Section" → Cross-section Drawing

**Step 4 — Validate visually**
- Once found, render the first page as PNG and use vision_analyze to confirm it's the right document
- Look for: project name in title block, floor number labels, door/window schedules, room labels (Living, Bedroom, Kitchen, Utility)
- Report what you see: which floor, which building/tower, what the layout contains

## Worked Example: Kingfisher Towers 5th Floor Plan

User said via voice: **"Kingfisher Tars, Flow Plan, from the drive, can you open the flow plan from the drive?"**

1. **Interpret:** "Tars" → "Towers". "Flow Plan" → "Floor Plan". Query: Kingfisher Towers floor plan.
2. **Search:** `name contains 'Kingfisher'` found `20210128_KingfisherTowers_Flat14A_AbsoluteSaleDeed.pdf` in PSCP folder. Listing the PSCP folder revealed `KFT-5F Plan (1).pdf`.
3. **Interpret acronym:** KFT = Kingfisher Towers, 5F = 5th Floor.
4. **Validate:** OCR confirmed "KINGFISHER TOWERS — MUNICIPAL NO: 24, VITTAL MALLYA ROAD, BANGALORE — 5th FLOOR PLAN — 10 APARTMENTS, BADMINTON, SQUASH" with living/dining/kitchen/bedroom layouts, door/window schedules, and Prestige branding.
5. **Deliver:** Google Drive view link.

## Acronyms in DRAAS Drive Filenames

| Acronym | Meaning | Example |
|---|---|---|
| KFT | Kingfisher Towers | `KFT-5F Plan (1).pdf` |
| SC | South City | Various Prestige South City files |
| PSCP | Prestige South City Projects | Parent folder name |

When a search by full name returns stale results, try the acronym: `name contains 'KFT'` will match floor plans, specifications, and sale deeds that the full-name query may not surface under the user's transcription.