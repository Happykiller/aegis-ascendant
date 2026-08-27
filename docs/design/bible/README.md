---
titre: Bible de référence — le genre, et ce que nous en faisons
type: reference
statut: actif
maj: 2026-08-27
---

# Bible de référence du shoot'em up

Ce que le genre et le métier ont établi, et **où Aegis Ascendant se situe dessus**. Constituée le
2026-08-25 à partir de sources publiques (wikis, articles de conception, guides communautaires), à
la demande de l'opérateur ; **étendue le 2026-08-27** de six à treize pages, sur les mêmes sources
publiques, pour couvrir la conception générale (piliers, boucle, systèmes, expérience) en plus des
sujets propres au genre.

## ⚠️ Ce que cette bible est, et ce qu'elle n'est pas

- **Elle n'est pas la source de vérité du produit.** `docs/SPEC_AEGIS_ASCENDANT.md` et les
  `docs/decisions/ADR-*.md` le restent. Un principe de genre qui contredit un ADR **perd**.
- **Elle n'est pas un cahier des charges.** Rien ici n'est à implémenter du seul fait d'y figurer.
  Chaque page sépare nettement *ce que le genre dit* de *ce que nous faisons* et de *ce qui serait
  une piste* — et les pistes attendent une décision de l'opérateur.
- **Elle cite des jeux existants, et c'est délibéré.** On ne peut pas analyser un genre sans nommer
  ses œuvres. ⚠️ **Cela ne lève aucune interdiction** : la loi du projet reste entière, aucun nom,
  aucune silhouette, aucun élément identifiable d'une licence ne doit entrer dans le jeu
  (spec §0.2, assoupli par `ADR-0009` pour les seules planches de référence). Citer un mécanisme
  n'est pas le copier ; ce sont des idées de conception, pas des assets.

## Les pages

### Conception — ce qui vaut pour n'importe quel jeu

| Page | Ce qu'on y trouve |
|---|---|
| [Piliers et intention](07-piliers-et-intention.md) | Ce qu'est un pilier utilisable, le test du filtre — et l'**audit de nos cinq piliers**, dont un devenu orphelin |
| [Boucle de jeu](08-boucle-de-jeu.md) | Micro / méso / macro, la cadence de récompense, les quatre questions que le joueur doit pouvoir se poser |
| [Règles et systèmes](09-regles-et-systemes.md) | Boucles de rétroaction positives et négatives, MDA, **l'économie que le jeu n'a pas** |
| [Expérience joueur](10-experience-joueur.md) | Game feel et *juice*, canal de flow et dent de scie, apprendre sans tutoriel, accessibilité |

### Genre — ce qui est propre au shoot'em up

| Page | Ce qu'on y trouve |
|---|---|
| [Lisibilité](01-lisibilite.md) | Le contrat de lecture : couleurs réservées, chunking, télégraphie, densité. **La page la plus contraignante** — presque tout le reste en dépend |
| [Ennemis et vagues](02-ennemis-et-vagues.md) | Rôles stratégiques, priorité de cible, composition d'une vague, couloirs, chevauchement |
| [Niveau et rythme](03-niveau-et-rythme.md) | Structure d'un niveau **dans le temps** : introduction d'un mécanisme, respiration, mid-boss |
| [Level design](12-level-design.md) | Le niveau **dans l'espace** : rapport vaisseau/écran, repères et mémorisation, écriture des vagues, reprise après la mort |
| [Patterns de tir](11-patterns-de-tir.md) | La taxonomie du danmaku — anneaux, éventails, murs, piles, flux — et **la parité qui décide du sens d'un pattern** |
| [Boss](04-boss.md) | Phases, télégraphie, ce qui distingue un bon pattern d'un mauvais |
| [Puissance, mort, récupération](05-puissance-mort-recuperation.md) | Montée en puissance, ce qu'on perd en mourant, spirale de la mort |
| [Score et rang](06-score-et-rang.md) | Objectifs en conflit, chaînage, difficulté dynamique |
| [Lexique](13-lexique.md) | Le vocabulaire du genre, avec en troisième colonne **ce que nous en avons** — une carte de couverture |

## Comment elle est faite

Chaque page suit la même coupe, et **c'est la troisième colonne qui compte** :

1. **Ce que le genre dit** — sourcé, avec le lien.
2. **Chez nous** — l'état **réel** du code, vérifié au moment de l'écriture, pas supposé.
3. **L'écart, et ce qu'on en fait** — tenu, assumé, ou piste ouverte.

⚠️ **Les états « chez nous » vieillissent.** Ils sont datés (2026-08-25 pour les pages 01 à 06,
2026-08-27 pour les pages 07 à 13) et pointent des fichiers précis : avant de s'appuyer sur l'un
d'eux, vérifier qu'il est encore vrai. Un point de reprise faux coûte plus qu'un point de reprise
absent.

## Ce que l'extension du 2026-08-27 a trouvé

Quatre constats qui n'étaient documentés nulle part, et qui **appellent une décision de
l'opérateur** — chacun est développé, avec ses options, dans sa page :

1. **Le pilier D de la spec (§1.4) n'a plus d'implémentation** depuis `ADR-0010` : il décrit le
   passage au pilotage de la forteresse, supprimé le 2026-07-19. → [`07`](07-piliers-et-intention.md)
2. **`FAN` et `AIMED` ne sont employés par aucune unité de vague** : les deux schémas sont écrits et
   testés, mais tous les Needle Scout tirent une balle droite. Deux lignes de `.tres` les
   mettraient en jeu. → [`11`](11-patterns-de-tir.md)
3. **Le jeu n'a que des boucles de rétroaction positives**, et aucune ressource ne se dépense — donc
   aucune décision d'économie. Overdrive, arme secondaire et focus sont *prévus, absents et
   silencieux*. → [`09`](09-regles-et-systemes.md)
4. **`shake_multiplier` est codé mais injoignable** : la spec §7.3 exige une secousse désactivable,
   les référentiels d'accessibilité la classent en niveau de base, et il manque une ligne d'UI. →
   [`10`](10-experience-joueur.md)

## Sources

### Genre

- [Boghog's bullet hell shmup 101](https://shmups.wiki/library/Boghog%27s_bullet_hell_shmup_101) — Shmups Wiki. La source la plus dense : patterns, ennemis, vagues, scoring, mécaniques de base.
- [Help:Glossary](https://shmups.wiki/library/Help:Glossary) — Shmups Wiki, le vocabulaire du genre.
- [Sparen's Danmaku Design Studio](https://sparen.github.io/ph3tutorials/danmakudesign.html) — série de guides ; en particulier [A2, principes](https://sparen.github.io/ph3tutorials/ddsga2.html), [A3, taxonomie des patterns](https://sparen.github.io/ph3tutorials/ddsga3.html) et [A4, densité de balles](https://sparen.github.io/ph3tutorials/ddsga4.html).
- [Designing smart, meaningful SHMUPs](https://www.gamedeveloper.com/design/designing-smart-meaningful-shmups) — Game Developer, structure de niveau.
- [Balancing the sh#& out of our shmup](https://www.gamedeveloper.com/design/balancing-the-sh-out-of-our-shmup) — Game Developer, méthode d'équilibrage vécue.
- [Video Game Boss Design For Shmups](https://www.gamedeveloper.com/design/video-game-boss-design-for-shmups) — Game Developer.
- [(Breaking) The Shmup Dogma](https://www.gamedeveloper.com/design/-breaking-the-shmup-dogma) — Game Developer, la critique des conventions du genre (vies, crédits, smartbombs, difficulté).
- [The Anatomy of a Shmup](http://shmuptheory.blogspot.com/2010/02/anatomy-of-shmup.html) — SHMUPtheory, lisibilité et structure.
- [Battle Garegga / Advanced Rank](https://shmups.wiki/library/Battle_Garegga/Advanced_Rank) — Shmups Wiki, le rang décortiqué.
- [Shoot 'em up](https://en.wikipedia.org/wiki/Shoot_%27em_up) — Wikipedia, vue d'ensemble et vocabulaire.
- [Pixelblog 31](https://www.slynyrd.com/blog/2020/12/14/pixelblog-31-shmup-sprite-design) et [32](https://www.slynyrd.com/blog/2021/2/15/pixelblog-32-shmup-design-part-2) — SLYNYRD, conception visuelle et armes.
- [Shmups 101](https://racketboy.com/retro/shmups-101-a-beginners-guide-to-2d-shooters) — Racketboy, guide d'entrée.
- [shmups.system11.org](https://shmups.system11.org/) — le forum de référence du genre. ⚠️ **403 aux robots** : le guide de boss de Giest118 (`t=44816`) et le fil sur le *stage design* (`t=58682`) n'ont pas pu être consultés directement. À lire à la main si l'un de ces sujets est repris.

### Conception générale

- [Design Pillars – The Core of Your Game](https://www.gamedeveloper.com/design/design-pillars-the-core-of-your-game) — Game Developer, les piliers comme filtre.
- [How pillars and triangles can focus your game design](https://www.raspberrypi.com/news/how-pillars-and-triangles-can-focus-your-game-design/) — Raspberry Pi Foundation, la formulation d'un pilier.
- [The Importance of a Well Defined Core Gameplay Loop](https://www.gamedeveloper.com/design/the-importance-of-a-well-defined-core-gameplay-loop) — Game Developer.
- [Designing The Core Gameplay Loop](https://gamedesignskills.com/game-design/core-loops-in-gameplay/) — Game Design Skills, micro/méso/macro. ⚠️ **403 aux robots**.
- [Game systems: Feedback loops](https://machinations.io/articles/game-systems-feedback-loops-and-how-they-help-craft-player-experiences) — Machinations.
- [Mechanics, Dynamics, and Aesthetics](https://pressbooks.usnh.edu/creatinggames/chapter/mechanics-dynamics-and-aesthetics/) — le cadre MDA.
- [Game Design Theory Applied: The Flow Channel](https://www.gamedeveloper.com/design/game-design-theory-applied-the-flow-channel) — Game Developer, le canal de flow et la dent de scie.
- [How to Make Your Game Feel Good](https://egmatic.com/blog/how-to-make-your-game-feel-good) — game feel et *juice*, avec repères chiffrés.
- [The Art of Screenshake](https://www.youtube.com/watch?v=AJdEqssNZ-U) — Jan Willem Nijman (Vlambeer), INDIGO Classes 2013. ⚠️ Conférence vidéo, non transcrite.
- [Game Accessibility Guidelines — Basic](https://gameaccessibilityguidelines.com/basic/) — le niveau de base de l'accessibilité.
- [Why Super Mario Bros is still a fantastic lesson in game design](https://www.creativebloq.com/3d/video-game-design/why-super-mario-bros-is-still-a-fantastic-lesson-in-game-design) — Creative Bloq, l'onboarding sans tutoriel.
