# Deed of Declaration Analysis Under Karnataka Apartment Ownership Act, 1972

## Project Context
A Deed of Declaration (DOD) in Form A is the foundational document that submits a property to the Karnataka Apartment Ownership Act, 1972 (KAOA). It establishes individual apartment ownership, defines common areas, creates the Owners Association, and sets maintenance rules.

## Verification Workflow

### Phase 1: Research (Parallel)

Use `delegate_task` with two parallel research streams:

1. **KAOA Act Requirements** — Research all mandatory DOD contents per these sections:
   - Section 2: Submission to Act via registered DOD in Form A
   - Section 3: Definitions (apartment, common areas, association)
   - Section 4: MANDATORY DOD contents (8 elements)
   - Section 5: Common areas & facilities definition
   - Section 6: Undivided interest in common areas (carpet area basis)
   - Section 9: Bye-laws (Form B) mandatory provisions
   - Section 10: Association powers as body corporate
   - Section 11: Board of Managers (min 3) + Agent for Service
   - Section 13: Common expenses proportional to UDI
   - Section 14: Statutory lien for unpaid assessments

2. **Practical Research** — Search for:
   - Reddit: r/indianrealestate, r/bangalore, r/LegalAdviceIndia
   - Indian Kanoon case law on DOD disputes
   - Common builder trap clauses
   - Parking rights disputes under KAOA
   - Association formation delays and handover issues

### Phase 2: GPT 5.5 Compliance Analysis

Feed both research outputs + full DOD text into GPT 5.5 (via OpenRouter) asking for:

1. **Compliance Checklist** — 30+ requirement table marked PRESENT / PARTIALLY PRESENT / MISSING / NON-COMPLIANT with KAOA section references
2. **Correct Items** — What the DOD does well
3. **Issues & Gaps** — Each issue must include: what's wrong, relevant Act section, risk, and suggested fix wording
4. **Critical Priority** — Must-fix-before-registration vs best-practice improvements
5. **Bye-laws Review** — Against Section 9 requirements
6. **Recommendations** — Priority-ordered action items

### Phase 3: Analysis Document Creation

Create a Google Doc in the same folder as the DOD:
```python
doc = docs.documents().create(body={'title': 'YYYYMMDD_Project_DOD_Analysis_GPT55'}).execute()
# Move to target folder
drive.files().update(fileId=doc_id, addParents=folder_id, removeParents='0AF...').execute()
# Write content in a single insertText
service.documents().batchUpdate(documentId=doc_id, body={'requests': [{
    'insertText': {'location': {'index': 1}, 'text': content}
}]}).execute()
```

## 37-Point Compliance Checklist

| # | Requirement | KAOA Reference | Notes |
|---|-------------|---------------|-------|
| 1 | Property submitted to KAOA via registered DOD | Section 2 | Registration pending = ineffective |
| 2 | DOD executed by sole owner or all owners | Section 2 | If units sold, buyers may need to join |
| 3 | Correct legal description of land | Section 4 | Survey no, boundaries, extent |
| 4 | Title history / acquisition details | Form A | Sale deed refs, encumbrance disclosure |
| 5 | Building description: floors, units, layout | Section 4 | Basements, floors, total units |
| 6 | Sanctioned plan & approvals annexed | Form A | Plan, CC, OC must be attached |
| 7 | Occupation Certificate details | BBMP/RERA | Verify date is correct |
| 8 | Each apartment: number, floor, carpet area, boundaries | Section 4 | **CRITICAL** — Annexure must be complete |
| 9 | Number of apartments and types stated | Section 4 | 12 units, all 3BHK (example) |
| 10 | EXACT % undivided interest per apartment | Section 6 | **CRITICAL** — Must be expressed |
| 11 | UDI computation method stated | Section 6 | Carpet area / total carpet area × 100 |
| 12 | Common areas fully listed | Section 5 | Match statutory definition |
| 13 | Basements as common/limited common | Section 5 | Cannot exclude basements |
| 14 | Clubhouse as common amenity | Section 5 | Not for sale, no exclusive title |
| 15 | Restricted/limited common areas identified | Sections 5, 6 | Parking, terrace clearly defined |
| 16 | Common areas not partitionable | Section 6 | Standard non-partition clause |
| 17 | Common expenses proportional to UDI | Section 13 | NOT super built-up area |
| 18 | No owner exempt by non-use | Section 13 | Standard waiver clause |
| 19 | Statutory lien for unpaid assessments | Section 14 | Priority over other charges except tax |
| 20 | Use restrictions (residential only) | Sections 4, 9 | Residential, no commercial |
| 21 | Bye-laws annexed | Section 9 | Exhibit B — full text required |
| 22 | Board of Managers (min 3) | Section 11 | Election, term, powers |
| 23 | Agent for service of process | Section 11(1)(h) | Must designate person in Karnataka |
| 24 | Insurance provisions | Section 9 | Building, fire, public liability |
| 25 | Sinking fund / reserve fund | Section 9 | For major repairs & replacements |
| 26 | Encumbrances disclosed | Section 4 | Mortgages, litigation, tax dues |
| 27 | Amendment mechanism | Section 6, 9 | 75%? 2/3? Unanimity for UDI changes? |
| 28 | No waiver of statutory defect liability | RERA Sec 14(3) | Can't contract out of defect period |
| 29 | Sale deed consistency with DOD | KAOA practice | Cross-reference RERA disclosures |
| 30 | Correct execution & corporate authority | Registration Act | Board resolution date, signatory authority |
| 31 | Complete annexures & plans | Form A | All schedules must be filled |
| 32 | Parking schedule / allocation | Section 5 | Each space allocated to apartment |
| 33 | Handover obligations listed | Practice | Documents, equipment, AMCs, warranties |
| 34 | Promoter pays for unsold units | Practice | Must pay maintenance like any owner |
| 35 | Voting rights: equal vs proportional | Section 10 | Align with UDI or one-vote-per-equal-unit |
| 36 | Dispute resolution preserves RERA/courts | Section 9 | Arbitration cannot bar statutory remedies |
| 37 | Audit & account transparency | Section 9 | Annual CA audit, inspection rights |

## Common Critical Issues Found in DOD Drafts

### 1. Empty Annexure-1 (Apartment Schedule)
**Risk:** Registration rejection, UDI disputes, maintenance calculation chaos.
**Fix:** Complete with apartment number, floor, carpet area, boundaries, parking, UDI %.

### 2. "Exact UDI percentage not expressly mentioned"
**Risk:** Direct violation of Section 6. Common area ownership ambiguous.
**Fix:** DELETE that phrase. Calculate UDI as: (Carpet Area of Apt / Total Carpet Area) × 100.

### 3. Super Built-up Area Used for Maintenance
**Risk:** Owners challenge if super built-up is opaque or inflated.
**Fix:** Replace with "percentage of undivided interest" per Section 13.

### 4. Basements Excluded from Development
**Risk:** Contradicts Section 5 — basements contain parking, services, fire systems.
**Fix:** Delete exclusion. Declare basements as restricted/common areas.

### 5. Builder Retention of Unallotted Parking
**Risk:** After submission to KAOA, all areas vest in Association. Parking dispute = #1 Bangalore issue.
**Fix:** Unallotted parking vests in Association for visitor/common use.

### 6. Basement Seepage Defect Waiver
**Risk:** Likely unenforceable under RERA Section 14(3) — builder cannot contract out of structural defect liability.
**Fix:** Association handles routine maintenance; Promoter handles structural/construction defects during defect liability period.

### 7. OC Date Errors
**Risk:** Regulatory rejection, buyer suspicion.
**Fix:** Verify against actual OC document.

## Bye-Laws (Exhibit B) — Section 9 Compliance Checklist

Must verify these bye-law contents are present:
- [ ] Association name and registered office
- [ ] Automatic membership for all apartment owners
- [ ] Board of Managers: min 3, elected, term specified, removal procedure
- [ ] AGM and Special GM: frequency (annual), notice period, quorum, agenda
- [ ] Voting and proxy aligned with KAOA
- [ ] Common expense assessment: UDI-linked, due dates, late fees
- [ ] Collection, recovery, and lien enforcement procedure
- [ ] Maintenance of common areas (lifts, fire, pumps, basements, terrace, clubhouse)
- [ ] Sinking fund for major repairs (min 10% of maintenance)
- [ ] Insurance: building, fire, public liability, equipment
- [ ] Books of accounts and annual CA audit
- [ ] Fiscal year (1 April – 31 March)
- [ ] Use restrictions matching the DOD
- [ ] Tenant/occupant obligations (owner liable for tenant compliance)
- [ ] Damage/reconstruction procedure after fire/natural disaster
- [ ] Bye-law amendment process (75% or as per Act)
- [ ] Dispute resolution (mediation/arbitration — preserve RERA/consumer/civil remedies)
- [ ] Promoter liability for unsold apartment maintenance
- [ ] No promoter veto/nomination rights after handover
- [ ] Parking regulation per parking schedule
- [ ] Clubhouse usage rules (booking, charges, damage liability)

## Verifications After DOD Registration

- [ ] Cross-verify DOD against all sale deeds (UDI %, parking, carpet area must match)
- [ ] Cross-verify against RERA registration (carpet area, common amenities, plans)
- [ ] Confirm DOD is REGISTERED (stamp duty paid, sub-registrar seal)
- [ ] Confirm mortgagee NOC obtained if property was encumbered
- [ ] Confirm bye-laws are consistent with DOD and filed with Registrar
- [ ] Share registered DOD copy with all apartment owners
- [ ] Schedule first Association meeting within timeline
