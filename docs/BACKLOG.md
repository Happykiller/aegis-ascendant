# Backlog & pistes d'amélioration — Aegis Ascendant

> Point de reprise au **2026-07-23**. Arc jouable **`FIGHTER_WAVES → MINI_BOSS → FINAL_BOSS →
> DOCKING → VICTORY`** (ADR-0010 a supprimé la phase forteresse), **274 tests verts**.
>
> ⚠️ L'en-tête précédent annonçait un arc « appontage → forteresse » supprimé depuis, 80 tests, et
> un chemin `~/sandbox/macross` qui n'existe pas. Un point de reprise faux coûte plus qu'un point de
> reprise absent : il envoie la session suivante dans le mur sans qu'elle le questionne.

## Comment reprendre

1. `cd ~/aegis-ascendant`
2. `./scripts/check.sh` → doit être **ALL GREEN**.
3. `./scripts/play.sh` → jouer le code courant (il exporte si le build est périmé ; skill `/jouer`).
4. Lire **`.claude/resources/INDEX.md`** — le *ghost* : comment vérifier un rendu, mesurer une perf,
   réviser un asset. C'est là que vit le savoir de méthode.
5. Lire `docs/architecture/` et les **ADR** (`ADR-0001` à `ADR-0018`), qui priment sur la spec.

---

## ⏳ En cours — Pale Leviathan (coque livrée le 2026-07-23, câblage restant)

### ⏸ PRIORITÉ REPRISE — équilibrage & lisibilité (playtest opérateur, 2026-07-23)

**Le combat est câblé et fonctionne, mais il est INJOUABLE en l'état.** Verdict de l'opérateur
après plusieurs minutes de jeu réel : *« beaucoup beaucoup trop long, j'ai arrêté volontairement,
les pastilles P 1..4 se vidaient, le boss encore à 80 %, j'ai pas compris les phases, il n'a fait
qu'aller de gauche à droite, rien ne s'est passé. »* Décision actée : **coupe franche ~20 s/phase +
télégraphier la mécanique.** Deux chantiers, à faire dans cet ordre.

#### 1. Coupe des durées (÷ ~3) — le tuning, le test, le doc, un ADR

Racine : les durées visées sont énormes (phase 1 ≈ 68 s, total ≈ 3 min 10 en jeu **parfait**, bien
plus en vrai car le tir sur le corps clos ricoche sans dégât). Nouvelles valeurs, calées sur
`durée = PV / (dps 420 × occupation)` pour viser ~20 s/phase (phase 4 reste courte) :

| Champ (`resources/data/leviathan_tuning.gd` défaut **et** `resources/bosses/pale_leviathan_tuning.tres`) | Actuel | **Cible** | durée obtenue |
|---|---|---|---|
| `plate_health` | 3200 | **950** | 20,1 s |
| `node_health` | 2800 | **950** | 19,4 s |
| `spike_health` | 1500 | **550** | (phase 3) |
| `core_health` | 3200 | **1200** | 20,2 s (épines+noyau) |
| `heart_health` | 2600 | **2600** (inchangé) | 7,7 s |

Total ≈ **67 s**. Invariants inchangés (heart intact → invariant 4 ok ; fenêtres/télégraphes intacts) :
`validate()` passe toujours. À toucher en même temps, sinon `check.sh` casse :
- **`tests/unit/test_leviathan_tuning.gd`** : `test_phase_durations_land_in_the_intended_range`
  (bornes → phases 1-3 entre 15 et 25 s, phase 4 < 10 s) et
  `test_the_whole_fight_lands_in_the_three_to_four_minute_bracket` (total → 55–85 s ; renommer, ce
  n'est plus « 3-4 min »).
- **`docs/design/BOSS_PALE_LEVIATHAN.md`** : la section durées/occupation (« vise 65-75 / 55-65 /
  50-60 s ») et toute mention de PV par phase.
- **ADR nouveau** (`ADR-0019` ?) : ce ~70 s **contredit la spec §7 (« 3 à 4 min »)** — décision de
  playtest, un ADR prime sur la spec (cf. règle projet). Y consigner le verdict opérateur.

#### 2. Lisibilité — télégraphier la mécanique (le vrai fond du « rien ne se passe »)

En phase 1 **une seule plaque encaisse à la fois** (celle dans l'arc face au joueur, coquille qui
tourne sur 12 s) ; les autres tirs ricochent sur le corps clos. Rien à l'écran ne dit **laquelle**
viser. À faire :
- **Pastille cible active** : le module sait quelle plaque est exposée (`plate.is_exposed(...)`).
  Le faire remonter (signal `piece_active_changed(index)` ou lecture par le niveau) et, côté HUD,
  **surligner la pastille active / atténuer les autres** (nouvelle méthode `set_boss_limb_active`).
- **Télégraphe dans le monde** : teinter/pulser en émissif le nœud de coque de la plaque exposée
  (`plate.node`, un `Plate_0X`) pour qu'on voie où tirer. Idem plus tard pour le nœud/l'épine
  prioritaire.
- **Levier de rythme si toujours confus** (à rejuger, pas à appliquer d'office) :
  `shell_orbit_period` 12 → 8 s et/ou `plate_arc_deg` 100 → 120 — une plaque revient plus souvent.
- **Corps clos** : le ricochet `deflected` se lit « rien ne se passe ». Envisager un retour plus
  clair « ARMURE » quand on frappe le corps fermé (basse priorité).

#### Après les deux chantiers
`check.sh` vert, puis **valider au réel** : `balance-prober` pour la chronologie par phase (durées
mesurées), puis un `/jouer` manuel. Ne pas conclure « c'est bon » sur les seuls chiffres.

---

### Ce qui est acquis

| Livrable | Où | État |
|---|---|---|
| Conception du boss (4 phases, chiffres, invariants, spec 3D, 11 prompts) | `docs/design/BOSS_PALE_LEVIATHAN.md` | ✅ |
| Décision + dimensions 11 × 14 m | `ADR-0018`, tableau d'`ADR-0008` amendé | ✅ |
| Les 11 images (3 planches, 5 textures, 3 décors/VFX) | `assets/reference/concepts/`, `assets/source/` | ✅ mesurées, regardées, provenance au CSV |
| **Coque + silhouette (BRIEF-0041)** — noyau sphérique, épines longues/inégales, croissant asymétrique | `build_pale_leviathan.py`, `pale_leviathan.glb` | ✅ mesurée, rendue, regardée (voir réserve) |
| `GravityWell`, `TargetableProjectile` | `scripts/gameplay/` | ✅ 25 tests |
| `LeviathanTuning` + 6 invariants | `resources/data/` | ✅ 20 tests |
| `LeviathanPlate`, `LeviathanSpike`, `LeviathanCombat` | `scripts/bosses/` | ✅ 42 tests |

`./scripts/check.sh` : **274 tests verts**.

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

## P0 — Rendre la démo irréprochable

- [ ] **Contenu de la phase chasseur** — une seule vague de ~10 Needle Scouts puis mini-boss.
  Ajouter 1-2 vagues et une **2ᵉ famille d'ennemis** pour 2-3 min de jeu et laisser la puissance
  monter à 5. → tâches **H5** / **H6** de `docs/TASKS_HORIZONTAL.md`.
- [ ] **Écran titre** — texte nu. Le `title_backdrop.svg` et les emblèmes de faction de la forge
  **ne sont pas utilisés**. → tâche **H3**.
- [x] **Écrans** — **pause** et **victoire / rapport** reforgés dans le langage d'interface de
  l'accueil (ADR-0012). Les cadres SVG plein écran de la forge sont abandonnés, pas intégrés.
- [ ] **Écran d'échec de mission** — il n'en existe **aucun** : perdre tous les chasseurs appelle
  `continue_run()` et la partie repart, sans écran ni choix offert au joueur. Manque de gameplay
  autant que d'interface. → ex-tâche **H4**, redéfinie par l'ADR-0012.
- [ ] **Pacing de l'appontage** — trop rapide ; ajouter des temps de pause entre l'arrivée de la
  Citadelle, l'autopilote et le transfert (`graybox_root._start_docking`).
- [ ] **Équilibrage démo** — vérifier que la difficulté est « facile mais nerveuse ».
  Outil : sous-agent `balance-prober` (rend la chronologie de l'arc).

## P1 — Systèmes de gameplay manquants (spec, valeur forte)

- [ ] **Missiles secondaires** (verrouillage doux, salves, recharge par bonus — `Missile Rack` en asset).
- [ ] **Overdrive** (jauge, boost temporaire ; devient « Citadel Burst » en forteresse).
- [ ] **Configurations de tir** : Spread / Lance / Orbit (touche E).
- [ ] **Familles d'ennemis** : Crescent Interceptor, Choir Mine, Leech Drone, Null Bomber,
  Shield Carrier, Frigate Turret. `EnemyController` est une base de composition prête à étendre.
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

- [ ] **Enrichir les coques 3D** — les meshes existent mais restent sobres. → tâche **H1**.
- [ ] **Enrichir le fond** — la nébuleuse est belle mais uniforme : aucun élément remarquable
  (planète, bande galactique, débris qui dérivent). → tâche **H2**.
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
- [ ] **Fuite à la sortie** : 8 ObjectDB leaked / 4 resources still in use (tweens/timers non libérés).

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
