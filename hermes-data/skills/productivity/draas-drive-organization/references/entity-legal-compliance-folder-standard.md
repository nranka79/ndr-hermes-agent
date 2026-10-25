# Entity-level "Legal & Compliance" folder standard (NDR, 2026-09-18)

NDR's rule, dictated verbatim:

> *"We create one common Legal and Compliance folder under the entity level — not under projects.
> At folder level also, we create one other than projects."*

Projects keep their own ad-hoc `Legal` / `Legal Docs` / `Legal Notices` subfolders.
**Entity-level** legal (the firm's own statutory life) gets a dedicated `Legal & Compliance`
folder sitting alongside — never inside — the project folders.

## Canonical shape

```
BusDev > Bangalore > <Entity> > Legal & Compliance >
    NOC
    Registration & Registrar of Firms
    GST, PAN & TDS
    Statutory Notices
    Litigation
```

Level 1 = entity. Level 2 = `Legal & Compliance`. Level 3 = the five category folders above.

## Scope rule

| Document kind | Where it goes |
|---|---|
| Firm's own statutory life (NOCs issued to/for the entity, registrar filings, GST/PAN/TDS, notices served on the firm, litigation the firm is party to) | `<Entity> > Legal & Compliance > <category>` |
| Land/project-specific legal (title deeds, ECs, RTCs, DTCP sanctions, opinions on a survey number) | stays under the **project** folder, as today |

Entity-level legal is for **the firm**, not the land. Don't migrate project legal into it.

## Reference implementation — the entity pair

| Entity folder | ID |
|---|---|
| `BusDev` | `16P6CTecntuUompI9HmQ8RT9vCJIxftI2` |
| `BusDev > Bangalore` | `1oTbaqGWRYqC5JQAd00Lq63xdpxrXSoLV` |
| `DRA REN Development Partners` | `1lUcQR0Ulu8v5BroKZU9AyDLwxHbbU-4F` |
| `DRA KAAJ Development Partners` | `1jxTeU0PZWO7Ag_OYzTb3G-K_NazD-Vle` |

`Legal & Compliance` subfolders created 2026-09-18:

| Entity | Legal & Compliance | NOC | Registration & Registrar of Firms | GST, PAN & TDS | Statutory Notices | Litigation |
|---|---|---|---|---|---|---|
| DRA REN | `1XoHZn-Wc6PCaDo6slnSHh281Lq_nrqn6` | `1AtsICQVIWwYeknMbpP8CUSy4sOneU5go` | `1SEI9ITEzU6j3FkCpxI-esxzI4kRv5Az7` | `1OVb0O2oGBrYRMq_T4yEz3jgk4IjvnWwE` | `1oFTrWXv9aBoAGFZ4JtDGi_WXzHLmKzLX` | `1duESQQcXBMIGvBHYROMVajd5kJ88fAng` |
| DRA KAAJ | `11-FkAsrfZBoh4eZWXBWXefz5dysWE75e` | `1diHRbNOmfM1y_8LPzFBTzZaVfSwM-1Rj` | `1go7uRHJncMYCdq-RPcERCHJbxlQ-2wCU` | `17nYy-S9zDls4K1ccxPMyR17fiNt7wkk1` | `1IzxnWaW-HMXUkP70XwqVtdBuvvcK2zwB` | `1flbxfLTOUlMIMZeztdXa0BIrNcAK5Xpm` |

Idempotent create helper (safe to re-run; returns the existing ID if the folder is there):

```python
def mkfolder(drive, name, parent):
    ex = drive.files().list(
        q=f"name = '{name}' and '{parent}' in parents "
          f"and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id,name)", supportsAllDrives=True,
        includeItemsFromAllDrives=True).execute()
    if ex.get('files'):
        return ex['files'][0]['id'], False
    fid = drive.files().create(
        body={"name": name, "mimeType": "application/vnd.google-apps.folder",
              "parents": [parent]}, fields="id", supportsAllDrives=True).execute()['id']
    return fid, True
```

## ⚠️ Do NOT use the orphaned "Statutory Compliances" folder

There is exactly one folder literally named **`Statutory Compliances`**
(`1MB_k7vkEM3Q7vq6W6i0J8VOGy3cMy8Gu`, created 2020-09-25). It is **owned by a personal Gmail
account `manish8484447@gmail.com`** (display name "manish singh") — not a draas.com identity — it
has **no parent** (orphaned at root), and it holds only ITR / ITR 18-19 / Other Registration /
Annual Report / Annual Returns.

Verified **2026-09-18**. It is ungovernable (personal Drive, no company retention/sharing policy),
so treat it as unusable and never file DRA entity legal into it. If NDR asks "which Gmail owns it",
the answer is `manish8484447@gmail.com` — almost certainly **Manish Dinesh Ranka's** personal Drive,
distinct from his draas.com account.

## Worked example — the two Prizm Greystone NOCs (2026-09-18)

Both NOCs re-issued in Feroz Ahmed's name became the first tenants of the standard:

- `BusDev > Bangalore > DRA REN Development Partners > Legal & Compliance > NOC`
- `BusDev > Bangalore > DRA KAAJ Development Partners > Legal & Compliance > NOC`

The pre-existing ad-hoc `NOC` folders directly under each entity (old IDs `1XLeJx4vLcO8HJnwzL_fvJmVMbyfYV7yf`
and `1VCc8pwA6fIQm-AgLR0d-FP1JlcoUODt5`) were emptied by the move and then **deleted** — folder only,
no documents touched. `DRA Satvik Development Partners` needed renaming to `DRA REN Development Partners`
**and** relocating under `BusDev > Bangalore` (it had been sitting loose at My Drive root).

## Pitfalls

- **Entity folder names and locations drift — verify before assuming.** `DRA Satvik Development Partners`
  sat at Drive root and was the same entity NDR calls **DRA REN**. Always re-read the current name +
  parents rather than trusting a name from an earlier session. ("REN KAAJ" / "Ren-Kaj" = **REN KAAJ**,
  and note the voice alias **"Kaj" alone = DRA KAAJ**, a *different* firm.)
- **Old ad-hoc category folders are usually empty after a move — but verify before deleting.**
  List children first; delete only when the listing returns zero. Never trash a folder that still
  has items.
- **Keep a shortcut in the entity root.** NDR and Prakash navigate to the entity folder and expect
  the document at hand; a shortcut there costs nothing and preserves their muscle memory after a
  restructure. Shortcuts are `application/vnd.google-apps.shortcut`; read the target via
  `shortcutDetails.targetId` (the field `targetId` is **not** valid in a `files().list` `fields` mask —
  only `shortcutDetails` is).
- **Renaming a shortcut is a separate call from renaming its target.** After renaming a document,
  loop over its shortcuts and rename them too, or the folder shows the stale name. Full recipe
  (shortcut discovery via `shortcutDetails.targetId`, the `targetId`-is-not-a-valid-`fields`-mask
  trap): `rename-on-issuer-change.md`.

## Related

- `rename-on-issuer-change.md` — when the ISSUER in a document's filename goes stale (owner sold,
  firm renamed, lessor replaced), rename in place + rename the shortcuts. Naming convention
  `YYYYMMDD <Issuer> <DocType> - <Recipient>`.
