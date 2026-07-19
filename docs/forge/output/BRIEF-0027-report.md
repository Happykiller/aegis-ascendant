# BRIEF-0027 — Rapport de mission (points d'emport de tir du Specter-9)

- **Agent** : asset-forge (Claude)
- **Date** : 2026-07-19
- **Statut** : livré, contrat ADR-0008 vert, build déterministe

## 1. Objet

Compléter les points d'attache du Specter-9 pour que chaque flux de tir du joueur parte d'un canon
physique du mesh, à tous les niveaux de power. La coque n'exposait qu'un twin de nez très resserré
(`Muzzle_L/R`, `BARREL_X = 0.026`, deux tirs superposés). On passe de **5 à 10** points d'attache,
positions **dérivées de la géométrie** (tables de profil `PLANFORM`, `z_top`, `STRAKE`, `NACELLE`),
et on écarte les deux tubes de nez pour un twin lisible.

Périmètre respecté : seul `tools/blender/build_specter_9.py` (le script *est* l'asset, ADR-0008), le
`.glb` régénéré et le CSV de provenance sont modifiés. Aucun fichier `scripts/**` ni `.tscn` touché ;
le recâblage du pattern de tir reste au concepteur.

## 2. Positions réelles relevées sur le `.glb` régénéré

Mesures lues par `ak.export_hull()` sur le fichier binaire produit, exprimées dans le **repère Godot**
(X latéral, Y haut, Z longitudinal ; nez vers -Z). C'est le repère que lira le contrôleur joueur.

| Point d'attache | X | Y | Z | Rôle / niveau de power |
|---|---:|---:|---:|---|
| `Muzzle_L`      | -0.0800 | -0.0425 | -1.0700 | twin de nez babord (power 1+) |
| `Muzzle_R`      | +0.0800 | -0.0425 | -1.0700 | twin de nez tribord (power 1+) |
| `Muzzle_C`      | +0.0000 | -0.0425 | -1.0700 | canon d'axe central (power 4) |
| `Muzzle_Wing_L` | -0.5000 | -0.0180 | -0.0518 | canon d'aile babord (power 3) |
| `Muzzle_Wing_R` | +0.5000 | -0.0180 | -0.0518 | canon d'aile tribord (power 3) |
| `Muzzle_Tip_L`  | -0.8000 | -0.0087 | +0.4180 | pod de bout d'aile babord (power 5) |
| `Muzzle_Tip_R`  | +0.8000 | -0.0087 | +0.4180 | pod de bout d'aile tribord (power 5) |
| `Engine_L`      | -0.2350 | -0.0300 | +1.2200 | tuyère babord (traînée) — inchangé |
| `Engine_R`      | +0.2350 | -0.0300 | +1.2200 | tuyère tribord (traînée) — inchangé |
| `Cockpit`       | +0.0000 | +0.1398 | -0.5175 | centre du volume de verrière — inchangé |

L'escalade latérale des bouches de tir est monotone et bien étagée : axe (0) < twin de nez (±0.080)
< canons d'aile (±0.500) < pods de bout d'aile (±0.800), le tout sous la demi-largeur max 0.875.

## 3. Comment chaque position est dérivée de la géométrie

- **Twin de nez `Muzzle_L/R`** : `(±BARREL_X, MUZZLE_Y, _barrel_z())` — exactement l'axe des tubes du
  canon ventral, à leur bouche. Muzzles et géométrie des tubes (`build_details`, boucle `add_lathe`)
  partagent le **même** `BARREL_X` : flash, tube et balle restent alignés par construction.
- **Canon d'axe `Muzzle_C`** : `(0, MUZZLE_Y, _barrel_z())` — même plan de tir que le twin, entre les
  deux tubes.
- **Canons d'aile `Muzzle_Wing_L/R`** : `x = ±0.500` ; `y` = station du **bord d'attaque** où la
  demi-envergure `PLANFORM` vaut 0.500 (`_leading_edge_station(0.500) → y = -0.0518`) ; `z` =
  `z_top(0.500, section_params(y))` = -0.0180 (surface supérieure d'aile, anhédral compris). Le point
  tombe pile sur le point de bord d'attaque à mi-aile.
- **Pods de bout d'aile `Muzzle_Tip_L/R`** : `x = ±0.800` (en retrait sous la largeur max 0.875 pour
  rester sur la coque) ; `y` = coin avant du bout d'aile = station de largeur maximale du planform
  (`_tip_front_station() → y = 0.418`) ; `z` = `z_top(0.800, section_params(0.418))` = -0.0087
  (aile fortement affaissée par l'anhédral en bout).

Les deux stations sont calculées par inversion **monotone** de `PLANFORM` sur sa seule branche avant
(du nez au coin avant du bout d'aile), pour ne jamais basculer sur le bord de fuite.

## 4. Écartement du twin de nez (`BARREL_X` : 0.026 → 0.080)

Le brief suggérait `BARREL_X ≈ 0.12` « à ajuster pour rester sous le STRAKE ». Analyse de la coque :

- La demi-envergure du planform au droit de la **bouche** (`y = -1.07`) ne vaut que ~0.050, et à la
  **culasse** des tubes (`y ≈ -0.89`, station la plus large couverte par les tubes) elle vaut ~0.104.
- À `BARREL_X = 0.12`, les tubes flotteraient entièrement hors de la coque au niveau de la bouche
  (0.12 ≫ 0.050) : deux canons détachés dans le vide. Géométriquement intenable pour un canon de nez.

Valeur retenue : **`BARREL_X = 0.080`**, dérivée de la géométrie = demi-envergure à la culasse
(~0.104) moins le rayon de lèvre du tube (`BARREL_R × 1.22 ≈ 0.021`). Conséquences :

- La **culasse** des tubes reste ancrée sous le nez ; seule la partie avant projette, comme un vrai
  canon débouchant. Reste **sous la largeur maximale du longeron STRAKE (0.104)**.
- **Écartement du twin : 0.160 m** (2 × 0.080), contre 0.052 auparavant — soit ×3,1. Les deux bouches
  ont désormais un intervalle central net (bord à bord ~0.086 m entre les lèvres), largement supérieur
  au diamètre d'un tube (~0.041 m) : le twin se lit comme deux flux distincts, plus le flux d'axe
  central au milieu au power 4.
- Comme muzzles et tubes lisent le **même** `BARREL_X`, l'écartement s'applique d'un bloc : aucun
  risque de désalignement flash/tube/balle.

## 5. Contrat et déterminisme (sortie `export_hull`)

```
contrat OK — Specter-9
  triangles  : 9836        (budget 15000)   — inchangé (les tubes sont déplacés, pas ajoutés)
  sommets    : 9169
  bbox (Godot X,Y,Z) : 1.7500 x 0.4104 x 2.4598 m   (contrat 1.75 x ≤0.60 x 2.46, ±3%)
  centre     : (-0.0000, +0.0094, +0.0001)          (pivot centré, tol. ±0.02 m)
  materiaux  : 7 slots normalisés tous présents
```

- **Budget triangles** respecté (9836 ≤ 15000) : les 5 nouveaux hardpoints sont des Empties (0 tri) et
  l'écartement ne fait que translater la géométrie existante des tubes.
- **bbox / pivot / matériaux / orientation** dans le contrat ADR-0008.
- **Auto-validation** : `CONTRACT.required_attach_points` liste bien les 10 noms ; `export_hull()`
  échouerait si l'un manquait après régénération.
- **Déterminisme** : deux exécutions consécutives produisent un `.glb` **byte-identique**
  (SHA-256 `e7f2785a…c16b`), vérifié.

## 6. Livrables

| Fichier | État |
|---|---|
| `tools/blender/build_specter_9.py` | tubes écartés (`BARREL_X = 0.080`) + 5 hardpoints + 2 helpers de dérivation + contrat étendu à 10 points |
| `assets/imported/models/ships/specter_9.glb` | régénéré (LFS), 10 points d'attache, contrat vert |
| `assets/licenses/ASSET_PROVENANCE.csv` | ligne `specter_9_hull` : `modified_by = BRIEF-0027`, notes ré-écrites avec les 10 positions réelles |
| `docs/forge/output/BRIEF-0027-report.md` | ce rapport |

## 7. Limites connues et suggestions

- **Validation visuelle en attente** : conformément à l'ADR-0006, l'asset n'est *validé* qu'une fois
  rendu et regardé sur Windows par le concepteur. Deux points méritent l'œil :
  1. la **projection avant** des tubes de nez (leur tiers avant dépasse la pointe fine du nez) — c'est
     voulu (canon débouchant), mais à confirmer en rendu ¾ ;
  2. les **canons d'aile / bouts d'aile** posés sur une aile à fort anhédral (`z` négatif) : vérifier
     que les Empties affleurent bien la surface supérieure et non l'intérieur.
- **Écart assumé au brief** : `BARREL_X = 0.080` au lieu de `≈ 0.12` (valeur infaisable sans détacher
  les tubes du nez ; cf. §4). Si, après rendu, le twin paraît encore trop resserré, on peut monter
  jusqu'à ~0.083 (limite d'ancrage de la culasse sous la coque) sans changer le reste ; au-delà les
  tubes se détachent visuellement.
- **Suggestion pour le concepteur** : au recâblage de `_fire_pattern`, mapper directement les niveaux
  de power sur ces noms (power 1–2 : `Muzzle_L/R` ; +3 : `Muzzle_Wing_L/R` ; +4 : `Muzzle_C` ; +5 :
  `Muzzle_Tip_L/R`) et lire les positions via les nodes du `.glb` plutôt que par offsets codés en dur —
  c'est précisément ce que ces 10 hardpoints rendent possible.
