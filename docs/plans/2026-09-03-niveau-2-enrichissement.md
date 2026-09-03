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

# LOT A — Trois échelles de défense — ✅ LIVRÉ (2026-09-03)

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

## A3 — Les batteries — ⚠️ **RÉSOLU AUTREMENT QUE PRÉVU, ET MIEUX**

Ce plan proposait des marqueurs neufs `TurretL_NN` dans la coque. **Ce n'est pas ce qui a été
fait**, pour deux raisons dont la seconde est la bonne :

1. un marqueur neuf demande une reforge du `.glb` (Blender n'est même pas installé sur ce poste) ;
2. surtout, il aurait posé la batterie en **absolu**. Le jour où le lot B déplace une
   installation, chaque batterie serait restée en arrière, orpheline de ce qu'elle garde.

**Une batterie est donc enfant du marqueur de son HÔTE, décalée en local** (`BATTERIES` dans
`cortege_hardpoints.gd`). C'est ce que dit la consigne 9 — « 2 à 4 petites pièces autour d'une
grosse installation » — et ça annule le coût annoncé : **le lot B n'a rien à rejouer**, les
batteries suivent leurs hôtes sans qu'une ligne de la table ne change.

Livré : **7 batteries, 21 pièces**, sur 24 installations. Deux respirations franches (rien entre
s = 214 et 246, rien entre 348 et 410).

### ⚠️ Ce que la capture a corrigé, et que le calcul n'aurait pas trouvé

La première table écartait les pièces le long de la coque. Tests verts, distances respectées,
positions valides — et **à l'écran, chaque tourelle arrivait seule** : des files, jamais un
groupe. Seul le fait de regarder l'a montré (`ADR-0006`).

La cause est mesurable, et elle vaut pour tout le reste du lot :

| Palier | Largeur utile | Il faut |
|---|---|---|
| Pont médian (\|x\| 7,35 → 10,30) | **2,95 m** | ~4,05 m entre une petite et le socle de sa lourde |
| Pont intérieur (\|x\| 2,20 → 6,80) | **4,60 m** | idem |

⚠️ **Aucune grappe TRANSVERSALE n'est possible sur cette coque.** Mais deux petites n'ont besoin
que de 1,70 m l'une de l'autre : la batterie se pose donc en grappe serrée, **décalée de 4 à 7 m
devant son hôte**. Chaque batterie tient désormais dans moins de 3 m de coque, et deux tests
neufs le tiennent (`test_a_battery_reads_as_one_group_not_a_file`,
`test_two_pieces_of_a_battery_never_overlap`).

### ⚠️ Et la contremarche de chine, qui aurait coûté une capture de plus

Une pièce **hérite du Y de son hôte**. Le pont a deux paliers séparés par une marche de 60 cm à
\|x\| entre 6,80 et 7,35. Une batterie qui franchit la marche **flotte au-dessus du vide**, en
silence. Chaque offset garde donc sa pièce sur le palier de son hôte, et le test le vérifie sur la
**coque livrée**, pas sur cette phrase.

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

## A5 — Ce qui prouve le lot — état au 2026-09-03

| Preuve | État |
|---|---|
| Les invariants 2, 3, 5, 8 bouclent sur les deux échelles | ✅ `cortege_tuning.gd` |
| **Invariant 3 bis neuf** : la hiérarchie est déclarée, pas espérée (PV, cadence, fenêtre) | ✅ |
| 15 tests neufs (`test_cortege_light_turrets.gd`), 799 au total, 0 échec | ✅ |
| Les hôtes existent sur la **coque livrée** — un nom de travers = batterie jamais montée, en silence | ✅ |
| Aucune pièce ne franchit la contremarche, ni ne chevauche son hôte ou sa voisine | ✅ |
| Le journal confirme le montage : `17 tourelles (+21 légères)` | ✅ |
| **Capture regardée** : la silhouette légère est distincte de la lourde et bien assise | ✅ |
| **La grappe se lit-elle comme un groupe en jeu ?** | ⏳ **non tranché** — le tronçon 5 est encombré par la patrouille, aucune capture propre du groupe entier. Se juge en jouant |
| **Coût GPU sur Quadro T1000** | ⏳ non mesuré (21 pièces actives de plus) |

### ⚠️ Un réglage mort découvert en chemin, et non reproduit

`turret_burn_damage`, `turret_range` et `turret_beam_half_width` **ne sont lus par aucun script ni
test** depuis qu'`ADR-0040` a remplacé le faisceau par des balles : les dégâts vivent dans le
`ProjectileData`. Leur donner un jumeau léger aurait créé un réglage qu'on croit régler et qui ne
fait rien. L'échelle légère n'a donc que **cinq** réglages, tous branchés, et l'écart de dégâts
entre les deux tirs est borné par un **test** sur les deux Resources.

---

# LOT B — La coque cesse d'être un rectangle

> **B1 ✅, B2 ✅ et B3 ✅ LIVRÉS (2026-09-03)** — la largeur varie, les bords ne sont plus
> jumeaux, et le pont n'est plus plat. **B4 (repositionnement) reste à faire.**

Le plus gros lot, et celui qui porte le critère de sortie de l'opérateur (consigne 20).

## B1 — La largeur varie — ✅ LIVRÉ

`TAPER` va désormais jusqu'à la poupe. **Sept événements de contour** sur les 412 m qui étaient
constants, espacés irrégulièrement (44, 55, 53, 55, 65, 113 m) :

| s | kx | Ce que c'est |
|---|---|---|
| 106 | 0,82 | le col, avant le tronçon 2 |
| 150 | 1,21 | premier épaulement |
| 205 | 0,84 | étranglement |
| 258 | 1,23 | le grand élargissement du tronçon 3 |
| 313 | 0,83 | étranglement |
| 378 | **1,24** | la plateforme d'artillerie — le point le plus large |
| 491 | 0,80 | la poupe se resserre |

**`ky` ne bouge jamais**, et c'est la décision qui rend le lot abordable : la hauteur commande les
paliers du pont, sur lesquels les 24 Y de marqueurs sont échantillonnés. La largeur seule donne le
contour demandé et ne rejoue ni `ACCEPTED_PAD_BAY_PROXIMITY`, ni le cliquet de plafond, ni les Y.
**Le coût annoncé en §C3 n'a donc pas été payé.**

**`_marker_x()`** rapporte chaque marqueur à la largeur locale. Deux effets, dont le second n'était
pas prévu :

1. sans elle, étrangler la coque à 0,82 laisserait `Turret_16` (écrite à 10,20) **au-delà du bord**,
   un affût flottant à côté de son vaisseau ;
2. ⚠️ **et chaque marqueur reste sur son palier PAR CONSTRUCTION.** Le pont intérieur, la
   contremarche et le pont médian s'échelonnent tous par le même `kx` : un marqueur qui le suit ne
   peut plus franchir la marche, quelle que soit la largeur locale. Le problème que le lot A avait
   dû résoudre à la main ne se pose plus.

### ⚠️ Trois choses que le build a refusées, et ce qu'elles ont appris

| Ce qui a été refusé | Par quoi | Ce que ça a appris |
|---|---|---|
| Le tronçon 1 semé de stations jusqu'à **z = −500** | le harnais de **jonction** (« écart de 400 m ») | `TAPER_END` valait 88 (fin du **fuseau**) et vaut 500 (fin de la **table**) ; `_stations(0)` s'en servait pour borner la proue. Un renommage sémantique a changé un calcul à l'autre bout du fichier. D'où `PROW_TAPER_END`, distinct |
| Toute variation sous un **pont d'envol** | l'assertion neuve `_assert_taper_spares_the_bays()` | Elle a arrêté le build sur `Bay_01` dès sa première exécution — qui vit à s = 86, dans le fuseau, à kx = 0,984 **depuis toujours**. L'ouverture, définie par **indices d'anneau**, suit la peau ; c'est le **coaming du kit**, à cotes fixes, qui ne suit pas. Le seuil porte donc sur l'**ampleur** (3 %), pas sur l'égalité |
| Un épaulement à **s = 453** | le harnais **d'UV** (densité 0,141 pour 0,396 requises) | Il tombait sur **Ambry**, l'avant-poste humain greffé sur le bordé, déplié à 0,700 tuile/m. **Une greffe ne s'étire pas avec ce qui la porte** : Ambry rejoint les baies dans la garde |

### Ce que ça coûte, mesuré

- **41 874 triangles** sur 90 000 (46,5 %) — la densification des stations (1,25 m au lieu de 5,00 m
  dans les transitions, sans quoi le contour se lirait en facettes de six mètres) coûte ~1 400 tri.
- **Déterminisme préservé** : `build-hull.sh --check` vert, 0 octet divergent.
- Largeur hors-tout **34,72 m** ; sommet à **−3,200**, le plafond du décor tient.
- Le contrat de largeur a appris à lire `TAPER` — et refuse désormais une table qui dépasserait
  **+25 %**, la borne des consignes.

### Le critère 20, vérifié

Capture au grand élargissement (s ≈ 258) : le contour est **courbe** là où les captures
d'avant-reforge, même niveau et même caméra, montraient deux droites. Largeur mesurée sur l'image :
**1 094 px en haut, 1 517 px en bas**. ⚠️ Une part de cet écart est la perspective — un témoin à
largeur strictement nominale n'a pas pu être isolé (les zones nominales voisinent toujours une
transition). Ce qui tranche est la **forme** du bord, droite avant, courbe maintenant.

## B2 — L'asymétrie — ✅ LIVRÉ, ET PAR LA VOIE QUI ÉTAIT DITE LA PLUS CHÈRE

Ce plan recommandait **(a)** — garder le miroir et poser l'asymétrie par les modules — en réservant
**(b)** (casser le miroir du profil) comme « beaucoup plus cher ». C'est **(b)** qui a été fait, et
l'estimation était fausse pour une raison qu'il vaut la peine d'écrire :

> **La topologie de l'anneau ne change pas d'un point.** Mêmes indices, même ordre, mêmes
> matériaux, mêmes drapeaux de pont. Seules les **abscisses** d'un côté bougent. Rien de ce qui
> indexe l'anneau — `RING_MATERIALS`, `_ring_deck_flags`, `_bay_cell` — n'a besoin de le savoir.

Le coût réel a donc été de **quatre fonctions**, pas d'une refonte : `_asym()`, `_side_scale()`,
`_half_profile(s, side)` et `_ring()`. Et (a) aurait de toute façon échoué sur le critère 20 : un
module posé sur le pont ne change pas le **contour extérieur**, qui est ce que l'opérateur juge.

### Ce qui est livré

`ASYMMETRY` donne un facteur **par bord**, multiplié par celui de `TAPER` :

| s | Bord | Écart | Ce que c'est |
|---|---|---|---|
| 177 | bâbord | **−17,0 %** | le bord se pince d'un seul côté |
| 342 | tribord | **+16,0 %** | épaulement |
| 413 | bâbord | **+13,8 %** | bâbord bombe… |
| 434 | tribord | **−15,0 %** | …et tribord se pince 21 m plus loin : un décalage |

⚠️ **Aucun cumul avec un événement de `TAPER`** : les quatre asymétries sont posées sur des
plateaux où `kx` vaut 1, si bien qu'un bord mesure toujours exactement 14,00 m. Sans cette règle,
un épaulement de +16 % sur une coque déjà élargie de +24 % sortirait des +25 % que les consignes
bornent — et le contrat de largeur le refuserait. Largeur maximale mesurée : **34,72 m** pour une
borne à 35,00.

### ⚠️ Les gardes sont PAR BORD, et c'est ce qui rend le lot possible

Une baie à bâbord ne craint rien d'un épaulement à tribord. Protéger les deux côtés aurait fermé
presque toute la coque — les plateaux à `kx = 1` ne font que 16 à 28 m une fois les installations
protégées, et « quelques dizaines de mètres » est précisément ce que la consigne demande.

### ⚠️ Deux fonctions qui auraient menti en silence

- **`_surface_y(s, x)`** prenait `abs(x)`. C'est la fonction que **tout** le vocabulaire modulaire
  interroge — plaques, nervures, socles, greffes prennent leur base ici, coin par coin. Sur une
  coque asymétrique, elle aurait rendu l'assise de tribord à une pièce de bâbord : jusqu'à 19 % de
  largeur d'écart, donc une base posée sur une peau qui n'est pas la sienne.
- **`_clip_lane()`** rabattait les voies sur *la* demi-largeur. Une lisse rabattue sur tribord
  serait partie en porte-à-faux au-dessus du vide là où bâbord est pincé.

Aucune des deux n'aurait produit d'erreur.

### Ce que ça coûte

**48 678 triangles** sur 90 000 (54,1 %), contre 41 838 avant la densification des transitions
d'asymétrie — ~6 800 tri pour que le bord qui se pince ne se lise pas en facettes, précisément sur
le côté que la consigne 14 veut faire remarquer. Déterminisme préservé, 0 octet divergent.

## B3 — Le relief, en creux — ✅ LIVRÉ

Le décor inerte n'a que **1,26 m** au-dessus du pont (§C4) : la consigne 4 demande « de grands
volumes de plusieurs mètres », et vers le haut c'est impossible. La profondeur, elle, est libre —
8 m entre le pont et la quille.

**Quatre fosses** de 12 × 4,6 m, profondes de **1,55 m**, sur le pont intérieur : s = 136 et 393
(tribord), 228 (tribord), 292 (bâbord).

### ⚠️ Elles ne coûtent que 384 triangles, et c'est une décision de composition

Une fosse occupe **tout le pont intérieur d'un bord**, de |x| = 2,20 à 6,80 — deux abscisses qui
sont **déjà des points du profil**. Un point neuf aurait coûté deux segments d'anneau sur toute la
longueur du vaisseau, à chaque station des cinq tronçons : ~600 triangles par point, pour un creux
local. Et comme les ouvertures de baie, une fosse est définie par **indices d'anneau** : elle se
pince avec le bord qui se pince, sans une ligne de plus.

### ⚠️ Quatre défauts, tous silencieux, et l'ordre dans lequel ils sont tombés

| # | Le défaut | Comment il a été trouvé |
|---|---|---|
| 1 | Les fosses **n'apparaissaient pas au rapport** | Le tableau des modules est une **liste blanche** de labels : `fosses` n'y était pas. Elles ont été construites un build entier sans qu'aucune ligne ne les compte — et l'on a cherché dans le rendu ce qu'il fallait chercher ici. ⚠️ **Ce tableau existe précisément parce qu'une famille de modules a déjà disparu en silence dans ce fichier** |
| 2 | Deux fosses **mordaient un socle** de tourelle | L'assertion neuve `_assert_pits_are_clear()`, dès sa première exécution. En x elles ne les touchaient pas ; leurs **gardes** se recouvraient — un trou de 1,55 m à 72 cm du bord d'un socle |
| 3 | La moitié des faces regardait **du mauvais côté** | Ce fichier n'appelle pas `recalc_face_normals` (les tronçons sont des tubes ouverts, l'heuristique s'y trompe) : le sens d'une face est celui de l'ordre de ses sommets, et cet ordre s'inverse quand la fosse passe à bâbord. **Quatre chances de se tromper par fosse.** D'où `_face_towards()`, qui déclare la **direction voulue** au lieu de l'ordre |
| 4 | Le creux **existait et restait invisible** | Sondé dans le `.glb` (sommets à z = −5,89 aux bons x), rendu en Cycles, mesuré — et introuvable en jeu. Fond en `AA_Greeble`, il se lisait comme un **aplat noir**, le défaut même que `BRIEF-0094` reprochait aux greffes, et il mettait un second grand noir dans le cadre alors que **l'artère doit rester LE creux du vaisseau** |

### ⚠️ Ce qui a finalement rendu la fosse lisible

Le fond est passé en **matière de coque** (`AA_Hull`) et les parois en **noir de creux**
(`AA_Greeble`) — l'inverse de la première écriture. Puis, comme cela ne suffisait toujours pas :
les **deux parois de bout** sont en `AA_Trim`.

> **Sans arête claire, un creux n'est pas un volume : c'est une tache.** Le pont d'envol voisin se
> lit d'un coup d'œil parce qu'il a un coaming clair ; à 23 px/m sous une caméra qui plonge à 70°,
> une fosse anthracite aux parois noires se confond avec les bandes sombres du bordé.

⚠️ **Seulement les deux bouts, pas tout le pourtour** : `BRIEF-0089` a mesuré qu'« un matériau clair
sur une arête **continue** occupe plus de pixels qu'une pièce entière ». Deux plans de 4,6 m
accrochent la lumière ; un ruban de douze mètres aurait redessiné la coque.

### Le détour qui a coûté le plus, et ce qu'il enseigne

Trois captures in-game ont été dépensées à chercher une fosse invisible avant de **sonder le
`.glb`** — qui a répondu en une minute que la géométrie était juste, et déplacé la question du
« est-elle construite ? » vers le « pourquoi ne se voit-elle pas ? ». ⚠️ **Le repère de la sonde
était faux deux fois** (s = 200 − z, puis s = −z) avant qu'on remarque que glTF permute les axes :
`y` porte la station, `z` la hauteur. Une sonde qui rend « 0 sommet » ne prouve rien tant que son
repère n'a pas été vérifié sur une valeur connue.

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

✅ **A est livré, et il ne coûte rien à B.** Les batteries étant ancrées sur leurs hôtes, le lot B
peut déplacer une installation sans toucher une ligne de la table : la garde suit. C'est le seul
endroit de ce plan où la solution retenue s'est révélée moins chère que celle proposée.

⚠️ **B avant C et D est une contrainte**, pas un choix : C compose sur les volumes de B, et D ne
peut pas être mesuré avant que les marqueurs aient bougé.

## Ce que chaque lot demande à la forge

| Lot | Brief | Nature |
|---|---|---|
| A | ~~`BRIEF-0096`~~ | ✅ **aucune forge nécessaire** : la tourelle légère est un assemblage à 0,5 du kit existant (socle, couronne, corps, `turret_barrel_short`), 4 primitives |
| B | `BRIEF-0097` | reforge de la coque : largeur variable, relief en creux, repositionnement |
| C | `BRIEF-0098` | secteurs, variantes de baie, pont transversal |
| D | — | pas de forge : mesure et arbitrage |
