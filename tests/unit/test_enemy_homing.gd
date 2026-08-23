extends "res://tests/test_case.gd"
## Poursuite ennemie (EnemyHoming) — le seul déplacement du jeu qui regarde le joueur.
##
## Une poursuite accumule : sa position dépend de tout son passé, donc elle ne peut
## pas être une `EnemyPath` (fonction pure de l'âge). ADR-0022 promet en échange
## qu'elle reste **déterministe en headless** — le test lui injecte une suite
## scriptée de positions joueur et joue le rôle du chasseur. C'est ce fichier qui
## tient cette promesse.

const DELTA := 1.0 / 60.0
const SPEED := 4.0
const TURN := 2.0 # rad/s

func test_it_turns_toward_the_player() -> void:
	var velocity := Vector2(0.0, -SPEED) # elle descend
	var after := EnemyHoming.steer(velocity, Vector2.ZERO, Vector2(5.0, -1.0), TURN, DELTA)
	assert_true(after.x > velocity.x, "elle a viré vers la droite, où est le joueur")

## ⚠️ LE CONTRAT QUI REND LA SANGSUE JOUABLE. Le virage est BORNÉ : un poursuivant
## qui vire instantanément touche toujours, et le joueur n'a plus que le tir à lui
## opposer. Bornée, elle se sème par un crochet. Même raison que le virage des
## missiles du boss.
func test_the_turn_is_capped_which_is_what_makes_it_dodgeable() -> void:
	var velocity := Vector2(0.0, -SPEED)
	# Joueur exactement derrière : un virage non borné ferait demi-tour en une image.
	var after := EnemyHoming.steer(velocity, Vector2.ZERO, Vector2(0.0, 6.0), TURN, DELTA)
	var turned := absf(velocity.angle_to(after))
	assert_true(turned <= TURN * DELTA + 0.0001,
		"le virage tient dans son plafond (%f rad pour %f permis)" % [turned, TURN * DELTA])
	assert_true(turned > 0.0, "mais elle a quand même commencé à virer")

## On tourne la vitesse, on ne la remplace pas : une sangsue ne peut pas accélérer
## en virant. Sans ça, la fuir en ligne droite deviendrait impossible.
func test_steering_never_changes_the_speed() -> void:
	var velocity := Vector2(0.0, -SPEED)
	for i in 120:
		velocity = EnemyHoming.steer(velocity, Vector2(0.0, 3.0), Vector2(2.0, -4.0), TURN, DELTA)
		assert_almost_eq(velocity.length(), SPEED, 0.0001, "la norme est conservée (image %d)" % i)

func test_a_unit_with_no_turn_rate_flies_straight() -> void:
	var velocity := Vector2(0.0, -SPEED)
	var after := EnemyHoming.steer(velocity, Vector2.ZERO, Vector2(9.0, 9.0), 0.0, DELTA)
	assert_true(after.is_equal_approx(velocity), "sans vitesse de virage, elle ne vire pas")

## Vitesse quasi nulle : la direction n'a plus de sens, la faire tourner enverrait
## la coque dans un cap arbitraire.
func test_an_almost_stopped_unit_keeps_its_heading() -> void:
	var crawling := Vector2(0.0, -EnemyHoming.MIN_STEERING_SPEED * 0.5)
	var after := EnemyHoming.steer(crawling, Vector2.ZERO, Vector2(5.0, 5.0), TURN, DELTA)
	assert_true(after.is_equal_approx(crawling), "elle garde son cap plutôt qu'un cap au hasard")

## Cible atteinte pile : normaliser un vecteur nul rendrait NaN, qui se propagerait
## dans la position sans une seule erreur au journal.
func test_sitting_exactly_on_the_player_produces_no_nan() -> void:
	var velocity := Vector2(1.0, -3.0)
	var after := EnemyHoming.steer(velocity, Vector2(2.0, 2.0), Vector2(2.0, 2.0), TURN, DELTA)
	assert_true(is_finite(after.x) and is_finite(after.y), "la vitesse reste finie (%s)" % after)

# --- Le cap de départ ---------------------------------------------------------

func test_it_launches_toward_the_player_at_cruising_speed() -> void:
	var velocity := EnemyHoming.initial_velocity(Vector2(0.0, 9.0), Vector2(3.0, -5.0), SPEED)
	assert_almost_eq(velocity.length(), SPEED, 0.0001, "elle part à son régime")
	assert_true(velocity.y < 0.0 and velocity.x > 0.0, "et dans la direction du joueur")

## Sans cap initial, `steer` n'aurait rien à faire tourner (norme nulle) et la
## sangsue resterait plantée à son point d'entrée — vivante, immobile, occupant une
## entrée de pool.
func test_a_degenerate_launch_still_moves() -> void:
	var velocity := EnemyHoming.initial_velocity(Vector2(1.0, 1.0), Vector2(1.0, 1.0), SPEED)
	assert_almost_eq(velocity.length(), SPEED, 0.0001, "elle part quand même")
	assert_true(velocity.y < 0.0, "vers le bas, faute de mieux")

# --- La promesse d'ADR-0022 ---------------------------------------------------

## Une poursuite accumule, donc elle n'est pas une fonction de l'âge. Elle reste
## pourtant REPRODUCTIBLE : même suite de positions joueur, même résultat, au bit
## près. C'est ce qui permet de la vérifier sans arbre de scène et sans joueur.
func test_a_scripted_chase_replays_identically() -> void:
	var script: Array[Vector2] = []
	for i in 90:
		script.append(Vector2(sin(i * 0.11) * 6.0, -5.0 + cos(i * 0.07)))
	var first := _chase(script)
	var second := _chase(script)
	assert_true(first.is_equal_approx(second),
		"deux exécutions rendent la même position (%s puis %s)" % [first, second])

## Et elle rapproche vraiment : c'est la seule chose qu'une poursuite doit garantir.
func test_a_chase_actually_closes_the_distance() -> void:
	var script: Array[Vector2] = []
	for i in 90:
		script.append(Vector2(3.0, -5.0))
	var start := Vector2(-6.0, 8.0)
	var ending := _chase(script, start)
	assert_true(ending.distance_to(Vector2(3.0, -5.0)) < start.distance_to(Vector2(3.0, -5.0)),
		"elle a réduit l'écart (%f -> %f)" % [start.distance_to(Vector2(3.0, -5.0)),
			ending.distance_to(Vector2(3.0, -5.0))])

func _chase(script: Array[Vector2], start: Vector2 = Vector2(-6.0, 8.0)) -> Vector2:
	var position := start
	var velocity := EnemyHoming.initial_velocity(position, script[0], SPEED)
	for target in script:
		velocity = EnemyHoming.steer(velocity, position, target, TURN, DELTA)
		position += velocity * DELTA
	return position

func test_catching_is_a_distance_and_nothing_else() -> void:
	assert_true(EnemyHoming.has_caught(Vector2(0.0, 0.0), Vector2(0.3, 0.4), 0.6),
		"à 0,5 d'écart avec une portée de 0,6, elle a mordu")
	assert_false(EnemyHoming.has_caught(Vector2(0.0, 0.0), Vector2(0.3, 0.4), 0.4),
		"avec une portée de 0,4, pas encore")
