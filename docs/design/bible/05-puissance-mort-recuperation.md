---
titre: Puissance, mort, récupération — la spirale et ses garde-fous
type: reference
statut: actif
maj: 2026-08-27
---

# Puissance, mort, récupération

La montée en puissance est la moitié du plaisir du genre. Elle porte aussi son défaut structurel :
mourir enlève la puissance, donc rend la suite plus dure, donc fait remourir.

| Loi | Force | Énoncé |
|---|---|---|
| `LOI-PUI-01` | INTENTION | L'arme doit monter, et la montée doit se voir |
| `LOI-PUI-02` | RÉFÉRENCE | Trois familles d'armement : éventail, laser, options |
| `LOI-PUI-03` | **LOI** | La mort ne doit pas enterrer le joueur |
| `LOI-PUI-04` | CONTRAINTE | La perte de puissance à la mort est partielle, jamais totale |
| `LOI-PUI-05` | **LOI** | La mort nettoie l'écran et ouvre une invulnérabilité généreuse |
| `LOI-PUI-06` | RÉFÉRENCE | Le *bomb buffer* annule la mort après coup |

---

### `LOI-PUI-01` · L'arme doit monter, et la montée doit se voir — [INTENTION]

Le tir le plus courant est une **ligne de projectiles** qui devient un **éventail** en montant en
puissance — « un pisto-pois peu impressionnant au départ, nettement plus satisfaisant une fois
étalé ». **Cinq niveaux** est une échelle répandue.

Ce qui compte n'est pas le gain de dégâts : c'est que le joueur **voie** que son arme a changé.

### `LOI-PUI-02` · Trois familles d'armement — [RÉFÉRENCE]

| Famille | Ce qu'elle demande au joueur |
|---|---|
| **Éventail** | couverture large, visée relâchée |
| **Laser** | faisceau linéaire qui s'élargit : petite surface, **visée exigeante**, compensée par la puissance brute |
| **Options / satellites** | des modules qui suivent le vaisseau et dont la **position** change ce qu'ils apportent |

### `LOI-PUI-03` · La mort ne doit pas enterrer le joueur — **[LOI]**

C'est la loi cardinale du domaine, et elle a un nom : la **spirale de la mort**. Tout système de
perte à la mort doit être jugé sur une seule question — *le joueur qui vient de mourir a-t-il de
quoi survivre à ce qui l'a tué ?*

### `LOI-PUI-04` · La perte de puissance est partielle, jamais totale — [CONTRAINTE]

On redescend d'un ou deux niveaux, pas à zéro. Un jeu peut choisir de ne **rien** retirer : c'est
une position défendable, plus permissive que le genre, et qui doit alors être assumée comme telle.

### `LOI-PUI-05` · La mort nettoie l'écran et ouvre une invulnérabilité généreuse — **[LOI]**

Deux gestes indissociables : les projectiles ennemis vivants sont **annulés**, puis le joueur
renaît avec quelques secondes d'invulnérabilité.

C'est ce qui « prévient les **morts en chaîne** ». Sans le nettoyage, le joueur renaît dans le
rideau qui vient de le tuer, et son invulnérabilité expire au milieu.

⚠️ Les projectiles **du joueur** survivent : ils n'ont jamais tué personne.

### `LOI-PUI-06` · Le *bomb buffer* — [RÉFÉRENCE]

Bombarder dans les quelques images **après** le coup fatal annule quand même la mort. Pure
anti-frustration, et sans effet sur le reste du système.

## Sources

- [Boghog's bullet hell shmup 101](https://shmups.wiki/library/Boghog%27s_bullet_hell_shmup_101) — Shmups Wiki : montée en puissance, familles d'armes, nettoyage à la mort, invulnérabilité, *bomb buffer*.
- [Pixelblog 32 — Shmup Design Part 2](https://www.slynyrd.com/blog/2021/2/15/pixelblog-32-shmup-design-part-2) — SLYNYRD : la progression d'arme et sa lisibilité.
