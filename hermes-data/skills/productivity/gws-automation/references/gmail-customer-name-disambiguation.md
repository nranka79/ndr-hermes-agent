# Gmail Customer Email History Search — Name Disambiguation

**Problem:** User asks "find all emails about customer X." The inbox has multiple different people with the same name (Abhishek Kumar x4, etc.). A naive name search returns emails for several unrelated customers.

**Real example (Jul 2026):** Nishant asked for "Abhishek Kumar, Koltepatil Mirabilis D607." The inbox contained:
- **Abhishek <peaceabhi@gmail.com>** — D607 (the target)
- **abhishek kumar singh <abhishekattitude@gmail.com>** — E-501 (different customer, same project)
- **Abhishek R <rabhishek@worldofcontrols.com>** — E-301 (different customer)
- **Abhishek Kumar <abhishek@socialbeat.in>** — vendor/lead gen agency (not a customer)

---

## Strategy

### 1. Search by name + project simultaneously

Don't search by name alone. Always pair with project name:

```python
gmail = build_service('gmail', 'v1')

# Start broad, pair name with project
queries = [
    '"Abhishek Kumar" Mirabilis',
    '"Abhishek Kumar" Koltepatil',
    'Abhishek Kumar Mirabilis',
]
```

### 2. Identify distinct people with the same name

After getting results, examine the **From** addresses and associated **unit numbers** to identify how many distinct people match:

```python
# Get metadata for all results
for msg_id in message_ids:
    msg = gmail.users().messages().get(
        userId='me', id=msg_id, format='metadata',
        metadataHeaders=['From', 'To', 'Subject', 'Date']
    ).execute()
    headers = {h['name']: h['value'] for h in msg['payload']['headers']}
    # Note: each distinct email address = likely different person
    # Check subjects for unit numbers (E-501, D607, etc.)
```

**Signs you have multiple customers with the same name:**
- Multiple distinct sender email addresses
- Subjects reference different unit/flat numbers (E-501 vs D607)
- Different date ranges and topics (one is about booking, another about lead gen)
- One replies from `@gmail.com`, another from a corporate domain

### 3. Use the unit number as the definitive disambiguator

Once the user gives you a specific unit (D607), use that to filter:

```python
# Confirm which email belongs to the target unit
result = gmail.users().messages().list(
    userId='me', q='D607', maxResults=50
).execute()
# Cross-reference with the name-search results
```

### 4. Search comprehensively for the identified customer

Once the correct email address is identified (`peaceabhi@gmail.com`), search for ALL their communication:

```python
# Search by their email address
all_customer_msgs = set()
for q in [
    'peaceabhi@gmail.com',                              # direct emails
    '"Registration of flat" "D 607"',                   # registration thread
    'CMP/200812/0005887',                               # RERA complaint number (if filed)
]:
    result = gmail.users().messages().list(userId='me', q=q, maxResults=500).execute()
    for msg in result.get('messages', []):
        all_customer_msgs.add(msg['id'])
```

**Categories of emails to include:**
- Original lead/portal inquiry (may come through a different email, e.g., 99acres)
- Agreement/booking correspondence
- Financial statements and payment receipts
- Internal CRM booking info (emails between team about the customer)
- Registration/handover correspondence
- RERA complaints (search by complaint number, as these may not include the customer's email in To/From)
- Execution notices and court orders
- Maintenance bills (sent to bulk lists, but the unit is listed)

### 5. Present total count + categorized breakdown

Always present:
- **Total email count**
- **Timeline** (earliest to latest)
- **Categorized breakdown** so the user can see what's there without scrolling

```
GRAND TOTAL: 79 emails
Timeline: Aug 2017 – Mar 2024

Lead (99acres):        1 email
Agreement/Booking:     3 emails
Financial Statements:  8 emails
Customer Booking Info: 3 emails
RERA Complaint:        53 emails
Registration of D607:  3 emails
Execution Notice:      5 emails
Other:                 3 emails
```

---

## Pitfalls

- **Same name ≠ same person.** Always verify by email address AND unit number before combining results.
- **The original lead email is often different** from the customer's personal email. A 99acres lead goes to `rangoli.g@draas.com` while the customer replies from `peaceabhi@gmail.com`. Search by the customer's reply address, not just the lead.
- **RERA complaint emails may not have the customer's email in To/From** — they're exchanged between RERA authority, Koltepatil, and you. The customer is a party to the complaint but not always CC'd. Search by complaint number directly.
- **Forwarded emails to ndr@draas.com may arrive with different dates** than original. Validate using the `Date` header, not the inbox receipt date.
- **Deduplicate by message ID** when combining results from multiple queries — the same email can match multiple search terms.
