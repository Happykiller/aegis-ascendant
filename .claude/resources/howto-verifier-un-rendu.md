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

## ⚠️ `--capture-after` compte des IMAGES, pas des secondes

Et avec `--novsync`, une image ne dure pas 1/60ᵉ de seconde : le jeu tourne à plus de mille images
par seconde sur la RTX 4080. **`--capture-after=850` capture donc vers 0,85 s de jeu, pas vers
14 s.**

Coût, le 2026-08-28 : deux captures perdues à vouloir attraper la troisième réplique d'une bulle
qui en enchaîne quatre. Les deux images montraient la première réplique, à un caractère près — ce
qui *ressemblait* à une capture qui ne s'arme pas, alors que tout marchait.

Le repère : entre 260 et 850 images, la frappe du texte n'avait avancé que de 25 caractères. À
45 caractères par seconde, cela fait **0,55 seconde pour 590 images**. Si une capture semble figée
sur un instant très précoce, ce n'est pas la capture qui rate, c'est l'échelle.

Pour viser un instant tardif : soit multiplier par le rapport mesuré, soit **retirer `--novsync`**
et retrouver 60 images par seconde. Pour un écran statique (rapport, pause, codex), la question ne
se pose pas — 400 images suffisent toujours.

## ⚠️ Un pipe masque un lancement en arrière-plan

`./scripts/play.sh … | tail -40` lancé avec `run_in_background` **ne montre rien tant que le jeu
n'est pas fermé** : `tail` bufferise, donc le fichier de sortie reste vide et l'on croit que rien
ne démarre. Vécu le 2026-08-28, un lancement perdu à attendre une sortie qui existait déjà.

En arrière-plan, **ne pipe pas** : filtre à la lecture du fichier de sortie, pas à l'écriture.

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
| `--goto-graybox` | saute l'écran titre — ⚠️ **obligatoire devant tout `--skip-to-*`** (voir ci-dessous) |
| `--skip-to-field` / `--skip-to-boss` / `--skip-to-final` / `--skip-to-dock` | entre directement dans une phase du niveau |
| `--pause-demo` | ouvre le menu de pause à l'entrée du niveau |
| `--victory-demo` | saute droit au rapport de mission, score semé (sinon il faut jouer l'arc entier — c'est ainsi que cet écran a vécu longtemps avec la police par défaut sans que personne le voie) |
| `--demo` | pilote automatique + tir continu (utile pour voir des projectiles) |
| `--novsync` | débride la présentation |
| `--goto-codex` | ouvre le bestiaire ; `--codex-entry=N` choisit la coque |
| `--no-backdrop` | désactive le fond (isoler son coût, cf. [howto-mesurer-la-perf](howto-mesurer-la-perf.md)) |
| `--no-plumes` | désactive les plumes de réacteur (isoler leur coût, ADR-0017) |
| `--no-surface-maps` | le survol de lune garde sa géométrie mais perd ses textures (isoler leur coût, ADR-0028) |
| `--capture --capture-after=N` | PNG après N images, puis quitte |

## ⚠️ `--skip-to-*` seul ne quitte pas l'écran-titre

**Coûté le 2026-08-26** : un lancement complet — export, porte de qualité, déploiement — pour un
journal qui s'arrête à `[TitleStage] ready`. Aucune erreur, sortie en `code 0`, et pas une ligne
`[Level]`.

La cause est une **répartition de lecture**, et elle n'est écrite nulle part ailleurs :

| Drapeau | Lu par |
|---|---|
| `--goto-graybox` | `scripts/ui/title_menu.gd` — **l'écran-titre** |
| `--skip-to-field`, `--skip-to-boss`, `--skip-to-final`, `--skip-to-dock` | `scripts/gameplay/graybox_root.gd` — **le niveau** |

Un `--skip-to-*` seul demande donc à une scène **qui n'est pas chargée** de sauter une phase : le
jeu reste sagement au menu, et rien ne signale que le drapeau n'a trouvé personne pour le lire.
C'est le même silence que le `++` oublié, à un étage plus haut.

```bash
./scripts/play.sh -- --skip-to-field                  # ❌ reste à l'écran-titre
./scripts/play.sh -- --goto-graybox --skip-to-field   # ✅
```

**Le symptôme à guetter dans le journal** : `[TitleStage] ready` **sans** `[Level] ready` derrière.

## ⚠️ Mesurer la distance de l'OBJET, pas du décor derrière lui (26/08/2026)

**La leçon la plus chère de la session : cinq itérations sur un seul effet, et un brief de forge
entier bâti sur le chiffre faux.**

Un bolide tombe sur la lune. Pour dimensionner son rendu, j'ai calculé sa taille à l'écran depuis
la distance de **la lune** — son centre, à 96,5 unités. Or le bolide ne vit pas au centre de la
lune : il tombe sur sa **surface**, et le point d'impact est à **38,1 unités**, deux fois et demie
plus près.

| Point mesuré | Distance | Cadre visible | px/m | Un objet de 1,7 m |
|---|---|---|---|---|
| centre de la lune *(faux)* | 96,5 | 115,9 m | 4,66 | **7,9 px** |
| **point d'impact** *(juste)* | **38,1** | **45,8 m** | **11,78** | **20 px** |

**Ce que le faux chiffre a fait faire** : conclure que l'objet était trop petit pour porter une
silhouette, donc l'agrandir — il rendait alors un aplat de 36 px, « un gros cube jaune ». Et écrire
un brief demandant à la forge une recette de silhouette « pour 8 pixels », qu'elle a suivie
consciencieusement.

**La formule**, à appliquer au bon point :

```
px_par_metre = 540 / (2 × distance × tan(fov_vertical / 2))
```

⚠️ **540 et non 1080** : le rendu final passe par le post-process rétro. Et `fov = 62°` sur ce
projet — vérifier dans `graybox.tscn` plutôt que de le supposer.

⚠️ **Un décor lointain et ce qui vole devant lui ne sont pas à la même échelle d'écran.** L'erreur
ne produit ni exception ni test rouge : elle se voit en jeu, tard, et par quelqu'un d'autre.

## ⚠️ Juger une capture RÉDUITE pardonne exactement le défaut cherché

Deux itérations perdues le 26/08/2026 : un effet de traînée déclaré bon — « la différence est
franche » — sur des captures que j'avais **moi-même ramenées à 960 px** avant de les regarder.
L'opérateur a rendu la même scène en pleine résolution : un carton découpé, arêtes polygonales,
capuchon hexagonal, halo brun de bloom.

`ADR-0006` dit « rendu et regardé ». **Regarder une réduction n'est pas regarder le rendu** : c'est
regarder un flou qui pardonne, et il efface précisément ce qu'on cherche — un contour dur, une
facette, une couture, une saturation.

```bash
python3 tools/inspect-capture.py <capture.png> [--at X,Y] [--size 700x500] [--zoom N]
```

Il découpe **à l'échelle 1:1**, vise par défaut la zone la plus lumineuse (donc l'effet), agrandit
au **plus proche voisin** quand on le demande — les vrais pixels grossis, jamais des pixels
inventés — et rend le taux d'écrêtage. **Il ne sait pas redimensionner**, et c'est tout l'intérêt.

⚠️ La réduction reste permise pour **localiser** un sujet dans le cadre. Jamais pour **juger**.

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

## ⚠️ Le TÉMOIN : capturer un AUTRE sujet avant de théoriser (30/08/2026)

Une tache blanche-cyan est apparue au milieu de la fiche du Long Cortège, dans le bestiaire. J'ai
proposé **trois causes successives, toutes fausses**, chacune plausible et chacune coûtant un
cycle export + déploiement + capture :

1. un émissif de la coque — démenti en lisant le binaire : un seul émissif, magenta ;
2. la fusion des vingt-deux émissifs des pièces montées à l'échelle de la fiche — démenti en les
   baissant à 0,22 : la tache n'a pas bougé d'un pixel ;
3. le halo de l'environnement en mode écran — démenti par une capture `--no-glow` : la coque
   n'est translucide dans aucun des deux.

**La réponse est venue en trente secondes**, en capturant une **autre fiche** (`--codex-entry=0`,
le Specter-9) : elle portait la nébuleuse entière là où celle du Cortège était noire. Le fond
n'était pas un ciel mais un décor de proximité, et la caméra reculée pour une coque de 500 m le
réduisait à une tache au centre du cadre.

**La règle** : quand un artefact apparaît sur UN sujet, la première capture suivante doit être un
**autre sujet**, pas une hypothèse. Un témoin sépare en un coup « c'est cette pièce » de « c'est
l'écran ». Raisonner d'abord coûte un cycle par hypothèse, et les hypothèses plausibles sont
nombreuses.

⚠️ **Corollaire** : une correction posée sur une cause fausse ne devient pas inoffensive parce
qu'elle est verte. Les deux correctifs d'ombre écrits ici (étendre la portée, puis la couper) ont
été **retirés** — les garder aurait laissé dans le code deux garde-fous qui prétendent réparer ce
qu'ils n'ont jamais réparé, et le prochain lecteur aurait cherché ailleurs.

⚠️ **Et une correction d'échelle sur une composition dont on n'a pas lu TOUS les décalages
DÉPLACE le défaut au lieu de le fermer.** Trois corrections successives sur le même fond : réduit
à une tache → décor qui traverse la coque (repères `Landmarks` à z = +4, projetés devant le
vaisseau à l'échelle ×100) → décor posé devant elle. À chaque fois c'est l'opérateur qui l'a vu.
La sortie n'a pas été une quatrième formule mais un **changement d'approche** : ramener la pièce
au gabarit du présentoir plutôt qu'adapter le présentoir à la pièce.

## ⚠️ Un `grep` dans le tuyau avale une porte ROUGE (30/08/2026)

Écrit pour raccourcir la sortie :

```bash
./scripts/check.sh 2>&1 | grep -E "ALL GREEN|FAILED" | tail -2 && ./scripts/export-win.sh debug
```

Le code de retour d'un tuyau est celui de sa **dernière** commande. `check.sh` était **rouge**
(une erreur de compilation dans `codex_screen.gd`), `tail` a rendu 0, le `&&` a vu vert, l'export
a tourné **sur les sources précédentes** — et j'ai commenté la capture obtenue comme si elle
prouvait une correction. Elle était identique à la précédente **au MD5 près**.

**La règle** : ne jamais enchaîner une construction derrière une porte de qualité filtrée.

```bash
set -o pipefail                       # ou, plus sûr :
./scripts/check.sh > /tmp/chk.log 2>&1 || { echo "CHECK ROUGE"; tail -5 /tmp/chk.log; exit 1; }
```

Et **comparer les MD5** des captures successives : deux images identiques à l'octet près après un
changement de code signifient que le binaire n'a pas changé, pas que la correction est sans effet.
⚠️ L'inverse n'est pas vrai : une fiche de chasseur est **animée**, ses pixels diffèrent à chaque
capture — un MD5 différent ne prouve rien du tout. On compare les MD5 pour détecter l'IDENTIQUE,
jamais pour valider une différence.
