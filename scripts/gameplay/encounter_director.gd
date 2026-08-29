class_name EncounterDirector
extends Node
## Il joue l'arc d'un niveau, temps par temps, et c'est tout ce qu'il fait.
##
## ⚠️ IL EXISTE PARCE QUE L'ARC ÉTAIT UNE CHAÎNE D'APPELS. Chaque temps du niveau 1 appelait le
## suivant depuis son propre événement de fin — `_on_wave_cleared` → `_start_mini_boss` →
## `_on_mini_boss_defeated` → `_start_asteroid_field` → … Six fonctions, six événements
## différents, et l'arc lui-même n'existait nulle part : il fallait le reconstituer de tête.
## Réordonner un temps, en insérer un, ou rejouer une séquence ailleurs demandait de relire les
## six.
##
## ⚠️ ET IL NE SAIT FAIRE QUE DEUX CHOSES TOUT SEUL — une vague, un boss. Le reste est déclaré
## `SCRIPTED` et rendu au niveau. C'est délibéré : prétendre mettre en données le survol de
## lune, le puits qui monte avant le boss final ou l'appontage de la Citadelle aurait produit
## une Resource à trente champs dont vingt-huit valent zéro. Ce qui devient de la donnée, c'est
## l'ORDRE et l'IDENTITÉ des temps ; le sur-mesure reste du code, mais **à sa place dans l'arc**.

## Le temps commence. Le niveau règle ce qui lui appartient — musique, bornes, décor — avant
## que quoi que ce soit ne s'affiche. ⚠️ Émis AVANT le voile : c'est le seul instant où le niveau
## peut encore préparer sans qu'on le voie.
signal beat_entering(beat: LevelBeat)
## Le voile est plein (ou il n'y en a pas) : c'est ICI que le décor bascule.
signal beat_revealed(beat: LevelBeat)
## Un temps `SCRIPTED` a la main. Le niveau le joue et rappelle `advance()`.
signal beat_scripted(beat: LevelBeat)
## L'arc est allé au bout.
signal arc_finished()

var _arc: LevelArc = null
var _level: LevelRoot = null
var _index: int = -1
## Le temps courant est-il déjà en train de se refermer ? ⚠️ Une vague nettoyée pendant qu'un
## boss tombe — ça arrive — appellerait `advance()` deux fois et sauterait un temps entier.
var _advancing: bool = false

func bind(level: LevelRoot, arc: LevelArc) -> void:
	_level = level
	_arc = arc
	for error in arc.validate():
		push_error("[Arc] %s" % error)

## Le temps courant, ou `null` avant le début et après la fin.
func current() -> LevelBeat:
	return _arc.at(_index) if _arc != null else null

func current_id() -> StringName:
	var beat := current()
	return beat.id if beat != null else &""

func index() -> int:
	return _index

## Ouvre l'arc sur son premier temps.
func begin() -> void:
	_index = -1
	advance()

## Saute directement à un temps, par son NOM. ⚠️ POUR LA VÉRIFICATION, PAS POUR LE JEU : les
## drapeaux `--skip-to-*` existent parce qu'attendre trois minutes pour juger un boss coûte trois
## lancements. Un arc joué normalement ne saute jamais.
##
## ⚠️ ET IL POSE LE RANG JUSTE AVANT, puis avance : c'est ce qui garantit qu'un saut passe par
## exactement le même chemin d'entrée qu'un enchaînement normal — musique, bornes, décor,
## bannière. Un saut qui monterait le temps « à la main » finirait par diverger de l'arc, et
## c'est précisément ce qu'on découvre le jour où l'on teste avec un raccourci ce qui est cassé
## sans lui.
func jump_to(id: StringName) -> bool:
	var target := _arc.index_of(id) if _arc != null else -1
	if target < 0:
		push_error("[Arc] temps `%s` introuvable — saut ignoré" % id)
		return false
	_index = target - 1
	advance()
	return true

## Passe au temps suivant. ⚠️ APPELÉ PAR LE DIRECTEUR pour les temps qu'il sait clore lui-même,
## et PAR LE NIVEAU pour les temps `SCRIPTED` — c'est le seul contrat entre les deux.
func advance() -> void:
	if _arc == null:
		return
	_advancing = false
	_index += 1
	var beat := current()
	if beat == null:
		arc_finished.emit()
		return
	if _level != null and _level.should_skip_beat(beat):
		print("[Arc] %02d/%02d — %s SAUTE" % [_index + 1, _arc.size(), beat.id])
		call_deferred("advance")
		return
	print("[Arc] %02d/%02d — %s" % [_index + 1, _arc.size(), beat.id])
	beat_entering.emit(beat)
	if beat.veiled and _level != null:
		_level.veil(_reveal.bind(beat), _start.bind(beat))
	else:
		_reveal(beat)
		_start(beat)

## Ce qui se voit à l'entrée : le décor bascule, puis on annonce.
##
## ⚠️ LE DÉCOR AVANT L'ANNONCE, et sous le voile quand il y en a un. La bannière vit sur le HUD,
## au-dessus du voile : elle s'inscrit donc sur l'écran éteint, et le joueur la lit avant de
## découvrir ce qu'elle annonce.
func _reveal(beat: LevelBeat) -> void:
	beat_revealed.emit(beat)
	if _level == null:
		return
	if beat.banner_text != "":
		_level.banner(beat.banner_text, beat.banner_colour, beat.banner_hold)
	if beat.lyra_key != &"":
		_level.say(beat.lyra_key)

func _start(beat: LevelBeat) -> void:
	match beat.kind:
		LevelBeat.Kind.WAVE:
			_start_wave(beat)
		LevelBeat.Kind.BOSS:
			_start_boss(beat)
		_:
			beat_scripted.emit(beat)

## ⚠️ LE SEMEUR EST CHERCHÉ PAR NOM DANS LA SCÈNE DU NIVEAU, et son absence est DITE. Un arc qui
## s'arrête sur un nœud manquant se lit comme un boss qui ne vient pas, et se cherche au mauvais
## endroit — on enchaîne plutôt que de rester bloqué.
func _start_wave(beat: LevelBeat) -> void:
	var spawner := _level.get_node_or_null(String(beat.spawner_name)) as WaveSpawner
	if spawner == null:
		push_error("[Arc] temps `%s` : semeur `%s` introuvable — on enchaîne"
			% [beat.id, beat.spawner_name])
		call_deferred("advance")
		return
	if not spawner.wave_cleared.is_connected(_on_beat_over):
		spawner.wave_cleared.connect(_on_beat_over)
	spawner.begin()

func _start_boss(beat: LevelBeat) -> void:
	var stage := _make_stage(beat.boss_stage)
	stage.name = "BossStage_%s" % beat.id
	_level.add_child(stage)
	_level.dress_boss_stage(stage, beat)
	stage.score_value = beat.boss_score
	stage.show_boss_before_begin = beat.boss_banner_first
	stage.defeated.connect(_on_boss_defeated.bind(stage))
	stage.mount(beat.boss_scene, _level)

## ⚠️ PAR NOM ET NON PAR `PackedScene` : une mise en scène est du CODE, pas du contenu. La
## déclarer par un chemin de script dans une Resource mettrait un fichier `.gd` à la merci d'un
## renommage silencieux — et le niveau tomberait au montage du boss, pas à l'import.
func _make_stage(kind: StringName) -> BossStage:
	match kind:
		&"harvester":
			return HarvesterStage.new()
		&"leviathan":
			return LeviathanStage.new()
		_:
			return BossStage.new()

func _on_boss_defeated(world_position: Vector3, stage: BossStage) -> void:
	# ⚠️ LE NIVEAU PEUT PRENDRE LA MAIN. La finale Helios dure 1,8 s ; enchaîner l'appontage
	# par-dessus l'escamoterait, et c'est le seul moment spectaculaire du niveau.
	if _level != null and _level.on_boss_defeated(current(), stage, world_position):
		return
	_on_beat_over()

## Le temps se referme. ⚠️ UNE SEULE FOIS : deux sources peuvent l'annoncer dans la même image.
func _on_beat_over() -> void:
	if _advancing:
		return
	_advancing = true
	advance()
