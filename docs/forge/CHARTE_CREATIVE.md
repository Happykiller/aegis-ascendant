# Charte créative — Aegis Ascendant

Bible de référence pour toute production créative (agent `asset-forge` et humains).
Extraite de la spec (§3, §10, §15, §24) ; en cas de conflit, la spec prime.
Les valeurs hex marquées *(normatif)* sont obligatoires ; les autres sont des repères.

## 1. Univers et ton

Space opera **militaire rétrofuturiste**, esthétique inspirée de l'animation japonaise des
années 1980 **en général** (jamais d'une œuvre précise) : silhouettes mécaniques fortes,
lignes tendues, accents lumineux, héroïsme lisible. Pas de photoréalisme : rendu stylisé,
cohérent, spectaculaire.

## 2. Canon (noms officiels — ne pas en créer d'autres sans brief)

| Élément | Nom | Nature |
|---|---|---|
| Coalition humaine | **Helios Vanguard** | défense interplanétaire des colonies |
| Chasseur du joueur | **Specter-9** | chasseur spatial léger triangulaire |
| Porte-chasseur | **Aurora Spear** | vaisseau de lancement du joueur |
| Forteresse mobile | **Aegis Citadel** | prisme axial, deux bras-batteries, noyau énergétique |
| Ennemi | **The Null Choir** | intelligence collective biomécanique |
| Vaisseau-amiral ennemi | **The Pale Leviathan** | organo-mécanique, anneau incomplet, noyau visible |
| Mini-boss | **Choir Harvester** | trois bras, noyau central protégé |

## 3. Palettes

### Helios Vanguard (allié)
- Blanc cassé `#EDEAE3` — coques
- Bleu profond `#1C2B5E` — panneaux
- Cyan `#3FD9E8` — lignes lumineuses, moteurs, HUD
- Or `#E4B54A` — accents, insignes
- Rouge sécurité `#C93A31` — marquages restreints

### The Null Choir (ennemi)
- Anthracite `#24252B` — coques
- Violet sombre `#452663` — segments
- Ivoire froid `#DDDCD2` — carapaces
- Magenta `#D93D9C` — lumières, armes
- Vert maladif `#7C9E52` — usage très limité

### Projectiles (lisibilité avant tout — spec Pilier B)
- Alliés : cyan / bleu / or
- Ennemis : rouge corail / magenta / orange — **toujours cœur lumineux + halo contrasté**
- Les valeurs hex normatives de gameplay (émissifs, fond, contrastes) sont définies par
  `docs/forge/output/graybox_palette.md` *(normatif, livrable BRIEF-0002)*.

### Bonus (couleur + forme + icône + son distincts — jamais la couleur seule)
| Bonus | Couleur | Forme repère |
|---|---|---|
| Power Core | jaune-or | losange |
| Shield Cell | cyan | hexagone |
| Missile Rack | orange | chevron |
| Orbit Drone | violet | anneau |
| Overdrive Shard | magenta | éclat |
| Score Prism | vert | prisme |
| Rescue Beacon | blanc | étoile |

## 4. Règles de silhouettes (spec §15.3–15.5)

- **Specter-9** : triangulaire, deux propulseurs, ailes courtes, nez central, cockpit visible
  original, aucune transformation humanoïde, pièces mobiles limitées (aérofreins/armes).
- **Aegis Citadel** : lisible à très grande distance, noyau prismatique central, deux
  bras-batteries, grande baie d'appontage, surfaces segmentées, lumières d'échelle.
- **Null Choir** : sombre, segmenté, **asymétrique**, biomécanique ; fissures lumineuses.
- Test d'originalité : une silhouette doit évoquer *le genre*, jamais une œuvre identifiable.
  En cas de doute, s'éloigner davantage.

## 5. Interdits absolus (spec §0.2, §3)

> **Assoupli par ADR-0009** (projet personnel non commercial) : les références de
> `assets/source/references/` (voir leur `REFERENCE_INDEX.md`) peuvent servir d'inspiration au rendu ;
> la production reste originale (on transpose l'intention, on ne décalque pas). Voir l'ADR.

- Aucun nom/design dérivé de : Macross, SDF-1, Valkyrie, Zentradi, Robotech, ou toute licence.
- Prompts de génération : décrire fonctions, matériaux, proportions, époque graphique,
  ambiance — **jamais** de nom de licence ni d'artiste vivant.
- Aucun asset téléchargé sans licence explicite enregistrée. Aucun asset temporaire non signalé.

## 6. Formats et conventions de livraison

- Fichiers : anglais, `snake_case`. Textes in-game : anglais. Docs : français.
- Vecteurs : **SVG** propre (pas de metadata d'éditeur), viewBox carré pour icônes,
  lisible de 16 à 256 px.
- Images : PNG alpha propre, sans franges ; sources conservées dans `assets/source/`.
- 3D : glTF 2.0 (`.glb` en livraison), 1 unité = 1 m, +Z avant Godot, pivots posés, LOD si brief.
- Audio : WAV source dans `assets/source/audio/`, OGG en livraison, pas de clipping.
- **Provenance obligatoire** : une ligne par asset livré dans
  `assets/licenses/ASSET_PROVENANCE.csv` (voir en-tête du fichier).

## 7. Échelles indicatives (graybox)

- Specter-9 : ~1,2 unité de large. Needle Scout : ~0,9. Frégate : 8–12.
  Aegis Citadel : 60+. Pale Leviathan : 80+.
- Plan de jeu logique : rectangle 24 × 14 unités (X latéral, « haut écran » = -Z monde).
