# BRIEF-0086 — compte-rendu : le bolide et son éclat

- **Produit par** : asset-forge
- **Date** : 2026-08-26
- **Brief** : `docs/forge/briefs/BRIEF-0086-bolide-et-eclats.md`
- **Kit** : `tools/blender/lib/aegis_kit.py` **1.1.0, utilisé sans aucune modification**
- **Texture** : ⛔ **aucune produite** — `TEX-0002` (roche d'astéroïde) est réutilisée, comme le brief
  le prescrit. La section « Texture » du brief est présente et tranchée (`ADR-0028`).

---

## 1. Livrables

| Fichier | Ce que c'est |
|---|---|
| `tools/blender/build_impact_debris.py` | le script de construction des **deux** pièces — **il EST la source** (ADR-0008), aucun `.blend` |
| `assets/imported/models/vfx/bolide.glb` | le bolide (LFS) — 4 112 o |
| `assets/imported/models/vfx/impact_shard.glb` | l'éclat (LFS) — 4 144 o |
| `docs/forge/output/BRIEF-0086-planche-silhouettes.png` | 1920 × 1200 — **la recette** : les deux pièces à 8 et à 24 px, sur fond noir, à côté d'une sphère lisse de même taille, + les vues de trois quarts en chute |
| `docs/forge/output/BRIEF-0086-report.md` | ce fichier |

```bash
blender45 -b -P tools/blender/build_impact_debris.py             # les deux .glb
blender45 -b -P tools/blender/build_impact_debris.py -- --plate  # + la planche (Cycles CPU, ~40 s)
./scripts/build-hull.sh --check impact_debris                    # build + déterminisme
```

**Déterminisme** — deux exécutions consécutives, `.glb` byte-identiques :

| Fichier | sha256 |
|---|---|
| `bolide.glb` | `a0dd62737a2ab0e12c63ec0cb5884e733649060f16a2ad63e0f406f207342c63` |
| `impact_shard.glb` | `8050d308a4d0ae60f173d4e67e629e21181c72cb136cc6fcd9b0ffc57735d940` |

⚠️ `build-hull.sh --check` ne contrôle que le **premier** `.glb` qu'il repère dans le script
(`grep … | head -1`), donc le bolide seul. Le déterminisme de l'éclat a été vérifié à part, à la
main, avec le même `blender45 -t 1`. Ce n'est pas un défaut du script du brief : c'est une limite
connue de l'outil, signalée ici parce qu'elle est silencieuse.

`./scripts/check.sh` est **vert** avec les deux fichiers en place (468 tests, 2 976 assertions) ;
Godot les a importés sans avertissement et a produit leurs `.import`.

---

## 2. Mesures relevées **sur les `.glb` produits** (pas sur la scène Blender)

| | `Bolide` | `Shard` |
|---|---|---|
| Triangles | **32** (plafond 400) | **20** (plafond 150) |
| Sommets | 54 | 56 |
| Primitives | 1 | 1 |
| bbox Godot X × Y × Z | **1,380 × 1,100 × 2,700 m** | **0,500 × 0,280 × 1,050 m** |
| Origine (centre bbox) | (+0,0000, +0,0000, +0,0000) | (+0,0000, +0,0000, +0,0000) |
| Nœud | `Bolide`, racine, **aucune translation** | `Shard`, racine, **aucune translation** |
| `TEXCOORD_0` | **1/1 primitives** | **1/1 primitives** |
| `TANGENT` | 1/1 | 1/1 |
| Matériau | `Asteroid_Rock` (unique, partagé) | `Asteroid_Rock` (le même) |
| Surface | 13,53 m² | 1,50 m² |
| Fichier | 4 112 o | 4 144 o |

**Budgets tenus très largement** : 32 et 20 triangles, soit **8 %** et **13 %** des plafonds. Le
brief disait « plafonds, pas cibles ». À 8 px, un triangle de plus ne se voit pas : le budget est
allé dans le **choix** des plans de coupe, pas dans leur nombre.

**Vérifié indépendamment** par `python3 tools/blender/inspect_glb.py` (relecture du binaire) :
`UV+tangentes sur 1/1 maillages`, un seul nœud racine par fichier, `images: None`,
`textures: None`, aucune extension, aucun `emissiveFactor`.

**Aucun émissif, aucune texture** : `baseColorFactor = (0.100, 0.098, 0.118, 1)` en linéaire —
exactement `ROCK_ALBEDO` de `build_moon_flyby.py`, elle-même reprise de `scripts/vfx/moon_flyby.gd`
où elle a été validée en capture. Froide (B > R), sombre. Ni cyan, ni corail. Le harnais d'audit
**échoue le build** si une image, un `baseColorTexture`, un `emissiveTexture` ou un
`emissiveFactor` non nul apparaît.

---

## 3. UV — tuiles par mètre, et pourquoi ce chiffre-là

- **Dépliage** : `ak.box_project_uv(obj, texels_per_meter = 1 / 8)` — **littéralement la même ligne
  que `build_moon_flyby.build_rock()`**, avec la même constante.
- **Échelle monde : 8,0 m de roche par tuile, soit 0,125 tuile/m.** Elle est **cuite dans les UV**
  en coordonnées locales : côté Godot, `uv1_scale` **reste (1, 1, 1)**, exactement comme pour les
  trois astéroïdes du survol.
- Ce que la pièce couvre de la tuile de `TEX-0002` : **0,34 tuile** en longueur pour le bolide,
  **0,13 tuile** pour l'éclat. C'est voulu : normaliser sur la pièce aurait donné un grain trois
  fois plus fin et fait lire le bolide comme du gravier au lieu d'un bloc.

**Densité de texels mesurée triangle par triangle sur le fichier livré** (valeurs singulières de la
matrice plan-vers-UV — une moyenne d'aires ne verrait aucun étirement) :

| Pièce | m/tuile min → max | moyenne (cible 8,0) | anisotropie max |
|---|---|---|---|
| `Bolide` | 8,00 → 10,71 | **8,22** | 1,34 |
| `Shard` | 8,00 → 11,04 | **8,23** | 1,38 |

**Coutures** : la projection en boîte pose une couture partout où une face bascule d'un plan de
projection à l'autre — c'est le principe, et le brief le demande explicitement pour ces pièces vues
de loin. Elle est sans conséquence ici pour deux raisons additionnées : `TEX-0002` est une carte
**répétable** en niveaux de gris (aucun motif à raccorder), et la pièce fait 8 à 13 px à l'écran.
**Aucune planche au damier UV n'est donc livrée** : `ADR-0028` la rend obligatoire pour un dépliage
**continu à densité homogène**, ce que la projection en boîte n'est pas et ne prétend pas être.

⚠️ **Une échelle posée sur le nœud côté Godot multiplie cette densité d'autant.** Sous ×1,3 c'est
invisible ; au-delà, il faut revenir changer `BOLIDE_SIZE` / `SHARD_SIZE` dans le script et
rebâtir, pas étirer le nœud.

---

## 4. Les silhouettes, et le verdict à 8 px

### Ce qui a décidé de la forme

Les trois rochers du survol partent d'une icosphère de 1 280 triangles bruitée puis rabattue sur
onze plans de cassure. **Ici ce serait le mauvais outil** : à 8 px un bruit à haute fréquence
disparaît entièrement et ne laisse qu'un cercle. Les deux pièces partent donc d'une **boîte aux
proportions voulues, taillée par six ou sept plans choisis** — grandes facettes, coins nets,
trente triangles au lieu de mille.

- **Le bolide, « le coin »** : bloc de rapport **1,96 : 1** (2,70 pour 1,38 de large), épaulé à
  l'avant-bas par une grande cassure oblique, affiné vers l'arrière. 11 facettes planes ; la plus
  grande porte **19 %** de la surface, les trois plus grandes **52 %**.
- **L'éclat, « l'écharde »** : lame de rapport **3,75 : 1**, pointue à l'avant, cassée net à
  l'arrière en deux facettes, d'épaisseur décroissante. 10 facettes ; la plus grande **25 %**, les
  trois plus grandes **60 %**.
- **Rien sous ~40 cm** : plus petite arête du polyèdre **0,281 m** (bolide) et **0,136 m** (éclat),
  mesurée **avant** triangulation (les diagonales d'un n-gon ne sont pas des arêtes de forme). Le
  build échoue sous le plancher. ⚠️ Le plancher n'est pas le même pour les deux, et ce n'est pas une
  facilité : l'éclat **est** un détail de 40 cm — il ne fait qu'un mètre pour 28 cm d'épaisseur, et
  lui imposer 40 cm d'arête minimale reviendrait à interdire sa propre section.
- **Solides convexes**, délibérément : à 8 px une concavité de 40 cm vaut moins d'un pixel.

### Comment la planche mesure « 8 pixels » sans tricher

Caméra **orthographique**, `ortho_scale = 1,75 × la plus grande dimension de la pièce`, rendu dans
un cadre de 14 px : la pièce couvre exactement 8 px, et la sphère témoin — **même diamètre, même
cadre, même caméra, même lumière** — en couvre 8 aussi. Agrandissement au **plus proche voisin**
(×12 et ×4) : on regarde les vrais pixels, jamais un rééchantillonnage qui les lisserait.
`filter_size = 1,0` et non le défaut 1,5, ce qui approche un sous-échantillonnage 2×2 en boîte.

⚠️ **Les deux pièces ne s'y rendent pas pareil, parce que le jeu ne les rend pas pareil.** Le bolide
porte un matériau **non éclairé** (émission ×3,4) : ligne 1 de la planche. L'éclat est **éclairé** :
ligne 4. Chaque ligne a sa sphère témoin rendue **dans le même mode** — comparer un caillou éclairé
à une sphère émissive n'aurait rien prouvé.

### Verdict — mesuré, puis regardé

| À 8 px | Boîtes englobantes (3 poses) | Pixels allumés | contre la sphère | Recouvrement pièce/sphère |
|---|---|---|---|---|
| `Bolide` (non éclairé) | 8×10, 9×8, 10×10 | 50 → 66 | 83 (constant, boîte 10×10) | **60 % → 77 %** |
| `Shard` (éclairé) | 6×8, 7×6, 9×7 | 28 → 45 | 72 (constant, boîte 10×10) | **39 % → 62 %** |

| À 24 px | Boîtes englobantes | Pixels allumés | contre la sphère | Recouvrement |
|---|---|---|---|---|
| `Bolide` | 19×25, 22×20, 26×25 | 269 → 398 | 543 (boîte 26×26) | 50 % → 70 % |
| `Shard` | 16×24, 20×14, 23×20 | 160 → 294 | 512 (boîte 26×26) | 31 % → 57 % |

**Verdict : les deux pièces passent la recette à 8 px, et ce n'est pas serré.**

Ce que la planche a été **regardée** (`ADR-0006`) pour établir, et que les chiffres confirment :

1. **La sphère est un disque plein qui remplit le cadre et ne bouge jamais** — 83 px allumés aux
   trois poses, boîte **10×10** aux trois poses, immobilité d'une pose à l'autre **100 %** (mesurée,
   pas supposée : le harnais compare les masques). La boîte fait 10 et non 8 parce qu'elle compte
   tout pixel au-dessus de 6 % de luminance : le filtre d'antialiasing étale un disque de 8 px sur
   10 px de couverture partielle. Le même seuil s'applique aux deux, la comparaison reste juste.
2. **Le bolide couvre 20 à 40 % de pixels en moins et change de forme à chaque pose** : boîte
   8×10 (debout), puis 9×8 (couché), puis 10×10 (de biais). C'est cette **pulsation** qui le lit
   comme un caillou qui tourne, et une sphère ne peut pas la produire.
3. **L'éclat est le plus net des deux** : 28 à 45 px pour 72 à la sphère, recouvrement descendant à
   **39 %**. À 8 px il se lit comme un **trait**, pas comme une tache — c'est-à-dire exactement
   comme le débris qu'il est. C'est la pièce dont la forme paie le plus, parce qu'elle est éclairée
   et que son contour arrive intact à l'écran.
4. **À 24 px, le bolide n'est plus discutable** : les facettes se lisent, la grande cassure oblique
   accroche la clé, les trois poses donnent trois contours francs.

L'axe de culbute de la planche est **volontairement presque perpendiculaire à la longueur** : un axe
pris le long de la pièce l'aurait fait tourner sur elle-même sans que sa silhouette bouge d'un
pixel, et la planche n'aurait rien prouvé.

---

## 5. ⚠️ Ce que la planche ne dit pas, et qui compte : le bloom

`resources/graphics/space_environment.tres` pose `glow_enabled = true` et
`glow_hdr_threshold = 1.6`. Le bolide est posé à **3,4** d'émission (`moon_flyby.gd`). Il dépasse
donc franchement le seuil, et le moteur lui ajoute un halo **dont la largeur est en pixels d'écran,
pas en mètres**. À 8 px, ce halo noie le contour ; à 24 px, il ne fait que le border.

C'est cohérent avec ce que vous avez déjà mesuré en réduisant `BOLIDE_SCALE` de 3,0 à 1,8 (« à 3×
elle rendait une tache dorée saturée par le bloom »). Trois lectures possibles, dans l'ordre où je
les recommanderais :

1. **Laisser tel quel et assumer.** Votre commit dit déjà que c'est la **traînée** qui porte la
   lecture, pas la tête. Dans ce cadre le bolide forgé apporte surtout un **contour non circulaire à
   la pointe de la traînée** et une base de 1,38 m qui se raccorde bien au cône de rayon 0,7 — un
   gain réel mais secondaire, et le vrai bénéfice du chantier est alors l'**éclat**.
2. **Descendre `emission_energy_multiplier` sous 1,6** (≈ 1,4) pour la phase de chute. Le halo
   disparaît, la silhouette forgée redevient visible, et la tête cesse de concurrencer le flash
   d'impact (posé à 9,0). C'est la seule option qui rentabilise vraiment la géométrie du bolide.
3. Passer la tête en matériau **éclairé** comme les éclats : le maximum d'information de forme, mais
   elle redeviendrait sombre à 96 unités — l'écueil que votre commentaire de `_build_impact_kit()`
   documente déjà.

Je ne tranche pas : c'est du code, et c'est votre périmètre.

---

## 6. ⚠️ Deux pièges d'intégration

**a. L'axe long est Z, `basis_from_up()` aligne Y.** Le contrat de noms du brief dit « plus long que
large » : la grande dimension du bolide est donc **Godot +Z** (le harnais refuse le build si Z
n'excède pas X d'au moins 20 %). Or `moon_flyby.basis_from_up()` construit une base dont l'axe **Y**
suit la direction donnée — c'est ce qu'il faut pour les `CylinderMesh` de la traînée et de l'onde,
bâtis le long de +Y. **Le pointer tel quel sur le bolide le coucherait en travers de sa course.**
Pour aligner la longueur sur `bolide_heading()`, il faut une base qui met la direction sur Z :
`Basis.looking_at(heading)`, ou la base existante tournée de −90° autour de X.

**b. Taille livrée contre taille actuelle.** La doublure en place vaut aujourd'hui
`SphereMesh(rayon 0,85 × BOLIDE_SCALE 1,8)` × `scale (1, 0,62, 0,84)`, soit **3,06 × 1,90 × 2,57 m**.
Le bolide livré fait **2,70 × 1,38 × 1,10 m** — plus long que large, et nettement plus fin. Pour
retrouver exactement la masse à l'écran de la tête actuelle, une échelle uniforme de **1,13**
suffit, et elle est sans effet perceptible sur le grain (cf. §3). Les tailles réelles à l'écran, à
4,7 px/m :

| | livré | à l'écran (échelle 1,0) |
|---|---|---|
| `Bolide` | 2,70 m de long | **12,7 px** |
| `Shard` | 1,05 m de long | **4,9 px** |

L'éclat livré remplace le `BoxMesh(0,72 ; 0,40 ; 1,00)` actuel : même longueur, plus étroit
(0,50 contre 0,72) et plus fin (0,28 contre 0,40), et taillé en lame. C'est ce qui corrige le
« les éclats lisent encore comme des carrés plats » de votre commit.

---

## 7. `ak.export_hull()` n'a pas pu être utilisé — et pas pour la raison attendue

Le brief anticipait le problème de `BRIEF-0085` (des corps portant une translation). **Ce
problème-là ne se pose pas ici** : les deux pièces sont bien à l'origine, nœud sans translation,
comme le contrat de `export_hull()` l'exige. C'est un **autre** point du contrat qui bloque, et il
est net dans le kit :

```python
for name in tris_by_mat:
    if name not in MATERIAL_ORDER:
        problems.append(f"materiau hors nomenclature ADR-0008 : {name}")
```

`MATERIAL_ORDER` ne contient que les sept matériaux de faction (`AA_Hull`, `AA_Panel`…). Or le brief
impose « une couleur de roche froide et sombre, comme les astéroïdes du survol » — c'est-à-dire
`Asteroid_Rock`, qui n'appartient à aucune faction. Passer par `AA_Hull` aurait livré du blanc cassé
Vanguard (`#EDEAE3`) ou de l'anthracite Null Choir sur des cailloux neutres, et surtout aurait cassé
le **partage de matériau** avec les trois rochers du survol, que `TEX-0002` demande explicitement.

L'export et sa validation sont donc refaits dans le script, **comme au 0085** : même correction
d'axe (`Rotation(π, Z)` puis `yup`), même garde-fou analytique sur témoins asymétriques, même
relecture du `.glb` produit. **Le kit n'a pas été touché** — il est importé tel quel pour
`box_project_uv()`, `cleanup()` et `ContractError`.

---

## 8. Les dix harnais qui échouent le build

Tous s'exécutent à chaque `blender45 -b -P tools/blender/build_impact_debris.py`, et tous lèvent
`ContractError` sur le **fichier produit**, jamais sur la scène en mémoire :

1. chaîne d'axes vérifiée sur **témoins asymétriques** (une bounding box ne voit pas un demi-tour) ;
2. contrat de noms : le nœud s'appelle `Bolide` / `Shard`, et il est unique ;
3. le nœud est **à l'origine** — aucune translation cachée côté Godot ;
4. `TEXCOORD_0` **compté dans le binaire** sur 100 % des primitives, `TANGENT` idem ;
5. dimensions dans la tolérance (±4 %) ;
6. origine au **centre** de la bbox sur les trois axes (±1 cm) ;
7. « plus long que large » pour le bolide (Z > 1,2 × X) ;
8. plafonds de triangles ;
9. **aucune image, aucun `*Texture`, aucun émissif cuit** (`ADR-0028` + contrainte du brief) ;
10. densité de texels dans la fenêtre de `ROCK_METRES_PER_TILE`, et plus petite arête au-dessus du
    plancher de la pièce.

---

## 9. Limites connues et suggestions

- **Le bloom, §5.** C'est la seule vraie limite de ce livrable, et elle est hors de mon périmètre.
  Tant que la tête brûle à 3,4 au-dessus d'un seuil de 1,6, une part de la silhouette du bolide est
  payée pour rien. L'éclat, lui, n'est pas concerné.
- **Une seule variante d'éclat.** Les quatorze exemplaires partageront la même forme, et à 5 px
  personne ne le verra — mais s'ils devaient un jour grossir (un impact au premier plan, une phase
  plus proche), trois variantes taillées par le même mécanisme coûteraient 60 triangles au total.
  Le script est prêt à les produire : il suffit d'ajouter des entrées à `PIECES`.
- **Pas de LOD, pas de collision.** Le brief ne les demandait pas et à 20-32 triangles ils n'ont
  aucun sens.
- **La planche ne simule ni le post-process rétro, ni le tonemap AgX du jeu.** Elle rend en
  « Standard », délibérément : elle compare des **contours** et des couleurs cuites dans le code,
  et une courbe de tonalité aurait fait mentir l'aplat non éclairé du bolide.
- **Suggestion, si vous suivez la piste 2 du §5** : la vue de trois quarts de la planche (colonne de
  droite, sous la lumière du jeu) montre à quoi ressemblerait alors la tête. C'est cette image-là
  qu'il faudra comparer à une capture in-game, pas les vignettes.
