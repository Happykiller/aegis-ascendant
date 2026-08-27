extends SceneTree
## Banc de plongée : pilote le VRAI chasseur dans la chambre du réacteur livrée, et dit ce
## qu'il subit. Lancer :
##   godot4 --headless --path . --script res://tools/dive_bench.gd
##
## ⚠️ IL PILOTE `PlayerFighterController._slide_to()`, PAS UNE COPIE. Trois bancs précédents
## ont recopié la boucle de collision à la main et ont conclu que tout allait bien pendant
## que l'opérateur vivait le contraire — chacun avait recopié une version différente. Ici,
## si le jeu a un défaut, le banc l'a aussi.
##
## Sortie : un verdict par scénario, et `build/bench/dive-*.svg` — la trajectoire sur les
## murs à quatre instants, à regarder (ADR-0006 : rien n'est jugé sans avoir été vu).

const PlayerScript := preload("res://scripts/player/player_fighter_controller.gd")
const STEP := 1.0 / 60.0

var tuning: LeviathanTuning
var stats: PlayerStats
var centre := CoreInterior.PLANE_OFFSET

func _init() -> void:
	tuning = load("res://resources/bosses/pale_leviathan_tuning.tres")
	stats = load("res://resources/player/specter9_stats.tres")
	GameplayPlane.use_bounds(GameplayPlane.CHAMBER_BOUNDS)
	var entry: Vector2 = centre + tuning.dive_entry_local()
	var failures := 0
	failures += _run("tout-droit", entry, func(_t: float) -> Vector2: return Vector2(0.0, 1.0))
	failures += _run("biais-droite", entry, func(_t: float) -> Vector2: return Vector2(0.5, 0.87))
	failures += _run("biais-gauche", entry, func(_t: float) -> Vector2: return Vector2(-0.5, 0.87))
	failures += _run("immobile-couloir", centre + Vector2(0.0, -5.2), func(_t: float) -> Vector2: return Vector2.ZERO)
	failures += _run("tour-du-noyau", centre + Vector2(0.0, -4.2),
		func(t: float) -> Vector2: return Vector2(cos(t * 0.8), sin(t * 0.8)))
	failures += _run("va-et-vient", entry,
		func(t: float) -> Vector2: return Vector2(0.0, 1.0 if fmod(t, 3.0) < 2.0 else -1.0))
	print("")
	print("=== %d scénario(s) en défaut ===" % failures)
	quit(1 if failures > 0 else 0)

## Rend 1 si le scénario révèle un défaut : pénétration, fantôme (déplacé sans contact et
## à l'envers de la commande), ou figé longtemps alors qu'aucun mur ne le touche.
func _run(label: String, start: Vector2, command: Callable) -> int:
	var player := PlayerScript.new() as PlayerFighterController
	player.stats = stats
	var solids := PlaneShapes.new()
	solids.reserve(ReactorRings.shape_count(tuning.reactor_rings) + 2)
	player.solids = solids
	player.plane_position = start
	var velocity := Vector2.ZERO
	var penetrations := 0
	var ghosts := 0
	var frozen_free := 0
	var carried := 0
	var contact := 0
	var path := PackedVector2Array()
	var snapshots := []
	var frames := int(tuning.dive_time * 60.0)
	for i in frames:
		var t := float(i) * STEP
		solids.clear()
		ReactorRings.fill_shapes(solids, tuning.reactor_rings, centre, t)
		solids.add_disc(centre, tuning.flux_hitbox_radius)
		solids.add_disc(centre, CoreInterior.REACTOR_HOUSING_RADIUS)
		var input: Vector2 = command.call(t)
		velocity = PlayerFighterController.integrate_velocity(velocity, input,
			stats.max_speed, stats.accel_time, STEP)
		var before := player.plane_position
		var wanted := GameplayPlane.clamp_to_bounds(before + velocity * STEP)
		var caught := PlaneCollider.capsule_blocks(solids, before, Vector2(0.0, 1.0),
			stats.body_half_length, stats.body_radius)
		# LE VRAI CHEMIN DU JEU.
		player.plane_position = player._slide_to(wanted, STEP)
		var after := player.plane_position
		var moved := after - before
		var touching := PlaneCollider.capsule_blocks(solids, after, Vector2(0.0, 1.0),
			stats.body_half_length, stats.body_radius)
		if touching:
			penetrations += 1
		if caught:
			carried += 1
		# ⚠️ CONTRE LE DÉPLACEMENT VOULU, PAS CONTRE LA COMMANDE. Au demi-tour, l'inertie
		# (`accel_time`) fait encore avancer le corps à l'envers de la commande neuve pendant
		# quelques images : c'est le pilotage, pas un mur. Comparer à la commande brute
		# accusait la physique d'un « fantôme » qu'elle ne produit pas.
		elif moved.length() > 0.001 and (wanted - before).length() > 0.001 \
				and moved.dot(wanted - before) < -0.001:
			ghosts += 1
		var blocked_ahead := PlaneCollider.capsule_blocks(solids, wanted, Vector2(0.0, 1.0),
			stats.body_half_length, stats.body_radius)
		if blocked_ahead:
			contact += 1
		elif input.length() > 0.1 and moved.length() < 0.001 and wanted.distance_to(before) > 0.001:
			frozen_free += 1
		path.append(after)
		if i % (frames / 4) == 0 or i == frames - 1:
			snapshots.append([t, _copy(solids), after])
	var verdict := penetrations == 0 and ghosts == 0 and frozen_free == 0
	print("%-18s %s | contact %3d/%d | entraine %3d | penetre %d | fantome %d | fige-libre %d | arrivee (%+.2f, %+.2f)"
		% [label, "OK  " if verdict else "DEFAUT", contact, frames, carried, penetrations,
			ghosts, frozen_free, player.plane_position.x, player.plane_position.y])
	_svg(label, path, snapshots)
	player.free()
	return 0 if verdict else 1

func _copy(shapes: PlaneShapes) -> Array:
	var out := []
	for i in shapes.size():
		var row := [shapes.kind_at(i), shapes.centre_of(i)]
		for slot in range(2, 6):
			row.append(shapes.param(i, slot))
		out.append(row)
	return out

## Trajectoire sur les murs, en quatre instants : c'est ce qu'on REGARDE.
func _svg(label: String, path: PackedVector2Array, snapshots: Array) -> void:
	var scale := 22.0
	var w := 28.0 * scale
	var h := 24.0 * scale
	var lines := PackedStringArray()
	lines.append('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" style="background:#0a0612">' % [int(w), int(h), int(w), int(h)])
	lines.append('<rect width="%d" height="%d" fill="#0a0612"/>' % [int(w), int(h)])
	var colours := ["#6a3d9a", "#8d5bc4", "#b07fe6", "#d9b3ff"]
	for k in snapshots.size():
		var snap: Array = snapshots[k]
		var col: String = colours[mini(k, colours.size() - 1)]
		for row in snap[1]:
			if row[0] == PlaneShapes.Kind.RING_ARC:
				lines.append(_arc(row[1], row[2], row[3], row[4], row[5], col, scale, w, h))
			elif row[0] == PlaneShapes.Kind.DISC:
				var c := _px(row[1], scale, w, h)
				lines.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="#ff5fa2" stroke-width="1.5"/>' % [c.x, c.y, row[2] * scale])
	var d := ""
	for i in path.size():
		var p := _px(path[i], scale, w, h)
		d += ("M" if i == 0 else "L") + "%.1f %.1f " % [p.x, p.y]
	lines.append('<path d="%s" fill="none" stroke="#5ef2ff" stroke-width="2"/>' % d)
	var a := _px(path[0], scale, w, h)
	var b := _px(path[path.size() - 1], scale, w, h)
	lines.append('<circle cx="%.1f" cy="%.1f" r="5" fill="#5ef2ff"/>' % [a.x, a.y])
	lines.append('<circle cx="%.1f" cy="%.1f" r="5" fill="#ffd166"/>' % [b.x, b.y])
	lines.append('<text x="10" y="20" fill="#eee" font-family="monospace" font-size="14">%s — cyan: depart, jaune: arrivee, murs: du sombre (t=0) au clair (t=fin)</text>' % label)
	lines.append('</svg>')
	var file := FileAccess.open("res://build/bench/dive-%s.svg" % label, FileAccess.WRITE)
	if file != null:
		file.store_string("\n".join(lines))
		file.close()

func _px(p: Vector2, scale: float, w: float, h: float) -> Vector2:
	return Vector2(w * 0.5 + p.x * scale, h * 0.5 - p.y * scale)

func _arc(c: Vector2, r: float, thickness: float, start_deg: float, span_deg: float,
		col: String, scale: float, w: float, h: float) -> String:
	var inner := (r - thickness * 0.5) * scale
	var outer := (r + thickness * 0.5) * scale
	var a0 := deg_to_rad(start_deg)
	var a1 := deg_to_rad(start_deg + span_deg)
	var cc := _px(c, scale, w, h)
	# y d'écran inversé : on nie le sinus.
	var p0 := cc + Vector2(cos(a0), -sin(a0)) * outer
	var p1 := cc + Vector2(cos(a1), -sin(a1)) * outer
	var p2 := cc + Vector2(cos(a1), -sin(a1)) * inner
	var p3 := cc + Vector2(cos(a0), -sin(a0)) * inner
	var large := 1 if span_deg > 180.0 else 0
	return '<path d="M%.1f %.1f A%.1f %.1f 0 %d 0 %.1f %.1f L%.1f %.1f A%.1f %.1f 0 %d 1 %.1f %.1f Z" fill="%s" fill-opacity="0.55"/>' \
		% [p0.x, p0.y, outer, outer, large, p1.x, p1.y, p2.x, p2.y, inner, inner, large, p3.x, p3.y, col]
