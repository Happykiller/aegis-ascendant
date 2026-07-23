class_name EnginePlume
extends MeshInstance3D
## Plume d'échappement d'un réacteur — le cône de gaz et ses disques de Mach (ADR-0017).
##
## Remplace la traînée de particules (`EngineTrail`) dans son rôle de MOTEUR. La traînée
## survit à côté, réduite, dans son seul rôle honnête : les braises laissées dans le
## monde par un vaisseau qui se déplace.
##
## Sur le patron de `Beam` : le nœud et la math pure vivent dans le même fichier, la
## seconde étant statique pour être vérifiable sans rendu ni arbre.
##
## ⚠️ ZÉRO ALLOCATION PAR IMAGE — `_process` ne manipule que des flottants et des Color
## (types valeur), et ne pousse les uniformes que lorsque la poussée a bougé. Une plume
## stabilisée (escorte, ennemi, bestiaire) débranche même son `_process`.

const PlumeShader := preload("res://shaders/engine_plume.gdshader")

## Noms d'uniformes en `StringName` : poussés à chaque image, la conversion
## String -> StringName se referait sinon indéfiniment (leçon `beam.gd:64-65`).
const U_LENGTH := &"plume_length"
const U_THROAT := &"throat_radius"
const U_FLARE := &"tail_flare"
const U_SHOCK_COUNT := &"shock_count"
const U_SHOCK_DEPTH := &"shock_depth"
const U_CORE := &"core_color"
const U_PLUME := &"plume_color"
const U_TAIL := &"tail_color"
const U_ENERGY := &"energy"
const U_FLICKER := &"flicker"

## Maillages partagés. Le shader calcule TOUT le profil : deux plumes de même
## subdivision ont donc exactement la même géométrie source, quels que soient leur
## taille, leur camp et leur régime. Une vague entière partage un seul CylinderMesh.
static var _meshes: Dictionary[int, CylinderMesh] = {}

## Drapeau de bissection perf `--no-plumes`, sur le modèle de `--no-backdrop` et
## `--no-glow` (`title_stage.gd:87`). Sans lui, le coût des plumes n'est pas isolable
## et « ça rame » reste une opinion (`.claude/resources/howto-mesurer-la-perf.md`).
## Lu UNE fois : `OS.get_cmdline_user_args()` alloue un PackedStringArray à chaque appel.
static var _disabled: int = -1

static func _is_disabled() -> bool:
	if _disabled < 0:
		_disabled = 1 if "--no-plumes" in OS.get_cmdline_user_args() else 0
	return _disabled == 1

var _tuning: PlumeTuning
var _material: ShaderMaterial
var _scale: float = 1.0
var _target: float = 0.0
var _throttle: float = -1.0
## Dernière valeur effectivement poussée au shader : sous ce seuil de variation, on ne
## retouche rien (une plume à régime constant ne coûte plus que son rendu).
var _pushed: float = -1.0
const PUSH_EPSILON := 0.002

## `scale_factor` met la plume à l'échelle de la coque, comme `EngineTrail.make()` :
## le jet d'un Needle Scout de 1,9 m et celui d'un Leviathan ne peuvent pas mesurer
## pareil. Il ne passe PAS par `scale` du nœud — la mise à l'échelle d'un nœud
## multiplierait aussi la marge de culling et les uniformes déjà dimensionnés.
##
## `aft` : le sens de l'échappement, dans l'espace du parent. `Vector3.BACK` (+Z) pour
## une coque modelée nez vers -Z (le Specter-9, cf. `EngineTrail`) ; `Vector3.FORWARD`
## pour une coque lacée nez vers le bas de l'écran (les ennemis qui plongent).
static func make(tuning: PlumeTuning, scale_factor: float = 1.0,
		aft: Vector3 = Vector3.BACK) -> EnginePlume:
	var plume := EnginePlume.new()
	plume.name = "EnginePlume"
	plume._tuning = tuning
	plume._scale = scale_factor
	plume.mesh = _shared_mesh(tuning.rings, tuning.radial_segments)
	plume._material = ShaderMaterial.new()
	plume._material.shader = PlumeShader
	plume.material_override = plume._material
	plume.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# Le shader allonge la géométrie DANS le vertex : la boîte englobante reste celle du
	# cylindre unitaire et Godot culle la plume dès qu'elle sort du nez de la coque.
	# Même morsure que sur le faisceau (`beam.gd:37-40`) et sur les coques de boss.
	plume.extra_cull_margin = tuning.length_full * scale_factor + 1.0
	# La plume pousse vers +Y local ; une rotation de +90° autour de X envoie +Y sur +Z.
	plume.rotation.x = PI * 0.5 if aft.z >= 0.0 else -PI * 0.5
	plume.visible = not _is_disabled()
	plume.snap_throttle(tuning.idle_throttle)
	return plume

static func _shared_mesh(rings: int, radial_segments: int) -> CylinderMesh:
	var key := rings * 1000 + radial_segments
	var cached: CylinderMesh = _meshes.get(key)
	if cached != null:
		return cached
	var cylinder := CylinderMesh.new()
	# UNITAIRE, à dessein : le shader fait tout le profil (rayon, évasement, chocs,
	# longueur). Un maillage déjà conique multiplierait deux fois le même évasement.
	cylinder.top_radius = 1.0
	cylinder.bottom_radius = 1.0
	cylinder.height = 1.0
	cylinder.cap_top = false
	cylinder.cap_bottom = false
	cylinder.rings = rings
	cylinder.radial_segments = radial_segments
	_meshes[key] = cylinder
	return cylinder

## Poussée visée, de 0 (dérive) à 1 (plein régime). La plume s'y rend à sa propre
## vitesse — vive à la montée, lente à l'extinction.
func set_throttle(ratio: float) -> void:
	_target = clampf(ratio, 0.0, 1.0)
	if not is_equal_approx(_target, _throttle):
		set_process(true)

## Poussée imposée sans transition : à la construction, et au réveil d'un ennemi tiré
## du pool — un vaisseau qui rentre en scène ne doit pas allumer son moteur à l'écran.
func snap_throttle(ratio: float) -> void:
	_target = clampf(ratio, 0.0, 1.0)
	_throttle = _target
	_push()
	set_process(false)

func _process(delta: float) -> void:
	_throttle = advance(_throttle, _target, delta, _tuning.attack_rate, _tuning.decay_rate)
	# ⚠️ Le lissage exponentiel n'ATTEINT jamais sa cible : sans ce plancher d'arrêt, la
	# plume d'une escorte à régime constant recalculerait son approche indéfiniment.
	var settled := absf(_throttle - _target) < 0.001
	if settled:
		_throttle = _target
	if settled or absf(_throttle - _pushed) > PUSH_EPSILON:
		_push()
	if settled:
		# Régime atteint : plus rien à calculer tant que personne ne redemande.
		set_process(false)

func _push() -> void:
	var t := _throttle
	_pushed = t
	_material.set_shader_parameter(U_LENGTH,
		lerpf(_tuning.length_idle, _tuning.length_full, t) * _scale)
	_material.set_shader_parameter(U_THROAT,
		_tuning.throat_radius * lerpf(_tuning.throat_idle, 1.0, t) * _scale)
	_material.set_shader_parameter(U_FLARE, _tuning.tail_flare)
	_material.set_shader_parameter(U_SHOCK_COUNT, _tuning.shock_count)
	_material.set_shader_parameter(U_SHOCK_DEPTH, shock_depth_at(t, _tuning))
	# Le cœur ne devient blanc qu'en montant en régime : au ralenti, le col est de la
	# couleur du camp. C'est la moitié « couleur » du signal d'accélération.
	_material.set_shader_parameter(U_CORE, _tuning.plume_color.lerp(_tuning.core_color, t))
	_material.set_shader_parameter(U_PLUME, _tuning.plume_color)
	_material.set_shader_parameter(U_TAIL, _tuning.tail_color)
	_material.set_shader_parameter(U_ENERGY,
		_tuning.energy * lerpf(_tuning.energy_idle, 1.0, t))
	_material.set_shader_parameter(U_FLICKER, _tuning.flicker)

# --- Math pure, vérifiable sans rendu ------------------------------------------

## Poussée demandée par le pilote, de 0 à 1.
##
## `input` est la commande dans le repère du PLAN de jeu (`GameplayPlane.from_input` :
## +y = vers le haut de l'écran), `speed_ratio` la vitesse acquise rapportée au maximum.
##
## ⚠️ LES DEUX TERMES SONT NÉCESSAIRES. Sur la seule commande, la plume s'effondre à
## l'instant où le joueur lâche la touche alors que le vaisseau file encore. Sur la
## seule vitesse, elle ne dit rien de l'intention : elle ne bouge qu'APRÈS que le
## vaisseau a accéléré, donc trop tard pour que le geste et l'image coïncident.
static func throttle_from(input: Vector2, speed_ratio: float, tuning: PlumeTuning) -> float:
	var forward := maxf(input.y, 0.0)
	var brake := maxf(-input.y, 0.0)
	var ratio := tuning.idle_throttle \
		+ tuning.forward_gain * forward \
		+ tuning.lateral_gain * absf(input.x) \
		+ tuning.speed_gain * clampf(speed_ratio, 0.0, 1.0) \
		- tuning.brake_drop * brake
	return clampf(ratio, 0.0, 1.0)

## Un pas de lissage ASYMÉTRIQUE : on monte vite, on retombe lentement.
##
## ⚠️ `minf(1.0, ...)` obligatoire : sans lui, une image très longue (chargement,
## alt-tab) donnerait un facteur supérieur à 1 et la poussée DÉPASSERAIT sa cible —
## plume qui pompe au retour du focus. Même piège, même parade que `ship_flight.gd:89`.
static func advance(current: float, target: float, delta: float,
		attack_rate: float, decay_rate: float) -> float:
	var rate := attack_rate if target > current else decay_rate
	return lerpf(current, target, minf(1.0, delta * rate))

## Amplitude des disques de Mach à cette poussée : NULLE en dessous du seuil, puis
## ouverte progressivement. Les disques sont la preuve visible que le moteur est ouvert
## en grand — les montrer en permanence les priverait de tout sens.
static func shock_depth_at(throttle: float, tuning: PlumeTuning) -> float:
	return tuning.shock_depth * smoothstep(tuning.shock_threshold, 1.0, throttle)
