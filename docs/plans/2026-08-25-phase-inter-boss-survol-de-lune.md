---
titre: Une phase de jeu entre les deux boss — survol de lune et champ d'astéroïdes
date: 2026-08-25
auteur: session Claude (poste happykiller), sur demande de l'opérateur
perimetre: arc de jeu (graybox_root), vagues, fond spatial, assets 3D de décor
etat: lots 1 et 2 LIVRÉS (ADR-0027, 2026-08-25) ; lots 3 et 4 à appliquer
supersede: rien. Complète docs/plans/2026-08-25-bestiaire-ennemis.md sur son point 3.1
---

# Une phase de jeu entre les deux boss

> **Rédigé le 2026-08-25** à partir de la demande de l'opérateur, et de l'état **mesuré** du
> moteur.
>
> ✅ **Lots 1 et 2 livrés le 2026-08-25** — la phase existe et se joue, et son décor
> bascule. Voir **`ADR-0027`**. Les trois décisions ouvertes en bas de page ont été **tranchées** par
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

### Lot 3 — Les assets *(forge, briefs à écrire)*

À n'engager **qu'une fois le budget GPU du lot 2 connu**.

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

### Lot 4 — Équilibrage et ressenti

La phase change la durée de l'arc et la montée en puissance. Elle se juge en jouant, pas au
journal. Le Shield Carrier (`BRIEF-0046`, prêt) trouverait ici son emploi naturel.

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

Puis, et seulement en capture regardée (`ADR-0006`) :

```bash
rm -f /mnt/c/tmp/aegis-ascendant/capture.png
./scripts/play.sh -- --goto-graybox --capture --capture-after=<60 × t>
```

⚠️ Le PNG **doit** être effacé avant, la ligne `[ScreenCapture] saved` **doit** apparaître, et
un PNG de 15 Ko en 1920×1080 est presque uniforme — c'est le test d'écran noir le moins cher.
Et **mesurer le temps GPU par image**, jamais le FPS d'un lancement automatisé.
