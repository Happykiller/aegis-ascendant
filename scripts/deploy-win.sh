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

# powershell.exe is NOT always on the PATH. WSL's Windows-PATH interop can be off
# (appendWindowsPath=false, or a login profile that rebuilds PATH from scratch) while
# interop itself still works fine — observed on the Quadro T1000 machine, 2026-07-20,
# where every deploy died on "powershell.exe: commande introuvable" even though the
# binary answered perfectly by absolute path. Resolve, then fall back, then say so.
PS_EXE="$(command -v powershell.exe 2>/dev/null || true)"
[[ -n "$PS_EXE" ]] || PS_EXE="/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
[[ -x "$PS_EXE" ]] || fail "powershell.exe not found (WSL interop unavailable?) — tried PATH and ${PS_EXE}"

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
# Kill any prior instance: it holds a lock on the exe.
"$PS_EXE" -NoProfile -Command \
  "Get-Process AegisAscendant* -ErrorAction SilentlyContinue | Stop-Process -Force" \
  >/dev/null 2>&1 || true
# Killing is not enough. Windows releases the file handle ASYNCHRONOUSLY, so a copy
# issued straight after the kill fails with "Permission denied" — which then reads
# like broken WSL permissions and sends you hunting the wrong bug. It cost five
# false starts on 2026-07-12. Wait for the handle, and say so if it never comes.
for attempt in $(seq 1 20); do
  if cp "${SRC}/"* "$DEST_WSL/" 2>/dev/null; then
    break
  fi
  if [[ $attempt -eq 1 ]]; then
    log "exe still locked (a prior instance is dying) — waiting for Windows to release it"
  fi
  if [[ $attempt -eq 20 ]]; then
    fail "exe still locked after 10s — a game process is stuck; kill it by hand"
  fi
  sleep 0.5
done
cp "${ROOT}/scripts-win/run.ps1" "$DEST_WSL/"

log "launching on Windows (${DEST_WIN})"
# Always -File with an absolute Windows path: never rely on a UNC \\wsl$ CWD.
# Capture the exit code without tripping `set -e` on a non-zero game exit.
EXIT_CODE=0
"$PS_EXE" -NoProfile -ExecutionPolicy Bypass -File "${DEST_WIN}\\run.ps1" "${GAME_ARGS[@]}" || EXIT_CODE=$?
log "game exited with code ${EXIT_CODE}"
exit "$EXIT_CODE"
