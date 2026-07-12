#!/usr/bin/env bash
# Bootstrap Blender 4.5 LTS (Linux x64) inside WSL, for the scripted 3D asset
# pipeline (ADR-0008). Verified against the official SHA256 sums.
# Idempotent: safe to re-run; skips anything already installed.
#
# Blender is a *tool*, not a runtime dependency of the game: it lives outside the
# repository and is only ever invoked headless (`blender -b -P <script>`).
set -euo pipefail

BLENDER_VERSION="4.5.11"
BLENDER_SERIES="4.5" # download.blender.org groups releases by series
BASE_URL="https://download.blender.org/release/Blender${BLENDER_SERIES}"
TARBALL="blender-${BLENDER_VERSION}-linux-x64.tar.xz"
SUMS="blender-${BLENDER_VERSION}.sha256"

CACHE_DIR="${HOME}/.cache/aegis-bootstrap"
INSTALL_DIR="${HOME}/.local/opt/blender-${BLENDER_VERSION}"
BIN_LINK="${HOME}/.local/bin/blender45"

log()  { printf '[bootstrap-blender] %s\n' "$*"; }
fail() { printf '[bootstrap-blender] ERROR: %s\n' "$*" >&2; exit 1; }

command -v curl >/dev/null      || fail "curl is required"
command -v tar >/dev/null       || fail "tar is required"
command -v sha256sum >/dev/null || fail "sha256sum is required"

mkdir -p "$CACHE_DIR" "$(dirname "$BIN_LINK")"

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

if [[ -x "${INSTALL_DIR}/blender" ]]; then
  log "already installed: ${INSTALL_DIR}"
else
  fetch "$SUMS"
  fetch "$TARBALL"

  log "verifying SHA256 of ${TARBALL}"
  expected="$(grep -F " ${TARBALL}" "${CACHE_DIR}/${SUMS}" | awk '{print $1}')"
  [[ -n "$expected" ]] || fail "no SHA256 entry for ${TARBALL} in ${SUMS}"
  actual="$(sha256sum "${CACHE_DIR}/${TARBALL}" | awk '{print $1}')"
  [[ "$expected" == "$actual" ]] \
    || fail "SHA256 mismatch for ${TARBALL} (expected ${expected}, got ${actual})"

  log "extracting to ${INSTALL_DIR}"
  rm -rf "${INSTALL_DIR}.tmp"
  mkdir -p "${INSTALL_DIR}.tmp"
  tar -xJf "${CACHE_DIR}/${TARBALL}" -C "${INSTALL_DIR}.tmp" --strip-components=1
  rm -rf "$INSTALL_DIR"
  mv "${INSTALL_DIR}.tmp" "$INSTALL_DIR"
fi

ln -sfn "${INSTALL_DIR}/blender" "$BIN_LINK"
log "linked ${BIN_LINK} -> ${INSTALL_DIR}/blender"

# Blender ships its own Python and most libs, but still dynamically links a few
# X11/GL system libraries even in background mode. Fail loudly rather than let a
# forge script die halfway through a bake.
if ! "${BIN_LINK}" -b --version >/dev/null 2>&1; then
  log "headless smoke test failed; missing system libraries:"
  ldd "${INSTALL_DIR}/blender" 2>/dev/null | grep "not found" || true
  fail "install the missing packages (apt), then re-run this script"
fi

log "OK: $("${BIN_LINK}" -b --version | head -n1)"
log "usage: blender45 -b -P tools/blender/build_<unit>.py"
