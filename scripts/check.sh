#!/usr/bin/env bash
# Quality gate (spec §28.6, reduced for current phase):
#   1) headless import — fails on non-zero exit OR any ERROR/SCRIPT ERROR line
#      (the import exit code alone is not reliable);
#   2) headless test runner (parse check + unit tests) — fails on non-zero exit.
# Exits non-zero on the first failure.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GODOT="${GODOT_BIN:-$HOME/.local/bin/godot4}"

log()  { printf '[check] %s\n' "$*"; }
fail() { printf '[check] FAILED: %s\n' "$*" >&2; exit 1; }

[[ -x "$GODOT" ]] || fail "godot binary not found at ${GODOT} (run scripts/bootstrap.sh)"

# On a fresh clone, every LFS-tracked binary is a ~130-byte text pointer until
# `git lfs pull` runs. Godot then imports those pointers AS TEXTURES, and the failure
# reads like a pile of corrupt assets rather than a missing fetch — cost one wasted
# diagnosis on 2026-07-20. Name the real cause before spending 30s on the import.
LFS_POINTER="$(git -C "$ROOT" ls-files -z '*.png' '*.glb' '*.wav' '*.ogg' '*.blend' 2>/dev/null \
  | xargs -0 -r grep -l -m1 '^version https://git-lfs' 2>/dev/null | head -1 || true)"
if [[ -n "$LFS_POINTER" ]]; then
  fail "LFS objects not fetched (e.g. ${LFS_POINTER} is still a pointer) — run: git lfs pull"
fi

log "1/2 headless import"
IMPORT_LOG="$(mktemp)"
trap 'rm -f "$IMPORT_LOG"' EXIT
if ! "$GODOT" --headless --path "$ROOT" --import >"$IMPORT_LOG" 2>&1; then
  cat "$IMPORT_LOG"
  fail "import exited non-zero"
fi
if grep -E '^(ERROR|SCRIPT ERROR):' "$IMPORT_LOG" >/dev/null; then
  grep -E '^(ERROR|SCRIPT ERROR):' "$IMPORT_LOG" >&2
  fail "import produced errors"
fi
log "import OK"

log "2/2 test runner (parse check + unit tests)"
if ! "$GODOT" --headless --path "$ROOT" --script res://tests/test_runner.gd; then
  fail "tests failed"
fi

log "ALL GREEN"
