# Bilingual (Kannada / English) Legal Notice — Filing + Circulation

Verified 2026-09-17 on the Ranka Amber BMTF notice
(`BMTF/ADGP/Petition/1237/2026`). Applies to any statutory/police/department notice
received in Kannada that has to be (a) filed correctly, (b) translated, and (c) circulated
to the colleague handling closure.

## 1. The naming pair (DRAAS convention)

Every notice is filed as TWO files with a fixed suffix pattern — never one combined file
alone:

```
YYYYMMDD_<Project>_<Dept/Type>_Notice_Kannada_Original_Scan.pdf     # the scan as received
YYYYMMDD_<Project>_<Dept/Type>_Notice_English_Translation.pdf       # the English rendering
```

Precedent pair already on Drive (Labour Dept):
`20260825_RankaAmber_LabourDept_Notice_Kannada_Original_Scan.pdf` +
`20260825_RankaAmber_LabourDept_Notice_English_Translation.pdf`.
Destination: **`<Project> > Legal Notices`** (Ranka Amber = `1jOQzLjRAhy761CUU8aobTtDdmYqLyROm`).

## 2. ⚠️ PITFALL — a file named "English translation" may be ONE PAGE of it

The existing BMTF file labelled as the translation turned out to be **the signature page only**.
The real document was a 3-page PDF: p1 Kannada notice, p2 English translation, p3 English
signature block. Nobody had noticed, and it had already been linked to a colleague.

**Always enumerate pages before trusting a bilingual filename:**

```bash
for n in 1 2 3; do
  pdftotext -layout -f $n -l $n notice.pdf - | head -5
done
```

Kannada pages extract as Kannada Unicode (plus garbled Latin if a bad OCR overlay exists);
English pages extract as English sentences. Do not use an ASCII-ratio heuristic alone —
a Kannada page carrying lot-numbers and party names can score high on ASCII.

## 3. Extract a standalone translation (dependency-free path)

`pymupdf` may not be importable in the Hermes venv, and the `pymupdf` fallback is not worth
the detour. Poppler is already installed and does this in two commands:

```bash
pdfseparate -f 2 -l 3 notice.pdf /tmp/en-%d.pdf      # single %d, NOT escaped
pdfunite /tmp/en-2.pdf /tmp/en-3.pdf /tmp/English_Translation.pdf
```

⚠️ Writing the arg as `/tmp/en-%%d.pdf` (shell-escaped out of habit) makes `pdfseparate` exit
99 — there is no shell in `subprocess.run`, pass a bare `%d`.

Then UPDATE the existing Drive file in place rather than creating a duplicate, so any link
already circulated keeps working:

```python
svc.files().update(fileId=EN_ID, media_body=MediaFileUpload(local, mimetype='application/pdf'),
                   fields='id,name,size,md5Checksum').execute()
```

## 4. Completeness check before circulating

Grep the extracted text for the load-bearing clauses — a partial translation is worse than none:

```python
checks = {
    "title block": "BMTF Police Notice",
    "respondent block": "D'Silva Layout",
    "allegation para": "encroached upon at the construction site",
    "hearing instruction": "07/09/2026 at 11:30 AM",
    "document list head": "documents listed below",
    "last doc item": "No Objection Certificate obtained from RERA authority",
    "signatory": "Manoj Kurane",
}
```

## 5. Circulation — reply-all draft on the ORIGINAL thread

NDR's pattern: he sends the assignment to the handler, then later wants the notice *given* to
that handler on the same thread. Find the thread by Gmail search (`BMTF`, or
`<subject token> <handler first name>`), then create a threaded draft — **never a send**:

```python
msg['In-Reply-To'] = orig_message_id; msg['References'] = orig_message_id
gmail.users().drafts().create(userId='me', body={'message': {'threadId': THREAD, 'raw': raw}}).execute()
```

Verify: `drafts().get(format='metadata')` shows the right To/Cc/In-Reply-To, and
`threads().get()` shows the message count incremented. Reply-all = every recipient of the
original To/Cc — if the original only had one recipient, reply-all is a plain reply, and that
is correct, not a mistake to "fix" by adding people.

Handler for statutory/police notices at DRAAS: **Vinod Kumar Das (Rahul) — vkdas@draas.com**
(tracker P-108, zero-cost closure).

## 6. Access + hygiene

- The handler usually **already has writer access** inherited from the Legal Notices folder —
  a 90-day viewer grant is then impossible and unnecessary. See the inherited-permission
  pitfall in `draas-drive-organization` SKILL.md; report the existing (stronger) access
  instead of faking a grant.
- **Remove any `anyone with link` reader from a live legal/police notice** — a scanned notice
  making allegations about a project should not be link-public. Internal colleagues reach it
  by per-user permission or their folder access. Verify with
  `permissions().list(fields='permissions(id,type,role,emailAddress)')`.
