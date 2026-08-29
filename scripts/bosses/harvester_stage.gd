class_name HarvesterStage
extends BossStage
## La mise en scène du Choir Harvester — ce que `BossStage` ne peut pas savoir de lui.
##
## Trois choses lui appartiennent en propre, et une seule est du décor :
##
## - ses **appendices** ont chacun une jauge, et ils REPOUSSENT. Sans le relais de repousse, le
##   HUD montrerait une barre immobile pendant les quatorze secondes de reconstruction ;
## - son **iris** s'ouvre et se referme, et c'est le moment du combat : la seule fenêtre où le
##   joueur peut faire des dégâts. Il doit s'entendre, se sentir et se lire ;
## - un appendice qui cède explose là où il était, pas au centre du boss.
##
## ⚠️ LE NIVEAU NE CONNAÎT PAS LE HARVESTER, ET LE HARVESTER NE CONNAÎT PAS LE HUD. C'est cette
## classe qui les raccorde, et c'est tout son objet — le module de combat publie des signaux
## neutres, le HUD affiche des jauges neutres.

func _wire(mounted: BossController) -> void:
	var combat := mounted.get_node_or_null("Combat") as HarvesterCombat
	if combat == null:
		return
	combat.limb_destroyed.connect(_on_limb_destroyed.bind(mounted))
	combat.limb_gauge_changed.connect(_on_limb_gauge)
	combat.limb_rebuild_changed.connect(_on_limb_rebuild)
	combat.iris_opened.connect(_on_iris_opened.bind(mounted))
	combat.iris_closed.connect(_on_iris_closed)

## ⚠️ APRÈS `begin()`, jamais avant : c'est lui qui monte le module, donc qui crée les
## appendices. Les interroger plus tôt rendrait zéro et afficherait trois pastilles éteintes
## sur un boss intact.
func _after_begin(mounted: BossController) -> void:
	var combat := mounted.get_node_or_null("Combat") as HarvesterCombat
	if combat != null:
		combat.publish_gauges()

## ⚠️ SANS LUI, LE BLINDAGE MENT. Tirer sur une carapace sans rien produire à l'écran se lit
## comme un défaut, pas comme une armure — et le mode d'échec revient intact dès qu'un écran
## consomme une balle en silence.
func _on_limb_destroyed(_kind: StringName, mounted: BossController) -> void:
	# `boom` porte déjà la secousse : la redemander ici la doublerait.
	if _runtime != null:
		_runtime.boom(mounted.global_position, VfxExplosion.Category.MEDIUM, 0.5)
		_runtime.sfx(&"medium_explosion")

func _on_limb_rebuild(index: int, ratio: float) -> void:
	if _hud != null:
		_hud.set_boss_limb_regen(index, ratio)

func _on_limb_gauge(index: int, ratio: float, alive: bool) -> void:
	if _hud != null:
		_hud.set_boss_limb(index, ratio, alive)

## Le moment du combat : la carapace s'ouvre.
func _on_iris_opened(mounted: BossController) -> void:
	if _runtime != null:
		_runtime.boom(mounted.global_position, VfxExplosion.Category.MEDIUM, 0.9)
		_runtime.sfx(&"boss_phase_shift")
	if _hud != null:
		_hud.show_banner("NOYAU EXPOSE", Color("d93d9c"), 1.4)
	_say(&"core_exposed")

func _on_iris_closed() -> void:
	if _runtime != null:
		_runtime.sfx(&"docking_lock")
	if _hud != null:
		_hud.show_banner("CARAPACE REFERMEE", Color("e4b54a"), 1.0)
	_say(&"core_shielded")
