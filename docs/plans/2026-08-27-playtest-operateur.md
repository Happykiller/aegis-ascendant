---
titre: Retours de playtest du 2026-08-27 — puissance, regen, noyau, et le mouvement sur rails
date: 2026-08-27
auteur: session Claude, sur retours de l'opérateur après une partie complète (arc entier, rang S)
perimetre: équilibrage de la montée en puissance, signaux de boss, phase du noyau, bibliothèque de trajectoires
etat: **TOUT LIVRÉ** le 2026-08-27 (R1 à R4, `ADR-0029`, plus R5 et R6 d'une seconde partie).
  Reste le jugement en jeu : trois signaux et un équilibrage ne se valident pas au journal
supersede: rien. Complète docs/design/CONFORMITE-AEGIS.md
---

# Retours de playtest — 2026-08-27

Partie complète jouée à la main : titre → vagues → mini-boss → champ d'astéroïdes → Leviathan
(3 cycles) → appontage → victoire, **score 42 910, rang S**, sortie propre. Les cinq changements de
la session sont passés sans remarque.

Quatre retours en sont sortis. **Tous se vérifient dans le code**, et trois d'entre eux ont un
chiffre.

---

## R1 — On arrive en phase 2 à pleine puissance ✅ LIVRÉ

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

## R2 — La regen des « organes » ne se montre pas ✅ LIVRÉ

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

### R3a — Le noyau ne se désignait pas comme cible ✅ LIVRÉ

> « On doit guider l'utilisateur visuellement pour lui montrer que le noyau est la cible, là il
> semble juste un point du décor. »

C'est [`LOI-ENN-02`](../design/bible/02-ennemis-et-vagues.md) — « la priorité de cible se lit d'un
coup d'œil, ou elle n'existe pas » — et le projet a **déjà** payé ce défaut sur le Shield Carrier,
dont la portée « ne se voyait pas » et qu'il a fallu rendre en anneau.

### R3b — On sortait au minuteur, la jauge se figeait ✅ LIVRÉ

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

### R3c — La phase était immobile ✅ LIVRÉ

> « Cette phase n'est pas vivante, rien ne bouge. On pourrait imaginer que le boss bouge et donc le
> noyau suit le mouvement. »

Pendant la plongée, `release_drive()` n'est appelé qu'à la **sortie** : le corps est tenu immobile
pendant toute la phase. Le noyau est donc une cible fixe dans une arène fixe.

---

## R4 — Tout est sur rails, et ça se voit ✅ LIVRÉ (`ADR-0029`)

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
| ~~R3b~~ | ~~Éjecter au quota atteint~~ | — | ✅ **livré** le 2026-08-27 |
| ~~R1~~ | ~~Un Power Core tous les 16 kills~~ | — | ✅ **livré** — ⚠️ **reste à rejouer pour confirmer** |
| ~~R2~~ | ~~Jauge de regen verte~~ | — | ✅ **livré** — un filet de 2 px SOUS la jauge, `ADR-0023` intact |
| ~~R3a~~ | ~~Désigner le noyau comme cible~~ | — | ✅ **livré** — et l'écart était pire que « pas assez visible » |
| ~~R3c~~ | ~~Le boss dérive pendant la plongée~~ | — | ✅ **livré** — la dérive du flux devient non harmonique |
| ~~R4~~ | ~~Graine par instance + périodes non harmoniques~~ | — | ✅ **livré** — [`ADR-0029`](../decisions/ADR-0029-la-derive-organique.md) |

Les deux premiers sont sans ambiguïté et se livrent d'un bloc. R4 est le plus gros et le plus
visible ; c'est aussi celui qui, seul, change la sensation de tout le jeu.


---

## Ce que la mise en œuvre a trouvé, et que le plan ne disait pas

**R3a n'était pas un défaut de décoration : le repère MANQUAIT tout court.** Le halo du flux
(`_apply_flux_glow`) se pose sur le **cœur du boss** — resté **dehors** pendant la plongée
(`ADR-0025` : l'arène est une zone dédiée montée à l'origine du monde). Dans l'arène, la cible
n'avait donc **aucun rendu**, et elle dérive jusqu'à **~2,6 u** de l'ancre. Le joueur tirait sur
le réacteur du décor pendant que la cible était ailleurs : un signal **faux**, que la loi des
signaux tient pour pire qu'un signal absent.

**L'enveloppe de dérive était recopiée dans trois tests** sous forme d'un `sqrt(2.0)` — une
formule dupliquée qui ne pouvait que diverger du code. Elle est désormais exposée par
`flux_drift_envelope()` : le repère, les tests et le réglage partagent une seule vérité.

**La première jauge de regen a été écartée après l'avoir regardée.** Elle remplissait le creux
de la barre, ancrée à droite : elle ne mentait pas, mais sa longueur dépendait de l'avancement du
combat — trente pixels au cycle 1. Or elle mesure un **temps**, pas des dégâts : elle doit
balayer la même distance à chaque reconstruction.

⚠️ **Et une garde a pris une hypothèse à moi en défaut** : le premier test de la jauge croyait
abattre le flux d'une seule plongée. C'est impossible **par construction** (`ADR-0026` plafonne
les dégâts à un tiers par passage) — il fallait aller jusqu'au troisième cycle.


---

# Seconde partie du 2026-08-27 — deux défauts de plus

Arc complet à nouveau, fermé pendant l'appontage. Mini-boss à **15 560** contre 16 690 la partie
d'avant : **−1 130 points**, la trace indirecte d'un Power Core de moins ramassé en phase 1. R1 fait
donc ce qu'on lui demandait.

## R5 — « Mes tirs ne vont pas jusqu'au bout de l'écran » ✅ LIVRÉ

**Mesuré à la capture** : le bolt le plus haut mourait à **~170 px du bord**, soit 16 % de la hauteur
d'écran. Ils ne s'arrêtaient pas — ils **disparaissaient dans le cadre**, ce qui est pire.

⚠️ **Ce n'était pas la portée.** Le `ttl` du tir joueur autorise **36 unités** de trajet quand le
terrain en fait 16 : l'allonger n'aurait rien changé. C'était le **culling**. `BOUNDS` est le terrain
de **jeu**, pas le champ **visible** — le fond en montre bien davantage, et les ennemis naissent à
`y = 9,5` où on les voit arriver. La coupe à `y = 10` (bornes + marge de 2) tombait donc en plein
cadre.

`CULL_MARGIN` passe de **2,0 à 5,0**. Vérifié à la capture : le bolt le plus haut est désormais à
**~20 px du bord**. Deux gardes, dont une qui empêche de rechercher le défaut du mauvais côté :
*le `ttl` n'a jamais borné quoi que ce soit*.

## R6 — Les jauges d'appendice ne montrent pas la repousse ✅ LIVRÉ

> « Je ne vois pas les barres de vie de la griffe, etc. du premier boss se recharger pendant que le
> noyau est exposé. »

**Vérifié, et c'est le jumeau exact de R2 sur l'autre boss.** `limb_rebuild_time` vaut **14 secondes**,
et pendant tout ce temps la jauge restait **pleine et sombre, immobile** : la gauge n'était émise
qu'aux **transitions** — à la chute, puis au retour. Le joueur ne pouvait pas savoir s'il lui restait
dix secondes de répit ou une.

`HarvesterLimb.rebuild_ratio()` expose l'avancement, `limb_rebuild_changed` le publie à l'image, et
le HUD pose **le même filet vert** que la reconstruction de l'armure du Leviathan — un seul
vocabulaire : *vert fin = ça revient, et voilà dans combien de temps*.

⚠️ La barre sombre pleine **ne bouge pas** : elle dit toujours « celui-ci est tombé ». Deux
informations, deux tracés.
