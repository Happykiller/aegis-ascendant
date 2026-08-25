# ADR-0026 — Trois cycles par construction : le flux est plafonné par passage

- **Date** : 2026-08-25
- **Statut** : accepté (décision du propriétaire, après trois playtests)
- **Amende / supersede** : `ADR-0024` sur la **méthode** (le dimensionnement ne suffit pas),
  pas sur ses mesures, qui restent justes pour la plongée qu'elles ont mesurée.

## Contexte

Trois parties, trois comptes de cycles différents, toutes à puissance maximale :

| Réglage | Plongées | Dégâts placés par plongée |
|---|---|---|
| `flux_health` 5300, ancienne plongée | **6** | ≥ 883 |
| `flux_health` 2400, ancienne plongée | **4** | 600 – 800 |
| `flux_health` 2400, **arène dédiée** (`ADR-0025`) | **2** | > 1200 |

La dernière est la panne que l'invariant 5 nomme depuis le début : *« trop mou, le boss meurt
au premier passage et les cycles ne servent à rien »*. Deux cycles, l'armure ne revient
qu'une fois, et tout le propos d'`ADR-0021` tombe.

### Pourquoi aucun nombre ne pouvait marcher

Les dégâts réellement placés vont de **600 à plus de 1200** pour le **même joueur** à la
**même puissance**. Pour que le flux survive à deux passages et cède au troisième, il
faudrait simultanément :

```
flux_health > 2 × 1200 = 2400        (survivre au pire des deux premiers)
flux_health ≤ 3 ×  600 = 1800        (céder au meilleur des troisièmes)
```

**Contradictoire.** Aucune valeur ne satisfait les deux. `ADR-0024` ne pouvait pas tenir —
non parce que sa mesure était fausse, mais parce que la grandeur mesurée n'est pas stable.

### Et l'arène a déplacé la cible sous le calibrage

`ADR-0025` a doublé la mise sans que personne ne le prévoie : dans l'arène, le réacteur est
**droit devant le chasseur, ligne de tir dégagée**, dans un shooter vertical. Avant, la cible
dérivait devant une masse encombrée, le vaisseau relevé de 2,2 m sous une sphère. `ADR-0024`
avait donc calibré contre **une plongée qui n'existe plus**.

⚠️ La leçon générale : **un calibrage mesure une situation, pas une intention.** Changer la
situation invalide le calibrage en silence — aucun test n'échoue, l'invariant reste vert, et
c'est le playtest suivant qui paie.

## Décision

**Le flux ne peut perdre au plus qu'un tiers de sa réserve par passage**
(`flux_damage_per_dive()`). Les tirs au-delà portent, ils ne comptent plus.

Conséquence, et c'est tout l'objet : **trois cycles sont désormais le MEILLEUR cas, vrai par
construction et non par réglage.**

- Mieux jouer **raccourcit** chaque plongée, sans jamais en supprimer une.
- Moins bien jouer en **ouvre une de plus** — la sanction reste juste, et `DERNIER ASSAUT`
  (`ADR-0023`) garde son sens.
- `flux_health` reste à **2400** : il ne pilote plus le nombre de cycles, seulement le rythme
  à l'intérieur d'un passage.

## Vérification

Partie jouée immédiatement après, mêmes conditions (`--power=5`, droit au boss) :

```
CYCLE 1 / 3 — armure → noyau
CYCLE 2 / 3 — armure → noyau
CYCLE 3 / 3 — armure → noyau  →  DOCKING → VICTORY
```

**Trois cycles exactement**, aucun dépassement, aucune mort, aucune erreur. C'est la première
partie où le combat se déroule comme `ADR-0021` le décrit.

Trois tests gardent la règle : une plongée ne peut pas tuer plus que sa part, un passage
saturé cesse de compter sans arrêter le combat, et trois passages parfaits suffisent — *et
pas deux*.

## Ce qui reste à juger

- **Le ressenti du plafond** : quand un passage est saturé, les tirs portent sans compter.
  Invisible si les 5 s s'écoulent de toute façon, frustrant si le joueur le sent. Non tranché.
- **La mort en phase d'armure** observée à puissance maximale sur une partie ; l'opérateur a
  choisi de rejouer avant de conclure, et elle ne s'est pas reproduite. Un point sur deux.
- La tension jauge/temps signalée par `ADR-0024` (63 % de la barre pour 45 % du temps) est
  **toujours ouverte**.
