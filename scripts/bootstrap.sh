#!/usr/bin/env bash
# Bootstrap the Aegis Ascendant dev environment inside WSL.
# Installs Godot 4.7-stable (Linux x86_64) and the Windows export templates,
# with SHA512 verification against the official release sums.
# Idempotent: safe to re-run; skips anything already installed.
set -euo pipefail

GODOT_VERSION="4.7-stable"
GODOT_TEMPLATE_DIR_NAME="4.7.stable" # VERSION_NUMBER.VERSION_STATUS (patch 0 omitted)
BASE_URL="https://github.com/godotengine/godot/releases/download/${GODOT_VERSION}"
BIN_ZIP="Godot_v${GODOT_VERSION}_linux.x86_64.zip"
BIN_NAME="Godot_v${GODOT_VERSION}_linux.x86_64"
TPZ="Godot_v${GODOT_VERSION}_export_templates.tpz"
SUMS="SHA512-SUMS.txt"

CACHE_DIR="${HOME}/.cache/aegis-bootstrap"
INSTALL_DIR="${HOME}/.local/opt/godot-${GODOT_VERSION}"
BIN_LINK="${HOME}/.local/bin/godot4"
TEMPLATES_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/godot/export_templates/${GODOT_TEMPLATE_DIR_NAME}"

log()  { printf '[bootstrap] %s\n' "$*"; }
fail() { printf '[bootstrap] ERROR: %s\n' "$*" >&2; exit 1; }

command -v curl >/dev/null   || fail "curl is required"
command -v unzip >/dev/null  || fail "unzip is required"
command -v sha512sum >/dev/null || fail "sha512sum is required"

mkdir -p "$CACHE_DIR"

fetch() {
  local file="$1"
  if [[ -f "${CACHE_DIR}/${file}" ]]; then
    log "cached: ${file}"
  else
    log "downloading: ${file}"
    curl -fL --retry 3 -o "${CACHE_DIR}/${file}.part" "${BASE_URL}/${file}" \
      || fail "download failed: ${file}"
    mv "${CACHE_DIR}/${file}.part" "${CACHE_DIR}/${file}"
  fi
}

fetch "$SUMS"
fetch "$BIN_ZIP"
fetch "$TPZ"

log "verifying SHA512 checksums"
(
  cd "$CACHE_DIR"
  grep -E "(${BIN_ZIP}|${TPZ})\$" "$SUMS" | sha512sum -c - \
    || fail "checksum verification failed"
)

# --- Godot binary ---------------------------------------------------------
if [[ -x "${INSTALL_DIR}/${BIN_NAME}" ]]; then
  log "godot binary already installed"
else
  log "installing godot to ${INSTALL_DIR}"
  mkdir -p "$INSTALL_DIR"
  unzip -oq "${CACHE_DIR}/${BIN_ZIP}" -d "$INSTALL_DIR"
  chmod +x "${INSTALL_DIR}/${BIN_NAME}"
fi

mkdir -p "$(dirname "$BIN_LINK")"
ln -sf "${INSTALL_DIR}/${BIN_NAME}" "$BIN_LINK"

# --- Export templates ------------------------------------------------------
if [[ -f "${TEMPLATES_DIR}/windows_release_x86_64.exe" \
   && -f "${TEMPLATES_DIR}/windows_debug_x86_64.exe" ]]; then
  log "export templates already installed"
else
  log "installing export templates to ${TEMPLATES_DIR}"
  TMP_DIR="$(mktemp -d)"
  trap 'rm -rf "$TMP_DIR"' EXIT
  unzip -oq "${CACHE_DIR}/${TPZ}" -d "$TMP_DIR"
  [[ -d "${TMP_DIR}/templates" ]] || fail "unexpected tpz layout (no templates/ root)"
  mkdir -p "$TEMPLATES_DIR"
  mv "${TMP_DIR}/templates/"* "$TEMPLATES_DIR/"
fi

# --- Final checks ----------------------------------------------------------
VERSION_OUTPUT="$("$BIN_LINK" --version 2>/dev/null | tail -n 1)"
[[ "$VERSION_OUTPUT" == 4.7.stable* ]] \
  || fail "unexpected godot version: '${VERSION_OUTPUT}' (want 4.7.stable*)"
for tpl in windows_release_x86_64.exe windows_debug_x86_64.exe; do
  [[ -f "${TEMPLATES_DIR}/${tpl}" ]] || fail "missing template: ${tpl}"
done

log "OK — godot ${VERSION_OUTPUT} at ${BIN_LINK}"
log "OK — windows export templates in ${TEMPLATES_DIR}"
