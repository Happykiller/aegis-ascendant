---
titre: DAF — Dossier d'Architecture Fonctionnelle
type: index
statut: actif
maj: 2026-08-29
---

# DAF — architecture fonctionnelle

Ce que le jeu fait, pour qui, et sous quels invariants.

| Page | Ce qu'elle couvre | Statut | MAJ |
|---|---|---|---|
| [signaux.md](signaux.md) | Un effet qui change l'état du jeu **sans le montrer** se lit comme un défaut ; et un signal **mal lu** est pire qu'un signal absent — il enseigne une règle fausse. Cinq mécaniques prises en défaut le même jour | actif | 2026-08-26 |
| [arc-de-jeu.md](arc-de-jeu.md) | La campagne et ses deux niveaux, les six phases du premier, la traversée du second — et ⚠️ le vocabulaire « niveau / phase / tronçon », qui a changé le 29/08 | actif | 2026-08-29 |

## Les domaines fonctionnels, et où ils sont décrits

Aucun de ces domaines n'est recopié ici : chacun a déjà un document qui fait autorité. Cette table
est l'aiguillage — elle dit **où lire**, et **ce qui s'est décidé depuis**.

| Domaine | Où c'est décrit | Décisions qui l'amendent |
|---|---|---|
| Pitch, univers, factions | `ARCHITECTURE_FONCTIONNELLE.md` §1, §6 | ADR-0009 (référence d'inspiration réinstaurée) |
| Arc de la partie | [arc-de-jeu.md](arc-de-jeu.md) | **ADR-0010**, puis **ADR-0038** (le jeu est une campagne ; un survol n'est pas un niveau de plus) |
| Contrôles | `ARCHITECTURE_FONCTIONNELLE.md` §3 | — |
| Montée en puissance (Pulse Array 1→5) | `ARCHITECTURE_FONCTIONNELLE.md` §4.1 | — |
| Bouclier & survie | `ARCHITECTURE_FONCTIONNELLE.md` §4.2 | — |
| Bonus (pickups) | `ARCHITECTURE_FONCTIONNELLE.md` §4.3 | — |
| Ennemis & familles | `ARCHITECTURE_FONCTIONNELLE.md` §4.4 | ADR-0015 (bestiaire) |
| Mini-boss (Choir Harvester) | `ARCHITECTURE_TECHNIQUE.md` §9 | — |
| **Boss final (Pale Leviathan)** | **`ADR-0021`** fait foi sur le combat, **`ADR-0023`** sur ce que le HUD en montre ; `docs/design/BOSS_PALE_LEVIATHAN.md` décrit encore quatre phases et porte un avertissement en tête | ADR-0018, puis ADR-0020, puis **ADR-0021** (trois cycles armure/noyau, ~40 s), puis **ADR-0023** (la jauge montre le combat, plus la phase) |
| Appontage & clôture | `ARCHITECTURE_FONCTIONNELLE.md` §4.5 | **ADR-0010** — l'appontage devient la séquence de fin |
| Finale & victoire, score | `ARCHITECTURE_FONCTIONNELLE.md` §4.7, §4.8 | ADR-0012 (langage d'interface des écrans) |
| Direction artistique | `ARCHITECTURE_FONCTIONNELLE.md` §5 | ADR-0006, ADR-0011, ADR-0013, ADR-0014, ADR-0016, ADR-0017 |
| Difficulté & accessibilité | `ARCHITECTURE_FONCTIONNELLE.md` §7 | — ; reste largement à faire (`docs/BACKLOG.md`, P2) |

> **À COMPLÉTER — pour l'opérateur.** Faut-il éclater ces domaines en pages KB à part entière ?
> Tant qu'ils tiennent en une section d'un document déjà écrit et à jour, les dupliquer ici ne
> créerait que deux sources vouées à diverger. La page `arc-de-jeu.md` existe parce que, là,
> l'écart est **avéré**.
