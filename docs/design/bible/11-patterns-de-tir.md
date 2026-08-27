---
titre: Patterns de tir — la taxonomie du danmaku, et la parité qui décide de tout
type: reference
statut: actif
maj: 2026-08-27
---

# Patterns de tir

[`01-lisibilite.md`](01-lisibilite.md) dit **comment un pattern se lit**. Cette page dit **de quoi
il est fait** : les familles géométriques, leurs paramètres, et ce que chacune impose au joueur.

## Ce que le genre dit

### Le nombre de balles n'est pas le sujet

> « La première chose à noter, c'est que le facteur qui différencie n'est **pas** le nombre de
> balles. On peut en avoir beaucoup, mais si elles ne sont pas employées avec intention, ce n'est
> pas vraiment du bullet hell. »

### Les familles

| Famille | Construction | Ce qu'elle impose au joueur |
|---|---|---|
| **Anneau** (*ring*) | ≥ 3 balles tirées **au même instant**, écart angulaire commun = 360°/n | seule la **distance** protège ; aucune direction n'est sûre |
| **Éventail** (*spread*, *n-way*) | balles dans un **arc**, écart angulaire commun | ferme un secteur ; on le contourne |
| **Mur** (*wall*) | « toute formation de balles **à travers laquelle le joueur ne peut pas passer** » | **macro-esquive** : contourner, jamais traverser |
| **Pile** (*stack*, *n-stack*) | plusieurs balles **au même angle**, avec un **décalage de vitesse** | « de longs murs parfaits pour le *streaming*, et des lignes qui autorisent la micro-esquive » |
| **Flux** (*stream*) | anneaux ou chaînes de balles **visées**, tirés à la suite | on **s'éloigne latéralement** pour concentrer le flux et libérer l'écran |

### La parité de l'éventail décide de son sens

C'est le détail le plus opérationnel de toute cette page :

> Un nombre **impair** de balles **piège** le joueur ; un nombre **pair** fait que **toutes les
> balles de l'éventail l'évitent**.

Autrement dit, un éventail **visé** :

- **impair** → une balle part **exactement sur la ligne de visée**. Rester immobile tue. Le pattern
  **punit l'inaction**.
- **pair** → l'axe de visée est **vide**. Le joueur est « piégé dans un secteur angulaire **sans être
  touché** » : le pattern **contraint la position** au lieu de punir l'immobilité.

Les deux sont valides — mais ce sont **deux intentions opposées**, et elles se décident par un
nombre.

### Trois manières de choisir l'angle de départ

| Semence d'angle | Effet |
|---|---|
| **fixe** | motifs prévisibles, lisibles, apprenables — mais « laisse des **angles morts** » où le joueur peut se poster |
| **aléatoire** | couverture ; produit des patterns « désordonnés, particulièrement durs à esquiver » |
| **visée** | interaction directe avec la position du joueur |

⚠️ Le conseil est net : **ne pas n'employer que des semences fixes** si le pattern est fait pour être
esquivé — sinon un point sûr existe quelque part, et il sera trouvé.

### Les composés valent mieux que les gros patterns

Une **pile d'anneaux** (mêmes anneaux, vitesses différentes) donne gratuitement de la profondeur :
les composantes se séparent avec le temps, tout en partageant le même angle. Et surtout : « les
balles rapides d'un groupe **plus tardif** peuvent dépasser les balles lentes d'un groupe
**antérieur**, ce qui produit un chevauchement du motif et une complexité supérieure » — sans une
seule balle de plus.

Une **pile d'éventails** a la propriété inverse, et elle est défensive : « les piles d'éventails ont
des **bords nets** et laissent des ouvertures entre les piles, plus loin du point de tir, ce qui
permet de s'échapper ».

### Le vocabulaire de l'esquive

| Terme | Définition |
|---|---|
| **micro-esquive** | enfiler précisément de petits interstices, par mouvements délicats |
| **macro-esquive** | lire **tout l'écran** pour trouver les grandes ouvertures, par grands déplacements |
| **streaming** | éviter des balles visées en bougeant **le moins possible**, pour concentrer le tir en un seul flux et libérer un maximum d'écran |
| **restream** | créer un trou dans ce flux : changement de direction sec, pause, puis retour |

⚠️ **Un pattern ne devient intéressant que s'il désigne son mode d'esquive.** Un mur qu'on croit
micro-esquivable tue ; un nuage qu'on macro-esquive fait perdre l'écran.

## Chez nous — état au 2026-08-27

### La bibliothèque est une taxonomie explicite, et c'est rare

`EnemyFire` (`scripts/enemies/enemy_fire.gd`) est une géométrie **pure** — `(données, salve, index)
→ direction`, sans état, sans nœud, sans allocation — et sa règle d'admission est écrite dans le
fichier : **« deux schémas doivent différer par leur FORME, pas par leurs constantes »**.

| Notre schéma | Famille du genre | Constante |
|---|---|---|
| `SINGLE` | ligne | — |
| `NONE` | — (la menace est ailleurs : aura, aspiration, contact) | — |
| `FAN` | éventail **aveugle** | `FAN_SPREAD_DEG = 62` |
| `AIMED` | éventail **visé** | `AIMED_SPREAD_DEG = 12` |
| `RADIAL` | anneau, avec rotation de phase | `RADIAL_PHASE = 0.5` |

`RADIAL_PHASE = 0,5` fait exactement ce que le genre appelle « régularité **plus** une légère
fluctuation » : une couronne sur deux est décalée d'un demi-intervalle, « les trous de la première
sont bouchés par la seconde, **donc rester immobile ne paie jamais** ».

### Ce qui manque à la taxonomie : la pile

Aucun de nos schémas ne fait varier la **vitesse** à l'intérieur d'une salve. La famille *stack* —
et donc le chevauchement gratuit entre groupes successifs — n'existe pas. C'est le seul axe
géométrique du genre que la bibliothèque n'a pas.

### ⚠️ FAN et AIMED ne sont employés par aucune unité de vague

Vérifié dans les Resources : `fire` vaut `SINGLE` par défaut (`enemy_data.gd:28`) et **aucun
`.tres` d'ennemi ne le surcharge**, sauf trois passages en `NONE` (Leech Drone, Null Maw, Shield
Carrier) et **un seul** en `RADIAL` (Choir Mine, 14 balles).

Donc : les neuf Needle Scout et le Crescent Interceptor tirent **tous une balle droite**. L'éventail
aveugle et l'éventail visé sont **écrits, testés, documentés — et jamais joués**. Le seul schéma qui
punit l'immobilité au niveau des vagues n'est employé nulle part.

Les deux boss, eux, ont leurs propres patterns inline (`boss_controller.gd:281`) : `RADIAL`,
`AIMED_SPREAD`, `FAN`, cyclés toutes les 2 s.

### ⚠️ La parité de l'éventail visé du boss change toute seule à chaque phase

`Pattern.AIMED_SPREAD` tire `count = 3 + _phase` balles :

| Phase | Balles | Parité | Ce que le joueur vit |
|---|---:|---|---|
| 0 | 3 | impair | une balle **sur l'axe** — l'immobilité tue |
| 1 | 4 | **pair** | l'axe est **vide** — l'immobilité devient sûre |
| 2 | 5 | impair | l'immobilité tue de nouveau |

Personne n'a décidé cela : c'est la conséquence arithmétique de `3 + phase`. La phase 1 est donc,
pour ce pattern précis, **plus permissive** que la phase 0 — l'inverse de ce qu'une montée de phase
promet. `Pattern.FAN` (`7 + 2 × phase`) reste impair, et `EnemyFire._spread_ratio()` a le même
comportement de parité pour `FAN` comme pour `AIMED`.

## L'écart, et ce qu'on en fait

**Le plus rentable, et il ne coûte aucun code** : donner `FAN` et `AIMED` à des unités de vague.
Tout est déjà écrit et testé — il manque **deux lignes dans des `.tres`**. Le bestiaire gagnerait
d'un coup l'axe de variété que la page [`02`](02-ennemis-et-vagues.md) cherche, et le jeu son
premier pattern qui punit l'immobilité en dehors des boss.

⚠️ **Avec une contrainte à respecter en le faisant** : `AIMED` en nombre **impair** vise à tuer
l'immobilité, en nombre **pair** à contraindre la position. Choisir, et l'écrire dans le `.tres` —
pas laisser `burst_count = 5` par défaut décider du sens du pattern.

**À instruire, pas à corriger d'office** : la parité de `AIMED_SPREAD` du boss. Ce n'est un défaut
que si l'on constate en jouant que la phase 1 est plus permissive que la phase 0 ; ça peut aussi
être une respiration bienvenue. La mesure est facile — c'est le rôle du sous-agent `balance-prober`.

**Piste ouverte, non décidée** : la famille **pile**. Elle ajouterait de la profondeur sans ajouter
de balles (donc à budget GPU quasi constant), mais elle demande un décalage de vitesse par index,
c'est-à-dire un champ de plus dans `EnemyData` — qui en a déjà quatre axes (`Path`, `Motion`,
`Fire`, `Effect`). À ne pas ouvrir sans raison jouée, comme le dit déjà la page [`02`](02-ennemis-et-vagues.md).

## Sources

- [Sparen's Danmaku Design Studio — Guide A3](https://sparen.github.io/ph3tutorials/ddsga3.html) — la taxonomie complète : anneaux, éventails et leur parité, murs, piles, piles d'anneaux, piles d'éventails, chevauchement.
- [Sparen's Danmaku Design Studio — Guide A2](https://sparen.github.io/ph3tutorials/ddsga2.html) — l'intention avant le nombre, les trois semences d'angle, les angles morts des semences fixes.
- [Help:Glossary](https://shmups.wiki/library/Help:Glossary) — Shmups Wiki : micro/macro-esquive, streaming, restream.
