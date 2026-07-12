class_name GameplayPlane
## Logical 2D gameplay plane (spec §16.2). Pure static helpers, testable headless.
## Convention: logical plane = world XZ plane at Y = 0.
##   logical +x -> world +X (screen right)
##   logical +y -> world -Z (screen up)
## Logical positions are authoritative for all gameplay collisions; the 3D
## scene is only a projection of them.

## Logical play area in world units (spec/charter: 24 x 14, centered on origin).
const BOUNDS := Rect2(Vector2(-12.0, -7.0), Vector2(24.0, 14.0))

## Input vectors come in Godot's screen convention (+y = down); the logical
## plane is up-positive, so the vertical axis must be flipped on the way in.
static func from_input(input_vector: Vector2) -> Vector2:
	return Vector2(input_vector.x, -input_vector.y)

static func to_world(plane_position: Vector2) -> Vector3:
	return Vector3(plane_position.x, 0.0, -plane_position.y)

static func to_plane(world_position: Vector3) -> Vector2:
	return Vector2(world_position.x, -world_position.z)

static func clamp_to_bounds(plane_position: Vector2) -> Vector2:
	return plane_position.clamp(BOUNDS.position, BOUNDS.end)

static func is_inside(plane_position: Vector2, margin: float = 0.0) -> bool:
	return BOUNDS.grow(margin).has_point(plane_position)
