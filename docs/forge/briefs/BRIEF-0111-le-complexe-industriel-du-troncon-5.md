# BRIEF-0111 — Le complexe industriel du tronçon 5 : meubler 69 m de coque nue

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-09-08

## Objectif

Bâtir un **complexe industriel destructible** sur le flanc tribord du cinquième tronçon, dans les
soixante-neuf mètres de coque que rien n'occupe.

> « On cherche à peaufiner le niveau, plus de bloc non travaillé, non texturé, on meuble. Il y
> avait une section à droite sur le segment 5 : on peut faire un complexe industriel destructible
> avec nos assets » (opérateur, 2026-09-08).

## Le vide, mesuré

Ce que le tronçon 5 (`s = 400` à `500`) porte réellement, bord par bord :

| Bord | Occupé | **Vides ≥ 25 m** |
|---|---|---|
| **Tribord (+x)** | tourelles à `s = 410,0` et `478,8` | **`s = 410` → `479` : 69 m** |
| Bâbord (−x) | tourelles `415,2`, `463,3`, `470,0` ; pont d'envol `450,0` | `415` → `450` (35 m), `470` → `500` (30 m) |

Plus : nœud d'épine à `s = 406` (sur l'axe), conduite d'artère à `s = 435`.

⚠️ **C'EST LE PLUS GRAND VIDE LATÉRAL DU NIVEAU**, et il tombe dans le dernier tronçon — celui
que le joueur traverse juste avant la poupe, quand il a appris à lire la coque et qu'il cherche
quoi viser.

## ⚠️ AUCUN BUDGET DE TRIANGLES SUR CE LOT

> « Je ne veux pas entendre parler de budget et de restriction, je veux un jeu beau »
> (opérateur, 2026-09-08).

C'est une décision, et **les mesures lui donnent raison**. Le plafond de 80 000 triangles de la
poupe a été posé au `BRIEF-0105` par estimation, jamais par mesure. Or la poupe entière — trois
groupes propulsifs animés, douze verrous, vingt bras, dix-sept pièces instanciées, la garnison,
les panaches — rend à **2,0 à 3,7 ms par image** sur les **16,67** que donne une image à 60 Hz.
Il reste les trois quarts de l'image.

**Ne comptez donc pas les triangles, et ne coupez rien « pour tenir ».** Le seul plafond qui
existe est celui que la mesure imposera, et il se mesurera **après**, en temps GPU
(`.claude/resources/howto-mesurer-la-perf.md`) — jamais en sommets.

⚠️ **CE QUI RESTE VRAI, ET QUI N'EST PAS UN BUDGET** : un détail de 3 cm fait **1,4 pixel** à
45,8 px/m. Le supprimer n'est pas une économie, c'est un refus de payer pour ce que personne ne
verra. La spec §20 — « concentrer le travail sur peu de pièces » — parle de LISIBILITÉ, pas de
coût, et elle tient.

## Ce qu'il faut faire

### 1. L'emprise

`s ∈ [418 ; 472]` — **54 m utiles**, en gardant 8 m de garde de chaque tourelle voisine. Sur le
pont médian et la facette extérieure, `|x| ∈ [6,3 ; 10,6]` d'après le profil du corridor.

⚠️ **NE PAS MORDRE LA CONDUITE D'ARTÈRE À `s = 435`.** Elle est à `x = −3,60` — bâbord, donc hors
de votre emprise — mais son dégagement de tir passe par le canal : ne posez rien qui déborde sur
l'axe.

⚠️ **ET RIEN NE DOIT DÉPASSER `BUILD_CEILING_Y = −3,20`.** Le pont médian est à −4,99 : vous avez
**1,79 m** de ciel. C'est la contrainte qui a fait échouer le pylône au `BRIEF-0109`, et elle vaut
ici aussi — mesurez-la avant de dessiner, pas après.

### 2. Ce que le complexe est

Une **installation**, pas un tapis de greebles : la règle du `BRIEF-0094` tient — « un module de
relief ne se pose que dans l'emprise d'une installation ». Le complexe EST cette emprise, et il
doit se lire comme un lieu : une entrée, un cœur, une sortie.

Ce dont vous disposez, déjà réduit et dans le dépôt :

| Pièce | Triangles | Rôle |
|---|---:|---|
| `artery_conduit.glb` / `_bend` | 652 / 648 | **les cibles** — quatre états `Actif/Endommagé/Rupture/Rompu` |
| `artery_hose.glb` / `_bend` | 320 / 344 | décor souple |
| `stern_pylon.glb` | 2 612 | masse haute — ⚠️ **5,30 m pour 1,79 m de ciel : il ne rentre pas ici.** Ce n'est PAS une question de coût, c'est le plafond de vol : au-delà de `−3,20`, le chasseur entrerait dedans |

Plus **votre propre géométrie** pour ce qu'aucune pièce ne couvre : plate-forme, cuves,
passerelles, cheminées.

### 3. ⚠️ CE QUI EST DESTRUCTIBLE EST UNE **CONDUITE**, ET RIEN D'AUTRE

Le corridor a passé la journée à apprendre au joueur qu'une **conduite se coupe** — douze d'entre
elles sont des cibles, et les couper affaiblit la poupe (`ADR-0050`). Un complexe où d'autres
formes seraient destructibles lui apprendrait l'inverse au dernier tronçon.

**Posez donc `CTRL | Complexe NN` pour les conduites** — quatre à six — et du décor autour. Le code
les montera comme les douze autres, avec les mêmes états et le même effet.

⚠️ **ET LES REPÈRES MARQUENT LE BAS DE LA PIÈCE.** L'origine des `.glb` de l'artère n'est pas dans
la pièce (`(−0,36 ; 1,00 ; 1,38)` pour la conduite droite) ; le code compense en mesurant la boîte
englobante. Vos repères disent où le bas doit se poser.

### 4. Ce qui doit se voir, et à quelle échelle

Le corridor rend à **45,8 px/m**. Un détail de 3 cm fait 1,4 pixel. Concentrez le travail sur :

- la **silhouette** vue de dessus — la caméra plonge à 70°, elle voit les faces horizontales ;
- les **arêtes qui prennent la lumière** ;
- et **le contraste avec la coque nue** de part et d'autre : c'est ce qui fera exister le complexe
  comme un lieu et non comme une texture de plus.

⚠️ **LA LEÇON DU `BRIEF-0110`, ET ELLE EST À VOUS** : « sur cette caméra, l'emprise au sol paie
mieux que la hauteur » — une hauteur ne rend que 34 % de sa longueur à l'écran quand un plan en
rend 94 %.

## Texture (ADR-0028)

**Aucune image.** PBR par facteurs, comme tout le Long Cortège. Les slots du kit
(`AA_Hull`, `AA_Greeble`, `AA_Panel`, `AA_Emissive_Engine`) — et `CortegeSkin` posera les cartes
dérivées par-dessus, comme sur le reste de la coque.

⚠️ **`AA_Emissive_Engine` SEULEMENT SUR CE QUI DOIT S'ÉTEINDRE** au blackout de la fin. Une veine
peinte ailleurs resterait allumée sur un vaisseau mort, et rien ne le signalerait.

## Animation (ADR-0046 §6)

**Figée** pour la structure. Les conduites apportent les leurs.

## Livrables

| Fichier | Description |
|---|---|
| `tools/blender/build_long_cortege.py` | le complexe et ses repères |
| `assets/imported/models/backgrounds/long_cortege.glb` | le corridor |
| `docs/forge/output/BRIEF-0111-report.md` | emprise, repères, triangles, ciel mesuré |
| `docs/forge/output/BRIEF-0111-planche.png` | rendus à la caméra du jeu, **avec les conduites instanciées** |

## Critères d'acceptation

- [ ] **Le complexe tient dans `s ∈ [418 ; 472]`**, tribord, et garde ses 8 m aux deux tourelles.
- [ ] **Rien au-dessus de `−3,20`**, mesuré sur le binaire ; **rien sur l'axe** du canal.
- [ ] **Quatre à six `CTRL | Complexe NN`**, `y` échantillonné sur la peau, marquant le **bas**.
- [ ] **Il se lit comme un LIEU** : capture avant/après au même cadrage, à la caméra du jeu, avec
      les conduites instanciées. ⚠️ Le critère n'est pas « il y a de la matière », c'est « on voit
      une installation ».
- [ ] **Les harnais du corridor restent verts** — taper, emprises de pont d'envol, tourelles,
      nœuds, et les douze repères de conduite du `BRIEF-0110`.
- [ ] **Déterminisme** : trois exécutions, zéro octet divergent.
- [ ] **Le compte de triangles est RAPPORTÉ, jamais contraint** : dites ce que le complexe
      coûte et quel est le nouveau total du corridor (49 458 avant), pour que la mesure de perf
      qui suivra sache à quoi elle s'applique. ⚠️ Aucun de ces chiffres n'est un critère de
      rejet sur ce lot.

## Hors périmètre

- **Le code de jeu** : le concepteur monte les conduites sur vos repères et les câble à la charge.
- **La poupe**, ses canaux, ses dix-sept repères.
- **Les deux vides de bâbord** (35 et 30 m) : notés, pour un lot suivant s'il en faut un.
