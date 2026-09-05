#!/usr/bin/env bash
# Export the Windows x64 build (spec §27). Usage: export-win.sh [debug|release]
# Runs the quality gate first, refuses to export on red (spec §28.6).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GODOT="${GODOT_BIN:-$HOME/.local/bin/godot4}"
TARGET="${1:-debug}"
PRESET="Windows Desktop"
OUT_DIR="${ROOT}/build/windows"
OUT_EXE="${OUT_DIR}/AegisAscendant.exe"

log()  { printf '[export-win] %s\n' "$*"; }
fail() { printf '[export-win] FAILED: %s\n' "$*" >&2; exit 1; }

case "$TARGET" in
  debug)   EXPORT_FLAG="--export-debug" ;;
  release) EXPORT_FLAG="--export-release" ;;
  *) fail "unknown target '${TARGET}' (want debug|release)" ;;
esac

log "quality gate first"
"${ROOT}/scripts/check.sh"

log "exporting ${TARGET} build"
mkdir -p "$OUT_DIR"   # target directory must exist (Godot CLI requirement)
touch "${ROOT}/build/.gdignore"   # keep Godot from scanning build outputs
EXPORT_LOG="$(mktemp)"
trap 'rm -f "$EXPORT_LOG"' EXIT
if ! "$GODOT" --headless --path "$ROOT" "$EXPORT_FLAG" "$PRESET" "build/windows/AegisAscendant.exe" >"$EXPORT_LOG" 2>&1; then
  cat "$EXPORT_LOG"
  fail "export exited non-zero"
fi
if grep -E '^(ERROR|SCRIPT ERROR):' "$EXPORT_LOG" >/dev/null; then
  grep -E '^(ERROR|SCRIPT ERROR):' "$EXPORT_LOG" >&2
  fail "export produced errors"
fi

# ⚠️ ANGLE MORT COMBLE (2026-09-05, montee 4.7 -> 4.7.2). La sortie de l'exporteur part
# dans un log temporaire et n'etait affichee QUE sur erreur : un WARNING d'export ne
# remontait jamais a l'ecran. Or c'est exactement la que se voit une migration de moteur
# ou de templates — une ressource depreciee, un format d'import qui change, une option
# de preset qui n'existe plus. Il a fallu relancer l'exporteur a la main pour lire le
# log entier et pouvoir affirmer « zero avertissement ».
#
# Les avertissements ne font PAS echouer l'export : ils s'affichent, comptes, et c'est au
# lecteur de trancher. Un garde qui ferait rougir la porte sur un warning benin finirait
# contourne, ce qui coute plus que la regle ne rapporte.
WARN_COUNT="$(grep -cE '^(WARNING|USER WARNING):' "$EXPORT_LOG" || true)"
if [[ "$WARN_COUNT" -gt 0 ]]; then
  log "⚠️ ${WARN_COUNT} avertissement(s) d'export — a lire, ils ne bloquent pas :"
  grep -E '^(WARNING|USER WARNING):' "$EXPORT_LOG" | sort | uniq -c | sed 's/^/    /' >&2
else
  log "export sans avertissement"
fi

# Sanity: files exist with plausible sizes (exe embeds the engine: tens of MB).
[[ -f "$OUT_EXE" ]] || fail "missing ${OUT_EXE}"
[[ -f "${OUT_DIR}/AegisAscendant.pck" ]] || fail "missing AegisAscendant.pck"
EXE_SIZE=$(stat -c%s "$OUT_EXE")
PCK_SIZE=$(stat -c%s "${OUT_DIR}/AegisAscendant.pck")
(( EXE_SIZE > 10000000 )) || fail "exe suspiciously small (${EXE_SIZE} bytes)"
(( PCK_SIZE > 1000 ))     || fail "pck suspiciously small (${PCK_SIZE} bytes)"

# Companion files + manifest
cp "${ROOT}/LICENSES.md" "${OUT_DIR}/LICENSES.txt"
{
  echo "Aegis Ascendant — prototype (${TARGET} build)"
  echo "Run AegisAscendant.exe (keep AegisAscendant.pck next to it)."
} > "${OUT_DIR}/README.txt"
( cd "$OUT_DIR" && sha256sum ./*.exe ./*.pck > manifest.txt )

log "OK — $(du -h "$OUT_EXE" | cut -f1) exe, $(du -h "${OUT_DIR}/AegisAscendant.pck" | cut -f1) pck in build/windows/"
