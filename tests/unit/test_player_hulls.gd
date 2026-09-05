extends "res://tests/test_case.gd"
## Les coques JOUABLES portent-elles les points d'accroche que le contrôleur lit ?
##
## ⚠️ CE TEST FERME UN TROU QUI A COÛTÉ UNE PARTIE ENTIÈRE (2026-09-05). La
## `specter_9_v3` est entrée au dépôt avec trois bouches sur les sept que
## `PlayerFighterController.MUZZLE_NAMES` réclame. La porte de qualité est restée
## verte, le bestiaire l'a montrée sans broncher, et le défaut n'est apparu qu'au
## premier tir en jeu : huit `push_error` au journal, le doublet du **niveau 1**
## replié sur l'axe — deux balles superposées au lieu d'une paire — et quatre
## éclairs de bouche allumés au nombril du vaisseau.
##
## Le contrôleur DÉGRADE au centre au lieu de planter (`_attach_point()`), ce qui
## est le bon comportement en vol mais rend le défaut muet partout ailleurs qu'à
## l'écran. C'est exactement le raisonnement de `test_enemy_hulls.gd` : la
## mécanique était juste, la coque expédiée ne tenait pas son contrat.
##
## Le balayage est volontairement fait sur le DOSSIER et non sur une liste :
## une coque ajoutée demain est couverte sans qu'on y pense.

const CODEX_DIR := "res://resources/codex"

## Le vocabulaire d'accroche que `PlayerFighterController` lit à l'initialisation.
## Recopié plutôt qu'importé : le contrôleur est un `Node3D` avec des `@onready`,
## et les tests ne montent pas d'arbre de scène. Le test ci-dessous garde les deux
## listes d'accord.
const REQUIRED_POINTS: Array[String] = [
	"Muzzle_L", "Muzzle_R", "Muzzle_Wing_L", "Muzzle_Wing_R",
	"Muzzle_C", "Muzzle_Tip_L", "Muzzle_Tip_R",
	"Engine_L", "Engine_R",
]

func _playable_hulls() -> Array[PackedScene]:
	var found: Array[PackedScene] = []
	var dir := DirAccess.open(CODEX_DIR)
	if dir == null:
		return found
	for file in dir.get_files():
		if not file.ends_with(".tres"):
			continue
		var entry := load("%s/%s" % [CODEX_DIR, file]) as CodexEntry
		if entry != null and entry.playable_hull != null:
			found.append(entry.playable_hull)
	return found

func test_every_playable_hull_carries_every_attach_point_the_controller_reads() -> void:
	var hulls := _playable_hulls()
	assert_true(hulls.size() > 0, "le codex déclare bien des coques jouables")
	for packed in hulls:
		var hull := track(packed.instantiate()) as Node3D
		for point_name in REQUIRED_POINTS:
			assert_true(hull.get_node_or_null(NodePath(point_name)) != null,
				"%s porte '%s'" % [packed.resource_path.get_file(), point_name])

## ⚠️ ENFANT DIRECT, PAS DESCENDANT. `_attach_point()` fait un `get_node_or_null()`
## sur la coque et lit la `position` LOCALE du nœud trouvé. Un point rangé sous une
## pièce du `.glb` — le réflexe d'`ADR-0046` §3, pour qu'il suive l'aile — serait
## introuvable, et s'il l'était sa position serait exprimée dans le repère de l'aile.
## Tant que le contrôleur lit ainsi, la profondeur fait partie du contrat.
func test_the_attach_points_are_direct_children() -> void:
	for packed in _playable_hulls():
		var hull := track(packed.instantiate()) as Node3D
		for child in hull.get_children():
			if not child.name.begins_with("Muzzle_") and not child.name.begins_with("Engine_"):
				continue
			assert_true(child is Node3D,
				"%s/%s est un Node3D : le contrôleur lit sa position" % [
					packed.resource_path.get_file(), child.name])

## Les deux listes doivent rester d'accord — sinon ce fichier valide un contrat
## que le jeu n'a plus.
func test_the_required_points_match_the_controller() -> void:
	var source := FileAccess.get_file_as_string(
		"res://scripts/player/player_fighter_controller.gd")
	assert_true(not source.is_empty(), "le contrôleur se lit")
	for point_name in REQUIRED_POINTS:
		assert_true(source.contains('"%s"' % point_name),
			"'%s' est bien un nom lu par le contrôleur" % point_name)
