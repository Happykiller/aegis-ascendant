# BRIEF-0026 — Rendre l'émissif lisible depuis la caméra de jeu

- **Statut** : brouillon
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-07-12

## Objectif

Ajouter aux coques les **lignes et surfaces lumineuses vues de dessus** qui leur manquent, et
inscrire la règle dans le kit pour que les coques futures ne retombent pas dans le piège.

## Contexte

Constat fait sur le rendu en jeu du Specter-9, capture à l'appui : **ses tuyères cyan ne se voient
pas**. L'émissif a été posé là où il est physiquement — sur les faces arrière des tuyères — mais la
caméra de jeu est inclinée d'environ 20° au-dessus du plan, c'est-à-dire presque à la verticale.
Elle ne regarde jamais l'arrière d'un vaisseau. Tout l'émissif dépensé là est invisible.

Or c'est l'émissif qui porte l'identité de faction (cyan Vanguard / magenta Chœur Nul), et c'est lui
qui déclenche le glow. Les planches de concept le montrent d'ailleurs bien : les lignes d'énergie
courent sur le **dessus** des coques, pas seulement dans les tuyères.

C'est une règle de lisibilité, pas une préférence esthétique : **si une surface n'est pas visible
depuis une caméra à 20°, ce qu'on y met n'existe pas.**

## Périmètre

1. **Specter-9** — ajouter des lignes lumineuses dorsales conformes à la planche (épine centrale,
   liserés d'aile), et rendre l'anneau de tuyère visible d'en haut (lèvre biseautée vers le dessus,
   plutôt qu'un disque plat orienté vers l'arrière).
2. **Needle Scout** — sa rainure d'énergie magenta est déjà dorsale : vérifier qu'elle lit bien à sa
   taille réelle à l'écran (~30 px), l'élargir si nécessaire.
3. **Kit** — documenter la règle dans l'en-tête de `aegis_kit.py`, et vérifier si un contrôle
   automatique est possible (par exemple : « part de l'aire émissive visible depuis +Y »), sans
   sur-ingénierie si le rapport coût/bénéfice est mauvais — dans ce cas, le dire.

Le Choir Harvester, le Pale Leviathan et l'Aegis Citadel ont déjà des noyaux et des craquelures
dorsaux : les inspecter, mais ne les modifier que si le défaut est constaté.

## Méthode de vérification exigée

Ne pas juger sur un rendu 3/4 depuis Blender : **rendre chaque coque depuis un angle qui reproduit
la caméra de jeu** (environ 20° au-dessus du plan, vaisseau nez vers le haut de l'image), et juger
là-dessus. C'est exactement l'erreur qui a produit le défaut.

## Contraintes

- Palette et matériaux normalisés de l'ADR-0008 inchangés (`AA_Emissive_Engine` porte l'émissif).
- Budgets de triangles inchangés (le Specter-9 a 5 164 triangles de marge).
- Déterminisme et auto-validation inchangés ; les `.glb` doivent rester byte-identiques à leur
  rejeu.
- Les dimensions monde ne bougent pas (±3 %).

## Critères d'acceptation

- [ ] Les lignes lumineuses du Specter-9 se voient sur un rendu à 20° (le montrer)
- [ ] Les budgets et les bounding box restent dans le contrat
- [ ] La règle de lisibilité est écrite dans le kit
- [ ] Compte-rendu honnête, avec les rendus de contrôle à 20°

## Hors périmètre

Pas de textures, pas de LOD, pas d'animation. Ne pas toucher au code gameplay ni aux scènes.
