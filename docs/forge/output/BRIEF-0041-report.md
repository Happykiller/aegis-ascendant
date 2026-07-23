# BRIEF-0041 — Pale Leviathan, silhouette : compte-rendu

*Livré et intégré le 2026-07-23. Coque `pale_leviathan.glb` régénérée (sha256 `98529ce7…`),
provenance CSV ligne 99 mise à jour, rendu de recette `BRIEF-0041-planche-quatre-vues.png`.*

## Constat de reprise, corrigé par la mesure

Le brief avait été interrompu (agent `asset-forge` arrêté à la main). La note de reprise décrivait
un `.glb` intermédiaire hors-spec (largeur **9,481 m** pour un contrat à **11,0 ±3 %**) et un script
« forme restant à faire ». **Vérification faite plutôt que note crue** (empirisme > mémoire) : le
commit `0af3123` implémentait en réalité déjà toute la reforme — le message WIP sous-décrivait son
contenu (741 lignes : sphère du noyau, arc de coquille, épines allongées/inégales, gonflement du
croissant). Le `9,481 m` était un état antérieur écarté. Le script commité produit **11,03 m et passe
le contrat d'export**. Les épines `Spike_01`/`Spike_03` atteignent déjà `±HALF_W` (±5,50 m) : le
levier « largeur portée par l'envergure des épines » était déjà actionné.

La coque a donc été **régénérée** (le `.glb` sur disque était encore celui de BRIEF-0040), puis
vérifiée point par point.

## Mesures relevées (toutes sur le `.glb` régénéré)

**Matériaux** (`inspect_glb.py`, en sommets — les 3 cibles §1 du brief tenues) :

| Matériau | part | cible | verdict |
|---|---|---|---|
| `AA_Hull` | 35,2 % | ≥ 30 % | ✅ |
| `AA_Emissive_Engine` | 7,8 % | ≤ 8 % | ✅ |
| `AA_Greeble` | 17,9 % | ≤ 20 % | ✅ |
| `AA_Panel` 17,4 % · `AA_Trim` 19,8 % · `AA_Glass` 1,0 % · `AA_Marking_Red` 1,0 % | | | |

**Contrat d'export** (auto-validé, `contrat OK`) : bbox Godot **11,0313 × 3,1620 × 13,9972 m**
(X +0,28 %, Z −0,02 %, Y ≤ 3,20), centre `(−0,0001, +0,0110, −0,0014)`, **27 710 triangles /
40 630 sommets** (sous 40 000).

**Contrat de noms** : 30 maillages, parentage exact (`Shell_Ring→Shell_Crescent→Plate_0X`,
`Core→{Maw_Lip→Node_0X, Ring_0X, Heart}`, `Spike_0X→_Mid→_Tip`), lu dans le JSON du `.glb`.
**UV + tangentes présentes sur 30/30**.

**Déterminisme** : `./scripts/build-hull.sh --check pale_leviathan` → `déterminisme OK`,
sha256 `98529ce703faf6dfe6e6b5b560f68ef01299394b757a961f26f1840a359353a4`.

## Contrôle visuel (ADR-0006), panneau par panneau

Rendu 4 vues Cycles CPU comparé à `assets/reference/concepts/pale_leviathan_parts_sheet.png` :

1. **Symétrie → asymétrie : RÉSORBÉ.** Épines de longueurs franchement inégales (`Spike_01` ≈ 2×
   `Spike_04`), croissant qui gonfle d'un bout à l'autre. Enveloppe centrée au mm.
2. **Noyau plat → sphère : RÉSORBÉ, la réussite nette.** À l'angle de la caméra de jeu comme en vue
   de dessus, le noyau lit sans ambiguïté comme une boule magenta facettée, bombée et saillante
   au-dessus de l'armure.
3. **Épines courtes → longs dards : RÉSORBÉ.** Longues, segmentées, effilées, veinées, inégales.
4. **Anneau complet → croissant incomplet : PARTIEL, point le plus faible.** L'ouverture existe
   géométriquement mais la coquille est construite en bandes tangentielles concentriques : cette
   lecture « anneaux machinés » concurrence l'incomplétude et l'atténue, là où la planche montre une
   carapace de tuiles chevauchantes embrassant le noyau.

## Décision d'intégration

Livré **en l'état** : tous les critères mesurables verts, 3 écarts sur 4 résolus. La réserve n°4
(lisibilité de l'incomplétude / carapace vs anneaux) est **non bloquante** et versée au reste-à-faire
comme polish optionnel (BACKLOG). Levier propre si on l'ouvre : interrompre les bandes concentriques
du secteur d'ouverture (avant-tribord) plutôt qu'élargir l'encoche — incidence sur le harnais de
dégagement, à cadrer dans un brief séparé.
