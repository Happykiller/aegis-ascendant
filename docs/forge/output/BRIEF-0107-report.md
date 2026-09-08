# BRIEF-0107 — Creuser le massif arrière : compte-rendu de forge

- **Brief** : [`docs/forge/briefs/BRIEF-0107-creuser-la-poupe-pour-les-panaches.md`](../briefs/BRIEF-0107-creuser-la-poupe-pour-les-panaches.md)
- **Agent** : `asset-forge` — Blender 5.2.1 LTS, `-t 1`
- **Date** : 2026-09-08
- **Porte de qualité** : `./scripts/check.sh` → **ALL GREEN** (999 tests, 8 139 assertions,
  0 échec, 0 erreur de parse)
- **Périmètre touché** : `tools/blender/build_stern.py`, `stern_hull.glb`, cette page, la planche,
  la ligne de provenance. **Aucun `.gd`, aucun `.tscn`, aucun `.tres`.** Aucun commit git.

## Livrables

| Fichier | Contenu |
|---|---|
| `tools/blender/build_stern.py` | le générateur — **il est la source** (`ADR-0008`) ; il lit désormais aussi `plume_cortege.tres` et le repère `CTRL \| Socket VFX flamme` de `stern_engine.glb` |
| `assets/imported/models/backgrounds/stern_hull.glb` | la carène creusée, 298,1 Kio, `sha256 aaf3eddf…9b4c2632` |
| `docs/forge/output/BRIEF-0107-planche.png` | **huit** vignettes, dont quatre à la caméra du jeu, **les trois panaches allumés** |
| `assets/licenses/ASSET_PROVENANCE.csv` | ligne `stern_hull` réécrite |

```sh
blender-aegis -t 1 -b -noaudio -P tools/blender/build_stern.py            # le binaire
blender-aegis -t 1 -b -noaudio -P tools/blender/build_stern.py -- --plate # + la planche
```

---

## 1. Les cotes du panache ne sont plus écrites nulle part — elles sont relues

Le brief donne « axe `y = −8,63` », « demi-largeur 1,70 m », « départ `z = −4,03` ». Recopier ces
trois nombres dans le générateur aurait rouvert exactement l'écart que ce fichier passe cent lignes
à refermer sur l'anneau de jonction. Le générateur les **reconstruit** :

| Cote | D'où elle vient |
|---|---|
| bouche de tuyère `z = −5,980` | `stern_engine.glb`, nœud `CTRL \| Socket VFX flamme`, lu au build |
| morsure de gorge `+1,35` | `THROAT_BITE`, la seule constante recopiée (elle vit dans un `.gd` hors périmètre) |
| axe `y` | `deck_y + engine_seat.y × scale_of(central)`, lu dans `long_cortege_stern.tres` |
| demi-largeur 1,70 | `throat_radius × belly_flare`, lu dans `plume_cortege.tres` |
| longueur 14,00 | `length_full`, même Resource |

Ce que la relecture a fait apparaître, et que le brief n'écrivait pas : **le panache central n'est
pas à la même altitude que les latéraux.** Son groupe porte `central_scale = 1,06`, donc
`k = 0,922` au lieu de `0,87` :

| | axe `y` | départ `z` | pointe `z` | bande `y` occupée |
|---|---|---|---|---|
| latéraux (×2) | **−8,631** | −4,03 | −18,03 | −10,330 … −6,931 |
| **central** | **−8,438** | −4,27 | −18,27 | −10,137 … −6,738 |

Le fond retenu (−10,95) dégage donc **0,619 m** sous les latéraux et **0,813 m** sous le central.
Aucun des deux cas n'est limitant, mais il fallait le vérifier plutôt que de creuser pour une
seule des deux valeurs.

> Note de mesure : `1,70 m` est le produit `throat_radius × belly_flare`. Le maillage réel du
> shader (`engine_plume.gdshader`) culmine à **1,590 m** à `t = 0,125`, l'effilement ayant déjà
> commencé quand le ventre finit de s'ouvrir. La cote du brief est donc **conservatrice de 11 cm**,
> et c'est elle qui est gardée pour dimensionner le canal.

## 2. Le plateau n'a pas été percé : il est descendu, et le massif est remonté par bossages

Creuser par soustraction demandait un booléen — non déterministe à la topologie près, illisible
dans un générateur, et le fichier interdit déjà tout aléa (`-t 1`, trois exécutions au même
`sha256`). La méthode retenue est l'inverse :

1. `AFT_TOP_Y` pose le dessus du massif à **`CHANNEL_FLOOR_Y = −10,95`** sur les six premiers
   points de la demi-section (jusqu'à `|x| = 14,01`) — la peau est donc **basse par
   construction**, sans une seule soustraction ;
2. `build_channel_walls()` repose **quatre bossages** qui remontent la matière à `−8,40`, l'ancien
   plateau, et **laissent entre eux les trois canaux**.

```
   |x| ∈ [0 ; 2,20]     canal central
   |x| ∈ [2,20 ; 8,08]  bossage intérieur — il porte la tour d'échange
   |x| ∈ [8,08 ; 12,50] canal latéral
   |x| ∈ [12,50 ; 15,30] bossage extérieur — sa moitié dehors s'enterre sous la rampe de flanc
```

### ⚠️ Le point 5 devait descendre lui aussi, et c'est le harnais qui l'a dit

Laissé à son altitude d'origine (`−7,60` à `|x| = 14,01`), le point 5 rendait l'arête `4 → 5`
franchissante : elle traverse la ligne de dégagement `−10,90` à **`|x| = 11,58`**, soit **0,90 m
à l'intérieur du canal latéral** (qui va jusqu'à 12,48). Aucun des deux sommets de cette arête
n'était dans le canal — c'est exactement le cas que le brief annonce, et c'est le harnais
d'emprise du `BRIEF-0106`, réutilisé, qui le voit. Le relief de flanc repart donc du point 6
(`|x| = 15,78`), largement dehors.

### ⚠️ Le bloc de ventilation central a dû partir

`build_towers()` posait `|x| ≤ 2,10`, `z ∈ [−11,65 ; −8,45]`, sommet `−6,90` : **4 m de matière au
milieu exact du canal central**, dans la colonne de poussée du moteur central. Le `BRIEF-0106`
avait raison de le vouloir bas ; le `BRIEF-0107` mesure qu'il ne doit pas être là du tout. Il est
remplacé par **deux** blocs posés sur les bossages intérieurs, entre le canal et la tour
(`|x| ∈ [2,55 ; 3,75]`), avec leur bandeau `AA_Panel`.

## 3. Trois rainures ne sont pas une installation — ce que le canal porte

| Pièce | Cote | Rôle |
|---|---|---|
| paroi **en retrait** | 0,26 m | elle ne touche jamais le bord du canal |
| **nervures** | 0,26 × 0,30 m, pas 0,52 m, 6 par face | elles rattrapent le retrait **jusqu'au bord exact**, pas un millimètre plus loin |
| **chanfrein** | 0,70 m de large, **0,90 m de haut** | il regarde le panache par en dessous : c'est lui qui capte la seule lumière violette du niveau |
| **lèvre d'entrée** | 1,10 × 0,82 m, sommet `−7,95` | elle épaissit la bouche et monte 0,45 m au-dessus du plateau, plus son bandeau `AA_Panel` |
| **évasement de sortie** | 0,25 m par bord sur les 0,40 derniers mètres | le canal s'ouvre en sortant ; il ne se referme jamais |

Six faces de canal reçoivent nervures + lèvre (les deux faces de chaque bossage intérieur, plus la
face intérieure de chaque bossage extérieur ; la face extérieure de ces derniers est enterrée sous
la rampe de flanc et n'en porte pas).

**Rien sur le fond du canal, et c'est mesuré :** il reste 5 cm entre le fond retenu (−10,95) et la
ligne de dégagement (−10,90). Tout relief posé là la franchirait. Les 2,55 m de paroi, eux, sont
libres — c'est là que va tout le détail. C'est une limite assumée, pas un oubli.

**Aucun émissif :** `AA_Emissive_Engine` reste porté par la seule jonction d'artère (19,8 m²,
0,34 % de l'aire). Mesuré sur le binaire : **0,000000 m² d'émissif dans l'emprise des trois
canaux**. Le ruban de traverse arrière s'arrête à `z = −8,46`, soit 4 cm avant l'entrée.

## 4. Les critères d'acceptation, chiffrés sur le binaire

| Critère | Mesure sur `stern_hull.glb` | |
|---|---|---|
| Aucune matière dans le volume des trois panaches (`y > −10,90`, `\|x − station\| ≤ 2,20`, `z ≤ −8,50`), **par découpe** | **0,000000000 m²** | 🟢 |
| Le canal débouche | rien à `z ≤ −11,60` au-dessus de −10,95 ; les bossages s'arrêtent là, le biseau de peau finit les 0,40 m | 🟢 |
| ≥ 1,00 m de matière entre le fond du canal et `SOLE_Y` | **1,050 m** (et 1,50 m jusqu'à la peau réelle, `y ≈ −12,45`) | 🟢 |
| Les deux tours intactes, marge **mesurée et nommée** | socle relu `r = 1,520 m` ; marge au canal latéral **1,160 m**, au canal central **1,680 m** | 🟢 |
| Jonction `s = 500` inchangée au micron | **6,56 × 10⁻⁷ m** sur 48 sommets — **le chiffre exact d'avant le brief** (quantification float32 du glTF) | 🟢 |
| Rien de neuf dans l'emprise des berceaux | **0,000000 m²** de décor au-dessus du pont | 🟢 |
| Aucun `AA_Emissive_Engine` dans les canaux | **0,000000 m²** | 🟢 |
| Budget | **3 182** triangles / 20 000 (15,9 %) — les canaux coûtent **668 triangles** (`channel_greebles` 504 + `channel_walls` 128 + 36 pour les deux blocs de ventilation) | 🟢 |
| Déterminisme | trois exécutions → `sha256 aaf3eddf8f36e22a35b7ded1612965b5217c5c3910d188e2fdad66909b4c2632`, **zéro octet divergent** | 🟢 |
| Rendu et regardé à la caméra du jeu, **trois panaches allumés** | 8 vignettes, 4 à la caméra du jeu (0 ; 14 ; 5) FOV 62 | 🟢 |

> **Contre-mesure indépendante.** Les chiffres ci-dessus viennent du harnais du générateur, qui
> relit le `.glb` produit. Ils ont été refaits une seconde fois par un script séparé qui n'importe
> rien du générateur — décodage glTF à la main, découpe réimplémentée — et qui rend :
> `0 image embarquée`, `5 primitives, toutes avec TEXCOORD_0`, `3 182 triangles`,
> **`0,000000000000 m²`** dans le volume des panaches, `y ∈ [−12,600 ; −3,292]`, socle de tour
> `r = 1,5200` et marge `1,1600 m` aux deux tours. Un harnais qui se confirme lui-même ne prouve
> rien ; celui-ci a été contredit par personne.

Demi-largeur libre **mesurée** de chaque canal (le plus petit `|x − station|` d'un fragment de
matière resté au-dessus de −10,90, découpé sur le binaire après triangulation, soudure et
quantification float32) : **2,200 m** aux trois stations, soit **0,501 m de garde** sur le panache.

Autres invariants restés verts : plafond `y ≤ −3,292` (limite −3,20), quille `y ≥ −12,600`,
demi-largeur max 19,900 m, **zéro image embarquée** (`ADR-0028`), UV en projection en boîte
0,20 tuile/m — densité mesurée **0,1991**, anisotropie max **1,414** (borne √3 = 1,732, en baisse
depuis 1,511 : les faces neuves sont toutes alignées sur les axes).

### La cote la plus serrée, et pourquoi elle tombe pile

Elle est mesurée sur le binaire, pas déduite de la table : le harnais isole l'anneau supérieur du
socle (`y = −7,55`, altitude où **rien d'autre de la pièce n'a de sommet** — ni la lèvre à −9,30 et
−7,95, ni les nervures, ni les bossages) et en relit le rayon.

```
socle de tour   x = ±5,40 ± 1,520   ->  |x| ∈ [3,880 ; 6,920]
canal latéral   bord intérieur       ->  |x| = 8,080
marge                                ->  1,160 m      ← la cote annoncée par le brief
canal central   bord                 ->  |x| = 2,200
marge                                ->  1,680 m
```

⚠️ **Le bord extérieur du canal latéral est à 12,50 et non 12,48, et ces 2 cm sont de la
quantification, pas du goût.** Le glTF stocke en `float32` : `12,48` y devient `12,479999542`,
soit **4,6 × 10⁻⁷ m à l'intérieur de l'emprise mesurée** — assez pour qu'un harnais honnête
compte une aire non nulle. Le bord *intérieur*, lui, s'arrondit du bon côté
(`8,08 → 8,079999924`) et n'a besoin d'aucune marge : c'est ce qui laisse au socle des tours la
cote pleine de 1,16 m annoncée par le brief. Le canal est donc de demi-largeur 2,20 côté tour et
2,22 côté flanc.

## 5. La planche — huit vignettes, et pourquoi il en fallait huit

| # | Vue | Ce qu'elle prouve |
|---|---|---|
| 1 | caméra du jeu au plan de maintien, trois groupes réels + panaches | le cadrage canonique d'`ADR-0006` |
| 2 | **la même caméra, le massif au centre du cadre** | l'instant du survol où le défaut se voyait |
| 3 | la carène seule sous les trois panaches | le dégagement, sans les nacelles qui masquent |
| 4 | le massif de trois-quarts, panaches à 14 % d'énergie | la paroi, les nervures, le chanfrein, la lèvre |
| 5 | la jonction `s = 500`, rasante | elle n'a pas bougé |
| 6 | de dessus | les trois canaux alignés sur les trois axes moteur |
| 7 | blackout | rien de neuf ne reste allumé — **et la vignette peut enfin être rouge**, voir plus bas |
| 8 | damier UV à la perspective du jeu | pas d'étirement neuf |

⚠️ **La caméra du jeu ne voit pas le massif au plan de maintien, et c'est mesuré.**
`cortege_flyby.gd` immobilise le défilement de façon à poser les berceaux à `z = −6,47` ; le massif
arrière est alors à `z = −15` à `−18,5` monde, c'est-à-dire au bord supérieur du cadre. Une planche
cadrée là ne montrerait pas ce qu'on corrige. La vignette 2 avance la poupe de **13,62 m** (origine
`z = +7,15` au lieu de `−6,47`) pour viser le plateau du massif (`−8,40`, pas le pont) : **même
caméra, même champ, même distance, autre moment du survol**. Rien n'y est truqué et le calcul est
dans `AFT_WORLD_Z`.

⚠️ **Les panaches de la planche ne sont pas des cônes témoins.** Le shader d'`ADR-0017` ne tourne
pas dans Blender ; `_plume_radius()` et `_plume_shade()` en **rejouent le profil terme pour terme**
(ventre en `smoothstep(0 ; 0,08)`, effilement en racine, train de chocs triangulaire qui pince,
teinte cœur → corps → queue, alpha en `(1−t)^0,4`), et la couleur est peinte par sommet. Le rendu
est additif comme `blend_add`. Deux écarts, tous deux **dans le sens défavorable** : le terme
`shell` dépendant du regard est pris à son plancher (0,6), donc le bord est sous-estimé ; et la
vignette 4 baisse l'énergie à 14 % — parce qu'à pleine énergie le panache **remplit son canal** et
efface exactement ce qu'on vient de mesurer. Les quatre vues à la caméra du jeu sont à gain 1.

### ⚠️ La vignette de blackout ne pouvait pas échouer, et c'est corrigé

Héritée du `BRIEF-0106`, elle éteignait l'**émission** d'`AA_Emissive_Engine` et gardait le plein
éclairage de la planche. Or la couleur de base de ce matériau est le magenta `#D93D9C`, dont
l'albédo rouge vaut 0,706 : sous les 2,80 de puissance cumulée des trois directionnelles, le canal
rouge **sature**. Mesuré sur la planche précédente, les rubans éteints rendaient
`(255 ; 100 ; 250)` contre `(255 ; 113 ; 252)` allumés — **13 niveaux de vert d'écart sur 255**,
invisibles à l'œil. La vignette validait donc n'importe quoi, y compris un émissif mal rangé.

`_dim_scene()` ramène désormais les trois directionnelles **et** l'ambiante du monde à **12 %**, et
coupe les panaches (le blackout se déclenche quand la propulsion meurt). Mesuré sur la nouvelle
vignette : les rubans éteints rendent **`(109 ; 28 ; 78)`**, soit du diffus pur ; un émissif resté
allumé rendrait `(255 ; ~80 ; ~200)` **quel que soit l'éclairage**, puisque son émission ne dépend
pas des lampes. Le test peut enfin être rouge.

## Texture (`ADR-0028`)

**Aucune**, comme le brief le prescrit. Zéro image embarquée dans le `.glb` (le harnais `_audit()`
échoue le build si `gltf["images"]` est non vide), PBR par facteurs, régime du niveau entier. Les
UV existent et sont **comptés** : chaque primitive porte `TEXCOORD_0`, projection en boîte à
0,20 tuile/m dans le repère décalé de +2,00 m en z (la phase du tronçon 5 à la jonction).

## Animation (`ADR-0046` §6)

**Aucune.** C'est de la structure. `export_animations=False` dans l'export ; rien de neuf ne bouge.

## Limites connues

1. **Le fond du canal est nu.** Cinq centimètres séparent le fond (−10,95) de la ligne de
   dégagement (−10,90) : aucun relief ne tient dans cet intervalle. On pourrait en gagner en
   descendant le fond, mais le brief plafonne la profondeur à 1,00 m de matière au-dessus de
   `SOLE_Y` et le fond retenu est **au milieu exact** des deux contraintes (0,05 m d'un côté,
   0,05 m au-delà du minimum de l'autre). Si un jour on veut du relief au sol, il faut d'abord
   arbitrer laquelle des deux marges on dépense.
2. **La moitié extérieure des bossages extérieurs est enterrée** sous la rampe de flanc (à partir
   de `|x| ≈ 14,96`) : quelques faces invisibles, chiffrées à moins de 40 triangles. C'est le prix
   d'un raccord franc entre le bossage et le flanc, sans coudre à la main deux topologies.
3. **La vignette 4 baisse l'énergie du panache à 14 %.** C'est une planche de recette, pas une
   capture de jeu ; c'est écrit dans sa légende et dans le code. Aucune des vues à la caméra du jeu
   ne le fait.
4. **La vignette de blackout est éclairée à 12 %**, ce qui rend la silhouette sombre. C'est le
   seul régime sous lequel elle puisse détecter un émissif mal rangé (voir §5) ; on ne la lit pas
   pour juger la matière, mais pour compter des points lumineux.
5. **`THROAT_BITE = 1,35` est la seule cote recopiée** d'un `.gd` (`cortege_engine.gd`) : le
   périmètre du brief interdit de toucher au code, et il n'existe pas de Resource où la lire.
   Si elle change, le générateur ne suivra pas — c'est le seul point de rupture restant.

## Suggestions (hors périmètre, pour le concepteur)

- `THROAT_BITE` gagnerait à vivre dans `long_cortege_stern.tres` à côté de `flame_length` : c'est
  un paramètre de placement de VFX, et il est aujourd'hui le seul chaînon que la forge ne peut pas
  relire.
- Le canal est dimensionné sur `throat_radius × belly_flare = 1,70`, alors que le maillage culmine
  à 1,590 m. Si l'auteur ouvre un jour le ventre au-delà de `belly_flare = 1,62`, la garde de
  0,50 m tombe sous zéro **sans qu'aucun test ne le dise** — le générateur, lui, relit la Resource
  et le canal suivra automatiquement, mais seulement si on relance la forge.
