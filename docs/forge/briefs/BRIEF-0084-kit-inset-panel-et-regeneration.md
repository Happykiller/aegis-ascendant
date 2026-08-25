# BRIEF-0084 — Réparer `inset_panel()` dans le kit, et régénérer toutes les coques

- **Statut** : livré
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-08-25

## Objectif

Corriger **`ak.inset_panel()`** dans `tools/blender/lib/aegis_kit.py`, puis **régénérer toutes
les coques du dépôt** et rendre une revue avant/après de chacune.

## Contexte

`inset_panel()` est *le* moyen par lequel `ADR-0008` demande le détail : « le détail par la
géométrie ». **Il ne creuse rien depuis le début.** Deux défauts distincts, trouvés par deux
sessions différentes, tous deux **mesurés**, tous deux **totalement silencieux** — ni le
compte de triangles, ni le contrat d'export, ni le rendu ne les signalent.

### Défaut 1 — la normale de face vaut zéro sur un maillage frais

`bmesh.ops.inset_region` lit la normale de face, qui vaut `(0,0,0)` tant que
`normal_update()` n'a pas été appelé. Mesure de la session bestiaire : bordures d'aire
**0,000000 m²** sans la mise à jour, contre **0,000714 m²** avec, puis ressoudées par
`cleanup()`. **Il ne reste que le changement de matériau** : un panneau qui se voit et qui
n'existe pas.

### Défaut 2 — `inset_region` inset une RÉGION, pas des faces

N faces **contiguës** ne produisent qu'**un seul** liseré, autour de leur union. Trouvé par
la forge de `BRIEF-0082` : ses 240 plaques de pont ne donnaient qu'un liseré autour de
l'arène entière. Contrat vert, budget respecté, pont parfaitement lisse au rendu — il a fallu
recadrer un coin de la planche pour le voir. Correctif retenu là-bas : **découper la liste en
lots sans arête commune**, et insetter lot par lot. Coût mesuré : **12 386 → 19 414
triangles** sur ce décor, soit **+57 %**.

### Ce que le dépôt subit aujourd'hui

| Script | Appels `inset_panel` | `normal_update` |
|---|---|---|
| `build_specter_9.py` | 15 | **0** |
| `build_crescent_interceptor.py` | 12 | **0** |
| `build_aegis_citadel.py` | 9 | **0** |
| `build_pale_leviathan.py` | 9 | **0** |
| `build_choir_harvester.py` | 7 | **0** |
| `build_choir_mine.py` | 3 | **0** |
| `build_citadel_turret.py` | 2 | **0** |
| `build_needle_scout.py` | 2 | **0** |
| `build_citadel_beacon.py` | 1 | **0** |
| `build_null_maw.py` | 1 | **0** |
| `build_leech_drone.py` | 3 | 2 |
| `build_core_interior.py` | 1 | 2 |

**Lire d'abord** : `ADR-0008`, `ADR-0011` (budgets), `docs/forge/CHARTE_CREATIVE.md`, et les
rapports `BRIEF-0082-report.md` (défaut 2, avec son correctif) et `BRIEF-0083-report.md`.

## Contraintes

### 1. Vérifier les deux défauts AVANT de les corriger

⚠️ Les deux sont rapportés par d'autres sessions. **Ne les corrige pas sur leur parole** :
reproduis-les et mesure-les toi-même, sur un cas minimal, et rapporte les chiffres. Si l'un
des deux ne se reproduit pas, dis-le — c'est un résultat, pas un échec.

### 2. Le correctif va dans le KIT, pas dans les scripts

C'est la raison d'être de ce brief : corrigé script par script, le prochain l'oubliera comme
les onze précédents. `inset_panel()` doit être **juste par défaut**. Les scripts qui appellent
déjà `normal_update()` de leur côté ne doivent pas en souffrir (idempotence).

### 3. Budgets — il y a de la marge, sauf pour le chasseur

Plafonds d'`ADR-0011` et comptes actuels, **mesurés sur les `.glb` du dépôt** :

| Coque | Actuel | Plafond | Marge à +57 % |
|---|---|---|---|
| `specter_9` | 35 008 | 60 000 | ~54 960 — **le plus serré** |
| `aegis_citadel` | 62 712 | 120 000 | ~98 460 |
| `pale_leviathan` | 30 122 | 90 000 | ~47 290 |
| `choir_harvester` | 18 666 | 90 000 | large |
| `core_interior` | 19 414 | 22 000 (brief) | **déjà corrigé, ne pas le regénérer à la hausse** |
| légers (`needle_scout`, `crescent_interceptor`, `leech_drone`, `choir_mine`, `null_maw`) | 1 612 – 6 630 | 12 000 | large |
| `citadel_beacon`, `citadel_turret` | 1 852 / 2 596 | 120 000 | large |

**Si une coque dépasse son plafond, ne la mutile pas** : rapporte le dépassement, le compte
exact et ce que tu proposes. Un dépassement chiffré vaut mieux qu'un détail supprimé en
silence.

### 4. Le contrat de noms est sacré

⚠️ **Une régression de nom ou de parentage casse le gameplay sans qu'aucun test ne le voie.**
Le code résout ses pièces par `find_child` : `Plate_01..04`, `Spike_01..04`,
`Muzzle_Spike_01..04`, `Shell_Ring`, `Shell_Crescent`, `Core`, `Heart`, `Ring_01..05`,
`Shutter_01..06`, `Node_01..03`, `Petal_*`, `Muzzle_*`, `Engine_*`, `Cradle_*`,
`Reactor_Core`, `Entry_Point`… Pour **chaque** coque régénérée, compare la liste des nœuds et
leur parentage **avant/après** et rapporte le diff. Il doit être **vide**.

### 5. Déterminisme

Chaque `.glb` régénéré : trois exécutions, sha256 identique. Rapporte-le.

## Livrables

| Fichier | Description |
|---|---|
| `tools/blender/lib/aegis_kit.py` | `inset_panel()` corrigé |
| `assets/imported/models/**/*.glb` | toutes les coques régénérées |
| `docs/forge/output/BRIEF-0084-revue-avant-apres.png` | planche(s) de revue : chaque coque **avant et après**, à l'angle de la caméra de jeu, sur fond noir (`--no-backdrop` est l'outil de lecture de la géométrie) |
| `docs/forge/output/BRIEF-0084-report.md` | les deux défauts reproduits et mesurés, le correctif, et par coque : triangles avant/après, diff du contrat de noms, couverture UV, sha256, ligne de provenance à recaler |

## Provenance

⚠️ **N'ÉCRIS PAS dans `assets/licenses/ASSET_PROVENANCE.csv`** — un seul écrivain, ce sera
moi. Donne les lignes recalées dans le rapport, une par coque régénérée.

## Critères d'acceptation

- [ ] Les deux défauts **reproduits et mesurés par toi**, chiffres à l'appui.
- [ ] Correctif dans **`aegis_kit.py`**, idempotent pour les scripts déjà sains.
- [ ] Toutes les coques régénérées, **aucune** au-dessus de son plafond `ADR-0011` (ou
      dépassement rapporté et chiffré, jamais du détail supprimé en douce).
- [ ] Diff du contrat de noms **vide** pour chaque coque, rapporté coque par coque.
- [ ] UV sur 100 % des primitives, partout.
- [ ] Déterminisme vérifié (trois exécutions) sur chaque `.glb`.
- [ ] Planche avant/après **regardée** : le relief doit se voir là où il n'existait pas, et
      **aucune silhouette ne doit changer**.

## Hors périmètre

- Toute retouche de **forme** : ce chantier répare un outil, il ne redessine rien. Si une
  coque te paraît fautive, signale-la, ne la corrige pas.
- `shaft_radius()` de `build_pale_leviathan.py` (la cause des `Ring_01..05` à 19 cm) : connue,
  volontairement laissée — sa correction se prend avec une décision de gameplay.
- Le code de jeu, les scènes, les Resources, les tests.
