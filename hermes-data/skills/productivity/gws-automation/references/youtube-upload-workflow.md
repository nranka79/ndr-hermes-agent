# YouTube Upload Workflow

Upload a video to YouTube under a Google account via the GWS OAuth system.

## Scope Requirement

The standard `HERMES_GWS_SCOPES` does NOT include YouTube. The needed scope is:
```
https://www.googleapis.com/auth/youtube.upload
```

Without this scope, `build_service("youtube", "v3")` builds OK but every API call returns:
```
HttpError 403: Request had insufficient authentication scopes.
```

## Generating an OAuth URL with YouTube Scope

Since `send_oauth_url` only uses the standard GWS scopes (no YouTube), generate a custom URL:

```bash
/opt/hermes/.venv/bin/python3 -c "
import os
from google_auth_oauthlib.flow import Flow
from tools.gws_auth import _client_config, HERMES_GWS_SCOPES

scopes = list(HERMES_GWS_SCOPES) + ['https://www.googleapis.com/auth/youtube.upload']
flow = Flow.from_client_config(
    _client_config(),
    scopes=scopes,
    redirect_uri='https://transcribe.ahfl.in/gws/auth/callback',
    autogenerate_code_verifier=False,
)

tid = os.environ.get('HERMES_SESSION_USER_ID', '[REDACTED-TID]')
url, _ = flow.authorization_url(
    access_type='offline',
    prompt='consent',
    state=tid,
    login_hint='ndr@draas.com',  # Pre-fill the account
)
print(url)
" 2>&1
```

The URL must be sent to the user in a Telegram message (cannot use `send_oauth_url` — it hardcodes GWS-only scopes).

## After Authorization

Once the user authorizes, the token is stored in the vault under the existing service key (e.g. `google-draas`) with the added YouTube scope. Subsequent `build_service("youtube", "v3")` calls will have upload access.

## Uploading a Video

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

youtube = build_service("youtube", "v3", service_name="google-draas")

body = {
    "snippet": {
        "title": "Video Title",
        "description": "Description text",
    },
    "status": {
        "privacyStatus": "unlisted",  # "private" | "public" | "unlisted"
        "selfDeclaredMadeForKids": False,
    }
}

media = MediaFileUpload("/path/to/video.mp4", mimetype="video/mp4", resumable=True)

request = youtube.videos().insert(
    part="snippet,status",
    body=body,
    media_body=media
)

response = request.execute()
print(f"Video ID: {response['id']}")
print(f"Watch URL: https://youtu.be/{response['id']}")
```

## Large Videos

For videos over 100 MB, use `resumable=True` (as above). The upload is chunked automatically by the Google client library.

## Pitfalls

- The OAuth URL must be generated via `terminal()` (not `execute_code`) because the sandbox lacks `HERMES_OAUTH_CLIENT_ID` and `HERMES_OAUTH_CLIENT_SECRET` env vars.
- The `send_oauth_url` tool cannot be used for YouTube — it hardcodes the GWS scope list without YouTube.
- After authorization, the YouTube scope is merged into the existing token. No separate YouTube-specific token is needed — the same service key works for both GWS and YouTube.
- Uploading the same video twice creates a second video on YouTube — no dedup.
