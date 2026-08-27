---
titre: Level design — l'espace, les repères, la reprise
type: reference
statut: actif
maj: 2026-08-27
---

# Level design

[Niveau et rythme](03-niveau-et-rythme.md) traite le **temps** d'un niveau. Ce domaine traite son
**espace** — la taille du terrain, les repères qu'on y pose, la manière dont on l'écrit, et ce qui
se passe quand le joueur y meurt.

| Loi | Force | Énoncé |
|---|---|---|
| `LOI-LVL-01` | **LOI** | Le rapport vaisseau/écran commande tout le reste |
| `LOI-LVL-02` | INTENTION | Un niveau révèle, puis combine |
| `LOI-LVL-03` | INTENTION | Le décor est une barre de progression implicite |
| `LOI-LVL-04` | **LOI** | Le niveau fait bouger, ou il ne sert à rien |
| `LOI-LVL-05` | **LOI** | Aucun ennemi ne surgit hors du champ visible |
| `LOI-LVL-06` | **LOI** | Deux patterns simultanés, deux apparences de balle |
| `LOI-LVL-07` | CONTRAINTE | Un niveau s'écrit en file d'actions, pas en minuteurs dispersés |
| `LOI-LVL-08` | CONTRAINTE | Checkpoint ou reprise sur place : choisir, et en assumer le prix |

---

### `LOI-LVL-01` · Le rapport vaisseau/écran commande tout le reste — **[LOI]**

> Un **petit** personnage sur un **grand** écran accueille un jeu **rapide** et beaucoup d'éléments
> simultanés ; un personnage qui **remplit** une large part de l'écran autorise moins de sprites et
> laisse **moins de temps pour anticiper** les attaques.

C'est le paramètre qui commande densité possible, vitesse des projectiles, marge d'esquive et taille
des télégraphes.

⚠️ **C'est donc un paramètre d'équilibrage déguisé en constante technique.** Modifier les bornes du
terrain ou la taille de la hitbox change la difficulté du jeu entier sans toucher à une seule valeur
d'équilibrage. Un tel changement se décide, il ne s'ajuste pas.

### `LOI-LVL-02` · Un niveau révèle, puis combine — [INTENTION]

> Un bon *stage design* est censé **révéler toutes les mécaniques** disponibles au joueur, puis le
> mettre au défi de les **assembler** dans des situations variées, à mesure que le jeu durcit.

Et le mouvement des ennemis appartient à la conception du **niveau**, pas à celle de l'ennemi : la
créativité des trajectoires est le premier levier de variété d'une section.

### `LOI-LVL-03` · Le décor est une barre de progression implicite — [INTENTION]

> La clé pour gagner à un shmup est la **mémorisation** ; créer un fond **mémorisable** aide à
> orienter le joueur sur l'endroit **exact** où il se trouve dans le niveau.

Un fond qui se répète sans repère prive le joueur de la seule réponse à « où en suis-je ? »
(cf. [`LOI-BCL-04`](08-boucle-de-jeu.md)).

### `LOI-LVL-04` · Le niveau fait bouger — **[LOI]**

> « La conception de chaque niveau est structurée pour vous **donner envie de zigzaguer partout**. »

Un niveau qui laisse jouer depuis une seule position a échoué, quelle que soit sa densité.

### `LOI-LVL-05` · Aucun ennemi ne surgit hors du champ visible — **[LOI]**

> « Si les ennemis ne sont pas visibles par le joueur, comment le joueur pourrait-il seulement avoir
> une chance ? »

Les unités **entrent** dans le champ ; elles n'y apparaissent pas.

### `LOI-LVL-06` · Deux patterns simultanés, deux apparences de balle — **[LOI]**

> « Des patterns simultanés distincts doivent avoir des balles **d'apparence différente**. »

Sous pression, le joueur ne sépare pas deux nuages identiques issus de deux sources. C'est le cas où
[`LOI-LIS-02`](01-lisibilite.md) — grouper — devient insuffisant : il faut aussi **distinguer**.

### `LOI-LVL-07` · Un niveau s'écrit en file d'actions — [CONTRAINTE]

Une **file** — `poser(unité, x, y)`, `attendre(durée)` — qui permet de **remanier les formations** en
les déplaçant dans la liste. Des délais dispersés dans le code interdisent la seule chose dont un
niveau a besoin : être réordonné vingt fois.

### `LOI-LVL-08` · Checkpoint ou reprise sur place : choisir, et en assumer le prix — [CONTRAINTE]

| | **Checkpoint** | **Reprise sur place** |
|---|---|---|
| Comportement | on renaît à un point fixe, **puissance remise à zéro** | on renaît là où l'on est tombé |
| Réputation | « associé à une difficulté brutale » | permissif |
| Risque | boucle de mort : trop faible pour repasser le passage qui vient de tuer | **perte d'enjeu** |

Une troisième voie existe — reprise sur place **sans aucune perte** — qui supprime la boucle de mort
par construction, et l'enjeu avec. Elle est légitime si elle est **choisie**, pas subie.

## Sources

- [Pixelblog 31 — Shmup Design Part 1](https://www.slynyrd.com/blog/2020/12/14/pixelblog-31-shmup-sprite-design) — SLYNYRD : le rapport vaisseau/écran, les repères de fond et la mémorisation.
- [The Anatomy of a Shmup](http://shmuptheory.blogspot.com/2010/02/anatomy-of-shmup.html) — SHMUPtheory : le zigzag, les ennemis hors champ, les balles d'apparence distincte.
- [What does "stage design" mean to you?](https://shmups.system11.org/viewtopic.php?f=1&t=58682) — shmups.system11.org : révéler puis combiner. ⚠️ Forum consulté via résumé de recherche (403 aux robots).
- [Shmup Level Design/Scripting](https://gamedev.net/forums/topic/661568-shmup-level-designscripting-i39m-so-lost/5184798/) — GameDev.net : la file d'actions.
- [Help:Glossary](https://shmups.wiki/library/Help:Glossary) — Shmups Wiki : checkpoint, *Gradius syndrome*.
