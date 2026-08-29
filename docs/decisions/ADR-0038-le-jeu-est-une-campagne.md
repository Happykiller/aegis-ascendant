# ADR-0038 — Le jeu est une campagne, et un survol n'est pas un niveau de plus

- **Statut** : accepté
- **Date** : 2026-08-29
- **Prime sur** : `docs/SPEC_AEGIS_ASCENDANT.md` §11 (« le niveau »), qui décrit un arc unique
- **Suite de** : [`ADR-0036`](ADR-0036-l-ennemi-s-appelle-l-unisson.md) (la bible),
  [`ADR-0027`](ADR-0027-le-champ-d-asteroides.md) (le fond cède la place)

## Le contexte

Le jeu n'avait qu'**un** niveau — six phases, une scène, un `graybox_root.gd` de 1 470 lignes
qui les enchaîne en dur. La bible narrative écrite par `ADR-0036` en prévoit **douze**, et
l'opérateur a demandé le deuxième entier et jouable : le survol du **Long Cortège**, un vaisseau
de 6,8 km longé de la proue jusqu'aux deux tiers.

Trois questions se posaient, et une seule avait une réponse évidente.

## Les décisions

### 1. Un niveau est une **donnée**, pas une scène codée en dur

`Campaign` (autoload) lit un `CampaignBook` de `LevelData` typées. L'écran-titre route vers
`Campaign.current().scene` ; le rapport de mission propose **CONTINUER** quand il y a une suite,
REJOUER sinon.

⚠️ **Le niveau 1 y entre sans changer d'un octet**, et c'est la recette qui a validé le
changement : une partie complète, rendue à l'identique jusqu'au libellé du bouton.

### 2. Un survol n'est **pas** un arc de phases, et ne réutilise donc pas son script

`cortege_root.gd` ne copie pas `graybox_root.gd`. Ce dernier précharge deux boss et pilote six
phases ; le niveau 2 n'a pas de phases, il a une **traversée** — c'est un autre jeu, donc un
autre script. Ce qui est GÉNÉRIQUE est réutilisé tel quel : `BulletManager`, `FighterHUD`,
`GameplayPlane`, `PhaseTransition`, `PickupManager`, `WaveSpawner`.

⚠️ **La conséquence est narrative avant d'être technique.** Un arc de phases raconte par ses
changements de situation ; un survol traverse un objet unique pendant trois minutes et demie et
**rien ne change à l'écran**. La progression du joueur est alors dans ce qu'il COMPREND — d'où
cinq briefings de pause et huit répliques, qui ne sont pas de l'habillage mais la structure
même du niveau.

### 3. Une cible de survol se dimensionne par sa **fenêtre**, jamais à la main

`CortegeTuning.validate()` tient six invariants. Le premier commande tous les autres :

> **Un survol ne revient jamais en arrière.** Chaque cible n'est tirable que pendant la fenêtre
> où elle est à l'écran. Des points de vie choisis au-dessus de cette fenêtre rendent la cible
> indestructible EN PRATIQUE — et le joueur ne le saura jamais, il croira mal jouer.

⚠️ **Mais la borne basse n'est pas la même pour tous**, et la première écriture s'est trompée en
leur appliquant la même règle. Un **pont** et un **nœud** sont des DÉCISIONS : sous 45 % de ce
qui est atteignable, ils tombent en passant et le choix de les viser n'existe plus. Une
**tourelle** est une cible d'OPPORTUNITÉ — il y en a dix-sept — et n'a besoin que d'un
PLAFOND : au-delà de 35 % de la fenêtre, s'occuper d'une seule empêche de faire autre chose et
le survol devient une file d'attente.

### 4. Le Cortège ne se détruit pas

Le niveau se **traverse**. C'est le premier adversaire du jeu que le joueur ne peut pas abattre,
et c'est ce qui doit rester de lui (`docs/lore/NULL_CHOIR.md`).

## Ce que la construction a appris, et qu'aucun plan n'avait prévu

### Les pièces sont **enfants** de leur marqueur

La forge a livré les marqueurs comme Empties enfants de leur tronçon. Chaque tourelle, chaque
pont, chaque nœud est donc ajouté SOUS son marqueur : le défilement les emmène tous, sans une
ligne d'arithmétique de position — donc sans aucune façon de désynchroniser une pièce de la
coupole qu'on voit. C'est ce qui a coûté le plus cher sur les épines du Léviathan.

⚠️ **Mais les coques lâchées par un pont ne sont PAS ses enfants.** `EnemyController` pose sa
position en LOCAL : sous un pont, une coque lâchée serait décalée de tout ce que le décor a
parcouru et dériverait un peu plus à chaque seconde.

### Une pièce **reçoit** sa position, elle ne la lit pas dans l'arbre

`tick(delta, world)`. C'est ce qui les rend pilotables sans scène, donc vérifiables — et il le
fallait : **une partie complète en démonstration (208 s) n'a détruit qu'UNE cible de coque**,
parce que le pilote automatique esquive et tire droit devant, il ne vise pas un bordé. Le
télégraphe d'une tourelle et la chaîne « un nœud éteint le tronçon suivant » ne se prouvent
qu'au banc.

### L'état d'une pièce ne peut pas être porté par la coque

Les coupoles, les puits et les bulbes sont CUITS dans le maillage de leur tronçon et partagent
leurs matériaux : éteindre un pont abattu éteindrait les sept. Chaque pièce porte donc son
propre volume — un œil, un couvercle hexagonal, un bulbe — et c'est lui, et lui seul, qui dit
vivant / touché / abattu.

### Le trou de vingt-sept secondes

Mesuré, pas ressenti : la proue de la coque livrée est nue sur 65 unités, et rien n'y est
tirable avant 30 s de jeu. **Aucun réglage ne le refermait** — cherché entre 2,4 et 2,9 u/s et
entre 8 et 22 unités d'entrée en scène, l'ouverture ne descend jamais sous 17,6 s. C'est un
problème de CONTENU, et sa réponse est une **réception de proue** au `WaveSpawner` ordinaire.

Le reste de la même mesure est ce qui a permis de ne rien toucher d'autre : pic de **trois**
cibles simultanées, 3,6 % du temps — le risque de lisibilité que le plan redoutait n'existe pas.

## Ce que cette décision coûte

- Deux scripts de niveau à maintenir au lieu d'un. Assumé : ils ne partagent aucun mécanisme.
- Le `FighterHUD` sert désormais deux niveaux aux besoins différents. La loi de non-chevauchement
  des panneaux, écrite pour Lyra seule, a dû être **généralisée** — et elle a immédiatement servi
  à trancher entre elle et la jauge de traversée.
- La chaîne de score passe par le groupe `enemies` et non par les sources : deux branchements
  séparés auraient fini par diverger, et la première divergence est un double comptage.
