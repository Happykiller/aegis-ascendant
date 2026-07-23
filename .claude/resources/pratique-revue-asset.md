# Bonne pratique — regarder un asset avant de l'intégrer

## La règle

**Un livrable de la forge n'est pas un asset validé tant qu'il n'a pas été rendu et regardé.**

Un brief exécuté, une ligne de provenance et un fichier au bon endroit ne prouvent rien sur le
rendu. Avant d'intégrer un SVG livré par `asset-forge`, le **rasteriser et l'ouvrir** :

```bash
python3 -c "import cairosvg; cairosvg.svg2png(url='assets/source/…/x.svg', write_to='/tmp/x.png',
            output_width=512, output_height=512)"
# puis Read /tmp/x.png
```

## Ce que ça a coûté de ne pas le faire (12/07/2026)

`BRIEF-0015` avait livré six couches de parallaxe avec une spec de composition complète (ordre,
facteurs de déplacement, opacités). Tout était conforme sur le papier. Intégrées **sans être
regardées**, elles ont donné un tapis de losanges blancs et de pentagones gris — un rendu
objectivement **pire que le vide** qu'elles remplaçaient. Deux allers-retours de réglage perdus
avant de comprendre que le problème n'était pas le paramètre, mais l'asset.

## La cause profonde, lisible dans la provenance

Deux moyens de production coexistent dans `ASSET_PROVENANCE.csv`, et ils n'ont **pas le même
niveau** :

| `source_tool` | Nature | Verdict |
|---|---|---|
| `imagegen (OpenAI)` | peinture raster | **bon** — vaisseaux, boss, citadelle, planches de concept |
| `asset-forge (Codex)` → SVG | aplats vectoriels écrits à la main | **inutilisable pour le pictural** |

**Heuristique** : le SVG écrit à la main convient aux **formes fonctionnelles** (icônes, cadres
d'UI, bonus, emblèmes). Il ne convient **pas** au pictural (fonds, explosions, projectiles) : des
aplats à bords francs ne tiennent pas face au bloom.

Pour le pictural, deux voies : **imagegen** (dépend de l'opérateur) ou **procédural en shader**
(autonome, sans couture, réglable par uniformes). Voir `docs/decisions/ADR-0006`.

## Le rendu studio flatte ; le post-process rétro écrase le détail fin (20/07/2026)

Deux réalités de rendu, à ne pas confondre — un asset se juge dans **les deux**, et c'est la seconde
qui décide :

1. **`tools/render-hull.py` (Cycles, studio) flatte les coques** : éclairage trois points, pleine
   résolution, pas de post-process. C'est le bon outil pour vérifier la géométrie et l'orientation,
   mais il **survend** le rendu final. (Déjà noté ailleurs : les coques lisent plus sombre en jeu.)
2. **Le jeu passe tout par le post-process rétro** — `retro_post.gdshader` réduit à **960×540** puis
   `scanlines.gdshader`. Ce pipeline **plafonne le détail fin** : sur une petite coque, une texture
   de lignes de panneau se noie en bruit rayé, indiscernable des scanlines.

**Ce que ça a coûté** : reforge du Specter-9 avec feuille de détail. La v2 « plus visible » (rainures
à 0.22, plaques ×2,5) rendait la coque **grise et boueuse** en jeu alors qu'elle semblait correcte en
studio ; trois cycles export+deploy+capture pour retomber sur un réglage propre (rainures 0.45,
`uv1_scale` 0.6). Le studio ne montrait aucun de ces défauts.

**Conséquences à énoncer dans tout brief de coque** :

- **La géométrie porte l'essentiel de la lecture**, la texture n'est qu'une finition. Placer le
  budget de détail dans les volumes et les insets, pas dans une texture fine qui ne survivra pas au
  downsampling.
- **Juger en jeu, pas au studio** : `deploy-win.sh -- ++ --novsync --capture --capture-at=<s>`, puis
  recadrer le sujet et regarder. Ne pas valider une texture sur le seul rendu Cycles.
- Un détail qui n'est visible qu'à pleine résolution studio **n'existe pas** pour le joueur — même
  logique que la règle des 20° de BRIEF-0026, appliquée à la finesse au lieu de l'angle.

## Choisir la vue qui montre l'axe qu'on juge (23/07/2026)

« Juger en jeu » ne suffit pas : encore faut-il **la vue où la propriété qu'on règle est visible**.
Un même effet, correct ou raté, peut être indiscernable d'un écran à l'autre.

**Ce que ça a coûté** : la forme de la plume de réacteur (ADR-0017) a été jugée sur le **bestiaire**,
qui présente les coques de trois quarts avant. Le jet y part *en enfilade*, presque dans l'axe de la
caméra : sa longueur est écrasée par la perspective et son profil rendait un blob rond quelle que
soit la valeur réglée. Une itération complète de réglage — export, déploiement, capture, analyse —
faite sur une image qui ne pouvait pas répondre à la question posée.

**Les trois plans du jeu, et ce que chacun sait dire :**

| Plan | Angle | Bon juge de |
|---|---|---|
| Jeu (`--goto-graybox`) | quasi zénithal, 20° de la verticale | la lisibilité réelle, la taille relative au vaisseau |
| Accueil (défaut) | presque à l'horizontale, gros plan | **la forme** — silhouette, profil, dégradés |
| Bestiaire (`--goto-codex`) | trois quarts avant, coque qui tourne | le **volume** (ça tourne), les couleurs par camp |

Avant de lancer une capture : se demander **quel axe porte la propriété à juger**, et prendre le
plan qui ne l'écrase pas.

---

## Un contrat d'export valide pendant que la silhouette dérive

**Ce que ça a coûté (23/07/2026)** : la reforge de la coque du Pale Leviathan (BRIEF-0040) a passé
**tous** ses critères techniques — contrat de noms à 30 pièces, pivots, UV, tangentes, déterminisme
byte-identique, dix dégagements mesurés à fond de course et bloquants. Et la coque **ne ressemblait
pas à ses planches** : disque radialement symétrique là où la référence montre un croissant
asymétrique, rosette plate au lieu d'une sphère, cônes courts au lieu de longs dards. Un brief
correctif entier (BRIEF-0041) pour rattraper.

`ak.export_hull()` vérifie la boîte englobante, le budget de triangles, les matériaux, le pivot et
les points d'attache. **Aucune de ces cinq mesures ne parle de la forme.** Une coque peut être
parfaitement conforme et méconnaissable — c'est le même angle mort que le dégagement d'un volet, qui
ne se voit pas sur une pose fixe (`pratique-detail-en-fraction-de-corde.md`).

### La contre-mesure : un critère d'acceptation « côte à côte, panneau par panneau »

Un brief de coque doit exiger la planche de recette **posée à côté de la planche de référence**, et
un verdict **par écart nommé** dans le compte-rendu — pas un « conforme ». Nommer les écarts dans le
brief les rend vérifiables ; les laisser implicites les rend invisibles.

### Et la mesure qui objective « ça ne ressemble pas »

« Le rendu est délavé » ne se défend pas. La **répartition des sommets par matériau**, si :

```python
# lire le JSON du .glb, cumuler accessors['count'] par materiau
AA_Greeble 32.5% | AA_Emissive_Engine 28.7% | AA_Trim 14.9% | AA_Panel 11.3% | AA_Hull 11.0%
```

Deux faits en tombent, tous deux actionnables :

- **`AA_Emissive_Engine` à 28,7 %.** Un émissif **ne reçoit pas la lumière** : il rend plat et clair
  quelle que soit l'orientation de la surface. À près d'un tiers de la coque, il noie le modelé —
  c'est le défaut qu'ADR-0013 relève déjà pour le noyau de la citadelle, « une goutte blanche
  uniforme ». Repère : les planches montrent le magenta en **veines entre les plaques**, quelques
  pour cent. Au-delà de ~10 %, ce n'est plus un accent, c'est une livrée.
- **`AA_Hull` à 11 % contre 32,5 % de greeble.** Trois fois plus de machinerie que de blindage : la
  silhouette lit « machine » là où la référence lit « carapace ».

Le même relevé sert de **critère chiffré** au brief correctif, au lieu d'un adjectif.
