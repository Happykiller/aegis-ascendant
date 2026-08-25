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


## ⚠️ Une grande surface teintée ne peut pas être discrète ici

Mesuré le 2026-08-25 sur le champ du porteur de bouclier : trois essais de dôme — additif à 0,09
d'alpha, hémisphère à énergie divisée par dix, puis mélange normal **sans émission** à 0,11 — ont
rendu **le même aplat** magenta, recouvrant le porteur, les unités couvertes et les étoiles.

La cause n'est pas le réglage, c'est la **surface**, et deux étages du rendu la reprennent :

- le **bloom** du `WorldEnvironment` sature toute surface émissive un peu large ;
- surtout, le **`lift` de 1,25** du post-traitement rétro remonte les noirs — un violet à 11 %
  d'opacité en ressort vif.

Conséquence pratique : **ce qui doit rester discret doit être FIN**, pas transparent. Un cercle, un
liseré, un trait. Sur ce projet, baisser l'opacité d'une grande forme ne la rend pas discrète — ça
la rend seulement plus pâle une fois relevée par le lift, ce qui n'est pas la même chose.

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

## Deux captures, jamais une : la silhouette sur fond NOIR, la couleur sur le fond RÉEL

`--no-backdrop` n'est pas qu'un outil de perf. C'est **l'outil de lecture de la géométrie**, et
c'est le premier drapeau à sortir dès qu'on juge une forme, un point d'ancrage ou un alignement.

| Ce qu'on veut juger | Fond | Pourquoi |
|---|---|---|
| Silhouette, forme, **d'où part un effet**, ce qui traverse quoi | **`--no-backdrop`** | La nébuleuse est claire et bariolée ; une pièce claire dessus est illisible, et on valide des choses fausses |
| **Couleur**, contraste, lisibilité d'un télégraphe | **le fond réel** | Un signal se juge contre ce qui l'entoure. Sur fond noir, tout ressort — y compris ce qui disparaîtra en jeu |

**Ce que ça a coûté (23/08/2026)** — deux sessions, le même jour, chacune dans la mauvaise
configuration :

- Le boss final : ses lasers d'épines partaient **du vide**, et un correctif de braquage faisait
  **traverser le corps** aux épines. Trois captures sur fond de jeu n'avaient rien montré : cornes
  claires sur nébuleuse claire. **Une seule capture `--no-backdrop`** a rendu les deux défauts
  évidents en un coup d'œil.
- Les mines du bestiaire : leur signal d'engagement (émissif ×2,4) était **invisible en jeu** alors
  que la mesure disait qu'il montait. Cause : les pixels étaient déjà **écrêtés à 244-255**, et
  multiplier une valeur saturée est une opération nulle ; le fond magenta achevait de noyer une
  mine magenta. Là, il fallait le fond réel — sur fond noir, l'effet aurait paru parfait.

⚠️ **Et la grandeur à mesurer n'est pas toujours la luminance.** Sur un fond lumineux, ce qui se
voit est le **changement de teinte**. Mesurée sur les mines : luminance de la pièce engagée 236,6
contre 215-227 au repos — **dans la dispersion du repos**, donc rien. Écart rouge-vert sur les
mêmes pixels : 7,2 contre 26,8-53,2 — **aucun recouvrement**. Même image, même effet, une grandeur
qui ment et une qui tranche.

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

## Un cadrage se CALCULE : une fraction d'une hauteur ne dit rien de ce qu'on voit

Deux captures perdues le 2026-08-25, sur la même fonction de caméra, et aucune des deux erreurs
ne produit d'erreur, d'assertion ou de test rouge — seulement une image que personne ne regarde.

**1. Le cadrage posé en fraction.** `home.origin.y * 0.22` plaçait la caméra à **Y = 3,08** pour
une caméra d'origine à 14. La coque du boss fait **3,162 m** de haut : la caméra finissait
*dans* le boss, et la capture ne montrait qu'un amas de plaques.

La distance se déduit du **champ de vision**, pas d'un ratio :

```
distance = (taille_visee / 2) / tan(fov_vertical / 2)
```

À 62° verticaux, encadrer un puits de 4,378 m demande **3,64 m au minimum** ; se poser à 4,50 m
lui laisse 81 % de la hauteur d'écran et garde la lèvre visible autour. Et reculer le long de
l'axe **arrière de la caméra d'origine** (`home.basis.z`) plutôt qu'en dur : le cadrage suit si
la caméra est retouchée un jour.

**2. La transition glissée dans un monde masqué.** À la bascule vers l'arène intérieure, la
caméra revenait *en glissant* de la gueule du boss — une douzaine d'unités — vers l'origine où
l'arène est montée, en une demi-seconde. Or à cet instant le fond spatial et le corps du boss
sont **déjà masqués** : elle traversait du vide. Capture entièrement noire, HUD seul.

⚠️ **Un PNG de 15 Ko à 1920×1080 est presque uniforme.** La taille du fichier est le test le
moins cher qui soit : elle a signalé l'écran noir avant même l'ouverture de l'image.
