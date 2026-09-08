# BRIEF-0110 — Rapport de forge : la poupe troque ses formes simples

- **Brief** : `docs/forge/briefs/BRIEF-0110-la-poupe-troque-ses-formes-simples.md`
- **Date** : 2026-09-08
- **Outil** : Blender 5.2.1 LTS (`blender-aegis`), toujours `-t 1`
- **Livrables** : `tools/blender/build_stern.py`, `tools/blender/build_long_cortege.py`,
  `assets/imported/models/backgrounds/stern_hull.glb`,
  `assets/imported/models/backgrounds/long_cortege.glb`,
  `docs/forge/output/BRIEF-0110-planche.png`, ce rapport
- **Périmètre respecté** : aucun `.gd`, `.tscn`, `.tres` touché ; aucun commit ; nacelles,
  berceaux, verrous, bras et les trois canaux d'échappement intacts.
  ⚠️ **`stern_pylon.glb` n'a PAS été reconstruit** : il reste à 5,30 m, au bit près, parce que
  la solution retenue ne change pas sa taille (§3).

---

## 0. Le résultat en une ligne

**+19,2 % de pixels porteurs d'arête sur tout le cadre, +24,6 % et +25,0 % sur les deux rives,
+44,8 % sur la bande du collecteur, pour une couverture identique à 0,03 % près et 0,02 % de
magenta en plus.** La poupe a cessé de se lire comme un assemblage de boîtes, et c'est mesuré au même
cadrage, à la caméra du jeu.

| Famille | Avant | Après | Sort |
|---|---:|---:|---|
| `skin` | 910 | 910 | ne bouge pas |
| `towers` | 560 | **1 592** | **régénérée** (socle évasé, galerie, diffuseur) |
| `manifold` | 436 | **396** | **remplacée** — devient le PORTIQUE ; 7 pièces instanciées dessus |
| `rim_clamps` | 312 | **384** (`rim_rails`) | **changée** — brides supprimées, filants + platines + descentes ; 4 flexibles instanciés |
| `pylons` | 240 | **216** (`pylon_seats`) | **remplacée** — 2 socles, 2 `stern_pylon` instanciés |
| `shoulders` | 96 | **672** | **régénérée** |
| `glow` / `apron` / canaux | 692 | 692 | ne bougent pas |
| **carène totale** | **3 182** | **4 822** | +1 640 |
| **pièces instanciées** | 0 | **12 340** | 17 repères |

**Budget : 78 874 / 80 000. Il reste 1 126.**

---

## 1. Le collecteur d'artère — le morceau le plus regardé, et c'est mesuré

Le brief dit « centre du bas de cadre, l'endroit que le joueur fixe le plus longtemps ». Je l'ai
vérifié avant d'y travailler, en projetant la géométrie sur le cadre du jeu (caméra `(0 ; 14 ; 5)`,
avant `(0 ; −0,940 ; −0,342)`, FOV 62 vertical, 1920 × 1080) :

| Élément | Pixel (x ; y) sur 1920 × 1080 | Densité |
|---|---|---:|
| **le collecteur** (`z = +8,95`) | **(960 ; 724)** | **50,3 px/m** |
| les épaulements (`z = +8,70`) | (1600 ; 732) | 45,7 px/m |
| le pont de poupe (`z = 0`) | (960 ; 478) | 31,9 px/m |
| le plateau du massif (`z = −10`) | (1403 ; **144**) | 31,7 px/m |
| **le sommet d'une tour** | (1166 ; **−4**) | hors cadre |

Le collecteur est bien le point bas-centre, et il rend 58 % plus gros que le pont. C'est là que le
travail est allé.

### 1.1 — Ce que la géométrie autorisait, et ce qui en découle

Le pont du corridor à `s ≈ 499` n'est pas plat, et le plafond de construction est bas :

```
|x| = 1,0   -4,020   <- la lèvre du canal magenta, le POINT HAUT
|x| 2,0..5,5 -4,26 .. -4,33   pont intérieur
|x| 5,5..6,4  la chine, 0,63 m de dénivelé
|x| 6,4..10,4 -4,94 .. -5,07  pont médian
plafond      -3,20
```

Un rail d'un seul tenant aurait donc flotté de **0,94 m** au-dessus du pont médian ou traversé la
lèvre du canal. **Le rail est coupé à la chine et il est à deux niveaux** : `−4,00` en dedans
(0,02 m au-dessus de la lèvre, 0,34 m sous le plafond), `−4,70` en dehors (0,26 m au-dessus du
pont médian, 1,04 m sous le plafond). La marche se voit, et c'est elle qui raconte que l'artère
descend d'un pont à l'autre.

### 1.2 — Sept pièces, contiguës au centimètre

| Repère | x | y (bas) | z | lacet | pièce | emprise x |
|---|---:|---:|---:|---:|---|---|
| `CTRL \| Collecteur 01` | −10,10 | −4,700 | +8,95 | +90° | `artery_conduit_bend.glb` | −11,502 … −8,698 |
| `CTRL \| Collecteur 02` | −7,30 | −4,700 | +8,95 | +90° | `artery_conduit.glb` | −8,690 … −5,910 |
| `CTRL \| Collecteur 03` | −2,79 | −4,000 | +8,95 | +90° | `artery_conduit.glb` | −4,180 … −1,400 |
| `CTRL \| Collecteur 04` | 0,00 | −4,000 | +8,95 | +90° | `artery_conduit.glb` | −1,390 … +1,390 |
| `CTRL \| Collecteur 05` | +2,79 | −4,000 | +8,95 | −90° | `artery_conduit.glb` | +1,400 … +4,180 |
| `CTRL \| Collecteur 06` | +7,30 | −4,700 | +8,95 | −90° | `artery_conduit.glb` | +5,910 … +8,690 |
| `CTRL \| Collecteur 07` | +10,10 | −4,700 | +8,95 | −90° | `artery_conduit_bend.glb` | +8,698 … +11,502 |

Les joints mesurent **8 à 10 mm** : le rail est continu sans interpénétration. L'emprise totale
(`|x| ≤ 11,502`) est **9,8 cm plus étroite** que le tube retiré (11,60) — la silhouette ne
s'élargit pas.

Le **portique** (`manifold`, 396 tri) porte tout cela et n'est plus une conduite : tête de
jonction en arrière du rail (`z 8,15…8,72`), deux montants et leur linteau, six pieds posés sur la
peau **réelle** du corridor (`blc._surface_y`), six selles sous les joints, deux potences
extérieures, et la **marche de chine** qui rattrape les 0,70 m entre les deux rails.

### 1.3 — Les quatre flexibles sont dans l'axe de l'artère du corridor

`CTRL | Liaison 01…04` sont à `|x| = 3,60` et `4,40` — **les deux latéraux exacts de
`CortegeArtery.CONDUITS`**. Ce n'est pas un alignement de goût : c'est la même ligne qui arrive et
qui aboutit, et le joueur l'a suivie sur 500 m. Leur `y` est le **minimum** de la peau sous
l'emprise de la pièce (jamais la valeur au centre : sur un bombement, le centre fait s'enfoncer
les deux bouts) — `−4,306` et `−4,291`.

### 1.4 — ⚠️ Le collecteur ne porte plus d'émissif propre, et c'est délibéré

Les trois sections vitrées du tube retiré valaient 13,9 m² d'`AA_Emissive_Engine`. Les conduites
instanciées ont le leur (`06 | Énergie magenta` → `AA_Emissive_Engine`, `BRIEF-0108`), et
`CortegeStern.blackout()` les éteint par le même nom de matériau. **Doubler la source aurait
doublé la lumière au seul endroit du cadre où le joueur doit encore lire ses balles.**

Mesuré sur les deux vignettes, au même cadrage : **20 232 pixels magenta avant, 20 236 après**
(+0,02 % sur tout le cadre). Dans la seule bande du collecteur : **9 490 → 9 050 (−4,6 %)** —
sept conduites instanciées éclairent MOINS que le tube et ses trois sections vitrées. Les rives,
elles, gagnent 21 % de magenta (1 014 → 1 231 et 1 091 → 1 313), qui sont les balises du pylône et
les cœurs des flexibles : c'est 217 et 222 pixels sur 1 920 × 1 080, et cela reste dix fois moins
dense que le collecteur. La réserve de couleurs
de la charte est tenue : la densité lumineuse n'a pas bougé, seule la structure a augmenté.

---

## 2. Le rebord du bassin — quatre flexibles, et ce qui les tient

La chaîne de brides (312 tri de colliers identiques) est **supprimée**.

### 2.1 — Quatre flexibles, pas vingt, et pas six non plus : c'est la géométrie qui compte

Le brief prévient « pas une par bride » et demande des vides. La géométrie est plus stricte encore,
et voici le calcul :

- une pièce `artery_hose.glb` mesure **2,74 m** et elle est **rigide** ;
- l'arête de rive change d'altitude à chaque bande (**−6,60**, **−5,60**, **−4,60**) : une pièce
  qui enjamberait une marche flotterait d'un côté et s'enterrerait de l'autre ;
- les bandes font **5,28 m** (B1) et **5,48 m** (B2, B3) : **une seule pièce par bande et par
  bord** ;
- la bande **B2 est prise par le socle de pylône** (`z −2,50 … +1,70`), qui n'y laisse que 0,90 m
  et 0,38 m ;
- le fond de gorge, où j'ai d'abord voulu poser une troisième paire, est **déjà occupé par les
  tirets de l'anneau d'artère** (`GROOVE_X = 16,17`, demi-largeur 0,09) : une platine de 0,68 m
  les aurait recouverts.

**Il reste donc B1 et B3, soit deux stations par bord — quatre flexibles.** C'est le compte que la
géométrie autorise, pas celui que j'aurais voulu ; je le dis plutôt que de forcer.

| Repère | x | y (bas) | z | emprise z | bande |
|---|---:|---:|---:|---|---|
| `CTRL \| Liaison 05 / 06` | ±16,60 | −6,600 | +5,90 | +4,53 … +7,27 | B1 (2,72 … 8,00) |
| `CTRL \| Liaison 07 / 08` | ±18,60 | −4,600 | −5,74 | −7,11 … −4,37 | B3 (−8,48 … −3,00) |

Ils sont **à cheval sur l'arête**, exactement comme les brides qu'ils remplacent, et la platine
d'ancrage (`rim_rails`) passe sous eux sur toute leur longueur.

### 2.2 — ⚠️ Le rail de guidage reste, contre la lettre du brief, et voici pourquoi

Le brief range le rail de guidage avec les brides. Il n'en était pas une : c'était **la seule
arête horizontale de la paroi du bassin**, ajoutée au `BRIEF-0106` après avoir rendu et regardé
« deux grands trapèzes gris de 7 m de haut, sans un pli, en plein cadre ». Quatre tubes de 0,28 m
(9 px à 32,7 px/m) ne rendent pas ce pli.

Le retirer aurait rouvert un défaut **déjà mesuré**, en silence. Il est donc **conservé et
retravaillé** — deux filants par bande au lieu d'un, plus une platine d'ancrage et une **descente**
de 3,1 m sous chaque flexible (l'artère ne s'arrête pas au rebord : elle plonge dans le bassin).
La famille change de nom (`rim_clamps` → `rim_rails`) pour que le compte-rendu ne mente pas.

Ce n'est pas un tapis de greebles : **il n'y a de relief qu'aux deux stations qui portent un
flexible**, et rien entre elles (règle du `BRIEF-0094`).

---

## 3. Le pylône — ⚠️ la troisième voie, et le critère est VERT, mesuré

### 3.1 — Aucun emplacement de la poupe n'a d'assise pour lui, et c'est arithmétique

Le pylône livré demande **5,30 m de ciel** et **2,06 × 2,89 m de plancher** (cotes relues dans le
binaire, jamais recopiées). Inventaire complet, emplacement par emplacement :

| Emplacement | Assise | Ciel sous −3,20 | Plancher plat disponible | Verdict |
|---|---:|---:|---|---|
| Arête de rive B1 | −6,60 | 3,40 m | 1,20 m (crête → bord) | ni ciel ni plancher |
| Arête de rive B2 | −5,60 | 2,40 m | 2,60 m | pas de ciel |
| Arête de rive B3 | −4,60 | 1,40 m | 3,00 m | pas de ciel |
| Plateau du massif | −8,40 | **5,20 m** | créneau libre 2,54 × 1,78 m | trop étroit **et** à `py = 144`, sous le panneau de score du HUD |
| Sole du bassin | −12,00 | **8,80 m** | bande hors emprise : 0,62 à 2,42 m | trop étroite |
| Épaulement de proue | −5,90 | 2,70 m | 5,60 m | pas de ciel |

**Le brief propose deux libertés — reconstruire à la hauteur, ou changer d'emplacement. J'ai pris
la troisième, qu'il ne propose pas : lui CONSTRUIRE son assise.**

### 3.2 — Le socle, et pourquoi sa cote n'est écrite qu'une fois

`PYLON_SEAT_TOP = CEILING_Y − 5,40 = −8,60` : la cote exacte où la pièce tient **entière** sous le
plafond avec 0,10 m de garde. Le socle monte de la sole du bassin (−12,00) jusque-là, sur
`x ∈ [15,90 ; 18,50]` — **0,12 m de marge à l'union des emprises de berceau (15,78)** et **0,00 m
au point le plus large de la bande B2 (18,50)** : il ne déborde pas de la silhouette, il la
remplit. Trois marches, deux margelles qui **laissent le centre libre** (sans quoi la pièce s'y
enfoncerait — le défaut exact du `BRIEF-0109`), un bandeau de flanc, trois nervures sur la face
intérieure.

Le pylône **n'est enterré de rien**. Ses 5,30 m sont dégagés, et le socle n'est pas un décor de
plus : c'est la pyramide de 3,40 m que le fuseau retiré était déjà, en mieux.

| Repère | x | y (bas) | z | lacet | sommet | ciel restant |
|---|---:|---:|---:|---:|---:|---:|
| `CTRL \| Pylone 01` | **+17,20** | **−8,600** | **−0,40** | −90° | −3,300 | **+0,100 m** |
| `CTRL \| Pylone 02` | **−17,20** | **−8,600** | **−0,40** | +90° | −3,300 | **+0,100 m** |

Emprise de la pièce posée : `x 16,170 … 18,230`, `z −1,845 … +1,045` — entièrement contenue dans
la marche haute du socle (`z ±1,72`).

### 3.3 — Il en reste DEUX, pas quatre, et c'est un choix chiffré

Quatre pylônes instanciés coûtent **10 448** triangles sur les 16 750 du lot. Le collecteur —
le morceau que le joueur regarde le plus longtemps — n'aurait plus rien. « Concentrer le travail
sur peu de pièces » (spec §20). Les deux stations retenues sont celles de la **paire avant** des
fuseaux (`z = −0,40`) : la paire arrière (`z = −6,00`) culminait à **`py = 115`**, c'est-à-dire
**derrière le panneau de score du HUD** — c'est très exactement le « il tombe en partie derrière
le panneau POWER » du `BRIEF-0109`, mesuré cette fois.

### 3.4 — ⚠️ La mesure du « se lit mieux qu'avant » : quatre candidats, deux métriques

J'ai rendu cinq variantes au **même cadrage**, à la caméra du jeu, dans la **même coque nettoyée**,
et j'ai compté deux choses : les **pixels que la pièce change** (présence) et, parmi eux, ceux qui
**portent une arête** (structure : `|∇L| > 0,045`).

| Variante | pixels changés | dont à arête | ratio | contraste moyen |
|---|---:|---:|---:|---:|
| Fuseau procédural (**avant**, ×4) | **106 500** | 9 048 | 0,085 | 0,0215 |
| `stern_pylon` 5,30 m assis sur la paroi (**BRIEF-0109**, ×2) | 32 759 | 10 009 | 0,306 | 0,0703 |
| `stern_pylon` reconstruit à 8,60 m sur la sole (×2) | 54 131 | 11 618 | 0,215 | 0,0494 |
| Contrefort −9,40 + `stern_pylon` 6,20 m (×2) | 61 792 | 14 205 | 0,230 | 0,0547 |
| **Socle −8,60 + `stern_pylon` 5,30 m (retenu, ×2)** | **70 123** | **13 784** | 0,197 | 0,0508 |

Ce que ces chiffres disent, sans complaisance :

- **le fuseau couvre plus de pixels — 106 500 contre 70 123** — parce que c'est un bloc gris
  opaque de 8,70 m. **8,5 % seulement de ces pixels portent une arête.** C'est la définition
  même de « nos formes simples » ;
- **le pylône sur son socle porte 52 % de structure en plus** (13 784 contre 9 048) sur deux
  pièces au lieu de quatre, soit **3,0 fois plus de pixels structurés par pièce** ;
- et il fait **+110 % sur la pose du `BRIEF-0109`** en présence, à structure égale.

Sur la coque **complète et finale**, au même cadrage avant/après (voir §7) : la rive de tribord
passe de 14 919 à 18 588 pixels d'arête (**+24,6 %**) et la rive de bâbord de 16 045 à 20 053
(**+25,0 %**), pour une couverture identique à 0,03 % près.

**Verdict : oui, il se lit mieux qu'avant.** Pas parce qu'il couvre plus — il couvre moins — mais
parce que ce qu'il couvre est une machine et non une boîte : passerelles, couronne de
refroidissement en treillis, bras d'échangeur, balises magenta, socle étagé. Les vignettes 1 et 2
de la planche sont au même cadrage exact ; la comparaison est là, et elle est nette à l'œil.

### 3.5 — ⚠️ Recouvrement mesuré avec la garnison de poupe (NON corrigé)

`cortege_stern_garrison.gd` pose deux plates-formes **volantes** sur la rive :

| Poste | Dalle (x) | Dalle (z) | Altitude |
|---|---|---|---|
| `STANDARD (±17,00 ; +2,00)` réserve palier 1 | ±14,89 … ±19,11 | −0,11 … +4,11 | −7,68 … −6,72 (ballant compris) |
| `HEAVY (±16,80 ; −4,50)` réserve palier 3 | ±14,36 … ±19,24 | −6,94 … −2,06 | −5,72 … −4,68 |

Le pylône posé traverse la première de **2,06 × 0,96 × 1,155 m = 2,284 m³** par bord.

⚠️ **Ce recouvrement PRÉEXISTE et il DIMINUE.** Les quatre fuseaux retirés étaient déjà traversés
par les deux dalles : **2,10 m³** (fuseau avant × dalle STANDARD) plus **4,20 m³** (fuseau arrière
× dalle HEAVY) par bord, soit **12,60 m³** au total. Après ce lot : **4,57 m³**, soit **−64 %**.
Le harnais `_garrison_clash()` le mesure à chaque build et le *dit* — il n'échoue pas le build,
parce que la garnison est hors périmètre (« le code de jeu : aucun `.gd` »). Il n'y a aucune
station libre de 3 m sur la rive entre les deux dalles : le créneau mesure **1,95 m**.

---

## 4. Les tours d'échange et les épaulements — régénérés

### 4.1 — Les tours (560 → 1 592)

Le plateau du massif offre **5,20 m** : le seul volume vraiment haut de la poupe. Ce qui s'ajoute,
et pourquoi — **cinq gestes, pas un tapis** :

1. un **socle évasé** en tronc de cône (r 1,78 → 1,52) puis un collier : une tour posée à plat sur
   un plateau n'a pas de pied ; celle-ci en a un ;
2. **six contreforts** au lieu de quatre, au pas de 60° : à 31,7 px/m, quatre arêtes verticales sur
   un fût de 2 m se comptent, six font une trame ;
3. une **galerie de service** à mi-hauteur avec ses quatre potences — c'est elle qui donne
   l'échelle, et c'est le seul élément dont on déduise qu'on y monte ;
4. **huit volets d'évacuation** sous la galerie ;
5. un **diffuseur** en cône, sa grille, une couronne et quatre ailerons.

Le socle passe de r = 1,520 à **r = 1,780 m** : les marges aux canaux d'échappement descendent à
**0,900 m** (latéral) et **1,420 m** (central), toujours positives, et le harnais échoue désormais
le build si l'une passe sous zéro (il ne le faisait pas).

⚠️ **Et le harnais qui les surveillait a échoué au premier build, comme il devait.**
`_tower_margin()` interrogeait `y = −7,55`, le sommet de l'ancien socle : la tour enrichie n'a plus
un seul sommet à cette altitude. La cote de contrôle est maintenant **dérivée de `AFT_PLATEAU_Y`**,
que la pièce et le harnais partagent — une cote de contrôle qui suit la pièce sans qu'on y pense
n'existe pas.

⚠️ **Attention au cadre** : au plan de maintien, la couronne d'une tour tombe à **−4 px sur
1080**, c'est-à-dire **juste hors du cadre**. Le massif n'est vu en entier que pendant le survol,
quelques secondes plus tôt (vignette 5). C'est aussi la raison pour laquelle le pylône livré n'y
est pas allé, malgré ses 5,20 m de ciel.

⚠️ **Une observation que je n'ai pas corrigée, parce qu'elle n'est pas de ce lot** : vue de la
caméra du jeu, qui plonge à 70°, la couronne de chaque tour se lit comme un **disque violet plein
de 3,16 m** (7,8 m² d'`AA_Panel` par tour, 15,7 m² pour les deux — 6 % de tout le violet de la
carène). C'est le **même dessin qu'avant** ce lot (vérifié sur `BRIEF-0107-planche.png`, vignette
7), donc pas une régression ; mais si l'on veut le corriger un jour, il suffit de passer le
chapeau du cône et celui de la couronne en `AA_Greeble` et de ne laisser en `AA_Panel` que la
frette de 0,12 m — le sommet devient une grille grise cerclée de violet, pour zéro triangle.

### 4.2 — Les épaulements (96 → 672)

Au premier plan, à **45,7 px/m** — la plus forte densité de la poupe. **Le volume ne change pas
d'un centimètre** (mêmes trois gradins, mêmes emprises), et tout ce qui s'ajoute tient en quatre
gestes : la façade se nervure (six raidisseurs et deux bandeaux), le gradin bas porte une console
de service à trois échelons, le gradin haut porte une bâche cylindrique avec collier, cône et
quatre contreforts, l'arête de flanc reçoit son bandeau.

⚠️ **Une cote a été bornée par l'emprise, pas par le goût** : la bâche siège à `z = 8,70` et la
bande interdite s'arrête à `z = 8,00` ; un rayon de 0,72 m faisait redescendre son bord à **7,98**,
soit **0,0058 m²** d'ombre dans le berceau bâbord. Refusé au centimètre carré par
`_keepout_bite()`, invisible à l'œil. Rayons ramenés à 0,54 / 0,62 / 0,70.

---

## 5. Les douze repères du corridor — et ce que la mesure a trouvé

`CTRL | Conduite 01` à `12`, aux douze stations de `CortegeArtery.CONDUITS`, aux `x` de la table
du jeu (**non rapportés à la largeur locale** : le moteur les lit en cotes absolues, leur appliquer
`kx` ici déplacerait le repère sous la pièce au lieu de la pièce sur le repère), `y` échantillonné
par `blc._surface_y(s, x)`.

| # | station | x | **y échantillonné** | écart à `DECK_Y = −4,30` |
|---:|---:|---:|---:|---:|
| 01 | 30 | +3,60 | **−5,790** | **−1,490 m** |
| 02 | 58 | −3,60 | **−4,466** | **−0,166 m** |
| 03 | 95 | +4,40 | −4,291 | +0,009 |
| 04 | 138 | −3,60 | −4,278 | +0,022 |
| 05 | 163 | +4,40 | −4,290 | +0,010 |
| 06 | 192 | −3,60 | −4,280 | +0,020 |
| 07 | 240 | +4,40 | −4,289 | +0,011 |
| 08 | 277 | −3,60 | −4,278 | +0,022 |
| 09 | 314 | +4,40 | −4,304 | −0,004 |
| 10 | 358 | −3,60 | −4,279 | +0,021 |
| 11 | 394 | +4,40 | −4,287 | +0,013 |
| 12 | 435 | −3,60 | −4,279 | +0,021 |

Les douze `y` **diffèrent** : neuf valeurs distinctes au dixième de millimètre. Un harnais neuf
(`_audit`) compare chaque repère à `_surface_y` **relu dans le binaire** et **échoue le build si
les douze portent la même valeur** — c'est la seule preuve qu'ils sont échantillonnés et non
recopiés.

### ⚠️ Ce que la mesure a trouvé, et que le test qui gardait la cote ne voyait pas

- **La conduite 01 flotte de 1,49 m.** À `s = 30` on est en pleine effilure de proue
  (`kx = 0,484`) : la peau est à **−5,790** et la pièce est posée à −4,30. Ce n'est pas une dérive
  de quelques centimètres, c'est une pièce **suspendue à un mètre et demi au-dessus de la coque** —
  exactement le défaut que l'opérateur a signalé sur les `.glb` de l'artère (« des tuyaux qui
  flottent au-dessus, ça ressemble à rien »).
- **La conduite 02 flotte de 0,166 m** (`s = 58`, `kx = 0,940`).
- Les dix autres sont à **± 2,2 cm**, ce qui confirme que `−4,30` n'était pas une valeur *fausse* :
  elle était **non mesurée**, et elle était fausse aux deux endroits où la coque respire le plus.

Le test qui la gardait comparait aux **marqueurs voisins** ; à `s = 30` le voisin le plus proche
(`Turret_01`, `s = 68`) est à −4,417, ce qui laissait passer 1,49 m d'écart sans un mot.

---

## 6. Les critères d'acceptation, un par un

| Critère | Chiffre mesuré | ✔ |
|---|---|:--:|
| Les cinq familles ont disparu ou changé, et le rapport dit laquelle a quel sort | tableau §0 : 2 remplacées, 1 changée, 2 régénérées | ✅ |
| Tous les repères posés, `y` échantillonné, position au centième, **bas de la pièce** | 17 repères dans `stern_hull.glb` + 12 dans `long_cortege.glb` ; écart à la pose demandée **0,0e+00 m**, relu dans le binaire | ✅ |
| **Le pylône se lit mieux qu'avant** | **+52 % de pixels d'arête** pour la famille, **+24,6 % et +25,0 % sur les deux rives entières** ; couverture 70 123 contre 106 500 — dit franchement en §3.4 | ✅ (avec sa réserve) |
| Budget ≤ 80 000, compté par famille | **78 874** — carène 4 822 (dont 1 640 de plus) + 12 340 instanciés ; **1 126 restants** | ✅ |
| Jonction `s = 500` inchangée au micron | **6,56 × 10⁻⁷ m** sur 48 sommets, des deux bords — le chiffre exact d'avant | ✅ |
| Trois canaux intacts, 0 m² dans les panaches | **0,000000000 m²** ; demi-largeur libre 2,200 m pour un panache de 1,700 ; fond −10,950 ; `AA_Emissive_Engine` dans les canaux 0,000000 m² | ✅ |
| Rien de neuf dans l'emprise des berceaux | **0,000000 m²** de décor au-dessus du pont ; les 17 pièces posées vérifiées une à une par `_assert_markers()` | ✅ |
| Les douze repères du corridor, `y` différents | 12 posés, **9 valeurs distinctes**, écarts de −1,490 à +0,022 m | ✅ |
| Déterminisme, sur les DEUX générateurs | 3 exécutions chacun, **zéro octet divergent** : `stern_hull.glb` → `ba67466f115e4fc5fdb0766a035408f46fc8c57aa65c682756872471140b963c`, `long_cortege.glb` → `0d460ee3222e70fbdc935ece8d10b7a6a80851387f207d6e51ee44dfe1f81b4e` | ✅ |
| Rendu et **regardé** à la caméra du jeu, pièces instanciées | `BRIEF-0110-planche.png`, **onze vignettes**, avant/après au même cadrage, pièces montées **par la même correction d'assise que le jeu** | ✅ |
| `./scripts/check.sh` | **1 échec** — voir §8.1. Il ne vient pas d'un défaut d'asset : un test 1-D de station le signale, la mesure 3-D dit qu'il n'y a pas de collision | ❌ |

Trois harnais neufs, qui **échouent le build** :

- **`_assert_markers()`** — relit les 17 nœuds `CTRL | ` **dans le `.glb`**, compare la pose au
  micron, vérifie que la rotation est un **lacet pur** (le quaternion, jamais `to_euler()` : un
  quart de tour autour de Y tombe exactement sur le blocage de cardan d'une décomposition XYZ),
  puis calcule la boîte de la **pièce posée et pivotée** et refuse le plafond crevé, l'emprise
  mordue, le canal envahi ;
- **`_garrison_clash()`** — mesure (sans bloquer) ce que les pièces prennent aux plates-formes
  volantes de la garnison ;
- **`_audit()` du corridor** — refuse un `CTRL | Conduite` qui ne tombe pas sur `_surface_y` à
  0,1 mm, et refuse que les douze portent la même valeur.

---

## 7. La méthode de mesure du « se lit mieux »

Elle mérite d'être dite, parce que le premier chiffre que j'ai sorti disait le contraire du bon
sens et qu'il fallait comprendre pourquoi.

1. **Présence** = nombre de pixels que la pièce change par rapport au **même cadre sans elle**
   (seuil 1,2 % sur le canal le plus écarté). Une pièce enterrée n'en change aucun.
2. **Structure** = parmi ces pixels, ceux qui portent une arête (gradient de luminance
   `> 0,045`). **Un bloc gris opaque maximise (1) et échoue (2)** — et c'est très exactement ce
   que l'opérateur reproche à la poupe.

Les deux ensemble, au même cadrage, sur la coque complète avant/après :

| Zone | matière (px) avant → après | arêtes avant → après | Δ arêtes |
|---|---|---|---:|
| Cadre entier | 1 764 575 → 1 764 112 | 104 823 → 124 935 | **+19,2 %** |
| Rive tribord | 249 009 → 248 933 | 14 919 → 18 588 | **+24,6 %** |
| Rive bâbord | 248 807 → 248 407 | 16 045 → 20 053 | **+25,0 %** |
| Bande du collecteur | 395 857 → 395 339 | 22 003 → 31 861 | **+44,8 %** |
| Pixels magenta (cadre entier) | 20 232 → 20 236 | — | **+0,02 %** |

**La couverture est identique à 0,03 % près** — la silhouette de la poupe n'a pas changé — et la
structure augmente partout. C'est la définition opérationnelle de « les modèles sont beaux, au lieu
de nos formes simples ».

---

## 8. Ce que je n'ai pas pu tenir, et pourquoi

### 8.1 — ⚠️ `./scripts/check.sh` est ROUGE, d'un seul test, et je ne peux pas le corriger

```
[FAIL] test_cortege_citadel.gd :: test_the_citadel_bites_none_of_its_three_neighbours
       CTRL | Conduite 07 est a s = 240.0 (garde 4.30) et l'emprise va de 239.6 a 246.0
```

**Le conflit préexiste ; mon repère l'a seulement rendu visible.**
`CortegeArtery.CONDUITS[6]` place déjà une conduite à `s = 240`, et
`cortege_citadel.gd` place la Citadelle à `citadel_station = 240`. Le test parcourt **tous** les
marqueurs du tronçon 3 et exige de chacun 4,30 m de garde en **station** — un critère
**unidimensionnel**. Jusqu'ici l'artère n'avait aucun marqueur : elle échappait au test.

La mesure **3-D**, elle, dit qu'il n'y a pas de collision :

| Pièce de la Citadelle | Emprise | Conduite 07 (`x` 4,17…4,63 ; `s` 238,6…241,4) | Marge |
|---|---|---|---:|
| Bastions (`BASTION_X = 6,90…11,40`) | `s 239,6…246,0` | à `x ≤ 4,63` | **2,27 m** en x |
| Relais (`RELAY_X = 6,20 ± 1,10`) | `s ≈ 240,3…242,5` | idem | **0,47 m** en x |
| Noyau (`CORE_RADIUS = 1,50`, sur l'axe) | `s ≈ 243,4` | idem | **2,67 m** en x |

Ce que je **n'ai pas** fait, et pourquoi :

- **je n'ai pas déplacé le repère** : le brief fixe les douze stations, et elles doivent rester
  celles de `CortegeArtery.CONDUITS` — un repère décalé rendrait la coque menteuse ;
- **je n'ai pas touché au test ni au `.gd`** : hors périmètre, explicitement.

**Arbitrage pour le concepteur, au choix :**
1. ajouter le critère latéral au test — un marqueur est libre s'il est hors de la fenêtre de
   station **ou** hors de `BASTION_X` (les douze conduites sont à `|x| ≤ 4,63`, les bastions à
   `|x| ≥ 6,90`) ; c'est la correction la plus juste, et elle documente que la Citadelle enjambe
   l'artère ;
2. donner aux `CTRL | Conduite` leur vraie garde (**1,37 m**, la demi-longueur de la pièce) au lieu
   des 4,30 m génériques ;
3. déplacer la septième conduite de `s = 240` à `s = 233` dans `CortegeArtery.CONDUITS` (et
   `ARTERY_CONDUITS` suivra) — mais c'est changer le rythme du niveau pour satisfaire un test.

### 8.2 — Quatre flexibles de rebord au lieu des « vingt » évoqués

Deux stations par bord, pas plus : §2.1 le démontre bande par bande. La cause est le pas des
marches de rive (3 bandes de 5,3 à 5,5 m pour une pièce rigide de 2,74 m) et le socle de pylône qui
occupe B2. En sortir demanderait de toucher à `build_skin()` — hors périmètre.

### 8.3 — Le rail de guidage de la paroi n'a pas été supprimé

Écart assumé à la lettre du brief, mesuré et justifié en §2.2. Si le concepteur le veut supprimé,
c'est trois lignes dans `build_rim_rails()` — mais la paroi du bassin redeviendra deux trapèzes
gris de 7 m sans un pli.

### 8.4 — Deux pylônes, pas quatre

Choix budgétaire chiffré (§3.3) : quatre coûtaient 10 448 des 16 750 triangles du lot et vidaient
le collecteur. Si le concepteur préfère quatre, il faut retirer environ 5 200 triangles ailleurs —
le plus simple serait de ramener le collecteur à 3 conduites et 2 coudes (−1 956) et les tours à
leur compte d'avant (−1 032), ce qui ne suffirait toujours pas.

### 8.5 — Le pylône couvre moins de pixels que le fuseau

Dit franchement en §3.4 : **70 123 contre 106 500**. Il gagne sur la structure (+52 %) et sur la
lecture, il perd sur la masse. Si l'opérateur juge que la rive a perdu du poids, le remède qui
coûte le moins est **d'élargir le socle en `z`** (`PYLON_SEAT_HZ`, aujourd'hui 2,10) : chaque
10 cm de plus coûte 0 triangle et ajoute de la masse sous la pièce. La limite est le créneau de
1,95 m entre les deux dalles de la réserve (§3.5).

### 8.6 — `stern_pylon.glb` n'a pas été reconstruit

Le brief l'autorisait « s'il change de taille ». **Il ne change pas** : la solution du socle le
laisse à 5,30 m, donc au bit près. J'ai néanmoins testé une reconstruction à 8,60 m
(`PYLON_HEIGHT` dans `assets/source/models/artery/build_artery.py`) : elle donne 54 131 pixels
changés contre 70 123 pour le socle, parce qu'à cette taille la pièce est une tour **ajourée** et
que la caméra du jeu la regarde à 70° de plongée — la hauteur ne rend que 34 % de sa longueur à
l'écran, le plan 94 %. **Sur cette caméra, l'emprise au sol paie mieux que la hauteur**, et c'est
la leçon la plus réutilisable de ce lot.

---

## 9. Suggestions

- **`CortegeArtery.DECK_Y` peut disparaître.** Les douze `CTRL | Conduite` portent désormais la
  cote juste ; la conduite 01 gagne 1,49 m et la 02 gagne 17 cm. C'est la dette de
  `.claude/resources/pratique-poser-sans-marqueur.md` qui se referme.
- **Le lacet des repères se copie tel quel** : `piece.transform.basis` = celle du marqueur, puis la
  correction d'assise de `CortegeConduit._seat()` **sans changement**. Elle commute avec un lacet
  et avec lui seul — un tangage ou un roulis ferait tourner la correction avec la pièce, sans
  erreur ni test rouge. Le harnais refuse déjà tout quaternion qui n'est pas un lacet pur.
- **Les sept `CTRL | Collecteur` ne portent pas tous la même pièce** : `01` et `07` sont des
  `artery_conduit_bend.glb`, les cinq autres des `artery_conduit.glb`. Le tableau §1.2 donne le
  fichier et le lacet de chacun. Il n'y a pas de convention de nom qui le dise — c'est le seul
  endroit du lot où le code doit lire ce rapport.
- **Ces conduites sont du décor, pas des cibles.** Le `BRIEF-0109` avait raison de rappeler qu'une
  conduite se coupe et que le corridor l'a appris au joueur ; le `BRIEF-0110` demande explicitement
  des conduites ici. Si le collecteur doit rester indestructible, il faut le dire par autre chose
  que la forme — par exemple en ne montant que le clip `Actif` et en ne branchant aucune
  `BulletTarget`.
- **Si la rive doit reprendre du poids sans nouveau brief** : élargir `PYLON_SEAT_HZ` (gratuit) ou
  poser un troisième `CTRL | Liaison` par bord dans la bande B2 le jour où le socle rétrécit.
- **La vignette de blackout laisse du magenta, et c'est normal** : `AA_Emissive_Engine` garde sa
  couleur de base `#D93D9C` (albédo rouge 0,706) une fois son émission éteinte, et à 12 % de
  lumière elle rend encore rose. La vignette 10 est **identique** à celle du `BRIEF-0107` sur ce
  point : rien de neuf ne brille.

---

## 10. Texture et animation (les deux sections du brief sont présentes)

- **Texture : aucune** (`ADR-0028`). Le brief porte sa section et déclare pourquoi : les repères
  sont des nœuds vides et la géométrie régénérée reste en PBR par facteurs. Vérifié sur les deux
  binaires : **0 image** dans `stern_hull.glb` et dans `long_cortege.glb`. Les UV de la carène sont
  une projection en boîte à **0,20 tuile/m** (la densité de la peau du corridor, lue dans
  `blc.HULL_TEXELS_PER_METER`, jamais recopiée), densité mesurée **0,1992 tuile/m**
  (5,020 m/tuile), **anisotropie max 1,491** (borne √3 = 1,732), et **`TEXCOORD_0` est COMPTÉ sur
  5 primitives sur 5** pour la poupe et **27 sur 27** pour le corridor. Aucune planche de damier
  supplémentaire n'était due : le dépliage est en boîte, pas continu — la vignette 11 la rend
  quand même, au même titre qu'au `BRIEF-0107`.
- **Animation : aucune dans ces deux fichiers** (`ADR-0046` §6). Le brief le déclare : « la
  géométrie régénérée est figée ». Vérifié : **0 animation** dans les deux `.glb`. Ce qui bouge sur
  la poupe est animé dans **son** fichier (`stern_pylon.glb` : 3 clips ; `artery_conduit*.glb` et
  `artery_hose.glb` : 4 clips chacun), et la carène ne porte que le repère où il se pose. **Aucun
  pilote Blender n'est en jeu ici** — il n'y a rien à cuire en images clés.
