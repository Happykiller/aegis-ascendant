---
titre: Process — livrer sur ce projet
type: regle
statut: actif
maj: 2026-08-23
---

# Process

## Definition of Done (spec §35)

Une tâche n'est **terminée** que si les quatre sont vraies :

1. `./scripts/check.sh` est **vert** ;
2. le comportement est **vérifié** — en headless, et **sur Windows si c'est visuel** ;
3. la doc ou l'ADR est à jour ;
4. le commit est fait, **conventionnel** (`feat:`, `fix:`, `test:`, `perf:`, `docs:`, `chore:`),
   à l'impératif, petit, un seul objectif.

« Ça compile » n'est pas une preuve de comportement. « J'ai regardé le rendu studio » non plus :
le studio n'a ni l'éclairage, ni le fond, ni l'échelle réelle du sujet à l'écran — juger **en jeu**,
sur une capture regardée à l'échelle 1:1. *(Cette ligne disait « le post-traitement rétro écrase » ;
`ADR-0045` a retiré ce filtre — le réflexe reste, sa raison a changé.)*

## Décider : un ADR, pas un commentaire

Une décision qui écarte une option au profit d'une autre s'acte dans `docs/decisions/ADR-NNNN-*.md`,
avec son contexte et ce qu'elle amende. **Les ADR priment sur la spec.** Dix-neuf existent ; ils
sont la source la plus fiable du projet, parce qu'ils portent le *pourquoi* et l'alternative écartée.

## Produire de la matière créative : un brief, pas une improvisation

Toute production créative ou lourde (assets, palettes, scripts Blender, lore, SFX) passe par le
sous-agent `asset-forge` et un **brief versionné** (ADR-0004) :

1. rédiger `docs/forge/briefs/BRIEF-NNNN-<slug>.md` (gabarit : `docs/forge/BRIEF_TEMPLATE.md`) ;
2. invoquer `asset-forge` avec le brief — il lit d'abord `docs/forge/CHARTE_CREATIVE.md` ;
3. **revoir** (conformité charte, IP, formats, provenance), puis intégrer et committer.

Tout asset livré a sa ligne dans `assets/licenses/ASSET_PROVENANCE.csv` (spec §24.7).

⚠️ **Un livrable de forge n'est pas un asset validé tant qu'il n'a pas été rendu et regardé**
(ADR-0006). Et un contrat d'export qui passe ne dit rien de la **forme** : cinq mesures (bbox,
triangles, matériaux, pivot, attaches) ne parlent pas de silhouette. Méthode de revue :
`.claude/resources/pratique-revue-asset.md`.

## Capitaliser, puis clore

En fin de session : `/cloture` (capitalise, committe, pousse, arrête ce qui tourne). Pour
capitaliser seul : `/capitalize`. Voir [`../MOTEUR.md`](../MOTEUR.md).
