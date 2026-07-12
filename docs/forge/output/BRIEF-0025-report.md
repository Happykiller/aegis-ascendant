# BRIEF-0025 — Coque 3D de l'Aegis Citadel — compte-rendu

- **Agent** : asset-forge
- **Date** : 2026-07-12
- **Brief** : `docs/forge/briefs/BRIEF-0025-aegis-citadel-hull.md`
- **Normes** : `docs/decisions/ADR-0008-pipeline-3d-blender.md`, `docs/forge/CHARTE_CREATIVE.md`
- **Référence de design** : `assets/source/concepts/aegis_citadel_concept_sheet.png`
- **Outil** : Blender 4.5.11 LTS, headless (`blender45 -b -P …`)

## 1. Livrables

| Fichier | Rôle |
|---|---|
| `tools/blender/build_aegis_citadel.py` | script de construction, rejouable |
| `assets/imported/models/structures/aegis_citadel.glb` | le mesh livré (LFS, 787 884 o) |
| `docs/forge/output/BRIEF-0025-report.md` | ce document |
| `assets/licenses/ASSET_PROVENANCE.csv` | +1 ligne (`aegis_citadel_hull`) |

Commande unique : `blender45 -b -P tools/blender/build_aegis_citadel.py`

Le kit partagé `tools/blender/lib/aegis_kit.py` est **réutilisé sans une seule
modification** (voir §6 pour les évolutions que je *suggère*, sans les avoir faites).

## 2. Mesures réelles (relevées sur le `.glb` livré, pas sur la scène Blender)

| Critère | Contrat | Mesuré | Marge |
|---|---|---|---|
| Largeur (Godot X) | 19,6 m ±3 % | **19,6000 m** | 0,00 % |
| Longueur (Godot Z) | 16,6 m ±3 % | **16,6042 m** | +0,03 % |
| Hauteur (Godot Y) | ≤ 5,0 m | **4,8798 m** | 12 cm sous le plafond |
| Triangles | ≤ 30 000 | **21 028** | 30 % de marge |
| Sommets | — | 27 258 | — |
| Pivot (centre X/Z) | ±0,02 m | (+0,0000 ; +0,0061) | centré |
| Matériaux | les 7 | les 7, tous assignés | — |
| Points d'attache | 4 requis | 4 + 10 repères de pièces | — |
| Déterminisme | rejouable | **sha256 byte-identique** entre deux exécutions | — |

Répartition des triangles par matériau : `AA_Greeble` 12 110 · `AA_Trim` 4 439 ·
`AA_Emissive_Engine` 2 860 · `AA_Hull` 1 331 · `AA_Marking_Red` 132 · `AA_Panel` 112 ·
`AA_Glass` 44. Le `.glb` sort en **7 primitives** (une par matériau).

> Le nombre de triangles n'est *pas* une mesure de surface : `AA_Greeble` domine le
> comptage parce qu'il porte tout ce qui est rond et petit (dix tubes de canon, six
> fûts de tourelle, quatre entretoises, les nervures du cristal), alors que les grandes
> faces de coque et de panneau ne coûtent que deux triangles chacune. À l'œil, la
> citadelle est bien une masse **blanc cassé** ponctuée de panneaux bleus — c'est le
> rendu de contrôle qui l'a arbitré, pas le tableau (voir §4).

Orientation vérifiée sur le fichier produit (témoins asymétriques, comme l'exige
l'ADR-0008) : `Muzzle_Battery_L` en Godot `(−8,60 ; +1,05 ; −8,35)` — bouche du canon
bâbord, **à l'avant** (Z négatif = haut de l'écran) et **à gauche** (X négatif) ;
`Dock_Entry` en `(0 ; −0,06 ; +6,75)` — la baie regarde bien **vers le joueur**.

## 3. Choix de design et leurs raisons

**Relevé, pas invention.** La grande vue de dessus de la planche a été mesurée au pixel
puis calée sur les deux cotes imposées (19,6 × 16,6 m), ce qui donne une échelle unique
de **0,01445 m/px**. Toutes les tables du script en découlent : bras à ±7,65 m d'axe et
2,15 m de demi-largeur (bord externe à 9,80 = la demi-largeur imposée), noyau de 7,0 m
de long, rampe de 3,1 m. Les deux échelles (largeur et longueur) tombent à 0,2 % l'une
de l'autre : la planche était métriquement cohérente.

**Le prisme axial est une décision, pas un accident.** Le premier jet échantillonnait le
corps central sur treize stations suivant une courbe douce. En silhouette, cela donnait
un **œuf**, pas une forteresse. La table a été refaite anguleuse : trois cassures franches
(proue, épaule, hanche) et un **flanc parallèle de 5,6 m**. C'est lui qui porte le mot
« prisme » de la charte. Même parti pris sur les bras (flanc externe rectiligne sur 5,4 m).

**Trois masses, deux vides.** La lisibilité à très grande distance ne vient pas du détail :
elle vient des **entretoises**. Les deux trouées entre le corps et les bras sont ce qui
empêche la citadelle de se réduire à une tache. Elles sont donc franches (1,75 m de vide)
et tenues par des cylindres transversaux à colliers or et anneau cyan.

**Le noyau est volontairement démesuré** : 4,0 m de large et 7,0 m de long, soit 42 % de
la longueur totale de l'engin, prisme hexagonal facetté aux deux pointes, entièrement en
`AA_Emissive_Engine`. Il est assis dans un puits anthracite bordé d'un jonc or — le cadre
sombre est ce qui fait « lire » le cyan, à la manière de la planche.

**Batteries** : trois tubes par bras, le tube externe le plus long (c'est lui qui fixe la
bbox en −Y et qui porte `Muzzle_Battery_*`), montés en chandelle sur le pont du bras avec
colliers or, plus deux tubes arrière courts (présents sur la vue arrière de la planche).
**Six tourelles** secondaires à double tube (deux épaules avant, deux hanches, une par
bras), toutes pointées vers −Y. **Baie d'appontage** à l'arrière : gorge lumineuse
encastrée dans la culasse, rampe trapézoïdale à rails or et **quatre chevrons cyan**
pointant vers l'avant — le geste de guidage d'appontage.

**Marquages rouges** : rares, comme l'exige la charte — deux plaques de zone réglementée
de part et d'autre du puits du noyau, et une sur la proue. Rien d'autre.

## 4. Lisibilité — vérifiée, pas supposée

Deux contrôles, tous deux sur le `.glb` **livré** (pas sur la scène Blender) :

1. **Silhouette rastérisée** (projection XZ des 21 028 triangles, remplie en noir) puis
   réduite à 128, 64, 40, 24 et 16 px. La lecture en trois masses + les deux vides tient
   jusqu'à **~40 px** ; en dessous, l'objet devient un bloc en H et les canons disparaissent.
   C'est sans conséquence pratique : la citadelle fait 19,6 m sur un plan de jeu large de
   24 — elle occupe l'essentiel de la largeur de l'écran et ne sera jamais vue à 16 px.
2. **Rendu Cycles CPU** (headless), à 24° au-dessus du plan — l'angle réel de la caméra de
   jeu — et en vue de dessus stricte. C'est ce rendu qui a fait corriger deux défauts réels
   décrits ci-dessous.

**Défaut n° 1 corrigé — la citadelle était bleue.** Les panneaux `AA_Panel` étaient posés
avec un liston de 0,12 m sur des faces de pont larges de 2 m : le bleu mangeait ~90 % de la
surface et la coque Vanguard n'était plus blanc cassé. Les listons sont passés à 0,32 m
(pont) et 0,34 m (bras), et la proue comme la poupe restent entièrement blanches.

**Défaut n° 2 corrigé — le cristal était une goutte blanche.** Un matériau émissif ne reçoit
pas la lumière : toutes ses facettes ont exactement la même valeur, et le noyau, si soigné
soit-il en géométrie, se rendait comme une bulle lisse. **Les facettes d'un émissif ne
peuvent exister que par la géométrie** : trois nervures anthracite courent maintenant sur
les arêtes de taille (faîtière + deux arêtes de facette), comme les traits sombres de la
planche. Elles sont balayées par pas de 0,22 m — tendues d'une station à l'autre, elles
dépassaient de 60 cm au-dessus des pointes et donnaient trois griffes noires.

## 5. Limites connues (honnêtement)

- **Les « objets nommés séparément » sont livrés comme Empties, pas comme meshes distincts.**
  `export_hull()` du kit n'accepte **qu'un seul objet maillé** : il n'applique la correction
  d'axe qu'à `hull.data`, et sa bounding box se calcule sur les accesseurs de position
  (donc en coordonnées locales, sans transformée de nœud). Exporter `Core_Prism`,
  `Battery_L/R`, `Turret_01..06` et `Dock_Bay` comme meshes séparés aurait exigé soit de
  modifier le kit (interdit, trois autres agents s'en servent en ce moment), soit de refaire
  la correction d'axe dans le script de coque (ce que le kit interdit explicitement, et à
  raison : c'est le piège n° 1 du pipeline). J'ai donc **joint la coque en un mesh** et posé
  un **repère Empty nommé au barycentre réel de chaque pièce** : Godot recevra
  `Core_Prism`, `Battery_L`, `Battery_R`, `Turret_01`…`Turret_06`, `Dock_Bay` comme `Node3D`
  bien placés. Si le gameplay a besoin de **détruire une batterie séparément** (mesh à
  masquer, hitbox propre), il faudra faire évoluer le kit — voir §6.
- **Le cristal se rend blanc, pas cyan**, sous forte exposition : `AA_Emissive_Engine` a une
  force d'émission de 2,5 (valeur du kit, non modifiée). C'est le comportement voulu d'un
  noyau « très émissif » avec le glow de Godot (cœur blanc-chaud, halo cyan), mais si la
  review veut un cyan plus saturé, c'est un réglage **du kit ou du matériau côté Godot**, pas
  de cette coque.
- **Marge de hauteur mince** : 4,88 m pour un plafond à 5,00. Toute nervure ou antenne
  ajoutée sur le noyau devra reprendre 10 cm ailleurs.
- **Pas de LOD, pas de bake de texture, pas d'animation** : hors périmètre du brief. Le
  détail vient de la géométrie (biseaux, panneaux enfoncés, greebles), conformément à l'ADR.
- **Interpénétrations assumées** : mantelets, entretoises et gorge de baie s'enfoncent dans
  les coques qu'ils rejoignent (kitbash hard-surface classique, comme les carénages de
  tuyère du Specter-9). Aucun booléen : la coque reste rejouable et légère.

## 6. Évolutions du kit que je *suggère* (non faites)

Signalées ici plutôt qu'appliquées, conformément à la consigne.

1. **`export_hull()` multi-objets.** Accepter une *liste* de meshes, appliquer `_AXIS_FIX` à
   chacun, et calculer la bbox en composant les transformées de nœud. C'est le seul vrai
   manque : sans lui, aucune coque ne peut livrer de pièces nommées séparément (utile pour
   la citadelle, et probablement indispensable pour les boss à parties destructibles).
2. **`add_lathe(axis=…)`.** Le kit ne sait tourner qu'autour de **Y**. Cette coque avait besoin
   de révolutions autour de **Z** (fûts de tourelle) et de **X** (entretoises transversales) ;
   je les ai écrites en local (`_z_drum`, `_x_tube`), **uniquement avec les primitives publiques
   du kit** (`add_ring`, `bridge_rings`, `fan_to_point`). Trois coques sur cinq en auront besoin :
   un paramètre d'axe éviterait trois copies divergentes.
3. **`_bar()` (barre prismatique orientée librement dans le plan XY)** : chevrons, liserés
   diagonaux, nervures. Écrite en local ici aussi. Bonne candidate à la mutualisation.

## 7. Conformité IP

Création originale intégrale, construite au relevé de la planche de concept interne. Aucune
silhouette, aucun nom, aucun élément de Macross, Robotech, Gundam ou de toute autre licence.
La forme — prisme axial trapu, deux bras-batteries capsulaires séparés par des entretoises,
noyau cristallin dorsal surdimensionné — n'évoque aucun vaisseau connu : elle est dictée par
la charte (§4) et par la contrainte de lisibilité en vue de dessus.
