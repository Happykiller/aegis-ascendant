class_name LeviathanTuning
extends Resource
## Réglages du combat du Pale Leviathan, boss final (spec §8.1 : aucune valeur de
## gameplay en dur). Unités : distances en unités monde, temps en secondes, angles en
## degrés. Décision de référence : `ADR-0021`.
##
## LE COMBAT QUE CES VALEURS DÉCRIVENT — **trois cycles**, chacun fait de deux temps :
##
##     BRISER L'ARMURE  →  PLONGER DANS LE NOYAU  →  éjecté  →  (l'armure revient, amoindrie)
##
## Cycle 1 : 4 plaques, 4 tourelles-épines. Cycle 2 : 3. Cycle 3 : 2. Le boss se dégrade
## visiblement et chaque cycle est plus court que le précédent — la montée en intensité
## vient de la STRUCTURE, pas d'un réglage de densité.
##
## ⚠️ POURQUOI DEUX REFONTES EN UNE JOURNÉE. Le combat a d'abord eu quatre phases, chacune
## avec sa mécanique inédite : le joueur a abandonné pendant la première et n'a jamais vu
## les trois autres. ADR-0020 l'a ramené à deux phases linéaires : mécaniquement correct,
## mais le playtest a rendu « extrêmement lancinant — on arrose les plaques sans faire
## gaffe en attendant qu'elles disparaissent », et surtout deux choses ne se comprenaient
## pas à l'écran : à quoi servaient les épines, et qu'il fallait frapper le noyau.
##
## D'où les trois changements que ces valeurs portent :
##   1. **Les épines TIRENT** (tourelles laser télégraphiées), et chaque plaque brisée en
##      fait tomber une. Casser une plaque retire une menace IDENTIFIABLE — le rideau
##      s'allège d'un laser, pas d'un septième d'éventail que personne ne compte.
##   2. **On entre dans le noyau.** La cible ne se devine plus : le corps s'ouvre, le
##      chasseur y est aspiré, et le flux d'énergie remplit l'écran.
##   3. **Les plaques tombent VITE** (1270 → 460 PV). Le grief est le temps passé à
##      arroser sans décision ; on le divise par presque trois.
##
## COMMENT LES POINTS DE VIE SONT OBTENUS — jamais à l'oreille :
##
##     durée = PV / (reference_dps × occupation)
##
## `occupation` est la part du temps où le joueur peut réellement placer ses tirs sur une
## cible légitime. C'est le **vrai levier de conception**.

# ==========================================================================
# Hypothèses de dimensionnement — PAS des réglages de boss
# ==========================================================================

@export_group("Hypotheses de dimensionnement")
## Cadence soutenue du joueur à puissance 3. **La même hypothèse que le mini-boss**
## (`harvester_tuning.gd`), pour que les deux combats se comparent.
##
## ⚠️ C'est la cadence contre une cible LARGE — les quatre plaques de l'armure, qu'aucune
## balle ne rate. 420 dps, ce sont les quatre canons de puissance 3 qui portent tous
## (4 × 10 PV à 10,42 salves/s = 417). Elle ne vaut PAS contre le flux : voir
## `flux_reference_dps`.
@export var reference_dps: float = 420.0
## Cadence du même joueur contre le FLUX, une cible de 1,80 m qui dérive de 1,60 m.
##
## ⚠️ POURQUOI DEUX HYPOTHÈSES ET NON UNE. Le combat a longtemps dimensionné ses deux
## cibles avec `reference_dps`, et c'est ce qui l'a fait dérailler : sur une plaque large
## les canons d'aile (±16°) et de bout d'aile (±31°) portent, sur le flux ils partent à
## côté. Seuls les canons de nez comptent — deux à puissance 3, soit **208 dps**.
## Playtest du 2026-08-25 à puissance MAXIMALE : six plongées au lieu de trois, 177 dps
## réellement placés dans le flux. L'hypothèse à 420 était optimiste d'un facteur ~2,4, et
## l'invariant 5 la validait sans broncher parce qu'il se comparait à elle-même.
@export var flux_reference_dps: float = 208.0
## Vitesse maximale du chasseur (`resources/data/player_stats.gd`). Recopiée ici parce
## que `validate()` doit pouvoir juger l'aspiration **sans instancier le joueur**.
@export var reference_player_max_speed: float = 14.0
## Fenêtre de tir minimale exploitable, en secondes.
@export var min_window: float = 2.0
## Durée totale visée, et sa tolérance. Le garde-fou qui a manqué deux fois : chaque
## valeur peut rester sensée pendant que le combat dérive vers trois minutes.
@export var target_duration: float = 40.0
@export var duration_tolerance: float = 10.0

# ==========================================================================
# La structure en cycles
# ==========================================================================

@export_group("Cycles")
## Trois tours d'armure et trois plongées. ⚠️ Ce n'est PAS un plafond de durée : si le
## joueur tire mal dans le noyau, le flux survit et un cycle de plus s'ouvre (avec le
## plancher de plaques). Un boss qui mourrait au troisième cycle quoi qu'il arrive
## avancerait sur un compteur, pas sur ce que le joueur a fait.
@export var cycle_count: int = 3
## Plaques du premier cycle. Chaque cycle en retire une.
@export var plate_count: int = 4
## Plancher : en dessous, l'armure ne ferait plus obstacle et le cycle serait une
## formalité de deux secondes.
@export var plate_count_min: int = 2

# ==========================================================================
# Temps 1 — BRISER L'ARMURE
# ==========================================================================

@export_group("Temps 1 - Briser l'armure")
## ⚠️ 1270 → 460. Le grief du playtest est le TEMPS passé à arroser sans décision : la
## première salve d'armure tombe de ~22 s à ~8 s, et une plaque cède toutes les 2 s.
@export var plate_health: float = 460.0
## Durée d'un aller-retour complet du balancement de la coquille — le tempo du temps 1.
@export var shell_orbit_period: float = 9.0
## Amplitude du balancement de la coquille, en degrés de part et d'autre du joueur.
##
## ⚠️ LA COQUILLE NE TOURNE PLUS EN ROND, ELLE FAIT FACE. L'armure ne couvre que 198°
## (un CROISSANT — le nœud s'appelle `Shell_Crescent`) : en rotation continue, son vide
## se présentait au joueur 27 % du temps au premier cycle et 37 % au deuxième, soit deux
## à trois secondes par tour sans rien à tirer. C'est exactement le « lancinant » du
## playtest, et aucun réglage de vitesse ne l'enlevait — c'est de la géométrie.
##
## Le croissant est donc tenu face au joueur et balance autour de lui. Mesuré sur les
## azimuts réels : à ±60° les quatre plaques passent en tête à tour de rôle et le vide
## ne se présente JAMAIS, sur les trois cycles. Le plafond sûr est ±131° (4 plaques),
## ±114° (3) et ±117° (2) : 60 laisse la marge à tous.
@export var shell_sway_deg: float = 60.0
## Arc face au joueur où une plaque peut être exposée, **au premier cycle**.
## ⚠️ C'est un PLANCHER, pas une constante : voir `effective_arc_deg()`. Quand il ne
## reste que trois puis deux plaques, l'écart entre elles grandit, et un arc fixe
## laisserait des instants sans aucune cible — le joueur tirerait dans le vide sans
## qu'on lui dise pourquoi.
@export var plate_arc_deg: float = 100.0
## Généreux : la plaque bouge, elle est grosse, et viser sous un rideau de balles ne
## doit pas demander de la précision au pixel (spec §5.3).
@export var plate_hitbox_radius: float = 1.30
@export var shell_break_time: float = 2.0

@export_subgroup("Choeur d'eventails")
## Par plaque **encore debout** : moins de plaques = moins de rideau.
@export var fan_interval: float = 2.4
@export var fan_bullets: int = 7
@export var fan_spread_deg: float = 60.0
@export var fan_speed: float = 5.0

@export_subgroup("Tourelles-epines")
## ⚠️ CES RÉGLAGES ÉTAIENT MORTS. Le groupe s'appelait « Lance annoncée », décrivait une
## attaque que personne n'avait câblée, et `validate()` gardait son télégraphe depuis des
## semaines — un invariant sur une attaque qui n'existait pas. Les épines les emploient
## enfin : chacune est une tourelle laser, et **chaque plaque brisée en fait tomber une**.
## C'est ce qui donne un sens visible à la destruction d'une plaque.
@export var spine_windup_time: float = 1.0
@export var spine_beam_time: float = 0.9
@export var spine_recover_time: float = 1.3
@export var spine_half_width: float = 0.35
## Dégâts par CONTACT, et non par seconde — `PlayerShield.take_hit` accorde 1,2 s
## d'invulnérabilité par coup, donc un modèle « par seconde » serait écrêté de toute
## façon et le réglage mentirait sur ce qui se passe.
@export var spine_damage: float = 24.0
## Décalage entre deux tirs d'une même épine. Les épines sont déphasées entre elles :
## quatre lasers simultanés seraient un mur, quatre lasers qui se relaient sont une danse.
@export var spine_interval: float = 3.2
## Portée du faisceau, en unités du plan.
@export var spine_range: float = 26.0

@export_subgroup("Missiles ciblables")
@export var missile_salvo_interval: float = 6.0
@export var missile_count: int = 3
@export var missile_speed: float = 4.0
## Vitesse de virage, en radians par seconde. ⚠️ Bornée, et c'est ce qui rend le missile
## esquivable : un projectile qui vire instantanément touche toujours.
@export var missile_turn_rate: float = 1.4
@export var missile_health: float = 40.0
@export var missile_hitbox_radius: float = 0.30
@export var missile_damage: float = 22.0

# ==========================================================================
# Temps 2 — PLONGER DANS LE NOYAU
# ==========================================================================

@export_group("Temps 2 - Plonger dans le noyau")
## Le flux d'énergie au centre du noyau — la seule chose qui tue vraiment ce boss.
##
## Dimensionné pour tomber au TROISIÈME passage : 2400 PV / 3 = 800 PV par plongée, contre
## 884 atteignables (`flux_reference_dps` × `occupancy_dive` × `dive_time`). Le joueur
## mesuré au playtest du 2026-08-25 place ~883 PV par plongée : il tue donc le flux au
## cours du **troisième** passage, avec de la marge, jamais au deuxième (il lui en faudrait
## 1200).
##
## ⚠️ IL VALAIT 5300, ET C'ÉTAIT LE DÉFAUT LE PLUS COÛTEUX DU RÉGLAGE. Le chiffre était
## calibré contre `reference_dps` — la cadence sur une cible large — et tombait à **99 %**
## du plafond que l'invariant 5 autorise (bande permise : 55 à 100 %). Il n'y avait pas de
## marge, il y avait 1 % : la moindre imperfection ouvrait un cycle de plus. À puissance
## maximale, le playtest en a ouvert **trois**.
## ⚠️ Le défaut décrit une configuration SANS anneaux (le script n'en porte aucun) : le
## noyau y est atteignable en permanence, il lui faut donc davantage de santé que dans le
## réglage livré. Les deux valeurs décrivent deux jeux différents, chacun cohérent — c'est
## `validate()` qui l'impose, pas une convention.
@export var flux_health: float = 1400.0
## Large : le flux remplit le noyau, on ne le rate pas. Ce n'est pas un test d'adresse,
## c'est une récompense — le joueur a brisé une armure pour arriver là.
@export var flux_hitbox_radius: float = 1.80
## Le flux dérive dans le noyau : assez pour qu'on suive, pas assez pour qu'on cherche.
## Le blindage rotatif du réacteur (Reactor Chamber, plan du 2026-08-27).
##
## ⚠️ VIDE = COMPORTEMENT D'AVANT. Sans anneau, le flux est atteignable pendant toute la
## plongée, exactement comme avant ce chantier. C'est ce qui garde les tests existants
## comparables, et ce qui permet de désarmer le puzzle si le playtest le condamne.
@export var reactor_rings: Array[ReactorRing] = []

## Part de la plongée pendant laquelle un joueur qui JOUE BIEN a son corridor ouvert.
##
## ⚠️ C'EST UNE ESTIMATION, ET ELLE EST NOMMÉE POUR ÇA. Un joueur immobile n'aurait que
## ~13 % (le produit des deux couvertures d'anneaux) ; un joueur qui suit l'ouverture a
## bien davantage, borné par son déplacement. 0,45 est le point de départ — **à mesurer en
## jouant**, avec le sous-agent `balance-prober`.
##
## Elle entre dans l'invariant de portée ci-dessous : sans elle, on aurait armé le réacteur
## d'un blindage tout en continuant de calculer les dégâts atteignables comme s'il n'y en
## avait pas. C'est le calibrage silencieux qu'`ADR-0024` a coûté au projet.
@export_range(0.05, 1.0) var ring_occupancy: float = 0.45

## Marge entre la coque du chasseur et la face d'un mur. Sa hitbox fait 0,25 de rayon, mais
## c'est le MODÈLE qu'on voit s'encastrer : la marge se règle sur ce qui se regarde.
@export var wall_clearance: float = 0.55

# --- Le laser balayant du réacteur (lot 2) ----------------------------------

## Vitesse de balayage, en degrés par seconde. **Négative** : à contresens de l'anneau
## extérieur, pour que le laser et les ouvertures se croisent souvent au lieu de dériver
## ensemble.
##
## ⚠️ SIMULÉ AVANT D'ÊTRE ÉCRIT, sur trois minutes : un corridor **libre** — ouvert ET hors
## du faisceau — existe **100 % du temps**, pire blocage 0,00 s. Le laser met la pression,
## il ne condamne jamais. C'est la même exigence que pour les anneaux eux-mêmes.
# --- Les nodes orbitaux (lot 3) ---------------------------------------------

## Combien de verrous énergétiques tournent autour du réacteur. Zéro les désactive
## entièrement — le comportement des lots 1 et 2.
@export_range(0, 6) var node_count: int = 4
## ⚠️ 90 -> 55 APRÈS PLAYTEST. Quatre verrous de 90 PV plus un corridor à trouver ne
## tenaient pas dans cinq secondes : l'opérateur ne remplissait aucun quota, et le combat
## ne convergeait plus. `ring_occupancy` était annoncée comme une ESTIMATION à mesurer en
## jouant — c'est fait, et elle était optimiste.
@export var node_health: float = 55.0
## Rayon d'orbite. ⚠️ AU-DELÀ DE L'ANNEAU EXTÉRIEUR (6,2) : les nodes doivent être
## atteignables SANS corridor, sinon le joueur devrait ouvrir le blindage pour détruire ce
## qui verrouille le blindage.
@export var node_orbit_radius: float = 7.6
@export var node_orbit_deg: float = 21.0
@export var node_hitbox_radius: float = 0.62

@export var sweep_speed_deg: float = -29.0
## Portée du faisceau depuis le centre du réacteur, en unités.
@export var sweep_range: float = 16.0
## Demi-largeur mortelle du faisceau.
@export var sweep_half_width: float = 0.55
## Dégâts au contact, par image touchée.
@export var sweep_damage: float = 14.0
## Silence d'ouverture : le faisceau est visible mais INOFFENSIF pendant ce temps, à chaque
## entrée dans le noyau. ⚠️ Sans lui, le joueur pourrait naître dans un laser déjà armé —
## et une mort qu'on ne pouvait pas lire venir n'est pas une difficulté, c'est une injustice.
@export var sweep_arm_delay: float = 1.1

@export var flux_drift_radius: float = 1.60
@export var flux_drift_period: float = 3.4

@export_subgroup("Entree, sejour, ejection")
## Aspiration + autopilote + glissement de caméra. C'est la seule séquence non jouable
## du combat, donc elle est courte.
@export var dive_enter_time: float = 1.4
## Le temps de tir dans le noyau. ⚠️ Court EXPRÈS : « on n'aurait pas énormément de temps
## pour tirer dessus avant d'être à nouveau éjecté ».
## ⚠️ ELLE N'A PAS BOUGÉ, ET C'EST LE RÉSULTAT LE PLUS IMPORTANT DU LOT 3. Le blindage et
## les verrous auraient pu la faire passer à 14 s — c'était le premier réglage essayé, et il
## faisait durer le combat 67 s au lieu de 40. Deux gardes l'ont refusé : « la plongée est
## courte exprès » et « le combat tient sa promesse ». La conséquence est tombée là où elle
## devait, sur la SANTÉ DU FLUX : le noyau n'est atteignable qu'une fraction du temps, il
## lui faut donc bien moins de points de vie pour le même combat.
@export var dive_time: float = 5.0
@export var dive_eject_time: float = 1.0
## Aspiration qui tire le chasseur vers l'ouverture. ⚠️ DOIT rester sous
## `reference_player_max_speed` : le joueur entre parce qu'il le veut, l'aspiration
## l'accompagne. Au-delà, la phase devient une cinématique.
@export var pull_speed_max: float = 7.0
@export var pull_radius: float = 16.0

@export_subgroup("Le noyau ouvert")
## Écartement de la coquille quand le noyau s'ouvre. C'est le télégraphe de la plongée :
## le corps s'ouvre, donc il y a quelque chose à l'intérieur.
@export var shell_open_offset: float = 2.20
@export var shell_open_time: float = 0.9
## Rayon de la paroi intérieure du noyau, construite au vol pendant la plongée.
@export var chamber_radius: float = 7.0

# ==========================================================================
# Occupation visée — le levier de conception
# ==========================================================================

@export_group("Occupation visee")
## Temps 1 : la cible unique et surlignée fait moins chercher le joueur.
@export var occupancy_armor: float = 0.55
## Temps 2 : le flux est gros, proche et seul. On tire presque tout le temps.
@export var occupancy_dive: float = 0.85

# ==========================================================================
# Lectures dérivées
# ==========================================================================

## Plaques debout au début du cycle `cycle` (0-indexé), plancher compris.
func plates_for_cycle(cycle: int) -> int:
	return maxi(plate_count - cycle, plate_count_min)

## Arc d'exposition réellement appliqué quand `alive` plaques tiennent encore.
##
## ⚠️ L'ARC S'ÉLARGIT QUAND LE BOSS S'AFFAIBLIT. Quatre plaques sont espacées de 90°, trois
## de 120°, deux de 180° : un arc fixe de 100° laisserait, dès le deuxième cycle, des
## instants où AUCUNE plaque n'est atteignable. Le joueur tirerait dans le vide sans
## comprendre — exactement le genre de panne qui ne produit ni erreur ni test rouge.
## Le boss dégradé couvre moins bien : c'est cohérent, et c'est surtout jouable.
func effective_arc_deg(alive: int) -> float:
	if alive <= 0:
		return plate_arc_deg
	return maxf(plate_arc_deg, 360.0 / float(alive))

## Durée du temps 1 pour un cycle donné.
func armor_duration(cycle: int) -> float:
	var rate := reference_dps * occupancy_armor
	if rate <= 0.0:
		return 0.0
	return plate_health * float(plates_for_cycle(cycle)) / rate

## Durée d'une plongée complète, entrée et éjection comprises.
func dive_duration() -> float:
	return dive_enter_time + dive_time + dive_eject_time

## Durée attendue du combat entier, sous les hypothèses de dimensionnement.
func total_duration() -> float:
	var total := 0.0
	for cycle in cycle_count:
		total += armor_duration(cycle) + dive_duration()
	return total

## Part du combat passée à briser l'armure (le reste est passé dans le noyau).
func armor_share() -> float:
	var total := total_duration()
	if total <= 0.0:
		return 0.0
	var armor := 0.0
	for cycle in cycle_count:
		armor += armor_duration(cycle)
	return armor / total

## Total des points de vie du combat — dimensionnement uniquement.
##
## ⚠️ N'EST PAS LE DÉNOMINATEUR DE LA JAUGE. Il l'a été, et c'est ce qui faisait mentir le
## HUD : briser toute l'armure ne valait que 30 % d'une barre qui comptait quatre phases.
func total_structure() -> float:
	var total := flux_health
	for cycle in cycle_count:
		total += plate_health * float(plates_for_cycle(cycle))
	return total

## Durée pendant laquelle une plaque reste dans l'arc à chaque passage, au premier cycle.
func plate_window() -> float:
	return shell_orbit_period * plate_arc_deg / 360.0

## Points de vie qu'il faut placer par plongée pour tuer le flux en `cycle_count` passages.
## Le temps réellement passé à tirer sur le NOYAU pendant une plongée : la durée du séjour,
## moins ce qu'il faut pour abattre les verrous. Tant qu'un node vit, le flux est
## intouchable — ces secondes-là ne comptent pas.
func flux_damage_window() -> float:
	var clearing := 0.0
	if node_count > 0:
		clearing = float(node_count) * node_health / maxf(flux_reference_dps, 0.001)
	return maxf(dive_time - clearing, 0.0)

## Dégâts qu'un joueur de référence peut réellement placer sur le flux en une plongée.
##
## ⚠️ EXPOSÉ PARCE QUE LA FORMULE ÉTAIT RECOPIÉE. Trois tests la refaisaient à la main —
## `dps × occupancy × dive_time` — et deux d'entre eux sont devenus faux le jour où le
## blindage et les verrous ont retranché leur part. Une formule dupliquée ne peut que
## diverger de celle qui décide ; c'est le même remède que `flux_drift_envelope()`.
func flux_reachable_per_dive() -> float:
	var shielded := ring_occupancy if not reactor_rings.is_empty() else 1.0
	return flux_reference_dps * occupancy_dive * flux_damage_window() * shielded

func flux_damage_per_dive() -> float:
	return flux_health / float(maxi(cycle_count, 1))

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

	# --- Structure -------------------------------------------------------
	if cycle_count <= 0:
		errors.append("cycle_count must be > 0")
	if plate_count <= 0:
		errors.append("plate_count must be > 0")
	elif plate_count_min <= 0 or plate_count_min > plate_count:
		errors.append("plate_count_min must be in [1, plate_count]")

	# --- Points de vie et zones de touche --------------------------------
	for value in [plate_health, flux_health, missile_health]:
		if value <= 0.0:
			errors.append("every health pool must be > 0")
			break
	for value in [plate_hitbox_radius, flux_hitbox_radius, missile_hitbox_radius]:
		if value <= 0.0:
			errors.append("every hitbox radius must be > 0")
			break

	# --- INVARIANT 1 : le temps 1 offre toujours une cible ---------------
	# Une seule plaque est vulnérable à la fois, celle qui est surlignée, et l'arc doit
	# rester assez large pour qu'il y en ait toujours une.
	#
	# ⚠️ CE SEUIL NE SUFFIT PAS À LUI SEUL, et sa justification d'origine était fausse :
	# il compare l'arc à `360/alive`, l'écart de plaques d'une répartition RÉGULIÈRE que
	# la coque n'a jamais portée — les siennes sont espacées de 54° sur un croissant. Ce
	# qui garantit vraiment une cible en permanence, c'est le balancement face au joueur
	# (`shell_sway_deg`), et cela se vérifie sur la géométrie réelle, donc dans
	# `test_leviathan_combat.gd` et non ici. Le seuil est conservé comme plancher : il
	# élargit l'arc quand les plaques se raréfient, ce qui reste souhaitable.
	if shell_orbit_period <= 0.0:
		errors.append("shell_orbit_period must be > 0")
	# Sous 30°, les plaques du bord ne viennent jamais en tête et l'armure se joue comme
	# si elle n'en comptait qu'une ou deux ; au-delà de 110°, le balancement approche le
	# plafond mesuré (±114° à trois plaques) et le vide finit par passer devant.
	if shell_sway_deg < 30.0 or shell_sway_deg > 110.0:
		errors.append("shell_sway_deg must be in [30, 110], got %.0f" % shell_sway_deg)
	elif plate_arc_deg <= 0.0 or plate_arc_deg > 360.0:
		errors.append("plate_arc_deg must be in (0, 360]")
	else:
		for cycle in maxi(cycle_count, 1):
			var alive := plates_for_cycle(cycle)
			if effective_arc_deg(alive) < 360.0 / float(alive):
				errors.append("cycle %d: %d plates need a %.0f deg arc, got %.0f — there are moments with no target at all"
					% [cycle + 1, alive, 360.0 / float(alive), effective_arc_deg(alive)])
		if plate_window() < min_window:
			errors.append("phase 1 window too short: %.1f s orbit x %.0f deg / 360 = %.2f s (need >= %.1f)"
				% [shell_orbit_period, plate_arc_deg, plate_window(), min_window])

	# --- INVARIANT 2 : l'aspiration accompagne, elle ne pilote pas -------
	if pull_radius <= 0.0:
		errors.append("pull_radius must be > 0")
	if pull_speed_max <= 0.0:
		errors.append("pull_speed_max must be > 0")
	elif not GravityWell.escapes(pull_speed_max, reference_player_max_speed):
		errors.append("dive pull %.1f >= player speed %.1f — the player is sucked in whatever they do"
			% [pull_speed_max, reference_player_max_speed])
	elif not GravityWell.leaves_room(pull_speed_max, reference_player_max_speed):
		errors.append("dive pull %.1f leaves less than %.0f%% mobility against %.1f — escapable on paper, unplayable in fact"
			% [pull_speed_max, GravityWell.MIN_MOBILITY * 100.0, reference_player_max_speed])

	# --- INVARIANT 3 : le combat tient sa durée --------------------------
	if target_duration <= 0.0:
		errors.append("target_duration must be > 0 — it is the promise made to the player")
	elif duration_tolerance < 0.0:
		errors.append("duration_tolerance must be >= 0")
	else:
		var total := total_duration()
		if absf(total - target_duration) > duration_tolerance:
			errors.append("fight lasts %.0f s, outside the %.0f +/- %.0f s target — %s"
				% [total, target_duration, duration_tolerance,
					"cut health or shorten the dive" if total > target_duration else "the final boss must not be shorter than the mini-boss"])

	# --- INVARIANT 4 : les deux temps se partagent le combat -------------
	# Une armure qui prendrait 90 % du combat rendrait la plongée anecdotique, et
	# inversement. C'est exactement ce qui s'était produit avant : une phase de 8 s sur 67.
	var share := armor_share()
	if share < 0.25 or share > 0.75:
		errors.append("breaking armour takes %.0f%% of the fight — the two beats must each carry between 25%% and 75%%"
			% (share * 100.0))

	# --- INVARIANT 5 : le flux tombe au dernier passage, pas avant -------
	# Trop mou, le boss meurt au premier plongeon et les cycles ne servent à rien ; trop
	# dur, le joueur repart pour un tour de plus à chaque fois sans comprendre pourquoi.
	if sweep_half_width <= 0.0:
		errors.append("sweep_half_width must be > 0")
	if sweep_arm_delay <= 0.0:
		errors.append("sweep_arm_delay must be > 0 — c'est le délai qui rend le laser lisible à l'entrée")
	if not reactor_rings.is_empty() and is_zero_approx(sweep_speed_deg):
		errors.append("sweep_speed_deg à zéro : un faisceau immobile condamne un secteur pour toute la plongée")
	for i in reactor_rings.size():
		var ring := reactor_rings[i]
		if ring == null:
			errors.append("reactor_rings[%d] est nul" % i)
			continue
		for error in ring.validate():
			errors.append("reactor_rings[%d] : %s" % [i, error])
	if dive_time <= 0.0:
		errors.append("dive_time must be > 0 — it is the whole point of the dive")
	elif flux_reference_dps <= 0.0:
		errors.append("flux_reference_dps must be > 0 — the flux is not sized against the armour's dps")
	else:
		# ⚠️ `flux_reference_dps`, PAS `reference_dps`. Se comparer à la cadence sur cible
		# large revient à se donner raison : c'est ce qui a laissé passer un flux 2,2 fois
		# trop gros, validé à 99 % du plafond autorisé.
		var window := flux_damage_window()
		var reachable := flux_reachable_per_dive()
		var needed := flux_damage_per_dive()
		if needed > reachable:
			errors.append("flux needs %.0f damage per dive but only %.0f is reachable in %.1f s — the fight cannot end in %d cycles"
				% [needed, reachable, window, cycle_count])
		elif needed < reachable * 0.55:
			errors.append("flux needs only %.0f of the %.0f damage reachable per dive — it dies far too early, and the cycles never happen"
				% [needed, reachable])

	# --- INVARIANT 6 : toute attaque lourde est télégraphiée -------------
	if spine_windup_time <= 0.0:
		errors.append("spine_windup_time must be > 0 — the wind-up is what makes the beam dodgeable")
	if spine_beam_time <= 0.0:
		errors.append("spine_beam_time must be > 0")
	elif spine_windup_time < spine_beam_time * 0.5:
		errors.append("spine wind-up %.1f s is short next to a %.1f s beam — the telegraph must be readable, not a formality"
			% [spine_windup_time, spine_beam_time])
	if missile_turn_rate < 0.0:
		errors.append("missile_turn_rate must be >= 0")
	elif missile_turn_rate > PI:
		errors.append("missile_turn_rate %.2f rad/s turns faster than half a circle per second — unavoidable"
			% missile_turn_rate)

	# --- INVARIANT 7 : les occupations sont des parts -------------------
	for value in [occupancy_armor, occupancy_dive]:
		if value <= 0.0 or value > 1.0:
			errors.append("every occupancy must be in (0, 1]")
			break

	# --- Cadences --------------------------------------------------------
	for pair in [["fan_interval", fan_interval], ["spine_interval", spine_interval],
			["missile_salvo_interval", missile_salvo_interval],
			["shell_open_time", shell_open_time], ["dive_enter_time", dive_enter_time],
			["dive_eject_time", dive_eject_time], ["flux_drift_period", flux_drift_period]]:
		if float(pair[1]) <= 0.0:
			errors.append("%s must be > 0" % pair[0])

	return errors
