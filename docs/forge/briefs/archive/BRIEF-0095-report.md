# BRIEF-0095 — rapport de forge : les portes du pont d'envol

- **Rendu par** : asset-forge
- **Date** : 2026-08-30
- **Brief** : [`BRIEF-0095-portes-de-pont.md`](BRIEF-0095-portes-de-pont.md)
- **Section `## Texture` du brief** : **présente**, et elle tranche — *aucune demande de texture*,
  dépliage `ak.box_project_uv()` aux tuiles/m du kit, à mesurer dans le script et non à redeviner.
  Contrat `ADR-0028` respecté : je livre la géométrie et les UV, jamais la matière.

## Texture

**Aucune demande `TEX-NNNN`, et c'est ce que le brief tranchait.** Le kit de hangar s'habille par
facteurs PBR et par les matériaux nommés de la coque ; les deux battants n'emploient que des
matériaux **déjà présents** dans le kit — c'est aussi ce qui garantit que les sept pièces gelées
n'ont pas été réindexées.

**Dépliage livré** : `ak.box_project_uv()`, densité de texels mesurée à **0,141–0,200, moyenne
0,198 t/m** (5,04 m par tuile), anisotropie 1,41 — identique au bordé du kit. `TEXCOORD_0` est
compté dans le binaire, le harnais échoue s'il manque.

---

## 1. Livrables

| Chemin | Nature |
|---|---|
| `assets/imported/models/backgrounds/bay_kit.glb` | le kit, **neuf** pièces au lieu de sept |
| `tools/blender/build_bay_kit.py` | la source (ADR-0008), **étendue** et non réécrite |
| `docs/forge/output/BRIEF-0095-planche-portes.png` | planche 4 vues, 1440 × 2800 |
| `assets/licenses/ASSET_PROVENANCE.csv` | ligne `bay_kit` complétée + ligne `brief_0095_planche_portes` |

`sha256` du `.glb` : `77a908a6e1a6d9d9daf8a8f4f985a0ce06335f9cd4e4f44d5e99da860caa5d44` — 116 644 octets.

## 2. Les sept pièces existantes n'ont pas bougé d'un octet

C'était la condition la plus dure du lot, et elle a été **vérifiée, pas espérée**. Le `.glb`
d'avant a été mis de côté, puis les deux binaires ont été comparés **accesseur par accesseur** :
`POSITION`, `NORMAL`, `TANGENT`, `TEXCOORD_0`, indices, et le matériau de chaque primitive.

```
OK   bay_frame_left      OK   bay_inner_wall     OK   bay_launch_rail
OK   bay_frame_right     OK   bay_floor          OK   bay_service_block
OK   bay_frame_top
NEW  bay_door_left       NEW  bay_door_right
liste et facteurs de matériaux : identiques
```

Deux précautions rendent ce résultat possible et **le rendront encore vrai au prochain ajout** :

- les battants sont créés **en fin** de `build_parts()` et **en fin** de `PART_NAMES` : l'exporteur
  écrit dans l'ordre des objets, et ajouter en tête aurait décalé les sept ;
- les battants **n'emploient que des matériaux déjà présents** dans le kit (`AA_Hull`, `AA_Greeble`,
  `AA_Trim`, `AA_Emissive_Engine`). Un slot neuf aurait réindexé la liste, donc changé les
  primitives des sept.

Seul le conteneur grossit : 49 780 → 116 644 octets.

## 3. Triangles comptés

| Pièce | tri |
|---|---|
| `bay_door_left` | **402** |
| `bay_door_right` | **402** |
| **la paire** | **804** / budget **1 200** |
| kit complet (9 pièces) | 1 140 |
| hangar assemblé (rail ×2, traverse ×2) | 1 200 / 2 800 |
| les sept hangars du niveau | 8 400 / 20 000 |

Le budget a **piloté le dessin**, il ne l'a pas seulement borné. Le profil balayé compte douze
stations : chacune coûte deux triangles par bande, et le battant en compte une vingtaine. Une
station de plus, c'est +108 triangles pour la paire. C'est ce calcul qui a écarté la nervure en
relief au profit d'un chevron obtenu par la forme des caissons (§5).

## 4. Emprise mesurée, relevée sur le binaire

| | x | y | z |
|---|---|---|---|
| `bay_door_left` | `[-3,000 ; +0,120]` | `[+0,000 ; +0,175]` | `[-4,250 ; +4,250]` |
| `bay_door_right` | `[-0,120 ; +3,000]` | `[+0,000 ; +0,175]` | `[-4,250 ; +4,250]` |

- **emprise fermée** : chaque battant couvre sa demi-ouverture **en entier** (bord extérieur à
  ±3,000 exactement, contre la face interne du montant ; extrémités à ±4,250, contre les traverses) ;
- **épaisseur** : **0,175 m** ≤ 0,22 ;
- **point le plus haut** : **+0,175 m** ≤ +0,18 — il glisse sous la lèvre du coaming (+0,60) ;
- **dessous** : plat, à **y = 0,000**, l'origine *est* le point d'assemblage ;
- le seul dépassement au-delà de ±3,00 est **la denture**, à 0,12 m, et elle est demandée par le
  brief (« les deux battants s'interpénètrent »). **Rien ne dépasse du côté de la course.**

**Aucun jour** : l'emprise projetée des deux solides sur le plan (x, z) a été **rasterisée à 2 cm**
sur toute l'ouverture de 6,00 × 8,50 m — **0 cellule découverte sur 127 500**. Ce n'est pas un
raisonnement, c'est une mesure, et elle échoue le build.

**Volume signé** : +3,162 m³ pour chacun. C'est la preuve que les normales sortent — une pièce
retournée ne rate ni bbox, ni compte de triangles, ni mesure d'UV : elle disparaît en jeu par
culling arrière, sans une ligne au journal.

## 5. Points de conception que j'ai dû trancher

### 5.1 L'origine : « au centre de sa surface » **et** « arête de jonction sur x = 0 »

Le tableau du brief donne deux repères qui, lus à la lettre sur l'axe X, se contredisent : un
centre de surface mettrait l'origine à ∓1,50. **J'ai retenu l'arête de jonction**, et le résultat
satisfait les deux clauses sur deux axes sur trois : l'origine est **au milieu en Z**, **au plan de
la peau en Y**, et **sur l'arête de jonction en X**. C'est aussi la convention de tout le kit —
« origine au point d'assemblage » —, celle qui fait que `bay_frame_left` a sa face interne à 0,0000.

**Conséquence pour le moteur** : le montage n'est plus celui du `BoxMesh` centré. Les deux battants
se posent à `(0, 0, 0)` fermés, et l'ouverture est une **translation de 3,00 m vers l'extérieur** :

```
bay_door_left   position.x = -3,00 * ouverture      (0 fermé, 1 ouvert)
bay_door_right  position.x = +3,00 * ouverture
```

là où `_build_doors()` pose aujourd'hui `side * (OPENING_HALF_X * 0.5 + DOOR_SLIDE * _door_open)`.
Je n'ai touché à aucun script de gameplay : c'est au concepteur de recâbler.

### 5.2 « Miroir exact » est impossible — c'est un **demi-tour**

Le brief demande le battant tribord en « miroir exact ». Un miroir en X **ne peut pas** produire
deux dentures complémentaires, et cela se démontre en une ligne : si le bord bâbord est en `t(z)`,
le bord tribord miroir est en `-t(z)` ; pour qu'ils se rejoignent sans jour ni recouvrement il
faudrait `-t(z) = t(z)`, donc `t = 0`, donc pas de denture. Il faut retourner **aussi en Z**.

`bay_door_right` est donc le bâbord **tourné d'un demi-tour autour de Y**. Trois conséquences, dont
deux sont des avantages :

- la denture devient complémentaire **par construction**, sans table de correspondance à tenir ;
- un demi-tour **conserve la chiralité** : les normales restent bonnes, là où un vrai miroir les
  aurait retournées en silence ;
- tout le reste du dessin est **symétrique en Z**, de sorte que le battant *se lit* bien comme le
  miroir de l'autre. C'est ce qui a imposé un chevron plutôt qu'une diagonale unique.

### 5.3 La denture : la dent avance plus que le creux ne recule

Dent à **+0,12**, creux à **−0,10**, soit **2 cm d'interpénétration** partout. À égalité, les deux
battants se toucheraient sur des faces exactement coplanaires : jour nul en géométrie, mais
scintillement garanti au rendu, à la seule incidence rasante où on les voit. Six bandes alternées
de 1,4167 m : **trois dents par battant, six alternances sur la ligne de fermeture** — le brief
demandait « 3 à 5 dents », c'est lu comme la denture du joint.

### 5.4 Le sens de lecture : chevron **par la forme des caissons**, pas par une nervure

Le brief laissait le choix « nervure diagonale **ou** rainures de renfort ». Une nervure en relief
coûtait quatre stations de profil, soit **+448 triangles pour la paire** — au-dessus du budget.
J'ai obtenu la diagonale **sans un triangle de plus** : la lèvre intérieure des trois caissons
s'écarte vers l'extérieur à mesure qu'on approche du milieu du battant (de −0,62 aux extrémités à
−1,70 au milieu). Les caissons dessinent une pointe large, tournée **vers le côté où le battant se
retire**. C'est très lisible sur la vue de dessus et sur la vue de proue de la planche.

### 5.5 Aucune grande surface en `AA_Trim` — corrigé au rendu, pas au raisonnement

Premier jet : poutre de nez et sabots en `AA_Trim`, l'ivoire froid #DDDCD2 de l'appareillage,
comme les rails. Dans le puits sombre `AA_Trim` détache le rail ; **sur la peau**, à côté d'un
coaming en #24252B, il faisait deux cadres blancs autour de trous noirs, et les battants ne
lisaient plus comme la pièce qui les entoure. Retiré. Il n'en reste que le filet du chanfrein
extérieur, large de 6 cm, exactement comme sur le chanfrein du coaming. Un violet `AA_Panel` a
également été essayé sur la rainure des sabots, puis retiré : sur les battants **retirés**, deux
barres violettes couraient en travers du bordé et tiraient l'œil plus que la lueur du puits, qui
est l'information.

### 5.6 Émissif : un trait par battant, calibré **par la largeur**

Le brief autorise « deux traits de bordure au plus » et avertit que le moteur ramène tout émissif
de coque à 0,45 d'énergie. Le matériau `AA_Emissive_Engine` est **partagé avec les sept pièces
gelées** : y toucher les aurait modifiées. Mon seul levier est donc la **largeur**, et c'est celui
que j'ai réglé : un chanfrein de **0,09 m** sur l'arête de jonction, **1,08 m² par battant**. Il
suit la denture, donc il *dessine* la ligne de fermeture ; et il disparaît sous le coaming quand le
pont s'ouvre, ce qui est exactement ce qu'on veut d'un trait qui signe une fermeture.

L'émissif du kit passe de 8,8 à 11,0 m² bruts (3,8 % de l'aire vue du hangar assemblé, contre
4,7 % avant — la part **baisse**, l'aire totale ayant plus augmenté).

## 6. Dépliage et densité de texels

Projection en boîte, **même densité que le bordé et que les sept autres pièces** : `0,200 tuile/m`
(5,00 m par tuile). Mesurée sur le binaire, par valeurs singulières, triangle par triangle :

| Pièce | min | max | moyenne | m/tuile | anisotropie max |
|---|---|---|---|---|---|
| `bay_door_left` | 0,141 | 0,200 | 0,198 | 5,04 | **1,41** |
| `bay_door_right` | 0,141 | 0,200 | 0,198 | 5,04 | **1,41** |

Borne théorique de la méthode : 1,73. Les valeurs sont dans le même intervalle que `bay_inner_wall`
(1,42), ce qui est attendu : les mêmes chanfreins obliques.

**Coutures** : ce sont les discontinuités d'axe dominant de la projection, donc **les arêtes
vives** — le chanfrein de jonction, les marches de la poutre de nez, les lèvres de caisson, le
chanfrein extérieur, et le pourtour du dessous. Aucune au milieu d'une surface. Le brief ne
demandait pas de dépliage continu ; **aucune planche au damier UV n'est donc requise ici**, et
`uv1_scale` doit rester `(1 1 1)`.

`TEXCOORD_0` : **30 primitives sur 30**, comptées dans le `.glb`. `TANGENT` : 30/30.
Aucune image embarquée, aucun `baseColorTexture`/`normalTexture`/`emissiveTexture` — le harnais
échoue le build si l'un apparaît.

## 7. Ce que la planche montre — et ce qu'elle m'a fait corriger

`docs/forge/output/BRIEF-0095-planche-portes.png`, 1440 × 2800, quatre vues :

1. **Pont fermé**, à la caméra exacte du jeu, Specter-9 réel à sa place ;
2. **le même cadre, pont ouvert à 3,00 m** — la course réelle du moteur, pas une pose d'atelier ;
3. **le dessus** orthographique, kit seul, portes fermées : la denture, les caissons, le chevron ;
4. **vue de proue à 25°, longue focale** : bâbord fermé et tribord ouvert dans le même cadre.

Une **élévation strictement orthographique** a été rendue d'abord, puis abandonnée : sur une
vignette large de 1 440 px il faut 13 m de champ pour tenir la course, ce qui laisse 20 px à un
battant de 0,175 m — l'objet même de la vignette devenait un cheveu. Et à 18° d'élévation, le
spéculaire lave toutes les valeurs et la pièce ressort blanche. 25° est le compromis mesuré.

Un défaut de repère a aussi été trouvé en route et corrigé dans le script : le motif
`forward.cross(X).cross(forward)`, employé ailleurs dans le fichier pour construire le vecteur
« haut » d'une caméra, **rend exactement l'axe X** quand la visée est dans le plan (Y, Z). La caméra
sortait roulée d'un quart de tour, avec le champ vertical appliqué en travers — et rien dans le
rendu ne dit « roulé », on n'y voit qu'un cadrage étrange. Le nouveau code projette le « haut »
du monde.

## 8. Ce qu'il faut rendre au concepteur — une mesure, pas une objection

> **Un battant de 3,00 m retiré de 3,00 m sort entièrement de l'ouverture.**

Ouvert, `bay_door_left` occupe `x ∈ [−6,00 ; −2,88]`. La face extérieure du coaming est à
`x = −3,80`. Il reste donc **2,20 m de battant qui reposent sur le bordé**, au-dessus d'une peau
qui, à cet endroit, continue de descendre — d'où le « il flotte » que le brief redoute.

C'est une conséquence de la **course**, pas de la géométrie livrée : celle-ci ne déborde nulle part
de son emprise, et c'est bien ce que le brief exigeait de moi. La vignette 2 montre à quoi cela
ressemble à la caméra du jeu : ça se lit comme deux panneaux coulissants rétractés sur le bordé,
ce qui est acceptable — mais c'est un jugement d'opérateur, pas de forge. Trois issues possibles,
toutes hors de mon périmètre :

- **assumer** : c'est ce que fait déjà le moteur aujourd'hui, et la planche montre que ça tient ;
- **raccourcir la course** à ~2,2 m : les battants restent alors partiellement sur l'ouverture,
  mais leur arête reste sous le coaming et rien ne flotte. Le puits n'est plus dégagé qu'aux 3/4 ;
- **basculer plutôt que coulisser** : hors sujet pour ce lot, et cela demanderait une autre pièce.

## 9. Contrôles passés

| Contrôle | Résultat |
|---|---|
| `./scripts/build-hull.sh --check bay_kit` | **déterminisme OK**, 0 octet divergent (`-t 1`) |
| Sept pièces gelées, accesseur par accesseur | **identiques** |
| `TEXCOORD_0` / `TANGENT` comptés dans le `.glb` | 30/30 et 30/30 |
| Emprise, épaisseur, plafond, dessous plat | mesurés, dans les cotes |
| Absence de jour (rasterisation 2 cm) | 0 / 127 500 |
| Volume signé (normales sortantes) | +3,162 m³ ×2 |
| Budget | 804 / 1 200 |
| Couleurs réservées aux tirs (#3FD9E8, #FF5A3D) | absentes, y compris des annotations |
| Textures embarquées / images dans le `.glb` | aucune (ADR-0028) |
| `./scripts/check.sh` | **ALL GREEN** — 779 méthodes, 5 719 assertions, 0 échec |
| IP | aucune livrée, aucun marquage, aucune silhouette empruntée |

## 10. Suggestions

- **Le nom `bay_door_left` est piégeux** au montage : « left » désigne bâbord dans le repère du
  hangar, mais le moteur le pose à `x = 0` et non à `x = −3`. Le nom est gelé, je ne le touche pas ;
  une ligne de commentaire dans `_build_doors()` évitera une heure de recherche à quelqu'un.
- **Un état « battant coincé »** viendrait presque gratuitement : le moteur sait déjà arrêter la
  course à mi-chemin, et un pont abattu figé à 40 % d'ouverture, denture visible, dirait « cassé »
  bien plus fort qu'un pont simplement fermé.
- **Les caissons pourraient recevoir la carte de détail** le jour où l'opérateur en générera une :
  ils sont dépliés à la densité du bordé et leurs coutures sont sur les arêtes vives. Rien à
  reforger, une demande `TEX-NNNN` suffira.
