# BRIEF-0083 — L'iris à volets coulissants du Pale Leviathan : compte-rendu

*Mesuré le 2026-08-25. **Verdict : LIVRÉ, avec une réserve chiffrée qui n'appartient pas à cette
pièce.** Les six volets existent, coulissent sans jamais pivoter, tiennent tous les seuils — mais le
trou que le joueur **voit** n'est pas commandé par l'iris : il est borné à 3,499 m par de la
géométrie de `Body` et par le noyau, deux pièces hors du périmètre de ce brief. §7.*

| | valeur mesurée | seuil | marge |
|---|---|---|---|
| passage libre laissé par **l'iris**, ouvert | **4,378 m** | ≥ 4,200 m (cible corrigée) | +89 mm |
| — en largeurs de Specter-9 (1,752 m) | **2,50 ×** | ≥ 2,4 × | |
| passage libre, iris fermé | 3,207 m | — | l'iris gagne **+1 170 mm** |
| delta de triangles sur la coque entière | **+2 366** | ≤ +2 500 | 134 |
| couverture UV | **35 / 35 maillages** (`TEXCOORD_0` + `TANGENT`) | 100 % | — |
| contrat de noms du reste de la coque | **26 maillages bit à bit identiques** | intact | — |
| bounding box | 11,0286 × 3,1620 × 13,9972 m | inchangée au micron | — |
| pivot de coque | (−0,0127 ; +0,0110 ; −0,0014) | inchangé | ±0,020 |

**Coque livrée** : `assets/imported/models/bosses/pale_leviathan.glb`, 2 467 340 o,
sha256 `8c8112a8723a118dfe47de0d2ccf13f83eac6a66d0b32c73bb1122841190bad2`
(la coque du dépôt valait `1bfdf51b9145330ef66c76362b00814c868797b91cc53683921bbecfbb9eb07e`).
Déterminisme vérifié : `./scripts/build-hull.sh --check pale_leviathan` → *déterminisme OK*, deux
exécutions byte-identiques, `-t 1` forcé.

---

## 0. La correction de largeur du chasseur, vérifiée de mon côté

La cible de passage est passée de 3,0 à 4,2 m en cours de route. J'ai **re-mesuré le Specter-9
moi-même**, sur le `.glb` livré, en composant les transformations de nœuds :

| | X | Y | Z |
|---|---|---|---|
| agrégat des `min`/`max` d'accesseurs, **espace local** | **1,294** | 0,647 | 2,415 |
| composition des nœuds, **espace monde** | **1,752** | 0,647 | 2,460 |

La correction est exacte, et l'écart vient bien des ailes : elles sont portées par des nœuds
transformés, que l'agrégat local ignore. L'iris livré laisse **2,50 largeurs de chasseur**, la cible
en demandait 2,4. Le seuil est **codé en dur dans le harnais** (`IRIS_BORE_MIN = 2.10`, avec sa
justification) : il sera remesuré à chaque build, il ne dépendra pas de ce rapport.

---

## 1. Les six pivots, dans les DEUX repères

Chaîne d'axes (elle est vérifiée analytiquement par `aegis_kit._assert_axis_chain()` à chaque
export) : **auteur** `(x, y, z)` → **fichier** `(−x, z, y)` → **jeu** `(x, z, −y)`, la seconde flèche
étant `FACING_PLAYER = Vector3(0, PI, 0)` qu'applique `boss_controller.gd:94`.

Un volet est posé sur sa bissectrice, **sous la nappe, à mi-glissière** — c'est le patin. Rayon
1,860 m, altitude 0,980 m (le dessous du profil au rayon 1,86).

### Position absolue du pivot

| Pièce | azimut auteur | **repère FICHIER** (X, Y, Z) | **repère JEU** (X, Y, Z) |
|---|---|---|---|
| `Shutter_01` | 30° | (**−1,6108** ; +0,980 ; **+0,9300**) | (**+1,6108** ; +0,980 ; **−0,9300**) |
| `Shutter_02` | 90° | (+0,0000 ; +0,980 ; **+1,8600**) | (+0,0000 ; +0,980 ; **−1,8600**) |
| `Shutter_03` | 150° | (**+1,6108** ; +0,980 ; **+0,9300**) | (**−1,6108** ; +0,980 ; **−0,9300**) |
| `Shutter_04` | 210° | (**+1,6108** ; +0,980 ; **−0,9300**) | (**−1,6108** ; +0,980 ; **+0,9300**) |
| `Shutter_05` | 270° | (+0,0000 ; +0,980 ; **−1,8600**) | (+0,0000 ; +0,980 ; **+1,8600**) |
| `Shutter_06` | 330° | (**−1,6108** ; +0,980 ; **−0,9300**) | (**+1,6108** ; +0,980 ; **+0,9300**) |

### Ce que Godot lira dans le nœud glTF

Les six volets sont enfants de `Core` : le `.glb` porte la position **relative**, soit le tableau
ci-dessus moins la position de `Core` (0 ; +0,400 ; 0). Relevé sur le fichier livré :

```
Shutter_01  pos = (-1.6108, 0.58,  0.93)      Shutter_04  pos = ( 1.6108, 0.58, -0.93)
Shutter_02  pos = ( 0.0000, 0.58,  1.86)      Shutter_05  pos = ( 0.0000, 0.58, -1.86)
Shutter_03  pos = ( 1.6108, 0.58,  0.93)      Shutter_06  pos = (-1.6108, 0.58, -0.93)
```

### Azimuts dans le plan de jeu

`gameplay_plane.gd` pose `x = X`, `y = −Z`. Dans cette convention l'azimut du **fichier** vaut
l'azimut d'auteur − 180°, et l'azimut **en jeu** vaut exactement l'azimut d'auteur :

| Pièce | plan de jeu, **fichier** | plan de jeu, **en jeu** |
|---|---|---|
| `Shutter_01` | −150,0° | **+30,0°** |
| `Shutter_02` | −90,0° | **+90,0°** |
| `Shutter_03` | −30,0° | **+150,0°** |
| `Shutter_04` | +30,0° | **−150,0°** |
| `Shutter_05` | +90,0° | **−90,0°** |
| `Shutter_06` | +150,0° | **−30,0°** |

Le joueur est à **−90°** dans ce plan : c'est donc **`Shutter_05` qui lui fait face**, et c'est aussi
le volet posé sur la face menaçante de la coque (azimut d'auteur 270°, l'étrave). Le calage n'est pas
libre — les bornes de volet tombent à 0/60/…/300° pour que les trois nœuds gravitiques (58, 92 et
124°) atterrissent sur **trois volets différents** ; à 30/90 près, deux se retrouvaient sur le même.

### La direction de coulissement se lit dans la position du nœud

Parce que le pivot est sur la bissectrice, `normalize(Vector3(pos.x, 0, pos.z))` **rend exactement la
direction de glissement, dans les deux repères** (une rotation de 180° autour de Y laisse une
bissectrice sur elle-même). Le code n'a aucune donnée supplémentaire à transporter — c'est le procédé
de `harvester_combat._bind_iris()`. Ce que le code doit écrire, et rien d'autre :

```gdscript
var dir := Vector3(shutter.position.x, 0.0, shutter.position.z).normalized()
shutter.position = rest + Vector3(0.0, -sink, 0.0) + dir * slide
```

---

## 2. Le geste : deux translations, aucune rotation — et pourquoi l'ordre est une mesure

| | valeur | ce qui la borne |
|---|---|---|
| **recul** (−Z auteur = **−Y en jeu**, donc LOIN de la caméra) | **1 500 mm** | les nœuds gravitiques ne sortent de la piste de `Shell_Ring` qu'au-delà de **1 290 mm** (marge 20 mm à 1 300, **215** à 1 500) |
| **glissement** (radial sortant, dans le plan de la lèvre) | **600 mm** | à fond de course le volet doit tenir dans le volume creux du pont, sous le plafond de piste |
| genou (`IRIS_KNEE`) | **0,70** | voir ci-dessous |

**Le décalage des deux temps n'est pas un choix de style, c'est une mesure.** Le glissement est
*impossible* tant que le volet n'est pas descendu sous la coquille. Relevé au balayage :

| glissement amorcé à… | marge volet ↔ coquille | verdict |
|---|---|---|
| recul 0 mm, glissement 300 mm | **0,0 mm** | ❌ le volet entre dans `Shell_Crescent` |
| recul 200 mm, glissement 300 mm | **0,0 mm** | ❌ |
| recul 600 mm, glissement 300 mm | **0,0 mm** | ❌ |
| recul 1 040 mm, glissement 300 mm | 185,6 mm (volet) / **0,0 mm** (nœud) | ❌ le nœud entre dans `Shell_Ring` |
| **recul 1 500 mm, glissement 600 mm** | **630,6 mm** (volet) / **260,0 mm** (nœud) | ✅ |

`Shell_Crescent` commence à r = 2,240 entre z 0,750 et 1,156 ; `Shell_Ring` à r = 2,179 entre 0,280
et 0,678 (relevés sur le `.glb`, pas sur les tables du script). À eux deux ils bouchent tout ce qui
dépasse r = 2,18 **sur toute la hauteur du volet**. D'où : reculer d'abord, glisser ensuite.

**Aucun pivot, nulle part.** Les six pièces sont animées par des `Matrix.Translation` pures — dans le
script, dans le harnais de dégagement, et dans le snippet donné au code. C'est ce qui les sépare des
`Petal_01..N` du Choir Harvester, qui basculent vers l'extérieur autour d'un axe tangentiel. Le
volet, lui, s'**enfonce à l'opposé de la caméra** puis s'efface : à aucun instant de la course une
face ne se relève vers le joueur.

### Le harnais mesure maintenant l'iris contre la coquille

Le tableau de dégagement n'avait **jamais** mesuré une pièce de gueule contre la coquille — ni
`Maw_Lip`, ni les nœuds. C'est cette mesure manquante qui aurait laissé passer un glissement amorcé
trop tôt : bounding box parfaite, contrat de noms parfait, et la coquille traversant l'iris à chaque
orbite. La ligne existe désormais et **bloque l'export** (`Shutter_01..06 + Node_01..03 / coquille`,
course complète × 12 phases d'orbite ; ⚠️ pas de 30° et non 60°, sinon la symétrie d'ordre 6 de
l'iris ramènerait le balayage sur lui-même).

---

## 3. Fermé, la silhouette est celle d'aujourd'hui

`IRIS_PROFILE` **est** `LIP_PROFILE`, table pour table : rayons 2,06 → 1,66, z 0,84 → 1,19,
épaisseur 0,14, tranche interne émissive. Là où la lèvre était, l'iris est la même matière au
millimètre ; il l'étend simplement de 96° à 360°.

| | `Maw_Lip` (dépôt) | iris fermé (livré) |
|---|---|---|
| bande radiale | 1,66 → 2,06 m | **identique** |
| altitude du dessus | 0,84 → 1,19 m | **identique** |
| épaisseur de nappe | 0,14 m | **identique** |
| secteur couvert | 96° (arrière seul) | **360°**, en six secteurs de 59,4° |
| hauteur de coque | 3,1620 m | **3,1620 m**, au micron |
| marge la plus proche de la coque | 75,9 mm | **75,8 mm** |

**Ce qui change, et c'est le seul écart de silhouette assumé** : l'anneau 1,66 → 2,06 m, aujourd'hui
couvert par la lèvre uniquement sur le secteur arrière, l'est désormais **tout autour**. Vignettes 1
et 2 de la planche, même cadrage, même caméra de jeu : la lecture d'ensemble ne bouge pas, le collier
se referme sur les 264° qui étaient ouverts. C'était inévitable — six volets à 60° couvrent 360° par
définition — et c'est le sens même de « ouverture au repos = fermée ».

Les six coutures font **0,30° de jeu chacune**, soit 8,7 mm au rayon interne et 10,8 au rayon
externe. Le jeu n'est pas décoratif : le harnais exige une marge **strictement positive** entre deux
pièces mobiles, et des volets jointifs au sens propre rendraient 0,0 mm et bloqueraient l'export. Le
chanfrein de 5 mm creuse cette couture exactement comme les joints de tuile du reste de la coque —
mesure entre voisins : **17,4 mm**.

---

## 4. Le contrat de noms, vérifié maillage par maillage

Hachage par maillage (positions, normales, UV, tangentes, indices, matériau, translation du nœud),
coque du dépôt contre coque livrée :

| | maillages |
|---|---|
| **identiques bit à bit (26)** | `Body`, `Core`, `Heart`, `Plate_01`, `Plate_02`, `Plate_03`, `Plate_04`, `Ring_01`, `Ring_02`, `Ring_03`, `Ring_04`, `Ring_05`, `Shell_Crescent`, `Shell_Ring`, `Spike_01`, `Spike_01_Mid`, `Spike_01_Tip`, `Spike_02`, `Spike_02_Mid`, `Spike_02_Tip`, `Spike_03`, `Spike_03_Mid`, `Spike_03_Tip`, `Spike_04`, `Spike_04_Mid`, `Spike_04_Tip` |
| **modifiés (3)** | `Node_01`, `Node_02`, `Node_03` — déplacés de 5 cm, §5 |
| **disparu (1)** | `Maw_Lip` |
| **nouveaux (6)** | `Shutter_01` … `Shutter_06` |

### Hiérarchie complète du `.glb` livré (35 maillages, relevée sur le fichier)

```
Body               parent=(racine)      9844 tris
Core               parent=(racine)      1544 tris
Shell_Ring         parent=(racine)      1564 tris
Spike_01           parent=(racine)       424 tris
Spike_02           parent=(racine)       392 tris
Spike_03           parent=(racine)       356 tris
Spike_04           parent=(racine)       332 tris
  Heart            parent=Core           496 tris
  Ring_01          parent=Core           752 tris
  Ring_02          parent=Core           752 tris
  Ring_03          parent=Core           752 tris
  Ring_04          parent=Core           752 tris
  Ring_05          parent=Core           752 tris
  Shutter_01       parent=Core           512 tris     <- NOUVEAU
  Shutter_02       parent=Core           512 tris     <- NOUVEAU
  Shutter_03       parent=Core           512 tris     <- NOUVEAU
  Shutter_04       parent=Core           512 tris     <- NOUVEAU
  Shutter_05       parent=Core           512 tris     <- NOUVEAU
  Shutter_06       parent=Core           512 tris     <- NOUVEAU
    Node_01        parent=Shutter_01     192 tris     <- PARENT CHANGE (etait Maw_Lip)
    Node_02        parent=Shutter_02     192 tris     <- PARENT CHANGE
    Node_03        parent=Shutter_03     192 tris     <- PARENT CHANGE
  Shell_Crescent   parent=Shell_Ring    1952 tris
    Plate_01       parent=Shell_Crescent 472 tris
    Plate_02       parent=Shell_Crescent 472 tris
    Plate_03       parent=Shell_Crescent 588 tris
    Plate_04       parent=Shell_Crescent 472 tris
  Spike_01_Mid     parent=Spike_01       524 tris
    Spike_01_Tip   parent=Spike_01_Mid   462 tris
  Spike_02_Mid     parent=Spike_02       534 tris
    Spike_02_Tip   parent=Spike_02_Mid   480 tris
  Spike_03_Mid     parent=Spike_03       498 tris
    Spike_03_Tip   parent=Spike_03_Mid   436 tris
  Spike_04_Mid     parent=Spike_04       482 tris
    Spike_04_Tip   parent=Spike_04_Mid   390 tris
```

Les 14 points d'attache sont tous présents et **inchangés au millimètre** : `Core_Center`,
`Maw_Center`, `Tunnel_End`, `Muzzle_C/L/R`, `Muzzle_Plate_01..04`, `Muzzle_Spike_01..04`.

⚠️ **Les deux seules ruptures de contrat, et elles sont assumées** : `Maw_Lip` disparaît (c'est
l'objet du brief ; la pièce n'était référencée nulle part dans `scripts/`, vérifié par `grep` sur
`scripts/ scenes/ resources/ tests/`), et `Node_01..03` changent de parent. Ce second point était
**forcé** : leur parent n'existe plus. Le volet qui les porte est le seul choix physique — laissés
enfants de `Core`, ils seraient restés suspendus au-dessus du vide une fois l'iris ouvert.

---

## 5. Les nœuds gravitiques : 5 cm, et la mesure qui les exige

`NODE_R` passe de 1,78 à **1,83** et `NODE_Z` de 1,15 à **1,134** (le nœud reste enfoncé de 4 mm dans
la nappe, comme avant). Ni la longueur, ni l'inclinaison, ni le débattement de −60° ne bougent.

Motif, mesuré : le repli couche le nœud vers l'**intérieur** — direction héritée d'une lèvre à
charnière arrière qui n'existe plus — et le volet l'emmène désormais 1,5 m plus bas, c'est-à-dire au
droit de l'**équateur du noyau** (rayon 1,555 m à l'altitude critique).

| `NODE_R` | marge nœud ↔ noyau | marge nœud ↔ `Shell_Ring` |
|---|---|---|
| 1,78 (dépôt) | **7,0 mm** ❌ | 78,2 mm |
| 1,86 | 84,0 mm | **27,4 mm** ❌ |
| **1,83 (livré)** | **56,1 mm** ✅ | **57,2 mm** ✅ |

Pour repère, la coque du dépôt donnait 97,2 mm sur la ligne « `Node_01..03` ». On perd 41 mm, et on
achète le droit d'enfoncer l'iris de 1,5 m.

---

## 6. Le tableau de dégagement complet, rejoué sur le maillage livré

Le build **refuse d'exporter** si une marge tombe à zéro. Les lignes de l'iris sont **mesurées sans
aucun rayon d'exclusion** : l'argument qui rend un `skip` licite est l'invariance par *rotation*
autour du pivot, et une translation ne conserve aucune distance. Les volets sont donc mesurés
entiers.

| Pièce / débattement | dépôt | **livrée** |
|---|---|---|
| `Shell_Ring` / coque, orbite 360° | 77,0 mm | **77,0 mm** |
| `Shell_Crescent` / coque | 241,3 mm | **241,3 mm** |
| `Plate_01..04` / coque, coquille, entre elles | 65,9 mm | **65,9 mm** |
| `Core` / coque, rotation 360° | 166,5 mm | **166,5 mm** |
| `Maw_Lip` / coque et noyau, 0 → 90° | 75,9 mm | *(pièce supprimée)* |
| **`Shutter_01..06` / coque, recul libre 100 mm** | — | **11,1 mm** ✅ |
| **`Shutter_01..06` / noyau, anneaux, volets voisins**, course complète | — | **17,4 mm** ✅ |
| **`Shutter_01..06` + `Node_01..03` / coquille**, course × orbite | *(jamais mesuré)* | **57,2 mm** ✅ |
| `Node_01..03` / volet, noyau, coque | 97,2 mm | **56,1 mm** ⬊ (§5) |
| `Ring_01..05` / paroi du puits et entre eux | 63,6 mm | **63,6 mm** |
| `Spike_01..04` / coque, pointage ±40° | 190,3 mm | **190,3 mm** |
| `Spike_0X_Mid` et `_Tip`, flexion ±25° | 83,5 mm | **83,5 mm** |
| flexion VERTICALE encaissée sans morsure | ±5° | **±5°** |

### Ce que le volet traverse, et à partir de quand

⚠️ La ligne « recul libre 100 mm » ne dit pas que le volet reste hors de la coque sur toute sa
course — **il n'y reste pas, et c'est le geste demandé** (« reculent dans l'épaisseur de la coque »).
Mesure du contact réel, par pas de 2 cm :

- le volet dégage **entièrement** la coque jusqu'à **120 mm** d'enfoncement (marge 3,0 mm au dernier
  pas mesuré ; premier contact à 133 mm) ; ce qui l'arrête est la **denture fixe** de la lèvre du
  puits (`_build_rim_teeth`, crête à z = 0,65), pièce de `Body` que ce brief ne touche pas ;
- au-delà, son talon extérieur s'enfonce dans la lèvre : ce que l'œil lit est **le volet qui glisse
  sous l'anneau denté**, tandis que sa moitié interne continue de descendre à découvert dans la
  gueule ouverte, sur toute la course ;
- **à fond de course, le volet est entièrement dans le volume creux du pont** et **aucune de ses
  surfaces ne croise une surface de coque** : marge 253 mm. Il n'y a donc ni z-fighting ni
  interpénétration visible à l'arrivée — le volet est simplement avalé, et invisible.

Un piège rencontré en route, consigné dans le script parce qu'il se reproduira : le patin de
glissière était d'abord bâti avec `seg_box()`, dont `_align_y()` emploie la **rotation la plus
courte**. Sur une pente de 49° elle fait basculer la section de la boîte, et les coins bas
descendaient 5 cm plus bas que la ligne demandée — droit sur la denture fixe. Marge tombée à
**21,6 mm** au lieu de 75,8. Le patin est désormais un balayage de sections qui suit le profil.

---

## 7. ⚠️ RÉSERVE : le passage que l'iris laisse n'est pas le trou que le joueur voit

Mesure **indépendante**, faite sur le `.glb` livré sans Blender ni le script de coque (lecture
directe du chunk JSON, composition des translations de nœuds à la main, application de la course de
l'iris), du plus grand cylindre vertical centré sur l'axe du puits qui ne rencontre aucun triangle,
dans la fenêtre de plongée (au-dessus de y = −0,10) :

| Groupe de pièces | iris fermé | iris ouvert | dans le périmètre de ce brief ? |
|---|---|---|---|
| **iris** (`Shutter_01..06` + `Node_01..03`) | 3,207 m | **5,092 m** | ✅ oui |
| **coque** (`Body`) | 3,499 m | **3,499 m** | ❌ non |
| **coquille** (`Shell_*`, `Plate_*`) | 4,359 m | 4,359 m | ❌ non |
| **puits** (`Ring_01..05`, `Heart`) | 0,193 m | 0,193 m | ❌ non |
| **noyau** (`Core`) | 0,000 m | 0,000 m | ❌ non |

*(Le harnais du build publie 4,378 m pour l'iris ouvert plutôt que 5,092 : il prend le minimum sur
**tout** le corps du volet, y compris ce qui est descendu sous la fenêtre de plongée. C'est la mesure
conservatrice, c'est elle qui est opposée au seuil, et elle passe : 4,378 ≥ 4,200, marge 89 mm.)*

**Autrement dit** : la cible de 4,2 m est tenue **par l'iris**, avec 89 mm de marge sur la mesure
conservatrice et 892 mm sur la mesure de fenêtre. Mais trois pièces que ce brief n'a pas le droit de
toucher referment le trou avant lui :

1. **`Core`** — la boule de 3,12 m occupe l'axe. C'est le point n°1, et il est **déjà prévu** :
   l'en-tête du script de coque prescrit d'escamoter le noyau **par son maillage** (matériau,
   échelle) et jamais par la visibilité du nœud, puisque l'iris, les anneaux et le cœur en sont les
   enfants. La vignette 6 de la planche montre le résultat avec le noyau escamoté et le Specter-9 à
   l'échelle : **c'est cette image-là qui répond au verdict de playtest**, pas la vignette 5.

   ⚠️ **Et c'est exactement le piège qui est tendu aujourd'hui.** `leviathan_combat.gd:828` écrit
   `_heart_node.scale = ...`, et `_heart_node` **est le nœud `Core`** (ligne 392 : `find_child("Core")`).
   Le battement actuel (±12 %) est inoffensif parce qu'il est faible — mais il emmène déjà les cinq
   anneaux, le cœur, et désormais **les six volets** avec lui. Passer ce facteur à 0,10 pour
   escamoter la boule **escamoterait l'iris du même geste**, et le trou ne s'ouvrirait pas du tout.
   La transformation doit porter sur le **maillage** de `Core` (ses sommets, ou un shader), jamais
   sur le nœud. Ma planche le fait sur les sommets, précisément pour montrer le bon geste.
2. **`Body`** — la denture fixe de la lèvre du puits (l'ARMOR RING de la planche) mord jusqu'à
   r = 1,750, ce qui plafonne l'ouverture de coque à **3,499 m**, soit 2,00 largeurs de chasseur.
   Pour atteindre 4,2 m il faudrait reculer cette denture à r ≥ 2,10 **et** élargir la lèvre du puits
   (`DISC_R[0] = 1,90`, qui est aussi `SHAFT[0]` — les deux bougent ensemble ou le puits se décolle
   du pont). C'est une recoupe du pont et du puits : un autre brief, pas celui-ci.
3. **`Ring_01..05`** — ils pincent le passage à **0,193 m**. Ce n'est pas une conséquence de ce
   brief : c'est le défaut déjà relevé par `BRIEF-0082` (« les cinq anneaux sont trois fois plus
   petits que le vaisseau censé les traverser »). J'en ai trouvé **la cause exacte**, elle est
   gratuite à corriger, et je ne l'ai pas corrigée parce que le brief interdit de toucher aux
   `Ring_01..05` — §9, suggestion 1.

**Le maximum atteignable sans abîmer la coque, et je ne l'ai pas forcé** : l'iris à lui seul pourrait
dégager davantage (il suffit d'allonger le glissement), mais cela ne gagnerait **rien de visible**,
puisque `Body` referme à 3,499 m bien avant. Allonger le glissement ne ferait que consommer les
57 mm de marge à `Shell_Ring` pour un bénéfice nul. La course livrée est celle qui maximise les
marges à passage visible constant.

---

## 8. Budgets, matériaux, UV

| | dépôt | **livrée** | plafond |
|---|---|---|---|
| triangles | 27 756 | **30 122** | 40 000 (contrat) — **delta +2 366** pour ≤ +2 500 (brief) |
| sommets | 40 672 | **44 403** | |
| bbox (Godot X, Y, Z) | 11,0286 × 3,1620 × 13,9972 | **identique au micron** | 11,00 ±3 % / 3,20 / 14,00 ±3 % |
| pivot | (−0,0127 ; +0,0110 ; −0,0014) | **identique** | ±0,020 m |
| `AA_Hull` | 33,7 % | **31,9 %** | ≥ 30 % ✅ |
| `AA_Greeble` | 17,4 % | **19,2 %** | ≤ 20 % ✅ |
| `AA_Emissive_Engine` | 8,5 % | **8,5 %** | ≤ 8 % (écart connu, **strictement inchangé**) |
| UV + tangentes | 30/30 maillages | **35/35 maillages** | 100 % ✅ |

Les 2 366 triangles achètent 6 × 512. `IRIS_SEG` a été ramené de 8 à 7 segments par volet parce que
8 coûtait **46 triangles de trop** — la contrainte a mordu, elle est consignée dans le script.

Répartition d'un volet, matériau par matériau, et chaque ligne se justifie par la doctrine :
`AA_Trim` (ivoire) sur les deux bandes internes du dessus — la couronne qu'on voit ; `AA_Hull` sur
les deux bandes externes et le dos ; `AA_Greeble` sur le dessous, les deux flancs de secteur et le
patin ; `AA_Panel` sur la butée de fin de course ; **`AA_Emissive_Engine` sur la tranche interne
seule**.

⚠️ Cette tranche émissive est le vrai signal de l'ouverture, et c'est délibéré : la course est en
grande partie un **enfoncement**, donc peu lisible dans l'axe d'une caméra qui regarde de dessus. Au
repos les six arcs magenta dessinent un cercle continu autour de la boule ; dès que l'iris bouge, il
se casse en six morceaux qui s'éloignent. C'est ce qu'on lit sur les vignettes 3 → 4 → 5.

Aucun nouvel appel à `ak.inset_panel()` n'a été ajouté (le brief l'interdit : il est *no-op* sans
`normal_update()` préalable, et `build_pale_leviathan.py` en compte 10 sans le moindre appel — leurs
panneaux n'existent pas. **Ce défaut est intact, il n'a pas été corrigé ici.**)

---

## 9. Réserves, angles morts, et deux suggestions

1. **⚠️ La cause exacte des `Ring_01..05` à 19 cm, trouvée en passant.** `shaft_radius()` construit sa
   table par `[(-zz, rr) for zz, rr in reversed(SHAFT)]`, ce qui rend une liste d'abscisses
   **décroissantes** ; `lerp_table()` teste `x <= table[0][0]` et rend donc **toujours la borne**,
   jamais l'interpolation. `shaft_radius(-0.175)` vaut 0,32 au lieu de ~1,94, d'où
   `ring_radius(0) = 0.12`. C'est **exactement la même erreur** que celle que j'ai dû éviter pour
   `IRIS_PROFILE` (écrite en rayons décroissants, d'où la fonction `iris_top()` qui la retourne).
   Un caractère à changer, et les cinq anneaux reprennent leur taille — mais ils **pinceraient alors
   le passage à 2,99 m** (rayon interne 1,496), sous la cible de 4,2. Les deux décisions se tiennent
   et doivent être prises ensemble.
2. **La coque n'a pas été vue en jeu**, seulement en rendu Cycles à l'angle exact de la caméra de
   jeu (20° de la verticale). La règle du dépôt reste de confirmer en jeu (ADR-0006).
3. **`./scripts/check.sh` n'a pas été exécuté.** Aucun fichier moteur n'est touché par ce brief, et
   une autre forge travaille en parallèle sur `build_core_interior.py` : lancer la porte de qualité
   maintenant mesurerait son travail en cours. À passer à l'intégration, c'est là que le nouvel
   import du `.glb` sera vérifié.
4. **Le CSV de provenance n'a PAS été écrit** (consigne explicite : un seul écrivain). La ligne
   recalée est au §10.
5. **Suggestion — la chorégraphie que le code devrait écrire.** Le geste ne délivre son effet que si
   `Core` s'escamote *pendant* le recul. Proposition mesurée : sur `shell_open` de 0 → 0,70, enfoncer
   les volets de 0 → 1,50 m et faire fondre l'échelle du **maillage** de `Core` de 1,0 → ~0,10 ; sur
   0,70 → 1,00, glisser de 0 → 0,60 m (l'iris est alors sous la coquille, la manœuvre est
   invisible mais elle libère le champ pour le zoom de `BRIEF-0082`). C'est la seule séquence qui
   passe toutes les marges de §6.
6. **Suggestion — le harnais mesure encore l'iris contre une coquille au repos.** En jeu, la coquille
   s'est ouverte avant que l'iris ne bouge. La mesure livrée est donc **plus sévère que la réalité**,
   ce qui est le bon sens ; mais si un jour le combat ouvre l'iris coquille fermée, les 57 mm sont
   la seule chose qui sépare les deux pièces.

---

## 10. Fichiers, et la ligne de provenance à recaler

| Fichier | État |
|---|---|
| `tools/blender/build_pale_leviathan.py` | **modifié** — seul fichier de `tools/` touché |
| `assets/imported/models/bosses/pale_leviathan.glb` | **régénéré**, sha256 `8c8112a8…`, déterminisme vérifié |
| `docs/forge/output/BRIEF-0083-planche-quatre-vues.png` | **livrée** — 6 vignettes, sha256 `0af80c42…` |
| `docs/forge/output/BRIEF-0083-report.md` | ce rapport |
| `tools/blender/lib/aegis_kit.py` | **non touché** (gelé) |
| `tools/blender/build_core_interior.py` | **non touché** (autre forge) |
| `assets/licenses/ASSET_PROVENANCE.csv` | **non touché** (un seul écrivain — ligne ci-dessous) |
| `scripts/`, `scenes/`, `resources/`, `tests/`, `project.godot` | **non touchés** |

Lecture de la planche : **1** avant (`Maw_Lip` fermée, caméra de jeu) · **2** après (iris fermé, même
cadrage — la comparaison de silhouette) · **3** fermé, zoom sur la gueule · **4** mi-ouvert (recul
750 mm) · **5** dessus, ouvert · **6** dessus, ouvert, **noyau escamoté**, Specter-9 à l'échelle.
