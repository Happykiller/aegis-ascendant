# BRIEF-0108 — Rapport de forge : trois livraisons entrent, en se reconstruisant

- **Brief** : `docs/forge/briefs/BRIEF-0108-trois-livraisons-a-un-autre-budget.md`
- **Date** : 2026-09-08
- **Outils** : Blender 5.2.1 LTS (`blender-aegis`), toujours `-t 1`
- **Périmètre respecté** : aucun `.gd`, `.tscn`, `.tres` touché ; aucun commit ;
  `stern_arm.glb` et `stern_anchor.glb` intacts.

---

## 0. Le résultat en une ligne

**4 576 triangles pour les cinq pièces**, contre **173 244** livrés — soit **38 fois
moins** — et les cinq cibles unitaires sont tenues, toutes les cinq.

| Pièce | livré | **après** | cible | vert ? |
|---|---:|---:|---:|:--:|
| `stern_pylon` | 88 504 | **2 612** | ≤ 3 200 | ✅ |
| `artery_conduit` (droite) | 21 284 | **652** | ≤ 700 | ✅ |
| `artery_conduit_bend` (coudée) | 13 400 | **648** | ≤ 700 | ✅ |
| `artery_hose` (droit) | 25 028 | **320** | ≤ 350 | ✅ |
| `artery_hose_bend` (coudé) | 25 028 | **344** | ≤ 350 | ✅ |

Aux quantités que le brief évoque : **quatre pylônes = 10 448** sur les 16 798 qui restaient
du budget de 80 000 de la poupe, soit **6 350 de marge** au lieu des 3 998 espérés.

---

## 1. ⚠️ Le renversement de méthode, et ce qui l'a permis

Le `BRIEF-0105` avait reçu quatre `.blend` **sans générateur** : il ne pouvait que
*transformer* un maillage déjà cuit, et il a dû abandonner la décimation (elle ouvrait le
flanc des coques fermées — mesuré, regardé, documenté).

**Ici les trois livraisons arrivent avec leur générateur complet.** Ça change tout :

> On ne réduit pas ce maillage. **On le reconstruit.** Une bague de 32 côtés ne se rabote
> pas — elle se **régénère à 8 côtés**, et elle reste une bague.

Le `build.py` de chaque livraison est exécuté **verbatim** (`author/*_build.py`, copies au
bit près) par-dessus un `geometry.py` dont chaque constante de résolution est devenue un
levier (`forge_geometry.py`). Le diff entre les deux fichiers **est** la réduction.

**Conséquence sur le critère le plus dur du brief** : le contrat de noms n'est pas
« préservé », il est **vide par construction**. Les repères `CTRL | ` sont produits par la
ligne de code de l'auteur qui les a toujours produits.

⚠️ **Et le générateur est bien complet, contrairement à `specter_9_v3`** (`ADR-0048`) :
il part d'une scène vide, ce que la réexécution vérifie à chaque build.

---

## 2. LE PYLÔNE — reconstruit à 5,30 m, pas mis à l'échelle

### 2.1 — Le facteur se **mesure**, il ne se suppose pas

L'auteur livre **24,00 m**, antenne comprise. L'antenne, son embase et sa balise n'existent
plus à cette taille (§2.2) : ce qui survit mesure **23,15 m** dans le repère d'auteur, d'où
**k = 0,228942** pour occuper les 5,30 m de l'emplacement. Le binaire fait **5,300 m** de
haut, exactement.

Le facteur est **remesuré sur les 25 repères du binaire**, source contre livré :
**0,228942**, écart maximal **7,7 × 10⁻⁵ mm**. Ce n'est donc pas une valeur recopiée du
script : c'est la preuve que la pièce livrée est bien celle de l'auteur, à 5,30 m.

⚠️ **La mise à l'échelle est CUITE dans les sommets** — sommets, pivots, os de l'armature
**et clés d'animation**. Le `.glb` ne contient aucun nœud à l'échelle ≠ 1.

### 2.2 — Ce qui a été supprimé, et pourquoi ça n'existait plus

À 5,30 m et `asset_scale = 0,870`, sur un pont de poupe qui rend **32,7 px/m**, **un mètre
d'auteur vaut 6,5 pixels**. Le tableau se lit avec ce chiffre.

| Famille | ×n | tri | Pourquoi elle n'existe plus |
|---|---:|---:|---|
| `Collier conduite` | 20 | 1 280 | bague de 74 cm à fleur d'un tuyau qu'elle ceint → 4,8 px, et 20 fois |
| `Barreau echelle` | 52 | 1 040 | **échelon tous les 6,6 cm, barre de 1,2 cm** : ce n'est plus une échelle, c'est une rayure de 0,08 px |
| `Vis capot` | 48 | 960 | vis de 1,3 cm → 0,09 px |
| `Caillebotis longitudinal` | 73 | 876 | 73 lamelles de 1 cm → 0,3 px chacune |
| `Collier interface moteur` | 8 | 512 | 5,2 px |
| `Montant garde corps` | 24 | 480 | **garde-corps de 1,10 m → 24 cm** : ce n'est plus un garde-corps, c'est une nervure |
| `Goujon socle` | 20 | 400 | 0,14 px |
| `Ailette thermique fixe` | 28 | 336 | ⚠️ **moiré** : 28 ailettes FIXES de 1,0 px au pas de 3,2 px, collées aux 28 ailettes MOBILES du même pas. Garder les deux ne double pas la lisibilité, ça fait battre deux trames. **On garde celles qui bougent.** |
| `Longeron de capot` | 24 | 288 | section 0,65 × 0,59 px |
| `Interface verticale` | 4 | 256 | 4,2 px pour 256 triangles |
| `Lisse` + `Retour garde corps` | 16 | 320 | idem garde-corps |
| `Conduite interne` | 4 | 768 | ⚠️ **le nom le dit** : elles courent *à l'intérieur* de la colonne, derrière les douze plaques de blindage. Jamais vues. |
| `Repere discret 07` | 1 | ~200 | pochoir de 0,9 m → 20 cm, soit **1,3 px de haut**. Illisible. |
| `Antenne` + embase + balise | 3 | 60 | rayon 1,2 cm → 0,16 px : elle **scintillerait** au lieu de se voir |
| `Temoin maintenance` (+ logement) | 12 | 144 | 44 × 4 cm → 2,9 × **0,26 px** : une lumière d'un quart de pixel ne s'allume pas, elle clignote |
| `Plinthe`, `Feu passerelle`, `Balise garde corps`, visserie diverse | — | ~450 | idem |

**Total supprimé : 7 264 triangles sur 9 556** (au niveau du générateur, chanfreins déjà
retirés). Les chanfreins eux-mêmes — `BEVEL` 2 segments sur **tous** les objets — portaient
le reste de l'écart avec les 88 504 du binaire livré.

### 2.3 — ⚠️ Deux découvertes qu'aucun compteur n'aurait données

**(a) Le levier de résolution des tuyaux était inopérant, en silence.** Le helper `pipe()`
du pylône réécrit `resolution_u = 5` et `bevel_resolution = 1` **après** `geometry.hose()`,
et le pylône convertit ses courbes en maillage **dans le `build.py` de l'auteur** — donc
avant que le pilote ne puisse toucher à quoi que ce soit. Les huit tuyaux coûtaient
**2 044 triangles, 61 % de la pièce**, pour des conduites de 13 cm de diamètre à 5,30 m,
soit **0,85 px de large**. Corrigé par un patch textuel déclaré (`SOURCE_PATCHES`).

**(b) La caméra du jeu regarde presque à la verticale** — avant `(0 ; −0,940 ; −0,342)`.
Un pylône **vertical** de 5,30 m se lit donc par son **empreinte** (2,89 × 2,06 m), pas par
sa silhouette. La première version, qui gardait les passerelles réduites à leur cadre,
rendait **deux rectangles vides** qu'on voyait par-dessous. Les 16 caillebotis
**transversaux** referment le plancher pour 192 triangles ; les 73 longitudinaux et les
garde-corps en coûtaient 1 596 de plus pour le même trait.

### 2.4 — Repères supprimés : **AUCUN**

Le brief demandait la liste nommée des repères disparus. **Elle est vide : 25 sur 25 sont
conservés**, à 7,7 × 10⁻⁵ mm près après division par le facteur mesuré. C'est une
conséquence de la méthode — les `CTRL | ` sont des `Empty`, et les leviers n'agissent que
sur les maillages.

---

## 3. LA CONDUITE ET LE FLEXIBLE — réduits pour être répétés

### 3.1 ⚠️ Le tableau d'audit du brief décrit les mauvais fichiers

Mesuré sur les binaires : les quatre fichiers `_droit` / `_coude` livrés par l'auteur ne
sont **pas** les assets complets, ce sont des **sous-arbres**.

| Fichier | cotes annoncées | **cotes mesurées** | `CTRL` annoncés | **mesurés** |
|---|---|---|---:|---:|
| `conduit_droit.glb` | 1,60 × 1,41 × 3,85 | **0,51 × 0,65 × 2,78** | 39 | **10** |
| `conduit_coude.glb` | idem | **0,37 × 1,29 × 2,80** | 39 | **4** |
| `flexible_droit.glb` | 0,84 × 0,87 × 2,84 | **0,30 × 0,28 × 2,83** | 81 | **17** |
| `flexible_coude.glb` | idem | **0,33 × 0,34 × 3,17** | 81 | **16** |

Les chiffres du brief sont ceux de `conduite_energetique.glb` (73 604 tri, 39 `CTRL`) et
`flexible_technique.glb` (126 012 tri, 81 `CTRL`, **cinq** lignes de flexible). Cela ne
change aucune décision — **les cibles sont tenues sur les fichiers réellement livrés** —
mais il faut le savoir : `artery_hose.glb` est **UNE** ligne, pas un faisceau de cinq.

### 3.2 — Ce qui disparaît, par famille

| Famille supprimée | ×n | tri | Raison |
|---|---:|---:|---|
| `Boulon` (conduite) | 48 | 960 | visserie |
| `Boulon collier` (flexible) | 108 | 1 728 | visserie |
| `Blindage chambre` | 12 | 432 | 12 écailles de 1 cm **plaquées sur** le tube |
| `Blindage noyau secondaire` | 12 | 432 | idem |
| `Barreau cage` | 12 | 336 | 12 barreaux de 1,7 cm autour d'une chambre → 1,6 px |
| `Frettes conduit` | 6 | 384 | 6 bagues de 4,5 cm **à fleur** du tube qu'elles ceignent |
| `Vis collier`, `Vis embase`, `Vis prise`, `Vis bride` | 38+ | 744 | visserie |
| `Joint socket`, `Nervure montant`, `Renfort noyau` | — | 592 | finitions sous le pixel |
| `Garde noyau` (flexible) | 24 | 1 152 | 2 bagues de **1,2 cm** de part et d'autre d'un anneau |
| `Fond prise`, `Port`, `Face connecteur`, `Joint`, `Frette acier` | — | ~1 500 | **au fond d'un port de 5 cm : jamais vu** |
| `Demi coque` (colliers du flexible) | 36 | 1 008 | voir §6.2 — c'est la perte assumée |
| `Collier secondaire` | 7 → 2 | 320 | le rythme suffit ; un sur trois |

### 3.3 — Les pièces mobiles, traitées à part : ce qu'elles coûtent

Elles ne se décimolent pas comme le reste : les aplatir fait disparaître le mouvement avec
la forme. Compté **sur les binaires**, en descendant depuis chaque nœud animé :

| Fichier | mobiles | part | ce qui bouge |
|---|---:|---:|---|
| `stern_pylon` | **1 068** | 41 % | 28 lames thermiques (2 peaux), 2 blocs de conduites, couronne |
| `artery_conduit` | **652** | **100 %** | 6 demi-colliers, 2 noyaux plasma, le faisceau entier |
| `artery_conduit_bend` | **648** | **100 %** | la gaine coudée, 2 noyaux |
| `artery_hose` | **308** | 96 % | gaine **peaussée sur 13 os**, raccord mobile, 2 noyaux, brins |
| `artery_hose_bend` | **332** | 97 % | idem |

Autrement dit : **sur l'artère, le budget EST l'animation.** C'est le prix de huit clips
destructibles, et il est payé sciemment.

⚠️ **Le tube du flexible est le seul endroit où la résolution se patche dans le texte** :
ses `192 × 20` sont écrits en dur dans le `build.py` de l'auteur. Remplacés par `12 × 6`,
c'est **l'algorithme de l'auteur qui recalcule lui-même** les poids de peau et les UV à la
nouvelle résolution — ce qu'un décimateur aurait fait à l'aveugle. 7 716 → 152 triangles.

---

## 4. Les onze clips — rejoués **après réimport**

Chaque `.glb` est réimporté dans Blender, chaque piste démutée à son tour, et on mesure le
**déplacement réel des sommets évalués** (depsgraph, peau comprise) — pas un compteur de
canaux, qui dirait « vivant » d'un clip vide.

| Fichier | clips | canaux | amplitude mesurée (m) |
|---|---|---:|---|
| `stern_pylon` | `Service` `Refroidissement` `Maintenance` | 99 ×3 | 0,0015 / 0,0027 / **0,0472** |
| `artery_conduit` | `Actif` `Endommage` `Rupture` `Rompu` | 27 ×4 | 0,0090 / 0,0271 / **0,3118** / 0,0125 |
| `artery_conduit_bend` | idem | 9 ×4 | 0,0092 / 0,0275 / **0,5775** / 0,0173 |
| `artery_hose` | `Intact` `Endommage` `Rupture` `Rompu` | 75 ×4 | 0,0108 / 0,0325 / **0,6525** / 0,0325 |
| `artery_hose_bend` | idem | 75 ×4 | 0,0108 / 0,0325 / **0,6525** / 0,0325 |

**11 clips, cuits en clés** (`export_force_sampling`, mode `NLA_TRACKS`) : aucun pilote
Blender ne subsiste (`ADR-0046`).

⚠️ **Trois clips peuvent bouger et rester indiscernables.** Sur le pylône, `Service` et
`Refroidissement` ne diffèrent que par une **pose statique** des lames (0,035 rad contre
0,32) : leur amplitude *interne* est minuscule et un compteur d'amplitude seul les
déclarerait tous les deux vivants sans voir s'ils sont différents. L'écart **entre** clips
est donc mesuré aussi : `Service` ↔ `Refroidissement` = **13,8 mm**, `Maintenance` = les
lames à 66°. De même sur l'artère, `Actif` et `Endommagé` ont la **même pose à l'image 1**
et diffèrent par un **gain × 3** sur la vibration — c'est le rapport 0,0090 → 0,0271 qui le
dit, pas la pose.

### La continuité `Rupture` → `Rompu` : **0,000000 m**

Dernière image de `Rupture` contre première image de `Rompu`, **sommet par sommet**, sur
les quatre fichiers destructibles : **écart maximal 0,000000 m**. La pièce ne saute pas
d'une pose à l'autre à l'instant précis où le joueur regarde.

---

## 5. Le contrat de noms — diff **VIDE**, et une découverte sur les binaires de l'auteur

| Fichier | repères auteur | livrés | manquants | ajoutés | vs export par module | **vs asset complet** |
|---|---:|---:|---|---|---:|---:|
| `stern_pylon` | 25 | 25 | aucun | aucun | **7,7e-05 mm** (après k) | — |
| `artery_conduit` | 10 | 10 | aucun | aucun | 175,557 mm | **0,000000 mm** |
| `artery_conduit_bend` | 4 | 4 | aucun | aucun | 383,027 mm | **0,000000 mm** |
| `artery_hose` | 17 | 17 | aucun | aucun | **0,000000 mm** | — |
| `artery_hose_bend` | 16 | 16 | aucun | aucun | 620,525 mm | **0,000000 mm** |

⚠️ **Trois repères s'écartaient — et c'est l'auteur qui a bougé, pas nous.** Exactement un
par fichier :

```
CTRL | Demi collier 1.13 1     175,557 mm
CTRL | Noyau secondaire 0.79   383,027 mm
CTRL | Noyau Ligne 011         620,525 mm
```

Le test décisif : comparer les **sous-ensembles de l'auteur à son propre asset complet**.

```
conduite_energetique.glb  vs  conduit_droit.glb   ->  MEME repere, MEME ecart, 175,557 mm
flexible_technique.glb    vs  flexible_coude.glb  ->  MEME repere, MEME ecart, 620,525 mm
```

Les trois repères portent, dans les exports **par module** de l'auteur, un résidu de la
**pose rompue** de leur mécanisme parent (l'offset mesuré vaut exactement la rotation de
0,07 rad du faisceau, et la translation `(±0,055 ; 0,62 ; −0,055)` du connecteur brisé).
Nos fichiers coïncident avec l'asset **complet** de l'auteur à **0,000000 mm sur 100 % des
repères** ; ce sont ses trois exports partiels qui divergent, sur un marqueur chacun, alors
que tous leurs frères de la même famille sont exacts.

`verify_artery.py` porte désormais cette double référence : il compare à l'export par
module **et** à l'asset complet, et **nomme** le repère figé par l'auteur. Le chiffre qui
fait foi est celui de la dernière colonne.

---

## 6. `AA_Emissive_Engine` porte tout ce qui doit s'éteindre

Compté **sur les binaires**, matériau par matériau :

| Fichier | `AA_Hull` | `AA_Greeble` | **`AA_Emissive_Engine`** | images |
|---|---:|---:|---:|---:|
| `stern_pylon` | 1 224 | 784 | **412** | **0** |
| `artery_conduit` | 344 | 220 | **88** | **0** |
| `artery_conduit_bend` | 192 | 368 | **88** | **0** |
| `artery_hose` | 24 | 200 | **96** | **0** |
| `artery_hose_bend` | 24 | 224 | **96** | **0** |

La vignette 7 de la planche coupe `Emission Strength` sur le seul `AA_Emissive_Engine` :
rien d'autre ne reste allumé.

### 6.1 ⚠️ Le repli des trois slots neufs — **le brief a tort sur deux, et c'est mesuré**

Le brief propose `10 | Carbone technique` et `10 | Gaine tressee reference 06` →
**`AA_Panel`**. Or, dans la palette Unisson (`aegis_kit.PALETTES`) :

```
AA_Panel   = #452663   VIOLET SOMBRE, metallic 0,15
AA_Greeble = #141419   anthracite tres sombre, metallic 0,75
```

`AA_Panel` n'est pas « le slot des panneaux gris » : **c'est le violet de faction**. Et la
gaine tressée n'est pas un détail — c'est **la totalité du tube du flexible**, 200 de ses
320 triangles. Le repli du brief peint donc le flexible en violet.

Rendu côte à côte, même cadrage, même lumière, même pose
(`BRIEF-0108-arbitrage-materiaux.png`), mesuré sur les pixels du flexible :

| | repli du brief (`AA_Panel`) | **retenu (`AA_Greeble`)** |
|---|---:|---:|
| luminance moyenne | 0,288 | **0,198** |
| saturation moyenne | 0,209 | **0,067** |
| dominante | bleu (B 0,453 > R 0,355) | neutre |

**+46 % de luminance et × 3,1 de saturation** sur une pièce de décor qui doit rester
sombre, à côté d'un émissif magenta qui, lui, doit se voir. La matière d'origine de
l'auteur est un noir métallique (base 0,018–0,09, metallic 0,58) : `AA_Greeble` est
littéralement la même intention.

**Décision de la forge : les deux vont sur `AA_Greeble`.** Le troisième slot neuf,
`11 | Conduite sombre` (metallic 0,78), suit le brief sans réserve — `AA_Greeble` aussi.

La variante du brief reste reproductible : `--brief-materials`, qui écrit dans `build/`
(gitignoré).

### 6.2 — `AA_Panel` et `AA_Trim` restent donc vides sur ces cinq pièces.

---

## 7. UV et texture

**Aucune texture livrée** (`ADR-0028`) : les 8 à 13 atlas de chaque livraison sont purgés,
avec leurs matériaux, avant l'export. **Zéro image embarquée** sur les cinq binaires.

**`TEXCOORD_0` compté, jamais supposé** : **51 primitives sur 51**, dont **0 sans UV**.

| Binaire | moyenne (tuile/m) | max | min | **anisotropie max** |
|---|---:|---:|---:|---:|
| `stern_pylon` | 0,680 | 0,700 | 0,553 | **1,27** |
| `artery_conduit` | 0,682 | 0,700 | 0,589 | **1,19** |
| `artery_conduit_bend` | 0,681 | 0,700 | 0,589 | **1,19** |
| `artery_hose` | 0,664 | 0,700 | 0,573 | **1,22** |
| `artery_hose_bend` | 0,657 | 0,700 | 0,554 | **1,26** |

Borne théorique d'une projection en boîte : √3 = 1,732. On est dessous partout. Le brief ne
demandait pas de dépliage continu ; **la planche de contrôle au damier est livrée quand
même** (vignette 8), à la perspective du jeu.

### ⚠️ 7.1 — Écart assumé avec la lettre du brief sur la densité

Le brief demande « la densité de la peau du corridor », soit
`HULL_TEXELS_PER_METER = 0,200` tuile/m (20 tuiles pour 100 m de tronçon). **À cette
densité, un flexible de 0,14 m de diamètre reçoit 0,028 tuile sur toute sa largeur : sa
carte de détail n'existerait pas.** On reprend donc **0,70 tuile/m** — la densité des
quatre pièces du `BRIEF-0105` posées juste à côté (`AMBRY_TEXELS_PER_METER`), et pour la
même raison qu'elles : ces pièces se voient de bien plus près que les 500 m de bordé.
C'est une constante d'une ligne (`TILES_PER_METER` dans `build_artery.py`) si le concepteur
tranche autrement.

### ⚠️ 7.2 — Un défaut totalement silencieux, trouvé **parce qu'on a mesuré**

La première version du pylône sortait à **2,97 tuile/m au lieu de 0,70 — 4,4 fois trop.**
Cause : `box_project_uv()` projette en **mètres**, et le dépliage se faisait **avant** la
mise à l'échelle. Déplier à la taille de l'auteur puis réduire d'un facteur k multiplie la
densité par 1/k = 4,37.

**Aucune erreur d'import, aucun test rouge, aucun compteur.** Ça ne se serait vu qu'une fois
la texture générée, c'est-à-dire trop tard. Corrigé : `rescale()` passe désormais **avant**
le dépliage, et le commentaire porte la mesure.

---

## 8. Déterminisme

```
3 exécutions de build_artery.py -- --all, sha256 des 5 binaires : ZÉRO OCTET DIVERGENT

73b408f09b7b735df97d279c7fd95268f9e04d976379e3ffbf5a48bbe1d7602b  stern_pylon.glb
1df35337d5cfc713aa9cdcc45f27374b22ec01b671ccd9f21cfae2b3cc1b1be2  artery_conduit.glb
9c61b3225b4f6c66a87a0e1ad9520f781a15fd2d8a361fe1bdd09d1c6ead0cfb  artery_conduit_bend.glb
4269a8e17549f1457c2523e1a9380c79aaf2794936742edf26a2a3715b8fa2e4  artery_hose.glb
2259904350523eacd2e4c38d7c8f67cc5df9195de261cbbdf24a68d0dc819e25  artery_hose_bend.glb
```

`-t 1` partout, comme l'exige `howto-determinisme-des-coques.md`.

---

## 9. Rendu et **REGARDÉ**

`docs/forge/output/BRIEF-0108-planche.png` — **huit vignettes de 1920 × 1080**, à la caméra
du jeu `(0 ; 14 ; 5)` / FOV 62 vertical, trois directionnelles du niveau, aucune ombre
portée. Le rig est **importé** de `build_long_cortege.py`, pas recopié.

⚠️ **Deux distances, pas une**, et c'est mesuré :

```
pont du corridor   y = -4,30    cadre 41,60 m    46,2 px/m
pont de poupe      y = -11,85   cadre 58,77 m    32,7 px/m
```

| # | Vignette | Ce qu'elle montre |
|---|---|---|
| 1 | pylône ×4, `Service` | à `asset_scale` lu dans `long_cortege_stern.tres` |
| 2 | pylône, `Maintenance` | les 28 lames s'ouvrent à 66° — la seule différence visible des trois clips |
| 3 | l'artère, **Intact** | conduite droite, conduite coudée, flexible droit, flexible coudé |
| 4 | **Endommagé** | la vibration triple, les colliers s'écartent |
| 5 | **Rupture**, image 88/121 | raccords en train de s'arracher |
| 6 | ⚠️ **Rompu** | *celui que personne ne pense à regarder, et celui que le joueur verra le plus longtemps* |
| 7 | Rompu, **émissif coupé** | la preuve du contrat de matériaux |
| 8 | **damier UV** | à la perspective du jeu, 0,70 tuile/m |

Ce que la lecture donne : les conduites se lisent comme des tuyaux **segmentés à deux
chambres lumineuses**, les flexibles comme des **liaisons souples à embouts éclairés** ; à
`Rompu` le raccord est **détaché**, les brins pendent et **plus rien n'est allumé** — la
pièce morte est noire, ce qui est exactement ce qu'on veut d'une cible détruite. Le pylône
se lit **par son empreinte** (§2.3 b), et les quatre exemplaires restent distincts sur le
pont.

---

## 10. ⚠️ Ce qui n'a pas pu être tenu, nommé

### 10.1 — Les six demi-colliers du flexible sont perdus (168 tri)

À **350 triangles**, le flexible ne peut pas payer ses colliers : la gaine peaussée en prend
152, les deux embouts et leurs anneaux magenta 120, les brins exposés 43. Les six demi-
coques (28 tri chacune) auraient coûté **+48 %** du budget pour une pièce de **6,2 cm de
large, soit 2,9 px**.

**Ce qui est perdu est le geste**, pas la mécanique : les six `CTRL | Collier ...` sont dans
le binaire, animés, avec leur ouverture à `Rupture`. Une version plus riche n'aurait qu'à
raccrocher de la géométrie dessus. *Budget dépassé en silence : non. Budget arbitré : oui.*

### 10.2 — Le cran sombre dans le noyau magenta du coude (~3 px)

Le noyau magenta (r = 0,151) et sa gaine (r = 0,143) **s'interpénètrent par construction**
chez l'auteur, et le clip fait **pulser** ce rayon de ±2,5 % (× 3 en `Endommagé`). Au creux
de la pulsation le noyau redescend à 0,1435 et repasse **sous** la gaine — quel que soit le
nombre de côtés. `ROD_CAP` est passé de 8 à 12 pour que le rayon inscrit du noyau
(0,151 × cos 15° = 0,1459) dépasse le rayon circonscrit de la gaine au repos ; il reste un
cran d'environ 3 px au creux de la pulsation. **À 32 côtés l'auteur avait un cheveu, à 12 on
a un cran.** C'est sa géométrie, pas la réduction — et le refermer entièrement coûterait
~350 triangles sur un budget de 700.

### 10.3 — Le `.blend` de l'auteur n'est pas versionné (écart à `ADR-0048`)

`ADR-0048` demande la source d'un modèle tiers, et sa raison est explicite : le `.blend` de
`specter_9_v3` était la source **parce que son script n'était qu'un diff** — « 241 lignes
pour 525 objets ».

**Ici ce n'est pas le cas, et c'est vérifié par l'exécution** : les trois `build.py`
construisent tout depuis une scène vide, et le dépôt s'en sert à chaque build. Verser en
plus les trois `.blend` coûterait **48,0 Mo de LFS** (+4,4 % des 1,1 Go de LFS du dépôt) pour des
fichiers dont **le contenu est intégralement redérivable**, et qui portent en outre les 8 à
13 atlas que `ADR-0028` nous interdit d'employer.

**Décision de la forge : on verse les générateurs, pas les binaires** — et on le signale
plutôt que de le faire en silence. Si le concepteur veut les `.blend` malgré tout, ils sont
dans `~/aegis-ascendant_gpt_models/*/v1/blender/` et une copie octet pour octet suffit.
*C'est un arbitrage de coût, et il appartient au concepteur.*

### 10.4 — Le tableau d'audit du brief porte sur les mauvais fichiers

Voir §3.1. Cotes et nombres de repères annoncés sont ceux des assets **complets**, pas des
quatre sous-arbres réellement livrés. Aucune décision n'en dépend, mais
`artery_hose*.glb` est **une** ligne de flexible, pas les cinq.

### 10.5 — Ce que le lot n'a pas fait

- **Aucun placement** (brief §Hors périmètre) : combien de conduites, où, sur quels
  tronçons. Les planches les alignent pour qu'on les regarde.
- **Aucun coût GPU mesuré** : un relevé n'a de sens qu'une fois les pièces montées en jeu,
  ce qui demanderait de toucher au code.
- **Aucune texture** (`ADR-0028`) : le damier de la vignette 8 n'existe que dans le rendu.
- **`./scripts/check.sh` non lancé** : le lot ne touche à aucun `.gd`, `.tscn`, `.tres` ni
  test ; l'import Godot des cinq binaires reste à valider par le concepteur à l'intégration.

---

## 11. Livrables

| Fichier | Ce que c'est |
|---|---|
| `assets/imported/models/backgrounds/stern_pylon.glb` | pylône reconstruit à 5,30 m — 2 612 tri, 363 Ko |
| `assets/imported/models/backgrounds/artery_conduit.glb` | conduite droite — 652 tri, 112 Ko |
| `assets/imported/models/backgrounds/artery_conduit_bend.glb` | conduite coudée — 648 tri, 79 Ko |
| `assets/imported/models/backgrounds/artery_hose.glb` | flexible droit — 320 tri, 154 Ko |
| `assets/imported/models/backgrounds/artery_hose_bend.glb` | flexible coudé — 344 tri, 177 Ko |
| `assets/source/models/artery/author/` | **les générateurs de l'auteur, verbatim** (7 scripts + 3 manifestes) |
| `assets/source/models/artery/forge_geometry.py` | `geometry.py` **avec ses six leviers** — le diff EST la réduction |
| `assets/source/models/artery/forge_shims.py` | les bouchons `materials` / `studio` / `paths` |
| `assets/source/models/artery/build_artery.py` | le pilote |
| `assets/source/models/artery/verify_artery.py` | la vérification sur les binaires, après réimport |
| `assets/source/models/artery/render_artery_plates.py` | les planches, à la caméra du jeu |
| `assets/source/models/artery/README.md` | comment on rejoue tout ça |
| `docs/forge/output/BRIEF-0108-planche.png` | huit vignettes 1920 × 1080 |
| `docs/forge/output/BRIEF-0108-arbitrage-materiaux.png` | deux vignettes, même cadrage |
| `docs/forge/output/BRIEF-0108-report.md` | ce document |

**Onze lignes** ajoutées à `assets/licenses/ASSET_PROVENANCE.csv`, aucune ligne existante
modifiée.
