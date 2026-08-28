# Drive + Gmail Multi-Prong Search for Graphical Files (Floor Plans, Drawings, Images)

When the user asks you to find a graphical file (floor plan, layout drawing, combined unit plan, brochure image, etc.) that may exist in Drive and/or Gmail — or may not exist at all — use this systematic search methodology.

## The Search Ladder (execute in order, stop when found)

### Tier 1: Drive name-based search (specific folder + broader)

Search the project folder first, then the broader drive with keyword variants:

```python
# Inside the project folder
drive.files().list(q=f"'{folder_id}' in parents", spaces='drive', pageSize=100,
    fields='files(id,name,mimeType,size)').execute()

# Name keyword variants
queries = [
    "name contains 'Crissa' and (name contains '401' or name contains '404')",
    "name contains 'combined' and name contains 'Regalia'",
    "name contains 'combo' and name contains 'floor'",
    "name contains '401' and name contains '404'",
]
```

### Tier 2: Drive fullText search

Content-search across the entire drive for keywords:

```python
drive.files().list(q="fullText contains 'Crissa' and fullText contains 'combined'",
    spaces='drive', pageSize=30, fields='files(id,name)').execute()
```

### Tier 3: Gmail keyword search

Search the user's mailbox for the same keywords:

```python
gmail.users().messages().list(userId='me', q='Crissa 401 404 combined floor', maxResults=10).execute()
```

### Tier 4: Email thread attachment inventory

The file may be an attachment in a specific email thread. Get the full thread and walk all parts:

```python
thread = gmail.users().threads().get(userId='me', id=thread_id, format='full').execute()
for m in thread['messages']:
    parts = [m['payload']]
    while parts:
        part = parts.pop(0)
        if 'parts' in part: parts.extend(part['parts'])
        if part.get('filename'): print(f"  ATTACHMENT: {part['filename']}")
```

### Tier 5: Recursive folder enumeration

Some folders are empty — check ALL subfolders recursively:

```python
subfolders = drive.files().list(q=f"'{parent_id}' in parents and mimeType='application/vnd.google-apps.folder'",
    spaces='drive', pageSize=20, fields='files(id,name)').execute()
for sub in subfolders.get('files', []):
    contents = drive.files().list(q=f"'{sub['id']}' in parents", spaces='drive', pageSize=100).execute()
```

### Tier 6: Keyword family expansion

| Concept | Search terms |
|---------|-------------|
| Combined | combined, combo, merger, merge, merged, amalgamation, joined, together, 401+404, 401-404, 401_and_404 |
| Layout | layout, floor plan, floorplan, plan, drawing, schematic |
| Context | full floor, entire floor, whole floor, typical floor |
| Alternate names | 4th floor, fourth floor, Crissa block, Crissa wing |

### Tier 7: Check the email body for conceptual references

The "combined" concept may exist only in email body text, not as a separate file. For example, an email saying *"Crissa 401 & 404 are on the same 4th floor and can be combined into approx. 4,810 sft if needed"* describes a **capability**, not a file. The user may remember the email text and assume a file exists.

### Tier 8: Cross-reference the brochure

The brochure file (e.g. `BR_Floorplan_Widespread.pdf`) may contain the combined layout as a visual in the building-wide floor plan, even though no separate "combined unit" file exists.

## Reporting absence

When you've exhausted all tiers and the file truly doesn't exist:

1. **State clearly** what was searched and with what queries
2. **List what DOES exist** — individual floor plans, source of the "combined" concept in email body, brochure
3. **Give options:**
   - Forward the individual plans + brochure (the brochure may show the combined layout)
   - Ask the user for the exact filename or source (WhatsApp, physical copy, builder's portal)
   - Check if the combined plan was received as a WhatsApp image (not stored in Drive/Gmail)

## Pitfalls

- **Empty subfolder trap:** A folder named "Documents Provided By [Entity]" may be completely empty. Report this to the user.
- **Email body vs attachment confusion:** The user may remember an email that *mentioned* the combined concept and assume a file was attached. Always check the email body text.
- **Multiple email threads:** The same inventory may have been sent to multiple recipients. Check all related threads (inventory email, coloured floor plans email, various recipients).
- **PDF vs JPG vs PNG:** The same floor plan may exist in multiple formats (PDF from one email, JPG from another, PNG from a third). All are valid representations.
- **Brochure contains the combined layout:** The brochure file may show the combined unit layout on a single page even though a separate "combined" file was never created.
- **Drive folder listing `parents='X' in parents` returns 0 despite files existing:** If a `parents=` query returns 0 but the user is certain files exist, cross-check with a name-based search (see `drive-share-pitfalls.md` — known Drive API quirk).