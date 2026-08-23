# BRIEF-0045 — Retourner `Spike_03` et `Spike_04` vers l'avant : compte-rendu

*Livré le 2026-08-23. Coque `pale_leviathan.glb` régénérée
(sha256 `7b96674bda938c0ee28296beb7d9e212642e1343b2d13891144516cf08308bf2`),
script `tools/blender/build_pale_leviathan.py` modifié sur **quatre triplets**,
planche de recette `BRIEF-0045-planche-quatre-vues.png`.*

**Verdict : LIVRÉ.** Les quatre épines pointent maintenant dans le demi-plan avant. Le prix payé —
un seul, mesuré, énoncé plus bas — est une **arche de 22 à 28 cm** sur les deux épines retournées ;
il est imposé par le harnais de dégagement du script, pas par le rendu.

---

## 1. Ce qui a changé, à la pièce près

Diff du script : **`ctrl` et `tip` de `Spike_03` et `Spike_04`**, plus le commentaire qui les
justifie. Rien d'autre.

`root` et `r0` sont restés intouchés **volontairement** : `_build_masts()` les relit pour poser le
socle, l'embase, le jonc et le nodule de chaque mât — autrement dit ils alimentent `Body`. Les
déplacer aurait déplacé de la matière dans la coque, ce que le brief interdit.

Preuve, relevée en comparant les accesseurs du `.glb` avant/après (positions, normales, UV,
tangentes, indices, matériau — hachés par maillage) :

| | maillages |
|---|---|
| **identiques bit à bit (24)** | `Body`, `Core`, `Heart`, `Maw_Lip`, `Node_01..03`, `Plate_01..04`, `Ring_01..05`, `Shell_Crescent`, `Shell_Ring`, **`Spike_01`, `Spike_01_Mid`, `Spike_01_Tip`, `Spike_02`, `Spike_02_Mid`, `Spike_02_Tip`** |
| **modifiés (6)** | `Spike_03`, `Spike_03_Mid`, `Spike_03_Tip`, `Spike_04`, `Spike_04_Mid`, `Spike_04_Tip` |

44 nœuds avant, 44 après, **mêmes noms** (contrat de noms intact). Seuls ont bougé :
`Spike_03_Mid/_Tip`, `Spike_04_Mid/_Tip`, `Muzzle_Spike_03`, `Muzzle_Spike_04`. Les nœuds racines
`Spike_03` et `Spike_04` sont **au millimètre où ils étaient** — leurs mâts n'ont pas bougé non plus.

---

## 2. Les six preuves demandées

### Preuve 1 — les quatre angles

Axe `Spike_NN → Muzzle_Spike_NN`, composé depuis les translations parent→enfant du glTF, projeté
dans le plan de jeu (x = X godot, y = −Z godot ; **le joueur est à −90°**). Même convention et même
outil de mesure que le tableau du brief — qui est reproduit **à l'identique** sur la coque d'avant,
ce qui valide l'instrument avant de s'en servir.

| Épine | avant | après | axe après (x ; y) | dans [−160° ; −20°] |
|---|---|---|---|---|
| `Spike_01` | −111,3° | **−111,3°** | (−0,895 ; −2,294) | ✅ (inchangée) |
| `Spike_02` | −71,0° | **−71,0°** | (+0,732 ; −2,131) | ✅ (inchangée) |
| `Spike_03` | +59,3° | **−42,7°** | (+1,048 ; −0,966) | ✅ |
| `Spike_04` | +111,5° | **−138,1°** | (−0,909 ; −0,815) | ✅ |

L'éventail couvre **95,4°** avec un pas volontairement inégal : 26,8° / 40,3° / 28,2°. Aucune paire
n'est un miroir : le miroir de `Spike_01` (−111,3°) serait −68,7°, celui de `Spike_02` serait
−109,0° ; les nouvelles épines tombent à −42,7° et −138,1°, à plus de 25° de ces images.

### Preuve 2 — les bouches sont au bout

Distances euclidiennes 3D depuis l'origine de la coque (son centre de gravité géométrique et son
pivot), relevées sur les nœuds du `.glb` :

| Épine | centre → `Spike_NN` | centre → `Muzzle_Spike_NN` | écart |
|---|---|---|---|
| `Spike_01` | 4,320 m | **5,496 m** | +1,176 m ✅ |
| `Spike_02` | 4,373 m | **5,926 m** | +1,553 m ✅ |
| `Spike_03` | 4,316 m | **5,289 m** | +0,974 m ✅ |
| `Spike_04` | 4,686 m | **5,211 m** | +0,525 m ✅ |

Les quatre bouches sont strictement plus loin du corps que la base de leur épine, et elles restent
posées sur l'axe de la pièce (elles sont construites à `t = port` sur la Bézier, décalées de la
normale de section — la géométrie ne peut pas les mettre ailleurs).

### Preuve 3 — aucune interpénétration

Deux mesures indépendantes, l'une sur le `.glb` livré, l'autre par le harnais du script.

**(a) Sur le `.glb`, coquille rejouée comme le combat l'écrit.** `Shell_Ring` tourné autour de Y sur
**12 positions d'orbite** (pas de 30°, période 9 s), `Shell_Crescent` et `Plate_01..04` entraînés
par la hiérarchie, puis **chute de plaque** rejouée avec la formule exacte de
`leviathan_combat._tick_plate_falls()` — bascule `fall × 135°` autour de la tangente, écartement
radial `fall × 1,8 m`, affaissement `−1,2 fall²` — à `fall ∈ {0,25 ; 0,50 ; 0,75 ; 1,00}`, et pour
les **deux** conventions d'axe qui coexistent dans le dépôt (`base_angle = i·90°` du runtime, et
l'angle géométrique réel de la plaque). Nuages denses (sommets + centroïdes + milieux d'arêtes),
distance minimale surface à surface.

| Épine | plaques en place, 12 orbites | pendant une chute de plaque |
|---|---|---|
| `Spike_01` | +109,7 mm (orbite 240°) | +2,8 mm (orbite 30°, chute 0,50) |
| `Spike_02` | +184,7 mm (orbite 120°) | +12,5 mm (orbite 150°, chute 0,75) |
| `Spike_03` | **+114,1 mm** (orbite 150°) | **+2,3 mm** (orbite 240°, chute 0,75) |
| `Spike_04` | **+503,9 mm** (orbite 0°) | **+24,6 mm** (orbite 0°, chute 0,75) |

**Ces huit valeurs sont identiques au millième près à celles de la coque d'avant.** Ce n'est pas une
coïncidence et c'est vérifiable : le minimum est atteint sur la **rotule d'épaule**, la seule partie
de l'épine qui passe à portée de la coquille — et elle n'a pas bougé. Tout ce qui a bougé est à
`r ≥ 4,2 m`, hors de la piste des plaques (`r ≤ 3,74 m` au repos).

Marge minimale, toutes pièces et toutes poses confondues : **+2,3 mm**. C'est faible, c'est
l'existant, et ce n'est pas une régression.

**(b) Par le harnais du script** (soupes de triangles + BVH, rotations réécrites en repère Godot,
sphères d'exclusion aux charnières) — la table est imprimée à chaque build :

| Contrôle | avant | après |
|---|---|---|
| `Shell_Ring` / coque, orbite 360° | 77,0 mm | **77,0 mm** |
| `Shell_Crescent` / coque, orbite × bascule 65° | 241,3 mm | **241,3 mm** |
| `Plate_01..04` / coque, coquille et entre elles | 71,3 mm | **71,3 mm** |
| `Spike_01..04` / coque, pointage ±40° | 190,3 mm | **199,7 mm** ⬈ |
| `Spike_0X_Mid` et `_Tip` / coque et chaîne, flexion ±25° | 87,2 mm | **87,2 mm** |
| `Core`, `Maw_Lip`, `Node_0X`, `Ring_0X` | 166,5 / 75,9 / 97,2 / 63,6 mm | **idem** |

Aucune ligne ne baisse ; celle des épines monte de 9,4 mm. Le build **refuse d'exporter** si une
marge tombe à zéro : le `.glb` livré est donc un `.glb` qui a passé cette porte.

**(c) Épine contre épine** — angle mort du harnais, mesuré à part sur le `.glb` :

| Paire voisine | avant | après |
|---|---|---|
| `Spike_01` ↔ `Spike_04` | 1 487 mm | **783 mm** |
| `Spike_02` ↔ `Spike_03` | 1 516 mm | **475 mm** |

C'est le vrai coût de silhouette et il est énoncé au §3. 475 mm sur une coque de 11 m, c'est 4,3 %
de l'envergure, soit ~19 px sur la vue de dessus de la planche : les deux lames se lisent séparément
(le vérifier sur le panneau « APRÈS » de la planche).

### Preuve 4 — budgets

Relevés par `tools/blender/inspect_glb.py` sur le fichier livré, et par le contrat d'export.

- **Triangles : 27 710** — *exactement* le compte d'avant (la topologie n'a pas changé, seules des
  positions de sommets ont bougé). Plafond du brief 30 000, contrat 40 000. ✅
- **Boîte englobante Godot : 11,0307 × 3,1620 × 13,9972 m** (avant : 11,0313 × 3,1620 × 13,9972).
  Sous le plafond 12,0 × 3,4 × 15,0 du brief avec 8 %, 7 % et 7 % de marge. **Centre
  (−0,0003 ; +0,0110 ; −0,0014)**, pivot centré à 0,3 mm en X pour une tolérance de 20 mm. ✅
- **Matériaux** (part en triangles / en sommets / en aire) :

| Matériau | après | avant | cible du brief |
|---|---|---|---|
| `AA_Hull` | 33,7 % / 35,2 % / 50,5 % | 33,7 % / 35,2 % / 50,5 % | ≥ 30 % ✅ |
| `AA_Emissive_Engine` | 8,5 % / **7,8 %** / 4,7 % | 8,5 % / 7,8 % / 4,7 % | ≤ 8 % ⚠️ voir ci-dessous |
| `AA_Greeble` | 17,5 % / 17,9 % / 14,2 % | 17,5 % / 17,9 % / 14,2 % | ≤ 20 % ✅ |
| `AA_Panel` 18,1 % · `AA_Trim` 20,7 % · `AA_Glass` 0,9 % · `AA_Marking_Red` 0,6 % (triangles) | | | |

⚠️ **Honnêteté sur l'émissif** : `AA_Emissive_Engine` vaut 7,8 % **en sommets** (la métrique du
BRIEF-0041, qui a posé la cible ≤ 8 %) mais **8,5 % en triangles**. Le chiffre est **strictement
inchangé** par ce brief — aucune face n'a changé de matériau, la répartition est celle de la coque
validée. Si la cible doit valoir sur les triangles, c'est un écart préexistant à traiter dans son
propre brief, pas une régression de celui-ci.

### Preuve 5 — UV et tangentes

145 primitives dans le `.glb` (c'est le compte de « surfaces » côté Godot),
**145 avec `TEXCOORD_0`, 145 avec `TANGENT`** — identique à la coque d'avant. `_triangulate_ngons()`
et le dépliage box (`TEXELS_PER_METER = 0,18`) sont dans le chemin de build et n'ont pas été touchés.

Précision méthodologique (`.claude/resources/pratique-revue-asset.md`) : pour les **UV**, le fichier
fait foi — rien ne les reconstruit à l'import, c'est donc la mesure qui compte. Les tangentes, elles,
seraient refabriquées par Godot (`meshes/ensure_tangents=true`) ; leur présence dans le fichier est
un bonus, pas la preuve. Le comptage a été fait sur les deux fichiers avec le même outil.

### Preuve 6 — déterminisme

```
./scripts/build-hull.sh --check pale_leviathan
[build-hull]   déterminisme OK — 7b96674bda938c0ee28296beb7d9e212642e1343b2d13891144516cf08308bf2
```

Deux exécutions consécutives (`-t 1` forcé par le script), sha256 identique.

**Contrôle de l'instrument** : avant de toucher au script, l'ancienne version a été rejouée depuis
`git show HEAD:` — elle a reproduit `98529ce703faf6…`, c'est-à-dire **exactement le `.glb` qui était
sur disque**. La chaîne de build est donc reproductible de bout en bout, et la coque d'avant utilisée
comme témoin dans tout ce rapport est bien celle du dépôt.

---

## 3. Le prix payé, et pourquoi il a fallu le payer

### Ce qui a bloqué la version « à plat »

La première implémentation gardait les deux épines **dans le plan de la coque** (z inchangé) et
n'a pas passé le build :

```
CONTRAT ROMPU — pièces mobiles qui mordent la coque :
  - Spike_0X_Mid et _Tip : Spike_03 : pointage -40 deg / flexion +0 deg (y) / Spike_03_Mid
```

Diagnostic mesuré, pas supposé : le harnais éprouve chaque épine sur **pointage ±40° × flexion ±25°**
(la provision d'articulation de BRIEF-0040). Une épine tournée vers l'avant depuis une racine posée
à l'azimut **195,3°** dévie de 58° de sa direction radiale ; braquée de 40° de plus, elle en dévie de
98° et **son milieu revient vers l'axe** — de `r = 5,1 m` à `r = 4,00 m`, c'est-à-dire pile sur le
**mât de `Spike_02`** (azimut 165,6°, `r = 4,15 m`, sommet z = 1,10). Morsure de 8 cm.

Il n'y a pas d'échappatoire dans le plan, et ce n'est pas une opinion : balayage systématique de
`ctrl` × `tip` sur une grille — **504 géométries** retenues par la contrainte de boîte, dont **455**
également dans le demi-plan avant, chacune évaluée sur les **25 poses** du harnais (5 pointages ×
5 flexions) contre le nuage dense de `Body`. **Aucune** ne tient à longueur constante. Les seules
qui dégagent au niveau de l'existant (≥ +50 mm) sont des moignons de **1,9 à 2,0 m de corde** contre
4,49 m ; en descendant le seuil à +20 mm on ne monte qu'à 2,6 m, et le meilleur score de tout le
balayage est **+51 mm** — l'existant, pas mieux. Même constat pour `Spike_04` (725 candidats) : les
survivantes font **1,0 à 1,9 m** contre 2,68 m. Autrement dit : **à plat, retourner ces épines coûte
plus de la moitié de leur longueur**, ce qui inverse la hiérarchie que le brief protège
explicitement — `Spike_03` deviendrait plus courte que `Spike_04`, le « moignon » désigné.

### Ce qui a été payé à la place : une arche

Les deux épines retournées **s'arquent** au-dessus des mâts qu'elles survolent au pointage extrême :

| | `ctrl.z` | `tip.z` | z de la fibre à mi-course | crête du maillage |
|---|---|---|---|---|
| `Spike_03` avant | 1,14 | 0,98 | 1,095 m | 1,492 m |
| `Spike_03` après | **1,58** | 0,98 | **1,315 m** (+22 cm) | **1,492 m** (inchangée) |
| `Spike_04` avant | 1,12 | 0,94 | 1,070 m | 1,454 m |
| `Spike_04` après | **1,55** | **1,20** | **1,350 m** (+28 cm) | **1,506 m** (+5,2 cm) |

Deux choses limitent la casse, et elles sont mesurées :

1. **L'arche reste sous la rotule d'épaule.** Le point le plus haut d'une épine était déjà sa rotule
   (1,45 à 1,50 m) ; l'arche culmine plus bas. La **hauteur de la coque ne bouge pas d'un micron** :
   3,1620 m avant comme après, imposée par le noyau (+1,592).
2. **Vu de la caméra de jeu (20° de la verticale), 28 cm se projettent en 9,6 cm** sur une coque de
   11 m, soit 0,9 % de l'envergure — invisible. C'est le panneau « vue de jeu » de la planche.

`Spike_03` garde sa pointe piquée vers le bas (0,98 m) comme les autres ; `Spike_04` est la seule
dont la pointe remonte (1,20 m au lieu de 0,94 m), parce que c'est sa pointe, et elle seule, qui
survole le mât de `Spike_01` au pointage +40°. Garder sa pointe piquée exigeait une arche à 1,49 m,
c'est-à-dire **au-dessus de la crête des plaques** : le remède aurait été pire.

### Ce que la silhouette perd, ce qu'elle garde

| Critère | avant | après | verdict |
|---|---|---|---|
| Cordes (bout de pièce → racine) | 5,79 / 5,07 / 4,50 / 2,69 m | **5,79 / 5,07 / 4,35 / 2,68 m** | hiérarchie et inégalité intactes (rapport 2,15 → 2,16) |
| Éventail des axes | 2 avant, 2 arrière | **4 avant, pas inégal** | objectif du brief |
| Jour entre voisines | 1 487 / 1 516 mm | **783 / 475 mm** | **c'est le vrai coût** |
| Aire de silhouette, vue de dessus | 94 408 px | **94 308 px** (−0,1 %) | inchangée |
| Aire de silhouette, vue de jeu | 92 392 px | **92 648 px** (+0,3 %) | inchangée |
| Boîte de silhouette, vue de dessus | 355 × 433 px | **356 × 433 px** | inchangée |

**Ce qui se perd, en clair** : l'arrière de la coque (haut de l'écran) perd ses deux cornes ; il ne
reste là qu'un ovoïde lisse. Et `Spike_03` longe désormais le bord de la coque au lieu de s'en
détacher franchement — c'est la conséquence directe de l'obligation d'aller chercher x = −5,52 m
(voir plus bas). Les deux se voient sur la comparaison de la planche, et j'estime que ce sont des
changements, pas des dégradations : la coque lit maintenant comme une bête qui **tend quatre lames
vers le joueur**, ce que le combat raconte, au lieu de deux devant et deux derrière.

### La contrainte cachée qui a dicté la forme de `Spike_03`

`Spike_03` porte à elle seule la borne **−X** de la boîte englobante (`Spike_01`, gelée, porte la
borne +X à +5,516 m). Une lame avant qui se serait contentée de la portée de `Spike_02` (5,05 m)
aurait ramené la largeur à 10,56 m — **4 % d'écart, contrat rompu à ±3 %** — et surtout décentré le
pivot de 23 cm pour une tolérance de 2 cm. D'où la courbe qui sort d'abord au large : le ventre de
la Bézier est à x = −5,52 m, et l'enveloppe mesurée sur le `.glb` vaut −5,5157 → **−5,5172 m**, soit
1,5 mm de dérive et 0,75 mm de décentrage.

---

## 4. Limites connues

- **La provision d'articulation ±40° n'est pas utilisée par le jeu.** `_spine_track` et
  `SPINE_TRACK_DEG` existent dans `leviathan_combat.gd` mais **aucune ligne ne les applique** au
  nœud : les épines sont posées au repos et rien ne les braque. L'arche du §3 est donc payée pour
  une porte de build, pas pour un mouvement à l'écran. Ce n'est pas à la forge d'en décider : le
  harnais est le contrat, il a été satisfait sans le modifier. Si le concepteur juge la provision
  caduque, la relâcher rendrait les deux épines parfaitement plates — c'est une ligne du script.
- **La marge minimale du couple épine/plaque en chute reste de +2,3 mm** (`Spike_03`, orbite 240°,
  chute 0,75). Elle est identique à l'existant et le brief ne la vise pas, mais elle est fine : une
  future retouche des plaques peut la faire passer sous zéro sans que rien ne le signale, le harnais
  du script ne mesurant jamais les épines contre la coquille.
- **`./scripts/check.sh` n'a pas été exécuté.** Une autre session écrit en parallèle dans
  `assets/imported/models/ships/` ; un `--import` de ma part y aurait généré des `.import` qui ne
  m'appartiennent pas. Le `.glb.import` de la coque ne contient aucun hachage de source, il n'a donc
  pas besoin d'être régénéré — mais la porte de qualité reste à passer côté intégration.
- **La coque n'a pas été vue en jeu**, seulement en rendu Cycles (qui flatte) : le post-process
  rétro à 960×540 écrase le détail fin. Ici la lecture repose sur la géométrie et sur des pièces de
  4 m, donc le risque est faible, mais la règle du dépôt est de juger en jeu.

## 5. Suggestions

1. **Trancher sur `_spine_track`.** Soit on câble le braquage (et l'arche se justifie pleinement),
   soit on retire les constantes mortes — dans ce cas, ramener `ctrl.z`/`tip.z` de `Spike_03` et
   `Spike_04` à leurs valeurs plates redonne exactement la silhouette d'origine sur l'axe z, sans
   toucher aux angles.
2. **Étendre le harnais aux épines contre la coquille et entre elles.** Les deux angles morts
   relevés ici (marge +2,3 mm contre une plaque en chute, 475 mm entre voisines) ne sont visibles
   qu'avec un outil hors du script. Le code de mesure utilisé pour ce rapport est reproductible et
   tiendrait dans `_clearance_table()`.
3. **Refaire le playtest sur le grief d'origine.** L'objectif est la cohérence du tir ; la géométrie
   est corrigée, mais `_aim_spine()` continue de viser le joueur plutôt que de prolonger l'axe de la
   pièce (avec son commentaire qui dit « la cohérence complète demanderait de reforger la coque »).
   Cette reforge est faite : le commentaire et, si l'écart mesuré est petit, la logique de visée
   peuvent maintenant suivre.

## 6. Fichiers

| Fichier | État |
|---|---|
| `tools/blender/build_pale_leviathan.py` | modifié (4 triplets + commentaire) |
| `assets/imported/models/bosses/pale_leviathan.glb` | régénéré, sha256 `7b96674b…` |
| `docs/forge/output/BRIEF-0045-planche-quatre-vues.png` | planche 4 vues + vue de dessus annotée avant/après |
| `docs/forge/output/BRIEF-0045-report.md` | ce rapport |
| `assets/licenses/ASSET_PROVENANCE.csv` | ligne du `.glb` mise à jour (hash + brief) |
