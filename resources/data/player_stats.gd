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

## Demi-largeur du CORPS, pour la collision avec le décor solide. C'est AUSSI le rayon de
## la capsule, donc ce qui déborde aux deux bouts : voir [member body_half_length].
##
## ⚠️ MESURÉ SUR `specter_9.glb`, PAS ESTIMÉ (loi « les corps ne se chevauchent pas ») :
## X ±0,876, Z ±1,230, **transformations de nœuds appliquées**. Cette précision a coûté une
## erreur : lire les bornes brutes des accesseurs donne ±0,65, parce que les canons de bout
## d'aile sont montés sur des nœuds décalés. Un `.glb` ne se mesure pas sans parcourir sa
## hiérarchie. À ne pas confondre avec
## `hitbox_radius` (0,25), qui décide de ce qui BLESSE et reste volontairement généreux pour
## le joueur — un shoot vertical se joue avec une hitbox plus petite que le vaisseau.
@export var body_radius: float = 0.88

## Demi-longueur du SEGMENT de la capsule — PAS la demi-longueur du vaisseau.
##
## ⚠️ LA DISTINCTION EST TOUT LE PIÈGE, ET ELLE A COÛTÉ UN CORPS 71 % TROP LONG.
## `PlaneCollider.capsule_blocks()` promène un disque de `body_radius` le long du segment
## `−body_half_length … +body_half_length` : l'étendue réelle du corps dans l'axe vaut donc
## **`body_half_length + body_radius`**, jamais `body_half_length` seule. La demi-longueur
## mesurée sur le `.glb` (1,23) avait été versée ici telle quelle : la capsule s'étirait à
## 2,11, soit 0,88 unité de coque fantôme DEVANT le nez et autant derrière. Le joueur l'a vu
## avant le code, une fois l'overlay `--show-solids` allumé — « la zone de collision du
## vaisseau est trop longue, surtout devant » (2026-08-28).
##
## La valeur juste se déduit, elle ne se choisit pas :
## `demi-longueur de coque − body_radius`, soit `1,23 − 0,88 = 0,35`. La capsule épouse
## alors exactement la boîte du `.glb` : 2,46 dans l'axe, 1,76 en travers.
@export var body_half_length: float = 0.35

## L'étendue RÉELLE du corps dans l'axe, celle qu'un décor doit dégager. Elle existe parce
## que trois appelants la recalculaient à la main, et qu'un quatrième l'oublierait.
func body_reach() -> float:
	return body_half_length + body_radius

## Le POIDS du chasseur, dans la même unité arbitraire qu'[member EnemyData.mass].
##
## ⚠️ TOUT LE CONTRAT D'ÉCRASEMENT VIT ICI, ET NON SUR LES FICHES D'EN FACE. Ce qui décide
## qu'un éclaireur est traversable, ce n'est pas l'éclaireur : c'est le chasseur qui lui
## rentre dedans. Régler le seuil chez lui, c'est pouvoir le déplacer d'un chiffre pour
## toute la faune — au lieu de rouvrir treize `.tres` en espérant n'en oublier aucun.
@export var mass: float = 10.0

## De combien il faut être plus lourd pour passer À TRAVERS au lieu d'être arrêté.
##
## ⚠️ SA VALEUR EST UN ARBITRAGE DE JEU, PAS DE PHYSIQUE. À 3, le Specter-9 (10 t) écrase
## tout ce qui pèse 3,33 t ou moins : les éclaireurs et l'intercepteur passent, le porteur
## de bouclier (8 t) arrête. C'est exactement la ligne que le playtest demandait — « ça
## devient injouable pendant les vagues » — sans rendre le jeu traversable pour autant.
@export var crush_mass_ratio: float = 3.0

## Points de bouclier payés par tonne écrasée.
##
## ⚠️ RIEN N'EST TRAVERSÉ GRATUITEMENT, sinon foncer dans le tas devient la stratégie
## dominante et le tir devient décoratif. À 8, un éclaireur (1 t) coûte 8 des 100 points du
## bouclier ; l'invulnérabilité d'après impact (`invuln_time`) empêche qu'une vague entière
## se facture en une image, mais la traversée reste chère.
@export var crush_damage_per_mass: float = 8.0

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
	# ⚠️ LE GARDE D'AVANT EXIGEAIT `body_half_length >= body_radius`, « un vaisseau n'est pas
	# plus large que long » — vrai de la COQUE, faux du segment de la capsule, et c'est lui
	# qui verrouillait l'erreur : il refusait précisément la valeur correcte (0,35). La
	# question à poser porte sur l'étendue, la seule grandeur comparable à la largeur.
	if body_half_length < 0.0:
		errors.append("body_half_length must be >= 0 (c'est un demi-SEGMENT, pas une demi-longueur de coque)")
	if body_reach() < body_radius:
		errors.append("etendue du corps (%.2f) < body_radius (%.2f) : un vaisseau n'est pas plus large que long"
			% [body_reach(), body_radius])
	if fire_interval <= 0.0:
		errors.append("fire_interval must be > 0")
	if mass <= 0.0 or is_inf(mass) or is_nan(mass):
		errors.append("mass must be a finite value > 0")
	if crush_mass_ratio < 1.0:
		# En dessous de 1, le chasseur écraserait des corps AUSSI LOURDS QUE LUI, voire
		# plus lourds : plus rien ne l'arrêterait, et la loi des corps n'aurait plus d'objet.
		errors.append("crush_mass_ratio must be >= 1 (below 1 the fighter goes through anything)")
	if crush_damage_per_mass < 0.0:
		errors.append("crush_damage_per_mass must be >= 0")
	if shield_max <= 0.0:
		errors.append("shield_max must be > 0")
	if lives < 1:
		errors.append("lives must be >= 1")
	return errors
