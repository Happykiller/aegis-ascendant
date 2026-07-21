# ADR-0013 — Textures déverrouillées : jeux dédiés, relief, couleur

- **Statut** : accepté
- **Date** : 2026-07-21
- **Amende** : ADR-0011 §2 (« ce qui reste interdit »), ADR-0008 (interdiction des textures)
- **Contexte spec** : §24.4 (textures), §24.2 (modèles 3D)

## Contexte

ADR-0011 a entrouvert la porte : feuilles répétables **en niveaux de gris**, multipliées sur la
palette. C'était le bon premier pas — il a sorti le Specter-9 du « jouet ». Mais il laissait deux
interdits :

> *Ce qui reste interdit : les textures peintes à la main par vaisseau (atlas UV dédié) […] et les
> textures porteuses de couleur, qui contourneraient la palette.*

Ces deux verrous bloquent la reforge de l'Aegis Citadel. Le constat qui les met en défaut :

| Symptôme | Cause |
|---|---|
| La citadelle n'a **aucune** texture possible | son `.glb` n'a ni UV ni tangentes — `box_project_uv()` n'est appelé que par `build_specter_9.py` |
| Le noyau cristallin lit comme **une goutte blanche uniforme** | `AA_Emissive_Engine` est exclu du détail, et un émissif ne reçoit pas la lumière : ses facettes n'existent que si la géométrie les porte (`build_aegis_citadel.py:549-556`) |
| Une feuille unique pour six coques | elle est calée sur un chasseur de 2 m ; sur une forteresse de 19,6 m elle lit comme du bruit rayé |
| Aucun relief réel | une multiplication d'albedo peint des rainures, elle n'en creuse pas : la lumière ne les voit pas |

Le propriétaire du projet arbitre : **on ne veut plus d'interdit sur les textures.** Si un asset
image est nécessaire, on écrit le prompt correspondant et on le produit.

## Décision

**Les restrictions de texture d'ADR-0011 §2 et d'ADR-0008 sont levées.** Sont désormais autorisés :

1. **Les jeux de textures dédiés à une unité** — la citadelle peut avoir les siens, calés à son
   échelle, sans les partager.
2. **Le relief** : normal maps, roughness, ambient occlusion, height.
3. **La couleur** : une carte peut porter une teinte lorsque c'est motivé (cristal, décalques,
   marquages), et pas seulement multiplier un gris.
4. **Les décalques** : hachures de zone, numéros, bandes d'avertissement.

## Ce qui reste vrai — et n'est pas un interdit, mais un fait

Lever un verrou de projet ne change pas ce qu'un générateur d'images sait faire. Trois limites sont
**techniques** et gouvernent toujours la méthode :

| Limite | Conséquence de méthode |
|---|---|
| Un générateur d'images ne produit pas de **vraie normal map** — il peint une image violette *qui y ressemble*, aux gradients faux, donc à l'éclairage incohérent | on lui demande une **hauteur en niveaux de gris** ; la normale, la rugosité et l'AO sont **dérivées par `tools/derive-maps.py`**. Elles ne se génèrent jamais. |
| Il ne sait pas **peindre sur un layout UV imposé** | l'atlas peint par îlot reste hors de portée. On travaille en **feuilles répétables**, projetées en boîte — mais dédiées et à la bonne échelle. |
| Il ne produit pas de **vraie transparence** (il peint un damier) | déjà encodé dans `tools/bg-key-alpha.py`. |
| Le **tuilage sans couture** est souvent raté, même demandé explicitement | `derive-maps.py --check-tiling` colle l'image à elle-même et signale la couture avant intégration. |

## Ce qui ne change pas

- **La palette du kit reste la source de vérité des teintes.** Une carte qui *multiplie* ne l'altère
  pas ; une carte qui *remplace* une couleur doit être un **choix motivé et documenté**, jamais un
  effet de bord. Le jour où une coque ne ressemble plus à la charte, c'est un bug, pas un style.
- **Les sept matériaux** (`MATERIAL_ORDER`) et leurs noms : les scènes Godot s'y raccrochent.
- **Le script Python EST la source** de l'asset ; aucun `.blend` versionné (ADR-0008).
- **Déterminisme** : deux exports byte-identiques, auto-validation par `export_hull()`.
- **Provenance obligatoire** : toute texture a sa ligne dans `ASSET_PROVENANCE.csv`, source **et**
  dérivée (spec §24.7).
- **La règle du regard** (ADR-0006) : une texture n'est pas validée tant qu'elle n'a pas été
  appliquée, rendue et regardée **en jeu**, post-process rétro actif. Le rendu studio flatte.
- **Le coût est à mesurer**, pas à supposer : temps GPU par image, avant/après, aux deux endroits
  où la coque apparaît (accueil et combat).

## Conséquences

- **`tools/derive-maps.py`** devient une pièce obligatoire du pipeline : sans lui, la décision 2 se
  paierait en normal maps fausses.
- **Le skill `/asset-image`** (`.claude/skills/asset-image/`) est le point d'entrée : il rend un
  prompt autosuffisant, le nom du fichier, son chemin de dépôt et sa ligne de provenance. Il existe
  parce que le projet a déjà perdu des itérations à redécouvrir les mêmes pièges de génération.
- **`box_project_uv()` doit être appelé par tous les scripts de coque**, pas seulement le
  Specter-9. Une coque sans UV est une coque qu'aucune de ces décisions n'atteint.
- **`scripts/fx/hull_detail.gd`** ne sait poser qu'une carte partagée. Il devra accepter un jeu par
  unité, ou céder la place à un détail dédié pour les pièces qui le méritent.
- Le coût LFS n'est plus payé une fois pour toutes : un jeu dédié par unité se paie par unité.
  C'est le prix assumé de la décision — à surveiller si le nombre d'unités traitées grandit.
