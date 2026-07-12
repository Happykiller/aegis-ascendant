# BRIEF-0025 — Coque 3D de l'Aegis Citadel (forteresse alliée)

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-07-12

## Objectif

Modéliser l'**Aegis Citadel**, la forteresse mobile alliée qui donne son nom au jeu, en `.glb` PBR,
avec le kit hard-surface partagé.

## Contexte

La citadelle est aujourd'hui un `Sprite3D` plat créé à la volée par `aegis_citadel.gd`. C'est
l'objet que le joueur défend et le repère visuel permanent de la faction Vanguard : la charte exige
qu'elle soit « lisible à très grande distance ».

**Lire d'abord** : `docs/decisions/ADR-0008-pipeline-3d-blender.md` (conventions normatives),
`docs/forge/CHARTE_CREATIVE.md`, puis `tools/blender/lib/aegis_kit.py` (le kit existe déjà, livré
par le BRIEF-0021 : **le réutiliser, ne pas le réécrire**). Prendre `tools/blender/build_specter_9.py`
comme modèle de structure de script.

Référence de design : **`assets/source/concepts/aegis_citadel_concept_sheet.png`**. Regarde-la avec
Read : la grande vue de dessus est la vue de travail ; il y a aussi face, profil, 3/4, et des gros
plans des tourelles et des canons.

Traits à respecter (la charte : « prisme axial, deux bras-batteries, noyau énergétique ») :

- **corps central en prisme allongé**, blanc cassé à panneaux bleu profond, liserés or ;
- **noyau cristallin cyan** en prisme hexagonal facetté, encastré sur le dessus du corps central —
  c'est la signature de la silhouette, il doit être gros et très émissif ;
- **deux bras-batteries latéraux** massifs, séparés du corps par des entretoises, chacun portant de
  **longs canons multi-tubes** pointés vers l'avant ;
- **tourelles secondaires** à double tube réparties sur le pont supérieur ;
- **baie d'appontage** à l'arrière, avec rampe et éclairage cyan directionnel (chevrons) ;
- silhouette symétrique en X, massive, industrielle et **propre** (contraste voulu avec la
  carapace organo-mécanique du Chœur Nul).

## Contraintes

- **IP** : design original ; s'en tenir à la planche.
- **Palette** : palette **Vanguard** de la charte §3 — blanc cassé `#EDEAE3`, bleu profond
  `#1C2B5E`, cyan `#3FD9E8` (émissif), or `#E4B54A`, rouge sécurité `#C93A31` (marquages rares).
  Matériaux normalisés du kit.
- **Techniques** :
  - Dimensions monde : **19,6 m (X) × 16,6 m (Z)**, ±3 %. Hauteur Y ≤ 5,0 m.
  - Orientation d'auteur, dans Blender : **canons vers -Y** (ils tirent vers le haut de l'écran),
    **baie d'appontage vers +Y** (côté joueur), dessus vers +Z.
  - Pivot à l'origine, centré sur le corps central au niveau du plan de jeu.
  - Budget : **≤ 30 000 triangles**.
  - Déterministe, headless, Blender 4.5 LTS.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/build_aegis_citadel.py` | script de construction, rejouable |
| `assets/imported/models/structures/aegis_citadel.glb` | le mesh exporté (LFS) |
| `docs/forge/output/BRIEF-0025-report.md` | compte-rendu : mesures réelles, limites |

## Structure et points d'attache requis

Objets nommés séparément : `Core_Prism` (le noyau cristallin), `Battery_L`, `Battery_R` (les deux
bras), `Turret_01`… (les tourelles secondaires), `Dock_Bay`.

Points d'attache (Empties) : `Core_Center`, `Muzzle_Battery_L`, `Muzzle_Battery_R` (bouche des
canons principaux), `Dock_Entry` (point d'apparition/retour du joueur à la baie).

## Provenance

Une ligne dans `assets/licenses/ASSET_PROVENANCE.csv` (append shell) : `asset_type=model3d`,
`source_tool=asset-forge (Blender 4.5.11, script)`, `license=proprietary-internal`,
`prompt_file=docs/forge/briefs/BRIEF-0025-aegis-citadel-hull.md`.

## Critères d'acceptation

- [ ] `blender45 -b -P tools/blender/build_aegis_citadel.py` régénère le `.glb` sans erreur
- [ ] Bounding box 19,6 × 16,6 m (±3 %), hauteur ≤ 5,0 m — chiffres réels dans le compte-rendu
- [ ] ≤ 30 000 triangles
- [ ] Noyau prismatique cyan très émissif, deux bras-batteries à canons longs, tourelles, baie
      d'appontage — pièces **nommées**
- [ ] Silhouette lisible en tout petit (le vérifier : rendre la silhouette et la regarder réduite)
- [ ] Points d'attache présents et correctement placés
- [ ] Le kit partagé est **réutilisé sans modification** (toute évolution nécessaire est signalée
      dans le compte-rendu, pas faite en douce)
- [ ] Provenance renseignée

## Hors périmètre

Ne pas toucher au code gameplay, aux `.tscn`, ni aux autres coques. Pas de textures, pas de LOD,
pas d'animation ni de rig. Pas de `.blend` versionné.
