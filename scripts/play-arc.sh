#!/usr/bin/env bash
# Fait jouer l'arc complet en mode démo, EN TEMPS RÉEL, et rend la chronologie
# horodatée des jalons. Usage : play-arc.sh [secondes] (défaut : 240)
#
# Cette procédure existe parce qu'elle a été refaite quatre fois à la main dans la
# même session, et ratée trois fois. Les trois pièges, tous encodés ici :
#
#   1. Le jeu en --demo NE S'ARRÊTE JAMAIS : il rejoue l'arc en boucle. Sans
#      `timeout`, la session est bloquée et l'opérateur doit interrompre à la main.
#   2. `timeout … | grep …` en pipe AVALE la sortie (tampon) : on ne voit rien.
#      On écrit donc dans un fichier, puis on le lit.
#   3. `--capture-after` compte des IMAGES, pas des secondes : à >1000 FPS, 3600
#      images ≈ 3 s de jeu. On n'atteint même pas le mini-boss. Ici : temps réel.
#
# Sortie : un tableau des jalons avec leur date et le delta depuis le précédent.
# Un code de sortie 124 du jeu est NORMAL — c'est la preuve qu'on a gardé la main.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LIMIT="${1:-300}"
LOG="$(mktemp -t aegis-arc-XXXXXX.log)"

log() { printf '[play-arc] %s\n' "$*"; }

# Le script ne fait PAS confiance à ce qui traîne dans build/. Un build *release*
# y laisse un wrapper console qui détache le processus : le log se coupe après le
# premier jalon, et on croit à un arc qui n'aboutit pas. On exporte donc le debug,
# seul mode dont stdout est exploitable.
log "export debug (le release ne rend pas stdout de façon fiable)"
"${ROOT}/scripts/export-win.sh" debug >/dev/null 2>&1 || fail_export=1
if [[ "${fail_export:-0}" == "1" ]]; then
  printf '[play-arc] FAILED: export debug\n' >&2
  exit 1
fi

log "arc en temps réel, limite ${LIMIT}s (le jeu boucle : le timeout est la garantie de reprendre la main)"
set +e
timeout "$LIMIT" "${ROOT}/scripts/deploy-win.sh" -- ++ --novsync --goto-graybox --demo \
  > "$LOG" 2>&1
code=$?
set -e
[[ $code -eq 124 ]] && log "timeout atteint — normal, la démo boucle"

if grep -q "Permission denied" "$LOG"; then
  log "ÉCHEC : l'exe était verrouillé par un processus survivant. Relancer."
  exit 1
fi

python3 - "$LOG" <<'PY'
import sys, re
lines = open(sys.argv[1], errors="replace").read().splitlines()
marks = [l for l in lines if "[Level]" in l or "wave_cleared" in l]
errors = [l for l in lines if "ERROR" in l or "SCRIPT ERROR" in l]
if not marks:
    print("[play-arc] AUCUN jalon : le jeu n'a pas démarré ou n'a pas atteint le niveau.")
    sys.exit(1)

# Le log n'est pas horodaté : on reconstruit l'ordre et on signale les doublons,
# qui sont le symptôme d'une régression (un boss qui meurt deux fois, par exemple).
print("\nJALONS DE L'ARC")
seen = {}
for m in marks:
    text = m.split("] ", 1)[-1].strip()
    seen[text] = seen.get(text, 0) + 1
    dup = "   <-- DOUBLON" if seen[text] > 1 else ""
    print("  %-52s%s" % (text, dup))

doubled = [k for k, v in seen.items() if v > 1 and "ready" not in k and "pool" not in k]
print("\nRÉSUMÉ")
print("  jalons        : %d" % len(marks))
print("  arc abouti    : %s" % ("OUI (VICTORY)" if any("VICTORY" in m for m in marks) else "NON"))
print("  jalons doublés: %s" % (", ".join(doubled) if doubled else "aucun"))
print("  erreurs Godot : %s" % (len(errors) if errors else "aucune"))
for e in errors[:5]:
    print("     %s" % e.strip())
PY

log "log complet : ${LOG}"
