# Pratique — poser le détail en **fraction**, jamais en coordonnée absolue

Deux reforges de plan, deux fois le même dégât. C'est assez pour en faire une règle.

## Ce qui se passe

Un script de coque pose ses détails — bandeaux, marquages, greebles, liserés — à des **abscisses
absolues** : `add_box(bm, (0.42, -0.31, 0.05), ...)`. Ça marche, tant que la silhouette ne bouge pas.

Le jour où le plan change — flèche du bord d'attaque reculée de 12°, corde d'aile réduite — ces
coordonnées ne désignent plus rien. Sur BRIEF-0034, **quatre bandeaux sur sept se sont retrouvés hors
de la coque**, flottant dans le vide. Rien ne l'a signalé : le contrat d'`export_hull()` vérifie la
bounding box, le budget, les matériaux et les points d'attache — pas qu'un détail touche encore la
surface qu'il décore.

## La règle

Exprimer chaque détail **relativement à la géométrie qui le porte** :

```python
# ✗ fragile — ne survit pas au premier changement de plan
ak.add_box(bm, (0.42, -0.31, 0.05), (0.18, 0.06, 0.01), "AA_Trim")

# ✓ suit la coque
x = wing_span_at(y) * 0.62          # fraction de la demi-envergure a cette station
ak.add_box(bm, (x, y, deck_z(y) + 0.01), ...)
```

Les tables de profil (`HULL`, `ARM`, `CORE`…) existent déjà dans chaque script : elles sont la
source de vérité de la forme. Un détail qui ne les interroge pas est un détail qui mentira.

## Le cas vicieux : le détail qui casse une pièce mobile

Sur BRIEF-0034, un marquage doré hérité de la passe précédente s'est retrouvé **à cheval sur la
nouvelle charnière** d'un volet. Conséquence mesurée : le dégagement en rotation est tombé de 18,5°
à **2,8°** — très en dessous des 11° que le jeu applique. Le volet traversait donc la coque en
virage.

**Le contrat a validé cette version sans un mot**, parce que la bounding box **au repos** était
parfaite. Un défaut d'animation ne se voit pas sur une pose fixe.

Parade retenue : le script **remesure le débattement à chaque build** (`_flap_travel_limit()`), sur
le maillage réellement livré. Tout script qui produit une pièce mobile doit faire de même tant que
`ak.moving_part()` ne sait pas le vérifier lui-même.
