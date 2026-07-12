# ADR-0006 — Fond spatial procédural plutôt que couches de parallaxe vectorielles

- **Date** : 2026-07-12
- **Statut** : accepté (arbitrage joueur en session de test)

## Contexte

Le retour de test était double : la zone de jeu était encadrée d'un **carré cyan** et
l'environnement paraissait **vide**. Le carré était de l'échafaudage graybox (quatre boîtes
émissives `EdgeTop/Bottom/Left/Right` matérialisant les bornes), et le fond un shader
procédural minimal (nébuleuse fbm ténue + trois couches d'étoiles) sans structure lisible.

`BRIEF-0015` avait pourtant livré **six couches de parallaxe** (`assets/source/backgrounds/`)
avec une spec de composition complète (ordre, facteurs de déplacement, opacités). Elles ont
été intégrées à titre d'essai : import, shader de composition six textures, tuilage miroir,
défilement différentiel. Le pipeline fonctionne, mais **le rendu est mauvais**.

La cause est une différence de moyen de production, visible dans la provenance : les planches
de concept que l'on veut égaler viennent d'`imagegen (OpenAI)` — de la peinture raster — tandis
que les couches de parallaxe ont été **écrites à la main en SVG** par Codex. Ce sont des aplats
géométriques : les « croiseurs » sont des losanges blancs, les « débris » des pentagones gris.
Correctement mises à l'échelle, elles saturent l'écran de polygones répétés en miroir et se
battent avec le vaisseau et les projectiles. Aucun réglage d'opacité ou de tuilage ne comble
cet écart de nature.

Trois voies étaient ouvertes : (a) panorama peint généré à l'imagegen, (b) shader procédural
haut de gamme, (c) base procédurale + éléments peints. La voie (b) a été retenue.

## Décision

- Le carré cyan est **supprimé** : les bornes de jeu ne sont plus matérialisées à l'écran.
- Le fond est un **shader procédural de seconde génération** (`shaders/space_background.gdshader`) :
  nébuleuse en *domain warping* (fbm réinjecté dans ses propres coordonnées, d'où des volutes
  filamenteuses au lieu d'un flou isotrope), voiles de poussière qui **soustraient** de la
  matière, quatre couches d'étoiles en parallaxe, occlusion des étoiles par les nuages denses.
- Les **six couches de `BRIEF-0015` ne sont pas intégrées** et restent en `assets/source/`
  (non importées). Leur spec de composition (`docs/forge/output/space_parallax_layers.md`)
  reste valable si l'on repasse un jour à un fond raster peint.
- Contraintes de lisibilité tenues (palette normative) : fond froid et désaturé, **jamais** le
  cyan `#3FD9E8` réservé au tir allié ni le corail `#FF5A3D` réservé au danger ennemi ; tiers
  central volontairement assombri (`center_calm`) là où se lit le combat.

## Conséquences

- **Aucune dépendance à un outil de génération d'images** pour le décor : le fond est du code,
  il se règle par uniformes, ne se tuile pas, et n'a ni couture ni répétition visible.
- **Coût mesuré : 0,60 ms de GPU par image** (0,755 ms avec le fond contre 0,155 ms sans),
  soit 3,6 % du budget d'une image à 60 Hz. Acceptable sur la cible ; à re-mesurer si la
  résolution ou le nombre d'octaves augmente.
- Le décor reste **abstrait** : pas de structures peintes (station, croiseurs, planète).
  Si le besoin s'en fait sentir, la voie (c) reste ouverte — éléments peints dérivant
  au-dessus de cette base procédurale, produits via un brief forge + imagegen.
- **Corollaire méthodologique** : un brief forge dont le rendu final n'a jamais été vu en jeu
  n'est pas un asset validé. Le SVG écrit à la main convient aux formes fonctionnelles (icônes,
  cadres d'UI) et non aux fonds picturaux.

## Vérification

- Rendu contrôlé par capture d'écran depuis WSL (`--capture`), sans intervention manuelle.
- `RenderingServer.viewport_get_measured_render_time_gpu` est désormais imprimé par le helper
  de capture : le **FPS d'un lancement automatisé n'est pas exploitable** (Windows étrangle la
  présentation quand la session n'est pas affichée — relevés absurdes de 2 à 17 FPS), alors que
  le temps GPU par image reste fiable.
