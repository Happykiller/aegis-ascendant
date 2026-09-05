# ADR-0046 — Une coque naît animée : pièces mobiles, points de tir et plume au contrat

- **Date** : 2026-09-05
- **Statut** : accepté (décision du propriétaire du projet)
- **Amende** : `ADR-0008` (contrat d'export), `ADR-0028 §2` (ce que le contrat compte),
  `ADR-0044 §3` (les familles de pièces mobiles, jusqu'ici propres à une coque)

## Contexte

Consigne de l'opérateur, 2026-09-05 :

> « dans notre forge des objets 3D, il ne faut pas oublier que je veux que les objets 3D puissent
> être micro-animés […] les ailes qui bougent suivant la vitesse, les ailettes de direction, les
> tuyères qui s'ouvrent et se ferment, les cônes de flammes qui doivent bien s'ajuster, et d'où
> partent les tirs. Toutes ces contraintes, il ne faut pas les faire à l'arrache à chaque fois, à
> chaque demande. »

Le constat est juste, et il se prouve sur quatre défauts déjà payés.

### 1. Rien n'oblige une coque à être animable

`aegis_kit.py` sait fabriquer des pièces mobiles (`MovingPart`, `moving_part()`, `attach_pair()`)
et des points d'attache (`attach_point()`), mais `_validate_glb()` (l.1179-1343) ne vérifie
**aucune** famille d'animation. Il compte les triangles, la bbox, le pivot, les matériaux et les
points d'attache **nommés dans le contrat de la coque** — c'est-à-dire ceux que l'auteur du script
a bien voulu déclarer. Une coque livrée entièrement figée passe la porte sans un mot.

La conséquence se lit dans les briefs : `BRIEF-0098` a dû porter **une table de neuf familles**
avec, pour chacune, parent, axe, pose de repos et plafond visé. Cette table est un travail de
rédaction refait à chaque coque, et rien ne garantit que la suivante emploie les mêmes noms.

### 2. Les plafonds mesurés sont RECOPIÉS À LA MAIN dans le moteur

`scripts/fx/ship_flight.gd` porte aujourd'hui, en constantes GDScript :

```
FLAP_DEG := 11.0     SWEEP_DEG := 26.0     PETAL_DEG := 24.0
NOZZLE_YAW_DEG := 5.0     AIRBRAKE_DEG := 60.0     INTAKE_DEG := 15.0
RUDDER_DEG := 24.0     GRAPPLE_DEG := 90.0     CANOPY_DEG := 40.0
RUDDER_AXIS_L := Vector3(-0.4810, 0.8331, 0.2731)
```

Chacune de ces valeurs a été **mesurée par le build** (balayage BVH au pas de 1°, jeu minimal
2,5 mm) puis **transcrite à la main** depuis un rapport de forge, avec sa marge « un cran sous le
plafond ». Y compris un vecteur d'axe à quatre décimales.

C'est un chiffre mesuré sur un binaire, recopié dans un autre fichier. **Le jour où la coque est
reforgée, la constante ne bouge pas** — et rien ne le signale : l'aile traversera la nacelle en
silence. Le dépôt a déjà une loi contre exactement ça (« un corps se décrit par sa taille RÉELLE,
mesurée sur le modèle, jamais par un chiffre plausible ») ; l'animation y échappait.

### 3. Les tirs partent d'où l'aile était, pas d'où elle est

`BRIEF-0098-report.md` §10.5, limite connue et non corrigée :

> « `Muzzle_Wing_*` et `Muzzle_Tip_*` restent figés à la pose déployée (le kit ne parente pas les
> points d'attache) — limite déjà connue de BRIEF-0035/0036. »

Les ailes se replient à pleine poussée (`SWEEP_DEG = 26`). Les bouches à feu, elles, ne bougent
pas. **Ce n'est pas un défaut cosmétique : c'est l'origine des projectiles qui ment**, dans le seul
état où le joueur va vite. Et le dépôt a une loi là-dessus aussi : « la collision et l'image lisent
la même donnée ».

### 4. La plume ne connaît pas la tuyère d'où elle sort

`Engine_*` est un Empty nu : une position, rien d'autre. Le cône de `engine_plume.gd` est réglé à
la main, coque par coque, et `BRIEF-0098-report.md` §10.6 note que sur la cellule-témoin la plume
« traverse la couronne » et « passera par les pétales ouverts » — un comportement voulu ici, mais
**deviné**, jamais dérivé du rayon de gorge réel.

## Décision

**Une coque n'est pas un maillage auquel on ajoute de l'animation ensuite. Le gréement fait partie
du contrat d'export, au même titre que la bounding box.**

### 1. Un vocabulaire de nœuds normatif, dans le kit — plus dans les briefs

Le kit porte la liste des familles et des points d'attache, avec pour chacune sa convention de
charnière, son axe et son sens d'ouverture. Un brief **choisit** dans ce vocabulaire ; il ne le
redéfinit plus.

| Famille | Rôle | Piloté par |
|---|---|---|
| `Wing_L/R` | flèche variable | poussée |
| `Flap_*` (sous `Wing_*`) | volets de bord de fuite | inclinaison |
| `Nozzle_L/R` | lacet vectoriel | inclinaison |
| `Petal_*` (sous `Nozzle_*`) | corolle de tuyère | poussée |
| `Airbrake_L/R` | aérofreins | freinage |
| `Intake_L/R` | rampes d'entrée d'air | poussée |
| `Rudder_L/R` | gouvernes de dérive | inclinaison |
| `Grapple_L/R` | grappins | appontage |
| `Canopy` | verrière | appontage |
| `Gear_*` | train d'atterrissage | appontage |

Points d'attache : `Muzzle_*` (origine de tir), `Engine_*` (plume), `Cockpit`, `Hardpoint_*`.

**Toutes les familles restent optionnelles** — `ADR-0044 §3` ne change pas : on anime ce qu'on
trouve, on ignore ce qu'on ne trouve pas. Ce qui devient obligatoire, c'est de **déclarer**
lesquelles la coque porte, et de ne pas inventer d'autres noms.

### 2. Un point d'attache est PARENTÉ à la pièce qui le porte

`attach_point()` prend un parent. Une bouche à feu d'aile est **enfant de `Wing_L`** ; elle suit la
flèche sans une ligne de code côté moteur. Le contrat refuse un `Muzzle_*` orphelin quand la coque
déclare une famille mobile susceptible de le porter.

C'est la correction du défaut n°3, et elle se prouve en le faisant tomber : mettre les ailes en
flèche maximale et vérifier que la position monde du `Muzzle_Wing_L` a bougé.

### 3. Les plafonds se mesurent au build et s'EXPORTENT — plus une constante recopiée

Le balayage BVH sort des scripts de coque (où `build_specter_9_c.py:53-77` l'a écrit pour lui seul)
et entre dans le kit. Chaque build **mesure**, pour chaque famille présente : l'axe réel, le signe
d'ouverture, et le plafond mécanique avant interpénétration.

Le résultat est **écrit à côté du `.glb`**, dans un fichier de gréement versionné
(`<coque>_rig.tres`). `ShipFlight` le **lit** ; ses constantes disparaissent. Une reforge qui
réduit un débattement met à jour le gréement dans le même commit que le maillage — ou le build est
rouge.

### 4. La plume est dérivée de la gorge, pas devinée

`Engine_*` porte le **rayon de gorge** et la **direction** mesurés sur la géométrie qui l'entoure.
`engine_plume.gd` s'y ajuste. Une tuyère plus large donne une plume plus large, sans réglage.

### 5. Le contrat d'export vérifie le gréement

`_validate_glb()` gagne : noms hors vocabulaire refusés ; points d'attache parentés ; fichier de
gréement produit et cohérent avec le `.glb` ; aucune interpénétration à aucun extrême de course.

### 6. Le brief gagne une section `## Animation` obligatoire

Même précédent qu'`ADR-0028` pour la texture, et pour la même raison : une permission qu'on peut
oublier n'est pas un process. Deux issues, **jamais de silence** — soit le brief nomme les familles
que la coque porte et ce qui les pilote, soit il déclare qu'elle est figée **et écrit pourquoi**.

## Ce qui ne change pas

- **`ShipFlight` ne lit toujours rien** : ni input, ni vitesse, ni autoload. Ses appelants lui
  poussent des ratios. Un vaisseau de décor s'en sert sans embarquer de gameplay.
- **Le déterminisme** : le gréement est mesuré par un balayage déterministe, il ne contient aucun
  nombre tiré au hasard ni recopié.
- **Aucune campagne de rattrapage.** Les coques déjà livrées ne sont pas reforgées pour elles-mêmes ;
  elles gagnent le gréement à l'occasion d'une reforge. Le contrat ne devient dur que pour les
  coques neuves — sinon la porte serait rouge sur treize coques dès le premier commit.

## Conséquences

- `tools/blender/lib/aegis_kit.py` : vocabulaire, `attach_point(parent=)`, `measure_travel()`,
  écriture du gréement, extension de `_validate_glb()`.
- `scripts/fx/ship_flight.gd` : ses onze constantes deviennent des lectures de gréement. C'est une
  simplification, pas un ajout.
- `scripts/fx/engine_plume.gd` : dérive sa géométrie du rayon de gorge.
- `docs/forge/BRIEF_TEMPLATE.md` et `.claude/agents/asset-forge.md` : la section `## Animation`.
- Le défaut des bouches à feu figées est corrigé, et il était **de gameplay**.
