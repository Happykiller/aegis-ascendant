# assets/source/ — ce qui **fabrique** du runtime

Étape source : `.gdignore`é, jamais importée par Godot. Un fichier n'a sa place ici que s'il répond
à *quel outil le lit, et quel fichier de `assets/imported/` en sort ?*

Deux états, et le second est le plus utile à connaître :

- 🟢 **alimente le jeu** — un fichier de `imported/` en dérive aujourd'hui ;
- 💤 **dort** — livrable de forge valide, avec sa provenance, que **rien n'utilise**. Ce n'est ni un
  déchet ni un oubli : c'est un candidat, et la colonne *pourquoi* dit ce qui l'attend ou ce qui l'a
  écarté. Ne pas les intégrer par réflexe parce qu'ils existent — plusieurs ont été explicitement
  abandonnés par un ADR.

## 🟢 Ce qui alimente le jeu

| Source | Outil | Produit |
|---|---|---|
| `audio/sfx/*.wav` (20) | `tools/audio/build_audio.py` | `imported/audio/sfx/*.wav` (QOA) |
| `audio/music/*.wav` (gitignoré, ~50 Mo) | `tools/audio/build_audio.py` | `imported/audio/music/*.ogg` (ADR-0007) |
| `backgrounds/raster/planet_hero.png` | `tools/bg-key-alpha.py` | `imported/backgrounds/planet_hero.png` |
| `backgrounds/raster/nebula_monument_a.png` | `tools/bg-key-alpha.py` | `imported/backgrounds/nebula_a.png` |
| `backgrounds/raster/nebula_monument_b.png` | `tools/bg-key-alpha.py` | `imported/backgrounds/nebula_b.png` |
| `backgrounds/raster/galaxy_distant.png` | `tools/bg-key-alpha.py` | `imported/backgrounds/galaxy_distant.png` |
| `textures/hull/texture_hull_panels_seamless_2048.png` | fusion en carte de multiplication | `imported/textures/hull/hull_detail_mul.png` (ADR-0011) |
| `textures/hull/texture_greeble_mechanical_seamless_2048.png` | idem | idem |
| `textures/hull/texture_surface_wear_grime_seamless_2048.png` | idem | idem |
| `textures/citadel/citadel_panels_height.png` | `tools/derive-maps.py` | `imported/textures/citadel/citadel_panels_{nrm,rough,ao,mul}.png` |
| `textures/citadel/citadel_greebles_height.png` | `tools/derive-maps.py --strength 9 --fix-tiling 90` | `imported/textures/citadel/citadel_greebles_{nrm,rough,ao}.png` |
| `textures/citadel/crystal_facets_height.png` | `tools/derive-maps.py --strength 4 --mul-floor 0.7 --fix-tiling 90` | `imported/textures/citadel/crystal_facets_{nrm,rough,ao,mul}.png` |
| `identity/helios_vanguard_emblem.svg` | copie runtime | `imported/ui/helios_vanguard_emblem.svg` |
| `pickups/power_core.svg` | copie runtime | `imported/sprites/pickups/power_core.svg` |
| `pickups/shield_cell.svg` | copie runtime | `imported/sprites/pickups/shield_cell.svg` |
| `pickups/score_prism.svg` | copie runtime | `imported/sprites/pickups/score_prism.svg` |

> Les **coques 3D** n'ont pas de fichier source ici : elles sont **générées par script** —
> `tools/blender/build_*.py` écrit directement dans `imported/models/`. Leur « source » est le code
> Python, versionné dans `tools/`, et leur référence de design est une planche de
> `assets/reference/concepts/` (ADR-0008, ADR-0011).

## 💤 Ce qui dort

| Source | Pourquoi |
|---|---|
| `textures/citadel/citadel_wear_mask.png` | **en attente** : l'encrassement doit être fondu dans la carte de multiplication du blindage — `StandardMaterial3D` n'empile pas deux albedo |
| `textures/citadel/citadel_deck_markings_mask.png` | **en attente** : le poser sur le seul pont demande un contrôle **par face** que la projection en boîte ne donne pas ; l'appliquer à un matériau entier peindrait des hachures sur toute la coque |
| `ui/screens/pause_frame.svg` | **écarté — ADR-0012** : la pause est bâtie en langage d'interface |
| `ui/screens/victory_frame.svg` | **écarté — ADR-0012** : idem pour le rapport de mission |
| `ui/screens/main_menu_frame.svg` | **écarté — ADR-0012** : l'accueil est un diorama 3D + Control |
| `ui/screens/title_backdrop.svg` | **écarté** : remplacé par le diorama 3D de l'accueil |
| `ui/screens/results_frame.svg` | jamais utilisé — le rapport de mission porte déjà score et rang |
| `ui/screens/mission_failed_frame.svg` | **en attente** : il n'existe aucun écran d'échec (voir backlog) |
| `ui/hud/fighter_hud_frame.svg` | **écarté** : le HUD est construit en code (`scripts/ui/fighter_hud.gd`) |
| `ui/hud/fortress_hud_frame.svg` | **écarté** : idem |
| `ui/hud/mode_transition.svg` | **écarté** : idem |
| `ui/indicators/danger_indicator.svg` | en attente : pas d'indicateur hors-écran implémenté |
| `ui/indicators/objective_marker.svg` | en attente : pas d'objectifs formels (backlog P1) |
| `ui/systems/{helios_lance,missiles,rail_battery,shield}.svg` | en attente : icônes de systèmes, HUD sans emplacement pour elles |
| `vfx/combat/*.svg` (8) | **écarté — ADR-0006** : aplats vectoriels inutilisables face au bloom |
| `vfx/projectiles/*.svg` (6) | **écarté — ADR-0006** : idem |
| `vfx/telegraphs/*.svg` (2) | **écarté — ADR-0006** : idem |
| `backgrounds/parallax/parallax_*.svg` (6) | **écarté — ADR-0006** : le fond est procédural |
| `pickups/{missile_rack,orbit_drone,overdrive_shard,rescue_beacon}.svg` | en attente : ces bonus ne sont pas implémentés (backlog P1) |
| `identity/{aegis_citadel_mark,hull_marking_strips,null_choir_symbol,pilot_patch,specter_squadron_mark}.svg` | en attente : un seul emblème a trouvé son emploi |

> Le SVG reste bon pour l'**UI et les icônes**, mauvais pour le **pictural** — c'est le partage tracé
> par l'ADR-0006, et il explique à lui seul la majorité de cette colonne.

Pour regarder un de ces fichiers sans l'intégrer : `python3 tools/preview-svg.py <chemin…>`
(planche contact ; ne jamais juger un asset sans l'avoir rendu — ADR-0006).
