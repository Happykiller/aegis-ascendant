shader_type spatial;
render_mode unshaded, blend_mix, cull_disabled, depth_draw_never, shadows_disabled;

// Atmosphère de la planète de fond.
//
// POURQUOI — `planet_hero.png` est un disque à bord BINAIRE : mesuré, son alpha passe
// de 255 à 0 en 4 pixels sur un rayon de 500, soit 0,8 % du rayon. À la taille où la
// planète est rendue (~300 px), ce dégradé tombe sous le pixel. Un disque clair
// (luminance moyenne 0,247) posé d'un trait net sur une nébuleuse sombre et chargée :
// il se lit comme un autocollant, pas comme un corps céleste dans le même espace.
//
// Trois choses le remettent dans le milieu, et la troisième est la plus importante :
//
//  1. un LIMBE adouci — on remplace l'alpha de la texture par une transition calculée,
//     large de quelques pixels à l'écran ;
//  2. un ANNEAU atmosphérique juste à l'intérieur du limbe, qui donne l'épaisseur d'air ;
//  3. un HALO extérieur, qui déborde sur le fond. C'est lui qui fait que la planète est
//     DANS l'image et non DESSUS — un disque sans halo reste une découpe, même avec un
//     bord doux.
//
// Anneau et halo sont modulés par la luminance de la texture au limbe : une atmosphère
// ne brille que du côté éclairé. Les allumer sur tout le pourtour donnerait un anneau
// de néon autour d'une planète à moitié dans la nuit.
//
// ⚠️ Le billboard est fait ICI, en vertex(). La propriété `billboard` d'un Sprite3D
// agit sur son matériau interne, que `material_override` remplace : sans ce code, la
// planète redeviendrait un disque écrasé sous la caméra inclinée du combat.

uniform sampler2D disc_tex : source_color, filter_linear_mipmap;

// Géométrie du disque dans l'image, MESURÉE sur le fichier (bbox des pixels opaques),
// pas estimée : le disque n'est ni centré ni inscrit dans le carré.
uniform vec2 disc_center = vec2(0.5056, 0.4864);
uniform float disc_radius = 0.401;

// Adoucissement du limbe, en fraction du rayon. 0,018 donne ~3 px à l'écran : assez
// pour tuer l'escalier, trop peu pour donner une planète floue.
uniform float limb_softness : hint_range(0.0, 0.1) = 0.018;

uniform vec4 atmosphere_color : source_color = vec4(0.45, 0.66, 1.0, 1.0);
uniform float rim_width : hint_range(0.0, 0.5) = 0.22;
uniform float rim_energy : hint_range(0.0, 3.0) = 0.3;
uniform float halo_width : hint_range(0.0, 0.6) = 0.235;
uniform float halo_energy : hint_range(0.0, 2.0) = 0.38;
uniform float opacity : hint_range(0.0, 1.0) = 1.0;

float luma(vec3 c) {
	return dot(c, vec3(0.2126, 0.7152, 0.0722));
}

void vertex() {
	// Billboard qui conserve l'échelle (le rayon du disque ne doit pas respirer avec
	// l'orientation de la caméra).
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(
		INV_VIEW_MATRIX[0], INV_VIEW_MATRIX[1], INV_VIEW_MATRIX[2], MODEL_MATRIX[3]);
	MODELVIEW_MATRIX = MODELVIEW_MATRIX * mat4(
		vec4(length(MODEL_MATRIX[0].xyz), 0.0, 0.0, 0.0),
		vec4(0.0, length(MODEL_MATRIX[1].xyz), 0.0, 0.0),
		vec4(0.0, 0.0, length(MODEL_MATRIX[2].xyz), 0.0),
		vec4(0.0, 0.0, 0.0, 1.0));
}

void fragment() {
	vec4 tex = texture(disc_tex, UV);

	// Rayon normalisé : 1,0 est exactement le limbe.
	float r = length(UV - disc_center) / disc_radius;

	// 1. Limbe adouci. On IGNORE l'alpha de la texture : il est binaire, c'est le
	// défaut qu'on corrige. La forme, elle, est parfaitement circulaire — la mesure
	// donne 0,3987 de rayon en x contre 0,4043 en y.
	float disc = 1.0 - smoothstep(1.0 - limb_softness, 1.0 + limb_softness, r);

	// De quel côté l'atmosphère doit-elle s'allumer ? On regarde la texture au point
	// du limbe le plus proche : nuit = sombre, jour = clair.
	vec2 limb_uv = disc_center + normalize(UV - disc_center) * disc_radius * 0.96;
	float lit = smoothstep(0.08, 0.38, luma(texture(disc_tex, limb_uv).rgb));

	// 2. Anneau intérieur.
	float rim = smoothstep(1.0 - rim_width, 1.0, r) * disc * lit;

	// 3. Halo extérieur — hors du disque uniquement.
	float halo = (1.0 - smoothstep(1.0, 1.0 + halo_width, r)) * (1.0 - disc) * lit;

	// Dans le disque on garde la texture ; dehors, seule l'atmosphère existe.
	//
	// ⚠️ `lit` DOIT multiplier la couleur du dehors, et pas seulement l'anneau et le
	// halo. Sans lui, la bande de transition du limbe peignait `atmosphere_color` à
	// pleine luminance (0,64) sous une alpha d'environ 0,5 — sur TOUT le pourtour,
	// côté nuit compris. Mesuré par différence d'images : un trait bleu de 2 à 3 px
	// cerclait la planète là où le fond était noir, et l'on avait remplacé une
	// découpe franche par un cerclage au compas. Le halo diffus, lui, était correct
	// dès le premier essai — c'est le terme qu'on ne soupçonnait pas qui traçait.
	vec3 sky = atmosphere_color.rgb * lit;
	vec3 col = mix(sky, tex.rgb, disc);
	col += atmosphere_color.rgb * rim * rim_energy;

	ALBEDO = col;
	ALPHA = clamp(disc + halo * halo_energy, 0.0, 1.0) * opacity;
}
