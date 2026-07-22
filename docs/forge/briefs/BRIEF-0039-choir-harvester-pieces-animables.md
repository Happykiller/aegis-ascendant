# BRIEF-0039 — Choir Harvester : des pièces réellement animables, et trois appendices

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-07-22

## Objectif

Reforger `tools/blender/build_choir_harvester.py` pour que **toutes les pièces mobiles du mini-boss
soient animables depuis Godot**, et pour que sa structure corresponde à sa planche : **trois**
appendices — une faux, une griffe à trois têtes, un canon — autour d'un corps-iris.

## Contexte

Le combat du Choir Harvester est entièrement réécrit côté gameplay : le joueur détruira ses trois
appendices pour ouvrir l'iris et frapper le noyau, les appendices repoussant en boucle. Le code de
ce combat est écrit **en parallèle de ce brief**, contre le contrat de noms du §« Livrables ».

### Le défaut à corriger — il est technique, pas esthétique

Ton propre en-tête de script annonce déjà l'intention :

> « Le gameplay doit pouvoir cibler et animer le noyau, les cinq pétales de l'iris, les trois bras
> et le module arrière : ils sont donc livrés comme **objets distincts et nommés** »

Les objets sont bien distincts. **Mais ils ne peuvent pas être animés**, et le script explique
pourquoi sans en tirer la conséquence :

> « Toutes les pieces sont donc laissees a la transformation identite, geometrie exprimee dans le
> repere global (…) Les pivots d'animation sont livres a cote, sous forme de points d'attache
> `Hinge_*`. »

Une pièce dont l'origine est celle du modèle tourne **autour du centre du boss**, pas autour de sa
charnière. Les marqueurs `Hinge_*` livrés à côté ne servent à rien : Godot ne sait pas s'en servir
comme pivot sans reparenter à la main, ce que le gameplay ne fera pas.

Le kit a **exactement la primitive qui manque**, écrite depuis (BRIEF-0035) :

```python
ak.moving_part(name, bm, pivot, parent=None)   # aegis_kit.py:728
```

Elle pose l'origine de l'objet **sur son pivot** et accepte un `parent` — donc des **chaînes
articulées**. C'est ce qui fait bouger les ailes et les volets du Specter-9. Le cœur de ce brief
est de faire passer le Harvester dessus.

### Ce que dit la planche

`assets/reference/concepts/choir_harvester_concept_sheet.png`, à relire en entier :

- le corps est un **iris** : les pétales blindés se referment sur un noyau magenta. Un panneau
  montre l'état **ouvert** — pétales écartés, noyau plein cadre, rayonnant. Les deux états sont à
  atteindre par rotation des pétales sur leur charnière ;
- **trois** appendices, pas quatre : la **faux** (bras segmenté + lame en croissant), la **griffe à
  trois têtes** (un seul bras qui se divise en trois têtes à œil magenta — panneau de détail en bas
  à droite), et le **canon** (fût segmenté à bouches multiples, panneau de détail en bas au centre) ;
- un panneau d'**état endommagé** : fissures magenta et fumée. Utile plus tard, hors périmètre ici.

Le modèle actuel a `Arm_Scythe`, `Arm_Claw_L`, `Arm_Claw_R` et `Pod_Rear`. **Les deux griffes
fusionnent** en un seul bras à trois têtes, et le module arrière **devient** le canon.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/build_choir_harvester.py` | le script reforgé — il **est** la source de l'asset (ADR-0008) |
| `assets/imported/models/bosses/choir_harvester.glb` | régénéré via `./scripts/build-hull.sh choir_harvester` |
| `docs/forge/output/BRIEF-0039-report.md` | compte-rendu, **avec le tableau de dégagement** (voir Critères) |

### Contrat de noms — non négociable

Le code du combat est écrit contre cette liste. Un nom qui diverge casse l'intégration.

| Nœud | Nature | Pivot (repère d'auteur) |
|---|---|---|
| `Arm_Scythe` | `moving_part`, racine | épaule |
| `Scythe_Mid` | `moving_part`, `parent="Arm_Scythe"` | coude |
| `Scythe_Blade` | `moving_part`, `parent="Scythe_Mid"` | poignet |
| `Arm_Claw` | `moving_part`, racine | épaule |
| `Claw_Head_1`, `_2`, `_3` | `moving_part`, `parent="Arm_Claw"` | cou de chaque tête |
| `Arm_Cannon` | `moving_part`, racine | rotule |
| `Cannon_Barrel` | `moving_part`, `parent="Arm_Cannon"` | axe de recul du fût |
| `Petal_01`..`Petal_05` | `moving_part` | leur charnière actuelle |
| `Core` | objet statique | — |

Points d'attache à exposer, **en plus** de `Core_Center` et `Engine_C` déjà présents :

- `Muzzle_Claw_1`, `Muzzle_Claw_2`, `Muzzle_Claw_3` — à l'œil de chaque tête de griffe ;
- `Muzzle_Cannon` — à la bouche du fût.

`Muzzle_L` et `Muzzle_R` disparaissent : ils désignaient les deux griffes d'avant. ⚠️ Ils figurent
dans `required_attach_points` du `HullContract` — le contrat est à mettre à jour dans le même geste,
sinon l'auto-validation refusera l'export.

Les anciens marqueurs `Hinge_*` **disparaissent aussi** : le pivot vit désormais dans l'origine de
la pièce, et laisser des marqueurs concurrents inviterait un futur lecteur à s'en servir.

## Contraintes

- **IP** — interdits habituels de `CLAUDE.md`.
- **Palette** — charte §3, Null Choir (anthracite `#24252B`, violet `#452663`, ivoire `#DDDCD2`,
  magenta `#D93D9C`). L'iris ouvert doit lire comme une **source**, pas comme un trou clair.
- **Contrat de dimensions** — `HullContract` conservé : 4,55 (X) × 7,00 (Z) × 1,60 (Y max), budget
  25 000 triangles. La fusion des deux griffes libère du budget ; ne pas le dépenser en greebles
  fins, ils disparaissent sous le post-traitement rétro (960×540 + scanlines). Si la silhouette
  impose une dérive, **la signaler au compte-rendu** plutôt que d'élargir le contrat en silence.
- **Déterminisme** — régénérer par `./scripts/build-hull.sh choir_harvester`, jamais par un
  `blender45` nu : le `-t 1` est ce qui rend le `.glb` reproductible (mikktspace somme dans un ordre
  dépendant du nombre de threads).

### ⚠️ Le dégagement — la leçon la plus chère du projet

Le Specter-9 a coûté **quatre briefs** (0033 → 0036) sur ce seul point. Le pire cas : un marquage
posé à cheval sur une charnière a fait tomber le dégagement d'un volet de 18,5° à **2,8°**, sous la
valeur utilisée par le jeu — donc un volet qui traversait la coque. **Le contrat a validé sans un
mot**, parce que la boîte englobante au repos était parfaite : un défaut d'animation ne se voit pas
sur une pose fixe.

Conséquence pour ce brief : chaque pièce mobile doit être **mesurée à fond de course**, et le
résultat **rapporté**. Une pièce qui ne dégage pas est un défaut bloquant, pas une remarque.

Corollaire hérité : `.claude/resources/pratique-detail-en-fraction-de-corde.md` — poser le détail
**en fraction de corde, jamais en coordonnée absolue**. Deux reforges de plan, deux fois le même
dégât.

## Débattements visés par le gameplay

Ce sont les angles que le code appliquera. Le modèle doit les encaisser avec de la marge.

| Pièce | Mouvement | Amplitude |
|---|---|---|
| `Arm_Scythe` / `Scythe_Mid` / `Scythe_Blade` | réarme au-dessus du corps puis estoc vers l'avant | **±55°** cumulés sur la chaîne |
| `Arm_Claw` | balayage de visée latéral | **±35°** |
| `Claw_Head_1..3` | convergence des trois têtes vers la cible | **±20°** chacune |
| `Arm_Cannon` | pointage | **±30°** |
| `Cannon_Barrel` | recul au tir | **−0,25 m** en translation le long du fût |
| `Petal_01..05` | ouverture de l'iris | **0° → 78°** autour de leur charnière |

L'ouverture des pétales est la plus critique : à 78° ils doivent découvrir le noyau **entièrement**
vu de dessus (c'est l'angle de la caméra de jeu), sans se mordre entre eux ni mordre la lèvre du
puits.

## Critères d'acceptation

- [ ] Toutes les pièces du contrat de noms existent, avec les bons parents.
- [ ] `./scripts/build-hull.sh --check choir_harvester` : **0 octet divergent**.
- [ ] L'auto-validation de `ak.export_hull()` passe (bbox, budget, matériaux, pivot, attaches).
- [ ] Le compte-rendu porte un **tableau « pièce / débattement appliqué / marge minimale mesurée »**
      couvrant les six lignes ci-dessus. Une marge négative ou nulle est un échec.
- [ ] À 78°, le noyau est entièrement dégagé en vue de dessus — le vérifier par rendu, pas par calcul.
- [ ] Planche 4 vues produite (`blender45 -b -P tools/blender/render-hull.py -- <glb>`) et
      **regardée** avant de rendre (ADR-0006), plus **un rendu de l'iris ouvert**.
- [ ] Aucun `Hinge_*` ne subsiste ; `Muzzle_L`/`Muzzle_R` ont disparu du contrat comme du modèle.

## Hors périmètre

- **Ne pas** toucher au code GDScript, aux scènes `.tscn` ni aux Resources : le combat est écrit en
  parallèle, et deux écrivains sur les mêmes fichiers produisent des commits mélangés
  (`.claude/resources/pratique-ecrivain-unique.md`).
- **Ne pas** modéliser l'état endommagé (fissures, fumée) : il viendra par shader, plus tard.
- **Ne pas** produire de SFX ni de texture : un brief séparé couvrira la charge et le faisceau.
