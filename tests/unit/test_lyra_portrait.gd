extends "res://tests/test_case.gd"
## Le portrait de Lyra Vantella (`ADR-0035`). Un seul module pour trois ecrans : ce qui casse
## ici casse l'accueil, le HUD et le briefing d'un coup.

const PortraitScript := preload("res://scripts/ui/lyra_portrait.gd")
const BRIEF := "res://docs/forge/characters/CHR-0004-lyra-figure.json"
## Ce que la figure pied-en-cap exige, au minimum, du dossier `lyra/`.
const FIGURE_SET: PackedStringArray = ["figure", "holo_sphere"]

func _portrait(dir: String) -> LyraPortrait:
	var portrait := track(PortraitScript.new()) as LyraPortrait
	portrait.layer_dir = dir
	portrait._ready()
	return portrait

## ⚠️ TROIS BOUCHES, PAS DES VISEMES. Le seuillage EST le procede : c'est lui qui decide si
## elle a l'air de parler, pas l'animation. Une valeur qui sortirait des trois etats ferait
## disparaitre sa bouche.
func test_the_mouth_only_ever_takes_three_shapes() -> void:
	for step in 101:
		var level := float(step) / 100.0
		var mouth := PortraitScript.mouth_for(level)
		assert_true(mouth >= 0 and mouth <= 2,
			"niveau %.2f -> bouche %d, hors des trois etats" % [level, mouth])

func test_the_mouth_follows_the_voice_at_the_bornes() -> void:
	assert_eq(PortraitScript.mouth_for(0.0), 0, "silence : bouche fermee")
	assert_eq(PortraitScript.mouth_for(PortraitScript.MOUTH_HALF - 0.01), 0,
		"juste sous le premier seuil, toujours fermee")
	assert_eq(PortraitScript.mouth_for(PortraitScript.MOUTH_HALF), 1,
		"au premier seuil, entrouverte")
	assert_eq(PortraitScript.mouth_for(PortraitScript.MOUTH_OPEN), 2,
		"au second, ouverte")
	assert_eq(PortraitScript.mouth_for(1.0), 2, "saturation : ouverte, jamais au-dela")

## ⚠️ LES SEUILS DOIVENT SE SUIVRE. Inverses ou egaux, la bouche du milieu n'existerait
## jamais — et le defaut ne se verrait qu'a l'oeil, sur une animation qu'on croit subtile.
func test_the_two_thresholds_are_ordered() -> void:
	assert_true(PortraitScript.MOUTH_HALF > 0.0, "le premier seuil est au-dessus du silence")
	assert_true(PortraitScript.MOUTH_OPEN > PortraitScript.MOUTH_HALF,
		"et le second au-dessus du premier (%.2f > %.2f)"
			% [PortraitScript.MOUTH_OPEN, PortraitScript.MOUTH_HALF])

## Sans planche livree, il monte sa doublure et le DIT. La spec §0.2 interdit un asset
## temporaire non signale : c'est ce que `has_artwork()` permet a l'appelant de refuser.
func test_without_layers_it_falls_back_to_a_stand_in() -> void:
	var portrait := _portrait("res://assets/imported/ui/characters/personne")
	assert_false(portrait.has_artwork(), "aucun calque : pas de planche")
	assert_true(portrait.get_node_or_null("Doublure") != null,
		"mais une doublure, et elle porte son nom")

## Le regime se change sans planche : le cadre porte la couleur, pas le visage.
func test_the_mood_can_change_before_the_art_exists() -> void:
	var portrait := _portrait("res://assets/imported/ui/characters/personne")
	portrait.set_mood(Color("c93a31"))
	portrait.set_speech_level(2.0)
	portrait._process(0.016)
	assert_true(true, "aucun plantage sans planche, meme a un niveau hors bornes")

## ⚠️ DEUX SOURCES SUR LE MEME FAIT, ET CE DEPOT SAIT CE QUE CA COUTE. La liste des calques
## vit dans le code (ordre de profondeur) ET dans la demande d'asset (ce qu'on commande). Si
## elles divergent, on commande une planche que le jeu n'affichera pas — ou l'inverse, et un
## calque manquant ne se voit qu'a l'ecran.
func test_the_code_and_the_asset_request_ask_for_the_same_layers() -> void:
	var raw := FileAccess.get_file_as_string(BRIEF)
	assert_false(raw.is_empty(), "la demande CHR-0004 se lit")
	var brief: Variant = JSON.parse_string(raw)
	assert_true(brief is Dictionary, "et c'est du JSON valide")
	var demandes := {}
	for entry in (brief as Dictionary)["layers"]:
		demandes[String((entry as Dictionary)["name"])] = true
	for name in demandes.keys():
		assert_true(name in PortraitScript.LAYER_ORDER,
			"CHR-0004 commande `%s` — le code ne le monte jamais" % name)
	# ⚠️ Les holos ne sont PAS dans CHR-0004 (deja livres par CHR-0001, et conserves) : le
	# code doit quand meme les monter, sinon la sphere disparait de la paume.
	for name in FIGURE_SET:
		assert_true(name in PortraitScript.LAYER_ORDER,
			"le jeu pied-en-cap a besoin de `%s`" % name)
	# Et le greement du titre place exactement ce jeu-la : un calque de trop est un fantome.
	var rig: CharacterRig = load("res://resources/dialogue/lyra_rig.tres")
	assert_true(rig.validate().is_empty(), "le greement de Lyra est valide")
	assert_eq(rig.layers.size(), FIGURE_SET.size() + 1, "figure, sa bouche greffee, la sphere — le bracelet est retire")
	for name in FIGURE_SET:
		assert_true(rig.pose_of(StringName(name)) != null, "le greement place `%s`" % name)

## Les variantes d'expression portent le nom de la BASE : un dossier a `figure`, l'autre
## `tete`, et les deux doivent trouver leur bouche sans qu'on renomme un fichier.
func test_expression_names_follow_the_base() -> void:
	assert_eq(PortraitScript.BASES[0], "figure", "la figure d'un tenant passe avant la tete")
	assert_eq(PortraitScript.MOUTH_SUFFIXES.size(), 2, "deux bouches au-dessus de la base")
	assert_eq(PortraitScript.EYE_SUFFIXES.size(), 2, "deux paupieres au-dessus de la base")

## ⚠️ LA FIGURE D'UN TENANT A UNE BOUCHE, ET ELLE S'OUVRE. C'est ce qu'on a perdu en passant du
## puzzle (CHR-0001) a la figure (CHR-0004) — « on a perdu le mouvement des levres qu'on avait
## avant » (operateur, 2026-08-28). La variante est une greffe : ce test garantit que le module
## la trouve sous le nom de la base et la montre quand elle parle fort.
func test_the_shipped_figure_opens_her_mouth_when_she_speaks_loud() -> void:
	var portrait := track(PortraitScript.new()) as LyraPortrait
	portrait.rig = load("res://resources/dialogue/lyra_rig.tres")
	portrait._ready()
	assert_true(portrait.has_artwork(), "la figure livree se charge")
	var open: TextureRect = portrait.get_node_or_null("figure_bouche_ouverte")
	assert_true(open != null, "la variante `figure_bouche_ouverte` est montee")
	portrait.set_speech_level(0.0)
	portrait._process(0.016)
	assert_false(open.visible, "bouche fermee dans le silence")
	portrait.set_speech_level(1.0)
	portrait._process(0.016)
	assert_true(open.visible, "bouche ouverte quand elle parle fort")
	# Sans bouche `mi`, un niveau moyen ouvre aussi — sinon elle reste fermee entre les cretes.
	portrait.set_speech_level(0.3)
	portrait._process(0.5)
	assert_true(open.visible, "un niveau moyen l'ouvre quand il n'y a pas de bouche intermediaire")
	portrait.set_speech_level(0.0)
	portrait._process(0.016)
	assert_true(open.visible, "un creux de 16 ms ne la referme pas : elle tient %.0f ms" % (PortraitScript.MOUTH_HOLD * 1000.0))
	portrait._process(0.5)
	assert_false(open.visible, "un vrai silence la referme")
