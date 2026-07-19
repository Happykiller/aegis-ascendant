shader_type spatial;
render_mode unshaded, cull_disabled, shadows_disabled, depth_draw_never;

// Procedural deep-space backdrop for the play field.
//
// Sits below the gameplay plane and scrolls toward the player to sell forward
// motion. Fully procedural: no texture, no seam, no tiling artefact however far
// it scrolls.
//
// Structure (back to front):
//   1. deep space gradient
//   2. nebula — domain-warped fbm, so the clouds curl instead of reading as
//      grey blur; two masses at different scroll rates give parallax depth
//   3. dust lanes — a second warped field that *subtracts*, carving dark
//      filaments across the clouds (this is what makes it read as volume)
//   4. four star layers, each scrolling faster than the last
//
// Readability rules (docs/forge/output/graybox_palette.md): the backdrop stays
// cold and desaturated, never touches the cyan reserved for allied fire nor the
// coral reserved for enemy fire, and stays calmest in the middle third where the
// fight happens.

uniform vec3 deep_color : source_color = vec3(0.027, 0.039, 0.071);
uniform vec3 nebula_cold : source_color = vec3(0.13, 0.22, 0.50);
uniform vec3 nebula_deep : source_color = vec3(0.32, 0.16, 0.50);
uniform vec3 nebula_rim : source_color = vec3(0.36, 0.60, 0.75);
uniform vec3 star_color : source_color = vec3(0.82, 0.88, 1.0);
uniform vec3 landmark_color : source_color = vec3(0.24, 0.29, 0.40);

// Magenta accent painted onto the brightest cloud ridges, per ADR-0009 (richer,
// more colourful field). Kept off the centre lane and far from the coral #FF5A3D
// reserved for enemy fire. The planet and moon are now real drifting sprites
// (scenes/vfx/space_backdrop.tscn), not procedural — this shader owns only the
// infinite, seamless stars + nebula.
uniform vec3 nebula_accent : source_color = vec3(0.55, 0.20, 0.42);
uniform float accent_strength : hint_range(0.0, 1.0) = 0.45;

uniform float scroll_speed = 0.35;
uniform float nebula_strength : hint_range(0.0, 2.0) = 1.0;
uniform float dust_strength : hint_range(0.0, 2.0) = 0.9;
uniform float star_brightness : hint_range(0.0, 4.0) = 1.7;

// How much darker the middle third is than the edges. The art must never fight
// the ship and the bullets for attention.
uniform float center_calm : hint_range(0.0, 1.0) = 0.35;

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

// Rotate each octave to break the value-noise grid alignment (no blocky bands).
const mat2 OCTAVE_ROT = mat2(vec2(0.80, 0.60), vec2(-0.60, 0.80));

float fbm(vec2 p) {
	float v = 0.0;
	float amp = 0.5;
	for (int i = 0; i < 5; i++) {
		v += amp * value_noise(p);
		p = OCTAVE_ROT * p * 2.03 + vec2(37.1, 17.3);
		amp *= 0.5;
	}
	return v;
}

// Domain warping (Iñigo Quilez): feed noise back into its own coordinates twice.
// This is the whole trick — it turns isotropic mush into curling, filamented
// cloud with a sense of flow. `flow` is returned so the colour can follow the
// warp instead of being painted on flat.
float warped_fbm(vec2 p, out float flow) {
	vec2 q = vec2(fbm(p), fbm(p + vec2(5.2, 1.3)));
	vec2 r = vec2(fbm(p + 3.4 * q + vec2(1.7, 9.2)), fbm(p + 3.4 * q + vec2(8.3, 2.8)));
	flow = length(r);
	return fbm(p + 3.0 * r);
}

// One star layer: sparse bright points on a jittered grid.
float star_layer(vec2 uv, float density, float seed, float threshold, float time) {
	vec2 g = uv * density;
	vec2 cell = floor(g);
	vec2 f = fract(g);
	float rnd = hash21(cell + seed);
	if (rnd < threshold) {
		return 0.0;
	}
	vec2 star_pos = vec2(hash21(cell + seed + 1.7), hash21(cell + seed + 3.1));
	vec2 delta = f - star_pos;
	float d = length(delta);
	// Crisp point: a tight halo plus a hot pinpoint core, instead of a soft blob.
	// This is the fix for the "blurry stars" — the light is concentrated, so the
	// retro pixelation resolves a sharp pixel instead of a smear.
	float core = smoothstep(0.045, 0.0, d) + smoothstep(0.016, 0.0, d) * 1.4;
	// The rarest stars are bright anchors carrying a 4-point diffraction cross, so
	// the field has a few landmarks instead of reading as uniform noise.
	float rare = smoothstep(0.988, 1.0, rnd);
	float spike_h = smoothstep(0.34, 0.0, abs(delta.x)) * smoothstep(0.020, 0.0, abs(delta.y));
	float spike_v = smoothstep(0.34, 0.0, abs(delta.y)) * smoothstep(0.020, 0.0, abs(delta.x));
	float cross = (spike_h + spike_v) * rare;
	float twinkle = 0.70 + 0.30 * sin(time * 2.4 + rnd * 40.0);
	return (core + cross * 0.7) * twinkle * mix(0.55, 1.8, rare);
}

void fragment() {
	// The quad is 90 x 70, so square up the UV before sampling noise: otherwise
	// every cloud and every star is stretched along X.
	vec2 p = UV * vec2(1.286, 1.0);
	float t = TIME * scroll_speed;

	// --- Nebula: two masses, scrolling at different rates (parallax depth).
	// The camera only frames ~0.6 x 0.47 of UV, so the noise must run at a high
	// enough frequency to fit several cells in shot — below ~5x the clouds
	// degenerate into flat wedges the size of the screen.
	float flow_far;
	float far_mass = warped_fbm(p * 5.0 + vec2(0.0, t * 0.30), flow_far);
	float flow_near;
	float near_mass = warped_fbm(p * 9.0 + vec2(11.0, t * 0.55), flow_near);

	// A large-scale mask keeps whole regions thin, so the field breathes instead
	// of being uniformly cloudy from edge to edge. It never fully clears: the
	// floor keeps a haze everywhere.
	float region = mix(0.30, 1.0, smoothstep(0.25, 0.75, fbm(p * 2.6 + vec2(0.0, t * 0.22))));

	float base_mass = far_mass * 0.75 + near_mass * 0.25;
	float clouds = smoothstep(0.36, 0.82, base_mass) * region;

	// --- Dust lanes: a warped ridge field that carves *into* the clouds.
	float flow_dust;
	float dust_raw = warped_fbm(p * 6.5 + vec2(4.0, t * 0.42), flow_dust);
	float dust = smoothstep(0.44, 0.70, dust_raw);
	clouds *= 1.0 - dust * dust_strength * 0.65;

	// Colour follows the warp: cold indigo in the body, violet where the cloud
	// is dense, a cool rim where it thins out into the void, and a parcimonious
	// magenta accent burning on the densest ridges (ADR-0009: richer field).
	vec3 col = deep_color;
	vec3 cloud_col = mix(nebula_cold, nebula_deep, clamp(flow_far * 1.2, 0.0, 1.0));
	cloud_col = mix(cloud_col, nebula_rim, pow(clamp(near_mass, 0.0, 1.0), 3.0) * 0.55);
	float ridge = smoothstep(0.62, 0.95, base_mass) * pow(clamp(flow_near, 0.0, 1.0), 1.5);
	cloud_col = mix(cloud_col, nebula_accent, ridge * accent_strength);
	col = mix(col, cloud_col, clamp(clouds, 0.0, 1.0) * nebula_strength);

	// --- Distant galactic band: a broad diagonal veil with broken, noisy edges.
	// It crawls independently of the nebula and is darkest through the combat lane.
	float band_axis = p.y - (0.18 + p.x * 0.46 + t * 0.035);
	float band_noise = fbm(p * 4.2 + vec2(18.0, t * 0.08));
	float galaxy = smoothstep(0.24, 0.02, abs(band_axis + (band_noise - 0.5) * 0.16));
	galaxy *= 0.30 + band_noise * 0.28;
	col += landmark_color * galaxy * 0.32;

	// The moon and the distant planet that used to live here are now real drifting
	// sprites (scenes/vfx/space_backdrop.tscn) — hand-authored art instead of the
	// procedural corner-glow / ghost-ring that read poorly. This shader keeps only
	// the infinite, seamless nebula + stars behind them.

	// --- Stars: five depths, the near ones racing, the far ones crawling. The far
	// dense layer fills the void so the field never reads as empty.
	float stars = 0.0;
	stars += star_layer(p + vec2(0.0, t * 0.22), 26.0, 47.0, 0.940, TIME) * 0.55;
	stars += star_layer(p + vec2(0.0, t * 0.35), 34.0, 0.0, 0.948, TIME) * 1.00;
	stars += star_layer(p + vec2(0.0, t * 0.62), 58.0, 11.0, 0.958, TIME) * 0.72;
	stars += star_layer(p + vec2(0.0, t * 1.05), 92.0, 23.0, 0.966, TIME) * 0.48;
	stars += star_layer(p + vec2(0.0, t * 1.70), 140.0, 37.0, 0.978, TIME) * 0.30;
	// Thick cloud occludes the starfield behind it — cheap, and sells the depth.
	stars *= 1.0 - clamp(clouds, 0.0, 1.0) * 0.65;
	col += star_color * stars * star_brightness;

	// --- Rare foreground debris. Large cells and a high threshold prevent a
	// repeating field; stretched chips move faster than every star layer.
	vec2 debris_uv = p + vec2(0.17, t * 2.8);
	vec2 debris_grid = debris_uv * vec2(15.0, 11.0);
	vec2 debris_cell = floor(debris_grid);
	vec2 debris_f = fract(debris_grid) - 0.5;
	float debris_seed = hash21(debris_cell + 71.0);
	vec2 debris_offset = vec2(hash21(debris_cell + 13.0), hash21(debris_cell + 29.0)) - 0.5;
	float chip = smoothstep(0.12, 0.04,
		length((debris_f - debris_offset * 0.55) * vec2(0.55, 1.8)));
	chip *= smoothstep(0.986, 0.998, debris_seed);
	col += mix(vec3(0.10, 0.12, 0.17), landmark_color, debris_seed) * chip * 0.65;

	// --- Keep the middle third calm: the fight reads there.
	float from_center = abs(UV.x - 0.5) * 2.0;
	col *= mix(1.0 - center_calm, 1.0, smoothstep(0.30, 1.0, from_center));

	ALBEDO = col;
}
