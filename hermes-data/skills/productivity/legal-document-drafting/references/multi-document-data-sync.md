# Multi-Document Data Sync — Legal Document Sets

When a data point (villa plan specs, pricing, party details, project name, FSI) is referenced across multiple documents in a legal document set, EVERY document must be updated — not just the primary one.

## Common DRAAS Document Sets

| Document | Primary Content | Plan Data Location |
|----------|---------------|-------------------|
| **Agreement for Sale** (standalone) | Plot/land conveyance only | Schedule A (plot description only — no villa data) |
| **Construction Agreement** (standalone) | Build terms, villa specs | Schedule C (BUA/carpet table, room config tables, FSI, drawing refs), Recital G (summary paragraph) |
| **Combined AoS + Construction** | Merged sale + build | Schedule B (villa description paragraph), Recital I (WHEREAS clause mentioning BUA) |

## Steps When Updating Villa Plan Data

### 1. Construction Agreement (standalone)

Update these elements:

- **Recital G**: BUA (~2,689 sq.ft), Carpet (~1,775 sq.ft), FSI, drawing numbers, architect
- **Schedule C sub-section A** (Built-up/Carpet Breakup table): Floor-wise BUA and RERA Carpet values
- **Schedule C sub-section B** (Room Configuration tables): Room names, dimensions, areas per floor
- **Schedule C sub-section C** (Summary table): Bedrooms, toilets, parking, floors, lift
- **FSI line** (between sections A and B)

### 2. Combined Agreement

Update these elements (different locations than Construction Agreement):

- **Schedule B** (villa description paragraph): Floor count (G+2), BHK (3BHK), BUA (~2,689 sq.ft), Carpet (~1,775 sq.ft), FSI (1.83), drawing numbers, architect name
- **Recital I** (WHEREAS clause): The "having a Build-up area of [ ] sq. ft." reference

### 3. Verify Both

```python
# For paragraph text (Combined Agreement):
from tools.gws_skill_bridge import call as gws
result = gws("docs_get", service_name="google-draas", doc_id="DOC_ID")
for kw in ["2,689", "1,775", "1.83", "G+2", "3BHK", "Anest Raj"]:
    if kw in result:
        print(f"✅ {kw}")

# For table data (Construction Agreement):
from tools.gws_auth import build_service
service = build_service("docs", "v1", service_name="google-draas")
doc = service.documents().get(documentId="DOC_ID").execute()
# Iterate body.content for table elements
# See google-workspace-api → references/docs-batch-update.md → "Verifying After Update"
```

## Pitfalls

1. **Section numbering differs**: Construction Agreement uses Schedule C for villa specs; Combined Agreement uses Schedule B for the same type of data. Don't assume the same section label.
2. **Recital letter differs**: Construction Agreement's plan reference is in Recital G; Combined Agreement's is in Recital I.
3. **Table data invisible to text search**: The bridge's `docs_get` returns paragraph text only. Table cell content is in the JSON structure under `table.tableRows[].tableCells[].content[]`.
4. **Combined Agreement has no standalone villa tables**: It has a single paragraph description in Schedule B, not the detailed floor-by-floor room tables that the Construction Agreement has.
