# ADR-0024 — Le flux du Leviathan a sa propre cadence de référence

- **Date** : 2026-08-25
- **Statut** : accepté (décision du propriétaire, après playtest à puissance maximale)
- **Amende / supersede** : `ADR-0021` sur le seul dimensionnement du flux. Les trois cycles,
  la plongée et le reste du combat sont inchangés.

## Contexte

Deuxième partie du 2026-08-25, lancée **directement au boss avec `--power=5`** — le plafond
du jeu. Le boss est tombé, l'arc s'est terminé (`DOCKING → VICTORY`, score 20 000). Mais le
journal donne le compte exact :

```
CYCLE 1 / 3 — armure / noyau
CYCLE 2 / 3 — armure / noyau
CYCLE 3 / 3 — armure / noyau
DERNIER ASSAUT — armure / noyau      ← 4e
DERNIER ASSAUT — armure / noyau      ← 5e
DERNIER ASSAUT — armure / noyau      ← 6e
```

**Six plongées au lieu de trois, à la puissance maximale du jeu.** Ce n'est pas une question
d'adresse : c'est un défaut de dimensionnement, et il est mesurable.

### La cause : une seule hypothèse de cadence pour deux cibles très différentes

`LeviathanTuning` dimensionnait **les deux temps du combat** avec le même
`reference_dps = 420`, documenté comme « cadence soutenue du joueur à puissance 3 ». Ce
chiffre est exact — pour une cible **large** :

| | dps |
|---|---|
| Puissance 3, 4 canons × 10 PV à 10,42 salves/s, **toutes portent** | **417** ≈ `reference_dps` |
| Plafond théorique à puissance 5 (7 canons) | 729 |
| Puissance 5, **canons droits seuls** (`L`, `R`, `C`) | 312 |
| **Effectivement placé dans le flux au playtest** (5300 PV / 6 plongées / 5 s) | **177** |

Les canons d'aile tirent à ±16°, ceux de bout d'aile à ±31°. Contre quatre grandes plaques
ils portent — et c'est pourquoi la phase d'armure a été jugée bien équilibrée le matin même.
Contre le **flux**, une sphère de 1,80 m de rayon qui **dérive** de 1,60 m, ils partent à
côté. Le modèle supposait que toutes les balles touchaient les deux cibles.

### L'invariant se donnait raison

L'invariant 5 vérifie que le flux est tuable en `cycle_count` passages :

```
atteignable = reference_dps × occupancy_dive × dive_time = 420 × 0,85 × 5,0 = 1785 PV
exigé       = flux_health / cycle_count                  = 5300 / 3      = 1767 PV
```

Il passait. Mais il se comparait à **sa propre hypothèse optimiste**, et le réglage tombait à
**99,0 % du plafond** qu'il autorise (bande permise : 55 à 100 %). Il n'y avait pas de marge,
il y avait 1 % : le combat n'aboutissait en trois cycles que si le joueur plaçait 85 % de son
temps de tir à une cadence qu'il ne peut pas atteindre sur cette cible.

⚠️ **Une garde qui se mesure à la mauvaise hypothèse ne peut pas échouer, et elle rassure.**
C'est la même famille de défaut que celui déjà payé sur ce projet (« une garde sur la mauvaise
propriété est pire que pas de garde »), appliquée cette fois à un modèle de dimensionnement.

## Décision

1. **Deux hypothèses de cadence, pas une.** `reference_dps` (420) reste la cadence contre
   l'armure — cible large, toutes les balles portent, et elle reste **partagée avec le
   mini-boss** pour que les deux combats se comparent. Nouveau `flux_reference_dps` (**208**)
   pour le flux : les deux canons de nez de la puissance 3, les seuls qui touchent une petite
   cible mobile.
2. **L'invariant 5 se compare à `flux_reference_dps`**, et refuse une cadence de flux nulle.
3. **`flux_health` : 5300 → 2400.** Soit 800 PV par plongée contre 884 atteignables — **90,5 %
   du plafond au lieu de 99,0 %**.
4. **Aucun autre réglage ne bouge.** Ni `plate_health`, ni `shell_orbit_period`, ni les durées :
   la phase d'armure venait d'être jugée bonne, et `flux_health` n'entre ni dans
   `armor_duration()` ni dans `dive_duration()`. Le combat dure toujours ~40 s en théorie.

### Ce que ça donne pour le joueur mesuré

Il plaçait **~883 PV par plongée** à puissance maximale. Avec 2400 PV :

- au 2ᵉ passage il en a placé 1766 sur 2400 → **le flux tient, les cycles ont lieu** ;
- il lui faut **2,72 plongées** → **le flux cède pendant la troisième**, avec de la marge.

C'est exactement la promesse d'`ADR-0021` : ni au premier passage, ni jamais.

## Conséquences

- Le libellé `DERNIER ASSAUT` d'`ADR-0023` n'est pas retouché : on supprime sa **cause**
  plutôt que son symptôme. Il reste en place pour le dépassement, qui redevient l'exception
  qu'il aurait toujours dû être.
- Quatre tests neufs dans `test_leviathan_tuning.gd`, dont deux qui gardent précisément la
  confusion d'origine : `flux_reference_dps` doit rester **sous** `reference_dps`, et
  l'ancienne valeur de 5300 PV — qui validait — doit désormais être **refusée**.
- ⚠️ **À surveiller au prochain playtest, conséquence assumée et non résolue** : la jauge
  (`fight_ratio`, `ADR-0023`) répartit désormais **63 % sur l'armure et 37 % sur le flux**,
  alors que le temps se répartit à **45 % / 55 %**. La barre avance donc plus vite pendant
  l'armure que pendant la plongée — soit l'inverse de l'intensité dramatique voulue. Les deux
  objectifs sont en tension réelle : pour que le flux pèse à la fois plus lourd dans la jauge
  **et** tombe en trois passages, il faudrait que le joueur y place davantage de dégâts —
  cible plus grosse, ou fenêtre plus longue. C'est un choix de conception, pas un réglage :
  il n'est pas fait ici.

## Ce qui reste à juger

Le combat n'a **pas** été rejoué après ce changement. Trois cycles à puissance maximale sont
attendus par le calcul et par la mesure ; ils ne sont pas constatés. À vérifier en jouant, et
idéalement **dans les conditions réelles de l'arc** — puissance qui monte avec les vagues,
non `--power=5`, qui ne dit rien du rythme réel.
