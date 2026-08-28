# School Absence + Exam Accommodation — Email Pattern

Used when a child is absent due to illness and has a scheduled exam the next day.
This is a FRESH email (not a reply), notifying the school and requesting accommodation.

## When to use

- Child is absent today (illness), unlikely to attend tomorrow
- There is a scheduled exam tomorrow
- Parent wants to know: can the child take it on an alternate day, or come in just for the exam?

## Recipient structure — IMPORTANT: differs by child (validated Aug 2026)

### Rivan @ Aditi (Std 07 SS, 2026-27)

- **To:** Ms. Neetu Shrivastava (neetu.shrivastava@gsuite.aditi.edu.in), Mr. V. Subath Senan (subath.senan@gsuite.aditi.edu.in)
- **Source:** Welcome to New Academic Year PDF (07 parent letter.pdf, 26 May 2026 email from Subath Senan)
- **Note:** This is Rivan's class. Ranjitha Tikandar handles attendance/leave notes for the class teachers but is NOT a class teacher herself.

### Ruhaan @ Aditi (Std 9 / IGCSE Year 2, 2026-27)

- **To:** Ranjitha Tikandar (ranjitha.tikandar@gsuite.aditi.edu.in), Priya Rao (priya.rao@gsuite.aditi.edu.in)
- **Source:** Email chain (Jun-Aug 2026) — Ranjitha explicitly called Priya her "co-class teacher" in a June email about leave note formatting. Priya's signature reads "Faculty — Law, Legal Studies, Global Perspectives, Debating."
- **Cc:** Joyce Jose (joyce.jose@gsuite.aditi.edu.in) — HOD/coordinator, Roshini Ranka (rnr@draas.com), Ruhaan Ranka (pebblyshark69@gmail.com)
- **Bcc:** Joel Kribairaj (joel@aditi.edu.in) — school administrator, only if user explicitly names them
- **Sender:** Always ndr@draas.com for NDR's work communication
- **Do NOT confuse Std 07 SS class teachers (Neetu + Subath) with Ruhaan's class teachers.** They are different children in different grades.

## How to verify roles before drafting

1. Search the contacts sheet (`NDR DRAAS Google contacts`) for each person — may be incomplete or absent.
2. Search Gmail threads (`q='from:<domain> subject:<topic>'`) for the persons involved — email signatures often reveal roles (e.g. Priya Rao's signature: "Faculty — Law, Legal Studies, Global Perspectives, Debating").
3. Check the original thread headers (From, To, Cc in the forwarded body or direct email) — who initiated the leave note, who was CC'd, who handled the certificate request.
4. **Authoritative source for class teachers: the school's Welcome/Introductory PDF at the start of the academic year.** Search Gmail for `subject:"Welcome" from:<school-domain>` and download the attached PDF — schools typically list class teachers + teaching team explicitly in this document. Extract text with `pdftotext` or `pymupdf`. This is more reliable than inferring roles from individual email threads. (Validated: Aditi Std 07 SS Welcome PDF, 26 May 2026, listed Neetu Shrivastava + Subath Senan as class teachers, while the attendance/leave thread involved Ranjitha Tikandar who is not a class teacher.)
5. Ruhaan's Drive folder (`Ruhaan` folder, id `0B1Oc8cSaJXPGbl9VMEZBdE04Z28`) has report cards, health history forms, and class photographs — useful but does NOT explicitly label teacher roles. Don't spend excessive time here.
6. If the user says "there may be two class teachers," don't assume — verify from the authoritative Welcome PDF first, then from email threads. In the Aditi case, Priya Rao is NOT a co-class teacher (she's Faculty); the academic coordinator/HOD role sits on Cc, not To.
7. Report your findings to the user with a clear recommendation before drafting — including the fact that the person handling attendance (Ranjitha) may not be the actual class teacher, and offering to Cc both.

## Email structure

1. **Open** — polite, one line: "Given Ruhaan's condition today, it is unlikely he will be able to attend tomorrow."
2. **State the situation** — there is a scheduled exam; he will likely miss it.
3. **Request guidance** — offer two options as questions:
   - Can he take the exam on an alternate day?
   - Can he come in solely for the exam, sit separately, and leave?
4. **Update on medical action** — we are trying to reach the doctor; may take him for a consultation.
5. **Conditional** — will confirm with the doctor whether he is up to date on the material.
6. **Close** — "Please advise us. We are happy to cooperate fully with whatever arrangement works best."

## Tone rules

- Cooperative, not demanding. The school decides what's possible.
- Don't presuppose the answer (e.g. don't say "he will take it on Monday").
- Express willingness to work with whatever arrangement suits the school.
- Keep it brief — this is a notification + request, not a debate about policy.

## Related

- `email-drafter` SKILL.md → Stage 2 → **School / authority communication tone** — for emails that challenge/query a school policy (doctor's certificate requirement, etc.). That pattern is more detailed and question-heavy; this one is simpler and notification-focused.