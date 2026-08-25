---
titre: Base de connaissance — Aegis Ascendant
type: index
statut: actif
maj: 2026-08-25
---

# Base de connaissance — Aegis Ascendant

La mémoire longue du projet : ce qu'il faut **savoir** avant d'agir. Elle porte le *pourquoi*, les
invariants et les décisions — jamais le *comment*, que le code dit mieux et sans divergence.

⚠️ **Cette KB n'est pas la source de vérité du produit, elle aiguille vers elle.** Ici, la vérité
vit dans `docs/SPEC_AEGIS_ASCENDANT.md` (cahier des charges) et `docs/decisions/ADR-*.md` (qui
**priment sur la spec** en cas d'écart). Une page de KB qui recopierait l'une des deux serait fausse
au premier commit ; elle les référence.

| Entrée | Ce qu'on y trouve |
|---|---|
| [`DAT/`](DAT/README.md) | Architecture **technique** : stack et versions, arborescence, environnements de travail |
| [`DAF/`](DAF/README.md) | Architecture **fonctionnelle** : l'arc de jeu et ses domaines, avec l'état réel du code |
| [`REGLES/`](REGLES/README.md) | Process, workflows, consignes, normes, **lois** — les deux dernières sont contraignantes |
| [`MOTEUR.md`](MOTEUR.md) | Cartographie de `.claude/` : quel skill, quel sous-agent, quel hook, et **quand s'en servir** |
| [`HISTORY.md`](HISTORY.md) | Index chronologique des sujets abordés, pour ne pas refaire deux fois le même chemin |
| [`../design/bible/`](../design/bible/README.md) | **Bible de référence du genre** : ce que le shoot'em up a établi, et où nous nous situons dessus. Hors KB — c'est du savoir externe, pas de la mémoire de projet — mais on y aiguille depuis ici |

## KB ou `.claude/resources/` ? La frontière

Le projet a **deux** réceptacles, et les confondre fabrique deux sources qui divergeront :

- **`docs/KB/`** (ici) — ce qu'il faut savoir **du jeu** : sa technique, son fonctionnel, ses règles.
  Versionné avec le produit, lisible par un humain qui n'a jamais ouvert Claude.
- **[`.claude/resources/`](../../.claude/resources/INDEX.md)** — ce qu'il faut savoir pour
  **travailler avec Claude ici** : pièges d'outillage, boucles de vérification, méthodes de mesure.
  Chargé à la demande, indexé par son propre `INDEX.md`.

La question qui tranche : *est-ce que ça parle du jeu, ou de la façon de travailler sur le jeu ?*
