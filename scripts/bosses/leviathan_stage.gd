class_name LeviathanStage
extends BossStage
## La mise en scène du Pale Leviathan — vingt-deux fonctions qui vivaient dans le script du
## niveau 1, et qui n'avaient rien à y faire.
##
## ⚠️ CE BOSS EST LE PLUS COÛTEUX DU JEU À METTRE EN SCÈNE, et c'est ce qui rendait la
## frontière si nécessaire. Il ne se contente pas de mourir : il ouvre un LIEU. La plongée
## masque le fond spatial, monte une arène, change les bornes du plan de vol, déplace la
## caméra, met le chasseur en pilotage automatique, puis défait tout cela — trois fois. Écrire
## cet enchaînement dans le script du couloir d'Ossane, c'était le rendre impossible à rejouer
## ailleurs et impossible à lire dans son ensemble.
##
## ⚠️ ET C'EST LUI QUI DÉCIDE DE CE QUE MONTRE LA JAUGE, pas le niveau. Elle a montré
## `structure_ratio()` — « ce qu'on peut casser MAINTENANT » — et se remplissait donc à nouveau
## à chaque bascule : le joueur voyait armure 100→0, noyau 100→0, armure 100→0… « phase 1 phase
## 2 phase 1 phase 2, j'ai l'impression que c'était en boucle » (playtest du 2026-08-25). Il
## décrivait exactement ce que le HUD lui affichait. C'est `fight_ratio()` qui monte.

## ⚠️ LE PORTAIL DU FOND SPATIAL, INJECTÉ ET NON APPELÉ EN DUR. La plongée doit masquer le fond
## — mais le fond appartient au NIVEAU, qui s'en sert aussi pour son survol de lune. Deux
## propriétaires du même état finissent par se contredire ; ici la mise en scène DEMANDE, et le
## niveau décide. C'est la forme d'injection que recommande Godot pour ce cas précis.
## Bannières du Pale Leviathan — les couleurs exactes du design (`docs/design/
## BOSS_PALE_LEVIATHAN.md`) : ivoire pour la structure qui cède, magenta pour la gueule.
const _BANNER_IVORY := Color("e8e2cf")
const _BANNER_MAGENTA := Color("d93d9c")
## Libellés des pastilles de sous-cibles, par phase. Numérotés parce que les pièces sont
## identiques (contrairement aux appendices nommés du Harvester) et abrégés pour tenir
## dans la jauge : P = plaque, N = nœud gravitique, E = épine. Le bandeau de phase donne
## le contexte, le numéro distingue la cible.
## Les quatre plaques de la phase 1. ⚠️ Il n'y a plus de rangée pour les nœuds ni pour
## les épines : ADR-0020 les a retirés du combat, ils ne sont plus que des pièces qui
## tombent. Une pastille sans cible derrière est un mensonge de HUD.
const _LEVIATHAN_PLATE_LABELS: PackedStringArray = ["P 1", "P 2", "P 3", "P 4"]

## Libellés de la rangée quand elle porte les VERROUS et non les plaques. Quatre lettres : la
## colonne est étroite, et « VERROU 1 » y déborderait.
## ⚠️ `var` et non `const` : un `PackedStringArray(...)` n'est pas une expression constante en
## GDScript, et le script entier refuse alors de se charger.
static var _LEVIATHAN_LOCK_LABELS := PackedStringArray(["V1", "V2", "V3", "V4", "V5", "V6"])

var backdrop_gate: Callable = Callable()

var _combat: LeviathanCombat = null
var _core_interior: CoreInterior = null
var _regen_plates: int = 0
var _core_marker_age: float = 0.0
## Où le chasseur était AVANT d'entrer. ⚠️ Relevé avant le pilotage automatique : celui-ci
## l'emmène à la gueule, et le relever une fois dedans mémoriserait le point d'aspiration —
## il ressortirait ailleurs qu'il n'est entré.
var _outside_plane: Vector2 = Vector2.ZERO

## La pose d'entrée et l'échelle du Leviathan. ⚠️ Il naît HORS du plan de vol, à Y = 12 : sa
## descente est la phase d'approche, et l'y poser après son montage le ferait clignoter au
## centre le temps d'une image.
const ENTRY_PLANE := Vector2(0.0, 12.0)
const BOSS_SCALE := 0.75

func _configure(mounted: BossController) -> void:
	mounted.plane_position = ENTRY_PLANE
	mounted.scale = Vector3.ONE * BOSS_SCALE

func _wire(mounted: BossController) -> void:
	_wire_combat(mounted)

## ⚠️ LA CHAMBRE EST UN OBSTACLE, ET ELLE N'EXISTE QUE PENDANT LA PLONGÉE. Le carter du
## réacteur est plus large que le flux qu'il abrite ; sans lui le chasseur passait dedans.
## `visible` fait foi : la chambre n'existe que le temps du plongeon, et le carter avec elle.
func fill_solids(shapes: PlaneShapes) -> void:
	super.fill_solids(shapes)
	if is_instance_valid(_core_interior) and _core_interior.visible:
		shapes.reserve(shapes.size() + 1)
		shapes.add_disc(_core_interior.reactor_plane_position(), _core_interior.housing_radius())

## Là où le chasseur en est de sa plongée — pour les instruments du HUD.
func core_plane_position() -> Vector2:
	return _core_interior.reactor_plane_position() if _core_interior != null else Vector2.ZERO

func is_diving() -> bool:
	return is_instance_valid(_combat) and _combat.phase() == LeviathanCombat.Phase.DIVE

## Les écrans qui arrêtent une balle — ils appartiennent au boss, pas au niveau.
func fire_screens() -> PlaneShapes:
	return _combat.fire_screens() if is_instance_valid(_combat) else null

func advance(delta: float) -> void:
	_track_core_target(delta)

## Le module, pour que le niveau puisse l'interroger sans connaître son type.
func combat_module() -> LeviathanCombat:
	return _combat

## Le cadrage de la chambre : elle est plus haute que le plan ordinaire, la caméra recule
## d'autant. ⚠️ Déplacé ici avec la plongée — il n'avait qu'un seul appelant, et c'était elle.
func _frame_chamber() -> void:
	var director := _camera as CameraDirector
	if director == null:
		return
	var chamber := GameplayPlane.CHAMBER_BOUNDS
	director.frame_scaled(chamber.size.y / GameplayPlane.BOUNDS.size.y,
		GameplayPlane.to_world(chamber.get_center()), 0.0)

## L'armure revient — avec une plaque de moins. ⚠️ À ANNONCER : une armure qui repousse
## sans un mot se lit comme un bug, pas comme une mécanique. Le compte dans la bannière
## dit que le boss se répare de plus en plus mal.
func _on_armour_reformed(_cycle: int, plates: int) -> void:
	_sfx(&"danger_alarm")
	_banner("ARMURE REFORMEE — %d PLAQUES" % plates, _BANNER_IVORY, 1.4)
	_say(&"armour_reformed")
	if _hud != null:
		_hud.set_boss_limbs(_LEVIATHAN_PLATE_LABELS.slice(0, plates))

## Glisse la caméra vers le noyau, ou la ramène. ⚠️ Passe par la POSE DE REPOS du
## `CameraDirector` : écrire `Camera3D.transform` directement serait écrasé par le shake
## à l'image suivante.
## Le zoom d'entrée : on plonge dans l'ouverture jusqu'à ce qu'elle remplisse l'écran.
##
## ⚠️ IL NE CADRE PLUS LA PHASE, IL LA COUVRE. Il glissait à mi-chemin du boss et y restait
## pendant toute la plongée — d'où « on perd de vue le vaisseau qui est dans la sphère » :
## un cadrage bâtard, ni le plan de jeu ni un gros plan. Il sert maintenant de RIDEAU : il
## va jusqu'au bout, la bascule de lieu se fait derrière, et le cadrage normal reprend une
## fois dedans (`dive_entered` appelle `_dive_camera(false)`).

## Le repère de cible SUIT le flux, à l'image, et il BAT.
##
## ⚠️ Le suivi n'est pas un luxe : c'est tout l'intérêt. Un repère posé une fois à l'entrée
## se retrouverait à plusieurs unités de la cible dès la première seconde de dérive — il
## deviendrait le second signal faux, après le réacteur du décor.
##
## Sondage plutôt que signal : c'est une valeur CONTINUE, et un signal par image ne dirait
## rien de plus qu'une lecture par image.
func _track_core_target(delta: float) -> void:
	if _core_interior == null or _combat == null:
		return
	if not _core_interior.visible:
		return
	_core_marker_age += delta
	_core_interior.set_target_marker(_combat.flux_plane_position(), true)
	# ⚠️ Le battement dit si le tir COMPTE. Un repère qui bat pareil ouvert et fermé
	# laisserait le joueur tirer dans un blindage plein sans rien pour l'en avertir.
	_core_interior.pulse_target_marker(_core_marker_age, _combat.reactor_open())
	_core_interior.pose_rings(_combat.tuning.reactor_rings, _combat.combat_age())
	for i in _combat.tuning.node_count:
		_core_interior.pose_node(i, _combat.node_plane_position(i),
			_combat.node_alive(i), _core_marker_age)

# --- Helios Lance finale + victory (spec §12.7) -----------------------------

func _build_core_interior() -> void:
	if _core_interior != null:
		return
	_core_interior = CoreInterior.new()
	_core_interior.name = "CoreInterior"
	add_child(_core_interior)
	if _core_interior.is_stand_in():
		# ⚠️ À DIRE, TOUJOURS. Une doublure procédurale qui passerait pour l'asset livré
		# ferait juger le décor de la forge sur autre chose que la forge.
		print("[Level] core interior: DOUBLURE procedurale (decor BRIEF-0082 absent)")

## Bascule extérieur / intérieur. Le fond spatial et le corps du boss disparaissent : on
## n'est plus dans l'espace, on est DANS quelque chose. C'est la moitié de la sensation.

## Un missile a fini sa course. Deux issues, deux lectures, et il faut que le joueur les
## distingue à l'oreille comme à l'œil :
##
## - **sur le chasseur** : il a encaissé. Explosion moyenne, secousse de caméra, et le son de
##   coque — c'est un coup reçu, pas un fait d'armes ;
## - **abattu en vol** : il a répondu. Explosion plus petite, aucune secousse, et le son
##   d'explosion légère — la récompense de la leçon que ce projectile existe pour enseigner.
##
## ⚠️ LES DEUX ÉTAIENT MUETTES. Le missile touchait et disparaissait, ou tombait et
## disparaissait : dans les deux cas, rien à l'écran. « J'ai eu l'impression qu'ils font rien
## à part me courir après » — le joueur décrivait exactement ce qu'il voyait.
func _on_missile_ended(world_position: Vector3, on_player: bool) -> void:
	if on_player:
		_boom(world_position, VfxExplosion.Category.MEDIUM, 0.45)
		_sfx(&"hull_impact")
	else:
		_boom(world_position, VfxExplosion.Category.SMALL, 0.0)
		_sfx(&"medium_explosion", -3.0)

## Un tir est mort sur un mur. Même gerbe que sur une carapace : ce que le joueur doit lire,
## c'est « ça a été arrêté », et la source ne change rien à cette lecture.
##

## Raccorde le module du Pale Leviathan au reste du niveau. Câblé AVANT `begin()` : c'est
## `begin` qui déclenche le montage du module et la première émission de phase.
func _wire_combat(boss: BossController) -> void:
	var combat := boss.get_node_or_null("Combat") as LeviathanCombat
	if combat == null:
		return
	_combat = combat
	combat.phase_entered.connect(_on_phase)
	combat.structure_changed.connect(_on_structure)
	combat.piece_gauge_changed.connect(_on_piece_gauge)
	combat.piece_active_changed.connect(_on_piece_active)
	combat.piece_destroyed.connect(_on_piece_destroyed)
	combat.pull_changed.connect(_on_pull)
	combat.dive_started.connect(_on_dive_started)
	combat.dive_entered.connect(_on_dive_entered)
	combat.dive_ended.connect(_on_dive_ended)
	combat.armour_reformed.connect(_on_armour_reformed)
	combat.armour_regen.connect(_on_armour_regen)
	combat.dive_time_left.connect(_on_dive_time_left)
	combat.node_gauge_changed.connect(_on_node_gauge)
	combat.missile_ended.connect(_on_missile_ended)
	combat.node_destroyed.connect(_on_node_destroyed)

## La jauge du boss montre la PROGRESSION DU COMBAT — `fight_ratio()`, qui ne remonte
## jamais — et non la santé de la cible courante.
##
## ⚠️ ELLE A MONTRÉ `structure_ratio()`, et c'était le défaut le plus coûteux du combat.
## Cette mesure vaut « ce qu'on peut casser MAINTENANT » : elle se remplit à nouveau à
## chaque bascule. Le joueur voyait donc armure 100→0, noyau 100→0, armure 100→0, noyau
## 100→0… Playtest du 2026-08-25, sur un combat pourtant jugé mieux équilibré : « phase 1
## phase 2 phase 1 phase 2, j'ai l'impression que c'était en boucle ». Il ne se trompait
## pas — il décrivait exactement ce que le HUD lui affichait.
## La mesure qui prouvait l'avancement existait déjà, juste et testée ; son UNIQUE
## consommateur était la musique. L'oreille savait que le combat montait, l'œil n'avait
## rien. L'état de la cible courante n'est pas perdu pour autant : il vit sur la rangée de
## pastilles, qui suit les plaques du cycle.

## remplit en vert.
func _on_armour_regen(ratio: float, plates: int) -> void:
	if _hud == null:
		return
	if ratio <= 0.0:
		_regen_plates = 0
		return
	if _regen_plates != plates:
		_regen_plates = plates
		_hud.set_boss_limbs(_LEVIATHAN_PLATE_LABELS.slice(0, plates))
		for i in plates:
			_hud.set_boss_limb(i, 0.0, false)   # à terre : la barre sombre dit « pas encore »
	for i in plates:
		_hud.set_boss_limb_regen(i, ratio)

## L'état d'un verrou : la rangée de pastilles le porte, comme elle porte les plaques
## pendant l'armure. ⚠️ La rangée est ÉTEINTE pendant la plongée depuis `ADR-0025` (« plus de
## plaques ») : c'est le premier verrou annoncé qui la redresse.

## Démonte la chambre — et lui reprend ses bornes.
##
## ⚠️ LE FILET, ET IL EST NÉCESSAIRE. La sortie heureuse (`_on_dive_ended`) rend
## déjà le plan de vol ; ce n'est pas le seul chemin qui quitte le lieu. Mourir dedans,
## abandonner la partie depuis la pause, ou voir le boss tomber pendant une plongée passent
## tous par ici. Une borne oubliée laisserait le joueur voler jusqu'à −10,7 dans la phase
## SUIVANTE, hors du cadre de la caméra — et rien ne le signalerait.
func _clear_core_interior() -> void:
	GameplayPlane.reset_bounds()
	if _core_interior == null:
		return
	_core_interior.queue_free()
	_core_interior = null

## ⚠️ ET LE FILET DU FILET : quitter la scène rend TOUJOURS le plan ordinaire. `bounds` est
## le seul état global du jeu ; il ne doit pas pouvoir survivre au niveau qui l'a changé —
## un retour au titre en pleine plongée, et l'écran-titre hériterait des bornes de la
## chambre.

func _on_dive_ended(_cycle: int, flux_down: bool) -> void:
	# On quitte le lieu : il rend le plan de vol. Voir `_leave_chamber()` pour les AUTRES
	# chemins de sortie — celui-ci n'est que le plus heureux.
	GameplayPlane.reset_bounds()
	# L'éjection est une secousse, pas un fondu : on est recraché.
	_boom(boss.global_position if boss != null else Vector3.ZERO,
		VfxExplosion.Category.HEAVY, 0.85)
	_sfx(&"boss_phase_shift")
	if _player != null:
		_player.end_autopilot()
		_player.plane_lift = 0.0   # on ressort, le chasseur redescend dans le plan
		_player.plane_position = _outside_plane
	if _combat != null:
		_combat.dive_anchor = Vector2.INF   # le flux redevient une affaire de boss
	if _core_interior != null:
		_core_interior.set_target_marker(Vector2.ZERO, false)
	_show_core_interior(false)
	_dive_camera(false)
	_clear_core_interior()
	if not flux_down:
		_banner("EJECTE", _BANNER_IVORY, 1.0)

## L'armure revient — avec une plaque de moins. ⚠️ À ANNONCER : une armure qui repousse
## sans un mot se lit comme un bug, pas comme une mécanique. Le compte dans la bannière
## dit que le boss se répare de plus en plus mal.

## ⚠️ C'EST ICI QUE L'ON CHANGE DE LIEU, et c'est tout l'objet de la refonte. Le zoom de
## `dive_started` a fini sa course : l'écran est rempli par l'ouverture, donc la bascule
## passe inaperçue. On masque l'extérieur, on montre l'arène, on y pose le chasseur — et
## **la caméra revient à son cadrage normal**, parce que l'arène est bâtie à l'échelle du
## plan de jeu. C'est ce dernier point qui règle « on perd de vue le vaisseau » : dans le
## noyau, le jeu se lit exactement comme partout ailleurs.
func _on_dive_entered(_cycle: int) -> void:
	if _player != null:
		_player.end_autopilot()
	# ⚠️ LE LIEU PREND SES BORNES AVANT QU'ON Y POSE LE CHASSEUR. La chambre est plus grande
	# que l'arène ouverte (`GameplayPlane.CHAMBER_BOUNDS`) : le blindage y occupe 16,6 unités
	# de diamètre, et sous le plan de vol ordinaire le chasseur n'avait la place ni de tenir
	# entre les murs ni de se poster dessous — il était convoyé le long des arcs et éjecté.
	# L'ordre compte : poser sa position d'abord la ferait borner par l'ancien plan.
	GameplayPlane.use_bounds(GameplayPlane.CHAMBER_BOUNDS)
	_show_core_interior(true)
	if _player != null and _core_interior != null:
		# ⚠️ LE MÊME POINT QUE L'AUTOPILOTE, et il n'y en a plus qu'un. Ici on lisait
		# l'ancrage `Entry_Point` du décor — sculpté avant que les murs n'existent — pendant
		# que l'autopilote visait `dive_entry_local()`, déduit des anneaux. Deux points
		# d'entrée pour le même fait : le chasseur était posé à un endroit puis conduit à un
		# autre, et le premier a fini hors de l'aire de jeu sans que rien ne s'en aperçoive.
		_player.plane_position = _core_interior.reactor_plane_position() \
			+ _combat.tuning.dive_entry_local()
		# Dedans, le chasseur revole DANS le plan : plus besoin de le soulever pour qu'il
		# cesse de disparaître derrière la cible, il n'y a plus de sphère devant lui.
		_player.plane_lift = 0.0
	# La cible suit le lieu : le flux vit désormais sur le réacteur de l'arène et non au
	# centre du corps du boss, resté dehors.
	if _combat != null and _core_interior != null:
		_combat.dive_anchor = _core_interior.reactor_plane_position()
		# ⚠️ ET ON DIT OÙ ELLE EST. La cible dérive de plusieurs unités autour de l'ancre ;
		# sans repère, le joueur tire sur le réacteur du décor pendant qu'elle est ailleurs.
		_core_marker_age = 0.0
		_core_interior.set_target_marker(_combat.flux_plane_position(), true)
		# Le blindage se dresse avec l'arène : ses arcs se déduisent des MÊMES Resources
		# que la mécanique, jamais d'une copie.
		_core_interior.build_rings(_combat.tuning.reactor_rings)
		_core_interior.build_nodes(_combat.tuning.node_count)
		_regen_plates = 0   # la rangée se redressera au premier verrou annoncé
	_frame_chamber()

## L'état d'un verrou : la rangée de pastilles le porte, comme elle porte les plaques
## pendant l'armure. ⚠️ La rangée est ÉTEINTE pendant la plongée depuis `ADR-0025` (« plus de
## plaques ») : c'est le premier verrou annoncé qui la redresse.
func _on_node_gauge(index: int, ratio: float, alive: bool) -> void:
	if _hud == null or _combat == null:
		return
	if _regen_plates != -1:
		_regen_plates = -1
		_hud.set_boss_limbs(_LEVIATHAN_LOCK_LABELS.slice(0, _combat.tuning.node_count))
	_hud.set_boss_limb(index, ratio, alive)

## L'armure se reconstruit : la RANGÉE DE PLAQUES le montre, cuve par cuve, au lieu de
## laisser une seconde de vide.
##
## ⚠️ La rangée est éteinte pendant la plongée (« plus de plaques »). On la redresse ici,
## pour le cycle QUI VIENT — c'est ce qui permet de voir arriver l'armure, et combien il en
## reste. Même vocabulaire que la repousse des appendices du mini-boss : une barre qui se
## Le sablier de la plongée. Le niveau relaie : le module ne connaît pas le HUD, le HUD ne
## connaît pas le Leviathan.
func _on_dive_time_left(ratio: float) -> void:
	if _hud != null:
		_hud.set_dive_time_left(ratio)

## remplit en vert.

## Le champ gravitique (vagues d'aspiration de la phase 2) s'ajoute à la vitesse du joueur. Le module publie
## à chaque image tant que la phase l'exige ; on la recalcule ici depuis la position
## COURANTE du joueur (il bouge) et on la lui impose — il la consomme et la remet à zéro,
## si bien qu'une phase sans champ ne traîne aucune aspiration résiduelle.
func _on_pull(speed_max: float, radius: float, centre: Vector2) -> void:
	if _player == null:
		return
	# `add_pull` et non `apply_pull` : l'aspiration s'AJOUTE à celles déjà posées cette
	# image. Le boss est seul aujourd'hui, mais un champ de mines et lui peuvent se
	# retrouver dans la même rencontre — et une affectation effacerait silencieusement les
	# puits des autres, sans erreur ni test rouge.
	_player.add_pull(GravityWell.pull_at(_player.plane_position, centre, radius, speed_max))

# --- La plongée dans le noyau (ADR-0021) --------------------------------------
## Le playtest disait : « on ne voit pas, on ne comprend pas qu'il faut aller dans le
## noyau pour tirer ». La cible ne se DÉSIGNE donc plus, elle se REMPLIT l'écran : le
## corps s'ouvre, le chasseur y est tiré, la caméra plonge derrière lui. C'est la même
## grammaire que l'appontage — un autopilote et un cadrage — parce que le joueur l'a
## déjà apprise à la fin du niveau.

## Distance de la caméra à la gueule au bout du zoom, en mètres. Déduite du champ de
## vision (62° verticaux) et du passage libre mesuré de l'iris (4,378 m) : 3,64 m serait le
## minimum pour qu'il remplisse l'écran, 4,5 lui en laisse 81 % et garde la lèvre visible.
const DIVE_FRAME_DISTANCE := 4.5
## Hauteur de la gueule au-dessus du plan, dans la coque du boss.
const DIVE_MAW_HEIGHT := 1.5

## L'intérieur du noyau : une **zone dédiée**, montée à l'origine du monde et à l'échelle
## du plan de jeu. Bâtie par code et non posée dans `graybox.tscn` — la scène est éditée
## par une autre session, et un `.tscn` se fusionne très mal à deux.
## Où était le chasseur juste avant d'entrer : on l'y repose en ressortant, sans quoi il
## réapparaît dehors à la place qu'il occupait DANS l'arène intérieure — deux repères qui
## n'ont rien à voir.
## Etat du fond spatial avant qu'on le masque, pour le rendre tel quel et non « allume ».
var _backdrop_was_visible: bool = true
## Le fond est-il masqué en ce moment ? Sans ce drapeau, un second masquage relèverait
## `false` comme « état d'avant » et le fond ne reviendrait jamais.
var _backdrop_hidden: bool = false

## Masque le fond spatial, ou le RESTAURE tel qu'il était.
##
## ⚠️ ON RESTAURE CE QU'IL Y AVAIT, pas « visible ». `--no-backdrop` éteint le fond pour
## juger une silhouette ; un `visible = true` au sortir rallumerait le fond au milieu d'une
## mesure, et l'on conclurait sur deux images qui ne se comparent pas.
##
## Deux décors s'en servent désormais — l'arène du noyau (`ADR-0025`) et le survol de lune
## (`ADR-0027`) : la précaution vit ici, en un seul endroit, plutôt qu'en deux copies.

func _on_node_destroyed(_index: int, world_position: Vector3) -> void:
	_boom(world_position, VfxExplosion.Category.MEDIUM, 0.35)
	_sfx(&"medium_explosion")

func _on_piece_destroyed(_phase: int, _index: int, world_position: Vector3) -> void:
	_boom(world_position, VfxExplosion.Category.MEDIUM, 0.4)
	_sfx(&"medium_explosion")
	# Une plaque qui cède est le seul retour que le joueur ait sur sa progression dans
	# l'armure : elle mérite qu'on tienne l'image (LOI-EXP-03).
	_freeze(HitStop.PLATE)

## Le champ gravitique (vagues d'aspiration de la phase 2) s'ajoute à la vitesse du joueur. Le module publie
## à chaque image tant que la phase l'exige ; on la recalcule ici depuis la position
## COURANTE du joueur (il bouge) et on la lui impose — il la consomme et la remet à zéro,
## si bien qu'une phase sans champ ne traîne aucune aspiration résiduelle.

## Bascule extérieur / intérieur. Le fond spatial et le corps du boss disparaissent : on
## n'est plus dans l'espace, on est DANS quelque chose. C'est la moitié de la sensation.
func _show_core_interior(inside: bool) -> void:
	if _core_interior != null:
		_core_interior.visible = inside
	backdrop_gate.call(inside)
	if boss != null:
		boss.visible = not inside
		# Le corps s'efface AVEC sa cible : caché mais touchable, il faisait écran aux balles
		# qui passaient le noyau (voir `BossController.set_body_targetable`).
		boss.set_body_targetable(not inside)

## Démonte la chambre — et lui reprend ses bornes.
##
## ⚠️ LE FILET, ET IL EST NÉCESSAIRE. La sortie heureuse (`_on_dive_ended`) rend
## déjà le plan de vol ; ce n'est pas le seul chemin qui quitte le lieu. Mourir dedans,
## abandonner la partie depuis la pause, ou voir le boss tomber pendant une plongée passent
## tous par ici. Une borne oubliée laisserait le joueur voler jusqu'à −10,7 dans la phase
## SUIVANTE, hors du cadre de la caméra — et rien ne le signalerait.

## La jauge du boss montre la PROGRESSION DU COMBAT — `fight_ratio()`, qui ne remonte
## jamais — et non la santé de la cible courante.
##
## ⚠️ ELLE A MONTRÉ `structure_ratio()`, et c'était le défaut le plus coûteux du combat.
## Cette mesure vaut « ce qu'on peut casser MAINTENANT » : elle se remplit à nouveau à
## chaque bascule. Le joueur voyait donc armure 100→0, noyau 100→0, armure 100→0, noyau
## 100→0… Playtest du 2026-08-25, sur un combat pourtant jugé mieux équilibré : « phase 1
## phase 2 phase 1 phase 2, j'ai l'impression que c'était en boucle ». Il ne se trompait
## pas — il décrivait exactement ce que le HUD lui affichait.
## La mesure qui prouvait l'avancement existait déjà, juste et testée ; son UNIQUE
## consommateur était la musique. L'oreille savait que le combat montait, l'œil n'avait
## rien. L'état de la cible courante n'est pas perdu pour autant : il vit sur la rangée de
## pastilles, qui suit les plaques du cycle.
func _on_structure(ratio: float) -> void:
	var progress := _combat.fight_ratio() if _combat != null else ratio
	if _hud != null:
		_hud.set_boss_health(progress)
	_music().boss_health_ratio = progress
	_push_music()

## Une sous-cible a bougé. Le niveau relaie : le HUD ne connaît pas le Leviathan, le
## module ne connaît pas le HUD.

## La plaque à viser a changé (phase 1) ou s'est éteinte (`-1`, autres phases). Le niveau
## relaie au HUD, qui surligne la pastille active — le joueur voit enfin laquelle traiter.
func _on_piece_active(index: int) -> void:
	if _hud != null:
		_hud.set_boss_limb_active(index)

## L'armure se reconstruit : la RANGÉE DE PLAQUES le montre, cuve par cuve, au lieu de
## laisser une seconde de vide.
##
## ⚠️ La rangée est éteinte pendant la plongée (« plus de plaques »). On la redresse ici,
## pour le cycle QUI VIENT — c'est ce qui permet de voir arriver l'armure, et combien il en
## reste. Même vocabulaire que la repousse des appendices du mini-boss : une barre qui se
## Le sablier de la plongée. Le niveau relaie : le module ne connaît pas le HUD, le HUD ne
## connaît pas le Leviathan.

func _cycle_label(cycle: int, cycles: int) -> String:
	return "DERNIER ASSAUT" if cycle >= cycles else "CYCLE %d / %d" % [cycle + 1, cycles]

## Chaque transition du Leviathan, donnée à voir : bannière (les mots exacts du design),
## secousse, bascule musicale, et la rangée de pastilles reconfigurée pour les sous-cibles
## de la phase qui s'ouvre. Les phases avancent sur une condition MATÉRIELLE — le module
## en est seul juge, le niveau ne fait que l'annoncer.
## Chaque bascule du Leviathan. ⚠️ Les phases avancent sur une condition MATÉRIELLE —
## l'armure du cycle à terre, ou le compte à rebours du noyau épuisé. Le module en est
## seul juge ; le niveau ne fait que l'annoncer et régler la musique.
func _on_phase(phase: int) -> void:
	match phase:
		LeviathanCombat.Phase.ARMOR:
			# La rangée de pastilles suit le nombre de plaques du cycle : au cycle 2 il
			# n'y en a plus que trois, et une quatrième pastille mentirait.
			if _hud != null and _combat != null:
				_hud.set_boss_limbs(_LEVIATHAN_PLATE_LABELS.slice(0, _combat.plates().size()))
			_cycle_beat()
		LeviathanCombat.Phase.DIVE:
			# La mise en scène est portée par `dive_started` : ici, seulement la musique.
			_cycle_beat()
		LeviathanCombat.Phase.DEFEATED:
			# La mort est portée par `defeated` → `_on_final_boss_defeated` (finale Helios).
			# Seul le compteur est éteint ici : le panneau, lui, survit à la phase.
			if _hud != null:
				_hud.set_boss_cycle("")

## Règle la musique sur l'avancement du combat. `boss_phase` porte le CYCLE : la
## partition monte à chaque tour, et le dernier cycle sonne comme le dernier.

## Une sous-cible a bougé. Le niveau relaie : le HUD ne connaît pas le Leviathan, le
## module ne connaît pas le HUD.
func _on_piece_gauge(index: int, ratio: float, alive: bool) -> void:
	if _hud != null:
		_hud.set_boss_limb(index, ratio, alive)

## La plaque à viser a changé (phase 1) ou s'est éteinte (`-1`, autres phases). Le niveau
## relaie au HUD, qui surligne la pastille active — le joueur voit enfin laquelle traiter.

## Règle la musique sur l'avancement du combat. `boss_phase` porte le CYCLE : la
## partition monte à chaque tour, et le dernier cycle sonne comme le dernier.
func _cycle_beat() -> void:
	if _combat == null:
		return
	var cycles: int = _combat.tuning.cycle_count if _combat.tuning != null else 1
	var cycle := _combat.cycle()
	_music().boss_phase = mini(cycle, maxi(cycles - 1, 0))
	_music().boss_phase_count = cycles
	_push_music()
	var label := _cycle_label(cycle, cycles)
	if _hud != null:
		_hud.set_boss_cycle(label)
	print("[Level] leviathan %s — %s" % [label,
		"noyau" if _combat.phase() == LeviathanCombat.Phase.DIVE else "armure"])

## Le cycle courant, tel que le joueur doit le lire.
##
## ⚠️ AU-DELÀ DE `cycle_count`, NE JAMAIS AFFICHER « 4 / 3 ». Le combat n'est pas borné à
## trois tours et ne l'a jamais été : `plates_for_cycle()` rend le plancher de plaques
## indéfiniment, et le boss ne meurt qu'une fois le flux assez frappé. L'invariant 5 de
## `LeviathanTuning` garantit seulement que trois tours SUFFIRAIENT à un joueur tirant
## 85 % du temps dans le noyau à la cadence de référence — c'est une hypothèse de
## dimensionnement, pas une fin de combat. Le playtest du 2026-08-25 a produit un quatrième
## tour, et le journal a affiché « cycle 4/3 » : un compteur qui dépasse son total dit au
## joueur que le jeu s'est trompé. On nomme le dépassement au lieu de le compter.
## Le nom de la phase courante, pour qui mesure plutôt que pour qui joue : la sonde de
## densité s'en sert pour situer un chiffre. Public, parce qu'un outil de mesure n'a pas à
## connaître l'`enum` privé du director.

## Glisse la caméra vers le noyau, ou la ramène. ⚠️ Passe par la POSE DE REPOS du
## `CameraDirector` : écrire `Camera3D.transform` directement serait écrasé par le shake
## à l'image suivante.
## Le zoom d'entrée : on plonge dans l'ouverture jusqu'à ce qu'elle remplisse l'écran.
##
## ⚠️ IL NE CADRE PLUS LA PHASE, IL LA COUVRE. Il glissait à mi-chemin du boss et y restait
## pendant toute la plongée — d'où « on perd de vue le vaisseau qui est dans la sphère » :
## un cadrage bâtard, ni le plan de jeu ni un gros plan. Il sert maintenant de RIDEAU : il
## va jusqu'au bout, la bascule de lieu se fait derrière, et le cadrage normal reprend une
## fois dedans (`dive_entered` appelle `_dive_camera(false)`).
func _dive_camera(inside: bool, snap: bool = false) -> void:
	var director := _camera as CameraDirector
	if director == null:
		return
	if not inside:
		# ⚠️ COUPE FRANCHE A L'ENTREE, GLISSEMENT A LA SORTIE. En glissant à l'entrée, la
		# caméra revenait de la gueule — à une douzaine d'unités de là — vers l'origine où
		# l'arène est montée, pendant une demi-seconde. Or à cet instant le fond spatial et
		# le corps du boss sont déjà masqués : elle traversait donc un monde vide et la
		# capture ne montrait QUE le HUD sur du noir. La coupe est invisible parce que le
		# zoom vient de remplir l'écran ; le glissement, lui, ne l'était pas du tout.
		director.restore_rest(0.0 if snap else 0.5)
		return
	var home := director.home_transform()
	var focus := boss.global_position if boss != null else Vector3.ZERO
	# ⚠️ ON SE POSE A UNE DISTANCE CALCULEE, PAS A UNE FRACTION DE LA HAUTEUR D'ORIGINE.
	# Premier essai : `home.origin.y * 0.22`, soit Y = 3,08 pour une caméra d'origine à 14.
	# La coque du boss fait 3,162 m de haut : la caméra finissait DANS la coque, et la
	# capture ne montrait qu'un amas de plaques — ni gueule, ni ouverture, ni plongée.
	# Une fraction d'une hauteur ne dit rien de ce qu'on cadre.
	#
	# Le cadrage se déduit du champ de vision : à 62° verticaux, encadrer un puits de
	# 4,378 m demande 3,64 m au minimum. On se pose à `DIVE_FRAME_DISTANCE`, ce qui lui
	# laisse ~81 % de la hauteur d'écran — assez pour qu'il déborde presque, assez peu
	# pour qu'on voie encore la lèvre s'écarter autour.
	# On recule le long de l'axe ARRIERE de la caméra d'origine, donc l'orientation et la
	# lecture du plan de jeu sont conservées, et le cadrage suit si la caméra est retouchée.
	var backward := home.basis.z.normalized()
	var maw := focus + Vector3(0.0, DIVE_MAW_HEIGHT, 0.0)
	var enter := _combat.tuning.dive_enter_time if _combat != null and _combat.tuning != null else 1.4
	director.push_rest(Transform3D(home.basis, maw + backward * DIVE_FRAME_DISTANCE),
		maxf(enter - 0.15, 0.2))

func _on_dive_started(cycle: int, centre: Vector2) -> void:
	_sfx(&"boss_phase_shift")
	# ⚠️ CETTE BANNIÈRE A DIT « ENCORE » à chaque plongée sauf la première — le mot nomme
	# la répétition, dans le seul moment du combat qui pouvait nommer l'avancement. Elle
	# compte désormais les passages : deux, trois, quatre. Un nombre qui monte se lit comme
	# du terrain gagné ; « encore » se lit comme du surplace.
	_banner("DANS LE NOYAU" if cycle == 0 else "NOYAU — PASSAGE %d" % (cycle + 1),
		_BANNER_MAGENTA, 1.2)
	_say(&"dive_entered")
	if _hud != null:
		_hud.set_boss_limbs(PackedStringArray())   # plus de plaques : la rangée s'éteint
	_build_core_interior()
	if _player != null:
		# ⚠️ AVANT `begin_autopilot`, pas apres. L'autopilote emmene le chasseur a la gueule :
		# relever sa position une fois dedans memoriserait le point d'aspiration, pas
		# l'endroit d'ou le joueur est parti — et il ressortirait ailleurs qu'il n'est entre.
		_outside_plane = _player.plane_position
		# ⚠️ Pendant l'autopilote le chasseur est GUIDÉ, invulnérable et il ne tire pas
		# (`player_fighter_controller.gd:133`). C'est acceptable — et voulu — pour les
		# 1,4 s de l'entrée : le joueur regarde le corps s'ouvrir. Mais il faut lui rendre
		# la main à l'instant exact où le tir s'ouvre, d'où `end_autopilot()` juste après.
		# ⚠️ PAS AU CENTRE EXACT : le flux y est, et le chasseur disparaissait DERRIÈRE lui —
		# vu en capture, un noyau splendide et pas un vaisseau à l'écran. On le pose en
		# dessous, à portée de tir : c'est la position d'un shooter vertical, celle où le
		# joueur sait déjà ce qu'il a à faire.
		#
		# ⚠️ ET LA DISTANCE NE S'ÉCRIT PLUS ICI. Elle valait `-5.0`, une constante posée avant
		# que les murs n'existent — et qui tombait EN PLEIN DEDANS. Le chasseur naissait dans
		# le blindage, se faisait repousser vers l'intérieur et se retrouvait encagé : « je
		# fonce tout droit et mon vaisseau est bloqué, il avance pas ». `dive_entry_local()`
		# la déduit des anneaux livrés, et une garde refuse ce qui enfermerait.
		_player.begin_autopilot(centre + _combat.tuning.dive_entry_local())
		# Il vole DANS le noyau, au-dessus de son plancher : sans cette hauteur il passe
		# derrière la coque et on ne le voit plus.
		_player.plane_lift = CoreInterior.FLIGHT_LIFT
	_dive_camera(true)

## ⚠️ C'EST ICI QUE L'ON CHANGE DE LIEU, et c'est tout l'objet de la refonte. Le zoom de
## `dive_started` a fini sa course : l'écran est rempli par l'ouverture, donc la bascule
## passe inaperçue. On masque l'extérieur, on montre l'arène, on y pose le chasseur — et
## **la caméra revient à son cadrage normal**, parce que l'arène est bâtie à l'échelle du
## plan de jeu. C'est ce dernier point qui règle « on perd de vue le vaisseau » : dans le
## noyau, le jeu se lit exactement comme partout ailleurs.
