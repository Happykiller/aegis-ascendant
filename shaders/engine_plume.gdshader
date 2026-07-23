shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled, fog_disabled;

// Plume d'échappement — le cône de gaz éjecté par la tuyère, avec ses DISQUES DE MACH :
// les nœuds lumineux successifs que les ondes de choc dessinent dans le jet.
//
// POURQUOI UNE GÉOMÉTRIE ET PAS DES PARTICULES — les disques de Mach sont des ondes
// STATIONNAIRES : elles restent fixes par rapport à la tuyère pendant que le gaz les
// traverse. Des particules qui s'éloignent de l'émetteur ne peuvent pas les tenir en
// place, quel que soit le réglage (ADR-0017). D'où un maillage solidaire de la coque.
//
// LE MAILLAGE ATTENDU est un CylinderMesh UNITAIRE : rayons haut et bas à 1, hauteur 1,
// capuchons coupés. Tout le profil est calculé ici — le maillage n'apporte que sa
// subdivision. On lit l'axe sur VERTEX.y et JAMAIS sur UV.y : Godot range la paroi du
// cylindre dans la MOITIÉ haute de l'espace UV (`uv.y = v * 0.5`, cylinder_mesh.cpp), le
// reste étant réservé aux capuchons — un profil piloté par UV.y s'arrêterait à mi-plume.

// Longueur du jet, en unités monde, mesurée depuis le col. Poussée par le GDScript.
uniform float plume_length : hint_range(0.05, 8.0) = 1.2;
// Rayon au col (la section de sortie de la tuyère).
uniform float throat_radius : hint_range(0.005, 2.0) = 0.09;
// Évasement du VENTRE : rayon au plus large, rapporté au col. Le ventre se situe juste
// en aval de la tuyère — au-delà, la plume se referme.
uniform float belly_flare : hint_range(0.2, 6.0) = 1.8;
// Nombre de disques. ⚠️ PLAFOND DE LISIBILITÉ : le post rétro rend à 960×540, où la
// plume du joueur fait ~40 px de long. Au-delà de 3 disques le motif devient une
// bouillie grise (cf. .claude/resources/pratique-revue-asset.md).
uniform float shock_count : hint_range(0.0, 5.0) = 3.0;
// Amplitude des disques, 0 = plume lisse. C'est ce paramètre que la poussée ouvre :
// à bas régime un moteur ne montre AUCUN disque.
uniform float shock_depth : hint_range(0.0, 0.9) = 0.35;

uniform vec3 core_color : source_color = vec3(0.85, 0.98, 1.0);
uniform vec3 plume_color : source_color = vec3(0.247, 0.851, 0.91);
uniform vec3 tail_color : source_color = vec3(0.11, 0.17, 0.37);
uniform float energy : hint_range(0.0, 12.0) = 3.2;
// Battement de combustion. ⚠️ Au-delà de ~0,1 ça ne lit plus comme une flamme mais
// comme un défaut de rendu (le même piège que le scintillement des tuyères mécaniques).
uniform float flicker : hint_range(0.0, 0.25) = 0.06;

varying float axial;

void vertex() {
	// 0 au col, 1 en queue. Le cylindre unitaire va de y = +0,5 (haut) à y = -0,5.
	float t = clamp(0.5 - VERTEX.y, 0.0, 1.0);
	// LE PROFIL EST UNE PLUME, PAS UN CÔNE. Le gaz s'épanouit en sortant de la tuyère
	// (détente), puis se dilue et se referme en POINTE. Deux termes, donc :
	//   — le ventre, qui s'ouvre vite sur le premier quart ;
	//   — l'effilement, qui reprend tout et termine sur un point.
	//
	// ⚠️ Un évasement MONOTONE (`mix(1.0, flare, pow(t, k))`, quel que soit l'exposant)
	// rend un CÔNE OUVERT à bout franc et large — la forme la plus éloignée d'une plume,
	// et celle qu'on obtient par défaut si l'on ne pense qu'à « ça s'ouvre en sortant ».
	// ⚠️ Le ventre s'ouvre TRÈS TÔT (8 % de la course) et TRÈS PEU. Étalé sur un quart
	// avec un facteur d'évasement franc, il produit un bulbe collé à la tuyère suivi
	// d'une colonne à flancs parallèles : le contraire d'une plume, qui est large à la
	// sortie puis se referme d'un seul mouvement.
	float belly = mix(1.0, belly_flare, smoothstep(0.0, 0.08, t));
	float taper = pow(1.0 - t, 0.5);
	float cone = belly * taper;
	// Le train de chocs : une cellule TRIANGULAIRE, pincée aux deux bouts et renflée au
	// milieu, amortie vers la queue — chaque cellule dissipe, la suivante est plus molle.
	//
	// ⚠️ TRIANGLE ET NON SINUS. Un sinus arrondit les raccords : la plume devient un
	// chapelet de perles rondes (vérifié en capture), soit exactement l'effet « petits
	// nuages » qu'on remplace. Les flancs droits et les angles vifs du triangle sont ce
	// qui fait lire un DIAMANT — la forme tient à la dérivée, pas à l'amplitude.
	float cell = 1.0 - abs(2.0 * fract(t * shock_count) - 1.0);
	// ⚠️ Le train de chocs ne commence PAS au col : la section de sortie de la tuyère
	// est une donnée mécanique, et un premier renflement posé dessus donne à la plume
	// un bulbe collé au vaisseau. Le premier choc s'établit en aval.
	// Le choc PINCE, il ne gonfle jamais : la cellule va de l'enveloppe pleine (au
	// renflement) à `1 - shock_depth` (au col de choc). Autorisé à dépasser l'enveloppe,
	// le premier choc posait un bulbe plus large que la tuyère juste derrière la coque.
	float shock = 1.0 - shock_depth * (1.0 - cell) * (1.0 - t) * smoothstep(0.0, 0.12, t);
	// VERTEX.xz est de norme 1 sur un cylindre unitaire : la multiplication EST le rayon.
	VERTEX.xz *= throat_radius * cone * shock;
	// La plume pousse vers +Y local, depuis l'origine du nœud (donc depuis la tuyère) —
	// et non centrée sur elle comme le serait le cylindre brut.
	VERTEX.y = t * plume_length;
	axial = t;
}

void fragment() {
	float t = axial;
	// Le disque de Mach lui-même : le choc droit qui recomprime le gaz AU PINCEMENT,
	// donc là où la cellule est la plus étroite — et non sur le renflement. C'est
	// l'anneau brillant que montrent les plumes de moteur-fusée.
	float cell = 1.0 - abs(2.0 * fract(t * shock_count) - 1.0);
	float node = pow(1.0 - cell, 7.0) * (1.0 - t) * step(0.02, shock_depth);
	// Épaisseur optique : de biais, le regard traverse plus de gaz. C'est ce terme qui
	// fait lire un VOLUME et non un tube peint.
	float rim = 1.0 - abs(dot(NORMAL, VIEW));
	// ⚠️ L'ENVELOPPE NE DOIT PAS ÊTRE UN ANNEAU. Le cône est rendu `cull_disabled` et
	// additif : ses deux parois s'additionnent, et sur la silhouette elles sont toutes
	// deux rasantes. Pondéré à 0,3 + 0,7·rim, le bord devenait un cerceau lumineux et
	// la plume lisait comme une bulle de savon (vérifié en capture). Le gaz garde donc
	// un plancher large, et le biais ne fait que l'accentuer.
	float shell = 0.6 + 0.4 * rim;
	float fill = mix(1.0, shell, smoothstep(0.02, 0.4, t));
	// Le jet s'éteint EN SE DILUANT le long de sa course.
	//
	// ⚠️ EXPOSANT FAIBLE, à dessein. C'est la GÉOMÉTRIE qui termine la plume, en pointe ;
	// l'alpha ne fait que la diluer. Mesuré à 1,3, l'alpha éteignait le jet bien avant que
	// le maillage ne se referme : on ne voyait que le ventre, coupé net — un bout franc,
	// exactement le défaut de forme signalé.
	float decay = pow(1.0 - t, 0.4);

	// ⚠️ Le blanc du cœur reste CONFINÉ au col (14 % de la course). Étalé sur 30 %, il
	// couvrait la moitié visible du jet : la plume rendait une colonne blanche, et la
	// couleur de camp — donc la moitié du signal d'accélération — disparaissait.
	vec3 col = mix(core_color, plume_color, smoothstep(0.0, 0.14, t));
	col = mix(col, tail_color, smoothstep(0.35, 1.0, t));
	// Un disque de Mach est plus CHAUD que le gaz autour : le choc recomprime.
	col = mix(col, core_color, node * 0.85);

	float flick = 1.0 + flicker * sin(TIME * 41.0 + t * 9.0);

	ALBEDO = col * energy * flick;
	ALPHA = clamp(fill * decay + node * 0.6, 0.0, 1.0);
}
