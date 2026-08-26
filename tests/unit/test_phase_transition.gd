extends "res://tests/test_case.gd"
## `PhaseTransition` — le voile qui raccorde deux décors (lot 5 du plan inter-boss).
##
## ⚠️ CE QUE CE FICHIER GARDE, et pourquoi il existe. Le défaut qu'il prévient est passé
## une fois : la bascule de décor était un booléen sur une seule image, l'arc sortait en
## `code 0`, les quatre jalons du journal étaient présents — et la phase clignotait aux
## deux bouts. **Aucun test ne pouvait le voir**, parce qu'un `visible = false` n'émet rien.
##
## On ne teste donc pas « le voile s'affiche » (ça, c'est une capture regardée, ADR-0006)
## mais la seule chose qui décide de tout : **la fenêtre où le voile est plein**. Si elle
## est vide ou décalée, le changement de décor se fait à découvert et le clignotement
## revient, silencieusement.

const Transition := preload("res://scripts/vfx/phase_transition.gd")

const IN := 0.5
const HOLD := 0.1
const OUT := 0.8

func test_the_veil_is_absent_before_it_is_played() -> void:
	assert_almost_eq(Transition.veil_alpha(0.0, IN, HOLD, OUT), 0.0, 0.0001,
		"à l'instant zéro, aucun voile")
	assert_almost_eq(Transition.veil_alpha(-1.0, IN, HOLD, OUT), 0.0, 0.0001,
		"avant, non plus")

func test_the_veil_is_gone_again_at_the_end() -> void:
	var total := Transition.total_time(IN, HOLD, OUT)
	assert_almost_eq(Transition.veil_alpha(total, IN, HOLD, OUT), 0.0, 0.0001,
		"à la fin, l'écran est rendu")
	assert_almost_eq(Transition.veil_alpha(total + 5.0, IN, HOLD, OUT), 0.0, 0.0001,
		"et il le reste")

## LE test du fichier. Le décor change dans cette fenêtre et nulle part ailleurs.
func test_there_is_a_real_window_where_the_swap_is_invisible() -> void:
	assert_true(Transition.is_opaque(IN, IN, HOLD, OUT),
		"le voile est plein dès la fin de la fermeture")
	assert_true(Transition.is_opaque(IN + HOLD * 0.5, IN, HOLD, OUT),
		"et il le reste pendant le palier")
	assert_false(Transition.is_opaque(IN * 0.5, IN, HOLD, OUT),
		"pas avant : changer là laisserait voir l'ancien décor")
	assert_false(Transition.is_opaque(IN + HOLD + OUT * 0.5, IN, HOLD, OUT),
		"pas après : changer là laisserait voir le nouveau apparaître")

## Le palier n'est pas décoratif : c'est la marge qui absorbe un temps d'image long. À
## 12 images par seconde (83 ms), une image entière doit encore tomber dedans.
func test_the_hold_survives_a_long_frame() -> void:
	assert_true(Transition.HOLD >= 1.0 / 12.0,
		"le palier (%.3f s) tient une image à 12 Hz" % Transition.HOLD)

func test_the_veil_closes_then_opens_monotonically() -> void:
	var previous := 0.0
	for i in 50:
		var t := IN * float(i) / 50.0
		var a := Transition.veil_alpha(t, IN, HOLD, OUT)
		assert_true(a >= previous - 0.0001, "la fermeture ne recule jamais (t=%.3f)" % t)
		previous = a
	previous = 1.0
	for i in 50:
		var t := IN + HOLD + OUT * float(i) / 50.0
		var a := Transition.veil_alpha(t, IN, HOLD, OUT)
		assert_true(a <= previous + 0.0001, "l'ouverture ne remonte jamais (t=%.3f)" % t)
		previous = a

## On quitte sèchement, on découvre lentement — c'est le sens du geste, pas un réglage.
## Un fondu symétrique se lit comme un fondu de montage, pas comme une entrée dans un lieu.
func test_the_opening_is_slower_than_the_closing() -> void:
	assert_true(Transition.FADE_OUT > Transition.FADE_IN,
		"l'ouverture (%.2f s) dure plus que la fermeture (%.2f s)"
			% [Transition.FADE_OUT, Transition.FADE_IN])

## ⚠️ La règle de lisibilité la plus dure du projet : le cyan appartient au tir allié, le
## corail au tir ennemi. Un voile plein cadre dans l'une de ces deux teintes volerait leur
## sens à tous les projectiles de l'écran. Elle a déjà coûté une itération sur le bolide.
func test_the_veil_never_borrows_a_reserved_colour() -> void:
	var veil := Transition.VEIL_COLOR
	assert_true(veil.r < 0.1 and veil.g < 0.1 and veil.b < 0.1,
		"le voile est le noir de l'espace du jeu, pas une teinte")
	assert_true(veil.b >= veil.r,
		"et il reste froid — un voile qui tire au chaud vire au corail en montant")

## Une durée nulle n'est pas une division par zéro : c'est « déjà fermé ».
func test_degenerate_durations_do_not_divide_by_zero() -> void:
	assert_almost_eq(Transition.veil_alpha(0.01, 0.0, 0.0, 0.0), 0.0, 0.0001,
		"sans aucune durée, il n'y a pas de voile")
	assert_almost_eq(Transition.veil_alpha(0.01, 0.0, 1.0, 0.0), 1.0, 0.0001,
		"une fermeture nulle vaut déjà fermé")
	assert_almost_eq(Transition.total_time(-1.0, -1.0, -1.0), 0.0, 0.0001,
		"des durées négatives ne raccourcissent rien")

## ⚠️ CE TEST EXISTE PARCE QUE LE DÉFAUT EST ARRIVÉ. Le voile a été écrit à la couche 3 sur
## une lecture fausse de `graybox.tscn` — `layer = 5` y est celle des SCANLINES, pas celle du
## HUD. `FighterHUD` n'a aucune ligne `layer`, donc il vit à la valeur par défaut d'un
## `CanvasLayer` : **1**. Le voile passait au-dessus, et à voile plein la jauge, le score et
## la bannière s'éteignaient avec le décor.
##
## Deux bornes, et une seule valeur les satisfait :
##   > −1 pour passer AU-DESSUS de `RetroPost` (son `lift` de 1,25 remonte les noirs et
##        délaverait un voile posé dessous) ;
##   <  1 pour passer SOUS le HUD.
func test_the_veil_sits_under_the_hud_and_over_the_retro_pass() -> void:
	const HUD_DEFAULT_LAYER := 1   # CanvasLayer sans ligne `layer` dans fighter_hud.tscn
	const RETRO_POST_LAYER := -1   # graybox.tscn
	assert_true(Transition.LAYER < HUD_DEFAULT_LAYER,
		"le voile (%d) reste sous le HUD (%d) — sinon la jauge s'éteint avec le décor"
			% [Transition.LAYER, HUD_DEFAULT_LAYER])
	assert_true(Transition.LAYER > RETRO_POST_LAYER,
		"et au-dessus du post-traitement (%d), dont le lift délaverait le voile"
			% RETRO_POST_LAYER)
