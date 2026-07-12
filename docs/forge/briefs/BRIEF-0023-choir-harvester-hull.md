# BRIEF-0023 — Coque 3D du Choir Harvester (mini-boss)

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-07-12

## Objectif

Modéliser le **Choir Harvester**, mini-boss du Chœur Nul, en `.glb` PBR, avec le kit hard-surface
partagé.

## Contexte

Le Choir Harvester est aujourd'hui un `Sprite3D` plat créé à la volée par `boss_controller.gd`. Il
occupe une bonne part de l'écran pendant son combat : c'est un objet que le joueur **regarde**, il
mérite du volume et un noyau qui pulse.

**Lire d'abord** : `docs/decisions/ADR-0008-pipeline-3d-blender.md` (conventions normatives),
`docs/forge/CHARTE_CREATIVE.md`, puis `tools/blender/lib/aegis_kit.py` (le kit existe déjà, livré
par le BRIEF-0021 : **le réutiliser, ne pas le réécrire**). Prendre `tools/blender/build_specter_9.py`
comme modèle de structure de script.

Référence de design : **`assets/source/concepts/choir_harvester_concept_sheet.png`**. Regarde-la
avec Read : elle contient la vue principale, plusieurs 3/4, et des gros plans des pétales et du bras.

Traits à respecter (la charte le résume par « trois bras, noyau central protégé ») :

- **corps discoïde blindé** vu de dessus, cerclé d'anneaux segmentés ;
- **noyau magenta central protégé par des pétales blindés en iris** (plaques anthracite qui se
  referment dessus) — c'est le point faible du boss, il doit se lire au premier coup d'œil ;
- **un grand bras articulé en faux** (segments + lame incurvée ivoire), replié au-dessus du corps ;
- **deux bras articulés plus courts** terminés par des griffes à œil magenta ;
- **un module arrière** (nacelle/propulsion) relié par un cou segmenté ;
- lignes d'énergie magenta dans les interstices de la carapace.

Le noyau et les pétales sont les éléments dont le gameplay se sert : ils doivent être des **objets
séparés et nommés** (voir points d'attache) pour qu'on puisse les animer et les cibler plus tard.

## Contraintes

- **IP** : design original ; s'en tenir à la planche.
- **Palette** : palette **antagoniste « Chœur Nul »** — anthracite `#24252B`, violet sombre
  `#452663`, ivoire froid `#DDDCD2`, magenta `#D93D9C` en émissif. Matériaux normalisés du kit.
- **Techniques** :
  - Dimensions monde : **4,55 m (X) × 7,00 m (Z)**, ±3 %. Hauteur Y ≤ 1,60 m.
  - Orientation d'auteur : **la face menaçante (noyau, bras) vers -Y**, le module arrière vers +Y,
    dessus vers +Z, dans Blender — comme toutes les unités. La rotation qui le fait descendre à
    l'écran est faite en jeu, **pas** dans le mesh.
  - Pivot à l'origine, **centré sur le noyau** (le boss dérive et tourne autour de lui).
  - Budget : **≤ 25 000 triangles**.
  - Déterministe, headless, Blender 4.5 LTS.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/build_choir_harvester.py` | script de construction, rejouable |
| `assets/imported/models/bosses/choir_harvester.glb` | le mesh exporté (LFS) |
| `docs/forge/output/BRIEF-0023-report.md` | compte-rendu : mesures réelles, limites |

## Structure et points d'attache requis

Objets nommés séparément (le gameplay s'en servira) : `Core` (le noyau émissif), `Petal_01`…
`Petal_05` (les pétales de l'iris), `Arm_Scythe`, `Arm_Claw_L`, `Arm_Claw_R`, `Pod_Rear`.

Points d'attache (Empties) : `Core_Center`, `Muzzle_L`, `Muzzle_R` (d'où partent ses tirs),
`Engine_C` (module arrière).

## Provenance

Une ligne dans `assets/licenses/ASSET_PROVENANCE.csv` (append shell) : `asset_type=model3d`,
`source_tool=asset-forge (Blender 4.5.11, script)`, `license=proprietary-internal`,
`prompt_file=docs/forge/briefs/BRIEF-0023-choir-harvester-hull.md`.

## Critères d'acceptation

- [ ] `blender45 -b -P tools/blender/build_choir_harvester.py` régénère le `.glb` sans erreur
- [ ] Bounding box 4,55 × 7,00 m (±3 %), hauteur ≤ 1,60 m — chiffres réels dans le compte-rendu
- [ ] ≤ 25 000 triangles
- [ ] Noyau magenta émissif, pétales, bras en faux et deux bras à griffes présents et **nommés**
- [ ] Pivot centré sur le noyau
- [ ] Points d'attache présents et correctement placés
- [ ] Le kit partagé est **réutilisé sans modification** (toute évolution nécessaire est signalée
      dans le compte-rendu, pas faite en douce)
- [ ] Provenance renseignée

## Hors périmètre

Ne pas toucher au code gameplay, aux `.tscn`, ni aux autres coques. Pas de textures, pas de LOD,
pas d'animation ni de rig (les pièces sont juste séparées et nommées ; l'animation viendra plus
tard, côté Godot). Pas de `.blend` versionné.
