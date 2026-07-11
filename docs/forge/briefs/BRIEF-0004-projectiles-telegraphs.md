# BRIEF-0004 — Projectiles et télégraphes de combat

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur intérimaire (Codex, continuité exceptionnelle)
- **Date** : 2026-07-11

## Objectif

Créer un kit SVG original de projectiles et télégraphes pour guider la vertical slice. Le kit
doit rendre alliés, ennemis et zones d'attaque identifiables par couleur, structure et forme.

## Contraintes

- SVG carré `0 0 128 128`, fond transparent, sans texte, metadata, filtre ni dégradé.
- Aplats et strokes uniquement ; poids inférieur à 4 Ko par fichier.
- Alliés : cyan `#3FD9E8`, or `#E4B54A`, blanc cassé `#EDEAE3`.
- Ennemis : cœur chaud `#FFE9D2`, halo corail `#FF5A3D`, magenta `#D93D9C`.
- Structure obligatoire des projectiles ennemis : cœur clair et enveloppe chaude distincte.
- Les télégraphes doivent rester ouverts et peu opaques une fois transposés dans Godot ; le
  SVG source emploie des contours discontinus et laisse le centre majoritairement vide.
- Création originale, sans reprise des compositions ou silhouettes des planches de référence.

## Livrables

| Fichier | Fonction |
|---|---|
| `assets/source/vfx/projectiles/allied_pulse.svg` | tir allié standard |
| `assets/source/vfx/projectiles/allied_lance.svg` | tir concentré |
| `assets/source/vfx/projectiles/allied_missile.svg` | missile secondaire |
| `assets/source/vfx/projectiles/enemy_pulse.svg` | projectile ennemi standard |
| `assets/source/vfx/projectiles/enemy_arc.svg` | projectile latéral d'intercepteur |
| `assets/source/vfx/projectiles/enemy_mine_pulse.svg` | fragment radial de mine |
| `assets/source/vfx/telegraphs/line_attack.svg` | annonce d'un tir linéaire |
| `assets/source/vfx/telegraphs/radial_attack.svg` | annonce d'une attaque radiale |

## Provenance

Une ligne par SVG dans `assets/licenses/ASSET_PROVENANCE.csv`, avec
`source_tool=asset-forge (Codex)`, `license=proprietary-internal` et ce brief comme
`prompt_file`.

## Critères d'acceptation

- [ ] Huit SVG valides, légers et sans fonctions SVG complexes
- [ ] Alliés et ennemis distinguables en monochrome par leur structure
- [ ] Cœur et halo présents sur chaque projectile ennemi
- [ ] Télégraphes linéaire et radial non confondus avec les projectiles actifs
- [ ] Provenance complète

## Hors périmètre

Pas de particules, animation, shader, scène, collision, ressource ou intégration Godot.
