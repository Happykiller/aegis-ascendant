class_name HullDetailSet
extends Resource
## Le jeu de cartes de détail d'une coque de chasseur (ADR-0011, ADR-0013, ADR-0044 §4).
##
## POURQUOI UNE RESOURCE — `HullDetail` ne savait poser qu'UNE feuille, partagée par
## toutes les coques, et ses quatre cartes étaient des `preload` en dur dans le script.
## `ADR-0013` l'avait annoncé : « il devra accepter un jeu par unité ». La cellule-témoin
## est la première à en avoir un (`TEX-0017` à `0019`), calé pour le gros plan et non
## pour un rendu à 14 cm de plaque. Un jeu par coque, dans une Resource typée, validée —
## et plus une seule carte en dur.
##
## DEUX JEUX DANS UN : la coque, et ses TUYÈRES. Les sept matériaux `AA_*` sont imposés
## par le contrat d'export, un huitième n'existe pas ; une matière de tuyère distincte
## n'est possible que parce que les tuyères sont des NŒUDS séparés (`Nozzle_*`, et
## leurs `Petal_*`). `HullDetail` choisit donc le jeu par le nom du nœud, pas par le
## matériau. Le jeu de tuyère est optionnel — tout ou rien.

@export_group("Coque")
## Carte de MULTIPLICATION : les plaques valent ~1,0 (neutre), les rainures moins.
## Posée en `albedo_texture` par-dessus la couleur de palette importée du `.glb`.
@export var mul: Texture2D
@export var normal: Texture2D
@export var roughness: Texture2D
@export var ao: Texture2D
## Relief discret : une coque de chasseur est lisse, ses rainures sont des traits.
@export_range(0.0, 2.0, 0.01) var normal_scale: float = 0.7
## Facteur d'`uv1_scale` : < 1,0 agrandit les plaques (moins de répétitions).
@export_range(0.01, 8.0, 0.01) var tiling: float = 0.25

@export_group("Verriere")
## Opacité de `AA_Glass` pour cette coque, ou -1 pour garder celle du `.glb`.
##
## ⚠️ ELLE EXISTE PARCE QUE LE KIT IMPOSE LA MÊME VITRE À TOUTES LES COQUES : alpha 0,86,
## une verrière sombre, juste ce qu'il faut pour lire « verre » sur un chasseur sans
## intérieur. La cellule-témoin a un cockpit DEDANS (berceau, arceau, consoles) et le
## rapport de forge le dit : « dans Godot l'intérieur sera faible ». Une vitre se règle
## côté moteur, pas en changeant le kit pour quinze coques.
@export_range(-1.0, 1.0, 0.01) var glass_alpha: float = -1.0

@export_group("Tuyeres (optionnel, tout ou rien)")
@export var nozzle_mul: Texture2D
@export var nozzle_normal: Texture2D
@export var nozzle_roughness: Texture2D
@export var nozzle_ao: Texture2D
@export_range(0.0, 2.0, 0.01) var nozzle_normal_scale: float = 0.8
@export_range(0.01, 8.0, 0.01) var nozzle_tiling: float = 1.0

## Le jeu de tuyère existe-t-il ? Il ne se pose que complet : une tuyère avec une
## normale mais sans rugosité prendrait la rugosité de la coque, et personne ne le
## verrait au journal.
func has_nozzle_set() -> bool:
	return nozzle_mul != null and nozzle_normal != null \
		and nozzle_roughness != null and nozzle_ao != null

func validate() -> PackedStringArray:
	var errors := PackedStringArray()
	for pair: Array in [["mul", mul], ["normal", normal], ["roughness", roughness], ["ao", ao]]:
		if pair[1] == null:
			errors.append("%s map is required" % pair[0])
	if normal_scale < 0.0:
		errors.append("normal_scale must be >= 0")
	if tiling <= 0.0:
		errors.append("tiling must be > 0")
	if glass_alpha > 1.0 or (glass_alpha < 0.0 and glass_alpha != -1.0):
		errors.append("glass_alpha must be -1 (untouched) or within [0, 1]")
	var nozzle_maps := 0
	for map: Texture2D in [nozzle_mul, nozzle_normal, nozzle_roughness, nozzle_ao]:
		if map != null:
			nozzle_maps += 1
	if nozzle_maps != 0 and nozzle_maps != 4:
		errors.append("nozzle set is all-or-nothing (got %d of 4 maps)" % nozzle_maps)
	if nozzle_normal_scale < 0.0:
		errors.append("nozzle_normal_scale must be >= 0")
	if nozzle_tiling <= 0.0:
		errors.append("nozzle_tiling must be > 0")
	return errors
