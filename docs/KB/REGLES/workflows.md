---
titre: Workflows — les enchaînements outillés, et leur ordre
type: regle
statut: actif
maj: 2026-08-23
---

# Workflows

Chaque enchaînement ci-dessous est **encodé** quelque part : un script, un skill, un sous-agent. La
règle du projet est de les **appeler**, pas de les refaire à la main — ils ont tous été refaits à la
main au moins une fois, et ratés.

## Coder → vérifier → livrer

```
écrire  →  ./scripts/check.sh  →  (si visuel) ./scripts/play.sh ou une capture  →  commit
```

- `check.sh` fait l'import **puis** les tests. Le runner nu ne fait pas l'import : tout `class_name`
  neuf y rend `Identifier not declared`.
- Le sous-agent **`godot-verifier`** absorbe le bruit de build/deploy et ne rend que le verdict
  (« est-ce vert, combien ça coûte, à quoi ça ressemble »).
- Le sous-agent **`godot-reviewer`** relit un diff contre les règles dures — lecture seule.

## Juger un rendu

Claude **juge son propre rendu** par capture PNG depuis WSL ; inutile de solliciter l'opérateur.
⚠️ Effacer `capture.png` **avant** chaque lancement et exiger la ligne `saved`, sinon on juge un PNG
périmé ; les flags de jeu passent **après `++`** ; `--capture-after` compte des **images**, pas des
secondes. → `.claude/resources/howto-verifier-un-rendu.md`.

Ce qu'une capture ne peut pas dire : « est-ce que ça arrive, et une seule fois ». Ça, c'est un test.
→ `.claude/resources/pratique-verifier-par-test.md`.

## Mesurer un coût

Temps GPU par image, jamais le FPS d'un lancement automatisé, et toujours avec la machine qui l'a
produit. Isoler un effet = mesurer avec **et** sans. → `.claude/resources/howto-mesurer-la-perf.md`.

## Produire un asset

```
brief versionné  →  asset-forge  →  rendu + revue côte à côte  →  provenance CSV  →  intégration
```

Skill `/asset-image` pour rédiger un prompt d'image **autosuffisant** (l'opérateur génère hors du
dépôt : un prompt qui suppose du contexte est un prompt raté).

## Équilibrer

Le sous-agent **`balance-prober`** joue l'arc en mode démo et rend la chronologie (durées par phase,
scores, morts). Il ne modifie jamais les Resources de gameplay.

⚠️ Aucun de ces outils ne remplace le **playtest de l'opérateur** : c'est lui qui a dit « beaucoup
beaucoup trop long » du boss final, ce qu'aucune mesure automatique n'avait signalé (ADR-0019).
