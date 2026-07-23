class_name RetroPost
extends CanvasLayer
## Applique le réglage « pixelisation » au post-process rétro de la scène qui le porte.
##
## POURQUOI UN NŒUD ET PAS UN AUTOLOAD — le post-process vit dans les scènes
## (`graybox.tscn`, `boot.tscn`, `codex.tscn`), chacune avec son propre `ShaderMaterial`
## et ses propres réglages de luminosité (`lift` vaut 1,18 / 1,25 / 1,3 selon la scène,
## cf. ADR-0016). Un autoload devrait aller les chercher dans l'arbre à chaque
## changement de scène ; le nœud, lui, est déjà là.
##
## CE QUE LE RÉGLAGE COUPE, ET CE QU'IL NE COUPE PAS — seulement l'accrochage sur la
## grille de pixels. La postérisation, le tramage, le réchauffement et surtout le
## relèvement des tons moyens continuent de travailler.
##
## ⚠️ C'est ce dernier point qui interdit la solution évidente (`visible = false` sur la
## couche). Le correctif de luminosité d'ADR-0016 vit dans CE shader : éteindre le nœud
## rendrait l'image nette **et** la replongerait dans le sombre, en réintroduisant
## exactement le défaut qu'un ADR entier a servi à débusquer.
##
## Autoload résolu par chemin (convention projet) : le script reste compilable en mode
## `--script`, où les globales d'autoload n'existent pas.

const SettingsManagerScript := preload("res://scripts/core/settings_manager.gd")
const U_TARGET_RES := &"target_res"

@onready var _settings: SettingsManagerScript = get_node_or_null("/root/SettingsManager")

var _material: ShaderMaterial
## Grille telle qu'elle est ÉCRITE DANS LA SCÈNE, relevée une fois. Jamais en dur : les
## trois scènes pourraient diverger un jour, et une valeur codée ici les ramènerait
## silencieusement à la même — en écrasant un réglage qu'on aurait choisi ailleurs.
var _authored_res: Vector2 = Vector2(960.0, 540.0)

func _ready() -> void:
	var effect := get_node_or_null("Effect") as CanvasItem
	if effect == null:
		push_error("[RetroPost] la couche n'a pas d'enfant 'Effect'")
		return
	_material = effect.material as ShaderMaterial
	if _material == null:
		push_error("[RetroPost] 'Effect' n'a pas de ShaderMaterial")
		return
	var stored: Variant = _material.get_shader_parameter(U_TARGET_RES)
	if stored is Vector2:
		_authored_res = stored
	if _settings != null:
		_settings.graphics_changed.connect(_on_graphics_changed)
		_apply(_settings.get_graphics().pixelation)
	else:
		_apply(true)

func _on_graphics_changed(data: SettingsData) -> void:
	_apply(data.pixelation)

## Désactiver, c'est porter la grille à la taille RÉELLE du viewport : l'accrochage
## devient l'identité, et pas une ligne du shader ne change de chemin.
##
## ⚠️ Le `ShaderMaterial` est une sous-ressource de la scène, donc partagée entre les
## instances de cette scène (le piège documenté dans `title_stage.gd:61-70`). Ici chaque
## scène est une racine montée seule et le réglage est réappliqué à chaque `_ready` :
## sans conséquence, mais à savoir avant d'instancier l'une d'elles deux fois.
func _apply(pixelated: bool) -> void:
	if _material == null:
		return
	_material.set_shader_parameter(U_TARGET_RES,
		_authored_res if pixelated else Vector2(get_viewport().get_visible_rect().size))
