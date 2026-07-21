# assets/reference/ — ce qu'on **regarde**

Aucun fichier d'ici ne finit dans le jeu. Rien n'y est lu par un outil, rien ne s'y écrit. On y
regarde pour décider — puis on produit ailleurs, en original.

`.gdignore`é : jamais importé par Godot.

| Dossier | Nature | Qui l'a produit | Statut IP |
|---|---|---|---|
| `concepts/` (8 planches) | planches de conception **du projet** | la forge (`asset-forge`), sur brief versionné | **originales** — nous en sommes les auteurs |
| `inspiration/` (10 planches) | cibles d'ambiance et de rendu | **tiers** (ChatGPT imagegen) | **sensibles** — voir ci-dessous |
| `DA.md` | la direction artistique — invariants visuels | projet | — |

La distinction n'est pas cosmétique : **elle a des conséquences juridiques.**

## `concepts/` — nos planches

Produites par la forge sur brief (`docs/forge/briefs/BRIEF-*.md`), elles décrivent nos propres
vaisseaux, structures et personnages. Ce sont les **références de design citées par les scripts
Blender** : `tools/blender/build_specter_9.py` renvoie à `concepts/specter_9_concept_sheet.png`.

Elles ne sont pas des assets pour autant — un concept sheet ne s'importe pas, il se regarde pendant
qu'on écrit la géométrie.

## `inspiration/` — planches tierces

Générées par IA, elles portent parfois des noms ou codes visuels de licences existantes (« Macross »,
« Raiden », « Valkyrie »). Elles servent d'**intention** — composition, densité, chaleur, profondeur,
palette — jamais de calque.

Leur histoire tient en deux ADR, et il faut connaître les deux :

- **ADR-0005** les avait mises en **quarantaine hors dépôt**, par prudence IP ;
- **ADR-0009** les a **réinstaurées et versionnées** ici : projet **personnel, non commercial, non
  distribué**, risque assumé par le propriétaire.

> ⚠️ **Si le projet devait être distribué un jour**, cette posture serait à revoir : il faudrait
> purger ce dossier de l'arbre **et de l'historique git**. C'est la raison d'être de la frontière
> entre `concepts/` et `inspiration/` — elle rend cette purge possible sans toucher à nos propres
> planches. Ne jamais mélanger les deux.

Le détail planche par planche — ce qu'on y observe et ce qu'on en retient — est dans
[`inspiration/REFERENCE_INDEX.md`](inspiration/REFERENCE_INDEX.md).

## Ce qui n'a rien à faire ici

Une texture répétable, un PNG détouré, un WAV : ce sont des **entrées de production**, elles vont
dans `assets/source/`. Trois textures de coque (`texture_*_seamless_2048.png`) ont vécu ici par
erreur alors qu'elles fabriquent `hull_detail_mul.png` — c'est exactement le mélange que cette
séparation existe pour empêcher.
