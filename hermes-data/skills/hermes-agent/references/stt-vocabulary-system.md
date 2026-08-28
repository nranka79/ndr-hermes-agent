# STT Vocabulary / Dictionary System

Improves speech-to-text transcription accuracy by injecting proper nouns and domain-specific terms into faster-whisper's `initial_prompt` and `hotwords` parameters.

## Implementation

**File:** `/opt/hermes/tools/user_vocab.py`

**Storage:** GWS Token Vault (service name `"vocab"`) — NOT flat files anymore.

Vocabulary lives in the same vault that stores OAuth tokens, at `/opt/gws-vault/tokens/{user_id}/vocab`, accessed exclusively through the Unix socket at `/run/gws-vault/vault.sock`. All reads/writes use `tools.gws_vault_client` (`get_token`, `set_token`, `delete_token` with service=`"vocab"`). The vault enforces per-user isolation via `SO_PEERCRED` on read ops.

The old flat files at `HERMES_HOME/vocab/<user_id>.json` (typically `/data/hermes/vocab/`) are **no longer authoritative** — leftover artifacts from before the vault migration.

**API:**
- `load_vocab(user_id)` → `List[str]` — returns the list or `[]`
- `add_terms(user_id, terms)` — merges new terms, dedupes, sorts
- `remove_terms(user_id, terms)` — removes specific terms
- `clear_vocab(user_id)` — deletes the file
- `build_initial_prompt(terms)` — builds a natural sentence for faster-whisper
- `build_hotwords(terms)` — comma-separated hotword string

## Critical: Vocab Keyed by Canonical Vault User ID (Not Raw Telegram ID)

**The vault stores vocab under the canonical user ID (e.g. `ndr-<telegram-id>`), NOT under the raw Telegram numeric ID `ndr`.** This changed during the vault identity-migration (Jul 2026). The canonical ID is obtained via vault's `resolve` operation:

```
resolve(telegram, ndr) → "ndr-<telegram-id>"
resolve(email, ndr@draas.com) → "ndr-<telegram-id>"
```

All identities (Telegram ID, draas.com email, ahfl.in email) resolve to the same canonical ID, so vocab added from one identity is visible from all:

| user_id passed to load_vocab | Session identity used | Finds vocab? |
|------------------------------|----------------------|:------------:|
| `ndr-<telegram-id>` (canonical) | canonical | ✅ Yes — this is how the transcription pipeline calls it |
| `ndr` (raw Telegram) | raw Telegram | ❌ No — stored under canonical ID, not raw ID |
| `ndr@draas.com` (email) | email | ❌ No — stored under canonical ID, not email |

### What this means in practice

The transcription pipeline (`transcription_tools.py:1672`) calls:
```python
terms = load_vocab(user_id)
```
where `user_id` is the **canonical vault user ID** from the session context. So as long as the pipeline receives the canonical ID, vocab lookup works automatically. But when debugging or troubleshooting manually, always use the canonical ID (`ndr-<telegram-id>`), never the raw Telegram ID.

To discover what services exist for a user:
```python
import json, socket
sock = '/run/gws-vault/vault.sock'
req = json.dumps({"op":"list_services","user_id":"ndr","session_uid":"ndr"}).encode()+b'\n'
c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); c.connect(sock); c.sendall(req)
resp = b''
while b'\n' not in resp: chunk = c.recv(4096); resp += chunk if chunk else b'\n'
c.close()
svcs = json.loads(resp.decode()).get("services", [])
```

To resolve a Telegram ID to a canonical user:
```python
req = json.dumps({"op":"resolve","identity_type":"telegram","identity_value":"ndr"}).encode()+b'\n'
# → {"ok": true, "user_id": "ndr@draas.com"}
```

### Migration from Telegram IDs to Email Identities (Historical)

The DRAAS deployment previously used Telegram numeric IDs as session identities. After switching to Google Workspace SSO, session identities changed. However, **the vault still uses Telegram IDs as the storage key** — the identity resolution maps the Telegram ID to the canonical user at read time. Old Telegram-ID-based flat files may still exist at `/data/hermes/vocab/`. These should be:
1. Read and merged into the vault entry (using vault set)
2. Deleted after successful merge

**CRITICAL — the vocab lives in the vault under the Telegram ID key, NOT under the email key.** When you need to add/list/modify vocab, always use the Telegram ID as `user_id`.

## Adding Terms

### User-Facing Interface: `/vocab` Slash Command

The `/vocab` command is handled in `gateway/slash_commands.py` and works on Telegram and CLI:

| Command | What it does |
|---|---|
| `/vocab list` | Show all your terms |
| `/vocab add term1, term2, term3` | Add terms **(comma-separated!)** |
| `/vocab remove term1, term2` | Remove specific terms |
| `/vocab clear` | Delete all terms |

**CRITICAL: comma-separation rule.** The `/vocab add` handler splits input on **commas only** (`remainder.split(",")`). Space-separated words like "anbarasan anbu kantesh" become ONE term ("anbarasan anbu kantesh"), not three. Always use commas: "anbarasan, anbu, kantesh".

### Adding Multiple Terms at Once (Batch)

When the user says "add X, Y, Z to the vocabulary" or sends a list of words by voice or text:

1. **Parse each word as its own separate term.** If the user lists multiple words in a single message/sentence, split them into individual entries. A sentence like "add Hinglish Hindi Marathi Gujarati" should become 4 separate terms, not 1 combined string.

2. **Determine the correct user_id** — usually their email for @draas.com accounts.

3. **Choose the approach:**
   - **Slash command (user-facing):** `/vocab add term1, term2, term3` — works on Telegram or CLI
   - **Programmatic (bulk):** Use `add_terms(user_id, [list of individual terms])` from `user_vocab.py` — reads/writes the vault

4. **Pitfall — the combined-term mistake (real incident, Jul 2026):** User added terms via voice: "add anbarasan anbu kantesh gowri" — space-separated, no commas. The `/vocab add` handler received `"anbarasan anbu kantesh gowri"` as a single argument and stored it as ONE vault entry instead of 4. This completely defeats STT vocabulary no-ops because no spoken word will match the combined string. Always split on commas between terms.

   **If you discover a combined term in the vault:** Delete the broken vault entry and write back the properly split list via vault API (see "Fixing Incorrect Terms" below).

5. **Verification:** Use `/vocab list` or vault get to confirm each term is a separate string element:
   ```json
   ["Byadarhalli", "Palya", "Aamir"]
   ```
   NOT:
   ```json
   ["Byadarhalli, Palya, Aamir"]
   ```

### Adding Terms for a Specific User

When the user asks "add X to the vocabulary":

1. Determine which user_id their voice messages are transcribed under (usually their email for ndr@draas.com, Telegram ID for Telegram DM users)
2. Call `add_terms(user_id, [list of terms])`
3. If the user has multiple identities, ask whether they want terms added to all profiles or just one

## Fixing Incorrect or Merged Terms

If a term was added incorrectly (combined terms, misspelled, unwanted), use the vault API — there is no file to edit.

### Option A: Use `/vocab` commands (end-user)

- `/vocab clear` — wipe everything, then `/vocab add term1, term2, ...`
- `/vocab remove term` — remove individual terms

### Option B: Direct vault API (bulk fixes)

Use the vault's set/delete ops via raw socket:

```python
import json, socket, os
sock = '/run/gws-vault/vault.sock'
secret = os.environ.get('GWS_VAULT_SECRET') or os.environ.get('VAULT_SECRET') or ''

def vault_set(uid, svc, data):
    c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); c.connect(sock)
    c.sendall(json.dumps({"op":"set","user_id":uid,"service":svc,
              "token_json":json.dumps(data,ensure_ascii=False),
              "vault_secret":secret}).encode()+b'\n')
    c.recv(4096); c.close()

def vault_delete(uid, svc):
    c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); c.connect(sock)
    c.sendall(json.dumps({"op":"delete","user_id":uid,"service":svc,
              "vault_secret":secret}).encode()+b'\n')
    c.recv(4096); c.close()
```

**Example: fix combined terms**
```python
# Before: ["anbarasan anbu kantesh"]  — ONE combined term
vault_delete("ndr", "vocab")
terms = sorted({"Anbarasan", "Anbu", "Kantesh", "Gowri", "Manohar"})
vault_set("ndr", "vocab", list(terms))
# After: ["Anbarasan", "Anbu", "Gowri", "Kantesh", "Manohar"]
```

### Verification After Fix

Use vault get to read back and check for combined terms:
```python
req = json.dumps({"op":"get","user_id":"ndr","service":"vocab",
                  "session_uid":"ndr"}).encode()+b'\n'
c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); c.connect(sock)
c.sendall(req)
resp = b''
while True:
    d = c.recv(4096)
    if not d: break; resp += d
    if b'\n' in resp: break
c.close()
r = json.loads(resp.decode())
if r.get('ok'):
    terms = json.loads(r['token_json'])
    combined = [t for t in terms if ',' in t or ' ' in t]
    status = f"WARNING: {len(combined)} combined: {combined}" if combined else "all clean"
    print(f"{len(terms)} terms — {status}")
```

## Persistence

- **Docker image rebuild:** SAFE — vault data lives at `/opt/gws-vault/tokens/` on the host, bind-mounted into the container
- **Gateway restart:** SAFE — vault persistence is independent of the gateway process
- **Vocab is NOT wiped by any normal operation** — only by explicit vault delete

## Checking Current Vocab

Use `/vocab list` slash command on Telegram or CLI.

For debugging (vault inspection):
```python
import json, socket
sock = '/run/gws-vault/vault.sock'
req = json.dumps({"op":"get","user_id":"ndr","service":"vocab",
                  "session_uid":"ndr"}).encode()+b'\n'
c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); c.connect(sock); c.sendall(req)
resp = b''
while True:
    d = c.recv(4096)
    if not d: break; resp += d
    if b'\n' in resp: break
c.close()
r = json.loads(resp.decode())
if r.get('ok'):
    print(json.loads(r['token_json']))
else:
    print(f"No vocab: {r.get('error')}")
```

## Detection Notes

- The user_vocab.py module is imported by the transcription pipeline at `/opt/hermes/tools/transcription_tools.py`
- Terms are injected into every transcription call automatically once saved
- There is no CLI or dashboard UI for managing vocab — it's done programmatically via the tools