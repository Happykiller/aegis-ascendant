---
titre: MOTEUR — cartographie de .claude/
type: index
statut: actif
maj: 2026-08-23
---

# Le cerveau moteur — ce que Claude sait *faire* ici

Inventaire de `.claude/` **au 2026-08-23**, avec la seule colonne qu'un scan automatique ne peut pas
produire : *pourquoi ça existe, et quand s'en servir*.

## Skills

| Skill | Quand l'utiliser | Fichier |
|---|---|---|
| `/jouer` | Mettre le jeu entre les mains de l'opérateur pour un test réel — il **exporte si le build est périmé**, donc on joue le code courant et non le précédent. Tourne en arrière-plan (au premier plan, le délai d'expiration fermerait la fenêtre en pleine partie) et rend la chronologie à la fermeture | `.claude/skills/jouer/SKILL.md` |
| `/asset-image` | Rédiger un prompt d'image **autosuffisant** : le texte à coller, le nom du fichier, son chemin, la commande suivante, la ligne de provenance. L'opérateur génère hors du dépôt | `.claude/skills/asset-image/SKILL.md` |
| `/capitalize` | Fin de session : verser ce qui a **coûté** dans le bon réceptacle, et l'indexer | `.claude/skills/capitalize/SKILL.md` |
| `/cloture` | Refermer la session : capitaliser, committer, pousser, arrêter ce qui tourne, prouver que c'est clean | `.claude/skills/cloture/SKILL.md` |

## Sous-agents

Un sous-agent existe pour **une** raison : garder hors du contexte principal soit un volume de bruit,
soit une expertise à part. Aucun d'eux n'écrit du code de gameplay.

| Agent | Pourquoi il est isolé du contexte principal | Fichier |
|---|---|---|
| `asset-forge` | Production créative lourde, pilotée par un brief versionné (ADR-0004). La session principale reste le **concepteur** : architecture, intégration, review | `.claude/agents/asset-forge.md` |
| `godot-verifier` | Absorbe ~50 lignes de bruit de `check.sh`/export/deploy pour ne rendre que trois faits : est-ce vert, combien ça coûte, à quoi ça ressemble | `.claude/agents/godot-verifier.md` |
| `godot-reviewer` | Relit un diff contre les **règles dures** (typage, allocations, pooling, autoloads) et rend un verdict classé. Lecture seule — ne corrige jamais | `.claude/agents/godot-reviewer.md` |
| `balance-prober` | Joue l'arc en temps réel et rend sa chronologie. Sert l'équilibrage sans toucher aux Resources | `.claude/agents/balance-prober.md` |
| `spec-auditor` | Audite le code contre **une section** de la spec (fan-out : une instance par section), en tenant compte des ADR qui priment | `.claude/agents/spec-auditor.md` |

## Hooks

| Événement | Ce qu'il automatise | Fichier |
|---|---|---|
| `SessionStart` *(prévu)* | Accueil de session : scanne `.claude/` et rappelle skills, agents et hooks disponibles | `.claude/hooks/welcome.py` |

> ⚠️ **Constaté le 2026-08-23 : `welcome.py` n'est branché nulle part.** Il n'est référencé ni dans
> `.claude/settings.local.json` (qui ne contient que trois permissions), ni dans
> `~/.claude/settings.json` — dont le `SessionStart` global appelle `~/.koa/koa-hook.sh`, qui ne
> mentionne pas ce fichier. Le script existe et paraît complet (162 lignes), mais **il ne s'exécute
> pas**. À COMPLÉTER : le brancher, ou le retirer.

## MCP

| Serveur | Ce qu'il donne accès | Config |
|---|---|---|
| *(aucun au niveau projet)* | — | pas de `.mcp.json` |

Les serveurs MCP visibles en session (Atlassian, Playwright…) viennent de la configuration
**globale** de l'utilisateur, pas de ce dépôt.

## Ressources de méthode

`.claude/resources/` n'est pas un exécutable du moteur, mais il en fait partie : c'est le savoir de
**méthode** (comment vérifier, comment mesurer, comment réviser un asset). Il a son propre index —
[`.claude/resources/INDEX.md`](../../.claude/resources/INDEX.md) — et la frontière avec cette KB est
posée dans [`README.md`](README.md).

## Complémentarité `MOTEUR.md` ↔ accueil de session

Si `welcome.py` est un jour branché, les deux ne feront pas doublon : le hook dit **ce qui est
disponible maintenant** (il scanne), cette page dit **pourquoi ça existe et quand s'en servir**.
