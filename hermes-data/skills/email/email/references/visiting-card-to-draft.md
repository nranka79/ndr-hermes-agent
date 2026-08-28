# Visiting Card → Contact → Research → Email Draft

Workflow for when the user sends a photo of a visiting card and wants to add the person to contacts, research them, assess Kelsa fit, and send a follow-up note.

## Trigger

User sends a photo/scan of a visiting card and says "add this" / "save this" / "send him a note" / "research this person."

## Canonical Sequence

### 1. Extract card details
- Use `vision_analyze` on the image to extract: name, title, company, phone(s), email, address, qualifications
- Cross-reference with the raw image if OCR output has errors

### 2. Research the person & company
- Search Google Contacts (`searchContacts`) for existing records — avoid duplication
- Use web search or Wikipedia API to research the company (size, sector, relevance)
- Assess role: does the role suggest decision-making authority in workflow/process automation?
- Key dimensions for **Kelsa fit** assessment:
  - **As customer**: does the company have complex workflows that Kelsa could automate?
  - **As partner/reseller**: does the company serve clients who need workflow automation?
  - **As door-opener**: could this person introduce us to broader decision-makers?

### 3. Add to Google Contacts
Use `people().createContact()` with:
- `names`: givenName + familyName + displayName
- `emailAddresses`: work primary
- `phoneNumbers`: work + mobile
- `organizations`: name, title, department
- `addresses`: work with street, city, region, postalCode
- `biographies`: serendipity notes, how/where/when the meeting happened, Kelsa-fit assessment

```python
from tools.gws_auth import build_service
service = build_service('people', 'v1', service_name='google-draas')
result = service.people().createContact(body={...}).execute()
```

### 4. Add to NDR DRAAS Contact Sheet
Append a row to Sheet ID `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g` tab `NDR DRAAS Google contacts.csv`.
Use `sheets.spreadsheets().values().append()` with `valueInputOption='USER_ENTERED'`.

Row format: `[First, Last, ..., Company, Title, Department, Notes, Tags, *, Work, Email, ..., Work Phone, Mobile, ..., Address]`

### 5. Save the card image
Copy the cached image to `/data/hermes/users/ndr/visiting-cards/` with a descriptive filename:
`<First>_<Last>_<Company>_<YYYY-MM-DD>.jpg`

### 6. Draft the follow-up email
Follow the email-drafter workflow. Key elements for this type of email:

- **Thank the person** genuinely for the unexpected/kind interaction
- **Name the serendipity** — connect what they do (managed services, engineering, etc.) with what you do (Kelsa workflow automation)
- **Acknowledge the rushed context** if applicable (you were in a hurry, couldn't talk long)
- **Propose two angles** for Kelsa without being pushy:
  1. Their company using Kelsa internally
  2. Their company offering Kelsa to their own clients (partner model)
- **Soft ask** — "Let me know if 20 minutes works to show you what we've built"

Use plain text for this type of email (personal follow-up, not a report).

## Pitfalls

- `searchContacts(query=...)` may return similar names from other orgs — verify the email domain matches the company on the card before reusing an existing contact
- The NDR DRAAS Contact Sheet row number (4211+) changes as rows are appended — use `append`, not `update` with a hardcoded row number
- Visiting card images cached by vision_analyze disappear after the session — copy to the permanent directory immediately
