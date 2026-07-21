# BRIEF-0022 — Coque 3D du Needle Scout

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-07-12

## Objectif

Modéliser le **Needle Scout**, l'ennemi léger de base du Chœur Nul, en `.glb` PBR, avec le kit
hard-surface partagé.

## Contexte

Le Needle Scout est aujourd'hui un `Sprite3D` plat. C'est l'ennemi le plus fréquent à l'écran :
il est souvent présent en nombre, donc **il doit rester lisible tout petit et coûter peu**.

**Lire d'abord** : `docs/decisions/ADR-0008-pipeline-3d-blender.md` (conventions normatives),
`docs/forge/CHARTE_CREATIVE.md`, puis `tools/blender/lib/aegis_kit.py` (le kit existe déjà, livré
par le BRIEF-0021 : **le réutiliser, ne pas le réécrire**). Prendre `tools/blender/build_specter_9.py`
comme modèle de structure de script.

Référence de design : **`assets/reference/concepts/null_choir_enemy_families_sheet.png`**, **première
famille** (rangée du haut) — la petite silhouette en dard effilé. Regarde-la avec Read.

Traits à respecter : dard mince et pointu, symétrique, profil très effilé, plaques de carapace
anthracite/violet sombre, **fine ligne d'énergie magenta** courant le long de l'axe central,
petites ailettes arrière. Rien de plus : c'est un ennemi de piétaille, la lisibilité prime sur le
détail.

## Contraintes

- **IP** : design original, aucun élément identifiable d'une licence existante.
- **Palette** : palette **antagoniste « Chœur Nul »** de la charte §3 — anthracite `#24252B`,
  violet sombre `#452663`, ivoire froid `#DDDCD2`, magenta `#D93D9C` en émissif. Matériaux
  normalisés du kit.
- **Techniques** :
  - Dimensions monde : **0,65 m (X) × 1,90 m (Z)**, ±3 %. Hauteur Y ≤ 0,30 m.
  - Orientation d'auteur : **nez vers -Y, dessus vers +Z** dans Blender — comme toutes les unités.
    Le fait que l'ennemi descende à l'écran est une rotation faite en jeu, **pas** dans le mesh.
  - Pivot à l'origine, centré.
  - Budget : **≤ 3 000 triangles**. C'est un budget serré et il est volontaire : cet ennemi est
    instancié en masse. Ne pas le dépasser « juste un peu ».
  - Déterministe, headless, Blender 4.5 LTS.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/build_needle_scout.py` | script de construction, rejouable |
| `assets/imported/models/ships/needle_scout.glb` | le mesh exporté (LFS) |
| `docs/forge/output/BRIEF-0022-report.md` | compte-rendu : mesures réelles, limites |

## Points d'attache requis

`Muzzle_C` (bouche de tir unique, à la pointe), `Engine_C` (tuyère arrière, départ de traînée).

## Provenance

Une ligne dans `assets/licenses/ASSET_PROVENANCE.csv` (append shell) : `asset_type=model3d`,
`source_tool=asset-forge (Blender 4.5.11, script)`, `license=proprietary-internal`,
`prompt_file=docs/forge/briefs/BRIEF-0022-needle-scout-hull.md`.

## Critères d'acceptation

- [ ] `blender45 -b -P tools/blender/build_needle_scout.py` régénère le `.glb` sans erreur
- [ ] Bounding box 0,65 × 1,90 m (±3 %), hauteur ≤ 0,30 m — chiffres réels dans le compte-rendu
- [ ] ≤ 3 000 triangles
- [ ] Palette Chœur Nul, ligne d'énergie magenta émissive présente
- [ ] Points d'attache `Muzzle_C` et `Engine_C` correctement placés
- [ ] Le kit partagé est **réutilisé sans modification** (si une évolution du kit est vraiment
      nécessaire, la signaler dans le compte-rendu au lieu de la faire en douce)
- [ ] Provenance renseignée

## Hors périmètre

Ne pas toucher au code gameplay, aux `.tscn`, ni aux autres coques. Pas de textures, pas de LOD,
pas d'animation, pas de `.blend` versionné.
