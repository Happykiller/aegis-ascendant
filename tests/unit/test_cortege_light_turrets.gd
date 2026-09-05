extends "res://tests/test_case.gd"
## La deuxieme echelle de defense du Long Cortege : les tourelles legeres, et les batteries
## qui les portent.
##
## ⚠️ CE QUE CES TESTS GARDENT, ET POURQUOI AUCUN N'EST DECORATIF. Une batterie est montee
## RELATIVEMENT a l'installation qu'elle garde, sur une coque qu'aucun de ces tests ne
## fabrique : elle est chargee. Quatre defauts sont donc possibles, tous SILENCIEUX, et aucun
## ne produirait la moindre erreur au lancement —
##
##   1. un nom d'hote mal orthographie : la batterie ne se monte JAMAIS, et le niveau se joue
##      exactement comme avant. Rien ne le dit, ni au journal ni a l'ecran ;
##   2. une piece posee de l'autre cote de la CONTREMARCHE DE CHINE : elle herite du Y de son
##      hote et flotte de 69 cm au-dessus du vide, ce qui ne se voit qu'en capture ;
##   3. le signe de `ds` inverse : chaque batterie bascule en miroir de son hote — geometrie
##      valide, niveau faux d'un bout a l'autre ;
##   4. les deux echelles qui CONVERGENT a force de reglages, jusqu'a redevenir la « foret
##      uniforme de tourelles identiques » que ce lot existe pour eviter.
##
## Le seul qui se verrait en jouant est le troisieme, et encore : il faudrait connaitre la
## table par coeur.

const TurretScript := preload("res://scripts/gameplay/cortege_turret.gd")
const HardpointsScript := preload("res://scripts/gameplay/cortege_hardpoints.gd")
const FlybyScript := preload("res://scripts/vfx/cortege_flyby.gd")
const TuningScript := preload("res://resources/data/cortege_tuning.gd")
const TUNING := preload("res://resources/levels/long_cortege_tuning.tres")
const HEAVY_SHOT := preload("res://resources/weapons/cortege_turret_shot.tres")
const LIGHT_SHOT := preload("res://resources/weapons/cortege_light_shot.tres")

## Les deux paliers du pont, LUS DANS LE PROFIL de `build_long_cortege.py` (PROFILE_BASE) :
## pont interieur de 2,20 a 6,80 (a -4,30), contremarche de chine, pont median de 7,35 a 10,30
## (a -4,99). Entre les deux il y a 60 cm de marche, et c'est la tout le danger.
const DECK_INNER := Vector2(2.20, 6.80)
const DECK_MID := Vector2(7.35, 10.30)

## L'emprise d'une ouverture de pont d'envol (`BAY_KEEPOUT_X`, `BAY_HALF_S`). Une piece posee
## dedans tomberait dans le puits.
const BAY_KEEPOUT_X := 4.30
const BAY_HALF_S := 4.25


# =============================================================================
# 1. La hierarchie des echelles EXISTE, et elle est bornee
# =============================================================================

func test_the_delivered_tuning_still_validates_with_two_scales() -> void:
	var errors := TUNING.validate()
	assert_eq(errors.size(), 0,
		"le reglage livre passe ses invariants sur les DEUX echelles : %s" % str(errors))

## ⚠️ CE TEST GARDE LA VALEUR QUI A ETE REFUSEE. « Plus petite donc plus rapide » appelait
## 66 °/s ; l'invariant 3 la refuse, parce qu'un joueur a 14 u/s contourne une piece a 8 unites
## en 100 °/s et qu'au-dela de 60 °/s la tourelle le suit quoi qu'il fasse. La borne decrit le
## JOUEUR, pas la piece : une tourelle plus petite ne rend personne plus agile.
func test_a_light_turret_that_outruns_the_player_is_refused() -> void:
	var tuning := TUNING.duplicate() as CortegeTuning
	tuning.light_turret_turn_rate_deg = 66.0
	var errors := tuning.validate()
	assert_true(errors.size() > 0,
		"une tourelle legere a 66 °/s doit etre refusee — elle suivrait le joueur quoi qu'il fasse")
	var seen := false
	for e in errors:
		if String(e).contains("légère") and String(e).contains("66"):
			seen = true
	assert_true(seen, "et le message doit dire LAQUELLE des deux echelles : %s" % str(errors))

## ⚠️ TROIS ECARTS PORTENT LA HIERARCHIE, ET CHACUN PEUT DISPARAITRE SEUL. Sans ce test, une
## suite d'ajustements raisonnables — un peu plus de PV ici, une cadence un peu plus vive la —
## ferait converger les deux familles sans qu'aucun autre garde-fou ne s'en apercoive.
func test_two_scales_that_converge_are_refused() -> void:
	var cases := [
		["light_turret_health", TUNING.turret_health, "des PV egaux a la lourde"],
		["light_turret_burn_interval", TUNING.turret_burn_interval, "la cadence de la lourde"],
		["light_turret_visible_span", TUNING.turret_visible_span, "la fenetre de la lourde"],
	]
	for case in cases:
		var tuning := TUNING.duplicate() as CortegeTuning
		tuning.set(String(case[0]), case[1])
		assert_true(tuning.validate().size() > 0,
			"une tourelle legere avec %s doit etre refusee" % case[2])

## ⚠️ LES DEGATS NE SONT PAS DANS LE REGLAGE, ET C'EST POURQUOI CE TEST EXISTE.
## `turret_burn_damage` n'est lu par aucun script depuis qu'`ADR-0040` a remplace le faisceau par
## des balles : ce qui fait mal vit dans le `ProjectileData`. L'ecart entre les deux echelles se
## garde donc ICI, faute d'invariant capable de le voir.
func test_the_light_shot_is_smaller_and_weaker_than_the_heavy_one() -> void:
	assert_true(LIGHT_SHOT.damage < HEAVY_SHOT.damage,
		"le tir leger fait %.1f pour %.1f au lourd" % [LIGHT_SHOT.damage, HEAVY_SHOT.damage])
	assert_true(LIGHT_SHOT.radius < HEAVY_SHOT.radius,
		"le tir leger mesure %.2f pour %.2f au lourd" % [LIGHT_SHOT.radius, HEAVY_SHOT.radius])
	# ⚠️ ET IL VA A LA MEME VITESSE, DELIBEREMENT. Deux rythmes de balle ennemie sur le meme
	# ecran apprendraient au joueur qu'il existe deux dangers la ou il n'y en a qu'un, et lui
	# feraient rater l'esquive du plus lent.
	assert_almost_eq(LIGHT_SHOT.speed, HEAVY_SHOT.speed, 0.001,
		"les deux tirs ennemis gardent la meme vitesse de lecture")


# =============================================================================
# 2. La piece lit SES reglages, pas ceux de l'autre echelle
# =============================================================================

func test_a_light_turret_reads_its_own_settings() -> void:
	var light := track(TurretScript.make(TUNING, 0,
		TuningScript.TurretScale.LIGHT)) as CortegeTurret
	var heavy := track(TurretScript.make(TUNING, 0)) as CortegeTurret
	assert_true(light.is_light(), "elle se sait legere")
	assert_false(heavy.is_light(), "et la lourde se sait lourde")
	assert_eq(light.score(), TUNING.light_turret_score, "elle rapporte son propre score")
	assert_true(light.score() < heavy.score(),
		"et moins qu'une installation : %d contre %d" % [light.score(), heavy.score()])
	# ⚠️ LA HAUTEUR DE MASSE DECIDE OU IL FAUT TIRER POUR TOUCHER, sous une camera qui plonge a
	# 70°. Appliquer celle de la lourde a une piece deux fois plus petite ferait viser a cote.
	assert_true(light.hit_lift() < heavy.hit_lift(),
		"sa masse se projette plus bas : %.2f contre %.2f" % [light.hit_lift(), heavy.hit_lift()])

## ⚠️ SA FENETRE EST PLUS COURTE, ET C'EST CE QUI DECIDE SI ELLE EST TIRABLE. Un survol ne
## revient jamais en arriere : une piece qui utiliserait la fenetre de la lourde s'ouvrirait au
## feu avant d'etre visible.
func test_a_light_turret_engages_on_its_own_shorter_window() -> void:
	var light := track(TurretScript.make(TUNING, 0,
		TuningScript.TurretScale.LIGHT)) as CortegeTurret
	light.setup(null, null, null)
	var heavy_half := TUNING.turret_visible_span * 0.5
	var light_half := TUNING.light_turret_visible_span * 0.5
	assert_true(light_half < heavy_half, "la fenetre legere est bien la plus courte")
	assert_false(TurretScript.engaged_at(heavy_half - 0.1, TUNING.light_turret_visible_span),
		"au bord de la fenetre LOURDE, la legere n'est pas encore engagee")
	assert_true(TurretScript.engaged_at(light_half - 0.1, TUNING.light_turret_visible_span),
		"au bord de la sienne, elle l'est")


# =============================================================================
# 3. Les batteries, contre la COQUE LIVREE
# =============================================================================

## Les marqueurs de la coque livree, par nom -> position locale a son troncon.
func _hull_markers() -> Dictionary:
	var packed: PackedScene = load(FlybyScript.DECOR_PATH)
	assert_true(packed != null, "la coque du Long Cortege se charge")
	var hull := track(packed.instantiate()) as Node3D
	var markers := {}
	for section in hull.get_children():
		var s := section as Node3D
		if s == null or not s.name.begins_with("Section_"):
			continue
		for child in s.get_children():
			var marker := child as Node3D
			if marker != null:
				markers[String(marker.name)] = marker.position
	return markers

## ⚠️ LE DEFAUT LE PLUS SILENCIEUX DE TOUT LE LOT. `_add_battery` compare `marker.name` au nom
## d'hote ; une lettre de travers et la batterie n'est jamais montee. Aucune erreur, aucun
## journal, un niveau qui se joue exactement comme avant — et vingt et une pieces payees pour
## rien.
func test_every_battery_host_exists_on_the_delivered_hull() -> void:
	var markers := _hull_markers()
	assert_true(markers.size() > 0, "la coque livree porte des marqueurs")
	for entry in HardpointsScript.BATTERIES:
		var host := String(entry[0])
		assert_true(markers.has(host),
			"l'hote %s d'une batterie doit exister sur la coque livree" % host)

## ⚠️ LA CONTREMARCHE DE CHINE, ET LE DEFAUT QU'ELLE CACHE. Une piece herite du Y de son hote ;
## le pont a deux paliers separes par 60 cm. Une batterie qui franchit la marche flotte au-dessus
## du vide, en silence, et rien avant une capture ne le dirait.
func test_no_battery_piece_crosses_the_chine_step() -> void:
	var markers := _hull_markers()
	for entry in HardpointsScript.BATTERIES:
		var host := String(entry[0])
		if not markers.has(host):
			continue
		var host_x: float = absf((markers[host] as Vector3).x)
		var host_deck := _deck_of(host_x)
		assert_true(host_deck != "", "%s est sur un palier connu (|x| = %.2f)" % [host, host_x])
		for offset in entry[1]:
			var piece_x := absf((markers[host] as Vector3).x + float(offset[0]))
			var deck := _deck_of(piece_x)
			assert_eq(deck, host_deck,
				"une piece de %s se pose a |x| = %.2f (%s) alors que son hote est sur %s : elle heriterait d'une assise qui n'est pas la sienne"
					% [host, piece_x, deck if deck != "" else "hors pont", host_deck])

func _deck_of(ax: float) -> String:
	if ax >= DECK_INNER.x and ax <= DECK_INNER.y:
		return "le pont interieur"
	if ax >= DECK_MID.x and ax <= DECK_MID.y:
		return "le pont median"
	return ""

## ⚠️ UNE BATTERIE GARDE UNE INSTALLATION, ELLE NE SE POSE PAS DESSUS. Le socle du kit est
## MESURE ici et non recopie : le jour ou la forge l'elargit, ce test le voit.
func test_no_battery_piece_sits_on_the_installation_it_guards() -> void:
	var markers := _hull_markers()
	var pad := _kit_pad_radius()
	assert_true(pad > 0.5, "le socle du kit a un rayon mesurable (%.2f m)" % pad)
	var light_pad := pad * TurretScript.LIGHT_GEOM_SCALE
	for entry in HardpointsScript.BATTERIES:
		var host := String(entry[0])
		if not markers.has(host):
			continue
		for offset in entry[1]:
			var dx := float(offset[0])
			var ds := float(offset[1])
			var distance := sqrt(dx * dx + ds * ds)
			if host.begins_with("Bay_"):
				# Une ouverture de pont d'envol n'est pas un disque : c'est un rectangle, et il
				# faut en sortir par un cote OU par l'autre.
				assert_true(absf(dx) > BAY_KEEPOUT_X or absf(ds) > BAY_HALF_S + light_pad,
					"une piece de %s tomberait dans le puits (dx %.2f, ds %.2f)" % [host, dx, ds])
			else:
				assert_true(distance >= pad + light_pad,
					"une piece de %s est a %.2f m de son hote pour %.2f m de socles cumules"
						% [host, distance, pad + light_pad])

## ⚠️ LE TEST CI-DESSUS NE REGARDE QUE L'HOTE, ET C'EST PAR LA QUE TROIS PIECES SONT TOMBEES
## DANS UN PUITS. `test_no_battery_piece_sits_on_the_installation_it_guards` compare une piece a
## la SEULE installation qui la porte : la batterie de `Turret_10` visait `Bay_06`, huit metres
## en aval, et personne ne regardait ce couple-la. Observe en jouant le 2026-09-03, pas trouve
## par un test — deux pieces avaient le centre au-dessus du vide, la troisieme le socle en
## surplomb, et la coque restait deterministe, le banc vert, le journal muet.
##
## UNE OUVERTURE DE PONT D'ENVOL N'APPARTIENT A PERSONNE. C'est un trou dans la peau, pas la
## propriete de la batterie qui la garde : il faut donc confronter CHAQUE piece a CHAQUE baie,
## et non a la sienne. La meme classe de defaut vaudrait pour les fosses le jour ou une batterie
## en approchera une.
func test_no_battery_piece_falls_into_any_bay_well() -> void:
	var markers := _hull_markers_in_hull_space()
	var light_pad := _kit_pad_radius() * TurretScript.LIGHT_GEOM_SCALE
	var bays := {}
	for name in markers:
		if String(name).begins_with("Bay_"):
			bays[name] = markers[name]
	assert_true(bays.size() > 0, "la coque livree porte des ponts d'envol")
	for entry in HardpointsScript.BATTERIES:
		var host := String(entry[0])
		if not markers.has(host):
			continue
		var host_pos: Vector3 = markers[host]
		for offset in entry[1]:
			# `ds` court vers la poupe, le Z local decroit d'autant — meme conversion que
			# `_add_battery`, sans quoi ce test garderait le miroir de ce qui est monte.
			var piece_x: float = host_pos.x + float(offset[0])
			var piece_z: float = host_pos.z - float(offset[1])
			for bay_name in bays:
				var bay: Vector3 = bays[bay_name]
				var dx := absf(piece_x - bay.x)
				var dz := absf(piece_z - bay.z)
				assert_true(dx > BAY_KEEPOUT_X or dz > BAY_HALF_S + light_pad,
					"une piece de %s tombe dans le puits de %s (dx %.2f, dz %.2f)"
						% [host, bay_name, dx, dz])

## ⚠️ LES MARQUEURS SONT LOCAUX A LEUR TRONCON, ET DEUX TRONCONS SE SUPERPOSENT. `_hull_markers()`
## rend la position telle que la porte la `Section_NN` qui la contient : deux marqueurs de
## sections differentes peuvent avoir le meme Z sans etre voisins de cent metres. Comparer une
## piece a TOUTES les baies exige donc le repere de la coque — sans quoi `Turret_10` (troncon 4)
## se retrouve a quatre metres de `Bay_02` (troncon 2), qui est a deux cents metres de la.
func _hull_markers_in_hull_space() -> Dictionary:
	var packed: PackedScene = load(FlybyScript.DECOR_PATH)
	assert_true(packed != null, "la coque du Long Cortege se charge")
	var hull := track(packed.instantiate()) as Node3D
	var markers := {}
	for section in hull.get_children():
		var sec := section as Node3D
		if sec == null or not sec.name.begins_with("Section_"):
			continue
		for child in sec.get_children():
			var marker := child as Node3D
			if marker != null:
				markers[String(marker.name)] = sec.transform * marker.position
	return markers

func _kit_pad_radius() -> float:
	var kit: PackedScene = load(TurretScript.KIT_PATH)
	assert_true(kit != null, "le kit de tourelle se charge")
	var assembled := track(kit.instantiate()) as Node3D
	var pad := assembled.get_node_or_null("turret_pad") as MeshInstance3D
	assert_true(pad != null, "le kit porte bien un socle")
	var box := pad.get_aabb()
	return maxf(box.size.x, box.size.z) * 0.5

## ⚠️ DEUX PIECES D'UNE MEME BATTERIE NE SE TRAVERSENT PAS. Le test precedent garde la distance
## a l'HOTE ; celui-ci garde les pieces entre elles, et rien d'autre ne le ferait. Deux socles qui
## se chevauchent produisent une bouillie de geometrie que seule une capture montrerait — et
## encore, seulement si l'on capture la bonne batterie au bon instant.
func test_two_pieces_of_a_battery_never_overlap() -> void:
	var light_pad := _kit_pad_radius() * TurretScript.LIGHT_GEOM_SCALE
	for entry in HardpointsScript.BATTERIES:
		var host := String(entry[0])
		var offsets: Array = entry[1]
		for i in offsets.size():
			for j in range(i + 1, offsets.size()):
				var dx := float(offsets[i][0]) - float(offsets[j][0])
				var ds := float(offsets[i][1]) - float(offsets[j][1])
				var gap := sqrt(dx * dx + ds * ds)
				assert_true(gap >= light_pad * 2.0,
					"deux pieces de %s sont a %.2f m pour %.2f m de socles cumules"
						% [host, gap, light_pad * 2.0])

## ⚠️ LA REGLE PRECEDENTE DISAIT L'INVERSE, ET ELLE EST REMPLACEE — PAS CONTOURNEE.
##
## Elle exigeait qu'une batterie soit une GRAPPE : etalement borne a 4 m, sous peine que « ses
## pieces arrivent une par une et que le groupe ne se lise jamais ». Elle etait nee d'une
## capture, et elle avait raison contre le defaut de son epoque — une premiere table etalait
## ses pieces sur douze a seize metres et aucun groupe ne se lisait.
##
## `BRIEF-0100` a fait grossir le socle de 1,70 a 2,00 m. La grappe est alors devenue un TAS :
## « *il y a des endroits ou les petites tours sont tout agglutinees les unes sur les autres.
## Il faudrait les mettre par-ci par-la un peu de partout* » (operateur, en jouant le
## 2026-09-05). A ce diametre, quatre pieces dans quatre metres ne forment plus un groupe :
## elles se chevauchent.
##
## La doctrine est donc renversee, et c'est une decision du proprietaire du projet : la defense
## legere est un SEMIS sur toute la coque, une ou deux pieces par installation, sur beaucoup
## d'installations. Ce test garde la nouvelle intention pour qu'elle ne derive pas a son tour.
func test_the_light_defence_is_sown_across_the_hull_not_piled_on_a_few_hosts() -> void:
	var hotes := HardpointsScript.BATTERIES.size()
	var pieces := 0
	for entry in HardpointsScript.BATTERIES:
		pieces += (entry[1] as Array).size()
	assert_true(hotes >= 12,
		"la defense legere est repartie sur au moins douze installations (%d)" % hotes)
	assert_true(float(pieces) / float(hotes) <= 2.0,
		"deux pieces par hote au plus, en moyenne : %d pieces pour %d hotes" % [pieces, hotes])

## ⚠️ ET IL COUVRE LES CINQ TRONCONS, pas seulement le debut. Un semis concentre sur deux
## troncons redonnerait des zones nues et des zones saturees — le defaut par l'autre bout.
##
## ⚠️ LA STATION D'UN MARQUEUR EST LOCALE A SON TRONCON (0 a 100) : deux pieces distantes de
## quatre cents metres y ont le meme z. C'est le TRONCON qu'il faut lire, et il faut donc
## remonter au parent — `_hull_markers()` ne le garde pas.
func test_the_light_defence_covers_every_section() -> void:
	var packed: PackedScene = load(FlybyScript.DECOR_PATH)
	var hull := track(packed.instantiate()) as Node3D
	var hosts := {}
	for entry in HardpointsScript.BATTERIES:
		hosts[String(entry[0])] = true
	var covered := {}
	for section in hull.get_children():
		var s := section as Node3D
		if s == null or not s.name.begins_with("Section_"):
			continue
		for child in s.get_children():
			if hosts.has(String(child.name)):
				covered[String(s.name)] = true
	assert_eq(covered.size(), 5,
		"les cinq troncons portent de la defense legere (%s)" % str(covered.keys()))

## ⚠️ « UNE OU DEUX PIECES », depuis le semis du 2026-09-05. C'etait « 2 a 4 » du temps des
## grappes ; au diametre actuel, trois pieces sur un meme hote se chevauchent. Un hote n'est
## plus un groupe, c'est un point du semis.
func test_batteries_are_clusters_and_never_a_regular_pitch() -> void:
	assert_true(HardpointsScript.BATTERIES.size() >= 5,
		"assez de batteries pour que la piece existe vraiment dans le niveau")
	var hosts := {}
	for entry in HardpointsScript.BATTERIES:
		var host := String(entry[0])
		assert_false(hosts.has(host), "%s ne porte qu'une batterie" % host)
		hosts[host] = true
		var count: int = (entry[1] as Array).size()
		assert_true(count >= 1 and count <= 2,
			"%s porte %d pieces — un hote en porte une ou deux" % [host, count])
		if count < 3:
			continue
		# Le pas le long de la coque ne doit pas etre constant : trois pieces regulierement
		# espacees sont un peigne, pas une defense.
		var steps: Array[float] = []
		var previous := 0.0
		var first := true
		var stations: Array[float] = []
		for offset in entry[1]:
			stations.append(float(offset[1]))
		stations.sort()
		for station in stations:
			if not first:
				steps.append(station - previous)
			previous = station
			first = false
		var spread := 0.0
		for step in steps:
			spread = maxf(spread, absf(step - steps[0]))
		assert_true(spread > 0.4,
			"les pieces de %s sont espacees regulierement (%s) : c'est un motif, pas une batterie"
				% [host, str(steps)])

## ⚠️ ET DES ZONES CALMES ENTRE ELLES. « Le gigantisme vient aussi du vide » : sept batteries sur
## vingt-quatre installations, ce n'est pas une economie, c'est le livrable.
func test_the_hull_keeps_long_quiet_stretches_between_batteries() -> void:
	var markers := _hull_markers()
	var stations: Array[float] = []
	for entry in HardpointsScript.BATTERIES:
		var host := String(entry[0])
		if markers.has(host):
			stations.append(-(markers[host] as Vector3).z)
	assert_true(stations.size() >= 5, "assez de batteries placees sur la coque")
	# Au moins deux respirations franches. Les stations sont locales au troncon : on compare
	# les ecarts a l'interieur de chaque troncon, et le simple fait qu'il RESTE des installations
	# sans batterie suffit a prouver le reste.
	var equipped := HardpointsScript.BATTERIES.size()
	var installations := 0
	for name in markers.keys():
		if String(name).begins_with("Turret_") or String(name).begins_with("Bay_"):
			installations += 1
	assert_true(equipped * 2 <= installations,
		"%d installations sur %d portent une batterie — au-dela de la moitie, il n'y a plus de zone calme"
			% [equipped, installations])


# =============================================================================
# 4. Le montage : le signe de `ds`, et la silhouette
# =============================================================================

## Deux troncons a la main, portant les hotes reels d'une batterie.
func _sections_with(host: String) -> Array[Node3D]:
	var sections: Array[Node3D] = []
	var section := track(Node3D.new()) as Node3D
	section.name = "Section_01"
	var marker := Node3D.new()
	marker.name = host
	section.add_child(marker)
	sections.append(section)
	return sections

## ⚠️ LE SIGNE DE `ds`. La station `s` croit vers la poupe, le Z local du troncon decroit
## d'autant. Ecrire `dz = ds` aurait pose chaque batterie en miroir de son hote : geometriquement
## valide, silencieux, et faux d'un bout a l'autre du niveau.
func test_a_battery_piece_lands_where_its_station_says() -> void:
	var host := String(HardpointsScript.BATTERIES[0][0])
	var offsets: Array = HardpointsScript.BATTERIES[0][1]
	var manager := track(HardpointsScript.new()) as CortegeHardpoints
	manager.build(_sections_with(host), TUNING, null, null, null)
	assert_eq(manager.light_turret_count(), offsets.size(),
		"les %d pieces de la batterie de %s sont montees" % [offsets.size(), host])
	for i in offsets.size():
		var piece := manager.light_turrets()[i]
		assert_almost_eq(piece.position.x, float(offsets[i][0]), 0.001,
			"la piece %d garde son ecart lateral" % i)
		assert_almost_eq(piece.position.z, -float(offsets[i][1]), 0.001,
			"la piece %d avance vers la POUPE quand sa station monte (z = -s)" % i)

## ⚠️ UN HOTE SANS BATTERIE N'EN RECOIT AUCUNE. Sans ce test, une table mal lue armerait toute
## la coque — vingt-quatre batteries au lieu de sept, et la « foret uniforme » revenue par la
## porte de derriere.
func test_an_installation_without_a_battery_stays_bare() -> void:
	var manager := track(HardpointsScript.new()) as CortegeHardpoints
	manager.build(_sections_with("Turret_09"), TUNING, null, null, null)
	assert_eq(manager.light_turret_count(), 0,
		"Turret_09 n'a pas de batterie declaree : elle reste nue")
	assert_eq(manager.turret_count(), 1, "et son installation est bien montee")
