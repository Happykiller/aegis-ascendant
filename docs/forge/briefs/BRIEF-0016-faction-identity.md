# BRIEF-0016 — Identité Helios Vanguard et Null Choir

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur intérimaire (Codex, continuité exceptionnelle)
- **Date** : 2026-07-11

## Objectif

Créer un petit système d'identité vectorielle original pour les deux factions, les assets héros
et les marquages de coque.

## Principes

- Helios Vanguard : géométrie stable, axe vertical, anneau de protection interrompu et prisme.
- Null Choir : anneau incomplet irrégulier, noyau décentré et trois relais dissonants.
- Specter-9 : trajectoire brisée autour d'un delta compact, sans chiffre.
- Aegis Citadel : prisme encadré par deux blocs-batteries, sans silhouette humanoïde.
- Aucun symbole ailé, animal, œil, crâne, couronne, étoile militaire existante ou logo texte.

## Contraintes

- SVG sans texte, metadata, filtre ni dégradé ; aplats et strokes uniquement.
- Emblèmes et patch en `viewBox="0 0 128 128"`.
- Marquages de coque en `viewBox="0 0 512 128"`.
- Lisibilité en monochrome obligatoire.
- Palette exclusivement issue de la charte.
- Ne jamais reprendre les emblèmes visibles dans `assets/reference/inspiration/reference_*.png`.

## Livrables

| Fichier | Fonction |
|---|---|
| `assets/source/identity/helios_vanguard_emblem.svg` | emblème allié |
| `assets/source/identity/null_choir_symbol.svg` | symbole ennemi |
| `assets/source/identity/specter_squadron_mark.svg` | marquage du Specter-9 |
| `assets/source/identity/aegis_citadel_mark.svg` | marque de la Citadel |
| `assets/source/identity/pilot_patch.svg` | patch pilote générique |
| `assets/source/identity/hull_marking_strips.svg` | bandes et chevrons de coque |

## Provenance

Une ligne par SVG dans `assets/licenses/ASSET_PROVENANCE.csv`, avec
`source_tool=asset-forge (Codex)`, `license=proprietary-internal` et ce brief comme
`prompt_file`.

## Critères d'acceptation

- [ ] Six SVG valides et originaux
- [ ] Deux factions distinguables en monochrome
- [ ] Aucun texte, chiffre, animal, aile, œil ou crâne
- [ ] Les marques héros dérivent du système allié sans le dupliquer
- [ ] Provenance complète

## Hors périmètre

Pas de logo texte du jeu, typographie, texture, decal Godot, scène ou intégration.
