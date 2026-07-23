class_name SettingsData
extends RefCounted
## Player settings, as pure data (spec §13, §19.2). Volumes are linear 0..1 — that is what
## a slider is — and only become decibels at the AudioServer boundary.
## No node, no file, no AudioServer: instantiable and testable by hand.

## Bus name -> linear volume. Keys match resources/audio/default_bus_layout.tres.
const BUSES: Array[StringName] = [&"Master", &"Music", &"SFX", &"Voice"]
const DEFAULTS: Dictionary = {
	&"Master": 0.8,
	&"Music": 0.7,
	&"SFX": 0.9,
	&"Voice": 1.0,
}

## Below this, the slider means "off" and we mute outright rather than fade to a
## barely-audible -60 dB.
const SILENCE_THRESHOLD := 0.001
const SILENCE_DB := -80.0

var volumes: Dictionary = DEFAULTS.duplicate()

## Grille de pixels du post-process rétro. Vraie par défaut : c'est l'identité visuelle
## du jeu, l'option est un confort, pas un réglage neutre.
##
## ⚠️ Ce drapeau ne coupe QUE l'accrochage sur la grille. La postérisation, le tramage
## et surtout le relèvement des tons moyens (`lift`) vivent dans le même shader, et
## c'est lui qui porte le correctif de luminosité d'ADR-0016 : éteindre le nœud entier
## replongerait l'image dans le sombre au lieu de la rendre nette.
var pixelation: bool = true

func get_linear(bus: StringName) -> float:
	return volumes.get(bus, DEFAULTS.get(bus, 1.0))

func set_linear(bus: StringName, value: float) -> void:
	if not DEFAULTS.has(bus):
		push_warning("[Settings] unknown bus: %s" % bus)
		return
	volumes[bus] = clampf(value, 0.0, 1.0)

func audio_to_dict() -> Dictionary:
	return volumes.duplicate()

## Tolerant on purpose: a settings file from an older build, or one a player has edited by
## hand, must not brick the game. Unknown keys are dropped, bad values clamped.
func audio_from_dict(source: Dictionary) -> void:
	volumes = DEFAULTS.duplicate()
	for bus in BUSES:
		var value: Variant = source.get(bus, source.get(String(bus)))
		if value is float or value is int:
			volumes[bus] = clampf(float(value), 0.0, 1.0)

func graphics_to_dict() -> Dictionary:
	return {&"pixelation": pixelation}

## Même tolérance que pour l'audio : un fichier écrit par une version qui ne connaissait
## pas cette section laisse le défaut en place, et une valeur d'un autre type ne casse
## rien. Un joueur ne doit jamais avoir à supprimer son `settings.cfg`.
func graphics_from_dict(source: Dictionary) -> void:
	pixelation = true
	var value: Variant = source.get(&"pixelation", source.get("pixelation"))
	if value is bool:
		pixelation = value
	elif value is int or value is float:
		# ConfigFile relit parfois un booléen sauvegardé comme entier.
		pixelation = float(value) != 0.0

## A slider is linear in loudness-ish terms; the mixer wants decibels.
static func to_db(linear: float) -> float:
	if linear <= SILENCE_THRESHOLD:
		return SILENCE_DB
	return linear_to_db(clampf(linear, 0.0, 1.0))
