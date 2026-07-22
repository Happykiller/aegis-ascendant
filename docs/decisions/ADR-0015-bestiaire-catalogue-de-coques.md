# ADR-0015 — Le bestiaire catalogue des coques, et ne recopie aucune valeur de jeu

- **Statut** : accepté
- **Date** : 2026-07-22
- **Portée** : `scenes/ui/codex.tscn`, `scripts/ui/codex_*.gd`, `resources/data/codex_entry.gd`,
  `resources/codex/*.tres`
- **Contexte spec** : §19 (interfaces) ; s'appuie sur **ADR-0012** (écrans en langage d'interface)
  et **ADR-0008** (les `.glb` portent des marqueurs nommés)

## Contexte

L'écran d'accueil reçoit une entrée **LE BESTIAIRE** : une coque à la fois, en 3D, plein cadre,
manipulable (rotation, zoom), animée, avec ses caractéristiques en langage HUD.

Deux questions se posaient, et une réponse par réflexe aurait été mauvaise dans les deux cas.

### 1. Que catalogue-t-on — des ennemis, ou des coques ?

Le jeu compte **13 ennemis** mais **5 modèles 3D**. Huit des neuf `resources/enemies/*.tres`
partagent le fuseau du Needle Scout et ne diffèrent que par la trajectoire, les points de
structure, la vitesse et le score.

Une fiche par ennemi produirait **huit fiches consécutives montrant exactement le même vaisseau**.
Le modèle 3D — qui est tout l'intérêt de l'écran — cesserait d'être une information dès la
deuxième.

### 2. D'où viennent les chiffres affichés ?

Une fiche technique affiche des points de structure, une vitesse, une cadence de tir, un score.
Toutes ces valeurs **existent déjà**, dans trois endroits distincts :

| Coque | Source réelle |
|---|---|
| Specter-9 | `resources/player/specter9_stats.tres` (`PlayerStats`) |
| Ennemis | `resources/enemies/*.tres` (`EnemyData`) |
| Boss | des `@export` posés **sur la scène de gameplay**, pas dans une Resource |

Les recopier dans la fiche était la solution évidente, et elle est fausse : au premier
rééquilibrage, le bestiaire annoncerait des valeurs périmées **sans que rien ne le signale**. Une
fiche technique qui ment est pire qu'une absence de fiche.

## Décision

### Une fiche par COQUE, les variantes listées dedans

`resources/codex/*.tres` compte **cinq** fiches — une par `.glb`. La fiche du Needle Scout porte un
bloc **« PROFILS DE VOL (8) »** qui liste ses huit variantes avec, pour chacune, le nom de sa
trajectoire, ses points de structure, sa vitesse et son score. L'information reste complète ; le
modèle 3D reste une information.

### La fiche POINTE vers les valeurs, elle ne les copie pas

`CodexEntry` ne contient aucune valeur de gameplay. Elle porte **un pointeur** vers l'unique source
de vérité, et `validate()` refuse qu'il y en ait deux :

```gdscript
@export var player_stats: PlayerStats
@export var enemy_data: EnemyData
@export var boss_scene: PackedScene
# validate() : exactement UNE des trois.
```

Corollaire pour les boss : leurs valeurs vivent sur une scène. On les lit par
`PackedScene.get_state()` — **sans instancier**. Instancier `pale_leviathan.tscn` ferait tourner
`boss_controller._ready()`, donc une entrée en scène, des tirs et une recherche de `BulletManager`,
dans un écran de menu.

### Les dimensions se MESURENT, elles ne se saisissent pas

Longueur, envergure et hauteur sont calculées à l'exécution sur la boîte englobante des maillages
de la coque réellement affichée, avant application de la feuille de détail et des traînées de
réacteur. Le compte de polygones vient des mêmes maillages. Une coque reforgée met donc sa fiche à
jour toute seule, et le recadrage automatique de la caméra s'en déduit aussi.

### Ne reste en dur que ce qui n'existe nulle part : la fiction

Désignation, classe, constructeur, masse, équipage, statut, notice. Produits par la forge sur brief
versionné (**BRIEF-0037**, ADR-0004), livrés dans `docs/forge/output/codex_hull_datasheets.md`.

### On tourne le modèle, pas la caméra

Une caméra en orbite garde les lumières fixes par rapport à la coque : le relief ne bouge plus, et
une coque sombre le reste. En tournant le modèle sous des lumières fixes, les arêtes s'allument
l'une après l'autre — c'est toute la raison d'être d'un présentoir.

Le plateau est à deux étages, `Tilt` (tangage) **au-dessus** de `Yaw` (lacet) : dans cet ordre-là,
et pas l'inverse, la coque bascule autour de l'axe horizontal de l'**écran** quel que soit son
lacet. L'ordre inverse la ferait basculer autour de son propre axe, et le geste « je la penche vers
moi » cesserait de fonctionner dès qu'elle est de profil.

### Les pièces mobiles sont animées en démonstration

`ShipFlight` reçoit deux ratios oscillants de périodes non harmoniques (7,0 s et 4,3 s) : les ailes
à flèche variable balaient toute leur course, les volets se déportent en opposition, les pétales de
tuyère s'ouvrent et se referment. Un vaisseau figé ne dit pas ce qu'il fait — et le mécanisme le
plus travaillé du projet (BRIEF-0033 à 0036) ne se voyait jusqu'ici qu'en vol, de loin.

## Conséquences

- Ajouter une coque au bestiaire = un `.glb`, une fiche `.tres`, une ligne dans `_ROSTER`. Aucune
  valeur à tenir à jour.
- Rééquilibrer un ennemi met le bestiaire à jour **sans y toucher**.
- `tests/unit/test_codex_entries.gd` teste les fiches **réellement embarquées** : un pointeur
  cassé, une variante disparue ou un accent dans un champ affiché en capitales échouent à la porte
  de qualité, et non sur un écran que personne n'ouvre.
- L'écran est joignable en capture par `++ --goto-codex --codex-entry=N` : les cinq fiches sont
  regardables sans naviguer à la main (ADR-0006 — un asset non regardé n'est pas validé).

## Ce qui a été écarté

- **Treize fiches, une par ennemi** — huit montreraient le même modèle.
- **Cinq fiches sans les variantes** — la vraie diversité du jeu (les trajectoires) disparaîtrait
  du catalogue.
- **Un overlay au-dessus du diorama de l'accueil** — le bestiaire monte son propre présentoir, sa
  caméra et ses lumières ; il aurait fallu masquer le diorama et lutter contre sa chorégraphie.
- **Les tourelles et les balises seules** — ce sont des pièces de la citadelle, pas des coques.
  Elles apparaissent dans sa fiche, comptées sur sa coque.

## Addendum du 22/07/2026 — l'Aegis Citadel, et la famille de coque

Le vaisseau mère avait été écarté comme « décor ». C'était une erreur de classement : l'opérateur
l'a réclamé le jour même, et il a raison — la citadelle est une coque majeure, le joueur finit
par la piloter, et c'est la plus animée du jeu.

Elle a forcé une distinction que les cinq premières fiches ne rendaient pas nécessaire.
**L'Aegis Citadel n'a aucune valeur de combat** : ni points de structure, ni vitesse, ni cadence de
tir n'existent pour elle dans le code. Elle n'est pas un objet destructible.

`CodexEntry` reçoit donc un champ **`family`** :

| Famille | Source de stats | Trois lignes centrales | Animation |
|---|---|---|---|
| `FIGHTER` | exactement une (`PlayerStats` / `EnemyData` / scène de boss) | STRUCTURE, VITESSE, CADENCE, avec jauges | `HullDetail` + `ShipFlight` |
| `FORTRESS` | **aucune**, et `validate()` en refuse une | TOURELLES, BALISES, BATTERIES, **sans jauge** | `CitadelDetail` + `CitadelLife` |

Deux points de méthode, tous deux hérités de la règle centrale de cet ADR :

1. **Les équipements sont COMPTÉS sur la coque**, par préfixe de marqueur (`Turret_`, `Beacon_`,
   `Muzzle_Battery`), exactement comme les dimensions sont mesurées. Ajouter une septième tourelle
   au `.glb` met la fiche à jour toute seule.
2. **Pas de jauge sous un décompte.** Six tourelles ne se lisent pas sur une échelle : une barre y
   inventerait un maximum qui n'existe pas. `docs/BACKLOG.md` mettait déjà en garde contre le
   réflexe inverse — « ne pas forcer le gabarit coque sur eux, c'est en le forçant qu'on obtient
   des colonnes de tirets ».

Fiction livrée par la forge sur **BRIEF-0038**.
