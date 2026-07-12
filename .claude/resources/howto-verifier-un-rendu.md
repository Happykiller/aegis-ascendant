# Howto — vérifier un rendu visuel depuis WSL, sans solliciter l'opérateur

Le dev se fait dans WSL (pas de GPU fiable), le jeu tourne sur Windows (ADR-0002). On pourrait
croire qu'il faut demander à l'opérateur de regarder l'écran à chaque itération visuelle. **Non.**

Le projet embarque un helper de capture (`scripts/debug/screen_capture.gd`) : il attend N images,
écrit un PNG à côté de l'exe, puis quitte. Le PNG est lisible depuis WSL sous
`/mnt/c/tmp/aegis-ascendant/` — donc Claude peut **juger son propre rendu**.

```bash
./scripts/export-win.sh debug
./scripts/deploy-win.sh -- ++ --novsync --goto-graybox --capture --capture-after=200
# -> [ScreenCapture] saved (0) — GPU 0.753 ms/frame: C:/tmp/aegis-ascendant/capture.png
```

Puis lire l'image (outil `Read`) depuis `/mnt/c/tmp/aegis-ascendant/capture.png`.

## Les deux pièges qui coûtent une itération chacun

**1. Le séparateur `++` est obligatoire.** Les flags de jeu sont lus par
`OS.get_cmdline_user_args()`, qui ne renvoie que ce qui suit `++`. Sans lui, les flags sont avalés
par Godot et **silencieusement ignorés** — la capture ne s'arme pas, et rien ne le signale.

```bash
./scripts/deploy-win.sh -- --capture              # ❌ ignoré, aucune capture
./scripts/deploy-win.sh -- ++ --capture           # ✅
```

**2. `--capture-after` compte des IMAGES, pas des secondes.** Le jeu tourne à >1000 FPS en
`--novsync` : 3600 images ≈ **3 secondes de jeu**, pas une minute. Pour atteindre le mini-boss il
faut laisser tourner en temps réel (`timeout 300 ./scripts/deploy-win.sh -- ++ --novsync --demo`)
et lire la sortie, pas viser une image.

## Flags utiles

| Flag | Effet |
|---|---|
| `--goto-graybox` | saute l'écran titre |
| `--demo` | pilote automatique + tir continu (utile pour voir des projectiles) |
| `--novsync` | débride la présentation |
| `--no-backdrop` | désactive le fond (isoler son coût, cf. [howto-mesurer-la-perf](howto-mesurer-la-perf.md)) |
| `--capture --capture-after=N` | PNG après N images, puis quitte |
