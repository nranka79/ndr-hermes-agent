# Project Folder Discovery & Consolidation

**Scenario:** A DRAAS real estate project has documents scattered across multiple Google Drive folders — possibly under different names, in different tree locations, owned by different entities, and mixed with unrelated projects that share the same survey number.

**Key principle (from Nishant, Jul 2026):** *Show me everything first, let me decide how to organize it.* Do NOT propose moves or restructure until the user has seen the full inventory. **But also: every plan must use the canonical DRAAS hierarchy below — never propose dropping files into My Drive root.**

## DRAAS Canonical Project Hierarchy (mandatory)

Every DRAAS real estate project MUST follow this structure:

```
DRA Projects /
  └─ [Entity name] (DTLP / DRA Satvik / DRA KAAJ / etc.) /
       └─ [Project name] /
            ├─ 01_Title_and_Legal_Opinions/    ← deeds, opinions, EC, patta, FMB
            ├─ 02_Approvals/                   ← HNDT, RERA, plan sanction, OS fees
            ├─ 03_Marketing_Collaterals/       ← brochures, posters, videos, plant docs
            ├─ 04_Sanction_Drawings/           ← sanctioned building plans, layouts
            ├─ 05_Execution_Documents_and_Drawings/  ← structural, arch, firm docs (PAN/GST/TAN)
            └─ 06_Customer_Documents/          ← customer KYC, agreements
```

**Rules:**
- The umbrella for any DRA Thindulu / DTLP project is `DRA Projects / DRA Thindulu Land Partners (DTLP) / [Project] / [buckets]`
- **Never** drop a new file into My Drive root, even if the project is "scattered" — find the canonical project folder first
- If no canonical project folder exists, ask before creating one
- Subfolders inside buckets follow existing project conventions (e.g., `01_Title_and_Legal_Opinions / Legal_Opinions /`, `01_Title_and_Legal_Opinions / Sale_Deeds /`)

**Known canonical homes (as of Jul 2026):**
- DRA Projects / DRA Thindulu Land Partners (DTLP) / Ranka Udaya — for 240/3 (DRA Thindulu LP)
- DRA Projects / DRA Thindulu Land Partners (DTLP) / Thindulu Land — for the 2.16 Acres Thindlu Village property (Sy 108/205/206) — a different DTLP project
- DRA Projects / Ranka Oasis — for SLP / 158, 166, 167, 168, 176, 177 (Sevaganapalli LP)
- DRA Projects / Amber — for Ranka Amber (KIADB Devasandra)
- DRA Projects / Serenity Hill View — for Serenity Hill View project (DIFFERENT from "Serenity Estate" legacy name — see below)

**Different DTLP projects under the same DTLP umbrella (Jul 2026 lesson):** DRA Thindulu Land Partners (DTLP) is a partnership entity that holds MULTIPLE different land parcels. Each parcel gets its OWN subfolder under `DRA Projects / DTLP /`, not under the project name. Examples:
- `DRA Projects / DTLP / Ranka Udaya` — for 240/3 (1.75 Acres, Sevaganapalli Village)
- `DRA Projects / DTLP / Thindulu Land` — for the 2.16 Acres Thindlu Village property (Sy 108/205/206)

**Don't conflate DTLP projects just because they share the DTLP umbrella.** They are different properties with different title chains, different sellers, different file sets. When reorging, each DTLP project gets its own 6-bucket structure under its own subfolder. **Common confusion:** "Thindlu Land Partners land 1 (2.16 Acres)" looks like it might be Ranka Udaya because both are DTLP — but they are NOT. Different Sy Nos, different villages (Sevaganapalli vs Thindlu), different legal chains. Search by survey number AND village to disambiguate.

**Common naming confusion (Jul 2026):**
- **"Serenity Estate"** = OLD name for Ranka Udaya 240/3 (renamed Q4 2025). All Serenity Estate material belongs under Ranka Udaya.
- **"Serenity Hill View" / "Serenity Hillview"** = SEPARATE active 2026 project, NOT a renamed version of Ranka Udaya. Distinct.

## Discovery Steps

### 1. Find ALL folders by project name variants

The same project may exist under multiple names. In one real case, "Serenity Hill View" was also stored under "Godwad Bhavan Jain Trust Nandi Hills property". Search all known variants:

```python
from tools.gws_auth import build_service
drive = build_service("drive", "v3", service_name="google-draas")

def find_folder(name_contains):
    resp = drive.files().list(
        q=f"name contains '{name_contains}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
        fields="files(id, name, parents, mimeType, webViewLink)",
        pageSize=10, supportsAllDrives=True, includeItemsFromAllDrives=True
    ).execute()
    return resp.get("files", [])

# Search every name variant AND old names
for term in ["Ranka Udaya", "DRA Thindulu", "DRA Thindlu", "DTLP", "Serenity Estate"]:
    folders = find_folder(term)
    # Record each with its parent location
```

**Always search for old names too** — "Serenity Estate", "Thindlu Land Partners", etc. The same project may have legacy folders under its old name.

### 1.5. Broad search for ALL related files (Jul 2026 lesson)

**Critical expansion of the discovery pattern:** when a project's documents seem to be in 1-2 folders, do NOT stop there. Run a broad fullText + name search across Drive for every name variant. Real case (Ranka Udaya reorg, Jul 2026): searching just "Serenity Estate" found 26 files; broadening to 12 query terms across all of Drive found **181 candidates in 64 different parent folders** — a 7x expansion of the scope.

The broad-search query set that worked for Ranka Udaya:

```python
queries = [
    "Ranka Udaya", "RankaUdaya", "Serenity Estate", "SerenityEstate",
    "Thindulu", "Thindlu", "Thindli", "DTLP", "DRA Thindulu",
    "240/3", "240-3", "Sevaganapalli 240",
]
# Run each via fullText + name search
```

After broad search, **filter aggressively** to drop false positives:
- SLP project (158, 166, 167, 168, 176, 177 series) is a different project — exclude
- Other DRA Projects siblings (Amber, Riverstone, Northstar, R99, RAQ, Mirabilis) — exclude
- Ranka Oasis / Sevaganapalli Land Partners is the SLP project, not RU — exclude
- TAAL, Westbury, Ankal Palya, Ranka99, RAQ — different projects entirely
- User-personal folders (PRR Wedding, Murjani, etc.) — exclude

A file is "in scope" if any in-scope keyword appears in its name OR any parent folder name. Reject if any out-of-scope keyword appears in the same combined string. The broad search typically finds 2-3x more files than the obvious-folder search. Always do it.

### 2. Find ALL survey-number related folders

A survey number like "Sy No 93/2" may appear in different states (Bangalore Hurulugurki vs Goa Bamnolim). Distinguish by:
- Village name in the folder title (Hurulugurki vs Bamnolim)
- Document content (parties/authorities mentioned)
- Parent folder location in Drive

Present both to the user with clear geographic context so they can identify which belongs to the current project.

### 3. Search for partnership entity names

The project may involve a separate partnership entity whose documents live in their own folder:

```python
for term in ["DRA Thindulu Land Partners", "Sevaganapalli Land Partners", "DRA Realty", entity_variants]:
    resp = drive.files().list(
        q=f"name contains '{term}' and trashed = false",
        fields="files(id, name, parents, mimeType, webViewLink)",
        pageSize=50, supportsAllDrives=True, includeItemsFromAllDrives=True
    ).execute()
```

Also search for individual documents (not just folders) matching entity names — scattered docs may not be inside a project folder.

### 4. Check folder parent locations (KEY for DTLP umbrella rule)

For each found folder, determine its parent and grandparent — the chain tells you if it's at root or under the canonical umbrella:

```python
folder_info = drive.files().get(fileId=folder_id, fields="parents, name, webViewLink", supportsAllDrives=True).execute()
parent_ids = folder_info.get("parents", [])
if parent_ids:
    parent = drive.files().get(fileId=parent_ids[0], fields="name, parents, webViewLink", supportsAllDrives=True).execute()
    # Walk up to root
```

**Key findings to note:**
- Is the folder at root level or under the canonical umbrella (`DRA Projects / DTLP / Project`)? **If at root, it must be moved.**
- Under "My Drive" vs "Shared Drive"?
- Some under "DRA Projects" while others at root?

**If you find project material at My Drive root, that's a red flag** — propose moving it under the canonical umbrella, not just into a new subfolder.

### 5. List ALL contents of each folder

Present a complete itemized list (files + subfolders with links) for every relevant folder, grouped by folder:

```
📁 Godwad Bhavan Jain Trust (72 files — legal docs)
  📄 sale deed 1043/75-76.pdf
  📄 RTC 1974-1975.pdf
  ...

📁 Godwad Jain Trust Resort (25 files — renders/site plans)
  📄 Nandi Resort Site Plan revised.pdf
  ...

📁 Serenity Hill View (3 subfolders — sparse)
  📁 Architectural/
  📁 Brochure/
  📁 Structural/ (empty)
```

### 6. Identify cross-folder relationships

Flag when the same content appears related across folders:
- Legal docs in one folder, architectural/renders in another — same project, different doc types filed separately
- Trust/entity docs in a separate folder — partnership entity folder (e.g., Redsol Farmers Collective) contains agreements between trust and partnership
- Scattered individual docs — board resolutions, letterheads, proposals matching entity name but not inside any project folder
- **Same project under old + new name** — the most common DRAAS sprawl pattern (e.g., "Serenity Estate" + "Ranka Udaya" for the same 240/3 property)

### 7. Classify every file into a bucket

For each scattered file, classify into one of the 6 DRAAS buckets:

| File name pattern | Bucket |
|---|---|
| `*deed*`, `*legal opinion*`, `*legal report*`, `*ec *`, `*encumbrance*`, `*patta*`, `*fmb*`, `*gift*`, `*partition*`, `*rera order*`, `*spa*`, `*affidavit*`, `*legal heir*`, `*attestation*`, `*payment receipt*`, `*lakhs*`, `*replacement*`, `*cheque*`, `*relinquishment*`, `*gpa*` | **01_Title_and_Legal_Opinions** |
| `*hndt*`, `*approval letter*`, `*panchayat*`, `*conversion*`, `*osra*`, `*tangedco*`, `*ptcl*`, `*grant certificate*`, `*rtc*`, `*mr no*`, `*sketch*`, `*akarband*`, `*order sheet*`, `*plan sanction*` | **02_Approvals** |
| `*brochure*`, `*hoarding*`, `*poster*`, `*walkthrough*`, `*marketing*`, `*plant*`, `*green wall*`, `*jasmine*`, `*vine*`, `*bougainvillea*`, `*flex*`, `*sunpack*`, `*wall gate*`, `*signage*`, `*logo*`, `*layout look*`, `*pathway*`, `*krackerz*`, `*turnkey*`, `*leads*`, `*info*` | **03_Marketing_Collaterals** |
| `*building plan*`, `*sanctioned*`, `*sanction draw*`, `*final layout*`, `*layout plan*`, `*approved layout*` | **04_Sanction_Drawings** |
| `*structural*`, `*architectural*`, `*execution*`, `*dwg*`, `*rvt*`, `*skp*`, `*cad*`, `*elevation*`, `*floor plan*`, `*master files list*`, `*partnership deed*`, `*reconstitution*`, `*pan*`, `*gst*`, `*tan*`, `*firm*`, `*registration*` | **05_Execution_Documents_and_Drawings** |
| `*aadhar*`, `*pan card*`, `*kyc*`, `*customer*` | **06_Customer_Documents** |

**Always review the auto-classified list** — the heuristic catches ~90% but the user's eyes catch the rest (e.g., `2 Plot No.2 Sy.No. 166-3 SEVAGANAPALLI.docx` is a sale deed → 01; `DRA Thindlu PAN.pdf` is firm PAN → 05; `40623 (5) (3).pdf` is a plan doc → 02).

### 8. Present the reorg plan as an HTML doc in TMP (user's preferred review format)

The user (Jul 2026) said: *"give me a plan as a .html file in the temp folder, using html.css so I can make it very easy to read, showing me the current org structure, the current different folders, where do they lie, what is the root, what is the entire tree under which these folders lie, right? And then the proposed RE-OGG. In the most visual and easy to understand man as possible."*

The plan MUST include:
- **AS-IS section** — full current tree (root → all scattered folders → their contents)
- **TO-BE section** — proposed tree (canonical DRAAS hierarchy → 6 buckets → file assignments)
- **Side-by-side file table** with: source folder, current name, new name, target bucket, reason
- **Decisions table** with: defaults + 4-letter answer fields (A/B/C/D)
- **Execution phases** as numbered callout boxes

Use the dark theme + class-level sections (CSS variables for colors). Save to `TMP` folder (id `18p74II2uL32sNDzDDwXzmlOUdJJOTmE-` for `ndr@draas.com`).

**Sample plan templates and CSS pattern:** see `references/reorg-plan-html-template.md`.

**Get sign-off with `clarify` tool** before executing. The user has multiple decisions to make (A/B/C/D for filenames, subfolder creation, etc.).

### 9. Execution Phase — After User Approves the Moves

Once the user says "go ahead," execute the reorganization in this order:

#### Phase 1: Create the target folder structure

Create all destination folders before moving anything. **Only create folders the user explicitly approved:**

```python
def create_folder(name, parent_id):
    f = drive.files().create(
        body={'name': name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_id]},
        fields='id, name, webViewLink', supportsAllDrives=True
    ).execute()
    return f['id']
```

Typical sequence: (a) create `DRA Thindulu Land Partners (DTLP)` if it doesn't exist, (b) move existing `DRA Projects / Ranka Udaya` into DTLP, (c) create the 6 bucket folders under Ranka Udaya.

#### Phase 2: Pre-check ownership before moving

**The most common failure is trying to move a folder Nishant doesn't own.** Before moving any folder, check:

```python
f = drive.files().get(
    fileId=folder_id,
    fields="id, name, ownedByMe, capabilities(canAddMyDriveParent, canCopy)",
    supportsAllDrives=True
).execute()

if not f.get('ownedByMe'):
    cap = f.get('capabilities', {})
    print(f"Cannot move — owned by another user. canAddMyDriveParent={cap.get('canAddMyDriveParent')}, canCopy={cap.get('canCopy')}")
```

#### Phase 3: Three approaches for moving content

| Situation | Approach | How |
|-----------|----------|-----|
| **Folders you own** | `files.update()` with addParents + removeParents | Standard Drive API move |
| **Folders shared by another user (canCopy=True)** | Copy individual files to your target folder | `drive.files().copy(fileId, body={'parents': [target_id], 'name': name}, supportsAllDrives=True)` |
| **Folders shared by another user (canCopy=False)** | Create shortcuts in the target folder | `drive.files().create(body={'name': name, 'mimeType': 'application/vnd.google-apps.shortcut', 'parents': [target_id], 'shortcutDetails': {'targetId': file_id}}, supportsAllDrives=True)` |

**Root-level files:** When a folder's `parents` field returns `None` or `'root'`, omit `removeParents` and only use `addParents`:

```python
drive.files().update(
    fileId=file_id,
    addParents=target_folder_id,
    # No removeParents
    supportsAllDrives=True
).execute()
```

If the API still returns `"Increasing the number of parents is not allowed"`, the folder is owned by another user and cannot be moved — fall back to copy or shortcut.

#### Phase 4: Batch operations by type

Group all operations and execute in order:

1. **Create folders** — batch all creates first (they don't depend on each other)
2. **Move folders** — each folder is one API call; report successes and failures
3. **Move files** — each file is one `files.update` call; group by bucket to track progress
4. **Rename after move** — rename files/folders after they reach their destination
5. **Verify empty** — re-list each source folder, confirm 0 items remain
6. **Trash empties** — only after confirming all content has been successfully relocated (recoverable 30 days)

```python
# Example execution pattern
results = []

# Create
legal_id = create_folder("01_Title_and_Legal_Opinions", rau_id)

# Move
try:
    f = drive.files().update(
        fileId=source_file_id,
        addParents=legal_id,
        removeParents=old_parent_id,
        supportsAllDrives=True
    ).execute()
    results.append(f"✅ Moved: {name} → 01_Title_and_Legal_Opinions")
except HttpError as e:
    if "not allowed" in str(e):
        results.append(f"⚠️ Cannot move {name} (owned by other user). Copying instead...")
        copy_file(source_file_id, legal_id, name)
    else:
        results.append(f"❌ Failed: {e}")
```

#### Phase 5: Report results

```
**✅ Completed (X of Y):**
- Created DRA Thindulu Land Partners (DTLP) under DRA Projects
- Moved DRA Projects / Ranka Udaya → DRA Projects / DTLP / Ranka Udaya
- Created 6 bucket folders under Ranka Udaya
- Moved 53 files → 01_Title_and_Legal_Opinions
- Moved 47 files → 03_Marketing_Collaterals
- Trashed 6 empty source folders (recoverable 30 days)

**⚠️ Blocked (ownership):**
- File X (id) — owned by other@example.com → shortcut created instead

**⏳ Pending (manual review):**
- File Y — needs user classification (vendor-side vs acquirer-side opinion)
```

## Pitfalls

- **Same survey number ≠ same property.** Sy No 93/2 exists in both Hurulugurki (Bangalore) and Bamnolim (Goa). Village name, not survey number alone, identifies the property.
- **Empty folders are intentional placeholders.** Don't delete them without asking.
- **Folder names change over time.** "Serenity Hill View" and "Godwad Bhavan Jain Trust Nandi Hills property" may refer to the same land — the project was renamed. "Serenity Estate" is the OLD name for Ranka Udaya — those files belong with Ranka Udaya.
- **Check root vs DRA Projects parent.** Some folders at Drive root, others under "DRA Projects". **If a project folder is at root, propose moving it under the canonical umbrella, not just into a new subfolder.**
- **Scattered entity docs.** Search for entity name as general file search, not just folder search.
- **The user wants links, not moves.** Until explicitly told, provide links for examination.
- **Multiple related folders for same trust.** A trust may have: (a) main legal folder, (b) active development folder with plans, (c) empty placeholder folder. Present all three.
- **DTLP umbrella rule.** All DTLP projects must live under `DRA Projects / DTLP / [Project] / [6 buckets]`. If you see a `Ranka Udaya` folder at My Drive root, that's a structural violation to fix.
- **Vendor-side vs acquirer-side opinions for same survey are NOT duplicates.** They cover the same property from different stakeholder angles. File both, label clearly.
- **Don't conflate entities.** SLP (Sevaganapalli Land Partners) covers the 158/166/167/168/176/177 series (Ranka Oasis). DRA Thindulu LP covers 240/3 (Ranka Udaya). Three different DRA entities for Sevaganapalli area — file opinions under the right project's bucket.
- **Don't stop at the obvious folder** — see section 1.5. Broad search typically multiplies scope by 2-3x.
- **Different DTLP projects are siblings, not the same project.** Ranka Udaya (240/3) and Thindulu Land (108/205/206) both belong under DTLP but as separate subfolders with their own 6-bucket structures.

## gws_skill_bridge drive_search Bug Workaround

**`gws_skill_bridge.call("drive_search", ...)` crashes** with `AttributeError: 'types.SimpleNamespace' object has no attribute 'raw_query'`. Use `gws_auth.build_service` directly:

```python
from tools.gws_auth import build_service

def drive_query(q, page_size=30):
    service = build_service("drive", "v3", service_name="google-draas")
    r = service.files().list(
        q=f"fullText contains '{q}' or name contains '{q}'",
        pageSize=page_size,
        fields="files(id,name,mimeType,parents,modifiedTime,md5Checksum,size,version,webViewLink),nextPageToken",
        supportsAllDrives=True, includeItemsFromAllDrives=True,
    ).execute()
    return r.get("files", [])
```

Also add `parents` and `md5Checksum` to the `fields` mask — both are critical for reorg tasks (you need to know where files live and detect duplicates).
