---
titre: Bible du shoot vertical — corpus de lois
type: reference
statut: actif
maj: 2026-08-27
---

# Bible du shoot vertical

**88 lois** pour faire un bon shoot vertical. Elles ne parlent d'aucun jeu en particulier :
n'importe quel projet du genre peut les suivre telles quelles.

> **Ce document est une table de lois, de règles et de conventions.** Ce n'est pas un plan
> d'implémentation, pas un cahier des charges, et pas la description d'un jeu existant.

## Comment lire une loi

Chaque loi porte un identifiant stable et une **force normative**. On cite une loi par son
identifiant, jamais par sa page : `LOI-PAT-03` restera `LOI-PAT-03`.

```
LOI-PAT-03 · La parité d'un éventail décide de son sens — [LOI]
└─┬─┘ └┬┘ └┬┘
  │    │   └── numéro dans le domaine, stable à vie
  │    └────── domaine (trois lettres)
  └─────────── préfixe unique du corpus
```

### Les quatre forces

| Force | Ce qu'elle exige | Combien |
|---|---|---:|
| **[LOI]** | **Respect exact.** L'enfreindre casse le genre ; on ne s'en écarte que par une décision explicite et écrite | 48 |
| **[CONTRAINTE]** | Une **fourchette** ou un choix borné. Liberté à l'intérieur des limites indiquées | 15 |
| **[INTENTION]** | Un **résultat** imposé, les moyens sont libres | 17 |
| **[RÉFÉRENCE]** | Un usage constaté, une inspiration. **Jamais une obligation** | 8 |

⚠️ **Une [RÉFÉRENCE] n'est pas une loi faible** : c'est une autre nature. Un projet qui ne l'applique
pas n'a rien à justifier. Un projet qui enfreint une **[LOI]** doit dire pourquoi.

### Les domaines

| Code | Domaine | Page |
|---|---|---|
| `LIS` | Lisibilité | [01](01-lisibilite.md) |
| `ENN` | Ennemis et vagues | [02](02-ennemis-et-vagues.md) |
| `RYT` | Niveau et rythme — le **temps** | [03](03-niveau-et-rythme.md) |
| `BOS` | Boss | [04](04-boss.md) |
| `PUI` | Puissance, mort, récupération | [05](05-puissance-mort-recuperation.md) |
| `SCO` | Score et rang | [06](06-score-et-rang.md) |
| `PIL` | Piliers et intention | [07](07-piliers-et-intention.md) |
| `BCL` | Boucle de jeu | [08](08-boucle-de-jeu.md) |
| `SYS` | Règles et systèmes | [09](09-regles-et-systemes.md) |
| `EXP` | Expérience joueur | [10](10-experience-joueur.md) |
| `PAT` | Patterns de tir | [11](11-patterns-de-tir.md) |
| `LVL` | Level design — l'**espace** | [12](12-level-design.md) |
| — | [Lexique](13-lexique.md) : le vocabulaire, sans loi | [13](13-lexique.md) |

## Les quatre lois qu'on relit avant les autres

Si l'on ne devait en retenir que quatre, ce seraient celles dont tout le reste dépend :

- [`LOI-LIS-05`](01-lisibilite.md) — **la densité n'est pas la difficulté.** Presque tout ce qu'on
  croit être un problème d'équilibrage est un problème de lecture.
- [`LOI-PIL-03`](07-piliers-et-intention.md) — **un pilier nomme un ressenti, pas une
  fonctionnalité.** Sinon il meurt avec la fonctionnalité, sans que personne ne s'en aperçoive.
- [`LOI-EXP-08`](10-experience-joueur.md) — **un effet invisible se lit comme un défaut ; un signal
  mal lu est pire qu'un signal absent.**
- [`LOI-EXP-12`](10-experience-joueur.md) — **un système qui fonctionne n'est pas validé.** Une
  porte de qualité verte n'a jamais démontré qu'un jeu était lisible.

## Comment s'en servir

**Pour concevoir.** Une idée se confronte aux lois de son domaine avant d'être écrite. Le filtre de
[`LOI-PIL-04`](07-piliers-et-intention.md) s'applique aussi aux lois : *bien / neutre / mauvais*.

**Pour relire.** Un rendu, un pattern, une vague se relisent loi par loi. Le manquement se cite par
identifiant : « `LOI-LVL-06` — les deux nuages ont la même balle. »

**Pour auditer un jeu.** Chaque loi devient une ligne d'un rapport de conformité — *tenue*,
*écartée* (avec sa raison), *non vérifiée*. Voir ci-dessous.

**Pour un autre jeu.** Copier le dossier. Il ne contient rien de spécifique à un projet : ni valeur,
ni nom, ni fichier. Seul le rapport de conformité l'est.

## ⚠️ Ce que ce corpus n'est pas

- **Il ne décrit aucun jeu.** L'état d'un projet donné vit dans son **rapport de conformité** —
  pour celui-ci : [`../CONFORMITE-AEGIS.md`](../CONFORMITE-AEGIS.md).
- **Il ne prime sur aucune spécification produit.** Une loi de genre qui contredit une décision de
  projet **perd** : le projet a le droit d'être différent, il a le devoir de le savoir.
- **Il cite des jeux existants, et c'est délibéré.** On ne peut pas analyser un genre sans nommer
  ses œuvres. Citer un mécanisme n'est pas le copier : ce sont des idées de conception, pas des
  assets, et cela ne lève aucune contrainte d'originalité ou de propriété intellectuelle.

## Sources

### Genre

- [Boghog's bullet hell shmup 101](https://shmups.wiki/library/Boghog%27s_bullet_hell_shmup_101) — Shmups Wiki. La source la plus dense : patterns, ennemis, vagues, scoring, mécaniques de base.
- [Help:Glossary](https://shmups.wiki/library/Help:Glossary) — Shmups Wiki, le vocabulaire du genre.
- [Sparen's Danmaku Design Studio](https://sparen.github.io/ph3tutorials/danmakudesign.html) — [A2](https://sparen.github.io/ph3tutorials/ddsga2.html), [A3](https://sparen.github.io/ph3tutorials/ddsga3.html), [A4](https://sparen.github.io/ph3tutorials/ddsga4.html) : principes, taxonomie des patterns, densité.
- [Designing smart, meaningful SHMUPs](https://www.gamedeveloper.com/design/designing-smart-meaningful-shmups) — Game Developer, structure de niveau.
- [Balancing the sh#& out of our shmup](https://www.gamedeveloper.com/design/balancing-the-sh-out-of-our-shmup) — Game Developer, équilibrage vécu.
- [Video Game Boss Design For Shmups](https://www.gamedeveloper.com/design/video-game-boss-design-for-shmups) — Game Developer.
- [(Breaking) The Shmup Dogma](https://www.gamedeveloper.com/design/-breaking-the-shmup-dogma) — Game Developer, la critique des conventions du genre.
- [The Anatomy of a Shmup](http://shmuptheory.blogspot.com/2010/02/anatomy-of-shmup.html) — SHMUPtheory.
- [Battle Garegga / Advanced Rank](https://shmups.wiki/library/Battle_Garegga/Advanced_Rank) — Shmups Wiki, le rang décortiqué.
- [Shoot 'em up](https://en.wikipedia.org/wiki/Shoot_%27em_up) — Wikipedia, vue d'ensemble.
- [Pixelblog 31](https://www.slynyrd.com/blog/2020/12/14/pixelblog-31-shmup-sprite-design) et [32](https://www.slynyrd.com/blog/2021/2/15/pixelblog-32-shmup-design-part-2) — SLYNYRD.
- [Shmups 101](https://racketboy.com/retro/shmups-101-a-beginners-guide-to-2d-shooters) — Racketboy.
- [shmups.system11.org](https://shmups.system11.org/) — le forum de référence. ⚠️ **403 aux robots** : le guide de boss de Giest118 (`t=44816`) et le fil sur le *stage design* (`t=58682`) n'ont pas pu être lus directement.

### Conception générale

- [Design Pillars – The Core of Your Game](https://www.gamedeveloper.com/design/design-pillars-the-core-of-your-game) — Game Developer.
- [How pillars and triangles can focus your game design](https://www.raspberrypi.com/news/how-pillars-and-triangles-can-focus-your-game-design/) — Raspberry Pi Foundation.
- [The Importance of a Well Defined Core Gameplay Loop](https://www.gamedeveloper.com/design/the-importance-of-a-well-defined-core-gameplay-loop) — Game Developer.
- [Designing The Core Gameplay Loop](https://gamedesignskills.com/game-design/core-loops-in-gameplay/) — Game Design Skills. ⚠️ **403 aux robots**.
- [Game systems: Feedback loops](https://machinations.io/articles/game-systems-feedback-loops-and-how-they-help-craft-player-experiences) — Machinations.
- [Mechanics, Dynamics, and Aesthetics](https://pressbooks.usnh.edu/creatinggames/chapter/mechanics-dynamics-and-aesthetics/) — le cadre MDA.
- [Game Design Theory Applied: The Flow Channel](https://www.gamedeveloper.com/design/game-design-theory-applied-the-flow-channel) — Game Developer.
- [How to Make Your Game Feel Good](https://egmatic.com/blog/how-to-make-your-game-feel-good) — game feel et *juice*.
- [The Art of Screenshake](https://www.youtube.com/watch?v=AJdEqssNZ-U) — Jan Willem Nijman (Vlambeer), INDIGO Classes 2013.
- [Game Accessibility Guidelines — Basic](https://gameaccessibilityguidelines.com/basic/).
- [Why Super Mario Bros is still a fantastic lesson in game design](https://www.creativebloq.com/3d/video-game-design/why-super-mario-bros-is-still-a-fantastic-lesson-in-game-design) — Creative Bloq.

### Apports de l'audit du 2026-08-27

Trois lois viennent d'un rapport d'audit externe plutôt que d'une source publique du genre —
[`LOI-EXP-09`](10-experience-joueur.md) (le contrat SEE/UNDERSTAND/FEEL/ANTICIPATE/DECIDE),
[`LOI-EXP-12`](10-experience-joueur.md) (vérification ≠ validation) et le vocabulaire des quatre
forces normatives ci-dessus. Rapport archivé :
[`../AUDIT-2026-08-27-bible-supreme.md`](../AUDIT-2026-08-27-bible-supreme.md).

[`LOI-EXP-08`](10-experience-joueur.md) est une **loi de terrain** : elle est née de cinq mécaniques
prises en défaut le même jour sur un projet réel, pas d'une lecture.
