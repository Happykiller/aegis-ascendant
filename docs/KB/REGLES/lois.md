---
titre: Lois — ce qu'on ne fait jamais sur ce projet
type: regle
statut: actif
maj: 2026-08-27
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
  1,30 × 2,41 : le disque couvrait les ailes et **pas le nez**, qui traversait les murs. Un
  vaisseau est plus long que large — il se décrit en **capsule**, pas en cercle.
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
