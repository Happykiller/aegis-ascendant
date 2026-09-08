# BRIEF-0112 — Rapport de forge : les vraies tours d'échange

- **Brief** : `docs/forge/briefs/BRIEF-0112-les-vraies-tours-d-echange.md`
- **Date** : 2026-09-08
- **Outil** : Blender 5.2.1 LTS (`blender-aegis`), toujours `-t 1`
- **Livrables** : `assets/imported/models/backgrounds/stern_tower.glb`,
  `assets/imported/models/backgrounds/stern_hull.glb`, `assets/source/models/tower/`,
  `tools/blender/build_stern.py`, `docs/forge/output/BRIEF-0112-planche.png`, ce rapport
- **Périmètre respecté** : aucun `.gd`, `.tscn`, `.tres` touché ; aucun commit ; nacelles,
  berceaux, verrous, bras et les trois canaux d'échappement intacts ; `build_long_cortege.py`
  **pas ouvert** (le complexe industriel du `BRIEF-0111` n'est pas approché).

---

## 0. Le résultat en une ligne

**129 272 → 8 388 triangles, 26,00 → 4,70 m, 32 repères sur 32 au 0,34 µm, trois clips et
quatre rotors rejoués après réimport — et la tour se lit.** Au même cadrage, à la caméra du
jeu, la poupe gagne **+11,8 % de pixels porteurs d'arête sur tout le cadre**, **+71,1 % sur la
bande des tours du plateau** et **+26,1 % / +18,2 % sur les deux rives**, pour une couverture
identique à 0,12 % près.

| | avant (BRIEF-0110) | après |
|---|---|---|
| Les tours du plateau | 2 × 796 tri **procéduraux** | 2 × `stern_tower.glb` **instanciés** |
| Les flancs arrière | rien | 2 tours de plus, sur deux plateaux construits |
| Carène | 4 822 tri | **3 426** (−1 592 de tours, +168 d'assises) |
| Repères | 17 | **21** |
| Triangles instanciés | 12 340 | **45 892** |

---

## 1. ⚠️ LA HAUTEUR : CE N'EST PAS LE PLAFOND QUI BORNE CETTE PIÈCE, C'EST SON EMPREINTE

Le brief a raison sur les 26 m — posée sur le pont de poupe, la tour de l'auteur culmine à
`y = +14,15`, la hauteur exacte de l'œil. Mais en cherchant où dépenser les 8,60 m que la
règle B autorise, on tombe sur autre chose, et c'est mesuré :

> **La tour fait 14 m de large pour 26 de haut, soit 0,538 m de plan par mètre de hauteur.**
> Prendre les 5,20 m de la règle A demande **2,80 m** d'empreinte ; prendre les 8,60 m de la
> règle B en demande **4,63 m**. La poupe n'a nulle part 4,63 m de plan libre à `|x| ≥ 16`.

Les deux seules fenêtres de la poupe, relues dans le générateur, jamais recopiées :

| Fenêtre | Plat mesuré (en `z`) | Tour possible | Pourquoi elle s'arrête là |
|---|---:|---:|---|
| Plateau du bossage (`RIDGE_Z`) | **2,60 m** (`−8,60 … −11,20`) | **4,83 m** | au-delà de `−11,20` le bossage redescend vers `RIDGE_TAIL_TOP_Y` (`−9,25`) : « le canal s'ouvre vers l'arrière » (`BRIEF-0107`) |
| Étagère de rive du massif | **3,00 m** (`−8,60 … −11,60`) | 5,57 m | `−8,60` est la face avant du massif (7 m de falaise en 12 cm de `z`), `−11,60` le dernier anneau plein avant l'effilement de poupe |

**La borne est donc 4,83 m, et elle vient du sol.** On livre **4,70 m** — un seul binaire,
quatre stations, 3,4 cm de marge à chaque bout du plat le plus court. En dessous de cette
marge, la quantification `float32` suffit à faire flotter un coin de socle.

### 1.1 — Ce que la règle B rapporte vraiment ici : **3,80 m d'assise, pas de hauteur de pièce**

| Repère | Position (x ; y ; z) | Règle | Assise `y` | **Sommet `y` absolu** | Marge à sa limite |
|---|---|:--:|---:|---:|---:|
| `CTRL \| Tour 01` | (+5,400 ; −8,400 ; −9,900) | **A** | −8,400 | **−3,700** | 0,500 m sous `−3,20` |
| `CTRL \| Tour 02` | (−5,400 ; −8,400 ; −9,900) | **A** | −8,400 | **−3,700** | 0,500 m sous `−3,20` |
| `CTRL \| Tour 03` | (+17,725 ; −4,600 ; −10,100) | **B** | −4,600 | **+0,100** | 1,900 m sous `+2,00` |
| `CTRL \| Tour 04` | (−17,725 ; −4,600 ; −10,100) | **B** | −4,600 | **+0,100** | 1,900 m sous `+2,00` |

Les tours 03/04 sont **la même pièce que 01/02**, et leur sommet est **3,80 m plus haut** —
parce que leur assise l'est. Elles dépassent le plafond de construction de **2,70 m** ; c'est
légal parce que leur emprise entière tient à `|x| ≥ 16,460`, hors du plan de vol qui s'arrête
à 14.

⚠️ **Le harnais applique la règle sur l'EMPRISE, jamais sur le repère.** `_marker_ceiling()`
prend `min(|x|)` de la boîte **posée et pivotée** : un repère à `|x| = 17` dont la pièce
déborde à 15,5 aurait un pied dans la couche où le chasseur vole, et le centre ne le dirait
pas. Il échoue le build.

### 1.2 — Ce qu'il faudrait pour dépenser les 0,87 m restants sur les flancs

Un second binaire à 5,57 m (`VARIANTS` dans `build_tower.py`, une ligne) **et** un plateau de
rive allongé (`TOWER_SEAT_STAGES`, `TOWER_SEAT_Z`). Le sommet passerait de `+0,10` à `+0,97`.
Je ne l'ai pas fait : **0,87 m de plus sur une pièce vue à 70° de plongée rend 0,30 m
d'écran**, soit 11 px à 37,7 px/m — pour un fichier de plus et une assise qui mordrait
l'effilement de poupe. La leçon du `BRIEF-0110` §8.6 vaut ici en négatif : sur cette caméra,
c'est **l'emprise au sol** qui paie, et c'est aussi elle qui coûte.

### 1.3 — ⚠️ Et le corridor n'en profite pas, comme le brief le prévoyait

Confirmé sur `build_long_cortege.py` (lu, pas modifié) : la demi-largeur du corridor plafonne
à ~12 m, tout y est **dans** le plan de vol, donc seule la règle A s'y applique — 1,1 à 1,8 m
de ciel selon le pont. **Cette tour n'y a pas sa place**, et je n'en ai posé aucune. Le
`BRIEF-0111` vient d'y intégrer un complexe industriel ; son fichier n'a pas été ouvert.

---

## 2. La régénération — on ne décime jamais

`author/tower_build.py` est exécuté **verbatim** par-dessus `../artery/forge_geometry.py`.

⚠️ **Et c'est littéralement le même `geometry.py`** : celui de cette livraison est **octet pour
octet** celui des trois du `BRIEF-0108` (`md5 96fb44d83a06750ff5dd678ded65f258`). On ne
duplique donc pas la version patchée — `build_tower.py` importe celle de `../artery/` et
**vérifie l'égalité md5 au démarrage**. Deux copies d'un même levier, c'est un levier qui
divergera un jour en silence.

```
129 272  triangles livrés par l'auteur
 17 428  construits par son générateur, chanfreins coupés (levier 1)
 10 064  jetés par la liste de suppression et le pas de série
  8 388  LIVRÉS
```

### 2.1 — Ce qui n'existe plus à 4,70 m, et pourquoi ça a cessé d'être ce que c'est

À `k = 0,180769`, **un mètre d'auteur vaut 6,8 px** sur le plateau (37,7 px/m à `y = −8,40`)
et 8,2 px sur la rive (45,4 px/m à `y = −4,60`). Le tableau se lit avec le premier, qui est le
plus sévère.

| Famille | ×n | tri | Ce qu'elle devient à 4,70 m |
|---|---:|---:|---|
| `Collier de raccord` | 16 | 1 536 | bague de 16 cm d'épaisseur **à fleur du tuyau qu'elle ceint** → 1,1 px |
| `Grille ventilateur` | 12 | 1 152 | 12 anneaux de 4,4 cm de section → **0,30 px** — ⚠️ et ils cachaient les rotors, voir §2.2 |
| `Rayon grille ventilation` | 32 | 896 | 32 fils de 4,2 cm de diamètre → **0,29 px**, au pas de 45° |
| `Collier vertical` | 8 | 768 | idem colliers, 1,1 px |
| `Fixation nervure` | 32 | 640 | tétons de 11 cm de diamètre → 0,75 px |
| `Goujon ancrage` · `Vis porte` | 32 | 640 | goujons de 14 cm, vis de 11 cm → 0,8 à 0,95 px |
| `Boulon nervure` | 24 | 480 | boulons de 15 cm **posés sur** la nervure → 1,0 px |
| `Caillebotis` + `Traverse caillebotis` | 40 | 480 | 40 lames de 2,7 à 4,5 cm au pas de 16 cm → **0,31 px au pas de 1,1** : ce n'est plus un caillebotis, c'est une trame qui bat |
| `Montant` + `Lisse` + `Retour garde corps` | 16 | 448 | **un garde-corps de 1,12 m devient un rebord de 20 cm** ; les lisses font 0,44 px |
| `Temoin capot` · `Temoin ventilateur` · `Voyant porte` | 32 | 384 | 4,4 à 10 cm de haut → **0,30 à 0,68 px**. Une lumière d'un demi-pixel ne s'allume pas, elle clignote — **et elle vole du magenta au tir ennemi** |
| `Insert capot` · `Insert de porte` | 16 | 192 | 4 cm d'épaisseur plaqués sur ce qu'ils décorent → 0,27 px |
| `Plinthe socle` · `Plinthe passerelle` · `Balise passerelle` | 10 | 120 | 6 cm d'épaisseur → 0,41 px |
| `Bord acier` | 1 | 96 | frette de 12 cm **posée sur** la couronne de bouche → 0,82 px |
| `Repere discret 08` | 1 | — | pochoir de 0,8 m → **14,5 cm, soit 5,4 px de haut pour DEUX chiffres** — 3,4 px par glyphe, illisible et moiré. ⚠️ C'est un numéro de série de l'auteur (« asset 08/10 »), pas un marquage du jeu |
| **Total supprimé** | | **7 832** | |

Et cinq séries longues gardées **une sur deux** — le rythme suffit, la trame complète bat :

| Série | ×n → gardés | tri jetés | Pas d'origine | Pas après |
|---|---:|---:|---:|---:|
| `Ailette de dissipation` (le cône du diffuseur) | 23 → 12 | 1 056 | 17,4 cm = **1,18 px** — la fréquence de Nyquist, au pixel près | 2,4 px |
| `Ailette echangeur` | 92 → 46 | 552 | 50 cm = 3,4 px | 6,8 px |
| `Grille concentrique` (diffuseur) | 6 → 3 | 288 | — | — |
| `Montant ventilateur` | 32 → 16 | 192 | — | — |
| `Rayon de grille` (diffuseur) | 24 → 12 | 144 | — | — |
| **Total pas de série** | | **2 232** | | |

`7 832 + 2 232 = 10 064` — le compte du grand livre, à l'unité.

### 2.2 — ⚠️ Deux choses que seul le rendu dit

**(a) Supprimer la grille des ventilateurs RÉVÈLE les rotors.** Les 12 anneaux et 32 rayons
filaires plaqués sur la bouche des carters se lisaient, à 0,26 px de section, comme un voile
gris — et derrière lui, les quatre rotors ne se voyaient pas. La bouche reste fermée par sa
couronne et son bord d'acier ; le rotor est **dedans**, visible, et c'est ce que le brief
demande (« quatre rotors »). Ce n'est pas une économie, c'est une correction.

**(b) `pipe()` réécrit la résolution des courbes APRÈS `geometry.hose()`** — exactement le
défaut du pylône au `BRIEF-0108`, dans le même helper, à la même ligne. Sans le patch textuel
déclaré (`SOURCE_PATCHES`), le levier 3 est **sans effet et rien ne le dit** : les huit
conduites de refroidissement sont des **courbes**, elles n'ont de triangles qu'à la
conversion, bien après que le pilote ne puisse plus rien.

### 2.3 — Le contrat de noms : diff **VIDE**

| | auteur | livré | manquants | ajoutés | écart après division par `k` mesuré |
|---|---:|---:|---|---|---:|
| `stern_tower.glb` | **32** | **32** | aucun | aucun | **0,000342 mm** |

Le facteur `0,180769` est **remesuré sur les 32 repères** du binaire, source contre livré : ce
n'est pas une valeur recopiée du script, c'est la preuve que la pièce livrée est bien celle de
l'auteur à 4,70 m. Les `CTRL | ` sont des `Empty` et aucun levier ne les touche : le diff est
vide **par construction**, pas par précaution.

---

## 3. Les quatre rotors et les trois clips — **quel clip fait tourner quoi**

Mesuré **après réimport du `.glb`**, piste par piste, sur le **déplacement réel des sommets
évalués** (depsgraph, peau comprise). Un compteur de canaux dirait « vivant » d'un clip vide.

| Clip | Images | Objets animés | Les 4 rotors | Amplitude max | Ce qui bouge |
|---|---:|---:|:--:|---:|---|
| **`Service`** | 49 | 7 | **oui, les 4** | 0,3290 m | rotors **1 tour / boucle**, conduites ±1,4 mm, noyau pulse |
| **`Refroidissement`** | 49 | 7 | **oui, les 4** | 0,3290 m | rotors **2 tours / boucle**, conduites ±2,9 mm, noyau ×2 |
| **`Maintenance`** | 97 | 7 | **non, arrêtés** | 0,3024 m | **4 portes ouvertes à 0,302 m** sur 4 os de charnières ; conduites et noyau continuent |

⚠️ **`Service` et `Refroidissement` ne diffèrent que par une VITESSE, et un compteur
d'amplitude les déclarerait jumeaux** : les deux valent 0,3290 m, parce que dans les deux cas
une pale finit par faire un demi-tour. La mesure qui les sépare est le **déplacement au quart
du clip** :

```
Service           0,232652 m   =  2 r sin(45°)   -> le rotor a fait 90°
Refroidissement   0,329020 m   =  2 r            -> il a fait 180°
Maintenance       0,000000 m   -> il ne tourne pas
```

C'est la seule mesure qui distingue les trois **sans lire le script de l'auteur**, et elle est
dans `verify_tower.py`.

**Ce que le concepteur a à décider** (le brief le laisse ouvert, à raison) : le clip par
défaut. `PIECE_REST_CLIP["tower"] = "Service"` dans `build_stern.py` n'engage que la planche.
Mon avis, non contraignant : `Service` en croisière, `Refroidissement` tant que les trois
groupes vivent, **et rien du tout au blackout** — quatre rotors qui s'arrêtent en même temps
que les panaches s'éteignent, c'est une image de fin qui ne coûte pas une ligne de shader.
`Maintenance` n'est pas un régime moteur : c'est une pose de décor, à réserver aux tours qui
ne sont pas dans le champ de l'action.

**Les trois clips sont cuits en clés** (`NLA_TRACKS`, `export_force_sampling`) : aucun pilote
Blender ne subsiste (`ADR-0046`). C'est vérifié après réimport, pas supposé.

---

## 4. Les assises — et pourquoi il a fallu en construire deux

### 4.1 — Le plateau du bossage porte 01/02 tel quel

`build_towers()` est **retirée**, avec ses deux blocs de ventilation qui en étaient le décor
de pied. Les repères `Tour 01/02` reprennent la station des tours supprimées, à **15 cm
près** : `z = −9,90` au lieu de `−10,05`, parce que le plat du bossage va de `−8,60` à
`−11,20` et que **−9,90 en est le milieu exact**. À `−10,05`, l'empreinte débordait de 15 cm
sur la partie qui redescend vers la poupe.

### 4.2 — Les flancs arrière n'avaient pas d'assise, et il a fallu la construire

C'est la « troisième voie » du `BRIEF-0110` §3.1, pour la même raison. L'épaulement du massif
descend de `−4,60` (à `|x| = 18,20`) à `−5,63` (à 16,40), et les terrasses redescendent en
dehors jusqu'à `−7,07`. **Posée dessus telle quelle, la tour serait enterrée de 1,2 m d'un
côté et suspendue de l'autre** — le défaut exact que le `BRIEF-0109` a payé.

`build_tower_seats()` (168 triangles pour les deux) pose donc deux plateaux à trois marches,
`x 16,30 … 19,15`, `z −8,60 … −11,60`, dessus plat à **`−4,60`** — l'altitude de l'arête de
rive, donc pas une ligne de silhouette de plus. Le point le plus large de la poupe reste
`19,90`.

### 4.3 — Le `y` des quatre repères est **échantillonné**, et un harnais le prouve

`_seat_probe()` tire un rayon vertical sur une grille de 7 × 7 **dans le binaire**, sous
l'empreinte réelle de chaque pièce posée, et échoue le build si la pièce flotte, si elle
s'enterre de plus d'un centimètre, ou si l'assise n'est pas plate.

| Repère | Empreinte | Peau relue (min … max) | **Creux** | Repère `y` | Sommet `y` |
|---|---|---|---:|---:|---:|
| `Tour 01` | 2,531 × 2,531 m | −8,400 … −8,400 | **0,0000 m** | −8,400 | −3,700 |
| `Tour 02` | 2,531 × 2,531 m | −8,400 … −8,400 | **0,0000 m** | −8,400 | −3,700 |
| `Tour 03` | 2,531 × 2,531 m | −4,600 … −4,600 | **0,0000 m** | −4,600 | +0,100 |
| `Tour 04` | 2,531 × 2,531 m | −4,600 … −4,600 | **0,0000 m** | −4,600 | +0,100 |

⚠️ **On tire un rayon, on ne cherche pas les sommets proches.** Le dessus d'un bossage est un
quadrilatère de 4 × 2,6 m **sans un sommet à l'intérieur** : une mesure « sommets à moins de
30 cm » y rendrait l'altitude d'une arête voisine, ou rien.

---

## 5. Le recouvrement — mesuré, par pièce, en m³

`_piece_clash()` compare **toutes les paires** de pièces posées et de volumes construits :
21 pièces + 8 volumes, soit **406 paires**.

| Paire | Recouvrement |
|---|---:|
| `Tour 03/04` × les deux socles de pylône (`x ±17,20`, `z −0,40`) | **0,000 m³** |
| `Tour 03/04` × `Liaison 05…08` (les quatre flexibles de rebord) | **0,000 m³** |
| `Tour 03/04` × plate-forme volante `STANDARD (±17,00 ; +2,00)` | **0,000 m³** |
| `Tour 03/04` × plate-forme volante `HEAVY (±16,80 ; −4,50)` | **0,000 m³** |
| `Tour 01/02` × tout le reste | **0,000 m³** |
| **Toutes les 406 paires** | **AUCUN** |

**Le créneau `z −8,60 … −11,60` a été choisi pour ça, et le calcul est celui-ci** : les socles
de pylône tiennent `z −2,50 … +1,70`, les quatre flexibles de rebord `z 4,53 … 7,27` et
`−7,11 … −4,37`, les deux plates-formes volantes `z −0,11 … +4,11` et `−6,94 … −2,06`. C'est
le seul créneau de plus de 3 m qui reste sur l'étagère de rive, et il est à l'arrière du
massif.

⚠️ **Le seul recouvrement de la poupe reste celui du `BRIEF-0110`** : `CTRL | Pylone 01/02`
traverse la dalle `STANDARD` de la garnison de **2,284 m³** par bord. Il **préexiste**, il
n'appartient pas à ce lot, et les tours ne l'aggravent pas d'un centimètre cube.

⚠️ **Et le seuil du harnais est 1 µm, pas zéro** : une pièce posée sur son assise partage
exactement une face avec elle, ce qui donne un recouvrement de 5×10⁻¹⁶ m — positif. À zéro,
chaque pièce bien posée se déclarait « en conflit avec son propre socle », et un rapport qui
crie tout le temps ne se lit plus.

---

## 6. Ce qui n'a pas bougé, et c'est vérifié

| Critère | Chiffre relu dans le binaire |
|---|---|
| Jonction `s = 500` | **6,56 × 10⁻⁷ m** sur 48 sommets, des deux bords — le chiffre exact d'avant |
| Les trois canaux d'échappement | **0,000000000 m²** de coque dans le volume des panaches ; demi-largeur libre **2,200 m** aux trois stations, fond `−10,950` |
| `AA_Emissive_Engine` dans les canaux | **0,000000 m²** |
| Emprise des berceaux | **0,000000 m²** de décor au-dessus du pont |
| Demi-largeur max | **19,900 m** (inchangée) |
| Plafond de la carène | `y_max = −3,250` (les tours sont instanciées, pas cuites) |
| `build_long_cortege.py` | **pas ouvert** |

---

## 7. Textures et UV (`ADR-0028`)

**Le brief porte bien sa section `## Texture`, et sa section `## Animation`** — elles sont
réunies sous un titre commun, et les deux tranchent : *« Aucune image — PBR par facteurs,
`CortegeSkin` posera les cartes dérivées »* et *« Les trois clips sont conservés et cuits en
clés, rejoués après réimport »*. Aucun arbitrage n'a été nécessaire.

**Aucune texture livrée.** Les **13 images embarquées** de la livraison sont purgées avec
leurs matériaux avant l'export ; le binaire en porte **zéro**.

**`TEXCOORD_0` compté, jamais supposé : 31 primitives sur 31, dont 0 sans UV.**

| | `stern_tower.glb` | `stern_hull.glb` |
|---|---:|---:|
| Densité moyenne | **0,6701 tuile/m** (1,492 m/tuile) | 0,1994 tuile/m (5,015 m/tuile) |
| Min … max | 0,4065 … 0,7000 | — |
| **Anisotropie max** | **1,722** | 1,356 |
| Borne théorique d'une projection en boîte | √3 = **1,732** | √3 |

Le dépliage est une **projection en boîte** — c'est ce que le brief prescrit implicitement en
ne demandant pas de dépliage continu, et c'est cohérent avec les cinq pièces du `BRIEF-0108`
posées à côté (`0,70 tuile/m`, même raison : ces pièces se voient bien plus près que les 500 m
de bordé du corridor, où 0,200 tuile/m suffit). **Il n'y a donc pas de couture au sens d'un
dépliage continu** : les coutures sont les arêtes de la boîte, c'est-à-dire les changements de
face dominante, et elles tombent par construction sur les arêtes vives de la géométrie.

⚠️ **1,722 contre une borne de 1,732 : c'est serré, et j'ai cherché où.** Mesuré triangle par
triangle sur le binaire : **0,204 m² sur 90,40 (0,23 % de la surface)** dépassent une
anisotropie de 1,5, et ils sont **tous les quatre au même endroit** — les faces obliques des
quatre jambes structurelles (`04_support_1` … `07_support_4`, 0,051 m² chacune), qui sont des
poutres inclinées à 45° dans les deux plans, l'angle exact où une projection en boîte est la
plus mauvaise. **Le reste de la pièce, y compris tout le diffuseur, est sous 1,5.** Si une
carte de détail directionnelle devait s'y lire, c'est le seul endroit à reprendre.

⚠️ **Et on redimensionne AVANT de déplier.** `box_project_uv()` projette en **mètres** :
déplier à la taille de l'auteur puis réduire d'un facteur `k` multiplie la densité par `1/k`,
soit **5,5 fois trop ici**. Aucune erreur, aucun test rouge, et ça ne se verrait qu'une fois la
texture générée — donc trop tard (`BRIEF-0108` §7.2).

**Répartition des matériaux** (comptée sur le binaire) :

| Slot | Triangles | Ce que c'est |
|---|---:|---|
| `AA_Hull` | 5 644 | socle, colonne, capots, diffuseur, supports, portes |
| `AA_Greeble` | 2 284 | cavités, conduites (slot `11`), carbone technique (slot `10`) |
| `AA_Emissive_Engine` | **460** | le noyau thermique, les balises de pied, les lignes du diffuseur — **tout ce que `blackout()` doit éteindre** |
| `AA_Panel` / `AA_Trim` | 0 | — |

Les deux slots neufs suivent l'arbitrage du `BRIEF-0108` §6.1 : `AA_Greeble` (`#141419`) et
non `AA_Panel`, qui est le **violet de faction** `#452663`.

---

## 8. Déterminisme

Trois exécutions de chaque générateur, `-t 1`, **zéro octet divergent** :

```
stern_tower.glb   ea02c8893befca2b79ef8914c862e2f03b3b03036197525d947c361007461324   (x3)
stern_hull.glb    040a2c09f4210176023da4f4f6f6ff06b18c1ac5a64f3ab22ea4554ef31e5bb4   (x3)
```

---

## 9. Rendu et **REGARDÉ** (`ADR-0006`)

`docs/forge/output/BRIEF-0112-planche.png` — **neuf vignettes de 1920 × 1080**, à la caméra du
jeu `(0 ; 14 ; 5)` / FOV 62 vertical, trois directionnelles du niveau, aucune ombre portée,
**les quatre tours instanciées** par la correction d'assise du jeu (`CortegeStern._seat()`,
reproduite mot pour mot).

| # | Vignette | Ce qu'elle montre |
|---:|---|---|
| 1 | **AVANT** | la poupe du `BRIEF-0110` : deux cylindres procéduraux à chapeau violet, rien sur les flancs arrière |
| 2 | le plan de maintien | ce que le joueur voit à l'arrêt : le massif est au bord haut du cadre |
| 3 | la rive de tribord | le pylône (px 1129 ; 606), `Tour 03` sur son plateau de rive (px 813 ; 229) et `Tour 01` sur le bossage (px 172 ; 609) — les trois pièces hautes de la poupe dans un seul cadre, à trois altitudes |
| 4 | **APRÈS, même cadrage que 1** | les quatre tours instanciées |
| 5 | sans les groupes | les quatre tours sur leurs assises, sous les trois panaches |
| 6 | le massif de trois-quarts | les trois canaux, panaches à 14 % |
| 7 | de dessus | les quatre tours et les deux plateaux de rive, hors du plan de vol |
| 8 | **blackout** | émissif coupé — *celui que personne ne pense à regarder* |
| 9 | **damier UV** | à la perspective du jeu, deux densités annoncées |

⚠️ **Les numéros des vignettes viennent désormais de l'ordre de rendu.** Ils étaient écrits en
dur dans le générateur : dès qu'on en sautait une avec `--views`, la planche sortait avec des
numéros troués **et doublés** (deux vignettes « 7 »). Corrigé.

⚠️ **La carène d'avant le lot est extraite de `git HEAD` et rendue avec SES PROPRES repères,
relus dans son binaire** — pas avec la table courante. Monter 21 repères sur une coque qui en
porte 17 y poserait quatre tours sans assise, et la comparaison ne comparerait plus rien.

### La mesure du « on voit une tour d'échange »

Même cadrage, même caméra, même lumière, avant contre après. **Présence** = pixels de matière ;
**structure** = pixels portant une arête (`|∇L| > 0,045`). Un bloc gris opaque maximise la
première et échoue la seconde — c'est la définition de « nos formes simples ».

| Zone du cadre | Arêtes avant | Arêtes après | Δ structure | Matière avant | Matière après | Δ couverture |
|---|---:|---:|---:|---:|---:|---:|
| Cadre entier | 132 318 | 147 880 | **+11,8 %** | 1 896 782 | 1 894 439 | −0,12 % |
| Bande des tours du plateau | 1 351 | 2 312 | **+71,1 %** | 384 000 | 384 000 | 0,00 % |
| Rive de tribord | 17 739 | 22 368 | **+26,1 %** | 415 780 | 415 725 | −0,01 % |
| Rive de bâbord | 30 618 | 36 199 | **+18,2 %** | 412 114 | 410 440 | −0,41 % |
| **Pixels magenta** (cadre entier) | 33 610 | 34 397 | **+2,34 %** | — | — | — |

**La couverture est identique à 0,12 % près** — la silhouette de la poupe n'a pas changé — et
la structure augmente partout.

⚠️ **Les +2,34 % de magenta sont le seul chiffre qui va dans le mauvais sens, et il est
petit** : 787 pixels de plus sur 2 073 600, soit **0,038 % du cadre**. Ils viennent du cœur
thermique des quatre tours (460 triangles d'`AA_Emissive_Engine` chacune). La réserve de
couleurs de la charte reste tenue, et j'ai supprimé les trois familles de témoins de la tour
(`Temoin capot`, `Temoin ventilateur`, `Voyant porte`, §2.1) précisément pour ça : à 0,3–0,7 px
elles auraient volé du magenta au tir ennemi sans rien éclairer.

⚠️ **Ce que je n'ai pas mesuré, et qu'il faudra mesurer une fois monté** : la lisibilité des
balles PAR-DESSUS (`ADR-0006`). Aucune vignette de cette planche ne porte de tir — la poupe
n'est pas jouable depuis la forge. Le chiffre de 0,038 % du cadre est un indice, pas la preuve.

### Le blackout, vérifié sur la vignette 8

`CortegeStern.blackout()` n'éteint que ce qui porte `AA_Emissive_Engine`. Mesuré dans la
couronne d'une tour du plateau, au même cadrage :

```
allumé    2 805 pixels magenta,  luminance max 1,000
éteint        0 pixel magenta,   luminance max 0,459  (albédo, pas émission)
```

**Les quatre cœurs s'éteignent.** Ce qui reste à 12 % d'éclairage est la couleur de base
`#D93D9C` du slot, exactement comme sur les pièces du `BRIEF-0110`.

**Verdict : oui, on voit une tour d'échange.** Ce qui remplaçait les deux cylindres gris à
chapeau violet, c'est une machine : un **diffuseur conique à ailettes**, une **grille radiale
à 12 rayons** avec son **cœur magenta** au centre, quatre **carters de ventilateur ouverts sur
leur rotor**, quatre jambes contreventées, une passerelle de service tournée vers la caméra.
La couverture ne bouge pas — la silhouette de la poupe est la même — et la structure augmente
partout.

⚠️ **Ce que la caméra ne montre pas, et il faut le savoir** : elle plonge à 70°. De ce point de
vue, **c'est le disque du diffuseur qui domine** et il ombrelle une partie du fût ; les quatre
carters et la passerelle se lisent en périphérie, pas au centre. C'est le dessin d'une tour de
refroidissement **vue de dessus**, ce qui est juste, mais ce n'est pas la silhouette de profil
des aperçus de l'auteur. Les tours de flanc (03/04), plus hautes de 3,80 m, sont celles qui
montrent le plus de fût.

---

## 10. ⚠️ Ce qu'il reste à faire, et qui n'est pas de la forge

### 10.1 — **UNE LIGNE DE CODE MANQUE, ET SON ABSENCE EST TOTALEMENT SILENCIEUSE**

`CortegeStern.DRESS` (`scripts/gameplay/cortege_stern.gd`) mappe un préfixe de repère vers un
`.glb`. Il n'a pas d'entrée `"CTRL | Tour"`. `_kit_for()` rend alors une chaîne vide et
`_dress()` **passe au repère suivant sans un mot** : les quatre tours ne s'afficheraient pas,
sans erreur, sans test rouge, sans une ligne de journal.

```gdscript
"CTRL | Tour": "res://assets/imported/models/backgrounds/stern_tower.glb",
```

Je ne l'ai pas écrite — le brief interdit tout `.gd`. **C'est le premier geste de
l'intégration.**

### 10.2 — Le clip par défaut et le câblage des rotors

Décision de conception (§3). Rien dans le `.glb` ne l'impose : les trois pistes NLA y sont
toutes les trois, muettes à l'import.

### 10.3 — Écart assumé à `ADR-0048` : le `.blend` de l'auteur n'est pas versionné

Même arbitrage qu'au `BRIEF-0108` §10.3, et pour la même raison **vérifiée par l'exécution** :
le générateur est complet, il part d'une scène vide, et le dépôt s'en sert à chaque build. Le
`.blend` pèse 9,7 Mo de LFS et porte les 13 atlas que `ADR-0028` nous interdit d'employer. Il
est dans `~/aegis-ascendant_gpt_models/tour-echange-thermique/v1/blender/` ; une copie octet
pour octet suffit si le concepteur le veut. *C'est un arbitrage de coût, et il lui appartient.*

### 10.4 — `./scripts/check.sh` n'a pas été lancé

Le lot ne touche à aucun `.gd`, `.tscn`, `.tres` ni test. ⚠️ **Mais le `BRIEF-0110` a laissé
`check.sh` rouge** sur `test_cortege_citadel.gd ::
test_the_citadel_bites_none_of_its_three_neighbours`, un conflit **préexistant** qu'un repère
neuf a rendu visible et que la mesure 3-D contredit (`BRIEF-0110` §8.1). Ce lot n'y change
rien : ses quatre repères sont dans la poupe, pas dans le tronçon 3. L'arbitrage reste au
concepteur.

### 10.5 — Aucun coût GPU mesuré

Un relevé n'a de sens qu'une fois les pièces montées en jeu, ce qui demanderait de toucher au
code. Repère : la poupe entière rendait à **2,0–3,7 ms** sur les 16,67 d'une image à 60 Hz
avec 12 340 triangles instanciés ; elle en porte maintenant **45 892**.

### 10.6 — Le compte de triangles, rapporté et non contraint

| | |
|---|---:|
| Carène | **3 426** (était 4 822) |
| Pièces instanciées sur 21 repères | **45 892** (dont 4 × 8 388 = 33 552 de tours) |
| **Total poupe** | **111 030** |

Le repère historique de 80 000 est **dépassé de 31 030**, et c'est **délibéré** : l'opérateur a
tranché le 2026-09-08. La ligne reste imprimée par le générateur, sans plus rien refuser — un
chiffre qu'on ne compte plus est un chiffre qu'on ne saura plus. Aucun harnais de ce lot
n'échoue sur un budget.

---

## 11. Livrables

| Fichier | Ce que c'est |
|---|---|
| `assets/imported/models/backgrounds/stern_tower.glb` | la tour régénérée — 4,70 m, 8 388 tri, 863 Kio, 32 repères, 3 clips |
| `assets/imported/models/backgrounds/stern_hull.glb` | la carène — `build_towers()` retirée, 2 plateaux de rive, 21 repères |
| `tools/blender/build_stern.py` | le générateur de la carène : `build_tower_seats()`, `_marker_ceiling()`, `_seat_probe()`, `_piece_clash()` |
| `assets/source/models/tower/author/` | **les sources de l'auteur, verbatim** (3 scripts + 1 manifeste) |
| `assets/source/models/tower/build_tower.py` | le pilote : leviers, suppressions, patches déclarés, UV, export |
| `assets/source/models/tower/verify_tower.py` | la vérification **sur le binaire, après réimport** |
| `assets/source/models/tower/README.md` | comment on rejoue tout ça |
| `docs/forge/output/BRIEF-0112-planche.png` | neuf vignettes 1920 × 1080, avant/après au même cadrage |
| `docs/forge/output/BRIEF-0112-report.md` | ce document |

**Six lignes** ajoutées à `assets/licenses/ASSET_PROVENANCE.csv` et **une** mise à jour
(`stern_hull`) ; aucune autre ligne existante modifiée.
