# BRIEF-0111 — Rapport de forge : le complexe industriel du tronçon 5

- **Brief** : `docs/forge/briefs/BRIEF-0111-le-complexe-industriel-du-troncon-5.md`
- **Date** : 2026-09-08
- **Outil** : Blender 5.2.1 LTS (`blender-aegis`), toujours `-t 1`
- **Livrables** : `tools/blender/build_long_cortege.py`,
  `assets/imported/models/backgrounds/long_cortege.glb`,
  `docs/forge/output/BRIEF-0111-planche.png`, ce rapport
- **Périmètre respecté** : aucun `.gd`, `.tscn`, `.tres` touché ; aucun commit ;
  la poupe et ses dix-sept repères intacts ; **les 42 repères existants du corridor
  sont inchangés au micron**, vérifié en relisant les deux binaires.

---

## 0. ⚠️ LE VIDE N'EST PAS DE 69 M, IL EST DE 24,5 — ET C'EST LE POINT LE PLUS IMPORTANT DU LOT

Le brief pose l'emprise à `s ∈ [418 ; 472]`, « 54 m utiles » dans un vide tribord de 69 m.
**Il y en a 24,5.**

Les 69 m sont mesurés sur les **marqueurs** (dix-sept tourelles, sept ponts, cinq nœuds).
**Ambry n'en est pas un** : c'est une pièce *cuite dans la peau* du tronçon 5, de `s = 446` à
`474` avec ses colliers de greffe de `444,5` à `475,5`, à `x` 7,60 à 13,60 — **le même bord**.
Aucune table de marqueurs ne la voit.

C'est un angle mort connu de ce fichier, et il a déjà coûté : `ARTERY_CONDUITS` porte le
commentaire « ⚠️ 232 ET NON 240 : LA CITADELLE OCCUPE 239,6 A 246,0 […] le banc de pose ne la
voyait pas ». Le compte de calme imprimé à chaque build l'écrivait d'ailleurs noir sur blanc
avant ce lot : *« les cinq plus larges : s 0-42 (42 m), **s 419-444 (25 m)**, … »*.

| Ce qui occupe le bord tribord du tronçon 5 | `s` |
|---|---|
| `Turret_13` | 410,0 |
| **le vide réel** | **418,0 → 442,5 (24,5 m)** |
| Ambry, colliers compris | 444,5 → 475,5 |
| `Turret_17` | 478,8 |

**Ce que j'en ai fait** : le complexe occupe `s ∈ [418,0 ; 442,5]`. 8 m de garde à `Turret_13`,
2 m de tôle nue avant le premier collier d'Ambry. Le critère « tient dans `[418 ; 472]` » est
tenu ; les **54 m utiles ne le sont pas**, et ne pouvaient pas l'être sans démolir Ambry.

**Et c'est la bonne taille pour ce qu'on en fait** : la caméra du jeu montre **27,1 m de pont à
la fois** (mesuré en intersectant les deux rayons de bord du champ avec le plan du pont médian).
Un complexe de 24,5 m remplit **un écran entier** dans le sens du défilement. Meubler 54 m en
aurait demandé deux, et aurait collé le complexe à Ambry — dont tout l'intérêt est d'arriver
seule, après du calme.

**Un harnais bloquant fait désormais ce constat par machine** : `_assert_plant_is_clear()` vérifie
les 8 m de garde à chaque tourelle tribord, la non-intersection d'Ambry *colliers compris*, la
tenue de la voie de conduite sur le pont à chaque station couverte, l'appartenance du bassin à
l'emprise, et la distance à l'axe. Testé en négatif : porter l'emprise à `[414 ; 448,5]` le fait
échouer en nommant les deux fautes.

---

## 1. Ce que le complexe EST

Le critère du lot n'est pas « il y a de la matière », c'est « **on voit une installation** ».
Trois choses le portent, et aucune n'est un tapis de greebles :

| | Quoi | Pourquoi |
|---|---|---|
| **une EMPRISE** | plancher de 0,35 m en trois segments, longeron de rive (0,62 m), longeron de chine (0,30 m), deux traverses de bout | un bord, donc un **dedans** et un **dehors**, avant qu'aucun volume n'y soit posé |
| **deux SEUILS** | portiques à `s = 419,30` et `441,35`, linteau à −3,90 | on **entre** et on **sort** |
| **un CŒUR** | bassin `s 427,3 → 436,2`, `x` nominal 7,35 → 10,30, fond **−6,62** (1,63 m sous le pont médian), trois passerelles, deux bouts de coaming clairs | le seul endroit où l'on voit **dedans** quelque chose |

Plus, dans l'ordre du survol : **la ferme de quatre cuves** octogonales de l'entrée, le massif
d'allée, **les deux cheminées tronconiques** du cœur, le massif et les deux cuves de sortie, la
passerelle transversale, trois caisses d'allée, **onze plots de rive** et **huit traverses de
plancher** qui donnent la cadence.

### Le complexe suit la taille du bord, et ce n'est pas décoratif

`ASYMMETRY` **pince tribord de 15 %** à `s = 434` — 1,5 m qui rentrent et ressortent en plein
milieu de l'emprise. Tout le mobilier est donc écrit en **x nominal** et multiplié par
`_side_scale`, comme la peau elle-même :

```
au large (s = 418)      x absolu  6,85 → 12,30
au pincement (s = 434)  x absolu  5,82 → 10,46
```

Une pièce écrite en absolu se serait retrouvée à cheval sur la chine, ou en porte-à-faux au-dessus
du vide, **sans qu'aucune erreur ne le dise**. Le pincement devient au contraire lisible : sur la
vignette de dessus, le complexe se resserre avec la coque.

### La seule chose écrite en absolu : la voie de conduite

Une conduite est une pièce **rigide** de 2,78 m que le moteur pose telle quelle sur le repère ;
lui appliquer `kx` déplacerait le repère sous la pièce au lieu de la pièce sur le repère
(c'est déjà ce que dit `ARTERY_CONDUITS`). La voie est donc droite — et **il y en a deux** :

- `x = +9,20` à l'entrée, où le bord est à sa largeur nominale ;
- `x = +8,20` à la sortie, où il sort à peine du pincement (`_side_scale = 0,888` à `s = 436,6`)
  et où la voie d'entrée **passerait sous le plancher**. Le harnais le refuse, chiffre à l'appui.

La ligne ressort donc un mètre plus près de l'axe. Ce n'est pas un pis-aller : ça se lit comme un
renvoi, le complexe a dévié la conduite qu'il traverse.

---

## 2. Les cinq repères — `CTRL | Complexe NN`

Ils marquent le **BAS** de la pièce (convention `CortegeConduit._seat()` : boîte englobante
mesurée, jamais l'origine du fichier, qui vaut `(−0,36 ; 1,00 ; 1,38)` pour la conduite droite).
Leur `y` est le **dessus du berceau**, lui-même échantillonné sur la peau — `_surface_box()` prend
ses quatre coins dans `_surface_y()` et rend le Y de son dessus.

| Repère | `s` | `x` absolu | `y` (bas) | peau | berceau | dessus d'une coudée | ciel |
|---|---:|---:|---:|---:|---:|---:|---:|
| `CTRL \| Complexe 01` | 419,6 | +9,20 | **−4,6773** | −4,9714 | +0,294 | −3,757 | 0,557 |
| `CTRL \| Complexe 02` | 422,4 | +9,20 | **−4,6773** | −4,9714 | +0,294 | −3,757 | 0,557 |
| `CTRL \| Complexe 03` | 425,2 | +9,20 | **−4,6777** | −4,9714 | +0,294 | −3,758 | 0,558 |
| `CTRL \| Complexe 04` | 438,0 | +8,20 | **−4,6790** | −4,9657 | +0,287 | −3,759 | 0,559 |
| `CTRL \| Complexe 05` | 440,8 | +8,20 | **−4,6661** | −4,9557 | +0,290 | −3,746 | 0,546 |

Quatre valeurs distinctes sur cinq. **Trois choses échouent le build** : les cinq `y` égaux (le
repère serait une constante recopiée — la dette payée au `BRIEF-0110` sur `CortegeArtery.DECK_Y`),
une assise au niveau de la peau (le berceau n'aurait pas été posé), et une conduite **coudée**
(0,92 m, mesuré sur `artery_conduit_bend.glb`) qui dépasserait le plafond de construction.

Chaque berceau porte **deux selles sombres** de part et d'autre : à 70° de plongée, c'est ce
qu'on voit sous le tube, et c'est ce qui dit qu'il est *posé*.

⚠️ **Les deux portiques sont hors de la voie, et c'est une contrainte mesurée.** Leur linteau est
à −3,90 ; une conduite coudée assise sur son berceau culmine à **−3,757**, donc 14 cm plus haut.
Un portique à cheval sur la voie serait traversé par la pièce que le concepteur a le droit d'y
monter, sans erreur d'import ni test rouge. Les seuils enjambent donc le **plancher** ; deux
bornes leur répondent de l'autre côté de l'allée.

---

## 3. Les critères, un par un, avec leur chiffre

| Critère du brief | Mesure | |
|---|---|---|
| Tient dans `s ∈ [418 ; 472]`, tribord, 8 m de garde aux deux tourelles | emprise **418,0 → 442,5** ; garde 8,00 m à `Turret_13` (410,0) et 36,3 m à `Turret_17` (478,8) ; harnais bloquant | ✅ |
| Rien au-dessus de −3,20, **mesuré sur le binaire** | sommet du complexe **−3,460** (marge 0,260 m sous le plafond de construction, 0,460 sous le plafond de vol −3,00). Pièce la plus haute montable sur un repère : **−3,746**. Le sommet du tronçon 5 reste **−3,200** (le mât d'Ambry) | ✅ |
| Rien sur l'axe du canal | point le plus proche **x = 5,82** (au pincement), soit **4,12 m** du rebord du canal (1,70). La conduite d'artère de `s = 435` (`x = −3,60`) est **inchangée au micron** | ✅ |
| Quatre à six `CTRL \| Complexe NN`, `y` échantillonné, marquant le bas | **cinq**, §2 | ✅ |
| Il se lit comme un LIEU — capture avant/après au même cadrage, conduites instanciées | `BRIEF-0111-planche.png`, vignettes 1 et 2, §4 | ✅ |
| Les harnais du corridor restent verts | build vert : taper/baies, fosses, tranchées, bastions, canal, garde mutuel des marqueurs, plafond, jonctions, contrat de noms, UV, largeur, couleurs réservées, orientation. `./scripts/check.sh` **ALL GREEN** (1021 tests, 8745 assertions, 0 échec) | ✅ |
| Déterminisme | **3 exécutions → même sha256** `c59ae7f965cc83740665a7ac255bdf180d5df72b9f6e352909a2bc7d8cf2bf33` ; `./scripts/build-hull.sh --check long_cortege` : *déterminisme OK* | ✅ |
| Le compte de triangles est RAPPORTÉ, jamais contraint | §5 | ✅ |

---

## 4. « On voit une installation » — mesuré, pas affirmé

Deux vignettes, **même caméra, même cadrage, même éclairage**, le cadrage étant *calculé* et non
choisi (`_plant_frame_centre()` intersecte les rayons de bord du champ avec le plan du pont). Les
cinq conduites et leurs flexibles sont **réellement instanciés**, par la correction d'assise exacte
du jeu.

| Bande tribord du cadre (770 px de large) | AVANT | APRÈS | |
|---|---:|---:|---|
| pixels porteurs d'arête (gradient > 18) | 2 723 | **16 241** | **+496 %** |
| part des pixels couverts qui portent une arête | 0,4 % | **2,5 %** | ×6,2 |
| pixels couverts | 669 541 | 639 835 | −4,4 % |
| **luminance moyenne** | 52,4 | **49,7** | **−5,2 %** |
| pixels magenta | 0 | **82** | +82 |

Sur le cadre entier, les arêtes passent de 25 023 à 42 077 (**+68 %**).

Les deux dernières lignes sont celles qui comptent pour le piège du lot : **le complexe n'a pas
éclairci le cadre, il l'a structuré**. La couverture *baisse* (le bassin est un trou), la
luminance moyenne *baisse*, et l'on gagne cinq fois plus d'arêtes. Le chasseur et ses balles se
lisent par-dessus (charte §6) : 82 pixels magenta ajoutés sur 831 600, et aucun cyan ni corail.

---

## 5. Les comptes — rapportés, jamais contraints

| | AVANT | APRÈS | Δ |
|---|---:|---:|---:|
| **le complexe seul** | — | **1 756 tri** | — |
| Section_01 | 6 440 | 6 440 | **0** |
| Section_02 | 10 212 | 10 212 | **0** |
| Section_03 | 9 768 | 9 768 | **0** |
| Section_04 | 12 536 | 12 536 | **0** |
| Section_05 | 10 502 | **12 686** | +2 184 |
| **corridor** | **49 458** | **51 642** | **+2 184** |

Les 2 184 se décomposent en : le complexe (1 756), les parois et le fond du bassin, les cellules
de peau **non émises** à son emprise (10 de plus), et la **redistribution des modules semés du
seul tronçon 5** — la zone interdite du complexe rejette des tirages, ce qui décale le flux `rng`
en aval (plaques 88 → 98, nervures 18 → 23, pastilles 21 → 23, travées 3 → 5). Les tronçons 1 à 4
sont **identiques au bit près**.

Autres relevés sur le `.glb` livré :

- **surface** 45 488,3 → 46 674,5 m² ;
- **émissif** 226,18 → **227,38 m²** (+1,20 m², soit **+0,53 %**) — trois barres de passerelle et
  quatre feux de seuil, rien d'autre ;
- `AA_Trim` 100,84 → 114,35 m² (les deux **bouts** du coaming du bassin) ;
- `AA_Panel` 41,15 → 44,79 m² (six dessus de cuve et de cheminée) ;
- **28 primitives sur 28 avec `TEXCOORD_0` et `TANGENT`** — comptés dans le binaire, pas supposés.

Aucun de ces chiffres n'a servi à couper quoi que ce soit. Le seul plafond qui a réellement
décidé de la forme est le **plafond de vol** : c'est lui qui interdit `stern_pylon.glb` (5,30 m
pour 1,79 m de ciel) et qui envoie tout le volume **vers le bas** — le bassin de 1,63 m est la
seule masse d'un mètre et demi que ce lot pouvait offrir.

---

## 6. Texture et animation

**Aucune image** (`ADR-0028`), conformément à la section `## Texture` du brief : PBR par facteurs,
quatre slots du kit (`AA_Hull`, `AA_Greeble`, `AA_Panel`, `AA_Emissive_Engine`) plus `AA_Trim`
pour les deux bouts du coaming.

Le complexe est maillé **dans le bmesh du tronçon**, et non à côté comme Ambry. Ambry a son propre
objet parce qu'elle a sa propre échelle d'UV (0,700 tuile/m) et son propre huitième slot ; le
complexe est de la matière de l'Unisson, à la même distance de vue. Il est donc déplié **avec le
bordé**, en projection en boîte à **0,200 tuile/m (5,00 m par tuile)** :

| | cible | mesuré | anisotropie max |
|---|---:|---:|---:|
| Section_05 **après** | 0,200 t/m | 0,141 à 0,200, **moyenne 0,198** (5,06 m/tuile) | 1,42 |
| Sections 02 à 04 (témoins) | 0,200 t/m | 0,141 à 0,200, moyenne 0,197 | 1,42 |

Le lot **ne dégrade pas** la densité : le tronçon 5 est au niveau de ses voisins. Le minimum de
0,141 est la borne de la méthode (une face à 45° projette en `cos 45°`), pas un étirement.

Le brief demande une projection en boîte, donc pas de dépliage continu — mais la planche porte
quand même une **vignette au damier UV à la perspective du jeu** (grande case = 1 tuile de 5,00 m,
petite = 62,5 cm) : sur un lot où une pièce épouse un pincement de 15 %, un étirement qui ne se
découvrirait qu'après la texture générée serait découvert trop tard.

`AA_Emissive_Engine` **seulement sur ce qui doit s'éteindre** : trois barres de 0,10 m au-dessus
du bassin et quatre feux de seuil, 1,20 m² au total. `CortegeSkin.emissives_of()` les éteindra
avec le reste de la coque au blackout de la fin.

**Animation** (`ADR-0046` §6) : le brief déclare la structure **figée**, et elle l'est —
0 animation dans le `.glb`. Les conduites apportent les leurs.

---

## 7. Une décision qui a été prise, mesurée, puis retournée

Le complexe a d'abord été inscrit dans `_installation_spans()`. C'est ce que dit la règle du
`BRIEF-0094` — « un module de relief ne se pose que dans l'emprise d'une installation » — et cela
lui donnait ses plaques d'ancrage.

**La capture a montré le prix.** `MARKER_APRONS` est la *fusion* des emprises et ne garde **aucun
x** : ouvrir 27,7 m à tribord les ouvre aussi **à bâbord**. Le bord opposé, vide en face du
complexe, s'est couvert de **quarante-cinq plaques** — exactement le « détail presque partout »
que le `BRIEF-0094` avait supprimé — et le calme du tronçon 5 tombait de 43,8 % à 19,2 %.

Le complexe porte donc **son propre appareillage** (longerons, plots, traverses, berceaux) et ne
demande rien au vocabulaire semé. Conséquence voulue : les cinq tronçons gardent leurs modules.
Son emprise entre quand même dans le **compte de calme** — `build_section()` l'ajoute à `occupied`
comme les fosses, les tranchées et la passerelle. *« Un indicateur qui ne voit pas ce qu'on vient
d'ajouter ne mesure plus rien. »*

Deux autres arbitrages menés au rendu, et non au jugement :

- **l'ivoire a été réduit deux fois.** Le coaming du bassin était clair sur ses quatre bords : il
  devenait la chose la plus lumineuse du cadre et **volait la lecture à Ambry**, qui arrive quatre
  mètres plus loin et dont tout l'intérêt est d'être la seule chose claire des 500 m. Il ne reste
  clair que sur ses **deux bouts** — la règle exacte que `build_pits()` avait déjà payée.
- **le violet est revenu, mais sur des VOLUMES.** Un capot rectangulaire en `AA_Panel` se lisait
  comme un décalque posé ; il est repassé en matière de coque. Les six dessus **ronds** (quatre
  cuves, deux cheminées) le gardent : à 45,8 px/m, une silhouette ronde est le seul signal du
  niveau qui ne se confonde avec rien d'autre.

---

## 8. Ce que je n'ai pas pu tenir, et pourquoi

1. **Les 54 m d'emprise.** Livré 24,5. Ambry occupe le reste du bord (§0). Je n'ai pas déplacé
   Ambry ni mordu dessus : elle est hors périmètre, et c'est le seul avant-poste humain des 500 m.
   Ce qu'il reste à meubler sur ce bord après ce lot : **rien**.
2. **L'emprise en `x` du brief (`[6,3 ; 10,6]`) est débordée vers le large** : je vais jusqu'à
   **12,30 en nominal**, c'est-à-dire jusqu'à la cassure de facette. Raison : entre 6,80 (lèvre de
   chine) et 12,35 la coque est plate à **16 cm près sur 5,5 m** — c'est la seule bande du
   vaisseau où une installation s'étend sans être coupée par une pente. S'arrêter à 10,6 aurait
   donné une bande que le pincement réduit à 3,6 m, trop mince pour lire comme un lieu, et aurait
   laissé une lisière nue entre le complexe et le bord. Rien ne dépasse la silhouette : au plus
   large, le complexe s'arrête **1,70 m en dedans** du bord de coque.
3. **Le calme du tronçon 5 tombe de 43,8 % à 19,2 %** (total du corridor : 45,5 % → 40,6 %). Ce
   n'est pas un effet de bord, c'est l'objet du lot — 24,5 m de bordé nu deviennent une
   installation — mais c'est le tronçon le plus chargé du vaisseau, et il vaut d'être dit. La plus
   longue plage nue du tronçon passe de 24,6 m à 17,0 m.
4. **Les cinq repères prennent la pièce DROITE en toute sécurité ; la COUDÉE passe partout sauf
   sous les portiques**, où elle culminerait 14 cm au-dessus du linteau. Les seuils ont été
   déplacés hors de la voie pour que ce cas n'existe pas — mais si le concepteur ajoutait un
   portique à cheval sur la ligne, l'audit le refuserait.
5. **Le brief demande « quatre à six conduites » et j'en pose cinq**, mais elles sont sur **deux
   voies** et non une (§1). Une ligne unique traversant tout le complexe était impossible : au
   pincement, une voie droite unique sort du pont ou passe sous le plancher.
6. **Aucun `stern_pylon.glb` n'est posé** : 5,30 m pour 1,79 m de ciel, le brief le dit lui-même.
   Aucun `artery_hose` n'est instancié par la coque non plus — c'est `CortegeConduit._mount_hose()`
   qui le monte en frère, et la planche le reproduit.

---

## 9. Refaire ces livrables

```bash
# la coque, déterministe
./scripts/build-hull.sh --check long_cortege

# la planche — ⚠️ -t 1 : le mode --complexe REBÂTIT le .glb, et le multi-thread
# fait diverger les tangentes (voir l'en-tête de build-hull.sh)
git show HEAD:assets/imported/models/backgrounds/long_cortege.glb \
  | git lfs smudge > /tmp/long_cortege_avant.glb
blender-aegis -b -t 1 -P tools/blender/build_long_cortege.py -- \
  --complexe --avant /tmp/long_cortege_avant.glb
```

La planche fait 1920 × 4600 : AVANT, APRÈS, damier UV (les trois à la caméra du jeu, 1920 × 1080),
vue de dessus orthographique (22 m, proue à gauche, avec `Turret_13` et le premier collier d'Ambry
pour contexte), élévation tribord avec la **dalle du plafond de vol matérialisée**.

---

## 10. Suggestions pour la suite

- **Les deux vides de bâbord** (`s 415 → 450`, 35 m, et `s 470 → 500`, 30 m) restent nus, comme le
  brief le prévoit. Le second est le dernier bordé avant la poupe : c'est là qu'un second lot
  paierait le plus. ⚠️ **Refaire le relevé sur la géométrie et non sur les marqueurs** — le pont
  d'envol `Bay_07` (450,0) et la passerelle sont des pièces, pas des marqueurs.
- **La règle « une installation ouvre les deux bords »** de `MARKER_APRONS` est un vrai défaut de
  ce fichier, pas seulement une gêne pour ce lot : Ambry ouvre déjà 32 m de bâbord pour rien.
  Rendre `_in_apron()` / `_inside_zone()` sensibles au bord se ferait en une dizaine de lignes,
  mais rejouerait le tirage des cinq tronçons — c'est un lot à lui seul.
- **Le concepteur peut monter la pièce coudée** sur `CTRL | Complexe 01` et `05` pour marquer
  l'entrée et la sortie de la ligne ; les trois autres gagnent à rester droites (la ligne se lit
  comme une ligne).
