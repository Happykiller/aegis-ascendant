# BRIEF-0003 — Icônes des pickups de la vertical slice

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur intérimaire (Codex, continuité exceptionnelle)
- **Date** : 2026-07-11

## Objectif

Créer les sept icônes canoniques de pickups sous forme de SVG originaux, lisibles pendant le
gameplay et directement utilisables pour les prototypes UI et sprites.

## Contexte

La charte impose une identification redondante par couleur et silhouette. Les planches de
`assets/reference/concepts/` servent uniquement à inventorier les fonctions : aucune silhouette,
composition, lueur ou marque ne doit être copiée.

## Contraintes

- SVG carré `0 0 128 128`, transparent, sans texte, metadata, filtre ni dégradé.
- Aplats et strokes uniquement ; lisible à 24 px ; poids cible inférieur à 4 Ko par fichier.
- Silhouettes normatives : losange, hexagone, triple chevron, anneau, éclat, prisme, étoile.
- Chaque icône possède un cœur clair et un contour sombre `#070A12` pour rester lisible.
- Couleurs principales : or `#E4B54A`, cyan `#3FD9E8`, orange `#FF8A32`, violet `#8C5BE8`,
  magenta `#D93D9C`, vert `#7C9E52`, blanc `#EDEAE3`.
- Accents autorisés : blanc `#EDEAE3`, bleu profond `#1C2B5E`, anthracite `#24252B`.
- Création originale, sans logo, nom ou silhouette identifiable d'une licence existante.

## Livrables

| Fichier | Forme |
|---|---|
| `assets/source/pickups/power_core.svg` | losange |
| `assets/source/pickups/shield_cell.svg` | hexagone |
| `assets/source/pickups/missile_rack.svg` | triple chevron |
| `assets/source/pickups/orbit_drone.svg` | anneau |
| `assets/source/pickups/overdrive_shard.svg` | éclat |
| `assets/source/pickups/score_prism.svg` | prisme |
| `assets/source/pickups/rescue_beacon.svg` | étoile |

## Provenance

Une ligne par SVG dans `assets/licenses/ASSET_PROVENANCE.csv`, avec
`source_tool=asset-forge (Codex)`, `license=proprietary-internal` et ce brief comme
`prompt_file`.

## Critères d'acceptation

- [ ] Sept SVG valides avec `viewBox="0 0 128 128"`
- [ ] Formes distinctes même en monochrome
- [ ] Palette conforme et contraste structurel sur fond clair ou sombre
- [ ] Aucun texte, filtre, dégradé ou metadata d'éditeur
- [ ] Provenance complète

## Hors périmètre

Pas d'animation, halo Godot, son, modèle 3D, script, scène ou ressource gameplay.
