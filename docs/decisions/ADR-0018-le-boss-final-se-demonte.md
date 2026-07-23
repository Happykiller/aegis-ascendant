# ADR-0018 — Le boss final se démonte ; sa coque passe à 11 × 14 m

- **Date** : 2026-07-23
- **Statut** : accepté (décision du propriétaire, cadrage de session)
- **Amende** : ADR-0008 §dimensions (ligne « Pale Leviathan »), réaffirmé par ADR-0011 §« ce qui ne change pas »
- **Complète** : ADR-0010 (le boss final se combat au chasseur)
- **Référence de conception** : `docs/design/BOSS_PALE_LEVIATHAN.md`

## Contexte

`scenes/bosses/pale_leviathan.tscn` est un `BossController` **nu** : 20 000 PV, `phase_count = 4`,
et rien d'autre. Ses quatre « phases » se déclenchent aux seuils de points de vie et ne changent que
la forme de trajectoire (`BossMovement.pattern_for_phase`) et le nombre de balles des trois motifs
génériques `RADIAL / AIMED_SPREAD / FAN`, qui cyclent toutes les deux secondes et gagnent 12 % de
cadence par phase (`scripts/bosses/boss_controller.gd:260-293`).

Le corps est **vulnérable en permanence**. Aucune sous-cible, aucun verrou, aucune condition. C'est
**cinq fois les points de vie du mini-boss sans sa mécanique** : un sac à points de vie, au moment
du jeu qui devait en être le climax.

Le Choir Harvester, lui, a une vraie boucle : trois appendices destructibles qui protègent le corps,
une fenêtre qui s'ouvre quand les trois sont à terre ensemble, une repousse qui referme tout — et un
dimensionnement dont l'existence de la fenêtre est **prouvée** par `HarvesterTuning.validate()`.

Le réflexe serait de rejouer cette boucle en plus gros : six appendices, deux iris. C'est
précisément ce qu'il ne faut pas faire. Le joueur a appris cette leçon vingt minutes plus tôt ; le
boss final ne serait plus qu'un contrôle de vitesse d'exécution.

## Décision

### 1. Le pilier — un démontage, pas un verrou

**Le Harvester est un verrou** (trois clés ouvrent une fenêtre, en boucle, tout repousse).
**Le Leviathan est un démontage** : chaque phase lui arrache une partie du corps, **rien ne
repousse**, et *la pièce arrachée à la phase N devient la mécanique de la phase N+1*.

La progression se lit sur la **silhouette**, pas sur une jauge. À la fin il ne reste qu'un noyau
décharné. Là où le Harvester récompense la vitesse d'enchaînement, le Leviathan récompense
l'endurance et le choix.

### 2. Quatre phases, quatre verbes

| Phase | Nom | Verbe | Mécanique |
|---|---|---|---|
| 1 | Armor Choir | BRISER | 4 plaques qui **orbitent** : la fenêtre naît d'une géométrie, pas d'un minuteur |
| 2 | Gravitic Maw | RÉSISTER | un **champ d'aspiration** tire le chasseur ; 3 nœuds le coupent par tiers |
| 3 | Boarding Swarm | PRIORISER | les 4 épines **se détachent** et deviennent des unités autonomes |
| 4 | Into the Maw | OSER | l'aspiration dépasse la vitesse du joueur : on **entre** dans la gueule |

Le détail — attaques, télégraphes, chiffres, invariants — vit dans
`docs/design/BOSS_PALE_LEVIATHAN.md`, qui est la référence de mise en œuvre. **Cet ADR acte la
décision ; il ne la répète pas.**

### 3. Les dimensions de la coque passent à 11,0 × 14,0 m

| | Avant | Après |
|---|---|---|
| Largeur (Godot X) | 7,02 m | **11,0 m** |
| Longueur (Godot Z) | 8,77 m | **14,0 m** |
| Hauteur max (Godot Y) | 2,50 m | **3,20 m** |

La ligne « Pale Leviathan » du tableau d'ADR-0008 §dimensions est amendée en conséquence.

**Pourquoi c'est nécessaire, et pas confortable.** Le plan de jeu fait 28 × 16 unités
(`GameplayPlane.BOUNDS`). À 8,77 m, le boss final était **à peine 25 % plus grand que le mini-boss**
(4,55 × 7,00) — il ne pouvait pas écraser l'écran, ce qui est la première chose qu'on attend de lui.
À 14 m il occupe la quasi-totalité de la profondeur utile.

**Pourquoi il fallait un ADR.** ADR-0011 a explicitement refusé de toucher à ce tableau :

> « **Dimensions X/Z imposées, tolérance ±3 %.** C'est le contrat de gameplay : hitbox, télégraphes
> et lisibilité en dépendent. ADR-0008 §dimensions reste normatif. »

Ce n'est donc pas un réglage : c'est une exception motivée, et elle ne vaut **que pour cette coque**.

### 4. Ce qui ne change pas

- **Le budget de triangles n'est pas en cause.** ADR-0011 l'a porté à **90 000** pour la classe
  *boss*, mesure GPU à l'appui. Le `tri_budget = 25_000` que déclare `build_pale_leviathan.py` n'est
  que le contrat que ce script s'impose ; le porter à 40 000 reste très en deçà du plafond et ne
  demande aucune décision — ADR-0011:110 réclame d'ailleurs cette relecture des contrats.
- Les sept matériaux et leur ordre, la palette Null Choir, le déterminisme, l'auto-validation par
  `ak.export_hull()`, le script Python comme source unique : inchangés (ADR-0008, ADR-0011).
- L'arc de niveau reste celui d'ADR-0010 : `FIGHTER_WAVES → MINI_BOSS → FINAL_BOSS → DOCKING →
  VICTORY`, le boss se combat au chasseur.

## Conséquences

- **La coque actuelle est inutilisable en l'état**, et pas seulement à cause de sa taille :
  `build_pale_leviathan.py` ne contient **aucun appel à `ak.moving_part()`** (0 occurrence, contre
  10 dans `build_choir_harvester.py`). Chaque pièce a son origine au centre du modèle et pivoterait
  autour du boss, pas autour de sa charnière. **Aucune des quatre phases n'est réalisable dessus.**
  C'est le défaut exact que BRIEF-0039 a corrigé sur le mini-boss.
- **Aucune texture ne peut s'y appliquer** : `ak.box_project_uv()` n'est appelé par aucun script de
  boss. Sans UV ni tangentes, le jeu de textures livré (11 images, commit `a23922b`) n'a nulle part
  où se poser. La reforge doit poser les deux dans le même geste.
- La reforge fait l'objet de **BRIEF-0040**.
- **Divergence relevée en passant, et non reconduite** : le tableau d'ADR-0008 donne au Leviathan une
  « hitbox de référence » de **3,6**, alors que `pale_leviathan.tscn` déclare `hitbox_radius = 2,7`.
  La valeur normative n'a jamais été appliquée. Avec la refonte, ce nombre change de sens — le corps
  n'est plus la cible qu'en phase 3-4, le reste du temps ce sont les sous-cibles qui portent le
  combat. La colonne « hitbox de référence » de cette ligne est donc **retirée du tableau** plutôt
  que mise à jour : elle sera fixée par `LeviathanTuning`, par phase, avec le reste des réglages.
- Coût GPU à surveiller : une coque de 14 m à 40 000 triangles avec une vingtaine de pièces mobiles
  est l'objet le plus lourd du jeu après la citadelle. À mesurer avec `godot-verifier` (temps GPU par
  image, jamais le FPS — cf. `.claude/resources/`).

## Alternatives écartées

- **Garder 7,02 × 8,77 et compenser par le nombre de pièces mobiles.** Écartée : la menace d'un boss
  final passe d'abord par l'occupation de l'écran ; on ne compense pas une silhouette absente.
- **Rejouer la boucle du Harvester en plus gros.** Écartée : c'est l'anticlimax décrit en contexte.
- **Rendre la taille variable selon la phase** (silhouette compacte puis envergure doublée). Écartée
  pour l'instant : séduisant, mais le contrat de dimensions devrait alors porter l'enveloppe
  déployée, ce qui rend la validation d'export ambiguë. Réexaminable après la reforge.
