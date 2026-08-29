---
titre: DAT — Dossier d'Architecture Technique
type: index
statut: actif
maj: 2026-08-23
---

# DAT — architecture technique

Ce que la machine fait tourner, et avec quoi. Les pages ci-dessous portent les faits **lus dans le
dépôt** (fichiers de dépendances, scripts de bootstrap, `project.godot`), pas des souvenirs.

| Page | Ce qu'elle couvre | Statut | MAJ |
|---|---|---|---|
| [couches.md](couches.md) | ⚠️ **À lire avant d'écrire un niveau ou un boss.** Les quatre couches du jeu — données, moteur, runtime, level design — et la question unique qui range n'importe quoi | actif | 2026-08-29 |
| [stack.md](stack.md) | Moteur, langage, outils de la chaîne d'assets, versions épinglées et **où elles sont épinglées** | actif | 2026-08-23 |
| [arborescence.md](arborescence.md) | Les dossiers de premier niveau et le rôle de chacun | actif | 2026-08-23 |
| [environnements.md](environnements.md) | Où l'on développe, où l'on teste, et par quelles commandes | actif | 2026-08-23 |

## Sources de premier rang — à lire avant d'écrire ici

Ces documents existent déjà et **font autorité**. La KB les référence, ne les recopie pas :

| Document | Portée | Réserve |
|---|---|---|
| [`docs/architecture/ARCHITECTURE_TECHNIQUE.md`](../../architecture/ARCHITECTURE_TECHNIQUE.md) | Vue d'ensemble du code : autoloads, plan de gameplay, director, projectiles, boss, UI, perf | ⚠️ Daté du **2026-07-11** — postérieur à rien de ce qui a suivi (ADR-0010 à ADR-0019) |
| [`docs/SPEC_AEGIS_ASCENDANT.md`](../../SPEC_AEGIS_ASCENDANT.md) | Cahier des charges complet (2813 lignes) ; son **§0 est un contrat d'exécution** | Les ADR **priment** sur elle en cas d'écart |
| [`docs/decisions/`](../../decisions/) | 19 ADR — décisions actées, avec leur contexte et ce qu'elles amendent | La source la plus fiable du projet |
| [`docs/balance/graybox_baseline.md`](../../balance/graybox_baseline.md) | Mesures de référence du jalon graybox | ⚠️ Un chiffre de perf n'a de sens **qu'avec sa machine** |
