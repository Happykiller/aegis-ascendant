# BRIEF-0115 — Rapport de forge : Ambry devient un lieu

- **Brief** : `docs/forge/briefs/BRIEF-0115-ambry-sur-planche.md`
- **Planche de concept** (le contrat) : `assets/reference/concepts/ambry_concept_sheet_2026-09.png`
- **Planche de matières** (le contrat de slots) : `assets/reference/concepts/ambry_texture_atlas_2026-09.png`
- **Spécification écrite** : `docs/forge/concepts/AMBRY-ce-qu-on-doit-voir.md`
- **Date** : 2026-09-13 · **Outil** : Blender 5.2.1 LTS (`blender-aegis`), toujours `-t 1`
- **Livrables** : `tools/blender/build_long_cortege.py`,
  `assets/imported/models/backgrounds/long_cortege.glb`,
  `docs/forge/output/BRIEF-0115-planche.png`, ce rapport
- **Périmètre respecté** : aucun `.gd`, `.tscn`, `.tres` touché ; le complexe industriel du
  tronçon 5, la poupe et le reste du bordé sont inchangés ; aucun commit.

---

## 0. La réponse en une ligne

**Ambry n'est plus une plaque avec des boîtes dessus : c'est un village de sept bâtiments dont
aucun ne ressemble au voisin, aux fenêtres allumées, dont le sol a été arraché avec lui et dont
la soudure a coulé.** Rien n'a monté d'un millimètre — le sommet reste le mât, à `−3,200`, le
plafond de construction au millimètre.

| | BRIEF-0114 | BRIEF-0115 |
|---|---:|---:|
| Triangles d'Ambry | 3 168 | **5 300** (×1,67) |
| Slots propres à Ambry | 1 | **12** |
| Triangles d'Ambry sur un slot du **bordé** | **1 652** | **0** |
| Fenêtres allumées | **0** | **46** |
| Portes de 60 cm | 0 | **6** |
| Pièces posées de travers | 0 | **7** (1,9 à 2,9°) |
| Blocs de soubassement débordant des dalles | 0 | **24** |
| Coulures de métal fondu sur les colliers | 0 | **16** |
| Modules d'habitation | 4, identiques | **7, toutes cotes différentes** |
| Hauteur des modules au-dessus des dalles | 0,70 m (×4) | **0,30 à 1,00 m** |
| Sommet | −3,200 | **−3,200** (identique) |

---

## 1. Les quatre « À ÉVITER » de la planche, levés un par un

Le panneau était la grille d'acceptation. Voici les quatre, et ce qui les remplace.

### 1.1 « Boîtes identiques » → sept modules, et pas deux pareils

`AMBRY_MODULES` pose **sept volumes** dont aucun ne partage ni ses cotes, ni sa hauteur, ni son
toit. Un relais de quatre-vingts personnes se bâtit par ajouts sur quarante ans : la table est une
**chronologie**, pas du bruit.

| Module | Emprise (m) | Hauteur au-dessus des dalles | Devers | Toit |
|---|---|---:|---:|---|
| M1 | 2,18 × 2,80 | **0,86** | 0,0° | bac à parapet 3 côtés, 2 lanterneaux, échelle |
| M2 | 1,12 × 1,90 | **0,42** | **+2,6°** | bâche tendue de travers, en dévers, 4 amarres |
| M3 | 2,10 × 2,25 | **0,96** | **−2,2°** | **voûte** — cinq pans en berceau, verrière de faîte |
| M4 | 0,88 × 1,35 | **0,34** | 0,0° | trois caisses empilées, un touret de câble |
| M5 | 2,20 × 2,80 | **1,00** | **+1,9°** | quatre **panneaux solaires** inclinés |
| M6 | 1,68 × 2,10 | **0,74** | **−2,8°** | bac, 2 lanterneaux, **parabole** orientée |
| M7 | 1,65 × 1,45 | **0,30** | 0,0° | **cuve octogonale** et un évent |

M5, la plus haute, est calée pour que ses panneaux s'arrêtent à `−3,22` : **les 1,28 m de ciel sont
utilisés**, pas subis.

### 1.2 « Ailettes vertes » → la serre pousse au lieu de border

Le défaut nommé était exact : sept **arceaux verts de 97 cm de haut**, qui lisaient comme le
radiateur d'une machine. Ce qui est livré :

- les arceaux sont **ivoire** et **fins** — 9 cm, contre 16 cm de vert avant ;
- la verrière est un volume translucide **continu** sur son slot propre (`AA_Glass_Ambry`), sept
  travées de six pans d'arc, **entière, pas un carreau cassé** ;
- le vert est ce qu'il y a **dedans** : **cinq rangs de culture longitudinaux à cinq hauteurs
  différentes** (0,30 / 0,46 / 0,38 / 0,52 / 0,34 m) plus deux bacs transversaux, avec leurs
  sillons sombres entre eux.

Vérifié au rendu : sur la vignette de poupe et sur la vue de dessus, **on voit le vert à travers
le vitrage, et on voit qu'il est en rangs**. C'est ce que « ça pousse encore » demandait.

### 1.3 « Tout d'équerre » → le re-plombé est enfin dans la géométrie

La bible dit « rien de détruit, rien de volé, **tout rebâti légèrement de travers** », et le
générateur avait lu « remis d'aplomb ». **Sept pièces sont maintenant de travers**, et le Détail C
donne la fourchette : 2 à 3°.

| Pièce | Devers |
|---|---:|
| module M2 | **+2,6°** |
| module M3 | **−2,2°** |
| module M5 | **+1,9°** |
| module M6 | **−2,8°** |
| **la serre entière** | **+2,3°** (8,4 cm d'écart d'un bout à l'autre) |
| le pas d'appontage et son « H » | **+2,5°** |
| le socle du mât | **+2,9°** |
| la bâche de M2 | **+9,4° par rapport à son module**, qui est déjà de travers |
| les huit massifs de collier | **3,4 / 6,8 / 8,2 / 4,1°**, symétriques inversés fore/aft |

Et les trois signatures nommées par le Détail C :

- **passerelle décalée** : la passerelle qui enjambe la ruelle entre M3 et M5 tombe à **0,38 m à
  côté** de la porte qu'elle dessert. Parfaitement fixée, parfaitement inutile ;
- **main courante absurde** : la lisse intérieure borde un vide sur 17,5 m, puis **continue sur
  2,10 m** au-dessus d'une cour pleine et finit en l'air ;
- **pièce au mauvais endroit** : les trois plus bas modules (M2, M4, M7) n'ont pas de porte — ils
  ont une **trappe de service** plaquée sur une façade où personne ne peut entrer debout.

Rien ne dépasse 3° : **le malaise demande une seconde, pas zéro.**

### 1.4 « Aucune vie lisible » → l'inventaire, avec sa taille à l'écran

À 45,8 px/m. Tout est compté par le générateur (`stats["life"]`), pas affirmé.

| Objet | Nombre | Taille écran |
|---|---:|---|
| **fenêtres allumées** | **46** | lanterneaux 0,54 × 0,44 m = **25 × 20 px** ; bandeaux de façade 0,26 à 0,58 m |
| **portes** | 6 | 0,60 m = **27 px** |
| montants de garde-corps | 49 | 0,14 m = 6 px, reliés par **3 mains courantes continues** |
| blocs de roche arrachée | 24 | 0,68 à 1,90 m |
| coulures de métal fondu | 16 | 0,55 à 1,85 m de long |
| marquages de sol (le « H » + hachures de rive) | 15 | le H fait 1,45 × 1,05 m = **66 × 48 px** |
| taquets d'amarrage | 9 | 0,26 m = 12 px |
| rangs de culture | 7 | 0,40 × 3,80 m |
| caisses et conteneurs | 6 | 0,38 à 0,56 m, deux empilées |
| pièces de linge sur un fil | 6 | 0,30 à 0,38 m |
| panneaux solaires | 4 | 1,52 × 0,48 m, inclinés de 12° |
| haubans d'antenne | 4 | 3,2 m de portée en plan |
| cuves octogonales | 3 | 0,68 à 0,84 m de diamètre |
| échelles extérieures | 2 | 4 barreaux chacune |
| tourets de câble | 2 | 0,52 m |
| bâche tendue | 1 | 1,00 × 1,18 m |
| panneau peint à la main | 1 | 0,96 × 0,12 m |
| véhicule d'entretien | 1 | **1,60 × 0,88 m = 73 × 40 px**, garé de travers de 13° |

> ⚠️ **Le véhicule n'est pas sur le pas d'appontage, et c'est une correction faite AU RENDU.** Il y
> était garé au premier tirage, en plein milieu. Or le pas doit rester **vide** : c'est de là que
> Wren est parti deux semaines avant que tout se taise, et son vide **est** le sujet. Il est allé
> dans la cour ouverte par le recul de M3.

---

## 2. Les fenêtres allumées — `AA_Window_Ambry`, et la conséquence de jeu

**46 quads émissifs**, ambre chaud `#E4B54A` — l'or de la charte Helios Vanguard, lu dans
`ak.PALETTES`, jamais recopié à la main. `emissiveStrength = 1,2`, **posé dans le `.glb`**.

Elles sont placées **là où la caméra les voit**, et l'ordre suit la mesure du `BRIEF-0110` (à 70°
de plongée une face horizontale rend 94 % de sa surface, une verticale 34 %) :

| Emplacement | Nombre | Pourquoi là |
|---|---:|---|
| **lanterneaux de toiture** (4 en bac, 1 en faîte de voûte) | 5 | 94 % de rendement — trois fois ce que pèse une fenêtre de façade |
| bandeaux de face **avant** (normale +z, tournée vers la caméra) | 17 | le joueur arrive par là |
| bandeaux de face **inboard** (tournée vers x = 0, où est la caméra) | 17 | le bord qu'elle voit de face |
| **feux de seuil** au-dessus des quatre portes de module | 4 | ils nomment les portes, qui sinon ne seraient qu'un creux sombre |
| hublot du sas de la serre, deux fenêtres du local technique | 3 | les deux bâtiments qui ne sont pas des modules |
| **total** | **46** | |

⚠️ **Ce n'est pas `AA_Emissive_Engine`, et la conséquence est celle que le brief voulait.**
`CortegeSkin.apply()` ne connaît pas ce slot : il ne le réécrit pas, ne l'habille pas, et
`emissives_of()` ne le ramasse pas. **Au blackout final, les 85 conduits magenta du vaisseau
s'éteindront et les fenêtres d'Ambry resteront allumées.** Rien à câbler : la valeur du binaire est
celle du jeu, et c'est aussi celle que rend la planche — un seul chiffre, un seul endroit
(`AMBRY_WINDOW_ENERGY`).

Aire vue des fenêtres : **5,3 m²**, soit 0,03 % de l'aire vue du corridor. C'est peu, et c'est
exactement le bon ordre : elles doivent **ponctuer**, pas éclairer.

---

## 3. Le découpage en douze slots par nature (ajout du 2026-09-13)

### 3.1 Ce qui est livré, slot par slot — triangles et densité MESURÉE

Relevé sur le binaire, triangle par triangle, par `_audit()`. Aucune image, PBR par facteurs.

| Slot | Base (charte) | Fini m/r | Tri | Part | tuile/m min | moy | max | aniso | TEX-AMB | Ce qu'il porte |
|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| `AA_Hull_Ambry` | `#EDEAE3` Vanguard *hull* | 0,05 / 0,45 | 838 | 15,8 % | 0,675 | **0,700** | 0,700 | 1,04 | 01 | dalles de rive, murs, toits, parapets, pignons, socles |
| `AA_Tech_Ambry` | `#24252B` Vanguard *greeble* | 0,70 / 0,50 | 1 332 | 25,1 % | 0,445 | **0,699** | 0,700 | 1,57 | 02·11·17·18 | plateau, traverses, machinerie, conduits, mât, vergues, haubans, parabole, panneaux solaires |
| `AA_Deck_Ambry` | `#DDDCD2` Unisson *trim* | 0,30 / 0,65 | 1 406 | 26,5 % | 0,690 | **0,699** | 0,700 | 1,01 | 03·04 | la rue, caillebotis, passerelles, garde-corps, échelles, taquets, marquages de sol |
| `AA_Pad_Ambry` | `#141419` Unisson *greeble* | 0,15 / 0,78 | 12 | 0,2 % | 0,692 | **0,699** | 0,700 | 1,01 | 05 | le pas d'appontage |
| `AA_Weld_Ambry` | `#141419` Unisson *greeble* | 0,88 / 0,30 | 288 | 5,4 % | 0,691 | **0,699** | 0,700 | 1,01 | 06 | **les deux colliers et leurs coulures — à l'UNISSON** |
| `AA_Rock_Ambry` | `#24252B` Vanguard *greeble* | 0,00 / 0,92 | 428 | 8,1 % | 0,488 | **0,678** | 0,700 | 1,43 | 07 | le soubassement arraché |
| `AA_Glass_Ambry` | `#0A0910`, α 0,86, transm. 0,30 | 0,00 / 0,08 | 74 | 1,4 % | 0,611 | **0,677** | 0,700 | 1,15 | 08 | la verrière de la serre, le pare-brise du véhicule |
| `AA_Green_Ambry` | `#7C9E52` Unisson *marking* | 0,00 / 0,58 | 84 | 1,6 % | 0,695 | **0,700** | 0,700 | 1,01 | 09 | la végétation — le seul vert des 500 m |
| `AA_Window_Ambry` | `#E4B54A` Vanguard *trim* | 0,00 / 0,35 **+ ém. 1,2** | 552 | 10,4 % | 0,699 | **0,700** | 0,700 | 1,00 | 10 | les fenêtres éclairées |
| `AA_Cloth_Ambry` | `#DDDCD2` Unisson *trim* | 0,00 / 0,90 | 84 | 1,6 % | 0,629 | **0,694** | 0,700 | 1,11 | 12·15 | bâche, linge |
| `AA_Crate_Ambry` | `#24252B` Vanguard *greeble* | 0,25 / 0,62 | 72 | 1,4 % | 0,678 | **0,697** | 0,700 | 1,03 | 13 | caisses et conteneurs |
| `AA_Sign_Ambry` | `#24252B` Vanguard *greeble* | 0,10 / 0,65 | 130 | 2,5 % | 0,696 | **0,700** | 0,700 | 1,01 | 14·16 | portes, trappes, panneau peint |
| **TOTAL** | | | **5 300** | | **0,445** | **0,697** | **0,700** | **1,57** | | cible annoncée **0,700 tuile/m** = 1,43 m par tuile |

**Toutes les couleurs viennent de `ak.PALETTES`**, jamais d'un hex écrit à la main : si la charte
change, les slots changent avec elle. Deux slots peuvent partager une valeur — le fini les sépare
aujourd'hui, la carte les séparera tout à fait demain. **TEX-AMB-17 (panneaux solaires)** et
**TEX-AMB-18 (antenne/relais)** ont été **repliés sur `AA_Tech_Ambry`** : leur géométrie est
minuscule (cinq pièces) et leur matière est du métal technique sombre comme le reste. Si vous voulez
les habiller séparément, dites-le et je les sors — c'est une ligne.

### 3.2 ⚠️ Le défaut ouvert du `BRIEF-0114` est fermé, et il ne peut plus revenir

> **Triangles d'Ambry encore sur un slot du bordé : 0.**

Ils étaient **1 652 sur 3 364**. `CortegeSkin.apply()` choisit l'échelle d'UV **par nom de
matériau** ; toute face d'Ambry restée sur `AA_Greeble`, `AA_Hull`, `AA_Glass` ou
`AA_Marking_Red` recevait donc la carte du bordé à 0,200 tuile/m alors qu'Ambry est dépliée à
0,700 — **3,5 fois trop fine**, et le défaut est totalement silencieux : ni erreur d'import, ni
test rouge, il ne se serait vu qu'une fois les images générées, donc trop tard.

Deux harnais neufs, **bloquants**, sur le binaire :

1. tout triangle d'un slot d'Ambry **hors de l'emprise d'Ambry** échoue le build (l'ancien contrôle
   ne couvrait que `AA_Hull_Ambry`) ;
2. tout triangle **dans** l'emprise d'Ambry porté par un slot du **bordé** échoue le build. C'est le
   contrôle inverse, et c'est lui qui empêche le défaut de se réintroduire.

**Côté code, il ne reste donc plus rien à corriger pour l'échelle** : il suffira d'ajouter les onze
nouveaux noms à `CortegeSkin.SKINS` avec `AMBRY_UV_SCALE` quand les cartes existeront. La ligne
`var scale := AMBRY_UV_SCALE if name == &"AA_Hull_Ambry" else HULL_UV_SCALE` gagnerait à devenir un
test d'appartenance (`name.ends_with("_Ambry")`), mais c'est votre périmètre, pas le mien.

### 3.3 ⚠️ Deux slots du kit sont désormais VIDES, à dessein

`AA_Glass` et `AA_Marking_Red` **n'avaient qu'un seul client dans les 500 mètres : Ambry** — sa
verrière et le vert de sa serre. Maintenant que chaque nature d'Ambry a son slot, **plus rien du
Long Cortège n'est ni en verre ni en vert**. C'est le résultat cherché, pas un accident.

Ils restent **déclarés** sur le maillage (les index de slot ne bougent pas, ceux du kit non plus),
ils sont listés dans `EMPTY_ON_PURPOSE`, et **le build échoue si l'un d'eux reprend une face**.
L'exporteur glTF n'écrit que ce qui porte une primitive : le binaire compte donc **17 matériaux**
(5 du bordé + 12 d'Ambry) au lieu de 8.

### 3.4 ⚠️ Un atlas à îlots packés est impossible — confirmé, et voici pourquoi

Vous aviez raison et je le confirme sur le code : `ak.box_project_uv()` écrit
`uv = (coordonnée monde) × tuiles_par_mètre` **sans aucun packing**. Les `u` et `v` sortent de
`[0, 1]` (ici jusqu'à ±52 en `v`, la station étant en mètres), et **deux faces situées à 1,43 m
l'une de l'autre dans le monde retombent exactement sur le même point de la feuille**. Les îlots ne
se recouvrent pas « un peu » : ils sont **volontairement superposés**, c'est ce qui rend le
dépliage gratuit et déterministe.

Conséquences, et elles sont nettes :

- **une carte tuilée par slot fonctionne parfaitement** — c'est même le seul régime pour lequel ce
  dépliage a été écrit. Chaque image `ambry_<nature>_*.png` doit être **répétable (seamless)** et
  se lit à **1,43 m par tuile** ; elle se pose avec `uv1_scale = AMBRY_UV_SCALE (1.0)`, exactement
  comme `ambry_hull` aujourd'hui ;
- **un atlas à îlots packés est impossible sans reforger le dépliage** : il faudrait un
  `smart_project` ou un dépliage continu écrit à la main, plus un packing déterministe — et tout le
  contrat de densité de ce fichier (moyenne annoncée, borne √3, jonctions entières entre tronçons)
  serait à refaire ;
- **il n'y a rien à gagner à le faire ici.** Un atlas sert quand on veut une texture *unique* par
  objet ; ce que vous voulez est l'inverse — douze matières que l'on habille **séparément**. Les
  slots par nature donnent ça, et ils le donnent aujourd'hui.

Un seul point d'attention pour la génération : comme la projection est en **boîte**, une face
verticale et une face horizontale prennent leurs UV dans deux plans différents. **Une carte qui a un
« haut » et un « bas » (une porte dessinée, une signalétique orientée) ne se posera pas
correctement** — elle sortira tournée d'un quart de tour sur les faces dont l'axe dominant est
différent. `TEX-AMB-14` (signalétique) et `TEX-AMB-16` (portes) sont les deux natures concernées :
il faut les générer **sans orientation forte**, ou accepter que le motif tourne. Les dix autres
(tôle, roche, câbles, végétation, toile, caisses, verre…) sont isotropes et n'ont pas ce problème.

---

## 4. La greffe : une couture qui n'est jamais propre, et une roche qui déborde

### 4.1 La couture

C'est le canon de l'Unisson (`NULL_CHOIR.md`) : « la jonction entre la coque d'origine et ce qui a
poussé dessus **n'est jamais propre** ». La version précédente était trois massifs d'équerre à
brides régulières — une bride d'usine. Ce qui est livré, par collier :

- **quatre massifs** à quatre dévers différents (3,4 / 6,8 / 8,2 / 4,1°), de longueurs et de
  hauteurs différentes (`raft −0,06` à `raft +0,19`), qui **se chevauchent** ;
- **huit coulures** : des langues de métal fondu de 0,10 à 0,24 m de large et 0,55 à 1,85 m de long,
  chacune à son propre dévers, qui **ont coulé du collier sur les dalles claires** et s'y sont
  figées 2 à 5,5 cm au-dessus. **16 au total**, et ce sont elles qui se voient le plus : du sombre
  irrégulier mordant sur de l'ivoire droit.

Elles sont sur `AA_Weld_Ambry` : **elles appartiennent au vaisseau, pas à l'avant-poste**, et
c'est pour ça que ce slot est le seul dont la matière viendra de l'Unisson (TEX-AMB-06).

### 4.2 La roche — elle DÉBORDE, elle ne pend pas

Votre point 3 était la contrainte qui a décidé de sa forme, et c'est ma propre mesure du
`BRIEF-0113` : **à 70° de plongée, rien sous un radeau de 5,5 m n'est visible** — le rayon qui passe
par l'arête basse extérieure ressort au-delà de la zone de garde. De la roche suspendue sous la
dalle aurait été, une fois de plus, une idée non livrée.

Les **24 blocs** sont donc des penta- et hexagones irréguliers (aucune empreinte à quatre côtés,
aucune arête parallèle à une autre) qui **sortent de l'emprise des dalles** :

- en avant de `s = 446,5` et en arrière de `s = 473,5` — deux grappes, à la greffe et à la poupe ;
- en deçà de `x = 7,90` et au-delà de `x = 13,40` — une frange le long des deux rives, parce que
  **le radeau EST un morceau de sol arraché**, pas une plate-forme ;
- **9 d'entre eux montent au-dessus du plan des dalles** (jusqu'à `raft + 0,30`) : on n'a pas
  découpé proprement, on a pris le morceau.

Ils restent tous dans `AMBRY_KEEPOUT` (x 6,90..14,10 ; s 443,5..476,5), et le harnais de strays le
vérifie sur le binaire.

**C'est ce qui casse le rectangle.** Le grief « pas de forme » était mesurable : le contour d'Ambry
était un rectangle de 27 × 5,5 m. Il ne l'est plus — vignette 6 de la planche, à comparer à la
silhouette de la planche de concept.

### 4.3 Et le second accent de silhouette : les quatre haubans

Le mât est le seul accent vertical autorisé, et il touche `BUILD_CEILING_Y` au millimètre. Aucune
primitive de ce fichier ne savait écrire un câble oblique : `_strut()` est nouvelle. Les quatre
haubans partent de `−3,54` et rayonnent sur **3,2 m en plan** vers quatre plots ancrés dans les
dalles. À 70° de plongée, **c'est la seule figure non rectangulaire des 27 m**, et c'est ce qui rend
la quatrième zone lisible de loin.

---

## 5. Ce qui n'a pas monté d'un millimètre

Mesuré **sur le binaire produit**, pas sur l'intention.

| | Valeur |
|---|---:|
| mât d'antenne (le sommet d'Ambry) | **−3,200** |
| plafond de construction (règle A) | **−3,20** |
| panneaux solaires de M5 | −3,22 |
| parabole de M6 | −3,22 |
| verrière de faîte de M3 | −3,26 |
| parapet le plus haut | −3,34 |
| faîte de la serre | −3,55 |
| dessus des dalles (`AMBRY_RAFT_Y`) | −4,48 |
| fond de la rue | −4,62 |
| fond du plateau (`AMBRY_TRAY_Y`) | −4,78 |

`_assert_build_ceiling()` (bloquant, il lit le `.glb` produit, translation comprise) et le garde
local de `build_ambry()` passent tous deux. **Le ciel disponible est mieux utilisé qu'avant** : la
pièce la plus haute après le mât est passée de −3,53 à −3,22, et c'est un panneau solaire, pas un
accident.

---

## 6. Le bord avant, et la réplique de Lyra

> **Lu dans le binaire : `AA_Hull_Ambry` culmine à `z = −46,500` local sur `Section_05`
> (translation `−400`), soit `s = 446,500`.**

Exigé : `446,5 ± 1`. `./scripts/check.sh` : **ALL GREEN — 1 034 tests, 8 842 assertions, 0 échec,
0 erreur d'analyse**, dont `test_the_front_edge_of_ambry_is_read_from_the_hull` et
`test_the_ambry_line_waits_until_ambry_is_in_the_frame`.

C'est la contrainte qui a le plus pesé sur le plan. Ce qui l'ancre est la **première dalle de rive
extérieure**, dont le bord avant est à `s = 446,50` exactement. Tout ce qui déborde en avant — les
colliers, les coulures, la roche, la rue — est sur **un autre slot d'Ambry**, donc invisible de
`_slot_front_edge()`. C'est même devenu leur rôle : **annoncer Ambry avant qu'elle n'entre.**

---

## 7. Les comptes, rapportés et non contraints

### Par famille

| Famille | Tri | Part |
|---|---:|---:|
| zone habitation (7 modules complets, façades, toits, linge, véhicule, passerelle) | 1 704 | 32,2 % |
| garde-corps (49 montants + 3 mains courantes) | 624 | 11,8 % |
| traverses (12 têtes + 12 sabots + 12 béquilles) | 432 | 8,2 % |
| **roche arrachée** (24 blocs) | 428 | 8,1 % |
| la rue et sa bordure | 336 | 6,3 % |
| zone serre (verrière, arceaux, rangs, pignons, sas) | 324 | 6,1 % |
| zone antenne (fosse, local, mât, vergues, haubans) | 304 | 5,7 % |
| colliers de greffe (8 massifs + 16 coulures) | 288 | 5,4 % |
| rive extérieure + taquets | 288 | 5,4 % |
| pas d'appontage (dalle, « H », plots, hachures) | 240 | 4,5 % |
| zone greffe (fouille, cuves, caisses, panneau) | 200 | 3,8 % |
| pavage de cour | 120 | 2,3 % |
| plateau | 12 | 0,2 % |
| **TOTAL** | **5 300** | **35,7 tri/m²** |

### Coût à l'échelle du corridor

| | BRIEF-0114 | BRIEF-0115 |
|---|---:|---:|
| `Section_05` | 15 026 tri | **17 158** |
| corridor entier | 53 982 tri | **56 114** (62,3 % du total) |
| `.glb` | 3 152 288 o | **3 375 972 o** (+7,1 %) |

**Aucun budget n'a été appliqué** — décision de l'opérateur, toujours en vigueur. Ce qui a été
appliqué, c'est l'autre règle, celle qui n'est pas un budget : *un détail de 3 cm fait 1,4 pixel*.
Le plus petit trait posé est le joint de 12 cm (5,5 px) ; rien n'est plus fin.

⚠️ **Mais voir la limite 9.1 : le générateur porte encore un cliquet local, et Section_05 en occupe
95,3 %.**

---

## 8. Textures et UV (ADR-0028)

**Aucune image, aucune texture dans le `.glb`** — `_audit()` le vérifie (bloquant :
`baseColorTexture`, `normalTexture`, `emissiveTexture`, `images`…) et il passe. PBR par facteurs et
slots, comme tout le Long Cortège.

- **Dépliage** : `ak.box_project_uv(ambry, 0,700 tuile/m)`, **inchangé** — projection en boîte,
  1,43 m par tuile, contre 5,00 m pour le bordé. Le brief ne demande pas de dépliage continu pour
  cette pièce et rien n'en justifie un : aucune carte de détail ne porte ici de motif orienté (voir
  §3.4 pour la seule réserve).
- **`TEXCOORD_0` COMPTÉ, jamais supposé** : `_audit()` compte les primitives du `.glb` et échoue si
  une seule en manque. **37/37 primitives portent `TEXCOORD_0` et 37/37 portent `TANGENT`** — dont
  les **17 du `Section_05`**, c'est-à-dire les 12 d'Ambry.
- **Densité par slot** : tableau §3.1. Moyenne d'ensemble **0,697 tuile/m** pour une cible de 0,700
  (écart 0,4 %). Minimum **0,445** sur `AA_Tech_Ambry` : ce sont les **haubans**, quatre tubes
  obliques dont aucune face n'est alignée sur un axe du monde. La borne théorique de la projection
  en boîte est cible/√3 = **0,404** ; on est au-dessus, et l'anisotropie maximale de **1,57** reste
  sous la demi-tuile. Le second minimum, 0,488, est la roche, pour la même raison (facettes
  irrégulières).
- **Planche au damier UV** : vignette 5, à la perspective du jeu. Grande case = 1,43 m, petite =
  17,9 cm. Les cases restent carrées sur les dalles, la rue, les toits et les rives ; elles ne
  s'allongent que sur les facettes obliques de la roche et sur les haubans, dans le rapport annoncé.
- **Aucune demande `TEX-NNNN` n'est livrée** : la planche de matières est un contrat de **slots**,
  et les images ne sont pas de ce lot (brief §« Découper Ambry en slots par nature »).

---

## 9. Limites connues

### 9.1 ⚠️ `Section_05` occupe 95,3 % d'un cliquet que ce fichier s'impose encore

`TRI_BUDGET_SECTION = 18_000` est un contrôle **bloquant** hérité du `BRIEF-0089` :
`Section_05` sort à **17 158**. Il reste **842 triangles** avant que le build ne refuse de sortir.

Ce n'est pas un budget que j'ai appliqué — je n'ai rien rogné — mais c'est un mur que **le prochain
lot va rencontrer**, et il vaut mieux le savoir maintenant qu'au moment où le build cassera sans
raison apparente. Le tronçon 5 porte trois choses lourdes à la fois : Ambry (5 300), le complexe
industriel (1 756) et la peau. **Je n'ai pas touché à la constante** : lever un cliquet de contrat
sans qu'on me le demande serait pire que de le signaler. À votre arbitrage — 24 000 laisserait de
la marge sans changer le budget total (90 000, occupé à 62,3 %).

### 9.2 La cour est sombre, et c'est un choix subi autant que voulu

Le pavage de cour ne pose que **10 dalles**. La raison est mécanique et mesurée : le bâti fait
3,63 m de large, les modules en occupent 0,88 à 2,20, et une dalle qui mord sur un module n'est pas
posée. Avec trois colonnes de 1,21 m, **pas une seule** dalle ne passait — la cour sortait
entièrement sombre. Six colonnes au pas de 0,74 m la font remonter à 10.

Le sol entre les bâtiments est donc, pour l'essentiel, **le fond du plateau** à `−4,78`. À 70° de
plongée il se lit comme une cour à l'ombre, pas comme un trou — vérifié au rendu — et c'est ce qui
donne au village sa profondeur. Mais **la valeur claire a baissé de 1,7 %** (luminance 209,4 contre
213,1 sur le cadre de proue). C'est dix fois moins que la marge du `BRIEF-0114`, et la décision de
l'opérateur (« l'ivoire reste ») est tenue. Si vous voulez plus de clair, le levier est d'élargir
le bâti en rognant la rive extérieure — une ligne, mais c'est une décision de plan.

### 9.3 Le contraste local mesuré n'augmente pas

| Vignette | AVANT | APRÈS |
|---|---:|---:|
| cadre proue — luminance | 213,1 | **209,4** |
| cadre proue — contraste local 16 px | 24,73 | **23,30** |
| cadre poupe — luminance | 220,6 | **220,4** |
| cadre poupe — contraste local 16 px | 28,35 | **25,45** |

**Et je préfère le dire franchement : ce chiffre-ci ne mesure pas ce que le lot corrige.** Le
`BRIEF-0114` cherchait du *relief* et le contraste local en fenêtres de 16 px est le bon instrument
pour ça — il a doublé, à juste titre. Le `BRIEF-0115` cherche de la *lecture* : des formes
différentes, des orientations fausses, des objets à l'échelle humaine, des fenêtres allumées.
Remplacer des fonds `AA_Greeble` très noirs (`#141419`) par de l'anthracite `#24252B` et poser de
grands toits ivoire fait **baisser** l'écart-type local tout en **augmentant** ce qu'on comprend de
l'image. Les deux vignettes de caméra sont là pour ça, et c'est elles qu'il faut regarder — pas le
nombre.

Ce qui est mesurable et qui a bougé dans le bon sens est en §0 : sept silhouettes au lieu de
quatre identiques, 46 fenêtres au lieu de zéro, 24 débords au lieu d'un rectangle.

### 9.4 La bâche est écrue, pas bleue — et c'est un essai fait puis défait

La planche de matières nomme « **toile bleue** » dans sa palette (TEX-AMB-12) et la planche de
concept en montre une sur la vue gameplay. J'ai donc posé le `#1C2B5E` d'Helios Vanguard, **rendu à
la caméra du jeu, et regardé** (ADR-0006). Verdict sans appel : une bâche de 1,36 × 2,08 m en bleu
saturé devient **l'objet le plus visible des 27 mètres**, avant les fenêtres allumées — elle vole la
lecture à ce qui est le sujet, et elle contredit « le vert de la serre est la seule couleur ». Elle
est repassée à l'écru `#DDDCD2` et réduite à 60 % du toit. **Le bleu reviendra par la carte** si
vous le voulez, ou en repassant une entrée de `AMBRY_MATERIAL_SPECS` à `_VANGUARD["panel"]`.

### 9.5 Un cadre de jeu ne montre que 26,4 m, Ambry en fait 27 (30 avec ses colliers)

Inchangé depuis le `BRIEF-0114` : il n'existe **aucun cadrage** qui montre Ambry entière à la
caméra du jeu. La planche en donne donc deux, plus la vue de dessus. Ce n'est pas une limite du
lot, c'est ce que le joueur vivra — et c'est pourquoi les quatre zones devaient rester lisibles
**une par une**.

### 9.6 Les trois tranchées comptent moins qu'avant

Elles séparaient les quatre zones quand la cour était ivoire d'un bout à l'autre. Maintenant que le
sol du bâti est majoritairement sombre, elles se fondent dans les ruelles. Elles sont conservées
(0,55 m, ouvertes jusqu'au fond du plateau, et **elles ne coupent jamais la rue** — Ambry reste
intacte), mais leur travail est aujourd'hui fait par les **volumes**, pas par elles.

---

## 10. Déterminisme et vérifications

- **Trois exécutions, zéro octet divergent** :
  `9e9a0da5baac7b230b8d1b8cb4596d03db1c30fa7daee19e8c434fbe29f52315`
  (`blender-aegis -t 1 -b`, comme l'impose `scripts/build-hull.sh`).
- **Tous les harnais bloquants du générateur passent** : plafond de construction et plafond de vol,
  jonctions de tronçons, contrat de noms, les 30 marqueurs, UV et tangentes sur **37/37**
  primitives, largeurs, couleurs réservées aux tirs, **absence de texture et d'image**, orientation
  des normales, gardes de tourelle, dégagement du complexe, emprise d'Ambry — plus les **trois
  harnais neufs de ce lot** (strays par slot, emprunt d'un slot du bordé, slots vides à dessein).
- **`./scripts/check.sh` : ALL GREEN** — 1 034 tests, 8 842 assertions, 0 échec, 0 erreur d'analyse.
- **Les 42 repères du corridor sont inchangés** ; le repère `Ambry` reste à
  `(+10,65 ; −4,200 ; −60,00)`.
- **Hiérarchie de palette** (aire vue) : structure 76,8 % (cible 80), appareillage 21,9 %,
  violet + magenta **1,37 %** (cible 5, cliquet 9).

---

## 11. La planche

`docs/forge/output/BRIEF-0115-planche.png` — 1920 × 6380, **sept vignettes**.

| # | Vue | Ce qu'elle tranche |
|---|---|---|
| 1 | **AVANT**, caméra du jeu, cadre proue | « je comprends toujours pas visuel ce que c'est » |
| 2 | **APRÈS**, **même cadrage** | la greffe, sa roche débordante, le pas vide et son « H », le début du village |
| 3 | **AVANT**, caméra du jeu, cadre poupe | les boîtes identiques et les ailettes vertes |
| 4 | **APRÈS**, **même cadrage** | l'habitation, la serre qui pousse, le mât et ses haubans |
| 5 | **Damier UV** à la perspective du jeu | 0,700 tuile/m sur Ambry contre 0,200 sur le bordé ; aucune image dans le `.glb` |
| 6 | **De dessus** (31 m, orthographique) | **à comparer à la silhouette de la planche de concept** |
| 7 | **Élévation tribord** (31 m) + dalle du plafond de vol | rien au-dessus de `−3,20` ; les sept hauteurs de module |

Le Specter-9 réel est à sa place de jeu sur les quatre vignettes de caméra (ADR-0025) : les balles
doivent se lire par-dessus, et elles se lisent.

> ⚠️ **La planche est CONSERVATRICE.** `_plate_lights()` ne projette aucune ombre — délibéré depuis
> le `BRIEF-0089` : valider un relief qui ne se lirait *que* par ses ombres serait un piège. En jeu,
> `directional_shadow_max_distance` vaut 40 et Ambry est à ~20 m de la caméra : **chaque module,
> chaque coulure et chaque bloc de roche recevra une ombre portée que la planche ne montre pas.**
