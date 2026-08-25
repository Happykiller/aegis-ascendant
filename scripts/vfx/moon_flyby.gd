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

func _ready() -> void:
	reveal(false)
	_build()

func is_stand_in() -> bool:
	return _is_stand_in

## Montre ou cache le survol. ⚠️ Coupe AUSSI `_process` : un décor invisible qui continue
## de faire dériver ses rochers dépense pour rien pendant les trois quarts de la partie.
func reveal(on: bool) -> void:
	visible = on
	set_process(on)

func _process(delta: float) -> void:
	if _moon != null:
		_moon.rotate_x(MOON_SPIN * delta)
	for i in _drifters.size():
		var body := _drifters[i]
		body.position = drifted(body.position, _drift_velocities[i], delta)

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
	if ResourceLoader.exists(DECOR_PATH):
		var packed := load(DECOR_PATH) as PackedScene
		if packed != null:
			_decor = packed.instantiate() as Node3D
	if _decor == null:
		_decor = _build_stand_in()
		_is_stand_in = true
	add_child(_decor)
	_collect_bodies()

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
	root.add_child(_sky())
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
	# Ce qui fait le change de décor : les trois couches de nuages tombent.
	material.set_shader_parameter("nebula_strength", 0.12)
	material.set_shader_parameter("dust_strength", 0.08)
	material.set_shader_parameter("accent_strength", 0.0)
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
	var mesh := MeshInstance3D.new()
	mesh.name = rock_name
	mesh.mesh = sphere
	mesh.material_override = material
	mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mesh.position = at
	mesh.scale = Vector3(1.0, 0.62, 0.84)
	mesh.rotation = Vector3(0.4, 1.1, -0.3)
	return mesh
