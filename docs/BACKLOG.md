# Backlog & pistes d'amélioration — Aegis Ascendant

> Point de reprise au 2026-07-11. Le jeu a un **arc complet jouable** (chasseur → bonus →
> mini-boss → appontage → forteresse → boss final 4 phases → victoire), 39 tests verts,
> perf réelle > 1000 FPS. Ce document liste ce qui reste, par priorité, pour reprendre sereinement.

## Comment reprendre demain (checklist)
1. `cd ~/sandbox/macross`
2. `./scripts/check.sh` → doit être **ALL GREEN** (39 tests).
3. `./scripts/export-win.sh debug && ./scripts/deploy-win.sh` → jouer (Entrée).
4. Lire `docs/architecture/ARCHITECTURE_TECHNIQUE.md` et `..._FONCTIONNELLE.md`.
5. ⚠️ Perf en test autonome : toujours ajouter `--novsync` (sinon 4 FPS = session Windows inactive, pas un bug).

---

## P0 — Rendre la démo irréprochable (rapide, fort impact)

- [ ] **Musique adaptative** — le plus gros manque ressenti. La forge a produit la *structure*
  (`docs/forge/output/adaptive_music_structure.md`) mais **aucune piste**. Options : générer des
  pistes (outil musique) puis les intégrer dans `AudioManager` avec transitions par phase, ou
  au minimum une boucle d'ambiance + un thème de boss.
- [ ] **Pacing de l'appontage** — la séquence est un peu rapide ; ajouter de petits temps de
  pause (holds) entre l'arrivée de la Citadelle, l'autopilote et le transfert pour que le
  « moment » respire. *(director `_start_docking`/`_on_citadel_arrived`.)*
- [ ] **Contenu de la phase chasseur** — une seule vague de ~10 Needle Scouts puis mini-boss.
  Ajouter 1-2 vagues et une **2ᵉ famille d'ennemis** (voir P1) pour ~2-3 min de jeu et laisser
  la puissance monter à 5.
- [ ] **Équilibrage démo** — vérifier en jeu réel (écran allumé) que la difficulté est bien
  « facile mais nerveuse » : dégâts ennemis, cadence des patterns boss, temps de kill du boss final.
- [ ] **Écran titre** — utiliser le `title_backdrop.svg` de la forge en fond ; ajouter un vrai
  logo (SVG d'identité forge) au lieu du texte simple.

## P1 — Systèmes de gameplay manquants (spec, valeur forte)

- [ ] **Vulnérabilité en mode démo/attract** propre ; **missiles secondaires** (verrouillage
  doux, salves, recharge par bonus — `Missile Rack` déjà en asset).
- [ ] **Overdrive** (jauge, boost cadence/puissance/bouclier temporaire ; devient « Citadel Burst »
  en forteresse) — `Overdrive Shard` déjà en asset.
- [ ] **Configurations de tir** : Spread / Lance / Orbit (touche E) — assets projectiles prêts.
- [ ] **Familles d'ennemis** : Crescent Interceptor, Choir Mine, Leech Drone, Null Bomber,
  Shield Carrier, Frigate Turret. Le `EnemyController` est une base de composition prête à étendre.
- [ ] **EncounterDirector** formel (remplacer le pilotage en dur dans `graybox_root`) : timeline
  data-driven avec conditions, checkpoints, synchro musique/caméra, déclenchement mini-boss.
- [ ] **Objectifs de défense** (segment « Citadel Under Siege ») : batteries à protéger.
- [ ] **Scoring avancé** : multiplicateur, combos, précision, esquive proche, batteries sauvées ;
  **résumé de fin détaillé** (spec §14.3) au lieu du seul score+rang.
- [ ] **Manette** (glyphes adaptatifs) + **remapping** des touches.

## P2 — Accessibilité, options, méta (spec §13, §19)

- [ ] **Menu d'options** : Display / Graphics / Audio / Controls / Accessibility.
- [ ] **Presets graphiques** (Low/Medium/High/Ultra), option FPS/VSync exposée à l'utilisateur.
- [ ] **Accessibilité** : réduction shake, réduction flash, désactivation aberration chromatique,
  intensité bloom, contraste renforcé, volumes séparés (musique/SFX/voix), sous-titres, pause.
- [ ] **Voix radio** (commandante / opérateur / IA) — concepts personnages produits par la forge
  (`radio_characters_concept_sheet.png`), à sonoriser + sous-titrer.
- [ ] **Checkpoints** formels (avant appontage / avant boss) et **SettingsManager** persistant.

## P3 — Art & finition

- [ ] **Note de modélisation Aegis Citadel** : la silhouette « lit » légèrement comme un buste ;
  casser cette lecture si passage en 3D (voir `docs/forge/REVIEW_NOTES.md`).
- [ ] **Note Pale Leviathan** : décentrer davantage le noyau.
- [ ] **Couleur des explosions** : arbitrer orange chaud vs consigne « froid/désaturé »
  (`graybox_palette.md`) pour ne pas noyer le corail du danger ennemi.
- [ ] **BRIEF-0019 (frégates)** : prompt prêt, **planche raster à générer** puis provenancer.
- [ ] **Sprite Needle Scout** en meilleure résolution (l'actuel est trop petit → mesh gardé) ;
  intégrer d'autres assets forge non encore utilisés (HUD frames, indicateurs, backgrounds parallax,
  écrans menu/pause/échec, emblèmes de faction).
- [ ] **Projectiles** : remplacer les box/sphères par les SVG de projectiles de la forge
  (cœur + halo) pour plus de lisibilité et de style.
- [ ] **Passage 3D optionnel** (spec) : modèles glTF via Blender à partir des concepts — gros
  chantier, seulement si une limite visuelle le justifie.

## P4 — Dette technique & robustesse

- [ ] **Extraire un `FortressController`** dédié (le contrôle est aujourd'hui dans `graybox_root`).
- [ ] **Swept collision** pour projectiles rapides (spec §21.2) — nécessaire avant d'introduire
  des projectiles très véloces.
- [ ] **Nettoyage à la sortie** : les warnings « ObjectDB leaked » apparaissent sur `--quit-after`
  forcé (tweens/timers) ; libérer proprement si on veut un arrêt net (sans impact en jeu normal).
- [ ] **Couverture de test** : le bench headless ne mesure pas le rendu MultiMesh ; ajouter des
  tests d'intégration (spawn vague, mort ennemi, collecte bonus, transition de phase) via un
  harnais headless piloté.
- [ ] **Retirer/ranger les flags de debug** avant une build « release » (`--skip-*`, `--pickup-demo`,
  `--no-backdrop/glow`), ou les garder derrière une macro debug.
- [ ] **Export release** (`build-release.ps1` équivalent bash) + icône/console off + manifeste/hash.
- [ ] **Nettoyer les captures** dans `build/` (gitignoré, mais volumineux localement).

## P5 — Pipeline & production (spec §24, §30)

- [ ] **Sous-agents & hooks** (`.claude/agents/*` gameplay-architect, godot-reviewer, etc.) et
  hooks de contrôle léger après édition GDScript.
- [ ] **CI locale** : formaliser le Quality Gate (spec §28.6) et le soak test (30 min, mémoire/FPS).
- [ ] **Provenance** : maintenir `ASSET_PROVENANCE.csv` à chaque nouvel asset ; générer la planche
  frégates manquante.
- [ ] **Musique/voix** : décider de l'outil de génération et enregistrer la provenance.

---

## Notes de reprise importantes
- **Perf** : le jeu tourne à > 1000 FPS ; ne jamais re-diagnostiquer le « 4 FPS » comme un bug
  (V-Sync + session inactive). Mémoire : `aegis-vsync-throttle`.
- **Convention autoloads** : jamais d'identifiant global d'autoload dans un script (casse `--script`).
- **assets/source/** est `.gdignore`é ; pour utiliser un asset en jeu, le copier dans
  `assets/imported/` (il sera importé par Godot).
- **Quarantaine IP** : `/_ip_quarantine/` (gitignoré) contient des références contaminées à
  ne JAMAIS versionner ni utiliser (ADR-0005).
- Toute production créative/lourde passe par un **brief `docs/forge/briefs/` + sous-agent
  asset-forge** (ADR-0004), pas par la session principale.
