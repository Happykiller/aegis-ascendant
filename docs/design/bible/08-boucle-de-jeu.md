---
titre: Boucle de jeu — les trois échelles, et la cadence de récompense
type: reference
statut: actif
maj: 2026-08-27
---

# Boucle de jeu

Le genre décrit volontiers *ce que le joueur affronte*. Cette page décrit *ce qu'il fait, en
boucle* — l'unité de temps la plus courte du jeu, et les échelles qui l'emboîtent.

## Ce que le métier dit

### Trois échelles emboîtées

| Boucle | Durée | Contenu type |
|---|---|---|
| **micro** — instant à instant | **1 à 5 s** | viser → tirer → se replacer |
| **méso** — minute à minute | **2 à 10 min** | entrer dans une zone → la nettoyer → en sortir plus fort |
| **macro** — session à session | heures, jours | finir → débloquer → recommencer autrement |

La règle qui les relie : « les micro-boucles doivent se **rattacher naturellement** aux
macro-boucles ». Une micro-boucle satisfaisante qui ne nourrit aucune boucle plus longue produit un
jeu qu'on repose au bout de dix minutes ; une macro-boucle riche assise sur une micro-boucle terne
produit un jeu qu'on ne commence jamais.

### La première récompense arrive avant la première minute

Repère chiffré : la micro-boucle se résout en **1 à 5 s**, et la **première récompense doit tomber
dans les 30 à 60 premières secondes**.

### On doit savoir ce qu'est le jeu en quelques minutes

> Une boucle de jeu « ne devrait **jamais se mesurer en heures** — on doit savoir à quoi ressemble
> votre jeu en quelques **minutes** de jeu. »

Une boucle mal définie « masque l'objectif immédiat sous un excès de macro », et compte sur le
joueur pour « trouver le fun » après un investissement de temps qu'il n'a aucune raison de consentir.

### Les quatre choses que le joueur doit pouvoir dire

À tout instant, il doit savoir :

1. **quel est l'objectif immédiat** ;
2. **quelles tâches** l'y mènent ;
3. **combien de temps** ça va prendre ;
4. **ce qui reste acquis** ensuite.

⚠️ Le point 3 est le plus négligé, et c'est le plus structurant : « le joueur doit savoir s'il peut
finir dans **une seule session** ».

## Chez nous — état au 2026-08-27

### La micro-boucle : ~0,12 s, et elle n'a pas de temps mort

Le tir est **automatique et continu** — `fire_interval = 0,12 s` (`resources/data/player_stats.gd`),
resserré à 0,096 s dès le niveau de puissance 2. Il n'y a donc pas de boucle « viser → tirer » :
l'acte du joueur est **se placer**. La micro-boucle réelle tient en trois gestes simultanés :

```
lire la menace  →  se replacer  →  ramasser ce qui tombe
```

Elle est **plus courte que le repère du métier** (1–5 s) : à 14 unités/s de vitesse de pointe
atteinte en 0,18 s, une décision de placement se prend et se paie en moins d'une seconde. C'est
cohérent avec le pilier A — la difficulté est de position, pas de punition.

### La cadence de récompense est **déterministe**, pas aléatoire

`PickupManager.roll_drop()` ne tire rien au sort malgré son nom :

- un bonus tombe **tous les 4 ennemis détruits** (`_DROP_EVERY := 4`) ;
- un bonus sur trois est un **Power Core** (`_POWER_EVERY := 3`), soit **un niveau de puissance tous
  les 12 ennemis** ;
- les deux autres suivent un cycle fixe `bouclier → score → bouclier`.

Conséquence à connaître avant de toucher au bestiaire : **la cadence de montée en puissance est
indexée sur le nombre d'ennemis d'une vague, pas sur le temps**. Ajouter du popcorn accélère le
power-up ; ajouter des ennemis coriaces le ralentit, à durée de phase identique.

### La boucle méso : la phase

Les six phases (`FIGHTER_WAVES → MINI_BOSS → ASTEROID_FIELD → FINAL_BOSS → DOCKING → VICTORY`,
`scripts/gameplay/graybox_root.gd`) sont les boucles méso. Le champ d'astéroïdes dure 45 à 60 s ; le
boss final tourne en **trois cycles** armure → noyau (`ADR-0021`, `ADR-0026`) — c'est la seule boucle
du jeu qui se répète explicitement, et le seul endroit où le joueur peut **prévoir** ce qui vient.

### La boucle macro : une partie de 12 à 15 minutes, et un rang

La cible spec §5.1 est **12 à 15 min**. En sortie, `MissionReport` affiche un score et un rang par
seuils (`scripts/ui/mission_report.gd:172`) : **12 000 / 25 000 / 40 000**. C'est, aujourd'hui, la
**seule** raison mécanique de relancer une partie. Le Codex/bestiaire est consultable au menu, il ne
se débloque pas.

### Les quatre questions, testées sur notre jeu

| Question | Réponse dans le jeu |
|---|---|
| objectif immédiat | ✅ lisible — ce qui est à l'écran |
| quelles tâches | ✅ tirer, esquiver, ramasser |
| combien de temps | ⚠️ **le joueur ne le sait jamais** — aucun indicateur de progression de niveau ; seule la jauge de boss dit où on en est, et seulement pendant un boss (`ADR-0023`) |
| ce qui reste acquis | ⚠️ **rien** entre deux parties, hors score |

## L'écart, et ce qu'on en fait

**Tenu.** La micro-boucle est immédiate et sans temps mort, la première récompense arrive
largement avant la 60ᵉ seconde (4 ennemis détruits suffisent), et le jeu se comprend en quelques
secondes. C'est la partie que le métier tient pour la plus difficile, et elle est acquise.

**Assumé.** Pas de progression entre parties : c'est un prototype de démonstration (spec §1.3), pas
un jeu de rétention. La macro-boucle est le **rang**, et cela suffit au périmètre.

**Piste ouverte, non décidée.** La troisième question — *combien de temps ?* — est la seule
faiblesse structurelle. Le genre y répond par un **numéro de segment** ou une **barre de
progression de niveau** ; nous n'avons ni l'un ni l'autre en dehors des boss. ⚠️ Un tel indicateur
touche le HUD, dont la règle est qu'il ne doit rien ajouter qui se consulte en pilotant
(`scripts/ui/fighter_hud.gd:198`) — donc il ne serait acceptable qu'entre deux phases, sur l'écran
de transition existant (`scripts/vfx/phase_transition.gd`), pas en permanence.

## Sources

- [The Importance of a Well Defined Core Gameplay Loop](https://www.gamedeveloper.com/design/the-importance-of-a-well-defined-core-gameplay-loop) — Game Developer : la boucle qui se mesure en minutes, les quatre critères de progression lisible.
- [Designing The Core Gameplay Loop: A Beginner's Guide](https://gamedesignskills.com/game-design/core-loops-in-gameplay/) — Game Design Skills : micro/méso/macro et les repères chiffrés (1–5 s, 30–60 s, 2–10 min). ⚠️ Le site rend un **403 aux robots** : consulté via résumé de recherche, à relire à la main si le sujet est repris.
- [Game Design using Micro Macro Meta Grouping](https://levimoore.dev/game-design-using-micro-macro-meta-grouping/) — le découpage micro/macro/méta.
