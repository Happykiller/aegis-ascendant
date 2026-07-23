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

## Les trois pièges qui coûtent une itération chacun

**0. Le PNG périmé — le plus vicieux, parce qu'il déguise les deux autres.** `capture.png` **reste
sur le disque** entre deux lancements. Si la capture ne s'arme pas (piège n°1) ou si le jeu quitte
avant l'image visée, le fichier de la fois d'avant est toujours là : on le lit, et on croit
regarder son propre changement. On peut ainsi « analyser » longuement un rendu qui date d'une autre
session — et en tirer des conclusions fausses sur du code qu'on vient d'écrire.

Deux réflexes, systématiques :

```bash
rm -f /mnt/c/tmp/aegis-ascendant/capture.png     # avant de lancer
./scripts/deploy-win.sh -- ++ … --capture | grep -i saved   # la ligne DOIT apparaître
```

Pas de ligne `[ScreenCapture] saved` = pas de capture. Ne rien lire, ne rien conclure.

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

**3. Le compteur se RÉARME à chaque chargement de scène.** La ligne `[ScreenCapture] armed: N
frames` apparaît une fois au démarrage, puis **une seconde fois** quand la scène de jeu se monte :
les images se comptent depuis le **dernier** montage, pas depuis le lancement. C'est ce qui rend
les captures d'événements chronométrés praticables — **sans `--novsync`**, une image vaut 1/60 s
depuis `[Level] ready`, donc un événement à *t* secondes se vise à `60 × t` :

```bash
# la 3e mort survient à 10,5 s de jeu, le rapport se lève 1,6 s après
./scripts/deploy-win.sh -- ++ --goto-graybox --defeat-demo --capture --capture-after=780
```

⚠️ Ne pas combiner ce calcul avec `--novsync` : la cadence n'est plus 60 Hz et l'arithmétique
s'effondre.

## Flags utiles

| Flag | Effet |
|---|---|
| `--goto-graybox` | saute l'écran titre |
| `--pause-demo` | ouvre le menu de pause à l'entrée du niveau |
| `--victory-demo` | saute droit au rapport de mission, score semé (sinon il faut jouer l'arc entier — c'est ainsi que cet écran a vécu longtemps avec la police par défaut sans que personne le voie) |
| `--demo` | pilote automatique + tir continu (utile pour voir des projectiles) |
| `--novsync` | débride la présentation |
| `--goto-codex` | ouvre le bestiaire ; `--codex-entry=N` choisit la coque |
| `--no-backdrop` | désactive le fond (isoler son coût, cf. [howto-mesurer-la-perf](howto-mesurer-la-perf.md)) |
| `--no-plumes` | désactive les plumes de réacteur (isoler leur coût, ADR-0017) |
| `--capture --capture-after=N` | PNG après N images, puis quitte |
