# BRIEF-0042 — Coque 3D de la Choir Mine

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-08-23

## Objectif

Modéliser la **Choir Mine**, troisième silhouette d'ennemi du Chœur Nul, en `.glb` PBR, avec le kit
hard-surface partagé — **et avec des segments réellement articulés**, que le jeu ouvre pendant le
télégraphe.

## Contexte

C'est la **première unité du jeu qui n'est pas un vaisseau**. Les trois coques existantes sont des
machines de vol qui traversent l'écran ; celle-ci ne manœuvre pas. Elle dérive avec le décor, dort,
et n'existe que par la distance : le joueur avance vers elle, elle s'éveille, elle éclate en une
couronne de projectiles (voir `docs/decisions/ADR-0022-les-ennemis-peuvent-connaitre-le-joueur.md`,
qui décrit son cycle `DORMANT → ALERT → WINDUP → ACTIVE`).

Toute la silhouette doit dire ça d'un coup d'œil : **un objet, pas un pilote**. Si elle se lit comme
un petit vaisseau, elle a raté sa première seconde de jeu — le joueur essaiera de l'esquiver au lieu
de la traiter comme un obstacle qu'on décide de dépenser ou de contourner.

**Lire d'abord** : `docs/decisions/ADR-0008-pipeline-3d-blender.md` (conventions normatives),
`docs/decisions/ADR-0011-detail-des-coques-budgets-et-textures.md` (budgets relevés),
`docs/forge/CHARTE_CREATIVE.md`, puis `tools/blender/lib/aegis_kit.py` — **le kit existe, le
réutiliser sans le modifier**. Deux modèles de structure :
`tools/blender/build_needle_scout.py` (assemblage, matériaux par bande) et
`docs/forge/briefs/BRIEF-0039-choir-harvester-pieces-animables.md` (**pièces articulées** :
`ak.moving_part()`, origines aux points de pivot).

Référence de design : **`assets/reference/concepts/null_choir_enemy_families_sheet.png`**,
**troisième cellule en partant du haut** (Choir Mine) — vue de dessus à gauche, vue 3/4 à droite.
Regarde-la avec Read.

Traits à respecter :

- **disque radial trapu**, ramassé, nettement plus épais qu'une coque de chasseur ;
- une **couronne de modules périphériques** — la planche en montre une dizaine ;
- un **noyau central** proéminent, c'est lui qui portera la pulsation en jeu ;
- **une pointe unique** qui casse la symétrie radiale. Elle n'est pas décorative : la charte §4
  impose au Chœur Nul « au minimum une rupture asymétrique majeure », et sur un objet aussi
  régulier c'est la seule chose qui l'empêche de lire comme une roue dentée.

## Contraintes

- **IP** : design original, aucun élément identifiable d'une licence existante.
- **Palette** : palette antagoniste **Chœur Nul** de la charte §3 — anthracite `#24252B`, violet
  sombre `#452663`, ivoire froid `#DDDCD2`, magenta `#D93D9C` en émissif. Matériaux normalisés du
  kit, `MATERIAL_ORDER` inchangé.
- **Techniques** :
  - Dimensions monde : **1,15 m (X) × 1,15 m (Z)**, ±3 %.
  - ⚠️ **Hauteur : 0,45 à 0,55 m.** C'est une dérogation ASSUMÉE à la règle d'ADR-0008 (« hauteur
    Y ≈ 15-25 % de la longueur »), qui décrit des cellules d'avion. Un objet ramassé n'obéit pas à
    la même règle qu'une aile, et c'est justement l'épaisseur qui le distingue d'un chasseur vu de
    dessus. Consigner la valeur réelle dans le compte-rendu ; la session principale recensera la
    coque dans ADR-0008.
  - Orientation d'auteur : **nez vers -Y, dessus vers +Z** dans Blender. Une mine n'a pas de nez,
    mais la convention reste : c'est l'axe -Y qui deviendra « vers le joueur » en jeu. **Poser la
    pointe asymétrique sur cet axe -Y**, pour qu'elle pointe vers le joueur.
  - Pivot à l'origine, au centre géométrique du disque.
  - Budget : **≤ 6 000 triangles**. ADR-0011 a relevé le plafond « ennemi léger » à 12 000, mais la
    mine est instanciée en champ : la moitié du plafond est déjà confortable pour un objet radial.
  - Ne jamais écrire un signe de X à la main pour les paires : **bâbord est `+X`** en repère
    d'auteur — utiliser `attach_pair()`.
  - Déterministe, headless, Blender 4.5 LTS.

### Pièces articulées — la partie neuve

Le jeu ouvre la mine pendant son télégraphe (0,3 à 0,8 s), puis elle éclate. Il faut donc des pièces
que Godot puisse **faire pivoter**, déclarées par `ak.moving_part(nom, bmesh, pivot, parent)`.

| Nœud | Ce que c'est | Pivot |
|---|---|---|
| `Segment_01` … `Segment_06` | six segments de la carapace, répartis autour du noyau | sur le **bord intérieur** de chaque segment, côté noyau, pour qu'ils s'écartent en corolle plate et non en tournant autour du centre du disque |

⚠️ **Le piège documenté** (`aegis_kit.moving_part` docstring, et
`.claude/resources/pratique-detail-en-fraction-de-corde.md`) : une pièce dont l'origine reste à zéro
décrit un arc de cercle autour du centre de l'objet au lieu de s'articuler. Poser les origines au
point d'articulation, et **vérifier au rendu, pièce déviée**, pas seulement au repos — un défaut
d'animation ne se voit pas sur une pose fixe, et le contrat d'export validera sans un mot.

Donner dans le compte-rendu, pour chaque segment : la position du pivot en coordonnées Godot, et
**le débattement mécanique disponible avant que la pièce ne traverse une voisine ou le noyau**. Ce
chiffre est la donnée dont la session principale a besoin pour régler l'ouverture ; sans lui, elle
la règlera à l'aveugle et la mine s'auto-intersectera à l'écran.

### Où mettre le détail (contrainte de lisibilité, pas de goût)

La caméra de jeu regarde la scène quasiment **de dessus** (la vue « game » de `tools/render-hull.py`
est prise à 70° au-dessus du plan). Tout le détail et **tout l'émissif** doivent vivre sur les
surfaces supérieures. Ce qui est posé sur les flancs verticaux n'existe pas pour le joueur.

Le noyau supérieur porte l'émissif principal : c'est lui que le jeu fait respirer au repos et monter
en régime à l'approche (`EnemyVitals`). Il doit donc être **franchement visible de dessus** et rester
lisible une fois la mine ouverte — c'est-à-dire quand les segments l'auront dégagé.

Le détail vient de la **géométrie** — `bevel_sharp_edges`, `inset_panel`, `greeble_strip`,
`add_lathe` — jamais d'une texture fine : le post-traitement rend en 960×540 avec scanlines et
l'écrase (ADR-0011, ADR-0016).

⚠️ **Émissif au-delà d'environ 10 % de la surface de coque, ce n'est plus un accent, c'est une
livrée** (`.claude/resources/pratique-revue-asset.md`). Sur une mine dont le noyau doit pulser, la
tentation est forte : donner la répartition mesurée des matériaux dans le compte-rendu.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/build_choir_mine.py` | script de construction, rejouable |
| `assets/imported/models/ships/choir_mine.glb` | le mesh exporté (LFS) |
| `docs/forge/output/BRIEF-0042-report.md` | compte-rendu : mesures réelles, débattements, limites |

## Points d'attache requis

- `Muzzle_C` — **au centre du noyau**, sur l'axe. La mine tire une couronne complète depuis son
  cœur, pas depuis un canon : ce point est l'origine de la couronne.
- **PAS de `Engine_C`.** Une mine n'a pas de moteur — le contrôleur a été modifié pour ne poser une
  plume d'échappement que si la coque en déclare un. Une tuyère allumée la ferait lire comme un
  vaisseau en approche, c'est-à-dire comme la seule chose qu'elle n'est pas.

## Provenance

Une ligne dans `assets/licenses/ASSET_PROVENANCE.csv`, **ajoutée en append shell (`>>`), jamais par
réécriture du fichier** : un autre brief de coque tourne en parallèle et réécrire le CSV écraserait
sa ligne. `asset_type=model3d`, `source_tool=asset-forge (Blender 4.5.11, script)`,
`license=proprietary-internal`, `prompt_file=docs/forge/briefs/BRIEF-0042-choir-mine-hull.md`. Le
champ `notes` porte le rapport de contrat condensé, sur le modèle de la ligne `needle_scout_hull`
(sans accents ni virgules internes).

## Critères d'acceptation

- [ ] `blender45 -b -P tools/blender/build_choir_mine.py` régénère le `.glb` sans erreur
- [ ] Bounding box 1,15 × 1,15 m (±3 %), hauteur entre 0,45 et 0,55 m — chiffres réels au rapport
- [ ] ≤ 6 000 triangles
- [ ] Deux exécutions successives produisent un `.glb` **byte-identique**
      (`./scripts/build-hull.sh --check choir_mine` — il force `-t 1`, le multithread casse le
      déterminisme des tangentes)
- [ ] Palette Chœur Nul, émissif magenta présent **et visible depuis le dessus**, répartition
      des matériaux mesurée et donnée
- [ ] `Muzzle_C` au centre du noyau ; **aucun** `Engine_C`
- [ ] Six `Segment_NN` déclarés en pièces mobiles, pivots au bord intérieur, **débattement mesuré**
- [ ] **Rendu et regardé** :
      `blender45 -b -P tools/render-hull.py -- assets/imported/models/ships/choir_mine.glb`, et le
      compte-rendu dit ce que la planche montre. Un livrable non rendu n'est pas un livrable
      (ADR-0006). Dire notamment : **la mine se lit-elle comme un objet et non comme un vaisseau,
      sur la vue « jeu », à petite taille ?**
- [ ] Une planche supplémentaire **segments ouverts** (pose déviée), pour prouver que l'articulation
      ne traverse rien
- [ ] Le kit partagé est réutilisé **sans modification** (si une évolution est vraiment nécessaire,
      la signaler dans le compte-rendu au lieu de la faire en douce)
- [ ] Provenance renseignée

## Hors périmètre

Ne pas toucher au code gameplay, aux `.tscn`, aux `.tres`, aux tests, ni aux autres coques. Pas de
textures peintes, pas de LOD, pas de `.blend` versionné. La trajectoire, la Resource de données, la
pose des segments en jeu et l'intégration en vague sont traitées côté session principale : **ne rien
en faire**. Ne pas toucher non plus à `tools/blender/build_null_maw.py` (BRIEF-0043), qui est produit
en parallèle.
