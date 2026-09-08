# BRIEF-0110 — La poupe troque ses formes simples contre les pièces livrées

- **Statut** : livré et intégré
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-09-08

## Objectif

Remplacer **tout le décor procédural de la poupe** par les pièces tierces livrées et réduites au
`BRIEF-0108`, et **régénérer richement** les familles qu'aucune pièce livrée ne peut remplacer.

> « Les modèles sont beaux, au lieu de nos formes simples » (opérateur, 2026-09-08).

C'est une demande de **densité perçue**, pas de comptage : la poupe doit cesser de se lire comme
un assemblage de boîtes.

## Ce qui est en place aujourd'hui, mesuré

| Famille | Triangles | Ce qu'elle fait | Sort |
|---|---:|---|---|
| `skin` | 910 | le loft de la carène | **ne bouge pas** |
| `towers` | 524 | deux tours d'échange thermique | **régénérer** |
| `manifold` | 436 | le collecteur d'artère | **remplacer** par des conduites |
| `rim_clamps` | 312 | la chaîne de brides du rebord | **remplacer** par des flexibles |
| `pylons` | 240 | quatre pylônes de rive | **remplacer** par `stern_pylon` |
| `shoulders` | 96 | deux épaulements de proue | **régénérer** |
| `glow` | 48 | les tirets de l'anneau | ne bouge pas |
| `apron` | 12 | la dalle d'assise | ne bouge pas |
| **canaux** | 668 | les trois canaux d'échappement (`BRIEF-0107`) | **ne bougent pas** |

**Budget** : la poupe consomme **64 894** triangles sur 80 000. Il en reste **15 106**, et le
retrait de `manifold + rim_clamps + pylons + towers + shoulders` (1 608) en libère autant :
**16 714 disponibles**.

## Ce qu'il faut faire

### 1. Le collecteur d'artère — conduites et flexibles

C'est le remplacement le plus évident et le plus visible : le collecteur est **au centre du bas
du cadre**, l'endroit que le joueur fixe le plus longtemps, et l'artère y aboutit sur les trois
groupes.

`artery_conduit.glb` (652 tri, 2,78 m) et `artery_conduit_bend.glb` (648) **sont** un collecteur :
c'est leur planche d'origine. Composez-en la jonction, accompagnée de `artery_hose.glb` (320) pour
les liaisons souples.

⚠️ **DES REPÈRES, PAS DE LA GÉOMÉTRIE.** Vous ne posez pas les pièces dans le `.glb` : vous posez
`CTRL | Collecteur NN` et `CTRL | Liaison NN`, et le code monte les instances. Une pièce dupliquée
dans la carène coûterait ses triangles **autant de fois qu'elle apparaît** ; instanciée, elle n'est
en mémoire qu'une fois.

⚠️ **ET L'ORIGINE DES PIÈCES N'EST PAS DANS LES PIÈCES.** La racine d'`artery_conduit` porte
encore sa translation dans le module d'origine — `(−0,36 ; 1,00 ; 1,38)`. Le code compense en
mesurant la boîte englobante (bas sur le repère, centre sur le repère). **Vos repères marquent
donc le point où le BAS de la pièce doit se poser**, pas son origine de fichier. Dites dans votre
rapport comment vous avez vérifié que la pose tombe juste.

### 2. La chaîne de brides du rebord — des flexibles

312 triangles de colliers identiques le long du rebord. `artery_hose.glb` fait exactement ça, en
mieux, avec ses colliers et ses brins.

⚠️ **PAS UNE PAR BRIDE.** Un flexible tous les deux mètres sur 40 m de rebord, c'est vingt
instances : gardez le rythme irrégulier de la chaîne actuelle et **laissez des vides**. C'est la
règle du `BRIEF-0094` — « un module de relief ne se pose que dans l'emprise d'une installation ».

### 3. Les quatre pylônes de rive — `stern_pylon`, à la hauteur qui rentre

⚠️ **LE PYLÔNE LIVRÉ NE RENTRE PAS À 5,30 m, ET C'EST MESURÉ** (`BRIEF-0109`). Le ciel sous
`BUILD_CEILING_Y = −3,20` :

| Emplacement | Assise | Ciel |
|---|---:|---:|
| Étagère de rive B1 | −6,60 | **3,40 m** |
| Étagère de rive B2 | −5,60 | **2,40 m** |
| Étagère de rive B3 | −4,60 | **1,40 m** |
| Épaulement de proue (gradin bas) | −5,90 | 2,70 m |

L'opérateur veut le pylône **dans le jeu**. Deux libertés vous sont données, et vous choisissez :

- **le reconstruire à la hauteur de son emplacement** — comme au `BRIEF-0108`, en SUPPRIMANT ce
  qui n'existerait plus, pas en rétrécissant ;
- **choisir d'autres emplacements** que les quatre stations actuelles, si un endroit de la poupe
  lui donne plus de ciel. La bande B1 en offre 3,40 : c'est là que la pièce sera la plus haute.

⚠️ **ET IL DOIT SE LIRE À 32,7 px/m.** Le `BRIEF-0109` a échoué exactement là : enterré aux trois
quarts, il rendait un treillis mince, moins lisible que le fuseau de 60 triangles qu'il
remplaçait. **Le critère n'est pas « il est posé », c'est « il se lit mieux qu'avant »** — et la
comparaison avant/après au même cadrage en fait partie.

### 4. Les tours d'échange et les épaulements — régénérer

Aucune pièce livrée ne leur correspond. Elles ne changent pas de nature : elles **s'enrichissent**,
avec le budget qui se libère.

- **Tours d'échange** (524 pour deux) : elles se dressent sur le plateau du massif, qui offre
  **5,20 m** de ciel — le seul volume vraiment haut de la poupe. Donnez-leur la silhouette que
  cette hauteur permet.
- **Épaulements de proue** (96 pour deux) : ils sont **au premier plan**, à `z ∈ [8,00 ; 9,40]`,
  et ce sont trois boîtes empilées. À 45,8 px/m ils occupent une place que leur détail ne justifie
  pas.

⚠️ **PAS UN TAPIS DE GREEBLES.** La spec §20 : « concentrer le travail sur peu de pièces ». C'est
le défaut que le `BRIEF-0094` a corrigé sur 500 m de coque, et la règle qui en est sortie tient
ici.

### 5. Douze repères pour le corridor — la dette de l'artère

Dans `build_long_cortege.py` cette fois : `CTRL | Conduite 01` à `12`, aux stations de
`CortegeArtery.CONDUITS` (30, 58, 95, 138, 163, 192, 240, 277, 314, 358, 394, 435), aux `x`
alternés `±3,60` / `±4,40`, **`y` échantillonné sur la peau**.

⚠️ **C'EST LA SEULE COTE DU CHANTIER DE L'ARTÈRE QUI NE VIENNE PAS DE L'ASSET**, et elle s'est vue
à l'écran : les douze conduites sont posées à `y = −4,30` constant alors que la peau du corridor
**se rétrécit** avec la station. Le test qui la surveillait comparait aux marqueurs voisins et
laissait passer un écart visible.

## Texture (ADR-0028) / Animation (ADR-0046)

**Aucune texture.** Les repères sont des nœuds vides. La géométrie régénérée est **figée**.

## Livrables

| Fichier | Description |
|---|---|
| `tools/blender/build_stern.py` | familles retirées, familles régénérées, repères posés |
| `tools/blender/build_long_cortege.py` | les douze `CTRL \| Conduite NN` |
| `assets/imported/models/backgrounds/stern_hull.glb` | la carène |
| `assets/imported/models/backgrounds/long_cortege.glb` | le corridor |
| `assets/imported/models/backgrounds/stern_pylon.glb` | reconstruit s'il change de taille |
| `docs/forge/output/BRIEF-0110-report.md` | mesures, repères, budget, avant/après |
| `docs/forge/output/BRIEF-0110-planche.png` | rendus **avec les pièces instanciées sur les repères** |

## Critères d'acceptation

- [ ] **Les cinq familles ont disparu ou changé**, et le rapport dit laquelle a quel sort.
- [ ] **Tous les repères sont posés**, `y` échantillonné, position au centième, et **ils marquent
      le BAS de la pièce**.
- [ ] **Le pylône se LIT mieux qu'avant** : capture avant/après au même cadrage, à la caméra du
      jeu. ⚠️ C'est le critère qui a fait échouer le `BRIEF-0109` — ne le rendez pas vert par
      politesse, dites-le s'il ne l'est pas.
- [ ] **Budget** : ≤ 80 000 pour la poupe entière, pièces instanciées comprises, compté par
      famille.
- [ ] **La jonction à `s = 500` est inchangée** au micron, et **les trois canaux d'échappement
      sont intacts** (0 m² dans les volumes de panache).
- [ ] **Rien de neuf dans l'emprise des berceaux.**
- [ ] **Les douze repères du corridor** existent, et leur `y` diffère bien d'une station à
      l'autre — c'est la preuve qu'ils sont échantillonnés et non constants.
- [ ] **Déterminisme** : trois exécutions, zéro octet divergent, sur les DEUX générateurs.
- [ ] **Rendu et REGARDÉ à la caméra du jeu** (`ADR-0006`), avec les pièces instanciées.

## Hors périmètre

- **Le code de jeu** : le concepteur monte les pièces sur vos repères. Aucun `.gd`, `.tscn`, `.tres`.
- **La peau, la dalle, l'anneau lumineux, les canaux d'échappement.**
- **Les nacelles, berceaux, verrous et bras** : livrés au `BRIEF-0105`, intouchables.
