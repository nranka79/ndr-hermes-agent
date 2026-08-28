# Document Version Chronology via Drive Metadata

When a project has multiple files (master plans, inventory sheets, layout drawings) from different dates, it's critical to build a timeline to spot version mismatches. DRAAS projects often have files created by architects (bk@findingform.design), shared to ndr@draas.com, and re-uploaded by sales1.blr — each in different folders with different dates.

## The Technique

Use the Drive API `files().get()` and `files().list()` to fetch `createdTime`, `modifiedTime`, and `owners` for every relevant file, then build a chronological timeline.

### Key metadata fields

```python
svc.files().get(fileId=ID, fields='id,name,createdTime,modifiedTime,owners,size').execute()

svc.files().list(
    q="name contains 'Oasis Master Plan'",
    fields='files(id,name,createdTime,modifiedTime,mimeType,size,owners)'
).execute()
```

| Field | What it reveals |
|-------|----------------|
| `createdTime` | When the file was first created (author's original) |
| `modifiedTime` | Last modification (may differ from created if revised) |
| `owners` | Which account owns the file — critical for cross-account sharing understanding |
| `mimeType` | `.pdf`, `.dwg`, spreadsheet — tells you which tool produced it |

### Real example — Ranka Oasis version mismatch

The Oasis Master Inventory Sheet was **created 24 May 2026**, but the Master Plan PDFs were **created 4 Jul 2026** — a 6-week gap. This explained why the plot numbering in the inventory sheet didn't match the plan.

**Cross-account owner insight:**
| Owner | Files | Implication |
|-------|-------|------------|
| `bk@findingform.design` (architect) | Inventory sheet, master plan PDFs, DWG | Files shared *from* his account — appear individually in Drive, not in a folder |
| `ndr@draas.com` | Approved plan drawing, sale deeds | Your copies — fully writable |
| `sales1.blr@draas.com` | DTCP layout, sanction docs | Uploaded by Bharat — check permissions |

### Presenting the timeline

Format as a chronological table — oldest first — with a clear note on the gap/discrepancy:

```
| Document | Date | Owner |
|----------|------|-------|
| DTCP Layout Plan | 13 Jan 2026 | sales1.blr |
| Approved Plan Drawing | 30 Mar 2026 | ndr |
| 📊 Inventory Sheet CREATED | 24 May 2026 🟡 | bk@findingform.design |
| 📐 Master Plan PDF | 04 Jul 2026 🟢 | bk |
| CAD Drawing | 07 Jul 2026 | bk |
| Inventory Sheet LAST MODIFIED | 13 Jul 2026 | bk |

⚠️ Gap: Inventory sheet (May 24) is 6 weeks older than master plan (Jul 4).
    Different layout iterations → numbering won't match.
```

### When to use this

- **User says "the numbering doesn't match"** between two project documents
- **Multiple versions** of plans/inventory sheets from different dates
- **Cross-account confusion** — user can't find files because they're owned by an external account and not in a shared folder
- **Due diligence** — establishing which document is the latest/final version before acting on it

### Pitfalls

- **`modifiedTime` can be earlier than `createdTime`** — this happens when files are copied/moved. The `createdTime` is the authoritative creation timestamp.
- **`fullText contains` won't search inside `owners`** — use separate queries per owner email or per project name variant.
- **Name-based queries are case-insensitive** but search operators differ between Drive API (`name contains`) and gws CLI.
- **Files shared externally** (owned by `bk@findingform.design`) don't appear in your Drive folder tree — they show up as individual shared items in search. This is why the user can't "find them in [their] Drive".
