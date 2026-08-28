extends "res://tests/test_case.gd"
## BulletManager collision, TTL and culling on the logical plane (spec §21.2).

var _hits: Array[float] = []
var _impacts: Array[Array] = []

func _on_hit(damage: float) -> void:
	_hits.append(damage)

func _on_target_hit(plane_position: Vector2, victim_team: int) -> void:
	_impacts.append([plane_position, victim_team])

func _make_target(team: int, pos: Vector2, radius: float) -> BulletTarget:
	var target := BulletTarget.make(team, radius, Callable(self, "_on_hit"))
	target.position = pos
	return target

func test_enemy_bullet_hits_player_target() -> void:
	var bm := BulletManager.new()
	bm.register_target(_make_target(BulletManager.Team.PLAYER, Vector2.ZERO, 0.3))
	bm.spawn_bullet(BulletManager.Team.ENEMY, Vector2(0.0, -0.2), Vector2(0.0, 1.0), 0.1, 15.0, 5.0)
	bm.step(1.0 / 60.0)
	assert_eq(_hits.size(), 1, "hit callback fired once")
	assert_almost_eq(_hits[0], 15.0, 0.0001, "damage forwarded")
	assert_eq(bm.active_count(), 0, "bullet released on hit")
	bm.free()

func test_same_team_never_hits() -> void:
	var bm := BulletManager.new()
	bm.register_target(_make_target(BulletManager.Team.PLAYER, Vector2.ZERO, 0.5))
	bm.spawn_bullet(BulletManager.Team.PLAYER, Vector2.ZERO, Vector2.ZERO, 0.2, 10.0, 5.0)
	bm.step(1.0 / 60.0)
	assert_eq(_hits.size(), 0, "no friendly fire")
	assert_eq(bm.active_count(), 1, "bullet still alive")
	bm.free()

func test_disabled_target_ignored() -> void:
	var bm := BulletManager.new()
	var target := _make_target(BulletManager.Team.PLAYER, Vector2.ZERO, 0.5)
	target.enabled = false
	bm.register_target(target)
	bm.spawn_bullet(BulletManager.Team.ENEMY, Vector2.ZERO, Vector2.ZERO, 0.2, 10.0, 5.0)
	bm.step(1.0 / 60.0)
	assert_eq(_hits.size(), 0, "disabled target not hit")
	bm.free()

func test_far_bullet_does_not_hit() -> void:
	var bm := BulletManager.new()
	bm.register_target(_make_target(BulletManager.Team.PLAYER, Vector2(-10.0, -6.0), 0.3))
	bm.spawn_bullet(BulletManager.Team.ENEMY, Vector2(10.0, 6.0), Vector2.ZERO, 0.1, 10.0, 5.0)
	bm.step(1.0 / 60.0)
	assert_eq(_hits.size(), 0, "distant bullet misses")
	assert_eq(bm.active_count(), 1, "distant bullet alive")
	bm.free()

## The hit callback only carries damage, so the impact VFX has no other way to
## learn where the hit landed or whose hull took it.
func test_hit_reports_impact_position_and_victim() -> void:
	var bm := BulletManager.new()
	bm.target_hit.connect(_on_target_hit)
	bm.register_target(_make_target(BulletManager.Team.PLAYER, Vector2(2.0, -3.0), 0.4))
	bm.spawn_bullet(BulletManager.Team.ENEMY, Vector2(2.0, -3.2), Vector2.ZERO, 0.1, 10.0, 5.0)
	bm.step(1.0 / 60.0)
	assert_eq(_impacts.size(), 1, "impact reported once")
	var where: Vector2 = _impacts[0][0]
	assert_true(where.distance_to(Vector2(2.0, -3.2)) < 0.05,
		"impact carries the bullet's position, not the target's (got %s)" % where)
	assert_eq(_impacts[0][1], BulletManager.Team.PLAYER, "victim team is the side that was hit")
	bm.free()

func test_miss_reports_no_impact() -> void:
	var bm := BulletManager.new()
	bm.target_hit.connect(_on_target_hit)
	bm.register_target(_make_target(BulletManager.Team.PLAYER, Vector2(-10.0, -6.0), 0.3))
	bm.spawn_bullet(BulletManager.Team.ENEMY, Vector2(10.0, 6.0), Vector2.ZERO, 0.1, 10.0, 5.0)
	bm.step(1.0 / 60.0)
	assert_eq(_impacts.size(), 0, "a miss draws nothing")
	bm.free()

## Regression: a boss died twice. Two bullets landing on the same frame both
## reached the hit callback — the first killed it, the second found health already
## at zero and ran the defeat path again, paying the reward and starting the
## docking sequence twice. A target that goes cold mid-pass must stop absorbing.
var _lethal_target: BulletTarget
var _lethal_hits: int = 0
var _lethal_bm: BulletManager

func _on_lethal_hit(_damage: float) -> void:
	_lethal_hits += 1
	# What a dying entity does: disable, then unregister from inside the callback.
	_lethal_target.enabled = false
	_lethal_bm.unregister_target(_lethal_target)

func test_dead_target_absorbs_no_further_bullets_this_frame() -> void:
	_lethal_bm = BulletManager.new()
	_lethal_target = BulletTarget.make(BulletManager.Team.ENEMY, 0.8, Callable(self, "_on_lethal_hit"))
	_lethal_target.position = Vector2.ZERO
	_lethal_bm.register_target(_lethal_target)
	for i in 4: # a whole salvo arriving together
		_lethal_bm.spawn_bullet(BulletManager.Team.PLAYER,
			Vector2(-0.3 + 0.2 * i, 0.0), Vector2.ZERO, 0.1, 10.0, 5.0)
	_lethal_bm.step(1.0 / 60.0)
	assert_eq(_lethal_hits, 1, "the killing blow lands once, not once per bullet")
	assert_eq(_lethal_bm.active_count(), 3, "the rest of the salvo flies on through")
	_lethal_bm.free()

func test_ttl_expiry_releases_bullet() -> void:
	var bm := BulletManager.new()
	bm.spawn_bullet(BulletManager.Team.ENEMY, Vector2.ZERO, Vector2.ZERO, 0.1, 10.0, 0.05)
	bm.step(0.1)
	assert_eq(bm.active_count(), 0, "expired bullet released")
	bm.free()

func test_out_of_bounds_releases_bullet() -> void:
	var bm := BulletManager.new()
	bm.spawn_bullet(BulletManager.Team.PLAYER, Vector2(0.0, 6.9), Vector2(0.0, 50.0), 0.1, 10.0, 10.0)
	bm.step(0.25) # -> y = 19.4, far beyond BOUNDS.end.y + CULL_MARGIN
	assert_eq(bm.active_count(), 0, "out-of-bounds bullet culled")
	bm.free()

# --- Écrans : les formes qui arrêtent un tir ----------------------------------

var _screened: Array[Array] = []

func _on_screened(plane_position: Vector2, team: int) -> void:
	_screened.append([plane_position, team])

## Un mur en travers, et un couloir a cote. Deux bolts identiques a 1,5 u l'un de l'autre :
## l'un doit mourir, l'autre passer.
##
## ⚠️ C'EST LA DIFFERENCE ENTRE UN ECRAN ET UNE CIBLE. Le blindage du Levithan etait une
## `BulletTarget` unique de rayon 0,95 : elle attrapait un disque de mur et laissait passer
## tout le reste — « on voit un cercle sur le mur qui bloque bien les tirs mais en dehors les
## tirs passent » (operateur, 2026-08-28). Un ecran arrete sur toute sa longueur.
func test_a_screen_stops_a_bullet_everywhere_along_the_wall() -> void:
	_screened.clear()
	var bm := BulletManager.new()
	bm.bullet_screened.connect(_on_screened)
	var walls := PlaneShapes.new()
	walls.reserve(1)
	# Un mur de 8 u de large, a y = 1, epais de 0,5 comme celui de la chambre.
	walls.add_capsule(Vector2(-4.0, 1.0), Vector2(4.0, 1.0), 0.25)
	bm.screens = walls
	for x: float in [0.0, 1.5, -3.0]:
		bm.spawn_bullet(BulletManager.Team.PLAYER, Vector2(x, 0.0), Vector2(0.0, 24.0),
			0.12, 10.0, 5.0)
	# 8 images a 60 Hz : 3,2 u de trajet, largement de quoi franchir y = 1.
	for frame in 8:
		bm.step(1.0 / 60.0)
	assert_eq(bm.active_count(), 0, "les trois bolts sont morts sur le mur, pas seulement celui du milieu")
	assert_eq(_screened.size(), 3, "et chacun a produit sa gerbe")
	for entry in _screened:
		var point: Vector2 = entry[0]
		assert_almost_eq(point.y, 0.75, 0.25,
			"la gerbe se pose sur la FACE du mur (y = %.2f), pas derriere" % point.y)
		assert_eq(int(entry[1]), BulletManager.Team.PLAYER, "et elle sait de qui etait le tir")
	bm.free()

## Hors de la chambre il n'y a pas d'ecran, et les balles ne doivent rien payer.
func test_without_screens_nothing_changes() -> void:
	_screened.clear()
	var bm := BulletManager.new()
	bm.bullet_screened.connect(_on_screened)
	bm.spawn_bullet(BulletManager.Team.PLAYER, Vector2.ZERO, Vector2(0.0, 24.0), 0.12, 10.0, 5.0)
	for frame in 8:
		bm.step(1.0 / 60.0)
	assert_eq(bm.active_count(), 1, "le bolt vole toujours")
	assert_eq(_screened.size(), 0, "et rien ne l'a arrete")
	bm.free()

## ⚠️ LE TUNNELING EST LE MODE D'ECHEC DE CE MECANISME, et il ne se voit pas : un bolt qui
## saute par-dessus un mur mince ne laisse ni erreur ni trace. On le mesure sur un mur
## VOLONTAIREMENT plus fin qu'un pas d'image.
func test_a_fast_bullet_cannot_tunnel_through_a_thin_wall() -> void:
	_screened.clear()
	var bm := BulletManager.new()
	bm.bullet_screened.connect(_on_screened)
	var walls := PlaneShapes.new()
	walls.reserve(1)
	walls.add_capsule(Vector2(-4.0, 2.0), Vector2(4.0, 2.0), 0.02)
	bm.screens = walls
	# 120 u/s : 2 u par image, cent fois l'epaisseur du mur.
	bm.spawn_bullet(BulletManager.Team.PLAYER, Vector2.ZERO, Vector2(0.0, 120.0), 0.01, 10.0, 5.0)
	for frame in 4:
		bm.step(1.0 / 60.0)
	assert_eq(bm.active_count(), 0, "il ne traverse pas : le trajet est echantillonne, pas juste son arrivee")
	assert_eq(_screened.size(), 1, "une gerbe, une seule")
	bm.free()

## Un ecran n'est pas une cible : il ne rend aucun degat a personne.
func test_a_screened_bullet_damages_nobody() -> void:
	_hits.clear()
	_screened.clear()
	var bm := BulletManager.new()
	bm.bullet_screened.connect(_on_screened)
	var walls := PlaneShapes.new()
	walls.reserve(1)
	walls.add_capsule(Vector2(-4.0, 1.0), Vector2(4.0, 1.0), 0.25)
	bm.screens = walls
	# Une cible ennemie DERRIERE le mur : le mur doit la proteger.
	bm.register_target(_make_target(BulletManager.Team.ENEMY, Vector2(0.0, 2.0), 0.5))
	bm.spawn_bullet(BulletManager.Team.PLAYER, Vector2.ZERO, Vector2(0.0, 24.0), 0.12, 10.0, 5.0)
	for frame in 8:
		bm.step(1.0 / 60.0)
	assert_eq(_hits.size(), 0, "la cible derriere le mur n'a rien pris")
	assert_eq(_screened.size(), 1, "le tir est mort sur le mur")
	bm.free()


## ⚠️ LA PHASE LARGE NE DOIT JAMAIS RATER UN TIR. Elle a ete ajoutee parce que le test fin
## coutait 1,55 ms par image au banc (150 bolts, 9 % du budget 60 Hz) ; elle ecarte d'avance
## les balles trop loin du mur, et celles qui volent DANS le puits central ou il n'y a rien.
## Un raccourci de perf qui laisse passer un tir est pire que le cout qu'il economise : ce
## test prend les vrais anneaux livres et tire depuis l'interieur du trou vers l'exterieur,
## en traversant toute l'epaisseur du mur.
func test_the_broad_phase_never_misses_a_bolt_leaving_the_central_well() -> void:
	_screened.clear()
	var previous := GameplayPlane.use_bounds(GameplayPlane.CHAMBER_BOUNDS)
	var tuning: LeviathanTuning = load("res://resources/bosses/pale_leviathan_tuning.tres")
	var walls := PlaneShapes.new()
	ReactorRings.fill_shapes(walls, tuning.reactor_rings, Vector2.ZERO, 0.0)
	assert_true(walls.size() > 0, "la chambre livree a bien des murs")
	var bm := BulletManager.new()
	bm.bullet_screened.connect(_on_screened)
	bm.screens = walls
	# Le milieu de la portion PLEINE de chaque arc : du mur, garanti. On tire depuis le
	# centre vers ce point, donc en partant du TROU que la phase large ecarte.
	var aimed := 0
	for i in walls.size():
		var radius: float = walls.param(i, 2)
		var angle: float = deg_to_rad(walls.param(i, 4) + walls.param(i, 5) * 0.5)
		var direction := Vector2(cos(angle), sin(angle))
		bm.spawn_bullet(BulletManager.Team.PLAYER, direction * 0.5, direction * 24.0,
			0.12, 10.0, 5.0)
		aimed += 1
	# De quoi traverser tout le rayon de la chambre.
	for frame in 60:
		bm.step(1.0 / 60.0)
	assert_eq(_screened.size(), aimed,
		"les %d bolts partis du puits sont tous morts sur leur mur" % aimed)
	assert_eq(bm.active_count(), 0, "aucun n'a traverse")
	bm.free()
	GameplayPlane.use_bounds(previous)


## ⚠️ LA MOITIE DE LA GERBE DU BOSS MOURAIT A SA NAISSANCE. Le Leviathan tire depuis ses
## plaques — `origin + 2,6` autour d'un corps pose a y = 11,9 — donc jusqu'a y = 14,5, quand
## la coupe des projectiles est a 13,0. La regle « hors du plan, on recycle » s'appliquait
## des le premier pas : les balles des plaques du HAUT disparaissaient a l'image de leur
## creation. Aucune erreur, aucune trace, et un compteur de projectiles juste. C'est le meme
## defaut que celui trouve sur les missiles du meme boss le 2026-08-28.
func test_a_bullet_born_above_the_cull_line_lives_until_it_gets_in() -> void:
	GameplayPlane.reset_bounds()
	var muzzle := Vector2(0.0, 14.5)   # une plaque haute du Leviathan, mesuree
	assert_false(GameplayPlane.is_inside(muzzle, BulletManager.CULL_MARGIN),
		"la bouche est bien HORS de la coupe : c'est tout le probleme")
	_hits.clear()
	var bm := BulletManager.new()
	# Une cible DANS le terrain, sur sa trajectoire : si elle la touche, c'est qu'elle a
	# survecu a sa naissance ET qu'elle est bien entree. On mesure le comportement, pas un
	# membre prive.
	bm.register_target(_make_target(BulletManager.Team.PLAYER, Vector2(0.0, 7.0), 0.4))
	bm.spawn_bullet(BulletManager.Team.ENEMY, muzzle, Vector2(0.0, -7.0), 0.18, 12.0, 5.0)
	bm.step(1.0 / 60.0)
	assert_eq(bm.active_count(), 1, "elle ne meurt pas a l'image de sa creation")
	for frame in 90:
		bm.step(1.0 / 60.0)
	assert_eq(_hits.size(), 1, "elle est entree dans le terrain et a touche sa cible")
	bm.free()

## Le pendant : la tolerance ne rend pas une balle immortelle. Le `ttl` la borne, sans qu'il
## ait fallu inventer un second compteur.
func test_a_bullet_fired_away_from_the_plane_still_dies_on_its_ttl() -> void:
	GameplayPlane.reset_bounds()
	var bm := BulletManager.new()
	bm.spawn_bullet(BulletManager.Team.ENEMY, Vector2(0.0, 14.5), Vector2(0.0, 40.0),
		0.18, 12.0, 0.5)
	for frame in 45:
		bm.step(1.0 / 60.0)
	assert_eq(bm.active_count(), 0, "jamais entree, elle meurt quand meme — sur son ttl")
	bm.free()

## Et une balle qui a VRAIMENT quitte le terrain est toujours recyclee tout de suite : la
## tolerance ne vaut qu'avant l'entree.
func test_a_bullet_that_leaves_after_entering_is_recycled_at_once() -> void:
	GameplayPlane.reset_bounds()
	var bm := BulletManager.new()
	var top: float = GameplayPlane.bounds.end.y + BulletManager.CULL_MARGIN
	bm.spawn_bullet(BulletManager.Team.PLAYER, Vector2(0.0, top - 0.2), Vector2(0.0, 24.0),
		0.12, 10.0, 5.0)
	bm.step(1.0 / 60.0)
	assert_eq(bm.active_count(), 0, "elle etait dedans, elle sort, elle part")
	bm.free()
