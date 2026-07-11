# Notes de revue — production forge (audit 2026-07-11)

Suivi des points relevés à la revue du concepteur sur la première grande passe `asset-forge`.
La production est globalement solide (prompts IP-propres, provenance sans trou réel, script
audio déterministe et sans téléchargement, SVG propres et conformes). Points de suivi :

## IP — traité
- 7 planches `reference_*.png` contaminées (marques visibles) → **quarantinées** hors dépôt
  (voir `docs/decisions/ADR-0005`). Les 8 planches de concept originales sont conservées.

## À corriger avant modélisation 3D (briefs futurs)
- **Aegis Citadel** : la vue de face lit légèrement comme un buste torse+épaules (noyau = tête,
  bras-batteries = épaules). Abaisser/écarter les bras pour casser cette lecture humanoïde
  (charte §4, §15.4). Déjà noté dans la provenance de la planche.
- **Pale Leviathan** : le noyau magenta est presque centré alors que le canon exige un noyau
  **décentré** (silhouette asymétrique, §15.5). Décentrer réellement à la modélisation.

## À arbitrer en Phase 1 (test capture)
- **VFX explosions** : `small/medium/heavy_explosion`, `debris_burst`, `sparks` emploient un
  orange chaud `#FF8A32`. `graybox_palette.md` (§limites) recommande des explosions
  **froides/désaturées** pour préserver la saillance du corail `#FF5A3D` du danger ennemi.
  À vérifier à l'écran (glow + tone mapping) avant de figer.

## Livrable manquant
- **BRIEF-0019 (frégates & batteries externes)** : le prompt de génération est produit
  (`docs/forge/output/frigates_and_batteries_generation_prompt.md`) mais la planche raster
  `assets/source/concepts/frigates_and_batteries_concept_sheet.png` **n'a jamais été générée**.
  Statut : *prompt livré, image à produire*. À régénérer via l'outil imagegen puis provenancer.

## Cosmétique
- `sparks.svg` : description CSV « froides et or » alors que l'asset contient de l'orange —
  harmoniser la description ou retirer l'orange.
- Écarts palette assumés (non normatifs) : `#8C5BE8` (orbit_drone, violet éclairci),
  bleus-gris de `parallax_03_planet`.
