# BRIEF-0044 — Leech Drone, coque 3D : compte-rendu

*Livré le 2026-08-23 par `asset-forge`. `leech_drone.glb` sha256
`f812c5d12c166a3d149ef0a129184e560cfccf01751907e4909dbb537e1af754` (330 804 o).*

## 1. Livrables

| Fichier | Quoi |
|---|---|
| `tools/blender/build_leech_drone.py` | script de construction, déterministe, auto-validant, trois harnais de mesure |
| `assets/imported/models/ships/leech_drone.glb` | le mesh (LFS) |
| `docs/forge/output/BRIEF-0044-planche-quatre-vues.png` | recette 4 vues au repos (ADR-0006) |
| `docs/forge/output/BRIEF-0044-pinces-ouvertes.png` | 6 poses **à la perspective réelle du jeu** + rangée réduite à 46 px |
| `docs/forge/output/BRIEF-0044-silhouette-comparee.png` | aplats noirs : Leech Drone / Needle Scout / Choir Mine / Null Maw |
| `docs/forge/output/BRIEF-0044-report.md` | ce document |

## 2. Les trois chiffres que le brief exige

| Question | Réponse mesurée |
|---|---|
| Croissance du diamètre apparent, **caméra de `graybox.tscn`** | **+22,9 %** (nez opposé au joueur) / **+16,2 %** (nez vers le joueur) |
| Seuil de 12 % franchi à | **20°** / **33°** selon l'orientation — la valeur retenue, 51°, a de la marge dans les deux |
| Débattement mécanique | **aucune butée dans le domaine utilisable** : 1re interpénétration à **166°** (`Claw_01/02`) et **147°** (`Claw_03`) |
| `TEXCOORD_0` dans le `.glb` produit | **22/22 primitives**, vérifié par relecture du binaire, le build échoue s'il en manque une |

**Verdict : l'articulation sert.** Elle n'est pas décorative, et elle ne l'est pas par accident —
la géométrie a été choisie *pour* ça (§4). Si le chiffre était tombé sous 12 %, il aurait fallu
retirer le mécanisme ; il ne l'est dans aucune des deux orientations de jeu.

**Valeur à écrire dans la Resource : `open_angle_deg = 51`.** Ce n'est pas une butée mécanique,
c'est le **maximum d'enveloppe** : au-delà, la silhouette *redescend* (§5).

## 3. Contrat et mesures

| Critère | Exigé | Mesuré | |
|---|---|---|---|
| Largeur X | 0,70 m ±3 % | **0,7011 m** (+0,16 %) | ✅ |
| Longueur Z | 0,85 m ±3 % | **0,8504 m** (+0,05 %) | ✅ |
| Hauteur Y | ≤ 0,34 m | **0,3206 m** (94 % du plafond ; 37,7 % de la longueur) | ✅ |
| Centrage du pivot | ±20 mm en X/Z | (+0,0000 ; −0,0083 ; −0,0002) | ✅ |
| Triangles | ≤ 4 000 | **3 888** (marge 2,8 %) | ✅ |
| Sommets | — | 5 940 | |
| UV | 100 % des primitives | **22/22 `TEXCOORD_0`**, 22/22 `TANGENT` | ✅ |
| Déterminisme | 2 exports identiques | `build-hull.sh --check leech_drone` → OK | ✅ |
| `Muzzle_C` | avant, sur l'axe, entre les pinces | (0 ; +0,0170 ; −0,3140) | ✅ |
| `Engine_C` | **obligatoire** | (0 ; +0,0700 ; +0,2760) | ✅ |
| Pièces mobiles | 3 `Claw_NN` | `Claw_01/02/03` | ✅ |
| Kit partagé | non modifié | `aegis_kit.py` intact (`git status` propre dessus) | ✅ |

⚠️ **La bbox du contrat est celle de la pose FERMÉE.** Ouverte à 51°, l'enveloppe hors-tout vaut
environ **0,84 × 1,01 m**. C'est voulu — c'est même tout l'objet du brief — mais si une hitbox
devait suivre l'ouverture, c'est ce chiffre-là qu'elle suit, pas 0,70 × 0,85.

## 4. La leçon de BRIEF-0042, et pourquoi cette coque ne la repaie pas

### 4.1 Le mécanisme du défaut, démonté

Sur la Choir Mine, six plaques pivotaient parfaitement et l'ouverture était invisible. Le rapport
d'origine l'attribue à l'enveloppe qui appartenait à la couronne. C'est vrai, mais **il y a une
cause plus profonde, et elle est générale à toute pièce animée par `EnemyPose`** :

`EnemyPose._hinge_axis` rend la tangente horizontale au rayon, `axe = (−r.z, 0, r.x)`. On vérifie
analytiquement que `axe × radial = +Y` : **un angle positif emmène le rayon vers le haut**. Une
pièce qui pointe déjà vers l'extérieur voit donc son rayon multiplié par `cos(angle)` — *elle
rentre*. Le pivot ne peut pas faire grossir une silhouette dans ce sens. Jamais.

### 4.2 La conséquence, appliquée ici

Pour qu'une rotation **agrandisse** l'enveloppe, la pièce doit pointer vers le **bas** au repos et
se relever. D'où la posture de cette coque : **au repos les trois pinces pendent sous le plan de
jeu, à 51° sous l'horizontale, doigts crochus** — un prédateur replié ; **ouvertes, elles se
déplient à l'horizontale** et le rayon des bouts de doigt passe de 0,535 à 0,645 m.

Le gain est calculable, donc **choisi et non subi** :

```
gain = hypot(e, h) − e          angle optimal = atan(h / e)
e = débord radial du bout de doigt au-delà de la charnière
h = plongée du bout de doigt sous la charnière
```

| Pince | charnière (rayon, z) | `e` | `h` | gain de rayon | en % du rayon |
|---|---|---|---|---|---|
| `Claw_01` / `Claw_02` (avant) | 0,350 m / +0,062 | 0,1846 m | 0,2280 m | **108,7 mm** | +20,3 % |
| `Claw_03` (arrière) | 0,300 m / −0,005 | 0,1250 m | 0,1544 m | **73,6 mm** | +17,3 % |

`h` est ce que la **hauteur** achète : les 41 mm de plafond encore libres à mi-brief ont été
dépensés là, et ils font passer la croissance de +19,5/+13,4 % à +22,9/+16,2 %. C'est le seul
levier, et il est borné par le plafond de 0,34 m.

### 4.3 « Rien ne doit les déborder » — la vérification, à chaque build

Le script **refuse d'exporter** si, à un angle quelconque du balayage, le rayon XZ maximal de la
coque **fixe** atteint celui des pinces :

| pose | rayon XZ, coque fixe (corps + bras + nacelle + museau) | rayon XZ, pinces |
|---|---|---|
| fermée (0°) | 0,3177 m | **0,5346 m** |
| 51° | 0,3177 m | **0,6450 m** |

Les pinces dépassent la coque fixe de **68 %** au repos et de **103 %** ouvertes. **Les quatre
extrêmes de la bounding box sont des bouts de doigt** — c'est ce qui a dicté la disposition (§6).

## 5. Débattement mécanique, pince par pince

Mesuré sur le **maillage livré**, par pas de 1°, en BVH triangle-à-triangle **dans les deux sens**,
contre la coque fixe **et** contre les deux voisines, avec la convention exacte de `EnemyPose`
(origine sur la charnière, `Basis(axe, angle)`, même angle pour les trois).

| Pièce | pivot (X, Y, Z) Godot | axe | 1re interpénétration | obstacle | marge repos | marge 51° | marge 85° |
|---|---|---|---|---|---|---|---|
| `Claw_01` (bâbord avant) | (−0,2183 ; +0,0620 ; −0,2736) | (+0,7817 ; 0 ; −0,6236) | **166°** | coque fixe (bras/corps) | 56,8 mm | 79,4 mm | 57,7 mm |
| `Claw_02` (tribord avant) | (+0,2183 ; +0,0620 ; −0,2736) | (+0,7817 ; 0 ; +0,6236) | **166°** | coque fixe (bras/corps) | 56,8 mm | 79,4 mm | 57,7 mm |
| `Claw_03` (arrière) | (0,0000 ; −0,0050 ; +0,3000) | (−1,0000 ; 0 ; 0) | **147°** | coque fixe (bras/corps) | 65,2 mm | 57,7 mm | 40,3 mm |

- **Dernière valeur sûre, mécaniquement : 146°** (la plus contrainte des trois, moins un pas).
  C'est **61° au-delà** du plafond du code (`EnemyPose.MAX_OPEN_DEG = 85`). Autrement dit :
  **il n'y a pas de butée à respecter ici**, contrairement à la Choir Mine (57°) et au Null Maw
  (57,5°). Ce qui limite l'ouverture n'est pas la mécanique, c'est la lecture.
- **Les pinces ne se touchent jamais** entre elles, à aucun angle : elles sont à 77° et 141°
  d'azimut l'une de l'autre et chacune tourne dans son propre plan vertical.
- Cette absence de butée n'est pas un hasard : la douille de poignet est une **surface de
  révolution autour de l'axe de charnière**, donc une rotation conserve sa distance à la chape.
  L'articulation est mécaniquement exacte, pas approchée.
- Le rayon d'exclusion de charnière (`HINGE_SKIP = 60 mm`) n'est pas réglé à vue : le script
  mesure ce qu'il ampute réellement (59,1 mm de pièce et 58,2 mm de coque autour du pivot) et
  l'imprime. Une rotation autour du pivot conserve la distance au pivot : ce qui est écarté est
  exactement ce qui ne peut, par construction, rencontrer autre chose.

### La courbe d'enveloppe — et son maximum

Diamètre apparent de la silhouette projetée (plus grande distance entre deux points), à la
**géométrie perspective réelle du jeu** : caméra de `scenes/gameplay/graybox.tscn`, position
(0 ; 14 ; 5), axe de visée à 70° sous l'horizontale, fov 62°, 1080 p ⇒ **14,87 unités** et
**60,45 px par unité**. Cadrage figé sur l'état fermé.

| ouverture | nez opposé au joueur | nez **vers** le joueur | rayon XZ des pinces |
|---|---|---|---|
| 0° (repos) | 51,62 px | 52,66 px | 0,5346 m |
| 10° | +6,8 % | +5,3 % | 0,5718 m |
| 20° | **+12,7 %** | +9,9 % | 0,6022 m |
| 30° | +17,5 % | **+13,3 %** | 0,6249 m |
| 40° | +20,9 % | +15,5 % | 0,6393 m |
| **51°** | **+22,9 %** (63,44 px) | **+16,2 %** (61,16 px) | **0,6450 m** |
| 60° | +23,2 % | +15,3 % | 0,6416 m |
| 70° | +22,0 % | +12,9 % | 0,6294 m |

⚠️ **La courbe a un maximum et redescend.** 51° est ce maximum par construction (`atan(h/e)`) ;
à 70° on a déjà reperdu 3 points. Une donnée de jeu réglée « au plus haut possible » serait donc
*moins* lisible qu'à 51°. Même remarque que pour le Null Maw : la butée mécanique n'est pas une
cible esthétique — ici elle est à 146° et ne veut plus rien dire.

### Le coulissement radial : mesuré, mais non recommandé

`EnemyPose` peut ajouter un glissement le long du rayon. Il n'y a **aucune butée mécanique** (les
pinces s'éloignent de tout), et il paie très bien :

| `open_spread` | diamètre | croissance | jour ouvert à la charnière |
|---|---|---|---|
| 0,00 | 63,44 px | +22,9 % | 0 mm |
| 0,15 | 68,72 px | +33,1 % | **52,5 mm** |
| 0,30 | 74,00 px | +43,4 % | 105,0 mm |
| 0,50 | 81,04 px | +57,0 % | 175,0 mm |

**Recommandation : `open_spread = 0`.** Contrairement à la Choir Mine — dont les plaques
survolaient une couronne et pouvaient glisser sans rien montrer — la pince est ici **emboîtée dans
la chape de son bras** : coulisser ouvre un jour visible de 52 mm dès 0,15, soit un poignet
déboîté. La rotation seule suffit largement au seuil demandé. Si la session veut malgré tout du
coulissement, 0,10 (35 mm) est le maximum avant que le jour ne se lise à 46 px.

## 6. Le seul écart au brief, et pourquoi

**La planche montre un triskèle (une pince devant, deux derrière). J'ai tourné la triade de 180° :
deux pinces devant, à ±38,6° du nez, une derrière sur l'axe.** Ce n'est pas une préférence, c'est
une contrainte arithmétique :

- la coque est **21 % plus longue que large** (0,70 × 0,85) ;
- des pinces à 120° placent les deux arrière à `y = +0,5 R` : pour tenir 0,850 m de long avec
  0,700 m de large, il aurait fallu **soit** élargir à 0,85 m (hors contrat), **soit** laisser la
  queue et la nacelle dépasser les pinces arrière de 22 cm — c'est-à-dire **exactement le défaut
  de BRIEF-0042** : une enveloppe qui n'appartient pas à la pièce animée ;
- le brief demande par ailleurs *« trois pinces courtes ouvertes vers l'avant »* et *« on doit voir
  ce qu'elle veut faire avant qu'elle le fasse »* : les deux grosses pinces doivent mener ;
- et `Muzzle_C` est spécifié *« à l'avant, sur l'axe, **entre les pinces** »* — une formulation qui
  suppose deux pinces encadrant l'axe, pas une pince posée dessus.

Ce que la planche apporte est conservé : trois pinces réparties autour de l'axe, symétrie
bilatérale, corps globulaire à panneautage radial, noyau dorsal, vérins ivoire dans les bras,
doigts recourbés. La troisième pince devient l'**ancre postérieure** — une vraie sangsue en a une —
et c'est elle qui donne à la coque son avant et son arrière.

## 7. Ce que la coque raconte, et où va le détail

- **Elle vient, elle n'attend pas.** Museau-ventouse ivoire à l'avant (`Muzzle_C`), nacelle
  dorsale magenta à l'arrière (`Engine_C`) : le couple donne un sens de marche à un corps presque
  sphérique. Les deux mines n'ont ni l'un ni l'autre.
- **Elle est fragile, et ça se voit d'abord.** 0,70 × 0,85 m contre 1,15 (Choir Mine), 1,45
  (Null Maw), 1,90 (Needle Scout) : **la plus petite coque du bestiaire**. En jeu elle mesure
  **44 à 52 px** selon sa position dans le plan (60,45 px/unité à l'origine, 52,07 à la ligne
  d'apparition) — la valeur de 46 px demandée par le brief est représentative de sa moitié haute.
- **Détail sur le dessus uniquement** (caméra à 20° de la verticale, BRIEF-0026 / ADR-0011) :
  calotte à 18 panneaux radiaux enfoncés, six bossages irréguliers à l'équateur, gradins du noyau,
  dos des bras et des paumes. Les dessous sont en `AA_Greeble` nu.

### Répartition des matériaux, en **aire réellement vue**

Rasterisation avec z-buffer depuis la caméra de jeu : ce qui est occulté ne compte pas
(compter l'aire des triangles surestimerait tout le dessous des doigts).

> ⚠️ **LES POURCENTAGES CI-DESSOUS SONT FAUX** — relevé le 2026-08-25, pendant `BRIEF-0046`.
> Le rastériseur « aire vue » de ce harnais n'employait pas de vraies coordonnées barycentriques
> (`w0 = 1 + u.x·(AC.y − AB.y)/det` : `u.y` n'y figure pas). Il rejetait donc le centre de gravité
> d'un triangle sur deux, et **amputait des pixels** — 40 % de ceux d'une lentille sur la coque
> suivante. **Le maillage, lui, n'est pas en cause** : seule la mesure l'est. Les autres chiffres
> de ce rapport (dimensions, triangles, débattements) sont indépendants de ce code et restent
> valables.
>
> Le correctif est écrit et démontré dans `tools/blender/build_shield_carrier.py` ; il n'a **pas**
> été porté ici — la coque devrait être remesurée pour que ce tableau redevienne vrai.


| Matériau | part de l'aire vue | rôle |
|---|---|---|
| `AA_Greeble` | 42,6 % | dessous, poignets, chapes, creux — jamais vu de face |
| `AA_Hull` | 19,9 % | ventre blindé, listels entre panneaux |
| `AA_Panel` | 18,2 % | les 18 panneaux violets de la calotte, dos des bras et des paumes |
| `AA_Trim` | 10,1 % | vérins des bras, museau, griffes, filet du noyau |
| `AA_Emissive_Engine` | **4,79 %** | lentille dorsale Ø 120 mm, 3 veines, 3 cernes de paume, lèvre de tuyère |
| `AA_Marking_Red` (vert maladif) | 3,0 % | deux nodules de tailles différentes, à 18° et 163° |
| `AA_Glass` | 1,4 % | membrane sombre autour de la lentille, bouche du museau |

**L'émissif est un accent, pas une livrée : 4,79 % pour un seuil de 10 %.** Il est concentré : la
lentille dorsale porte l'essentiel — c'est elle que le jeu fera respirer — et les trois cernes de
paume marquent les extrémités. Ces cernes ne coûtent **aucun triangle** (ce sont les faces de
bordure que l'inset crée de toute façon) et ce sont eux qui, vus du dessus, disent « ici il y a une
main » quand les doigts sont raccourcis par la perspective.

## 8. Deux défauts silencieux trouvés en cours de route

### 8.1 Les UV — le décompte réel est de **trois** coques, pas deux

Audit de tout `assets/imported/models/`, en relisant les binaires :

| Coque | primitives | `TEXCOORD_0` | |
|---|---|---|---|
| `leech_drone.glb` | 22 | **22** | ✅ |
| `specter_9`, `pale_leviathan`, `choir_mine`, `null_maw`, `aegis_citadel`, `citadel_beacon`, `citadel_turret` | — | toutes | ✅ |
| `needle_scout.glb` | 7 | **0** | ❌ |
| `crescent_interceptor.glb` | 7 | **0** | ❌ |
| **`choir_harvester.glb`** | 61 | **0** | ❌ *(non signalée jusqu'ici)* |

Le mini-boss est dans le même cas que les deux chasseurs : **aucune feuille de détail ADR-0011 ne
peut s'y poser**, et c'est la coque la plus grosse des trois. À reforger si le sujet est rouvert.

Sur cette coque, la garantie n'est pas une intention : `_assert_texcoords()` **relit le `.glb`
publié** et lève une `ContractError` si une seule primitive manque à l'appel.

### 8.2 `ak.inset_panel()` est un no-op **silencieux** si les normales ne sont pas à jour

`bmesh.ops.inset_region` calcule son décalage à partir de la normale de face. Sur un BMesh
fraîchement bâti par `bm.faces.new()` — donc par `bridge_rings`, `add_lathe`, ou tout `_sweep`
local — cette normale vaut **(0, 0, 0)** tant que personne ne l'a demandée. L'inset produit alors
quatre faces de bordure d'**aire nulle** (mesuré : `0,000000 m²` sans `normal_update()`,
`0,000714 m²` avec), que le `remove_doubles` de `ak.cleanup()` ressoude au passage suivant.

Résultat : le panneau n'est ni enfoncé ni cerné, il ne reste que le changement de matériau — et
**rien ne le dit** : ni le nombre de triangles final, ni le contrat, ni le rendu (un panneau plat
de la bonne couleur ressemble beaucoup à un panneau enfoncé de 5 mm). Découvert ici parce que trois
faces magenta *disparaissaient* du décompte par matériau entre la construction et l'export.

Corrigé **à l'appel** (`_inset()` dans le script de coque), le kit n'étant pas modifiable dans ce
brief. **Suggestion pour la session principale : la place juste de ce `bm.normal_update()` est dans
`aegis_kit.inset_panel()` lui-même** — une ligne, aucune régression possible, et toutes les coques
déjà livrées y gagneraient les panneaux qu'elles croient avoir. À vérifier en priorité sur
`build_choir_mine.py`, `build_null_maw.py` et `build_specter_9.py`, dont les insets suivent
immédiatement une construction par `bridge_rings`.

## 9. Distinction des autres familles

`BRIEF-0044-silhouette-comparee.png` — aplats noirs, même champ (2,05 m) et même perspective, avec
une rangée à l'échelle réelle du jeu :

| | silhouette |
|---|---|
| **Leech Drone** | trépied **ajouré** et minuscule : un noyau compact et trois membres séparés par deux grands vides |
| Needle Scout | dard plein, long et fin, une seule ligne |
| Choir Mine | disque plein à denture périphérique |
| Null Maw | couronne annulaire, centre percé |

Le Leech est le seul à ne pas être une masse pleine, et le seul dont l'aire allumée soit inférieure
à la moitié de sa bbox. À 46 px la confusion est impossible, y compris avec le Needle Scout, dont
la silhouette est deux fois plus longue et n'a aucun appendice latéral.

## 10. Limites connues

1. **La vignette « game » de la planche 4 vues montre la coque de dos.** `render-hull.py` place la
   caméra du côté du joueur avec le nez de la coque vers le haut de l'écran ; or la sangsue
   *poursuit* et fait donc face au joueur. Dans l'orientation réelle, les pinces avant se lisent
   comme la pince arrière se lit sur la planche — c'est la vignette trois-quarts qui le montre.
   C'est aussi pourquoi tous les chiffres de croissance sont donnés **dans les deux orientations**.
2. **La croissance est moindre nez-vers-le-joueur** (+16,2 % contre +22,9 %) : dans cette
   orientation les deux grosses pinces sont du côté proche de la caméra, et leur remontée les
   déplace vers le bas de l'écran au lieu de vers le haut. C'est le chiffre à retenir pour arbitrer,
   pas l'autre.
3. **L'enveloppe ouverte (0,84 × 1,01 m) sort du contrat de bbox.** C'est le but, mais une hitbox
   fixe réglée sur 0,70 × 0,85 laissera les pinces ouvertes « traverser » le joueur sans contact.
4. **La plume de `Engine_C` survole `Claw_03`.** La tuyère est dorsale (z = +0,070) et l'ancre
   arrière plonge sous le plan : à la caméra de jeu, la plume passe visuellement au-dessus de la
   pince, 232 mm plus haut que son bout de doigt. Ça ne traverse rien, mais si la plume est large,
   elle masquera partiellement l'ancre.
5. **`AA_Trim` occupe 10,1 % de l'aire vue** — beaucoup d'ivoire pour une faction sombre. C'est un
   choix (les vérins clairs sont la signature de la planche et ils marquent les bras à 46 px), mais
   c'est le premier réglage à baisser si la session trouve la coque trop claire en essaim.
6. **Marge de triangles très mince : 2,8 %** (3 888 / 4 000). Toute retouche de détail passera par
   une coupe ailleurs. Le budget d'ADR-0011 pour un ennemi léger est 12 000 ; le 4 000 du brief est
   un choix d'essaim, pas une limite technique.
7. Les harnais de rendu des planches de poses et de silhouettes vivent dans le **bac à sable** : le
   brief n'ouvre `tools/` que pour `build_leech_drone.py`. Les mesures, elles, sont dans le script
   de coque et **rejouées à chaque build**.

## 11. Reproduire

```bash
blender45 -t 1 -b -P tools/blender/build_leech_drone.py     # + les 3 harnais de mesure
./scripts/build-hull.sh --check leech_drone                  # déterminisme (2 exports, sha256)
blender45 -b -P tools/render-hull.py -- assets/imported/models/ships/leech_drone.glb
```

Le script échoue bruyamment — et n'écrit rien — si la bbox, le budget, les matériaux, les points
d'attache, l'orientation, le débattement (< 51°), la croissance d'enveloppe (< 12 %), la propriété
« les pinces portent l'enveloppe » ou les UV sortent du contrat.
