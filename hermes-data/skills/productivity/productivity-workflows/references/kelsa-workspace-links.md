# Kelsa Workspace Pipeline Links — DRAAS / O3 Infotech

Kelsa (kelsa.io) is the no-code SaaS workflow platform built by O3 Infotech. DRAAS uses it for task management across multiple pipelines. Team members refer to Kelsa workspace pipelines as **"pipes"** (e.g., "invoice pipe kelsa" = Invoice Processing pipeline in Kelsa).

## Trigger

- User says: "link from [pipeline name] pipe kelsa"
- User says: "kelsa link for [pipeline]"
- User asks for a specific Kelsa workspace link

## How It Works

Each DRAAS pipeline in Kelsa has a numeric **workspace ID**. The link format is:

```
https://kelsa.io/{workspace_id}/tasks?search_query=scheduled%3Ctoday;assignee:me
```

**Kelsa sends daily Action Items emails** from `no-reply@kelsa.io` (production) or `no-reply@kelsa-staging.xyz` (staging) with subject "Kelsa: Action Items". These emails contain an HTML table that maps pipeline names to workspace IDs.

## Filtering a Workspace by Entity / Vendor / Project

Users often ask for a Kelsa link filtered to a specific entity (e.g., "AJ Architect in invoice pipe"). You can append `search_query=<term>` to the workspace URL:

```
https://kelsa.io/516/tasks?search_query=AJ%20Architect
```

This tells Kelsa to show only tasks matching that query within that pipeline. If the search term has spaces, URL-encode them as `%20`. The exact search syntax is Kelsa-internal (tokenises by word), so use short identifiable terms like the vendor name, project name, or invoice number.

## How to Extract a Workspace ID from a Kelsa Action Items Email

1. Fetch the latest Kelsa Action Items email from the user's Gmail:
   ```python
   gmail.users().messages().list(userId='me', q='from:no-reply@kelsa.io Action Items', maxResults=1)
   ```

2. Get the raw HTML body and parse the table. The HTML structure puts pipeline name in a `<td>` with `background-color: #408de3` (or similar blue header) and the overdue count + workspace link in the next `<td>`:
   ```html
   <td>DRA Invoice Processing</td>
   <td><a href="https://kelsa.io/516/tasks?search_query=...">4</a></td>
   ```

3. To find the workspace ID for a specific pipeline name, search the HTML for the pipeline name text, then extract the href from the nearest anchor tag:
   ```python
   import re
   # After pipeline name "DRA Invoice Processing", find the nearest workspace link
   idx = body.find('DRA Invoice Processing')
   nearby = body[idx:idx+300]
   match = re.search(r'kelsa\.io/(\d+)/tasks', nearby)
   workspace_id = match.group(1)  # e.g., '516'
   ```

4. The link can be fetched via Gmail API:
   ```python
   from tools.gws_auth import build_service
   gmail = build_service('gmail', 'v1')
   m = gmail.users().messages().get(userId='me', id=msg_id, format='full').execute()
   
   def get_html_part(part):
       if part.get('mimeType') == 'text/html':
           data = part.get('body', {}).get('data', '')
           if data:
               return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
       for p in part.get('parts', []):
           result = get_html_part(p)
           if result:
               return result
       return ''
   
   body = get_html_part(m['payload'])
   ```

## DRAAS Pipeline Names → Workspace IDs

These are the production Kelsa workspace IDs as of June 2026 (from Anbarasan's Action Items email). IDs are stable across the organization:

| Pipeline Name | Workspace ID |
|---|---|
| DRA Materials Receipt | 514 |
| **DRA Invoice Processing** | **516** |
| DRA Land Proposal | 519 |
| DRA Partner Debits | 523 |
| DRA PO-WO Issuing | 537 |
| DRA Site Visits | 540 |
| DRA Document Handling | 546 |
| DRA Petty Cash | 555 |
| DRA Snags | 556 |
| DRA Engineering Daily Jobs | 971 |
| DRA Asset Tracking | 1453 |
| DRA Unacceptable Finishes | 1982 |
| DRA Commitments | 2002 |
| DRA Attendance Tracker | 4529 |
| Attendance Tracker (New) | 7711 |

## Per-User Note

Each user gets their own Action Items email with their overdue counts, but workspace IDs are shared across the organization. If the IDs change or new pipelines are added, re-parse the latest Action Items email to get current mappings.

## Keyword Resolution

When a DRAAS team member uses shorthand:
- **"kelsa"** = kelsa.io (the SaaS platform, NOT the Kannada word for "work")
- **"pipe"** = pipeline / workspace in Kelsa  
- **"[subject] pipe"** = that specific Kelsa pipeline (e.g., "invoice pipe" = Invoice Processing pipeline)
- **"link from kelsa"** = a Kelsa workspace URL of the form `https://kelsa.io/{id}/tasks`
