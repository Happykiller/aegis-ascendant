class_name CommsTrace
extends Line2D
## Oscillogramme du bloc COMMS de l'interface Helios. L'accueil et l'écran de pause
## portent le MÊME appareil : c'est lui qui fait que les deux écrans se lisent comme
## une seule interface, et non comme deux maquettes voisines.
##
## Deux régimes :
##   LIVE — canal ouvert, la trace vit ;
##   HOLD — canal tenu, ligne plate parcourue par un balayage. C'est ce qui dit
##          « simulation suspendue » sans écrire le mot une deuxième fois.
##
## Points PRÉALLOUÉS une fois : la courbe est réécrite en place à chaque image,
## jamais reconstruite (spec §31, zéro allocation en boucle).

enum Mode { LIVE, HOLD }

const POINTS := 48
const SPAN := 232.0       # largeur de la fenêtre de tracé, en pixels d'interface
const AMPLITUDE := 26.0

@export var mode: Mode = Mode.LIVE

var _points: PackedVector2Array = PackedVector2Array()
var _age: float = 0.0

func _ready() -> void:
	_points.resize(POINTS)
	_redraw()

func _process(delta: float) -> void:
	_age += delta
	_redraw()

func _redraw() -> void:
	for i in POINTS:
		var t := float(i) / float(POINTS - 1)
		var value := _sample_hold(t) if mode == Mode.HOLD else _sample_live(t)
		_points[i] = Vector2(t * SPAN, -value * AMPLITUDE * 0.5)
	points = _points

## Trois sinusoïdes de périodes non harmoniques : assez irrégulier pour lire comme
## un signal, assez bon marché pour être gratuit.
func _sample_live(t: float) -> float:
	var phase := _age * 2.1 + t * 9.0
	return sin(phase) * 0.5 + sin(phase * 2.7) * 0.28 + sin(phase * 6.1) * 0.12

## Ligne de base tenue, parcourue par un balayage gaussien qui sort du cadre entre
## deux passes. Une trace RIGOUREUSEMENT plate lirait comme un canal mort — or le
## jeu n'est pas mort, il attend.
func _sample_hold(t: float) -> float:
	var sweep := fmod(_age * 0.32, 1.35) - 0.175
	var d := t - sweep
	return exp(-d * d * 520.0) * 0.85 + sin(_age * 1.1 + t * 2.0) * 0.04
