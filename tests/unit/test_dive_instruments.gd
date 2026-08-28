extends "res://tests/test_case.gd"
## Les instruments du combat final. Ils vivaient dans `graybox_root.gd` et n'etaient donc
## testables par RIEN : le niveau ne se monte pas a la main. C'est tout l'interet de les
## avoir sortis — ce fichier n'existait pas, il ne pouvait pas exister.

const InstrumentsScript := preload("res://scripts/debug/dive_instruments.gd")
const PlayerScript := preload("res://scripts/player/player_fighter_controller.gd")

func _player() -> PlayerFighterController:
	var player := track(PlayerScript.new()) as PlayerFighterController
	player.stats = load("res://resources/player/specter9_stats.tres")
	player.plane_position = Vector2(1.5, -2.5)
	return player

func _walls() -> PlaneShapes:
	var shapes := PlaneShapes.new()
	shapes.reserve(1)
	shapes.add_disc(Vector2.ZERO, 2.0)
	return shapes

## Sans drapeau, il n'y a pas d'instrument du tout : le niveau ne paie meme pas un appel.
func test_no_flag_means_no_instrument() -> void:
	assert_true(InstrumentsScript.from_args(PackedStringArray()) == null,
		"aucun drapeau, aucun instrument")
	assert_true(InstrumentsScript.from_args(PackedStringArray(["--novsync"])) == null,
		"un drapeau qui ne les concerne pas non plus")
	assert_false(InstrumentsScript.from_args(PackedStringArray(["--dive-trace"])) == null,
		"mais `--dive-trace` en monte un")
	assert_false(InstrumentsScript.from_args(PackedStringArray(["--dive-probe"])) == null,
		"et `--dive-probe` aussi")

## ⚠️ L'ENREGISTREUR COUVRE TOUT LE COMBAT, PAS SEULEMENT LA PLONGEE. La premiere version ne
## s'armait que dans le noyau : un defaut survenu pendant l'armure ne laissait aucune trace,
## et il fallait refaire une partie pour rien.
func test_the_recorder_covers_the_whole_fight_not_just_the_dive() -> void:
	var instruments: DiveInstruments = InstrumentsScript.from_args(
		PackedStringArray(["--dive-trace"]))
	var player := _player()
	var walls := _walls()
	# Hors du combat final : rien ne s'enregistre.
	for frame in 10:
		instruments.tick(1.0 / 60.0, player, walls, false, false, Vector2.ZERO)
	assert_eq(instruments.recorded(), 0, "hors du boss final, l'instrument se tait")
	# Pendant l'armure (combat final, hors plongee) : il enregistre.
	for frame in 10:
		instruments.tick(1.0 / 60.0, player, walls, true, false, Vector2.ZERO)
	assert_eq(instruments.recorded(), 10, "pendant l'armure, il enregistre")
	for frame in 5:
		instruments.tick(1.0 / 60.0, player, walls, true, true, Vector2.ZERO)
	assert_eq(instruments.recorded(), 15, "et pendant la plongee aussi")

## Une ligne doit dire la meme chose que son en-tete, sinon la trace ment a qui la relit.
func test_a_recorded_line_matches_its_header() -> void:
	var instruments: DiveInstruments = InstrumentsScript.from_args(
		PackedStringArray(["--dive-trace"]))
	var player := _player()
	instruments.tick(1.0 / 60.0, player, _walls(), true, true, Vector2.ZERO)
	var line := instruments.line_at(0)
	var colonnes: PackedStringArray = InstrumentsScript.header().split("|")[0].split(";")
	var champs: PackedStringArray = line.split("|")[0].split(";")
	assert_eq(champs.size(), colonnes.size(),
		"%d champs pour %d colonnes annoncees" % [champs.size(), colonnes.size()])
	assert_almost_eq(float(champs[3]), player.plane_position.x, 0.001,
		"la position x est bien celle du chasseur")
	assert_almost_eq(float(champs[4]), player.plane_position.y, 0.001,
		"et la position y aussi")
	assert_eq(int(champs[6]), 1, "le drapeau de plongee dit qu'on y est")
	# ⚠️ ET LES FORMES SUIVENT, sinon la trace ne repond pas a la question qui l'a fait
	# naitre : « enregistre le deplacement du vaisseau EN MEME TEMPS que la position des
	# murs » (operateur, 2026-08-28).
	assert_eq(line.split("|").size(), 2, "une forme solide est jointe a l'image")

## ⚠️ UN INSTRUMENT NE DOIT JAMAIS FAIRE TOMBER LE JEU. Il tourne dans la boucle physique,
## sous un drapeau qu'on active justement quand quelque chose va mal — donc au pire moment.
func test_it_survives_a_missing_fighter_or_missing_shapes() -> void:
	var instruments: DiveInstruments = InstrumentsScript.from_args(
		PackedStringArray(["--dive-trace", "--dive-probe"]))
	instruments.tick(1.0 / 60.0, null, _walls(), true, true, Vector2.ZERO)
	instruments.tick(1.0 / 60.0, _player(), null, true, true, Vector2.ZERO)
	var orphelin := track(PlayerScript.new()) as PlayerFighterController
	instruments.tick(1.0 / 60.0, orphelin, _walls(), true, true, Vector2.ZERO)
	assert_eq(instruments.recorded(), 0,
		"sans chasseur, sans formes ou sans reglages, il ne consigne rien et ne tombe pas")
