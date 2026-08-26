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
# Usage :
#   ./scripts/release.sh              # fabrique le livrable dans build/release/
#   ./scripts/release.sh vX.Y.Z       # fabrique PUIS publie la release GitHub
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
VERSION="${1:-}"
DEPOT_RELEASES="Happykiller/aegis-ascendant-releases"
SORTIE="build/release/AegisAscendant.exe"

log() { printf '[release] %s\n' "$*"; }

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

if [ -z "$VERSION" ]; then
	log "livrable pret : $SORTIE"
	log "pour publier : ./scripts/release.sh vX.Y.Z"
	exit 0
fi

command -v gh >/dev/null || { log "gh introuvable — publication impossible"; exit 1; }
log "publication de $VERSION sur $DEPOT_RELEASES"
gh release create "$VERSION" "$SORTIE" \
	--repo "$DEPOT_RELEASES" \
	--title "Aegis Ascendant ${VERSION#v}" \
	--notes-file - <<NOTES
Telechargez **AegisAscendant.exe** et double-cliquez. Rien a installer.

- Windows 10/11 x64
- Aucune dependance, aucun runtime a ajouter
- Le jeu s'ouvre sur son ecran-titre ; Echap pour quitter

Prototype : le contenu evolue d'une version a l'autre.
NOTES
log "publie : https://github.com/$DEPOT_RELEASES/releases/tag/$VERSION"
