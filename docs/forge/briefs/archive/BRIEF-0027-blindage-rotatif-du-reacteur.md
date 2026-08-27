# BRIEF-0027 — La matière du blindage rotatif du réacteur

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-08-27

## Objectif

Produire la **demande de texture normalisée** (`docs/forge/textures/TEX-0009-*.json`) et son prompt
pour la matière des **deux murs rotatifs de la Chambre du Réacteur** — le blindage du boss final.
La génération raster elle-même revient à l'opérateur (voie ImageGen) ; ce brief livre le contrat.

## Contexte

La Chambre du Réacteur (plan `docs/plans/2026-08-27-reactor-chamber.md`) enferme le noyau du Pale
Leviathan derrière **deux anneaux blindés contrarotatifs**. Ils viennent d'être refondus en volumes
pleins et clos (`scripts/bosses/core_interior.gd`, `_arc()`), après un playtest où l'opérateur les a
lus comme « juste des U inversés » puis « un halo de couleur » — c'est-à-dire **sans matière**.

Le matériau est aujourd'hui un `StandardMaterial3D` par facteurs seuls : `albedo (0.22, 0.19, 0.28)`,
`metallic 0.55`, `roughness 0.45`, émission violette à 0,30. Ça donne un volume, pas une machine.

**Ce qu'on regarde réellement** : la caméra est en plongée quasi verticale. La face vue est donc la
**tranche supérieure** du mur — une bande annulaire d'**1,00 m de large**, longue de 4,05 m (mur
extérieur, arc de 40° à R=5,8 m) et de 2,30 m (mur intérieur, arc de 60° à R=2,2 m). Les parois
latérales (0,70 m de haut) ne se voient qu'en tranche, à la faveur de la rotation.

## Contraintes

- **IP** : aucun nom, silhouette ni marquage identifiable (spec §0.2). Pas de lettrage, pas de
  numéro de coque, pas d'insigne — cette surface tourne, tout glyphe deviendrait un point de
  fixation du regard sur une pièce qui doit rester du décor.
- **Palette / DA** : registre **machine froide**, sombre et peu saturé — violet-graphite du réacteur
  (`#38304a` environ). Elle passe **derrière** le gameplay : elle ne doit jamais rivaliser avec le
  noyau (orange, la cible) ni avec les verrous (cyan-vert). ⚠️ Cyan `#3FD9E8` et corail `#FF5A3D`
  sont **interdits** (règle 5 du contrat textures) : ils appartiennent aux projectiles.
- **Lisibilité (LOI-LIS-01)** : le mur est un **obstacle mortel**. Sa matière doit dire « blindé,
  massif, infranchissable » d'un coup d'œil, et surtout **ne pas** suggérer une ouverture, une
  grille ou un interstice — le joueur cherche précisément un passage sur cette phase, et un motif
  qui mime un corridor lui coûterait une vie.
- **Techniques** : `1024x1024`, tuilable **mesuré** (`derive-maps.py --check-tiling`), fond opaque,
  **carte de hauteur en niveaux de gris** (`output_usage: source_for_normal`, ADR-0013 : la normale
  se dérive, jamais ne se demande). Rendu final post-processé à 960×540 : pas de micro-détail qui
  disparaîtra.

## Texture (ADR-0028 — OBLIGATOIRE)

L'asset **dépend d'une demande de texture**, à créer :

- `docs/forge/textures/TEX-0009-blindage-reacteur.json` — plaque de blindage de sas de réacteur,
  vue du dessus, hauteur en niveaux de gris.

**Échelle monde** : `2,0 m × 2,0 m` par tuile, `confidence: "decided"`. Justification à reporter
dans le JSON : la bande vue fait 1,00 m de large (`thickness = 1.0` dans
`resources/bosses/pale_leviathan_tuning.tres`, et 1 unité = 1 m par `ADR-0008`) ; une tuile de 2 m
place donc **une demi-tuile en travers du mur**, soit deux à quatre plaques visibles sur la
longueur d'un arc — assez pour lire un appareillage, trop peu pour lire une répétition.

**Dépliage** : la géométrie est générée par code (`_arc()`), pas importée. Elle porte un dépliage
**continu et à densité homogène**, que j'ajoute côté moteur : `u` proportionnel à la **longueur
d'arc réelle** (donc identique en densité sur les deux anneaux malgré leurs rayons différents), `v`
proportionnel à la largeur traversée. Il n'y a pas de `.glb`, donc pas de `TEXCOORD_0` à compter —
mais la densité de texels est à vérifier **à la capture**, pas sur parole.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `docs/forge/textures/TEX-0009-blindage-reacteur.json` | La demande normalisée, dix blocs dans l'ordre du contrat, `x_delivery` et `x_prompt_fr` compris |
| (rapport) | Le `x_prompt_fr` **recopié en clair dans le rapport final**, prêt à coller dans ImageGen par l'opérateur |

## Provenance

Pas de ligne CSV à ce stade : **aucun binaire n'est livré par ce brief**. Le JSON prépare
`x_delivery.csv_line` pour `assets/source/textures/bosses/reactor_armour_height_1024.png` et ses
quatre dérivées dans `assets/imported/textures/bosses/`, à coller le jour de l'intégration.

## Critères d'acceptation

- [ ] Le JSON passe **les six règles** de `docs/forge/textures/README.md`, et le rapport dit
      laquelle a été vérifiée comment — pas « conforme » en bloc
- [ ] `resolution` = `1024x1024` ; `transparent_background` absent ou `false` ; `tileable: true`
- [ ] `color_palette.forbidden` contient cyan `#3FD9E8` **et** corail `#FF5A3D`
- [ ] `output_usage: "source_for_normal"` et la description demande bien une **hauteur** (clair =
      saillant), jamais une carte de normale
- [ ] `world_scale.confidence: "decided"` avec le `rationale` ci-dessus, chiffres repris
- [ ] Le `x_prompt_fr` **ouvre sur la consigne de fond** en nommant les intrus (dégradé, vignettage,
      halo, étoiles, nébuleuse, atmosphère, sol, décor), conformément à l'avertissement du contrat
- [ ] Le prompt interdit explicitement tout **lettrage, chiffre, insigne, symbole**
- [ ] Le prompt interdit tout motif lisible comme une **ouverture, une grille, une fente ou un
      interstice** — et le rapport dit en une phrase pourquoi cette interdiction existe ici

## Hors périmètre

- **Ne pas générer d'image** ni écrire de PNG : la génération raster passe par l'opérateur.
- Ne toucher à **aucun** script de `scripts/`, à aucune `Resource` de gameplay, à aucune scène.
- Ne pas traiter le noyau, les verrous orbitaux, les rails ni le décor animé de la chambre : ce
  brief ne couvre que **les deux murs**.
