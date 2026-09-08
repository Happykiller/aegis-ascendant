# BRIEF-0107 — Creuser le massif arrière : trois canaux d'échappement

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-09-08

## Objectif

Ouvrir **trois canaux d'échappement** dans le massif arrière de `stern_hull.glb`, en face des
trois groupes propulsifs, pour que leurs panaches ne traversent plus la coque du vaisseau qui
les porte.

## Contexte

### Le défaut, mesuré

Les trois panaches sont passés de trois boîtes additives à la plume de `ADR-0017` (violette,
14 m de long, 3,40 m de large). Ils sortent maintenant de l'intérieur de la tuyère — et **ils
entrent droit dans le massif arrière**.

> « On a du conflit avec la coque, je propose de la creuser pour laisser la place aux
> panaches » (opérateur, 2026-09-08, en jouant).

Les cotes, dérivées du réglage livré (`long_cortege_stern.tres`, `plume_cortege.tres`) et du
générateur (`build_stern.py`) :

| Ce qui compte | Valeur |
|---|---|
| Axe du panache | `y = −8,63` (assise moteur : `deck_y −11,85 + engine_seat.y 3,70 × k 0,87`) |
| Départ (bouche de tuyère + morsure) | `z = −4,03` |
| Pointe à plein régime | `z = −18,03` |
| Demi-largeur au ventre | **1,70 m** (`throat_radius 1,133 × belly_flare 1,50`) |
| Bande occupée en `y` | **−10,33 à −6,93** |
| Stations `x` des trois axes | **0** et **±10,28** |

Le massif arrière commence à `z = −8,60` et son plateau est à **`y = −8,40`**
(`AFT_PLATEAU_Y`). Le panache le rencontre donc à `z = −8,60` et, à partir de là,
**sa moitié basse (de −10,33 à −8,40) est dans la matière** sur les 3,40 m de profondeur du
massif. La pointe ressort au-delà de la poupe (`z = −12`), dans le vide — cette part-là va bien.

⚠️ **CE N'EST PAS UN DÉFAUT DE PLACEMENT DU PANACHE.** Sa bouche est lue dans le binaire
(`CTRL | Socket VFX flamme`, `z = −5,980`), son axe est celui du contrat de mariage de l'auteur.
C'est la coque qui n'a jamais réservé la place — le `BRIEF-0106` demandait « rien au-dessus des
berceaux », il ne disait rien de ce qui passe DERRIÈRE eux.

### Ce que la géométrie permet

`build_stern.py` :

```
AFT_Z          = -8.60     # le massif commence ici
AFT_PLATEAU_Y  = -8.40     # son plateau
AFT_CREST_Y    = -4.60     # sa crête, sur les flancs
SOLE_Y         = -12.00    # le dessous de la coque
TOWER_X        = (-5.40, 5.40) ; TOWER_Z = -10.05   # les deux tours d'échange
```

Il y a donc **3,60 m** entre le plateau (`−8,40`) et la semelle (`−12,00`) : de quoi creuser
sans percer.

## Ce qu'il faut faire

### 1. Trois canaux, aux stations des moteurs

| Cote | Valeur | Pourquoi |
|---|---|---|
| Stations `x` | **0** et **±10,28** | les axes des trois groupes (`engine_spacing`) |
| Demi-largeur | **≥ 2,20 m** | 1,70 de panache + 0,50 de garde |
| Plage `z` | **de −8,50 à la fin du massif** | 0,10 m avant la paroi, pour que l'entrée soit franche |
| Fond | **`y ≤ −10,90`** | 0,57 m sous le bord bas du panache (−10,33) |
| Épaisseur restante | **≥ 1,00 m** au-dessus de `SOLE_Y` | la coque ne se perce pas |

⚠️ **LE CANAL S'OUVRE VERS L'ARRIÈRE, PAS VERS LE HAUT.** Une simple encoche dans le plateau
laisserait une lèvre au niveau `z = −12` que le panache traverserait encore. Le canal doit
**déboucher** : à l'extrémité arrière du massif, il est ouvert sur le vide.

### 2. ⚠️ Les deux tours d'échange ne bougent pas

Elles sont à `x = ±5,40`, `z = −10,05`, socle de rayon 1,52. Les canaux latéraux vont de
`|x| = 8,08` à `12,48`, le canal central de `−2,20` à `+2,20` : **il reste 1,16 m de marge**
entre le bord d'un canal et le socle d'une tour. Vérifiez-le sur le binaire plutôt que sur cette
phrase — c'est la cote la plus serrée du lot.

### 3. Ce que le creusement doit RENDRE, et pas seulement enlever

⚠️ **UN TROU N'EST PAS UNE INSTALLATION.** Trois rainures lisses se liraient comme un défaut de
modélisation, exactement comme la dalle grise que le `BRIEF-0106` a remplacée. Un canal
d'échappement est une pièce : lèvre renforcée à l'entrée, parois nervurées, et — c'est le point
— **de quoi accrocher la lumière du panache**. Le panache est violet et non magenta
(`plume_cortege.tres`) : c'est la seule lumière violette de tout le niveau, et une paroi qui la
capte donne au massif la profondeur qu'une rainure plate n'aura jamais.

⚠️ **PAS D'ÉMISSIF DANS LES CANAUX.** `CortegeStern.blackout()` éteint tout ce qui porte
`AA_Emissive_Engine` quand la propulsion meurt ; un canal qui brillerait de lui-même resterait
allumé sur un vaisseau mort, et **rien ne le signalerait** (ni erreur, ni test). La lumière doit
venir du panache, donc de la matière qui la réfléchit — `AA_Hull` et `AA_Greeble`.

## Texture (ADR-0028)

**Aucune.** Le Long Cortège entier est en PBR par facteurs, zéro image, et son harnais échoue le
build si une texture apparaît.

## Animation (ADR-0046 §6)

**Figée.** C'est de la structure.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/build_stern.py` | le générateur, avec sa fonction de canaux |
| `assets/imported/models/backgrounds/stern_hull.glb` | la carène, creusée |
| `docs/forge/output/BRIEF-0107-report.md` | mesures des trois canaux, marges aux tours, triangles |
| `docs/forge/output/BRIEF-0107-planche.png` | rendus à la caméra du jeu |

## Critères d'acceptation

- [ ] **Aucune matière dans le volume des trois panaches**, mesuré sur le binaire : pour chaque
      station `x ∈ {0, ±10,28}`, aucun triangle au-dessus de `y = −10,90` dans
      `|x − station| ≤ 2,20` et `z ≤ −8,50`. ⚠️ Découpé, pas testé par sommets : un triangle
      peut traverser un volume sans qu'aucun de ses trois sommets n'y soit — c'est le harnais
      d'emprise du `BRIEF-0106` §5, réutilisez-le.
- [ ] **Le canal débouche** : à l'extrémité arrière du massif, il est ouvert.
- [ ] **≥ 1,00 m de matière** entre le fond du canal et `SOLE_Y` (−12,00).
- [ ] **Les deux tours d'échange sont intactes** et leur marge au canal le plus proche est
      **mesurée et nommée** (attendu : 1,16 m).
- [ ] **La jonction à `s = 500` est inchangée**, au micron : c'est le critère qui prime depuis le
      `BRIEF-0106`, et le harnais `_assert_junction()` existe déjà.
- [ ] **Rien de neuf dans l'emprise des berceaux** (`|x| ≤ 15,78` et `|z| ≤ 8,00` au-dessus du
      pont) : le massif est à `z ≤ −8,60`, donc dehors — mais le vérifier coûte une ligne.
- [ ] **Aucun `AA_Emissive_Engine` dans les canaux**, compté sur le binaire.
- [ ] **Budget** : la carène est à 2 514 triangles sur 20 000. Il y a toute la place ; dites ce
      que les canaux coûtent.
- [ ] **Déterminisme** : trois exécutions, zéro octet divergent.
- [ ] **Rendu et REGARDÉ à la caméra du jeu** (`ADR-0006`), **avec les trois panaches allumés** —
      c'est la seule vue qui prouve quoi que ce soit ici. Une planche sans panache montrerait
      trois rainures et ne dirait rien du problème qu'on corrige.

## Hors périmètre

- **Le code de jeu.** Les panaches, leur réglage et leur montage sont livrés et testés (999
  tests) : ne toucher à aucun `.gd` ni `.tres`.
- **Les nacelles, berceaux, verrous** : ils ne changent pas.
- **Le corridor** et sa jonction.
