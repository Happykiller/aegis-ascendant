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

## Outillage de développement — demandé le 2026-08-28

> ✅ **Les deux lignes ci-dessous sont LIVRÉES** (commits `c745be5` et `f821292`, 2026-08-28).
> Laissées ici pour mémoire ; ne rien y rouvrir.

- [x] **Afficher les zones de collision, toujours, en développement.** `SolidsOverlay`
  (`--show-solids`, actif par défaut en build debug, `--hide-solids` pour une capture propre,
  jamais en release). C'est cet outil, et lui seul, qui a montré que le décor de la chambre
  tournait **à l'envers** de sa collision après quatre correctifs à l'aveugle. ✅ **L'option de
  menu existe** : une section DÉBOGAGE dans les Options, comme l'opérateur l'avait suggéré —
  « voire même laisser une option dans le menu ».
- [x] **L'étendre aux autres lieux** — ✅ l'overlay dessine désormais aussi ce qu'une **balle**
  touche (`BulletTarget`), dans une couleur distincte. L'écart entre « ce qui arrête un corps » et
  « ce qui arrête une balle » se voit : le second défaut de la soirée, le noyau qui se faisait
  écran, se serait vu du premier coup.

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
| [`2026-08-29-niveau-2-refonte-geometrie.md`](plans/2026-08-29-niveau-2-refonte-geometrie.md) | ⚠️ **La géométrie ne porte pas les fonctions de gameplay** : la tourelle lit comme un jeton, le hangar comme un bouton, l'artère comme un laser. Kit modulaire, cavités réelles, palette 80/15/5 | **lots 1-5 livrés** et vérifiés en capture ; **LOT 6 (décoration) DÉBLOQUÉ** — la partie jouée qu'il attendait a eu lieu le 2026-09-03 |
| [`2026-09-03-citadelle-de-defense-midpoint.md`](plans/2026-09-03-citadelle-de-defense-midpoint.md) | **Un verrou de level design a mi-parcours** : une fortification transversale ferme la route, deux relais alimentent un bouclier, le noyau tombe et le passage s'ouvre. **Pas un boss.** ⚠️ Deux chiffres decident : le budget vertical est de **1,30 m** quand le brief demande 2,50, et la mi-parcours n'offre que **18 m** de coque libre | **a appliquer** — rien d'engage, **3 arbitrages attendent l'operateur** (symetrie, orange hors palette, voisinage du noeud d'epine) |
| [`2026-08-29-niveau-2-execution.md`](plans/2026-08-29-niveau-2-execution.md) | **Le niveau 2 de bout en bout** : campagne, coque de 6,8 km, trois mécaniques de coque, voix, dialogues, briefings, demandes de texture, équilibrage | **lots A à G livrés** ; les cinq textures `TEX-0010` à `TEX-0014` sont **livrées et intégrées** (journal : « coque habillée — 21 surfaces »). Reste la **mesure GPU sur la Quadro T1000** |
| [`2026-08-27-chambre-du-reacteur-jouable.md`](plans/2026-08-27-chambre-du-reacteur-jouable.md) | La chambre a été taillée pour un chasseur-**disque** ; il est une **capsule**. ⚠️ Le chiffre qui a justifié d'agrandir l'arène — 4,22 × 1,76 — était **faux** : la capsule s'allongeait de son propre rayon aux deux bouts. Le corps réel fait **2,46 × 1,76** (`ADR-0034`, 2026-08-28). L'agrandissement tient (la chambre est jouable, le banc est vert), mais il a été décidé sur un chasseur 71 % trop long | **lots 1-4 livrés**, reste la plongée jouée |

> ✅ **L'enrichissement du niveau 2 est CLOS** (2026-09-03) — les quatre lots des 20
> consignes sont livrés, le plan est dans [`plans/archive/`](plans/archive/). Deux
> consignes assumées non exécutées : la **11** (orienter une baie demanderait de refaire
> le mécanisme de `BRIEF-0091`, chiffré non faisable) et la **12** (bastions construits,
> mesurés, **retirés** — 33 m de bordé pour aucune lecture nouvelle). Livré à **261,0 m
> de calme, 52,2 %**, soit **+1,9 point** — et non les +8,3 annoncés en cours de route.
>
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

## Ouvert par la revue du 2026-08-28 (ADR-0034)

Deux lignes de comptabilité, pour que personne ne les redécouvre ni ne les repropose à l'aveugle.

- **Défaut LATENT de la gerbe du Léviathan.** `_fire_fans()` tire depuis `origin + 2,6` : une
  bouche peut naître au-dessus de la coupe des projectiles (13,0) et la balle mourrait à l'image
  de sa création, en silence. **Mesuré en jeu : zéro occurrence** sur 110 s de boss — les plaques
  qui tirent sont toujours sous la ligne. `BulletManager` a été **durci** (on ne retire pas ce qui
  n'est jamais entré, le `ttl` borne l'attente), donc le piège est refermé sans que le jeu change.
  ⚠️ Ne pas rouvrir en croyant corriger un bug vivant : ce n'en est pas un. Il l'était en revanche
  sur les **missiles**, qui naissent au centre du boss.
- **Découper la présentation de la plongée hors de `graybox_root.gd` : ÉVALUÉ ET ÉCARTÉ.** Les
  ~300 lignes de la section « plongée » ne forment pas un module : elles appellent `_sfx`,
  `_banner`, `_hud`, `_boom`, `_frame_chamber`, `GameplayPlane.use_bounds`, et touchent `_player`,
  `_leviathan`, `_final_boss`, `_regen_plates`, `_core_marker_age`. Les sortir demanderait soit une
  référence arrière vers le niveau (un couplage pire), soit **huit signaux de retour** — dix appels
  directs et lisibles remplacés par de l'indirection. Ce n'est pas un mélange de modules, c'est le
  **script d'un acte**. Le seul vrai candidat, si le sujet revient : la présentation de la chambre
  (décor, caméra, fond, repère de cible), en assumant les signaux.
  ✅ Ce qui a été extrait, lui, était propre : les instruments `--dive-probe` / `--dive-trace` →
  `scripts/debug/dive_instruments.gd`, désormais **testable** (il ne l'était par rien).

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

## ⚠️ Un défaut silencieux du kit de forge, corrigé — mais son passif reste à mesurer

- [ ] **Quels assets ont souffert du dépliage sur quads gauches ?** `ak.box_project_uv()`
      projetait selon une normale MOYENNE : sur un quad gauche, cette normale n'est celle
      d'aucun des deux triangles exportés, et l'un des deux pouvait sortir projeté selon un axe
      qui n'est pas le sien — **en silence**. Mesuré par la forge : densité minimale 0,078 pour
      une borne théorique de 0,116, soit un étirement que la projection en boîte ne *peut pas*
      produire. Corrigé le 2026-08-29 (`ak.triangulate()` triangule tout AVANT le dépliage, et
      c'est `box_project_uv` qui l'appelle).
      ⚠️ **Quinze scripts de coque dépendent de cette fonction** : `specter_9`, `pale_leviathan`,
      `aegis_citadel`, `choir_mine`, `leech_drone`, `null_maw`, `shield_carrier`,
      `core_interior`, `moon_flyby`, `citadel_turret`, `citadel_beacon`, `impact_debris`,
      `bay_kit`, `long_cortege`, `turret_kit`. Le seul verdict qui vaille est un **rebuild
      comparé** : reconstruire chacun et voir si son sha256 bouge. Un sha inchangé prouve qu'il
      n'avait aucun quad gauche ; un sha qui bouge demande de regarder la planche.

## ⚠️ Une décision qui appartient à l'opérateur, et qui débloquerait beaucoup

- [ ] **Le Quadro T1000 est-il encore une cible ?** `ADR-0011` a calé TOUS les budgets de
      triangles dessus — « sur le poste courant (Quadro T1000, budget 16,7 ms) » — et son §115
      dit que ces budgets sont le premier levier si la cible change. L'opérateur joue sur une
      **RTX 4080** et a demandé de ne pas être avare sur la qualité des modèles (2026-08-29).
      ⚠️ **Ce n'est pas bloquant aujourd'hui** : la classe « structure » accorde 120 000 tri, la
      coque du niveau 2 en consomme 40 446, il reste 79 554. Mais si la T1000 sort du périmètre,
      les budgets peuvent tripler, et c'est une décision de produit, pas de session.
      ⚠️ **Et ce n'est PAS ce qui limite la qualité visible.** Le post-traitement rétro rend à
      960×540, soit 23 px/m sur la coque : toute géométrie plus fine que ~9 cm est moyennée
      puis disparaît — mesuré, la coque a perdu 33 % de luminance pour un relief invisible.
      Relever le budget permet plus de SILHOUETTE et plus de VARIÉTÉ, pas plus de finesse.

## ✅ TRANCHÉ — la portée du projet est un partage entre amis (2026-09-03)

**Décision du propriétaire, prise en connaissance des faits ci-dessous. Le sujet est CLOS : ne pas
le rouvrir, ne pas le reposer en début de session.**

`ADR-0009` et `ADR-0014` avaient été écrits sur la formule « personnel, non commercial, **non
distribué** », et prévoyaient une révision en cas de distribution. Les faits ont bougé — les deux
dépôts sont publics, quatre releases existent — mais **la portée réelle n'a pas changé** : le jeu
est partagé à des amis, il n'est ni vendu ni promu. Le propriétaire assume le risque IP, comme les
deux ADR l'énonçaient déjà.

Ce que ça règle, et qu'il est inutile de recalculer :

- les 10 planches de `assets/reference/inspiration/` **restent versionnées** (LFS) et restent la
  cible d'inspiration du rendu — `ADR-0009` s'applique tel quel ;
- le **Specter-9 garde le plan de sa planche**, dérives comprises — `ADR-0014` s'applique tel quel,
  et son « premier élément à refaire en cas de distribution » ne se déclenche pas ;
- aucune purge d'arbre ni d'historique n'est à prévoir ; aucun dépôt n'est à repasser en privé.

⚠️ **Le seul cas qui rouvrirait le sujet est une VENTE ou une mise en boutique** (Steam, itch.io) —
c'est-à-dire le mot « non commercial », qui est le seul des trois à n'avoir jamais bougé. Rien
d'autre : ni le nombre de releases, ni la visibilité des dépôts, ni un nouvel asset de référence.

## ⚠️ La densité ×3,5 du niveau 2 — jouée le 2026-09-03, son coût toujours pas mesuré

> ✅ **Le titre de cette section disait « n'a été jouée par personne » : ce n'est plus vrai.** La
> partie du 2026-09-03 (survol complet, victoire, score 77130) a été jouée avec la patrouille à
> 209 coques, et l'opérateur n'a pas demandé de redescendre. **Ce qui reste ouvert est le COÛT**,
> ci-dessous — la jouabilité est tranchée, la performance non.

L'opérateur a validé le niveau à **59 coques** de patrouille (« c'est beaucoup mieux »), puis a
demandé « au moins ×3 ou ×4 ». La patrouille livrée et **publiée en v0.4.0** en porte **209**, sur
55 entrées, avec un pas descendu de 7,0 s à 2,8 s. Personne ne l'a jouée à la main — ni lui, ni
moi.

**Et son coût n'est connu que sur la RTX 4080** : 1,103 ms/image, relevé à un **instant** du
tronçon 02, non comparable au 2,076 ms d'avant densification (autre moment, autre contenu à
l'écran). C'est la **Quadro T1000** qui contraint le budget (×14 à build identique, `ADR-0011`),
et elle n'a pas été mesurée. Premier endroit où regarder si un joueur signale des saccades.

## ⚠️ Niveau 2 — ce que le LOT B1 laisse ouvert (2026-09-03)

- [x] ~~**B2 — l'asymétrie**~~ — livré, et par la voie (b) que le plan disait « beaucoup plus
      chère ». ⚠️ **L'estimation était fausse, et la raison vaut d'être retenue** : casser le
      miroir ne change PAS la topologie de l'anneau (mêmes indices, mêmes matériaux, mêmes
      drapeaux) — seules les abscisses d'un côté bougent. Quatre fonctions, pas une refonte. Et
      (a) aurait échoué sur le critère 20 : un module posé sur le pont ne change pas le CONTOUR.
- [x] ~~**B3 — le relief en creux**~~ — livré : 4 fosses de 12 × 4,6 m, profondes de 1,55 m, pour
      384 triangles (les abscisses 2,20 et 6,80 étaient déjà des points du profil). ⚠️ **La leçon
      qui dépasse ce lot** : sans arête claire, un creux n'est pas un volume, c'est une tache. La
      géométrie était juste, sondée et mesurée dans le `.glb`, et restait invisible en jeu.
- [x] ~~**B4 — le repositionnement des installations**~~ — livré : 22 des 24 ont bougé, coque calme
      50,3 → **58,6 %**, emprises fusionnées 248,6 → 206,8 m. ⚠️ **Le « plafond théorique » de la
      forge n'en était pas un** : les emprises FUSIONNENT quand elles se recouvrent, donc grouper
      libère du calme. La clause « sans déplacer un marqueur » portait tout le poids.
- [ ] **Quatre-vingts mètres sans aucune variation, entre s = 402 et 482.** C'est la conséquence
      des gardes : `Turret_13` porte une batterie, `Bay_07` est une ouverture, et Ambry occupe
      446 à 474. La seule fenêtre libre y fait 10 m, trop court pour une transition. ⚠️ **Le
      tronçon 5 est donc le moins mouvementé du niveau, au moment où le rythme devrait monter.**
      À reprendre au lot B4, quand les installations pourront bouger.
- [ ] **Le témoin à largeur nominale n'a pas pu être isolé.** Toute zone à `kx = 1` voisine une
      transition, si bien que la part de perspective dans l'élargissement mesuré (1 094 → 1 517 px)
      n'est pas chiffrée. Ce qui tranche visuellement est la FORME du bord, pas le nombre.

## ⚠️ Niveau 2 — ce que le LOT C laisse ouvert (2026-09-03)

- [ ] **`build_bastions()` est du code mort volontaire.** La table `BASTIONS` est vide : trois
      bastions ont été construits, mesurés à 33 m de bordé, et retirés parce qu'ils faisaient
      passer le calme SOUS son point de départ. Le code et son assertion restent. ⚠️ **À supprimer
      si personne ne les réclame** — du code qui ne s'exécute jamais finit par mentir.
- [ ] **C2 — l'orientation des ponts d'envol n'est pas modifiable** à coût raisonnable : une
      ouverture est un trou GENERE dans la peau (indices d'anneau + points de profil en dur), pas
      un objet posé. La tourner demanderait de refaire le mécanisme que `BRIEF-0091` a construit
      pour éviter les booléens. À rouvrir si les sept hangars se ressemblent trop **en jouant**.
- [ ] ⚠️ **Le « PLAFOND THEORIQUE » du rapport ne compte que les marqueurs** (293,2 m), alors que
      le calme réel est de 261,0 m depuis que fosses, passerelle et bastions y entrent. Les deux
      chiffres sont justes et mesurent deux choses ; leur voisinage dans le même rapport peut
      tromper un lecteur pressé.

## ⚠️ Niveau 2 — le placement des tourelles, audité le 2026-09-03

> Audit déclenché par une observation de l'opérateur en jouant : « des petites tourelles dans les
> ponts de décollage ». Les tables sont relues dans les sources (`TURRETS`, `BAYS`, `PITS`,
> `SPINES`, `AMBRY_*` de `build_long_cortege.py`, `BATTERIES` de `cortege_hardpoints.gd`).

- [x] ~~**Trois pièces légères dans l'ouverture de `Bay_06`**~~ — corrigé : la batterie de
      `Turret_10` est retournée vers la proue. ⚠️ **Le reste de la coque est net** : zéro pièce
      légère sur un socle lourd, zéro pièce qui en traverse une autre, zéro tourelle lourde dans
      une baie. Le défaut était unique, et il était le seul que le jeu montrait.
- [ ] **Quatre paires de lourdes reproduisent le MÊME motif** : `Turret_01/02` (5,3 m),
      `07/08` (5,0), `11/12` (5,0), `13/14` (5,2) — deux pièces sur bords opposés, écart de 5,0 à
      5,3 m, **étendue de 0,3 m sur quatre occurrences**. C'est la signature d'un optimiseur qui
      **sature sa contrainte** : le recuit du lot B4 avait 5,00 m comme borne anti-symétrie, et il
      s'y est collé quatre fois. Un joueur qui a lu la première paire sait lire les trois autres.
      ⚠️ **Le corriger n'est pas un réglage** : un marqueur déplacé rejoue son Y (échantillonné sur
      la peau) et les fenêtres de relâche du `BRIEF-0092`. C'est un arbitrage d'opérateur, pas une
      déduction de session — et il se juge en jouant, les paires étant séparées de 100 à 190 m
      (≈ 80 s au rythme du survol).
- [ ] **Les `|x|` se rangent en deux rails, et c'est structurel.** 11 tourelles entre 8,2 et 10,2
      (pont médian), 6 entre 5,6 et 6,2 (pont intérieur), **rien entre 6,2 et 8,2** — c'est la
      contremarche de chine (6,80 à 7,35) plus les gardes de socle. La coque n'a pas de position
      intermédiaire à offrir ; le seul levier serait un palier de plus, donc une reforge.
- [ ] **Le tronçon 5 porte 5 lourdes sur 17**, dont trois d'affilée (`15`, `16`, `17` à 463,3 /
      470,0 / 478,8, deux du même bord). Densité voulue en fin de niveau — à confirmer en jouant,
      c'est le même endroit que les trois autres manques déjà consignés du tronçon 5.

## ⚠️ Niveau 2 — ce que le LOT B4 laisse ouvert (2026-09-03)

- [x] ~~**Le nouveau rythme n'a été jugé par personne EN JOUANT.**~~ — jugé le **2026-09-03**,
      validé par l'opérateur **sans retouche**. Énoncé d'origine — ⚠️ C'est le lot qui touche le
      plus directement au ressenti : 22 installations ont changé de station, donc l'ordre et
      l'espacement de tout ce que le joueur rencontre. La densité instantanée est bornée (3
      installations par fenêtre de 20 m, inchangée) et `test_the_survey_does_not_open_on_dead_air`
      garde l'ouverture — mais **une borne n'est pas un ressenti**.
- [ ] **Les fenêtres de relâche et d'engagement du `BRIEF-0092` n'ont pas été rejouées.** Elles
      portaient les positions d'origine. Rien ne dit qu'elles sont fausses — rien ne dit qu'elles
      sont encore vraies.
- [ ] **Le solveur vit dans le scratchpad, pas dans le dépôt.** Les positions sont désormais des
      constantes comme les autres ; le recuit qui les a trouvées, avec ses huit contraintes
      apprises une à une, n'est nulle part. ⚠️ Le jour où une installation doit bouger, tout est à
      refaire — ou à réapprendre par les mêmes refus.
- [ ] **Deux tourelles restent à 5,3 m l'une de l'autre** (`Turret_01`/`02` à 68,0 et 73,3, bords
      opposés) : la contrainte anti-symétrie exige 5 m, elles y sont tout juste. À regarder en
      jouant — c'est la toute première rencontre du niveau.

## ⚠️ Niveau 2 — ce que le LOT B3 laisse ouvert (2026-09-03)

- [ ] **Quatre fosses seulement, et aucune sur les tronçons 1 et 5.** Les gardes (socles, baies,
      Ambry, nœuds) ne laissent pas de place ailleurs sans déplacer un marqueur. ⚠️ Le tronçon 5
      cumule donc les trois manques : pas de variation de largeur entre s = 402 et 482, pas de
      fosse, et la part calme la plus basse du niveau (33,6 %).
- [ ] **Le liseré clair des bouts de fosse n'a pas été mesuré en aire.** `BRIEF-0089` a montré
      qu'un matériau clair coûte plus de pixels que sa surface ne le laisse croire, et la palette
      80/15/5 est un contrat. Huit plans de 4,6 m ont été ajoutés en `AA_Trim` sans que l'aire par
      matériau soit re-relevée.
- [ ] **`_face_towards()` ne sert qu'aux fosses.** Les autres familles de modules posent encore
      leurs faces à l'ordre des sommets, sans déclarer de direction — et `_assert_skin_outward()`
      ne couvre que la peau, avant tout module. ⚠️ Une face de module retournée disparaîtrait en
      jeu sans un mot ; rien ne dit qu'il n'y en a pas déjà.

## ⚠️ Niveau 2 — ce que le LOT B2 laisse ouvert (2026-09-03)

- [ ] **L'asymétrie n'a pas encore été REGARDÉE en jeu.** Elle est vérifiée numériquement (4 zones,
      écarts de 13,8 à 17,0 %, aucun cumul avec `TAPER`, largeur max 34,72 m sous la borne de
      35,00) et la coque est déterministe — mais aucune capture in-game ni planche n'a encore été
      jugée. ⚠️ C'est exactement le genre de chose qu'`ADR-0006` refuse de considérer comme acquis :
      le lot A a montré qu'une composition valide au calcul pouvait ne pas se lire à l'écran.
- [ ] **Le budget triangles est monté à 54,1 %** (48 678 / 90 000), contre 46,5 % avant la
      densification des transitions d'asymétrie. Il reste de la marge, mais B3 (le relief) et C
      (les secteurs) puisent dans le même budget, et le coût GPU n'est toujours pas mesuré sur la
      Quadro T1000.
- [ ] **Les plateaux à `kx = 1` ne font que 16 à 28 m** une fois les installations protégées : il
      n'y a plus de place pour une cinquième asymétrie sans déplacer un marqueur. ⚠️ Comme pour le
      rythme (lot D), l'espace de composition est **plafonné par les positions figées**.

## ⚠️ Niveau 2 — ce que le LOT A laisse ouvert (2026-09-03)

- [ ] **La grappe se lit-elle comme un GROUPE en jeu ?** Les batteries sont resserrées (moins de
      3 m d'étendue chacune, contre 12 à 16 m à la première écriture) et deux tests le tiennent,
      mais **aucune capture propre du groupe entier n'a été obtenue** : le tronçon 5 est encombré
      par la patrouille, et le porteur de bouclier masque la zone à chaque essai. ⚠️ C'est la
      question que le lot existe pour résoudre (consigne 9) — elle se tranche **en jouant**, pas
      en capturant.
- [ ] **Le coût GPU des 21 pièces actives n'est pas mesuré**, et surtout pas sur la Quadro T1000.
      Chacune pivote, tire et porte une cible inscrite au gestionnaire de balles pendant sa
      fenêtre. Relevés RTX 4080 pendant les captures : **5,4 à 6,0 ms/image** au tronçon 5 — mais
      avec un porteur de bouclier à l'écran, donc non comparable à quoi que ce soit.
- [ ] **Trois réglages morts, laissés en place.** `turret_burn_damage`, `turret_range` et
      `turret_beam_half_width` ne sont lus par AUCUN script ni test depuis qu'`ADR-0040` a
      remplacé le faisceau par des balles. Ils servent encore de garde aux invariants 5 et 6, ce
      qui les rend inoffensifs — mais un lecteur les prendra pour des réglages. À retirer, ou à
      rebrancher, le jour où l'on touche à l'équilibrage des tourelles.
- [ ] **La troisième échelle (point-defense) n'est pas faite**, et c'est délibéré : l'opérateur
      l'écrit « éventuelle ». Elle se décide après avoir vu la deuxième jouer.

## ⚠️ Niveau 2 — ce qui reste après la refonte de géométrie (2026-08-29)

> **Joué le 2026-09-03**, survol complet des cinq tronçons, victoire, score 77130, zéro erreur.
> L'opérateur a validé le rythme de l'enrichissement géométrique (lots A à D) **sans retouche** :
> « moi c'est ok ». C'est la nature de preuve qu'attend le **lot 6** ci-dessous — le déblocage
> reste sa décision, pas une déduction de session.

- [ ] **Donner un numéro de série aux ponts d'envol**, comme en portent déjà les tourelles
      (`turret.serial`). `[Cortege] pont d'envol détruit — tronçon 03` s'imprime **deux fois**
      dans un survol normal, puisque les stations `BAYS` 224,6 et 290,0 sont toutes deux dans le
      tronçon 03 : la chronologie se lit comme une double émission de signal. Coût déjà payé une
      fois — une investigation complète pour un comportement correct (2026-09-03). Trois lignes
      dans `cortege_bay.gd` / `cortege_root.gd`.
- [ ] **Horodater le journal du survol.** Rien n'y porte de temps : l'ordre des événements est
      sûr, les **durées** ne s'en tirent pas — ni le respect des 208 s annoncées, ni la longueur
      réelle d'une plage de calme à l'écran. C'est ce qui a empêché de mesurer le rythme du
      niveau autrement qu'au ressenti de l'opérateur (lot D, 2026-09-03).

- [ ] **Mesurer le coût GPU du survol sur la Quadro T1000.** Toutes les mesures de la session
      portent la ligne Vulkan **RTX 4080** : 0,93 à 1,71 ms par image. La machine qui CONTRAINT
      est l'autre, et le rapport entre les deux est de **×14** — ce qui placerait le niveau entre
      13 et 24 ms sur les 16,67 disponibles à 60 Hz. ⚠️ **Mais le facteur ne se transpose pas tel
      quel** : le survol REMPLACE le fond spatial complet (13,05 ms mesurés sur T1000) par un ciel
      `deep_sky` presque gratuit. Le solde peut être favorable ; tant qu'il n'est pas mesuré, on
      ne sait pas. Protocole : `.claude/resources/howto-mesurer-la-perf.md`, à 60 Hz, trois tirs
      alternés, **jamais `--novsync`**.
- [x] ~~**Les cinq images de texture** (`TEX-0010` à `TEX-0014`)~~ — livrées par l'opérateur,
      dérivées et câblées. Le journal dit « coque habillée — 21 surfaces ».
- [ ] **LOT 6 — la décoration**, dernier lot de la refonte de géométrie du niveau 2.
      ✅ **Sa condition d'ouverture est LEVÉE** : il attendait que l'opérateur juge les lots 1 à 5
      en jouant — décorer avant que les fonctions soient lisibles, c'est ajouter du bruit sur une
      hiérarchie non validée. La partie a eu lieu le **2026-09-03** (survol complet, victoire,
      score 77130, rythme validé sans retouche). **Le lot est prenable.**
- [ ] **Le neuvième slot `AA_Gear` (grège moyen)** — proposé par la forge au `BRIEF-0094`, pas
      créé. La palette de l'Unisson n'a rien entre `AA_Hull` (#24252B) et `AA_Trim` (#DDDCD2),
      ce qui empêche de tenir les 15 % d'appareillage sans forcer `AA_Trim` — or un matériau
      clair sur une arête continue occupe plus de pixels qu'une pièce entière (`BRIEF-0089`). Il
      appellerait une carte neuve, donc un `TEX-NNNN` : à prendre le jour où un asset le demande
      pour lui-même, pas pour rattraper un pourcentage.
- [ ] **`build_bay_kit._tile_close()` porte la même expression de caméra roulée** que celle que
      la forge a corrigée dans le kit de tourelle. Sans effet sur le `.glb` — c'est un helper de
      rendu de planche — mais il rendra une vignette fausse au prochain usage.
- [x] ~~**Un playtest humain du niveau 2.**~~ — fait le **2026-09-03** : survol complet des cinq
      tronçons, victoire, score 77130, zéro erreur. ⚠️ **Ce qu'il ne dit toujours pas** : les PV des
      cibles de coque restent **dimensionnés**, pas **mesurés** (ADR-0019) — la partie s'est gagnée,
      elle n'a pas relevé combien de cibles sont tombées dans leur fenêtre.
- [ ] **Les deux réglages d'habillage n'ont jamais été jugés EN JOUANT.**
      `CortegeSkin.EMISSIVE_ENERGY` (1,0 → **0,45**) et `CortegeSkin.PANEL_DAMP` (**0,45**) ont
      été arrêtés sur trois captures fixes, **au seul tronçon 2**, et sur **RTX 4080**. Une
      capture fixe ne dit rien de deux choses qui décident ici : ce que donne l'artère quand elle
      **défile** sous les yeux pendant 208 s, et si l'émissif reste distinguable des **balles**
      quand l'écran se charge. ⚠️ Le sens de l'erreur n'est pas symétrique : trop bas, l'artère
      cesse de dire que le vaisseau est vivant ; trop haut, on retrouve le « laser » que toute la
      refonte visait à supprimer.
- [ ] **Le rythme calme / installation / calme est PLAFONNÉ par les marqueurs figés.** La forge
      a mesuré 251,4 m calmes sur 500 (50,3 %) et démontré que c'est le **maximum atteignable**
      sans déplacer de marqueur : la plus large plage nue hors proue fait 22 m, où le brief en
      demande 15 à 20 **de chaque côté** d'une installation. J'ai refusé de les déplacer — ils
      portent l'équilibrage mesuré (fenêtres de relâche et d'engagement, arbitrages du
      `BRIEF-0092`). ⚠️ C'est un arbitrage, pas une limite technique : le jour où l'on voudra le
      rythme complet, il faudra rejouer ces mesures, et c'est un chantier, pas un réglage.
- [x] ~~**La proximité acceptée `Turret_14` / `Bay_07` déclare un chiffre PÉRIMÉ.**~~ — ⚠️ **caduc : `ACCEPTED_PAD_BAY_PROXIMITY` est une table VIDE** (`= ()`), elle ne déclare plus rien. L'audit du 2026-09-03 le confirme géométriquement : zéro tourelle lourde en contact avec une baie. Énoncé d'origine —
      `ACCEPTED_PAD_BAY_PROXIMITY` (dans `build_long_cortege.py`) dit « la lèvre du socle
      effleure le coaming sur 0,25 m », arbitrage du `BRIEF-0092` — donc **avant** que la
      tourelle ait des canons. Depuis le kit, ce qui dépasse n'est plus une lèvre statique mais
      un **canon qui balaie**, mesuré à ~0,55 m au-dessus du coaming pendant la rotation. La
      décision reste probablement la bonne (deux installations qui se touchent est une lecture
      crédible), mais **la table ne décrit plus ce qui se passe** : à re-mesurer et à re-déclarer
      avec sa vraie nature, sinon le prochain lecteur arbitrera sur un fait faux.

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
- [x] ~~**Écran titre**~~ — les deux moitiés sont closes. L'emblème `helios_vanguard_emblem.svg`
  **était déjà utilisé** par trois écrans (`boot.tscn`, `mission_report.tscn`, `pause_screen.tscn`)
  et l'accueil porte un `SpaceBackdrop` : il n'a jamais été « nu ». Et `title_backdrop.svg` est
  **écarté par `ADR-0042`** — sixième cadre SVG plein écran de `BRIEF-0017`, le seul qu'`ADR-0012`
  n'avait pas nommé. Il n'y a plus d'asset qui dort : il y a un asset jugé. (ex-tâche **H3**).
- [x] **Écrans** — **pause** et **victoire / rapport** reforgés dans le langage d'interface de
  l'accueil (ADR-0012). Les cadres SVG plein écran de la forge sont abandonnés, pas intégrés.
- [x] ~~**Écran d'échec de mission**~~ — **livré le 2026-07-23** (`d1f4c5a`), enrichi le
  2026-08-28 (`a5bfb61`). `MissionReport.Outcome.DEFEAT` : titre « DEFAITE », « SPECTER-9 PERDU ·
  ENTREE PORTEE AU REGISTRE », relais « 0 MS · RADIE », COMMS « SIGNAL PERDU », boutons
  **REESSAYER** / **TITRE**, et la navigatrice qui rapporte (`mission_failed`). `_on_game_over()`
  transite réellement vers `GAME_OVER` — le `continue_run()` silencieux a disparu — et le rapport
  se lève après `DEFEAT_HOLD` (1,6 s) pour ne pas escamoter la mort. Câblé dans les **deux**
  niveaux (`graybox_root`, `cortege_root`). ⚠️ **Reste un vrai trou** : aucun test ne couvre
  `mission_report.gd`, alors qu'il décide de la fin de partie et porte trois embranchements
  (REJOUER / CONTINUER / REESSAYER).
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
- [x] ~~**`shaft_radius()` rend toujours la borne de sa table**~~ — ⚠️ **caduc : la fonction n'existe plus**. Aucune occurrence dans un `.gd` ni un `.py` du dépôt ; elle ne survit que dans des rapports de forge archivés. La dette portait sur du code disparu. Énoncé d'origine — (abscisses décroissantes contre
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
- [x] ~~**EncounterDirector** formel (remplacer le pilotage en dur dans `graybox_root`)~~ —
      **livré** : `scripts/gameplay/encounter_director.gd`, monté par `LevelRoot.setup_arc()`, et
      `graybox_root.gd:271` l'appelle (`_director = setup_arc(ARC)`). Timeline
  data-driven, checkpoints, synchro musique/caméra.
- [ ] **Objectifs de défense** (« Citadel Under Siege ») : batteries à protéger.
- [ ] **Scoring avancé** : multiplicateur, combos, précision ; **résumé de fin détaillé** (spec §14.3).
- [ ] **Remapping** des touches. ⚠️ **La manette, elle, est faite** : `input_bootstrap._register_joypad()` enregistre les actions au démarrage. Seul le remapping reste, et `input_bootstrap.gd:4` l'annonce déjà comme la suite.

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

## ✅ Bible narrative et 3 répliques manquantes — LIVRÉ le 2026-08-28

`docs/lore/BIBLE.md` (BRIEF-0087) avait relevé les **trois seuls moments du jeu sans réplique** :
avant la première vague, DOCKING, VICTORY. Ils sont comblés — `VOX-0003`, trois `DialogueLine`
dans `lyra_ingame.tres`, trois cues sur le bus `Voice`, câblage dans `graybox_root.gd`
(`mission_start` seulement si `_phase == Phase.FIGHTER_WAVES`, donc jamais sur un `--skip-to-*`).
Le pilote **Wren Adaire / Halyard** est passé au canon de `docs/forge/CHARTE_CREATIVE.md`, avec sa
réserve : jamais dans la bouche de Lyra.

**Ce que le chantier a appris, et qui vaut pour la prochaine réplique** :

- ⚠️ **Le `hold` du `.tres` doit couvrir la durée du fichier — le panneau du HUD ne le sait pas.**
  `FighterHUD.say()` ne tient que `maxf(hold, 1.0) + 0,45 s` : ni frappe du texte, ni attente de
  l'audio, contrairement à la bulle de l'accueil où le temps de frappe s'ajoute. Le commentaire de
  `dialogue_line.gd` (« c'est l'audio qui commande, `hold` devient un plancher ») ne décrit donc
  que `dialogue_box.gd`. Les `hold` estimés du plan (5,5–6,5 s) coupaient deux répliques de 6,10 et
  6,72 s. **Mesurer le fichier, régler ensuite.** Garde posé :
  `test_a_line_never_leaves_the_screen_while_it_is_still_speaking`.
- ⚠️ **`mission_complete` s'entend sans se lire**, et aucun ordre d'appel n'y change rien :
  `_show_report()` cache le HUD, donc le panneau de Lyra avec lui. Assumé — si le texte doit être
  lu sur l'écran de résultats, **c'est au rapport de le porter**. À juger en jouant.
- Le garde `test_the_ingame_voice_request_matches_the_game` **nommait `VOX-0002` en dur** et
  comparait son nombre de répliques au `.tres` : ajouter du contenu conforme le cassait. Il balaye
  désormais `docs/forge/voice/`, apparie par clé, et vérifie les deux sens.
- `tools/voice/forge_voice.py` écrivait ses préversions dans `/mnt/c/Users/faro/Desktop`, **codé en
  dur sur un utilisateur qui n'existe pas** : `--preview` mourait sur un `PermissionError` après
  avoir tout synthétisé. Le Bureau se demande maintenant à Windows.
- `_lyra()` **imprime désormais la clé** (`[Lyra] <clé>`, et `clé inconnue` le cas échéant). Sans
  ça, une réplique qui ne part pas ne laisse aucune trace — c'est ce qui avait laissé les sept
  premières muettes une soirée entière avec leurs fichiers en place.

**Vérifié en jeu** (`balance-prober`, 5 lancements, 2026-08-28) : les **10 clés** de `_lyra()`
partent, dans l'ordre attendu, **zéro** `clé inconnue`, **zéro** cue non résolue. `mission_start`
sort bien dans `_ready()` sur une partie complète, et **ne sort pas** sur un `--skip-to-*`.

**Reste dû** : l'écoute des trois `_comms` par l'opérateur (règle du skill `forger-voix` — un
fichier produit n'est pas une voix validée). Elles sont sur le Bureau, dans
`lyra-mission-et-fin-essais-voix/`. Si le timbre ne convient pas, `--voix` / `--cadence` puis
`--deposer` à nouveau : rien d'autre ne bouge.

## À REJOUER — le réacteur a pris 50 % de vie (2026-08-29)

Demande de l'opérateur. La hausse seule cassait deux invariants (combat à 52 s hors cible, et
**939 PV atteignables sur les 1000 demandés par plongée** — donc un quatrième cycle, ce
qu'`ADR-0026` empêche par construction). Trois valeurs bougent donc **ensemble**, et elles ne
valent qu'ensemble :

| | Avant | Après |
|---|---|---|
| `flux_health` (le réacteur) | 2000 | **3000** |
| `dive_time` (durée d'une plongée) | 9,0 s | **10,0 s** |
| `plate_health` (une plaque d'armure) | 460 | **320** |
| *durée du combat* | 44,3 s | 48,4 s |
| *part passée sur l'armure* | 34 % | **25 %** |

⚠️ **Ce n'est pas un réglage, c'est un déplacement d'équilibre** : le boss ne devient pas plus
long, il devient plus **centré sur le réacteur**. Un tiers de temps d'armure en moins, un tiers de
temps de noyau en plus.

**Ça ne se valide qu'en jouant** (`ADR-0019`) — les invariants disent que le combat est *possible*,
jamais qu'il est *bon*. Deux choses à sentir, et une seule partie suffit :

- la phase d'armure à 320 PV la plaque **ne doit pas devenir expédiée** : c'est elle qui fait
  monter la tension avant la plongée, et le grief « lancinant » d'`ADR-0021` venait de l'excès
  inverse ;
- la plongée à 10 s **ne doit pas se mettre à traîner**. Le joueur de référence y passe désormais
  9,59 s sur 10 possibles : il n'a plus de marge, et un joueur moins précis touchera le plafond de
  temps au lieu du quota de dégâts — ce qui rouvrirait un quatrième cycle en pratique, sans que
  l'invariant ne le voie.

## Ouvert par la partie de vérification du 2026-08-28 (sans rapport avec les voix)

Trois défauts relevés en jouant l'arc en démo pour vérifier les répliques. **Aucun n'appartient au
chantier de la voix** ; ils sont ici pour ne pas être redécouverts.

- ⚠️ **Le combat CONTINUE après la défaite.** Constaté : `[Level] all fighters lost — DEFEAT,
  score 4860`, puis le Léviathan enchaîne `CYCLE 2 / 3 — armure` deux secondes plus tard, avec sa
  réplique de Lyra. Le rapport de mission se lève sur un boss qui se bat encore. `_defeated` verrouille
  le second rapport, mais **rien n'arrête le boss** — c'est le pendant exact du trou comblé à
  l'inverse (le boss qui ne mourait jamais). Le plus probable : une passe d'extinction manquante
  dans le chemin `game_over`.
- ⚠️ **Le mini-boss bloque le pilote automatique, de façon reproductible (3 runs sur 3).** L'iris du
  Choir Harvester s'ouvre **une fois** — les trois appendices à terre simultanément — puis les
  membres se reconstruisent (`limb_rebuild_time` = 14 s) et il ne se rouvre **jamais** : la démo
  n'atteint plus la victoire, quel que soit le temps laissé. Ce n'est pas de la lenteur, c'est une
  impasse. ⚠️ **Conséquence d'outillage** : `balance-prober` ne peut plus relever une chronologie
  d'arc complète, et c'est son objet même. À juger aussi à la main : si le pilote automatique n'y
  arrive pas, la fenêtre est peut-être trop étroite pour un joueur humain aussi.
- [x] ~~`[Level] ready — phase FIGHTER_WAVES` imprimé inconditionnellement~~ — corrigé le
  2026-08-28 : la ligne annonçait `FIGHTER_WAVES` même après un `--skip-to-dock`, donc elle
  paraissait **après** `[Level] DOCKING`. Elle imprime maintenant la phase réelle.
