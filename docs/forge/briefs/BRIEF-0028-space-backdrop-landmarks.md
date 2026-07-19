# BRIEF-0028 — Landmarks image du fond spatial (planète + nébuleuses)

- **Statut** : livré (vague 2 partielle — planète + nébuleuse A intégrées)
- **Assigné à** : opérateur (génération ChatGPT) + session principale (détourage + intégration)
- **Date** : 2026-07-19

## Objectif

Ajouter au fond spatial procédural (`shaders/space_background.gdshader`, refonte vague 1)
des **landmarks « héros » peints** qui dérivent lentement derrière le plan de jeu : une
planète et des amas de nébuleuse, pour atteindre le niveau du board de référence
`assets/source/references/reference_gameplay_vfx_environment_board.png` (couches 2 nébuleuse /
3 planète). Motivation : le fond, même après la vague 1, gagne en identité avec de vrais objets
peints comme points d'accroche, sans surcharger le couloir de combat central.

## Contexte

- Le fond est un plan-sol (`scenes/vfx/space_backdrop.tscn`) vu par une caméra inclinée
  (plan de jeu XZ à Y=0, caméra Y=14). Un objet rond peint sur ce plan serait écrasé par la
  perspective → les landmarks sont des **Sprite3D en billboard** (face caméra), placés à
  Y≈-3 (derrière les vaisseaux, devant la brume procédurale).
- Le rendu final passe par le post-process rétro (pixelisation ~960×540) : inutile de viser
  du photoréalisme fin, mais les images doivent être propres et contrastées.

## Contraintes

- **IP** : designs originaux, aucune marque/nom/silhouette sous licence (ADR-0009).
- **Palette/DA** : froid, désaturé, bleus/violets/magenta ; **jamais** le cyan allié
  (turquoise électrique) ni le corail-rouge des tirs ennemis. Lumière clé haut-gauche.
- **Technique** : PNG ; ChatGPT ne produit pas de vraie transparence (il **peint un damier**).
  → soit fond **noir pur** (nébuleuses, composées par clé de luminance/saturation), soit objet
  opaque sur fond clair uni (planète, détourée par flood-fill). Le canal alpha est reconstruit
  côté session principale.

## Livrables

- `assets/source/planet_hero.png` — source ChatGPT (planète, fond damier blanc). **Livré.**
- `assets/source/nebula_monument_a.png` — source ChatGPT (nébuleuse, fond damier noir). **Livré.**
- `assets/imported/backgrounds/planet_hero.png` — texture in-game (alpha détouré). **Livré.**
- `assets/imported/backgrounds/nebula_a.png` — texture in-game (alpha par clé saturation). **Livré.**
- `assets/source/nebula_monument_b.png` — source (nébuleuse violette). **À régénérer sur fond
  NOIR PUR** (la version livrée est sur damier blanc → cœur clair non récupérable).
- `assets/source/galaxy_distant.png` — optionnel. **À régénérer sur fond noir pur** (halo gris
  opaque sur la version livrée).

## Prompts de génération (ChatGPT, optimisés)

Voir le fichier de plan `~/.claude/plans/on-a-un-tr-s-adaptive-tiger.md` (section « Prompts
d'images — optimisés pour ChatGPT ») : couleurs en mots (pas de hex), transparence + PNG
explicites, fallback **fond noir pur** pour tout objet lumineux, bans cyan/corail en clair.

## Provenance

Quatre lignes ajoutées à `assets/licenses/ASSET_PROVENANCE.csv` (`*_src` = source ChatGPT,
`*_tex` = texture détourée ; `modified_by` documente la méthode de reconstruction alpha).

## Critères d'acceptation

- [x] Planète ronde (billboard), coin haut, ne stationne pas au centre.
- [x] Nébuleuse colorée présente, couloir de combat central lisible.
- [x] Aucun cyan allié ni corail ennemi dans le décor.
- [x] `./scripts/check.sh` vert ; coût GPU négligeable (+0.02 ms/frame mesuré).
- [x] Vérifié par capture in-game (aucun résidu de damier visible).

## Hors périmètre

- 2e variante de nébuleuse (`nebula_b`) et galaxie : en attente de régénération sur fond noir.
- Tuning fin des positions/vitesses de dérive : itérable dans `space_backdrop.tscn`.
