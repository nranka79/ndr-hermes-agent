#!/usr/bin/env python3
"""Run a property-rd gws script with the vault-client auth fallback.

WHY: In cron contexts there is no Telegram session, so
tools.gws_auth.build_service resolves the wrong session identity and returns a
googleapiclient Resource with bad credentials WITHOUT raising. sheet_io's
get_service() only falls through to _vault_credentials(email) when
build_service RAISES — so the documented `--email ndr@draas.com` fallback
never triggers and every call 403s with "The caller does not have permission".

This shim monkeypatches build_service to raise, forcing get_service through
the vault-client path (resolve email -> get_token -> Credentials), which has
worked for the R&D sheet in cron since 2026-08.

Usage (note PYTHONPATH + pass --email to the target):
  PYTHONPATH=/opt/hermes python3 scripts/vault_fallback_runner.py \
      scripts/pricing_refresh.py --sheet <id> --listings f.json \
      --alert-file a.json --email ndr@draas.com

Works for sheet_io.py read/append, pricing_refresh.py, radius_query.py,
kml_generator.py — anything that imports sheet_io.get_service.
"""
import importlib.util
import sys

sys.path.insert(0, "/opt/hermes")

import tools.gws_auth  # noqa: E402


def _force_raise(*args, **kwargs):
    raise RuntimeError("forced vault fallback (cron shim)")


tools.gws_auth.build_service = _force_raise

target = sys.argv[1]
sys.argv = [target] + sys.argv[2:]
spec = importlib.util.spec_from_file_location("target_mod", target)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
if hasattr(mod, "main"):
    sys.exit(mod.main())
