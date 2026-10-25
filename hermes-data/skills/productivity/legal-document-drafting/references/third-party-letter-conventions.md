# Third-party letters & declarations — NDR's conventions (2026-10-11)

Class of task: NDR asks to draft letters FROM a third party (family friend / acquaintance)
to himself, family members, or "To Whomsoever It May Concern", for personal/family use.
Example (11 Oct 2026): "Rupa" → Nishant Ranka (thanks/acknowledgement, up to 3.5),
→ Manish Ranka (same, up to 3.3), → family of late Mr. Dinesh Ranka (declaration clearing
rumours of financial dealings). The intent is risk mitigation: a third party of standing
puts on record that no financial dealing ever existed with the late family member.

## Wording rules (NDR's explicit preferences — respect exactly)

- MINIMAL wording. One idea per sentence. No elaboration.
- Money figures stay BARE and VAGUE: just the number (e.g. "up to 3.5", "up to 3.3").
  NO currency, NO unit (lakh/crore/₹), NO reference to what the amount is about.
- Always include the characterisation NDR wants on record:
  - help is VOLUNTARY, offered "as and when available, based on your availability and capability"
  - "in no way a mandatory obligation" on the giver
  - "I sincerely and truly appreciate this offer of help, which you have voluntarily offered,
    and I am forever thankful and grateful."
- Date = today's date, always.

## Letter anatomy

Thank-you/acknowledgement:
  Title: "LETTER OF THANKS AND ACKNOWLEDGEMENT"
  Date line → "To," + addressee block → "Dear <First name>," → body:
    "I have been associated with your family as a family for many, many years. As of today,
    I acknowledge and deeply appreciate the help you have voluntarily come forward to offer
    me - for my business and financial requirements and other personal needs - up to <N>,
    as and when available, based on your availability and capability." + voluntary/no-obligation
    para + sincere thanks para → "With regards," → signature.

Declaration:
  Title: "DECLARATION" then "TO WHOMSOEVER IT MAY CONCERN"
  "To, The Family of Late Mr. <Name>" → body: rumours circulating are "hearsay, speculative
  and unfounded - nothing more than gossip and baseless conspiracy theory"; "at no stage has
  there been any financial dealing, claim or transaction of any kind" with the late person;
  association is "simply been good family friends for many, many years"; current help is a
  voluntary, independent gesture by the family on reaching out "for my personal and business
  needs, and for the investment needs I am trying to pursue"; close "I am willing to put this
  declaration on record." → "Yours faithfully," → signature.

## Identity & address rules (HARD — never invent)

- Signatory name: use EXACTLY what NDR dictated. If only a first name was dictated
  ("Rupa"), do NOT guess a surname. Flag that the full name can be swapped in on request.
  Note: contacts has "Rupa Shetty Advocate" (+91 95385 33666, "Advocate for N D Durani
  clover greens lands") — NOT confirmed as this signatory; do not assume.
- Addressee postal addresses: NEVER invent. Missing address → visible placeholder line
  "[Address to be entered]" in the addressee block, then ask NDR.
- NDR's own standard address block (verified from Roma Ventures Authorization Letter,
  passport/VoA files, Kanta Ranka's Aadhaar & voter-registration work):
    Mr. Nishant Ranka
    #1503, Embassy Habitat,
    No. 59 Palace Road,
    Bengaluru - 560 001
- Manish Ranka (NDR's brother, Director DRA Projects, mdr@drahomes.in,
  +91 98866 29074): NO postal address on file in contacts as of Oct 2026 — flag to NDR
  when a letter needs his block.

## Creation & delivery workflow

- "Make the documents in my personal email account (gmail.com)" => create as Google Docs
  owned by nishantranka@gmail.com via vault service_name `google-gmail`.
- Docs API (sanctioned path — native drive tools can't fill a native Doc body):
    from tools.gws_auth import build_service
    docs = build_service("docs", "v1", service_name="google-gmail")
    doc = docs.documents().create(body={"title": title}).execute()
    docs.documents().batchUpdate(documentId=doc["documentId"], body={"requests": [{
        "insertText": {"location": {"index": 1}, "text": full_body_with_trailing_newline}}]}).execute()
  body text = lines joined with "\n"; ensure trailing "\n" so the last paragraph renders.
- Doc naming: "YYYYMMDD <Party> - <Doc Type> - <Recipient>"
  e.g. "20261011 Rupa - Letter of Thanks and Acknowledgement - Nishant Ranka".
- ALWAYS verify by reading back: docs.documents().get(documentsId=..., fields="title,body")
  and print the reconstructed text; also drive.files().get(... fields="owners") to confirm
  the owning account is the one requested. Deliver webViewLink.

## Pitfalls

- `clarify` tool may be unavailable in API-server contexts — ask inline in the reply and
  proceed with placeholders rather than blocking the whole deliverable.
- contact_resolver exposes phones/emails/org but NOT postal addresses. For address lookups:
  session_search (e.g. "Embassy Habitat address") + Drive document scans are the reliable
  routes; the resolver's row numbers map to "NDR DRAAS Google contacts" sheet
  (1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g, tab 'NDR DRAAS Google contacts.csv'),
  NOT the older capped "NDR CONTACTS" sheet (1fYa-... , max 1001 rows).