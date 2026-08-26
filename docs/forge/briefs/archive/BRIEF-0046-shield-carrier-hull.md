# BRIEF-0046 — Coque 3D du Shield Carrier

- **Statut** : livré
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-08-23

## Objectif

Modéliser le **Shield Carrier**, sixième silhouette d'ennemi du Chœur Nul, en `.glb` PBR — avec un
**projecteur dorsal** proéminent et **trois bras de berceau articulés** qui le tiennent.

## Contexte

C'est l'unité qui **ne menace pas le joueur** : elle ne tire pas, elle ne poursuit pas, elle ne
touche jamais. Elle rend **invulnérables les autres ennemis** de sa bulle. Tant qu'elle vit, la vague
est un mur — et le joueur doit comprendre **en une seconde** que c'est elle qu'il faut abattre
d'abord, pas ce qu'il a devant le canon.

Toute la coque sert donc à répondre à une seule question, sans texte et sans tutoriel : *pourquoi
mes tirs ne font-ils rien ?* Elle doit se lire comme **une source**, pas comme un combattant.

⚠️ **LA BULLE N'EST PAS DANS TON PÉRIMÈTRE.** Le dôme de protection est généré **par le code**, à
partir du rayon d'aura de la Resource : il doit montrer la portée RÉELLE, qui est une valeur de
gameplay et non une dimension de maillage. Si tu le sculptais, il mentirait au premier réglage. Ce
que tu livres, c'est **l'émetteur** : le projecteur et son berceau.

Trois contrastes doivent être lisibles d'un coup d'œil :

- **contre les mines** (`choir_mine`, `null_maw`) : celles-là attendent, posées. Celle-ci **vole**.
- **contre la sangsue** (`leech_drone`) : la sangsue est minuscule et se termine par des pinces —
  une main. Celle-ci est **la plus grosse coque légère du bestiaire** et se termine par un dôme.
- **contre les chasseurs** : ni dard ni croissant. Pas de nez. **Rien qui ressemble à une arme.**

**Lire d'abord** : `docs/decisions/ADR-0008-pipeline-3d-blender.md`,
`docs/decisions/ADR-0011-detail-des-coques-budgets-et-textures.md`,
`docs/forge/CHARTE_CREATIVE.md`, puis `tools/blender/lib/aegis_kit.py` — **kit réutilisé sans
modification**. Modèle : `tools/blender/build_leech_drone.py`, le plus récent et le mieux instrumenté
(harnais de débattement, garde d'enveloppe, vérification des UV à l'export).

Référence de design : **`assets/reference/concepts/null_choir_enemy_families_sheet.png`**,
**septième et dernière cellule** (Shield Carrier). Regarde-la avec Read. Traits à respecter : **deux
coques en amande** enserrant un **gros projecteur central**, masse générale la plus lourde de la
planche.

## Contraintes

- **IP** : design original, aucun élément identifiable d'une licence existante.
- **Palette** : antagoniste **Chœur Nul** (charte §3). Matériaux du kit, `MATERIAL_ORDER` inchangé.
- **Techniques** :
  - Dimensions monde : **2,20 m (X) × 1,80 m (Z)**, ±3 %. Hauteur ≤ 0,70 m.
    Presque le double de la Choir Mine (1,15) et deux fois et demie la sangsue (0,70) : **la masse
    est l'information**, et elle doit se lire avant le détail.
  - Orientation d'auteur : **nez vers -Y, dessus vers +Z**.
  - Pivot à l'origine, centré.
  - Budget : **≤ 8 000 triangles**. Elle n'arrive pas en essaim — une ou deux par vague.
  - **Bâbord = `+X`** ; `attach_pair()` pour toute paire.
  - Déterministe, headless, Blender 4.5 LTS.
  - ⚠️ **UV OBLIGATOIRES** (`ak.box_project_uv()`) et **n-gons triangulés** avant export. Trois
    coques du dépôt sont sorties sans UV et ne peuvent recevoir aucune carte de détail ; le défaut
    est totalement silencieux. **Compte `TEXCOORD_0` dans le `.glb` produit**, ne suppose pas.
    (Les tangentes, elles, sont régénérées par l'import Godot — ce ne sont pas elles le sujet.)

### Pièces articulées

| Nœud | Ce que c'est | Pivot |
|---|---|---|
| `Cradle_01` … `Cradle_03` | trois bras de berceau tenant le projecteur | à leur **base**, sur la coque : ils s'écartent vers l'extérieur en découvrant le projecteur |

Ces bras **respirent** en jeu : cette unité n'a pas de télégraphe — elle ne déclenche rien, elle
protège en permanence — donc sa pose suit une oscillation lente et non un cycle d'attaque. C'est ce
qui la fera lire comme **une machine en fonctionnement** plutôt que comme une épave qui plane.

Le jeu les pilote par `EnemyPose` : pivot autour d'un axe horizontal **tangent au rayon de la pièce**
(`axe = normalize(-pos.z, 0, pos.x)`, origine = point d'articulation), plus un coulissement radial
optionnel le long de `normalize(pos.x, 0, pos.z)`.

⚠️ **LA LEÇON DE BRIEF-0042, DÉJÀ PAYÉE DEUX FOIS.** Sur la Choir Mine, six plaques pivotaient
parfaitement et l'ouverture était **invisible en jeu** : l'enveloppe appartenait à la couronne de
modules et non aux plaques, que le pivot faisait même *rentrer*. Une pièce animée pour changer une
silhouette doit **porter** cette silhouette. Le script du Leech Drone refuse d'exporter si la coque
fixe atteint le rayon des pinces — **fais la même chose ici**, avec les bras.

Donne au compte-rendu, comme pour les deux précédentes : le **débattement mécanique** de chaque bras
(première interpénétration, dernière valeur sûre), et la **croissance du diamètre apparent** entre
repos et ouverture, mesurée **à la perspective réelle du jeu** (caméra de `graybox.tscn`, 14,87 u,
70° sous l'horizontale) et non au cadrage serré de `render-hull.py`, qui surestime d'un facteur 7.

**Seuil posé d'avance : sous 10 % de croissance de diamètre, dis-le** — l'oscillation restera un
signe de vie et non une lecture d'état, et je ne prétendrai pas le contraire. Ne réajuste pas le
critère au résultat.

### Où mettre le détail, et l'émissif

Caméra quasi **de dessus** (70°). Détail et émissif sur les surfaces **supérieures**, en
**géométrie** jamais en texture fine.

⚠️ **EXCEPTION ASSUMÉE SUR L'ÉMISSIF, ET UNE SEULE.** La règle du dépôt est « au-delà de ~10 % de
l'aire vue, ce n'est plus un accent mais une livrée ». Ici le projecteur **est** la fonction de
l'unité et doit dominer : vise **12 à 15 %**, concentrés **sur le seul projecteur**, le reste de la
coque restant sous 3 %. Donne la répartition mesurée pour que l'écart soit constaté et pas supposé.

Et un point que le codex m'a appris à demander : la répartition doit être donnée **sur l'aire vue
par la caméra de jeu ET sur l'aire totale**. Le bestiaire présente les coques de trois quarts et
montre des flancs que le jeu ne montre jamais — une aire de marquage n'a de sens qu'avec la vue
depuis laquelle on la mesure.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/build_shield_carrier.py` | script de construction, rejouable |
| `assets/imported/models/ships/shield_carrier.glb` | le mesh exporté (LFS) |
| `docs/forge/output/BRIEF-0046-report.md` | compte-rendu : mesures réelles, débattements, limites |

## Points d'attache requis

- `Muzzle_C` — sur l'axe, à l'avant. Elle ne tire **jamais**, mais `EnemyController` lit ce point à
  l'initialisation de toute coque : il doit exister.
- `Engine_C` — **obligatoire** : elle vole sous puissance et le jeu lui accroche une plume.

## Provenance

Une ligne dans `assets/licenses/ASSET_PROVENANCE.csv`, **en append shell (`>>`)**, jamais par
réécriture. `asset_type=model3d`, `source_tool=asset-forge (Blender 4.5.11, script)`,
`license=proprietary-internal`, `prompt_file=docs/forge/briefs/BRIEF-0046-shield-carrier-hull.md`.

## Critères d'acceptation

- [ ] `blender45 -b -P tools/blender/build_shield_carrier.py` régénère le `.glb` sans erreur
- [ ] Bounding box 2,20 × 1,80 m (±3 %), hauteur ≤ 0,70 m — chiffres réels au rapport
- [ ] ≤ 8 000 triangles
- [ ] `./scripts/build-hull.sh --check shield_carrier` : deux exécutions, `.glb` byte-identique
- [ ] **`TEXCOORD_0` sur 100 % des primitives**, vérifié dans le `.glb` produit
- [ ] `Muzzle_C` et `Engine_C` correctement placés
- [ ] Trois `Cradle_NN` en pièces mobiles, **débattement mesuré**, et **les bras portent la
      silhouette** dans les deux poses (garde à l'export, comme le Leech Drone)
- [ ] **Croissance du diamètre apparent mesurée** à la perspective du jeu, verdict à 46 px
- [ ] Répartition des matériaux donnée **sur l'aire vue ET sur l'aire totale**
- [ ] **Rendu et regardé** (ADR-0006) : planche 4 vues + planche bras écartés
- [ ] Elle se distingue des cinq autres coques d'ennemis sur l'aplat noir vu de dessus — et **elle ne
      ressemble à rien qui puisse tirer**
- [ ] Kit réutilisé **sans modification**
- [ ] Provenance renseignée

## Hors périmètre

Pas de `.tscn`, `.tres`, code, tests. **Pas de dôme de protection** : il est généré par le code
depuis le rayon d'aura. Pas de textures peintes, pas de LOD, pas de `.blend` versionné.
