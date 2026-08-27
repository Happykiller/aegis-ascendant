# Pratique — quand le joueur et la mesure se contredisent, DESSINER avant de raisonner

## Ce que ça a coûté

Soirée du 2026-08-27 → 28, chambre du réacteur. L'opérateur : « je suis poussé sur la droite,
il y a quelque chose d'invisible qui m'empêche de bouger ». **Quatre diagnostics chiffrés se sont
succédé, chacun avec son banc, ses mesures et son correctif** — le couloir trop étroit (vrai, mais
insuffisant), le convoyage par le bout des arcs (vrai, mais pas la cause), les bornes du plan, le
carter du noyau. Chaque banc concluait que tout allait bien ; l'opérateur revenait avec le même
symptôme. Puis il a demandé : « fais apparaître la représentation des collisions pour qu'on voie ».
**Une capture** avec les formes de collision dessinées par-dessus l'image a montré les arcs verts
à 90 degrés des arcs violets : le décor tournait à l'envers de la collision (maillage en miroir +
pivot en négatif, deux fautes qui s'annulaient à l'instant zéro).

Aucun des quatre bancs ne pouvait le voir : **ils mesuraient tous la collision seule, qui était
juste en elle-même.** Le désaccord était entre deux représentations, et seule leur superposition
le montre.

## La règle

1. **Quand un joueur et une mesure se contredisent, c'est le joueur qui a raison** — et il faut
   instrumenter le JEU, pas raffiner le banc. Deux bancs d'affilée peuvent se tromper de la même
   façon.
2. **Dessiner les couches invisibles avant de raisonner dessus.** Le jeu a quatre représentations
   par objet — image, corps (`PlaneShapes`), cibles (`BulletTarget`), écrans de tir — et la
   plupart des « murs invisibles » sont un désaccord entre deux d'entre elles. `SolidsOverlay`
   les superpose ; il est allumé par défaut en build de développement, réglable dans le menu
   Options → Débogage. **Ne jamais diagnostiquer une collision sans une capture overlay.**
3. **Un banc qui recopie la boucle de collision ment.** Trois bancs ont recopié `_slide_to()` à la
   main, chacun d'une version différente. `tools/dive_bench.gd` pilote le VRAI
   `PlayerFighterController._slide_to()` — si le jeu a un défaut, le banc l'a aussi.
4. **Enregistrer la COMMANDE à côté de la position** (`--dive-trace`). Une trace de positions ne
   distingue pas « il va à droite » de « il est poussé à droite » ; avec la commande, c'est
   démontré sans interprétation. Et le mode `--demo` ne monte jamais vers le noyau : il ne
   rencontre aucun mur et ne prouve rien sur la collision.
5. **Isoler quand un symptôme survit à des correctifs** — « la méthode de la sphère indienne »
   de l'opérateur : retirer l'élément suspect (`--no-rings`) et voir si le symptôme part avec
   lui. Sans murs, le déplacement était propre → les murs étaient en cause, et l'asymétrie
   gauche/droite qu'on croyait voir n'était que des tapotements courts (accélération sur 0,18 s).
   Puis **rebâtir un élément à la fois**.

## Le piège de plomberie qui a fait passer un commit rouge

`./scripts/check.sh | grep … && git commit` prend le code de retour de **`grep`**, pas de la
porte : un commit est passé avec un test rouge (`edeb643`, amendé). Lire le code de retour de la
porte elle-même :

```bash
./scripts/check.sh > check.log 2>&1; CODE=$?; [ "$CODE" -eq 0 ] && git commit …
```
