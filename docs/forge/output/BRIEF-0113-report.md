# BRIEF-0113 — Rapport de forge : les tours de rive n'ont pas de siège, et voici la mesure

- **Brief** : `docs/forge/briefs/BRIEF-0113-les-tours-de-rive-sont-hors-cadre.md`
  (+ l'ajout du coordinateur : **voie D**, « baisser l'assise, garder la station »)
- **Date** : 2026-09-08
- **Outil** : Blender 5.2.1 LTS (`blender-aegis`), toujours `-t 1`
- **Livrables** : `tools/blender/build_stern.py`,
  `assets/imported/models/backgrounds/stern_hull.glb`,
  `docs/forge/output/BRIEF-0113-planche.png`, ce rapport
- **Périmètre respecté** : aucun `.gd`, `.tscn`, `.tres` touché (ils sont **lus**, voir §5) ;
  `stern_tower.glb` **pas rouvert** ; `build_long_cortege.py`, le complexe du tronçon 5, les
  nacelles, berceaux, verrous, bras et les trois canaux d'échappement intacts.

---

## 0. La réponse en une ligne

**Voie C : deux tours.** Les deux plateaux de rive et `CTRL | Tour 03/04` sont retirés, et les
trois autres voies sont fermées — **mesurées, pas estimées** :

| Voie | Verdict | Le chiffre qui ferme |
|---|---|---|
| **A** — les remettre sur le plateau, à `x = ±9` ou `±11` | **impossible** | `x 8,08..12,48` **est** le canal d'échappement latéral ; le seul autre plat du massif (bossage extérieur) demande une assise à **−7,79**, qui crève la règle A de 9 cm **et** reste hors cadre à **−13 px** |
| **B** — avancer l'étagère de rive | **fermée** | le cadre s'ouvre à partir de `z ≈ −5,2`, mais la rive est occupée **sans interruption de `z = −7,11` à `+7,27`**, et la seule pièce qui libère la fenêtre est une plate-forme de tourelle **qui n'a nulle part où aller** (il lui faut 4,88 m de rive libre ; le plus grand créneau restant en fait **3,49**) |
| **D** — baisser l'assise, station inchangée | **impossible** | à `z = −10,10`, la peau est à **−4,60 sur tout `x 17,2..19,0`**. Descendre à −8,17 y demande d'**enlever 3,6 m de massif**. Ce n'est pas un piédestal, c'est un puits — et ce générateur refuse les booléens par construction |
| **C** — deux tours | **retenue** | l'assise qui marche est **−8,40**, la poupe n'en a que **deux**, et elles portent déjà `Tour 01/02` |

---

## 1. Les quatre couples (pied ; sommet), en pixels

Projection refaite à part, indépendamment du banc, et **elle retombe au dixième de pixel sur les
quatre chiffres du brief** — c'est ce qui valide le modèle avant de s'en servir pour décider.

| Repère | Assise | `z` local | **Pied** | **Sommet** | Verdict |
|---|---:|---:|---:|---:|---|
| `CTRL \| Tour 01` | −8,400 | −9,900 | **146,3 px** | **+13,3 px** | dans le cadre |
| `CTRL \| Tour 02` | −8,400 | −9,900 | **146,3 px** | **+13,3 px** | dans le cadre |
| `CTRL \| Tour 03` | −4,600 | −10,100 | **37,0 px** | **−142,4 px** | ⛔ hors cadre |
| `CTRL \| Tour 04` | −4,600 | −10,100 | **37,0 px** | **−142,4 px** | ⛔ hors cadre |

⚠️ **ET LE SOMMET EST UNE FACE, PAS UN POINT.** Le banc projette `position + hauteur`,
c'est-à-dire le **centre** de la face haute. Une tour de 2,53 m de côté vue à 70° de plongée étale
sa face haute sur **70 px** : les coins arrière de `Tour 01/02` tombent à **−21 px**, donc
**dehors**, quand leur centre est à +13. C'est le seul écart que j'aie trouvé au banc, il ne change
aucun verdict de ce lot, et il est signalé plutôt que corrigé (le banc est gardé verbatim).

---

## 2. Voie D — la vérification 1, faite sur le binaire

> « La coque descend-elle jusqu'à −8,40 à `|x| ≈ 17,7` ? »

**Non.** Profil transversal du massif à `z = −10,10`, relu dans `stern_hull.glb` par lancer de
rayon vertical (jamais par « sommets proches ») :

| `x` | peau `y` | ce que c'est |
|---:|---:|---|
| 12,48 | −10,95 | fond du canal latéral — **le panache passe ici** |
| 13,46 … 14,60 | **−8,40** | dessus du bossage extérieur — **1,14 m de plat** |
| 14,96 | −8,40 | la rampe de flanc franchit −8,40 **en montant** |
| 15,78 | −6,20 | pied du relief de flanc |
| 17,05 | −5,04 | |
| **17,73** | **−4,60** | **la station demandée** |
| 18,20 … 19,00 | −4,60 | l'arête de rive, plate sur 0,80 m |
| 19,40 | −5,90 | terrasse 2 |
| 19,80 | −7,10 | terrasse 3 |
| 19,90 | −8,30 | le point le plus large — au-delà, la coque **rentre** |

À la station des tours, l'assise demandée par la voie D est **3,57 m sous la peau**, et la peau ne
repasse sous −4,90 nulle part entre `x = 17,2` et `x = 19,0`. Le coordinateur envisageait un
**piédestal** ; il faudrait l'inverse — **un puits de 2,53 m de côté et 3,6 m de fond, creusé dans
le massif arrière**. Or ce générateur ne soustrait rien : « c'est la seule façon d'obtenir une
topologie prévisible, un fichier déterministe et un générateur qu'on relise » (`build_stern.py`,
`BRIEF-0107`). Un booléen ici, c'est le déterminisme du binaire qu'on rouvre — et le déterminisme
est un critère d'acceptation de tous les lots de cette poupe.

⚠️ **Et le sponson n'est pas une porte de sortie non plus** : la seule surface à `−8,40` outre les
bossages est *au-delà* du point le plus large (19,90). Un siège là-bas porte la tour **en dehors
de la silhouette**, à `|x| ≈ 21,2` — 1,3 m de plus que le point le plus large de la poupe, sur une
coque dont l'évasement 17,10 → 18,50 → 19,90 est une décision mesurée du `BRIEF-0106`.

### 2.1 — Et l'assise qui marche, il y en a **deux** sur toute la poupe

Le tableau ci-dessus le dit sans commentaire : à cette station, la seule altitude `−8,40` est le
**dessus des bossages**. Il y en a quatre (deux par bord) ; les deux intérieurs portent
`Tour 01/02`, et l'extérieur est celui que la voie A ferme au paragraphe suivant. **La voie D et
la voie C sont donc la même phrase** : « garder l'assise qui rend la tour visible ». Elle en a
exactement deux, elles sont prises, et c'est pour cela que le lot livre deux tours.

---

## 3. Voie A — le plateau à `x = ±9` / `±11`, et le bossage extérieur

`x = ±9` et `±11` **sont le canal d'échappement latéral** : il est centré sur `x = ±10,28` et
libre de `8,08` à `12,48` (demi-largeur libre mesurée **2,200 m** pour un panache de 1,700). Rien
n'y va, jamais.

Reste le **bossage extérieur** (`x 12,50..15,30`), dont le dessus plat mesure **1,14 m** pour une
empreinte de 2,531. Un plateau construit peut élargir l'assise vers l'extérieur — jusqu'où ? Mesuré
sur le binaire, empreinte par empreinte, à `z = −10,10` :

| `cx` | empreinte `x` | peau max sous l'empreinte | assise minimale | sommet | écran |
|---:|---|---:|---:|---:|---:|
| 13,700 | 12,43 … 14,97 | −7,790 | −7,790 | −3,090 | −13,3 px |
| **13,7455** | **12,48 … 15,01** | **−7,790** | **−7,790** | **−3,090** | **−13,3 px** |
| 14,000 | 12,73 … 15,27 | −7,583 | −7,583 | −2,883 | −20,6 px |

`cx = 13,7455` est la **borne du harnais de canal** (`|cx − 10,28| ≥ 2,20 + 1,2655`) : la première
position légale, l'empreinte collée au bord du canal. Elle échoue **deux fois** :

- **plafond** : sommet à `−3,09`, soit **9 cm au-dessus de la règle A** (`−3,20`) — et la règle B
  ne s'applique pas, l'empreinte étant à `|x| < 16` ;
- **cadre** : sommet à **−13 px**, donc dehors de toute façon.

La rampe de flanc monte trop vite : elle passe de `−10,95` à `−6,20` en 1,77 m de `x`, si bien
qu'élargir l'assise vers l'extérieur **remonte** l'assise minimale plus vite que la fenêtre du
cadre ne se referme. Les deux contraintes se croisent **sans laisser d'intervalle**.

---

## 4. Voie B — la carte complète de la rive

Le cadre s'ouvre bien en avançant : à assise −4,60 le sommet repasse au-dessus de 0 px vers
`z ≈ −5,2`. Voici la rive **station par station**, sur la carène livrée : l'assise que la peau
offre réellement sous une empreinte de 2,531 m, le sommet d'une tour de 4,70 m posée dessus, et ce
qui occupe déjà la place.

| `cz` | assise offerte | sommet `y` | **sommet écran** | occupant |
|---:|---:|---:|---:|---|
| −8,00 | −4,340 | +0,360 | −89 px | flexibles 07/08, plate-forme HEAVY |
| −7,00 | −4,340 | +0,360 | −56 px | flexibles 07/08, plate-forme HEAVY |
| −6,00 | −4,600 | +0,100 | −11 px | flexibles 07/08, plate-forme HEAVY |
| −5,50 | −4,340 | +0,360 | −5 px | flexibles 07/08, plate-forme HEAVY |
| **−5,00** | −4,600 | +0,100 | **+24 px** | flexibles 07/08, plate-forme HEAVY |
| −4,00 | −4,340 | +0,360 | +50 px | flexibles 07/08, plate-forme HEAVY |
| −3,00 | −4,340 | +0,360 | +88 px | plate-forme HEAVY, socle de pylône |
| −2,00 | −4,698 | +0,002 | +142 px | plate-forme HEAVY, socle de pylône |
| −1,00 | −5,647 | −0,947 | +216 px | HEAVY, socle de pylône, STANDARD |
| 0,00 | −5,647 | −0,947 | +257 px | socle de pylône, plate-forme STANDARD |
| +1,00 | −5,647 | −0,947 | +299 px | socle de pylône, plate-forme STANDARD |
| +2,00 | −5,647 | −0,947 | +343 px | socle de pylône, plate-forme STANDARD |
| +3,00 | −5,647 | −0,947 | +389 px | plate-forme STANDARD |
| +4,00 | −6,340 | −1,640 | +453 px | STANDARD, flexibles 05/06 |
| +5,00 | −6,340 | −1,640 | +501 px | STANDARD, flexibles 05/06 |
| +6,00 | −6,340 | −1,640 | +551 px | flexibles 05/06 |
| +7,00 | −5,340 | −0,640 | +587 px | flexibles 05/06 |

**Il n'y a pas une seule ligne libre.** L'occupation en `z` est continue de **−7,11 à +7,27** :

```
-7,11 .. -4,37   CTRL | Liaison 07/08   (flexibles de rebord — décor, à moi)
-6,94 .. -2,06   plate-forme volante HEAVY   (code)
-2,50 .. +1,70   socle de pylône             (décor, à moi ; il porte CTRL | Pylone 01/02)
-0,11 .. +4,11   plate-forme volante STANDARD (code)
+4,53 .. +7,27   CTRL | Liaison 05/06        (décor, à moi)
```

Les créneaux résiduels font **1,87 m**, **0,42 m** et **0,70 m**, pour une empreinte de 2,531.

### 4.1 — « Nommez la station » : je l'ai cherchée, et elle n'existe pas

Le brief propose de déplacer une plate-forme volante si je nomme la station. La seule qui libère
une fenêtre à la fois **visible** et **assez large** est **HEAVY (`±16,80 ; −5,20 ; −4,50`)**.
Alors j'ai cherché où la remettre — et c'est là que ça casse :

- une dalle HEAVY occupe **4,884 m** en `z` (rayon de service 1,99 + marge 0,45, doublé) ;
- elle vit à `y ≈ −5,2`, donc elle doit trouver **4,884 m de rive libre** à cette altitude ;
- après le déplacement de la tour, les créneaux restants sur la rive font **3,49 m** (entre le
  pylône et les flexibles avant), **1,87 m** et **1,37 m**. Le plus grand est **1,4 m trop court** ;
- elle ne peut pas reculer non plus : au-delà de `z = −8,48` il n'y a plus de bassin, et une
  dalle à `y = −5,2` s'y retrouverait **dans la matière du massif** (la peau y est à −4,60).

**Déplacer HEAVY revient donc à la sortir de la rive** — c'est-à-dire à retirer un canon de la
poupe qui vient d'apprendre à se défendre (`ADR-0049`) **pour poser un décor**. Je ne le propose
pas. Si le concepteur veut quand même quatre tours, la recette est prête et tient en deux cotes :
plateau top `−4,60`, `cx = ±17,725`, `cz = −4,90` (empreinte `z −6,17..−3,63`) → **pied 191 px,
sommet 32 px** ; et il faut que HEAVY **et** les flexibles 07/08 quittent la bande.

⚠️ **Et le critère « sous 240 px » n'aurait de toute façon jamais été tenu à la rive.** Le
coordinateur l'a retiré ; la mesure lui donne raison. Pour un sommet sous les panneaux de coin, il
faut `z ≥ +0,43` à assise −4,60 — c'est-à-dire **la bande du pylône et de STANDARD**, la seule
partie de la rive qui rende entre 250 et 550 px.

---

## 5. Ce que le lot ajoute au générateur : **le cadre est devenu un harnais**

C'est la vraie livraison de ce lot. `_frame_probe()` projette **chaque pièce posée** par la caméra
du jeu au plan de maintien et **échoue le build** si son sommet sort du cadre. Le défaut du
`BRIEF-0112` était totalement silencieux : ni erreur d'import, ni test rouge, ni ligne de journal.

**Rien n'y est recopié** — quatre sources sont lues :

| Ce qui est lu | Où | Pourquoi pas une constante |
|---|---|---|
| la caméra (transformation + FOV) | `scenes/gameplay/cortege.tscn` | une cote écrite deux fois finit par diverger |
| la résolution de sortie | `project.godot` | idem |
| le plan de maintien (`hold_plane_y`) | `resources/levels/long_cortege_stern.tres` | déjà lu par le fichier |
| les panneaux du HUD | `scripts/ui/fighter_hud.gd` | ils bougent avec le HUD, pas avec la coque |

Deux pièges rencontrés, tous deux silencieux, tous deux commentés dans le code :

- **les douze nombres d'un `Transform3D` sont des LIGNES, pas des colonnes.** Les deux lectures
  donnent une caméra valide : l'une plonge à 70°, l'autre regarde le ciel. Seule la bonne retombe
  sur les 146 / 13 / 37 / −142 px du brief ;
- **dans l'expression rationnelle qui lit les panneaux, `Vector2\(...\)` doit passer AVANT
  `[\w.]+`** : sinon le moteur capture le mot « Vector2 » et s'arrête là. Trois panneaux sur
  quatre passaient inaperçus, sans un mot. C'est exactement la classe de défaut que ce lot traite.

### 5.1 — Ce que le harnais a trouvé d'autre (mesuré, non corrigé)

Le sommet des **19** pièces est désormais dans le cadre. Mais le harnais imprime aussi les
panneaux de HUD traversés, et il en sort trois faits que personne n'avait :

| Pièce | Pied | Sommet | Face haute | Panneau |
|---|---:|---:|---|---|
| `CTRL \| Tour 01/02` | 146 px | 13 px | **−21 … 49 px** | bandeau de boss (`x 560..1360`, `y 28..114`) |
| `CTRL \| Liaison 07` | 163 px | 155 px | 113 … 198 px | score + traversée (`x 1570..1892`) |
| `CTRL \| Liaison 08` | 163 px | 155 px | 113 … 198 px | bouclier (`x 28..458`, `y 28..178`) |

Les deux flexibles de rebord arrière sont donc, eux aussi, **derrière des panneaux opaques à 82 %**
— pas hors cadre, mais pas regardés non plus. Ce n'est pas dans le périmètre de ce lot ; c'est dit.

Pour référence, la pièce la mieux placée de la poupe reste le **pylône** : pied 418 px, sommet
308 px, hors de tout panneau. C'est le repère de ce qu'« un siège visible » veut dire ici.

---

## 6. Le recouvrement, remesuré

`_piece_clash()` compare **toutes les paires** de pièces posées et de volumes construits — 19
pièces + 6 volumes (2 plateaux de socle, 4 margelles), soit **300 paires**.

| Paire | Recouvrement |
|---|---:|
| `Tour 01/02` × socles de pylône | **0,000 m³** |
| `Tour 01/02` × `Liaison 01…08` | **0,000 m³** |
| `Tour 01/02` × `Pylone 01/02`, `Collecteur 01…07` | **0,000 m³** |
| `Tour 01/02` × plates-formes volantes `STANDARD` / `HEAVY` | **0,000 m³** |
| **Les 300 paires** | **AUCUN** |

⚠️ **Le seul recouvrement de la poupe reste celui du `BRIEF-0110`** : `CTRL | Pylone 01/02`
traverse la dalle `STANDARD` de la garnison de **2,284 m³** par bord. Il **préexiste**, il
n'appartient pas à ce lot, et retirer les deux tours de rive ne l'a ni aggravé ni réduit.

⚠️ **Un fait de plus, trouvé en sondant la rive, et qui n'est pas de ce lot** : la peau sous
l'empreinte du **pylône** monte à **−5,92** alors que son repère est à **−8,60**. Son flanc
extérieur est donc **enterré jusqu'à 2,68 m** dans les terrasses de la bande B2. `_seat_probe()` ne
le voit pas — il ne sonde que les repères de **tour**. C'est mesuré et signalé ; le corriger
demanderait de rouvrir le socle de pylône, ce que ce lot n'a pas à faire.

---

## 7. Ce qui n'a pas bougé, et c'est vérifié sur le binaire

| Critère | Chiffre relu |
|---|---|
| Jonction `s = 500` | **6,56 × 10⁻⁷ m** sur 48 sommets, des deux bords — le chiffre exact d'avant |
| Les trois canaux d'échappement | **0,000000000 m²** de coque dans le volume des panaches ; demi-largeur libre **2,200 m** aux trois stations, fond **−10,950** |
| `AA_Emissive_Engine` dans les canaux | **0,000000 m²** |
| Emprise des berceaux | **0,000000 m²** de décor au-dessus du pont |
| Demi-largeur max | **19,900 m** (inchangée) |
| Plafond de la carène | `y_max = −3,250` |
| `stern_tower.glb` | **pas rouvert** (`ea02c888…` inchangé) |
| Carène | 3 426 → **3 258** triangles (−168 : les deux plateaux de rive) |
| Repères | 21 → **19** |
| Total poupe | 111 030 → **94 086** triangles (rapporté, pas contraint) |

---

## 8. Textures et UV (`ADR-0028`) — et **deux sections manquent au brief**

⚠️ **Le `BRIEF-0113` n'a ni section `## Texture` ni section `## Animation`.** `ADR-0028` et
`ADR-0046 §6` les rendent obligatoires, précisément pour qu'une permission ne dépende pas de la
mémoire de celui qui rédige. Je le signale et je livre quand même, parce que ce lot **ne crée
aucune géométrie** : il en retire.

- **Aucune texture livrée** ; le binaire porte **zéro image** ;
- **`TEXCOORD_0` compté, jamais supposé : 5 primitives sur 5**, dont 0 sans UV ;
- dépliage **inchangé** : projection en boîte à **0,1994 tuile/m** mesurée (annoncée 0,20, la
  densité exacte du bordé du corridor, lue dans `blc.HULL_TEXELS_PER_METER`), anisotropie max
  **1,356** pour une borne théorique √3 = 1,732 ;
- **aucune animation** : la poupe est de la structure ; ce qui bouge (nacelles, berceaux, verrous,
  bras, et les rotors des tours) est dans les pièces instanciées, pas dans la carène.

---

## 9. Déterminisme

Trois exécutions, `-t 1`, **zéro octet divergent** :

```
stern_hull.glb   d050ae4f019d4928bc129c37297ca7e2dedd66b9b6bfbadd19bba0ca9e79ead3   (x3)
```

---

## 10. Rendu et **REGARDÉ** (`ADR-0006`)

`docs/forge/output/BRIEF-0113-planche.png` — **neuf vignettes de 1920 × 1080**, à la caméra du jeu
`(0 ; 14 ; 5)` / FOV 62 vertical, avec les trois groupes propulsifs, leurs panaches et les pièces
instanciées sur les repères.

⚠️ **LES DEUX PREMIÈRES SONT LE SEUL VERDICT, ET C'EST LA LEÇON DU LOT.** Elles sont **au plan de
maintien** — la poupe à `z = −6,47` monde, là où le survol s'arrête — avant contre après, même
cadrage. Les vignettes cadrées sur le massif (3 et 5) **avancent la poupe** pour montrer l'instant
du survol où elle est pleine face : c'est ce cadrage-là, pris pour un verdict au `BRIEF-0112`, qui
a fait passer pour bonnes deux tours que le jeu ne montre pas.

**Et les deux vignettes de verdict sont identiques à 0,006 % près.** Mesuré sur les pixels, hors
bande de légende : **110 pixels diffèrent sur 1 756 800**, et ce sont des grains
d'échantillonnage Cycles. C'est *exactement* le résultat attendu — retirer `Tour 03/04` ne change
rien à l'image **parce qu'elles n'y étaient pas**, et leur plateau non plus : son arête haute
court de **78 px** (avant) à **−3 px** (arrière), le long du bord, et le massif la masque. La
légende chiffrée de chaque vignette est **lue dans le binaire qu'on rend** (`_frame_caption`) :
celle du haut porte ses quatre tours (pied 146 / 37 px, sommet 13 / −142), celle du bas ses deux.

### 10.1 — **22 050 pixels contre 110** : le chiffre qui condamne le cadrage studio

La même paire avant/après, rendue aux **deux** cadrages, mesurée sur les pixels :

| Cadrage | Pixels qui changent quand on retire `Tour 03/04` | Part du cadre |
|---|---:|---:|
| **au plan de maintien** (vignettes 1 et 2) — *ce que le jeu montre* | **110** (bruit d'échantillonnage) | 0,006 % |
| cadré sur le massif (vignettes 3 et 5) — *une planche studio* | **22 050** | 1,26 % |

Les deux tours de rive occupent **22 050 pixels sur la planche du `BRIEF-0112`** et **zéro dans le
jeu**. Ce n'est pas une nuance de jugement, c'est un rapport de 200 pour 1 — et c'est toute la
raison pour laquelle les vignettes de verdict de ce lot sont au plan de maintien.

Ce que la planche montre aussi, et qui mérite d'être su : **au plan de maintien, tout le massif
arrière tient dans les 150 px du haut du cadre**. `Tour 01/02` y sont deux couronnes au ras du
bord. Le moment où elles se lisent vraiment est *pendant* le survol, deux secondes plus tôt —
c'est ce que rendent les vignettes 3 et 5.

| # | Vignette | Ce qu'elle montre |
|---:|---|---|
| 1 | **AVANT, au plan de maintien** | les quatre tours montées ; on n'en voit que deux |
| 2 | **APRÈS, même cadrage** | les deux tours ; l'image n'a pas changé |
| 3 | avant, cadré sur le massif | l'instant du survol où la poupe est pleine face |
| 4 | la rive de tribord | le socle et le pylône ; **l'étagère de rive est rendue nue** |
| 5 | après, cadré sur le massif | les deux tours sur les bossages |
| 6 | sans les groupes | les deux tours sur leurs assises, sous les trois panaches |
| 7 | le massif de trois-quarts | les trois canaux, panaches à 14 % |
| 8 | la jonction `s = 500` | rasante, inchangée au micron |
| 9 | de dessus | les deux tours, les trois canaux, la rive nue |

---

## 11. Ce qui reste au concepteur

### 11.1 — ⚠️ **DEUX COMPTEURS VONT ROUGIR, ET IL FAUT LES CHANGER — JE N'Y TOUCHE PAS**

Le lot passe de **21 à 19 repères** et de **4 à 2 tours**. Deux assertions codent ces nombres en
dur, et elles sont toutes les deux dans du `.gd`, hors périmètre :

| Fichier | Ligne | Il faut lire |
|---|---|---|
| `docs/forge/briefs/_BANC-CADRE-0113.gd.txt` | `assert_true(vues == 4, …)` | `vues == 2` |
| `tests/unit/test_cortege_stern.gd` (≈ 911) | `assert_true(reperes.size() >= 21, …)` | `>= 19` |

⚠️ **La seconde est un test EXISTANT, et elle rendra `./scripts/check.sh` rouge tant qu'elle
n'aura pas bougé.** Je l'ai cherchée exprès, parce que c'est le pendant exact du défaut que ce lot
traite : un compteur écrit en dur ne sait pas qu'on a retiré une pièce, et il le dit — mais au
mauvais endroit et avec le mauvais mot. C'est la bonne nouvelle du jour : ce défaut-là, lui, n'est
**pas** silencieux.

Les deux assertions qui comptent vraiment dans le banc — `y_sommet >= 0` et
`y_pied <= hauteur` — passent sur les deux tours restantes, et sur les 17 autres pièces aussi
(§5.1).

### 11.2 — Le reste du câblage est déjà bon

`CortegeStern.DRESS` porte bien `"CTRL | Tour"` depuis `b5f2aac`, `_dress()` et `_run_towers()`
itèrent les repères du binaire sans en compter, `test_no_dressing_key_points_at_a_marker_that_is_gone`
reste vert (les deux tours survivent, donc la clé vise encore un repère), et
`test_the_exchange_tower_carries_the_clips_the_code_plays` ne touche qu'au binaire de la tour, que
ce lot n'a pas rouvert.

### 11.3 — Si quatre tours restent souhaitées

Alors la question n'est plus de forge, elle est de **gameplay** : il faut décider si la
plate-forme de tourelle `HEAVY` quitte la rive de poupe. Si oui, la recette est au §4.1 et je la
pose en un lot court. Si non, la poupe porte deux tours — et deux tours vues valent mieux que
quatre tours dont la moitié n'est dans le champ de personne.

---

## 12. Livrables

| Fichier | Ce que c'est |
|---|---|
| `tools/blender/build_stern.py` | `build_tower_seats()` et les constantes `TOWER_SEAT_*` retirées ; deux repères au lieu de quatre ; **`_frame_probe()`, `_game_camera()`, `_viewport()`, `_hud_panels()`, `_screen()` ajoutés** ; la vue `hold_avant` et `_frame_caption()` pour la planche |
| `assets/imported/models/backgrounds/stern_hull.glb` | la carène — 3 258 triangles, 19 repères, 314,9 Kio |
| `docs/forge/output/BRIEF-0113-planche.png` | neuf vignettes 1920 × 1080, avant/après **au plan de maintien** |
| `docs/forge/output/BRIEF-0113-report.md` | ce document |

**Deux lignes** ajoutées à `assets/licenses/ASSET_PROVENANCE.csv` et **une** mise à jour
(`stern_hull`) ; aucune autre ligne existante modifiée.
