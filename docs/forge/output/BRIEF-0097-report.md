# BRIEF-0097 — compte-rendu de forge : les vantaux de la Citadelle

- **Agent** : `asset-forge`
- **Date** : 2026-09-04
- **Brief** : [`docs/forge/briefs/BRIEF-0097-citadelle-vantaux.md`](../briefs/archive/BRIEF-0097-citadelle-vantaux.md)
- **Plan** : [LOT 4 — l'ouverture](../../plans/2026-09-03-citadelle-de-defense-midpoint.md)
- **Script source** : `tools/blender/build_citadel_kit.py` — **modifié**, pas remplacé (Blender 4.5.11,
  kit `aegis_kit` **inchangé**)

## 0. Livrables

| Fichier | sha256 | Taille |
|---|---|---|
| `assets/imported/models/backgrounds/citadel_kit.glb` | `c81944e29cddfd07bf905d7e1646cf1704f794c25bf85af88bbd6783072e710f` | 130 032 o |
| `docs/forge/output/BRIEF-0097-planche-vantaux.png` | `af3811106e775a3b869f0419abdd7809a10db42822949ac842e00a05c5434cee` | 1440 × 4140, **8 vignettes** |
| `tools/blender/build_citadel_kit.py` | — | le script **est** la source (`ADR-0008`) |

**Déterminisme** : `./scripts/build-hull.sh --check citadel_kit` → **« déterminisme OK »**, 0 octet
divergent. Confirmé une troisième fois : le passage `--plate`, qui reconstruit l'asset avant de
rendre, rend le **même** sha256.

⚠️ `docs/forge/output/BRIEF-0096-planche-citadelle.png` **reste en place** : c'est l'archive du
LOT 2 (elle montre la porte d'un seul tenant, qui n'existe plus). Le script ne la régénère plus.

---

## 1. LA PREUVE que les six pièces conservées n'ont pas bougé

**Méthode.** Le compte de triangles et la boîte englobante ne prouvent rien : on peut déplacer un
sommet sans changer ni l'un ni l'autre. On hache donc, **nœud par nœud**, les **octets** de chaque
accesseur de chaque primitive du `.glb` — `POSITION`, `NORMAL`, `TEXCOORD_0`, `TANGENT` et les
indices — dans l'ordre du fichier, plus le nom du matériau de chaque primitive. Le `.glb` d'avant
est celui du commit `1035b82` (LOT 2, `54545b6f…`).

| Nœud | triangles | emprise (x, y, z) | primitives · matériaux | sha256 des accesseurs |
|---|---|---|---|---|
| `citadel_bastion` | 172 | (+6,900000, 0, −3,200000) → (+11,400000, +2,900000, +3,200000) | 2 · Hull+Greeble | `8b117061…c2a4` |
| `citadel_conduit` | 80 | (+1,200000, 0, −0,440000) → (+5,400000, +0,620000, +0,440000) | 3 · Hull+Trim+Greeble | `683c482a…e27c` |
| `citadel_core` | 348 | (−1,200000, 0, −1,200000) → (+1,200000, +2,180000, +1,200000) | 4 · Hull+Trim+Greeble+Emissive | `9cb87c92…8fcf` |
| `citadel_crown` | 124 | (+7,400000, 0, −1,900000) → (+10,000000, +0,600000, +1,900000) | 3 · Hull+Trim+Greeble | `fa32fb00…5ec7` |
| `citadel_pylon` | 88 | (+13,580000, 0, −0,900000) → (+17,200001, +3,600000, +0,900000) | 2 · Hull+Greeble | `fd47cbae…428e` |
| `citadel_relay` | 204 | (+5,400000, 0, −0,800000) → (+7,000000, +1,900000, +0,800000) | 3 · Hull+Greeble+Emissive | `213b512e…333d` |

**Le diff entre les deux relevés est VIDE** — mêmes triangles, mêmes emprises au millionième, mêmes
matériaux, **mêmes octets de sommets et d'indices**. Reproductible :

```bash
python3 <<'EOF' > avant.txt   # sur le .glb du commit 1035b82
# ... voir la méthode ci-dessus ; l'outil tient en 60 lignes et lit le glTF binaire
EOF
diff avant.txt apres.txt      # -> vide, hors les lignes citadel_gate / leaf / housing
```

**Pourquoi c'est vrai par construction, et pas seulement par mesure.** Aucune ligne des six
fonctions `build_pylon`, `build_bastion`, `build_crown`, `build_relay`, `build_conduit`,
`build_core`, `build_shield` n'a été touchée, ni aucune des constantes qu'elles lisent, ni aucune
primitive partagée (`_loft`, `_box`, `_octagon`, `_rect`, `_regular`, `_ring_x`, `_ring_y`,
`_face_facing`, `_newell`). Une seule constante a été **renommée** — `GATE_HALF_X` → `DOOR_HALF_X`,
même littéral `17.20`, que `PYLON_X1` continue de lire : un renommage ne change pas un flottant.
L'ordre de construction a changé (le vantail et le logement passent en tête de `build_parts`), ce
qui déplace les pièces dans le fichier mais **pas leur contenu** — c'est précisément ce que
l'empreinte par nœud vérifie.

---

## 2. La table que le moteur attend — emprises MESURÉES sur le binaire

Repère local d'une pièce : **x de coque** (cuit dans la géométrie), **y depuis son assise**,
**s relatif à la station 240**.

| Nœud | x min | x max | y min | y max | s min | s max | triangles | copies |
|---|---|---|---|---|---|---|---|---|
| `citadel_leaf` | **0,00** | **12,90** | 0,00 | 3,60 | −0,60 | +0,60 | **172** | 2 |
| `citadel_housing` | **12,70** | **17,20** | 0,00 | 3,90 | −0,80 | +0,80 | **132** | 2 |
| `citadel_pylon` | 13,58 | 17,20 | 0,00 | 3,60 | −0,90 | +0,90 | 88 | 2 |
| `citadel_bastion` | 6,90 | 11,40 | 0,00 | 2,90 | −0,40 | +6,00 | 172 | 2 |
| `citadel_crown` | 7,40 | 10,00 | 0,00 | 0,60 | +1,60 | +5,40 | 124 | 2 |
| `citadel_relay` | 5,40 | 7,00 | 0,00 | 1,90 | +0,60 | +2,20 | 204 | 2 |
| `citadel_conduit` | 1,20 | 5,40 | 0,00 | 0,62 | +0,96 | +1,84 | 80 | 2 |
| `citadel_core` | −1,20 | 1,20 | 0,00 | 2,18 | +2,20 | +4,60 | 348 | 1 |
| `citadel_shield` | −1,80 | 1,80 | −1,50 | 1,50 | +1,98 | +2,22 | 28 | 1 |
| | | | | | | **TOTAL** | **1 348** | 16 |

- **Neuf nœuds, les noms de la table du brief à la lettre, et `citadel_gate` a disparu.** Le harnais
  échoue le build si l'un manque **ou si l'un est en trop**.
- **1 348 triangles** pour le kit (budget du brief **≤ 2 300**, budget du script 3 000) : **+44**
  seulement par rapport au LOT 2, pour un plafond autorisé de +900. Le verrou assemblé, 16
  instances, pèse 2 320 triangles.
- Les deux **écarts assumés** du LOT 2 (`citadel_pylon.x0`, `citadel_conduit.y1`) sont inchangés et
  toujours déclarés dans `_EMPRISE_ECARTS`. **Le LOT 4 n'en ajoute aucun** : le vantail et le
  logement tombent sur leur emprise au millimètre.

### Ce que le moteur écrit — une translation, un yaw, et **une course**

| pièce | translation | yaw | course |
|---|---|---|---|
| `citadel_leaf` | (± course, −6,60, 0,00) | 0 et π | **0,00 fermé → 4,25 ouvert**, en x local |
| `citadel_housing` | (0, −6,90, 0,00) | 0 et π | — |

Le vantail est modelé **tribord, origine à son bout intérieur**. La copie bâbord subit le yaw de π,
donc sa course s'écrit `−travel` dans le repère parent : **aucune autre arithmétique de côté**.

---

## 3. La chaîne de cotes, vérifiée **aux deux positions**

Relevé sur les sommets du binaire, pas sur les constantes :

| | course 0,00 (fermé) | course 4,25 (ouvert) |
|---|---|---|
| le vantail occupe | x **+0,00 → +12,90** | x **+4,25 → +17,15** |
| engagement dans le logement (x₀ = 12,70) | **+0,200 m** ← *le recouvrement demandé* | +4,450 m |
| marge sous le bout extérieur 17,20 | +4,300 m | **+0,050 m** ← *rien ne dépasse* |
| passe libre (2 × x min) | 0,00 m (porte fermée) | **8,50 m** |
| jeu latéral dans le fourreau | +0,020 m | +0,020 m |
| jeu sous l'assise | +0,020 m | +0,020 m |

Le **fourreau est relu dans le fichier**, jamais supposé : sa demi-largeur utile (**0,62 m**) est le
plus petit `|s|` de tout ce qui se trouve au-dessus de sa sole, et le dessus de sa sole (**−6,62**)
est obtenu **au lancer de rayons verticaux à l'intérieur du U** — 171 rayons. C'est un correctif
mesuré : lire le sommet le plus haut *parmi les sommets compris entre les joues* rendait 0,00, parce
que la sole **déborde** dans les joues de 4 cm (pour ne pas leur affleurer) et qu'aucun de ses
sommets n'est donc « dans » la cavité. Le harnais annonçait 0,30 m de jeu là où il y en a 0,02.

**8,50 m de passe pour un Specter-9 de 1,76 unité de large** (`body_radius = 0,88`, `ADR-0034`) :
**4,8 fois sa largeur**. À mi-course (2,12 m) elle en fait déjà 2,4 fois.

---

## 4. Les deux mâchoires — et pourquoi elles ne s'interpénètrent PAS

### 4.1 La démonstration qui a décidé du dessin

Le brief demande trois choses qui, prises à la lettre **ensemble**, sont incompatibles ; voici
l'arithmétique, parce qu'elle décide de tout le reste.

Notons `a(s)` l'abscisse la plus interne de la matière du vantail tribord dans la bande `s`. Le yaw
de π du moteur envoie `(x, s)` sur `(−x, −s)` : le vantail bâbord occupe donc, dans la bande `s`,
les `x ≤ −a(−s)`. **Il n'y a de jour dans aucune bande si et seulement si `a(s) + a(−s) ≤ 0`.**
Une denture qui se recouvre vraiment a une **saillie** `p > 0` : `a` vaut `a₀` dans les bandes à
dent et `a₀ + p` dans les autres. La condition devient `2a₀ + p ≤ 0`, soit **`a₀ ≤ −p/2`** : *le
vantail doit franchir l'axe de la moitié de sa saillie*. Il perdrait alors `p` sur la passe
(8,50 → 8,50 − p), sortirait de son emprise « x 0 → 12,90 » et son bout ouvert dépasserait 17,15.
Une saillie visible à 23 px/m demande `p ≥ 0,50` : **la passe tomberait à 8,00 m et l'emprise serait
fausse de 25 cm.**

**Choix retenu, et il est dit plutôt qu'appliqué en silence** : les cotes du brief sont tenues
**exactement** (0,00 / 12,90 / 4,25 / 17,15 / 8,50 / recouvrement 0,20), et l'engrènement est un
**tenon-mortaise** — la face de butée reste pleine et plane à `x = 0`, la dent d'un vantail vient
fermer la mortaise de l'autre. À une caméra qui plonge à 70°, un tenon qui *entre* dans sa mortaise
et un tenon qui *s'arrête devant* donnent **la même image** : ce qui se lit est l'alternance et son
changement de phase, pas le contact.

### 4.2 Le dessin

- L'épaisseur (1,20 m) est coupée en **six bandes de 0,20 m**. Ce vantail porte les bandes **0, 2,
  4** — **trois dents, compte impair** — et laisse les trois autres en mortaises de **0,60 m de
  creux** sur un lit **plein à −3,60**.
- **Le compte impair n'est pas une préférence, c'est le miroir qui l'impose** : le yaw de π renvoie
  la bande `k` sur la bande `5 − k`, donc `{0, 2, 4}` sur `{5, 3, 1}` — le complémentaire exact.
  Une denture qui alternerait **en hauteur** reviendrait identique sur l'autre vantail : dent contre
  dent. **Seule l'excentricité en `s` est retournée par le yaw.**
- **Le tableau** : les 2,40 m les plus internes de chaque vantail sont **plus épais en haut** que la
  poutre — dessus de **0,96 m** contre 0,60. Deux lignes transversales à x = ±2,40, et la largeur
  apparente du dessus **double** au centre. C'est le « tableau » que la capture du LOT 2 disait
  manquant, et il ne coûte qu'un jeu de cotes dans la même section à dix points.
- **Le refend** : les dents s'arrêtent **7 cm avant** le plan de joint. Fermé, les deux retraits
  font au milieu exact une **gorge transversale de 0,14 m de large sur 0,60 m de creux** qui
  traverse toute l'épaisseur — un trait **noir**, franc, perpendiculaire à la porte. Elle a été
  ajoutée **après le premier tirage de la planche**, où la mâchoire se lisait comme **un** bloc
  clair au centre et non comme **deux** peignes qui se rejoignent. S'y ajoute un rentrant de 5 cm
  sur les cinq premiers centimètres du flanc, qui prolonge le trait sur les deux faces.

### 4.3 La mâchoire, MESURÉE — profil de crête à 30 cm du joint

À 30 cm de part et d'autre du plan de joint, on demande à la matière, **au lancer de rayons
verticaux sur le binaire**, jusqu'où elle monte, bande par bande :

| bande | `s` | crête tribord | crête bâbord | lecture |
|---|---|---|---|---|
| 0 | −0,60 → −0,40 | **3,60** | 2,97 | dent à tribord |
| 1 | −0,40 → −0,20 | 3,00 | **3,60** | mortaise à tribord |
| 2 | −0,20 → +0,00 | **3,60** | 3,00 | dent à tribord |
| 3 | +0,00 → +0,20 | 3,00 | **3,60** | mortaise à tribord |
| 4 | +0,20 → +0,40 | **3,60** | 3,00 | dent à tribord |
| 5 | +0,40 → +0,60 | 2,97 | **3,60** | mortaise à tribord |

**Trois dents par vantail, la marche vaut 0,60 m, aucune bande n'a la même phase que sa voisine, et
la phase s'inverse en franchissant l'axe.** Le harnais échoue le build si l'une de ces trois choses
tombe. (Les 2,97 des bandes extrêmes sont le chanfrein de couronnement du lit, 3 cm sous le lit
plat — mesuré, pas arrondi.)

### 4.4 « Fermé, aucun jour » — mesuré dans les deux directions

- **Rayon horizontal** (le jour d'une porte), 552 échantillons sur la section fermée : **454 sont
  concernés** — c'est-à-dire que les deux vantaux ont de la matière près du joint —, et sur ceux-là
  **448 montrent les deux corps qui se touchent** au plan `x = 0`. Les **6 restants** sont dans la
  gorge de refend : **ouverture maximale 0,072 m**, pour une gorge dont la largeur maximale possible
  est 0,10 m par construction. Les 98 échantillons écartés sont des **canaux de mortaise ouverts**,
  où il n'y a rien à joindre à cette hauteur — les tester reviendrait à interdire la denture
  demandée.
- **Rayon vertical** (le jour de la caméra, qui plonge à 20° de la verticale), 1 098 échantillons sur
  toute la zone du joint : **0 trou**, épaisseur minimale rencontrée **2,424 m**. Les mortaises sont
  des **poches**, pas des fentes : le lit est plein, on ne voit jamais la coque au travers.

⚠️ **Le lancer de rayons compte par nombre d'enlacement, pas par parité.** Le vantail est une union
de **quatre coques qui s'interpénètrent** (le corps et ses trois dents, enfoncées de 10 cm dans le
lit) : une parité compterait « dehors » au milieu d'un recouvrement et rapporterait un jour là où il
y a deux épaisseurs de métal.

---

## 5. Le logement — un fourreau, et son sommet est à −3,00

| | assise | hauteur mesurée | sommet composé | plafond | marge |
|---|---|---|---|---|---|
| `citadel_leaf` | −6,60 | 3,60 | **−3,00** | −3,00 (`ADR-0041`) | 0,00 |
| `citadel_housing` | **−6,90** | 3,90 | **−3,00** | −3,00 (`ADR-0041`) | 0,00 |

**Le fourreau a gagné sa garde par le BAS.** C'est la cote qui pouvait tout casser en silence, et
trois harnais la tiennent maintenant : le sommet composé de chaque pièce est confronté à son plafond
(déjà là au LOT 2), le logement doit être **plus épais** que le vantail (1,60 contre 1,20), et son
assise doit être **strictement sous** celle du vantail. Les trois échouent le build.

**C'est un U, pas une boîte, et la cote l'impose** : le sommet du vantail est *déjà* au plafond, il
ne reste pas un centimètre pour un couvercle. Deux joues (0,18 m d'épaisseur, collier de bouche à
0,80 sur les 60 premiers centimètres, deux cerces débordantes chacune) et une sole. Porte fermée, le
U montre d'en haut une **rainure de 1,24 m de large sur 4,30 m** à chaque bout de la porte ; ouverte,
le vantail la remplit. La rainure **est** l'explication du mécanisme, et elle ne coûte pas un
triangle.

---

## 6. Matériaux, émissif, UV

- **Aucun émissif sur les deux pièces neuves**, vérifié **par matériau** sur le binaire : l'aire
  `AA_Emissive_Engine` est nulle partout sauf `citadel_relay` (1,68 m², 11,3 % de sa propre aire) et
  `citadel_core` (4,19 m², 20,3 %). Le harnais échoue si une autre pièce en porte un millimètre
  carré — la règle du LOT 4 est plus dure que celle du LOT 2, et elle est *exécutée*.
- **`AA_Trim` : 0,8 % de l'aire du kit** (plafond du brief 3 %) — les merlons de couronne, le
  bouchon de conduit, et les **dessus des six dents**, qui sont le seul endroit où un liséré clair
  *dit* quelque chose. Aucun liséré continu.
- Les sept slots de `ak.MATERIAL_ORDER` et eux seuls ; ni `AA_Panel` ni `AA_Marking_Red` ; aucune
  couleur réservée aux tirs (`#3FD9E8`, `#FF5A3D`) dans un facteur de matériau.
- **UV : `TEXCOORD_0` COMPTÉ, 24 primitives sur 24** ; `TANGENT` 24/24 ; **aucune image dans le
  `.glb`** (`ADR-0028`, vérifié : ni `baseColorTexture`, ni normale, ni occlusion, ni émissive, et
  `images` est vide).
- **Dépliage : projection en boîte `ak.box_project_uv()` à 0,200 tuile/m**, la densité du bordé —
  celle de `bay_kit`, `turret_kit` et `spine_kit`. Mesurée triangle par triangle sur le binaire :
  **vantail 0,126 à 0,200 t/m, moyenne 0,199 (5,04 m/tuile), anisotropie max 1,58** ; **logement
  0,169 à 0,200, moyenne 0,200 (5,01 m/tuile), anisotropie 1,18**. La borne théorique de la méthode
  est 1,73 (une face à 45° des trois plans). **Aucune couture à signaler** : la projection en boîte
  n'est pas un dépliage continu, le brief la demande explicitement, et aucune planche de damier
  supplémentaire n'est due — la vignette 8 de la planche la montre quand même, à la perspective du
  jeu, avec la coque et les quatre kits à la même échelle.

---

## 7. Ce qui a été regardé (ADR-0006)

`docs/forge/output/BRIEF-0097-planche-vantaux.png`, 1440 × 4140, huit vignettes, produite par **le
même script que l'asset** (`-- --plate`) :

1. **Le test d'acceptation** — porte **fermée**, caméra de `graybox.tscn` sans retouche, **noir et
   blanc, émissifs coupés**, Specter-9 réel à sa place de jeu ;
2. **à mi-course** (2,12 m, passe 4,25 m) ;
3. **ouverte** (4,25 m, passe 8,50 m) ;
4. **la mâchoire de près**, trois quarts, noir et blanc — décor compris ;
5. **le plan** (la caméra du jeu est à 20° de la verticale : ce plan est, à peu de chose près, ce que
   le joueur voit) ;
6. **l'élévation de face**, calée sur la largeur réelle du cadre de jeu (41,6 m) ;
7. **le même cadre en couleur**, porte ouverte — ce que l'émissif ajoute ;
8. **le damier UV**.

**Verdict du test noir et blanc, regardé à la résolution du jeu** (la planche ramenée à 960 px de
large et postérisée à 20 niveaux, soit ce que `retro_post` en fera) : au centre de la porte, **deux
blocs de trois barres claires séparés par un trait noir franc, et les barres d'un bloc tombent en
face des creux de l'autre**. On lit « ça s'ouvre au milieu ». Ouverte, les deux moitiés sont
franchement séparées et l'artère se voit au travers.

---

## 8. Limites connues, et deux choses à trancher côté moteur

1. ⚠️ **LE PORTIQUE OCCUPE LA COURSE DU VANTAIL, ET C'EST MESURÉ.** `citadel_pylon` est hors
   périmètre (« il ne change pas »), mais ses deux jambes vivent à `|s| ∈ [0,42 ; 0,90]` et son
   chapiteau à `|s| ≤ 0,84`, c'est-à-dire **dans le passage** du vantail rétracté (`|s| ≤ 0,60`).
   Mesure sur le binaire, 725 échantillons de la section du vantail : **223 rencontrent le portique**,
   soit **1,33 m² des 4,32 m² de section (30,8 %)**, sur **jusqu'à 1,55 m en x** (x 15,60 → 17,15),
   pour `s` de −0,576 à +0,576 et Y monde de −6,54 à −4,06.
   **En jeu, cela ne se voit pas** : le vantail culmine à −3,00, le portique à −4,05, et la caméra
   plonge à 70° — le dessus du vantail masque tout ce qui est dessous, et les joues du fourreau
   ferment les flancs. **Porte fermée, ce qu'on aperçoit au fond de la rainure est le chapiteau du
   portique, 1,11 m sous le seuil** : de la machinerie au fond d'une poche, ce qui est plutôt un
   gain de lecture. Si le concepteur veut la propreté géométrique : `PYLON_LEG_S 0,66 → 0,76` et
   `PYLON_LEG_HALF_S 0,24 → 0,14` mettent les jambes à `|s| ∈ [0,62 ; 0,90]`, exactement au ras de
   la cavité — **mais cela modifie une pièce validée au LOT 2, et je ne l'ai pas fait.**
2. **Le logement se lit d'en haut comme un plateau à rainure, pas comme une fente noire** : sa
   profondeur (3,62 m) est éclairée par le dessus, et la sole rend en gris moyen. Il est par ailleurs
   à 83 % du demi-cadre, donc au ras du bord de l'écran. Rien à corriger tant que le LOT 5 ne le
   rapproche pas du centre.
3. **Les dessus de dents et les merlons de couronne partagent une signature** (des barres ivoire
   parallèles). Ils sont à 8 m l'un de l'autre, à des échelles différentes (0,20 × 1,18 m contre
   0,52 × 2,12 m) et la mâchoire est la seule à **changer de phase** sur une ligne. Si la confusion
   apparaît en jeu, la correction est d'un caractère : passer le dessus des dents en `AA_Hull` et
   laisser l'ombre des mortaises seule porter la lecture.
4. **`CortegeCitadel` ne trouvera plus `citadel_gate`, et la porte de qualité le dit.**
   `./scripts/check.sh` → **858 tests, 6 637 assertions, UNE seule défaillance** :
   `test_cortege_citadel.gd :: test_every_piece_the_engine_looks_for_exists_in_the_kit`
   (`tests/unit/test_cortege_citadel.gd:743`), parce que `CortegeCitadel.PIECES`
   (`scripts/gameplay/cortege_citadel.gd:461`) liste encore `["citadel_gate", GATE_BASE_Y, 0.00,
   false]`. **Je n'ai touché ni le code ni le test** : c'est le travail annoncé comme concurrent, et
   la table du §2 est exactement ce dont il a besoin. À noter, deux tests d'à côté passent **déjà**
   sur les pièces neuves : `test_every_mirrored_piece_is_centred_on_its_own_z` et
   `test_the_two_pieces_that_die_are_the_only_ones_that_glow`.
5. **Une leçon d'outillage, redite** : `baykit._label()` **ne replie pas** une étiquette trop longue,
   il la **coupe sans le dire**. Deux légendes de la première planche finissaient au milieu d'un mot.
   Les retours à la ligne sont désormais explicites (`\n`).

---

## 9. Ce que le harnais a attrapé pendant le chantier

Quatre défauts silencieux, tous trouvés par une mesure et non par l'œil :

1. **Un jour de 0,10 × 0,05 m par flanc, traversant, sous la porte fermée** : le refend, appliqué
   d'abord à *toute* la section, ouvrait une encoche au pied du vantail. Il ne mord plus qu'au-dessus
   de la lisse (2,34), là où la caméra voit quelque chose de toute façon.
2. **Le fond du fourreau lu à 0,00 au lieu de 0,28** (voir §3) — 0,30 m de jeu annoncé pour 0,02 m
   réel.
3. **Deux arguments de rayon inversés** dans le test vertical : il interrogeait `(x = s, s = x)` et
   rapportait 576 trous inexistants.
4. **La mâchoire se lisait comme un seul bloc clair** au premier tirage : c'est le rendu, pas la
   mesure, qui l'a dit — d'où la gorge de refend du §4.2. `ADR-0006` a encore payé.

Et deux règles de miroir, désormais distinguées par le harnais : **le centrage en Z vaut pour les
neuf** (c'est l'excentricité en `s` que le yaw retourne) ; la règle de côté, elle, dépend de ce que
l'origine **désigne** — le centre pour six pièces, qui doivent rester franchement tribord ; le
**bout intérieur** pour le vantail, dont la matière doit commencer à `x = 0` *tout juste*, ni avant
(les deux copies se recouvriraient et la passe perdrait le double) ni après (les deux moitiés
laisseraient un jour de deux fois l'écart au milieu). Une règle unique refusait l'une ou laissait
passer l'autre.
