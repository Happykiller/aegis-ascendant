# BRIEF-0027 — Points d'emport de tir du Specter-9 (hardpoints par niveau de power)

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-07-19

## Objectif

Compléter les points d'attache du Specter-9 pour que **chaque flux de tir du joueur parte d'un canon
physique du mesh**, à tous les niveaux de power. Aujourd'hui la coque n'expose qu'un twin de nez très
resserré (`Muzzle_L`/`Muzzle_R`, écartement `BARREL_X=0.026`) ; le code reconstruit les tirs d'aile et
de bout d'aile avec des offsets latéraux **codés en dur**, sans emplacement réel. On veut un jeu de
hardpoints qui **mappe 1:1 l'échelle de puissance** (spec §9.1), positions **dérivées de la
géométrie** (jamais devinées, cf. l'entête de `build_attach_points()`).

## Contexte

- Fichier source : `tools/blender/build_specter_9.py` (le script EST l'asset, ADR-0008). Kit :
  `tools/blender/lib/aegis_kit.py` (`ak.attach_pair()`, `ak.attach_point()`).
- Repère d'auteur : **nez -Y, dessus +Z, babord +X** ; `ak.attach_pair(base, x, y, z)` pose `_L`
  (babord) / `_R` (tribord) avec le bon signe, `x` = distance **positive** à l'axe.
- Référence de design : `assets/source/concepts/specter_9_concept_sheet.png` (canon ventral + aile
  delta double flèche) et la cible de rendu `assets/source/references/reference_fortress_battle_scene.png` où le
  chasseur crache **plusieurs flux parallèles** depuis le nez, les ailes et les bouts d'aile.
- Le pattern de tir (`scripts/player/player_fighter_controller.gd::_fire_pattern`) sera recâblé
  **par le concepteur** pour lire ces points ; ta mission s'arrête au mesh + contrat.

## Contraintes

- **IP** : aucune (points d'attache = Empties invisibles + léger ajustement de deux tubes existants).
  Création originale, dérivée de la géométrie de la coque.
- **Géométrie** : le mesh doit rester dans le contrat ADR-0008 inchangé (bbox `1.75 × ~0.41 × 2.46`,
  budget 15 000 tris, 7 matériaux, pivot centré). Le seul ajout de matière autorisé est
  l'**écartement des deux tubes de canon de nez** (voir ci-dessous) ; les autres hardpoints sont des
  Empties sans coût triangle.
- **Déterminisme** : build byte-identique entre deux exécutions (aucun aléa non seedé).
- **Auto-validation** : ajouter les nouveaux noms à `CONTRACT.required_attach_points` pour que
  `ak.export_hull()` échoue si un point manque après régénération.

## Travail demandé

### 1. Twin de nez lisible (`Muzzle_L` / `Muzzle_R`)

Les deux tubes ventraux à `BARREL_X=0.026` sont quasi coïncidents : deux tirs en sortent superposés
(illisibles comme « twin »). **Écarter les tubes** à un `BARREL_X ≈ 0.12` (valeur à ajuster pour rester
sous le longeron ventral `STRAKE` et cohérente avec la planche — le canon ventral y est un bloc à deux
bouches), en déplaçant la **géométrie des tubes** (`build_details`, boucle `add_lathe` des barrels) **et**
les muzzles ensemble, pour que flash, tube et balle restent alignés. `y = MUZZLE_Y`, `z = _barrel_z()`.

### 2. Hardpoints d'aile (`Muzzle_Wing_L` / `Muzzle_Wing_R`) — power 3

Sur le bord d'attaque, à mi-aile : `x ≈ ±0.50`. Dériver `y` de `PLANFORM` (station où la demi-envergure
vaut ~0.50, bord d'attaque avant) et `z` de la surface supérieure d'aile `z_top(x, …)` à cette station.
Emplacement d'un canon d'aile qui tire vers l'avant.

### 3. Canon d'axe central (`Muzzle_C`) — power 4

Bouche axiale : `x = 0`, dans l'axe du canon ventral (`y = MUZZLE_Y`, `z = _barrel_z()`) — le tir
« renforcé d'axe » part du centre du bloc-canon, entre les deux tubes.

### 4. Hardpoints de bout d'aile (`Muzzle_Tip_L` / `Muzzle_Tip_R`) — power 5

Aux bouts d'aile, légèrement en retrait du bord (`x ≈ ±0.80`, sous la largeur max 0.875 pour rester sur
la coque). Dériver `y` du coin avant du bout d'aile (`PLANFORM` ~`(0.418, 0.875)`) et `z` de la surface
d'aile (attention à l'anhédral). Emplacement des pods de bout d'aile de la salve latérale complète.

### 5. Contrat & régénération

- Étendre `CONTRACT.required_attach_points` : `Muzzle_L, Muzzle_R, Muzzle_Wing_L, Muzzle_Wing_R,
  Muzzle_C, Muzzle_Tip_L, Muzzle_Tip_R, Engine_L, Engine_R, Cockpit`.
- Régénérer : `blender45 -b -P tools/blender/build_specter_9.py`.
- Vérifier que `ak.export_hull()` passe (bbox/budget/matériaux/pivot/attach points OK) et relever les
  mesures réelles (tris, bbox, positions des 10 points).

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/build_specter_9.py` | tubes écartés + 5 nouveaux hardpoints + contrat étendu |
| `assets/imported/models/ships/specter_9.glb` | coque régénérée (LFS), + `.import`/`.uid` |
| `assets/licenses/ASSET_PROVENANCE.csv` | mettre à jour la ligne `specter_9_hull` (modified_by BRIEF-0027, nouvelles mesures : 10 points d'attache) |

## Provenance

Mettre à jour la ligne existante `specter_9_hull` : `modified_by = BRIEF-0027`, et dans les notes
remplacer « 5 points d'attache (Muzzle_L/R, Engine_L/R, Cockpit) » par la liste des **10** points, avec
les positions réelles relevées. Rester « création originale ».

## Critères d'acceptation

- [ ] `blender45 -b -P tools/blender/build_specter_9.py` régénère le `.glb` sans erreur de contrat.
- [ ] Le `.glb` expose exactement les 10 points d'attache nommés, aux positions dérivées de la géométrie.
- [ ] Les deux tubes de nez sont visiblement écartés (twin lisible) ; flash/tube/muzzle alignés.
- [ ] bbox et budget triangles toujours dans le contrat ADR-0008 ; build déterministe.
- [ ] Provenance à jour.
- [ ] Rapport de mission dans `docs/forge/output/BRIEF-0027-report.md` (positions des 10 points, mesures).

## Hors périmètre

- Ne pas toucher au code gameplay (`scripts/**`) ni aux `.tscn` : le recâblage du pattern de tir est
  fait par le concepteur.
- Ne pas modifier les autres coques (Needle Scout, boss, citadelle) : leurs muzzles existent déjà.
- Pas de changement de silhouette ni de matériaux au-delà de l'écartement des deux tubes de canon.
