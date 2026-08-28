# Shareholder Agreement — Transfer / Gift Restriction Analysis

Use this workflow when Nishant asks about restrictions on transferring, gifting, or selling shares held in any family company (DRA Projects, DRA Developers & Projects, Southcity Properties, Mantri Techzone, etc.) to a third party (spouse, children, trust, or external buyer).

## Trigger Phrases
- "Can I gift my shares to my wife?"
- "Any restrictions in the SHA on transferring shares?"
- "What does the SHA say about gifting?"
- "Can I transfer shares to Roshni?"
- "Review the SHA for transfer blockers"

## Workflow

### 1. Find the SHA Documents on Drive

Search Nishant's Drive for the relevant company's SHA:

```python
drive = build_service('drive', 'v3')

# Search patterns — try all:
for term in [f"name contains '{company_name}'", "name contains 'Shareholder'",
             "name contains 'Share Transfer'", "name contains 'SHA'",
             "name contains 'Agreement'"]:
    results = drive.files().list(
        q=f"{term} and name contains '{year or '20'}' and trashed=false",
        fields='files(id, name, modifiedTime)'
    ).execute()
```

**Known locations for DRAAS family companies:**
- DRA Projects: "DRA Projects - Share Transfer Agreement v4 ndr 05JUN20" (Final Docs JUN2020 subfolder in Family folder) — Google Doc
- DRA Developers & Projects: "DRA Developers - Share Transfer Agreement v2" (Family folder) — Google Doc
- Southcity Properties: "Southcity Properties - Share Transfer Agreement v2" (Family folder) — Google Doc
- Mantri Techzone: "Mantri Techzone - Share Transfer Agreement Final 02JUN20" — **Deed of Gift**, not an SHA
- Consolidated PDF bundles also exist in "DR DDR Fmly Signed Docs" folder: `drap docs.pdf`, `dradp docs.pdf`, `scpl documents.pdf`

**Note:** Share Transfer Agreements from 2020 are typically Google Docs or .docx files stored under the "Family" folder or "Final Docs JUN2020" subfolder.

### 2. Read/Export the Document

For Google Docs:
```python
content = drive.files().export(fileId=doc_id, mimeType='text/plain').execute()
full_text = content.decode('utf-8')
```

For PDFs from "DR DDR Fmly Signed Docs", use text extraction.

### 3. Scan for These Specific Clauses

| What to look for | What it means for gift to spouse |
|---|---|
| **Parties list** | Are there only immediate family members (Dinesh, Kanta, 3 children) OR external parties (uncle Sanjeev, cousin Piyush, partnership entities)? External parties increase scrutiny. |
| **Transfer restriction clauses** | "No shareholder shall transfer..." — explicit block |
| **Right of First Refusal (ROFR)** | Must offer to existing shareholders first. If absent, no pre-emptive right. |
| **Pre-emptive rights** | Existing shareholders can buy the shares first — creates a delay even if ultimately allowed. |
| **Gift exception** | Some SHAs explicitly exclude gifts to "wife/husband/children" from transfer restrictions. |
| **"Permitted Transferee" definition** | If spouse is listed, gift is unrestricted. If not listed, transfer may trigger ROFR. |
| **Board/director approval requirement** | "transfer requires consent of Board/all directors" — usually routine but needs a resolution. |
| **Affirmative vote / unanimous consent matters** | Some decisions (new business, liabilities, guarantees) need ALL shareholders to approve. Share transfer is rarely in this list, but check. |
| **Tag-along / drag-along** | These apply to third-party sales, not gifts to family members. |
| **Ratio maintenance (inter-group)** | For JV companies (e.g., Mantri Techzone with Pai Group 65:35), any inter-se change within the Ranka group must maintain the overall group ratio. This can block or complicate gifts. |
| **Authorization clause** | Who is authorized to represent the shareholder? Dinesh Ranka often holds this authority. Gifting may require his sign-off. |

### 4. Also Check (Beyond the SHA)

- **Company's Articles of Association (AoA)** — governs share transfers for ALL private companies. SHA supplements AoA; AoA may have additional restrictions.
- **Companies Act, 2013 Section 56** — share transfer requires a proper instrument of transfer, stamp duty, and board approval.
- **Income Tax Act — Gift to Spouse** — gift to spouse is exempt from gift tax, but income from gifted shares may be clubbed with the transferor's income under Section 64(1)(iv).
- **Private Company Restrictions** — AoA of a private company typically restricts the right to transfer shares and limits the number of members.

### 5. Presentation

Present the answer as a table per company:

| Company | SHA Blocker? | Board Resolution Needed? | Catch |
|---------|-------------|-------------------------|-------|
| DRA Projects | ❌ No | ✅ Yes — routine | None |
| DRA Developers | ❌ No | ✅ Yes — routine | Uncle/cousin are shareholders |
| Southcity Properties | ❌ No | ✅ Yes — routine | DRA Investments (entity) is shareholder |
| Mantri Techzone | ⚠️ Maybe | ✅ Yes | 65:35 Pai/Ranka JV ratio must be maintained |

**Format:** Mention each company separately. Lead with the conclusion (blocked or not), then detail the specific clauses.

### 6. Known Pitfalls

- **SHA may not be the only governing document.** For JV companies like Mantri Techzone, there's typically a separate SHA between the joint venture partners (Pai Group and Ranka Group) that governs cross-entity transfers. Find and read that too.
- **"Share Transfer Agreement" ≠ "Shareholders Agreement".** Some documents in the Drive are specifically Share Transfer Agreements (recording a specific past transfer) combined with some SHA-like governance clauses. Check the title and scope.
- **Gift Deeds vs SHAs.** For Mantri Techzone, the governing document is a Deed of Gift (Dharmesh → Nishant/Manish/Mamata), not an SHA. The restriction in that Gift Deed is the 65:35 ratio agreement, not standard SHA language.
- **Document dates matter.** The 2020 documents may have been superseded by later amendments (e.g., "Addendum to DRAP SHA 03-07-2020 dt 06-08-2025"). Always check for addenda/amendments.
- **Current shareholding may differ from Schedule A in the SHA.** SHA schedules show shareholding at the time of signing. Current holdings may be different, which affects the analysis of blocked percentages.
