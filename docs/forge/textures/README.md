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

### ⚠️ Le fond se demande EN PREMIER, et se refuse plutôt que se rattraper

Relevé le 2026-08-26 : les images revenaient **avec un fond** dès que le sujet n'occupait pas tout
le cadre, obligeant à une seconde passe. La consigne était pourtant là — mais **enterrée à la fin**,
dans « Éviter absolument ». Un générateur pondère ce qu'il lit **en premier**.

Deux corrections, appliquées à tous les `x_prompt_fr` :

1. **La consigne de fond ouvre le prompt**, avant même le sujet.
2. **Elle nomme les intrus**, parce que « fond noir » ne les interdit pas : dégradé, vignettage,
   halo de fond, étoiles, nébuleuse, atmosphère, sol, décor.

**Le contrôle** : les quatre coins doivent être à **0-2 sur 255**. Au-dessus, le générateur a ajouté
un fond — **le renvoyer plutôt que de le rattraper**.

#### ⛔ Et ne JAMAIS demander un détourage pour un élément volumétrique

Le rattrapage courant (« supprimez l'arrière-plan, contours nets et lisses, fond transparent ») est
acceptable pour un **objet solide** — une tête de bolide a un bord défini.

Il est **catastrophique pour une bouffée, une flamme, un nuage** : leur bord doit se **dissoudre
progressivement dans le rien**. Un détourage à contour net leur coupe la lueur au ras et rend
exactement le **carton** que la règle « une surface se texture, un volume se peuple » cherche à
éviter.

Pour ceux-là, la recette du dépôt est meilleure : fond noir + `bg-key-alpha.py --mode black`, qui
reconstruit un alpha **doux** dérivé de la luminance et préserve le dégradé de disparition. Si un
damier a malgré tout été peint, `--mode sat` est le rattrapage (moins propre, résidu possible).

## ⚠️ Le plancher de MODULATION — ce que le rendu rétro détruisait, quoi qu'on demande

> ⛔ **PÉRIMÉ DEPUIS `ADR-0045` (2026-09-05).** Le post-process rétro a été **retiré du dépôt** :
> plus de grille 960×540, plus de postérisation à 20 niveaux, plus de scanlines. Les deux maillons
> qui fabriquaient ce plancher n'existent plus, et **la règle des ~6 niveaux de gris ne s'applique
> plus**. La section reste ici parce qu'elle documente une méthode de diagnostic qui, elle, garde
> toute sa valeur : quand un détail est invisible alors que la chaîne est juste, **mesurer l'aval**
> avant d'accuser la texture. Les chiffres, eux, sont ceux d'une chaîne qui n'existe plus.
> La résolution de source est à rouvrir en même temps (règle 1 « jamais 2048 » — voir `ADR-0046`).

Relevé le 2026-09-04, en mesurant pourquoi la maille hexagonale de `TEX-0015` était **invisible**
sur le panneau de bouclier de la Citadelle alors que toute la chaîne était juste.

La chaîne de texture était **correcte à 1 % près** : pas de maille mesuré à 28,4 px à l'écran pour
28,6 prédits, échelle UV juste, mipmaps activées. Et pourtant : rien. La cause est **en aval**, et
elle borne tout ce que ce contrat peut demander :

| Maillon | Ce qu'il fait | Mesuré |
|---|---|---|
| `retro_post.gdshader` | accroche l'image à `target_res` | **960 × 540** — le panneau de 152 px n'en fait plus que 76 |
| `levels = 20.0` | postérise | pas de **12,75 niveaux de gris** ; le panneau ne contient QUE 204 / 217 / 229 / 242 / 255 |
| la maille | ce qu'elle module | **0,83 niveau** — un quinzième d'une marche |

⚠️ **UN DÉTAIL DONT LA MODULATION EST SOUS ~6 NIVEAUX DE GRIS N'EXISTE PAS DANS CE JEU.** Il ne
franchit pas une marche de postérisation. Le tramage de Bayer le porte encore *statistiquement* —
c'est pourquoi il se **mesure** au spectre — mais l'œil ne le voit pas, et aucun réglage de la
carte, de l'UV ou de l'import n'y change quoi que ce soit.

⚠️ **ET LA SATURATION MANGE UN CANAL À LA FOIS.** Sur ce même panneau le rouge était écrêté sur
52 % de l'aire, avec **deux valeurs en tout** : il ne transportait plus aucune texture. Une carte
posée sous une émission forte perd ses canaux un par un, le plus saturé d'abord.

**Ce que ça change pour une demande** : `readability_requirements` doit raisonner en **contraste**,
pas seulement en pixels. « 9 à 18 px par maille » était vrai et insuffisant — la maille faisait
29 px et ne se voyait pas. La bonne question est : *de combien de niveaux de gris ce détail
module-t-il, une fois l'émission appliquée ?* Sous six, ne pas le demander.

⚠️ **Le corollaire est une économie.** Un détail invisible est une carte payée pour rien. Avant de
demander de la finesse, vérifier qu'elle a la place de vivre : une surface petite, très émissive
et postérisée à 20 niveaux ne porte que des **aplats et des silhouettes** — ce que la consigne 19
du redesign dit déjà pour la géométrie, et qui vaut aussi pour la matière.

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
| [`TEX-0005-bolide-incandescent.json`](TEX-0005-bolide-incandescent.json) | la tête du bolide qui brûle | ✅ livrée, intégrée |
| [`TEX-0006-trainee-de-flamme.json`](TEX-0006-trainee-de-flamme.json) | son sillage filamenté | ✅ livrée, intégrée |
| [`TEX-0007-bouffee-de-poussiere.json`](TEX-0007-bouffee-de-poussiere.json) | **un élément** de particule pour l'onde d'impact | **à commander** |
| [`TEX-0008-champ-du-porteur.json`](TEX-0008-champ-du-porteur.json) | le champ du Shield Carrier | **à commander** |
| [`TEX-0017-specter-borde-composite.json`](TEX-0017-specter-borde-composite.json) | peau de bordé : plaques, lignes de panneau, rivets, trappes. ⚠️ Demandée pour le Talvern (`ADR-0044`), **coque annulée** — la carte, elle, n'a rien de propre à elle | ✅ **livrée** 2026-09-05, déposée en source, **non câblée** |
| [`TEX-0018-specter-mecanique-de-baie.json`](TEX-0018-specter-mecanique-de-baie.json) | fond de baie : tuyauteries, boîtiers, vérins | ✅ **livrée** 2026-09-05, rattrapée (fondu 48 px), **non câblée** |
| [`TEX-0019-specter-metal-de-tuyere.json`](TEX-0019-specter-metal-de-tuyere.json) | métal de tuyère, lamelles horizontales → anneaux une fois enroulées | ✅ **livrée** 2026-09-05, rattrapée (fondu 96 px), **non câblée** |

## ⚠️ Une surface se texture. Un VOLUME se peuple.

Relevé par l'opérateur le 2026-08-26, et c'est la règle qui manquait à ce contrat :

> « avoir des textures pour des surfaces je trouve ça normal et bien, mais pour des effets de
> nuage, particule, comme la traînée, jet de régolithe à l'impact, flammes, etc, je veux pas voir
> une texture plate et moche genre carton »

| Nature | Technique | Ce que la texture devient |
|---|---|---|
| **Surface** — lune, rochers, coque, tête du bolide | une image sur la géométrie | l'habillage d'une forme qui existe déjà |
| **Volume** — poussière, flamme, braises, éjectas | un **système de particules** | **un ÉLÉMENT** répété des dizaines de fois |

Un effet volumétrique peint sur **un seul quad** est un carton : ni profondeur, ni parallaxe, ni
variation dans le temps. Il ne tient que vu de face et en mouvement rapide, et s'effondre dès qu'on
le regarde. Le volume vient du **nombre et de la dispersion**, pas de l'image.

**Conséquence sur la rédaction d'une demande** : pour un volume, ne jamais demander l'effet entier.
Demander **une bouffée**, **une braise**, **un éclat** — neutre, sans bord, sans direction propre.
Et poser le test qui tranche : *répétée cinquante fois à des tailles et rotations différentes,
reconnaît-on le motif ?* Si oui, elle est trop typée.

Le dépôt a déjà le motif technique : `scripts/fx/vfx_explosion.gd` (étincelles + débris en
`GPUParticles3D`), avec son piège documenté — `emitting` retombe à `false` dès la salve **émise**,
pas éteinte.

⚠️ **Et la règle ne s'applique PAS à tout** : `TEX-0008` (le champ du porteur) est une **frontière**,
pas un volume. Un panneau y est correct — et même souhaitable, puisque son bord doit rester lisible
au pixel près.

⚠️ **TEX-0005 et 0006 sont des `sprite`, pas des `surface_tile`**, et c'est la première fois. La
raison est mesurée : la tête du bolide rend à **130 px** à l'écran, et tout ce qui est échantillonné
depuis une tuile de 1024 étalée sur 8 m de monde y arrive soit en dalle plate, soit en bouillie une
fois le bloom passé dessus. À cette taille, une image **autorisée à la taille d'affichage** bat
n'importe quelle dérivation. C'est un cas où la règle « une texture PBR se génère en une seule
carte » ne s'applique pas : ce n'est pas de la matière de surface, c'est un objet peint.

⚠️ **Les conditionnelles ne se commandent pas sur plan.** Elles se décident sur une capture regardée
(`ADR-0006`) : si les creux se lisent déjà, elles ajoutent du coût pour rien.
