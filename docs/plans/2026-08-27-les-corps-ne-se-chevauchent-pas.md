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

## Lot 2 — les coques de boss ❌ À FAIRE

Le corps du Pale Leviathan, ses plaques, ses bras, la pince et la faux du Harvester : rien ne les
empêche aujourd'hui d'être traversés. Ce sont les plus gros objets du jeu et les plus visibles.

- Déclarer chaque pièce en forme (disque pour un corps, capsule pour un bras).
- Les verser dans le jeu de formes du niveau, pas seulement du boss.
- ⚠️ Attention au **contact qui blesse** : `take_contact_damage` existe déjà. Ne pas confondre
  « ne se chevauchent pas » et « ne se touchent pas » — un boss qui repousse au lieu de blesser
  changerait le combat.

## Lot 3 — les vaisseaux entre eux ❌ À FAIRE, ET À TRANCHER

Le chasseur traverse les ennemis, et les ennemis se traversent entre eux.

**Question de conception, pas de technique** : aujourd'hui toucher un ennemi coûte des points de
vie. Le non-chevauchement voudrait dire **repousser**. Les deux sont incompatibles sur le même
contact ; il faut choisir, ennemi par ennemi :

- les **kamikazes** (sangsues, mines) doivent traverser puisqu'ils explosent ;
- les **coques lourdes** (porteur de bouclier, frégates) gagneraient à repousser ;
- les **ennemis entre eux** : un empilement de trois sangsues au même pixel est le défaut le plus
  visible, et le moins coûteux à corriger — une répulsion douce suffit, sans collision dure.

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

Il **manque** : corps contre corps (deux capsules qui se repoussent l'une l'autre), nécessaire au
lot 3. Le lot 2 n'en a pas besoin — un boss ne se laisse pas pousser.
