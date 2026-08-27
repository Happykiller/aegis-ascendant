---
titre: Règles et systèmes — les boucles de rétroaction et l'économie
type: reference
statut: actif
maj: 2026-08-27
---

# Règles et systèmes

Les autres domaines décrivent des **contenus** : des vagues, des boss, des patterns. Celui-ci décrit
ce qui les relie — les **boucles de rétroaction** qui font qu'un succès en appelle un autre, ou
qu'il se paie.

| Loi | Force | Énoncé |
|---|---|---|
| `LOI-SYS-01` | RÉFÉRENCE | Deux familles de rétroaction, et deux seulement |
| `LOI-SYS-02` | **LOI** | Une boucle positive sans contrepoids s'emballe |
| `LOI-SYS-03` | INTENTION | Les deux familles ensemble règlent la difficulté |
| `LOI-SYS-04` | **LOI** | On conçoit des mécaniques, le joueur reçoit une expérience — jamais l'inverse |
| `LOI-SYS-05` | **LOI** | Sans ressource qui se dépense, il n'y a pas d'économie |
| `LOI-SYS-06` | **LOI** | Une règle cachée sur laquelle le joueur ne peut rien se lit comme un bug |
| `LOI-SYS-07` | **LOI** | Dans un shoot vertical le joueur vise en se DÉPLAÇANT : aucune porte ne se filtre sur son azimut |

---

### `LOI-SYS-01` · Deux familles de rétroaction — [RÉFÉRENCE]

| | Boucle **positive** (renforçante) | Boucle **négative** (équilibrante) |
|---|---|---|
| Définition | « permet au joueur de **bâtir sur ses succès** » — ce qui arrive fait que ça arrive encore, plus fort à chaque tour | « plus vous poussez fort, **plus elle repousse** » |
| Effet ressenti | accomplissement, montée en puissance, emballement | tension maintenue, retour au milieu |
| Exemple canonique | les *killstreaks* : tuer donne des atouts qui font tuer | l'objet qui vise **le premier** d'une course |
| Danger | l'emballement : le meneur devient inatteignable | l'effort annulé : le joueur cesse de croire que jouer mieux change quelque chose |

### `LOI-SYS-02` · Une boucle positive sans contrepoids s'emballe — **[LOI]**

L'avertissement est documenté et daté : « une **seule** boucle de rétroaction positive peut nuire à
l'équilibre d'un jeu ». Le cas d'école a résisté à plusieurs rééquilibrages avant d'être retiré.

Un jeu peut légitimement n'avoir **que** des boucles positives — c'est un choix de générosité. Mais
alors le contrepoids doit venir d'ailleurs (une difficulté **scriptée**, par exemple), et être
identifié comme tel.

### `LOI-SYS-03` · Les deux familles ensemble règlent la difficulté — [INTENTION]

C'est la combinaison qui est décrite comme « le Graal » : les succès sont **récompensés** par la
positive, pendant que la capacité croissante du joueur est **contenue** par la négative.

Sans la positive, jouer mieux ne se ressent pas ; sans la négative, la partie se décide dans les
deux premières minutes.

### `LOI-SYS-04` · On conçoit des mécaniques, le joueur reçoit une expérience — **[LOI]**

Le cadre **MDA** (*Mechanics, Dynamics, Aesthetics*) sépare trois couches : les **règles** qu'on
écrit, les **dynamiques** qui en émergent pendant la partie, l'**expérience** qui en résulte. Le
concepteur va des mécaniques vers l'expérience ; **le joueur fait le chemin inverse** et ne voit
jamais les règles.

⚠️ Conséquence pratique : une boucle de rétroaction n'est **jamais** visible en lisant le code d'un
système isolé. Elle naît de deux systèmes qui se parlent.

### `LOI-SYS-05` · Sans ressource qui se dépense, il n'y a pas d'économie — **[LOI]**

Une ressource qui se gagne mais ne se **dépense** jamais n'est pas une ressource : c'est un
compteur. Le joueur ne choisit jamais entre deux emplois d'une même chose, donc il ne prend aucune
décision d'économie.

Un seul mécanisme dépensable — une bombe, une jauge, une charge — introduit d'un coup : le conflit
d'objectifs de [`LOI-SCO-02`](06-score-et-rang.md), une décision récurrente dans la micro-boucle, et
une boucle négative naturelle (on le dépense quand on va mal).

### `LOI-SYS-06` · Une règle cachée sur laquelle le joueur ne peut rien se lit comme un bug — **[LOI]**

Généralisation de la quatrième règle du rang ([`LOI-SCO-06`](06-score-et-rang.md)) à tout système
adaptatif. Le joueur n'a pas besoin de **comprendre** le système ; il a besoin de constater que ce
qu'il fait **change** quelque chose. À défaut, il attribue la variation au hasard ou au défaut.

### `LOI-SYS-07` · Le joueur vise en se déplaçant, jamais en pivotant — **[LOI]**

Dans un shoot vertical, le tir part **droit devant**. Le joueur n'a pas d'azimut : il n'a qu'une
**position**. Son seul moyen de choisir *où* il frappe est de se placer dans l'axe de la cible —
c'est-à-dire, pour une cible qui est devant lui, de s'aligner **latéralement** et rien d'autre.

Il en découle une règle qu'on ne peut pas contourner par le réglage :

> **Aucune porte, aucun obstacle, aucune fenêtre de vulnérabilité ne peut se filtrer sur l'azimut
> du joueur autour de sa cible.** Le seul azimut qu'il puisse présenter est celui d'où il tire —
> un seul, toujours le même.

C'est le piège le plus coûteux du genre, parce qu'il **se conçoit très bien sur le papier**. Un
blindage percé d'ouvertures qui tournent est une belle idée : elle demande au joueur de « trouver
le corridor et d'aller s'y placer ». Elle marcherait dans un jeu à visée libre. Ici, elle demande
quelque chose qui **n'existe pas** — et la mécanique dégénère silencieusement en **attente** : le
joueur ne peut qu'espérer que l'ouverture passe devant lui.

Le symptôme est reconnaissable et il ne ressemble pas à sa cause : le combat n'est pas *dur*, il est
**long**. Le joueur joue bien, sa cadence est bonne, et rien n'avance. On croit à un problème de
points de vie ; c'en est un de géométrie.

**Comment vérifier.** Ne jamais mesurer « une ouverture existe-t-elle quelque part sur le cercle ».
C'est la mesure qui rassure et ne dit rien. Mesurer la **fraction du temps où la ligne de tir
réelle est dégagée** — depuis la seule direction dont le joueur dispose. Les deux chiffres peuvent
différer d'un facteur trois sans qu'aucun test ne rougisse.

**Ce qui reste permis**, et qui est la bonne façon d'employer l'idée : un obstacle mobile qui coupe
la ligne de tir **par intermittence**. Il ne demande plus au joueur de se placer, il **rythme** son
tir — et un rythme, dans ce genre, se lit et s'anticipe. La différence entre les deux tient en une
question : *le joueur peut-il agir sur l'ouverture, ou seulement l'attendre ?*

Corollaire d'équilibrage : la fraction de temps dégagée est une **entrée du calcul de dégâts**, pas
un détail de mise en scène. Si l'obstacle coupe la moitié du temps, la cible doit avoir la moitié
des points de vie. Une estimation de cette fraction qu'aucun test ne confronte à la géométrie livrée
est un [`LOI-SYS-06`](#loi-sys-06--une-règle-cachée-sur-laquelle-le-joueur-ne-peut-rien-se-lit-comme-un-bug) de plus, du côté du concepteur cette fois.

## Sources

- [Game systems: Feedback loops](https://machinations.io/articles/game-systems-feedback-loops-and-how-they-help-craft-player-experiences) — Machinations : les deux familles, l'avertissement sur l'emballement.
- [Feedback Loops – Game Design Toolkit](https://tkdev.dss.cloud/gamedesign/toolkit/feedback-loops/) — la formulation « renforçante / équilibrante ».
- [Mechanics, Dynamics, and Aesthetics](https://pressbooks.usnh.edu/creatinggames/chapter/mechanics-dynamics-and-aesthetics/) — le cadre MDA et la lecture inversée concepteur/joueur.
