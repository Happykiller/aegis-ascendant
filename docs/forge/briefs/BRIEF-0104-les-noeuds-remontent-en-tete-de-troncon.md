# BRIEF-0104 — Les nœuds remontent en tête de leur tronçon

- **Statut** : à faire
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-09-06

## Objectif

Déplacer les cinq marqueurs `Spine_01..05` du **milieu** de leur tronçon vers son **début**.
Cinq nombres dans une table, et rien d'autre — mais c'est ce qui rend visible une mécanique que
le joueur ne peut aujourd'hui pas voir.

## Contexte

### Ce que l'opérateur a demandé

> « *Les nœuds ne sont pas logiques : au début d'un tronçon, on devrait avoir un nœud. Et après,
> ce nœud gère les lignes d'alimentation sur tout le tronçon à venir. Et donc, quand on détruit
> un nœud, on devrait voir les tronçons lumineux violets derrière s'éteindre.* »

### ⚠️ LA MOITIÉ MOTEUR EST DÉJÀ FAITE — CE LOT NE LIVRE QUE DE LA GÉOMÉTRIE

`CortegeSpineNode.weakened_section()` a été retournée le 2026-09-06 (commit `5288dd4`) : un nœud
éteint désormais **son propre** tronçon, conduits et tourelles. Aucun `.gd` n'est à toucher ici.

Et l'ancienne règle — éteindre le tronçon **suivant** — n'était pas absurde : elle refusait de
récompenser après coup un joueur qui a déjà traversé le danger. Elle était juste **tant que le
nœud siégeait au milieu du sien**, ce qu'il fait aujourd'hui. Mesuré, les cinq sont à **54, 52,
60, 38 et 59 %** du début de leur tronçon. La conséquence était fatale à la lecture : ce qui
s'éteignait se trouvait quarante mètres devant, **hors de l'écran**. « Quand je détruis un nœud,
pas de changement » — il ne pouvait structurellement rien voir.

Retourner la règle sans remonter les nœuds ne suffit pas : le joueur abattrait le nœud à
mi-tronçon et n'éteindrait que la moitié de couloir **derrière** lui. Les deux moitiés se
tiennent, et c'est la seconde que ce lot livre.

## Ce qu'il faut faire

### 1. Une seule table change : `SPINES`

Dans `tools/blender/build_long_cortege.py` :

```python
SPINES: tuple[float, ...] = (54.1, 151.8, 260.2, 338.5, 458.8)   # avant
SPINES: tuple[float, ...] = (46.0, 103.0, 203.0, 305.0, 406.0)   # après
```

Ces cinq valeurs ne sont pas un souhait : elles ont été **mesurées contre les gardes réelles du
module**, en appelant `_assert_pits_are_clear()`, `spine_seat_y()` et `_scales()` sur la coque.
Le tableau ci-dessous donne la marge de chacune sur les deux gardes qui la contraignent.

| Marqueur | avant | après | +/début | fond plat dispo (il faut 0,66) | tranchée (il faut 0,35) |
|---|---|---|---|---|---|
| `Spine_01` | 54,1 | **46,0** | +46,0 | 0,691 (+0,031) | 0,409 (+0,059) |
| `Spine_02` | 151,8 | **103,0** | +3,0 | 0,706 (+0,046) | 0,530 (+0,180) |
| `Spine_03` | 260,2 | **203,0** | +3,0 | 0,706 (+0,046) | 0,530 (+0,180) |
| `Spine_04` | 338,5 | **305,0** | +5,0 | 0,773 (+0,113) | 0,530 (+0,180) |
| `Spine_05` | 458,8 | **406,0** | +6,0 | 0,840 (+0,180) | 0,530 (+0,180) |

### 2. ⚠️ POURQUOI TROIS DES CINQ NE SONT PAS À +2,8, ET POURQUOI `Spine_01` EST À +46

Ce ne sont pas des arrondis de confort. Chaque écart a une cause mesurée, et **la connaître évite
de « corriger » un nombre qui est déjà à sa place** :

- **`Spine_01` ne peut PAS remonter plus haut : le fuseau de proue est trop étroit.** Le berceau
  fait 1,32 m de large et le fond plat du canal est contracté par `_scales()`. En dessous de
  **s = 44,1** le berceau ne tient plus dans le fond, et `_audit()` arrête le build en le disant.
  46,0 laisse 31 mm de marge — la plus mince des cinq, et c'est volontaire.

  **Et ce n'est pas une reddition, c'est la bonne station.** Les quatre voies lumineuses du canal
  ne s'allument, elles aussi, qu'à partir de **s ≈ 41** (`_canal_lane()` : la voie interne à 28,
  l'externe à 42). L'artère du tronçon 1 commence là. Le nœud à 46 siège donc **quatre mètres
  après le début de ce qu'il alimente** — ce qui est exactement la lecture demandée, et le
  tronçon 1 n'a rien d'allumé en amont à éteindre.

- **`Spine_04` est bloqué à 304,1 par la fosse de maintenance de s = 292.** Elle est à bâbord,
  de |x| = 2,20 à 6,80, et son `PIT_KEEPOUT` de 2,20 m **atteint l'axe** : x_hi vaut exactement
  0,0. Additionnée à `APRON_SPINE`, son emprise interdit tout l'intervalle 280–304.
  `_assert_pits_are_clear()` refuse 303,0 en toutes lettres — vérifié.

- **`Spine_05` est bloqué à 405,1 par la fosse de s = 393**, même mécanisme, tribord.

⚠️ **Ne pas déplacer les fosses pour gagner deux mètres.** Deux d'entre elles ont déjà été
recalées par cette assertion (l'en-tête de `PITS` le raconte) ; +5 et +6 mètres, à 2,4 u/s, font
deux secondes d'entrée de tronçon. Le jeu n'y perd rien, la coque y perdrait un arbitrage.

### 3. Ce qui bouge par ricochet, et qu'il faut laisser bouger

- **Le Y des cinq marqueurs.** `spine_seat_y()` le recalcule : `Spine_01` passe de −4,7530 à
  **−4,9075** (le fond du canal monte dans le fuseau), les quatre autres à −4,5800. C'est le
  comportement attendu — le marqueur porte l'assise, il ne la choisit pas.
- **Les emprises `APRON_SPINE` et donc les plages nues.** Mesuré : **18 plages, dont 11 de 12 m
  ou plus** (le cliquet en exige 8), **53,4 % de longueur calme** contre 58,6 % aujourd'hui. Le
  rythme tient ; l'imprimer dans le rapport.
- **Le vocabulaire modulaire semé autour des nœuds** suit ses emprises. Normal.

### 4. ⚠️ CE QUI NE DOIT PAS BOUGER D'UN DIXIÈME DE MILLIMÈTRE

`Turret_01..17`, `Bay_01..07` et `Ambry`. Le moteur les adresse par leur nom et pose dessus
dix-sept affûts, sept hangars et dix-neuf batteries légères ; une translation silencieuse les
emmènerait tous. **Le diff du contrat de noms doit être vide sauf sur les cinq `Spine_NN`.**

Les branches de `BRIEF-0103` non plus : elles s'enracinent à la station de **leur tourelle**
(`BRANCH_ROOT_X = 1,12`), pas à celle d'un nœud. Elles ne se redessinent pas.

## Texture (ADR-0028)

**Aucune.** Rien de neuf n'est modelé : cinq marqueurs se déplacent sur une coque déjà dépliée.

## Animation (ADR-0046 §6)

**Figée.** Un marqueur est un repère ; ce qui bouge est le vaisseau sous la caméra.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/build_long_cortege.py` | la table `SPINES`, et le commentaire qui dit pourquoi ces cinq valeurs |
| `assets/imported/models/backgrounds/long_cortege.glb` | la coque régénérée |
| `docs/forge/output/BRIEF-0104-report.md` | mesures, diff des marqueurs, plages nues, captures |

## Provenance

Mettre à jour **la ligne existante** `long_cortege_hull` (ne pas la dupliquer).

## Critères d'acceptation

- [ ] **Le diff du contrat de noms ne montre QUE les cinq `Spine_NN`**, au 1/10 de mm sur les
      vingt-cinq autres. C'est le critère qui prime.
- [ ] **Les cinq stations livrées, avec leur marge mesurée** sur les deux gardes (fond plat,
      tranchée) — et non recopiées de ce brief.
- [ ] `_assert_pits_are_clear()` passe, et le rapport **nomme** les deux fosses qui ont contraint
      `Spine_04` et `Spine_05`. Si un jour l'une bouge, on saura ce qui tenait ces deux nombres.
- [ ] **Nombre de plages nues et part calme imprimés**, cliquet des 8 plages vert.
- [ ] `./scripts/build-hull.sh --check long_cortege` : **zéro octet divergent**, trois exécutions.
- [ ] **`TEXCOORD_0` compté**, **zéro image embarquée**.
- [ ] **Rendu et REGARDÉ à la caméra du jeu** (`ADR-0006`) : pour **au moins deux tronçons**, une
      vue à l'**entrée du tronçon** montrant le nœud dans le cadre dès la frontière franchie —
      c'est toute la demande. Livrer chaque vue **alimentée** et **nœud abattu** : l'état éteint
      est celui qui doit rester lisible, et celui que personne ne pense à regarder.
- [ ] **Le tronçon 1 est montré aussi**, avec sa réponse honnête : le nœud à +46 et le début de
      l'artère à ≈ 41 dans le même cadre, ou la mesure qui dit qu'ils n'y tiennent pas.

## Hors périmètre

- **Le code de jeu** : `weakened_section()` est déjà retournée. Ne toucher à aucun `.gd`,
  `.tscn` ni `.tres`.
- **Les fosses, les tourelles, les hangars, Ambry, la citadelle, les branches** : rien d'autre
  que `SPINES` ne change.
- **Le kit `spine_kit.glb`** : il est modelé sur le plan Y = 0 du marqueur, il suit tout seul.
