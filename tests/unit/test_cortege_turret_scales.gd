extends "res://tests/test_case.gd"
## Les TROIS echelles de tourelle du Long Cortege, et la hierarchie qui les separe.
##
## ⚠️ CE FICHIER EXISTE PARCE QU'UNE TROISIEME FAMILLE EST LE MOMENT OU UNE HIERARCHIE SE PERD.
## Avec deux echelles, l'ecart se voit a l'oeil dans la table de reglages. Avec trois, il faut
## quatre comparaisons par marche et huit en tout : personne ne les tient de tete, et une
## standard qui deriverait vers la lourde redonnerait la « foret uniforme de tourelles
## identiques » que la consigne 15 interdit — sans qu'aucun nombre n'ait l'air faux.
##
## L'invariant 3 bis de `CortegeTuning` boucle desormais sur les couples CONSECUTIFS de l'enum.
## Ce fichier prouve deux choses qu'un invariant ne prouve pas tout seul : qu'il refuse vraiment
## une inversion, et que le NIVEAU pose bien les echelles qu'on croit.

const TuningScript := preload("res://resources/data/cortege_tuning.gd")
const TurretScript := preload("res://scripts/gameplay/cortege_turret.gd")
const HardpointsScript := preload("res://scripts/gameplay/cortege_hardpoints.gd")
const SHIPPED := "res://resources/levels/long_cortege_tuning.tres"

func _sound() -> CortegeTuning:
	return load(SHIPPED).duplicate()

func _says(reglage: CortegeTuning, mot: String) -> bool:
	for e in reglage.validate():
		if mot in e:
			return true
	return false

# --- La hierarchie, sur la Resource livree -----------------------------------

## ⚠️ L'ORDRE DE L'ENUM EST LA HIERARCHIE. Si quelqu'un reordonne `TurretScale`, la boucle des
## invariants comparerait les mauvaises marches et passerait au vert sur un reglage inverse.
func test_the_scales_are_declared_from_lightest_to_heaviest() -> void:
	assert_eq(int(CortegeTuning.TurretScale.LIGHT), 0, "la legere est la premiere marche")
	assert_eq(int(CortegeTuning.TurretScale.STANDARD), 1, "la standard est au milieu")
	assert_eq(int(CortegeTuning.TurretScale.HEAVY), 2, "la lourde est la derniere")

func test_each_step_up_is_tougher_slower_and_seen_from_further() -> void:
	var tuning: CortegeTuning = load(SHIPPED)
	var echelles: Array = CortegeTuning.TurretScale.values()
	for i in echelles.size() - 1:
		var petite: int = echelles[i]
		var grande: int = echelles[i + 1]
		var nom := "%s -> %s" % [CortegeTuning.turret_scale_name(petite),
			CortegeTuning.turret_scale_name(grande)]
		assert_true(tuning.turret_health_of(petite) < tuning.turret_health_of(grande),
			"%s : les PV montent" % nom)
		assert_true(tuning.turret_span_of(petite) < tuning.turret_span_of(grande),
			"%s : la fenetre s'allonge" % nom)
		assert_true(tuning.turret_burn_interval_of(petite) > tuning.turret_burn_interval_of(grande),
			"%s : la cadence se resserre" % nom)
		assert_true(tuning.turret_turn_rate_of(petite) > tuning.turret_turn_rate_of(grande),
			"%s : la rotation ralentit — la masse se paie en lenteur" % nom)

## ⚠️ LE PLAFOND DE L'INVARIANT 2 VAUT AUSSI POUR LA LOURDE. Elle a 520 PV la ou la standard en a
## 180 : c'est le seul reglage du niveau qui approche la borne, et c'est celui qu'un ajustement
## futur poussera dessus sans y penser.
func test_even_the_heavy_falls_inside_the_window_it_is_given() -> void:
	var tuning: CortegeTuning = load(SHIPPED)
	var lourde := CortegeTuning.TurretScale.HEAVY
	var atteignable := tuning.turret_reachable_of(lourde)
	var part := tuning.turret_health_of(lourde) / atteignable
	assert_true(part < 0.35,
		"la lourde coute %.0f%% de sa fenetre (plafond 35%%)" % (part * 100.0))
	assert_true(part > 0.12,
		"et elle ne tombe pas en passant : %.0f%% de sa fenetre" % (part * 100.0))

# --- L'invariant refuse-t-il VRAIMENT une inversion ? -------------------------

func test_a_standard_as_tough_as_the_heavy_is_refused() -> void:
	var tuning := _sound()
	tuning.turret_health = tuning.heavy_turret_health
	assert_true(_says(tuning, "hiérarchie des échelles disparaît"),
		"une standard aussi dure que la lourde est refusée : %s" % str(tuning.validate()))

func test_a_heavy_that_turns_as_fast_as_the_standard_is_refused() -> void:
	var tuning := _sound()
	tuning.heavy_turret_turn_rate_deg = tuning.turret_turn_rate_deg
	assert_true(_says(tuning, "la masse doit se payer en lenteur"),
		"une lourde aussi vive que la standard est refusée : %s" % str(tuning.validate()))

func test_a_heavy_seen_no_further_than_the_standard_is_refused() -> void:
	var tuning := _sound()
	tuning.heavy_turret_visible_span = tuning.turret_visible_span
	assert_true(_says(tuning, "ne se distingue pas d'aussi loin"),
		"une lourde qui ne se voit pas de plus loin est refusée")

## ⚠️ LA MARCHE DU BAS DOIT RESTER GARDEE ELLE AUSSI. Ajouter une echelle au milieu est
## exactement le moment ou l'on cesse de verifier celle d'avant.
func test_a_light_as_dense_as_the_standard_is_still_refused() -> void:
	var tuning := _sound()
	tuning.light_turret_burn_interval = tuning.turret_burn_interval
	assert_true(_says(tuning, "inverse la hiérarchie"),
		"une batterie aussi dense que la standard est toujours refusée")

# --- Ce que le NIVEAU pose reellement ----------------------------------------

## Les dix-sept marqueurs du contrat de forge, montes a la main.
func _seventeen_markers() -> Array[Node3D]:
	var section := track(Node3D.new()) as Node3D
	section.name = "Section_01"
	for i in 17:
		var marker := Node3D.new()
		marker.name = "Turret_%02d" % (i + 1)
		section.add_child(marker)
	var sections: Array[Node3D] = [section]
	return sections

## ⚠️ TROIS, PAS DIX-SEPT. Le defaut d'echelle de `CortegeTurret` etait `HEAVY` tant qu'il n'y
## avait que deux familles ; le laisser aurait donne dix-sept pieces a 520 PV au lieu de 180 —
## un niveau trois fois plus dur, et pas une ligne de journal pour le dire.
func test_the_level_poses_exactly_three_heavy_turrets() -> void:
	var manager := track(HardpointsScript.new()) as CortegeHardpoints
	manager.build(_seventeen_markers(), load(SHIPPED), null, null, null)
	var lourdes: Array[String] = []
	for piece in manager.turrets():
		if piece.is_heavy():
			lourdes.append(piece.get_parent().name)
	assert_eq(lourdes.size(), 3,
		"trois lourdes sur dix-sept — « peu d'exemplaires » (planche du 2026-09-05)")
	for nom in lourdes:
		assert_true(nom in HardpointsScript.HEAVY_TURRETS,
			"%s est bien un emplacement declare" % nom)

func test_every_other_marker_carries_a_standard_never_a_light() -> void:
	var manager := track(HardpointsScript.new()) as CortegeHardpoints
	manager.build(_seventeen_markers(), load(SHIPPED), null, null, null)
	for piece in manager.turrets():
		if piece.is_heavy():
			continue
		assert_false(piece.is_light(),
			"%s est une standard : les legeres viennent par batteries, jamais sur un marqueur"
				% piece.get_parent().name)

# --- La geometrie suit l'echelle ---------------------------------------------

## ⚠️ TROIS FACTEURS DISTINCTS, ET LA CIBLE SUIT. Une lourde deux fois plus grande avec la
## hitbox d'une standard serait un vaisseau qu'on rate en visant son blindage.
func test_the_three_scales_have_three_different_sizes() -> void:
	var petite := TurretScript.target_radius_of(CortegeTuning.TurretScale.LIGHT)
	var moyenne := TurretScript.target_radius_of(CortegeTuning.TurretScale.STANDARD)
	var grande := TurretScript.target_radius_of(CortegeTuning.TurretScale.HEAVY)
	assert_true(petite < moyenne and moyenne < grande,
		"les rayons de cible montent avec l'echelle : %.2f < %.2f < %.2f"
			% [petite, moyenne, grande])

## ⚠️ L'EMPRISE DE LA LOURDE EST BORNEE PAR LA COQUE, PAS PAR LA PLANCHE. La plus large
## plateforme que le decor declare fait 3,20 m de rayon (`PAD_RADIUS`, troncon 5) pour une
## emprise de standard de 2,08. Depasser ce rapport ferait deborder la piece dans le vide — vu
## en jeu le 2026-09-05 sur le modele de reference, a 3,62 m d'emprise.
func test_the_heavy_never_outgrows_the_widest_platform_the_hull_declares() -> void:
	const FOOTPRINT_STANDARD := 2.08
	const PAD_RADIUS_MAX := 3.20
	var emprise := FOOTPRINT_STANDARD * TurretScript.HEAVY_GEOM_SCALE
	assert_true(emprise <= PAD_RADIUS_MAX + 0.001,
		"la lourde pose %.2f m de rayon pour %.2f m de plateforme" % [emprise, PAD_RADIUS_MAX])
