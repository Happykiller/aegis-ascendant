# BRIEF-0044 — Coque 3D du Leech Drone

- **Statut** : livré
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-08-23

## Objectif

Modéliser le **Leech Drone**, cinquième silhouette d'ennemi du Chœur Nul, en `.glb` PBR — **avec
trois pinces articulées** que le jeu ouvre à l'approche et referme à l'accrochage.

## Contexte

C'est le premier ennemi du jeu qui **poursuit le joueur**. Les huit familles précédentes suivent une
courbe indifférente à sa position ; celle-ci le traque, le rattrape, s'accroche à sa coque et lui
vole une part de sa vitesse. Elle est fragile — mais il faut viser un point mobile pendant qu'elle
vous ralentit.

Deux contrastes doivent être lisibles d'un coup d'œil :

- **contre les mines** (`choir_mine`, `null_maw`, BRIEF-0042/0043) : celles-là sont des objets qui
  attendent. Celle-ci est une **machine qui vient** — elle a un avant, un arrière, et un moteur.
- **contre le Needle Scout** : le dard est effilé et rapide sur une seule ligne. La sangsue est
  **trapue, courte, et se termine par des pinces ouvertes** : on doit voir ce qu'elle veut faire
  avant qu'elle le fasse.

**Lire d'abord** : `docs/decisions/ADR-0008-pipeline-3d-blender.md`,
`docs/decisions/ADR-0011-detail-des-coques-budgets-et-textures.md`,
`docs/forge/CHARTE_CREATIVE.md`, puis `tools/blender/lib/aegis_kit.py` — **le kit existe, le
réutiliser sans le modifier**. Modèles : `tools/blender/build_needle_scout.py` (structure) et
`tools/blender/build_choir_mine.py` (**pièces articulées**, `ak.moving_part()` — c'est le plus
récent et le mieux instrumenté).

Référence de design : **`assets/reference/concepts/null_choir_enemy_families_sheet.png`**,
**quatrième cellule en partant du haut** (Leech Drone). Regarde-la avec Read.

Traits à respecter : petit **corps globulaire**, **trois pinces courtes ouvertes vers l'avant**,
**noyau dorsal** proéminent.

## Contraintes

- **IP** : design original, aucun élément identifiable d'une licence existante.
- **Palette** : antagoniste **Chœur Nul** (charte §3). Matériaux du kit, `MATERIAL_ORDER` inchangé.
- **Techniques** :
  - Dimensions monde : **0,70 m (X) × 0,85 m (Z)**, ±3 %. Hauteur ≤ 0,34 m.
    Volontairement **la plus petite coque du bestiaire** : elle est fragile, et sa taille doit le
    dire avant que le joueur ne l'apprenne en la tuant.
  - Orientation d'auteur : **nez vers -Y, dessus vers +Z**. Les pinces regardent -Y.
  - Pivot à l'origine, centré.
  - Budget : **≤ 4 000 triangles**. Elle arrive en essaim — c'est le budget le plus serré du
    bestiaire, et c'est délibéré.
  - **Bâbord = `+X`** en repère d'auteur ; `attach_pair()` pour toute paire.
  - Déterministe, headless, Blender 4.5 LTS.
  - ⚠️ **UV OBLIGATOIRES** (`ak.box_project_uv()`) et **n-gons triangulés** avant export. Deux
    coques du dépôt sont sorties sans UV et ne peuvent recevoir aucune carte de détail ; le défaut
    est silencieux. Vérifie `TEXCOORD_0` **dans le `.glb` produit**, ne suppose pas.

### Pièces articulées

| Nœud | Ce que c'est | Pivot |
|---|---|---|
| `Claw_01` … `Claw_03` | trois pinces, réparties autour de l'axe | à la **base** de chaque pince, côté corps : elles s'écartent vers l'extérieur, comme une main qui s'ouvre |

Le jeu les pilote par `EnemyPose`, qui applique **deux gestes** : un pivot autour d'un axe horizontal
tangent au rayon de la pièce (`axe = normalize(-pos.z, 0, pos.x)`, origine = point d'articulation)
**et** un coulissement radial optionnel le long de `normalize(pos.x, 0, pos.z)`.

⚠️ **LA LEÇON DE BRIEF-0042, À NE PAS REPAYER.** Sur la Choir Mine, les six plaques pivotaient
parfaitement — et **l'ouverture était invisible en jeu**. Cause mesurée : l'enveloppe de la coque
appartenait à sa couronne de modules (r = 0,578 m) et non aux plaques (0,496 fermées, 0,477 à 45° —
le pivot les faisait *rentrer*). **Une pièce qu'on anime pour changer une silhouette doit porter
cette silhouette.**

Donc, ici : **les pinces doivent être la partie la plus extérieure de la coque**, fermées comme
ouvertes. Rien ne doit les déborder. Et le compte-rendu doit donner :

1. le **débattement mécanique** de chaque pince (angle de première interpénétration, dernière valeur
   sûre), mesuré au harnais comme pour la Choir Mine ;
2. la **croissance du diamètre apparent** entre fermé et ouvert, en **pourcentage**, mesurée à la
   perspective réelle du jeu (caméra de `graybox.tscn`) et non au cadrage serré de `render-hull.py`,
   qui surestime d'un facteur 7 ;
3. le verdict à **46 px**, planche réduite à l'appui.

**Seuil posé d'avance : sous 12 % de croissance de diamètre, l'articulation ne sert à rien** et il
faudra le dire plutôt que de livrer un mécanisme décoratif.

### Où mettre le détail

Caméra quasi **de dessus** (vue « game » à 70°). Détail et émissif sur les surfaces **supérieures**,
en **géométrie** jamais en texture fine. Le noyau dorsal porte l'émissif principal : c'est lui que le
jeu fait respirer et virer au blanc à l'engagement. **Au-delà de ~10 % de l'aire vue, l'émissif n'est
plus un accent mais une livrée** — donner la répartition mesurée.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/build_leech_drone.py` | script de construction, rejouable |
| `assets/imported/models/ships/leech_drone.glb` | le mesh exporté (LFS) |
| `docs/forge/output/BRIEF-0044-report.md` | compte-rendu : mesures réelles, débattements, limites |

## Points d'attache requis

- `Muzzle_C` — à l'avant, sur l'axe, entre les pinces. La sangsue ne tire pas, mais
  `EnemyController` lit ce point à l'initialisation de toute coque : il doit exister.
- `Engine_C` — **obligatoire ici**, contrairement aux mines. Celle-ci a un moteur et le jeu lui
  accroche une plume : c'est ce qui la fera lire comme une chose qui *vient*, et non comme un objet
  qui dérive.

## Provenance

Une ligne dans `assets/licenses/ASSET_PROVENANCE.csv`, **en append shell (`>>`)**, jamais par
réécriture. `asset_type=model3d`, `source_tool=asset-forge (Blender 4.5.11, script)`,
`license=proprietary-internal`, `prompt_file=docs/forge/briefs/BRIEF-0044-leech-drone-hull.md`.

## Critères d'acceptation

- [ ] `blender45 -b -P tools/blender/build_leech_drone.py` régénère le `.glb` sans erreur
- [ ] Bounding box 0,70 × 0,85 m (±3 %), hauteur ≤ 0,34 m — chiffres réels au rapport
- [ ] ≤ 4 000 triangles
- [ ] `./scripts/build-hull.sh --check leech_drone` : deux exécutions, `.glb` byte-identique
- [ ] **`TEXCOORD_0` présent sur 100 % des primitives**, vérifié dans le `.glb` produit
- [ ] Palette Chœur Nul, émissif visible du dessus, répartition mesurée
- [ ] `Muzzle_C` **et** `Engine_C` correctement placés
- [ ] Trois `Claw_NN` en pièces mobiles, **débattement mesuré**, et **les pinces sont la partie la
      plus extérieure de la coque** dans les deux poses
- [ ] **Croissance du diamètre apparent mesurée** à la perspective du jeu, verdict à 46 px
- [ ] **Rendu et regardé** (ADR-0006) : planche 4 vues + planche pinces ouvertes
- [ ] Elle se distingue du Needle Scout ET des deux mines sur l'aplat noir vu de dessus
- [ ] Kit réutilisé **sans modification**
- [ ] Provenance renseignée

## Hors périmètre

Pas de `.tscn`, `.tres`, code, tests — la session principale s'en charge. Pas de textures peintes,
pas de LOD, pas de `.blend` versionné.
