# BRIEF-0116 — Rapport de forge : la hiérarchie des valeurs d'Ambry

- **Brief** : `docs/forge/briefs/BRIEF-0116-ambry-la-hierarchie-des-valeurs.md`
- **Planche de concept** (le contrat) : `assets/reference/concepts/ambry_concept_sheet_2026-09.png`
- **Suite de** : `BRIEF-0115` et du correctif de valeur `e55bba3`
- **Date** : 2026-09-14 · **Outil** : Blender 5.2.1 LTS (`blender-aegis`), toujours `-t 1`
- **Livrables** : `tools/blender/build_long_cortege.py`,
  `assets/imported/models/backgrounds/long_cortege.glb`,
  `docs/forge/output/BRIEF-0116-planche.png`, ce rapport
- **Périmètre respecté** : aucune image, aucun `.gd`, `.tscn`, `.tres` ; **aucune géométrie
  touchée** (5 300 triangles avant, 5 300 après, au triangle près) ; aucun commit.

---

## 0. La réponse en une ligne

**Le plafond de valeur ne rendait pas seulement les sept modules égaux : il rendait égales TOUTES
les matières claires d'Ambry.** Six slots — la bâche, la coque, le pont, les futurs paliers, la
peinture du pas — tenaient dans 13 % de luminance et couvraient 56 % des pixels de la pièce. Ce lot
les étage : trois paliers de tôle, un pont descendu sous le bâti, un pas repeint en or, une bâche
rendue au bleu. **Rien n'a bougé d'un millimètre** et le sommet reste `−3,200`.

| Mesuré sur la bande d'Ambry, cadre poupe | AVANT | APRÈS |
|---|---:|---:|
| luminance médiane | 105,2 | **75,8** |
| tons moyens (60–160) | 27,1 % | **43,8 %** |
| quasi-blanc (> 200) | 11,6 % | **8,0 %** |
| saturation | 22,8 % | **23,6 %** |
| écart-type de luminance | 70,5 | 60,3 |
| slots clairs tenant dans 13 % de luminance | **6 (56 % des pixels)** | **2 (23 %)** |

---

## 1. ⚠️ L'instrument d'abord, parce que le lot précédent a été jugé sur le mauvais

> **Le mode `--ambry` du générateur rend le `.glb` NU. Depuis `e55bba3`, ce n'est plus ce que le
> jeu montre — et le défaut est totalement silencieux.**

`CortegeSkin` retouche chaque matière d'Ambry **à l'import**, et rien de tout cela n'est dans le
binaire : plafond de valeur (0,58 de luminance linéaire), réchauffement `AMBRY_WARM`, douze cartes,
`uv1_scale` 0,35, `normal_scale` 1,60. Juger Ambry sur la planche du générateur, c'est juger un
ivoire à **0,824** de luminance quand le joueur en voit un à **0,58**. **C'est exactement ce qui a
fait rejeter la bâche bleue au `BRIEF-0115`** : elle faisait un trou dans un blanc qui, en jeu,
n'existait déjà plus.

Les vignettes de ce lot sont donc rendues avec un **rejeu de `CortegeSkin`** par-dessus l'import
glTF. La recette, pour qu'elle soit refaisable :

| Élément | Source | Valeur |
|---|---|---|
| caméra | `scenes/gameplay/graybox.tscn:29` | `(0 ; 14 ; 5)`, FOV 62 **vertical**, plongée 70° |
| trois lumières | même fichier | clé 1,55 (1 ; 0,976 ; 0,925) · rim 0,70 · remplissage 0,55 ; **énergie × π** (Blender divise par π, Godot non) ; ombre portée sur la clé seule |
| ambiante | `resources/graphics/space_environment.tres` | `(0,55 ; 0,62 ; 0,78) × 0,8`, visible des rayons **non-caméra** seulement (nœud *Light Path*), sans quoi le fond spatial s'éclaire |
| étalonnage | même fichier | AgX, `exposure` = log2(1,4), puis luminosité 1,02 / contraste 1,08 / **saturation 1,46** en numpy |
| matières | `scripts/fx/cortege_skin.gd` | plafond + `AMBRY_WARM` sur l'albédo, `_mul` en multiplication, `_nrm` à 1,60, `_rough` canal R, `uv1_scale` 0,35 ; `AA_Trim` amorti, `AA_Panel` × 0,45 |
| masque de mesure | — | l'emprise d'Ambry **projetée par la même caméra**, jamais un rectangle à vue de nez |
| masque par slot | — | une **passe d'identifiants** (chaque matériau devient un aplat émissif codé), donc un compte par slot et non une estimation |

Un avertissement a été posé dans le docstring de `render_ambry_plate()` : **aucun verdict de
couleur ne doit sortir de ce mode tant qu'il ne rejoue pas la peau.** Le replier dans l'outil est
une bonne idée et c'est votre périmètre, pas le mien — c'est une trentaine de lignes.

⚠️ **Conséquence à retenir pour lire les chiffres** : mon instrument n'est pas le vôtre. Il ne
reproduit ni le glow de Godot ni son ordre d'opérations, et il lit **plus clair et plus saturé**
que vos captures en jeu (médiane 105 là où vous mesurez 86, saturation 22,8 % là où vous mesurez
17,7 %). **Ce sont donc les ÉCARTS avant/après qui transfèrent, pas les valeurs absolues** — et
tous sont mesurés sur le même masque, la même lumière et le même étalonnage.

---

## 2. Le vrai sujet : les modules — et le piège du plafond

### 2.1 Ce que la mesure par slot montrait, AVANT

| slot | part des pixels | luminance | saturation |
|---|---:|---:|---:|
| `AA_Window_Ambry` | 2,56 % | 222,2 | 34,2 % |
| `AA_Cloth_Ambry` (bâche) | 0,96 % | **194,4** | 3,7 % |
| zone du futur palier B | 3,13 % | **187,1** | 6,5 % |
| zone du futur palier C | 5,19 % | **186,7** | 6,0 % |
| `AA_Hull_Ambry` | 22,14 % | **181,4** | 5,0 % |
| `AA_Deck_Ambry` | 23,15 % | **173,7** | 5,0 % |
| marquages du pas (sur le pont) | 1,20 % | **171,7** | 3,8 % |

**Six slots dans 13 % de luminance, sur 56 % des pixels d'Ambry.** Votre diagnostic — « ils
comptent comme une masse » — était juste, et il portait plus loin que les sept modules : le
plafond de valeur rabat **toute** matière claire à 0,58, donc l'ivoire de coque `#EDEAE3` (0,824)
**et** l'ivoire de pont `#DDDCD2` (0,712) en ressortent **exactement égaux**. La seule différence
mesurée (4 %) venait du fini, pas de la couleur.

### 2.2 ⚠️ Le piège : un palier défini sur la charte est annulé par le plafond

C'est le point qui a décidé de toute l'implémentation, et il n'est pas intuitif.

> `#EDEAE3` a une luminance linéaire de **0,824**. Un « ivoire 15 % plus sombre » vaut **0,571**.
> Le premier est rabattu à 0,58, le second passe intact à 0,571. **Les deux modules sortent à
> 1,5 % l'un de l'autre.**

Un palier posé naïvement sur la couleur de charte est donc **anéanti par le correctif même qui
rend les textures visibles**. Les paliers se calculent ici **sous le plafond** : on part de la
couleur déjà rabattue, et on l'assombrit en **valeur perçue** (espace sRGB), parce que « 15 % plus
sombre » veut dire 15 % pour l'œil, pas 15 % d'une grandeur linéaire que personne ne voit.

### 2.3 Et un albédo n'arrive pas entier à l'écran

Premier tirage, facteurs 0,85 et 0,70 comme le brief les proposait. Mesure pixel par pixel sur les
seules surfaces qui avaient changé :

| facteur d'albédo | rendu attendu | **rendu mesuré** |
|---:|---:|---:|
| 0,85 | 0,85 | **0,91** |
| 0,70 | 0,70 | **0,82** |

40 % de la lumière qui arrive à l'écran ne vient pas de l'albédo — spéculaire d'une ambiante à 0,8,
rebonds des quarante-six fenêtres, diélectrique à `roughness` 0,45 — et cette part-là ne
s'assombrit pas avec lui. Le modèle se cale en une ligne, `rendu = 0,60 × albédo + 0,40`, vérifié
sur les deux paliers du même tirage. **Les facteurs livrés sont donc 0,75 et 0,50, pour obtenir
−15 % et −30 % À L'ÉCRAN.**

### 2.4 Ce qui est livré

Trois slots neufs, **en fin de table** : aucun des dix-neuf index précédents ne bouge.

| slot | hex | facteur | tri | part des pixels | **luminance rendue** | écart à l'ivoire |
|---|---|---:|---:|---:|---:|---:|
| `AA_Hull_Ambry` (palier A) | `#EDEAE3` | — | 634 | 22,14 % | **180,2** | — |
| `AA_HullB_Ambry` | `#989692` | 0,75 | 108 | 3,13 % | **158,4** | **−12 %** |
| `AA_HullC_Ambry` | `#656461` | 0,50 | 96 | 5,19 % | **118,4** | **−34 %** |

⚠️ **Et leur suffixe est `_Ambry`, pas `_Ambry_B`.** Le brief proposait `AA_Hull_Ambry_B` ;
`CortegeSkin` choisit l'échelle d'UV par `name.ends_with("_Ambry")`, si bien qu'un slot nommé ainsi
serait retombé sur l'échelle du **bordé** — 2,86 m par tuile au lieu de 4,08 — le jour où on lui
aurait donné une carte. C'est mot pour mot le défaut que le `BRIEF-0115` a fermé, et il est tout
aussi silencieux. **Le suffixe reste en dernier.**

### 2.5 La répartition — trois générations, et aucun voisin au même palier

|  | palier | pourquoi |
|---|---|---|
| **M1** (2,18 × 2,80, parapet) | **A** | le bloc d'origine, contre le pas |
| **M2** (bâche) | **B** | annexe collée au flanc de M1 |
| **M3** (voûte, 2,10 × 2,25) | **C** | un **berceau** — une coque cintrée ne sort pas du même rouleau que des panneaux plats |
| **M4** (caisses) | **B** | remplissage |
| **M5** (solaire, 2,20 × 2,80) | **A** | le second bloc de la paire d'origine |
| **M6** (parabole) | **B** | deuxième génération, tôle re-roulée jamais peinte |
| **M7** (cuve) | **C** | le dernier appentis, soudé avec ce qui restait |

Deux contraintes ont décidé, et aucune n'est décorative :

1. **Les huit adjacences portent toutes un écart.** M1-M2, M1-M3, M3-M4, M3-M5, M4-M5, M5-M6,
   M5-M7, M6-M7 : pas un couple de voisins ne partage un palier. Ni damier (l'alternance n'est pas
   régulière), ni dégradé monotone de la proue vers la poupe.
2. **Le palier va au plus VU, pas au plus petit.** M3 (voûte, 5 560 px à l'écran) et M1 (parapet,
   9 072 px) sont les deux plus grandes surfaces de tôle d'Ambry : les laisser au même palier
   revenait à ne rien faire. Les trois modules bas ont leur toit encombré — une bâche, trois
   caisses, une cuve — et n'offrent presque pas de tôle : **un palier posé là ne se serait vu sur
   aucune capture.** C'est pourquoi le premier tirage, qui mettait C sur M2/M4/M7, a été refait.

---

## 3. ⚠️ Le quatrième changement, celui que vous n'avez pas demandé : la rue descend

**Sept modules ré-étagés posés sur un sol de leur propre valeur restent une masse.** Le plafond
avait aussi collapsé le pont : coque 181,4 et pont 173,7, **4 % d'écart sur 45 % des pixels
d'Ambry**.

La planche tranche largement dans l'autre sens : ses coursives rendent **28 à 98** de luminance
quand ses toits rendent **147 à 186** — un rapport de 0,2 à 0,55. C'est cohérent avec la matière :
un **caillebotis** (`TEX-AMB-03/04`) est surtout du vide, il ne peut pas avoir la valeur d'une tôle
pleine.

La valeur se cale **entre deux murs**, pas sur un goût : la rue doit passer **sous** le plus sombre
des trois paliers de bâti (118) et rester **au-dessus** du pas d'appontage (67), que le brief exige
distinct de ce qui l'entoure.

| essai | albédo perçu | rendu | verdict |
|---|---:|---:|---|
| 1er | 0,30 | **70,7** | **refusé** — la rue et le pas confondus, critère cassé |
| **retenu** | **0,45** | **94,4** | 20 % sous la coque C, **29 % au-dessus du pas** |

⚠️ **C'est le seul changement de ce lot que le brief ne demande pas.** Il se défait en remettant
`_UNISON["trim"]` à l'entrée `AMBRY_DECK` de `AMBRY_MATERIAL_SPECS` — une ligne. Je le signale
haut parce qu'il porte 23 % des pixels d'Ambry et qu'il est responsable de la plus grande part de
la chute de médiane (105 → 76).

---

## 4. La bâche — rejugée, et le bleu revient (mais pas celui-là)

**Trois tirages, même cadrage, même lumière, mesurés sur les seuls pixels du slot** (vignette 6) :

| | luminance | saturation | rapport à l'ivoire (180,2) |
|---|---:|---:|---:|
| écru `#DDDCD2` (l'état précédent) | 194,4 | 3,7 % | 1,08 |
| **bleu délavé `#5B6486` — RETENU** | **132,1** | **31,3 %** | **0,73** |
| bleu profond `#1C2B5E` (celui du BRIEF-0115) | 84,0 | **59,9 %** | 0,47 |
| **la planche, sur sa propre vue gameplay** | **92,3** | **26,5 %** | **0,49** |

**Verdict : le bleu délavé.** Trois raisons, dans l'ordre de poids :

1. **La planche ne montre pas le bleu profond.** Sa bâche rend (83, 93, 114) : un bleu **délavé**,
   à 26,5 % de saturation. `#1C2B5E` est à 70 %. Une bâche de quarante ans sous la lampe n'est pas
   un panneau de coque neuf — on la construit donc comme telle, par un mélange **tracé** des deux
   hex de la charte (`panel` tiré de 30 % vers `hull`), jamais par un hex inventé.
2. **Votre verdict de 2026-09-13 avait raison sur la RAISON, pas sur le remède.** Rendu
   aujourd'hui, le `#1C2B5E` reste **l'objet le plus saturé des vingt-sept mètres** : 59,9 % quand
   rien d'autre sur Ambry ne dépasse 35 % (les fenêtres). Regardé (vignette 6, à droite), il ne lit
   pas comme du tissu, il lit comme un **décalque** — son propre modelé est écrasé. L'écru, lui,
   était invisible (1,08 fois l'ivoire : il *était* l'ivoire).
3. **Sur la luminance seule, le bleu profond colle mieux à la planche (0,47 contre 0,49).** Je le
   dis parce que c'est vrai et que ça tempère le verdict : si vous voulez plus de couleur, le
   réglage est **un seul nombre** — le 0,30 de `_mix_hex(_VANGUARD["panel"], _VANGUARD["hull"],
   0.30)`. À 0,20 la bâche rendrait environ 116 de luminance pour 40 % de saturation.

⚠️ **Le garde-fou tient dans les trois cas** : les fenêtres restent à 221 de luminance, soit
**1,7 fois** la bâche retenue et 40 points au-dessus du deuxième élément le plus lumineux.

---

## 5. Le pas d'appontage — le verdict de valeur TIENT, et il est maintenant mesuré

### 5.1 Pourquoi le pas ne devient pas jaune-ocre

Le brief lit sur la planche « un pas jaune-ocre chaud avec un H sombre ». **Mesuré sur la planche,
c'est l'inverse** : l'intérieur du pas rend **(50, 48, 48)**, luminance 48,4, saturation 4,1 % — un
ardoise **sombre et neutre** — et ce sont **le « H », son cercle et les bandes de rive qui sont
OR**. (Vue gameplay, x 827–935, y 357–435 de la planche ; agrandissement au plus proche voisin pour
lever tout doute.)

Et la valeur du pas est déjà trop claire, pas trop sombre :

| | planche | notre rendu AVANT |
|---|---:|---:|
| pas / ivoire voisin | **0,26** | **0,37** |

Un pont clair de plus l'éloignerait de la planche. **Le verdict du `BRIEF-0115` est donc maintenu,
et cette fois il est chiffré.**

### 5.2 Ce qui était faux, c'était la teinte — et c'est le plafond vu par le bas

Le pas rendait **(63,0 ; 68,1 ; 74,7)**, franchement **bleu** (saturation 15,8 %), là où la planche
donne neutre à 4,1 %. La cause est le pendant exact du défaut que le plafond vient de corriger :

> **À albédo 0,007, une surface ne montre plus sa propre couleur — elle montre celle de
> l'ambiante, qui est bleue (0,55 ; 0,62 ; 0,78). On ne peut rien moduler au plafond ; on ne peut
> rien montrer au plancher.**

`#141419` est tiré vers l'or de la charte **à luminance linéaire constante** (`#171410`) : la
valeur ne bouge pas d'un millième, la teinte cesse d'être bleue.

### 5.3 Et la peinture devient l'accent chaud

Le « H », ses deux jambages, sa barre et les **douze hachures de rive** quittent `AA_Deck_Ambry`
(ivoire) pour `AA_Mark_Ambry` : **l'or `#E4B54A` de la charte**, mat (`roughness` 0,72), **non
émissif**. 180 triangles, 5,9 m², 1,20 % des pixels d'Ambry.

**Les écarts demandés, mesurés :**

| | AVANT | APRÈS |
|---|---:|---:|
| luminance du pas | 67,5 | **66,7** (−1,2 %, soit rien) |
| saturation du pas | 15,8 % | **6,8 %** (planche : 4,1 %) |
| luminance de la peinture | 171,7 | **164,8** |
| saturation de la peinture | 3,8 % | **58,5 %** |
| **écart de luminance peinture ↔ pas** | **× 2,54** | **× 2,47** |
| **écart de teinte peinture ↔ pas** | ~0° utile (deux quasi-neutres) | **179°**, à 58,5 % de saturation |
| **écart de luminance pas ↔ rue qui l'entoure** | × 2,57 | **× 1,42**, et de teinte : neutre-chaud contre neutre |

L'échange **baisse** la luminance (l'or est à 183 de luminance intrinsèque, l'ivoire à 202) et
**monte** la saturation : les deux critères du lot vont dans le même sens. Le pas reste
parfaitement distinct de ce qui l'entoure — par la valeur (× 1,42 sur la rue, × 2,7 sur le bâti à
180) **et** par la teinte.

**C'est l'endroit le plus chargé d'Ambry, et il a enfin quelque chose à dire.** Vignette 5, à 1:1.

---

## 6. L'échelle de valeurs d'Ambry, après — treize slots, treize marches

Mesurée slot par slot sur le rendu, cadre poupe, masque par passe d'identifiants.

| slot | part px | AVANT | **APRÈS** | sat. APRÈS | |
|---|---:|---:|---:|---:|---|
| `AA_Window_Ambry` | 2,56 % | 222,2 | **221,2** | 35,2 % | **les fenêtres — et elles le restent** |
| `AA_Hull_Ambry` | 22,14 % | 181,4 | **180,2** | 5,0 % | palier A — M1, M5, les dalles, la rive |
| `AA_Mark_Ambry` | 1,20 % | 171,7 | **164,8** | **58,5 %** | **neuf** — l'or du pas |
| `AA_HullB_Ambry` | 3,13 % | 187,1 | **158,4** | 8,1 % | **neuf** — M2, M4, M6 |
| `AA_Cloth_Ambry` | 0,96 % | 194,4 | **132,1** | **31,3 %** | la bâche, rendue au bleu |
| `AA_HullC_Ambry` | 5,19 % | 186,7 | **118,4** | 9,3 % | **neuf** — M3 (la voûte), M7 |
| `AA_Deck_Ambry` | 23,15 % | 173,7 | **94,4** | 4,2 % | la rue et les coursives |
| `AA_Rock_Ambry` | 1,93 % | 83,7 | 82,6 | 19,4 % | le soubassement arraché |
| `AA_Pad_Ambry` | 10,35 % | 67,5 | **66,7** | 6,8 % | le pas — valeur tenue, teinte corrigée |
| `AA_Crate_Ambry` | 1,29 % | 58,2 | 55,4 | 14,5 % | caisses |
| `AA_Sign_Ambry` | 0,66 % | 55,3 | 44,8 | 1,6 % | portes, trappes, panneau |
| `AA_Tech_Ambry` | 17,99 % | 45,5 | 41,8 | 18,2 % | machinerie, mât, panneaux |
| `AA_Weld_Ambry` | 1,91 % | 29,4 | 27,0 | 28,1 % | les colliers — à l'Unisson |

> Les trois derniers baissent de 3 à 10 points **sans qu'on y ait touché** : ils recevaient du
> rebond de la rue, qui a perdu 45 % de sa valeur. C'est rapporté, pas voulu.

**Six marches lisibles là où il y en avait deux** — et les fenêtres tiennent le haut avec 40 points
d'avance sur la suivante.

---

## 7. La saturation : rapportée, pas forcée — et le levier n'est pas dans le `.glb`

| | AVANT | APRÈS | cible (planche) |
|---|---:|---:|---:|
| saturation, cadre proue | 22,8 % | **23,9 %** | 26,7 % |
| saturation, cadre poupe | 22,8 % | **23,6 %** | 26,7 % |

**+0,8 à +1,1 point.** Sur votre instrument, cela devrait porter les 17,7 % vers 18,5–19 %. **Le
gap ne se ferme pas, et la mesure dit pourquoi :**

> `AA_Hull_Ambry` porte **22 % des pixels** d'Ambry et rend à **5,0 % de saturation**. L'ivoire de
> la planche est à **17,5 %** (206, 188, 170). Tant que la plus grande surface de la pièce est
> quasi neutre, aucun accent de 1 % de pixels ne peut déplacer la moyenne de neuf points.

Et le levier est chez vous, pas dans le binaire : `AMBRY_WARM = (1,0 ; 0,955 ; 0,885)` ne porte
l'albédo qu'à **9,4 %** de saturation, que l'ambiante bleue ramène à 5,0 % à l'écran. **Pour que
l'ivoire d'Ambry rende la couleur de la planche, il faudrait environ `AMBRY_WARM = (1,00 ; 0,885 ;
0,77)`** — calculé sur les rapports de canaux mesurés, R/G/B rendus 182,8 / 180,1 / 173,7 contre
206 / 188 / 170 visés. Il coûterait un peu de luminance, ce qui va dans le sens du lot.

⚠️ **Je ne l'ai pas compensé dans le `.glb`, et c'est délibéré** : réchauffer l'ivoire à la forge
ferait exister **deux** corrections de teinte concurrentes pour la même surface, dont une
invisible depuis le code. Le réchauffement a un propriétaire : `CortegeSkin`.

---

## 8. ⚠️ Vos trois nouveaux slots veulent-ils des cartes ? Non — mais ils veulent leur ligne

**Aucune image neuve n'est nécessaire**, comme le brief l'anticipait : deux tôles de la même
famille posées à dix ans d'écart ont le même appareillage et pas la même valeur.

| slot | carte | ce qu'il faut poser dans `SKINS` |
|---|---|---|
| `AA_HullB_Ambry` | **partage `ambry_hull`** (TEX-AMB-01) | `&"AA_HullB_Ambry": "ambry_hull"` |
| `AA_HullC_Ambry` | **partage `ambry_hull`** | `&"AA_HullC_Ambry": "ambry_hull"` |
| `AA_Mark_Ambry` | **partage `ambry_pad`** (TEX-AMB-05) — c'est de la peinture sur les mêmes panneaux | `&"AA_Mark_Ambry": "ambry_pad"` |

`test_every_declared_skin_finds_its_maps_on_disk` passera : les images existent déjà.

⚠️ **Et les deux paliers en ont vraiment besoin, ce n'est pas cosmétique.** `_ambry_value()` est
appelée **à l'intérieur de `_skin_surface()`** : un slot absent de `SKINS` ne reçoit ni carte, ni
relief, **ni réchauffement**. Deux modules de tôle mats, froids et lisses au milieu de cinq
modules texturés et chauds se verraient immédiatement. Le palier de **valeur**, lui, tiendrait
quand même — voir ci-dessous.

⚠️ **Rassurance sur le plafond : il ne redoublera pas l'assombrissement.** Les cinq couleurs
touchées par ce lot sont toutes cuites **sous** 0,58 de luminance linéaire, donc `k = 1` et la
fonction ne fait plus que réchauffer :

| slot | luminance linéaire de l'albédo livré | plafond |
|---|---:|---|
| `AA_HullB_Ambry` | 0,306 | intact |
| `AA_HullC_Ambry` | 0,127 | intact |
| `AA_Cloth_Ambry` | 0,131 | intact |
| `AA_Deck_Ambry` | 0,102 | intact |
| `AA_Mark_Ambry` | 0,500 | intact (de justesse) |

`AA_Mark_Ambry` peut rester hors de `SKINS` sans dommage de valeur — l'or est déjà sous le plafond
— mais il y perdrait son grain et sa chaleur sur 1,2 % des pixels.

---

## 9. Textures et UV (ADR-0028)

- **Aucune image, aucune texture dans le `.glb`.** Lu dans le binaire : `images: 0`,
  `textures: 0`. `_audit()` le vérifie et échoue le build sinon.
- **`TEXCOORD_0` COMPTÉ, jamais supposé** : **40/40 primitives** portent `TEXCOORD_0` et
  **40/40** portent `TANGENT` (37/37 au `BRIEF-0115` ; les trois de plus sont les trois slots
  neufs). Le contrôle est bloquant.
- **Dépliage inchangé** : `ak.box_project_uv()` à **0,700 tuile/m**. Les trois slots neufs sont
  hérités du même dépliage et mesurés à **0,697 à 0,700 tuile/m, anisotropie 1,00** — la meilleure
  du fichier, leurs faces étant toutes alignées sur un axe du monde. Aucune couture à déclarer :
  la projection en boîte n'en produit pas, et aucun dépliage continu n'est demandé ici.
- **Aucune demande `TEX-NNNN` n'est livrée**, conformément au refus motivé du brief.

---

## 10. Ce qui n'a pas bougé

| | valeur |
|---|---:|
| **bord avant de `AA_Hull_Ambry`** (lu dans le binaire) | **`s = 446,500`** — exigé 446,5 ± 1 |
| bord avant du palier B / du palier C | `s = 453,08` / `456,11` (loin derrière : la réplique de Lyra ne peut pas être déplacée par eux) |
| sommet d'Ambry (le mât) | **−3,200** |
| plafond de construction | −3,20 |
| triangles d'Ambry | **5 300** (identique) |
| triangles `Section_05` | **17 158** (identique, 95,3 % du cliquet local) |
| triangles du corridor | **56 114** (identique) |
| `.glb` | 3 379 332 o (+3 360 o, **+0,1 %**) |
| matériaux dans le binaire | 17 → **20** |
| triangles d'Ambry sur un slot du bordé | **0** |
| violet + magenta, aire vue | **1,37 %** (cible 5, cliquet 9) |

**Déterminisme** : quatre exécutions consécutives de `./scripts/build-hull.sh long_cortege`,
**zéro octet divergent** —
`edc3eb792764d0f260e070deaa695810d4029678958a0e87b0cfed8398e35c7b`.

**`./scripts/check.sh` : ALL GREEN** — 1 035 tests, 8 887 assertions, 0 échec, 0 erreur d'analyse,
dont `test_the_front_edge_of_ambry_is_read_from_the_hull`,
`test_the_ambry_line_waits_until_ambry_is_in_the_frame`,
`test_every_ambry_material_keeps_its_own_unwrap_scale` et
`test_every_declared_skin_finds_its_maps_on_disk`.

---

## 11. La planche

`docs/forge/output/BRIEF-0116-planche.png` — 1920 × 6254, **sept bandes**.

| # | Vue | Ce qu'elle tranche |
|---|---|---|
| 1 | **AVANT**, cadre proue, caméra du jeu | la masse blanche, le « H » ivoire, la bâche invisible |
| 2 | **APRÈS**, **même cadrage** | le pas et son or, la rue descendue, le premier palier |
| 3 | **AVANT**, cadre poupe | les sept modules à une seule valeur |
| 4 | **APRÈS**, **même cadrage** | trois paliers, la bâche bleue, la rue sous le bâti |
| 5 | **le pas d'appontage à 1:1** | ivoire → or, à la taille où le joueur le verra |
| 6 | **l'arbitrage de la bâche** | écru / délavé / bleu profond, côte à côte, avec leurs mesures |
| 7 | **l'échelle de valeurs mesurée** | treize slots, treize marches, les fenêtres en tête |

---

## 12. Limites connues

### 12.1 Mon instrument n'est pas le vôtre, et les absolus ne transfèrent pas

Développé en §1. Médiane 105 chez moi contre 86 chez vous sur le même état de départ ; saturation
22,8 % contre 17,7 %. **Reprenez vos propres chiffres sur une capture en jeu avant d'inscrire quoi
que ce soit** : ce sont les écarts que je garantis, pas les niveaux.

### 12.2 La médiane descend peut-être plus bas que vous ne le vouliez

105 → 76 sur mon instrument, soit −28 %. Reporté sur le vôtre, la bande d'Ambry passerait de 86 à
environ **62**, pour une planche à 51. C'est le bon sens de marche, mais c'est un grand pas, et il
est porté aux trois quarts par **la rue** (§3), qui est le changement non demandé. **Si c'est trop,
le levier est le 0,45 de `_AMBRY_DECK_HEX`** — à 0,60 la rue rendrait environ 115, ce qui la
remettrait au niveau du palier C et annulerait une partie du bénéfice. Je préfère vous donner le
cran plutôt que de le choisir à votre place.

### 12.3 Le palier C ne porte que deux modules, et c'est un arbitrage assumé

Les trois modules bas (M2, M4, M7) n'offrent presque aucune tôle à l'œil : leur toit est une bâche,
trois caisses ou une cuve. Mettre le palier le plus sombre sur eux aurait été **invisible en jeu**
— c'est ce que le premier tirage a montré. Le récit s'est donc adapté à la mesure : la voûte de M3,
qui est la plus grande surface de tôle après M1, porte le palier C parce qu'un berceau n'est pas du
panneau plat. Si vous préférez le récit inverse (les petits ajouts tardifs les plus sombres), c'est
sept lignes dans `AMBRY_MODULE_TIER` — mais alors il n'y aura rien à voir.

### 12.4 La saturation reste à 3 points de la planche, et le reste du chemin est dans le code

Développé en §7. `AMBRY_WARM ≈ (1,00 ; 0,885 ; 0,77)` est la valeur mesurée qui rendrait l'ivoire de
la planche. Votre périmètre.

### 12.5 Les portes n'ont pas été touchées, et c'est un gisement de couleur laissé de côté

`AA_Sign_Ambry` (portes, trappes, panneau peint) rend à **44,8 de luminance et 1,6 % de
saturation** : six portes de 27 px qui ne se voient pas. Le Détail C de la planche montre une porte
**rouille**. La charte a `#C93A31` (rouge sécurité, « marquages restreints »), mais le rouge touche
à la réserve des tirs ennemis et le brief ne demandait rien là-dessus : **je ne l'ai pas fait de
ma propre initiative.** C'est 0,66 % des pixels, donc environ +0,3 point de saturation, et surtout
six repères d'échelle humaine qui deviendraient lisibles. À votre arbitrage.

### 12.6 `Section_05` occupe toujours 95,3 % de son cliquet local

Inchangé depuis le `BRIEF-0115` : 17 158 triangles pour un `TRI_BUDGET_SECTION` de 18 000. Ce lot
n'a pas ajouté un seul triangle, mais le mur est toujours là pour le prochain.
