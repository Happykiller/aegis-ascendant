#!/usr/bin/env bash
# Régénère une coque 3D — et le fait de façon DÉTERMINISTE.
#
#   ./scripts/build-hull.sh aegis_citadel          # une coque
#   ./scripts/build-hull.sh --all                  # toutes
#   ./scripts/build-hull.sh --check aegis_citadel  # 2 exécutions + comparaison sha256
#
# POURQUOI CE SCRIPT — ADR-0008 exige que deux exécutions rendent un `.glb`
# byte-identique. Cet invariant est FAUX si Blender tourne multi-thread : le calcul
# des tangentes (mikktspace, activé par ADR-0011) somme en virgule flottante dans un
# ordre qui dépend du nombre de workers. Mesuré le 2026-07-21 sur l'Aegis Citadel :
#
#   blender45 -b     -> 6 à 12 octets divergents entre deux exécutions,
#                       TOUS dans des accesseurs TANGENT
#   blender45 -t 1 -b -> 0 octet divergent
#
# Le défaut est silencieux et trompeur : le Specter-9, qui a proportionnellement
# PLUS d'UV dégénérées (2,97 % contre 0,58 %), reste stable — assez pour faire
# croire que le problème vient du modèle plutôt que de l'ordonnancement.
#
# D'où ce script : le `-t 1` ne doit pas dépendre de qui se souvient de le taper.

set -euo pipefail

cd "$(dirname "$0")/.."

BLENDER="${BLENDER:-blender45}"
BUILD_DIR="tools/blender"

usage() {
    echo "usage: $0 [--check] <nom_de_coque|--all>" >&2
    echo "       les noms disponibles :" >&2
    for f in "$BUILD_DIR"/build_*.py; do
        echo "         $(basename "$f" .py | sed 's/^build_//')" >&2
    done
    exit 2
}

CHECK=0
[ "${1:-}" = "--check" ] && { CHECK=1; shift; }
[ $# -eq 1 ] || usage

if [ "$1" = "--all" ]; then
    TARGETS=()
    for f in "$BUILD_DIR"/build_*.py; do
        TARGETS+=("$(basename "$f" .py | sed 's/^build_//')")
    done
else
    TARGETS=("$1")
fi

for name in "${TARGETS[@]}"; do
    script="$BUILD_DIR/build_${name}.py"
    [ -f "$script" ] || { echo "[build-hull] script introuvable : $script" >&2; exit 1; }

    echo "[build-hull] $name"
    # -t 1 : voir l'en-tête. Ne pas le retirer sans refaire la mesure.
    "$BLENDER" -t 1 -b -P "$script" 2>&1 | grep -Ev "^(Blender|Read blend|$)" || true

    glb=$(grep -oE 'assets/imported/models/[a-z]+/[a-z_0-9]+\.glb' "$script" | head -1)
    [ -n "$glb" ] || { echo "[build-hull]   (sortie .glb non repérée dans le script)"; continue; }

    if [ "$CHECK" -eq 1 ]; then
        first=$(sha256sum "$glb" | cut -d' ' -f1)
        "$BLENDER" -t 1 -b -P "$script" >/dev/null 2>&1
        second=$(sha256sum "$glb" | cut -d' ' -f1)
        if [ "$first" = "$second" ]; then
            echo "[build-hull]   déterminisme OK — $first"
        else
            echo "[build-hull]   ÉCHEC DÉTERMINISME" >&2
            echo "[build-hull]     $first" >&2
            echo "[build-hull]     $second" >&2
            exit 1
        fi
    else
        echo "[build-hull]   $glb — $(sha256sum "$glb" | cut -d' ' -f1)"
    fi
done
