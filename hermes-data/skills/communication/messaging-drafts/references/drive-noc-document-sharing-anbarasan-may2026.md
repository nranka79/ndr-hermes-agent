# Google Drive — Restrict to Explicit Viewers

**Date:** 2026-05-27  
**User:** Roshini Ranka  
**Task:** Share NOC documents with Anbarasan (pm2.blr@draas.com) — restrict to explicit viewers only.

## Pattern

When the user says "change share settings to only those explicitly added" or "add [email] as viewer":

```python
from tools.gws_auth import build_service

service = build_service("drive", "v3")

files = [
    ("Document Name", "FILE_ID"),
    # ...
]

for name, fid in files:
    # 1. Remove 'anyone' permission (public link access)
    perms = service.permissions().list(fileId=fid).execute()
    for p in perms.get("permissions", []):
        if p.get("type") == "anyone":
            service.permissions().delete(fileId=fid, permissionId=p.get("id")).execute()
    
    # 2. Add specific email as viewer
    service.permissions().create(
        fileId=fid,
        body={"type": "user", "role": "reader", "emailAddress": "pm2.blr@draas.com"},
        fields="id,emailAddress,role"
    ).execute()
    print(f"  ✅ {name} — 'anyone' removed, pm2.blr@draas.com added as viewer")
```

## Key Files from This Session

| Document | File ID |
|----------|---------|
| Fire NOC (Ranka North Star, Oct 2015) | 1jhHnHZL9U5tc0gbFNpBJTvuWbmD6Xlhv |
| BBMP Plan Sanction (PRJ_0987_21-22) | 1Xzy6gGDJ75aEWEe3HsDAvBl7n9FY_qFX |
| BESCOM Power NOC (2016, Expired) | 199FKYrbso08p-vwHcUjovXuj1RXOLJ4h |
| BWSSB Water & Sewage NOC (2016, Expired) | 12eP9uCkiRdNFRqclQkaPjgxUwFlyILhg |
| AAI Height Clearance NOC (2015, Expired) | 14HNFh2QJ_QOcu49dndLpbgfVBW5sOVd4 |
| AAI Height Clearance NOC (2016, Expired) | 15UKKV2RTyZME3lCFINfrSOTVL5aUHLko |
| KSPCB Consent for Establishment (2021, Valid till 2026) | 1HgRKyV5iTAYiO4FckvVdsd3-SFzjEILI |
| GFTS Height Clearance (2015, Expired) | 12Ni1Fwm-Oz4gYpluzulqB5OBN3QZqW2z |

**NOC Tracker Sheet:** 1Zy0geB_PT7BDrJa02Do2ktg9jMCyFfb-jIzU5HSGny4

## Anbarasan Contact (DRA — Project Manager)

Found in "DRA Contact Updated List 2016" (ID: 16LYrhAAiAib9I_lIHjdu9CNRU8nszvXQ2b0rvO7T-sY), Row 27:
- **Name:** ANBARASAN
- **Role:** DRA — Project Manager
- **Phones:** 8792227985 / 9036600055 / 8150029900 / 9036513535
- **Also noted:** TN# 9500215559 / 9994213535

## User Preference — Share Settings

Roshini's consistent instruction: when sharing business documents externally, remove "anyone with link" access and add the specific recipient's email as viewer explicitly. Never leave documents publicly accessible for external sharing.

## Ampersand in WhatsApp URL — Fullwidth Fix (Roshini Preference)

When the message body contains `&` (e.g., "BWSSB Water & Sewage NOC"), replace with **fullwidth ampersand ＆** (U+FF06) before URL-encoding. Do NOT use `%2526` — the fullwidth version is what works on this user's mobile WhatsApp.

```python
# WRONG — causes encoding break on mobile
message = "BWSSB Water & Sewage NOC"

# CORRECT — fullwidth ampersand survives WhatsApp WebView parsing
message = "BWSSB Water ＆ Sewage NOC"
encoded = urllib.parse.quote(message, safe='')
```