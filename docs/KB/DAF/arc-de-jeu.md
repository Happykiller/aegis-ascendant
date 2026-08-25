---
titre: L'arc d'une partie — six phases, un seul vaisseau
type: daf
statut: actif
maj: 2026-08-25
---

# L'arc d'une partie

## L'invariant

Le joueur **pilote le chasseur Specter-9 du début à la fin**. Aucune transformation, aucun
changement de véhicule en cours de niveau. C'est la décision **ADR-0010** (2026-07-19), prise après
usage : le changement de vaisseau cassait le flow et la lisibilité de l'arme du joueur.

## Les six phases

```
FIGHTER_WAVES → MINI_BOSS → ASTEROID_FIELD → FINAL_BOSS → DOCKING → VICTORY
```

Vérifié dans le code : `scripts/gameplay/graybox_root.gd` (`enum Phase`). Le niveau entier
est piloté par ce director, en dur — un `EncounterDirector` data-driven reste à écrire
(`docs/BACKLOG.md`, P1).

`ASTEROID_FIELD` est la dernière arrivée (**ADR-0027**, 2026-08-25) : la traversée qui sépare les
deux boss, jouée avec les trois unités que le bestiaire avait livrées sans qu'aucune rencontre ne
les emploie (Choir Mine, Null Maw, Leech Drone). Elle dure 45 à 60 s. Son décor propre — survol de
lune et astéroïdes — reste à faire : il **remplacera** le fond spatial au lieu de s'y ajouter,
faute de budget GPU (voir l'ADR).

⚠️ **`MusicContext.LevelPhase` reflète `Phase` PAR VALEUR.** Les deux enums se modifient ensemble ;
`tests/unit/test_music_director.gd` est le seul garde-fou et il est là pour ça.

À ne pas confondre avec la machine d'états **applicative** `GameState.State`
(`BOOT, LOADING, FIGHTER_COMBAT, GAME_OVER, VICTORY, CODEX`, dans `scripts/core/game_state.gd`) :
elle gouverne les écrans, pas la progression du niveau. Les cinq phases ci-dessus se déroulent
**entièrement à l'intérieur** de `FIGHTER_COMBAT`.

Chaque phase a son `_start_*()` dans le director, et c'est la fin de la précédente qui l'appelle :
la vague nettoyée ouvre sur le mini-boss, sa défaite sur le champ d'astéroïdes, le champ nettoyé
sur le boss final. Deux `WaveSpawner` distincts portent les deux vagues — le second est monté et
**peuplé** au même instant que le premier, mais dort jusqu'à `begin()` (spec §26.1 : zéro
`instantiate()` en cours de partie).

Le **docking est la séquence de clôture**, pas un milieu de niveau : la citadelle arrive après la
défaite du boss final, le chasseur s'y ancre en autopilote, puis l'écran de victoire.

## ⚠️ Écart constaté avec la documentation d'architecture

`docs/architecture/ARCHITECTURE_FONCTIONNELLE.md` date du **2026-07-11**, soit **huit jours avant**
ADR-0010. Ses §4.5 et §4.6 décrivent encore :

- un appontage **en milieu de niveau** suivi d'un transfert de commande ;
- une **phase forteresse jouable** — le joueur déplace la citadelle et tire ses Twin Rail Batteries,
  avec une jauge d'intégrité.

**Rien de tout cela n'existe plus** : ADR-0010 a supprimé la phase `COMMAND_TRANSFER` et le contrôle
de la forteresse. Le boss final se combat au chasseur, comme le mini-boss.

> **À COMPLÉTER — décision de l'opérateur.** Que fait-on de `ARCHITECTURE_FONCTIONNELLE.md` §4.5 et
> §4.6 ? Trois options : (a) le corriger et le redater, (b) l'archiver en le marquant « état au
> 2026-07-11, voir ADR-0010 », (c) le laisser tel quel et se reposer sur les ADR. Cette KB ne
> tranche pas seule — le document est hors de son périmètre d'écriture.
