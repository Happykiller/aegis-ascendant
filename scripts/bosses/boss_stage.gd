class_name BossStage
extends Node
## Ce qui est vrai de TOUT combat de boss : le monter, relayer sa santé, annoncer sa défaite.
##
## ⚠️ IL EXISTE PARCE QUE LA MISE EN SCÈNE DES DEUX BOSS VIVAIT DANS LE SCRIPT DU NIVEAU 1 —
## trente fonctions sur soixante-dix-neuf. Un niveau qui voudrait rejouer le Pale Leviathan, ou
## simplement en poser un autre, devait donc recopier ces trente fonctions ou s'en passer.
## C'est la même frontière manquante que pour `CombatRuntime`, un cran plus haut.
##
## ⚠️ CE QUI EST ICI, ET CE QUI EST DANS UN SOUS-TYPE. Ici : monter la coque, câbler les trois
## signaux que TOUT `BossController` émet (`health_changed`, `defeated`, `deflected`), afficher
## le bandeau, figer l'image à la mort. Dans un sous-type : ce qui n'appartient qu'à CE boss —
## les appendices du Harvester, les plaques et la plongée du Leviathan. La règle de partage est
## la même que partout : « est-ce que le boss suivant en aura besoin sans rien y changer ? »
##
## Les services sont INJECTÉS, jamais cherchés par chemin : c'est la recommandation
## d'organisation de Godot, et c'est ce qui rend une scène de boss réutilisable ailleurs.

## Ce que le boss rend au niveau — le seul canal, et il RÉPOND, il n'ordonne pas.
signal defeated(world_position: Vector3)

## La coque montée, tant qu'elle vit.
var boss: BossController = null

var _runtime: CombatRuntime = null
var _hud: CanvasLayer = null
var _game_state: Object = null
var _bullets: BulletManager = null
var _player: PlayerFighterController = null
## Les répliques du niveau. ⚠️ INJECTÉES ET NON PRÉCHARGÉES : ce sont du CONTENU, il change
## d'un niveau à l'autre, et un boss rejoué ailleurs n'y dirait pas les mêmes choses.
var _lines: DialogueScript = null

## Ce que la mort du boss vaut au score. Zéro par défaut : un boss qui ne rapporte rien est un
## choix de conception, pas un oubli — mais il doit être écrit quelque part.
var score_value: int = 0

func bind(runtime: CombatRuntime, hud: CanvasLayer, game_state: Object,
		bullets: BulletManager, player: PlayerFighterController,
		lines: DialogueScript = null) -> void:
	_runtime = runtime
	_hud = hud
	_game_state = game_state
	_bullets = bullets
	_player = player
	_lines = lines

## Monte le boss et le met en scène.
##
## ⚠️ L'ORDRE COMPTE, ET IL A DÉJÀ COÛTÉ. `_wire()` est appelé AVANT `begin()` parce que c'est
## `begin()` qui monte le module de combat, donc qui crée les appendices ; et les jauges sont
## publiées APRÈS, parce que les interroger avant rend zéro et affiche des pastilles éteintes
## sur un boss intact.
func mount(scene: PackedScene, parent: Node) -> BossController:
	boss = scene.instantiate() as BossController
	parent.add_child(boss)
	boss.health_changed.connect(_on_health)
	boss.defeated.connect(_on_defeated)
	# Le corps d'un boss peut être blindé : sans ce retour, tirer dessus ne produit RIEN à
	# l'écran et se lit comme un défaut, pas comme une armure. Le signal existe sur tout boss ;
	# tous ne le déclenchent pas.
	boss.deflected.connect(_on_deflected)
	_wire(boss)
	boss.begin(_bullets, _player)
	if _runtime != null:
		_runtime.sfx(&"danger_alarm")
	if _hud != null:
		_hud.show_boss(boss.display_name)
	_after_begin(boss)
	return boss

## Point d'accroche des sous-types : câbler le module propre à CE boss. Rien par défaut.
func _wire(_mounted: BossController) -> void:
	pass

## Point d'accroche des sous-types, après que le module existe.
func _after_begin(_mounted: BossController) -> void:
	pass

## La santé du boss vers le HUD. ⚠️ Ce que la jauge montre est décidé par le sous-type quand il
## a mieux à dire — le Leviathan y met la PROGRESSION DU COMBAT et non la santé de la cible
## courante, parce que celle-ci se remplit à nouveau à chaque bascule et faisait lire le combat
## « en boucle » (playtest du 2026-08-25).
func _on_health(ratio: float) -> void:
	if _hud != null:
		_hud.set_boss_health(ratio)

func _on_deflected(world_position: Vector3) -> void:
	# Étincelle blanche et son de bouclier : la carapace RENVOIE le tir.
	if _runtime != null:
		_runtime.boom(world_position, VfxExplosion.Category.IMPACT, 0.0)
		_runtime.sfx(&"shield_impact")

## La mort. ⚠️ Quatre gestes, et le dernier libère la coque : un boss mort qui reste dans
## l'arbre continue de porter ses cibles auprès du gestionnaire de balles.
func _on_defeated(world_position: Vector3) -> void:
	if _game_state != null and score_value > 0:
		_game_state.add_score(score_value)
	if _runtime != null:
		_runtime.boom(world_position, VfxExplosion.Category.HEAVY, 1.0)
		_runtime.sfx(&"heavy_explosion")
		_runtime.freeze(HitStop.BOSS)
	if _hud != null:
		_hud.hide_boss()
	_teardown()
	if boss != null:
		boss.queue_free()
		boss = null
	defeated.emit(world_position)

## Le module de combat monté, s'il y en a un. `begin()` le crée : avant lui, il n'existe pas.
func combat() -> Node:
	return boss.get_node_or_null("Combat") if is_instance_valid(boss) else null

## Verse le CORPS du boss parmi les obstacles du plan.
##
## ⚠️ CE CHEMIN A ÉTÉ PERDU UNE FOIS, ET LA PORTE DE QUALITÉ EST RESTÉE VERTE. En sortant la
## mise en scène du script du niveau, la référence au module de combat a disparu avec elle :
## `is_instance_valid(null)` rend faux, la boucle des obstacles ne versait plus rien, et le
## boss devenait TRAVERSABLE. Aucune erreur, aucun test rouge — un boss qu'on traverse se
## découvre en jouant. C'est pour ça que ce service est ici et non chez l'appelant.
func fill_solids(shapes: PlaneShapes) -> void:
	var module := combat()
	if module == null or not module.has_method("fill_solids"):
		return
	if module.has_method("solid_capacity"):
		shapes.reserve(shapes.size() + module.solid_capacity())
	module.fill_solids(shapes)

## Point d'accroche des sous-types : défaire ce qu'ils ont monté. Rien par défaut.
func _teardown() -> void:
	pass

## Raccourci de réplique — le sous-type en dit plusieurs, et la garde de nullité ne doit pas
## être recopiée à chaque fois.
func _say(key: StringName) -> void:
	if _runtime != null and _lines != null:
		_runtime.say(_lines, key)
