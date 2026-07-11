# BRIEF-0002 — Palette colorimétrique normative de la graybox

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-07-11

## Objectif

Définir la **palette normative de gameplay** pour la phase graybox : couleurs exactes (hex sRGB +
énergie émissive suggérée) du chasseur joueur, des ennemis, des projectiles par équipe, du fond
et des repères, garantissant la lisibilité exigée par la spec (Pilier B : tout identifiable en
moins de 200 ms).

## Contexte

La graybox n'utilise que des primitives Godot (PrismMesh, BoxMesh, SphereMesh) avec des
`StandardMaterial3D` émissifs, sur fond spatial sombre. Le concepteur appliquera ces valeurs
dans les matériaux. Cette palette deviendra la référence normative citée par la charte §3.
Voir charte §3 (palettes factions), spec §15.2 (palette), §21.4 (lisibilité projectiles),
§11.2 (projectiles dangereux très contrastés).

## Contraintes

- Base : palettes factions de la charte §3 (alliés cyan/bleu/or ; ennemis rouge corail/magenta/orange).
- Lisibilité :
  - les projectiles **ennemis** doivent être les éléments les plus saillants de l'écran
    (contraste maximal sur le fond ET sur les explosions à venir) ;
  - projectiles alliés clairement distincts des ennemis même en périphérie de vision ;
  - daltonisme : différencier aussi par la luminance, pas seulement par la teinte
    (vérifier deutéranopie au minimum, indiquer la méthode utilisée) ;
  - fond nettement plus sombre que tout élément actif.
- Format : un fichier markdown avec tableaux (élément, hex albedo, hex émissif, énergie
  suggérée 0–4, rôle, contraste vérifié), directement transposable en `StandardMaterial3D`.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `docs/forge/output/graybox_palette.md` | palette normative graybox |

## Provenance

Une ligne dans `assets/licenses/ASSET_PROVENANCE.csv` : `asset_id=graybox_palette`,
`asset_type=color-spec`, `source_tool=asset-forge (Claude)`, `license=proprietary-internal`,
`prompt_file=docs/forge/briefs/BRIEF-0002-graybox-palette.md`.

## Critères d'acceptation

- [ ] Couvre : joueur, Needle Scout, projectile allié, projectile ennemi, fond, sol/repères de
      bounds, flash d'impact, texte HUD provisoire
- [ ] Chaque entrée : hex albedo + hex émissif + énergie suggérée + justification courte
- [ ] Ratios de contraste chiffrés (WCAG relative luminance ou équivalent) projectile/fond
- [ ] Note daltonisme (méthode + verdict)
- [ ] Cohérent avec les palettes factions de la charte §3

## Hors périmètre

Pas de textures, pas de shaders, pas de post-processing, pas de couleurs de bonus (viendront
avec le brief pickups).
