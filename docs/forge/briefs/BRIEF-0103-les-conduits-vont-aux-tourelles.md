# BRIEF-0103 — Le courant se voit : des conduits du canal jusqu'aux tourelles

- **Statut** : livré
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-09-06

## Objectif

Relier **visuellement** l'épine dorsale aux tourelles qu'elle alimente. Aujourd'hui le canal
central brille, les tourelles tirent, et **rien ne dit que les deux sont branchés** — alors que
le jeu les relie depuis des semaines.

## Contexte

### Ce que l'opérateur a demandé, et pourquoi il a raison

> « *On a les épines dorsales avec l'espèce de colonne vertébrale avec une lumière violette, et
> les tours, on ne voit toujours pas visuellement un rapport entre les trois. Je propose que de
> la colonne vertébrale il y ait aussi des lignes violettes qui vont vers les tours, au moins
> les grosses. Et quand on détruit un des nœuds, il faut que les lignes de la section concernée
> s'éteignent.* »

### ⚠️ LA MÉCANIQUE EXISTE DÉJÀ EN ENTIER — C'EST L'IMAGE QUI MANQUE

Abattre un nœud d'épine fait **déjà** tomber les tourelles du tronçon suivant à **45 % de vitesse
de rotation** et **2,6 fois plus lentes à tirer** (`turret_weakened_turn_factor`,
`turret_weakened_interval_factor`). C'est testé, borné par un invariant, et le journal l'annonce.
Le joueur, lui, ne peut relier ni l'un ni l'autre à son geste.

**Et l'extinction est faite** (commit `4273f1f`) : le matériau émissif de chaque tronçon passe en
veine sombre quand son nœud tombe. Elle n'attend que des conduits à éteindre.

Ce lot ne livre donc **que de la géométrie**. Aucune ligne de code de jeu.

## Ce qu'il faut faire

### 1. Une branche par tourelle, du canal jusqu'à son emplacement

Les cinq nœuds d'épine sont dans le canal, sur l'axe (`SPINES = 54,1 · 151,8 · 260,2 · 338,5 ·
458,8`, `CANAL_FLOOR_Y = −4,58`, `CANAL_RIM_X = 1,70`). Les dix-sept tourelles sont sur les
flancs, de |x| = 6,00 à 12,40.

Une branche part donc **du bord du canal** et court jusqu'à l'emplacement de sa tourelle. Elle
suit le pont — elle ne vole pas au-dessus.

⚠️ **Les cotes des marqueurs se lisent SUR LE `.glb`, pas sur la table `TURRETS`.** Les deux
diffèrent jusqu'à 2,30 m (`Turret_11` : 10,10 annoncé, 12,40 posé) et quatre emplacements
tombent hors des deux paliers de pont. Une branche tirée sur la table arriverait à côté.

### 2. Le matériau décide de tout : `AA_Emissive_Engine`, et rien d'autre

⚠️ **C'est la seule chose qui rend l'extinction possible.** `CortegeSkin` reconnaît ce slot par
son nom et lui donne une copie **par tronçon** ; c'est cette copie que le moteur baisse quand le
nœud tombe. Une branche peinte dans un autre slot resterait allumée sur un vaisseau mort, et
**rien ne le signalerait** — ni erreur, ni test.

Le corps de la branche (la gaine, le caniveau) peut être en `AA_Greeble` ; seule la **veine**
est émissive.

### 3. Les trois lourdes sont plus grosses, et ça doit se voir

`Turret_08` (s 263,0), `Turret_12` (380,0) et `Turret_15` (463,3) sont les trois emplacements
lourds. Leur branche est **plus large** que celle d'une standard — c'est ce qui fait lire une
hiérarchie d'alimentation, et ça répond au « au moins les grosses tours » de la demande.

### 4. ⚠️ Où une branche N'A PAS le droit d'aller

- **Dans le disque de 2,50 m autour d'un marqueur de tourelle** — `_turret_clash()`, garde posée
  par `BRIEF-0101` : rien de saillant sous un affût, sinon il s'y enfonce. La branche **s'arrête
  au bord du disque**, ce qui est d'ailleurs la bonne lecture : le courant arrive à la
  plateforme, pas sous la tourelle.
- **Dans l'ouverture d'un pont d'envol** (`_bay_clash`) ni dans un puits (`_pit_clash`).
- **Au-dessus de `BUILD_CEILING_Y = −3,20`.**
- **En travers du canal** : une branche dessert son propre flanc.

### 5. Ce qui ne doit pas régresser

Le harnais de `BRIEF-0101` mesure le dégagement des dix-sept emplacements **sur le binaire** et
échoue le build si un module repasse au-dessus d'une assise. Il doit rester vert.

## Texture (ADR-0028)

**Aucune.** Le Long Cortège entier est en PBR par facteurs, zéro image, et son harnais échoue le
build si une texture apparaît. La veine tire sa lumière de son matériau émissif, habillé en jeu
par `CortegeSkin` avec la carte `cortege_emissive` déjà en place — donc rien à fournir.

**Dépliage** : `ak.box_project_uv()` à la densité de la peau (0,200 tuile/m, valeur à relire dans
le fichier). `TEXCOORD_0` compté dans le `.glb`.

## Animation (ADR-0046 §6)

**Figée.** Une branche est de la tôle et une veine de la lumière : rien ne bouge. Ce qui varie —
l'intensité — est un réglage de matériau poussé par le moteur, pas une image clé.

⚠️ **Et les trente marqueurs ne bougent pas d'un dixième de millimètre.** `Turret_01..17`,
`Bay_01..07`, `Spine_01..05`. Le moteur les adresse par leur nom ; une translation silencieuse
déplacerait dix-sept tourelles, sept hangars et cinq nœuds sans qu'une ligne de code ne change.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/build_long_cortege.py` | la famille de branches, et son harnais |
| `assets/imported/models/backgrounds/long_cortege.glb` | la coque régénérée |
| `docs/forge/output/BRIEF-0103-report.md` | mesures, tracés, ce qui n'a pas pu être desservi |

## Provenance

Mettre à jour **la ligne existante** `long_cortege_hull` (ne pas la dupliquer) : nombre de
branches, emplacements desservis et non desservis, part émissive ajoutée.

## Critères d'acceptation

- [ ] **Les trente marqueurs sont inchangés**, au 1/10 de mm, diff du contrat de noms **VIDE**.
      C'est le critère qui prime.
- [ ] **Chaque branche est en `AA_Emissive_Engine` pour sa veine** — compté sur le binaire, par
      tronçon. ⚠️ Sans ça l'extinction ne prend pas, et rien ne le dira.
- [ ] **Aucune branche dans le disque de 2,50 m** d'un marqueur de tourelle : le harnais de
      `BRIEF-0101` reste vert, et la mesure est refaite sur le `.glb` livré.
- [ ] **Aucune branche dans une ouverture de pont ni dans un puits**, mesuré.
- [ ] **Combien de tourelles sont desservies, et lesquelles ne le sont pas** — avec la raison.
      Un emplacement inatteignable est un résultat, pas un échec ; le cacher en est un.
- [ ] `./scripts/build-hull.sh --check long_cortege` : **zéro octet divergent**, trois exécutions.
- [ ] **`TEXCOORD_0` compté**, **zéro image embarquée**.
- [ ] **Rendu et REGARDÉ à la caméra du jeu** (`ADR-0006`), avec les tourelles réelles montées :
      une branche se juge sur sa lisibilité à 45,8 px/m, pas sur une vue de dessus. Livrer aussi
      une vue **éteinte** — c'est l'état qui doit rester lisible, et c'est celui que personne ne
      pense à regarder.

## Hors périmètre

- **Le code de jeu** : l'extinction est faite. Ne toucher à aucun `.gd`, `.tscn` ni `.tres`.
- **Les tourelles elles-mêmes** et le kit d'épine : ce lot ne pose que des branches.
- **La citadelle** : ses pièces sont posées par le moteur.
