#!/usr/bin/env python3
"""Hermes Google Workspace domain-admin toolkit (domain-wide delegation).

Act on ANY user in the Google Workspace domain as the admin identity, via a
service account with domain-wide delegation (DWD). Credential handling is
delegated to the gws-vault daemon over its Unix socket: the vault is the only
place that stores the DWD service-account key, and it only ever hands it out
to vault admins (fail-closed, audited). This library never sees disk secrets
from the vault's perspective -- the key is fetched in-memory per process and
never written to disk.

┌ DWD SAFETY RULES ──────────────────────────────────────────────────────────┐
│ • get_gws_credentials is admin-only: the vault resolves `session_uid` and   │
│   denies unless role=="admin" or permissions.vault_admin. Never call the   │
│   vault op for a non-admin.                                                │
│ • The DWD service-account key lives ONLY in the vault and, once fetched,    │
│   in this process's memory. It is never written to disk and never logged.   │
│   Use _mask() for any output that mentions it.                              │
│ • Every dwd-mode grant is audited server-side by the vault (peer_uid,       │
│   requester, target).                                                       │
│ • Impersonation uses subject=<target email>. In user mode the target's own  │
│   refresh-token flow is used and subject is omitted.                        │
└──────────────────────────────────────────────────────────────────────────────┘

Operations implemented (each takes a target name/email + the current session
identity): Gmail (search/send/draft/trash/labels), Drive (list/get/create/
update/delete/permissions/transfer-ownership), Docs (create), Contacts
(gdata m8 feed -- list/get/create/update/delete/export vCard 3.0).

Env:
  GWS_VAULT_SOCKET       vault Unix socket (default /run/gws-vault/vault.sock)
  GWS_VAULT_SECRET       admin secret, only needed for non-credential vault
                         writes (also read from /etc/gws-vault.env)
  GWS_VAULT_SYSTEM_ADMIN default session_uid (the admin acting); default
                         ndr@nishantranka.com

Dependencies: google-auth, google-api-python-client, httpx
"""

from __future__ import annotations

import argparse
import base64
import email.mime.base
import email.mime.multipart
import email.mime.text
import email.utils
import html.parser
import json
import logging
import os
import socket
from typing import Any, Optional

from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger("gws_admin")

# ---------------------------------------------------------------------------
# Configuration & constants
# ---------------------------------------------------------------------------

DEFAULT_SYSTEM_ADMIN = "ndr@nishantranka.com"
DWD_SERVICE = "google-dwd"

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]
DOCS_SCOPES = ["https://www.googleapis.com/auth/documents"]
CONTACTS_SCOPES = ["https://www.google.com/m8/feeds/"]
DEFAULT_SCOPES = sorted(set(GMAIL_SCOPES + DRIVE_SCOPES + DOCS_SCOPES + CONTACTS_SCOPES))

# Contacts feed (Google Contacts Data API / "gdata" m8 feeds -- deliberately
# NOT the People API).
CONTACTS_BASE = "https://www.google.com/m8/feeds/contacts/default/base"


def _secret_from_env_file(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("GWS_VAULT_SECRET="):
                    return line.split("=", 1)[1].strip().strip("'\"")
    except OSError:
        pass
    return ""


def _load_secret() -> str:
    secret = os.environ.get("GWS_VAULT_SECRET", "")
    if secret:
        return secret
    for path in ("/etc/gws-vault.env", "/opt/hermes/.env"):
        secret = _secret_from_env_file(path)
        if secret:
            return secret
    return ""


def _mask(value: Any) -> str:
    """Mask a secret for display/logging: '…' + last 4 chars."""
    s = str(value or "").strip()
    if not s:
        return "…"
    return ("\u2026" + s[-4:]) if len(s) > 4 else ("\u2026" + s)


def _system_domain() -> str:
    admin = os.environ.get("GWS_VAULT_SYSTEM_ADMIN", DEFAULT_SYSTEM_ADMIN) or ""
    if "@" not in admin:
        return ""
    return admin.rsplit("@", 1)[1].strip().lower()


def _dwd_allowed_domains() -> set[str]:
    """Allowed DWD domains (direct email targets, no vault identity needed).

    ``GWS_VAULT_DWD_DOMAINS`` (comma-separated) wins when set; otherwise the
    system admin's domain. Mirrors the vault daemon's rule.
    """
    raw = os.environ.get("GWS_VAULT_DWD_DOMAINS", "").strip()
    if raw:
        return {d.strip().lower() for d in raw.split(",") if d.strip()}
    dom = _system_domain()
    return {dom} if dom else set()


def _is_system_domain_email(addr: str) -> bool:
    """True when *addr* looks like a mail address in an allowed DWD domain."""
    a = str(addr or "").strip()
    if "@" not in a or " " in a:
        return False
    local, _, domain = a.partition("@")
    if not local or not domain:
        return False
    return domain.strip().lower() in _dwd_allowed_domains()


# ---------------------------------------------------------------------------
# Vault client (Unix socket, same request/response style as
# admin-app/app/vault_client.py and scripts/vault-gateway.py)
# ---------------------------------------------------------------------------


class VaultError(RuntimeError):
    pass


class VaultClient:
    def __init__(self, socket_path: Optional[str] = None, secret: Optional[str] = None):
        self.socket_path = socket_path or os.environ.get("GWS_VAULT_SOCKET", "/run/gws-vault/vault.sock")
        self.secret = secret if secret is not None else _load_secret()

    def _call(self, payload: dict) -> dict:
        if not self.socket_path or not os.path.exists(self.socket_path):
            raise VaultError(f"Vault socket not found at {self.socket_path}")
        data = (json.dumps(payload) + "\n").encode("utf-8")
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(15)
        try:
            s.connect(self.socket_path)
            s.sendall(data)
            buf = b""
            while b"\n" not in buf:
                chunk = s.recv(65536)
                if not chunk:
                    break
                buf += chunk
            if not buf:
                raise VaultError("Vault closed connection without a response")
            return json.loads(buf.split(b"\n", 1)[0].decode("utf-8"))
        finally:
            try:
                s.close()
            except Exception:  # noqa: BLE001
                pass

    def search_identities(self, query: str, identity_type: Optional[str] = None) -> list[dict]:
        payload = {"op": "search_identities", "query": query}
        if identity_type:
            payload["identity_type"] = identity_type
        resp = self._call(payload)
        if not resp.get("ok"):
            raise VaultError(resp.get("error", "search_identities failed"))
        return resp.get("results", [])

    def get_identity(self, user_id: str) -> dict:
        resp = self._call({"op": "get_identity", "user_id": user_id, "session_uid": user_id})
        if not resp.get("ok"):
            raise VaultError(resp.get("error", "get_identity failed"))
        return resp.get("identity", {})

    def get_gws_credentials(self, session_uid: str, target: str) -> dict:
        """Admin-only credential read for a target. Returns the vault's raw
        response: mode user|dwd, user_id, email, and either token_json or
        needs_auth. token_json is the target's google refresh-token payload
        (user mode) or the DWD service-account key (dwd mode)."""
        resp = self._call({
            "op": "get_gws_credentials",
            "session_uid": session_uid,
            "target": target,
        })
        if not resp.get("ok"):
            raise VaultError(resp.get("error", "get_gws_credentials failed"))
        return resp


# ---------------------------------------------------------------------------
# Target resolution (client-side; the vault is still authoritative)
# ---------------------------------------------------------------------------

def _prefer_email(emails: list[str]) -> str:
    """Pick a canonical email: prefer one ending in the system domain."""
    emails = [e for e in (emails or []) if e]
    if not emails:
        return ""
    domain = _system_domain()
    if domain:
        for e in emails:
            if str(e).strip().lower().endswith("@" + domain):
                return str(e).strip()
    return str(emails[0]).strip()


def resolve_target(vault: VaultClient, name_or_email: str) -> dict:
    """Resolve a person to (user_id, email) via vault search_identities.

    Mirrors the vault's get_gws_credentials resolution rules for the lookup
    side only (never touches credentials): exact email first, then a
    case-insensitive name substring; when a record has several emails, prefer
    one in the system domain. Returns a summary dict (never a token).
    """
    needle = (name_or_email or "").strip()
    if not needle:
        raise VaultError("target is required")
    results = vault.search_identities(needle)
    matched_field = "name"
    if not results and "@" in needle:
        results = vault.search_identities(needle, identity_type="email")
        matched_field = "email"
    if not results:
        # No vault identity, but a bare email in an allowed DWD domain is
        # still a valid target — DWD acts on the account directly (the vault
        # enforces the allowed-domain + admin checks on the credential op).
        if _is_system_domain_email(needle):
            return {
                "user_id": needle,
                "email": needle,
                "name": needle,
                "matched_field": "email",
                "matches": 1,
                "direct": True,
            }
        raise VaultError(f"No identity matches target {needle!r}")

    if len(results) == 1:
        r = results[0]
        emails = r.get("emails") or []
        email = _prefer_email(emails)
        return {
            "user_id": r.get("user_id", ""),
            "email": email,
            "name": r.get("name", ""),
            "matched_field": r.get("matched_field") or matched_field,
            "matches": len(results),
        }

    # Multiple name-substring matches: keep the set so the caller can decide,
    # but still prefer an exact-email hit (search_identities matched by name).
    for r in results:
        if str(r.get("user_id", "")).lower() == needle.lower():
            return {
                "user_id": r.get("user_id", ""),
                "email": _prefer_email(r.get("emails") or []),
                "name": r.get("name", ""),
                "matched_field": "email",
                "matches": len(results),
            }
    raise VaultError(f"Ambiguous target {needle!r}: {len(results)} identities match; be more specific")


# ---------------------------------------------------------------------------
# Credential resolution with in-memory SA key cache
# ---------------------------------------------------------------------------

# Per-process cache of the DWD service-account JSON, keyed by admin email.
# Never written to disk.
_SERVICE_ACCOUNT_CACHE: dict[str, dict] = {}


class NeedsAuthorization(RuntimeError):
    """The target has no personal Google token yet (needs_auth from the vault)."""


class GWSDWActor:
    """Resolve targets to Google API clients, acting as the session admin."""

    def __init__(self, session_uid: Optional[str] = None, vault: Optional[VaultClient] = None):
        self.session_uid = (session_uid
                            or os.environ.get("GWS_VAULT_SYSTEM_ADMIN", "")
                            or DEFAULT_SYSTEM_ADMIN)
        self.vault = vault or VaultClient()

    # ── core ──────────────────────────────────────────────────────────────

    def get_credentials(self, target: str) -> tuple[str, str, Credentials]:
        """Return (mode, email, Credentials) to act AS *target*.

        Raises NeedsAuthorization if the target has no personal token and the
        vault chose user mode. In dwd mode the service-account key is fetched
        from the vault and cached in memory; the returned credentials are
        subject-bound to *target*.
        """
        resp = self.vault.get_gws_credentials(self.session_uid, target)
        email = resp.get("email", "")
        if resp.get("needs_auth"):
            raise NeedsAuthorization(
                f"{email} has no personal Google token yet; authorize them once via the OAuth flow"
            )
        token_json = resp.get("token_json", "")
        try:
            info = json.loads(token_json)
        except json.JSONDecodeError as exc:
            raise VaultError(f"vault returned malformed credential payload: {exc}") from exc

        if resp.get("mode") == "user":
            if not info.get("scopes"):
                info["scopes"] = DEFAULT_SCOPES
            creds = Credentials.from_authorized_user_info(info)
            return "user", email, creds

        if resp.get("mode") == "dwd":
            sa = self._cached_service_account(info)
            creds = sa.with_subject(email)
            return "dwd", email, creds

        raise VaultError(f"vault returned unknown mode: {resp.get('mode')!r}")

    def _cached_service_account(self, sa_info: dict) -> service_account.Credentials:
        key = str(sa_info.get("client_email") or "default")
        if key not in _SERVICE_ACCOUNT_CACHE:
            _SERVICE_ACCOUNT_CACHE[key] = dict(sa_info)
        return service_account.Credentials.from_service_account_info(
            _SERVICE_ACCOUNT_CACHE[key], scopes=DEFAULT_SCOPES
        )

    # ── service factories ─────────────────────────────────────────────────

    def _subject_credentials(self, target: str) -> tuple[str, Credentials]:
        _, email, creds = self.get_credentials(target)
        return email, creds

    def gmail(self, target: str) -> "GmailService":
        _, creds = self._subject_credentials(target)
        return GmailService(creds)

    def drive(self, target: str) -> "DriveService":
        _, creds = self._subject_credentials(target)
        return DriveService(creds)

    def docs(self, target: str) -> "DocsService":
        _, creds = self._subject_credentials(target)
        return DocsService(creds)

    def contacts(self, target: str) -> "ContactsService":
        email, creds = self._subject_credentials(target)
        creds.refresh(GoogleAuthRequest())
        return ContactsService(creds.token, acting_as=email)


# ---------------------------------------------------------------------------
# Gmail
# ---------------------------------------------------------------------------

class GmailService:
    def __init__(self, creds: Credentials):
        self.service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    def search_messages(self, q: str, max_results: int = 25) -> list[dict]:
        resp = self.service.users().messages().list(
            userId="me", q=q, maxResults=max_results
        ).execute()
        return resp.get("messages", [])

    def list_labels(self) -> list[dict]:
        resp = self.service.users().labels().list(userId="me").execute()
        return resp.get("labels", [])

    def _build_mime(self, to, subject, body, cc=None, bcc=None,
                    attachments=None) -> str:
        msg = email.mime.multipart.MIMEMultipart()
        msg["to"] = to
        if cc:
            msg["cc"] = cc
        if bcc:
            msg["bcc"] = bcc
        msg["subject"] = subject
        msg["from"] = "me"
        msg.attach(email.mime.text.MIMEText(body, "plain", "utf-8"))
        for att in attachments or []:
            filename = att.get("filename", "attachment.bin")
            data = base64.b64decode(att.get("data", ""))
            part = email.mime.base.MIMEBase(
                att.get("mime_type", "application/octet-stream").split("/")[0] or "application",
                att.get("mime_type", "application/octet-stream").split("/")[1] or "octet-stream",
            )
            part.set_payload(data)
            email.encoders.encode_base64(part)
            part.add_header("Content-Disposition", "attachment", filename=filename)
            msg.attach(part)
        return msg.as_string()

    def _send(self, raw: str, *, thread_id: Optional[str] = None) -> dict:
        body = {"raw": base64.urlsafe_b64encode(raw.encode("utf-8")).decode()}
        if thread_id:
            body["threadId"] = thread_id
        return self.service.users().messages().send(userId="me", body=body).execute()

    def send_message(self, to, subject, body, cc=None, bcc=None,
                     attachments=None) -> dict:
        raw = self._build_mime(to, subject, body, cc=cc, bcc=bcc, attachments=attachments)
        return self._send(raw)

    def create_draft(self, to, subject, body, cc=None, bcc=None,
                     attachments=None) -> dict:
        raw = self._build_mime(to, subject, body, cc=cc, bcc=bcc, attachments=attachments)
        message = {"raw": base64.urlsafe_b64encode(raw.encode("utf-8")).decode()}
        return self.service.users().drafts().create(
            userId="me", body={"message": message}
        ).execute()

    def delete_message(self, message_id: str) -> dict:
        """Move a message to Trash."""
        return self.service.users().messages().trash(
            userId="me", id=message_id
        ).execute()


# ---------------------------------------------------------------------------
# Google Drive
# ---------------------------------------------------------------------------

class DriveService:
    def __init__(self, creds: Credentials):
        self.service = build("drive", "v3", credentials=creds, cache_discovery=False)

    def list_files(self, query: str, page_size: int = 100) -> list[dict]:
        resp = self.service.files().list(q=query, pageSize=page_size,
                                         fields="files(id,name,mimeType,owners,modifiedTime,size)").execute()
        return resp.get("files", [])

    def get_file_metadata(self, file_id: str) -> dict:
        return self.service.files().get(fileId=file_id, fields="*").execute()

    def create_file(self, name, mime_type="text/plain", content=None,
                    folder_id=None) -> dict:
        body = {"name": name, "mimeType": mime_type}
        if folder_id:
            body["parents"] = [folder_id]
        if content is None:
            return self.service.files().create(body=body, fields="id,name,mimeType").execute()
        return self._upload(body, content, mime_type)

    def _upload(self, body: dict, content: bytes, mime_type: str) -> dict:
        from io import BytesIO
        from googleapiclient.http import MediaIoBaseUpload
        media = MediaIoBaseUpload(BytesIO(content), mimetype=mime_type, resumable=False)
        return self.service.files().create(body=body, media_body=media,
                                           fields="id,name,mimeType").execute()

    def update_file(self, file_id, name=None, content=None, mime_type=None,
                    folder_id=None) -> dict:
        body = {}
        if name is not None:
            body["name"] = name
        if mime_type is not None:
            body["mimeType"] = mime_type
        if folder_id is not None:
            body["parents"] = [folder_id]
        if content is not None:
            from io import BytesIO
            from googleapiclient.http import MediaIoBaseUpload
            media = MediaIoBaseUpload(BytesIO(content), mimetype=mime_type or "application/octet-stream",
                                      resumable=False)
            return self.service.files().update(fileId=file_id, body=body or None,
                                               media_body=media, fields="id,name,mimeType").execute()
        return self.service.files().update(fileId=file_id, body=body or None,
                                           fields="id,name,mimeType").execute()

    def delete_file(self, file_id: str) -> None:
        self.service.files().delete(fileId=file_id).execute()

    def list_permissions(self, file_id: str) -> list[dict]:
        resp = self.service.permissions().list(fileId=file_id,
                                               fields="permissions(id,type,role,emailAddress,displayName)").execute()
        return resp.get("permissions", [])

    def transfer_ownership(self, file_id: str, new_owner_email: str) -> dict:
        """Transfer ownership via the two-step permissions flow.

        Step 1: ensure the new owner already has a permission on the file
        (create one as writer if absent). Step 2: promote that permission to
        owner with ``transferOwnership=true``, which hands the file over.
        """
        perm_id = None
        for p in self.list_permissions(file_id):
            if str(p.get("emailAddress", "")).strip().lower() == new_owner_email.strip().lower():
                perm_id = p.get("id")
                break
        if perm_id is None:
            created = self.service.permissions().create(
                fileId=file_id,
                body={"type": "user", "role": "writer", "emailAddress": new_owner_email},
            ).execute()
            perm_id = created.get("id")
        if not perm_id:
            raise RuntimeError("could not establish a permission for the new owner")
        return self.service.permissions().update(
            fileId=file_id,
            permissionId=perm_id,
            body={"role": "owner"},
            transferOwnership=True,
        ).execute()


# ---------------------------------------------------------------------------
# Google Docs
# ---------------------------------------------------------------------------

class DocsService:
    def __init__(self, creds: Credentials):
        self.service = build("docs", "v1", credentials=creds, cache_discovery=False)

    def create_document(self, title: str, content_html: Optional[str] = None) -> dict:
        doc = self.service.documents().create(body={"title": title}).execute()
        doc_id = doc.get("documentId")
        text = _html_to_text(content_html) if content_html else ""
        if text and doc_id:
            self._insert_text(doc_id, text)
        return doc

    def _insert_text(self, doc_id: str, text: str) -> None:
        requests = [{"insertText": {"location": {"index": 1}, "text": text}}]
        self.service.documents().batchUpdate(
            documentId=doc_id, body={"requests": requests}
        ).execute()


class _HtmlToText(html.parser.HTMLParser):
    """Best-effort HTML -> plain text (keeps paragraph/div/br as newlines)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in ("p", "div", "br", "li", "h1", "h2", "h3", "tr"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("p", "div", "li", "h1", "h2", "h3", "tr"):
            self.parts.append("\n")

    def handle_data(self, data):
        self.parts.append(data)

    def text(self) -> str:
        out = "".join(self.parts)
        out = "\n".join(line.strip() for line in out.splitlines())
        return out.strip("\n") + ("\n" if out.strip() else "")


def _html_to_text(content_html: str) -> str:
    parser = _HtmlToText()
    try:
        parser.feed(content_html or "")
        return parser.text()
    except Exception:  # noqa: BLE001
        return ""


# ---------------------------------------------------------------------------
# Google Contacts (gdata m8 feeds -- deliberately NOT the People API)
# ---------------------------------------------------------------------------

class ContactsService:
    """Thin client for the Google Contacts Data API (m8 feeds).

    Talks to the same Atom/JSON feed the legacy ``gdata`` library used, with an
    OAuth2 bearer token minted for the acted-on user.
    """

    def __init__(self, access_token: str, acting_as: str = ""):
        self.access_token = access_token
        self.acting_as = acting_as
        import httpx
        self._http = httpx.Client(timeout=30)

    def _headers(self, **extra) -> dict:
        headers = {"Authorization": f"OAuth2 {self.access_token}", "GData-Version": "3.0"}
        headers.update(extra)
        return headers

    def _get(self, url: str, params: dict | None = None) -> dict:
        resp = self._http.get(url, headers=self._headers(), params=params or {})
        resp.raise_for_status()
        return resp.json()

    def _post(self, url: str, data: str, etag: Optional[str] = None) -> dict:
        headers = self._headers(**({"If-Match": etag} if etag else {}))
        headers["Content-Type"] = "application/atom+xml"
        resp = self._http.post(url, content=data, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def _delete(self, url: str, etag: str) -> None:
        headers = self._headers(**({"If-Match": etag} if etag else {}))
        resp = self._http.delete(url, headers=headers)
        resp.raise_for_status()

    # ── feeds ─────────────────────────────────────────────────────────────

    def list_contacts(self, max_results: int = 100, query: str = "") -> list[dict]:
        params = {"alt": "json", "max-results": max_results}
        if query:
            params["q"] = query
        data = self._get(CONTACTS_BASE, params)
        return data.get("feed", {}).get("entry", [])

    def get_contact(self, contact_id: str) -> dict:
        return self._get(f"{CONTACTS_BASE}/{contact_id}", {"alt": "json"})

    def create_contact(self, name: str, emails: Optional[list[str]] = None,
                       phones: Optional[list[str]] = None) -> dict:
        return self._post(CONTACTS_BASE, _contact_atom(name, emails, phones))

    def update_contact(self, contact_id: str, name: str,
                       emails: Optional[list[str]] = None,
                       phones: Optional[list[str]] = None,
                       etag: Optional[str] = None) -> dict:
        return self._post(f"{CONTACTS_BASE}/{contact_id}", _contact_atom(name, emails, phones), etag=etag)

    def delete_contact(self, contact_id: str, etag: Optional[str] = None) -> None:
        if not etag:
            etag = (self.get_contact(contact_id).get("gd", {}).get("etag") or "")
        self._delete(f"{CONTACTS_BASE}/{contact_id}", etag)

    def export_contacts(self, fmt: str = "vcard3") -> str:
        """Export all contacts as vCard 3.0 (or vcard4 / atom)."""
        resp = self._http.get(
            CONTACTS_BASE,
            headers=self._headers(),
            params={"alt": "json", "fmt": fmt, "max-results": "1000000"},
        )
        resp.raise_for_status()
        return resp.text


def _contact_atom(name: str, emails: Optional[list[str]] = None,
                  phones: Optional[list[str]] = None) -> str:
    ns = ('xmlns="http://www.w3.org/2005/Atom" '
          'xmlns:gd="http://schemas.google.com/g/2005"')
    parts = [f'<entry {ns}><title type="text">{_xml_escape(name or "")}</title>']
    for i, e in enumerate(emails or []):
        rel = "http://schemas.google.com/g/2005#work" if i == 0 else "http://schemas.google.com/g/2005#other"
        parts.append(f'<gd:email rel="{rel}" address="{_xml_escape(e)}" primary="true" '
                     f'displayName="{_xml_escape(name or "")}"/>')
    for i, p in enumerate(phones or []):
        rel = "http://schemas.google.com/g/2005#work" if i == 0 else "http://schemas.google.com/g/2005#other"
        parts.append(f'<gd:phoneNumber rel="{rel}">{_xml_escape(p)}</gd:phoneNumber>')
    parts.append("</entry>")
    return "".join(parts)


def _xml_escape(value: str) -> str:
    return (str(value)
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cmd_resolve(args) -> int:
    vault = VaultClient()
    info = resolve_target(vault, args.target)
    print(json.dumps(info, indent=2))
    return 0


def _cmd_credentials(args) -> int:
    actor = GWSDWActor(session_uid=args.session_uid)
    mode, email, creds = actor.get_credentials(args.target)
    # Only ever surface identifiers + masked material, never token_json.
    print(json.dumps({
        "mode": mode,
        "user_id": email,
        "email": email,
        "scopes": list(getattr(creds, "scopes", None) or []),
        "token_suffix": _mask(getattr(creds, "token", "")),
        "service_account": _mask(getattr(creds, "service_account_email", "")),
    }, indent=2))
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--session-uid", default=os.environ.get("GWS_VAULT_SYSTEM_ADMIN", DEFAULT_SYSTEM_ADMIN),
                        help="admin identity acting (session_uid); default %(default)s")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    p_resolve = sub.add_parser("resolve", help="resolve a name/email to user_id+email")
    p_resolve.add_argument("target")
    p_resolve.set_defaults(func=_cmd_resolve)

    p_creds = sub.add_parser("credentials", help="resolve credentials mode for a target (no secrets shown)")
    p_creds.add_argument("target")
    p_creds.set_defaults(func=_cmd_credentials)

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())