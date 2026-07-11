# BRIEF-0017 — Écrans et menus

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur intérimaire (Codex, continuité exceptionnelle)
- **Date** : 2026-07-11

## Objectif

Créer les compositions vectorielles des principaux écrans de la vertical slice, sans texte afin
que la localisation et l'accessibilité restent gérées dans Godot.

## Écrans

1. fond d'écran titre ;
2. cadre du menu principal ;
3. pause ;
4. échec de mission ;
5. victoire ;
6. résumé et statistiques de fin.

## Direction

UI Helios Vanguard militaire et sobre : panneaux bleu-noir, lignes cyan, accents or, angles
coupés et larges marges. L'échec emploie le corail avec parcimonie ; la victoire utilise l'or
sans flash blanc plein écran.

## Contraintes

- SVG `viewBox="0 0 1920 1080"`, sans texte, metadata, filtre ni dégradé.
- Aplats et strokes uniquement ; aucun visuel raster embarqué.
- Zones de titre, boutons et statistiques laissées vides.
- Compatibilité 16:9 de 1080p à 4K par mise à l'échelle.
- Aucun logo texte, symbole de licence ou copie des écrans de référence.

## Livrables

| Fichier | Fonction |
|---|---|
| `assets/source/ui/screens/title_backdrop.svg` | écran titre |
| `assets/source/ui/screens/main_menu_frame.svg` | menu principal |
| `assets/source/ui/screens/pause_frame.svg` | pause |
| `assets/source/ui/screens/mission_failed_frame.svg` | échec |
| `assets/source/ui/screens/victory_frame.svg` | victoire |
| `assets/source/ui/screens/results_frame.svg` | résumé de fin |

## Provenance

Une ligne par SVG dans `assets/licenses/ASSET_PROVENANCE.csv`, avec
`source_tool=asset-forge (Codex)`, `license=proprietary-internal` et ce brief comme
`prompt_file`.

## Critères d'acceptation

- [ ] Six écrans cohérents et distincts
- [ ] Zones de contenu lisibles et non décorées
- [ ] Échec et victoire différenciés autrement que par la couleur
- [ ] SVG valides, légers et sans texte
- [ ] Provenance complète

## Hors périmètre

Pas de typographie, labels, boutons Godot, animation, navigation, scène ou intégration.
