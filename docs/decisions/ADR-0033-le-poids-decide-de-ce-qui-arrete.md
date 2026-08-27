# ADR-0033 — Le poids décide de ce qui arrête, et le reste est écrasé

- **Statut** : accepté
- **Date** : 2026-08-27
- **Contexte** : playtest de l'opérateur du 2026-08-27 (soir), phase `FIGHTER_WAVES`
- **Amende** : la loi « les corps ne se chevauchent pas » (`docs/KB/REGLES/lois.md`), posée le
  même jour, et `ADR-0032` qui lui a donné son moteur

## Contexte

Le chantier collision du 2026-08-27 a rendu les vaisseaux ennemis solides (lot 3) : deux corps ne
peuvent plus occuper le même endroit. C'était le but, et sur les murs, le réacteur et les coques de
boss, c'est exactement ce qu'il fallait.

Joué, le même changement a produit l'inverse de ce qu'il promettait sur les **vagues** :

> « pendant les vagues d'ennemis, ça devient injouable — si on ne les tue pas assez vite, en fait
> ils nous empêchent de bouger » — l'opérateur

## Le défaut

Ce n'est pas la collision qui est fausse : c'est la **règle** qui était trop courte. Elle disait
« deux corps » sans jamais dire **lesquels**, donc elle traitait un éclaireur de reconnaissance
comme un mur de réacteur. Un chasseur de combat arrêté net par une escorte légère n'est crédible
pour personne — et le remède qu'on attend d'un joueur (tirer plus vite) ne rattrape pas une
géométrie qui se referme.

Le manque est un mot : la **masse**. Deux corps de la même catégorie de poids s'arrêtent ; en
dessous d'un certain rapport, le plus lourd passe — et ce qu'il traverse ne survit pas.

## Décision

**1. Une masse dans la fiche d'identité.** `EnemyData.mass` et `PlayerStats.mass`, en tonnes
arbitraires. Le bestiaire livré : éclaireurs 0,9 à 1,3 ; intercepteur 1,6 ; porteur de bouclier
8,0 ; chasseur 10,0.

**2. Le contrat d'écrasement vit chez le chasseur**, pas sur les fiches d'en face :
`crush_mass_ratio` (3,0) dit de combien il faut être plus lourd pour passer, et
`crush_damage_per_mass` (8,0) ce que ça coûte. Un seul chiffre déplace la ligne pour toute la
faune, au lieu de treize `.tres` à rouvrir.

**3. Un module pur, [`MassRules`]**, qui répond à deux questions et rien d'autre : *est-ce que ça
écrase ?* et *combien ça coûte ?* Statique, sans nœud, testable à la main comme `PlaneCollider`.

**4. Un corps trop léger n'est pas un obstacle amoindri : il n'est PAS un obstacle.**
`WaveSpawner.fill_solids()` ne le verse plus dans les formes du niveau, et `crush_contacts()` le
détruit au contact de la capsule du chasseur. Les deux lisent le même test à la même image : une
unité ne peut jamais être à la fois un mur et une proie.

**5. Rien n'est traversé gratuitement.** L'écrasement passe par `take_contact_damage()`, donc par
la fenêtre d'invulnérabilité du chasseur : traverser une vague coûte du bouclier sans jamais la
vider en une image. Foncer dans le tas reste cher — sinon le tir deviendrait décoratif.

**6. La mort par écrasement est une mort normale.** `EnemyController.crush()` inflige des dégâts
létaux par le chemin habituel : `died` → `destroyed` → score et explosion. Une unité qui
disparaîtrait en silence ressemblerait à un bug de pop, pas à une collision.

## Ce que ça change du jeu

- Les vagues d'éclaireurs ne peuvent plus enfermer le joueur : elles se traversent, à un prix.
- Le **porteur de bouclier reste un corps** (8 t contre un seuil à 3,33) — c'est le seul ennemi qui
  arrête encore le chasseur, et ça sert son rôle de cible prioritaire. ⚠️ **Non jugé en partie** :
  si le playtest le trouve pénible, c'est un chiffre dans `shield_carrier.tres`, pas une décision à
  rouvrir.
- Murs, réacteur, décor et coques de boss sont inchangés : tout ce qui est versé dans un
  `PlaneShapes` est de masse infinie **par construction**, et le reste.

## Ce qu'on n'a pas fait

- **Pas de masse sur les formes.** Un champ de masse par forme aurait permis un décor destructible
  au contact ; rien ne le demande, et ça aurait ouvert la porte à des murs qu'on écrase par erreur.
- **Pas de transfert d'inertie.** Le chasseur n'est ni ralenti ni dévié par ce qu'il broie : ce
  serait une perte de contrôle de plus, et la plainte de départ était déjà une perte de contrôle.
- **Pas de masse pour les kamikazes.** Mine, sangsue et gueule ne sont pas `solid` : leur contact
  EST leur attaque, l'écrasement ne les concerne pas. Elles portent une masse par cohérence de
  fiche, elle ne décide de rien.
