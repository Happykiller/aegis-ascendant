---
titre: Mettre le jeu en conformité avec la bible — plan d'implémentation
date: 2026-08-27
auteur: session Claude (poste happykiller), sur demande de l'opérateur
perimetre: gameplay, options/HUD, données de vagues et d'ennemis, tests. Aucun asset de forge
etat: **lot 0 LIVRÉ** (2026-08-27, vérifié en jeu) ; lot 1 prêt ; lot 2 à instruire ;
  lots 3-5 bloqués (décision ou coût)
supersede: rien. Applique docs/design/CONFORMITE-AEGIS.md
---

# Mettre le jeu en conformité avec la bible

> Source des écarts : [`docs/design/CONFORMITE-AEGIS.md`](../design/CONFORMITE-AEGIS.md).
> Les lois sont dans [`docs/design/bible/`](../design/bible/README.md) et se citent par
> identifiant (`LOI-PAT-03`).

## Contexte

Le rapport de conformité a classé les 88 lois du corpus sur le jeu réel : ce qui est tenu, ce qui
est **écarté** délibérément, ce qui est **absent** faute de décision, et ce qui n'a **jamais été
vérifié**. Il constate ; il ne dit pas quoi faire.

Ce plan le dit — dans l'ordre du **rapport entre ce que ça coûte et ce que ça rend au joueur**.

## Le principe de tri, et ce qu'il exclut

⚠️ **Une loi de genre qui contredit une décision de projet perd** (`bible/README`). On ne ferme donc
**pas** un écart au motif qu'il est un écart. Trois cas sont explicitement **hors de ce plan** :

| Écart | Pourquoi on n'y touche pas |
|---|---|
| `LOI-PUI-04` — perte de puissance à la mort | **écartée volontairement** : c'est le pilier A appliqué sans réserve. La refermer rendrait le jeu plus dur pour se conformer à un genre qu'on a choisi de ne pas suivre ici |
| `LOI-LVL-08` — checkpoints | même chose : la reprise sur place fait le travail. C'est la **spec** §5.3 qu'il faudrait corriger, pas le code (décision **D-5**) |
| `LOI-SYS-02` — boucles positives sans contrepoids | assumée, tant que le playtest ne montre pas que la seconde moitié de l'arc est trop facile |

**Ce plan ferme les écarts qui coûtent quelque chose au joueur**, pas ceux qui coûtent à la
conformité.

---

## Lot 0 — les trois gestes gratuits ✅ LIVRÉ le 2026-08-27

Aucune décision requise, aucun arbitrage de design. Fait d'un bloc, vérifié en jeu.

> **Ce que la vérification a changé au plan.** `LOI-LVL-06` ne se jouait **pas** dans le champ
> d'astéroïdes comme annoncé en 0.3 : sur ses quatre unités, **une seule tire** (Choir Mine,
> `RADIAL`) — les trois autres sont en `fire = NONE`. L'écart est dans la **vague d'ouverture**, et
> c'est 0.2 qui vient de le créer : trois schémas de tir, **un seul `needle_shot.tres`**. Il passe
> en tête du lot 2. C'est le bénéfice d'un ❔ transformé en ❌ localisé.
>
> Coût du lot : un drapeau `--options-demo`, parce que l'écran d'options ne s'atteignait qu'au
> clavier et n'était donc vérifiable que par l'opérateur.

### 0.1 — Exposer la secousse d'écran (`LOI-EXP-11`)

Le système existe et le multiplicateur aussi ; **il manque une ligne d'UI**. La spec l'exige déjà
(§7.3 : « secousse réduite ou désactivable »), et les référentiels d'accessibilité la classent au
niveau de base.

| Fichier | Changement |
|---|---|
| `scripts/core/settings_data.gd` | champ `shake: float = 1.0` ; l'ajouter à `graphics_to_dict()` / `graphics_from_dict()` |
| `scripts/core/settings_manager.gd` | `set_shake(value: float)`, sur le modèle exact de `set_pixelation()` — même `_schedule_save()`, même signal `graphics_changed` |
| `scenes/ui/options_menu.tscn` | une `HBoxContainer` **`Shake`** dans `Center/Panel/Graphics`, jumelle de `Pixelation` : `Name` + `Slider` (0 → 1) + `Value` |
| `scripts/ui/options_menu.gd` | brancher le slider, comme `_on_pixelation_toggled` |
| `scripts/gameplay/graybox_root.gd`, `scripts/ui/title_stage.gd` | poser `shake_multiplier` sur le `CameraDirector` au `_ready`, et se connecter à `graphics_changed` |

⚠️ **Trois scènes portent un `CameraDirector`** — `graybox.tscn`, `boot.tscn`, `bestiary_lab.tscn`.
Le réglage doit valoir pour toutes celles qui secouent, sinon il « ne marche pas » au titre.

⚠️ **La tolérance de relecture est un contrat, pas une politesse** : `graphics_from_dict()` doit
laisser le défaut en place si la clé manque — « un joueur ne doit jamais avoir à supprimer son
`settings.cfg` ».

**Tests** (`tests/unit/test_settings_data.gd`, qui existe déjà) : valeur bornée à [0, 1] ; un
fichier **sans** la clé `shake` rend 1.0 ; un `shake` d'un mauvais type ne casse rien ; 0 signifie
bien zéro et non « défaut ».

### 0.2 — Mettre `FAN` et `AIMED` en jeu (`LOI-PAT-02`, `LOI-PAT-03`)

Les deux schémas sont **écrits, testés, documentés — et joués nulle part** : `fire` vaut `SINGLE`
par défaut et aucun `.tres` d'ennemi ne le surcharge. `EnemyController._salvo()` appelle bien
`EnemyFire.shot_count()` et `EnemyFire.direction()` (`enemy_controller.gd:403`, `:413`) : le
changement est **réellement de deux lignes**.

Les deux unités ne sont pas choisies au hasard — c'est la **trajectoire** qui désigne le schéma :

| Unité | Trajectoire | Schéma | `burst_count` | Pourquoi celle-là |
|---|---|---|---|---|
| `needle_scout_lancer` | `HOVER_STRAFE` — s'arrête à `y = 3,5` pendant 2,6 s | **`AIMED`** | **3** (impair) | Une unité qui **s'immobilise** est la seule qui puisse viser honnêtement. Et l'impair met une balle **sur l'axe** : elle punit l'immobilité du joueur pendant qu'elle-même est immobile — l'échange est lisible |
| `needle_scout_strafe` | `STRAFE_RUN` — traverse vite (4,5) | **`FAN`** | 5 | Un éventail aveugle de 62° **ferme un couloir** au passage. C'est ce que fait déjà sa trajectoire ; le tir le dit enfin |

⚠️ **La parité se choisit, elle ne se subit pas** (`LOI-PAT-03`). `burst_count` vaut **5 par
défaut** : laisser le défaut sur `AIMED` donnerait un éventail **impair** par accident. Écrire la
valeur dans le `.tres`, et écrire **pourquoi** en commentaire.

**Tests** — sur le modèle de `test_asteroid_field_wave.gd`, qui garde « ce qu'une retouche peut
casser en silence » :

- au moins **une** unité de la vague d'ouverture tire `AIMED` — sinon le seul schéma qui punit
  l'immobilité redevient orphelin sans que rien ne le signale ;
- l'unité `AIMED` a un `burst_count` **impair** — la garde de parité, qui est la loi ;
- `test_enemy_resources.gd` continue de passer (`burst_count >= 2` pour `FAN`/`AIMED`/`RADIAL`).

**Vérification en jeu, obligatoire** : la salve visée du lancier se lit-elle comme visée ? C'est
`LOI-LIS-02` (grouper) qui décide, et aucun test ne répondra.

### 0.3 — Vérifier `LOI-LVL-06` — dix secondes de jeu, zéro ligne de code

Dans le champ d'astéroïdes, **trois unités tirent en même temps**. « Deux patterns simultanés
distincts doivent avoir des balles d'apparence différente. » Nos `ProjectileData` diffèrent par
unité, mais **rien ne le garantit**.

Jouer la phase, regarder. Si les projectiles se confondent, ça devient un item du lot 2 ; sinon la
ligne passe de ❔ à ✅ dans le rapport de conformité, et c'est tout.

---

## Lot 1 — ce que le joueur perd aujourd'hui sans le savoir

### 1.1 — La manette (`LOI-EXP-11`, spec §7.2) — décision **D-4**

`InputBootstrap` n'enregistre **aucun événement joypad**, alors que la spec décrit une disposition
Xbox complète. Pour un shooter montré à un professionnel (spec §1.3), c'est le manque le plus
visible du rapport.

| Fichier | Changement |
|---|---|
| `scripts/core/input_bootstrap.gd` | un `_add_joypad_action()` jumeau de `_add_key_action()` : `move_*` sur l'axe du stick gauche (avec `MOVE_DEADZONE`), `fire_primary` sur A **et** RT, `ui_options` sur Menu |

**Test** : chaque action de **jeu** (`move_*`, `fire_primary`) possède au moins un événement clavier
**et** un événement joypad. C'est la garde qui empêche qu'un ajout d'action future arrive manchot.

⚠️ **Ce qui ne se teste pas** : que ça se joue bien. À vérifier manette en main, sur Windows.
Le remappage complet (UI de reconfiguration) reste hors de ce lot — c'est un écran, pas un
branchement.

### 1.2 — L'ouverture calme (`LOI-EXP-07`, spec §5.2)

**Les premiers ennemis apparaissent à `time_offset = 0.3`.** Le joueur découvre qu'il se déplace en
se faisant tirer dessus, alors que la spec demande une « prise en main calme » en **premier point**
de sa courbe d'intensité.

| Fichier | Changement |
|---|---|
| `resources/encounters/wave_graybox_01.tres` | décaler **toute** la timeline d'un même delta — l'ordre relatif des entrées est du design déjà réglé, il ne se retouche pas ici |

⚠️ **Le delta est un arbitrage, pas une évidence.** Trois secondes vides au démarrage sont aussi
trois secondes où un spectateur ne voit rien, et le P0 du backlog vise « 2-3 minutes
irréprochables ». **Proposition : 2,0 s** — assez pour toucher les commandes, trop court pour
qu'une démo paraisse morte. À trancher en jouant, pas au journal.

**Test** : « aucun ennemi avant N secondes » — la garde qui empêche qu'une retouche de timeline
reprenne le vide sans le dire.

### 1.3 — Le hit stop (`LOI-EXP-03`)

60 à 80 ms de gel sur une destruction décisive — plaque du Leviathan, coup fatal au mini-boss.
C'est la technique la plus rentable du *game feel*, et elle est **absente** (aucune occurrence de
`time_scale` dans `scripts/`).

⚠️ **À instruire avant d'écrire, pour trois raisons vérifiées dans ce projet :**

1. `Engine.time_scale` fige **aussi** les VFX, la caméra et l'audio positionnel. Un gel qui
   suspend l'explosion qu'il est censé souligner produit l'effet inverse.
2. Le projet mesure un **temps GPU par image** ; un gel modifie cette mesure de façon trompeuse
   (cf. [`howto-mesurer-la-perf`](../../.claude/resources/howto-mesurer-la-perf.md)).
3. Le shake est **centralisé** dans `CameraDirector` — le hit stop doit l'être au même endroit, ou
   les deux effets se marcheront dessus.

**Livrable d'instruction attendu** : quel nœud gèle quoi, et ce qui continue de tourner. Puis un
test de durée (le gel dure ce qu'il annonce et **rend toujours la main**), et un jugement à l'œil.

---

## Lot 2 — la lisibilité qu'on n'a jamais mesurée

Quatre lignes ❔ du rapport. Elles ne se ferment pas par du code mais par une **mesure**, et
`ADR-0019` a montré ce que coûte de croire une mesure automatique sur une question de ressenti.

| # | Loi | Ce qu'il faut d'abord |
|---|---|---|
| 2.1 | `LOI-LIS-02`, `LOI-LIS-03` — le chunking n'a **aucun support visuel** | Regarder une couronne de 14 projectiles (Choir Mine) à **1:1**. Si elle ne se lit pas comme un groupe : orienter le sprite selon la vitesse, ou poser une traînée. **Ne rien coder avant d'avoir regardé** |
| 2.2 | `LOI-LIS-08` — profondeur d'affichage | Le jeu est en 3D sur plan logique : l'ordre de rendu dépend de la géométrie, **pas d'une règle**. Vérifier qu'aucun projectile ne passe **sous** une coque ou un décor. Si oui, c'est une règle de rendu à écrire, pas un réglage |
| 2.3 | `LOI-LIS-05` — la densité n'est pas un outil chez nous | La première chose utile n'est pas un réglage mais une **mesure** : projectiles hostiles simultanés, et fraction d'écran occupée, par phase. `BulletManager.team_count()` existe déjà — il suffit de l'échantillonner et de le journaliser. Le sous-agent `balance-prober` le lira |
| 2.4 | `LOI-ENN-04` — toucher un ennemi collé | Les canons du chasseur sont **frontaux**. Une unité collée au nez est-elle atteignable ? Jamais mesuré. Si non, c'est « une punition sans lecture », et le genre la nomme |

⚠️ **2.3 est le seul des quatre qui produise du code** — une sonde, pas une correction. Les trois
autres sont des **regards**, et deux d'entre eux peuvent se conclure par « rien à faire ».

---

## Lot 3 — la structure (cher, et pas urgent)

| # | Loi | Chantier |
|---|---|---|
| 3.1 | `LOI-LVL-07`, spec §11.3 | **`EncounterDirector`.** `WaveData`/`WaveEntry` sont déjà la file d'actions recommandée, mais elles **posent des ennemis** et rien d'autre : pas d'attente de condition, pas de synchronisation musique/caméra, pas de transmission, pas de checkpoint. Le director réel reste `graybox_root.gd`, **en dur**. C'est le plus gros item du backlog P1, et il débloque 3.2 et 3.3 |
| 3.2 | `LOI-BCL-04` (3ᵉ question) | **Un repère de progression.** Le joueur ne sait jamais *combien de temps il reste*. ⚠️ Pas sur le HUD — sa règle est qu'il n'accueille rien qui se consulte en pilotant (`fighter_hud.gd:198`) — mais sur l'**écran de transition** qui existe déjà (`scripts/vfx/phase_transition.gd`) |
| 3.3 | `LOI-RYT-04`, `LOI-RYT-05` | **Le mid-boss ne couronne l'apprentissage de rien**, parce que la phase 1 n'introduit aucun mécanisme ; et **le boss final n'enseigne rien avant de l'exiger**. C'est le même problème vu deux fois : la progression du niveau n'a pas de mécanique à enseigner. Le lot 0.2 en pose la première brique — un schéma de tir qui se lit et s'apprend |

---

## Lots bloqués sur décision

### Lot 4 — l'Overdrive (décision **D-3**)

Un seul mécanisme, et il ferme **trois** lois d'un coup : `LOI-SYS-05` (une ressource qui se
dépense, donc une économie), `LOI-SCO-02` (le conflit d'objectifs), et il crée la boucle négative
qui manque à `LOI-SYS-03` — on le dépense quand on va mal.

Prévu par la spec §9.4. **Bloqué** : Overdrive, arme secondaire et focus sont *prévus, absents et
silencieux*. Il faut décider lequel des trois états est le bon avant d'écrire une ligne.

### Lot 5 — le score comme système (décision **D-2**)

Toute la section `SCO` en dépend, et la question tient en une phrase : *l'arc se rejoue-t-il pour
le score, ou se traverse-t-il une fois ?*

Si « on rejoue » : la marche la plus courte n'est **pas** le rang — c'est `LOI-SCO-02`, qui ne
demande aucun système neuf. Il suffit qu'une chose désirable **coûte** quelque chose. Le lot 4 la
fournit.

---

## Ce que ce plan ne fait pas

- **Le pilier D** (`D-1`) — écart de **documentation**, pas de code. Il se ferme dans la spec §1.4.
- **Les checkpoints** (`D-5`) — c'est la spec §5.3 qu'il faut corriger, pas le jeu.
- **Le `README.md`** — non corrigé, sur décision de l'opérateur : la KB porte l'arc réel.
- **Aucun asset de forge.** Rien dans ce plan ne demande une image, un son ou une coque.

## Ordre recommandé

```
lot 0 (une session)  →  0.3 et 1.2 se jugent EN JOUANT, dans la foulée
   ↓
lot 1.1 manette      →  puis 1.3 hit stop, après instruction
   ↓
lot 2 : les regards d'abord (2.1, 2.2, 2.4), la sonde ensuite (2.3)
   ↓
décisions D-2 / D-3  →  lots 4 et 5
   ↓
lot 3 : EncounterDirector, quand le contenu qu'il doit orchestrer existe
```

## Definition of Done — par item, pas par lot

Chaque item est terminé quand : `./scripts/check.sh` est **vert**, le comportement est **vérifié**
(headless, et **sur Windows si c'est visuel**), la ligne correspondante du rapport de conformité est
**mise à jour** avec sa nouvelle preuve, et le commit est conventionnel, petit, à un seul objectif.

⚠️ **La mise à jour du rapport de conformité fait partie du travail.** Un écart fermé mais toujours
listé comme ouvert coûte la prochaine session — c'est exactement la dette que ce corpus a servi à
révéler.
