# BRIEF-0098 — Specter-9 Talvern : la cellule-témoin, **la plus belle des trois coques**

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal (session Fable 5.1)
- **Date** : 2026-09-04
- **Décision** : [`ADR-0044`](../../decisions/ADR-0044-la-cellule-temoin-troisieme-coque-sans-plafond.md) — **à lire avant la charte** : il amende le plafond de triangles et étend le contrat des pièces mobiles
- **Plan** : `docs/plans/2026-09-04-specter-9-talvern-la-cellule-temoin.md`

## Objectif

Construire **une troisième coque du Specter-9**, `specter_9_c`, la plus détaillée et la plus
belle des trois — celle contre laquelle l'Arsenal mesure les autres. Même architecture que la coque
en service (c'est **la même unité**, `ADR-0014` s'applique tel quel), même contrat de gameplay
(1,75 × 2,46 m), mais **exécutée sans compromis** : chaque cassure de panneau est un vrai creux
biseauté, chaque mécanisme est une pièce qui bouge sur sa charnière, la verrière laisse voir un
cockpit, et chaque tuyère est **douze pétales** qui s'ouvrent.

Demande de l'opérateur, telle quelle :

> « Je veux le plus beau que tu puisses réaliser, sans aucune restriction. Un vaisseau magnifique,
> très détaillé, beaucoup de détails, beaucoup de polygones. Et en plus, micro-animé : les ailes
> qui se rétractent, les volets qui bougent, les tuyères qui s'ouvrent et qui se ferment, et
> caetera. Vraiment le plus beau des trois. »

## Contexte — ce qui existe, et ce qu'il faut lire

| Lire | Pourquoi |
|---|---|
| `assets/reference/inspiration/specter_9_multi_angle_turnaround.png` | **la source de forme** : sept vues (dessus, dessous, face, profils, arrière, trois-quarts). C'est elle qu'on met côte à côte avec ton rendu |
| `assets/reference/inspiration/reference_specter_9_design_sheet.png` | les **systèmes** : aérofreins dorsaux, entrées d'air variables, poussée directionnelle, grappins d'appontage avant, rail magnétique dorsal, cockpit |
| `assets/reference/concepts/specter_9_concept_sheet.png` | notre planche : le **langage de panneaux** (blanc cassé / bleu profond / or) et les tuyères rondes |
| `tools/blender/build_specter_9.py` | **le plan de départ.** Le partage de la demi-envergure (fuselage 0,15 / fente / nacelle / fente / emplanture / aile), l'emplanture polaire de BRIEF-0036, les pétales, les dix points d'attache, le déterminisme. **Repars de ses cotes**, pas de zéro — ce plan a coûté six briefs |
| `docs/forge/output/BRIEF-0035-report.md`, `BRIEF-0036-report.md` | comment les dégagements se **mesurent à chaque build** et pourquoi le build échoue en dessous |
| `.claude/resources/pratique-detail-en-fraction-de-corde.md` | tout détail en fraction de la géométrie porteuse, jamais en coordonnée absolue |
| `.claude/resources/pratique-revue-asset.md` | le rendu studio flatte ; le rétro écrase le détail fin ; l'émissif au-delà de ~10 % est une livrée |
| `docs/forge/textures/README.md` §plancher de modulation | **un détail sous ~6 niveaux de gris n'existe pas dans ce jeu** |

Ce que le jeu fait de cette coque : **~48 px en combat** (caméra à 20° de la verticale, légèrement
en arrière — on voit le dos et les tuyères), **gros plan à l'accueil** (quatre chasseurs, éclairage
trois points) et **bestiaire** (rotation libre à la souris, zoom — la seule vue où le ventre existe).

## Ce que « le plus beau » veut dire ici — la direction

Le post-traitement rétro (960×540, postérisation à 20 niveaux) est un filtre qui **ne garde que ce
qui ombre**. La beauté demandée ne peut donc pas venir du micro-détail ni d'une texture fine : elle
vient de **trois échelles**, et chacune a sa place.

| Échelle | Ce que c'est | Où elle se lit | Règle |
|---|---|---|---|
| **1 — silhouette et volumes** | fuselage porteur, deux nacelles, ailes en lames, doubles dérives, nez effilé, verrière longue | 48 px, combat | **la planche de référence, masses à la même place.** Contour non convexe (les échancrures de BRIEF-0035 restent) |
| **2 — cassures de panneaux** | lignes de panneau **creusées** (3-6 mm, biseautées), panneaux bleus **en retrait** d'un pas, arêtes de coque **biseautées à 2-3 segments** qui accrochent la lumière | accueil, bestiaire | **assez profond pour ombrer** : une rainure qui ne module pas 6 niveaux de gris après postérisation n'existe pas. Vérifie-le en rendant AVEC un contraste réduit (20 niveaux) |
| **3 — mécanique** | pétales, charnières, carters, vérins dans les baies, rangs de fixations, cockpit | bestiaire, zoom | **uniquement dans les zones techniques** : cadre de verrière, couronnes de tuyère, carters d'emplanture, intérieurs de baie, rail dorsal. **Un chasseur est lisse ; ses zones techniques sont denses.** Jamais de greeble semé sur une peau propre |

Où va l'œil, dans l'ordre — c'est là que tu dépenses : **1. la verrière et le cockpit**, **2. les
tuyères** (le point focal arrière, vu en jeu), **3. l'emplanture et la racine d'aile**, **4. le rail
dorsal et les aérofreins**, 5. les dérives, 6. les entrées d'air, 7. le ventre.

## Le plan, panneau par panneau (repère d'auteur : nez −Y, dessus +Z, **bâbord +X**)

Repars des tables de `build_specter_9.py` (`PLANFORM`, `FUSELAGE`, `NACELLE_*`, `WING_*`,
`GLOVE_*`, `FIN`) — **les cotes peuvent bouger de quelques centimètres**, le partage de la
demi-envergure et les fentes traversantes ne bougent pas.

1. **Nez et fuselage.** Nez effilé, arête dorsale continue du nez aux dérives. Le fuselage est un
   **volume** (flancs verticaux, pas une bande). Sur le dos, en arrière de la verrière : le **rail
   magnétique dorsal** — un chenal en retrait, `AA_Greeble`, avec deux filets `AA_Emissive_Engine`
   fins au fond. C'est le seul émissif dorsal autorisé hors tuyères.
2. **Verrière et cockpit.** Verrière longue, en goutte, **cadre `AA_Trim`** à trois montants,
   vitrage `AA_Glass`. **Dedans, un cockpit** : le pilote est en **décubitus ventral** (fiche du
   bestiaire) — donc pas un siège mais un **berceau** incliné, un arceau de visée devant, deux blocs
   de console latéraux, en `AA_Greeble` avec deux ou trois fentes émissives de 1 cm. Le cockpit est
   dans le maillage principal. ⚠️ Je vérifierai **dans Godot** que l'intérieur se voit à travers
   `AA_Glass` ; rends-le aussi dans ta planche (vitre rendue transmissive).
3. **Emplanture et ailes.** L'emplanture fixe polaire de BRIEF-0036 (le pivot enfoui). **Sur son
   dos, un carter de pivot** démontable : platine `AA_Trim`, quatre fixations. Les ailes sont des
   **lames** à profil réel (bord d'attaque rond, bord de fuite fin), avec **un panneau bleu en retrait
   sur l'extrados**, une rainure de longeron, et le **pod de bout d'aile** (canon `Muzzle_Tip_*`) avec
   un feu de position émissif de 1 cm.
4. **Volets** : enfants des ailes, comme aujourd'hui, avec leurs deux charnières visibles côté
   intrados.
5. **Nacelles.** Corps fermés, séparés du fuselage par les fentes de BRIEF-0035. **Entrée d'air** en
   avant : lèvre oblique, gorge `AA_Greeble`, et **une rampe mobile** (`Intake_*`) sur la lèvre
   supérieure. Trois anneaux de panneau creusés sur la longueur. **Tuyère** en arrière : le corps de
   tuyère et sa couronne sont **dans le nœud `Nozzle_*`**, pas dans la coque — un fond de chambre
   `AA_Emissive_Engine`, un anneau `AA_Trim`, et **douze pétales** enfants.
6. **Dérives** : deux, inclinées à ~30°, fixes, dans la coque. Chacune porte une **gouverne**
   mobile (`Rudder_*`) sur son bord de fuite, avec sa charnière.
7. **Aérofreins dorsaux** : deux panneaux (`Airbrake_*`) sur le dos, de part et d'autre du rail,
   entre la verrière et les dérives. Charnière **avant**, ils s'ouvrent vers le haut. **Sous
   chacun, une baie** `AA_Greeble` avec son vérin (deux cylindres emboîtés) — c'est là que
   `TEX-0018` vivra.
8. **Ventre.** Les deux tubes du canon de nez (`Muzzle_L/R`) et le canon d'axe (`Muzzle_C`), la
   quille. **Deux grappins d'appontage** (`Grapple_*`) sous le nez, **repliés à plat contre la
   quille** au repos, pointe vers l'arrière. Deux bandes de hachures `AA_Marking_Red` **sans
   texte** au bord des baies de grappin.

## Les pièces mobiles — noms figés, pivots, sens, cibles

Tout ce qui bouge est un `ak.moving_part()` avec **son pivot sur sa charnière**. Le contrat
d'`ADR-0044` §3 : `ShipFlight` anime ce qu'il trouve par son nom exact.

| Nœud | Parent | Charnière (repère d'auteur) | Pose de repos | Plafond mécanique **mesuré à chaque build**, build **ÉCHOUE** en dessous de |
|---|---|---|---|---|
| `Wing_L`, `Wing_R` | coque | axe **vertical** au flanc externe de nacelle | déployée (0°) | flèche **≥ 30°** (peau de nacelle, bbox, fuselage — les trois contraintes de BRIEF-0035) |
| `Flap_L`, `Flap_R` | `Wing_*` | ligne de constante `y` (le long de X) | 0° | **±14°** (cloison d'échancrure, emplanture) |
| `Nozzle_L`, `Nozzle_R` | coque | **⚠️ pivot SUR L'AXE de la tuyère, dans le plan des charnières de pétales** — `ShipFlight` dérive l'axe de chaque pétale de sa position radiale dans ce repère | — | lacet vectoriel **±6°** sans toucher la nacelle |
| `Petal_L_00..11`, `Petal_R_00..11` | `Nozzle_*` | tangente au cercle des charnières, à la couronne | **fermés**, jeu angulaire ~2,4° entre pétales | ouverture **≥ 20°** vers l'extérieur, sans se croiser ni toucher la nacelle |
| `Airbrake_L`, `Airbrake_R` | coque | charnière **avant**, le long de X | fermé, affleurant | **≥ 55°** (dérives, verrière) |
| `Intake_L`, `Intake_R` | coque | charnière avant de la lèvre supérieure, le long de X | fermée | **≥ 12°** |
| `Rudder_L`, `Rudder_R` | coque | **l'axe de la dérive**, incliné du même angle qu'elle — **donne le vecteur d'axe dans le repère Godot** | 0° | **±22°** |
| `Grapple_L`, `Grapple_R` | coque | charnière arrière, le long de X, sous le nez | replié à plat vers l'arrière | **≥ 90°** (pendant vers le bas, sans toucher les tubes de canon) |
| `Canopy` | coque | charnière **arrière**, le long de X | fermée | **≥ 35°** (arête dorsale, aérofreins fermés) |

⚠️ Pour **chaque famille**, le rapport donne **l'axe Godot et le signe qui OUVRE** (mesuré sur le
`.glb`, pas déduit — BRIEF-0035 a documenté qu'un même signe des deux côtés envoyait une aile vers
le nez). Le code sera écrit sur tes chiffres.

⚠️ **La bbox du contrat est mesurée AU REPOS.** Une pièce qui déborde une fois ouverte le passerait
sans un mot — d'où la table de plafonds ci-dessus, remesurée à chaque build sur le maillage livré,
comme `_wing_sweep_limit()` et `_glove_clearance()` le font aujourd'hui. Ajoute une **table de
dégagements** au rapport : pour chaque couple (pièce ouverte × pièce voisine), le jeu minimal en mm.

## Points d'attache — les dix d'`ADR-0008`, inchangés

`Muzzle_L`, `Muzzle_R`, `Muzzle_Wing_L`, `Muzzle_Wing_R`, `Muzzle_C`, `Muzzle_Tip_L`,
`Muzzle_Tip_R`, `Engine_L`, `Engine_R`, `Cockpit`. Le contrôleur les lit **par leur nom dans la
coque** (`_cache_muzzles`) : leurs positions sont libres, leur présence ne l'est pas — le `.glb`
se monte **nu**, sans scène d'ajustement. `Engine_*` au **fond de chambre** de chaque tuyère (la
plume part de là). `Muzzle_Wing_*` sur les ailes **mobiles** : c'est acceptable aujourd'hui (la
coque en service fait pareil), les positions sont lues au repos.

## Contraintes

- **IP** (`ADR-0014`, `ADR-0044` §5) : le plan et les dérives de la planche sont repris ; **exclus** :
  la livrée tricolore, le badge numéroté, tout texte, insigne, chiffre ou marquage lisible. Les
  hachures rouges sans texte sont autorisées, à dose de marquage restreint.
- **Palette** : les sept matériaux `AA_*`, palette `vanguard`. Répartition **mesurée en aire** au
  rapport, cibles : `AA_Hull` 55-70 %, `AA_Panel` 12-20 %, `AA_Greeble` 8-15 %, `AA_Trim` **≤ 4 %**,
  `AA_Glass` ~2 %, `AA_Emissive_Engine` **≤ 3 %**, `AA_Marking_Red` **≤ 1 %**. Au-delà des plafonds,
  c'est une livrée.
- **Dimensions** : 1,75 × 2,46 m à ±3 %, **ailes déployées** ; hauteur **0,62-0,72 m** dérives
  comprises ; pivot au centre, sur le plan de jeu.
- **Budget** : `tri_budget = 400_000` — un **garde-fou d'accident**, pas une cible. Rapporte le
  compte réel, par pièce. Biseaux à 2-3 segments partout sur la peau, plus sur les couronnes de
  tuyère et le cadre de verrière ; `shade_smooth_by_angle`. Godot génère les LOD à l'import : tu
  n'en fais aucun.
- **Déterminisme** : `./scripts/build-hull.sh --check specter_9_c` vert. Une seule graine.
- **Kit** : `aegis_kit.py` peut recevoir de **nouvelles fonctions** (profil d'aile, pétale, vérin,
  dépliage cylindrique) — **jamais une modification d'une fonction existante** : quinze scripts en
  dépendent. Incrémente `VERSION`.
- **Détail en fraction** de la géométrie porteuse, jamais en coordonnée absolue.

## Texture (ADR-0028 — OBLIGATOIRE)

**L'asset dépend de trois demandes, générées par l'opérateur, câblées par le concepteur** — tu ne
produis aucune image et tu n'appliques aucune texture. Ton travail est le **dépliage** :

| Demande | Zone | Dépliage attendu |
|---|---|---|
| `docs/forge/textures/TEX-0017-specter-borde-composite.json` | tout ce qui n'est pas tuyère ni intérieur de baie (`AA_Hull`, `AA_Panel`, `AA_Trim`, `AA_Marking_Red`) | `ak.box_project_uv()` à **2,5 tuiles/m** (0,40 m par tuile) |
| `docs/forge/textures/TEX-0018-specter-mecanique-de-baie.json` | intérieurs de baie d'aérofrein, logements de grappin, gorge d'entrée d'air, baie de cockpit (`AA_Greeble`) | boîte à **4 tuiles/m** |
| `docs/forge/textures/TEX-0019-specter-metal-de-tuyere.json` | **les nœuds `Nozzle_*` et `Petal_*`** en entier | dépliage **cylindrique** autour de l'axe de tuyère, `u` sur la circonférence (2 tuiles au tour), `v` le long de l'axe à la même densité |

Le moteur pose le jeu **par nœud** (`HullDetail` — tuyères et pétales d'un côté, coque de
l'autre) : c'est pour ça que le corps de tuyère doit être dans `Nozzle_*`. Déplie chaque zone
**avant** de joindre, la densité doit être homogène dans chaque zone (mesure-la : moyenne et
anisotropie, comme BRIEF-0089). **`TEXCOORD_0` compté dans le `.glb`**, tangentes exportées.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/build_specter_9_c.py` | le script — la source de l'asset |
| `tools/blender/lib/aegis_kit.py` | **seulement** si des fonctions neuves y sont ajoutées |
| `assets/imported/models/ships/specter_9_c.glb` | coque + pièces mobiles + dix points d'attache (LFS) |
| `docs/forge/output/BRIEF-0098-planche-quatre-vues.png` | `render-hull.py` : game, dessus, profil, trois-quarts |
| `docs/forge/output/BRIEF-0098-planche-reference.png` | **ta vue de dessus à côté de la planche de référence, à la même hauteur** — c'est la vérification qu'`ADR-0014` exige |
| `docs/forge/output/BRIEF-0098-planche-mecanismes.png` | **chaque famille mobile à ses deux extrêmes** (repos / plafond), une ligne par famille |
| `docs/forge/output/BRIEF-0098-planche-cockpit.png` | gros plan verrière, vitre transmissive |
| `docs/forge/output/BRIEF-0098-planche-aplat-noir.png` | silhouette de dessus, ailes déployées et à 26° |
| `docs/forge/output/BRIEF-0098-planche-uv.png` | damier UV, les trois zones |
| `docs/forge/output/BRIEF-0098-report.md` | mesures : bbox, triangles par pièce, aire par matériau, **table des plafonds**, **table des dégagements**, **axe + signe d'ouverture par famille**, densités UV, déterminisme, limites connues |

## Provenance

Une ligne dans `assets/licenses/ASSET_PROVENANCE.csv` pour le `.glb` et une par planche livrée
(`source_tool` = `asset-forge (Claude)`, `prompt_file` = ce brief). Mentionner `ADR-0044` et
`ADR-0014` dans la note du `.glb`.

## Critères d'acceptation

- [ ] Vue de dessus **côte à côte avec la planche** : masses à la même place — fuselage porteur,
      nacelles, lames, dérives ; contour **non convexe**
- [ ] **Les 48 nœuds mobiles** existent avec leurs noms exacts, pivot sur charnière, parentage
      conforme (`Flap_*` sous `Wing_*`, `Petal_*` sous `Nozzle_*`)
- [ ] Table des plafonds : **tous au-dessus des cibles**, remesurés à chaque build, build rouge en
      dessous
- [ ] Table des dégagements : aucune interpénétration, à aucun extrême, pour aucun couple
- [ ] Axe Godot et signe d'ouverture **mesurés** par famille
- [ ] Cockpit visible à travers la verrière sur la planche
- [ ] Répartition des matériaux dans les cibles — émissif ≤ 3 %, or ≤ 4 %, rouge ≤ 1 %
- [ ] Bbox 1,75 × 2,46 ±3 % au repos, hauteur 0,62-0,72, pivot centré, 10 points d'attache
- [ ] Triangles **≤ 400 000**, compte réel rapporté par pièce
- [ ] **UV présentes et `TEXCOORD_0` COMPTÉ dans le `.glb`** ; densités mesurées pour les trois
      zones ; dépliage cylindrique sur `Nozzle_*`/`Petal_*`
- [ ] `./scripts/build-hull.sh --check specter_9_c` vert
- [ ] Aucun texte, chiffre, insigne, livrée
- [ ] Les six planches livrées, **regardées** par toi avant le rapport

## Hors périmètre

Ne pas toucher au code Godot (`scripts/`, `scenes/`, `resources/`), ni aux deux coques existantes
(`build_specter_9.py`, `specter_9.glb`, `specter_9_b.*`), ni générer une texture. Pas de `.blend`.
Pas de train d'atterrissage (la planche apponte par grappins et rail). Pas de LOD.
