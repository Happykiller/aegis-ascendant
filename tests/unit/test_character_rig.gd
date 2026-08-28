extends "res://tests/test_case.gd"
## Le greement d'un personnage (`ADR-0035`) : ou poser chacun de ses calques.
##
## ⚠️ IL EXISTE PARCE QU'UN GENERATEUR D'IMAGES NE SAIT PAS CO-ENREGISTRER. Le contrat
## CHR-0001 exigeait « meme toile, meme cadrage, meme origine » ; la livraison du 2026-08-28 a
## rendu dix fichiers de 1024x1536 dont l'empilement etait FAUX — une tete de 907 px pour un
## corps de 1460. Le controle de dimensions la faisait passer pour conforme. Depuis CHR-0004
## la figure est d'un seul tenant : le greement ne place plus que les hologrammes autour d'elle.

const RigScript := preload("res://resources/data/character_rig.gd")
const PoseScript := preload("res://resources/data/layer_pose.gd")
const SHIPPED := "res://resources/dialogue/lyra_rig.tres"

func _pose(layer: StringName, group: StringName, scale: float, off: Vector2) -> LayerPose:
	var p: LayerPose = PoseScript.new()
	p.layer = layer; p.group = group; p.scale = scale; p.offset = off
	return p

func _rig(poses: Array) -> CharacterRig:
	var r: CharacterRig = RigScript.new()
	r.layers.assign(poses)
	return r

func test_a_pose_needs_a_layer_and_a_positive_scale() -> void:
	assert_true(_pose(&"", &"g", 1.0, Vector2.ZERO).validate().size() > 0, "sans calque, refus")
	assert_true(_pose(&"a", &"g", 0.0, Vector2.ZERO).validate().size() > 0, "echelle nulle, refus")
	assert_eq(_pose(&"a", &"g", 0.5, Vector2.ZERO).validate().size(), 0, "sinon il passe")

func test_a_layer_cannot_be_placed_twice() -> void:
	var r := _rig([_pose(&"tete", &"t", 1.0, Vector2.ZERO), _pose(&"tete", &"t", 1.0, Vector2.ZERO)])
	assert_true(r.validate().size() > 0, "deux placements pour un calque : lequel gagne ?")

## ⚠️ UN GROUPE PARTAGE SON PLACEMENT. Ses pieces ont ete dessinees ENSEMBLE, donc elles sont
## deja co-enregistrees entre elles : leur donner des valeurs differentes les desaligne, et le
## defaut ne se voit qu'a l'ecran.
func test_a_group_cannot_have_two_different_placements() -> void:
	var meme := _rig([_pose(&"tete", &"t", 0.5, Vector2(10, 20)),
			_pose(&"meches", &"t", 0.5, Vector2(10, 20))])
	assert_eq(meme.validate().size(), 0, "meme groupe, memes valeurs : c'est le cas normal")
	var divergent := _rig([_pose(&"tete", &"t", 0.5, Vector2(10, 20)),
			_pose(&"meches", &"t", 0.5, Vector2(11, 20))])
	assert_true(divergent.validate().size() > 0,
		"un pixel d'ecart dans un groupe est une faute de saisie, pas un reglage")

func test_bounds_covers_every_placed_layer() -> void:
	var r := _rig([_pose(&"a", &"", 1.0, Vector2.ZERO), _pose(&"b", &"", 0.5, Vector2(-600, -400))])
	var b := r.bounds()
	# Le calque `a` occupe toute la toile ; `b`, reduit et decale, deborde a gauche et en haut.
	assert_true(b.position.x < 0.0 and b.position.y < 0.0, "l'emprise suit le calque qui deborde")
	assert_true(b.end.x >= r.canvas.x and b.end.y >= r.canvas.y, "et couvre celui qui remplit")

func test_looking_up_an_unknown_layer_gives_nothing() -> void:
	var r := _rig([_pose(&"tete", &"t", 1.0, Vector2.ZERO)])
	assert_true(r.pose_of(&"tete") != null, "le calque place se trouve")
	assert_true(r.pose_of(&"orteil") == null, "un calque absent rend null, il ne plante pas")

## Le greement livre, celui que l'accueil monte vraiment.
func test_the_shipped_rig_is_sound_and_covers_the_delivered_layers() -> void:
	var rig: CharacterRig = load(SHIPPED)
	assert_true(rig != null, "le greement se charge")
	assert_eq(rig.validate().size(), 0, "et il est valide : %s" % str(rig.validate()))
	# ⚠️ CHAQUE CALQUE QUE LE MODULE MONTE DOIT ETRE PLACE. Un calque sans placement se
	# poserait plein cadre au milieu d'une figure assemblee — enorme, et au mauvais endroit.
	var attendus := PackedStringArray()
	attendus.append_array(LyraPortrait.LAYER_ORDER)
	for base in LyraPortrait.BASES:
		for suffix in LyraPortrait.MOUTH_SUFFIXES:
			attendus.append(base + suffix)
		for suffix in LyraPortrait.EYE_SUFFIXES:
			attendus.append(base + suffix)
	for nom in attendus:
		var fichier := "res://assets/imported/ui/characters/lyra/%s.png" % nom
		if not ResourceLoader.exists(fichier):
			continue   # calque pas encore livre : ce test ne juge pas la production
		assert_true(rig.pose_of(StringName(nom)) != null,
			"le calque `%s` est livre mais le greement ne le place pas" % nom)

## ⚠️ LA FIGURE EST D'UN SEUL TENANT, A L'ECHELLE 1. C'est la revision de CHR-0004 : la tete
## qui faisait les deux tiers du corps n'existe plus parce qu'il n'y a plus de tete a part.
## Si un calque `tete` ou `buste` revient dans ce greement, c'est le puzzle qui revient.
func test_the_figure_is_one_piece_at_scale_one() -> void:
	var rig: CharacterRig = load(SHIPPED)
	var figure := rig.pose_of(&"figure")
	assert_true(figure != null, "la figure est placee")
	assert_true(is_equal_approx(figure.scale, 1.0), "a l'echelle 1 — c'est elle la reference")
	assert_true(rig.pose_of(&"tete") == null and rig.pose_of(&"buste") == null,
		"aucun morceau de corps a part : le puzzle CHR-0001 est remplace")
	# Les holos sont plus petits que la figure : un holo a l'echelle du corps couvrirait la poitrine.
	var holo := rig.pose_of(&"holo_sphere")
	assert_true(holo != null and holo.scale < 0.5, "la sphere est placee, et petite")
	assert_true(rig.pose_of(&"holo_bracelet") == null, "le bracelet est retire (operateur, 2026-08-28)")
