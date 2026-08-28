class_name BulletManager
extends Node3D
## Data-oriented projectile system (spec §21).
## All buffers are preallocated in _init(); nothing allocates during gameplay.
## Logic lives in step(delta) — separate from _physics_process so headless
## tests can drive it directly (no MultiMesh needed: rendering is skipped when
## the node is not inside a scene with its MultiMeshInstance3D children).

enum Team { PLAYER = 0, ENEMY = 1 }

## A bullet connected. `victim_team` is the team that was *hit*, so a listener can
## colour the impact by side. The hit callback only carries damage, which is all
## the victim needs — but nothing else knew where the hit landed, so there was no
## way to draw it.
signal target_hit(plane_position: Vector2, victim_team: int)

## Un projectile s'est arrêté sur un ÉCRAN — une forme du décor, pas une cible. `team` est
## celle du projectile arrêté, pour que l'appelant colore la gerbe du bon côté.
##
## ⚠️ IL REMPLACE UNE FAUSSE CIBLE. Les balles n'étaient testées contre AUCUNE géométrie :
## le blindage du Léviathan était simulé par une `BulletTarget` unique de rayon 0,95, posée
## sur la ligne joueur→noyau. Elle attrapait donc un disque de mur, et un seul — « on voit un
## cercle sur le mur qui bloque bien les tirs mais en dehors les tirs passent » (opérateur,
## 2026-08-28, overlay `--show-solids` à l'appui). Pire, elle ratait par construction les
## flux latéraux des canons d'aile, qui ne croisent jamais cette ligne.
signal bullet_screened(plane_position: Vector2, team: int)

const MAX_BULLETS := 600                       # spec §21.3 hard budget
const TEAM_BUDGETS: PackedInt32Array = [150, 450]  # player / enemy sub-budgets
## Marge au-delà de `BOUNDS` avant qu'un projectile soit recyclé.
##
## ⚠️ ELLE VALAIT 2,0, ET LES TIRS MOURAIENT DANS LE CADRE. `BOUNDS` est le terrain de JEU,
## pas le champ VISIBLE : le fond en montre bien davantage (les ennemis naissent à y = 9,5 et
## on les voit arriver). Une coupe à y = 10 escamotait donc les bolts du joueur à environ
## 170 px du haut de l'écran — mesuré à la capture le 2026-08-27. « Mes tirs ne vont pas
## jusqu'au bout de l'écran, cela fait étrange » : ils ne s'arrêtaient pas, ils
## DISPARAISSAIENT, ce qui est pire.
##
## ⚠️ Ce n'est PAS une histoire de portée : le `ttl` du tir joueur autorise 36 unités de
## trajet quand le terrain en fait 16. Rallonger le `ttl` n'aurait rien changé.
const CULL_MARGIN := 5.0

## Pas d'échantillonnage du segment parcouru dans l'image, quand on le confronte aux écrans.
##
## ⚠️ C'EST UNE AFFAIRE DE TUNNELING, PAS DE PRÉCISION. Un bolt joueur avance de 0,40 u par
## image (24 u/s à 60 Hz) et le mur du réacteur n'est épais que de 0,50 : tester la seule
## position d'arrivée suffirait aujourd'hui, et cesserait de suffire au premier tir rapide
## ou au premier mur fin. On échantillonne donc le trajet, à un pas plus court que le plus
## mince des murs.
const SCREEN_SAMPLE_PITCH := 0.2
## Borne haute du nombre de pas : un projectile aberrant ne doit pas coûter une boucle
## illimitée dans le chemin critique.
const SCREEN_MAX_STEPS := 8

## Fixed-capacity flat spatial grid over BOUNDS.grow(CULL_MARGIN).
const GRID_COLS := 12
const GRID_ROWS := 8
const CELL_CAP := 32

var _positions: PackedVector2Array
var _velocities: PackedVector2Array
var _radii: PackedFloat32Array
var _damages: PackedFloat32Array
var _ttls: PackedFloat32Array
var _teams: PackedInt32Array
var _alive: PackedByteArray
## Le projectile a-t-il ete DANS le plan au moins une fois ? Tant que non, en sortir ne le
## tue pas — voir la garde de `step()`.
var _entered: PackedByteArray
var _free_stack: PackedInt32Array
var _free_top: int = 0
var _team_counts: PackedInt32Array
var _visible_counts: PackedInt32Array
var _grid_counts: PackedInt32Array
var _grid_data: PackedInt32Array
var _grid_overflows: int = 0
## Point de contact du dernier écran touché. Membre, et non valeur de retour composite :
## la boucle de `step()` est un chemin critique et ne doit rien allouer (spec §31).
var _screen_contact: Vector2 = Vector2.ZERO
## L'enveloppe des écrans, mesurée UNE fois par image : centre, rayon englobant, et le rayon
## du TROU au milieu (voir [method _measure_screens]).
var _screen_centre: Vector2 = Vector2.ZERO
var _screen_outer: float = 0.0
var _screen_inner: float = 0.0
var _grid_origin: Vector2
var _cell_size: Vector2
## Les formes qui ARRÊTENT un projectile — versées par le niveau, à l'image, et nulles le
## reste du temps. Distinctes des corps solides qui arrêtent un VAISSEAU : un noyau peut
## être infranchissable sans faire écran au tir qui le vise (c'est même exactement le piège
## dans lequel ce boss est tombé une fois).
##
## Aucune allocation : le niveau passe la même instance d'image en image.
var screens: PlaneShapes = null
var _targets: Array[BulletTarget] = []
## Set while walking _targets, so a hit callback that unregisters its own target
## defers the erase instead of mutating the array under the loop.
var _resolving: bool = false
var _pending_unregister: Array[BulletTarget] = []
var _multimeshes: Array[MultiMesh] = []
var _buffers: Array[PackedFloat32Array] = []

func _init() -> void:
	_positions.resize(MAX_BULLETS)
	_velocities.resize(MAX_BULLETS)
	_radii.resize(MAX_BULLETS)
	_damages.resize(MAX_BULLETS)
	_ttls.resize(MAX_BULLETS)
	_teams.resize(MAX_BULLETS)
	_alive.resize(MAX_BULLETS)
	_entered.resize(MAX_BULLETS)
	_free_stack.resize(MAX_BULLETS)
	for i in MAX_BULLETS:
		_free_stack[i] = MAX_BULLETS - 1 - i   # pop order: 0, 1, 2, ...
	_free_top = MAX_BULLETS
	_team_counts.resize(2)
	_visible_counts.resize(2)
	_grid_counts.resize(GRID_COLS * GRID_ROWS)
	_grid_data.resize(GRID_COLS * GRID_ROWS * CELL_CAP)
	# ⚠️ `MAX_BOUNDS` ET NON LES BORNES COURANTES : la grille est allouée UNE fois, et le plan
	# de vol s'élargit dans la chambre du réacteur. Dimensionnée sur le plan ordinaire, elle
	# aurait laissé les balles de la chambre retomber dans des cellules voisines — une
	# collision manquée par-ci par-là, sans la moindre erreur pour le dire.
	var grid_bounds := GameplayPlane.MAX_BOUNDS.grow(CULL_MARGIN)
	_grid_origin = grid_bounds.position
	_cell_size = grid_bounds.size / Vector2(GRID_COLS, GRID_ROWS)

## ⚠️ L'EN-TETE PROMETTAIT DEJA CE QUE LE CODE NE FAISAIT PAS. « Rendering is skipped when
## the node is not inside a scene with its MultiMeshInstance3D children » : `get_node()`
## rendait `null` et la ligne suivante levait une erreur de script — quatre par passage de
## la suite de tests, depuis toujours. `step()` sait deja se passer des MultiMesh
## (`var render := not _multimeshes.is_empty()`) ; il ne manquait que de ne pas mourir
## avant. On nomme l'enfant absent plutot que de se taire : une VRAIE scene a qui il
## manquerait un noeud doit se voir, sans pour autant rougir un test qui monte le
## gestionnaire a la main.
func _ready() -> void:
	for child_name: String in ["PlayerBullets", "EnemyBullets"]:
		var instance := get_node_or_null(child_name) as MultiMeshInstance3D
		if instance == null or instance.multimesh == null:
			push_warning("[BulletManager] sans '%s' : rendu des projectiles desactive" % child_name)
			_multimeshes.clear()
			_buffers.clear()
			return
		var multimesh := instance.multimesh
		multimesh.instance_count = MAX_BULLETS   # once only: reallocates GPU buffers
		multimesh.visible_instance_count = 0
		_multimeshes.append(multimesh)
		# Bulk transform buffer (12 floats/instance): far cheaper than one
		# set_instance_transform() call per bullet each frame. Pre-fill the
		# identity basis once; per frame only the origin (x,z) is rewritten.
		var buffer := PackedFloat32Array()
		buffer.resize(MAX_BULLETS * 12)
		for s in MAX_BULLETS:
			var base := s * 12
			buffer[base] = 1.0       # basis x.x
			buffer[base + 5] = 1.0   # basis y.y
			buffer[base + 10] = 1.0  # basis z.z
		_buffers.append(buffer)

func _physics_process(delta: float) -> void:
	step(delta)

## Spawns a bullet; returns its index, or -1 when the pool or team budget is full.
func spawn_bullet(team: int, pos: Vector2, vel: Vector2, radius: float,
		damage: float, ttl: float) -> int:
	if _free_top == 0 or _team_counts[team] >= TEAM_BUDGETS[team]:
		return -1
	_free_top -= 1
	var i := _free_stack[_free_top]
	_positions[i] = pos
	_velocities[i] = vel
	_radii[i] = radius
	_damages[i] = damage
	_ttls[i] = ttl
	_teams[i] = team
	_alive[i] = 1
	# ⚠️ UNE BOUCHE PEUT ETRE HORS DU PLAN, ET LA MOITIE DE LA GERBE MOURAIT LA. Le Leviathan
	# tire depuis ses plaques, `origin + 2,6` : jusqu'a y = 14,5 quand la coupe est a 13,0.
	# Le premier pas de ces balles les trouvait « dehors » et les recyclait a l'image de leur
	# creation — sans erreur, sans trace, et avec un compteur de projectiles parfaitement
	# juste. On ne retire pas ce qui n'est jamais entre ; le `ttl` borne l'attente, donc
	# aucune balle ne peut courir indefiniment vers le vide.
	_entered[i] = 1 if GameplayPlane.is_inside(pos, CULL_MARGIN) else 0
	_team_counts[team] += 1
	return i

func spawn_from_data(team: int, pos: Vector2, direction: Vector2, data: ProjectileData) -> int:
	return spawn_bullet(team, pos, direction.normalized() * data.speed,
		data.radius, data.damage, data.ttl)

func despawn(index: int) -> void:
	if _alive[index] == 1:
		_release(index)

## Les cibles, en LECTURE — pour l'overlay de debug (`SolidsOverlay`) et rien d'autre.
## Ce qu'une balle touche n'est pas ce qui arrête un corps : les deux couches se voient
## désormais côte à côte, et un désaccord entre elles se lit à l'écran au lieu de se
## chercher pendant une soirée (le noyau qui se faisait écran à sa propre cible).
func targets() -> Array[BulletTarget]:
	return _targets

func register_target(target: BulletTarget) -> void:
	if not _targets.has(target):
		_targets.append(target)

## Safe to call from a hit callback: the erase is deferred to the end of the pass
## rather than mutating the array mid-iteration. Bosses unregister exactly this
## way, from inside their own hit handler.
func unregister_target(target: BulletTarget) -> void:
	if _resolving:
		if not _pending_unregister.has(target):
			_pending_unregister.append(target)
		return
	_targets.erase(target)

func active_count() -> int:
	return MAX_BULLETS - _free_top

func team_count(team: int) -> int:
	return _team_counts[team]

## Advances every bullet, rebuilds the spatial grid, feeds the MultiMeshes
## (compacted 0..n-1) and resolves circle-circle hits on the logical plane.
func step(delta: float) -> void:
	_grid_counts.fill(0)
	_visible_counts[Team.PLAYER] = 0
	_visible_counts[Team.ENEMY] = 0
	var render := not _multimeshes.is_empty()
	var screening := screens != null and screens.size() > 0
	if screening:
		_measure_screens()
	for i in MAX_BULLETS:
		if _alive[i] == 0:
			continue
		_ttls[i] -= delta
		var p := _positions[i] + _velocities[i] * delta
		if _ttls[i] <= 0.0:
			_release(i)
			continue
		if GameplayPlane.is_inside(p, CULL_MARGIN):
			_entered[i] = 1
		elif _entered[i] == 1:
			_release(i)
			continue
		if screening and _near_screens(p, _positions[i].distance_to(p), _radii[i]) \
				and _crosses_screen(_positions[i], p, _radii[i]):
			# ⚠️ LA POSITION D'ARRÊT EST CELLE DU CONTACT, pas celle d'arrivée : la gerbe se
			# dessine sur la face du mur, là où le joueur a vu son tir mourir.
			bullet_screened.emit(_screen_contact, _teams[i])
			_release(i)
			continue
		_positions[i] = p
		_grid_insert(i, p)
		var team := _teams[i]
		if render:
			# Write only the origin (world x,z) into this team's transform buffer;
			# the identity basis floats were set once in _ready.
			var base := _visible_counts[team] * 12
			_buffers[team][base + 3] = p.x    # origin.x
			_buffers[team][base + 11] = -p.y  # origin.z (world -Z = screen up)
		_visible_counts[team] += 1
	if render:
		for team in 2:
			_multimeshes[team].buffer = _buffers[team]
			_multimeshes[team].visible_instance_count = _visible_counts[team]
	_resolve_hits()

## Efface d'un coup toutes les balles d'une équipe, et rend combien sont tombées.
##
## ⚠️ C'EST UN GARDE-FOU CONTRE LA MORT EN CHAÎNE, pas une commodité. Le joueur qui meurt
## réapparaît 1,2 s plus tard **au centre bas**, avec 2 s d'invulnérabilité — mais tout ce
## qui volait à l'instant de sa mort vole toujours. Il renaît donc parfois au milieu d'un
## rideau, et son invulnérabilité expire là où il ne peut rien faire. Le genre traite ce
## cas depuis toujours : on annule les balles, PUIS on donne l'invulnérabilité.
##
## Pas de boucle critique ici : c'est un événement rare, on peut parcourir le budget entier.
func clear_team(team: int) -> int:
	var cleared := 0
	for i in MAX_BULLETS:
		if _alive[i] == 1 and _teams[i] == team:
			_release(i)
			cleared += 1
	return cleared

## Rend un projectile au pool. **IDEMPOTENT**, et ce n'est pas une précaution décorative.
##
## ⚠️ LA LIBÉRATION EST RÉENTRANTE PAR CONSTRUCTION, et le chemin est entièrement synchrone :
##   1. `_resolve_hits` trouve qu'un tir ennemi atteint le joueur ;
##   2. `target.hit_callback.call(...)` — le joueur encaisse et MEURT ;
##   3. sa mort appelle `clear_team(ENEMY)`, le garde-fou contre la mort en chaîne
##      (`graybox_root._on_player_destroyed`) — voulu, documenté, et non négociable ;
##   4. `clear_team` libère tous les tirs ennemis vivants, DONT celui qu'on traite ;
##   5. retour dans `_resolve_hits`, qui libère une seconde fois le même index.
##
## Sans cette garde, le même index part deux fois sur la pile libre. Vécu en jeu le
## 2026-08-26 : « Out of bounds set index '600' ». ⚠️ **Et le dégât visible n'était pas le
## pire.** L'écriture hors bornes interrompt la fonction AVANT `_free_top += 1`, donc la
## pile est sauvée par accident — mais `_team_counts` a déjà été décrémenté à la ligne
## d'avant. Le compte part à **−1**, et le budget par équipe cesse alors de borner quoi que
## ce soit, sans une ligne au journal, longtemps après que l'erreur a défilé.
##
## Rendre `_release` idempotent supprime la catégorie entière plutôt que ce cas-ci : tout
## futur rappel qui vide l'écran depuis un `hit_callback` est couvert d'avance.
func _release(i: int) -> void:
	if _alive[i] == 0:
		return
	_alive[i] = 0
	_team_counts[_teams[i]] -= 1
	_free_stack[_free_top] = i
	_free_top += 1

func _grid_insert(bullet_index: int, p: Vector2) -> void:
	var cell := _cell_of(p)
	var count := _grid_counts[cell]
	if count >= CELL_CAP:
		# Never crash on overflow: the bullet keeps flying but skips hit tests
		# this frame; throttled warning for tuning (spec §21.2).
		_grid_overflows += 1
		if _grid_overflows % 300 == 1:
			push_warning("[BulletManager] grid cell overflow (total: %d)" % _grid_overflows)
		return
	_grid_data[cell * CELL_CAP + count] = bullet_index
	_grid_counts[cell] = count + 1

## L'enveloppe des écrans pour cette image : un disque englobant, et le rayon du trou au
## milieu quand tous les écrans sont des anneaux autour d'un même centre — ce qui est le cas
## du seul décor qui en pose, la chambre du réacteur.
##
## ⚠️ ELLE EXISTE PARCE QUE LE TEST FIN COÛTAIT 1,55 ms PAR IMAGE, mesuré au banc sur le
## budget plein de 150 bolts : dix fois le coût de la boucle de projectiles elle-même, et
## 9 % du budget 60 Hz — dépensés pour des balles qui, pour la plupart, volent loin des murs
## ou dans le puits central où il n'y a rien à toucher. Deux comparaisons de distance les
## écartent. La mesure est CONSERVATRICE : elle ne peut qu'écarter des balles qui n'auraient
## rien touché, jamais en rater une.
func _measure_screens() -> void:
	_screen_centre = screens.centre_of(0)
	_screen_outer = 0.0
	# Un trou n'existe que si TOUT est un anneau autour du même centre. Au moindre écran
	# d'une autre nature, on renonce au raccourci plutôt que de risquer un tir qui traverse.
	var hole := INF
	for i in screens.size():
		var c := screens.centre_of(i)
		var reach := 0.0
		match screens.kind_at(i):
			PlaneShapes.Kind.DISC:
				reach = screens.param(i, 2)
				hole = 0.0
			PlaneShapes.Kind.RING_ARC:
				var r := screens.param(i, 2)
				var half := screens.param(i, 3) * 0.5
				reach = r + half
				if c.is_equal_approx(_screen_centre):
					hole = minf(hole, r - half)
				else:
					hole = 0.0
			PlaneShapes.Kind.CAPSULE:
				var b := Vector2(screens.param(i, 2), screens.param(i, 3))
				c = (c + b) * 0.5
				reach = c.distance_to(b) + screens.param(i, 4)
				hole = 0.0
		_screen_outer = maxf(_screen_outer, _screen_centre.distance_to(c) + reach)
	_screen_inner = 0.0 if is_inf(hole) else maxf(hole, 0.0)

## Ce projectile peut-il seulement approcher un écran cette image ? `travel` est la longueur
## du pas, et la marge la couvre : juger sur le point d'arrivée suffit alors pour tout le
## segment.
func _near_screens(p: Vector2, travel: float, radius: float) -> bool:
	var margin := travel + radius
	var distance := p.distance_to(_screen_centre)
	if distance > _screen_outer + margin:
		return false
	return distance >= _screen_inner - margin

## Le trajet `from` -> `to` traverse-t-il un écran ? Écrit le point de contact dans
## `_screen_contact`. Le pas d'échantillonnage se déduit de la distance parcourue, donc un
## projectile lent ne paie pas le prix d'un rapide.
func _crosses_screen(from: Vector2, to: Vector2, radius: float) -> bool:
	var travel := from.distance_to(to)
	var steps := clampi(int(ceil(travel / SCREEN_SAMPLE_PITCH)), 1, SCREEN_MAX_STEPS)
	# On part de 1 : `from` a déjà été jugé libre à l'image précédente.
	for s in range(1, steps + 1):
		var point := from.lerp(to, float(s) / float(steps))
		if PlaneCollider.blocks(screens, point, radius):
			_screen_contact = point
			return true
	return false

func _cell_of(p: Vector2) -> int:
	var col := clampi(int((p.x - _grid_origin.x) / _cell_size.x), 0, GRID_COLS - 1)
	var row := clampi(int((p.y - _grid_origin.y) / _cell_size.y), 0, GRID_ROWS - 1)
	return row * GRID_COLS + col

func _resolve_hits() -> void:
	_resolving = true
	for target in _targets:
		if target.enabled:
			_resolve_target(target)
	_resolving = false
	# Unregistrations requested by a hit callback were held back so the loop above
	# never mutated the array it was walking.
	if not _pending_unregister.is_empty():
		for target in _pending_unregister:
			_targets.erase(target)
		_pending_unregister.clear()

## Scan the 3x3 cells around one target.
##
## A hit callback can kill its owner, and a dead entity disables its target. We
## stop the moment that happens: otherwise the rest of the salvo already sitting
## in these cells keeps landing on a corpse, and an entity that reports its death
## from the hit path (the bosses do) reports it once per bullet — which paid the
## boss reward twice and started the docking sequence twice.
func _resolve_target(target: BulletTarget) -> void:
	var col := clampi(int((target.position.x - _grid_origin.x) / _cell_size.x), 0, GRID_COLS - 1)
	var row := clampi(int((target.position.y - _grid_origin.y) / _cell_size.y), 0, GRID_ROWS - 1)
	for dc in 3:
		var c := col + dc - 1
		if c < 0 or c >= GRID_COLS:
			continue
		for dr in 3:
			var r := row + dr - 1
			if r < 0 or r >= GRID_ROWS:
				continue
			var cell := r * GRID_COLS + c
			var count := _grid_counts[cell]
			for k in count:
				var i := _grid_data[cell * CELL_CAP + k]
				if _alive[i] == 0 or _teams[i] == target.team:
					continue
				var reach := _radii[i] + target.radius
				if _positions[i].distance_squared_to(target.position) <= reach * reach:
					target.hit_callback.call(_damages[i])
					target_hit.emit(_positions[i], target.team)
					_release(i)
					if not target.enabled:
						return
