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
## ⚠️ INJECTÉE, jamais cherchée par `get_node("CameraDirector")`. Une mise en scène qui cherche
## un nœud par son chemin suppose l'arbre du niveau qui l'héberge — et cesse d'être réutilisable
## le jour où un autre niveau range ses nœuds autrement.
var _camera: Node = null
## Les répliques du niveau. ⚠️ INJECTÉES ET NON PRÉCHARGÉES : ce sont du CONTENU, il change
## d'un niveau à l'autre, et un boss rejoué ailleurs n'y dirait pas les mêmes choses.
var _lines: DialogueScript = null

## ⚠️ L'ORDRE DU BANDEAU N'EST PAS LE MÊME POUR TOUS, ET LE PERDRE COÛTERAIT UNE RANGÉE DE
## PASTILLES ÉTEINTES SUR UN BOSS INTACT. `show_boss()` ÉTEINT les pastilles ; `begin()` monte
## le module, qui les rallume en émettant sa première phase. Le Pale Leviathan a donc besoin du
## bandeau AVANT `begin()`. Le Choir Harvester, lui, ne rallume rien depuis `begin()` : il
## publie ses jauges après, et le bandeau doit venir d'abord pour ne pas les effacer. Deux
## boss, deux ordres, et aucun des deux ne se devine — d'où ce drapeau plutôt qu'un choix
## implicite.
var show_boss_before_begin: bool = false

## Ce que la mort du boss vaut au score. Zéro par défaut : un boss qui ne rapporte rien est un
## choix de conception, pas un oubli — mais il doit être écrit quelque part.
var score_value: int = 0

func bind(runtime: CombatRuntime, hud: CanvasLayer, game_state: Object,
		bullets: BulletManager, player: PlayerFighterController,
		lines: DialogueScript = null, camera: Node = null) -> void:
	_runtime = runtime
	_hud = hud
	_game_state = game_state
	_bullets = bullets
	_player = player
	_lines = lines
	_camera = camera

## Monte le boss et le met en scène.
##
## ⚠️ L'ORDRE COMPTE, ET IL A DÉJÀ COÛTÉ. `_wire()` est appelé AVANT `begin()` parce que c'est
## `begin()` qui monte le module de combat, donc qui crée les appendices ; et les jauges sont
## publiées APRÈS, parce que les interroger avant rend zéro et affiche des pastilles éteintes
## sur un boss intact.
func mount(scene: PackedScene, parent: Node) -> BossController:
	boss = scene.instantiate() as BossController
	# ⚠️ AVANT `add_child` : une pose ou une échelle appliquée après le montage se voit à
	# l'écran le temps d'une image, et sur un boss de huit mètres ça ne passe pas inaperçu.
	_configure(boss)
	parent.add_child(boss)
	boss.health_changed.connect(_on_health)
	boss.defeated.connect(_on_defeated)
	# Le corps d'un boss peut être blindé : sans ce retour, tirer dessus ne produit RIEN à
	# l'écran et se lit comme un défaut, pas comme une armure. Le signal existe sur tout boss ;
	# tous ne le déclenchent pas.
	boss.deflected.connect(_on_deflected)
	_wire(boss)
	if show_boss_before_begin and _hud != null:
		_hud.show_boss(boss.display_name)
	boss.begin(_bullets, _player)
	if _runtime != null:
		_runtime.sfx(&"danger_alarm")
	if not show_boss_before_begin and _hud != null:
		_hud.show_boss(boss.display_name)
	_after_begin(boss)
	return boss

## Point d'accroche des sous-types : poser la coque avant qu'elle n'entre dans l'arbre.
func _configure(_mounted: BossController) -> void:
	pass

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

## Les écrans qui ARRÊTENT une balle sans la prendre. Aucun par défaut : tous les boss n'en
## posent pas. ⚠️ Générique ici pour que le directeur puisse les demander sans savoir quel boss
## il a monté — c'est ce qui évite au niveau de tenir une référence par boss, et donc de
## l'oublier.
func fire_screens() -> PlaneShapes:
	return null

## Point d'accroche des sous-types : défaire ce qu'ils ont monté. Rien par défaut.
func _teardown() -> void:
	pass

# --- Les gestes du runtime, avec leur garde ----------------------------------
#
# ⚠️ ILS EXISTENT POUR QUE LA MISE EN SCÈNE SOIT TESTABLE SANS RUNTIME. Un banc monte le boss
# et son module, rien d'autre : `_runtime` y est nul, et un appel direct fait tomber le test
# sur une erreur qui ne dit rien du comportement gardé. Les gardes sont ici, une fois, plutôt
# que recopiées à chaque appel — il y en a une quarantaine.

## L'état musical. Un exemplaire de rechange quand il n'y a pas de runtime : la mise en scène
## peut alors écrire dedans sans que personne ne le lise, ce qui est exactement ce qu'un banc
## veut.
var _spare_music: MusicContext = MusicContext.new()

func _music() -> MusicContext:
	return _runtime.music if _runtime != null else _spare_music

func _push_music() -> void:
	if _runtime != null:
		_runtime.push_music()

func _sfx(cue: StringName, volume_db: float = 0.0) -> void:
	if _runtime != null:
		_runtime.sfx(cue, volume_db)

func _boom(world_position: Vector3, category: VfxExplosion.Category, trauma: float) -> void:
	if _runtime != null:
		_runtime.boom(world_position, category, trauma)

func _banner(text: String, colour: Color, duration: float) -> void:
	if _runtime != null:
		_runtime.banner(text, colour, duration)

func _freeze(duration: float) -> void:
	if _runtime != null:
		_runtime.freeze(duration)

## Raccourci de réplique — le sous-type en dit plusieurs, et la garde de nullité ne doit pas
## être recopiée à chaque fois.
func _say(key: StringName) -> void:
	if _runtime != null and _lines != null:
		_runtime.say(_lines, key)
