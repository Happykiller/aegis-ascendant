---
titre: Conformité d'Aegis Ascendant au corpus de lois du shoot vertical
type: reference
statut: actif
maj: 2026-08-27
---

# Conformité — Aegis Ascendant

Ce que le jeu fait, loi par loi. Le corpus est dans [`bible/`](bible/README.md) et ne parle d'aucun
jeu ; **tout le spécifique Aegis est ici**.

## Comment lire

| État | Signification |
|---|---|
| ✅ **tenue** | vérifié dans le code, les données ou une décision écrite |
| ⚠️ **partielle** | tenue par endroits, ou tenue sans être outillée |
| ❌ **écartée** | **délibérément** non suivie, avec une raison. Ce n'est pas une dette |
| ❌ **absente** | non suivie, sans décision — une dette ou un oubli |
| ❔ **non vérifiée** | jamais mesurée ni jouée sur ce point |
| — | sans objet pour ce jeu |

⚠️ **Les états vieillissent.** Chaque section porte sa date de vérification et pointe des fichiers
précis. Avant de s'appuyer sur une ligne, vérifier qu'elle est encore vraie : un point de reprise
faux coûte plus qu'un point de reprise absent.

> **Ce rapport ne décide de rien.** Il constate. Les écarts qui appellent un arbitrage sont
> rassemblés en fin de page, et attendent l'opérateur.

---

## Lisibilité — `LIS`

*Vérifié le 2026-08-25.*

| Loi | État | Preuve |
|---|---|---|
| `LOI-LIS-01` couleurs réservées | ✅ tenue | **écrite dans le shader** : `shaders/space_background.gdshader` — le fond « ne touche jamais au cyan réservé au tir allié ni au corail réservé au tir ennemi ». Appliquée le jour même au bolide du survol de lune (`ADR-0027`) |
| `LOI-LIS-02` grouper | ⚠️ partielle | les salves (`FAN`, `RADIAL`, `AIMED`) produisent des groupes, mais **rien ne garantit qu'un groupe se lise comme un groupe** |
| `LOI-LIS-03` renfort visuel | ❌ absente | aucune orientation de sprite selon l'angle, aucune traînée sur les trajectoires inhabituelles |
| `LOI-LIS-04` annoncer l'attaque | ✅ tenue | `EnemyReaction` : `alert_radius` où l'unité s'éveille **et le montre**, puis `windup_time`. Le Leviathan télégraphie ses bascules par bannière, secousse et son. Le contrat « ce qui s'allume part » est écrit dans le fichier |
| `LOI-LIS-05` densité ≠ difficulté | ❔ non vérifiée | **aucune notion de densité** dans le code ni les Resources. Les vagues sont composées à l'intuition |
| `LOI-LIS-06` espace négatif | ❔ non vérifiée | jamais traité comme une donnée |
| `LOI-LIS-07` vitesse des projectiles | ✅ tenue | spec §11.2 : « davantage de projectiles lents et lisibles ». Choix conscient, cohérent avec `LOI-LVL-01` |
| `LOI-LIS-08` rien de mortel caché | ❔ non vérifiée | jeu 3D sur plan logique : l'ordre de rendu dépend de la géométrie, **pas d'une règle explicite** |

Zone calme centrale : ✅ le fond s'assombrit au tiers central (`center_calm`) — « l'art ne doit
jamais disputer l'attention au vaisseau et aux balles ».

## Ennemis et vagues — `ENN`

*Vérifié le 2026-08-25.*

| Loi | État | Preuve |
|---|---|---|
| `LOI-ENN-01` couverture des rôles | ✅ tenue | pression : les neuf Needle Scout, le Crescent Interceptor. Interdiction de zone : **Null Maw** (`GRAVITY_WELL`), Choir Mine en barrage. Défi direct : **Leech Drone** (`HOMING`), les deux boss. Plus un quatrième rôle que le genre nomme peu : le **Shield Carrier** (`SHIELD_AURA`), priorité de cible **pure** |
| `LOI-ENN-02` priorité lisible | ⚠️ partielle | le Shield Carrier est le mécanisme même — sa **portée ne se voyait pas**, corrigée en anneau (pas en dôme : trois volumes ont rendu un aplat, condamnés par leur surface) |
| `LOI-ENN-03` PV du popcorn | ✅ tenue | Choir Mine 12 PV, Leech Drone 10 — une salve suffit |
| `LOI-ENN-04` toucher de près | ❔ non vérifiée | les canons du chasseur sont frontaux ; une unité collée au nez est-elle atteignable ? **jamais mesuré** |
| `LOI-ENN-05` approcher paie | ✅ tenue | `pull_speed_max` de la Null Maw plafonné à 7,0 contre 14,0 de vitesse joueur, et `GravityWell.leaves_room()` l'**impose** |
| `LOI-ENN-06` couloirs Toaplan | ❌ absente | les vagues posent des `spawn_plane_position` en unités monde, **pas en couloirs**. Le champ d'astéroïdes emploie quatre colonnes échelonnées — du Toaplan sans le nommer |
| `LOI-ENN-07` zigzag | ✅ tenue | neuf courbes distinctes (`WEAVE`, `ARC_CROSS`, `SERPENTINE`, `SPIRAL`, `STRAFE_RUN`…) |
| `LOI-ENN-08` chevauchement | ✅ tenue | vague 1 (nuées qui se recouvrent) et champ d'astéroïdes (sangsues pendant la descente des puits) |
| `LOI-ENN-09` tout l'écran | ✅ tenue | terrain de 28 × 16 unités employé de bord à bord |
| `LOI-ENN-10` régimes selon performance | ❌ absente | comportement unique par unité. `chase_time` de la sangsue (8 s) est le seul filet |
| `LOI-ENN-11` combiner | ✅ tenue | principe explicite du champ d'astéroïdes : trois unités **superposées** au lieu de successives |

## Niveau et rythme — `RYT`

*Vérifié le 2026-08-25, mis à jour le 2026-08-26.*

| Loi | État | Preuve |
|---|---|---|
| `LOI-RYT-01` structure fractale | ⚠️ partielle | ouvrir ✅ (V de Needle Scout), développer ✅ (familles par blocs sur ~50 s), intensifier ✅ (tenaille finale) |
| `LOI-RYT-02` un mécanisme à la fois | ✅ tenue | **par construction** dans le champ d'astéroïdes : mines seules, puis puits, puis sangsues, puis tout ensemble |
| `LOI-RYT-03` le repos n'est pas du vide | ✅ tenue | la phase 2 est conçue comme respiration entre deux boss (`ADR-0027`), et **la musique le dit** : 108 BPM au lieu de 132 |
| `LOI-RYT-04` mid-boss = climax du mécanisme | ⚠️ partielle | le Choir Harvester clôt la phase 1 — donc bien *au milieu de l'arc* — mais **il ne couronne l'apprentissage de rien** : aucun mécanisme n'est introduit pendant la phase 1 |
| `LOI-RYT-05` le boss final résume | ⚠️ partielle | le Leviathan a ses propres mécaniques (plaques, plongée, flux) **jamais enseignées avant** |
| `LOI-RYT-06` repères | ✅ tenue | deux boss, changement complet de décor en phase 2, bannières |
| `LOI-RYT-07` le décor ne ment pas | ⚠️ **vigilance active** | un astéroïde décoratif frôlait le chasseur au lot 2, écarté du couloir de vol. L'arbitrage « astéroïdes solides, lune décor » **rouvre exactement ce problème** |

Ralentir avant la fin : ✅ **livré le 2026-08-26** — c'était le seul ❌ de cette section.

## Boss — `BOS`

*Vérifié le 2026-08-25.*

| Loi | État | Preuve |
|---|---|---|
| `LOI-BOS-01` pièce par pièce | ✅ tenue | quatre plaques à abattre, **une de moins à chaque cycle** : « le boss se répare de plus en plus mal » |
| `LOI-BOS-02` phases distinctes | ✅ tenue | armure et plongée n'ont rien en commun — l'une dehors, l'autre **dans une arène dédiée** (`ADR-0025`) |
| `LOI-BOS-03` la barre annonce | ✅ tenue | **corrigé** (`ADR-0023`) : le HUD recevait `structure_ratio()` (la cible courante) au lieu de `fight_ratio()` — six remplissages se lisaient comme une boucle. La mesure juste existait et n'allait qu'à la musique |
| `LOI-BOS-04` patterns, pas chaos | ✅ tenue | **garanti par construction** (`ADR-0026`) : dégâts par plongée plafonnés à un tiers — trois cycles vrais par construction, non par calibrage |
| `LOI-BOS-05` signal reconnaissable | ✅ tenue | chaque bascule : bannière, secousse, son, changement musical. Le Choir Harvester rend explicitement ses tirs déviés (`deflected`), « tirer dessus sans rien produire se lit comme un défaut, pas comme une armure » |
| `LOI-BOS-06` le boss appartient au niveau | ⚠️ écart connu | ni l'armure démontable, ni la plongée, ni le flux n'ont été enseignés avant |

> **Les boss sont la partie la mieux tenue du projet — et chacun de ces points l'a été *après* un
> playtest, jamais du premier coup.** `ADR-0019` (combat ramené de 3 min à 67 s), `ADR-0023` (la
> jauge qui bouclait), `ADR-0024` (le flux dimensionné sur la mauvaise cadence), `ADR-0026` (le
> plafond) : quatre décisions, quatre parties jouées. **Aucune mesure automatique n'a jamais rien vu
> de tout cela** — c'est [`LOI-EXP-12`](bible/10-experience-joueur.md) en pratique.

## Puissance, mort, récupération — `PUI`

*Vérifié le 2026-08-25, complété le 2026-08-27.*

| Loi | État | Preuve |
|---|---|---|
| `LOI-PUI-01` l'arme monte | ✅ tenue | cinq niveaux (`LV.1` à l'écran), `Pickup.Kind.POWER`, cadence ×0,8 dès le niveau 2, flux supplémentaires aux niveaux 3/4/5 |
| `LOI-PUI-02` familles d'armement | ⚠️ **une seule** | ni laser, ni options. Le chasseur a ses canons de nez, et c'est tout |
| `LOI-PUI-03` la mort n'enterre pas | ✅ tenue | et **au-delà** du genre |
| `LOI-PUI-04` perte partielle | ❌ **écartée, délibérément** | `_destroy()` (`player_fighter_controller.gd:263`) ne touche **pas** à `_power_level` : on ne perd **aucune** puissance. Plus généreux que la spec §5.3, qui n'exige qu'« au moins un niveau » conservé. **C'est le pilier A appliqué sans réserve** |
| `LOI-PUI-05` nettoyage + invulnérabilité | ✅ tenue | **ajouté le 2026-08-25** après vérification : il **manquait**. `BulletManager.clear_team(ENEMY)` à la mort du joueur (`graybox_root.gd:961`) ; 1,2 s de pause puis **2,0 s** d'invulnérabilité |
| `LOI-PUI-06` bomb buffer | — | sans objet : **il n'y a pas de bombe** |

Écran d'échec : ❌ **il n'en existe aucun** — perdre tous les chasseurs appelle `continue_run()` et
la partie repart, sans écran ni choix. Au P0 du backlog.

## Score et rang — `SCO`

*Vérifié le 2026-08-25.*

| Loi | État | Preuve |
|---|---|---|
| `LOI-SCO-01` faire faire ce qu'on ne ferait pas | ❌ absente | le score est une **conséquence mécanique du fait de jouer** |
| `LOI-SCO-02` objectifs en conflit | ❌ absente | rien ne se gagne en prenant un risque, rien ne se perd en jouant prudemment |
| `LOI-SCO-03` chaînage | ❌ absente | — |
| `LOI-SCO-04` linéaire/exponentiel | — | sans objet sans chaînage |
| `LOI-SCO-05` agressif/défensif | — | idem |
| `LOI-SCO-06` le rang | ❌ absente | la difficulté est **entièrement scriptée** : la timeline d'une `WaveData`, et les cycles du boss |

Ce qui existe : `GameState.add_score()`. Chaque ennemi vaut son `score_value` (90 la Choir Mine, 140
la Null Maw, 160 la Leech Drone), le mini-boss 5 000, le boss final 20 000, un ramassage 500. Le
rapport de mission attribue un **rang par seuils** — 12 000 / 25 000 / 40 000
(`mission_report.gd:172`).

⚠️ **C'est le plus grand écart du rapport, et ce n'est pas forcément un défaut.** Un système de score
profond sert une pratique de répétition (le 1CC, le classement). Rien dans la spec ne dit qu'Aegis
vise cela, et le P0 du backlog parle d'une **démo irréprochable**, pas d'un jeu à scoring. Voir la
décision **D-2** en fin de page.

## Piliers et intention — `PIL`

*Vérifié le 2026-08-27.*

La spec §1.4 pose **cinq piliers**, nommés A à E.

| Pilier (spec §1.4) | État |
|---|---|
| **A** — Puissance accessible | ✅ **tenu, et au-delà** — voir `LOI-PUI-04` |
| **B** — Lisibilité parfaite (< 200 ms) | ⚠️ tenu en partie — c'est la section `LIS` entière |
| **C** — Échelle évolutive | ✅ tenu — Needle Scout → Choir Harvester → Pale Leviathan, plus la citadelle |
| **D** — Transformation de la boucle | ❌ **sans implémentation** — voir ci-dessous |
| **E** — Originalité juridique | ✅ tenu, avec l'exception unique et actée du Specter-9 (`ADR-0014`) |

| Loi | État | Preuve |
|---|---|---|
| `LOI-PIL-01` trois à cinq | ✅ tenue | cinq, en haut de la fourchette |
| `LOI-PIL-02` une phrase, langage actif | ✅ tenue | les cinq énoncés tiennent en une phrase |
| `LOI-PIL-03` un ressenti, pas une fonctionnalité | ❌ **absente** | les cinq nomment des **fonctionnalités**, sauf le A — seul écrit comme un ressenti (« le joueur doit être puissant rapidement ») |
| `LOI-PIL-04` le test du filtre | ❔ non vérifiée | aucun usage documenté des piliers comme filtre de décision |
| `LOI-PIL-05` couper | ❔ non vérifiée | aucune suppression attribuée à un pilier |
| `LOI-PIL-06` pilier sans implémentation | ❌ **violée** | voir ci-dessous |

### ⚠️ Le pilier D n'a plus d'objet

Il décrit le transfert de commande vers la citadelle : on quitte le chasseur, on pilote la
forteresse, la boucle change de nature. **`ADR-0010` (2026-07-19) a supprimé cette phase** — un seul
vaisseau du début à la fin, parce que le changement de véhicule cassait le flow et la lisibilité de
l'arme.

Le pilier est resté dans la spec **huit jours de plus que son implémentation**, et personne ne l'a
rouvert depuis. C'est très exactement ce que `LOI-PIL-03` prédit : **un pilier qui nomme une
fonctionnalité meurt avec elle**, sans bruit.

Ce qui, aujourd'hui, remplit encore sa **fonction** — rompre la boucle, changer la nature de l'acte
— c'est l'**entrée dans le noyau** du Pale Leviathan (`ADR-0025`) : coquille écartée, aspiration,
autopilote, caméra qui plonge, tir plein cadre, éjection. La boucle est suspendue et remplacée, une
trentaine de secondes, trois fois.

## Boucle de jeu — `BCL`

*Vérifié le 2026-08-27.*

| Loi | État | Preuve |
|---|---|---|
| `LOI-BCL-01` trois échelles | ✅ tenue | **micro** : `fire_interval = 0,12 s`, tir automatique — l'acte du joueur est **se placer**, et une décision se paie en moins d'une seconde. **Méso** : la phase (champ d'astéroïdes 45–60 s ; boss en trois cycles). **Macro** : la partie de 12–15 min |
| `LOI-BCL-02` récompense avant 60 s | ✅ tenue | **4 ennemis détruits suffisent** |
| `LOI-BCL-03` compris en minutes | ✅ tenue | quelques secondes suffisent |
| `LOI-BCL-04` les quatre questions | ⚠️ **deux sur quatre** | objectif ✅, tâches ✅. **Combien de temps ❌** — aucun indicateur de progression hors jauge de boss (`ADR-0023`). **Ce qui reste acquis ❌** — rien entre deux parties, hors score |
| `LOI-BCL-05` la micro nourrit la macro | ⚠️ partielle | la macro-boucle est le **rang de fin** et rien d'autre ; le Codex se consulte, il ne se débloque pas |

### La cadence de récompense est **déterministe**

`PickupManager.roll_drop()` ne tire rien au sort malgré son nom : un bonus **tous les 4 ennemis**
(`_DROP_EVERY := 4`), un Power Core **un bonus sur trois** (`_POWER_EVERY := 3`) — soit **un niveau
de puissance tous les 12 ennemis**. Les deux autres suivent un cycle fixe `bouclier → score →
bouclier`.

⚠️ **À connaître avant de toucher au bestiaire** : la montée en puissance est indexée sur le
**nombre d'ennemis**, pas sur le temps. Ajouter du popcorn accélère le power-up ; ajouter des
ennemis coriaces le ralentit, à durée de phase identique.

## Règles et systèmes — `SYS`

*Vérifié le 2026-08-27.*

| Loi | État | Preuve |
|---|---|---|
| `LOI-SYS-01` deux familles | — | vocabulaire |
| `LOI-SYS-02` positive sans contrepoids | ⚠️ **écartée, assumée** | **le jeu n'a que des boucles positives** — voir ci-dessous |
| `LOI-SYS-03` les deux ensemble | ❌ absente | aucune boucle négative |
| `LOI-SYS-04` MDA | ✅ tenue | rien à corriger : c'est une loi de méthode |
| `LOI-SYS-05` ressource dépensable | ❌ **absente** | **aucune ressource ne se dépense** — voir ci-dessous |
| `LOI-SYS-06` règle cachée | ✅ tenue | par absence : aucun système adaptatif caché |

### Inventaire des boucles

| Boucle | Sens | Chemin |
|---|---|---|
| **Puissance** | **positive** | tuer → bonus tous les 4 → Power Core tous les 12 → cadence ×0,8 et flux en plus → tuer plus vite |
| **Bouclier** | **positive** | ne pas être touché 3 s → régénération à 12 /s → encaisser plus tard |
| **Mort** | **neutre** | une vie en moins, **aucune puissance** perdue |
| **Cycles du boss** | scriptée | l'armure revient amoindrie : 4 plaques, puis 3, puis 2 |

Les deux boucles positives **se renforcent l'une l'autre** et rien ne pousse en sens inverse. C'est
la configuration dont `LOI-SYS-02` dit qu'elle s'emballe — **mais elle est ici voulue** (pilier A),
et le contrepoids assumé est la **timeline scriptée** : la difficulté monte parce que la phase
suivante est plus dure, pas parce que le joueur va bien.

### L'économie : quatre ressources, aucune ne se dépense

| Ressource | Se gagne | Se dépense | Arbitrage |
|---|---|---|---|
| Bouclier (100) | régénération, bonus (+35) | en encaissant | ❌ subi |
| Vies (3) | — | en mourant | ❌ continues illimités |
| Puissance (1→5) | 1 bonus / 12 ennemis | **jamais** | ❌ |
| Score | ennemis, bonus, phases | **jamais** | ❌ |

Les trois mécanismes que la spec prévoyait pour cela — **arme secondaire** (§9.3), **Overdrive**
(§9.4), **focus** (§7.1) — **n'existent dans aucun script** : `InputBootstrap` ne déclare que
`move_*`, `fire_primary` et `ui_options`. Ce ne sont pas des réglages manquants, ce sont des
systèmes non écrits.

## Expérience joueur — `EXP`

*Vérifié le 2026-08-27.*

| Loi | État | Preuve |
|---|---|---|
| `LOI-EXP-01` trois choses alignées | ✅ tenue | réponse : `accel_time = 0,18 s`, sous les 0,25 s exigés — **et `validate()` échoue au-delà**. Retour : gerbe teintée par camp, flash de coque, catégories d'explosion, texte flottant, cue audio par bonus |
| `LOI-EXP-02` ne pas juicer un jeu qui répond mal | ✅ tenue | l'ordre a été respecté de fait |
| `LOI-EXP-03` hit stop | ❌ **absent** | aucune occurrence de `time_scale` dans `scripts/`. Le screen shake existe, centralisé à **trauma** (intensité en trauma²) |
| `LOI-EXP-04` accepter l'intention | — | sans objet : aucune commande n'a de fenêtre (pas de saut, pas de dash, pas de bombe) |
| `LOI-EXP-05` ni ennui ni angoisse | ❔ non vérifiée | « vérifier que la difficulté est facile mais nerveuse » est au P0 du backlog |
| `LOI-EXP-06` puissance puis baisse | ❌ **absente** | la montée en puissance est **continue** (1 Power Core / 12 ennemis) et ne provoque **aucun palier de respiration**. Le joueur ne vit jamais le moment « je suis devenu fort, et ça se voit » |
| `LOI-EXP-07` apprendre en jouant | ❌ **absente** | **les premiers ennemis apparaissent à `time_offset = 0.3`** (`wave_graybox_01.tres`), en deux nuées de quatre. La spec §5.2 demande pourtant une « prise en main calme » en premier point de sa courbe d'intensité. Ni tutoriel, ni écran de commandes, ni espace vide initial |
| `LOI-EXP-08` effet invisible = défaut | ✅ **tenue, et c'est une loi née ici** | cinq mécaniques prises en défaut le 2026-08-26 : freinage de la sangsue, champ protecteur, puits gravitique, sursis de mine. Capitalisée dans [`KB/DAF/signaux.md`](../KB/DAF/signaux.md) |
| `LOI-EXP-09` contrat joueur | ⚠️ partielle | la loi des signaux en couvre le fond, **sans le formalisme** SEE/UNDERSTAND/FEEL/ANTICIPATE/DECIDE ni la ligne « à ne jamais produire » — qui aurait attrapé le lien du Shield Carrier lu comme « je suis ralenti » |
| `LOI-EXP-10` jamais la couleur seule | ✅ **tenue, et surveillée** | un cue audio par type de bonus, « parce qu'un bonus doit être identifiable sans le regarder » (`graybox_root.gd:253`) ; la charte créative l'interdit explicitement |
| `LOI-EXP-11` socle d'accessibilité | ❌ **le plus gros écart de la page** | voir ci-dessous |
| `LOI-EXP-12` fonctionner ≠ validé | ✅ **tenue en pratique** | c'est la leçon des quatre ADR de boss : aucune mesure automatique n'a rien vu |

### Le socle d'accessibilité, ligne par ligne

| Ligne | État |
|---|---|
| Remappage | ❌ **absent** — `InputBootstrap` déclare les actions en dur ; son propre commentaire dit que l'UI de remappage « viendra plus tard » |
| Manette | ❌ **absente** — seul `_add_key_action()` existe, **aucun événement joypad** n'est enregistré, alors que la spec §7.2 décrit une disposition Xbox complète |
| Secousse réductible | ⚠️ **codée mais injoignable** — `CameraDirector.shake_multiplier` documente « 0 désactive entièrement » (spec §16.3), et le menu d'options n'expose que **4 volumes + la pixelisation** |
| Couleur seule | ✅ tenue |
| Choix de difficulté | ❌ un seul réglage, non exposé |
| Clignotement | ⚠️ l'invulnérabilité fait clignoter la coque à **~18 Hz** — sur le vaisseau seul, pas en plein écran, mais c'est la zone que le joueur fixe |

## Patterns de tir — `PAT`

*Vérifié le 2026-08-27.*

| Loi | État | Preuve |
|---|---|---|
| `LOI-PAT-01` le nombre n'est pas le sujet | ✅ tenue | la bibliothèque est construite sur l'intention, pas sur le compte |
| `LOI-PAT-02` cinq familles | ⚠️ **quatre sur cinq** | `SINGLE` (ligne), `FAN` (éventail aveugle, 62°), `AIMED` (éventail visé, 12°), `RADIAL` (anneau), `NONE`. **La pile n'existe pas** : aucun schéma ne fait varier la vitesse dans une salve |
| `LOI-PAT-03` la parité | ⚠️ **violée sans le savoir** | voir ci-dessous |
| `LOI-PAT-04` semences d'angle | ⚠️ partielle | fixe et visée présentes ; `RADIAL_PHASE = 0,5` entrelace les couronnes — « les trous de la première sont bouchés par la seconde, **donc rester immobile ne paie jamais** » |
| `LOI-PAT-05` composer | ✅ tenue | `RADIAL_PHASE` est exactement « régularité plus une légère fluctuation » |
| `LOI-PAT-06` désigner l'esquive | ⚠️ partielle | la macro-esquive n'est demandée que par les couronnes de la Choir Mine |
| `LOI-PAT-07` forme, pas constantes | ✅ **tenue, et testée** | la règle est écrite dans `enemy_fire.gd` et **un test de variété la vérifie** : « FAN et AIMED ne diffèrent pas par leur ouverture, ils diffèrent parce que l'un est aveugle et l'autre voit » |

### ⚠️ `FAN` et `AIMED` ne sont employés par aucune unité de vague

`fire` vaut `SINGLE` par défaut (`enemy_data.gd:28`) et **aucun `.tres` d'ennemi ne le surcharge**,
sauf trois passages en `NONE` (Leech Drone, Null Maw, Shield Carrier) et **un seul** en `RADIAL`
(Choir Mine, 14 balles).

Les neuf Needle Scout et le Crescent Interceptor tirent donc **tous une balle droite**. L'éventail
aveugle et l'éventail visé sont **écrits, testés, documentés — et jamais joués**. Le seul schéma qui
punit l'immobilité au niveau des vagues n'est employé nulle part. **Deux lignes de `.tres` le
mettraient en jeu.**

### ⚠️ La parité de l'éventail visé du boss change toute seule

`Pattern.AIMED_SPREAD` (`boss_controller.gd:288`) tire `count = 3 + _phase` balles :

| Phase | Balles | Parité | Ce que le joueur vit |
|---|---:|---|---|
| 0 | 3 | impair | une balle **sur l'axe** — l'immobilité tue |
| 1 | 4 | **pair** | l'axe est **vide** — l'immobilité devient sûre |
| 2 | 5 | impair | l'immobilité tue de nouveau |

Personne n'a décidé cela : c'est l'arithmétique de `3 + phase`. La phase 1 est donc, pour ce pattern,
**plus permissive** que la phase 0 — l'inverse de ce qu'une montée de phase promet. `Pattern.FAN`
(`7 + 2 × phase`) reste impair.

## Level design — `LVL`

*Vérifié le 2026-08-27.*

| Loi | État | Preuve |
|---|---|---|
| `LOI-LVL-01` rapport vaisseau/écran | ✅ tenue | `GameplayPlane.BOUNDS` = **28 × 16 unités** (`gameplay_plane.gd:12`), hitbox de rayon **0,25** — **1,8 % de la largeur**. Franchement « petit vaisseau, grand écran » : beaucoup d'éléments, projectiles lents, temps d'anticipation long |
| `LOI-LVL-02` révéler puis combiner | ✅ tenue | principe explicite du champ d'astéroïdes |
| `LOI-LVL-03` décor = progression | ⚠️ partielle | `BackdropLandmark` tient planètes et nébuleuses **hors du couloir central** ; `MoonFlyby` donne son décor propre à la phase 2. Mais ils **dérivent et bouclent** : ils disent « on est dans cette phase », pas « on en est aux deux tiers » |
| `LOI-LVL-04` faire bouger | ✅ tenue | neuf courbes distinctes |
| `LOI-LVL-05` pas de surgissement | ✅ tenue | spawn à `y = 9,5`, au-dessus du bord haut (`y_max = 8`) : les coques **entrent** dans le champ |
| `LOI-LVL-06` deux patterns, deux apparences | ❔ **non vérifiée** | les `ProjectileData` diffèrent par unité, mais rien ne garantit que **deux patterns simultanés** emploient des projectiles distincts. Le champ d'astéroïdes superpose trois unités — **c'est là que ça se joue**, et c'est dix secondes de jeu à vérifier |
| `LOI-LVL-07` file d'actions | ✅ tenue | `WaveData` / `WaveEntry` sont littéralement la structure : `time_offset`, `enemy_scene`, `spawn_plane_position`, `count`, `spacing`. ⚠️ Pas encore l'`EncounterDirector` de la spec §11.3 : la file pose des ennemis, elle n'attend pas une condition et ne synchronise rien |
| `LOI-LVL-08` checkpoint ou reprise | ❌ **écartée, délibérément** | le mot « checkpoint » **n'apparaît dans aucun script**, alors que la spec §5.3 en demande deux. Le jeu fait la troisième voie : reprise sur place à `(0, −5)`, sans perte, continues illimités. Évite le *Gradius syndrome* par construction — et supprime l'enjeu de la mort |

⚠️ `BOUNDS` est un **paramètre d'équilibrage majeur déguisé en constante technique**. S'il bouge un
jour, c'est un ADR, pas un ajustement (`LOI-LVL-01`).

---

## Les écarts qui appellent une décision

Cinq, et aucun ne se tranche seul.

### D-1 — Le pilier D est orphelin (`LOI-PIL-06`)

Trois issues : **le réécrire** autour de l'entrée dans le noyau, qui a repris sa fonction ; **le
retirer** et assumer quatre piliers ; **lui redonner une implémentation** — mais `ADR-0010` a tranché
après usage.

### D-2 — L'arc se rejoue-t-il pour le score, ou se traverse-t-il une fois ?

Elle commande toute la section `SCO`. Les deux réponses sont défendables et mènent à des chantiers
très différents. Si la réponse est « on rejoue », la marche la plus courte n'est **pas** le rang :
c'est `LOI-SCO-02`, le conflit d'objectifs, qui ne demande aucun système nouveau.

### D-3 — Overdrive, arme secondaire et focus : à écrire, ou hors périmètre ?

Prévus par la spec (§9.3, §9.4, §7.1), absents du code, et **silencieux**. C'est le pire des états.
Un seul d'entre eux — l'Overdrive — apporterait d'un coup `LOI-SYS-05` (une ressource dépensable),
`LOI-SCO-02` (le conflit) et une boucle négative naturelle.

### D-4 — La manette (`LOI-EXP-11`)

Décrite par la spec §7.2, inexistante. Pour un shooter montré à un professionnel (spec §1.3), c'est
probablement le manque le plus visible du rapport.

### D-5 — Les checkpoints de la spec §5.3 (`LOI-LVL-08`)

Ils n'existent pas et **rien ne les réclame** : la reprise sur place fait le travail, mieux et plus
simplement. Le plus honnête serait sans doute de **retirer la ligne de la spec** — mais la spec est
source de vérité et ce rapport ne la modifie pas.

## Ce qui est gratuit, et qui n'attend rien

Trois gestes qui ne demandent aucun arbitrage :

1. **Exposer `shake_multiplier`** dans le menu d'options. Le système existe, la spec l'exige (§7.3),
   les référentiels d'accessibilité le classent en niveau de base — il manque **une ligne d'UI** à
   côté de la case « pixelisation », déjà branchée sur le même chemin de réglages persistants.
2. **Donner `FAN` et `AIMED` à des unités de vague** — deux lignes de `.tres`. ⚠️ En choisissant la
   **parité** volontairement (`LOI-PAT-03`), pas en laissant `burst_count = 5` décider du sens.
3. **Vérifier `LOI-LVL-06` en jouant** le champ d'astéroïdes : les projectiles des trois unités
   simultanées se distinguent-ils ? Dix secondes de jeu.
