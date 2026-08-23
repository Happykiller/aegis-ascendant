# ADR-0020 — Le Pale Leviathan passe de quatre phases à deux

- **Date** : 2026-08-23
- **Statut** : accepté (décision du propriétaire, après playtest)
- **Amende / supersede** : `ADR-0018` (le boss final se démonte en quatre phases),
  `ADR-0019` (coupe des durées à ~67 s), spec §7 et §12.

## Contexte

Le combat comptait quatre phases, chacune portant un verbe et une mécanique inédite :
**BRISER** (quatre plaques d'armure sur une coquille tournante), **RÉSISTER** (trois nœuds
gravitiques qui aspirent le chasseur), **PRIORISER** (quatre épines détachées en escorte
armée), **OSER** (plongée dans la gueule pendant un compte à rebours). ADR-0019 en avait
déjà coupé les durées de ~3 min à ~67 s après un premier playtest.

Le playtest du 2026-08-23 a rendu un verdict plus dur : *« il est mal équilibré, je n'aime
pas le combat, on ne voit pas bien les phases — il faut revoir entièrement son équilibrage
et son gameplay »*. Le journal de la partie confirme le point le plus coûteux : elle s'est
arrêtée **pendant la phase 1**, sans qu'aucune ligne `leviathan phase N/4` ne soit émise.
Le joueur n'a jamais vu les trois autres phases — celles qui portaient l'essentiel du
travail de conception.

Trois causes, toutes vérifiées dans le code avant décision :

1. **La jauge mentait.** `structure_changed` divisait les dégâts par les PV des **quatre**
   phases cumulées (12 650). Briser toute l'armure valait 3 800, soit **30 %** de la barre :
   après vingt secondes d'effort le boss affichait encore 70 %. C'était déjà le retour du
   playtest de juillet — « les pastilles se vidaient, le boss encore à 80 % » — et il
   n'avait pas été traité, seulement contourné par des pastilles individuelles.
2. **La fenêtre de tir de la phase 1 n'existait pas.** Quatre plaques espacées de 90°, arc
   d'exposition de 100° : il y avait **toujours** une plaque exposée, souvent deux. La
   mécanique annoncée — lire la rotation, choisir son moment — ne contraignait jamais rien,
   et le code l'assumait en commentaire (« aucun temps mort »).
3. **Les dégâts s'étalaient.** Toutes les plaques exposées encaissaient. Comme la plaque
   la plus centrée change toutes les ~3 s, le feu du joueur se répartissait sur les quatre :
   elles descendaient ensemble et **tombaient toutes à la fin**. Les quinze premières
   secondes de la phase ne produisaient aucune destruction visible.

Aucun test ne voyait rien de tout cela : ils vérifiaient la mécanique (« la plaque hors arc
ne peut pas être touchée ») et jamais son effet (« quelque chose tombe-t-il avant la fin ? »).

## Décision

**Deux phases, deux gestes, ~40 s.**

```
PHASE 1 — BRISER L'ARMURE   4 plaques x 1270 PV   ~22 s   (55 % du combat)
PHASE 2 — LE CŒUR           4500 PV               ~18 s   (45 % du combat)
```

- **Une seule plaque est vulnérable à la fois** : celle qui est surlignée. Le feu se
  concentre, une plaque cède toutes les ~5,5 s, et le démontage se voit. Les PV par plaque
  MONTENT (950 → 1270) alors que la phase raccourcit : ce n'est pas une contradiction, c'est
  la fin de l'étalement.
- **La jauge montre la phase en cours**, et se remplit à nouveau à la bascule — l'idiome de
  shmup « il lui reste une deuxième barre ». Briser l'armure vide une barre entière.
- **Le cœur est exposé en permanence** en phase 2 : plus de gueule qui se referme, plus de
  compte à rebours. La cible est visible du premier au dernier tir.
- **Nœuds, épines et noyau intermédiaire disparaissent comme cibles.** Ils restent à l'écran
  et **se détachent quand une plaque cède** : le boss se démonte à vue, sans qu'aucune règle
  nouvelle n'ait à s'apprendre. `LeviathanSpike` et ses treize tests sont supprimés — garder
  des tests verts sur du code que plus rien n'appelle donne l'illusion d'une couverture.
- **L'aspiration survit comme pression, pas comme phase** : des vagues intermittentes en
  phase 2, toujours sous la vitesse du joueur. Une phase impose d'apprendre une règle ; une
  pression se sent sans qu'on l'explique.
- **La coquille s'écarte et le cœur bat** à l'entrée en phase 2. C'est le seul « texte » de
  la transition, avec la bannière **COEUR A NU**.

## Deux invariants neufs, qui gardent ce qui avait échappé

`LeviathanTuning.validate()` refusait déjà des réglages absurdes pris un par un. Il ne voyait
ni la dérive de durée, ni une phase devenue décorative. Il les voit désormais :

- **La durée totale** doit tomber dans `target_duration ± duration_tolerance` (40 ± 10 s).
  C'est le garde-fou qui manquait : le combat a dérivé vers trois minutes une fois, vers
  soixante-sept secondes ensuite, et **il a fallu un playtest à chaque fois** pour le voir.
- **Chaque phase porte entre 25 % et 75 %** du combat. La phase 4 valait 8 s sur 67 : une
  transition déguisée en phase.

Et l'invariant de fenêtre est remplacé : il vérifiait qu'une plaque reste **assez longtemps**
atteignable, jamais qu'il y en ait **une**. Avec une seule plaque vulnérable, l'arc doit
maintenant couvrir au moins l'écart entre deux plaques (100° ≥ 90°), sans quoi il existe des
instants où le joueur tire dans le vide sans qu'on lui dise pourquoi.

## Conséquences

- Le boss final n'est plus « plus gros » que le mini-boss en points de vie bruts (9 580 contre
  ~11 500) : il l'est par sa **durée** (~40 s contre ~30 s) et par le fait qu'il demande
  **deux gestes** au lieu d'un cycle répété. La spec §7 (« 3 à 4 min ») est caduque depuis
  ADR-0019 ; cet ADR l'écarte définitivement.
- Le travail de conception des phases 2 à 4 (`BOSS_PALE_LEVIATHAN.md` §4 à §6) devient de la
  **matière non employée**, pas du code mort : le document reste, avec un avertissement en
  tête. Si le combat devait un jour regagner une phase, elle y est décrite.
- Les assets restent tous utilisés : la coque, ses plaques, ses épines et ses nœuds sont à
  l'écran — les deux derniers comme pièces qui tombent.
- `--leviathan-phase=2` reste le hook pour regarder la phase 2 sans la jouer.

## Ce qui reste à juger, et par qui

L'alignement du halo sur la plaque réellement touchée, la lisibilité de l'écartement de la
coquille et le ressenti de durée ne se jugent **pas** à la capture : ils demandent une partie
jouée. C'est la leçon d'ADR-0019, et elle vaut pour cette refonte aussi.
