class_name HarvesterTuning
extends Resource
## Réglages du combat du Choir Harvester (spec §8.1 : aucune valeur de gameplay en
## dur). Unités : distances en unités monde, temps en secondes, angles en degrés.
##
## LA BOUCLE QUE CES VALEURS DÉCRIVENT — les trois appendices attaquent et protègent
## le corps. Détruits, ils cessent d'attaquer et repoussent après `limb_rebuild_time`.
## Les trois à terre en même temps ouvrent l'iris et exposent le noyau ; le premier
## qui repousse le referme.
##
## ⚠️ La durée de la fenêtre de tir n'est PAS un réglage : elle vaut
## `limb_rebuild_time` moins le temps que le joueur met à enchaîner les deux
## appendices suivants. Enchaîner vite est donc récompensé sans qu'aucune règle ne le
## dise — et allonger `limb_rebuild_time` allonge la fenêtre autant que le répit.

@export_group("Appendices")
## Points de structure d'un appendice. Ils ne comptent PAS dans la jauge du boss :
## la jauge montre le noyau, seul objet que le joueur fait réellement descendre.
@export var limb_health: float = 90.0
## Rayon de la zone de touche d'un appendice. Généreux (spec §5.3) : viser un bras
## qui bouge sous un rideau de balles ne doit pas demander de la précision au pixel.
## 1,05 et non 0,85 : la zone est centrée sur les ARTICULATIONS et un bras mesure
## près de trois mètres — un cercle plus serré laisserait la moitié du bras visible
## mais intouchable.
@export var limb_hitbox_radius: float = 1.05
## Délai de repousse, mesuré depuis la destruction.
@export var limb_rebuild_time: float = 9.0
## Durée de l'animation de repli (destruction) et de redéploiement.
@export var limb_retract_time: float = 0.45
@export var limb_deploy_time: float = 0.8

@export_group("Iris et noyau")
## Ouverture des pétales, en degrés. Le modèle est validé jusqu'à 78° (BRIEF-0039) ;
## on reste en deçà, la marge absorbe le lissage qui dépasse sa cible avant de s'y poser.
@export var iris_open_deg: float = 72.0
@export var iris_open_time: float = 0.8
@export var iris_close_time: float = 0.45
## Rayon de touche du noyau, une fois découvert.
@export var core_hitbox_radius: float = 1.1

@export_group("Griffe a trois tetes")
## Secondes entre deux salves. C'est la pression de fond du combat.
@export var claw_fire_interval: float = 0.85
## Débattement de visée du bras et convergence des têtes (degrés).
@export var claw_sweep_deg: float = 32.0
@export var claw_head_converge_deg: float = 18.0

@export_group("Faux")
## Le réarme est le télégraphe : c'est lui qui rend l'estoc esquivable.
@export var scythe_windup_time: float = 1.0
@export var scythe_strike_time: float = 0.35
@export var scythe_recover_time: float = 1.4
## Rayon de la zone tranchante, autour de la lame, pendant la frappe.
@export var scythe_reach_radius: float = 1.6
## Dégâts au contact. Lourds : c'est un corps-à-corps télégraphié d'une seconde.
@export var scythe_damage: float = 34.0

@export_group("Canon")
@export var cannon_charge_time: float = 2.0
@export var cannon_beam_time: float = 1.5
@export var cannon_recover_time: float = 2.6
## Demi-largeur du faisceau. La ligne de télégraphe est plus fine — voir `Beam`.
@export var beam_half_width: float = 0.55
## Dégâts par CONTACT, et non par seconde.
##
## ⚠️ Ce n'est pas une approximation : `PlayerShield.take_hit` accorde 1,2 s
## d'invulnérabilité à chaque coup encaissé. Un modèle « dégâts par seconde » serait
## donc écrêté par le bouclier de toute façon, et le réglage mentirait sur ce qui se
## passe. Rester dans un faisceau de 1,5 s coûte au plus deux contacts.
@export var beam_damage: float = 28.0
## Recul du fût au tir (unités, le long de son axe).
@export var cannon_recoil: float = 0.25

func validate() -> PackedStringArray:
	var errors := PackedStringArray()
	if limb_health <= 0.0:
		errors.append("limb_health must be > 0")
	if limb_hitbox_radius <= 0.0:
		errors.append("limb_hitbox_radius must be > 0")
	if core_hitbox_radius <= 0.0:
		errors.append("core_hitbox_radius must be > 0")
	if limb_rebuild_time <= 0.0:
		errors.append("limb_rebuild_time must be > 0")
	if limb_retract_time <= 0.0 or limb_deploy_time <= 0.0:
		errors.append("limb retract/deploy times must be > 0")
	# Le repli et le redéploiement se DÉROULENT DANS le délai de repousse : ensemble
	# plus longs que lui, l'appendice serait déclaré vivant avant la fin de son
	# animation de sortie, et l'iris se refermerait sur un bras encore rentré.
	elif limb_retract_time + limb_deploy_time > limb_rebuild_time:
		errors.append("limb_retract_time + limb_deploy_time must be <= limb_rebuild_time (got %.2f + %.2f > %.2f)"
			% [limb_retract_time, limb_deploy_time, limb_rebuild_time])
	if iris_open_deg <= 0.0 or iris_open_deg > 78.0:
		# 78° est le plafond MÉCANIQUE mesuré par la forge (BRIEF-0039) : au-delà les
		# pétales se mordent entre eux.
		errors.append("iris_open_deg must be in (0, 78] (mechanical ceiling, BRIEF-0039)")
	if iris_open_time <= 0.0 or iris_close_time <= 0.0:
		errors.append("iris open/close times must be > 0")
	if claw_fire_interval <= 0.0:
		errors.append("claw_fire_interval must be > 0")
	if scythe_windup_time <= 0.0:
		# Sans réarme, l'estoc devient imparable : le télégraphe EST la règle du duel.
		errors.append("scythe_windup_time must be > 0 — the wind-up is what makes the lunge dodgeable")
	if scythe_strike_time <= 0.0:
		errors.append("scythe_strike_time must be > 0")
	if scythe_reach_radius <= 0.0:
		errors.append("scythe_reach_radius must be > 0")
	if scythe_damage <= 0.0:
		errors.append("scythe_damage must be > 0")
	if cannon_charge_time <= 0.0:
		errors.append("cannon_charge_time must be > 0 — the charge is the telegraph")
	if cannon_beam_time <= 0.0:
		errors.append("cannon_beam_time must be > 0")
	if beam_half_width <= 0.0:
		errors.append("beam_half_width must be > 0")
	if beam_damage <= 0.0:
		errors.append("beam_damage must be > 0")
	return errors
