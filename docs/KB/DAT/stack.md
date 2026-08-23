---
titre: Stack technique et versions épinglées
type: dat
statut: actif
maj: 2026-08-23
---

# Stack technique

Toutes les versions ci-dessous sont **épinglées dans le dépôt** : c'est le fichier qui fait foi, pas
cette page. La colonne « épinglé où » existe pour qu'on aille corriger à la source.

| Brique | Version | Épinglé où |
|---|---|---|
| Moteur | **Godot 4.7-stable**, renderer **Forward+** | `scripts/bootstrap.sh` (`GODOT_VERSION`), `project.godot` (`config/features`) |
| Langage | **GDScript typé** — le typage est une règle dure, pas un style | `docs/SPEC_AEGIS_ASCENDANT.md` §31 |
| Blender (chaîne 3D) | **4.5.11**, invoqué `blender45` | `scripts/bootstrap-blender.sh` |
| Outils d'assets | Python 3 (`tools/*.py`) | `tools/` |
| Binaire de jeu | Export **Windows Desktop x64** → `build/windows/AegisAscendant.exe` | `export_presets.cfg` |
| Binaires versionnés | **Git LFS** (`*.png`, `*.wav`, `*.ogg`, `*.glb`, `*.blend`) | `.gitattributes` |

## Ce qui n'est pas dans la stack, et c'est voulu

Aucune dépendance native, aucun backend, aucun réseau, aucun framework de test tiers — le runner de
tests est maison (`tests/test_runner.gd`, spec §28.1). Ces absences sont des **lois** du projet, pas
des trous à combler : voir [`REGLES/lois.md`](../REGLES/lois.md).

## Réglages de projet qui se paient à l'écran

- Résolution de référence **1920 × 1080** (`project.godot`), rendue à travers un post-traitement
  rétro à **960 × 540 + scanlines**. Conséquence pratique : **le détail fin d'une texture disparaît
  en jeu**. Le détail se met dans la géométrie — cf. `.claude/resources/pratique-revue-asset.md`.
- Scène de démarrage : `scenes/boot/boot.tscn`.
- Quatre autoloads, dans un ordre qui compte (`SettingsManager` avant `AudioManager`, sans quoi les
  volumes de bus sont appliqués trop tard) : détail dans `ARCHITECTURE_TECHNIQUE.md` §2.

⚠️ **Un autoload ne s'appelle jamais par son identifiant global dans un script** : les tests
tournent en mode `--script`, où les autoloads n'existent pas, et `GameState.foo()` casse alors la
compilation. Câbler par signal/injection, ou cache typé. C'est une loi — voir
[`REGLES/lois.md`](../REGLES/lois.md).
