# Process — étendre le ghost : sous-agent ou skill ?

Doctrine héritée du cluster FitDesk (galakrond), éprouvée sur un roster de 8 agents. **S'y aligner
plutôt que d'inventer un dialecte concurrent.**

## Le critère de décision

| | Sous-agent (`.claude/agents/`) | Skill (`.claude/skills/`) |
|---|---|---|
| Nature | **read-heavy**, **fan-out** (une instance par cible) | procédure **déterministe**, déroulée **inline** |
| Sortie | rend un **verdict** | interagit avec l'opérateur |
| Raison d'être | garder le **bruit** hors du contexte de l'orchestrateur (sortie de build, logs, `npm audit`) | l'orchestrateur doit voir chaque étape |

**Le vrai gain d'un sous-agent est l'économie de contexte, pas le stockage d'une check-list.** Sans
ce critère on recrée des agents redondants.

## L'écriture est une exception, pas la norme

Un agent **write-capable** ne se justifie que si : **la mutation est nécessaire par nature** ET **le
scope est verrouillable** ET **le bruit doit sortir du contexte**.

Modèle **« forge »** (le plus verrouillé, à préférer) : **pas d'outil `Edit`/`Write`** — la mutation
passe uniquement par un **script ou une cible Make épinglée**, dont la sortie est confinée à un
répertoire connu. C'est le modèle d'`asset-forge` sur ce projet, et de `legal-pdf-forge` /
`android-artifact-forge` sur FitDesk.

Tout autre besoin d'écriture **reste un skill par défaut**.

## Deux contraintes techniques, non négociables

**1. Placement — toujours `.claude/agents/` à la racine du CWD de session.** Claude Code ne découvre
les sous-agents qu'à deux niveaux : `~/.claude/agents/` (user) et `.claude/agents/` **relatif au
répertoire de lancement de la session**. Il n'y a **pas de scan récursif**. Un agent rangé dans un
sous-dossier est invisible, quel que soit son contenu.

**2. Pas de hot-reload.** Un sous-agent créé pendant une session **n'est pas invocable dans cette
même session** — le registre est résolu au démarrage. Ne pas boucler à essayer de l'invoquer :
soit exécuter sa méthode à la main via Bash en attendant, soit prévenir l'opérateur qu'une nouvelle
session sera nécessaire pour l'essayer.

## Roster actuel d'Aegis Ascendant — 5 agents (1 write-capable)

| Agent | Type | Rôle |
|---|---|---|
| `asset-forge` | **forge** (write via brief) | production créative lourde — exécute un brief versionné `docs/forge/briefs/BRIEF-NNNN-*.md` (ADR-0004) |
| `godot-verifier` | forge (scripts épinglés, pas d'`Edit`/`Write`) | porte de qualité + build + capture + **coût GPU** ; rend un verdict compact, absorbe le bruit |
| `godot-reviewer` | read-only | relit un diff GDScript contre les règles dures (typage, zéro alloc, autoloads, palette) |
| `balance-prober` | read-only | joue la démo en temps réel, rend la **chronologie de l'arc** (durées, scores, anomalies) |
| `spec-auditor` | read-only | audite le code contre une **section** de la spec (fan-out), ADR compris |

**Maillon faible assumé** : `spec-auditor` n'a aucun besoin récurrent constaté à sa création
(12/07/2026). S'il ne sert pas d'ici quelques sessions, le **replier** plutôt que le laisser pourrir
— c'est la discipline qui empêche un roster de se remplir d'agents décoratifs.

## Avant de proposer un nouvel agent

1. La tâche est-elle **récurrente** ? (une fois ≠ un agent)
2. Produit-elle du **bruit** qu'on veut sortir du contexte ?
3. Rend-elle un **verdict** exploitable en une ligne ?
4. Si elle écrit : la mutation est-elle **par nature**, et le scope **verrouillable par script** ?

Trois « oui » sur quatre → candidat. Sinon → **skill**, ou rien.
