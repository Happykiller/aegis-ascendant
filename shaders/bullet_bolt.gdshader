shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;

// Glowing projectile. Two shapes, chosen by `dart`:
//   dart = 1 → an elongated energy BOLT: a thin bright spine tapering to points
//              along its length, a tight glow hugging it. This is the player's
//              laser — the reference draws sharp darts, not soft blobs/bubbles.
//   dart = 0 → a round ORB: bright core + soft halo, the classic danmaku bullet
//              for enemy fire.
// Procedural, so it stays crisp at any size and needs no texture. The quad's own
// aspect (elongated mesh vs square) does the rest: UV.x is the thin axis, UV.y the
// long one.

uniform vec3 core_color : source_color = vec3(1.0, 0.914, 0.824);
uniform vec3 halo_color : source_color = vec3(1.0, 0.353, 0.239);
uniform float core_size : hint_range(0.05, 0.9) = 0.28;
uniform float halo_opacity : hint_range(0.0, 1.0) = 0.55;
uniform float energy : hint_range(0.0, 8.0) = 2.6;
uniform float dart : hint_range(0.0, 1.0) = 1.0;

void fragment() {
	vec2 p = (UV - 0.5) * 2.0; // p.x = thin axis, p.y = long axis
	float core;
	float halo;
	if (dart > 0.5) {
		// Sharp bolt: spine width pinches to points at both ends (a lens/dart).
		float taper = clamp(1.0 - abs(p.y), 0.0, 1.0);
		float w = core_size * taper;
		core = smoothstep(w, 0.0, abs(p.x));
		float hw = core_size * 2.4 * taper + 0.05;
		halo = smoothstep(hw, w, abs(p.x)) * taper;
	} else {
		// Round orb: bright core wrapped in a soft halo.
		float d = length(p);
		core = smoothstep(core_size, 0.0, d);
		halo = smoothstep(1.0, core_size, d);
	}
	ALBEDO = mix(halo_color, core_color, core) * energy;
	ALPHA = clamp(halo * halo_opacity + core, 0.0, 1.0);
}
