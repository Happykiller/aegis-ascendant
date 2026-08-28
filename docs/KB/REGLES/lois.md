---
titre: Lois — ce qu'on ne fait jamais sur ce projet
type: regle
statut: actif
maj: 2026-08-28
---

# Lois

Non négociables. Une loi ne se contourne pas « juste pour cette fois » : si elle bloque, on
s'arrête et on demande.

## Propriété intellectuelle (spec §0.2, assoupli par ADR-0009)

- **Aucun nom, silhouette ou élément identifiable** de Macross, Robotech ou d'une autre licence.
- **Exception unique et actée** : le Specter-9 reprend le plan de sa planche de référence, dérives
  comprises (**ADR-0014**). Elle ne s'étend à **aucune** autre coque ; marquages, livrées et noms
  restent exclus partout.
- Les planches d'inspiration tierces sont versionnées **uniquement** dans
  `assets/reference/inspiration/`, jamais mélangées à `concepts/` — la frontière rend possible une
  purge IP sans toucher à nos propres planches (ADR-0005, ADR-0009).
- **Aucun asset sans licence enregistrée** ; aucun asset temporaire non signalé.

## Intégrité de la vérification

- **Ne pas contourner un test. Ne pas cacher une erreur d'import ou d'export.** Un check vert obtenu
  en désarmant l'instrument ne vaut rien.
- ⚠️ **Un test peut être vert et MORT, sans que personne n'ait rien désarmé.** GDScript n'a pas
  d'exception : sur un appel invalide il journalise `SCRIPT ERROR` et **abandonne la méthode**. Les
  assertions restantes ne tournent jamais, le tableau des échecs reste vide, le harnais annonce
  `[PASS]`. Deux gardes de `test_hud_layout` n'ont ainsi **rien gardé depuis leur écriture**
  (`as Control` sur un `CanvasLayer` → `null`), et la disparition d'un membre interrogé par un test
  est passée au travers le 2026-08-28. Deux filets, et il faut **les deux** : **zéro assertion =
  échec** (`tests/test_runner.gd`) et **`SCRIPT ERROR` = porte rouge** (`scripts/check.sh`, en ne
  filtrant QUE `SCRIPT ERROR:` — les `ERROR:` sont provoqués exprès et annoncés).
  Le détail : [`.claude/resources/pratique-un-test-vert-peut-etre-mort.md`](../../../.claude/resources/pratique-un-test-vert-peut-etre-mort.md).
- **Un garde se vérifie en le faisant TOMBER.** Injecter l'erreur qu'il doit attraper, constater la
  porte rouge, retirer l'injection. Un garde jamais vu rougir n'est pas un garde — c'est exactement
  ce que le cas ci-dessus démontre.
- Ne jamais lancer Godot **sans `--headless`** dans WSL (ADR-0002).

## Les corps ne se chevauchent pas (posée le 2026-08-27)

> « De façon globale dans le jeu je veux maintenant qu'on gère la physique, les objets n'ont
> plus le droit de se chevaucher : vaisseaux, boss, mur, réacteur, etc. » — l'opérateur

- **Deux corps solides ne peuvent jamais occuper le même endroit.** Ça vaut pour le chasseur, les
  boss et leurs pièces, les murs, le réacteur, le décor solide. Un chevauchement visible est un
  **défaut**, pas une approximation acceptable, même bref, même partiel.
- **La collision passe par [`PlaneCollider`]** (`ADR-0032`), jamais par un test écrit sur place.
  Un obstacle nouveau se déclare en **forme** ; il n'ajoute pas de code de collision.
- **Un corps se décrit par sa taille RÉELLE, mesurée sur le modèle**, jamais par un chiffre
  plausible. ⚠️ Le chasseur a été donné pour un disque de 0,85 alors que `specter_9.glb` mesure
  **1,752 × 2,46** (hiérarchie parcourue, transformations appliquées) : le disque couvrait les
  ailes et **pas le nez**, qui traversait les murs. Un vaisseau est plus long que large — il se
  décrit en **capsule**, pas en cercle.
  ⚠️ **Cette loi a elle-même porté un chiffre faux — 1,30 × 2,41 — pendant trois jours.** C'est
  la lecture des bornes brutes des accesseurs du `.glb`, sans composer les transformations des
  nœuds : les canons de bout d'aile sont montés décalés, donc ils manquent à l'appel. **Un `.glb`
  ne se mesure pas sans parcourir sa hiérarchie**, et le projet s'est fait prendre trois fois
  (25/08, 27/08, 28/08).
- **Une capsule n'est pas une boîte : le rayon s'ajoute aux DEUX bouts.**
  `PlaneCollider.capsule_blocks()` promène un disque de `body_radius` le long du segment
  `−half_length … +half_length`, donc l'étendue réelle vaut **`half_length + radius`**, jamais
  `half_length` seule. Mesurer juste ne suffit pas : il faut **convertir**. La demi-longueur du
  `.glb` (1,23) versée telle quelle dans `body_half_length` a donné un chasseur de **4,22 dans
  l'axe pour une coque de 2,46** — 0,88 unité de coque fantôme devant le nez, et autant derrière
  (`ADR-0034`). L'étendue se lit par `PlayerStats.body_reach()`, jamais recalculée à la main.
- ⚠️ **Un garde qui refuse la valeur juste encode une convention fausse — suspecter le garde.**
  Ici `validate()` exigeait `body_half_length >= body_radius` (« un vaisseau n'est pas plus large
  que long ») : vrai de la COQUE, faux du segment. Il rendait 0,35 impossible et a **verrouillé
  l'erreur** au lieu de l'attraper. Un invariant se pose sur la grandeur comparable — ici
  l'étendue, pas le demi-segment.
- **Ce qui arrête un CORPS et ce qui arrête un TIR sont deux questions distinctes**, et deux
  listes : `fill_solids()` d'un côté, `fire_screens()` de l'autre. Un noyau peut être
  infranchissable sans faire écran au tir qui le vise. Les confondre a désactivé une phase
  entière — versé parmi ce qui bloque une balle, le noyau se faisait **écran à sa propre cible**,
  et le joueur voyait des impacts sans que la jauge bouge (`ADR-0034`). ⚠️ Et un écran est de la
  **géométrie**, jamais une cible posée à l'endroit où l'on croit que le tir passe : la fausse
  cible qui simulait le blindage n'arrêtait qu'un disque de mur et ratait par construction les
  flux latéraux des canons d'aile.
- **La collision et l'image lisent la même donnée.** Si l'une change, l'autre suit dans le même
  commit. Un mur qui bloque ailleurs qu'où il est dessiné est le pire défaut possible : le joueur
  ne peut pas l'apprendre.
- Le contact qui **blesse** (tir, ennemi kamikaze) reste un mécanisme à part : ne pas confondre
  « ne se chevauchent pas » avec « ne se touchent pas ».
- ⚠️ **… tant qu'ils jouent dans la même catégorie de poids** (`ADR-0033`, amendement du même jour).
  Un corps trop léger n'est pas un obstacle amoindri : **il n'est pas un obstacle**. Il n'est pas
  versé dans les formes du niveau, il est **écrasé** au contact — détruit par le chemin normal
  (score, explosion), et payé en bouclier par celui qui l'a broyé. La règle sans la masse traitait
  un éclaireur comme un mur de réacteur, et rendait les vagues injouables : « si on ne les tue pas
  assez vite, ils nous empêchent de bouger » (playtest 2026-08-27).
- **La masse se déclare dans la fiche d'identité** (`EnemyData.mass`, `PlayerStats.mass`), et le
  SEUIL se règle chez celui qui écrase (`crush_mass_ratio`) — jamais sur chaque fiche d'en face.
  Tout ce qui est versé dans un `PlaneShapes` est de masse **infinie par construction** : une forme
  ne porte pas de masse, c'est ce qui fait d'elle un obstacle.
- **Les surfaces ont une VITESSE, et une seule règle s'applique partout** (2026-08-28) : au
  contact, la vitesse d'un corps selon la normale de la surface ne peut pas être inférieure à
  celle de la surface. Une face de front arrête « comme une voiture dans un mur », en biais on
  glisse, le BOUT d'un mur qui tourne entraîne, sa FACE glisse sous le corps. Tout dégagement
  « après coup » par un chemin choisi est interdit : il a donné un ressort, un convoyeur et un
  vaisseau figé. `PlaneCollider.move_capsule()` est la seule entrée du pilotage.
- **Quatre représentations, UNE convention.** Image, corps (`PlaneShapes`), cibles
  (`BulletTarget`), écrans de tir — tout ce qui pose une forme dans le monde passe par
  `GameplayPlane.to_world`, sommets et pivots compris. ⚠️ Le décor de la chambre a tourné **à
  l'envers** de sa collision pendant un jour (maillage en miroir + pivot négatif) : la garde
  `test_the_decor_walls_are_where_the_collision_walls_are` compare un sommet du décor à l'arc de
  collision. Toute nouvelle pièce mobile a droit à la même garde.
- **Une unité ne peut jamais être à la fois un mur et une proie.** Les deux listes se dérivent du
  même test, à la même image ; les séparer laisserait le chasseur prisonnier d'un cadavre.

## Architecture

- **Jamais d'identifiant global d'autoload dans un script** (`GameState.foo()`) : ça casse la
  compilation en mode `--script`. Câbler par signal/injection, ou cache typé
  `const XScript := preload(...)` + `@onready var _x: XScript = get_node("/root/X")`.
- **Pas de multijoueur, pas de monde ouvert, pas de backend**, aucune dépendance native qui ne soit
  justifiée par un profilage.

## Dépôt

- Le dépôt est **imbriqué** dans le home : ne **jamais** l'ajouter depuis un dépôt parent, et ne
  jamais traiter `/home/admin` comme un dépôt Git.
- **Un seul écrivain à la fois.** Deux agents qui écrivent en parallèle produisent des commits
  mélangés et une porte rouge sans coupable ; `C:\tmp` et le processus Windows ne sont pas cloisonnés
  par les worktrees. → `.claude/resources/pratique-ecrivain-unique.md`.
