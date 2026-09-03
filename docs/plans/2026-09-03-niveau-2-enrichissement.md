# Niveau 2 — enrichissement : la silhouette, les secteurs, et les trois échelles de défense

- **Auteur** : session Claude, sur les 20 consignes de l'opérateur (2026-09-03)
- **Périmètre** : la **silhouette** de la coque du Long Cortège, ses **secteurs**, son **rythme**,
  et une **seconde échelle de défense**. Pas les textures, pas les mécaniques existantes.
- **Complète** : [`2026-08-29-niveau-2-refonte-geometrie.md`](2026-08-29-niveau-2-refonte-geometrie.md),
  dont il reprend **la règle de production et le test d'acceptation sans les modifier**. Ce plan
  ne supersède rien : les lots 1 à 5 de la refonte sont livrés et tiennent.
- **Source** : les 20 consignes de redesign de l'opérateur, 2026-09-03.

## Le constat de l'opérateur

> « Casser fortement l'effet *piste rectangulaire / couloir tout droit*. Le joueur doit avoir
> l'impression de survoler la coque d'un vaisseau gigantesque, avec des secteurs fonctionnels
> différents, et non un rectangle de 500 m décoré. »

⚠️ **La moitié des 20 points est déjà livrée.** Les consignes ont été écrites contre une lecture
du niveau qui précède la refonte du 2026-08-29 (lots 1 à 5). Ce plan ne traite **que le reste**,
et le tableau ci-dessous dit lequel — pour qu'aucun lot ne repaie ce qui est déjà en dépôt.

## Traçabilité des 20 consignes

| # | Consigne | Statut | Lot |
|---|---|---|---|
| 1 | Ne pas refaire le vaisseau depuis zéro | **règle du plan**, pas un lot | — |
| 2 | Casser les deux bords parallèles (±15-25 %) | ❌ à faire | **B** |
| 3 | Créer des secteurs visuellement différents | ❌ à faire | **C** |
| 4 | Terrasses de coque, plusieurs niveaux | ⚠️ **à faire sous contrainte dure** (§C3) | **B** |
| 5 | Conserver une zone de circulation claire | **garde-fou**, vérifié au test | — |
| 6 | Artère = tranchée technique, pas ligne de terrain | ✅ **livré** — lot 3 de la refonte : canal enfoncé de 0,56 m, rebords à \|x\| ≤ 1,70, plus de crête centrale | — |
| 7 | Trois échelles de défense | ❌ à faire | **A** |
| 8 | Hiérarchie grosse / moyenne / petite | ❌ à faire | **A** |
| 9 | Petites tourelles en batteries (clusters) | ❌ à faire | **A** |
| 10 | Ponts d'envol = cavités reconnaissables | ✅ **livré** — lot 1 de la refonte : vraies ouvertures, peau générée trouée, appareil au fond | — |
| 11 | Varier la disposition des ponts d'envol | ❌ à faire | **C** |
| 12 | Gros volumes pour fabriquer le level design | ❌ à faire | **C** |
| 13 | Ponts transversaux ponctuels | ❌ à faire | **C** |
| 14 | Asymétrie obligatoire | ❌ à faire | **B** |
| 15 | Éviter la répétition procédurale visible | ⚠️ **plafonné** (§C2) | **D** |
| 16 | Laisser de grandes surfaces calmes | ⚠️ **plafonné à 50,3 %** (§C2) | **D** |
| 17 | Limiter le magenta | ✅ **livré** — lot 4 : palette 80/15/5, facette extérieure dévioletée | — |
| 18 | Priorité absolue aux silhouettes (test N&B) | ✅ **c'est déjà LE test d'acceptation** de la refonte, repris ici tel quel | — |
| 19 | Rester techniquement économique (primitives) | ✅ **règle en vigueur** : ≤ 6-8 primitives par structure | — |
| 20 | Contour extérieur qui varie nettement | ❌ à faire — **c'est le critère de sortie du lot B** | **B** |

---

# Les six contraintes dures qui décident du découpage

Aucune n'est une opinion. Chacune est lue dans le code ou mesurée.

## C1 — Il y a exactement **412 m de bords strictement parallèles**, et c'est mesurable

`build_long_cortege.py` ne fait varier la largeur que sur le **fuseau de proue** :

```python
TAPER = ((0.0, 0.008, 0.16), (5.0, 0.100, 0.26), (58.0, 0.940, 0.93), (88.0, 1.000, 1.00))
TAPER_END = 88.0
def _scales(s):  # s >= TAPER_END -> (1.0, 1.0)
```

De `s = 88` à `s = 500`, `kx = 1.0` : la demi-largeur vaut `HALF_WIDTH = 14,0` **au micron près**,
soit **28 m bord à bord sur 412 m**. L'opérateur ne décrit pas une impression — il décrit la
table. C'est le lot B, et c'est le seul lot dont le résultat se voit sur une capture fixe.

## C2 — Les 30 marqueurs sont figés, et **deux choses différentes** en dépendent

Le `BRIEF-0092` fige « noms, X, Z inchangés ». Deux conséquences, à ne pas confondre :

1. **Le moteur les résout PAR NOM à chaque image.** Un déplacement est sûr ; une disparition ou
   un renommage casse le niveau. → *ajouter* des marqueurs est sans risque.
2. **Ils portent l'équilibrage mesuré** — fenêtres de relâche et d'engagement, arbitrages du
   `BRIEF-0092`. Le backlog l'écrit noir sur blanc : le rythme calme/installation plafonne à
   **50,3 %** (251,4 m calmes sur 500), c'est le *maximum atteignable sans déplacer un marqueur*,
   et les déplacer « est un chantier, pas un réglage ».

⚠️ **Conséquence de découpage, et c'est la décision structurante de ce plan** : les consignes 14,
15 et 16 (asymétrie, rythme, respiration) demandent de **re-répartir les installations**. Le lot B
rejoue déjà les Y de marqueurs par construction (§C3). **Les faire séparément revient à payer deux
fois la même reforge** — donc le repositionnement vit DANS le lot B, et le lot D ne fait que le
mesurer et l'arbitrer.

## C3 — Élargir la coque **rejoue les 24 Y de tourelle et de pont**

Le fichier le dit à sa ligne 260 :

> « RIEN NE BOUGE AU-DELÀ DE x = 2,20, ET C'EST UNE CONTRAINTE DURE […] le Y d'un marqueur de
> tourelle est ÉCHANTILLONNÉ sur la peau (`turret_seat_y`), et celui d'un pont aussi
> (`bay_mouth_y`). Tant que le profil est IDENTIQUE au-delà de 2,20, les vingt-quatre Y sont
> inchangés au micron. »

Faire varier la largeur de ±15-25 % change le profil **précisément là**. Donc le lot B :

- rejoue les 24 Y échantillonnés ;
- **re-mesure et re-déclare** `ACCEPTED_PAD_BAY_PROXIMITY` — qui déclare déjà un chiffre périmé
  (0,25 m de lèvre statique, alors que ce qui dépasse est désormais un canon qui balaie à ~0,55 m
  au-dessus du coaming) ;
- rejoue le cliquet de plafond du kit et son test
  `test_no_turret_ever_reaches_the_flight_plane`.

Ce n'est **pas un blocage** : c'est le prix, et il doit être annoncé avant de commencer, pas
découvert au milieu.

## C4 — Les « grands volumes » ne montent pas : ils se creusent

`ADR-0041` a dédoublé le plafond :

| | Cote | Marge au-dessus du pont (−4,26) |
|---|---|---|
| Décor **inerte** | **−3,00** | **1,26 m** |
| Pièce de **gameplay** (destructible) | **−2,40** | 1,86 m |

⚠️ **La consigne 4 demande « de grands volumes de plusieurs mètres produisant de vraies ombres ».
Vers le haut, c'est impossible** : le décor inerte dispose de 1,26 m, un point. Une terrasse de
3 m masquerait le combat sans jamais pouvoir être touchée — exactement ce que le plafond interdit.

**La sortie est celle qu'a déjà empruntée le lot 1** : la profondeur se prend **vers le bas**.
Fosses, baies de maintenance en creux, décrochements de bordé, épaulements en largeur. Une
tranchée de 2 m de fond lit comme un volume de 2 m et ne coûte rien au plafond. Le lot B compose
donc son relief en **creux et en largeur**, pas en hauteur.

## C5 — Les invariants de `CortegeTuning` s'appliquent à toute échelle nouvelle

Une seconde famille de tourelle n'est pas un réglage cosmétique : elle passe les mêmes
`validate()` que la première, en particulier —

- **invariant 2** — *toute cible tombe dans sa fenêtre* : « c'est l'invariant qui décide si le
  niveau existe ». Un survol ne revient jamais en arrière : une petite tourelle avec moins de PV
  mais une fenêtre plus courte peut très bien être **intuable**.
- **invariant 3** — *une tourelle se distance* : le joueur contourne à 100 °/s, la grosse pivote à
  42 °/s. Une petite qui pivoterait trop vite deviendrait la « taxe » que la spec §11.2 interdit.
- **invariant 6** — un télégraphe ne promet pas un tir hors de portée.
- **invariant 8** — une tourelle abîmée reste une tourelle.

## C6 — Le coût n'est connu que sur la mauvaise machine

Toutes les mesures du niveau 2 portent la ligne **RTX 4080**. La machine qui **contraint** est la
**Quadro T1000** (×14 à build identique, `ADR-0011`), et elle n'a jamais mesuré ce niveau. Ce plan
ajoute de la géométrie **et** des entités actives. Protocole obligatoire avant de valider tout
lot : `.claude/resources/howto-mesurer-la-perf.md`, à 60 Hz, trois tirs alternés, **jamais
`--novsync`**.

Budget triangles : la coque consomme **~40 000 sur 90 000**. Le kit dispose du reste, aujourd'hui
employé par 17 tourelles et 7 hangars.

---

# LOT 0 — Jouer avant d'enrichir · **prérequis, pas une formalité**

Trois éléments du backlog disent la même chose : **personne n'a jamais joué ce niveau à la main.**

- la densité de patrouille **×3,5 (209 coques)**, publiée en v0.4.0, n'a été jouée ni par
  l'opérateur ni par une session ;
- `CortegeSkin.EMISSIVE_ENERGY` (0,45) et `PANEL_DAMP` (0,45) ont été arrêtés sur **trois captures
  fixes, au seul tronçon 2** — or ce qui décide ici est ce que donne l'artère **quand elle
  défile**, et si son émissif reste distinguable des **balles** quand l'écran se charge ;
- les PV des cibles de coque sont **dimensionnés, pas mesurés** : le pilote automatique n'a détruit
  qu'**une** cible en 208 s, parce qu'il ne vise pas un bordé.

Et le **LOT 6 de la refonte précédente (décoration) attend explicitement cette partie jouée** :
décorer avant que les fonctions soient jugées lisibles, c'est ajouter du bruit par-dessus une
hiérarchie non validée.

**Livrable** : une partie complète du niveau 2, à la main (`/jouer`), et un verdict écrit sur
quatre questions —

1. la coque lit-elle encore comme un rectangle **maintenant qu'elle a ses affûts, ses cavités et
   sa tranchée** ? (si non, le lot B change de priorité) ;
2. la densité ×3,5 est-elle jouable, ou faut-il redescendre ?
3. l'artère est-elle au bon niveau d'émissif **en mouvement** ? ⚠️ le sens de l'erreur n'est pas
   symétrique : trop bas, le vaisseau cesse d'être vivant ; trop haut, on retrouve le « laser » que
   toute la refonte visait à supprimer ;
4. une cible de coque tombe-t-elle dans sa fenêtre **quand c'est un humain qui vise** ?

⚠️ **Ce lot peut invalider une partie du reste.** C'est sa raison d'être.

---

# LOT A — Trois échelles de défense

C'est la demande de départ de l'opérateur, et **le seul lot qui ne touche aucun marqueur
existant** : il est donc livrable seul, et en premier.

## A1 — La hiérarchie

| Échelle | Rôle | Silhouette | Fréquence |
|---|---|---|---|
| **Lourde** (existante) | événement local | affût : socle 3,4 m, couronne, bloc blindé, **deux** canons de 2,90 m | rare |
| **Légère** (nouvelle) | décor actif, pression continue | embase courte, couronne réduite, **un** canon court | en batteries |
| *Point-defense* | *optionnel* | — | **hors périmètre de ce plan** — l'opérateur l'écrit « éventuelle » ; une troisième famille se décide après avoir vu la deuxième jouer |

⚠️ **Ne jamais obtenir une forêt uniforme de tourelles identiques** (consigne 8). Le garde-fou est
un test, pas une intention : cf. §A5.

## A2 — Le kit

`build_turret_kit.py` expose déjà le vocabulaire nécessaire — `build_pad`, `build_anchor_skirt`,
`build_ring`, `build_body`, `build_barrel`, **`build_barrel_short` (2,20 m, déjà écrit)**,
`build_service_box`, `build_pipe`.

La tourelle légère est donc un **assemblage d'un sous-ensemble existant à une autre échelle**, pas
un kit neuf : embase + couronne + corps réduit + un `barrel_short`. ⚠️ **≤ 6 primitives
principales**, et la règle de production de la refonte s'applique sans changement — *la silhouette
d'abord, l'émissif ne fait que renforcer une fonction déjà lisible*.

⚠️ **Elle doit rester lisible comme une tourelle, et lisible comme une PETITE.** Le test N&B (§18)
oppose aujourd'hui tourelle et hangar ; il devra désormais opposer **trois** objets.

## A3 — Les marqueurs, en clusters

- **Préfixe neuf** : `TurretL_NN` (L = léger). `CortegeHardpoints.build()` dispatche déjà sur
  `Turret_` / `Bay_` / `Spine_` — une branche de plus, et rien d'existant n'est touché.
- ⚠️ **Posés à la main, en table séparée**, comme les 30 autres : « une position de gameplay ne se
  seede pas : elle se décide, elle se relit et elle se corrige ».
- **En batteries de 2 à 4**, autour d'une grosse installation, le long d'un bord, ou autour d'un
  hangar. **Jamais un pas régulier.**
- ⚠️ **Ces marqueurs seront rejoués par le lot B**, qui reforge la coque. Le coût est petit (une
  table) et il est annoncé ici pour qu'il ne soit pas découvert plus tard.

## A4 — Le moteur

- `CortegeTurret` prend un **profil** (lourd / léger) — pas une seconde classe. La pièce est déjà
  écrite autour d'un seul mécanisme de position (« elle est enfant de son marqueur, et c'est tout
  le mécanisme »), et ce mécanisme ne change pas.
- **Projectile** : une Resource dédiée, plus petite et moins dangereuse que
  `cortege_turret_shot.tres`. ⚠️ **Même corail que le reste des tirs ennemis** — un second rouge
  apprendrait au joueur qu'il existe deux dangers là où il n'y en a qu'un.
- **Tuning** : un groupe `Tourelles légères` dans `CortegeTuning`, et les invariants **2, 3, 6, 8
  étendus à la nouvelle échelle**. Un invariant qui ne couvre pas la pièce neuve est un invariant
  qui ment.
- ⚠️ **Le cycle `AHEAD / LIVE / PASSED` s'applique** : une tourelle passée rend sa cible au
  gestionnaire de balles. Avec 20-30 pièces de plus, ce n'est plus une optimisation, c'est la
  condition pour que le coût par balle reste borné.

## A5 — Ce qui prouve le lot

- test N&B à trois objets (§A2) ;
- un test qui **refuse un pas régulier** : aucune batterie ne doit être reproductible par une
  formule `tous les X mètres` ;
- invariants 2/3/6/8 verts sur la nouvelle échelle ;
- **une capture regardée** (`ADR-0006`) ;
- **coût GPU mesuré sur T1000**, avec et sans les pièces neuves (§C6).

---

# LOT B — La coque cesse d'être un rectangle

Le plus gros lot, et celui qui porte le critère de sortie de l'opérateur (consigne 20).

## B1 — La largeur varie

Étendre `TAPER` **au-delà de `s = 88`** avec des stations de largeur, sur les 412 m aujourd'hui
constants : étranglements, élargissements, épaulements, décrochements. **±15 à 25 %** de
`HALF_WIDTH`, pas davantage — « ce n'est pas un nouveau vaisseau ».

⚠️ **`_scales()` applique aujourd'hui kx ET ky ensemble.** Faire varier la largeur sans toucher la
hauteur demande de les découpler, ou d'assumer que la coque s'épaissit là où elle s'élargit — ce
qui est peut-être souhaitable (un renflement se lit mieux). **À arbitrer en regardant, pas en
raisonnant.**

## B2 — L'asymétrie (consigne 14)

⚠️ **Le profil est aujourd'hui construit par miroir** : `_ring()` calcule la moitié tribord puis
la recopie en bâbord. **Une coque asymétrique demande de casser ce miroir**, ce qui touche
`_half_profile`, `_ring`, `_ring_x`, `_ring_materials`, `_ring_deck_flags` et le dépliage UV.

C'est le vrai coût du lot B, et il n'est pas dans les cotes : il est dans la **structure du
générateur**. Deux voies, à trancher avant d'écrire :

- **(a)** garder le miroir pour la section transversale et poser l'asymétrie **par les modules**
  (bastions, excroissances, épaulements posés d'un seul bord) — moins cher, et suffisant pour la
  consigne 14 telle qu'elle est formulée (« un gros bastion à droite, quelques petites défenses à
  gauche ») ;
- **(b)** casser le miroir dans le profil lui-même — plus fidèle à « la coque peut être plus large
  d'un côté pendant quelques dizaines de mètres », beaucoup plus cher.

**Recommandation : (a) d'abord, et ne passer à (b) que si la capture ne suffit pas.** La consigne
20 juge un **contour**, et un bastion de 6 m posé d'un seul bord modifie un contour.

## B3 — Le relief, en creux et en largeur (consigne 4)

Voir **§C4** : le décor inerte n'a que **1,26 m** au-dessus du pont. Le relief se compose donc en
fosses, baies de maintenance en creux, décrochements de bordé et épaulements — **jamais en
terrasses hautes**. Une seule exception possible : une masse **destructible** peut monter jusqu'à
−2,40, mais elle devient alors une pièce de gameplay, avec PV, fenêtre et invariants.

## B4 — Le repositionnement des installations

⚠️ **C'est ici, et nulle part ailleurs** (voir §C2). Le lot B rejoue déjà les Y : c'est le seul
moment où déplacer un `s` de marqueur ne coûte pas une seconde reforge.

Ce qui doit être rejoué **et re-déclaré** :

- les 24 Y échantillonnés (`turret_seat_y`, `bay_mouth_y`) ;
- `ACCEPTED_PAD_BAY_PROXIMITY` — **avec sa vraie nature** : un canon qui balaie à ~0,55 m
  au-dessus du coaming, et non la lèvre statique de 0,25 m qu'il déclare encore. Sinon « le
  prochain lecteur arbitrera sur un fait faux » ;
- `_marker_clashes()` et le cliquet de plafond du kit ;
- les fenêtres de relâche et d'engagement du `BRIEF-0092`, **qui sont de l'équilibrage mesuré** :
  les déplacer sans les rejouer est la seule façon de casser ce niveau en silence.

## B5 — La circulation reste claire (consigne 5)

Garde-fou non négociable : les volumes sont **du décor et du support d'ennemis**, pas un labyrinthe.
Le test : l'espace négatif autour du joueur et de ses projectiles ne diminue nulle part sous ce
qu'il vaut aujourd'hui.

---

# LOT C — Secteurs fonctionnels, ponts variés, pont transversal

## C1 — Des secteurs lisibles à la silhouette (consigne 3)

Les 5 tronçons de 100 m deviennent **5 secteurs de fonction différente** — étroit et militaire,
large avec ponts d'envol, très mécanique… ⚠️ **Le changement doit être visible avant même les
textures**, donc porté par les gros volumes et la largeur (lot B), pas par la peinture.

## C2 — Les ponts d'envol se diversifient (consignes 11, 12)

Aujourd'hui les 7 baies partagent orientation et implantation. À varier : latéral gauche, latéral
droit, l'un dans un élargissement de coque. ⚠️ **Toujours une sortie compatible avec le
gameplay** — un hangar dont l'appareil ne peut pas sortir est un bug, pas une variation.

Le catalogue de gros volumes autorisé par l'opérateur : bastion de défense, excroissance latérale,
plateforme d'artillerie, zone de maintenance en creux, bloc rapporté gigantesque, conduit
transversal.

## C3 — Le pont transversal (consigne 13)

Une structure qui **enjambe la tranchée centrale** et relie les deux bords. C'est le geste le plus
efficace contre l'axe infini — et le plus facile à gâcher : **un seul**, ou deux au maximum.
« Un élément exceptionnel est plus intéressant qu'un motif répété. »

⚠️ **Il passe au-dessus de la tranchée, donc au-dessus du canal émissif** — et le plafond du décor
(−3,00) le borne. Le plan de refonte prévoyait déjà ce cas pour le bandeau dorsal : « la tranchée
lui mange un demi-mètre et il culmine sous −3,00 ». Le pont transversal se dimensionne pareil, et
**son propre test le vérifie**.

---

# LOT D — Le rythme, et ce qu'il coûte de le vouloir entier

Consignes 15 et 16 : *calme → batterie → grande installation → zone technique → hangar →
respiration*, avec 10 à 20 m visuellement calmes autour de chaque installation.

⚠️ **Ce lot ne peut PAS être livré si le lot B n'a pas rejoué les marqueurs.** La forge a mesuré :
50,3 % de coque calme est le **maximum atteignable** à marqueurs figés, et la plus large plage nue
hors proue fait **22 m**, quand la consigne en demande 15 à 20 **de chaque côté** d'une
installation. Le refus de les déplacer était un arbitrage explicite, pas une limite technique.

**Livrable de ce lot** : la mesure refaite après le lot B, l'écart au rythme demandé, et
l'arbitrage de l'opérateur sur ce qui reste — pas une promesse de 100 %.

---

# Test d'acceptation

Il **reprend celui de la refonte du 2026-08-29 sans le modifier**, et lui ajoute trois lignes.

1. **Noir et blanc, émissifs coupés** (`--no-glow`, désaturation) : on distingue sans hésitation
   tourelle lourde ≠ **tourelle légère** ≠ hangar ≠ tranchée. *(Étendu : trois objets, pas deux.)*
2. **Aire par matériau** mesurée sur le `.glb` : 80 / 15 / 5 ± 5 points. Les volumes neufs sont
   **anthracite/gris** — consigne 17 : *ne jamais utiliser une surface violette simplement pour
   rendre un nouveau volume visible*.
3. **Silhouette ≤ 6-8 primitives principales** par structure, comptées au rapport.
4. **Budget** : coque + kit ≤ 90 000 triangles, ventilé au rapport.
5. **Les deux plafonds tiennent** : décor inerte < −3,00, gameplay < −2,40, tests moteur verts.
6. **NOUVEAU — le contour varie.** Sur une capture fixe du niveau, le contour extérieur varie
   nettement du haut vers le bas de l'image, et l'œil identifie plusieurs zones fonctionnelles.
   ⚠️ **Il ne doit plus être possible de résumer le niveau comme « deux bandes parallèles séparées
   par une ligne rose ».** C'est le critère de sortie de l'opérateur, et il se juge **en
   regardant**, pas en mesurant.
7. **NOUVEAU — aucun pas régulier.** Aucune batterie, aucune installation ne doit être
   reproductible par une formule `tous les X mètres`.
8. **NOUVEAU — coût GPU sur Quadro T1000**, protocole `.claude/resources/howto-mesurer-la-perf.md`.
   ⚠️ Un chiffre RTX 4080 ne vaut pas verdict ici.
9. Et la règle qui prime : **une capture regardée** (`ADR-0006`) — et, pour ce plan, **une partie
   jouée** (lot 0).

---

# Ce que ce plan ne fait pas

- **Il ne touche pas aux textures.** Elles sont livrées et correctes ; le défaut restant est
  géométrique. (Le neuvième slot `AA_Gear` reste au backlog : à prendre le jour où un asset le
  demande pour lui-même, pas pour rattraper un pourcentage.)
- **Il ne change aucune mécanique existante** : une tourelle tire toujours en continu et pivote
  lentement, un pont produit tant qu'il vit, un nœud affaiblit le tronçon suivant. Une **échelle**
  s'ajoute ; aucun comportement n'est remplacé.
- **Il ne refait pas la coque depuis zéro** (consigne 1) : découpage, scrolling, matériaux, UV,
  systèmes de tourelles, baies et événements sont conservés.
- **Il n'ouvre pas le LOT 6 (décoration)** de la refonte précédente. Celui-ci attend la validation
  des lots 1 à 5 par l'opérateur, en jouant — c'est le lot 0 de ce plan qui la produit.
- **Il ne crée pas la troisième famille de tourelle** (point-defense) : l'opérateur l'écrit
  « éventuelle », et elle se décide après avoir vu la deuxième jouer.

---

# Ordre et dépendances

```
LOT 0  jouer                    ← prérequis ; peut invalider B, C et D
  │
  ├── LOT A  trois échelles     ← indépendant, ne touche aucun marqueur existant
  │
  └── LOT B  la silhouette      ← rejoue les 24 Y, ACCEPTED_PAD_BAY_PROXIMITY,
       │                          le cliquet de plafond, et REPOSITIONNE les installations
       ├── LOT C  secteurs & ponts
       └── LOT D  le rythme     ← ne peut être mesuré qu'après B
```

⚠️ **A avant B est un choix, pas une contrainte** : c'est la demande de départ de l'opérateur, et
le lot livrable le plus tôt. Le prix est que B rejouera la table `TurretL_NN` — une table, pas une
reforge.

⚠️ **B avant C et D est une contrainte**, pas un choix : C compose sur les volumes de B, et D ne
peut pas être mesuré avant que les marqueurs aient bougé.

## Ce que chaque lot demande à la forge

| Lot | Brief | Nature |
|---|---|---|
| A | `BRIEF-0096` | tourelle légère : assemblage d'un sous-ensemble du kit existant, ≤ 6 primitives |
| B | `BRIEF-0097` | reforge de la coque : largeur variable, relief en creux, repositionnement |
| C | `BRIEF-0098` | secteurs, variantes de baie, pont transversal |
| D | — | pas de forge : mesure et arbitrage |
