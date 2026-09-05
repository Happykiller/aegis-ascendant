# ADR-0044 — La cellule-témoin : une troisième coque du Specter-9, **sans plafond de triangles**

> ## ⛔ ANNULÉ PAR L'OPÉRATEUR — 2026-09-05
>
> « *c'est très moche. Autant sur la forme que sur les textures* […] *on va annuler cette
> version. C'est un échec. Donc, on ne garde que les deux premières versions du vaisseau.* »
>
> **La coque `specter_9_c` (Specter-9 Talvern) est retirée du jeu et du dépôt** : le `.glb`,
> son script de forge, sa fiche de bestiaire, son jeu de textures et son atlas. Le jeu revient
> à deux coques, `specter_9` et `specter_9_b`.
>
> Le verdict porte sur **les deux axes à la fois** — la silhouette et la matière. Ce n'est donc
> pas un défaut d'exécution à corriger : c'est le résultat qui est refusé.
>
> **Ce qui survit, et pourquoi.** L'outillage bâti autour d'elle n'est pas annulé, parce qu'il
> ne lui appartenait pas :
> - `atlas_unwrap()` et la cuisson d'atlas (`ADR-0046`, `ADR-0047`) — c'est la seule voie vers
>   une livrée peinte, et elle reste demandée ;
> - les familles de pièces mobiles de `ShipFlight` — optionnelles par nom, elles ne coûtent rien
>   aux deux coques restantes et serviront la suivante ;
> - la levée du filtre rétro (`ADR-0045`), sans rapport avec cette coque.
>
> **Ce qui redevient sans objet** : la levée de plafond de triangles n'a plus de bénéficiaire ;
> le seuil des 12 ms sur Quadro T1000 était déjà remplacé par `ADR-0045`. Les demandes de
> texture `TEX-0017` à `TEX-0019` sont caduques et n'ont jamais été commandées.
>
> L'ADR reste au dépôt : il porte le *pourquoi* d'une tentative et son verdict, ce qui vaut
> mieux qu'un silence. `docs/forge/briefs/BRIEF-0098-*` et son rapport restent également, sans
> leurs planches — elles rendaient la coque retirée.

- **Statut** : annulé (2026-09-05) — accepté le 2026-09-04
- **Date** : 2026-09-04
- **Décision** : opérateur — « *je veux le plus beau que tu puisses réaliser, sans aucune
  restriction* »
- **Amende** : `ADR-0011` (plafond héros de 60 000 triangles — pour **cette coque seulement**),
  `ADR-0008` §matériaux (le contrat des pièces mobiles s'étend)
- **S'appuie sur** : `ADR-0014` (le plan de la planche), `ADR-0013` (jeux de textures dédiés),
  `ADR-0034` (la hitbox vient des Resources, jamais du maillage), `ADR-0028` (la texture est une étape)
- **Portée** : **le Specter-9 uniquement**, comme `ADR-0014`. Aucun autre budget ne bouge.

## Contexte

Le joueur dispose de **deux carrosseries** pour la même cellule : la coque en service
(`specter_9.glb`, 35 412 triangles, six pièces mobiles, contrat `AA_*` complet) et la coque gagnée
au poker (`specter_9_b.glb`, 53 222 triangles, monobloc offert par un tiers — ni palette, ni
pièce mobile). L'opérateur en veut une **troisième**, et il l'a définie par son ambition, pas par
un besoin de gameplay : la plus belle des trois, très détaillée, riche en polygones, et
**micro-animée** — ailes qui se rétractent, volets, tuyères qui s'ouvrent et se ferment, « et
caetera ».

Trois choses du dépôt s'opposent ou se prêtent à cette demande :

| | État | Ce que ça implique |
|---|---|---|
| `ADR-0011` | héros plafonné à **60 000** triangles | le plafond est un garde-fou « le budget se justifie au rendu, pas au chiffre » — et il refuserait la demande |
| `ShipFlight` | anime **`Wing_L/R`, `Flap_L/R`, `Nozzle_L/R`** et rien d'autre ; la tuyère « s'ouvre » par un **changement d'échelle** | la micro-animation demandée n'a pas de contrat de nommage, et l'ouverture des pétales n'est pas une ouverture |
| `ADR-0011` §justification | le temps GPU est dominé par le **remplissage écran**, pas par la géométrie : la scène la plus chargée en triangles (l'accueil) est la moins chère | la géométrie est le levier le moins coûteux du jeu — c'est **mesuré**, pas supposé |

Et une règle du ghost qui borne l'ambition avant même de commencer : le post-traitement rétro
(960×540, postérisation à 20 niveaux) **écrase le détail fin** — « mettre le détail dans la
géométrie, pas dans une texture fine » (`pratique-revue-asset`), et « un détail dont la modulation
est sous ~6 niveaux de gris n'existe pas dans ce jeu » (`docs/forge/textures/README.md`). Le plus
beau vaisseau du jeu n'est pas celui qui porte le plus de micro-détail : c'est celui dont la
silhouette, les volumes et les cassures de panneaux **survivent** à ce filtre.

## Décision

### 1. Une troisième carrosserie, même cellule

Le **Specter-9 Talvern** — identifiant `specter_9_c` partout dans le dépôt, jamais renommé
(`pratique-renommer-ce-que-le-joueur-lit`) — entre au bestiaire comme troisième coque
**emmenable**. Il partage `specter9_stats.tres` : mêmes points de structure, même vitesse, même
hitbox (`ADR-0034`). **On compare des formes, pas des chiffres.** Les dimensions de contrat restent
**1,75 × 2,46 m à ±3 %, ailes déployées** — c'est le contrat de gameplay, il ne se négocie pas.

Fiction (elle tient à l'univers, `docs/lore/FACTIONS.md` §Arsenal) : chaque lot de Specter-9 sort
des cales avec une cellule de plus que le bon de commande, la **cellule-témoin**, montée à la main
sur le pont de certification et contre laquelle Oda Talvern mesure les autres. Chaque mécanisme y
est fonctionnel, chaque panneau démontable. Elle ne vole jamais. Celle-ci a volé. La fiche donne
les faits et laisse le joueur les rapprocher — comme pour la coque gagnée au poker.

### 2. Le plafond de triangles est remplacé par une mesure

Pour **cette coque**, le `tri_budget` du contrat d'export n'est plus un plafond de qualité mais un
**garde-fou d'accident** : **400 000** triangles. Au-delà, ce n'est plus du détail, c'est une erreur
de script (un biseau à trop de segments, une révolution sur-échantillonnée), et `export_hull()`
doit continuer de refuser bruyamment.

Ce qui remplace le plafond : **le coût GPU par image, mesuré** (`howto-mesurer-la-perf`), aux deux
endroits où la coque apparaît — l'écran d'accueil (gros plan, quatre chasseurs) et le combat —
avant et après, trois tirs de chaque côté, sur les deux machines connues (RTX 4080 de l'opérateur,
Quadro T1000). **Le vaisseau est accepté si l'accueil reste sous 12 ms sur T1000** (il est à 8,3
avec la coque en service, `ADR-0011`) et si le combat ne bouge pas au-delà du bruit de mesure
(~1,9 ms). Sinon, c'est la géométrie qui cède — par les LOD que Godot génère à l'import
(`meshes/generate_lods=true`, déjà actif), puis par le script.

Ce que le budget ne rachète pas : **la règle de BRIEF-0026** — ce qui n'est pas visible depuis
la caméra de jeu (20° de la verticale) n'existe pas en combat. Le détail ventral n'existe que pour
le bestiaire, où la coque se tourne à la souris. Il est autorisé, mais il vient **après** le dos.

### 3. Le contrat des pièces mobiles s'étend, et reste optionnel

Le nommage d'`ADR-0008` (`Muzzle_*`, `Engine_*`, `Cockpit`) et de BRIEF-0035 (`Wing_L/R`,
`Flap_L/R` enfants des ailes, `Nozzle_L/R`) reste normatif. S'y ajoutent, **tous optionnels** —
`ShipFlight` anime ce qu'il trouve et ignore ce qu'il ne trouve pas, si bien que les deux coques
existantes continuent de voler sans modification :

| Nœud | Pièce | Axe | Piloté par |
|---|---|---|---|
| `Petal_L_00..11`, `Petal_R_00..11` | pétales de tuyère, **enfants** de `Nozzle_L/R` | rotation sur leur charnière | poussée — ils **s'ouvrent**, la tuyère ne change plus d'échelle |
| `Airbrake_L`, `Airbrake_R` | aérofreins dorsaux | rotation, charnière avant | freinage |
| `Intake_L`, `Intake_R` | rampe d'entrée d'air variable | rotation, charnière avant | poussée |
| `Rudder_L`, `Rudder_R` | gouverne de dérive, **enfant** de rien (la dérive est fixe) | rotation autour de l'axe de la dérive | inclinaison |
| `Grapple_L`, `Grapple_R` | grappins d'appontage, sous le nez | rotation, charnière arrière | appontage |
| `Canopy` | verrière | rotation, charnière arrière | appontage (ouverture après le verrouillage) |

Et **`Nozzle_L/R` reçoivent un lacet** de poussée vectorielle (± quelques degrés avec
l'inclinaison) — c'est ce que la planche appelle « poussée directionnelle », et ça se lit du dessus.

Chaque débattement a un **plafond mécanique mesuré à chaque build** sur le maillage livré, le
build échouant sous la cible — c'est la méthode de BRIEF-0035/0036, qui a déjà trouvé un volet
tombé à 2,8° sous une bbox parfaite. Les cibles sont dans le brief ; le code (`ShipFlight`) reste
**en deçà** avec la marge de lissage habituelle.

### 4. Un jeu de textures dédié, par la voie de l'opérateur

`ADR-0013` autorise les jeux dédiés ; `ADR-0028` en fait une étape. Cette coque en a un : trois
demandes (`TEX-0017` bordé, `TEX-0018` mécanique des baies, `TEX-0019` métal de tuyère), générées
par l'opérateur, dérivées par `derive-maps.py`. `HullDetail` apprend à poser **un jeu par coque**
au lieu de la feuille partagée — c'est la conséquence qu'`ADR-0013` annonçait sans l'exécuter.

Les textures restent des **feuilles répétables projetées** : pas d'atlas peint. La beauté
demandée ne peut donc pas venir d'une peinture — elle vient de la géométrie, et les feuilles
n'ajoutent que la matière.

### 5. Ce qu'`ADR-0014` couvre, et ce qu'il exclut toujours

La coque reprend le plan de la planche de référence — c'est **la même unité**, l'exception
d'`ADR-0014` s'applique telle quelle et **ne s'étend pas d'un pouce**. Restent exclus, sur cette
coque comme sur les deux autres : la **livrée tricolore**, le **badge numéroté**, tout **texte,
insigne ou marquage lisible**. Les hachures d'avertissement sans texte (`ADR-0013` §4) sont
autorisées, en `AA_Marking_Red`, à dose de marquage restreint.

## Ce qui ne change pas

- Les **sept matériaux** et leur ordre, la palette, les dix points d'attache, le pivot au centre.
- **Le script Python EST la source**, déterministe, bâti par `./scripts/build-hull.sh` (`-t 1`).
- La coque **se regarde avant de s'intégrer** (`ADR-0006`) : planche quatre vues, **chaque pièce
  mobile à ses deux extrêmes**, aplat noir — puis en jeu, post-traitement actif.
- **Un seul écrivain** : la forge écrit `tools/`, `assets/`, le CSV ; le concepteur écrit le code.
  Aucun `git add -A` pendant qu'elle travaille.

## Conséquences

- `ShipFlight` gagne deux entrées (`set_brake`, `set_docking`) et sept familles de nœuds
  optionnels, sous test (`test_ship_flight.gd` — les plafonds mécaniques du rapport de forge y
  entrent comme constantes, c'est le seul endroit où ils survivent à un réglage distrait).
- `HullDetail.apply(hull, set)` prend une Resource typée `HullDetailSet` (avec `validate()`) ; la
  feuille partagée devient le jeu par défaut.
- L'écran d'accueil monte **la coque choisie** au bestiaire sur le héros — aujourd'hui `boot.tscn`
  câble `specter_9.glb` en dur pour le héros et les trois escortes.
- La phase `DOCKING` pousse `set_docking(1.0)` au chasseur : les grappins sortent, puis la
  verrière s'ouvre au verrouillage. Les deux coques existantes n'ont pas ces nœuds : rien ne se
  passe, et c'est correct.
- Une ligne dans `ASSET_PROVENANCE.csv` par fichier livré ; les binaires en LFS.

## Ce qui rouvrirait cette décision

Une mesure : l'accueil au-dessus de 12 ms sur T1000 après LOD, ou une capture en combat où la
coque **lit moins bien** que celle en service à 48 px — le plus beau vaisseau en gros plan ne peut
pas être le moins lisible en jeu.
