# BRIEF-0085 — compte-rendu : le décor de survol (lune à cratères + trois astéroïdes)

- **Produit par** : asset-forge
- **Date** : 2026-08-26
- **Brief** : `docs/forge/briefs/BRIEF-0085-survol-de-lune-decor.md`
- **Kit** : `tools/blender/lib/aegis_kit.py` **1.1.0, utilisé sans aucune modification**

---

## 1. Livrables

| Fichier | Ce que c'est |
|---|---|
| `tools/blender/build_moon_flyby.py` | le script de construction — **il EST la source** (ADR-0008), aucun `.blend` |
| `assets/imported/models/backgrounds/moon_flyby.glb` | le décor (LFS) |
| `docs/forge/output/BRIEF-0085-planche-survol.png` | 1920 × 1080 — trois vues **à la perspective du jeu** (t = 0 / 30 / 60 s) + une élévation orthographique avec le plafond matérialisé |
| `docs/forge/output/BRIEF-0085-planche-uv.png` | 1920 × 1080 — **damier UV** à la perspective du jeu (t = 0 et 60 s) + deux gros plans (flanc de cratère, grand bassin) |
| `docs/forge/output/BRIEF-0085-report.md` | ce fichier |

```bash
blender45 -b -P tools/blender/build_moon_flyby.py            # le .glb seul
blender45 -b -P tools/blender/build_moon_flyby.py -- --plate # + les deux planches (Cycles CPU, ~2 min)
./scripts/build-hull.sh --check moon_flyby                   # build + contrôle de déterminisme
```

**Déterminisme** : deux exécutions consécutives, `.glb` byte-identique —
`sha256 93ede16769b62094d7154e2c82f4d57fb9cd2edab2f1b0163cc68f51d0918c94`, 783 656 o.

⚠️ **Passer par `build-hull.sh`, pas par `blender45 -b` à la main.** Le piège documenté dans l'en-tête
du script m'est retombé dessus pendant ce chantier : un build lancé en `-t 4` (pour accélérer le
rendu des planches) produit un `.glb` dont **toutes les mesures sont identiques** — mêmes triangles,
même bbox, mêmes positions — mais dont le sha256 diffère (`a89ac174…`). Ce sont les tangentes
mikktspace, sommées dans un ordre qui dépend du nombre de workers. Le fichier livré est celui du
build **`-t 1`**.

**Aucune texture n'est embarquée** (`ADR-0028`) : deux matériaux en couleur unie, zéro `images`,
zéro `baseColorTexture`, zéro émissif — le harnais d'audit échoue le build si l'un d'eux apparaît.

---

## 2. Mesures relevées **sur le `.glb` produit** (pas sur la scène Blender)

| Nœud | Triangles (budget) | Position lue par le code | bbox X × Y × Z (m) | Sommet Y |
|---|---|---|---|---|
| `Moon` | **11 280** (12 000) | (−0.00, −78.00, +34.00) | 111.93 × 119.83 × 63.20 | **−17.88** |
| `Asteroid_01` | **1 280** (2 500) | (−13.00, −13.00, −18.00) | 8.31 × 10.26 × 8.80 | −8.56 |
| `Asteroid_02` | **1 280** (2 500) | (+15.00, −29.00, +15.00) | 6.56 × 8.60 × 6.02 | −24.80 |
| `Asteroid_03` | **1 280** (2 500) | (+19.00, −34.00, −34.00) | 20.10 × 14.78 × 16.65 | −26.10 |

- **15 120 triangles / 14 340 sommets** au total, 4 maillages, 4 nœuds **racines** (décor plat).
- **Plafond** : le point le plus haut du décor est à **Y = −8.56** (limite −3,00) — 5,6 m de marge.
- **Sommet de la calotte : −17.88** (attendu −18 ± 1), centre implicite (0, −78, 34), rayon 60.
- Rayons réels de la calotte : **56.42 à 61.07 m** — creux max 3,58 m, bourrelet max 1,07 m.
- **`TEXCOORD_0` : 4/4 primitives. `TANGENT` : 4/4.** Compté dans le binaire, jamais supposé.
- Matériaux : `Moon_Regolith` (11 280 t) et `Asteroid_Rock` — **un seul datablock partagé par les
  trois rochers**, comme `TEX-0002` le demande.
- Albédo posé, en **linéaire** : lune (0.115, 0.115, 0.140), roche (0.100, 0.098, 0.118). Ce ne sont
  pas des valeurs inventées : ce sont **exactement** celles que la doublure porte déjà dans
  `moon_flyby.gd` et qui ont été validées en capture. Elles tiennent la fenêtre 0,10–0,13 et sont
  froides (B > R). Mesuré sur la planche (Cycles + AgX, sans le post-traitement rétro du jeu) :
  la surface rend **sRGB (0.458, 0.490, 0.544)**, soit un gris franchement bleu.

**Vérifié dans le moteur** : `./scripts/check.sh` est vert avec le `.glb` en place
(462 tests, 0 échec). Les treize tests de `test_moon_flyby.gd` passent **sur le décor livré et non
sur la doublure** — donc `_collect_bodies()` trouve `Moon` et les trois `Asteroid_*`, et
`test_nothing_rises_into_the_play_field` a mesuré le plafond sur cette géométrie-ci.
Godot a généré `assets/imported/models/backgrounds/moon_flyby.glb.import` (à committer).

---

## 3. La frontière géométrie / texture — le sujet du brief

### 3.1 Ce qui la trace : la tuile fait 55 m, et cela borne des **deux** côtés

- **Par le haut.** Une carte qui se répète tous les 55 m ne peut porter aucune forme de plus d'un
  tiers de tuile sans que la répétition se lise comme un quadrillage. **Tout ce qui dépasse ~16 m est
  donc géométrique par obligation**, pas par goût. C'est l'argument le plus fort de tout ce
  chantier, et il est indépendant de mon jugement.
- **Par le bas.** Le plus gros cratère de `TEX-0001` fait ~9 m et son cratère médian ~2,8 m. En
  dessous de 8 m, la carte fait mieux qu'un maillage à 12 000 triangles, pour un coût nul.

### 3.2 L'échelle livrée

| Famille | Taille | Qui la porte |
|---|---|---|
| grain, piqûres, petits cratères | 0,5 → 9 m | **`TEX-0001`** |
| cratères francs (18) | **8 → 10 m** | géométrie |
| cratères anciens, adoucis (8) | 8 → 10 m, creux 0,26 × rayon | géométrie |
| grands bassins (8) | **16 → 34 m** | géométrie |
| ondulation de fond | 45 → 95 m, ±0,75 m | géométrie |

### 3.3 Le chevauchement à 9 m : tranché, et comment

Le brief demandait de trancher. **J'ai fait les deux choses qu'il proposait, pas une seule :**

1. **Remonté** les cratères géométriques au **sommet** de la fourchette : rayon 4,0 à 5,0, soit
   8 à 10 m de diamètre. Aucun n'est en dessous. Ils ne recoupent donc la famille peinte que sur sa
   **queue extrême** — le plus gros cratère d'une tuile, un par 55 m — et pas sur son gros de la
   distribution (2,8 m).
2. **Espacé** : écartement minimal de 1,25 × (somme des rayons) entre deux creux, plus 14 m de
   dégagement autour des trois points d'impact. Il n'y a nulle part deux familles côte à côte.

Et j'ai ajouté une **troisième séparation, qualitative** : les deux familles ne se ressemblent pas.
Les cratères géométriques ont une **rupture de pente à la crête** (tablier d'éjectas resserré à
1,35 rayon), des **banquettes** sur les plus grands, et surtout ils **mordent la silhouette au
limbe**. Ceux de la carte n'existent qu'en ombrage.

### 3.4 ⚠️ Écart assumé au brief : les bassins dépassent la fourchette « 1,5 à 5 »

Les 18 + 8 **cratères** tiennent la borne (rayon 4,0 à 5,0). Les **8 bassins** la dépassent
franchement (rayon 8 à 17, soit 16 à 34 m de diamètre). Trois raisons, dans l'ordre de force :

1. **La planche de référence est le juge déclaré du chantier** et elle montre un bassin qui occupe
   *un sixième du cadre*. À la distance mesurée (la surface est à **36 m** de la caméra en bas de
   cadre, contre 110 m au limbe), cela vaut ~25 m de surface, pas 10.
2. La leçon « un cratère de rayon 9 lisait comme une **flaque** » a été payée sur la **doublure**,
   dont les cratères étaient des **palets plats posés à R − 0,2**. C'est l'absence de creux qui
   faisait la flaque, pas le diamètre. Les bassins livrés sont creux (1,6 à 3,55 m), terrassés, à
   bord bas, avec pic central sur les deux plus grands — l'exact contraire du palet.
3. Au-delà de 16 m, **la texture ne peut plus rien** (§3.1). Soit la géométrie porte cette échelle,
   soit personne ne la porte, et le limbe reste un arc de cercle parfait pendant soixante secondes.

Si cet écart n'est pas acceptable, il se referme en une ligne : la table `_features()` du script
liste les huit bassins avec leur rayon.

### 3.5 Ce qui a été laissé à la géométrie **malgré** la texture

- **Le limbe** : ondulation de fond ±0,75 m (longueurs d'onde 45 à 95 m) + les creux qui le
  découpent. Aucune carte ne dessine une silhouette.
- **Les grands creux** : ils portent une ombre **réelle** au sens du brief, c'est-à-dire une
  variation d'ombrage due à l'orientation des faces. ⚠️ Les planches sont rendues **sans aucune
  ombre portée** (`visible_shadow = False` sur tous les objets), précisément pour ne pas valider un
  relief qui n'existerait que par une ombre que le jeu ne calcule pas
  (`directional_shadow_max_distance` = 40 m, la lune est à 96 m).

---

## 4. Le dépliage — mesures

### 4.1 Ce qui est livré : une projection **azimutale équidistante**, pas une projection en boîte

`ak.box_project_uv()` est utilisé **pour les rochers seulement**. La calotte porte une projection
azimutale équidistante centrée sur le **milieu de la bande vue** (longitude −83°, latitude 0°), à
l'échelle **55 m par tuile**. Deux propriétés décident :

- **Aucune couture à l'intérieur de la pièce.** C'est une carte **unique et continue** ; sa seule
  discontinuité est l'antipode du centre, à 180°, alors que la calotte s'arrête à 82°.
- L'échelle est **exacte dans la direction radiale partout** ; elle ne dérive que tangentiellement,
  d'un facteur ψ/sin ψ. Un déroulé cylindrique aurait donné 1/cos β, soit **deux fois plus de
  dérive** aux mêmes endroits.

### 4.2 Densité de texels mesurée, triangle par triangle, sur le maillage livré

Méthode : pour chaque triangle, la matrice 2 × 2 qui envoie son plan sur le plan UV, puis ses
**valeurs singulières** — leurs inverses sont les mètres par tuile dans les deux directions
principales. Une moyenne d'aires ne verrait aucun étirement ; celle-ci le voit.

| Domaine | m/tuile (min → max) | Moyenne | Anisotropie max / moyenne | Aire |
|---|---|---|---|---|
| **bande vue, sphère nue** | **43,0 → 56,3** | **53,0** | **1,30** / 1,08 | 1 150 m² |
| bande vue, relief compris | 41,0 → 110,1 | 53,5 | 2,16 / 1,14 | 10 822 m² |
| bande vue, tout | 41,0 → 110,1 | 53,4 | 2,16 / **1,13** | 11 973 m² |
| toute la calotte (ceinture comprise) | 30,9 → 110,1 | 50,9 | 2,25 / 1,25 | 21 924 m² |

**Comment lire ces chiffres — deux causes se superposent et il faut les séparer :**

1. **La projection.** C'est la ligne « sphère nue » : **43 à 56 m/tuile**, cible 55, **anisotropie
   ≤ 1,30**. La tuile est donc au pire 28 % plus dense dans un coin du cadre qu'au centre. C'est
   très loin du « deux fois plus dense » que le brief donne comme seuil de visibilité, et c'est le
   meilleur qu'une carte plane puisse faire sur une bande sphérique de 121° × 99° (théorème de
   Gauss : aucun dépliage n'y est isométrique).
2. **La pente du relief.** C'est ce qui produit les 110 m/tuile : le flanc d'un cratère est plus
   long que sa projection, d'un facteur 1/cos(pente). Sur les murs les plus raides (52° au sommet du
   mur), la tuile s'étire localement de 1,6 × **dans la direction de la pente uniquement**. Ce n'est
   pas un défaut du dépliage : **tout terrain déplacé le fait, quel que soit le dépliage**, et une
   carte de grain isotrope le supporte sans se trahir. La planche au damier permet de le juger —
   c'est exactement ce qu'elle montre sur la vignette « gros plan cratère franc ».

⚠️ La ligne « sphère nue » ne pèse que 1 150 m² : l'ondulation de fond déplace presque toute la
surface au-delà du seuil de 10 cm qui définit « nue ». Elle mesure donc la projection **pure**, pas
une part majoritaire de la calotte.

### 4.3 Où sont les coutures

**Il n'y en a aucune à l'intérieur de la pièce.** Les seules discontinuités du dépliage sont le
**bord** du maillage, qui est :

- en longitude, à **−185°** (derrière l'horizon, sur la face opposée à la caméra, à 41° au-delà du
  limbe le plus tardif) et à **+6°** (sous le bas du cadre, 28° au-delà du bord bas au moment le
  plus favorable) ;
- en latitude, à **±68°**, soit 18,5° au-delà de la latitude la plus extrême jamais vue (±49,5°).

Le maillage n'est pas fermé sur ce bord (ni jupe ni fond) : il est hors champ par construction, et
le fermer aurait coûté ~800 triangles pour une surface qui ne se montre jamais. On le voit sur la
quatrième vignette de la planche de survol, qui regarde le décor de tribord — c'est la seule
manière de le voir.

---

## 5. La forme, et pourquoi elle est une **bande** et non une calotte

Le script **recalcule à chaque build** la région de la lune que la caméra peut voir, en balayant la
rotation, et **échoue si elle sort du cœur maillé**. Mesure du build livré :

- **bande vue** : longitude **−144° à −22,5°**, latitude **±49,5°** — 9 900 m², 21 % de la sphère ;
- **cœur maillé fin** : longitude −147° à −16°, latitude ±56° (mailles de 2,72° × 2,92°, soit
  2,85 × 3,06 m) ;
- **ceinture de sécurité** à mailles larges (6°) jusqu'à −185°/+6° et ±68°.

Trois choses en découlent, toutes mesurées et non supposées :

1. **Le point sous-caméra n'est pas dans le cadre** : il tombe 6,5° sous le bord bas. Ce qu'on voit
   de la lune est une bande comprise entre le bas du cadre et le limbe.
2. **La surface est proche en bas de cadre (36 m) et lointaine au limbe (110 m).** Un cratère de 9 m
   fait ~125 px en bas de cadre et une trentaine, écrasés, près du limbe. C'est ce rapport de 3 qui
   justifie une densité de mailles **uniforme en mètres** : la rotation fait passer chaque parcelle
   par les deux régions.
3. **La rotation déplace la fenêtre** : c'est l'union sur tout le parcours qu'il faut mailler.

⚠️ **Hypothèse de durée, à connaître.** Le brief annonce « ~63° parcourus », ce qui correspond à
**50 s**. La phase, elle, s'arrête au nettoyage de la vague et non à un chronomètre. J'ai maillé fin
pour **60 s (75,6°)**, la borne haute de la fourchette annoncée, et posé la ceinture large pour
qu'une phase deux fois plus longue ne montre jamais un trou — seulement une bande sans cratères.

---

## 6. Le maillage : où passent les 11 280 triangles

Grille structurée en (longitude, latitude), **raffinée localement autour des creux** : 3 × 3 sur la
cuvette et la crête d'un cratère franc (mailles de 0,95 m — dix mailles en travers d'un cratère de
9 m), 2 × 2 sur son tablier d'éjectas et sur les bassins moyens, 1 partout ailleurs. Une maille de
2,9 m ne sait pas dessiner un cratère de 9 m ; à 0,95 m son bord porte enfin une ombre, et la sphère
lisse entre les creux ne coûte rien.

Le point délicat est la **jonction** entre mailles de finesse différente : les sommets de bord d'une
maille subdivisée sont posés **exactement sur la corde du voisin** (interpolation linéaire) au lieu
d'être projetés sur la sphère. Sans cela, la surface s'ouvrirait d'une fente. Le relief est nul à
cet endroit — le raffinement déborde toujours l'emprise du creux — donc l'écart à la sphère vaut
1 cm quand la fente, elle, vaudrait toute la flèche de la maille.

**Les rochers** : icosphère à 4 subdivisions (1 280 triangles chacun), bruit directionnel à basse
fréquence, étirement anisotrope, puis **onze plans de cassure** qui rabattent les sommets sur des
facettes plates. Faces **plates** assumées (`smooth = False`) : une roche cassante n'a pas de normale
continue. UV en projection en boîte à **8 m par tuile, identique sur les trois** — c'est la
contrainte dure de `TEX-0002` et elle est tenue par construction (une seule constante).

---

## 7. Les harnais — tout ce qui suit **échoue le build**

| Harnais | Ce qu'il mesure | Relevé du build livré |
|---|---|---|
| chaîne d'axes | l'identité Godot → auteur → `_AXIS_FIX` → `yup`, sur des témoins **asymétriques** | OK |
| plafond | Y max de chaque nœud, translation comprise | −8,56 (limite −3) |
| sommet | Y max de la calotte | −17,88 (attendu −18 ± 1) |
| budgets | triangles par maillage | 11 280 / 1 280 × 3 |
| UV | `TEXCOORD_0` compté dans le binaire | 4/4 |
| matériaux | aucun émissif, aucune texture, aucune image | OK |
| noms | `Moon` + `Asteroid_01..03` **racines**, aucun enfant | OK |
| couverture caméra | la bande vue tient dans le cœur maillé | OK |
| centre de projection | il reste au milieu de la bande vue (±6°) | OK |
| **dégagement des impacts** | distance du point d'impact au **bord** du relief le plus proche | **12,0 / 11,7 / 13,9 m** (seuil 6) |
| **couverture de la rotation** | nombre de creux **dans le cadre**, tous les 5° | **7 à 16** (seuil 4) |

⚠️ Deux détails du harnais des impacts méritent d'être connus, parce qu'ils sont exactement le genre
de choses qui passent inaperçues :

- Le code calcule le point d'impact en coordonnées **monde**, **à l'instant du choc** — donc après
  que la lune a tourné de `MOON_SPIN × t`. La zone à dégager n'est pas sous le point monde à t = 0 :
  elle est en amont de θ(t), de 13,9°, 32,8° et 50,4° respectivement. Se tromper là, c'est dégager
  trois zones qui ne seront jamais frappées.
- Le harnais de couverture compte dans la fenêtre **instantanée**, pas dans la bande cumulée. La
  première écriture comptait dans la bande cumulée et annonçait « 16 à 28 creux au cadre » là où il
  y en a trois fois moins.

---

## 8. Ce que le concepteur doit savoir pour intégrer

1. ⚠️ **`uv1_scale` doit rester (1, 1, 1).** Les UV portent **déjà** l'échelle : 55 m par tuile sur
   la lune, 8 m sur les rochers. Le `sphere_tiles(MOON_RADIUS, MOON_METRES_PER_TILE)` que la doublure
   applique à sa `SphereMesh` ferait ici tuiler la carte **6,9 fois de trop en u et 3,4 en v**. C'est
   le piège d'intégration numéro un de cette livraison.
2. Les matériaux à habiller s'appellent **`Moon_Regolith`** (→ `TEX-0001`) et **`Asteroid_Rock`**
   (→ `TEX-0002`, **partagé** par les trois rochers : un seul matériau à dresser).
3. `Moon` est un `MeshInstance3D` **posé à (0, −78, 34)**, c'est-à-dire au centre de la sphère : le
   `rotate_x()` du code tourne donc la calotte **sur elle-même**, exactement comme le pivot de la
   doublure. ⚠️ Le brief écrit « `Moon` … à l'origine du décor » ; je l'ai lu comme « au sommet de la
   hiérarchie », **pas** comme « à (0,0,0) ». Un `Moon` posé à l'origine ferait décrire à la calotte
   un arc de 85 unités de rayon autour du monde à chaque image.
4. Les trois rochers gardent **les positions et rayons de la doublure** (déjà réglés en capture,
   `Asteroid_02` compris, qui avait été écarté du couloir de vol). Le code déduit leur vitesse de
   dérive de `position.y` : ces translations sont donc du **gameplay visuel**, pas de la mise en page.
5. Rien dans le `.glb` n'est animé, n'a de collision ni d'émissif.

---

## 9. Ce qui a été rendu et regardé (ADR-0006)

Les deux planches sont rendues **avec l'éclairage réel du jeu** : les trois directionnelles de
`graybox.tscn` (directions, énergies et couleurs relevées sur le fichier, converties en soleils
Cycles par le facteur π), l'ambiante `space_environment.tres` (0,55 / 0,62 / 0,78 × 0,8) posée en
monde, le fond `#070A12`, la caméra à (0, 14, 5) plongeant de 70°, FOV 62 vertical, 1920 × 1080 —
et **aucune ombre portée**, comme en jeu.

Ce que j'y ai vu, et corrigé, en trois passes :

1. **Première passe : la lune rendait LISSE.** Cratères à 0,36 rayon de profondeur, tablier étalé
   jusqu'à 1,55 rayon : rien ne se lisait. La cause est mesurable — la KeyLight arrive **de derrière
   la caméra**, à 55° au-dessus de l'axe de visée ; l'éclairage est frontal et une pente douce n'y
   fait aucune ombre. Correction : profondeur 0,42 rayon, bourrelet 0,105, **tablier resserré à
   1,35 rayon** (c'est la rupture de pente à la crête qui porte la lecture), ondulation de fond
   ×1,6, et 34 creux au lieu de 24.
2. **Deuxième passe : le gros plan du damier ne montrait pas son cratère.** Il visait le plus grand
   cratère du catalogue, posé à −127° de longitude — une zone que **seule la troisième lumière**
   effleure. Le damier s'y lisait, le relief non. Les gros plans visent désormais dans la fenêtre
   réellement vue à l'entrée dans la phase.
3. **Troisième passe : les légendes de l'élévation orthographique étaient invisibles** (taille
   exprimée en mètres, cadre de 84 m). Elles sont maintenant en **fraction de cadre**, ce qui vaut
   pour les six caméras des planches, de 18° de champ à l'orthographique.

**Lisibilité du jeu par-dessus la surface** (critère final du brief) : le Specter-9 réel et deux
Choir Mines réelles sont dans le cadre, à leur taille et à leur place de jeu — ce n'est pas une
décoration, c'est le repère d'échelle (`ADR-0025`) et le test de lisibilité. Mesuré sur la vignette
t = 0 s : surface sRGB (0.458, 0.490, 0.544), chasseur jusqu'à (0.863, 0.878, 0.894), mines magenta
saturées. **Le chasseur et les mines se lisent**, sans le glow ni le post-traitement rétro du jeu qui
ne feront qu'aider.

---

## 10. Limites connues, réserves, et ce que je n'ai pas pu faire

1. **Le relief géométrique reste discret sous l'éclairage frontal du jeu.** C'est mesurable et c'est
   structurel : sans ombre portée et avec une lumière venue de derrière la caméra, un creux de 2 m
   sur 9 ne produit qu'un écart d'ombrage modeste, encore comprimé par le tonemap AgX. Les planches
   montrent la géométrie **seule** — c'est le pire cas. `TEX-0001` (normale + AO + multiplication)
   ajoutera par-dessus la couche que la géométrie ne peut pas payer. **Si, capture en main, le
   relief manque encore**, le levier le moins cher est `SURFACE_NORMAL_SCALE` puis `TEX-0003` (les
   éjectas clairs), pas un maillage plus dense.
2. **Densité de creux.** 7 à 16 grands creux au cadre, contre les quarante et quelques de la planche
   de référence. C'est un choix : la carte en apporte 20 à 30 **par tuile**, soit ~150 sur le cadre.
   L'addition doit donner la surface criblée de la référence ; **cela ne se vérifiera qu'en jeu**.
3. **Le tonemap de mes planches n'est pas celui du jeu de bout en bout.** AgX est commun aux deux,
   mais le jeu ajoute glow, `adjustment_*` et le post-traitement rétro (warmth/saturation) qui
   réchauffe tout gris neutre — le piège documenté du « rose pâle ». Mes valeurs sRGB sont donc un
   ordre de grandeur, pas une prédiction.
4. **Durée de la phase** : voir §5. Au-delà de 60 s, le limbe montre la ceinture large, sans creux.
5. **`ak.export_hull()` n'est pas utilisé**, et ce n'est pas un choix de confort — c'est une
   incompatibilité de contrat, vérifiée dans le code du kit, que je documente parce qu'elle
   resservira au prochain décor :
   - il exporte **une** coque maillée dont le nœud reste à l'origine ; or les quatre corps d'ici
     portent chacun une **translation que le moteur relit** (`drift_speed_at(body.position.y)`) ;
   - son contrôle d'orientation compare le Y d'auteur des sommets **locaux** au Z du glTF
     **translation comprise** : il n'est vrai que si le nœud de la coque est à l'origine, donc
     échanger les rôles (lune en pièce mobile, rocher en coque) ne le sauve pas ;
   - il exige en outre un pivot centré à 2 cm près et une bbox largeur × longueur imposée, deux
     notions sans objet pour un décor de 160 m.

   L'export et la validation sont donc **refaits dans le script**, à l'identique sur le fond : même
   correction d'axe, même relecture du `.glb` **produit**, même règle « au moindre écart, on échoue ».
   Le kit n'est pas modifié d'une ligne. **Si cette limite doit disparaître**, la plus petite
   modification utile du kit serait un `export_decor(bodies, ...)` où chaque corps porte son pivot et
   où le contrôle d'orientation se fait sur les sommets **monde**.
6. **Les matériaux ne sont pas ceux de `MATERIAL_ORDER`.** Aucune couleur de la charte ne convient :
   les palettes y sont des palettes de **faction**, et la lune n'en a pas ; la valeur imposée par la
   lisibilité (0,115 linéaire) ne correspond à aucune entrée. J'ai donc posé deux matériaux dédiés,
   en reprenant **exactement** les couleurs déjà validées en capture dans `moon_flyby.gd`. Si la
   nomenclature doit être respectée malgré tout, c'est une décision de charte, pas de forge.
7. **Aucune couleur de sommet.** Un `COLOR_0` aurait donné aux fonds de cratère l'assombrissement
   d'albédo que le brief appelle de ses vœux, sans être une texture — mais il ne prend effet que si
   le matériau active `vertex_color_use_as_albedo`, ce que `dress()` ne fait pas, et il contredirait
   le « couleur unie » du brief. Piste laissée ouverte, non prise.
