# ADR-0016 — Les coques étaient sombres parce que le contraste pivotait à 0,5

- **Statut** : accepté
- **Date** : 2026-07-22
- **Amende** : l'entrée ⚠️ « les coques lisent BEAUCOUP plus sombre en jeu qu'en rendu studio »
  de `docs/BACKLOG.md` (20/07/2026), dont le diagnostic était **incomplet**
- **Portée** : `shaders/retro_post.gdshader`, `resources/graphics/space_environment.tres`,
  `scenes/gameplay/graybox.tscn`, `scenes/boot/boot.tscn`, `scenes/ui/codex.tscn`

## Contexte

Le 20/07, le backlog actait que « les coques lisent beaucoup plus sombre en jeu qu'en rendu
studio » et concluait : « c'est l'éclairage de scène, pas les meshes ». La conclusion était juste
mais **partielle**, et le correctif n'avait été appliqué qu'à l'écran titre. Le 22/07, l'opérateur
reformule le constat sur le jeu lui-même : « on manque de luminosité, les vaisseaux font sombre ».

Deux causes, mesurées séparément.

### Cause 1 — la troisième lumière n'existait que sur l'écran titre

`boot.tscn` monte un éclairage **trois points** (clé 1,55 / contour 0,7 / **remplissage 0,55**),
celui de `tools/render-hull.py`. `graybox.tscn` n'en avait que **deux** : le remplissage, celui-là
même qui relève les fuselages laissés dans le noir, manquait dans le seul endroit où l'on passe du
temps. L'ambiante suivait le même écart : 0,90 au titre contre 0,55 en combat.

### Cause 2 — le post-traitement rétro n'était qu'un assombrisseur

`retro_post.gdshader` applique `col = (col - 0.5) * contrast + 0.5` avec `contrast = 1.18`.

Ce pivot à 0,5 suppose une image dont les tons moyens sont autour du gris moyen. Or **toute
l'image de ce jeu vit sous 0,25** : espace profond, coques sombres, nébuleuse. Sur une telle image,
un contraste pivoté à 0,5 ne peut que **soustraire**, partout, sans exception.

Mesuré sur une image réelle du combat, en inversant le shader :

| | Sortie du rendu 3D | À l'écran | Écart |
|---|---|---|---|
| Coque du joueur | 0,226 | 0,177 | **−22 %** |
| Nébuleuse de fond | 0,083 | 0,008 | **−90 %** |

Le « contraste » retirait donc 22 % de luminance à la coque et écrasait le fond à un
quatre-vingtième de sa valeur.

## Décision

### 1. La troisième lumière est ajoutée au combat, et l'ambiante remonte

`graybox.tscn` reçoit le `FillLight` de `boot.tscn`, aux mêmes valeurs — même appareil, pas un
réglage concurrent. `space_environment.tres` passe de 0,55 à **0,80** d'ambiante.

**0,80 et non les 0,90 du titre** : le titre n'a aucune contrainte de lisibilité de gameplay. Un
écart délibéré subsiste pour que les coques ne montent pas au niveau de luminance des projectiles
ennemis — la lisibilité des tirs prime (spec Pilier B).

Gain mesuré sur la coque du joueur : **+5,7 %** seulement. C'est peu en moyenne, et c'est pourtant
à garder : une lumière de remplissage ne change pas la luminance moyenne, elle **révèle le relief**
du côté non éclairé. Une moyenne ne mesure pas ça.

### 2. Le shader reçoit un relèvement des tons moyens (`lift`)

Nouvel uniform, **appliqué avant le contraste** :

```glsl
col = pow(max(col, vec3(0.0)), vec3(1.0 / lift));
```

Un gamma, et **pas un pivot de contraste plus bas** : le pivot abaissé aurait relevé la coque en
écrasant la nébuleuse à zéro (à 0,20 de pivot, un fond à 0,008 devient négatif). Un gamma préserve
les extrémités — le noir reste noir, le blanc reste blanc — et ne relève que les tons moyens, là où
les vaisseaux vivent.

Valeur par défaut **1,0**, c'est-à-dire le comportement historique : aucun écran n'est modifié tant
qu'il ne demande rien. Réglages posés :

| Écran | `lift` | Pourquoi |
|---|---|---|
| `graybox.tscn` (combat) | 1,25 | le sujet de la remarque |
| `boot.tscn` (accueil) | 1,18 | déjà éclairci par son environnement, il lui en faut moins |
| `codex.tscn` (bestiaire) | 1,30 | un catalogue n'a aucune contrainte de gameplay : c'est l'écran où la coque doit être la plus lisible du jeu |

### 3. `glow_hdr_threshold` ne bouge pas

Il reste à 1,6. Ne pas le baisser pour « éclaircir » : il avait été **remonté** à cette valeur
(tâche H7) pour passer au-dessus de la luminance des coques, afin que le bloom serve les
**émissifs** et pas les fuselages. Le baisser ferait baver les coques et mangerait précisément le
relief qu'on vient de récupérer.

## Résultat mesuré

Luminance moyenne, mesurée sur la coque du joueur et sur une zone de fond sans HUD, à cadrage
identique :

| Étape | Coque | Fond | Contraste coque/fond |
|---|---|---|---|
| Avant | 0,168 | 0,008 | 20,4 |
| + troisième lumière et ambiante 0,80 | 0,177 (+5,7 %) | 0,009 | 19,9 |
| + `lift` 1,25 | **0,211 (+25,8 %)** | 0,022 | 9,5 |

Le contraste coque/fond tombe de 20,4 à 9,5 : le fond remonte plus que la coque, en relatif. C'est
accepté, pour deux raisons. La nébuleuse était écrasée à un quatre-vingtième de sa valeur de rendu
— on lui rend ce qui lui était pris. Et le fond conserve son `center_calm`, qui assombrit le tiers
central : la zone où le combat se lit reste la plus sombre de l'image.

Coût GPU sur Quadro T1000 (poste de dev, ×14 par rapport à la RTX 4080) : 13,5 → 12,5 ms/image,
c'est-à-dire **dans le bruit de mesure** — le `lift` est une instruction `pow` par pixel et la
lumière de remplissage n'a pas d'ombre.

## Conséquences

- Toute nouvelle scène 3D doit monter **trois** lumières, pas deux. Le remplissage n'est pas
  décoratif : sans lui, une coque sombre reste sombre quoi qu'on fasse à l'ambiante.
- ⚠️ **Ne jamais remonter `contrast` pour « donner du punch »** à cet écran. Sur une image dont les
  tons vivent sous 0,25, ce réglage n'ajoute pas de contraste : il soustrait de la lumière. Le
  levier d'exposition, c'est `lift`.
- Le constat du 20/07 est clos, mais sa moitié manquante montre le coût d'un diagnostic arrêté
  trop tôt : la piste « éclairage de scène » était bonne et n'expliquait qu'un cinquième de l'écart.
