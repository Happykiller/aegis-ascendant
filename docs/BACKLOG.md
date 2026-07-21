# Backlog & pistes d'amélioration — Aegis Ascendant

> Point de reprise au **2026-07-12** (fin de journée). Arc complet jouable (chasseur → bonus →
> mini-boss → appontage → forteresse → boss final 4 phases → victoire), **80 tests verts**,
> **0,78 ms de GPU par image** (4,7 % du budget 60 Hz).

## Comment reprendre

1. `cd ~/sandbox/macross`
2. `./scripts/check.sh` → doit être **ALL GREEN** (80 tests).
3. `./scripts/export-win.sh debug && ./scripts/deploy-win.sh` → jouer (Entrée).
4. Lire **`.claude/resources/INDEX.md`** — le *ghost* : comment vérifier un rendu, mesurer une perf,
   réviser un asset. C'est là que vit le savoir de méthode.
5. Lire `docs/architecture/` et les **ADR** (`ADR-0001` à `ADR-0008`), qui priment sur la spec.

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
- [ ] ⚠️ **Les coques lisent BEAUCOUP plus sombre en jeu qu'en rendu studio.** Constaté le
  20/07/2026 en comparant `tools/render-hull.py` (éclairage trois points) et une capture de
  `graybox.tscn` : sur le Crescent Interceptor, l'ivoire et l'anthracite disparaissent contre la
  nébuleuse, et seuls les filets magenta émissifs portent la silhouette. Vaut pour **toutes** les
  coques, pas seulement la nouvelle — c'est l'éclairage de scène, pas les meshes. ADR-0008 prévenait
  que « sans éclairage travaillé les meshes paraîtront pires que les sprites » : c'est exactement ça.
  Attention : juger une coque au seul rendu studio la flatte. Toujours confirmer par une capture en
  jeu (`--capture-at=<s>` vise le bon instant de vague).
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
