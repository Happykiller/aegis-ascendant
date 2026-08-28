extends "res://tests/test_case.gd"
## Les repliques de Lyra Vantella (`ADR-0035`). Contenu de jeu, donc Resource typee avec son
## `validate()` — et ce fichier est ce qui rend la garde reelle.

const LineScript := preload("res://resources/data/dialogue_line.gd")
const ScriptScript := preload("res://resources/data/dialogue_script.gd")
const TITLE := "res://resources/dialogue/lyra_title.tres"

func _line(text: String) -> DialogueLine:
	var line: DialogueLine = LineScript.new()
	line.text = text
	return line

## Une replique muette n'est pas une replique.
func test_a_line_without_text_is_refused() -> void:
	assert_true(_line("").validate().size() > 0, "un texte vide est refuse")
	assert_true(_line("   \n  ").validate().size() > 0,
		"des espaces et des sauts de ligne non plus : `strip_edges` tranche")
	assert_eq(_line("Bienvenue, Pilote.").validate().size(), 0, "une vraie replique passe")

func test_a_line_refuses_a_negative_hold() -> void:
	var line := _line("Ok")
	line.hold = -0.5
	assert_true(line.validate().size() > 0, "une duree negative est refusee")

## ⚠️ DEUX SIGNAUX, PAS UN. A la taille du portrait en jeu, une expression seule ne se lit
## pas : c'est le CADRE qui porte le regime, et sa couleur vient de la replique. Si les deux
## regimes rendaient la meme couleur, l'alerte serait muette (`docs/KB/DAF/signaux.md`, loi 2).
func test_the_two_moods_do_not_share_a_colour() -> void:
	var calme := _line("Tout va bien")
	var alerte := _line("Danger")
	alerte.mood = LineScript.Mood.ALERT
	assert_true(calme.mood_colour() != alerte.mood_colour(),
		"calme (%s) et alerte (%s) se distinguent" % [calme.mood_colour(), alerte.mood_colour()])
	assert_almost_eq(alerte.mood_colour().r, Color("c93a31").r, 0.01,
		"l'alerte porte le rouge securite de la charte")
	assert_almost_eq(calme.mood_colour().b, Color("3fd9e8").b, 0.01,
		"le calme porte le cyan Helios")

## ⚠️ LA PAGINATION VIENT DE LA DONNEE, PAS DE L'AFFICHAGE. La maquette annonce
## « Message 1/4 » : laisser l'interface le compter, c'est le voir diverger le jour ou une
## replique s'ajoute.
func test_the_page_label_counts_from_one_and_never_lies() -> void:
	var script: DialogueScript = ScriptScript.new()
	script.id = &"test"
	script.lines = [_line("a"), _line("b"), _line("c")]
	assert_eq(script.page_label(0), "MESSAGE 1/3", "la premiere page compte a partir de 1")
	assert_eq(script.page_label(2), "MESSAGE 3/3", "la derniere aussi")
	# Hors bornes : l'entree du joueur peut avancer plus vite que l'etat.
	assert_eq(script.page_label(9), "MESSAGE 3/3", "au-dela, on reste sur la derniere")
	assert_eq(script.page_label(-1), "MESSAGE 1/3", "en deca, sur la premiere")

func test_reading_out_of_bounds_gives_nothing_and_does_not_crash() -> void:
	var script: DialogueScript = ScriptScript.new()
	script.id = &"test"
	script.lines = [_line("a")]
	assert_true(script.line_at(0) != null, "la replique existe")
	assert_true(script.line_at(1) == null, "au-dela, rien")
	assert_true(script.line_at(-1) == null, "en deca non plus")

func test_an_empty_script_is_refused() -> void:
	var script: DialogueScript = ScriptScript.new()
	assert_true(script.validate().size() >= 2, "sans id ni replique, deux reproches")
	script.id = &"test"
	script.lines = [_line("")]
	var errors := script.validate()
	assert_true(errors.size() > 0, "une replique fautive fait rougir le script entier")
	assert_true(String(errors[0]).contains("lines[0]"),
		"et l'erreur DIT laquelle : %s" % errors[0])

## Le script livre, celui que l'accueil monte vraiment.
func test_the_shipped_title_script_is_sound() -> void:
	var script: DialogueScript = load(TITLE)
	assert_true(script != null, "le script de l'accueil se charge")
	assert_eq(script.validate().size(), 0, "et il est valide : %s" % str(script.validate()))
	assert_eq(script.size(), 4, "quatre repliques, comme la maquette l'annonce")
	assert_eq(script.page_label(0), "MESSAGE 1/4", "la pastille de la maquette")
	# ⚠️ LES ACCENTS SONT UNE EXIGENCE, PAS UN DETAIL. Les deux polices du projet couvrent tout
	# le Latin-1 accentue (verifie le 2026-08-28 sur leurs tables cmap) : rien n'oblige a
	# ecrire un francais mutile, et une garde vaut mieux qu'une bonne intention.
	var accentue := false
	for i in script.size():
		if String(script.line_at(i).text).contains("é") \
				or String(script.line_at(i).text).contains("ê"):
			accentue = true
	assert_true(accentue, "elle parle un francais accentue")


# --- La voix : ce que le crete-metre du bus rend a la bouche --------------------

## ⚠️ LE PLANCHER DE BRUIT N'EST PAS UN SILENCE. Un `.ogg` encode ne descend jamais a
## -80 dB : un seuil trop bas ferait bavarder la bouche du portrait entre deux repliques,
## et le defaut se lirait comme une animation cassee, pas comme un reglage audio.
func test_the_voice_meter_treats_the_noise_floor_as_silence() -> void:
	assert_almost_eq(DialogueBox.level_from_db(-80.0), 0.0, 0.001, "un vrai silence")
	assert_almost_eq(DialogueBox.level_from_db(DialogueBox.VOICE_SILENCE_DB), 0.0, 0.001,
		"le seuil lui-meme compte comme silence")
	assert_true(DialogueBox.level_from_db(DialogueBox.VOICE_SILENCE_DB + 6.0) > 0.0,
		"six decibels au-dessus, elle parle")

func test_the_voice_meter_stays_between_zero_and_one() -> void:
	for step in 121:
		var db := -100.0 + float(step)
		var level := DialogueBox.level_from_db(db)
		assert_true(level >= 0.0 and level <= 1.0,
			"%.0f dB -> %.3f, hors bornes" % [db, level])
	assert_almost_eq(DialogueBox.level_from_db(0.0), 1.0, 0.001, "a 0 dB, saturation")
	assert_almost_eq(DialogueBox.level_from_db(12.0), 1.0, 0.001,
		"au-dela de 0 dB elle ne depasse pas — un bus peut ecreter")

## ⚠️ UN CRETE-METRE PEUT RENDRE -INF. Godot le fait sur un bus qui n'a jamais rien joue :
## sans cette garde, `inverse_lerp` propage un NaN jusque dans la bouche du portrait, et
## rien au journal ne le dit.
func test_the_voice_meter_survives_an_infinite_reading() -> void:
	assert_almost_eq(DialogueBox.level_from_db(-INF), 0.0, 0.001, "-inf : silence")
	assert_almost_eq(DialogueBox.level_from_db(NAN), 0.0, 0.001, "NaN : silence aussi")

## Le bus `Voice` existe et porte sa chaine comms : c'est elle qui la fait sortir de la radio
## du vaisseau. Un bus sans effets rendrait une voix de studio posee sur le jeu.
func test_the_voice_bus_exists_and_is_filtered() -> void:
	var bus := AudioServer.get_bus_index("Voice")
	assert_true(bus >= 0, "le bus Voice est declare dans default_bus_layout.tres")
	assert_true(AudioServer.get_bus_effect_count(bus) >= 3,
		"il porte sa chaine comms (%d effets)" % AudioServer.get_bus_effect_count(bus))
## ⚠️ TROIS SOURCES SUR LE MEME TEXTE : le `.tres` que le jeu affiche, la demande de voix que
## l'operateur enregistre, et le champ `voice_cue` qui les relie. Si elles divergent, on fait
## enregistrer une phrase que le jeu n'affiche pas — et personne ne s'en apercoit avant
## d'entendre le decalage en jeu. La demande DERIVE du `.tres` ; ce test le verifie.
func test_the_voice_request_asks_for_exactly_what_the_game_says() -> void:
	var raw := FileAccess.get_file_as_string("res://docs/forge/voice/VOX-0001-lyra-accueil.json")
	assert_false(raw.is_empty(), "la demande VOX-0001 se lit")
	var doc: Variant = JSON.parse_string(raw)
	assert_true(doc is Dictionary, "et c'est du JSON valide")
	var demandees: Array = (doc as Dictionary)["lines"]
	var script: DialogueScript = load(TITLE)
	assert_eq(demandees.size(), script.size(),
		"%d repliques commandees pour %d affichees" % [demandees.size(), script.size()])
	for i in script.size():
		var attendu: String = script.line_at(i).text
		var commande: String = String((demandees[i] as Dictionary)["text"])
		assert_eq(commande, attendu,
			"replique %d : la demande dit « %s », le jeu dit « %s »"
				% [i + 1, commande.replace("\n", " "), attendu.replace("\n", " ")])
## Toutes les repliques COMMANDEES pour le jeu, quelle que soit la demande qui les porte.
##
## ⚠️ ON BALAYE LE DOSSIER, ON NE LISTE PAS LES DEMANDES. Ce test nommait `VOX-0002` en dur et
## comparait son NOMBRE de repliques a celui du `.tres` : ajouter les trois bornes de mission
## par `VOX-0003` (2026-08-28) le faisait echouer alors que rien n'etait faux. Un garde qui se
## brise quand on ajoute du contenu conforme finit par etre desarme au lieu d'etre lu.
##
## L'appariement se fait par CLE, jamais par rang : c'est ainsi que le jeu les demande. Les
## repliques de l'accueil s'enchainent, elles, et n'ont pas de cle — le filtre sur
## `dialogue_key` les laisse a leur propre garde, juste au-dessus.
func _ingame_requests() -> Dictionary:
	var par_cle := {}
	var dossier := "res://docs/forge/voice/"
	for nom in DirAccess.get_files_at(dossier):
		if not nom.begins_with("VOX-") or not nom.ends_with(".json"):
			continue
		var raw := FileAccess.get_file_as_string(dossier + nom)
		assert_false(raw.is_empty(), "la demande %s se lit" % nom)
		var doc: Variant = JSON.parse_string(raw)
		assert_true(doc is Dictionary, "%s est du JSON valide" % nom)
		if not (doc is Dictionary):
			continue
		for entree in ((doc as Dictionary)["lines"] as Array):
			var cle := String((entree as Dictionary).get("dialogue_key", ""))
			if cle.is_empty():
				continue
			assert_false(par_cle.has(cle),
				"la cle `%s` est commandee deux fois (doublon dans %s)" % [cle, nom])
			par_cle[cle] = entree
	return par_cle
## ⚠️ TROIS SOURCES SUR LE MEME TEXTE, ici aussi : le `.tres`, la demande, et le `voice_cue`
## qui les relie. Si elles divergent, on fait enregistrer une phrase que le jeu n'affiche pas.
func test_the_ingame_voice_request_matches_the_game() -> void:
	var demandees := _ingame_requests()
	var script: DialogueScript = load("res://resources/dialogue/lyra_ingame.tres")
	assert_true(script.size() > 0, "le script de jeu porte des repliques")
	for i in script.size():
		var ligne := script.line_at(i)
		var cle := String(ligne.key)
		assert_true(demandees.has(cle),
			"la replique `%s` est affichee par le jeu mais commandee nulle part" % cle)
		if not demandees.has(cle):
			continue
		var entree: Dictionary = demandees[cle]
		assert_eq(String(entree["text"]), ligne.text,
			"replique `%s` : la demande et le jeu disent la meme chose" % cle)
		# ⚠️ LE REGIME AUSSI. Une replique enregistree sur le mauvais ton se remarque plus
		# qu'un mot faux : c'est le contraste calme/alerte qui porte l'information.
		var attendu := "ALERTE" if ligne.mood == DialogueLine.Mood.ALERT else "CALME"
		assert_eq(String(entree["mood"]), attendu,
			"replique `%s` : la direction d'acteur suit le regime du jeu" % cle)
		demandees.erase(cle)
	# Le sens inverse : une replique commandee que le jeu n'affiche plus, c'est une voix
	# qu'on fait enregistrer pour rien — et un fichier qui dort dans `imported/`.
	assert_eq(demandees.size(), 0,
		"repliques commandees mais absentes du jeu : %s" % ", ".join(demandees.keys()))
## ⚠️ LE PANNEAU DU HUD NE SAIT RIEN DE LA DUREE DE LA VOIX. `FighterHUD.say()` ne tient que
## `maxf(hold, 1.0) + LYRA_FADE` : contrairement a la bulle de l'accueil, il n'y a ici NI
## frappe du texte NI attente de l'audio. Un `hold` trop court coupe donc la replique au
## milieu d'un mot, et rien ne le signale — le fichier existe, la cue resout, le son part.
##
## Le cas s'est presente : `mission_start` et `docking` (VOX-0003) avaient recu les `hold`
## ESTIMES du plan de reprise (5,5-6,5 s) pour des voix de 6,10 et 6,72 s. Mesure d'abord,
## reglage ensuite.
func test_a_line_never_leaves_the_screen_while_it_is_still_speaking() -> void:
	const FADE := 0.45 # FighterHUD.LYRA_FADE — le panneau vit encore pendant son fondu
	var bank: AudioCueBank = load("res://resources/audio/sfx_bank.tres")
	var par_cue := bank.build_index()
	var script: DialogueScript = load("res://resources/dialogue/lyra_ingame.tres")
	var mesurees := 0
	for i in script.size():
		var ligne := script.line_at(i)
		if ligne.voice_cue == &"":
			continue
		var cue: AudioCueData = par_cue.get(ligne.voice_cue)
		assert_true(cue != null,
			"la cue `%s` de la replique `%s` est declaree dans la banque"
				% [ligne.voice_cue, ligne.key])
		if cue == null or cue.stream == null:
			continue
		mesurees += 1
		var duree := cue.stream.get_length()
		assert_true(ligne.hold + FADE >= duree,
			"replique `%s` : elle dure %.2f s et le panneau la tient %.2f s"
				% [ligne.key, duree, ligne.hold + FADE])
	assert_true(mesurees > 0, "des repliques ont bien ete mesurees (%d)" % mesurees)
## Le meme garde sur l'ACCUEIL, dont l'arithmetique est differente — et c'est bien pour ca
## qu'il lui faut son propre test. La bulle (`dialogue_box.gd`) ECRIT le texte avant de le
## tenir : le temps a l'ecran vaut `longueur / TYPE_SPEED + hold`, la frappe s'ajoutant au
## maintien. Un `hold` qui suffirait au HUD peut donc etre trop court ici, et l'inverse.
##
## Le cas s'est presente le 2026-08-28 : les deux repliques d'accueil reecrites pour l'ouverture
## en patrouille de routine ont ete synthetisees plus longues que les anciennes, et `title_4`
## quittait l'ecran 0,22 s avant la fin de sa propre voix. Rien ne l'aurait signale.
func test_a_title_line_never_leaves_the_bubble_while_it_is_still_speaking() -> void:
	const TYPE_SPEED := 45.0 # DialogueBox.TYPE_SPEED — caracteres par seconde
	var bank: AudioCueBank = load("res://resources/audio/sfx_bank.tres")
	var par_cue := bank.build_index()
	var script: DialogueScript = load(TITLE)
	for i in script.size():
		var ligne := script.line_at(i)
		if ligne.voice_cue == &"":
			continue
		var cue: AudioCueData = par_cue.get(ligne.voice_cue)
		if cue == null or cue.stream == null:
			continue
		var a_l_ecran := float(ligne.text.length()) / TYPE_SPEED + ligne.hold
		assert_true(a_l_ecran >= cue.stream.get_length(),
			"replique %d de l'accueil : elle dure %.2f s et la bulle la tient %.2f s"
				% [i + 1, cue.stream.get_length(), a_l_ecran])
