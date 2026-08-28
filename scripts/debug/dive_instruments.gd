class_name DiveInstruments
extends RefCounted
## Les deux instruments du combat final : la SONDE (`--dive-probe`), qui dit à voix haute ce
## que le chasseur subit, et l'ENREGISTREUR (`--dive-trace`), qui écrit une image par ligne
## dans un CSV relisible depuis WSL après un lancement Windows.
##
## ⚠️ ILS VIVAIENT DANS LE NIVEAU, ET ILS N'Y AVAIENT RIEN À FAIRE. Cent dix lignes de
## formatage de CSV et d'écriture de fichier au milieu du script qui orchestre les phases,
## le HUD et l'audio — et surtout **intestables** : `graybox_root` ne se monte pas à la main.
## Sortis ici, ils ne dépendent plus ni de l'arbre, ni des autoloads, ni du niveau : on leur
## passe ce qu'ils mesurent, et une suite peut les faire tourner (règle du projet : les
## unités se testent sans le moteur).
##
## Ils ne s'arment que sous drapeau. Sans drapeau, [method from_args] rend `null` et le
## niveau ne paie même pas un appel.

## Période d'échantillonnage de la sonde, en secondes. Quatre lignes par seconde : assez pour
## suivre un blocage, assez peu pour rester lisible dans un journal de partie.
const PROBE_PERIOD := 0.25

var _probe: bool = false
var _trace: bool = false
var _probe_clock: float = 0.0
var _trace_age: float = 0.0
var _lines := PackedStringArray()

## Rend l'instrument demandé par la ligne de commande, ou `null` si aucun drapeau ne
## l'appelle. Le niveau n'a donc rien à savoir des drapeaux.
static func from_args(args: PackedStringArray) -> DiveInstruments:
	var probe := "--dive-probe" in args
	var trace := "--dive-trace" in args
	if not (probe or trace):
		return null
	var instruments := DiveInstruments.new()
	instruments._probe = probe
	instruments._trace = trace
	return instruments

## Une image. `in_final_boss` arme l'enregistreur, `in_dive` arme la sonde.
func tick(delta: float, player: PlayerFighterController, solids: PlaneShapes,
		in_final_boss: bool, in_dive: bool, reactor_centre: Vector2) -> void:
	if player == null or player.stats == null or solids == null:
		return
	_tick_probe(delta, player, solids, in_dive, reactor_centre)
	_tick_trace(delta, player, solids, in_final_boss, in_dive)

## Écrit l'enregistrement à côté de l'exécutable, comme la capture d'écran — c'est le seul
## dossier que WSL peut relire après un lancement Windows. À appeler en quittant.
func flush() -> void:
	if not _trace or _lines.is_empty():
		return
	var path := OS.get_executable_path().get_base_dir().path_join("dive-trace.csv")
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		push_error("[DiveTrace] ecriture impossible : %s" % path)
		return
	file.store_line(header())
	for line in _lines:
		file.store_line(line)
	file.close()
	print("[DiveTrace] %d images -> %s" % [_lines.size(), path])

## L'en-tête du CSV. Public parce qu'un test doit pouvoir confronter une ligne à ses colonnes
## sans écrire de fichier — c'est le seul moyen de garder les deux d'accord.
static func header() -> String:
	return "t;input_x;input_y;pos_x;pos_y;contact;dive|formes(kind,p0..p5)"

## Combien d'images ont été enregistrées. Pour les tests, et pour dire au journal ce qu'on a.
func recorded() -> int:
	return _lines.size()

func line_at(index: int) -> String:
	return _lines[index] if index >= 0 and index < _lines.size() else ""

## Ce que le chasseur subit dans la chambre, mesuré dans le JEU et non dans un banc.
func _tick_probe(delta: float, player: PlayerFighterController, solids: PlaneShapes,
		in_dive: bool, reactor_centre: Vector2) -> void:
	if not _probe:
		return
	if not in_dive:
		_probe_clock = 0.0
		return
	_probe_clock -= delta
	if _probe_clock > 0.0:
		return
	_probe_clock = PROBE_PERIOD
	var here := player.plane_position
	var forward := player.plane_forward()
	var half: float = player.stats.body_half_length
	var radius: float = player.stats.body_radius
	var touching := PlaneCollider.capsule_blocks(solids, here, forward, half, radius)
	var freed := PlaneCollider.resolve_capsule(solids, here, forward, half, radius)
	print("[Dive] pos (%+.2f, %+.2f) | r=%.2f du centre | %s | poussee (%+.2f, %+.2f) | %d formes | bornes %.1f..%.1f"
		% [here.x, here.y, here.distance_to(reactor_centre),
			"CONTACT" if touching else "libre  ",
			freed.x - here.x, freed.y - here.y, solids.size(),
			GameplayPlane.bounds.position.y, GameplayPlane.bounds.end.y])

## Enregistre une image : le temps, la commande, la position, le contact, et TOUTES les
## formes solides telles que la collision les voit — murs compris, avec leur rotation.
##
## ⚠️ TOUT LE COMBAT, ET PLUS SEULEMENT LA PLONGÉE. La première version ne s'armait que dans
## le noyau : si le défaut se produit dehors — pendant l'armure, l'approche — elle n'en garde
## aucune trace, et il faut refaire une partie pour rien. Un instrument qui ne regarde qu'où
## l'on croit que le problème est ne sert qu'à confirmer ce qu'on croit.
func _tick_trace(delta: float, player: PlayerFighterController, solids: PlaneShapes,
		in_final_boss: bool, in_dive: bool) -> void:
	if not _trace or not in_final_boss:
		return
	_trace_age += delta
	var here := player.plane_position
	var forward := player.plane_forward()
	var touching := PlaneCollider.capsule_blocks(solids, here, forward,
		player.stats.body_half_length, player.stats.body_radius)
	var line := "%.4f;%.3f;%.3f;%.3f;%.3f;%d;%d" % [_trace_age,
		player.last_input.x, player.last_input.y, here.x, here.y,
		1 if touching else 0, 1 if in_dive else 0]
	for i in solids.size():
		var c := solids.centre_of(i)
		line += "|%d,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f" % [solids.kind_at(i), c.x, c.y,
			solids.param(i, 2), solids.param(i, 3), solids.param(i, 4), solids.param(i, 5)]
	_lines.append(line)
