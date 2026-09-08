# BRIEF-0109 — Rapport de forge : la poupe cède la place, et elle dit où

- **Brief** : `docs/forge/briefs/BRIEF-0109-la-poupe-cede-la-place-aux-vraies-pieces.md`
- **Date** : 2026-09-08
- **Outil** : Blender 5.2.1 LTS (`blender-aegis`), toujours `-t 1`
- **Livrables** : `tools/blender/build_stern.py`,
  `assets/imported/models/backgrounds/stern_hull.glb`,
  `docs/forge/output/BRIEF-0109-planche.png`, ce rapport
- **Périmètre respecté** : aucun `.gd`, `.tscn`, `.tres` touché ; aucun commit ; aucune pièce du
  `BRIEF-0108` modifiée. `./scripts/check.sh` **vert** après la livraison (1 020 méthodes de test,
  8 731 assertions, 0 échec) — la coque réimporte sans un mot, repères compris.

---

## 0. Le résultat en une ligne

**2 942 triangles** (contre 3 182), soit **−240 exactement** : les quatre fuseaux, et rien
d'autre. **Huit repères** sont dans le binaire, leur `y` échantillonné sur la surface réelle, et
la marge au plafond la plus serrée des quatre pylônes vaut **+0,114 m**.

| Ce qui est parti | Ce qui arrive |
|---|---|
| `build_pylons()` — 4 fuseaux étagés, **240 tri** | 4 × `CTRL \| Pylone NN`, **0 tri** |
| — | 4 × `CTRL \| Liaison NN`, **0 tri** |

---

## 1. Ce que j'ai retiré, et ce qui s'appuyait dessus

`build_pylons()` et sa constante `PYLON_STAGES` sont supprimés ; la station `PYLON_Z =
(−0,40 ; −6,00)` reste, parce que ce sont désormais les **stations des repères** — les mêmes,
au centième, que celles des fuseaux retirés.

**Le bandeau de flanc `AA_Panel` est parti avec, et il n'était porté par rien d'autre** : c'était
un rectangle de 0,16 m d'épaisseur plaqué sur la face extérieure du fuseau, à `x_out − 0,24`,
entre `y = −8,20` et `−5,20`, sur 1,90 m de long. Ses quatre coordonnées dérivaient toutes du
fuseau (`x_out = wmax − 0,10`, `cz ± 0,95`) : sans lui il n'existe plus de surface où le poser.
L'autre accent coloré du flanc, celui de `build_shoulders()` (`|x| = 16,86…17,02`, `z ∈
[8,24 ; 9,16]`), **n'a pas bougé** — il appartient aux épaulements avant, pas aux pylônes.

**L'étagère de rive est intacte** : elle vit dans `build_skin()` (points 13 à 19 de la
demi-section), et le loft n'a pas été touché d'un sommet. Le profil de largeur mesuré sur le
binaire le dit station par station :

```
500..505 : 17,10     506..510 : 18,50     511..519 : 19,90     520 : 18,31
```

— exactement les valeurs du `BRIEF-0107`. Les fuseaux n'avaient jamais porté la largeur maximale
(ils s'arrêtaient à `wmax − 0,10`), donc leur départ ne change pas la silhouette d'un centimètre.

---

## 2. Les quatre repères de pylône

### 2.1 — Les chiffres, lus dans le binaire

Pièce mesurée dans `stern_pylon.glb` (jamais recopiée du brief) : **2,889 × 5,300 × 2,060 m**,
origine au pied (`y_min = +0,000`).

> ⚠️ **La cote annoncée par le brief (2,75 m en x) est fausse de 14 cm.** Le socle mesure bien
> 2,748 m, mais les deux passerelles débordent de 7 cm de chaque côté entre `y = 1,20` et `4,00`.
> Un repère calculé sur la cote annoncée aurait laissé 14 cm d'erreur d'emprise sans que rien ne
> le dise. `_piece_box()` relit le `.glb`.

| Repère | x | y | z | lacet | sommet | **marge au plafond** | peau échantillonnée |
|---|---:|---:|---:|---:|---:|---:|---:|
| `CTRL \| Pylone 01` | **+17,42** | **−8,614** | **−0,40** | −90° | −3,314 | **+0,114 m** | −8,614 |
| `CTRL \| Pylone 02` | **−17,42** | **−8,614** | **−0,40** | +90° | −3,314 | **+0,114 m** | −8,614 |
| `CTRL \| Pylone 03` | **+18,34** | **−8,618** | **−6,00** | −90° | −3,318 | **+0,118 m** | −8,618 |
| `CTRL \| Pylone 04` | **−18,34** | **−8,618** | **−6,00** | +90° | −3,318 | **+0,118 m** | −8,618 |

Aucune des quatre marges ne passe sous zéro : le harnais `_assert_markers()` échouerait le build.
Les valeurs exactes du binaire sont `±17,4230 / −8,6138` et `±18,3390 / −8,6182`.

### 2.2 — ⚠️ Aucun point de l'étagère ne convient, et c'est arithmétique

C'est le point dur du lot, et il faut le dire net.

```
arête de rive        bande 2 : −5,60      bande 3 : −4,60
plafond du niveau                −3,20                −3,20
ciel disponible                   2,40 m               1,40 m
hauteur de la pièce               5,30 m               5,30 m
```

Il n'y a **pas 5,30 m de ciel au-dessus des terrasses**, et il n'y en aura jamais tant que
`CEILING_Y` vaut −3,20. Posé sur la terrasse la plus basse (−8,07 en bande 2, −7,08 en bande 3),
un pylône crèverait le plafond de **0,40 m** et de **1,40 m**. L'y enfoncer jusqu'à la cote légale
(−8,60) l'enterrerait de **0,54 m** et de **3,35 m** : il ne resterait qu'un moignon de **1,95 m**
en bande 3, sur les 5,30 de la pièce.

**L'assise est donc prise un cran plus bas**, sur la paroi qui monte du bassin à l'arête :
`_pylon_seat()` balaie la peau de l'arête vers l'intérieur, au millimètre, et retient le **premier
point dont l'altitude laisse passer les 5,30 m**. C'est le point le plus haut et le plus extérieur
qui soit légal. C'est aussi, exactement, ce que faisait le fuseau retiré : il partait de `SOLE_Y`,
3,4 m sous la terrasse.

Conséquence assumée, chiffrée :

| | bande 2 (`Pylone 01/02`) | bande 3 (`Pylone 03/04`) |
|---|---:|---:|
| emprise x de la pièce | 16,39 … 18,45 | 17,31 … 19,37 |
| emprise z de la pièce | −1,84 … +1,04 | −7,44 … −4,56 |
| **encastrement max** (côté extérieur) | 3,01 m | 4,02 m |
| **hauteur émergée au-dessus de l'arête** | 2,29 m | 1,28 m |
| **porte-à-faux au-dessus du bassin** | 0,91 m, à 3,39 m de la sole | 0,89 m, à 3,38 m |
| marge à l'emprise des berceaux (15,78) | **0,61 m** | **1,53 m** |

Le pylône **sort de la rive** au lieu de se poser dessus. Rendu et regardé (vignette 2 bis), c'est
lisible : la face intérieure est dégagée sur ses 5,30 m et c'est celle que la caméra du jeu voit ;
la face extérieure est prise dans les terrasses.

### 2.3 — ⚠️ Le rayon se tire sur la PEAU, pas sur la coque

Un rayon vertical tiré sur la coque **complète** à `x = 17,42` ne touche pas l'étagère : il touche
le **dessus d'une bride** de `build_rim_clamps()`, à `y = −5,14`. Le pylône se serait assis
**3,53 m trop haut** et aurait crevé le plafond de 3,43 m — sans une erreur, la bride étant du
décor parfaitement légitime. `_skin_bvh()` n'interroge donc que `build_skin()`.

### 2.4 — Le quart de tour est une cote, pas un goût

Le socle mesure 2,748 m dans son `x` local et 2,060 dans son `z` ; l'étagère n'offre que 0,90 m
(bande 2) à 1,30 m (bande 3). Présentée en travers, la pièce déborde de **1,45 m** de chaque côté ;
pivotée de 90°, de **1,03 m**, et son grand axe s'aligne sur la rive au lieu de la traverser. Le
quart de tour met en outre sa face détaillée (passerelles, sockets moteur, `z` local positif) du
côté du bassin — le seul que la caméra voie. Les deux bords sont en miroir : `−90°` à tribord,
`+90°` à bâbord.

---

## 3. Les quatre repères de liaison

| Repère | x | y | z | lacet | sommet | marge au plafond | peau (corridor) |
|---|---:|---:|---:|---:|---:|---:|---:|
| `CTRL \| Liaison 01` | **+3,85** | **−4,484** | +9,80 | −90° | −4,044 | +0,844 m | −4,324 |
| `CTRL \| Liaison 02` | **−3,85** | **−4,484** | +9,80 | +90° | −4,044 | +0,844 m | −4,324 |
| `CTRL \| Liaison 03` | **+8,70** | **−5,230** | +9,80 | −90° | −4,790 | +1,590 m | −5,070 |
| `CTRL \| Liaison 04` | **−8,70** | **−5,230** | +9,80 | +90° | −4,790 | +1,590 m | −5,070 |

**Le repère est la pose de l'ORIGINE de la pièce, pas son point de contact**, parce que c'est ce
que le code fait de plus simple (`piece.position = marker.position`). Les deux ne coïncident que
si l'origine est au point bas : c'est le cas du pylône (`y_min = 0,000`), pas du flexible
(`y_min = +0,160`, son tube est porté 0,30 m au-dessus de son origine). Le `y` du repère est donc
**l'assise moins 0,160 m**, l'écart étant lu dans `artery_hose.glb`.

### 3.1 — Pourquoi *devant* le collecteur, et pas dessous

Le brief demande la jonction « là où le collecteur aboutit ». **Sous le collecteur, il n'y a pas
la place** — mesuré :

- entre la peau du corridor (`−4,966` à `x = 7,60`) et le dessous des six colliers de serrage
  (`−4,808`) il reste **0,158 m** ; le flexible fait **0,280 m** de diamètre ;
- les créneaux libres entre colliers (1,48 à 3,58 m) sont coupés par les quatre pieds du
  collecteur (`x = ±4,60` et `±9,80`, 0,84 m d'emprise) et par le bloc de jonction (`|x| ≤ 1,85`).
  **Le plus long dégagement continu mesure 2,42 m**, pour une pièce de 2,74 m.

En **avant** du collecteur, `z ≥ 9,62 + 0,14`, le pont est nu. Les quatre flexibles sont donc à
`z = 9,80` (emprise `9,66 … 9,94`), couchés en travers, arrivant au collecteur — ce qui est
précisément la lecture demandée.

### 3.2 — Les deux stations latérales sont les deux plateaux plats

Le pont du corridor à `s = 498,20` a deux plateaux et une chine entre eux :

```
|x| 2,0 … 5,6   ->  −4,262 … −4,334     dénivelé 0,054 m sur les 2,74 m de la pièce
|x| 5,6 … 6,4   ->  la chine, 0,65 m de dénivelé
|x| 6,4 … 10,4  ->  −4,942 … −5,070     dénivelé 0,109 m
```

Une pièce **rigide** ne peut pas franchir la chine ; les deux stations retenues (`|x| = 3,85` et
`8,70`) sont au milieu des deux plateaux. L'assise est le **minimum** de la peau sous les 2,74 m,
jamais la valeur au centre — sur un bombement, la valeur du centre fait s'enfoncer les deux bouts.
Le bombement résiduel est donné ci-dessus : 5,4 cm et 10,9 cm.

### 3.3 — Des flexibles, pas des conduites

Le brief en fait une règle de lecture et elle est tenue : ce sont quatre `artery_hose.glb`, du
décor. Aucune `artery_conduit*.glb` n'est posée sur la poupe.

### 3.4 — Une mesure qui intéresse la dette de l'artère

À `s = 498,20`, la peau que ces repères échantillonnent vaut **−4,288 à `|x| = 3,60`** et
**−4,301 à `|x| = 4,40`** — les deux latéraux exacts des douze conduites du corridor. La constante
posée `CortegeArtery.DECK_Y = −4,30` tombe donc à **1,3 cm** de ce que la peau dit vraiment. Elle
n'était pas fausse ; elle était seulement **non mesurée**, et c'est ce que ce lot supprime ici.

---

## 4. Les critères d'acceptation, un par un

| Critère | Chiffre mesuré | ✔ |
|---|---|:--:|
| Les 4 pylônes procéduraux ont disparu, l'étagère est intacte | 3 182 → **2 942 tri (−240)** ; profil de largeur identique (17,10 / 18,50 / 19,90 / 18,31) | ✅ |
| 4 `CTRL \| Pylone NN`, `y` échantillonné, position au centième | `±17,42 / −8,614 / −0,40` et `±18,34 / −8,618 / −6,00` — relus dans le `.glb`, écart à la pose demandée **0,0e+00 m** | ✅ |
| Marge au plafond mesurée et nommée pour chacun | **+0,114 / +0,114 / +0,118 / +0,118 m** (plafond −3,20) | ✅ |
| 2 à 4 `CTRL \| Liaison NN`, hors emprise et hors canaux | **4**, à `z = 9,80` (emprise `9,66 … 9,94`, soit **1,66 m** hors de la bande interdite `\|z\| ≤ 8,00`) ; canaux à `z ≤ −8,50`, distance **18,16 m** | ✅ |
| Jonction `s = 500` inchangée au micron | **6,56 × 10⁻⁷ m** sur 48 sommets, des deux bords — le chiffre exact d'avant | ✅ |
| Trois canaux intacts, 0 m² dans les panaches | **0,000000000 m²** ; demi-largeur libre **2,200 m** pour un panache de 1,700 ; fond −10,950 ; harnais `_plume_intrusion()` / `_channel_clearance()` toujours là | ✅ |
| Emprise des berceaux | **0,000000 m²** de décor au-dessus du pont ; les 8 pièces posées vérifiées une à une par `_assert_markers()` | ✅ |
| Budget | voir §5 | ✅ |
| Déterminisme | 3 exécutions, `sha256 = 82163a1ff0b2665e678ed31b4e0d56e8f8fb9552d12a8b071fceb436613baf58`, **zéro octet divergent** | ✅ |
| Rendu et REGARDÉ à la caméra du jeu, pièces posées | `BRIEF-0109-planche.png`, **9 vignettes**, les 4 pylônes et les 4 flexibles montés sur les repères **relus dans le binaire** | ✅ |

Deux harnais neufs, qui échouent le build :

- `_assert_markers()` — relit les huit nœuds `CTRL | ` **dans le `.glb`**, compare la pose au
  micron, vérifie que le lacet est un lacet **pur** (le quaternion, jamais `to_euler()` : un quart
  de tour autour de `y` tombe exactement sur le blocage de cardan d'une décomposition XYZ), puis
  calcule la boîte de la pièce **posée et pivotée** et refuse le plafond crevé, l'emprise mordue,
  le canal envahi.
- `_pylon_seat()` — refuse de rendre une assise si la rive n'en offre aucune sous −8,60.

---

## 5. Budget

Le compte de la poupe **entière** (coque + berceaux + moteurs + ancrages + bras), sur les 80 000
du brief :

| | triangles | reste sur 80 000 |
|---|---:|---:|
| avant (`BRIEF-0108`) | 64 894 | 15 106 |
| après retrait des 4 fuseaux | **64 654** | 15 346 |
| + 4 `stern_pylon` (4 × 2 612) | **75 102** | 4 898 |
| + **2** `artery_hose` (2 × 320) | **75 742** | **4 258** |
| + **4** `artery_hose` (4 × 320) | **76 382** | **3 618** |

⚠️ **Le brief compte deux flexibles, je livre quatre repères.** L'arithmétique du brief
(75 982 → 75 742 → 4 258) correspond à **deux** `artery_hose` ; poser les quatre en coûte
**640 de plus** et laisse **3 618**. Les repères, eux, ne coûtent rien : le concepteur peut n'en
monter que deux (les `Liaison 01/02`, les plus centraux, ceux que la caméra cadre le mieux) et
retrouver exactement le chiffre du brief. La coque, elle, tient **2 942 / 20 000 (14,7 %)** de son
propre budget.

---

## 6. Ce que je n'ai pas pu tenir, et pourquoi

1. **« Posés sur la surface de l'étagère »** — l'assise n'est pas sur la terrasse mais sur la
   paroi qui y monte, un cran plus bas. C'est arithmétique et sans échappatoire (§2.2) : il n'y a
   que 1,40 à 2,40 m de ciel au-dessus de l'arête pour une pièce de 5,30 m. Le brief prévoyait le
   cas (« si un repère la fait passer sous zéro, c'est le repère qui descend ») ; je l'ai fait
   descendre **jusqu'au point le plus haut qui soit légal**, pas plus, et je donne l'encastrement
   qui en résulte (3,01 m et 4,02 m côté extérieur).

2. **La chaîne de brides de rive n'a pas été ouverte, et quatre brides sont maintenant dans le
   volume du pylône.** Mesuré, bride par bride :

   | Pylône | brides concernées (z) | recouvrement | emprise de la bride |
   |---|---|---:|---|
   | 01 / 02 | `[−1,15 ; −0,15]` | **1,00 m** (totale) | x 16,80…17,86, y −8,20…−5,14 |
   | 01 / 02 | `[+0,70 ; +1,70]` | 0,345 m | idem |
   | 03 / 04 | `[−7,20 ; −6,20]` | **1,00 m** (totale) | x 17,70…18,86, y −7,20…−4,14 |
   | 03 / 04 | `[−5,35 ; −4,35]` | 0,795 m | idem |

   Les deux brides intégralement recouvertes sont **entièrement contenues dans la boîte du
   pylône** (en x, en y et en z) ; le rail de guidage de la bande 3 (`x 17,92…18,20`,
   `y −8,15…−7,65`) l'est aussi, celui de la bande 2 passe **0,035 m sous** le socle et ne touche
   rien. Interrompre la chaîne aurait été une modification de silhouette que le brief ne demande
   pas (« ne touchez qu'à ce qui est décrit ») : **je la signale au lieu de la faire**. Si le
   rendu final gêne, la correction tient en trois lignes dans `build_rim_clamps()` — sauter les
   brides dont l'empan en `z` croise `PYLON_Z ± 1,45`.

3. **La cote de pièce annoncée par le brief est fausse en x** (2,75 contre 2,889 mesurés) : je
   n'ai pas tenu le chiffre du brief, j'ai tenu le binaire (§2.1).

4. **Le budget diffère de 640 triangles** de l'arithmétique du brief, parce que je livre quatre
   repères de liaison au lieu de deux (§5). Le choix reste ouvert côté code.

---

## 7. Suggestions

- **Un `CTRL | Liaison` de plus n'est pas gratuit à l'écran non plus** : quatre flexibles alignés
  au même `z` lisent comme une nappe. Si seulement deux sont montés, préférer `01/02`
  (`|x| = 3,85`) : ils tombent dans l'axe du bloc de jonction et se lisent sous le collecteur.
- **`CortegeArtery.DECK_Y` peut cesser d'être une dette sans nouveau brief** : la même mécanique
  que `_hose_seat()` (interroger `blc._surface_y()` à la station de la conduite) donnerait aux
  douze conduites du corridor l'assise que ces quatre flexibles ont déjà. La mesure du §3.4 dit
  que l'écart serait de l'ordre du centimètre — c'est la *provenance* de la cote qui change, pas
  sa valeur.
- **Si un jour la rive doit porter une masse haute qui se lise**, ce n'est pas le repère qu'il
  faut bouger, c'est l'arête : abaisser `crest_y` de la bande 3 de −4,60 à −5,60 rendrait 1,00 m
  de ciel, et un pylône y émergerait de 2,28 m au lieu de 1,28. C'est une décision de silhouette,
  donc un brief.

---

## 8. Texture et animation (sections du brief présentes)

- **Texture : aucune** (`ADR-0028`). Le brief porte sa section et déclare pourquoi : les repères
  ne portent pas de maillage. Le `.glb` contient **0 image**, vérifié par `_audit()` ; les UV de
  la coque sont inchangées — projection en boîte **0,20 tuile/m**, densité mesurée **0,1989
  tuile/m** (5,027 m/tuile), anisotropie max **1,414** (borne √3 = 1,732), et les 5 primitives
  portent toutes `TEXCOORD_0`, **compté** dans le binaire.
- **Animation : aucune dans ce fichier** (`ADR-0046` §6). La coque reste figée ; ce qui bouge sur
  la rive est animé dans **son** fichier (`stern_pylon.glb`, 3 clips), et la coque ne porte que le
  repère où il se pose. Aucun pilote Blender n'est en jeu ici.
