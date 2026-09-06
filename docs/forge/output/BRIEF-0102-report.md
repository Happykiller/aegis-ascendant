# BRIEF-0102 — La Specter-9 D dépliée en atlas : mesures, arbitrages, limites

- **Forge** : `asset-forge` (Claude), 2026-09-06
- **Brief** : [`BRIEF-0102-atlas-de-la-specter-9-d.md`](../briefs/BRIEF-0102-atlas-de-la-specter-9-d.md)
- **Outils** : Blender 5.2.1 LTS, `-t 1` forcé ; numpy/Pillow hors Blender
- **Source** : `assets/source/models/specter_9_d/spectre9_d.blend` (régime `ADR-0048`)

## Ce que ce lot livre, en une phrase

Les 406 pièces de la coque tiennent désormais dans **une seule image adressable** : le
fuselage y occupe 40 % de la surface, chaque aile 13 %, chaque nacelle 12 %, et une
coulure peut enfin être posée à un endroit choisi. **Le rig, la géométrie et la palette
sont intacts** ; la peinture, elle, reste à faire.

⚠️ **Et il ne faut rien promettre de plus.** La variance locale du rendu, à la caméra du
jeu, passe de **202,7 % à 203,5 %** : elle n'a pas bougé. C'est attendu — le brief le
disait, et la mesure du 2026-09-05 sur une autre coque le disait déjà. **Un atlas rend la
peinture possible ; il ne peint pas.** La coque habillée de l'atlas cuit ressemble à celle
d'avant, à ses lignes de panneau près.

---

## 1. Le rig survit — c'est le critère qui prime, et il est vérifié deux fois

### Au niveau du fichier, clé par clé

Les quatre clips, leurs quatre canaux, leurs échantillons et leurs valeurs ont été
comparés entre le `.glb` d'avant et celui d'après :

| Clip | Canaux | Échantillons | Durée | Amplitude tuyère | Amplitude aile |
|---|---|---|---|---|---|
| `Flight_Demo` | 4 | 241 | 8,00 s | 0,5800 m | 0,1564 (quaternion) |
| `Maneuver_to_Cruise` | 4 | 46 | 1,50 s | 0,2400 m | 0,0698 |
| `Cruise_to_Intercept` | 4 | 46 | 1,50 s | 0,3400 m | 0,0867 |
| `Intercept_to_Maneuver` | 4 | 61 | 2,00 s | 0,5800 m | 0,1564 |

**Écart maximal sur l'ensemble des clés des quatre clips (temps ET valeurs) :
`5,96e-08`** — le bruit de la quantification float32, rien d'autre.

### Après réimport, en rejouant

Le `.glb` livré a été réimporté dans une scène vide et **les quatre clips ont été
rejoués**, image par image, en mesurant le déplacement et la rotation monde des six
nœuds du contrat :

| Clip | images | `Wing L/R` | `Nozzle L/R` | `MARKER exhaust L/R` |
|---|---|---|---|---|
| `Flight_Demo` | 193 | **18,00°** | **0,5837 m** | **0,5837 m** |
| `Maneuver_to_Cruise` | 37 | 2,38° | 0,0718 m | 0,0718 m |
| `Cruise_to_Intercept` | 37 | 2,38° | 0,0718 m | 0,0718 m |
| `Intercept_to_Maneuver` | 49 | 6,21° | 0,1876 m | 0,1876 m |

**Le même tableau, au chiffre près, sort du `.glb` d'avant.** Les marqueurs suivent leur
tuyère (ils en sont enfants), les ailes tournent sans se déplacer, les tuyères se
déplacent sans tourner. Le nombre d'images diffère de la source (193 pour 241) parce que
Blender réimporte à 24 im/s quand la scène d'origine est à 30 : c'est une propriété de la
scène de relecture, pas du fichier — les durées en secondes, elles, sont identiques.

### La hiérarchie et les noms

Sept nœuds de contrat, mêmes noms, mêmes parents, mêmes échelles :

```
CTRL | Aircraft            (racine)
├── CTRL | Wing L / R      t = (∓1,000 ; 0,050 ; 2,480)
└── CTRL | Nozzle L / R    t = (∓1,325 ; 0,280 ; −4,810)
    └── MARKER | exhaust L / R   t = (0 ; 0 ; −1,450)
```

**Seule différence mesurable de tout le rig** : les deux `CTRL | Nozzle` passent de
`−4,809999` à `−4,810000` sur Z, soit **1 µm** de modèle (0,2 µm en jeu). C'est la
requantification float32 de l'export, pas un déplacement.

**Comment ça a été obtenu** : le script reprend **telle quelle** la recette d'export de
l'auteur (`assets/source/models/specter_9_d/scripts/export_asset.py`) — échantillonnage
des pilotes en images clés, quatre pistes NLA, `export_animation_mode="NLA_TRACKS"`.
Aucun `join`, aucun `apply` de modificateur, aucun reparentage. Les modificateurs
(329 biseaux, 329 normales pondérées, 172 solidifications) restent sur leurs objets et ne
sont appliqués que par l'exporteur, comme avant.

## 2. La géométrie ne bouge pas — et ce n'était pas gratuit

**413 nœuds · 406 maillages · 49 116 triangles · `TEXCOORD_0` sur 406 primitives sur
406 · 0 boucle UV hors du carré.** Compté sur le fichier livré, pas supposé.

⚠️ **Un piège a failli coûter 320 triangles, et il mérite d'être noté.** `atlas_unwrap()`
triangule avant de déplier, pour une raison mesurée (`ak.triangulate`) : un quad gauche
n'a pas de normale, sa projection se calcule pour un plan qui n'est celui d'aucun de ses
deux triangles, et l'îlot se replie sur lui-même. **Sans triangulation préalable, le
recouvrement mesuré passe à 9 398 texels (1,5e-02, trente fois le seuil d'`ADR-0047`).**

Mais cette coque est portée par des modificateurs, et **le biseau ne produit pas la même
chose au sommet d'un quad et au sommet d'un triangle** : trianguler tout ajoutait
320 triangles (49 436 au lieu de 49 116), sur deux pièces seulement.

La règle appliquée n'arbitre pas, elle **mesure** : on triangule une pièce, on recompte sa
géométrie évaluée, **et on annule si elle a bougé**. Résultat : 404 pièces triangulées,
deux refusent (`CANOPY | fixed smoked glazing` et `HULL | continuous editable fuselage`),
et le recouvrement résiduel qu'elles causent est **nul**.

## 3. La densité de texels, famille par famille

### Sur la cage de base — ce que le dépliage a produit

Atlas de **2048²**, remplissage **57,1 %**, 57 120 boucles UV, 2,8 s.

| Famille | Poids | Pièces | Aire (m²) | Part d'atlas | texels/m modèle | p05 – p95 |
|---|---|---|---|---|---|---|
| `skin` | 1,00 | 245 | 366,23 | **93,3 %** | **78,1** | 68 – 80 |
| `mechanism` | 0,55 | 80 | 53,22 | 3,9 % | 41,8 | 37 – 44 |
| `glazing` | 0,55 | 1 | 11,08 | 0,8 % | 41,4 | 36 – 44 |
| `canopy_frame` | 1,00 | 8 | 3,25 | 0,7 % | 72,3 | 61 – 80 |
| `hardware` | 0,45 | 53 | 13,39 | 0,7 % | 34,5 | 30 – 36 |
| `markings` | 1,00 | 19 | 2,57 | 0,7 % | 78,1 | 66 – 80 |

**Écart maximal entre familles : 78,1 / 34,5 = 2,26.** Il dépasse le facteur 2 du brief et
se justifie : `hardware` ne contient que des rivets de 20 mm, des ailerons de missile de
3 mm d'épaisseur et des bouches de canon. **À 45,8 px/m à l'écran en jeu, un rivet fait un
cinquième de pixel** ; lui donner la densité du fuselage, c'est payer des texels qu'aucun
écran ne restituera. À l'intérieur d'une famille, en revanche, l'homogénéité est réelle :
la peau tient dans **68–80 texels/m entre les 5e et 95e centiles**, soit ±8 %.

### Ce que ça vaut à l'écran

| | modèle | jeu (×0,19501) | écran |
|---|---|---|---|
| Densité de la peau | 78,1 texels/m | **401 texels/m** | 45,8 px/m → **sur-échantillonné 8,7×** |
| Au bestiaire (coque ~5× plus grande) | | | sur-échantillonné ~1,7× |

⚠️ **La cote annoncée par le brief était optimiste, et il faut le dire** : il attendait
« de l'ordre de 150 texels/m », calculés sur la boîte englobante. La surface développée
réelle est de **449 m² de cage** (une coque de 406 pièces a beaucoup plus de peau qu'un
parallélépipède), et le packing en lit 57 %. **La valeur mesurée est donc la moitié de
l'estimation : 78 texels/m.** Elle reste très au-dessus de l'écran.

⚠️ **Et l'atlas est 5,4× plus GROSSIER que la feuille qu'il remplace** : 0,831 tuile/m ×
512 px = 425 texels/m de modèle pour la feuille tuilée, contre 78 pour l'atlas. C'est le
prix de l'adressabilité, et il est payé volontairement. Passer l'atlas à 4096 rendrait
156 texels/m pour quatre fois le poids LFS ; c'est un arbitrage de concepteur, pas de
forge.

### Sur le maillage exporté — densité médiane par triangle

| Famille | texels/m (médiane) |
|---|---|
| `skin` | 88,6 |
| `markings` | 80,3 |
| `canopy_frame` | 73,0 |
| `mechanism` | 47,6 |
| `glazing` | 43,1 |
| `hardware` | 36,2 |

## 4. Le recouvrement : trois nombres, et ils ne disent pas la même chose

| Ce qu'on mesure | Résultat | Verdict |
|---|---|---|
| **La mise en page** (cage de base, garde d'`ADR-0047`, sonde 1024²) | **0 texel** sur 616 762 couverts | ✅ très en dessous du seuil de 5e-04 |
| **Entre pièces différentes**, sur le maillage exporté | **0 texel** | ✅ une coulure ne bavera jamais d'une plaque sur sa voisine |
| **À l'intérieur d'une pièce**, sur le maillage exporté | 96 814 / 581 081 = **1,67e-01** | ⚠️ voulu — voir ci-dessous |

⚠️ **Les 16,7 % de texels comptés deux fois sont le dos des pièces, et c'est une
ÉCONOMIE.** 172 pièces portent un modificateur `SOLIDIFY` (épaisseur 18 mm, décalage
intérieur) : leur coque intérieure est une copie de la face visible et **hérite de ses
UV**. Le contrôle le prouve : la somme des couvertures pièce par pièce (581 081 texels)
est **exactement** égale à la couverture globale — donc aucun texel n'est partagé entre
deux pièces, et la totalité du recouvrement est interne à 184 pièces.

Peindre une rayure sur une plaque la peint aussi sur sa face cachée, à 18 mm derrière,
tournée vers l'intérieur de la coque. **Personne ne la verra jamais, et ça rend 16,7 % de
l'atlas à ce qu'on regarde.** L'alternative — donner des texels propres aux faces cachées
— coûterait un sixième de la carte pour rien.

## 5. Les arbitrages, avec leurs parts chiffrées

### Par famille (le poids agit **en carré** sur la surface consommée)

| Famille | Part d'atlas **sans** pondération | Part **avec** | Ce qu'on y gagne |
|---|---|---|---|
| `skin` | 81,4 % | **93,3 %** | +7,0 % de densité linéaire pour la peau |
| `mechanism` | 11,8 % | 3,9 % | 24 pétales, 8 bandes, 2 manchons télescopiques : jamais peints |
| `hardware` | 3,0 % | 0,7 % | rivets, canons, missiles : sous le pixel |
| `glazing` | 2,5 % | 0,8 % | on ne peint pas sur une verrière fumée |
| `canopy_frame` | 0,7 % | 0,7 % | inchangé, poids 1 |
| `markings` | 0,6 % | 0,7 % | inchangé, poids 1 |

(Part sans pondération = part de l'aire développée ; part avec = mesurée dans l'atlas.)

**Le levier est réel mais modeste, et il ne faut pas le survendre** : la peau représente
déjà **81,4 %** de la surface développée. Reprendre les 18,6 % restants ne peut rendre que
**+7,0 % de densité linéaire** — soit 78,1 texels/m au lieu de 73,0. Le vrai levier de
densité serait la résolution ou le partage gauche/droite (voir §8).

### Par zone (le découpage vient des collections du `.blend`, pas d'une heuristique)

| Zone | Part de l'atlas |
|---|---|
| Fuselage | **40,4 %** |
| Wing L / Wing R | 13,1 % / 13,0 % |
| Engine L / Engine R | 12,1 % / 12,2 % |
| Tail fin L / R | 2,4 % / 2,4 % |
| Fixed canopy | 1,5 % |
| Nozzle L / R | 1,4 % / 1,4 % |

La symétrie gauche/droite des parts (13,1 vs 13,0 ; 12,1 vs 12,2) est un bon indice que le
packing n'a favorisé aucun côté.

## 6. Ce que la cuisson a produit — et le défaut qu'elle cachait

`tools/bake-atlas.py` a cuit **52 642 arêtes** en lignes de panneau, couvre 93,5 % de
l'image après dilatation, et **passe son `--check`** : deux cuissons, mêmes sha256
(albédo `b2e7e3f25c79bcc9`, hauteur `d85138da346244da`).

### ⚠️ DÉFAUT TROUVÉ ET CORRIGÉ : l'outil écrivait ses cartes À L'ENVERS

En glTF, `v = 0` désigne le **haut** de l'image (§3.8.2) ; l'outil posait son texel à la
ligne `(1 − v) × côté`, c'est-à-dire en bas. Godot lit la convention glTF, et Blender y
revient après l'inversion de son importeur : **les deux moteurs échantillonnaient le
miroir vertical de ce qu'on avait cuit.**

Sur une feuille répétable, un retournement ne se voit pas — le motif est le même à
l'endroit et à l'envers, et c'est pourquoi le défaut a survécu. **Sur un atlas, il mélange
toute la coque** : la première capture montrait la verrière peinte en bronze de sabord et
les ailes bleues par plaques. Il n'a été trouvé **qu'en regardant** la coque habillée
(`ADR-0006`), jamais par un test — c'est le troisième défaut de cet outil trouvé de cette
façon, après l'espace de couleur et la rainure comptée deux fois.

⚠️ **Conséquence pour le dépôt : tout atlas cuit avant le 2026-09-06 est faux et doit être
recuit.** Aucun n'est versionné aujourd'hui, donc rien à rattraper — mais la mesure du
2026-09-05 qui avait conclu « la variance n'a pas bougé » a été faite sur une carte
retournée.

### La feuille n'a pas été perdue : elle a été REPORTÉE

Cette coque n'a **aucun `baseColorFactor`** : ses quatre teintes vivent dans des textures.
L'extension demandée par le brief va un cran plus loin que « lire la teinte par matériau » :
quand le maillage a gardé le jeu d'UV de sa feuille (`TEXCOORD_1`), la feuille est
**échantillonnée et reportée dans l'atlas** au lieu d'être moyennée.

- **25 148 triangles sur 49 116 (51,2 %)** portent la feuille reportée : la tôle, le joint,
  le liseré, les rivets et la patine réécrits les 5 et 6 septembre passent dans l'atlas à
  leur échelle monde.
- Les 48,8 % restants (graphite, verrière, bronze, ion, encre) sont des matériaux à
  facteur : ils prennent leur couleur telle quelle.
- Les quatre teintes moyennes mesurées sur les feuilles retirées, en linéaire, et reportées
  en couleur unie dans le `.glb` :

| Matériau | linéaire | sRGB |
|---|---|---|
| `MAT | white` | (0,5536 ; 0,5808 ; 0,5671) | (196, 200, 198) |
| `MAT | blue` | (0,0051 ; 0,0256 ; 0,0647) | (16, 44, 72) |
| `MAT | red` | (0,4107 ; 0,0044 ; 0,0036) | (172, 14, 12) |
| `MAT | metal` | (0,0594 ; 0,0709 ; 0,0836) | (69, 75, 82) |

⚠️ **Le report perd de la finesse, et c'est arithmétique** : une tuile de 1,20 m occupait
512 px sur la feuille, elle occupe **94 texels** dans l'atlas. La structure survit (la
rainure de joint fait ~4 texels, les rivets ~1), la micro-texture non. À 11 px à l'écran
par tuile, rien de tout cela n'était visible de toute façon.

## 7. Ce qu'il faut savoir avant de peindre

- **La planche de repérage** (`BRIEF-0102-atlas.png`) donne les dix zones du `.blend` en
  couleurs, leur part d'atlas en légende, et le nom des vingt plus grosses pièces posé sur
  leur îlot. C'est le plan à joindre à la future demande de peinture.
- **Les coutures suivent les pièces.** Avec 406 objets, chaque plaque est son propre îlot :
  une couture tombe donc sur un bord de plaque réel, là où la géométrie casse déjà. Le
  brief demandait de couper « sous le ventre » ; **ce n'était applicable qu'aux deux
  grandes pièces continues** (fuselage et âme d'aile), où `smart_project` coupe à 66°,
  c'est-à-dire sur les arêtes vives. Aucune couture n'a été posée en travers d'une surface
  ouverte, mais **aucune n'a été forcée sous le ventre non plus** : le dire plutôt que de
  le laisser croire.
- **Les tranches de 18 mm des plaques sortent à densité nulle.** 1 542 triangles,
  12,12 m², 175 pièces : ce sont les faces de bord générées par `SOLIDIFY`, dont les UV
  sont dégénérées par construction. Elles prennent la couleur d'une ligne de l'atlas. À
  0,8 px à l'écran, c'est sans conséquence — mais un peintre qui cherche pourquoi une
  tranche est unie a ici sa réponse.
- **Le damier a été rendu et regardé** (`BRIEF-0102-uv-checker.png`, caméra du jeu, 70°
  au-dessus du plan) : les carreaux sont carrés sur le fuselage, les nacelles, les ailes et
  la verrière ; ils sont visiblement plus grands sur la verrière (poids 0,55, donc 1,8×) —
  c'est l'effet voulu, pas une dérive.

## 8. Limites connues, et ce que je n'ai pas obtenu

1. **La capture au bestiaire n'a pas été faite, et je ne pouvais pas la faire.** Habiller
   la coque de l'atlas côté moteur demande de câbler `HullDetailSet` (le champ `albedo`,
   le régime atlas) et d'ajouter les noms de matériaux `MAT | *` à `HullDetail._DETAILED`,
   qui ne connaît que les `AA_*` du kit. C'est du `.gd` et du `.tres` : hors périmètre.
   `BRIEF-0102-avant-apres.png` est la meilleure approximation — même éclairage, même
   angle, mêmes réglages, la carte posée comme le moteur la poserait (couleur neutre,
   tuilage 1).
2. **Le `.glb` livré est plus PAUVRE que celui d'hier tant que l'atlas n'est pas câblé.**
   Il ne porte plus ses six cartes embarquées : elles étaient indexées par les anciennes UV
   et n'auraient plus rien voulu dire. Chaque matériau texturé porte à la place sa couleur
   unie mesurée. **En jeu, la coque lira donc en aplats jusqu'à ce que l'atlas soit posé.**
   C'est le seul état conforme à `ADR-0028` que la forge puisse livrer, mais ce n'est pas
   un état neutre : il vaut mieux câbler l'atlas dans la même passe.
3. **Le dépliage est presque, mais pas tout à fait, reproductible.** Sur trois exécutions,
   deux rendent des UV strictement identiques (et la cuisson qui suit rend le même
   sha256) ; la troisième donne le même remplissage, les mêmes boîtes UV pour les
   406 pièces et les mêmes densités, mais **deux pièces bougent** :
   `L | nozzle dark expansion band.003` de **15 texels** et `HULL | nose optical sensor`
   de **1,6 texel**. `ADR-0047` affirme que `smart_project`
   rend « le même sha256 des UV, au bit près » ; **c'était mesuré sur 40 objets, ça ne tient
   pas tout à fait sur 406.** Conséquence pratique : **l'atlas livré est un contrat.** Si on
   le recuit après avoir peint, deux pièces (toutes deux dans les familles à poids réduit)
   glisseront. Le `.glb` et les cartes doivent voyager ensemble.
4. **La variance locale n'a pas bougé** (202,7 % → 203,5 %). L'atlas ne rend pas la coque
   plus belle ; il rend la peinture possible. Le gain visible se limite aux lignes de
   panneau, désormais géométriquement justes.
5. **Les six PNG extraits par Godot à côté du `.glb`**
   (`assets/imported/models/ships/specter_9_d_*_basecolor.png` et consorts, non suivis par
   git) sont désormais orphelins : le `.glb` ne contient plus d'image à extraire. Ils ne
   gênent rien mais ils ne servent plus à rien.
6. **`assets/source/models/specter_9_d/README.md` mérite un paragraphe** (il dit encore
   « il faudrait d'abord redéplier les 406 pièces en un atlas unique »). Je ne l'ai pas
   touché : il n'est pas dans les livrables du brief.

## 9. Comment rejouer

```sh
blender-aegis -t 1 -b -P tools/blender/unwrap_specter_9_d.py
python3 tools/bake-atlas.py build/specter_9_d_atlas_source.glb --stem specter_9_d \
    --out assets/imported/textures/hull --zones build/specter_9_d_zones.json \
    --plate docs/forge/output/BRIEF-0102-atlas.png --check
blender-aegis -t 1 -b -P tools/blender/unwrap_specter_9_d.py -- --renders
python3 tools/derive-maps.py assets/imported/textures/hull/specter_9_d_height.png   # ADR-0013
```

⚠️ `build/specter_9_d_atlas_source.glb` (le `.glb` de cuisson : deux jeux d'UV et les six
cartes d'origine) **n'est pas versionné** — `build/` est ignoré. Le premier script le
reproduit ; c'est la seule dépendance entre les deux étapes.

## 10. Vérifications passées

- `./scripts/check.sh` : **ALL GREEN** (912 tests, 7 007 assertions, 0 échec).
- `blender-aegis -t 1 -b -P tools/blender/test_atlas_unwrap.py` : **TOUT PASSE**, dont deux
  tests ajoutés — un poids de 0,5 rend un rapport de densité mesuré de **2,000**, et
  `triangulate_first=False` laisse la cage intacte.
- `blender-aegis -t 1 -b -P tools/blender/test_moving_parts.py` : **tout est vert**.
