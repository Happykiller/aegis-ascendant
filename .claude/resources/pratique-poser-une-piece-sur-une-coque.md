# Poser une pièce sur une coque : trois choses que la cote ne dit pas

**Origine** : 2026-09-07, la garnison de la poupe du niveau 2. Quatorze tourelles placées à la
main sur une carène livrée. Trois défauts, trois causes distinctes, et **aucun ne se voit dans
la cote prise isolément**.

## 1. Une pièce n'est pas touchable là où elle se voit

`GameplayPlane.aim_point_of` projette la hitbox d'une pièce hors du plan de vol :

```
   t = -oeil.y / (piece.y - oeil.y)     plan_x = t * monde_x
```

⚠️ **`t` dépend de la HAUTEUR de la pièce.** Sur le pont de poupe (`y = −11,85`) il vaut 0,54 ;
sur un pylône (`y = −3,30`) il vaut 0,81. La **même** cote en `x` donne deux hitboxes distantes
de deux mètres et demi. Une tourelle posée trop au large est visible et **intouchable** ; posée
trop loin en profondeur, elle vise le joueur et **ne tire jamais** — et ce second défaut ne
produit ni erreur, ni test rouge, ni ligne de journal. En jouant, on conclut qu'elle est
« passive ».

Corollaire piégeux : les Resources de la poupe (`hold_plane_y`, `anchor_reach()`,
`anchor_rows()`) raisonnent en **monde 1:1**. C'est conservateur pour ce qui est sur le pont,
faux pour tout ce qu'on pose plus haut.

**La réponse** : une fonction pure qui projette chaque poste, et un banc qui les refuse.
`test_cortege_stern_garrison.gd` a rejeté deux placements avant toute capture.

## 2. Deux pièces disjointes sur la coque se chevauchent à l'écran

« On a beaucoup de chevauchement » (opérateur, capture à l'appui). Six légères alignées sur une
lèvre, **distantes de 3,4 m** — donc parfaitement disjointes en 3D — et **jointives une fois
projetées**, parce que la projection rapproche d'un facteur 0,54.

⚠️ **Le rayon projeté d'une pièce vaut son rayon d'assise fois SON facteur.** Deux pièces à des
hauteurs différentes ne se compriment pas pareil : prendre un facteur commun laisse passer
exactement les paires qui posent problème.

⚠️ Et un test d'écran seul ne suffit pas — deux pièces empilées à la verticale ont la même
projection. Il en faut **deux** : l'écart projeté, et l'écart dans le monde.

## 3. Une caméra qui plonge à 70° ne voit JAMAIS un dessous

Les plates-formes volantes portaient un liseré lumineux **sous** la dalle, pour dire « rien ne la
tient ». La capture n'en montrait pas un pixel : à 70° de plongée, la face inférieure d'une pièce
horizontale n'est jamais visible. C'est un effet qu'on paie et que personne ne verra.

⚠️ **Faire déborder plutôt que cacher.** Le même liseré, 16 % plus large que la dalle et glissé
juste dessous, dessine un contour lumineux tout autour de la silhouette — lisible de dessus,
et c'est lui qui fait flotter l'objet.

Même famille que [pratique-designer-une-cible](pratique-designer-une-cible.md) §2 : ce qui compte
n'est pas ce que la pièce EST, mais ce que la caméra du jeu en montre.

## 4. Ce qui se cache derrière une pièce mobile — le défaut le plus cher

Cinq pièces sur seize étaient **invisibles en jeu**, et aucune n'avait de cote fausse. La cause :
les trois groupes propulsifs font onze mètres de long et **se dressent entre la caméra et tout ce
qui est derrière eux**. Le massif arrière — la seule surface franche de la poupe, celle où
étaient posées les lourdes et deux moyennes — est masqué pendant **toute la phase**.

⚠️ **Un volume libre au sens de la géométrie n'est pas un volume VISIBLE.** L'emprise des
berceaux interdisait ce qui masquerait un verrou ; elle ne disait rien de ce qui serait masqué
PAR un moteur. La règle utile est plus forte et la contient : une pièce doit être **devant** la
face de poupe (`z >= 8`) ou **au large** des nacelles (`|x| >= 15,5`).

⚠️ Et le test qui gardait l'ancienne règle est devenu **vert et vide** le jour où la nouvelle a
été appliquée : plus aucune pièce dans l'emprise, donc plus une assertion exécutée. Le harnais
l'a signalé (cf. [pratique-un-test-vert-peut-etre-mort](pratique-un-test-vert-peut-etre-mort.md)).

## 5. Une pièce en veille se lit comme une épave

« Les canons ne tirent pas, ne bougent pas. » Une tourelle dormante dont on s'était contenté
d'**éteindre l'œil** est indiscernable d'une pièce détruite : le joueur lui tire dessus, rien ne
change, et il conclut à un bug.

⚠️ **La veille est un troisième état, et un état ne se distingue pas par une absence.** Elle passe
au **bleu froid** — la couleur que le niveau a déjà apprise au joueur sur les verrous d'ancrage,
où elle veut dire « pas encore celui-là » — avec un **battement lent** : une lueur fixe reste une
diode morte. Et le réveil **éclate**, parce qu'un palier d'escalade n'existe, pour le joueur, que
par cet instant-là.

## Et quand la coque n'a pas d'assise, on ne triche pas : on fait flotter

La carène de poupe n'a **aucune surface plane de plus de 1,40 m** hors de son massif arrière —
les étagères de rive font 0,40 à 1,20. Toute pièce moyenne (socle de 3,32 m) posée sur un gradin
flottait donc à moitié dans le vide, et se lisait comme un défaut d'intégration.

La sortie n'est pas de rétrécir la pièce ni de forcer la cote : c'est **la plate-forme volante**,
proposée par l'opérateur. Elle donne une assise franche à n'importe quelle hauteur, elle décolle
les pièces les unes des autres en profondeur — et elle ne ment plus, parce qu'elle flotte pour de
bon. ⚠️ Elle n'est dispensée d'**aucune** règle d'emprise pour autant : une dalle au-dessus d'un
berceau masque un verrou exactement comme un pylône.
