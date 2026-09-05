# Long Cortège — Tourelle lourde / Citadelle

Modèle réalisé d'après la troisième colonne de la planche `tourelles.png` fournie.
Le socle circulaire à étages, les blocs de blindage sombres, les deux canons massifs
et les petites touches magenta reprennent les caractéristiques de cette variante lourde.
Les vues de la planche demandent une interprétation de certaines formes cachées.

## Fichiers

- `tourelle_lourde.blend` : modèle éditable, matériaux intégrés, caméras et animation.
- `tourelle_lourde.glb` : modèle avec ses textures et son animation, sans studio.
- `tourelle_lourde_motion.mp4` : démonstration de huit secondes, échantillonnée à 10 images/s.
- Les cinq PNG préfixés `tourelle_lourde_` : rendus de trois quarts, dessus, face,
  côté et position de recul, à partir du modèle livré.
- `verification.json` : dimensions, triangles et vérification des mouvements après réimport GLB.

## Articulations

La base est fixe. Le pivot `CTRL | Yaw 360` porte la tête tournante. Son axe Z peut
tourner librement ; la démonstration utilise une plage de -22° à +20°.
`CTRL | Elevation` incline le berceau des canons. La démonstration élève le tir de 0 à 22°.
`CTRL | L recoil` et `CTRL | R recoil` commandent séparément les deux ensembles coulissants.
Les marqueurs `MARKER | L muzzle` et `MARKER | R muzzle` suivent les bouches de canon.

Le recul est une **translation rigide de 0,56 m**, sans écraser ni raccourcir les maillages.
Les tubes, leurs chemises et leurs tiges de piston reculent dans les berceaux fixes.
Le mouvement démarre vite puis revient plus lentement. La timeline va de 1 à 240 à 30 images/s :

| Images | Mouvement |
|---|---|
| 1–55 | Repos, puis acquisition de cible |
| 66 / 77 / 90 / 101 | Tirs alternés gauche et droite |
| 135–177 | Nouvelle visée et deux salves simultanées |
| 215–240 | Retour en face et dernière salve |

Tous les mouvements sont modifiables par images clés. Le GLB contient un clip de
démonstration coordonné. Il ne comprend pas de logique de ciblage, de dégâts ou de physique.

## Matériaux et fidélité

Texture de métal sombre usé créée avec **imagegen intégré**, prompt dans `TEXTURE_PROMPT.md`.
Les cartes de rugosité et de normales sont cuites dans Blender à partir de cette image.
Ce sont des cartes artistiques, et non un scan mesuré. Elles sont intégrées au .blend et au .glb.
Les panneaux, joints, verrous, anneaux et ouvertures de bouche sont de la géométrie.

Cette livraison privilégie le détail visible et l'animation. Elle ne vise pas les budgets
LOD 2 500 / 1 000 / 400 polygones mentionnés sur la planche ; aucun LOD de jeu n'est inclus.
Le modèle détaillé compte 45 412 triangles. Ses dimensions vérifiées sont de 10,118 m
de long, 7,307 m de large et 4,166 m de haut.

## Reconstruction

Blender 5.2.1 LTS. Les fichiers sources et la texture générée sont conservés dans ce dossier.

```sh
/home/admin/.local/bin/blender45 -b -noaudio -t 8 --python build_turret.py
/home/admin/.local/bin/blender45 -b -noaudio --python verify_turret.py
/home/admin/.local/bin/blender45 -b -noaudio -t 8 --python render_motion.py
ffmpeg -v error -y -framerate 10 -i motion_frames/%03d.png -c:v libx264 -crf 20 -pix_fmt yuv420p -r 30 tourelle_lourde_motion.mp4
```

La reconstruction du .blend intègre la planche depuis `reference.png`, inclus dans ce dossier.
La texture générée existe déjà ; aucune nouvelle génération d'image n'est nécessaire.
