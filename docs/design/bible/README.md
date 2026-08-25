---
titre: Bible de référence — le genre, et ce que nous en faisons
type: reference
statut: actif
maj: 2026-08-25
---

# Bible de référence du shoot'em up

Ce que le genre a établi, et **où Aegis Ascendant se situe dessus**. Constituée le 2026-08-25 à
partir de sources publiques (wikis, articles de conception, guides communautaires), à la demande
de l'opérateur.

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

| Page | Ce qu'on y trouve |
|---|---|
| [Lisibilité](01-lisibilite.md) | Le contrat de lecture : couleurs réservées, chunking, télégraphie, densité. **La page la plus contraignante** — presque tout le reste en dépend |
| [Ennemis et vagues](02-ennemis-et-vagues.md) | Rôles stratégiques, priorité de cible, composition d'une vague, couloirs, chevauchement |
| [Niveau et rythme](03-niveau-et-rythme.md) | Structure d'un niveau, introduction d'un mécanisme, respiration, mid-boss |
| [Boss](04-boss.md) | Phases, télégraphie, ce qui distingue un bon pattern d'un mauvais |
| [Puissance, mort, récupération](05-puissance-mort-recuperation.md) | Montée en puissance, ce qu'on perd en mourant, spirale de la mort |
| [Score et rang](06-score-et-rang.md) | Objectifs en conflit, chaînage, difficulté dynamique |

## Comment elle est faite

Chaque page suit la même coupe, et **c'est la troisième colonne qui compte** :

1. **Ce que le genre dit** — sourcé, avec le lien.
2. **Chez nous** — l'état **réel** du code, vérifié au moment de l'écriture, pas supposé.
3. **L'écart, et ce qu'on en fait** — tenu, assumé, ou piste ouverte.

⚠️ **Les états « chez nous » vieillissent.** Ils sont datés du 2026-08-25 et pointent des fichiers
précis : avant de s'appuyer sur l'un d'eux, vérifier qu'il est encore vrai. Un point de reprise faux
coûte plus qu'un point de reprise absent.

## Sources

- [Boghog's bullet hell shmup 101](https://shmups.wiki/library/Boghog%27s_bullet_hell_shmup_101) — Shmups Wiki. La source la plus dense : patterns, ennemis, vagues, scoring, mécaniques de base.
- [Sparen's Danmaku Design Studio](https://sparen.github.io/ph3tutorials/danmakudesign.html) — série de guides ; en particulier [A4, densité de balles](https://sparen.github.io/ph3tutorials/ddsga4.html).
- [Designing smart, meaningful SHMUPs](https://www.gamedeveloper.com/design/designing-smart-meaningful-shmups) — Game Developer, structure de niveau.
- [Balancing the sh#& out of our shmup](https://www.gamedeveloper.com/design/balancing-the-sh-out-of-our-shmup) — Game Developer, méthode d'équilibrage vécue.
- [Video Game Boss Design For Shmups](https://www.gamedeveloper.com/design/video-game-boss-design-for-shmups) — Game Developer.
- [Battle Garegga / Advanced Rank](https://shmups.wiki/library/Battle_Garegga/Advanced_Rank) — Shmups Wiki, le rang décortiqué.
- [Shoot 'em up](https://en.wikipedia.org/wiki/Shoot_%27em_up) — Wikipedia, vue d'ensemble et vocabulaire.
- [Pixelblog 31](https://www.slynyrd.com/blog/2020/12/14/pixelblog-31-shmup-sprite-design) et [32](https://www.slynyrd.com/blog/2021/2/15/pixelblog-32-shmup-design-part-2) — SLYNYRD, conception visuelle et armes.
- [shmups.system11.org](https://shmups.system11.org/) — le forum de référence du genre. ⚠️ Le guide de boss de Giest118 (`t=44816`) **n'a pas pu être consulté** : le forum rend un 403 aux robots. À lire à la main si le sujet est repris.
