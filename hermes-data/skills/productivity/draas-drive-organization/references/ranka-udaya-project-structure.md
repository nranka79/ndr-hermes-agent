# Ranka Udaya — Drive Folder Structure

Ranka Udaya (DRA Thindlu Land Partners project, Sevaganapalli village, Krishnagiri dt., Pakalur SRO) has **multiple Drive folders with the same name, owned by different accounts**. Uploading to the wrong one fails 403.

## Folder Map

| Folder Name | ID | Owner | canAddChildren | What it holds |
|---|---|---|---|---|
| **Ranka Udaya** (CANONICAL) | `1sdDX5htwSKF2SSe_re-jjYb-8SsFCk8Z` | **ndr@draas.com** | ✅ True | Numbered 01–06 taxonomy: 01_Title_and_Legal_Opinions, **02_Approvals**, 03_Marketing_Collaterals, 04_Sanction_Drawings, 05_Execution_Documents_and_Drawings, 06_Customer_Documents |
| Ranka Udaya (marketing) | `129WGpGKBCE12ZqobdQj4CCT5Nxdc1Fgc` | BK@fnw.homes | ❌ False | Marketing collaterals, brochures, posters, flex, hoarding, sunpack, video (see `marketing-collateral-lookup` ref) |
| Ranka Udaya (DRA Tindlu Land partners Master Folder) | `10sk0X6dq9-Rzo2BajJKNFkEts_pfRxLT` | sales1.blr@draas.com | ✅ True | Bharat's master folder — use when NDR says "put it in the master folder" |
| Ranka Udaya (other) | `1QXJ_ZxFiOl0WyL8Y-ERiUWeARDLhMazF` | sales1.blr@draas.com | ✅ True | Legacy / alternate |
| Ranka Udaya (other) | `1QlnjLpvjlL-lHNTRx6EvTmkITjPBRlGs` | bk@findingform.design | ❌ False | Read-only |
| Ranka Udaya (other) | `1sdDX5htwSKF2SSe_re-jjYb-8SsFCk8Z` | ndr@draas.com | ✅ True | (same as canonical above) |

## Canonical Approvals Folder

`02_Approvals` subfolder inside the canonical ndr-owned folder:
- ID: `1EsCJ0GOdDC37mZzyUlpl2-IEZZ_NcvRl`
- Link: `https://drive.google.com/drive/folders/1EsCJ0GOdDC37mZzyUlpl2-IEZZ_NcvRl`
- Upload guideline value orders, RERA registrations, sanction letters, NOCs, and other approval documents here.

## Upload Pitfall (verified 2026-09-08)

**Uploading to the first "Ranka Udaya" hit by name → 403 `insufficientParentPermissions`.** The name-search returns the marketing folder (BK@fnw.homes, read-only) first. Always check `owners[0].emailAddress` and `capabilities.canAddChildren` before uploading:

```python
f = svc.files().get(fileId=candidate_id, fields="id, name, owners, capabilities(canAddChildren)").execute()
if not f.get('capabilities', {}).get('canAddChildren'):
    raise ValueError(f"Folder {f['name']} is read-only (owner {f['owners'][0]['emailAddress']})")
```

After upload, verify:
```python
verify = svc.files().get(fileId=uploaded['id'], fields="id, name, parents, owners").execute()
assert verify['owners'][0]['emailAddress'] == 'ndr@draas.com', "Not owned by ndr"
```

Set `anyone` reader permission for shareable links:
```python
svc.permissions().create(fileId=uploaded['id'], body={'type': 'anyone', 'role': 'reader'}).execute()
```

## Subject Matter

Ranka Udaya is a residential layout at **Sevaganapalli village, Pakalur SRO, Krishnagiri district**. Survey No. 240/BA-2, Residential Grade-I Type-D.  
Guideline value order: File No. 6414/A3/2026, dated 8.9.2026, District Registrar (Administration), Krishnagiri — filed in `02_Approvals`.