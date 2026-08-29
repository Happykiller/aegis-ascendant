extends Node
## Où en est le joueur dans la campagne (autoload "Campaign").
##
## ⚠️ IL EXISTE PARCE QUE « CONTINUER » N'EXISTAIT PAS. Le rapport de mission ne savait que
## `reload_current_scene()` : on recommençait le même niveau, indéfiniment. Le deuxième niveau
## rend ce trou bloquant (`docs/plans/2026-08-29-niveau-2-execution.md`, lot A).
##
## ⚠️ ON RETIENT UN NOM, PAS UN RANG. Un index dans le livre désignerait un autre niveau le
## jour où l'un s'insère au milieu — et le joueur reprendrait ailleurs que là où il s'est
## arrêté, sans que rien ne le signale. Même leçon que les `voice_cue` et les clés de dialogue.

const BOOK := preload("res://resources/campaign/campaign_book.tres")

## Le niveau en cours. Vide = celui que le livre donne en premier.
var current_id: StringName = &""

func _ready() -> void:
	for error in BOOK.validate():
		push_error("[Campaign] %s" % error)
	if current_id == &"":
		var first := BOOK.first()
		if first != null:
			current_id = first.id

func current() -> LevelData:
	var level := BOOK.find(current_id)
	return level if level != null else BOOK.first()

## Le niveau suivant, ou `null` si c'est le dernier JOUABLE. C'est ce qui décide entre
## CONTINUER et REJOUER sur le rapport de mission.
func next() -> LevelData:
	return BOOK.after(current_id)

func has_next() -> bool:
	return next() != null

## Avance d'un niveau et rend celui qu'il faut monter, ou `null` s'il n'y en a plus.
func advance() -> LevelData:
	var following := next()
	if following == null:
		return null
	current_id = following.id
	print("[Campaign] niveau %s" % current_id)
	return following

## Revenir au début — ce que fait « RETOUR AU TITRE », et une partie perdue qu'on recommence.
func restart() -> void:
	var first := BOOK.first()
	current_id = first.id if first != null else &""

## Numéro affichable (1-based) et total, pour un HUD ou un rapport. ⚠️ Dérivé du livre, jamais
## tenu à la main : un compte tenu à la main ment au premier niveau inséré.
func position() -> Vector2i:
	return Vector2i(BOOK.index_of(current_id) + 1, BOOK.size())
