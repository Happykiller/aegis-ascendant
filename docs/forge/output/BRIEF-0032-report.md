# BRIEF-0032 — Aegis Citadel : reforge complète — compte-rendu

- **Brief** : `docs/forge/briefs/BRIEF-0032-aegis-citadel-reforge.md`
- **Exécuté par** : asset-forge (Claude) — Blender 4.5.11 LTS, headless
- **Date** : 2026-07-21
- **Référence de design** : `assets/reference/concepts/aegis_citadel_concept_sheet.png` (lue avec `Read`)
- **Cadre** : ADR-0013 (textures déverrouillées), ADR-0011 (budgets, hauteur 5,60 m),
  ADR-0008 (pipeline 3D), `docs/forge/CHARTE_CREATIVE.md`

---

## 1. Livrables

| Fichier | État | Mesure |
|---|---|---|
| `tools/blender/build_aegis_citadel.py` | retravaillé | 1 345 lignes |
| `assets/imported/models/structures/aegis_citadel.glb` | régénéré | 62 712 tri / 4 533 972 o |
| `tools/blender/build_citadel_turret.py` | **nouveau** | 203 lignes |
| `assets/imported/models/structures/citadel_turret.glb` | **nouveau** | 2 596 tri / 180 924 o |
| `tools/blender/build_citadel_beacon.py` | **nouveau** | 225 lignes |
| `assets/imported/models/structures/citadel_beacon.glb` | **nouveau** | 1 852 tri / 150 296 o |
| `docs/forge/output/BRIEF-0032-report.md` | ce fichier | — |
| `assets/licenses/ASSET_PROVENANCE.csv` | ligne coque **réécrite** + 2 ajoutées | 126 lignes |

`aegis_kit.py` n'a **pas** été modifié. Aucune texture n'est embarquée dans les `.glb`.
Les deux nouveaux `.glb` n'ont pas encore de `.import` : c'est Godot qui les génère au premier
import, côté session principale.

---

## 2. Mesures réelles

### Coque — `aegis_citadel.glb`

| Grandeur | Mesure | Contrat | Verdict |
|---|---|---|---|
| Triangles | **62 712** | ≤ 120 000 (cible 70-90 k) | OK, sous la cible basse — voir §7 |
| Sommets | 86 388 | — | — |
| Largeur X | **19,6316 m** | 19,60 ± 3 % | +0,16 % |
| Longueur Z | **16,6044 m** | 16,60 ± 3 % | +0,03 % |
| Hauteur Y | **5,3000 m** | ≤ 5,60 m | 0,30 m de marge |
| Pivot | (−0,0000 ; +0,0023) en X/Z | ± 0,02 m | OK |
| Matériaux | 7/7 | `MATERIAL_ORDER` | OK |
| `TEXCOORD_0` + `TANGENT` | présents sur les **7** primitives | exigés | OK |
| Points d'attache | 17 | 17 exigés | OK |

Répartition par matériau (triangles) : `AA_Greeble` 36 469 · `AA_Hull` 11 915 · `AA_Trim` 8 070 ·
`AA_Emissive_Engine` 4 108 · `AA_Panel` 1 798 · `AA_Marking_Red` 308 · `AA_Glass` 44.

⚠️ Ce tableau ne dit **pas** la surface : `AA_Greeble` domine en triangles parce que les joints de
plaque sont des couronnes fines, très nombreuses et très petites. En surface, la coque reste
franchement ivoire — le rendu le confirme.

**509 plaques** ont été découpées (180 sur le corps central, 329 sur les deux bras).

### Sous-modèles

| | Triangles | bbox X × Y × Z (Godot) | Budget |
|---|---|---|---|
| `citadel_turret.glb` | **2 596** | 1,480 × 0,750 × 2,079 m | 3 000 (brief : « ~2 000 ») |
| `citadel_beacon.glb` | **1 852** | 0,940 × 0,510 × 0,940 m | 2 000 (brief : « ~1 200 ») |

La balise dépasse l'ordre de grandeur annoncé (1 852 contre ~1 200). Le coût ne vient pas du nombre
de facettes — descendre la nacelle de 12 à 10 segments et l'anneau de 20 à 16 n'a rendu que
32 triangles — mais des **petites boîtes** (feux d'anneau, tuyères, visière, marquage) et du biseau
qui les suit. Descendre à 1 200 exigerait de supprimer des pièces que la planche montre. J'ai
préféré livrer la pièce complète et le dire.

---

## 3. Points d'ancrage — coordonnées exactes

Ce sont les positions demandées par la correction du coordinateur : **l'origine du sous-modèle et
le marqueur coïncident**. Elles sont dérivées de la géométrie (`turret_seat()` interpole le pont
depuis les tables de profil), jamais écrites à la main.

Rappel de la chaîne d'axes ADR-0008 : `(x, y, z)` auteur → `(−x, z, y)` Godot. **Bâbord = +X auteur
= −X Godot.**

| Marqueur | Repère d'auteur (x, y, z) | **Repère Godot (x, y, z)** | Ce que c'est |
|---|---|---|---|
| `Turret_01` | (+2,000 ; −6,200 ; +1,0800) | **(−2,0000 ; +1,0800 ; −6,2000)** | assise sur le pont, épaule avant bâbord |
| `Turret_02` | (−2,000 ; −6,200 ; +1,0800) | **(+2,0000 ; +1,0800 ; −6,2000)** | épaule avant tribord |
| `Turret_03` | (+2,850 ; +2,050 ; +1,2007) | **(−2,8500 ; +1,2007 ; +2,0500)** | flanc arrière bâbord |
| `Turret_04` | (−2,850 ; +2,050 ; +1,2007) | **(+2,8500 ; +1,2007 ; +2,0500)** | flanc arrière tribord |
| `Turret_05` | (+7,650 ; +0,300 ; +1,0387) | **(−7,6500 ; +1,0387 ; +0,3000)** | pont du bras bâbord |
| `Turret_06` | (−7,650 ; +0,300 ; +1,0387) | **(+7,6500 ; +1,0387 ; +0,3000)** | pont du bras tribord |
| `Beacon_01` | (0,000 ; −7,550 ; +2,550) | **(+0,0000 ; +2,5500 ; −7,5500)** | centre de nacelle, au-dessus de la proue |
| `Beacon_02` | (+4,600 ; +5,600 ; +1,850) | **(−4,6000 ; +1,8500 ; +5,6000)** | en retrait, poupe bâbord |
| `Beacon_03` | (−4,600 ; +5,600 ; +1,850) | **(+4,6000 ; +1,8500 ; +5,6000)** | en retrait, poupe tribord |

**Les Y de tourelle diffèrent** (1,0800 / 1,2007 / 1,0387) parce que le pont n'est pas plat : la
valeur est lue sur la table de profil à la station de chaque tourelle. C'est voulu.

**Marge d'animation vérifiée** (dérive annoncée ±0,55 m en orbite, ±0,30 m en vertical) :

- `Beacon_01` — au plus bas et au plus proche, le dessous de la nacelle est à **1,99 m** ; la pièce
  la plus haute sous elle (mât d'antenne de proue) culmine à **1,72 m**. 27 cm de garde.
  En plan, la nacelle va jusqu'à y = −8,10 m, dedans la bbox (−8,30).
- `Beacon_02/03` — à x = 4,60 ± 0,55 et y = 5,60 ± 0,55, il n'y a **aucune coque** : le culot des
  bras s'arrête à y = +3,70 et la rampe ne fait que 1,66 m de demi-largeur. Débord bbox : x max
  5,15 (limite 9,80), y max 6,15 (limite 8,30).

Autres points d'attache, inchangés et vérifiés présents : `Core_Center`, `Muzzle_Battery_L/R`
(sur le tube le plus avancé, Godot ±8,20 ; +1,34 ; −8,35), `Dock_Entry`, `Core_Prism`,
`Battery_L/R`, `Dock_Bay`.

Les sous-modèles portent leurs propres repères : tourelle `Turret_Pivot` (0,0,0), `Muzzle_L/R`,
`Turret_Lens` ; balise `Beacon_Center` (0,0,0), `Ring_Center`, `Ring_Axis`, `Beacon_Eye`.

---

## 4. UV — l'échelle retenue et pourquoi

`ak.box_project_uv(citadel, 0.12)` — **une tuile pour 8,33 m de coque**, appliqué à l'identique aux
trois modèles.

- Le Specter-9 est à **4 tuiles/m** parce qu'il mesure 2 m. Le même chiffre sur 19,6 m donnerait
  78 répétitions en travers de la forteresse : la feuille lit comme du bruit rayé, exactement le
  piège que le brief signale.
- À 0,12, une tuile couvre à peu près **un bras-batterie**. La feuille module les grandes surfaces
  sans concurrencer les plaques géométriques, qui restent la source du détail lisible.
- **La tourelle et la balise partagent la même densité**, alors qu'elles ne font que 1,5 m et 0,9 m
  et n'occupent donc qu'un fragment de tuile. C'est délibéré : deux échelles de feuille qui se
  touchent se voient — les plaques changeraient de taille au passage du socle de tourelle. La
  cohérence de l'assemblage prime sur la richesse d'une pièce de 1,5 m, dont le détail est de
  toute façon géométrique.

Vérifié dans les trois `.glb` : `TEXCOORD_0` **et** `TANGENT` présents sur **toutes** les primitives,
aucune `image` ni `texture` dans le glTF.

```
AegisCitadel  prim 0..6 : ['NORMAL', 'POSITION', 'TANGENT', 'TEXCOORD_0']
```

Note technique : sans `_triangulate_ngons()` (les n-gons des culots), l'exporteur glTF renonce aux
tangentes (« Tangent space can only be computed for tris/quads ») et le verrou d'ADR-0013 resterait
en place malgré les UV. Les trois scripts embarquent donc ce passage.

---

## 5. Déterminisme — **le critère n'est PAS tenu pour la coque**, et voici pourquoi

Deux exécutions consécutives de chaque script, `sha256sum` :

```
exécution 1                                                          exécution 2
1b2060ce50c66fb3a58008913b65ec118f0594bd0c5783fb7dc91e4cf57475ad     cb31ff5300d1ec395adeab4d12de659b2779334e8149165f637e82f9d3519165   aegis_citadel.glb   ✗
b36f1a0bcefb6e74f71b610bdf00e846ee92142095e3b91ca941061a83788cb7     b36f1a0bcefb6e74f71b610bdf00e846ee92142095e3b91ca941061a83788cb7   citadel_turret.glb  ✓
5ece8f47b4cf97150c5c3a76d5f28585518fbf6b5f63954b9ba51be4e7f1536d     5ece8f47b4cf97150c5c3a76d5f28585518fbf6b5f63954b9ba51be4e7f1536d   citadel_beacon.glb  ✓
```

**La tourelle et la balise sont byte-identiques. La coque ne l'est pas** : 2 octets d'écart sur
4 533 972 sur ce couple d'exécutions (2 à 8 selon les tirages ; cinq exécutions ont donné cinq
empreintes distinctes).

### Ce n'est pas du hasard non seedé, et ce n'est pas nouveau

Trois mesures, dans cet ordre :

1. **Tous les octets divergents sont dans des accesseurs `TANGENT`.** Vérifié en localisant chaque
   octet dans les `bufferViews` : accesseur 18 (`prim3.TANGENT`), accesseur 28 (`prim5.TANGENT`), etc.
2. **Le maillage, lui, est bit-à-bit identique.** En mettant à zéro les seuls buffers `TANGENT`, les
   cinq exécutions donnent la même empreinte :
   `06ba6b0e19e925a019477aab112fcb035c64ae41f13ccae421c2909c3452d051`.
   `POSITION`, `NORMAL`, `TEXCOORD_0` et `INDICES` sont donc parfaitement reproductibles — le
   script, ses graines et ses tirages ne sont pas en cause.
3. **Le défaut est PRÉ-EXISTANT.** Contrôle sur `build_specter_9.py`, script que je n'ai pas touché :
   deux exécutions donnent `bdb995be…` puis `2115be41…`, soit **4 octets d'écart, tous dans
   `prim0.TANGENT` et `prim3.TANGENT`**. L'invariant « deux exports byte-identiques » d'ADR-0008 et
   d'ADR-0011 a cessé d'être vrai le jour où `export_tangents=True` est entré dans le kit ; personne
   ne l'avait mesuré depuis.

Amplitude : les valeurs diffèrent de **1e-4** (ex. `0,395100` contre `0,395000`), ce qui ressemble à
un float instable dans ses derniers bits tombant de part et d'autre d'un arrondi de
déduplication de l'exporteur. Visuellement, 1e-4 sur une tangente normalisée est nul.

### Ce que je n'ai pas fait

Corriger demanderait de toucher `ak.export_hull()` (quantifier les tangentes après export, ou les
recalculer nous-mêmes). **Le brief l'interdit explicitement** : je le signale, la session principale
arbitre. Voir §9, suggestion 2.

---

## 6. Rendu et regard (ADR-0006) — ce que la planche montre vraiment

Rendus produits et **regardés** :

```
blender45 -b -P tools/render-hull.py -- assets/imported/models/structures/aegis_citadel.glb
blender45 -b -P tools/render-hull.py -- assets/imported/models/structures/citadel_turret.glb
blender45 -b -P tools/render-hull.py -- assets/imported/models/structures/citadel_beacon.glb
```

Plus une planche d'**assemblage** (coque + 6 tourelles + 3 balises posées sur leurs marqueurs) et
une vue arrière dédiée à la baie, produites par un script de vérification jetable — c'est le seul
moyen de contrôler que les pivots tombent juste, un marqueur mal placé ne se voyant qu'une fois la
pièce posée.

### Critère explicite du brief : « des dizaines de plaques, des liserés or, un cristal facetté »

**Tenu.** Sur la vue « jeu » et la vue de dessus, là où il n'y avait que trois grands aplats, on
voit maintenant un pavage de plaques (509 découpées) à joints sombres, des liserés or courant le
long d'une plaque sur six, des champs bleus contigus sur les flancs du corps central et sur le pont
des bras, et un cristal à plan hexagonal dont les arêtes de taille sont soulignées de nervures.

### Ce que je livre, honnêtement, comparé à la planche

Ce qui y est :

- plaquage ivoire découpé, joints visibles, liserés or ;
- **quatre canons par bras** en deux rangées d'altitude, culasses étagées, colliers dorés, manchons
  de bouche ivoire à âme cyan ;
- **tourelles dômées à lentille cyan annulaire** cerclée d'or et double tube, assises dans une
  cuvette du pont ;
- **trois balises flottantes**, nacelle facettée, anneau doré à feux cyan, œil cyan ;
- **baie d'appontage à gorge réellement creusée** : le portail est percé dans la face arrière (la
  dernière section n'est plus capée, elle est reliée à la bouche du tunnel), la gorge s'enfonce de
  1,9 m et son fond est lumineux — vue de l'arrière, on voit la lumière sortir du tunnel, avec
  linteau or, rails dorés, chevrons cyan et feux d'approche ;
- **cristal** à plan hexagonal, arête faîtière, épaulements, ceinture de taille, dans un cadre
  technique or/anthracite à contreforts et marquages rouges.

Ce qui n'y est pas, et pourquoi :

1. **Les plaques sont rectangulaires, la planche les montre polygonales et irrégulières.** C'est une
   limite d'outil, pas un choix : le détail naît de `bridge_rings`, qui produit une grille de bandes.
   L'irrégularité obtenue est celle des *longueurs* (runs de 1 à 4 bandes, tirés au sort de façon
   seedée) et celle des *rôles* (bleu, or, ivoire) — pas celle des contours. Voir §9, suggestion 4.
2. **Le cristal ne « brille » pas par facettes.** Physiquement impossible : un émissif ne reçoit pas
   la lumière, ses facettes ont toutes la même valeur. Les facettes n'existent que par les nervures
   anthracite. J'ai dû les élargir à **18 cm** (contre 9 au premier jet) : à 9 cm elles font un pixel
   à la distance de jeu et le noyau redevient une goutte blanche. C'est un compromis assumé — la
   planche, elle, dessine des arêtes *plus claires* que le corps du cristal, ce que la géométrie
   seule ne sait pas faire. C'est exactement le trou que la texture dédiée (ADR-0013) devra combler.
3. **Le corps central reste plus lisse que la planche** au niveau des épaisseurs de blindage : chaque
   plaque n'est enfoncée que de 3 cm, là où la planche suggère des plaques posées avec une vraie
   tranche. Aller plus loin sans casser la silhouette demanderait un « extrude par plaque », que le
   kit ne fait pas.
4. **Six tourelles**, pas plus : le contrat `Turret_01..06` est lu par le code Godot, la planche en
   montre davantage. Hors périmètre.

### Biseau : essayé à 2 segments, **resté à 1**, et voici la mesure

Le brief demandait de juger au rendu. Les deux versions ont été construites et rendues côte à côte :

| | Triangles | Lecture |
|---|---|---|
| `segments=1`, width 0,03 | **46 232** (à densité intermédiaire) | joints de plaque nets, arêtes du prisme franches |
| `segments=2`, width 0,03 | 92 334 | joints amollis, cadres ivoire des panneaux bleus fondus, arête externe empâtée |

Le doublement du budget achète un ramollissement. Sur une coque qui vaut par ses arêtes vives et
dont tout le nouveau détail EST une arête, c'est un mauvais échange. **Resté à 1 segment**, comme le
brief le prévoyait explicitement.

---

## 7. Budget : 62 712 triangles pour une cible de 70-90 k

Sous la cible basse, et je préfère l'assumer plutôt que de gonfler. Les leviers restants étaient :
`segments=2` sur le biseau (+30 000 — refusé au rendu, §6), un pas de station encore plus fin
(les plaques passeraient sous 30 cm, ce qui n'est plus une plaque de forteresse mais une tuile), ou
des greebles supplémentaires sous la quille (invisibles depuis la caméra de jeu — ADR-0011 dit que
ce qu'on y met n'existe pas).

Le brief dit « un plafond, pas un objectif ». Les 57 000 triangles de marge restent disponibles le
jour où une passe de détail *visible* les justifie.

Chemin parcouru : 21 028 → **62 712** triangles (×3,0), 112 → **1 798** triangles de `AA_Panel`,
0 → 509 plaques, 0 → UV+tangentes.

---

## 8. Décisions de construction notables

- **Densification sans changement de silhouette.** `densify()` insère des stations par interpolation
  **linéaire** : chaque point ajouté est déjà sur la surface. Les cassures franches (proue, épaule,
  hanche) restent des cassures — la table de 9 stations d'origine est intacte, ce sont ses sommets.
  Même principe latéralement : la section passe de 10 à **14 sommets**, les 4 ajoutés étant
  exactement sur les droites de leurs voisins. Le pont se découpe donc en quatre lisières au lieu de
  deux, sans arrondir quoi que ce soit. Bbox X/Z conservée à 0,16 % près.
- **Le cristal a été redessiné en plan.** Le premier jet échantillonnait un ovale : quelles que
  soient les facettes, il se rendait en œuf lumineux. La planche montre un **hexagone** — deux
  arêtes droites vers chaque pointe, un flanc parallèle. C'est ce changement-là, plus que le nombre
  de facettes, qui a sorti le noyau de son statut de goutte.
- **Sept sommets de section, pas dix.** Contrainte de lissage : `shade_smooth_by_angle(34°)` efface
  toute arête sous 34°. Une section à dix sommets donnait des arêtes à ~30° — lissées, donc
  inexistantes. Sept sommets portent la même hauteur avec des angles de 36 à 90°.
- **Deux pièges de normale documentés dans le code.** (a) `inset_panel(depth<0)` creuse le long de la
  normale de face, or les normales ne sont recalculées qu'à `new_object()` : la boucle du pont de
  rampe, parcourue bâbord→tribord, avait une normale vers le bas et l'inset **soulevait** le
  plancher de 12 cm, masquant ses propres chevrons. (b) Le dernier chevron de la rampe débordait de
  13 cm au-delà du talon et décentrait le pivot de 6,7 cm — c'est `export_hull()` qui l'a attrapé,
  pas moi.
- **Les nervures du cristal sont balayées** par pas de 12 cm le long de la surface (`_rib_chain`), et
  non posées d'une station à l'autre : à 20 cm la ceinture de taille se rendait en dents de scie là
  où le cristal se pince.
- **La quille reste sobre** (grandes découpes, pas de greebles) : ADR-0011, ce qui n'est pas visible
  depuis la caméra de jeu n'existe pas. Tout l'effort de détail est allé sur le pont, désormais vu
  de trois quarts en gros plan sur l'écran d'accueil.
- **L'œil de la balise est sur le CAPOT**, pas seulement à l'avant, pour la même raison : la caméra
  regarde à 20° de la verticale et ne voit presque jamais la face avant d'une balise.

---

## 9. Limites du kit rencontrées — `aegis_kit.py` NON modifié, arbitrage demandé

Cinq manques, par ordre d'impact. Aucun n'a été corrigé en douce.

1. **`export_hull()` n'exporte qu'UN objet maillé.** Conséquence directe sur ce brief :
   l'anneau de la balise **ne peut pas** être une pièce distincte, alors que le brief le demandait.
   Repli livré, comme prévu par le brief : les marqueurs **`Ring_Center`** (0,0,0) et **`Ring_Axis`**
   (0 ; 0 ; 0,30 auteur → 0 ; 0,30 ; 0 Godot) donnent le centre **et l'axe** de l'anneau — un point
   seul ne suffit pas à définir une rotation. Si Godot doit faire tourner l'anneau, il faut soit
   faire évoluer le kit vers un export multi-objets (`export_hull(parts: list[Object], …)`, chaque
   objet recevant la correction d'axe), soit livrer un `citadel_beacon_ring.glb` séparé.
2. **Les tangentes cassent l'invariant de déterminisme** (§5), pour toute la flotte et pas seulement
   ici. Deux issues possibles, à arbitrer : quantifier les `TANGENT` dans `export_hull()` après
   export (arrondi à ~1e-6, l'écart mesuré est de 1e-4 sur une valeur normalisée), ou assouplir
   l'invariant du kit en « byte-identique hors `TANGENT` », avec la vérification correspondante.
   Dans les deux cas c'est une décision de projet, pas un correctif de forge.
3. **`_triangulate_ngons()` est maintenant dupliqué dans quatre scripts** (Specter-9, citadelle,
   tourelle, balise). Ce n'est pas un détail de confort : sans lui **il n'y a pas de tangentes**,
   donc pas de relief, donc ADR-0013 reste lettre morte. Sa place est dans `export_hull()`, juste
   avant l'export.
4. **Aucune primitive de découpe de face.** Les plaques ne peuvent être que des unions de bandes de
   `bridge_rings`, d'où leur régularité rectangulaire (§6, écart n°1). Une primitive de subdivision
   de face (grille irrégulière seedée, ou découpe par plan) est ce qui manque pour atteindre le
   plaquage polygonal de la planche. C'est le plus gros gisement de fidélité restant.
5. **`inset_panel(depth)` suit une normale non encore recalculée** (§8). Soit `inset_panel` devrait
   raisonner en « vers l'intérieur du solide », soit le kit devrait exposer un
   `recalc_normals(bm)` public à appeler avant les insets. Le piège coûte une itération complète à
   chaque fois qu'on le rencontre.

Point de méthode, sans gravité : **`box_project_uv()` projette en coordonnées monde**, donc les
sous-modèles construits autour de l'origine échantillonnent tous le même coin de la feuille. Sans
conséquence avec une feuille répétable ; à savoir si un jour une carte non tuilable est utilisée.

Enfin, deux desserrages de contrat assumés et commentés dans le code : `pivot_tolerance=0,60` pour
la tourelle (son pivot est l'axe de rotation, pas le centre de bbox — les tubes débordent d'un
mètre) et `0,12` pour la balise. Le contrôle qui compte pour ces pièces, le témoin **asymétrique**
d'orientation (bouches de tir, œil), reste actif. Un drapeau `is_subassembly` dans `HullContract`
serait plus honnête qu'un nombre.

---

## 10. Critères d'acceptation

| Critère | État |
|---|---|
| Les trois scripts régénèrent sans erreur en headless | ✅ |
| Deux exécutions : `.glb` byte-identiques | ⚠️ **tourelle et balise oui, coque non** — cause identifiée, pré-existante, hors de mon périmètre (§5) |
| Bbox X/Z inchangée à ±3 % ; hauteur ≤ 5,60 m | ✅ 19,632 × 16,604 ; 5,300 m |
| Les trois `.glb` contiennent `TEXCOORD_0` et `TANGENT` | ✅ |
| Coque ≤ 120 000 triangles (cible 70-90 k) | ⚠️ 62 712 : sous le plafond, **sous la cible** (§7) |
| Points d'attache conservés + `Beacon_01..03` | ✅ 17/17 |
| Les tourelles ne sont plus dans le maillage de la coque | ✅ seuls les socles restent |
| Rendu et regardé ; dizaines de plaques, liserés or, cristal facetté | ✅ (§6) |
| Provenance : ligne coque réécrite, deux lignes ajoutées | ✅ |

---

## 11. Suggestions pour la suite

1. **Câbler les sous-modèles** : instancier `citadel_turret.glb` sur `Turret_01..06` et
   `citadel_beacon.glb` sur `Beacon_01..03` (coordonnées §3), puis animer — balayage lent des
   tourelles, orbite ±0,55 m / ±0,30 m des balises. C'est là que le pivot se vérifie vraiment.
2. **Mesurer le coût GPU** avant/après aux deux endroits où la coque apparaît (accueil et combat),
   comme l'exige ADR-0011 : ×3 sur la géométrie, plus 9 sous-modèles instanciés.
3. **Produire le jeu de textures dédié** (`docs/forge/output/citadel_textures_generation_prompt.md`) :
   la coque a désormais ses UV à 0,12 tuile/m. C'est ce qui apportera l'usure et les décalques que la
   géométrie ne peut pas porter, et surtout la lumière interne du cristal.
4. **Arbitrer les points §9**, en priorité le n°2 (déterminisme) et le n°4 (découpe de face).
