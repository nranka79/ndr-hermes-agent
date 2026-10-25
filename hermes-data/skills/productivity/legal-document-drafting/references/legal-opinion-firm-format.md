# Firm-Formatted Legal Opinion — Format, Structure & Production Pipeline

When NDR asks for a "proper legal view", a "neutral legal opinion", or to "present it as
if it came from a law firm", the deliverable is a **branded, letterheaded opinion document**
rendered to PDF and delivered as a **Drive link** — not a chat answer.

**Firm name to use: "DNR Law Firm"** (Advocates & Legal Consultants). NDR instructed this
explicitly. Keep the sub-line and office cities generic
("Bengaluru · Chennai · New Delhi") — do not invent partners, addresses or bar numbers.

## When to use this

- "Can you present this as a proper legal view / as if from a law firm"
- "Frame each of these as a question and give me an opinion"
- "Support our argument with case law" / "what would the authority say"
- Any chargeability, registrability or compliance question going on the record
- Contractually: whenever the output may be shown to a Sub-Registrar, lender or counsel

Do **not** route one-line legal questions through this pipeline. It is for opinions that
will be read by a third party.

## Document structure (this is the format NDR approved)

1. **Letterhead** — firm name in spaced small caps, sub-line, office cities, then a
   double rule.
2. **Confidential banner** — "PRIVILEGED & CONFIDENTIAL · PREPARED FOR THE ADDRESSEE ONLY",
   gold/amber. Always present.
3. **Meta block** — To (name + entity) · Date · Our Ref (`DNR/OP/YYYY/MMDD-XX`) · Subject.
4. **I. Scope of this Opinion and Documents Examined** — state exactly which instruments
   were read, with registration numbers, and — importantly — record what you were **not**
   furnished. This is where credibility is built and where a real firm would caveat.
5. **II. Questions Presented** — one boxed/`callout` question per issue. **This is the key
   formatting instruction NDR gave: frame each issue as its own numbered question.**
6. **III. Opinion in Brief** — a 3-column table: Question | Our Opinion (`NOT CHARGEABLE` /
   `BARRED` / `ADVISABLE`) | Principal Authority. Answer first, reasons later.
7. **IV. Statutory Framework** — the provisions, with block-quoted operative text.
   Verify the current amendment position and *say so* (e.g. "the 2025 amendment effects no
   change to rates").
8. **V. Analysis** — one sub-part per question. **Open each contested question with the
   view most favourable to the other side, stated fairly.** NDR asked for the neutral view
   first ("forget my view — if you were the Sub-Registrar, how would you compute it?").
   Then answer it. Never stack authority without first conceding the strongest counter-case.
9. **VI. Conclusion** — numbered, mirroring the questions one-to-one.
10. **VII. Recommendations, and a Respectful Request to the Registering Authority** —
    ordered action list, ending with the **polite deferral ask**: if the officer remains
    uncomfortable, request referral under **s.31** (adjudication) rather than deciding it
    himself. Frame it as protecting him as much as the client.
11. **VIII. Authorities Relied Upon** — table of case | proposition, plus a list of
    statutory provisions considered (including ones *referred to a larger Bench*).
12. **IX. Qualifications and Disclaimer** — no verification of documents, illustrative
    computations flagged as such, no guarantee of outcome, addressee-only.
13. **Signature block** — "For DNR LAW FIRM" + rule + "Authorised Signatory".

## Style rules NDR expects

- **Polite and cooperative, never adversarial toward the authority.** The addressee may be
  the very officer being answered. "We make no criticism of that duty", "we respectfully
  submit", "we would request him to be pleased to refer".
- **Quantify the exposure** so the stakes are visible, but label every figure illustrative
  and defer value to the adjudicating authority.
- **Correct the client where the client is wrong**, inside the document. In the North Star
  matter the client had told Vaidyanathan that Sriram "is not a party" to the addendum,
  while Sreeraman Vaidyanathan is named Landowner 6 on its face. The opinion said so plainly
  — flag it in chat too, it is commercially material.
- **Defer the mandatory question honestly**: "not mandatory in the strict sense, but
  strongly advisable" is the shape. Do not tell NDR to skip a registration that carries his
  own security interest.
- **Close the chat message with the caveat** that this is research, not a signed opinion,
  and that counsel must vet it before it goes on the record.

## Production pipeline (HTML → PDF → Drive)

`/mnt/uploads` is often mounted **read-only**, so a file written there may not survive and
cannot be served to the web chat. Use a working directory under `/opt/data` and deliver via
Drive.

### 1. Write in chunks, then assemble

A single large `write_file` call can time out the stream (the assembled document here was
~70 KB / 22 A4 pages). Write **part1.html … part7.html** (~7–14 KB each), keeping the
`<head>`/CSS and the header in part 1, then concatenate:

```python
# /opt/data/<work>/build.py
import re, pathlib
d = pathlib.Path("/opt/data/dnr-opinion")
p1 = d.joinpath("part1.html").read_text(encoding="utf-8")
p1 = re.sub(r"</div>\s*</body>\s*</html>\s*$", "", p1)   # strip provisional closer
rest = "".join(d.joinpath(f"part{i}.html").read_text(encoding="utf-8") for i in range(2, 8))
out = p1 + rest
d.joinpath("OUT.html").write_text(out, encoding="utf-8")
# sanity: tags must balance
print(out.count("<div"), out.count("</div>"), out.count("<h2>"))
```

Subsequent parts carry body content only; the final part closes `</div></body></html>`.

### 2. Render to A4 PDF with the bundled headless Chromium

```bash
CHROME=/opt/hermes/.playwright/chromium_headless_shell-1234/chrome-headless-shell-linux64/chrome-headless-shell
"$CHROME" --headless --disable-gpu --no-sandbox --no-pdf-header-footer \
  --print-to-pdf=/opt/data/<work>/OUT.pdf "file:///opt/data/<work>/OUT.html"
```

dbus/vaapi/bluez warnings on stderr are harmless — check for the
`NNNN bytes written to file` line instead. (Path is versioned; list
`/opt/hermes/.playwright/` if it moves.)

### 3. Verify the render before delivering

```bash
pdfinfo OUT.pdf | head -12                    # page count, title
pdftoppm -png -r 80 -f 1 -l 1 OUT.pdf pg      # full first page
pdftoppm -png -r 150 -x 0 -y 0 -W 1250 -H 470 -f 1 -l 1 OUT.pdf hdr   # header crop
```

Then OCR the **header crop** — small letterhead text is exactly what a low-DPI full-page
render loses, and the confirmation reads out as:

```
DNR LAW FIRM / ADVOCATES & LEGAL CONSULTANTS / Bengaluru - Chennai - New Delhi
PRIVILEGED & CONFIDENTIAL / PREPARED FOR THE ADDRESSEE ONLY
```

### 4. Upload to Drive, public-read, via the sanctioned auth layer

Use `tools.gws_auth.build_service('drive', 'v3', service_name='google-draas')` and
`MediaFileUpload`. **Never** read a token JSON off disk — see the credential hard rules.

```python
svc = build_service("drive", "v3", service_name="google-draas")
res = svc.files().create(body={"name": name}, media_body=media,
                         fields="id, name, webViewLink, size").execute()
svc.permissions().create(fileId=res["id"],
                         body={"role": "reader", "type": "anyone"}).execute()
```

Run it with the correct session identity — from a terminal subprocess the session env can
carry the wrong `HERMES_SESSION_USER_ID`:

```bash
cd /opt/hermes && HERMES_SESSION_USER_ID=<ndr id> /opt/hermes/.venv/bin/python upload.py
```

`/opt/hermes/.venv/bin/python` already has the Google client libraries — no venv build needed.

### 5. Verify, then deliver

Re-fetch each file and assert the permission, not just the ID:

```python
svc.files().get(fileId=fid, fields='name,size,permissions(type,role)').execute()
# expect ('anyone','reader') + ('user','owner')
```

Upload **both** the PDF (the one to send/print) and the HTML source (so NDR can edit and
re-render), and report both links with sizes. Then offer the follow-on: the s.31
adjudication application and the covering letter to the authority, in the same format.

## CSS conventions that produced the approved look

- A4 `.doc` container, `max-width: 210mm`, generous padding, subtle shadow on screen.
- Georgia / Times serif stack; navy `#14324f` for headings and rules.
- `h2` section headings: uppercase, letter-spaced, underlined by a hairline rule.
- `.stat` block for quoted statutory text: left navy border, pale blue fill, uppercase label.
- `.callout` for framed issues (the Questions Presented boxes); `.warn` amber for
  "must reserve this point" caveats.
- `table.gen` — navy header row, uppercase small-caps headers, zebra rows.
- `.yes` / `.no` classes for `ADVISABLE` / `NOT CHARGEABLE` verdicts.
- `@media print` — drop the background and shadow, tighten padding, and set
  `page-break-inside: avoid` on tables, callouts and block quotes.
