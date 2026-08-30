# BRIEF-0095 — Les portes du pont d'envol

- **Statut** : livré
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-08-30
- **Modifie** : `tools/blender/build_bay_kit.py` → `assets/imported/models/backgrounds/bay_kit.glb`

## Texture

**Aucune demande de texture.** Le kit de hangar existant s'habille par facteurs PBR et par les
matériaux nommés de la coque ; ses deux battants doivent lire comme la même pièce que le cadre
qui les entoure. Une carte de détail sur 6,00 × 8,50 m vus à 23 px/m ne rendrait rien que le
relief ne rende déjà.

**Dépliage attendu** : `ak.box_project_uv()`, mêmes tuiles/m que `bay_frame_*` — mesure-les dans
le script, ne les redevine pas. `TEXCOORD_0` compté au harnais, comme partout.

## Le défaut, tel qu'il se voit

Les deux battants n'existent pas dans le kit. Le moteur les **fabrique lui-même**
(`cortege_bay.gd:269`, `_build_doors()`) : deux `BoxMesh` gris de 3,00 × 0,14 × 8,50, matériau
uni, aucune arête. Tout ce qui les entoure — cadre, paroi, plancher, rails, coffret — vient de
toi ; eux seuls sont des boîtes.

C'est le reproche déjà entendu sur ce hangar, et il est resté vrai sur la seule pièce qu'on
n'avait pas forgée : « on dirait des jeux faits avec des formes carrées » (opérateur), puis
« les portes des ponts de décollage » (opérateur, 2026-08-30, en jouant).

## Ce qui est demandé

**Deux pièces neuves dans `bay_kit.glb`**, aux noms et points d'assemblage **gelés** — le moteur
les monte par leur nom, comme les sept autres :

| Pièce | Ce que c'est | Origine |
|---|---|---|
| `bay_door_left`  | le battant bâbord, celui qui se retire vers −X | **au centre de sa surface, dans le plan de la peau** (y = 0), arête de jonction sur x = 0 |
| `bay_door_right` | le battant tribord, miroir exact | idem, arête de jonction sur x = 0 |

**Cotes non négociables** — elles viennent du moteur, pas d'un choix :

- **emprise fermée** : chaque battant couvre `x ∈ [−3,00 ; 0]` (resp. `[0 ; 3,00]`) et
  `z ∈ [−4,25 ; +4,25]`. Fermés, les deux ne laissent **aucun jour** : le puits ne doit pas
  fuir sa lueur magenta quand il ne produit pas — c'est tout le contraste qui fait lire
  l'ouverture ;
- **épaisseur** ≤ **0,22 m**, et le point le plus haut du battant ≤ **+0,18 m** au-dessus de la
  peau : il glisse **sous la lèvre du coaming**, il ne la chevauche pas ;
- **course** : le moteur les retire de 3,00 m sur ±X. Rien ne doit dépasser en −X (resp. +X)
  au-delà de l'emprise, sinon le battant ouvert sort du hangar et flotte sur le bordé.

**Ce qui doit les faire lire comme des portes**, et non comme deux dalles :

- une **arête de jonction dentelée** au milieu : les deux battants s'interpénètrent quand ils
  sont fermés (une denture franche, 3 à 5 dents, pas un simple biseau). C'est la seule chose
  qu'on voit à coup sûr, parce qu'elle est au centre de l'ouverture ;
- des **caissons en creux** sur la face visible — 2 ou 3 par battant, arêtes marquées ;
- une **nervure diagonale** ou des **rainures de renfort** qui donnent un sens de lecture : un
  battant qui glisse doit dire de quel côté il part **même à l'arrêt** ;
- des **logements de rail** aux deux extrémités en Z, là où le battant s'engage dans le cadre.

**Émissif** : deux **traits de bordure** au plus, sur l'arête de jonction, dans la teinte d'état
du hangar. Ils sont là pour signer la ligne de fermeture ; ils ne doivent pas concurrencer la
lueur du puits, qui est l'information. ⚠️ Le moteur baisse tout émissif de coque à **0,45**
d'énergie (`cortege_skin.gd`) — calibre en conséquence, un trait jugé bon à 1,0 ressort en laser.

## Contraintes

- **IP** : rien d'identifiable, aucune livrée, aucun marquage typographique.
- **Palette** : celle du kit de hangar, inchangée. Cyan `#3FD9E8` et corail `#FF5A3D` restent
  interdits (réservés aux tirs).
- **Budget** : ≤ **1 200 tri pour les deux battants réunis**. C'est une pièce vue de loin, sept
  fois dans le niveau, et le kit entier tient déjà dans son enveloppe.
- **Déterminisme** : `./scripts/build-hull.sh --check bay_kit` doit rendre **0 octet divergent**,
  `-t 1` forcé.
- **Plafond** : rien ne monte au-dessus de +0,18 m. Le plan de jeu est à Y = 0 sur la coque
  descendue à −3,5 ; un battant qui monterait resterait du décor, mais il masquerait le combat.

## Ce que ce brief ne touche pas

- **Les sept pièces existantes du kit** : `bay_frame_left/right/top`, `bay_inner_wall`,
  `bay_floor`, `bay_launch_rail`, `bay_service_block`. Acceptées, livrées, câblées, mesurées.
  N'y touche pas — un seul octet qui bouge et je dois revérifier sept montages.
- **La coque** `long_cortege.glb` et ses marqueurs.
- **L'animation** : la course, le temps d'ouverture et l'état « pont mort, portes bloquées »
  sont du moteur. Tu livres les deux volumes, rien de plus.

## Vérification

- Le harnais du script **échoue** s'il manque `TEXCOORD_0`, si le budget est dépassé, ou si
  l'emprise fermée laisse un jour.
- **Compte de triangles** et **emprise mesurée** (bbox des deux battants) dans le rapport.
- **Une planche 4 vues** (`docs/forge/output/BRIEF-0095-planche-portes.png`), dont **une vue
  fermée et une vue ouverte à 3,00 m** — c'est la seule qui prouve que la course ne fait pas
  sortir le battant du hangar. Sans planche, le livrable n'est pas validé (ADR-0006).
- Ligne de provenance dans `assets/licenses/ASSET_PROVENANCE.csv`.
