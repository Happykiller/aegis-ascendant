# Couper l'artère — ce que le survol prend à la poupe

- **Date** : 2026-09-08
- **Demande** : de nouveaux modèles tiers (conduite énergétique, flexible) sont livrés « pour
  potentiel intégration » ; l'opérateur tranche qu'ils deviennent des **cibles destructibles sur
  l'artère**, et que les couper **affaiblit la poupe**.
- **Assets** : `BRIEF-0108` (réduction), en cours à la forge.
- **État de départ** : commit `2a8f123`, 999 tests verts, GPU 3,6 ms/image (RTX 4080).

---

## 0. Le problème que ça résout, et qui n'est pas « il manque des cibles »

**Ce que le joueur fait pendant quatre minutes de survol n'a aucune conséquence sur la fin.** Il
peut raser dix-sept tourelles, sept ponts d'envol et cinq nœuds d'épine, ou traverser en ligne
droite : la poupe est exactement la même dans les deux cas. Le niveau se joue en deux moitiés qui
ne se parlent pas.

L'artère les relie déjà, **visuellement** : le canal magenta court sur les 500 m et se termine au
collecteur des trois groupes (`BRIEF-0106` §5), et c'est lui que le blackout éteint quand la
propulsion meurt. Il ne lui manque que d'être **coupable**.

⚠️ **ET C'EST POUR ÇA QUE L'EFFET N'EST PAS LOCAL.** La première idée — « couper une conduite
éteint son tronçon d'artère » — a été écartée : le **nœud d'épine fait déjà exactement ça** sur
son tronçon, et c'est la mécanique centrale du corridor. Deux cibles pour un effet de même forme,
c'est une cible de trop et un joueur qui ne sait plus laquelle sert à quoi.

---

## 1. La règle, en une phrase

> **Chaque conduite coupée retire de la charge à la poupe.** Le Cortège arrive à ses moteurs avec
> moins d'énergie qu'il n'en aurait eu.

Une seule grandeur : la **charge**, de 1,00 (rien coupé) à un plancher. Elle est décidée à la fin
du survol et ne bouge plus. Elle agit sur **deux** choses, pas plus :

| Ce qu'elle change | Pourquoi celle-là |
|---|---|
| **La morsure du souffle** (`surge_bite`) | C'est le seul danger de la phase qui vienne des MOTEURS. Moins d'énergie, moins de souffle : le lien est lisible sans une ligne de dialogue. |
| **La vie des verrous** (`anchor_health`) | Ce sont eux que l'artère tient serrés. Moins d'énergie, ils cèdent plus vite — et le joueur le SENT au premier verrou, pas au troisième moteur. |

⚠️ **PAS L'ESCALADE, PAS LES SALVES.** La garnison et les vagues sont ce que le vaisseau lâche
pour se défendre, pas ce que l'artère alimente. Les brancher dessus rendrait la fin plus vide au
lieu de la rendre plus courte, et le chantier du 2026-09-07 vient précisément de la remplir.

⚠️ **ET IL Y A UN PLANCHER.** Tout couper ne doit pas donner une phase finale gratuite : c'est la
récompense d'un survol méticuleux, pas un interrupteur. Plancher proposé : **0,70** — au mieux,
30 % de moins. À caler en jouant.

---

## 2. Les lots

### LOT 1 — La conduite, pièce destructible

`CortegeConduit`, sur le patron de `CortegeAnchor` (quatre états, hitbox depuis la Resource,
jamais depuis le mesh — `ADR-0034`).

- Quatre états câblés sur les quatre clips livrés : `Actif → Endommagé → Rupture → Rompu`.
- Hitbox, vie et score dans `CortegeTuning`.
- ⚠️ **La fenêtre de ciblage est `target_span`**, comme tout le reste du niveau, et la position
  passe par `GameplayPlane.aim_point_of` : c'est une pièce POSÉE SUR LA COQUE, donc elle tombe
  sous la leçon de `pratique-poser-une-piece-sur-une-coque` — sa hitbox n'est pas là où elle se
  voit, et un banc doit le vérifier avant toute capture.
- Le flexible l'accompagne : **décor**, pas cible. Il habille la liaison et se rompt avec elle.

**Recette** : un test par transition ; une capture par état, `Rompu` compris — c'est celui que le
joueur verra le plus longtemps.

### LOT 2 — La pose le long de l'artère

Une table de placement, comme la garnison de poupe.

- Combien : **dix à douze**, réparties sur les cinq tronçons, **pas une par tronçon** — un pas
  régulier se sent, et le nœud d'épine occupe déjà ce rythme-là.
- Où : sur l'artère, donc sur l'axe. ⚠️ **L'axe est aussi la route du joueur** : une conduite qui
  barre le canal se lirait comme un obstacle, pas comme une cible. Les poser en **bordure**
  d'artère, et le vérifier par la projection.
- ⚠️ **Elles ne doivent pas voler la place des nœuds d'épine.** Cinq nœuds, cinq stations
  connues : aucune conduite dans leur fenêtre.

**Recette** : les invariants de placement du `test_cortege_stern_garrison` transposés — hitbox
dans le plan de vol, dans la fenêtre de tir, et **aucun chevauchement à l'écran**.

### LOT 3 — La charge, et ce qu'elle change

- `CortegeSternTuning` gagne `charge_floor` et le facteur par conduite.
- `CortegeRoot` compte les conduites coupées pendant le survol et passe la charge à la poupe
  **au montage**, avant que le premier verrou n'existe.
- ⚠️ **La charge est FIGÉE à l'entrée de la phase.** La calculer en continu ferait varier la vie
  d'un verrou pendant qu'on lui tire dessus — c'est-à-dire une cible dont la barre bouge sans
  qu'on l'ait touchée.
- Lyra le dit **une fois**, à l'arrivée, et seulement si la charge a réellement baissé.

**Recette** : un test qui prouve que la charge est bornée, monotone, et figée après `begin()`.

### LOT 4 — Le retour, l'équilibrage, la doc

- Comment le joueur SAIT qu'il a gagné quelque chose : c'est la question ouverte du lot. Une
  réplique suffit-elle ? Faut-il un chiffre au rapport de mission ?
- ADR : la mécanique et son plancher.
- Ghost : ce que la pose sur l'axe aura appris.

---

## 3. Ce qui est hors périmètre

- **L'escalade et les salves de la poupe** : elles ne dépendent pas de l'artère.
- **Le nœud d'épine** : sa mécanique ne bouge pas d'une ligne.
- **Le pylône** du `BRIEF-0108` : il va sur la poupe, il ne fait pas partie de cette mécanique.
- **L'équilibrage de la poupe** (`ADR-0049`, backlog) : toujours ouvert, et ce plan le rend
  **plus** urgent — on s'apprête à donner au joueur un moyen de la rendre plus facile alors qu'on
  ne sait pas encore si elle est trop dure.
