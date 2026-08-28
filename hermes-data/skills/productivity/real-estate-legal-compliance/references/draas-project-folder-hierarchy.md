# DRAAS Project Folder Hierarchy — Drive Organization

**Convention for organizing DRAAS real estate projects on Google Drive.**
Based on user correction during Ranka Stelo / AHFL reorganization (Jun 2026).

## Core Principle: Parent Company > Project

The hierarchy flows from **parent company (entity)** down to **project name**, NOT the reverse.

### Correct

```
AHFL (parent company)
└── Ranka Stelo (project under AHFL)
    ├── Legal
    ├── Sale Deeds
    ├── Project Docs
    ├── Plans & Drawings
    ├── Approvals (RERA, Bank, NOCs)
    ├── CRM
    ├── Engineering
    ├── Marketing
    └── Procurement
```

### Wrong (what was found in existing structure)

```
RANKA STELO (top level)
└── AHFL (subfolder) ← wrong — company should parent the project, not vice versa
    ├── Internal
    ├── Legal
    ├── Marketing
    ├── Purchase
    └── Work
```

## Application to Other Projects

Apply the same principle to all DRAAS entities:

| Parent Company | Project Folder(s) |
|---------------|-------------------|
| AHFL (Associated Housing Finance Ltd) | Ranka Stelo, etc. |
| DRA Realty Pvt Ltd | Ranka Amber, Ranka North Star, etc. |
| DRAAS | Direct projects |

## Where Projects Live (Current State)

Projects may be split across two structural locations on Drive:

1. **Dedicated top-level folder** named after the parent company — holds company-level folders like AHFL, Architect, Engineering Solutions, PMC
2. **Under `Current Properties`** — holds project-specific subfolders (Stelo, with CRM, RERA, Plans, DHARWAD PROJECT DOCUMENTS)

**Target state:** Consolidate all project materials under the parent company folder.

## Common Issues Found During Reorganization

- **Duplicate files**: Same file appearing in both `AHFL > Work` and `Stelo > root`
- **Empty folders**: Bank Approvals, CRM, GFC Drawings, Inspections, Procurement, RERA, Schedule subfolders are often empty
- **Duplicate working folders**: Multiple `WORKING FILES` and `WORKING FOLDER` dirs under same parent
- **Loose root-level files**: 50+ files directly in project root — move into category subfolders

## When to Use This Convention

- Organizing scanned document indexes (e.g., "Index of Documents for DHARWAD Property")
- Creating or restructuring project folders for RERA submission
- Filing legal documents (sale deeds, agreements, NOCs) for any DRAAS project
- Mapping existing folder structures before proposing reorganization
