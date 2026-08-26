---
titre: Une phase de jeu entre les deux boss — survol de lune et champ d'astéroïdes
date: 2026-08-25
auteur: session Claude (poste happykiller), sur demande de l'opérateur
perimetre: arc de jeu (graybox_root), vagues, fond spatial, assets 3D de décor
etat: lots 1 et 2 LIVRÉS ; lot 3 partiel (impacts livrés, assets à forger) ;
  lot 3-bis (textures) : T1 et T3 commandables immédiatement ;
  lot 4 à appliquer (constats de playtest consignés) ; lot 5 EN COURS (A + D)
supersede: rien. Complète docs/plans/2026-08-25-bestiaire-ennemis.md sur son point 3.1
---

# Une phase de jeu entre les deux boss

> **Rédigé le 2026-08-25** à partir de la demande de l'opérateur, et de l'état **mesuré** du
> moteur.
>
> ✅ **Lots 1 et 2 livrés le 2026-08-25**, et **la moitié du lot 3** : les impacts sur la
> lune sont là, seuls les assets de forge restent. Voir **`ADR-0027`**. Les trois décisions ouvertes en bas de page ont été **tranchées** par
> l'opérateur : oui pour l'ADR, **45-60 s** de durée, **astéroïdes solides / lune décor**.
> Les lots 2 à 4 restent entiers.

## Contexte — pourquoi ce chantier

Deux manques se rejoignent, et une seule phase les comble :

1. **Le bestiaire n'est jouable qu'au banc d'essai.** Choir Mine, Null Maw et Leech Drone sont
   livrés, testés, au codex — et n'apparaissent dans **aucune vague**. L'arc n'en a qu'une,
   `resources/encounters/wave_graybox_01.tres`, qui n'emploie que des Needle Scout et le
   Crescent Interceptor. (Point 3.1 du plan bestiaire.)
2. **Le P0 du backlog** dit la même chose depuis le début : « une seule vague de ~10 Needle
   Scouts puis mini-boss ; ajouter 1-2 vagues pour 2-3 min de jeu ».

Demande de l'opérateur, mot pour mot :

> « Créer une phase de jeu entre les deux boss avec les nouvelles unités ennemies, mais
> j'aimerais que le décor évolue, qu'on n'ait pas le même qu'avant le premier boss. En plus de
> l'aspect, intégrer des objets 3D dans le fond qui sont en mouvement, genre des astéroïdes
> qu'on survolerait, vraiment énormes, pour montrer la grandeur de l'espace. Sur toute cette
> phase entre les boss, on survolerait même une lune, avec ses cratères ; on pourrait assister
> même à des astéroïdes qui la percuteraient, faisant s'envoler des débris. Une belle scène. »

C'est donc **du contenu**, pas de la dette : la première fois depuis longtemps.

## Ce que le moteur permet déjà — relevé, pas supposé

> ⚠️ **Relevé du 2026-08-25 AVANT le lot 1.** Les deux premières lignes ne décrivent plus
> le code : `Phase` porte désormais `ASTEROID_FIELD`, et un second `WaveSpawner` endormi
> existe. Conservé tel quel — c'est l'état sur lequel la conception a été faite.

| Élément | État |
|---|---|
| Machine à phases | `enum Phase { FIGHTER_WAVES, MINI_BOSS, FINAL_BOSS, DOCKING, VICTORY }` dans `scripts/gameplay/graybox_root.gd:44`. Chaque phase a son `_start_*()` ; `_on_wave_cleared()` enchaîne sur `_start_mini_boss()` |
| Vagues | `WaveData` / `WaveEntry` (`resources/data/`) — timeline **data-driven**, déjà « la graine du futur EncounterDirector ». `WaveSpawner` préinstancie **tout son pool dans `_ready()`** |
| Unités | `EnemyController` + les 4 axes d'`ADR-0022` (`Path`, `Motion`, `Fire`, `Effect`). Les trois unités ont `.tres`, `.tscn`, coque et fiche codex |
| Fond | `scenes/vfx/space_backdrop.tscn` : un `MeshInstance3D` sous `space_background.gdshader`, plus **quatre `Sprite3D`** (`Planet`, `NebulaA`, `NebulaB`, `Galaxy`) pilotés par `BackdropLandmark` — dérive + rebouclage, zéro allocation par image |
| Musique | `MusicDirector` mappe un état **par `LevelPhase`** : une phase neuve demande son entrée |

⚠️ **`BackdropLandmark` est un `Sprite3D` billboardé, pas de la géométrie 3D.** Ce que demande
l'opérateur — des volumes qu'on survole, avec du relief et des impacts — sort de ce que ce
système sait faire. C'est une extension, pas un réglage.

## ⚠️ La contrainte n°1 : il reste ~4 ms de budget GPU

Mesures du 2026-08-25 sur le poste réel (**Quadro T1000**, pas la RTX 4080 de la spec) :

| Scène | GPU / image |
|---|---|
| Combat de boss, **fond complet** | **13,05 ms** puis 12,35 ms |
| Zoom de plongée | 9,25 ms |
| **Dans l'arène, fond masqué** | **2,73 ms** |
| Budget 60 FPS | **16,67 ms** |

Deux lectures, et elles commandent toute la conception :

- **Le fond est le poste de dépense dominant** — 13,05 contre 2,73 quand il est masqué.
- **Il reste moins de 4 ms.** Empiler une lune, des astéroïdes volumétriques et des débris
  **par-dessus** la nébuleuse actuelle ne tient pas.

### Décision structurante qui en découle : le décor **se remplace**, il ne s'ajoute pas

C'est aussi ce que l'opérateur demande (« qu'on n'ait pas le même qu'avant le premier boss ») :
pendant cette phase, la nébuleuse et ses quatre landmarks **cèdent la place** au survol de lune.
On échange un poste de dépense contre un autre au lieu de les additionner. Le mécanisme de
bascule existe déjà — `_show_core_interior()` masque le fond et le boss à l'entrée de l'arène
(`ADR-0025`) : même geste, autre décor.

## Les lots, dans l'ordre

### Lot 1 — La phase existe et se joue *(aucun asset requis)* — ✅ **LIVRÉ**

Le contenu avant la beauté : une phase jouable avec le décor actuel, pour valider le **rythme**
avant d'investir dans les assets.

- Nouvelle valeur `ASTEROID_FIELD` dans `Phase`, **entre `MINI_BOSS` et `FINAL_BOSS`**.
  ⚠️ `MusicContext.LevelPhase` **reflète `Phase` par valeur** — un test le garde
  (`test_music_director.gd:14`). Les deux enums se modifient ensemble, et le test le dira.
- `_start_asteroid_field()` sur le modèle de `_start_mini_boss()` ; `_on_mini_boss_defeated`
  y enchaîne au lieu d'aller au boss final.
- **Une seconde `WaveData`** : `resources/encounters/wave_asteroid_field_01.tres`, composée des
  trois unités livrées. Mines posées en barrage, Null Maw en zone interdite, Leech Drone en
  harcèlement.
- ⚠️ **`WaveSpawner` construit son pool dans `_ready()` depuis UNE `@export var wave`.** La
  spec §26.1 interdit tout `instantiate()` en jeu. Deux options, à trancher au code : un
  **second nœud `WaveSpawner`** endormi (le plus simple, pool préalloué à part), ou un spawner
  qui préalloue les deux vagues. Le second nœud est préférable — il ne touche pas à une classe
  qui marche.
- Son entrée dans `MusicDirector`.

**Vérifiable** : `./scripts/check.sh` vert, puis `./scripts/play.sh` — le journal doit montrer
`MINI_BOSS → ASTEROID_FIELD → FINAL_BOSS` et `[WaveSpawner] pool ready` **deux fois, au
montage seulement**. Une seconde occurrence en cours de vague serait une réallocation.

#### Ce qui a été fait, et les écarts au plan

| Point du plan | Livré |
|---|---|
| `ASTEROID_FIELD` entre `MINI_BOSS` et `FINAL_BOSS` | ✅ dans les **deux** enums, gardés alignés par `test_music_director.gd` |
| `_start_asteroid_field()` sur le modèle de `_start_mini_boss()` | ✅ + `_on_asteroid_field_cleared()` qui enchaîne sur le boss final |
| Seconde `WaveData` avec les trois unités | ✅ `resources/encounters/wave_asteroid_field_01.tres` — 36 unités, 20 entrées, dernier spawn à 40,1 s |
| Second `WaveSpawner` endormi | ✅ `@export var autostart` + `begin()`. La classe existante n'est qu'**étendue** |
| Entrée dans `MusicDirector` | ✅ **`FORTRESS_AWAKENING` réemployé** — écart au plan, qui ne disait pas lequel : ce lit était rendu et **orphelin** depuis qu'`ADR-0010` a supprimé la forteresse. Un test neuf refuse désormais qu'un cue rendu n'ait plus aucune phase pour l'atteindre |
| — | ➕ `--skip-to-field` ; `--no-wave` coupe les **deux** vagues et laisse l'arc passer, au lieu de bloquer sur une phase qui ne finit jamais |
| — | ➕ `tests/unit/test_asteroid_field_wave.gd` : la borne de durée est **calculée** depuis les vitesses réelles, pas affirmée en commentaire |

⚠️ **La durée réelle n'est pas le dernier spawn.** Les mines et les puits dérivent à 1,1 u/s
et mettent **17,3 s** à traverser le champ : la phase va de ~42 s (joueur qui nettoie tout) à
~54 s (joueur qui ne détruit rien). C'est ce trajet que le test borne.

### Lot 2 — Le décor bascule *(aucun asset non plus)* — ✅ **LIVRÉ**

- Un nœud `MoonFlyby` monté comme `CoreInterior` l'est : bâti au montage, caché, révélé à
  l'entrée de la phase, avec une **doublure procédurale** tant que les assets n'existent pas.
- Bascule : nébuleuse + landmarks masqués, survol montré. Rétabli à la sortie.
  ⚠️ Restaurer **l'état antérieur**, pas « visible » — `--no-backdrop` doit survivre à la
  phase, sinon une mesure de silhouette se ferait sur deux images incomparables (leçon
  d'`ADR-0025`).
- **Mesurer le GPU avec et sans**, à ce stade et pas plus tard : c'est le chiffre qui dira
  combien d'asset le lot 3 peut se payer.

#### Ce qui a été fait

`MoonFlyby` monte au **montage du niveau** (et non à l'entrée en phase comme
`CoreInterior` : une allocation de décor en pleine partie est ce que la spec §26.1
proscrit), avec doublure procédurale annoncée au journal. La bascule passe par un
`_set_backdrop_hidden()` **unique**, partagé avec la plongée du noyau — la précaution
`--no-backdrop` vivait en un exemplaire, elle n'a pas été recopiée. `--no-flyby` fournit
le témoin de mesure ; `--skip-to-field` sert l'aller.

**Mesure, sur ce poste (RTX 4080), t = 30 s, même scène :** survol **0,738 ms** contre
**0,938 ms** pour le fond habituel — **−0,200 ms, −21 %**. L'échange est gagnant.
⚠️ **Mais le poste qui contraint est la Quadro T1000**, celle des 13,05 ms ci-dessus. Le
signe se transpose, l'ampleur non : **refaire cette mesure au bureau avant d'engager le
lot 3**.

**Vérifié en capture, aller ET retour** : à t = 8 s et 30 s le survol est là (lune en bas
de cadre, deux rochers en parallaxe, ciel étoilé sans nébuleuse) ; à t = 64 s le boss final
se joue sous la **nébuleuse revenue**, sans résidu.

⚠️ **Trois défauts corrigés parce qu'on a REGARDÉ**, aucun n'aurait produit d'erreur : la
lune rendait rose pâle et noyait le chasseur (les lumières et le post-traitement réchauffent
tout gris neutre) ; les cratères flottaient au-dessus de la surface et se détachaient au
limbe ; un rocher frôlait le chasseur, ce qu'un décor sans collision ne doit pas promettre.
⚠️ Et **un quatrième que le test a trouvé avant le rendu** : le ciel du survol, posé à la
hauteur du fond habituel, aurait masqué tous ses propres rochers en silence.

### Lot 3 — Les assets *(forge)* — 🟢 **DÉBLOQUÉ le 2026-08-26 : impacts et textures livrés, géométrie à forger**

~~À n'engager **qu'une fois le budget GPU du lot 2 connu**.~~ → ✅ **Il l'est.**

> 🟢 **MESURÉ SUR QUADRO T1000 LE 2026-08-26, trois tirs alternés par configuration.** Le survol
> coûte **5,28–5,94 ms** par image contre **12,59–14,24 ms** pour le fond spatial qu'il remplace :
> il en coûte **moins de la moitié**, et l'économie est d'au moins **6,6 ms**, soit 40 % du budget
> 60 Hz. La garde de `BRIEF-0085` est **levée**, ses budgets de triangles sont confirmés — la phase
> garde la marge entière, pas la moitié qu'ils supposaient.
>
> ⚠️ **Et les textures ne coûtent rien de mesurable** : avec et sans se recouvrent entièrement
> (`--no-surface-maps`), la version texturée étant même plus rapide deux fois sur trois. Leur coût
> est sous le plancher de bruit de la machine — ce qui n'autorise pas à en empiler.

> ✅ **Les impacts sont faits** (voir `ADR-0027`) : trois bolides dorés percutent la lune à
> 11 s, 26 s et 40 s, avec flash et gerbe d'éclats. C'était du **code**, pas de l'asset —
> il n'y avait aucune raison de l'attendre. ⚠️ Ils n'empruntent PAS `VFXManager`, dimensionné
> pour le combat au premier plan : à trois fois cette distance, la même explosion serait un
> point.
>
> ⏳ **La lune et les astéroïdes attendent**, et la garde tient toujours : la mesure qui
> autorise leur budget doit être refaite **sur la Quadro T1000**. Ce qu'on sait aujourd'hui
> vient de la RTX 4080.
>
> 📄 **Le brief est écrit et prêt** : `BRIEF-0085-survol-de-lune-decor.md`, laissé au statut
> **brouillon** — il porte lui-même la garde, et ses budgets (12 000 triangles pour la
> calotte, 2 500 par rocher) sont **provisoires** tant que le bureau n'a pas mesuré. Il
> consigne la géométrie du lieu que le lot 2 a posée, le contrat de noms lu par le code, et
> les trois fautes que la doublure a rendues visibles : la teinte qui vire au rose sous les
> lumières du jeu, les cratères qui se détachent au limbe au lieu de creuser, et le corail
> qu'un décor ne doit jamais emprunter.
>
> 💡 **Et le budget a beaucoup changé depuis** : le ciel du survol est passé de 0,738 à
> **0,323 ms** en cessant de calculer une nébuleuse qu'il n'affiche pas (`deep_sky`). La
> phase 2 coûte désormais **un tiers** du fond spatial habituel. Il y a donc plus de marge
> pour les assets qu'au moment où ce plan a été écrit — reste à la mesurer là où elle
> compte.

> **Le lot 2 a posé la géométrie du lieu** : ciel à Y = −45, lune de rayon 60 centrée
> (0, −78, 34), rochers entre −13 et −34, plafond à −3. Les assets s'y substituent, ils ne
> la redéfinissent pas — et `test_moon_flyby.gd` tient les bornes.

- **La lune** — surface à cratères, occupant le bas ou le côté du cadre, dérivant lentement.
  Le sujet technique est le rapport **détail perçu / coût** : une sphère très subdivisée est
  hors budget ; une carte de hauteur sur une géométrie modeste ne l'est pas.
- **Les astéroïdes** — deux ou trois volumes, réutilisés à plusieurs échelles et rotations.
  Le « vraiment énorme » se joue par la **parallaxe et le cadrage**, pas par le nombre de
  triangles : un rocher proche qui traverse lentement dit mieux l'échelle que dix petits.
- **Les impacts** — un astéroïde percute la lune, des débris s'envolent. À traiter comme du
  **VFX scripté** sur des jalons de la phase, pas comme de la simulation : `VfxExplosion` et le
  pooling existent déjà.

⚠️ **Rappels de brief, tous payés cette session** : UV sur 100 % des primitives (trois coques du
dépôt en sont dépourvues), `ak.inset_panel()` corrigé en 1.1.0 mais son option `per_face`
est à choisir sciemment, et **toute planche de recette porte une vue avec le chasseur posé à
l'échelle** — la coque du boss livrait des « anneaux qu'on franchit » de 30 cm pour un chasseur
de 2,46 m, et rien ne l'avait signalé.

### Lot 3-bis — Les textures *(voie opérateur)* — 📋 **besoin exprimé le 2026-08-26**

> **Pourquoi cette section existe.** `BRIEF-0085` partage le travail en trois mains et écrit noir
> sur blanc, à la forge : « ⚠️ **PAS DE TEXTURES.** Ni peintes, ni générées, ni procédurales cuites
> dans le `.glb`. La matière de la surface vient de l'opérateur. » Cette voie-là n'avait **aucune
> expression de besoin** nulle part — ni brief, ni fiche, ni liste. La forge sait ce qu'elle doit
> livrer, le générateur d'images ne savait rien.

#### Le contrat d'interface

L'expression de besoin est un **JSON normalisé**, pas un prompt. Il sépare les contraintes
techniques de la description visuelle — c'est ce qui évite les demandes qui se contredisent
(« réaliste, tileable, en perspective, avec de la profondeur »). La chaîne est :

```text
Besoin du jeu  →  JSON normalisé  →  validation  →  prompt ImageGen  →  génération  →  derive-maps.py
                  (ce document)      (§ règles)     (skill /asset-image)
```

💡 **Le JSON est le contrat stable ; le prompt est jetable.** `/asset-image` sait déjà transformer un
besoin en prompt collable, avec nom de fichier, chemin de dépôt et commande de suite. Ce qui lui
manquait était l'**entrée** — c'est ce que ces blocs lui donnent. Le jour où la façon de rédiger un
prompt change, les blocs ci-dessous ne bougent pas.

#### ⚠️ Règles de validation propres à ce projet

Le schéma générique est bon ; il faut le **contraindre** avec ce que le dépôt a déjà payé. Un JSON
qui viole une de ces six règles ne part pas.

| # | Règle | Pourquoi — et ce que l'oubli a coûté |
|---|---|---|
| 1 | `resolution` ∈ **`1024x1024`**, `1536x1024`, `1024x1536` — **jamais 2048** | ⚠️ **Le schéma d'exemple dit `2048x2048` : ici ça donne un 1024 agrandi**, du détail inventé par l'interpolation. Ce sont les seuls formats natifs du générateur. Et le rendu final passe par le post-process rétro à **960×540** : une tuile de 1024 sur 5,5 m donne déjà 186 px/m. *Coût de l'oubli : dix blocs de prompt repris (23/07/2026)* |
| 2 | `output_usage: "source_for_normal"` ⇒ on demande une **hauteur en niveaux de gris** (clair = saillant), **jamais une normal map** | Un générateur rend une image violette **qui y ressemble**, aux gradients faux : le relief s'éclaire à l'envers et *ça a l'air correct*. `tools/derive-maps.py` dérive normale, rugosité et AO depuis la hauteur |
| 3 | `transparent_background: true` **interdit** | On reçoit un **damier peint** dans une image RGB opaque (BRIEF-0028). On demande `pure_black` ou `pure_white`, puis `tools/bg-key-alpha.py` |
| 4 | `tileable: true` se **mesure**, ne se croit pas | Un « seamless » demandé n'est pas un seamless obtenu — invisible en preview, évident en jeu. `derive-maps.py --check-tiling` doit dire OK |
| 5 | `color_palette.forbidden` contient **toujours** le cyan (`#3FD9E8`) et le corail (`#FF5A3D`) | Réservés au tir allié et au tir ennemi (`space_background.gdshader`, DA §6, bible [Lisibilité](../design/bible/01-lisibilite.md)). Un décor qui les emploie **vole leur lisibilité aux projectiles**. Cette règle a déjà coûté une itération sur le bolide d'impact (`ADR-0027`) |
| 6 | `world_scale` est **réel ou déclaré inconnu** — jamais plausible | Une échelle inventée cadre la densité de détail sur du vide. Une feuille calée sur un chasseur de 2 m lit comme du bruit sur une forteresse de 20 m : c'est le défaut n°1 du projet |

⚠️ **Deux notes qui ne sont pas des règles mais des limites.** Le `color_mode: grayscale` n'est pas
un dogme : `ADR-0013 §3` autorise la couleur **quand elle est motivée**, et `derive-maps.py`
*avertit* seulement si l'image reçue est colorée. Et une génération d'image ne garantit **aucune
propriété numérique stricte** — ni normale physiquement correcte, ni profondeur métrique, ni absence
de couture au pixel : c'est la validation en aval qui les établit, jamais le prompt.

#### ✅ Ce qui NE bloque pas — correction du 2026-08-26

> ⚠️ **Une première version de cette section déclarait le besoin bloqué sur la densité de texels de
> `BRIEF-0085`. C'était faux, et la vérification l'a montré.**

**L'échelle monde d'une tuile n'appartient pas à la forge : elle se pose à l'intégration.** Le dépôt
le fait déjà deux fois — `hull_detail.gd:85` et `citadel_detail.gd:67` appliquent un `uv1_scale` sur
le matériau importé. C'est le concepteur qui choisit combien de mètres couvre une tuile, pas le
`.glb`.

Ce que le rapport de la forge closura est donc **plus étroit** que je ne l'avais écrit : il dit si le
dépliage est **homogène** (pas d'étirement sur les flancs de cratères), pas quelle taille fait la
tuile. Une texture générée à la mauvaise échelle **se rattrape par un chiffre** ; une texture posée
sur des UV qui s'étirent est à refaire.

**Conséquence pratique : T1 et T3 peuvent être générées MAINTENANT**, en parallèle du reste du plan.
`world_scale` porte une valeur **décidée**, pas mesurée — et elle est marquée comme telle.

#### ✅ T2 et T4 sont probablement inutiles — `derive-maps.py --mul`

Seconde correction, du même coup de vérification. Le contraste d'albédo qui doit **dessiner les
cratères là où aucune ombre ne les dessine** n'a pas besoin d'une seconde génération : `--mul`
produit une **carte de multiplication** dérivée de la hauteur, où les creux valent moins de 1,0 et
les surfaces neutres 1,0. C'est exactement le mécanisme d'`ADR-0011` sur les coques :

> `hull_detail.gd` — « Godot calcule `albedo = albedo_texture × albedo_color`. En posant la carte
> comme `albedo_texture` et en GARDANT la couleur de palette importée du `.glb`, les plaques
> conservent exactement leur teinte et seules les rainures se creusent. »

Appliqué à la lune : la teinte froide et sombre reste celle du matériau, et les cratères
**s'assombrissent d'eux-mêmes**, pilotés par la même hauteur qui les creuse. `--mul-floor` règle la
noirceur maximale des creux (défaut 0,55).

⚠️ **Ce que `--mul` ne fait PAS** : les **ejectas clairs** rayonnant autour des impacts récents. Ils
sont plus clairs que la surface, donc au-dessus de 1,0 — une carte de multiplication ne peut pas les
produire. Si la capture montre que la lune manque de ces traînées, **alors** T2 se commande, et
seulement pour ça.

**T2 et T4 passent donc de « conditionnelles » à « probablement inutiles ».** Les blocs restent
écrits, ils ne se commandent pas sans une capture qui les réclame.

#### La liste

Quatre textures, dont **deux obligatoires** et deux conditionnelles. Les conditionnelles ne se
décident pas sur plan : elles dépendent de ce que la première capture montre.

| # | Fichier source | Rôle | Statut |
|---|---|---|---|
| **T1** | `moon_regolith_height_1024.png` | hauteur du grain et des petits cratères de la calotte | **obligatoire** |
| **T2** | `moon_regolith_albedo_1024.png` | ejectas clairs autour des impacts récents | **probablement inutile** — `--mul` couvre le reste |
| **T3** | `asteroid_rock_height_1024.png` | hauteur de la roche des trois astéroïdes | **obligatoire** |
| **T4** | `asteroid_rock_albedo_1024.png` | variation d'albédo de la roche | **probablement inutile** |

⚠️ **La condition de T2 est écrite dans le brief, et elle est sérieuse** : « à cette distance
**aucune ombre portée ne dessinera le relief** (`directional_shadow_max_distance` vaut 40, la lune
est bien au-delà) […] un cratère purement géométrique, sans contraste d'albédo, risque d'être
**invisible** ». Autrement dit : si T1 seule ne fait pas lire les creux en capture, T2 n'est pas un
agrément, c'est la seule chose qui les dessine. **T2 se décide en regardant, pas ici.** Même
raisonnement pour T4, en moins critique — les rochers passent vite.

---

#### 📄 Les demandes sont des FICHIERS, pas des blocs de ce plan

⚠️ **Corrigé le 2026-08-26.** Une première version portait les JSON en ligne, ici. Deux défauts :
ils ne suivaient pas le contrat demandé (blocs de prose au format historique de `/asset-image`), et
un plan de 900 lignes n'est pas traitable en séparé. Demande de l'opérateur, mot pour mot :
« j'aimerai que quand on génère des prompts à traiter que **l'ensemble de la demande soit dans un
fichier**, plus facile à traiter en séparé ».

Une demande = un fichier, autosuffisant :

| Fichier | Sujet | Statut |
|---|---|---|
| [`TEX-0001-moon-regolith-height.json`](../forge/textures/TEX-0001-moon-regolith-height.json) | grain et petits cratères de la calotte | **à commander** |
| [`TEX-0002-asteroid-rock-height.json`](../forge/textures/TEX-0002-asteroid-rock-height.json) | roche des trois astéroïdes | **à commander** |
| [`TEX-0003-moon-regolith-albedo.json`](../forge/textures/TEX-0003-moon-regolith-albedo.json) | ejectas clairs de la lune | conditionnelle |
| [`TEX-0004-asteroid-rock-albedo.json`](../forge/textures/TEX-0004-asteroid-rock-albedo.json) | variation d'albédo de la roche | conditionnelle |

Le **contrat** (schéma, six règles de validation, extensions `x_`) est dans
[`docs/forge/textures/README.md`](../forge/textures/README.md), institué par
[`ADR-0028`](../decisions/ADR-0028-la-texture-est-une-etape.md) : la texture est désormais une
**étape du process**, plus une permission. Le gabarit de brief, la charte créative et l'agent
`asset-forge` ont été mis à jour le même jour ; le skill `/asset-image` produit maintenant un
fichier `TEX-NNNN` au lieu d'un bloc de conversation.

Chaque fichier porte tout : le besoin, les contraintes techniques vérifiées contre les six règles,
l'échelle monde avec sa `confidence`, le chemin de dépôt, la commande `derive-maps.py`, les
vérifications et la ligne de provenance prête à coller. Et `x_prompt_fr` porte le prompt **dérivé**
de ces champs — régénérable, jamais édité à la main.

#### Ce qu'il reste à décider

1. **T2 et T4 sont-elles commandées ?** → **ne se décide pas ici.** Une capture après T1/T3, et la
   question se répond seule.
2. **Une cinquième texture pour le ciel du survol ?** → **Non, et c'est acté** : le ciel est un
   **shader** (`space_background.gdshader` en mode `deep_sky`), pas une image. `BRIEF-0085` le range
   déjà hors périmètre. Le noter ici évite qu'on le redemande.
3. **Où vivent ces JSON à terme ?** Ils sont dans ce plan parce que c'est là que le besoin est né.
   S'ils servent une seconde fois, leur place est un gabarit du dépôt — à voir en `/capitalize`,
   pas maintenant.

#### Vérification propre à ce lot

```bash
# Pour chaque source deposee dans assets/source/textures/backgrounds/
python3 tools/derive-maps.py <source>.png \
  --out assets/imported/textures/backgrounds --check-tiling \
  --preview /tmp/<nom>.png
```

La ligne **« tuilage »** doit dire **OK** — c'est elle qui transforme un seamless *demandé* en
seamless *obtenu*. Puis la preview s'ouvre et **se regarde** (`ADR-0006`). Et enfin, la seule
vérification qui compte vraiment : la phase 2 en capture, avec le chasseur et les mines par-dessus.
Si la surface est belle et que le chasseur s'y perd, la texture est **à refaire**, pas à ajuster.

### Lot 4 — Équilibrage et ressenti

La phase change la durée de l'arc et la montée en puissance. Elle se juge en jouant, pas au
journal. Le Shield Carrier (`BRIEF-0046`) trouverait ici son emploi naturel.

⚠️ **Et il manquait pour une raison précise, relevée le 2026-08-25** : son comportement est
**entièrement codé** — `Effect.SHIELD_AURA`, la garde de validation, le relais dans
`EnemyController`, les tests, le banc d'essai — mais l'unité n'a **ni Resource, ni scène, ni
coque**. `BRIEF-0046` était prêt depuis le 23/08 et n'avait jamais été exécuté. C'est lui,
et non l'équilibrage, qui bloquait ce lot : il a été confié à la forge.

Une fois la coque livrée, l'intégration reste à faire de mon côté : `.tres`, `.tscn`, fiche
codex, et **son entrée dans la vague du champ d'astéroïdes** — une ou deux unités, pas plus.
Elle ne menace rien et change tout : tant qu'elle vit, la vague est un mur.

#### Playtest du 2026-08-26 — la Choir Mine s'évite trop bien

Premier passage de l'opérateur sur la phase complète, arc joué depuis l'écran-titre. Constat :
« les mines ne se déclenchent que sur le survol du corps, c'est beaucoup trop facile à éviter ».

Le rayon de proximité existe pourtant, et la distance est mesurée correctement dans le plan de
jeu (`enemy_controller.gd:411`). Ce n'est donc pas un bug : c'est un **réglage**, et il se lit
dans la combinaison, pas dans un chiffre isolé (`resources/enemies/choir_mine.tres`) :

| Réglage | Valeur | Ce qu'il fait |
|---|---|---|
| `hitbox_radius` | 0,58 | la coque |
| `trigger_radius` | **2,2** | où l'engagement part |
| `alert_radius` | 4,5 | où le noyau s'allume |
| `windup_time` | **0,7 s** | le délai avant la salve |

⚠️ **Ce sont les 0,7 s qui font le défaut, autant que les 2,2 unités.** On entre à 2,2, la mine
s'ouvre pendant 700 ms, et le chasseur est sorti de la couronne (2,2 u de portée) avant que les
14 projectiles ne partent. Le contrat « ce qui s'allume part » (`enemy_reaction.gd`) est tenu —
mais ce qui part ne touche personne. D'où le ressenti de contact pur.

Deux leviers, donc, et **il faut choisir lequel** : élargir `trigger_radius`, ou raccourcir
`windup_time`. Ils ne disent pas la même chose — le premier agrandit la zone interdite, le
second retire au joueur le temps de lire le télégraphe. La spec §11.2 borne le télégraphe à
300-800 ms : il reste 400 ms de marge à la baisse, pas plus.

⚠️ **Contrainte dure de validation** : `enemy_data.gd:215` impose `alert_radius > trigger_radius`.
Monter le déclenchement oblige à monter l'alerte avec — un `trigger_radius` à 3,2 demande un
`alert_radius` vers 5,5, sinon `validate()` échoue et `check.sh` casse.

⚠️ **Ne pas fixer ces valeurs au jugé.** La phase compte 10 entrées de mines réparties sur 37 s
(`wave_asteroid_field_01.tres`) : un passage de `balance-prober` dit combien déclenchent
réellement, et c'est ce chiffre qui doit caler le réglage — pas une impression de partie. Toute
retouche se revérifie ensuite au banc d'essai (`--goto-lab=mine`), qui porte ses propres copies
des rayons (`bestiary_lab.gd:147-148`) : **elles doivent bouger ensemble**, sinon le banc ment.

### Lot 5 — La mise en scène des transitions — 🔨 **EN COURS (A + D, tranché le 2026-08-26)**

> **Ajouté le 2026-08-26**, après le premier playtest de l'arc complet. Le plan n'avait **rien**
> sur ce sujet : le lot 2 a posé la bascule de décor, personne ne s'est demandé comment on y
> **entre**. C'est un manque du plan, pas un écart d'exécution.

Constat de l'opérateur, mot pour mot : « il y a un souci de transition après le premier boss,
on a un clignotement pour être dans la phase 2 avec le nouveau décor, puis clignotement à
nouveau et on voit le boss de fin ».

#### Pourquoi ça clignote — la cause est nue

La bascule est un **booléen sur une seule image**, aux deux bouts de la chaîne :

```gdscript
# scripts/vfx/moon_flyby.gd:155
func reveal(on: bool) -> void:
	visible = on

# scripts/gameplay/graybox_root.gd:585
	backdrop.visible = false
```

`_show_moon_flyby()` (`graybox_root.gd:408`) appelle les deux **dans la même image**. Il y a donc
exactement deux coupes franches, et ce sont celles que l'opérateur a vues :

| Moment | Appel | Ce qui se passe |
|---|---|---|
| Mini-boss mort | `_start_asteroid_field()` → `_show_moon_flyby(true)` (`:377`) | la nébuleuse s'éteint, le survol s'allume, même image |
| Champ nettoyé | `_start_final_boss()` → `_show_moon_flyby(false)` (`:446`) | le survol s'éteint **et** le boss est instancié dans la foulée, sans délai |

⚠️ **Le journal ne pouvait pas le dire.** Un `visible = false` n'émet aucune ligne : la partie
est sortie en `code 0`, tous les jalons présents, et le défaut est resté invisible au relevé.
C'est un cas d'école d'`ADR-0006` — ce qui est visuel se juge en regardant, pas au log.

⚠️ Le bandeau « CHAMP D'ASTEROIDES » (1,6 s, `graybox_root.gd:379`) existe déjà, mais le décor
change **sous** lui. Le bandeau n'est pas une transition : il annonce, il ne raccorde pas.

#### Ce qu'il faut construire

Une transition n'est pas qu'un fondu : c'est le raccord entre deux lieux et deux musiques. Les
fondus audio sont déjà là et durent **6 s** (`[Audio] music 4 -> 6` au playtest) — l'image, elle,
bascule en **une image**. Le décalage entre les deux est une bonne part du malaise.

- **Entrée dans le champ** — faire **céder** la nébuleuse au lieu de l'éteindre. Le survol monte
  pendant que le fond descend, sur une durée à caler contre le fondu musical de 6 s.
- **Sortie vers le boss final** — séparer les deux gestes qui sont aujourd'hui collés : le décor
  se retire, **puis** le Leviathan entre. Il apparaît actuellement dans la même image que le
  retour de la nébuleuse.
- **Le point de passage obligé reste `_start_final_boss()`** — le commentaire de `:441` le dit :
  c'est le seul chemin que `--skip-to-final` et `--no-wave` empruntent aussi. Toute mise en scène
  doit **tolérer d'être sautée**, sinon les drapeaux de développement se retrouvent avec un décor
  qui survit à sa phase.

#### Ce que la bible de design impose — lue le 2026-08-26

⚠️ **Ce lot avait d'abord été écrit sans consulter `docs/design/bible/`**, arrivée le 2026-08-25
(commit `df2e899`). Relecture faite, elle change la nature du sujet : la transition n'est pas un
défaut cosmétique, c'est le seul point de l'arc que la bible notait déjà **❌ non tenu**.

**Le manque était écrit AVANT le playtest.** [Niveau et rythme](../design/bible/03-niveau-et-rythme.md),
tableau « chez nous » :

> | Ralentir avant la fin | ❌ **Non tenu.** Le boss final arrive après le champ d'astéroïdes, sans respiration |

Le genre est explicite sur cette marche : on **ralentit avant le boss final**, on laisse souffler,
et c'est ce qui construit l'attente. L'opérateur a ressenti le 26 ce que la bible avait relevé le
25, sans qu'aucun des deux ne parte de l'autre. Le second clignotement n'est donc pas un raccord
manquant : c'est **une respiration manquante**, dont le raccord manquant est le symptôme visible.

Et [Boss](../design/bible/04-boss.md) le dit d'une phrase, sur le rapport du boss à son niveau :

> « Des attaques sans rapport avec le thème du niveau font un boss **détaché**. La transition
> compte autant que le combat. »

**Trois contraintes dures en découlent**, tirées de [Lisibilité](../design/bible/01-lisibilite.md),
« la page dont tout le reste dépend » :

1. **Les couleurs sont réservées.** Le **cyan** appartient au tir allié, le **corail** au tir
   ennemi, et la règle est écrite dans `shaders/space_background.gdshader`. ⛔ Aucun voile, flash
   ou fondu de transition ne peut les employer — `ADR-0027` a déjà arbitré exactement ça sur le
   bolide d'impact, qui est **doré** pour cette raison.
2. **La zone calme centrale.** Le fond s'assombrit au tiers central (`center_calm`) parce que
   « l'art ne doit jamais disputer l'attention au vaisseau et aux balles ». Une transition qui
   passe par le centre du cadre viole le seul endroit que le jeu s'interdit.
3. **Le décor ne doit pas mentir.** Rien qui traverse le champ de jeu ne doit ressembler à un
   obstacle sans en être un. Au lot 2, un astéroïde décoratif frôlait le chasseur et a dû être
   écarté du couloir de vol — une transition qui fait passer de la matière devant le joueur
   rouvre ce problème.

**Et un repère à ne pas gâcher.** Boghog appelle *landmark uniqueness* ce qui donne au joueur sa
carte mentale du niveau, et cite nommément « un changement de fond ». Nous en avons un, entier,
et nous le dépensons en une image. Une transition ne fait pas que réparer le clignotement : elle
**encaisse** un repère que le lot 2 a payé et que personne ne voit passer.

#### 💡 Ce que la bible a fait apparaître, et que personne n'avait relevé

**Le champ d'astéroïdes enseigne DÉJÀ une mécanique du Leviathan, et rien ne le dit.**

La bible pose comme écart de fond que « le boss final n'enseigne rien avant de l'exiger »
([Boss](../design/bible/04-boss.md), [Niveau et rythme](../design/bible/03-niveau-et-rythme.md)).
C'est vrai des plaques et de la plongée. Ça ne l'est **pas** de l'aspiration :

| | |
|---|---|
| `scripts/gameplay/gravity_well.gd:2` | « Champ d'aspiration radial — **la primitive de la phase 2 du Pale Leviathan** » |
| `scripts/enemies/enemy_controller.gd:414` | « gravitique du boss (`GravityWell`), mais **posée par une unité de vague** » |
| `resources/enemies/null_maw.tres:42` | `pull_radius = 4.5` |

Le Null Maw et le boss final appellent **la même fonction** — `GravityWell.pull_at()`. La phase 2
contient donc déjà, quatre fois (deux puits à 10 s et 11,5 s, deux en tenaille à 30 s), la leçon
que le boss exigera. Elle est enseignée par accident et récoltée par personne.

C'est ce qui rend la proposition D possible, et c'est aussi une note pour la bible elle-même : sa
ligne « le boss final ne résume rien » mérite une nuance datée.

#### Quatre propositions de transition

Elles sont classées par ce qu'elles **achètent**, pas par difficulté. Elles ne s'excluent pas
toutes : **A est contenue dans B, C et D** — c'est le raccord de base que les trois autres
habillent.

---

##### A — Le fondu croisé instrumenté *(le raccord minimal)*

Le fond spatial et le survol se croisent sur une durée réglable au lieu de commuter. Le joueur
garde la main, la vague continue, rien d'autre ne change.

- **Ce que ça achète** : le clignotement disparaît, aux deux bouts. Rien de plus.
- **Ce que ça coûte** : une opacité pilotée sur les deux décors, et **les deux coûts GPU
  s'additionnent pendant le croisement**. La marge existe — le ciel du survol est descendu à
  **0,323 ms**, un tiers du fond habituel — mais elle se mesure sur la **Quadro T1000**.
- **Ce que ça ne règle pas** : la respiration manquante. Le Leviathan arrivera toujours sans que
  rien n'ait ralenti. ⚠️ **La bible resterait ❌ sur sa ligne.**
- **Risque** : aucun sur la lisibilité, tant qu'aucune teinte ne s'ajoute au croisement.

##### B — La respiration avant le Leviathan *(ce que la bible réclame)*

Le champ nettoyé, l'arc **ne relance pas immédiatement**. Trois à cinq secondes sans aucune
menace : le survol se retire, la musique a déjà tourné, l'écran se vide — puis le boss entre.
C'est la marche « ralentir avant la fin », littéralement.

- **Ce que ça achète** : le seul ❌ du tableau de la bible passe à ✅. Et le pic se lit comme un
  pic, parce qu'il y a eu un creux — « le repos n'est pas du vide : c'est ce qui rend le pic
  lisible comme un pic ».
- **Ce que ça coûte** : **du temps d'arc**, et c'est le vrai arbitrage. La bible pose elle-même la
  garde : « la durée de l'arc est déjà à sa cible (2-3 min), ajouter du temps mort peut coûter
  plus que ça ne rapporte. **À juger en jouant l'arc entier.** » La phase 2 est bornée à 45-60 s
  (décision n°2) ; la respiration s'ajoute **par-dessus**, elle ne s'y prend pas.
- **Point de vigilance** : le genre dit aussi « garder le joueur occupé en permanence ». Une
  respiration n'est pas un écran d'attente — il faut quelque chose à regarder, sinon c'est un
  temps mort. C'est ce qui pousse vers C.
- **Risque** : le joueur croit que le jeu a planté. Un signe est obligatoire.

##### C — L'entrée en scène du Leviathan *(le raccord diégétique)*

La transition n'est pas un effet, c'est un **événement**. Le décor sort du cadre pour une raison
qu'on voit : le survol s'éloigne, et le Leviathan **se lève du limbe de la lune** et l'éclipse —
il vient du lieu que le joueur vient de traverser.

- **Ce que ça achète** : le clignotement, la respiration **et** l'écart de la page Boss — « le
  boss appartient à son niveau ». Le repère (*landmark*) est encaissé au lieu d'être dépensé.
- **Ce que ça coûte** : le plus cher des quatre. Une chorégraphie, un cadrage, un boss dont
  l'échelle doit tenir contre une lune de rayon 60 — et probablement des captures à chaque
  itération. ⚠️ La géométrie du lieu est **posée et tenue par un test** (`test_moon_flyby.gd` :
  ciel à Y = −45, lune centrée (0, −78, 34), plafond à −3) : la mise en scène s'y inscrit, elle
  ne la redéfinit pas.
- **Risque** : ⛔ **la zone calme centrale**. Un boss qui monte plein centre pendant que le joueur
  y est encore, c'est exactement ce que `center_calm` s'interdit. L'entrée doit se faire par un
  bord, ou le joueur doit être invité à sortir du centre avant.
- **Second risque** : le décor qui ment. La lune est **décor sans collision** (décision n°3) ; la
  faire bouger de façon spectaculaire près du plan de jeu promet une matière qui n'existe pas.

##### D — Le sas qui enseigne *(la transition comme leçon)*

Exploite ce que la section précédente a mis au jour : la phase 2 pose déjà des puits gravitiques
qui sont **la primitive du boss**. Au lieu de nettoyer l'écran, le dernier puits **ne meurt pas**
— il grossit, dérive vers le haut, et devient l'aspiration du Leviathan qui entre. La leçon et
l'examen se touchent.

- **Ce que ça achète** : tout ce que B achète, **plus** une entaille dans l'écart de fond que la
  bible pose deux fois — « le boss final n'enseigne rien avant de l'exiger ». Et ça ne coûte
  aucun asset : la primitive, le pooling et le rendu du puits existent.
- **Ce que ça coûte** : du **code de gameplay**, pas de la mise en scène. Un puits qui survit à sa
  vague sort du contrat de `WaveSpawner` (`wave_cleared` ne partirait plus quand on croit).
  ⚠️ Et il faut décider s'il **blesse** pendant le sas — un puits qui aspire pendant une
  respiration n'est plus une respiration.
- **Risque** : casser la borne de durée de la phase, tenue par `test_asteroid_field_wave.gd`.
- **Note** : D et C ne s'excluent pas — le puits qui monte **est** une entrée en scène.

---

##### Récapitulatif

| | Clignotement | Respiration (bible ❌) | Boss rattaché au niveau | Enseigne | Coût | Asset requis |
|---|---|---|---|---|---|---|
| **A** Fondu croisé | ✅ | — | — | — | faible | non |
| **B** Respiration | ✅ | ✅ | — | — | faible + temps d'arc | non |
| **C** Entrée en scène | ✅ | ✅ | ✅ | — | élevé | oui (lot 3) |
| **D** Sas qui enseigne | ✅ | ✅ | partiel | ✅ | moyen | non |

⚠️ **A est le socle** : quelle que soit l'option retenue, le fondu croisé est à faire, parce que
c'est lui qui supprime la coupe franche. B, C et D disent ce qu'on met **dedans**.

💡 **Recommandation** : **A + D**. C'est la seule combinaison qui répare le défaut vu, coche la
ligne ❌ de la bible et entame l'écart de fond du boss — **sans attendre le lot 3**, puisqu'elle
n'emploie que des primitives déjà livrées. C reste la belle version, à garder pour le jour où la
lune et les rochers existent vraiment.

#### Ce qu'il faut décider avant de coder

1. **Quelle proposition ?** → ✅ **TRANCHÉ le 2026-08-26 : A + D.** Fondu croisé aux deux bouts,
   et le dernier puits gravitique survit à sa vague — il grossit, dérive vers le haut, et devient
   l'aspiration du Leviathan qui entre. **C est écartée pour l'instant**, pas rejetée : elle
   attend la lune et les rochers du lot 3.
2. **Quelle durée ?** Elle se soustrait au temps de jeu et s'ajoute à la durée de l'arc, déjà
   bornée à 45-60 s pour la phase elle-même (décision n°2 ci-dessous).
3. **Le joueur garde-t-il la main pendant ?** Une transition qui verrouille les commandes est une
   cinématique ; une qui les laisse est un raccord. Les deux se défendent, pas au même prix.

⚠️ **Coût GPU** : un fondu croisé fait cohabiter les deux décors pendant sa durée — donc les deux
coûts s'additionnent au moment du raccord. La marge existe (le ciel du survol est descendu à
**0,323 ms**, un tiers du fond habituel), mais elle se mesure **sur la Quadro T1000**, comme tout
le reste de ce plan.

#### Vérification propre à ce lot

Aucune ligne de journal ne prouvera quoi que ce soit ici. Il faut des **captures regardées**
pendant le raccord — donc plusieurs `--capture-after` encadrant l'instant de bascule — et un
`/jouer` de bout en bout pour le ressenti.

## Ce qui demandait une décision de l'opérateur — ✅ **tranché le 2026-08-25**

1. **Un ADR est-il requis ?** → **Oui.** `ADR-0027`, écrit au lot 1.
2. **Combien de temps doit durer la phase ?** → **45 à 60 s**, contre les ~40 s du boss final.
   Encodé comme borne dans `test_asteroid_field_wave.gd`.
3. **La lune est-elle décor pur, ou objet de gameplay ?** → **Mixte** : les **astéroïdes
   seront solides** (quelques rochers proches, obstacles à éviter), la **lune reste du décor**
   — ni collision ni hitbox sur la surface survolée.
   ⚠️ Cet arbitrage porte sur les **lots 2-3** et n'a rien changé au lot 1. Il ajoute au lot 3
   un sujet que le plan n'avait pas : des astéroïdes de premier plan qui **collisionnent**
   sont des entités de gameplay, pas du décor — donc une hitbox, un pooling, et un
   équilibrage. À traiter comme tel au moment du brief.
   ⚠️ Et un second, apparu en regardant le lot 2 : **solides et décoratifs partageront le
   cadre**. Rien ne les distinguera à l'œil si on n'y pourvoit pas, et l'injustice joue dans
   les deux sens — croire qu'on peut éviter un rocher qui traverse, ou traverser un rocher
   qui tue.

## Vérification, de bout en bout

```bash
./scripts/check.sh                    # porte de qualité — DoD du projet
./scripts/play.sh                     # arc complet depuis l'écran-titre
# le journal doit montrer :
#   [Level] mini-boss defeated
#   [Level] ASTEROID FIELD
#   [WaveSpawner] pool ready: N      <- au montage UNIQUEMENT
#   [Level] FINAL BOSS
```

⚠️ **Et ce relevé ne suffit pas** — playtest du 2026-08-26 : ces quatre lignes étaient
toutes présentes, la partie est sortie en `code 0`, et la phase avait pourtant deux coupes
franches de décor (lot 5) et des mines qu'on évite en ligne droite (lot 4). Un journal vert
dit que l'arc s'enchaîne, jamais qu'il se joue bien.

Puis, et seulement en capture regardée (`ADR-0006`) :

```bash
rm -f /mnt/c/tmp/aegis-ascendant/capture.png
./scripts/play.sh -- --goto-graybox --capture --capture-after=<60 × t>
```

⚠️ Le PNG **doit** être effacé avant, la ligne `[ScreenCapture] saved` **doit** apparaître, et
un PNG de 15 Ko en 1920×1080 est presque uniforme — c'est le test d'écran noir le moins cher.
Et **mesurer le temps GPU par image**, jamais le FPS d'un lancement automatisé.
