---
titre: Une phase de jeu entre les deux boss — survol de lune et champ d'astéroïdes
date: 2026-08-25
auteur: session Claude (poste happykiller), sur demande de l'opérateur
perimetre: arc de jeu (graybox_root), vagues, fond spatial, assets 3D de décor
etat: à appliquer — rien n'est commencé
supersede: rien. Complète docs/plans/2026-08-25-bestiaire-ennemis.md sur son point 3.1
---

# Une phase de jeu entre les deux boss

> **Rédigé le 2026-08-25** à partir de la demande de l'opérateur, et de l'état **mesuré** du
> moteur. Rien n'est commencé : ce document est un point de départ, pas un compte-rendu.

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

### Lot 1 — La phase existe et se joue *(aucun asset requis)*

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

### Lot 2 — Le décor bascule *(aucun asset non plus)*

- Un nœud `MoonFlyby` monté comme `CoreInterior` l'est : bâti au montage, caché, révélé à
  l'entrée de la phase, avec une **doublure procédurale** tant que les assets n'existent pas.
- Bascule : nébuleuse + landmarks masqués, survol montré. Rétabli à la sortie.
  ⚠️ Restaurer **l'état antérieur**, pas « visible » — `--no-backdrop` doit survivre à la
  phase, sinon une mesure de silhouette se ferait sur deux images incomparables (leçon
  d'`ADR-0025`).
- **Mesurer le GPU avec et sans**, à ce stade et pas plus tard : c'est le chiffre qui dira
  combien d'asset le lot 3 peut se payer.

### Lot 3 — Les assets *(forge, briefs à écrire)*

À n'engager **qu'une fois le budget GPU du lot 2 connu**.

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

## Ce qui demande une décision de l'opérateur

1. **Un ADR est-il requis ?** L'arc est acté par `ADR-0010` (« un seul vaisseau, appontage
   final ») qui avait **supprimé** une phase. En rajouter une le modifie : à mon sens oui, un
   ADR court, au moment du lot 1.
2. **Combien de temps doit durer la phase ?** Le P0 vise « 2-3 min de jeu » pour tout l'arc ;
   le boss final fait déjà ~40 s.
3. **La lune est-elle décor pur, ou objet de gameplay ?** Le plan ci-dessus la traite comme du
   **décor** — aucune collision, aucune hitbox. Un survol dont on peut heurter le relief est un
   autre jeu, et un autre chantier.

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
