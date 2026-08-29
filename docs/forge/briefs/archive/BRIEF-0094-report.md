# BRIEF-0094 — compte-rendu de forge

> **Trois lots livrés complets**, dans l'ordre de priorité du brief : l'artère devient une
> tranchée (P1) et le nœud d'épine devient un kit, la palette se replie sur la structure (P2),
> le relief se rassemble autour des installations et laisse la moitié du bordé nue (P3).

- **Brief** : [`BRIEF-0094-artere-palette-relief.md`](BRIEF-0094-artere-palette-relief.md)

## Texture

⛔ **Aucune demande `TEX-NNNN`, et c'est la position du brief, reprise telle quelle.** Sa section
`## Texture` est **présente et elle tranche** : « ce brief redistribue des matériaux existants et
remodèle de la géométrie ; il n'introduit aucune surface qui appellerait une carte neuve ».
`TEX-0010` à `TEX-0014` sont livrées et intégrées, et les huit slots du `.glb` sont exactement
ceux d'avant. Livré : **géométrie, UV et slots**, rien d'autre — aucune image, aucun
`baseColorTexture`, vérifié sur le binaire par le harnais (`ADR-0028`).

⚠️ **Une réserve, et elle est la raison d'un arbitrage non pris** (§8.1) : la cible « 15 % de
grège moyen » n'a de slot dans aucune palette du dépôt. Créer le neuvième slot aurait appelé une
carte neuve — donc contredit cette section-ci. Le slot est **proposé, pas créé**.

> *Cette section existe aussi parce que `scripts/lint-regles.sh` lit tout
> `docs/forge/briefs/BRIEF-*.md` comme un brief, ce compte-rendu compris. La règle a raison de ne
> pas faire d'exception : un document de forge qui parle de matière dit où il en est.*

## Livrables

| Chemin | Nature | Octets |
|---|---|---|
| `assets/imported/models/backgrounds/long_cortege.glb` | coque remodelée (5 tronçons, 30 marqueurs) | 1 884 056 |
| `assets/imported/models/backgrounds/spine_kit.glb` | **neuf** — kit de nœud d'épine, 3 pièces | 33 088 |
| `docs/forge/output/BRIEF-0094-planche-epine.png` | **neuve** — planche de recette, 1440 × 3260, 6 vignettes | 4,8 Mo |
| `docs/forge/output/BRIEF-0089-planche-sections.png` | planche de la coque, régénérée | 5,7 Mo |
| `tools/blender/build_long_cortege.py` | source de la coque (ADR-0008) | — |
| `tools/blender/build_spine_kit.py` | **neuf** — source du kit d'épine | — |
| `tools/blender/build_turret_kit.py` | **modifié uniquement pour le plafond** (voir §7) | — |

Provenance : trois lignes touchées dans `assets/licenses/ASSET_PROVENANCE.csv` (deux créées,
`spine_kit` et `brief_0094_planche_epine` ; deux mises à jour, `long_cortege_hull` et
`brief_0089_planche_sections`).

**Vérifications dures**

```
./scripts/build-hull.sh --check long_cortege   déterminisme OK — a3ce2c09…b3d9
./scripts/build-hull.sh --check spine_kit      déterminisme OK — 0300db4b…0561
./scripts/build-hull.sh --check turret_kit     déterminisme OK — 2a1924b7…b3e5   (inchangé)
./scripts/build-hull.sh --check bay_kit        déterminisme OK — 03632a3e…cac1   (inchangé)
./scripts/check.sh                             ALL GREEN — 767 tests, 5 656 assertions, 0 échec
```

`turret_kit.glb` et `bay_kit.glb` sont **byte-identiques** à ce qu'ils étaient : le brief dit de
ne pas y toucher, et la seule ligne modifiée du kit de tourelle est un harnais d'audit.

---

## 1. Les chiffres, tous relevés sur le binaire produit

### Triangles

| Tronçon | tri | % du budget (18 000) |
|---|---:|---:|
| Section_01 | 6 432 | 35,7 % |
| Section_02 | 4 560 | 25,3 % |
| Section_03 | 4 616 | 25,6 % |
| Section_04 | 4 404 | 24,5 % |
| Section_05 | 5 686 | 31,6 % |
| **coque** | **25 698** | **28,6 %** du budget total (90 000) |

Avant ce lot : 36 026. La coque **perd 10 328 triangles** (−28,7 %) tout en gagnant l'artère
et ses travées. Les trois postes : le champ de plaques passe de 1 071 à 462 modules, les
pastilles de 384 à 119, les cinq bulbes d'épine disparaissent (≈ 1 250 tri).

| Kit d'épine | tri |
|---|---:|
| `spine_cradle` | 92 |
| `spine_core` | 140 |
| `spine_brace` | 48 (× 4) |
| **kit livré** | **280** |
| **nœud assemblé** | **424** / 1 400 |
| **cinq nœuds du niveau** | **2 120** / 7 000 |

Coque + les trois kits, pour le niveau entier : 25 698 + 2 120 (épines) + 44 863 (17 tourelles)
+ ~14 000 (7 hangars) ≈ **86 700** sur 90 000 — le budget tient, avec le décor le plus léger
qu'il ait jamais eu.

### UV — comptées dans le binaire, jamais supposées

| Fichier | primitives | `TEXCOORD_0` | `TANGENT` |
|---|---:|---:|---:|
| `long_cortege.glb` | 28 | **28 / 28** | 28 / 28 |
| `spine_kit.glb` | 9 | **9 / 9** | 9 / 9 |

Dépliage : **projection en boîte**, comme le prescrit `BRIEF-0089` pour une pièce vue de loin.
Le brief ne demandait pas de dépliage continu ; les coutures sont donc celles de la méthode (un
changement d'axe dominant par face), et le damier UV de la planche le montre à la perspective du
jeu — dernière vignette.

**Densité de texels mesurée** (valeurs singulières, triangle par triangle) :

| Pièce | cible | mesure min → max | moyenne | m/tuile | anisotropie max |
|---|---:|---|---:|---:|---:|
| Section_01 | 0,200 | 0,144 → 0,200 | 0,197 | 5,07 | 1,39 |
| Section_02..05 | 0,200 | 0,147 → 0,200 | 0,197–0,198 | 5,06–5,07 | 1,36 |
| Ambry | 0,700 | 0,609 → 0,700 | 0,699 | 1,43 | 1,15 |
| `spine_cradle` | 0,200 | 0,120 → 0,200 | 0,196 | 5,10 | 1,67 |
| `spine_core` | 0,200 | 0,121 → 0,200 | 0,183 | 5,46 | 1,65 |
| `spine_brace` | 0,200 | 0,159 → 0,200 | 0,196 | 5,10 | 1,26 |

Le plancher n'est pas la cible : une projection en boîte étire par `1/cos(angle à l'axe
dominant)`, et le pire cas géométrique est `√3 = 1,732`. Aucune face ne descend sous cette
borne ; le harnais échoue le build si l'une le fait.

### Aires par matériau — deux colonnes, et la seconde est la seule qui parle de l'écran

L'aire **totale** d'une coque de 500 m est aux deux tiers son ventre, que la caméra du jeu (70°
de plongée) ne voit jamais ; s'y ajoutaient jusqu'ici **6 000 m² de jupes enterrées** de modules,
toutes en `AA_Greeble`. Comparer la cible 80/15/5 — qui décrit des **pixels** — à ce chiffre-là
n'a aucun sens. L'aire **vue** est donc mesurée à part : une face compte si sa normale regarde la
caméra *et* si elle est au-dessus de la peau à son propre (x, s). C'est une approximation, elle
ignore les occultations entre pièces, et elle est déclarée comme telle dans le code.

| Matériau | aire totale | % | **aire vue** | **%** | avant (total) |
|---|---:|---:|---:|---:|---:|
| `AA_Hull` (anthracite `#24252B`) | 15 695,1 m² | 32,50 % | 15 328,7 m² | **76,62 %** | 24,98 % |
| `AA_Greeble` (creux `#141419`) | 31 814,4 m² | 65,88 % | 3 997,7 m² | **19,98 %** | 64,79 % |
| `AA_Hull_Ambry` (`#EDEAE3`) | 344,9 m² | 0,71 % | 279,1 m² | 1,40 % | 0,62 % |
| `AA_Emissive_Engine` (magenta) | 193,8 m² | 0,40 % | 193,6 m² | **0,97 %** | 0,43 % |
| `AA_Panel` (violet `#452663`) | 97,3 m² | **0,20 %** | 97,3 m² | **0,49 %** | **7,52 %** |
| `AA_Marking_Red` | 85,7 m² | 0,18 % | 52,5 m² | 0,26 % | 0,15 % |
| `AA_Trim` (ivoire `#DDDCD2`) | 32,9 m² | **0,07 %** | 32,6 m² | **0,16 %** | **1,46 %** |
| `AA_Glass` | 25,5 m² | 0,05 % | 25,5 m² | 0,13 % | 0,05 % |
| **TOTAL** | 48 289,7 m² | | 20 007,0 m² | | |

**Contre la cible du brief, sur l'aire vue :**

| Rôle | mesuré | cible | écart |
|---|---:|---:|---:|
| structure — gris / anthracite | **78,01 %** | 80 % | −2,0 pt ✅ |
| appareillage — la machinerie | **20,53 %** | 15 % | +5,5 pt ⚠️ |
| violet + magenta | **1,45 %** | 5 % | −3,6 pt ✅ |

**Le violet a reculé de 93 %** en aire totale (7,52 % → 0,20 %), là où l'opérateur en demandait
60 à 70 %. C'est délibérément au-delà : voir §3.

Kit d'épine, mêmes trois colonnes (kit brut / nœud assemblé / vu) :

| Matériau | kit | assemblé | **vu** |
|---|---:|---:|---:|
| `AA_Greeble` | 9,60 m² (71,4 %) | 11,23 m² (68,2 %) | 4,76 m² (48,1 %) |
| `AA_Hull` | 2,66 m² (19,8 %) | 3,86 m² (23,4 %) | 3,86 m² (38,9 %) |
| `AA_Emissive_Engine` | 0,87 m² (6,5 %) | 0,87 m² (5,3 %) | 0,79 m² (**8,0 %**) |
| `AA_Trim` | 0,32 m² (2,4 %) | 0,50 m² (3,0 %) | 0,50 m² (5,0 %) |

---

## 2. PRIORITÉ 1 — l'artère est une tranchée

### Ce qui a changé dans le profil

La **crête dorsale a disparu**. Elle culminait à −3,62 et portait sur son arête, en continu sur
500 m, une bande `AA_Emissive_Engine` de 0,28 m doublée d'un liseré ivoire de 0,64 m — posée sur
le point le plus haut du vaisseau. « L'artère est beaucoup trop proche d'un laser géant » : le
défaut n'était pas dans `TEX-0013`, qui respectait sa consigne, il était dans la géométrie qui
lui offrait une bande pleine sur une crête.

```
|x| ≤ 0,88   FOND du canal à −4,58, plat  (1,76 m de fond utile)
|x| = 1,00   la paroi, 0,38 m
|x| = 1,12   arête interne du rebord, −4,02
|x| ≤ 1,70   le REBORD mécanique, sombre, 0,58 m par bord
|x| = 2,20   pied du bandeau dorsal, sur le pont à −4,26   ← identique à avant
```

- canal de **2,00 m** de large entre les arêtes internes des deux rebords (cote du brief) ;
- **enfoncé de 0,56 m** sous l'arête de son rebord, **0,32 m** sous le pont ;
- rebord `AA_Greeble` (`#141419`, le noir de creux du kit) de part et d'autre.

### Les conduits — 4 bandes, jamais toute la largeur, jamais continues

| Grandeur | valeur |
|---|---|
| voies | **4** (deux par bord), de **18 cm** et **12 cm** |
| aire éclairée en travers | 0,60 m sur 2,00 m de canal, soit **30 % de sa largeur** |
| longueur cumulée allumée | **1 078 m** sur 2 000 m de voies possibles (**54 %**) |
| longueur d'une portion allumée | 5,5 à 14,0 m, tirée par voie |
| coupure | 1,6 à 4,6 m, phase décalée par voie *et* par bord |
| travées sombres | **21** poutres de 0,55 m, enterrées de 0,62 m, tous les 16 à 30 m |

Les interruptions sont faites **deux fois** : un trou dans la lumière (la coupure de tirage) et
une **poutre qui barre la tranchée** (la travée). Un trou seul laisse un canal vide sur 4 m, qui
se lit comme une panne ; une poutre donne la même coupure *et* une raison mécanique.

⚠️ **Le fuseau de proue impose une découpe.** Le fond du canal y monte de 2,2 cm par mètre : une
bande de 14 m posée d'un trait sur le point le plus bas de ses quatre coins s'enterrerait de
26 cm à son extrémité haute et disparaîtrait sans un mot. Les conduits du tronçon 1 sont donc
émis par tronçons de 1,6 m ; ailleurs le fond est plat et la bande sort d'une seule pièce. C'est
ce qui explique les 113 modules de conduit du tronçon 1 contre 24 à 26 ailleurs.

L'artère **s'allume là où le vaisseau devient assez large pour la porter** : le fond plat du
canal est mis à l'échelle du fuseau, les voies extérieures n'existent qu'à partir de s ≈ 38 m.

⛔ **Plus aucun centre blanc continu** : `AA_Trim` ne touche plus aucune arête longitudinale (ni
la crête, qui n'existe plus, ni la lisse de chine — voir §3).

---

## 3. PRIORITÉ 2 — la palette

### Ce qui a quitté le violet

| Surface | avant | après | aire concernée |
|---|---|---|---|
| facette extérieure (segments 11 et 12 du profil) | `AA_Panel` | `AA_Hull` puis `AA_Hull` | **≈ 3 000 m²**, en continu sur 500 m par bord |
| plaques du bordé (12 % d'entre elles) | `AA_Panel` | `AA_Hull` / `AA_Greeble` | ≈ 250 m² |
| première couche de chaque greffe | `AA_Panel` | `AA_Hull` | ≈ 900 m² |
| **terrasse haute d'une greffe sur deux** | — | `AA_Panel` | **97 m²** — tout ce qui reste |

Les deux segments de facette faisaient à eux seuls 3,00 m de développé par bord **en continu sur
500 m** : c'étaient eux, les « gros rectangles violets posés partout ». Le violet ne survit
maintenant que sur un **volume**, et sur un volume qui monte.

### Ce qui a quitté l'ivoire

`AA_Trim` passe de 1,46 % à **0,07 %** de l'aire totale, et c'est une correction faite **au
rendu, pas au raisonnement** :

- la **lisse de chine** (0,36 m × 97 m, deux fois) donnait deux traits blancs pleins du haut au
  bas du cadre d'acceptation, en noir et blanc comme en couleur — les « rubans blancs » que le
  premier rendu du Cortège avait déjà payés, revenus par la seule pièce qu'on avait laissée
  claire. Elle passe en `AA_Greeble` ;
- les **chapeaux de nervure** (une sur trois, 4,65 m de long) mettaient quatre barres ivoire dans
  un seul cadre. Ils alternent maintenant deux valeurs sombres : la variation se lit à la lumière
  rasante, pas à la valeur.

Il ne reste d'ivoire que sur des pièces de moins de 2 m² : échines de greffe, sole du berceau
d'épine, aiguille du cœur.

### Les greffes se distinguent par leur hauteur, leur orientation et leur silhouette

« Réduire le violet **et** relever ces masses est la même correction, pas deux. » Les trois :

1. **hauteur** — les couches montaient de 0,28 à 0,42 m, bridées par la crête qui ne laissait que
   0,40 m de dégagement au centre. La crête a disparu : le pont offre 1,04 à 1,10 m sous le
   plafond de construction, et les couches montent de **0,34 à 0,54 m**. Une greffe fait
   désormais **0,7 à 1,05 m** de haut au lieu de 0,3 à 0,8 ;
2. **orientation** — toutes les empreintes étaient alignées sur les axes du vaisseau, donc
   indiscernables du bordé autrement que par la couleur. Une primitive nouvelle
   (`_surface_poly`) les pose **tournées de 7 à 23°**, le sens alternant d'une greffe à l'autre ;
3. **silhouette** — 2 à 3 terrasses décroissantes plus, une fois sur 2,5, une échine étroite.

⚠️ **Le violet est passé de « toutes les couches sauf la première » à « la terrasse haute d'une
greffe sur deux » après avoir regardé le rendu.** Sur toutes les couches, il produisait un
parallélogramme violet plein sur chaque greffe — le « gros rectangle violet posé » du brief,
simplement tourné. Sur une greffe sur deux, la couleur cesse de *désigner* la greffe (c'est la
silhouette qui le fait) et redevient un accent.

---

## 4. PRIORITÉ 3 — le relief et les zones calmes

### La règle appliquée

**Un module de relief ne se pose que dans l'emprise d'une installation.** Ailleurs, la tôle est
nue — et elle n'est pas vide pour autant : `TEX-0010` (bordé/plaques) est livrée et intégrée,
elle porte les joints, les rivets et l'usure que la géométrie faisait à sa place. C'est le
partage que l'en-tête du script annonce depuis `BRIEF-0089` (« le détail perçu vient des
textures, pas des triangles ») et qui n'avait jamais été appliqué.

Les emprises sont **dérivées des marqueurs**, jamais écrites à la main : ±4,2 m autour d'une
tourelle, ±5,4 m autour d'un pont d'envol, ±3,8 m autour d'un nœud, l'emprise d'Ambry +2,0 m.
Les greffes sont **hébergées** par ces emprises (elles doivent y tenir tout entières) et
deviennent à leur tour des points d'ancrage pour les plaques et les pastilles.

⚠️ **Contenance, et surtout pas intersection.** La première version testait l'intersection : une
greffe de 11 m qui effleurait le bord d'une emprise de 8,4 m débordait de 10 m sur la plage nue
voisine, une plaque acceptée au contact débordait de 3, et de proche en proche la part calme
mesurée tombait à **13 %** pour un plafond théorique de 50. Un module qui déborde ne « dépasse »
pas un peu : il **déplace la frontière**, et la frontière est le livrable.

### La mesure, et sa définition

> Est **calme** un mètre de longueur du tronçon dont le **bordé** ne porte aucun module en
> relief. Sont exclus du compte, parce qu'ils sont continus **par construction** et n'ont donc
> pas de rythme à rompre : l'**artère** et tout ce qui vit entre ses rebords (|x| ≤ 1,70 :
> conduits, travées, nœuds), et les **lisses longitudinales**, qui donnent au joueur sa seule
> lecture continue de la vitesse. Sont comptés : plaques, nervures, greffes, pastilles, et
> l'emprise des installations elles-mêmes.

| Tronçon | calme | part | plus longue plage | plages ≥ 8 m |
|---|---:|---:|---:|---:|
| Section_01 | 65,2 m | 65,2 % | **46,2 m** | 3 |
| Section_02 | 47,8 m | 47,8 % | 15,0 m | 3 |
| Section_03 | 49,6 m | 49,6 % | 20,0 m | 3 |
| Section_04 | 55,2 m | 55,2 % | 17,6 m | 3 |
| Section_05 | 33,6 m | 33,6 % | 9,6 m | 1 |
| **TOTAL** | **251,4 m** | **50,3 %** | **46,2 m** | **13** |

⚠️ **50,3 % est le plafond, pas un réglage.** Les trente marqueurs de gameplay occupent 248,6 m
d'emprises fusionnées et laissent 251,4 m en 22 plages, dont 9 de 12 m ou plus (les cinq plus
larges : s 0–46, s 187–210, s 91–114, s 254–274, s 364–382). La forge atteint ce plafond
**exactement** : aucun module ne sort de son emprise. Faire mieux demanderait de déplacer des
marqueurs — c'est un arbitrage de conception, il est en §8.

Compte des modules après restriction : 462 plaques (1 071 avant), 78 nervures (182), 100 greffes
(103), 119 pastilles (384), 42 lisses (inchangé), 213 conduits et 21 travées (nouveaux).

---

## 5. Le kit d'épine — table des emprises

**Repère local du marqueur `Spine_NN`** (X latéral, Y haut, Z survol, +Z = proue).
`Y = 0` est le **plan d'assise dans le fond du canal**, porté par le marqueur.

| Pièce | parent | position d'assemblage | copies | tri |
|---|---|---|---|---:|
| `spine_cradle` | marqueur | `(0, 0, 0)` | 1 | 92 |
| `spine_core` | marqueur | `(0, +0,21, 0)` | 1 — **la seule détruite** | 140 |
| `spine_brace` | marqueur | `(±0,50, +0,30, ±dz)`, yaw 0 ou π | 2 ou 4 | 48 |

- `dz = 0` pour deux entretoises, `0,78` pour quatre.
- Le **yaw vaut π du côté bâbord** : la pièce penche toujours vers son −X local, donc toujours
  vers l'axe du nœud. Aucun tangage à écrire côté moteur — l'inclinaison est dans la géométrie.
- `spine_core` se pose à **+0,21** et non à +0,30 : sa base repose au **fond de la cuvette** du
  berceau, pas sur le plateau. Le poser à +0,30 le ferait flotter de 9 cm dans son logement — un
  défaut invisible à 23 px/m et visible sur toutes les images une fois le nœud abattu.

### Cotes relevées sur le binaire

| Grandeur | valeur | cote du brief |
|---|---|---|
| hauteur totale du nœud | **1,50 m** | 0,7–1,0 × 1,76 m → viser 1,50 |
| emprise du berceau | **1,32 × 2,56 m** | plus large que le cœur ✅ |
| fût | 0,68 m de large pour 1,29 m de haut (**1,90 : 1**) | — |
| lanterne émissive | 0,30 m, soit **20 %** du nœud | règle dure : ≤ 25 % |
| couronne horizontale | 0,16 m de large | — |
| capot sombre | 0,20 m | — |
| entretoise | 0,34 m de déport pour 0,62 m de montée = **28,7°** | — |
| émissif par pièce | berceau **0,000 m²**, cœur **0,873 m²**, entretoise **0,000 m²** | règle dure du brief ✅ |

### Les cinq emplacements, mesurés sur la coque livrée

| Marqueur | assise | bas d'emprise | dénivelé | rebord | sommet | hors tranchée | marge au plafond décor |
|---|---:|---:|---:|---:|---:|---:|---:|
| Spine_01 | −4,811 | −4,869 | 0,058 | −4,367 | −3,311 | 1,056 | 0,311 |
| Spine_02..05 | −4,580 | −4,580 | 0,000 | −4,050 | −3,080 | 0,970 | 0,080 |

La tranchée **cache 0,44 à 0,53 m** du nœud ; il en dépasse 0,97 à 1,06 m. Le sommet reste sous
le plafond du **décor inerte** (−3,00) : le nœud n'a **pas** besoin du plafond de gameplay
relevé, contrairement aux tourelles.

### La troisième silhouette

Ce qui sépare les deux premières est un axe : l'un **creuse**, l'autre **dépasse**. Une
troisième pièce ne peut pas se placer sur cet axe-là sans tomber du côté de l'un des deux. Elle
se place donc sur un autre :

| | signe | orientation | proportion |
|---|---|---|---|
| hangar | négatif | horizontal | rectangulaire, un cadre vide |
| tourelle | positif | horizontal | trapue, un tambour et deux tubes |
| **nœud** | positif | **vertical** | **effilé**, un fût et des diagonales |

Deux signaux, tous deux géométriques (ils survivent au noir et blanc et aux 23 px/m) : la seule
pièce du niveau plus haute que large, et la seule qui porte des **obliques**.

⚠️ **Et un troisième signal, ajouté après avoir regardé la planche.** La caméra du jeu plonge à
70°, donc à 20° de la **verticale** : un flanc de lanterne, même évasé, lui est présenté presque
de profil et ne rend quasiment aucun pixel, tandis que le capot occupe tout le dessus. Premier
tirage : **un nœud parfaitement sombre à la perspective du jeu** — la seule cible du niveau dont
la récompense arrive quarante secondes plus tard, et on ne la voyait pas. La réponse est une
surface émissive qui **regarde la caméra** : un anneau quasi horizontal de 16 cm au sommet de la
lanterne, entre son bord (0,34) et le pied du capot (0,18). Vu d'en haut, le nœud est un **anneau
clair autour d'une pointe sombre** — une figure que ni la tourelle ni le hangar ne produisent.

Six primitives principales (la règle en autorise 6 à 8) : le berceau, le fût, la lanterne, le
capot, l'aiguille, les entretoises.

### Deux familles, par assemblage seul

| Famille | entretoises | dz |
|---|---:|---:|
| A — deux entretoises | 2 | 0,00 m |
| B — quatre entretoises | 4 | 0,78 m |

Et un troisième état, qui n'est pas une famille mais le cœur du partage : **la carcasse**. Le
moteur détruit `spine_core` seul ; berceau et entretoises restent, sans un seul émissif. La
troisième vignette de la planche montre les deux côte à côte.

---

## 6. Les marqueurs — ce qui a bougé et ce qui n'a pas bougé

| | noms | X | Z | Y |
|---|---|---|---|---|
| `Turret_01..17` | inchangés | inchangés | inchangés | **inchangés au micron** |
| `Bay_01..07` | inchangés | inchangés | inchangés | **inchangés au micron** |
| `Spine_01..05` | inchangés | inchangés | inchangés | **−3,160 → −4,580** (plan d'assise dans le canal) |
| `Ambry` | inchangé | inchangé | inchangé | inchangé |

Les 24 Y de tourelle et de pont sont **échantillonnés sur la peau** (`turret_seat_y`, rayon
2,08 m ; `bay_mouth_y`). Le profil a donc été refait de façon à être **identique au-delà de
x = 2,20** : le marqueur le plus intérieur est `Turret_05`/`Turret_08` à |x| = 5,60, dont
l'emprise descend à |x| = 3,52. C'est ce qui permet de ne rejouer ni `ACCEPTED_PAD_BAY_PROXIMITY`
ni les arbitrages de `BRIEF-0092`, et le harnais de marqueurs le vérifie sur le binaire.

---

## 7. Le plafond — le cliquet est remplacé par la vraie borne

`CEILING_OVERSHOOT_MAX = 0,43` a disparu de `build_turret_kit.py`. À sa place :

```python
GAMEPLAY_CEILING_Y = -2.40
FLYBY_SOURCE = ".../scripts/vfx/cortege_flyby.gd"

def _assert_gameplay_ceiling() -> None:
    """Le plafond recopie ici est-il celui que le moteur applique ?"""
```

⚠️ **La valeur est recopiée depuis le moteur — c'est le seul endroit des trois kits où ça
arrive — donc elle est confrontée.** Blender ne lit pas le GDScript ; le harnais relit
`scripts/vfx/cortege_flyby.gd`, y cherche `const GAMEPLAY_CEILING_Y :=` et échoue le build si les
deux nombres ont dérivé. Le contrôle porte maintenant sur le **sommet réel** de la tourelle la
plus haute, pas sur un dépassement figé :

```
10 tourelles sur 17 montent au-dessus du plafond du DÉCOR INERTE (−3,00), de 0,422 m au pire
   — et c'est ACTÉ : une tourelle se tire dessus.
la plus haute culmine à −2,578, soit 0,178 m sous le plafond des PIÈCES DE GAMEPLAY (−2,40)
   et 2,58 unités sous le plan de vol.
```

`turret_kit.glb` est byte-identique : seul l'audit a changé.

---

## 8. Ce que je n'ai PAS tranché — ce sont des décisions de conception

### 8.1 Le neuvième slot, « grège moyen » — proposé, pas créé

La cible d'appareillage est à **20,5 % au lieu de 15 %**, et l'écart n'est pas un défaut de
dosage : la palette de l'Unisson n'a **rien entre `AA_Hull` (`#24252B`) et `AA_Trim`
(`#DDDCD2`)**. Le brief autorise à proposer un slot de plus, sur le précédent d'`AA_Hull_Ambry`.
**Je ne l'ai pas créé, et pour une raison qui vient du brief lui-même** : sa section `Texture`
écrit qu'il « n'introduit aucune surface qui appellerait une carte neuve ». Or un nouveau slot en
appellerait une — `cortege_skin.gd` associe une carte à chaque matériau nommé, et un slot sans
carte reste un aplat. Créer le slot, c'était contredire la section `Texture` du même brief.

La proposition, si le concepteur la retient :

```
AA_Gear   "#5A5750"  grège moyen — l'appareillage
          metallic 0,30, roughness 0,52 (entre la tôle peinte d'AA_Hull et la
          carapace polie d'AA_Trim)
          candidats : dessus du rebord du canal, chapeaux de nervure, massifs
          de machinerie autour des socles, coffrets  ≈ 2 400 m² d'aire vue,
          soit ~12 % — la cible tomberait juste
          demande de texture à écrire : TEX-00xx, dérivée de TEX-0012 (machinerie)
```

### 8.2 Le rythme demande de déplacer des marqueurs, et je ne les ai pas déplacés

Le brief pose « **15–20 m calmes** → une installation → zone calme → un hangar → calme → un
groupe de tourelles ». La séquence existe, mais **elle est bornée par la carte des marqueurs**,
que le brief fige (« noms, X, Z inchangés ») :

- 22 plages nues, dont 9 de 12 m ou plus, et **la plus large hors proue fait 22 m** ;
- une greffe de 8 m posée dans une plage de 22 m ne laisserait que 7 m de tôle de chaque côté,
  quand le brief en demande 15 à 20. **Aucune plage n'est assez large** pour héberger une
  installation *et* garder sa respiration ;
- j'ai donc choisi de **n'en poser aucune dans les plages** : les greffes sont hébergées par les
  emprises de marqueur. La conséquence est que « une installation » de la séquence est toujours
  *aussi* une tourelle, un hangar ou un nœud.

Pour obtenir la séquence complète, il faut **écarter quelques marqueurs** de façon à ouvrir 3 ou
4 plages de 30 m et plus. C'est une décision de gameplay (densité de menace, rythme de tir), pas
de forge, et elle rejouerait `_marker_clashes()`.

### 8.3 Le nœud siège exactement là où vole le joueur

Sur le premier tirage de la planche, le Specter-9 **masquait entièrement** `Spine_04` : le nœud
est sur l'axe du vaisseau, et c'est là que le chasseur vole quand il ne manœuvre pas. J'ai décalé
le chasseur de 3,60 m à tribord **pour la planche seulement**, et je le signale plutôt que de le
cacher : c'est une information de conception. Trois lectures possibles, aucune n'est de la forge :

1. c'est **voulu** — « plus dur à atteindre qu'il n'est dur à tuer » (`cortege_spine_node.gd`), et
   le joueur doit se décaler pour voir sa cible ;
2. c'est **à corriger côté caméra** — le nœud pourrait s'annoncer par les arcs, qui débordent de
   la silhouette du chasseur ;
3. c'est **à corriger côté marqueur** — décaler les `Spine_NN` de ±2 m, ce que le canal permet
   (2,00 m de large pour un berceau de 1,32) mais que le brief interdit (« X et Z inchangés »).

### 8.4 La cible « 5 % de violet et magenta » est atteinte par le bas

Mesuré : **1,45 %** de l'aire vue pour 5 % visés — 3,6 points sous la cible, dans la tolérance
de ±5 du plan mais du **côté sombre**. Monter à 5 % demanderait de tripler l'aire émissive, ce
qui entre en conflit direct avec les deux autres règles du même brief (« l'émissif ne doit jamais
dominer l'écran », « le halo est le travail du moteur »). Le réglage qui manque n'est pas
géométrique : c'est l'**énergie d'émission** du matériau côté Godot, qui n'est pas dans mon
périmètre. Je livre la géométrie qui permet les deux, et je laisse le dosage au concepteur.

### 8.5 Les zones calmes n'ont pas été « remplies » par la texture — c'est un pari

50 % du bordé est désormais de la tôle nue en géométrie. Le pari est que `TEX-0010` porte le
détail à sa place. Il est **vérifiable et il n'a pas été vérifié ici** : les planches de la forge
rendent des couleurs unies (ADR-0028 interdit d'embarquer la texture), donc la seule preuve
possible est une capture **en jeu, texture appliquée**. Si le bordé y paraît vide, le remède
n'est pas de remettre des plaques : c'est de rehausser l'échelle de `TEX-0010` (`HULL_UV_SCALE`,
déjà à 0,5 dans `cortege_skin.gd`, et le calcul d'entier y est écrit).

---

## 9. La planche regardée (`ADR-0006`)

`docs/forge/output/BRIEF-0094-planche-epine.png` — 1440 × 3260, Cycles CPU, six vignettes :

1. **TEST D'ACCEPTATION** — hangar `Bay_06`, tourelle `Turret_11` et nœud `Spine_04` dans le
   **même cadre**, **noir et blanc, émissifs coupés**, à la caméra de `graybox.tscn` sans
   retouche (0, 14, 5) FOV 62. Les trois se distinguent : un trou, un canon, une couronne dans
   la tranchée ;
2. le **même cadre en couleur** — ce que l'émissif ajoute à une fonction déjà lisible ;
3. le nœud et sa **carcasse** de trois quarts dans la tranchée ;
4. l'**artère de près** ;
5. le **rythme** sur 128 m (s = 245 à 373), vue longue orthographique ;
6. le **damier UV**, à la perspective du jeu, coque et kits ensemble.

⚠️ **Le cadre d'acceptation est choisi par la mesure.** La caméra du jeu ne voit qu'une fenêtre
de **16 m en `s`** à la profondeur du pont. `Bay_06` (348), `Spine_04` (350) et `Turret_11` (360)
y tiennent en visant s = 353. Premier essai à s = 348 : `Turret_10` (336) tombait **derrière la
caméra**, et le test ne montrait que deux structures sur trois.

Quatre défauts ont été trouvés **en regardant**, pas en calculant, et corrigés :

| Vu | Corrigé |
|---|---|
| deux traits blancs pleins du haut au bas du cadre | la lisse de chine et les chapeaux de nervure perdent `AA_Trim` |
| un parallélogramme violet plein sur chaque greffe | violet sur la seule terrasse haute, d'une greffe sur deux |
| le nœud entièrement sombre vu du jeu | la couronne émissive horizontale de 16 cm |
| le chasseur masquait le nœud | décalé de 3,60 m pour la planche, et signalé (§8.3) |

`docs/forge/output/BRIEF-0089-planche-sections.png` a été régénérée : elle montre la coque à
canal, la palette réduite et les zones calmes, avec ses neuf vignettes habituelles.

---

## 10. Limites connues

- **L'aire « vue » est une approximation.** Elle retient les faces qui regardent la caméra et qui
  sont au-dessus de la peau, mais elle **ignore les occultations entre pièces** : le dessus d'une
  couche basse de greffe, en partie couvert par la couche du dessus, y entre entièrement. Le biais
  va dans le sens défavorable au violet (il le surestime), donc il ne cache pas de dérive.
- **Le rendu d'acceptation est en Cycles, pas en Godot.** L'émission y est calibrée sur la clé du
  jeu (`énergie × π`) mais le *bloom* du moteur n'y est pas. La lecture finale de l'artère —
  « le chasseur et les balles se lisent-ils encore par-dessus ? » — demande une capture en jeu.
- **Le tronçon 5 n'a qu'une plage calme de 9,6 m** : Ambry y occupe 32 m à elle seule, et cinq
  tourelles s'y ajoutent. C'est le tronçon le plus chargé du vaisseau, par construction
  (`BRIEF-0089` fait croître la densité de la proue à la poupe) — mais c'est aussi le dernier que
  le joueur traverse, donc le plus fatigant.
- **`AA_Trim` est à 0,07 % de l'aire totale.** Il reste *assigné* (le harnais l'exige), mais il
  ne porte plus grand-chose. Si le neuvième slot est créé (§8.1), il faudra décider si `AA_Trim`
  garde un rôle ou s'il devient le liseré de quelques pièces seulement.
- **Le fût du nœud mesure 1,90 : 1** (0,68 de large pour 1,29 de haut) et non 2,15 : 1 comme dans
  les premières mesures — la couronne l'a élargi de 6 cm. Il reste la seule pièce du niveau plus
  haute que large, et le harnais le vérifie ; c'est simplement moins marqué qu'annoncé.

## 11. Suggestions

- **Câbler `spine_kit.glb` avant de juger le lot en jeu.** `CortegeSpineNode` construit
  aujourd'hui sa propre sphère (`BULB_RADIUS`, `BULB_LIFT`) et ne connaît pas le kit ; tant qu'il
  n'est pas monté, le nœud sera une boule violette **posée sur** le marqueur, désormais au fond
  du canal. Les arcs (`ARC_REACH = 1,35`) ont été dimensionnés contre un bulbe à +0,45 ; contre
  la lanterne, ils devraient partir de +1,10 environ.
- **Une capture en jeu avec `TEX-0010` appliquée** répondra à la seule question que la forge ne
  peut pas trancher (§8.5) : les 250 m de tôle nue sont-ils « une grande plage » ou « un vide » ?
- **`build_bay_kit._tile_close()` porte encore la formule de « haut » cassée** signalée au
  `BRIEF-0093` (`(avant × X) × avant`, qui roule la caméra). Hors périmètre ici, toujours vrai.

---

# Arbitrage du concepteur — les cinq points de la §8

*Ajouté après intégration et vérification en jeu (captures au tronçon 2, 2026-08-29). La forge a
eu raison de ne trancher aucun des cinq : ce sont des décisions de conception.*

| # | Décision | Raison |
|---|---|---|
| 8.1 | **Pas de neuvième slot** `AA_Gear` | Il appellerait une carte neuve, donc un `TEX-NNNN`, donc une reforge de plus. La proposition est bonne et reste ouverte : elle se prendra le jour où un asset la demandera pour lui-même, pas pour rattraper un pourcentage. |
| 8.2 | **Les marqueurs ne bougent pas** | Ils portent de l'équilibrage **mesuré** — fenêtre de relâche des ponts, fenêtre d'engagement des tourelles, arbitrages du `BRIEF-0092`. Les écarter pour gagner du rythme referait toutes ces mesures pour un gain qui n'est pas prouvé. 50,3 % de longueur calme est le plafond sous marqueurs figés, et la capture montre que ça suffit : le regard tient sur les installations. |
| 8.3 | **Le nœud reste sur l'axe** — c'est voulu | C'est écrit depuis le premier jour dans `cortege_spine_node.gd` : il est *plus dur à atteindre qu'il n'est dur à tuer*, parce qu'il siège là où convergent les tourelles des deux bords. Le déplacer supprimerait la seule difficulté de placement du niveau. |
| 8.4 | **La cible des 5 % de violet est RETIRÉE** | Elle mesurait la mauvaise chose. Vérification faite en capture : le réglage moteur qu'il fallait bouger était l'énergie d'émission, et il fallait la **baisser** — 1,0 → 0,45. Une aire mesurée sur le binaire ne dit rien de ce que l'écran montre, parce que le `lift` de 1,25 du post-traitement relève les noirs. Ce qui compte est la hiérarchie à l'écran, et elle se juge en regardant. |
| 8.5 | **Le pari des 250 m de tôle nue est GAGNÉ** | Vérifié : la coque nue lit comme du bordé plaqué, joints visibles, sans bruit. `TEX-0010` tient à cette échelle. |

Et un défaut trouvé à l'intégration, que la planche ne pouvait pas montrer : la **dalle d'une
greffe était plus claire que la tourelle qu'elle porte** — une inversion de hiérarchie, corrigée
côté moteur (`CortegeSkin.PANEL_DAMP`) et non à la palette, parce que le violet de `AA_Panel`
est la teinte de faction de l'Unisson et qu'elle va bien partout ailleurs.
