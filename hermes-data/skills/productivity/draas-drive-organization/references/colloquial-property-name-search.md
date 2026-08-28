# Finding Properties by Colloquial Name on DRAAS Drive

## The Problem

Users often refer to properties by **colloquial names** that don't appear anywhere in Drive filenames or folder names. For example:

| User Says | Actual Legal Name |
|---|---|
| "Devraj Holiday Village" | **6A Holiday Village Road, Mallasandra Village, Kanakpura Road** — 6 acres 3 guntas |
| "Serenity Hill View" | Survey No. 92/3, Hurulagurki, Devanahalli |

A direct Drive search with the colloquial name returns zero or irrelevant results.

## The Solution — Family Settlement Document Cross-Reference

DRAAS properties derived from the Dinesh Ranka estate are catalogued in **family settlement documents** that list every asset by its formal legal description. These are the cross-reference key.

### Step 1: Search Family Settlement Documents

Search for these specific documents on Drive — they contain **Schedule A** or **Schedule B** asset lists:

| Document to Search | Why |
|---|---|
| **DR Schedule A & B Assets List** | Master list of all Dinesh Ranka estate assets with full legal descriptions, sizes, and locations |
| **Global Settlement between DR Heirs** | Lists how each asset is divided among heirs; often has more detailed legal descriptions |
| **DR - WILL Final [date]** | The will itself — lists properties with survey numbers, village names, and acreages |
| **MoU Asset Distribution Agreement** | Asset distribution with formal legal names |
| **Family Arrangement Deed** (e.g. `20250629 FINAL DR - KDR DDR NDR MDR MRR FAMILY ARRANGEMENT DEED`) | Latest family settlement |

**Search query pattern:**
```python
# If you know part of the colloquial name (e.g., "Devraj", "Holiday Village")
results = service.files().list(
    q="fullText contains 'Holiday Village' and name contains 'Schedule'",
    spaces='drive',
    fields='files(id, name)'
).execute()

# Or search within known family settlement docs
doc_ids = [
    '1fNuTFMioA_KgtxFTD-VoLjz6a2vfY5Fk5y3UAP1j4HA',  # DR Schedule A&B
    '1Ou4eao8IZFKGFPy294AaRNujeJ7q3aKRwl5TZBKLbuE',   # Global Settlement
]
for doc_id in doc_ids:
    content = service.files().export(fileId=doc_id, mimeType='text/plain').execute()
    text = content.decode('utf-8-sig')
    for line in text.split('\n'):
        if any(kw in line.lower() for kw in ['holiday', 'kanakpura', 'mallasandra']):
            print(line)
```

### Step 2: Extract the Formal Legal Name

From the settlement document, extract the full legal property description. The Schedule A format typically looks like:

> **6A Holiday Village Road - Kanakpura Road** - All that 50% right, title and interest in property at **Mallasandra Village**, admeasuring **6 acres and 03 guntas** situated off Kanakpura Road on Holiday Village Road – sale agreement in the name of **Dinesh Ranka**.

Key fields to extract:
- **Street address** (e.g. "6A Holiday Village Road")
- **Village** (e.g. "Mallasandra")
- **Road/location** (e.g. "Kanakpura Road")
- **Size** (e.g. "6 acres 3 guntas")
- **Owner** (e.g. "Dinesh Ranka — 50%")
- **Counterparty** (e.g. "Dayananda Pai — 50%")

### Step 3: Search Drive with the Formal Name

Now use the formal address/village name to find actual documents:

```python
# Search by village name + property terms
service.files().list(
    q="fullText contains 'Mallasandra' and (name contains 'Pai' or name contains 'agreement')",
    spaces='drive'
).execute()

# Search by road/street name
service.files().list(
    q="name contains 'Kanakpura' and mimeType contains 'pdf'",
    spaces='drive'
).execute()
```

### Step 4: Check Both Parties' Documentation

The property may involve:
- **Dayananda Pai / Pai Group** (counterparty — e.g., Century Real Estate)
- **M Devraj / Devaraj** (original seller)
- **Dinesh Ranka** (the estate owner)

Documents may be filed under any of these names. The **Kanakpura Property** folder (`1rUek0mMGnH2U8z3BgUMTTx4RsAn3BVD6`) is a common repository for Pai-Devraj-Ranka property docs.

## Pitfalls

- **No direct folder for the colloquial name.** "Devraj Holiday Village" has no folder or file on Drive — the actual docs are in "Kanakpura Property" folder and the formal name is in family settlement documents only.
- **"Devraj" can be confusing.** It could refer to: (a) M Devraj — the original seller of the Kanakpura property, (b) Devraj H. Ranka — Nishant's grandfather, or (c) Devraj Holiday Village — the colloquial name. Use full legal names from settlement docs to disambiguate.
- **Separate properties by the same parties.** Dinesh Ranka / Dayananda Pai had multiple business relationships: (1) Pernem Goa JDA (386 acres, being cancelled, ₹11 Cr refund), (2) Holiday Village Road Kanakpura (6 acres, 50:50 profit share/JDA). Don't mix them up — use the legal description to keep them straight.
- **Property size semantics.** The user may say "6 acre" — the record may say "6 acres 3 guntas" (1 gunta = 0.0247 acres, so 6.074 acres). Be specific when discussing with the counterparty.
