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

## Multiplicateur de secousse d'écran, dans [0, 1]. **0 éteint la secousse**
## (spec §7.3 : « secousse réduite ou désactivable » ; §16.3).
##
## Plein par défaut : la secousse fait partie de la sensation du jeu, l'option est un
## confort d'accessibilité — pas un réglage neutre qu'on activerait après coup.
##
## ⚠️ Zéro est une valeur VOULUE, pas une absence. Toute relecture doit distinguer
## « le joueur a mis 0 » de « la clé manque » — sans quoi couper la secousse ne tient
## pas d'une session à l'autre.
var shake: float = 1.0

# --- Débogage : les couches invisibles du jeu, rendues visibles ---------------
#
# ⚠️ ELLES EXISTENT PARCE QU'UNE SOIRÉE ENTIÈRE A ÉTÉ PERDUE À NE PAS LES VOIR. Le décor de
# la chambre du réacteur tournait à l'envers de sa collision, et quatre diagnostics chiffrés
# se sont succédé avant qu'on dessine simplement les formes par-dessus l'image. « C'est un
# outil extrêmement précieux. Dès qu'on est en développement, on doit toujours les afficher »
# (opérateur, 2026-08-28). D'où le défaut : ALLUMÉES en build de développement, ÉTEINTES en
# release — et réglables dans le menu des options dans les deux cas.
#
# Quatre représentations pour une même chose, et seule la première est le jeu :
#   - ce qu'on VOIT (l'image) — toujours affiché ;
#   - les CORPS (`bodies`) : ce qui arrête un vaisseau — vert ;
#   - les CIBLES (`targets`) : ce qu'une balle touche et blesse — orange / magenta ;
#   - les ÉCRANS (`screens`) : ce qui bloque une balle sans la prendre — rouge.

## Noms des couches, tels que le menu et le gestionnaire les désignent.
const DEBUG_LAYERS: Array[StringName] = [&"bodies", &"targets", &"screens"]

var debug_bodies: bool = OS.is_debug_build()
var debug_targets: bool = OS.is_debug_build()
var debug_screens: bool = OS.is_debug_build()

func get_debug_layer(layer: StringName) -> bool:
	match layer:
		&"bodies": return debug_bodies
		&"targets": return debug_targets
		&"screens": return debug_screens
	push_warning("[Settings] unknown debug layer: %s" % layer)
	return false

func set_debug_layer(layer: StringName, enabled: bool) -> void:
	match layer:
		&"bodies": debug_bodies = enabled
		&"targets": debug_targets = enabled
		&"screens": debug_screens = enabled
		_: push_warning("[Settings] unknown debug layer: %s" % layer)

func debug_to_dict() -> Dictionary:
	return {&"bodies": debug_bodies, &"targets": debug_targets, &"screens": debug_screens}

## Même tolérance que les autres sections : une clé absente laisse le défaut DU BUILD (allumé
## en développement, éteint en release), et un entier vaut un booléen.
func debug_from_dict(source: Dictionary) -> void:
	for layer in DEBUG_LAYERS:
		var fallback := OS.is_debug_build()
		var value: Variant = source.get(layer, source.get(String(layer)))
		if value is bool:
			set_debug_layer(layer, value)
		elif value is int or value is float:
			set_debug_layer(layer, float(value) != 0.0)
		else:
			set_debug_layer(layer, fallback)

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
	return {&"pixelation": pixelation, &"shake": shake}

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
	shake = 1.0
	var shake_value: Variant = source.get(&"shake", source.get("shake"))
	if shake_value is float or shake_value is int:
		shake = clampf(float(shake_value), 0.0, 1.0)

## A slider is linear in loudness-ish terms; the mixer wants decibels.
static func to_db(linear: float) -> float:
	if linear <= SILENCE_THRESHOLD:
		return SILENCE_DB
	return linear_to_db(clampf(linear, 0.0, 1.0))
