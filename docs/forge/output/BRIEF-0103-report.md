# BRIEF-0103 — compte-rendu : le courant se voit, du canal jusqu'aux affûts

- **Brief** : `docs/forge/briefs/BRIEF-0103-les-conduits-vont-aux-tourelles.md`
- **Date** : 2026-09-06 — `asset-forge`
- **Livrables** : `tools/blender/build_long_cortege.py`,
  `assets/imported/models/backgrounds/long_cortege.glb`,
  `docs/forge/output/BRIEF-0103-planche-branches.png` (rendu d'acceptation, 4 vues), ce fichier.
- **Empreinte du binaire** :
  `sha256 af9418fd262ae426d67f8f03170aa5d1526a94bd29a53f2840986e052175006e`
  — 2 657 812 octets, **48 678 triangles** (54,1 % du budget), **27/27 primitives avec
  `TEXCOORD_0`**, 27/27 avec `TANGENT`, **0 image embarquée**.
- **Ce lot ne livre que de la géométrie.** Aucun `.gd`, `.tscn` ni `.tres` n'a été touché.

---

## 1. Le diff du contrat de marqueurs : **VIDE**

C'est le critère qui prime, il passe donc en premier. Les trente Empties du `.glb` livré
ont été comparés à ceux du `.glb` de `HEAD` (extrait par `git lfs smudge`), nom par nom,
parent par parent, composante par composante :

```
marqueurs avant : 30    après : 30
DIFF DU CONTRAT DE MARQUEURS : VIDE
écart maximal sur les 30 marqueurs : 0,000000 mm
```

Zéro, pas « sous le dixième de millimètre » : les translations sont **bit pour bit** les
mêmes. `Turret_01..17`, `Bay_01..07`, `Spine_01..05` et `Ambry` sont inchangés, chacun
toujours enfant du même tronçon, aucun ne porte de maillage.

C'est une conséquence de la construction, pas un coup de chance : une branche ne modifie
ni `TURRETS`, ni `PROFILE`, ni `TAPER`, ni aucune des fonctions qui échantillonnent la peau
(`turret_seat_y`, `bay_mouth_y`, `spine_seat_y`). Elle **pose de la matière au-dessus**, et
rien de ce qui décide d'un marqueur ne regarde la matière.

---

## 2. Les cotes se lisent sur le `.glb`, et c'est ce qui change le tracé

`_branch_routes()` part de `_marker_x(s, x)`, jamais de la colonne `x` de `TURRETS`. L'écart
va **jusqu'à 2,30 m** :

| Affût | `TURRETS` | `.glb` | écart | palier NOMINAL |
|---|---|---|---|---|
| `Turret_04` | −9,20 | **−11,03** | 1,83 | **hors palier** (au-delà de 10,30) |
| `Turret_07` | +9,80 | **+12,05** | 2,25 | **hors palier** |
| `Turret_08` | −5,60 | −6,74 | 1,14 | pont intérieur |
| `Turret_11` | +10,10 | **+12,40** | **2,30** | **hors palier** |
| `Turret_12` | −6,20 | −7,66 | 1,46 | pont intérieur |
| `Turret_14` | −9,40 | **−10,75** | 1,35 | **hors palier** |

Les **quatre** emplacements que le brief annonçait hors des paliers sont bien
`Turret_04 · 07 · 11 · 14`. Ils ne sont hors palier qu'en cotes **nominales** : rapportés à
la largeur locale (`_side_scale`, qui vaut jusqu'à 1,24 sur ces stations), ils retombent
tous sur le pont médian. Une branche tirée sur la table serait donc arrivée **jusqu'à
2,30 m à côté de son affût**, sur un palier qui n'est pas le sien — et rien ne l'aurait dit.

---

## 3. La famille : une gaine, et une veine qui est le seul émissif

Elle suit `build_conduits()`, dont elle est le prolongement, et non une famille étrangère :
un corps sombre en `AA_Greeble`, et **dedans** une bande en `AA_Emissive_Engine`.

| | gaine (`AA_Greeble`) | veine (`AA_Emissive_Engine`) |
|---|---|---|
| standard (14 affûts) | 0,52 m de large, +0,09 m | 0,22 m, +0,15 m |
| **lourde** (3 affûts) | 0,86 m, +0,09 m | **0,40 m**, +0,15 m |

Les six centimètres de joue entre les deux sont ce qui empêche la veine de se lire comme un
autocollant posé à plat : c'est le parti « serti » du conduit de canal, repris tel quel.

**Les trois lourdes sont `Turret_08`, `Turret_12`, `Turret_15`** — la même table que
`cortege_hardpoints.gd` (`HEAVY_TURRETS`), recopiée dans le script de forge et déclarée
comme telle : faire lire le moteur par la forge créerait une dépendance à l'envers (même
argument que pour `TURRET_KEEPOUT_R`). Si la table du jeu change, on perd la hiérarchie
visuelle, jamais une collision.

### Le ruban est DRAPÉ, et c'est la seule difficulté du lot

`_surface_box()` pose ses quatre coins au point le **plus bas** de l'empreinte. Sur un ruban
de 8 m qui part du rebord du canal (−4,02), franchit le talus (−4,26), longe le pont
intérieur (−4,30) puis **tombe de 60 cm dans la contremarche de chine** (−4,94), la
dénivelée atteint **0,92 m** : la branche aurait disparu sous la coque sur les trois quarts
de sa longueur, sans une erreur ni une ligne de journal.

D'où `_drape_ribbon()` : chaque sommet prend sa propre hauteur. Comme `_surface_y()` est
linéaire par morceaux en `x`, `_drape_samples()` échantillonne aux **points de rupture du
profil** — la peau est suivie exactement, sans un triangle de trop. Le ruban est un seul
solide (dessus, dessous, deux joues, deux bouchons), sans aucune face intérieure, et son
bobinage est **déclaré** via `_face_towards()` : l'ordre des sommets s'inverse quand le
ruban passe à bâbord, et une face retournée ne produit aucune erreur — elle disparaît.

---

## 4. Les veines, comptées **par tronçon, sur le binaire**

`_audit()` compte les triangles réellement en `AA_Emissive_Engine` **dans le couloir de
chaque branche** et compare leur aire à celle du tracé. Le contrôle est bloquant : zéro
triangle, ou une aire amputée, échoue le build.

| Tronçon | branches | triangles de veine | aire de veine | émissif **total** du tronçon |
|---|---|---|---|---|
| `Section_01` | 2 | 26 | 1,81 m² | 254 tri / 27,56 m² |
| `Section_02` | 3 | 44 | 3,34 m² | 122 tri / 41,97 m² |
| `Section_03` | 3 | 38 | 3,98 m² | 110 tri / 40,30 m² |
| `Section_04` | 4 | 56 | 5,72 m² | 146 tri / 45,71 m² |
| `Section_05` | 5 | 74 | 6,28 m² | 166 tri / 47,80 m² |
| **total** | **17** | **238** | **21,13 m²** | 798 tri / 203,3 m² |

Détail par affût (colonnes « tri » et « m² relevé » lues sur le `.glb`, colonne « tracé »
calculée avant maillage) :

| affût | classe | du x | au x | longueur | veine | tri | m² relevé | tronçon |
|---|---|---|---|---|---|---|---|---|
| `Turret_01` | standard | −1,07 | −3,40 | 2,33 | 0,22 | 8 | 0,522 | `Section_01` |
| `Turret_02` | standard | +1,09 | +6,80 | 5,71 | 0,22 | 18 | 1,288 | `Section_01` |
| `Turret_03` | standard | +1,12 | +7,00 | 5,88 | 0,22 | 18 | 1,325 | `Section_02` |
| `Turret_04` | standard | −1,34 | −8,43 | 7,09 | 0,22 | 18 | 1,589 | `Section_02` |
| `Turret_05` | standard | +1,12 | +3,00 | 1,88 | 0,22 | 8 | 0,424 | `Section_02` |
| `Turret_06` | standard | −1,10 | −5,62 | 4,53 | 0,22 | 10 | 1,007 | `Section_03` |
| `Turret_07` | standard | +1,38 | +9,45 | 8,08 | 0,22 | 20 | 1,836 | `Section_03` |
| `Turret_08` | **LOURDE** | −1,35 | −4,14 | 2,79 | 0,40 | 8 | 1,134 | `Section_03` |
| `Turret_09` | standard | +1,07 | +5,24 | 4,17 | 0,22 | 10 | 0,928 | `Section_04` |
| `Turret_10` | standard | −1,12 | −7,20 | 6,08 | 0,22 | 18 | 1,391 | `Section_04` |
| `Turret_11` | standard | +1,38 | +9,80 | 8,43 | 0,22 | 20 | 1,912 | `Section_04` |
| `Turret_12` | **LOURDE** | −1,38 | −5,06 | 3,68 | 0,40 | 8 | 1,486 | `Section_04` |
| `Turret_13` | standard | +1,12 | +6,20 | 5,08 | 0,22 | 12 | 1,128 | `Section_05` |
| `Turret_14` | standard | −1,28 | −8,15 | 6,87 | 0,22 | 18 | 1,551 | `Section_05` |
| `Turret_15` | **LOURDE** | −1,12 | −3,40 | 2,28 | 0,40 | 8 | 0,931 | `Section_05` |
| `Turret_16` | standard | −1,12 | −7,60 | 6,48 | 0,22 | 20 | 1,494 | `Section_05` |
| `Turret_17` | standard | +1,12 | +6,40 | 5,28 | 0,22 | 16 | 1,172 | `Section_05` |

L'aire relevée dépasse toujours (longueur × largeur) : c'est le **drapé** — le ruban est plus
long que sa projection, et c'est le talus du rebord et la contremarche de chine qui paient
la différence.

**Part émissive de la coque** : `AA_Emissive_Engine` passe de 183,5 à **203,3 m²** d'aire
totale (0,41 → **0,45 %**) et de 182,1 à **202,2 m²** d'aire vue (1,01 → **1,12 %**).
« Violet + magenta » sur l'aire vue : **1,31 %**, cible 5, cliquet du harnais 9.

---

## 5. Quelles tourelles sont desservies — **les dix-sept**, et aucune ne manque

`_branch_routes()` teste chaque couloir contre les quatre gardes du fichier (`_bay_clash`,
`_pit_clash`, `_ambry_clash`, `_turret_clash`) plus une longueur utile minimale de 1,20 m,
et **aucun des dix-sept n'est rejeté**. Un emplacement inatteignable aurait été rendu ici
avec sa raison ; il n'y en a pas.

Ce n'est pas un hasard de tracé, c'est la conséquence de trois choix :

- la branche court à la **station exacte** de son affût, ce qui la rend perpendiculaire au
  seul obstacle longitudinal du pont (les ouvertures de hangar), au lieu de le longer ;
- elle **dessert son propre flanc** : les sept ouvertures et les six creux sont sur un bord,
  et une branche ne traverse jamais le canal ;
- elle **s'arrête au bord du disque**, donc elle n'a jamais à négocier avec l'affût.

Les deux plus courtes sont `Turret_05` (1,88 m) et `Turret_15` (2,28 m), deux affûts posés
sur le pont intérieur, tout près du canal : elles restent au-dessus du minimum de 1,20 m et
mesurent respectivement **87 et 105 px de long** à l'écran — une conduite, pas un bouton.

---

## 6. Le dégagement des dix-sept affûts, mesuré **sur le `.glb`**

Mesure faite sur les sommets qui appartiennent au couloir d'une branche (et à lui seul),
relus dans le binaire livré :

| branche | sommets | **sa** tourelle | autre affût | pont d'envol | fosse / tranchée | sommet Y | sous plafond |
|---|---|---|---|---|---|---|---|
| `Turret_01` | 52 | **2,602** | 11,620 | 15,586 | 61,827 | −4,019 | 0,819 |
| `Turret_02` | 96 | **2,602** | 8,697 | 8,590 | 56,440 | −3,967 | 0,767 |
| `Turret_03` | 96 | **2,602** | 33,426 | 7,363 | 9,040 | −3,870 | 0,670 |
| `Turret_04` | 96 | **2,602** | 21,776 | 21,590 | 10,458 | −3,870 | 0,670 |
| `Turret_05` | 52 | **2,602** | 23,950 | 4,518 | 30,740 | −3,870 | 0,670 |
| `Turret_06` | 60 | **2,602** | 43,191 | **3,555** | 6,106 | −3,870 | 0,670 |
| `Turret_07` | 123 | **2,602** | 9,403 | 27,490 | 11,340 | −3,870 | 0,670 |
| `Turret_08` | 59 | **2,608** | 14,160 | 23,594 | 16,485 | −3,870 | 0,670 |
| `Turret_09` | 68 | **2,602** | 16,747 | 18,337 | 24,955 | −3,870 | 0,670 |
| `Turret_10` | 96 | **2,602** | 15,574 | 3,790 | 37,740 | −3,870 | 0,670 |
| `Turret_11` | 136 | **2,602** | 10,202 | 27,291 | 11,740 | −3,870 | 0,670 |
| `Turret_12` | 59 | **2,608** | 14,522 | 31,045 | 7,484 | −3,870 | 0,670 |
| `Turret_13` | 78 | **2,600** | 12,855 | 36,257 | 10,740 | −3,870 | 0,670 |
| `Turret_14` | 109 | **2,602** | 11,226 | 30,290 | 16,316 | −3,870 | 0,670 |
| `Turret_15` | 52 | **2,608** | 9,249 | 9,095 | 63,956 | −3,870 | 0,670 |
| `Turret_16` | 123 | **2,602** | 6,440 | 15,490 | 70,818 | −3,870 | 0,670 |
| `Turret_17` | 84 | **2,602** | 14,180 | 25,398 | 79,540 | −3,870 | 0,670 |

- **Disque de 2,50 m : jamais entamé.** Le pire cas est 2,600 m (`Turret_13`), soit 10 cm de
  marge — c'est la garde voulue (`BRANCH_STOP = TURRET_KEEPOUT_R + 0,10`), pas un reste.
- **Ouverture de pont d'envol : jamais entamée.** Le pire cas est 3,555 m (`Turret_06` /
  `Bay_04`), très au-delà du coaming de 0,80 m du kit.
- **Fosse et tranchée de bastion : jamais entamées.** Pire cas 6,106 m.
- **Plafond** : le point le plus haut d'une branche est à **Y = −3,870**, soit 0,67 m sous le
  plafond de construction (−3,20) et 0,87 m sous celui du décor (−3,00).

Le harnais de `BRIEF-0101` reste vert, et sa table est **inchangée au millième** : les dix-
sept colonnes « module / assise » du build sont identiques à celles d'avant ce lot. Une
branche est de la matière, mais elle est posée là où le disque n'est pas.

---

## 7. Ce qui ne doit pas régresser : le cinquième garde

Une plaque de 0,16 à 0,34 m posée à la station d'un affût aurait noyé la veine de 0,15 —
défaut aussi muet que celui de `BRIEF-0101`. `_branch_clash()` rejoint donc les quatre
gardes existantes, avec 12 cm de tôle nue de chaque côté, et il est interrogé **après le
tirage** (« on tire, puis on décide d'émettre ») : le flux `rng` ne bouge pas d'un cran.

| Famille | Ce qu'elle fait quand la garde de branche parle |
|---|---|
| `build_plates()` | se décale (mêmes replis que la garde d'affût) |
| `build_ribs()` | s'éloigne de son installation |
| `build_grafts()` | s'écarte, ou est barrée |
| `build_pips()` | est retirée |

Coût mesuré, en modules : plaques 311 → **309**, greffes 54 → **50**, pastilles 75 → **70**,
nervures 75 → 75. Les zones calmes ne bougent pas d'un mètre (253,8 m, 50,8 %, plage max
50,3 m) : une branche vit à la station d'un marqueur, donc dans une emprise déjà comptée
comme occupée.

---

## 8. Largeur à l'écran — la mesure qui décide

Le cadre du jeu fait **41,60 m** au plan du pont (`_frame_coverage(-4,30)`), donc à
1920 px : **46,2 px/m en latéral**. Une branche court en latéral, sa largeur se lit donc
**en profondeur**, où le raccourci vaut `sin 70°` = 0,940 (la caméra plonge de 70,06°) :
**43,4 px/m**.

| | largeur | **à l'écran** |
|---|---|---|
| veine standard | 0,22 m | **9,5 px** |
| veine lourde | 0,40 m | **17,4 px** |
| gaine standard | 0,52 m | 22,6 px |
| gaine lourde | 0,86 m | 37,3 px |
| *(repère)* conduit du canal | 0,18 / 0,12 m | 8,3 / 5,5 px (en latéral) |

9,5 px est la plus fine chose du décor qui reste une **ligne** et non un pointillé ; la
lourde en fait presque le double, et c'est ce qui fait lire la hiérarchie d'alimentation
sans une once de couleur. Les branches ont été dimensionnées contre ces nombres, pas contre
une vue de dessus.

---

## 9. Rendu et regardé (`ADR-0006`) — `BRIEF-0103-planche-branches.png`

Quatre vues, **à 1920 × 1080, la résolution du jeu** (et non les 1440 de la planche de
sections : un ruban de 22 cm ne se juge pas à une échelle qui n'existe pas), à la caméra du
jeu, avec les **affûts réels de `turret_kit.glb`** montés sur les marqueurs et le nœud réel
de `spine_kit.glb` dans le canal :

1. `s 377` — `Turret_12` **lourde** (pont intérieur) et `Turret_11` standard (pont médian), **alimenté** ;
2. la même, **nœud abattu** ;
3. `s 261` — `Spine_03` dans le canal, `Turret_08` **lourde** et `Turret_07` standard, **alimenté** ;
4. la même, **nœud abattu**.

La planche reproduit **le réglage du moteur, pas celui du `.glb`** : `CortegeSkin` ne
multiplie pas l'émission, il l'**écrase** (`emission_energy_multiplier = 0,45` vif, `0,06`
éteint), et il pose `cortege_emissive` en albédo *et* en émission. Rendre le `.glb` brut
aurait donné une veine 3,9 fois trop vive et un écart vif/mort de 1,1 au lieu de 7,5 — une
planche qui valide ce que personne ne verra. La carte est **lue** pour le rendu ; elle
n'entre dans aucun `.glb` (`ADR-0028`).

**Ce qu'on voit** : la branche part visiblement de la lèvre du canal, franchit le talus,
traverse le pont, descend la contremarche de chine quand il y en a une, et s'arrête au ras
de la jupe de l'affût. La lourde est nettement plus large que la standard dans le même
cadre. Le Specter-9 réel et ses moteurs cyan restent lisibles par-dessus.

**Ce que la vue éteinte apprend, et c'est une réserve à remonter au concepteur** — la
branche **ne disparaît pas** : la gaine `AA_Greeble` de 0,52/0,86 m la dessine en relief, et
la veine reste une bande sombre distincte. Le but du lot est donc tenu (« ce circuit est
mort », pas « il n'y a rien ici »). **Mais l'écart mesuré est faible** : sur la bande de la
branche, la luminance moyenne ne baisse que de **4 à 5 %** entre alimenté et éteint. La
cause est mesurable et elle n'est pas dans la géométrie : le moteur ne change que
l'**émission**, or sous la clé directionnelle du jeu (1,55) le terme **diffus** de l'albédo
domine, et `cortege_emissive` sert d'albédo dans les deux états. Ce que la planche ne peut
pas montrer, c'est le **bloom** : c'est lui, en jeu, qui portera l'essentiel de l'écart. Si
le regard en jeu le confirme trop faible, le levier n'est pas ici — il est dans
`CortegeSkin` (assombrir aussi l'albédo à l'extinction, comme `PANEL_DAMP` le fait déjà pour
`AA_Panel`), et c'est du code de jeu, hors périmètre de ce lot.

---

## 10. Texture et dépliage (`ADR-0028`)

- **Aucune texture livrée**, aucune demande `TEX-NNNN` : le brief le tranche et il a raison —
  le Cortège entier est en PBR par facteurs, et la veine tire sa lumière du matériau émissif
  qu'habille `cortege_emissive`, déjà en place. Le harnais échoue le build si une image
  apparaît dans le `.glb` ; il est vert, `gltf["images"]` est absent.
- **Dépliage** : `ak.box_project_uv()` à la densité de la peau, `HULL_TILES_PER_SECTION = 20`
  soit **0,200 tuile/m** (5,00 m par tuile). Les branches sont dépliées avec le reste du
  tronçon, après triangulation, en une seule projection.
- **Densité mesurée sur le `.glb`**, par tronçon : moyenne **0,197 tuile/m** (5,07 m/tuile),
  minimum 0,141, maximum 0,200, anisotropie max **1,42**. Le minimum est la borne théorique
  de la projection en boîte (cible / √3 = 0,115) et non un défaut ; Ambry garde sa propre
  échelle, 0,699 tuile/m en moyenne.
- **`TEXCOORD_0` compté** : **27 primitives sur 27**, comme `TANGENT`.
- Le brief ne demandait pas de dépliage continu : **aucune planche au damier UV** n'est
  jointe pour ce lot — celle de `BRIEF-0089` (`--plate`, dernière vignette) couvre déjà la
  projection en boîte, inchangée ici.

---

## 11. Animation (`ADR-0046` §6)

**Figée**, comme le brief le déclare, et la déclaration est exacte : le `.glb` ne porte
aucune animation, aucun pilote, aucune image clé. Ce qui varie — l'intensité de la veine —
est un réglage de matériau poussé par le moteur.

---

## 12. Déterminisme

`./scripts/build-hull.sh --check long_cortege`, **trois exécutions** (six builds) :

```
=== run 1 ===  [build-hull]   déterminisme OK — af9418fd262ae426d67f8f03170aa5d1526a94bd29a53f2840986e052175006e
=== run 2 ===  [build-hull]   déterminisme OK — af9418fd262ae426d67f8f03170aa5d1526a94bd29a53f2840986e052175006e
=== run 3 ===  [build-hull]   déterminisme OK — af9418fd262ae426d67f8f03170aa5d1526a94bd29a53f2840986e052175006e
```

**Zéro octet divergent**, même `sha256` aux six exécutions. Les branches ne consomment aucun
tirage (`build_branches()` ne reçoit pas de `rng`) : le flux seedé des cinq familles est
exactement celui d'avant ce lot, aux rejets de `_branch_clash()` près.

---

## 13. Limites connues

1. **La table des lourdes est recopiée.** `BRANCH_HEAVY = (8, 12, 15)` double
   `cortege_hardpoints.HEAVY_TURRETS`. Si le moteur re-classe une tourelle, la branche
   gardera l'ancienne largeur — on perd une hiérarchie visuelle, jamais un dégagement (le
   rayon de garde est déjà celui de la classe lourde partout).
2. **La famille d'affût de la planche est approchée.** Le moteur la tire de
   `(serial + section) % 3` ; la forge n'a ni l'un ni l'autre et prend `(numéro + tronçon)`.
   Cela ne change ni une cote ni un dégagement — seulement l'aspect des affûts sur l'image.
3. **La planche n'a ni bloom ni post-traitement rétro.** Voir §9 : l'écart vif/éteint y est
   donc mesuré dans le cas le plus sévère.
4. **Deux branches sont courtes** (`Turret_05` 1,88 m, `Turret_15` 2,28 m) parce que leur
   affût est près du canal. C'est la géométrie du vaisseau, pas un choix : entre le rebord
   et le disque de dégagement, il n'y a pas plus de place.
5. **Une branche est droite.** Elle court à la station de son affût, sans coude. Un tracé
   coudé (longer le canal puis tourner) desservirait aussi les dix-sept, en coûtant des
   triangles et une lecture moins directe ; il redeviendra utile le jour où un obstacle
   barrera un couloir, et `_branch_routes()` est écrit pour l'accueillir (elle rend déjà une
   `reason` par affût).

## 14. Suggestions

- **Regarder l'extinction en jeu, bloom compris** (§9). Si l'écart reste faible, la piste la
  plus courte est un `EMISSIVE_DEAD_ALBEDO` dans `CortegeSkin`, sur le modèle de
  `PANEL_DAMP` — trois lignes, aucune reforge.
- **Une branche par pont d'envol** serait le même geste pour les sept hangars, et le couloir
  existe (les ouvertures sont sur le pont médian, le canal est à 6 m). À arbitrer : sept
  branches de plus, c'est +9 m² d'émissif vu et une lecture « tout est branché » qui pourrait
  diluer celle des tourelles.
- **Un nœud sur la branche.** Une petite boîte `AA_Greeble` posée à mi-parcours, à l'endroit
  où la veine franchit la contremarche de chine, dirait « il y a une machine ici » pour 12
  triangles. Volontairement pas fait dans ce lot : le brief demandait une ligne, pas un
  vocabulaire.
