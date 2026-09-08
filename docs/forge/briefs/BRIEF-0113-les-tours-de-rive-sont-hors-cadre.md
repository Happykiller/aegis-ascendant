# BRIEF-0113 — Les deux tours de rive sont hors cadre : leur trouver un siège que la caméra voit

- **Statut** : livré et intégré — voie C retenue (deux tours)
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-09-08
- **Suite de** : `BRIEF-0112` (livré, intégré, commit `b5f2aac`)

## Ce qui s'est passé

Le `BRIEF-0112` est bon. La tour est belle, la régénération est propre, les mesures sont justes,
le recouvrement est nul, le déterminisme tient. **`Tour 01` et `Tour 02` fonctionnent.**

`Tour 03` et `Tour 04` **ne sont pas dans l'image**.

## La mesure, et comment elle se refait

La poupe au repos est à `z = −hold_plane_y` en coordonnées monde. Ce n'est pas un calibrage :
le survol s'arrête à `LEAD_IN + station − hold`, le décor porte `parcouru − LEAD_IN`, et la poupe
est posée à `−station` dessus. Les trois termes se simplifient. `hold_plane_y = 6,47`.

En projetant par la caméra de `scenes/gameplay/cortege.tscn` — `Transform3D(1,0,0, 0,0.342,0.94,
0,−0.94,0.342, 0,14,5)`, `fov = 62` vertical, sortie 1920 × 1080 :

| Repère | Assise | Sommet | **Pied à l'écran** | **Sommet à l'écran** |
|---|---:|---:|---:|---:|
| `Tour 01/02` | −8,400 | −3,700 | 146 px | **13 px** |
| `Tour 03/04` | −4,600 | +0,100 | 37 px | **−142 px** ⛔ |

Le cadre va de 0 à 1080. **Le sommet des tours de rive est 142 pixels au-dessus du bord.** Seul un
liseré de 37 px de leur pied entre dans l'image — et il tombe derrière les panneaux `SCORE` et
`SHIELD` du HUD, qui descendent à ~230 px dans les coins.

Deux dérivations indépendantes donnent le même chiffre : un calcul à part, et le banc GDScript
gardé verbatim dans **`docs/forge/briefs/_BANC-CADRE-0113.gd.txt`**. Ce banc est le critère
d'acceptation de ce lot — il ne lit aucune constante : la caméra vient de la scène, l'arrêt de la
Resource, les repères et la hauteur des pièces des binaires.

## ⚠️ CE N'EST PAS UNE POSE NÉGLIGENTE, C'EST UN RENVERSEMENT

Votre raisonnement du `BRIEF-0112` était juste sur ses prémisses : la règle B autorise 8,60 m à
`|x| ≥ 16` parce que le plan de vol s'arrête à `|x| = 14`, et le seul créneau de plus de 3 m qui
reste sur l'étagère de rive est `z −8,60..−11,60`, à l'arrière du massif. Vous l'avez mesuré, et
c'est vrai.

**Mais la caméra s'arrête à `z = −5,69`** pour une pièce assise à −4,60. Le créneau libre et la
fenêtre visible ne se recouvrent pas.

> **La règle B achète de la hauteur derrière le cadre.** Sur cette poupe, elle ne paie rien.

Et c'est **mon omission autant que votre erreur** : mon brief donnait deux enveloppes — le plafond
de construction `−3,20` et le plan de vol — et pas la troisième, qui est le cadre. C'est la
deuxième fois après le `BRIEF-0109` qu'une pièce légale, bien faite et correctement mesurée n'est
regardée par personne.

## La troisième contrainte, écrite pour de bon

Une pièce n'existe que si la caméra la voit. Pour une assise `y` donnée, le `z` le plus lointain
qui garde le sommet dans l'image :

| Assise | Hauteur de la pièce | Sommet à 0 px (bord) | Sommet à 240 px (sous le HUD) |
|---:|---:|---:|---:|
| −8,40 (plateau du massif) | 4,70 | `z ≥ −10,38` | `z ≥ −2,59` |
| −4,60 (étagère de rive) | 4,70 | `z ≥ −5,69` | `z ≥ +0,43` |

⚠️ **PLUS UNE PIÈCE EST HAUTE EN `y`, PLUS ELLE SORT TÔT PAR LE HAUT.** C'est contre-intuitif et
c'est exactement ce qui a piégé le lot précédent : l'étagère de rive est 3,80 m plus haut que le
plateau du massif, donc sa fenêtre visible est 4,7 m plus **courte**. La hauteur d'assise que la
règle B rapporte, le cadre la reprend.

## Ce qu'il faut faire

**Trouver deux sièges visibles pour `Tour 03` et `Tour 04`.** Vous choisissez comment ; quatre
voies, et **la D est celle que l'opérateur a nommée** — commencez par elle :

### A. Les remettre sur le plateau du massif, à côté des deux qui marchent

`Tour 01/02` sont à `x = ±5,40`, `z = −9,90`, assise −8,40, et elles sont dans le cadre. Le
plateau a-t-il de l'empreinte à `x = ±9` ou `±11` à la même station ? C'est la voie la plus sûre :
elle réutilise une assise déjà prouvée, et la règle A y suffit (5,20 m de ciel pour 4,70 m de
pièce).

### B. Avancer l'étagère de rive

Il faudrait `z ≥ −5,69`, et vous avez mesuré que la rive est pleine de `z −7,11` à `+7,27` :
socles de pylône, flexibles de rebord, plates-formes volantes de la garnison. **Dites si une de
ces pièces peut reculer** plutôt que de renoncer — les flexibles de rebord sont du décor, les
plates-formes volantes appartiennent au code et je peux les déplacer si vous nommez la station.

### C. Deux tours au lieu de quatre

C'est une réponse recevable, et elle vaut mieux que deux pièces invisibles. Si A et B ne donnent
rien, **retirez `Tour 03/04` et les deux plateaux de rive**, et dites-le.

### D. Baisser l'assise, garder la station — **la voie que l'opérateur a nommée**

> « Il faut ajuster la hauteur pour qu'il soit visible correctement » (opérateur, 2026-09-08).

Lu comme une réduction de la **tour**, ça ne marche pas : à l'assise −4,60 elle ne pourrait faire
que **1,13 m**, ce qui n'est plus une tour d'échange mais un capot. Lu comme une baisse de
l'**assise**, ça marche — et c'est la voie la plus économe, puisqu'elle ne touche ni la station ni
l'empreinte, donc elle ne rouvre aucun recouvrement.

À `z = −10,10` inchangé, avec la tour de 4,70 m :

| Assise | Pied | Sommet | Verdict |
|---:|---:|---:|---|
| −4,60 (livrée) | 37 px | **−142 px** | hors cadre |
| −5,60 | 67 | −98 | hors cadre |
| −6,60 | 95 | −57 | hors cadre |
| −7,40 | 116 | −27 | hors cadre |
| **−8,17** | ~137 | **0** | limite exacte |
| **−8,40** | 141 | **+8** | dans le cadre |
| −9,40 | 164 | +40 | plus confortable |

⚠️ **L'assise doit descendre à `−8,17` ou plus bas** — 3,57 m sous l'étagère livrée, soit
l'altitude du plateau du massif (−8,40), celle qui fait déjà marcher `Tour 01/02`.

Deux vérifications, et ce sont les vôtres : la coque descend-elle jusque-là à `|x| ≈ 17,7`
(les étagères livrées sont à −6,60 / −5,60 / −4,60) ; et le recouvrement redescend avec le
plateau, donc à l'altitude des socles de pylône (−8,60) — mesurez-le.

⚠️ **LE CRITÈRE « SOMMET SOUS 240 px » NE S'APPLIQUE PAS AUX TOURS DE RIVE** : il demanderait une
assise à −17,86. Pour elles, le critère est **sommet ≥ 0**, comme `Tour 01/02` qui frôlent le bord
à +13 px et se lisent très bien.

⚠️ **ET CETTE FOIS, MESUREZ LE CADRE AVANT DE DESSINER.** Le rendu de contrôle ne suffit pas : une
planche studio « à la caméra du jeu » ne porte pas la station de la poupe, donc elle montre une
tour que le jeu ne montrera pas. Le seul verdict est la projection ci-dessus.

## Ce qui ne change pas

- **La tour elle-même est acceptée.** `stern_tower.glb`, 4,70 m, 8 388 triangles, ses 32 repères,
  ses trois clips : ne la retouchez pas. Ce lot ne déplace que des sièges.
- **`Tour 01/02` sont acceptées** à `x = ±5,40`, `z = −9,90`. Vous pouvez les avancer si le
  plateau le permet — leur sommet à 13 px frôle le bord — mais ce n'est pas demandé.
- **Aucun budget de triangles**, même décision qu'au `BRIEF-0112`.
- **Aucun `.gd`, `.tscn`, `.tres`.**

## Texture (ADR-0028) / Animation (ADR-0046 §6)

**Aucune, et c'est un refus motivé, pas un oubli.** Ce lot ne crée aucune géométrie : il déplace
ou retire des sièges déjà construits. Rien de neuf n'a de surface à habiller, donc rien ne se
peint — la carène garde ses matériaux par facteurs et `CortegeSkin` posera ses cartes dérivées
comme sur le reste. Même raison pour l'animation : les sièges sont figés, et les seuls clips en jeu
sont ceux de `stern_tower.glb`, que ce lot ne rouvre pas.

## Livrables

| Fichier | Description |
|---|---|
| `tools/blender/build_stern.py` | les sièges déplacés ou retirés |
| `assets/imported/models/backgrounds/stern_hull.glb` | la carène |
| `docs/forge/output/BRIEF-0113-report.md` | la voie retenue, et **le `y` écran du pied et du sommet de chaque tour** |
| `docs/forge/output/BRIEF-0113-planche.png` | avant/après au même cadrage |

## Critères d'acceptation

- [ ] **Le sommet de chaque `CTRL | Tour NN` tombe entre 0 et 1080 px** par la projection
      ci-dessus, et le rapport donne les quatre couples (pied, sommet) en pixels.
- [ ] Idéalement le sommet est **sous 240 px**, hors des panneaux de HUD des deux coins hauts.
- [ ] **Recouvrement mesuré à nouveau** — socles de pylône, repères `Liaison`, plates-formes
      volantes — en m³, par pièce.
- [ ] **La jonction `s = 500` et les trois canaux d'échappement sont intacts.**
- [ ] **Déterminisme** : trois exécutions, zéro octet divergent.
- [ ] **Rendu et REGARDÉ**, avant/après au même cadrage.
- [ ] Si la voie C est retenue : les deux plateaux de rive partent aussi, et le rapport le dit.

## Hors périmètre

- **Le modèle de tour**, ses clips, ses repères.
- **Le code de jeu** : je remonte le banc du cadre et je recâble ce qu'il faut.
- **Le corridor**, le complexe du tronçon 5, les nacelles, berceaux, verrous, bras, canaux.
