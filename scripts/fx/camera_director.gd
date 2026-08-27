class_name CameraDirector
extends Node3D
## Owns the gameplay Camera3D and applies centralized trauma-based screen shake
## (spec §16.3). Shake is an additive offset around a REST POSE, so gameplay dodging is
## never disturbed. Trauma accumulates (capped) and decays.
##
## La pose de repos était fixe ; elle est désormais **déplaçable** (`push_rest`), ce qui
## donne le plongeon dans le noyau du boss final (ADR-0021) sans toucher au shake : le
## tremblement reste additif par-dessus, où que la caméra soit posée. ⚠️ Un cadrage animé
## en écrivant directement `Camera3D.transform` serait écrasé par le shake à l'image
## suivante — c'est pour ça que le déplacement passe par la pose de repos, et pas par la
## caméra.

const SettingsManagerScript := preload("res://scripts/core/settings_manager.gd")

## Secousse rendue au joueur quand il déplace le curseur, pour qu'il JUGE son réglage
## au lieu de le deviner. Un curseur d'accessibilité qui ne produit rien pendant qu'on
## le bouge est exactement le signal muet que le projet a appris à traquer.
const PREVIEW_TRAUMA := 0.45

@export var max_translation: float = 0.35
@export var max_roll_deg: float = 2.2
@export var trauma_decay: float = 1.6
@export var noise_speed: float = 28.0
## Accessibility multiplier (spec §16.3): 0 disables shake entirely.
@export var shake_multiplier: float = 1.0

var _camera: Camera3D
## Pose d'origine, jamais perdue : `restore_rest()` y ramène toujours.
var _home_transform: Transform3D
## Pose de repos courante — celle autour de laquelle le shake s'applique.
var _rest_transform: Transform3D
## Cible et vitesse du glissement en cours (`_rest_move_time <= 0` : pas de glissement).
var _rest_target: Transform3D
var _rest_move_time: float = 0.0
var _rest_move_left: float = 0.0
var _rest_from: Transform3D
var _trauma: float = 0.0
var _noise: FastNoiseLite
var _noise_time: float = 0.0

func _ready() -> void:
	# Accessibilité (spec §7.3) : la secousse suit le réglage du joueur dans TOUTES les
	# scènes qui portent un director — l'accueil et le banc d'essai comme le combat.
	# C'est le nœud de scène qui s'abonne, jamais l'autoload : lui ne connaît aucun nœud
	# de rendu (settings_manager.gd). Absent en mode `--script`, d'où le `or_null`.
	var settings := get_node_or_null("/root/SettingsManager") as SettingsManagerScript
	if settings != null:
		settings.graphics_changed.connect(_on_graphics_changed)
		shake_multiplier = settings.get_graphics().shake
	_camera = get_node_or_null("Camera3D") as Camera3D
	if _camera == null:
		push_error("[CameraDirector] expects a child Camera3D")
		return
	_rest_transform = _camera.transform
	_home_transform = _rest_transform
	_rest_target = _rest_transform
	_rest_from = _rest_transform
	_noise = FastNoiseLite.new()
	_noise.noise_type = FastNoiseLite.TYPE_PERLIN
	_noise.frequency = 0.08

## Le réglage a bougé : on l'applique, et on le FAIT SENTIR.
##
## ⚠️ Pas d'aperçu en pause. Le tremblement s'anime dans `_process`, qui ne tourne pas
## tant que l'arbre est en pause : le trauma resterait en attente et se déchargerait
## d'un coup à la reprise, sur un joueur qui a repris les commandes.
func _on_graphics_changed(data: SettingsData) -> void:
	var changed := not is_equal_approx(shake_multiplier, data.shake)
	shake_multiplier = data.shake
	if changed and data.shake > 0.0 and not get_tree().paused:
		add_trauma(PREVIEW_TRAUMA)

## Add trauma in [0,1]; shake intensity scales with trauma squared.
func add_trauma(amount: float) -> void:
	_trauma = clampf(_trauma + amount, 0.0, 1.0)

## Glisse la pose de repos vers `target` en `duration` secondes. Le shake continue de
## s'appliquer par-dessus pendant le trajet.
func push_rest(target: Transform3D, duration: float) -> void:
	_rest_from = _rest_transform
	_rest_target = target
	_rest_move_time = maxf(duration, 0.0001)
	_rest_move_left = _rest_move_time

## Ramène la caméra à sa pose d'origine. ⚠️ Toujours passer par ici plutôt que de
## mémoriser la pose côté appelant : une séquence interrompue (mort du joueur, sortie de
## niveau) laisserait la caméra dans le noyau du boss, et rien ne le remettrait droit.
func restore_rest(duration: float) -> void:
	push_rest(_home_transform, duration)

## Pose d'origine de la caméra, pour composer un cadrage relatif.
func home_transform() -> Transform3D:
	return _home_transform

## Vrai tant qu'un glissement est en cours.
func is_moving() -> bool:
	return _rest_move_left > 0.0

func _process(delta: float) -> void:
	if _camera == null:
		return
	if _rest_move_left > 0.0:
		_rest_move_left = maxf(_rest_move_left - delta, 0.0)
		# Lissage en cosinus : un glissement linéaire donne deux à-coups, au départ et à
		# l'arrivée, et ils se lisent comme une saccade de moteur.
		var t := 1.0 - _rest_move_left / _rest_move_time
		var eased := 0.5 - 0.5 * cos(clampf(t, 0.0, 1.0) * PI)
		_rest_transform = _rest_from.interpolate_with(_rest_target, eased)
	if _trauma <= 0.0:
		_camera.transform = _rest_transform
		return
	_trauma = maxf(_trauma - trauma_decay * delta, 0.0)
	_noise_time += delta * noise_speed
	var shake := _trauma * _trauma * shake_multiplier
	var ox := _noise.get_noise_2d(_noise_time, 0.0)
	var oy := _noise.get_noise_2d(0.0, _noise_time)
	var oz := _noise.get_noise_2d(_noise_time, _noise_time)
	var offset := Vector3(ox, oy, 0.0) * max_translation * shake
	var roll := deg_to_rad(max_roll_deg) * oz * shake
	var shaken := _rest_transform
	shaken.origin += offset
	shaken.basis = _rest_transform.basis * Basis(Vector3(0.0, 0.0, 1.0), roll)
	_camera.transform = shaken
