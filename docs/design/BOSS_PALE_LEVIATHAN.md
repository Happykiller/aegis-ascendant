# THE PALE LEVIATHAN — conception du boss final

- **Statut** : proposition de conception (aucun code écrit)
- **Rédigé par** : concepteur principal
- **Date** : 2026-07-23
- **Amende** : spec §12 (déjà amendée par ADR-0010 : le boss se combat **au chasseur**)
- **Références** : `docs/forge/CHARTE_CREATIVE.md` §2–§4, `assets/reference/DA.md` §5.2/§6,
  `ADR-0008` (pipeline 3D), `ADR-0010` (un seul vaisseau), `BRIEF-0024` (coque actuelle),
  `BRIEF-0039` (le précédent qui a rendu le mini-boss animable)
- **Planche existante** : `assets/reference/concepts/pale_leviathan_concept_sheet.png`

---

## 1. Pourquoi ce document

### 1.1 L'état réel du boss final

`scenes/bosses/pale_leviathan.tscn` est un `BossController` **nu**. Il déclare 20 000 PV, une hitbox
de 2,7, `phase_count = 4` — et rien d'autre. Ses quatre « phases » se déclenchent aux seuils de PV et
ne changent que deux choses : la **forme de trajectoire**
(`SWAY → FIGURE_EIGHT → ORBIT → CHARGE_RETREAT`, `scripts/bosses/boss_movement.gd`) et le **nombre de
balles** des trois motifs génériques `RADIAL / AIMED_SPREAD / FAN`, qui cyclent toutes les deux
secondes et gagnent 12 % de cadence par phase (`scripts/bosses/boss_controller.gd:260-293`).

Le corps est **vulnérable en permanence**. Il n'y a ni sous-cible, ni verrou, ni condition. C'est
cinq fois les points de vie du mini-boss, sans sa mécanique : un sac à PV.

### 1.2 Ce qu'il ne faut surtout pas faire

Le Choir Harvester a une vraie boucle, et elle est bonne : trois appendices destructibles qui
protègent le corps, une fenêtre qui s'ouvre quand les trois sont à terre en même temps, et une
repousse qui referme tout. Le réflexe serait de la rejouer en plus gros — six appendices, deux iris.

Ce serait un anticlimax. Le joueur aurait déjà appris la leçon vingt minutes plus tôt, et le boss
final ne serait qu'un contrôle de vitesse d'exécution.

### 1.3 Le pilier : le Harvester est un verrou, le Leviathan est un démontage

| | Choir Harvester | Pale Leviathan |
|---|---|---|
| Structure | **cyclique** — trois clés ouvrent une fenêtre, tout repousse | **monotone** — chaque phase arrache une partie du corps, rien ne repousse |
| Ce qui est récompensé | la **vitesse d'enchaînement** (abattre trois bras avant que le premier ne revienne) | l'**endurance et le choix** (tenir quatre phases, décider quoi frapper) |
| Où se lit la progression | sur la jauge du HUD | sur la **silhouette** — à la fin il ne reste qu'un noyau décharné |
| Le corps | blindé, sauf pendant l'iris | jamais un mur : chaque phase a sa cible légitime |

**La règle de conception qui découle du pilier** : *la pièce que le joueur arrache à la phase N
devient la mécanique de la phase N+1.* La coquille brisée découvre la gueule ; la gueule domptée
devient le tunnel ; les épines détachées deviennent l'essaim. Le boss ne « change de motif », il
**se démonte**, et chaque perte a une conséquence physique visible.

C'est aussi ce que raconte la planche : le panneau « noyau fermé », le panneau « vortex », le panneau
« épines en éventail » et le panneau « brisé » sont déjà là, côte à côte. Le design ne va rien
inventer contre elle — il l'exploite.

---

## 2. Vue d'ensemble

| Phase | Nom | Le verbe | Durée visée | Ce que le joueur arrache |
|---|---|---|---|---|
| 1 | **Armor Choir** | BRISER | 65–75 s | les 4 plaques d'armure de la coquille |
| 2 | **Gravitic Maw** | RÉSISTER | 55–65 s | les 3 nœuds gravitiques de la lèvre |
| 3 | **Boarding Swarm** | PRIORISER | 50–60 s | les 4 épines |
| 4 | **Into the Maw** | OSER | 15–25 s | le cœur |

**Total visé : ~3 min 30**, dans la fourchette de la spec §7 (3 à 4 minutes pour le boss final).

### 2.1 La courbe de tension

```
  intensité
     │                                              ╭──╮ phase 4
     │                              ╭───────────╮  ╱    │ (court, total)
     │              ╭───────────╮  ╱             ╲╱     │
     │  ╭────────╮ ╱             ╲╱                     │
     │ ╱          ╲                                     │
     └──────────────────────────────────────────────────▶ temps
       BRISER      RÉSISTER      PRIORISER       OSER
       lisible     étouffant     saturé          vertigineux
```

Chaque transition de phase est un **répit d'une à deux secondes** (la coque se réorganise, le boss ne
tire pas) : c'est là que le joueur respire, voit ce qu'il a cassé, et lit la nouvelle règle.

### 2.2 Le contrat de lisibilité

Trois choses ne doivent jamais manquer, sous peine de rejouer les défauts déjà payés sur le
Harvester :

1. **Toute attaque lourde a un télégraphe qui annonce un point fixe.** Le verrou de cible se fait au
   *début* du réarme, jamais pendant — sinon le coup est imparable
   (`harvester_combat.gd:359-365`, et la règle est inscrite dans `HarvesterTuning.validate()`).
2. **Tirer sur une pièce blindée doit produire quelque chose à l'écran.** Le signal `deflected` de
   `BossController` existe déjà et fait une étincelle blanche + `shield_impact` : sans lui, une
   armure se lit comme un bug.
3. **Il y a toujours une cible légitime.** À aucun moment le joueur ne doit se demander où tirer. Si
   la réponse n'est pas évidente, la phase est ratée.

### 2.3 La jauge du HUD

⚠️ Le HUD n'a qu'un `set_boss_health(ratio)` (`scripts/ui/fighter_hud.gd:339`). Sur le Harvester, il
montre le **noyau**, qui ne bouge que pendant l'iris — le reste du temps la jauge est figée, ce qui
est acceptable pour deux minutes.

Sur quatre phases ce serait une faute : une jauge immobile pendant soixante secondes dit « tu ne fais
rien ». La jauge du Leviathan montre donc les **dégâts cumulés sur l'ensemble des structures**,
plaques et nœuds et épines compris :

```
ratio = 1 − (dégâts infligés à toutes les pièces) / TOTAL_STRUCTURE
```

Elle descend en continu du début à la fin. Les **trois pastilles d'appendice** du bandeau
(`set_boss_limb`) sont réutilisées telles quelles pour montrer les sous-cibles de la phase courante —
elles en portent trois, la phase 1 et la phase 3 en ont quatre : on affiche les **trois encore
debout**, ou on étend le bandeau à quatre (choix d'implémentation, à trancher au moment du code ;
l'extension à quatre est préférable et coûte peu).

---

## 3. Phase 1 — ARMOR CHOIR (le verbe : BRISER)

### 3.1 État de la coque

La coquille en croissant recouvre le noyau, exactement comme sur le panneau principal de la planche.
Quatre plaques d'armure y sont enchâssées, réparties à 90°. **La coquille tourne lentement autour de
l'axe du noyau** : les plaques défilent, l'une après l'autre, face au joueur.

### 3.2 La mécanique

**La fenêtre de tir naît de la rotation, pas d'un minuteur.** Une plaque n'encaisse que lorsqu'elle
est dans l'arc face au joueur (±50° autour de l'axe caméra) ; de l'autre côté, elle est masquée par
le corps et les tirs se réfléchissent (`deflected`).

C'est la différence de nature avec l'iris du Harvester : là-bas, la fenêtre était un **état** que le
joueur provoquait ; ici c'est une **géométrie** qu'il doit lire et anticiper. Il n'attend pas, il
choisit son moment — et comme les plaques sont à 90° avec un arc utile de 100°, **il y a toujours à
peu près une cible disponible** : la phase n'a aucun temps mort.

**Rien ne repousse.** Une plaque tombée est tombée. Le rideau de balles s'allège d'un quart à chaque
fois : le retour est immédiat, physique, et il enseigne au joueur que dans ce combat, casser paie.

### 3.3 Les attaques

| Attaque | Télégraphe | Effet | Cadence |
|---|---|---|---|
| **Chœur d'éventails** | aucun (pression de fond, balles lentes et lisibles) | chaque plaque **encore debout** crache un éventail de 7 balles, vitesse 5, ouverture 60°, décalées entre elles — un rideau qui tourne avec l'orbite | toutes les 2,4 s par plaque |
| **Lance annoncée** | ligne fine et battante du noyau au point verrouillé, 1,8 s (`Beam` en régime télégraphe, déjà écrit) | faisceau de 1,2 s, demi-largeur 0,7, **28 dégâts par contact** | toutes les 7 s |
| **Missiles ciblables** | sifflement + traînée magenta | 3 missiles vitesse 4 qui infléchissent vers le joueur, 22 dégâts au contact — **destructibles au tir** | 2 salves toutes les 6 s |

Les missiles ciblables sont la nouveauté de lecture de la phase : ils apprennent au joueur qu'il peut
*répondre* à un projectile, ce dont il aura besoin en phase 3.

### 3.4 Sortie

Dernière plaque abattue → la coquille se **rétracte en 2 s** (65° de bascule), découvrant le noyau
intact. Le boss ne tire pas pendant la rétraction.

- VFX : `VfxExplosion.Category.HEAVY` au centre + secousse 0,9
- Audio : `boss_phase_shift`
- Bannière : **« COQUILLE BRISEE »** en ivoire, 1,6 s

Le noyau apparaît, magnifique et **toujours invulnérable** : le joueur croit avoir gagné une cible,
il a gagné une phase. C'est le bon moment pour lui mentir une seconde.

---

## 4. Phase 2 — GRAVITIC MAW (le verbe : RÉSISTER)

### 4.1 État de la coque

Le noyau s'ouvre. Les craquelures magenta se creusent en un **vortex violet sombre** — c'est
littéralement le deuxième panneau de gros plan de la planche, celui qui montre l'entonnoir. La lèvre
de la gueule porte trois **nœuds gravitiques** saillants.

### 4.2 La mécanique — l'aspiration

Un champ radial tire le chasseur vers le centre du boss. C'est la première fois du jeu que
**le joueur n'a plus le contrôle total de son vaisseau**.

```
vitesse_aspiration(d) = pull_speed_max × clamp(1 − d / pull_radius, 0, 1)
```

**La menace n'est pas le contact avec la gueule.** C'est de ne plus pouvoir esquiver : le rideau de
balles n'a pas changé, mais la marge de manœuvre a fondu. Le joueur qui jouait à 14 u/s en joue à 7.

> ⚠️ **L'invariant qui rend la phase jouable** : `pull_speed_max` doit rester **strictement
> inférieure** à `PlayerStats.max_speed` (14,0) — sinon le chasseur est aspiré quoi qu'il fasse et la
> phase devient une cinématique. La valeur retenue, **7,0 u/s**, laisse exactement la moitié de la
> mobilité. C'est un `validate()` à écrire, pas un commentaire : c'est le genre de réglage qui a
> l'air raisonnable isolément et rend le jeu injouable une fois combiné.

**Les trois nœuds coupent l'aspiration par tiers.** Chaque nœud abattu retire un tiers de
`pull_speed_max`. Le retour est immédiat et se *sent* dans les doigts : le joueur récupère sa vitesse
morceau par morceau. Un tout-ou-rien aurait été moins bon — ici, chaque victoire partielle paie.

### 4.3 Les débris

Huit à douze blocs de coque traversent l'écran, aspirés en spirale vers la gueule. Ils sont
**indestructibles**, infligent 30 dégâts au contact, et **occultent les balles ennemies** : ce sont à
la fois un danger et la seule couverture de la phase. Le joueur apprend à s'en servir.

### 4.4 Les attaques

| Attaque | Télégraphe | Effet | Cadence |
|---|---|---|---|
| **Pulsations du vortex** | la gueule se contracte visiblement avant | anneau de 14 balles radiales, vitesse 6 | toutes les 3 s |
| **Balayages d'épines** | la pointe s'illumine 0,8 s avant | les épines **encore attachées** tracent un laser court qui balaie 40° | toutes les 5 s, une épine à la fois |

### 4.5 Sortie

Troisième nœud abattu → le vortex s'effondre en 1,5 s, l'aspiration tombe à zéro, **la gueule reste
béante**.

- VFX : implosion (`MEDIUM` inversée) puis `HEAVY`
- Audio : `boss_phase_shift`
- Bannière : **« GUEULE OUVERTE »** en magenta, 1,4 s

---

## 5. Phase 3 — BOARDING SWARM (le verbe : PRIORISER)

### 5.1 État de la coque

**Les quatre épines se détachent du corps** et deviennent des unités autonomes. C'est le moment le
plus spectaculaire de la conception : une pièce qui faisait partie de la silhouette du boss depuis
trois minutes s'en arrache et vient chercher le joueur.

Le corps, lui, n'est plus qu'un tronc et une gueule ouverte.

### 5.2 La mécanique — le dilemme

Le noyau est **enfin touchable en permanence**. Mais quatre épines et un flux de transports occupent
l'écran, et l'une des épines a pour seul travail de se placer devant le noyau.

Le joueur doit choisir à chaque seconde : taper le boss, ou nettoyer. Il n'y a pas de bonne réponse
absolue — seulement une bonne réponse à l'instant t. C'est le verbe de la phase.

### 5.3 Les quatre épines

| Épine | Rôle | Comportement | PV |
|---|---|---|---|
| `Spike_01` | **Fonceuse** | charge télégraphiée (1,0 s de verrou, ligne fine), traverse l'écran à 20 u/s, 30 dégâts au contact | 1 500 |
| `Spike_02` | **Tireuse** | se poste à distance haute, salves ajustées de 3 balles toutes les 1,2 s | 1 500 |
| `Spike_03` | **Bloqueuse** | s'interpose entre le joueur et le noyau, absorbe les tirs — **c'est elle qui crée le dilemme** | 1 500 |
| `Spike_04` | **Escorte** | orbite le noyau à 3 u, tir rapproché rapide | 1 500 |

Hitbox 0,9 chacune. Elles ne repoussent pas.

### 5.4 Les transports d'abordage

Toutes les 8 s, deux transports se détachent du corps et filent vers le bas de l'écran.

⚠️ **ADR-0010 a supprimé l'intégrité de forteresse** : il n'y a plus rien à protéger derrière le
joueur, et une jauge abstraite serait un mensonge. La sanction est donc **matérielle** : un transport
qui sort du champ **revient six secondes plus tard par le bas, en escorte armée**, et reste. Laisser
passer, c'est augmenter la pression pour le reste de la phase. Le joueur comprend la règle en une
fois, sans qu'aucun texte ne la lui dise.

Réutiliser les coques existantes (`scenes/enemies/needle_scout_*.tscn`, `crescent_interceptor.tscn`)
plutôt que d'en modéliser une : le budget de production va à la coque du boss.

### 5.5 Sortie

Quatre épines détruites → le boss est **nu**. Sa silhouette a perdu les trois quarts de sa masse ;
c'est le panneau « brisé » de la planche, atteint par le jeu et non par une cinématique.

- VFX : quatre `MEDIUM` en chaîne puis un `HEAVY`
- Audio : `boss_phase_shift`, puis bascule musicale sur `final_charge`
- Bannière : **« STRUCTURE DECHARNEE »** en ivoire, 1,8 s

---

## 6. Phase 4 — INTO THE MAW (le verbe : OSER)

### 6.1 Le renversement

L'aspiration reprend, mais cette fois **au-delà de la vitesse du chasseur** (16 u/s contre 14). On ne
résiste plus. La règle de la phase 2 est explicitement cassée, et c'est le sujet de la phase : le
joueur a passé une minute à lutter contre cette force, il doit maintenant l'accepter.

Le HUD l'annonce sans ambiguïté — bannière **« ENTREZ »**, en magenta, 2 s. Il n'y a aucune autre
option : le boss n'a plus de point faible extérieur.

### 6.2 Le tunnel

La gueule devient un puits vertical. Cinq anneaux internes (`Ring_01..05`), chacun percé d'une
**ouverture qui tourne** à vitesse différente. Le joueur, aspiré vers le fond, doit aligner sa
position latérale sur l'ouverture de chaque anneau au moment où il le franchit.

- Toucher un anneau : **35 dégâts** + rejet vers l'arrière de 3 u (on perd du terrain, on ne meurt pas)
- Au fond : le **cœur** (`Heart`), 2 600 PV, exposé, sans aucune protection. Tir libre.

### 6.3 Le compte à rebours

**La gueule se referme 12 s après l'entrée.** Deux issues :

- **Le cœur tombe** → le boss meurt. Explosions en chaîne de l'intérieur vers l'extérieur, `helios_lance`,
  puis la Citadelle arrive → `DOCKING` → `VICTORY` (arc ADR-0010 inchangé).
- **Le cœur tient** → à 10 s, l'aspiration s'**inverse** en expulsion pendant 2 s : c'est la fenêtre
  de sortie, et elle est généreuse parce qu'elle est la seule. Le joueur éjecté regarde la gueule se
  refermer, le boss recharge 8 s, puis rouvre. On recommence.
- **Le joueur est encore dedans à la fermeture** → mort. Une vie.

12 s à 420 dps = 5 040 dégâts potentiels pour un cœur à 2 600 PV : **une descente propre suffit**.
Une descente où l'on touche deux anneaux et où l'on tâtonne n'y arrive pas. C'est exactement le
niveau d'exigence voulu pour un dernier geste : difficile, jamais injuste, refaisable.

### 6.4 En cas de mort

Spec §12.8, conservée : **reprise au début de la phase en cours**, boss remis aux PV de début de
phase, pièces de la phase restaurées. Sans cela, la destruction définitive des pièces obligerait à
refaire trois minutes pour une erreur de dix secondes — la mécanique du démontage se retournerait
contre le joueur.

---

## 7. Chiffres et dimensionnement

### 7.1 La règle qui donne les points de vie

Comme pour `HarvesterTuning`, aucune valeur ne doit être posée « à l'oreille ». La règle :

```
durée_de_phase = PV_de_la_phase / (reference_dps × occupation)
```

- `reference_dps = 420` — la cadence soutenue du joueur à puissance 3, **la même hypothèse que le
  mini-boss** (`resources/data/harvester_tuning.gd:46`). Ce n'est pas un réglage de boss, c'est
  l'hypothèse de dimensionnement, et elle doit être écrite noir sur blanc pour être vérifiable.
- `occupation` — la part du temps où le joueur peut réellement placer ses tirs sur une cible
  légitime. Elle varie par phase, et c'est le **vrai levier de conception** : une phase où l'on
  esquive plus qu'on ne tire a une occupation basse, donc moins de PV pour la même durée.

### 7.2 Le tableau

| Phase | Cibles | PV unitaires | PV de phase | Occupation | Durée calculée |
|---|---|---|---|---|---|
| 1 — Armor Choir | 4 plaques | 3 200 | 12 800 | 0,45 | **67,7 s** |
| 2 — Gravitic Maw | 3 nœuds | 2 800 | 8 400 | 0,35 | **57,1 s** |
| 3 — Boarding Swarm | 4 épines + noyau | 1 500 / 3 200 | 9 200 | 0,40 | **54,8 s** |
| 4 — Into the Maw | le cœur | 2 600 | 2 600 | 0,80 | **7,7 s** de tir utile, dans une fenêtre de 12 s |
| | | | **33 000** | | **~3 min 08** de combat net |

Plus les transitions (≈ 7 s cumulées) et les temps morts d'entrée : **~3 min 20 à 3 min 40**.

Pour comparaison, le Choir Harvester totalise environ 11 500 dégâts sur trois cycles pour un combat
de deux minutes. Le boss final demande **près de trois fois plus**, sur quatre règles différentes.

### 7.3 Les invariants à faire porter par `validate()`

Ce sont eux qui empêchent un réglage « raisonnable pièce par pièce » de produire un combat
impossible. Chacun se vérifie en une ligne, et chacun corrige une panne silencieuse.

| Invariant | Pourquoi |
|---|---|
| `pull_speed_max_phase2 < PlayerStats.max_speed` (14,0), et idéalement `≤ 0,6 ×` | au-delà, le chasseur est aspiré quoi qu'il fasse : la phase 2 devient une cinématique |
| `pull_speed_max_phase4 > PlayerStats.max_speed` | c'est le sujet de la phase 4 : si on peut résister, il n'y a plus de course |
| `arc_touchable_plaque / 360 × periode_orbite ≥ 2,0 s` | une fenêtre plus courte que deux secondes ne se joue pas — c'est la constante `MIN_WINDOW` du Harvester, transposée à une géométrie |
| `PV_coeur / reference_dps ≤ 0,7 × duree_gueule_ouverte` | il doit rester de la marge pour l'erreur : un cœur qu'on ne peut abattre qu'en jouant parfaitement rend la phase 4 aléatoire |
| `∀ attaque lourde : windup > 0` | le télégraphe **est** la règle du duel. Cet invariant existe déjà mot pour mot dans `HarvesterTuning.validate()` |
| `somme des PV de phase == TOTAL_STRUCTURE` | sinon la jauge du HUD ment sur la progression |

### 7.4 Réglages détaillés (proposition de `LeviathanTuning`)

```
[Phase 1 — Armor Choir]
plate_health            = 3200.0     PV d'une plaque
plate_count             = 4
shell_orbit_period      = 12.0   s   un tour complet de la coquille
plate_arc_deg           = 100.0  °   arc face joueur où la plaque encaisse (±50°)
plate_hitbox_radius     = 1.30       généreux : elle bouge et elle est grosse
shell_retract_time      = 2.0    s   la rétraction de fin de phase
fan_interval            = 2.4    s   par plaque encore debout
fan_bullets             = 7
fan_spread_deg          = 60.0   °
fan_speed               = 5.0
lance_windup_time       = 1.8    s   ⚠️ le télégraphe
lance_beam_time         = 1.2    s
lance_half_width        = 0.70
lance_damage            = 28.0       par CONTACT (i-frames de 1,2 s, cf. Harvester)
lance_interval          = 7.0    s
missile_salvo_interval  = 6.0    s
missile_count           = 3
missile_speed           = 4.0
missile_turn_rate       = 1.4    rad/s
missile_health          = 40.0       ciblable : une salve du joueur suffit
missile_damage          = 22.0

[Phase 2 — Gravitic Maw]
node_health             = 2800.0
node_count              = 3
node_hitbox_radius      = 1.00
pull_radius             = 16.0       portée du champ
pull_speed_max          = 7.0    u/s ⚠️ < max_speed du joueur (14,0)
pull_relief_per_node    = 0.3333     chaque nœud abattu retire un tiers
debris_count            = 10
debris_speed            = 6.0
debris_damage           = 30.0
maw_pulse_interval      = 3.0    s
maw_pulse_bullets       = 14
spike_sweep_windup      = 0.8    s
spike_sweep_arc_deg     = 40.0   °
spike_sweep_interval    = 5.0    s

[Phase 3 — Boarding Swarm]
spike_health            = 1500.0
spike_hitbox_radius     = 0.90
core_health             = 3200.0
charger_windup          = 1.0    s   ⚠️ le télégraphe de la fonceuse
charger_speed           = 20.0   u/s
charger_damage          = 30.0
gunner_interval         = 1.2    s
blocker_offset          = 2.5    u   distance à laquelle elle s'interpose
escort_orbit_radius     = 3.0    u
transport_interval      = 8.0    s
transport_count         = 2
transport_return_delay  = 6.0    s   il revient en escorte armée

[Phase 4 — Into the Maw]
heart_health            = 2600.0
maw_open_time           = 12.0   s   le compte à rebours
maw_reopen_delay        = 8.0    s   après un échec
eject_window            = 2.0    s   l'aspiration s'inverse — la seule sortie
pull_speed_max_final    = 16.0   u/s ⚠️ > max_speed : on n'y résiste pas
ring_count              = 5
ring_gap_deg            = 70.0   °   l'ouverture de chaque anneau
ring_spin_base          = 0.5    tr/s (chaque anneau a un multiplicateur distinct)
ring_damage             = 35.0
ring_knockback          = 3.0    u
```

---

## 8. Architecture visée

### 8.1 Composition, comme le Harvester

`BossController` **ne bouge pas**. Il garde ce qui est générique : entrée, déplacement, roulis et
tangage déduits de la vitesse, PV, signaux HUD, mort, prise de main sur le déplacement
(`drive_toward` / `release_drive`). Il sert déjà deux boss ; il en servira deux après.

Un module `scripts/bosses/leviathan_combat.gd`, **nœud enfant de la scène**, lui prend exactement ce
que le module du Harvester lui prend :

- l'armement (`external_attacks = true`, déclaré dans le `.tscn` et non seulement posé par le module
  — l'ordre des `_ready()` est un équilibre qu'un refactor casserait sans bruit) ;
- la vulnérabilité du corps (`vulnerable`).

Fichiers pressentis :

| Fichier | Rôle |
|---|---|
| `scripts/bosses/leviathan_combat.gd` | la machine à phases et l'orchestration |
| `scripts/bosses/leviathan_plate.gd` | une plaque : PV, état, arc touchable (`RefCounted`) |
| `scripts/bosses/leviathan_spike.gd` | une épine : PV, comportement une fois détachée (`RefCounted` tant qu'attachée) |
| `scripts/bosses/maw_tunnel.gd` | la phase 4 : anneaux, compte à rebours, cœur |
| `resources/data/leviathan_tuning.gd` | tous les réglages + `validate()` (§7.3) |
| `scripts/fx/leviathan_detail.gd` | le jeu de textures **dédié** au boss, sur le modèle de `citadel_detail.gd` (ADR-0013) — voir §9.6 et l'annexe B |

### 8.2 Les trois primitives nouvelles

Chacune est isolée et **testable headless**, sans arbre ni rendu — c'est la condition pour qu'une
mécanique qui demande trois minutes de jeu à atteindre soit vérifiable.

**1. Champ d'aspiration** — `scripts/gameplay/gravity_well.gd`, fonctions statiques pures :

```gdscript
static func pull_at(position: Vector2, center: Vector2, radius: float,
        speed_max: float) -> Vector2
```

Appliquée à la vélocité du joueur. Sur le modèle de `BossMovement` et de `Beam.hits()` : pas de
nœud, pas d'état, testable directement. Le joueur expose déjà
`integrate_velocity()` en statique (`player_fighter_controller.gd:361`) — l'aspiration s'y compose.

**2. Projectile ennemi ciblable** — le missile de la phase 1. ⚠️ Point à vérifier à
l'implémentation : `BulletTarget.make(Team, radius, callback)` existe, mais il faut confirmer que
`BulletManager._resolve_hits` accepte qu'une cible d'équipe alliée soit portée par un objet **du camp
ennemi**. Si le gestionnaire ne le permet pas tel quel, l'extension est petite et se fait là, pas
dans le boss.

**3. Détachement d'une pièce de coque** — l'épine qui devient une unité. Reparenter le `Node3D` de la
coque sous un nœud d'unité autonome en **conservant la transformation monde**. Pièges connus :
`extra_cull_margin` est posé récursivement par `_pad_cull_margin` (`boss_controller.gd:110`) et doit
suivre la pièce ; et une cible laissée enregistrée dans le `BulletManager` sur une pièce détachée
serait le « mur invisible » exact contre lequel `HarvesterCombat.release()` a été écrit.

### 8.3 Les pièges déjà payés — à ne pas repayer

- **Ordre d'enregistrement des cibles.** `BulletManager._resolve_hits` parcourt les cibles dans
  l'ordre d'enregistrement et **consomme** la balle sur la première qui la réclame. Les sous-cibles
  (plaques, nœuds, épines) doivent s'enregistrer **avant** la cible de corps, via le signal `began`
  émis exprès avant (`boss_controller.gd:131-141`). Dans l'autre sens, un tir ajusté sur une plaque
  serait absorbé par le corps.
- **Un seul écrivain par axe.** Une pièce est tour à tour orientée par son animation et par sa
  destruction : la composition se fait à **un seul endroit**. Le module pose, les pièces disent
  seulement où elles en sont (`harvester_limb.gd`, en-tête).
- **`RefCounted` plutôt que `Node`** pour les sous-pièces tant qu'elles n'ont besoin ni d'arbre, ni
  de `_process`, ni de signaux. Elles deviennent instanciables à la main en test.
- **Zéro allocation dans `tick()`.** L'iris du Harvester a coûté cinq `Basis` et cinq
  lire-modifier-écrire sur `.transform` par image **pendant tout le combat** avant qu'on ne le pose
  qu'en cas de mouvement réel (`harvester_combat.gd:280-288`). Sur un boss à quatre phases et une
  vingtaine de pièces mobiles, la même erreur coûte vingt fois plus.
- **Hook de vérification.** Le Harvester a `++ --harvester-window` pour atteindre sa fenêtre
  instantanément (ADR-0006 : un écran qu'on n'atteint qu'en fin d'arc ne se **regarde** jamais). Le
  Leviathan en a besoin d'un par phase : `--leviathan-phase 1..4`.

---

## 9. Spécification 3D

### 9.1 Le défaut à corriger d'abord

`tools/blender/build_pale_leviathan.py` livre bien `Core`, `Shell_Crescent` et `Spike_01..04` comme
objets séparés — mais il ne contient **aucun appel à `ak.moving_part()`** (0 occurrence, contre 10
dans `build_choir_harvester.py`). Chaque pièce a donc son origine au centre du modèle : la faire
tourner la fait pivoter **autour du boss**, pas autour de sa charnière.

C'est mot pour mot le défaut que BRIEF-0039 a corrigé sur le mini-boss. La coque actuelle est
inanimable, et **aucune des quatre phases décrites ici n'est réalisable dessus**. La reforge du
script est donc un préalable, pas une amélioration.

### 9.2 Dimensions — élargissement demandé

| | Actuel | Proposé |
|---|---|---|
| Largeur (Godot X) | 7,02 m | **11,0 m** |
| Longueur (Godot Z) | 8,77 m | **14,0 m** |
| Hauteur max (Godot Y) | 2,50 m | **3,20 m** |
| Budget triangles | 25 000 (contrat du script) | **40 000** |

Le plan de jeu fait 28 × 16 unités (`GameplayPlane.BOUNDS`). À 14 m de long, le boss en occupe la
**quasi-totalité de la profondeur utile** : il écrase l'écran, ce qu'un boss final doit faire et que
7 × 8,77 ne faisait pas — c'était à peine 25 % de plus que le mini-boss (4,55 × 7,00).

**Le budget de triangles ne pose aucun problème** : ADR-0011 a relevé le plafond de la classe *boss*
de 25 000 à **90 000**, mesure GPU à l'appui. Le `tri_budget = 25_000` que déclare aujourd'hui
`build_pale_leviathan.py` n'est que le contrat que ce script s'impose à lui-même ; le porter à
40 000 reste très en deçà du plafond et se fait dans le script, sans décision à prendre. ADR-0011:110
demande d'ailleurs explicitement que les contrats des scripts existants soient relus.

> ⚠️ **L'élargissement des dimensions, lui, demande un ADR.** Le tableau X/Z d'ADR-0008 (lignes
> 80-85) est normatif, et ADR-0011 le **réaffirme expressément** en refusant d'y toucher : « c'est le
> contrat de gameplay : hitbox, télégraphes et lisibilité en dépendent » (ADR-0011:96-97). Passer de
> 7,02 × 8,77 à 11,0 × 14,0 est donc une décision à acter avant toute reforge, pas un réglage.

### 9.3 Contrat de noms — non négociable

Le code sera écrit contre cette liste, comme pour le Harvester. Un nom qui diverge casse
l'intégration en silence.

| Nœud | Nature | Parent | Pivot (repère d'auteur) |
|---|---|---|---|
| `Body` | maillage porteur (`hull`) | — | il porte à lui seul l'étendue longitudinale (cf. en-tête du script actuel) |
| `Shell_Ring` | `moving_part`, racine | — | **axe du noyau** — porte l'orbite, et rien d'autre |
| `Shell_Crescent` | `moving_part` | `Shell_Ring` | charnière arrière — porte la bascule de fin de phase 1 (⚠️ §11.4 : la planche la fait **éclater** plutôt que se rétracter) |
| `Plate_01`..`Plate_04` | `moving_part` | `Shell_Crescent` | leur charnière radiale |
| `Core` | `moving_part`, racine | — | centre du noyau |
| `Maw_Lip` | `moving_part` | `Core` | lèvre de la gueule |
| `Node_01`..`Node_03` | `moving_part` | `Maw_Lip` | leur embase |
| `Ring_01`..`Ring_05` | `moving_part` | `Core` | axe du tunnel, échelonnés en profondeur |
| `Heart` | statique | `Core` | — |
| `Spike_01`..`Spike_04` | `moving_part`, racine | — | épaule — **détachables au runtime** |
| `Spike_0X_Mid` | `moving_part` | `Spike_0X` | coude |
| `Spike_0X_Tip` | `moving_part` | `Spike_0X_Mid` | pointe |

⚠️ **Trois niveaux pour la coquille, et c'est délibéré.** `Shell_Ring` porte l'orbite,
`Shell_Crescent` la rétraction, `Plate_0X` la chute. Empiler deux de ces mouvements sur le même nœud
(`rotation.y` pour l'un, `rotation.x` pour l'autre) marche jusqu'au jour où les deux sont actifs
ensemble — et ce jour-là, la composition d'Euler produit une pose fausse que personne ne sait
relire. Un axe, un nœud, un écrivain.

**Points d'attache** : `Core_Center`, `Maw_Center`, `Tunnel_End`, `Muzzle_C`, `Muzzle_L`, `Muzzle_R`,
`Muzzle_Plate_01..04`, `Muzzle_Spike_01..04`.

Les anciens `Muzzle_L` / `Muzzle_R` / `Muzzle_C` de `required_attach_points` sont **conservés** (le
boss générique les lit encore si `external_attacks` retombe à faux) ; les nouveaux s'y ajoutent. Le
`HullContract` est à mettre à jour dans le même geste, sinon l'auto-validation refuse l'export.

### 9.4 Débattements exigés par le gameplay

Ce sont les angles que le code appliquera. Le modèle doit les encaisser **avec de la marge**.

| Pièce | Mouvement | Amplitude |
|---|---|---|
| `Shell_Ring` | orbite des plaques | **360° continu** autour de l'axe du noyau |
| `Shell_Crescent` | bascule de fin de phase 1 | **0° → 65°** — ⚠️ §11.4 : à remplacer par un **état détruit** (la coquille éclate en débris), le débattement n'est plus qu'un repli d'amorce |
| `Plate_01..04` | chute après destruction | **0° → −80°** |
| `Core` | rotation lente d'ambiance | **360° continu** |
| `Maw_Lip` | ouverture de la gueule | **0° → 90°** |
| `Node_01..03` | rétraction à la destruction | **0° → −60°** |
| `Ring_01..05` | rotation de l'ouverture | **360° continu**, vitesses distinctes |
| `Spike_01..04` | pointage avant détachement | **±40°** |
| `Spike_0X_Mid` / `_Tip` | flexion | **±25°** chacun |

> ⚠️ **Le dégagement — la leçon la plus chère du projet.** Le Specter-9 a coûté **quatre briefs**
> (0033 → 0036) sur ce seul point : un marquage posé à cheval sur une charnière a fait tomber le
> dégagement d'un volet de 18,5° à **2,8°**, et le contrat a validé sans un mot parce que la boîte
> englobante *au repos* était parfaite. Un défaut d'animation ne se voit pas sur une pose fixe.
>
> Conséquence : **chaque pièce mobile doit être mesurée à fond de course**, et la marge minimale
> rapportée dans un tableau. Une marge nulle ou négative est un défaut bloquant. Corollaire hérité :
> poser le détail **en fraction de corde, jamais en coordonnée absolue**
> (`.claude/resources/pratique-detail-en-fraction-de-corde.md`).

Deux vérifications **par rendu, pas par calcul** :

- à `Maw_Lip` 90°, le tunnel et `Heart` sont **entièrement dégagés en vue de dessus** — c'est l'angle
  de la caméra de jeu ;
- à `Plate_0X` −80°, les quatre plaques tombées ne se mordent ni entre elles ni avec la coquille.

### 9.5 Palette et matériaux

Palette **Null Choir** de la charte §3, inchangée : anthracite, violet sombre, ivoire froid, magenta
en émissif, vert maladif en usage très limité. Les sept matériaux normalisés du kit
(`ak.MATERIAL_ORDER`).

Le vortex doit lire comme une **profondeur**, pas comme un disque noir : la planche le montre bien —
un entonnoir violet sombre avec des spirales magenta qui s'enfoncent. C'est un shader, pas de la
géométrie.

⚠️ Le cyan et le corail sont **réservés au gameplay** (DA §6) : aucun décor ni aucune coque ne les
emploie, sous peine de voler leur lisibilité aux projectiles.

### 9.6 Textures — le blocage à lever d'abord

ADR-0013 a **levé tous les interdits de texture** : jeux dédiés à une unité, relief, couleur,
décalques. Le Leviathan a donc droit au sien, comme la citadelle.

> ⚠️ **Mais il ne peut en recevoir aucune aujourd'hui.** `ak.box_project_uv()` n'est appelé que par
> `build_specter_9.py`, `build_aegis_citadel.py`, `build_citadel_turret.py` et
> `build_citadel_beacon.py`. **Aucun script de boss ne le fait** — ni le Leviathan, ni le Harvester.
> Sans UV ni tangentes, une texture n'a nulle part où s'appliquer. C'est mot pour mot le symptôme
> qu'ADR-0013 relève pour la citadelle avant sa reforge.
>
> La reforge du §9.1 doit donc appeler `ak.box_project_uv(obj, TEXELS_PER_METER)` sur chaque
> maillage, **dans le même geste que les `moving_part`**. Sinon toute l'annexe B est produite pour
> rien.

**Densité proposée : `TEXELS_PER_METER = 0.18`**, soit **une tuile pour 5,5 m**. Repères mesurés
ailleurs dans le projet : la citadelle est à 0,12 (une tuile pour 8,33 m, une plaque de blindage lit
alors ~1,4 m) et le Specter-9 à 4,0 (une tuile pour 25 cm). Sur une coque de 14 m, 0,18 donne des
écailles d'environ 1,1 m — l'échelle que montre la planche.

⚠️ **À confirmer au rendu, pas au calcul.** La citadelle a dû doubler la taille de ses greebles après
mesure : à la densité du blindage, chaque élément faisait 28 cm, soit **deux pixels** une fois passé
le post-process rétro à 960×540, et les ponts lisaient comme de la saleté
(`scripts/fx/citadel_detail.gd:34-40`). C'est la leçon d'ADR-0011 : le détail fin se noie.

Le jeu de textures est décrit prompt par prompt dans **l'annexe B**.

---

## 10. Ce qui reste à faire, et dans quel ordre

| # | Travail | Qui | Bloquant pour |
|---|---|---|---|
| 1 | **ADR** amendant le tableau de dimensions X/Z (ADR-0008:80-85, réaffirmé par ADR-0011:96) | concepteur | tout le reste |
| 2 | **ADR** actant la refonte du boss final (ce document en devient la référence) | concepteur | — |
| 3 | **BRIEF** — planches de concept annotées (**annexe A**, 3 prompts) | asset-forge | la reforge de coque |
| 4 | **BRIEF** — reforge de `build_pale_leviathan.py` : `moving_part`, contrat §9.3, dégagements §9.4, **et `box_project_uv`** (§9.6) | asset-forge | l'implémentation **et** les textures |
| 5 | **BRIEF** — jeu de textures dédié (**annexe B**, 5 prompts) + `scripts/fx/leviathan_detail.gd` | asset-forge puis concepteur | le rendu final |
| 6 | **BRIEF** — décor et VFX de l'arène (**annexe C**, 3 prompts) | asset-forge puis concepteur | le rendu final |
| 7 | **BRIEF** — SFX : aspiration du vortex, détachement d'épine, fermeture de gueule | asset-forge | le polish |
| 8 | Primitives §8.2 (aspiration, projectile ciblable, détachement), **avec leurs tests** | concepteur | le module |
| 9 | `LeviathanTuning` + `validate()` (§7.3) | concepteur | le module |
| 10 | `leviathan_combat.gd` phase par phase, hooks `--leviathan-phase N` | concepteur | — |

⚠️ **L'ordre 4 avant 5-6 n'est pas négociable** : sans les UV posées par la reforge, aucune des
textures de l'annexe B n'a de surface où s'appliquer (§9.6).

**Écrivain unique** : les briefs 3-4-5 et les travaux 6-7-8 ne se chevauchent pas dans les mêmes
fichiers. La forge ne touche ni au GDScript, ni aux scènes, ni aux Resources
(`.claude/resources/pratique-ecrivain-unique.md`).

---

## 11. Retour des images — ce que la livraison a donné

*Section écrite après réception : les 11 images ont été livrées, regardées et mesurées. Elle vaut
compte-rendu de recette — les prompts des annexes restent tels quels, ils ont fait leur travail.*

### 11.1 Recette

| Contrôle | Résultat |
|---|---|
| Présence | **11/11**, aux chemins exacts |
| Palette des 3 cartes couleur | **0 % de cyan, de corail ou d'orange**, sur les trois. `core_albedo` : 61 % violet / 39 % magenta. `maw_vortex` : 58 / 42. `nebula` : 85 / 15. Le verrou DA §6 tient |
| Grisé des 5 cartes N&B | chroma ≤ 0,002 — très en dessous du seuil d'alerte 0,08 de `derive_maps.load_height()` |
| Masque de craquelures | franchement bimodal, comme exigé |
| Échelle des motifs | mesurée par **autocorrélation** du profil moyen, pas à l'œil |
| Détourage alpha | vortex et nébuleuse : aucun résidu sur la couleur d'espace de la scène |

### 11.2 Échelle des motifs — mesurée

| Tuile | Période mesurée | Demandée | Verdict |
|---|---|---|---|
| `leviathan_scales` | **0,99 m** | 1,10 m | conforme |
| `maw_tunnel_wall` | **0,82 m** | 0,80 m | conforme |
| `leviathan_greebles` | conduits de **55 à 70 cm** | 25 cm | plus **gros** que demandé — du bon côté, le détail fin se noie à 960×540 |

> ⚠️ **Méthode.** L'autocorrélation du profil moyen mesure la **période dominante** ; sur les
> greebles elle rend 2,71 m, qui est la volute macro et non le calibre du conduit. Une mesure par
> longueur de plage a été tentée pour y remédier : elle rend 1 cm sur les écailles, dont on sait
> qu'elles font 1 m. **Témoin faux, mesure jetée** — le calibre des greebles est un relevé à l'œil
> sur la source en pleine résolution, et il est annoncé comme tel.

### 11.3 Tuilage — le point qui a coûté du travail

Aucune tuile n'est arrivée seamless. Mesures natives (`derive-maps.py --check-tiling`, seuil 4 %) et
rattrapage retenu :

| Tuile | X natif | Y natif | Fondu retenu | Verdict après examen |
|---|---|---|---|---|
| `leviathan_damage_mask` | 1,8 % | 2,2 % | **aucun** | seul livrable seamless d'origine |
| `leviathan_core_albedo` | 3,0 % | 3,0 % | **aucun** | passe |
| `leviathan_scales_height` | 4,2 % | 5,3 % | **48 px** | bande invisible |
| `leviathan_cracks_mask` | 6,6 % | 3,4 % | **48 px** | le réseau irrégulier absorbe la bande |
| `maw_tunnel_wall_height` | 4,5 % | **11,9 %** | **48 px** | passe — voir la réserve ci-dessous |
| `leviathan_greebles_height` | 8,3 % | 10,3 % | **40 px** | passe — voir la réserve ci-dessous |

> ⚠️ **Après `--fix-tiling`, le chiffre de tuilage ne veut plus rien dire** : le fondu force le
> raccord à 0,0 % par construction. Le seul critère est **l'œil sur la planche contact 2×2**. C'est
> pour ça que l'outil imprime « REGARDER le résultat » plutôt qu'un verdict.

**Deux réserves consignées**, à lever en jeu une fois la coque munie de ses UV :

1. **`greebles`** — la bande miroir est *détectable* sur une planche contact plate quand on la
   cherche. Pari retenu : projetée à 0,5 tuile sur une coque courbe puis écrasée à 960×540, elle ne
   lira pas. Si elle lit, régénérer plutôt qu'élargir le fondu.
2. **`maw_tunnel_wall`** — le motif est **nativement symétrique gauche-droite** ; le brief demandait
   des anneaux irréguliers. Ce n'est pas un défaut de tuilage (les rendus à 48 et 96 px sont
   identiques), c'est un trait de l'image. Acceptable pour un tunnel traversé en douze secondes, à
   revoir si la répétition saute aux yeux.

### 11.4 Les planches ont tranché des points de conception

L'illustration est meilleure que la spec sur plusieurs points. **Le §9.3 s'aligne sur elle**, pas
l'inverse.

| Point | Ce que disait §9 | Ce que montre la planche | Décision |
|---|---|---|---|
| Fin de phase 1 | la coquille se **rétracte** (0° → 65°) | elle **éclate en débris** (panneau CORE EXPOSED) | **suivre la planche** — plus spectaculaire, et parfaitement cohérent avec « rien ne repousse ». `Shell_Crescent` n'a donc plus besoin d'un débattement de rétraction : il lui faut un état *détruit* |
| Ouverture des anneaux | non nommée | **OFFSET GATE**, décalée d'un anneau au suivant | **adopter le terme** : il nomme la mécanique de la phase 4, et un nom rend une règle enseignable |
| `Maw_Lip` | ce nom | légendé **OUTER RIM** | garder `Maw_Lip` dans le code ; équivalence notée ici |
| Anneaux internes | `Ring_01..05` (5) | **6** dans l'éclaté | à trancher à la reforge. 6 allonge le puits d'un temps ; l'invariant §7.3 sur la durée d'ouverture tranchera |
| Nœuds gravitiques | 3, enfants de `Maw_Lip` | 2 visibles, à **base articulée** | 3 confirmé : une projection de profil en masque un. La base articulée confirme le parentage |
| Segments d'épine | `Base / Mid / Tip` | 3ᵉ segment légendé **SPIKE MID** | erreur de légende. Garder `Tip` |
| Cotes des orthos | 11 m large × 14 m long | les 4 vues cotées « 14.0 m » | erreur de légende : la vue de face montre les 11 m |

---

# ANNEXES — prompts de génération d'images

Tout se génère **hors du dépôt**, chez l'opérateur. Chaque bloc de prompt se colle tel quel : il ne
suppose aucun contexte.

| Annexe | Ce que c'est | Ce que ça sert | Où ça finit |
|---|---|---|---|
| **A** — 3 planches | documents de travail **annotés** | concevoir et modeler | `assets/reference/concepts/` (jamais chargé) |
| **B** — 5 textures | 4 hauteurs/masques N&B + 1 albédo couleur | le rendu de la coque en jeu | `assets/source/textures/leviathan/` → `assets/imported/textures/leviathan/` |
| **C** — 3 décors/VFX | images peintes détourées | l'arène du combat final | `assets/source/backgrounds|vfx/` → `assets/imported/…` |

### Ce qu'un générateur ne sait pas faire — et qu'on ne lui demande donc jamais

Ces trois pièges ont **déjà été payés** par le projet ; ils sont inscrits dans `/asset-image` et dans
l'en-tête de `tools/derive-maps.py`.

| Ce qu'on serait tenté de demander | Ce qui arrive | Ce qu'on demande à la place |
|---|---|---|
| « une normal map » | une image violette **qui y ressemble**, aux gradients faux — et qui a l'air correcte | une **hauteur en niveaux de gris** (clair = saillant). `tools/derive-maps.py` en dérive normale, rugosité, AO et carte de multiplication |
| « fond transparent, PNG alpha » | un **damier peint** dans une image RGB opaque | un **fond noir pur** (objet lumineux) ou **uni très clair** (objet opaque), l'alpha se reconstruit ensuite |
| « seamless, sans couture » | souvent une couture quand même, invisible sur l'image seule | on demande le seamless **et on le mesure** : `derive-maps.py --check-tiling` |

Corollaire : **une texture PBR se génère en une seule carte**, pas en quatre. Demander quatre cartes
« cohérentes entre elles » donne quatre images qui ne le sont pas.

Deux règles de plus, propres à ce boss :

- **Un émissif ne reçoit pas la lumière.** Les craquelures magenta du noyau ne sont donc **pas** un
  relief : c'est un **masque**. Lui demander une hauteur ne produirait rien de visible — c'est
  exactement ce qui a fait lire le noyau de la citadelle comme « une goutte blanche uniforme »
  (ADR-0013).
- **Le détail fin se noie** dans le post-process rétro (960×540 + scanlines). Chaque prompt dit donc
  l'**échelle réelle** du motif, et on vise gros plutôt que fin.

### La résolution — demander 2048 est un mensonge

Le générateur d'images de ChatGPT ne rend **pas** de 2048 × 2048. Ses formats natifs sont
**1024 × 1024**, **1536 × 1024** et **1024 × 1536**. Lui demander 2048, c'est recevoir un 1024
agrandi : du détail **inventé par l'interpolation**, jamais du détail supplémentaire.

Le dépôt le confirme, fichier par fichier — toutes les images réellement rendues par le générateur y
sont dans un format natif :

| Fichier | Taille réelle |
|---|---|
| `citadel_panels_height.png`, `citadel_greebles_height.png`, `crystal_facets_height.png` | **1254 × 1254** |
| `nebula_monument_a.png`, `nebula_monument_b.png` | **1536 × 1024** |
| `planet_hero.png`, `galaxy_distant.png` | **1254 × 1254** |

Les trois seuls fichiers en 2048 du dépôt (`assets/source/textures/hull/*_seamless_2048.png`)
datent d'avant ce pipeline et ne viennent pas de cette route.

**Et ça n'a aucune importance.** La citadelle tourne en jeu sur des cartes en 1254, et le rendu final
passe par le post-process rétro à **960 × 540** : une texture en 1024 sur une tuile de 5,5 m donne
186 pixels par mètre, soit largement plus que ce que l'écran peut montrer. Viser 2048 coûte du poids
et du temps de génération pour un détail que le filtre rétro efface (c'est la leçon d'ADR-0011 : le
détail fin se noie).

**Donc : on demande le format natif, et on ne redimensionne pas.** Les carrés en 1024 × 1024, les
planches en 1536 × 1024.

### La couleur — délibérée sur les cartes de relief, pas ailleurs

Question légitime, et la réponse n'est pas la même pour tous les livrables.

**Une hauteur et un masque sont gris par définition**, pas par goût : ce sont des champs scalaires
(clair = saillant, sombre = creux). `derive-maps.py` en calcule la normale, la rugosité, l'AO et la
multiplication d'albedo. Il **avertit d'ailleurs explicitement** si l'image reçue est colorée :

> `⚠ image nettement colorée (chroma moyenne …) — est-ce bien une carte de HAUTEUR en niveaux de gris ?`
> — `tools/derive-maps.py:58-64`

Parce qu'une hauteur colorée est le symptôme d'un générateur qui a rendu *une jolie image de
blindage* au lieu de la carte demandée. Ce n'est pas un caprice de format : c'est le contrôle qui
attrape l'erreur.

**D'où vient la couleur du boss, alors ?** Des **matériaux Blender**, qui portent la palette Null
Choir normative (charte §3). La carte `_mul` ne fait que la moduler. C'est pour cela que les cartes
sont grises : la palette est la source de vérité, et un albédo peint en couleur la **recouvrirait**.

**Mais rien n'oblige à s'y tenir partout.** ADR-0013 §3 a explicitement débloqué la couleur
« lorsque c'est motivé (cristal, décalques, marquages) » — et le projet **ne s'en est jamais servi** :
toutes les cartes importées sont en mode `L`, sauf les normales qui sont RGB par construction. Le
verrou est levé depuis deux mois et personne ne l'a franchi.

Deux endroits le méritent sur ce boss, et ils sont dans les annexes :

- **le vortex** (9/11) — déjà en couleur : c'est un effet lumineux, il n'a aucun matériau de palette
  derrière lui à moduler ;
- **la croûte du noyau** (8/11) — ajoutée pour cette raison : c'est l'équivalent exact du
  `crystal_facets` de la citadelle, la seule surface du boss où la teinte varie *à l'intérieur* d'un
  même matériau (croûte violette morte ↔ chair magenta incandescente). Une multiplication grise ne
  sait pas faire cette bascule.

Partout ailleurs — écailles, greebles, craquelures, dégâts, paroi du puits — le gris est le bon
choix, et il est délibéré.

> ✅ **`tools/bg-key-alpha.py` — corrigé, et la cause n'était pas celle annoncée.** Une version
> précédente de ce document affirmait que le script « ne tourne pas, scipy manquant ». C'était faux
> en substance : `scipy` ne sert qu'à `key_light()` (flood-fill par composantes connexes, pour un
> objet opaque sur fond clair). Nos deux images sont des objets **lumineux sur noir pur** →
> `--mode black` → `key_black()`, qui tient en trois lignes de numpy.
>
> Le blocage réel était un `from scipy import ndimage` **au niveau module** : le script refusait de
> démarrer pour *tous* les modes à cause de la dépendance d'un seul. L'import est désormais local à
> `key_light()`, et `black`/`sat` fonctionnent sans rien installer. Le détourage des deux images de
> l'annexe C a été fait et vérifié sur cette base.

---

## ANNEXE A — planches de conception

### ⚠️ Les légendes — lire avant de coller

Le skill `/asset-image` interdit d'habitude tout texte dans une image générée. **Ces trois planches
sont l'exception délibérée** : ce sont des documents de travail destinés à être *lus* par un
modeleur, et une maquette sans légende oblige à deviner ce qu'on regarde. Les prompts demandent donc
explicitement des étiquettes.

Ce que ça implique :

- **Étiquettes courtes, 1 à 3 mots, en majuscules, en anglais** — les générateurs déforment le texte
  long ; un mot ou deux passent presque toujours.
- **Reliées par un trait fin** au détail qu'elles désignent, plus un **cartouche de titre** par
  panneau.
- Restent **interdits** : filigrane, signature, logo, nom de marque, nom d'artiste, faux texte
  décoratif de remplissage.
- Si une légende sort illisible, on **re-lettre proprement** par-dessus : ces planches ne sont que
  des références, elles n'entrent jamais dans le jeu, et un re-lettrage manuel est légitime.

---

### 1/11 — `pale_leviathan_phases_sheet`

```
PROMPT — à coller tel quel :
────────────────────────────────────────────────────────────
Planche de conception technique pour un vaisseau-amiral extraterrestre biomécanique
de jeu vidéo, création originale, style animation japonaise des années 1980 revisitée
en peinture numérique nette, sur fond bleu-nuit très sombre quadrillé comme un plan
d'ingénieur.

La planche montre QUATRE grands panneaux alignés, de gauche à droite, qui présentent
le MÊME vaisseau à quatre stades successifs de destruction. Le vaisseau mesure 14
mètres de long ; dans chaque panneau, un petit chasseur triangulaire blanc cassé de
2,5 mètres est dessiné à côté pour donner l'échelle.

Panneau 1 — vaisseau intact : un gros noyau sphérique magenta incandescent, sillonné
de craquelures lumineuses, à demi recouvert par une coquille en croissant faite de
plaques blindées ivoire froid et anthracite qui se chevauchent comme des écailles.
Quatre plaques d'armure distinctes, plus épaisses que les autres, sont réparties à
quatre-vingt-dix degrés sur cette coquille. Quatre longs bras-épines effilés et
segmentés, veinés de magenta, partent du corps vers l'arrière et les côtés. Silhouette
franchement asymétrique.

Panneau 2 — les quatre plaques d'armure ont été arrachées, la coquille en croissant
est basculée en arrière, le noyau sphérique s'est ouvert en un entonnoir tourbillonnant
violet sombre aux spirales magenta. Trois excroissances anguleuses saillent de la lèvre
de cet entonnoir. Des débris de coque flottent autour, aspirés en spirale.

Panneau 3 — les quatre bras-épines se sont détachés du corps et flottent séparément
autour de lui, chacun dans une posture différente, pointes tournées vers l'extérieur.
Le corps central n'est plus qu'un tronc décharné et un entonnoir béant.

Panneau 4 — le vaisseau n'est plus qu'un squelette : l'entonnoir grand ouvert forme un
puits vertical bordé d'anneaux internes concentriques percés chacun d'une ouverture,
et tout au fond brille un petit cœur magenta intense. Le chasseur d'échelle est dessiné
en train de plonger dans le puits.

Chaque panneau porte, en haut, un court cartouche de titre en majuscules, et deux ou
trois étiquettes de un à trois mots en majuscules reliées par un trait fin blanc aux
détails qu'elles désignent (par exemple ARMOR PLATE, CRESCENT SHELL, GRAVITIC NODE,
DETACHED SPIKE, INNER RINGS, HEART). Le lettrage est net, fin, technique.

Palette stricte : anthracite, violet sombre, ivoire froid, magenta lumineux, plus une
pointe très rare de vert maladif. Aucun bleu cyan, aucun rouge corail.

Éviter absolument : filigrane, signature, logo, nom de marque, nom d'artiste, texte
décoratif de remplissage, paragraphes de faux texte, photoréalisme, flou, personnages
humains, planète ou nébuleuse en fond, symétrie parfaite, surfaces lisses et propres
de vaisseau militaire humain.
────────────────────────────────────────────────────────────
```

```
FORMAT      : PNG, 1536 x 1024 (paysage natif du generateur), couleur
DÉPOSER     : assets/reference/concepts/pale_leviathan_phases_sheet.png
ENSUITE     : rien à dériver — c'est une planche de référence, jamais chargée par le
              moteur (assets/reference/ porte un .gdignore). Vérifier qu'elle passe
              bien par Git LFS : git check-attr filter -- <chemin>
VÉRIFIER    : les quatre panneaux racontent bien une DÉGRADATION progressive (on doit
              pouvoir les remettre dans l'ordre sans les titres) ; les légendes sont
              lisibles ; aucun cyan ni corail
PROVENANCE  : pale_leviathan_phases_sheet,assets/reference/concepts/pale_leviathan_phases_sheet.png,concept-art,imagegen (ChatGPT),,tiers (genere IA),proprietary-internal,2026-07-23,docs/design/BOSS_PALE_LEVIATHAN.md,,"Planche des quatre phases du boss final ; annotee"
```

---

### 2/11 — `pale_leviathan_core_states_sheet`

```
PROMPT — à coller tel quel :
────────────────────────────────────────────────────────────
Planche de détails techniques pour un vaisseau-amiral extraterrestre biomécanique de
jeu vidéo, création originale, style animation japonaise des années 1980 revisitée en
peinture numérique nette, fond bleu-nuit très sombre quadrillé comme un plan
d'ingénieur.

Six panneaux de gros plans, disposés en deux rangées de trois.

Rangée du haut — les trois états du noyau central, vus de face, chacun cadré serré :
1) FERMÉ : une sphère magenta incandescente de trois mètres de diamètre, parcourue
d'un réseau de craquelures lumineuses, sertie dans un anneau de plaques blindées
ivoire froid et anthracite qui se chevauchent.
2) OUVERT EN ENTONNOIR : la même sphère creusée en un tourbillon violet très sombre,
aux spirales magenta qui s'enfoncent vers un point de fuite ; trois excroissances
anguleuses saillent de la lèvre circulaire.
3) PUITS : l'entonnoir vu dans l'axe, transformé en tunnel profond bordé de cinq
anneaux internes concentriques, chacun percé d'une large ouverture décalée par rapport
au précédent ; tout au fond brille un petit cœur magenta intense.

Rangée du bas — trois détails de pièces, isolés sur le fond quadrillé :
4) une plaque d'armure arrachée, vue de trois quarts : blindage ivoire froid en
écailles superposées sur une âme anthracite, arêtes ébréchées, interstices lumineux
magenta, environ deux mètres de large.
5) une excroissance gravitique de la lèvre : cône anguleux segmenté, veiné de magenta,
avec une embase articulée, environ un mètre cinquante.
6) un bras-épine détaché, vu en entier de profil : long dard segmenté de six mètres,
effilé, blindage ivoire et anthracite, veines magenta le long des segments, articulation
d'épaule visible à la base et petites bouches d'arme à mi-longueur.

Chaque panneau porte un court cartouche de titre en majuscules et deux ou trois
étiquettes de un à trois mots en majuscules, reliées par un trait fin blanc au détail
désigné (par exemple CLOSED CORE, VORTEX, INNER RING, HEART, ARMOR PLATE, GRAVITIC
NODE, SPIKE, SHOULDER JOINT). Lettrage net, fin, technique.

Palette stricte : anthracite, violet sombre, ivoire froid, magenta lumineux, plus une
pointe très rare de vert maladif. Aucun bleu cyan, aucun rouge corail.

Éviter absolument : filigrane, signature, logo, nom de marque, nom d'artiste, texte
décoratif de remplissage, paragraphes de faux texte, photoréalisme, flou, personnages
humains, planète ou nébuleuse en fond, surfaces lisses et propres de vaisseau militaire
humain.
────────────────────────────────────────────────────────────
```

```
FORMAT      : PNG, 1536 x 1024 (paysage natif du generateur), couleur
DÉPOSER     : assets/reference/concepts/pale_leviathan_core_states_sheet.png
ENSUITE     : rien à dériver. Vérifier le passage en Git LFS.
VÉRIFIER    : le panneau PUITS doit lire comme une PROFONDEUR (un tunnel où l'on
              plonge), pas comme un disque noir — c'est le point qui portera la
              phase 4 ; les six panneaux sont cohérents entre eux en matière
PROVENANCE  : pale_leviathan_core_states_sheet,assets/reference/concepts/pale_leviathan_core_states_sheet.png,concept-art,imagegen (ChatGPT),,tiers (genere IA),proprietary-internal,2026-07-23,docs/design/BOSS_PALE_LEVIATHAN.md,,"Etats du noyau et details de pieces du boss final ; annotee"
```

---

### 3/11 — `pale_leviathan_parts_sheet`

```
PROMPT — à coller tel quel :
────────────────────────────────────────────────────────────
Planche d'ingénierie en vue éclatée pour un vaisseau-amiral extraterrestre
biomécanique de jeu vidéo, création originale, style plan technique dessiné : traits
nets, éclairage neutre et frontal, très peu d'ombres portées, fond bleu-nuit sombre
quadrillé.

Deux zones.

Zone du haut — quatre vues orthographiques du vaisseau intact, alignées et à la même
échelle, sans perspective : vue de dessus, vue de face, vue de profil, vue de trois
quarts arrière. Le vaisseau mesure 14 mètres de long et 11 mètres de large. Un gros
noyau sphérique magenta au centre, une coquille en croissant de plaques blindées ivoire
froid et anthracite qui le surplombe, quatre plaques d'armure plus épaisses réparties
à quatre-vingt-dix degrés sur cette coquille, et quatre longs bras-épines segmentés
partant vers l'arrière et les côtés. Silhouette asymétrique. Sous chaque vue, une ligne
de cote fine avec ses flèches aux extrémités.

Zone du bas — une vue éclatée du même vaisseau : toutes les pièces mobiles écartées les
unes des autres le long de fines lignes de rappel pointillées, comme une notice de
montage. Les pièces à montrer séparément : le corps porteur, l'anneau tournant de la
coquille, la coquille en croissant elle-même, les quatre plaques d'armure, le noyau
sphérique, la lèvre de l'entonnoir, les trois excroissances gravitiques, les cinq
anneaux internes du tunnel, le petit cœur, et les quatre bras-épines chacun décomposé
en trois segments (base, milieu, pointe).

Chaque pièce écartée porte une étiquette de un à trois mots en majuscules, reliée par
un trait fin blanc à la pièce, et un petit disque marquant son axe de rotation quand
elle en a un. Étiquettes suggérées : BODY, SHELL RING, CRESCENT, ARMOR PLATE, CORE,
MAW LIP, GRAVITIC NODE, INNER RING, HEART, SPIKE, SPIKE MID, SPIKE TIP.

Palette stricte : anthracite, violet sombre, ivoire froid, magenta lumineux. Aucun bleu
cyan, aucun rouge corail.

Éviter absolument : filigrane, signature, logo, nom de marque, nom d'artiste,
paragraphes de faux texte, perspective forcée sur les vues orthographiques,
photoréalisme, flou, ombres dramatiques, personnages humains, fond étoilé.
────────────────────────────────────────────────────────────
```

```
FORMAT      : PNG, 1536 x 1024 (paysage natif du generateur), couleur
DÉPOSER     : assets/reference/concepts/pale_leviathan_parts_sheet.png
ENSUITE     : rien à dériver. Vérifier le passage en Git LFS.
              Cette planche est l'entrée directe du brief de reforge de
              tools/blender/build_pale_leviathan.py : la confronter au contrat de noms
              du §9.3 de ce document, pièce par pièce.
VÉRIFIER    : toutes les pièces du contrat §9.3 sont présentes et identifiables ; les
              vues du haut sont bien orthographiques (aucune fuite perspective) ; les
              axes de rotation marqués correspondent aux pivots du §9.3
PROVENANCE  : pale_leviathan_parts_sheet,assets/reference/concepts/pale_leviathan_parts_sheet.png,concept-art,imagegen (ChatGPT),,tiers (genere IA),proprietary-internal,2026-07-23,docs/design/BOSS_PALE_LEVIATHAN.md,,"Vues orthographiques et eclate des pieces animables du boss final ; annotee"
```

---

---

## ANNEXE B — jeu de textures dédié au Leviathan

Consommé par `scripts/fx/leviathan_detail.gd`, sur le modèle exact de `citadel_detail.gd`.
**Prérequis absolu** : la reforge de coque doit avoir appelé `ak.box_project_uv()` (§9.6).

| Texture | Ce qu'elle habille | Nature |
|---|---|---|
| `leviathan_scales` | le corps, la coquille, les 4 plaques d'armure | hauteur N&B tuilable |
| `leviathan_greebles` | les interstices, les segments d'épines, la lèvre de la gueule | hauteur N&B tuilable |
| `leviathan_cracks` | le réseau lumineux magenta du noyau | **masque**, pas un relief |
| `leviathan_damage` | l'endommagement révélé par `health_ratio()` | **masque** |
| `leviathan_core_albedo` | la croûte du noyau | **couleur** — la seule, et elle est motivée |

La dernière est celle qui manque au mini-boss : `HarvesterLimb.health_ratio()` a été écrit
« pour un retour visuel d'endommagement (émissifs, fissures) » (`harvester_limb.gd:158`) et n'a
jamais rien eu à afficher. Le Leviathan lui donne enfin sa carte — et le Harvester pourra la
réutiliser.

---

### 4/11 — `leviathan_scales_height`

```
PROMPT — à coller tel quel :
────────────────────────────────────────────────────────────
Texture répétable en niveaux de gris représentant un blindage biomécanique fait
d'écailles blindées qui se chevauchent, vue orthogonale de dessus, éclairage neutre
et parfaitement plat, aucune ombre portée, aucune perspective, aucun vignettage,
aucun assombrissement des bords.

C'est une carte de HAUTEUR : le blanc est saillant, le noir est creux. Les écailles
sont claires et bombées, les interstices entre elles sont sombres et étroits.

Chaque écaille mesure environ 1,1 mètre de large dans le monde réel, et la tuile
entière couvre environ 5,5 mètres : on voit donc à peu près cinq écailles en largeur
et cinq en hauteur. Les écailles se recouvrent partiellement comme des tuiles de
toit ou des plaques de carapace, avec de légères variations de taille et
d'orientation d'une écaille à l'autre — jamais une grille régulière. Quelques
écailles portent une arête médiane ou une rainure fine.

L'image doit se répéter parfaitement en tuile, sans aucune couture visible sur les
quatre bords.

Éviter absolument : couleur, teinte, perspective, ombre portée, vignettage, bords
assombris, cadre, objet isolé au centre, texte, lettres, chiffres, logo, filigrane,
signature, nom de marque ou d'artiste, rivets photoréalistes, rouille, surfaces
lisses et propres de vaisseau militaire humain, grille régulière trop ordonnée.
────────────────────────────────────────────────────────────
```

```
FORMAT      : PNG, 1024 x 1024 (carre natif du generateur), niveaux de gris
DÉPOSER     : assets/source/textures/leviathan/leviathan_scales_height.png
ENSUITE     : # 1) mesurer la couture AVANT d'intégrer
              python3 tools/derive-maps.py \
                assets/source/textures/leviathan/leviathan_scales_height.png \
                --out /tmp --name probe --check-tiling
              # 2) si OK, dériver les quatre cartes
              python3 tools/derive-maps.py \
                assets/source/textures/leviathan/leviathan_scales_height.png \
                --out assets/imported/textures/leviathan --name leviathan_scales \
                --mul --preview /tmp/leviathan_scales.png
VÉRIFIER    : la ligne « tuilage » dit OK ; ouvrir la preview — le quart haut-gauche
              montre 2x2 tuiles, la couture s'y voit. Puis EN JEU : le rendu studio
              flatte, le post-process 960x540 écrase le détail fin (ADR-0011)
PROVENANCE  : leviathan_scales_height_src,assets/source/textures/leviathan/leviathan_scales_height.png,raster_texture,ChatGPT imagegen (OpenAI),,tiers (genere IA),proprietary-internal,2026-07-23,docs/design/BOSS_PALE_LEVIATHAN.md,,"Carte de hauteur N&B repetable — ecailles blindees du boss final (~1,1 m en jeu)"
              + une ligne par dérivée versionnée (_nrm, _rough, _ao, _mul), avec
              source_tool = tools/derive-maps.py — cf. lignes 132-135 du CSV
```

---

### 5/11 — `leviathan_greebles_height`

```
PROMPT — à coller tel quel :
────────────────────────────────────────────────────────────
Texture répétable en niveaux de gris représentant un encombrement mécanique
organique dense : faisceaux de conduits souples, vertèbres, câbles tressés, petits
blocs machinés et nervures irrégulières entremêlés, vue orthogonale de dessus,
éclairage neutre et parfaitement plat, aucune ombre portée, aucune perspective,
aucun vignettage.

C'est une carte de HAUTEUR : le blanc est saillant, le noir est creux. Les conduits
et les vertèbres sont clairs, les cavités entre eux sont franchement sombres et
profondes.

Le motif est grossier, pas fin : chaque conduit fait environ 25 centimètres de
diamètre et la tuile entière couvre environ 5,5 mètres. On doit reconnaître des
pièces, pas un moucheté. La composition est irrégulière et organique — des
faisceaux qui serpentent, jamais un damier ni un alignement.

L'image doit se répéter parfaitement en tuile, sans aucune couture visible sur les
quatre bords.

Éviter absolument : couleur, teinte, perspective, ombre portée, vignettage, bords
assombris, cadre, objet isolé au centre, texte, lettres, chiffres, logo, filigrane,
signature, nom de marque ou d'artiste, motif trop fin et régulier, aspect de circuit
imprimé, tuyauterie industrielle humaine bien rangée.
────────────────────────────────────────────────────────────
```

```
FORMAT      : PNG, 1024 x 1024 (carre natif du generateur), niveaux de gris
DÉPOSER     : assets/source/textures/leviathan/leviathan_greebles_height.png
ENSUITE     : mêmes deux commandes que 4/11, avec --name leviathan_greebles
VÉRIFIER    : ⚠️ le tuilage EN JEU à deux densités. La citadelle a dû tuiler ses
              greebles DEUX FOIS plus gros que son blindage : à densité égale chaque
              élément faisait 28 cm, soit deux pixels après le post-process, et les
              ponts lisaient comme de la saleté (citadel_detail.gd:34-40). Prévoir le
              même TILING_GREEBLE = 0.5 côté leviathan_detail.gd
PROVENANCE  : leviathan_greebles_height_src,assets/source/textures/leviathan/leviathan_greebles_height.png,raster_texture,ChatGPT imagegen (OpenAI),,tiers (genere IA),proprietary-internal,2026-07-23,docs/design/BOSS_PALE_LEVIATHAN.md,,"Carte de hauteur N&B repetable — encombrement mecanique organique du boss final (conduits ~25 cm)"
              + une ligne par dérivée versionnée
```

---

### 6/11 — `leviathan_cracks_mask`

⚠️ **Un masque, pas une hauteur.** Les craquelures sont un **émissif**, et un émissif ne reçoit pas
la lumière : lui dériver un relief ne produirait rien de visible. C'est l'erreur qui a fait lire le
noyau de la citadelle comme une goutte blanche uniforme (ADR-0013).

```
PROMPT — à coller tel quel :
────────────────────────────────────────────────────────────
Texture répétable en noir et blanc pur représentant un réseau de craquelures
organiques ramifiées, comme une croûte fendue ou un delta de rivière, vue
orthogonale de dessus, éclairage neutre et parfaitement plat, aucune ombre portée,
aucune perspective, aucun vignettage.

C'est un MASQUE, pas une texture d'aspect : les craquelures sont d'un blanc franc et
uniforme, tout le reste est d'un noir franc et uniforme. Aucun dégradé sauf un très
léger adoucissement d'un ou deux pixels au bord des traits.

Les craquelures forment un réseau irrégulier de veines qui se divisent en branches de
plus en plus fines. Les veines principales font environ 8 centimètres de large dans le
monde réel ; la tuile entière couvre environ 2 mètres. Les cellules entre les veines
sont de tailles très variées, arrondies et irrégulières, jamais hexagonales ni
régulières.

L'image doit se répéter parfaitement en tuile, sans aucune couture visible sur les
quatre bords.

Éviter absolument : couleur, gris intermédiaires étendus, dégradés doux, lueur,
halo, flou, perspective, ombre portée, vignettage, texte, lettres, chiffres, logo,
filigrane, signature, nom de marque ou d'artiste, motif hexagonal régulier, aspect
de vitrail ou de mosaïque, éclats de verre brisé rectilignes.
────────────────────────────────────────────────────────────
```

```
FORMAT      : PNG, 1024 x 1024 (carre natif du generateur), noir et blanc
DÉPOSER     : assets/source/textures/leviathan/leviathan_cracks_mask.png
ENSUITE     : python3 tools/derive-maps.py \
                assets/source/textures/leviathan/leviathan_cracks_mask.png \
                --out assets/imported/textures/leviathan --name leviathan_cracks --mask
              (--mask ne dérive NI normale NI AO : il ne sort que le masque recadré)
VÉRIFIER    : le masque doit être franc — l'ouvrir et vérifier que l'histogramme est
              bien à deux pics. Un masque « gris » donne un émissif laiteux
PROVENANCE  : leviathan_cracks_mask_src,assets/source/textures/leviathan/leviathan_cracks_mask.png,raster_texture,ChatGPT imagegen (OpenAI),,tiers (genere IA),proprietary-internal,2026-07-23,docs/design/BOSS_PALE_LEVIATHAN.md,,"Masque N&B repetable — reseau de craquelures emissives du noyau (veines ~8 cm)"
              + une ligne pour leviathan_cracks_mask.png dans imported/
```

---

### 7/11 — `leviathan_damage_mask`

Révélé progressivement en fonction de `health_ratio()` d'une pièce : à pleine vie le masque est
invisible, à zéro il est complet. C'est ce qui donne enfin un usage au retour d'endommagement prévu
par `harvester_limb.gd:158`.

```
PROMPT — à coller tel quel :
────────────────────────────────────────────────────────────
Texture répétable en niveaux de gris représentant des dégâts de combat progressifs
sur une carapace : fissures, éclats de blindage arrachés, brûlures et traînées de
suie, vue orthogonale de dessus, éclairage neutre et parfaitement plat, aucune ombre
portée, aucune perspective, aucun vignettage.

C'est un MASQUE PROGRESSIF : la valeur de gris code l'ORDRE d'apparition des dégâts.
Le blanc marque les blessures les plus graves et les plus profondes, les gris moyens
les dégâts intermédiaires, le noir les zones qui restent intactes. Les dégâts sont
donc organisés en amas de gravité décroissante : quelques foyers très clairs, des
auréoles de gris autour, et de larges plages noires.

Les impacts principaux font environ 60 centimètres dans le monde réel, et la tuile
entière couvre environ 5,5 mètres. Il y a trois ou quatre foyers majeurs par tuile,
pas davantage : ce sont de vraies blessures, pas du grain.

L'image doit se répéter parfaitement en tuile, sans aucune couture visible sur les
quatre bords.

Éviter absolument : couleur, rouille orange, perspective, ombre portée, vignettage,
bords assombris, cadre, texte, lettres, chiffres, logo, filigrane, signature, nom de
marque ou d'artiste, impacts de balles régulièrement espacés, grain uniforme sur
toute la surface, aspect de bruit ou de texture de papier.
────────────────────────────────────────────────────────────
```

```
FORMAT      : PNG, 1024 x 1024 (carre natif du generateur), niveaux de gris
DÉPOSER     : assets/source/textures/leviathan/leviathan_damage_mask.png
ENSUITE     : python3 tools/derive-maps.py \
                assets/source/textures/leviathan/leviathan_damage_mask.png \
                --out assets/imported/textures/leviathan --name leviathan_damage --mask
VÉRIFIER    : seuiller le masque à 0,25 / 0,50 / 0,75 dans un visualiseur et regarder
              les trois états : ils doivent raconter une dégradation croissante
              crédible, pas trois motifs sans rapport
PROVENANCE  : leviathan_damage_mask_src,assets/source/textures/leviathan/leviathan_damage_mask.png,raster_texture,ChatGPT imagegen (OpenAI),,tiers (genere IA),proprietary-internal,2026-07-23,docs/design/BOSS_PALE_LEVIATHAN.md,,"Masque N&B progressif — endommagement des pieces du boss, revele par health_ratio()"
              + une ligne pour leviathan_damage_mask.png dans imported/
```

---

### 8/11 — `leviathan_core_albedo` ⟵ **en couleur, et c'est motivé**

La seule carte **colorée** du jeu de coque, et la première du projet à exercer le déverrouillage
d'ADR-0013 §3. La raison est la même que pour le cristal de la citadelle : sur le noyau, la teinte
varie **à l'intérieur d'un même matériau** — croûte violette morte contre chair magenta
incandescente. Une multiplication grise sait assombrir, elle ne sait pas faire cette bascule.

⚠️ **La couleur reste soumise à la palette.** Elle ne l'élargit pas : ce sont les teintes Null Choir
de la charte §3 et rien d'autre. Une carte qui introduirait une couleur hors palette contournerait la
règle au lieu de la servir — c'est exactement ce qu'ADR-0011 craignait, et ce qu'ADR-0013 n'a pas
autorisé.

```
PROMPT — à coller tel quel :
────────────────────────────────────────────────────────────
Texture répétable EN COULEUR représentant la surface d'un noyau d'énergie organique :
une croûte minérale fendue à travers laquelle affleure une matière incandescente, vue
orthogonale de dessus, éclairage neutre et parfaitement plat, aucune ombre portée,
aucune perspective, aucun vignettage.

C'est une carte de COULEUR (albédo), pas un relief : elle décrit ce que la surface
EST, pas comment elle est bosselée.

La croûte occupe environ les deux tiers de l'image : plaques minérales d'un violet
très sombre, presque anthracite, mates et éteintes, aux bords irréguliers. Le tiers
restant est la matière qui affleure entre elles : magenta lumineux, saturé, avec un
cœur presque blanc-rose au plus profond des fissures, et une transition douce du
magenta vers le violet sur les bords de chaque plaque, comme du métal chauffé qui
refroidit vers l'extérieur. Quelques rares filets ivoire froid, très fins, parcourent
la croûte.

Aucune autre couleur : pas de bleu cyan, pas de rouge corail, pas d'orange, pas de
jaune, pas de vert vif.

Les plaques de croûte mesurent environ 40 centimètres dans le monde réel et la tuile
entière couvre environ 2,5 mètres : on voit donc une trentaine de plaques. La
répartition est organique et irrégulière, jamais un damier ni un réseau hexagonal.

L'image doit se répéter parfaitement en tuile, sans aucune couture visible sur les
quatre bords.

Éviter absolument : perspective, ombre portée, vignettage, bords assombris, cadre,
objet isolé au centre, texte, lettres, chiffres, logo, filigrane, signature, nom de
marque ou d'artiste, aspect de lave ou de roche volcanique terrestre, aspect de
braise de feu de bois, teintes orangées ou jaunes, motif hexagonal régulier, lueur
diffuse qui noierait le contraste entre croûte et matière.
────────────────────────────────────────────────────────────
```

```
FORMAT      : PNG, 1024 x 1024 (carre natif du generateur), COULEUR
DÉPOSER     : assets/source/textures/leviathan/leviathan_core_albedo.png
ENSUITE     : ⚠️ NE PAS passer par derive-maps.py — ce n'est pas une hauteur, et
              l'outil avertirait justement qu'elle est colorée (derive-maps.py:58-64).
              Elle se copie telle quelle, après vérification du tuilage :
              python3 tools/derive-maps.py \
                assets/source/textures/leviathan/leviathan_core_albedo.png \
                --out /tmp --name probe --check-tiling
              cp assets/source/textures/leviathan/leviathan_core_albedo.png \
                 assets/imported/textures/leviathan/
              Le relief du noyau, lui, vient de la géométrie (croûte modélisée par
              build_pale_leviathan.py) et du masque de craquelures 6/11.
VÉRIFIER    : ⚠️ LA PALETTE, pixel par pixel. Échantillonner l'image et confirmer que
              toutes les teintes tombent dans le Null Choir (anthracite, violet
              sombre, ivoire froid, magenta). Une dérive vers l'orange ou le rouge
              corail est un REJET : elle volerait leur lisibilité aux projectiles
              ennemis (DA §6). Puis en jeu, à l'échelle réelle
PROVENANCE  : leviathan_core_albedo_src,assets/source/textures/leviathan/leviathan_core_albedo.png,raster_texture,ChatGPT imagegen (OpenAI),,tiers (genere IA),proprietary-internal,2026-07-23,docs/design/BOSS_PALE_LEVIATHAN.md,,"Carte d'albedo COULEUR de la croute du noyau — premiere carte coloree du projet (ADR-0013 §3) ; teintes Null Choir uniquement"
              + une ligne pour la copie dans imported/
```

---

## ANNEXE C — décor et VFX de l'arène

Le fond du jeu est **procédural** (ADR-0006) : on ne repeint pas un panorama. Mais BRIEF-0028 a
établi le complément légitime — des **landmarks peints en Sprite3D billboard**, posés derrière le
plan de jeu, devant la brume procédurale. C'est ce registre-là qu'on emploie ici, plus deux textures
pour la gueule.

✅ Les deux images à fond noir de cette annexe ont été détourées et vérifiées : `bg-key-alpha.py`
fonctionne en `--mode black` depuis que son import de `scipy` est local à `key_light()` (cf.
préambule des annexes).

**Les débris de la phase 2 ne sont pas dans cette annexe** : ce sont des morceaux de coque, et le
`.glb` du boss en produira naturellement une fois les plaques modélisées. Réutiliser les maillages
plutôt que de générer des sprites.

---

### 9/11 — `maw_vortex_color`

```
PROMPT — à coller tel quel :
────────────────────────────────────────────────────────────
Texture carrée représentant un tourbillon vu exactement dans son axe, centré, sur
fond NOIR PUR. Création originale pour un jeu vidéo de science-fiction.

Un entonnoir de matière énergétique qui s'enfonce vers un point de fuite au centre
exact de l'image : des spirales de plus en plus serrées à mesure qu'elles approchent
du centre, où elles se perdent dans une obscurité profonde. La lecture doit être
celle d'une PROFONDEUR dans laquelle on plonge, pas d'un disque plat.

Couleurs : violet très sombre pour la masse de l'entonnoir, magenta lumineux pour
les filaments et les arêtes des spirales, quelques traînées ivoire froid très fines.
Le centre est presque noir, la périphérie est la plus lumineuse. Aucun bleu cyan,
aucun rouge corail, aucun orange.

L'entonnoir occupe environ 85 pour cent de la largeur de l'image ; les 15 pour cent
restants sont du noir pur absolu, jusqu'aux bords. L'ouverture représente 6 mètres de
diamètre dans le monde réel.

Éviter absolument : damier de transparence, fond gris ou bleuté, halo qui déborde
jusqu'aux bords, étoiles, planète, nébuleuse en arrière-plan, texte, lettres,
chiffres, logo, filigrane, signature, nom de marque ou d'artiste, aspect de galaxie
spirale vue de loin, aspect de coquillage, symétrie parfaite mécanique.
────────────────────────────────────────────────────────────
```

```
FORMAT      : PNG, 1024 x 1024 (carre natif du generateur), couleur, fond noir pur
DÉPOSER     : assets/source/vfx/maw/maw_vortex_color.png
ENSUITE     : alpha par clé de luminance (le noir devient transparent) → 
              assets/imported/vfx/maw/maw_vortex.png
              ✅ FAIT et vérifié :
              python3 tools/bg-key-alpha.py --mode black \
                assets/source/vfx/maw/maw_vortex_color.png \
                assets/imported/vfx/maw/maw_vortex.png --lo 6 --hi 50 \
                --preview /tmp/prev_vortex.png
              Le shader de la gueule fait TOURNER cette carte en coordonnées polaires :
              elle est donc générée immobile, l'animation est du code
VÉRIFIER    : en jeu, à l'échelle réelle. Le test est unique et non négociable — on
              doit avoir envie d'y entrer (c'est le sujet de la phase 4). Un disque
              noir est un échec, même joli
PROVENANCE  : maw_vortex_color_src,assets/source/vfx/maw/maw_vortex_color.png,raster_texture,ChatGPT imagegen (OpenAI),,tiers (genere IA),proprietary-internal,2026-07-23,docs/design/BOSS_PALE_LEVIATHAN.md,,"Carte polaire couleur de l'entonnoir gravitique ; tournee par shader"
```

---

### 10/11 — `maw_tunnel_wall_height`

```
PROMPT — à coller tel quel :
────────────────────────────────────────────────────────────
Texture répétable en niveaux de gris représentant la paroi intérieure d'un conduit
biomécanique : anneaux de vertèbres blindées, nervures longitudinales, sphincters de
matière organique et petites bouches d'où sortent des filaments, vue orthogonale de
dessus, éclairage neutre et parfaitement plat, aucune ombre portée, aucune
perspective, aucun vignettage.

C'est une carte de HAUTEUR : le blanc est saillant, le noir est creux. Les anneaux de
vertèbres sont clairs et fortement bombés, les sillons entre eux sont profondément
sombres — le relief doit être franc, bien plus marqué que sur un blindage extérieur.

Le motif est organisé en BANDES HORIZONTALES : les anneaux se succèdent
perpendiculairement à l'axe du conduit. Chaque anneau fait environ 80 centimètres de
large dans le monde réel, et la tuile entière couvre environ 5 mètres, soit six
anneaux environ. Les anneaux sont irréguliers en épaisseur, jamais identiques.

L'image doit se répéter parfaitement en tuile, sans aucune couture visible sur les
quatre bords.

Éviter absolument : couleur, perspective, ombre portée, vignettage, bords assombris,
cadre, texte, lettres, chiffres, logo, filigrane, signature, nom de marque ou
d'artiste, aspect de tuyau industriel humain, anneaux parfaitement identiques et
régulièrement espacés, aspect anatomique explicite ou organique répugnant.
────────────────────────────────────────────────────────────
```

```
FORMAT      : PNG, 1024 x 1024 (carre natif du generateur), niveaux de gris
DÉPOSER     : assets/source/textures/leviathan/maw_tunnel_wall_height.png
ENSUITE     : mêmes deux commandes que 4/11, avec --name maw_tunnel_wall
VÉRIFIER    : le tuilage sur l'axe VERTICAL surtout — c'est celui que le joueur
              parcourt en descendant le puits, et une couture y lit comme un anneau
              de plus qui n'existe pas
PROVENANCE  : maw_tunnel_wall_height_src,assets/source/textures/leviathan/maw_tunnel_wall_height.png,raster_texture,ChatGPT imagegen (OpenAI),,tiers (genere IA),proprietary-internal,2026-07-23,docs/design/BOSS_PALE_LEVIATHAN.md,,"Carte de hauteur N&B repetable — paroi interieure du puits de la phase 4 (anneaux ~80 cm)"
              + une ligne par dérivée versionnée
```

---

### 11/11 — `nebula_leviathan_arena`

Le combat final ne doit pas se jouer sur le même ciel que la première vague. Ce landmark rejoint
`planet_hero`, `nebula_a`, `nebula_b` et `galaxy_distant` déjà livrés par BRIEF-0028, dans le même
registre technique : **Sprite3D billboard**, à Y≈-3, derrière les vaisseaux et devant la brume.

```
PROMPT — à coller tel quel :
────────────────────────────────────────────────────────────
Amas de nébuleuse peint, isolé sur fond NOIR PUR, pour un jeu vidéo de science-fiction.
Création originale.

Une masse de gaz stellaire dense et menaçante, aux volutes lourdes et tourmentées, plus
compacte et plus sombre qu'une nébuleuse ordinaire — elle doit évoquer un orage qui
couve plutôt qu'un voile diffus. En son cœur, quelques foyers d'un magenta profond qui
transparaissent à travers le gaz, comme si quelque chose brûlait à l'intérieur.

Couleurs : violet très sombre et anthracite pour la masse, magenta profond pour les
foyers internes, ivoire froid très désaturé pour quelques crêtes éclairées. Ensemble
sombre et froid, faible saturation générale. Aucun bleu cyan, aucun rouge corail,
aucun orange.

L'amas occupe environ 80 pour cent de l'image et ses bords s'effilochent progressivement
vers le noir pur, sans halo net ni contour dur. Le reste est du noir pur absolu.
Lumière clé venant du haut à gauche.

L'objet est très éloigné et sert de toile de fond : composition large et calme, aucun
détail fin qui accrocherait l'œil, aucun élément qui pourrait passer pour un vaisseau
ou un projectile.

Éviter absolument : damier de transparence, fond gris ou bleuté, cadre, vignettage,
étoiles brillantes au premier plan, planète, vaisseau, texte, lettres, chiffres, logo,
filigrane, signature, nom de marque ou d'artiste, couleurs saturées et vives, contours
nets, aspect de peinture à l'huile texturée.
────────────────────────────────────────────────────────────
```

```
FORMAT      : PNG, 1536 x 1024 (paysage natif du generateur), couleur, fond noir pur
DÉPOSER     : assets/source/backgrounds/raster/nebula_leviathan_arena.png
ENSUITE     : alpha par clé de luminance → assets/imported/backgrounds/nebula_leviathan_arena.png
              ✅ FAIT et vérifié : bg-key-alpha.py --mode black --lo 4 --hi 40
              Puis l'ajouter aux landmarks de scenes/vfx/space_backdrop.tscn, activé
              seulement à la phase FINAL_BOSS
VÉRIFIER    : ⚠️ EN JEU et pendant le combat, pas en preview. Le fond ne doit jamais
              se battre avec les projectiles : le couloir de combat central reste
              lisible, c'est la règle de DA §6 et le défaut exact qui a fait rejeter
              les six couches de parallaxe d'ADR-0006
PROVENANCE  : nebula_leviathan_arena_src,assets/source/backgrounds/raster/nebula_leviathan_arena.png,raster_texture,ChatGPT imagegen (OpenAI),,tiers (genere IA),proprietary-internal,2026-07-23,docs/design/BOSS_PALE_LEVIATHAN.md,,"Landmark peint de l'arene du boss final ; billboard derriere le plan de jeu (registre BRIEF-0028)"
              + une ligne pour la version détourée dans imported/
```

---

## Au retour des images

**Les regarder.** Un asset non rendu et non regardé n'est pas validé (ADR-0006) — et le rendu studio
flatte : ce qui compte, c'est le post-process rétro à 960×540 avec ses scanlines.

1. Confronter la planche 3 au contrat de noms du §9.3, pièce par pièce — c'est elle qui pilote la
   reforge Blender.
2. Vérifier que la reforge a bien appelé `box_project_uv()` **avant** d'intégrer quoi que ce soit de
   l'annexe B (§9.6).
3. Ajouter les lignes de provenance dans `assets/licenses/ASSET_PROVENANCE.csv` — une par source,
   une par dérivée versionnée.
4. Vérifier que les binaires passent bien par Git LFS : `git check-attr filter -- <chemin>`.
5. Ouvrir les briefs du §10 dans l'ordre : coque (4), puis textures (5), puis décor (6).
