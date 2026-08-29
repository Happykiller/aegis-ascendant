---
titre: Niveau 2 — le survol du vaisseau-monde
type: plan
auteur: concepteur principal
date: 2026-08-29
état: lots 0 et 1 LIVRÉS (planche déposée, lore écrit) ; lots 2-6 à faire
périmètre: architecture de campagne, nouveau niveau jouable, coque de forge
supersède: rien — premier plan multi-niveaux du projet
---

# Niveau 2 — le survol du vaisseau-monde

Demande de l'opérateur (2026-08-29) : un niveau entier passé à **survoler un vaisseau ennemi
immense, de la proue à la poupe**, sur le modèle du survol de lune de la phase inter-boss — mais
la coque remplace le décor, et elle se défend.

Planche d'inspiration fournie : `ENEMY CAPITAL`, bio-mécanique, 6,8 km, quatre armements listés
(*Singularity Lance*, *Gravity Pulsar*, *Spawn Drones*, *Corruption Field*).
⚠️ **Elle n'est pas encore dans le dépôt** — à déposer dans `assets/reference/inspiration/`
(ADR-0009) avec sa ligne de provenance avant tout brief de forge.

## Ce qui est tranché

| Question | Décision |
|---|---|
| Phase ou niveau ? | **Un vrai niveau 2, séparé.** Pas une 7ᵉ phase du niveau 1 |
| 3ᵉ mécanique | **L'épine dorsale** — voir §3 |
| Tourelles, ponts d'envol | Retenus tous les deux |

## 0. Le vocabulaire, parce qu'il diverge

Le jeu contient **un niveau** à **six phases** (`FIGHTER_WAVES → MINI_BOSS → ASTEROID_FIELD →
FINAL_BOSS → DOCKING → VICTORY`). Ce qu'on appelait « le niveau 2, le champ de mines » est la
**phase** `ASTEROID_FIELD`. La bible de campagne, elle, prévoit **douze niveaux**
(`docs/lore/CAMPAGNE.md`).

À partir d'ici : **niveau** = une mission complète avec son propre écran de rapport ; **phase** =
un segment à l'intérieur d'un niveau. Le survol est le **niveau 2**.

## 1. Lore — ✅ TRANCHÉ ET ÉCRIT (2026-08-29)

`CAMPAGNE.md` donne aujourd'hui **Ambry** au niveau 2 : l'avant-poste où le pilote a grandi,
silencieux depuis 379, qu'on découvre *debout, intact, re-plombé* — et **radié**.

**Validé par l'opérateur : on fusionne.** Le vaisseau s'appelle **The Long Cortège**, nom
repris d'un candidat écarté au nom de la faction (`NULL_CHOIR.md` §1, rapport de l'an 344) —
« un convoi qui accompagne quelque chose de mort depuis très longtemps ».

**Le principe :** Le vaisseau-monde est **ce qui a
pris Ambry**. On ne va pas à l'avant-poste : on survole la chose qui l'emporte, et l'avant-poste
est **greffé sur sa coque**, quelque part vers la poupe — intact, re-plombé, éclairé.

Ce que ça gagne :

- la révélation d'Ambry (*radié, pas détruit*) arrive **à la fin d'un survol**, au terme d'une
  traversée de plusieurs minutes : elle est méritée au lieu d'être annoncée ;
- le vaisseau-monde cesse d'être un décor : c'est un **convoi funéraire** qui emporte un village.
  Il correspond au lore de l'Unisson mieux qu'un vaisseau de guerre — *il n'attaque pas, il
  emporte* ;
- ⚠️ **plafond respecté** : le joueur voit qu'ils prennent des structures entières. Il n'apprend
  ni pourquoi, ni ce qu'est une Voix, ni la Grille.

⚠️ **La planche dit « FLAGSHIP » et liste des armes.** Notre ennemi n'est pas une marine : le
vaisseau se défend parce qu'on le dérange sur un ouvrage, pas parce qu'il fait la guerre. La forme
de la planche est retenue ; le vocabulaire de sa fiche, non.

## 2. Architecture — ce qui manque vraiment

C'est le vrai coût, et il est en amont du contenu.

**L'état des lieux, vérifié :**

- `GameState` n'a **aucune notion de niveau** — un seul état `FIGHTER_COMBAT` ;
- `title_menu.gd` code `graybox.tscn` **en dur** ;
- `mission_report.gd` REJOUER fait `reload_current_scene()` — recommencer, jamais continuer ;
- ⚠️ **`graybox_root.gd` (1 470 lignes) EST le niveau 1** : il précharge ses deux boss et pilote
  son arc en dur. **Le copier pour le niveau 2 serait la pire décision de ce chantier.**

**Lot 1 — la campagne comme donnée** (prérequis de tout le reste)

- `resources/data/level_data.gd` — une Resource typée par niveau : `id`, `scene`, `title`,
  `briefings`, `music`. Avec son `validate()`, comme toute Resource de contenu (spec §31).
- `resources/campaign/campaign_book.tres` — la liste ordonnée. Le niveau 1 y entre **sans changer
  d'un octet** : c'est le test que la structure ne casse rien.
- Un autoload `Campaign` (ou un champ dans `GameState`) qui tient le niveau courant et sait dire
  `next()`.
- `mission_report` gagne **CONTINUER** quand un niveau suivant existe ; REJOUER reste pour le
  dernier et pour la défaite.
- Progression persistée dans `user://settings.cfg`, section `campaign` — le mécanisme existe
  (`SettingsManager`), il suffit d'une clé.

⚠️ **Ce lot ne doit RIEN changer au ressenti du niveau 1.** Sa recette : jouer l'arc en entier et
ne voir aucune différence, sauf le bouton du rapport.

**Lot 2 — le niveau 2 a son propre script racine**, pas une copie de `graybox_root`. Il réutilise
ce qui est déjà générique (`BulletManager`, `WaveSpawner`, `FighterHUD`, `GameplayPlane`,
`GravityWell`) et n'hérite d'aucune phase. Son déroulé est un **survol continu**, pas une suite de
rencontres : c'est un script différent parce que c'est un jeu différent, pas par duplication.

## 3. Le contenu du survol

### La coque — un décor qui défile, pas un boss

Le vaisseau ne bouge pas dans le plan de jeu : **c'est lui qui défile sous le joueur**, comme la
lune de `MoonFlyby` (ADR-0027), et le même arbitrage s'applique — il **remplace** le fond au lieu
de s'y ajouter, pour la même raison de budget GPU. Découpé en **tronçons** enchaînés, chacun avec
sa densité d'obstacles : proue effilée, flancs à tourelles, ponts d'envol, section arrière, poupe
aux réacteurs.

⚠️ **Budget à mesurer sur la Quadro T1000, pas sur la RTX 4080** — c'est elle qui contraint
(`howto-mesurer-la-perf`). Le survol de lune coûtait 0,323 ms/image ; c'est le repère.

### Les trois mécaniques de coque

**A. Tourelles** — fixées à la coque, télégraphient, tirent, encaissent. Le jeu sait déjà faire :
`CitadelLife` anime les tourelles de l'Aegis Citadel, `Beam` gère un tir télégraphié
(`leviathan_combat`). ⚠️ Elles doivent défiler **avec** la coque : une tourelle qui reste à
l'écran pendant que le décor avance casse l'illusion de survol en une seconde.

**B. Ponts d'envol** — des baies d'où sortent les unités du bestiaire. Réemploi direct de
`WaveSpawner`, avec le point d'apparition **ancré au pont** et non au bord de l'écran. Un pont
détruit cesse de produire : c'est ce qui rend le joueur acteur de la densité qu'il subit.

**C. L'épine dorsale** *(la mécanique choisie)* — une artère d'énergie court sur toute la longueur
du vaisseau, ponctuée de **nœuds**. Abattre un nœud **éteint les tourelles du tronçon suivant**.

Ce qu'elle apporte, et pourquoi elle vaut mieux qu'un troisième type d'ennemi : elle donne au
survol une **structure de décision** au lieu d'une liste de cibles. À chaque tronçon le joueur
choisit — abattre les tourelles une par une (sûr, lent, coûteux en bouclier) ou remonter à la
source (rapide, mais le nœud est défendu et il faut le trouver avant d'être passé devant).
⚠️ **Un survol se déroule dans une seule direction et ne revient jamais en arrière** : rater un
nœud est définitif, et c'est ce qui rend le choix réel.

Ancrage de lore, jamais dit à voix haute : le vaisseau **n'a pas de blindage sur son artère**
parce qu'il n'a jamais eu à se défendre d'un intérieur. C'est un ouvrage, pas un navire de guerre.

## 4. Découpe proposée

| Lot | Contenu | Vérification |
|---|---|---|
| ~~**0**~~ | ✅ Planche déposée, indexée, tracée | fait le 2026-08-29 |
| ~~**1**~~ | ✅ Lore écrit : `CAMPAGNE.md` niveau 2, `NULL_CHOIR.md`, charte | fait le 2026-08-29 |
| **2** | Architecture de campagne (`LevelData`, `CampaignBook`, CONTINUER, progression) | **le niveau 1 se joue à l'identique** |
| **3** | `BRIEF-00NN` à la forge : la coque du vaisseau-monde, par tronçons | rendue et **regardée** (ADR-0006) |
| **4** | Le survol : défilement, tourelles, ponts d'envol | jouable de bout en bout |
| **5** | L'épine dorsale et ses nœuds | le choix se sent en jouant |
| **6** | Rythme, densité, durée cible | `/jouer`, puis `balance-prober` |

⚠️ **Les lots 2 et 4 sont les seuls vraiment risqués.** Le 2 touche à ce qui marche déjà ; le 4
est un mode de jeu que le dépôt n'a jamais écrit.

## 5. Ce que ce plan ne fait pas

- Il ne spécifie **aucun chiffre d'équilibrage** : ils se mesurent en jouant (`ADR-0019`).
- Il ne promet **pas les douze niveaux**. Il construit la structure qui les rendrait possibles, et
  livre le deuxième.
- Il ne touche pas au niveau 1 autrement que par le bouton du rapport.
