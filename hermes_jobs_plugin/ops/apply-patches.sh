#!/usr/bin/env bash
# Apply the hermes-jobs vendor patches to the deployed Hermes checkout.
#
# Each patch is checked and applied INDEPENDENTLY of the others -- an
# earlier version of this script bailed out for ALL patches the moment
# ONE target file already carried its marker, which would have silently
# skipped every later patch forever. Never do that again: one marker,
# one file, one patch, checked on its own.
#
# Usage (on the Hermes host):
#   bash apply-patches.sh                 # apply
#   bash apply-patches.sh --check         # dry run, change nothing
#
# After applying, the gateway must be restarted to reload the modules:
#   docker restart hermes-hermes-1
set -euo pipefail

REPO="${HERMES_AGENT_REPO:-/opt/hermes/hermes-agent}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_DIR="$HERE/patches"
CHECK_ONLY="${1:-}"

cd "$REPO"

# patch_file : target_file : marker_string
PATCHES=(
  "0001-runs-restore-history.patch:gateway/platforms/api_server.py:hermes-jobs: opt-in conversation restore"
  "0002-plugin-command-busy-bypass.patch:hermes_cli/commands.py:hermes-jobs fix (2026-10-26)"
)

any_applied=0
for entry in "${PATCHES[@]}"; do
  IFS=":" read -r patch_name target marker <<< "$entry"
  patch_path="$PATCH_DIR/$patch_name"

  if [[ ! -f "$patch_path" ]]; then
    echo "[error] missing patch file: $patch_path" >&2
    exit 1
  fi

  if grep -qF "$marker" "$target"; then
    echo "[skip]  $patch_name -- $target already carries this patch"
    continue
  fi

  echo "[check] $patch_name"
  git apply --3way --check "$patch_path"

  if [[ "$CHECK_ONLY" == "--check" ]]; then
    echo "[ok]    $patch_name applies cleanly (nothing written)"
    continue
  fi

  echo "[apply] $patch_name"
  git apply --3way "$patch_path"
  python3 -m py_compile "$target"
  any_applied=1
done

if [[ "$CHECK_ONLY" == "--check" ]]; then
  echo "[ok] dry run complete for all patches"
else
  if [[ "$any_applied" == "1" ]]; then
    echo "[ok] patched and byte-compiled. Restart: docker restart hermes-hermes-1"
  else
    echo "[ok] nothing to do -- all patches already applied"
  fi
fi
