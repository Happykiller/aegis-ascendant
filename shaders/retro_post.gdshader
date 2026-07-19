shader_type canvas_item;

// Retro post-process over the rendered 3D frame (ADR-0009 target: la référence est
// du pixel-art HD dense et chaud, pas de la 3D froide). Pixelation + palette
// posterisation + ordered (Bayer) dithering + a mild warm/contrast/saturation lift.
// No asset is re-authored: it restyles the whole frame. Drawn on a full-rect
// ColorRect on a CanvasLayer *below* the HUD, so the interface stays crisp.

uniform sampler2D screen_tex : hint_screen_texture, filter_nearest;
// Virtual pixel grid (16:9). Lower = chunkier pixels.
uniform vec2 target_res = vec2(480.0, 270.0);
// Colour steps kept per channel after quantisation.
uniform float levels : hint_range(2.0, 64.0) = 20.0;
uniform float dither_amount : hint_range(0.0, 2.0) = 0.9;
uniform float saturation : hint_range(0.0, 2.0) = 1.18;
uniform float contrast : hint_range(0.5, 2.0) = 1.10;
uniform float warmth : hint_range(-0.2, 0.2) = 0.03;

// 4x4 Bayer matrix (values 0..15), the classic ordered-dither kernel.
const float BAYER[16] = float[16](
	0.0, 8.0, 2.0, 10.0,
	12.0, 4.0, 14.0, 6.0,
	3.0, 11.0, 1.0, 9.0,
	15.0, 7.0, 13.0, 5.0
);

void fragment() {
	// 1. Pixelate: snap the sample to the virtual grid (nearest filtering).
	vec2 uv = floor(SCREEN_UV * target_res) / target_res;
	vec3 col = texture(screen_tex, uv).rgb;

	// 2. Push the cold, flat 3D toward the reference: contrast, a touch of warmth,
	// then saturation around luma.
	col = (col - 0.5) * contrast + 0.5;
	col.r += warmth;
	col.b -= warmth;
	float luma = dot(col, vec3(0.299, 0.587, 0.114));
	col = mix(vec3(luma), col, saturation);
	col = clamp(col, 0.0, 1.0);

	// 3. Ordered dithering before quantisation → retro dithered gradients instead
	// of hard colour bands.
	ivec2 c = ivec2(mod(SCREEN_UV * target_res, 4.0));
	float threshold = (BAYER[c.y * 4 + c.x] / 16.0 - 0.5) * dither_amount;
	col += threshold / levels;

	// 4. Posterise to a limited palette.
	col = floor(col * levels + 0.5) / levels;

	COLOR = vec4(clamp(col, 0.0, 1.0), 1.0);
}
