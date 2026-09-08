# ADR-0050 — Le survol prend à la poupe : les conduites de l'artère

- **Date** : 2026-09-08
- **Statut** : accepté (décision de l'opérateur : les modèles tiers deviennent des **cibles
  destructibles sur l'artère**, et les couper **affaiblit la poupe**)
- **Plan d'exécution** : [`2026-09-08-couper-l-artere.md`](../plans/2026-09-08-couper-l-artere.md)
- **Assets** : `BRIEF-0108` (réduction du pylône, de la conduite et du flexible)
- **Complète** : `ADR-0049` — la poupe se défend ; celui-ci lui donne une prise en amont

## Contexte

**Ce que le joueur faisait pendant quatre minutes de survol n'avait aucune conséquence sur la
fin.** Il pouvait raser dix-sept tourelles, sept ponts d'envol et cinq nœuds d'épine, ou traverser
en ligne droite : la poupe était exactement la même dans les deux cas. Le niveau 2 se jouait en
deux moitiés qui ne se parlent pas.

L'artère les reliait déjà **visuellement** — le canal magenta court sur les 500 m et se termine au
collecteur des trois groupes (`BRIEF-0106` §5), et c'est lui que le blackout éteint quand la
propulsion meurt. Il ne lui manquait que d'être **coupable**.

## La décision

Douze **conduites destructibles** sont posées le long de l'artère. Chaque conduite coupée retire
de la **charge** à la poupe : le Cortège arrive à ses moteurs avec moins d'énergie qu'il n'en
aurait eu.

| Grandeur | Valeur | Où |
|---|---|---|
| Conduites | **12** | `CortegeArtery.CONDUITS` |
| Retrait par conduite | **2,5 %** | `charge_per_conduit` |
| Plancher | **0,70** | `charge_floor` |
| Ce qu'elle change | la **morsure du souffle**, la **vie des verrous** | `CortegeSternTuning` |

## Les quatre choses qui ont été écartées, et pourquoi

### 1. ⚠️ L'effet local — parce que le nœud d'épine le fait déjà

La première formulation était « couper une conduite éteint son tronçon d'artère ». Elle a été
refusée : **le nœud d'épine éteint déjà son tronçon**, et c'est la mécanique centrale du corridor.
Deux cibles pour un effet de même forme, c'est une cible de trop et un joueur qui ne sait plus
laquelle sert à quoi.

### 2. ⚠️ L'escalade et les salves — parce que ça viderait la fin

La charge aurait pu retarder un palier ou alléger une salve. Non : la garnison et les vagues sont
ce que le vaisseau **lâche pour se défendre**, pas ce que l'artère alimente. Les brancher dessus
rendrait la phase finale plus **vide** au lieu de plus **courte** — et `ADR-0049` vient précisément
de la remplir. Un test lit la source de `CortegeStern` pour garder cette frontière.

### 3. ⚠️ Une charge continue — parce qu'une barre ne doit pas bouger toute seule

Elle est **figée au montage de la poupe**, avant que le premier verrou n'existe. La recalculer en
cours de phase ferait varier la vie d'un verrou pendant qu'on lui tire dessus : une cible dont la
barre descend sans qu'on l'ait touchée. Une conduite coupée après l'arrivée ne compte pas — le
vaisseau a déjà rempli ses moteurs.

### 4. ⚠️ Un plancher plus bas — parce que ce serait un autre jeu

À 0,70, un survol parfait rend la phase 30 % plus douce. En dessous de 0,50 (refusé par
`validate()`), le joueur méticuleux ne jouerait plus le même jeu que le joueur pressé : il jouerait
un jeu **plus facile**, ce qui est l'inverse d'une récompense. Douze conduites à 2,5 % atteignent
exactement le plancher, et la douzième compte encore — les deux sont testés.

## Ce que le joueur en voit

- **Sur le coup** : la conduite se rompt, son flexible avec, et le score monte de 450.
- **À l'arrivée** : Lyra le dit — *« Ses conduites ont lâché en route, Halyard. Il arrive à ses
  moteurs avec moins qu'il n'en voulait. »* ⚠️ **Seulement si la charge a baissé** : annoncer
  « rien n'a changé » à un joueur qui n'a rien coupé lui apprendrait qu'il a raté quelque chose
  sans lui dire quoi.
- **Au rapport** : `ARTERE 7/12`, ajouté à la trace de comms. ⚠️ **Un complément, pas une ligne**
  — le rapport est partagé avec le niveau 1, qui n'a pas d'artère.

⚠️ **Et c'est le rapport qui rend la mécanique COMPTABLE.** La réplique dit que c'est arrivé ; elle
ne dit pas combien, donc elle ne se compare pas d'une partie à l'autre. Une récompense qu'on ne
peut pas mesurer n'est pas une récompense, c'est une ambiance.

## Conséquences

- La pose des douze conduites est gardée par un banc qui **lit la coque** : aucune à moins de 8 m
  d'un nœud d'épine, ni de 6 m d'une tourelle ou d'un pont.
- ⚠️ **Une cote de ce lot n'est pas lue** : l'assise des conduites (`DECK_Y = −4,30`), parce que
  l'artère n'a aucun marqueur dans la coque livrée. Un test la compare au `y` échantillonné des
  marqueurs voisins. La vraie sortie serait un brief de forge pour douze repères
  `CTRL | Conduite NN` — noté au backlog.
- ⚠️ **L'équilibrage de la poupe devient plus urgent, pas moins** (`ADR-0049`) : on vient de
  donner au joueur un moyen de la rendre plus facile alors qu'on ne sait toujours pas si elle est
  trop dure.
