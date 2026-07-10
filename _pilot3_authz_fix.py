# THROWAWAY — not to be committed. Pilot 3 authz app-gate fix.
import io

path = r"C:\Users\ruhaan\Hermes_Project\gateway\authz_mixin.py"
with io.open(path, "r", encoding="utf-8") as f:
    src = f.read()

old = '''                if _rec:
                    # Per-app access gate (admin.ahfl.in App Access toggles).
                    # Fail-open: an absent apps.telegram key OR True authorizes
                    # (existing users have no apps key and must keep working);
                    # only an explicit False blocks. If the vault is unreachable,
                    # find_user_by_identity raises and we fall through to the env
                    # allowlist below — so a vault outage can never lock out a
                    # user who is in TELEGRAM_ALLOWED_USERS.
                    _apps = (_rec.get("permissions", {}) or {}).get("apps", {}) or {}
                    if _apps.get("telegram") is False:
                        logger.info(
                            "Telegram user %s blocked by admin App Access "
                            "(permissions.apps.telegram=False)", user_id,
                        )
                        return False
                    return True'''

new = '''                if _rec:
                    # Per-app access gate (admin.ahfl.in App Access toggles).
                    # Read apps STRAIGHT FROM THE VAULT, not from _rec:
                    # find_user_by_identity merges the users.json record OVER the
                    # vault record, and users.json carries its own `permissions`
                    # key (with no `apps`), so setdefault keeps the stale file
                    # perms and masks an admin-set apps.telegram=False. Query the
                    # vault directly for the authoritative, live value.
                    # Fail-open: absent apps.telegram key OR True authorizes
                    # (existing users have no apps key and must keep working);
                    # only an explicit False blocks. Vault unreachable => the
                    # inner except falls back to _rec (no block), and the outer
                    # except lets a full outage fall through to the env allowlist
                    # below, so a vault outage can never lock out a user who is in
                    # TELEGRAM_ALLOWED_USERS.
                    _apps = {}
                    try:
                        from tools import gws_vault_client as _vault
                        _cu = _vault.resolve("telegram", user_id)
                        if _cu:
                            _vrec = _vault.get_identity(_cu, session_uid=_cu)
                            _apps = ((_vrec or {}).get("permissions", {}) or {}).get("apps", {}) or {}
                    except Exception:
                        _apps = (_rec.get("permissions", {}) or {}).get("apps", {}) or {}
                    if _apps.get("telegram") is False:
                        logger.info(
                            "Telegram user %s blocked by admin App Access "
                            "(permissions.apps.telegram=False)", user_id,
                        )
                        return False
                    return True'''

if old not in src:
    raise SystemExit("PATCH TARGET NOT FOUND — aborting")
src = src.replace(old, new, 1)
with io.open(path, "w", encoding="utf-8") as f:
    f.write(src)
print("PATCHED authz_mixin.py (vault-direct app-gate)")
