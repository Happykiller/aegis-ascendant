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
## ⚠️ LA TOURELLE NE TÉLÉGRAPHIE PLUS, ELLE TIRE EN CONTINU — ET C'EST UN GAIN DE LISIBILITÉ,
## pas une perte. Le modèle précédent était celui du Léviathan : `READY → WINDUP → FIRING →
## RECOVER`, avec un préavis qui annonçait le coup. Il marche sur un boss, qu'on regarde. Il ne
## marche pas ici : « je ne vois pas les tourelles qui me tirent dessus » (opérateur, en jouant
## le 2026-08-29). Sur un décor qui défile, avec dix-sept pièces réparties sur deux flancs, un
## préavis de 0,8 s passe inaperçu — le joueur regarde ailleurs, il esquive.
##
## Un faisceau PERMANENT résout le problème par construction : la menace est visible tout le
## temps, et sa direction se lit d'un coup d'œil. Ce qui remplace le télégraphe, c'est la
## LENTEUR : la tourelle pivote, le joueur va plus vite qu'elle.

## Vitesse de rotation de la tourelle, en degrés par seconde.
##
## ⚠️ C'EST LE SEUL RÉGLAGE DE DIFFICULTÉ DE LA PIÈCE, et il remplace le télégraphe : l'invariant
## 3 vérifie qu'elle reste DISTANÇABLE. Un joueur à 14 u/s qui passe à 8 unités d'une tourelle
## tourne autour d'elle à 100 °/s ; au-delà de cette vitesse, la tourelle le suit quoi qu'il
## fasse et le faisceau devient un impôt.
@export var turret_turn_rate_deg: float = 42.0

## Ce que le faisceau coûte à chaque morsure, et l'intervalle entre deux morsures.
##
## ⚠️ EN MORSURES ET NON PAR SECONDE. Le bouclier du chasseur a sa propre fenêtre : lui verser
## `dps × delta` à chaque image ferait perdre presque tout dans les images gelées, et rendrait
## les dégâts dépendants de la cadence d'affichage. Une morsure toutes les 0,4 s se règle, se
## teste, et se sent.
@export var turret_burn_damage: float = 7.0
@export var turret_burn_interval: float = 0.4
## Portée du faisceau, et sa demi-largeur. ⚠️ La portée doit couvrir la DIAGONALE du plan de
## jeu (16,1 unités) : une tourelle postée dans un coin doit pouvoir atteindre le coin opposé,
## sinon son télégraphe promet un tir qui n'arrive pas — et un télégraphe qui ment est pire
## que pas de télégraphe.
@export var turret_range: float = 34.0
@export var turret_beam_half_width: float = 0.30
## Ce que rapporte une tourelle abattue.
@export var turret_score: int = 900

@export_group("Ponts d'envol")
## ⚠️ ILS COÛTENT CHER À FAIRE TOMBER, C'EST LEUR RAISON D'ÊTRE. Un pont laissé debout produit
## en continu ; l'abattre est une décision, pas un réflexe. Mais le prix a une borne, et c'est
## l'invariant 2 qui la tient.
@export var bay_visible_span: float = 24.0
@export var bay_health: float = 900.0
## Intervalle entre deux lâchers, tant que le pont vit.
@export var bay_release_interval: float = 2.2
## Combien d'unités par lâcher.
@export var bay_release_count: int = 2
## Le pool propre à CHAQUE pont. ⚠️ Il est alloué au montage du niveau et jamais pendant la
## partie (spec §26.1) : il doit couvrir le pire cas, soit tous les lâchers d'un pont qui vit
## jusqu'au bout de sa fenêtre. `validate()` le vérifie plutôt que de le supposer.
@export var bay_pool_size: int = 10
@export var bay_score: int = 4200

@export_group("Épine dorsale")
## Un nœud par tronçon.
@export var node_visible_span: float = 14.0
@export var node_health: float = 260.0
## Ce qu'un nœud abattu abîme : les tourelles du tronçon SUIVANT.
@export var node_weakens_next_section: bool = true
@export var node_score: int = 2600

## Ce qu'il reste à une tourelle abîmée, en part de son réglage nominal.
##
## ⚠️ CES DEUX FACTEURS EXISTENT PARCE QUE L'EXTINCTION TOTALE A VIDÉ LE NIVEAU. Mesuré en jeu le
## 2026-08-30 : les cinq nœuds tombent, chacun éteignait tout son tronçon, et **quinze tourelles
## sur dix-sept** se taisaient avant d'être à portée. Le joueur y lisait une panne, pas une
## récompense. Une tourelle abîmée reste donc vivante — elle pivote plus lentement et tire moins
## souvent — et l'invariant 8 borne les deux valeurs des DEUX côtés : trop haut la récompense ne
## se sent pas, trop bas on retrouve l'extinction sous un autre nom.
@export var turret_weakened_turn_factor: float = 0.45
@export var turret_weakened_interval_factor: float = 2.6

# ==========================================================================
# Fonctions dérivées — à lire, jamais à recopier dans un test
# ==========================================================================

## Combien de temps un pont passe AU-DESSUS DU TERRAIN, et non dans sa fenêtre de tir.
##
## ⚠️ LES DEUX NE SONT PAS LA MÊME CHOSE, et les confondre a produit un pont qui ne lâchait
## qu'UNE FOIS là où l'invariant en promettait deux. La fenêtre de tir déborde le plan de vol —
## la caméra plonge et voit loin devant, donc on tire sur un pont bien avant qu'il n'arrive.
## Mais il ne peut LÂCHER que quand il est au-dessus du terrain : une coque née plus haut que la
## borne du plan est détruite à sa première trame par le despawn de `EnemyController`. C'est
## donc la hauteur du plan de vol, et elle seule, qui dit la pression qu'un pont exerce.
func release_window() -> float:
	if scroll_speed <= 0.001:
		return 0.0
	return GameplayPlane.BOUNDS.size.y / scroll_speed

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

	# --- INVARIANT 3 : UNE TOURELLE SE DISTANCE -------------------------
	#
	# ⚠️ IL REMPLACE « TOUTE ATTAQUE LOURDE EST TÉLÉGRAPHIÉE », et il le remplace parce que le
	# télégraphe ne marchait pas ici. La règle de la spec §11.2 dit qu'un tir sans préavis est
	# une taxe et non une difficulté ; elle reste vraie. Ce qui change, c'est la façon de la
	# tenir : sur un boss qu'on regarde, on annonce le coup ; sur dix-sept pièces réparties le
	# long d'un décor qui défile, on rend la menace PERMANENTE et VISIBLE, et on la fait
	# perdre. Le faisceau est son propre préavis, à condition qu'on puisse le semer.
	#
	# Le seuil se calcule et ne se choisit pas : un joueur à `max_speed` qui contourne une
	# tourelle à distance `d` tourne autour d'elle à `max_speed / d` radians par seconde. La
	# tourelle doit rester sous cette vitesse, avec de la marge — sinon elle colle au joueur
	# quoi qu'il fasse, et le faisceau redevient une taxe.
	const PLAYER_SPEED := 14.0     # `player_stats.gd` : max_speed
	const CLOSE_RANGE := 8.0       # la distance à laquelle on passe VRAIMENT près d'une pièce
	var escapable_deg := rad_to_deg(PLAYER_SPEED / CLOSE_RANGE)
	if turret_turn_rate_deg <= 0.0:
		errors.append("turret_turn_rate_deg doit être > 0 — une tourelle qui ne pivote pas ne vise jamais personne")
	elif turret_turn_rate_deg > escapable_deg * 0.6:
		errors.append("une tourelle pivote à %.0f °/s alors qu'un joueur en contourne une à %.0f °/s : elle le suivrait quoi qu'il fasse, et un faisceau qu'on ne peut pas semer est une taxe, pas une difficulté"
			% [turret_turn_rate_deg, escapable_deg])
	if turret_burn_interval <= 0.0:
		errors.append("turret_burn_interval doit être > 0 — sinon la morsure dépend de la cadence d'affichage")

	# --- INVARIANT 4 : un pont laissé debout PRODUIT ---------------------
	# Sans quoi l'abattre ne serait pas une décision : c'est la pression qu'il exerce qui
	# donne sa valeur au choix de le faire taire.
	if bay_release_interval <= 0.0:
		errors.append("bay_release_interval doit être > 0 — un pont qui ne produit pas n'est pas une menace")
	elif bay_release_count <= 0:
		errors.append("bay_release_count doit être >= 1")
	else:
		var lachers := int(release_window() / bay_release_interval)
		if lachers < 2:
			errors.append("un pont ne lâche que %d fois pendant qu'il survole le terrain (%.1f s) — trop peu pour peser sur la décision de l'abattre"
				% [lachers, release_window()])

	# --- INVARIANT 4 bis : LE POOL D'UN PONT COUVRE SON PIRE CAS ---------
	# ⚠️ Un pont à court de coques cesse de produire sans que rien ne le dise, et sa menace
	# s'éteint toute seule — le joueur croirait l'avoir fait taire. Le pire cas se CALCULE :
	# c'est le nombre de lâchers que sa fenêtre autorise, fois la taille d'un lâcher.
	if bay_release_interval > 0.0 and bay_release_count > 0:
		var pire := (int(release_window() / bay_release_interval) + 1) * bay_release_count
		if bay_pool_size < pire:
			errors.append("le pool d'un pont tient %d coques pour %d lâchées au pire — il s'épuiserait en pleine fenêtre, et le pont semblerait s'être tu tout seul"
				% [bay_pool_size, pire])

	# --- INVARIANT 5 : les cadences ne sont pas nulles --------------------
	for pair in [["turret_burn_damage", turret_burn_damage], ["turret_range", turret_range],
			["turret_beam_half_width", turret_beam_half_width]]:
		if float(pair[1]) <= 0.0:
			errors.append("%s doit être > 0" % pair[0])

	# --- INVARIANT 6 : un télégraphe ne promet pas un tir hors de portée --
	# La diagonale du plan de vol ordinaire : une tourelle dans un coin, le joueur dans
	# l'autre. En dessous, le faisceau s'arrête avant sa cible alors que la ligne de visée
	# l'a désignée.
	var diagonale := GameplayPlane.BOUNDS.size.length()
	if turret_range > 0.0 and turret_range < diagonale:
		errors.append("portée de tourelle %.1f pour une diagonale de plan de %.1f — le télégraphe désignerait une cible que le faisceau n'atteint pas"
			% [turret_range, diagonale])

	# --- INVARIANT 8 : une tourelle abîmée reste une tourelle ------------
	# ⚠️ CE N'EST PAS UN GARDE-FOU DE CONFORT. Sa version précédente — l'extinction — a été
	# mesurée en jeu : 15 tourelles sur 17 neutralisées, un niveau vidé par sa propre
	# récompense, et une pièce immobile que le joueur a lue comme cassée. Les deux bornes qui
	# suivent disent la même chose dans les deux sens : l'affaiblissement doit se SENTIR, et il
	# ne doit jamais redevenir un silence.
	if turret_weakened_turn_factor <= 0.0:
		errors.append("turret_weakened_turn_factor doit être > 0 — une tourelle abîmée qui ne pivote plus se lit comme cassée, pas comme abîmée, et c'est le défaut que ce réglage corrige")
	elif turret_weakened_turn_factor < 0.2:
		errors.append("turret_weakened_turn_factor = %.2f : à ce point la rotation ne se voit plus, et l'extinction revient sous un autre nom"
			% turret_weakened_turn_factor)
	elif turret_weakened_turn_factor >= 1.0:
		errors.append("turret_weakened_turn_factor = %.2f : abattre un nœud ne changerait rien à la rotation, donc la récompense ne se sentirait pas"
			% turret_weakened_turn_factor)
	if turret_weakened_interval_factor <= 1.0:
		errors.append("turret_weakened_interval_factor doit être > 1 — sinon une tourelle abîmée tire aussi vite qu'intacte")
	elif turret_burn_interval > 0.0 and turret_visible_span > 0.0 and scroll_speed > 0.0:
		# Combien de fois une tourelle abîmée mord ENCORE pendant qu'on la survole. En dessous de
		# deux, le joueur ne la voit jamais tirer et croit qu'elle est morte — ce qui nous
		# ramène exactement au défaut d'origine.
		var traversee := turret_visible_span / scroll_speed
		var morsures := traversee / (turret_burn_interval * turret_weakened_interval_factor)
		if morsures < 2.0:
			errors.append("une tourelle abîmée ne tirerait que %.1f fois pendant sa fenêtre (%.1f s) : en dessous de deux morsures le joueur ne la voit jamais tirer et la croit morte"
				% [morsures, traversee])

	return errors
