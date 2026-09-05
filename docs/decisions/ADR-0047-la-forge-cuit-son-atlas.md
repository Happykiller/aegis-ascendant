# ADR-0047 — La forge cuit son atlas : une carte peut REMPLACER la palette

- **Date** : 2026-09-05
- **Statut** : accepté
- **Amende** : `ADR-0011 §2` et `ADR-0013` (l'atlas peint était réputé hors de portée),
  `ADR-0028` (la voie de l'opérateur reste, une seconde s'ouvre à côté),
  `ADR-0044 §4` (« les textures restent des feuilles répétables projetées »)

## Contexte

Mesuré le 2026-09-05, en cherchant pourquoi le jeu « fait jouet » : **sur les 50 textures
importées du dépôt, 49 sont des niveaux de gris ou des normal maps.** Aucune coque de
vaisseau ne porte d'albédo peint.

La cause n'est pas un oubli, c'est le mécanisme lui-même. `HullDetail` pose sa carte en
`albedo_texture` **par-dessus** la couleur de palette du `.glb` — Godot calcule
`albedo = texture × couleur`. Une telle carte creuse une rainure ; elle ne peut, **par
construction, jamais éclaircir**. Donc jamais peindre une bande, un filet, un matricule.

C'était le bon choix quand il a été fait : la palette gardait une source de vérité unique
et une feuille servait toutes les coques. Mais l'opérateur demande une livrée, et la
planche de référence en porte une depuis juillet 2026.

⚠️ **Et la piste alternative a été testée, puis écartée sur mesure.** Les réflexions
d'environnement — hypothèse sérieuse, puisque `AA_Trim` est à 0,85 de métallicité sans
rien à réfléchir — donnent un résultat **négatif et monotone** : le ciel aplatit la coque
sans produire une seule haute lumière. Détail dans `ADR-0045`.

Restait l'obstacle nommé par `ADR-0013` : « il ne sait pas peindre sur un layout UV
imposé, l'atlas peint par îlot reste hors de portée ». **Cette phrase visait la voie
imagegen**, et elle reste vraie pour elle. Elle ne dit rien d'un atlas **cuit par un outil
du dépôt**, depuis les UV du maillage lui-même.

## Décision

### 1. Une carte peut REMPLACER la palette, pas seulement la multiplier

`HullDetailSet` gagne un champ `albedo`. Quand il est posé, le jeu change de régime :

| Régime | La carte | Le tuilage |
|---|---|---|
| **feuille** (défaut, inchangé) | MULTIPLIE la palette du `.glb` | libre, répétable |
| **atlas** | REMPLACE la palette — `albedo_color` passe au blanc | **vaut 1**, obligatoirement |

⚠️ **Le tuilage à 1 n'est pas un réglage, c'est une condition.** Dans un atlas, chaque
texel a une **adresse** sur la coque ; un tuilage la déplace, et le matricule finirait sur
une aile. `validate()` le refuse, parce que le défaut serait autrement silencieux.

### 2. L'atlas est cuit par le dépôt, et il est DÉTERMINISTE

`tools/bake-atlas.py` produit, depuis le `.glb` seul :

- **`<coque>_albedo.png`** — les couleurs de palette **lues dans le fichier**
  (`baseColorFactor`), jamais recopiées dans l'outil : la palette garde une seule source
  de vérité, elle transite simplement par l'image ;
- **`<coque>_height.png`** — le relief en niveaux de gris, **à passer à
  `tools/derive-maps.py`**. `ADR-0013` ne bouge pas sur ce point : une normale se
  **dérive**, elle ne se génère pas.

**Les lignes de panneau ne sont pas inventées** : ce sont les arêtes du maillage dont
l'angle dièdre dépasse un seuil, projetées dans l'espace UV. Le dessin suit donc la
géométrie au lieu de la contredire.

### 3. Le choix numpy contre un bake Cycles est motivé par le déterminisme

Un bake Cycles échantillonne : sa reproductibilité dépendrait de la graine, du nombre de
fils, du débruiteur et de la version — quatre conditions dont une échappe au dépôt. La
génération numpy est **exacte par construction**. `--check` cuit deux fois et compare les
sha256, comme `build-hull.sh` le fait pour les coques.

### 4. Le dépliage en atlas entre au kit

`box_project_uv()` produit **volontairement** des îlots qui se recouvrent — sans
conséquence pour une feuille répétable, rédhibitoire pour de la peinture.
`ak.atlas_unwrap()` produit des îlots disjoints, packés dans le carré, et **mesure** son
recouvrement.

⚠️ **Il enveloppe `bpy.ops.uv.smart_project`, que le kit refusait par principe** — « son
résultat bouge d'une version de Blender à l'autre ». Argument de prudence, jamais mesuré.
Il l'a été : sur la coque réelle, deux exécutions rendent **le même sha256 des UV, au bit
près**, et la propriété a **survécu à la montée 4.5.11 → 5.2.1** sans une modification.
Ce qui la rend vraie : la version est épinglée et `-t 1` est forcé.

⚠️ **Le zéro absolu de recouvrement n'est pas atteignable, et c'est mesuré.** Plus on
coupe pour l'éviter, plus le packing s'effondre — jusqu'à ne lire que 6 % de l'atlas. Le
garde est donc **proportionnel** (5 pour 10 000 des texels couverts), calibré sur une
série, et il refuse toujours un îlot entier posé sur un autre.

## Ce qui ne change pas

- **La voie de l'opérateur d'`ADR-0028` reste entière.** Une feuille répétable demandée
  par un `TEX-NNNN` et générée hors du dépôt est toujours la façon normale d'obtenir de
  la matière. L'atlas est une **seconde voie**, pas un remplacement.
- **La palette du kit reste la source de vérité des teintes.** L'atlas la lit, il ne
  l'invente pas.
- **La normale se dérive** (`ADR-0013`), jamais ne se génère.
- **La règle du regard** (`ADR-0006`) : deux défauts de cet outil — un espace de couleur
  linéaire écrit en sRGB, et une rainure comptée deux fois — n'ont été trouvés **qu'en
  jeu**, jamais par un test.

## Conséquences

- Le contrat de `docs/forge/textures/README.md` gagne une troisième issue possible.
- La contradiction dormante entre `SPEC §24.4` (« héros : 2K à 4K ») et la règle 1 du
  contrat de texture (« jamais 2048 », motivée par un rendu à 960×540 qui n'existe plus)
  est **tranchée en faveur de la spec** : un atlas de coque se cuit en 2048².
- Le poids LFS n'est plus payé une fois pour toutes : un atlas se paie **par coque**.
- ⚠️ **Aucune campagne de rattrapage.** Les coques déjà livrées gardent leur feuille ;
  elles ne reçoivent un atlas qu'à l'occasion d'une reforge, jamais pour elles-mêmes.
