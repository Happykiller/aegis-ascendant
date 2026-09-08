class_name CortegeStern
extends Node3D
## La phase finale du niveau 2 : la poupe du Long Cortège et ses trois groupes propulsifs.
##
## ⚠️ CE N'EST PAS UN BOSS, ET LE CODE DOIT LE RENDRE VISIBLE. Aucune barre de vie, aucune vague,
## aucun moteur à arroser. Trois moteurs, neuf ou dix verrous, et une seule question posée au
## joueur : *lesquels tiennent encore ?* Le spectacle vient de ce qui part, pas de ce qui résiste.
##
## ⚠️ ET LE CORTÈGE N'EST PAS COULÉ, IL EST ÉCHOUÉ (décision D1 du plan, 2026-09-06). Le lore le
## dit depuis toujours — « il n'y a pas de bataille à gagner contre lui » — et cette phase ne le
## contredit pas : on lui prend sa propulsion, pas sa vie. Il ralentit, il dérive, il continue.
## Ce qu'on gagne ici est du TEMPS, pas une victoire.
##
## ⚠️ LES DEUX LATÉRAUX DANS N'IMPORTE QUEL ORDRE, LE CENTRAL EN DERNIER (spec §12 et §14). Ce
## n'est pas une contrainte de difficulté, c'est ce qui raconte la perte progressive de poussée :
## le central ne devient attaquable que lorsque l'énergie des deux autres converge vers lui.

## Les trois moteurs sont partis : le niveau peut se taire.
signal finished()
## Un moteur vient de quitter son berceau — le niveau le raconte (spec §13).
signal engine_lost(remaining: int)
## Les verrous du central viennent de s'ouvrir.
signal core_exposed()
## ⚠️ « LE VAISSEAU DOIT RÉAGIR » (spec §13). Un groupe de vingt mètres qui s'arrache sans que
## rien ne bouge à l'écran se lit comme un objet retiré d'une scène, pas comme une structure qui
## cède. La secousse est le seul retour que le joueur reçoive du VAISSEAU lui-même.
signal shockwave(trauma: float)

## Une pièce de la garnison est tombée. ⚠️ RELAYÉ ET NON RECÂBLÉ DEPUIS LE NIVEAU : la garnison
## naît dans `setup()`, c'est-à-dire après que le niveau a connecté ses signaux de poupe. Un
## branchement direct dessus s'écrirait forcément plus tard, dans une méthode qui n'existe pas.
signal turret_destroyed(turret: CortegeTurret)

## ⚠️ `APPROACH` N'EST PLUS UNE ANIMATION, C'EST UNE ATTENTE. La poupe existe et défile avec la
## coque bien avant d'être jouable ; ses verrous restent fermés tant que le vaisseau n'a pas fini
## de freiner. Sans cette attente, le joueur pourrait travailler un ancrage encore à mi-écran.
enum Phase { APPROACH, FIGHT, DONE }

var tuning: CortegeSternTuning = null
## Voir `--no-flames` : la bissection de perf de la phase.
var show_flames: bool = true

var _engines: Array[CortegeEngine] = []
var _phase: Phase = Phase.APPROACH
var _clock: float = 0.0
var _bullets: BulletManager = null
var _player: PlayerFighterController = null
var _vfx: VFXManager = null
var _core_open: bool = false
var _down: int = 0
## Le banc de vérification : un verrou tombe toutes les `n` secondes, tout seul.
##
## ⚠️ IL EXISTE PARCE QUE LA FIN DE LA PHASE EST AUTREMENT INVÉRIFIABLE. Elle demande dix
## verrous abattus à la main, répartis sur trente mètres, dans un ordre imposé ; le pilote de
## démonstration tire droit devant et n'atteint que la colonne centrale. Sans ce drapeau, la
## seule preuve que le niveau SE TERMINE serait une partie jouée par un humain — et c'est
## exactement le genre de preuve qu'on cesse de refaire. Même motif que `--citadel-state=` et
## `--spine-down=`. Les dégâts partent par le VRAI chemin : le `hit_callback` des balles.
var _auto_cut: float = -1.0
var _cut_clock: float = 0.0
## Le réglage du CORRIDOR, dont la poupe a besoin pour armer ses tourelles.
##
## ⚠️ DEUX RESSOURCES, ET C'EST VOULU. `CortegeSternTuning` dit ce qu'est cette phase ;
## `CortegeTuning` dit ce qu'est une tourelle du Long Cortège — points de vie, cadence, portée,
## score, aux trois échelles. Recopier ces valeurs dans la Resource de poupe aurait donné une
## tourelle de poupe qui dérive de celles du corridor sans qu'une ligne ne le dise.
## Ce qu'il reste d'énergie à la poupe, de `charge_floor` à 1,00.
##
## ⚠️ ELLE EST FIGÉE AVANT `build()`, ET C'EST LE CONTRAT. La recalculer en cours de phase ferait
## varier la vie d'un verrou pendant qu'on lui tire dessus — une cible dont la barre bouge sans
## qu'on l'ait touchée. Le niveau la pose une fois, au montage, et plus jamais.
var charge: float = 1.0

var corridor_tuning: CortegeTuning = null
var _garrison: CortegeSternGarrison = null

static func make(p_tuning: CortegeSternTuning) -> CortegeStern:
	var stern := CortegeStern.new()
	stern.tuning = p_tuning
	return stern

# --- La règle, pure et testable sans arbre -------------------------------------

## ⚠️ IL N'Y A PLUS D'« ARRIVÉE », ET C'ÉTAIT LE DÉFAUT. La poupe se montait à part et GLISSAIT
## dans le cadre pour venir se ranger — « il y a une espèce de plateforme qui amène les moteurs
## à la fin, alors que les moteurs doivent être rattachés au vaisseau » (opérateur, en
## regardant). Il avait raison : les trois groupes sont boulonnés à la carène depuis toujours,
## et une poupe qui se déplace toute seule dit le contraire de ce que le niveau raconte.
##
## Elle est désormais **enfant du décor**, à la station 508 : elle défile avec les 500 mètres qui
## la précèdent, à la même vitesse, parce qu'elle est le même vaisseau. Ce qui s'arrête à la fin,
## c'est le DÉFILEMENT — le chasseur se met en station devant les moteurs (`CortegeFlyby`
## freine en racine, comme le verrou de la Citadelle). Rien n'accoste.

## Le joueur est-il dans la colonne de poussée d'un moteur posé en `x` ?
##
## ⚠️ SEULE L'ABSCISSE COMPTE, ET C'EST VOULU. La tuyère pointe vers le haut de l'écran et le
## joueur est en dessous, sur la même verticale : le prolongement de l'axe passe par lui, quelle
## que soit sa hauteur. Ajouter une borne en `y` créerait un endroit sûr juste sous le moteur —
## exactement là où le joueur doit se poster pour travailler ses verrous, donc exactement là où
## la poussée doit le chasser.
static func in_thrust_column(player_x: float, engine_x: float, half: float) -> bool:
	return absf(player_x - engine_x) <= half

## Le central s'ouvre-t-il ? ⚠️ IL FAUT LES DEUX LATÉRAUX PARTIS, pas seulement abîmés : c'est
## la redirection d'énergie de la spec §14 qui l'expose, et elle n'a lieu qu'une fois les deux
## groupes détachés.
static func core_is_exposed(laterals_gone: int) -> bool:
	return laterals_gone >= 2

# --- La pièce ------------------------------------------------------------------

func setup(bullets: BulletManager, vfx: VFXManager,
		player: PlayerFighterController = null) -> void:
	_bullets = bullets
	_vfx = vfx
	_player = player
	for engine in _engines:
		engine.setup(bullets, vfx)
	# ⚠️ LA GARNISON SE MONTE ICI ET NON DANS `build()`, parce qu'une tourelle a besoin du
	# gestionnaire de balles pour exister utilement — et que `build()` est appelé avant que le
	# niveau n'ait passé le sien. Sans réglage de corridor, la poupe reste désarmée : c'est ce
	# qui permet aux bancs de la monter sans traîner toute la table du niveau.
	if corridor_tuning != null:
		_garrison = CortegeSternGarrison.make(corridor_tuning)
		add_child(_garrison)
		_garrison.build(bullets, player, vfx)
		_garrison.turret_destroyed.connect(_on_garrison_kill)

## Monte la poupe : son pont, puis les trois groupes.
##
## ⚠️ LE PONT EST ENCORE UNE BOÎTE, ET C'EST LE SEUL MORCEAU QUI LE RESTE. Les nacelles, les
## berceaux et les verrous sont les pièces réduites ; la structure qui les porte attend le
## LOT 6. Une dalle grise sous des pièces finies se voit — c'est dit plutôt que caché.
func build() -> void:
	_mount_hull()
	for side in [-1.0, 0.0, 1.0]:
		var engine := CortegeEngine.make(tuning, side)
		engine.name = "Engine_%s" % ("Center" if is_zero_approx(side) else
			("Right" if side > 0.0 else "Left"))
		engine.show_flame = show_flames
		engine.charge = charge
		engine.position = Vector3(tuning.slot_x(side), tuning.deck_y, 0.0)
		engine.build()
		engine.weakened.connect(_on_engine_weakened)
		engine.detaching.connect(_on_engine_detaching)
		engine.detached.connect(_on_engine_detached)
		add_child(engine)
		_engines.append(engine)

## Le vaisseau s'est immobilisé : les verrous des deux latéraux s'ouvrent.
func begin() -> void:
	if _phase != Phase.APPROACH:
		return
	_phase = Phase.FIGHT
	_open_laterals()
	print("[Poupe] le survol s'immobilise — les verrous des deux latéraux sont ouverts, %d désigné(s)"
		% designate_open())

## La carène de poupe (`BRIEF-0106`) : 2 514 triangles, sa jonction avec le cinquième tronçon
## exacte au dix-millionième de mètre.
const HULL_KIT := "res://assets/imported/models/backgrounds/stern_hull.glb"

## Monte la carène, ou la dalle grise si elle manque.
##
## ⚠️ LA DALLE RESTE COMME DOUBLURE, ET ELLE A SERVI QUATRE LOTS. Toute la phase a été conçue,
## jouée et testée dessus avant qu'une seule pièce finale n'entre — c'est la leçon de la cellule
## témoin, et c'est ce qui a permis de trouver en boîtes grises des défauts que les vraies pièces
## auraient masqués.
func _mount_hull() -> void:
	var packed: PackedScene = load(HULL_KIT) as PackedScene
	var carene := packed.instantiate() as Node3D if packed != null else null
	if carene == null:
		_greybox_deck()
		return
	carene.name = "Hull"
	add_child(carene)

func _greybox_deck() -> void:
	var pont := MeshInstance3D.new()
	pont.name = "SternDeck"
	var box := BoxMesh.new()
	box.size = Vector3(half_span() * 2.0 + 4.0, 1.60, tuning.cradle_size.z * 1.6)
	pont.mesh = box
	pont.position = Vector3(0.0, tuning.deck_y - 0.80, 0.0)
	pont.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.09, 0.09, 0.11)
	mat.metallic = 0.4
	mat.roughness = 0.6
	pont.material_override = mat
	add_child(pont)

func half_span() -> float:
	return tuning.half_span()

## La garnison, pour le niveau (score) et les bancs. `null` tant qu'aucun réglage de corridor
## n'a été passé.
## Monte l'escalade d'un cran. ⚠️ SANS GARNISON, ELLE NE FAIT RIEN ET NE PLANTE PAS : les bancs
## montent la poupe sans réglage de corridor, et la phase doit rester jouable désarmée.
func _escalate(tier: int) -> void:
	if _garrison == null:
		return
	_garrison.set_tier(tier, tuning.pressure_of(tier))

## Force un palier — bissection (`--stern-tier=N`). ⚠️ IL EXISTE PARCE QUE LE PALIER 3 ARRIVE
## APRÈS DEUX ARRACHEMENTS : le juger demandait deux minutes de tir par essai.
func force_tier(tier: int) -> void:
	_escalate(tier)

func garrison() -> CortegeSternGarrison:
	return _garrison

func _on_garrison_kill(turret: CortegeTurret) -> void:
	turret_destroyed.emit(turret)

func engines() -> Array[CortegeEngine]:
	return _engines

func phase() -> Phase:
	return _phase

func engines_down() -> int:
	return _down

func is_core_exposed() -> bool:
	return _core_open

## ⚠️ APPELÉ PAR LE NIVEAU, PAS PAR L'ARBRE. Même contrat que les autres pièces du Cortège : la
## poupe est pilotable sans scène, donc vérifiable sans jouer quatre minutes de survol.
func tick(delta: float, eye: Vector3) -> void:
	if _phase == Phase.DONE:
		return
	_clock += delta
	for engine in _engines:
		engine.tick(delta, global_position + engine.position, eye)
	if _garrison != null:
		_garrison.tick(delta, eye)
	_burn_the_player(delta)
	if _auto_cut > 0.0 and _phase == Phase.FIGHT:
		_cut_clock -= delta
		if _cut_clock <= 0.0:
			_cut_clock = _auto_cut
			_cut_one()

## ⚠️ ON APPELLE À CHAQUE IMAGE, ET C'EST LE BOUCLIER QUI CADENCE. `PlayerShield.take_hit()`
## accorde 1,2 s d'invulnérabilité après tout coup : appeler soixante fois par seconde ne fait
## donc PAS soixante fois plus de dégâts, ça fait une morsure toutes les 1,2 s tant qu'on reste
## dedans. C'est exactement le comportement voulu — traverser une colonne coûte une morsure, y
## rester en coûte une par seconde et quelques — mais il fallait le savoir : la première version
## passait un taux « par seconde » multiplié par `delta`, et le joueur perdait 0,77 point par
## souffle au lieu de 26.
func _burn_the_player(_delta: float) -> void:
	if _player == null or _phase != Phase.FIGHT:
		return
	var x := _player.plane_position.x
	for engine in _engines:
		if not engine.is_blasting():
			continue
		if in_thrust_column(x, tuning.slot_x(engine.side),
				tuning.danger_half_width(engine.is_central)):
			_player.take_contact_damage(tuning.surge_bite * charge)
			return

## Éteint tout ce que la poupe porte encore d'émissif — le blackout du §16.
##
## ⚠️ ELLE EXISTE PARCE QUE LE BLACKOUT NE COUVRAIT QUE LA COQUE. `CortegeRoot._blackout()` ne
## parcourt que les tronçons du survol : la poupe, montée à part, gardait ses veines allumées
## sur trois berceaux vides. Invisible en boîtes grises — il n'y restait presque rien d'allumé —
## et flagrant dès que les pièces réduites entrent, avec leurs 1 824 triangles émissifs.
##
## ⚠️ ET ÉTEINDRE L'ÉMISSION NE SUFFIT PAS, C'EST MESURÉ. La forge a compté sur la vignette
## « berceau vide, émissif coupé » : **4 480 → 3 605 pixels magenta, −20 % seulement**. L'albédo
## d'`AA_Emissive_Engine` EST le magenta de faction (0,694 / 0,047 / 0,332) contre 0,018 pour
## `AA_Hull` — quarante fois plus clair. Émission coupée, la surface reste PEINTE. C'est
## exactement pourquoi `CortegeSkin.extinguish()` touche les deux, et pourquoi on passe par elle
## plutôt que de baisser une énergie à la main.
##
## ⚠️ ET CHAQUE MAILLAGE REÇOIT SA COPIE. Les cinq `.glb` de poupe partagent leurs matériaux
## entre instances : éteindre le partagé éteindrait les trois moteurs d'un coup, y compris ceux
## qui tiennent encore. C'est le piège déjà payé sur les relais de la Citadelle, sur les puits et
## sur les cinq bulbes d'épine.
func blackout() -> int:
	var eteints := 0
	for mesh in _all_meshes(self):
		for i in mesh.get_surface_override_material_count():
			var base := mesh.get_active_material(i) as StandardMaterial3D
			if base == null or not base.emission_enabled:
				continue
			var mine: StandardMaterial3D = base.duplicate()
			CortegeSkin.extinguish(mine)
			mesh.set_surface_override_material(i, mine)
			eteints += 1
	return eteints

static func _all_meshes(node: Node, out: Array[MeshInstance3D] = []) -> Array[MeshInstance3D]:
	var mesh := node as MeshInstance3D
	if mesh != null:
		out.append(mesh)
	for child in node.get_children():
		_all_meshes(child, out)
	return out

## Ouvre `--stern-cut=<secondes>` : un verrou par intervalle, dans l'ordre où le jeu les ouvre.
func force_cut(interval: float) -> void:
	_auto_cut = maxf(interval, 0.05)
	_cut_clock = _auto_cut

func _cut_one() -> void:
	for engine in _engines:
		for anchor in engine.anchors():
			if not (anchor.is_alive() and anchor.is_vulnerable()):
				continue
			var cible := anchor.target()
			# ⚠️ IL ENTAME, IL NE TUE PAS — 55 % de la vie par coup. Un banc qui tuerait d'un
			# seul appel ne traverserait JAMAIS l'état ENDOMMAGÉ, donc ne prouverait rien de la
			# moitié visuelle du lot, et aucune capture ne pourrait le montrer.
			if cible != null and cible.hit_callback.is_valid():
				cible.hit_callback.call(tuning.anchor_health * 0.55)
			return

## Les deux latéraux s'ouvrent ensemble : le joueur choisit son ordre (spec §12).
func _open_laterals() -> void:
	for engine in _engines:
		engine.set_locked(engine.is_central)

## Allume la désignation sur tout verrou qu'on peut abattre à cet instant. Rend leur nombre.
##
## ⚠️ APPELÉE AUX DEUX SEULS MOMENTS OÙ LE JOUEUR APPREND QUELQUE CHOSE : l'ouverture des latéraux
## et celle du central. Une désignation posée ailleurs — à intervalle, à la moindre réplique —
## cesserait d'être un enseignement pour devenir un clignotant, et le joueur cesserait de la lire.
##
## ⚠️ ET ELLE NE DÉSIGNE QUE LE VULNÉRABLE. Marquer un verrou fermé apprendrait au joueur à tirer
## sur une pièce invincible : c'est exactement le contresens que Lyra essaie d'éviter.
func designate_open() -> int:
	var marques := 0
	for engine in _engines:
		for anchor in engine.anchors():
			if anchor.is_alive() and anchor.is_vulnerable():
				anchor.designate(tuning.designation_time)
				marques += 1
	return marques

func _on_engine_weakened(engine: CortegeEngine, lost: int) -> void:
	print("[Poupe] moteur %s affaibli — %d ancrage(s) perdu(s)"
		% [engine.name, lost])

## ⚠️ LYRA PARLE ICI, PAS QUATRE SECONDES PLUS TARD. « Un groupe décroché » se dit au moment où
## le verrou cède — c'est là que le joueur l'a mérité, et c'est là qu'il regarde. Câblée sur
## `detached`, elle attendait que le moteur ait FINI de dériver : au banc, les deux répliques
## des latéraux se suivaient à une seconde d'intervalle, alors qu'elles racontent deux moments
## distincts du niveau.
func _on_engine_detaching(engine: CortegeEngine) -> void:
	_down += 1
	print("[Poupe] arrachement du moteur %s" % engine.name)
	# ⚠️ ICI ET NON SUR `detached` : le palier doit monter à l'instant où le joueur a gagné
	# quelque chose, pas quatre secondes plus tard quand le moteur a fini de dériver. C'est la
	# même règle que la réplique de Lyra, et elle a déjà été payée une fois sur ce fichier.
	_escalate(_down)
	shockwave.emit(tuning.detach_trauma_central if engine.is_central else tuning.detach_trauma)
	engine_lost.emit(3 - _down)

## ⚠️ ET LE CENTRAL S'OUVRE ICI, SUR LE DÉPART ACHEVÉ — pas sur l'arrachement. La redirection
## d'énergie de la spec §14 suppose que les deux groupes ont VRAIMENT quitté le vaisseau ;
## l'avancer de quatre secondes ferait converger la poussée vers un moteur encore accroché.
func _on_engine_detached(_engine: CortegeEngine) -> void:
	# ⚠️ LE CENTRAL S'OUVRE ICI ET NULLE PART AILLEURS. Le compter sur « deux moteurs abîmés »
	# l'ouvrirait pendant que les latéraux tirent encore ; le compter sur un minuteur le
	# rendrait dépendant de la vitesse du joueur. Il s'ouvre quand les deux sont PARTIS.
	var lateraux := 0
	for engine in _engines:
		if not engine.is_central and engine.is_gone():
			lateraux += 1
	if not _core_open and core_is_exposed(lateraux):
		_core_open = true
		for engine in _engines:
			if engine.is_central:
				engine.set_locked(false)
				# ⚠️ ET SON EXTINCTION S'OUVRE AVEC (spec §15). Elle n'existe qu'ici : tant que
				# les latéraux poussent, le central n'a aucune raison de s'interrompre.
				engine.open_vent()
		print("[Poupe] l'énergie converge vers le moteur central — %d verrou(s) ouvert(s) et désigné(s)"
			% designate_open())
		# Le dernier palier : tout ce qui reste debout tire sans répit.
		_escalate(3)
		core_exposed.emit()
	var partis := 0
	for engine in _engines:
		if engine.is_gone():
			partis += 1
	if partis < _engines.size():
		return
	_phase = Phase.DONE
	print("[Poupe] les trois groupes ont quitté leurs berceaux — propulsion coupée")
	finished.emit()
