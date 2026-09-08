# BRIEF-0109 — La poupe cède la place : retirer le procédural, poser des repères

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-09-08

## Objectif

Faire de la place, dans `stern_hull.glb`, aux pièces livrées et réduites au `BRIEF-0108` — et
donner au code **des repères pour les poser**, au lieu de cotes écrites à la main.

Deux gestes, et le second est le plus important :

1. **Retirer les quatre pylônes procéduraux** (`build_pylons()`), qui vont être remplacés.
2. **Poser des repères `CTRL | `** aux quatre emplacements de pylône **et** au collecteur
   d'artère.

## Contexte

### Ce qui est remplacé, et le rapport de force

| Pièce actuelle | Triangles | Ce qui la remplace |
|---|---|---|
| Les 4 pylônes de rive (`build_pylons`) | **240 pour les quatre**, soit 60 chacun | `stern_pylon.glb` — **2 612**, 5,30 m, 3 clips animés |
| — (le collecteur n'est pas remplacé) | — | il est **habillé** par des `artery_hose.glb` (320 tri) |

Soixante triangles par pylône contre 2 612 : c'est un facteur 43, plus trois animations
(`Service`, `Refroidissement`, `Maintenance`) que la version procédurale n'a pas du tout.

**Budget** : la poupe consomme **64 894** triangles sur 80 000. Quatre pylônes livrés (10 448) et
quatre flexibles (1 280) portent le total à **75 982**, moins les 240 retirés → **75 742**. Il
reste **4 258**. C'est serré et c'est assumé : dites-le si votre travail le dépasse.

### ⚠️ POURQUOI DES REPÈRES, ET PAS UNE TABLE DANS LE CODE

Le chantier de l'artère vient de payer cette leçon. Les douze conduites du corridor se posent par
**station calculée**, parce que la coque n'a aucun repère pour elles — et leur assise (`y = −4,30`)
est **la seule cote de tout le chantier qui ne vienne pas de l'asset**. Elle est gardée par un
test qui la compare aux marqueurs voisins, mais c'est une dette, écrite comme telle
(`.claude/resources/pratique-poser-sans-marqueur.md`).

Ici, on ne la reprend pas. **La coque dit où les pièces vont**, comme elle le fait déjà pour les
dix-sept tourelles, les sept ponts, les cinq nœuds et les dix sockets d'ancrage.

## Ce qu'il faut faire

### 1. Retirer `build_pylons()`

Les quatre fuseaux étagés des étagères de rive (`PYLON_Z = (−0,40 ; −6,00)`, bandes 2 et 3)
disparaissent. **L'étagère reste** : c'est elle qui portera le vrai pylône.

⚠️ **VÉRIFIEZ CE QUI S'APPUYAIT DESSUS.** Le bandeau de flanc `AA_Panel` posé par
`build_pylons()` part avec — s'il servait à autre chose qu'à habiller le fuseau, dites-le au lieu
de le supprimer en silence.

### 2. Quatre repères de pylône

`CTRL | Pylone 01` à `04`, aux stations exactes des fuseaux retirés, **posés sur la surface** de
l'étagère (le `y` échantillonné, pas une constante) et orientés comme la pièce doit l'être.

Le pylône livré fait **2,75 × 5,30 × 2,06 m**, son origine à sa base. Le repère marque **le pied**.

⚠️ **ET IL DOIT TENIR SOUS LE PLAFOND.** `CEILING_Y = −3,20` : un pylône de 5,30 m posé à
`y = −8,60` culmine à −3,30, soit 10 cm de marge. Mesurez-la sur le binaire et donnez-la ; si un
repère la fait passer sous zéro, c'est le repère qui descend, pas le plafond qui monte.

### 3. Deux à quatre repères de collecteur

`CTRL | Liaison 01` à `04`, à la jonction de l'artère et des trois groupes — là où le collecteur
aboutit. Ils porteront des `artery_hose.glb` (0,28 × 0,61 × 2,74 m), en décor.

⚠️ **DES FLEXIBLES, PAS DES CONDUITES, ET C'EST UNE RÈGLE DE LECTURE.** Le corridor vient
d'apprendre au joueur qu'une **conduite se coupe** — douze d'entre elles sont des cibles. En poser
sur la poupe, où elles ne serviraient à rien, lui apprendrait l'inverse au pire moment. Le
flexible, lui, est du décor partout : il ne ment pas.

⚠️ **RIEN DANS L'EMPRISE DES BERCEAUX** (`|x| ≤ 15,78` et `|z| ≤ 8,00` au-dessus du pont), et
**rien dans les trois canaux d'échappement** du `BRIEF-0107`. Les deux harnais existent.

## Texture / Animation

**Aucune texture.** Les repères ne portent pas de maillage — ce sont des nœuds vides, comme
`CTRL | Socket VFX flamme`.

## Livrables

| Fichier | Description |
|---|---|
| `tools/blender/build_stern.py` | sans `build_pylons()`, avec les repères |
| `assets/imported/models/backgrounds/stern_hull.glb` | la carène |
| `docs/forge/output/BRIEF-0109-report.md` | positions des repères, marge au plafond, triangles |
| `docs/forge/output/BRIEF-0109-planche.png` | rendus, **avec les pièces du BRIEF-0108 posées sur les repères** |

## Critères d'acceptation

- [ ] **Les quatre pylônes procéduraux ont disparu** et l'étagère de rive est intacte.
- [ ] **Quatre `CTRL | Pylone NN`**, `y` échantillonné sur la surface, position donnée au
      centième. La **marge au plafond** (`−3,20`) est mesurée et nommée pour chacun.
- [ ] **Deux à quatre `CTRL | Liaison NN`**, hors emprise des berceaux et hors canaux.
- [ ] **La jonction à `s = 500` est inchangée**, au micron (`_assert_junction()`).
- [ ] **Les trois canaux d'échappement sont intacts** : 0 m² de matière dans les volumes de
      panache, le harnais du `BRIEF-0107` existe.
- [ ] **Budget** : le compte après, et ce qu'il reste sur 80 000 une fois les pièces posées.
- [ ] **Déterminisme** : trois exécutions, zéro octet divergent.
- [ ] **Rendu et REGARDÉ à la caméra du jeu** (`ADR-0006`), **avec `stern_pylon.glb` et
      `artery_hose.glb` posés sur les repères** — une planche de repères vides ne prouve rien.

## Hors périmètre

- **Le code de jeu** : c'est le concepteur qui montera les pièces sur vos repères. Ne touchez à
  aucun `.gd`, `.tscn` ni `.tres`.
- **Les pièces elles-mêmes** : livrées et réduites au `BRIEF-0108`, elles ne changent pas.
- **Les deux tours d'échange thermique** et le reste du massif arrière.
