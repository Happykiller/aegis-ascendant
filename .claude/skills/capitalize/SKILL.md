---
name: capitalize
description: Amélioration continue de fin de session. Analyse ce qui vient de se passer, identifie ce qui doit rejoindre la base de connaissance docs/KB/ ou le ghost .claude/resources/ (faire mieux) et ce qui est candidat à devenir un skill, un sous-agent ou un hook (faire plus efficacement). Ne capitalise que ce qui a coûté, et propose toujours avant d'écrire. Déclencher avec /capitalize.
trigger: /capitalize
---

# /capitalize — capitaliser sur la session

Ta mission : transformer ce qui vient de se passer en **acquis durable**. Une session qui s'achève
sans capitalisation, c'est un apprentissage perdu qu'on repaiera plus tard.

Ce skill existe parce que la capitalisation a été faite **six fois à la main dans une seule
session**, et que la moitié des leçons y ont été payées deux fois : le séparateur `++` oublié, le
FPS qui ne mesure rien, le PNG de capture périmé, le `timeout` absent qui a bloqué l'opérateur.

Deux sorties possibles, et deux seulement :

- **Faire mieux** → une connaissance rejoint la KB (`docs/KB/`) ou le ghost (`.claude/resources/`).
- **Faire plus efficacement** → un geste répété devient un outil dans `.claude/`.

## Commandes disponibles

| Commande | Action |
| --- | --- |
| `/capitalize` | Analyse la session et propose les deux volets |
| `/capitalize kb` | Volet connaissance seulement |
| `/capitalize moteur` | Volet industrialisation seulement |
| `/capitalize check` | Audit : liens morts, index désynchronisés, pages trop grosses ou obsolètes — dans `docs/KB/` **et** dans `.claude/resources/INDEX.md` |

## Le seul critère qui vaut

**Ne capitalise QUE ce qui a coûté.** Une leçon mérite d'être écrite si, sans elle, un agent futur
va perdre une itération — ou pire, tirer une conclusion fausse.

Si tu n'as rien appris qui coûte, **dis-le et n'écris rien.** Un ghost qui grossit sans raison brûle
du contexte à chaque session.

## Étape 1 — relire la session

Reprends l'échange depuis le début et liste, sans filtrer encore :

- ce qui a été **découvert** sur le projet (comportement, contrainte, dépendance cachée) ;
- ce qui a été **décidé**, et surtout **pourquoi** — l'alternative écartée compte autant ;
- ce que l'opérateur a **corrigé** chez toi : c'est le signal le plus fort de tous, une correction
  non capitalisée se reproduira ;
- les gestes que tu as **répétés** ou qui ont été laborieux.

## Étape 2 — filtrer

Ne retiens que ce qui passe les trois filtres :

1. **Durable** — vrai encore dans trois mois, pas seulement aujourd'hui.
2. **Non déductible** — pas déjà lisible dans le code, la spec, un ADR ou l'historique git.
   Documenter ce que le dépôt dit déjà, c'est fabriquer une source qui divergera. (« BulletManager
   utilise une grille spatiale » — ça se lit.)
3. **Réutilisable** — servira à une prochaine session, pas seulement à celle-ci.

Et un quatrième, propre à ce projet : **vérifié**. Une règle fausse dans le ghost est **pire que pas
de règle** — elle se propage sans qu'on la questionne.

Ce qui ne passe pas est **jeté**, explicitement.

## Étape 3 — volet connaissance (faire mieux)

La question qui tranche entre les deux réceptacles : *est-ce que ça parle du jeu, ou de la façon de
travailler sur le jeu ?*

| Nature de l'acquis | Destination |
| --- | --- |
| Comment **travailler** avec Claude ici : outillage, boucle de vérification, méthode, piège de plomberie | **`.claude/resources/`** + sa ligne dans `INDEX.md` |
| Fait technique, stack, environnement, arborescence | `docs/KB/DAT/` |
| Règle de jeu, domaine fonctionnel, invariant de gameplay | `docs/KB/DAF/` |
| Process, workflow, norme de code ou de test | `docs/KB/REGLES/process.md`, `workflows.md`, `normes.md` |
| Correction ou préférence de l'opérateur envers toi | `docs/KB/REGLES/consignes.md` |
| Invariant non négociable | `docs/KB/REGLES/lois.md` |
| Une **décision actée** sur le produit (on a écarté X au profit de Y, et voici pourquoi) | **`docs/decisions/ADR-NNNN-*.md`** |
| Un **reste à faire** ou un chantier ouvert | **`docs/BACKLOG.md`** |
| Préférence, relation, fait d'hôte non dérivable du dépôt | **mémoire auto** (`~/.claude/projects/-home-admin-aegis-ascendant/memory/`) + sa ligne dans `MEMORY.md` |
| Une contrainte **courte et permanente**, à charger à chaque session | `CLAUDE.md` — **un pointeur, jamais le détail** |

⚠️ **`CLAUDE.md` se charge en entier à chaque session.** Y verser du détail brûle du contexte même
pour une tâche triviale. Le détail va dans `.claude/resources/` ou dans la KB, chargés à la demande.

⚠️ **La KB n'est pas la source de vérité du produit** : spec et ADR le restent, et les ADR priment
sur la spec. Une page de KB qui recopie l'une des deux sera fausse au premier commit — elle
**référence**.

Règles d'écriture :

- **Enrichir avant de créer** : cherche d'abord la page existante qui couvre le sujet.
- **Index-first** : toute nouvelle page est ajoutée au `README.md` de son dossier (ou à
  `INDEX.md`) dans le même geste. Une page non indexée est une page perdue.
- **Découper** : au-delà de ~200 lignes ou ~15 Ko, une page devient un dossier + son index.
- **Écrire le POURQUOI et le COÛT**, jamais le seul quoi. Une règle sans son histoire ne convainc
  personne et se fait contourner :

  > ❌ « Toujours utiliser `timeout`. »
  > ✅ « Le jeu en `--demo` ne s'arrête jamais : il rejoue l'arc en boucle. Sans `timeout`, la
  >    session est bloquée et l'opérateur doit interrompre à la main — vécu le 12/07/2026, y
  >    compris via un sous-agent, qui a hérité du blocage. »

  Les **chiffres** valent mieux que les adjectifs : « le FPS ne veut rien dire ici » convainc moins
  que « 2 FPS sans le fond, 17 FPS avec — un fond n'accélère pas un jeu ».

- **Corriger ce qui est faux.** Si la session a démenti une règle existante, la **réécrire**, pas en
  ajouter une seconde à côté. Deux règles contradictoires valent moins que zéro. Si la contradiction
  porte sur une page que tu n'as pas écrite, **arrête-toi et propose** — pas d'écrasement silencieux.
- Mettre à jour le champ `maj:` des pages KB touchées.
- Ajouter une ligne à `docs/KB/HISTORY.md`.

## Étape 4 — volet moteur (faire plus efficacement)

| Forme | Quand c'est le bon choix | Où |
| --- | --- | --- |
| **Hook** | Ça doit se déclencher tout seul, de façon déterministe, sans que personne y pense | `.claude/hooks/` |
| **Skill** | Une procédure qu'on redemande, qui demande du jugement, invoquée par `/nom` | `.claude/skills/<nom>/SKILL.md` |
| **Sous-agent** | Un travail volumineux ou une expertise à part, qui polluerait le contexte principal | `.claude/agents/<nom>.md` |
| **Script** | Une procédure **déterministe** — pas de jugement, que des étapes | `scripts/` ou `tools/` |
| **Règle** | Ça ne s'automatise pas : ça se rappelle | `docs/KB/REGLES/` ou `.claude/resources/` |

⚠️ **Une procédure déterministe ne se capitalise pas en prose : elle s'encode dans un script.**
C'est la leçon du 12/07/2026 — `play-arc.sh` et le correctif de `deploy-win.sh` sont nés de quatre
procédures réécrites à la main, et ratées trois fois. **Si tu peux l'écrire en bash, ne l'écris pas
en français.** Et si un sous-agent existe pour cette tâche, **branche-le sur le script** au lieu de
le laisser réinventer la procédure.

Garde-fous :

- **Le seuil, c'est trois.** Un geste fait une fois ne justifie pas un outil. Deux fois, on note.
  Trois fois, on outille.
- **Vérifie que ça n'existe pas déjà**, dans `.claude/` du projet comme dans `~/.claude/`. Le
  critère sous-agent/skill est tranché dans `.claude/resources/process-etendre-le-ghost.md`.
- Un outil non maintenu est pire que pas d'outil : si tu ne sais pas dire quand il se déclenchera la
  prochaine fois, c'est une règle, pas un outil.
- Tout outil créé est ajouté à `docs/KB/MOTEUR.md`, avec sa colonne « quand l'utiliser ».

## Étape 5 — proposer, puis écrire

**N'écris rien avant validation.** Présente d'abord :

```
## À intégrer à la connaissance
- [.claude/resources/pratique-verifier-par-test.md] Un test qui construit un Node le fuit :
  pas d'arbre en mode --script. Coût : 789 objets fuités, diagnostic hérité faux.
- [KB/REGLES/consignes.md] /jouer nu démarre normalement — drapeaux seulement sur demande.

## Candidats à l'industrialisation
- [script] Sonder les fuites fichier par fichier : refait à la main, déterministe.

## Écarté
- Le contournement du bug d'import : temporaire, disparaîtra à la prochaine version de Godot.
```

L'opérateur valide, retire ou amende. **Ensuite** seulement tu écris, puis tu rends compte :
fichiers créés, fichiers enrichis, index mis à jour, ligne ajoutée à `HISTORY.md`.

Commit : `docs(ghost): <la leçon, pas l'action>`. Le message porte le coût, pas le geste.

## Ne pas confondre avec la mise à jour du backlog

Ce skill capitalise **le savoir**, pas l'avancement. Si tu as terminé une tâche, mets à jour
`docs/BACKLOG.md` — mais ce n'est pas de la capitalisation, c'est de la comptabilité.
