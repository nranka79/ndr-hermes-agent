# Law-Firm Letterhead Opinion Letters (NDR)

Use when NDR asks for legal advice to be presented as if it came from a
professional law firm — typically because it will be shown to a **third party**
(Sub-Registrar, municipal/authority officer, counterparty, landowner, bank).
He names the firm himself ("we'll put it as DNR law firm"). Default firm:
**DNR Law Firm — Advocates & Legal Consultants, Bengaluru · Chennai · New Delhi.**

Template: `templates/dnr-law-firm-opinion.html` (complete CSS + skeleton).

**See also:** `references/karnataka-stamp-duty-jda-addendum.md` — the Karnataka
Stamp Act research bank for the recurring DRAAS question of duty on a JDA, an
addendum to a JDA, and an assignment of developer rights (Article 5(f) / 5(J),
the ₹200 GPA proviso, s.46A limitation, s.31 adjudication, and the case law).
That reference also carries the *worked example* of taking the neutral view first
and then correcting one limb of NDR's own framing.

**Also see:** `references/nri-registered-gpa-consulate-route.md` — fresh
**registered** GPA for an overseas landowner when the Sub-Registrar refuses to accept
an unregistered GPA (consulate attestation / apostille → District Registrar
adjudication), plus the powers checklist, the per-owner "different JDA" trap, and the
rule that every particular must be traced to the executed instrument.

---

## THE BREVITY RULE — read this first

This is a corrected preference, not a guess. The first deliverable he asked for
was a **22-page** full-reasoning opinion. He rejected it:

> "that legal opinion… can be shorter… it's too big. We want to bring it down to
> the minimum. Basically, what's important so the sub-register can read
> questions, answers, case law. Very simple. Not applicable, not applicable, not
> applicable. We don't want to get into too much detail right now."

Target shape for an opinion that goes **out of the building**: **4–6 pages A4.**
Structure, in this order:

1. **Letterhead** — firm name, "Advocates & Legal Consultants", cities.
2. **Privileged & Confidential** banner.
3. **Meta table** — To / Date / Our Ref / Subject.
4. **SUMMARY OF OPINION table** — the single most important element.
   Columns: *Question | Our Opinion | Principal Authority*. Answer in bold,
   colour-coded (`No` in red, `Yes` in green, qualified answers in plain bold).
   A reader who reads nothing else must get the whole answer here.
5. **Per-question blocks**, one question per section. Each block is exactly
   four parts, no more:
   - `Question` — the question as actually asked at the counter.
   - `Our Opinion` — one paragraph. Direct answer in bold, then the reason.
   - `Statutory Provisions` — the sections relied on, with the operative words.
   - `Authorities Cited` — case names in full with court, bench and date, plus
     one line each on what it holds.
6. **Request to the authority** — the polite escalation (see below).
7. **Conclusion** — numbered points mirroring the summary table.
8. **Signature block** — `For DNR Law Firm / Advocates & Legal Consultants`.

Keep a **long-form** version only when NDR asks to be convinced himself, or when
an advocate needs the reasoning to sign off. Do not volunteer the long version
for an authority-facing letter.

## The "polite escalation" closing (he asks for this explicitly)

Never frame it as a demand. The pattern he wants:

- State your position plainly: on our analysis nothing further is payable.
- "If the registering authority should nevertheless entertain any doubt…"
  request that the question be **referred for determination rather than resolved
  at the counter**.
- Cite the enabling provision for the reference (for Karnataka: **s.31**,
  Deputy Commissioner (Stamps), ₹100 fee, **s.32** certificate, and the
  **s.31(1)(b) proviso** relieving penalty on payment of the determined duty).
- Frame the reference as **protecting the officer too** — a reasoned appealable
  determination instead of a counter-level decision with no notice and no appeal.
- End with willingness to file and abide by the determination.

He summarised the intent as: *"should be more like a request… if they still feel
uncomfortable, get a deputy commissioner's opinion."*

## Framing discipline

- **Take the neutral view first when asked for it.** He says "forget my view…
  if you were the sub-registrar, how would you compute it?" — lead with the
  worst-case revenue view, quantify it, *then* give the position that prevails
  and say why. He trusts this far more than a one-sided brief.
- **Label illustrative numbers as illustrative.** State which inputs you could
  not verify (guidance value, current levy table) rather than presenting a
  computed rupee figure as settled.
- **Correct him where the record contradicts him** — but do it explicitly and
  late, after giving him the answer he wants. See
  `references/karnataka-stamp-duty-jda-addendum.md` for a worked example where
  his framing was right in substance but wrong on one limb.
- **Always carry the disclaimer**: research-backed draft formatted as a firm
  opinion, not signed by a licensed advocate; have counsel vet before it goes on
  the record. He has never objected to this and it protects him.

## The e-stamp certificate is the killer exhibit

For any executed Indian instrument, **page 1 of the PDF carries an e-Stamp
Certificate** in a data block. Read it — it is the State's own classification of
the document and often decides the chargeability argument outright.

Extract: certificate number, issue date/time, **"Description of Document"**
(this is the Article under the stamp schedule), property description,
consideration, and **stamp duty paid**.

Worked example: an "Addendum to JDA" showed
`Article 5(J) — Agreement (in any other cases)`, consideration `Rs. 0 (Zero)`,
duty `Rs. 500`. That is the revenue's own system saying the instrument is a
residual fixed-duty agreement, not a 2% development agreement — cite the
certificate number in the opinion and attach it.

---

## Delivery pipeline — HTML → A4 PDF → Drive

NDR's standing preference: deliverables as **Drive links (public-read)**, not
chat attachments. `professional-documents` / `html-presentations` cover the
general pipeline; the notes below are the specifics that bite.

### 1. Write HTML with the template CSS

Copy `templates/dnr-law-firm-opinion.html`. Named colours: navy `#14324f`,
muted `#5b6b7b`, gold accent `#a8802f`, green `#1c6b3a`, red `#8b1a1a`.
Serif throughout (Georgia). Justified body text. Numbered paragraphs.

### 2. Render to PDF — A4 pitfall

`chrome-headless-shell --print-to-pdf` **defaults to US Letter.** You will get
`612 x 792 pts (letter)` and 7 pages instead of A4 and 6. Fix it in CSS, not in
the command line:

```css
@page { size: A4 portrait; margin: 0; }
@media print {
  body { background: #fff; padding: 0; font-size: 11pt; }
  .doc { box-shadow: none; padding: 14mm 14mm; max-width: none; }
  h2 { page-break-after: avoid; }
  table.gen, .qa, .ans, .auth, .stat { page-break-inside: avoid; }
}
```

Locate the browser binary rather than hardcoding a path (it moves with Playwright
updates):

```bash
find / -name "chrome-headless-shell" -type f -executable 2>/dev/null | head -1
```

Then render:

```bash
"$SHELL_BIN" --headless --no-sandbox --disable-gpu --disable-dev-shm-usage \
  --no-pdf-header-footer --print-to-pdf=OUT.pdf "file:///ABS/PATH/IN.html"
```

`--no-pdf-header-footer` is required or Chromium stamps URL/date margins.
Harmless stderr noise about dbus / Floss / vaapi is expected — check that the
binary reports `N bytes written to file`.

### 3. Verify before delivering

```bash
pdfinfo OUT.pdf | grep -E "Pages|Page size"     # want: A4, and the page count
pdftoppm -png -r 90 -f 1 -l 2 OUT.pdf preview   # then vision_analyze page 1
```

Always eyeball page 1. Confirm letterhead, banner, meta table and the summary
table all render — a broken summary table is the one thing he would notice.

### 4. Upload to Drive

Build the service through the sanctioned auth layer — never a raw token file:

```python
import sys; sys.path.insert(0, "/opt/hermes")
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

svc = build_service("drive", "v3", service_name="google-draas")
# files().create(...) then permissions().create(role="reader", type="anyone")
```

Run this in the **`execute_code` sandbox**, not a terminal subprocess. The
sandbox carries the true session identity; a terminal subprocess does not.

```python
# CORRECT — sandbox, explicit service_name
from tools.gws_auth import build_service
svc = build_service("drive", "v3", service_name="google-draas")
```

Two things that silently break the alternative paths (both hit 2026-09-19):

- **Always pass `service_name` explicitly.** A bare `build_service("drive", "v3")`
  resolves the session's default vault key and can come back
  `RuntimeError: Failed to load google credentials: No google token for user
  ndr-<uid>. Authorize first.` — even though the token plainly exists.
  `load_credentials("google-draas")` succeeds in the same process where bare
  `build_service` fails, which is the tell that this is a key-resolution problem,
  not a missing authorisation.
- **Do not force `HERMES_SESSION_USER_ID` in a terminal subprocess.** Forcing the
  numeric uid makes the vault key it as `ndr-<uid>`, which has no token, so the
  upload fails with the same misleading "Authorize first" error. The sandbox
  needs no forcing.

Never read or reference a token file — always this auth layer.

Upload **both** the PDF (the one to send/print) and the HTML (so he can edit and
re-render). Verify each link returns HTTP 200.

---

## Pitfalls

- **Do not deliver the long-form reasoning to an authority.** He will send it
  back. Lead with the summary table at every length.
- **Do not skip `@page { size: A4 }`** — silent Letter-size output.
- **Do not present a computed duty figure as settled** when the guidance value
  or current levy table is unverified. Give the *method* and mark the rate
  illustrative.
- **Do not omit the neutral/worst-case view** when he asks for it. Answering
  only in his favour reads as advocacy and he will not rely on it.
- **Flag unexamined documents as open gaps inside the opinion**, not just in
  chat — e.g. GPAs whose duty payment could collapse the argument entirely.
