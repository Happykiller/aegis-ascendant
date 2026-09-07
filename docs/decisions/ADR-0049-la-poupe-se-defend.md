# ADR-0049 — La poupe se défend : l'écart assumé à la spec §19

- **Date** : 2026-09-07
- **Statut** : accepté (décision de l'opérateur : « *il va falloir qu'on mette du challenge.
  Aujourd'hui, il n'y a rien, on tire sur les trucs* »)
- **Déroge à** : `SPEC §19` — « les moteurs sont les protagonistes ; je réduirais énormément les
  ennemis, pas de respawn » — **pour la phase finale du niveau 2 uniquement**
- **Ne touche pas** : `SPEC §17` (le silence final), confirmé intouchable par l'opérateur
- **Plan d'exécution** : [`2026-09-07-la-poupe-se-defend.md`](../plans/2026-09-07-la-poupe-se-defend.md)

## Contexte

La phase finale du niveau 2 — l'arrachement des trois groupes propulsifs — a été livrée en huit
lots et jouée de bout en bout le 2026-09-07. Elle fonctionne : dix verrous, quatre états,
arrachement en cinq temps, blackout, silence, aveu de Lyra, victoire.

Et elle se joue **sans adversaire**. L'opérateur l'a traversée entière **sans perdre un point de
bouclier** : le seul danger était la colonne de poussée, qu'il suffit de ne pas traverser.

Le code tenait explicitement les deux nuées du corridor en laisse dès le montage de la poupe, en
citant la spec §19. C'était fidèle au texte, et le résultat est une conclusion de niveau vide.

## La décision

**Le vide est levé. Le respawn ne l'est pas.**

Ce qui entre :

- une **garnison** de douze tourelles aux trois calibres, posée sur le corps du vaisseau et sur
  des plates-formes volantes ;
- une **escalade** à quatre paliers, accrochée aux arrachements et non à un minuteur ;
- **quatre salves** d'ennemis, accrochées aux mêmes évènements.

Ce qui reste de la spec §19, et qui est gardé par des tests :

- **Pas de respawn.** Une tourelle abattue reste abattue ; une salve consommée ne revient pas.
  `_launch_salvo` retire son nom du jeu dès qu'il a servi — un second `begin()` remettrait
  l'horloge du semeur à zéro et lui referait cracher son pool entier, c'est-à-dire le respawn
  interdit, obtenu par accident.
- **Les moteurs restent les protagonistes.** Rien ne masque un verrou, et seule la pièce la moins
  chère (55 PV) a le droit de se trouver dans la colonne de tir d'un verrou — une moyenne (180) ou
  une lourde (520) y serait un mur devant la seule cible de la phase.
- **Le silence de la spec §17 est intouchable.** Aucune salve après la coupure de propulsion ; ce
  qui vole encore finit sa trajectoire, et plus une seule coque ne naît.

## Les quatre arbitrages, et ce qui a été écarté

| # | Question | Retenu | Écarté, et pourquoi |
|---|---|---|---|
| D1 | Le rythme | **Escalade sur les arrachements** | Un **minuteur** punirait le joueur qui explore ; l'arrachement punit celui qui avance, et c'est le seul des deux qui raconte quelque chose — « le Cortège se défend de ce qu'on lui prend ». Une **garnison fixe** aurait fait de l'arrivée le pic de la phase, et la fin se serait jouée en descente. |
| D2 | Le placement | **Par calibre** | Les légères peuvent garder un berceau ; les moyennes et lourdes tiennent les flancs et l'avant. |
| D3 | Les vagues | **Salves évènementielles** | Un **flux continu** aurait fait de la phase un combat de vagues avec des verrous en décor. Une **ligne de temps unique** aurait fait tomber la salve du second moteur à la trente-huitième seconde, que le joueur l'ait arraché ou non. |
| D4 | La fin | **Le silence reste vide** | Un dernier assaut sur la mort des moteurs aurait effacé l'image qui clôt le niveau. |

## Les trois contraintes découvertes en le faisant

Elles ne se déduisaient d'aucune cote, et chacune a coûté une itération jugée en capture.

1. **Une pièce n'est pas touchable là où elle se voit.** `aim_point_of` projette sa hitbox d'un
   facteur qui dépend de sa HAUTEUR (0,54 sur le pont, 0,81 sur un pylône). Trop au large, elle
   est visible et intouchable ; trop en profondeur, elle vise sans jamais tirer — et ce second
   défaut ne produit ni erreur, ni test rouge, ni ligne de journal.
2. **Un volume libre n'est pas un volume visible.** Les trois groupes propulsifs font onze mètres
   de long et masquent le massif arrière — la seule surface plane franche de la poupe — pendant
   toute la phase. La règle utile est plus forte que l'emprise des berceaux et la contient :
   **devant** la face de poupe, ou **au large** des nacelles.
3. **Une pièce en réserve ne peut pas attendre sur place.** Éteinte puis passée au bleu froid des
   verrous d'ancrage, elle a été signalée les deux fois comme un canon en panne. Un objet immobile
   au milieu d'une fusillade ne peut pas vouloir dire « plus tard ». La réserve **arrive** : elle
   entre par hors cadre sur sa plate-forme quand le joueur l'a méritée.

Le détail de méthode est dans
[`pratique-poser-une-piece-sur-une-coque`](../../.claude/resources/pratique-poser-une-piece-sur-une-coque.md).

## Conséquences

- `SPEC §19` doit être lue avec cet ADR : il **prime** en cas d'écart (règle du projet).
- Le contenu chiffré — nombre de pièces, paliers, composition des salves — est **du réglage**, pas
  de la décision : il vit dans `CortegeSternTuning` et dans les quatre `wave_cortege_stern_*.tres`,
  et il bougera avec l'équilibrage.
- **L'équilibrage n'est pas fait.** Il demande une partie jouée à la main ; le banc, qui n'esquive
  pas, ne peut pas trancher. Voir `docs/BACKLOG.md`.
