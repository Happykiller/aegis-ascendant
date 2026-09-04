# Specter-9 Talvern — la cellule-témoin : la troisième coque, la plus belle

| | |
|---|---|
| **Date** | **2026-09-04** |
| **Auteur** | session Claude (Fable 5.1), sur la demande orale de l'opérateur |
| **Périmètre** | une **troisième carrosserie jouable** du Specter-9 : la plus détaillée des trois, riche en géométrie, **micro-animée** (ailes, volets, pétales de tuyère, aérofreins, rampes d'entrée d'air, gouvernes, grappins, verrière), avec son jeu de textures dédié généré par l'opérateur |
| **État** | ✅ **LOT 0 clos** (2026-09-04) — `ADR-0044`, `BRIEF-0098`, `TEX-0017` à `0019` écrits. **LOT 1 lancé** : la forge construit |
| **Décision** | [`ADR-0044`](../decisions/ADR-0044-la-cellule-temoin-troisieme-coque-sans-plafond.md) |
| **Supersède** | rien. Les deux coques existantes restent en service et ne bougent pas |
| **Source** | l'opérateur, 2026-09-04 : « *le plus beau que tu puisses réaliser, sans aucune restriction […] beaucoup de détails, beaucoup de polygones […] micro-animer, les ailes qui se rétractent, les volets qui bougent, les tuyères qui s'ouvrent et qui se ferment* » ; planches `assets/reference/inspiration/specter_9_multi_angle_turnaround.png` et `reference_specter_9_design_sheet.png` |

# ▶ POINT DE REPRISE — 2026-09-04

## En une phrase

**La décision est actée et la forge est lancée.** Rien n'est encore rendu ni regardé : le premier
`.glb` n'existe pas. Aucun code n'a bougé.

## Ce qui reste à faire, dans l'ordre

1. **LOT 1** — relire le rapport de forge **sur les planches, pas sur le texte** ; un brief
   correctif s'il faut (`BRIEF-0099`).
2. **LOT 2** — le code : `ShipFlight` étendu, `HullDetailSet`, fiche du bestiaire, accueil et
   appontage.
3. **LOT 3** — les textures de l'opérateur, dérivées et câblées, **regardées en jeu**.
4. **LOT 4** — la mesure GPU qui décide (`ADR-0044` §2).
5. **LOT 5** — jouer.

---

## Ce que la coque doit être, en une phrase

> « Celle contre laquelle on mesure les autres. »

Une cellule-témoin de l'Arsenal : la même architecture que la coque en service — c'est la même
unité, `ADR-0014` s'applique — mais **exécutée sans compromis** : chaque cassure de panneau est un
vrai creux biseauté, chaque mécanisme est une pièce qui bouge sur sa charnière, la verrière laisse
voir un cockpit, et les tuyères sont douze pétales chacune.

## Ce qui borne l'ambition, et qu'il faut avoir en tête avant de juger un rendu

- **Le post-traitement rétro écrase le détail fin** (960×540, postérisation à 20 niveaux). Un
  détail qui module moins de ~6 niveaux de gris n'existe pas. Le détail se met dans la
  **géométrie** — des creux assez profonds et des biseaux assez larges pour ombrer — jamais dans
  une finesse de texture.
- **En combat le vaisseau fait ~48 px.** Ce qui compte à cette taille : la silhouette, la flèche
  des ailes, les tuyères qui s'ouvrent. Le reste est pour l'accueil et le bestiaire.
- **La caméra de jeu est à 20° de la verticale**, légèrement en arrière : on voit le dos et les
  tuyères. Le ventre n'existe que dans le bestiaire — il vient **après**.
- **Le contrat gameplay ne bouge pas** : 1,75 × 2,46 m, hitbox depuis les Resources.

---

## LOT 0 — Les décisions — ✅ **CLOS (2026-09-04)**

| Livré | Chemin |
|---|---|
| L'ADR : troisième coque, plafond remplacé par une mesure, contrat des pièces mobiles étendu, jeu de textures dédié | `docs/decisions/ADR-0044-…md` |
| Le brief de forge | `docs/forge/briefs/BRIEF-0098-specter-9-talvern-cellule-temoin.md` |
| Trois demandes de texture pour l'opérateur | `docs/forge/textures/TEX-0017-specter-borde-composite.json`, `TEX-0018-specter-mecanique-de-baie.json`, `TEX-0019-specter-metal-de-tuyere.json` |

**Trois choix tranchés ici, et pourquoi :**

- **Un garde-fou à 400 000 triangles, pas un plafond.** « Sans restriction » ne peut pas vouloir
  dire « sans garde » : `export_hull()` doit continuer de refuser un accident de script. Ce qui
  décide, c'est la mesure GPU (LOT 4).
- **Les pétales sont des nœuds, pas une échelle.** L'ouverture par `scale` de `ShipFlight` était un
  ersatz honnête pour six pièces mobiles ; pour « des tuyères qui s'ouvrent et se ferment », il
  faut des pétales qui pivotent. Douze par tuyère, enfants de `Nozzle_*`. `ShipFlight` dérive l'axe
  de charnière de chaque pétale de sa position radiale — d'où une contrainte de brief : le pivot de
  la tuyère est **sur son axe, dans le plan des charnières**.
- **Le jeu de textures se pose par NŒUD, pas par matériau.** Les sept matériaux `AA_*` sont
  imposés et `export_hull()` refuse tout autre nom. Une matière de tuyère distincte de la coque
  n'est donc possible que parce que les tuyères sont des **nœuds séparés** — `HullDetail` saura
  poser un jeu sur `Nozzle_*`/`Petal_*` et un autre sur le reste.

## LOT 1 — La coque, par la forge — ⏳ **EN COURS**

`BRIEF-0098`. Ce que je relirai, et dans cet ordre :

1. **La planche quatre vues à côté de la planche de référence, à la même hauteur** (`ADR-0014`
   §méthode) — pas la bbox, la répartition des masses.
2. **La planche des mécanismes** : chaque famille à ses deux extrêmes. Une pose fixe ne prouve
   rien (`pratique-detail-en-fraction-de-corde`).
3. **La table des dégagements** : tous au-dessus des cibles du brief, sinon le build a échoué et le
   rapport le dit.
4. **La répartition des matériaux mesurée** : émissif ≤ 3 %, or ≤ 4 %, rouge ≤ 1 %. Au-delà c'est
   une livrée, et la livrée est exclue.
5. `TEXCOORD_0` **compté**, déterminisme `--check` vert.

Puis mon propre rendu (`render-hull.py`) et une capture **en jeu** (bestiaire, accueil), post-process
actif — le studio flatte.

## LOT 2 — Le code — ✅ **LIVRÉ pour ce qui ne dépend pas du `.glb`** (2026-09-04, `5f0c474`, `2bdd5c7`)

Ce qui est fait, testé (882 tests, 0 échec) et committé — **avant** que la coque existe, parce
que rien ici n'en dépend :

- `ShipFlight` : `set_brake`, `set_docking`, sept familles optionnelles, lacet de tuyère ; **l'axe
  d'un pétale est dérivé de sa position radiale** dans le repère de sa tuyère, et le test vérifie
  que la POINTE s'écarte de l'axe plutôt que de faire confiance au signe. Les plafonds du test sont
  les **cibles du brief** — ⚠️ à recaler sur le rapport de forge.
- `HullDetailSet` + `hull_detail_default.tres` ; `HullDetail.apply(hull)` résout le jeu depuis le
  `scene_file_path` de la coque et pose la matière de tuyère **par nœud**. Registre `SETS` vide
  jusqu'au LOT 3.
- Le contrôleur pousse le freinage subi (`_shown_drag`) et l'approche d'appontage
  (`begin_docking`, distinct de `begin_autopilot` que la plongée du boss emploie aussi).
- Le héros de l'accueil monte la coque choisie au bestiaire (`_swap_hero_hull`).

Ce qui attend le `.glb` : la fiche `specter_9_c.tres` et son entrée au `ROSTER`, le recalage des
constantes de `ShipFlight` et de `test_ship_flight.gd` sur les plafonds mesurés, l'axe réel des
gouvernes (`FIN_CANT_DEG`), et une capture en jeu.

### Ce que le lot prévoyait

| Pièce | Ce qui change | Test |
|---|---|---|
| `scripts/fx/ship_flight.gd` | `set_brake(ratio)`, `set_docking(ratio)` ; familles optionnelles `Petal_*`, `Airbrake_*`, `Intake_*`, `Rudder_*`, `Grapple_*`, `Canopy` ; lacet de tuyère ; **les pétales remplacent l'échelle** quand ils existent | `test_ship_flight.gd` : chaque plafond mécanique du rapport devient une constante, et un test le garde ; les deux coques sans ces nœuds restent muettes sans erreur |
| `resources/data/hull_detail_set.gd` (+ `.tres`) | `HullDetailSet` typée, `validate()` — cartes mul/nrm/rough/ao, échelle, `normal_scale`, et un **jeu de tuyère** séparé | validation de la Resource |
| `scripts/fx/hull_detail.gd` | `apply(hull, set = DEFAULT)` ; pose le jeu de tuyère sur `Nozzle_*`/`Petal_*` par nom de nœud | comptage des surfaces retexturées sur un faux arbre |
| `resources/codex/specter_9_c.tres` + `codex_screen.gd` | la fiche ; `playable_hull` = le `.glb` (il est à l'échelle, pas de scène d'ajustement) | `test_codex_entries.gd` |
| `player_fighter_controller.gd` | pousse `set_brake` (depuis `drag_throttle`/freinage) et `set_docking` (phase `DOCKING`) | — |
| `title_stage.gd` / `boot.tscn` | le héros de l'accueil monte **la coque choisie** | capture |

⚠️ Le contrôleur cherche **sept** `Muzzle_*` et deux `Engine_*` par leur nom, et journalise neuf
erreurs s'ils manquent (`specter_9_b.tscn` le dit). Le brief impose les dix points d'attache
d'`ADR-0008` : le `.glb` se monte **nu**.

## LOT 3 — Les textures — à faire, par l'opérateur

Les trois JSON sont prêts. Ordre d'intérêt : **`TEX-0017`** (le bordé — c'est 80 % de la surface),
puis `TEX-0019` (les tuyères sont le point focal arrière), puis `TEX-0018` (intérieurs de baie,
visibles seulement mécanismes ouverts).

Pour chaque livraison : `derive-maps.py --check-tiling` d'abord, import avec mipmaps (**29 cartes
sur 50 en sont privées dans le dépôt**, c'est le défaut de Godot), puis **regarder en jeu**. Le
contrat le dit : la chaîne peut être juste à 1 % près et la carte invisible.

## LOT 4 — La mesure qui décide — à faire

`godot-verifier`, accueil et combat, trois tirs, avant/après, RTX 4080 **et** T1000 quand elle est
disponible. Critère `ADR-0044` §2 : accueil < 12 ms sur T1000. Vérifier que les LOD d'import
s'appliquent bien à des nœuds glTF séparés (48 pièces mobiles, c'est 48 maillages).

## LOT 5 — Jouer — à faire

Bestiaire (rotation, zoom, cockpit), accueil, une partie complète, l'appontage. Le skill `/jouer`
rend la chronologie.

---

## Ce qui n'est PAS dans ce chantier

- Toucher aux deux coques existantes, ou à leurs stats.
- Un atlas peint par vaisseau — hors pipeline (`ADR-0013` §limites).
- Le train d'atterrissage : la planche apponte par **grappins et rail dorsal**, pas sur roues.
- Une livrée, un numéro, un insigne (`ADR-0014`).
