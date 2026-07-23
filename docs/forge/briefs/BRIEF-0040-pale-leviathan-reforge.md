# BRIEF-0040 — Pale Leviathan : une coque animable, texturable, et à sa vraie taille

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-07-23

## Objectif

Reforger `tools/blender/build_pale_leviathan.py` pour que la coque du boss final soit **animable
depuis Godot**, **texturable**, et conforme à ses nouvelles dimensions. Sans cette reforge, aucune
des quatre phases du combat n'est réalisable et les onze images déjà livrées ne servent à rien.

## Contexte

`docs/design/BOSS_PALE_LEVIATHAN.md` décrit le combat en quatre phases ; `ADR-0018` l'acte et
amende les dimensions. La coque actuelle bloque les deux, pour deux raisons **techniques, pas
esthétiques**.

### Défaut 1 — rien n'est animable

Le script livre bien `Core`, `Shell_Crescent` et `Spike_01..04` comme objets séparés. Mais il ne
contient **aucun appel à `ak.moving_part()`** — 0 occurrence, contre 10 dans
`build_choir_harvester.py`. Son propre en-tête explique pourquoi sans en tirer la conséquence :

> « Toutes les pieces sont donc laissees a la transformation identite, geometrie exprimee dans le
> repere global »

Une pièce dont l'origine est celle du modèle tourne **autour du centre du boss**, pas autour de sa
charnière. C'est mot pour mot le défaut que **BRIEF-0039** a corrigé sur le mini-boss, et la
primitive qui manque existe déjà :

```python
ak.moving_part(name, bm, pivot, parent=None)   # aegis_kit.py:728
```

Elle pose l'origine de l'objet **sur son pivot** et accepte un `parent` — donc des **chaînes
articulées**. C'est ce qui fait bouger les ailes du Specter-9 et les trois appendices du Harvester.

### Défaut 2 — rien n'est texturable

`ak.box_project_uv()` n'est appelé que par `build_specter_9.py`, `build_aegis_citadel.py`,
`build_citadel_turret.py` et `build_citadel_beacon.py`. **Aucun script de boss ne le fait.** Sans UV
ni tangentes, une texture n'a nulle part où s'appliquer — c'est le symptôme exact qu'ADR-0013 relève
pour la citadelle avant sa reforge.

Or **le jeu de textures est déjà livré et validé** (commit `a23922b`) :
`assets/source/textures/leviathan/` contient les écailles, les greebles, les craquelures, les dégâts,
l'albédo du noyau et la paroi du puits. Ils attendent des UV.

### Ce que disent les planches

Trois planches annotées ont été livrées et validées. **Les lire avec `Read` avant de commencer** —
elles portent le contrat de noms, pas seulement l'intention :

| Planche | Ce qu'elle donne |
|---|---|
| `assets/reference/concepts/pale_leviathan_parts_sheet.png` | **la référence de ce brief** : 4 vues orthographiques cotées + éclaté des pièces, chacune nommée |
| `assets/reference/concepts/pale_leviathan_core_states_sheet.png` | noyau fermé / vortex / puits à anneaux, et les détails plaque, nœud, épine |
| `assets/reference/concepts/pale_leviathan_phases_sheet.png` | les 4 états de destruction — c'est la cible d'ensemble |

⚠️ **Deux erreurs de légende connues** sur la planche des pièces, à ne pas recopier : le 3ᵉ segment
d'épine y est noté `SPIKE MID` alors que c'est **`Tip`** ; et les quatre vues sont toutes cotées
« 14.0 m » alors que la vue de face montre les **11 m** de largeur.

## Contraintes

- **IP** — interdits habituels de `CLAUDE.md`. Design original, s'en tenir aux planches.
- **Palette** — charte §3, Null Choir : anthracite `#24252B`, violet `#452663`, ivoire `#DDDCD2`,
  magenta `#D93D9C`. Les sept matériaux normalisés du kit (`ak.MATERIAL_ORDER`).
- **Contrat de dimensions — nouveau, acté par ADR-0018** :
  **11,0 m (X) × 14,0 m (Z)**, tolérance ±3 %, hauteur Y ≤ **3,20 m**.
  `tri_budget` porté à **40 000** (très en deçà du plafond de 90 000 d'ADR-0011 ; le relever dans le
  `HullContract` du script fait partie du livrable).
- **Déterminisme** — tout aléa passe par `random.Random(seed)`, jamais le module global. Deux
  exécutions byte-identiques. Régénérer par `./scripts/build-hull.sh pale_leviathan`, **jamais** par
  un `blender45` nu : le `-t 1` est ce qui rend le `.glb` reproductible.
- **Repère d'auteur** — nez/face menaçante vers −Y, dessus +Z, babord +X. Pivot à l'origine, centré
  sur le noyau.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/build_pale_leviathan.py` | le script reforgé — il **est** la source de l'asset (ADR-0008) |
| `assets/imported/models/bosses/pale_leviathan.glb` | régénéré via `./scripts/build-hull.sh pale_leviathan` |
| `docs/forge/output/BRIEF-0040-report.md` | compte-rendu, **avec le tableau de dégagement** (voir Critères) |

### Contrat de noms — non négociable

Le code du combat sera écrit contre cette liste. Un nom qui diverge casse l'intégration en silence.

| Nœud | Nature | Parent | Pivot (repère d'auteur) |
|---|---|---|---|
| `Body` | maillage porteur (`hull`) | — | porte à lui seul l'étendue longitudinale |
| `Shell_Ring` | `moving_part`, racine | — | **axe du noyau** — porte l'orbite, et rien d'autre |
| `Shell_Crescent` | `moving_part` | `Shell_Ring` | charnière arrière |
| `Plate_01`..`Plate_04` | `moving_part` | `Shell_Crescent` | leur charnière radiale |
| `Core` | `moving_part`, racine | — | centre du noyau |
| `Maw_Lip` | `moving_part` | `Core` | lèvre de la gueule (légendée `OUTER RIM` sur la planche) |
| `Node_01`..`Node_03` | `moving_part` | `Maw_Lip` | leur embase articulée |
| `Ring_01`..`Ring_05` | `moving_part` | `Core` | axe du tunnel, échelonnés en profondeur |
| `Heart` | statique | `Core` | — |
| `Spike_01`..`Spike_04` | `moving_part`, racine | — | épaule — **détachables au runtime** |
| `Spike_0X_Mid` | `moving_part` | `Spike_0X` | coude |
| `Spike_0X_Tip` | `moving_part` | `Spike_0X_Mid` | pointe |

⚠️ **Trois niveaux pour la coquille, et c'est délibéré.** `Shell_Ring` porte l'orbite,
`Shell_Crescent` la bascule, `Plate_0X` la chute. Empiler deux de ces mouvements sur le même nœud
(`rotation.y` pour l'un, `rotation.x` pour l'autre) marche jusqu'au jour où les deux sont actifs
ensemble — et ce jour-là, la composition d'Euler produit une pose fausse que personne ne sait
relire. **Un axe, un nœud, un écrivain.**

**Points d'attache à exposer** : `Core_Center`, `Maw_Center`, `Tunnel_End`, `Muzzle_C`, `Muzzle_L`,
`Muzzle_R`, `Muzzle_Plate_01..04`, `Muzzle_Spike_01..04`.

Les trois `Muzzle_C/L/R` actuels sont **conservés** (le contrôleur générique les lit encore si
`external_attacks` retombe à faux) ; les autres s'y ajoutent. Le `HullContract` du script est à
mettre à jour dans le même geste, sinon l'auto-validation refuse l'export.

### Les UV — la moitié oubliée du livrable

Appeler **`ak.box_project_uv(obj, TEXELS_PER_METER)` sur chaque maillage**, dans le même geste que
les `moving_part`.

**`TEXELS_PER_METER = 0.18`**, soit une tuile pour 5,5 m. Repères mesurés ailleurs : la citadelle
est à 0,12 (une tuile pour 8,33 m) et le Specter-9 à 4,0 (une tuile pour 25 cm). Sur une coque de
14 m, 0,18 donne des écailles d'environ 1,1 m — l'échelle des planches, et celle à laquelle la
texture d'écailles a été générée (période mesurée : 0,99 m).

## Débattements exigés par le gameplay

Ce sont les angles que le code appliquera. Le modèle doit les encaisser **avec de la marge**.

| Pièce | Mouvement | Amplitude |
|---|---|---|
| `Shell_Ring` | orbite des plaques | **360° continu** autour de l'axe du noyau |
| `Shell_Crescent` | bascule de fin de phase 1 | **0° → 65°** |
| `Plate_01..04` | chute après destruction | **0° → −80°** |
| `Core` | rotation lente d'ambiance | **360° continu** |
| `Maw_Lip` | ouverture de la gueule | **0° → 90°** |
| `Node_01..03` | rétraction à la destruction | **0° → −60°** |
| `Ring_01..05` | rotation de l'ouverture (`OFFSET GATE`) | **360° continu**, vitesses distinctes |
| `Spike_01..04` | pointage avant détachement | **±40°** |
| `Spike_0X_Mid` / `_Tip` | flexion | **±25°** chacun |

### ⚠️ Le dégagement — la leçon la plus chère du projet

Le Specter-9 a coûté **quatre briefs** (0033 → 0036) sur ce seul point. Le pire cas : un marquage
posé à cheval sur une charnière a fait tomber le dégagement d'un volet de 18,5° à **2,8°**, sous la
valeur utilisée par le jeu — donc un volet qui traversait la coque. **Le contrat a validé sans un
mot**, parce que la boîte englobante au repos était parfaite : un défaut d'animation ne se voit pas
sur une pose fixe.

Chaque pièce mobile doit donc être **mesurée à fond de course**, et le résultat **rapporté**. Une
marge nulle ou négative est un défaut bloquant, pas une remarque.

Corollaire hérité : poser le détail **en fraction de corde, jamais en coordonnée absolue**
(`.claude/resources/pratique-detail-en-fraction-de-corde.md`). Deux reforges de plan, deux fois le
même dégât.

## Provenance

Mettre à jour la ligne existante du `.glb` dans `assets/licenses/ASSET_PROVENANCE.csv`
(`prompt_file` → `docs/forge/briefs/BRIEF-0040-pale-leviathan-reforge.md`, note mentionnant les
nouvelles dimensions et l'ajout des pièces mobiles et des UV).

## Critères d'acceptation

- [ ] Toutes les pièces du contrat de noms existent, avec les **bons parents**.
- [ ] `ak.box_project_uv()` est appelé sur chaque maillage ; le `.glb` porte des UV **et** des
      tangentes.
- [ ] `./scripts/build-hull.sh --check pale_leviathan` : **0 octet divergent** (déterminisme).
- [ ] L'auto-validation d'`ak.export_hull()` passe : bbox 11,0 × 14,0 (±3 %), Y ≤ 3,20, ≤ 40 000
      triangles, matériaux, pivot, points d'attache.
- [ ] Le compte-rendu porte un tableau **« pièce / débattement appliqué / marge minimale mesurée »**
      couvrant les neuf lignes ci-dessus. Une marge nulle ou négative est un échec.
- [ ] **Vérifié par rendu, pas par calcul** : à `Maw_Lip` 90°, le tunnel et `Heart` sont entièrement
      dégagés **en vue de dessus** (l'angle de la caméra de jeu) ; à `Plate_0X` −80°, les quatre
      plaques tombées ne se mordent ni entre elles ni avec la coquille.
- [ ] Planche 4 vues produite (`blender45 -b -P tools/blender/render-hull.py -- <glb>`) et
      **regardée** avant de rendre (ADR-0006), plus un rendu **gueule ouverte**.
- [ ] Chiffres réels (dimensions, triangles) dans le compte-rendu — pas « conforme ».

## Hors périmètre

- **Ne pas** toucher au code GDScript, aux scènes `.tscn` ni aux Resources : le module de combat
  sera écrit en parallèle, et deux écrivains sur les mêmes fichiers produisent des commits mélangés
  (`.claude/resources/pratique-ecrivain-unique.md`).
- **Ne pas** intégrer les textures ni écrire `scripts/fx/leviathan_detail.gd` : ce brief pose les
  **UV**, l'application viendra ensuite, côté session principale.
- **Ne pas** modéliser l'état endommagé (fissures, suie) : il viendra par shader, avec le masque
  `leviathan_damage_mask` déjà livré.
- **Ne pas** produire de SFX ni de nouvelle image : tout est livré.
