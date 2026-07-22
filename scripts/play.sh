#!/usr/bin/env bash
# Lancer le jeu pour un test à la main, en garantissant qu'on teste le code COURANT.
#
# Raison d'être : `deploy-win.sh` N'EXPORTE PAS. Il copie et lance ce qui traîne dans
# `build/windows/`. Modifier un script puis appeler `deploy-win.sh` fait donc jouer le
# build PRÉCÉDENT, sans le moindre avertissement — et l'on conclut sur du code qui
# n'est pas le sien. Ce script ferme ce trou : il compare les sources au `.pck` et
# n'exporte que si nécessaire.
#
# Il pose aussi le séparateur `++` tout seul. Sans lui, les drapeaux de jeu sont
# avalés par Godot et **silencieusement ignorés** (`OS.get_cmdline_user_args()` ne
# renvoie que ce qui suit `++`) : la scène demandée ne s'ouvre pas et rien ne le dit.
#
# Usage :
#   scripts/play.sh                          # lance le jeu au menu d'accueil
#   scripts/play.sh -- --goto-codex          # ouvre directement le bestiaire
#   scripts/play.sh -- --goto-graybox --demo # combat, pilote automatique
#   scripts/play.sh --release                # build de sortie au lieu de debug
#   scripts/play.sh --rebuild                # réexporte même si le build est à jour
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PCK="${ROOT}/build/windows/AegisAscendant.pck"
# `build/` est gitignoré : le journal d'export y vit sans polluer le dépôt.
EXPORT_LOG="${ROOT}/build/play-export.log"

FLAVOUR="debug"
FORCE=0
GAME_ARGS=()

log()  { printf '[play] %s\n' "$*"; }
fail() { printf '[play] FAILED: %s\n' "$*" >&2; exit 1; }

## L'aide EST l'en-tête du fichier : deux textes à maintenir divergent toujours, et
## c'est l'aide qui ment en premier. On s'arrête à la première ligne non commentée.
usage() {
	awk 'NR == 1 { next } /^#/ { sub(/^# ?/, ""); print; next } { exit }' "$0"
}

while [[ $# -gt 0 ]]; do
	case "$1" in
		--release) FLAVOUR="release"; shift ;;
		--debug)   FLAVOUR="debug";   shift ;;
		--rebuild) FORCE=1;           shift ;;
		-h|--help) usage; exit 0 ;;
		--) shift; GAME_ARGS=("$@"); break ;;
		*) fail "option inconnue : $1 (les drapeaux de JEU vont après « -- »)" ;;
	esac
done

# Ce qui, modifié, rend le build périmé.
#
# `assets/source` et `docs` en sont absents à dessein : ils ne partent pas dans le
# `.pck` (`.gdignore`), et les y mettre ferait réexporter pour un brief relu.
# `tests/` non plus : un test qui change ne change pas le comportement du jeu, et on
# est ici pour jouer.
WATCHED=(scenes scripts resources shaders assets/imported project.godot export_presets.cfg)

# ⚠️ Filtrer par EXTENSION, pas seulement par dossier. `scripts/` contient tout le
# GDScript du jeu *et* l'outillage bash : sans ce filtre, éditer `play.sh` lui-même
# déclarait le build périmé et relançait un export complet. Un faux positif de plus
# et l'on prend l'habitude de forcer, ce qui ramène le trou qu'on vient de boucher.
BUILT_EXTENSIONS=(gd tscn tres gdshader glb svg png ttf ogg wav import godot cfg)

## Premier fichier source plus récent que le `.pck`, s'il en existe un.
## Le NOMMER et pas seulement répondre oui/non : « ton build est périmé » sans dire
## par quoi laisse penser à un faux positif, et on finit par ajouter `--rebuild`
## partout pour ne plus y penser.
newer_than_build() {
	local paths=()
	local entry
	for entry in "${WATCHED[@]}"; do
		[[ -e "${ROOT}/${entry}" ]] && paths+=("${ROOT}/${entry}")
	done
	[[ ${#paths[@]} -gt 0 ]] || return 0
	local filter=()
	local ext
	for ext in "${BUILT_EXTENSIONS[@]}"; do
		[[ ${#filter[@]} -gt 0 ]] && filter+=(-o)
		filter+=(-name "*.${ext}")
	done
	find "${paths[@]}" -type f \( "${filter[@]}" \) -newer "$PCK" -print -quit 2>/dev/null || true
}

## Export SILENCIEUX, résumé en trois lignes — sauf en cas d'échec, où l'on rend tout.
##
## ⚠️ Ce n'est pas du confort. La porte de qualité crache ~180 lignes, dont des
## `[GameState] BOOT -> CODEX` émis par les TESTS. Mêlées au journal de la partie,
## elles se lisent comme le parcours réel du joueur : on rendrait à l'opérateur une
## chronologie qu'il n'a pas jouée. Le journal de lancement ne doit contenir QUE la
## session.
run_export() {
	mkdir -p "$(dirname "$EXPORT_LOG")"
	if ! "${ROOT}/scripts/export-win.sh" "$FLAVOUR" >"$EXPORT_LOG" 2>&1; then
		log "ECHEC de l'export — journal complet ci-dessous"
		cat "$EXPORT_LOG" >&2
		exit 1
	fi
	grep -E '^=== .*failure|^\[check\] ALL GREEN|^\[export-win\] OK' "$EXPORT_LOG" \
		| sed 's/^/[play]   /' || true
}

if [[ $FORCE -eq 1 ]]; then
	log "réexport demandé (--rebuild)"
	run_export
elif [[ ! -f "$PCK" ]]; then
	log "aucun build : export ${FLAVOUR}"
	run_export
else
	STALE="$(newer_than_build)"
	if [[ -n "$STALE" ]]; then
		log "build périmé (${STALE#"${ROOT}/"} est plus récent) : export ${FLAVOUR}"
		run_export
	else
		log "build à jour — on lance tel quel"
	fi
fi

# `++` posé ici, une fois pour toutes. `exec` : le code de sortie du jeu devient
# celui de ce script, et le processus n'est pas doublé pendant toute la partie.
if [[ ${#GAME_ARGS[@]} -gt 0 ]]; then
	log "drapeaux de jeu : ${GAME_ARGS[*]}"
	exec "${ROOT}/scripts/deploy-win.sh" -- ++ "${GAME_ARGS[@]}"
fi
exec "${ROOT}/scripts/deploy-win.sh"
