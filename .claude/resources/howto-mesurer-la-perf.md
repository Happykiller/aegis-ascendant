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
