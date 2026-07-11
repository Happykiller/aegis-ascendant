#!/usr/bin/env bash
# Copy the exported Windows build to the Windows filesystem and launch it
# natively (ADR-0002). Usage: deploy-win.sh [-- game_args...]
# Example: deploy-win.sh -- --print-fps
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${ROOT}/build/windows"
DEST_WSL="/mnt/c/tmp/aegis-ascendant"
DEST_WIN='C:\tmp\aegis-ascendant'

log()  { printf '[deploy-win] %s\n' "$*"; }
fail() { printf '[deploy-win] FAILED: %s\n' "$*" >&2; exit 1; }

# Both exe and pck are required (separate pck, spec §27.1).
[[ -f "${SRC}/AegisAscendant.exe" ]] || fail "no build found — run scripts/export-win.sh first"
[[ -f "${SRC}/AegisAscendant.pck" ]] || fail "AegisAscendant.pck missing from build"

GAME_ARGS=()
if [[ "${1:-}" == "--" ]]; then
  shift
  GAME_ARGS=("$@")
fi

log "copying build to ${DEST_WSL}"
mkdir -p "$DEST_WSL"
# Kill any prior instance so it does not hold a lock on the exe (avoids
# "Permission denied" on copy when a previous run was interrupted).
powershell.exe -NoProfile -Command \
  "Get-Process AegisAscendant* -ErrorAction SilentlyContinue | Stop-Process -Force" \
  >/dev/null 2>&1 || true
cp "${SRC}/"* "$DEST_WSL/"
cp "${ROOT}/scripts-win/run.ps1" "$DEST_WSL/"

log "launching on Windows (${DEST_WIN})"
# Always -File with an absolute Windows path: never rely on a UNC \\wsl$ CWD.
# Capture the exit code without tripping `set -e` on a non-zero game exit.
EXIT_CODE=0
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "${DEST_WIN}\\run.ps1" "${GAME_ARGS[@]}" || EXIT_CODE=$?
log "game exited with code ${EXIT_CODE}"
exit "$EXIT_CODE"
