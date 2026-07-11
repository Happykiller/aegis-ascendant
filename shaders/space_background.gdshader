shader_type spatial;
render_mode unshaded, cull_disabled, shadows_disabled;

// Procedural scrolling deep-space backdrop for the play field.
// Sits below the gameplay plane and scrolls toward the player to sell forward
// motion. Fully procedural (no textures): starfield (3 parallax layers) + nebula.
// Bright stars/nebula feed the WorldEnvironment glow for the "claque".

uniform vec3 nebula_color_a : source_color = vec3(0.08, 0.12, 0.32);
uniform vec3 nebula_color_b : source_color = vec3(0.35, 0.10, 0.42);
uniform vec3 deep_color : source_color = vec3(0.015, 0.02, 0.05);
uniform float scroll_speed = 0.35;
uniform float nebula_strength = 0.6;
uniform float star_brightness = 2.2;

float hash21(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

float value_noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	float a = hash21(i);
	float b = hash21(i + vec2(1.0, 0.0));
	float c = hash21(i + vec2(0.0, 1.0));
	float d = hash21(i + vec2(1.0, 1.0));
	return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm(vec2 p) {
	float v = 0.0;
	float amp = 0.5;
	// Rotate each octave to break the value-noise grid alignment (no blocky bands).
	mat2 rot = mat2(vec2(0.80, 0.60), vec2(-0.60, 0.80));
	for (int i = 0; i < 6; i++) {
		v += amp * value_noise(p);
		p = rot * p * 2.03 + vec2(37.1, 17.3);
		amp *= 0.5;
	}
	return v;
}

// One star layer: sparse bright points on a jittered grid.
float star_layer(vec2 uv, float density, float twinkle_seed, float time) {
	vec2 g = uv * density;
	vec2 cell = floor(g);
	vec2 f = fract(g);
	float rnd = hash21(cell + twinkle_seed);
	if (rnd < 0.965) {
		return 0.0;
	}
	vec2 star_pos = vec2(hash21(cell + 1.7), hash21(cell + 3.1));
	float d = length(f - star_pos);
	float core = smoothstep(0.09, 0.0, d);
	float twinkle = 0.6 + 0.4 * sin(time * 3.0 + rnd * 40.0);
	return core * twinkle;
}

void fragment() {
	vec2 uv = UV;
	float t = TIME * scroll_speed;

	// Nebula: two scrolling fbm octaves, parallaxed.
	float n1 = fbm(uv * 3.0 + vec2(0.0, t * 0.5));
	float n2 = fbm(uv * 6.0 - vec2(t * 0.3, t * 0.8));
	float neb = pow(clamp(n1 * n2 * 2.2, 0.0, 1.0), 1.8);
	vec3 col = deep_color;
	col = mix(col, nebula_color_a, neb * nebula_strength);
	col = mix(col, nebula_color_b, pow(neb, 2.5) * nebula_strength);

	// Three star layers at different depths → parallax scroll.
	float stars = 0.0;
	stars += star_layer(uv + vec2(0.0, t * 0.6), 40.0, 0.0, TIME) * 1.0;
	stars += star_layer(uv + vec2(0.0, t * 1.1), 70.0, 11.0, TIME) * 0.7;
	stars += star_layer(uv + vec2(0.0, t * 1.8), 110.0, 23.0, TIME) * 0.45;
	col += vec3(0.7, 0.85, 1.0) * stars * star_brightness;

	ALBEDO = col;
}
