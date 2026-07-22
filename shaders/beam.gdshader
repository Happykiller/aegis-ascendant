shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled;

// Faisceau du canon du Choir Harvester — et sa ligne de télégraphe.
//
// UN SEUL OBJET, DEUX RÉGIMES. La ligne de visée qui annonce le tir et le faisceau
// qui frappe sont le même quad : seuls `width`, `energy` et `pulse` changent. Deux
// nœuds distincts auraient divergé au premier réglage — c'est la leçon de
// `comms_trace.gd`, qui sert l'accueil et l'écran de pause avec un seul appareil.
//
// Additif et sans écriture de profondeur : le faisceau passe par-dessus le plan de
// jeu sans z-fighter avec les coques, qui vivent au même Y.

uniform vec4 core_color : source_color = vec4(1.0, 0.88, 1.0, 1.0);
// Magenta du Null Choir (charte §3, #D93D9C) : le danger ennemi ne doit jamais
// emprunter le cyan allié.
uniform vec4 edge_color : source_color = vec4(0.851, 0.239, 0.612, 1.0);
uniform float energy : hint_range(0.0, 4.0) = 1.0;
// 0 = faisceau plein ; 1 = télégraphe, qui bat pour dire « ça n'a pas encore tiré ».
uniform float pulse : hint_range(0.0, 1.0) = 0.0;
uniform float scroll_speed = 5.0;
// Estompe les deux extrémités : un faisceau qui commence et finit net lit comme un
// rectangle posé sur l'image.
uniform float end_fade : hint_range(0.0, 0.5) = 0.06;

void fragment() {
	// UV.x traverse la largeur, UV.y file le long du faisceau.
	float across = abs(UV.x - 0.5) * 2.0;

	// Cœur presque blanc, bords magenta : la recette des projectiles du projet
	// (« toujours cœur lumineux + halo contrasté », charte §3).
	float core = 1.0 - smoothstep(0.0, 0.32, across);
	float glow = pow(1.0 - smoothstep(0.0, 1.0, across), 2.0);

	// Battement du télégraphe. À `pulse = 0` le facteur vaut exactement 1 : le
	// faisceau de tir ne clignote pas, il est plein.
	float beat = 1.0 - pulse * (0.5 + 0.5 * sin(TIME * 9.0)) * 0.65;

	// Filage le long du canon : sans lui, un faisceau immobile paraît peint.
	float streak = 0.85 + 0.15 * sin(UV.y * 26.0 - TIME * scroll_speed);

	float ends = smoothstep(0.0, end_fade, UV.y) * (1.0 - smoothstep(1.0 - end_fade, 1.0, UV.y));

	vec3 col = mix(edge_color.rgb, core_color.rgb, core);
	ALBEDO = col;
	// Additif : c'est ALBEDO qui porte l'intensité, ALPHA ne sert qu'au découpage.
	ALBEDO *= (core * 1.6 + glow) * energy * beat * streak * ends;
	ALPHA = 1.0;
}
