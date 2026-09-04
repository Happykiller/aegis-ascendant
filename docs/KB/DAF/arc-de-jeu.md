---
titre: L'arc d'une partie — une campagne de deux niveaux, un seul vaisseau
type: daf
statut: actif
maj: 2026-08-29
---

# L'arc d'une partie

## L'invariant

Le joueur **pilote le chasseur Specter-9 du début à la fin**. Aucune transformation, aucun
changement de véhicule en cours de niveau. C'est la décision **ADR-0010** (2026-07-19), prise après
usage : le changement de vaisseau cassait le flow et la lisibilité de l'arme du joueur.

## ⚠️ Le vocabulaire a changé le 2026-08-29 — « niveau 2 » existe maintenant

**Cette page disait l'inverse jusqu'au 2026-08-29**, et c'était juste à l'époque : « le jeu n'a
qu'un NIVEAU, et un niveau 2 n'existe pas — si on l'entend, c'est de la phase 2 qu'il s'agit ».
`ADR-0038` a rendu cette phrase fausse, et la laisser aurait fait lire « champ d'astéroïdes »
partout où l'opérateur dit « le deuxième niveau ».

L'état actuel, vérifié dans `resources/campaign/campaign_book.tres` :

| Ce que dit l'opérateur | Ce que c'est |
|---|---|
| « le niveau 1 » | le couloir d'Ossane, `scenes/gameplay/graybox.tscn` — six phases, ~3 min |
| « la phase 1 » / « la phase 2 » | **des phases DU NIVEAU 1** : les vagues, puis le champ d'astéroïdes |
| « le niveau 2 » | le survol du Long Cortège, `scenes/gameplay/cortege.tscn` — **cinq tronçons, pas de phases**, ~3 min 40 |

⚠️ Et le niveau 2 **n'a pas de phases du tout** : il a une traversée. Parler de « la phase 3 du
niveau 2 » n'a pas de sens ; on dit **le tronçon 3**. La confusion à surveiller n'est plus
niveau/phase mais phase/tronçon.

⚠️ Ne pas confondre non plus avec l'`enum Phase` du director du niveau 1, qui en compte six et
nomme aussi le docking et la victoire : le décompte de l'opérateur est celui des **sections
jouées**, pas des états du code.

## La campagne

`Campaign` (autoload) lit un `CampaignBook` de `LevelData` typées : l'écran-titre route vers le
niveau courant, et le rapport de mission propose **CONTINUER** quand il y en a un suivant. La
bible narrative en prévoit douze (`docs/lore/CAMPAGNE.md`) ; deux sont jouables.

`--goto-level=<id>` ouvre un niveau par son nom depuis l'écran-titre. ⚠️ Il POSE le niveau courant
avant de router — sinon le rapport proposerait « CONTINUER » vers le niveau d'après celui qu'on
n'a pas joué.

## Le niveau 2 — le survol du Long Cortège

Il ne ressemble à rien de ce qui précède, et c'est ce qu'il faut savoir avant d'y toucher :

- **il n'y a pas de phases**, cinq tronçons de 100 unités défilent à 2,4 u/s, soit ~208 s ;
- **rien ne change à l'écran** d'un bout à l'autre — même bordé, même artère, mêmes tourelles.
  La progression du joueur est dans ce qu'il COMPREND : cinq briefings de pause et huit répliques
  de Lyra ne sont pas de l'habillage, ils sont la structure du niveau ;
- **trois mécaniques de coque** : tourelles (télégraphe obligatoire), ponts d'envol (ils
  produisent tant qu'ils vivent), nœuds d'épine (abattre l'un éteint les tourelles du tronçon
  SUIVANT) ;
- **un VERROU à mi-parcours** depuis le 2026-09-04 : la **Citadelle de Défense**, à `s = 240`
  sur le tronçon 3. Elle **ferme physiquement la route** — le survol freine, s'immobilise, et ne
  repart que quand deux relais puis un noyau sont tombés. ⚠️ **Ce n'est pas un boss**, et ça se
  mesure : la séquence entière est bornée à 30-45 s par `CortegeTuning.citadel_lock_time()`.
  L'arrêt du défilement n'est pas une mise en scène — à 2,4 u/s, 40 s de combat vaudraient 96 m
  de coque quand la fenêtre libre en fait 19 ;
- **le Cortège ne se détruit pas.** Le niveau se traverse ; il continue sa route.

⚠️ **Et le niveau dure 240 s, pas 208.** `level_duration()` compte le défilement **plus** la
séquence du verrou : les lire séparément faisait comparer 208 s à la promesse pendant qu'on en
jouait 240.

⚠️ **Un survol ne revient jamais en arrière.** Chaque cible n'est tirable que pendant la fenêtre
où elle est à l'écran, et c'est ce qui dimensionne tous ses points de vie
(`resources/data/cortege_tuning.gd`, six invariants). Des PV choisis à la main au-dessus de cette
fenêtre rendent la cible indestructible EN PRATIQUE, et le joueur croira mal jouer.

⚠️ **Le pilote automatique ne mesure rien ici.** Une partie complète en `--demo` (208 s) n'a
détruit qu'UNE cible de coque : il esquive et tire droit devant, il ne vise pas un bordé. Pour
juger l'équilibrage de ce niveau, il faut un humain — ou le banc de `tests/unit/test_cortege_hardpoints.gd`.

## Les six phases du niveau 1

```
FIGHTER_WAVES → MINI_BOSS → ASTEROID_FIELD → FINAL_BOSS → DOCKING → VICTORY
```

Vérifié dans le code : `scripts/gameplay/graybox_root.gd` (`enum Phase`). Le niveau entier
est piloté par ce director, en dur — un `EncounterDirector` data-driven reste à écrire
(`docs/BACKLOG.md`, P1).

`ASTEROID_FIELD` est la dernière arrivée (**ADR-0027**, 2026-08-25) : la traversée qui sépare les
deux boss, jouée avec les trois unités que le bestiaire avait livrées sans qu'aucune rencontre ne
les emploie (Choir Mine, Null Maw, Leech Drone). Elle dure 45 à 60 s.

Elle a **son propre décor** : `MoonFlyby` (`scripts/vfx/moon_flyby.gd`) — un survol de lune, monté
au montage du niveau et révélé à l'entrée en phase. ⚠️ Il **remplace** le fond spatial au lieu de
s'y ajouter : c'est ce que demandait l'opérateur et ce qu'impose le budget GPU, et l'échange est
gagnant (−0,200 ms/image mesuré). Les assets restent à forger — une doublure procédurale tient le
rôle et **le dit dans le journal**.

⚠️ **`MusicContext.LevelPhase` reflète `Phase` PAR VALEUR.** Les deux enums se modifient ensemble ;
`tests/unit/test_music_director.gd` est le seul garde-fou et il est là pour ça.

À ne pas confondre avec la machine d'états **applicative** `GameState.State`
(`BOOT, LOADING, FIGHTER_COMBAT, GAME_OVER, VICTORY, CODEX`, dans `scripts/core/game_state.gd`) :
elle gouverne les écrans, pas la progression du niveau. Les cinq phases ci-dessus se déroulent
**entièrement à l'intérieur** de `FIGHTER_COMBAT`.

Chaque phase a son `_start_*()` dans le director, et c'est la fin de la précédente qui l'appelle :
la vague nettoyée ouvre sur le mini-boss, sa défaite sur le champ d'astéroïdes, le champ nettoyé
sur le boss final. Deux `WaveSpawner` distincts portent les deux vagues — le second est monté et
**peuplé** au même instant que le premier, mais dort jusqu'à `begin()` (spec §26.1 : zéro
`instantiate()` en cours de partie).

Le **docking est la séquence de clôture**, pas un milieu de niveau : la citadelle arrive après la
défaite du boss final, le chasseur s'y ancre en autopilote, puis l'écran de victoire.

## ⚠️ Écart constaté avec la documentation d'architecture

`docs/architecture/ARCHITECTURE_FONCTIONNELLE.md` date du **2026-07-11**, soit **huit jours avant**
ADR-0010. Ses §4.5 et §4.6 décrivent encore :

- un appontage **en milieu de niveau** suivi d'un transfert de commande ;
- une **phase forteresse jouable** — le joueur déplace la citadelle et tire ses Twin Rail Batteries,
  avec une jauge d'intégrité.

**Rien de tout cela n'existe plus** : ADR-0010 a supprimé la phase `COMMAND_TRANSFER` et le contrôle
de la forteresse. Le boss final se combat au chasseur, comme le mini-boss.

> **À COMPLÉTER — décision de l'opérateur.** Que fait-on de `ARCHITECTURE_FONCTIONNELLE.md` §4.5 et
> §4.6 ? Trois options : (a) le corriger et le redater, (b) l'archiver en le marquant « état au
> 2026-07-11, voir ADR-0010 », (c) le laisser tel quel et se reposer sur les ADR. Cette KB ne
> tranche pas seule — le document est hors de son périmètre d'écriture.
