# Ranka Project Folder Taxonomy — Entity → Project → Category

NDR's agreed structure for DRAAS projects (stated 2026-09-11):

```
<Entity>/
└── <Project Name>/
    ├── Title               (title-related documents)
    ├── Approvals           (title & approvals related)
    ├── Legal               (other legals, notices)
    ├── Engineering / Architecture
    ├── Marketing           (collaterals + other)
    └── Customer
```

Two working implementations exist on Drive — both valid, don't "fix" one into the other:

- **Named-category style** (Ranka Amber, under DRA Realty): `Title`, `Approvals`, `Architectural & Engineering`, `Marketing & Content`, `Legal Notices`, `Customer`, `Misc`
- **Numbered 01–06 style** (Ranka Udaya, DTLP projects): `01_Title_and_Legal_Opinions`, `02_Approvals`, `03_Marketing_Collaterals`, `04_Sanction_Drawings`, `05_Execution_Documents_and_Drawings`, `06_Customer_Documents`

Use this file to answer "show me the folder structure for <Ranka project>" / "what's already in place for X" without re-walking the whole drive.

## Entity roots (verified 2026-09-11, ndr@draas.com token)

| Entity | Folder ID | Parent | Notes |
|---|---|---|---|
| **DRA Realty** | `1vuUfqKcbldp4tkW0cHyE4S7zSwaKVOom` | My Drive root | Holds Ranka Amber + Ranka Chikkaballapur 40 (RC40, ×3 same-name) + Vgp kagganur |
| **DRA Thindulu Land Partners (DTLP)** | `1hVmHk7dRTqYyPWl6aHfc_SOT3-q0Dn4X` | `Current Properties` `1ZCV3Kh2nfme4Bqf4hUAPsyI_JtSQDv3R` | Holds Ranka Udaya + Thindulu Land |
| **Sevaganapalli Land Partners** | `104VWF9-XdeLX612NjHE9s2-92KTpmz77` | My Drive root | owned by **presales.blr@draas.com**; parent of the misnamed `04_Engineering_and_Design` |

**Sevaganapalli Land Partners actual top-level layout (walked 2026-09-15):**
`01_Legal_and_Title_Docs` `1EmWRUvpjVb_BVxC-kl9JzSgaJhSt6hEN`, `02_Partnership_and_Firm_Docs` `1AKzDfl7B9Jzwp4uHDtXVIKdZl6HnGP4I`, `03_Approvals_and_Regulatory` `1hBnZFuZqvXCR0TeLPyk88v2JqZGoTawk`, `04_Engineering_and_Design` `1KJnzw6WVk0jwIjdHaQ_Vsgf6P_zcZwjW`, `05_Investors_and_Finance` `1g2KVcEbNOLkwGjM_4CmO11m8lDpiyRNA`, `06_Marketing_and_Brochures` `1saSsK_YUCcRduAaQQlz1ngvDkxjRRzpo`, `07_Communication_and_Correspondence` `1dXmaDx9rJu7fKBp44u1yQipqgCmclK4L`, `08_Acquisitions` `1_YrlCkehNgp_oK3mERY_q-YsPQflQxkN`, `09_Project_Management` `1MVrKxD3j4EZZ6kvHlrfkmorc5BZZmke_` (empty), `10_Reference_Docs` `1-VZ6V4aILwIvUoPpxwCQlSryPmIS4tjb` + `Balaji Land` `1pKvhDHDFvMNJsEnveaRl-VGJ4tAuAKog` + `_Archive` `11Aa1z6p9o0KpOHYhnkDLU9ltqiZWMHdb`. So Oasis files found stored directly under `Balaji Land` (Jiraaf term sheets) are IN this entity — not misplaced. NDR plans to consolidate ALL Oasis files from the 5 colleague drives into a single Ranka Oasis folder under this entity and swap colleague copies for shortcuts.
| **DRA Projects** | `1wYtUJJwELLu7o1dIr38p_QthRHaMwWvH` | My Drive root | owned by **bk@findingform.design** (architect) — read-only-ish, see SKILL.md write restrictions |

## Per-project state

### Ranka Amber — ✅ follows it (named-category)
`DRA Realty` → **Ranka Amber** `1pr8qQDrQYPC1PK7T4ZIJJY-iYjy3noe5`

| Subfolder | ID | Contents (2026-09-11) |
|---|---|---|
| Title | `1IK0xUcNOGUJ0XlW3K6rcpgu-qzadeVxl` | 31 files + Title Documents / Property Taxes / Property Documents |
| Approvals | `1oBDneKVz7wpC0IheGIE0rW9LNWrHXcHo` | 54 files + 10 subfolders (sanction plans, RERA docs, affidavits, demand notes, CC application) |
| Legal Notices | `1jOQzLjRAhy761CUU8aobTtDdmYqLyROm` | BMTF + Labour Dept notices |
| Architectural & Engineering | `1A3Foefaxfs39rzNPQOIxRNR8zTybXxPo` | Architectural, STRUCTURAL DWGS, AJ Architect Options, Drawings |
| Marketing & Content | `1lNIemJ10KuGXrDQJLQZ-jOOMBfK5hCvr` | Brochure, Renders, Ranka Amber_Enhanced |
| Customer | `1B0zA0iybCjI3wNeVU9LI8ALWyC5Yk74G` | AoA proforma, allotment letters, receipts |
| Misc | `1_RDP-7hLj3DmXgdXfD5ue5ZhYRq_X_BV` | 1 file (architect invoice) |

**Owner-mix caveat:** the ndr-owned Approvals folder *contains* psingh@ and sales1.blr@ subfolders — those inner folders are externally owned, so renames/moves inside them fail (403). Check `owners[0]` before writing.

### Ranka Udaya — ✅ follows the numbered taxonomy (DTLP)
`DRA Thindulu Land Partners (DTLP)` → **Ranka Udaya** `1sdDX5htwSKF2SSe_re-jjYb-8SsFCk8Z`

| Subfolder | ID |
|---|---|
| 01_Title_and_Legal_Opinions | `1SxLbgAHXqwETKKceYmHjAn4mZ6pyoJdD` |
| 02_Approvals | `1EsCJ0GOdDC37mZzyUlpl2-IEZZ_NcvRl` |
| 03_Marketing_Collaterals | `1fRYtiqclzInfz2rVZHFNziou9KSEg77B` |
| 04_Sanction_Drawings | `18Akgjmjtr4G_ZafkBvOk0nfDqmVQw9Gl` |
| 05_Execution_Documents_and_Drawings | `1cIbeCVsFtXtL9o0BYAEp3XHh6_t0lv2J` |
| 06_Customer_Documents | `1ByuQVQFooB2zaBxlqUrIpSXeDyElY17b` |

**Open cleanup item:** ~100 loose files (sale deeds, ECs, brochures, MIS sheets, FMB/village maps) still sit at the **project root**, outside the numbered folders.

### Ranka Oasis — ❌ does NOT follow the structure (3+ copies)
This is the outlier. Structure is split across accounts with no project-level Title/Approvals/Marketing split.

1. **ndr copy** (mis-parented): `Sevaganapalli Land Partners` → **`04_Engineering_and_Design`** `1KJnzw6WVk0jwIjdHaQ_Vsgf6P_zcZwjW` → Ranka Oasis `1w947jyUeOH-k40qm4rrNwIc2j1BHwUTO`
   - children: `158 1C7 Documents` `1Dl3VT7ksOpcUgG2fjZC1UpAb5M9XGlQc`, `Entrance Concepts` `1a5j0unT4twc5tIj-PzBamKA9kCMhXU1u`, `Legal` `1wD1kMPJ6RZNohMOVs8UF1qiPQL8LDnxI`, `Plot 119 Legal Set` `1lVlRlVKzHc4ID4H7e_ec3toSSfiYeo1w` (sales1-owned), `Ranka Oasis Proposed Villa Deisngs` `15spE6YEwuKGDXbnZeCooKElbtZozeU5n` (17 files)
   - `04_Engineering_and_Design` siblings: BOQ_and_Estimates `1j-rsbNbpKHQmzs3Mrsz1hSkiHSOPbgfO`, Floor_Plan_Configs `1PPCL_NDQe5byQGhSfI_pYl46TivXiiLb`, Geotechnical_Reports `1Lq_f9P4mEC23V5T3aXxB3BnFIC9GChSU` (contains `Ranka Oasis Engineering` `1wrwSgW8IYzNMP085knPUhFkkVzctqaiv`), Layout_Plans `1KuTBuR9Y1T8c6_b0jBnU_Gtzq6NIGjKZ`, Road_and_Infrastructure `1U2_faNki1ZKr3gCZlu5h5GfGtXLfxVYC`, Survey_and_Topography `1YNm5ttnCamxROSFPBkhLcfYhLWWE6CN8`, Villa_Designs `1mfDSLF1K4Rt7K01krI25AJAQGuTMHjiv`
2. **Architect copy** under `DRA Projects`: `1YOkuGk4Xx35gddo4tLecRyXqD7gvcRui` (bk@findingform.design) — 9 subfolders: `10/09/2026`, `Brochure`, `Entrance` (AUTOCAD / PDF / Renders / SKP-RVT / STRUCTURAL), `Marketing office`, `Master Plan & Section`, `MEP`, `OLD`, `Villa floor plans` (EAST/WEST 1500/1800, Reviewed Floor Plans, updated pdf/rvt), `Villa Renders`
3. **Other scattered copies:** sales1 copy `1fsnp6V1Fzz3CffWBAiSDqEY1AG3xG4id` (under `1fjmNWlp_hif_xR8RcEKAn5T-cgWmLjlW`), pm2 copy `1B-FyItTQ7AkwsfO8f0U_DQHTEEn37IsY`, plus root-level `Ranka Oasis R&D 2026-08-12` `1m-eqbkUoQN5CSKwRuv0UNq0tyvYsQ5Jw`, sales1 `Ranka Oasis Approvals` `17pqfdNEW6leLDVfPGH62oNJ0bhFl5Id1`, `Ranka Oasis - Design & Marketing` `1Pq35uw9K0i36pW30c66Go1_mfP2zmaR3`

## Reusable recipe — "show me the folder structure for <project>"

1. **Sweep by name, then disambiguate by owner + parent chain.** `name contains 'Ranka' and mimeType='application/vnd.google-apps.folder' and trashed=false` returned **119 folders** — same-name duplicates are the norm (Ranka Udaya ×6, Ranka Oasis ×4+). Never identify a folder by name alone.
2. **Chain each candidate up to My Drive root** (`0AFOc8cSaJXPGUk9PVA`) to prove which entity owns it, and read `owners[0].emailAddress` + `capabilities.canAddChildren` before proposing any write.
3. **Walk with a recursive lister** that prints, per folder: name, ID, owner, `canAddChildren`, and child counts (subfolders vs files). Depth 3 is enough for a structure review; stop before dumping filenames — NDR wants the shape, not an inventory.
4. Report per project: which entity it hangs off, which subfolders exist, and an explicit ✅/❌ against the agreed taxonomy. Flag loose files sitting at project root and externally-owned subfolders, since both block later cleanup.

## Pitfalls

- **"Ranka Vasis" is not a project.** Voice transcription of **Ranka Oasis** (see `voice-search-property-documents.md`). Searching variants for a non-existent project wastes the turn — if a project name returns zero Drive hits, suspect voice garbling of a sibling project name and ask/confirm rather than deep-searching.
- **`04_Engineering_and_Design` is not an entity.** It is a mid-tree bucket under `Sevaganapalli Land Partners`; the Oasis project folder nested inside it is a misplacement, not the entity root.
- **Entity folder ≠ project folder.** DRA Realty and DTLP are project containers; don't report their children (RC40, Vgp kagganur, Thindulu Land) as part of the requested project.
- **Run GWS scripts with the terminal() vault pattern** (`HERMES_SESSION_USER_ID=ndr /opt/hermes/.venv/bin/python3`), not `execute_code` — see SKILL.md pitfall.
