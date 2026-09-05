# BRIEF-0100 — Le kit de tourelles reforgé : compte-rendu de forge

- **Date** : 2026-09-05
- **Brief** : `docs/forge/briefs/BRIEF-0100-tourelles-trois-classes.md`
- **Planche cible** : `assets/reference/concepts/tourelles_lourdes_concept_sheet_2026-09-05.png`
- **Recettes portées** : `resources/gpt_models/tourelle-lourde_v1/build_turret.py` (+ `geometry.py`)
  — **recettes uniquement, aucun fichier, aucun matériau, aucune cote repris**

## Livrables

| Fichier | État |
|---|---|
| `tools/blender/build_turret_kit.py` | réécrit sur place (3000 lignes) |
| `assets/imported/models/backgrounds/turret_kit.glb` | régénéré — `sha256 da120b7d…`, 435 760 o |
| `docs/forge/output/BRIEF-0100-planche-tourelles.png` | 1440 × 3720, sept vignettes, produite par `-- --plate` |
| `docs/forge/output/BRIEF-0100-report.md` | ce fichier |
| `assets/licenses/ASSET_PROVENANCE.csv` | ligne `turret_kit` mise à jour, ligne de planche ajoutée |

---

## 1. ⛔ La cote de la planche ne passe pas, et ce n'est pas l'emprise qui l'interdit

Le brief demandait de mesurer **l'emprise**. La mesure a désigné une autre borne, plus serrée,
que personne n'avait relevée : **la hauteur**.

| | valeur | source |
|---|---|---|
| Plafond des pièces de gameplay | **−2,40** | `cortege_flyby.gd::GAMEPLAY_CEILING_Y`, `ADR/BRIEF-0094` |
| Assise la plus **haute** des 17 emplacements | **−4,270** (Turret_08) | `turret_seat_y()` |
| **Dégagement vertical disponible** | **1,870 m** | la différence |

Une tourelle lourde de **4,20 m** culminerait à **−0,07** : sept centimètres sous le plan de vol
du joueur. Ce n'est pas une marge à négocier, c'est la tourelle dans le cockpit.

### 1 bis. ⚠️ Et la classe lourde livrée aujourd'hui viole déjà ce plafond

`cortege_turret.gd` porte `HEAVY_GEOM_SCALE := 1.538` depuis le commit `f9516f8` de ce matin.
Appliqué au kit d'alors (1,70 m), il donne :

| marqueur lourd | assise | sommet à ×1,538 | plafond | **dépassement** |
|---|---|---|---|---|
| Turret_08 | −4,270 | **−1,655** | −2,40 | **+0,745 m** |
| Turret_12 | −4,276 | −1,661 | −2,40 | +0,739 m |
| Turret_15 | −4,284 | −1,669 | −2,40 | +0,731 m |

Le défaut est **silencieux dans les deux harnais** : le harnais du kit multipliait `TURRET_H`
par 1 (il ignorait les échelles), et `test_no_turret_ever_reaches_the_flight_plane` compose les
AABB avec les *lifts* du moteur **sans jamais appeler `_geom_scale()`**. Les trois lourdes
montent donc à 1,655 unité sous le plan de vol au lieu de 2,40, et rien ne le dit.

**Le nouveau harnais mesure classe par classe** (`_audit()`, bloc « LES TROIS CLASSES ») et
échoue le build si une classe dépasse. C'est ce qui fixe l'échelle lourde à **1,200**.

### 1 ter. Et une seconde borne, par le bas, que la mesure a fait apparaître

La peau **remonte** vers la crête dorsale au-delà de l'emprise, et les tubes balaient à 360°.
Montée maximale de la peau au-dessus de l'assise, sur le disque balayé :

| rayon | 3 m | 4 m | 5 m | 6 m | 7 m | 8 m |
|---|---|---|---|---|---|---|
| montée max | 0,608 | 0,631 | 0,651 | 0,665 | 0,679 | **0,898** |
| (marqueur) | T03 | T03 | T16 | T16 | T16 | T03 |

Le dessous d'un tube doit donc passer **au-dessus de 0,68 m** — sinon le canon laboure la coque
une fois par tour, et ça ne se voit qu'en jeu, en mouvement. À l'échelle native le dessous du
tube est à **0,745 m** (marge 0,104 m). Et **au-delà de ~7,5 m d'allonge la marge disparaît** :
c'est cette borne, et non le goût, qui limite la longueur des tubes.

**Conséquence** : la fenêtre verticale utile pour la classe native est **[≈1,55 ; 1,870] m** —
le bas fixé par la peau qui remonte (l'axe des tubes doit être haut), le haut par le plafond de
gameplay. D'où `TURRET_H = 1,52 m` et `s_lourde ≤ 1,870 / 1,52 = 1,230`.

---

## 2. Les trois classes — cotes MESURÉES sur le `.glb` livré

Le kit livre **une** géométrie ; le moteur en fait trois classes par mise à l'échelle
(`_geom_scale()`), exactement ce que la planche demande (« MODULES PARTAGÉS — MÊMES BLOCS.
TROIS ÉCHELLES »). Cotes relevées sur le binaire, pas annoncées.

| classe | échelle | longueur | écart planche | hauteur | écart planche | emprise R | allonge |
|---|---|---|---|---|---|---|---|
| légère | **0,538** | **2,88 m** | −17,6 % | **0,82 m** | −48,9 % | 1,00 m | 1,88 m |
| standard | **1,000** | **6,50 m** | **±0,0 %** | **1,52 m** | −45,7 % | 2,08 m | 4,42 m |
| lourde | **1,200** | **7,80 m** | −22,0 % | **1,82 m** | −56,6 % | 2,50 m | 5,30 m |

Planche : 3,5/1,6 · 6,5/2,8 · 10,0/4,2 m. La longueur est mesurée hors-tout, assemblée, azimut
nul : bord arrière de la pièce la plus large (jupe ou tambour) → bouche du tube.

**Ce qu'il faut changer côté moteur** (le code appartient au concepteur, la forge ne l'a pas
touché) :

| constante (`cortege_turret.gd`) | aujourd'hui | **à poser** | pourquoi |
|---|---|---|---|
| `HEAVY_GEOM_SCALE` | 1.538 | **1.200** | 1,538 met la lourde 0,745 m au-dessus du plafond de gameplay |
| `LIGHT_GEOM_SCALE` | 0.5 | **0.538** | le rapport de la planche elle-même (3,5 / 6,5) |
| `RING_LIFT` | 0.02 | **0.04** | cotes d'assemblage du kit reforgé |
| `BODY_LIFT` | 0.37 | **0.40** | idem |
| `BARREL_LIFT` | 0.90 | **0.98** | idem |
| `BARREL_SEAT_Z` | 0.60 | **0.70** | culasse au fond du masque, masque creusé de 0,14 |
| `SERVICE_RADIUS` | 1.46 | **1.66** | le plateau du socle a changé de rayon |
| `SERVICE_LIFT` | 0.14 | **0.20** | idem |
| `MUZZLE_REACH` | 3.50 | **4.42** | d'où sort la balle |
| `HIT_LIFT` | 0.90 | **0.98** | la masse se projette sur l'axe des tubes |
| `FAMILIES[*][2]` (écartements) | 0.72/0.86/0.98 | **0.80/0.92/1.00** | le masque est plus large |

⚠️ **Ces onze nombres sont périmés à la seconde où le `.glb` est committé.** Sans eux, le moteur
pose un bloc 3 cm trop bas, des tubes 8 cm trop bas et 10 cm trop en arrière, et l'appareillage
20 cm trop près de l'axe — visible, silencieux, et sans erreur au journal.

### Ce qui n'a pas pu être obtenu, et pourquoi

- **La hauteur de la planche, dans les trois classes.** −46 à −57 %. Borne dure, mesurée
  ci-dessus. La seule façon de l'atteindre serait de descendre le plafond des pièces de gameplay
  (décision de conception, hors périmètre) ou de creuser la coque sous les emplacements.
- **Les 10,0 m de la lourde.** Obtenus à 7,80 m (−22 %), et l'écart vient **entièrement** du
  facteur d'échelle ramené de 1,538 à 1,200. La classe standard, elle, tient la planche
  exactement (6,50 m).
- **Les proportions de la planche.** La planche montre une base ≈ 1,3 fois plus large que haute ;
  la nôtre est 2,4 fois plus large que haute. C'est la conséquence directe du point précédent, et
  c'est **le compromis le moins cher à l'écran** : sous une caméra qui plonge à 70°, un mètre de
  hauteur se projette à 0,34 m et un mètre de plan à 0,94 m. Un déficit de hauteur coûte donc
  presque trois fois moins qu'un déficit de longueur ou d'emprise, qui eux ont été tenus.

---

## 3. Le rayon d'emprise — mesuré, pas supposé

`turret_seat_y()` échantillonne la peau sur **2,08 m de rayon** pour poser l'assise du marqueur.
Le dénivelé sous l'emprise, aux dix-sept emplacements, en fonction du rayon :

| rayon | 2,08 | 2,40 | 2,60 | **2,80** | 3,00 | 3,20 | 3,60 | 4,00 |
|---|---|---|---|---|---|---|---|---|
| dénivelé max | 0,684 | 0,714 | 0,729 | **0,995** | 1,386 | 1,914 | 3,118 | 4,624 |
| emplacements > 0,85 m | 0 | 0 | 0 | **3** | 4 | 4 | 7 | 11 |

**Réponse en trois temps :**

1. **2,08 m est le plus grand rayon posable partout**, et c'est une borne de la **coque**, pas du
   terrain : au-delà, le socle déborde sur de la peau que `turret_seat_y()` n'a jamais
   échantillonnée. Le kit y reste **exactement** (`SKIRT_R = cortege.TURRET_FOOTPRINT_R`, lu et
   non recopié). C'est l'emprise retenue à l'échelle native.
2. **Le terrain, lui, en autoriserait 2,60 m** aux dix-sept emplacements (dénivelé ≤ 0,729 m).
   Il décroche à 2,80 (T02 0,995 · T16 0,972 · T10 0,854) et s'effondre à 3,20 (T16 1,914).
   Une emprise plus large que 2,60 demanderait donc **une reforge de la coque**, pas seulement du
   kit — et n'apporterait rien.
3. **Les 3,62 m du modèle tiers ne se posent nulle part** : à ce rayon le pourtour accuse jusqu'à
   2,6 m de dénivelé. La capture en jeu du 2026-09-05 (« il débordait déjà de la coque ») est
   confirmée par la mesure.

### Où la lourde se pose, et où elle ne se pose pas

L'emprise de la lourde vaut **2,50 m** (2,08 × 1,200). Elle dépasse le rayon d'échantillonnage
de la coque de 0,42 m — **et c'est mesuré comme sûr, pas supposé** : aux trois marqueurs que le
moteur lui réserve (`HEAVY_TURRETS = Turret_08, Turret_12, Turret_15`), la peau ne remonte
**jamais** au-dessus de l'assise sur ce disque (montée 0,037 / 0,010 / 0,013 m), donc le socle ne
peut pas la traverser ; le creux qu'elle enjambe (0,709 m au pire des dix-sept) est absorbé par
une jupe enterrée de 2,40 m à cette échelle.

**Elle se pose donc aux dix-sept emplacements sans exception** — les trois retenus par le moteur
sont même parmi les plus plats de la coque. La contrainte qui la borne n'est pas *où*, c'est
*combien* : `s = 1,200` et pas davantage, à cause du plafond vertical.

### ⚠️ Un défaut latent trouvé au passage : les tourelles légères FLOTTAIENT

L'assise est calculée sur un disque de 2,08 m, mais le socle d'une **légère** ne fait que 1,00 m
de rayon. Sous elle, le creux vaut encore **0,648 m** (T09) — et sa jupe, mise à l'échelle,
n'en couvrait que 0,85 × 0,5 = **0,425 m**. Les légères flottaient donc jusqu'à 0,22 m depuis
BRIEF-0093, sans qu'aucun harnais le voie.

Corrigé : `PAD_BURIED` passe de 0,85 à **2,00 m**, ce qui donne 1,076 m à l'échelle légère pour
un creux de 0,648 m. C'est de la géométrie **enterrée dans la coque** : elle ne coûte que
144 triangles invisibles et ne se voit jamais en jeu. Le harnais mesure désormais le creux
**au rayon de chaque classe** (`turret_hollow()`), pas au rayon d'échantillonnage.

---

## 4. Les quatre recettes portées

Aucun fichier, aucun matériau, aucune cote du modèle tiers n'a été repris. Les recettes ont été
ré-exprimées avec `tools/blender/lib/aegis_kit.py` et la palette du Chœur Nul.

### Recette 1 — le socle est fait de modules, pas d'un disque

Chez eux : 24 secteurs blindés + 24 panneaux d'accès + 24 tôles + 24 verrous + 48 boulons =
**~144 maillages pour le seul socle**. Ici : **zéro maillage de plus**. Le découpage est obtenu
en **modulant le rayon du même anneau de révolution** — deux sommets au rayon plein, un sommet en
retrait de 7 cm, ×24 modules (72 segments). Chaque module montre une facette plate et une gorge
en V sur toute la hauteur du tambour, et le socle reste **une coque fermée**, ce qui est la seule
chose que `_assert_solid()` sait prouver.

Les vingt-quatre **panneaux d'accès du plateau** suivent le même principe : une hauteur *par
sommet* (relief de 3 cm) et un matériau *par segment* (violet sombre sur la semelle, noir dans le
joint). Coût : zéro face supplémentaire.

### Recette 2 — la plaque, le retrait, le liseré ⭐

C'est la dépense la plus rentable du fichier, et le brief avait raison. Toute plaque rapportée
est posée sur un **retrait sombre** (`AA_Greeble`) et bordée d'un **liseré ivoire** (`AA_Trim`,
métallicité 0,85) de 3 à 5 cm : socle, jupe, couronne, plaques de flanc, dalles de toit, viseur,
bloc de recul, coffret, et chacun des trois gradins de chemise des tubes.

C'est le seul détail qui satisfait **les deux seuils mesurés à la fois**
(`docs/forge/textures/README.md`, relevé du 2026-09-05) : 5 cm passent le seuil de *présence*
(~4,4 cm de monde à 45,8 px/m) **et** l'ivoire sur anthracite tranche de bien plus que les dix
niveaux du plancher de contraste. Rappel de la mesure : un contour de 27 px qui ne module que
quatre niveaux se lit **moins bien** qu'une gorge de 5,9 px qui tranche en noir.

⚠️ **Corrigé après avoir regardé le premier rendu** (`ADR-0006`) : posé en anneau **continu**, ce
liseré rendait un **halo blanc autour de chaque tourelle** à la caméra du jeu — la faute exacte
que `BRIEF-0089` avait chiffrée et que ce fichier documente déjà sur la couronne de la jupe. Il
est maintenant **pointillé** : un trait par semelle (24 sur le socle, 12 sur la jupe, 16 sur la
couronne). Il dit la même chose — « les plaques sont séparées, leurs joints sont bordés d'une
arête claire » — et il ne cerne plus la pièce. Part d'ivoire dans l'aire **vue** : **7,5 %**.

### Recette 3 — chemises en gradins, bouche réellement creuse

Le tube passe de 5 paliers à **21**. Manchon de recul (Ø 0,52) fermé par un liseré, puis **trois
gradins** de 0,235 → 0,215 → 0,195 m de rayon, chacun fermé par un liseré clair et un épaulement
sombre, puis le tube nu, le frein de bouche, la lèvre claire, et **l'alésage** : couronne de
lèvre, chemise, fond sombre **55 cm en retrait**. Le tout est **une seule coque fermée** — le
bricolage « anneau de bouche recousu à la main » de la version précédente a disparu.

### Recette 4 — le magenta réduit à des fentes

L'œil rond de 0,36 m a **disparu**. Il reste, sur toute la tourelle :

- une fente de **0,32 × 0,03 m** au fond du masque, entre les deux tubes (21,1 % de la hauteur,
  règle dure : 25 %) ;
- deux fentes de **0,03 × 0,30 m** sur les joues ;
- une fente de **3 cm** sur **4 des 24 modules** du socle — obtenue par un *matériau par segment*
  sur une bande de 3 cm, donc **zéro face supplémentaire**.

Aire émissive sur la tourelle assemblée : **0,1 m² sur 142,6**, soit **0,2 % de ce qui est vu**.

---

## 5. Contrat avec le moteur : diff des noms

**Aucune pièce renommée, aucune pièce neuve, aucune pièce supprimée.**

| pièce | origine | inchangée ? |
|---|---|---|
| `turret_pad` | centre, Y = assise | ✅ |
| `turret_anchor_skirt` | centre, Y = assise | ✅ |
| `turret_ring` | centre, **sur l'axe de rotation** | ✅ |
| `turret_body` | centre, sur l'axe | ✅ |
| `turret_barrel` | la culasse | ✅ (longueur 2,90 → 3,72 m) |
| `turret_barrel_short` | la culasse | ✅ (2,20 → 2,80 m) |
| `turret_service_box` | sa base | ✅ |
| `turret_pipe` | sa base | ✅ |

**Pièces posées par tourelle : 9** (lourde et standard), 4 pour la légère — **identique à
BRIEF-0093**, donc +0 sur les +2 autorisés. Tout le détail est **fusionné dans les huit
maillages**. À titre de comparaison, le modèle tiers pose 465 maillages ; à dix-sept tourelles ce
serait 7 905 instances.

`_assert_on_axis()` est **conservé et vert** sur `turret_ring` (centroïde + bbox, X **et** Z) et
sur `turret_body` (X seulement — il doit rester dissymétrique en Z, c'est ce qui fait qu'on lit
où il regarde). Mesuré sur les positions **uniques** du binaire, au micron.

---

## 6. Le compte réel

| | valeur |
|---|---|
| Triangles du kit (8 pièces, une fois) | **6 088** |
| Triangles d'une tourelle **assemblée** (9 pièces) | **6 228** — 2 364 avant, ×2,63 |
| Triangles des **dix-sept** tourelles | **105 876** — 40 188 avant |
| Maillages / primitives | 8 / **30** |
| `TEXCOORD_0` **compté** | **30 / 30** |
| `TANGENT` compté | **30 / 30** |
| Images embarquées | **0** — le harnais échoue le build si l'une apparaît |
| Octets | **435 760** |

Le budget de triangles **n'est plus un critère d'acceptation** (`ADR-0044`, et le brief le
confirme : quatre relevés GPU dominés par leur dispersion n'établissent aucun surcoût). Les deux
constantes `TRI_BUDGET_*` restent dans le fichier comme **garde-fou d'emballement** — trois fois
le compte mesuré — et le paragraphe qui les justifiait par le post-traitement rétro a été
supprimé.

### Le paragraphe périmé a disparu

Le fichier disait, en toutes lettres, sous « OÙ LE BUDGET A ÉTÉ DÉPENSÉ » : « *le
post-traitement rétro rend à 960x540, soit 23 px/m sur la coque, et toute géométrie plus fine que
9 cm est moyennée puis disparaît* ». `ADR-0045` a supprimé ce filtre du dépôt. **Le paragraphe
est supprimé et remplacé** par ce qui est vrai aujourd'hui, mesuré sur capture 1920×1080 native :
45,8 px/m en travers, 40,0 px/m dans l'axe (rapport 0,87 — la densité **n'est pas isotrope**),
≈41 px/m sur le pont ; seuil de présence ~2 px (4,4 cm), seuil de forme ~3 px (6,5 cm), plancher
de contraste ~10 niveaux. C'est ce qui autorise 72 segments au socle et 24 modules lisibles.

### Répartition en aire, relevée sur le `.glb`

| matériau | kit brut | tourelle assemblée | **ce qui est VU** |
|---|---|---|---|
| `AA_Greeble` | 65,4 % | 64,7 % | **29,0 %** |
| `AA_Hull` | 27,7 % | 28,3 % | **54,6 %** |
| `AA_Panel` | 3,1 % | 3,3 % | **8,8 %** |
| `AA_Trim` | 3,6 % | 3,6 % | **7,5 %** |
| `AA_Emissive_Engine` | 0,1 % | 0,1 % | **0,2 %** |

Est « vu » ce qui est au-dessus du plan d'assise **et** qui ne regarde pas le pont (la caméra
plonge à 70° : une face tournée vers le pont ne lui est jamais présentée). L'écart entre « kit
brut » et « vu » est la jupe enterrée de 2,00 m, qui pèse lourd et ne rend pas un pixel.

---

## 7. Palette et matériaux

`ak.set_faction(ak.FACTION_NULL_CHOIR)`, **sept slots, aucun matériau nouveau**.
`MATERIAL_ORDER` et `_MATERIAL_SPECS` d'`aegis_kit.py` **n'ont pas été touchés**.

| leur matériau | notre slot | usage ici |
|---|---|---|
| `dark weathered armor` | `AA_Hull` | la masse blindée, les semelles, les tubes |
| `warm graphite panels` | `AA_Panel` | panneaux d'accès du plateau, dalles de toit, piste de couronne |
| `deep graphite recesses` | `AA_Greeble` | joints, retraits, jupe enterrée, alésage |
| `rubbed titanium edges` + `recoil piston steel` | `AA_Trim` | **le liseré**, les conduites |
| `unlit bore interior` | `AA_Greeble` | le fond d'alésage |
| `restrained magenta energy` | `AA_Emissive_Engine` | les fentes |
| `serial markings` | **rien** | voir ci-dessous |

⚠️ **Aucun marquage n'est posé.** Le brief autorisait `AA_Marking_Red` « en usage très limité —
ou rien ». Dans la palette du Chœur Nul ce slot vaut **vert maladif `#7C9E52`**, dont la charte
dit « usage très limité » : une sérigraphie verte sur dix-sept tourelles n'est pas « limitée ».
Et le matricule `LC / CITADELLE / 03` du modèle tiers ne se recopie évidemment pas. **Rien** a
donc été choisi. Si un matricule est voulu, il relève d'une demande de texture pour le niveau
entier, pas d'un slot de géométrie.

---

## 8. Texture — aucune, et le brief le dit

Le brief **porte sa section `## Texture`** (`ADR-0028`) et déclare explicitement n'en demander
aucune : le niveau 2 entier est en PBR par facteurs, sans une seule image, et le harnais échoue
le build si une carte apparaît. Rien n'a donc été livré comme texture.

- **Dépliage** : `ak.box_project_uv()` à **0,200 tuile/m** (5,00 m par tuile) — la densité du
  bordé, **relue dans `build_long_cortege.HULL_TEXELS_PER_METER`** et non recopiée. (Le brief
  écrivait « 0,12 tuile/m » ; la valeur réelle du fichier est 0,200, et c'est elle qui a été
  suivie, comme le brief le demandait.)
- **Densité mesurée sur le binaire**, par valeurs singulières triangle par triangle (une moyenne
  d'aires ne verrait aucun étirement) :

| pièce | min | max | moyenne | m/tuile | anisotropie max |
|---|---|---|---|---|---|
| `turret_pad` | 0,125 | 0,200 | 0,191 | 5,22 | 1,60 |
| `turret_anchor_skirt` | 0,118 | 0,200 | 0,188 | 5,33 | 1,70 |
| `turret_ring` | 0,141 | 0,200 | 0,195 | 5,13 | 1,42 |
| `turret_body` | 0,115 | 0,200 | 0,193 | 5,19 | **1,73** |
| `turret_barrel` | 0,135 | 0,200 | 0,190 | 5,27 | 1,48 |
| `turret_barrel_short` | 0,135 | 0,200 | 0,190 | 5,26 | 1,48 |
| `turret_service_box` | 0,127 | 0,200 | 0,190 | 5,27 | 1,57 |
| `turret_pipe` | 0,140 | 0,200 | 0,193 | 5,18 | 1,43 |

1,73 est **la borne théorique de la projection en boîte** (√3) : une face à 45° des trois axes.
Aucune pièce ne la dépasse.

- **Coutures** : une projection en boîte coupe sur les six changements d'axe dominant. Elles sont
  donc sur les arêtes de la géométrie, jamais au milieu d'une face — c'est le comportement voulu
  pour une pièce vue de loin et sans carte de détail.
- **Pas de planche au damier « dépliage continu »** : le brief demande explicitement une
  projection en boîte, pas un dépliage continu. Une vignette au damier est quand même livrée
  (vignette 7), à la perspective du jeu, pour vérifier que le grain du kit et celui du bordé sont
  les mêmes — c'est la faute que `BRIEF-0090` avait corrigée sur Ambry.

---

## 9. Déterminisme

`./scripts/build-hull.sh --check turret_kit` lancé **deux fois** (soit **quatre** exécutions
Blender `-t 1`) :

```
[build-hull]   déterminisme OK — da120b7d1f5588ea1b3fa6bc87d03e1efb4c88cd49a5df6709436f3679448b95
[build-hull]   déterminisme OK — da120b7d1f5588ea1b3fa6bc87d03e1efb4c88cd49a5df6709436f3679448b95
```

**Zéro octet divergent.** Le motif `set(asset.objects)` du script tiers **n'a pas été porté** :
tout ce qui est itéré ici est un `tuple` ou un `range` (`_module_relief()` rend un tuple,
`PAD_GLOW_MODULES` est un tuple écrit). Le seul `set` du fichier sert de test d'appartenance
(`skip`), jamais d'ordre d'émission.

---

## 10. La planche de recette

`docs/forge/output/BRIEF-0100-planche-tourelles.png`, 1440 × 3720, Cycles CPU 32 échantillons,
produite par **le même script** (`-- --plate`). Sept vignettes :

1. **Test d'acceptation, noir et blanc, émissifs coupés** — une tourelle et un hangar dans le
   même cadre, caméra de `graybox.tscn` sans retouche (0 14 5, FOV 62, 70° sous l'horizontale),
   Specter-9 réel à sa place de jeu. Verdict : le hangar **CREUSE** (un cadre vide), la tourelle
   **DÉPASSE** (deux tubes à 4,42 m de l'axe). Aucune confusion possible, sans une seule aide de
   couleur ni de lumière. **Le test de `BRIEF-0093` est rejoué et passé.**
2. **Le même cadre en couleur** — ce que l'émissif ajoute à une fonction déjà lisible.
3. **Trois quarts, lourde seule** — les 24 semelles, les liserés pointillés, les gradins de
   chemise, les bouches creuses.
4. **Les trois classes côte à côte, à la caméra du jeu**, avec leurs cotes et leur écart à la
   planche.
5. **Le test des 55 px** (règle 5 de la planche) — les trois silhouettes rendues **à 55 pixels de
   large**, en blanc plat sur noir, à taille réelle **et** agrandies six fois au plus proche
   voisin (aucune interpolation : on regarde les pixels du test). Résultat : 55 × 19 px pour la
   légère, 55 × 17 px pour les deux autres ; socle, tête et tube restent séparables sur les trois.
6. **Élévation de flanc, les trois classes**, avec les trois plans qui décident : assise (ambre),
   plafond du décor (rouge), plafond des pièces de gameplay (vert).
7. **Damier UV** à l'angle du jeu, même échelle sur la coque et sur le kit.

### ⚠️ Deux défauts trouvés *en regardant* la planche, pas en la mesurant (ADR-0006)

- **Le halo blanc** (recette 2, ci-dessus) : invisible à toute mesure, évident au premier rendu.
- **La paire du test d'acceptation était périmée.** Le fichier disait « Turret_14 (s = 428) et
  Bay_07 (s = 436), à 8 m l'une de l'autre » ; dans la coque livrée aujourd'hui, Turret_14 est à
  s = 415,2 et Bay_07 à s = 450 — **35 m**, donc les deux hors cadre, et la vignette rendait une
  vue générale du vaisseau. Le couple le plus proche des tables actuelles est **Turret_06 /
  Bay_04** (8,05 m, même bord) : c'est lui qui sert désormais. *Ce genre de péremption n'échoue
  aucun harnais : le rendu part sans erreur, il ne montre simplement plus rien.*

---

## 11. Ce qui reste ouvert

- **Les onze constantes du moteur** de la section 2 — c'est le seul travail bloquant.
- **Le balayage au-dessus d'un pont d'envol** : l'allonge portée à 4,42 m fait que Turret_05,
  Turret_06 et Turret_10 balaient de 1,2 à 1,8 m **au-delà du coaming** d'un hangar voisin
  (mesure au rapport de build). Le garde mutuel de `BRIEF-0092` arbitre sur des **socles** ; il
  ne connaît pas les tubes. À trancher côté conception : soit c'est voulu (une batterie qui
  couvre son hangar), soit deux stations bougent de trois mètres.
- **L'élévation et le recul** : hors périmètre, volontairement. La place est **prévue** — le
  berceau est plat entre les deux manchons et le masque est en dépouille, un tourillon
  transversal viendrait s'y loger sans toucher à la forme — mais **rien n'est gréé** : le kit ne
  livre aucune animation, c'est le moteur qui compose et qui fait tourner (`ADR-0046` §6).
- **Le prototype tiers** (`proto_tourelle_lourde.glb`, `--turret-proto`) reste branché dans
  `cortege_turret.gd`. Il a servi de recette ; il n'a plus de rôle. Son retrait est un bloc
  (`PROTO_PATH`, `_build_proto_head()`, le `.glb` et ses trois PNG de texture) — décision du
  concepteur.
- **Les seize autres tourelles du jeu** (citadelle, Léviathan) : aucune campagne de rattrapage,
  comme le brief le demande.
- ⚠️ **La lisibilité de l'ÉTAT de la tourelle est à revérifier en jeu.** La règle 4 de la planche
  a fait passer l'émissif de 0,36 m de lentille ronde à des traits de 3 cm : il ne pèse plus que
  **0,2 %** de l'aire vue. Sur la vignette 2 (caméra du jeu, couleur), le magenta de la tourelle
  est à la limite du visible. C'est exactement ce que la règle demande — mais `cortege_turret.gd`
  s'en sert pour dire *télégraphe / abîmée / morte*. Si l'état ne se lit plus, **la réponse est
  d'augmenter l'énergie des matériaux côté moteur (`GLOW_*`), pas d'agrandir la fente** : les
  deux fentes de joue ont justement été ajoutées pour qu'un état reste lisible quel que soit
  l'azimut de la tourelle.

## 12. Portes de qualité

- `./scripts/build-hull.sh --check turret_kit` : **vert**, trois lancements, zéro octet divergent.
- `./scripts/check.sh` : **import headless Godot OK** ; le script échoue ensuite sur une règle
  dure **étrangère à ce lot** — `tests/unit/test_cortege_turret_scales.gd.uid` n'est pas suivi
  par git. Ce `.uid` est généré à l'import par Godot pour un test créé ce matin côté moteur
  (commit `f9516f8`) ; la forge ne touche pas à `tests/`. Il est à `git add` par le concepteur.
- Aucun `.gd`, `.tscn` ni `.tres` modifié — vérifié par `git status`.
