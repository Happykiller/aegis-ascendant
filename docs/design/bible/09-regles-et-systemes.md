---
titre: Règles et systèmes — les boucles de rétroaction, et l'économie qu'on n'a pas
type: reference
statut: actif
maj: 2026-08-27
---

# Règles et systèmes

Les pages précédentes décrivent des **contenus** : des vagues, des boss, des patterns. Celle-ci
décrit ce qui les relie — les **boucles de rétroaction** qui font qu'un succès en appelle un autre,
ou qu'il se paie.

> À lire avec [`06-score-et-rang.md`](06-score-et-rang.md), qui traite le cas particulier le plus
> connu (le rang). Ici, l'outil général.

## Ce que le métier dit

### Deux familles, et deux seulement

| | Boucle **positive** (renforçante) | Boucle **négative** (équilibrante) |
|---|---|---|
| Définition | « permet au joueur de **bâtir sur ses succès** » — ce qui arrive fait que ça arrive encore, plus fort à chaque tour | « plus vous poussez fort, **plus elle repousse** » |
| Effet ressenti | accomplissement, montée en puissance, emballement | tension maintenue, retour au milieu |
| Exemple canonique | les *killstreaks* : tuer donne des atouts qui font tuer | la carapace bleue de *Mario Kart*, qui vise **le premier** |
| Danger | l'emballement : le joueur en tête devient inatteignable | l'effort annulé : le joueur cesse de croire que jouer mieux change quelque chose |

### Le danger d'une positive seule est documenté

L'avertissement est explicite sur le cas des killstreaks : « une **seule** boucle de rétroaction
positive peut nuire à l'équilibre d'un jeu ». Le système a produit un emballement pour les joueurs
en tête, a résisté à plusieurs tentatives de rééquilibrage, puis a été retiré.

### Les deux ensemble = une difficulté qui se règle toute seule

C'est la combinaison qui est décrite comme « le Graal de la conception de jeux » : les succès sont
**récompensés** par la boucle positive, pendant que la capacité croissante du joueur est
**contenue** par la négative. Sans la positive, jouer mieux ne se ressent pas ; sans la négative,
la partie se décide dans les deux premières minutes.

### MDA : on conçoit dans un sens, on joue dans l'autre

Le cadre **MDA** (*Mechanics, Dynamics, Aesthetics*) sépare trois couches : les **règles** qu'on
écrit, les **dynamiques** qui en émergent pendant la partie, l'**expérience** que le joueur en
retire. Le concepteur va des mécaniques vers l'expérience ; le joueur fait le chemin **inverse** et
ne voit jamais les règles.

⚠️ Conséquence pratique pour ce projet : une boucle de rétroaction n'est **jamais** visible en
lisant le code d'un système isolé. Elle naît de deux systèmes qui se parlent — chez nous, du
`PickupManager` et du `PlayerFighterController`, qui ne se connaissent qu'à travers un `add_power()`.

## Chez nous — état au 2026-08-27

### Inventaire des boucles réellement présentes

| Boucle | Sens | Chemin dans le code |
|---|---|---|
| **Puissance** | **positive** | tuer → `roll_drop()` tous les **4** ennemis → un Power Core tous les **12** → `add_power()` → cadence de tir ×0,8 et flux supplémentaires (`_fire()`, niveaux 3/4/5) → tuer plus vite |
| **Bouclier** | **positive** | ne pas être touché **3 s** → régénération à **12 /s** → encaisser plus tard |
| **Mort** | **neutre** — et c'est un choix | `_destroy()` retire une vie, **pas un niveau de puissance** ; puis 1,2 s de pause et 2,0 s d'invulnérabilité |
| **Rang / difficulté dynamique** | ❌ **absente** | rien ne lit la performance du joueur |
| **Cycles du boss** | scriptée | l'armure revient **amoindrie** — 4 plaques, puis 3, puis 2 (`ADR-0021`, `ADR-0026`) |

### Le constat systémique

**Le jeu n'a que des boucles positives.** Les deux qui existent se renforcent l'une l'autre — plus
de puissance ⇒ moins de coups reçus ⇒ bouclier plein ⇒ plus d'agressivité possible — et **rien ne
pousse en sens inverse**. La mort elle-même, qui est la soupape du genre, ne retire aucune
puissance chez nous.

C'est très exactement la configuration dont le métier dit qu'elle « peut nuire à l'équilibre ».
⚠️ **Mais elle est ici voulue** : c'est le pilier A (« une grande puissance sans difficulté
punitive », spec §1.2) appliqué sans réserve, et le seul contrepoids assumé est la **timeline
scriptée** — la difficulté monte parce que la phase suivante est plus dure, pas parce que le joueur
va bien.

### L'économie : quatre ressources, et aucune ne se dépense

| Ressource | Se gagne | Se dépense | Arbitrage possible |
|---|---|---|---|
| Bouclier (100) | régénération, bonus (+35) | en encaissant | ❌ subi, jamais choisi |
| Vies (3) | — | en mourant | ❌ continues illimités |
| Puissance (1→5) | 1 bonus / 12 ennemis | **jamais** | ❌ |
| Score | ennemis, bonus, phases | **jamais** | ❌ |

**Aucune ressource du jeu ne se dépense volontairement.** Il n'y a donc pas d'économie, et pas de
décision d'économie : le joueur ne choisit jamais entre deux emplois d'une même chose.

Les trois mécanismes que la spec prévoyait pour cela — **arme secondaire** (§9.3), **Overdrive**
(§9.4), **focus/précision** (§7.1) — **n'existent dans aucun script** : `InputBootstrap` ne déclare
que `move_*`, `fire_primary` et `ui_options`. Ce ne sont pas des réglages manquants, ce sont des
systèmes non écrits.

## L'écart, et ce qu'on en fait

**Assumé, et documenté ici pour ne plus être redécouvert.** L'absence de boucle négative est la
conséquence directe du pilier A. Elle ne devient un problème que si l'on constate en jouant que la
seconde moitié de l'arc est trop facile pour un joueur qui a bien commencé — ce que le backlog P0
appelle déjà « vérifier que la difficulté est *facile mais nerveuse* ».

**La marche la plus courte, si ce constat tombe**, n'est ni le rang ni la perte de puissance : c'est
de **rendre une ressource dépensable**. Un seul mécanisme — l'Overdrive de la spec §9.4 — introduit
d'un coup le conflit d'objectifs qui manque à la page [`06`](06-score-et-rang.md), une décision
récurrente dans la micro-boucle, et une boucle négative naturelle (on le dépense quand on va mal).

⚠️ **Ne pas ajouter une boucle négative *cachée*.** Le projet a déjà appris ce que coûte un
calibrage qui devient faux en silence (`ADR-0024`, `ADR-0026`), et le genre insiste sur le point 4
du rang : le joueur doit pouvoir **agir** sur le système, même sans le comprendre. Une difficulté
qui monte sans que rien ne le dise se lit comme un bug, pas comme un adversaire.

> **À COMPLÉTER — décision de l'opérateur.** Overdrive, arme secondaire et focus sont dans la spec
> et absents du code. Trois états possibles, et il faut en choisir un explicitement : **à écrire**
> (ils reviennent au backlog), **hors périmètre de la démo** (un ADR le dit, comme `ADR-0010` l'a
> fait pour la forteresse), ou **remplacés** par autre chose. Aujourd'hui ils sont dans le pire des
> quatre états : *prévus, absents, et silencieux*.

## Sources

- [Game systems: Feedback loops and how they help craft player experiences](https://machinations.io/articles/game-systems-feedback-loops-and-how-they-help-craft-player-experiences) — Machinations : les deux familles, les exemples, l'avertissement sur l'emballement des killstreaks.
- [Feedback Loops – Game Design Toolkit](https://tkdev.dss.cloud/gamedesign/toolkit/feedback-loops/) — la formulation « renforçante / équilibrante ».
- [Mechanics, Dynamics, and Aesthetics](https://pressbooks.usnh.edu/creatinggames/chapter/mechanics-dynamics-and-aesthetics/) — le cadre MDA et la lecture inversée concepteur/joueur.
