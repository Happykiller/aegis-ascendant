# BRIEF-0029 — Coque 3D du Crescent Interceptor

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-07-20

## Objectif

Modéliser le **Crescent Interceptor**, deuxième silhouette d'ennemi du Chœur Nul, en `.glb` PBR,
avec le kit hard-surface partagé.

## Contexte

Le bestiaire compte huit ennemis qui partagent **tous la coque `needle_scout.glb`** : la variété est
aujourd'hui 100 % comportementale, zéro variété visuelle. Cette coque est donc la **deuxième
silhouette du jeu**, et la première occasion de montrer que le Chœur Nul aligne plus d'une machine.
Elle doit se distinguer du Needle Scout **d'un coup d'œil, à petite taille** — c'est le seul critère
qui compte.

**Lire d'abord** : `docs/decisions/ADR-0008-pipeline-3d-blender.md` (conventions normatives),
`docs/forge/CHARTE_CREATIVE.md`, puis `tools/blender/lib/aegis_kit.py` — **le kit existe, le
réutiliser sans le modifier**. Prendre `tools/blender/build_needle_scout.py` comme modèle de
structure (même classe d'unité, même budget, mêmes attaches).

Référence de design : **`assets/source/references/reference_asset_overview_board.png`**, panneau
`ENNEMIS`, **rangée du haut, deuxième vignette** (« CRESCENT INTERCEPTOR »). Regarde-la avec Read.

Traits à respecter :

- **fuselage central étroit**, verrière/capteur visible sur l'axe ;
- **deux longerons latéraux** portant chacun une **lame d'aile en croissant** orientée vers l'avant —
  c'est LA signature, et ce qui l'oppose au dard mono-bloc du Needle Scout ;
- **deux tuyères** en bout de longeron ;
- carapace segmentée, panneaux d'accent sur les longerons.

⚠️ **Transposition, pas décalque.** Sur la planche de référence, les ennemis sont gris/argent à
réacteurs bleus. Ce n'est **pas** la palette du jeu : appliquer la palette antagoniste Chœur Nul
(ci-dessous). On reprend la *silhouette et l'intention*, jamais le coloris ni un détail identifiable
(ADR-0009).

## Contraintes

- **IP** : design original, aucun élément identifiable d'une licence existante.
- **Palette** : palette **antagoniste « Chœur Nul »** de la charte §3 — anthracite `#24252B`,
  violet sombre `#452663`, ivoire froid `#DDDCD2`, magenta `#D93D9C` en émissif. Matériaux
  normalisés du kit, `MATERIAL_ORDER` inchangé.
- **Techniques** :
  - Dimensions monde : **1,10 m (X) × 1,60 m (Z)**, ±3 %. Hauteur Y ≤ 0,28 m.
    Volontairement **plus large et plus court** que le Needle Scout (0,65 × 1,90) : c'est ce
    contraste de proportions qui rend les deux ennemis distinguables à petite taille.
  - Orientation d'auteur : **nez vers -Y, dessus vers +Z** dans Blender, comme toutes les unités.
    Que l'ennemi descende à l'écran est une rotation faite en jeu, **pas** dans le mesh.
  - Pivot à l'origine, centré.
  - Budget : **≤ 3 000 triangles** — même budget « ennemi léger » que le Needle Scout (qui n'en
    consomme que 1 612). Il est instancié en masse : ne pas le dépasser « juste un peu ».
  - Ne jamais écrire un signe de X à la main pour les paires : **bâbord est `+X`** en repère
    d'auteur — utiliser `attach_pair()`.
  - Déterministe, headless, Blender 4.5 LTS.

### Où mettre le détail (contrainte de lisibilité, pas de goût)

La caméra de jeu est à **20° de la verticale** : on voit ces coques quasiment **de dessus**.
Vérifié en rendant le Needle Scout avec `tools/render-hull.py` — les vues « jeu » et « dessus » y
sont presque indiscernables.

Conséquence : **tout le détail doit vivre sur les surfaces supérieures** (découpes de panneaux,
greebles, ligne d'énergie). Ce qui est posé sur les flancs verticaux n'existe pas pour le joueur.
C'est exactement le défaut relevé sur le Specter-9, qui dépense son émissif sur les faces arrière
de ses tuyères (BRIEF-0026). Ne pas le reproduire.

Le détail vient de la **géométrie** — `bevel_sharp_edges`, `inset_panel`, `greeble_strip`,
`add_lathe` — **jamais de textures** (ADR-0008 : aucune texture map, PBR par facteurs).

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/build_crescent_interceptor.py` | script de construction, rejouable |
| `assets/imported/models/ships/crescent_interceptor.glb` | le mesh exporté (LFS) |
| `docs/forge/output/BRIEF-0029-report.md` | compte-rendu : mesures réelles, limites |

## Points d'attache requis

- `Muzzle_C` — bouche de tir unique, sur l'axe, à la pointe du fuselage.
- `Engine_C` — **obligatoire** : `EnemyController` y accroche la traînée de propulsion et
  `push_error` s'il manque. Avec deux tuyères, le placer **sur l'axe, au niveau du plan de sortie
  des tuyères**, là où les deux plumes se rejoignent visuellement.
- `Engine_L` / `Engine_R` — en bout de chaque longeron, via `attach_pair()`. Non consommés
  aujourd'hui (le contrôleur n'allume qu'une traînée centrale), posés pour une double traînée
  ultérieure sans avoir à re-modéliser.

## Provenance

Une ligne dans `assets/licenses/ASSET_PROVENANCE.csv` (append shell) : `asset_type=model3d`,
`source_tool=asset-forge (Blender 4.5.11, script)`, `license=proprietary-internal`,
`prompt_file=docs/forge/briefs/BRIEF-0029-crescent-interceptor-hull.md`. Le champ `notes` porte le
rapport de contrat condensé, sur le modèle de la ligne `needle_scout_hull` : triangles/budget, bbox
réelle, sommets, matériaux, liste des points d'attache avec coordonnées Godot, déterminisme,
affirmation d'originalité.

## Critères d'acceptation

- [ ] `blender45 -b -P tools/blender/build_crescent_interceptor.py` régénère le `.glb` sans erreur
- [ ] Bounding box 1,10 × 1,60 m (±3 %), hauteur ≤ 0,28 m — chiffres réels dans le compte-rendu
- [ ] ≤ 3 000 triangles
- [ ] Deux exécutions successives produisent un `.glb` **byte-identique** (`sha256sum`) — le
      déterminisme est une exigence d'ADR-0008, pas un bonus
- [ ] Palette Chœur Nul, émissif magenta présent **et visible depuis le dessus**
- [ ] `Muzzle_C`, `Engine_C`, `Engine_L`, `Engine_R` correctement placés
- [ ] **Rendu et regardé** : `blender45 -b -P tools/render-hull.py -- assets/imported/models/ships/crescent_interceptor.glb`,
      et le compte-rendu dit ce que la planche montre. Un livrable non rendu n'est pas un livrable
      (ADR-0006). Dire notamment si le croissant se lit encore sur la vue « jeu ».
- [ ] La silhouette se distingue du Needle Scout sur la vue de dessus, à petite taille
- [ ] Le kit partagé est **réutilisé sans modification** (si une évolution du kit est vraiment
      nécessaire, la signaler dans le compte-rendu au lieu de la faire en douce)
- [ ] Provenance renseignée

## Hors périmètre

Ne pas toucher au code gameplay, aux `.tscn`, aux `.tres`, aux tests, ni aux autres coques. Pas de
textures, pas de LOD, pas d'animation, pas de `.blend` versionné. La trajectoire, la Resource de
données et l'intégration en vague sont déjà traitées côté session principale : **ne rien en faire**.
