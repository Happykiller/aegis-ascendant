# BRIEF-0024 — Compte-rendu : coque 3D du Pale Leviathan

- **Agent** : asset-forge
- **Date** : 2026-07-12
- **Brief** : `docs/forge/briefs/BRIEF-0024-pale-leviathan-hull.md`
- **Statut** : livré

## Livrables

| Fichier | Rôle |
|---|---|
| `tools/blender/build_pale_leviathan.py` | script de construction (LA source de l'asset, ADR-0008) |
| `assets/imported/models/bosses/pale_leviathan.glb` | mesh exporté (LFS, 718 792 o) |
| `docs/forge/output/BRIEF-0024-report.md` | ce document |
| `assets/licenses/ASSET_PROVENANCE.csv` | ligne `pale_leviathan_hull` ajoutée |

Régénération : `blender45 -b -P tools/blender/build_pale_leviathan.py` (headless, Blender 4.5.11 LTS).

## Mesures réelles (relevées sur le `.glb` livré, pas sur la scène Blender)

Chiffres produits par la validation de `ak.export_hull()`, qui relit le fichier binaire.

| Critère | Exigé | Mesuré | Marge |
|---|---|---|---|
| Largeur X | 7,02 m ±3 % | **7,0004 m** | −0,28 % |
| Longueur Z | 8,77 m ±3 % | **8,7700 m** | 0,00 % |
| Hauteur Y | ≤ 2,50 m | **2,3912 m** | −4,4 % |
| Triangles | ≤ 25 000 | **16 838** | 33 % de budget libre |
| Sommets | — | 24 752 | — |
| Pivot (centre bbox X, Z) | ±0,02 m | **(+0,0004 ; +0,0000)** | — |
| Matériaux | les 7 normalisés | les 7, tous portés par des faces | — |
| Points d'attache | 4 | `Core_Center`, `Muzzle_L`, `Muzzle_R`, `Muzzle_C` | — |

Répartition des triangles par matériau (palette Le Chœur Nul) :
`AA_Greeble` 5 253 · `AA_Emissive_Engine` 4 067 · `AA_Panel` 2 787 · `AA_Hull` 2 240 ·
`AA_Trim` 2 139 · `AA_Marking_Red` 220 · `AA_Glass` 132.

**Déterminisme vérifié** : trois exécutions successives donnent un `.glb` byte-identique
(SHA256 `805b9f51613e5cef1e4fae14405666d7b3bcf54112efa317b4b47365ee3be779`). Tout aléa passe par
un `random.Random(seed)` local (graine maîtresse `SEED = 481516`), jamais par le module `random`
global : écailles du croissant, croûte du noyau, tuiles du collier, greebles.

**Structure du `.glb`** : 7 nœuds à maillage + 4 Empties, **tous à la transformation identité**
(aucune rotation cachée côté Godot) :
`Body`, `Core`, `Shell_Crescent`, `Spike_01`, `Spike_02`, `Spike_03`, `Spike_04`.

## Choix créatifs et justification

**Le noyau est le seul à hurler en magenta.** La sphère (r = 1,05 m, soit 30 % de la largeur,
comme sur la planche) est bâtie en `AA_Emissive_Engine` ; une croûte de plaques violettes est
ensuite *soulevée* facette par facette (42 %, tirage seedé). Ce qui reste au niveau de la sphère —
les interstices et les parois d'inset — est émissif : la lumière sort **d'entre** les plaques.
C'est la craquelure lumineuse de la planche, obtenue par la géométrie, pas par une texture (ADR-0008).

Une première version mettait aussi du magenta sur le dessus des plaques du croissant. Résultat :
un tournesol de rayons roses qui volait la vedette au noyau. Or le noyau **est la cible** : il doit
être le seul point magenta massif de la silhouette (spec, pilier B — lisibilité). Corrigé : aucun
dessus de plaque n'est émissif, le magenta de la coque se limite à des lignes fines.

**Le croissant est une armure à écailles, pas une roue à rayons.** Première version : une rangée de
plaques radiales (courtes en azimut, pleine largeur en radial). Vu de dessus — l'angle de la caméra
de jeu — cela donnait une rosace, un store vénitien. Refait en **trois rangées concentriques de
tuiles tangentielles** (longues le long de l'arc, courtes en radial), décalées en phase, qui se
recouvrent en radial *et* en azimut, chaque rangée montant sur la précédente. C'est la définition
géométrique d'une armure à écailles, et c'est ce que montre la planche.

**Les interstices lumineux viennent de la contremarche.** Chaque tuile chevauche sa voisine ; son
bord d'attaque dépasse donc en petite marche verticale. Une fois sur deux (tirage seedé), cette
contremarche est émissive. Vu de dessus, on obtient un réseau de fines coutures magenta entre les
plaques — sans peindre la moindre surface, et sans concurrencer le noyau. Même procédé sur le
collier du noyau et sur les écailles dorsales : c'est ce qui fait la carapace organo-mécanique.

**L'anneau est incomplet du côté armé.** Le croissant court de −150° à +80° d'azimut (230°) ; les
130° manquants ouvrent sur le quadrant **arrière-tribord**, exactement là où sortent les deux
longues épines. L'ouverture n'est pas décorative : c'est le côté où le boss frappe. Le bord interne
de la rangée haute descend à r ≈ 0,90 m pour z ≈ 1,15 m, c'est-à-dire **au-dessus** du sommet du
noyau (1,05 m) : le croissant surplombe réellement le noyau, il ne se contente pas de l'entourer.

**Asymétrie — quatre sources indépendantes, aucune symétrie en X.**
1. l'axe du corps serpente (`BODY_BEND` : +0,20 m à la proue, −0,30 m au dard) ;
2. les flancs ont des multiplicateurs distincts (`BODY_PORT_MUL` / `BODY_STAR_MUL`) — épaule bâbord
   lourde à l'avant, tribord à l'arrière ;
3. les quatre épines diffèrent en longueur, courbure, épaisseur, nombre de vertèbres (8/5/7/6) et
   aplatissement ; une seule (`Spike_04`) pointe vers l'avant ;
4. les veines lumineuses de flanc ne sont pas appairées (bâbord : y ∈ [−3,1 ; 1,0] ; tribord :
   y ∈ [−0,9 ; 3,3]), non plus que les trois membranes sombres de la proue.

Une contrainte du kit doit cependant être connue : **l'enveloppe** (bounding box) doit être centrée
sur le pivot à ±2 cm. Les deux pointes d'épines extrêmes sont donc à x = ±3,51 m — l'enveloppe est
équilibrée, mais la silhouette ne l'est pas (les deux épines qui atteignent ces extrêmes n'ont ni
la même longueur, ni le même angle, ni la même section). L'asymétrie est intégralement conservée à
l'intérieur de l'enveloppe.

**Épines segmentées, veinées.** Chaque bras est une section elliptique aplatie (rz = 0,58–0,66 × rx,
pour rester sous le plafond de hauteur) balayée le long d'une Bézier quadratique. Le rayon repart en
avant à chaque vertèbre : chaque segment recouvre le suivant comme une écaille, et l'anneau de
jonction — le plus étroit — est émissif. Les veines de magenta de la planche sont donc, elles aussi,
de la géométrie. Griffes en ivoire froid (`AA_Trim`).

**Les 7 matériaux normalisés sont tous portés.** `AA_Trim` (ivoire froid) est le matériau dominant
des carapaces — c'est le « Pale » du Pale Leviathan. `AA_Glass` : trois membranes sombres non
appairées sur la proue. `AA_Marking_Red` (vert maladif côté Chœur Nul) : cinq nodules à la racine des
bras, **usage très limité** comme l'impose la charte §3.

## Limites connues

1. **Le kit ne sait exporter qu'un seul maillage — contournement en place, évolution demandée.**
   `ak.export_hull(hull, attach_points, …)` n'applique la correction d'axe qu'à l'objet passé en
   `hull` (`hull.data.transform(_AXIS_FIX)`) ; les autres objets de la liste sont traités comme des
   Empties (seule leur `location` est tournée). Or le brief impose six maillages nommés, puisqu'en
   glTF un objet = un nœud = un nœud Godot, et que les quatre phases doivent manipuler les pièces.
   Le kit étant gelé (trois autres agents l'utilisent en parallèle), je ne l'ai **pas** modifié.
   Contournement, documenté en tête du script :
   - `Body` est passé comme `hull`, et il est conçu pour porter **à lui seul** l'étendue
     longitudinale totale (proue à y = −4,385, dard à y = +4,385) — car `export_hull()` compare le Y
     d'auteur du seul `hull` au Z du `.glb` complet ; toute autre pièce qui dépasserait ferait
     échouer le contrat d'orientation ;
   - les cinq autres maillages reçoivent explicitement la même correction d'axe, en réutilisant la
     matrice du kit (`ak._AXIS_FIX`, accès en lecture seule) plutôt qu'une copie locale qui pourrait
     dériver, puis sont passés dans la liste `attach_points`, que l'exporteur se contente de
     sélectionner. Leur `location` valant (0, 0, 0), la rotation que le kit leur applique est un
     no-op, et la validation d'orientation les ignore (ce sont des nœuds à maillage).

   **Évolution demandée** (à décider par le concepteur, hors de mon périmètre) :
   `export_hull(parts: list[bpy.types.Object], attach_points, filepath, contract)` — appliquer
   `_AXIS_FIX` à chaque maillage, et calculer `author_y` sur l'union des pièces au lieu du seul
   `hull`. Cela supprimerait à la fois l'accès à un symbole privé et la contrainte artificielle qui
   force `Body` à être la pièce la plus longue. Tant que ce n'est pas fait, **ne pas déplacer la
   pointe de proue ni celle du dard** sans revérifier que rien d'autre ne les dépasse en Y.

2. **Le pivot centré impose un noyau au milieu de la longueur.** Le brief exige « pivot centré sur le
   noyau » et l'ADR-0008 exige une bbox centrée sur le pivot : le noyau est donc à mi-longueur, et le
   corps s'étend autant vers l'avant (bec blindé) que vers l'arrière (dard). La planche suggérait une
   masse plus ramassée vers l'avant ; c'est le seul écart notable à la référence, et il est imposé
   par le contrat, pas choisi.

3. **Interpénétrations volontaires.** Le noyau traverse le corps (il dépasse de 0,5 m au-dessus et
   0,63 m en dessous), les tuiles se chevauchent, les épines plongent dans la coque. Aucun booléen
   n'est calculé : c'est sans conséquence en rendu, et cela économise beaucoup de géométrie. Le
   collier de plaques masque la ligne d'intersection noyau/corps.

4. **Le noyau n'est pas biseauté** (`bevel_sharp_edges` sauté sur `Core`, lissage seul) : chanfreiner
   ses ~200 écailles de croûte coûtait plus de 4 000 triangles pour un gain nul sur une sphère
   émissive.

5. **Vu de face** (nez vers le joueur), la coque est très plate et le noyau déborde sous la coque.
   C'est le prix du plafond de hauteur (2,50 m) et de la lisibilité en vue de dessus ; à ~20° de la
   verticale, la caméra de jeu ne voit jamais cet angle.

6. Contrôle visuel fait par rendus **Cycles CPU** hors dépôt (WSL sans GPU : EEVEE rend noir en
   headless, cf. ADR-0002). Le rendu final sous Godot/Forward+ n'a pas été vérifié — c'est l'étape
   d'intégration de la session principale.

## Suggestions (hors périmètre de ce brief)

- **Phases** : `Shell_Crescent` peut s'ouvrir/pivoter autour de `Core_Center` pour exposer le noyau
  (phase 3), et les `Spike_0x` peuvent être détruits un à un (phase 2) — les pivots des épines sont à
  l'origine du modèle, une rotation autour de `Core_Center` les fait balayer proprement.
- Le noyau étant un objet à part, un `emission_energy` animé sur son matériau suffit à le faire
  **respirer** sans toucher au mesh ; un second matériau plus sombre en phase 4 (noyau « fermé »,
  gros plan de la planche) est faisable par override côté Godot.
- Il reste **8 100 triangles** de budget : de quoi ajouter des crocs internes au collier ou une
  seconde rangée d'écailles sur le dard, si le boss paraît trop sobre en plan rapproché.
