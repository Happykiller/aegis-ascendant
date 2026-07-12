# ADR-0008 — Pipeline 3D : coques en modèles Blender scriptés, exportées en glTF

- **Statut** : accepté
- **Date** : 2026-07-12
- **Contexte spec** : §2.5 (stratégie de rendu), §24.2 (modèles 3D), §24.3 (Blender), §24.4 (textures)

## Contexte

À ce stade, **aucun objet 3D n'existe dans le jeu**. Le chasseur, les ennemis, les deux boss et la
citadelle sont tous des `Sprite3D` : des quads plats texturés avec le PNG de leur planche de
concept, posés à plat sur le plan de jeu, et rendus **`shaded = false`** (unlit). La
`DirectionalLight3D` de la scène n'a donc littéralement aucun effet. C'est du carton découpé dans
un décor 3D.

C'est un écart direct à la spec §2.5, qui impose « chasseur, ennemis majeurs, forteresse et boss en
**modèles 3D** », les sprites étant réservés aux projectiles, impacts, halos et HUD (§24.5). Le
pipeline §24.2/§24.3 n'avait jamais été amorcé : ni Blender installé, ni `.blend`, ni `.glb`.

La caméra de jeu est inclinée d'environ 20° au-dessus du plan (quasi vue de dessus). C'est
suffisant pour que le volume, les tuyères émissives et le roulis en virage se lisent réellement —
la 3D n'est pas un luxe invisible ici.

## Décision

Toutes les coques (chasseur, ennemis, boss, structures) deviennent des **modèles 3D générés par
script Blender versionné**, exportés en glTF binaire et importés par Godot.

```
tools/blender/lib/aegis_kit.py     ← bibliothèque hard-surface partagée (la source de cohérence)
tools/blender/build_<unit>.py      ← un script par coque, déterministe et rejouable
        │  blender45 -b -P tools/blender/build_<unit>.py
        ▼
assets/imported/models/<classe>/<unit>.glb   ← LFS
        │  import Godot
        ▼
scenes/<classe>/<unit>.tscn        ← le mesh remplace le Sprite3D
```

Blender **4.5.11 LTS** est installé hors dépôt par `./scripts/bootstrap-blender.sh` (tarball
officiel, SHA256 vérifié, symlink `blender45`), et n'est **jamais** invoqué autrement qu'en
headless (`blender45 -b -P …`), conformément à l'ADR-0002.

**Le script Python EST la source de l'asset.** Aucun `.blend` n'est versionné : un `.blend` est un
binaire opaque qu'on ne peut ni relire ni diff-er, et qui n'est pas rejouable en headless. Le
couple (script, `.glb`) suffit à reconstruire et à auditer.

## Conventions normatives

Ces règles sont contraignantes : c'est ce qui permet à cinq coques produites séparément de rester
cohérentes entre elles et avec le gameplay.

### Échelle et orientation

- 1 unité Blender = **1 mètre** Godot. Export avec `export_yup=True`.
- **Orientation d'auteur** (dans Blender, Z-up) : nez vers **-Y**, dessus vers **+Z**.
- **Orientation cible** (dans Godot) : nez vers **-Z** (le haut de l'écran), dessus vers **+Y**.
- Ces deux règles ne s'enchaînent **pas** naïvement, et c'est un piège coûteux. L'exporteur glTF de
  Blender 4.5 applique `(x, y, z) → (x, z, -y)` : un nez modelé en `-Y` ressort en **`+Z`** côté
  Godot, c'est-à-dire **à reculons**. La réconciliation (une rotation de 180° autour de Z) est faite
  **une seule fois, dans `export_hull()` du kit**. Un script de coque n'a donc jamais à y penser :
  il modélise nez vers `-Y`, il obtient nez vers `-Z` en jeu.
- **Corollaire contre-intuitif** : dans le repère d'auteur, **bâbord (la gauche à l'écran) est `+X`**.
  Utiliser `attach_pair()` du kit, qui prend une distance positive et pose les signes lui-même.
- Cette orientation vaut pour **toutes** les unités, y compris les ennemis. Le fait qu'un ennemi
  descende à l'écran est une rotation du nœud en jeu, **jamais** une orientation figée dans le mesh.
- **La bounding box ne peut pas détecter une coque retournée** (elle est symétrique en Z : `min`/`max`
  sont identiques dans les deux sens). La validation d'orientation doit donc s'appuyer sur des
  témoins **asymétriques** — typiquement les points d'attache : une bouche de tir est à l'avant, une
  tuyère à l'arrière. C'est ce que fait le kit.
- **Pivot = origine = centre de la coque**, au niveau du plan de jeu. Le roulis (`bank`) du joueur
  et les rotations des boss passent par ce point : un pivot décalé se voit immédiatement.

### Dimensions monde imposées

Le mesh doit occuper exactement le volume que le sprite occupait, sinon les hitbox, les
télégraphes et la lisibilité changent silencieusement. Tolérance **±3 %** sur la bounding box.

| Unité | Largeur (X) | Longueur (Z) | Hitbox de référence |
|---|---|---|---|
| Specter-9 (joueur) | 1,75 m | 2,46 m | 0,25 |
| Needle Scout | 0,65 m | 1,90 m | 0,45 |
| Choir Harvester (boss) | 4,55 m | 7,00 m | 2,0 |
| Pale Leviathan (boss) | 7,02 m | 8,77 m | 3,6 |
| Aegis Citadel (structure) | 19,6 m | 16,6 m | — |

La hauteur (Y) est libre, mais reste **modeste** : une coque trop épaisse casse la lecture en vue
de dessus. Viser Y ≈ 15-25 % de la longueur pour les chasseurs.

### Points d'attache

Exportés comme Empties (Godot les reçoit en `Node3D` enfants), nommés strictement :
`Muzzle_L`, `Muzzle_R`, `Engine_L`, `Engine_R`, `Cockpit`, `Hardpoint_01`… Le code cesse ainsi de
coder en dur les offsets de tir et de traînée (aujourd'hui `Vector3(0, 0, -0.9)` en dur dans
`player_fighter_controller.gd`).

### Matériaux

PBR **par facteurs**, pas de texture map : `baseColor` / `metallic` / `roughness` / `emissive`
portés par le matériau glTF. Noms imposés (les scènes Godot s'y raccrochent) :

| Matériau | Couleur charte | Rôle |
|---|---|---|
| `AA_Hull` | Blanc cassé `#EDEAE3` | coque principale |
| `AA_Panel` | Bleu profond `#1C2B5E` | panneaux |
| `AA_Trim` | Or `#E4B54A` | accents, insignes |
| `AA_Greeble` | Anthracite `#24252B` | mécanique, creux |
| `AA_Glass` | sombre, transmissif | verrière |
| `AA_Emissive_Engine` | Cyan `#3FD9E8` | tuyères, lignes lumineuses |
| `AA_Marking_Red` | Rouge sécurité `#C93A31` | marquages restreints |

Pour le Chœur Nul (ennemis/boss), la palette antagoniste de la charte se substitue :
`#24252B`, `#452663`, `#DDDCD2`, magenta `#D93D9C` en émissif.

**Le détail vient de la géométrie**, pas des textures : biseaux (bevel), découpes et enfoncements
de panneaux (inset/extrude), greebles, puis assignation de matériaux par groupe de faces. C'est ce
que montrent les planches de concept (aplats + panneaux), et à 20° de caméra une texture PBR bakée
n'apporterait presque rien pour un coût de production et de LFS très supérieur. Le bake de
textures (albedo/roughness/normal) reste possible **plus tard**, par unité, si un plan rapproché
(menu, cinématique) l'exige.

### Budgets

| Classe | Triangles max |
|---|---|
| Héros (Specter-9) | 15 000 |
| Ennemi léger | 3 000 |
| Boss | 25 000 |
| Structure | 30 000 |

### Déterminisme

Aucun aléa non seedé. Rejouer un `build_<unit>.py` doit produire le même mesh. Chaque script
s'auto-vérifie en fin de course (bounding box, nombre de triangles, matériaux présents, points
d'attache présents) et échoue bruyamment plutôt que d'exporter un asset hors contrat.

## Conséquences

- L'éclairage devient **signifiant** : les coques passent en `shaded`, la key light existante prend
  effet, et il faut compléter la scène (key + rim + fill) — sans quoi les meshes paraîtront pires
  que les sprites.
- Les sprites restent la bonne réponse pour projectiles, impacts, halos, pickups et HUD (§24.5) :
  ce pipeline ne les remplace pas.
- `boss_controller.gd` et `aegis_citadel.gd`, qui fabriquent aujourd'hui leur `Sprite3D` en code
  depuis un `sprite_texture`, devront prendre une **coque `PackedScene`** à la place.
- Coût perf à surveiller sur la citadelle et les boss (les seuls objets à fort budget).

## Alternatives rejetées

- **Garder les sprites** : hors spec §2.5, et la scène 3D (caméra inclinée, lumière, particules) ne
  sert alors à rien.
- **Modéliser à la main dans l'interface Blender** : impossible dans WSL headless (ADR-0002), et
  non reproductible.
- **Générer la géométrie côté Godot (CSG / `ArrayMesh`)** : pas d'outillage hard-surface (ni bevel,
  ni booléen propre), et le résultat ne serait ni auditable ni exportable.
