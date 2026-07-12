shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;

// Glowing projectile: a hot core wrapped in a soft halo, drawn on a flat quad
// lying on the play plane. Procedural, so it stays crisp at any size and needs
// no texture.
//
// This is the shape the palette prescribes (graybox_palette.md §"Transposition"):
// a bright core plus a wider, dimmer halo — never a bare core, which reads as an
// impact flash. Energy pushes the core above 1.0 so the environment glow catches
// it and the bolt blooms instead of sitting flat on the backdrop.

uniform vec3 core_color : source_color = vec3(1.0, 0.914, 0.824);
uniform vec3 halo_color : source_color = vec3(1.0, 0.353, 0.239);
uniform float core_size : hint_range(0.05, 0.9) = 0.34;
uniform float halo_opacity : hint_range(0.0, 1.0) = 0.55;
uniform float energy : hint_range(0.0, 8.0) = 2.5;

void fragment() {
	// UV centred to [-1, 1]: the quad's own aspect stretches this into a bolt
	// (elongated mesh) or an orb (square mesh) without touching the shader.
	vec2 p = (UV - 0.5) * 2.0;
	float d = length(p);

	float core = smoothstep(core_size, 0.0, d);
	float halo = smoothstep(1.0, core_size, d);

	ALBEDO = mix(halo_color, core_color, core) * energy;
	ALPHA = clamp(halo * halo_opacity + core, 0.0, 1.0);
}
