# Customer project letters when a registered sale deed cannot be given

Worked case: **Ranka Iris** (DRA Developers & Projects Pvt Ltd), 2026-10-05. Two letters
handed to the office by NDR for review, correction and filing:

- `POSSESSION_LETTER_RANKA_IRIS_Apt_1006.docx`
- `LETTER_REGISTRATION_DELAY_RANKA_IRIS_Apt_1008.docx`

Then a third act: the possession letter had to be **re-pointed from Apt 1006 to Apt 1008**
for a different purchaser pair. Both are covered below.

---

## 1. When this instrument pair is the right answer

A buyer needs to establish his **date of acquisition** for a long-term capital gains
exemption (s.54 / 54F) — or a bank file needs evidence of possession — but the project
cannot yet execute and register the sale deed. On Iris the blocker is genuine and entirely
outside the developer: the individual apartment khata must exist before the sale deed can be
presented for registration, and the GBA e-khata software rejects newly completed apartment
units (system-level, affects all Bengaluru developers at the same stage).

The pair that answers this, and that the buyer's CA asked for:

| Letter | What it establishes |
|---|---|
| **Possession letter** | vacant, peaceful, physical possession handed over on a date — the acquisition event. Carries an acknowledgment recital the purchaser signs. |
| **Registration-delay letter** | why the registered deed does not yet exist, that the delay is the Authority's and not the purchaser's, and that possession / payments / rights are unaffected. |

**Both letters must be in the SAME purchaser's name.** Possession proof plus the reason
there is no registered deed are one evidentiary package; split across two flats they answer
nothing. When the user describes "one customer" needing this, first establish *which* flat,
then reconcile both letters onto that flat.

Write the exemption proposition as *"the position the purchaser's CA has advised"* — do not
assert the tax outcome as our legal conclusion.

## 2. ⚠️ Correction-priority rule (NDR, 2026-10-05 — the point of the whole review)

NDR's instruction, verbatim in substance: *"Pvt Ltd is acceptable, don't worry about it.
As far as the inconsistency or weaker proposition for the buyer, don't worry, that's for the
buyer to look out. Rest of the data inconsistencies from our end, errors like OC things,
let's fix it."*

So on a document review, split every finding into two buckets and only act on the first:

- **FIX — errors on OUR side, factual and citable.** A wrong official document number, a
  wrong issuing authority, a wrong entity name in the signature block, a wrong unit number /
  floor, wrong areas, a stale reference. These get corrected in the document.
- **LEAVE — drafting and risk allocation.** Weaker wording that happens to favour the buyer,
  stylistic inconsistency between two letters, "Pvt Ltd" vs "Private Limited", an internal
  contradiction inherited from an executed agreement. Do not rewrite these, do not list them
  as defects, and do not make them a condition of issue.

Corollary: a defect inherited from **our own executed agreement** (e.g. a parking clause whose
parenthetical area contradicts its own dimensions) is not ours to silently "fix" either — a
possession letter must not assert a figure the executed agreement does not support. Drop the
unsupportable specific, keep the entitlement, and hand the discrepancy back with the source.

## 3. Review checklist — verify every citable particular against the source document

Run in this order; each is a place a real error was found.

1. **Every official document number, read off the document itself.** Iris: both letters cited
   the OC as `BBMP/Addl.Dir/JD North/0037/2013-14 dated 04.06.2026`. That number is the
   **2013 building-plan sanction / licence-permit** (`LP 0037/2013-14`, dt 02-09-2013) — it
   appears inside the OC only as *Ref (3)*. The OC is
   **`ACTP/BCCC/OC/001/2026-27` dt 04.06.2026**. Only the date was right. In a letter whose
   whole purpose is to be evidence, a wrong official number is the one thing that must not ship.
2. **The issuing authority.** The possession letter said the OC was issued by the *BBMP*. It
   was issued by the **Bengaluru Central City Corporation** (Office of the Additional Chief
   Town Planner). BBMP no longer issues these; the same letter then correctly named the GBA for
   the khata, contradicting itself inside one page.
3. **Entity name in the signature block**, taken from the executed agreement, not memory.
4. **Co-allottee names — check the customer master sheet, NOT the agreement.** See §5. On Iris
   the possession letter named a second purchaser who was absent from the executed agreement;
   the customer register proved the letter right and the agreement the outlier. **Check before
   you delete a name**, and if you already flagged it, retract it explicitly.
5. **Unit, floor and type** in the subject line, Schedule table and acknowledgment recital all
   changed together — a partial change is how a letter ends up describing two different flats.
6. **Areas and UDS** — see §4.
7. **Consideration** — see §6.
8. **Car park** — see §7.
9. **DatES. Both letters were undated, and the possession letter's "Date of handing over
   possession" and its "We have this day taken over possession" recital were blank.** For this
   claim the possession date *is* the date of acquisition, so a blank makes the recital
   meaningless and invites a back-dating question. Flag it as the single most important item
   and require the real, provable date at issue. Never fill it yourself.

## 4. Unit areas: use the Deed of Declaration schedule as the authority

The **Deed of Declaration, ANNEXURE-1** carries the final unit-wise schedule — for each unit:
sanctioned area (sq m), area as per OC (sq m), actual built-up (sq m and sq ft), **carpet area
(sq ft)** and **UDS allocated to each unit (sq ft)**. On Iris it gives even floors
`350.82 / 3774.8232 / 2198.6 / 880.84` and odd floors `349.04 / 3755.6704 / 2198.6 / 876.38`.

Read it with `files().export(fileId, mimeType='text/plain')` and search for `ANNEXURE` — the
schedule sits deep in the document and the export returns the whole body in one call.

**Rule for re-pointing a letter to a different flat:** you may carry a letter's area figures
across only when the schedule proves the two units are **identical**. On Iris, Apt 1006 and
Apt 1008 are both even-floor units and the ANNEXURE-1 rows are *character-for-character the
same* — that identity is the evidence that justifies the carry-over. Otherwise go and find the
target unit's own agreement. Note the agreement basis (3775 / 880) and the Deed schedule basis
(3774.8232 / 880.84) are two legitimate roundings of one measurement — do not present one as an
error (see the rounding pitfall in the parent skill).

## 5. The customer register — the authority on WHO the purchasers are

`Ranka IRIS Customer Detials` (Google Sheet, `1Q7jrrMWJlQnMjm-IrgH7zx5ASne2lyc...` — resolve by
name). One row per unit, with:

`AptNo | Floor | Booking Date | A2S Date | Sale Value | GST | Tot. Sale Consideration |
SBUA Area | FA name/DoB/PAN/phone/email | SA name/DoB/PAN/phone/email | Correspondence Address |
Permanent Address | Channel Partner | BHK | Agreement link | Sale deed link`

- **FA = First Applicant, SA = Second Applicant.** This is where you confirm whether a second
  purchaser is really a co-allottee. Column semantics are unobvious — read the header row.
- It carries the postal addresses to serve a letter to (a possession letter goes to the
  purchaser's address, not the flat's).
- `fullText contains '<surname>'` on Drive is the fastest way to find it.
- Watch the SBUA column: on Iris it reproduced the odd-floor figure (3755) on an even-floor unit.
  It is a register, not a measurement authority.

## 6. ⚠️ PITFALL — the customer register is NOT the contract authority for consideration

The master sheet's `Tot. Sale Consideration` = `Sale Value + 5% GST` (Iris: 57,148,750 +
2,857,438 = 60,006,188). The **executed agreement** for the same unit says **5,99,66,550**
(= base 57,111,000 + 5% GST). A real gap of about ₹39,600, i.e. a later price revision.

Consequences to carry forward:

- Do not quote the register figure in a contract-level letter without saying where it came from.
- **No per-unit executed Agreement for Sale exists on Drive for most Iris units** — only
  `Ranka Iris Flat 1006 Agreement of Sale.pdf` was findable, and nothing at all for 1008, in
  Drive or in the mailbox. When this happens, put the register figure in **with its provenance
  stated to NDR**, flag it as the one line needing confirmation against the executed agreement,
  and do not present it as contract-sourced.
- The property folders do hold `Proforma` agreements (blank, per-unit fields unfilled) — useful
  for clause wording, useless for figures.
- A signed-copies `Customer Signed copy.rar` (46 MB) sat on the Drive and could not be opened:
  no `unrar`/`7z` on the host and no root to install one. Do not spend the session on it —
  report the gap and ask for the agreement.

## 7. Car park clause in a possession letter

Only state what the record supports: the **entitlement** and, where confident, the bay numbers
and basement. Never carry over the previous unit's bay number, and never restate a parenthetical
area that contradicts the dimensions in the same clause of our own agreement (Iris: "45 Sq. Ft.
each" beside "2.5m x 5.5m", which is ~148 sq ft). Where the executed agreement for the target
unit is unavailable, write the entitlement alone — `2 (Two) Car Parking Spaces (exclusive right
to use)` — and hand the bay numbers back to the user.

Parking basis for Iris is now fixed at **24 allotted (2/unit) + 6 visitor** — see
`real-estate/unit-area-and-cost-sheet` → `references/ranka-iris-unit-entitlements.md`, flag 4.

## 8. Mechanics — re-point a letter in place, keep the file ID, verify by re-download

Editing the Drive file **in place** rather than uploading a new one keeps the canonical link
and every existing share alive (on Iris, `piyush@draas.com` held reader access that would have
been lost on a fresh upload). Drive **version history preserves the superseded content**, so an
in-place rewrite is not destructive — say so when the user changes a letter's addressee, because
it means the old version is recoverable.

```python
# 1. download the CURRENT Drive copy as the template (not the original upload)
req = drive.files().get_media(fileId=FID); MediaIoBaseDownload(fh, req)
# 2. run-level replace — paragraphs AND table cells; per-run so formatting survives
for p in doc.paragraphs + [p for t in doc.tables for row in t.rows
                           for c in row.cells for p in c.paragraphs]:
    for r in p.runs:
        for a, b in PAIRS:
            if a in r.text: r.text = r.text.replace(a, b)
# 3. write back: content + new name in one update, same fileId
drive.files().update(fileId=FID, body={'name': NEW_NAME}, media_body=MediaFileUpload(path))
```

Replacement pairs that must all move together for an Iris-style re-point: addressee (both
occurrences — the address block *and* the acknowledgment recital), postal address lines, subject
line (unit **and** floor), consideration (figure **and** words), Schedule rows for apartment /
car park / allottees, and the purchaser signature block. The acknowledgment recital catches
people out because it repeats the names far from the address block.

**Verify by re-downloading and asserting on the text** — never trust the successful update
return. Assert both directions: the target strings ARE present, and an explicit list of stale
strings is ABSENT (`Aroor`, `Sandhya`, `1006`, `5,99,66,550`, old pincode). A grep for the
things that should be gone is what proves a re-point actually completed.

## 9. Messaging the correction to the colleague who owns the document

NDR's correction (2026-10-05): *"give me a WhatsApp message of all that we have fixed in the two
documents, then giving the links to the documents, rather than telling him what all is wrong in
the document and then asking him to just review it once more."*

So the message is **"what has been FIXED" + document links + "please issue these versions"** —
never a defect list with a request to review. Corrections you decided *not* to make (per §2)
are simply omitted, not reported. Items you could not fix go to **NDR**, not into the colleague
message. Deliver as a WhatsApp deep link built with the `whatsapp_link` tool (split parts arrive
as separate links; send each as its own message). Confirm the recipient's number label first
(NDR uses the `Work` label) and remember a Drive link is useless to the recipient until they
have at least reader access — check the permissions and grant before sending.
