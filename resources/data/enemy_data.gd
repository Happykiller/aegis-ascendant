class_name EnemyData
extends Resource
## Enemy tuning values (spec §11, §22). Units: world units, seconds.

## Statistiques du joueur, chargées et non recopiées : `validate()` doit pouvoir
## dire si un puits gravitationnel lui laisse de quoi manœuvrer, et la seule
## réponse juste est celle du chasseur réel (spec §22 : aucune duplication
## silencieuse d'une valeur de gameplay).
const PLAYER_STATS := preload("res://resources/player/specter9_stats.tres")

## Trajectoire suivie. Le mouvement est DATA-DRIVEN : le contrôleur échantillonne
## EnemyPath, il ne décide de rien. Ajouter une famille, c'est choisir ici.
## L'ordre est celui de la variété perçue, pas une hiérarchie. Chaque valeur a une
## signature de mouvement qu'aucune autre n'imite (voir EnemyPath).
## ⚠️ APPENDRE en fin de liste, jamais insérer : les .tres sérialisent l'INDICE
## numérique, donc une insertion au milieu réaffecterait silencieusement la
## trajectoire de tous les ennemis existants.
enum Path { WEAVE, DIVE, ARC_CROSS, HOVER_STRAFE, SERPENTINE, SPIRAL, BOOMERANG, STRAFE_RUN,
	CRESCENT_HOOK, DRIFT }
@export var path: Path = Path.WEAVE

## Schéma de tir (`EnemyFire`). Deuxième axe de variété, orthogonal au premier :
## la trajectoire dit où va la coque, celui-ci dit où part le coup. `SINGLE` est
## l'indice 0, donc les Resources écrites avant cet axe gardent exactement leur
## comportement — un coup droit vers le bas.
## ⚠️ Même règle d'APPEND que `Path` : l'indice est ce qui est sérialisé.
enum Fire { SINGLE, NONE, FAN, AIMED, RADIAL }
@export var fire: Fire = Fire.SINGLE

## Ce que l'unité fait qui n'est PAS une balle. Une menace peut se passer de
## projectile : le puits gravitationnel ne blesse pas, il mange l'esquive.
## ⚠️ Même règle d'APPEND.
enum Effect { NONE, GRAVITY_WELL, LEECH, SHIELD_AURA }
@export var effect: Effect = Effect.NONE

## Qui pilote la position. `PATH` échantillonne `EnemyPath`, fonction pure de l'âge —
## c'est le cas des neuf familles écrites avant cet axe, et l'indice 0 le garantit.
## `HOMING` poursuit le joueur (`EnemyHoming`) : sa position accumule, donc elle ne
## peut pas être une trajectoire. C'est le seul mode qui regarde le joueur pour se
## DÉPLACER (ADR-0022).
## ⚠️ Même règle d'APPEND que les autres enums.
enum Motion { PATH, HOMING }
@export var motion: Motion = Motion.PATH

@export var display_name: String = "enemy"
@export var max_health: float = 20.0
## Downward travel speed (units/s).
@export var move_speed: float = 3.5
## Lateral sine weave: amplitude (units) and frequency (cycles/s).
@export var weave_amplitude: float = 1.5
@export var weave_frequency: float = 0.4
## Seconds between shots; enemies only fire while inside the play area.
@export var fire_interval: float = 1.9
@export var projectile: ProjectileData
## Logical hitbox radius (generous on enemies, spec §5.3 accessibility).
@export var hitbox_radius: float = 0.45
@export var score_value: int = 100

## DIVE : secondes d'approche lente avant que l'ennemi ne fonde.
@export var dive_delay: float = 1.2
## HOVER_STRAFE : ligne où l'ennemi se stabilise, et durée du vol stationnaire.
## BOOMERANG : même ligne — c'est là qu'il fait demi-tour.
@export var hold_y: float = 3.0
@export var hold_time: float = 2.2
## ARC_CROSS / SPIRAL : rayon du cercle parcouru (unités).
## CRESCENT_HOOK : règle l'ampleur de la feinte vers l'extérieur.
@export var arc_radius: float = 7.0
## CRESCENT_HOOK : instant (s) du sommet de la feinte, avant que la coupe ne l'emporte.
@export var hook_delay: float = 1.0

## Nombre de coups par salve (FAN, AIMED, RADIAL). Sans effet sur SINGLE.
@export var burst_count: int = 5

# --- Menace de proximité (EnemyReaction) -------------------------------------
#
# Un rayon de déclenchement NUL veut dire « cette unité ne réagit pas » : elle
# suit sa courbe et tire, comme les neuf familles écrites avant cet axe. C'est ce
# qui dispense d'un enum de plus pour dire « réactive ou non ».

## Distance (unités) à laquelle l'unité s'éveille et le MONTRE. L'avertissement est
## gratuit : à ce stade rien n'est encore engagé, le joueur peut faire demi-tour.
@export var alert_radius: float = 0.0
## Distance à laquelle elle s'engage — sans retour possible. Toujours < alert_radius,
## faute de quoi l'unité passerait de l'inertie à la détonation sans un mot.
@export var trigger_radius: float = 0.0
## Sursis avant l'engagement, en secondes. À zéro (le défaut, toutes les unités sauf la
## mine), franchir `trigger_radius` engage IMMÉDIATEMENT — le comportement d'origine.
##
## ⚠️ AU-DESSUS DE ZÉRO, L'UNITÉ S'ACCORDE UNE FENÊTRE DE RETRAIT. Elle réagit dès l'entrée
## mais ne s'engage qu'à l'échéance ; ressortir avant la referme. Ça n'annule PAS le
## télégraphe — l'invariant d'`EnemyReaction` tient — ça insère une étape avant lui.
@export var arm_grace: float = 0.0
## Durée du télégraphe (s). La spec §11.2 impose 300 à 800 ms : en deçà le joueur
## n'a pas le temps de lire, au-delà la menace cesse d'en être une.
@export var windup_time: float = 0.6
## Durée de la charge (s) : la salve part, l'aspiration tire, l'aura tient.
@export var active_time: float = 0.4
## Temps mort avant réarmement (s). ZÉRO = usage unique — la mine est vidée et le
## restera. Une mine qui se réarme est une zone interdite ; une mine à usage unique
## est un obstacle qu'on peut dépenser. Ce ne sont pas les mêmes règles du jeu.
@export var rearm_time: float = 0.0

## GRAVITY_WELL : portée (unités) et vitesse d'aspiration au centre (unités/s).
@export var pull_radius: float = 0.0
@export var pull_speed_max: float = 0.0

## HOMING : vitesse de virage (radians/s).
##
## ⚠️ C'est elle qui rend la poursuite ESQUIVABLE. Un poursuivant qui vire
## instantanément touche toujours, et le joueur n'a plus que le tir à lui opposer.
## Bornée, il peut le semer par un crochet — la même raison qui borne le virage des
## missiles du boss (`TargetableProjectile.turn_rate`).
@export var homing_turn_rate: float = 0.0
## HOMING : secondes de poursuite avant que l'unité ne rompe et file droit.
##
## ⚠️ CE N'EST PAS UN RÉGLAGE DE DIFFICULTÉ, C'EST UNE SÉCURITÉ DE POOL. Une
## trajectoire finit toujours par sortir du champ — c'est ce qui libère son entrée.
## Une poursuite, non : un poursuivant qui rate sa proie tourne indéfiniment à
## l'intérieur des bornes et gèle sa place à vie. Passé ce délai il cesse de virer,
## donc il sort par un bord comme tout le monde.
@export var chase_time: float = 8.0

## SHIELD_AURA : rayon (unités) dans lequel les AUTRES ennemis deviennent
## invulnérables. Passif : il n'y a ni télégraphe ni déclenchement — tant que le
## porteur vit, la bulle tient.
##
## ⚠️ LE PORTEUR NE SE COUVRE JAMAIS LUI-MÊME. C'est toute la mécanique : sans cette
## règle il serait invulnérable et immortel, et la « cible prioritaire » deviendrait
## une cible impossible.
@export var aura_radius: float = 0.0

## LEECH : part de la vitesse du joueur volée tant que l'unité est accrochée, et
## drain de bouclier par seconde.
##
## ⚠️ Le drain est CADENCÉ PAR L'INVULNÉRABILITÉ du chasseur (1,2 s après impact),
## pas par une valeur d'ici : le bouclier ne peut pas se vider en continu. La menace
## réelle de la sangsue est le frein, pas les dégâts.
@export var drag_factor: float = 0.0
@export var drain_per_second: float = 0.0

# --- Coque articulée (EnemyPose) ---------------------------------------------

## Préfixe des pièces mobiles à ouvrir pendant le télégraphe : "Segment" pour la
## Choir Mine, "Petal" pour le Null Maw. Vide = coque rigide, comme les neuf
## familles écrites avant celle-ci.
@export var moving_part_prefix: String = ""
## Ouverture à pleine charge, en degrés.
##
## ⚠️ Cette valeur n'est pas un goût : c'est le DÉBATTEMENT MÉCANIQUE mesuré par la
## forge sur la coque, au-delà duquel une pièce traverse sa voisine. Il est consigné
## dans le compte-rendu du brief de la coque. La régler à l'œil, c'est prendre le
## risque d'une auto-intersection qu'aucune pose fixe ne montre.
@export var open_angle_deg: float = 0.0
## Coulissement des pièces vers l'extérieur à pleine ouverture, en fraction de leur
## propre rayon. Zéro = elles pivotent sur place.
##
## ⚠️ Il existe parce que le pivot SEUL ne se voit pas : 45 degrés mesurés et testés
## restent invisibles sur un objet de 46 pixels vu de dessus, sous le bloom. Ce qui
## se lit à cette taille est l'ENVELOPPE globale. Comme `open_angle_deg`, la valeur
## est un débattement mesuré par la forge — ici contre la couronne de modules de
## l'équateur, que le pivot n'approche jamais.
@export var open_spread: float = 0.0

func validate() -> PackedStringArray:
	var errors := PackedStringArray()
	if max_health <= 0.0:
		errors.append("max_health must be > 0")
	if move_speed <= 0.0:
		errors.append("move_speed must be > 0")
	if fire_interval <= 0.0:
		errors.append("fire_interval must be > 0")
	if hitbox_radius <= 0.0:
		errors.append("hitbox_radius must be > 0")
	if score_value < 0:
		errors.append("score_value must be >= 0")
	if path == Path.DIVE and dive_delay < 0.0:
		errors.append("dive_delay must be >= 0")
	if path == Path.HOVER_STRAFE and hold_time <= 0.0:
		errors.append("hold_time must be > 0 for HOVER_STRAFE")
	if (path == Path.ARC_CROSS or path == Path.SPIRAL) and arc_radius <= 0.0:
		errors.append("arc_radius must be > 0 for ARC_CROSS/SPIRAL")
	if path == Path.CRESCENT_HOOK:
		if arc_radius <= 0.0:
			errors.append("arc_radius must be > 0 for CRESCENT_HOOK")
		if hook_delay <= 0.0:
			# Division par hook_delay dans la trajectoire : zéro n'est pas seulement
			# absurde, c'est une NaN qui se propagerait dans la position.
			errors.append("hook_delay must be > 0 for CRESCENT_HOOK")
	errors.append_array(_validate_fire())
	errors.append_array(_validate_reaction())
	errors.append_array(_validate_effect())
	errors.append_array(_validate_pose())
	errors.append_array(_validate_motion())
	errors.append_array(_validate_leech())
	errors.append_array(_validate_aura())
	return errors


## Une unité qui ne tire pas n'a pas besoin de munition — mais une unité qui tire
## sans projectile est une salve muette qu'aucune erreur ne signalerait en jeu.
func _validate_fire() -> PackedStringArray:
	var errors := PackedStringArray()
	if fire == Fire.NONE:
		return errors
	if projectile == null:
		errors.append("projectile is required unless fire is NONE")
	else:
		errors.append_array(projectile.validate())
	# Un éventail d'un seul coup n'est pas un éventail : c'est un SINGLE qui se
	# ment. La règle de variété se garde ici, pas seulement dans les tests.
	if fire != Fire.SINGLE and burst_count < 2:
		errors.append("burst_count must be >= 2 for FAN/AIMED/RADIAL")
	if fire == Fire.RADIAL and burst_count < 3:
		errors.append("burst_count must be >= 3 for RADIAL (a ring needs a ring)")
	return errors


func _validate_reaction() -> PackedStringArray:
	var errors := PackedStringArray()
	if not EnemyReaction.is_reactive(self):
		return errors
	if alert_radius <= trigger_radius:
		# Sans marge d'éveil, l'unité passe de l'inertie à l'engagement dans la même
		# image : le joueur n'a rien vu venir, et le télégraphe ne sert plus à rien.
		errors.append("alert_radius must be > trigger_radius when the unit reacts")
	if windup_time < 0.3 or windup_time > 0.8:
		# Spec §11.2 : la fenêtre de lecture n'est pas un goût, c'est un contrat.
		errors.append("windup_time must be between 0.3 and 0.8 s (spec §11.2 telegraph)")
	if active_time <= 0.0:
		errors.append("active_time must be > 0 when the unit reacts")
	if rearm_time < 0.0:
		errors.append("rearm_time must be >= 0 (zero means single use)")
	if arm_grace < 0.0:
		errors.append("arm_grace must be >= 0 (zero means: no reprieve, engage on contact)")
	if arm_grace > 0.0 and arm_grace >= active_time + windup_time + rearm_time + 4.0:
		# Un sursis plus long que le cycle entier de l'unité la rendrait inoffensive sans
		# que rien ne le dise : elle se rearmerait avant d'avoir jamais tiré.
		errors.append("arm_grace is longer than the whole reaction cycle — the unit would never fire")
	return errors


func _validate_motion() -> PackedStringArray:
	var errors := PackedStringArray()
	if motion != Motion.HOMING:
		return errors
	if homing_turn_rate <= 0.0:
		# Sans virage, la poursuite est une ligne droite : l'unité rate le joueur à
		# la première esquive et ne revient jamais. Silencieux, et ruineux.
		errors.append("homing_turn_rate must be > 0 for HOMING")
	if chase_time <= 0.0:
		# Zéro voudrait dire « ne poursuit jamais » ; l'absence de borne, elle,
		# voudrait dire « gèle une entrée de pool à vie ».
		errors.append("chase_time must be > 0 for HOMING (it is the pool's safety net)")
	return errors


func _validate_leech() -> PackedStringArray:
	var errors := PackedStringArray()
	if effect != Effect.LEECH:
		return errors
	if drag_factor <= 0.0:
		errors.append("drag_factor must be > 0 for LEECH")
	elif drag_factor > PlayerFighterController.MAX_EXTERNAL_DRAG:
		# Le pilote garde 40 % de sa mobilité quoi qu'il arrive — même invariant que
		# le puits gravitationnel, et pour la même raison : en deçà, l'esquive devient
		# une loterie et la menace cesse d'en être une.
		errors.append("drag_factor above %.2f leaves no room to manoeuvre"
			% PlayerFighterController.MAX_EXTERNAL_DRAG)
	if drain_per_second < 0.0:
		errors.append("drain_per_second must be >= 0")
	if not EnemyReaction.is_reactive(self):
		errors.append("LEECH requires a trigger_radius (it must catch the player first)")
	return errors


func _validate_aura() -> PackedStringArray:
	var errors := PackedStringArray()
	if effect != Effect.SHIELD_AURA:
		return errors
	if aura_radius <= 0.0:
		errors.append("aura_radius must be > 0 for SHIELD_AURA")
	if EnemyReaction.is_reactive(self):
		# Une aura qui se déclencherait serait une aura qu'on peut attendre. Celle-ci
		# tient tant que le porteur vit : c'est ce qui force à le viser LUI.
		errors.append("SHIELD_AURA is passive and must not declare a trigger_radius")
	return errors


func _validate_pose() -> PackedStringArray:
	var errors := PackedStringArray()
	if moving_part_prefix.is_empty():
		return errors
	if open_angle_deg <= 0.0:
		errors.append("open_angle_deg must be > 0 when moving_part_prefix is set")
	elif open_angle_deg > EnemyPose.MAX_OPEN_DEG:
		errors.append("open_angle_deg above %.0f would drive a part through its neighbour"
			% EnemyPose.MAX_OPEN_DEG)
	if open_spread < 0.0 or open_spread > EnemyPose.MAX_SPREAD:
		errors.append("open_spread must be between 0 and %.2f of the part radius"
			% EnemyPose.MAX_SPREAD)
	return errors


func _validate_effect() -> PackedStringArray:
	var errors := PackedStringArray()
	if effect != Effect.GRAVITY_WELL:
		return errors
	if pull_radius <= 0.0:
		errors.append("pull_radius must be > 0 for GRAVITY_WELL")
	if pull_speed_max <= 0.0:
		errors.append("pull_speed_max must be > 0 for GRAVITY_WELL")
	elif not GravityWell.leaves_room(pull_speed_max, PLAYER_STATS.max_speed):
		# Le même invariant que la phase gravitique du boss, pour la même raison :
		# une aspiration à laquelle on ne peut rien opposer n'est plus un danger,
		# c'est une cinématique. Sur une MINE c'est pire — le joueur choisit de
		# s'approcher, il doit pouvoir choisir de repartir.
		errors.append("pull_speed_max leaves no room to manoeuvre (max %.1f for a %.1f u/s fighter)"
			% [PLAYER_STATS.max_speed * (1.0 - GravityWell.MIN_MOBILITY), PLAYER_STATS.max_speed])
	if not EnemyReaction.is_reactive(self):
		errors.append("GRAVITY_WELL requires a trigger_radius (it is a reaction, not a passive)")
	return errors
