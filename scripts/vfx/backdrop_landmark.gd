class_name BackdropLandmark
extends Sprite3D
## A hand-authored background landmark (planet, nebula cloud) that drifts slowly
## across the play field behind the gameplay plane and wraps once it leaves view,
## so the infinite scroll never exposes a pop. Billboarded so a round planet stays
## round under the tilted gameplay camera (see scenes/gameplay/graybox.tscn).
##
## Rendering: unshaded + transparent Sprite3D, drawn behind the fighters (its Y sits
## below the Y=0 gameplay plane) and in front of the procedural backdrop. Kept off
## the central combat lane by its wrap band, per the backdrop readability rules.
##
## Zero allocation in _process (spec §31): only the value-type `position` is mutated,
## never a new node/array per frame.

## Drift in world units per second. Nebulae crawl sideways; the planet barely moves.
@export var drift_velocity: Vector3 = Vector3(-0.35, 0.0, 0.0)

## Wrap band (world units). When the landmark passes the far edge along a drifting
## axis, it teleports back to the near edge, so it re-enters seamlessly off-screen.
@export var wrap_min: Vector3 = Vector3(-26.0, -6.0, -18.0)
@export var wrap_max: Vector3 = Vector3(26.0, -6.0, 10.0)

func _process(delta: float) -> void:
	var p := position
	p += drift_velocity * delta
	if drift_velocity.x > 0.0 and p.x > wrap_max.x:
		p.x = wrap_min.x
	elif drift_velocity.x < 0.0 and p.x < wrap_min.x:
		p.x = wrap_max.x
	if drift_velocity.z > 0.0 and p.z > wrap_max.z:
		p.z = wrap_min.z
	elif drift_velocity.z < 0.0 and p.z < wrap_min.z:
		p.z = wrap_max.z
	position = p
