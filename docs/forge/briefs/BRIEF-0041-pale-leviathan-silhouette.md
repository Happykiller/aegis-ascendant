# BRIEF-0041 — Pale Leviathan : rendre la silhouette à sa planche

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-07-23
- **Suite de** : BRIEF-0040 (livré, intégré au commit `e57a285`)

## Objectif

Corriger **la forme et le budget de matière** de `build_pale_leviathan.py` pour que la coque
ressemble à ses planches. Rien d'autre : tout l'acquis technique de BRIEF-0040 est conservé.

## Contexte

BRIEF-0040 a été **accepté sur le plan technique**, et il a dépassé sa commande : 30 pièces au
contrat de noms avec le bon parentage, `TEXCOORD_0` et `TANGENT`, déterminisme reproductible,
dégagements mesurés **à chaque build et bloquants**, et la découverte que l'exportateur glTF
abandonne silencieusement les tangentes sur un maillage à n-gons.

**Ce qui ne va pas est ailleurs : la coque ne ressemble pas aux planches.** Ce n'est pas une
question de goût, et deux mesures le disent.

### Mesure 1 — un tiers de la coque est émissif

Répartition des sommets par matériau dans le `.glb` livré :

| Matériau | Part | |
|---|---|---|
| `AA_Greeble` | 32,5 % | |
| `AA_Emissive_Engine` | **28,7 %** | ⚠️ |
| `AA_Trim` | 14,9 % | |
| `AA_Panel` | 11,3 % | |
| `AA_Hull` | **11,0 %** | ⚠️ |
| `AA_Marking_Red`, `AA_Glass` | 1,6 % | |

**Un émissif ne reçoit pas la lumière** : il rend plat, uniforme et clair, quelle que soit
l'orientation de la surface. À 28,7 % de la coque, il noie le modelé et fait lire l'ensemble en
**rose pâle délavé**. C'est le défaut qu'ADR-0013 relève déjà pour le noyau de la citadelle, qui
lisait comme « une goutte blanche uniforme ».

Sur les planches, le magenta est un **réseau de veines fines entre les plaques** — quelques pour
cent de la surface, pas un tiers.

### Mesure 2 — le blindage a disparu sous la machinerie

`AA_Greeble` (32,5 %) contre `AA_Hull` (11,0 %) : trois fois plus d'encombrement mécanique que de
blindage. Les planches montrent exactement l'inverse — de **grandes plaques d'écailles** ivoire et
anthracite qui se recouvrent, dominant la silhouette, avec la machinerie reléguée aux interstices.
D'où la lecture actuelle en « disque machiné » plutôt qu'en coque blindée organique.

### Quatre écarts de forme

Comparaison faite panneau par panneau avec `assets/reference/concepts/pale_leviathan_parts_sheet.png`
et `pale_leviathan_core_states_sheet.png` :

| | Ce qui est livré | Ce que montre la planche |
|---|---|---|
| **Symétrie** | radiale d'ordre 4 | **asymétrique** — charte §4 (« Null Choir : sombre, segmenté, **asymétrique** »), et BRIEF-0024 disait déjà « ne pas *corriger* en mettant une symétrie » |
| **Noyau** | rosette plate | **sphère** magenta, bombée, plein cadre (panneau `CLOSED CORE`) |
| **Épines** | cônes courts, ~1/4 du corps | longs **dards segmentés** — le panneau `DETACHED SPIKE` en montre un presque aussi long que le corps |
| **Coquille** | anneau complet | **croissant** : « anneau **incomplet** » est l'identité canon du vaisseau (charte §2) |

Le compte-rendu de BRIEF-0040 §4.5 dit avoir donné 230° de matière au croissant. À l'écran, les
anneaux concentriques qui l'entourent referment visuellement l'ouverture : **l'incomplétude ne se
lit pas**, et c'est elle qui doit se lire.

## Ce qui est acquis et NE DOIT PAS bouger

C'est la moitié du brief. Y toucher serait perdre le travail de BRIEF-0040.

- **Le contrat de noms et le parentage** — 30 pièces, `Shell_Ring → Shell_Crescent → Plate_0X`,
  `Core → Maw_Lip → Node_0X`, `Core → Ring_0X`, `Core → Heart`, `Spike_0X → _Mid → _Tip`. Le module
  de combat est **écrit contre ces noms en ce moment même**.
- **Les 29 `moving_part`** et leurs pivots, **`box_project_uv(0.18)`** sur les 30 maillages, la passe
  `_triangulate_ngons()` qui sauve les tangentes.
- **Le harnais de dégagement** et son caractère bloquant. Les dix lignes doivent rester mesurées et
  positives après la reforme de forme.
- **Le déterminisme** et l'auto-validation du contrat.
- Les débattements du tableau de BRIEF-0040, **y compris la flexion verticale d'épine à ±5°** : elle
  est jugée **acceptable** et n'est plus une non-conformité. Dans un shooter vu de dessus, la flexion
  qui compte est celle du plan de jeu, et elle est tenue à ±25°.

## Ce qu'il faut changer

### 1. Budget de matière

Cibles, à rapporter mesurées dans le compte-rendu :

| Matériau | Cible | Pourquoi |
|---|---|---|
| `AA_Emissive_Engine` | **≤ 8 %** | des veines, pas une livrée. C'est ce qui rend le magenta *lumineux* au lieu de délavé |
| `AA_Hull` | **≥ 30 %** | le blindage doit dominer la silhouette |
| `AA_Greeble` | **≤ 20 %** | la machinerie vit dans les interstices |

⚠️ Ne pas obtenir ces chiffres en supprimant de la géométrie : c'est une **réaffectation** de
matériaux et un rééquilibrage des masses, pas un appauvrissement. Le budget reste 40 000 triangles
(31 098 aujourd'hui — il reste de la marge).

### 2. Casser la symétrie radiale

La silhouette doit être reconnaissable **et déséquilibrée**. Pistes, non prescriptives : longueurs
d'épines inégales, croissant nettement plus épais d'un côté, ouverture du croissant franchement
décentrée, une plaque plus grande que les trois autres.

⚠️ **Les quatre plaques doivent rester interchangeables en jeu** : elles orbitent et le joueur les
abat dans n'importe quel ordre. L'asymétrie porte sur la coque et les épines, **pas** sur les zones
de touche.

### 3. Le noyau redevient une sphère

Bombé, saillant, lisible comme une **boule** en vue de dessus — l'angle de la caméra de jeu. C'est la
cible que le joueur regarde pendant quatre minutes et la vignette de sa fiche de codex.

### 4. Les dards s'allongent

Épines nettement plus longues et plus effilées, segmentées, veinées. Elles se détachent en phase 3
et deviennent des unités autonomes : elles doivent être **lisibles seules**, hors du corps.

### 5. Le croissant doit se lire comme incomplet

L'ouverture doit être visible **en vue de dessus, au repos**, sans compter sur l'animation. Si les
anneaux concentriques la referment visuellement, ce sont eux qui doivent reculer ou s'interrompre.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/build_pale_leviathan.py` | script amendé |
| `assets/imported/models/bosses/pale_leviathan.glb` | régénéré via `./scripts/build-hull.sh pale_leviathan` |
| `docs/forge/output/BRIEF-0041-report.md` | compte-rendu |
| `docs/forge/output/BRIEF-0041-planche-quatre-vues.png` | planche de recette |

Mettre à jour la ligne `pale_leviathan_hull` de `assets/licenses/ASSET_PROVENANCE.csv`.

## Critères d'acceptation

- [ ] **Répartition des matériaux mesurée et rapportée**, aux trois cibles du §1.
- [ ] Le contrat de noms est **inchangé** : 30 pièces, mêmes noms, mêmes parents. Le vérifier en
      relisant le JSON du `.glb`, pas en s'en souvenant.
- [ ] UV **et** tangentes toujours présentes sur les 30 maillages.
- [ ] `./scripts/build-hull.sh --check pale_leviathan` : 0 octet divergent.
- [ ] Contrat d'export : bbox 11,0 × 14,0 (±3 %), Y ≤ 3,20, ≤ 40 000 triangles.
- [ ] Les dix lignes de dégagement restent **positives**, remesurées.
- [ ] **Regardé avant de rendre** (ADR-0006) : la planche 4 vues **côte à côte** avec
      `pale_leviathan_parts_sheet.png`. Les quatre écarts du contexte doivent être visiblement
      résorbés — et le dire panneau par panneau dans le compte-rendu, pas « conforme ».
- [ ] En vue de dessus au repos : le croissant lit comme **incomplet**, le noyau comme une **sphère**.

## Hors périmètre

- **Ne pas** toucher au code GDScript, aux scènes ni aux Resources : `leviathan_combat.gd` s'écrit en
  parallèle (`.claude/resources/pratique-ecrivain-unique.md`).
- **Ne pas** modifier le contrat de noms, les pivots, ni la densité d'UV.
- **Ne pas** corriger `build_choir_harvester.py` : le même défaut de tangentes l'affecte, mais il
  fera l'objet de son propre brief — un brief, un objectif.
- **Ne pas** produire de texture ni de SFX.
