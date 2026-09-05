# BRIEF-0100 — Le kit de tourelles reforgé : trois classes, et du détail qui tient

- **Statut** : livré
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-09-05
- **Planche cible** : `assets/reference/concepts/tourelles_lourdes_concept_sheet_2026-09-05.png`
- **Recettes à porter** : `resources/gpt_models/tourelle-lourde_v1/build_turret.py` (+ `geometry.py`)

## Objectif

Reforger `tools/blender/build_turret_kit.py` pour que les tourelles du Long Cortège atteignent
la planche : **trois classes** (légère, standard, lourde) au lieu de deux, et un traitement de
surface qui existe en géométrie. Le script reste la source (`ADR-0008`), la palette reste celle
du Chœur Nul, et le contrat de pièces que le moteur assemble ne change pas de vocabulaire.

## Contexte

### Ce que l'opérateur a constaté, et ce que la mesure a confirmé

« *La forge n'arrive pas assez près des concepts fournis.* » Vérifié en jeu le 2026-09-05, à la
caméra du survol, tronçon 2, t = 16,5 s : notre tourelle se lit comme un bloc gris lisse, deux
tubes fins et un point magenta. Un modèle tiers monté au même endroit, dans le même moteur, avec
le même éclairage, lit avec ses joints, ses modules blindés et ses arêtes claires.

**Le moteur n'est pas en cause.** L'écart est dans la géométrie.

### La cote qui manquait, et personne ne l'avait relevée

| | notre kit assemblé | planche, classe lourde |
|---|---|---|
| Longueur | **5,2 m** | 10,0 m |
| Hauteur | **1,9 m** | 4,2 m |

**Le jeu n'a pas de tourelle lourde.** Notre plus grosse se situe entre la *légère* et la
*standard* de la planche. Les deux échelles du code (`TurretScale { HEAVY, LIGHT }`) sont un
rapport 1 à 0,5 sur une seule géométrie — pas trois classes.

### ⚠️ Le budget actuel est justifié par une chaîne de rendu qui n'existe plus

`build_turret_kit.py` écrit, en toutes lettres, sous « OÙ LE BUDGET A ÉTÉ DÉPENSÉ » :

> « *le post-traitement rétro rend à 960x540, soit 23 px/m sur la coque, et toute géométrie plus
> fine que 9 cm est moyennée puis disparaît* »

`ADR-0045` a **supprimé ce filtre du dépôt** le 2026-09-05. La densité réelle mesurée est de
**45,8 px/m**. Ce paragraphe est donc faux, et c'est lui qui a plafonné la tourelle à six
primitives. **Il doit disparaître du fichier avec la reforge** — le laisser rejustifierait la
platitude au prochain passage.

### Ce qu'on a mesuré du modèle poussé, et pourquoi on le prend

Son `build_turret.py` a été rejoué dans un bac à sable, sur notre Blender 5.2.1 épinglé, `-t 1` :
il **reproduit sa livraison au bit près** (`sha256 86fbaf62…`). Ce n'est pas une boîte noire :
c'est un générateur complet et déterministe, du même régime que le nôtre.

⚠️ **On prend ses RECETTES, pas ses fichiers.** Ni son `.glb`, ni ses matériaux, ni ses cotes
telles quelles. Le test en jeu a montré deux régressions qu'un copier-coller aurait importées :
sa base de 3,62 m de rayon **déborde de la coque**, et sa palette graphite chaud lit comme **une
autre faction** à côté du violet-anthracite du Chœur Nul.

## Ce qu'il faut porter, recette par recette

Lire `resources/gpt_models/tourelle-lourde_v1/build_turret.py`. Les quatre recettes qui font
l'écart, et qu'aucune n'est chère :

1. **Le socle est fait de modules, pas d'un disque.** 24 secteurs blindés radiaux, chacun avec
   son panneau d'accès sur le plateau, sa tôle en retrait sur le pourtour, son verrou et ses deux
   boulons. C'est ce qui fait lire « machine » plutôt que « jeton ». Chez eux : lignes 74-105.
2. **Les plaques sont séparées, et leurs joints sont bordés d'une arête claire.** Une plaque
   posée, un retrait sombre derrière, un liseré fin en matériau poli sur le bord. ⚠️ **C'est la
   dépense la plus rentable de tout le fichier** : le liseré accroche la lumière clé à n'importe
   quelle distance — exactement l'argument que notre propre kit fait déjà pour ses chanfreins,
   et qu'il n'a appliqué qu'aux grandes arêtes.
3. **Les tubes sont chemisés en gradins**, du plus large à la culasse au plus étroit à la bouche,
   avec une bouche **réellement creuse** (lèvre, chemise, alésage sombre en retrait).
4. **Le magenta est réduit à des fentes.** Jamais une surface, jamais un halo : des traits de
   2 cm. C'est la règle 4 de la planche (« *le magenta signale l'énergie, pas le volume* »).

## Contraintes

### Palette — la nôtre, et la correspondance est établie

`ak.set_faction(ak.FACTION_NULL_CHOIR)`, sept slots, **aucun matériau nouveau**. Leurs huit
matériaux se replient sur nos sept sans perte :

| leur matériau | notre slot | pourquoi |
|---|---|---|
| `dark weathered armor` | `AA_Hull` | la masse blindée |
| `warm graphite panels` | `AA_Panel` | les plaques rapportées |
| `deep graphite recesses` | `AA_Greeble` | les creux et les joints |
| `rubbed titanium edges` | `AA_Trim` | **le liseré** — métallicité 0,85 chez nous contre 0,77 chez eux, l'effet est le même |
| `recoil piston steel` | `AA_Trim` | même famille ; ne pas créer un huitième slot |
| `unlit bore interior` | `AA_Greeble` | l'alésage |
| `restrained magenta energy` | `AA_Emissive_Engine` | `#D93D9C`, c'est **exactement** notre magenta |
| `serial markings` | `AA_Marking_Red` | usage **très limité** (la palette le dit) — ou rien |

⚠️ **Ne pas toucher `MATERIAL_ORDER` ni `_MATERIAL_SPECS`.** L'index d'un matériau est stable sur
toutes les coques du dépôt ; y ajouter un slot les reforgerait toutes.

### Les trois classes — mêmes blocs, trois échelles

C'est ce que la planche demande elle-même (« MODULES PARTAGÉS — MÊMES BLOCS. TROIS ÉCHELLES »),
et c'est déjà l'architecture du kit. **Ne pas la remplacer** : le moteur compose dix-sept
tourelles à partir des pièces, et cette variété est un livrable.

| Classe | Longueur | Hauteur | Tubes |
|---|---|---|---|
| Légère | 3,5 m | 1,6 m | 1 |
| Standard | 6,5 m | 2,8 m | 2 |
| Lourde | 10,0 m | 4,2 m | 2, longs |

⚠️ **LA LOURDE EST BORNÉE PAR LA COQUE, PAS PAR LA PLANCHE, ET C'EST À MESURER.**
`TURRET_FOOTPRINT_R = 2,08 m` (dans `build_long_cortege.py`, revérifié par le kit à chaque build)
est le rayon de l'emprise que le kit pose sur la peau. Sur ce diamètre de 4,16 m, le pourtour
accuse déjà **jusqu'à 0,683 m de dénivelé** aux dix-sept emplacements. Une emprise plus large
enjambe davantage de chine.

**La mission doit donc trouver le plus grand rayon d'emprise qui reste posable, et le dire au
rapport** — pas supposer que 10,0 m de long tiennent. Si la lourde n'entre qu'aux tronçons 4-5,
c'est un résultat valable et cohérent avec le niveau (« de plus en plus massives ») : le dire.
Si elle n'entre nulle part à 10 m, **réduire la classe et écrire la cote obtenue**. Une lourde à
8,5 m qui se pose vaut mieux qu'une lourde à 10 m qui flotte.

### Le contrat avec le moteur — il ne change pas

Les huit pièces gardent **leurs noms, leurs origines et leurs repères** : `turret_pad`,
`turret_anchor_skirt`, `turret_ring`, `turret_body`, `turret_barrel`, `turret_barrel_short`,
`turret_service_box`, `turret_pipe`. Les pièces neuves s'ajoutent, aucune ne se renomme.

⚠️ **`_assert_on_axis()` reste, et il doit rester rouge s'il échoue.** L'origine de `turret_ring`
et de `turret_body` est sur l'axe de rotation au micron : sinon la tourelle balaie en décrivant
un cercle au lieu de pivoter, et **ça ne se voit qu'en jeu, en mouvement**.

### Le détail va dans le MAILLAGE, pas dans le nombre de pièces

Leur tourelle coûte **465 maillages**. La nôtre en pose 6 à 8 par tourelle, dix-sept fois. Un
kit à 465 pièces multiplierait les instances par soixante. Le détail se fusionne donc dans les
pièces existantes ; le nombre de pièces posées par tourelle ne doit pas augmenter de plus de
deux.

**Le budget de triangles n'est plus un critère d'acceptation** (`ADR-0044` l'a déjà retiré pour
une coque). Quatre relevés GPU du 2026-09-05 (1,037 / 1,209 puis 1,800 / 0,765 ms sur RTX 4080)
sont dominés par la dispersion : ils n'établissent **aucun surcoût**, et n'en excluent aucun.
Dépenser librement, mesurer, et **rapporter le compte réel**.

### Déterminisme

`./scripts/build-hull.sh --check turret_kit` doit dire zéro octet divergent. Aucun aléa, aucun
`random`, aucune dépendance à l'ordre d'un `set` Python. ⚠️ Leur script itère sur
`set(asset.objects)` : **ce motif ne se porte pas tel quel** — l'ordre d'un `set` n'est pas
garanti d'une exécution à l'autre.

### IP

Création originale. La planche est **la nôtre** (fournie par l'opérateur pour ce projet). Aucun
nom, silhouette ou marquage d'une licence tierce. Le matricule sérigraphié de leur modèle
(`LC / CITADELLE / 03`) ne se recopie pas : s'il y a un marquage, il est à nous.

## Texture (ADR-0028)

**Aucune, et voici pourquoi.** Le Long Cortège entier est en PBR par facteurs, sans une seule
image : `long_cortege.glb`, `turret_kit.glb`, `spine_kit.glb` et `citadel_kit.glb` portent zéro
`baseColorTexture`, et **le harnais d'audit échoue le build si l'une apparaît**. Le niveau 2 n'a
pas de chaîne de texture — lui en ajouter une pour la seule tourelle créerait une pièce qui ne
ressemble à rien d'autre autour d'elle.

C'est aussi ce que la mesure autorise : dans le modèle poussé, la carte de métal usé est un voile
discret ; **l'écart de lecture vient de sa géométrie**, et c'est elle qu'on porte. La matière
peinte reste une décision ouverte, à prendre pour le niveau entier ou pas du tout.

**Dépliage attendu** : `ak.box_project_uv()` à la même densité que le kit actuel (0,12 tuile/m,
valeur à relire dans le fichier et non à recopier d'ici). `TEXCOORD_0` **compté** dans le `.glb`,
jamais supposé — trois coques du dépôt sont sorties sans UV et le défaut est totalement muet.

## Animation (ADR-0046 §6)

**La tourelle bouge, et une seule famille est pilotée par le jeu.**

| Famille | Axe | Pilotée par | Où |
|---|---|---|---|
| La tête tournante | lacet, **Y** | la visée du joueur, 42 °/s (`cortege_turret.gd`) | `turret_ring` + `turret_body` + tubes, montés sous un nœud `Rotator` créé **par le moteur** |

⚠️ **Le kit ne livre AUCUNE animation, et c'est délibéré.** Il livre des pièces à l'identité,
dans leur repère ; c'est le moteur qui les compose et qui fait tourner le nœud intermédiaire.
Rien ne se cuit en images clés ici — il n'y a pas de pilote Blender à cuire.

**Ce que ça impose quand même à la géométrie**, et c'est tout l'objet de `ADR-0046` §3 :

- l'origine de toute pièce **montée sur la partie tournante** est sur l'axe de rotation ;
- une pièce d'appareillage (`turret_service_box`, `turret_pipe`) reste **ancrée**, jamais sur la
  tête — sinon les conduites tourneraient avec les canons ;
- le socle doit avoir une **cuvette** assez profonde pour que la couronne y soit *logée* et non
  *posée* : c'est ce qui rend la rotation lisible d'un coup d'œil.

**Hors périmètre de ce brief, et volontairement** : l'élévation et le recul, que le modèle poussé
gréé en `CTRL | Elevation` et `CTRL | L/R recoil`. Ce sont deux familles de plus, elles demandent
un pilote côté moteur qui n'existe pas, et les mélanger à une reforge de forme rendrait
impossible de savoir laquelle des deux a fait la différence. **Prévoir la place**, ne pas la
gréer : que la géométrie du berceau n'interdise pas d'y revenir.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `tools/blender/build_turret_kit.py` | le générateur reforgé — **le fichier existant est réécrit**, pas doublé |
| `assets/imported/models/backgrounds/turret_kit.glb` | le kit régénéré |
| `docs/forge/output/BRIEF-0100-planche-tourelles.png` | planche de recette, produite par le **même script** (`-- --plate`) |
| `docs/forge/output/BRIEF-0100-report.md` | mesures, choix, limites |

## Provenance

Mettre à jour **la ligne existante** `turret_kit` de `assets/licenses/ASSET_PROVENANCE.csv` (ne
pas en créer une seconde : c'est une reforge, comme `BRIEF-0084` l'a fait). Y nommer : la planche
cible, les trois classes et leurs cotes obtenues, le rayon d'emprise retenu, le compte de
triangles et de pièces réel, et le fait que les recettes de surface sont portées de
`resources/gpt_models/tourelle-lourde_v1/build_turret.py` — **recettes, aucun fichier repris**.

## Critères d'acceptation

- [ ] **Les trois classes existent** et leurs cotes sont mesurées sur le `.glb` livré, pas
      annoncées. Écart à la planche donné en pourcentage pour chacune.
- [ ] **Le rayon d'emprise de la lourde est MESURÉ contre la peau** aux dix-sept emplacements, et
      le rapport dit où elle se pose et où elle ne se pose pas. ⚠️ Un « ça devrait tenir » n'est
      pas une réponse : `turret_seat_y()` donne le dénivelé, s'en servir.
- [ ] `_assert_on_axis()` **conservé et vert** sur `turret_ring` et `turret_body`.
- [ ] **Les huit noms de pièces existent toujours**, aux mêmes origines. Diff du contrat de noms
      donné au rapport ; toute pièce ajoutée est listée.
- [ ] **Pas plus de deux pièces posées en plus par tourelle** qu'aujourd'hui.
- [ ] `./scripts/build-hull.sh --check turret_kit` : **zéro octet divergent**, trois exécutions.
- [ ] **`TEXCOORD_0` compté** dans le `.glb`, et **zéro image embarquée** — le harnais du cortège
      échoue sinon.
- [ ] **Le paragraphe « post-traitement rétro / 23 px/m / 9 cm » a disparu du fichier**, et la
      raison du budget est réécrite sur ce qui est vrai aujourd'hui (`ADR-0045`, 45,8 px/m).
- [ ] **La planche de recette montre les trois classes côte à côte**, à la caméra de jeu
      (`graybox.tscn` : 0 14 5, FOV 62, 70° sous l'horizontale), **et** le test de la planche :
      lisibles à **55 px** de large, silhouette seule, émissifs coupés (règle 5).
- [ ] Aucune régression de silhouette : la tourelle **DÉPASSE** toujours, là où un hangar
      **CREUSE** — c'est le test d'acceptation de `BRIEF-0093`, à rejouer.

## Hors périmètre

- **L'élévation et le recul** (voir `## Animation`).
- **Toute texture** (voir `## Texture`).
- **Le code de jeu.** L'ajout d'une troisième valeur à `CortegeTuning.TurretScale`, ses réglages
  bornés, le rayon d'emprise par classe et le placement des lourdes sur la coque appartiennent au
  concepteur. La forge livre la géométrie ; ne toucher à aucun `.gd`, `.tscn` ni `.tres`.
- **Les seize autres tourelles du jeu** (citadelle, Léviathan) : aucune campagne de rattrapage.

## ⚠️ Si le brief demande un KIT : les noms sont figés ici

`turret_pad`, `turret_anchor_skirt`, `turret_ring`, `turret_body`, `turret_barrel`,
`turret_barrel_short`, `turret_service_box`, `turret_pipe`. Toute pièce **neuve** se nomme
`turret_<quelque chose>` en minuscules, et le rapport la liste avec son origine et son parent
attendu — c'est le moteur qui la posera, il ne devine pas.
