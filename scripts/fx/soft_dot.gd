class_name SoftDot
## Radial white-to-transparent ramp, built in code (no texture asset).
##
## Every additive quad in the game — engine trail, muzzle flash, explosion
## sparks — needs this. Without it a particle is a bare quad: a hard-edged
## square of additive white. The ramp is what turns it into an ember.

## Cached: the texture is immutable and every additive material shares it.
static var _cached: GradientTexture2D = null

static func texture() -> GradientTexture2D:
	if _cached != null:
		return _cached
	var gradient := Gradient.new()
	gradient.set_color(0, Color(1.0, 1.0, 1.0, 1.0))
	gradient.set_color(1, Color(1.0, 1.0, 1.0, 0.0))
	gradient.add_point(0.45, Color(1.0, 1.0, 1.0, 0.55))
	var tex := GradientTexture2D.new()
	tex.gradient = gradient
	tex.width = 64
	tex.height = 64
	tex.fill = GradientTexture2D.FILL_RADIAL
	tex.fill_from = Vector2(0.5, 0.5)
	tex.fill_to = Vector2(1.0, 0.5)
	_cached = tex
	return _cached
