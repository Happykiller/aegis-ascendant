# ADR-0010 — Un seul vaisseau ; suppression de la transformation en forteresse ; docking = clôture

- **Date** : 2026-07-19
- **Statut** : accepté (décision du propriétaire)
- **Amende / supersede** : spec §6.5 (docking en milieu de niveau), §6.6 (transfert de commande),
  §12 (boss forteresse joué en pilotant la citadelle).

## Contexte

Le niveau enchaînait : `FIGHTER_WAVES → MINI_BOSS → DOCKING → COMMAND_TRANSFER → FORTRESS_BOSS →
VICTORY`. À l'appontage, le joueur **cessait de piloter le chasseur** et **devenait la forteresse**
(Aegis Citadel) : déplacement de la citadelle, tir de ses batteries, jauge d'intégrité — puis le boss
final se combattait sous cette forme. C'était une **épreuve technique** (changement de véhicule en
cours de niveau). À l'usage, le propriétaire juge ce changement de vaisseau raté : il casse le flow et
la lisibilité de l'arme du joueur.

## Décision

- Le joueur **pilote le chasseur Specter-9 du début à la fin**. Plus aucune transformation.
- Nouvel arc : **`FIGHTER_WAVES → MINI_BOSS → FINAL_BOSS → DOCKING → VICTORY`**.
  - Le **boss final** (Pale Leviathan) se combat **au chasseur**, exactement comme le mini-boss.
  - Le **docking devient la séquence de clôture** : après la défaite du boss final (finish
    spectaculaire « Helios Lance » conservé), la citadelle arrive, le chasseur s'y ancre en
    autopilote, puis l'écran de victoire.
- **Supprimé** : phase `COMMAND_TRANSFER`, contrôle de la forteresse (déplacement + batteries
  `_fire_battery`), intégrité de forteresse, usage de la jauge HUD forteresse.

## Conséquences

- `scripts/gameplay/graybox_root.gd` nettement simplifié (enum `Phase` à 5 états, `_physics_process`
  réduit au bruit moteur, retrait des constantes/vars/fonctions forteresse).
- Musique adaptative alignée : `FINAL_BOSS` pilote la musique de boss (phases → charge finale) ; l'état
  `DOCKING` devient le **lit calme de la conclusion** (au lieu d'un passage en milieu de niveau).
  `music_context.gd` (enum), `music_director.gd` (resolve) et `test_music_director.gd` mis à jour ;
  `check.sh` vert (93 tests). Flux vérifié en jeu (`--skip-to-final`) : FINAL BOSS → 4 phases →
  DOCKING → VICTORY.
- Flag debug `--skip-to-fortress` → **`--skip-to-final`** (saut au boss final).
- **Orphelins conservés** (inoffensifs, élagage possible plus tard) : `fighter_hud.set_integrity()`,
  l'état musical `FORTRESS_AWAKENING` (+ son `.ogg` et son entrée de banque), le cadre HUD forteresse,
  `resources/weapons/fortress_battery.tres`, `AegisCitadel.battery_origin()`. Le modèle **Aegis
  Citadel reste utilisé** pour l'appontage de clôture.
- Les sections spec §6.5/§6.6/§12 sont **amendées/superseded** par cet ADR (les ADR priment sur la
  spec, cf. CLAUDE.md).
