# BRIEF-0021 — Kit hard-surface + coque 3D du Specter-9 — compte-rendu

- **Agent** : asset-forge
- **Date** : 2026-07-12
- **Brief** : `docs/forge/briefs/BRIEF-0021-hull-kit-specter-9.md`
- **Normes** : `docs/decisions/ADR-0008-pipeline-3d-blender.md`, `docs/forge/CHARTE_CREATIVE.md`
- **Référence de design** : `assets/source/concepts/specter_9_concept_sheet.png`
- **Outil** : Blender 4.5.11 LTS, headless (`blender45 -b -P …`)

## 1. Livrables

| Fichier | Rôle |
|---|---|
| `tools/blender/lib/aegis_kit.py` | bibliothèque hard-surface partagée (v1.0.0) |
| `tools/blender/build_specter_9.py` | script de construction du chasseur, rejouable |
| `assets/imported/models/ships/specter_9.glb` | le mesh livré (LFS, 285 920 o) |
| `docs/forge/output/BRIEF-0021-report.md` | ce document |
| `assets/licenses/ASSET_PROVENANCE.csv` | +1 ligne (`specter_9_hull`) |

Commande unique : `blender45 -b -P tools/blender/build_specter_9.py`

## 2. Mesures réelles (relevées sur le `.glb` livré, pas sur la scène Blender)

| Critère | Contrat | Mesuré | Marge |
|---|---|---|---|
| Largeur (Godot X) | 1,75 m ±3 % | **1,7500 m** | 0,00 % |
| Longueur (Godot Z) | 2,46 m ±3 % | **2,4598 m** | −0,01 % |
| Hauteur (Godot Y) | ≤ 0,60 m | **0,4104 m** | 16,7 % de la longueur |
| Triangles | ≤ 15 000 | **9 836** | 34 % de marge |
| Sommets | — | 9 171 | — |
| Pivot (centre X/Z) | ±0,02 m | (−0,0000 ; +0,0001) | centré |
| Matériaux | les 7 | les 7, tous assignés | — |
| Points d'attache | 5 | 5 | — |
| Déterminisme | rejouable | **sha256 byte-identique** entre deux exécutions | — |

Répartition des triangles par matériau : `AA_Hull` 4 139 · `AA_Greeble` 3 107 ·
`AA_Trim` 1 102 · `AA_Emissive_Engine` 700 · `AA_Panel` 496 · `AA_Glass` 240 ·
`AA_Marking_Red` 52. Le `.glb` sort en **7 primitives** (une par matériau) : Godot
recevra 7 surfaces nommées.

Points d'attache livrés (repère Godot, nez vers −Z, +X à tribord) :

```
Muzzle_L  (-0.0260, -0.0425, -1.0700)     Engine_L  (-0.2350, -0.0300, +1.2200)
Muzzle_R  (+0.0260, -0.0425, -1.0700)     Engine_R  (+0.2350, -0.0300, +1.2200)
Cockpit   ( 0.0000, +0.1398, -0.5175)
```

Ils ne sont pas saisis à la main : ils sont **dérivés des mêmes tables** que la
géométrie (axe des tubes du canon, plan de sortie des tuyères, volume de la
verrière). Les bouches de tir remplacent le `Vector3(0, 0, -0.9)` codé en dur dans
`player_fighter_controller.gd` : la valeur juste est z = −1,07, avec un écartement
latéral de ±0,026 et un décalage ventral de −0,0425.

## 3. Point dur : **l'ADR-0008 se contredit sur l'orientation**

L'ADR-0008 pose deux règles incompatibles :

1. repère d'auteur : « nez vers **−Y**, dessus vers +Z » ;
2. résultat attendu : « après export yup, cela donne dans Godot : nez vers **−Z** ».

**La seconde ne découle pas de la première.** Vérifié empiriquement sur Blender
4.5.11 (export d'un maillage témoin, relecture binaire du `.glb`) : l'exporteur
applique `(x, y, z) → (x, z, −y)`. Un nez modelé en −Y ressort donc en **+Z** côté
Godot — c'est-à-dire vers le **bas** de l'écran. Appliquée telle quelle, la règle de
l'ADR fait voler **toute la flotte à reculons**.

C'est une panne silencieuse : la bounding box est symétrique, donc min/max Z sont
identiques dans les deux cas. Aucun contrôle dimensionnel ne peut la voir. Je l'ai
d'ailleurs constaté en direct : mon premier garde-fou (comparaison des bornes en Z)
**a laissé passer une coque retournée**.

**Arbitrage retenu.** J'ai gardé la règle qui porte le gameplay (nez vers −Z dans
Godot) *et* le repère d'auteur de l'ADR (nez vers −Y), pour que les cinq coques
produites séparément restent interopérables. `aegis_kit.export_hull()` réconcilie
les deux **en un seul endroit** : une rotation de 180° autour de Z avant l'export.
Chaîne complète : `(x, y, z)_auteur → (−x, z, y)_glTF`. C'est une rotation rigide
(pas un miroir) : bâbord reste bâbord.

Deux garde-fous protègent désormais cet invariant :

- `_assert_axis_chain()` — contrôle analytique de la chaîne d'axes avant tout export ;
- vérification, sur le `.glb` livré, que **chaque point d'attache** tombe là où la
  chaîne le prédit. Témoin asymétrique (une bouche de tir est à l'avant, une tuyère
  à l'arrière) : une coque retournée échoue immédiatement.

Preuve, en neutralisant la correction (c'est-à-dire en suivant l'ADR à la lettre) :

```
chaine d'axes rompue — nez (-Y auteur -> -Z Godot) :
    obtenu (0.0, 0.0, 1.0), attendu (0.0, 0.0, -1.0)
```

> **Action demandée à la session principale** : amender l'ADR-0008. Je n'ai pas le
> droit d'y toucher. La phrase « Après export yup, cela donne dans Godot : nez vers
> −Z » est fausse et doit devenir : « le kit applique une rotation de 180° en Z à
> l'export pour obtenir ce résultat ». À défaut, un agent qui réimplémenterait
> l'export sans le kit reproduirait le bug.

### Conséquence à connaître pour les 4 autres coques

Dans le repère d'auteur imposé (nez −Y), **bâbord est +X** et **tribord −X**
(`right = forward × up = −X`). C'est contre-intuitif et c'est un piège à inversion
gauche/droite. Le kit expose `PORT` / `STARBOARD` et surtout `attach_pair()`, qui
prend une distance **positive** à l'axe et pose lui-même les signes. Aucun auteur ne
devrait jamais écrire un signe de X à la main.

## 4. Deuxième piège rencontré (corrigé dans le kit)

`mesh.materials.clear()` **remet à zéro le `material_index` de tous les polygones**.
Poser les slots de matériaux *après* `bmesh.to_mesh()` efface donc silencieusement
toute l'assignation : la coque repasse intégralement en `AA_Hull`, sans le moindre
avertissement. C'est exactement ce qui s'est produit au premier build (7 matériaux
créés, 1 seule primitive exportée). Le kit pose désormais les slots **avant** le
transfert du BMesh, et `apply_material_slots()` refuse d'écraser des slots existants.

Piège n°3, plus discret : `bmesh.ops.bevel` a `material=0` par défaut, ce qui force
**tous les chanfreins en `AA_Hull`** — les tuyères émissives se seraient retrouvées
cerclées de blanc. Le kit passe `material=-1` (héritage des faces adjacentes).

## 5. Le kit (API stable, rien de spécifique au Specter-9)

Vérifié : aucune dimension, aucun budget, aucune forme du Specter-9 ne vit dans le
kit. Il ne connaît que les conventions de l'ADR.

- **Repère & pièges** : `PORT`, `STARBOARD`, documentation en tête de module.
- **Scène** : `reset_scene()`, `new_object(name, bm)`.
- **Palette** : `PALETTES` (Vanguard + **Null Choir**, prête pour les 3 coques
  antagonistes), `set_faction()`, `srgb_hex_to_linear()`, `material()` (mémoïsé),
  `mat_index()`, `MATERIAL_ORDER` (index de slot stables sur toutes les coques).
- **Hard-surface** : `add_ring`, `bridge_rings`, `fan_to_point`, `cap_ring`,
  `add_box`, `add_lathe` (solide de révolution : tuyères, canons, noyaux),
  `inset_panel` (découpe/enfoncement), `greeble_strip` (semé, **seedé**),
  `mirror_x`, `bevel_sharp_edges`, `shade_smooth_by_angle`, `cleanup`,
  `join_objects`.
- **Attaches** : `attach_point()`, `attach_pair()`.
- **Contrat** : `HullContract`, `HullReport`, `export_hull()`, `ContractError`.

`mirror_x` et la palette Null Choir, non exercés par le Specter-9, ont été
**fumigés séparément** (symétrie exacte, volume signé +0,16 m³ ⇒ winding inversé
correctement ; refus documenté du mélange de factions).

Note d'implémentation : `shade_smooth_by_angle()` marque les arêtes vives en pur
BMesh plutôt que d'appeler `shade_auto_smooth` (modificateur Geometry Nodes) —
même rendu, mais purement déclaratif, donc rejouable à l'identique.

## 6. Auto-validation : la preuve

`export_hull()` **relit le `.glb` produit** (parse binaire du conteneur, pas la scène
en mémoire) et échoue sur : bounding box hors ±3 %, dépassement de hauteur, pivot
décentré, budget de triangles, matériau requis absent *ou présent mais non assigné*,
matériau hors nomenclature, point d'attache manquant, orientation rompue.

Quatre ruptures provoquées volontairement :

```
### CAS : budget de triangles abaisse a 4 000
    - 9836 triangles > budget 4000
### CAS : largeur attendue falsifiee (2.10 m)
    - largeur X = 1.7500 m, attendu 2.1000 m (+/-3%) — ecart 16.67%
### CAS : plafond de hauteur abaisse a 0.20 m
    - hauteur Y = 0.4104 m > plafond 0.2000 m
### CAS : point d'attache inexistant exige
    - point d'attache requis absent : Hardpoint_09
```

Aucun export hors contrat n'est possible : `ContractError` est levée **après**
écriture du fichier, mais le build sort en erreur — le `.glb` hors contrat n'est
jamais annoncé comme valide. (Voir §8, limite connue.)

## 7. Choix créatifs et justification

Tout est relevé sur la planche de concept, puis remis à l'échelle des cotes
normatives de l'ADR (qui priment).

- **Planform à double flèche** : bord d'attaque avant très fléché (~20° de l'axe)
  jusqu'à une cassure nette à y = −0,241, puis aile externe beaucoup moins fléchée
  (~40°). C'est la « double flèche » du brief, et c'est ce qui donne la silhouette
  en pointe de flèche lisible en vue de dessus.
- **Interpolation linéaire par morceaux** des tables de profil, volontairement : une
  spline arrondirait les cassures qui *font* la silhouette hard-surface.
- **Épine dorsale creusée** (`inset_panel`, −20 mm) courant du nez à la poupe, avec
  bandeaux émissifs cyan et, en son milieu, l'assemblage de canon encadré d'or — le
  détail central le plus visible depuis la caméra de jeu, comme sur la planche.
- **Carénages de tuyère** : ajoutés après un premier rendu où les deux cylindres
  avaient l'air *posés sur un pont plat*. La planche montre des fuseaux noyés dans
  l'aile, dont seule la partie arrière (collier mécanique, jonc doré, tuyère) émerge.
  Le carénage a corrigé le défaut le plus visible du premier jet.
- **Tuyères** : solide de révolution à 24 segments (le point focal arrière du
  vaisseau ; on paie sa rondeur), lèvre sombre, jonc doré, gorge et fond émissifs
  cyan — la vue arrière obtenue est très proche de la planche.
- **Canon ventral** : longeron sombre épousant le ventre, débouchant sous le nez par
  **deux tubes** (d'où `Muzzle_L`/`Muzzle_R`), platine dorée + marquage rouge sous le
  fuselage (visibles sur la vue de profil de la planche). La planche montre aussi un
  bloc mécanique dorsal à mi-corps : les deux sont modelés, ils sont cohérents (un
  mécanisme central alimentant deux tubes de menton).
- **Rouge de sécurité restreint** (charte : « marquages restreints ») : bouts d'aile
  + une bande sur la platine ventrale. 52 triangles au total — assumé comme rare.
- **Chanfrein à 1 segment (4 mm)**, plus étroit que la moitié du creux des panneaux
  (10 mm) : la marche reste franche. Un biseau à 2 segments arrondissait entièrement
  les panneaux (ils avaient l'air *peints*) et coûtait 5 000 triangles de plus pour
  un gain nul à la distance de jeu.

Contrôle qualité : le `.glb` a été **réimporté et rendu** (Cycles CPU, headless) en
vue de dessus, vue caméra de jeu (~70° au-dessus du plan), 3/4, profil et arrière.
C'est ce qui a révélé le défaut des tuyères. Les rendus sont des contrôles, non des
livrables : ils ne sont pas versionnés.

**IP** : création originale de bout en bout, construite uniquement à partir de la
planche de concept interne. Aucun nom, silhouette, marquage ou élément identifiable
d'une licence existante. Aucun asset téléchargé.

## 8. Limites connues — ce qui n'est pas satisfaisant

1. **Le mesh n'est pas *watertight*.** Les sous-ensembles (tuyères, carénages,
   verrière, longeron, poutre, greebles) s'interpénètrent au lieu d'être unis par
   booléens. Invisible en jeu et parfaitement standard pour un mesh de rendu, mais
   il y a des faces internes : le compte de 9 836 triangles inclut de la géométrie
   jamais vue. Un booléen d'union coûterait cher et fragiliserait le déterminisme ;
   je ne l'ai pas fait.
2. **Le `.glb` est écrit avant d'être validé.** En cas de rupture de contrat, le
   build échoue bruyamment (code de sortie non nul, `ContractError`), mais un fichier
   hors contrat reste sur le disque. Écrire dans un temporaire puis promouvoir serait
   plus propre — à faire si un CI consomme ce chemin.
3. **Hauteur au plancher de la fourchette.** 0,4104 m, soit 16,7 % de la longueur :
   l'ADR vise 15-25 %, le brief 0,35-0,60 m. Conforme, mais la planche montre un
   vaisseau plus épais. J'ai privilégié la lisibilité en vue de dessus (consigne
   explicite du brief) ; épaissir reste possible en retouchant `CANOPY`, `NACELLE_Z`
   et `STRAKE`, sans toucher au kit.
4. **Le ratio largeur/longueur de la planche n'est pas celui de l'ADR.** La planche
   donne ~0,755, l'ADR impose 1,75/2,46 = 0,711. Les cotes de l'ADR priment (hitbox,
   télégraphes) : le vaisseau livré est donc **~6 % plus étroit** que la planche à
   longueur égale. Écart voulu, pas une erreur.
5. **`AA_Glass` est en `alphaMode: BLEND`** (alpha 0,86) et exporte aussi
   `KHR_materials_transmission`. Godot 4 ignore l'extension *transmission* mais
   honore l'alpha : la verrière sera translucide. Si le tri de transparence pose
   problème en jeu, la rendre opaque côté Godot est sans conséquence sur le mesh.
6. **Les panneaux bleus restent assez « aplats ».** Le détail vient de la géométrie
   (creux de 10 mm + chanfrein), sans lignes de panneaux fines ; la planche en montre
   davantage. Il reste **5 164 triangles de marge** sur le budget pour en ajouter si
   la review le demande.
7. **`attach_pair()` empêche d'inverser bâbord/tribord, mais rien ne vérifie qu'un
   auteur n'a pas placé un `Muzzle_L` à un endroit absurde.** La validation contrôle
   la *transformation*, pas la *sémantique* d'une position.

## 9. Suggestions pour la suite

- **Amender l'ADR-0008** sur l'orientation (§3) — prioritaire : les 4 briefs suivants
  partent en parallèle et leurs auteurs liront la phrase fausse.
- Éclairage : les coques passent en `shaded`. Sans key + rim + fill, elles paraîtront
  **plus ternes que les sprites** (l'ADR le dit déjà). La rim light froide est ce qui
  fait « décoller » le blanc cassé sur le fond sombre — mes rendus de contrôle le
  confirment nettement.
- Le `Cockpit` peut servir de point d'ancrage à la caméra de mort/cinématique.
- Les tuyères sont le seul poste coûteux (24 segments × 2). Si le budget devient
  tendu sur les boss, `NACELLE_SEGMENTS` est le premier curseur.
