# BRIEF-0024 — Coque 3D du Pale Leviathan (boss final)

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-07-12

## Objectif

Modéliser le **Pale Leviathan**, vaisseau-amiral du Chœur Nul et boss final, en `.glb` PBR, avec le
kit hard-surface partagé.

## Contexte

C'est le climax du jeu. Aujourd'hui, c'est un `Sprite3D` plat créé à la volée par
`boss_controller.gd`. C'est la coque qui a le plus à gagner à passer en 3D : elle est énorme à
l'écran, elle a quatre phases, et son noyau doit **respirer**.

**Lire d'abord** : `docs/decisions/ADR-0008-pipeline-3d-blender.md` (conventions normatives),
`docs/forge/CHARTE_CREATIVE.md`, puis `tools/blender/lib/aegis_kit.py` (le kit existe déjà, livré
par le BRIEF-0021 : **le réutiliser, ne pas le réécrire**). Prendre `tools/blender/build_specter_9.py`
comme modèle de structure de script.

Référence de design : **`assets/reference/concepts/pale_leviathan_concept_sheet.png`**. Regarde-la
avec Read : vue principale, 3/4, profil, face, gros plans du noyau (ouvert et fermé).

Traits à respecter (la charte le résume par « organo-mécanique, anneau incomplet, noyau visible ») :

- **gros noyau sphérique magenta** au centre, sillonné de craquelures lumineuses — visible, c'est
  la cible ;
- **coquille en croissant** (l'« anneau incomplet ») qui surplombe le noyau par le haut, faite de
  plaques blindées ivoire et anthracite qui se recouvrent comme des écailles ;
- **quatre longs bras-épines** effilés qui partent du corps vers l'arrière et les côtés, segmentés,
  veinés de magenta ;
- **asymétrie assumée** : la planche est asymétrique, ne pas « corriger » en mettant une symétrie
  en X. C'est ce qui rend la silhouette inquiétante.
- carapace organo-mécanique : plaques qui se chevauchent, interstices lumineux, pas de surfaces
  lisses et propres comme sur les vaisseaux Vanguard.

## Contraintes

- **IP** : design original ; s'en tenir à la planche.
- **Palette** : palette **antagoniste « Chœur Nul »** — anthracite `#24252B`, violet sombre
  `#452663`, ivoire froid `#DDDCD2`, magenta `#D93D9C` en émissif. Matériaux normalisés du kit.
- **Techniques** :
  - Dimensions monde : **7,02 m (X) × 8,77 m (Z)**, ±3 %. Hauteur Y ≤ 2,50 m.
  - Orientation d'auteur : **noyau/face menaçante vers -Y**, dessus vers +Z, dans Blender — comme
    toutes les unités. La rotation qui le fait descendre à l'écran est faite en jeu.
  - Pivot à l'origine, **centré sur le noyau**.
  - Budget : **≤ 25 000 triangles**.
  - Déterministe (attention : l'asymétrie et les écailles ne doivent pas venir d'un `random` non
    seedé — si tu utilises du bruit, seed-le explicitement).
  - Headless, Blender 4.5 LTS.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/build_pale_leviathan.py` | script de construction, rejouable |
| `assets/imported/models/bosses/pale_leviathan.glb` | le mesh exporté (LFS) |
| `docs/forge/output/BRIEF-0024-report.md` | compte-rendu : mesures réelles, limites |

## Structure et points d'attache requis

Objets nommés séparément (le gameplay et les phases s'en serviront) : `Core` (le noyau sphérique),
`Shell_Crescent` (la coquille en croissant), `Spike_01`… `Spike_04` (les quatre bras).

Points d'attache (Empties) : `Core_Center`, `Muzzle_L`, `Muzzle_R`, `Muzzle_C`.

## Provenance

Une ligne dans `assets/licenses/ASSET_PROVENANCE.csv` (append shell) : `asset_type=model3d`,
`source_tool=asset-forge (Blender 4.5.11, script)`, `license=proprietary-internal`,
`prompt_file=docs/forge/briefs/BRIEF-0024-pale-leviathan-hull.md`.

## Critères d'acceptation

- [ ] `blender45 -b -P tools/blender/build_pale_leviathan.py` régénère le `.glb` sans erreur
- [ ] Bounding box 7,02 × 8,77 m (±3 %), hauteur ≤ 2,50 m — chiffres réels dans le compte-rendu
- [ ] ≤ 25 000 triangles
- [ ] Noyau sphérique magenta émissif, coquille en croissant, quatre bras-épines, **asymétrie**
      conservée
- [ ] Pivot centré sur le noyau
- [ ] Pièces nommées et points d'attache présents
- [ ] Le kit partagé est **réutilisé sans modification** (toute évolution nécessaire est signalée
      dans le compte-rendu, pas faite en douce)
- [ ] Provenance renseignée

## Hors périmètre

Ne pas toucher au code gameplay, aux `.tscn`, ni aux autres coques. Pas de textures, pas de LOD,
pas d'animation ni de rig. Pas de `.blend` versionné.
