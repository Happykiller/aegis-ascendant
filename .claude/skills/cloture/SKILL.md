---
name: cloture
description: Rituel de fin de session de travail. Capitalise les acquis dans docs/KB/, committe et pousse chaque dépôt du projet, arrête les conteneurs du projet, puis vérifie que tout est clean. Fonctionne en autonomie et ne s'arrête que sur anomalie. Déclencher avec /cloture.
trigger: /cloture
---

# /cloture — clore la session de travail

Une session close, c'est trois choses vraies en même temps : **rien d'appris qui soit perdu,
rien d'écrit qui reste non poussé, rien qui tourne encore dans le vide.** Tant que l'une des
trois est fausse, la session n'est pas close — et tu le dis au lieu de conclure.

## Périmètre de ce projet

> Relevé le 2026-08-23, corrigé le 2026-08-25, **re-vérifié sur la machine le 2026-08-27**.
>
> ⚠️ **CE BLOC A CHANGÉ DE VALEUR DEUX FOIS, DANS LES DEUX SENS.** Il a annoncé
> `/home/admin` + `github-perso`, puis `/home/happykiller` + `github-happykiller`, puis
> `/home/admin` de nouveau. Chaque bascule se réclamait d'une vérification.
>
> **Vérifié le 2026-08-27, sur cette machine, par les quatre commandes de l'étape 1** :
> `pwd` rend `/home/happykiller/aegis-ascendant` ; `git remote -v` rend
> `git@github-happykiller:Happykiller/aegis-ascendant.git` ; `~/.ssh/config` déclare **les deux**
> alias `github-happykiller` et `github-perso` ; et `/home/admin/aegis-ascendant` **n'existe
> pas**. Le tableau ci-dessous porte donc ces valeurs-là.
>
> **La leçon, elle, ne bouge pas** : un périmètre ne se corrige pas de mémoire, et une correction
> non vérifiée est plus dangereuse qu'une erreur laissée en place — elle porte l'autorité d'une
> relecture. Le va-et-vient s'explique probablement par **plusieurs comptes sur cette machine**
> (voir `.claude/resources/pratique-ecrivain-unique.md`) : ce qui est vrai sous un utilisateur ne
> l'est pas sous l'autre. **Ne pas rebasculer ce bloc sans avoir relancé les quatre commandes**,
> et si le résultat diffère, écrire lequel des comptes on est plutôt que d'effacer l'autre.

| Dépôt | Chemin | Branche de travail | Remarque |
| --- | --- | --- | --- |
| `aegis-ascendant` | `/home/happykiller/aegis-ascendant` | `main` | Dépôt **unique**. Remote `origin` = `git@github-happykiller:Happykiller/aegis-ascendant.git` (alias SSH `github-happykiller`, compte `Happykiller`). Dépôt **imbriqué dans le home** : ne jamais l'ajouter depuis un dépôt parent, et ne jamais traiter `/home/happykiller` comme un dépôt Git |

| Stack | Fichier compose | Services |
| --- | --- | --- |
| *(aucune)* | — | Ce projet n'a **ni Docker ni conteneur**. L'étape 5 est sans objet ici |

**Ce qui « tourne » sur ce projet, à la place des conteneurs** : le jeu exporté, lancé côté
**Windows** depuis `C:\tmp\aegis-ascendant\`. Une fenêtre de jeu laissée ouverte tient le `.exe` et
fera échouer le prochain `deploy-win.sh`. Vérifier qu'aucune instance ne traîne — et ne **jamais**
tuer un processus Windows qui n'est pas ce jeu : `C:\tmp` n'est pas cloisonné, un autre agent peut
être en train de jouer (`.claude/resources/pratique-ecrivain-unique.md`).

Si cette section est vide ou fausse, **recense d'abord** (étape 1) et propose de la corriger dans
le même geste — un périmètre faux fait oublier un dépôt, et un dépôt oublié est une session non
close qui se croit close.

## Commandes disponibles

| Commande | Action |
| --- | --- |
| `/cloture` | Le rituel complet |
| `/cloture check` | Dry-run : ce qui *serait* fait, dépôt par dépôt, sans rien écrire ni arrêter |
| `/cloture sans-capi` | Saute la capitalisation, déjà faite dans la session |
| `/cloture sans-push` | Committe et arrête, mais ne pousse pas (réseau coupé, travail sensible) |

## Ordre d'exécution — non négociable

```
1. recenser  →  2. capitaliser  →  3. committer  →  4. pousser  →  5. arrêter  →  6. vérifier
```

Les conteneurs tombent **en dernier**, jamais en premier : un hook de pre-commit, une suite de
tests ou une migration lancée par la capitalisation peut encore avoir besoin de la base. Un
conteneur arrêté trop tôt transforme une clôture en séance de debug.

## Autonomie et arrêts

Tu enchaînes les six étapes **sans demander de validation**. Tu t'arrêtes net, tu exposes le
problème et tu attends, dans ces cas et ceux-là seulement :

- un **secret** (`.env`, clé privée, token, dump de base, credentials) est sur le point d'être
  committé ;
- un fichier modifié **n'a aucun rapport** avec la session : tu ne sais pas s'il doit partir ;
- un acquis de capitalisation **contredit** une page KB existante — jamais d'écrasement silencieux ;
- un **push rejeté** (non-fast-forward), une branche protégée, ou une règle projet qui impose une
  MR plutôt qu'un push direct ;
- un **conteneur tourne** sans être rattaché à un compose de ce projet : tu ne l'arrêtes pas ;
- un dépôt **reste sale** après commit (sous-module bougé, artefact non ignoré, conflit) ;
- un dépôt est en état intermédiaire : rebase, merge ou cherry-pick en cours.

## Interdits absolus

Aucun de ces gestes ne se justifie par « pour que ce soit clean » :

- `git push --force` / `--force-with-lease` sans demande explicite ;
- `git add -A` / `git add .` sans avoir lu la liste de ce que ça ajoute ;
- `git reset --hard`, `git checkout .`, `git clean -fd`, `git stash` silencieux — nettoyer, ce
  n'est pas détruire le travail de quelqu'un ;
- `docker compose down -v` (les volumes emportent les données), `docker system prune`,
  `docker stop $(docker ps -q)` ;
- committer sur une branche protégée que les règles du projet réservent aux MR.

## Étape 1 — recenser

```bash
find . -name .git -maxdepth 3 -prune | sed 's|/\.git$||' | sort
find . -maxdepth 3 \( -name 'docker-compose*.y*ml' -o -name 'compose*.y*ml' \) -not -path '*/node_modules/*'
docker compose ls 2>/dev/null
docker ps --format '{{.Names}}\t{{.Label "com.docker.compose.project"}}\t{{.Image}}'
```

Confronte le résultat à la section « Périmètre » et à `docs/KB/DAT/arborescence.md`. Un dépôt
présent sur le disque mais absent du tableau doit être traité **et** signalé.

Ordre de traitement : **les dépôts imbriqués et les dépendances avant le dépôt parent**. Un parent
poussé avant son sous-module pointe vers un commit que personne d'autre ne peut résoudre.

## Étape 2 — capitaliser

Exécute `/capitalize`. En clôture il travaille en autonomie : ce qui passe ses trois filtres
(durable, non déductible, réutilisable) est écrit ; ce qui contredit une page existante est un
**arrêt**, pas un arbitrage que tu rends seul.

Si `/capitalize` n'existe pas dans ce projet, ne l'improvise pas : signale-le, propose de lancer
`factory-ghost`, et poursuis la clôture sans le volet capitalisation.

## Étape 2 bis — ranger ce qui est clos

```bash
./scripts/audit-docs.sh          # rapport
./scripts/audit-docs.sh --fix    # archive les briefs livrés et les plans clos
```

Un chantier fini laisse derrière lui des documents qui pilotent encore. Cet audit **dérive**
l'état du dépôt — un brief est livré s'il a une sortie ou une ligne de provenance — et déplace
ce qui est clos dans `archive/`.

⚠️ **Pourquoi dériver au lieu de déclarer.** Le champ `Statut` des briefs existe depuis le
premier jour et a été tenu **5 fois sur 37** : au 2026-08-25, **32 briefs livrés** portaient
encore « assigné », `docs/` gardait deux documents morts depuis cinq et six semaines, et le
backlog contenait **deux copies divergentes** de ses sections P0-P4 — celle qu'on lisait en
premier était la périmée. Un état tenu à la main rouille toujours ; celui-ci se lit dans le
dépôt et personne n'a rien à maintenir.

**Ce que l'audit ne fait PAS** : décider. Il liste les briefs réellement ouverts et les plans
vivants. Fermer un chantier reste une décision de l'opérateur — et **avant d'archiver un plan,
verser ce qu'il laisse ouvert dans `docs/BACKLOG.md`** : un plan qu'on archive ne doit rien
emporter avec lui.

## Étape 3 — committer, dépôt par dépôt

Pour chaque dépôt du périmètre :

1. `git status --porcelain` et `git diff` — **lis** avant de stager. Ce que tu n'as pas lu, tu ne
   le committes pas.
2. Examine les fichiers non suivis **un par un**. Un artefact de build, un log, un dossier de
   dépendances ne se committe pas : il rejoint `.gitignore` (et c'est un commit à part).
3. **Découpe par sujet**, pas par session. Trois sujets touchés dans la journée font trois
   commits, pas un « wip fin de journée » que personne ne saura relire dans six mois.
4. Message de commit : reprends la convention réelle du dépôt (`git log --oneline -20`) et les
   règles de `docs/KB/REGLES/process.md`. Décris **l'effet obtenu**, pas la liste des fichiers.
5. Ne fabrique pas un commit vide pour « marquer la fin » : un dépôt sans modification reste sans
   commit, et c'est un résultat normal.

⚠️ Sur ce projet, la **Definition of Done** conditionne le commit : `./scripts/check.sh` doit être
vert, et le comportement vérifié (sur Windows s'il est visuel). Ne committe pas une porte rouge
« pour ne pas perdre le travail » — dis-le et arrête-toi.

## Étape 4 — pousser

Sur la **branche courante** de chaque dépôt, dans l'ordre de l'étape 1. Jamais de force.

Si le push est rejeté : ne rebase pas d'office, ne force pas. Rapporte l'écart
(`git rev-list --left-right --count @{upstream}...HEAD`) et laisse la décision.

Si les règles du projet imposent une MR sur cette branche, pousse la branche de travail et
**donne le lien de création de MR** au lieu de pousser sur la cible.

## Étape 5 — arrêter les conteneurs

Uniquement ce qui appartient au projet, stack par stack, depuis le dossier du compose :

```bash
docker compose -f <fichier> down       # sans -v : les volumes survivent
```

Un conteneur du projet lancé hors compose s'arrête nommément (`docker stop <nom>`). Tout ce qui
n'est pas identifié comme appartenant au projet **reste en vie** et part dans le rapport.

Sur ce projet, sans conteneur, cette étape se réduit à une vérification : **aucune fenêtre du jeu
ne doit rester ouverte** côté Windows (elle tient le `.exe` et fera échouer le prochain déploiement).

## Étape 6 — vérifier

La clôture n'est pas ce que tu as fait, c'est ce qui est vrai à la fin. Prouve-le :

```bash
# Chaque dépôt : working tree propre et rien en attente de push
for r in <dépôts du périmètre>; do
  printf '%-24s ' "$r"
  [ -z "$(git -C "$r" status --porcelain)" ] && printf 'clean  ' || printf 'SALE   '
  git -C "$r" rev-list --left-right --count @{upstream}...HEAD 2>/dev/null \
    | awk '{print ($1==0 && $2==0) ? "sync" : "retard/avance: "$1"/"$2}'
done

# Plus aucun conteneur du projet
docker ps --format '{{.Names}}\t{{.Label "com.docker.compose.project"}}'
```

## Étape 7 — rendre compte

Court, factuel, et honnête sur ce qui n'a pas pu être refermé :

```
## Clôture — <projet>

Capitalisation : 2 pages KB enrichies, 1 créée, 1 ligne HISTORY, 0 outil.

| Dépôt        | Commits | Push       | État final |
| ---          | ---     | ---        | ---        |
| gold_server  | 2       | ok develop | clean      |
| gold_front   | 1       | ok develop | clean      |
| gold         | 0       | —          | clean      |

Conteneurs : stack `gold` arrêtée (4 services). Aucun conteneur du projet encore en vie.

Non refermé :
- `gold_extension` : push rejeté, 3 commits d'avance côté remote — à rebaser à la main.
```

S'il n'y a rien dans « Non refermé », écris-le explicitement. **La session est close** est une
affirmation vérifiée, pas une formule de politesse.
