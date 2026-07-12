# BRIEF-0011 — Audio prototype

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur intérimaire (Codex, continuité exceptionnelle)
- **Date** : 2026-07-11

## Objectif

Créer un kit original de dix SFX de prototype et définir la structure musicale adaptative des
neuf états du niveau. Les sons doivent être courts, lisibles, reproductibles et sans clipping.

## Direction

Synthèse rétrofuturiste militaire : oscillateurs simples, bruit filtré, enveloppes rapides et
transitoires nettes. Aucun sample externe. Les sons alliés privilégient le registre clair et
stable ; les menaces ennemies, le registre instable et descendant.

## Livrables

| Fichier | Fonction |
|---|---|
| `assets/source/audio/sfx/player_pulse.wav` | tir allié |
| `assets/source/audio/sfx/enemy_pulse.wav` | tir ennemi |
| `assets/source/audio/sfx/hull_impact.wav` | impact de coque |
| `assets/source/audio/sfx/shield_impact.wav` | impact de bouclier |
| `assets/source/audio/sfx/small_explosion.wav` | destruction légère |
| `assets/source/audio/sfx/pickup_collect.wav` | collecte de bonus |
| `assets/source/audio/sfx/danger_alarm.wav` | alerte immédiate |
| `assets/source/audio/sfx/docking_lock.wav` | verrouillage d'appontage |
| `assets/source/audio/sfx/rail_battery.wav` | batterie lourde |
| `assets/source/audio/sfx/helios_lance.wav` | super-arme |
| `docs/forge/output/adaptive_music_structure.md` | structure musicale |
| `tools/audio/generate_prototype_sfx.py` | générateur déterministe |

## Contraintes techniques

- WAV PCM mono, 44 100 Hz, 16 bits.
- Crête absolue sous `-1 dBFS` ; aucune saturation numérique.
- Durée maximale 2 secondes ; silence terminal court.
- Génération entièrement procédurale avec bibliothèque standard Python.
- Aucun téléchargement, sample, thème, mélodie ou imitation d'une œuvre existante.

## Critères d'acceptation

- [x] Dix WAV valides et distincts
- [x] Aucun clipping, DC offset excessif ou fichier vide
- [x] Script reproductible avec graine fixe pour le bruit
- [x] Neuf états musicaux documentés avec tempo, tonalité, couches et transitions
- [x] Provenance complète

## Hors périmètre

Pas d'OGG, voix, doublage, musique finale, import Godot, bus audio ou mixage en jeu.

## Suite (2026-07-12)

Le hors-périmètre ci-dessus a depuis été levé, hors voix : OGG, musique finale (les neuf
états sont composés), import Godot, bus audio et mixage en jeu sont livrés par la passe
audio E1→E6 (voir `docs/decisions/ADR-0007-pipeline-audio.md`). Les dix WAV d'origine sont
passés à vingt, et `pickup_collect` a été remplacé par un son par type de bonus.
**Seules les voix radio restent à produire** (spec §18.4).
