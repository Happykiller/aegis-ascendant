---
titre: Environnements — développer, tester, livrer
type: dat
statut: actif
maj: 2026-08-23
---

# Environnements

## Deux machines, une seule frontière (ADR-0002)

| Où | Ce qu'on y fait | Contrainte |
|---|---|---|
| **WSL2 Debian** | Écrire le code, importer, tester, exporter | **Jamais de commande Godot sans `--headless`** : pas de GPU fiable |
| **Windows natif** | Regarder et jouer | Le build est copié dans `C:\tmp\aegis-ascendant\` puis lancé |

⚠️ `C:\tmp` et le processus Windows **ne sont pas cloisonnés par les worktrees** : un déploiement
tue le jeu d'un autre agent. Un seul écrivain à la fois — cf.
`.claude/resources/pratique-ecrivain-unique.md`.

## Les commandes canoniques (ADR-0003)

Elles sont listées dans [`CLAUDE.md`](../../../CLAUDE.md) et **ce qu'elles évitent** est documenté
dans le tableau « Outillage encodé » de
[`.claude/resources/INDEX.md`](../../../.claude/resources/INDEX.md). Deux points qui coûtent cher
quand on les ignore :

- **`./scripts/check.sh` est la porte de qualité, jamais `test_runner.gd` seul** : le runner nu ne
  fait pas l'import, donc tout `class_name` neuf rend `Identifier not declared` — une itération
  perdue à chercher une faute qui n'existe pas.
- **`./scripts/play.sh`, jamais `deploy-win.sh` seul** : `deploy-win.sh` n'exporte pas, on joue donc
  le build précédent sans le savoir.

## Mesurer une performance

Le **FPS d'un lancement automatisé ne mesure rien** (Windows bride la présentation) : la grandeur
utile est le **temps GPU par image**. Et un chiffre n'a de sens **qu'avec sa machine** — le même
build rend ~0,84 ms sur la RTX 4080 de la spec et ~12,0 ms sur le portable Quadro T1000 utilisé
depuis le 2026-07-20. Méthode : `.claude/resources/howto-mesurer-la-perf.md`.

> **À COMPLÉTER — question ouverte pour l'opérateur.** Le poste Quadro T1000 est-il la **machine de
> référence** ou un poste d'appoint ? Tant que ce n'est pas tranché, la spec (§ machine de référence
> RTX 4080, cible « 120 FPS à 1440p ») et le poste réel divergent d'un facteur ~14. Trancher
> impliquerait de réviser `docs/SPEC_AEGIS_ASCENDANT.md:9`, ADR-0002 et la cible de framerate.
