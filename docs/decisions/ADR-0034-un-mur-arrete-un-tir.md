# ADR-0034 — Un mur arrête un tir, et la capsule ne dépasse pas la coque

- **Statut** : accepté
- **Date** : 2026-08-28
- **Contexte** : playtest de l'opérateur du 2026-08-28, overlay des collisions (`--show-solids`)
  allumé pour la première fois sur une partie entière
- **Amende** : `ADR-0032` (module de collision de plan) et `ADR-0033` (le poids décide), qui
  ont donné un corps aux vaisseaux sans jamais en donner un aux **tirs**

## Contexte

L'overlay des solides existe depuis le 2026-08-28 au matin. Sa première partie complète a produit
trois observations de l'opérateur, toutes justes, et toutes invisibles au journal :

> « la zone de collision du vaisseau est trop longue, surtout devant »
>
> « durant le boss final je voyais deux petits cercles que je suis pas arrivé à comprendre ce que
> c'est »
>
> « durant la plongée, on voit un cercle sur le mur qui bloque bien les tirs mais en dehors les
> tirs passent »

Aucune n'était un réglage : chacune nommait un défaut de modèle.

## Les trois défauts

**1. La capsule s'allongeait de son propre rayon.** `PlaneCollider.capsule_blocks()` promène un
disque de `body_radius` le long du segment `−body_half_length … +body_half_length` : l'étendue du
corps vaut donc `half_length + radius`. La demi-longueur mesurée sur `specter_9.glb` (1,23) avait
été versée dans `body_half_length` telle quelle. Le chasseur occupait 4,22 dans l'axe pour une
coque de 2,46 — **0,88 unité de coque fantôme devant le nez, et autant derrière**. Le garde de
`validate()` (« un vaisseau n'est pas plus large que long ») verrouillait l'erreur : il refusait
précisément la valeur correcte.

**2. Les balles n'étaient testées contre aucune géométrie.** Le blindage du Léviathan était simulé
par une `BulletTarget` unique de rayon 0,95, posée à chaque image sur le premier point où la ligne
*joueur → noyau* rencontrait du plein. Elle attrapait un disque de mur, et un seul. Pire, elle
était calculée sur une ligne que les bolts ne suivent pas : ils partent des canons, décalés
latéralement, et montent **droit** — et à partir du niveau de puissance 3, deux flux partent à
±16°, qui ne croisent jamais ce disque.

**3. Les missiles du boss n'existaient pas.** Trois par salve, 40 PV, 22 de dégâts au contact —
et rien, dans tout le dépôt, ne les dessinait. Les deux cercles que l'opérateur ne comprenait pas
étaient leur hitbox de debug, seule trace visible d'une attaque invisible. Instrumenté, le défaut
s'est révélé plus profond : le Léviathan tire depuis `y = 11,9` quand le plan s'arrête à 8,0, et la
règle « hors du plan, on retire » s'appliquait dès le premier pas. **Trois missiles armés, trois
missiles morts, à chaque salve, pendant tout le combat**, sans erreur ni trace.

## Décision

**1. `body_half_length` est une demi-longueur de SEGMENT, et le dit.** Valeur : `1,23 − 0,88 =
0,35`. La capsule épouse la boîte mesurée du `.glb`. `PlayerStats.body_reach()` porte désormais
l'étendue réelle, seule grandeur qu'un décor doive dégager, et le garde de `validate()` porte sur
elle. `test_the_collision_capsule_stays_inside_the_measured_hull` mesure la capsule contre les
bornes du `.glb`, mur juste devant et juste derrière.

**2. Un tir est arrêté par de la GÉOMÉTRIE, pas par une cible.** `BulletManager.screens` reçoit un
`PlaneShapes` à l'image, versé par le niveau depuis `LeviathanCombat.fire_screens()` — la plomberie
existait et personne ne la consommait. Chaque projectile confronte son **trajet**, pas seulement son
point d'arrivée : un tir rapide ne traverse pas un mur mince. Le signal `bullet_screened` porte le
point de contact, dont le niveau fait la gerbe et le son. La fausse cible, `SHIELD_CATCH_RADIUS` et
`shield_deflected` sont supprimés.

> **Corollaire, et il a déjà coûté une soirée** : ce qui arrête un CORPS et ce qui arrête un TIR
> sont deux couches distinctes. Un noyau peut être infranchissable sans faire écran au tir qui le
> vise. `fill_solids()` répond à la première question, `fire_screens()` à la seconde, et les
> mélanger a désactivé une phase entière.

**3. Une attaque doit se voir, et une fin doit s'entendre.** Les missiles ont un corps dont la
taille se **déduit de la hitbox** (la loi du projet : l'image et la collision lisent la même
donnée). Le signal `missile_ended(world_position, on_player)` distingue les deux issues — explosion
moyenne et secousse sur le chasseur, explosion légère sans secousse quand le joueur l'abat. Le
rappel de dégâts porte le **missile**, plus son rang dans un tableau que le compactage réordonne.

**4. On ne retire pas ce qui n'est jamais entré.** `TargetableProjectile` arme sa sortie de plan
seulement une fois entré, avec un délai de grâce qui borne l'attente. Élargir la marge aurait
déplacé le seuil ; le boss peut dériver plus haut, et le défaut serait revenu en silence.

## Conséquences

- **Le combat s'est mis à durer ce qu'il promettait.** Le réglage du noyau était calibré contre un
  joueur qui place ses dégâts — joueur qui n'existait pas tant que la fausse cible mangeait ses
  bolts. Réconciliés, `flux_health` est passé de 1600 à 2000 pour remettre le besoin par plongée au
  milieu de la bande autorisée (57 % → 71 %) au lieu de raser son plancher.
- **Coût mesuré, puis payé.** Le test d'écran a coûté 1,55 ms par image au banc (150 bolts, 9 % du
  budget 60 Hz). Une phase large — disque englobant et **trou central**, mesurés une fois par image
  — le ramène à 0,23 ms (1,4 %). Elle est conservatrice par construction : elle ne peut qu'écarter
  des balles qui n'auraient rien touché.
- **Vérifié en jeu, pas seulement en test** : 46 bolts arrêtés sur une plongée, à des rayons de
  6,3 à 7,2 du noyau et à quatre azimuts — la bande du mur, sur toute sa longueur.
- Le banc de plongée (`tools/dive_bench.gd`) perd ses événements « entraîné sans contact » sur cinq
  scénarios sur six : la capsule juste ne se fait plus pousser par une géométrie qu'elle ne touchait
  pas.

## Ce qu'on n'a pas fait

- **La gerbe du boss a le même défaut de naissance que les missiles.** `_fire_fans()` tire depuis
  `origin + 2,6`, soit jusqu'à `y ≈ 14,5`, au-dessus de la coupe des balles (13,0) : celles des
  plaques du haut meurent à l'image de leur création. Corriger demande de changer la règle de
  recyclage des 600 projectiles ; ce n'est pas le même chantier.
