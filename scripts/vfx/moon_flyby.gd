class_name MoonFlyby
extends Node3D
## Le décor de la phase `ASTEROID_FIELD` — on survole une lune (ADR-0027).
##
## ⚠️ IL REMPLACE LE FOND, IL NE S'Y AJOUTE PAS. C'est la décision structurante du plan
## inter-boss, et elle a deux causes qui pointent au même endroit :
##   — l'opérateur veut « qu'on n'ait pas le même décor qu'avant le premier boss » ;
##   — le fond est le poste de dépense GPU dominant (13,05 ms mesurés fond complet contre
##     2,73 ms fond masqué, sur les 16,67 du budget 60 FPS, poste Quadro T1000). Empiler
##     une lune et des astéroïdes PAR-DESSUS la nébuleuse ne tient pas.
## On échange donc un décor contre l'autre. Le geste de bascule est celui d'`ADR-0025` :
## `_show_core_interior()` masquait déjà le fond à l'entrée de l'arène.
##
## GÉOMÉTRIE DU LIEU, relevée et non supposée. La caméra est à (0, 14, 5) et plonge de
## ~20° vers le centre du plan ; le fond spatial est un plan HORIZONTAL 90 × 70 posé cinq
## unités SOUS le jeu, à (0, −5, −4). Un survol se met donc là où le regard va déjà : sous
## le plan de jeu. La lune est une calotte qu'on voit par en dessous du champ, les
## astéroïdes flottent entre les deux.
##
## ⚠️ RIEN NE MONTE DANS LE PLAN DE JEU. Au lot 2 le survol est du DÉCOR PUR : aucune
## collision, aucune hitbox, et surtout aucun volume au-dessus de `CEILING_Y` — un rocher
## qui traverserait le plan masquerait le combat sans jamais pouvoir être touché.
## L'arbitrage de l'opérateur (astéroïdes solides, lune décor) porte sur le lot 3 : des
## rochers qui collisionnent sont des entités de gameplay, avec hitbox et pooling, pas des
## pièces de ce décor-ci.

## Décor de survol attendu de la forge (lot 3). Chargé à l'exécution et non `preload` :
## comme `CoreInterior`, la mécanique doit être jouable et testable AVANT que la forge ait
## livré, sinon le lot 2 ne pourrait pas se mesurer.
const DECOR_PATH := "res://assets/imported/models/backgrounds/moon_flyby.glb"

## Le ciel du survol réutilise le shader du fond spatial, réglé « ciel profond » : la
## nébuleuse s'éteint, les étoiles restent. C'est ce qui fait qu'on CHANGE de décor sans
## tomber dans le noir uni de l'arène du noyau — on est toujours dehors.
const SkyShader := preload("res://shaders/space_background.gdshader")

## --- La matière de la surface (ADR-0028) ---------------------------------------
##
## ⚠️ CES CARTES SONT OPTIONNELLES, ET CE N'EST PAS UNE COMMODITÉ. Le décor doit rester
## jouable et mesurable AVANT que la matière existe — c'est la même raison qui charge
## `DECOR_PATH` à l'exécution plutôt qu'en `preload`. Une texture absente dégrade en
## couleur unie, exactement comme aujourd'hui.
##
## Le mécanisme est celui d'`ADR-0011`, déjà en service sur les coques
## (`scripts/fx/hull_detail.gd`) : la carte de MULTIPLICATION va en `albedo_texture`, la
## couleur de palette reste dans `albedo_color`, et Godot calcule
## `albedo = albedo_texture × albedo_color`. La teinte froide et sombre de la lune est donc
## conservée telle quelle — seuls les creux s'assombrissent. Aucune couleur n'arrive par la
## texture, ce qui garde la réserve cyan/corail hors de portée par construction.
const MOON_MAPS := "res://assets/imported/textures/backgrounds/moon_regolith_height_1024"
const ROCK_MAPS := "res://assets/imported/textures/backgrounds/asteroid_rock_height_1024"

## Les coques du bolide et de l'éclat (`BRIEF-0086`). Chargées à l'exécution comme le
## décor : le mécanisme doit rester jouable et mesurable avant que la forge ait livré.
const BOLIDE_PATH := "res://assets/imported/models/vfx/bolide.glb"
const SHARD_PATH := "res://assets/imported/models/vfx/impact_shard.glb"

# --- Le bolide PEINT (TEX-0005 / TEX-0006) -----------------------------------
#
# ⚠️ POURQUOI DES IMAGES ET NON DES PRIMITIVES ÉCLAIRÉES. Cinq itérations ont échoué à
# construire cet impact avec de la géométrie et des cartes dérivées : « un simple cercle
# jaune », puis une traînée vue en enfilade, puis « un carton découpé », puis « un gros cube
# jaune », puis une émission procédurale que le bloom noyait. La mesure a fini par dire
# pourquoi : la tête rend à **130 × 120 px**, et son contraste local était DÉJÀ de 13,67 —
# quasiment celui de la lune. La matière était là ; c'est la technique qui ne convenait pas.
#
# À cette taille, une image **autorisée à la taille d'affichage** bat toute dérivation
# depuis une tuile de 1024 étalée sur huit mètres de monde.
const BOLIDE_SPRITE := "res://assets/imported/vfx/bolide_incandescent.png"
const TRAIL_SPRITE := "res://assets/imported/vfx/trainee_flamme.png"
## ⚠️ UN ÉLÉMENT, PAS L'EFFET. L'onde d'impact n'est plus un anneau ni un panneau peint : c'est
## un `GPUParticles3D` qui répète cette bouffée des dizaines de fois, à des tailles, rotations
## et durées propres. Règle posée par l'opérateur le 2026-08-26 : « une surface se texture,
## un VOLUME se peuple » — un effet volumétrique sur un seul quad est un carton, il n'a ni
## profondeur, ni parallaxe, ni variation dans le temps.
const DUST_SPRITE := "res://assets/imported/vfx/bouffee_poussiere.png"

## Combien de bouffées, et combien de temps elles vivent.
const DUST_COUNT := 52
const DUST_LIFE := 1.7

## Côté du quad, en mètres. ⚠️ MESURÉ SUR L'IMAGE, pas choisi : le bolide occupe 64,6 % de
## son cadre et la traînée 88,6 %. Pour une roche de 2,5 m il faut donc un quad de
## 2,5 / 0,646 ≈ 3,9 ; pour un sillage de 14 m, 14 / 0,886 ≈ 15,8.
const BOLIDE_SPRITE_SIZE := 3.9
## ⚠️ 11,0 ET NON 15,8 — l'opérateur en jouant : « la traînée recouvre tout le météore et
## même elle est avant lui ». Elle était à la fois trop longue et mal placée.
const TRAIL_SPRITE_SIZE := 11.0

## ⚠️ LE CONTENU DES DEUX IMAGES COURT SUR LEUR DIAGONALE — extrémité chaude en bas à
## droite, dissipation vers le haut à gauche — et non sur leur axe vertical. Sans cette
## rotation, le sillage partirait de travers par rapport à la course, ce qui se voit
## immédiatement et n'a l'air que d'un « effet mal placé ».
const SPRITE_DIAGONAL := -45.0

## Où se trouve l'extrémité CHAUDE de la traînée dans son image, en fraction du côté depuis
## le centre. Sans ce recul, la flamme naîtrait au milieu du panneau — donc à côté du bolide.
##
## ⚠️ 0,523 ET NON 0,42 : la première valeur était ESTIMÉE à l'œil sur le coin de l'image,
## la seconde est MESURÉE (centre de masse du centile le plus brûlant, à (1083, 1099) sur
## 1254). L'écart de 0,10 côté valait 1,6 m de décalage vers l'avant — assez pour que la
## flamme passe DEVANT le météore, ce que l'opérateur a vu immédiatement.
const TRAIL_HEAD_OFFSET := 0.523

## Combien de mètres de surface couvre une tuile. ⚠️ VALEURS DÉCIDÉES, pas mesurées — et
## c'est ICI qu'elles se rattrapent, pas dans l'image (`TEX-0001`, `TEX-0002`). Une tuile
## qui lit trop grosse ou trop fine est un chiffre à changer, jamais une texture à
## régénérer : le dépôt fait déjà ce geste dans `hull_detail.gd` et `citadel_detail.gd`.
##
## ⚠️ 55 m ET NON 12, CORRIGÉ EN REGARDANT (2026-08-26). À 12 m la calotte prenait 31 tuiles
## de circonférence et rendait un **papier de verre uniforme** : pas un cratère visible, et
## le quadrillage de la répétition qui commençait à se lire. C'est mot pour mot la leçon de
## `hull_detail.gd` — « le detail fin ne se noie pas seulement, il MENT ». À 55 m la calotte
## en prend 6,9, et un cratère moyen de `TEX-0001` (≈ 1/20 de tuile) fait ~2,8 m, soit une
## vingtaine de pixels à l'écran : il redevient un cratère.
##
## Les rochers gardent 8 m : ils sont petits, proches, et leur texture s'y lit déjà —
## vérifié sur la même capture.
const MOON_METRES_PER_TILE := 55.0
const ROCK_METRES_PER_TILE := 8.0

## Combien de fois la tuile de roche se répète sur les rochers LIVRÉS, dont les UV portent
## déjà l'échelle de 8 m par tuile (`BRIEF-0086`, mesuré à 0,125 tuile/m).
##
## ⚠️ 2,7 ramène la tuile à ~3 m de roche : un rocher de 10 m en montre alors trois, donc
## une dizaine de fractures qui se lisent comme du DÉTAIL. À 1 (une seule tuile pour tout
## le rocher), les trois grandes fractures de la carte devenaient la silhouette même du
## caillou. C'est le symétrique exact de la lune, qu'il a fallu DÉ-tuiler de 12 à 55 m le
## matin même : la même carte, deux objets, deux échelles opposées — et dans les deux cas
## le défaut se voit et ne se calcule pas.
const ROCK_RETILE := 2.7

## Force du relief. La lune est vue de TRÈS loin : une normale trop marquée y produit un
## moiré, la même leçon que la coque du Specter-9 passée de 1,5 à 0,7 parce qu'elle prenait
## un aspect martelé.
const SURFACE_NORMAL_SCALE := 0.8

## Plafond du décor. Le plan de jeu est en Y = 0 ; les repères du fond existant vivent
## entre −3 et −4,2. Rien du survol ne passe au-dessus.
const CEILING_Y := -3.0

## Rotation de la lune, en radians par seconde, autour de X — donc la surface défile vers
## le BAS de l'écran, dans le sens où le joueur avance. À 0,022 rad/s sur un rayon de 55,
## la surface file à ~1,2 u/s : lisible sur les 45-60 s de la phase (~63° parcourus) sans
## jamais donner l'impression d'une boule qui tourne sur elle-même.
const MOON_SPIN := 0.022

## Le ciel du survol, et sa taille. ⚠️ IL EST BIEN PLUS BAS que le fond spatial habituel
## (−5) : celui-ci n'a rien devant lui, alors que le survol doit loger une lune et des
## rochers ENTRE le ciel et le plan de jeu. Un ciel à −5 les aurait tous masqués — c'est
## exactement ce que `test_moon_flyby.gd` a attrapé à la première écriture.
## La taille suit la profondeur : à Y = −45, la caméra voit ~75 unités de haut.
const SKY_Y := -45.0
const SKY_SIZE := Vector2(300.0, 240.0)

## Géométrie de la lune. ⚠️ Le rayon et le centre vont ENSEMBLE, et deux bornes les
## tiennent : le sommet reste SOUS le plan de jeu (sinon la lune emplit le cadre et le
## combat se joue sur un mur gris) et AU-DESSUS du ciel (sinon elle passe derrière le fond
## et on ne survole plus rien). Elle est décalée vers +Z, c'est-à-dire vers le BAS du
## cadre : le plan demande une lune qui occupe le bas ou le côté, pas tout l'écran.
const MOON_RADIUS := 60.0
const MOON_CENTER := Vector3(0.0, -78.0, 34.0)

## Bande de rebouclage des astéroïdes, en Z monde. Ils dérivent vers +Z (vers le bas de
## l'écran) et reparaissent au fond, hors cadre. 85 unités : à la vitesse d'un rocher
## proche, une traversée dure ~35 s — l'ordre de grandeur de la phase.
const WRAP_MIN_Z := -45.0
const WRAP_MAX_Z := 40.0

## --- Les impacts (lot 3) ----------------------------------------------------
##
## « On pourrait assister à des astéroïdes qui la percuteraient, faisant s'envoler des
## débris. » C'est du **VFX scripté sur des jalons**, pas de la simulation : trois impacts
## à des instants fixes de la traversée, pour que la scène se joue à chaque partie de la
## même façon — un semis aléatoire rendrait toute capture incomparable.
##
## ⚠️ ILS N'EMPRUNTENT PAS `VFXManager`. Celui-ci est dimensionné pour le combat, au
## premier plan : ses explosions ont des tailles fixes par catégorie et aucune échelle. Un
## impact se produit ici sur une lune de 60 unités de rayon, à trois fois la distance du
## plan de jeu — la même explosion y serait un point. Le décor porte donc ses propres
## effets, à sa propre échelle, et préalloués comme tout le reste.

## Instants de la phase où un bolide touche. Choisis entre les pics de la vague : le
## joueur doit avoir une seconde pour REGARDER.
const IMPACT_TIMES: PackedFloat32Array = [11.0, 26.0, 40.0]
## Où ils tombent, en (x, z) monde. ⚠️ La HAUTEUR ne se choisit pas, elle se déduit de la
## sphère (`surface_point`) : une altitude écrite à la main placerait le flash au-dessus du
## sol ou dedans, et rien ne le dirait.
const IMPACT_SPOTS: PackedVector2Array = [
	Vector2(-6.0, 10.0), Vector2(12.0, 2.0), Vector2(-14.0, -2.0),
]
## Hauteur de chute du bolide, et sa durée. Assez long pour qu'on voie venir le coup.
## ⚠️ BORNÉE PAR LE PLAFOND, et pas par le goût : le point d'impact le plus HAUT est à
## −23,3, donc une chute de 26 faisait partir le bolide à +2,7 — au-dessus du plan de jeu,
## qu'il aurait traversé à chaque fois. Trouvé par `test_moon_flyby.gd`, jamais à l'écran.
const BOLIDE_DROP := 18.0
const BOLIDE_FALL := 2.4
## Durées de vie du flash et des éclats. ⚠️ LE FLASH A ÉTÉ RÉDUIT (2026-08-26) : c'est LUI,
## la sphère pleine au centre de l'impact, qui était « le simple cercle jaune » de la
## plainte. Il ne raconte plus le choc — l'anneau et les éclats s'en chargent — il n'est
## plus que l'étincelle blanche du premier contact, brève et petite.
const FLASH_LIFE := 0.45
const SHARD_LIFE := 3.0
## ⚠️ Le compte et la taille sont ceux de la DISTANCE, pas du goût : la gerbe se joue à
## trente unités de la caméra, où un éclat de 0,5 pèse une quinzaine de pixels. À huit
## morceaux de cette taille, « des débris qui s'envolent » rendait deux losanges perdus sur
## la surface. L'intensité finale, elle, se juge EN MOUVEMENT — une capture fige la seule
## chose qui fait lire une gerbe.
const SHARD_COUNT := 14
## Le chaud du décor. ⚠️ DORÉ, PAS CORAIL — et c'est une règle de charte, pas un goût.
## Le fond « ne touche jamais au cyan réservé au tir allié ni au corail réservé au tir
## ennemi » (`space_background.gdshader`, règles de lisibilité). L'essai précédent
## reprenait l'orange des explosions (1 / 0,46 / 0,16) : à l'écran, un objet de cette
## teinte qui DESCEND se lit comme un projectile ennemi à esquiver — et il est dans le
## décor, donc rien ne peut être fait contre lui. Un doré chaud reste incandescent sans
## revendiquer une menace.
const IMPACT_WARM := Color(1.0, 0.80, 0.45)

## Vitesse d'éjection des éclats, et le rappel qui les fait retomber. Ce n'est pas une
## gravité juste — c'est celle qui rend la gerbe lisible en trois secondes.
const SHARD_SPEED := 9.0
const SHARD_PULL := 5.0

# --- Ce qui rend un impact LISIBLE à 96 unités (2026-08-26) -------------------
#
# ⚠️ LE DIAGNOSTIC AVANT LES RÉGLAGES, parce qu'il change ce qu'il faut faire. Relevé de
# l'opérateur en jouant : « les astéroïdes qui se crashent sur la lune sont un simple
# cercle jaune ». C'est exact, et la cause est une MESURE, pas un goût :
#
# ⚠️ ET UN PREMIER CALCUL FAUX, CORRIGÉ LE 2026-08-26 — la distance n'est pas celle qu'on
# croit. J'avais mesuré au **centre de la lune** (96,5 unités, 4,7 px/m, donc 8 px pour le
# bolide) et bâti tous les réglages là-dessus. Or le bolide ne vit pas au centre de la
# lune : il tombe sur sa SURFACE, et le premier point d'impact est à **38,1 unités** de la
# caméra — deux fois et demie plus près.
#
#   au point d'impact : cadre visible 45,8 m pour 540 px, soit **11,8 px par mètre**.
#   Un bolide de 1,7 m y occupe **20 PIXELS**, pas 8.
#
# Conséquence directe : il n'avait AUCUN besoin d'être grossi, et l'agrandir en a fait un
# aplat doré de 36 px — « un gros cube jaune », mot de l'opérateur. La leçon générale est
# plus large que ce bolide : **mesurer la distance de l'OBJET, pas celle du décor derrière
# lui**. Le même faux chiffre est parti dans `BRIEF-0086`, où la forge a bâti sa recette
# de silhouette sur « 8 pixels ».
#
# Ce qui reste vrai, et qui a bien réglé la lisibilité : ce sont la TRAÎNÉE et l'ONDE qui
# couvrent des pixels, pas la tête.

## Taille de la DOUBLURE géométrique, quand la coque forgée n'est pas là. ⚠️ Elle n'agit
## que sur ce chemin de repli : la coque livrée, elle, porte sa propre taille.
const BOLIDE_SCALE := 1.0

## ⚠️ LE BOLIDE ARRIVE EN BIAIS, ET C'EST LA CORRECTION QUI DÉCIDE DE TOUT. Il tombait le
## long de la verticale locale de la lune ; or la caméra REGARDE D'EN HAUT. Une chute
## verticale est donc vue en enfilade : premier essai avec traînée, elle s'écrasait en une
## tache dorée informe au lieu d'un trait. Aucune longueur n'y aurait rien changé.
##
## Le trajet reçoit donc un écart LATÉRAL, qui le met en travers du cadre. Il arrive du
## haut-gauche de l'écran — le sens de lecture, et l'inverse de la dérive du décor, si
## bien qu'il tranche sur le mouvement de fond au lieu de s'y fondre.
##
## ⚠️ L'écart est HORIZONTAL (composante Y nulle) : il ne touche donc pas à la garde du
## plafond que `test_moon_flyby.gd` tient sur la trajectoire — le bolide ne monte pas d'un
## centimètre de plus qu'avant.
const BOLIDE_SLANT := 26.0
const BOLIDE_FROM := Vector3(-0.707, 0.0, -0.707)

## Ajustement de taille de la coque forgée.
##
## ⚠️ 0,65 ET NON 1,13 — corrigé le 2026-08-26 sur la mesure refaite au bon endroit. À 1,13
## la coque de 2,70 m rendait 36 px de long ; non éclairée et émissive, ça fait un APLAT
## doré, pas un caillou. À 0,65 elle fait 1,76 m, soit ~21 px : la taille pour laquelle
## l'effet avait été conçu, et où la silhouette a une chance de se lire.
##
## ⚠️ Au-delà de ~1,3, il faudrait revenir changer la taille DANS le script de la forge et
## rebâtir, pas étirer le nœud — les UV portent l'échelle monde, et un étirement ferait
## dériver le grain de la roche.
## ⚠️ REMONTÉ À 1,3 le 2026-08-26, sur la cible donnée par l'opérateur. « Gros cube jaune »
## ne visait pas la TAILLE mais l'absence de matière — j'avais rapetissé quand il fallait
## détailler. Sa cible montre une tête franchement grosse, faite de plaques sombres et de
## fissures brûlantes. La taille revient donc, la matière avec.
const BOLIDE_FIT := 1.3

## La traînée : un cône effilé DERRIÈRE le bolide, le long de sa course RÉELLE — pas de la
## verticale. C'est elle qui porte la lisibilité, pas la tête.
const TRAIL_LENGTH := 14.0
## ⚠️ 0,35 ET NON 0,7. À 0,7 la traînée rendait un CARTON DÉCOUPÉ : un cône plat, opaque
## de bout en bout, arêtes polygonales visibles et capuchon hexagonal en bout. Relevé par
## l'opérateur sur une capture en PLEINE RÉSOLUTION, là où mes propres captures — jugées
## réduites en 960 px — ne pouvaient pas le montrer.
const TRAIL_RADIUS := 0.35

## L'onde de choc : un ANNEAU qui s'étale sur la surface, pas une colonne qui monte.
##
## ⚠️ MÊME RAISON QUE LA TRAÎNÉE, ET C'EST LA PLAINTE D'ORIGINE. Vue d'au-dessus, une gerbe
## conique verticale EST un cercle jaune — « les astéroïdes qui se crashent sur la lune
## sont un simple cercle jaune ». Ce qui se lit en plongée, c'est ce qui s'étale dans le
## plan qu'on voit : un anneau qui grandit, et les éclats qui partent en arc (ils
## existaient déjà). L'anneau est un tube SANS COUVERCLES — plein, il redeviendrait le
## disque qu'on cherche à éviter.
const PLUME_LIFE := 1.4
const PLUME_HEIGHT := 2.2
const PLUME_RADIUS := 11.0

var _decor: Node3D
var _moon: Node3D
## Vrai quand la doublure procédurale a pris le relais faute de décor livré. Le niveau le
## journalise : un survol en doublure ne doit JAMAIS passer pour l'asset final (ADR-0006).
var _is_stand_in: bool = false

## Les corps qui dérivent, et leur vitesse, résolus UNE fois au montage. Deux tableaux
## parallèles plutôt qu'un dictionnaire par corps : `_process` ne doit rien allouer
## (spec §26.2), et un `Vector3` est un type valeur.
var _drifters: Array[Node3D] = []
var _drift_velocities: PackedVector3Array = PackedVector3Array()

## Horloge de la phase, repartie à zéro à chaque révélation, et le prochain impact à jouer.
var _clock: float = 0.0
var _next_impact: int = 0
## L'impact en cours : son âge, son point, et la verticale locale de la surface à cet
## endroit (les éclats partent d'ici et y retombent).
var _impact_age: float = -1.0
var _impact_at: Vector3 = Vector3.ZERO
var _impact_up: Vector3 = Vector3.UP
## Le bolide, le flash et les éclats : préalloués au montage, rejoués à chaque impact.
## La matière a-t-elle été trouvée ? ⚠️ Le journal le dit au montage, comme la doublure :
## une surface en aplat qui se croit texturée est exactement le genre de défaut muet que
## le projet paie deux fois (`ADR-0006`, `ADR-0025`).
## Les impacts se jouent-ils avec les images de l'opérateur (`TEX-0005`/`TEX-0006`) ou avec
## leur repli géométrique ? Le niveau le journalise : une doublure qui se croit peinte est
## exactement le genre de défaut muet que ce fichier collectionne.
var _painted_bolide: bool = false
var _painted_trail: bool = false
## Le nuage de poussière de l'impact. `null` tant que sa bouffée n'a pas été livrée — et
## l'anneau procédural reprend alors la main.
var _dust: GPUParticles3D
## Le nuage a-t-il déjà été lancé pour CET impact ? Voir le piège d'`emitting` plus bas.
var _dust_fired: bool = false

var _dressed_moon: bool = false
var _dressed_rocks: bool = false

## `--no-surface-maps` : le décor se joue en aplat, sans aucune carte. C'est le TÉMOIN du
## différentiel de coût des textures.
##
## ⚠️ UN INTERRUPTEUR, PAS UN FACTEUR. Baisser `normal_scale` à zéro atténuerait le résultat
## en payant les échantillonnages en entier — la leçon mesurée du ciel du survol, où une
## nébuleuse « éteinte » à 0,12 coûtait toujours 0,738 ms contre 0,323 pour un vrai
## branchement. Ici on ne pose simplement aucune texture : rien à échantillonner.
##
## ⚠️ À poser AVANT l'entrée dans l'arbre : `_ready()` bâtit le décor.
var maps_enabled: bool = true

var _bolide: MeshInstance3D
## La traînée derrière le bolide et la gerbe conique à l'impact — les deux seules pièces
## du kit qui couvrent assez de pixels pour se lire à 96 unités.
var _trail: MeshInstance3D
var _plume: MeshInstance3D
var _flash: MeshInstance3D
var _shards: Array[MeshInstance3D] = []
var _shard_velocities: PackedVector3Array = PackedVector3Array()

func _ready() -> void:
	reveal(false)
	_build()

func is_stand_in() -> bool:
	return _is_stand_in

## La matière de surface est-elle en place ? Lu par le niveau, qui le journalise : une
## calotte en aplat et une calotte texturée ne se distinguent pas dans un journal muet.
func has_surface_maps() -> bool:
	return _dressed_moon and _dressed_rocks

## Les impacts se jouent-ils avec les images peintes, ou avec leur repli géométrique ?
func has_painted_impacts() -> bool:
	return _painted_bolide and _painted_trail

## Montre ou cache le survol. ⚠️ Coupe AUSSI `_process` : un décor invisible qui continue
## de faire dériver ses rochers dépense pour rien pendant les trois quarts de la partie.
func reveal(on: bool) -> void:
	visible = on
	set_process(on)
	if on:
		# La phase commence ici : les jalons d'impact se comptent depuis l'entrée dans le
		# champ, pas depuis le montage du niveau.
		_clock = 0.0
		_next_impact = 0
	_end_impact()

func _process(delta: float) -> void:
	if _moon != null:
		_moon.rotate_x(MOON_SPIN * delta)
	for i in _drifters.size():
		var body := _drifters[i]
		body.position = drifted(body.position, _drift_velocities[i], delta)
	_clock += delta
	_advance_impacts(delta)

## Position suivante d'un corps qui dérive, rebouclée sur la bande. Pure et statique,
## donc vérifiable sans arbre de scène — la même raison qui a sorti `EnemyHoming` du
## contrôleur (ADR-0022).
static func drifted(from: Vector3, velocity: Vector3, delta: float) -> Vector3:
	var next := from + velocity * delta
	if velocity.z > 0.0 and next.z > WRAP_MAX_Z:
		next.z = WRAP_MIN_Z
	elif velocity.z < 0.0 and next.z < WRAP_MIN_Z:
		next.z = WRAP_MAX_Z
	return next

func _build() -> void:
	# ⚠️ LE CIEL APPARTIENT AU MÉCANISME, PAS À LA DOUBLURE — et il a vécu au mauvais
	# endroit jusqu'au 2026-08-26. Il était construit dans `_build_stand_in()` ; dès que le
	# `.glb` de la forge est arrivé, la doublure n'a plus été construite du tout, **et le
	# ciel avec elle**. La phase 2 se jouait sur du NOIR ABSOLU, sans une étoile.
	#
	# Rien ne pouvait le signaler : le décor livré est conforme, la porte de qualité est
	# verte, le journal ne parle pas d'un nœud qui n'existe pas, et `BRIEF-0085` mettait
	# le ciel hors périmètre à juste titre (c'est un shader, pas de la géométrie). Chacun
	# avait raison de son côté, et personne ne construisait le ciel.
	#
	# Relevé par l'opérateur en jouant : « lors de la phase 2 il n'y a pas de fond étoilé,
	# tout noir c'est moche ». Mesuré ensuite : la bande de ciel restait absolument noire
	# même multipliée par quatre en luminosité.
	add_child(_sky())
	if ResourceLoader.exists(DECOR_PATH):
		var packed := load(DECOR_PATH) as PackedScene
		if packed != null:
			_decor = packed.instantiate() as Node3D
	if _decor == null:
		_decor = _build_stand_in()
		_is_stand_in = true
	add_child(_decor)
	_collect_bodies()
	_silence_shadows()
	# APRÈS `_collect_bodies` : c'est lui qui relève `Moon` et les `Asteroid_*` par leur nom.
	_dress_decor()
	_build_impact_kit()

## Habille une surface avec un jeu de cartes dérivées, s'il existe.
##
## Retourne faux quand les cartes ne sont pas là — et c'est un chemin NORMAL, pas une
## erreur : le décor se joue en couleur unie tant que la matière n'a pas été livrée.
##
## ⚠️ `tiles` est en TUILES, pas en mètres : c'est l'appelant qui connaît la taille réelle
## de la pièce et fait la division. Une constante « mètres par tuile » posée ici ne saurait
## pas si elle habille une lune de 60 m ou un caillou de 3 m — et c'est exactement l'erreur
## qui fait lire une feuille comme du bruit sur une forteresse.
static func dress(material: StandardMaterial3D, prefix: String, tiles: Vector2) -> bool:
	var mul_path := prefix + "_mul.png"
	if not ResourceLoader.exists(mul_path):
		return false
	# La MULTIPLICATION, pas une couleur : `albedo_color` garde la teinte de palette.
	material.albedo_texture = load(mul_path) as Texture2D
	var nrm_path := prefix + "_nrm.png"
	if ResourceLoader.exists(nrm_path):
		material.normal_enabled = true
		material.normal_texture = load(nrm_path) as Texture2D
		material.normal_scale = SURFACE_NORMAL_SCALE
	var rough_path := prefix + "_rough.png"
	if ResourceLoader.exists(rough_path):
		material.roughness_texture = load(rough_path) as Texture2D
	var ao_path := prefix + "_ao.png"
	if ResourceLoader.exists(ao_path):
		material.ao_enabled = true
		material.ao_texture = load(ao_path) as Texture2D
	material.uv1_scale = Vector3(tiles.x, tiles.y, 1.0)
	return true

## Combien de tuiles il faut pour couvrir une sphère de ce rayon, en u et en v.
##
## Une `SphereMesh` déplie u sur la CIRCONFÉRENCE (2πr) et v sur le DEMI-MÉRIDIEN (πr) :
## les deux ne valent pas la même longueur, donc une échelle uniforme étirerait la tuile
## du simple au double. Pure et statique — c'est le genre de calcul qui a l'air évident et
## qu'on rate en silence.
static func sphere_tiles(radius: float, metres_per_tile: float) -> Vector2:
	if metres_per_tile <= 0.0:
		return Vector2.ONE
	return Vector2(TAU * radius / metres_per_tile, PI * radius / metres_per_tile)

## Éteint les ombres sur tout le décor. ⚠️ LA DOUBLURE LE FAIT EXPLICITEMENT SUR CHAQUE
## MAILLAGE (`SHADOW_CASTING_SETTING_OFF`) ; un `.glb` importé, lui, arrive avec les ombres
## ACTIVES par défaut, et le geste ne se reportait pas tout seul.
##
## Ce n'est pas un réglage de goût, c'est une conséquence de la géométrie du lieu : les
## rochers vivent entre Y = −13 et −34, donc à ~30 unités de la caméra — DANS les 40 de
## `directional_shadow_max_distance` — alors que la lune est à 96 et hors de portée. Le
## décor se retrouvait donc à moitié dans la carte d'ombres et à moitié dehors.
func _silence_shadows() -> void:
	if _decor == null:
		return
	for mesh in _meshes_under(_decor):
		mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF

## Habille le décor LIVRÉ par la forge — jamais la doublure, qui s'habille en se construisant.
##
## ⚠️ `uv1_scale` RESTE À 1, ET C'EST LE PIÈGE DE CE CHANTIER. Les UV du `.glb` portent
## **déjà** l'échelle : `BRIEF-0085` a déplié la calotte à 55 m par tuile et l'a mesuré
## (43,0 → 56,3 m/tuile sur la bande vue, anisotropie 1,30). Y appliquer `sphere_tiles()`,
## qui sert la doublure, tuilerait **6,9 fois de trop** — et le défaut ne produirait ni
## erreur ni test rouge, seulement un régolithe qui redevient du papier de verre. C'est la
## même faute que les 12 m corrigés le 2026-08-26, à un étage plus haut.
##
## Les trois rochers PARTAGENT un matériau (`Asteroid_Rock`) : on le dérive une seule fois.
func _dress_decor() -> void:
	if _is_stand_in or not maps_enabled or _decor == null:
		return
	# ⚠️ Un tableau, jamais `null` : GDScript refuse `null` pour un `Array[T]` typé, et la
	# faute ne se voit qu'à la compilation d'un script DÉPENDANT — le message parle alors
	# d'un fichier qu'on n'a pas touché.
	var moon_material: Array[StandardMaterial3D] = []
	if _moon != null:
		_dressed_moon = _dress_meshes_of(_moon, MOON_MAPS, moon_material)
	var rock_material: Array[StandardMaterial3D] = []
	for body in _drifters:
		_dressed_rocks = _dress_meshes_of(body, ROCK_MAPS, rock_material) or _dressed_rocks
	# ⚠️ LES ROCHERS SE RETUILENT, LA LUNE NON — et c'est une mesure, pas un goût.
	# `TEX-0002` est calée sur 8 m de roche et porte 3 à 5 fractures majeures par tuile.
	# Or les rochers livrés font 8 à 20 m : on n'en voyait donc qu'UNE SEULE TUILE, et les
	# trois fractures devenaient les arêtes du rocher ENTIER — de larges plages tonales à
	# bords droits, qui se lisent comme des plans superposés et non comme de la roche.
	# Relevé par l'opérateur : « les astéroïdes n'ont pas de texture ». Ils en avaient une,
	# à une échelle où elle ne pouvait pas se lire comme une matière.
	#
	# Le rattrapage est celui que le contrat annonçait : un chiffre, pas une régénération.
	for material in rock_material:
		material.uv1_scale = Vector3.ONE * ROCK_RETILE

## Pose les cartes sur chaque surface d'un nœud et de ses descendants.
##
## `shared` mutualise le matériau entre plusieurs nœuds : trois rochers taillés dans la même
## roche n'ont aucune raison d'en porter trois copies. Passer un tableau vide et le
## réutiliser d'un appel à l'autre suffit à les lier.
func _dress_meshes_of(root: Node3D, prefix: String,
		shared: Array[StandardMaterial3D]) -> bool:
	var done := false
	for mesh in _meshes_under(root):
		for i in mesh.mesh.get_surface_count():
			var tuned: StandardMaterial3D
			if not shared.is_empty():
				tuned = shared[0]
			else:
				var base := mesh.mesh.surface_get_material(i) as StandardMaterial3D
				# ⚠️ On DUPLIQUE : le matériau vient de l'import et serait partagé par toute
				# la session. Le muter en place ferait déborder ce décor hors de sa scène.
				tuned = (base.duplicate() as StandardMaterial3D) if base != null else StandardMaterial3D.new()
				if not dress(tuned, prefix, Vector2.ONE):
					return false
				shared.append(tuned)
			mesh.set_surface_override_material(i, tuned)
			done = true
	return done

static func _meshes_under(node: Node, out: Array[MeshInstance3D] = []) -> Array[MeshInstance3D]:
	var mesh := node as MeshInstance3D
	if mesh != null and mesh.mesh != null:
		out.append(mesh)
	for child in node.get_children():
		_meshes_under(child, out)
	return out

## Relève la lune et les corps qui dérivent. Le décor livré comme la doublure exposent le
## même contrat de noms : `Moon`, et des `Asteroid_*`. ⚠️ Un contrat de noms respecté n'est
## pas une preuve que l'asset fait ce qu'il dit — la leçon d'`ADR-0025`, où les « anneaux
## qu'on franchit » mesuraient 30 cm. C'est `test_moon_flyby.gd` qui mesure.
func _collect_bodies() -> void:
	_drifters.clear()
	_drift_velocities = PackedVector3Array()
	if _decor == null:
		return
	_moon = _decor.find_child("Moon", true, false) as Node3D
	for child in _decor.get_children():
		var body := child as Node3D
		if body == null or not body.name.begins_with("Asteroid"):
			continue
		_drifters.append(body)
		# Plus un rocher est proche, plus vite il file : c'est la parallaxe qui dit
		# l'échelle, pas le nombre de triangles. La vitesse se DÉDUIT de la hauteur, donc
		# un rocher déplacé ne peut pas garder une vitesse qui ne lui va plus.
		_drift_velocities.append(Vector3(0.0, 0.0, drift_speed_at(body.position.y)))

## Vitesse de dérive d'un corps posé à cette hauteur. Un rocher proche traverse le cadre
## en une trentaine de secondes ; un rocher lointain rampe.
static func drift_speed_at(y: float) -> float:
	# −10 (au plus près du jeu) → 3,2 u/s ; −40 (au loin) → 0,7 u/s.
	var far := clampf((absf(y) - 10.0) / 30.0, 0.0, 1.0)
	return lerpf(3.2, 0.7, far)

# --- Doublure procédurale ---------------------------------------------------
#
# ⚠️ CE N'EST PAS L'ASSET. Elle existe pour que la MÉCANIQUE — bascule du décor, dérive,
# parallaxe, et surtout le COÛT GPU — soit jouable et mesurable avant que la forge ait
# rendu. C'est cette mesure qui dira ce que le lot 3 peut se payer : l'engager avant
# serait dessiner un budget qu'on n'a pas.

func _build_stand_in() -> Node3D:
	var root := Node3D.new()
	root.name = "StandIn"
	root.add_child(_moon_body())
	# Trois rochers, trois profondeurs, trois tailles. Le « vraiment énorme » se joue par
	# la parallaxe et le cadrage : un bloc proche qui traverse lentement dit mieux
	# l'échelle que dix cailloux.
	# ⚠️ La HAUTEUR de chaque rocher est bornée par son rayon : un bloc de rayon r posé à
	# y doit tenir sous `CEILING_Y`, transformations comprises. Le test le mesure — c'est
	# lui qui a renvoyé le premier jeu de valeurs, où le plus gros traversait le champ.
	root.add_child(_rock("Asteroid_01", 6.5, Vector3(-13.0, -13.0, -18.0)))
	# ⚠️ CELUI-CI A ÉTÉ ÉCARTÉ DU COULOIR DE VOL. Posé à (11, −22, 6), il passait
	# visuellement À CÔTÉ du chasseur : un rocher qu'on croit pouvoir percuter, et qui
	# traverse. Au lot 2 le survol est du décor pur — il ne doit rien promettre qu'il ne
	# tienne. (Au lot 3, des rochers SOLIDES arriveront, et il faudra alors les
	# distinguer de ceux-ci à l'œil : c'est un sujet de conception, pas de placement.)
	root.add_child(_rock("Asteroid_02", 5.0, Vector3(15.0, -29.0, 15.0)))
	root.add_child(_rock("Asteroid_03", 12.0, Vector3(19.0, -34.0, -34.0)))
	return root

## Le ciel : le plan du fond spatial, mais posé BEAUCOUP plus bas et la nébuleuse éteinte.
## On reste dehors, sous un autre ciel — et cette fois il y a quelque chose entre lui et
## nous.
func _sky() -> MeshInstance3D:
	var material := ShaderMaterial.new()
	material.shader = SkyShader
	material.render_priority = -1
	material.set_shader_parameter("deep_color", Color(0.006, 0.008, 0.020))
	material.set_shader_parameter("star_color", Color(0.86, 0.90, 1.0))
	material.set_shader_parameter("star_brightness", 2.6)
	# ⚠️ CE QUI FAIT LE CHANGE DE DÉCOR, ET CE QUI LE PAIE. `deep_sky` n'atténue pas la
	# nébuleuse : il SAUTE les cinq champs de bruit du shader. Régler `nebula_strength`
	# à 0,12 laissait tourner les trois `warped_fbm` pour n'en garder que 12 % —
	# on payait le décor qu'on venait d'enlever.
	material.set_shader_parameter("deep_sky", true)
	material.set_shader_parameter("scroll_speed", -0.5)
	var plane := PlaneMesh.new()
	plane.size = SKY_SIZE
	plane.material = material
	var mesh := MeshInstance3D.new()
	mesh.name = "Sky"
	mesh.mesh = plane
	mesh.position = Vector3(0.0, SKY_Y, -4.0)
	mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mesh.extra_cull_margin = 100.0
	return mesh

## La lune : une calotte, pas une boule. Le joueur n'en voit que le haut, sous le champ —
## c'est ce qui la fait lire comme un astre survolé et non comme une planète posée au fond.
func _moon_body() -> Node3D:
	var pivot := Node3D.new()
	pivot.name = "Moon"
	pivot.position = MOON_CENTER
	var sphere := SphereMesh.new()
	sphere.radius = MOON_RADIUS
	sphere.height = MOON_RADIUS * 2.0
	# Segmentation modeste et assumée : à cette distance la silhouette est un arc, et
	# subdiviser une sphère de 55 m coûte sans se voir. Le relief viendra d'une carte de
	# hauteur au lot 3, pas d'un compte de triangles.
	sphere.radial_segments = 48
	sphere.rings = 24
	var material := StandardMaterial3D.new()
	# ⚠️ SOMBRE, ET FROIDE. Première capture regardée : à 0,30 d'albédo la lune rendait
	# rose pâle et le chasseur — blanc et bleu — s'y perdait, les mines aussi. Trois
	# lumières chaudes (`KeyLight` à 1 / 0,976 / 0,925), plus `warmth` et `saturation`
	# du post-traitement rétro, réchauffent tout ce qu'on leur donne : un gris neutre
	# ressort rosé. Le décor RECULE pour que le jeu avance — la même règle que le
	# réacteur du noyau, où deux teintes à dix points d'écart avaient déjà coûté.
	material.albedo_color = Color(0.115, 0.115, 0.140)
	material.roughness = 1.0
	material.metallic = 0.0
	# La matière, si elle a été livrée (`TEX-0001`). Sans elle, la calotte reste l'aplat
	# ci-dessus — le décor doit se jouer et se mesurer avant que la surface existe.
	_dressed_moon = maps_enabled and dress(material, MOON_MAPS,
		sphere_tiles(MOON_RADIUS, MOON_METRES_PER_TILE))
	var body := MeshInstance3D.new()
	body.name = "Surface"
	body.mesh = sphere
	body.material_override = material
	body.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	pivot.add_child(body)
	for crater in _craters():
		pivot.add_child(crater)
	return pivot

## Les cratères de la doublure : des cuvettes plus sombres posées sur la surface, portées
## par le pivot — elles tournent donc AVEC la lune. Assez pour lire un relief et un sens
## de défilement ; le vrai relief est un sujet de forge.
func _craters() -> Array[MeshInstance3D]:
	var out: Array[MeshInstance3D] = []
	# Latitude, longitude (degrés) et rayon de chaque cuvette. Semées à la main : un
	# semis aléatoire changerait à chaque partie et rendrait toute capture incomparable.
	# ⚠️ RAYONS DIVISÉS PAR DEUX après la première capture : à 9 unités sur une lune de
	# 60, une cuvette lisait comme une flaque posée sur l'astre, pas comme un cratère.
	var seeds := [
		[62.0, -25.0, 4.5], [78.0, 40.0, 2.8], [55.0, 18.0, 3.4],
		[70.0, -62.0, 2.0], [48.0, 55.0, 3.8], [84.0, -8.0, 1.8],
		[58.0, 78.0, 2.6], [66.0, 8.0, 1.5],
	]
	for seed_values: Array in seeds:
		var lat := deg_to_rad(float(seed_values[0]))
		var lon := deg_to_rad(float(seed_values[1]))
		var radius := float(seed_values[2])
		var normal := Vector3(cos(lat) * sin(lon), sin(lat), cos(lat) * cos(lon))
		var disc := CylinderMesh.new()
		disc.top_radius = radius
		disc.bottom_radius = radius * 0.72
		# ⚠️ UNE PASTILLE, PAS UN PALET. À 0,6 d'épaisseur posée à `R − 0,2`, la cuvette
		# dépassait de la surface — et au limbe, là où la lune tourne, elle se détachait
		# franchement de la silhouette : on voyait un objet POSÉ SUR la lune, l'exact
		# contraire d'un creux. Elle est maintenant assez fine pour n'avoir plus d'épaisseur
		# visible, et affleure juste assez pour que la sphère facettée ne l'avale pas.
		disc.height = 0.12
		disc.radial_segments = 16
		disc.rings = 1
		var material := StandardMaterial3D.new()
		# Un creux se lit par le NOIR qu'il fait, pas par son relief : à cette distance
		# aucune ombre portée ne le dessinera.
		material.albedo_color = Color(0.062, 0.060, 0.075)
		material.roughness = 1.0
		var mesh := MeshInstance3D.new()
		mesh.name = "Crater"
		mesh.mesh = disc
		mesh.material_override = material
		mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		# Posée SUR la surface et couchée dessus.
		mesh.position = normal * (MOON_RADIUS + 0.03)
		mesh.basis = _basis_facing(normal)
		out.append(mesh)
	return out

## Oriente un disque (dont l'axe est Y) le long d'une normale. Un `look_at` demanderait
## le nœud dans l'arbre ; ici on compose la base à la main, ce qui vaut hors arbre — donc
## sous les tests.
static func _basis_facing(normal: Vector3) -> Basis:
	var up := normal.normalized()
	var reference := Vector3.RIGHT if absf(up.x) < 0.9 else Vector3.FORWARD
	var right := reference.cross(up).normalized()
	return Basis(right, up, right.cross(up).normalized())

## Un rocher : une sphère écrasée sur trois axes, tournée. Pas de bruit procédural — la
## doublure sert à juger le MOUVEMENT et le coût, jamais la roche.
func _rock(rock_name: String, radius: float, at: Vector3) -> MeshInstance3D:
	var sphere := SphereMesh.new()
	sphere.radius = radius
	sphere.height = radius * 2.0
	sphere.radial_segments = 14
	sphere.rings = 8
	var material := StandardMaterial3D.new()
	# Même correction que la lune, et pour la même raison : c'est du décor, il passe
	# DERRIÈRE les mines et le chasseur.
	material.albedo_color = Color(0.100, 0.098, 0.118)
	material.roughness = 1.0
	# ⚠️ MÊME ÉCHELLE MONDE SUR LES TROIS ROCHERS, et c'est le rayon de CHACUN qui la
	# donne : une tuile calée sur le petit se lirait comme du gravier sur le gros. C'est
	# le défaut n°1 du projet, et `TEX-0002` le porte déjà comme contrainte dure.
	_dressed_rocks = (maps_enabled and dress(material, ROCK_MAPS,
		sphere_tiles(radius, ROCK_METRES_PER_TILE))) or _dressed_rocks
	var mesh := MeshInstance3D.new()
	mesh.name = rock_name
	mesh.mesh = sphere
	mesh.material_override = material
	mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mesh.position = at
	mesh.scale = Vector3(1.0, 0.62, 0.84)
	mesh.rotation = Vector3(0.4, 1.1, -0.3)
	return mesh

# --- Impacts ----------------------------------------------------------------

## Le point de la calotte à l'aplomb de (x, z), et rien d'autre : la hauteur est une
## CONSÉQUENCE du rayon, jamais un réglage. Rend `Vector3.INF` si (x, z) tombe hors du
## disque de la lune — un impact demandé à côté de l'astre est une erreur de données, pas
## une position à inventer.
static func surface_point(x: float, z: float) -> Vector3:
	var dx := x - MOON_CENTER.x
	var dz := z - MOON_CENTER.z
	var flat := dx * dx + dz * dz
	if flat >= MOON_RADIUS * MOON_RADIUS:
		return Vector3.INF
	return Vector3(x, MOON_CENTER.y + sqrt(MOON_RADIUS * MOON_RADIUS - flat), z)

## Position du bolide à `t` secondes de sa chute : il tombe DROIT sur son point, le long
## de la verticale locale de la surface. Pure — donc testable sans arbre de scène.
static func bolide_position(target: Vector3, up: Vector3, t: float) -> Vector3:
	# Chute accélérée : le dernier quart du trajet passe deux fois plus vite que le
	# premier, ce qui donne le coup au lieu d'une descente d'ascenseur.
	var progress := clampf(t / BOLIDE_FALL, 0.0, 1.0)
	return target + (bolide_start(target, up) - target) * (1.0 - progress * progress)

## D'où part le bolide : au-dessus de son point le long de la verticale locale, ET décalé
## latéralement pour que sa course traverse le cadre.
static func bolide_start(target: Vector3, up: Vector3) -> Vector3:
	return target + up * BOLIDE_DROP + BOLIDE_FROM * BOLIDE_SLANT

## Direction de la course, du départ vers le point d'impact — l'axe de la traînée.
static func bolide_heading(target: Vector3, up: Vector3) -> Vector3:
	return (bolide_start(target, up) - target).normalized()

## Position d'un éclat à `t` secondes de son éjection : sa vitesse propre, moins le rappel
## qui le ramène vers la surface. Pure, pour la même raison.
static func shard_position(origin: Vector3, velocity: Vector3, up: Vector3, t: float) -> Vector3:
	return origin + velocity * t - up * (0.5 * SHARD_PULL * t * t)

## Le cône thermique — REPLI de la traînée peinte (`TEX-0006`). Il reste au dépôt parce que
## le décor doit se jouer sans ses images, et parce que son dégradé thermique est juste :
## ce qui lui manquait n'était pas la couleur mais la STRUCTURE — les filaments et les
## braises, qu'un shader simple n'invente pas.
func _build_trail_cone() -> MeshInstance3D:
	var cone := _cone("ImpactTrail", TRAIL_RADIUS, 0.0, 1.0, 1.3)
	# Sans capuchons : le disque plat du bout se lisait comme un hexagone découpé.
	var mesh := cone.mesh as CylinderMesh
	mesh.cap_top = false
	mesh.cap_bottom = false
	_fade_along_length(cone)
	add_child(cone)
	return cone

## Le nuage de poussière de l'impact : des dizaines de bouffées projetées en éventail.
##
## ⚠️ POURQUOI DES PARTICULES ET NON UN PANNEAU. Un effet volumétrique peint sur un seul quad
## n'a ni profondeur, ni parallaxe, ni variation dans le temps : c'est un carton, et il ne
## tient que vu de face. Le volume vient du NOMBRE et de la DISPERSION — chaque bouffée a sa
## taille, sa rotation, sa vitesse et sa durée. La texture n'est plus l'effet, elle en est
## l'élément.
##
## Calqué sur `scripts/fx/vfx_explosion.gd`, qui fait déjà ses étincelles et ses débris ainsi.
##
## ⚠️ EN MÉLANGE ALPHA ET NON ADDITIF, contrairement à la traînée : de la poussière MASQUE le
## sol, elle ne s'ajoute pas à la lumière. Un additif en ferait un nuage lumineux — soit
## exactement le « cercle jaune » qu'on corrige.
func _build_dust() -> GPUParticles3D:
	if not ResourceLoader.exists(DUST_SPRITE):
		return null
	var node := GPUParticles3D.new()
	node.name = "ImpactDust"
	node.one_shot = true
	node.explosiveness = 1.0
	node.amount = DUST_COUNT
	node.lifetime = DUST_LIFE
	# Coordonnées MONDE : le nuage reste où l'impact a eu lieu, il ne suit pas le décor qui
	# dérive sous lui.
	node.local_coords = false
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	node.position = MOON_CENTER
	node.emitting = false

	var mat := ParticleProcessMaterial.new()
	mat.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
	mat.emission_sphere_radius = 0.8
	# ⚠️ SPREAD LARGE : à 82°, l'éventail rase la surface au lieu de monter en colonne. Une
	# colonne verticale serait vue en enfilade depuis la caméra en plongée — la faute qui a
	# coûté deux itérations sur la traînée.
	mat.spread = 82.0
	mat.initial_velocity_min = 4.0
	mat.initial_velocity_max = 13.0
	mat.damping_min = 3.0
	mat.damping_max = 7.0
	mat.scale_min = 1.1
	mat.scale_max = 3.4
	mat.angle_min = -180.0
	mat.angle_max = 180.0
	mat.angular_velocity_min = -26.0
	mat.angular_velocity_max = 26.0
	var grow := Curve.new()
	grow.add_point(Vector2(0.0, 0.35))
	grow.add_point(Vector2(0.4, 1.0))
	grow.add_point(Vector2(1.0, 1.25))
	var grow_tex := CurveTexture.new()
	grow_tex.curve = grow
	mat.scale_curve = grow_tex
	var ramp := Gradient.new()
	ramp.offsets = PackedFloat32Array([0.0, 0.18, 1.0])
	ramp.colors = PackedColorArray([
		Color(1.0, 0.95, 0.86, 0.0),
		Color(0.92, 0.88, 0.82, 0.85),
		Color(0.62, 0.60, 0.60, 0.0),
	])
	var ramp_tex := GradientTexture1D.new()
	ramp_tex.gradient = ramp
	mat.color_ramp = ramp_tex
	node.process_material = mat

	var quad := QuadMesh.new()
	quad.size = Vector2(2.6, 2.6)
	var draw := StandardMaterial3D.new()
	draw.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	draw.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	draw.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	# ⚠️ Sans `billboard_keep_scale`, le billboard JETTE l'échelle du nœud — piège n°1 de
	# `pratique-geometries-invisibles.md`, payé en trois captures vides.
	draw.billboard_keep_scale = true
	draw.vertex_color_use_as_albedo = true
	draw.albedo_texture = load(DUST_SPRITE) as Texture2D
	draw.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
	quad.material = draw
	node.draw_pass_1 = quad
	add_child(node)
	return node

## Un panneau incandescent portant une image, ou `null` si elle n'a pas été livrée.
##
## `additive` : la traînée s'AJOUTE au ciel (le noir de l'image n'y contribue rien, donc
## aucun détourage n'est nécessaire). Le bolide, lui, est en alpha : ses plaques sont
## SOMBRES MAIS OPAQUES, et un additif les rendrait transparentes — on verrait les étoiles
## à travers la roche.
func _sprite_panel(panel_name: String, path: String, size: float, additive: bool,
		energy: float) -> MeshInstance3D:
	if not ResourceLoader.exists(path):
		return null
	var quad := QuadMesh.new()
	quad.size = Vector2(size, size)
	var material := StandardMaterial3D.new()
	material.albedo_texture = load(path) as Texture2D
	material.albedo_color = Color.WHITE
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.emission_enabled = true
	material.emission_texture = material.albedo_texture
	material.emission = Color.WHITE
	# ⚠️ SOUS LE SEUIL DE BLOOM (1,6). C'est le dépassement qui a noyé les plaques du bolide
	# à l'itération précédente : le halo des fissures débordait et remplissait la roche.
	material.emission_energy_multiplier = energy
	if additive:
		material.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	# Un panneau qui écrirait la profondeur masquerait ce qui passe derrière lui.
	material.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	var node := MeshInstance3D.new()
	node.name = panel_name
	node.mesh = quad
	node.material_override = material
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	node.position = MOON_CENTER
	node.visible = false
	return node

## Pose une carte sur un matériau si elle existe, sans rien casser si elle manque.
static func _apply_map(material: StandardMaterial3D, slot: String, path: String) -> void:
	if ResourceLoader.exists(path):
		material.set(slot, load(path) as Texture2D)

## Fait s'éteindre une pièce LE LONG DE SA LONGUEUR, par un dégradé d'opacité.
##
## ⚠️ C'EST CE QUI SÉPARE UNE TRAÎNÉE D'UN MORCEAU DE CARTON. Sans lui, un cône additif à
## opacité constante rend un aplat à contour franc : la matière s'arrête net au lieu de se
## dissiper. Aucun réglage d'énergie ne le corrige — c'est la forme du signal qui est
## fausse, pas son intensité.
##
## Le dégradé est VERTICAL dans l'UV (`fill_from`/`fill_to` sur l'axe Y) parce que la
## coordonnée V d'un `CylinderMesh` court le long de sa hauteur ; un `GradientTexture1D`,
## échantillonné sur U, aurait fait varier l'opacité AUTOUR de la circonférence — donc des
## bandes dans le mauvais sens, ce qui a l'air d'un bug de texture et non d'un axe inversé.
func _fade_along_length(node: MeshInstance3D) -> void:
	# ⚠️ UN DÉGRADÉ THERMIQUE, PAS UNE SIMPLE OPACITÉ. Une traînée d'une seule teinte se lit
	# comme un ruban de papier : ce qui dit le FEU, c'est la température qui décroît le long
	# du sillage — blanc au contact, orange derrière, rouge sombre à la queue. C'est ce que
	# montre la cible de l'opérateur, et c'est ce qu'une opacité seule ne peut pas rendre.
	var ramp := Gradient.new()
	ramp.offsets = PackedFloat32Array([0.0, 0.45, 0.80, 1.0])
	ramp.colors = PackedColorArray([
		Color(0.75, 0.10, 0.02, 0.0),   # la queue : rouge sombre, dissipée
		Color(0.95, 0.28, 0.05, 0.55),  # le rouge du sillage
		Color(1.00, 0.62, 0.18, 0.9),   # l'orange
		Color(1.00, 0.96, 0.86, 1.0),   # le blanc du contact
	])
	var tex := GradientTexture2D.new()
	tex.gradient = ramp
	tex.width = 4
	tex.height = 64
	tex.fill_from = Vector2(0.0, 0.0)
	tex.fill_to = Vector2(0.0, 1.0)
	var material := node.material_override as StandardMaterial3D
	if material != null:
		material.albedo_texture = tex
		# ⚠️ BLANC : `albedo = albedo_texture × albedo_color`. Garder la teinte chaude ici
		# la multiplierait par celle du dégradé et écraserait tout vers l'orange — le blanc
		# du contact deviendrait un jaune, et la rampe thermique n'existerait plus.
		material.albedo_color = Color.WHITE
		material.emission = Color(1.0, 0.55, 0.20)

## Le maillage d'une coque forgée, ou `null` si elle n'a pas encore été livrée.
##
## ⚠️ Un SEUL maillage partagé par les quatorze éclats. Instancier la scène quatorze fois
## allouerait quatorze copies d'une géométrie de vingt triangles, pour rien.
static func _forged_mesh(path: String) -> Mesh:
	if not ResourceLoader.exists(path):
		return null
	var packed := load(path) as PackedScene
	if packed == null:
		return null
	var root := packed.instantiate()
	var found: Mesh = null
	for mesh in _meshes_under(root):
		found = mesh.mesh
		break
	root.queue_free()
	return found

## Une pièce forgée posée au repos, ou la doublure géométrique si elle manque.
##
## ⚠️ L'AXE LONG DE LA COQUE EST Z, ET `basis_from_up()` ALIGNE Y. La pointer telle quelle
## sur sa course la coucherait EN TRAVERS — relevé par la forge avant l'intégration, et
## c'est le genre de défaut qui se voit à peine à huit pixels tout en annulant le travail.
## On la fait donc tourner d'un quart de tour pour amener son axe long sur Y, une fois pour
## toutes, dans un pivot : ainsi la base d'orientation reste la même que pour la traînée.
func _forged(piece_name: String, path: String, radius: float) -> MeshInstance3D:
	var mesh := _forged_mesh(path)
	if mesh == null:
		return _rock(piece_name, radius, MOON_CENTER)
	var node := MeshInstance3D.new()
	node.name = piece_name
	node.mesh = mesh
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	node.position = MOON_CENTER
	return node

## Un cône incandescent, préalloué. `bottom` et `top` sont les rayons à la base et au
## sommet ; la hauteur vaut 1 et se pose ensuite par l'échelle, ce qui évite de reconstruire
## un maillage à chaque image.
##
## ⚠️ ADDITIF ET NON ÉCLAIRÉ. Le décor n'a aucune lumière qui puisse rendre une gerbe
## crédible à 96 unités, et un mélange normal sur fond noir donnerait une forme mate. En
## additif, la gerbe s'ajoute au ciel : elle brûle au lieu de se poser dessus.
func _cone(cone_name: String, bottom: float, top: float, height: float,
		energy: float) -> MeshInstance3D:
	var mesh := CylinderMesh.new()
	mesh.bottom_radius = bottom
	mesh.top_radius = top
	mesh.height = height
	# 24 segments et non 12 : l'anneau d'onde fait 11 unités de rayon, soit ~100 px de
	# large à l'écran, où un dodécagone se lit comme un dodécagone.
	mesh.radial_segments = 24
	mesh.rings = 1
	var material := StandardMaterial3D.new()
	material.albedo_color = IMPACT_WARM
	material.emission_enabled = true
	material.emission = IMPACT_WARM
	material.emission_energy_multiplier = energy
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	# Un additif qui écrit la profondeur masquerait ce qui passe derrière lui.
	material.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	var node := MeshInstance3D.new()
	node.name = cone_name
	node.mesh = mesh
	node.material_override = material
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	node.visible = false
	node.position = MOON_CENTER
	return node

## Longueur de la traînée à `t` secondes de chute. Elle CROÎT avec la distance déjà
## parcourue puis plafonne : une traînée à pleine longueur dès la première image se lit
## comme un trait posé, pas comme quelque chose qui arrive.
##
## Pure et statique, comme `bolide_position` et pour la même raison — un effet qui ne se
## joue que trois fois par phase, à onze secondes d'intervalle, ne se vérifie pas à l'œil.
static func trail_length(t: float) -> float:
	var progress := clampf(t / BOLIDE_FALL, 0.0, 1.0)
	# La distance réellement parcourue suit `1 - (1-p)²` — l'inverse de la chute accélérée
	# de `bolide_position`, donc la traînée s'allonge vite à la fin, quand ça compte.
	var travelled := BOLIDE_DROP * progress * progress
	return minf(travelled, TRAIL_LENGTH)

## Rayon et hauteur de la gerbe à `life` (0 à 1). Elle monte VITE puis s'évase en
## ralentissant : c'est le profil d'une éjection, où la matière part d'un coup et retombe.
static func plume_shape(life: float) -> Vector2:
	var t := clampf(life, 0.0, 1.0)
	var rise := sqrt(t)                  # la hauteur part d'un coup
	var spread := t * t                  # l'évasement vient après
	return Vector2(PLUME_RADIUS * (0.15 + 0.85 * spread), PLUME_HEIGHT * rise)

## Opacité de la gerbe. Elle tient sa pleine intensité brièvement puis s'éteint — un
## fondu linéaire depuis la première image ferait un voile qui s'évapore, pas un choc.
static func plume_fade(life: float) -> float:
	var t := clampf(life, 0.0, 1.0)
	if t < 0.15:
		return t / 0.15
	return 1.0 - (t - 0.15) / 0.85

## La base de la caméra active, ou une base de repli hors arbre de scène.
##
## ⚠️ `get_camera_3d()` rend `null` en mode `--script` (pas d'arbre), et une base nulle ferait
## disparaître les panneaux sans une erreur. Le repli n'est pas « joli », il est VALIDE —
## c'est tout ce qu'on lui demande.
func _camera_basis() -> Basis:
	if is_inside_tree():
		var cam := get_viewport().get_camera_3d()
		if cam != null:
			return cam.global_transform.basis
	return Basis.IDENTITY

## Base d'un panneau posé DANS LE PLAN DE LA CAMÉRA, dont l'axe long suit la projection
## écran de `heading`.
##
## ⚠️ C'est ce qui règle le défaut de l'itération n°2 : un effet aligné sur une direction du
## MONDE est vu en enfilade dès que la caméra plonge, et s'écrase en tache. Un panneau posé
## dans le plan de la caméra garde toute sa longueur à l'écran, quel que soit l'angle.
##
## `roll` tourne le panneau autour de l'axe de vue : les deux images de l'opérateur portent
## leur sujet sur la DIAGONALE, il faut donc les redresser (`SPRITE_DIAGONAL`).
##
## Pure et statique, et elle reçoit la base de la caméra en paramètre plutôt que d'aller la
## chercher : en mode `--script` il n'y a pas d'arbre de scène, donc pas de caméra.
static func billboard_basis(camera_basis: Basis, heading: Vector3, roll: float,
		length: float, width: float) -> Basis:
	var toward_camera := camera_basis.z.normalized()
	# `heading` projeté dans le plan de la caméra : on retire sa composante de profondeur.
	var axis := heading - toward_camera * heading.dot(toward_camera)
	# ⚠️ CAS DÉGÉNÉRÉ, ET IL EST SILENCIEUX : une course parallèle à l'axe de vue se projette
	# en un point. Normaliser un vecteur nul rend `NaN`, qui se propage jusqu'à faire
	# disparaître le panneau sans une seule erreur au journal — même piège que
	# `basis_from_up()`. On retombe alors sur la verticale écran, qui est toujours valide.
	if axis.length_squared() < 0.000001:
		axis = camera_basis.y
	axis = axis.normalized()
	var side := axis.cross(toward_camera).normalized()
	var a := deg_to_rad(roll)
	var turned_side := side * cos(a) + axis * sin(a)
	var turned_axis := axis * cos(a) - side * sin(a)
	return Basis(turned_side * width, turned_axis * length, toward_camera)

## Une base orientée dont l'axe Y suit `up`. ⚠️ Les cônes de Godot (`CylinderMesh`) sont
## bâtis le long de +Y : sans cette base, traînée et gerbe pointeraient vers le haut du
## MONDE et non vers la verticale locale de la lune — un détail qui ne se voit qu'aux
## impacts loin du sommet, donc deux fois sur trois.
static func basis_from_up(up: Vector3) -> Basis:
	var y := up.normalized()
	# Un axe de référence qui n'est jamais colinéaire à `y` : sinon le produit vectoriel
	# rend zéro et la base devient invalide, en silence.
	var seed := Vector3.RIGHT if absf(y.dot(Vector3.RIGHT)) < 0.9 else Vector3.FORWARD
	var x := seed.cross(y).normalized()
	return Basis(x, y, x.cross(y).normalized())

## Monte le bolide, le flash et les éclats. Rien n'est alloué passé ce point.
func _build_impact_kit() -> void:
	# ⚠️ AU REPOS, TOUT DORT AU CENTRE DE LA LUNE. Invisible ne suffit pas : posé à
	# l'origine, ce kit se serait tenu en plein milieu du plan de jeu, prêt à s'y afficher
	# à la moindre erreur de visibilité.
	# ⚠️ INCANDESCENT, ET PAS QU'UN CAILLOU. Première capture : un rocher de rayon 1,1
	# à la teinte du décor (albédo 0,10) était **invisible** à 30 unités sur fond noir —
	# l'impact tombait de nulle part. Le joueur doit VOIR venir le coup : le bolide
	# s'allume, comme tout ce qui brûle dans ce jeu.
	# ⚠️ PETIT. À 1,9 de rayon il rendait un disque de 114 px posé sur la lune : plus gros
	# que le choc qu'il allait produire, et sans profondeur puisqu'il n'est pas ombré.
	# Les images d'abord ; la coque forgée et le cône restent le REPLI, comme le décor.
	_bolide = _sprite_panel("Bolide", BOLIDE_SPRITE, BOLIDE_SPRITE_SIZE, false, 1.2)
	_painted_bolide = _bolide != null
	if _bolide == null:
		_bolide = _forged("Bolide", BOLIDE_PATH, 0.85 * BOLIDE_SCALE)
	# ⚠️ LE REPLI SEULEMENT. Ce matériau habille la coque forgée quand l'image n'est pas là ;
	# l'appliquer sur le panneau peint écraserait le sprite qu'on vient de poser.
	if not _painted_bolide:
		var bolide_material := StandardMaterial3D.new()
		# ⚠️ UNE ROCHE FISSURÉE, PAS UNE BRAISE UNIFORME. C'est la cible donnée par l'opérateur :
		# des plaques SOMBRES séparées par des fissures incandescentes. Un aplat chaud — ce
		# qu'il y avait — n'a ni matière ni forme ; l'incandescence doit se loger dans les CREUX
		# et nulle part ailleurs.
		bolide_material.albedo_color = Color(0.11, 0.10, 0.11)
		_apply_map(bolide_material, "albedo_texture", ROCK_MAPS + "_mul.png")
		_apply_map(bolide_material, "normal_texture", ROCK_MAPS + "_nrm.png")
		bolide_material.normal_enabled = bolide_material.normal_texture != null
		# La tuile de roche couvre 8 m ; le bolide en fait ~2,3. Sans retuilage on n'en verrait
		# qu'un quart — deux ou trois plaques géantes, pas un réseau de fissures.
		bolide_material.uv1_scale = Vector3.ONE * 4.0
		bolide_material.emission_enabled = true
		# Le masque est DÉRIVÉ de la hauteur de `TEX-0002` (`derive-maps.py --glow`) : l'inverse
		# durci de la hauteur, donc clair au fond des crevasses et éteint sur les plaques —
		# 11,1 % de la surface allumée, mesuré. Rien de généré, tout dérivé.
		_apply_map(bolide_material, "emission_texture", ROCK_MAPS + "_glow.png")
		bolide_material.emission = Color(1.0, 0.42, 0.10)
		# ⚠️ 1,2 ET NON 3,2 — MESURÉ, PAS ESTIMÉ. À 3,2 la tête rendait une luminance MOYENNE de
		# 165/255 avec 11 % de pixels écrêtés : les plaques sombres disparaissaient et il ne
		# restait qu'un aplat crème. Le contraste local était pourtant bon (13,67, quasiment
		# celui de la lune) — la matière ÉTAIT là, l'exposition la noyait.
		#
		# C'est la nuance que « ce qui doit rester discret doit être FIN » ne dit pas : une
		# fissure fine reste fine, mais si le fond qu'elle traverse est lui-même surexposé, il
		# n'y a plus de contraste pour la porter. Ce qui brûle a besoin de quelque chose de
		# SOMBRE autour, sinon rien ne brûle.
		bolide_material.emission_energy_multiplier = 1.2
		# ⚠️ ÉCLAIRÉ, ET NON PLUS EN APLAT. Non éclairée, la coque rendait sa couleur pleine sur
		# toute sa surface : à vingt pixels, un aplat n'a pas de forme — on paie 32 triangles
		# pour dessiner un rectangle. Éclairée, ses facettes prennent la lumière et la
		# silhouette existe ; l'émission ne sert plus qu'à dire qu'elle brûle, et reste sous le
		# seuil de bloom (1,6) pour ne pas la renoyer dans un halo.
		_bolide.material_override = bolide_material
		_bolide.material_override = bolide_material
	_bolide.visible = false
	add_child(_bolide)
	_trail = _sprite_panel("ImpactTrail", TRAIL_SPRITE, TRAIL_SPRITE_SIZE, true, 1.3)
	_painted_trail = _trail != null
	if _trail != null:
		add_child(_trail)
	else:
		_trail = _build_trail_cone()

	_dust = _build_dust()
	_plume = _cone("ImpactPlume", 1.0, 1.0, 1.0, 1.5)
	# ⚠️ SANS COUVERCLES : un tube plein, vu d'au-dessus, redevient le disque jaune qu'on
	# corrige. C'est l'ANNEAU qui dit l'onde de choc.
	var ring := _plume.mesh as CylinderMesh
	ring.cap_top = false
	ring.cap_bottom = false
	add_child(_plume)

	var flash_mesh := SphereMesh.new()
	flash_mesh.radius = 1.0
	flash_mesh.height = 2.0
	flash_mesh.radial_segments = 12
	flash_mesh.rings = 6
	var flash_material := StandardMaterial3D.new()
	# Émissif et non éclairé : un impact est une SOURCE, pas une surface.
	# ⚠️ ET IL PARLE LA LANGUE DU JEU. Le premier essai était crème (1 / 0,93 / 0,78) et
	# se lisait comme un disque de papier posé sur la lune. Tout ce qui explose ici est
	# d'un orange saturé (`VfxExplosion._TINT`, ADR-0009) : un choc d'une autre couleur
	# n'est pas une variation, c'est un objet qu'on ne reconnaît pas.
	flash_material.albedo_color = IMPACT_WARM
	flash_material.emission_enabled = true
	flash_material.emission = IMPACT_WARM
	flash_material.emission_energy_multiplier = 9.0
	flash_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_flash = MeshInstance3D.new()
	_flash.name = "ImpactFlash"
	_flash.mesh = flash_mesh
	_flash.material_override = flash_material
	_flash.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_flash.position = MOON_CENTER
	_flash.visible = false
	add_child(_flash)

	var shard_material := StandardMaterial3D.new()
	# Plus CLAIRS que la lune, pas plus sombres : des éclats noirs sur une surface sombre
	# se lisaient comme des trous. Ce sont des morceaux arrachés, ils prennent la lumière.
	shard_material.albedo_color = Color(0.42, 0.39, 0.40)
	shard_material.roughness = 1.0
	var shard_mesh := _forged_mesh(SHARD_PATH)
	for i in SHARD_COUNT:
		var shard := MeshInstance3D.new()
		shard.name = "Shard_%02d" % i
		if shard_mesh != null:
			shard.mesh = shard_mesh
		else:
			var box := BoxMesh.new()
			box.size = Vector3(0.72, 0.40, 1.0)
			shard.mesh = box
		shard.material_override = shard_material
		shard.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		shard.position = MOON_CENTER
		shard.visible = false
		add_child(shard)
		_shards.append(shard)
		# Les vitesses sont semées à la MAIN autour de la verticale, une fois pour toutes :
		# une gerbe tirée au sort changerait à chaque partie, et aucune capture ne se
		# comparerait à la précédente.
		# ⚠️ L'ANGLE EST DÉCALÉ, ET C'EST TOUT LE SUJET. À `TAU * i / N` exactement, les
		# quatorze morceaux formaient une COURONNE régulière sur la surface : on lisait un
		# motif, pas une explosion. Le décalage est déterministe (une sinusoïde de l'indice,
		# pas un tirage) : la gerbe est irrégulière et pourtant identique à chaque partie,
		# donc deux captures restent comparables.
		var angle := TAU * float(i) / float(SHARD_COUNT) + sin(float(i) * 12.9898) * 0.55
		var spread := 0.30 + 0.55 * absf(sin(float(i) * 4.1372))
		_shard_velocities.append(Vector3(cos(angle) * spread, 1.0, sin(angle) * spread)
			.normalized() * SHARD_SPEED * (0.55 + 0.55 * absf(sin(float(i) * 7.233))))

## Déclenche l'impact prévu, s'il est l'heure, et fait vivre celui qui est en cours.
func _advance_impacts(delta: float) -> void:
	if _impact_age < 0.0 and _next_impact < IMPACT_TIMES.size() \
			and _clock >= IMPACT_TIMES[_next_impact]:
		_begin_impact(_next_impact)
		_next_impact += 1
	if _impact_age < 0.0:
		return
	_impact_age += delta
	var falling := _impact_age < BOLIDE_FALL
	var course := bolide_heading(_impact_at, _impact_up)
	var view := _camera_basis()
	if _bolide != null:
		_bolide.visible = falling
		if falling:
			_bolide.position = bolide_position(_impact_at, _impact_up, _impact_age)
			if _painted_bolide:
				_bolide.basis = billboard_basis(view, course, SPRITE_DIAGONAL, 1.0, 1.0)
			else:
				# Repli : l'axe long de la coque forgée est +Z (`BRIEF-0086`), et
				# `looking_at` fait pointer −Z vers sa cible — on vise donc l'OPPOSÉ de la
				# course pour que le corps soit aligné dessus.
				_bolide.basis = Basis.looking_at(-course).scaled(Vector3.ONE * BOLIDE_FIT)
	if _trail != null:
		_trail.visible = falling
		if falling:
			# Le cône s'étire DERRIÈRE la tête, le long de la verticale de chute, et son
			# origine est en son milieu : d'où le demi-décalage.
			var head := bolide_position(_impact_at, _impact_up, _impact_age)
			if _painted_trail:
				# ⚠️ L'EXTRÉMITÉ CHAUDE DE L'IMAGE N'EST PAS SON CENTRE : elle est près d'un
				# coin. On recule donc le panneau le long de la course pour que ce point
				# tombe sur la tête du bolide, sinon la flamme naît à côté du caillou.
				_trail.basis = billboard_basis(view, course, SPRITE_DIAGONAL, 1.0, 1.0)
				_trail.position = head + course * (TRAIL_SPRITE_SIZE * TRAIL_HEAD_OFFSET)
			else:
				# Repli : le cône suit la COURSE RÉELLE et non la verticale — alignée sur
				# elle, la traînée était vue en enfilade et se lisait comme une tache.
				var span := trail_length(_impact_age)
				_trail.basis = basis_from_up(course)
				_trail.scale = Vector3(1.0, maxf(span, 0.001), 1.0)
				_trail.position = head + course * span * 0.5
	var since := _impact_age - BOLIDE_FALL
	if since < 0.0:
		return
	# ⚠️ LE NUAGE PART UNE SEULE FOIS, ET ON TIENT LE DRAPEAU NOUS-MÊMES. `emitting` retombe
	# à `false` dès la salve ÉMISE — pas éteinte — donc le relire pour savoir si on a déjà
	# tiré rendrait « non » dès l'image suivante, et le nuage repartirait en boucle. Piège
	# documenté dans `pratique-geometries-invisibles.md`, déjà payé ailleurs.
	if _dust != null and not _dust_fired:
		_dust_fired = true
		_dust.position = _impact_at
		var dust_mat := _dust.process_material as ParticleProcessMaterial
		if dust_mat != null:
			# L'éventail part le long de la verticale LOCALE de la lune, et la poussière
			# retombe dessus : un impact près du limbe ne projette pas vers le haut du monde.
			dust_mat.direction = _impact_up
			dust_mat.gravity = -_impact_up * 4.5
		_dust.restart()
	if _plume != null and _dust == null:
		# La gerbe part du POINT D'IMPACT et monte le long de la verticale locale. Son
		# origine étant en son milieu, elle se pose à la moitié de sa hauteur.
		var plume_life := since / PLUME_LIFE
		_plume.visible = plume_life < 1.0
		if _plume.visible:
			var shape := plume_shape(plume_life)
			_plume.basis = basis_from_up(_impact_up)
			_plume.scale = Vector3(shape.x, maxf(shape.y, 0.001), shape.x)
			_plume.position = _impact_at + _impact_up * shape.y * 0.5
			var mat := _plume.material_override as StandardMaterial3D
			if mat != null:
				mat.albedo_color.a = plume_fade(plume_life)
	if _flash != null:
		# Le flash naît large et s'éteint en s'affaissant : c'est la forme d'un choc, pas
		# d'une bulle qui gonfle.
		var life := clampf(since / FLASH_LIFE, 0.0, 1.0)
		_flash.visible = life < 1.0
		if _flash.visible:
			_flash.position = _impact_at
			_flash.scale = Vector3.ONE * (0.5 + 1.4 * life) * (1.0 - life * 0.7)
	for i in _shards.size():
		var alive := since < SHARD_LIFE
		_shards[i].visible = alive
		if alive:
			_shards[i].position = shard_position(
				_impact_at, _shard_velocities[i], _impact_up, since)
			_shards[i].rotate_y(delta * 2.2)
	if since >= maxf(maxf(FLASH_LIFE, SHARD_LIFE), PLUME_LIFE):
		_end_impact()

func _begin_impact(index: int) -> void:
	var spot := IMPACT_SPOTS[index]
	var at := surface_point(spot.x, spot.y)
	if at == Vector3.INF:
		# Point demandé hors du disque de la lune : on le DIT et on saute. Un impact posé
		# « au mieux » se jouerait dans le vide, et se chercherait longtemps.
		push_error("[MoonFlyby] impact %d hors de la lune : (%.1f, %.1f)" % [index, spot.x, spot.y])
		return
	_impact_at = at
	_impact_up = (at - MOON_CENTER).normalized()
	_impact_age = 0.0
	_dust_fired = false

func _end_impact() -> void:
	_impact_age = -1.0
	if _bolide != null:
		_bolide.visible = false
	if _flash != null:
		_flash.visible = false
	if _trail != null:
		_trail.visible = false
	if _plume != null:
		_plume.visible = false
	if _dust != null:
		_dust.emitting = false
	for shard in _shards:
		shard.visible = false
