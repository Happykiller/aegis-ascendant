class_name CortegeTuning
extends Resource
## Les réglages du survol du Long Cortège (niveau 2), et les invariants qui empêchent un
## réglage sensé de rendre le niveau injouable.
##
## ⚠️ ELLE EXISTE PARCE QU'UN SURVOL NE PARDONNE PAS. Le décor défile et **ne revient jamais en
## arrière** : chaque cible n'est tirable que pendant la fenêtre où elle est à l'écran. Des
## points de vie choisis à la main au-dessus de cette fenêtre rendent la cible indestructible
## EN PRATIQUE — et le joueur ne le saura jamais, il croira mal jouer et continuera de tirer
## sur ce qui ne peut pas tomber.
##
## C'est exactement le défaut qu'`ADR-0024` a payé sur le flux du Léviathan : des PV dimensionnés
## contre une cadence optimiste d'un facteur 2,4, qu'aucun test ne voyait parce que l'invariant
## se comparait à lui-même. Le modèle de ce fichier est `LeviathanTuning` et ses sept invariants.

# ==========================================================================
# Hypothèses de dimensionnement — PAS des réglages
# ==========================================================================

## Cadence du joueur de référence contre une CIBLE LARGE ET FIXE sur la coque (pont d'envol,
## tourelle). Tous les canons portent : c'est le cas favorable, celui de `reference_dps` du
## Léviathan.
@export var reference_dps: float = 420.0

## Cadence contre un NŒUD D'ÉPINE — petit, sur l'axe, à traverser le feu pour l'atteindre.
##
## ⚠️ DEUX HYPOTHÈSES ET NON UNE, et c'est la leçon d'`ADR-0024`. Se comparer à une seule
## cadence revient à se donner raison : sur une baie de plusieurs mètres les canons d'aile
## portent, sur un nœud ils partent à côté. Seuls les canons de nez comptent.
@export var node_reference_dps: float = 208.0

## Vitesse à laquelle la coque défile sous le joueur, en unités/seconde.
##
## ⚠️ ELLE COMMANDE TOUT LE RESTE. Repères du niveau 1 : la surface de la lune défile à
## 1,2 u/s, ses rochers de 0,7 à 3,2. En dessous de 2, un survol devient une dérive : le plan
## de jeu fait 16 unités de haut, donc à 0,8 u/s un point fixe met 20 s à traverser l'écran.
@export var scroll_speed: float = 2.4

## Part du temps où le joueur peut réellement placer ses tirs sur une cible de coque. Le reste
## du temps, il esquive. **C'est le vrai levier de conception**, pas les points de vie.
@export var occupancy_hull: float = 0.55
## Idem pour un nœud, plus bas : il faut s'aligner sur l'axe, là où tout converge.
@export var occupancy_node: float = 0.35

# ==========================================================================
# Structure du niveau
# ==========================================================================

## Le nombre de tronçons joués. ⚠️ Le vaisseau en compte sept (maquettes) ; le niveau 2 s'arrête
## au cinquième, sur Ambry. Les deux derniers appartiennent au niveau 3.
@export var section_count: int = 5
## Longueur d'un tronçon, en unités monde. Doit correspondre à la géométrie livrée.
@export var section_length: float = 100.0

## Durée visée pour le niveau entier, et sa tolérance. C'est la promesse faite au joueur.
@export var target_duration: float = 210.0
@export var duration_tolerance: float = 30.0

# ==========================================================================
# Les trois mécaniques de coque
# ==========================================================================

@export_group("Tourelles")
## Distance sur laquelle une tourelle reste tirable — sa taille plus la hauteur de l'écran.
@export var turret_visible_span: float = 20.0
@export var turret_health: float = 180.0
@export var turret_windup_time: float = 0.8
@export var turret_beam_time: float = 0.7
@export var turret_recover_time: float = 1.1
@export var turret_interval: float = 2.6
@export var turret_damage: float = 18.0

@export_group("Ponts d'envol")
## ⚠️ ILS COÛTENT CHER À FAIRE TOMBER, C'EST LEUR RAISON D'ÊTRE. Un pont laissé debout produit
## en continu ; l'abattre est une décision, pas un réflexe. Mais le prix a une borne, et c'est
## l'invariant 2 qui la tient.
@export var bay_visible_span: float = 24.0
@export var bay_health: float = 900.0
## Intervalle entre deux lâchers, tant que le pont vit.
@export var bay_release_interval: float = 3.5
## Combien d'unités par lâcher.
@export var bay_release_count: int = 2

@export_group("Épine dorsale")
## Un nœud par tronçon.
@export var node_visible_span: float = 14.0
@export var node_health: float = 260.0
## Ce qu'un nœud abattu éteint : les tourelles du tronçon SUIVANT.
@export var node_silences_next_section: bool = true

# ==========================================================================
# Fonctions dérivées — à lire, jamais à recopier dans un test
# ==========================================================================

## Combien de temps une cible reste tirable, à la vitesse de défilement courante.
func window_for(visible_span: float) -> float:
	if scroll_speed <= 0.001:
		return 0.0
	return visible_span / scroll_speed

## Ce qu'un joueur de référence peut réellement placer dans cette fenêtre.
func reachable_damage(visible_span: float, dps: float, occupancy: float) -> float:
	return dps * occupancy * window_for(visible_span)

func turret_reachable() -> float:
	return reachable_damage(turret_visible_span, reference_dps, occupancy_hull)

func bay_reachable() -> float:
	return reachable_damage(bay_visible_span, reference_dps, occupancy_hull)

func node_reachable() -> float:
	return reachable_damage(node_visible_span, node_reference_dps, occupancy_node)

## La durée du niveau, déduite de la géométrie et de la vitesse — jamais saisie à la main.
func level_duration() -> float:
	if scroll_speed <= 0.001:
		return 0.0
	return float(section_count) * section_length / scroll_speed

func section_duration() -> float:
	return level_duration() / float(maxi(section_count, 1))

# ==========================================================================
# validate() — les invariants
# ==========================================================================

func validate() -> PackedStringArray:
	var errors := PackedStringArray()

	# --- Hypothèses ------------------------------------------------------
	if reference_dps <= 0.0 or node_reference_dps <= 0.0:
		errors.append("les deux cadences de référence doivent être > 0 — ce sont les hypothèses de dimensionnement, pas des options")
	if scroll_speed <= 0.0:
		errors.append("scroll_speed doit être > 0 — un survol qui n'avance pas n'est pas un survol")
	for value in [occupancy_hull, occupancy_node]:
		if value <= 0.0 or value > 1.0:
			errors.append("les occupations sont des parts de temps, dans (0, 1]")
			break

	# --- INVARIANT 1 : le niveau dure ce qu'on a promis -------------------
	if section_count <= 0:
		errors.append("section_count doit être > 0")
	elif section_length <= 0.0:
		errors.append("section_length doit être > 0")
	elif duration_tolerance < 0.0:
		errors.append("duration_tolerance doit être >= 0")
	else:
		var duree := level_duration()
		if absf(duree - target_duration) > duration_tolerance:
			errors.append("le survol dure %.0f s, hors de la cible %.0f ± %.0f — changez la vitesse ou la longueur des tronçons"
				% [duree, target_duration, duration_tolerance])

	# --- INVARIANT 2 : TOUTE CIBLE TOMBE DANS SA FENÊTRE -----------------
	# ⚠️ C'EST L'INVARIANT QUI DÉCIDE SI LE NIVEAU EXISTE. Un survol ne revient jamais en
	# arrière : au-dessus de ce que la fenêtre permet, la cible est indestructible EN PRATIQUE,
	# et le joueur croira mal jouer.
	#
	# ⚠️ MAIS LA BORNE BASSE N'EST PAS LA MÊME POUR TOUS, et sa première écriture s'est
	# trompée en leur appliquant la même règle. Les trois cibles ne jouent pas le même rôle :
	#
	#   - un PONT et un NŒUD sont des DÉCISIONS. Ils doivent coûter — sous 45 % de ce qui est
	#     atteignable, ils tombent en passant et le choix de les viser n'existe plus ;
	#   - une TOURELLE est une cible d'OPPORTUNITÉ. Il y en a douze à dix-huit, souvent
	#     plusieurs à l'écran. Elle a besoin d'un PLAFOND, pas d'un plancher : au-delà de 35 %
	#     de la fenêtre, s'occuper d'une seule tourelle empêche de faire quoi que ce soit
	#     d'autre, et le survol devient une file d'attente.
	var decisions := [
		["un pont d'envol", bay_health, bay_reachable(), bay_visible_span],
		["un nœud d'épine", node_health, node_reachable(), node_visible_span],
	]
	for cible in decisions:
		var nom: String = cible[0]
		var pv: float = cible[1]
		var atteignable: float = cible[2]
		var portee: float = cible[3]
		if portee <= 0.0:
			errors.append("%s : sa fenêtre de tir est nulle — il ne serait jamais tirable" % nom)
		elif pv <= 0.0:
			errors.append("%s : ses points de vie doivent être > 0" % nom)
		elif pv > atteignable:
			errors.append("%s demande %.0f dégâts mais %.0f seulement sont atteignables en %.1f s — il ne peut PAS tomber, et le joueur croira mal jouer"
				% [nom, pv, atteignable, window_for(portee)])
		elif pv < atteignable * 0.45:
			errors.append("%s demande %.0f dégâts pour %.0f atteignables — il tombe en passant, et le choix de le viser n'existe plus"
				% [nom, pv, atteignable])
	if turret_visible_span <= 0.0:
		errors.append("une tourelle : sa fenêtre de tir est nulle")
	elif turret_health <= 0.0:
		errors.append("une tourelle : ses points de vie doivent être > 0")
	elif turret_health > turret_reachable() * 0.35:
		errors.append("une tourelle demande %.0f dégâts, soit %.0f%% de la fenêtre — au-delà de 35%%, s'en occuper empêche de faire autre chose et le survol devient une file d'attente"
			% [turret_health, turret_health / turret_reachable() * 100.0])

	# --- INVARIANT 3 : toute attaque lourde est télégraphiée --------------
	# Reprise mot pour mot de l'invariant 6 de `LeviathanTuning` : un tir qui part sans
	# préavis n'est pas une difficulté, c'est une taxe (spec §11.2).
	if turret_windup_time <= 0.0 or turret_beam_time <= 0.0:
		errors.append("une tourelle télégraphie avant de tirer : windup et beam > 0")
	elif turret_windup_time < turret_beam_time * 0.5:
		errors.append("télégraphe trop court : %.2f s de préavis pour %.2f s de tir (il en faut au moins la moitié)"
			% [turret_windup_time, turret_beam_time])

	# --- INVARIANT 4 : un pont laissé debout PRODUIT ---------------------
	# Sans quoi l'abattre ne serait pas une décision : c'est la pression qu'il exerce qui
	# donne sa valeur au choix de le faire taire.
	if bay_release_interval <= 0.0:
		errors.append("bay_release_interval doit être > 0 — un pont qui ne produit pas n'est pas une menace")
	elif bay_release_count <= 0:
		errors.append("bay_release_count doit être >= 1")
	else:
		var lachers := int(window_for(bay_visible_span) / bay_release_interval)
		if lachers < 2:
			errors.append("un pont ne lâche que %d fois pendant qu'il est à l'écran — trop peu pour peser sur la décision de l'abattre"
				% lachers)

	# --- INVARIANT 5 : les cadences ne sont pas nulles --------------------
	for pair in [["turret_interval", turret_interval], ["turret_recover_time", turret_recover_time],
			["turret_damage", turret_damage]]:
		if float(pair[1]) <= 0.0:
			errors.append("%s doit être > 0" % pair[0])

	return errors
