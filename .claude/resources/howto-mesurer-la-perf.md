# Howto — mesurer le coût d'un effet (et pourquoi le FPS ment)

## Le FPS d'un lancement automatisé est inexploitable

Quand la session Windows n'est pas activement affichée, le compositeur **bride la présentation**.
Les relevés deviennent absurdes et **non monotones** — mesuré le 12/07/2026 sur le même build :

| Configuration | FPS relevé |
|---|---|
| sans le fond (`--no-backdrop`) | **2 FPS** |
| avec la nébuleuse procédurale | **17 FPS** |

Un fond ne peut pas *accélérer* le jeu. Ces chiffres ne mesurent rien. Ne jamais conclure « c'est
lent » depuis un lancement non supervisé, et ne **jamais re-diagnostiquer le « 4 FPS » comme un
bug** — c'est le throttle, pas le moteur (perf réelle > 1000 FPS).

## La bonne métrique : le temps GPU par image

`RenderingServer.viewport_get_measured_render_time_gpu()` mesure le travail **sur le GPU**, ce qui
reste vrai que la fenêtre soit affichée ou non. Le helper de capture l'imprime :

```bash
./scripts/export-win.sh debug          # ⚠️ SANS CETTE LIGNE, ON MESURE LA FOIS D'AVANT
./scripts/deploy-win.sh -- ++ --novsync --goto-graybox --capture --capture-after=400
# -> [ScreenCapture] saved (0) — GPU 0.753 ms/frame
```

⚠️ **`deploy-win.sh` COPIE le build, il ne le reconstruit pas.** Il n'échoue pas si `build/` est
périmé : il déploie l'exécutable de la fois d'avant, le jeu démarre, la capture se sauve, le
chiffre GPU s'imprime — et **tout est faux sans qu'aucune erreur ne le dise**. Payé le
2026-08-25 : trois mesures d'un décor de survol prises sur un binaire antérieur à son écriture.
Le symptôme qui a sauvé la mesure était dans le JOURNAL, pas dans le chiffre — la ligne que le
nouveau code devait imprimer n'y était pas. **Faire imprimer au code neuf une ligne qui le
prouve, et l'exiger dans le log** : c'est le test d'exécutable périmé le moins cher.
`./scripts/play.sh`, lui, exporte si périmé — mais il pose le `++` et sert à JOUER, pas à mesurer.

**Budget : 16,7 ms par image à 60 Hz.** (6,9 ms à 144 Hz.)

## Une mesure unique ne vaut rien tant qu'on ne connaît pas sa dispersion

Le 2026-08-25, un témoin mesuré trois fois donnait **0,942 / 0,948 / 0,946 ms** — puis, un
tir isolé plus tôt, **1,535 ms**. Même build, même scène, même instant. Pris seul, ce
chiffre aurait fait conclure à une régression de 60 %.

**Trois tirs de chaque côté, alternés** : c'est le coût minimal d'un différentiel qu'on
publie. Si les deux séries se recouvrent, il n'y a pas d'effet à annoncer.

## ⚠️ Un uniforme à zéro n'économise rien

Un shader calcule ce qu'il calcule. Baisser un `uniform float strength` à 0,12 **atténue le
résultat** — les champs de bruit, eux, tournent en entier. Mesuré le 2026-08-25 sur le ciel
du survol de lune : la nébuleuse « éteinte » à 0,12 coûtait toujours **0,738 ms** ; un vrai
chemin (`uniform bool deep_sky` + `if` qui saute les cinq champs) l'a ramenée à **0,323 ms**.

Pour éteindre un poste de dépense, il faut un **branchement**, pas un facteur. Un
branchement sur uniform est cohérent sur toute la surface, donc quasi gratuit.

## Isoler le coût d'un effet : mesurer avec, puis sans

C'est la seule façon d'attribuer un coût. Exemple réel (nébuleuse en domain warping) :

| | GPU / image |
|---|---|
| `--no-backdrop` | 0,155 ms |
| avec le fond | 0,755 ms |
| **coût du fond** | **0,60 ms — 3,6 % du budget 60 Hz** |

Verdict : soutenable. Sans cette isolation, on n'aurait eu qu'un chiffre absolu ininterprétable.

## ⚠️ `--novsync` fausse un différentiel dès que la scène est vivante (26/08/2026)

L'exemple du haut de cette page mesure en `--novsync`, et c'est bon pour une scène **statique**. Dès
que le contenu évolue avec le temps de jeu — une vague qui fait apparaître ses unités selon une
timeline — `--novsync` **détruit la comparabilité**, et le piège est silencieux :

> `--capture-after` compte des **images**. À cadence libre, chaque configuration atteint l'image 480
> à un **temps de jeu différent** : la plus rapide y arrive plus tôt, donc avec **moins d'ennemis à
> l'écran**. On croit comparer un décor, on compare deux scènes.

L'effet joue dans le **mauvais sens** : la configuration la moins chère est mesurée sur une scène
plus vide, donc paraît encore moins chère. Le différentiel est gonflé par sa propre cause.

**La parade : mesurer à 60 Hz** (sans `--novsync`). Une image vaut alors 1/60 s depuis le montage de
la scène, l'image 480 vaut 8 s de jeu dans **toutes** les configurations, et une vague déterministe
y présente exactement les mêmes unités. Le temps GPU reste valide — il mesure le travail du GPU, pas
la présentation.

Appliqué au survol de lune, trois tirs alternés par configuration sur Quadro T1000 :

| Configuration | Plage |
|---|---|
| survol + textures | 5,28 – 5,94 ms |
| survol sans texture (`--no-surface-maps`) | 4,88 – 6,12 ms |
| fond spatial habituel (`--no-flyby`) | 12,59 – 14,24 ms |

Deux lectures, et **une seule est publiable** : les deux premières séries se **recouvrent
entièrement** — il n'y a pas d'effet à annoncer sur les textures, seulement un coût sous le plancher
de bruit. La troisième ne recouvre ni l'une ni l'autre : là, l'écart est réel.

⚠️ **Et la série la plus chère montait régulièrement** (12,59 → 13,53 → 14,24) : la dérive thermique
Max-Q décrite plus bas. Sa vraie valeur est vers le **bas** de sa plage — ce qui rend ici l'écart
plus net, mais l'inverse serait vrai si la série qui monte était celle qu'on veut voir gagner.

## Conséquence pour la Definition of Done

Un effet visuel n'est « terminé » que si son **coût GPU est mesuré et énoncé**, pas seulement
« ça a l'air de tourner ».

## Ne jamais conclure sur un seul relevé — mais le bruit n'a pas la même forme partout

**Règle** : lancer **au moins deux fois**, et regarder la **dispersion** avant de conclure. Un écart
isolé sur un build qui « ne devrait rien changer » n'est pas une régression tant qu'il n'est pas
reproduit. La *cause* du bruit, elle, dépend de la machine — ne pas appliquer mécaniquement une
recette prise sur un autre poste.

**RTX 4080 — caches Vulkan froids.** Le premier lancement après un `deploy` est surévalué, puis ça
se stabilise. Relevé le 12/07/2026, build inchangé :

| Run | GPU |
|---|---|
| 1ᵉʳ après deploy | **1,161 ms** ← artefact de cache froid |
| 2ᵉ … 5ᵉ | 0,836 / 0,840 / 0,840 / 0,863 ms |

Nominal ~0,838 ms. Garder le premier chiffre aurait fait chasser une régression de +0,38 ms
**qui n'existe pas**. Ici, « jeter le premier relevé » est la bonne recette.

**Quadro T1000 Max-Q — bruit apériodique, pas de cache froid.** Sur le poste portable, le 20/07/2026,
le 2ᵉ relevé est **plus haut** que le 1ᵉʳ : 11,404 / 12,450 / 11,458 / 12,724 / 13,266 ms. Pas de
décroissance, donc rien à « jeter » — c'est la modulation de fréquence d'un châssis Max-Q (contrainte
thermique et enveloppe de puissance). Sur ce type de machine, prendre **plusieurs relevés et retenir
la plage**, jamais un point : ici **11,4–13,3 ms**, soit ~1,9 ms d'amplitude sur un build strictement
identique. Une différence de cet ordre n'y signifie **rien**. À noter : les 5ᵉ et dernier relevés sont
les plus hauts — sur un portable, la dérive va plutôt vers le **réchauffement** que vers le cache froid,
donc une longue série de mesures monte au lieu de descendre.

## Un budget GPU n'existe pas sans sa machine

Un chiffre de perf n'est comparable qu'à un chiffre **du même poste**. Le même build, inchangé, rend :

| Machine | GPU / image |
|---|---|
| RTX 4080 (poste de référence de la spec) | ~0,84 ms |
| Quadro T1000 Max-Q (portable) | ~12,0 ms |

**×14 d'écart pour un code identique.** Toujours énoncer la machine avec le chiffre — sans quoi le
prochain relevé se lit comme un effondrement, et on part chasser une régression matérielle.
Corollaire : le budget 60 Hz (16,7 ms) est tenu sur le portable avec ~28 % de marge, mais le
**144 Hz (6,9 ms) y est hors d'atteinte** — ne pas y valider une cible de framerate haute.
