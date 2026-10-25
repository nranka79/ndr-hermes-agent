# Filing an External Judgment / Precedent + Temporary Share + Auto-Restrict

Class of task (verified 2026-10-13, *Dr G.V. Palaksha v. State of Karnataka*,
W.P. 20701/2025, HC Karnataka, 11-Feb-2026 → Ranka NorthStar TDR claim).

**Trigger shape.** NDR drops a PDF (usually an Indian Kanoon / eCourts download) and
dictates something like: *"this is a High Court judgment … it applies to <project> …
rename it and file it appropriately with a note about this document along with this
document, then give me a message for <official> sharing a link of this judgment so it
will be shareable for anyone to view temporarily, and in the next agent action after
N days change it to private / only those we share it with."*

That dictation is **four deliverables**, not one. Do all four in a single pass:
1. rename + file the source PDF;
2. write a companion **Note** document alongside it;
3. open a **temporary anyone-with-link** view window;
4. schedule the **restriction** as a `next_action` row, and draft the messages.

---

## 1. Read the document first, then file

NDR's "file it with a note about this document" **is** the authorisation to read the
attachment — the default "wait for instructions" rule for uploads does not apply once he
has told you what the document is for.

Extract with pymupdf from the venv and read **all** pages before writing the note —
the operative order is on the last page and is the part that matters:

```python
import pymupdf   # not `fitz` — that import is deprecated
doc = pymupdf.open(PATH)
for i in range(doc.page_count):
    print(f"===== PAGE {i+1} ====="); print(doc[i].get_text())
```

Indian Kanoon PDFs interleave the kanoon header/footer into the body text; expect the
order, the directions and the list of authorities to be split across pages.

## 2. Where to file it

- File into the project's **existing active working set** for that subject. For a
  judgment supporting a TDR claim that is
  `Ranka Northstar / TDR_DRC_Application_Sy14-1_RankaNorthstar` — a genuine working
  collection, which is the documented exception to the "no third level under a project
  bucket" rule (`draas-project-folder-structure`).
- Do **not** invent a new topic folder like `Judgments` / `Precedents` / `Legal`.
- **NDR saying "file it appropriately" overrides the TMP staging default.** TMP is for
  chat-session artifacts with no home; an explicit filing instruction means file it in
  the project, not in TMP. Say in the reply exactly which folder path you used.
- Naming (DRA hard rule `YYYYMMDD_Entity_Description`):
  `20260211_RankaNorthstar_HC-Karnataka_Judgment_<Petitioner>_vs_<Respondent>_<CaseNo>_<subject>.pdf`
  — date of the **order**, not of the filing; underscores only; the subject tag
  (`TDR_for_CDP_Road_Land`) is what makes it findable later.

## 3. The companion Note

Create it as a **native Google Doc** in the same folder (see
`google-doc-formatting-template` → "Creating a NATIVE Google Doc from HTML" — the native
`gws_drive_create_file` tool cannot convert HTML to a Doc). Note section order that has
worked:

1. Document details (case no., court, bench, date, neutral citation, source URL, parties)
2. Facts
3. Reliefs sought
4. Contentions — petitioners / respondents
5. **Held — the ratio**, quoting the statutory provisions verbatim
6. Operative order, numbered exactly as the court numbered it
7. **Why this matters to <project>** — NDR's own reading, in his framing
8. Points to verify / caveats
9. Filing (folder path, file names, who it was shared with, date)

Section 7 and 8 are the parts he actually re-reads. Section 8 is where you record the
honest gaps: pending appeals without stay, "persuasive not binding — different parties",
and any mismatch between the judgment's direction and NDR's framing of the claim.

## 4. Permissions — a file inherits its folder's collaborators

Uploading into a shared folder means the new file **immediately** carries every user on
that folder. Verify with `permissions().list` and treat that inherited set as the
"only those we share it with" state that the restriction step must preserve:

```
ndr@draas.com (owner) + writers: sales1.blr@draas.com, rnr@draas.com,
admin2.blr@draas.com, vkdas@draas.com, pingal.khan@ashlarlaw.com,
roshan@ashlarlaw.com
```

Consequences worth stating to NDR: the folder's existing collaborators (his advocate,
Roshini, Bharat) can already open the file, so a "restrict" step never means
"NDR only" — it means "drop the public link, keep the collaborators".

## 5. Opening the temporary view window

`gws_drive_permissions_add` supports `perm_type user|domain` **only** — an `anyone`
(link-share) entry must be created through the API:

```python
drive.permissions().create(
    fileId=PDF_ID, body={"type": "anyone", "role": "reader"},
    fields="id,type,role").execute()      # -> {'id': 'anyoneWithLink', ...}
```

Verify by listing and asserting an entry with `type == 'anyone'` exists. Open the window
on the **judgment only** — leave the internal Note private unless asked.

## 6. Scheduling the restriction

Add a `next_action` row (see the `next-agent-action` skill for the *working* invocation —
do not use the old `env -u PYTHONPATH` one-liner). The Context must be fully
self-contained because the cron agent has no memory:

- the Drive **fileId**, the file name, the folderId and `service_name`;
- the permissionId to delete (`anyoneWithLink`) and the exact API call;
- the list of user permissions to **KEEP** (name them);
- the instruction to add the named person as `reader` **first** if his email has since
  been supplied — and an explicit "do NOT guess or invent an email" guard;
- the verification step and the instruction to report before/after permission state.

If the person to be shared with has **no email address on record** (common for
government officials), say so plainly rather than guessing one: the temporary link is the
only mechanism, and the restriction row should carry that caveat.

## 7. The messages

Two audiences, two different registers (see `messaging-drafts` /
`confirm-before-actions` — present drafts, do not send unprompted):

- **The government official** (e.g. Mohan Sir, JDTP GBA East, +91 98868 85455 — **no
  email on record in contacts, Gmail or Drive**): give NDR a **WhatsApp tap-link** whose
  text is his dictation, first person, captioned `*<Project> — <subject>*`, ending with
  the judgment citation and the Drive link. Generate it with the `whatsapp_link` tool —
  never hand-build the URL. **The delivery mechanics matter as much as the link** — a
  ~2.7k-char deep link pasted inside a summary reply exceeds Telegram's 4096 cap, gets
  split mid-URL, and comes back to you as *"the encoding is not working"*. Send it as its
  OWN `send_message`, and verify the number against the contacts-sheet row first:
  `messaging-drafts/references/whatsapp-deep-link-delivery.md`.
- **The internal lawyer / colleague** (Rahul = **Vinod Kumar Das**, vkdas@draas.com, who
  *is* reachable on Telegram under the name "Vinod Kumar Das"): a shorter note — what the
  judgment says, NDR's reading of it, and that the same clarification has gone to the
  official — with both the judgment and the Note links. He already has access via the
  folder.

## 8. Pitfalls

- **`gws_drive_create_file` cannot make a Doc** — see `google-doc-formatting-template`.
- **Do not name the authority from the dictation without checking the order.** NDR's
  voice note said "VBMT authority"; the order actually directs the **BDA (R-2/R-3)**.
  Read the order and use what it says, then flag the delta to him.
- **Watch for a framing gap between NDR's claim and the court's direction.** Here the
  direction was TDR "proportionate to the said extent"; NDR frames it as TDR for "FAR we
  cannot use on the balance property". Record *both* bases in the Note rather than
  silently reconciling them.
- **Resolve names before drafting.** `entity_resolver` errored this session
  (`TypeError: _handle() got an unexpected keyword argument 'task_id'`). Fall back to
  `contact_resolver` (try the short name *and* the full name / org) plus
  `session_search` — that is what surfaced both "Rahul = Vinod Kumar Das, vkdas@draas.com,
  on Telegram" and "Mohan Sir JDTP GBA East has no email". Do not guess an address.
- **OneDrive-style "temporarily public" is a two-row lifecycle**: open now, restrict on
  the date NDR named. Both halves are `next_action` rows, not fresh cron jobs.
