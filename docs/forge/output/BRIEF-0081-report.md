# BRIEF-0081 — Dégeler l'azimut de `Spike_03` : compte-rendu

*Mesuré le 2026-08-24. **Verdict : LIVRÉ.** Les quatre épines visent le joueur en jeu, les trois
seuils du brief sont tenus avec de la marge, et la largeur de coque **diminue** de 2,7 mm.*

| | valeur | seuil du brief | marge |
|---|---|---|---|
| jour minimal entre épines voisines | **1 023 mm** | ≥ 800 mm | +28 % |
| écart angulaire minimal | **34,7°** | ≥ 20° | +74 % |
| largeur de coque | **11,0286 m** | ≤ 11,150 m | 121 mm |

**Coque livrée** : `assets/imported/models/bosses/pale_leviathan.glb`,
sha256 `1bfdf51b9145330ef66c76362b00814c868797b91cc53683921bbecfbb9eb07e`
(la coque du dépôt valait `98529ce703faf6dfe6e6b5b560f68ef01299394b757a961f26f1840a359353a4`).

## 0. ⚠️ L'azimut retenu est **220,0°**, et le fichier livré est bien celui-là

Ma session a été coupée entre la décision et son application ; le disque a un moment porté la
variante à **215,0°**. Elle est **abandonnée**. Ce qui est sur le disque aujourd'hui, script et
`.glb`, est la variante à **220,0°**, et les deux concordent :

- `tools/blender/build_pale_leviathan.py` → `"root": (-3.193, -2.679, 1.12)`, soit azimut
  **220,0°**, rayon 4,168 m ;
- `pale_leviathan.glb` → sha256 `1bfdf51b…`, régénéré par
  `./scripts/build-hull.sh --check pale_leviathan` **après** ce changement, et bit-à-bit identique
  à la variante mesurée dans ce rapport.

Pourquoi 220 et pas 215 : §4. Ce n'est pas un arrondi, c'est une mesure.

---

## 1. Contrôle d'instrument

Avant de toucher à quoi que ce soit, la coque du dépôt a été mesurée avec l'outillage de
`BRIEF-0080` (lecture directe du chunk JSON du `.glb`, composition des transformations
parent → enfant à la main, sans Blender ni Godot) :

| Épine | axe **fichier** | axe **en jeu** |
|---|---|---|
| `Spike_01` | −111,3° | **+68,7°** |
| `Spike_02` | −71,0° | **+109,0°** |
| `Spike_03` | +59,3° | **−120,7°** |
| `Spike_04` | +111,5° | **−68,5°** |

Ce sont **exactement** les quatre valeurs annoncées par le brief. Deuxième contrôle : le banc de
variantes (copie de travail du script, triplets pilotés par l'environnement) rebâtit la coque du
dépôt **byte pour byte** — sha256 `98529ce7…`. Troisième contrôle : l'outil de jour rend
1 486,4 et 1 516,3 mm sur le dépôt, c'est-à-dire les chiffres de `BRIEF-0080` et, à 1 mm près,
ceux de `BRIEF-0045`. Les trois instruments sont étalonnés.

---

## 2. Les quatre angles, dans les DEUX repères

Axe `Spike_NN → Muzzle_Spike_NN`, projeté dans le plan de jeu (`x = X`, `y = −Z`, le joueur à
**−90°**). L'angle « en jeu » vaut l'angle du fichier **+180°** : c'est `FACING_PLAYER =
Vector3(0, PI, 0)` appliqué par `boss_controller.gd:94`.

### Avant (coque du dépôt)

| Épine | axe (x ; y) fichier | **fichier** | **en jeu** | dans [−160 ; −20] en jeu |
|---|---|---|---|---|
| `Spike_01` | (−0,895 ; −2,294) | −111,3° | **+68,7°** | ❌ vers l'arrière |
| `Spike_02` | (+0,732 ; −2,131) | −71,0° | **+109,0°** | ❌ vers l'arrière |
| `Spike_03` | (+0,916 ; +1,542) | +59,3° | **−120,7°** | ✅ |
| `Spike_04` | (−0,491 ; +1,243) | +111,5° | **−68,5°** | ✅ |

### Après (coque livrée)

| Épine | axe (x ; y) fichier | **fichier** | **en jeu** | dans [−160 ; −20] en jeu |
|---|---|---|---|---|
| `Spike_01` | (−1,076 ; +0,594) | **+151,1°** | **−28,9°** | ✅ |
| `Spike_02` | (+1,151 ; +0,999) | **+40,9°** | **−139,1°** | ✅ |
| `Spike_03` | (+0,466 ; +1,813) | **+75,6°** | **−104,4°** | ✅ |
| `Spike_04` | (−0,491 ; +1,243) | +111,5° | **−68,5°** | ✅ inchangée |

**4/4.** Les quatre tombent dans [+20° ; +160°] dans le fichier, donc dans [−160° ; −20°] en jeu,
avec au minimum 8,9° de marge à la borne la plus proche (`Spike_01`, −28,9°).

---

## 3. Les trois seuils, chiffrés

Distance surface à surface entre épines voisines, mesurée sur le **maillage** (nuages complets +
BVH dans les deux sens), en 3D et projetée en vue de dessus. La saturation de l'outil est à
2 000 mm : au-delà, il n'affine pas.

| | dépôt | V1 (0080) | V2 (0080, refusée) | **livrée** | seuil |
|---|---|---|---|---|---|
| jour `Spike_01`↔`Spike_04` | 1 486,4 mm | 1 029 mm | 1 171 mm | **1 023,3 mm** | |
| jour `Spike_02`↔`Spike_03` | 1 516,3 mm | 1 516 mm | **159 mm** | **1 488,4 mm** | |
| **jour minimal** | 1 486,4 mm | 1 029 mm | **159 mm** | **1 023,3 mm** | **≥ 800** ✅ |
| jour minimal, projeté (vue de dessus) | 1 464,6 mm | — | 155,5 mm | **1 009,1 mm** | |
| autres paires (01-02, 01-03, 02-04, 03-04) | > 2 000 mm | — | — | **> 2 000 mm** | |
| **écart angulaire minimal** | 40,3° | 23,4° | **5,4°** | **34,7°** | **≥ 20** ✅ |
| éventail (écarts triés) | 40,3 / 52,3 / 130,3 / 137,1° | — | 5,4 / 29,0 / 46,8° | **34,7 / 35,9 / 39,6°** | |
| **largeur de coque** | 11,0313 m | 11,0294 m | **11,3112 m** | **11,0286 m** | **≤ 11,150** ✅ |
| cordes | 5,78 / 5,06 / 4,49 / 2,68 m | — | — | **5,81 / 4,97 / 4,61 / 2,68 m** | hiérarchie intacte |
| aire de silhouette, vue de dessus | 99,518 m² | — | 99,636 m² | **99,287 m²** (−0,23 %) | |
| aire de silhouette, vue de jeu (20°) | 93,966 m² | — | 94,233 m² | **93,941 m²** (−0,03 %) | |

Aucun seuil n'est franchi. **L'éventail livré (34,7°) est plus large que celui que `BRIEF-0045`
avait accepté (26,8°) et que celui de la V1 de `BRIEF-0080` (23,4°)** ; il ne perd que 5,6° sur la
coque du dépôt, laquelle n'avait que deux épines à placer vers l'avant au lieu de quatre.

La largeur **baisse** : 11,0286 m contre 11,0313. C'est le point où `BRIEF-0080` avait dû payer
2,83 % d'écart au contrat ; ici l'écart au `width_x = 11,00` retombe à **+0,26 %**.

---

## 4. Ce qui a été changé, et pourquoi 220°

### Le levier

`BRIEF-0080` avait établi l'impasse : `Spike_02` retournée doit atteindre le secteur avant-bâbord,
**où `Spike_03` est déjà**. Ce brief lève le gel, et c'est effectivement `Spike_03` qui débloque —
mais par sa **racine**, pas par son axe :

| | dépôt | livrée |
|---|---|---|
| racine `Spike_03` (Blender x, y, z) | (−4,02 ; −1,10 ; 1,12) | **(−3,193 ; −2,679 ; 1,12)** |
| azimut de la racine | 195,3° | **220,0°** (+24,7°) |
| rayon de la racine | 4,168 m | **4,168 m** (inchangé, plancher 4,15) |
| `ctrl` | (−5,36 ; −2,72 ; 1,14) | (−3,40 ; −4,90 ; 1,14) |
| `tip` | (−5,50 ; −5,34 ; 0,98) | (−5,25 ; −6,80 ; 0,98) |

`Spike_02` prend le **couloir extérieur** bâbord (axe −139,1°), `Spike_03` la **voie intérieure**
(axe −104,4°) : les deux lames divergent au lieu de se coller. `Spike_01` est retournée vers
l'avant-tribord (−28,9°) et `Spike_04`, qui visait déjà, n'a pas bougé d'un sommet.

Le mât suit sa racine : `_build_masts()` relit `root`, il n'y a rien d'autre à déplacer (§5.8).

### Le balayage

Modèle plan étalonné sur le dépôt (axe = racine → `bezier(port)` ; jour = axes échantillonnés
moins les deux rayons — il rend 1 354 et 1 328 mm là où le maillage donne 1 516 et 1 486 : il
**sous-estime de ~12 %**, donc il est conservateur). Grilles de 10 à 20 cm sur `ctrl` et `tip` des
trois épines mobiles, **azimut de la racine de `Spike_03` balayé de −180° à −115°** par pas de 5°,
filtrées par : corde à ±0,15 m de l'originale, axe dans la cible, silhouette hors du contour de
coque sur les 55 % terminaux, boîte et pivot. 1,58 million de quadruples valides, départagés par
matrices de jour par paires. Meilleur atteignable par azimut de racine :

| azimut racine `Spike_03` | déplacement | jour (modèle) | écart angulaire min |
|---|---|---|---|
| 195,3° (**gelée**, dépôt) | 0° | 954 mm | 27,3° |
| 205° | +9,7° | 1 062 mm | 28,6° |
| 215° | +19,7° | 1 062 mm | 36,2° |
| **220°** | **+24,7°** | **1 062 mm** | **35,9°** |
| 245° | +49,7° | 1 062 mm | 42,5° |

Deux enseignements. **(a)** Même racine gelée, une solution existait (954 mm / 27,3° au modèle,
soit ~1 070 mm au maillage) : le gel de 0080 n'était pas une impasse absolue, il coûtait 9° de
lisibilité d'éventail. **(b)** Le rendement s'écrase après +20° : reculer la racine de 50° ne
rachète rien sur le jour et complique la lecture (l'épine part alors du milieu de la face avant).

### Pourquoi 220 et pas 215 — le creux de dégagement des plaques

La variante à 215° a été construite, mesurée, **et écartée** : elle passe les trois seuils, mais
elle fait tomber une marge qui n'a rien à voir avec les épines. Le mât déplacé entre dans la
course des plaques, et le harnais du build le voit :

| azimut de la racine | 195,3° | 200° | 205° | 210° | **215°** | **220°** | 225° |
|---|---|---|---|---|---|---|---|
| `Plate_01..04` / coque, coquille, entre elles | 71,3 mm | 71,3 | 57,0 | 42,5 | **39,9** | **65,9** | 71,3 |
| jour `Spike_02`↔`Spike_03` | 1 516 mm | — | — | — | **1 156** | **1 488** | — |

À 220° le mât ressort du creux : **65,9 mm** au lieu de 39,9, et le jour bâbord gagne 332 mm au
passage. Tout le reste (axes, largeur, triangles, budgets) est identique entre les deux variantes.
Le prix résiduel — 71,3 → 65,9 mm, soit **−5,4 mm** — est le seul recul de marge de ce brief, et
il est assumé : c'est la contrepartie du déplacement de mât, mesurée et bornée.

---

## 5. Les huit preuves

### 5.1 Les quatre angles, deux repères, avant et après
§2. Les quatre dans [−160° ; −20°] en jeu. ✅

### 5.2 Les trois seuils
§3. 1 023 mm / 34,7° / 11,0286 m contre 800 / 20 / 11,150. ✅

### 5.3 Les bouches sont au bout

Distance 3D au centre de coque, sur les nœuds du `.glb` livré :

| Épine | centre → `Spike_NN` | centre → `Muzzle_Spike_NN` | écart |
|---|---|---|---|
| `Spike_01` | 4,320 m | 5,546 m | **+1,226 m** ✅ |
| `Spike_02` | 4,373 m | 5,466 m | **+1,093 m** ✅ |
| `Spike_03` | 4,316 m | 5,936 m | **+1,621 m** ✅ |
| `Spike_04` | 4,686 m | 5,853 m | **+1,167 m** ✅ |

### 5.4 Aucune interpénétration

**(a) Le harnais du script**, rejoué à chaque build sur le maillage livré (soupes de triangles +
BVH, rotations écrites en repère Godot, sphères d'exclusion aux charnières). Le build **refuse
d'exporter** si une marge tombe à zéro :

| Contrôle | dépôt | **livrée** |
|---|---|---|
| `Shell_Ring` / coque, orbite 360° | 77,0 mm | **77,0 mm** |
| `Shell_Crescent` / coque | 241,3 mm | **241,3 mm** |
| `Plate_01..04` / coque, coquille, entre elles | 71,3 mm | **65,9 mm** ⬊ (§4) |
| `Core` / `Maw_Lip` / `Node_0X` / `Ring_0X` | 166,5 / 75,9 / 97,2 / 63,6 mm | **idem** |
| `Spike_01..04` / coque, pointage ±40° | 190,3 mm | **190,3 mm** (pire cas : `Spike_04`, intacte) |
| `Spike_0X_Mid` et `_Tip`, flexion ±25° | 87,2 mm | **83,5 mm** ⬊ |
| flexion VERTICALE encaissée sans morsure | ±0° | **±5°** ⬈ |

Les 83,5 mm sont un contact `Spike_02_Mid`↔`Spike_02_Tip` **dans la chaîne** : c'est la courbure
propre de la faux, déjà le pire cas de la coque au dépôt (87,2 mm sur la même épine). −3,7 mm.

**(b) Les épines entre elles** — angle mort du harnais, mesuré à part : c'est le « jour » du §3.
Minimum **1 023,3 mm**, aucune paire sous 1 m.

**(c) Une plaque en chute contre une épine** — l'autre angle mort, mesuré avec les formules
exactes du combat (`_tick_plate_falls` : bascule `chute × 135°` autour de `(−sin, 0, cos)` de
`base_angle`, écartement radial `chute × 1,8 m`, affaissement `−1,2·chute²`) et avec les **azimuts
réels** relevés dans le `.glb` (§7), pour 12 positions d'orbite × 3 bascules × 5 taux de chute :

*Plaques à leur azimut construit, coquille à plat, pire cas cumulé jusqu'au taux de chute indiqué :*

| chute | `Spike_01` | `Spike_02` | `Spike_03` | `Spike_04` |
|---|---|---|---|---|
| 0,00 — dépôt / **livrée** | 102,0 / **102,0** | 529,7 / **561,4** | 1 755,4 / **> 2 000** | 503,9 / **503,9** |
| 0,25 — dépôt / **livrée** | **0,0** / **0,0** | 447,7 / **561,4** | 1 755,4 / **> 2 000** | 132,6 / **132,6** |
| 1,00 — dépôt / **livrée** | 0,0 / **0,0** | 343,1 / **561,4** | 1 755,4 / **> 2 000** | 0,0 / **0,0** |

⚠️ **Le zéro est PRÉEXISTANT et rigoureusement identique avant/après** : dès 25 % de chute, une
plaque traverse `Spike_01` — dont ni la racine ni l'azimut n'ont changé — et à 75 % elle traverse
`Spike_04`, qui n'a pas bougé d'un sommet. Les deux épines que ce brief déplace, elles,
**s'éloignent** des plaques (`Spike_02` +218 mm au pire cas, `Spike_03` sort de la portée de
mesure). Ce n'est pas une régression de ce brief : c'est un défaut de conception du mouvement —
une plaque qui bascule à r ≈ 4,9 m balaie l'anneau des racines d'épine à r ≈ 4,2 m, quelle que
soit la géométrie. Coquille basculée (32° ou 65°), la marge minimale de la coque livrée remonte à
**778,6 mm** (dépôt : 125,1 mm). Le sujet appartient au code, pas à la coque (§8).

### 5.5 Budgets tenus

| | dépôt | livrée | plafond |
|---|---|---|---|
| triangles | 27 710 | **27 756** | 30 000 (brief) / 40 000 (contrat) |
| sommets | 40 630 | **40 672** | |
| bbox (Godot X, Y, Z) | 11,0313 × 3,1620 × 13,9972 m | **11,0286 × 3,1620 × 13,9972 m** | 11,00 ±3 % / 3,20 / 14,00 ±3 % |
| pivot | (−0,0001 ; +0,0110 ; −0,0014) | **(−0,0127 ; +0,0110 ; −0,0014)** | ±0,020 m |
| `AA_Hull` | 33,7 % | **33,7 %** | ≥ 30 % |
| `AA_Greeble` | 17,4 % | **17,4 %** | ≤ 20 % |
| `AA_Emissive_Engine` | 8,5 % | **8,5 %** | ≤ 8 % (écart connu, **strictement inchangé**) |

Les +46 triangles viennent de la longueur d'arc des trois courbes, qui change le nombre de
stations ; la règle topologique, elle, est la même. La hauteur ne bouge pas d'un micron malgré
l'arche (§6), et le noyau reste le point le plus haut de la coque : crête d'épine **1,528 m**
contre **1,592 m** pour `Core` — l'exigence de `BRIEF-0041` tient, avec 64 mm.

### 5.6 UV et tangentes
**145 primitives, 145 `TEXCOORD_0`, 145 `TANGENT`** — comme au dépôt. ✅

### 5.7 Déterminisme
`./scripts/build-hull.sh --check pale_leviathan` → *déterminisme OK —
`1bfdf51b9145330ef66c76362b00814c868797b91cc53683921bbecfbb9eb07e`*, et c'est le fichier qui est
sur le disque. Deux exécutions, `-t 1` forcé, byte-identiques. ✅

### 5.8 Preuve que rien d'autre n'a bougé

Hachage par maillage (positions, normales, UV, tangentes, indices, matériau, translation du nœud),
dépôt contre livrée :

| | maillages |
|---|---|
| **identiques bit à bit (20)** | `Core`, `Heart`, `Maw_Lip`, `Node_01..03`, **`Plate_01..04`**, `Ring_01..05`, **`Shell_Crescent`**, **`Shell_Ring`**, **`Spike_04`, `Spike_04_Mid`, `Spike_04_Tip`** |
| **modifiés (10)** | `Body`, `Spike_01`+`_Mid`+`_Tip`, `Spike_02`+`_Mid`+`_Tip`, `Spike_03`+`_Mid`+`_Tip` |

44 nœuds avant, 44 après, **mêmes noms** : contrat de noms intact.

`Body` change parce que **le mât suit la racine de `Spike_03`**, et rien d'autre : sur 14 643
sommets, **120 diffèrent**, et les 120 sont à moins de **0,696 m** de la racine d'épine — les 120
d'avant autour de l'ancienne, les 120 d'après autour de la nouvelle, avec la **même distribution
de distances au millimètre** (min 0,143 m, max 0,696 m). Le mât s'est déplacé en bloc ; aucun autre
point de la coque n'a été touché.

---

## 6. L'arche de `ctrl.z`, et la provision de braquage ±40°

`Spike_01` et `Spike_02` portent un `ctrl.z = 1,55` au lieu de ~1,15. Son coût et sa cause, mesurés
sur la géométrie livrée (quatre builds) :

| variante | `Spike` / coque, pointage | chaîne, flexion ±25° | bbox | verdict |
|---|---|---|---|---|
| **arche 1,55 + provision ±40° — LIVRÉE** | **190,3 mm** | **83,5 mm** | 11,0286 × 3,1620 × 13,9972 | ✅ |
| plat (1,16 / 1,14) + provision ±40° | 190,3 mm | **0,0 mm** | — | ❌ **MORD** — le build refuse d'exporter (`Spike_01_Tip`, pointage −40°, flexion −12°) |
| plat, **sans** provision (`SPIKE_DEG = 0`) | 196,5 mm | 83,8 mm | identique | ✅ |
| arche, **sans** provision (témoin) | 196,5 mm | 83,5 mm | identique | ✅ |

Trois conclusions, dans l'ordre où elles servent à décider :

1. **L'arche tient uniquement à la provision ±40°.** Sans elle, les épines plates dégagent
   *mieux* (83,8 contre 83,5 mm) et le pointage n'existe plus.
2. **L'arche ne coûte rien d'autre.** La bbox est identique au micron dans les quatre cas, la
   hauteur reste 3,1620 m, le noyau reste le point haut (1,592 contre 1,528), le jour, l'éventail
   et la largeur sont des grandeurs **planes** : elles ne bougent pas d'un millimètre avec ou sans
   arche. Elle est donc **gardée**, conformément à la consigne « garde-la si elle ne coûte rien ».
3. **La variante sans provision est à une ligne**, si le concepteur tranche dans l'autre sens :
   `ctrl.z` de `Spike_01` 1,55 → 1,16 et de `Spike_02` 1,55 → 1,14, rien d'autre. Elle rend 6,2 mm
   de marge à la racine et 0,3 mm à la chaîne.

⚠️ **Les épines braquées, entre elles** (demande explicite du brief). Au repos le jour minimal est
de 1 023 mm ; mais le harnais braque chaque épine **indépendamment**, et deux voisines séparées de
34,7° qui partent chacune de 40° en sens opposé **se croisent** — géométriquement inévitable dès
que l'éventail est plus serré que 80°, ce qui est le cas de toute coque à quatre membres tournés
vers un même demi-plan (la cible fait 140° de large : 46,7° au mieux entre voisines). En revanche,
si les quatre épines **suivent la même cible** — c'est le sens de `_spine_track` — leur braquage
est commun, leurs écarts relatifs sont conservés et le jour de 1 023 mm est maintenu. **Le jour au
repos ne dit rien du braquage différentiel** : si le pointage revient, il devra être *commun* ou
borné par la moitié de l'écart angulaire.

---

## 7. Correction : la convention d'azimut des plaques

Le brief donne les azimuts réels **−152,0 / +154,0 / +100,0 / +46,0**. Mesure indépendante sur les
nœuds `Plate_01..04` du `.glb` (composition depuis la racine ; aucun de ces nœuds ne porte de
rotation) :

| nœud | position monde (X, Y, Z) | rayon | `atan2(Z, X)` | `atan2(−Z, X)` = **plan de jeu** |
|---|---|---|---|---|
| `Plate_01` | (−2,7371 ; +1,1000 ; −1,4554) | 3,100 | **−152,0°** | +152,0° |
| `Plate_02` | (−2,7863 ; +1,1000 ; +1,3590) | 3,100 | **+154,0°** | −154,0° |
| `Plate_03` | (−0,5383 ; +1,1000 ; +3,0529) | 3,100 | **+100,0°** | −100,0° |
| `Plate_04` | (+2,1534 ; +1,1000 ; +2,2300) | 3,100 | **+46,0°** | −46,0° |

Rayon 3,10 m, espacement 54°, croissant de 198° : **tout est confirmé**, et le harnais de ce
rapport emploie ces valeurs (§5.4c). Deux précisions qui coûteront moins cher maintenant que plus
tard :

- Les valeurs du brief sont dans la convention **`atan2(Z, X)`**, qui est le **miroir** du plan de
  jeu du projet (`gameplay_plane.gd` : `x = X`, `y = −Z`, employé pour les axes d'épines). Dans le
  repère où sont exprimés tous les angles d'épines de ce rapport, les mêmes plaques sont à
  **+152,0 / −154,0 / −100,0 / −46,0** dans le fichier, donc à **−28 / +26 / +80 / +134 en jeu**.
- Ces derniers nombres sont, **au dixième près, les constantes `PLATES` du script**
  (`(−28, 21), (26, 21), (80, 21), (134, 21)`). Les `PLATES` ne sont donc pas « des azimuts locaux
  à `Shell_Crescent` » : ce sont bien les azimuts monde, exprimés dans le repère du jeu. Ce qui
  est faux, c'est le `base_angle = TAU·i/alive` du runtime (0 / 90 / 180 / 270°, ou 120° à trois
  plaques), qui ne correspond à aucune plaque réelle. Mon rapport `BRIEF-0080` avait, lui aussi,
  décrit ces deux jeux de valeurs comme « deux conventions concurrentes » sans trancher : la
  bonne, c'est `PLATES` (au repère près), et le mode `geo` de mon harnais — `atan2(Z, X)` du pivot
  réel — l'employait déjà. Les mesures de 0080 sur ce point restent donc valides.

---

## 8. Réserves et angles morts

- **La coque n'a pas été vue en jeu**, seulement en rendu Cycles (vue de dessus orthographique et
  vue à l'angle exact de la caméra de jeu, `tools/render-hull.py`). Ce qui est jugé ici est une
  séparation de 1 023 mm sur une coque de 11 m : le rendu suffit à la voir. La règle du dépôt
  reste de confirmer en jeu.
- **`./scripts/check.sh` n'a pas été exécuté.** Aucun fichier moteur n'est touché par ce brief, et
  le concepteur modifie `scripts/bosses/leviathan_combat.gd` et `leviathan_plate.gd` en parallèle :
  lancer la porte de qualité maintenant mesurerait son travail en cours, pas le mien. À lui de la
  passer à l'intégration — c'est là que le nouvel import du `.glb` sera vérifié.
- **La plaque qui traverse une épine en tombant** (§5.4c) est un défaut **préexistant**, identique
  avant et après, et il appartient au code : soit la chute emmène la plaque hors de l'anneau des
  racines, soit `base_angle` cesse d'être `TAU·i/alive`. Deux mesures à faire côté moteur, pas
  côté coque.
- **`HALF_W` n'est plus une coordonnée de pointe.** Les deux bornes en X sont désormais portées
  par les maillages `Spike_01_Tip` (+5,527) et `Spike_02_Tip` (−5,502). La constante reste définie
  et documentée — c'est la demi-largeur du **contrat** — mais elle n'est plus référencée par une
  définition d'épine. Si le concepteur préfère qu'elle le redevienne, il faut décaler les deux
  pointes de ~2,7 cm, ce qui coûte 5 mm de jour.
- **Le harnais ne mesure toujours ni une épine contre la coquille, ni deux épines entre elles** :
  les deux chiffres qui décident ici viennent d'outils écrits pour `BRIEF-0080` et rejoués ici. Le
  code de mesure est reproductible et tiendrait dans `_clearance_table()` — c'est la suggestion 4
  de 0080, toujours ouverte.

---

## 9. Fichiers

| Fichier | État |
|---|---|
| `tools/blender/build_pale_leviathan.py` | **modifié** — seules les définitions d'épines (`root`/`ctrl`/`tip` de `Spike_01..03`) et leurs commentaires |
| `assets/imported/models/bosses/pale_leviathan.glb` | **régénéré** — sha256 `1bfdf51b9145330ef66c76362b00814c868797b91cc53683921bbecfbb9eb07e`, déterminisme vérifié |
| `docs/forge/output/BRIEF-0081-planche-quatre-vues.png` | **livrée** — avant / après / V2 refusée annotés dans le repère du jeu, plus les quatre vues de la coque livrée |
| `docs/forge/output/BRIEF-0081-report.md` | ce rapport |
| `assets/licenses/ASSET_PROVENANCE.csv` | ligne du `.glb` mise à jour (hash, date, brief, mesures) + ligne de la planche |
| `tools/blender/lib/aegis_kit.py` | **non touché** (gelé) |
| `scripts/`, `resources/`, `scenes/`, `tests/` | **non touchés** |
