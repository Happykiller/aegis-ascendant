# BRIEF-0005 — VFX de combat

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur intérimaire (Codex, continuité exceptionnelle)
- **Date** : 2026-07-11

## Objectif

Créer les motifs sources des principaux effets de combat de la vertical slice : impacts,
explosions, débris, étincelles et onde de choc. Ils serviront de références de forme et de
masques pour une intégration ultérieure en particules GPU.

## Contraintes

- SVG carré `0 0 128 128`, transparent, sans texte, metadata, filtre ni dégradé.
- Aplats et strokes uniquement ; poids inférieur à 4 Ko par fichier.
- Les explosions utilisent des masses angulaires, jamais un simple cercle lumineux.
- Trois tailles d'explosion immédiatement reconnaissables par leur complexité croissante.
- Les fumées et structures principales sont froides ou désaturées afin de ne pas confondre les
  explosions avec le halo corail des projectiles ennemis.
- Palette : fond structurel `#070A12`, anthracite `#24252B`, ivoire `#DDDCD2`, blanc froid
  `#D9E6F2`, cyan `#3FD9E8`, or `#E4B54A`, orange `#FF8A32`, corail `#FF5A3D`.
- Création originale ; les planches de concepts ne servent qu'à recenser les catégories.

## Livrables

| Fichier | Fonction |
|---|---|
| `assets/source/vfx/combat/hull_impact.svg` | impact mécanique |
| `assets/source/vfx/combat/shield_impact.svg` | impact énergétique |
| `assets/source/vfx/combat/small_explosion.svg` | destruction de drone |
| `assets/source/vfx/combat/medium_explosion.svg` | destruction d'appareil |
| `assets/source/vfx/combat/heavy_explosion.svg` | destruction de structure |
| `assets/source/vfx/combat/debris_burst.svg` | projection de fragments |
| `assets/source/vfx/combat/sparks.svg` | gerbe d'étincelles |
| `assets/source/vfx/combat/shockwave.svg` | onde de choc |

## Provenance

Une ligne par SVG dans `assets/licenses/ASSET_PROVENANCE.csv`, avec
`source_tool=asset-forge (Codex)`, `license=proprietary-internal` et ce brief comme
`prompt_file`.

## Critères d'acceptation

- [ ] Huit SVG valides, légers et sans fonctions complexes
- [ ] Impact de coque distinct de l'impact de bouclier
- [ ] Trois catégories d'explosion distinctes en silhouette et densité
- [ ] Débris, étincelles et onde de choc utilisables séparément
- [ ] Provenance complète

## Hors périmètre

Pas d'animation, particules, shader, son, éclairage, scène ou intégration Godot.
