# BRIEF-0046 — Shield Carrier, coque 3D : compte-rendu

*Livré le 2026-08-25 par `asset-forge`. `shield_carrier.glb` sha256
`d72eccd37b777e8854506fd9064f67138a92fb95539ec2465e6c5c14611ef8c7` (331 588 o).*

## 1. Livrables

| Fichier | Quoi |
|---|---|
| `tools/blender/build_shield_carrier.py` | script de construction, déterministe, auto-validant, quatre harnais de mesure |
| `assets/imported/models/ships/shield_carrier.glb` | le mesh (LFS) |
| `docs/forge/output/BRIEF-0046-planche-quatre-vues.png` | recette 4 vues au repos (ADR-0006) |
| `docs/forge/output/BRIEF-0046-bras-ecartes.png` | 6 poses **à la perspective réelle du jeu** + rangée à l'échelle du jeu |
| `docs/forge/output/BRIEF-0046-silhouette-comparee.png` | aplats noirs : les six coques d'ennemis, même champ, même perspective |
| `docs/forge/output/BRIEF-0046-report.md` | ce document |

> `assets/imported/models/ships/shield_carrier.glb.import` est apparu pendant la session : il a
> été écrit par un import Godot, pas par la forge. Il est normal et attendu (les cinq autres
> coques ont le leur, versionné), mais il n'est pas mon livrable.

## 2. Les chiffres que le brief exige

| Question | Réponse mesurée |
|---|---|
| Bounding box | **2,2000 × 1,8000 m**, hauteur **0,6494 m** — écart au contrat **0,00 %** en X et Z |
| Triangles | **4 788** (budget 8 000, marge 40 %) — 5 902 sommets |
| `TEXCOORD_0` dans le `.glb` produit | **19/19 primitives**, plus 19/19 `TANGENT`, vérifié par relecture du binaire |
| Croissance du diamètre apparent, **caméra de `graybox.tscn`** | **+19,47 %** à 40° (130,55 → 155,96 px) — **au-dessus du plancher de 10 %** |
| Débattement mécanique | **aucune butée** : rien ne se touche jusqu'à 90°, marge minimale 12,0 mm au repos |
| Émissif, aire **vue** | **12,70 %** — dont **10,48 % le projecteur** et **2,22 % tout le reste** |
| Émissif, aire **totale** | 4,38 % — dont 2,86 % le projecteur |
| Déterminisme | `build-hull.sh --check shield_carrier` → deux `.glb` byte-identiques |

**Verdict sur l'articulation : elle sert.** +19,5 % de diamètre apparent, et le seuil de 10 % est
déjà franchi à **14°**. Ce n'est pas un accident : la géométrie a été choisie pour ça (§4).

**Valeur à écrire dans la Resource : `open_angle_deg = 40`.** Ce n'est pas une butée — il n'y en a
pas — c'est le **maximum utile** : la courbe plafonne à 50° (+19,9 %) puis redescend, et au-delà de
50° les coquilles basculent assez pour montrer leur ventre, ce qui se lit comme un défaut et non
comme une ouverture.

## 3. Contrat et mesures

| Critère | Exigé | Mesuré | |
|---|---|---|---|
| Largeur X | 2,20 m ±3 % | **2,2000 m** (+0,00 %) | ✅ |
| Longueur Z | 1,80 m ±3 % | **1,8000 m** (+0,00 %) | ✅ |
| Hauteur Y | ≤ 0,70 m | **0,6494 m** (93 % du plafond) | ✅ |
| Centrage du pivot | ±20 mm en X/Z | (+0,0000 ; −0,0047 ; −0,0020) | ✅ |
| Triangles | ≤ 8 000 | **4 788** | ✅ |
| UV | 100 % des primitives | **19/19 `TEXCOORD_0`**, 19/19 `TANGENT` | ✅ |
| Orientation | nez −Z Godot | vérifiée par témoins asymétriques (`export_hull`) | ✅ |
| `Muzzle_C` | sur l'axe, à l'avant | (0 ; +0,1920 ; −0,7950) — au centre de la grille d'étrave | ✅ |
| `Engine_C` | **obligatoire** | (0 ; −0,0910 ; +0,8000) — lèvre de la tuyère ventrale | ✅ |
| Pièces mobiles | 3 `Cradle_NN` | `Cradle_01` (bâbord), `Cradle_02` (tribord), `Cradle_03` (arrière) | ✅ |
| Palette | Chœur Nul, `MATERIAL_ORDER` inchangé | les 7 matériaux présents et assignés | ✅ |
| Kit partagé | non modifié | `aegis_kit.py` intact (1.1.0), `git status` propre dessus | ✅ |

Répartition des triangles : `AA_Greeble` 2 546, `AA_Panel` 990, `AA_Hull` 395, `AA_Emissive_Engine`
356, `AA_Trim` 210, `AA_Marking_Red` 147, `AA_Glass` 144.

⚠️ **La bbox du contrat est celle de la pose FERMÉE.** Ouverte à 40°, l'enveloppe hors-tout vaut
environ **2,52 × 1,86 m**. C'est le but ; mais une hitbox réglée sur 2,20 × 1,80 laissera les
coquilles ouvertes traverser sans contact.

## 4. « Les bras portent la silhouette » — la leçon de BRIEF-0042, et pourquoi elle n'est pas repayée

### 4.1 Le mécanisme du défaut, et sa conséquence obligatoire

`EnemyPose._hinge_axis` rend la tangente horizontale au rayon ; `axe × radial = +Y`, donc **un angle
positif emmène le rayon vers le haut**. Une pièce qui pointe déjà vers l'extérieur voit son rayon
multiplié par `cos(angle)` : elle **rentre**. Pour qu'une rotation agrandisse l'enveloppe, la pièce
doit **plonger sous son plan au repos** et se relever. Gain = `hypot(e,h) − e`, optimum à
`atan(h/e)`.

### 4.2 Le parti pris qui en découle : **les amandes SONT les bras**

La planche montre « deux coques en amande enserrant un gros projecteur ». J'en ai fait **les deux
grands bras de berceau**, et non des coques fixes. Chacune est charnière sur la ligne longitudinale
`x = ±0,585` (donc son pivot est en `y = 0`, seule position qui donne un axe exactement
longitudinal) et **tout son bord extérieur est posé sur le cône de pente 40° issu de cette ligne** :
`plongée = (x_bord − 0,585) × tan 40°`. Conséquence voulue — la coquille **entière** arrive à plat
au même angle, d'un seul coup, au lieu de se tordre.

| Pièce | charnière | `e` | `h` | gain de rayon | en % du rayon |
|---|---|---|---|---|---|
| `Cradle_01` / `Cradle_02` (coquilles) | x = ±0,585 ; z = +0,140 | 0,5150 m | 0,4321 m | **157,3 mm** | +14,30 % |
| `Cradle_03` (berceau arrière) | y = +0,590 ; z = +0,120 | 0,3080 m | 0,2584 m | **94,1 mm** | +10,47 % |

`h` est ce que la **hauteur** achète : 0,6494 m sur 0,70 autorisés, et les 50 mm restants sont la
marge de chanfrein. C'est le seul levier, et il est borné par le plafond du brief.

### 4.3 La garde à l'export — deux gardes, en fait

Le script **refuse d'exporter** si, à un angle quelconque du balayage :

1. **garde globale** (celle du Leech Drone) : le rayon XZ maximal de la coque **fixe** atteint celui
   des pièces mobiles ;
2. **garde par bras** (ajoutée ici) : un bras cesse de déborder la coque fixe **dans son propre
   secteur azimutal** (±25°). Sans elle, une seule pièce très saillante suffirait à valider trois
   pièces dont deux remueraient derrière la coque sans rien changer.

| pose | rayon XZ coque fixe | rayon XZ des bras |
|---|---|---|
| fermée (0°) | 0,9274 m | **1,1000 m** |
| 40° | 0,9274 m | **1,2812 m** |

Par secteur, au repos : `Cradle_01` 1,100 contre 0,602 · `Cradle_02` 1,100 contre 0,611 ·
`Cradle_03` 0,909 contre 0,773 m. **Les quatre extrêmes de la bounding box appartiennent à des
pièces mobiles** : ±X et l'avant aux coquilles, l'arrière au berceau.

### 4.4 Écart assumé au brief : ce qui se découvre n'est pas le projecteur

Le brief demande des bras qui « s'écartent vers l'extérieur **en découvrant le projecteur** ». Un
bras qui recouvre la lentille au repos aurait son extrémité **en deçà** de sa charnière ; le signe
de rotation d'`EnemyPose` la ferait alors **plonger dans le tambour**, et surtout un tel bras ne
porterait **aucune** enveloppe — c'est exactement le défaut de BRIEF-0042. Les deux exigences du
brief (« ils découvrent le projecteur » et « les bras portent la silhouette ») sont **géométriquement
incompatibles** sous cette convention de pose. J'ai tranché pour la seconde, qui est un critère
d'acceptation mesuré.

Ce qui se découvre est donc la **gouttière du joint** : les segments magenta et la machinerie vert
maladif que les coquilles plaquent au repos et qui s'ouvrent en grand quand elles se relèvent. La
lentille, elle, reste visible en permanence — c'est la fonction de l'unité, la cacher serait un
contresens.

## 5. Débattement mécanique, bras par bras

Mesuré sur le **maillage livré**, par pas de 1°, en BVH triangle-à-triangle dans les deux sens,
contre la coque fixe **et** contre les deux voisins, avec la convention exacte d'`EnemyPose`.
**Aucun rayon d'exclusion de charnière** (`HINGE_SKIP = 0`) : rien n'est encastré, donc rien n'est
amputé — contrairement au Leech Drone qui devait exclure une douille de 60 mm.

| Pièce | pivot (X, Y, Z) Godot | axe | 1re interpénétration | marge repos | marge 40° | marge 85° |
|---|---|---|---|---|---|---|
| `Cradle_01` (bâbord) | (−0,5850 ; +0,1400 ; 0,0000) | (0 ; 0 ; −1) | **aucune ≤ 90°** | 12,0 mm | 12,7 mm | 12,7 mm |
| `Cradle_02` (tribord) | (+0,5850 ; +0,1400 ; 0,0000) | (0 ; 0 ; +1) | **aucune ≤ 90°** | 12,0 mm | 12,7 mm | 12,7 mm |
| `Cradle_03` (arrière) | (0,0000 ; +0,1200 ; +0,5900) | (−1 ; 0 ; 0) | **aucune ≤ 90°** | 22,8 mm | 27,7 mm | 23,0 mm |

- **Dernière valeur sûre : ≥ 90°**, soit au-delà du plafond du code (`EnemyPose.MAX_OPEN_DEG = 85`).
  Il n'y a **pas de butée à respecter** ici, comme sur le Leech Drone (146°) et contrairement à la
  Choir Mine (57°) et au Null Maw (57,5°). Ce qui limite l'ouverture est la lecture, pas la mécanique.
- La marge de 12,0 mm au repos est le **jeu du joint**, posé volontairement (`JOINT_GAP`) : la
  coquille ne touche jamais le flanc, et la rotation l'en éloigne (12,7 mm dès 40°).

### La courbe d'enveloppe — et son maximum

Diamètre apparent de la silhouette projetée, à la **géométrie perspective réelle du jeu** : caméra
de `scenes/gameplay/graybox.tscn`, position (0 ; 14 ; 5), axe de visée à 70° sous l'horizontale,
fov 62, 1080 p ⇒ **14,87 unités** et **60,44 px par unité**. Cadrage figé sur l'état fermé.

| ouverture | diamètre écran | croissance | rayon XZ des bras |
|---|---|---|---|
| 0° (repos) | 130,55 px | — | 1,1000 m |
| 10° | 139,81 px | +7,10 % | 1,1737 m |
| 20° | 147,45 px | **+12,95 %** | 1,2295 m |
| 30° | 152,90 px | +17,13 % | 1,2657 m |
| **40°** | **155,96 px** | **+19,47 %** | **1,2812 m** |
| 50° | 156,49 px | +19,87 % | 1,2756 m |
| 60° | 154,40 px | +18,27 % | 1,2489 m |
| 70° | 149,70 px | +14,67 % | 1,2022 m |

La coque est quasi symétrique avant/arrière : les chiffres sont identiques à 0,01 % près que le nez
soit tourné vers le joueur ou non — contrairement au Leech Drone, il n'y a donc **qu'un** chiffre à
retenir.

⚠️ **La courbe a un maximum et redescend** (`atan(h/e)` = 40°, le plateau 40-50° vient de la
contribution du berceau arrière). Une donnée réglée « au plus haut possible » serait *moins* lisible.

### Le coulissement radial : mesuré, non recommandé

| `open_spread` | diamètre | croissance | jour ouvert au joint |
|---|---|---|---|
| 0,00 | 155,96 px | +19,47 % | 0 mm |
| 0,15 | 166,65 px | +27,65 % | **88,5 mm** |
| 0,30 | 177,33 px | +35,84 % | 177,0 mm |
| 0,50 | 191,57 px | +46,75 % | 295,0 mm |

**Recommandation : `open_spread = 0`.** Il paie très bien, mais la coquille glisse alors le long de
son propre rayon et **décolle du flanc** : 88 mm de vide au joint dès 0,15, soit une carapace
déboîtée sur une unité qui doit se lire comme *une machine en fonctionnement*. Si la session en veut
malgré tout, 0,05 (30 mm) est le maximum avant que le jour ne se lise à l'échelle du jeu.

## 6. Ce que la coque raconte, et où va le détail

- **Un œil, pas une bouche.** Le projecteur est un tambour dorsal coiffé d'une lentille magenta de
  322 mm de rayon **tournée vers le ciel**, donc vers la caméra (20° de la verticale). Quatre rayons
  sombres lui font un iris — obtenus en re-matérialisant un segment de tour sur cinq, **zéro triangle
  supplémentaire**.
- **Rien qui puisse tirer.** Aucune pointe, aucun fût, aucun nez : l'avant est une **étrave large de
  680 mm** percée d'une grille sombre creusée dans le pont (quatre écailles réenfoncées en
  `AA_Glass`, lippe ivoire). `Muzzle_C` est posé dessus parce que `EnemyController` le lit — c'est un
  event, pas une arme. Premier essai écarté : un bloc d'admission en saillie était intégralement
  enterré sous le pont, donc invisible.
- **La masse est l'information.** 2,20 × 1,80 m contre 1,45 (Null Maw), 1,15 (Choir Mine), 0,85
  (Leech Drone). En jeu elle mesure **131 px de large** à l'origine du plan — presque trois fois la
  sangsue. La consigne « verdict à 46 px » des briefs précédents ne s'applique pas telle quelle : à
  46 px on ne verrait aucune de ces coques correctement, et celle-ci n'y sera jamais.
- **Elle vole.** Tuyère ventrale arrière magenta (`Engine_C`) abritée par le berceau, transom
  marqué : un arrière existe, donc un sens de marche. Les deux mines n'en ont pas.
- **Détail sur le dessus uniquement** (BRIEF-0026 / ADR-0011) : mosaïque de grandes écailles
  enfoncées sur les coquilles, pont annulaire à 26 écailles autour du tambour, gradins du
  projecteur, veines magenta, listels ivoire en diagonale (signature de la planche), deux blocs vert
  maladif dans la gouttière. Les dessous sont nus.

### Répartition des matériaux — aire VUE **et** aire TOTALE

Aire vue : rastérisation avec z-buffer depuis la caméra de jeu (ce qui est occulté ne compte pas).
Aire totale : somme des aires de faces, flancs et dessous compris — la vue de trois quarts du
bestiaire.

| Matériau | aire **vue** | aire **totale** | rôle |
|---|---|---|---|
| `AA_Panel` | 38,66 % | 15,62 % | fond des écailles des coquilles, pont, collier du tambour |
| `AA_Greeble` | 30,46 % | 50,78 % | **rainures** entre écailles, gouttière, dessous, tuyère, iris |
| `AA_Emissive_Engine` | **12,70 %** | 4,38 % | lentille Ø 644 mm, 5 veines, segments de gouttière, tuyère |
| `AA_Trim` | 7,71 % | 2,45 % | filet du tambour, listels des coquilles, lippe de l'étrave |
| `AA_Hull` | 6,05 % | 24,01 % | ceinture, ventre des coquilles, robe du tambour |
| `AA_Glass` | 3,32 % | 1,02 % | membrane sombre autour de la lentille, grille d'étrave |
| `AA_Marking_Red` (vert maladif) | 1,11 % | 1,75 % | deux blocs de gouttière + deux écailles, bâbord seulement |

**L'exception d'émissif demandée par le brief est tenue, et elle est concentrée : 12,70 % de l'aire
vue, dont 10,48 % le seul projecteur et 2,22 % tout le reste de la coque** (plancher 12 %, plafond
15 %, reste sous 3 %). Le script **refuse d'exporter** si l'émissif hors projecteur dépasse 3 %.
Sur l'aire *totale*, les mêmes surfaces ne pèsent que 4,38 % : c'est l'écart que le brief voulait
voir constaté — un ventre que le jeu ne montre jamais représente la moitié de la surface du modèle.

## 7. Un défaut trouvé en chemin : le rastériseur du harnais d'aire vue était faux

Le harnais « aire vue » a été repris du Leech Drone. Ses coordonnées barycentriques ne sont **pas**
des barycentriques :

```
w0 = ((by-ay)(cx-sx) - (bx-sx)(cy-ay)) / det     # BRIEF-0044
   = 1 + u.x (AC.y - AB.y) / det                 # développement : u.y n'y figure pas
```

Le test rejette donc des points intérieurs : sur `a=(0,0) b=(1,0) c=(0,1)`, le **centre de gravité**
sort à `w2 = −0,75`. Ici, il amputait **40 % des pixels de la lentille** et rendait des parts
d'allure normale mais fausses — `AA_Greeble` à 39,96 % de l'aire vue pour une coque regardée à 20° de
la verticale, c'est-à-dire un dessous majoritaire à la caméra, ce qui est impossible. Corrigé
(barycentriques exactes), la même coque donne `AA_Greeble` 30,5 % (les rainures, pas les dessous) et
l'émissif passe de 8,21 % à 12,70 %.

**Conséquence pour la session : les répartitions de matériaux du rapport BRIEF-0044 sont à
considérer comme fausses** (Greeble 42,6 %, émissif 4,79 %). Le maillage du Leech Drone, lui, n'est
pas en cause — seule la mesure l'était. Le correctif vit dans le script de cette coque, avec sa
démonstration en commentaire ; il n'a pas été porté dans `build_leech_drone.py`, hors périmètre.

## 8. Distinction des cinq autres coques

`BRIEF-0046-silhouette-comparee.png` — aplats noirs, même champ (2,60 m) et même perspective, avec
une rangée à l'échelle réelle du jeu :

| | silhouette vue de dessus |
|---|---|
| **Shield Carrier** | **trois lobes** : une masse centrale large flanquée de deux amandes séparées par une couture, plus un talon arrière. La seule coque plus large que longue, et de très loin la plus grosse |
| Null Maw | couronne annulaire à quatre pétales, centre percé |
| Choir Mine | disque plein à denture périphérique |
| Leech Drone | trépied ajouré minuscule |
| Crescent Interceptor | croissant à deux cornes et deux dards |
| Needle Scout | dard plein, une seule ligne |

Aucune confusion possible : c'est la seule masse tri-lobée, et à l'échelle du jeu elle occupe deux
fois la largeur de tout ce que le joueur a rencontré avant. **Et rien n'y ressemble à une arme** :
pas une pointe, pas un fût, pas un nez — l'objet le plus saillant est un dôme lumineux tourné vers
le haut.

## 9. Limites connues

1. **Ce qui s'ouvre n'est pas ce que le brief décrivait** (§4.4). Les bras découvrent la gouttière
   du joint, pas la lentille — sous peine de repayer BRIEF-0042. C'est le seul écart de fond.
2. **La bbox ouverte (≈ 2,52 × 1,86 m) sort du contrat.** Voulu, mais une hitbox fixe à 2,20 × 1,80
   laissera les coquilles ouvertes traverser sans contact.
3. **Au-delà de 50°, les coquilles montrent leur ventre** (`AA_Hull` nu, sans détail) et l'ouverture
   se lit moins bien alors même que le diamètre est encore grand. C'est la vraie raison de
   recommander 40°, plus que la courbe.
4. **Le motif d'écailles des coquilles est régulier** (4 colonnes × 4 rangées). La planche montre une
   mosaïque plus irrégulière ; le budget le permettrait (4 788 / 8 000), mais à 131 px un motif plus
   fin risquait de virer au bruit. À rouvrir si un plan rapproché existe un jour.
5. **La gouttière du joint est sombre au repos** : à la caméra de jeu, les coquilles se lisent comme
   deux volumes bien séparés du corps. C'est fidèle à la planche (elle montre le même sillon), mais
   si la session la trouve trop détachée, le levier est `JOINT_X` (rapprocher la charnière du corps)
   — au prix direct de la croissance d'enveloppe, qui est proportionnelle à `e = TIP_X − JOINT_X`.
6. **La plume d'`Engine_C` frôle le talon du berceau arrière.** La tuyère a été remontée à
   z = −0,091 exprès : le talon plonge à −0,177 et la ligne de visée du joueur passe au-dessus de
   lui. Une plume large de plus de ~120 mm mordra quand même le talon quand le berceau est fermé.
7. **`AA_Hull` ne pèse que 395 triangles** et 6 % de l'aire vue : sur cette coque, l'anthracite est
   porté par `AA_Greeble` (les rainures), et `AA_Hull` ne reste que sur la ceinture, le ventre et la
   robe du tambour. Les deux teintes sont voisines (#24252B et #141419), donc l'effet visuel est nul,
   mais un shader qui ciblerait `AA_Hull` par nom trouverait peu de matière.
8. Les harnais de rendu des planches de poses et de silhouettes vivent dans le **bac à sable** : le
   brief n'ouvre `tools/` que pour `build_shield_carrier.py`. Les mesures, elles, sont dans le script
   de coque et **rejouées à chaque build**.

## 10. Reproduire

```bash
blender45 -t 1 -b -P tools/blender/build_shield_carrier.py     # + les 4 harnais de mesure
./scripts/build-hull.sh --check shield_carrier                  # déterminisme (2 exports, sha256)
blender45 -b -P tools/render-hull.py -- assets/imported/models/ships/shield_carrier.glb
```

Le script échoue bruyamment — et n'écrit rien — si la bbox, le budget, les matériaux, les points
d'attache, l'orientation, le débattement (< 40°), la croissance d'enveloppe (< 10 %), la propriété
« chaque bras porte la silhouette dans son secteur », la part d'émissif hors projecteur (> 3 %) ou
les UV sortent du contrat.
