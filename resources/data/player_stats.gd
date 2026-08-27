class_name PlayerStats
extends Resource
## Player fighter tuning values (spec §8.1: no gameplay value hard-coded).
## Units: distances in world units, times in seconds, angles in degrees.

## Maximum planar speed (units/s).
@export var max_speed: float = 14.0
## Time to reach max_speed from rest; spec §7.3 requires < 0.25 s.
@export var accel_time: float = 0.18
## Logical hitbox radius; deliberately smaller than the visual model (spec §8.2).
@export var hitbox_radius: float = 0.25

## Demi-largeur du CORPS, pour la collision avec le décor solide.
##
## ⚠️ MESURÉ SUR `specter_9.glb`, PAS ESTIMÉ (loi « les corps ne se chevauchent pas ») :
## X ±0,876, Z ±1,230, **transformations de nœuds appliquées**. Cette précision a coûté une
## erreur : lire les bornes brutes des accesseurs donne ±0,65, parce que les canons de bout
## d'aile sont montés sur des nœuds décalés. Un `.glb` ne se mesure pas sans parcourir sa
## hiérarchie. À ne pas confondre avec
## `hitbox_radius` (0,25), qui décide de ce qui BLESSE et reste volontairement généreux pour
## le joueur — un shoot vertical se joue avec une hitbox plus petite que le vaisseau.
@export var body_radius: float = 0.88

## Demi-longueur du corps. C'est elle qui manquait : décrit par un disque de sa demi-largeur,
## le chasseur laissait son NEZ dépasser de 0,38 et traverser les murs.
@export var body_half_length: float = 1.23
## Seconds between primary shots.
@export var fire_interval: float = 0.12
## Maximum visual roll when strafing; never affects the hitbox (spec §7.3).
@export var max_bank_deg: float = 35.0

@export_group("Shield & survival")
## Shield capacity in units (spec §8.3: 100 at start).
@export var shield_max: float = 100.0
## Quiet seconds before shield regeneration begins.
@export var shield_regen_delay: float = 3.0
## Shield regeneration rate (units/s) once it starts.
@export var shield_regen_rate: float = 12.0
## Invulnerability window after an impact (spec §8.3).
@export var invuln_time: float = 1.2
## Visual lives before game over; continues are unlimited for the demo (spec §8.4).
@export var lives: int = 3

func validate() -> PackedStringArray:
	var errors := PackedStringArray()
	if max_speed <= 0.0:
		errors.append("max_speed must be > 0")
	if accel_time <= 0.0 or accel_time > 0.25:
		errors.append("accel_time must be in (0, 0.25] (spec §7.3)")
	if hitbox_radius <= 0.0:
		errors.append("hitbox_radius must be > 0")
	if body_radius <= 0.0:
		errors.append("body_radius must be > 0")
	if body_half_length < body_radius:
		errors.append("body_half_length (%.2f) < body_radius (%.2f) : un vaisseau n'est pas plus large que long"
			% [body_half_length, body_radius])
	if fire_interval <= 0.0:
		errors.append("fire_interval must be > 0")
	if shield_max <= 0.0:
		errors.append("shield_max must be > 0")
	if lives < 1:
		errors.append("lives must be >= 1")
	return errors
