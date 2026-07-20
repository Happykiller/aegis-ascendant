# BRIEF-0029 — Compte-rendu : coque 3D du Crescent Interceptor

- **Agent** : asset-forge
- **Date** : 2026-07-20
- **Brief** : `docs/forge/briefs/BRIEF-0029-crescent-interceptor-hull.md`
- **Statut** : livré, contrat ADR-0008 vert, rendu et jugé

## 1. Livrables

| Fichier | Rôle |
|---|---|
| `tools/blender/build_crescent_interceptor.py` | script de construction (la source de l'asset) |
| `assets/imported/models/ships/crescent_interceptor.glb` | mesh exporté (LFS) |
| `docs/forge/output/BRIEF-0029-report.md` | ce document |
| `assets/licenses/ASSET_PROVENANCE.csv` | ligne `crescent_interceptor_hull` |

Régénération :

```bash
~/.local/bin/blender45 -b -P tools/blender/build_crescent_interceptor.py
~/.local/bin/blender45 -b -P tools/render-hull.py -- assets/imported/models/ships/crescent_interceptor.glb
```

Le kit `tools/blender/lib/aegis_kit.py` est réutilisé **sans aucune modification**.
Aucune évolution du kit n'a été nécessaire (voir §6 pour la seule fonction locale ajoutée,
qui n'utilise que des primitives du kit).

## 2. Mesures réelles (relevées sur le `.glb` livré)

| Grandeur | Valeur | Contrat | Verdict |
|---|---|---|---|
| Triangles | **2 665** | ≤ 3 000 | 89 % du budget |
| Sommets | 1 955 | — | — |
| Bounding box (Godot X, Y, Z) | **1,0985 × 0,1674 × 1,5995 m** | 1,10 × ≤ 0,28 × 1,60 (±3 %) | écart X 0,14 %, écart Z 0,03 % |
| Centre (pivot) | (−0,0000, +0,0145, −0,0003) | ±0,02 m en X/Z | centré |
| Taille du fichier | 69 556 o | — | — |

Répartition des triangles par matériau (les 7 slots normalisés sont assignés) :

| Matériau | Triangles | Où |
|---|---|---|
| `AA_Hull` | 1 400 | carène, longerons, lames |
| `AA_Greeble` | 669 | parois de gorge, ventre, greebles, panneaux sourds |
| `AA_Emissive_Engine` | 214 | gorges dorsales + fonds de tuyère |
| `AA_Trim` | 188 | plaques ivoire du dessus des lames, lèvres de tuyère |
| `AA_Marking_Red` | 88 | deux évents vert maladif (charte : « usage très limité ») |
| `AA_Panel` | 68 | trois timbres violets |
| `AA_Glass` | 38 | bandeau de verrière axial |

Points d'attache (coordonnées **Godot**, telles que lues dans le `.glb`) :

| Nom | Position | Rôle |
|---|---|---|
| `Muzzle_C` | (0,0000, 0,0000, −0,8060) | bouche de tir, 6 mm devant la pointe du fuselage |
| `Engine_C` | (0,0000, 0,0040, +0,7940) | traînée centrale consommée par `EnemyController` |
| `Engine_L` | (−0,3350, 0,0040, +0,7940) | tuyère bâbord (posée via `attach_pair()`) |
| `Engine_R` | (+0,3350, 0,0040, +0,7940) | tuyère tribord |

`Engine_L`/`Engine_R` sont posés par `ak.attach_pair()` : aucun signe de X n'est écrit à la
main dans le script.

## 3. Déterminisme

Deux exécutions successives du build produisent un `.glb` **byte-identique** :

```
2b908fd2e8c6ae88ed09ade77f5c0be7c330667d209ed62e57a0800d82e2edc9
2b908fd2e8c6ae88ed09ade77f5c0be7c330667d209ed62e57a0800d82e2edc9
```

Les deux seuls appels aléatoires sont des `greeble_strip()` explicitement seedés (2917 bâbord,
6043 tribord).

## 4. Ce que la planche de rendu montre réellement

Rendu avec `tools/render-hull.py` (planche 4 vues : `game` / `dessus` / `profil` /
`trois-quarts`, fond `#070A12`, Cycles CPU).

**Vue « jeu » (20° de la verticale) et vue « dessus » sont quasi indiscernables**, ce qui
confirme la prémisse du brief : ce que la vue de dessus ne montre pas n'existe pas en jeu.

Ce qu'on y lit, du plus fort au plus faible :

1. **Deux grands arcs en parenthèse « ( ) »** encadrant le fuselage, chacun souligné d'un filet
   magenta qui suit la concavité. C'est la lecture dominante, immédiate, et c'est la signature
   demandée.
2. Le **fuselage-dard central**, sombre, avec sa fine ligne d'énergie axiale et l'œil magenta du
   capteur au tiers avant.
3. Les **deux longerons** parallèles, leurs plaques ivoire et leur gorge magenta interrompue.
4. Les **plaques de liaison** en delta arrière, anthracite, avec un timbre violet central.
5. Les tuyères ne se voient **pas** de dessus (leurs culots regardent l'arrière) — c'est attendu,
   et c'est pourquoi elles ne portent aucune charge de lisibilité.

Vue de profil : coque très plate (0,167 m pour 1,60 m de long, soit 10 %), ce qui est conforme à
l'esprit « ne pas épaissir une coque vue de dessus ».

### Lisibilité à petite taille, face au Needle Scout

Les vues « jeu » des deux coques ont été réduites à 34, 52 et 80 px et comparées côte à côte.
**Dès 34 px, les deux silhouettes sont distinctes** : le Scout est une masse triangulaire pleine,
le Crescent est ajouré et bordé de deux arcs. Le contraste de proportions imposé par le brief
(1,10 × 1,60 contre 0,65 × 1,90) fait la moitié du travail ; les arcs magenta font l'autre moitié.

## 5. Choix créatifs et justifications

### Trois itérations de géométrie, toutes déclenchées par le rendu

Ce point mérite d'être consigné, car les deux premiers jets **passaient tous les contrôles
automatiques** (bbox, budget, matériaux, orientation, pivot) et étaient pourtant à rejeter :

- **Jet 1** — lame étroite (120 mm) à rails quasi parallèles à l'axe. Au rendu, la coque
  montrait *cinq échardes parallèles* et aucun croissant.
- **Jet 2** — réponse par l'élargissement (220 mm de corde). Mauvais diagnostic : une lame large
  ne lit pas « croissant », elle lit « feuille ». Le violet, en outre, y devenait la couleur
  dominante du vaisseau.
- **Jet 3 (livré)** — ce qui fait un croissant n'est ni la finesse ni la largeur, c'est la
  **courbure** : le bord intérieur doit être réellement concave, c'est-à-dire bomber vers
  l'extérieur au-delà de la corde qui joint ses extrémités. La lame livrée fait 100 mm de large
  pour un **balayage latéral de 300 mm** (talon x = 0,35 ancré dans le longeron, ventre x = 0,55,
  pointe ramenée à x = 0,25 près de l'axe).

Aucun contrôle automatique n'aurait attrapé les jets 1 et 2. Seule la planche l'a fait.

### Où vit le détail

Tout l'émissif et tous les panneaux d'accent sont sur des **surfaces supérieures** :
gorge axiale du fuselage, gorges des longerons, gorge du bord intérieur des lames, plaques
ivoire du dessus des lames, capteur dorsal. Les fonds de tuyère restent magenta (une tuyère
éteinte serait absurde) mais **ne sont pas comptés comme lisibilité** : c'est exactement le
défaut relevé sur le Specter-9 (BRIEF-0026), et la coque ne dépend pas d'eux.

Le ventre est traité au strict minimum (moins creusé que le dos, matériaux sourds) : le joueur
ne le voit jamais.

### Discipline chromatique

Le violet `#452663` du kit remonte **beaucoup plus clair que prévu** sous la key light
(métallicité 0,15, rugosité 0,40) : au jet 2, quatre plaques violettes suffisaient à faire une
machine lavande, à l'opposé du Chœur Nul « sombre » de la charte §4. Le violet est donc réduit à
**68 triangles** — trois timbres encadrés d'anthracite — et les autres panneaux enfoncés utilisent
`AA_Greeble`, qui donne le même relief sans tache de couleur. La dominante est anthracite,
comme le veut la charte.

Le magenta a subi la même cure : rainure axiale ramenée de 56 à 30 mm de lèvre à lèvre, et
**seul le fond** de la rainure est émissif (ses deux parois restent anthracite). Sans quoi la
coque portait un ruban rose qui écrasait tout.

### Asymétrie

La charte §4 décrit le Chœur Nul comme asymétrique. La silhouette portante reste symétrique
(deux longerons, deux lames) — un ennemi instancié en masse doit être lisible avant d'être
étrange. L'asymétrie est portée par le **bruit mécanique** : seeds de greebles différents par
côté, et deux évents vert maladif de longueurs inégales (46 et 38 mm). Zéro triangle
supplémentaire, aucun risque sur la bounding box.

### Transposition, pas décalque (ADR-0009)

De la vignette de référence on garde l'**intention** : fuselage central étroit et cranté,
longerons latéraux terminés par des tuyères, lames balayant vers l'avant, verrière axiale.
On abandonne le coloris (gris/argent à réacteurs bleus), les proportions, la structure des
lames (la référence a des ailes en delta plein plus deux canards ; ici c'est un arc unique par
côté) et tout détail identifiable. Création originale, aucun élément de licence tierce.

## 6. Limites connues et points à signaler

1. **Le budget de triangles est dominé par le biseautage.** À 38° de seuil (la valeur du Needle
   Scout), le bevel doublait la coque : 1 443 → 3 181 triangles, hors budget. Cette coque a
   beaucoup plus de bords francs que le Scout (trois volumes, deux lames, neuf panneaux insetés,
   et chaque bord d'inset présente une arête à 90°). Le seuil est porté à **50°**, ce qui ramène à
   2 665. Conséquence assumée : les raccords de carène entre 38° et 50° ne sont plus chanfreinés —
   ils restent nets grâce au lissage par angle, et rien ne se voit à la planche. Si une future
   coque du même genre visait un budget plus serré, c'est le premier levier.
2. **La verrière `AA_Glass` est peu lisible** (38 triangles, matériau volontairement très sombre).
   Elle existe et se lit comme une zone noire allongée à l'avant du dos, mais c'est le **capteur
   magenta** qui joue réellement le rôle de « point de mire axial ». Le brief demandait
   « verrière/capteur visible sur l'axe » : le critère est satisfait par le capteur, pas par le
   vitrage.
3. **Interpénétrations assumées.** Les lames traversent les longerons, les plaques de liaison
   traversent fuselage et longerons, les tuyères s'enfoncent dans les longerons. Aucun booléen
   n'est appliqué (le kit n'en propose pas, et l'ADR-0008 privilégie le détail par primitives).
   Invisible au rendu, mais un maillage non-manifold aux jonctions — sans conséquence pour un
   rendu opaque, à savoir si un jour on veut de la transparence ou de la physique fine.
4. **Une fonction locale, `_disc_stack()`**, empile des anneaux coaxiaux à l'axe Z pour le capteur
   dorsal, parce que `ak.add_lathe()` ne tourne qu'autour de l'axe Y (tuyères, canons). Elle
   n'utilise que des primitives du kit et **ne le modifie pas** ; elle est identique dans son
   principe à celle de `build_needle_scout.py`. **Suggestion** (hors périmètre de ce brief) : si
   une troisième coque en a besoin, ce serait le bon moment pour promouvoir un `add_lathe_z()`
   dans `aegis_kit.py` plutôt que de la dupliquer une fois de plus.
5. **Aucun test en jeu.** La coque n'a été jugée qu'en rendu Cycles avec l'éclairage de
   `tools/render-hull.py` (key + fill + rim). L'éclairage réel de `graybox.tscn` diffère ; c'est
   à la session principale de confirmer après intégration, notamment l'intensité perçue du
   magenta émissif (facteur 2,5 dans le kit).
6. **`Engine_L`/`Engine_R` ne sont pas consommés** aujourd'hui : conforme au brief, qui les
   demande pour une double traînée ultérieure.

Aucun critère du brief n'a été jugé impossible ou ambigu.
