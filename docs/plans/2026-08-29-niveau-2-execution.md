---
titre: Niveau 2 — Le Long Cortège, plan d'exécution complet
type: plan
auteur: concepteur principal
date: 2026-08-29
état: à appliquer — lots A à G
périmètre: architecture multi-niveaux, coque de forge, survol jouable, voix
supersède: `2026-08-29-niveau-2-le-survol.md`, dont les lots 0 et 1 sont livrés et repris ici
---


## Contexte

Le jeu contient **un seul niveau** (six phases, ~3 min, v0.3.0 publiée). L'opérateur demande le
**niveau 2 entier et jouable** : un survol continu d'un vaisseau ennemi de 6,8 km, de la proue vers
l'arrière, avec tourelles, ponts d'envol et une épine dorsale. Il s'absente ; le plan doit
s'exécuter sans lui, avec une vérification objective à chaque lot.

**Livrables attendus** : l'architecture multi-niveaux, la coque, le gameplay, les patterns, les
voix, les dialogues — et la liste des textures à générer, qu'il fournira au retour.

## Décisions actées

| Sujet | Décision |
|---|---|
| Phase ou niveau | **Un vrai niveau 2**, séparé, avec son propre rapport |
| Nom du vaisseau | **The Long Cortège** (lore écrit, `NULL_CHOIR.md`, `CAMPAGNE.md`) |
| 3ᵉ mécanique | **L'épine dorsale** — nœuds qui éteignent les tourelles du tronçon suivant |
| Ponts d'envol | Destructibles, **beaucoup de PV**, relâchent le **bestiaire existant** |
| Fin du niveau | **Ambry greffé au tiers arrière** — le dernier tiers reste pour le niveau 3 |
| Durée | **3 à 4 min** |
| Autonomie | **Tout sauf le push** |

## Ce que les trois planches apportent

Elles montrent **sept sections numérotées** (`SECTION 01/07`, `02/07`, `03/07`) et nomment les
phases : **PROW APPROACH**, **EARLY HULL**, **MID HULL**. Les deux tiers demandés = **sections 1
à 5**, la 5 portant Ambry.

Elles dessinent aussi, sans qu'on l'ait demandé :

- **l'épine dorsale**, comme une arête centrale lumineuse ponctuée de **bulbes** — nos nœuds ;
- les **baies hexagonales magenta** avec des vaisseaux dedans — nos ponts d'envol ;
- des **tourelles rondes à canons doubles**, de plus en plus massives d'une section à l'autre ;
- un **indicateur de progression** en bas à droite : la silhouette du vaisseau, remplie au fur et
  à mesure. C'est la meilleure idée des planches et elle ne coûte presque rien.

⚠️ Leur HUD montre `BOMBS` et `ENERGY`, qui **n'existent pas** dans le jeu (nous avons SHIELD,
POWER, FIGHTERS, SCORE). **Hors périmètre** : on ne crée pas deux systèmes pour une planche.

---

# LOT A — L'architecture de campagne

**C'est le seul lot qui touche à ce qui marche déjà. Sa recette : le niveau 1 se joue à
l'identique.**

L'état des lieux, vérifié : `GameState` n'a qu'un état `FIGHTER_COMBAT` ; `title_menu.gd:14` code
`graybox.tscn` en dur ; `mission_report._on_replay_pressed()` fait `reload_current_scene()` ;
`SceneRouter.goto_scene(path)` est déjà générique (le seul morceau réutilisable tel quel).

**À créer**

- `resources/data/level_data.gd` — Resource typée : `id`, `scene: PackedScene`, `display_name`,
  `briefings: BriefingBook`, `dialogue: DialogueScript`. Avec `validate()` (spec §31).
- `resources/campaign/campaign_book.tres` + `resources/data/campaign_book.gd` — la liste ordonnée.
  **Le niveau 1 y entre sans changer d'un octet.**
- Autoload `Campaign` (`scripts/core/campaign.gd`) : niveau courant, `next()`, `has_next()`.
  Progression persistée par `SettingsManager` (section `campaign`) — le mécanisme existe.

**À modifier**

- `mission_report.gd` — bouton **CONTINUER** quand `Campaign.has_next()`, REJOUER sinon et en
  défaite. Les constantes `_TITLE`/`_TAGLINE`/`_REPLAY_LABEL` sont déjà des dictionnaires par
  issue : y ajouter le cas.
- `title_menu.gd` — router vers `Campaign.current().scene` au lieu de la constante.

**Vérification** : `check.sh` vert **et** une partie complète du niveau 1, sans différence
perceptible autre que le bouton.

---

# LOT B — La coque (brief de forge)

**Le précédent structurel est `build_moon_flyby.py`**, pas une coque de vaisseau. Il **n'utilise
pas `ak.export_hull()`** et écrit pourquoi : le contrat impose un pivot centré à 2 cm et une bbox
largeur × longueur, « deux notions qui n'ont pas de sens pour un décor de 160 m ». Il refait
export et validation **localement, à l'identique sur le fond**. Le Cortège suivra ce chemin.

**Le précédent de découpe est `build_core_interior.py`** : 30 × 18 m, **douze nœuds racines
nommés et juxtaposés** (`Floor`, `Reactor`, `Catwalk_01..04`, `Rim_01..06`), sommets en
coordonnées absolues. C'est exactement la structure d'une coque en tronçons.

**Contrat proposé pour `BRIEF-0089`**

- Sortie : `assets/imported/models/backgrounds/long_cortege.glb`
- **Cinq tronçons**, nœuds racines `Section_01..05`, chacun **sans enfants** (le moteur lit leur
  translation pour placer le défilement), plus les marqueurs :
  - `Turret_NN` — points d'attache (Empties), tourelles instanciées en scènes séparées, comme
    `CitadelLife` le fait pour l'Aegis Citadel ;
  - `Bay_NN` — points d'attache des ponts d'envol ;
  - `Spine_NN` — les nœuds de l'épine dorsale ;
  - `Ambry` — sur la section 5.
- **Budget** : classe *structure* = 120 000 tri (ADR-0011). La Citadelle en consomme 62 884, le
  `core_interior` 19 414 pour 30 × 18 m (**36 tri/m²**, le rapport « grand décor » le plus bas du
  dépôt). Viser **≤ 90 000 pour les cinq sections**, budget par section au brief.
- **UV obligatoires**, `TEXCOORD_0` **compté** — le build doit **échouer** s'il en manque
  (`build_core_interior.py` et `build_moon_flyby._audit()` le font déjà). Trois coques du dépôt
  sont sorties sans UV, en silence.
- **Plafond `CEILING_Y = -3.0`** : rien de la coque ne monte dans le plan de jeu. Harnais
  bloquant, comme le survol de lune.
- **Déterminisme** : `./scripts/build-hull.sh --check long_cortege`, `-t 1` forcé.
- ⛔ **La forge ne livre AUCUNE texture** (ADR-0028) : géométrie et UV seulement.

---

# LOT C — Les textures à demander

⚠️ **Partage en trois mains (ADR-0028)** : l'opérateur génère les images, la forge livre la
géométrie, le concepteur rédige les `TEX-NNNN`, dérive les cartes et câble le matériau.

Le contrat est `docs/forge/textures/README.md` — un JSON par image, résolution ∈ {1024×1024,
1536×1024, 1024×1536} (**jamais 2048**), hauteur en niveaux de gris jamais de normal map,
`world_scale` **mesuré ou décidé**, et cyan `#3FD9E8` / corail `#FF5A3D` **toujours interdits**
(réservés aux tirs). Le skill `/asset-image` produit ces fichiers.

**Les demandes à écrire** (`docs/forge/textures/TEX-00NN-*.json`), déduites des planches :

| # | Sujet | Pourquoi |
|---|---|---|
| 1 | **Bordé de coque** — plaques hexagonales, rivets, joints | la surface dominante des trois planches |
| 2 | **Hauteur du bordé** (niveaux de gris) | pour dériver la normale et l'AO |
| 3 | **Panneaux d'usure / greffes** | les zones plus sombres et irrégulières |
| 4 | **Émissif d'épine dorsale** — l'arête lumineuse et ses bulbes | la mécanique doit se VOIR |
| 5 | **Émissif de baie** — l'intérieur magenta des ponts d'envol | idem |
| 6 | **Tourelle** — bordé + anneau | pièce vue de près, mérite sa carte |
| 7 | **Ambry greffé** — bordé humain, contraste avec le reste | la révélation du niveau |

La liste définitive et chiffrée (échelle monde par tuile, mesurée) sort **après** la livraison de
la géométrie : c'est la géométrie qui donne l'échelle, jamais l'inverse.

---

# LOT D — Le survol jouable

**Le mécanisme se copie de `MoonFlyby`**, en remplaçant la rotation par une **translation** :

- le décor **remplace le fond** — `_set_backdrop_hidden(true)` + le survol porte **son propre
  ciel** en `deep_sky` (le chemin qui saute cinq champs de bruit ; un uniforme à zéro
  n'économise rien) ;
- bascule sous le voile de `PhaseTransition`, jamais à découvert ;
- `reveal(false)` coupe `visible` **et** `set_process` ;
- fonction de défilement **statique et pure**, comme `MoonFlyby.drifted()`, donc testable sans
  arbre de scène ;
- `_silence_shadows()` sur tout le `.glb` — `directional_shadow_max_distance = 40`.

**Script racine propre au niveau** : `scripts/gameplay/cortege_root.gd`. Il **ne copie pas**
`graybox_root.gd` (1 470 lignes, ses boss en dur) : il réutilise `BulletManager`, `FighterHUD`,
`GameplayPlane`, `PlaneShapes`, `PhaseTransition`.

**L'indicateur de progression** (idée des planches) : la silhouette du Cortège avec la position
courante, dans un coin du HUD. Il porte aussi le numéro de section, qui donne au joueur la seule
information qu'un survol ne peut pas montrer — **combien il en reste**.

---

# LOT E — Les trois mécaniques

**Tourelles.** Le modèle est la tourelle-épine du Léviathan, pas `CitadelTurret` (décorative, ne
tire ni n'encaisse). Machine `READY → WINDUP → FIRING → RECOVER`, télégraphe obligatoire
(invariant n° 6 de `LeviathanTuning` : `windup ≥ beam × 0.5`), `Beam.hits()` pour les dégâts,
`BulletTarget` pour l'encaissement. ⚠️ Le `Beam` doit être `top_level = true` — sinon double
transformation et faisceau hors cadre, sans erreur au journal.

**Ponts d'envol.** ⚠️ **`WaveSpawner` ne sait pas ancrer un spawn à un objet mobile** : les
positions sont figées dans une `PackedVector2Array` au `_ready()`. Le point d'entrée qui existe est
`EnemyController.activate(position, seed)`, qui accepte n'importe quelle position. Le pont pilote
donc son propre pool et appelle `activate()` à sa position courante — pas de modification de
`WaveSpawner`, pas de régression sur le niveau 1.

**Épine dorsale.** ⚠️ **`GravityWell.speed_max_after(base, nodes_down, node_count)` est déjà
écrite pour « n nœuds abattus rendent 1/n »** — la fonction existe, testée, il n'y a qu'à s'en
servir pour le soulagement progressif.

**Réglages : une Resource typée avec ses invariants**, `resources/data/cortege_tuning.gd`, sur le
modèle des sept invariants de `LeviathanTuning`. Le premier est **non négociable** :

```
pv_pont ≤ dps_de_référence × temps_de_survol_du_pont × part_du_temps_où_l'on_peut_viser
```

Au-dessus, le pont est indestructible en pratique et le joueur croira mal jouer. C'est le défaut
qu'`ADR-0024` a payé sur le flux du Léviathan — dimensionné contre une cadence optimiste d'un
facteur 2,4, qu'aucun test ne voyait. La cadence de référence doit être **celle qui porte sur un
pont**, jamais celle mesurée sur une cible large.

---

# LOT F — Voix, dialogues, briefings

Tout le mécanisme existe et vient d'être exercé.

- **Cinq briefings de pause**, un par section (`SectorBriefing`, ≤ 3 objectifs) : la description
  dit *pourquoi on est là*, les objectifs *ce qu'on y fait*.
- **Répliques de Lyra** dans un nouveau `resources/dialogue/lyra_cortege.tres`, déclenchées par
  `_lyra(clé)` : entrée de section, première tourelle, premier pont, premier nœud abattu, et
  **Ambry** — la seule qui compte.
- **Demande de voix `VOX-0005`**, forgée par `tools/voice/forge_voice.py --cadence 1.0`
  (⚠️ la cadence n'était tracée nulle part et la chaîne n'est pas reproductible : déposer, puis
  mesurer, puis régler le `hold`).
- ⚠️ **Plafond de révélation** : le joueur ne doit rien apprendre de l'Unisson au-delà de « ils
  emportent des structures entières ». Ni Voix, ni Grille, ni commanditaires.
- ⚠️ **Lyra dit « Halyard »** (`ADR-0037`), et « Wren » **est déjà dépensé** au niveau 1 : la règle
  d'unicité est opposable, ce niveau ne l'emploie pas.

---

# LOT G — Rythme et équilibrage

Cinq sections en 3-4 min ≈ **40 à 48 s par section**. Densité croissante, à mesurer et non à
supposer (`ADR-0019`) : `/jouer` pour le ressenti, `balance-prober` pour la chronologie.

⚠️ **Risque de lisibilité** : un tronçon offre trois cibles concurrentes (tourelle, pont, nœud).
Si le survol devient illisible, **retirer le nœud du tronçon, pas le pont** — un pont se voit et
se comprend seul, un nœud demande qu'on ait compris le système.

⚠️ **Le budget se mesure sur la Quadro T1000**, jamais sur la RTX 4080 (×14 entre les deux).
Repères : survol de lune 0,323 ms (4080) ; fond complet 13,05 ms sur 16,67 (T1000). Et
`--novsync` détruit la comparabilité dès que la scène est vivante : mesurer à 60 Hz, trois tirs
alternés.

---

# Vérification, lot par lot

| Lot | Preuve exigée |
|---|---|
| A | `check.sh` vert **et** niveau 1 joué à l'identique |
| B | `.glb` livré, contrat vert, `--check` déterministe, **planche 4 vues regardée** (ADR-0006) |
| C | Les `TEX-*.json` valident les six règles du contrat |
| D | Le niveau se lance, défile de bout en bout, GPU mesuré sur T1000 |
| E | Une tourelle télégraphie, un pont tombe dans sa fenêtre, un nœud éteint son tronçon — chacun gardé par un test |
| F | Les répliques partent en jeu (`[Lyra] <clé>` au journal), `hold ≥ durée` mesurée |
| G | Une partie complète, chronologie relevée |

**À chaque lot** : `./scripts/check.sh` **ALL GREEN**, `./scripts/lint-regles.sh` OK, commit
conventionnel. **Aucun push.**

## Ce que ce plan ne fait pas

- Il n'ajoute **ni bombes ni jauge d'énergie** (présentes sur les planches, absentes du jeu).
- Il ne va **pas jusqu'à la poupe** : sections 6 et 7 réservées au niveau 3.
- Il ne **détruit pas** le Cortège — il continue sa route, et c'est ce qui doit rester de lui.
