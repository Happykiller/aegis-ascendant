class_name CortegeFlame
extends Node3D
## La flamme d'un groupe propulsif — le principal élément artistique de la phase finale (spec §5).
##
## ⚠️ « MIEUX VAUT UN MOTEUR ASSEZ SIMPLE AVEC UNE EXCELLENTE PROPULSION ANIMÉE QU'UN MOTEUR
## ULTRA DÉTAILLÉ AVEC UNE FLAMME MÉDIOCRE » (spec §20). C'est le seul endroit de ce chantier où
## la spec demande explicitement de SURINVESTIR, et c'est cohérent avec ce que le dépôt sait
## déjà : sur 500 m de coque, le détail perçu vient de la matière et de la lumière, pas des
## triangles.
##
## ⚠️ ELLE N'EST JAMAIS CONSTANTE, ET C'EST TOUT CE QUI LA REND VIVANTE. Un cône opaque de
## longueur fixe se lit comme un décor collé sous une tuyère. La spec chiffre la variation —
## longueur ±10 à 15 %, largeur ±5 à 10 % — et ces bornes valent mieux qu'un « ça bouge un peu » :
## au-delà, la flamme bat comme un cœur et attire l'œil hors de la cible ; en deçà, elle est morte.
##
## ⚠️ ET LA VARIATION EST DÉTERMINISTE. Deux sinusoïdes incommensurables, jamais un tirage au
## hasard : un survol se juge en comparant deux passages, et une flamme aléatoire rend deux
## captures incomparables. Même règle que le tremblement d'arrachement et que les arcs du nœud.

## Ce que la flamme rend selon ce que fait le moteur.
enum Regime { STEADY, ROUGH, SPUTTER, DYING }

## Les trois couches de la spec §5 : cœur étroit très lumineux, corps magenta, halo.
## ⚠️ TROIS ET PAS UNE. Une seule couche additive donne un aplat qui sature au centre et coupe
## net sur les bords ; c'est la superposition qui fait le dégradé, sans une seule texture.
const CORE_TINT := Color(1.0, 0.86, 0.98)
const BODY_TINT := Color("d93d9c")
const HALO_TINT := Color(0.62, 0.20, 0.72)

const CORE_WIDTH := 0.26
const BODY_WIDTH := 0.62
const HALO_WIDTH := 1.00
const CORE_LENGTH := 0.55
const BODY_LENGTH := 0.90
const HALO_LENGTH := 1.15

const CORE_GLOW := 5.4
const BODY_GLOW := 3.1
const HALO_GLOW := 1.3

## Les deux fréquences de la respiration. ⚠️ INCOMMENSURABLES : un rapport simple (2, 3, 1,5)
## donne un motif qui se répète, et l'œil apprend un motif en quelques secondes.
const BREATH_A := 0.83
const BREATH_B := 2.17

var _layers: Array[MeshInstance3D] = []
var _mats: Array[StandardMaterial3D] = []
var _base_len := 1.0
var _base_wide := 1.0
var _phase := 0.0

static func make(length: float, width: float, phase: float) -> CortegeFlame:
	var flame := CortegeFlame.new()
	flame._base_len = length
	flame._base_wide = width
	flame._phase = phase
	return flame

# --- La règle, pure et testable sans arbre -------------------------------------

## (facteur de longueur, facteur de largeur) à `t` secondes, pour un régime donné.
##
## ⚠️ LES BORNES SONT CELLES DE LA SPEC, ET ELLES SONT TESTÉES. Une flamme qui les dépasse ne
## paraît pas « plus vivante » : elle devient le sujet de l'image, et le joueur cesse de regarder
## les verrous — c'est-à-dire la seule chose qu'il ait à faire.
static func shape_at(t: float, phase: float, regime: Regime) -> Vector2:
	var l_amp := 0.12
	var w_amp := 0.07
	match regime:
		# ⚠️ ABÎMÉE, ELLE N'EST PAS PLUS PETITE : ELLE EST PLUS IRRÉGULIÈRE. Une flamme qui
		# rétrécit se lirait comme un moteur qu'on éteint proprement ; ce qu'il faut lire, c'est
		# une machine qui perd sa tenue.
		Regime.ROUGH:
			l_amp = 0.26
			w_amp = 0.15
		Regime.SPUTTER:
			l_amp = 0.55
			w_amp = 0.24
		Regime.DYING:
			l_amp = 0.70
			w_amp = 0.30
	var a := sin((t + phase) * BREATH_A * TAU)
	var b := sin((t + phase * 1.7) * BREATH_B * TAU)
	var l := 1.0 + l_amp * (0.62 * a + 0.38 * b)
	var w := 1.0 + w_amp * (0.45 * b - 0.55 * a)
	# ⚠️ LE HOQUET DE L'INTERMITTENTE EST UN SEUIL, PAS UNE SINUSOÏDE. « Poussée intermittente »
	# (spec §8) veut dire qu'elle S'INTERROMPT : une simple variation d'amplitude, si grande
	# soit-elle, ne se lit jamais comme une coupure.
	if regime == Regime.SPUTTER and b < -0.55:
		l *= 0.28
	return Vector2(maxf(l, 0.05), maxf(w, 0.05))

## Le régime que doit rendre la flamme, déduit de l'état du moteur et de rien d'autre.
static func regime_for(state: int, leaving: bool) -> Regime:
	if leaving:
		return Regime.DYING
	match state:
		CortegeEngine.State.DAMAGED_1: return Regime.ROUGH
		CortegeEngine.State.DAMAGED_2: return Regime.SPUTTER
	return Regime.STEADY

# --- La pièce ------------------------------------------------------------------

func build() -> void:
	_add_layer("Halo", HALO_WIDTH, HALO_LENGTH, HALO_TINT, HALO_GLOW)
	_add_layer("Body", BODY_WIDTH, BODY_LENGTH, BODY_TINT, BODY_GLOW)
	_add_layer("Core", CORE_WIDTH, CORE_LENGTH, CORE_TINT, CORE_GLOW)

func _add_layer(nom: String, width: float, length: float, teinte: Color, glow: float) -> void:
	var mesh := MeshInstance3D.new()
	mesh.name = nom
	var box := BoxMesh.new()
	box.size = Vector3(_base_wide * width, _base_wide * width * 0.5, _base_len * length)
	mesh.mesh = box
	# Le panache part de la tuyère vers le HAUT de l'écran : la boîte est décalée d'une
	# demi-longueur pour que son ORIGINE soit la bouche, pas son centre.
	mesh.position.z = -_base_len * length * 0.5
	mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	# ⚠️ ADDITIF ET SANS ÉCRITURE DE PROFONDEUR : trois couches qui se découperaient l'une
	# l'autre donneraient trois silhouettes empilées au lieu d'un dégradé — et le panache
	# passerait derrière la coque au lieu de devant.
	mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	mat.no_depth_test = true
	mat.albedo_color = teinte
	mat.emission_enabled = true
	mat.emission = teinte
	mat.emission_energy_multiplier = glow
	mat.render_priority = 4
	mesh.material_override = mat
	add_child(mesh)
	_layers.append(mesh)
	_mats.append(mat)

## Un pas. `power` est ce qu'il reste de poussée (1 en régime, 0 quand la machine s'est tue) ;
## `surge` la surintensité d'une poussée annoncée.
func tick(t: float, regime: Regime, power: float, surge: float) -> void:
	var forme := shape_at(t, _phase, regime)
	for i in _layers.size():
		var mesh := _layers[i]
		var box := mesh.mesh as BoxMesh
		if box == null:
			continue
		var longueurs: Array[float] = [HALO_LENGTH, BODY_LENGTH, CORE_LENGTH]
		var largeurs: Array[float] = [HALO_WIDTH, BODY_WIDTH, CORE_WIDTH]
		var lueurs: Array[float] = [HALO_GLOW, BODY_GLOW, CORE_GLOW]
		var l: float = _base_len * longueurs[i] * forme.x * power * surge
		var w: float = _base_wide * largeurs[i] * forme.y * (1.0 + (surge - 1.0) * 0.4)
		box.size = Vector3(w, w * 0.5, maxf(l, 0.01))
		mesh.position.z = -maxf(l, 0.01) * 0.5
		_mats[i].emission_energy_multiplier = lueurs[i] * power * surge
		mesh.visible = power > 0.01
