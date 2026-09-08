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
## ⚠️ ET C'EST LA PLUME DU CHASSEUR, PAS TROIS BOÎTES. « Faut travailler les jets d'éjection, on
## pourrait reprendre le travail qu'on a sur notre vaisseau le Specter-9 mais en plus grand et de
## teinte violette » (opérateur, 2026-09-08). La première version empilait trois boîtes additives
## — cœur, corps, halo — ce qui donnait un aplat rose à bord franc, sans gorge ni ventre. Le
## shader d'`ADR-0017` a les trois, plus ses disques de Mach, et c'est ce qui fait lire une
## TUYÈRE au lieu d'un rectangle lumineux.
##
## ⚠️ CE FICHIER GARDE LA RÈGLE, IL CHANGE LE RENDU. `shape_at()` et `regime_for()` ne bougent
## pas d'une décimale : ce sont elles qui portent la variation de la spec §5 et les quatre
## régimes, et elles sont testées. Ce qui change est ce qui les affiche.
##
## ⚠️ ET LA VARIATION EST DÉTERMINISTE. Deux sinusoïdes incommensurables, jamais un tirage au
## hasard : un survol se juge en comparant deux passages, et une flamme aléatoire rend deux
## captures incomparables. Même règle que le tremblement d'arrachement et que les arcs du nœud.

## Ce que la flamme rend selon ce que fait le moteur.
enum Regime { STEADY, ROUGH, SPUTTER, DYING }

## Le réglage de la plume — en MÈTRES DE JEU, pas en facteur d'échelle.
##
## ⚠️ IL VIT DANS UNE RESOURCE, comme tout paramètre de gameplay (spec §31). Le mettre ici en
## constantes rendrait la teinte et la taille des trois panaches inaccessibles à l'éditeur, et
## `flame_length` de `CortegeSternTuning` cesserait de commander quoi que ce soit.
const PLUME: PlumeTuning = preload("res://resources/vfx/plume_cortege.tres")

## Les deux fréquences de la respiration. ⚠️ INCOMMENSURABLES : un rapport simple (2, 3, 1,5)
## donne un motif qui se répète, et l'œil apprend un motif en quelques secondes.
const BREATH_A := 0.83
const BREATH_B := 2.17

var _plume: EnginePlume = null
var _pushed := -1.0
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

## ⚠️ LE PANACHE POUSSE VERS `-Z`, DONC VERS LE HAUT DE L'ÉCRAN. `EnginePlume.make` oriente sa
## géométrie selon l'axe qu'on lui donne : `Vector3.BACK` (le défaut, pour un chasseur qui va
## vers le haut et pousse vers le bas) l'enverrait vers le bas du cadre — c'est-à-dire dans la
## coque du Cortège.
func build() -> void:
	# `flame_length` reste le maître : c'est lui qui est dans la Resource du niveau, et c'est lui
	# qu'on tourne pour régler la phase. L'échelle rapporte simplement la plume à sa cote.
	_plume = EnginePlume.make(PLUME, _base_len / PLUME.length_full, Vector3.FORWARD)
	_plume.name = "Plume"
	add_child(_plume)

## Un pas. `power` est ce qu'il reste de poussée (1 en régime, 0 quand la machine s'est tue) ;
## `surge` la surintensité d'une poussée annoncée.
##
## ⚠️ LA POUSSÉE EST IMPOSÉE, JAMAIS LISSÉE. `set_throttle` amène la plume à sa cible avec la
## réponse d'un réacteur de chasseur (montée vive, extinction lente) : appliquée à une variation
## qui bat à 0,83 et 2,17 Hz, elle la moyennerait et le hoquet de l'intermittente disparaîtrait.
## C'est `shape_at()` qui décide de la forme, et elle décide seule.
##
## ⚠️ ET ON NE POUSSE QUE SI ÇA A BOUGÉ. Dix uniformes par image et par moteur pour un panache au
## régime constant, c'est ce que `EnginePlume` a été écrit pour éviter.
func tick(t: float, regime: Regime, power: float, surge: float) -> void:
	if _plume == null:
		return
	var forme := shape_at(t, _phase, regime)
	var voulue: float = forme.x * power * surge
	var ratio := clampf(voulue, 0.0, 1.0)
	_plume.visible = power > 0.02
	if absf(ratio - _pushed) > 0.004:
		_pushed = ratio
		_plume.snap_throttle(ratio)
