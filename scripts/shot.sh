#!/usr/bin/env bash
# Capturer une image du jeu à un instant donné, et la rendre prête à REGARDER.
#
# Raison d'être : cette procédure a été refaite **onze fois à la main** dans la seule
# session du 2026-09-07, et trois de ses pièges ont coûté un cycle de déploiement
# complet chacun (~90 s). Elle est déterministe de bout en bout : elle s'encode.
#
# Les quatre pièges qu'elle ferme, et qu'aucun ne signale :
#
#   1. `--capture-at=12` SEUL N'ARME RIEN. `ScreenCapture` teste la présence du jeton
#      exact `--capture` (`"--capture" in args`) ; sans lui le jeu se lance, joue, et
#      ne capture jamais. Aucune erreur, aucun avertissement — juste un PNG absent.
#   2. LE PNG PRÉCÉDENT SURVIT. Sans effacement préalable, un lancement raté laisse
#      l'ancienne image en place et l'on juge une capture périmée en croyant voir la
#      dernière modification. C'est le piège le plus coûteux : il rend une CONCLUSION
#      fausse, pas une erreur.
#   3. LE BUILD DEBUG ALLUME `SolidsOverlay` PAR DÉFAUT (`debug_layers()` retombe sur
#      `OS.is_debug_build()`). Juger un rendu sans `--hide-solids`, c'est valider un
#      affichage — cercles de hitbox orange compris — que le joueur ne verra jamais.
#      D'où `--solids` pour le demander explicitement quand on veut vérifier OÙ
#      tombent les hitboxes, ce qui est un autre travail.
#   4. `deploy-win.sh` N'EXPORTE PAS et rend la main à la fermeture du jeu. On passe
#      donc par `play.sh` (qui exporte si nécessaire et pose le `++`) sous `timeout`.
#
# Usage :
#   scripts/shot.sh --at=26 -- --goto-level=long_cortege --goto-stern
#   scripts/shot.sh --at=26 --out=poupe.png -- --goto-stern
#   scripts/shot.sh --at=26 --solids -- --goto-stern     # montre les hitboxes
#
# Rend le chemin WSL de l'image et le temps GPU par image. ⚠️ Le FPS n'est PAS rendu :
# Windows bride la présentation d'une session non regardée, il ne mesure rien.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SHOT="/mnt/c/tmp/aegis-ascendant/capture.png"

AT="12"
OUT=""
SOLIDS="--hide-solids"
DEADLINE=300
GAME_ARGS=()

log()  { printf '[shot] %s\n' "$*"; }
fail() { printf '[shot] FAILED: %s\n' "$*" >&2; exit 1; }

usage() {
	awk 'NR == 1 { next } /^#/ { sub(/^# ?/, ""); print; next } { exit }' "$0"
}

while [[ $# -gt 0 ]]; do
	case "$1" in
		--at=*)  AT="${1#--at=}";  shift ;;
		--out=*) OUT="${1#--out=}"; shift ;;
		--solids) SOLIDS="--show-solids"; shift ;;
		--timeout=*) DEADLINE="${1#--timeout=}"; shift ;;
		-h|--help) usage; exit 0 ;;
		--) shift; GAME_ARGS=("$@"); break ;;
		*) fail "option inconnue : $1 (les drapeaux de JEU vont après « -- »)" ;;
	esac
done

[[ "$AT" =~ ^[0-9]+([.][0-9]+)?$ ]] || fail "--at attend des secondes, reçu « $AT »"

# ⚠️ PIÈGE 2 : effacer AVANT, toujours. Et vérifier que l'effacement a pris — un
# fichier verrouillé par une visionneuse Windows survivrait au `rm` sans un mot.
rm -f "$SHOT"
[[ -e "$SHOT" ]] && fail "l'ancienne capture n'a pas pu être effacée ($SHOT) — une visionneuse la tient ?"

log "capture à ${AT} s (${SOLIDS})"
LOG="$(mktemp)"
trap 'rm -f "$LOG"' EXIT

# ⚠️ PIÈGE 1 : les DEUX jetons. `--capture` arme, `--capture-at` date.
if ! timeout "$DEADLINE" "${ROOT}/scripts/play.sh" -- \
		"${GAME_ARGS[@]}" "$SOLIDS" --capture "--capture-at=${AT}" >"$LOG" 2>&1; then
	log "le lancement a échoué ou dépassé ${DEADLINE} s — journal complet :"
	cat "$LOG" >&2
	exit 1
fi

# ⚠️ EXIGER LA LIGNE `saved`, pas seulement la présence du fichier. Une capture
# écrite avec un code d'erreur non nul existe et est vide.
SAVED="$(grep -E '^\[ScreenCapture\] saved' "$LOG" || true)"
[[ -n "$SAVED" ]] || { log "aucune ligne « saved » — la capture ne s'est pas armée :"; \
	grep -E 'ScreenCapture|Vulkan|SCRIPT ERROR' "$LOG" >&2 || cat "$LOG" >&2; exit 1; }
[[ -s "$SHOT" ]] || fail "la ligne « saved » est là mais le PNG est vide ($SHOT)"

DEST="$SHOT"
if [[ -n "$OUT" ]]; then
	DEST="$OUT"
	[[ "$DEST" == /* ]] || DEST="${SCRATCH_DIR:-${ROOT}/build}/${OUT}"
	mkdir -p "$(dirname "$DEST")"
	cp "$SHOT" "$DEST"
fi

# Ce que le journal contient d'utile, et rien d'autre : la machine (elle TRANCHE — à
# build identique le temps GPU est ×14 entre la RTX 4080 et la Quadro T1000) et le
# coût par image.
grep -E '^Vulkan' "$LOG" | sed 's/^/[shot]   /' || true
printf '[shot]   %s\n' "${SAVED#\[ScreenCapture\] }"
log "image : ${DEST}"
log "⚠️ la REGARDER en 1:1 (tools/inspect-capture.py) — une réduction efface le défaut"
