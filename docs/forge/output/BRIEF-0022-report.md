# BRIEF-0022 — Coque 3D du Needle Scout — compte-rendu

- **Agent** : asset-forge
- **Date** : 2026-07-12
- **Brief** : `docs/forge/briefs/BRIEF-0022-needle-scout-hull.md`
- **Normes** : `docs/decisions/ADR-0008-pipeline-3d-blender.md`, `docs/forge/CHARTE_CREATIVE.md`
- **Référence de design** : `assets/source/concepts/null_choir_enemy_families_sheet.png`, **première famille** (rangée du haut)
- **Outil** : Blender 4.5.11 LTS, headless (`blender45 -b -P …`)

## 1. Livrables

| Fichier | Rôle |
|---|---|
| `tools/blender/build_needle_scout.py` | script de construction, rejouable |
| `assets/imported/models/ships/needle_scout.glb` | le mesh livré (LFS, 49 932 o) |
| `docs/forge/output/BRIEF-0022-report.md` | ce document |
| `assets/licenses/ASSET_PROVENANCE.csv` | +1 ligne (`needle_scout_hull`) |

Commande unique : `blender45 -b -P tools/blender/build_needle_scout.py`

Le kit partagé `tools/blender/lib/aegis_kit.py` est **réutilisé sans la moindre
modification** (voir §6 pour la seule évolution qui mériterait discussion).

## 2. Mesures réelles (relevées sur le `.glb` livré, pas sur la scène Blender)

| Critère | Contrat | Mesuré | Marge |
|---|---|---|---|
| Largeur (Godot X) | 0,65 m ±3 % | **0,6500 m** | 0,00 % |
| Longueur (Godot Z) | 1,90 m ±3 % | **1,8993 m** | −0,04 % |
| Hauteur (Godot Y) | ≤ 0,30 m | **0,2252 m** | 11,9 % de la longueur |
| Triangles | ≤ 3 000 | **1 612** | 46 % de marge |
| Sommets | — | 1 409 | — |
| Pivot (centre X/Z) | ±0,02 m | (−0,0000 ; −0,0003) | centré |
| Matériaux | nomenclature ADR-0008 | **les 7**, tous assignés | — |
| Points d'attache | `Muzzle_C`, `Engine_C` | 2 | — |
| Déterminisme | rejouable | **sha256 byte-identique** entre deux exécutions | — |

Répartition des triangles par matériau : `AA_Hull` 666 · `AA_Emissive_Engine` 338 ·
`AA_Greeble` 178 · `AA_Trim` 168 · `AA_Panel` 154 · `AA_Marking_Red` 88 ·
`AA_Glass` 20. Le `.glb` sort en **7 primitives** (une par matériau).

Points d'attache livrés (repère Godot : nez vers −Z, +X à tribord) :

```
Muzzle_C  (0.0000, +0.0000, -0.9550)   5 mm devant la pointe, sur l'axe
Engine_C  (0.0000, +0.0020, +0.9460)   plan de sortie de la tuyère
```

`Engine_C` est bien en +Z (arrière) et `Muzzle_C` en −Z (avant) : le témoin
asymétrique du kit (`export_hull`) le vérifie sur le fichier binaire, ce que la
bounding box, symétrique, ne saurait faire.

## 3. Lecture du concept et choix de modélisation

La première famille de la planche est un **dard biconique** : nez très acéré,
maître-couple juste en arrière du milieu, effilement continu jusqu'à la poupe,
carapace anthracite/violette segmentée, deux plaques ivoire à mi-corps, deux
ailettes arrière en flèche, et une **ligne d'énergie magenta** courant sur tout
l'axe dorsal, s'ouvrant en losange autour d'un noyau-œil.

- **Coque** : 20 sections transverses de 12 sommets. La section porte elle-même
  la chine (arête vive à mi-hauteur, la ligne qui fait la lecture de dard) et la
  rainure d'énergie.
- **Ligne magenta** : c'est une **rainure en V réellement creusée** dans la
  section (2 sommets par anneau), pas un `inset` posé après coup. Elle coûte donc
  quasiment zéro triangle, elle est du détail par la géométrie (ADR-0008 §
  Matériaux), et surtout elle ne dégénère pas là où les faces deviennent
  minuscules : près du nez, un `inset_region` aurait produit des faces nulles.
  Largeur : 28 mm de lèvre à lèvre au maître-couple (6 % de la largeur de coque),
  84 mm au noyau. C'est la « fine ligne » demandée.
- **Carapace** : 4 plaques violettes enfoncées (−7 mm) sur les épaules dorsales,
  séparées par des joints anthracite. C'est le trait dominant du Chœur Nul
  (charte §4, « segmenté ») ; un joint reste lisible réduit, un greeble non.
- **Plaques ivoire** : panneau enfoncé sur chaque flanc supérieur à mi-corps,
  bordure anthracite conservée (elles lisent comme des pièces rapportées) ; plus
  un liseré ivoire sur le fil du bord d'attaque, qui fait exister la pointe quand
  le vaisseau ne fait que 30 px de haut.
- **Noyau-œil** : socle anthracite, lunette ivoire, membrane `AA_Glass`, pupille
  magenta émissive, au débouché du losange de la rainure. 88 triangles.
- **Ailettes** : prismes fins en flèche arrière ; leur bout porte la largeur
  hors-tout (0,325 m de demi-envergure, soit exactement 0,65 m).
- **Vert maladif** : deux évents de 22 × 62 mm sur les épaules arrière. La charte
  dit « usage très limité » ; le premier jet en faisait deux dalles de
  46 × 110 mm qui volaient la vedette à la ligne magenta.

Aucun greeble semé : à cette taille à l'écran, un greeble est du bruit payé en
triangles. Le budget est tenu à 1 612 tris, soit **54 % du plafond**, et ce n'est
pas une économie subie : ajouter du détail micro n'aurait rien apporté à 30 px.

## 4. Deux pièges rencontrés (et ce qu'ils coûteraient à la coque suivante)

**a. Le biseau fait exploser une pointe.** Modélisé d'abord avec un nez en
sommet unique (`fan_to_point`, comme le Specter-9), le dard sortait du
`bevel_sharp_edges` avec une **bille noire de 2 à 3 cm** à la place de la pointe.
Cause : à ce sommet convergent douze arêtes quasi parallèles, et l'étendue d'un
biseau de sommet varie en 1/sin(angle entre arêtes) — l'offset de 4 mm s'échappe
le long de l'axe. Le contrat ADR-0008 ne voit rien (la bounding box perdait
6 mm, très en deçà des ±3 %) : **seul un rendu de contrôle l'a montré**. Le nez
se termine donc par une micro-section de 14 × 9 mm, ce qui rend l'angle entre
arêtes sain ; le biseau y produit un chanfrein de 4 mm, invisible en jeu.
Toute coque à pointe très acérée (le Pale Leviathan a des éperons) rencontrera
exactement ce problème.

**b. La scène de contrôle est en Z-up, pas dans le repère Godot.** L'importeur
glTF de Blender reconvertit `Y-up → Z-up` : dans une scène de re-import, le nez
est de nouveau en +Y. Placer une caméra de vérification aux coordonnées Godot
donne des vues fausses — et donc une validation visuelle fausse.

## 5. Limites connues

- **La tuyère est un ajout au concept.** La planche montre une poupe en pointe ;
  le brief exige un `Engine_C` (départ de traînée). Arbitrage : petite tuyère
  effilée (78 mm de diamètre pour 1,90 m de long, lèvre ivoire, fond magenta).
  La silhouette de dard est conservée, la traînée a une origine physique, mais
  ce n'est pas littéralement la planche.
- **La tuyère est peu visible en jeu.** Un Needle Scout descend vers le joueur :
  la caméra le voit de face-dessus, tuyère à l'opposé. Le halo de propulsion, si
  on en veut un, devra venir des particules ancrées sur `Engine_C`, pas du mesh.
- **Pas de LOD, pas de bake de texture, pas d'animation** (hors périmètre du
  brief). À 1 612 triangles, un LOD n'a probablement aucun intérêt : le coût de
  masse sera dans les draw calls et les 7 surfaces, pas dans la géométrie.
- **7 primitives pour un ennemi de piétaille.** Le `.glb` sort une primitive par
  matériau ; instancié en masse, cela fait 7 surfaces par scout. Si le profilage
  montre un coût de draw call, la réponse n'est pas de retoucher ce mesh mais
  d'activer le `MultiMesh`/l'instanciation côté moteur — hors périmètre ici, mais
  c'est signalé.
- L'`AA_Glass` (membrane du noyau) est transmissif : 20 triangles seulement, mais
  ils passeront dans la passe transparente côté Godot. Si cela gêne en masse, le
  noyau peut passer en `AA_Greeble` sans rien perdre de la lecture.

## 6. Évolution du kit qui *mériterait* d'être discutée (non faite)

Le kit n'a pas été modifié, conformément au brief. Une seule évolution paraît
réellement utile pour les coques à venir :

**`bevel_sharp_edges()` gagnerait un paramètre d'exclusion** (liste d'arêtes ou de
sommets à ne pas biseauter, ou un `vertex_only=False` / `clamp` plus agressif).
Aujourd'hui, la seule parade contre l'explosion de biseau sur une pointe acérée
(§4a) est de **modifier la géométrie** pour éviter le sommet pathologique. C'est
acceptable pour un dard ; ce le sera moins pour une coque dont la pointe doit
rester un vrai sommet. Un `bmesh.ops.bevel` accepte `affect="EDGES"` avec une
sélection : il suffirait d'exposer un filtre.

Accessoirement, `add_lathe()` tourne autour de l'axe **Y** (longitudinal), ce qui
convient aux tuyères et aux canons. Le noyau-œil dorsal du Needle Scout est un
solide de révolution autour de **Z** ; il a été construit ici par un helper local
(`_disc_stack`) qui n'utilise que des primitives du kit (`add_ring`,
`bridge_rings`, `cap_ring`). Si une deuxième coque en a besoin (les boss du Chœur
Nul ont des noyaux dorsaux), le kit gagnerait un `add_lathe(axis=…)`.

## 7. Conformité IP

Silhouette entièrement dérivée de la planche interne du Chœur Nul (elle-même
originale) : dard biconique, carapace segmentée, rainure d'énergie axiale,
ailettes en flèche. Aucun nom, logo, marquage ni élément de forme emprunté à une
licence existante. Le script ne contient aucun prompt ni référence externe.
