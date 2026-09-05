extends LevelRoot
## Le niveau 2 : le survol du Long Cortège, de la proue vers l'arrière.
##
## ⚠️ CE SCRIPT NE COPIE PAS CELUI DU NIVEAU 1, ET IL N'A PLUS À LE FAIRE. Il l'a d'abord évité
## pour la bonne raison — le niveau 2 n'a pas de phases, il a une traversée : c'est un autre
## jeu, donc un autre script — mais en l'évitant il perdait tout ce que ce fichier contenait
## d'universel, et le joueur l'a constaté en jouant : pas de voix, pas d'explosions d'ennemi,
## pas d'écrasement, pas de zones de debug. Ce n'était pas une série d'oublis, c'était une
## frontière manquante.
##
## Ce qui est universel vit désormais dans `LevelRoot` — le montage, le runtime de combat, la
## pause, le rapport, les calques de debug — et dans `CombatRuntime`, les lois. Ce fichier ne
## garde que ce qui appartient au Long Cortège : la traversée, ses trois mécaniques, son récit.

const TUNING := preload("res://resources/levels/long_cortege_tuning.tres")
const LYRA_LINES := preload("res://resources/dialogue/lyra_cortege.tres")
const BRIEFINGS := preload("res://resources/dialogue/cortege_briefings.tres")

## Ce que Lyra dit en entrant dans un troncon. ⚠️ PAR TRONÇON ET NON PAR ÉVÉNEMENT, parce que ce
## niveau n'a pas d'événements : rien ne change pendant trois minutes et demie, sauf ce que le
## joueur comprend. La progression du RÉCIT est donc la seule progression qu'il ait, et elle est
## portée par la seule chose qui avance — la coque sous lui.
const SECTION_LINES: Array[StringName] = [
	&"survey_start", &"hull_guns", &"bay_first", &"spine_seen", &"ambry",
]

## Combien de temps le rapport attend après la dernière réplique.
##
## ⚠️ IL ATTEND PARCE QUE LA DERNIÈRE RÉPLIQUE EST LA SEULE QUI COMPTE. C'est là que Lyra avoue
## avoir lu le dossier avant le décollage — la fracture de tout l'acte I. Enchaîner le rapport
## par-dessus la couperait au milieu, et le joueur ne saurait jamais ce qu'il vient de manquer.
## Mesuré, pas estimé : la voix dure 5,45 s et la réplique tient 6,5 s à l'écran.
const REPORT_DELAY := 7.5

@onready var _flyby: CortegeFlyby = $CortegeFlyby
@onready var _backdrop: Node3D = get_node_or_null("SpaceBackdrop") as Node3D
@onready var _hardpoints: CortegeHardpoints = $Hardpoints

## Le verrou de mi-parcours. ⚠️ IL N'EST PAS DANS LA SCÈNE, ET IL NE PEUT PAS L'ÊTRE : il se
## monte SOUS UN TRONÇON de la coque livrée, donc après `reveal()`, comme les points d'ancrage.
## Un nœud posé dans le `.tscn` resterait immobile pendant que le vaisseau défile sous lui.
var _citadel: CortegeCitadel = null
## La progression musicale due au TRONÇON seul, et la montée que le verrou y ajoute.
var _section_progress: float = 0.0
var _music_lift: float = 0.0
## Dernière valeur réellement poussée ; -1 tant que rien ne l'a été.
var _music_pushed: float = -1.0

## L'œil de la caméra de jeu. ⚠️ TENU PAR LE NIVEAU PARCE QUE LUI EST DANS L'ARBRE : les pièces
## posées hors du plan de jeu se touchent là où elles se PROJETTENT (`aim_point_of`), et ce
## point dépend d'où on les regarde. La caméra bouge — secousses, recadrages — donc on la relit
## à chaque image plutôt que de figer un décalage qui deviendrait faux au premier tremblement.
var _eye: Node3D = null

var _finished: bool = false
var _defeated: bool = false
## ⚠️ « PREMIÈRE FOIS » ET NON « À CHAQUE FOIS ». Sept ponts et cinq nœuds tombent dans une
## partie : répéter la même réplique à chacun la userait jusqu'au bruit de fond, et couvrirait
## la réplique de tronçon qui, elle, porte le récit.
var _said_bay_down: bool = false
var _said_node_down: bool = false
## ⚠️ AU PREMIER NŒUD VU, PAS AU PREMIER ABATTU. C'est la seule cible du jeu dont la récompense
## arrive quarante secondes plus tard : l'expliquer après coup ne sert plus à rien.
var _said_node_seen: bool = false

## Les fenêtres de tir, dessinées par-dessus les calques du socle. ⚠️ ELLES SONT PROPRES À CE
## NIVEAU : le socle sait montrer une hitbox, il ne peut pas savoir qu'une pièce n'est tirable
## que pendant la fenêtre où elle est à l'écran.
var _survey_zones: SurveyZones = null


func _ready() -> void:
	for error in TUNING.validate():
		push_error("[Cortege] réglage invalide : %s" % error)
	# Le survol lit ses paramètres du réglage : la vitesse commande la durée, donc les fenêtres
	# de tir, donc tout l'équilibrage. Rien n'est saisi deux fois.
	_flyby.scroll_speed = TUNING.scroll_speed
	_flyby.section_length = TUNING.section_length
	_flyby.section_count = TUNING.section_count
	_flyby.section_entered.connect(_on_section_entered)
	_flyby.survey_finished.connect(_on_survey_finished)
	# ⚠️ LE SOCLE D'ABORD : il monte les services, le runtime de combat, la pause et les calques
	# de debug. Il ne s'appelle pas tout seul, et c'est voulu — un `super._ready()` oublié ne se
	# voit pas à la lecture, une ligne manquante si.
	setup_level()
	# ⚠️ LE FOND CÈDE LA PLACE, il ne se superpose pas (`ADR-0027`).
	if _backdrop != null:
		_backdrop.visible = false
	_flyby.reveal(true)
	# ⚠️ APRÈS `reveal`, parce que `reveal` repose le décor : les points d'ancrage lisent leur
	# position dans le monde, et les monter avant reviendrait à les créer sur une coque qui n'est
	# pas encore là où elle sera.
	_eye = get_node_or_null("CameraDirector/Camera3D") as Node3D
	# ⚠️ SON ABSENCE NE PASSE PAS EN SILENCE. Sans œil, `aim_point_of` prend sa branche dégénérée
	# — caméra dans le plan — et rend la projection brute : toutes les pièces du niveau se
	# touchent alors ailleurs qu'où on les voit, le verrou s'immobilise 20 % trop loin, et tout
	# continue sans un mot. Le banc de test refuse explicitement cette valeur ; le runtime doit
	# la refuser aussi.
	if _eye == null:
		push_error("[Cortege] CameraDirector/Camera3D introuvable — les pièces de coque se toucheraient ailleurs qu'où on les voit")
	_hardpoints.build(_flyby.sections(), TUNING, _bullets, _player as PlayerFighterController,
		_vfx, _eye)
	_hardpoints.turret_destroyed.connect(_on_turret_destroyed)
	_hardpoints.bay_destroyed.connect(_on_bay_destroyed)
	_hardpoints.node_destroyed.connect(_on_node_destroyed)
	_hardpoints.section_weakened.connect(_on_section_weakened)
	_hardpoints.node_engaged.connect(_on_node_engaged)
	_mount_citadel()
	# ⚠️ UNE SECONDE ADOPTION, ET ELLE EST NÉCESSAIRE. Le socle a adopté les unités déjà dans
	# l'arbre — la réception de proue — mais `build()` vient de monter sept pools de ponts
	# d'envol, soixante-dix coques de plus. Le runtime adopte par le GROUPE : ce qui n'était pas
	# encore là ne peut pas avoir été adopté, et une unité non adoptée ne rapporte rien,
	# n'explose pas et ne fait aucun bruit.
	adopt_units()
	if _player != null and _player.has_signal("game_over"):
		_player.game_over.connect(_on_game_over)
	_push_music(0)
	# ⚠️ OUTIL DE VÉRIFICATION, PAS UN RACCOURCI DE JEU. `--cortege-from=<n>` démarre le survol
	# au tronçon n : sans lui, juger la section 3 demande d'attendre deux minutes de défilement,
	# et une capture automatisée n'y arrive pas du tout. Même esprit que `--skip-to-*` du
	# niveau 1 et que `--leviathan-phase=2`, dont l'absence avait coûté trois lancements.
	_survey_zones = SurveyZones.new()
	_survey_zones.name = "SurveyZones"
	add_child(_survey_zones)
	var args := OS.get_cmdline_user_args()
	for arg in args:
		# ⚠️ OUTIL DE VÉRIFICATION, PAS UN RACCOURCI DE JEU. Le critère du LOT 3 de la
		# citadelle est « une capture par état », et aucun des trois derniers n'est atteignable
		# sans un joueur : le pilote automatique tire droit devant. Même esprit que
		# `--leviathan-phase=2`. Les dégâts partent par le VRAI chemin — voir
		# `CortegeCitadel._apply_forced_state()`.
		if arg.begins_with("--citadel-state=") and _citadel != null:
			var niveau := arg.substr(16).to_int()
			_citadel.force_state(niveau)
			print("[Cortege] citadelle : état %d demandé au verrouillage" % niveau)
		if arg.begins_with("--cortege-from="):
			var section := maxi(arg.substr(15).to_int() - 1, 0)
			_flyby.skip_to_section(section)
			print("[Cortege] saut au tronçon %d" % (section + 1))
	# ⚠️ L'INDICATEUR EST DEMANDÉ PAR LE NIVEAU, PAS POSÉ PAR LE HUD. Le niveau 1 traverse six
	# lieux et n'a rien à jauger : une barre qui ne bouge pas y serait pire qu'aucune barre.
	if _hud != null and _hud.has_method("show_survey"):
		_hud.show_survey(TUNING.section_count)
	if _flyby.is_stand_in():
		print("[Cortege] coque DOUBLÉE — %s absent" % CortegeFlyby.DECOR_PATH.get_file())
	print("[Cortege] survol — %d sections, %.1f u/s, %.0f s attendues"
		% [TUNING.section_count, TUNING.scroll_speed, TUNING.level_duration()])

# --- Ce que valent les trois mécaniques ---------------------------------------
#
# ⚠️ LE SCORE EST DANS LE RÉGLAGE, PAS ICI. Ce sont des paramètres d'équilibrage : ils se
# recalent en jouant, et un chiffre écrit dans le script du niveau échapperait à `validate()`
# comme aux tests (spec §31).

## ⚠️ LA PIÈCE DIT CE QU'ELLE VAUT, LE NIVEAU NE LE DÉDUIT PAS. Deux échelles de tourelle
## partagent ce signal ; lire `TUNING.turret_score` ici aurait payé une pièce d'appoint au prix
## d'une installation, et un joueur qui rase une batterie de quatre aurait gagné plus qu'en
## abattant la tourelle lourde qu'elle garde — la hiérarchie inversée à l'endroit exact où elle
## se mesure.
func _on_turret_destroyed(turret: CortegeTurret) -> void:
	_game_state.add_score(turret.score())

## ⚠️ UN PONT ABATTU S'ANNONCE. Il coûte quinze cents points de vie, soit les deux tiers de ce
## qu'un joueur de référence peut placer dans sa fenêtre : sans un retour franc, l'effort le plus
## cher du niveau se solderait par un silence.
func _on_bay_destroyed(bay: CortegeBay) -> void:
	_game_state.add_score(TUNING.bay_score)
	print("[Cortege] pont d'envol détruit — tronçon %02d" % (bay.section + 1))
	if _hud != null and _hud.has_method("show_banner"):
		_hud.show_banner("PONT D'ENVOL DÉTRUIT", Color("d93d9c"), 1.8)
	if not _said_bay_down:
		_said_bay_down = true
		say(&"bay_down")

## Le premier nœud entre dans sa fenêtre. ⚠️ Les éclairs disent « tire ici » ; elle seule peut
## dire POURQUOI — et sans le pourquoi, la troisième mécanique du niveau n'existe pas.
func _on_node_engaged(_node: CortegeSpineNode) -> void:
	if _said_node_seen:
		return
	_said_node_seen = true
	say(&"node_seen")

func _on_node_destroyed(node: CortegeSpineNode) -> void:
	_game_state.add_score(TUNING.node_score)
	# ⚠️ ET LE VERROU FAIBLIT AVEC SON TRONÇON. Les points d'ancrage éteignent les vingt-et-une
	# batteries de coque ; les quatre tourelles de la citadelle ne sont pas dans leurs listes, et
	# ce sont précisément celles qui canardent le joueur pendant qu'il est IMMOBILE devant le
	# mur. Sans cette ligne, la récompense a un trou exactement là où elle se sent le plus.
	#
	# ⚠️ LE TRONÇON SE RECALCULE ICI ET NE S'ÉCOUTE PAS : `section_weakened` ne part que si une
	# tourelle LOURDE intacte a été touchée, ce qui n'a rien à voir avec la question posée.
	if _citadel != null:
		_citadel.weaken_section(
			CortegeSpineNode.weakened_section(node.section, _flyby.sections().size()))
	print("[Cortege] nœud d'épine %02d abattu" % (node.section + 1))
	if not _said_node_down:
		_said_node_down = true
		say(&"node_down")

## ⚠️ C'EST ICI QUE LA TROISIÈME MÉCANIQUE DEVIENT COMPRÉHENSIBLE, ou nulle part. La récompense
## d'un nœud arrive quarante secondes plus tard, sur un tronçon que le joueur n'a pas encore vu :
## rien à l'écran ne relie la cause à l'effet. Le niveau doit donc DIRE ce qui vient de se passer,
## au moment où ça se passe, et nommer sa conséquence.
func _on_section_weakened(section: int, turrets: int) -> void:
	print("[Cortege] tronçon %02d affaibli — %d tourelles" % [section + 1, turrets])
	if turrets <= 0:
		return
	if _hud != null and _hud.has_method("show_banner"):
		_hud.show_banner("TRONÇON %02d AFFAIBLI · %d TOURELLES" % [section + 1, turrets],
			Color("7a4de8"), 2.0)

## ⚠️ LA JAUGE SE MET À JOUR ICI ET NON DANS LE HUD. Le HUD ne connaît aucun niveau en
## particulier — c'est ce qui lui permet de servir les deux —, et le survol est la seule chose
## qui sache où l'on en est. Même partage que `show_boss` / `set_boss_health`.
func _process(_delta: float) -> void:
	# ⚠️ PERCUTER EST UNE LOI, ET ELLE MANQUAIT ICI. Le chasseur traverse les coques lâchées par
	# les ponts d'envol sans les écraser tant que personne ne l'appelle — et l'absence ne se
	# voit pas comme un défaut : elle se voit comme des ennemis qui « passent à travers ».
	if _runtime != null and not (_finished or _defeated):
		_runtime.crush()
	if not (_finished or _defeated):
		_tick_citadel(_delta)
	if _hud != null and not (_finished or _defeated):
		_hud.set_survey(_flyby.progress(), _flyby.current_section())
	_draw_debug_zones()

# --- LE VERROU DE MI-PARCOURS -------------------------------------------------

## Monte la Citadelle de Défense sous son tronçon.
##
## ⚠️ ELLE SE POSE PAR ARITHMÉTIQUE ET NON SUR UN MARQUEUR, et c'est une exception assumée. Les
## trente marqueurs de la coque sont figés — leur en ajouter un demande une reforge du `.glb`,
## et le lot 1 doit être jouable avant. La station est donc convertie ici en `z` local, par les
## deux fonctions pures de `CortegeCitadel` que les tests interrogent. ⚠️ LE LOT 2 REND CETTE
## POSE CADUQUE : quand la géométrie entrera dans `build_long_cortege.py`, elle portera son
## propre marqueur et cette conversion disparaîtra.
func _mount_citadel() -> void:
	# ⚠️ PAS DE CITADELLE SANS COQUE, ET C'EST LA MÊME RÈGLE QUE POUR LES TRENTE MARQUEURS. La
	# doublure procédurale pose ses tronçons à `HULL_Y = -8` et ne porte AUCUN marqueur : elle
	# n'a donc ni tourelle, ni pont, ni nœud. Un verrou posé dessus dessinerait ses boîtes huit
	# mètres sous la dalle — enterrées, invisibles — pendant que le mur solide, lui, arrêterait
	# le joueur à sa hauteur nominale. Un mur invisible qui bloque : le pire des deux.
	if _flyby.is_stand_in():
		print("[Cortege] citadelle NON MONTÉE — la coque est doublée, il n'y a pas de tronçon à équiper")
		return
	var sections := _flyby.sections()
	var index := CortegeCitadel.section_of(TUNING)
	if index < 0 or index >= sections.size():
		push_error("[Cortege] la citadelle vise le tronçon %d, la coque en porte %d"
			% [index + 1, sections.size()])
		return
	_citadel = CortegeCitadel.make(TUNING)
	_citadel.name = "Citadel"
	_citadel.setup(_bullets, _player as PlayerFighterController, _vfx)
	_citadel.position = Vector3(0.0, 0.0, CortegeCitadel.local_z_in_section(TUNING))
	sections[index].add_child(_citadel)
	_citadel.turret_destroyed.connect(_on_turret_destroyed)
	_citadel.relay_destroyed.connect(_on_citadel_part_destroyed)
	_citadel.core_destroyed.connect(_on_citadel_part_destroyed)
	print("[Cortege] citadelle armée — s = %.0f, tronçon %d, %.0f s de séquence attendues"
		% [TUNING.citadel_station, index + 1, TUNING.citadel_sequence_time()])

## Une pièce du verrou est tombée. ⚠️ LE SCORE VIENT DE LA PIÈCE, PAS DU NIVEAU : relais et
## noyau ne valent pas la même chose, et lire ici un seul chiffre les paierait au même prix.
func _on_citadel_part_destroyed(part: CitadelPart) -> void:
	_game_state.add_score(part.score)

## ⚠️ LE VERROU COMMANDE LA VITESSE, ET LE NIVEAU L'APPLIQUE. Laisser la citadelle écrire
## `scroll_speed` donnerait deux écrivains à la même valeur : le jour où l'un se tait, la vitesse
## reste là où l'autre l'a laissée — et un survol figé ne produit aucune erreur.
func _tick_citadel(delta: float) -> void:
	if _citadel == null:
		return
	var eye := _eye.global_position if is_instance_valid(_eye) else Vector3.ZERO
	_citadel.tick(delta, _flyby.travelled(), eye)
	_flyby.scroll_speed = TUNING.scroll_speed * _citadel.scroll_factor()
	# LOT 5 — la respiration (§18). Le verrou dit ce qu'il veut, le niveau l'écrit.
	_music_lift = _citadel.music_lift()
	_apply_music()

## Refait les obstacles du plan et les donne au chasseur.
##
## ⚠️ CE NIVEAU N'EN AVAIT AUCUN, et il n'en avait pas besoin : on survole, on ne heurte rien.
## La citadelle est la première chose du Long Cortège qui ARRÊTE un corps — donc la première
## raison de tenir cette liste ici. ⚠️ ET C'EST CELLE DU SOCLE, pas une seconde : `LevelRoot` la
## dessine déjà dans ses calques de debug, donc en tenir une à soi rendrait `--show-solids`
## aveugle au seul mur du niveau.
##
## ⚠️ EN IMAGE PHYSIQUE, ET AVANT RIEN D'AUTRE. Le chasseur se dégage CHEZ LUI, après son propre
## déplacement : la liste doit être à jour quand il la lit, et refaite à chaque image parce que
## le mur défile jusqu'à s'arrêter.
##
## ⚠️ LES UNITÉS NE SONT PAS VERSÉES ICI, ET C'EST UN MANQUE CONNU. `CombatRuntime.fill_solids()`
## rendrait solides les coques trop lourdes à écraser — le niveau 1 le fait, le niveau 2 ne l'a
## jamais fait. L'ajouter changerait la collision de tout le survol, ce qui n'appartient pas à ce
## lot : c'est au backlog, à juger en jouant.
func _physics_process(_delta: float) -> void:
	_solids.clear()
	if _citadel != null:
		_citadel.fill_solids(_solids)
	if _player != null and _player.solids != _solids:
		_player.solids = _solids

## Les zones de debug : celles du socle, plus les fenêtres de tir que lui seul ne peut pas
## connaître — elles viennent du réglage de ce niveau.
func _draw_debug_zones() -> void:
	draw_debug_zones()
	if _survey_zones != null:
		_survey_zones.draw(TUNING, debug_layers().y == 1, _hardpoints)


func _on_section_entered(index: int) -> void:
	print("[Cortege] SECTION %02d / %02d" % [index + 1, TUNING.section_count])
	_push_music(index)
	if _hud != null and _hud.has_method("show_banner"):
		_hud.show_banner("SECTION %02d" % (index + 1), Color("d93d9c"), 1.4)
	if index >= 0 and index < SECTION_LINES.size():
		say(SECTION_LINES[index])

func dialogue() -> DialogueScript:
	return LYRA_LINES

func briefings() -> BriefingBook:
	return BRIEFINGS

## Le nom de la « phase » courante, pour l'écran de pause. ⚠️ CE NIVEAU N'A PAS DE PHASES : ses
## briefings sont indexés par TRONÇON, et le nom se fabrique. Le contrat de `BriefingBook` reste
## le même — on cherche par NOM, jamais par rang (`ADR-0034`).
func phase_label() -> String:
	return "SECTION_%02d" % (_flyby.current_section() + 1)

## ⚠️ C'EST LE SEUL ÉCRAN OÙ LE JOUEUR A LE TEMPS DE LIRE, et ce niveau en a plus besoin que
## l'autre : il traverse UN SEUL objet pendant trois minutes et demie, et rien d'autre ne lui dit
## où il en est de la coque.
func _on_pause_toggled(is_paused: bool) -> void:
	if _hud != null:
		_hud.visible = not is_paused
	if is_paused and _pause != null:
		_pause.show_briefing(BRIEFINGS.find(StringName(phase_label())))


## ⚠️ LE CORTÈGE N'EST PAS ABATTU, IL CONTINUE SA ROUTE. C'est le premier adversaire du jeu que
## le joueur ne peut pas détruire, et c'est ce qui doit rester de lui (`docs/lore/NULL_CHOIR.md`).
## Ce qui se termine ici, c'est la traversée — pas lui.
func _on_survey_finished() -> void:
	if _finished or _defeated:
		return
	_finished = true
	# ⚠️ LA MUSIQUE DE VICTOIRE ATTEND QUE L'ÉCRAN SE VIDE, comme au niveau 1 : une résolution
	# qui tomberait par-dessus des tirs encore en vol se lirait comme une erreur de montage.
	if _runtime != null:
		_runtime.music.level_phase = MusicContext.LevelPhase.VICTORY
		_runtime.music.hostiles_clear = _bullets == null \
			or _bullets.team_count(BulletManager.Team.ENEMY) == 0
		_runtime.push_music()
	print("[Cortege] VICTORY — score %d" % _game_state.score)
	say(&"survey_end")
	_game_state.transition_to(GameStateScript.State.VICTORY)
	get_tree().create_timer(REPORT_DELAY).timeout.connect(
		show_report.bind(MissionReport.Outcome.VICTORY))

func _on_game_over() -> void:
	if _finished or _defeated:
		return
	_defeated = true
	print("[Cortege] all fighters lost — DEFEAT, score %d" % _game_state.score)
	_game_state.transition_to(GameStateScript.State.GAME_OVER)
	get_tree().create_timer(1.6).timeout.connect(
		show_report.bind(MissionReport.Outcome.DEFEAT))

## Pousse l'état musical du survol. ⚠️ IL N'Y EN AVAIT AUCUN, ET ÇA NE S'ENTENDAIT PAS COMME UN
## SILENCE. Le niveau 2 n'écrivait pas une ligne d'audio : il héritait donc de la piste que le
## niveau 1 laissait tourner en quittant son rapport de mission, et la jouait pendant les
## 208 secondes du survol. Le journal de la partie du 2026-08-30 le dit en creux — aucun
## `[Audio] music X -> Y` entre l'entrée dans le Cortège et sa fin. Un défaut qui ne produit
## aucune erreur et aucune absence de son est exactement celui qu'on ne cherche jamais.
##
## ⚠️ ET C'EST LE TRONÇON QUI FAIT MONTER LA MUSIQUE, PAS UNE HORLOGE. Le survol n'a ni vagues
## ni boss : sa seule progression est spatiale. La rendre en `wave_progress` réutilise la montée
## déjà réglée du niveau 1 (Launch → Skirmish → Fleet Battle) sans ajouter un état à
## `MusicContext.LevelPhase` — dont `test_music_director.gd` garde les valeurs une par une.
func _push_music(section: int) -> void:
	var derniere := maxi(TUNING.section_count - 1, 1)
	_section_progress = clampf(float(section) / float(derniere), 0.0, 1.0)
	_apply_music()

## Compose la progression SPATIALE du survol et la montée que le verrou demande.
##
## ⚠️ LA COMPOSITION EST MONOTONE, ET C'EST CE QUI LA REND SÛRE : à `lift = 0` on retrouve
## exactement la valeur du tronçon, à `lift = 1` on atteint 1,0. La musique ne peut donc jamais
## DESCENDRE sous ce que la position dans le vaisseau justifie — un verrou qui apaiserait la
## bande-son serait pire que pas de verrou.
##
## ⚠️ ET ON NE POUSSE QUE SI ÇA BOUGE. `_apply_music()` est appelée à chaque image ; le
## `MusicDirector` fait des fondus de plusieurs secondes et ne demande pas d'être réveillé
## soixante fois par seconde. Le seuil est plus fin que le plus serré des deux paliers de
## `MusicContext` (0,25 et 0,70), donc aucune transition ne peut être manquée.
func _apply_music() -> void:
	if _runtime == null:
		return
	var cible := _section_progress + (1.0 - _section_progress) * _music_lift
	if _music_pushed >= 0.0 and absf(cible - _music_pushed) < 0.01:
		return
	_music_pushed = cible
	_runtime.music.level_phase = MusicContext.LevelPhase.FIGHTER_WAVES
	_runtime.music.wave_progress = cible
	_runtime.push_music()
