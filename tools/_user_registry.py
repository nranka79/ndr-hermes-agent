import json
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_registry_cache: Optional[dict] = None
_registry_mtime: float = 0.0


def _registry_path() -> Path:
    return Path(os.environ.get("HERMES_HOME", "")) / "users.json"


def load_user_registry() -> dict:
    global _registry_cache, _registry_mtime
    path = _registry_path()
    try:
        mtime = path.stat().st_mtime
        if _registry_cache is not None and mtime == _registry_mtime:
            return _registry_cache
        _registry_cache = json.loads(path.read_text(encoding="utf-8"))
        _registry_mtime = mtime
        return _registry_cache
    except Exception as e:
        logger.debug("Could not load user registry: %s", e)
        return {}


def get_user_config(telegram_user_id: str | int) -> dict:
    return load_user_registry().get(str(telegram_user_id), {})
