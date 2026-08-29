# BRIEF-0089 — La coque du Long Cortège, en cinq tronçons

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-08-29

## Objectif

Produire **la coque du vaisseau que le joueur survole pendant tout le niveau 2** : un décor
défilant, découpé en **cinq tronçons juxtaposés**, portant les marqueurs auxquels le jeu
accrochera ses tourelles, ses ponts d'envol et les nœuds de l'épine dorsale.

## Contexte

Le Long Cortège (`docs/lore/NULL_CHOIR.md`) est un vaisseau de 6,8 km qui **emporte** des
structures entières greffées sur son bordé. Le joueur le survole de la proue vers l'arrière ;
il ne l'affronte pas et ne peut pas le détruire. Plan : `docs/plans/2026-08-29-niveau-2-execution.md`.

**Références visuelles, à ouvrir avant de commencer :**

| Fichier | Ce qu'il donne |
|---|---|
| `assets/reference/inspiration/reference_enemy_capital_worldship.png` | la silhouette d'ensemble, la segmentation, l'axe lumineux, la poupe massive |
| `assets/reference/concepts/cortege_phase1_prow_approach_mockup.png` | section 1 : proue effilée, premières tourelles, premières baies |
| `assets/reference/concepts/cortege_phase2_early_hull_mockup.png` | section 2 : baies hexagonales, épine à bulbes |
| `assets/reference/concepts/cortege_phase3_mid_hull_mockup.png` | section 3 : tourelles à canons doubles, plus massives |

⚠️ **Ce qu'on retient de ces planches** : la forme, la segmentation, l'axe central, la densité
croissante. ⚠️ **Ce qu'on écarte** : le vocabulaire de marine de guerre de la fiche
(« FLAGSHIP », « SINGULARITY LANCE »), et le HUD des maquettes (BOMBS, ENERGY) qui n'existe pas
dans le jeu.

## ⚠️ Le précédent à suivre : `build_moon_flyby.py`, PAS une coque de vaisseau

`ak.export_hull()` **ne peut pas** être appelé ici, et le script du survol de lune écrit
pourquoi (lignes 100-120) — c'est une incompatibilité de contrat, vérifiée dans le code du kit :

- il exporte **une** coque dont le nœud reste à l'origine, or **chaque tronçon porte une
  translation que le moteur relit** pour le placer ;
- son contrôle d'orientation n'est vrai que si le nœud de la coque est à l'origine ;
- il impose un pivot centré à 2 cm et une bbox largeur × longueur, « deux notions qui n'ont pas
  de sens » pour un décor de cette taille.

**Refaire export et validation localement, à l'identique sur le fond** : même correction d'axe,
même relecture du `.glb` **produit** (jamais de la scène en mémoire), même règle « au moindre
écart, on échoue ». Le kit fournit le reste sans modification : `box_project_uv()`, `cleanup()`,
`srgb_hex_to_linear()`, `ContractError`.

Pour la **découpe en sous-volumes nommés**, le précédent est `build_core_interior.py` : douze
nœuds racines juxtaposés, sommets en coordonnées absolues.

## Contraintes

- **IP** : rien d'identifiable d'une licence existante. La planche d'inspiration est une cible de
  *forme*, jamais un décalque.
- **Palette** : Null Choir / Unisson (charte §3) — anthracite `#24252B`, violet sombre `#452663`,
  ivoire froid `#DDDCD2`, magenta `#D93D9C` (émissif), vert maladif `#7C9E52` très limité.
  Les 7 matériaux `AA_*` sont requis et assignés.
- ⛔ **Cyan `#3FD9E8` et corail `#FF5A3D` interdits** : ils appartiennent aux tirs.

### Géométrie — le contrat

| Point | Exigence |
|---|---|
| Sortie | `assets/imported/models/backgrounds/long_cortege.glb` |
| Tronçons | **5 nœuds racines** `Section_01` … `Section_05`, **sans enfants maillés** |
| Placement | chaque tronçon porte **sa translation** ; ils s'enchaînent le long de l'axe de survol, bout à bout, **sans trou ni recouvrement visible** |
| Largeur | **28 unités** de bord à bord (le plan de jeu fait 28 : la coque emplit l'écran) |
| Longueur | **≈ 34 unités par tronçon**, à ajuster pour que la jonction soit invisible |
| ⚠️ Hauteur | **rien au-dessus de `Y = -3`** — c'est le plafond du plan de jeu. Harnais **bloquant**, comme `moon_flyby._audit()` |
| Budget | **≤ 90 000 triangles au total**, ≤ 18 000 par tronçon. Repère : `core_interior` fait 36 tri/m² d'emprise, le plus bas du dépôt pour un grand décor |

### Les marqueurs — c'est par eux que le jeu accroche son gameplay

Des **points d'attache** (`ak.attach_point`, des Empties), jamais des maillages : le jeu y
instancie ses propres scènes, comme `CitadelLife` le fait pour les tourelles de la Citadelle.

| Nom | Nombre | Où |
|---|---|---|
| `Turret_01` … `Turret_NN` | **12 à 18**, densité croissante de la section 1 à la 5 | sur les flancs et les superstructures, jamais sur l'axe |
| `Bay_01` … `Bay_NN` | **5 à 8** | les baies hexagonales des planches, plutôt vers l'extérieur |
| `Spine_01` … `Spine_05` | **exactement 5, un par tronçon** | **sur l'axe central**, aux bulbes de l'arête lumineuse |
| `Ambry` | **1** | sur `Section_05`, l'avant-poste humain greffé — voir plus bas |

⚠️ **Le build doit ÉCHOUER si un marqueur manque.** Un contrat de noms muet est ce qui a fait
qu'une coque a été livrée sans ses UV, sans qu'aucun test ne rougisse.

### Ambry — la seule chose de ce vaisseau qui ne lui appartient pas

Sur la section 5, un **avant-poste humain de quatre-vingts personnes**, *greffé* sur le bordé :
antenne, serre, modules d'habitation. Il doit **jurer** avec le reste — géométrie orthogonale,
matériaux `AA_Hull`/`AA_Trim` clairs contre l'anthracite, aucune émission magenta. Il est
**intact et re-plombé**, pas en ruine : c'est ce qui rend la découverte insoutenable.

## Texture (ADR-0028 — OBLIGATOIRE)

⛔ **Ne livre AUCUNE texture.** Géométrie et UV seulement.

Cette coque **dépendra** de demandes `TEX-00NN` que le concepteur écrira **après** la livraison —
c'est la géométrie qui donne l'échelle monde d'une tuile, jamais l'inverse. Sujets prévus : bordé
de coque, hauteur du bordé, panneaux d'usure, émissif d'épine, émissif de baie, bordé d'Ambry.

**Dépliage attendu :**

| Usage | Dépliage |
|---|---|
| Bordé des cinq tronçons | `ak.box_project_uv()`, **échelle à décider et à ANNONCER en tuiles/m** — repère : `aegis_citadel` 0,12, `pale_leviathan` 0,18, `core_interior` 0,55 |
| Ambry | même projection, échelle **plus fine** : c'est une structure humaine vue de plus près |

⚠️ **UV sur 100 % des primitives, `TEXCOORD_0` COMPTÉ dans le `.glb` produit** — compté, jamais
supposé, et le build **échoue** s'il en manque une.

## Livrables

| Fichier | Description |
|---|---|
| `tools/blender/build_long_cortege.py` | le script de forge, déterministe |
| `assets/imported/models/backgrounds/long_cortege.glb` | la coque en cinq tronçons |
| `docs/forge/output/BRIEF-0089-report.md` | le compte-rendu, avec les mesures |
| `docs/forge/output/BRIEF-0089-planche-sections.png` | une planche de recette : les cinq tronçons vus de dessus, à l'échelle |

## Provenance

Une ligne dans `assets/licenses/ASSET_PROVENANCE.csv` pour le `.glb`, avec son **sha256**.

## Critères d'acceptation

- [ ] Cinq nœuds racines `Section_01..05`, chacun avec sa translation, **sans enfants maillés**
- [ ] Les tronçons s'enchaînent **sans trou ni recouvrement** — mesuré, pas estimé
- [ ] **Aucun sommet au-dessus de `Y = -3`** — contrôlé sur le `.glb` produit
- [ ] Tous les marqueurs présents, aux noms exacts ; le build échoue s'il en manque un
- [ ] **`TEXCOORD_0` compté sur 100 % des primitives**
- [ ] Densité de texels **mesurée** et annoncée en tuiles/m, par pièce
- [ ] ≤ 90 000 triangles au total, ≤ 18 000 par tronçon — **comptés**
- [ ] Les 7 matériaux `AA_*` présents et assignés ; aucun cyan, aucun corail
- [ ] **Déterminisme vérifié** : `./scripts/build-hull.sh --check long_cortege`, 0 octet divergent
- [ ] La planche de recette est produite **et regardée** (ADR-0006)

## Hors périmètre

- **Aucune texture**, aucune carte, aucun matériau texturé.
- **Aucun fichier de jeu** : ni `scenes/`, ni `scripts/`, ni `resources/`, ni test.
- **Aucune tourelle, aucun pont, aucun nœud modélisé** : uniquement leurs **points d'attache**.
  Les pièces sont des scènes que le jeu instancie.
- Les sections **6 et 7** (poupe) : elles appartiennent au niveau 3.
