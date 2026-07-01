import sys
sys.path.insert(0, "/app")
from tools.gws_auth import build_service

# Try People API directory listing
try:
    psvc = build_service("people", "v1", telegram_id="7449813913")
    result = psvc.people().listDirectoryPeople(
        sources=["DIRECTORY_SOURCE_TYPE_DOMAIN_PROFILE"],
        readMask="names,emailAddresses,phoneNumbers"
    ).execute()
    people = result.get("people", [])
    print("Directory people count:", len(people))
    for p in people:
        name = p.get("names", [{}])[0].get("displayName", "")
        emails = [e["value"] for e in p.get("emailAddresses", [])]
        phones = [ph["value"] for ph in p.get("phoneNumbers", [])]
        print("  %s | %s | %s" % (name, emails, phones))
except Exception as e:
    print("People API error:", type(e).__name__, str(e)[:200])

# Also try admin SDK directly with the OAuth token
try:
    from googleapiclient.discovery import build
    from tools.gws_auth import load_credentials
    creds = load_credentials("7449813913")
    admin_svc = build("admin", "directory_v1", credentials=creds)
    result = admin_svc.users().list(domain="draas.com").execute()
    users = result.get("users", [])
    print("\nAdmin SDK users count:", len(users))
    for u in users:
        print("  %s | %s | %s" % (
            u.get("name", {}).get("fullName", ""),
            u.get("primaryEmail", ""),
            [p.get("value") for p in u.get("phones", [])]
        ))
except Exception as e:
    print("Admin SDK error:", type(e).__name__, str(e)[:200])
