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

## ⏸ Reprise en cours — Pale Leviathan (session du 2026-07-23)

**HEAD au moment de la coupure : `c11f1df`, poussé sur `origin/main`.** Tout ce qui suit est
commité et poussé sauf mention contraire.

### Ce qui est acquis

| Livrable | Où | État |
|---|---|---|
| Conception du boss (4 phases, chiffres, invariants, spec 3D, 11 prompts) | `docs/design/BOSS_PALE_LEVIATHAN.md` | ✅ |
| Décision + dimensions 11 × 14 m | `ADR-0018`, tableau d'`ADR-0008` amendé | ✅ |
| Les 11 images (3 planches, 5 textures, 3 décors/VFX) | `assets/reference/concepts/`, `assets/source/` | ✅ mesurées, regardées, provenance au CSV |
| Coque animable et texturable (30 pièces, UV, tangentes) | `build_pale_leviathan.py`, `pale_leviathan.glb` | ✅ techniquement — **silhouette à corriger** |
| `GravityWell`, `TargetableProjectile` | `scripts/gameplay/` | ✅ 25 tests |
| `LeviathanTuning` + 6 invariants | `resources/data/` | ✅ 20 tests |
| `LeviathanPlate`, `LeviathanSpike`, `LeviathanCombat` | `scripts/bosses/` | ✅ 42 tests |

`./scripts/check.sh` : **274 tests verts**.

### ⚠️ BRIEF-0041 interrompu en cours de route — état exact

L'agent `asset-forge` a été **arrêté à la main** pendant la reforge de silhouette. Son dernier mot :
« maintenant les plaques et les épines » — le rééquilibrage des matériaux était donc fait, la forme
des plaques et des épines ne l'était pas.

**Ce qui est commité** : `tools/blender/build_pale_leviathan.py` en l'état (~+528/−213 lignes,
syntaxe valide, **jamais exécuté jusqu'au bout**) et `tools/blender/inspect_glb.py`, l'outil
d'inspection que l'agent s'est écrit.

**Ce qui n'est PAS commité, et pourquoi** : le `.glb` régénéré a été **restauré à la version
BRIEF-0040**. La coque produite par le script en cours mesurait **9,481 m de large pour un contrat à
11,0 ±3 %** — hors tolérance de 14 %. La longueur (13,997 m) passait, portée par le `Body` ; la
largeur, portée par les épines, manquait, ce qui est cohérent avec « les épines restaient à faire ».
Ce `.glb` venait donc d'un export **dont l'auto-validation a échoué** : `ak.export_hull()` écrit le
fichier *puis* le relit, si bien qu'un échec laisse un fichier non conforme sur le disque.

Un artefact généré non conforme n'a rien à faire dans le dépôt : il est reproductible depuis le
script, et le garder priverait le jeu d'une coque valide pour rien.

**Le bon côté — le rééquilibrage de matière est acquis et mesuré** sur ce `.glb` intermédiaire :

| Matériau | Avant (BRIEF-0040) | Après (WIP) | Cible BRIEF-0041 |
|---|---|---|---|
| `AA_Emissive_Engine` | 28,7 % | **7,8 %** | ≤ 8 % ✅ |
| `AA_Hull` | 11,0 % | **35,2 %** | ≥ 30 % ✅ |
| `AA_Greeble` | 32,5 % | **17,9 %** | ≤ 20 % ✅ |

Contrat de noms intact (30 maillages), `TANGENT` et `TEXCOORD_0` présents, 27 710 triangles.
⚠️ **Rien de tout cela n'a été regardé** (ADR-0006) : aucun rendu n'a été produit.

**Reprise** : relancer `asset-forge` sur `BRIEF-0041`. Il repart du script commité, qui porte déjà
le plus gros du travail — lui dire que **seules la forme des plaques et des épines** restent, et que
la largeur de 11,0 m dépend de l'envergure des épines.

### Comment vérifier la coque quand elle revient

Ne pas prendre le compte-rendu de la forge pour argent comptant — c'est ce qui a fait passer la
première version. Les quatre contrôles qui ont servi au BRIEF-0040 :

1. **Contrat de noms** — relire le JSON du `.glb` (30 maillages, parents exacts), pas le rapport.
2. **Répartition des matériaux** — la mesure qui objective « ça ne ressemble pas ». Cibles de
   BRIEF-0041 : `AA_Emissive_Engine` ≤ 8 %, `AA_Hull` ≥ 30 %, `AA_Greeble` ≤ 20 %.
   *(Relevé avant correctif : 28,7 / 11,0 / 32,5.)*
3. **Déterminisme** — `./scripts/build-hull.sh --check`.
4. **Regarder** la planche 4 vues **à côté de** `assets/reference/concepts/pale_leviathan_parts_sheet.png`
   (ADR-0006). Les quatre écarts nommés au brief : symétrie radiale, noyau plat, épines courtes,
   croissant qui ne lit pas comme incomplet.

La méthode est capitalisée dans `.claude/resources/pratique-revue-asset.md`.

### Ce qui reste, dans l'ordre

1. Récolter/relancer `BRIEF-0041` (ci-dessus).
2. **Câbler la scène** : `pale_leviathan.tscn` monte `LeviathanCombat` (`external_attacks = true`,
   un `.tres` de `LeviathanTuning` pour les valeurs qui divergent des défauts).
3. **Relayer dans `graybox_root.gd`** : `pull_changed` → vélocité du joueur, `piece_gauge_changed` et
   `structure_changed` → HUD, `piece_destroyed` → VFX/SFX, bannières par phase.
4. **Détachement visuel des épines** (3ᵉ primitive, §8.2 du document) — différée exprès : elle dépend
   des nœuds de la coque, qui bougeaient encore.
5. **Textures** : dériver dans `assets/imported/textures/leviathan/` **et** écrire
   `scripts/fx/leviathan_detail.gd` dans le même commit (`CLAUDE.md` : rien d'inutilisé dans
   `imported/`). Paramètres de dérivation consignés au §11.3 du document de conception.
6. **Décor** : vortex et landmark de l'arène (`--mode black`), câblés dans `space_backdrop.tscn`.
7. **Brief séparé** : `build_choir_harvester.py` n'a ni `_triangulate_ngons()` ni `box_project_uv()`
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
