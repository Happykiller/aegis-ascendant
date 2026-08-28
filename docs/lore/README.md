---
titre: Index du lore — par quelle page commencer
type: lore
statut: actif
maj: 2026-08-28
---

# Le lore d'Aegis Ascendant

Six pages. Une seule est à lire en entier ; les autres se consultent.

> ⚠️ **Ce lore SAIT tout ; le jeu n'en montre presque rien.** L'histoire s'étage sur une
> campagne de douze niveaux (`CAMPAGNE.md`) et le jeu contient **le niveau 1**. Avant
> d'employer un fait, vérifier son palier `[niv. N]` : écrit trop tôt, il ne reste rien pour
> la suite.

## Les six pages

| Page | Ce qu'elle contient | Quand l'ouvrir |
|---|---|---|
| [`BIBLE.md`](BIBLE.md) | Le grand récit : d'où vient cette humanité, le système Helios, la chronologie, ce qu'est la guerre en 386, ce que le niveau 1 représente. | **Une fois, en entier**, avant de toucher au reste. |
| [`FACTIONS.md`](FACTIONS.md) | Les quatre entités humaines — Helios Vanguard, le Registre d'Helios, l'Arsenal Orbital Talvern, les Sans-Trame — ce qu'elles veulent, ce qu'elles cachent, comment elles s'accrochent. Plus le Specter-9, l'*Aurora Spear* et l'Aegis Citadel replacés. | Quand un texte doit avoir un **point de vue** : qui parle, au nom de quoi. |
| [`NULL_CHOIR.md`](NULL_CHOIR.md) | L'ennemi : **le nom** (sept candidats, un recommandé), l'origine, la langue, les Voix, et l'histoire des neuf unités. | Avant toute description de l'ennemi. Sa section « ce que l'Unisson n'est pas » est le garde-fou le plus utile du dépôt. |
| [`PERSONNAGES.md`](PERSONNAGES.md) | Huit personnes : ce qu'elles veulent, ce qu'elles cachent, une phrase que chacune seule pourrait dire, et leur arc du niveau 1 au niveau 12. | Quand quelqu'un doit parler, ou qu'on parle de quelqu'un. |
| [`CAMPAGNE.md`](CAMPAGNE.md) | La charpente des douze niveaux, et surtout la liste de **ce que le joueur ignore encore à la fin du niveau 1**. Charpente narrative, **pas un document de design**. | Pour vérifier un palier de révélation. À chaque fois. |
| [`EXPLOITATION.md`](EXPLOITATION.md) | **La page d'usage** : écran par écran, ce que le lore y met et ce qu'on n'a pas le droit d'y dire. Plus l'inventaire des répliques enregistrées, le coût du renommage, et les décisions à rouvrir. | **En premier**, dès qu'on écrit un texte destiné au jeu. |

## Par quelle page commencer, selon ce qu'on fait

- **J'écris une réplique, un briefing, un texte d'écran** → [`EXPLOITATION.md`](EXPLOITATION.md),
  toujours. Elle renvoie aux autres au bon endroit.
- **Je découvre le projet** → [`BIBLE.md`](BIBLE.md), puis [`CAMPAGNE.md`](CAMPAGNE.md) §2.
- **Je conçois un ennemi, une coque, un décor** → [`NULL_CHOIR.md`](NULL_CHOIR.md) §6 : chaque
  unité y a un **métier d'origine** dont sa forme découle.
- **Je juge si une idée narrative est jouable** → [`CAMPAGNE.md`](CAMPAGNE.md) §6 : elle dit
  explicitement ce que cette charpente ne promet pas.

## Les deux règles qui ne se discutent pas

1. **Lyra dit « Pilote »**, jamais « Adaire », jamais « Halyard ».
2. **L'ennemi ne parle pas.** On peut afficher un relevé de signal ; on peut faire citer une
   traduction par un humain, à ses risques. Jamais une réplique attribuée à l'ennemi.

## État

Écrit sous [`BRIEF-0088`](../forge/briefs/BRIEF-0088-grande-bible-univers.md), qui remplace
`BRIEF-0087` et l'ancienne bible minimale. Deux points restent **ouverts et le disent** :

- le **nom de la faction** — « Null Choir » a été rejeté ; sept candidats sont proposés et le
  lore est écrit avec le recommandé, **The Unison**, pour être jugeable sur pièces
  (`NULL_CHOIR.md` §1) ;
- la **fin de la campagne** — trois issues compatibles, aucune tranchée (`CAMPAGNE.md` §5).

Ce dossier ne contient **aucune décision** : les écarts avec les ADR et la charte sont listés
dans [`EXPLOITATION.md`](EXPLOITATION.md) §8, à trancher par le concepteur.
