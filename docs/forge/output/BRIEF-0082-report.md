# BRIEF-0082 — L'intérieur du noyau du Pale Leviathan : compte-rendu

*Mesuré le 2026-08-25. **Verdict : LIVRÉ**, avec **un écart assumé** (§3) et **une erreur de cote
détectée dans le brief lui-même** (§2). Le décor mesure 30,00 × 3,84 × 18,00 m, le réacteur 4,20 m
de diamètre, l'écart R−G vaut **+55,4 points** pour un plancher de 25, et le disque de dégagement
de rayon 11 m est tenu **à la lettre**, vérifié par assertion à chaque build.*

| Critère du brief | Seuil | Mesuré | |
|---|---|---|---|
| Enveloppe au sol | 28 × 16 à 32 × 20 m | **30,000 × 18,000 m** | ✅ |
| Hauteur totale | ≤ 4,0 m | **3,840 m** | ✅ |
| Rien au-dessus de Y = 0,9 m dans r = 11 m | r ≥ 11,0 m | **r = 11,166 m** | ✅ |
| Diamètre du réacteur | 3,5 à 4,5 m | **4,200 m** | ✅ |
| Contrat de noms | 12 maillages | **12/12** | ✅ |
| Points d'ancrage | 2 | **`Reactor_Core`, `Entry_Point`** | ✅ |
| UV | 100 % des primitives | **49/49 TEXCOORD_0, 49/49 TANGENT** | ✅ |
| Budget | ≤ 22 000 triangles | **19 414 (88,2 %)** | ✅ |
| Export déterministe | même sha256 | **3 exécutions identiques** | ✅ |
| Écart R−G réacteur / sol+parois | ≥ 25 points | **+55,36 points** | ✅ |
| Planche avec le Specter-9 à l'échelle | 1 vue | **vue 4, 5 exemplaires du `.glb` réel** | ✅ |

**Livrables**

| Fichier | sha256 |
|---|---|
| `assets/imported/models/bosses/core_interior.glb` | `95d6876f8cccf1dc5e76b467731e525af54d2fbdc4ec4f2058703412359be7a8` |
| `tools/blender/build_core_interior.py` | script source, déterministe, autonome |
| `docs/forge/output/BRIEF-0082-planche-quatre-vues.png` | planche de recette 1800 × 1240 |
| `docs/forge/output/BRIEF-0082-report.md` | ce fichier |

Taille du `.glb` : **1 231 112 octets**. Reconstruction :

```bash
blender45 -b -P tools/blender/build_core_interior.py            # le .glb seul
blender45 -b -P tools/blender/build_core_interior.py -- --plate # + la planche + la mesure R-G
```

⚠️ **Aucune ligne n'a été ajoutée à `assets/licenses/ASSET_PROVENANCE.csv`** : une autre forge écrit
dans ce fichier en parallèle. Les deux lignes exactes à insérer sont données au §11.

---

## 1. Ce qui a été livré

Une **arène vue du dessus**, autonome, qui remplit le plan de jeu et où l'on peut voler.

```
                     ← 30,00 m →
   ┌───────────────────────────────────────────┐   ↑
   │ ███████████   parapet 0,75 m   ███████████ │   │   ← haut de l'écran (Godot −Z)
   │ █                                       █ │   │
   │ █    ▁▁▁▁▁ nervures ▁▁▁▁▁               █ │   │
   │ █          ┌───────────┐                █ │  18,00 m
   │ █ ═════════╡  RÉACTEUR ╞═════════       █ │   │   ← travées à 90°
   │ █          └───────────┘                █ │   │
   │ █                                       █ │   │
   │ ██████████ ╞═ porte 6,0 m ═╡ ██████████ █ │   ↓
   └───────────────────────────────────────────┘
        parois 3,52 m         Entry_Point          ← bas de l'écran (Godot +Z)
```

| Nœud | Rôle | Enveloppe (repère d'auteur) | Triangles |
|---|---|---|---|
| `Floor` | pont, nervures, parapets, machinerie, chevrons | 30,00 × 18,00 × 1,07 | 5 604 |
| `Reactor` | la cible | 4,20 × 4,20 × 2,54 | 2 838 |
| `Catwalk_01` | travée vers le haut de l'écran | 3,20 × 6,37 × 0,39 | 580 |
| `Catwalk_02` | travée bâbord | 12,50 × 3,20 × 0,39 | 1 112 |
| `Catwalk_03` | travée d'entrée (traverse la porte) | 3,20 × 7,05 × 0,39 | 656 |
| `Catwalk_04` | travée tribord | 12,50 × 3,20 × 0,39 | 1 112 |
| `Rim_01` / `Rim_04` | flancs longs, toute la profondeur | 1,55 × 18,00 × 3,52 | 2 224 ×2 |
| `Rim_02/03/05/06` | retours d'angle des bords haut/bas | 5,80 × 1,55 × 3,52 | 766 ×4 |

Points d'ancrage, en coordonnées **Godot** telles que relues dans le `.glb` :

| Nom | Position | Justification |
|---|---|---|
| `Reactor_Core` | `(0,000 ; +1,100 ; 0,000)` | centre de masse visible de la cible : à mi-hauteur entre le fût et le dôme émissif |
| `Entry_Point` | `(0,000 ; 0,000 ; +7,600)` | dans la porte du parapet bas, sur la travée d'entrée, à 1,40 m du bord — le chasseur apparaît **dans** le cadre, pas dessus |

Répartition des matériaux (les sept de l'ADR-0008 sont présents et assignés) :

| Matériau | Triangles | Aire | Emploi |
|---|---|---|---|
| `AA_Greeble` | 8 723 | 62,1 % | joints de plaques, dessous, faces externes, machinerie |
| `AA_Hull` | 6 768 | 32,9 % | fond des plaques, fût, chants supérieurs |
| `AA_Trim` | 2 709 | 3,0 % | liserés osseux, arcs-boutants, couronne, chevrons |
| `AA_Panel` | 422 | 1,4 % | bande médiane des parois, face interne des parapets |
| `AA_Emissive_Engine` | 672 | **0,3 %** | dôme, épaulement, six braises — **et rien d'autre** |
| `AA_Glass` | 96 | 0,2 % | manchon translucide du réacteur |
| `AA_Marking_Red` | 24 | 0,1 % | quatre marques de vert maladif au bout des travées |

---

## 2. ⚠️ Le brief se trompe sur la cote du Specter-9 — et c'est la cote qui sert de mètre-étalon

Le brief pose le chasseur comme référence : **« 1,29 × 0,65 × 2,41 m »**. Le fichier que le jeu
charge n'a pas ces dimensions.

```
--- Specter-9 posé sur la planche : 1.752 x 0.647 x 2.460 m (X x Y x Z Godot) ---
```

Mesuré deux fois, indépendamment : par lecture directe des accesseurs `POSITION` de
`assets/imported/models/ships/specter_9.glb` (avec composition des translations de nœuds, car les
volets et les tuyères sont des pièces mobiles), et par import Blender pour la planche. Les deux
donnent **1,752 × 0,647 × 2,460 m**. C'est d'ailleurs la valeur normative du tableau de l'ADR-0008
(1,75 × 2,46, tolérance ±3 %) : **c'est le brief qui est en écart, pas la coque**.

L'écart est de **+36 % en largeur**. Il n'est pas anodin ici : un décor dimensionné contre 1,29 m
serait un tiers trop étroit partout, ce qui est *exactement* la famille d'erreur que ce brief
existe pour empêcher. La chaîne « on cite une cote au lieu de la mesurer » est celle qui a produit
les anneaux de 30 cm.

**Conséquence dans le livrable** : `fighter_envelope()` **relit le `.glb` du chasseur à chaque
build**. Aucune cote de référence n'est écrite en dur dans le script (les deux constantes de repli
ne servent que si le fichier a disparu), et le rapport d'échelle imprime un avertissement explicite
quand la mesure s'écarte du chiffre du brief. Toutes les colonnes ci-dessous emploient **1,752 m**.

```
--- echelle mesuree CONTRE LE SPECTER-9 REEL (1.752 x 0.647 x 2.460 m, lu dans specter_9.glb) ---
  ATTENTION : le brief annonce 1,29 m de large, le fichier en mesure 1.752.
  arene, largeur                  30.000 m =  17.12 largeurs de chasseur
  arene, profondeur               18.000 m =   7.32 longueurs de chasseur
  reacteur, diametre               4.200 m =   2.40 largeurs de chasseur
  dome emissif, diametre           1.960 m =   1.12 largeurs de chasseur
  travee, largeur                  3.200 m =   1.83 largeurs de chasseur
  porte d'entree, largeur          6.000 m =   3.42 largeurs de chasseur
  ouverture des bords longs       16.600 m =   9.47 largeurs de chasseur
  passage reacteur <-> paroi      12.350 m =   7.05 largeurs de chasseur
  passage reacteur <-> parapet     6.220 m =   3.55 largeurs de chasseur
  garde au sol sous le chasseur    0.300 m =   0.46 hauteurs de chasseur
  passage le plus etroit           6.000 m =   3.42 largeurs de chasseur (plancher : 2,50)
```

Le harnais **échoue le build** si le passage le plus étroit descend sous **2,5 largeurs de
chasseur**. Deux cotes ont été élargies *à cause de cette mesure*, pas à l'œil : la travée est
passée de 2,60 à **3,20 m** (1,48 → 1,83 chasseur) et la porte d'entrée de 5,20 à **6,00 m**
(2,97 → 3,42 chasseur).

Pour comparaison directe avec la faute que le brief cite :

| | largeur | en chasseurs |
|---|---|---|
| `Ring_01` de la coque du boss | 0,33 m | **0,19** |
| `Heart` de la coque du boss | 0,63 m | **0,36** |
| `Catwalk` livrée ici | 3,20 m | **1,83** |
| Porte d'entrée livrée ici | 6,00 m | **3,42** |
| Passage réacteur ↔ paroi | 12,35 m | **7,05** |

---

## 3. ⚠️ L'écart assumé : le disque de rayon 11 m est plus grand que l'arène

Le brief demande trois choses qui **ne peuvent pas être vraies ensemble** :

1. une enveloppe au sol de 28 × 16 à 32 × 20 m — donc |Z| ≤ 10 m au grand maximum ;
2. des parois de **2,5 à 4,0 m de haut** qui « ferment le cadre » ;
3. **aucune géométrie au-dessus de Y = 0,9 m dans le disque de rayon 11 m**.

Le disque de rayon 11 **déborde l'arène sur ses deux bords longs**. À Z = 9 m il couvre encore
|X| ≤ √(121 − 81) = 6,32 m ; même à l'enveloppe maximale autorisée (Z = 10 m) il couvre encore
|X| ≤ 4,58 m. Autrement dit : **aucune paroi haute ne peut exister au milieu des bords haut et bas**,
quelle que soit l'enveloppe choisie dans la fourchette du brief. La contradiction est géométrique,
pas un problème d'exécution.

**Arbitrage retenu, et il sert l'intention écrite du brief** (« le couloir jouable doit rester
libre », « tout ce qui monte cache le vaisseau ») :

- La règle (3) est tenue **à la lettre**, et **vérifiée par assertion sur les sommets** à chaque
  build — pas supposée :

  ```
  --- degagement du couloir : premier obstacle au-dessus de 0.90 m a r = 11.166 m (Rim_02) ---
  ```

  `_assert_clearance()` balaie tous les sommets de tous les objets sauf `Reactor`, retient ceux
  au-dessus de Y = 0,9 m, et échoue si le plus proche de l'origine est à moins de 11,0 m. Marge
  mesurée : **166 mm**.

- Ce sont donc **les parois qui plient** : six segments hauts (3,52 m) sur les deux flancs longs et
  les quatre angles, et **un parapet bas de 0,75 m** en travers des deux ouvertures des bords
  haut/bas — sous le seuil de 0,9 m, donc licite.

- Le contrat de noms est **intégralement tenu** : `Rim_01..06` sont bien six parois de 3,52 m de
  haut, inclinées de 1,55 m vers l'intérieur. Ce sont leurs **longueurs** qui varient, pas leur
  nature.

**Pourquoi ça tombe juste plutôt que mal.** Dans un shmup vertical, le haut et le bas de l'écran
sont précisément les zones qu'il ne faut jamais boucher : c'est de là qu'arrivent les menaces et
c'est par là qu'on entre. Une paroi de 3,5 m au milieu du bord bas aurait masqué le chasseur à son
apparition. Le parapet ferme le cadre à l'œil (on voit son dessus et sa face interne depuis une
caméra à 20° de la verticale) sans jamais entrer dans le couloir de vol. L'ouverture du bas est
d'ailleurs percée d'une **porte de 6,00 m** où `Entry_Point` est posé : le lieu dit par où l'on est
arrivé.

Vue 3 de la planche (coupe en long) montre le résultat : les deux parapets, de part et d'autre, à
0,45 m au-dessus du plan de vol.

---

## 4. Le décor recule, la cible avance — mesuré, pas affirmé

Méthode de mesure, entièrement automatique et rejouée à chaque `--plate` :

1. **Deux rendus de la même vue de dessus orthographique.** Le premier est la vue 1 de la planche.
2. Le second remplace tous les matériaux par des **émissions plates** — rouge pour `Reactor`, vert
   pour `Floor` + `Rim_*`, bleu pour les travées (exclues, le brief parle de « sol + parois ») —
   avec `filter_size = 0.01` et 1 échantillon, pour obtenir des masques francs.
3. Les masques sélectionnent les pixels du premier rendu. Aucun seuil de teinte, aucune sélection à
   l'œil : la mesure porte sur les **objets nommés du contrat**.
4. Les images sont relues en **sRGB brut** (`colorspace = Non-Color`) : « 25 points d'écart R−G »
   s'entend sur des octets d'image, pas sur des intensités linéaires.
5. La vue est rendue en **`view_transform = "Standard"`**. C'est important : AgX, le défaut de
   Blender 4.x, désature violemment les hautes lumières — le dôme magenta ressortait **blanc** et
   la mesure aurait été fausse dans le sens flatteur.

```
--- contraste mesure sur la vue de dessus (sRGB 0-255) ---
  reactor      7620 px   R=175.02 G=119.17 B=168.46   R-G =  +55.85
  decor      338456 px   R= 66.71 G= 66.22 B= 75.68   R-G =   +0.49
  ecart R-G reacteur - decor = +55.36 points (plancher : 25)
```

**+55,4 points**, soit 2,2 × le plancher. Le build **échoue** sous 25.

Rappel du précédent qu'il fallait ne pas rejouer : chambre à R−G 41,9 **et** flux à 31,5, dix points
d'écart. Ici l'écart vient de ce que **le décor n'a aucune teinte du tout** (R−G = 0,5, c'est-à-dire
neutre à un demi-point près) :

- **Aucun émissif nulle part ailleurs que sur le réacteur.** Pas même un rail lumineux à l'entrée,
  qui aurait pourtant aidé à lire la porte. Le guidage d'entrée est fait de **chevrons ivoire** :
  c'est la valeur qui guide, pas la couleur.
- **Aucune teinte sur le pont.** Une version intermédiaire y semait des plaques violettes et ivoire.
  Rendues, ce sont des carrés colorés isolés posés sur un sol neutre — et le jeu a déjà un
  vocabulaire pour ça : le violet est la couleur de l'**Orbit Drone**, l'ivoire celle du **Rescue
  Beacon** (charte §3). Un décor n'a pas le droit d'imiter un bonus. La variation du pont passe
  donc par **trois profondeurs de plaque** (affleurante, alvéole −0,105 m, plaque saillante
  +0,030 m), pas par la couleur.
- Le violet `#452663` de la charte est conservé, mais **uniquement sur les parois** (bande médiane
  segmentée) et la face interne des parapets, où il est clairement architectural : 1,4 % de l'aire.
- Le vert maladif `AA_Marking_Red` est réduit à **quatre** marques d'un mètre, au bout de chaque
  travée, contre la paroi — là où l'on ralentit, pas là où l'on tire. Il était d'abord au pied du
  réacteur (douze taches encerclant la cible) : c'était un contresens, mesuré à la planche.

La cible se distingue **par la forme et par la valeur**, comme le brief l'exige :

- c'est le **seul objet rond** d'une arène entièrement orthogonale (hors nervures) ;
- c'est le **seul objet qui perce vers le haut** : tout le reste du décor vit sous le plan de vol
  (pont −0,30 m, travées −0,05 m, nervures −0,14 m) ou au-delà du couloir (parois, parapets) ;
- c'est le **seul objet lumineux**, et son dôme fait 1,96 m de diamètre apparent, soit **1,12
  largeur de chasseur** : la cible se lit à la taille du vaisseau qui la vise.

---

## 5. Trois pièges rencontrés, et ce qu'ils coûtaient

Aucun des trois n'émet le moindre message : géométrie inchangée, contrat vert, budget respecté. Ils
ne se voient **qu'au rendu**, ce qui est l'argument même d'ADR-0006.

### 5.1 `inset_region` inset une RÉGION, pas des faces

Le brief signalait un piège sur `ak.inset_panel()` (normales nulles sur un maillage fraîchement
bâti) et il est réel — `bm.normal_update()` est appelé dans le script, jamais dans le kit, qui reste
gelé. **Mais il y en a un second, plus coûteux** : `bmesh.ops.inset_region` traite l'ensemble des
faces passées comme **une seule région** dès qu'elles partagent des arêtes.

Les 240 plaques contiguës du pont ne produisaient donc qu'**un unique liseré de 9 cm tout autour de
l'arène**. Le damier annoncé par ~2 200 triangles n'existait nulle part au rendu, et le pont
ressortait parfaitement lisse. Il a fallu **recadrer et agrandir un coin de la planche** pour s'en
apercevoir — à taille de planche, un pont lisse et un pont plaqué se ressemblent.

Correctif, dans `_inset()` : la liste est découpée en **lots sans arête commune** (deux suffisent
pour une grille régulière, comme un damier), et l'opérateur est appelé une fois par lot. Les faces
d'un lot non encore traité restent valides — `inset_region` ne touche pas aux voisines de la région.
Effet mesuré : **12 386 → 19 414 triangles**, et un pont, des parois et des travées qui existent.

### 5.2 La calotte du réacteur cachait l'émissif — depuis la vue du jeu

Première version du réacteur : basin sombre, fût, lentille magenta, **coiffe ivoire par-dessus**.
Élégante en coupe. Rendue de dessus — c'est-à-dire vue du jeu — la cible était **un bouton blanc**,
et pas un pixel de magenta n'arrivait à l'écran. C'est mot pour mot le défaut que BRIEF-0026 avait
déjà payé sur le Specter-9 (« émissif cyan dépensé sur des faces invisibles d'en haut »).

Le réacteur a été rebâti autour d'une seule contrainte : **la partie émissive est ce qu'il y a de
plus haut, dégagée de toute structure**. Un dôme ouvert au ciel, six méridiens sombres qui le
segmentent (sans eux il se lit comme une bulle rose lisse), six arcs-boutants ivoire qui montent à
côté de lui et non devant, un anneau émissif sur l'épaulement et six braises au fond de la douve.

Ce n'est plus un choix, c'est un invariant vérifié : `_assert_target_uncapped()` échoue si la
moindre face non émissive et non `AA_Greeble` entre dans la **colonne verticale du dôme**.

```
--- cible degagee : emissif jusqu'a z = 1.980 m ; structure dans la colonne du dome : aucune ---
```

### 5.3 La casquette des parois avalait la machinerie de pied

Un bandeau de caissons a été semé au pied des parois (`ak.greeble_strip`, entièrement piloté par sa
graine, ADR-0008) pour occuper la périphérie — la seule bande de l'arène où l'on ne se bat pas.
Posé à 1,15 m du mur, il était **intégralement invisible en vue de dessus** : le dévers des parois
surplombe 1,55 m de pont. Reculé à **2,50 m**, il se voit. Corollaire général : sur ce décor, la
bande de 1,55 m qui longe chaque paroi haute n'existe pas pour la caméra de jeu.

Deux défauts mineurs de la même famille, corrigés au passage :

- **Damier de z-fighting dans les quatre angles.** Les chants supérieurs des parois de flanc et des
  retours d'angle étaient coplanaires dans la zone de recouvrement : quatre taches noires de
  2 × 1,5 m, parfaitement visibles. Les retours d'angle sont désormais posés **2 cm plus bas**.
- **Trou noir dans les quatre angles.** Une première version chanfreinait les angles des parois ; le
  pont débordait alors le mur sur un triangle de 4,5 m². Les parois se **recouvrent** franchement.

---

## 6. Échelle, orientation, contrat d'export

Chaîne d'axes du kit : `(x, y, z)`<sub>auteur</sub> → `(−x, z, y)`<sub>Godot</sub>. Conséquence
utilisée partout dans le script : **+Y d'auteur = +Z Godot = bas de l'écran**, là où l'on entre.

Le décor est symétrique en X mais **volontairement asymétrique en profondeur** — parapet continu en
haut de l'écran, parapet percé d'une porte et chevronné en bas. C'est ce qui donne un sens de
lecture au lieu, et c'est aussi le seul **témoin asymétrique** qui permette au contrat du kit de
prouver que l'arène n'est pas exportée à l'envers : `Entry_Point` est relu à
`(0,000 ; 0,000 ; +7,600)` dans le `.glb`, exactement où la chaîne d'axes le prédit.

```
contrat OK — Core Interior (Pale Leviathan)
  triangles  : 19414
  sommets    : 22552
  bbox (Godot X,Y,Z) : 30.0000 x 3.8400 x 18.0000 m
  centre     : (+0.0000, +1.3000, +0.0000)
```

Le pivot est centré à mieux que 0,02 m en X et en Z (tolérance du contrat) ; le centre en Y vaut
+1,30 m, ce qui est simplement la mi-hauteur d'un volume qui va de −0,62 à +3,22.

**UV** : `ak.box_project_uv()` est appliqué à chacun des douze objets, et le fichier **produit** est
relu pour compter les attributs — on ne suppose pas, on vérifie, parce que quatre coques du dépôt
sont sorties sans UV sans le moindre avertissement.

```
--- UV du .glb livre : 49/49 primitives portent TEXCOORD_0, 49/49 portent TANGENT ---
```

Les n-gons (culots de balayage, disques de fond) sont triangulés avant export : sans cela
l'exporteur renonce aux tangentes et l'ADR-0011 devient inopérant.

**Déterminisme** : trois exécutions consécutives, trois fois
`95d6876f8cccf1dc5e76b467731e525af54d2fbdc4ec4f2058703412359be7a8`. Aucun aléa non seedé ; les
seuls tirages (machinerie de pied) passent par `ak.greeble_strip` avec des graines fixes (5101–5106).

---

## 7. La planche de recette

`docs/forge/output/BRIEF-0082-planche-quatre-vues.png`, 1800 × 1240, Cycles CPU, 96 échantillons,
fond `#070A12` (le fond spatial du jeu), `view_transform = Standard`.

| Vue | Contenu |
|---|---|
| 1 — dessus | orthographique, la lecture du jeu ; porte l'écart R−G mesuré |
| 2 — trois quarts | on est **dans** une cavité : dévers des parois, profondeur du bassin |
| 3 — coupes | deux bandes empilées : en travers (plan Godot Z = 0) et en long (plan Godot X = 0) |
| 4 — dessus + Specter-9 | **cinq exemplaires de `specter_9.glb`**, le fichier que le jeu charge |

Trois choix méritent d'être signalés :

- **La vue 4 pose le chasseur réel, pas une maquette.** Un bloc « à peu près aux cotes du
  chasseur » réintroduirait exactement le défaut que cette vue doit exclure. Le `.glb` est importé,
  ses sept maillages sont joints, et cinq clones sont posés : sur `Entry_Point`, remontant la travée
  d'entrée, en rase-mottes le long du réacteur, au large, et au plus près de la paroi tribord.
- **Les légendes sont calculées, jamais recopiées.** « travée 3,20 m = 1,8 chasseur » est dérivé des
  constantes du script et de la largeur **mesurée** du chasseur. Une légende recopiée à la main est
  la façon la plus courante de faire mentir une planche : deux d'entre elles étaient déjà fausses
  après un élargissement de travée, avant d'être rendues dynamiques.
- **Deux coupes plutôt qu'une.** Une arène de 3,84 m de haut pour 30 m de large laisse les deux
  tiers d'une tuile carrée vides. La coupe est obtenue par `clip_start` sur une caméra
  orthographique — en orthographique, `clip_start` **est** le plan de coupe.

---

## 8. Ce que le décor n'est pas, et pourquoi

- **Aucune animation, aucune hitbox, aucune logique.** Le décor est statique ; les douze maillages
  sont exportés comme **nœuds racines distincts, tous à l'origine**, avec leurs sommets en
  coordonnées absolues. Le code pose ce qui bouge depuis les deux points d'ancrage.
  *Note d'implémentation* : le seul moyen offert par le kit gelé pour exporter plusieurs maillages
  nommés est `ak.MovingPart`, dont la vocation est l'animation. Il est ici employé avec un pivot nul
  pour onze pièces **statiques**. Côté Godot le résultat est exactement ce qu'on veut — douze
  `MeshInstance3D` aux noms du contrat, transformations à l'identité — mais le nom de la primitive
  peut surprendre à la relecture.
- **Aucune pièce de la coque du boss n'a été touchée.** `build_pale_leviathan.py` et
  `pale_leviathan.glb` sont hors périmètre (BRIEF-0083) et une autre forge y travaillait pendant
  cette mission. `tools/blender/lib/aegis_kit.py` n'a **pas** été modifié d'un octet.
- **Aucun mécanisme d'ouverture de gueule**, aucune transition. Le décor est le lieu qu'on découvre
  une fois entré.

---

## 9. Limites connues

1. **Le rayon de dégagement de 11 m est tenu, mais l'esprit du brief l'était déjà à 8 m.** La
   contrainte réelle du gameplay est `GameplayPlane.BOUNDS` (X ±14, Z ±8) : rien de haut n'y entre,
   et la marge à la paroi est de 1,00 m en X. Si un jour la contrainte devait être relue comme
   « l'intérieur des bornes de jeu » plutôt que « le disque de rayon 11 », le décor la respecte
   aussi — mais alors les parapets pourraient redevenir des parois hautes et le cadre se fermerait
   complètement. C'est un arbitrage à réouvrir sciemment, pas par accident.
2. **Le pont est dense en vue de dessus.** 240 plaques de 1,50 m avec un joint de 7 cm : c'est ce
   qui donne l'échelle quand rien d'autre n'est dans le cadre, mais sous un rideau de projectiles
   c'est un fond chargé. La valeur à baisser en premier, si l'opérateur le juge bruyant, est la
   profondeur d'enfoncement (`-0,032 m` pour les plaques affleurantes) : c'est l'ombre du joint, pas
   sa couleur, qui porte le contraste.
3. **`AA_Glass` est en `alphaMode: BLEND`** (le kit règle `alpha = 0,86`). Le manchon du réacteur est
   petit — 96 triangles, 0,2 % de l'aire — mais c'est le seul élément du décor qui impose un tri de
   transparence à Godot. Si cela pose problème au rendu, le supprimer coûte une ligne (et il faudra
   alors passer `required_materials` sans `AA_Glass` au contrat).
4. **Le budget est à 88,2 %.** Il reste 2 586 triangles. Ce n'est pas assez pour une famille de
   détail supplémentaire ; c'est assez pour un ajustement. Toute reprise significative devra
   arbitrer entre la finesse du pont (`DECK_NX/NY`) et autre chose.
5. **Le rendu n'a été jugé qu'à la planche, jamais en jeu.** Ni la lisibilité sous projectiles, ni la
   sensation d'entrer, ni la durée de la plongée ne se jugent à la capture — c'est la leçon
   d'ADR-0019 et d'ADR-0020. Ce décor est à voir sur Windows, en combat, avant d'être déclaré bon.
6. **Le contraste R−G mesuré dépend de l'éclairage de la planche.** Il est représentatif (trois
   sources larges, fond du jeu, transformation d'affichage neutre), pas identique à la scène Godot,
   qui a son propre éclairage et son propre glow. Le rapport de valeurs, lui, est structurel :
   décor sans teinte, cible seule émissive.

---

## 10. Suggestions (hors périmètre, pour le concepteur)

1. **Corriger la cote du Specter-9 dans les briefs et documents qui la citent** (§2). Le chiffre
   1,29 m circule ; le fichier vaut 1,752 m. Tant que les deux coexistent, un décor sur deux sera
   dimensionné contre le mauvais étalon.
2. **Généraliser `_assert_clearance()` et le rapport « en chasseurs »** au reste du parc. Deux
   fonctions d'une trentaine de lignes chacune ; elles auraient attrapé les anneaux de 30 cm au
   premier build. Le meilleur endroit serait un module d'outillage voisin du kit — pas le kit
   lui-même, qui est gelé.
3. **Le piège `inset_region`/région (§5.1) concerne toutes les coques du dépôt.** Il vaudrait la
   peine de vérifier, sur les scripts existants qui appellent `ak.inset_panel()` avec plus d'une
   face contiguë, que le panneautage annoncé existe vraiment dans le `.glb`. Le symptôme est
   silencieux et le compte de triangles ne le trahit pas — il est simplement plus bas que prévu, ce
   que personne ne regarde.
4. **Pour BRIEF-0083 (l'ouverture de la gueule)** : `Entry_Point` est à `(0 ; 0 ; +7,6)` et la porte
   du parapet fait 6,00 m de large. Faire coïncider la sortie du tunnel de la coque avec ce point,
   et non l'inverse — c'est le décor qui porte l'échelle jouable.
5. **Le dôme émissif est l'unique source lumineuse du lieu.** Si la scène Godot n'ajoute aucune
   lumière ponctuelle au centre de l'arène, le décor sera plat. Une `OmniLight3D` magenta faible
   posée sur `Reactor_Core` ferait beaucoup, pour rien.

---

## 11. Lignes de provenance à insérer

⚠️ **Non écrites par cette forge**, sur consigne : `assets/licenses/ASSET_PROVENANCE.csv` a un autre
écrivain en parallèle. Colonnes du fichier :

```
asset_id,file_path,asset_type,source_tool,source_url,author,license,generated_date,prompt_file,modified_by,notes
```

Deux lignes à ajouter — le brief n'en exige qu'une (le `.glb`) ; la seconde suit l'usage du dépôt,
qui enregistre aussi les planches de recette (cf. `brief_0080_planche_quatre_vues`). Notes en ASCII
pur, comme les entrées voisines.

```csv
core_interior,assets/imported/models/bosses/core_interior.glb,model3d,"asset-forge (Blender 4.5.11, script)",,asset-forge (Claude),proprietary-internal,2026-08-25,docs/forge/briefs/BRIEF-0082-noyau-interieur-passerelle-reacteur.md,,"Decor 3D autonome : l interieur du noyau ouvert du Pale Leviathan (arene vue de dessus ou le chasseur plonge au deuxieme temps de chaque cycle, ADR-0021). N EST PAS une piece de la coque du boss. Genere par tools/blender/build_core_interior.py via tools/blender/lib/aegis_kit.py reutilise SANS AUCUNE modification (le script est la source, ADR-0008 : aucun .blend versionne). Creation originale ; aucun element de licence tierce ; palette Null Choir de la charte. MESURES RELEVEES SUR LE .glb LIVRE : bbox Godot 30.0000 x 3.8400 x 18.0000 m (contrat 30 x 18, tolerance 1 pct ; plafond de hauteur 4,0 m), pivot centre (+0.0000, +1.3000, +0.0000), 19414 triangles (88,2 pct du budget de 22000), 22552 sommets, 12 maillages, 1231112 octets. CONTRAT DE NOMS COMPLET, douze nœuds racines a l origine, sommets en coordonnees absolues : Floor, Reactor, Catwalk_01..04, Rim_01..06. 2 points d ancrage : Reactor_Core (0.000, +1.100, 0.000) et Entry_Point (0.000, 0.000, +7.600). 7 materiaux PBR par facteurs, repartition en AIRE : AA_Greeble 62,1 pct / AA_Hull 32,9 / AA_Trim 3,0 / AA_Panel 1,4 / AA_Emissive_Engine 0,3 / AA_Glass 0,2 / AA_Marking_Red 0,1. UV VERIFIEES SUR LE FICHIER PRODUIT par relecture du binaire : 49/49 primitives portent TEXCOORD_0 et 49/49 TANGENT (ak.box_project_uv a 0,55 tuile/m ; triangulation des n-gons avant export ; le build ECHOUE s il en manque une). ECHELLE, qui est l objet meme de ce brief : toutes les cotes sont rapportees au Specter-9 RELU DANS SON .glb a chaque build (fighter_envelope()), jamais a une valeur recopiee. ATTENTION, LE BRIEF SE TROMPE : il annonce le chasseur a 1,29 x 0,65 x 2,41 m, le fichier en mesure 1.752 x 0.647 x 2.460 (valeur normative de l ADR-0008), soit +36 pct en largeur ; le decor est dimensionne contre la valeur MESUREE. Reacteur 4,20 m = 2,40 largeurs de chasseur ; dome emissif 1,96 m = 1,12 ; travee 3,20 m = 1,83 ; porte d entree 6,00 m = 3,42 ; passage reacteur-paroi 12,35 m = 7,05 ; passage le plus etroit 6,00 m = 3,42 (le build echoue sous 2,50). A comparer aux Ring_01..05 de la coque du boss : 0,19 largeur de chasseur. DEGAGEMENT DU COULOIR verifie par assertion sur les sommets a chaque build : premier obstacle au-dessus de Y = 0,9 m a r = 11.166 m, hors reacteur (seuil 11,0 ; marge 166 mm). ECART ASSUME : le disque de rayon 11 m deborde une arene profonde de 18 m, donc aucune paroi haute ne peut exister au milieu des bords haut et bas ; les six Rim_01..06 tiennent les flancs et les angles (3,52 m de haut, devers 1,55 m vers l interieur) et deux parapets de 0,75 m — sous le seuil — ferment les deux ouvertures. Voir docs/forge/output/BRIEF-0082-report.md section 3. CONTRASTE : le decor n a AUCUNE teinte et AUCUN emissif ; tout ce qui brille appartient a la cible. Ecart R-G mesure sur la vue de dessus par masques d objets (rendu d identite a materiaux plats, sRGB brut, view transform Standard) : reacteur +55,85, sol+parois +0,49, ECART +55,36 points pour un plancher de 25 ; le build echoue sous 25. La partie emissive du reacteur est ce qu il y a de PLUS HAUT (dome ouvert au ciel) : une premiere version la coiffait d une calotte ivoire et la cible ne montrait pas un pixel de magenta en vue de dessus ; un invariant (_assert_target_uncapped) echoue desormais si la moindre face structurelle entre dans la colonne du dome. PIEGE GENERAL DECOUVERT ICI, qui concerne toutes les coques du depot : bmesh.ops.inset_region inset une REGION et non des faces, donc N faces contigues ne produisent QU UN liseré ; les 240 plaques du pont ne se voyaient nulle part au rendu alors que le contrat etait vert. Le script decoupe la liste en lots sans arete commune. Aucune animation, aucune hitbox, aucune logique : le code pose ce qui bouge depuis les deux points d ancrage. Build deterministe : trois executions byte-identiques, sha256 95d6876f8cccf1dc5e76b467731e525af54d2fbdc4ec4f2058703412359be7a8. Rendu et regarde : docs/forge/output/BRIEF-0082-planche-quatre-vues.png."
brief_0082_planche_quatre_vues,docs/forge/output/BRIEF-0082-planche-quatre-vues.png,render,"asset-forge (Blender 4.5.11, Cycles CPU, cameras orthographiques + composition numpy)",,asset-forge (Claude),proprietary-internal,2026-08-25,docs/forge/briefs/BRIEF-0082-noyau-interieur-passerelle-reacteur.md,,"Planche de recette de core_interior.glb (BRIEF-0082), 1800 x 1240, 96 echantillons, fond spatial du jeu 070A12, view_transform Standard (AgX desaturerait les hautes lumieres et fausserait la mesure R-G dans le sens flatteur). Produite par le meme script que l asset : blender45 -b -P tools/blender/build_core_interior.py -- --plate. Quatre vues. 1/ DESSUS orthographique, la lecture du jeu, portant l ecart R-G mesure. 2/ TROIS QUARTS, le devers des parois et la profondeur de la cavite. 3/ COUPES, deux bandes empilees (plan Godot Z = 0 puis plan Godot X = 0), obtenues par clip_start sur camera orthographique — en orthographique clip_start EST le plan de coupe. 4/ DESSUS AVEC LE SPECTER-9 A L ECHELLE : cinq exemplaires du .glb REEL du chasseur (assets/imported/models/ships/specter_9.glb, 1.752 x 0.647 x 2.460 m, sept maillages joints puis clones), poses sur Entry_Point, sur la travee d entree, au ras du reacteur, au large et contre la paroi tribord. C est la vue qui prouve l echelle, et c est elle qui aurait attrape les anneaux de 30 cm de la coque du boss ; aucune maquette de substitution n est utilisee. Les legendes sont CALCULEES a partir des constantes du script et de la largeur mesuree du chasseur, jamais recopiees (deux d entre elles etaient deja fausses apres un elargissement de travee, avant d etre rendues dynamiques). La planche porte aussi la mesure de contraste : masques d objets obtenus par un second rendu a materiaux d emission plats (rouge = Reactor, vert = Floor + Rim_*, bleu = travees exclues), filter_size 0.01 pour des bords francs, images relues en sRGB brut (colorspace Non-Color). Creation originale ; aucun element de licence tierce."
```

⚠️ **Rappel LFS** : `.gitattributes` route déjà `*.glb` et `*.png` vers Git LFS. Les deux binaires
livrés (`core_interior.glb`, `BRIEF-0082-planche-quatre-vues.png`) doivent y passer.
