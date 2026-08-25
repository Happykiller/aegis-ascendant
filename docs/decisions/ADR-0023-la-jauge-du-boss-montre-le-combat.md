# ADR-0023 — La jauge du boss final montre le COMBAT, plus la phase en cours

- **Date** : 2026-08-25
- **Statut** : accepté (décision du propriétaire, après playtest)
- **Amende / supersede** : `ADR-0020` sur le seul point de la jauge (« la jauge montre la
  phase en cours, et se remplit à nouveau à la bascule »). Le reste d'`ADR-0020` et tout
  `ADR-0021` sont inchangés.

## Contexte

Premier playtest du combat refondu en cycles (`ADR-0021`). Verdict de l'opérateur :

> « Le combat contre le boss de fin est mieux équilibré, mais j'ai réalisé phase 1 phase 2
> phase 1 phase 2 et j'ai l'impression que c'était en boucle. »

L'équilibrage était donc acquis. La lisibilité de la **progression**, non — et le journal
de la partie disait pourquoi, ligne par ligne :

```
[Level] leviathan cycle 1/3 — armure     [Level] leviathan cycle 3/3 — armure
[Level] leviathan cycle 1/3 — noyau      [Level] leviathan cycle 3/3 — noyau
[Level] leviathan cycle 2/3 — armure     [Level] leviathan cycle 4/3 — armure   ← quatrième tour
[Level] leviathan cycle 2/3 — noyau
```

### La cause : la seule mesure qui prouvait l'avancement n'allait qu'à la musique

`LeviathanCombat` expose deux mesures, toutes les deux justes, toutes les deux testées :

| Mesure | Ce qu'elle vaut | Se remplit à nouveau ? |
|---|---|---|
| `structure_ratio()` | la santé de ce qu'on peut casser **maintenant** | **oui, à chaque bascule** |
| `fight_ratio()` | la part du combat qui reste, toutes phases confondues | jamais |

Le HUD recevait la **première**. Le joueur voyait donc, dans l'ordre : armure 100→0, noyau
100→0, armure 100→0, noyau 100→0, armure 100→0, noyau 100→0. **La jauge faisait
littéralement une boucle sous ses yeux** — l'opérateur n'a pas mal interprété le combat, il
a décrit exactement ce que le HUD lui affichait.

`fight_ratio()` existait, était correct et gardé par un test
(`test_the_fight_progress_never_climbs_back_up`). Son **unique** consommateur était
`_music.boss_health_ratio`. L'oreille savait que le combat montait ; l'œil n'avait rien.

⚠️ **Aucun test ne pouvait voir ce défaut**, et ce n'était pas une négligence : les tests du
module gardaient les deux mesures et avaient raison sur les deux. Le module était juste,
c'est le **câblage** qui était faux. C'est le pendant exact de la leçon déjà payée sur ce
projet — *un test de géométrie ne remplace pas un test d'existence* — appliqué cette fois
au branchement plutôt qu'au rendu.

### Pourquoi `ADR-0020` avait raison, et pourquoi il ne l'a plus

`ADR-0020` a choisi la jauge par phase **délibérément**, pour un bon motif : l'idiome de
shmup « il lui reste une deuxième barre ». Cet idiome fonctionne parce qu'il y a **deux**
barres — un boss en deux temps, une bascule, une surprise.

`ADR-0021`, pris le même jour, a remplacé les deux phases par **trois cycles de deux
temps** — soit **six** remplissages. Répété six fois, « il lui reste une deuxième barre »
ne se lit plus comme une révélation mais comme du surplace. La décision d'`ADR-0020`
n'était pas fausse : `ADR-0021` en a retiré la prémisse sans que personne le remarque.

## Décision

1. **La jauge du boss final montre `fight_ratio()`.** Elle part pleine, descend, et ne
   remonte jamais — du premier tir à la mort du boss.
2. **La santé de la cible courante n'est pas perdue** : elle vit sur la rangée de pastilles
   de plaques, qui suit déjà le cycle (4, puis 3, puis 2).
3. **Un compteur de cycle persistant** est affiché à droite du nom du boss : `CYCLE 2 / 3`.
   Le nombre de cycles n'existait jusqu'ici que dans le journal.
4. **Au-delà du dernier cycle prévu, le compteur NOMME au lieu de compter** :
   `DERNIER ASSAUT`, jamais `CYCLE 4 / 3`.
5. **La bannière de plongée cesse de dire la répétition.** Elle disait `ENCORE` à tous les
   passages sauf le premier — le mot nomme le surplace dans le seul moment du combat qui
   pouvait nommer le progrès. Elle compte désormais : `NOYAU — PASSAGE 2`, `3`, `4`.

### Ce qui n'est PAS décidé ici

**L'équilibrage n'est pas touché.** L'opérateur venait de le juger meilleur ; aucun réglage
de `LeviathanTuning` n'est modifié par cet ADR. Le quatrième cycle observé au playtest reste
**permis** — il est simplement nommé au lieu d'être affiché comme une anomalie.

## Conséquences

- Le combat n'a jamais été borné à `cycle_count` et ne l'est toujours pas :
  `plates_for_cycle()` rend le plancher de plaques indéfiniment, et le boss ne meurt qu'une
  fois le flux assez frappé. L'**invariant 5** de `LeviathanTuning` garantit que trois tours
  *suffiraient* à un joueur tirant 85 % du temps dans le noyau à la cadence de référence :
  c'est une **hypothèse de dimensionnement, pas une fin de combat**. Le playtest l'a
  démontré en produisant un quatrième tour. Cette distinction est désormais écrite dans le
  code, à côté du compteur.
- La musique est inchangée : elle recevait déjà `fight_ratio()`. HUD et partition lisent
  maintenant la même valeur, ce qui supprime par construction la divergence qui avait coûté
  le `music 9 -> 8 -> 9` du playtest précédent.
- Nouveau fichier de tests `tests/unit/test_leviathan_hud_relay.gd` (5 méthodes) : il garde
  le **relais**, pas le module — la jauge reçoit bien la progression, elle ne remonte jamais
  sur trois cycles, et le compteur ne peut pas afficher `4 / 3`.

## Ce qui reste à juger

Cet ADR corrige ce que le joueur **voit**. Il ne dit pas si trois cycles sont le bon compte,
ni si un quatrième tour reste agréable une fois qu'on sait où l'on en est. À rejuger à la
partie suivante — et seulement là.
