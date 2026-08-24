# BRIEF-0080 — Retourner `Spike_01` et `Spike_02` vers l'avant : compte-rendu

*Mesuré le 2026-08-24. **Verdict : NON LIVRÉ**, en application du seuil posé par le brief lui-même
(§ « Le seuil, posé AVANT la mesure »). La coque du dépôt est **inchangée** —
`assets/imported/models/bosses/pale_leviathan.glb` vaut toujours
`98529ce703faf6dfe6e6b5b560f68ef01299394b757a961f26f1840a359353a4`, et
`tools/blender/build_pale_leviathan.py` n'a pas une ligne de différence.*

**Ce qui est livré** : ce rapport, la planche `BRIEF-0080-planche-quatre-vues.png` (qui montre la
coque refusée, mesurée et regardée), et une ligne de provenance pour cette planche.

**Ce qui n'est pas livré, et pourquoi** : la géométrie retournée existe, elle passe le contrat, elle
passe le harnais de dégagement, elle est déterministe — et elle **casse la silhouette validée par
`BRIEF-0041`**. Le jour entre `Spike_02` et `Spike_03` tombe de **1516 mm à 159 mm** et leur écart
angulaire de **40,3° à 5,4°** : deux des quatre membres deviennent un **doublet parallèle**. Le
chiffre est en dessous du tiers de ce que `BRIEF-0045` avait déjà signalé comme « le vrai coût »
(475 mm), et il ne vient pas d'un mauvais choix de courbe : c'est le **maximum atteignable**, établi
par balayage (§5).

---

## 1. Les quatre angles, dans les DEUX repères

Axe `Spike_NN → Muzzle_Spike_NN`, composé depuis les translations parent→enfant du glTF, projeté
dans le plan de jeu (`x = X`, `y = −Z`, **le joueur est à −90°**). L'angle « en jeu » est
l'angle du fichier **+180°**, ramené dans ]−180 ; 180] : c'est l'effet de
`FACING_PLAYER = Vector3(0, PI, 0)` appliqué à la coque par `boss_controller.gd:94`.

### Coque du dépôt (état actuel, inchangé)

| Épine | axe (x ; y) **fichier** | angle **fichier** | angle **en jeu** | dans [−160° ; −20°] en jeu |
|---|---|---|---|---|
| `Spike_01` | (−0,895 ; −2,294) | **−111,3°** | **+68,7°** | ❌ vers l'arrière |
| `Spike_02` | (+0,732 ; −2,131) | **−71,0°** | **+109,0°** | ❌ vers l'arrière |
| `Spike_03` | (+0,916 ; +1,542) | **+59,3°** | **−120,7°** | ✅ |
| `Spike_04` | (−0,491 ; +1,243) | **+111,5°** | **−68,5°** | ✅ |

Ce tableau **reproduit à la virgule celui de l'en-tête du brief**. C'est le contrôle d'instrument :
la mesure est faite sur le `.glb` du dépôt, avant de toucher à quoi que ce soit.

### Coque candidate (les deux retournées) — mesurée, puis refusée

| Épine | axe (x ; y) **fichier** | angle **fichier** | angle **en jeu** | dans [−160° ; −20°] en jeu |
|---|---|---|---|---|
| `Spike_01` | (−1,139 ; +0,939) | **+140,5°** | **−39,5°** | ✅ |
| `Spike_02` | (+1,200 ; +2,539) | **+64,7°** | **−115,3°** | ✅ |
| `Spike_03` | (+0,916 ; +1,542) | **+59,3°** | **−120,7°** | ✅ inchangée |
| `Spike_04` | (−0,491 ; +1,243) | **+111,5°** | **−68,5°** | ✅ inchangée |

L'objectif du brief est donc **atteignable** : les quatre visent le joueur. Le refus ne porte pas
sur l'objectif, il porte sur son prix.

---

## 2. Ce qui a été fabriqué pour pouvoir décider

Deux triplets, et rien d'autre (mêmes `root`, donc mêmes mâts, donc `Body` intouché) :

```python
"Spike_01": ctrl = (5.90, -0.20, 1.55)   tip = ( 5.55, -6.20, 1.10)
"Spike_02": ctrl = (-5.90, -2.00, 1.55)  tip = (-5.55, -3.80, 1.10)
```

La coque candidate a été construite avec **le script du dépôt**, ses deux triplets pilotés par
l'environnement (copie de travail en bac à sable, jamais dans `tools/`), puis rendue et **regardée**
(ADR-0006). Elle vit dans le scratchpad de session ; rien n'en est versionné à part son image.

### Les sept preuves, sur la coque candidate

1. **Les quatre angles, dans les deux repères** — tableau du §1. Les quatre tombent dans
   [+20° ; +160°] dans le fichier, donc dans [−160° ; −20°] en jeu. ✅
2. **Les bouches sont au bout** (distance au centre de coque, sur les nœuds du `.glb`) :

   | Épine | centre → `Spike_NN` | centre → `Muzzle_Spike_NN` | écart |
   |---|---|---|---|
   | `Spike_01` | 4,320 m | 5,684 m | **+1,364 m** ✅ |
   | `Spike_02` | 4,373 m | 5,711 m | **+1,338 m** ✅ |
   | `Spike_03` | 4,316 m | 5,746 m | **+1,430 m** ✅ |
   | `Spike_04` | 4,686 m | 5,853 m | **+1,167 m** ✅ |

3. **Aucune interpénétration.** Deux mesures.
   **(a) Le harnais du script**, imprimé à chaque build (soupes de triangles + BVH, rotations
   écrites en repère Godot, sphères d'exclusion aux charnières) :

   | Contrôle | dépôt | candidate |
   |---|---|---|
   | `Shell_Ring` / coque, orbite 360° | 77,0 mm | **77,0 mm** |
   | `Shell_Crescent` / coque | 241,3 mm | **241,3 mm** |
   | `Plate_01..04` / coque, coquille, entre elles | 71,3 mm | **71,3 mm** |
   | `Core` / `Maw_Lip` / `Node_0X` / `Ring_0X` | 166,5 / 75,9 / 97,2 / 63,6 mm | **idem** |
   | `Spike_01..04` / coque, pointage ±40° | 190,3 mm | **176,1 mm** (`Spike_02`) |
   | `Spike_0X_Mid` et `_Tip`, flexion ±25° | 87,2 mm | **91,1 mm** ⬈ |

   Le build **refuse d'exporter** si une marge tombe à zéro : la candidate a passé cette porte.
   **(b) Les épines contre la coquille en mouvement** — l'angle mort du harnais, mesuré à part avec
   les formules exactes du combat (`_tick_plate_falls` : bascule `chute × 135°` autour de
   `(−sin, 0, cos)` de `base_angle`, écartement radial `chute × 1,8 m`, affaissement `−1,2·chute²`),
   sur **12 positions d'orbite × 3 bascules de croissant × 5 taux de chute × 3 conventions
   d'azimut** (géométrique, `i·90°` du cycle à 4 plaques, `i·120°` du cycle à 3), soit 540 poses :

   | Convention | `Spike_01` | `Spike_02` | `Spike_03` | `Spike_04` |
   |---|---|---|---|---|
   | `i·90°`, croissant au repos — **dépôt** | 16,2 mm | 44,5 mm | 21,3 mm | 357,7 mm |
   | `i·90°`, croissant au repos — **candidate** | **38,6 mm** ⬈ | **120,2 mm** ⬈ | 21,3 mm | 357,7 mm |
   | toutes les autres combinaisons | 0,0 mm | 0,0 mm | 0,0 mm | 0,0 à 140,1 mm |

   ⚠️ **Ce zéro est PRÉEXISTANT et identique avant/après** : dès que le croissant bascule, ou dès
   qu'on prend l'azimut géométrique des plaques plutôt que celui du runtime, les plaques qui tombent
   **traversent** les épines — sur la coque du dépôt comme sur la candidate. Ce n'est pas une
   régression de ce brief, c'est un défaut que rien ne mesure aujourd'hui (voir §7).
4. **Budgets tenus** : **27 728 triangles** (27 710 au dépôt ; +18, la longueur d'arc des deux
   courbes change le nombre de stations — la topologie, elle, suit la même règle), plafond 30 000.
   `AA_Hull` **33,7 %**, `AA_Greeble` **17,4 %**, `AA_Emissive_Engine` **8,5 %** en triangles
   (8,5 % au dépôt aussi — l'écart connu à la cible « ≤ 8 % », qui vaut en sommets, est strictement
   inchangé). **bbox 11,3112 × 3,1620 × 13,9972 m**, sous le plafond 12,0 × 3,4 × 15,0 du brief ;
   pivot centré à (+0,0029 ; +0,0110 ; −0,0014). ⚠️ La **largeur** passe de 11,0313 à 11,3112 m —
   c'est **2,83 % d'écart au contrat** (`width_x = 11,00`, tolérance ±3 %) : la candidate consomme
   94 % de la tolérance. Pourquoi elle n'a pas le choix : §4.
5. **UV et tangentes** : **145 primitives, 145 `TEXCOORD_0`, 145 `TANGENT`** — comme au dépôt.
6. **Déterminisme** : deux exécutions de la candidate (`-t 1` forcé), sha256 identique
   `ce16f1628155be34a60549b5832f7685c536038f60f770a50ab964c4ee7c30a4`. Et sur le dépôt :
   `./scripts/build-hull.sh --check pale_leviathan` → `déterminisme OK — 98529ce7…`, c'est-à-dire
   **exactement le fichier qui est sur disque**. La chaîne est reproductible de bout en bout, et la
   coque témoin de ce rapport est bien celle du dépôt.
7. **`Spike_03` et `Spike_04` n'ont pas bougé** — hachage par maillage (positions, normales, UV,
   tangentes, indices, matériau, translation du nœud), dépôt contre candidate :

   | | maillages |
   |---|---|
   | **identiques bit à bit (24)** | `Body`, `Core`, `Heart`, `Maw_Lip`, `Node_01..03`, `Plate_01..04`, `Ring_01..05`, `Shell_Crescent`, `Shell_Ring`, **`Spike_03`, `Spike_03_Mid`, `Spike_03_Tip`, `Spike_04`, `Spike_04_Mid`, `Spike_04_Tip`** |
   | **modifiés (6)** | `Spike_01`, `Spike_01_Mid`, `Spike_01_Tip`, `Spike_02`, `Spike_02_Mid`, `Spike_02_Tip` |

   44 nœuds avant, 44 après, **mêmes noms** (contrat de noms intact). `Body` identique : les `root`
   n'ont pas bougé, donc les mâts non plus.

**Autrement dit : la candidate est techniquement irréprochable. Le refus est un refus de forme.**

---

## 3. Le seuil : ce que le retournement casse

### La mesure

Distance surface à surface entre épines voisines, sur le maillage (nuages complets + BVH dans les
deux sens), en 3D et **projetée en vue de dessus** — c'est la projection qui dit ce que l'œil verra
sous une caméra à 20° de la verticale :

| | dépôt | candidate | variation |
|---|---|---|---|
| jour `Spike_02` ↔ `Spike_03` (3D) | 1 516,3 mm | **159,0 mm** | **−89,5 %** |
| jour `Spike_02` ↔ `Spike_03` (projeté) | 1 515,6 mm | **155,5 mm** | −89,7 % |
| jour `Spike_01` ↔ `Spike_04` (3D) | 1 486,4 mm | **1 171,1 mm** | −21,2 % |
| écart angulaire minimal entre deux axes | **40,3°** | **5,4°** | −87 % |
| éventail des quatre axes (écarts triés) | 40,3 / 52,3 / 130,3 / 137,1° | **5,4 / 29,0 / 46,8 / 278,8°** | |
| corde des quatre épines | 5,78 / 5,06 / 4,49 / 2,68 m | **5,85 / 5,06 / 4,49 / 2,68 m** | hiérarchie intacte |
| aire de silhouette, vue de dessus | 99,518 m² | **99,636 m²** | +0,1 % |
| aire de silhouette, vue de jeu (20°) | 93,966 m² | **94,233 m²** | +0,3 % |
| largeur hors-tout | 11,0313 m | **11,3112 m** | +2,5 % |

Les deux premières valeurs de « jour » du dépôt (1 486 et 1 516 mm) **retrouvent exactement celles
du rapport de `BRIEF-0045`** (1 487 et 1 516 mm) : l'instrument est le même, et il est étalonné.

**Ce n'est pas l'aire de silhouette qui se perd — elle ne bouge pas — c'est la SÉPARATION des
membres.** `BRIEF-0041` a construit son asymétrie sur quatre bras « ni la même longueur ni le même
espacement », dont « aucune paire n'est le miroir d'une autre ». À 5,4° et 159 mm, `Spike_02` et
`Spike_03` ne sont plus deux bras : c'est un bras fourchu.

### Le regard

Panneaux « AVANT » et « APRÈS » de `BRIEF-0080-planche-quatre-vues.png`, vues de dessus
orthographiques (mêmes champ, même éclairage, même échelle métrique), **présentées après
`FACING_PLAYER`** — c'est-à-dire exactement l'orientation que le joueur voit, le joueur en bas.

- **AVANT** : quatre appendices isolés qui rayonnent dans quatre directions, deux vers le joueur,
  deux vers le haut de l'écran. Ça lit « créature ».
- **APRÈS** : deux paires de cornes presque parallèles, une par flanc, dans un plan symétrique.
  Ça lit « masque à antennes ». Sur le flanc bâbord (à droite de l'image, `Spike_02` + `Spike_03`)
  les deux lames se touchent presque : à la taille de jeu elles fusionneront.

Les deux images disent la même chose que les deux chiffres. C'est ce faisceau-là qui déclenche le
seuil du brief : *« asymétrie perdue »*.

---

## 4. Pourquoi la largeur de coque doit augmenter — et pourquoi ça ne se négocie pas

`Spike_02` part de sa racine à l'azimut 165,6°. Pour viser le joueur, il lui faut atteindre le
secteur avant-bâbord, **où `Spike_03` est déjà**, et `Spike_03` est gelée. Deux routes, deux
impasses, mesurées sur le maillage :

- **Par l'intérieur** (entre la coque et `Spike_03`) : le couloir est **fermé**. À l'azimut 205°,
  le bord de coque est à r = 4,89 m et le flanc interne de `Spike_03` à r = 5,00 m — **11 cm**, et
  l'épaule de `Spike_03` y passe. Plus près de l'axe, on entre dans la piste de la coquille
  (r ≤ 3,76 : `SHELL_TRACK`), c'est-à-dire sous les plaques.
- **Par le dessus ou par le dessous** : impossible. Au-dessus, il faudrait culminer à ~1,65 m, donc
  dépasser le noyau (+1,592) — `BRIEF-0041` exige que le noyau soit le point le plus haut — et
  crever le plafond de hauteur (3,20 m pour 3,162 aujourd'hui : il reste 3,8 cm). En dessous, la
  descente n'est libre qu'au-delà du bord de coque ; ramenée vers l'axe par le pointage de ±40°,
  l'épine passe **sur le puits** (calculé sur la courbe d'essai : son milieu arrive à r = 2,6 m au
  pointage +40°, soit dans la piste de la coquille et à l'aplomb du noyau).
- **Par l'extérieur** : c'est la seule qui reste, et elle coûte de la largeur. `Spike_03` est à
  r = 5,22 m (az 205°), 5,87 (az 210°), 6,56 (az 216°) : pour rester dehors, `Spike_02` doit aller
  chercher x = −5,66 m. La borne −X étant tenue par `Spike_03` à −5,5157 m, **`Spike_01` doit
  grandir d'autant** pour que le pivot reste centré (tolérance ±20 mm) — d'où 11,31 m de large.

Le balayage chiffre ce que chaque mètre de largeur achète, à corde constante (≥ 4,70 m) :

| budget en x | jour `Spike_02`↔`Spike_03` | largeur hors-tout | contrat ±3 % |
|---|---|---|---|
| −5,55 m (largeur actuelle conservée) | **61 mm** | 11,03 m | ✅ |
| −5,66 m (retenu pour la candidate) | **201 mm** au mieux ; **159 mm** mesurés sur la courbe retenue* | 11,31 m | ✅ à 0,17 point près |
| −5,80 m | 460 mm | 11,63 m | ❌ 5,8 % d'écart |
| −6,25 m | 897 mm | 12,53 m | ❌ |

\* la courbe retenue n'est pas celle qui maximise le jour : à 201 mm, la marge de harnais de
`Spike_02` tombait à 110 mm au lieu de 176. On a préféré 17 mm de jour de moins et 66 mm de marge
de plus — le classement des candidates ne change pas d'un ordre de grandeur.

**Conserver la largeur actuelle donne 61 mm de jour** — deux lames qui se touchent. Et le jour de
475 mm que `BRIEF-0045` avait jugé acceptable **est hors contrat** dans ce sens-ci.

---

## 5. Le balayage : il n'y a pas de meilleure courbe

Balayage systématique de `ctrl × tip` pour `Spike_02` : grilles de 20 cm sur les quatre coordonnées
planes, ~35 000 géométries, filtrées par l'angle visé, la corde et le budget de boîte, puis
départagées par un modèle axe + rayon (la Bézier échantillonnée, moins les deux rayons d'épine).
Ce modèle est **étalonné et conservateur** : sur la coque du dépôt il rend 1 354 et 1 328 mm là où
le maillage en donne 1 516 et 1 486. Les finalistes ont ensuite été rebâties et remesurées sur le
maillage. Front de Pareto, à budget de largeur tenu (x ≥ −5,665) :

| corde de `Spike_02` | jour maximal atteignable | commentaire |
|---|---|---|
| ≥ 5,3 m | 169 mm | |
| ≥ 5,06 m (**la longueur actuelle**) | **201 mm** | la candidate en réalise 159 avec une meilleure marge de harnais |
| ≥ 4,7 m | 260 mm | |
| ≥ 4,5 m | 303 mm | à égalité avec `Spike_03` (4,49 m) : la hiérarchie s'écrase |
| ≥ 4,0 m | 386 mm | −21 % de longueur |
| ≥ 3,5 m | 548 mm | −31 % |
| ≥ 3,0 m | 750 mm | le bras devient un moignon |

**Aucune combinaison ne rend à la fois la longueur et la séparation.** Le raccourcissement est un
mauvais échange : il achète du jour métrique et **détruit l'écart angulaire** (mesuré sur la
variante à 4,30 m : jour 325 mm mais éventail minimal **3,9°**, et `Spike_02` passe sous `Spike_03`
en longueur — exactement l'inversion de hiérarchie que `BRIEF-0045` avait refusée pour lui-même).

---

## 6. La provision de braquage à ±40° : ce qu'elle coûte, et ce qu'elle ne cause pas

Le brief demande de trancher ce point plutôt que de payer une arche à l'aveugle. Mesure, sur les
deux courbes retenues, en faisant varier le seul `ctrl.z` (harnais du script, 25 poses par épine) :

| `ctrl.z` | `Spike_01` racine / flexion | `Spike_02` racine / flexion | verdict (référence : 190,3 / 87,2 mm) |
|---|---|---|---|
| **1,16 (plat)** | 198,7 / **0,0 mm** | 131,5 / **0,0 mm** | ❌ **mord** — le build refuse d'exporter |
| 1,35 | 244,8 / 59,9 | 143,4 / 9,7 | ❌ sous la référence |
| 1,45 | 269,5 / 107,8 | 155,5 / 50,5 | ❌ `Spike_02` sous la référence |
| **1,55 (retenu)** | 294,6 / **129,9** | 176,1 / **91,4** | ✅ au-dessus de la référence |

C'est **le même verdict qu'en 0045, en miroir** : à plat, une épine avant braquée de 40° revient
vers l'axe et mord la coque (`Spike_01_Mid` au pointage −40°, `Spike_02_Mid` au pointage +20°).
Le prix est une **arche de +0,39 m sur `ctrl.z` de `Spike_01` et +0,41 m sur celle de `Spike_02`**
(pointes remontées de 1,00 → 1,10 et 0,96 → 1,10). Elle reste **sous la rotule d'épaule** : crête de
maillage 1,497 → 1,528 m, très en dessous du noyau (1,592 m), **hauteur de coque inchangée**
(3,1620 m).

**Et sans la provision** (mêmes courbes, `ctrl.z` plat, harnais rejoué à pointage 0° et flexion
±25°) :

| | `Spike_01` racine / flexion | `Spike_02` racine / flexion |
|---|---|---|
| plat, sans braquage | **277,8 / 130,2 mm** | **185,7 / 95,3 mm** |

Les deux épines plates dégagent **mieux que la coque actuelle** (190,3 / 87,2 mm). Donc :

> **La provision ±40° est bien le seul obstacle à des épines planes** — et rien dans le code ne la
> franchit depuis la suppression de `_spine_track` et `SPINE_TRACK_DEG`. Si elle est abandonnée,
> l'arche disparaît d'une ligne (`ctrl.z` de 1,55 à 1,16 / 1,14) sans rien coûter d'autre.

**Mais l'arche n'est pas la raison du refus.** Le jour de 159 mm, l'éventail à 5,4° et les 11,31 m
de large sont des grandeurs **planes** : elles sont identiques avec ou sans arche, avec ou sans
provision. Relâcher `SPIKE_DEG` ne rachète rien de ce qui motive le refus.

---

## 7. Angles morts connus (à ne pas confondre avec ce brief)

- **Le harnais ne mesure jamais une épine contre la coquille, ni contre une autre épine.** Les deux
  chiffres qui décident ici — jour entre voisines, plaque en chute contre épine — viennent d'outils
  écrits pour ce rapport. Le second dit que, **sur la coque actuelle**, une plaque qui tombe traverse
  une épine dans toutes les conventions sauf une. Ce n'est pas l'objet de ce brief, c'est un sujet à
  part entière (§8, suggestion 2).
- **Deux conventions d'azimut de plaque coexistent** dans le dépôt : `PLATES` du script
  (−28 / 26 / 80 / 134°) et `base_angle = TAU·i/alive` du runtime (0 / 90 / 180 / 270°, ou 120°
  quand il ne reste que trois plaques). La chute est calculée avec la seconde et la géométrie est
  posée avec la première ; c'est ce désaccord qui produit les 0,0 mm ci-dessus.
- **La coque n'a pas été vue en jeu**, seulement en rendu Cycles orthographique à l'angle de la
  caméra de jeu. Ici, ce qui est jugé est une séparation de 159 mm sur une coque de 11 m : le rendu
  suffit à la voir, mais la règle du dépôt reste de juger en jeu.
- **`./scripts/check.sh` n'a pas été exécuté** : aucun fichier moteur n'a été touché (le seul ajout
  est une image dans `docs/`), et le `.glb` du dépôt est bit-à-bit celui d'avant.

---

## 8. Ce que je propose

### V1 — retourner `Spike_01` seule (prête à appliquer, mesurée, regardée)

Le blocage est **entièrement** du côté bâbord : c'est `Spike_03`, gelée, qui bouche le secteur de
`Spike_02`. Côté tribord, `Spike_04` est un moignon de 2,68 m et laisse la place.

```python
"Spike_01": ctrl = (5.75, -0.40, 1.55)   tip = (5.40, -6.20, 1.10)
```

Mesures (build complet, contrat passé) :

| | dépôt | V1 |
|---|---|---|
| axes en jeu | +68,7 / +109,0 / −120,7 / −68,5° | **−45,0** / +109,0 / −120,7 / −68,5° |
| épines qui visent le joueur | 2 sur 4 | **3 sur 4** |
| jour `Spike_01`↔`Spike_04` | 1 486 mm | **1 029 mm** |
| jour `Spike_02`↔`Spike_03` | 1 516 mm | **1 516 mm** (intact) |
| écart angulaire minimal | 40,3° | **23,4°** (comparable aux 26,8° acceptés en 0045) |
| harnais épines | 190,3 / 87,2 mm | **190,3 / 87,2 mm** (inchangé : le pire cas est ailleurs) |
| bbox | 11,0313 × 3,1620 × 13,9972 | **11,0294 × 3,1620 × 13,9972** |
| triangles | 27 710 | 27 734 |

Elle ne coûte **ni largeur, ni marge, ni longueur** ; elle coûte une arche (même mécanique qu'au §6)
et 457 mm de jour côté tribord. Panneau « VARIANTE V1 » de la planche. **Je ne l'ai pas livrée
parce que le brief demande les deux épines** : livrer la moitié d'une commande sans le dire serait
exactement l'erreur que 0080 corrige. C'est au concepteur de dire si le périmètre change.

### V2 — les deux, au prix mesuré

Les triplets du §2 ; tout le prix est aux §3 et §4. À retenir si l'on juge que la cohérence du tir
vaut plus que l'asymétrie de la silhouette. Dans ce cas, **noter que la largeur passe à 11,31 m** —
la valeur `width_x = 11,00` du contrat mériterait d'être amendée plutôt que de vivre à 0,17 point de
sa tolérance.

### Autres pistes, si l'on veut vraiment les quatre épines vers l'avant

1. **Dégeler `Spike_03`.** Elle est bonne *en direction*, pas *en place* : c'est elle qui occupe le
   secteur dont `Spike_02` a besoin. La reculer de 20 à 25° d'azimut (sans changer son axe) rouvre
   le couloir et rendrait un éventail à quatre membres séparés. Un brief de deux lignes, et le
   balayage est déjà écrit.
2. **Déplacer la racine de `Spike_02`.** Elle est gelée par `_build_masts()` qui relit `root` pour
   poser le mât — mais rien n'interdit de bouger le mât avec elle. Un `root` reculé vers l'azimut
   140° donnerait à l'épine un secteur libre.
3. **Trancher sur `_spine_track`.** Si le braquage ne revient pas, retirer `SPIKE_DEG` du harnais
   rendrait toutes les épines plates et rendrait 40 à 90 mm de marge partout (§6). Si le braquage
   revient, il faudra de toute façon mesurer les épines **entre elles** : à 159 mm, deux voisines
   braquées de 40° se traversent, et rien ne le signalerait.
4. **Étendre `_clearance_table()`** aux épines contre la coquille et entre elles. Le code de mesure
   de ce rapport est reproductible et tiendrait dans le script.

---

## 9. Fichiers

| Fichier | État |
|---|---|
| `tools/blender/build_pale_leviathan.py` | **inchangé** |
| `assets/imported/models/bosses/pale_leviathan.glb` | **inchangé** — sha256 `98529ce703faf6dfe6e6b5b560f68ef01299394b757a961f26f1840a359353a4`, revérifié par deux builds |
| `docs/forge/output/BRIEF-0080-planche-quatre-vues.png` | **livré** — avant / après / V1 annotés dans le repère du jeu, plus les quatre vues de la candidate |
| `docs/forge/output/BRIEF-0080-report.md` | ce rapport |
| `assets/licenses/ASSET_PROVENANCE.csv` | une ligne ajoutée **pour la planche seulement** ; la ligne du `.glb` est intacte (son hash n'a pas changé) |
| `tools/blender/lib/aegis_kit.py` | **non touché** (gelé) |
| `scripts/`, `resources/`, `scenes/`, tests | **non touchés** |
