# Pratique — juger une image en la MESURANT, pas à l'œil

Le projet sait déjà qu'un asset non regardé n'est pas validé
([pratique-revue-asset](pratique-revue-asset.md)). Cette page dit l'étape d'après : **regarder ne
suffit pas non plus** dès qu'il s'agit de luminosité, de contraste ou d'exposition. L'œil s'adapte,
et deux captures vues l'une après l'autre paraissent toujours différentes.

## Le cas qui a coûté un aller-retour (22/07/2026)

Remarque de l'opérateur : « on manque de luminosité, les vaisseaux font sombre ».

Le diagnostic évident était l'éclairage — et il était **inscrit au backlog depuis deux jours**, avec
la bonne formule : « c'est l'éclairage de scène, pas les meshes ». Correctif appliqué (troisième
lumière ajoutée au combat, ambiante 0,55 → 0,80), capture avant/après, comparaison à l'œil :
« c'est mieux ».

**La mesure disait +5,7 %.** Autrement dit : rien. Le diagnostic était juste et n'expliquait
qu'un cinquième de l'écart. La vraie cause était ailleurs (ADR-0016) et n'aurait jamais été
cherchée si l'on s'était arrêté au « c'est mieux ».

## La procédure

Mesurer la luminance **sur la zone qui pose problème**, pas sur l'image entière — une moyenne
globale est dominée par le fond et ne bouge pas :

```python
from PIL import Image
import numpy as np

def lum(path, box=None):
    a = np.asarray(Image.open(path).convert('RGB'), dtype=np.float32) / 255.0
    if box:
        a = a[box[1]:box[3], box[0]:box[2]]   # (x0, y0, x1, y1)
    return 0.2126*a[...,0] + 0.7152*a[...,1] + 0.0722*a[...,2]

SUJET = (895, 780, 1035, 965)     # la coque du joueur
FOND  = (1500, 400, 1850, 700)    # nébuleuse pure, sans HUD ni vaisseau
for f in ("avant.png", "apres.png"):
    s, b = lum(f, SUJET).mean(), lum(f, FOND).mean()
    print("%-12s sujet=%.4f  fond=%.4f  contraste=%.1f" % (f, s, b, s/b))
```

Trois chiffres, trois questions différentes :

| Chiffre | Ce qu'il répond |
|---|---|
| luminance du **sujet** | « est-ce plus lumineux ? » — la question posée |
| luminance du **fond** | « ai-je éclairci le sujet, ou tout l'écran ? » |
| **rapport sujet/fond** | « la lisibilité en jeu a-t-elle survécu ? » — celui qu'on oublie |

Le rapport est le garde-fou. Sur ce cas il est tombé de 20,4 à 9,5 : décision prise en connaissance
de cause, et écrite dans l'ADR, au lieu d'être subie.

## Deux réflexes qui vont avec

- **Cadrer les deux captures à l'identique.** Le joueur ne bouge pas sans entrée : `--goto-graybox
  --capture-after=N` place le sujet au même pixel d'un lancement à l'autre, ce qui rend la boîte de
  mesure réutilisable telle quelle.
- **Inverser la chaîne pour trouver la cause.** Connaissant la formule du post-traitement, on
  remonte de la valeur à l'écran vers la valeur en sortie de rendu 3D. C'est ce calcul —
  `pre = (final - 0.5)/contrast + 0.5` — qui a montré que le fond perdait 90 % de sa luminance dans
  le shader, et désigné le coupable en une ligne au lieu d'une série d'essais.

⚠️ Corollaire, valable au-delà de ce cas : **un réglage nommé « contraste » n'ajoute du contraste
que si l'image occupe la plage autour de son pivot.** Sur une image entièrement sombre, un contraste
pivoté à 0,5 est un assombrisseur, et son nom ment.
