---
titre: Pale Leviathan — après la première partie jouée en cycles
date: 2026-08-25
auteur: session Claude « boss » (aegis-ascendant, poste happykiller)
perimetre: scripts/bosses/, scripts/gameplay/graybox_root.gd, scripts/ui/fighter_hud.gd, resources/data/leviathan_tuning.gd, tools/blender/lib/aegis_kit.py
etat: à appliquer
supersede: docs/plans/2026-08-23-boss-pale-leviathan.md (intégralement)
---

# Pale Leviathan — après la première partie jouée en cycles

> **Ce document fait foi au 2026-08-25.** Il ne remplace ni la spec ni les ADR (qui priment).
> Le plan du 2026-08-23 avait **un seul point bloquant** : rejouer le combat. C'est fait —
> son résultat est ci-dessous, et il change la suite.

## Ce que la partie a tranché

Arc complet joué depuis l'écran-titre, sortie propre, aucune `SCRIPT ERROR`. Verdict :

> « Le combat contre le boss de fin est mieux équilibré, mais j'ai réalisé phase 1 phase 2
> phase 1 phase 2 et j'ai l'impression que c'était en boucle. »

**L'équilibrage d'`ADR-0021` est acquis** — c'était la question ouverte depuis deux refontes,
elle est close. Le grief « lancinant » du 23/08 ne s'est pas reproduit.

Ce qui restait était un défaut de **lisibilité de la progression**, corrigé le jour même par
**`ADR-0023`** : le HUD recevait `structure_ratio()` (la cible courante, qui se remplit à
chaque bascule) au lieu de `fight_ratio()` (la progression, qui ne remonte jamais). Le joueur
voyait la jauge faire six fois 100→0. `fight_ratio()` existait, était juste et testé — son
unique consommateur était la **musique**.

Vérifié en capture au cycle 2 : jauge **mesurée à 80,6 %** contre 80,5 % attendus par le
calcul, compteur `CYCLE 2 / 3` lisible, trois pastilles. Avant le correctif, ce même instant
affichait **100 %**. GPU 13,0 ms/image — Quadro T1000, conforme au ×14 connu, pas une
régression.

## Ce qui reste, dans l'ordre

### 1. Rejouer — mais la question a changé

Le combat est maintenant **lisible et équilibré**. Ce qui n'est **pas** jugé :

- **Le nombre de cycles.** La partie en a produit **quatre** (le flux n'est pas tombé au
  troisième passage). C'est permis et désormais nommé `DERNIER ASSAUT` au lieu de
  `CYCLE 4 / 3`. Reste à savoir si un quatrième tour est agréable **maintenant qu'on voit
  où l'on en est** — c'était peut-être toute la question.
- **Alignement halo ↔ hitbox** : jamais jugeable à l'arrêt, toujours ouvert.
- **Cadrage de la plongée en mouvement.**

⚠️ **Ne pas retoucher l'équilibrage sans une nouvelle partie.** Leviers disponibles si et
seulement si le verdict les demande : `shell_orbit_period` 9→7, `plate_health` 460→380,
`flux_health` 5300→plus bas (le garde-fou d'`validate()` refusera d'aller trop loin).

### 2. Correction du kit Blender — **débloquée, c'est le prochain chantier**

L'ordre convenu entre les deux sessions était : *BRIEF-0080 intégré → correction du kit →
régénération → re-revue des silhouettes*. **BRIEF-0080 est intégré** (les quatre épines
pointent vers le joueur, le laser suit l'axe de l'épine). Le premier verrou est donc levé.

`ak.inset_panel()` est un **no-op sur un maillage fraîchement bâti** : `inset_region` lit une
normale de face nulle tant que `normal_update()` n'a pas été appelé. Bordures d'aire
**0,000000 m²** contre **0,000714** avec. Il ne reste que le changement de matériau — un
panneau qui se voit sans exister. Concernées : `build_pale_leviathan.py` (10 appels, 0
`normal_update`), `build_choir_harvester.py` (7), plus `choir_mine`, `null_maw`, `specter_9`.

⚠️ Le correctif va dans **`lib/aegis_kit.py`**, pas dans chaque script — sinon le prochain
l'oubliera comme les précédents. Conséquence à anticiper : la régénération change **tous** les
`sha256`, donc `assets/licenses/ASSET_PROVENANCE.csv` **et** les compte-rendus de brief qui
les citent. CSV partagé → un seul écrivain, probablement un seul commit.

### 3. Dettes ouvertes, aucune urgente

- **`choir_harvester.glb` est sans UV** (0/61) : le mini-boss est intexturable. Cause : ni
  `_triangulate_ngons()` ni `box_project_uv()` dans son script.
- **`HarvesterCombat` attache ses `Beam` comme le Leviathan le faisait** — enfants d'un `Node`
  sous le `BossController`, donc doublement transformés. Corrigé chez le Leviathan
  (`top_level = true`, et c'est le seul endroit du dépôt où le drapeau apparaît),
  **jamais vérifié chez le mini-boss**. Si ses faisceaux sont décalés, personne ne l'a remarqué.
- **`AudioManager` n'arrête pas ses flux à la sortie** : 2 × le nombre de sons en lecture fuit
  à chaque fermeture. Bénin, mais c'est le bruit qui noiera la prochaine vraie fuite.
  ⚠️ Se mesure **uniquement en headless avec `--quit-after`**.
- **`BOSS_PALE_LEVIATHAN.md` décrit toujours quatre phases.** Avertissement en tête ; ses §4 à
  §6 sont de la matière non employée. Sert encore pour les assets.

## Ce que ce chantier a appris

- **Un test d'unité ne remplace pas un test de branchement.** Les deux mesures du combat
  étaient justes et gardées ; c'est le câblage entre le module et le HUD qui était faux, et
  aucun test du module ne pouvait le voir. D'où `tests/unit/test_leviathan_hud_relay.gd`, qui
  garde le **relais** sur un espion de HUD.
- **Une décision juste peut être invalidée par une décision ultérieure, en silence.**
  `ADR-0020` avait choisi la jauge par phase pour un bon motif — l'idiome « il lui reste une
  deuxième barre ». `ADR-0021` a remplacé deux phases par six temps sans que personne ne
  revisite l'idiome. Ce n'est pas une erreur d'exécution, c'est une prémisse retirée.
- **Un compteur qui dépasse son total accuse le jeu.** `cycle 4/3` disait au joueur que le
  programme s'était trompé, alors que le combat n'a jamais été borné à trois tours.
