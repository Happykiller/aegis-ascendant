# BRIEF-0098 — Rapport : le Specter-9 Talvern, la cellule-témoin

- **Agent** : asset-forge (Claude)
- **Date** : 2026-09-04
- **Brief** : `docs/forge/briefs/BRIEF-0098-specter-9-talvern-cellule-temoin.md`
- **Lu au préalable** : `docs/forge/CHARTE_CREATIVE.md`, `ADR-0044`, le brief, `tools/blender/build_specter_9.py`
  (le plan de départ), `tools/blender/lib/aegis_kit.py`, `BRIEF-0035-report.md`, `BRIEF-0036-report.md`,
  les trois planches de référence, `pratique-detail-en-fraction-de-corde.md`, `pratique-revue-asset.md`,
  `docs/forge/textures/README.md`, `TEX-0017/0018/0019`.
- **Section `## Texture` du brief** : présente (ADR-0028). L'asset dépend de `TEX-0017` (bordé, boîte
  2,5 tuiles/m), `TEX-0018` (baies, boîte 4 tuiles/m), `TEX-0019` (tuyères, cylindrique 2 tuiles au tour).
  Aucune texture livrée ; les UV le sont, comptées.

---

## 0. Livrables

| Fichier | Rôle |
|---|---|
| `tools/blender/build_specter_9_c.py` | **la source** de l'asset (ADR-0008), 2 950 lignes, déterministe |
| `tools/blender/lib/aegis_kit.py` | **1.2.0** — huit fonctions **ajoutées**, aucune existante modifiée : `add_tube`, `add_actuator`, `airfoil_half_thickness`, `box_project_uv_by_material`, `cylinder_project_uv`, `texel_density`, `glb_accessor`, `glb_primitives` |
| `assets/imported/models/ships/specter_9_c.glb` | coque + **39 pièces mobiles** + 10 points d'attache, **4 749 320 o**, sha256 `3e2e55a1a6f4d69ae8a7d358253c47d477ba12f1f88375128c68aef6a905a30c` (LFS) |
| `docs/forge/output/BRIEF-0098-planche-quatre-vues.png` | `render-hull.py` : jeu, dessus, profil, trois-quarts |
| `docs/forge/output/BRIEF-0098-planche-reference.png` | vue de dessus **à côté** de la vue TOP du turnaround, même longueur |
| `docs/forge/output/BRIEF-0098-planche-mecanismes.png` | 9 familles × (repos / cible / plafond ou −cible) |
| `docs/forge/output/BRIEF-0098-planche-cockpit.png` | verrière fermée (vitre transmissive) et ouverte à 35° |
| `docs/forge/output/BRIEF-0098-planche-aplat-noir.png` | silhouette de dessus, ailes déployées et à 26° |
| `docs/forge/output/BRIEF-0098-planche-uv.png` | damier UV, les trois zones |
| `assets/licenses/ASSET_PROVENANCE.csv` | 7 lignes ajoutées (le `.glb` et les six planches) |

**Déterminisme** : `./scripts/build-hull.sh --check specter_9_c` → *déterminisme OK*, deux exécutions
byte-identiques (`3e2e55a1…`). Build complet, mesures BVH comprises : ~5 s.

**Aucun fichier de `scenes/`, `scripts/`, `resources/`, ni les deux coques existantes, n'a été touché.**
`./scripts/build-hull.sh specter_9` a été lancé deux fois pour un test (voir §9.1) et le fichier LFS
committé a été **restauré** (`git checkout`) : `git status` ne montre que les livrables ci-dessus.

---

## 1. Ce que la coque est

La **même unité** que `specter_9.glb` : le plan de `build_specter_9.py` est repris tel quel — partage de
la demi-envergure (0,130 / fente 42 mm / nacelle 0,172–0,368 / fente 58 mm / aile jusqu'à 0,875),
fentes traversantes, emplanture polaire de BRIEF-0036, pivot d'aile enfoui, dix points d'attache. Les cotes
qui bougent sont justifiées en commentaire dans le script, à l'endroit où elles bougent.

Ce qui change, c'est l'exécution, dans l'ordre du brief :

1. **Verrière et cockpit** — verrière en goutte, pièce mobile `Canopy` (charnière arrière), bulle
   `AA_Glass`, deux longerons de base et **trois montants** `AA_Trim`. Dessous, un **puits de 40 mm**
   (seuil doré, parois sombres) avec un **berceau incliné** (décubitus ventral), un **arceau de visée**,
   **deux consoles** latérales, et cinq fentes émissives de 1 cm (2 par console, 1 sur l'arceau).
2. **Tuyères** — la nacelle se termine en **douille creuse** (rebord 0,985, fond 0,925) ; le nœud
   `Nozzle_*` contient **le corps entier** : col à rotule dans la douille, évasement, six bossages,
   **anneau doré**, **chambre émissive** à axe relevé. Pivot **sur l'axe, dans le plan des charnières**
   (y = 1,048). **Douze pétales** enfants, charnière sur la peau externe (r = 0,093), pied 3 mm en arrière
   du col, peau externe blanche, faces internes et raidisseur sombres, lèvre de sortie dorée. Les pétales
   du haut sont raccourcis de 70 mm (la chambre se voit à 20° de la verticale).
3. **Emplanture et ailes** — emplanture BRIEF-0036 inchangée ; **carter de pivot** démontable (embase,
   platine dorée, **quatre fixations**). Lames à **profil de voilure** (`airfoil_half_thickness`, maître-
   couple à 32 % de corde), deux rainures de longeron, trois panneaux bleus en retrait, **pod de bout
   d'aile** (lathe, feu de position de 1 cm), deux paliers de charnière de volet sous l'intrados.
4. **Volets** — enfants des ailes, deux ferrures visibles côté intrados.
5. **Nacelles** — **entrée d'air oblique** (le haut 32 mm en avant du bas), lèvre dorée, gorge sombre,
   cône central ; **rampe mobile** `Intake_*` sur la lèvre supérieure ; **trois anneaux de panneau
   creusés** (−3 mm de rayon, bordés de deux marches) au lieu de bandes peintes ; 32 segments.
6. **Dérives** — pied à corde pleine (noyé dans la nacelle jusqu'à s = 0,26), partie haute au bord de
   fuite **échancré en arc concave** concentrique à la charniere ; **gouverne** `Rudder_*` à nez rond
   (34 % de corde, 5 mm de jeu), axe = l'axe de la dérive.
7. **Aérofreins** — deux trappes conformes au pont sur la tablette de joue (segments 0-2), charnière
   avant ; **baie** de 22 mm `AA_Greeble` avec **vérin** (deux cylindres emboîtés, chapes) et deux nervures.
8. **Ventre** — canon (tubes + `Muzzle_C`), quille, **grappins** sur chape (joues dans la coque,
   tourillon coaxial), logements de 4 mm dans le flanc de quille, **cinq hachures rouges sans texte** par
   logement. C'est le seul rouge de la coque (avec un témoin de 3 cm sur le bloc dorsal).
9. **Rail dorsal** — chenal de 16 mm creusé dans l'arête, **deux filets émissifs de 7 mm** au fond.

Détail **uniquement** dans les zones techniques : aucun greeble semé sur la peau (les bandeaux de
greebles du pont, de la joue et du nez de la coque en service sont supprimés ; il reste ceux du dessus des
caissons de liaison).

---

## 2. Contrat du `.glb` livré (relu sur le fichier)

| Grandeur | Valeur | Contrat |
|---|---|---|
| Largeur X (Godot) | **1,7500 m** | 1,75 ± 3 % ✔ |
| Longueur Z | **2,4600 m** | 2,46 ± 3 % ✔ |
| Hauteur Y | **0,6512 m** (26,5 % de la longueur) | 0,62 – 0,72 ✔ |
| Centre | (−0,0000, −0,0264, +0,0000) | pivot centré X/Z ✔ |
| Triangles | **102 738** | garde-fou 400 000 (26 %) ✔ |
| Sommets / primitives | 83 820 / 116 | — |
| Matériaux | 7 / 7, couleurs unies, aucune texture | ✔ |
| `TEXCOORD_0` | **116 / 116 primitives**, compté | ✔ |
| Tangentes | exportées (`export_tangents=True`) | ✔ |
| Points d'attache | 10 / 10 | ✔ |
| Pièces mobiles | **39** nœuds, noms exacts, parentage conforme | ✔ (voir §9.2 sur « 48 ») |
| Texte, chiffre, insigne, livrée | aucun | ✔ |

Points d'attache (Godot X, Y, Z) : `Muzzle_L/R` (∓0,042, −0,068, −1,070), `Muzzle_C` (0, −0,068, −1,070),
`Muzzle_Wing_L/R` (∓0,5935, +0,009, +0,052), `Muzzle_Tip_L/R` (∓0,857, −0,014, +0,234) — sur le nez du pod —,
`Engine_L/R` (∓0,270, −0,014, +0,954) — **au fond de chambre**, comme demandé —, `Cockpit` (0, +0,200, −0,375).

### Triangles par pièce

| Nœud | Triangles | Parent |
|---|---|---|
| `Specter9C` (coque) | 65 766 | — |
| `Nozzle_L` / `Nozzle_R` | 4 328 chacun | — |
| `Canopy` | 3 024 | — |
| `Wing_L` / `Wing_R` | 2 366 chacun | — |
| `Grapple_L` / `Grapple_R` | 988 chacun | — |
| `Petal_{L,R}_00..11` | 628 chacun (15 072 les 24) | `Nozzle_*` |
| `Flap_L` / `Flap_R` | 576 chacun | `Wing_*` |
| `Intake_L` / `Intake_R` | 484 chacun | — |
| `Airbrake_L` / `Airbrake_R` | 444 chacun | — |
| `Rudder_L` / `Rudder_R` | 252 chacun | — |

Biseaux : 3,0 mm à **2 segments** sur la coque, 2,2 mm à 2 segments sur les pièces de coque, 2,0 mm à
**3 segments** sur les tuyères, les pétales et la verrière ; `shade_smooth_by_angle(34°)` partout.
Le budget n'a pas été « dépensé » : 102 738 triangles suffisent à ce que chaque cassure soit un vrai
creux biseauté ; au-delà, c'est le post-traitement rétro qui décide, pas la géométrie (ADR-0044 §2).

---

## 3. Plafonds mécaniques — remesurés à chaque build, build rouge en dessous

Méthode (`_sweep_family`) : les sommets de la pièce (enfants compris) tournent autour de sa charnière par
pas de 1°, et un arbre BVH de chaque voisin (coque filtrée à la région, pièces voisines au repos, pétales
adjacents ouverts du même angle) rend la distance à la surface la plus proche ; le **containment** est un
nombre d'enroulement par lancer de rayon (robuste aux solides qui se chevauchent — le test par la normale
du point le plus proche mentait sur toute arête convexe, voir §8). Le balayage s'arrête à la première image
où un jeu passe sous **2,5 mm** ; le build **échoue** si ce plafond est sous la cible du brief. Les mesures
polaires de BRIEF-0035/0036 (`_wing_sweep_limit`, `_flap_travel_limit`, `_glove_clearance`,
recouvrement de racine) restent en place et bloquantes.

| Famille | Cible brief | **Plafond mesuré** | Première butée |
|---|---|---|---|
| `Wing_L/R` | ≥ 30° | **35°** (BVH, garde 2,5 mm) ; 32,25° (polaire, garde 12 mm) | peau de nacelle à y = +0,487 (36°) |
| `Flap_L/R` | ±14° | **±21°** (BVH) ; 23,2° (cloison) | l'aile (paliers de charnière) à −22° |
| `Nozzle_L/R` (lacet) | ±6° | **±7°** | rebord de douille à ±8° (jeu 2,1 mm) |
| `Petal_*` (24) | ≥ 20° | **≥ 40°, aucune butée** | — |
| `Airbrake_L/R` | ≥ 55° | **94°** | arête du pont à 95° |
| `Intake_L/R` | ≥ 12° | **≥ 60°, aucune butée** | — |
| `Rudder_L/R` | ±22° | **±32°** | dérive / nacelle à ±33° |
| `Grapple_L/R` | ≥ 90° | **≥ 150°, aucune butée** | — |
| `Canopy` | ≥ 35° | **≥ 80°, aucune butée** | — |

Mesures héritées : **emplanture** jeu vertical minimal **3,3 mm** (seuil 3 ; à 0° de flèche, x = 0,478,
y = +0,135 — le profil de voilure est plus épais que la lentille) ; **racine recouverte** −14,0 mm à 0° et
**−28,2 mm à 30°** (négatif = recouvrement) ; **fentes** fuselage/nacelle 106 / 68 / 53 / 86 mm (BRIEF-0035 :
106 / 65 / 53 / 86 — l'entrée d'air oblique ouvre la deuxième de 3 mm).

⚠️ `ShipFlight` est aujourd'hui à 26° de flèche et 11° de volet : les deux tiennent avec marge.

---

## 4. Table des dégagements — jeu minimal (mm) à la CIBLE du brief, pièce ouverte × voisine

| Pièce (à sa cible) | Voisine | Jeu |
|---|---|---|
| `Wing_*` à 30° | coque (sous-face d'emplanture) | **+4,2** |
| `Wing_*` à 30° | `Nozzle_*`, `Airbrake_*`, `Rudder_*` | hors portée |
| `Flap_*` à +14° / −14° | `Wing_*` (cloison, paliers) | **+8,5 / +5,1** |
| `Flap_*` à ±14° | coque | +21,4 / +29,9 |
| `Nozzle_*` (+ 12 pétales) à ±6° | douille de nacelle | **+4,9 / +4,9** |
| `Nozzle_*` à ±6° | `Rudder_*` | hors portée |
| `Petal_*` à 20° | `Nozzle_*` (col, anneau) | **+8,5 à +8,6** |
| `Petal_*` à 20° | pétale voisin, lui aussi à 20° | **+4,6** |
| `Petal_*` à 20° | coque | +62,1 |
| `Airbrake_*` à 55° | coque (baie, arête, dérives) | **+3,8** |
| `Airbrake_*` à 55° | `Canopy`, `Rudder_*` | hors portée |
| `Intake_*` à 12° | coque (nacelle, emplanture) | **+3,5** |
| `Intake_*` à 12° | `Wing_*` | hors portée |
| `Rudder_*` à ±22° | coque (dérive, nacelle) | **+3,3 / +3,3** |
| `Rudder_*` à ±22° | `Nozzle_*`, `Airbrake_*` | hors portée |
| `Grapple_*` à 90° | coque (quille, chape, tubes) | **+3,6** |
| `Canopy` à 35° | coque (puits, dosseret, arête) | **+12,2** |
| `Canopy` à 35° | `Airbrake_*` | hors portée |

Aucune interpénétration, à aucun extrême, pour aucun couple (le build l'aurait refusé). Au repos, le jeu
le plus serré est le pied de pétale sur le col : **3 mm** (voulu : c'est la ligne de charnière).

---

## 5. Axes Godot et signe qui OUVRE — mesurés sur le `.glb`, jamais déduits

L'audit relit le fichier, tourne les sommets **locaux** de chaque nœud de +5° autour de l'axe candidat et
regarde où part la pièce. C'est ce signe qui doit être écrit dans `ShipFlight`.

| Nœud | Axe (repère Godot, local au nœud) | Sens mesuré |
|---|---|---|
| `Wing_L` | (0, 1, 0) | **+** = flèche (le bout recule, +z) |
| `Wing_R` | (0, 1, 0) | **−** = flèche (miroir, comme aujourd'hui) |
| `Flap_L`, `Flap_R` | (1, 0, 0) | **+** = bord de fuite **descend** ; opposer les deux côtés pour l'inclinaison |
| `Nozzle_L`, `Nozzle_R` | (0, 1, 0) | **+** = la sortie va vers **+x (tribord)**, les deux côtés — un lacet coordonné est le même signe |
| `Petal_{L,R}_nn` | **Z × radial**, radial = translation du pétale dans le repère de la tuyère, normalisée dans le plan XY | **+** = le pétale **s'écarte** (vérifié sur les 24) |
| `Airbrake_L/R` | (1, 0, 0) | **+** = le bord arrière **descend** → ouvrir = **−θ** |
| `Intake_L/R` | (1, 0, 0) | **+** = le bord arrière **descend** → ouvrir = **−θ** |
| `Rudder_L` | (**−0,4810, +0,8331, +0,2731**) | **+** = bord de fuite vers **+x (tribord)** |
| `Rudder_R` | (**+0,4810, +0,8331, +0,2731**) | **+** = bord de fuite vers **+x (tribord)** |
| `Grapple_L/R` | (1, 0, 0) | **+** = la pointe **descend** → ouvrir = **+θ** |
| `Canopy` | (1, 0, 0) | **+** = l'avant **monte** → ouvrir = **+θ** |

Exemple pour les pétales : `Petal_L_03` a pour translation locale (0, +0,093, 0) → radial (0, 1, 0) →
axe (−1, 0, 0) ; `Petal_L_00` : radial (−1, 0, 0) → axe (0, −1, 0). Le repère local de `Nozzle_*` a
son +Z sur l'axe de poussée (vers l'arrière) et son origine au plan des charnières.

⚠️ `ShipFlight` ouvre aujourd'hui la tuyère par un **changement d'échelle** : sur cette coque le nœud
`Nozzle_*` contient le corps entier, une échelle le déformerait. Les pétales remplacent l'échelle
(ADR-0044 §3).

---

## 6. Matériaux — aire GÉOMÉTRIQUE et aire VUE

Aire géométrique (toutes faces du `.glb`, cachées comprises — la douille, le puits, les baies, les faces
internes) : `AA_Hull` 36,2 %, `AA_Panel` 21,7 %, `AA_Trim` **3,0 %**, `AA_Greeble` 35,9 %, `AA_Glass`
1,4 %, `AA_Emissive_Engine` **1,7 %**, `AA_Marking_Red` **0,1 %** (10,61 m² au total).

Aire **vue** (rendu d'identifiants, un échantillon par pixel, orthographique 2,7 m ; la vue « jeu » est
la caméra réelle à 20° de la verticale) :

| Vue | Hull | Panel | Trim | Greeble | Glass | Émissif | Rouge |
|---|---|---|---|---|---|---|---|
| **jeu (20°)** | **55,6** | **18,7** | **4,4** | **17,4** | 2,3 | **1,4** | **0,1** |
| dessus | 57,8 | 19,2 | 3,8 | 15,4 | 2,5 | 1,2 | 0,1 |
| dessous | 63,4 | 6,8 | 1,3 | 28,5 | 0,0 | 0,0 | 0,0 |
| avant | 37,3 | 13,9 | 8,9 | 36,2 | 3,4 | 0,2 | 0,1 |
| arrière | 17,7 | 14,4 | 10,9 | 40,6 | 0,0 | **16,2** | 0,1 |
| bâbord / tribord | 39,5 | 36,8 | 4,0 | 15,8 | 3,4 | 0,3 | 0,1 |
| moyenne 7 vues | 44,4 | 20,9 | 5,3 | 24,2 | 2,2 | 2,8 | 0,1 |

Cibles du brief : Hull 55–70, Panel 12–20, Greeble 8–15, Trim ≤ 4, Glass ~2, Émissif ≤ 3, Rouge ≤ 1.
**Dans la vue de jeu** : Hull, Panel, Glass, Émissif et Rouge sont dans les cibles ; **Trim est à 4,4 %
(+0,4)** et **Greeble à 17,4 % (+2,4)**. De dessus, Trim passe (3,8) et Greeble est à 15,4. Deux passes de
réduction ont déjà été faites (pavé rouge de bordé, coiffes rouges et bord d'attaque rouge supprimés ;
or retiré de la lèvre d'emplanture, du jonc d'arête, de la platine de quille, des tranches de fuite ; peau
externe des pétales passée en blanc de coque, qui a fait tomber le greeble vu de 22,7 à 17,4 %). Ce qui
reste de greeble vu d'en haut : le puits (nécessairement sombre), les faces internes des pétales visibles
par le biseau du haut, le chenal du rail, les tranches de dérive et de lame, les tubes de chine. Ce qui
reste d'or : le cadre de verrière (0,069 m²), le seuil du puits, les anneaux de tuyère, les platines de
carter, les bords d'attaque. **Deux retouches proposées, non appliquées** (§10).

L'émissif vu de l'**arrière** est à 16,2 % : ce sont les deux chambres, le point focal arrière voulu ; le
jeu ne cadre jamais la coque par l'arrière à l'horizontale.

---

## 7. Dépliage UV — trois zones, densités mesurées sur le `.glb` (valeurs singulières)

| Zone | Demande | Méthode | Cible | **Moyenne** | Min – max | Anisotropie max | Aire |
|---|---|---|---|---|---|---|---|
| coque hors greeble (`Hull`, `Panel`, `Trim`, `Red`, tous nœuds sauf tuyères) | TEX-0017 | boîte par matériau | 2,5 t/m | **2,426** (0,412 m/tuile) | 1,443 – 2,508 | 1,73 | 6,23 m² |
| `AA_Greeble` de coque | TEX-0018 | boîte par matériau | 4,0 t/m | **3,897** (0,257 m/tuile) | 2,398 – 4,012 | 1,67 | 3,32 m² |
| `Nozzle_*` + `Petal_*` (hors émissif) | TEX-0019 | **cylindrique**, u = 2 tuiles au tour, v = 3,25 t/m (2 / (2π · 0,098)) | 2 t/tour | **3,306** (0,303 m/tuile) | 1,804 – 5,691 | 2,19 | 0,73 m² |

- Les minima des deux zones en boîte sont **la borne de la méthode** (2,5 / √3 = 1,443 ; 4 / √3 = 2,31) :
  faces à 54,7° de leur axe dominant. Coutures = les changements d'axe dominant de la boîte ; sur une
  peau où les feuilles sont **répétables**, elles ne se voient pas (c'est l'hypothèse d'ADR-0011).
- Zone tuyère : `u` est angulaire, donc la densité au tour vaut 2 tuiles / (2π r) et **varie avec le
  rayon** — 3,2 t/m sur l'anneau (r = 0,101), 5,7 t/m au nez du col (r = 0,056, **caché dans la
  douille**), d'où le max et l'anisotropie 2,19 ; sur la peau visible des pétales (r 0,093–0,109) la
  densité est 2,9–3,4 t/m, homogène avec `v`. La **couture** cylindrique est à l'angle 0 = +X du repère
  d'auteur = **−X Godot** (côté bâbord de chaque tuyère : flanc externe de la tuyère bâbord, flanc interne
  de la tuyère tribord). Les faces de tranche (flancs des pétales) sont dépliées en (rayon, axe), les
  fonds en plan polaire, pour qu'aucune face n'ait une UV d'aire nulle.
- TEX-0019 annonce ~3,3 t/m le long de l'axe et 2 tuiles au tour : c'est ce qui est livré.
  `uv1_scale` du jeu de tuyère peut rester à 1.
- **Planche de contrôle** : `BRIEF-0098-planche-uv.png` — damier 2 × 2 par tuile, bleu/blanc = coque,
  orange = greeble, vert = tuyères ; perspective de jeu, gros plan de tuyère (pétales à 20°), baie
  d'aérofrein ouverte. Aucun étirement visible ; les trois densités se distinguent à l'œil.

---

## 8. Ce que la mesure a trouvé en cours de route (et que la relecture n'aurait pas vu)

1. **Les insets de la coque loftée partaient vers l'EXTÉRIEUR.** Le loft enroule ses faces vers
   l'intérieur ; `inset_panel` creuse le long de la normale de winding. Le puits de cockpit sortait en
   **bloc de 40 mm** sur le pont, les baies d'aérofrein en blocs de 22 mm. Trouvé par le balayage BVH (la
   trappe était « à l'intérieur de la coque » de 16 mm au repos), corrigé par un `recalc_face_normals`
   avant tout plaquage — la leçon de BRIEF-0036 sur l'aile, appliquée à la coque. ⚠️ **À vérifier sur
   la coque en service**, dont `build_hull()` est identique sur ce point : ses panneaux de pont et son
   puits sont-ils creusés ou en relief ? (BRIEF-0084 a mesuré le correctif d'`inset_panel` sur une grille
   de test, pas la direction sur le loft.)
2. **Le test « intérieur » par la normale du point le plus proche ment sur une arête convexe** : une
   trappe 15 mm en l'air au-dessus de sa baie était vue « dans le bordé » parce que son plus proche
   point était le haut de celui-ci. Remplacé par un nombre d'enroulement par rayon.
3. **Une section concave n-gone (la dérive échancrée) sort de `bmesh.ops.triangulate` avec des sommets
   dupliqués** ; et deux solides dont les culots partagent un plan (pied et partie haute de dérive)
   produisent des triangles jumeaux après soudure. L'exporteur prévenait « mesh not valid ». Corrigé
   par des éventails vers le centroïde et un chevauchement de 4 mm entre les deux solides.
4. **Le pied de dérive (corde jusqu'à 1,012) surplombait le corps de tuyère** dès que la nacelle s'arrête
   en douille à 0,985 : corde de pied ramenée à 0,975.
5. **La charnière de pétale au milieu de l'épaisseur** faisait avancer le coin externe du pied de 2,7 mm
   dans le cône du col à 20° : posée sur la peau externe, le coin interne recule en s'ouvrant.
6. **Une trappe d'aérofrein à cheval sur la marche de flanc** (segments 2-4) était une plaque en L dont
   l'inset s'effondrait ; elle est sur la tablette de joue (segments 0-2), avec une marge externe de 9 mm
   parce que le bord externe de la baie est l'arête même du bordé (parois en dévers).
7. **L'arceau de visée traversait le montant avant de verrière** ; la pointe de verrière entrait de
   29 mm dans la paroi du puits ; les consoles frôlaient les longerons à 1,4 mm. Trois cotes reculées.

---

## 9. Ce que j'ai vu sur les planches qui ne va pas, ou qu'il faut savoir

### 9.1 Référence côte à côte (`planche-reference.png`)

Même longueur (481 px de long mesurés sur la référence par seuillage, 482 sur le rendu). Masses à la même
place : fuselage porteur, deux nacelles flanquantes, lames, doubles dérives inclinées, verrière au tiers
avant ; contour non convexe. **Écarts nommés**, tous **hérités du plan de BRIEF-0035/0036** que le brief
demandait de reprendre :

- les **lames sont bien plus courtes** que celles de la planche (449 mm de portée exposée, corde
  d'emplanture 0,44 m) — la planche a des ailes qui courent de l'entrée d'air à la poupe ;
- le **nez est une aiguille** là où la planche a un nez large à chines ;
- la **verrière est plus étroite** (0,103 m) et sombre, la planche a une bulle dorée large ;
- les **nacelles avancent plus** (jusqu'à −0,44) que sur la planche.

### 9.2 Planche des mécanismes

Les neuf familles bougent dans le bon sens et la pose du plafond est visible pour chacune. Mais :
- **les aérofreins sont des lames de 27 × 157 mm**, pas des panneaux — la tablette de joue n'a que
  40 mm de large entre la marche de flanc et le bordé, et c'est le seul dos plat entre la verrière et les
  dérives. Ils se lisent au bestiaire ouverts, pas fermés ;
- **le lacet de tuyère à ±6° est à peine lisible** en vue de dessus (les couronnes tournent de 6°) ;
- **la rampe d'entrée d'air** lit comme une plaque posée (3 mm au-dessus de la peau) : fermée, elle ne
  se distingue de la nacelle que par son ombre ;
- **le débattement de volet ±14°** est discret vu de trois quarts arrière ; c'est le contrat.

### 9.3 Cockpit

L'intérieur se voit à travers la vitre **rendue transmissive pour la planche** (alpha 0,22). Dans le
`.glb`, `AA_Glass` garde le matériau normalisé du kit : **alpha 0,86** — dans Godot l'intérieur sera
faible. Le berceau et les fentes émissives se lisent ; **l'arceau de visée est masqué par le montant
avant** sous cet angle. Ouverte, la verrière montre le puits sombre et le seuil doré.

### 9.4 Quatre vues, aplat noir

Les pétales blancs à raidisseurs sombres rendent l'arrière plus clair que la coque en service ; de
profil, la couronne lit comme une lanterne à fentes — c'est le parti pris (métal clair de la planche de
concept), il peut déplaire. L'aplat noir montre, à 26°, un **filet blanc à la charnière des volets**
(les 11 mm de jeu vus de dessus) : il existait déjà sur la coque en service.

### 9.5 Reproductibilité de la coque en service

`./scripts/build-hull.sh specter_9` sur cette machine rend `3fb521b9…` (2 336 564 o), **pas** le fichier
committé `14aba06d…` (2 325 476 o) — **avec ou sans** mes ajouts au kit (testé par `git stash`). Le
défaut est antérieur à ce brief (version de Blender ? kit d'alors ?) ; le fichier LFS committé a été
restauré. À signaler au concepteur : la source ne reproduit plus le binaire.

---

## 10. Limites connues et suggestions

1. **39 nœuds mobiles, pas 48.** La table du brief en compte 39 (2+2+2+24+2+2+2+2+1) ; « 48 » est une
   erreur de somme. `EXPECTED_MOVING_NODES = 39` est vérifié au build.
2. **Grappin : deux consignes du brief se contredisaient** (« charnière arrière » / « replié à plat vers
   l'arrière »). Retenu : charnière à la **racine, à l'avant du logement**, bras couché **vers l'arrière**
   au repos, **pendant vers le bas à 90°** (+θ autour de X Godot). À trancher si l'autre lecture était voulue.
3. **Trim 4,4 % et Greeble 17,4 % vus de la caméra de jeu** (cibles ≤ 4 et 8–15). Deux retouches
   simples restent possibles : platine de carter en `AA_Panel` (−0,4 point d'or) et tubes de chine en
   `AA_Panel` (−1 point de greeble). Non appliquées : la consigne finale était de ne plus rebâtir.
4. **`AA_Glass` à alpha 0,86** : le cockpit exige un matériau plus transparent côté Godot pour cette
   coque (override sur `specter_9_c` — le kit impose la même spec à toutes les coques).
5. **`Muzzle_Wing_*` et `Muzzle_Tip_*` restent figés à la pose déployée** (le kit ne parente pas les
   points d'attache) — limite déjà connue de BRIEF-0035/0036.
6. **`Engine_*` est au fond de chambre**, à l'intérieur de la tuyère : la plume traverse la couronne,
   ce que le brief demandait ; elle passera par les pétales ouverts.
7. Le **balayage BVH échantillonne des sommets**, pas l'intérieur des faces : une face plane voisine
   pourrait s'approcher entre deux sommets. Les maillages biseautés sont denses ; le risque est
   millimétrique, pas nul.
8. Les **planches sont un rendu studio** (Cycles) : elles prouvent la géométrie, pas la hiérarchie en
   jeu (bloom, lift, postérisation). La capture en jeu, avec `HullDetail` et les trois textures, reste à
   faire par le concepteur — ADR-0044 §2 ne juge la coque qu'au temps GPU mesuré.
9. **La sous-face de l'emplanture** reste une casquette ouverte (arbitrage de BRIEF-0036), visible au
   bestiaire depuis le dessous.

---

## 11. Critères d'acceptation

- [x] Vue de dessus côte à côte avec la planche, même hauteur ; masses à la même place, contour non convexe ; écarts nommés (§9.1)
- [x] Les nœuds mobiles de la table du brief existent (39, voir §10.1), pivot sur charnière, `Flap_*` sous `Wing_*`, `Petal_*` sous `Nozzle_*`
- [x] Table des plafonds, tous au-dessus des cibles, remesurés à chaque build, build rouge en dessous
- [x] Table des dégagements : aucune interpénétration à aucun extrême
- [x] Axe Godot et signe d'ouverture mesurés par famille
- [x] Cockpit visible à travers la verrière sur la planche (vitre rendue transmissive — §9.3)
- [x] Émissif ≤ 3 %, rouge ≤ 1 % (géométrique et vue de jeu) ; or 3,0 % géométrique / **4,4 % vu de jeu** ; greeble **17,4 % vu de jeu** (§6)
- [x] Bbox 1,7500 × 2,4600, hauteur 0,6512, pivot centré, 10 points d'attache
- [x] 102 738 triangles ≤ 400 000, compte par pièce
- [x] UV présentes, `TEXCOORD_0` compté 116/116 ; densités mesurées pour les trois zones ; cylindrique sur `Nozzle_*`/`Petal_*`
- [x] `./scripts/build-hull.sh --check specter_9_c` vert
- [x] Aucun texte, chiffre, insigne, livrée
- [x] Six planches livrées et regardées
