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

## Fenêtre de tir minimale exploitable, en secondes. En deçà, le joueur voit l'iris
## s'ouvrir et se refermer sans avoir le temps d'y placer une salve : la mécanique
## centrale du combat existerait sur le papier et nulle part à l'écran.
const MIN_WINDOW := 2.0

@export_group("Appendices")
## Points de structure d'un appendice. Ils ne comptent PAS dans la jauge du boss :
## la jauge montre le noyau, seul objet que le joueur fait réellement descendre.
##
## ⚠️ CE N'EST PAS UN NOMBRE LIBRE. Avec `T = limb_health / reference_dps`, la fenêtre
## de tir vaut `limb_rebuild_time − 2T` : doubler cette valeur sans toucher au délai de
## repousse divise la fenêtre, et au-delà d'un certain seuil il n'y en a plus du tout —
## un boss invincible. `validate()` refuse ce cas, mais le calcul se fait ICI, à la main,
## avant d'écrire le nombre.
@export var limb_health: float = 1000.0
## Rayon de la zone de touche d'un appendice. Généreux (spec §5.3) : viser un bras
## qui bouge sous un rideau de balles ne doit pas demander de la précision au pixel.
## 1,05 et non 0,85 : la zone est centrée sur les ARTICULATIONS et un bras mesure
## près de trois mètres — un cercle plus serré laisserait la moitié du bras visible
## mais intouchable.
@export var limb_hitbox_radius: float = 1.05
## Délai de repousse, mesuré depuis la destruction.
@export var limb_rebuild_time: float = 14.0
## Dégâts par seconde de référence du joueur — sa cadence soutenue à puissance 3
## (4 traits par salve, ~10 salves/s, 10 dégâts le trait).
##
## Ce n'est pas un réglage de boss : c'est l'HYPOTHÈSE de dimensionnement, écrite noir
## sur blanc pour que `validate()` puisse vérifier qu'une fenêtre de tir existe encore.
## Sans elle, la règle « fenêtre = repousse − 2 × temps d'abattage » n'est vérifiable
## nulle part et le premier réglage un peu ambitieux rend l'iris impossible à ouvrir.
@export var reference_dps: float = 420.0
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
@export var scythe_strike_time: float = 0.4
@export var scythe_recover_time: float = 1.4
## Rayon de la zone tranchante, autour de la LAME, pendant la frappe.
@export var scythe_reach_radius: float = 1.6
## Vitesse de l'estoc : à quelle allure le CORPS se fend sur le point verrouillé.
##
## ⚠️ L'estoc déplace le boss entier, il n'agite pas un bras dans le vide. C'était le
## défaut de la première version : la lame frappait un point abstrait à vingt unités de
## là, et rien à l'écran ne reliait le geste au dégât.
@export var scythe_lunge_speed: float = 26.0
## Jusqu'où le corps consent à descendre pendant l'estoc, en unités du plan sous sa
## position de croisière. Borne l'agressivité : sans elle le boss finit collé au joueur,
## qui n'a plus d'espace pour esquiver la frappe suivante.
@export var scythe_lunge_reach: float = 7.0
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
	if reference_dps <= 0.0:
		errors.append("reference_dps must be > 0 — it is the sizing assumption, not an option")
	elif limb_health > 0.0 and limb_rebuild_time > 0.0:
		# LA RÈGLE QUI REND LE BOSS TUABLE. Le joueur abat un appendice en `T`, il lui en
		# reste deux : le premier repousse `limb_rebuild_time` après sa chute, donc la
		# fenêtre où les trois sont à terre ensemble vaut `repousse − 2T`. Nulle ou
		# négative, l'iris ne s'ouvre JAMAIS et le combat est injouable — sans qu'aucune
		# erreur ne le dise, puisque chaque valeur prise séparément est parfaitement sensée.
		var kill_time := limb_health / reference_dps
		var window := limb_rebuild_time - 2.0 * kill_time
		if window < MIN_WINDOW:
			errors.append("no usable window: rebuild %.1f s − 2 × %.1f s kill = %.1f s (need >= %.1f)"
				% [limb_rebuild_time, kill_time, window, MIN_WINDOW])
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
	if scythe_lunge_speed <= 0.0:
		# Une vitesse nulle, c'est un estoc qui n'atteint jamais son point : la faux
		# redeviendrait le geste décoratif qu'elle était.
		errors.append("scythe_lunge_speed must be > 0 — the body has to actually reach the lock")
	if scythe_lunge_reach <= 0.0:
		errors.append("scythe_lunge_reach must be > 0")
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
