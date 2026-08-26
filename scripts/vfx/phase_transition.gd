class_name PhaseTransition
extends CanvasLayer
## Le raccord entre deux décors de l'arc : un voile se ferme, le décor change dessous,
## le voile se rouvre (`ADR-0027`, lot 5 du plan inter-boss).
##
## POURQUOI IL EXISTE. La bascule de décor était un booléen sur UNE SEULE IMAGE —
## `MoonFlyby.reveal()` et `_set_backdrop_hidden()` appelés ensemble. Playtest du
## 2026-08-26 : « un clignotement pour être dans la phase 2 avec le nouveau décor, puis
## clignotement à nouveau et on voit le boss de fin ». Le journal ne pouvait pas le voir :
## un `visible = false` n'émet aucune ligne, et la partie sortait en `code 0`.
##
## ⚠️ POURQUOI UN VOILE ET NON UN VRAI FONDU CROISÉ. Les deux décors sont des plans
## OPAQUES qui partagent `space_background.gdshader` (`depth_draw_never`). Rendre le shader
## transparent pour mélanger leurs opacités ferait passer AUSSI le ciel du survol dans la
## passe transparente — donc devant la lune et les rochers, qui sont opaques et dessinés
## avant. On échangerait un clignotement contre un décor à l'envers. Le voile ne touche ni
## au shader ni à l'ordre de rendu.
##
## Et il est honnête sur les deux instants où il sert : à la mort du mini-boss et au champ
## nettoyé, **l'écran est vide**. Le voile ne cache aucun combat.
##
## LA COULEUR N'EST PAS NOIRE, et ce n'est pas un détail : c'est le `deep_color` du fond
## spatial. Ni cyan ni corail — ils sont réservés au tir allié et au tir ennemi
## (`docs/design/bible/01-lisibilite.md`), et cette règle a déjà coûté une itération sur le
## bolide d'impact.
##
## Le voile passe SOUS le HUD (couche 3 contre 5) : la bannière de phase se lit par-dessus,
## et c'est voulu — l'écran s'éteint, le nom de la phase s'inscrit, le nouveau décor
## apparaît dessous.

## Émis quand le voile est complètement fermé : c'est LÀ que le décor se change, et nulle
## part ailleurs. Un changement fait plus tôt ou plus tard se voit.
signal midpoint
## Émis quand le voile est complètement rouvert et que la main est rendue à l'arc.
signal finished

## Le `deep_color` de `scenes/vfx/space_backdrop.tscn` — le noir de l'espace du jeu, pas
## un noir absolu qui trancherait sur lui.
const VEIL_COLOR := Color(0.01, 0.017, 0.038)

## La fermeture est plus VIVE que l'ouverture, et c'est le sens du geste : on quitte
## sèchement, on découvre lentement. Un fondu symétrique se lit comme un fondu de montage,
## pas comme une entrée dans un lieu.
const FADE_IN := 0.55
## Le palier à opacité pleine. Il n'est pas décoratif : c'est la marge dans laquelle le
## changement de décor tombe à coup sûr, quel que soit le temps d'image.
##
## ⚠️ 0,12 s ET NON 0,08 — corrigé le 2026-08-26, **défaut trouvé par son propre test**.
## À 0,08 s le palier était plus court qu'une image à 12 Hz (0,083 s) : une image longue
## pouvait sauter par-dessus, et le décor changeait alors à découvert. Le clignotement
## qu'on venait de supprimer serait revenu sur une machine lente, sans une ligne au
## journal. `test_the_hold_survives_a_long_frame` tient cette borne.
const HOLD := 0.12
const FADE_OUT := 0.75

## Couche du voile — **0, et il n'y a qu'une seule valeur possible**.
##
## ⚠️ CORRIGÉ DE 3 À 0 LE 2026-08-26, DÉFAUT VU EN CAPTURE. J'avais lu `layer = 5` dans
## `graybox.tscn` en croyant que c'était le HUD : c'est **Scanlines**. `FighterHUD` est un
## `CanvasLayer` **sans couche explicite**, donc à la valeur par défaut **1**. Le voile à 3
## passait au-dessus de lui : à voile plein, jauge, score et bannière disparaissaient —
## exactement ce que ce commentaire prétendait éviter. Une capture regardée l'a montré en
## un coup d'œil ; aucun test, aucune ligne de journal ne pouvait le dire.
##
## L'empilement réel de la scène, et ce qu'il impose :
##
##   RetroPost  −1   le post-traitement rétro
##   >>> VOILE   0   au-dessus de l'image traitée, SOUS l'interface
##   FighterHUD  1   (défaut d'un CanvasLayer — aucune ligne `layer` dans sa scène)
##   Scanlines   5
##
## Être au-dessus de `RetroPost` compte autant qu'être sous le HUD : le `lift` de 1,25 du
## post-traitement **remonte les noirs**, et un voile posé dessous en ressortirait délavé
## au lieu d'éteindre l'écran.
const LAYER := 0

var _rect: ColorRect
var _elapsed: float = 0.0
var _running: bool = false
var _midpoint_sent: bool = false


## Opacité du voile à un instant donné. **Pure et statique** : c'est la seule chose à
## vérifier ici, et elle se vérifie sans arbre de scène ni fenêtre — la même raison qui a
## sorti `EnemyReaction` du contrôleur d'ennemi.
##
## Trois régimes, dans l'ordre : la fermeture, le palier plein, l'ouverture. En dehors,
## zéro — le voile n'existe pas avant d'être joué et n'existe plus après.
static func veil_alpha(elapsed: float, fade_in: float, hold: float,
		fade_out: float) -> float:
	if elapsed <= 0.0:
		return 0.0
	if elapsed < fade_in:
		# Une durée de fermeture nulle veut dire « déjà fermé », pas une division par zéro.
		return 1.0 if fade_in <= 0.0 else clampf(elapsed / fade_in, 0.0, 1.0)
	if elapsed < fade_in + hold:
		return 1.0
	if fade_out <= 0.0:
		return 0.0
	return clampf(1.0 - (elapsed - fade_in - hold) / fade_out, 0.0, 1.0)

## Durée totale du raccord. Exposée parce que l'arc s'en sert pour raisonner sur le temps
## qu'il ajoute — la bible pose que la durée de l'arc est déjà à sa cible.
static func total_time(fade_in: float, hold: float, fade_out: float) -> float:
	return maxf(fade_in, 0.0) + maxf(hold, 0.0) + maxf(fade_out, 0.0)

## Le voile est-il fermé à cet instant ? C'est la fenêtre dans laquelle un changement de
## décor est invisible.
static func is_opaque(elapsed: float, fade_in: float, hold: float,
		fade_out: float) -> bool:
	return is_equal_approx(veil_alpha(elapsed, fade_in, hold, fade_out), 1.0)


func _ready() -> void:
	layer = LAYER
	_rect = ColorRect.new()
	_rect.name = "Veil"
	_rect.color = Color(VEIL_COLOR.r, VEIL_COLOR.g, VEIL_COLOR.b, 0.0)
	# Plein cadre quelle que soit la résolution, et transparent aux clics : le voile ne
	# doit jamais manger une entrée de l'interface qui vit au-dessus de lui.
	_rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_rect)
	visible = false
	set_process(false)

## Joue le raccord. Rejouer alors qu'il tourne le REPREND À ZÉRO plutôt que de l'ignorer :
## un arc qui enchaîne deux transitions doit voir la seconde, pas la perdre en silence.
func play() -> void:
	_elapsed = 0.0
	_midpoint_sent = false
	_running = true
	visible = true
	if _rect != null:
		_rect.color.a = 0.0
	set_process(true)

func _process(delta: float) -> void:
	if not _running:
		return
	_elapsed += delta
	var alpha := veil_alpha(_elapsed, FADE_IN, HOLD, FADE_OUT)
	# ⚠️ CEINTURE ET BRETELLES, et les deux sont nécessaires. Le palier donne la marge
	# NORMALE ; ceci garantit le cas PATHOLOGIQUE — une image si longue qu'elle saute
	# par-dessus le palier entier (une compilation de shader, un `alt-tab`). Sans cette
	# ligne, le décor changerait à découvert et le clignotement reviendrait exactement
	# là où on ne le teste jamais : sur la machine lente de quelqu'un d'autre.
	if not _midpoint_sent and _elapsed >= FADE_IN:
		alpha = 1.0
	if _rect != null:
		_rect.color.a = alpha
	# ⚠️ APRÈS avoir posé l'opacité : le décor se change sur une image où le voile est
	# DÉJÀ plein. L'émettre avant laisserait passer une image de l'ancien décor à 99 %.
	if not _midpoint_sent and _elapsed >= FADE_IN:
		_midpoint_sent = true
		midpoint.emit()
	if _elapsed >= total_time(FADE_IN, HOLD, FADE_OUT):
		_running = false
		visible = false
		set_process(false)
		finished.emit()
