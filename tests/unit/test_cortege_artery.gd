extends "res://tests/test_case.gd"
## La pose des conduites : ou elles tombent, et ce qu'elles ne doivent pas voler.

const TUNING: CortegeTuning = preload("res://resources/levels/long_cortege_tuning.tres")
const Artery := preload("res://scripts/gameplay/cortege_artery.gd")
const HULL := "res://assets/imported/models/backgrounds/long_cortege.glb"
const SCENE := "res://scenes/gameplay/cortege.tscn"

## Les stations deja occupees, LUES dans la coque livree — jamais recopiees du generateur.
## ⚠️ C'EST LE POINT DE CE FICHIER. Recopier ici les tables de `build_long_cortege.py` ferait
## passer ces tests au vert le jour ou une tourelle se deplace, pendant qu'en jeu une conduite
## siegerait dessus.
func _occupied() -> Array:
	var packed: PackedScene = load(HULL)
	assert_true(packed != null, "la coque se charge")
	if packed == null:
		return []
	# ⚠️ ON INSTANCIE, ON NE LIT PAS L'ETAT PACKE. Un nœud de glTF porte un `transform`, jamais une
	# propriete `position` : la chercher dans `SceneState` rend zero marqueur et TROIS tests verts
	# et vides. Le harnais l'a dit ; sans lui on aurait cru la pose verifiee.
	var coque := track(packed.instantiate()) as Node3D
	var out: Array = []
	for node in _descendants(coque):
		var nom := String(node.name)
		if not (nom.begins_with("Turret_") or nom.begins_with("Bay_")
				or nom.begins_with("Spine_")):
			continue
		var n3 := node as Node3D
		if n3 == null:
			continue
		# ⚠️ LA STATION SE RECOMPOSE, ELLE NE SE LIT PAS. Un marqueur porte son `z` DANS SON
		# TRONÇON : `Turret_07` (s = 258) et une conduite a s = 58 ont exactement le meme `z`
		# local, −58. Comparer les `z` a fait echouer six assertions sur des pieces distantes de
		# deux cents metres — le banc avait tort, pas la table.
		var section := _section_index_of(n3)
		out.append([nom, n3.position, float(section) * Artery.SECTION_LENGTH + absf(n3.position.z)])
	return out

## Le rang du tronçon qui porte un marqueur, lu sur la hierarchie (`Section_03` -> 2).
static func _section_index_of(node: Node3D) -> int:
	var courant: Node = node
	while courant != null:
		var nom := String(courant.name)
		if nom.begins_with("Section_"):
			return maxi(nom.substr(8).to_int() - 1, 0)
		courant = courant.get_parent()
	return 0

func _descendants(node: Node, out: Array[Node] = []) -> Array[Node]:
	for child in node.get_children():
		out.append(child)
		_descendants(child, out)
	return out

## ⚠️ AUCUNE CONDUITE DANS LA FENETRE D'UN NŒUD D'EPINE. Le nœud est le SUJET de son tronçon :
## une conduite posee dans sa fenetre volerait le tir qui lui est destine, et le joueur ne
## saurait plus laquelle des deux lui a rendu quoi.
func test_no_conduit_steals_a_spine_node() -> void:
	var occupes := _occupied()
	assert_true(occupes.size() > 20, "la coque porte bien ses marqueurs (%d)" % occupes.size())
	for station in Artery.stations():
		for entree: Array in occupes:
			if not String(entree[0]).begins_with("Spine_"):
				continue
			var ecart := absf(station - float(entree[2]))
			assert_true(ecart >= 8.0,
				"la conduite a s = %.0f est a %.1f m de %s — elle lui volerait son tir"
					% [station, ecart, entree[0]])

## ⚠️ NI SUR UNE TOURELLE, NI SUR UN PONT. Une conduite dans l'emprise d'une plateforme de
## tourelle se lirait comme une piece de la tourelle, et le joueur tirerait sur la mauvaise.
func test_no_conduit_lands_on_an_existing_installation() -> void:
	var occupes := _occupied()
	for station in Artery.stations():
		for entree: Array in occupes:
			var ecart := absf(station - float(entree[2]))
			assert_true(ecart >= 6.0,
				"la conduite a s = %.0f garde %.1f m de %s" % [station, ecart, entree[0]])

## ⚠️ LE PAS N'EST PAS REGULIER. Un metronome se sent, et le niveau en a deja un — un nœud tous
## les cent metres. Si les douze conduites tombaient a intervalle constant, elles deviendraient
## un decor rythmique au lieu d'une occasion.
func test_the_spacing_is_never_a_metronome() -> void:
	var s := Artery.stations()
	assert_true(s.size() >= 10, "il y a bien une dizaine de conduites (%d)" % s.size())
	var ecarts: Array[float] = []
	for i in range(1, s.size()):
		var d := s[i] - s[i - 1]
		assert_true(d > 0.0, "les stations montent")
		ecarts.append(d)
	var mini := ecarts.min() as float
	var maxi := ecarts.max() as float
	assert_true(maxi - mini > 10.0,
		"les ecarts respirent : de %.0f a %.0f m" % [mini, maxi])

## ⚠️ ELLES ALTERNENT LES BORDS. Douze conduites du meme cote feraient de la moitie du cadre une
## zone morte, et le joueur prendrait l'habitude de ne regarder qu'un bord.
func test_the_sides_alternate() -> void:
	var tribord := 0
	for entry: Array in Artery.CONDUITS:
		if float(entry[2]) > 0.0:
			tribord += 1
	var total := Artery.CONDUITS.size()
	assert_true(absi(tribord * 2 - total) <= 2,
		"%d a tribord sur %d — les deux bords sont servis" % [tribord, total])

## ⚠️ LA CONVENTION DE POSE VIENT DU BINAIRE. `Turret_17` est a la station 478,8 et sa
## translation vaut `z = -78,8` : un marqueur porte `-(s - 100 x tronçon)`. Si cette convention
## changeait, douze conduites se poseraient a cent metres de leur place, sans une erreur.
func test_the_placement_convention_matches_the_binary() -> void:
	var occupes := _occupied()
	var vu := false
	for entree: Array in occupes:
		if String(entree[0]) != "Turret_17":
			continue
		vu = true
		var p: Vector3 = entree[1]
		# La tourelle 17 est a s = 478,8 (table du generateur, verifiee ici par le binaire).
		assert_true(absf(p.z - Artery.local_z_of(478.8)) < 0.01,
			"la convention rend %.2f pour la station 478,8, le binaire porte %.2f"
				% [Artery.local_z_of(478.8), p.z])
		assert_true(absf(float(entree[2]) - 478.8) < 0.01,
			"et la station recomposee vaut %.2f" % float(entree[2]))
		assert_eq(Artery.section_of(478.8), 4, "et elle vit au cinquieme tronçon")
	assert_true(vu, "Turret_17 a bien ete trouvee dans la coque")

## ⚠️ L'ASSISE EST POSEE, PAS LUE — et c'est le seul endroit du lot ou une cote ne vient pas de
## l'asset. L'artere n'a aucun marqueur : le `y` des conduites est une constante. Ce test la
## compare au `y` des marqueurs voisins, qui, eux, sont echantillonnes sur la peau. Si la coque
## se reforge et que le pont bouge, il le dit au lieu de laisser douze conduites flotter.
func test_the_deck_height_agrees_with_the_skin() -> void:
	var occupes := _occupied()
	var proches := 0
	for entree: Array in occupes:
		var p: Vector3 = entree[1]
		# Les marqueurs du pont interieur et median : ceux dont le `x` encadre nos conduites.
		if absf(p.x) < 2.0 or absf(p.x) > 10.5:
			continue
		proches += 1
		assert_true(absf(p.y - Artery.DECK_Y) < 0.9,
			"%s est a y = %.2f, l'assise des conduites a %.2f — elles ne flottent pas"
				% [entree[0], p.y, Artery.DECK_Y])
	assert_true(proches > 10, "assez de marqueurs voisins compares (%d)" % proches)
