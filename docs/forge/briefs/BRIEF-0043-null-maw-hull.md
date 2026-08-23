# BRIEF-0043 — Coque 3D du Null Maw

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-08-23

## Objectif

Modéliser le **Null Maw**, quatrième silhouette d'ennemi du Chœur Nul, en `.glb` PBR, avec le kit
hard-surface partagé — **corolle articulée** qui s'ouvre en jeu, et anneau d'accrétion qui tourne.

## Contexte

Le Null Maw est l'unité qui **ne blesse pas**. Quand le joueur s'approche trop, elle s'ouvre et
génère un micro-puits d'aspiration : elle ne lui retire pas de bouclier, elle lui retire sa marge de
manœuvre, et le colle aux dangers voisins (`docs/decisions/ADR-0022-les-ennemis-peuvent-connaitre-le-joueur.md`).
Elle se referme, se réarme, et recommence : c'est une **zone interdite**, pas un obstacle qu'on
dépense.

C'est une variante de famille de la Choir Mine (BRIEF-0042, produit en parallèle), et la difficulté
du brief est là : **les deux doivent être distinguables au premier coup d'œil, à petite taille, sur
fond sombre**, alors qu'elles partagent une classe d'objet et une palette. Si le joueur les confond,
il traitera un puits comme une bombe — il tirera dessus de loin au lieu de simplement le contourner,
et la mécanique ne se lira jamais.

**Ce qui les oppose, et qui doit être visible avant toute autre chose :**

| | Choir Mine | Null Maw |
|---|---|---|
| Volume | disque **fermé**, plein, ramassé | coque **ouverte** sur un vide central |
| Ce qu'on voit au centre | un noyau solide et bombé | un **trou**, un puits sombre bordé de lumière |
| Rythme des bords | une couronne régulière de modules | des **pétales longs et inégaux**, en nombre impair |
| Silhouette en aplat noir | un cercle | une **fleur**, franchement dentelée |

**Lire d'abord** : `docs/decisions/ADR-0008-pipeline-3d-blender.md`,
`docs/decisions/ADR-0011-detail-des-coques-budgets-et-textures.md`, `docs/forge/CHARTE_CREATIVE.md`,
puis `tools/blender/lib/aegis_kit.py` — **le kit existe, le réutiliser sans le modifier**. Modèles
de structure : `tools/blender/build_needle_scout.py` et, pour les pièces articulées,
`docs/forge/briefs/BRIEF-0039-choir-harvester-pieces-animables.md`.

Référence de design : **`assets/reference/concepts/null_choir_enemy_families_sheet.png`**,
**troisième cellule** (Choir Mine) comme point de départ de FAMILLE — le Null Maw n'a pas de
vignette propre, c'est une unité neuve. Regarde la planche avec Read pour en tenir le vocabulaire
(carapace segmentée, fissures magenta rayonnant d'un cœur), puis **écarte-t'en délibérément** sur
les quatre lignes du tableau ci-dessus.

## Contraintes

- **IP** : design original, aucun élément identifiable d'une licence existante.
- **Palette** : palette antagoniste **Chœur Nul** de la charte §3. Matériaux normalisés du kit,
  `MATERIAL_ORDER` inchangé.
  - ⚠️ Le vide central n'est pas un matériau émissif : c'est **l'absence** de coque. Le magenta
    borde le puits, il ne le remplit pas. Un centre lumineux plein le ferait lire comme le noyau
    d'une mine, exactement ce qu'on cherche à éviter.
- **Techniques** :
  - Dimensions monde : **1,45 m (X) × 1,45 m (Z)**, ±3 %. Volontairement **plus large** que la
    Choir Mine (1,15) : c'est un deuxième signal de distinction, et il porte une information juste —
    le Null Maw a plus de portée et plus de points de vie.
  - ⚠️ **Hauteur : 0,35 à 0,45 m.** Plus plate que la mine, dérogation assumée à la règle de
    hauteur d'ADR-0008 pour la même raison (ce n'est pas une cellule d'avion). Valeur réelle au
    compte-rendu.
  - Orientation d'auteur : **nez vers -Y, dessus vers +Z**. La corolle s'ouvre vers **+Z** (le
    dessus), donc vers la caméra.
  - Pivot à l'origine, au centre du puits.
  - Budget : **≤ 7 000 triangles** (plafond « ennemi léger » relevé à 12 000 par ADR-0011 ; une
    corolle coûte plus qu'un disque, elle reste largement sous le plafond).
  - **Bâbord est `+X`** en repère d'auteur — utiliser `attach_pair()` pour toute paire.
  - Déterministe, headless, Blender 4.5 LTS.

### Pièces articulées — la partie neuve

| Nœud | Ce que c'est | Pivot |
|---|---|---|
| `Petal_01` … `Petal_05` | cinq pétales de la corolle, **longueurs inégales**, répartis autour du puits | à la **base** de chaque pétale, côté extérieur du puits : ils basculent vers l'extérieur en s'ouvrant, comme une fleur, pas comme un couvercle qui glisse |
| `Ring` | anneau d'accrétion, sous la corolle, autour du puits | au **centre**, sur l'axe : il ne fait que tourner sur lui-même |

**Cinq pétales, nombre impair et longueurs inégales** : c'est ce qui interdit à la silhouette de
retomber sur la symétrie régulière de la mine, et ce qui satisfait l'exigence d'asymétrie de la
charte §4 sans avoir à coller une verrue sur un objet radial.

⚠️ **Le piège documenté** (`aegis_kit.moving_part` docstring) : une pièce dont l'origine reste à
zéro décrit un arc de cercle autour du centre de l'objet au lieu de s'articuler. Poser les origines
aux points de pivot, et **vérifier au rendu, pièces déviées** — un défaut d'animation ne se voit pas
sur une pose fixe, et le contrat d'export validera sans un mot.

Donner au compte-rendu, pour chaque pétale : pivot en coordonnées Godot, **débattement mécanique
disponible** avant auto-intersection, et l'angle auquel le puits central devient franchement visible
de dessus (c'est le seuil que la session principale utilisera comme « ouvert »).

### Où mettre le détail

La caméra de jeu regarde presque **de dessus** (vue « game » de `tools/render-hull.py` à 70°). Tout
le détail et tout l'émissif vivent sur les surfaces **supérieures**. Détail en **géométrie**, jamais
en texture fine — le rendu 960×540 + scanlines l'écrase (ADR-0011, ADR-0016).

L'émissif doit dire **où est le danger** : un liseré sur la lèvre intérieure des pétales, l'anneau
d'accrétion. Rappel : **au-delà d'environ 10 % de la surface, ce n'est plus un accent, c'est une
livrée** — donner la répartition mesurée des matériaux.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/build_null_maw.py` | script de construction, rejouable |
| `assets/imported/models/ships/null_maw.glb` | le mesh exporté (LFS) |
| `docs/forge/output/BRIEF-0043-report.md` | compte-rendu : mesures réelles, débattements, limites |

## Points d'attache requis

- `Muzzle_C` — au centre du puits, sur l'axe. Le Null Maw ne tire pas, mais `EnemyController` lit ce
  point à l'initialisation de toute coque : il doit exister, et le centre est sa place juste.
- **PAS de `Engine_C`.** Elle dérive avec le décor et n'a pas de moteur ; le contrôleur ne pose une
  plume que si la coque en déclare un.

## Provenance

Une ligne dans `assets/licenses/ASSET_PROVENANCE.csv`, **ajoutée en append shell (`>>`), jamais par
réécriture du fichier** : BRIEF-0042 tourne en parallèle et une réécriture écraserait sa ligne.
`asset_type=model3d`, `source_tool=asset-forge (Blender 4.5.11, script)`,
`license=proprietary-internal`, `prompt_file=docs/forge/briefs/BRIEF-0043-null-maw-hull.md`.

## Critères d'acceptation

- [ ] `blender45 -b -P tools/blender/build_null_maw.py` régénère le `.glb` sans erreur
- [ ] Bounding box 1,45 × 1,45 m (±3 %), hauteur entre 0,35 et 0,45 m — chiffres réels au rapport
- [ ] ≤ 7 000 triangles
- [ ] Deux exécutions successives produisent un `.glb` **byte-identique**
      (`./scripts/build-hull.sh --check null_maw`)
- [ ] Palette Chœur Nul ; le centre est un **vide**, pas une surface lumineuse ; répartition des
      matériaux mesurée
- [ ] `Muzzle_C` au centre ; **aucun** `Engine_C`
- [ ] Cinq `Petal_NN` + `Ring` déclarés en pièces mobiles, pivots corrects, **débattements mesurés**
- [ ] **Rendu et regardé** :
      `blender45 -b -P tools/render-hull.py -- assets/imported/models/ships/null_maw.glb`. Un
      livrable non rendu n'est pas un livrable (ADR-0006).
- [ ] Une planche supplémentaire **corolle ouverte**, montrant que le puits se lit et que rien ne
      s'auto-intersecte
- [ ] ⚠️ **LE CRITÈRE QUI DÉCIDE** : mettre côte à côte l'**aplat noir vu de dessus** du Null Maw et
      celui de la Choir Mine (BRIEF-0042), et dire franchement si on les distingue à petite taille.
      Si la réponse est non, le livrable n'est pas bon — c'est la méthode d'ADR-0014, et c'est le
      seul test qui compte pour une variante de famille. Si le second `.glb` n'est pas encore
      disponible au moment du rendu, le dire et comparer à la vignette de la planche de concept.
- [ ] Le kit partagé est réutilisé **sans modification**
- [ ] Provenance renseignée

## Hors périmètre

Ne pas toucher au code gameplay, aux `.tscn`, aux `.tres`, aux tests, ni aux autres coques. Pas de
textures peintes, pas de LOD, pas de `.blend` versionné. La Resource de données, la pose des pétales
en jeu et l'intégration en vague sont traitées côté session principale : **ne rien en faire**. Ne pas
toucher non plus à `tools/blender/build_choir_mine.py` (BRIEF-0042), produit en parallèle.
