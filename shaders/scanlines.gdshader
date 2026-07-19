shader_type canvas_item;

// Light CRT scanline overlay: thin dark horizontal lines, alpha-blended over the
// whole screen for a retro-arcade read (spec: HUD refonte). Drawn on a full-rect
// ColorRect on a CanvasLayer above everything.

uniform float line_alpha : hint_range(0.0, 1.0) = 0.18;
uniform float period : hint_range(2.0, 8.0) = 4.0; // dark for the top half of each period

void fragment() {
	float dark = step(period * 0.5, mod(FRAGCOORD.y, period));
	COLOR = vec4(0.0, 0.0, 0.0, dark * line_alpha);
}
