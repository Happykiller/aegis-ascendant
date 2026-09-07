# BRIEF-0105 — Rapport de forge : la poupe entre dans le budget

- **Brief** : `docs/forge/briefs/BRIEF-0105-la-poupe-entre-dans-le-budget.md`
- **Date** : 2026-09-07
- **Outils** : Blender 5.2.1 LTS (`blender-aegis`), toujours `-t 1`
- **Porte de qualité** : `./scripts/check.sh` → **ALL GREEN**, 957 tests, 7 757 assertions,
  0 échec, 0 erreur de parse. Aucun `.gd`, `.tscn` ni `.tres` touché.

---

## 0. Le résultat en une ligne

**60 020 triangles pour la poupe entière**, aux quantités du jeu, contre un budget de
80 000 — soit **75 % du budget**, et **1,9 % des 3 170 000 triangles livrés**. Les cinq
binaires pèsent **2,49 Mo** au lieu de **314,8 Mo**, soit **126 fois moins**.

Les quatre cibles unitaires du brief sont tenues, toutes les quatre.

| Pièce | livré | **après** | cible | quantité | total | budget |
|---|---:|---:|---:|---:|---:|---:|
| groupe moteur | 276 816 | **7 816** | ≤ 8 000 | ×3 | 23 448 | 24 000 |
| berceau | 157 104 | **5 848** | ≤ 6 000 | ×3 | 17 544 | 18 000 |
| ancrage | 54 640 | **900** | ≤ 900 | ×10 | 9 000 | 9 000 |
| bras (+ miroir) | 66 332 | **496** | ≤ 500 | ×20 | 9 920 | 10 000 |
| | | | | | **60 020** | **80 000** |

Marge restante : **19 980 triangles**, soit à peu près ce que le brief prévoyait.

---

## 1. ⚠️ Le renversement de méthode, et ce qui l'a imposé

Le brief demandait de décimer. **La décimation a été essayée, mesurée, regardée, puis
abandonnée.** C'est le fait le plus important de ce lot, et il ne se lit sur aucun
compteur.

### Ce qu'on voit quand on rabote

Quatre versions rendues au **même cadrage, à la caméra du jeu**, même lumière, même pose :

| Version | Triangles moteur | Ce que la capture montre |
|---|---:|---|
| `COLLAPSE` uniforme, ratio 0,26 | 7 633 | la nacelle rend une **tôle déchiquetée** : zigzag de triangles noirs sur tout le fût |
| ratio 0,42, grandes pièces figées | 8 124 | **dents noires** sur tous les capots, pire qu'avant |
| ratio 0,62 + désherbage | 7 938 | dents noires résiduelles sur les panneaux latéraux |
| **aucun `COLLAPSE`, désherbage seul** | **7 816** | **propre** — la même image qu'à 38 008 triangles, en plus simple |

### Pourquoi, et c'est topologique

Ce maillage **n'est pas une surface** : c'est une **pile de centaines de coques fermées**.
Un capot est une boîte de douze triangles. Un `COLLAPSE` qui lui en laisse sept ne le
simplifie pas — **il lui ouvre le flanc**. On voit alors la pièce sombre du dessous à
travers, et la coque se couvre d'un zigzag noir que rien ne signale : ni erreur, ni test,
ni compteur de triangles.

> **Un assemblage de pièces rigides ne se réduit pas en rabotant chaque pièce.
> Il se réduit en gardant MOINS DE PIÈCES, ENTIÈRES.**

### La conséquence, et elle est forte

**Aucun sommet de l'auteur n'a bougé.** Tout triangle livré est exactement le sien, à la
seule exception des pièces de révolution que `coarsen()` dé-subdivise (78 passes sur le
moteur, 8 sur l'ancrage, 4 sur le bras, 0 sur le berceau). La silhouette n'est donc pas
approchée : elle est **la même, avec moins de pièces**.

---

## 2. Les leviers, dans l'ordre de ce qu'ils rapportent

### Levier 1 — les biseaux : 81 % du fichier, et 0,23 pixel à l'écran

C'est le plus gros écart du lot et il ne se voit qu'en ouvrant le `.blend`.

| Pièce | source `.blend` | `.glb` livré | facteur | modificateurs `BEVEL` |
|---|---:|---:|---:|---:|
| moteur | 50 656 | 276 816 | ×5,5 | 1 282 sur 1 282 objets |
| berceau | 21 904 | 157 104 | ×7,2 | 948 sur 948 |
| ancrage | 10 144 | 54 640 | ×5,4 | 295 sur 295 |
| bras | 10 940 | 66 332 | ×6,1 | 401 sur 401 |

Tous sont des `BEVEL` à **2 segments**, larges de **1 à 12 mm**. À l'échelle de jeu
(0,870) et à la densité mesurée (§6), un biseau de 8 mm fait **0,23 pixel**. Il coûte
81 % du fichier et ne rend rien. Il part en entier, et avec lui les `WEIGHTED_NORMAL`
qui l'accompagnaient — les normales sont **dérivées** de la géométrie restante
(`ADR-0013`), jamais générées.

### Levier 2 — la visserie

Tout ce qui porte `09 | Vis et raccords` disparaît, comme le brief le demande.

| Pièce | triangles | le pire coupable |
|---|---:|---|
| moteur | 11 736 | `Rivet de blindage` ×384 = **10 752** |
| berceau | 7 024 | `Vis de face pylone` ×48 = 3 360 |
| ancrage | 1 560 | `Boulon hexagonal` ×38 = 760 |
| bras | 2 840 | `Boulon lateral` = 2 360 |

Un rivet de 6,3 cm fait **1,8 pixel** ; 384 d'entre eux coûtaient 21 % du moteur.

### Levier 3 — les conduites

Les tuyaux sont des **courbes**, pas des maillages : ils n'existaient pas dans le compte
du `.blend` et apparaissaient à l'export. Leur résolution est ramenée à `resolution_u = 1`
avant conversion. C'est la seule réduction du lot qui ne coûte aucune forme : la section
d'un tube de 10 cm ne vaut pas seize côtés à 4 pixels.

### Levier 4 — la dé-subdivision des pièces de révolution

⚠️ **Sans elle, le désherbage supprime la silhouette du moteur.** Mesuré : sans
`coarsen()`, le tri au rendement supprime `Couple structurel`, `Joint noir de couple`,
`Etage de tuyere` et `Levre acier` — les **bagues structurelles** et les étages de tuyère.
La nacelle devient un **fût nu ceint d'anneaux magenta**, et le blindage a disparu.

Ces pièces sont des tores réguliers à 512 triangles. `UNSUBDIV` divise la résolution de
leur grille par deux à chaque passe et **une bague reste une bague** — ce qu'un `COLLAPSE`
ne sait pas faire. Seules les pièces au-dessus d'un seuil d'**emprise à l'écran**
(`protect_area`) y passent.

### Levier 5 — le désherbage

Les pièces sont triées par **rendement : pixels par triangle**, et supprimées entières
jusqu'au budget.

⚠️ **Trier par taille seule ne marche pas, et c'est mesuré deux fois.** Une sangle de
4,86 m de tour et 3 cm d'épaisseur a une « plus grande dimension » de 4,86 m alors qu'elle
ne couvre presque rien : l'emprise est le **produit des deux plus grandes cotes**, pas la
plus grande. Et trier par emprise seule gardait, sur l'ancrage, une **couronne émissive de
508 triangles — 58 % du budget pour une lampe** — en supprimant la **semelle**,
c'est-à-dire la pièce par laquelle l'ancrage tient au berceau.

| Pièce | désherbé | les trois premiers noms |
|---|---:|---|
| moteur | 11 300 | `Surplaque asymetrique` 896, `Joint raccord` 768, `Raccord refroidissement` 768 |
| berceau | 4 480 | `Joint de palier` 1 280, `Palier porteur` 640, `Bague socket AR D` 320 |
| ancrage | 6 856 | `Couronne verrou` 1 440, `Oeil fixation coque` 768, `Collier piston` 736 |
| bras | 6 424 | `Ecaille Longeron bras` 672, `Temoin pivot` 640, `Anneau pivot` 640 |

Une chose qui n'a **pas** marché, pour mémoire : souder à 6 mm les îlots jointifs, afin de
rendre au `COLLAPSE` un chemin de contraction. Le bras y gagnait 9 triangles, **l'ancrage
en perdait 225** (930 → 1 155). La soudure crée des arêtes non-manifold qui *bloquent* le
collapse au lieu de l'ouvrir.

---

## 3. Les pièces mobiles, traitées à part — ce qu'elles coûtent

Elles portent une valeur **2,5 fois supérieure** au désherbage (`MOVING_VALUE`) : les
supprimer emporterait le mouvement avec la forme.

| Pièce | triangles mobiles | part du total | ce qui bouge |
|---|---:|---:|---|
| moteur | **3 024** | 39 % | 12 pétales, 4 pistons, anneau émissif, tuyère, 2 refroidissements |
| berceau | **2 968** | 51 % | 4 mâchoires, 4 verrous, 4 conduites détachables, 4 connecteurs, 2 protections, 2 rails |
| ancrage | **428** | 48 % | mâchoire articulée, 2 corps + 2 tiges de piston, verrou, 2 plaques, connecteur |
| bras | **428** | 86 % | bras principal, mâchoire mobile, corps + tige de piston, 2 blindages, patin |

Autrement dit : **sur le bras, presque tout le budget est de l'animation**, et sur le
berceau plus de la moitié. C'est le prix de dix-huit clips, et il est payé sciemment.

---

## 4. Le contrat de noms — diff **VIDE**

Le critère qui prime. Vérifié **sur les binaires**, source contre réduit, position monde
de chaque nœud, en descendant tout le graphe :

| Pièce | repères source | repères réduits | manquants | ajoutés | **écart maximal** |
|---|---:|---:|---|---|---:|
| moteur | 29 | 29 | aucun | aucun | **0,000000 mm** |
| berceau | 42 | 42 | aucun | aucun | **0,000000 mm** |
| ancrage | 16 | 16 | aucun | aucun | **0,000000 mm** |
| bras | 13 | 13 | aucun | aucun | **0,000000 mm** |

**100 repères sur 100, à l'identique.** La raison est structurelle et non chanceuse : tous
les `CTRL | ` sont des `Empty`, et la réduction n'agit **que** sur les maillages.

⚠️ **Et Godot les lit tels quels.** Le risque n'était pas la forge, c'était l'import : la
barre verticale et les espaces auraient pu être avalés par `validate_node_name()`. Contrôlé
sur la **scène importée** (`.godot/imported/*.scn`, décompressée) :

```
stern_engine       29 repères CTRL, AnimationPlayer présent
stern_cradle       42
stern_anchor       16
stern_arm          13     stern_arm_mirror  13
```

Les noms sortent **verbatim**, « `CTRL | Socket ancrage arriere` » compris.

---

## 5. `AA_Emissive_Engine` porte tout ce qui doit s'éteindre

Compté **sur le binaire**, matériau par matériau :

| Pièce | `AA_Hull` | `AA_Greeble` | **`AA_Emissive_Engine`** | images |
|---|---:|---:|---:|---:|
| moteur | 4 384 | 2 712 | **720** | **0** |
| berceau | 3 792 | 1 336 | **720** | **0** |
| ancrage | 688 | 176 | **36** | **0** |
| bras (et miroir) | 340 | 108 | **48** | **0** |

Les neuf slots de l'auteur sont repliés comme le brief le prescrit ; `AA_Trim` et
`AA_Panel` restent vides (la livraison ne contient ni liseré clair ni volume de faction).

⚠️ **L'émissif a une part RÉSERVÉE du budget** (`GLOW_SHARE = 0,14`), prise avant tout
désherbage. Sans elle, le tri au rendement laissait **zéro triangle émissif sur le bras**
et douze sur l'ancrage — logique et piégeux : une veine lumineuse est une petite pièce
chère en triangles, donc le pire rendement de la coque. Elle ne s'achète pas en pixels.

⚠️ **RÉSERVE : couper l'émission ne suffira PAS au blackout du LOT 8.** Mesuré sur la
cinquième vignette de la planche (berceau vide, `Emission Strength` mis à 0 sur le seul
`AA_Emissive_Engine`) : **4 480 pixels magenta → 3 605**, soit **−20 % seulement**. La
raison est dans le matériau du kit : l'albédo d'`AA_Emissive_Engine` **est** le magenta de
faction (0,694 / 0,047 / 0,332) contre 0,018 pour `AA_Hull` — **quarante fois plus clair**.
Émission coupée, la surface reste peinte en magenta et la lumière clé la révèle. Le
blackout devra donc **assombrir aussi l'albédo**, pas seulement l'émission. Ce n'est pas un
défaut de la réduction (le Long Cortège a exactement le même matériau), c'est une cote de
jeu à poser au LOT 8.

---

## 6. Les dix-huit clips

Comptés sur les binaires, canaux et durées, puis **amplitude par canal** comparée à celle
des binaires de l'auteur :

| Pièce | clips | canaux | écart d'amplitude maximal vs source |
|---|---|---:|---:|
| moteur | `Fonctionnement` `Endommage` `Detachement` | 66 / 66 / 66 | **0,00e+00** |
| berceau | `Intact` `Sous_contrainte` `Liberation` `Berceau_vide` | 60 × 4 | **0,00e+00** |
| ancrage | `Intact` `Endommage` `Ouverture` `Fermeture` `Rompu` | 27 × 5 | **0,00e+00** |
| bras | `Serre` `Ouverture` `Ouvert` `Fermeture` `Rupture` `Rompu` | 21 × 6 | **0,00e+00** |

**18 clips, cuits en clés** (`export_force_sampling`, mode `NLA_TRACKS`) : aucun pilote
Blender ne subsiste, conformément à `ADR-0046`. Rejoués après réimport dans Blender et
retrouvés dans la scène importée par Godot, avec son `AnimationPlayer`.

**La continuité `Liberation` → `Berceau_vide` survit** : dernière clé de `Liberation`
contre première clé de `Berceau_vide`, canal par canal, **écart maximal 0,000000** — la
même valeur que sur le binaire de l'auteur. Le berceau ne saute pas d'une pose à l'autre.

Une différence assumée avec l'auteur : son export du **moteur** omettait
`export_optimize_animation_keep_anim_object`, ce qui laissait 21 canaux mobiles seulement
dans `Fonctionnement`. Le nôtre en écrit 66 (22 nœuds × 3 chemins), constants compris,
comme le font déjà ses trois autres pièces. C'est **plus complet**, pas différent : les
amplitudes sont identiques au bit près, et les poses de fin de clip sont restaurées.

---

## 7. Les UV, et la densité mesurée

Dépliage en **projection en boîte** (`ak.box_project_uv`) à **0,70 tuile/m**, soit
**1,43 m par tuile** — la densité d'Ambry sur le Long Cortège (`AMBRY_TEXELS_PER_METER`),
et pour la même raison : ces pièces se voient bien plus près que les 500 m de bordé
(0,200 tuile/m). Aucune contrainte d'entier ne s'applique : rien ici ne joint un tronçon.

**`TEXCOORD_0` compté, jamais supposé** : 28 + 38 + 12 + 10 + 10 primitives, **0 sans UV**.

| Binaire | moyenne | m/tuile | min | max | **anisotropie max** |
|---|---:|---:|---:|---:|---:|
| `stern_engine` | 0,679 | 1,47 | 0,423 | 0,700 | **1,65** |
| `stern_cradle` | 0,694 | 1,44 | 0,417 | 0,700 | **1,68** |
| `stern_anchor` | 0,696 | 1,44 | 0,464 | 0,700 | **1,51** |
| `stern_arm` (et miroir) | 0,694 | 1,44 | 0,495 | 0,700 | **1,41** |

La borne théorique d'une projection en boîte est √3 = 1,732 : on est dessous partout.
Le brief ne demandait pas de dépliage continu ; **la planche de contrôle au damier est
livrée quand même** (vignette 6 de `BRIEF-0105-etats.png`), à la perspective du jeu — les
cases y sont carrées et de taille égale d'une pièce à l'autre.

---

## 8. L'arbitrage de la texture — la comparaison, pas la décision

`docs/forge/output/BRIEF-0105-arbitrage-texture.png` — deux vignettes 1920 × 1080, **même
cadrage, même lumière, même pose, et géométrie strictement identique** (la réduction étant
une suppression, elle donne le même maillage dans les deux chaînes).

| | Option A — les onze atlas | Option B — PBR par facteurs |
|---|---:|---:|
| Coût **Git LFS** des 5 binaires | **236,0 Mo** | **2,49 Mo** |
| Part du LFS actuel du dépôt (639 Mo) | **+37 %** | +0,4 % |
| Images embarquées par pièce | 11 | **0** |
| Luminance moyenne du sujet | 0,203 | 0,186 |
| Écart-type de luminance (contraste de surface) | **0,0972** | 0,0780 |

Ce que les atlas achètent est mesurable : **+25 % de contraste de surface** pour **+8,8 %
de luminance**. Ce n'est donc pas « plus clair », c'est **plus détaillé** — usure, lignes
de panneau, grain directionnel sur les tranches.

Ce qu'ils coûtent est mesurable aussi : **+233,5 Mo de LFS**, et un niveau qui n'a
aujourd'hui **aucune image** dans sa coque de 500 m.

**La forge ne tranche pas** (`ADR-0006` : l'opérateur décide en regardant). La commande qui
reconstruit l'option A est dans `assets/source/models/stern/README.md` ; elle écrit dans
`build/`, gitignoré.

---

## 9. Déterminisme

`./scripts/build-hull.sh --check` ne s'applique pas (le script de réduction n'est pas un
`tools/blender/build_*.py`), mais son **invariant** est vérifié à l'identique et une fois
de plus qu'il ne le demande :

```
3 exécutions de reduce_stern.py -- --all, sha256 des 5 binaires : ZÉRO OCTET DIVERGENT

01113f89f2beb4e708023e1515cc05ad6a213a1669c9bc7acb6ceb567645bfcb  stern_engine.glb
be63b2d619e9a644b813a391688d95565515cd4479bb1e076d819d5b50e322ac  stern_cradle.glb
b18e4e274162e5a875048938d089bc87e8bb57eafe2c489374d4534f7f5cdf56  stern_anchor.glb
d7480cd6a38808f1757aeb438be356d844ec418ccb7b5529c8e2099da6e6400f  stern_arm.glb
fbdd801b159d298a07cfaa16c54c90d5aad8b05d771eb6d85615a36e447c32e1  stern_arm_mirror.glb
```

`-t 1` partout, comme l'exige `howto-determinisme-des-coques.md`.

---

## 10. Rendu et REGARDÉ — les quatre états, plus deux

`docs/forge/output/BRIEF-0105-etats.png` — **six vignettes de 1920 × 1080**, la résolution
du jeu, à la caméra du jeu `(0 ; 14 ; 5)` / FOV 62 vertical, avec les trois directionnelles
du niveau et **aucune ombre portée** (le rig est *importé* de `build_long_cortege.py`, pas
recopié).

Les trois groupes sont montés aux cotes **lues** dans `resources/levels/long_cortege_stern.tres`
— `asset_scale`, `central_scale`, `engine_spacing`, `deck_y`, `engine_seat`, `socket_*`,
`hold_plane_y`, `lateral_anchors`, `central_anchors` — par le même calcul que
`cortege_engine.gd`. Une cote qui bougerait dans la Resource invalide la planche au lieu
de la laisser mentir.

| # | Vignette | Ce qu'elle montre |
|---|---|---|
| 1 | **moteur intact** | `Fonctionnement` / `Intact` / `Intact` / `Serre` |
| 2 | **moteur endommagé** | `Endommage` / `Sous_contrainte` / `Endommage` / `Serre` |
| 3 | **arrachement en cours** | `Detachement` / `Liberation` / `Rompu` / `Rupture`, image 98 sur 121 |
| 4 | **berceau vide** | aucun moteur, trois berceaux morts — l'image qui clôt le niveau |
| 5 | berceau vide, **émissif coupé** | la preuve du contrat de matériaux (voir §5) |
| 6 | **damier UV** | à la perspective du jeu, 0,70 tuile/m |

Ce que la lecture donne : les trois groupes se distinguent, le central se lit comme plus
gros, la tuyère pointe vers le haut de l'écran, les veines magenta sont les seuls accents
et elles ne volent pas la lisibilité au tir allié (cyan). Le berceau vide **lit comme un
cadre vide** : quatre pylônes, mâchoires ouvertes, raccords débranchés.

⚠️ Les **bras** sont posés par la forge, pas par le jeu : `cortege_engine.gd` ne les monte
pas encore (c'est le LOT 7). Ils sont aux quatre coins de chaque berceau, mâchoire tournée
vers le fût — douze au total sur la planche, là où le brief en prévoit une vingtaine.

---

## 11. ⚠️ Cinq réserves, dont deux qui contredisent une cote du jeu

### 11.1 — Le px/m du brief n'est pas celui de la poupe : **32,7**, pas 45,8

Le brief raisonne sur **45,8 px/m**. C'est la densité du **corridor**, dont le pont est à
`y = −4,30`. La poupe se joue à `deck_y = −11,85`, soit **7,55 m plus bas**, donc plus loin
de la caméra :

```
pont à −4,30   : profondeur 19,47 m,  cadre 41,60 m  ->  46,2 px/m   (43,4 en profondeur)
pont à −11,85  : profondeur 27,51 m,  cadre 58,77 m  ->  32,7 px/m   (30,7 en profondeur)
```

Un tiers de moins. Toutes les estimations de lisibilité du brief sont donc **optimistes de
40 %** : un boulon de 3 cm ne fait pas 1,4 px mais **0,85 px** à l'échelle 0,870, et une
bague de 8 cm 2,3 px et non 3,7. Cela ne change aucune décision — cela les renforce
toutes.

*C'est une mesure, pas une demande de changement de cote.*

### 11.2 — Le blackout du LOT 8 ne prendra pas sur l'émission seule

Voir §5 : couper l'émission ne retire que **20 %** des pixels magenta. L'albédo
d'`AA_Emissive_Engine` est le magenta de faction, 40 fois plus clair que la tôle. **C'est
au jeu de trancher**, pas à la forge : soit `CortegeSkin` assombrit l'albédo du matériau
mort en plus de son émission, soit la poupe morte restera rose. Le même constat vaut pour
les 500 m de bordé, qui partagent ce matériau.

### 11.3 — Ce qui a été perdu, nommé

Ce qui disparaît n'est pas « du détail en général » :

- **le moteur** perd ses 384 rivets de blindage, ses manchons, ses inserts de sangle, ses
  aubes de chambre, six blindages de corps sur seize, son **cœur lumineux** et son **halo**
  (512 triangles chacun, dans le fût, invisibles depuis la caméra du jeu) ;
- **le berceau** perd ses joints de palier, ses bagues de socket et ses corps de socket
  (les logements d'ancrage restent, ce sont leurs finitions qui partent) ;
- **l'ancrage** perd sa couronne de verrou (1 440 triangles, ramenés à 36 d'émissif), ses
  yeux de fixation, ses colliers de piston et ses rotules ;
- **le bras** perd ses écailles de longeron, son anneau de pivot, son cœur émissif et ses
  rotules — il ne lui reste que **8 groupes**, dont 86 % d'animation.

**L'ancrage et le bras sont ceux qui souffrent le plus** : à ×10 et ×20, 900 et 500
triangles ne laissent que le strict nécessaire. L'ancrage à 900 triangles est une semelle,
une mâchoire, deux plaques latérales et un verrou. À 2,4 m × 0,870, soit **68 px de long**,
c'est le bon ordre de grandeur — mais si la phase les met un jour au premier plan, il
faudra une seconde version.

### 11.4 — Les sources pèsent 243 Mo de LFS

`ADR-0048` demande la source, et elle est là : les quatre `.blend` **octet pour octet**,
sans retouche. Mais ils portent chacun onze atlas 2048² empaquetés, soit **243 Mo**
(+38 % du LFS actuel du dépôt). Si l'option B est retenue définitivement, dépaqueter les
images les ramènerait à ~24 Mo — au prix de rendre **l'option A irreproductible depuis le
dépôt seul**. C'est un arbitrage de coût, pas de technique : la forge le signale et n'en
décide pas.

### 11.5 — Ce que le lot n'a pas fait

- **Le facteur d'échelle de D2 n'a pas été re-mesuré.** Le brief l'interdit explicitement
  (« ces cinq valeurs ne sont pas à toucher ») et je n'ai touché à aucun `.tres`. Pour
  information, la mesure que le LOT 5 attendait : avec `asset_scale = 0,870`,
  `anchor_reach()` vaut `10,28 + 3,70 × 0,870 = **13,50 m**` — dans les `|x| ≤ 14` visés,
  avec **0,50 m de marge**. En rejouant la chaîne complète (`engine_spacing` étant lui-même
  dérivé de `k` : `11,19 k × (1 + 1,06)/2 + 0,25`), la portée s'écrit `15,226 k + 0,25`, et
  le plus grand facteur admissible est **k = 0,903** pour `|x| ≤ 14` (et 0,875 pour la borne
  de 13,6 du brief). Le facteur **peut donc remonter de 0,870 à 0,903**, soit +3,8 % de
  taille pour toute la poupe. C'est au concepteur de décider s'il le fait suivre — la forge
  n'a touché à aucun `.tres`.
- **Aucun coût GPU mesuré.** Le LOT 5 le demande, pas ce brief, et un relevé n'a de sens
  qu'une fois les pièces montées en jeu — ce que je ne peux pas faire sans toucher au code.
- **Aucune texture produite** (`ADR-0028`) : ni peinte, ni générée, ni cuite. Le damier de
  la vignette 6 n'existe que dans le rendu.

---

## 12. Livrables

| Fichier | Ce que c'est |
|---|---|
| `assets/imported/models/backgrounds/stern_engine.glb` | groupe moteur, 7 816 tri, 1,22 Mo |
| `assets/imported/models/backgrounds/stern_cradle.glb` | berceau, 5 848 tri, 0,79 Mo |
| `assets/imported/models/backgrounds/stern_anchor.glb` | ancrage destructible, 900 tri, 0,19 Mo |
| `assets/imported/models/backgrounds/stern_arm.glb` | bras d'ancrage, 496 tri, 0,15 Mo |
| `assets/imported/models/backgrounds/stern_arm_mirror.glb` | son miroir, 496 tri, 0,15 Mo |
| `assets/source/models/stern/stern_{engine,cradle,anchor,arm}.blend` | les sources tierces, intactes (`ADR-0048`) |
| `assets/source/models/stern/reduce_stern.py` | la réduction — **la seule chose entre la source et le binaire** |
| `assets/source/models/stern/render_stern_plates.py` | les planches, à la caméra du jeu |
| `assets/source/models/stern/README.md` | comment on rejoue tout ça |
| `docs/forge/output/BRIEF-0105-etats.png` | six vignettes 1920 × 1080 |
| `docs/forge/output/BRIEF-0105-arbitrage-texture.png` | deux vignettes, même cadrage |
| `docs/forge/output/BRIEF-0105-report.md` | ce document |

Douze lignes ajoutées à `assets/licenses/ASSET_PROVENANCE.csv`, aucune ligne existante
modifiée.
