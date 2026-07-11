# BRIEF-0001 — Icône applicative du jeu

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-07-11

## Objectif

Créer l'icône officielle du jeu (fenêtre Windows, exécutable, projet Godot) : un **SVG original**
évoquant l'Aegis Citadel ou le Specter-9, identité Helios Vanguard.

## Contexte

L'icône est référencée par `project.godot` (`application/config/icon="res://icon.svg"`) et sera
convertie automatiquement en ICO par l'export Windows de Godot 4.7. Elle doit être identifiable
dans une barre des tâches comme sur un grand écran titre. Voir charte §2 (canon), §3 (palette
Helios Vanguard), §4 (silhouettes), §5 (interdits).

## Contraintes

- IP : création 100 % originale ; aucun emblème/logo existant, aucune silhouette de licence.
- Palette : fond bleu profond, motif cyan/or/blanc cassé (charte §3, Helios Vanguard).
- Techniques :
  - SVG unique, viewBox carré `0 0 128 128`, sans metadata d'éditeur, sans texte ;
  - formes simples et géométriques : lisible à 16×16, spectaculaire à 256×256 ;
  - pas de dégradés complexes ni de filtres SVG (compatibilité rasterisation Godot) —
    aplats et strokes uniquement ;
  - poids < 4 Ko.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `icon.svg` (racine du projet) | icône applicative |

## Provenance

Une ligne dans `assets/licenses/ASSET_PROVENANCE.csv` : `asset_id=icon_app`,
`source_tool=asset-forge (Claude)`, `license=proprietary-internal`, `prompt_file=docs/forge/briefs/BRIEF-0001-app-icon.md`.

## Critères d'acceptation

- [ ] SVG valide (parse XML sans erreur), viewBox 0 0 128 128, < 4 Ko
- [ ] Aucun texte, aucune metadata d'éditeur, aplats/strokes seulement
- [ ] Couleurs exclusivement issues de la palette Helios Vanguard (charte §3)
- [ ] Motif original (prisme/delta/étoile de garde…), non dérivé d'une licence
- [ ] Compte-rendu : intention du motif en 2–3 phrases

## Hors périmètre

Pas d'écran titre, pas de logo texte, pas de variantes de couleur — une seule icône.
