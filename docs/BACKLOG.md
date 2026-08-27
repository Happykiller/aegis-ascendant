# Backlog & pistes d'amélioration — Aegis Ascendant

> Point de reprise au **2026-08-25**. Arc jouable **`FIGHTER_WAVES → MINI_BOSS → ASTEROID_FIELD →
> FINAL_BOSS → DOCKING → VICTORY`**, **420 tests verts**.
>
> ⚠️ **Une phase de plus, et son décor.** `ASTEROID_FIELD` (**ADR-0027**) s'insère entre les deux
> boss : la traversée qui les sépare, jouée avec les trois unités que le bestiaire avait livrées
> sans qu'aucune rencontre ne les emploie. Elle revient sur le découpage d'`ADR-0010`, qui avait
> *supprimé* une phase de milieu de niveau. **Lots 1 et 2 du plan livrés** : la phase se joue, et
> son décor bascule — le survol de lune REMPLACE la nébuleuse au lieu de s'y ajouter, pour
> **−0,622 ms/image** — la phase 2 coûte **un tiers** du fond habituel (0,323 contre 0,945 ms,
> mesuré RTX 4080 ; à refaire sur la T1000, c'est elle qui contraint). Les **impacts** de lune
> sont livrés aussi. Restent les **assets** du lot 3 et le lot 4 (rythme).
>
> Le boss final, refondu en cycles par `ADR-0021`, a enfin été **joué** (2026-08-25) :
> l'équilibrage est **acquis**, le grief « lancinant » ne s'est pas reproduit. Restait une
> **progression invisible** — le HUD montrait la cible courante, qui se remplit à chaque
> bascule, au lieu de l'avancement du combat. Corrigé par **`ADR-0023`**, vérifié en capture.
> Seconde partie le même jour, droit au boss à puissance max : **six plongées au lieu de
> trois**. Le flux était dimensionné avec la cadence de l'**armure** — cible large où toutes
> les balles portent — alors que seuls les canons de nez touchent une cible de 1,80 m qui
> dérive. **`ADR-0024`** lui donne sa propre hypothèse et ramène `flux_health` de 5300 à 2400.
> Rejoué : il donnait **deux** cycles, parce que la refonte de la plongée en **zone dédiée**
> (`ADR-0025` — la gueule s'ouvre par un iris à volets, on entre dans une arène avec
> passerelle et réacteur) avait doublé la capacité à toucher le flux. Et la mesure a montré
> qu'**aucun nombre de PV ne pouvait donner trois cycles** : les dégâts par plongée vont de
> 600 à plus de 1200 pour le même joueur. **`ADR-0026`** plafonne les dégâts à un tiers par
> passage — trois cycles par **construction**. ✅ Vérifié en partie : trois cycles exactement,
> zéro dépassement, zéro erreur. **Le combat tourne comme `ADR-0021` le décrit.**
>
> ⚠️ Une autre session travaille en parallèle sur le **bestiaire ennemi** (`ADR-0022`,
> `scripts/enemies/`, `wave_spawner`, assets). Périmètres disjoints, mais `C:\tmp` et le
> processus Windows ne sont **pas** cloisonnés : s'annoncer avant tout déploiement.
>
> ⚠️ L'en-tête précédent annonçait un arc « appontage → forteresse » supprimé depuis, 80 tests, et
> un chemin `~/sandbox/macross` qui n'existe pas. Un point de reprise faux coûte plus qu'un point de
> reprise absent : il envoie la session suivante dans le mur sans qu'elle le questionne.

## ⚠️ Les plans datés font foi sur « ce qui reste »

Ce backlog est un inventaire ; il ne dit pas **quel document est le plus récent**. Les plans de
travail vivent dans **`docs/plans/AAAA-MM-JJ-<sujet>.md`**, datés dans leur nom **et** dans leur
en-tête (auteur, périmètre, état, ce qu'ils supersèdent). En cas de désaccord entre ce fichier et un
plan plus récent, **le plan gagne**.

| Plan | Sujet | État |
|---|---|---|
| [`2026-08-25-bestiaire-ennemis.md`](plans/2026-08-25-bestiaire-ennemis.md) | Familles d'ennemis, coques et comportements — **repris** après la fin du régime à deux sessions | à appliquer |
| [`2026-08-25-phase-inter-boss-survol-de-lune.md`](plans/2026-08-25-phase-inter-boss-survol-de-lune.md) | Une phase de jeu entre les deux boss : unités du bestiaire + survol de lune | **lot 1 livré** (ADR-0027) ; lots 2-4 à faire |
| [`2026-08-27-bible-supreme.md`](plans/2026-08-27-bible-supreme.md) | Rapport d'audit externe « Bible suprême » : vérifié et trié — gouvernance documentaire | **3 décisions ouvertes**, rien d'engagé |
| [`2026-08-27-conformite-bible.md`](plans/2026-08-27-conformite-bible.md) | Fermer les écarts du rapport de conformité — secousse exposée, `FAN`/`AIMED` en jeu, manette, ouverture calme, hit stop | **lots 0, 1 et 2 livrés** ; lots 3-5 bloqués |
| [`2026-08-27-playtest-operateur.md`](plans/2026-08-27-playtest-operateur.md) | Retours de playtest : montée en puissance trop rapide, regen invisible, phase du noyau au minuteur, **trajectoires sur rails** | **tout livré** (R1→R10) |
| [`2026-08-27-reactor-chamber.md`](plans/2026-08-27-reactor-chamber.md) | La phase du noyau devient une **machine** : anneaux rotatifs à fenêtre de vulnérabilité, rails, lasers balayants, nodes | **4 points bloquants**, rien d'engagé |
| [`2026-08-27-chambre-du-reacteur-jouable.md`](plans/2026-08-27-chambre-du-reacteur-jouable.md) | La chambre a été taillée pour un chasseur-**disque** ; il est une **capsule** de 4,22 × 1,76 et n'entre pas dans le couloir (2,60). Agrandir l'arène — décidé par l'opérateur | **lots 1-4 livrés**, reste la plongée jouée |

> ✅ **Le chantier du boss est CLOS** (2026-08-25). Ses deux plans sont dans
> [`plans/archive/`](plans/archive/) et ce qui restait ouvert est dans **P0 bis** ci-dessous.
>
> **`docs/plans/` ne contient que du vivant.** Ce qui est clos descend dans `archive/` — on
> déplace, on ne se contente pas de changer un champ. `./scripts/audit-docs.sh` dérive l'état
> du dépôt et range tout seul (`--fix`) ; il est appelé par `/cloture`.

## Comment reprendre

1. `cd ~/aegis-ascendant`
2. `./scripts/check.sh` → doit être **ALL GREEN**.
3. `./scripts/play.sh` → jouer le code courant (il exporte si le build est périmé ; skill `/jouer`).
4. Lire **`.claude/resources/INDEX.md`** — le *ghost* : comment vérifier un rendu, mesurer une perf,
   réviser un asset. C'est là que vit le savoir de méthode.
5. Lire `docs/architecture/` et les **ADR** (`ADR-0001` à `ADR-0018`), qui priment sur la spec.

---

## ⏳ En cours — Pale Leviathan (refondu en cycles le 2026-08-23)

### ✅ REFONTE FAITE — trois cycles armure/noyau (`ADR-0021`)

Verdict opérateur, sur un combat pourtant **gagné** : *« extrêmement lancinant — on arrose les
plaques sans faire gaffe en attendant qu'elles disparaissent ; les tentacules, je ne vois pas à
quoi elles servent ; et qu'il faille aller dans le noyau pour tirer, on ne le voit pas, on ne
le comprend pas. »* Trois griefs de natures différentes : du temps sans décision, des pièces
sans rôle, une cible qu'il fallait deviner.

Ce qui est en place :

| Grief | Réponse livrée |
|---|---|
| « lancinant » | Plaques à **460 PV** (contre 1270) : une cède toutes les ~2 s, la salve d'armure passe de ~22 s à ~8 s |
| « les tentacules ne servent à rien » | Ce sont des **tourelles laser télégraphiées** (`Beam`), et **chaque plaque brisée en éteint une** |
| « on ne comprend pas qu'il faut tirer le noyau » | **On y entre** : coquille écartée, aspiration, autopilote, caméra qui plonge, flux d'énergie plein cadre, ~5 s de tir puis éjection |
| — | **Trois cycles** : 4 plaques, puis 3, puis 2. L'armure revient toujours amoindrie |

Deux invariants neufs : l'**arc d'exposition s'élargit** quand il reste moins de plaques (sans
quoi il existe des instants sans aucune cible dès le cycle 2), et le **flux est dimensionné**
pour tomber au troisième passage — ni au premier, ni jamais.

⚠️ **Le second invariant dit moins qu'il n'en a l'air**, et la partie du 2026-08-25 l'a
montré : il compare les PV du flux à ce qu'un joueur atteindrait en tirant 85 % du temps dans
le noyau à la cadence de référence. C'est une hypothèse de **dimensionnement**, pas une fin de
combat — un quatrième cycle est possible, et il est arrivé (`ADR-0023`).

#### Reste à juger — PAR UNE PARTIE

- ✅ **`/jouer` — FAIT le 2026-08-25.** Équilibrage acquis (« mieux équilibré »), mais la
  progression était invisible (« phase 1 phase 2 phase 1 phase 2, en boucle ») : la jauge
  montrait la cible courante et se remplissait six fois. Traité par **`ADR-0023`**.
- ✅ **Le NOMBRE de cycles — traité par `ADR-0024`.** Mesuré à puissance maximale : six
  plongées. `flux_health` 5300 → 2400, et le flux reçoit sa propre cadence de référence
  (208 au lieu de 420) — se mesurer à la cadence de l'armure revenait à se donner raison.
- ⚠️ **Rejouer après `ADR-0024`** : trois cycles sont attendus par le calcul, pas constatés.
- **Alignement halo ↔ hitbox** : non jugeable à l'arrêt.
- **Cadrage de la plongée** : réglé à l'œil en trois captures. Le chasseur est visible dans le
  noyau (`plane_lift`), mais sa lisibilité en mouvement reste à confirmer.
- **Leviers** si la phase d'armure traîne encore : `shell_orbit_period` 9→7,
  `plate_health` 460→380 (le garde-fou de durée refusera d'aller trop loin).

#### Dette laissée par la refonte

- ⚠️ **Quatre coques sur dix sont sans UV, donc impossibles à texturer** — mesuré le 2026-08-23
  **une fois chargées dans Godot** (`mesh.surface_get_format() & ARRAY_FORMAT_TEX_UV`) :
  `choir_harvester` **0/61** (le mini-boss), `crescent_interceptor` 0/7, `needle_scout` 0/7,
  `null_maw` 0/36 avant sa reforge. Saine : `pale_leviathan` **145/145**.
  Cause : sans `_triangulate_ngons()` ni `box_project_uv()`, le dépliage n'est jamais produit — et
  aucun importateur ne peut le deviner. Ce n'est pas un rendu dégradé aujourd'hui, c'est une **porte
  fermée pour demain** : `HullDetail.apply()` n'a rien où plaquer.
  ⚠️ **Correction d'une conclusion fausse** : cette ligne a d'abord annoncé « sans tangentes », sur
  un comptage de `TANGENT` dans le JSON des `.glb`. Les tangentes sont **fabriquées par Godot à
  l'import** (`meshes/ensure_tangents=true`, identique sur toutes les coques) : `needle_scout` passe
  de 0/7 dans le fichier à 7/7 chargées. Le fichier ne dit pas ce dont le moteur dispose.
- ⚠️ **`ak.inset_panel()` est un no-op sur un BMesh fraîchement bâti** — signalé par la forge de la
  session bestiaire, mesuré : `inset_region` lit la normale de face, qui vaut `(0,0,0)` tant que
  `normal_update()` n'a pas été appelé. Bordures d'aire **0,000000 m²** sans la mise à jour contre
  **0,000714 m²** avec, puis ressoudées par `cleanup()`. **Il ne reste que le changement de
  matériau** : un panneau qui se voit et qui n'existe pas.
  → **Les deux coques de boss sont concernées** : `build_pale_leviathan.py` (10 appels,
  0 `normal_update`, 28 `bridge_rings`) et `build_choir_harvester.py` (7 appels, 0). Comme d'habitude
  ici, **rien ne le signale** — ni le compte de triangles, ni le contrat d'export, ni le rendu.
  → Le correctif a sa place dans **`lib/aegis_kit.py` lui-même**, sinon le prochain script l'oubliera
  comme les précédents. Mais le kit est partagé : le corriger régénère **tous** les `.glb` du dépôt,
  donc déterminisme à revérifier et silhouettes à re-regarder, coque par coque. **Chantier à part,
  pas un correctif à glisser** — accord pris entre les deux sessions le 2026-08-23.
- ⚠️ **`HarvesterCombat` attache ses `Beam` comme le Leviathan le faisait** — enfants d'un
  `Node` sous le `BossController`, donc doublement transformés. Le Leviathan est corrigé
  (`top_level = true`) ; **le mini-boss n'a pas été vérifié**. Si ses faisceaux sont décalés,
  personne ne l'a jamais remarqué.
- Le document de conception `BOSS_PALE_LEVIATHAN.md` décrit toujours quatre phases. Il porte un
  avertissement en tête et sert encore pour les assets ; ses §4 à §6 sont de la matière non
  employée.

### Ce qui est acquis

| Livrable | Où | État |
|---|---|---|
| Conception du boss (4 phases, chiffres, invariants, spec 3D, 11 prompts) | `docs/design/BOSS_PALE_LEVIATHAN.md` | ✅ |
| Décision + dimensions 11 × 14 m | `ADR-0018`, tableau d'`ADR-0008` amendé | ✅ |
| Les 11 images (3 planches, 5 textures, 3 décors/VFX) | `assets/reference/concepts/`, `assets/source/` | ✅ mesurées, regardées, provenance au CSV |
| **Coque + silhouette (BRIEF-0041)** — noyau sphérique, épines longues/inégales, croissant asymétrique | `build_pale_leviathan.py`, `pale_leviathan.glb` | ✅ mesurée, rendue, regardée (voir réserve) |
| `GravityWell`, `TargetableProjectile` | `scripts/gameplay/` | ✅ 25 tests (le puits sert désormais les vagues d'aspiration de la phase 2) |
| `LeviathanTuning` + 6 invariants | `resources/data/` | ✅ 20 tests |
| `LeviathanPlate`, `LeviathanCombat` | `scripts/bosses/` | ✅ refondus par ADR-0020 ; `LeviathanSpike` supprimé avec ses 13 tests |

`./scripts/check.sh` : **311 tests verts** (les deux sessions confondues).

### ✅ BRIEF-0041 (silhouette) — livré et intégré

La reforge de silhouette était en réalité **déjà complète dans le script commité** (`0af3123`) : le
message WIP sous-décrivait son contenu (sphère du noyau, arc de coquille, épines allongées/inégales,
gonflement du croissant, tous présents). Le `9,481 m` de la note de reprise était un état
intermédiaire écarté ; le script commité produit **11,03 m et passe le contrat d'export**. La coque
a été **régénérée** (le `.glb` sur disque était encore celui de BRIEF-0040) puis vérifiée point par
point, pas sur la foi du rapport :

- **bbox 11,0313 × 3,1620 × 13,9972 m** (X +0,28 %, Z −0,02 %, Y ≤ 3,20), 27 710 tris / 40 630 sommets.
- Matériaux aux 3 cibles : `AA_Hull` 35,2 % (≥ 30), `AA_Emissive_Engine` 7,8 % (≤ 8), `AA_Greeble` 17,9 % (≤ 20).
- Contrat de noms intact (30 maillages, parentage exact), `TANGENT` + `TEXCOORD_0` sur 30/30.
- Déterminisme OK, sha256 `98529ce7…`. Rendu de recette : `docs/forge/output/BRIEF-0041-planche-quatre-vues.png`.

**3 des 4 écarts résolus et lisibles** : symétrie→asymétrie, noyau plat→sphère saillante, épines
courtes→longs dards inégaux. **Réserve visuelle non bloquante** (écart n°4, candidate à un polish
ultérieur) : la coquille lit comme des **anneaux concentriques machinés** plutôt qu'une **carapace de
tuiles chevauchantes**, et l'incomplétude du croissant reste peu dramatique. Levier propre si on
l'ouvre un jour : **interrompre les bandes concentriques côté ouverture** (avant-tribord) plutôt
qu'élargir l'encoche — travail de géométrie de coquille avec incidence sur le harnais de dégagement.
La méthode de revue est capitalisée dans `.claude/resources/pratique-revue-asset.md`.

### ✅ Câblage de scène + relais niveau — fait (commit `feat(boss): le Leviathan combat`)

`pale_leviathan.tscn` monte `LeviathanCombat` (`external_attacks = true`) avec
`resources/bosses/pale_leviathan_tuning.tres`. Le relais complet est dans `graybox_root.gd` :
`structure_changed` → jauge continue, `pull_changed` → `PlayerFighterController.apply_pull()`,
`piece_gauge_changed` → 4 pastilles (`FighterHUD.set_boss_limbs`, recentrées, 0 régression Harvester),
`piece_destroyed` → VFX/SFX, `phase_entered` → bannières par phase. **Deux trous comblés au passage** :
le boss ne mourait jamais (`BossController.defeat()` ajouté ; le module l'appelle quand le cœur tombe)
et le corps n'était jamais clos (il l'est désormais de bout en bout, seul le cœur compte). Vérifié
Windows (4 phases, HUD, aspiration ; GPU 0,92 ms) + 2 tests montés sur un vrai `BossController`.

### Ce qui reste, dans l'ordre

1. **Détachement visuel des épines** (3ᵉ primitive, §8.2 du document) — différée exprès : elle dépend
   des nœuds de la coque, qui bougeaient encore.
2. **Textures** : dériver dans `assets/imported/textures/leviathan/` **et** écrire
   `scripts/fx/leviathan_detail.gd` dans le même commit (`CLAUDE.md` : rien d'inutilisé dans
   `imported/`). Paramètres de dérivation consignés au §11.3 du document de conception.
3. **Décor** : vortex et landmark de l'arène (`--mode black`), câblés dans `space_backdrop.tscn`.
4. **Polish silhouette (optionnel)** : réserve écart n°4 du croissant (voir plus haut).
5. **Brief séparé** : `build_choir_harvester.py` n'a ni `_triangulate_ngons()` ni `box_project_uv()`
   — le mini-boss est probablement sans tangentes, donc intexturable. Trouvaille du BRIEF-0040.

---

## Livré le 12/07/2026 — ne plus le proposer

| Chantier | État |
|---|---|
| Axe vertical inversé (flèche bas = monter) | ✅ corrigé + 4 tests |
| Fond spatial | ✅ nébuleuse procédurale volumétrique (domain warping) — **ADR-0006** ; le carré cyan graybox a disparu |
| Sprites & projectiles | ✅ plus aucune primitive : bolts cœur+halo, traînées douces (`SoftDot`) |
| Retour d'impact | ✅ gerbe teintée par camp (blanc froid sur coque ennemie, cyan sur notre bouclier) + flash de coque |
| Vie des ennemis | ✅ réacteur, roulis dans le virage, flash à l'impact |
| Boss qui mourait deux fois | ✅ corrigé aux deux niveaux (garde `_defeated` + cible qui cesse d'absorber) + test |
| Audio | ✅ banque de cues typée, 20 SFX, **musique adaptative 9 états** + thème de titre, bus, réglages persistants, menu d'options — **ADR-0007** |
| Mix audio | ✅ musique normalisée en **loudness** (−16 dB RMS) ; compresseur déplacé du Master vers SFX (le tir du joueur écrasait la partition) |
| Passage 3D | ✅ **5 coques en meshes glTF** (Specter-9, Needle Scout, Citadelle, Choir Harvester, Pale Leviathan) + éclairage clé/contour avec ombres — **ADR-0008** |
| Ghost | ✅ `.claude/resources/` (index de process) + roster de **5 sous-agents** |

---

## Livré le 22/07/2026

| Chantier | État |
|---|---|
| **Bandeau de vie du boss sur le HUD** | ✅ `_panel` traitait « ancre ≠ 0 » comme « ancré à droite » : le bandeau, seul panneau ancré au CENTRE, s'étalait de centre−1200 à centre−400 et se posait sur la jauge de bouclier. Invisible en développement — il faut atteindre le mini-boss pour le voir. Gardé par `tests/unit/test_hud_layout.gd`, qui échoue bien sur l'ancienne formule |
| **Planète « découpée »** | ✅ son PNG a un bord BINAIRE (alpha 255 → 0 en 4 px sur un rayon de 500, mesuré) : à l'écran le dégradé tombait sous le pixel. `shaders/planet_atmosphere.gdshader` — limbe adouci, anneau, et surtout **halo débordant sur le fond**, tous modulés par le côté éclairé |
| **Luminosité** | ✅ le post-traitement rétro pivotait son contraste à 0,5 sur une image entièrement sous 0,25 : il n'était qu'un assombrisseur. `lift` en gamma + troisième lumière ajoutée au combat — **+25,8 %** sur la coque du joueur, mesuré — **ADR-0016** |
| **Aegis Citadel au bestiaire** | ✅ sixième fiche, famille `FORTRESS` : aucune valeur de combat, donc ses **équipements comptés sur la coque** (6 tourelles, 3 balises, 2 batteries, 1 baie) au lieu de trois lignes de tirets. Tourelles et balises montées et animées (`CitadelLife`) — **BRIEF-0038** |
| **Bestiaire** (menu d'accueil) | ✅ cinq coques sur présentoir 3D — rotation souris/clavier, zoom, pièces mobiles animées en démonstration, fiche technique HUD qui vire au camp. Dimensions et polygones **mesurés** sur la coque, PV/vitesse/cadence/score **lus** dans les Resources de gameplay (aucune recopie) ; fiction produite par la forge (**BRIEF-0037**) — **ADR-0015** |

---

## Ouvert par le chantier collision (2026-08-27)

Les quatre lots du plan `2026-08-27-les-corps-ne-se-chevauchent-pas.md` sont livrés. Ce qu'ils
laissent, en revanche, n'appartient à aucun d'eux :

- **Le couloir entre les deux murs du réacteur n'est pas un lieu.** Le chasseur est toujours
  aligné sur l'axe vertical, donc radialement c'est sa LONGUEUR (2,46) qui devrait tenir dans
  l'espace libre du couloir (0,84 une fois l'envergure retranchée). Il ne peut pas y entrer,
  quelle que soit son adresse. La phase se joue très bien en tirant du dessous à travers les
  ouvertures — mais le « labyrinthe » demandé au playtest est un **décor**, pas un terrain.
  ⚠️ **À trancher avant d'y accrocher la moindre mécanique.** Trois issues : élargir le couloir
  (l'arène ne le permet pas sans reprendre l'enveloppe du flux), passer à **un seul** anneau, ou
  assumer que c'est du décor et le dire dans le plan. Garde en place :
  `test_the_corridor_between_the_walls_is_scenery_not_a_place`.

- **Les paliers musicaux lisent une jauge qui a changé de sens.** Depuis l'amendement d'`ADR-0023`,
  `fight_ratio()` ne compte plus que les dégâts sur le flux : elle ne bouge donc pas pendant la
  phase d'armure. Les seuils de `_update_music()` avaient été calés sur l'ancienne mesure, qui
  comptait aussi les plaques. Constaté sur trois parties d'affilée : la partition passe de 7 à 8
  au cycle 2 et **n'atteint jamais 9**. Rien n'est cassé, mais la montée arrive trop tard et le
  combat ne culmine pas. Recalage à faire sur les nouveaux ratios (1 → 2/3 → 1/3 → 0).

- **Les bordures de la salle du réacteur sortent du cadre** depuis son agrandissement (échelle
  1,26, lot 4). On voit le sol jusqu'au bord de l'écran au lieu du mur du fond. Choix assumé —
  l'alternative rendait l'entrée de plongée impossible — mais **non jugé par l'opérateur**.

## P0 — Rendre la démo irréprochable

- [x] **Contenu de la phase chasseur** — une **seconde vague** existe : le champ d'astéroïdes
  (`resources/encounters/wave_asteroid_field_01.tres`, 36 unités sur 40 s), inséré entre les deux
  boss par **ADR-0027** et joué avec Choir Mine / Null Maw / Leech Drone. L'arc gagne 45 à 60 s et
  passe la cible « 2-3 min de jeu ». ⚠️ Reste ouvert : **laisser la puissance monter à 5** — le
  champ ne distribue aucun bonus de puissance particulier, c'est le `PickupManager` qui décide.
  (ex-tâches **H5** / **H6** ; `TASKS_HORIZONTAL.md` est archivé.)
- [ ] **Rythme du champ d'astéroïdes** — la composition de la vague est une **hypothèse de
  conception**, pas une mesure : densité des barrages, superposition puits/sangsues, pic à 32 s.
  Elle se juge en jouant (`ADR-0019`). C'est le lot 4 du plan.
- [ ] **Écran titre** — texte nu. Le `title_backdrop.svg` et les emblèmes de faction de la forge
  **ne sont pas utilisés**. (ex-tâche **H3**).
- [x] **Écrans** — **pause** et **victoire / rapport** reforgés dans le langage d'interface de
  l'accueil (ADR-0012). Les cadres SVG plein écran de la forge sont abandonnés, pas intégrés.
- [ ] **Écran d'échec de mission** — il n'en existe **aucun** : perdre tous les chasseurs appelle
  `continue_run()` et la partie repart, sans écran ni choix offert au joueur. Manque de gameplay
  autant que d'interface. → ex-tâche **H4**, redéfinie par l'ADR-0012.
- [ ] **Pacing de l'appontage** — trop rapide ; ajouter des temps de pause entre l'arrivée de la
  Citadelle, l'autopilote et le transfert (`graybox_root._start_docking`).
- [ ] **Équilibrage démo** — vérifier que la difficulté est « facile mais nerveuse ».
  Outil : sous-agent `balance-prober` (rend la chronologie de l'arc).
- [x] **Bascule de décor du champ d'astéroïdes** — lot 2 : `MoonFlyby` monté au montage, doublure
  procédurale, aller-retour vérifié en capture, **−0,200 ms** contre le fond habituel.
- [x] **Impacts sur la lune** — trois bolides dorés, flash et gerbe, sur des jalons fixes de la
  phase (11 / 26 / 40 s). Préalloués, hors `VFXManager` (question d'échelle).
- [ ] **Assets du survol** — lot 3 : lune à cratères, astéroïdes. **Brief écrit**
  (`BRIEF-0085`, au **brouillon** volontairement). ⚠️ **Remesurer d'abord le différentiel sur la
  Quadro T1000** : les chiffres viennent de la RTX 4080, et c'est le poste du bureau qui contraint
  (13,05 ms fond complet sur les 16,67 du budget). C'est cette mesure qui fige les budgets du brief.
- [x] **Le champ de protection se voit** — un **anneau** au ras du plan de jeu, centré sur la portée
  réelle de la Resource, avec sa respiration. ⚠️ **Pas de dôme**, et c'est une décision : trois
  essais de volume ont tous rendu un aplat magenta qui recouvrait le porteur et les étoiles. La
  cause n'est pas le réglage mais la **surface** — le bloom et le `lift` de 1,25 du post-traitement
  rétro ravivent tout violet, même à 11 % d'opacité. Un cercle fin porte mieux la seule information
  utile : **où** la bulle s'arrête.
- [x] ~~**⚠️ Le dôme de protection n'a AUCUN rendu**~~ — relevé le 2026-08-25 en regardant la capture.
  `_project_aura()` couvre bien les voisins, et une unité couverte montre qu'elle encaisse sans
  perdre de PV — mais **la portée de la bulle ne se voit nulle part**. `BRIEF-0046` l'avait pourtant
  écrit noir sur blanc : « le dôme est généré par le code, à partir du rayon d'aura ; il doit montrer
  la portée RÉELLE » — ce code n'a jamais été écrit. Sans lui, le joueur voit que ses tirs ne portent
  pas mais ne peut pas savoir **où** la bulle s'arrête, donc ne peut pas jouer contre. C'est la suite
  immédiate du Shield Carrier.
- [x] **Shield Carrier en jeu** — son comportement est codé et testé depuis le 23/08
  (`Effect.SHIELD_AURA`), et l'unité est désormais **complète** : coque forgée (`BRIEF-0046`, 4 788
  triangles, UV 19/19), `.tres`, `.tscn`, fiche codex et **deux exemplaires dans la vague du champ
  d'astéroïdes** — le premier à 15,5 s pour enseigner le mécanisme seul, le second à 31 s pour le
  faire payer. ⚠️ Il lui manque son dôme (ligne au-dessus).
- [ ] **Intensité de la gerbe d'impact** — se juge **en mouvement**, pas en capture : une image
  fixe fige la seule chose qui fait lire des débris qui s'envolent.
- [ ] **Solides et décoratifs dans le même cadre** — l'arbitrage « astéroïdes solides, lune décor »
  ouvre un sujet de lisibilité : rien ne distinguera à l'œil un rocher qui tue d'un rocher qui
  traverse. À trancher au brief du lot 3.

## Évolutions issues de la bible du genre (2026-08-25)

Tirées de [`docs/design/bible/`](design/bible/README.md), **classées par retour sur
investissement** : gain perçu par le joueur, divisé par le coût et le risque. ⚠️ Ce classement
n'est pas une feuille de route — les trois dernières lignes attendent une décision, pas du temps.

| # | Évolution | Coût | Gain | État |
|---|---|---|---|---|
| 1 | **Vider l'écran des tirs ennemis à la mort** | ~20 lignes | supprime la mort en chaîne, que tout le genre neutralise ainsi | ✅ **fait** |
| 2 | **Une respiration avant le boss final** | ~10 lignes | le genre la nomme comme structurante ; l'arc enchaîne aujourd'hui champ → boss sans transition | à faire |
| 3 | **Le Shield Carrier en jeu** | coque + intégration | le rôle « priorité de cible », structurant, dont nous n'avons **aucune** expérience de terrain | en cours (forge) |
| 4 | **Peut-on toucher un ennemi collé au nez ?** | une observation | si non, c'est une frustration que le genre nomme explicitement | à vérifier en jouant |
| 5 | **Renfort visuel des salves groupées** | moyen | le *chunking* : une salve radiale de 14 projectiles est le cas type | à juger en jouant d'abord |
| 6 | **Les couloirs comme convention de vague** | faible | outil de composition (motif Toaplan, 5-7 couloirs) ; gain différé | piste |
| 7 | **Conflit d'objectifs dans le score** | ? | **décision produit d'abord** : rejoue-t-on l'arc pour le score, ou le traverse-t-on une fois ? | question ouverte |

### Ce que la bible dit de NE PAS faire

- **Pas de bombe, de laser ni d'options** parce que le genre les emploie. `ADR-0010` a supprimé une
  transformation de vaisseau pour flow cassé ; ajouter des systèmes parce qu'ils existent ailleurs
  refait cette erreur.
- **Pas de rang / difficulté dynamique** avant la question n°7. C'est un mécanisme puissant qui se
  règle en aveugle et se mesure mal — et le projet sait ce que coûte un calibrage qui devient faux
  en silence (`ADR-0024`, `ADR-0026`).
- **Pas de régimes de comportement selon la performance** : cela ajouterait un cinquième axe à
  `EnemyData`, qui en a déjà quatre (`ADR-0022`). À ne pas ouvrir sans raison jouée.

### Une hypothèse de la bible démentie par le code

La bible listait **deux** garde-fous anti-spirale de la mort à vérifier. Vérification faite le
2026-08-25 :

- **Le nettoyage des balles manquait** → corrigé (ligne 1 du tableau).
- **La perte de puissance à la mort n'existe pas** — et c'est **volontaire, pas un oubli** :
  `_destroy()` et `_respawn()` ne touchent pas à `_power_level`. Nous sommes donc **plus généreux**
  que le genre, conformément à la spec §5.3 (« forgiving »). ⚠️ Rien à corriger : le vecteur de
  spirale que le genre redoute n'existe pas chez nous.

## P0 bis — Dettes du chantier du boss (clos le 2026-08-25)

> Versées ici depuis `docs/plans/2026-08-25-boss-pale-leviathan.md` **avant son archivage** :
> un plan qu'on archive ne doit rien emporter avec lui.

- [ ] **Trois coques sont sans UV** — `choir_harvester` **0/61**, `crescent_interceptor` 0/7,
  `needle_scout` 0/7, vérifié le 2026-08-25. Ce n'est pas cosmétique : `codex_screen.gd` leur
  applique `HullDetail.apply()`, qui échantillonne alors la feuille de détail **en un seul
  texel**. Correctif : un `ak.box_project_uv()` par script — mais ça change le rendu en jeu.
- [ ] **`HarvesterCombat` attache ses `Beam` comme le Leviathan le faisait** — enfants d'un
  `Node` sous le `BossController`, donc **doublement transformés**. Le Leviathan est corrigé
  (`top_level = true`) et c'est **le seul endroit du dépôt où ce drapeau apparaît** : le
  mini-boss n'a jamais été vérifié. Si ses faisceaux sont décalés, personne ne l'a remarqué.
- [ ] **`BOSS_PALE_LEVIATHAN.md` décrit toujours quatre phases** — **11 mentions** de phase 4,
  alors qu'`ADR-0021` en a fait trois cycles. Ses §4 à §6 sont de la matière non employée.
- [ ] **Trois coques à 97-98 % de garde-fous de script** posés sans justification mesurée
  (`null_maw` 7 000, `crescent_interceptor` 3 000, `leech_drone` 4 000), alors que le plafond
  normatif de leur classe est **12 000** (`ADR-0011`). Le prochain détail y butera.
- [ ] **`shaft_radius()` rend toujours la borne de sa table** (abscisses décroissantes contre
  un `lerp_table()` qui teste `x <= table[0][0]`) : c'est la **cause** des `Ring_01..05` à
  19 cm. ⚠️ La corriger donnerait un passage de 2,99 m, **sous** la cible de 4,2 m de
  `BRIEF-0083` — les deux décisions se prennent ensemble.
- [ ] **Deux points de ressenti non tranchés** : le plafond de dégâts par plongée
  (`ADR-0026`) se sent-il comme un mur ? et la jauge occupe 63 % de la barre pour 45 % du
  temps (`ADR-0024`).

## P1 — Systèmes de gameplay manquants (spec, valeur forte)

- [ ] **Missiles secondaires** (verrouillage doux, salves, recharge par bonus — `Missile Rack` en asset).
- [ ] **Overdrive** (jauge, boost temporaire ; devient « Citadel Burst » en forteresse).
- [ ] **Configurations de tir** : Spread / Lance / Orbit (touche E).
- [ ] **Familles d'ennemis** — chantier repris par une session dédiée (`ADR-0022`). Le
  **Crescent Interceptor est livré** (cette ligne l'annonçait encore comme à faire) ; restent
  Choir Mine, Leech Drone, Null Bomber, Shield Carrier, Frigate Turret. `EnemyController` est
  une base de composition prête à étendre.
- [ ] **EncounterDirector** formel (remplacer le pilotage en dur dans `graybox_root`) : timeline
  data-driven, checkpoints, synchro musique/caméra.
- [ ] **Objectifs de défense** (« Citadel Under Siege ») : batteries à protéger.
- [ ] **Scoring avancé** : multiplicateur, combos, précision ; **résumé de fin détaillé** (spec §14.3).
- [ ] **Manette** + **remapping** des touches.

## P2 — Accessibilité & méta (spec §13, §19)

- [ ] **Accessibilité** : réduction shake/flash, intensité bloom, contraste renforcé, sous-titres, pause.
- [ ] **Presets graphiques** (Low/Medium/High/Ultra) + option FPS/VSync exposée.
- [ ] **Voix radio** (concepts personnages produits par la forge) — à sonoriser + sous-titrer.
- [ ] **Checkpoints** formels (avant appontage / avant boss).

## P3 — Art & finition

- [ ] **Enrichir les coques 3D** — les meshes existent mais restent sobres. (ex-tâche **H1**).
- [ ] **Enrichir le fond** — la nébuleuse est belle mais uniforme : aucun élément remarquable
  (planète, bande galactique, débris qui dérivent). (ex-tâche **H2**).
- [ ] **Couleur des explosions** : arbitrer orange chaud vs consigne « froid/désaturé ».
- [x] ~~⚠️ **Les coques lisent BEAUCOUP plus sombre en jeu qu'en rendu studio.**~~ **Résolu le
  22/07/2026 — ADR-0016.** Le diagnostic du 20/07 (« c'est l'éclairage de scène, pas les meshes »)
  était juste mais n'expliquait qu'**un cinquième** de l'écart, et son correctif n'avait été
  appliqué qu'à l'écran titre. Deux causes, mesurées : la **troisième lumière** (remplissage)
  manquait dans `graybox.tscn`, et surtout le post-traitement rétro pivotait son contraste à **0,5**
  sur une image dont tous les tons vivent **sous 0,25** — il ne pouvait donc que soustraire
  (−22 % sur la coque, −90 % sur le fond). Corrigé par un `lift` en gamma dans le shader. Gain
  final : **+25,8 %** de luminance sur la coque du joueur.
  ⚠️ Reste vrai : juger une coque au seul rendu studio la flatte. Toujours confirmer par une
  capture en jeu.
- [ ] **Étendre le bestiaire au-delà des coques** — l'écran existe, et la famille `FORTRESS`
  (ADR-0015, addendum) a montré comment lui ajouter une nature de coque sans tordre le gabarit.
  Restent hors catalogue : les **bonus** et les **projectiles**. Un bonus n'a ni dimensions ni
  structure : lui donner sa propre famille, comme on l'a fait pour la forteresse, plutôt que de
  lui servir un gabarit de coque — c'est en le forçant qu'on obtient des colonnes de tirets.
- [ ] **BRIEF-0019 (frégates)** : prompt prêt, planche raster à générer.
- [ ] ⚠️ Les **SVG picturaux de la forge sont écartés** (projectiles, explosions, parallaxe) : aplats
  vectoriels, inutilisables face au bloom (**ADR-0006**). Le SVG reste bon pour l'**UI et les icônes**.

## P4 — Dette technique

- [ ] **Flag `--no-shadow`** pour bissecter le coût de l'éclairage (le projet a déjà `--no-backdrop`
  et `--no-glow`). Demandé par `godot-verifier`, qui ne peut pas isoler le coût des ombres sans lui.
- [ ] **Extraire un `FortressController`** (le contrôle est aujourd'hui dans `graybox_root`).
- [ ] **Swept collision** pour projectiles rapides (spec §21.2).
- [ ] **Tests d'intégration** (spawn vague, mort ennemi, transition de phase) via harnais headless.
- [ ] **Export release** + icône/console off + manifeste/hash.
- [x] ~~**Fuite à la sortie** : 8 ObjectDB leaked / 4 resources still in use (tweens/timers non
  libérés).~~ **Résolu le 2026-08-23.** Le diagnostic « tweens/timers » était faux, et le chiffre
  avait entre-temps décuplé (**789** objets fuités / 10 resources / pages du `PagedAllocator`).
  Sondé fichier par fichier : **la totalité venait d'un seul test**, `test_leviathan_combat.gd`,
  qui instancie un `LeviathanCombat` (`extends Node`) par méthode. Un Node construit à la main hors
  arbre n'a **aucun parent pour le récupérer**, là où les unités `RefCounted` meurent avec le cas de
  test — et Godot ne rapporte la pile qu'à la sortie, donc le bruit ne désigne jamais son coupable.
  ⚠️ **Résolu POUR LE RUNNER DE TESTS seulement — le jeu, lui, n'arrête pas ses flux audio à la
  sortie.** Diagnostic complet (`--verbose`, jeu entier) : les quinze instances fuitées sont
  **toutes** audio — `AudioStreamWAV` ×3, `AudioStreamPlaybackWAV` ×4, `OggPacketSequence` ×2,
  `AudioStreamOggVorbis` ×2, `AudioStreamPlaybackOggVorbis` ×2, `OggPacketSequencePlayback` ×2 ;
  ressources retenues : `player_pulse.wav`, `enemy_pulse.wav`, `engine_loop.wav`, `main_theme.ogg`,
  `launch.ogg`. **Aucune géométrie, aucun matériau, aucun nœud.**
  **La règle est mécanique : le compte vaut 2 × le nombre de sons en cours de lecture** — 4/2 sur
  l'écran-titre (le thème seul), 14/7 en combat (thème + lancement + trois boucles de SFX).
  → Correctif : un `stop()` des flux à la sortie, dans `AudioManager`. Non fait.
  ✅ **Le RUNNER, lui, est propre** : `tests/test_case.gd` expose `track()` / `free_tracked()`,
  appelé après chaque méthode ; la sortie du check ne porte plus une seule ligne de fuite.
  ⚠️ Restent 3 `ERROR: Condition "!is_inside_tree()" is true`, **préexistantes et sans rapport** :
  `BossController.defeat()` fait `defeated.emit(global_position)` sur un boss que les tests
  montent hors arbre. Inoffensif, mais non étiqueté `[test] expected error below` comme les deux
  autres erreurs volontaires du run — un lecteur les prend pour un vrai défaut.
  ⚠️ **Mesurer avec un `quit` DÉTERMINISTE**, sinon le chiffre n'en est pas un : en headless,
  `godot4 --headless --quit-after N` arrête à une image fixe et rend cinq fois le même relevé. Un
  lancement Windows via `play.sh` s'arrête, lui, à un instant variable — d'où des relevés qui ont
  donné `0/0`, `4/2` et `8/4` pour la même commande, et une accusation portée à tort contre la
  chambre du noyau du boss. Le phénomène est parfaitement déterministe ; c'était la méthode qui ne
  l'était pas.
- ⚠️ **Quatre coques sur dix sont sans UV, donc impossibles à texturer** — mesuré le 2026-08-23
  **une fois chargées dans Godot** (`mesh.surface_get_format() & ARRAY_FORMAT_TEX_UV`) :
  `choir_harvester` **0/61** (le mini-boss), `crescent_interceptor` 0/7, `needle_scout` 0/7,
  `null_maw` 0/36 avant sa reforge. Saine : `pale_leviathan` **145/145**.
  Cause : sans `_triangulate_ngons()` ni `box_project_uv()`, le dépliage n'est jamais produit — et
  aucun importateur ne peut le deviner. Ce n'est pas un rendu dégradé aujourd'hui, c'est une **porte
  fermée pour demain** : `HullDetail.apply()` n'a rien où plaquer.
  ⚠️ **Correction d'une conclusion fausse** : cette ligne a d'abord annoncé « sans tangentes », sur
  un comptage de `TANGENT` dans le JSON des `.glb`. Les tangentes sont **fabriquées par Godot à
  l'import** (`meshes/ensure_tangents=true`, identique sur toutes les coques) : `needle_scout` passe
  de 0/7 dans le fichier à 7/7 chargées. Le fichier ne dit pas ce dont le moteur dispose.
- ⚠️ **`HarvesterCombat` attache ses `Beam` comme le Leviathan le faisait** — enfants d'un
  `Node` sous le `BossController`, donc doublement transformés. Le Leviathan est corrigé
  (`top_level = true`) ; **le mini-boss n'a pas été vérifié**. Si ses faisceaux sont décalés,
  personne ne l'a jamais remarqué.
- Le document de conception `BOSS_PALE_LEVIATHAN.md` décrit toujours quatre phases. Il porte un
  avertissement en tête et sert encore pour les assets ; ses §4 à §6 sont de la matière non
  employée.

### Ce qui est acquis

| Livrable | Où | État |
|---|---|---|
| Conception du boss (4 phases, chiffres, invariants, spec 3D, 11 prompts) | `docs/design/BOSS_PALE_LEVIATHAN.md` | ✅ |
| Décision + dimensions 11 × 14 m | `ADR-0018`, tableau d'`ADR-0008` amendé | ✅ |
| Les 11 images (3 planches, 5 textures, 3 décors/VFX) | `assets/reference/concepts/`, `assets/source/` | ✅ mesurées, regardées, provenance au CSV |
| **Coque + silhouette (BRIEF-0041)** — noyau sphérique, épines longues/inégales, croissant asymétrique | `build_pale_leviathan.py`, `pale_leviathan.glb` | ✅ mesurée, rendue, regardée (voir réserve) |
| `GravityWell`, `TargetableProjectile` | `scripts/gameplay/` | ✅ 25 tests (le puits sert désormais les vagues d'aspiration de la phase 2) |
| `LeviathanTuning` + 6 invariants | `resources/data/` | ✅ 20 tests |
| `LeviathanPlate`, `LeviathanCombat` | `scripts/bosses/` | ✅ refondus par ADR-0020 ; `LeviathanSpike` supprimé avec ses 13 tests |

`./scripts/check.sh` : **311 tests verts** (les deux sessions confondues).

### ✅ BRIEF-0041 (silhouette) — livré et intégré

La reforge de silhouette était en réalité **déjà complète dans le script commité** (`0af3123`) : le
message WIP sous-décrivait son contenu (sphère du noyau, arc de coquille, épines allongées/inégales,
gonflement du croissant, tous présents). Le `9,481 m` de la note de reprise était un état
intermédiaire écarté ; le script commité produit **11,03 m et passe le contrat d'export**. La coque
a été **régénérée** (le `.glb` sur disque était encore celui de BRIEF-0040) puis vérifiée point par
point, pas sur la foi du rapport :

- **bbox 11,0313 × 3,1620 × 13,9972 m** (X +0,28 %, Z −0,02 %, Y ≤ 3,20), 27 710 tris / 40 630 sommets.
- Matériaux aux 3 cibles : `AA_Hull` 35,2 % (≥ 30), `AA_Emissive_Engine` 7,8 % (≤ 8), `AA_Greeble` 17,9 % (≤ 20).
- Contrat de noms intact (30 maillages, parentage exact), `TANGENT` + `TEXCOORD_0` sur 30/30.
- Déterminisme OK, sha256 `98529ce7…`. Rendu de recette : `docs/forge/output/BRIEF-0041-planche-quatre-vues.png`.

**3 des 4 écarts résolus et lisibles** : symétrie→asymétrie, noyau plat→sphère saillante, épines
courtes→longs dards inégaux. **Réserve visuelle non bloquante** (écart n°4, candidate à un polish
ultérieur) : la coquille lit comme des **anneaux concentriques machinés** plutôt qu'une **carapace de
tuiles chevauchantes**, et l'incomplétude du croissant reste peu dramatique. Levier propre si on
l'ouvre un jour : **interrompre les bandes concentriques côté ouverture** (avant-tribord) plutôt
qu'élargir l'encoche — travail de géométrie de coquille avec incidence sur le harnais de dégagement.
La méthode de revue est capitalisée dans `.claude/resources/pratique-revue-asset.md`.

### ✅ Câblage de scène + relais niveau — fait (commit `feat(boss): le Leviathan combat`)

`pale_leviathan.tscn` monte `LeviathanCombat` (`external_attacks = true`) avec
`resources/bosses/pale_leviathan_tuning.tres`. Le relais complet est dans `graybox_root.gd` :
`structure_changed` → jauge continue, `pull_changed` → `PlayerFighterController.apply_pull()`,
`piece_gauge_changed` → 4 pastilles (`FighterHUD.set_boss_limbs`, recentrées, 0 régression Harvester),
`piece_destroyed` → VFX/SFX, `phase_entered` → bannières par phase. **Deux trous comblés au passage** :
le boss ne mourait jamais (`BossController.defeat()` ajouté ; le module l'appelle quand le cœur tombe)
et le corps n'était jamais clos (il l'est désormais de bout en bout, seul le cœur compte). Vérifié
Windows (4 phases, HUD, aspiration ; GPU 0,92 ms) + 2 tests montés sur un vrai `BossController`.

### Ce qui reste, dans l'ordre

1. **Détachement visuel des épines** (3ᵉ primitive, §8.2 du document) — différée exprès : elle dépend
   des nœuds de la coque, qui bougeaient encore.
2. **Textures** : dériver dans `assets/imported/textures/leviathan/` **et** écrire
   `scripts/fx/leviathan_detail.gd` dans le même commit (`CLAUDE.md` : rien d'inutilisé dans
   `imported/`). Paramètres de dérivation consignés au §11.3 du document de conception.
3. **Décor** : vortex et landmark de l'arène (`--mode black`), câblés dans `space_backdrop.tscn`.
4. **Polish silhouette (optionnel)** : réserve écart n°4 du croissant (voir plus haut).
5. **Brief séparé** : `build_choir_harvester.py` n'a ni `_triangulate_ngons()` ni `box_project_uv()`
   — le mini-boss est probablement sans tangentes, donc intexturable. Trouvaille du BRIEF-0040.

---

## Notes de reprise importantes

- **Perf** : ne jamais mesurer en FPS depuis un lancement automatisé (Windows bride la présentation ;
  relevés absurdes de 2 à 17 FPS, non monotones). Utiliser le **temps GPU par image**.
  ⚠️ Un chiffre n'a de sens **qu'avec sa machine** : le poste de dev depuis le 20/07/2026 est un
  portable **Quadro T1000**, où le même build rend ~12 ms contre ~0,84 ms sur la RTX 4080 de la spec.
  → `.claude/resources/howto-mesurer-la-perf.md`
- **À trancher — statut du poste Quadro T1000** : machine de référence, ou poste d'appoint ? Tant que
  ce n'est pas décidé, la spec (§ machine de référence RTX 4080) et le poste réel divergent. Si ce
  poste devient la référence, réviser `docs/SPEC_AEGIS_ASCENDANT.md:9`, `ADR-0002`, et la cible
  « 120 FPS à 1440p » (§2526) — hors d'atteinte sur ce GPU.
- **Vérifier un rendu** : `--capture` écrit un PNG lisible depuis WSL. ⚠️ effacer le PNG **avant**,
  et les flags passent **après `++`**. → `.claude/resources/howto-verifier-un-rendu.md`
- **Un asset de la forge n'est pas validé tant qu'il n'a pas été rendu et regardé** (ADR-0006).
- **Plusieurs agents en parallèle** : `C:\tmp` et le processus Windows ne sont **pas** cloisonnés par
  les worktrees — un déploiement tue le jeu d'un autre agent.
  → `.claude/resources/pratique-ecrivain-unique.md`
- **Références visuelles** : `assets/reference/inspiration/` (`REFERENCE_INDEX.md`) — cible d'inspiration
  du rendu, versionnées (ADR-0009 supersede la quarantaine d'ADR-0005). Production toujours originale.
