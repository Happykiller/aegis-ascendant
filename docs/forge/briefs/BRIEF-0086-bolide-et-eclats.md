# BRIEF-0086 — Le bolide et ses éclats : donner un corps aux impacts sur la lune

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-08-26

## Objectif

Remplacer les **deux sphères lisses** qui tiennent lieu de bolide et d'éclats dans les impacts sur
la lune (phase 2, `ADR-0027`) par deux petites coques forgées : un **bolide** et un **éclat**.

Demande de l'opérateur, en jouant le 2026-08-26 : « les astéroïdes qui se crashent sur la lune sont
un simple cercle jaune, faut les 3D, texture, etc ».

## ⚠️ Lis ça d'abord : la géométrie ne suffira PAS, et il faut le savoir avant de modéliser

Le bolide actuel est une sphère de **0,85 de rayon**, posée sur une lune à **96 unités de la
caméra**. À cette distance le cadre visible fait ~115 m de haut pour 540 px de rendu utile :

> **le bolide occupe 8 pixels.**

Une coque splendide y ferait toujours 8 pixels. Ce qui rend l'impact lisible n'est donc pas ton
maillage mais **la traînée et la gerbe** — qui sont du **code**, et que je traite de mon côté.

**Ce que ça change pour toi, concrètement :**

- **Ne mets aucun détail sous ~40 cm.** Il ne sera jamais échantillonné. Le budget va dans la
  **silhouette** : un caillou qui n'est pas une boule, avec deux ou trois facettes franches qui
  accrochent une lumière rasante et font tourner la forme pendant la chute.
- **La silhouette est TOUT.** À 8 px, on ne lit qu'un contour. Une sphère lit comme un point ; un
  éclat anguleux lit comme un débris. C'est le seul critère de recette.
- **Le bolide sera agrandi côté code** (je vise ~3× son diamètre actuel) et portera une traînée.
  Modélise-le donc pour être vu **de trois quarts en chute**, pas de face.

## Texture (ADR-0028)

**Aucune demande nouvelle.** Les deux pièces réutilisent
[`TEX-0002-asteroid-rock-height.json`](../textures/TEX-0002-asteroid-rock-height.json) — c'est de la
roche d'astéroïde, et c'en est. Les cartes sont déjà dérivées et en jeu.

⚠️ **Conséquence sur tes UV, et elle est stricte** : la tuile de `TEX-0002` est calée sur **8 m de
roche**. Un bolide de ~2,5 m de diamètre n'en voit donc qu'un tiers. Déplie en **projection en
boîte à la même échelle monde que les trois astéroïdes du survol** — surtout pas en normalisant
sur la pièce, ce qui donnerait un grain trois fois trop fin et ferait lire le bolide comme du
gravier au lieu d'un bloc. **Donne les tuiles/m au rapport.**

⚠️ **UV obligatoires et `TEXCOORD_0` COMPTÉ dans le `.glb`** — compté, jamais supposé (`ADR-0028`).

## Contraintes

- **IP** : création originale, aucun élément identifiable d'une licence.
- **Palette** : ⛔ **ni cyan, ni corail** (réservés au tir allié et au tir ennemi). ⚠️ Et **aucun
  émissif** dans le `.glb` : la chaleur du bolide est posée par le code (matériau non éclairé,
  émission ×3,4), et une émission cuite dans la coque s'y ajouterait sans qu'on puisse l'éteindre.
  Livre une couleur de roche froide et sombre, comme les astéroïdes du survol.
- **Techniques** : Blender 4.5 LTS, headless, déterministe. Kit `tools/blender/lib/aegis_kit.py`
  réutilisé **sans modification**. N-gons triangulés avant export.
- ⚠️ **`ak.export_hull()` t'a posé problème sur `BRIEF-0085`** (contrat incompatible avec des corps
  qui portent une translation). Ici les deux pièces sont **à l'origine** — le contrat devrait
  convenir. Si ce n'est pas le cas, refais comme au 0085 et dis-le au rapport ; ne touche pas au kit.

### Budgets

| Pièce | Triangles | Raison |
|---|---|---|
| `Bolide` | **≤ 400** | 8 px à l'écran. Au-delà, on paie un détail que le rendu n'échantillonne pas |
| `Shard` | **≤ 150** | 14 exemplaires simultanés, et plus petits encore que le bolide |

⚠️ Ce sont des **plafonds**, pas des cibles. Si la silhouette tient en 180 triangles, livre 180.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/build_impact_debris.py` | script de construction des DEUX pièces, rejouable, déterministe |
| `assets/imported/models/vfx/bolide.glb` | le bolide (LFS) |
| `assets/imported/models/vfx/impact_shard.glb` | l'éclat (LFS) |
| `docs/forge/output/BRIEF-0086-report.md` | mesures réelles, tuiles/m, budgets tenus, choix de silhouette |
| `docs/forge/output/BRIEF-0086-planche-silhouettes.png` | **les deux pièces rendues À 8 ET À 24 PIXELS**, sur fond noir, à côté d'une sphère lisse de même taille |

⚠️ **La planche est le cœur de la recette de ce brief.** Ce n'est pas une belle vue : c'est la
**preuve que la silhouette survit au sous-échantillonnage**. Si à 8 px ton bolide et une sphère lisse
sont indiscernables, la coque ne sert à rien et il faut retravailler la silhouette, pas la texture.
Rends aussi une vue de trois quarts en chute, l'angle réel.

## Contrat de noms — lu par le code

| Nœud | Ce que c'est |
|---|---|
| `Bolide` | racine du bolide, **à l'origine**, plus long que large |
| `Shard` | racine de l'éclat, **à l'origine** |

## Provenance

Une ligne par asset dans `assets/licenses/ASSET_PROVENANCE.csv`, **en append shell (`>>`)**.
`asset_type=model3d`, `source_tool=asset-forge (Blender 4.5.11, script)`,
`license=proprietary-internal`, `prompt_file=docs/forge/briefs/BRIEF-0086-bolide-et-eclats.md`.

## Critères d'acceptation

- [ ] `blender45 -b -P tools/blender/build_impact_debris.py` régénère les deux `.glb` sans erreur
- [ ] Budgets tenus, chiffres réels au rapport
- [ ] **`TEXCOORD_0` sur 100 % des primitives**, compté dans chaque `.glb`
- [ ] Dépliage en boîte **à la même échelle monde que les astéroïdes du survol**, tuiles/m au rapport
- [ ] **Aucun émissif**, aucun cyan, aucun corail
- [ ] Les deux pièces ont leur origine **au centre**, pas décalée
- [ ] **Planche de silhouettes rendue et regardée** : à 8 px, le bolide se distingue d'une sphère lisse
- [ ] `./scripts/build-hull.sh --check` : deux exécutions, `.glb` byte-identique
- [ ] Provenance renseignée

## Hors périmètre

Pas de `.tscn`, `.tres`, code ni tests. **Aucune texture** (`TEX-0002` est réutilisée). **Aucun
effet** : traînée, gerbe conique, flash et trajectoire sont du code, et je m'en charge — c'est ce
qui rendra tes coques visibles, pas l'inverse.
