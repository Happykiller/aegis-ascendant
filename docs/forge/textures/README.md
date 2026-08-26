# Textures — le contrat d'expression de besoin

Ce dossier tient les **demandes de texture**, une par fichier, au format JSON normalisé.

> **Institué par [`ADR-0028`](../../decisions/ADR-0028-la-texture-est-une-etape.md)** : la texture
> est une **étape du process**, plus une permission. `ADR-0013` avait levé les interdits sans jamais
> instituer d'étape — trois ADR sur le sujet, et le mot « texture » n'apparaissait ni dans la charte
> créative, ni dans le gabarit de brief, ni dans la définition de l'agent `asset-forge`.

Il existe parce que les textures sont la **voie de l'opérateur** : `BRIEF-0085` écrit à la forge « ⚠️ PAS DE
TEXTURES — la matière de la surface vient de l'opérateur », et cette voie-là n'avait ni gabarit, ni
liste, ni contrat.

## Pourquoi un JSON et pas un prompt

> « Le point important est de **séparer les contraintes techniques de la description visuelle**.
> C'est ce qui évite les prompts ambigus du type "texture réaliste, tileable, vue en perspective,
> avec profondeur", où certaines exigences se contredisent. »
> — l'opérateur, 2026-08-26

La chaîne est en deux étages, et c'est délibéré :

```text
Besoin du jeu
      ↓
Expression de besoin normalisée JSON      ←  ce dossier, contrat STABLE
      ↓
Validation                                ←  les six règles ci-dessous
      ↓
Transformation en prompt ImageGen         ←  skill /asset-image, JETABLE
      ↓
Génération
      ↓
tools/derive-maps.py                      ←  normale, rugosité, AO, multiplication
```

**Le JSON est le contrat ; le prompt est jetable.** Le jour où la façon de rédiger un prompt change,
les fichiers de ce dossier ne bougent pas. C'est aussi pour ça que `x_prompt_fr` porte
`derived_from` : ce champ est une **sortie**, régénérable, et ne doit pas être édité à la main.

## Le schéma

Blocs, dans l'ordre : `texture_type`, `purpose`, `technical`, `world_scale`, `composition`,
`visual`, `data_semantics`, `lighting`, `constraints`, `integration_notes`.

Trois clés sont des **extensions du projet**, préfixées `x_` pour que le schéma générique reste
intact :

| Clé | Contenu |
|---|---|
| `x_delivery` | statut, priorité, chemin de dépôt, dérivées attendues, vérifications, ligne de provenance CSV prête à coller |
| `x_prompt_fr` | le prompt transformé, **dérivé** des champs ci-dessus |
| `world_scale.confidence` | `measured` ou `decided` — voir règle 6 |

## ⚠️ Les six règles de validation

Un fichier qui viole l'une d'elles ne part pas au générateur.

| # | Règle | Pourquoi — et ce que l'oubli a coûté |
|---|---|---|
| 1 | `resolution` ∈ **`1024x1024`**, `1536x1024`, `1024x1536` | **Jamais 2048** : on reçoit un 1024 agrandi, du détail inventé par l'interpolation. Ce sont les seuls formats natifs. Et le rendu final passe par le post-process rétro à **960×540**. *Coût de l'oubli : dix blocs de prompt repris (23/07/2026)* |
| 2 | `output_usage: "source_for_normal"` ⇒ demander une **hauteur en niveaux de gris** (clair = saillant) | Une « normal map » demandée donne une image violette **qui y ressemble**, aux gradients faux : le relief s'éclaire à l'envers et *ça a l'air correct*. `derive-maps.py` dérive |
| 3 | `transparent_background: true` **interdit** | On reçoit un **damier peint** dans une image RGB opaque (BRIEF-0028). Utiliser `pure_black` / `pure_white`, puis `tools/bg-key-alpha.py` |
| 4 | `tileable: true` se **mesure** | Un seamless demandé n'est pas un seamless obtenu : invisible en preview, évident en jeu. `derive-maps.py --check-tiling` doit dire OK |
| 5 | `color_palette.forbidden` contient **toujours** cyan `#3FD9E8` et corail `#FF5A3D` | Réservés au tir allié et au tir ennemi (`space_background.gdshader`, DA §6, bible *Lisibilité*). Un décor qui les emploie **vole leur lisibilité aux projectiles**. A déjà coûté une itération sur le bolide d'impact (`ADR-0027`) |
| 6 | `world_scale` est **réel ou déclaré** — jamais plausible | `confidence: "measured"` ou `"decided"` + `rationale`. Une échelle inventée cadre la densité de détail sur du vide : une feuille calée sur un chasseur de 2 m lit comme du bruit sur une forteresse de 20 m |

### Deux limites qui ne sont pas des règles

- **`grayscale` n'est pas un dogme.** `ADR-0013 §3` autorise la couleur **quand elle est motivée**
  (cristal, décalques, croûte émissive) ; `derive-maps.py` *avertit* seulement si l'entrée est
  colorée. Demander de la couleur là où elle sert, du gris partout ailleurs.
- **Une génération d'image ne garantit aucune propriété numérique stricte** — ni normale
  physiquement correcte, ni profondeur métrique, ni absence de couture au pixel. C'est la validation
  en aval qui les établit, jamais le prompt.

## 💡 Ce que `--mul` rend inutile

Avant de demander une carte d'albédo, vérifier qu'elle est vraiment nécessaire : `derive-maps.py
--mul` produit une **carte de multiplication** dérivée de la hauteur, où les creux valent moins de
1,0 et les surfaces neutres 1,0. Godot calcule `albedo = albedo_texture × albedo_color` : la teinte
du matériau reste, et **seuls les creux s'assombrissent** (mécanisme d'`ADR-0011`, en service dans
`scripts/fx/hull_detail.gd`).

⚠️ Ce que `--mul` ne peut pas faire : ce qui est **plus clair** que la surface — ejectas, marquages,
givre. Une multiplication ne dépasse pas 1,0. C'est le seul cas qui justifie une seconde génération.

## Nommage

`TEX-NNNN-<slug>.json`, numéro pris à la suite. La source générée porte
`<sujet>_<rôle>_<taille>.png` et va dans `assets/source/textures/<famille>/` — **toujours**, même si
elle sert telle quelle. Les dérivées sont produites par l'outil, jamais générées.

## Les demandes

| Fichier | Sujet | Statut |
|---|---|---|
| [`TEX-0001-moon-regolith-height.json`](TEX-0001-moon-regolith-height.json) | grain et petits cratères de la calotte lunaire | **à commander** |
| [`TEX-0002-asteroid-rock-height.json`](TEX-0002-asteroid-rock-height.json) | roche des trois astéroïdes | **à commander** |
| [`TEX-0003-moon-regolith-albedo.json`](TEX-0003-moon-regolith-albedo.json) | ejectas clairs de la lune | conditionnelle — `--mul` couvre le reste |
| [`TEX-0004-asteroid-rock-albedo.json`](TEX-0004-asteroid-rock-albedo.json) | variation d'albédo de la roche | conditionnelle |
| [`TEX-0005-bolide-incandescent.json`](TEX-0005-bolide-incandescent.json) | la tête du bolide qui brûle | **à commander** |
| [`TEX-0006-trainee-de-flamme.json`](TEX-0006-trainee-de-flamme.json) | son sillage filamenté | **à commander** |

⚠️ **TEX-0005 et 0006 sont des `sprite`, pas des `surface_tile`**, et c'est la première fois. La
raison est mesurée : la tête du bolide rend à **130 px** à l'écran, et tout ce qui est échantillonné
depuis une tuile de 1024 étalée sur 8 m de monde y arrive soit en dalle plate, soit en bouillie une
fois le bloom passé dessus. À cette taille, une image **autorisée à la taille d'affichage** bat
n'importe quelle dérivation. C'est un cas où la règle « une texture PBR se génère en une seule
carte » ne s'applique pas : ce n'est pas de la matière de surface, c'est un objet peint.

⚠️ **Les conditionnelles ne se commandent pas sur plan.** Elles se décident sur une capture regardée
(`ADR-0006`) : si les creux se lisent déjà, elles ajoutent du coût pour rien.
