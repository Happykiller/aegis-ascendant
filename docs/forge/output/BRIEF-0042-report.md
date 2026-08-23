# BRIEF-0042 — compte-rendu : coque 3D de la Choir Mine

- **Brief** : `docs/forge/briefs/BRIEF-0042-choir-mine-hull.md`
- **Exécuté par** : asset-forge
- **Date** : 2026-08-23
- **Lu avant production** : `docs/forge/CHARTE_CREATIVE.md`, le brief,
  `ADR-0008` (pipeline 3D), `ADR-0011` (budgets et textures), la planche
  `assets/reference/concepts/null_choir_enemy_families_sheet.png` (3ᵉ cellule),
  `tools/blender/lib/aegis_kit.py`, `tools/blender/build_needle_scout.py` (structure),
  `tools/blender/build_choir_harvester.py` (pièces articulées + harnais de dégagement),
  `scripts/enemies/enemy_pose.gd` (**la convention de rotation que le jeu applique réellement**),
  `.claude/resources/pratique-detail-en-fraction-de-corde.md` et `pratique-revue-asset.md`.

---

## 1. Livrables

| Fichier | Nature |
|---|---|
| `tools/blender/build_choir_mine.py` | le script de construction — il **est** la source de l'asset (ADR-0008) |
| `assets/imported/models/ships/choir_mine.glb` | le mesh (LFS ; `git check-attr` → `filter: lfs`) |
| `docs/forge/output/BRIEF-0042-report.md` | ce compte-rendu |
| `docs/forge/output/BRIEF-0042-planche-quatre-vues.png` | planche de recette au repos (`tools/render-hull.py`) |
| `docs/forge/output/BRIEF-0042-poses-segments-ouverts.png` | **preuve d'articulation** : 4 panneaux, segments déviés |

Trois lignes ajoutées à `assets/licenses/ASSET_PROVENANCE.csv` **en append shell** (`>>`), jamais par
réécriture : un autre brief de coque tournait en parallèle. Le CSV relu après coup a 171 lignes,
toutes à 11 colonnes.

`aegis_kit.py` est réutilisé **sans une seule modification**. Aucun `.gd`, `.tscn`, `.tres`, ni
`tools/blender/build_null_maw.py` n'a été touché.

---

## 2. Chiffres réels, relevés sur le `.glb` livré

| Mesure | Valeur | Contrat |
|---|---|---|
| Bounding box (Godot X × Y × Z) | **1,1500 × 0,5020 × 1,1500 m** | 1,15 ±3 % → écart **0,00 %** en X et en Z |
| Hauteur | **0,502 m** | fenêtre imposée 0,45–0,55 ✅ |
| Rapport hauteur/diamètre | **43,7 %** | dérogation assumée à ADR-0008 (« 15–25 % ») |
| Centre (pivot) | **(+0,0000 ; +0,0210 ; +0,0000)** | centré en X/Z à moins de 0,1 mm |
| Triangles | **5 632** | budget 6 000 → **94 % consommé**, 368 de marge |
| Sommets | 6 706 | — |
| Poids | 388 212 o | — |
| Matériaux | les **7** présents | `Greeble` 2 840 t · `Hull` 733 t · `Panel` 482 t · `Trim` 380 t · `Emissive` 976 t · `Marking` 93 t · `Glass` 128 t |
| Attributs de sommet | `POSITION`, `NORMAL`, **`TEXCOORD_0`**, **`TANGENT`** | UV **et** tangentes sur 7/7 maillages |
| Points d'attache | **`Muzzle_C` seul**, en (0,0000 ; +0,2000 ; 0,0000) | **aucun `Engine_C`** ✅ |
| Déterminisme | `./scripts/build-hull.sh --check choir_mine` → **déterminisme OK** | sha256 `b60d5e378f4efdbca419b31c47fffbaafd097dcd716b59901256644ad5f55e6a` |

Nœuds du `.glb` : `ChoirMine_Hull` + `Segment_01..06` + `Muzzle_C`, tous **racines**, tous à rotation
identité et sans échelle — rien de caché dans une transformation de nœud.

---

## 3. Débattement mécanique mesuré — la donnée demandée

Le script **remesure le débattement à chaque build**, sur le maillage réellement livré, avec
*exactement* la convention de `scripts/enemies/enemy_pose.gd` (origine sur la charnière, axe déduit
de la position du nœud `axis = (-r.z, 0, r.x)`, `Basis(axe, angle)`, **même angle pour les six**).
Il **refuse d'exporter** sous 45° (`TRAVEL_FLOOR_DEG`). Pas de simulation approchée : distance
BVH triangle-à-triangle dans les deux sens, plaque contre coque fixe **et** plaque contre voisines,
tous les degrés de 0 à 90.

| Pièce | Pivot (coordonnées **Godot**, mètres) | Limite avant auto-intersection | Ce qui bloque |
|---|---|---|---|
| `Segment_01` | (−0,2269 ; +0,1480 ; +0,1310) | **56°** | voisine `Segment_02` |
| `Segment_02` | ( 0,0000 ; +0,1480 ; +0,2620) | **56°** | voisine `Segment_03` |
| `Segment_03` | (+0,2269 ; +0,1480 ; +0,1310) | **56°** | voisine `Segment_04` |
| `Segment_04` | (+0,2269 ; +0,1480 ; −0,1310) | **56°** | voisine `Segment_05` |
| `Segment_05` | ( 0,0000 ; +0,1480 ; −0,2620) | **56°** | voisine `Segment_06` |
| `Segment_06` | (−0,2269 ; +0,1480 ; −0,1310) | **56°** | voisine `Segment_01` |

Les six sont géométriquement identiques à une rotation près : la limite est la même au dixième de
degré. Marge minimale, degré par degré (`Segment_01`, identique aux autres) :

| ouverture | 0° | 20° | 40° | **45°** | 48° | **50°** | 52° | 54° | 56° | 57° |
|---|---|---|---|---|---|---|---|---|---|---|
| marge | 10,1 mm | 11,4 | 12,9 | **12,9** | 12,9 | **11,2** | 7,7 | 4,2 | 0,7 | **0 (contact)** |
| obstacle | coque | coque | coque | coque | coque | voisine | voisine | voisine | voisine | voisine |

**Comment lire ce tableau.**

- De 0 à 48°, le minimum n'est pas un risque : c'est la **fente statique** de 10–13 mm entre le pied
  de plaque et le pont, qui ne se referme jamais (elle s'ouvre même légèrement quand la plaque se
  lève). Aucune limite là.
- À partir de 50°, ce sont les **voisines** qui se rejoignent : en se levant, une plaque garde son
  décalage tangentiel mais perd du rayon, donc son emprise **angulaire grossit**. C'est le vrai mur.
- **Débattement mécanique = 56°.** Premier contact à 57°.

**Réglage recommandé pour `EnemyData.open_angle_deg` : 45°** (12,9 mm de marge, soit 4 % du rayon de
la mine — de quoi encaisser une interpolation qui dépasse). **50° reste sain** (11,2 mm). **Ne pas
dépasser 52°** : au-delà, la marge tombe sous 8 mm et un simple *overshoot* d'easing fait se toucher
deux plaques. Le garde-fou `EnemyPose.MAX_OPEN_DEG = 85` ne protège de rien ici — il est 29° au-dessus
du réel.

> ⚠️ **Le harnais a servi, et immédiatement.** En grossissant la pointe asymétrique, je l'ai fait
> mordre la plaque qui la coiffe : débattement mesuré **−1°** (contact dès le repos), alors que la
> bounding box, le budget, les matériaux et le pivot restaient parfaits et que `export_hull()`
> aurait publié sans un mot. Corrigé en abaissant la pointe de 5 cm. C'est exactement le défaut
> décrit dans `pratique-detail-en-fraction-de-corde.md` — sauf qu'il a été vu avant d'être livré.

---

## 4. Contrôle visuel (ADR-0006) — ce que les planches montrent réellement

### 4.1 Planche de repos, `BRIEF-0042-planche-quatre-vues.png`

Ce que je vois, panneau par panneau :

- **Vue « jeu » (20° de la verticale)** : un **galet blindé hexagonal**. Six grandes plaques violettes
  bombées en couronne, un cœur magenta plein et brillant au centre, six veines magenta rayonnant du
  cœur vers la périphérie, une couronne de blocs et de fûts sombres qui **dépasse tout autour** de la
  carapace, deux caissons vert maladif et deux caissons ivoire en périphérie (sept fûts anthracite pour le reste), et **une pointe claire
  unique à 12 h**, qui saillit d'un secteur volontairement en retrait.
- **Vue de dessus** : même lecture, symétrie d'ordre 6 franche, cassée par la pointe et par
  l'irrégularité des modules (deux fûts grêles encadrent la pointe).
- **Vue de profil** : **c'est le panneau qui décide**. On voit un galet épais à ventre noir bombé,
  des modules greffés sur l'équateur, un pont en gradins et le cœur qui dépasse à peine. La pointe
  saillit sur le côté, à hauteur d'équateur. **Aucun fuselage, aucune aile, aucune tuyère** : rien
  qui ressemble à une cellule de vol.
- **Vue trois-quarts** : le volume se lit comme une **mine posée** ; les plaques forment un dôme
  segmenté, le noyau en tambour à gradins concentriques émerge en son centre.

**La question qui décide — se lit-elle comme un objet et non comme un vaisseau, à petite taille ?**
Vérifiée, pas supposée : la vue « jeu » a été réduite à **46 px** (taille réelle en jeu : 1,15 unité
sur un plan large de 24, rendu 960 px) puis à **30 px**. À 46 px, la mine est une **rondelle sombre
avec une pastille brillante au centre et un bord bosselé** ; à 30 px, une pastille brillante cerclée
de sombre. **Aucune direction de marche n'apparaît à aucune taille** : pas de nez, pas de traînée,
pas d'axe long. Réponse : **oui, ça lit comme un objet.** C'est le seul point sur lequel je n'ai
aucune réserve.

**Ce que la planche montre aussi et qu'il faut savoir** : le magenta rend **rose pastel** en studio.
Ce n'est pas une dérive de palette — le matériau est bien `#D93D9C` à `emission_strength = 2.5`, réglé
par le kit et partagé avec les cinq autres coques ; c'est le rendu Cycles sans bloom qui délave un
émissif. `pratique-revue-asset.md` prévient que le studio flatte et que **c'est en jeu que ça se
juge** : je ne peux pas exporter vers Windows depuis la forge, donc **cette vérification-là reste
à faire côté session principale**, avec le post-process rétro.

### 4.2 Planche d'ouverture, `BRIEF-0042-poses-segments-ouverts.png`

Quatre panneaux : repos 0° (vue jeu), **45°** (vue jeu, réglage recommandé), **56°** (dessus, limite
mesurée), **56°** (trois-quarts). Poses écrites avec la convention de `enemy_pose.gd`, et en écrivant
`rotation_quaternion` — l'importeur glTF pose `rotation_mode = 'QUATERNION'` et un `rotation_euler`
serait **silencieusement ignoré** (piège relevé dans BRIEF-0040-report §3 ; j'ai écrit le quaternion
d'emblée pour ne pas rendre une pose de repos en croyant rendre une pose extrême).

Ce que ces panneaux montrent :

- les six plaques **pivotent bien sur leur bord intérieur** : elles se dressent en corolle, le bout
  monte et rentre légèrement, **elles ne tournent pas autour du centre du disque** ;
- **rien ne traverse rien** : ni une voisine, ni le tambour du noyau, ni le pont ;
- le **cœur magenta reste entièrement dégagé** aux quatre poses — c'est lui qui pulse, il ne doit
  jamais être masqué, et il ne l'est pas ;
- effet de bord utile au gameplay : en s'ouvrant, la mine **s'assombrit** (on voit le dessous
  anthracite des plaques et le pont) pendant que le cœur reste brillant. Le télégraphe se lit donc
  en contraste, pas seulement en silhouette.

---

## 5. Répartition des matériaux — mesurée, et mesurée là où ça compte

`inspect_glb.py` donne l'aire **totale** ; sur un galet, plus de la moitié de cette aire est un ventre
et des flancs que la caméra de jeu ne voit **jamais**. J'ai donc mesuré les deux (la seconde colonne
compte les seules faces dont la normale monte à moins de 70° de la verticale, c'est-à-dire ce que
voit la caméra du jeu) :

| Matériau | aire totale (4,47 m²) | **aire vue par la caméra (1,73 m², soit 39 %)** |
|---|---|---|
| `AA_Greeble` | 45,5 % | **37,7 %** |
| `AA_Hull` | 26,0 % | **30,1 %** |
| `AA_Panel` | 13,7 % | **18,4 %** |
| `AA_Emissive_Engine` | 3,9 % | **7,0 %** |
| `AA_Trim` | 6,7 % | **5,3 %** |
| `AA_Glass` | 0,6 % | 1,3 % |
| `AA_Marking_Red` (vert maladif) | 3,6 % | **0,2 %** |

Trois lectures :

1. **Émissif à 7,0 % de ce que le joueur voit** (3,9 % de la coque entière) : sous la barre des ~10 %
   au-delà de laquelle « ce n'est plus un accent, c'est une livrée ». Et il est **concentré** : un
   cœur de 216 mm de diamètre + six veines fines + un filet de gorge, pas un saupoudrage.
2. **Carapace 53,8 % contre machinerie 37,7 % sur les surfaces vues.** L'inverse (le défaut relevé sur
   le Pale Leviathan : trois fois plus de greeble que de blindage) aurait fait lire une machine
   ouverte au lieu d'un objet blindé. Le greeble qui reste est là où il doit être : le ventre, les
   fûts de la couronne, les tranches et le dessous des plaques.
3. **Vert maladif à 0,2 % du visible** : la charte dit « usage très limité », c'est tenu — deux
   caissons, vus surtout de flanc.

---

## 6. Choix créatifs, et ce qui les impose

**L'épaisseur est l'argument principal.** 0,502 m pour 1,15 m de diamètre (43,7 %). C'est la
dérogation demandée par le brief, et c'est elle qui fait le travail : vu de dessus, un chasseur est
une flèche fine, une mine est un galet. Aucun autre choix n'aurait suffi à lui seul.

**Le noyau a été refait après le premier rendu.** Version 1 : anneau magenta large + pupille
minuscule au fond d'une lentille sombre. Réduite à 46 px, la mine lisait comme un **donut** — et
c'était *l'anneau* qui pulsait, pas le cœur. Version 2 : anneaux fins (violet, magenta, ivoire) et
**dôme magenta plein de 216 mm** au centre. Ce que le jeu fait respirer doit être la tache la plus
brillante **et la plus compacte** de l'objet.

**Les plaques sont des pétales, pas des parts de tarte.** Une plaque à largeur *angulaire* constante
se heurte à sa voisine dès ~40° d'ouverture (en se levant elle perd du rayon, donc son emprise
angulaire grossit). En donnant à la plaque une **largeur tangentielle** qui culmine à mi-corde et
retombe au bout, on gagne ~16° de débattement pour la même silhouette. C'est ce qui fait tenir les
56° mesurés.

**Le détail est là où la caméra regarde** : gradins concentriques du noyau, dos bombé des plaques
avec deux panneaux enfoncés (liston anthracite de 16 mm entre eux), couture magenta sur la crête,
veines de pont dans les six fentes, dos des fûts avec panneau enfoncé. Les flancs verticaux ne
portent **que** du matériau. Zéro texture : tout est géométrie (ADR-0011).

**Les six fentes tombent à 0°, 60°, 120°…, c'est-à-dire pile sur un module** de la couronne : la
veine magenta relie le cœur à un module. Le disque lit comme un **circuit**, pas comme une denture.

**L'asymétrie ne tient pas qu'à la pointe.** La pointe (unique, sur `-Y`, donc pointée vers le joueur)
est la rupture majeure exigée ; elle est appuyée par un secteur en retrait (ses deux voisins reculent
de 12 % et sont deux fois plus grêles), par une répartition inégale des types de modules, par deux
plaques à lèvre ivoire non diamétralement opposées, et par trois plaques dont le panneau extérieur
reste anthracite. Sans ce dernier point, six dos violets faisaient un aplat clair continu et la mine
rendait plus lumineuse que sa planche.

**Ce que je n'ai pas fait** : aucun `Engine_C` (le brief l'interdit et une tuyère allumée la ferait
lire comme un vaisseau en approche) ; aucun greeble semé (à 46 px c'est du bruit qui coûte des
triangles) ; aucune texture peinte.

---

## 7. Limites connues et points d'attention pour l'intégration

1. **`Muzzle_C` est à `Y = +0,200 m`, au cœur du noyau — donc 20 cm au-dessus du plan de jeu.**
   Le brief demande « au centre du noyau, sur l'axe » : c'est ce qui est livré, et c'est cohérent
   avec l'idée que la couronne jaillit du cœur. Mais si la salve doit vivre **dans le plan de jeu**
   (comme tous les autres projectiles), le contrôleur doit n'en prendre que X/Z, ou retirer 0,20 m
   en Y. Le dire ici plutôt que de le laisser découvrir à l'écran.
2. **Marge de budget mince : 368 triangles** (94 % de 6 000 consommés). Tout ajout de détail
   ultérieur impose de reprendre ailleurs. Le plafond de classe d'ADR-0011 (12 000) laisserait, lui,
   toute la place — c'est le brief qui a serré à 6 000, à raison pour une unité instanciée en champ.
3. **Les six plaques sont géométriquement identiques.** L'ouverture est donc parfaitement synchrone
   et symétrique. Si le télégraphe gagne à être désynchronisé (plaques décalées de quelques
   millisecondes), c'est faisable côté jeu **sans toucher au mesh** — mais `EnemyPose.pose()` écrit
   aujourd'hui le même angle pour toutes.
4. **Jugé en studio seulement.** La forge ne peut pas exporter vers Windows. La lecture du magenta
   sous `retro_post` + scanlines et le contraste réel de la mine sur le fond du jeu restent à vérifier
   côté session principale (`pratique-revue-asset.md`).
5. **La pointe est coiffée par `Segment_05`** : elle sort du secteur `-Y`, sous la plaque qui s'ouvre.
   Elle est fixe (elle appartient à la coque), donc elle ne bouge pas pendant le télégraphe — c'est
   voulu, mais si un jour la pointe doit s'animer, il faudra en faire une pièce mobile et refaire la
   mesure de dégagement.
6. Le rapport hauteur/longueur de 43,7 % **doit être recensé dans ADR-0008** comme une exception
   motivée, faute de quoi la prochaine coque héritera d'une règle qui a l'air contredite.

---

## 8. Kit partagé : rien changé, et deux manques signalés

`aegis_kit.py` est utilisé **tel quel** (`MATERIAL_ORDER` intact, palette intacte, `attach_pair`
disponible mais inutile ici — aucune paire bâbord/tribord sur un objet radial). Trois choses ont dû
être écrites **localement** dans le script de coque, et elles sont candidates au kit si un troisième
script les redemande — je les signale au lieu de les glisser dans le kit :

1. **`_sweep()`** — balayage d'un profil fermé le long de stations orientées (centre, demi-vecteur
   transversal, demi-vecteur vertical). Le kit n'a que `add_box` (aligné sur les axes) et `add_lathe`
   (autour de X/Y/Z) : aucune primitive ne sait poser une boîte ou un fût **orienté sur un rayon**.
   Les 11 modules de la couronne, la pointe, les veines et les coutures sortent tous de là. C'est
   exactement le même besoin que les `seg_box`/`limb` réécrits dans le Harvester et le Leviathan —
   le troisième script à le réimplémenter, donc le bon moment pour le remonter.
2. **`_triangulate_ngons()`** — sans lui, l'exporteur **abandonne silencieusement les tangentes**
   (`Tangent space can only be computed for tris/quads`) parce que les `cap_ring` produisent des
   n-gons. Résultat mesuré : `UV+tangentes sur 0/7 maillages` avant, **7/7** après, et **le nombre de
   triangles exportés est inchangé** (l'exporteur triangulait déjà, mais après le calcul des
   tangentes). Le Needle Scout livré est dans ce cas (`0/1`). Ce contrôle a sa place dans
   `export_hull()`, ou au moins un avertissement bruyant.
3. **`add_lathe` ne sait pas fermer sa dernière boucle** : il n'expose ni ses anneaux ni une option
   de capuchon. Contournement utilisé : un point de rayon nul en fin de contour (un faux pôle). Un
   paramètre `cap_last` coûterait trois lignes.

---

## 9. Critères d'acceptation du brief

| Critère | Verdict |
|---|---|
| `blender45 -b -P tools/blender/build_choir_mine.py` régénère sans erreur | ✅ |
| Bbox 1,15 × 1,15 (±3 %), hauteur 0,45–0,55, chiffres au rapport | ✅ 1,1500 × 1,1500 ; **0,502 m** |
| ≤ 6 000 triangles | ✅ **5 632** |
| Deux exécutions byte-identiques (`--check`) | ✅ `déterminisme OK`, sha256 `b60d5e37…` |
| Palette Chœur Nul ; émissif magenta visible de dessus ; répartition mesurée | ✅ 7,0 % de l'aire vue ; répartition §5 |
| `Muzzle_C` au centre du noyau ; aucun `Engine_C` | ✅ (réserve §7.1 sur son Y) |
| Six `Segment_NN` mobiles, pivots au bord intérieur, débattement mesuré | ✅ **56°**, tableau §3 |
| Rendu et regardé ; la mine lit-elle comme un objet à petite taille ? | ✅ vérifié à 46 px et 30 px — §4.1 |
| Planche supplémentaire segments ouverts | ✅ `BRIEF-0042-poses-segments-ouverts.png` |
| Kit réutilisé sans modification | ✅ (manques signalés §8, non appliqués) |
| Provenance renseignée | ✅ 3 lignes, ajoutées en `>>` |
