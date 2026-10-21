# Gunjur Sy 40 — Preliminary Title Opinion Collection Checklist (P-119)

Session detail for the NDR rule "opinion furnish-list → verbatim colleague checklist".
Built 2026-09-04 from BRK Law's Preliminary Title Report; delivered to Vinod (Rahul) as
task P-119 (email draft r2170091947646310728, WhatsApp 2-part link).

## Property
- Sy No. 40, Gunjur Village, Tubagere Hobli, Doddaballapur Taluk, Bengaluru Rural
- 18 acres 21 guntas; old splits 40/P1 and 40/P2
- Opinion: B. R. Krishna / BRK Law (krishna@brklaw.in), dated 03-09-2026, File 158/25,
  Bill No. 99 = ₹9,26,250 (NDR counter-offer: ~₹25k/acre × ~18A ≈ ₹4.5L, adjust paid amount)
- Chain top-line: grant to B. Thippaiah → RTC continuity under Patel Hanume Gowda →
  ... → Smt. Kamalamma & others → Dharmesh D. Ranka (sale deed 20-09-2004), via the
  Jaravabai/Wills chain (see gunjur-dodballapur-jaravabai-chain.md)

## Where the furnish-list lives
- Gmail thread `19fd1ffbd3d85cd9` — subject "Gunjur Sy. No. 40 - NIL PTCL & Section 48A
  Endorsements (Grant Clearance)" (google-draas account)
- Krishna's opinion email msg `1a06749408bb230f` (3-Sep 12:40 UTC) carries the attachment
  **Scanned_Preliminary_Title_Report_3_9_26.pdf**
- The 20-item list is in Section 9 "The following documents shall be furnished for completion
  of the title due diligence" (~lines 988–1064 of pdftotext output)

## Extraction recipe (works because the scan has an embedded text layer)
```python
import sys, base64; sys.path.insert(0, "/opt/hermes")
from tools.gws_auth import build_service
gmail = build_service("gmail", "v1", service_name="google-draas")
msg = gmail.users().messages().get(userId="me", id="1a06749408bb230f", format="full").execute()
# walk payload parts -> body.attachmentId for "Scanned_Preliminary_Title_Report_3_9_26.pdf"
data = gmail.users().messages().attachments().get(userId="me",
        messageId="1a06749408bb230f", id=<attachmentId>).execute()
open("/tmp/report.pdf","wb").write(base64.urlsafe_b64decode(data["data"]))
# then: pdfinfo + pdftotext -layout report.pdf report.txt ; grep for "furnished"
```
No vision/OCR needed — pdftotext pulls the hidden text layer directly. OCR variants to
expect: "KTADB" = KIADB; "Hudbast" = Hadbas; "Karda" = khata records; "PICL/PTCL" = PTCL.

## Full 22-item checklist (as sent, grouped A–F)
A. Grant/title origin (9A 21G grant portion): Grant Order + Grant Certificate + Caste
   Certificate + upset-price receipt (B. Thippaiah); Certificate of Sale + Chalan (treasury)
B. Family/succession: Attested Family Tree of B. Thippaiah (children, spouses, grandchildren,
   Tahsildar attested); Attested Family Tree of Patel Hanumegowda (wives, sons, daughters,
   grandchildren); Death certs B. Thippaiah & T. Thippaiah; Inheritance Cert No. 2/1988-89
C. Court/orders: O.S. No. 196/1991 file (plaint, WS, decree, withdrawal memo, order sheet —
   Munsiff Court, Doddaballapura); Order 15-06-1994 No. 23/1994-95 (Dy Tahsildar,
   Doddaballapura); Order 27-07-1996 No. 6/1996-97 (Asst Tahsildar, Tubagere); MR extracts
   Sr 14/1979-81 & Sr 10/2019-20
D. Revenue records: RTCs 1979-80 to 1983-84 for Sy 40/P1; same for Sy 40/P2 (the gap years —
   report covers 1969-70→1979-79, 1984-85→2018-19, 2019-20→2023-24, 2025-26); Karda; Village
   Map of Gunjur; Hudbast; Survey Sketch (Survey Dept: location, extent, boundaries, road)
E. Acquisition endorsements (no acquisition of Sy 40): LPA; KIADB; KHB; NH/State Highway +
   District Authority (road-widening)
F. Fiscal/EC: up-to-date tax paid receipts; ECs 01-04-1940 to 31-03-2004 AND 22-12-2023 to
   date (report covers 01-04-2004 to 21-12-2023 only)

Deferred to developer (Prestige) full-DD stage — NOT in Rahul's list: public notice, original
verification.

## Status
- Tracker P-119 (Vinod/Rahul, Ongoing): Deliverable G = full checklist above; N notes dated
  [2026-09-04] record the 7→22 item expansion.
- Email draft r2170091947646310728 updated IN PLACE via drafts().update (raw MIME single
  part, To/Subject headers) — never create a duplicate draft.
- WhatsApp: whatsapp_link split into 2 parts (part 1 = intro..item 16, part 2 = items 17..22);
  deliver each part as its own message.