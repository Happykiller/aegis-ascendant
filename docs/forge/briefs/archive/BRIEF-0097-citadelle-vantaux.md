# BRIEF-0097 — les vantaux de la Citadelle : la porte s'ouvre

- **Statut** : livré
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-09-04

## Objectif

Remplacer `citadel_gate` — une poutre d'un seul tenant — par **deux vantaux qui se rétractent
dans deux logements latéraux**, et donner à la denture la **mâchoire en vis-à-vis** qui lui
manque. C'est le **LOT 4** du plan
[`2026-09-03-citadelle-de-defense-midpoint.md`](../../../plans/2026-09-03-citadelle-de-defense-midpoint.md) :
**l'ouverture**.

## Contexte

Le verrou est joué, mesuré, et ses quatre états se voient (LOTS 1 à 3). Ce qui manque est la
dernière chose que la séquence promet : **la route s'ouvre**. Aujourd'hui la porte est simplement
**escamotée** à `CLEARED` — un palliatif que j'ai écrit au LOT 2 et documenté comme tel : « ce
n'est pas l'ouverture du lot 4, c'est la version qui ne mente pas en attendant ».

⚠️ **ET LA CAPTURE DU LOT 2 A NOMMÉ LE DÉFAUT QUI VA AVEC.** La denture, posée **sur le dessus**
de la poutre, dents vers le haut et **sans rangée en vis-à-vis**, se lit comme un **créneau de
rempart** ou un peigne — pas comme un joint de battants. « Il manque le vantail : pas de tableau,
pas de ligne de refend au milieu, pas de deux moitiés. » Les deux problèmes n'en sont qu'un : une
porte qui ne montre pas sa jointure ne se lit pas comme une porte, et une porte qui n'a pas deux
moitiés ne peut pas s'ouvrir.

## Contraintes

**IP.** Aucun nom, silhouette ou élément identifiable d'une licence (spec §0.2).

**Palette.** Faction **Unisson** (`ak.FACTION_NULL_CHOIR`), les sept slots de `ak.MATERIAL_ORDER`
et eux seuls. `AA_Hull` pour la masse, `AA_Greeble` pour les creux, la denture et la machinerie,
`AA_Trim` **au plus 3 % de l'aire**.

⚠️ **AUCUN ÉMISSIF, ET LA RÈGLE EST PLUS DURE QU'AU `BRIEF-0096`.** Le moteur détruit
`citadel_relay` et `citadel_core` séparément, et c'est leur lueur qui rend leur mort visible. Un
vantail qui brillerait entrerait en concurrence avec les deux seuls signaux d'état du verrou.

**Techniques.** Godot 4.7. Le script `tools/blender/build_citadel_kit.py` est **modifié**, pas
remplacé : les six autres pièces ne bougent pas d'un micron, et `--check` doit toujours dire
« déterminisme OK ». **Budget : +900 triangles au plus** — le kit est à 1 304 pour 3 000, il
restera donc sous 2 300.

## Les cotes — MESURÉES, et l'emboîtement est arithmétique

Toutes en repère de coque. La chaîne fait tenir trois choses en même temps : **fermé, il n'y a
aucun jour** ; **ouvert, la passe est mesurable** ; **et rien ne dépasse jamais `x = 17,20`**.

| | valeur | d'où elle vient |
|---|---|---|
| bout extérieur de la porte | **17,20** | inchangé — c'est ce qui couvre tout le plan de vol (LOT 1) |
| longueur d'un vantail | **12,90 m** | de `x = 0` à `x = 12,90`, fermé |
| course de rétraction | **4,25 m** | ouvert, le vantail va de `4,25` à `17,15` — **0,05 m sous le bout** |
| logement | `x` **12,70 → 17,20** | il chevauche le vantail fermé de **0,20 m** : aucun jour |
| passe ouverte | **8,50 m** monde | `|x| < 4,25`, soit **7,00 unités de plan** après projection |
| assise du vantail | **−6,60** | celle de la porte actuelle, inchangée |
| hauteur du vantail | **3,60 m** | sommet à **−3,00**, le plafond du décor inerte (`ADR-0041`) |
| assise du logement | **−6,90** | il est un FOURREAU : plus bas et plus haut que ce qu'il reçoit |
| hauteur du logement | **3,90 m** | sommet à **−3,00** exactement — ⚠️ pas un centimètre au-dessus |

⚠️ **LA PASSE FAIT QUATRE FOIS LA LARGEUR DU CHASSEUR, ET C'EST MESURÉ.** Le corps réel du
Specter-9 fait **1,76 unité** en travers (`body_radius = 0,88`, `ADR-0034`) : 7,00 unités de plan
lui laissent quatre fois sa largeur. La chambre du réacteur a déjà payé l'inverse — « c'est comme
si tout le cercle était un mur pour moi » — et une passe qu'il faut enfiler n'est pas une passe.

⚠️ **LE SOMMET DU LOGEMENT EST LA COTE QUI PEUT TOUT CASSER EN SILENCE.** Un fourreau doit être
plus grand que ce qu'il reçoit ; s'il monte de 30 cm au-dessus du vantail depuis la même assise,
il franchit le plafond du décor. C'est pour ça que son assise **descend** au lieu que son sommet
monte.

## La table du kit — les noms sont FIGÉS

| Nœud | Ce que c'est | Origine | Emprise demandée | Sort |
|---|---|---|---|---|
| `citadel_leaf` | **le vantail**, avec sa denture à l'extrémité INTÉRIEURE | pied, extrémité intérieure (`x = 0`) | `x` 0 → 12,90 · `s` ±0,60 · Y 0 → 3,60 | **NOUVEAU** — miroité par le moteur |
| `citadel_housing` | **le logement**, un fourreau qui reçoit le vantail | pied, côté tribord | `x` 12,70 → 17,20 · `s` ±0,80 · Y 0 → 3,90 | **NOUVEAU** — miroité |
| `citadel_gate` | la poutre d'un seul tenant | — | — | **SUPPRIMÉ** |
| les six autres | porte, portique, bastion, couronne, relais, conduit, noyau, bouclier | — | — | **INCHANGÉS, au micron** |

⚠️ **`citadel_leaf` EST MODELÉ TRIBORD ET SON ORIGINE EST SON BOUT INTÉRIEUR**, pas son centre.
C'est ce qui permet au moteur d'écrire la course comme une translation en `x` — 0 fermé, 4,25
ouvert — sans arithmétique de côté. Le miroir se fait par un yaw de π, comme les cinq pièces du
`BRIEF-0096`. ⚠️ **Et il ne peut donc PAS être centré en Z sur son origine** : il l'est en `s`
(±0,60 autour de son axe), ce qui suffit — c'est l'excentricité en `s` que le yaw de π retourne,
pas celle en `x`. Le harnais du kit doit distinguer les deux cas.

## Les deux mâchoires — c'est le critère d'acceptation

> « Il manque le vantail : pas de tableau, pas de ligne de refend au milieu, pas de deux
> moitiés. » — capture du 2026-09-04

La denture actuelle est un **peigne posé sur le dessus**. Ce qu'il faut est un **joint** :

1. **Les dents sont dans l'ÉPAISSEUR, pas sur le dessus.** Elles occupent la tranche intérieure du
   vantail sur ses 2,40 m les plus internes, et elles s'engrènent avec celles du vantail opposé.
   Fermé, les deux séries s'imbriquent et il n'y a **pas un jour** entre elles.
2. **La ligne de refend se voit.** Une porte fermée doit montrer **où** elle s'ouvrira : un joint
   vertical au centre, marqué par un décrochement d'épaisseur ou un jeu d'ombre — c'est ce qui
   fait qu'on la lit comme fermée plutôt que comme un mur.
3. **Et le compte de dents est IMPAIR par vantail**, pour que les deux séries s'imbriquent sans
   qu'une dent tombe en face d'une dent. Trois ou cinq, pas quatre.

⚠️ **Le test noir et blanc reste le juge**, comme au `BRIEF-0096` : émissifs coupés, on doit lire
« ça s'ouvre au milieu » sans une couleur.

## Texture (`ADR-0028`)

**Aucune demande, et voici pourquoi.** Les vantaux sont de la masse de coque : `TEX-0010`
(bordé plaques) et `TEX-0012` (machinerie) sont **déjà livrées et intégrées**, et le brief §1
demande de réutiliser au maximum. Surtout, le LOT 3 a **mesuré** ce qu'une carte peut espérer sur
ce niveau : `retro_post` accroche l'image à 960 × 540 et postérise à 20 niveaux, soit un pas de
12,75 niveaux de gris — **un détail dont la modulation est sous ~6 niveaux n'existe pas**
(`docs/forge/textures/README.md`). Une porte se lit par sa **silhouette** et par sa **jointure**,
pas par sa matière.

**Dépliage attendu** : `ak.box_project_uv()`, **0,200 tuile/m** — la densité du bordé, pour qu'un
raccord vantail/coque ne montre pas deux échelles. ⚠️ **`TEXCOORD_0` COMPTÉ dans le `.glb`**,
jamais supposé : trois coques du dépôt sont sorties sans UV, en silence.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/build_citadel_kit.py` | **modifié** : `citadel_gate` retiré, `citadel_leaf` et `citadel_housing` ajoutés |
| `assets/imported/models/backgrounds/citadel_kit.glb` | neuf pièces, aux noms figés |
| `docs/forge/output/BRIEF-0097-report.md` | cotes MESURÉES pièce par pièce, triangles, **et la preuve que les six pièces conservées n'ont pas bougé** |
| `docs/forge/output/BRIEF-0097-planche-vantaux.png` | la planche : fermé, à mi-course, ouvert — **et le test noir et blanc** |

## Provenance

La ligne `citadel_kit` de `ASSET_PROVENANCE.csv` est **mise à jour**, pas dupliquée : c'est le même
asset. Ajouter à ses notes la mention du `BRIEF-0097` et des deux pièces neuves.

## Critères d'acceptation

- [ ] **Les neuf nœuds portent EXACTEMENT les noms de la table**, et `citadel_gate` a disparu
- [ ] **FERMÉ, AUCUN JOUR** : les deux vantaux miroités s'imbriquent au centre, et le chevauchement
      vantail/logement vaut **0,20 m** — mesuré, pas supposé
- [ ] **OUVERT, RIEN NE DÉPASSE `x = 17,20`** : le vantail rétracté finit à 17,15 au plus
- [ ] **Le sommet du logement est à −3,00 une fois posé**, pas un centimètre au-dessus
      (`ADR-0041`, décor inerte)
- [ ] **Le test noir et blanc, émissifs coupés** : on lit « ça s'ouvre au milieu ». **C'est le
      critère qui décide**, et la planche doit le montrer aux trois positions
- [ ] **Aucun émissif** sur les deux pièces neuves — vérifié par matériau
- [ ] **Les six pièces conservées sont inchangées au micron** : même compte de triangles, mêmes
      emprises, même matériaux. Le rapport doit le PROUVER, pas l'affirmer
- [ ] **≤ 2 300 triangles** pour le kit entier
- [ ] **UV présentes et `TEXCOORD_0` COMPTÉ** dans le `.glb`
- [ ] **`./scripts/build-hull.sh --check citadel_kit` dit « déterminisme OK »**
- [ ] **Aucune normale retournée** — une pièce retournée DISPARAÎT en jeu et aucune mesure ne le
      voit. Calculer le bobinage (`_face_facing`), ne pas l'écrire
- [ ] Le rapport donne l'**emprise mesurée** de chaque pièce neuve, **et la course de rétraction
      vérifiée** : vantail à 0 puis à 4,25, sans intersection avec le logement ni dépassement

## Hors périmètre

- **L'animation.** C'est du code : le moteur interpole la course entre `OPENING` et `CLEARED`.
- **La forme solide.** Le moteur verse deux capsules qui se rétractent avec les vantaux, puis
  plus rien. C'est lui qui mesure la passe.
- **Le portique** (`citadel_pylon`) ne change pas : il descend du bout de la poutre à la lisse
  d'épaule, et ce travail-là est fait.
- **Les feux, les états, les conduits** : LOT 3, livré.
- **La respiration après le verrou** : LOT 5.
