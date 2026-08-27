# Plan — les corps ne se chevauchent pas

> « De façon globale dans le jeu je veux maintenant qu'on gère la physique, les objets n'ont
> plus le droit de se chevaucher : vaisseaux, boss, mur, réacteur, etc. C'est une nouvelle
> règle. » — l'opérateur, 2026-08-27

Loi posée dans [`docs/KB/REGLES/lois.md`](../KB/REGLES/lois.md). Moteur : `ADR-0032`
([`PlaneCollider`], [`PlaneShapes`]). Ce plan dit **où elle est tenue et où elle ne l'est pas
encore** — parce qu'une loi appliquée à un seul endroit se lit comme une loi appliquée partout,
et c'est ainsi qu'on croit un chantier fini.

## Lot 1 — la chambre du réacteur ✅ FAIT

- Le chasseur est une **capsule** (0,88 × 1,23 de demi-dimensions, mesurées sur `specter_9.glb`
  transformations de nœuds appliquées), plus un disque. C'est son **nez** qui traversait.
- Les murs rotatifs et **le noyau** sont des formes ; le noyau n'est plus franchissable.
- Un corps coincé sort par le chemin le plus court, bouts d'arc compris.
- Le point d'entrée se déduit des anneaux, et une garde refuse ce qui enfermerait.
- La chambre est remontée de 1,2 dans le plan : centrée, la géométrie ne laissait plus que
  0,04 unité pour voler sous le blindage.

## Lot 2 — les coques de boss ✅ FAIT

- Chaque boss **déclare** ses formes (`fill_solids()`), il n'écrit pas de collision. Le niveau
  ne connaît ni plaques, ni bras, ni anneaux : c'est ce qui rendra le boss suivant gratuit.
- **Pale Leviathan** : coque + plaques debout pendant l'armure ; murs rotatifs + flux dans le
  noyau. ⚠️ Jamais les deux : une coque apparaissant dans le noyau écraserait le joueur au
  moment où il a plongé pour l'oublier.
- **Choir Harvester** : corps + appendices **encore debout**. Un bras à terre laisse passer —
  c'est la récompense de l'avoir abattu.
- Un boss **en cours de descente n'oppose rien** : le rendre solide en pleine traversée
  pousserait un joueur qui n'a rien fait de mal.
- Le chasseur obéit **chez lui**, après son propre déplacement et son propre bornage : l'ordre
  compte, sinon on le corrige puis le pilotage le renfonce à l'image suivante.
- Le contact qui **blesse** est intact : `take_contact_damage` n'a pas été touché. Ne pas
  confondre « ne se chevauchent pas » et « ne se touchent pas ».

⚠️ **Ce que le lot 2 ne fait PAS** : le boss ne se laisse pas pousser. La collision est
unilatérale — le chasseur cède, la coque non. C'est voulu ici (un boss poussé par un chasseur
serait ridicule) et c'est exactement ce qui manquera au lot 3.

## Lot 3 — les vaisseaux entre eux ✅ FAIT

**Arbitrage retenu** (proposé, non contredit) : le doute se tranche par *« est-ce que le contact
EST son attaque ? »*.

- **Trois traversent** — `choir_mine`, `leech_drone`, `null_maw`. Une mine qui rebondit sur le
  chasseur au lieu d'exploser est désamorcée par sa propre collision, et rien ne le dirait :
  elle aurait l'air de fonctionner, elle tournerait autour de sa cible.
- **Les dix autres coques sont des corps.** Elles repoussent le chasseur — ce qui le sort de la
  zone de dégâts au lieu de l'y laisser mijoter. Le contact qui blesse est intact.
- **Entre pairs, la répulsion est réciproque et douce** : chacune prend la moitié. Faire céder
  une seule des deux ferait passer la nuée pour un tas de billes poussées par la dernière
  arrivée.

⚠️ **Le point technique qui n'était pas évident** : une unité sur trajectoire recalcule sa
position **entièrement** à chaque image (`EnemyPath.position_at` est pure). Une poussée écrite
dans `plane_position` disparaît à l'image suivante — la répulsion n'existerait qu'une image sur
deux, et à l'écran ça ne se lit pas comme une panne mais comme un **frémissement**. D'où un écart
persistant, réappliqué après le recalcul, **amorti** vers zéro : l'unité s'écarte puis revient sur
sa figure. Une répulsion permanente aurait déformé les nuées jusqu'à ce qu'elles ne dessinent
plus rien.

Borné (`SEPARATION_MAX`) : dix unités au même endroit ne s'éjectent pas hors de l'écran.

## Lot 4 — le décor solide ❌ À FAIRE

Les rails de la chambre, les batteries des frégates, la lune du survol. Aucun n'est un obstacle
aujourd'hui ; certains ne devraient pas l'être (le survol est un fond). À arbitrer pièce par pièce.

## Ce que le moteur sait déjà faire

| Besoin | Appel |
|---|---|
| Corps rond contre décor | `PlaneCollider.resolve(shapes, point, radius)` |
| Corps allongé (vaisseau) | `PlaneCollider.resolve_capsule(shapes, centre, axe, demi-longueur, rayon)` |
| Ligne de tir | `PlaneCollider.first_hit(shapes, de, vers, rayon)` |
| Déclarer un obstacle | `shapes.add_disc` / `add_ring_arc` / `add_capsule` |

| Écarter deux pairs | `EnemyController.nudge(offset)`, appelé par le semeur |

Le corps-contre-corps du lot 3 est traité par **répulsion douce** (chacun prend la moitié) plutôt
que par collision dure : entre unités mobiles, une collision dure fige les nuées et se lit comme
un bug. Le chasseur contre un boss reste **unilatéral** — un boss poussé par un chasseur serait
ridicule.
