extends "res://tests/test_case.gd"
## Pièces articulées d'une coque ennemie (EnemyPose).
##
## Contrairement aux trajectoires et aux salves, celui-ci manipule de vrais Node3D :
## on les construit à la main et on les confie à `track()`, sinon ils fuient (mode
## `--script` : pas d'arbre, donc pas de parent pour les récupérer).
##
## Ce qu'on teste ici ne se voit sur AUCUNE capture d'écran fixe : une pièce mal
## articulée décrit un arc autour du centre de l'objet au lieu de basculer, et la
## pose au repos est parfaite dans les deux cas. C'est exactement le défaut qui a
## coûté une reforge de volet au Specter-9.

const OPEN_DEG := 40.0

## Une coque radiale de test : quatre pièces sur les quatre points cardinaux.
func _hull(count: int = 4, prefix: String = "Segment") -> Node3D:
	var hull := track(Node3D.new()) as Node3D
	for i in count:
		var angle := TAU * float(i) / float(count)
		var part := Node3D.new()
		part.name = "%s_%02d" % [prefix, i + 1]
		part.position = Vector3(sin(angle) * 0.5, 0.0, cos(angle) * 0.5)
		hull.add_child(part)
	return hull

func test_a_rigid_hull_binds_to_nothing() -> void:
	assert_true(EnemyPose.bind(_hull(), "", OPEN_DEG) == null, "sans préfixe, rien à poser")
	assert_true(EnemyPose.bind(_hull(), "Petal", OPEN_DEG) == null,
		"un préfixe qui ne correspond à rien ne rend pas un objet vide")
	assert_true(EnemyPose.bind(null, "Segment", OPEN_DEG) == null, "pas de coque, pas de pose")

## Les pièces se découvrent en série, jusqu'au premier trou. C'est ce qui permet à
## une coque à cinq pétales et une à six segments de partager le même code.
func test_it_finds_every_numbered_part() -> void:
	var hull := _hull(6)
	var pose := EnemyPose.bind(hull, "Segment", OPEN_DEG)
	assert_true(pose != null, "six segments sont trouvés")
	pose.pose(1.0)
	for child in hull.get_children():
		var part := child as Node3D
		assert_true(part.rotation.length() > 0.01,
			"%s a bien été posée (rotation %s)" % [part.name, part.rotation])

## ⚠️ LE PIÈGE. Une pièce doit BASCULER autour de sa charnière, pas tourner autour
## du centre de l'objet. La différence se mesure sur son ORIGINE : elle ne bouge
## pas d'un millimètre quand la coque s'ouvre — seule son orientation change.
func test_opening_never_moves_a_part_off_its_hinge() -> void:
	var hull := _hull()
	var pose := EnemyPose.bind(hull, "Segment", OPEN_DEG)
	var before: Array[Vector3] = []
	for child in hull.get_children():
		before.append((child as Node3D).position)
	pose.pose(1.0)
	for i in hull.get_child_count():
		var after := (hull.get_child(i) as Node3D).position
		assert_true(before[i].distance_to(after) < 0.0001,
			"la pièce %d a pivoté sur place (%s -> %s)" % [i, before[i], after])

## Chaque pièce bascule vers l'EXTÉRIEUR, donc autour d'un axe tangent à son propre
## rayon. Si toutes partageaient un axe unique, la coque s'ouvrirait comme un livre :
## deux pièces s'écarteraient et les deux autres s'enfonceraient dans le noyau.
func test_each_part_hinges_around_its_own_radius() -> void:
	var north := EnemyPose._hinge_axis(Vector3(0.0, 0.0, 0.5))
	var east := EnemyPose._hinge_axis(Vector3(0.5, 0.0, 0.0))
	assert_almost_eq(north.length(), 1.0, 0.0001, "l'axe est unitaire")
	assert_almost_eq(north.dot(Vector3(0.0, 0.0, 1.0)), 0.0, 0.0001,
		"et perpendiculaire au rayon de sa pièce")
	assert_almost_eq(absf(north.dot(east)), 0.0, 0.0001,
		"deux pièces opposées de 90 degres ont des axes distincts")

## Une pièce pile au centre : le rayon y est indéfini, et normaliser un vecteur nul
## rendrait NaN — une rotation NaN fait disparaître la pièce sans une seule erreur.
func test_a_part_at_the_dead_centre_gets_a_usable_axis() -> void:
	var axis := EnemyPose._hinge_axis(Vector3.ZERO)
	assert_almost_eq(axis.length(), 1.0, 0.0001, "l'axe reste utilisable (%s)" % axis)

func test_the_hull_closes_completely_at_rest() -> void:
	var hull := _hull()
	var pose := EnemyPose.bind(hull, "Segment", OPEN_DEG)
	pose.pose(1.0)
	pose.reset()
	for child in hull.get_children():
		assert_true((child as Node3D).rotation.length() < 0.0001,
			"%s est refermée" % (child as Node3D).name)

## Le garde-fou : une donnée absurde ne doit pas désassembler la coque à l'écran.
func test_an_absurd_opening_angle_is_capped() -> void:
	var hull := _hull()
	var pose := EnemyPose.bind(hull, "Segment", 400.0)
	pose.pose(1.0)
	var opened := (hull.get_child(0) as Node3D).rotation.length()
	assert_true(opened <= deg_to_rad(EnemyPose.MAX_OPEN_DEG) + 0.0001,
		"l'ouverture est plafonnée (%f°)" % rad_to_deg(opened))

## Un ratio hors bornes ne doit pas non plus passer : le contrôleur le calcule, mais
## une garde ici coûte une ligne et supprime la catégorie.
func test_the_ratio_is_clamped_at_both_ends() -> void:
	var hull := _hull()
	var pose := EnemyPose.bind(hull, "Segment", OPEN_DEG)
	pose.pose(4.0)
	var over := (hull.get_child(0) as Node3D).rotation.length()
	pose.pose(-2.0)
	var under := (hull.get_child(0) as Node3D).rotation.length()
	assert_almost_eq(over, deg_to_rad(OPEN_DEG), 0.0001, "au-delà de 1, elle est grande ouverte")
	assert_almost_eq(under, 0.0, 0.0001, "en deçà de 0, elle est fermée")

# --- Ce que l'ouverture RACONTE ------------------------------------------------

func _mine() -> EnemyData:
	var data := EnemyData.new()
	data.alert_radius = 4.0
	data.trigger_radius = 2.0
	data.windup_time = 0.6
	data.active_time = 0.4
	return data

## La coque s'ouvre pendant le télégraphe, et pas avant : une mine qui bâillerait
## dès qu'on l'approche aurait déjà tout dit, et les 700 ms qui décident n'auraient
## plus rien à montrer.
func test_the_hull_only_opens_during_the_windup() -> void:
	var data := _mine()
	assert_eq(EnemyReaction.open_ratio(EnemyReaction.State.DORMANT, 0.0, data), 0.0,
		"endormie, elle est fermée")
	assert_eq(EnemyReaction.open_ratio(EnemyReaction.State.ALERT, 2.0, data), 0.0,
		"éveillée, elle est encore fermée")
	assert_almost_eq(EnemyReaction.open_ratio(EnemyReaction.State.WINDUP, 0.3, data), 0.5,
		0.0001, "elle s'ouvre au rythme du télégraphe")
	assert_eq(EnemyReaction.open_ratio(EnemyReaction.State.ACTIVE, 0.1, data), 1.0,
		"et elle est grande ouverte à la charge")

## Les deux règles du jeu se lisent sur la carcasse : ce qui est fini reste ouvert,
## ce qui va revenir se referme. C'est ce qui rend visible, de loin, le moment où
## une zone interdite redevient dangereuse.
func test_a_spent_hull_says_whether_it_will_come_back() -> void:
	var once := _mine()
	assert_eq(EnemyReaction.open_ratio(EnemyReaction.State.SPENT, 1.0, once), 1.0,
		"à usage unique, elle reste ouverte : elle est finie")
	var again := _mine()
	again.rearm_time = 2.5
	assert_eq(EnemyReaction.open_ratio(EnemyReaction.State.SPENT, 1.0, again), 0.0,
		"si elle se réarme, elle se referme pendant son temps mort")
