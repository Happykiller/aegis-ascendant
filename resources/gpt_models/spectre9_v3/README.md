# Spectre 9 — V3 à géométrie variable

Ouvrir `spectre9_v3.blend`. La V2 reste disponible séparément.

## Commander la vitesse

La commande `CTRL | Flight configuration` est sélectionnée à l'ouverture.
Dans les propriétés personnalisées de cet objet, `speed` varie de **0 à 1**.
La timeline 1–180 montre automatiquement une accélération puis une décélération.
Pour un réglage manuel, supprimer les images clés de la propriété `speed`, puis
modifier sa valeur. Les 44 pilotes de transformation restent actifs dans le .blend.

| État | Vitesse visuelle | Ailes | Diamètre de sortie des tuyères |
|---|---|---|---|
| Basse vitesse, image 1 | 0 | Déployées ; distance entre témoins de bout d'aile 8,90 m | 1,40 m |
| Haute vitesse, image 84 | 1 | Pivotement arrière de 30° ; distance entre témoins 5,65 m | 0,79 m |
| Retour, image 168 | 0 | Déployées | 1,40 m |

Les ailes pivotent dans le plan horizontal autour de leurs emplantures, sous des
carénages fixes avec paliers visibles. Les élevons suivent chaque aile et gardent
leur propre pivot. Les canons suivent les ailes ; leurs supports compensent la rotation
pour maintenir le tir vers l'avant. Les missiles restent sur les supports fixes intérieurs.

Chaque tuyère comporte **20 pétales rigides articulés**. Ils tournent autour de leurs
charnières tangentielles, et se recouvrent progressivement lorsque la sortie se resserre.
La gorge et le cœur lumineux restent fixes.

La relation « vitesse élevée = ailes repliées et tuyères resserrées » est une règle
visuelle choisie pour ce chasseur fictif. `speed` n'est ni une mesure en km/h ni un Mach.
Aucune amélioration aérodynamique n'est calculée. Le diamètre des témoins de tuyère
décrit la géométrie nominale des pétales, hors leur épaisseur.

## Autres articulations

La démonstration V3 se déroule en configuration de vol : verrière fermée, trains rentrés.
Les autres pivots de la V2 sont conservés et réglables ; leurs anciennes images clés
ne sont pas actives dans cette démonstration. La V2 conserve son animation de déploiement.

## Export et vérification

`spectre9_v3.glb` contient les matériaux et textures intégrés ainsi que le clip animé.
Les pilotes Blender sont convertis en images clés pour cet export. Pour commander
directement la vitesse dans un moteur de jeu, il faut relier la vitesse du jeu aux
pivots ou à la progression du clip : le GLB n'exécute pas les pilotes Blender.

`verification.json` compare les transformations du .blend et du GLB réimporté à cinq
instants, contrôle la réduction d'envergure et d'ouverture des tuyères et vérifie
l'orientation des supports de canons.

Les quatre PNG montrent les deux états vus de dessus et de trois quarts arrière.
`spectre9_v3_motion.mp4` montre les mêmes mouvements sous ces deux angles (12 secondes).
Ce sont des rendus du modèle livré.

## Reconstruction

Le script utilise `../v2/spectre9_v2.blend` et `../v2/geometry.py`.
La V3 a été produite avec Blender 5.2.1 LTS, actuellement installé derrière l'alias
local `blender45`.

```sh
/home/admin/.local/bin/blender45 -b -noaudio -t 8 --python build_spectre9_v3.py
/home/admin/.local/bin/blender45 -b -noaudio --python verify_spectre9_v3.py
/home/admin/.local/bin/blender45 -b -noaudio -t 8 --python render_motion.py
ffmpeg -v error -y -framerate 5 -i motion_frames/%03d.png -c:v libx264 -crf 20 -pix_fmt yuv420p -r 30 spectre9_v3_motion.mp4
```
