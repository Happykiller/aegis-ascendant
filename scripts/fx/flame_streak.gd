class_name FlameStreak
## A tapered vertical streak — bright and wide at the head, pinching to a point at
## the tail — built in code (no texture asset). Replaces the round SoftDot on engine
## exhaust so a trail reads as a flame jet, not a string of soap bubbles.

## Cached: immutable, shared by every exhaust quad.
static var _cached: ImageTexture = null

static func texture() -> ImageTexture:
	if _cached != null:
		return _cached
	var w := 32
	var h := 96
	var img := Image.create(w, h, false, Image.FORMAT_RGBA8)
	for y in h:
		var ny := float(y) / float(h - 1)         # 0 head (top) .. 1 tail (bottom)
		var width := maxf(1.0 - ny * 0.9, 0.03)   # pinches toward the tail
		var bright := pow(1.0 - ny, 0.7)          # hottest at the head, fades out
		for x in w:
			var nx := (float(x) / float(w - 1) - 0.5) * 2.0
			var edge := clampf(1.0 - absf(nx) / width, 0.0, 1.0)
			var a := pow(edge, 1.6) * bright
			img.set_pixel(x, y, Color(1.0, 1.0, 1.0, a))
	_cached = ImageTexture.create_from_image(img)
	return _cached
