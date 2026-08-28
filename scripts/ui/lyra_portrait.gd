class_name LyraPortrait
extends Control
## Lyra Vantella à l'écran — la voix du jeu, incarnée (`ADR-0035`).
##
## UN SEUL MODULE POUR TROIS ÉCRANS : l'accueil, le HUD et le briefing le montent. Le
## personnage ne doit pas exister en trois copies qui dérivent — c'est la même loi que
## « la collision et l'image lisent la même donnée ».
##
## ## Comment elle vit
##
## L'illustration est **une figure d'un seul tenant** (`docs/forge/characters/CHR-0004-lyra-figure.json`)
## qui respire et balance d'un bloc, par translation quantifiée au pixel ; seuls ses
## hologrammes vivent sur leur propre horloge. L'amplitude reste minuscule : une respiration
## qu'on REMARQUE se lit comme un défaut d'animation.
##
## ⚠️ ELLE A ÉTÉ UN PUZZLE, ET LE PUZZLE A PERDU. La première version montait dix calques
## (CHR-0001) pour un squelette 2D. Livrés séparément, ils n'avaient ni les mêmes proportions
## ni la même coiffure — et la frange, peinte sur la tête ET sur son propre calque, clignotait.
## Un générateur d'images réussit une figure entière et échoue sur des morceaux.
##
## Le portrait en buste du HUD (`lyra_buste/`) reste un groupe de tête co-enregistré
## (CHR-0002) : il n'a pas de bras à raccorder, et c'est le seul jeu qui ait une bouche.
##
## ⚠️ **LA DOUBLURE EST SIGNALÉE, ET ELLE DOIT L'ÊTRE.** Tant que les calques ne sont pas
## livrés, on dessine une silhouette de fil de fer qui ÉCRIT ce qu'elle attend. La spec §0.2
## interdit « tout asset temporaire non signalé » : une doublure muette finit par se faire
## prendre pour le rendu final, et l'on discute d'un cadrage sur un objet qui n'existe pas.
##
## ⚠️ **ZÉRO ALLOCATION DANS `_process`** (spec §31). Les pièces sont montées une fois ; la
## boucle n'écrit que des transformations et des visibilités.

## Les calques attendus, dans leur ORDRE DE PROFONDEUR — du fond vers l'avant. C'est cette
## liste qui fait foi, pas le contenu du dossier : un calque manquant doit se voir.
## Deux jeux la parcourent : la figure d'un tenant (`figure` + holos, pied-en-cap) et le
## groupe de tête du buste (`cheveux_arriere`, `tete`, `meches_avant`). Un dossier n'en a
## qu'un ; les noms de l'autre sont simplement absents.
const LAYER_ORDER: PackedStringArray = [
	"cheveux_arriere", "figure", "tete", "meches_avant", "holo_bracelet", "holo_sphere",
]
## Les pièces dont on cherche les expressions, par ordre de préférence : la première présente
## est la BASE. Ses variantes portent son nom suivi d'un suffixe (`figure_yeux_fermes`).
const BASES: PackedStringArray = ["figure", "tete"]
## Les pièces d'expression, superposées à la base et jamais visibles ensemble.
const MOUTH_SUFFIXES: PackedStringArray = ["_bouche_mi", "_bouche_ouverte"]
const EYE_SUFFIXES: PackedStringArray = ["_yeux_mi", "_yeux_fermes"]

## Respiration : le buste monte et descend de trois pixels en quatre secondes. ⚠️ Discrète à
## ce point-là parce qu'une respiration qu'on REMARQUE se lit comme un défaut d'animation.
const BREATH_PERIOD := 4.1
const BREATH_PIXELS := 1.6
## Balancement des cheveux. La masse arrière traîne, la queue traîne davantage : c'est ce
## retard qui fait qu'on croit à un poids.
const SWAY_PERIOD := 11.5
## ⚠️ 1,4° -> 0,45°, PARCE QUE LES CHEVEUX SCINTILLAIENT. Une rotation rééchantillonne la
## texture à chaque image : sur des mèches fines, les pixels rampent — et le post-traitement
## rétro, qui remonte les noirs et pose ses scanlines, transforme ce rampement en clignotement.
## « Le visage nickel mais les cheveux clignotent » (opérateur, en jeu, 2026-08-28). L'effet
## qu'on cherche est un poids, pas un mouvement.
##
## ⚠️ REMPLACÉ PAR UN DÉPLACEMENT : même à un demi-degré, une rotation rééchantillonne. Le
## balancement est désormais latéral et quantifié au pixel — le décalage temporel entre les
## mèches suffit à faire croire au poids.
const SWAY_PIXELS := 0.8
const SWAY_LAG: Dictionary[String, float] = {
	"figure": 0.30, "cheveux_arriere": 0.35, "meches_avant": 0.18,
}
## L'holo dérive sur sa propre horloge — il n'est pas de la chair, il ne respire pas.
const HOLO_PERIOD := 9.3
const HOLO_DEG := 5.0

## Clignement : rare, bref, et JAMAIS régulier. Un clignement métronomique est le signe le
## plus sûr qu'on regarde une machine.
const BLINK_MIN := 2.6
const BLINK_MAX := 6.4
const BLINK_TIME := 0.13

## Les trois bouches se choisissent à l'amplitude de la voix, pas aux phonèmes : à cette
## taille un jeu de visèmes complet ne se lit pas et coûte dix fois plus cher.
const MOUTH_HALF := 0.18
const MOUTH_OPEN := 0.46
## Une bouche ouverte TIENT au moins ce temps. ⚠️ MESURÉ AU TITRE LE 2026-08-28 (sonde sur le
## bus Voice) : le niveau suit les syllabes — 0,60 / 0,13 / 0,00 / 0,58 à 250 ms d'écart. Sans
## tenue, la bouche claque à chaque creux entre deux syllabes ; avec 90 ms, elle reste ouverte
## le temps d'un mot et se ferme dans les vrais silences (< −35 dB).
const MOUTH_HOLD := 0.09

## Où sont les calques. Vide = doublure, et elle le dit.
@export_dir var layer_dir: String = "res://assets/imported/ui/characters/lyra"
## Où poser chaque calque. ⚠️ SANS GRÉEMENT, LES PIÈCES S'EMPILENT PLEIN CADRE — ce qui n'est
## juste que pour un jeu de calques déjà co-enregistrés entre eux (le buste du HUD). Une
## planche pied-en-cap livrée par un générateur ne l'est PAS : il faut son gréement, sinon la
## tête fait les deux tiers du corps (`ADR-0035`, livraison du 2026-08-28).
@export var rig: CharacterRig = null
## Le socle holographique sous ses pieds. ⚠️ SANS LUI ELLE FLOTTE DANS LE CIEL — « on
## pourrait lui donner un sol style holo » (opérateur, 2026-08-28). Une figure pied-en-cap
## posée sur une nébuleuse n'a rien qui la porte : le regard cherche le sol et n'en trouve
## pas. Un disque suffit, et il raconte en plus la bonne chose — elle est une PROJECTION.
##
## Faux pour un cadrage buste : il n'y a pas de pieds à poser.
@export var pedestal: bool = false

var _pieces: Dictionary[String, TextureRect] = {}
## Les noms résolus des variantes (`<base><suffixe>`), fixés une fois au montage.
var _mouths: PackedStringArray = []
var _mouth_open_left: float = 0.0
var _eyes: PackedStringArray = []
var _rest: Dictionary[String, Vector2] = {}
var _age: float = 0.0
var _blink_clock: float = 0.0
var _blink_left: float = 0.0
var _speech: float = 0.0
var _mood: Color = Color("3fd9e8")
var _stand_in: Control = null
var _socle: Control = null
## L'emprise de la figure assemblée, et la transformation qui la ramène dans ce Control.
var _bounds: Rect2 = Rect2()
var _fit: float = 1.0
var _fit_origin: Vector2 = Vector2.ZERO

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	if rig != null:
		_bounds = rig.bounds()
	if pedestal:
		_build_pedestal()
	_build()
	_blink_clock = randf_range(BLINK_MIN, BLINK_MAX)
	resized.connect(_refit)
	_refit.call_deferred()

## Ramène l'emprise du gréement dans le rectangle de ce Control, en conservant les
## proportions. ⚠️ C'EST LE MÊME CALCUL POUR LES TROIS ÉCRANS : le gréement est écrit une
## fois, sur sa toile de référence, et chaque écran le cadre à sa taille. Sans ça, il faudrait
## trois jeux de chiffres — et trois occasions de les faire diverger.
func _refit() -> void:
	if size.y <= 1.0:
		return
	if rig == null:
		# ⚠️ SANS GRÉEMENT, LES PIÈCES SONT ANCRÉES PLEIN CADRE — mais elles ont quand même
		# besoin d'un pivot et d'une échelle. Les oublier ici laissait le buste du HUD tourner
		# autour de son coin haut-gauche, et respirer de douze pixels sur cent quatre-vingts.
		var reference := _reference_height()
		_fit = size.y / maxf(reference, 1.0)
		for piece: String in _pieces.keys():
			var rect: TextureRect = _pieces[piece]
			rect.pivot_offset = _pivot_for(piece, rect.size)
			_rest[piece] = rect.position
		return
	if _bounds.size.x <= 0.0 or _bounds.size.y <= 0.0:
		return
	_fit = minf(size.x / _bounds.size.x, size.y / _bounds.size.y)
	_fit_origin = (size - _bounds.size * _fit) * 0.5
	_place_pieces()

## La hauteur de la planche source, quand aucun gréement ne la déclare. Elle sert d'unité au
## souffle et au balancement : sans elle, la même amplitude serait invisible sur un buste de
## cent quatre-vingts pixels et énorme sur un pied-en-cap de neuf cents.
func _reference_height() -> float:
	for piece: String in _pieces.keys():
		var texture: Texture2D = _pieces[piece].texture
		if texture != null:
			return float(texture.get_height())
	return 1536.0

## Pose chaque calque là où le gréement le dit. Séparé de l'animation : celle-ci n'ajoute que
## de petits décalages par-dessus, elle ne recalcule jamais le placement.
func _place_pieces() -> void:
	if rig == null:
		return
	for piece: String in _pieces.keys():
		var pose := rig.pose_of(StringName(piece))
		if pose == null:
			continue
		var rect: TextureRect = _pieces[piece]
		var origin := rig.canvas * 0.5 * (1.0 - pose.scale) + pose.offset
		rect.position = _fit_origin + (origin - _bounds.position) * _fit
		rect.size = rig.canvas * pose.scale * _fit
		rect.pivot_offset = _pivot_for(piece, rect.size)
		_rest[piece] = rect.position

## Monte les calques livrés, ou la doublure. Rendre vrai quand la vraie planche est là —
## l'appelant peut ainsi refuser de publier une capture faite sur la doublure.
func has_artwork() -> bool:
	return not _pieces.is_empty()

func _build() -> void:
	for name in LAYER_ORDER:
		_add_piece(name)
	var base := ""
	for candidate in BASES:
		if _pieces.has(candidate):
			base = candidate
			break
	for suffix in MOUTH_SUFFIXES:
		_mouths.append(base + suffix)
		_add_piece(base + suffix, false)
	for suffix in EYE_SUFFIXES:
		_eyes.append(base + suffix)
		_add_piece(base + suffix, false)
	if _pieces.is_empty():
		_build_stand_in()

func _add_piece(piece: String, shown: bool = true) -> void:
	var path := "%s/%s.png" % [layer_dir, piece]
	if not ResourceLoader.exists(path):
		return
	var rect := TextureRect.new()
	rect.name = piece
	rect.texture = load(path) as Texture2D
	rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if rig == null:
		# Sans gréement : plein cadre. Valable pour un jeu de calques déjà co-enregistrés
		# entre eux — le buste du HUD, découpé d'un seul tenant.
		rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	else:
		rect.stretch_mode = TextureRect.STRETCH_SCALE
	rect.visible = shown
	add_child(rect)
	_pieces[piece] = rect
	_rest[piece] = rect.position

## Le disque holographique sur lequel elle se tient.
##
## ⚠️ DESSINÉ, PAS TEXTURÉ, et ajouté AVANT les calques pour passer dessous. Trois anneaux
## concentriques et une lueur : à cette échelle une texture ne rendrait rien de plus, et elle
## coûterait un asset de plus à commander, à détourer et à tracer en provenance.
func _build_pedestal() -> void:
	_socle = Control.new()
	_socle.name = "Socle"
	_socle.set_anchors_preset(Control.PRESET_FULL_RECT)
	_socle.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_socle)
	_socle.draw.connect(_draw_pedestal)
	_socle.resized.connect(_socle.queue_redraw)
	_socle.queue_redraw.call_deferred()

## ⚠️ IL RESPIRE AVEC ELLE, mais à contretemps. Un socle rigoureusement fixe sous une figure
## qui bouge se lit comme un décalque ; à contretemps, il se lit comme une projection qui la
## suit. C'est le même principe que le retard des cheveux.
func _draw_pedestal() -> void:
	if _socle.size.x <= 1.0 or _bounds.size.x <= 0.0:
		return
	# ⚠️ ACCROCHÉ À LA FIGURE, PAS AU CADRE. La première version prenait la taille du Control :
	# les anneaux débordaient de la colonne et leur centre tombait sous les pieds — elle
	# flottait toujours, avec un socle en plus. Ce qui porte une figure, c'est SA base.
	var bas := _fit_origin.y + _bounds.size.y * _fit
	# ⚠️ CENTRÉ SUR LE CORPS, PAS SUR L'EMPRISE. L'emprise inclut la sphère holographique, qui
	# déborde d'un tiers à gauche : le socle se posait donc à côté de ses pieds. Ce qui porte
	# une figure, c'est l'axe de son CORPS — et le corps, c'est le buste.
	var corps: LayerPose = null
	if rig != null:
		corps = rig.pose_of(&"figure")
		if corps == null:
			corps = rig.pose_of(&"buste")
	var largeur := _bounds.size.x * _fit
	var axe := _fit_origin.x + largeur * 0.5
	if corps != null:
		var origine := rig.canvas.x * 0.5 * (1.0 - corps.scale) + corps.offset.x
		axe = _fit_origin.x + (origine - _bounds.position.x) * _fit \
			+ rig.canvas.x * corps.scale * _fit * 0.5
		largeur = rig.canvas.x * corps.scale * _fit
	var centre := Vector2(axe, bas - largeur * 0.055)
	var pulse := 1.0 + sin(TAU * _age / 3.7) * 0.03
	for i in 3:
		var t := float(i) / 2.0
		var rayon := Vector2(largeur * (0.30 + 0.10 * t), largeur * (0.060 + 0.020 * t)) * pulse
		var teinte := Color(_mood.r, _mood.g, _mood.b, 0.42 - 0.12 * t)
		# L'ellipse se trace point à point : `draw_arc` ne sait faire qu'un cercle.
		var prev := centre + Vector2(rayon.x, 0.0)
		for k in range(1, 49):
			var a := TAU * float(k) / 48.0
			var p := centre + Vector2(cos(a) * rayon.x, sin(a) * rayon.y)
			_socle.draw_line(prev, p, teinte, 2.0)
			prev = p
	# Le halo au sol, qui donne l'assise.
	_socle.draw_circle(centre, largeur * 0.20, Color(_mood.r, _mood.g, _mood.b, 0.10))

## ⚠️ ELLE ÉCRIT CE QU'ELLE EST. Une doublure qui ressemble vaguement au résultat final se
## fait prendre pour lui, et l'on finit par juger un cadrage sur du vide (spec §0.2 :
## « aucun asset temporaire non signalé »).
func _build_stand_in() -> void:
	_stand_in = Control.new()
	_stand_in.name = "Doublure"
	_stand_in.set_anchors_preset(Control.PRESET_FULL_RECT)
	_stand_in.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_stand_in)
	_stand_in.draw.connect(_draw_stand_in)
	# ⚠️ SANS CES DEUX LIGNES ELLE NE SE DESSINE JAMAIS. Connecter `draw` n'appelle rien :
	# Godot n'émet le signal que sur une demande de redessin. La capture du 2026-08-28 a
	# montré une colonne vide avec sa seule étiquette — un signal branché ne prouve pas
	# qu'il est émis.
	_stand_in.resized.connect(_stand_in.queue_redraw)
	_stand_in.queue_redraw.call_deferred()

	var label := Label.new()
	label.text = "LYRA — DOUBLURE\nCALQUES ATTENDUS : CHR-0004"
	label.add_theme_font_size_override("font_size", 12)
	label.add_theme_color_override("font_color", Color(1.0, 0.72, 0.29, 0.85))
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	# ⚠️ `PRESET_CENTER_BOTTOM` ancre le HAUT du label sur le bas du parent : l'étiquette
	# tombait donc SOUS le panneau, hors de son cadre (vu en jeu le 2026-08-28). On la
	# remonte de sa propre hauteur.
	label.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	label.offset_top = -34.0
	label.offset_bottom = -2.0
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_stand_in.add_child(label)

## Une silhouette de fil de fer, aux proportions de la planche de référence : elle ne sert
## qu'à juger le CADRAGE et l'échelle, jamais l'apparence.
func _draw_stand_in() -> void:
	# ⚠️ LA TAILLE DE `_stand_in`, PAS CELLE DU PORTRAIT. La première version lisait `size`,
	# c'est-à-dire celle de `LyraPortrait` — encore nulle au moment où l'enfant se dessine.
	# Toutes les formes s'écrasaient sur un point, et la capture ne montrait que l'étiquette.
	var w := _stand_in.size.x
	var h := _stand_in.size.y
	if w <= 1.0 or h <= 1.0:
		return
	var c := Color(_mood.r, _mood.g, _mood.b, 0.45)
	var mid := w * 0.5
	# Tête, buste, jambes — les trois masses qui décident du cadrage.
	_stand_in.draw_circle(Vector2(mid, h * 0.10), w * 0.11, c, false, 2.0)
	_stand_in.draw_rect(Rect2(mid - w * 0.17, h * 0.19, w * 0.34, h * 0.34), c, false, 2.0)
	_stand_in.draw_rect(Rect2(mid - w * 0.13, h * 0.53, w * 0.26, h * 0.44), c, false, 2.0)
	# Les bras, dont le droit qui porte la sphère holo.
	_stand_in.draw_line(Vector2(mid - w * 0.17, h * 0.24), Vector2(mid - w * 0.34, h * 0.12), c, 2.0)
	_stand_in.draw_line(Vector2(mid + w * 0.17, h * 0.24), Vector2(mid + w * 0.36, h * 0.34), c, 2.0)
	_stand_in.draw_circle(Vector2(mid + w * 0.40, h * 0.34), w * 0.07, c, false, 2.0)
	# La colonne RÉSERVÉE, en pointillés : c'est elle qu'on juge tant que la planche n'est pas
	# là — sa largeur, sa hauteur, et ce qu'elle laisse au menu.
	var dash := Color(1.0, 0.72, 0.29, 0.35)
	var step := 14.0
	var y := 0.0
	while y < h:
		_stand_in.draw_line(Vector2(0.0, y), Vector2(0.0, minf(y + 7.0, h)), dash, 1.0)
		_stand_in.draw_line(Vector2(w, y), Vector2(w, minf(y + 7.0, h)), dash, 1.0)
		y += step

## Le point autour duquel la pièce tourne.
##
## ⚠️ SANS LUI, UNE ROTATION FAIT GLISSER AU LIEU DE BALANCER. Un `Control` tourne par défaut
## autour de son coin haut-gauche : sur une pièce de 1500 px de haut, 1,4° déplacent l'autre
## bout de **37 pixels**. Les cheveux ne balanceraient pas, ils patineraient — et le défaut ne
## se voit pas sur une capture fixe, seulement en jeu.
##
## Les cheveux pendent de la tête : leur pivot est en haut. L'holo flotte : il tourne autour
## de son centre. Le reste ne tourne pas, et son pivot n'a aucune importance.
func _pivot_for(piece: String, taille: Vector2) -> Vector2:
	if piece == "holo_bracelet" or piece == "holo_sphere":
		return taille * 0.5
	if SWAY_LAG.has(piece):
		return Vector2(taille.x * 0.5, taille.y * 0.18)
	return Vector2.ZERO

## Le régime : cyan au calme, rouge en alerte. C'est le CADRE qui le porte — à la taille du
## portrait en jeu, une expression seule ne se lit pas (`docs/KB/DAF/signaux.md`, loi 2).
func set_mood(colour: Color) -> void:
	_mood = colour
	if _stand_in != null:
		_stand_in.queue_redraw()
	if _socle != null:
		_socle.queue_redraw()

## L'amplitude de ce qu'elle dit, entre 0 et 1. Zéro quand elle se tait.
func set_speech_level(level: float) -> void:
	_speech = clampf(level, 0.0, 1.0)

func _process(delta: float) -> void:
	_age += delta
	if _socle != null:
		_socle.queue_redraw()
	_tick_blink(delta)
	_pose_pieces()
	_pose_mouth(delta)

func _tick_blink(delta: float) -> void:
	if _blink_left > 0.0:
		_blink_left -= delta
		return
	_blink_clock -= delta
	if _blink_clock <= 0.0:
		_blink_clock = randf_range(BLINK_MIN, BLINK_MAX)
		_blink_left = BLINK_TIME
	_set_visible(_eyes[1], false)
	_set_visible(_eyes[0], false)

func _pose_pieces() -> void:
	if _pieces.is_empty():
		return
	# ⚠️ LE SOUFFLE SUIT LE CADRAGE. Trois pixels sur un portrait de 900 px de haut se
	# devinent ; les mêmes trois pixels sur le buste du HUD, haut de 180, se voient comme un
	# tremblement. On l'exprime donc dans l'échelle de la figure, pas en pixels d'écran.
	var breath := sin(TAU * _age / BREATH_PERIOD) * BREATH_PIXELS * maxf(_fit, 0.05) * 4.0
	# ⚠️ ARRONDI AU PIXEL ENTIER, ET C'EST LA VRAIE CAUSE DU SCINTILLEMENT. Un déplacement
	# sous-pixel force Godot à rééchantillonner la texture À CHAQUE IMAGE : les mèches fines
	# rampent, et le post-traitement rétro — qui remonte les noirs et pose ses scanlines —
	# transforme ce rampement en clignotement. Mesuré sur fond noir, deux images à un dixième
	# de seconde : 18,7 % des pixels de la chevelure changeaient, et 15,2 % de ceux du CORPS —
	# preuve que ce n'était pas le balancement des cheveux mais la figure entière.
	#
	# Arrondi, le mouvement devient une marche d'un pixel toutes les quelques dixièmes de
	# seconde. C'est exactement ce qu'on veut : on cherche une respiration, pas un glissement.
	var pas := roundf(breath)
	for piece: String in _pieces.keys():
		var rect: TextureRect = _pieces[piece]
		# ⚠️ LE SOUFFLE EST UNE TRANSLATION DE GROUPE, JAMAIS DE PIÈCE. La première version
		# donnait 100 % de l'amplitude à la tête et 40 % aux cheveux : le visage GLISSAIT
		# de quelques pixels dans sa propre chevelure, à chaque respiration. « On voit le
		# visage se déplacer en hauteur » (opérateur, en jeu, 2026-08-28). Les pièces d'un
		# groupe ont été dessinées ensemble : les faire bouger séparément les déchire.
		rect.position = _rest[piece] + Vector2(0.0, roundf(pas * _breath_share(piece)))
		# Le balancement, lui, RESTE par pièce : c'est une rotation autour d'un pivot propre
		# à chaque mèche, et c'est le décalage entre elles qui fait croire à un poids.
		# ⚠️ LE BALANCEMENT AUSSI EST QUANTIFIÉ, et il a cessé d'être une rotation. Une
		# rotation rééchantillonne par construction, à n'importe quelle amplitude. Un
		# déplacement latéral d'un ou deux pixels entiers, décalé dans le temps d'une mèche à
		# l'autre, donne la même impression de poids sans toucher un seul pixel.
		var lag: float = SWAY_LAG.get(piece, 0.0)
		if lag > 0.0:
			rect.position.x += roundf(sin(TAU * (_age / SWAY_PERIOD - lag)) * SWAY_PIXELS
				* maxf(_fit, 0.05) * 4.0)
		elif piece.begins_with("holo_"):
			# L'holo, lui, a le droit de tourner : il n'a pas de mèches, et une projection
			# qui dérive est justement ce qu'on veut lire.
			rect.rotation = deg_to_rad(sin(TAU * _age / HOLO_PERIOD) * HOLO_DEG)
	if _blink_left > 0.0:
		_set_visible(_eyes[1], true)

## Quelle part du souffle revient à cette pièce. ⚠️ TOUTES LES PIÈCES D'UN MÊME GROUPE
## PARTAGENT LA MÊME : c'est ce qui les empêche de se déchirer entre elles. Le corps porte le
## souffle entier, la tête le suit presque, l'holo flotte et le suit à peine — il n'est pas
## de la chair.
func _breath_share(piece: String) -> float:
	# ⚠️ TOUT LE CORPS RESPIRE D'UN SEUL BLOC, et c'est le bout du chemin. Des parts
	# différentes (corps 1,00, tête 0,88) faisaient franchir leur pas d'arrondi à des instants
	# différents : la tête sautait d'un pixel sur un corps immobile, puis l'inverse. Mesuré,
	# la chevelure s'agitait encore de 14 % là où le corps était retombé à 0.
	#
	# La respiration ne se lit pas au décalage entre les pièces — elle se lit au mouvement
	# lui-même. Ce qui donne le poids, c'est le balancement latéral des mèches, et lui seul
	# reste décalé dans le temps.
	return 0.25 if piece.begins_with("holo_") else 1.0

func _pose_mouth(delta: float) -> void:
	if _pieces.is_empty():
		return
	# ⚠️ SANS BOUCHE INTERMÉDIAIRE, L'OUVERTE PREND LE RELAIS DÈS LE SEUIL BAS. La figure d'un
	# tenant (CHR-0004) n'a qu'une bouche greffée : exiger 0,46 la laissait fermée pendant les
	# trois quarts d'une réplique — « on a perdu le mouvement des lèvres » (opérateur).
	var has_mid := _pieces.has(_mouths[0])
	var open_from := MOUTH_OPEN if has_mid else MOUTH_HALF
	if _speech >= open_from:
		_mouth_open_left = MOUTH_HOLD
	else:
		_mouth_open_left -= delta
	_set_visible(_mouths[0], has_mid and _speech >= MOUTH_HALF and _speech < MOUTH_OPEN)
	_set_visible(_mouths[1], _mouth_open_left > 0.0)

func _set_visible(piece: String, shown: bool) -> void:
	var rect: TextureRect = _pieces.get(piece)
	if rect != null:
		rect.visible = shown

## Quelle bouche pour cette amplitude ? Pur, donc mesurable sans monter la scène — et c'est
## le seuillage, pas l'animation, qui décide si elle a l'air de parler.
static func mouth_for(level: float) -> int:
	if level >= MOUTH_OPEN:
		return 2
	return 1 if level >= MOUTH_HALF else 0
