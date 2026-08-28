#!/usr/bin/env bash
# Quality gate (spec §28.6, reduced for current phase):
#   1) headless import — fails on non-zero exit OR any ERROR/SCRIPT ERROR line
#      (the import exit code alone is not reliable);
#   2) règles dures de CLAUDE.md, appliquées et non plus seulement écrites
#      (scripts/lint-regles.sh) ;
#   3) headless test runner (parse check + unit tests) — fails on non-zero exit,
#      ET sur toute SCRIPT ERROR (une méthode interrompue se déclarait « PASS »).
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

log "1/3 headless import"
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

# ⚠️ LES RÈGLES DURES N'AVAIENT AUCUNE APPLICATION AUTOMATIQUE. Typage, autoloads, `.uid`,
# `validate()` et pointeurs de doc étaient vérifiés à la main, ou en prose par `godot-reviewer`.
# Une règle déterministe s'encode : le 2026-08-28, `MOTEUR.md` a pointé six heures durant une
# fonction qui avait déménagé, et rien dans le dépôt ne pouvait le voir.
log "2/3 regles dures (CLAUDE.md)"
"$ROOT/scripts/lint-regles.sh" || fail "regles dures violees"

# ⚠️ LE CODE DE SORTIE NE SUFFIT PAS, ET C'EST LE MEME PIEGE QUE POUR L'IMPORT CI-DESSUS.
# GDScript n'a pas d'exception : sur un appel invalide il journalise `SCRIPT ERROR` et
# ABANDONNE la methode en cours. Les assertions restantes ne tournent jamais, le tableau des
# echecs reste vide, et le harnais annonce « PASS ». Deux gardes de `test_hud_layout` n'ont
# ainsi rien garde depuis leur ecriture, et la disparition de `_shield_target` est passee au
# travers le 2026-08-28. Le runner refuse desormais une methode a zero assertion ; ce filet-ci
# attrape l'autre moitie du cas — une methode interrompue APRES quelques assertions vertes.
#
# On ne filtre que `SCRIPT ERROR:`. Les `ERROR:` provoques exprès par un test (transitions
# d'etat invalides) passent par `push_error` et gardent leur marqueur `[test] expected error`.
log "3/3 test runner (parse check + unit tests)"
TEST_LOG="$(mktemp)"
trap 'rm -f "$IMPORT_LOG" "$TEST_LOG"' EXIT
set +e
"$GODOT" --headless --path "$ROOT" --script res://tests/test_runner.gd 2>&1 | tee "$TEST_LOG"
TEST_STATUS=${PIPESTATUS[0]}
set -e
if [[ "$TEST_STATUS" -ne 0 ]]; then
  fail "tests failed"
fi
if grep -E '^SCRIPT ERROR:' "$TEST_LOG" >/dev/null; then
  grep -E '^SCRIPT ERROR:' "$TEST_LOG" | sort | uniq -c >&2
  fail "la suite est verte mais elle a leve des erreurs de script — une methode a ete interrompue en silence"
fi

log "ALL GREEN"
