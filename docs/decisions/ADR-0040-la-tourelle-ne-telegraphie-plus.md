# ADR-0040 — Une tourelle de coque ne télégraphie plus, elle pivote lentement

- **Statut** : accepté
- **Date** : 2026-08-29
- **Prime sur** : l'invariant 3 de `resources/data/cortege_tuning.gd`, tel qu'écrit le matin même
- **Ne touche pas** : `LeviathanTuning` invariant 6, qui reste vrai pour un boss

## Le constat

L'opérateur, en jouant le niveau 2 :

> « Je ne vois pas les tourelles qui me tirent dessus. En handicap, elles auraient une rotation
> lente mais un tir continu. »

## Pourquoi le télégraphe ne marchait pas ici

Le premier modèle reprenait celui de la tourelle-épine du Pale Leviathan : `READY → WINDUP →
FIRING → RECOVER`, avec 0,8 s de préavis. Ce modèle est bon, et il reste en service **sur le
boss**.

Il ne transpose pas, pour une raison de cadrage et non de réglage :

| | Boss | Coque du Cortège |
|---|---|---|
| Nombre de pièces | 4 épines, au même endroit | **17 tourelles, sur deux flancs** |
| Où regarde le joueur | le boss — c'est le sujet | le décor défile, il esquive |
| Durée d'exposition | tout le combat | ~8 s par pièce, puis elle est passée |

Un préavis de 0,8 s sur une pièce qu'on n'a aucune raison de regarder n'annonce rien. Le joueur
prenait des dégâts sans savoir d'où.

## La décision

**Le faisceau est permanent, et la tourelle pivote lentement.**

- La menace est visible **tout le temps** : on sait en permanence quelles pièces sont vivantes
  et où elles pointent ;
- ce qui la rend jouable n'est plus le préavis mais la **lenteur** : 42 °/s, contre ~100 °/s
  pour un joueur qui contourne une tourelle à 8 unités ;
- un **canon visible** tourne avec le faisceau. Sans pièce mobile, un rayon sortant d'un décor
  immobile se lit comme un piège, pas comme une machine.

### L'invariant qui remplace le télégraphe

> **Une tourelle se distance.** `turret_turn_rate_deg` doit rester sous 60 % de la vitesse
> angulaire à laquelle un joueur à `max_speed` contourne une pièce à 8 unités.

⚠️ **La loi de la spec §11.2 ne change pas** : un tir qu'on ne peut pas éviter est une taxe, pas
une difficulté. Seule la façon de la tenir change — on annonce le coup sur un boss, on rend la
menace permanente et **semable** sur un décor.

⚠️ Et la morsure est **cadencée** (7 points toutes les 0,4 s), pas proportionnelle au temps :
verser `dps × delta` à chaque image ferait perdre presque tout dans les images gelées par un
arrêt sur image, et rendrait les dégâts dépendants de la cadence d'affichage.

## La décision jumelle : un pont d'envol se voit produire

Même session, même cause :

> « Aucune animation de pont d'envol, les ennemis apparaissent par magie. On pourrait imaginer
> la porte qui s'ouvre et on verrait décoller les ennemis de l'intérieur, hors ligne de vue ;
> il s'approche de la sortie puis décolle. »

Un pont qu'on abat pour **tarir sa production** doit d'abord se lire *comme* une production.
Une silhouette monte du fond du puits, franchit la bouche, et **c'est seulement là que la coque
entre en jeu** — 0,85 s pendant lesquelles le joueur voit d'où ça vient.

⚠️ **La silhouette est décorative, la coque est poolée.** `EnemyController` pose sa position en
coordonnées du plan de jeu, à hauteur nulle : il ne sait pas monter d'un puits creusé trois
mètres et demi plus bas. Lui apprendre aurait ajouté un état dans la classe la plus chaude du
jeu, pour une animation d'une seconde.

⚠️ Et elle est **sombre sur fond clair**, ce qui est l'inverse du premier essai : une silhouette
pâle se noyait dans le magenta du puits — vu en capture. Le fond d'une baie est ce qu'il y a de
plus lumineux sur toute la coque ; ce qui s'en détache est ce qui est sombre.

## Ce que ça coûte

- Dix-sept faisceaux permanents à l'écran au pire, contre quelques-uns par intermittence.
  Mesuré : le survol tient entre 0,62 et 2,1 ms par image sur RTX 4080 — mais **le budget se
  mesure sur la Quadro T1000**, et cette mesure reste au backlog.
- Un test de télégraphe remplacé par un test de vitesse de rotation, sur une **fonction pure** :
  une tourelle qui pivote trop vite colle au joueur quoi qu'il fasse, et ça ne se voit sur
  aucune capture.
