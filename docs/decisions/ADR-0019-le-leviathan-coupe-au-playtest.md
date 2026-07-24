# ADR-0019 — Le Leviathan coupé au playtest : ~67 s, et « plus gros » se mesure en durée

- **Date** : 2026-07-24
- **Statut** : accepté (décision du propriétaire après playtest manuel)
- **Contredit** : spec §7 (« 3 à 4 minutes pour le boss final ») — un ADR prime sur la spec
- **Complète** : ADR-0018 (le boss final se démonte) — même combat, tuning révisé
- **Référence de conception** : `docs/design/BOSS_PALE_LEVIATHAN.md` §2, §7.2

## Contexte

Le combat du Pale Leviathan acté par ADR-0018 est câblé, testé (invariants de `LeviathanTuning`,
enchaînement des quatre phases piloté en headless) et livré. Il **fonctionne**. Mais au premier
playtest manuel réel, il s'est révélé **injouable** — pas par un bug, par son dimensionnement.

Verdict de l'opérateur, verbatim :

> « beaucoup beaucoup trop long, j'ai arrêté volontairement, les pastilles P 1..4 se vidaient, le
> boss encore à 80 %, j'ai pas compris les phases, il n'a fait qu'aller de gauche à droite, rien ne
> s'est passé. »

Deux pannes distinctes derrière cette phrase :

1. **Durée.** Les phases visaient 65-75 / 55-65 / 50-60 s (§7.2 d'origine), soit ~3 min 10 de combat
   **parfait** — et bien plus en réel, car un tir sur le corps clos ricoche sans dégât hors de la
   fenêtre. À `plate_health = 3200`, la phase 1 seule durait ~68 s. Le joueur abandonne avant la
   phase 2.
2. **Lisibilité.** En phase 1, une seule plaque encaisse à la fois (celle dans l'arc face au joueur),
   les autres tirs ricochent — et rien à l'écran ne dit **laquelle** viser. D'où « j'ai pas compris
   les phases, rien ne s'est passé ». Traité séparément (signal `piece_active_changed`, surlignage
   HUD, télégraphe émissif in-world) ; **cet ADR ne couvre que la durée**.

## Décision

### 1. Couper les points de vie pour viser ~20 s par phase de brisure

Le modèle de dimensionnement d'ADR-0018 est conservé mot pour mot :

```
durée_de_phase = PV_de_la_phase / (reference_dps × occupation)
```

Seuls les PV changent. `reference_dps = 420` et les occupations (0,45 / 0,35 / 0,40 / 0,80)
restent les leviers déjà justifiés.

| Champ | Avant | Après | Durée obtenue |
|---|---|---|---|
| `plate_health` | 3200 | **950** | 20,1 s |
| `node_health` | 2800 | **950** | 19,4 s |
| `spike_health` | 1500 | **550** | phase 3 combinée |
| `core_health` | 3200 | **1200** | 20,2 s (épines + noyau) |
| `heart_health` | 2600 | **2600** (inchangé) | 7,7 s |

**Total ≈ 67 s** de combat net (contre ~33 000 PV / ~3 min 10 avant). Le cœur ne bouge pas : à
2600 PV il tombe en 6,2 s, soit sous les 0,7 × 12 s de la fenêtre d'ouverture (invariant 4) — la
marge d'erreur de la phase 4 est intacte.

### 2. « Plus gros que le mini-boss » se mesure désormais en durée et en variété, pas en PV bruts

ADR-0018 supposait implicitement — et un test l'affirmait (`test_the_final_boss_is_substantially_
bigger_than_the_mini_boss`) — que le boss final devait totaliser **au moins le double des PV** du
Choir Harvester (~11 500 sur trois cycles). La coupe rend cela faux : à 12 650 PV, le Leviathan
n'est plus que ~1,1× le Harvester en dégâts bruts.

C'est assumé. Le boss final reste supérieur au mini-boss là où ça compte pour le joueur :

- **la durée** — ~67 s de combat net contre ~2 min de Harvester dont l'essentiel est de la répétition ;
- **la variété** — quatre règles distinctes qui ne se répètent pas (BRISER / RÉSISTER / PRIORISER /
  OSER), là où le Harvester rejoue un cycle unique de verrou.

Un boss « éponge à PV » est précisément l'anticlimax qu'ADR-0018 refusait. Empiler des PV pour
satisfaire un seuil de comparaison irait contre l'esprit d'ADR-0018 autant que contre le retour de
l'opérateur. Le test est **recadré** en conséquence : il compare la durée totale (> 60 s) et non la
somme des PV.

## Conséquences

- **Un ADR prime sur la spec.** Le §7 de la spec annonce « 3 à 4 minutes » ; ce combat vise ~67 s.
  L'écart est délibéré et acté ici. La spec n'est pas modifiée ; cet ADR fait autorité.
- `resources/data/leviathan_tuning.gd` (défauts) **et** `resources/bosses/pale_leviathan_tuning.tres`
  (ancres) portent les nouvelles valeurs, tenus synchrones.
- Quatre tests de `tests/unit/test_leviathan_tuning.gd` sont mis à jour : bornes de durée par phase
  (15-25 s / < 10 s), total (55-85 s, renommé — ce n'est plus « 3-4 min »), plancher de
  `total_structure()` (> 12 000), et le test de comparaison au mini-boss recadré sur la durée.
- `docs/design/BOSS_PALE_LEVIATHAN.md` §2 et §7.2 reflètent les nouvelles durées et PV.
- **La coupe est validée sur les chiffres, pas sur le jeu, tant que `balance-prober` (chronologie par
  phase mesurée) et un `/jouer` manuel ne l'ont pas confirmée.** Le retour opérateur portait sur le
  ressenti, pas sur un tableur : la boucle se referme au réel.

## Alternatives écartées

- **Couper moins pour préserver « boss final ≥ 2× mini-boss en PV ».** Écartée : à ces occupations,
  garder > 23 000 PV ramène le total vers ~2 min, soit exactement le « trop long » rejeté par
  l'opérateur. Les deux objectifs sont incompatibles ; le retour de jeu tranche.
- **Baisser `reference_dps` ou remonter les occupations** au lieu des PV. Écartée : `reference_dps`
  est l'hypothèse partagée avec le mini-boss (elle rend les deux combats comparables), et les
  occupations sont déjà justifiées phase par phase. Toucher aux PV est le levier local et lisible.
- **Garder les durées et compter sur la seule lisibilité pour rendre le combat supportable.**
  Écartée : même parfaitement télégraphié, ~3 min sur une même règle par phase reste trop long — la
  durée et la lisibilité sont deux pannes séparées, corrigées séparément.
