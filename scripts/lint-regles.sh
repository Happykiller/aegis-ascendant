#!/usr/bin/env bash
# Les règles dures de CLAUDE.md, APPLIQUÉES — et non plus seulement écrites.
#
# ⚠️ ELLES N'AVAIENT AUCUNE APPLICATION AUTOMATIQUE. Chaque revue les redérivait à la main
# (huit greps le 2026-08-28) ou en prose via `godot-reviewer`. Une règle déterministe ne se
# capitalise pas en français : elle s'encode. Ce script est la version exécutable de la
# section « Règles de code » de CLAUDE.md ; `godot-reviewer` l'appelle au lieu de le refaire,
# et garde son jugement pour ce qui n'est pas mécanique.
#
# Appelé par `check.sh` (étape 2/3) : une violation ROUGIT la porte.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

FAILURES=0
say()  { printf '[lint] %s\n' "$*"; }
bad()  { printf '[lint] VIOLATION — %s\n' "$*" >&2; FAILURES=$((FAILURES + 1)); }

# Les sources de PRODUCTION. Les tests ont leurs propres libertés (montages à la main,
# transtypages explicites) et le harnais les couvre autrement.
PROD_GD=$(git ls-files 'scripts/*.gd' 'resources/*.gd' 'tools/*.gd')

# --- 1. GDScript typé partout (spec §31) -------------------------------------
# Une déclaration non typée laisse Godot inférer Variant : la faute ne se voit qu'à
# l'exécution, et souvent seulement dans le cas rare.
UNTYPED_VARS=$(grep -nE '^[[:space:]]*(@export[^ ]* )?var [a-zA-Z_][a-zA-Z0-9_]* = ' $PROD_GD || true)
[[ -n "$UNTYPED_VARS" ]] && bad "déclaration non typée (utiliser \`var x: T =\` ou \`var x :=\`) :" \
  && printf '%s\n' "$UNTYPED_VARS" >&2

UNTYPED_FUNCS=$(grep -nE '^[[:space:]]*(static )?func [a-zA-Z_][a-zA-Z0-9_]*\([^)]*\)[[:space:]]*:' $PROD_GD \
  | grep -v '\-> ' || true)
[[ -n "$UNTYPED_FUNCS" ]] && bad "fonction sans type de retour :" \
  && printf '%s\n' "$UNTYPED_FUNCS" >&2

# --- 2. Aucun identifiant global d'autoload dans un script -------------------
# ⚠️ `GameState.foo()` casse la compilation en mode `--script` : les autoloads n'y sont pas
# montés, et TOUTE la suite de tests tombe. Le contournement est le cache typé
# `const XScript := preload(...)` + `@onready var _x: XScript = get_node("/root/X")`.
AUTOLOADS='GameState|SceneRouter|SettingsManager|AudioManager'
AUTOLOAD_HITS=$(grep -nE "(^|[^A-Za-z_.\"'])($AUTOLOADS)\." $PROD_GD 2>/dev/null \
  | grep -vE 'scripts/core/(game_state|scene_router|settings_manager|audio_manager)\.gd:' \
  | grep -vE 'get_node\("/root/' \
  | grep -vE ':[0-9]+:[[:space:]]*#' \
  | grep -vE '(GameState|SceneRouter|SettingsManager|AudioManager)Script' \
  | grep -vE '\.(Phase|State)\b' || true)
[[ -n "$AUTOLOAD_HITS" ]] && bad "identifiant d'autoload utilisé directement (casse le mode --script) :" \
  && printf '%s\n' "$AUTOLOAD_HITS" >&2

# --- 3. Les `*.uid` sont committés -------------------------------------------
# Godot les régénère, mais un `.uid` absent du dépôt casse les références de scène chez le
# suivant qui clone.
MISSING_UID=""
for f in $(git ls-files '*.gd'); do
  git ls-files --error-unmatch "$f.uid" >/dev/null 2>&1 || MISSING_UID="$MISSING_UID $f.uid"
done
[[ -n "$MISSING_UID" ]] && bad "\`.uid\` non suivi(s) par git :$MISSING_UID"

# --- 4. Toute Resource de gameplay se valide (spec §31) ----------------------
# Un paramètre de gameplay sans invariant est un réglage qui peut devenir absurde en silence.
for f in $(git ls-files 'resources/data/*.gd'); do
  grep -q '^func validate()' "$f" || bad "Resource sans \`validate()\` : $f"
done

# --- 5. Les pointeurs de la doc désignent du code VIVANT ---------------------
# ⚠️ VOLONTAIREMENT ÉTROIT, DEUX FOIS. Un lint qui crie faux se fait désarmer.
#
# a) La PORTÉE. Seules les sources qui décrivent l'état COURANT sont inspectées : la KB, le
#    ghost, `CLAUDE.md` et les ADR. Sont exclus `docs/design/`, `docs/plans/`, `docs/forge/`,
#    `docs/architecture/`, `docs/archive/` et le backlog — un document de conception nomme
#    légitimement un fichier qu'on n'a pas encore écrit, ou qu'on n'écrira jamais. Mesuré :
#    cinq chemins de ce genre au premier passage, tous légitimes.
# b) La FORME. On ne vérifie que ce qui promet « c'est là » : un chemin de source cité entre
#    backticks, et la forme `fichier.gd` (`_symbole`) des tableaux d'outillage — celle qui a
#    menti le 2026-08-28, `MOTEUR.md` pointant encore `graybox_root.gd` (`_trace_dive`) après
#    que la fonction eut déménagé. Un nom cité en prose n'est jamais inspecté.
#    ⚠️ CONSÉQUENCE ASSUMÉE, ET ELLE S'EST VÉRIFIÉE SUR SA PROPRE DOC : dans la KB et le
#    ghost, on ne RACONTE pas un déménagement avec la forme d'un pointeur — le lint attrape le
#    récit, et il a raison. Dans `docs/KB/`, tout ce qui a la forme d'une adresse doit être une
#    adresse valide. Nommer le symbole seul, sans lui accoler son fichier entre parenthèses.
#    (Attrapé deux fois à la première exécution : l'entrée d'historique du jour, puis l'exemple
#    de cette règle-ci dans `MOTEUR.md`.)
DOCS=$(git ls-files 'docs/KB/*.md' 'docs/decisions/*.md' '.claude/*.md' 'CLAUDE.md')

DEAD_PATHS=$(grep -ohE '`(res://)?(scripts|resources|tools|tests)/[A-Za-z0-9_/.-]+\.gd`' $DOCS \
  | tr -d '`' | sed 's|^res://||' | sort -u \
  | while read -r path; do [[ -f "$path" ]] || echo "$path"; done)
if [[ -n "$DEAD_PATHS" ]]; then
  bad "chemin de source cité dans la KB/le ghost et introuvable :"
  printf '  %s\n' $DEAD_PATHS >&2
fi

DEAD_SYMBOLS=$(grep -ohE '`[A-Za-z0-9_]+\.gd` \(`[A-Za-z0-9_]+`\)' $DOCS | sort -u \
  | while read -r pair; do
      file=$(echo "$pair" | sed -E 's/^`([^`]+)`.*/\1/')
      sym=$(echo "$pair" | sed -E 's/.*\(`([^`]+)`\)$/\1/')
      target=$(find scripts resources tools tests -name "$file" -print -quit 2>/dev/null)
      if [[ -z "$target" ]]; then
        echo "$file introuvable, cité avec \`$sym\`"
      elif ! grep -qE "(func|var|const|signal|class_name) +$sym\b" "$target"; then
        echo "$target ne déclare plus \`$sym\`"
      fi
    done)
if [[ -n "$DEAD_SYMBOLS" ]]; then
  bad "la doc pointe un symbole qui n'existe plus :"
  printf '%s\n' "$DEAD_SYMBOLS" | sed 's/^/  /' >&2
fi

if [[ "$FAILURES" -gt 0 ]]; then
  say "$FAILURES règle(s) dure(s) violée(s) — voir CLAUDE.md § Règles de code"
  exit 1
fi
say "règles dures OK"
