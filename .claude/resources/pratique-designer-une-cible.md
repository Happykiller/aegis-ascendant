# Une consigne parlée n'est pas une désignation

**Origine** : 2026-09-07, phase finale du niveau 2. L'opérateur joue la phase entière sans une
erreur, la termine, puis dit : *« Ça fonctionne bien, mais visuellement, on ne sait pas de quoi
parle l'IA. »* Lyra disait « ne tirez pas sur les moteurs : coupez leurs ancrages » — et rien à
l'écran ne montrait lesquels.

## Trois défauts, et ils sont indépendants

### 1. La réplique tombait avant que la consigne ne soit vraie

`say(&"stern_seen")` était émis au **montage** de la poupe, c'est-à-dire à sa première apparition
dans le cadre — **onze secondes** avant que le vaisseau ne finisse de freiner et que les verrous
ne s'ouvrent. Pendant toute la réplique, les dix ancrages étaient **fermés, bleus et
invulnérables**. Le joueur entendait une consigne en regardant une carène où elle ne s'appliquait
pas encore, et l'avait oubliée quand elle devenait vraie.

⚠️ **Une réplique qui enseigne se dit à l'instant où le joueur peut agir**, pas à l'instant où la
pièce entre dans le champ. Le montage et l'ouverture sont deux évènements distincts ; il est
tentant de parler au premier, parce que c'est celui qui a un `signal`.

### 2. Un `PRIMITIVE_LINES` fait UN pixel, quelle que soit la distance

Les arcs électriques du nœud d'épine ont été portés sur les verrous : même motif, même
redessinage. Sur la capture, ils se lisaient comme des **rayures sur la coque**. La raison n'est
pas artistique : une primitive de lignes n'a pas d'épaisseur en mètres. Sur le nœud, la pièce
était proche et grosse ; sur le pont de poupe (**32,7 px/m**, contre 45,8 au corridor), il ne
restait qu'un trait d'un pixel.

⚠️ **Un effet qui doit être lu à une distance donnée se dessine en RUBAN**, orienté face à la
caméra — perpendiculaire = `direction.cross(VIEW_DIR)`, jamais un axe du monde : une largeur
portée par Y est écrasée par la plongée de 70°, une largeur portée par X disparaît sur les arcs
horizontaux. La constante de vue vaut `(0 ; −0,9403 ; −0,3403)` pour la caméra du jeu.

### 3. « Il se passe quelque chose ici » n'est pas « vise ICI »

Même épaissis, les arcs ne désignent pas : ils **animent**. Ce que l'opérateur demandait — mot
pour mot, « une illustration visuelle comme un indicateur » — est un **marqueur**, et un marqueur
obéit à des règles opposées à celles d'un effet de pièce :

| | l'effet (bandeau, arcs) | le marqueur (chevron) |
|---|---|---|
| profondeur | **testée** : il se fait masquer, il appartient à la pièce | **ignorée** : à moitié enfoui, il désignerait ce qui le cache |
| durée | permanent tant que l'état dure | **la durée de la réplique**, et pas une seconde de plus |
| cible | tout ce qui porte l'état | **seulement ce qu'on peut abattre** |

⚠️ **Ce qui autorise le marqueur à tricher sur la profondeur, c'est qu'il ne dure pas.** Un
marqueur permanent cesse d'être une explication pour devenir une interface — et ce jeu n'en a
aucune sur ses cibles. La fenêtre est bornée **haut** par un invariant de la Resource, pas
seulement bas.

⚠️ **Et il ne désigne que le vulnérable.** Marquer un verrou fermé apprendrait au joueur à tirer
sur une pièce invincible : le contresens exact que la réplique essayait d'éviter.

## Le piège de rendu qui coûte un cycle complet

Un `BILLBOARD_ENABLED` dont on a pris le sens de rotation à l'envers ne rend **rien** : ni erreur,
ni avertissement, ni test rouge. La capture revient simplement sans le marqueur, et l'on cherche
du côté de la visibilité, du culling de frustum, du timing. Poser `cull_mode = CULL_DISABLED` sur
tout panneau d'affichage bâti à la main. Cousin de
[pratique-geometries-invisibles](pratique-geometries-invisibles.md).

## Et une capture de debug n'est pas une capture

Le premier jugement s'est fait sur une image où six **cercles orange** entouraient les ancrages :
c'était `SolidsOverlay`, allumé **par défaut en build debug** (`debug_layers()` retombe sur
`OS.is_debug_build()`). Il rendait le rendu bien plus lisible qu'il ne l'est. ⚠️ **Juger un rendu
depuis un build debug demande `--hide-solids`** — sans quoi on valide un affichage que le joueur
ne verra jamais.
