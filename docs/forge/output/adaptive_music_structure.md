# Structure musicale adaptative — prototype

- **Brief** : `docs/forge/briefs/BRIEF-0011-audio-prototype.md`
- **Statut** : **implémenté** (2026-07-12). Ce document reste normatif : `tools/audio/generate_music.py`
  en lit les tempos, centres tonaux et couches, et `scripts/audio/music_director.gd` en applique les
  transitions. Toute modification ici doit être reportée dans les deux.

## Socle commun

- Signature principale : cellule originale de quatre notes, intervalles `+5, -2, +4` demi-tons.
- Mesure : 4/4, sauf Docking en 6/8.
- Sources : synthétiseurs analogiques, basse électronique et percussions orchestrales.
- Synchronisation : transitions aux fins de mesures de 4 ou 8, stems bouclables de même durée.
- Tonalité pivot : ré mineur modal ; éviter toute mélodie ou progression identifiable.

## États

| État | Tempo | Centre tonal | Couches actives | Transition |
|---|---:|---|---|---|
| Launch | 92 BPM | D dorien | drone, pulsation filtrée, motif lointain | ouverture du filtre sur 8 mesures |
| Skirmish | 116 BPM | D dorien | basse, batterie légère, arpège | ajout au prochain bloc de 4 mesures |
| Fleet Battle | 132 BPM | D mineur | percussions pleines, cuivres synthétiques, ostinato | montée de 2 mesures |
| Docking | 84 BPM, 6/8 | A suspendu | pulsation douce, séquence stéréo, nappes | pivot rythmique synchronisé sur 4 mesures |
| Fortress Awakening | 108 BPM | D dorien | chœur synthétique abstrait, basses, impacts espacés | couches activées par batterie |
| Boss Phase 1 | 136 BPM | D phrygien | ostinato sombre, batterie lourde, motif ennemi | coupe contrôlée puis impact |
| Boss Phase 2 | 148 BPM | E♭ mineur | contre-rythme, basse distordue, nappes tendues | accélération masquée sur 8 mesures |
| Final Charge | 156 BPM | D mineur | toutes couches alliées, montée harmonique, pulse Helios | crescendo verrouillé sur la charge |
| Victory | 96 BPM | D majeur add6 | motif principal élargi, accords ouverts, percussion réduite | résolution après le tir final |

## Implémentation (2026-07-12)

Pistes rendues : 16 mesures (8 pour Docking), 29 à 36 s chacune, stéréo 44,1 kHz, Vorbis,
2,9 Mo au total. Bouclées **par construction** : une queue de 2 s est rendue au-delà de la
dernière mesure puis repliée sur le début, si bien qu'une résonance longue retombe sur
elle-même au lieu d'être tranchée. Écart de soudure mesuré : ≤ 9 % du RMS, quasi nul sur
la plupart des pistes.

Fondus appliqués (`MusicDirector.crossfade_seconds`) : 6 s par défaut, **1,2 s vers Boss
Phase 2** (la « coupe contrôlée puis impact » ci-dessous), 2,5 s vers Final Charge, 3,5 s
vers Victory.

## Règles de mix adaptatif

- Les projectiles ennemis et alarmes conservent une réserve de 6 dB au-dessus de la musique.
- L'Overdrive ajoute une octave d'arpège et une couche de percussion, sans changer le tempo.
- Les dialogues radio réduisent temporairement le médium musical de 2 à 3 dB.
- Aucun changement d'état ne coupe une résonance longue : conserver une queue commune.
- Victory ne démarre qu'après disparition des projectiles dangereux.
