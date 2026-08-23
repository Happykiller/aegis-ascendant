---
titre: Lois — ce qu'on ne fait jamais sur ce projet
type: regle
statut: actif
maj: 2026-08-23
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
