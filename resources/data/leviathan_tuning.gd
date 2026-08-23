class_name LeviathanTuning
extends Resource
## Réglages du combat du Pale Leviathan, boss final (spec §8.1 : aucune valeur de
## gameplay en dur). Unités : distances en unités monde, temps en secondes, angles en
## degrés. Référence de conception : `docs/design/BOSS_PALE_LEVIATHAN.md`.
##
## LE COMBAT QUE CES VALEURS DÉCRIVENT — **deux phases, un seul geste à comprendre par
## phase** (`ADR-0020`). Le joueur brise l'armure, puis frappe le cœur. C'est tout.
##
## ⚠️ CE QUI A ÉTÉ RETIRÉ, ET POURQUOI. Le combat comptait quatre phases (armure, nœuds
## gravitiques, essaim d'abordage, plongée dans la gueule). Au playtest il a été jugé
## « mal équilibré, on ne voit pas les phases, je n'aime pas le combat » — et la partie
## s'est arrêtée en phase 1, sans que le joueur voie jamais les trois autres. Quatre
## mécaniques inédites en une minute, sans droit à l'erreur, ne s'apprennent pas : elles
## se subissent. Nœuds, épines et noyau intermédiaire ont disparu **comme cibles** ; ils
## restent à l'écran et se détachent quand l'armure cède, pour que le démontage se voie
## sans avoir à s'expliquer.
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
## et nulle part à l'écran.
@export var min_window: float = 2.0
## Durée totale visée pour le combat, en secondes, et sa tolérance. Le playtest a tranché
## « nerveux » : le boss final doit rester au-dessus du mini-boss (~30 s) sans devenir une
## épreuve d'endurance. `validate()` refuse un jeu de réglages qui sortirait de la plage —
## c'est le garde-fou qui a manqué quand le combat dérivait vers trois minutes.
@export var target_duration: float = 40.0
@export var duration_tolerance: float = 10.0

# ==========================================================================
# Phase 1 — BRISER L'ARMURE
# ==========================================================================

@export_group("Phase 1 - Briser l'armure")
## ⚠️ 950 → 1270 alors même que la phase RACCOURCIT. Ce n'est pas une contradiction :
## avant, les quatre plaques encaissaient dès qu'elles passaient dans l'arc, donc les
## dégâts du joueur s'étalaient sur les quatre et **aucune ne tombait avant la fin**.
## Une seule plaque est désormais vulnérable — celle qui est surlignée. Le feu se
## concentre, une plaque cède toutes les ~5,5 s, et le joueur voit son travail payer
## quatre fois au lieu d'une.
@export var plate_health: float = 1270.0
@export var plate_count: int = 4
## Durée d'un tour complet de la coquille. Accélérée (12 → 9 s) : c'est elle qui donne
## le tempo de la phase, et à 12 s la rotation se lisait comme une dérive lente.
@export var shell_orbit_period: float = 9.0
## Arc face au joueur où une plaque peut être exposée. ⚠️ CE N'EST PAS UN NOMBRE LIBRE :
## il doit rester **au moins égal à l'écart entre deux plaques** (360 / plate_count),
## sans quoi il existe des instants où aucune plaque n'est atteignable — le joueur tire
## dans le vide sans comprendre pourquoi. `validate()` refuse ce cas.
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
## ⚠️ RÉGLAGES SANS ATTAQUE — vérifié le 2026-08-23 : `LeviathanCombat` n'implémente
## aucune lance. Les valeurs sont conservées parce que la conception la prévoit
## (`BOSS_PALE_LEVIATHAN.md`) et que l'invariant de télégraphe la garde déjà, mais tant
## qu'aucun code ne les lit, **les régler ne change rien à l'écran**.
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
# Phase 2 — LE CŒUR
# ==========================================================================

@export_group("Phase 2 - Le coeur")
## Le cœur est exposé **en permanence** : plus de gueule qui se referme, plus de compte
## à rebours. La cible est visible du premier au dernier tir de la phase, et c'est ce
## qui rend la barre honnête — elle descend quand on tire, elle s'arrête quand on esquive.
## La pression vient de la DENSITÉ (salve circulaire, missiles, aspiration par vagues),
## jamais d'une règle nouvelle à apprendre au dernier moment.
@export var heart_health: float = 4500.0
## Élargi (1,10 → 1,60) : c'est désormais la SEULE cible de la phase. Une cible unique
## qu'on rate n'enseigne rien, elle punit.
@export var heart_hitbox_radius: float = 1.60
## Écartement de la coquille brisée, en unités monde. Purement visuel, mais c'est LUI
## qui dit « nouvelle phase » sans texte : le corps s'ouvre et le cœur apparaît.
@export var shell_open_offset: float = 2.20
@export var shell_open_time: float = 1.2

@export_subgroup("Aspiration intermittente")
## L'aspiration survit à la refonte, mais comme **pression** et non comme phase : elle
## revient par vagues, le joueur la sent, elle ne lui prend jamais les commandes.
## ⚠️ DOIT rester nettement sous `reference_player_max_speed`. Au-delà, le chasseur est
## aspiré quoi qu'il fasse et la phase devient une cinématique.
@export var pull_speed_max: float = 7.0
@export var pull_radius: float = 16.0
@export var pull_interval: float = 6.0
@export var pull_time: float = 2.5

@export_subgroup("Salve circulaire")
@export var pulse_interval: float = 3.0
@export var pulse_bullets: int = 14

# ==========================================================================
# Occupation visée par phase — le levier de conception
# ==========================================================================

@export_group("Occupation visee")
## Relevée (0,45 → 0,55) : la cible unique et surlignée fait moins chercher le joueur.
@export var occupancy_phase_1: float = 0.55
@export var occupancy_phase_2: float = 0.60

# ==========================================================================
# Lectures dérivées
# ==========================================================================

## Nombre de phases qui portent des points de vie. Le compte fait partie du contrat :
## le HUD annonce « PHASE n/N » et la jauge se remet à plein à chaque bascule.
const PHASE_COUNT := 2

## Points de vie de chaque phase. Sert la jauge du HUD **et** les invariants de durée.
func phase_health(phase: int) -> float:
	match phase:
		0: return plate_health * float(plate_count)
		1: return heart_health
	return 0.0

func occupancy(phase: int) -> float:
	match phase:
		0: return occupancy_phase_1
		1: return occupancy_phase_2
	return 1.0

## Durée attendue d'une phase, en secondes, sous les hypothèses de dimensionnement.
func phase_duration(phase: int) -> float:
	var rate := reference_dps * occupancy(phase)
	return phase_health(phase) / rate if rate > 0.0 else 0.0

## Durée attendue du combat entier. C'est la promesse faite au joueur (~40 s), et
## `validate()` la défend.
func total_duration() -> float:
	var total := 0.0
	for phase in PHASE_COUNT:
		total += phase_duration(phase)
	return total

## Total des structures, toutes phases confondues.
##
## ⚠️ N'EST PLUS LE DÉNOMINATEUR DE LA JAUGE. Il l'a été, et c'est ce qui faisait mentir
## le HUD : briser les quatre plaques ne valait que 30 % d'une barre qui comptait quatre
## phases, donc le joueur voyait « 70 % » après vingt secondes d'effort et concluait
## qu'il ne servait à rien. La jauge montre désormais la phase EN COURS. Ce total ne sert
## plus qu'au dimensionnement.
func total_structure() -> float:
	var total := 0.0
	for phase in PHASE_COUNT:
		total += phase_health(phase)
	return total

## Durée pendant laquelle une plaque donnée reste dans l'arc à chaque passage.
func plate_window() -> float:
	return shell_orbit_period * plate_arc_deg / 360.0

## Écart angulaire entre deux plaques voisines, en degrés.
func plate_spacing_deg() -> float:
	return 360.0 / float(plate_count) if plate_count > 0 else 360.0

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
	for value in [plate_health, heart_health, missile_health]:
		if value <= 0.0:
			errors.append("every health pool must be > 0")
			break
	if plate_count <= 0:
		errors.append("plate_count must be > 0")

	# --- Zones de touche -------------------------------------------------
	for value in [plate_hitbox_radius, heart_hitbox_radius, missile_hitbox_radius]:
		if value <= 0.0:
			errors.append("every hitbox radius must be > 0")
			break

	# --- INVARIANT 1 : la phase 1 offre toujours une cible ---------------
	# Une seule plaque est vulnérable à la fois, celle qui est surlignée. Si l'arc est
	# plus étroit que l'écart entre deux plaques, il existe des instants où AUCUNE
	# plaque n'est dans l'arc : le joueur tire dans le vide sans qu'on lui dise
	# pourquoi. C'était l'ancien invariant de « fenêtre », qui mesurait la mauvaise
	# grandeur — il vérifiait qu'une plaque restait assez longtemps, jamais qu'il y en
	# avait une.
	if shell_orbit_period <= 0.0:
		errors.append("shell_orbit_period must be > 0")
	elif plate_arc_deg <= 0.0 or plate_arc_deg > 360.0:
		errors.append("plate_arc_deg must be in (0, 360]")
	elif plate_arc_deg < plate_spacing_deg():
		errors.append("phase 1 arc %.0f deg is narrower than the %.0f deg between plates — there are moments with no target at all"
			% [plate_arc_deg, plate_spacing_deg()])
	elif plate_window() < min_window:
		errors.append("phase 1 window too short: %.1f s orbit x %.0f deg / 360 = %.2f s (need >= %.1f)"
			% [shell_orbit_period, plate_arc_deg, plate_window(), min_window])

	# --- INVARIANT 2 : l'aspiration de la phase 2 laisse jouer -----------
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
	if pull_time <= 0.0 or pull_interval <= 0.0:
		errors.append("pull_time and pull_interval must be > 0")
	elif pull_time >= pull_interval:
		errors.append("pull_time %.1f >= pull_interval %.1f — the pull never stops, so it is not intermittent"
			% [pull_time, pull_interval])

	# --- INVARIANT 3 : le combat tient sa durée --------------------------
	# Le garde-fou qui a manqué. Un boss dont chaque valeur est sensée peut dériver vers
	# trois minutes sans qu'aucun test ne s'en aperçoive : c'est arrivé, et il a fallu
	# un playtest pour le voir.
	if target_duration <= 0.0:
		errors.append("target_duration must be > 0 — it is the promise made to the player")
	elif duration_tolerance < 0.0:
		errors.append("duration_tolerance must be >= 0")
	else:
		var total := total_duration()
		if absf(total - target_duration) > duration_tolerance:
			errors.append("fight lasts %.0f s, outside the %.0f +/- %.0f s target — %s"
				% [total, target_duration, duration_tolerance,
					"cut health or raise occupancy" if total > target_duration else "the final boss must not be shorter than the mini-boss"])

	# --- INVARIANT 4 : chaque phase pèse dans le combat ------------------
	# Une phase de trois secondes n'est pas une phase, c'est une transition ; une phase
	# qui prend les trois quarts du combat rend l'autre décorative.
	if PHASE_COUNT > 0 and target_duration > 0.0:
		for phase in PHASE_COUNT:
			var share := phase_duration(phase) / target_duration
			if share < 0.25 or share > 0.75:
				errors.append("phase %d takes %.0f%% of the fight — a phase must carry between 25%% and 75%%"
					% [phase + 1, share * 100.0])

	# --- INVARIANT 5 : toute attaque lourde est télégraphiée -------------
	# Le télégraphe EST la règle du duel. Sans réarme, l'attaque devient imparable.
	if lance_windup_time <= 0.0:
		errors.append("lance_windup_time must be > 0 — the wind-up is what makes the beam dodgeable")
	if missile_turn_rate < 0.0:
		errors.append("missile_turn_rate must be >= 0")
	elif missile_turn_rate > PI:
		errors.append("missile_turn_rate %.2f rad/s turns faster than half a circle per second — unavoidable"
			% missile_turn_rate)

	# --- INVARIANT 6 : les occupations sont des parts -------------------
	# Une occupation hors de (0, 1] rendrait `phase_duration()` absurde, et c'est elle
	# qui justifie chaque point de vie du tableau.
	for phase in PHASE_COUNT:
		var value := occupancy(phase)
		if value <= 0.0 or value > 1.0:
			errors.append("occupancy of phase %d must be in (0, 1] (got %.2f)" % [phase + 1, value])

	# --- Cadences --------------------------------------------------------
	for pair in [["fan_interval", fan_interval], ["lance_interval", lance_interval],
			["missile_salvo_interval", missile_salvo_interval],
			["pulse_interval", pulse_interval], ["shell_open_time", shell_open_time]]:
		if float(pair[1]) <= 0.0:
			errors.append("%s must be > 0" % pair[0])

	return errors
