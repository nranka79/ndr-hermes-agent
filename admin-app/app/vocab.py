import json
import logging

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from .jinja_env import env
from .vault_client import VaultClient, VaultError

router = APIRouter()
logger = logging.getLogger("admin-app.vocab")

# Must match tools/user_vocab.py SERVICE — the STT vocabulary is stored in the
# vault as a JSON array of strings under this service name, keyed by the
# canonical user_id (e.g. "ndr-1000000001").
VOCAB_SERVICE = "vocab"


def _load_vocab(vault: VaultClient, user_id: str) -> list:
    """Return the user's vocab list, or [] if none stored / unparseable."""
    raw = vault.get_token(user_id, VOCAB_SERVICE)
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(t) for t in data if str(t).strip()]
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("vocab for %s is not valid JSON list: %s", user_id, exc)
    return []


@router.get("/{user_id}")
async def view_vocab(request: Request, user_id: str):
    vault: VaultClient = request.app.state.vault
    try:
        identity = vault.get_identity(user_id)
        if not identity:
            return HTMLResponse(env.get_template("error.html").render(
                user=request.session.get("user"), error=f"User {user_id} not found"
            ), status_code=404)
        terms = _load_vocab(vault, user_id)
    except Exception as e:
        return HTMLResponse(env.get_template("error.html").render(
            user=request.session.get("user"), error=str(e)
        ), status_code=500)
    return HTMLResponse(env.get_template("vocab.html").render(
        user=request.session.get("user"),
        user_id=user_id,
        user_name=identity.get("name", user_id),
        terms=terms,
        vocab_text="\n".join(terms),
    ))


@router.post("/{user_id}")
async def save_vocab(request: Request, user_id: str, vocab_text: str = Form("")):
    """Persist the edited vocab. Accepts newline- or comma-separated terms;
    dedupes and sorts to match tools/user_vocab.save_vocab semantics exactly,
    so the /vocab command and this editor stay byte-for-byte consistent."""
    vault: VaultClient = request.app.state.vault
    # Split on newlines first, then commas within each line.
    raw_terms = []
    for line in vocab_text.replace(",", "\n").splitlines():
        t = line.strip()
        if t:
            raw_terms.append(t)
    cleaned = sorted({t for t in raw_terms})
    try:
        if cleaned:
            vault.set_token(user_id, VOCAB_SERVICE, json.dumps(cleaned, ensure_ascii=False))
        else:
            # Empty list — delete the token entirely (mirrors clear_vocab).
            vault.delete_token(user_id, VOCAB_SERVICE)
    except VaultError as e:
        return HTMLResponse(env.get_template("error.html").render(
            user=request.session.get("user"), error=str(e)
        ), status_code=500)
    return RedirectResponse(url=f"/vocab/{user_id}", status_code=303)
