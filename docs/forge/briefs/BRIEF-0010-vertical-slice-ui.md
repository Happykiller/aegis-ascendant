# BRIEF-0010 — UI de la vertical slice

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur intérimaire (Codex, continuité exceptionnelle)
- **Date** : 2026-07-11

## Objectif

Créer les sources vectorielles de l'interface chasseur et forteresse, ainsi que les principaux
indicateurs et icônes système de la vertical slice.

## Direction

Interface militaire rétrofuturiste originale : lignes fines, panneaux ouverts, angles coupés,
grille discrète et hiérarchie claire. Le HUD ne doit jamais former un cadre continu autour du
plan de jeu. Les éléments dangereux restent visibles au centre et sur les bords.

## Palette

- fond translucide futur : `#070A12` ;
- panneaux : `#1C2B5E` ;
- allié actif : `#3FD9E8` ;
- accent/charge : `#E4B54A` ;
- texte futur : `#EDEAE3` ;
- danger : `#FF5A3D` ;
- état critique : `#D93D9C`.

## Contraintes

- SVG sans texte, metadata, filtre ni dégradé ; aplats et strokes uniquement.
- HUD principal en `viewBox="0 0 1920 1080"`, compatible 16:9.
- Icônes en `viewBox="0 0 128 128"`, lisibles à 24 px.
- Les emplacements de texte restent vides et seront alimentés par Godot.
- Création originale, sans interface, glyphe ou emblème de licence existante.

## Livrables

| Fichier | Fonction |
|---|---|
| `assets/source/ui/hud/fighter_hud_frame.svg` | cadre HUD chasseur |
| `assets/source/ui/hud/fortress_hud_frame.svg` | cadre HUD forteresse |
| `assets/source/ui/hud/mode_transition.svg` | motif de transition des modes |
| `assets/source/ui/indicators/danger_indicator.svg` | danger hors écran |
| `assets/source/ui/indicators/objective_marker.svg` | objectif |
| `assets/source/ui/systems/shield.svg` | bouclier |
| `assets/source/ui/systems/missiles.svg` | missiles |
| `assets/source/ui/systems/rail_battery.svg` | batterie lourde |
| `assets/source/ui/systems/helios_lance.svg` | Helios Lance |

## Provenance

Une ligne par SVG dans `assets/licenses/ASSET_PROVENANCE.csv`, avec
`source_tool=asset-forge (Codex)`, `license=proprietary-internal` et ce brief comme
`prompt_file`.

## Critères d'acceptation

- [ ] Deux HUD 16:9 distincts mais cohérents
- [ ] Zone centrale largement dégagée
- [ ] Transition compréhensible sans texte
- [ ] Indicateurs et systèmes distincts en monochrome
- [ ] SVG valides et provenance complète

## Hors périmètre

Pas de Control nodes, thème Godot, police, animation, script, scène ou logique d'interface.
