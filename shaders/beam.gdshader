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

// ⚠️ CORAIL, PAS MAGENTA. `graybox_palette.md` (normatif) sépare deux canaux ennemis
// et pose un contrat de lecture : le joueur doit trancher « en moins de 200 ms si
// l'objet rose/chaud est une SOURCE (magenta #D93D9C, énergie 1) ou un DANGER DIRECT
// (corail, énergie 2,5-4) ». Un faisceau qui tue en 1,5 s peint dans la couleur des
// feux de coque inverse ce contrat : il se lirait comme une pièce du boss.
//
// C'est littéralement la recette du projectile ennemi (`bullet_manager.tscn`) —
// cœur blanc CHAUD #FFE9D2, halo corail #FF5A3D — portée à l'échelle d'un rayon.
// Le premier jet ne vérifiait que la moitié de la règle (« ne pas emprunter le cyan
// allié ») et manquait l'autre moitié, qui était la seule qui comptait ici.
uniform vec4 core_color : source_color = vec4(1.0, 0.914, 0.824, 1.0);
uniform vec4 edge_color : source_color = vec4(1.0, 0.353, 0.239, 1.0);
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
