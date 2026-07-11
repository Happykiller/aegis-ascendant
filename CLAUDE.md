# CLAUDE.md — Aegis Ascendant

Prototype de vertical shooter 2.5D/3D sous **Godot 4.7-stable** (Forward+, GDScript typé), export `.exe` Windows x64.

## Source de vérité

- **`docs/SPEC_AEGIS_ASCENDANT.md`** — cahier des charges complet (lire §0 : contrat d'exécution, avant tout travail).
- **`docs/decisions/ADR-*.md`** — décisions actées qui priment sur la spec en cas d'écart (ex. : Godot 4.7 au lieu de 4.6).
- Ne jamais inventer une API/option CLI Godot : vérifier dans la doc officielle **4.7** (https://docs.godotengine.org/en/4.7/).

## Environnement (voir ADR-0002)

- Dev dans **WSL2 Debian** ; **jamais de commande Godot sans `--headless`** dans WSL (pas de GPU fiable).
- Test visuel : export Windows → copie `/mnt/c/tmp/aegis-ascendant/` → lancement natif (RTX 4080).
- Dépôt git **local, imbriqué** dans `~/sandbox` : ne jamais l'ajouter depuis le dépôt parent.

## Commandes canoniques (voir ADR-0003)

```bash
./scripts/bootstrap.sh    # installe Godot 4.7 + export templates (idempotent, SHA512)
./scripts/check.sh        # porte de qualité : import headless + parse + tests — DOIT être vert
./scripts/export-win.sh [debug|release]   # export Windows (check d'abord)
./scripts/deploy-win.sh [-- args_jeu]     # copie vers C:\tmp\aegis-ascendant + lance sur Windows
godot4 --headless --path . --script res://tests/test_runner.gd   # tests seuls
```

## Règles de code (spec §31)

- GDScript **typé** partout ; composition > héritage ; signaux pour les événements.
- Paramètres de gameplay dans des **Resources typées** (`resources/data/*.gd`), jamais en dur ; chaque Resource expose `validate()`.
- **Zéro allocation dans les boucles critiques** (tableaux Packed préalloués, pooling obligatoire).
- Fichiers `snake_case.gd`, classes `PascalCase`, constantes `UPPER_SNAKE_CASE`.
- Les tests ne touchent pas les autoloads (absents en mode `--script`) : unités instanciables à la main.
- **Committer les `*.uid`** générés par Godot ; `.godot/` et `build/` sont gitignorés.

## Délégation créative (voir ADR-0004)

La session principale est le **concepteur** (architecture, code, intégration, review). Toute production
créative/lourde (assets, palettes, scripts Blender, lore, SFX…) est déléguée au sous-agent
**`asset-forge`** (`.claude/agents/asset-forge.md`) via un brief versionné :

1. Rédiger `docs/forge/briefs/BRIEF-NNNN-<slug>.md` (gabarit : `docs/forge/BRIEF_TEMPLATE.md`).
2. Invoquer `asset-forge` avec le brief ; il lit d'abord `docs/forge/CHARTE_CREATIVE.md`.
3. Review (conformité charte, IP, formats, provenance) puis intégration et commit.

Tout asset livré a sa ligne dans `assets/licenses/ASSET_PROVENANCE.csv` (spec §24.7).

## Interdictions clés (spec §0.2)

- Aucun nom/silhouette/élément identifiable de Macross, Robotech ou d'une autre licence.
- Aucun asset sans licence enregistrée ; aucun asset temporaire non signalé.
- Ne pas contourner un test, ne pas cacher une erreur d'import/export.
- Pas de multijoueur, monde ouvert, backend, dépendance native non justifiée par profilage.

## Definition of Done (spec §35, réduit)

Une tâche n'est **terminée** que si : `./scripts/check.sh` vert + comportement vérifié
(headless, et sur Windows si visuel) + doc/ADR à jour + commit conventionnel
(`feat:`, `fix:`, `test:`, `perf:`, `docs:`, `chore:` — impératif, petit, un objectif).
