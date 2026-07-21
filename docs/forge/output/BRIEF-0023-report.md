# BRIEF-0023 — Coque 3D du Choir Harvester (mini-boss) — compte-rendu

- **Agent** : asset-forge
- **Date** : 2026-07-12
- **Brief** : `docs/forge/briefs/BRIEF-0023-choir-harvester-hull.md`
- **Normes** : `docs/decisions/ADR-0008-pipeline-3d-blender.md`, `docs/forge/CHARTE_CREATIVE.md`
- **Référence de design** : `assets/reference/concepts/choir_harvester_concept_sheet.png`
- **Outil** : Blender 4.5.11 LTS, headless (`blender45 -b -P …`)
- **Kit** : `tools/blender/lib/aegis_kit.py` v1.0.0, **réutilisé sans aucune modification**

## 1. Livrables

| Fichier | Rôle |
|---|---|
| `tools/blender/build_choir_harvester.py` | script de construction, rejouable, déterministe |
| `assets/imported/models/bosses/choir_harvester.glb` | le mesh livré (LFS, 699 236 o) |
| `docs/forge/output/BRIEF-0023-report.md` | ce document |
| `assets/licenses/ASSET_PROVENANCE.csv` | +1 ligne (`choir_harvester_hull`) |

Commande unique : `blender45 -b -P tools/blender/build_choir_harvester.py`

## 2. Mesures réelles (relevées sur le `.glb` livré, pas sur la scène Blender)

| Critère | Contrat | Mesuré | Marge |
|---|---|---|---|
| Largeur (Godot X) | 4,55 m ±3 % | **4,5441 m** | −0,13 % |
| Longueur (Godot Z) | 7,00 m ±3 % | **7,0000 m** | 0,00 % |
| Hauteur (Godot Y) | ≤ 1,60 m | **1,3605 m** | 19 % de la longueur |
| Triangles | ≤ 25 000 | **16 156** | 35 % de marge |
| Sommets | — | 23 821 | — |
| Pivot (centre bbox X, Z) | ±0,02 m | **(−0,0024 ; 0,0000)** | centré sur le noyau |
| Fichier | — | 699 236 o | — |

Le contrat est revalidé **sur le binaire produit** par `ak.export_hull()` (bounding box,
orientation, budget, matériaux, points d'attache) : l'export échoue plutôt que de livrer
hors contrat. Deux exécutions successives donnent un `.glb` **byte-identique**
(`md5 8ceeaf9a…` avant le dernier réglage esthétique) : le build est déterministe.

### Répartition des triangles par objet

| Objet | Triangles | Rôle gameplay |
|---|---|---|
| `Hull` | 7 168 | carapace, anneaux, bec, cou, berceau |
| `Core` | 640 | **point faible** — noyau magenta émissif |
| `Petal_01` … `Petal_05` | 388 × 5 | pétales blindés de l'iris (s'ouvrent/se referment) |
| `Arm_Scythe` | 1 752 | bras-faux (lame ivoire, fil magenta) |
| `Arm_Claw_L` | 1 296 | griffe bâbord (œil magenta = `Muzzle_L`) |
| `Arm_Claw_R` | 1 500 | griffe tribord (œil magenta = `Muzzle_R`) |
| `Pod_Rear` | 1 860 | module arrière (tuyères magenta) |

Les **11 nœuds maillés sont à la transformation identité** (aucun TRS caché) : la géométrie
est exprimée dans le repère du modèle, les chiffres validés sont donc les vrais chiffres monde.

### Répartition par matériau (palette antagoniste Chœur Nul)

| Matériau | Couleur | Triangles |
|---|---|---|
| `AA_Greeble` | `#141419` anthracite très sombre | 6 798 |
| `AA_Emissive_Engine` | `#D93D9C` magenta (émissif) | 3 647 |
| `AA_Trim` | `#DDDCD2` ivoire froid | 2 512 |
| `AA_Panel` | `#452663` violet sombre | 2 070 |
| `AA_Hull` | `#24252B` anthracite | 841 |
| `AA_Glass` | membrane sombre (alpha 0,86) | 280 |
| `AA_Marking_Red` | `#7C9E52` vert maladif | 8 |

Le vert maladif est, comme l'exige la charte, d'**usage très limité** : une seule plaque de
marquage sur le dos. Les sept matériaux normalisés sont présents (exigence du kit).

## 3. Structure livrée

**Objets séparés et nommés** (le gameplay les ciblera et les animera) :
`Hull`, `Core`, `Petal_01`…`Petal_05`, `Arm_Scythe`, `Arm_Claw_L`, `Arm_Claw_R`, `Pod_Rear`.

**Points d'attache** (Empties → `Node3D` côté Godot) :

| Nom | Position (Godot X, Y, Z) | Rôle |
|---|---|---|
| `Core_Center` | (0,000 ; 0,100 ; 0,000) | centre du noyau — cible, pulsation |
| `Muzzle_L` | (−0,761 ; −0,123 ; −2,856) | œil de la griffe bâbord |
| `Muzzle_R` | (+1,847 ; −0,160 ; −2,541) | œil de la griffe tribord |
| `Engine_C` | (0,000 ; 0,020 ; +3,395) | plan de sortie du module arrière |
| `Hinge_Petal_01..05` | sur la lèvre du puits, r = 1,02 m | **pivots d'iris** |
| `Hinge_Arm_Scythe` / `_Claw_L` / `_Claw_R` | épaules | pivots de bras |
| `Hinge_Pod_Rear` | (0 ; 0,020 ; +2,420) | pivot du module |

Les `Hinge_*` ne sont pas exigés par le brief : ils sont ajoutés parce que les pièces sont
livrées à l'identité (§5). Sans eux, une animation d'iris devrait deviner ses axes de rotation.

## 4. Choix créatifs

- **Corps discoïde** : ellipse 3,64 × 4,40 m (X × Y), carapace bombée, cerclée de 24 blocs
  d'armure violets/noirs orientés tangentiellement, d'un anneau interne de 12 tenons ivoire
  et de 5 ergots ivoire **volontairement irréguliers** (38°, 92°, 148°, 214°, 322°) : le
  Chœur Nul est asymétrique (charte §4).
- **Le point faible se lit au premier coup d'œil** : le noyau est un dôme magenta émissif au
  fond d'un puits, cerclé d'un anneau émissif, et cinq pétales blindés l'entourent en iris
  entrouvert. La longueur des pétales (0,86 m) est calibrée pour que leurs pointes laissent
  un **œil magenta ouvert de ~0,21 m de rayon** au centre : vu de dessus, le boss montre une
  étoile magenta à cinq branches. Un pétale plus long refermait l'iris en dôme et masquait
  le noyau — le boss n'avait alors plus de cible évidente.
- **Trois bras, tous différents** : le bras-faux part de l'épaule arrière bâbord, s'arque
  au-dessus du corps et se termine par une lame en croissant ivoire dont le **fil magenta est
  une bande large dans le plan de la lame** (posé sur la tranche, il aurait été vu par la
  tranche à 20° de caméra, donc invisible). Les deux bras à griffes ne sont **pas** des
  miroirs : le tribord est long et sortant, le bâbord court et replié vers l'axe. Chaque
  griffe a trois serres et un œil magenta sous verre — c'est d'eux que partent les tirs.
- **Module arrière** : fuseau à écailles relié par un cou segmenté, tenu par un berceau à
  deux longerons. Il est **aplati de 30 % en Z** : `add_lathe` ne fait que des sections rondes,
  et un module rond de 1,08 m de diamètre aurait épaissi le boss inutilement (l'ADR-0008
  demande une hauteur modeste pour la lecture en vue de dessus).
- **Le détail vient de la géométrie** (ADR-0008) : plaques extrudées par `inset_panel` sur des
  secteurs de la grille polaire, joints creusés, biseaux 8 mm à 1 segment, greebles semées avec
  la graine `40507`. Aucune texture.

## 5. Écarts assumés (à lire avant review)

### 5.1 Un bec avant, absent de la planche

`ak.export_hull()` valide l'orientation avec un **témoin asymétrique** : il compare l'étendue
en Y de l'objet `hull` aux extrêmes Z du `.glb` (à 1e-3 près). Autrement dit, **l'objet-coque
doit porter lui-même la pointe avant et la poupe du modèle**. Or, sur la planche, la pointe
avant est constituée par les bras (lame, serres) et la poupe par le module : trois objets
séparés, qui ne peuvent pas satisfaire ce témoin.

Solution retenue : la coque ancre les deux extrêmes avec des éléments **cohérents avec la
planche mais absents d'elle** — un **bec blindé** (y = −3,50 m) et un **berceau à deux
longerons** qui encadre le module et le déborde de 8 cm (y = +3,50 m). Le bec a été
délibérément **aminci et abaissé** après un premier rendu où il volait la silhouette au
disque : il est aujourd'hui un éperon plat et discret, pas un nez de vaisseau.

Alternative rejetée : rentrer les bras à l'intérieur du disque pour que la carapace porte les
extrêmes — cela aurait écrasé les bras, c'est-à-dire exactement ce que la planche montre.

### 5.2 `Arm_Claw_L` / `Arm_Claw_R` : une lecture, pas la planche

Sur la planche, les deux bras à griffes sont **du même côté** (à l'opposé de la faux). Le brief,
lui, impose les noms `Arm_Claw_L` / `Arm_Claw_R` et deux bouches de tir `Muzzle_L` / `Muzzle_R`.
J'ai tranché pour le gameplay : **une griffe par bord**, non miroitées (longueurs, coudes et
angles différents), les tirs partant de leurs yeux. L'asymétrie du Chœur Nul est portée par la
faux (bâbord, seule, très longue) et par la dissymétrie des deux griffes.

Conséquence : `attach_pair()` n'a pas pu servir pour les bouches (il impose |x|, y, z
identiques, donc deux griffes miroir). Les points sont posés avec `ak.attach_point()` et les
constantes `ak.PORT` / `ak.STARBOARD` du kit — jamais un signe de X écrit à la main. La chaîne
d'axes est vérifiée par le kit sur le binaire (`Muzzle_R` ressort bien en +X Godot = tribord).

### 5.3 Évolution du kit à prévoir (signalée, **pas** faite)

`ak.export_hull(hull, attach_points, …)` n'expose qu'**un seul** objet maillé. Les dix pièces
nommées de ce boss sont donc passées dans la liste `attach_points`, qui joue de fait le rôle de
« liste des objets à exporter avec la coque ». Deux conséquences que le script assume
explicitement :

1. `export_hull()` n'applique la correction d'axe qu'à `hull.data` ; le script l'applique donc
   aux pièces, **en réutilisant la constante du kit** (`ak._AXIS_FIX`, jamais une copie locale :
   une divergence ferait voler la coque à reculons sans qu'aucun contrôle ne le voie) ;
2. le validateur calcule la bounding box à partir des accesseurs glTF, donc dans l'espace
   **local** de chaque maillage : il ne verrait pas une pièce déplacée par un TRS de nœud.
   Toutes les pièces sont donc laissées à l'identité, et les pivots d'animation sont livrés
   à côté, en points d'attache `Hinge_*`.

**Évolution proposée** (pour la session principale, hors de ce brief) : donner à `export_hull()`
un paramètre `parts: list[Object]` qui (a) applique `_AXIS_FIX` à chaque pièce, (b) inclut les
pièces dans le calcul de `author_y` du témoin d'orientation, (c) refuse tout TRS de nœud non
identitaire. Le kit n'a **pas** été modifié : trois autres coques s'appuient dessus en parallèle.

## 6. Vérifications

- [x] `blender45 -b -P tools/blender/build_choir_harvester.py` régénère le `.glb` sans erreur
- [x] Bounding box 4,544 × 7,000 m (±3 % respecté), hauteur 1,361 m ≤ 1,60 m
- [x] 16 156 triangles ≤ 25 000
- [x] Noyau magenta émissif, 5 pétales, bras-faux et 2 bras à griffes **présents et nommés**
- [x] Pivot centré sur le noyau (centre de bbox à 2,4 mm de l'origine en X, 0,0 en Z)
- [x] Points d'attache présents, positions dérivées de la géométrie (jamais devinées)
- [x] Kit partagé réutilisé **sans modification** (évolution signalée en §5.3, pas faite)
- [x] Provenance renseignée (`choir_harvester_hull`)
- [x] Build déterministe (deux exécutions → `.glb` byte-identique)
- [x] IP : création originale, aucune silhouette ni nom d'une licence existante

Rendus de contrôle (Cycles, hors dépôt) faits en vue de dessus, en vue de jeu (~20° de la
verticale) et en 3/4 rapproché sur le noyau : l'iris magenta est le premier élément lu.

## 7. Limites connues

- **Pas de LOD, pas de textures, pas de rig** (hors périmètre du brief). Les pièces sont
  séparées et nommées ; l'animation (iris, bras, dérive du module) reste à faire côté Godot.
- Le `Hull` reste l'objet le plus lourd (7 168 tris) parce qu'il porte la grille polaire et
  tous les blocs du cerclage. Si le budget devenait critique ailleurs, `N_SEG` (36) et
  `RIM_BLOCKS` (24) sont les deux leviers immédiats.
- L'articulation des bras est faite de vertèbres + icosphères : c'est lisible à la distance de
  jeu, mais un plan très rapproché (cinématique) montrerait des sphères un peu lisses. Le bake
  de textures prévu par l'ADR-0008 reste possible plus tard, par unité.
- `assets/imported/models/bosses/choir_harvester.glb.import` a été généré pendant la session par
  un import Godot lancé en parallèle (autre agent) : il n'est pas de mon fait, mais il devra
  être committé avec le `.glb` (convention `*.uid`/`*.import` du dépôt).
