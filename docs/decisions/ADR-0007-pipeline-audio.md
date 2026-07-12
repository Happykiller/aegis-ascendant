# ADR-0007 — Pipeline audio : formats de livraison, mastering et génération

- **Statut** : accepté
- **Date** : 2026-07-12
- **Contexte** : passe audio complète (E1→E6). Complète ADR-0002 (WSL) et ADR-0004 (délégation créative).

## Contexte

La spec §18.5 décrit un pipeline « WAV source → OGG livraison, normalisation, bus séparés,
compression légère, limiteur master, aucun clipping ». Le prototype livrait des WAV bruts,
sans bus ni mastering, et sans musique. Trois questions devaient être tranchées avant de
produire quoi que ce soit.

## Décision

### 1. OGG pour la musique, WAV (importé en QOA) pour les SFX

La §18.5 est appliquée **à la lettre pour la musique** et **à l'esprit pour les SFX**.

- **Musique → OGG Vorbis** (`ffmpeg -c:a libvorbis -q:a 4`). Neuf pistes de ~30 s en WAV
  pèseraient ~50 Mo dans Git LFS ; en Vorbis, ~5 Mo. Non négociable.
- **SFX → WAV source, importés par Godot en QOA** (`compress/mode=2`, déjà en place).
  Le `.pck` **ne contient donc aucun PCM brut** : l'objectif de la spec (ne pas embarquer
  du non-compressé) est déjà atteint. Passer les SFX en Vorbis ajouterait une latence de
  décodage sur des one-shots de 80 à 200 ms, pour un gain de taille négligeable. La §18.5
  liste des formats de travail possibles, pas une obligation par cue.

Conséquence : `assets/source/audio/` et `assets/imported/audio/` cessent d'être des copies
identiques (ce qu'elles étaient, sans raison). `source/` est le **rendu brut du synthé**,
`imported/` la **version masterisée** — c'est ce que le moteur importe.

### 2. Un étage de mastering explicite : `tools/audio/build_audio.py`

Le mastering ne vit ni dans le générateur ni dans le moteur, mais dans une étape dédiée,
idempotente : DC retiré, normalisation à **−1 dBFS**, fondu de sortie de 5 ms (sauf sur les
cues bouclés, où il créerait le trou qu'on cherche à éviter), et une **assertion qui échoue
plutôt que de livrer un fichier qui clippe**. Le limiteur `AudioEffectHardLimiter` du bus
Master (`ceiling_db = -0.5`) est la seconde ligne de défense, pas la première.

Le bus layout lui-même est produit par `tools/audio/make_bus_layout.gd` via l'API du moteur,
et non écrit à la main : la sérialisation `.tres` d'`AudioBusLayout` est un format éditeur
qu'on n'a pas à deviner (rappel ADR-0002 : pas d'éditeur sous WSL).

### 3. Génération procédurale en Python, dans la session principale

ADR-0004 délègue la production créative à `asset-forge` via un brief versionné. **Écart
assumé ici** : les SFX ne sont pas des assets dessinés mais la **sortie déterministe d'un
script** (`tools/audio/generate_prototype_sfx.py`, seed fixe `0xAE615`). Le livrable
reviewable est le script, pas le WAV ; le versionner et le relire vaut mieux que de faire
transiter un binaire par un brief. La provenance reste enregistrée dans
`ASSET_PROVENANCE.csv` (§24.7), avec le script comme `source_tool`.

Corollaire : **les nouveaux cues s'ajoutent à la fin de `main()`**. Le RNG est partagé et
séquentiel — insérer un cue au milieu décalerait le bruit de tous les sons suivants et
ferait diverger des fichiers qu'on n'a pas touchés.

### 4. Pas d'`AudioStreamInteractive` pour la musique adaptative

Godot 4.7 fournit `AudioStreamInteractive` (clips + table de transitions). Sa sérialisation
`.tres` est un format éditeur non documenté, et on n'a pas d'éditeur. La musique adaptative
utilise donc **deux `AudioStreamPlayer` sur le bus `Music` et un `Tween` sur `volume_db`** :
robuste, testable, réversible. À reconsidérer le jour où une session éditeur Windows existe.

## Conséquences

- `ffmpeg` (avec `libvorbis`) devient une dépendance de **build d'assets**, pas de jeu.
- Les sources WAV de musique (~50 Mo) sont **gitignorées** ; seuls les OGG sont commités.
- `pickup_collect` est supprimé : remplacé par `pickup_power` / `pickup_shield` /
  `pickup_score`, un son distinct par bonus, exigé par la charte créative (« jamais la
  couleur seule ») et par la spec §10.1.
- Le seul son non couvert par un cue dédié reste la voix radio (spec §18.4) — hors périmètre,
  suivi au backlog.
