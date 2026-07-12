# Architecture technique — Aegis Ascendant

> État : reflète le code réel au terme de la session du 2026-07-11 (30 commits).
> Moteur : **Godot 4.7-stable**, renderer Forward+, GDScript typé. Voir aussi
> `docs/SPEC_AEGIS_ASCENDANT.md` (cahier des charges) et `docs/decisions/` (ADR).

## 1. Vue d'ensemble

Vertical shooter 2.5D : le gameplay se joue sur un **plan logique 2D** projeté dans une
scène 3D vue par une caméra perspective à faible angle. Le jeu déroule un arc complet en
une seule scène de niveau pilotée par une machine à phases.

Trois couches :
- **Autoloads** (services globaux) : état, navigation, audio.
- **Scène de niveau** (`graybox.tscn`) : contient tous les sous-systèmes de jeu et un
  **director** (`graybox_root.gd`) qui les orchestre par signaux.
- **Sous-systèmes** : joueur, projectiles, ennemis, boss, forteresse, pickups, VFX, UI.

Principes transverses (spec §20, §31) : composition > héritage ; **signaux** pour les
événements ; **Resources typées** pour les données ; **pooling** partout ; plan logique
autoritaire ; **zéro allocation dans les boucles critiques**.

## 2. Autoloads (`project.godot [autoload]`)

| Autoload | Fichier | Rôle |
|---|---|---|
| `GameState` | `scripts/core/game_state.gd` | Machine à états globale (`BOOT, LOADING, FIGHTER_COMBAT, GAME_OVER, VICTORY`), transitions validées + journalisées, `score`, signaux `state_changed`/`score_changed`. Enregistre les actions d'input au boot (via `InputBootstrap`) et gère le flag `--novsync`. |
| `SceneRouter` | `scripts/core/scene_router.gd` | `goto_scene(path)` avec vérification d'erreur. |
| `SettingsManager` | `scripts/core/settings_manager.gd` | Volumes par bus, persistés dans `user://settings.cfg`, appliqués à `AudioServer` au boot. Chargé **avant** `AudioManager`. La donnée elle-même est dans `SettingsData` (pure, testée). |
| `AudioManager` | `scripts/core/audio_manager.gd` | Pool de 16 `AudioStreamPlayer` sur le bus `SFX` + lit de moteur + **deux decks musique** avec crossfade par `Tween`. `play(cue, volume_db)`, `set_music_state(state)`, `set_engine_intensity(v)`. Aucun chemin d'asset en dur : tout vient des banques. |

### Audio (spec §18, ADR-0007)

- **Bus** (`resources/audio/default_bus_layout.tres`, généré par `tools/audio/make_bus_layout.gd`) :
  `Master` (compresseur léger + `AudioEffectHardLimiter` à −0,5 dB, donc aucun clipping),
  et `Music` / `SFX` / `Voice` qui y sont envoyés. Le bus `Voice` existe, les voix pas encore.
- **Banques** : `resources/audio/sfx_bank.tres` (20 cues) et `music_bank.tres` (9 pistes), toutes
  deux des `AudioCueBank` d'`AudioCueData` (stream, bus, niveau, plage de pitch, anti-spam,
  bouclage) — c'est la ressource typée demandée par la spec §22.1. Un cue inconnu déclenche un
  `push_warning`, il n'échoue plus en silence.
- **Musique adaptative** : `MusicDirector.resolve(MusicContext)` est une **fonction pure** — aucun
  nœud, aucun `AudioServer` — donc entièrement testable en headless. Le level director met à jour
  le contexte (progression de vague, phase, PV du boss, écran nettoyé) ; `AudioManager` exécute.
  Aucune coupure sèche : chaque changement d'état est un fondu (6 s par défaut, 1,2 s vers Boss
  Phase 2).
- **Pipeline d'assets** : `tools/audio/generate_prototype_sfx.py` (stdlib, seed fixe) et
  `generate_music.py` (numpy, un RNG par état) écrivent dans `assets/source/audio/` ;
  `build_audio.py` masterise (DC retiré, −1 dBFS, anti-clic) et livre dans `assets/imported/audio/`
  — WAV pour les SFX (importés en QOA), OGG pour la musique. Toute la chaîne est **idempotente**.

`InputBootstrap` (`scripts/core/input_bootstrap.gd`, `class_name`, **pas** un autoload) enregistre
les actions `move_left/right/up/down` (WASD + flèches, `physical_keycode`) et `fire_primary` (Espace).

**Convention critique** (CLAUDE.md) : ne jamais référencer un autoload par identifiant global
dans un script (`GameState.foo()` casse la compilation en mode `--script`). Toujours
`const XScript := preload(...)` + `@onready var _x := get_node("/root/X")`.

## 3. Le plan de gameplay (`GameplayPlane`)

`scripts/gameplay/gameplay_plane.gd` — classe **statique**, pure, testée headless.
- Plan logique = plan monde XZ à Y=0 ; `+y` logique = `-Z` monde (haut de l'écran).
- `to_world(Vector2) -> Vector3`, `to_plane(Vector3) -> Vector2`, `clamp_to_bounds`, `is_inside(margin)`.
- `BOUNDS = Rect2(-12,-7, 24,14)` (24×14 unités).
- **La position logique fait foi pour toutes les collisions** ; le 3D n'est qu'une projection.

## 4. Director de niveau (`graybox_root.gd`)

Script racine de `graybox.tscn`. Machine à phases (enum `Phase`) :

```
FIGHTER_WAVES ─(wave_cleared)→ MINI_BOSS ─(boss defeated)→ DOCKING
   → COMMAND_TRANSFER ─(timer)→ FORTRESS_BOSS ─(boss defeated)→ VICTORY
```

Il récupère par `@onready`/`get_node` les sous-systèmes de la scène (player, bullet manager,
VFX, caméra, HUD, pickups, wave spawner) et les câble par signaux. Il :
- réinitialise le score au démarrage ;
- connecte `enemy.destroyed` → score + explosion + shake + drop pickup + SFX ;
- lance le mini-boss quand la vague est nettoyée ;
- orchestre l'appontage (instancie l'Aegis Citadel, la fait glisser, met le joueur en autopilote) ;
- **héberge le contrôle de la forteresse** (déplacement, batteries, intégrité) dans son
  `_physics_process` pendant la phase `FORTRESS_BOSS` ;
- déclenche la finale Helios Lance et l'écran de victoire.

C'est le point central d'orchestration ; il porte aussi les **flags de debug** (voir §13).

## 5. Joueur

| Fichier | Rôle |
|---|---|
| `scripts/player/player_fighter_controller.gd` (`PlayerFighterController`) | Mouvement arcade (`move_toward`, accel < 250 ms), tir Pulse Array (niveaux 1-5 → géométrie de tir escaladante), bouclier, vies, invulnérabilité clignotante, respawn, autopilote (appontage), mode démo, traînée moteur + muzzle flash (GPUParticles3D construits en code). Émet `shield_changed`, `lives_changed`, `hit_taken`, `destroyed_at`, `game_over`, `power_changed`, `autopilot_reached`. |
| `scripts/player/player_shield.gd` (`PlayerShield`, `RefCounted`) | Modèle de bouclier pur (dégâts, invuln post-impact, régénération après délai). **Testé** (`tests/unit/test_player_shield.gd`). |
| `resources/data/player_stats.gd` (`PlayerStats`) + `resources/player/specter9_stats.tres` | Stats : vitesse, accel, hitbox, cadence, bouclier, régen, invuln, vies. `validate()`. |

Le visuel (`scenes/player/player_fighter.tscn`) est un **Sprite3D** (concept Specter-9) posé à
plat sur le plan (rotation X = -90° en code), inclinaison visuelle (banking) sur `VisualRoot`.
Le joueur s'enregistre comme `BulletTarget` (équipe PLAYER) auprès du BulletManager.

## 6. Système de projectiles (`BulletManager`)

`scripts/projectiles/bullet_manager.gd` — **data-oriented**, cœur perf du jeu.
- Tableaux `Packed*` préalloués (positions, vélocités, rayons, dégâts, TTL, équipes, alive),
  pile d'indices libres. `MAX_BULLETS = 600`, sous-budgets 150 (allié) / 450 (ennemi).
- Rendu par **2 `MultiMeshInstance3D`** (une par équipe : allié cyan / ennemi corail).
  Mise à jour du **buffer en bloc** (`multimesh.buffer =`, base d'identité pré-remplie, seule
  l'origine est réécrite par balle) — plus rapide que `set_instance_transform` par instance.
- **Grille spatiale** à capacité fixe (12×8×32, plate, zéro allocation) pour la collision.
- Collision cercle-cercle sur le plan logique, cellules 3×3 autour de chaque `BulletTarget`.
- Logique dans `step(delta)` séparée de `_physics_process` → **testable headless**.
- API : `spawn_bullet`, `spawn_from_data(team, pos, dir, ProjectileData)`, `despawn`,
  `register_target`/`unregister_target`.

`BulletTarget` (`scripts/projectiles/bullet_target.gd`, `RefCounted`) : proxy de collision
(position, radius, team, `hit_callback`). Chaque entité met à jour sa position chaque frame.

`ProjectileData` (`resources/data/projectile_data.gd`) : speed, radius, damage, ttl. Instances :
`pulse_shot`, `needle_shot`, `boss_shot`, `fortress_battery` (`.tres`).

## 7. Ennemis

- `scripts/enemies/enemy_controller.gd` (`EnemyController`) : base de composition. Descente +
  sinus latéral, tir frontal lent, `HealthComponent` enfant, `BulletTarget`, pooling
  (activate/deactivate, pas de `queue_free` en boucle). Émet `destroyed`.
- `scripts/gameplay/health_component.gd` (`HealthComponent`, Node) : PV, signaux `damaged`/`died`. **Testé**.
- `resources/data/enemy_data.gd` (`EnemyData`) + `needle_scout.tres` ; `scenes/enemies/needle_scout.tscn`
  (mesh magenta — le seul sprite forge basse-résolution non intégré).

## 8. Vagues (`WaveSpawner`)

`scripts/gameplay/wave_spawner.gd` : exécute une timeline `WaveData` (data-driven, base du futur
EncounterDirector). **Préinstancie** toutes les entités en `_ready` (pool désactivé), les active
par `time_offset`, émet `wave_cleared`. Ordonnancement pur `build_schedule()` **testé**.
`resources/data/wave_data.gd` + `wave_entry.gd` + `resources/encounters/wave_graybox_01.tres`.

## 9. Boss (`BossController`)

`scripts/bosses/boss_controller.gd` — **réutilisable** (mini-boss ET boss final).
- Corps = Sprite3D (concept), `HealthComponent` implicite via `_health`, `BulletTarget` (grand rayon).
- Cycle : entrée (invulnérable) → drift horizontal → attaques cyclées.
- **Patterns** (`Pattern` enum) : `RADIAL` (burst circulaire), `AIMED_SPREAD` (vers le joueur),
  `FAN` (éventail descendant). Intensité ↑ par phase (nombre de projectiles, cadence).
- **Phases** dérivées de seuils de PV (`phase_count`). Émet `phase_changed`, `health_changed`, `defeated`.
- Instances : `scenes/bosses/choir_harvester.tscn` (mini, 1 phase, 420 PV) et
  `pale_leviathan.tscn` (final, 4 phases, 950 PV).

## 10. Forteresse (`AegisCitadel` + contrôle dans le director)

- `scripts/fortress/aegis_citadel.gd` (`AegisCitadel`) : grand Sprite3D concept. `slide_to(target, speed)`
  (appontage + repositionnement en bas), `bay_position()`, signal `arrived`. Scène `aegis_citadel.tscn`.
- **Le contrôle de la forteresse est dans `graybox_root._physics_process`** (phase FORTRESS_BOSS) :
  déplacement sur l'axe X (clamp), **Twin Rail Batteries** (projectiles `fortress_battery`,
  alternance gauche/droite), `BulletTarget` PLAYER, **intégrité** (jauge, reset au lieu d'un
  échec dur — démo tolérante, spec §12.8). HUD passe en mode forteresse.

## 11. Effets visuels & caméra

| Élément | Fichier |
|---|---|
| Explosions poolées (flash sphère + étincelles GPU, 3 tailles) | `scripts/fx/vfx_explosion.gd` + `vfx_manager.gd` |
| Screen shake centralisé (trauma², décroissance, `FastNoiseLite`) | `scripts/fx/camera_director.gd` (contient la Camera3D enfant) |
| Fond spatial procédural (starfield 3 couches + nébuleuse fbm, défilant) | `shaders/space_background.gdshader` → `scenes/vfx/space_backdrop.tscn` |
| Post-processing (glow/bloom, tonemap AgX, adjustments) | `resources/graphics/space_environment.tres` (WorldEnvironment) |
| Traînée moteur + muzzle flash | construits en code dans `PlayerFighterController` |

## 12. UI

- `scripts/ui/fighter_hud.gd` + `scenes/ui/fighter_hud.tscn` : bouclier, puissance, score, vies,
  **barre de boss**, **bannière de phase** (DOCKING / COMMAND TRANSFER…), **mode forteresse**
  (relabel INTEGRITY / FORTRESS). Lié par le director via `bind_player`/`bind_score`.
- `scripts/ui/victory_screen.gd` + `victory_screen.tscn` : score, rang (S/A/B/C), rejouer (Entrée).
- `scripts/ui/boot_screen.gd` + `scenes/boot/boot.tscn` : titre + contrôles + Entrée → niveau.

## 13. Outillage, tests, build

- **Scripts bash** (`scripts/`) : `bootstrap.sh` (installe Godot 4.7 + templates, SHA512),
  `check.sh` (import headless + parse + tests — **porte de qualité**), `export-win.sh`,
  `deploy-win.sh` (copie `/mnt/c/tmp/aegis-ascendant`, tue les instances précédentes, lance via interop).
  `scripts-win/run.ps1` (lancement côté Windows).
- **Tests** (`tests/`) : `test_runner.gd` (SceneTree, découvre `unit/test_*.gd`, parse-check global),
  `test_case.gd` (assertions accumulantes). 39 tests (plane, pool, collision, health, wave, shield,
  transitions, mouvement). `perf/bench_bullets.gd` (bench headless du BulletManager).
- **Git LFS** pour `*.png/*.wav/*.ogg/*.glb/*.blend`. `assets/source/` est `.gdignore`é (non importé).
- **Flags de debug (cmdline, après `++`)** : `--goto-graybox`, `--demo`, `--no-wave`,
  `--pickup-demo`, `--skip-to-boss`, `--skip-to-dock`, `--skip-to-fortress`, `--skip-to-victory`,
  `--capture --capture-after=N`, `--no-backdrop`, `--no-glow`, `--novsync`.
  `scripts/debug/screen_capture.gd` sauvegarde une capture (boucle de vérif WSL→Windows).

## 14. Performance

- Bench headless : `BulletManager.step()` ≈ **0,32 ms** à 600 projectiles.
- Réel (RTX 4080, vsync off, scène la plus lourde forteresse+boss) : **1027–1771 FPS (0,87 ms/frame)**.
- ⚠️ **Le « 4 FPS » observé en test autonome = V-Sync bridée par une session Windows inactive**,
  PAS un bug (voir `docs/decisions/` / mémoire). Tester avec `--novsync`. En jeu réel écran allumé,
  la V-Sync cappe au moniteur.

## 15. Limites techniques connues

- Le rendu MultiMesh n'est pas couvert par le bench headless (pas de GPU en WSL).
- Swept collision absente (spec §21.2) : OK aux vitesses actuelles, à ajouter avant des projectiles très rapides.
- Le contrôle forteresse vit dans le director (pas encore extrait en `FortressController` dédié).
- Warnings « ObjectDB leaked » à la sortie **forcée** (`--quit-after` pendant tweens/timers) — sans
  impact en jeu normal (le changement de scène libère tout).
- Le Needle Scout reste un mesh (sprite forge trop basse résolution).
