# BRIEF-0031 — Specter-9 : passe de détail (sortir du « jouet »)

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-07-20

## Objectif

Retravailler `tools/blender/build_specter_9.py` pour que la coque cesse de lire comme un **jouet en
plastique moulé** : densifier le détail de surface, épaissir le volume, et déplier les UV.

**Ce n'est pas une refonte de silhouette.** La forme générale, les proportions X/Z et l'identité du
vaisseau ne changent pas. Ce qui change, c'est la densité de surface et l'épaisseur.

## Contexte

La coque actuelle est conforme à son contrat et fait néanmoins « trop jouet ». Le diagnostic est
chiffré, pas subjectif :

| Symptôme | Mesure actuelle |
|---|---|
| Fuselage à peine subdivisé | 32 stations × 15 abscisses ≈ **1 860 tris** pour toute la coque |
| Panneaux bleus « peints » plutôt que découpés | **496 tris** de `AA_Panel` sur tout le vaisseau |
| Vaisseau trop plat | **0,4104 m** de haut ; le rapport BRIEF-0021 §8.3 dit déjà « *la planche montre un vaisseau plus épais* » |
| Presque aucun greeble sur un héros | **~12 boîtes** au total |
| Aucune ligne de panneau fine | signalé dès BRIEF-0021-report §8.6 |

**Lire d'abord** : `docs/decisions/ADR-0011-detail-des-coques-budgets-et-textures.md` (il amende les
budgets et autorise les textures), puis `ADR-0008` pour tout le reste, puis
`docs/forge/CHARTE_CREATIVE.md`.

**Référence de design — une seule** : `assets/reference/concepts/specter_9_concept_sheet.png`.
Regarde-la avec Read. Traits porteurs du détail : plaquage ivoire **découpé en dizaines de panneaux
irréguliers** aux rainures visibles, bandeaux bleu marine structurés, accents or aux bouts d'aile et
autour des tuyères, verrière sombre allongée **encadrée en relief**, tuyères cylindriques à **buse
profonde et anneaux concentriques**, bloc mécanique dorsal, petits bandeaux cyan.

⚠️ **Ne PAS utiliser `assets/reference/inspiration/specter_9_multi_angle_turnaround.png`.** Ce fichier
montre un appareil différent (aile pivotante, double dérive, livrée tricolore) dont la silhouette est
trop proche d'une licence tierce. Décision du propriétaire : la planche de concept fait foi.

## Contraintes

- **IP** : création originale. On transpose l'intention de la planche, on ne décalque aucune
  silhouette sous licence (ADR-0009).
- **Palette** : inchangée, les 7 matériaux normalisés du kit, `MATERIAL_ORDER` intact.
- **Dimensions X/Z : INCHANGÉES**, 1,75 × 2,46 m à ±3 %. C'est le contrat de gameplay — hitbox,
  télégraphes et lisibilité en dépendent. Ne pas y toucher.
- **Hauteur Y** : c'est **la** marge. Passer de 0,41 m à **0,50-0,55 m**. ADR-0008 vise Y ≈ 15-25 %
  de la longueur, soit 0,37-0,615 m : on va vers le haut de la fourchette, pas au-delà.
- **Budget triangles : 60 000** (ADR-0011, relevé depuis 15 000). Ce n'est pas un objectif à
  atteindre : c'est un plafond qui ne doit plus être la raison d'un renoncement.
- Déterministe, headless, Blender 4.5 LTS. **Deux exécutions doivent rendre un `.glb`
  byte-identique** — vérifie-le toi-même au `sha256sum`.

## Travail demandé, par ordre de rendement décroissant

1. **Épaissir.** `CROWN` (l. 117-132) et `BELLY` (l. 135-150) plafonnent à ±0,11 m. C'est le seul
   levier qui change la lecture de volume, et il était déjà recommandé par le rapport d'origine.
2. **Subdiviser la coque.** `section_x()` (l. 333-343) ne pose que 15 abscisses par section. Les
   doubler donne des faces exploitables pour les panneaux et les rainures.
3. **Panneaux à deux niveaux.** `inset_panel` n'est jamais imbriqué ici, alors que
   `build_crescent_interceptor.py:597-598` fait déjà un double inset emboîté. Technique déjà prouvée
   dans le dépôt, jamais appliquée au héros.
4. **Lignes de panneau.** Des rainures fines et nombreuses sur le plaquage, comme la planche.
   La géométrie s'en charge là où c'est possible ; le reste viendra de la texture (point 8).
5. **Greebles.** Passer d'une douzaine à plusieurs dizaines (`greeble_strip`), en les concentrant
   **là où on les voit**.
6. **Tuyères.** Buse plus profonde, anneaux concentriques.
   ⚠️ **Lèvre biseautée vers le DESSUS.** BRIEF-0026 démontre que l'émissif actuel est posé sur les
   faces arrière, **invisibles depuis la caméra de jeu inclinée à 20° de la verticale** : « *si une
   surface n'est pas visible depuis une caméra à 20°, ce qu'on y met n'existe pas* ». Le Specter-9
   est en outre désormais vu **en gros plan de trois quarts arrière sur l'écran d'accueil** — les
   tuyères comptent doublement.
7. **Verrière** : cadre en relief, pas un ovale sombre posé à plat.
8. **UV.** Appeler `ak.box_project_uv(ship, texels_per_meter)` avant l'export. Le kit vient
   d'acquérir cette primitive, ainsi que `add_lathe(axis=...)` si tu en as besoin. Choisis l'échelle
   au rendu : trop haute, le détail devient du bruit ; trop basse, les plaques deviennent énormes.
   Dis dans le rapport la valeur retenue et pourquoi.
9. **Biseau.** `bevel_sharp_edges` est à `segments=1`. Le passer à 2 coûtait 5 000 triangles et
   arrondissait les panneaux (l. 782-786) — avec 60 000 de budget c'est désormais envisageable,
   mais **à juger au rendu, pas au chiffre**. Si ça ramollit les panneaux, reste à 1 et dis-le.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/build_specter_9.py` | script retravaillé, toujours rejouable |
| `assets/imported/models/ships/specter_9.glb` | le mesh exporté (LFS) |
| `docs/forge/output/BRIEF-0031-report.md` | compte-rendu : mesures réelles, ce que le rendu montre, limites |

## Critères d'acceptation

- [ ] `blender45 -b -P tools/blender/build_specter_9.py` régénère sans erreur
- [ ] Deux exécutions successives : `.glb` **byte-identique** (`sha256sum`)
- [ ] Bbox X/Z **inchangée** à ±3 % (1,75 × 2,46) ; hauteur portée à **0,50-0,55 m**
- [ ] Le `.glb` contient `TEXCOORD_0` (UV présentes)
- [ ] ≤ 60 000 triangles
- [ ] Les 10 points d'attache existants sont **conservés** aux mêmes rôles
- [ ] **Rendu et regardé** : `blender45 -b -P tools/render-hull.py -- assets/imported/models/ships/specter_9.glb`.
      Critère explicite : sur les vues « jeu » et « dessus », on doit voir des **lignes de panneau et
      du relief** là où il n'y avait que du blanc lisse. Le compte-rendu dit ce que la planche montre.
- [ ] L'émissif des tuyères est visible **depuis le dessus**, pas seulement de l'arrière
- [ ] Provenance mise à jour (la ligne `specter_9_hull` existe déjà — la réécrire, pas en ajouter une)

## Hors périmètre

Ne pas toucher au code gameplay, aux `.tscn`, aux `.tres`, aux tests, ni aux autres coques.
Ne pas modifier `aegis_kit.py` (il vient d'être étendu ; si un manque apparaît, **le signaler dans le
compte-rendu** au lieu de le corriger en douce). Pas de `.blend` versionné. Ne pas changer la
silhouette générale ni les dimensions X/Z. Ne pas embarquer de texture dans le `.glb` — les feuilles
sont appliquées côté Godot, ce qui est traité ailleurs.
