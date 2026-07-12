---
name: capitalize
description: Verse dans le ghost d'Aegis Ascendant ce que la session vient d'apprendre — pièges d'outillage, méthodes de vérification, préférences de l'opérateur. Range chaque leçon dans le bon réceptacle (.claude/resources / docs / mémoire) et l'indexe. Trigger /capitalize.
trigger: /capitalize
---

# /capitalize — verser les leçons de la session dans le ghost

Le **ghost**, c'est tout ce qui gouverne le fonctionnement de Claude sur ce projet : `CLAUDE.md`,
`.claude/` (agents, resources, settings) et la mémoire auto-rappelée.

Ce skill existe parce que la capitalisation a été faite **six fois à la main dans une seule
session**, et que la moitié des leçons y ont été payées deux fois : le séparateur `++` oublié, le
FPS qui ne mesure rien, le PNG de capture périmé, le `timeout` absent qui a bloqué l'opérateur.

## Le seul critère qui vaut

**Ne capitalise QUE ce qui a coûté.** Une leçon mérite d'être écrite si, sans elle, un agent futur
va perdre une itération — ou pire, tirer une conclusion fausse.

Ne capitalise **pas** :

- ce qui se dérive du code (« BulletManager utilise une grille spatiale » — ça se lit) ;
- ce qui n'a servi qu'à cette conversation ;
- une règle que tu n'as **pas vérifiée** (une règle fausse dans le ghost est **pire que pas de
  règle** : elle se propage sans qu'on la questionne — voir `subagent-hotreload-macross`).

Si tu n'as rien appris qui coûte, **dis-le et n'écris rien.** Un ghost qui grossit sans raison
brûle du contexte à chaque session.

## Où va quoi — la question à trancher pour chaque leçon

| Nature | Destination |
|---|---|
| Comment **travailler** avec Claude ici : outillage, boucle de vérification, méthode, piège de plomberie | **`.claude/resources/`** + sa ligne dans `INDEX.md` |
| Une **décision actée** sur le produit (on a écarté X au profit de Y, et voici pourquoi) | **`docs/decisions/ADR-NNNN-*.md`** |
| Un **reste à faire** ou un chantier ouvert | **`docs/BACKLOG.md`** |
| **Préférence de l'opérateur**, relation, fait d'hôte — non dérivable du repo | **mémoire auto** (`~/.claude/projects/-home-admin-sandbox-macross/memory/`) + sa ligne dans `MEMORY.md` |
| Une contrainte **courte et permanente**, à charger à chaque session | `CLAUDE.md` — **un pointeur, jamais le détail** |

⚠️ **`CLAUDE.md` se charge en entier à chaque session.** Y verser du détail brûle du contexte même
pour une tâche triviale. Le détail va dans `.claude/resources/`, chargé à la demande.

⚠️ Une **procédure déterministe** ne se capitalise pas en prose : elle s'**encode dans un script**.
C'est la leçon du 12/07/2026 — `play-arc.sh` et le correctif de `deploy-win.sh` sont nés de quatre
procédures réécrites à la main, et ratées trois fois. **Si tu peux l'écrire en bash, ne l'écris pas
en français.** Et si un sous-agent existe pour cette tâche, **branche-le sur le script** au lieu de
le laisser réinventer la procédure.

## Protocole

1. **Relire la session** et lister ce qui a coûté : un piège d'outil, une fausse piste, une
   correction de l'opérateur, une méthode qui a marché contre une qui a échoué.

2. **Pour chaque leçon, trancher son réceptacle** avec le tableau ci-dessus. En cas de doute entre
   `.claude/resources/` et `docs/` : *est-ce que ça parle du jeu, ou de la façon de travailler sur
   le jeu ?*

3. **Écrire la leçon avec son COÛT.** Une règle sans son histoire ne convainc personne et se fait
   contourner. Compare :

   > ❌ « Toujours utiliser `timeout`. »
   > ✅ « Le jeu en `--demo` ne s'arrête jamais : il rejoue l'arc en boucle. Sans `timeout`, la
   >    session est bloquée et l'opérateur doit interrompre à la main — vécu le 12/07/2026, y
   >    compris via un sous-agent, qui a hérité du blocage. »

   Les **chiffres** valent mieux que les adjectifs : « le FPS ne veut rien dire ici » convainc moins
   que « 2 FPS sans le fond, 17 FPS avec — un fond n'accélère pas un jeu ».

4. **Indexer**, sinon la leçon est morte : une ligne dans `.claude/resources/INDEX.md`, ou une ligne
   dans `MEMORY.md`. Une ressource non indexée ne sera jamais relue.

5. **Corriger ce qui est faux.** Si la session a démenti une règle existante du ghost, la
   **réécrire**, pas en ajouter une seconde à côté. Deux règles contradictoires valent moins que zéro.

6. **Commiter** : `docs(ghost): <la leçon, pas l'action>`. Le message porte le coût, pas le geste.

## Ne pas confondre avec la mise à jour du backlog

Ce skill capitalise **le savoir**, pas l'avancement. Si tu as terminé une tâche, mets à jour
`docs/BACKLOG.md` — mais ce n'est pas de la capitalisation, c'est de la comptabilité.
