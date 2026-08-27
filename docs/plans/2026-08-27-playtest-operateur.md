---
titre: Retours de playtest du 2026-08-27 — puissance, regen, noyau, et le mouvement sur rails
date: 2026-08-27
auteur: session Claude, sur retours de l'opérateur après une partie complète (arc entier, rang S)
perimetre: équilibrage de la montée en puissance, signaux de boss, phase du noyau, bibliothèque de trajectoires
etat: instruit et chiffré — rien d'implémenté, quatre chantiers à ordonner
supersede: rien. Complète docs/design/CONFORMITE-AEGIS.md
---

# Retours de playtest — 2026-08-27

Partie complète jouée à la main : titre → vagues → mini-boss → champ d'astéroïdes → Leviathan
(3 cycles) → appontage → victoire, **score 42 910, rang S**, sortie propre. Les cinq changements de
la session sont passés sans remarque.

Quatre retours en sont sortis. **Tous se vérifient dans le code**, et trois d'entre eux ont un
chiffre.

---

## R1 — On arrive en phase 2 à pleine puissance, et les PV ne suivent plus

> « Dans la phase deux les ennemis n'ont pas assez de points de vie vu qu'on commence souvent full
> puissance, et je réduirais le taux de drop de la puissance pour avoir max 4/5 en arrivant en
> phase 2. »

**Mesuré.** La vague d'ouverture compte **107 unités**. Le Power Core tombe tous les **12 kills**
(`_DROP_EVERY = 4`, un bonus sur trois est un Core) :

| Niveau | Atteint au | Part de la vague |
|---|---:|---:|
| 2 | 12ᵉ kill | 11 % |
| 3 | 24ᵉ kill | 22 % |
| 4 | 36ᵉ kill | 34 % |
| **5** | **48ᵉ kill** | **45 %** |

Le joueur passe donc **plus de la moitié de la phase 1 à pleine puissance**. Pire : la vague
distribue **8 Power Cores** alors que **4 suffisent** — la moitié tombe sur un joueur déjà plein et
**ne produit rien**. Un bonus qui ne fait rien est le signal muet de [`LOI-EXP-08`](../design/bible/10-experience-joueur.md).

Et l'écart de puissance est brutal : la cadence se resserre au niveau 2 (×0,8) puis le nombre de
bolts passe de 2 à 4, 5, 7. **Le niveau 5 tire ~4,4 fois plus vite que le niveau 1.** Les unités de
la phase 2 sont pourtant les plus coriaces du bestiaire (Choir Mine 44 PV, Shield Carrier 42) — elles
ne tiennent pas une seconde contre sept flux.

**Proposition chiffrée** : un Power Core tous les **16 kills** (`_POWER_EVERY` de 3 → 4). Niveau 2 au
16ᵉ, 3 au 32ᵉ, 4 au 48ᵉ, 5 au 64ᵉ. Sur les ~45 kills observés en phase 1, le joueur arrive donc en
**niveau 3-4**, ce que demande l'opérateur. ⚠️ Une seule constante, mais c'est de l'équilibrage :
**à rejouer pour confirmer**, pas à décréter.

---

## R2 — La regen des « organes » ne se montre pas

> « Lors des phases de regen des organes, au lieu d'avoir juste un temps avant qu'ils reviennent, on
> pourrait faire grandir leur barre de vie en vert qui montre la regen. »

**Vérifié.** `_leave_dive()` reforme l'armure **instantanément** (`_arm_cycle()` puis
`armour_reformed`). Le « temps » que ressent le joueur est l'**éjection** — `dive_eject_time = 1,0 s`
— pendant laquelle **rien ne se passe et rien ne le dit**.

C'est exactement ce que la loi des signaux nomme : un état existe, il n'est pas communiqué. La jauge
verte qui monte est la bonne réponse — elle transforme une attente en **compte à rebours lisible**.

⚠️ Attention à ne pas rouvrir `ADR-0023` : la jauge du boss montre la **progression du combat**
(`fight_ratio()`, qui ne remonte jamais). Une jauge de regen doit être un **second tracé**, vert, par-dessus
ou à côté — jamais la même mesure qui remonterait, sous peine de rejouer le défaut qui a coûté
l'ADR.

---

## R3 — La phase du noyau : cible illisible, sortie au minuteur, et rien qui bouge

Trois défauts distincts dans la même phase.

### R3a — Le noyau ne se désigne pas comme cible

> « On doit guider l'utilisateur visuellement pour lui montrer que le noyau est la cible, là il
> semble juste un point du décor. »

C'est [`LOI-ENN-02`](../design/bible/02-ennemis-et-vagues.md) — « la priorité de cible se lit d'un
coup d'œil, ou elle n'existe pas » — et le projet a **déjà** payé ce défaut sur le Shield Carrier,
dont la portée « ne se voyait pas » et qu'il a fallu rendre en anneau.

### R3b — ⚠️ On sort au minuteur, et la jauge se fige : c'est un défaut, pas un réglage

> « Il faudrait qu'on soit éjecté quand on a descendu suffisamment les PV, pas sur un timer, car là
> la barre de vie se fige et on attend. »

**Vérifié, et le code le dit lui-même.** Les dégâts sont plafonnés par plongée
(`flux_damage_per_dive()`, `ADR-0026`), et une fois le plafond atteint :

> « Le flux est déjà saturé pour ce passage : **les tirs portent, ils ne comptent plus.** »

La sortie, elle, n'a que deux conditions : `_flux_health <= 0` (dernier cycle) ou
`_dive_elapsed >= dive_time` — **5 secondes fixes**. Un joueur qui atteint le quota en 3 s attend
donc **2 secondes** devant une jauge gelée.

⚠️ **Et `ADR-0026` demandait l'inverse** : « mieux jouer **raccourcit chaque plongée** sans jamais en
supprimer une ». L'intention est écrite dans le fichier ; le code ne l'applique pas. Ce n'est pas un
changement d'équilibrage, c'est **la mise en œuvre d'une décision déjà prise**.

### R3c — La phase est immobile

> « Cette phase n'est pas vivante, rien ne bouge. On pourrait imaginer que le boss bouge et donc le
> noyau suit le mouvement. »

Pendant la plongée, `release_drive()` n'est appelé qu'à la **sortie** : le corps est tenu immobile
pendant toute la phase. Le noyau est donc une cible fixe dans une arène fixe.

---

## R4 — Tout est sur rails, et ça se voit

> « J'aimerais que tous les ennemis aient des mouvements aléatoires non linéaires, même s'ils
> doivent respecter un pattern. Ça fait figé, fête foraine, nul. »

**Vérifié, et c'est structurel.** `EnemyPath` est une bibliothèque de fonctions **pures** :
`(données, âge, spawn) → position`. **Aucun aléa, aucune graine.** Deux unités du même type nées au
même endroit décrivent exactement la même courbe, à chaque partie.

Cette pureté n'est pas un accident : `ADR-0022` la défend explicitement, et elle achète trois choses
qu'on ne veut pas perdre — le pooling sûr (une instance réactivée ne traîne rien), l'indépendance au
pas de temps, et la testabilité headless.

**Il n'y a pas à choisir.** Une **graine par instance**, posée à l'activation, garde les trois
propriétés et casse la répétition :

```
position_at(data, age, spawn)  →  position_at(data, age, spawn, seed)
```

- toujours pure : rien ne s'accumule, la forme ne dépend pas du pas de temps ;
- toujours sûre au pooling : la graine est **réassignée** à chaque activation ;
- toujours testable : une graine fixe rend un test déterministe.

La graine décale la **phase**, module l'**amplitude** et la **fréquence** dans une fourchette bornée
— la signature de la courbe est préservée (`WEAVE` reste un weave), seule sa réalisation change.

⚠️ **Et le remède au « linéaire » existe déjà dans ce dépôt.** `title_stage.gd` fait dériver sa
caméra sur des **périodes volontairement non harmoniques** (11,0 / 7,3 / 17,0 s) avec ce commentaire :

> « la scène ne doit jamais se retrouver deux fois dans la même pose, sinon **l'œil repère la boucle**
> et l'accueil redevient un décor. »

C'est mot pour mot le reproche de l'opérateur, résolu ailleurs et jamais transposé au bestiaire.

⚠️ Ce chantier touche le contrat de `ADR-0022` : il **mérite son ADR**.

---

## Ordre proposé

| # | Chantier | Coût | Nature |
|---|---|---|---|
| **R3b** | Éjecter au quota atteint, pas au minuteur | faible | **défaut** — `ADR-0026` le demandait déjà |
| **R1** | Un Power Core tous les 16 kills | faible | équilibrage — **à rejouer pour confirmer** |
| **R2** | Jauge de regen verte | moyen | signal — attention à `ADR-0023` |
| **R3a** | Désigner le noyau comme cible | moyen | signal |
| **R3c** | Le boss dérive pendant la plongée | moyen | vie de la scène |
| **R4** | Graine par instance + périodes non harmoniques | **élevé** | structurel — **ADR** |

Les deux premiers sont sans ambiguïté et se livrent d'un bloc. R4 est le plus gros et le plus
visible ; c'est aussi celui qui, seul, change la sensation de tout le jeu.
