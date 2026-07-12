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
