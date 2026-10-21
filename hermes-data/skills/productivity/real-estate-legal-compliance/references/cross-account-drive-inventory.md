# Cross-Account Drive Inventory & Bucket Mapping (verified 2026-09-15/17)

Use when the user asks you to scan **multiple colleagues' Google Workspace drives**
for everything related to one project, build a master inventory, and then map each
file into a target folder taxonomy. Classic trigger: *"scan the drives of A, B, C
and D, find all Ranka Oasis files, and build a master inventory sheet in my Drive
with the full folder chain, type, and what each file is about."*

Worked example: Ranka Oasis across 5 colleague drives → 3,151 unique items.

## Resolving the people to accounts first

Names are ambiguous and voice/transcription errors are common. Resolve BEFORE
scanning:

- `contact_resolver` / `entity_resolver` are the sanctioned tools. **They can fail
  with a 500 in some sessions** — if they do, fall back to (a) `session_search`
  over prior tracker/roster sessions, which reliably names the person↔email mapping,
  and (b) the DWD domain probe below to confirm the address is real.
- **The real existence test for a Workspace account is a cheap `drive_list`
  impersonation probe, not a name lookup.** `invalid_grant` = the address does not
  exist; `unauthorized_client` = the address may exist but is not impersonatable
  under the current DWD config. Do not trust fuzzy name matching — it
  pattern-matches anything to something.
- Confirmed DRAAS roster used here: Bharat Hawaldar = `sales1.blr@draas.com`;
  Bhagya G = `crm.blr@draas.com`; Anbarasan (Anbu) = `pm2.blr@draas.com`;
  Sinchana Gowda = `sgowda@draas.com`; Kantesh B G = `kanteshbg@draas.com`.

## Scanning: three query classes, always paginated

Run all three per account and union the results by file ID:

1. `name contains 'Oasis'` and `name contains '<project>'` (folder + file names)
2. `fullText contains '<project>'` (catches content mentions)
3. **Recursive walk of every matched FOLDER** — name hits alone miss the loose
   files inside a matched folder. This is where most files come from.

```
svc.files().list(q=..., pageSize=200,
                 fields='files(id,name,mimeType,parents,owners,webViewLink,size,modifiedTime)',
                 supportsAllDrives=True, includeItemsFromAllDrives=True,
                 corpora='allDrives').execute()
```

**Pitfall — `includeItemsFromAllDrives` is INVALID on `files().get`.** It is only a
`files().list` parameter. On `.get` it raises and kills every parent lookup, which
silently produces a sheet with empty folder chains. Use **`supportsAllDrives=True`
only** on `.get`. This one bug invalidated ~5,500 parent-chain lookups before it was
caught.

**Pitfall — a colleague's token cannot resolve parents of files they merely have
shared with them.** If a file is owned by `ndr` and only shared to `sales1.blr`, the
`sales1` token returns no parent for it. Therefore: resolve the chain **from the
OWNER's token**, then dedupe by file ID. Concurrency: 5 drives × thousands of items
takes minutes — run it with `background=True, notify_on_complete=True` and persist
each account's JSON to disk as it finishes, so a session death doesn't lose the run.

## Building the inventory rows

Dedupe by **file ID** (not name — the same deed genuinely lives in 2+ drives under
different names: `X.pdf` and `Copy of X.pdf`). Then:

- Walk `parents` up to the drive root to build the **full chain from "My Drive"**.
  The user asked for the whole sequence root→folder, so emit it as a joined path.
- Add an **"Also Found In"** column listing every other account that can see the
  file. ~1,685 of 3,151 files were visible to 2+ accounts. This is what tells the
  user which copies are redundant before consolidation.
- Record the **owner account + owner email** — this, not the scanning account,
  determines who has to transfer ownership later.

## Descriptions matter more than anything else here

The user's words: *"what is it about? That's important."* A filename echo is a
failed description. Tiered approach that worked:

1. **Google Docs/Sheets → read the actual content** (first paragraphs / first
   cells) and quote what it is. E.g. the Jiraaf term sheet descriptions quoted its
   real clauses.
2. **Parse structured filenames** — `OASIS-EAST 1800 T3.pdf` → "East-facing 1800
   sqft, Type 3 villa plan".
3. **Fall back to path context** (parent folder name) for plan/render folders.
4. **Content-check the junk-named ones** (123.pdf, padf.pdf, etc.) — a handful of
   these turned out to be referral-agent affidavits and a PO. Do not guess from the
   name; open them.
Flag any description that is still just a filename echo and say so, rather than
pretending it's classified.

## Bucket mapping (the second phase)

When asked "does our N-folder structure suffice?", the answer requires actually
classifying every row and letting the leftovers speak:

- Write a **multi-pass classifier** over filename + description + folder chain, with
  explicit priority (name rules > description rules > chain fallback).
- **Chain fallback is dangerous.** A `sale deed`-keyword rule fed by folder names
  pulled birth certificates and cancellation deeds into the Legal bucket. Make chain
  rules require keyword match AND exclude mismatched doc types.
- **Plural variants break naive regexes** — `floor plan` vs `floor plans`, `sale deed`
  vs `sale deeds`. Missing plurals dumped 188 rows into an unresolved bin.
- **Watch for greedy high-priority buckets.** An `allotment|allocation` pattern pulled
  the Customer rows into Title; the fix is to check the project archetype (a villa
  project's plot allotment to named buyers IS Customer).
- **Always surface a NOT-<PROJECT> bucket.** 135 of 3,151 files surfaced only because
  "Oasis" appeared somewhere in unrelated content (a land brief mentioning "Brigade
  Oasis" as a neighbouring project). These must be tagged so the consolidation phase
  leaves them alone.
- Deliver the verdict as: existing buckets + counts, NEW buckets the data demands
  with counts and one-line justification each, and the NOT-project exclusions. Then
  recommend final bucket names matching the entity-level taxonomy so the two levels
  line up.
- **Bug that cost real time:** an overrides branch returned the string `'FILE'` in a
  boolean slot, making every row truthy → all rows became FOLDER. Verify the
  classifier's kind field on a sample before writing 3,000 rows to a sheet.

## Delivery

- Write the inventory to a Google Sheet in the user's OWN Drive, then read it back
  and confirm row count + that links render before reporting done.
- Report per-owner and per-type breakdowns alongside the total — that is what drives
  the next phase (ownership transfer + shortcuts back into colleagues' folders).
