# Tâches horizontales — prompts autoportants pour un agent externe (Codex)

> Ces tâches sont **indépendantes** et parallélisables : chacune a un périmètre de fichiers
> disjoint. Chaque prompt est **autosuffisant** — il embarque les règles du projet, car l'agent
> externe **n'a ni `CLAUDE.md`, ni `.claude/`, ni les ADR** en contexte.
>
> Mode d'emploi : copier le **CONTRAT** ci-dessous **+** le prompt de la tâche voulue.

## Matrice de conflits (ne pas lancer en parallèle si ✗)

| | H1 3D | H2 Fond | H3 Titre | H4 Écrans | H5 Ennemi | H6 Vagues |
|---|---|---|---|---|---|---|
| **H1** 3D | — | ✓ | ✓ | ✓ | ✗ *(models/)* | ✓ |
| **H2** Fond | ✓ | — | ✓ | ✓ | ✓ | ✓ |
| **H3** Titre | ✓ | ✓ | — | ✓ *(fichiers distincts)* | ✓ | ✓ |
| **H4** Écrans | ✓ | ✓ | ✓ | — | ✓ | ✓ |
| **H5** Ennemi | ✗ | ✓ | ✓ | ✓ | — | ✗ *(H6 dépend de H5)* |
| **H6** Vagues | ✓ | ✓ | ✓ | ✓ | ✗ | — |

**H6 doit passer après H5** (elle emploie la nouvelle famille d'ennemis).

---

## CONTRAT — à coller en tête de CHAQUE prompt

```
Projet : Aegis Ascendant — vertical shooter 2.5D/3D, Godot 4.7-stable (Forward+), GDScript typé.
Dépôt  : ~/sandbox/macross (git local, branche main). Dev sous WSL2 Debian, jeu testé sur Windows.

RÈGLES NON NÉGOCIABLES
1. IP : aucun nom, silhouette ou élément identifiable de Macross, Robotech ou d'une autre licence.
   Tout est original. Un asset contaminé est un échec de la tâche.
2. Godot sous WSL : TOUJOURS `--headless`. Jamais de commande Godot sans ce flag (pas de GPU).
3. Porte de qualité : `./scripts/check.sh` DOIT être vert (ALL GREEN) avant tout commit. Elle fait
   import + parse + tests. Ne jamais la contourner ni masquer une erreur.
4. GDScript TYPÉ partout. Composition > héritage. Signaux pour les événements.
5. ZÉRO allocation dans les boucles critiques (`_process`, `_physics_process`, résolution de tirs) :
   pas de `.new()`, `[]`, `{}` par frame. Le pooling est obligatoire — rien n'est instancié ni
   `queue_free()` pendant le gameplay.
6. JAMAIS d'identifiant global d'autoload dans un script (`GameState.foo()`) : ça CASSE la
   compilation en mode `--script`, donc les tests. Utiliser signaux/injection, ou
   `const XScript := preload(...)` + `@onready var _x: XScript = get_node("/root/X")`.
7. PALETTE — contrainte de lisibilité, pas de goût :
   - cyan  #3FD9E8 = RÉSERVÉ au tir allié.  N'en mettre nulle part ailleurs.
   - corail #FF5A3D = RÉSERVÉ au danger/tir ennemi.  Idem.
   - fond spatial #070A12. Ennemis sombres à accent magenta #D93D9C.
   Un décor ou un VFX qui touche à ces deux couleurs brouille la lecture du jeu.
8. ASSETS : `assets/source/` est `.gdignore`é (non importé par le moteur). Pour qu'un asset serve
   en jeu, il doit être dans `assets/imported/`. TOUT asset livré a sa ligne dans
   `assets/licenses/ASSET_PROVENANCE.csv` (format en en-tête du CSV).
9. Fichiers `snake_case.gd`, classes `PascalCase`, constantes `UPPER_SNAKE_CASE`.
   Committer les `*.uid` générés par Godot.
10. Commit conventionnel, petit, un objectif : `feat:`, `fix:`, `perf:`, `docs:`, `chore:`, `test:`.

VÉRIFIER UN RENDU VISUEL (depuis WSL, sans écran) — le jeu sait se photographier :
    rm -f /mnt/c/tmp/aegis-ascendant/capture.png        # ⚠️ sinon on lit le PNG d'avant
    ./scripts/export-win.sh debug
    ./scripts/deploy-win.sh -- ++ --novsync --goto-graybox --demo --capture --capture-after=200
    # la ligne "[ScreenCapture] saved ... — GPU X.XXX ms/frame" DOIT apparaître
    # puis ouvrir /mnt/c/tmp/aegis-ascendant/capture.png
  ⚠️ Le séparateur `++` est OBLIGATOIRE : sans lui les flags sont silencieusement ignorés.
  ⚠️ `--capture-after` compte des IMAGES, pas des secondes (le jeu tourne à >1000 FPS).
  ⚠️ Ne JAMAIS juger la perf en FPS ici (Windows bride la présentation : relevés absurdes).
     La seule métrique valable est le temps GPU par image. Budget : 16,7 ms à 60 Hz.

DEFINITION OF DONE : check.sh vert + rendu vérifié par capture + provenance à jour + commit propre.
```

---

## H1 — Enrichir les coques 3D

**Pourquoi** : les cinq coques glTF sont livrées et fonctionnelles, mais volontairement sobres.
Elles manquent de détail de surface (panneaux, tuyères, aspérités) pour tenir la comparaison avec
les planches de concept.

**Périmètre** : `tools/3d/`, `assets/source/models/`, `assets/imported/models/`,
`assets/licenses/ASSET_PROVENANCE.csv`. **Ne touche à aucun script de gameplay ni à aucune scène.**

```
Lis d'abord docs/decisions/ADR-0008-pipeline-3d-blender.md : les coques sont générées par des
scripts Blender (tools/3d/) qui exportent du glTF vers assets/imported/models/. Le pipeline est
scripté et reproductible — n'édite JAMAIS un .glb à la main, modifie le script qui le produit.

Objectif : enrichir les cinq coques (specter_9, needle_scout, aegis_citadel, choir_harvester,
pale_leviathan) sans casser leur silhouette ni leurs points d'attache.

CONTRAINTES DURES :
- Les points d'attache de tir (Muzzle_C, Muzzle_L, Muzzle_R) doivent RESTER, aux mêmes places :
  scripts/bosses/boss_controller.gd les lit par nom pour placer les tirs. Les supprimer casse le jeu.
- Les coques sont modélisées NEZ EN AVANT (les scènes les retournent au besoin). Ne change pas
  l'orientation de référence.
- Budget : le rendu coûte 0,78 ms de GPU par image aujourd'hui. Mesure APRÈS ta modification
  (le temps GPU est imprimé par la capture) et n'excède pas 1,5 ms. Si tu dépasses, réduis.
- Les ennemis restent SOMBRES avec un accent magenta #D93D9C ; le vaisseau joueur reste clair.
  N'introduis ni cyan #3FD9E8 ni corail #FF5A3D sur une coque.

Travaille par ajouts géométriques discrets : lignes de panneaux, tuyères creusées, arêtes
chanfreinées, antennes. Vérifie chaque coque par capture d'écran (voir CONTRAT) avant de conclure.
Une coque enrichie mais illisible à la taille du jeu (l'ennemi fait ~60 px à l'écran) est un échec :
juge à la taille réelle, pas en gros plan.
```

---

## H2 — Enrichir le fond spatial

**Pourquoi** : la nébuleuse procédurale est réussie mais **uniforme** — aucun élément remarquable ne
passe jamais. Le regard n'a aucun repère de progression.

**Périmètre** : `shaders/space_background.gdshader` **uniquement** (et éventuellement les uniformes
dans `scenes/vfx/space_backdrop.tscn`). **Un seul fichier de shader : aucun conflit possible.**

```
Lis d'abord docs/decisions/ADR-0006-fond-spatial-procedural.md. Décision actée : le fond est
PROCÉDURAL, en shader. Les six couches de parallaxe SVG de la forge ont été essayées et ÉCARTÉES
(aplats vectoriels, rendu inutilisable) — ne les réintègre pas.

Le shader actuel (shaders/space_background.gdshader) fait : nébuleuse en domain warping (fbm
réinjecté dans ses propres coordonnées), voiles de poussière qui soustraient de la matière, quatre
couches d'étoiles en parallaxe, occlusion des étoiles par les nuages denses, et un masque qui
assombrit le tiers central (center_calm) pour que le combat s'y lise.

Objectif : lui donner des ÉLÉMENTS REMARQUABLES, toujours en procédural :
- une bande galactique lointaine, traversant le champ en diagonale ;
- un corps céleste occasionnel (planète/lune) qui dérive lentement, très désaturé ;
- de rares débris ou astéroïdes en avant-plan, qui défilent plus vite que les étoiles.

CONTRAINTES DURES :
- Le fond doit rester FROID et DÉSATURÉ. Il ne touche JAMAIS au cyan #3FD9E8 (tir allié) ni au
  corail #FF5A3D (danger ennemi) — sinon il entre en concurrence avec la lecture du combat.
- Le tiers central reste plus calme que les bords (garde le mécanisme center_calm).
- Coût actuel du fond : 0,60 ms de GPU par image. Mesure le tien (temps GPU imprimé par la capture,
  comparer avec et sans via le flag --no-backdrop) et ne dépasse pas 1,0 ms.
- Aucune couture, aucune répétition visible : le fond défile indéfiniment.

Vérifie par capture d'écran (voir CONTRAT). Le fond doit rester DERRIÈRE l'action : s'il attire
l'œil plus que le vaisseau, c'est raté.
```

---

## H3 — Écran titre

**Pourquoi** : l'écran d'accueil est du **texte nu**. La forge a livré un `title_backdrop.svg` et six
emblèmes de faction qui **ne sont pas utilisés**.

**Périmètre** : `scenes/ui/boot_screen.tscn` + `scripts/ui/boot_screen.gd`, `assets/imported/ui/`,
provenance. **Ne touche pas aux autres écrans (H4).**

```
L'écran de démarrage (scenes/ui/boot_screen.tscn, scripts/ui/boot_screen.gd) affiche un texte nu.
Un thème de titre musical joue déjà dessus (ne casse pas ce câblage).

Assets DISPONIBLES mais NON UTILISÉS (dans assets/source/, donc non importés par le moteur —
il faut les COPIER dans assets/imported/ pour qu'ils servent, puis ajouter leur ligne de provenance) :
    assets/source/ui/screens/title_backdrop.svg
    assets/source/identity/helios_vanguard_emblem.svg     (faction alliée)
    assets/source/identity/aegis_citadel_mark.svg
    assets/source/identity/specter_squadron_mark.svg
    assets/source/identity/null_choir_symbol.svg          (faction ennemie)

⚠️ AVANT d'intégrer un SVG, RASTERISE-LE ET REGARDE-LE :
    python3 -c "import cairosvg; cairosvg.svg2png(url='<chemin>.svg', write_to='/tmp/x.png',
                output_width=512, output_height=512)"
   Un livrable de la forge n'est PAS un asset validé tant qu'il n'a pas été rendu et vu. Certains
   SVG de ce projet se sont révélés inutilisables (voir ADR-0006). Le SVG de la forge est bon pour
   l'UI et les icônes ; il est mauvais pour le pictural.

Objectif : un vrai écran titre — fond (title_backdrop), logo/wordmark « AEGIS ASCENDANT », emblème
de faction, invite « Appuyez sur ENTRÉE », et une entrée vers le menu d'options qui existe déjà.
Godot importe le SVG nativement : le copier dans assets/imported/ suffit.

Soigne la hiérarchie visuelle et la lisibilité en 1920x1080. Vérifie par capture (voir CONTRAT) :
    ./scripts/deploy-win.sh -- ++ --novsync --capture --capture-after=120
(sans --goto-graybox, pour rester sur l'écran titre).
```

---

## H4 — Écrans & cadres de HUD

**Pourquoi** : la forge a livré les cadres de **pause**, **résultats**, **échec de mission**, et les
**HUD chasseur/forteresse**. Aucun n'est intégré : le HUD est du texte brut.

**Périmètre** : `scenes/ui/` (hors `boot_screen`), `scripts/ui/`, `assets/imported/ui/hud/`.
**Ne touche pas à l'écran titre (H3).**

```
Assets DISPONIBLES mais NON UTILISÉS (dans assets/source/ = non importés ; les copier dans
assets/imported/ et ajouter leur ligne dans assets/licenses/ASSET_PROVENANCE.csv) :
    assets/source/ui/hud/fighter_hud_frame.svg      (HUD phase chasseur)
    assets/source/ui/hud/fortress_hud_frame.svg     (HUD phase forteresse)
    assets/source/ui/hud/mode_transition.svg
    assets/source/ui/screens/pause_frame.svg
    assets/source/ui/screens/results_frame.svg
    assets/source/ui/screens/victory_frame.svg
    assets/source/ui/screens/mission_failed_frame.svg
    assets/source/ui/indicators/danger_indicator.svg
    assets/source/ui/indicators/objective_marker.svg

⚠️ AVANT d'intégrer un SVG, RASTERISE-LE ET REGARDE-LE (cairosvg, cf. H3) : un livrable de la forge
n'est pas validé tant qu'il n'a pas été vu.

Objectif : habiller les écrans et le HUD avec ces cadres, sans rien casser du câblage existant
(le HUD est alimenté par des signaux : shield_changed, lives_changed, power_changed — ne change pas
ces contrats, branche-toi dessus).

CONTRAINTES DURES :
- Le HUD ne doit JAMAIS masquer la zone de jeu ni empiéter sur la lisibilité des projectiles.
- Le cyan #3FD9E8 est réservé au tir allié : dans le HUD il sert d'accent d'interface (c'est déjà
  le cas), mais reste sobre — il ne doit pas être confondu avec un projectile.
- Il existe un écran de pause ? sinon crée-le (Échap), avec reprise et retour au titre.

Vérifie chaque écran par capture (voir CONTRAT).
```

---

## H5 — Deuxième famille d'ennemis (Crescent Interceptor)

**Pourquoi** : une seule famille d'ennemis (Needle Scout) sur toute la phase chasseur. Le combat n'a
aucune variété.

**Périmètre** : `resources/enemies/`, `scenes/enemies/`, `scripts/enemies/`,
`assets/*/models/ships/`, `tools/3d/`. ⚠️ **Conflit avec H1** (les deux touchent les modèles).

```
Le jeu n'a qu'une famille d'ennemis (Needle Scout). La planche de concept
assets/source/concepts/null_choir_enemy_families_sheet.png en décrit SEPT — la deuxième est le
CRESCENT INTERCEPTOR (silhouette en croissant, noyau magenta lumineux, deux vues : dessus et 3/4).

L'architecture est PRÊTE À ÉTENDRE, ne la refais pas :
- scripts/enemies/enemy_controller.gd = base de composition (mouvement, tir, réacteur, roulis,
  flash d'impact, pooling). Elle est pilotée par une Resource typée.
- resources/data/enemy_data.gd = la Resource (max_health, move_speed, weave_*, fire_interval,
  projectile, hitbox_radius, score_value) — chaque Resource expose validate().
- resources/enemies/needle_scout.tres = l'exemple à copier.
- scenes/enemies/needle_scout.tscn = la scène (coque glTF + HealthComponent).
- Le pipeline de coques 3D est décrit dans docs/decisions/ADR-0008 (scripts Blender -> glTF).

Objectif : ajouter le Crescent Interceptor — une Resource, une scène, une coque 3D, et un
comportement DIFFÉRENT du Needle Scout (qui descend en zigzag lent). Suggestion : plus rapide,
fonce en diagonale, tire moins mais plus vite. Le comportement doit rester DATA-DRIVEN autant que
possible ; si tu dois ajouter un mode de déplacement, ajoute-le proprement à EnemyController
(composition, pas héritage) sans casser le Needle Scout.

CONTRAINTES DURES :
- Ennemi SOMBRE à accent magenta #D93D9C. Ses tirs : cœur crème #FFE9D2 + halo corail #FF5A3D.
  Ne touche NI au cyan #3FD9E8 (réservé au tir allié).
- Pooling obligatoire : le spawner préinstancie et active/désactive. Rien ne s'instancie pendant
  le gameplay. Tout état visuel (particules, modulate) doit être REMIS À ZÉRO à la réactivation,
  sinon un cadavre continue de brûler.
- Écris des tests (tests/unit/) pour toute logique pure ajoutée. check.sh doit rester vert.
- Provenance obligatoire pour la coque livrée.

Vérifie en jeu par capture (voir CONTRAT), avec --demo pour voir les ennemis en action.
```

---

## H6 — Vagues supplémentaires (⚠️ après H5)

**Pourquoi** : une seule vague de ~10 Needle Scouts, puis le mini-boss. La phase chasseur dure moins
d'une minute et la puissance de tir n'a pas le temps de monter.

**Périmètre** : `resources/encounters/`, `scripts/gameplay/wave_spawner.gd`.
⚠️ **Dépend de H5** (emploie la nouvelle famille). Peut se faire sans, avec les seuls Needle Scouts,
mais le résultat sera moins varié.

```
La phase chasseur n'a qu'UNE vague (resources/encounters/wave_graybox_01.tres, ~10 Needle Scouts),
puis le mini-boss arrive. C'est trop court : la puissance de tir du joueur (5 niveaux, montée par
les bonus Power Core) n'atteint jamais son maximum.

Le système de vagues est DATA-DRIVEN et testé (tests/unit/test_wave_schedule.gd) :
- resources/data/wave_data.gd = la Resource (entrées, positions, timings) ; elle expose validate().
- scripts/gameplay/wave_spawner.gd = le spawner (pool préalloué, émet wave_cleared).
- scripts/gameplay/graybox_root.gd enchaîne : wave_cleared -> mini-boss.

Objectif : porter la phase chasseur à 2-3 minutes avec 2-3 vagues d'intensité croissante, et laisser
la puissance monter jusqu'à 5.

CONTRAINTES DURES :
- N'AGRANDIS PAS le pool sans mesurer : le spawner préalloue (aujourd'hui 10 ennemis). Rien ne
  s'instancie pendant le gameplay.
- Difficulté cible : « facile mais nerveuse ». Le joueur ne doit pas mourir en vague 1.
- Le rythme se juge en jouant, pas en lisant : lance la démo EN TEMPS RÉEL et lis les jalons.
      timeout 300 ./scripts/deploy-win.sh -- ++ --novsync --goto-graybox --demo 2>&1 | grep "\[Level\]"
  ⚠️ N'utilise PAS --capture-after pour ça : il compte des IMAGES, pas des secondes (à >1000 FPS,
     3600 images ≈ 3 secondes de jeu — tu n'atteindrais même pas le mini-boss).
- check.sh doit rester vert (les Resources de vague sont validées par des tests).

Rends les durées mesurées par phase dans ton compte-rendu.
```

---

# Retours de jeu du 12/07/2026 (opérateur) — tâches H7 à H9

Quatre critiques formulées manette en main. Trois ont une cause **mesurée**, donnée ci-dessous :
ne pas re-diagnostiquer, corriger.

| | H7 Lumière | H8 Arène | H9 Mouvement |
|---|---|---|---|
| conflit avec | — | — | ✗ **H5** (même fichier `enemy_controller.gd`) |

---

## H7 — Les vaisseaux sont trop lumineux (le bloom mange le relief)

**Constat opérateur** : « les vaisseaux sont trop lumineux ». Les captures le confirment : le
Specter-9, la Citadelle et le Leviathan sont des **masses blanches surexposées** — on a modélisé
cinq coques en 3D et le bloom en efface le détail.

**Périmètre** : `resources/graphics/space_environment.tres`, les lumières de
`scenes/gameplay/graybox.tscn`, les matériaux des coques. **Ne touche pas au gameplay.**

```
Les coques 3D perdent tout leur relief : elles rendent comme des silhouettes blanches surexposées.

CAUSES MESURÉES (ne pas re-diagnostiquer) :
- scenes/gameplay/graybox.tscn : KeyLight light_energy = 2.8 (très élevé), RimLight = 1.3.
- resources/graphics/space_environment.tres : glow_hdr_threshold = 0.95 (très bas),
  glow_hdr_scale = 2.0, glow_bloom = 0.25, tonemap_white = 6.0.
- Les coques ont un albédo clair. Tout ce qui dépasse le seuil part en halo : le résultat est un
  aplat blanc, et le travail de modélisation est invisible.

OBJECTIF : rendre le relief des coques lisible — panneaux, arêtes, ombrage — tout en gardant une
image qui « claque ». Le bloom doit servir les ÉMISSIFS (tirs, réacteurs, noyaux ennemis), pas les
coques.

PISTES (mesure, ne devine pas) : baisser l'énergie de la lumière clé, REMONTER le seuil HDR du glow
au-dessus de la luminance des coques, assombrir légèrement l'albédo, et laisser le bloom aux seuls
matériaux émissifs.

CONTRAINTES :
- Le vaisseau JOUEUR doit rester l'ancre visuelle : toujours repérable en moins de 200 ms.
- Les ennemis restent SOMBRES à accent magenta #D93D9C.
- Les projectiles gardent leur halo (cyan allié #3FD9E8, corail ennemi #FF5A3D) : c'est la
  hiérarchie de lisibilité du jeu, n'y touche pas.
- Mesure le temps GPU avant/après (le glow coûte cher) : il est imprimé par la capture.

VÉRIFICATION OBLIGATOIRE : capture d'écran (voir CONTRAT), en phase chasseur ET en phase forteresse
(--skip-to-fortress si le flag existe, sinon laisse tourner la démo). Sans capture, la tâche n'est
pas terminée : ce défaut ne se voit QU'À L'IMAGE.
```

---

## H8 — L'arène est une boîte, et le combat final se joue à bout portant

**Constat opérateur** : « le gameplay donne l'impression d'être enfermé dans une toute petite boîte »
et « le combat de fin n'a pas de sens, on est collé l'un à l'autre ».

**Les deux sont vrais, et chiffrés.**

**Périmètre** : `scripts/gameplay/gameplay_plane.gd` (BOUNDS), la caméra de
`scenes/gameplay/graybox.tscn`, les constantes de forteresse et l'entrée du boss dans
`scripts/gameplay/graybox_root.gd` / `scenes/bosses/pale_leviathan.tscn`.
⚠️ Tâche **structurante** : la lancer seule, elle touche le cœur spatial du jeu.

```
Deux défauts d'échelle, mesurés — ne les re-diagnostique pas, corrige-les.

DÉFAUT 1 — « enfermé dans une petite boîte ». Le joueur ne peut atteindre que ~60 % de ce qu'il voit.
  - scripts/gameplay/gameplay_plane.gd : BOUNDS = Rect2(-12, -7, 24, 14) — soit 24 x 14 unités.
  - La caméra (scenes/gameplay/graybox.tscn) est à (0, 14, 5), inclinée ~70°, FOV par défaut (75°),
    en 16:9. Elle cadre environ 40 x 24 unités AU NIVEAU DU PLAN DE JEU (y = 0).
  - Donc une couronne large de ~8 unités de chaque côté est VISIBLE mais INTERDITE. Le joueur se
    cogne à un mur invisible bien avant le bord de l'écran. C'est ça, la « boîte ».
  Corrige en rapprochant la zone jouable du cadre visible : élargir BOUNDS, et/ou resserrer le FOV,
  et/ou remonter la caméra. Il doit rester une marge (les ennemis entrent hors champ), mais elle doit
  être ÉTROITE, pas de 40 %.

DÉFAUT 2 — le combat final se joue à bout portant.
  - La forteresse Aegis est à y = -5.2 (scripts/gameplay/graybox_root.gd, _FORTRESS_Y) et ne se
    déplace qu'entre x = -8 et +8 (_FORTRESS_X_LIMIT).
  - Le Pale Leviathan entre à y = +3.5 (scenes/bosses/pale_leviathan.tscn, entry_plane_position).
  - Écart vertical : 8,7 unités. Or la forteresse fait À ELLE SEULE 8 à 10 unités de haut.
    Deux vaisseaux capitaux se canardent donc à distance de contact. Aucune manœuvre possible,
    aucune échelle lisible, aucune tension.
  Corrige : éloigne les deux protagonistes, donne à la forteresse une vraie latitude de déplacement,
  et rends la distance LISIBLE (le boss doit paraître un adversaire distant, pas une figurine collée).
  Réduire l'échelle des deux meshes est une option légitime si l'arène ne peut pas grandir assez.

CONTRAINTES DURES :
- BOUNDS est le cœur du jeu : les tirs, le culling, le spawn et le clamp du joueur en dépendent.
  tests/unit/test_gameplay_plane.gd le teste — check.sh DOIT rester vert.
- Zéro allocation dans les boucles critiques ; le culling des projectiles (CULL_MARGIN dans
  scripts/projectiles/bullet_manager.gd) doit rester cohérent avec les nouvelles bornes.
- Après changement, REJOUE l'arc complet EN TEMPS RÉEL et vérifie que rien ne casse :
      timeout 300 ./scripts/deploy-win.sh -- ++ --novsync --goto-graybox --demo 2>&1 | grep "\[Level\]"
  (⚠️ n'utilise PAS --capture-after pour ça : il compte des IMAGES, pas des secondes.)
- Vérifie AUSSI par capture que le cadrage tient en phase chasseur ET en phase forteresse.
```

---

## H9 — Le mouvement des ennemis est trop linéaire (⚠️ conflit avec H5)

**Constat opérateur** : « le mouvement des ennemis est trop linéaire, on peut pas faire mieux ? »

**Périmètre** : `scripts/enemies/enemy_controller.gd`, `resources/data/enemy_data.gd`,
`resources/enemies/*.tres`, `tests/unit/`.
⚠️ **Conflit direct avec H5** (même fichier) : ne pas lancer les deux en parallèle.

```
Tous les ennemis font EXACTEMENT la même chose, et c'est tout ce qu'ils savent faire
(scripts/enemies/enemy_controller.gd, _physics_process) :

    plane_position.y -= data.move_speed * delta                      # descente constante
    plane_position.x = _base_x + sin(_age * freq * TAU) * amplitude   # zigzag sinusoïdal

Une descente à vitesse constante plus une sinusoïde. Aucun piqué, aucune courbe, aucune formation,
aucune réaction au joueur. D'où l'impression de linéarité — elle est littérale.

OBJECTIF : donner de vrais comportements, DATA-DRIVEN (pilotés par la Resource EnemyData, pas
codés en dur), pour que chaque famille et chaque vague ait sa personnalité.

PISTES (en choisir plusieurs, pas toutes) :
- des TRAJECTOIRES : entrée en arc, piqué vers la position du joueur puis dégagement, boucle,
  passage rasant sur un côté puis demi-tour ;
- des FORMATIONS : delta, ligne, colonne — les ennemis d'une vague se coordonnent au lieu de
  tomber chacun dans son couloir ;
- des PHASES : approche → attaque → retraite, plutôt qu'un défilement uniforme jusqu'au bord ;
- une PAUSE de tir télégraphiée (l'ennemi se stabilise avant de tirer : le joueur peut lire l'attaque).

ARCHITECTURE — à respecter, ne la refais pas :
- EnemyController est une base de COMPOSITION (spec §20.3) : ajoute un mode de déplacement comme un
  composant/stratégie sélectionné par la Resource, PAS par héritage ni par un `if` géant.
- resources/data/enemy_data.gd est la Resource typée qui porte les paramètres ; elle expose
  validate(). Aucun paramètre de gameplay en dur dans le contrôleur.
- Le Needle Scout existant ne doit PAS régresser (son zigzag reste une trajectoire disponible).

CONTRAINTES DURES :
- ZÉRO allocation par frame : pas de `.new()`, de tableau ni de dictionnaire créé dans
  _physics_process. Les ennemis sont POOLÉS (activate/deactivate) : tout état de trajectoire doit
  être REMIS À ZÉRO à l'activation, sinon un ennemi recyclé rejoue la fin de la trajectoire du
  précédent.
- La logique de trajectoire doit être PURE et TESTÉE (tests/unit/) : une fonction
  (temps, paramètres) -> position, instanciable à la main en headless. check.sh doit rester vert.
- Difficulté cible : « facile mais nerveuse ». Un ennemi imprévisible n'est pas un ennemi injuste :
  toute attaque doit rester LISIBLE et esquivable.

VÉRIFICATION : joue la démo en temps réel et regarde (capture avec --demo). Un mouvement se juge en
mouvement, pas sur une image fixe.
```
