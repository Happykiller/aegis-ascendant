#!/usr/bin/env bash
# Fabrique le livrable Windows d'Aegis Ascendant : UN SEUL FICHIER .exe.
#
# ⚠️ POURQUOI UN EXE UNIQUE ET NON UN ZIP. Le livrable s'adresse a des gens qui veulent
# ESSAYER le jeu, pas l'installer : « faudrait un livrable simple a installer sous Windows »
# (operateur, 2026-08-26). Un zip demande de decompresser, de garder l'exe et le .pck
# ensemble, et de ne pas lancer le mauvais des deux. Un exe unique se telecharge et se
# double-clique.
#
# Il utilise le preset « Windows Release » (embed_pck=true) et NON celui du cycle de dev :
# `play.sh` compare les sources au .pck pour savoir si le build est perime, et embarquer le
# pck casserait ce test. Deux presets, deux usages.
#
# ⚠️ LA VERSION NE SE SAISIT PAS ICI, ELLE SE LIT. `project.godot` (`config/version`) est la
# seule source : c'est elle que Godot grave dans les metadonnees de l'exe, elle que
# l'ecran-titre et l'ecran de pause affichent, elle qu'un testeur nous citera. Un tag passe a
# la main pouvait donc publier un binaire qui ne le portait pas — et ca ne se voyait sur
# aucun des deux. L'argument reste accepte, mais il doit CONCORDER : il vaut confirmation,
# pas declaration.
#
# Usage :
#   ./scripts/release.sh              # fabrique le livrable dans build/release/
#   ./scripts/release.sh vX.Y.Z       # fabrique PUIS publie — vX.Y.Z doit etre la version du projet
#   ./scripts/release.sh --publish    # publie la version du projet, sans avoir a la retaper
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
ARG="${1:-}"
DEPOT_RELEASES="Happykiller/aegis-ascendant-releases"
SORTIE="build/release/AegisAscendant.exe"

log() { printf '[release] %s\n' "$*"; }

# La version du projet, telle que Godot la lira. Une seule ligne fait foi.
PROJET_VERSION="$(sed -n 's/^config\/version="\(.*\)"$/\1/p' project.godot | head -1)"
[ -n "$PROJET_VERSION" ] || { log "project.godot ne declare pas config/version"; exit 1; }
printf '%s' "$PROJET_VERSION" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$' \
	|| { log "version « $PROJET_VERSION » : il faut MAJEUR.MINEUR.CORRECTIF"; exit 1; }
TAG="v$PROJET_VERSION"

case "$ARG" in
	"")          PUBLIER=0 ;;
	--publish)   PUBLIER=1 ;;
	*)
		PUBLIER=1
		if [ "$ARG" != "$TAG" ]; then
			log "vous demandez $ARG, le projet porte $TAG"
			log "  changez config/version dans project.godot, ou passez $TAG"
			exit 1
		fi
		;;
esac

# Un tag deja publie ne se remplace pas : quelqu'un a peut-etre deja telecharge l'autre.
if [ "$PUBLIER" -eq 1 ] && command -v gh >/dev/null \
		&& gh release view "$TAG" --repo "$DEPOT_RELEASES" >/dev/null 2>&1; then
	log "$TAG est deja publie — montez config/version avant de refaire une release"
	exit 1
fi
log "version du projet : $PROJET_VERSION"

# ⚠️ LA PORTE D'ABORD, ET SANS DISCUSSION. Un livrable qu'on donne a quelqu'un d'autre ne se
# fabrique pas sur un depot dont on n'a pas verifie qu'il est vert.
log "porte de qualite"
./scripts/check.sh >/dev/null || { log "check.sh ROUGE — rien n'est publie"; exit 1; }
log "  vert"

log "export release (exe unique)"
mkdir -p build/release
rm -f "$SORTIE"
godot4 --headless --path . --export-release "Windows Release" "$SORTIE" >/dev/null 2>&1 || true

# ⚠️ ON VERIFIE LE PRODUIT, PAS LE CODE DE RETOUR. Godot rend 0 sur des exports partiels, et
# un .exe de quelques Mo est un export SANS ses donnees : il se lance et affiche un ecran
# vide. La taille est le test le moins cher qui soit.
[ -f "$SORTIE" ] || { log "aucun exe produit"; exit 1; }
TAILLE=$(stat -c%s "$SORTIE")
if [ "$TAILLE" -lt 50000000 ]; then
	log "exe de $((TAILLE/1024/1024)) Mo — trop petit, le pck n'est PAS embarque"
	exit 1
fi
# Et l'inverse : un .pck a cote signifie que le preset n'a pas embarque.
if [ -f "build/release/AegisAscendant.pck" ]; then
	log "un .pck traine a cote — le preset n'embarque pas"
	exit 1
fi
log "  OK — $((TAILLE/1024/1024)) Mo, fichier unique"

if [ "$PUBLIER" -eq 0 ]; then
	log "livrable pret : $SORTIE"
	log "pour publier : ./scripts/release.sh --publish   (soit $TAG)"
	exit 0
fi

command -v gh >/dev/null || { log "gh introuvable — publication impossible"; exit 1; }

# ⚠️ LES NOTES SONT UNE PAGE D'ACCUEIL, PAS UN MODE D'EMPLOI. C'est le seul endroit ou
# quelqu'un qui n'a jamais lance le jeu lit ce qu'il est — l'operateur l'a demande ainsi
# le 2026-08-28 : « on pourrait mettre le lore sur la page d'accueil de la release ».
# Elles vivent donc dans `docs/releases/vX.Y.Z.md`, versionnees et relues comme du
# contenu. Le texte generique ci-dessous ne sert que de repli, pour qu'une release
# reste possible si personne n'a ecrit ses notes.
NOTES_FILE="docs/releases/$TAG.md"
if [ -f "$NOTES_FILE" ]; then
	log "notes : $NOTES_FILE"
else
	NOTES_FILE="$(mktemp)"
	log "⚠️ pas de docs/releases/$TAG.md — notes generiques"
	cat > "$NOTES_FILE" <<NOTES
Telechargez **AegisAscendant.exe** et double-cliquez. Rien a installer.

- Windows 10/11 x64
- Aucune dependance, aucun runtime a ajouter
- Le jeu s'ouvre sur son ecran-titre ; Echap pour quitter

Prototype : le contenu evolue d'une version a l'autre.
NOTES
fi

log "publication de $TAG sur $DEPOT_RELEASES"
gh release create "$TAG" "$SORTIE" \
	--repo "$DEPOT_RELEASES" \
	--title "Aegis Ascendant $PROJET_VERSION" \
	--notes-file "$NOTES_FILE"
log "publie : https://github.com/$DEPOT_RELEASES/releases/tag/$TAG"
