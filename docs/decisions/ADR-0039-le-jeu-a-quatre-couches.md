# ADR-0039 — Le jeu a quatre couches, et la troisième manquait

- **Statut** : accepté
- **Date** : 2026-08-29
- **Prime sur** : `docs/SPEC_AEGIS_ASCENDANT.md` §26 et §31, qui décrivent des règles de code sans
  décrire de couches
- **Suite de** : [`ADR-0038`](ADR-0038-le-jeu-est-une-campagne.md) (le jeu est une campagne)

## Le déclencheur

L'opérateur, après avoir joué le niveau 2 :

> « Je ne devrais pas avoir à signaler des bugs de gameplay qu'on a déjà couverts dans le
> niveau 1. […] On doit avoir le moteur, vraiment le gros moteur factorisé quelque part, puis
> les level design, puis les éléments — vaisseaux, décors — qui ont leurs caractéristiques, et
> grâce à ces caractéristiques et aux mécanismes du moteur, ça réagit. »

Il avait raison, et les symptômes étaient précis : le niveau 2 se jouait **sans voix, sans
explosions d'ennemi, sans écrasement au contact et sans zones de debug**. Quatre défauts, quatre
oublis, **aucun message d'erreur** — le niveau se jouait, il avait juste l'air pauvre.

## L'état réel, avant

Contrairement à l'impression que ces défauts donnaient, deux couches sur quatre existaient déjà
et étaient bonnes :

| Couche | État avant |
|---|---|
| **Données** — ce qu'est une chose | ✅ 21 Resources typées avec `validate()`. `EnemyData` porte 38 caractéristiques : méthode de tir (`SINGLE/NONE/FAN/AIMED/RADIAL`), cadence, projectile et ses dégâts, poids, rayon de touche, surface de contact, trajectoire (10 valeurs), mode de déplacement, effet non-projectile |
| **Moteur** — comment ça marche | ✅ ~30 modules réutilisables : `BulletManager`, `GameplayPlane`, `PlaneCollider`, `MassRules`, `HealthComponent`, `EnemyPath/Fire/Homing/Reaction`, `WaveSpawner`, `GravityWell` |
| **Runtime** — les lois d'une partie | ❌ **n'existait pas comme couche** |
| **Level design** — ce niveau-ci | ⚠️ mêlé au runtime dans `graybox_root.gd` |

Le défaut n'était donc **pas** l'absence de moteur. C'était une **frontière manquante** :
`graybox_root.gd` faisait 1 469 lignes et tenait trois choses à la fois — le runtime commun, le
level design du niveau 1, et deux boss en dur. Écrire un second niveau sans le copier (ce qui
était juste : ses 1 469 lignes ne sont pas celles d'un survol) revenait à **perdre le runtime
avec le reste**.

## La décision

Quatre couches, et une question unique pour ranger n'importe quoi :

```
DONNÉES        Resources typées                « qu'est-ce que c'est ? »
MOTEUR         modules purs, testables seuls   « comment ça marche ? »
RUNTIME        CombatRuntime, LevelRoot,       « qu'est-ce qui est vrai de TOUTE partie ? »
               BossStage
LEVEL DESIGN   graybox_root, cortege_root,     « qu'est-ce qui n'est vrai que d'ICI ? »
               Resources de contenu
```

> **La règle de partage** : *est-ce que le niveau 3 en aura besoin sans rien y changer ?*
> Si oui, c'est du runtime. Sinon, c'est du level design.

### `CombatRuntime` — les lois

Mourir (score + explosion + son + bonus), toucher, percuter, annoncer, parler — **et une
réplique a une voix**. Il tient aussi l'arrêt sur image et l'état musical, demandés par des
événements de combat.

⚠️ **Il adopte les unités par le GROUPE, pas source par source.** Le niveau 1 peuple deux
`WaveSpawner`, le niveau 2 un plus sept pools de ponts d'envol, le niveau 3 fera autre chose.
Brancher source par source, c'est se garantir qu'une sera oubliée — et une unité qui ne rapporte
rien, ne sonne pas et n'explose pas ne ressemble pas à un bug, elle ressemble à une unité.

### `LevelRoot` — le socle

Trouver les services, monter le runtime, brancher le HUD et le joueur, ouvrir la pause avec son
briefing, poser les calques de debug, afficher le rapport. Les deux niveaux en héritent ; les
deux méthodes que le socle appelle sans pouvoir les connaître — `phase_label()`, `dialogue()`,
`briefings()` — restent aux niveaux.

⚠️ **`setup_level()` s'appelle explicitement, ce n'est pas `_ready()`.** Un `super._ready()`
oublié ne se voit pas à la lecture ; une ligne manquante, si.

### `BossStage` — un boss se met en scène lui-même

`HarvesterStage` et `LeviathanStage` portent les 30 fonctions qui vivaient dans le script du
niveau 1. Les services sont **injectés**, jamais cherchés par chemin : c'est la recommandation
d'organisation de Godot, et c'est ce qui rend une scène de boss réutilisable ailleurs.

## Le résultat, chiffré

| Fichier | Avant | Après |
|---|---|---|
| `graybox_root.gd` | 1 469 | **846** |
| `cortege_root.gd` | 278 | **220** |
| `level_root.gd` | — | 189 |
| `combat_runtime.gd` | — | 256 |
| `boss_stage.gd` + les deux | — | 259 + 630 |

## Ce que la refonte a trouvé, et que rien d'autre n'aurait trouvé

- **Un boss devenu traversable.** En sortant `_bind_harvester`, la référence au module partait
  avec elle : `is_instance_valid(null)` rend faux, la boucle des obstacles ne versait plus le
  corps du boss. 753 assertions vertes. `BossStage.fill_solids()` porte désormais ce service,
  donc aucun appelant ne peut plus l'oublier.
- **Un ordre qui n'est pas le même pour les deux boss.** `show_boss()` ÉTEINT la rangée de
  pastilles ; `begin()` monte le module, qui les rallume. Le Leviathan a besoin du bandeau
  AVANT, le Harvester APRÈS. Un ordre unique aurait affiché quatre pastilles éteintes sur un
  boss intact, sans erreur. D'où un drapeau explicite.
- **Le tri des tronçons du niveau 2.** `Node.name` est un `StringName`, et `<` sur un
  `StringName` compare des **pointeurs**, pas des lettres : le tri rendait `[05, 04, 03, 01, 02]`
  et l'ordre changeait d'un lancement à l'autre. Trouvé **en jouant**, par l'opérateur : le
  journal annonçait « nœud d'épine 04 abattu » pendant qu'il survolait le premier tronçon.

## L'arc aussi est une donnée (ajouté le 2026-08-29, même session)

`LevelBeat` + `LevelArc` + `EncounterDirector`. L'arc du niveau 1 vit dans
`resources/levels/ossane_arc.tres` : **sept temps déclarés, dans l'ordre**, avec leurs
bannières, leurs répliques, leurs vagues et leurs boss.

⚠️ **Le directeur ne sait faire que deux choses tout seul** — une vague, un boss. Trois temps
sur sept en profitent ; les quatre autres sont déclarés `SCRIPTED` et rendus au niveau : le
puits qui monte, l'appontage de la Citadelle, la finale Helios, la victoire. **C'est délibéré.**
Prétendre mettre en données un survol de lune ou une séquence d'appontage aurait produit une
Resource à trente champs dont vingt-huit valent zéro — une façon compliquée d'écrire du code,
pas une donnée. Ce qui devient une donnée, c'est **l'ordre et l'identité des temps** ; le
sur-mesure reste du code, mais **à sa place dans l'arc**.

⚠️ **Les raccourcis `--skip-to-*` passent par l'arc** (`jump_to`), et posent le rang juste avant
le temps visé pour emprunter exactement le même chemin d'entrée qu'un enchaînement normal —
musique, bornes, décor, bannière. Un saut qui monterait le temps « à la main » finirait par
diverger, et l'on découvrirait avec un raccourci ce qui est cassé sans lui.

⚠️ **Deux crochets rendent la main au niveau, et chacun paie une dette précise** :
`should_skip_beat()` — sans lui, `--no-wave` laisserait l'arc bloqué sur un semeur qui ne se
videra jamais ; et `on_boss_defeated()` qui rend `true` — la finale Helios dure 1,8 s, et
enchaîner l'appontage par-dessus l'escamoterait.

⚠️ **Le niveau 2 n'a pas d'arc, et c'est un choix.** Le survol du Long Cortège est un seul temps
continu ; lui déclarer un arc d'un élément serait de la cérémonie, pas de la structure. Le socle
supporte les deux.

`graybox_root.gd` : **1 469 → 816 lignes.**

## Ce que cette décision coûte

- Une indirection de plus entre un événement et son effet. Assumé : elle est la contrepartie du
  fait qu'un effet ne peut plus être oublié.
- Deux noms pour la même chose le temps de la transition (`_bullets` / `_bullet_manager`),
  documenté sur place plutôt que corrigé dans le même mouvement — la recette du chantier est
  « le niveau 1 se joue à l'identique ».
- Une règle dure de plus dans `lint-regles.sh` : un script racine de niveau qui ne convoque pas
  `CombatRuntime` est refusé.
