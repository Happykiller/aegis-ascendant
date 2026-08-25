# Bonne pratique — regarder un asset avant de l'intégrer


## ⚠️ L'instrument de mesure fait partie du livrable

Le 2026-08-25, la forge a signalé de elle-même que le rastériseur « aire vue » **hérité** d'un
script précédent ne calculait pas de vraies coordonnées barycentriques : il rejetait le centre de
gravité d'un triangle sur deux et amputait jusqu'à 40 % des pixels d'une pièce. Conséquence : les
répartitions de matériaux de `BRIEF-0044-report.md` sont **fausses**, et personne ne l'aurait su —
un pourcentage plausible ne se vérifie pas tout seul.

Trois réflexes qui en découlent :

- **Un harnais de mesure recopié se relit**, il ne se réutilise pas de confiance. C'est du code, il
  a des bugs, et ses bugs produisent des chiffres qui **ont l'air justes**.
- **Un correctif d'instrument doit être PORTÉ**, ou son absence écrite noir sur blanc. Ici il ne
  l'a pas été (hors périmètre de la forge) : le rapport périmé porte donc un avertissement en tête.
- **Quand un chiffre publié devient faux, on le marque là où il est lu**, pas seulement dans un
  journal. Quelqu'un rouvrira ce rapport sans lire l'historique.

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

## Un correctif de brief ne se propage pas aux autres livrables du MÊME brief (23/08/2026)

Deux coques sorties de la même forge, dans la même session, avec le même défaut connu — et **une
seule corrigée**. Mesuré sur les `.glb` livrés :

    choir_mine.glb    33 surfaces, 33 UV   ✓
    null_maw.glb      36 surfaces,  0 UV   ✗

Le correctif (`_triangulate_ngons()`) avait été appliqué au script sur lequel le défaut avait été
découvert, et pas à l'autre. Aucune erreur, aucun test rouge.

**C'est un mode de panne de la DÉLÉGATION, pas de l'outil.** Un agent qui corrige un défaut le
corrige là où il l'a vu ; rien ne l'oblige à balayer les autres fichiers du même lot, et son
rapport dira en toute bonne foi que le problème est réglé — ce qui est vrai, pour un des deux.

**Donc : ne jamais clore un brief à plusieurs livrables sur un rapport global. Auditer CHAQUE
fichier séparément**, et sur la mesure, pas sur le rapport.

### ⚠️ Mesurer la BONNE propriété : le fichier ne dit pas ce que le moteur charge

Cette entrée a d'abord été écrite sur les **tangentes**, et c'était faux. Deux sessions l'ont
conclu ensemble à partir d'un comptage de `TANGENT` dans le JSON des `.glb`, et la conclusion
n'a pas survécu à la vérification suivante :

    needle_scout.glb        fichier :  0 TANGENT / 7    chargé par Godot : 7 / 7
    crescent_interceptor    fichier :  0 TANGENT / 7    chargé par Godot : 7 / 7
    choir_harvester         fichier :  0 TANGENT / 61   chargé par Godot : 61 / 61

**L'import fabrique les tangentes** (`meshes/ensure_tangents=true`, réglage identique sur toutes
les coques du dépôt). Le relief de ces coques n'était donc pas mort du tout.

**Ce qui est vrai, et qui n'est pas la même chose : les UV ne s'inventent pas.** Aucun importateur
ne peut deviner comment déplier une coque. Une surface sans `TEXCOORD_0` ne peut recevoir **aucune**
carte de détail — `HullDetail.apply()` n'a rien où plaquer. Et la sévérité n'est pas la même : ce
n'est pas un rendu dégradé aujourd'hui, c'est une **porte fermée pour demain**.

État réel du dépôt, mesuré une fois chargé : **quatre coques sur dix sans UV** — `choir_harvester`
0/61 (le mini-boss), `null_maw` 0/36 avant reforge, `crescent_interceptor` 0/7, `needle_scout` 0/7.
Saine : `pale_leviathan` 145/145.

```gdscript
# La mesure qui compte : ce que le MOTEUR a chargé, pas ce que le fichier contient.
var fmt := mesh.surface_get_format(i)
fmt & Mesh.ARRAY_FORMAT_TEX_UV     # les UV — le fichier fait foi, rien ne les reconstruit
fmt & Mesh.ARRAY_FORMAT_TANGENT    # les tangentes — reconstruites à l'import, ne rien en conclure
```

Le comptage dans le JSON du `.glb` reste utile (rapide, sans moteur), mais il répond à « qu'y
a-t-il dans le fichier », **jamais** à « de quoi le moteur dispose ». Pour les UV les deux
coïncident ; pour les tangentes, non.

⚠️ La leçon dépasse le cas : **une garde écrite sur la mauvaise propriété est pire qu'aucune
garde.** Le test « toute coque neuve porte ses tangentes » n'aurait jamais pu échouer — vacant, et
rassurant, pendant que le vrai défaut restait entier.

### Le corollaire : une articulation peut marcher et ne rien dire

Même session, autre mesure : l'ouverture mécanique des plaques d'une mine — 45°, validée par test,
mesurée sur le maillage — est **invisible à la taille de jeu**. Vue à 70° au-dessus du plan, sur un
objet de 46 pixels, avec le bloom par-dessus. La mécanique fonctionne, sa **lisibilité** ne paie
pas, et le télégraphe repose entièrement sur la couleur.

⚠️ Un test qui prouve qu'une pièce pivote ne prouve pas que le joueur le voit. C'est la même
frontière que « le rendu studio flatte » plus haut, appliquée au mouvement plutôt qu'au détail.

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

## ⚠️ Mesurer un `.glb` sans appliquer les transformations de nœuds donne un chiffre FAUX

Agréger les bornes (`accessors[].min/max`) de tous les maillages d'un `.glb` donne une enveloppe
en espace **local**. Si des pièces sont portées par des nœuds transformés, le résultat est
faux — et il est **plausible**, donc personne ne le questionne.

Vécu le 2026-08-25, et le chiffre faux est parti dans deux briefs de forge :

| Specter-9 | Largeur |
|---|---|
| Bornes agrégées en espace **local** | **1,29 m** ← faux |
| Enveloppe **monde**, transformations composées | **1,752 m** |

**+36 %.** Ses ailes sont portées par des nœuds transformés. Un décor d'intérieur dimensionné
sur 1,29 aurait été d'un tiers trop étroit — l'erreur exacte que ce brief existait pour
empêcher. Ce sont les **deux forges** qui l'ont relevée, chacune de son côté ; la session
principale l'avait écrite sans la vérifier.

Le même piège guette **dans le code** : `Node3D.position` est locale. `global_position` est
juste dans l'arbre, mais ne veut rien dire hors de l'arbre — le régime des tests. Composer les
transformations jusqu'à la racine du décor est juste dans les deux cas.

```python
# Il faut composer la chaine de parente, pas agreger les bornes.
def world_bbox(js):
    stack = [(i, IDENTITY) for i in js["scenes"][0]["nodes"]]
    while stack:
        i, par = stack.pop()
        M = mul(par, mat_of(js["nodes"][i]))     # translation/rotation/scale du noeud
        ...                                       # transformer les 8 coins, PAS le min/max brut
        for c in js["nodes"][i].get("children", []):
            stack.append((c, M))
```

## Un contrat de noms respecté ne prouve RIEN sur l'échelle

La coque du boss final livre `Ring_01..05` et `Tunnel_End` — les noms exacts que le document de
conception réclamait pour « cinq anneaux internes que le chasseur franchit ». Mesurés :
**0,24 à 0,33 m**, pour un chasseur de **2,46 m**. Elles existaient par le **nom**, jamais à
l'**échelle**, et **rien** ne l'a signalé : ni le compte de triangles, ni le contrat d'export,
ni le rendu — le puits n'est jamais vu de près dans le jeu.

**La règle qui en découle, et elle est bon marché** : toute planche de recette d'un décor ou
d'une coque porte **une vue avec le chasseur posé à l'échelle**, depuis son `.glb` réel et non
une maquette. C'est la vue qui aurait attrapé les anneaux de 30 cm, et elle coûte un rendu.
