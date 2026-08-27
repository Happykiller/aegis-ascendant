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
>
> **Ce qu'on en fait** est dans [`docs/plans/2026-08-27-conformite-bible.md`](../plans/2026-08-27-conformite-bible.md) :
> quel fichier, quel test, dans quel ordre — et ce qu'on ne ferme **pas**, parce qu'un écart assumé
> n'est pas une dette.

---

## Lisibilité — `LIS`

*Vérifié le 2026-08-25.*

| Loi | État | Preuve |
|---|---|---|
| `LOI-LIS-01` couleurs réservées | ✅ tenue | **écrite dans le shader** : `shaders/space_background.gdshader` — le fond « ne touche jamais au cyan réservé au tir allié ni au corail réservé au tir ennemi ». Appliquée le jour même au bolide du survol de lune (`ADR-0027`) |
| `LOI-LIS-02` grouper | ⚠️ **partielle, et on sait désormais où** (2026-08-27) | ✅ **l'anneau se lit comme un anneau** — vérifié à **1:1** sur une couronne de 14 balles de Choir Mine : géométrie régulière, écart constant, le groupe est immédiat. ⚠️ **La salve visée, non** : les grappes de trois du lancier se fondent en une masse molle (capture t≈34 s). L'écart n'est pas la couronne, c'est l'éventail serré |
| `LOI-LIS-03` renfort visuel | ❌ absente | aucune orientation de sprite selon l'angle, aucune traînée sur les trajectoires inhabituelles |
| `LOI-LIS-04` annoncer l'attaque | ✅ tenue | `EnemyReaction` : `alert_radius` où l'unité s'éveille **et le montre**, puis `windup_time`. Le Leviathan télégraphie ses bascules par bannière, secousse et son. Le contrat « ce qui s'allume part » est écrit dans le fichier |
| `LOI-LIS-05` densité ≠ difficulté | ⚠️ **mesurée pour la première fois** (2026-08-27) | `DensityProbe` (`--density-probe`) rend un profil par seconde. Résultats ci-dessous — et le profil de la phase 1 est **une ligne plate avec un seul pic** |
| `LOI-LIS-06` espace négatif | ❔ non vérifiée | jamais traité comme une donnée |
| `LOI-LIS-07` vitesse des projectiles | ✅ tenue | spec §11.2 : « davantage de projectiles lents et lisibles ». Choix conscient, cohérent avec `LOI-LVL-01` |
| `LOI-LIS-08` rien de mortel caché | ❌ **aucune règle** (2026-08-27) | les balles rendent à **Y = 0** — l'ordonnée n'est jamais écrite dans le buffer du `MultiMesh` — et les coques aussi (`plane_lift = 0` hors plongée dans le noyau). **Balles et coques sont coplanaires** : c'est la géométrie du maillage et le tampon de profondeur qui décident, pas une règle. ⚠️ Aucun cas observé pour l'instant (les balles passent proprement sur un astéroïde, vérifié à 1:1), mais le genre ordonne explicitement les plans — nous n'ordonnons rien |

Zone calme centrale : ✅ le fond s'assombrit au tiers central (`center_calm`) — « l'art ne doit
jamais disputer l'attention au vaisseau et aux balles ».

### La densité, enfin chiffrée (2026-08-27)

Premier profil du projet, relevé en mode démo sur l'arc complet (`--density-probe`) :

| Phase | Pic | Moyenne des pics par seconde | Forme du profil |
|---|---:|---:|---|
| `FIGHTER_WAVES` | **30** | 4,7 | ⚠️ **une ligne plate et un seul pic** : 0 à 5 balles pendant **34 s**, puis 27–30 entre t=35 et t=39 (la tenaille finale), puis retour à 0–3 |
| `MINI_BOSS` | 12 | 6,6 | régulier, sans creux |

Ce que le chiffre dit, et qu'aucune relecture n'aurait donné : **la phase 1 est très peu dense
pendant sa première moitié**. Le genre traite la densité comme un axe à deux dimensions — spatiale
et temporelle ; nous n'avons ici qu'un créneau. C'est à rapprocher du P0 du backlog (« vérifier que
la difficulté est facile mais nerveuse »), qui devient une question mesurable au lieu d'une
impression.

⚠️ La ligne de synthèse (« PIC DE LA PARTIE ») ne s'écrit qu'à la **sortie propre** du jeu : un run
interrompu par un `timeout` la perd. Les lignes par seconde, elles, portent tout.

### L'angle mort du tir rapproché (2026-08-27)

Trois mesures, et une addition :

| Terme | Valeur | Source |
|---|---:|---|
| Canons de nez (`Muzzle_L/R`) | **+1,070** u devant le centre | coque `specter_9.glb`, relevée |
| Déplacement avant le premier test de collision | **+0,40** u | `pulse_shot` à 24 u/s, physique à 60 Hz — `step()` avance **puis** résout |
| Portée d'un impact | **0,57** u | rayon de balle 0,12 + hitbox d'un Needle Scout 0,45 |

**Un ennemi dont le centre est à moins de 0,90 u devant le chasseur ne peut pas être touché par les
canons de nez.**

⚠️ Et rien ne l'en chasse : **aucun chasseur ordinaire n'inflige de dégât de contact** (seules la
sangsue, la mine et les pièces de boss le font). Une unité posée là serait **inoffensive et
invulnérable** — l'impasse exacte que `LOI-ENN-04` nomme.

Détail non évident, et qui aggrave le cas : les canons d'aile et de bout d'aile sont modélisés
**derrière** le centre du chasseur. L'angle mort **se referme donc en montant en puissance** — le
joueur le subit précisément quand il est le plus faible.

✅ **Fermé le 2026-08-27** : les bolts naissent sur l'axe du chasseur, l'éclair de bouche reste au
canon. La coque n'a pas bougé — c'est le **point de naissance** de la balle qui a été découplé de
l'arme, exactement comme la hitbox l'est déjà du modèle. Vérifié à 1:1 : le rendu est **neutre**,
le joueur ne verra que l'ennemi collé qui meurt enfin.

## Ennemis et vagues — `ENN`

*Vérifié le 2026-08-25.*

| Loi | État | Preuve |
|---|---|---|
| `LOI-ENN-01` couverture des rôles | ✅ tenue | pression : les neuf Needle Scout, le Crescent Interceptor. Interdiction de zone : **Null Maw** (`GRAVITY_WELL`), Choir Mine en barrage. Défi direct : **Leech Drone** (`HOMING`), les deux boss. Plus un quatrième rôle que le genre nomme peu : le **Shield Carrier** (`SHIELD_AURA`), priorité de cible **pure** |
| `LOI-ENN-02` priorité lisible | ⚠️ partielle | le Shield Carrier est le mécanisme même — sa **portée ne se voyait pas**, corrigée en anneau (pas en dôme : trois volumes ont rendu un aplat, condamnés par leur surface) |
| `LOI-ENN-03` PV du popcorn | ✅ tenue | Choir Mine 12 PV, Leech Drone 10 — une salve suffit |
| `LOI-ENN-04` toucher de près | ✅ **tenue** (2026-08-27) | l'angle mort de **0,90 u** est **fermé** : le bolt naît sur l'axe du chasseur (`BOLT_FORWARD_OFFSET = 0`) au lieu du bout du canon, l'éclair de bouche restant sur l'arme. Même découplage que la hitbox « délibérément plus petite que le modèle visuel » (spec §8.2). Rendu **vérifié à 1:1** : visuellement neutre. `test_point_blank.gd` garde le zéro |
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
(`_DROP_EVERY := 4`), un Power Core **un bonus sur quatre** (`_POWER_EVERY := 4`) — soit **un niveau
de puissance tous les 16 ennemis** (`KILLS_PER_POWER`). ⚠️ **C'était 12 jusqu'au playtest du
2026-08-27** : le niveau 5 tombait alors au 48ᵉ kill d'une vague qui en compte 107, et la moitié des
huit Power Cores distribués atterrissait sur un joueur déjà plein. Les deux autres suivent un cycle fixe `bouclier → score →
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
| **Puissance** | **positive** | tuer → bonus tous les 4 → Power Core tous les **16** → cadence ×0,8 et flux en plus → tuer plus vite |
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
| Puissance (1→5) | 1 bonus / **16** ennemis | **jamais** | ❌ |
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
| `LOI-EXP-03` hit stop | ✅ **tenue** (2026-08-27) | `HitStop` (`scripts/fx/hit_stop.gd`) — **60 ms** quand une plaque du Leviathan cède, **80 ms** sur une défaite de boss : les deux dans la fenêtre documentée, et un test le garde. Le comptage est **pur** (`request` / `advance`), le nœud n'est qu'un applicateur. ⚠️ Tout gèle, **l'explosion comprise** — c'est le principe : un hit stop TIENT l'image de l'impact. Le son, lui, n'est pas touché par `Engine.time_scale`, donc le coup s'entend en plein pendant que l'image est suspendue |
| `LOI-EXP-04` accepter l'intention | — | sans objet : aucune commande n'a de fenêtre (pas de saut, pas de dash, pas de bombe) |
| `LOI-EXP-05` ni ennui ni angoisse | ❔ non vérifiée | « vérifier que la difficulté est facile mais nerveuse » est au P0 du backlog |
| `LOI-EXP-06` puissance puis baisse | ❌ **absente** | la montée en puissance est **continue** (1 Power Core / 16 ennemis) et ne provoque **aucun palier de respiration**. Le joueur ne vit jamais le moment « je suis devenu fort, et ça se voit » |
| `LOI-EXP-07` apprendre en jouant | ⚠️ **partielle** (2026-08-27) | **de l'espace, enfin** : `WaveData.lead_in = 2,0 s` de ciel vide avant le premier chasseur — ils tombaient à `0.3 s`, le joueur découvrait qu'il se déplace en se faisant tirer dessus (spec §5.2, « prise en main calme »). Le silence vit sur la **vague**, pas dans trente `time_offset` : l'ordre relatif des entrées est du design déjà réglé. ⚠️ Restent absents l'**erreur peu coûteuse** et son **évaluation juste après** — les deux autres tiers de la loi |
| `LOI-EXP-08` effet invisible = défaut | ✅ **tenue, et c'est une loi née ici** | cinq mécaniques prises en défaut le 2026-08-26 : freinage de la sangsue, champ protecteur, puits gravitique, sursis de mine. Capitalisée dans [`KB/DAF/signaux.md`](../KB/DAF/signaux.md) |
| `LOI-EXP-09` contrat joueur | ⚠️ partielle | la loi des signaux en couvre le fond, **sans le formalisme** SEE/UNDERSTAND/FEEL/ANTICIPATE/DECIDE ni la ligne « à ne jamais produire » — qui aurait attrapé le lien du Shield Carrier lu comme « je suis ralenti » |
| `LOI-EXP-10` jamais la couleur seule | ✅ **tenue, et surveillée** | un cue audio par type de bonus, « parce qu'un bonus doit être identifiable sans le regarder » (`graybox_root.gd:253`) ; la charte créative l'interdit explicitement |
| `LOI-EXP-11` socle d'accessibilité | ⚠️ partielle — **la secousse est réglable depuis le 2026-08-27** | voir ci-dessous |
| `LOI-EXP-12` fonctionner ≠ validé | ✅ **tenue en pratique** | c'est la leçon des quatre ADR de boss : aucune mesure automatique n'a rien vu |

### Le socle d'accessibilité, ligne par ligne

| Ligne | État |
|---|---|
| Remappage | ❌ **absent** — `InputBootstrap` déclare les actions en dur ; son propre commentaire dit que l'UI de remappage « viendra plus tard ». C'est un écran, pas un branchement |
| Manette | ✅ **tenue** (2026-08-27) — stick gauche au déplacement, A **et** gâchette droite au tir, Menu à la pause, et **le bestiaire est pilotable** (stick droit, gâchettes, tranches), lui qui n'écoute aucune action `ui_*`. ⚠️ Le constat de départ était trop noir : `project.godot` n'a **aucune section `[input]`**, donc les `ui_*` intégrées gardaient les défauts moteur — les menus se naviguaient **déjà** au pad. Ce qui manquait, c'était le jeu et le codex |
| Secousse réductible | ✅ **tenue** (2026-08-27) — curseur SECOUSSE au menu d'options, 0 → 100. C'est le `CameraDirector` lui-même qui s'abonne à `graphics_changed`, donc le réglage vaut pour **les trois scènes** qui en portent un (combat, accueil, banc d'essai). Et il **se sent** : déplacer le curseur déclenche une brève secousse à la nouvelle intensité — un réglage d'accessibilité qui ne produit rien pendant qu'on le bouge serait le signal muet de [`LOI-EXP-08`](bible/10-experience-joueur.md) |
| Couleur seule | ✅ tenue |
| Choix de difficulté | ❌ un seul réglage, non exposé |
| Clignotement | ⚠️ l'invulnérabilité fait clignoter la coque à **~18 Hz** — sur le vaisseau seul, pas en plein écran, mais c'est la zone que le joueur fixe |

## Patterns de tir — `PAT`

*Vérifié le 2026-08-27.*

| Loi | État | Preuve |
|---|---|---|
| `LOI-PAT-01` le nombre n'est pas le sujet | ✅ tenue | la bibliothèque est construite sur l'intention, pas sur le compte |
| `LOI-PAT-02` cinq familles | ⚠️ **quatre sur cinq, et toutes jouées depuis le 2026-08-27** | `SINGLE` (ligne), `FAN` (éventail aveugle, 62°), `AIMED` (éventail visé, 12°), `RADIAL` (anneau), `NONE`. **La pile n'existe pas** : aucun schéma ne fait varier la vitesse dans une salve |
| `LOI-PAT-03` la parité | ⚠️ **tenue en vague, subie chez le boss** | le lancier vise en **3** balles, impair et écrit dans son `.tres` avec sa raison, gardé par `test_opening_wave.gd`. Le boss, lui, la subit — voir ci-dessous |
| `LOI-PAT-04` semences d'angle | ⚠️ partielle | fixe et visée présentes ; `RADIAL_PHASE = 0,5` entrelace les couronnes — « les trous de la première sont bouchés par la seconde, **donc rester immobile ne paie jamais** » |
| `LOI-PAT-05` composer | ✅ tenue | `RADIAL_PHASE` est exactement « régularité plus une légère fluctuation » |
| `LOI-PAT-06` désigner l'esquive | ⚠️ partielle | la macro-esquive n'est demandée que par les couronnes de la Choir Mine. Le **streaming** devient possible depuis que le lancier vise (2026-08-27) |
| `LOI-PAT-07` forme, pas constantes | ✅ **tenue, et testée** | la règle est écrite dans `enemy_fire.gd` et **un test de variété la vérifie** : « FAN et AIMED ne diffèrent pas par leur ouverture, ils diffèrent parce que l'un est aveugle et l'autre voit » |

### ✅ `FAN` et `AIMED` sont en jeu depuis le 2026-08-27

Ils étaient **écrits, testés, documentés — et joués nulle part** : `fire` valait `SINGLE` par défaut
(`enemy_data.gd:28`) et aucun `.tres` d'ennemi ne le surchargeait. Les neuf Needle Scout et le
Crescent Interceptor tiraient **tous une balle droite**.

C'est la **trajectoire** qui a désigné le schéma, pas le hasard :

| Unité | Trajectoire | Schéma | Pourquoi |
|---|---|---|---|
| `needle_scout_lancer` | `HOVER_STRAFE` — s'arrête à `y = 3,5` pendant 2,6 s | **`AIMED`**, `burst_count = 3` | la seule unité de vague qui **s'immobilise**, donc la seule qui puisse viser honnêtement. Impair : une balle **sur l'axe**, l'immobilité du joueur se paie |
| `needle_scout_strafe` | `STRAFE_RUN` — traverse à 4,5 u/s | **`FAN`**, `burst_count = 5` | il traverse sans s'arrêter, viser n'aurait aucun sens. L'éventail aveugle **ferme le couloir** de son passage |

**Vérifié en jeu** (capture Windows, fond noir, t ≈ 34 s) : les salves du lancier **convergent sur le
chasseur immobile**, en grappes de trois. `test_opening_wave.gd` garde les deux schémas en jeu et la
parité de la salve visée — la garde a été éprouvée en la cassant (`burst_count = 4` → rouge).

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
| `LOI-LVL-06` deux patterns, deux apparences | ❌ **écart avéré** (2026-08-27) | voir ci-dessous — et le rapport se trompait d'endroit |
| `LOI-LVL-07` file d'actions | ✅ tenue | `WaveData` / `WaveEntry` sont littéralement la structure : `time_offset`, `enemy_scene`, `spawn_plane_position`, `count`, `spacing`. ⚠️ Pas encore l'`EncounterDirector` de la spec §11.3 : la file pose des ennemis, elle n'attend pas une condition et ne synchronise rien |
| `LOI-LVL-08` checkpoint ou reprise | ❌ **écartée, délibérément** | le mot « checkpoint » **n'apparaît dans aucun script**, alors que la spec §5.3 en demande deux. Le jeu fait la troisième voie : reprise sur place à `(0, −5)`, sans perte, continues illimités. Évite le *Gradius syndrome* par construction — et supprime l'enjeu de la mort |

⚠️ `BOUNDS` est un **paramètre d'équilibrage majeur déguisé en constante technique**. S'il bouge un
jour, c'est un ADR, pas un ajustement (`LOI-LVL-01`).

### ⚠️ `LOI-LVL-06` — trois schémas de tir, une seule apparence de balle

Ce rapport annonçait que la question se jouait dans le **champ d'astéroïdes**. C'était faux, et la
donnée le dit en trois lignes : sur les quatre unités de la phase, **une seule tire**
(Choir Mine, `RADIAL`) — Null Maw, Leech Drone et Shield Carrier sont toutes en `fire = NONE`. Deux
patterns simultanés ne s'y produisent **jamais**.

L'endroit réel est la **vague d'ouverture**, et c'est le lot 0 du 2026-08-27 qui l'a créé : elle
emploie désormais `SINGLE`, `FAN` et `AIMED` en même temps — et **les dix unités partagent le même
`needle_shot.tres`**. Vérifié à la capture : les salves sont des grappes de coral identiques.

Le joueur ne peut donc pas distinguer *« cette salve me suit »* de *« celle-là m'ignore »*, alors
que c'est exactement la différence que les deux schémas existent pour produire.

⚠️ **Et ce n'est PAS la décision de charte que ce rapport annonçait.** Vérifié le 2026-08-27 :
`ProjectileData` ne porte **aucun champ visuel** — ni couleur, ni maillage. L'apparence vit dans le
`MultiMesh`, **une par équipe**, et le buffer de transformation écrit uniquement l'origine : la base
identité est posée **une fois pour toutes** au `_ready`. Autrement dit, **toutes les balles ennemies
du jeu sont identiques par construction**, quelle que soit leur Resource.

Distinguer le tir visé demande donc une **capacité qui n'existe pas** dans `BulletManager` : soit un
troisième `MultiMesh`, soit des données par instance (`use_custom_data`) lues par le shader de bolt.
C'est un chantier sur une classe **critique et budgétée** (600 projectiles, quotas 150/450, zéro
allocation), pas deux lignes de `.tres`.

### ⚠️ Même cause, autre écart : la balle ne ressemble pas à sa hitbox (spec §17.3)

La spec exige que le rayon de collision « corresponde à la taille visuelle ». Mesuré :

| | Rayon de collision | Rayon visuel |
|---|---:|---:|
| `needle_shot` | 0,16 | **0,31** |
| `mine_burst` | 0,20 | **0,31** |
| `boss_shot` | 0,18 | **0,31** |
| `fortress_battery` | 0,30 | **0,31** |

Le quad ennemi fait 0,62 × 0,62 pour tout le monde. Les balles se voient donc **1,6 à 1,9 fois plus
grosses qu'elles ne touchent** — l'écart est dans le sens généreux, ce qui explique qu'il n'ait
jamais gêné personne. Mais une balle de mine et une balle de chasseur sont **strictement
indiscernables** alors que leurs hitbox diffèrent de 25 %.

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

### D-4 — La manette (`LOI-EXP-11`) — ✅ **fermée le 2026-08-27**

Les liaisons sont posées (spec §7.2) et gardées par `test_input_bootstrap.gd`, dont la garde
d'orientation a été éprouvée en la cassant. ⚠️ **Non vérifié manette en main** : aucune manette n'est
branchée sur le poste de développement — la seule chose qu'un test ne peut pas dire ici, c'est que
ça se joue bien.

Restent hors périmètre, et ce sont deux chantiers distincts : l'**UI de remappage** (un écran), et
les **glyphes qui suivent le dernier périphérique** que demande la même §7.2 — soit une passe sur
tous les écrans d'aide, qui affichent aujourd'hui des touches en dur (`ESC BACK`, `OPTIONS O`).

### D-5 — Les checkpoints de la spec §5.3 (`LOI-LVL-08`)

Ils n'existent pas et **rien ne les réclame** : la reprise sur place fait le travail, mieux et plus
simplement. Le plus honnête serait sans doute de **retirer la ligne de la spec** — mais la spec est
source de vérité et ce rapport ne la modifie pas.

## ✅ Le lot gratuit — livré le 2026-08-27

Les trois gestes du plan sont faits :

1. **La secousse est exposée** (`LOI-EXP-11`) — curseur SECOUSSE, avec aperçu au déplacement.
2. **`FAN` et `AIMED` sont en jeu** (`LOI-PAT-02`, `LOI-PAT-03`) — lancier visé en impair, strafe en
   éventail aveugle, parité gardée par un test éprouvé en le cassant.
3. **`LOI-LVL-06` est vérifiée** — et le résultat n'est pas celui qu'on attendait : l'écart n'est pas
   dans le champ d'astéroïdes (une seule unité y tire), il est dans la vague d'ouverture. Il est
   désormais **avéré et localisé**, ce qu'un ❔ ne permettait pas.

Ce que le lot a **coûté** : un drapeau de debug `--options-demo`, pour que l'écran d'options — qui ne
s'atteignait qu'au clavier — soit capturable depuis WSL comme le reste du jeu.
