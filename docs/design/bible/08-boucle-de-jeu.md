---
titre: Boucle de jeu — les trois échelles, et la cadence de récompense
type: reference
statut: actif
maj: 2026-08-27
---

# Boucle de jeu

Le genre décrit volontiers *ce que le joueur affronte*. Ce domaine décrit *ce qu'il fait, en boucle*
— l'unité de temps la plus courte du jeu, et les échelles qui l'emboîtent.

| Loi | Force | Énoncé |
|---|---|---|
| `LOI-BCL-01` | CONTRAINTE | Trois échelles : micro 1–5 s, méso 2–10 min, macro session à session |
| `LOI-BCL-02` | CONTRAINTE | La première récompense tombe avant la 60ᵉ seconde |
| `LOI-BCL-03` | **LOI** | Le jeu se comprend en minutes, jamais en heures |
| `LOI-BCL-04` | **LOI** | Le joueur peut répondre à quatre questions à tout instant |
| `LOI-BCL-05` | **LOI** | La micro-boucle doit nourrir une boucle plus longue |

---

### `LOI-BCL-01` · Trois échelles emboîtées — [CONTRAINTE]

| Boucle | Durée | Contenu type |
|---|---|---|
| **micro** — instant à instant | **1 à 5 s** | lire → décider → agir |
| **méso** — minute à minute | **2 à 10 min** | entrer dans une zone → la résoudre → en sortir plus fort |
| **macro** — session à session | heures, jours | finir → débloquer → recommencer autrement |

Un jeu d'action très rapide peut descendre **sous** la seconde sur la micro-boucle : le repère
signale un ordre de grandeur, pas un plancher.

### `LOI-BCL-02` · La première récompense tombe avant la 60ᵉ seconde — [CONTRAINTE]

La micro-boucle se résout en 1 à 5 s, et **la première récompense doit arriver dans les 30 à 60
premières secondes**. Ce qui se joue là n'est pas la générosité : c'est la démonstration que la
boucle **rend** quelque chose.

### `LOI-BCL-03` · Le jeu se comprend en minutes, jamais en heures — **[LOI]**

> Une boucle de jeu « ne devrait **jamais se mesurer en heures** — on doit savoir à quoi ressemble
> votre jeu en quelques **minutes** de jeu. »

Une boucle mal définie « masque l'objectif immédiat sous un excès de macro » et compte sur le joueur
pour « trouver le fun » après un investissement qu'il n'a aucune raison de consentir.

### `LOI-BCL-04` · Les quatre questions — **[LOI]**

À tout instant, le joueur doit pouvoir dire :

1. **quel est l'objectif immédiat** ;
2. **quelles tâches** l'y mènent ;
3. **combien de temps** ça va prendre ;
4. **ce qui reste acquis** ensuite.

⚠️ La troisième est la plus négligée, et la plus structurante : le joueur doit savoir s'il peut
finir **dans une seule session**. Dans un jeu à parcours linéaire, elle se répond par un repère de
progression — un numéro de section, une barre, un changement de décor.

### `LOI-BCL-05` · La micro-boucle doit nourrir une boucle plus longue — **[LOI]**

Une micro-boucle satisfaisante qui n'alimente rien produit un jeu qu'on repose au bout de dix
minutes ; une macro-boucle riche assise sur une micro-boucle terne produit un jeu qu'on ne commence
jamais.

## Sources

- [The Importance of a Well Defined Core Gameplay Loop](https://www.gamedeveloper.com/design/the-importance-of-a-well-defined-core-gameplay-loop) — Game Developer : la boucle qui se mesure en minutes, les quatre critères de progression lisible.
- [Designing The Core Gameplay Loop](https://gamedesignskills.com/game-design/core-loops-in-gameplay/) — Game Design Skills : micro/méso/macro et les repères chiffrés. ⚠️ Le site rend un **403 aux robots** : consulté via résumé de recherche.
- [Game Design using Micro Macro Meta Grouping](https://levimoore.dev/game-design-using-micro-macro-meta-grouping/) — le découpage micro/macro/méta.
