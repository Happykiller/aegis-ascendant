class_name DensityProbe
extends Node
## Combien de projectiles hostiles à l'écran, en même temps — et rien d'autre.
##
## `LOI-LIS-05` dit que la densité n'est pas la difficulté, et qu'elle se règle sur deux
## axes (spatial, temporel). Le projet n'a jamais eu ni l'un ni l'autre : les vagues sont
## composées à l'intuition, et personne n'a jamais su combien de balles le joueur affronte
## réellement à un instant donné.
##
## ⚠️ CE N'EST PAS UN RÉGLAGE, C'EST UNE MESURE. Il ne corrige rien, ne change aucun
## comportement, et ne tourne que sur `--density-probe`. La première chose utile face à une
## question de densité est un CHIFFRE ; le jugement vient après, en jouant.
##
## Sortie, une ligne par seconde de jeu :
##   [Density] t=12.0 phase=FIGHTER_WAVES enemy=37 max=41 player=18

const REPORT_PERIOD := 1.0

var _bullets: BulletManager
var _phase_label: Callable
var _clock: float = 0.0
var _report_at: float = REPORT_PERIOD
var _max_enemy: int = 0
## Sommet de toute la partie, rendu une dernière fois à la sortie : c'est CE chiffre
## qu'on compare d'une session d'équilibrage à l'autre.
var _peak_enemy: int = 0
var _peak_phase: String = "?"

static func make(bullets: BulletManager, phase_label: Callable) -> DensityProbe:
	var probe := DensityProbe.new()
	probe.name = "DensityProbe"
	probe._bullets = bullets
	probe._phase_label = phase_label
	return probe

func _physics_process(delta: float) -> void:
	if _bullets == null:
		return
	_clock += delta
	var enemy := _bullets.team_count(BulletManager.Team.ENEMY)
	if enemy > _max_enemy:
		_max_enemy = enemy
	if enemy > _peak_enemy:
		_peak_enemy = enemy
		_peak_phase = _label()
	if _clock < _report_at:
		return
	_report_at += REPORT_PERIOD
	print("[Density] t=%.1f phase=%s enemy=%d max=%d player=%d" % [
		_clock, _label(), enemy, _max_enemy,
		_bullets.team_count(BulletManager.Team.PLAYER)])
	# Le maximum est remis à zéro à chaque rapport : on veut un profil dans le TEMPS, pas
	# une valeur qui monte et ne redescend jamais. Le sommet global est gardé à part.
	_max_enemy = 0

func _exit_tree() -> void:
	print("[Density] PIC DE LA PARTIE : %d projectiles hostiles simultanés (phase %s)"
		% [_peak_enemy, _peak_phase])

func _label() -> String:
	if _phase_label.is_valid():
		return str(_phase_label.call())
	return "?"
