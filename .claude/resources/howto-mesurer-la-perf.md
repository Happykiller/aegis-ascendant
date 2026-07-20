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
./scripts/deploy-win.sh -- ++ --novsync --goto-graybox --capture --capture-after=400
# -> [ScreenCapture] saved (0) — GPU 0.753 ms/frame
```

**Budget : 16,7 ms par image à 60 Hz.** (6,9 ms à 144 Hz.)

## Isoler le coût d'un effet : mesurer avec, puis sans

C'est la seule façon d'attribuer un coût. Exemple réel (nébuleuse en domain warping) :

| | GPU / image |
|---|---|
| `--no-backdrop` | 0,155 ms |
| avec le fond | 0,755 ms |
| **coût du fond** | **0,60 ms — 3,6 % du budget 60 Hz** |

Verdict : soutenable. Sans cette isolation, on n'aurait eu qu'un chiffre absolu ininterprétable.

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
