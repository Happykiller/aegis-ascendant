# BRIEF-0032 — Aegis Citadel : reforge complète (le joyau de la couronne)

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-07-21

## Objectif

Faire de l'Aegis Citadel la **pièce maîtresse visuelle** du jeu : densifier massivement la coque,
**déplier ses UV** (elle n'en a aucune), et **sortir du maillage les pièces destinées à bouger** —
tourelles et balises deviennent des modèles à part, animés côté Godot.

**Ce n'est pas une refonte de silhouette.** Les trois masses — corps central prismatique, deux
bras-batteries, noyau cyan surdimensionné — ne changent pas, et les dimensions X/Z non plus. Ce qui
change, c'est la **densité de surface**, le **nombre de pièces lisibles** et la **texturabilité**.

## Contexte

La citadelle est conforme à son contrat et reste le figurant du jeu. Diagnostic chiffré :

| Symptôme | Mesure |
|---|---|
| **Aucune texture n'est possible** | le `.glb` n'a que `POSITION` + `NORMAL` — ni `TEXCOORD_0` ni `TANGENT` |
| Seule coque exclue du détail | `scripts/ui/title_stage.gd:105-107` : « *la citadelle n'est pas encore reforgée et n'en a pas* » |
| Budget inexploité | **21 028 triangles sur 120 000** autorisés (ADR-0011) — 82 % de marge |
| Rien ne peut bouger | tout est soudé par `ak.join_objects()` en un maillage unique |
| Le noyau lit comme une goutte blanche | l'émissif ne reçoit pas la lumière : ses facettes n'existent que par la géométrie (le script le documente déjà, l. 549-556) |
| Trois canons par bras | la planche en montre **quatre**, en deux paires superposées |

**Lire d'abord** : `docs/decisions/ADR-0013-textures-deverrouillees.md` (il lève les interdits de
texture et fixe la méthode), puis `ADR-0011` (budgets), puis `ADR-0008` pour tout le reste, puis
`docs/forge/CHARTE_CREATIVE.md`.

**Référence de design — une seule** : `assets/reference/concepts/aegis_citadel_concept_sheet.png`.
**Regarde-la avec `Read`**, elle porte tout le brief. Traits que le modèle actuel n'honore pas :
plaquage ivoire **découpé en dizaines de plaques irrégulières** aux joints visibles, liserés or le
long des arêtes de panneau, **quatre canons longs par bras** avec colliers et culasses greebées,
tourelles **dômées à lentille cyan annulaire** et double tube, **trois balises flottantes** tenues
dans un champ hexagonal, baie d'appontage à **gorge profonde** et chevrons cyan, cristal **facetté à
arêtes vives** dans un cadre technique or et anthracite.

## Contraintes

- **IP** : création originale. On transpose l'intention de la planche (ADR-0009).
- **Dimensions X/Z : INCHANGÉES**, **19,60 × 16,60 m à ±3 %**. Contrat de gameplay — hitbox,
  télégraphes et lisibilité en dépendent. Ne pas y toucher.
- **Hauteur Y** : plafond **5,60 m** (relevé par ADR-0011 ; l'ancien contrat dit encore 5,00 — le
  corriger). Mesure actuelle : 4,88 m. Il y a de la marge, elle n'est pas obligatoire.
- **Budget triangles : 120 000** — un plafond, pas un objectif. Cible raisonnable : **70 à 90 k**.
- **Palette** : les 7 matériaux normalisés, `MATERIAL_ORDER` intact, aucune couleur nouvelle.
- Déterministe, headless, Blender 4.5 LTS. **Deux exécutions doivent rendre un `.glb`
  byte-identique** — vérifie-le toi-même au `sha256sum`.
- **Ne pas embarquer de texture dans le `.glb`.** Les cartes sont appliquées côté Godot.

## Travail demandé, par ordre de rendement décroissant

### 1. Déplier les UV — à faire EN PREMIER

`ak.box_project_uv(citadel, TEXELS_PER_METER)` avant `export_hull()`, comme
`build_specter_9.py:1290`. **Sans ça, rien du reste de la chaîne texture n'existe.**

⚠️ **L'échelle est le piège.** Le Specter-9 est à **4 tuiles/m** — calé sur un chasseur de 2 m. La
citadelle en fait **19,6** : à la même densité, la feuille lit comme du bruit rayé. Vise une tuile
qui couvre **8 à 10 m de coque**, soit `TEXELS_PER_METER ≈ 0,10-0,12`. Dis la valeur retenue et
pourquoi dans le compte-rendu.

### 2. Sortir les pièces mobiles

- **`build_turrets()` disparaît de l'assemblage.** Les six tourelles deviennent
  `build_citadel_turret.py`, un modèle indépendant. Les marqueurs `Turret_01..06` restent et servent
  de points d'ancrage — **leur position et leur nom ne changent pas** (le code Godot les lit).
- **Ajouter `Beacon_01`, `Beacon_02`, `Beacon_03`** — trois marqueurs, placés comme sur la planche :
  un au-dessus de la proue, deux en retrait de part et d'autre de la poupe, **hors de la coque**
  (elles flottent). Ils ne doivent pas déborder la bbox X/Z.

### 3. Densifier les trois masses

- Stations intermédiaires sur `HULL` (9 aujourd'hui) et `ARM` (7) — sans lisser les cassures
  franches, qui font tout le caractère prismatique.
- **Découper les grands aplats en plaques irrégulières.** `inset_panel` n'est jamais imbriqué ici,
  alors que `build_crescent_interceptor.py:597-598` fait déjà un double inset emboîté : technique
  prouvée dans le dépôt, jamais appliquée à la citadelle.
- **Liserés or** le long des arêtes de panneau, comme la planche — l'or est aujourd'hui cantonné à
  quelques lisses.
- **Greebles** là où la caméra les voit. La règle ne bouge pas : *si une surface n'est pas visible
  depuis la caméra de jeu, ce qu'on y met n'existe pas* (ADR-0011). Mais la citadelle est désormais
  vue **de trois quarts en gros plan sur l'écran d'accueil** — le pont supérieur compte doublement.

### 4. Le noyau cristallin

C'est la signature de la faction, celle qui porte la lecture à toute distance. Plus de facettes,
nervures de taille affinées, cadre technique (jonc or, contreforts, marquages rouges) enrichi.
La texture de facettes viendra par-dessus, mais **la géométrie doit déjà tenir seule** : un émissif
ne reçoit pas la lumière.

### 5. Les quatre canons par bras

La planche montre **deux paires superposées**, pas trois tubes alignés. Culasses greebées, colliers
dorés, bouches à lèvre. `Muzzle_Battery_L/R` reste sur le tube **le plus avancé** — c'est lui qui
fixe la bbox en -Y et le point de tir lu par `aegis_citadel.gd:32`.

### 6. La baie d'appontage

La planche lui consacre un encart entier : gorge **profonde** (pas une boîte émissive posée à plat),
rails latéraux, feux d'approche, chevrons. `Dock_Entry` reste au même rôle.

### 7. Biseau

`bevel_sharp_edges` est à `segments=1`, `width=0.03`. Avec 120 000 triangles de budget, `segments=2`
devient envisageable — **à juger au rendu, pas au chiffre**. Si ça ramollit les arêtes du prisme,
reste à 1 et dis-le.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/build_aegis_citadel.py` | script retravaillé, toujours rejouable |
| `assets/imported/models/structures/aegis_citadel.glb` | coque exportée, **avec UV et tangentes** (LFS) |
| `tools/blender/build_citadel_turret.py` | **nouveau** — tourelle seule, pivot au centre de rotation |
| `assets/imported/models/structures/citadel_turret.glb` | **nouveau**, ~2 000 triangles |
| `tools/blender/build_citadel_beacon.py` | **nouveau** — balise : nacelle, anneau, œil cyan |
| `assets/imported/models/structures/citadel_beacon.glb` | **nouveau**, ~1 200 triangles |
| `docs/forge/output/BRIEF-0032-report.md` | compte-rendu : mesures réelles, ce que le rendu montre, limites |

### Contrat des deux nouveaux modèles

Ils sont **orientés pour être animés** — c'est leur seule contrainte forte :

- **Tourelle** : origine **au centre de rotation** (l'axe du fût), tubes pointant vers **-Y** dans le
  repère d'auteur. Une tourelle dont le pivot n'est pas au centre décrira un cercle au lieu de
  pivoter, et le défaut ne se verra qu'une fois animée.
- **Balise** : origine au centre de la nacelle. L'anneau doit être une **partie distincte
  nommée `Ring`** (marqueur `Ring_Center` si le kit ne sait pas exporter la pièce séparément — dis-le
  dans le compte-rendu, on adaptera côté Godot).
- Les deux : mêmes 7 matériaux, mêmes règles de déterminisme, UV dépliées.

## Critères d'acceptation

- [ ] Les trois scripts régénèrent sans erreur en headless
- [ ] Deux exécutions successives : `.glb` **byte-identiques** (`sha256sum`)
- [ ] Bbox X/Z **inchangée** à ±3 % (19,60 × 16,60) ; hauteur ≤ 5,60 m
- [ ] Les trois `.glb` contiennent `TEXCOORD_0` **et** `TANGENT`
- [ ] Coque ≤ 120 000 triangles (cible 70-90 k)
- [ ] Points d'attache **conservés** : `Core_Center`, `Muzzle_Battery_L/R`, `Dock_Entry`,
      `Core_Prism`, `Battery_L/R`, `Dock_Bay`, `Turret_01..06` — **plus** `Beacon_01..03`
- [ ] Les tourelles ne sont **plus** dans le maillage de la coque
- [ ] **Rendu et regardé** (ADR-0006) :
      `blender45 -b -P tools/render-hull.py -- assets/imported/models/structures/aegis_citadel.glb`
      Critère explicite : sur la vue « jeu » et la vue de dessus, on doit voir des **dizaines de
      plaques**, des liserés or et un cristal **facetté**, là où il n'y a aujourd'hui que trois
      grands aplats. Le compte-rendu dit ce que la planche montre, sans complaisance.
- [ ] Provenance mise à jour : la ligne de la coque **réécrite** (pas dupliquée), deux lignes
      ajoutées pour les nouveaux modèles

## Hors périmètre

Ne pas toucher au code gameplay, aux `.tscn`, aux `.gd`, aux `.tres`, aux tests, ni aux autres
coques. **Ne pas modifier `aegis_kit.py`** : s'il manque une primitive, **le signaler dans le
compte-rendu** au lieu de le corriger en douce — c'est la session principale qui arbitre une
évolution du kit. Pas de `.blend` versionné. Ne pas changer la silhouette générale ni X/Z. Ne pas
écrire l'animation (elle est faite côté Godot). Ne pas générer de texture — les cinq cartes sont
traitées par ailleurs (`docs/forge/output/citadel_textures_generation_prompt.md`).
