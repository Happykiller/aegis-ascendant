extends "res://tests/test_case.gd"
## Placement du bandeau des coques, dans le bestiaire.
##
## POURQUOI CE TEST EXISTE — le bandeau est CENTRÉ et sa largeur dépend des
## DONNÉES : elle croît avec le nombre de fiches. À six coques il tenait au centre
## de l'écran ; en passant à neuf, son bord gauche est venu recouvrir « ARCHIVE
## TECHNIQUE » dans le bloc d'identité. La porte de qualité était verte des deux
## côtés de la régression, et elle ne pouvait pas être autre chose : ajouter une
## ligne de données avait cassé un écran.
##
## Même famille que `test_hud_layout.gd`, née du bandeau de boss qui chevauchait la
## jauge de bouclier — **un panneau centré dont la largeur dépend des données**. Et
## même méthode : on ne demande rien à l'arbre de scène (le runner tourne en mode
## `--script`), on refait le calcul de Godot à la main.
##
## ⚠️ CE TEST EST TOURNÉ VERS L'AVANT. Il ne vérifie pas seulement les neuf coques
## d'aujourd'hui : il vérifie aussi le roster COMPLET de la spec §11.1, familles
## non encore livrées comprises. Un commentaire qui dit « au-delà d'une douzaine il
## faudra un retour à la ligne » prévient ; ce test-ci attrape, et il dira à
## laquelle exactement la limite tombe.

const DatasheetScript := preload("res://scripts/ui/codex_datasheet.gd")
const CodexScreenScript := preload("res://scripts/ui/codex_screen.gd")
const LABEL_FONT := preload("res://assets/fonts/PressStart2P.ttf")

const SEPARATOR := "/"

## Bloc d'identité, tel que `_build_identity()` le pose : trois lignes ancrées à
## MARGIN, la plus basse à y = 94 sur une hauteur de police + 10.
const IDENTITY_TOP := 48.0
const IDENTITY_BOTTOM := 94.0 + 10.0 + 10.0
const IDENTITY_WIDTH := 480.0

func _viewport() -> Vector2:
	return Vector2(
		float(ProjectSettings.get_setting("display/window/size/viewport_width", 1920)),
		float(ProjectSettings.get_setting("display/window/size/viewport_height", 1080)))

## Largeur naturelle du bandeau pour une liste de noms — la somme des étiquettes,
## des séparateurs et des écarts, comme un `HBoxContainer` la calculerait.
func _strip_width(names: PackedStringArray) -> float:
	var width := 0.0
	var pieces := 0
	for i in names.size():
		if i > 0:
			width += LABEL_FONT.get_string_size(SEPARATOR, HORIZONTAL_ALIGNMENT_LEFT, -1,
				DatasheetScript.ROSTER_FONT_SIZE).x
			pieces += 1
		width += LABEL_FONT.get_string_size(names[i].to_upper(), HORIZONTAL_ALIGNMENT_LEFT, -1,
			DatasheetScript.ROSTER_FONT_SIZE).x
		pieces += 1
	return width + float(DatasheetScript.ROSTER_SEPARATION) * float(maxi(pieces - 1, 0))

## Rectangle du bandeau : sa BOÎTE, celle que le conteneur occupe quoi qu'il
## contienne. C'est elle qui peut mordre le bloc d'identité, pas le texte.
func _strip_rect(_names: PackedStringArray) -> Rect2:
	var screen := _viewport()
	return Rect2(screen.x * 0.5 - DatasheetScript.ROSTER_HALF_WIDTH, DatasheetScript.ROSTER_TOP,
		DatasheetScript.ROSTER_HALF_WIDTH * 2.0,
		DatasheetScript.ROSTER_BOTTOM - DatasheetScript.ROSTER_TOP)

func _identity_rect() -> Rect2:
	return Rect2(DatasheetScript.MARGIN, IDENTITY_TOP, IDENTITY_WIDTH,
		IDENTITY_BOTTOM - IDENTITY_TOP)

func _shipped_names() -> PackedStringArray:
	var names := PackedStringArray()
	for entry in CodexScreenScript.ROSTER:
		names.append(entry.display_name)
	return names

# --- Aujourd'hui ---------------------------------------------------------------

func test_the_shipped_roster_never_covers_the_identity_block() -> void:
	var names := _shipped_names()
	assert_true(names.size() >= 9, "le bestiaire a bien grandi (%d fiches)" % names.size())
	var strip := _strip_rect(names)
	assert_false(strip.intersects(_identity_rect()),
		"le bandeau (%s) dégage le bloc d'identité (%s)" % [strip, _identity_rect()])

func test_the_shipped_roster_stays_on_screen() -> void:
	var strip := _strip_rect(_shipped_names())
	assert_true(strip.position.x >= DatasheetScript.MARGIN,
		"le bandeau respecte la marge à gauche (x=%f)" % strip.position.x)
	assert_true(strip.end.x <= _viewport().x - DatasheetScript.MARGIN,
		"et à droite (fin=%f)" % strip.end.x)

## ⚠️ LE FILET S'EST DÉCLENCHÉ, LE 2026-08-25. À neuf coques le bandeau tenait sur une
## ligne ; la dixième — le Shield Carrier — demande **1 925 px pour 1 816 disponibles**.
## Ce test disait « une seule ligne » et il est tombé exactement quand il l'avait
## annoncé, en nommant la coque responsable. Il n'y avait rien à réparer : le bandeau
## est un `HFlowContainer` et sa boîte a **toujours** été dimensionnée pour deux lignes
## (`ROSTER_TOP` 122 → `ROSTER_BOTTOM` 182).
##
## Ce qui est vérifié ici est donc l'invariant RÉEL, et non plus le format d'hier : le
## bandeau tient-il dans **sa boîte** ? Le jour où deux lignes ne suffiront plus, c'est
## ce test-ci qui tombera — et ce jour-là il faudra vraiment décider quelque chose.
const ROSTER_MAX_LINES := 2

func _lines_needed(names: PackedStringArray) -> int:
	var available := DatasheetScript.ROSTER_HALF_WIDTH * 2.0
	return int(ceil(_strip_width(names) / available))

func test_the_shipped_roster_fits_in_the_two_lines_of_its_box() -> void:
	var names := _shipped_names()
	var lines := _lines_needed(names)
	assert_true(lines <= ROSTER_MAX_LINES,
		"les %d coques tiennent en %d ligne(s) sur %d (%.0f px pour %.0f)"
			% [names.size(), lines, ROSTER_MAX_LINES, _strip_width(names),
				DatasheetScript.ROSTER_HALF_WIDTH * 2.0])

## Et le constat daté, pour qu'on sache quand le format a basculé : le bandeau n'est
## PLUS sur une ligne. Ce n'est pas une régression, c'est un seuil franchi.
func test_the_roster_has_outgrown_a_single_line() -> void:
	assert_eq(_lines_needed(_shipped_names()), 2,
		"le bandeau est passé à deux lignes avec la dixième coque")

# --- Demain --------------------------------------------------------------------

## Les trois familles de la spec §11.1 qui restent à livrer. Le jour où elles
## arrivent, ce test tombe AVANT la capture — et il dit laquelle a fait déborder.
## ⚠️ « Shield Carrier » a QUITTÉ cette liste le 2026-08-25 : elle est livrée, et le
## bandeau doit désormais la porter pour de vrai — ce que le test du dessus mesure.
const REMAINING_FAMILIES := ["Null Bomber", "Frigate Turret"]

func _full_roster() -> PackedStringArray:
	var names := _shipped_names()
	for family in REMAINING_FAMILIES:
		names.append(family)
	return names

## ⚠️ CELUI-CI EST UN AVERTISSEMENT, PAS UNE RÉGRESSION. S'il tombe, rien n'est
## cassé aujourd'hui : il dit que la PROCHAINE famille ne rentrera plus, et qu'il
## faut passer le bandeau à deux lignes ou à une fenêtre glissante avant de la
## livrer. La largeur de l'écran, elle, ne croît pas.
func test_the_full_bestiary_of_the_spec_still_fits_in_the_banner() -> void:
	var names := _full_roster()
	var width := _strip_width(names)
	var per_line := DatasheetScript.ROSTER_HALF_WIDTH * 2.0
	# Le bandeau réserve la hauteur de DEUX lignes : c'est sa capacité réelle.
	assert_true(width <= per_line * 2.0,
		"les %d coques de la spec tiennent dans les deux lignes du bandeau "
			% names.size()
		+ "(%.0f px pour %.0f) — si ce test tombe, il faut une troisième ligne ou une "
			% [width, per_line * 2.0]
		+ "fenêtre glissante AVANT de livrer la famille suivante")

## Et le débordement d'hier, chiffré, pour que personne ne croie que le retour à la
## ligne était une précaution théorique : sur UNE seule ligne, la spec complète ne
## rentrait pas.
func test_a_single_line_would_not_have_been_enough() -> void:
	assert_true(_strip_width(_full_roster()) > DatasheetScript.ROSTER_HALF_WIDTH * 2.0,
		"la spec complète débordait bien d'une ligne — le retour à la ligne n'est pas décoratif")

# --- Le bandeau existe-t-il seulement ? ---------------------------------------

## ⚠️ CE TEST EXISTE PARCE QUE LES PRÉCÉDENTS NE SUFFISAIENT PAS. Ils calculent une
## géométrie à partir de constantes — ils disent où le bandeau SERAIT, jamais s'il
## est là. Le jour où le conteneur est passé de `HBoxContainer` à `HFlowContainer`,
## `set_roster()` a continué de le chercher avec un cast vers l'ancien type : le
## cast a rendu `null`, la fonction est sortie sans un mot, et le bandeau a
## intégralement disparu de l'écran. Les cinq tests de mise en page sont restés
## verts, puisqu'ils raisonnaient sur un objet qui n'était plus construit.
##
## Un test de géométrie ne remplace pas un test d'existence.
func _datasheet() -> CodexDatasheet:
	var sheet: CodexDatasheet = DatasheetScript.new()
	sheet._ready()
	return sheet

func test_the_roster_banner_is_actually_built() -> void:
	var sheet := track(_datasheet()) as CodexDatasheet
	var names := _shipped_names()
	sheet.set_roster(names)
	var strip := sheet._root().get_node_or_null("Roster") as Container
	assert_true(strip != null, "le bandeau existe dans l'arbre de la fiche")
	# Une étiquette par coque, plus un séparateur entre chaque.
	assert_eq(strip.get_child_count(), names.size() * 2 - 1,
		"il porte les %d noms et leurs séparateurs" % names.size())

func test_every_shipped_hull_appears_in_the_banner() -> void:
	var sheet := track(_datasheet()) as CodexDatasheet
	var names := _shipped_names()
	sheet.set_roster(names)
	var strip := sheet._root().get_node_or_null("Roster") as Container
	var shown := PackedStringArray()
	for child in strip.get_children():
		var label := child as Label
		if label != null and label.text != SEPARATOR:
			shown.append(label.text)
	for name in names:
		assert_true(shown.has(name.to_upper()), "%s est listée au bandeau" % name)


# --- La notice ------------------------------------------------------------------
#
# ⚠️ CE BLOC N'ÉTAIT GARDÉ PAR RIEN, et il s'est vu au premier dépassement : la fiche du
# Shield Carrier, écrite le 2026-08-25, débordait de son cadre — trois lignes de texte
# couraient SOUS le panneau, par-dessus le mobilier du bas. Un `Label` en autowrap ne
# tronque pas : il déborde, silencieusement, et seule la capture le montre.
#
# Même famille que le bandeau : un bloc dont la hauteur dépend des DONNÉES. La longueur
# d'une notice est une décision d'écriture, prise loin d'ici, par quelqu'un qui ne pense
# pas en pixels.

## Géométrie de `_build_notice()` : le label est posé à (18, 46) dans un panneau de
## 660 x 186, et occupe 624 x 128.
const NOTICE_WIDTH := DatasheetScript.LEFT_WIDTH - 36.0
const NOTICE_HEIGHT := 128.0
const NOTICE_FONT_SIZE := 10
const NOTICE_LINE_SPACING := 9

## Nombre de lignes qu'occupe un texte enveloppé sur `NOTICE_WIDTH`. PressStart2P est
## monospace : l'avance d'un glyphe suffit à connaître le nombre de colonnes, et
## l'enveloppement se refait mot à mot comme `AUTOWRAP_WORD_SMART` le ferait.
func _notice_lines(text: String) -> int:
	var advance := LABEL_FONT.get_string_size("M", HORIZONTAL_ALIGNMENT_LEFT, -1,
		NOTICE_FONT_SIZE).x
	var columns := int(floor(NOTICE_WIDTH / advance))
	var lines := 1
	var used := 0
	for word in text.split(" ", false):
		var length := word.length()
		if used > 0 and used + 1 + length > columns:
			lines += 1
			used = length
		else:
			used += length + (1 if used > 0 else 0)
	return lines

## ⚠️ L'INTERLIGNE SÉPARE, IL NE SUIT PAS. `n` lignes occupent `n * hauteur +
## (n - 1) * interligne` — une division simple par « hauteur + interligne » retire une
## ligne de trop et transforme le test en faux positif sur des fiches qui tiennent.
func _notice_capacity() -> int:
	var line := LABEL_FONT.get_height(NOTICE_FONT_SIZE)
	var lines := 1
	while (lines + 1) * line + float(lines) * float(NOTICE_LINE_SPACING) <= NOTICE_HEIGHT:
		lines += 1
	return lines

func test_every_notice_fits_in_its_frame() -> void:
	var capacity := _notice_capacity()
	assert_true(capacity >= 5, "le cadre tient au moins cinq lignes (%d)" % capacity)
	for entry in CodexScreenScript.ROSTER:
		var lines := _notice_lines(entry.notice)
		assert_true(lines <= capacity,
			"%s : %d lignes pour %d (%d caracteres)"
				% [entry.display_name, lines, capacity, entry.notice.length()])
