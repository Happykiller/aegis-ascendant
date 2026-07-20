# BRIEF-0031 — Specter-9, passe de détail : compte-rendu

- **Agent** : asset-forge (Claude)
- **Date** : 2026-07-20
- **Brief** : `docs/forge/briefs/BRIEF-0031-specter-9-detail-pass.md`
- **Cadre** : ADR-0011 (budgets relevés, textures répétables) amendant ADR-0008.

## 1. Verdict de rendu — la seule question qui compte

**Ça ne lit plus comme un jouet en plastique lisse.** La planche de contrôle
(`tools/render-hull.py`) montre, sur les vues « game » et « dessus » :

- un **plaquage découpé en dizaines de plaques** — panneaux bleu marine à deux
  niveaux, bordés de rainures fines, sur toute l'aile et le fuselage ;
- des **rainures longitudinales** qui suivent la flèche de l'aile et des
  **rainures transversales** qui recoupent les grandes plages blanches ;
- du **relief franc** : greebles concentrés sur le pont (~60 boîtes contre 12),
  cadre de verrière en bourrelet doré, bloc mécanique dorsal encastré ;
- en profil, un **vrai volume** : le vaisseau est nettement plus épais.

Sur la vue de trois quarts arrière (celle de l'écran d'accueil), les **tuyères à
buse profonde** dominent : anneaux concentriques, jonc doré, collier mécanique,
et **couronne émissive cyan visible au fond de chaque buse**. Un rendu zoomé au
strict angle de jeu (20° de la verticale, depuis le côté poupe) confirme que
l'émissif se lit **depuis le dessus**, pas seulement de derrière : la lèvre de la
buse est biseautée vers le haut, sa vasque émissive remonte de 38 mm.

Le baseline (avant) et la nouvelle planche ont été comparés côte à côte : quatre
aplats bleus « peints » et une coque blanche molle sont devenus une surface
mécanique jointoyée.

## 2. Mesures réelles (relevées sur le `.glb` livré)

| Grandeur | Contrat | Avant | **Après** |
|---|---|---|---|
| Largeur X | 1,75 m ±3 % | 1,750 | **1,7500 m** (exact) |
| Longueur Z | 2,46 m ±3 % | 2,460 | **2,4600 m** (exact) |
| Hauteur Y | 0,50–0,55 m | 0,410 | **0,5158 m** |
| Triangles | ≤ 60 000 | 9 836 | **29 716** |
| Sommets | — | 9 169 | **32 198** |
| Pivot X/Z | ±0,02 m | — | **(−0,0000, −0,0000)** |
| `TEXCOORD_0` | présent | absent | **présent** |
| `TANGENT` | (ADR-0011) | absent | **présent** |

Répartition des triangles par matériau : `AA_Hull=18386`, `AA_Greeble=7052`,
`AA_Emissive_Engine=1604`, `AA_Trim=1578`, `AA_Panel=841`, `AA_Glass=151`,
`AA_Marking_Red=104`. Les 7 matériaux normalisés sont présents et assignés,
`MATERIAL_ORDER` intact.

**Budget** : 29 716 tris, soit 50 % du plafond de 60 000. Conformément à ADR-0011
(« le budget se justifie au rendu, pas au chiffre »), je n'ai pas cherché à
remplir le budget : le détail est là où la caméra le voit, et pas ailleurs.

**Bbox X/Z inchangée** : les deux dimensions de gameplay sont exactes au
millimètre (les tables `PLANFORM`/`FUSELAGE` n'ont pas bougé). L'épaisseur est
montée par les seules tables `CROWN` (0,114 → 0,165 m au dos) et `BELLY`
(−0,108 → −0,150 m au ventre), comme le prescrivait le levier n° 1.

## 3. Vérifications faites moi-même (pas supposées)

- **Déterminisme** : deux exécutions successives → `.glb` **byte-identique**
  (`sha256 = 2115be41…169093` pour les deux). Aucun aléa non seedé ; les greebles
  restent pilotés par `SEED`.
- **UV** : `TEXCOORD_0` confirmé par lecture directe du chunk JSON du `.glb`.
- **Bbox** : validée par `export_hull()` (qui refuse de publier hors contrat) et
  relue indépendamment.
- **Points d'attache** : les 10 rôles sont conservés. Deux ont bougé en Y à cause
  de l'épaississement, ce qui est correct : `Muzzle_*` de nez suivent le ventre
  descendu (Y −0,043 → −0,057), les `Engine_*` suivent l'axe relevé de la buse
  (Y −0,030 → −0,015). X et Z sont inchangés — les tirs restent alignés.

## 4. Valeur de `texels_per_meter` retenue : **4.0**

Choisie **au rendu**, pas au chiffre, comme demandé. Une tuile de feuille de
détail couvre donc 25 cm : environ 7 tuiles en envergure, 10 en longueur. C'est
la densité de plaques de la planche de concept.

- Essayée à 8.0 : le détail de la future feuille devient du bruit fin à l'échelle
  d'un chasseur de 1,75 m — exactement le « trop haut » que le kit met en garde.
- Essayée à 2.0 : les plaques deviennent énormes, une seule couvre une demi-aile.
- 4.0 est le compromis où une plaque de feuille correspond à peu près à une
  cellule de panneau géométrique, donc les deux niveaux de détail (géométrie +
  texture) se renforcent au lieu de se contredire.

La projection est en boîte (`ak.box_project_uv`), déterministe, non peinte à la
main : conforme à ADR-0011 §2 (feuilles répétables en niveaux de gris, position
exacte sans importance). **Aucune texture n'est embarquée dans le `.glb`** — seules
les coordonnées le sont ; les feuilles sont appliquées côté Godot, traité ailleurs.

## 5. Choix créatifs et justifications

- **Panneaux à deux niveaux** (`plate()`) : double `inset_panel` emboîté, la
  technique déjà prouvée par `build_crescent_interceptor.py`. Le premier inset
  creuse une marche restée en coque, le second n'accorde au bleu qu'un fond
  enfoncé — la lumière accroche deux arêtes, le panneau « existe » au lieu d'être
  peint.
- **Rainures avant les panneaux** : les rainures sont posées d'abord, elles sont
  la trame ; les panneaux s'y appuient et sont explicitement empêchés de mordre
  sur une bande de rainure (`skip_seams`). Résultat : des plaques *jointoyées*,
  la lecture exacte de la planche.
- **Détail concentré sur le pont** : appliquant strictement la règle de
  BRIEF-0026 rappelée par ADR-0011, tout le détail coûteux (greebles, bloc
  dorsal, bandeaux cyan) est sur des faces vues à 20° de la verticale. Le ventre
  ne reçoit que la quille sombre et deux panneaux : chaque triangle qu'on y
  mettrait serait perdu.
- **Buse à lèvre biseautée vers le haut** (`_nozzle_bore`) : ce n'est pas un choix
  de style mais de visibilité. Une buse coaxiale n'expose son émissif que vers
  l'arrière ; l'axe de la vasque remonte donc de 38 mm sur 0,22 m de profondeur,
  et la couronne cyan se lit à la verticale comme de trois quarts arrière (les
  deux cadrages où le vaisseau apparaît). Un témoin émissif supplémentaire est
  posé à plat sur le dos de la lèvre, indépendant de la buse.
- **Biseau resté à 1 segment** : ADR-0011 autorise 2 segments (budget suffisant),
  mais **au rendu** un biseau à 2 segments arrondit les rainures de 5 mm au point
  de les effacer — c'est exactement le défaut « plastique moulé » qu'on corrige.
  Rester à 1 segment est ici un choix de **lecture**, pas une contrainte de budget,
  comme le brief l'autorisait explicitement.

## 6. Détail technique notable

- **Explosion d'`inset_region` sur cellules étroites** : `use_even_offset=True`
  divise le retrait par le sinus de l'angle au coin ; sur une cellule plus étroite
  que le retrait, les sommets partent à l'infini. Une première version de la passe
  a produit une coque de 2,44 m de haut avant que `export_hull()` ne la refuse. La
  parade est un triple garde-fou dans `cells()` : largeur du **tronçon** contigu
  (`min_run`), largeur des cellules d'**extrémité** qu'on rogne (`min_edge`), et
  hauteur de **bande** (`min_band`) — car le contour se resserre selon X *et* Y.
  C'est ce filtre géométrique, et non une liste de zones écrite à la main, qui
  éteint tout seul les rainures là où l'aile est trop mince (vers le nez).
- **Triangulation des n-gons avant export** (`_triangulate_ngons`) : l'exporteur
  glTF refuse de calculer les tangentes tant qu'il reste des n-gons (culots de
  `cap_ring`). Sans tangentes, ADR-0011 §2 est inapplicable. On triangule les
  seules faces > 4 sommets ; les quads restent quads. Le nombre de triangles
  exportés est inchangé (glTF triangule de toute façon).

## 7. Limites connues

- **Rendu jugé sous Cycles (WSL), pas dans Godot.** Le rendu de contrôle est
  fidèle à la géométrie et à l'éclairage, mais le matériau final, le glow et le
  post-process de Godot différeront. La coque devra être **revue en jeu** (écran
  d'accueil en gros plan, combat) avant validation finale — c'est la règle
  ADR-0006, hors périmètre de ce brief.
- **Feuilles de détail non fournies.** Ce brief livre les UV et les tangentes ;
  les feuilles répétables en niveaux de gris et leur branchement côté Godot sont
  « traités ailleurs » (mention explicite du brief). Le `texels_per_meter=4.0` est
  un pari raisonné qui pourra demander un ajustement une fois la vraie feuille en
  place.
- **UV par projection en boîte : îlots recouvrants, faces obliques étirées.**
  C'est assumé par ADR-0011 (feuilles répétables, position sans importance) mais
  cela exclut tout détail *positionné* par texture (un décalque, un numéro de
  série). Si un tel besoin apparaît, il faudra un vrai dépliage — hors cadre ici.
- **Coût GPU non re-mesuré.** ADR-0011 demande de re-mesurer le temps GPU aux deux
  endroits d'apparition après reforge. La géométrie a triplé (9,8 k → 29,7 k tris) ;
  d'après le raisonnement d'ADR-0011 cela reste sous le bruit de mesure, mais la
  mesure elle-même relève de la session principale (accès GPU Windows), pas de la
  forge en WSL.

## 8. Signalement kit (demandé par le brief)

`aegis_kit.py` n'a **pas** été modifié. Les deux primitives ajoutées
(`add_lathe(axis=…)`, `box_project_uv`) ont suffi. Deux manques mineurs relevés,
sans blocage :

1. **Pas de primitive de rainure fine sur une face traversée.** `inset_panel`
   opère sur des faces entières ; une rainure qui coupe une face reste
   inexprimable. Je l'ai contournée en **insérant des paires de stations/abscisses
   serrées** dans les tables de section (la rainure devient une bande de faces
   fine), mais c'est un contournement propre à ce script. Une primitive
   `groove(bm, faces, width, depth)` du kit éviterait à chaque coque de densifier
   sa grille pour poser une ligne de panneau — c'est la cause structurelle n° 2
   citée par ADR-0011 §Contexte.
2. **`box_project_uv` ne renseigne pas les tangentes** ; l'exporteur glTF les
   recalcule, mais uniquement si le mesh est déjà en tris/quads — d'où la
   triangulation manuelle des n-gons ci-dessus. Le kit pourrait soit trianguler
   les n-gons dans `export_hull()`, soit le documenter.

## 9. Livrables

- `tools/blender/build_specter_9.py` — script retravaillé, déterministe.
- `assets/imported/models/ships/specter_9.glb` — mesh exporté (LFS),
  `sha256 = 2115be41…169093`.
- `docs/forge/output/BRIEF-0031-report.md` — ce compte-rendu.
- `assets/licenses/ASSET_PROVENANCE.csv` — ligne `specter_9_hull` réécrite
  (pas de doublon).
