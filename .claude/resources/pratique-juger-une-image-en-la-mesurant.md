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

## L'outil qui trouve la cause : la DIFFÉRENCE d'images

Mesurer dit *combien*. La différence dit *où*, et c'est elle qui désigne le coupable.

```python
a = np.asarray(Image.open("avant.png").convert('RGB'), dtype=np.float32)
b = np.asarray(Image.open("apres.png").convert('RGB'), dtype=np.float32)
# x4 : l'écart utile est souvent trop faible pour se voir sans amplification
Image.fromarray(np.clip(np.abs(b - a) * 4, 0, 255).astype(np.uint8)).save("diff.png")
```

L'image obtenue ne montre **que ce que le changement a ajouté** — le reste est noir. Cadrer les
deux captures à l'identique est donc la seule contrainte.

Cas réel (22/07/2026) : une atmosphère ajoutée en shader autour de la planète de fond. À l'œil,
« c'est mieux, mais il reste un liseré ». Impossible de dire si le liseré venait du shader ou de la
texture — elle en a un, peint dedans. La différence a tranché en une image : un anneau bleu de 2 à
3 px cerclait **tout** le disque, y compris le côté nuit, là où le fond était noir avant. Donc
entièrement dû au shader.

La cause, une fois qu'on savait où regarder, se lisait en une ligne : la couleur d'atmosphère était
peinte à pleine luminance dans la bande de transition du limbe, sans être modulée par le terme
« côté éclairé » — appliqué, lui, aux deux autres termes. **Le terme qu'on ne soupçonne pas est
celui qui n'a pas reçu la règle que les autres ont reçue.**

---

## L'échelle d'un motif se mesure aussi — et la mesure demande un témoin

La luminance n'est pas la seule propriété qu'on croit lire à l'œil. **L'échelle d'un motif de
texture** en est une autre, et l'œil s'y trompe autant.

**Ce que ça a coûté (23/07/2026)** : sur la paroi du puits du Pale Leviathan, j'ai jugé que les
anneaux étaient « deux fois trop fins » par rapport aux 80 cm demandés, et j'allais rejeter la
livraison. L'autocorrélation du profil moyen a rendu **0,82 m**. Je comptais les ornements *à
l'intérieur* de chaque anneau, pas les anneaux.

```python
h = np.asarray(Image.open(f).convert('L'), dtype=np.float32) / 255.
prof = h.mean(axis=1); prof -= prof.mean()          # axis=1 : période verticale
ac = np.correlate(prof, prof, 'full')[len(prof)-1:]; ac /= ac[0]
i = 1
while i < len(ac) and ac[i] > 0: i += 1             # sortir du pic central
periode_px = i + int(np.argmax(ac[i:i+len(prof)//2]))
```

⚠️ **Elle rend la période DOMINANTE, pas toujours celle qu'on cherche.** Sur une texture organisée
en grandes volutes, elle rend la volute (2,71 m) et pas le conduit qui la compose. Quand les deux
échelles coexistent, la mesure répond à côté — le dire, plutôt que de la présenter comme le calibre.

### La règle qui sauve : tout indicateur passe d'abord sur un témoin connu

Pour contourner le problème ci-dessus, j'ai écrit une mesure par **longueur de plage** (seuil à la
médiane, longueur médiane des plages claires). Passée sur les écailles, dont l'autocorrélation venait
de dire 0,99 m : elle a rendu **1 cm**. Elle comptait le grain de surface *à l'intérieur* de chaque
écaille.

Sans le témoin, ce « 3 cm » sur les greebles partait dans un compte-rendu comme un fait mesuré, et
justifiait un rejet. **Une mesure fausse est plus dangereuse qu'une absence de mesure** : elle porte
l'autorité du chiffre.

> Avant d'utiliser un indicateur maison, le passer sur une valeur **déjà connue par ailleurs**. S'il
> ne la retrouve pas, il est faux — le jeter, pas l'interpréter.

### Le cas particulier : une mesure que le correctif rend vide

`tools/derive-maps.py --fix-tiling N` force le raccord d'une tuile par fondu miroir. Après le fondu,
`--check-tiling` rend **0,0 %**, toujours, **par construction** — le correctif a réécrit les pixels
que la mesure compare.

Conclure « tuilage OK » sur ce zéro serait une tautologie. Le seul critère qui reste est la **planche
contact 2×2 regardée** : la bande miroir se voit, ou pas. C'est pour ça que l'outil imprime
« REGARDER le résultat » au lieu d'un verdict.
