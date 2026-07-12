# BRIEF-0021 — Kit hard-surface Blender + coque 3D du Specter-9

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-07-12

## Objectif

Poser la **bibliothèque hard-surface partagée** (`tools/blender/lib/aegis_kit.py`) qui servira aux
cinq coques du jeu, et l'éprouver en livrant la première : le **Specter-9**, chasseur du joueur, en
modèle 3D `.glb` PBR.

C'est le brief pilote. Les quatre autres coques (Needle Scout, Choir Harvester, Pale Leviathan,
Aegis Citadel) seront produites ensuite **en parallèle** avec ce même kit : tout ce qui est
générique doit donc vivre dans le kit, pas dans le script du Specter-9.

## Contexte

Aujourd'hui, aucun objet 3D n'existe dans le jeu : le vaisseau du joueur est un `Sprite3D` plat et
non éclairé. **Lire `docs/decisions/ADR-0008-pipeline-3d-blender.md` en entier avant de commencer**
— il contient les conventions normatives (échelle, orientation, pivot, matériaux, budgets,
déterminisme) et elles ne sont pas négociables.

Blender est déjà installé : `blender45 -b -P <script>` (via `./scripts/bootstrap-blender.sh`).
La chaîne Blender → glTF → import Godot est vérifiée et fonctionne en headless.

Référence de design : **`assets/source/concepts/specter_9_concept_sheet.png`**. C'est un vrai model
sheet — vue de dessus (grande), face, profil, arrière, deux vues 3/4, gros plans tuyères et canon,
silhouettes. Tout ce qu'il faut pour modéliser sans inventer.

Traits à respecter, lisibles sur la planche : aile delta à double flèche, nez pointu, verrière
allongée décalée vers l'avant, épine dorsale creusée, **deux grosses tuyères cylindriques** en
partie arrière avec anneau émissif cyan, canon ventral central sous le fuselage, panneaux bleu
profond sur coque blanc cassé, liserés or, marquages rouges en bout d'aile.

## Contraintes

- **IP** : aucune silhouette, nom ou élément identifiable de Macross, Robotech ou d'une autre
  licence. Le Specter-9 est un design original ; s'en tenir strictement à la planche de concept.
- **Palette / DA** : palette Vanguard de `docs/forge/CHARTE_CREATIVE.md` §3, via les matériaux
  normalisés de l'ADR-0008 (`AA_Hull`, `AA_Panel`, `AA_Trim`, `AA_Greeble`, `AA_Glass`,
  `AA_Emissive_Engine`, `AA_Marking_Red`).
- **Techniques** :
  - Dimensions monde imposées : **1,75 m (X) × 2,46 m (Z)**, tolérance ±3 %. Hauteur Y libre mais
    modeste (≈ 0,35-0,60 m) : la caméra est quasi au-dessus, une coque épaisse casse la lecture.
  - Orientation d'auteur : **nez vers -Y, dessus vers +Z** dans Blender (→ nez vers -Z dans Godot).
  - Pivot à l'origine, au centre de la coque, au niveau du plan de jeu.
  - Budget : **≤ 15 000 triangles**.
  - Détail par la **géométrie** (bevels, découpes/enfoncements de panneaux, greebles), pas par des
    textures. Aucun texture map, aucun UV bake : PBR par facteurs de matériau.
  - Déterministe : pas de `random` non seedé ; deux exécutions → même mesh.
  - Blender 4.5 LTS uniquement, en headless. API 4.5 (attention : `Emission Strength`,
    `export_yup`, etc. — vérifier, ne pas inventer d'API).

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/lib/aegis_kit.py` | bibliothèque partagée (voir API attendue ci-dessous) |
| `tools/blender/build_specter_9.py` | script de construction du chasseur, rejouable |
| `assets/imported/models/ships/specter_9.glb` | le mesh exporté (LFS) |
| `docs/forge/output/BRIEF-0021-report.md` | compte-rendu : méthode, mesures, limites |

## API attendue du kit

Le kit doit au minimum offrir, sous des noms clairs et documentés :

- réinitialisation de scène propre (factory settings, scène vide) ;
- accès aux **couleurs de la charte** et fabrique de **matériaux normalisés** mémoïsés
  (un `AA_Hull` unique partagé par toutes les coques) ;
- helpers hard-surface réutilisables : biseau, découpe/enfoncement de panneau, bandeau de greebles,
  symétrie en X ;
- création de **points d'attache** (Empties) ;
- **export glTF** conforme à l'ADR (yup, modificateurs appliqués, `.glb`) ;
- **validation de contrat** : bounding box vs dimensions attendues (±3 %), nombre de triangles vs
  budget, présence des matériaux et des points d'attache requis → **échec bruyant** si hors
  contrat, jamais un export silencieux.

Les quatre coques suivantes réutiliseront ce kit tel quel : ne rien y coder de spécifique au
Specter-9. Prévoir que la palette antagoniste (Chœur Nul) sera nécessaire.

## Points d'attache requis sur le Specter-9

`Muzzle_L`, `Muzzle_R` (bouches de tir, à l'avant), `Engine_L`, `Engine_R` (centre des tuyères,
d'où partira la traînée), `Cockpit` (centre de la verrière).

Ils remplaceront des offsets aujourd'hui codés en dur dans le contrôleur joueur — leur position
doit donc être **juste**, pas approximative.

## Provenance

Une ligne par asset livré dans `assets/licenses/ASSET_PROVENANCE.csv` (append shell, ne pas
réécrire le fichier) : `asset_type=model3d`, `source_tool=asset-forge (Blender 4.5.11, script)`,
`author=asset-forge (Claude)`, `license=proprietary-internal`,
`prompt_file=docs/forge/briefs/BRIEF-0021-hull-kit-specter-9.md`, `notes` = planche de concept
source + budget triangles atteint.

## Critères d'acceptation

- [ ] `blender45 -b -P tools/blender/build_specter_9.py` s'exécute sans erreur et régénère le `.glb`
- [ ] Bounding box mesurée : 1,75 × 2,46 m (±3 %), hauteur ≤ 0,60 m
- [ ] ≤ 15 000 triangles (chiffre réel donné dans le compte-rendu)
- [ ] Nez vers -Y / dessus vers +Z dans Blender ; pivot à l'origine, centré
- [ ] Les 7 matériaux normalisés existent et sont assignés de façon cohérente avec la planche
- [ ] Les 5 points d'attache existent, correctement placés
- [ ] Le script s'auto-valide et échoue si le contrat est rompu (le prouver : montrer le rapport)
- [ ] Provenance renseignée
- [ ] Le kit ne contient rien de spécifique au Specter-9

## Hors périmètre

- **Ne pas toucher au code gameplay ni aux scènes `.tscn`** : l'intégration est faite par le
  concepteur principal.
- Pas de textures, pas d'UV bake, pas de LOD, pas d'animation, pas de rig.
- Pas de `.blend` versionné : le script est la source.
- Ne pas modéliser les quatre autres coques (briefs séparés).
