# ADR-0002 — Développement dans WSL2, test visuel sous Windows natif

- **Date** : 2026-07-11
- **Statut** : accepté (décision utilisateur)

## Contexte

La machine de référence est un PC Windows 11 avec RTX 4080 ; l'agent de développement travaille
dans WSL2 (Debian). Le rendu Vulkan/Forward+ n'est pas fiable dans WSLg : lancer Godot en mode
fenêtré dans WSL peut geler. L'utilisateur a libéré ~20 Go dans WSL et préfère héberger le dépôt
sur le filesystem ext4 (I/O rapides pour git/imports).

## Décision

- Le dépôt vit dans WSL : `/home/admin/sandbox/macross/` (dépôt git **local**, sans remote,
  imbriqué dans `~/sandbox` — ne jamais l'ajouter depuis le dépôt parent).
- Dans WSL, **toute commande Godot est `--headless`** : import, tests, export.
- Le test visuel passe par : `export-win.sh` (export Windows x64 headless) →
  `deploy-win.sh` (copie `build/windows/` vers `/mnt/c/tmp/aegis-ascendant/`) →
  lancement natif via interop (`powershell.exe -File 'C:\tmp\aegis-ascendant\run.ps1'`).

## Conséquences

- Le jeu s'exécute toujours avec le vrai GPU (D3D12/Vulkan natifs Windows) — les mesures de
  performance (FPS, frametime) ne sont valides que côté Windows.
- Interop : toujours `-File` avec un chemin Windows absolu (jamais de CWD UNC `\\wsl$`) ;
  premier lancement possiblement ralenti par Windows Defender.
- Le build copié doit inclure `.exe` **et** `.pck` (pack séparé, spec §27.1).
- L'éditeur GUI Godot n'est pas utilisé ; les scènes `.tscn`/`.tres` sont écrites en texte.
