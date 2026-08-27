---
titre: Reactor Chamber — la phase du noyau devient une machine, pas une cible
date: 2026-08-27
auteur: session Claude, sur spécification et planche de l'opérateur
perimetre: phase DIVE du Pale Leviathan (CoreInterior), assets de forge, budget GPU
etat: instruit — RIEN d'engagé. Quatre points bloquants avant la première ligne de code
supersede: rien. Amenderait `ADR-0025` (l'arène) et `ADR-0026` (le plafond par plongée)
---

# Reactor Chamber

L'opérateur a fourni une planche et une spécification complète. Le diagnostic d'ouverture est
exactement celui que la session avait mesuré le matin même :

> « Le joueur entre dans le noyau puis se retrouve face à une cible quasiment fixe. »

Et la règle qu'il en tire :

> **Le décor crée le gameplay.** On évite donc de remplir simplement l'écran avec davantage
> d'ennemis.

⚠️ **La planche n'a pas pu être archivée** : elle n'était plus sur le disque au moment de
l'écriture. À redéposer pour entrer dans `assets/reference/concepts/` avec sa ligne de provenance
(spec §24.7) — c'est une planche **originale**, pas une référence tierce.

---

## 1. Ce que le projet a DÉJÀ, et qui sert directement

On ne part pas de zéro, et c'est la bonne nouvelle du dossier.

| Besoin de la spec | Ce qui existe | État |
|---|---|---|
| L'arène intérieure | `CoreInterior` — zone **dédiée** montée à l'origine du monde, à l'échelle du plan, extérieur masqué (`ADR-0025`) | ✅ et le décor est **livré** (`core_interior.glb`, BRIEF-0082) |
| Lasers balayants | `Beam` — faisceau tendu entre deux points du plan, **avec sa ligne de télégraphe** | ✅ déjà employé par les tourelles du Leviathan |
| Nodes orbitaux destructibles | l'idiome `LeviathanPlate` / `HarvesterLimb` : sous-cibles avec PV, halo de désignation, **rangée de pastilles au HUD** | ✅ et la rangée sait désormais montrer une **repousse** |
| Verrou « réacteur invulnérable » | `BulletTarget.enabled` — déjà ce qui rend le flux atteignable ou non | ✅ |
| Télégraphe des rails | `EnemyReaction` : `DORMANT → ALERT → ARMING → WINDUP → ACTIVE → SPENT`, avec la loi « **ce qui s'allume part** » | ✅ c'est littéralement la séquence `0,0 s clignote → 0,7 s bouge → 1,2 s danger` |
| Mouvement non linéaire | `OrganicDrift` (`ADR-0029`), périodes non harmoniques | ✅ livré le jour même |
| Repère de cible qui suit | le marqueur battant du `CoreInterior` | ✅ livré le jour même |
| Micro-zoom / secousse | `CameraDirector` — pose de repos déplaçable **plus** shake additif, et le shake est **réglable** | ✅ |

**Ce qui manque vraiment** : les **anneaux rotatifs à ouvertures**, les **rails mobiles**, et le
décor animé multi-couches.

---

## 2. ⚠️ Quatre points bloquants — à trancher AVANT la première ligne

### B1 — Le budget GPU, et c'est le plus dur

La machine qui **contraint** est la **Quadro T1000**, pas la RTX 4080 : à build identique le temps
GPU par image est **×14** entre les deux. Mesures de la journée **sur T1000** :

| Scène | ms/image |
|---|---:|
| Arène du noyau, telle quelle | **7,1 à 12,6** |
| Combat en vagues | 12,0 |
| Fond noir (`--no-backdrop`) | 3,9 à 5,2 |

À 60 Hz le budget est de **16,6 ms**. L'arène en consomme déjà les deux tiers **avant** d'ajouter
trois anneaux mécaniques, des rails, deux lasers, des étincelles, des arcs, de la vapeur et **sept
couches de parallaxe**.

⚠️ **Ce n'est pas un avertissement de principe** : `ADR-0027` a déjà dû faire *remplacer* le fond
spatial par le survol de lune plutôt que de l'y ajouter, pour tenir le budget. Le même arbitrage se
posera ici, en plus dur.

**Porte de mesure obligatoire** : chaque lot se mesure sur T1000 **avant** le suivant. Un lot qui
coûte plus de ~2 ms s'arrête et se discute.

### B2 — `ADR-0026` : le plafond par plongée contre la fenêtre de vulnérabilité

Aujourd'hui : les dégâts sont **plafonnés à un tiers par plongée**, ce qui rend les trois cycles
vrais **par construction et non par calibrage**. C'est une décision prise après trois playtests où
le compte de cycles variait de 3 à 6.

La spec propose autre chose : un réacteur avec **sa propre santé** (100 → 70 → 35 → 0) et une
**boucle de 8-12 s** dont seule la *fenêtre* est vulnérable.

Deux lectures, et il faut choisir :

| | (a) La fenêtre **dans** la plongée | (b) Le noyau devient une phase à part entière |
|---|---|---|
| Structure | chaque plongée = **2 ou 3 boucles** de fenêtre. Le plafond d'`ADR-0026` reste | le noyau a sa santé, ses trois paliers, et remplace les cycles |
| Durée ajoutée à l'arc | plongée de 5 s → ~20-25 s, soit **+45 à 60 s** sur le boss | **+2 à 3 minutes** |
| `ADR-0026` | intact | **abrogé**, et son problème revient |
| Coût | moyen | élevé |

**Recommandation : (a).** Elle donne le puzzle de positionnement — qui est *l'idée* de la spec —
sans rouvrir le problème de calibrage qu'`ADR-0026` a fermé, et sans faire exploser la durée d'arc
(cible spec §5.1 : 12-15 min).

### B3 — La palette entre en collision avec la réserve des couleurs

`LOI-LIS-01` : « une couleur qui **signifie** quelque chose ne doit servir à rien d'autre ».

| Spec | Chez nous aujourd'hui | Verdict |
|---|---|---|
| **CYAN** = projectiles | cyan = **le tir du joueur**, réservé dans le shader du fond | ✅ compatible : sur la planche, les dards cyan **sont** ceux du joueur. La ligne de la spec est juste mal formulée |
| **MAGENTA** = énergie du boss | magenta = Null Choir, et la jauge de boss | ✅ |
| **ROUGE** = danger immédiat | rouge sécurité Helios, peu employé en jeu | ✅ les lasers rouges sont lisibles et libres |
| **ORANGE** = mécanique / mouvement imminent | orange = **explosions et bonus** | ❌ **collision franche** |

⚠️ Sur la planche, l'orange n'est pas un signal : c'est de la **signalétique peinte** sur les rails
(flèches, hachures). Ça, c'est compatible — un marquage n'est pas un clignotement. Mais si l'orange
devient le **télégraphe** d'un rail qui va bouger, il entre en concurrence avec chaque explosion de
l'écran, et le joueur apprendra à l'ignorer.

**À trancher** : soit l'orange reste de la **peinture** et le télégraphe prend une autre couleur,
soit l'orange devient le danger imminent **et quitte** les bonus. Cette seconde option touche la
charte.

### B4 — La charge de forge

Anneaux, rails, nodes, réacteur : c'est un brief entier (`ADR-0004`), du même ordre que la coque du
Leviathan. Il faut le rédiger **après** avoir figé la géométrie de jeu, pas avant — sinon on
commande des pièces dont on ne connaît pas encore les dimensions utiles.

⚠️ **Les anneaux se prototypent sans la forge** : des tores segmentés procéduraux suffisent à
éprouver le puzzle. C'est ce que le projet a déjà fait avec la doublure du survol de lune.

---

## 3. Découpage — le gameplay d'abord, l'habillage en dernier

### Lot 1 — Les anneaux et la fenêtre de vulnérabilité ⭐ le cœur

**C'est l'idée entière de la spec**, et c'est presque uniquement du code.

Deux ou trois anneaux concentriques tournent à des vitesses différentes. Chacun porte des
**ouvertures**. Le flux n'est atteignable **que** lorsqu'une ouverture de chaque anneau s'aligne
avec l'axe joueur → noyau.

- Géométrie : tores segmentés procéduraux (doublure), puis pièces forgées.
- Cible : on n'invente rien — `BulletTarget.enabled` porte déjà « atteignable ou non ».
- Lisibilité : le noyau **change d'état visible** (protégé → vulnérable → critique), et le repère
  battant existe déjà.
- Boucle : `PRESSION → POSITIONNEMENT → OUVERTURE → FENÊTRE → FERMETURE`, 8-12 s.

⚠️ **Le mode d'échec à garder par un test** : un alignement qui n'arrive **jamais** (vitesses en
rapport tel que les ouvertures ne se croisent pas) enfermerait le joueur. La leçon d'`ADR-0029`
s'applique à l'envers — ici, il faut des périodes qui **retombent** en rythme, et il faut le prouver.

### Lot 2 — Les lasers balayants

`Beam` existe, télégraphe compris. Un balayage lent (30-45 °/s) autour du noyau, puis le double
balayage avec son secteur sûr mobile.

Coût faible, rendement élevé : c'est ce qui force à bouger même quand on pourrait rester sous le boss.

### Lot 3 — Les nodes orbitaux

Sous-cibles destructibles en orbite, qui **verrouillent** le réacteur tant qu'elles vivent. L'idiome
existe (plaques, appendices) **et la rangée de pastilles du HUD sait déjà** afficher leur état, leur
désignation et leur repousse.

### Lot 4 — Les rails mobiles

Géométrie qui change l'espace disponible. `EnemyReaction` fournit la machine de télégraphe, avec sa
loi : **ce qui s'allume part**. Un rail qui reculerait après avoir clignoté apprendrait au joueur à
ignorer les clignotements.

### Lot 5 — Le décor dynamique et la parallaxe

Le plus cher en GPU, le moins de gameplay. **En dernier, et seulement si B1 le permet.** Les sept
couches de la spec sont un objectif, pas un prérequis : deux ou trois suffiront probablement à
casser l'impression de « texture posée sous le joueur ».

---

## 4. La règle de lisibilité, et pourquoi elle passe avant l'esthétique

La spec la pose elle-même, et elle est juste :

```
1 JOUEUR  2 PROJECTILES  3 DANGERS  4 POINT FAIBLE  5 MACHINES  6 DÉCOR
```

Le projet a déjà payé cette leçon : trois essais de dôme pour le porteur de bouclier ont tous rendu
**le même aplat**, condamnés par leur **surface** et non par leur réglage — le bloom et le `lift` de
1,25 du post-traitement raviv­ent toute grande surface teintée. Un décor de machine somptueux et
lumineux **remonterait** de la même façon.

⚠️ Conséquence concrète : le décor de cette phase doit être **sombre, peu saturé, peu contrasté** —
et ça se vérifie à la capture 1:1, pas à l'intention.

---

## 5. Ce que ce plan ne fait pas

Il n'engage **rien**. Les quatre points bloquants du §2 appellent des décisions d'opérateur, et deux
d'entre eux (B2, B3) amenderaient des décisions déjà prises.

La question à trancher en premier est **B2** : elle décide si l'on parle d'une plongée enrichie
(+1 min sur l'arc) ou d'une phase de boss nouvelle (+3 min). Tout le reste en découle.
