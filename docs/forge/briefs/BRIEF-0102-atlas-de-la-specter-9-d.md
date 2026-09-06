# BRIEF-0102 — Déplier la Specter-9 D, pour qu'on puisse enfin la peindre

- **Statut** : livré
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-09-06
- **Source** : `assets/source/models/specter_9_d/` (régime `ADR-0048`)

## Objectif

Donner à la `specter_9_d` **une seule image pour toute sa coque**, sur laquelle une usure puisse
être posée à un endroit choisi. Aujourd'hui elle porte une feuille tuilée : tout ce qu'on y met se
répète partout, et c'est exactement ce qui la sépare de la `specter_9_b`.

Ce lot livre le **dépliage** et une **première cuisson** ; la peinture, elle, viendra ensuite —
par l'opérateur (`ADR-0028`) ou par nous.

## Contexte

### Le constat, dans les mots de l'opérateur

> « *On a un bel objet 3D pour la version D, mais qui manque de texture, de couleur, de patine,
> comme la version B.* »

Et sa formule vaut mieux que la mienne : **la B est simple de forme mais riche de peinture ; la D
est riche de forme mais pauvre de peinture.**

### Ce qui a déjà été fait, et pourquoi ça ne suffit pas

Les six cartes livrées avec le modèle étaient des **aplats** : albédo à ±2,3 %, normale à
**±2 sur 255**. Elles ont été réécrites (commits `d749b79` puis `22a26f4`) et portent désormais
une structure (joint de tôle, liseré, rivets) et une patine (deux champs doux tuilables, crasse
près des joints, désaturation de la peinture sale).

**Le gain est réel et il est mesuré** — amplitude d'albédo 12 → 73 niveaux, de normale 4 → 245.
Mais il bute sur une limite de nature : **une feuille qui se répète ne peut pas poser une coulure
à un endroit précis.** Sous les tuyères, sur le bord d'attaque, autour de la verrière — là où une
vraie coque se salit — il ne peut y avoir que le même motif qu'ailleurs.

### La cote qui commande tout le lot

Densité UV actuelle, mesurée sur le maillage : **0,831 tuile/m**. Une tuile couvre 1,20 m de
modèle, soit **11 pixels à l'écran** en jeu (coque à 2,46 m, 45,8 px/m physiques).

⚠️ **Un atlas change complètement cette arithmétique** : la coque entière tient dans une image.
À 2048² pour un vaisseau de 12,6 × 8,9 m, la densité utile est de l'ordre de **150 texels/m** —
deux ordres de grandeur au-dessus. C'est ce qui rend une coulure possible.

## Ce qu'il faut faire

### 1. Déplier les 406 pièces dans UN atlas

C'est la difficulté du lot, et elle est réelle. `ak.atlas_unwrap()` (`ADR-0047`) déplie **un**
objet ; il en faut un qui déplie **une collection** en pack commun, avec :

- des îlots **disjoints** — le garde de recouvrement d'`ADR-0047` s'applique (seuil proportionnel,
  5 pour 10 000 des texels couverts) ;
- une densité de texels **homogène** entre les pièces : une dérive de densité fait une coque
  nette d'un côté et floue de l'autre, et ça ne se voit qu'après la peinture ;
- les coutures **hors champ** autant que possible — la caméra plonge à 70°, donc le dessous est
  le bon endroit pour couper.

⚠️ **Les 406 pièces ne se valent pas.** Les 24 pétales de tuyère, les stabilisateurs de missile,
les rivets : personne ne peindra dessus. Regrouper ce qui mérite des texels (fuselage, ailes,
nacelles, dérives, verrière) et donner le reste à une zone commune est un **arbitrage attendu** —
le dire au rapport avec la part de l'atlas allouée à chaque famille.

### 2. Cuire une première image, pour qu'il y ait quelque chose à peindre PAR-DESSUS

`tools/bake-atlas.py` sait déjà cuire, depuis un `.glb` :

- **`specter_9_d_albedo.png`** — les couleurs lues dans le fichier, jamais recopiées dans l'outil ;
- **`specter_9_d_height.png`** — le relief, à passer à `tools/derive-maps.py` (`ADR-0013` : une
  normale se dérive).

⚠️ **Cette coque n'a pas de palette par facteurs** : ses quatre teintes vivent dans des textures
(`white/blue/red/metal_basecolor`) appliquées par matériau. L'outil devra donc lire **quel matériau
porte quelle face**, et non un `baseColorFactor`. C'est une extension de `bake-atlas.py`, pas un
outil neuf, et elle sert toutes les coques tierces à venir.

### 3. Rendre la peinture possible pour un humain

Livrer, en plus des cartes :

- une **planche de repérage** : l'atlas avec le nom des zones (nez, aile bâbord, nacelle tribord,
  dérive…), pour qu'on sache où l'on peint ;
- un **damier UV** rendu sur la coque, à la caméra du jeu, pour prouver que la densité est
  homogène et que les coutures tombent où on l'a dit.

## Texture (ADR-0028)

**L'atlas EST la texture, et ce lot le fabrique** — c'est le régime « atlas » d'`ADR-0047`, où la
carte REMPLACE la palette au lieu de la multiplier. Le tuilage vaut alors **1**, obligatoirement.

**Aucune demande `TEX-NNNN` n'est ouverte par ce lot** : il livre une image cuite depuis la
géométrie. La peinture qui viendra par-dessus — coulures, matricule 09, insignes — fera l'objet
d'une demande séparée, une fois qu'on aura la planche de repérage à lui donner.

**Dépliage attendu** : atlas packé, densité homogène, mesurée et rapportée en texels/m.

## Animation (ADR-0046 §6)

**La coque bouge, et le dépliage ne doit rien y changer.** Elle porte quatre clips glTF
(`Flight_Demo` 8 s, plus trois transitions) pilotant `CTRL | Wing L/R` et `CTRL | Nozzle L/R` :
ailes déployées, intermédiaires, repliées ; buses compactes puis étendues.

⚠️ **Un dépliage ne touche qu'aux UV** — mais un `join`, un `apply` de modificateur ou un
reparentage casserait le rig **sans qu'une erreur ne le dise**, et la coque sortirait figée. Les
noms des quatre contrôleurs, leur hiérarchie et les deux `MARKER | exhaust L/R` sont un contrat :
le moteur les lit. Le rapport doit **rejouer les quatre clips après réimport** et le dire.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/lib/aegis_kit.py` | `atlas_unwrap()` étendu à une collection, packée en commun |
| `tools/bake-atlas.py` | lecture des teintes **par matériau texturé**, pas seulement par facteur |
| `tools/blender/unwrap_specter_9_d.py` | notre transformation : ouvre la source, déplie, exporte |
| `assets/imported/models/ships/specter_9_d.glb` | la coque redépliée — géométrie et rig intacts |
| `assets/imported/textures/hull/specter_9_d_albedo.png` | l'atlas cuit |
| `assets/imported/textures/hull/specter_9_d_height.png` | le relief, à dériver |
| `docs/forge/output/BRIEF-0102-atlas.png` | planche de repérage des zones |
| `docs/forge/output/BRIEF-0102-report.md` | mesures, arbitrages, limites |

## Provenance

Mettre à jour **la ligne existante** `specter_9_d_hull` (ne pas en créer une seconde), et ajouter
une ligne par carte cuite. Y nommer la densité de texels obtenue, le recouvrement mesuré, et la
part de l'atlas allouée à chaque famille de pièces.

## Critères d'acceptation

- [ ] **Le rig survit** : les quatre clips rejoués après réimport, les quatre contrôleurs et les
      deux marqueurs présents, aux mêmes noms. ⚠️ C'est le critère qui prime : une coque figée ne
      se signale par aucune erreur.
- [ ] **Géométrie inchangée** : 413 nœuds, 406 maillages, 49 116 triangles. Ce lot ne redessine rien.
- [ ] **Densité de texels mesurée et homogène** — écart max entre familles donné au rapport ;
      au-delà d'un facteur 2 il faut le justifier.
- [ ] **Recouvrement d'îlots sous le seuil d'`ADR-0047`**, mesuré et rapporté.
- [ ] **`TEXCOORD_0` compté** dans le `.glb`.
- [ ] **Le damier UV est rendu à la caméra du jeu et REGARDÉ** (`ADR-0006`) : c'est la seule façon
      de voir une couture au mauvais endroit.
- [ ] La coque **habillée de l'atlas cuit** est capturée au bestiaire et comparée à l'état actuel.
      ⚠️ **L'atlas seul ne rend pas une coque belle** — mesuré le 2026-09-05 sur une autre coque,
      où la variance locale n'a pas bougé et où le rendu a été refusé. Il rend la peinture
      POSSIBLE. Ne pas promettre l'autre chose.

## Hors périmètre

- **La peinture elle-même** — coulures, matricule, insignes. Demande séparée, une fois la planche
  de repérage en main.
- **Toute retouche de forme.**
- **Le code de jeu** : le régime « atlas » de `HullDetailSet` existe déjà (`ADR-0047`) ; le câbler
  est à moi. Ne toucher à aucun `.gd`, `.tscn` ni `.tres`.
