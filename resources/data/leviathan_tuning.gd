class_name LeviathanTuning
extends Resource
## Réglages du combat du Pale Leviathan, boss final (spec §8.1 : aucune valeur de
## gameplay en dur). Unités : distances en unités monde, temps en secondes, angles en
## degrés. Référence de conception : `docs/design/BOSS_PALE_LEVIATHAN.md`.
##
## LE PILIER QUE CES VALEURS DÉCRIVENT — le Harvester est un **verrou** (trois clés
## ouvrent une fenêtre, en boucle, tout repousse). Le Leviathan est un **démontage** :
## chaque phase lui arrache une partie du corps, **rien ne repousse**, et la pièce
## arrachée devient la mécanique de la phase suivante.
##
## COMMENT LES POINTS DE VIE SONT OBTENUS — jamais à l'oreille :
##
##     durée_de_phase = PV_de_la_phase / (reference_dps × occupation)
##
## `occupation` est la part du temps où le joueur peut réellement placer ses tirs sur
## une cible légitime. C'est le **vrai levier de conception** : une phase où l'on
## esquive plus qu'on ne tire a une occupation basse, donc moins de points de vie pour
## la même durée. Changer un PV sans rejouer ce calcul, c'est changer la durée d'une
## phase sans s'en apercevoir.

# ==========================================================================
# Hypothèses de dimensionnement — PAS des réglages de boss
# ==========================================================================

@export_group("Hypotheses de dimensionnement")
## Cadence soutenue du joueur à puissance 3. **La même hypothèse que le mini-boss**
## (`harvester_tuning.gd`), pour que les deux combats se comparent.
##
## Ce n'est pas une option : c'est ce qui rend la règle `durée = PV / (dps × occupation)`
## vérifiable. Sans elle, aucun invariant de durée n'est calculable.
@export var reference_dps: float = 420.0
## Vitesse maximale du chasseur (`resources/data/player_stats.gd`). Recopiée ici parce
## que `validate()` doit pouvoir juger l'aspiration **sans instancier le joueur** — un
## test headless n'a pas de scène. À tenir à jour si `PlayerStats` change.
@export var reference_player_max_speed: float = 14.0
## Fenêtre de tir minimale exploitable, en secondes. En deçà, le joueur voit la cible
## passer sans avoir le temps d'y placer une salve : la mécanique existe sur le papier
## et nulle part à l'écran. C'est la constante `MIN_WINDOW` du Harvester, transposée à
## une géométrie plutôt qu'à un minuteur.
@export var min_window: float = 2.0

# ==========================================================================
# Phase 1 — ARMOR CHOIR (le verbe : BRISER)
# ==========================================================================

@export_group("Phase 1 - Armor Choir")
@export var plate_health: float = 3200.0
@export var plate_count: int = 4
## Durée d'un tour complet de la coquille. C'est elle qui fabrique la fenêtre de tir :
## les plaques défilent, le joueur choisit son moment.
@export var shell_orbit_period: float = 12.0
## Arc face au joueur où une plaque encaisse. ⚠️ CE N'EST PAS UN NOMBRE LIBRE : avec
## `arc/360 × période`, il donne la durée pendant laquelle une plaque est atteignable.
## Trop étroit, le joueur regarde la cible passer sans pouvoir la traiter.
@export var plate_arc_deg: float = 100.0
## Généreux : la plaque bouge, elle est grosse, et viser sous un rideau de balles ne
## doit pas demander de la précision au pixel (spec §5.3).
@export var plate_hitbox_radius: float = 1.30
@export var shell_break_time: float = 2.0

@export_subgroup("Choeur d'eventails")
## Par plaque **encore debout** : moins de plaques = moins de rideau. Le retour de la
## destruction est immédiat et physique, sans qu'aucun texte ne l'explique.
@export var fan_interval: float = 2.4
@export var fan_bullets: int = 7
@export var fan_spread_deg: float = 60.0
@export var fan_speed: float = 5.0

@export_subgroup("Lance annoncee")
## ⚠️ Le réarme EST la règle du duel : c'est lui qui rend la lance esquivable.
@export var lance_windup_time: float = 1.8
@export var lance_beam_time: float = 1.2
@export var lance_half_width: float = 0.70
## Dégâts par CONTACT, et non par seconde — `PlayerShield.take_hit` accorde 1,2 s
## d'invulnérabilité par coup, donc un modèle « par seconde » serait écrêté de toute
## façon et le réglage mentirait sur ce qui se passe.
@export var lance_damage: float = 28.0
@export var lance_interval: float = 7.0

@export_subgroup("Missiles ciblables")
@export var missile_salvo_interval: float = 6.0
@export var missile_count: int = 3
@export var missile_speed: float = 4.0
## Vitesse de virage, en radians par seconde. ⚠️ Bornée, et c'est ce qui rend le missile
## esquivable : un projectile qui vire instantanément touche toujours.
@export var missile_turn_rate: float = 1.4
## Faible exprès : une salve du joueur suffit. Le missile enseigne qu'on peut
## *répondre* à un projectile, il ne doit pas devenir une éponge.
@export var missile_health: float = 40.0
@export var missile_hitbox_radius: float = 0.30
@export var missile_damage: float = 22.0

# ==========================================================================
# Phase 2 — GRAVITIC MAW (le verbe : RÉSISTER)
# ==========================================================================

@export_group("Phase 2 - Gravitic Maw")
@export var node_health: float = 2800.0
@export var node_count: int = 3
@export var node_hitbox_radius: float = 1.00
@export var pull_radius: float = 16.0
## ⚠️ DOIT rester nettement sous `reference_player_max_speed`. Au-delà, le chasseur est
## aspiré quoi qu'il fasse et la phase devient une cinématique. `validate()` refuse le
## cas, mais le calcul se fait ICI, à la main, avant d'écrire le nombre.
@export var pull_speed_max: float = 7.0
@export var debris_count: int = 10
@export var debris_speed: float = 6.0
@export var debris_damage: float = 30.0
@export var maw_pulse_interval: float = 3.0
@export var maw_pulse_bullets: int = 14
@export var spike_sweep_windup: float = 0.8
@export var spike_sweep_arc_deg: float = 40.0
@export var spike_sweep_interval: float = 5.0

# ==========================================================================
# Phase 3 — BOARDING SWARM (le verbe : PRIORISER)
# ==========================================================================

@export_group("Phase 3 - Boarding Swarm")
@export var spike_health: float = 1500.0
@export var spike_count: int = 4
@export var spike_hitbox_radius: float = 0.90
## Le noyau devient enfin touchable en permanence — mais une épine s'interpose.
@export var core_health: float = 3200.0
@export var core_hitbox_radius: float = 2.20
@export var charger_windup: float = 1.0
@export var charger_speed: float = 20.0
@export var charger_damage: float = 30.0
@export var gunner_interval: float = 1.2
@export var blocker_offset: float = 2.50
@export var escort_orbit_radius: float = 3.0
@export var transport_interval: float = 8.0
@export var transport_count: int = 2
## Un transport qui sort du champ **revient en escorte armée**. ADR-0010 a supprimé
## l'intégrité de forteresse : il n'y a plus rien à protéger derrière le joueur, et une
## jauge abstraite serait un mensonge. La sanction est donc matérielle.
@export var transport_return_delay: float = 6.0

# ==========================================================================
# Phase 4 — INTO THE MAW (le verbe : OSER)
# ==========================================================================

@export_group("Phase 4 - Into the Maw")
@export var heart_health: float = 2600.0
@export var heart_hitbox_radius: float = 1.10
## Le compte à rebours de la phase. Trop court, la descente devient aléatoire.
@export var maw_open_time: float = 12.0
@export var maw_reopen_delay: float = 8.0
## L'aspiration s'inverse en expulsion : c'est la seule sortie, donc elle est généreuse.
@export var eject_window: float = 2.0
## ⚠️ SUPÉRIEURE à la vitesse du joueur, et c'est le SUJET de la phase : on ne résiste
## plus, on entre. `validate()` vérifie ce sens-là — un réglage qui repasserait sous la
## vitesse du joueur ferait disparaître la phase sans erreur.
@export var pull_speed_max_final: float = 16.0
@export var ring_count: int = 5
@export var ring_gap_deg: float = 70.0
@export var ring_spin_base: float = 0.5
@export var ring_damage: float = 35.0
@export var ring_knockback: float = 3.0

# ==========================================================================
# Occupation visée par phase — le levier de conception
# ==========================================================================

@export_group("Occupation visee")
@export var occupancy_phase_1: float = 0.45
@export var occupancy_phase_2: float = 0.35
@export var occupancy_phase_3: float = 0.40
@export var occupancy_phase_4: float = 0.80

# ==========================================================================
# Lectures dérivées
# ==========================================================================

## Points de vie de chaque phase. Sert la jauge du HUD **et** les invariants de durée.
func phase_health(phase: int) -> float:
	match phase:
		0: return plate_health * float(plate_count)
		1: return node_health * float(node_count)
		2: return spike_health * float(spike_count) + core_health
		3: return heart_health
	return 0.0

func occupancy(phase: int) -> float:
	match phase:
		0: return occupancy_phase_1
		1: return occupancy_phase_2
		2: return occupancy_phase_3
		3: return occupancy_phase_4
	return 1.0

## Durée attendue d'une phase, en secondes, sous les hypothèses de dimensionnement.
func phase_duration(phase: int) -> float:
	var rate := reference_dps * occupancy(phase)
	return phase_health(phase) / rate if rate > 0.0 else 0.0

## Total des structures. ⚠️ C'est ce que la jauge du HUD divise : elle montre les dégâts
## cumulés sur TOUT, pas les PV d'un corps. Sur quatre phases, une jauge figée pendant
## soixante secondes dirait au joueur « tu ne fais rien ».
func total_structure() -> float:
	var total := 0.0
	for phase in 4:
		total += phase_health(phase)
	return total

## Durée pendant laquelle une plaque est atteignable à chaque passage. C'est la
## « fenêtre » de la phase 1 — née d'une géométrie, pas d'un minuteur.
func plate_window() -> float:
	return shell_orbit_period * plate_arc_deg / 360.0

# ==========================================================================
# validate() — les invariants qui empêchent un réglage sensé de casser le jeu
# ==========================================================================

func validate() -> PackedStringArray:
	var errors := PackedStringArray()

	# --- Hypothèses ------------------------------------------------------
	if reference_dps <= 0.0:
		errors.append("reference_dps must be > 0 — it is the sizing assumption, not an option")
	if reference_player_max_speed <= 0.0:
		errors.append("reference_player_max_speed must be > 0 (mirror of PlayerStats.max_speed)")
	if min_window <= 0.0:
		errors.append("min_window must be > 0")

	# --- Points de vie ---------------------------------------------------
	for value in [plate_health, node_health, spike_health, core_health, heart_health, missile_health]:
		if value <= 0.0:
			errors.append("every health pool must be > 0")
			break
	if plate_count <= 0 or node_count <= 0 or spike_count <= 0 or ring_count <= 0:
		errors.append("plate/node/spike/ring counts must be > 0")

	# --- Zones de touche -------------------------------------------------
	for value in [plate_hitbox_radius, node_hitbox_radius, spike_hitbox_radius,
			core_hitbox_radius, heart_hitbox_radius, missile_hitbox_radius]:
		if value <= 0.0:
			errors.append("every hitbox radius must be > 0")
			break

	# --- INVARIANT 1 : la fenêtre de la phase 1 existe -------------------
	# Elle naît de la rotation de la coquille, pas d'un minuteur. Trop étroite, le
	# joueur regarde les plaques défiler sans pouvoir en traiter une : la phase est
	# injouable alors que chaque valeur prise séparément est parfaitement sensée.
	if shell_orbit_period <= 0.0:
		errors.append("shell_orbit_period must be > 0")
	elif plate_arc_deg <= 0.0 or plate_arc_deg > 360.0:
		errors.append("plate_arc_deg must be in (0, 360]")
	elif plate_window() < min_window:
		errors.append("phase 1 window too short: %.1f s orbit x %.0f deg / 360 = %.2f s (need >= %.1f)"
			% [shell_orbit_period, plate_arc_deg, plate_window(), min_window])

	# --- INVARIANT 2 : la phase 2 laisse jouer ---------------------------
	# `escapes()` seul autoriserait 13,9 contre 14,0, où l'on avance à un dixième
	# d'unité par seconde : techniquement libre, injouable en fait.
	if pull_radius <= 0.0:
		errors.append("pull_radius must be > 0")
	if pull_speed_max <= 0.0:
		errors.append("pull_speed_max must be > 0")
	elif not GravityWell.escapes(pull_speed_max, reference_player_max_speed):
		errors.append("phase 2 pull %.1f >= player speed %.1f — the player is sucked in whatever they do"
			% [pull_speed_max, reference_player_max_speed])
	elif not GravityWell.leaves_room(pull_speed_max, reference_player_max_speed):
		errors.append("phase 2 pull %.1f leaves less than %.0f%% mobility against %.1f — escapable on paper, unplayable in fact"
			% [pull_speed_max, GravityWell.MIN_MOBILITY * 100.0, reference_player_max_speed])

	# --- INVARIANT 3 : la phase 4 ne se résiste PAS ----------------------
	# C'est le sujet de la phase : la règle de la phase 2 est cassée volontairement.
	# Un réglage qui repasserait sous la vitesse du joueur ferait disparaître la
	# phase sans qu'aucune erreur ne le dise.
	if pull_speed_max_final <= reference_player_max_speed:
		errors.append("phase 4 pull %.1f <= player speed %.1f — the point of the phase is that you cannot resist"
			% [pull_speed_max_final, reference_player_max_speed])

	# --- INVARIANT 4 : le cœur est abattable avec de la marge ------------
	# Un cœur qu'on ne peut tuer qu'en jouant parfaitement rend la phase 4 aléatoire.
	# On exige que le tir utile tienne dans 70 % de la fenêtre d'ouverture.
	if maw_open_time <= 0.0:
		errors.append("maw_open_time must be > 0 — it is the countdown of the phase")
	elif reference_dps > 0.0:
		var kill_time := heart_health / reference_dps
		if kill_time > maw_open_time * 0.7:
			errors.append("heart takes %.1f s to kill, more than 70%% of the %.1f s window — no room for error"
				% [kill_time, maw_open_time])
	if eject_window <= 0.0:
		errors.append("eject_window must be > 0 — it is the only way out")
	elif eject_window >= maw_open_time:
		errors.append("eject_window %.1f >= maw_open_time %.1f — the exit would open before the dive"
			% [eject_window, maw_open_time])

	# --- INVARIANT 5 : toute attaque lourde est télégraphiée -------------
	# Le télégraphe EST la règle du duel. Sans réarme, l'attaque devient imparable.
	if lance_windup_time <= 0.0:
		errors.append("lance_windup_time must be > 0 — the wind-up is what makes the beam dodgeable")
	if charger_windup <= 0.0:
		errors.append("charger_windup must be > 0 — the wind-up is what makes the charge dodgeable")
	if spike_sweep_windup <= 0.0:
		errors.append("spike_sweep_windup must be > 0 — the wind-up is what makes the sweep dodgeable")
	if missile_turn_rate < 0.0:
		errors.append("missile_turn_rate must be >= 0")
	elif missile_turn_rate > PI:
		errors.append("missile_turn_rate %.2f rad/s turns faster than half a circle per second — unavoidable"
			% missile_turn_rate)

	# --- INVARIANT 6 : les occupations sont des parts -------------------
	# Une occupation hors de (0, 1] rendrait `phase_duration()` absurde, et c'est elle
	# qui justifie chaque point de vie du tableau.
	for phase in 4:
		var value := occupancy(phase)
		if value <= 0.0 or value > 1.0:
			errors.append("occupancy of phase %d must be in (0, 1] (got %.2f)" % [phase + 1, value])

	# --- Cadences --------------------------------------------------------
	for pair in [["fan_interval", fan_interval], ["lance_interval", lance_interval],
			["missile_salvo_interval", missile_salvo_interval],
			["maw_pulse_interval", maw_pulse_interval], ["spike_sweep_interval", spike_sweep_interval],
			["gunner_interval", gunner_interval], ["transport_interval", transport_interval]]:
		if float(pair[1]) <= 0.0:
			errors.append("%s must be > 0" % pair[0])

	return errors
