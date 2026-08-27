---
titre: Reactor Chamber — la phase du noyau devient une machine, pas une cible
date: 2026-08-27
auteur: session Claude, sur spécification et planche de l'opérateur
perimetre: phase DIVE du Pale Leviathan (CoreInterior), assets de forge, budget GPU
etat: **B2 tranché (`ADR-0030`), LOTS 1 ET 2 LIVRÉS**. Lots 3-5 entiers ;
  B1 (budget GPU) et B4 (forge) restent ouverts, B3 partiellement tranché
supersede: rien. Amenderait `ADR-0025` (l'arène) et `ADR-0026` (le plafond par plongée)
---

# Reactor Chamber

L'opérateur a fourni une planche et une spécification complète. Le diagnostic d'ouverture est
exactement celui que la session avait mesuré le matin même :

> « Le joueur entre dans le noyau puis se retrouve face à une cible quasiment fixe. »

Et la règle qu'il en tire :

> **Le décor crée le gameplay.** On évite donc de remplir simplement l'écran avec davantage
> d'ennemis.

✅ **La planche est archivée** : [`assets/reference/concepts/reactor_chamber_concept.png`](../../assets/reference/concepts/reactor_chamber_concept.png),
avec sa ligne de provenance (spec §24.7). Composition **originale** dérivée d'une capture du jeu —
pas une référence tierce.

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

### Lot 1 — Les anneaux et la fenêtre de vulnérabilité ✅ LIVRÉ le 2026-08-27

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

### Lot 2 — Les lasers balayants ✅ LIVRÉ le 2026-08-27

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


---

## Lot 1 — ce que la livraison a appris

**Le budget GPU ne s'est pas matérialisé, pour ce lot-là.** Mesuré sur **Quadro T1000** : **6,45
ms/image** dans l'arène blindée, contre **7,1 à 12,6 ms** relevés sur la même arène *avant* le
chantier. Les arcs sont des `ArrayMesh` de quelques dizaines de triangles : deux anneaux coûtent
moins que la variance entre deux lancements. **B1 reste entier pour les lots 4 et 5**, qui portent
les rails et le décor animé.

⚠️ **Un piège silencieux, et il valait le détour.** `reactor_rings = [...]` avait été écrit **au-dessus**
de `script = ExtResource(...)` dans le `.tres`. Godot applique les propriétés **dans l'ordre** :
posée avant le script, la ligne désigne une propriété que la ressource ne connaît pas encore, et
elle est **ignorée en silence**. Le blindage était absent du jeu, sans erreur ni test rouge — c'est
la garde « le joueur n'est jamais enfermé » qui l'a rattrapé, en constatant que le blindage livré
n'avait aucun anneau.

**Deux défauts connus, à traiter au lot 2 :**

1. ⚠️ **Les tirs traversent visuellement un blindage fermé.** Le verrou est logique, pas physique.
   Le projet a déjà nommé ce défaut sur le Harvester et y a répondu par une gerbe de déviation.
2. ⚠️ **Les anneaux se lisent comme de la peinture au sol.** Posés sous le plan de jeu pour ne pas
   masquer les balles, ils passent sous les nervures du décor livré.


---

## Lot 2 — trois choses, et la palette avance d'un pas

**Les tirs sont ARRÊTÉS par un blindage fermé.** Une seconde cible (`_shield_target`) se pose sur
l'anneau, **au droit du joueur** — là où ses bolts croisent le blindage — et rend une gerbe blanche
avec le son de bouclier. Aucun dégât : ce n'est pas une armure à user, c'est une porte à trouver.

⚠️ **Elle est enregistrée AVANT le flux.** `BulletManager._resolve_hits` parcourt les cibles dans
l'ordre d'enregistrement et **consomme** la balle sur la première qui la réclame : dans l'autre
sens, un tir aurait traversé un anneau fermé pour aller toucher le noyau. Les deux ne sont jamais
actives ensemble — mais l'ordre est une **garantie**, pas un effet de bord d'un état.

**Les anneaux remontent** de −0,30 à −0,08. À −0,30 ils passaient **sous les nervures** du décor et
se lisaient comme de la peinture au sol. Ils restent sous le plan de jeu : la règle de priorité met
les machines derrière les projectiles.

**Le laser balaie**, à −29 °/s, à contresens de l'anneau extérieur.

⚠️ **Simulé avant d'être écrit**, sur trois minutes : un corridor **libre** — ouvert ET hors du
faisceau — existe **100 % du temps**, pire blocage 0,00 s. Le laser met la pression, il ne condamne
jamais. Même exigence que pour les anneaux, par un autre chemin.

⚠️ **Il s'arme après coup** (1,1 s). Le joueur qui vient d'entrer voit d'où part le faisceau et dans
quel sens il tourne **avant** de pouvoir en mourir.

### B3 avance d'un pas, sans être tranché

Le faisceau sortait **orange** — la collision exacte que le plan annonçait. Il est désormais
**rouge sécurité Helios**, ce que la spec de l'opérateur demande elle-même (« ROUGE = danger
immédiat »). `Beam.tint()` pose les couleurs **par instance** : les faisceaux des épines n'ont pas
bougé.

⚠️ **La question de fond reste ouverte** : l'orange comme **télégraphe** de rail (lot 4) entrerait
toujours en concurrence avec les explosions et les bonus. Le laser ne la tranche pas, il la contourne.

### Le budget, mesuré à chaque étape (Quadro T1000)

| État | ms/image |
|---|---:|
| L'arène avant le chantier | 7,1 à 12,6 |
| Anneaux seuls | **6,45** |
| Anneaux + laser | **5,5 à 7,2** |

Deux lots, **aucun coût mesurable** : les arcs sont des `ArrayMesh` de quelques dizaines de
triangles, et le faisceau un quad. **B1 reste entier pour les lots 4 et 5**, qui portent les rails
et le décor animé — c'est là que le budget se jouera.
