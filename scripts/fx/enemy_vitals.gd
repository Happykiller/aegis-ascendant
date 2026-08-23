class_name EnemyVitals
extends RefCounted
## Les signes vitaux d'une coque ennemie : elle respire, et elle s'affole.
##
## Jusqu'ici un ennemi n'avait que trois gestes — le roulis dans son virage, le
## flash quand on le touche, sa plume de réacteur. Entre deux, la coque était un
## objet mort qui glissait vers le bas de l'écran. Ce composant lui donne un
## régime : une respiration lente au repos, et une montée en régime quand elle a
## senti le joueur (`EnemyReaction.threat_ratio`).
##
## ⚠️ ON DUPLIQUE LE MATÉRIAU. Celui importé du `.glb` est partagé par toutes les
## instances, et `AA_Emissive_Engine` porte le même nom sur TOUTES les coques du
## jeu : le muter en place ferait battre le chasseur du joueur au rythme d'une
## mine. Même piège, même parade que `CitadelLife._bind_breath()` et
## `HullDetail.apply()`.
##
## `RefCounted` et non `Node` : il n'a rien à faire dans l'arbre, il meurt avec son
## contrôleur, et il ne peut pas fuir dans un test (`tests/test_case.gd`).

## Respiration au repos, en fraction de l'énergie nominale. À ±10 % la coque vit ;
## au-delà elle clignote comme une alarme, ce qu'elle n'est pas encore.
const BREATH_AMPLITUDE := 0.10
const BREATH_PERIOD := 7.0
## Période du battement d'alerte. NON HARMONIQUE de la respiration, pour que deux
## mines posées côte à côte ne se synchronisent jamais — c'est la synchronisation
## qui trahit la machine (ADR-0015, même raison que les ratios du bestiaire).
const ALARM_PERIOD := 4.3
## Ce que le battement d'alerte devient à menace pleine : presque cinq fois plus
## rapide. Le joueur n'a pas besoin de compter, il entend le régime monter.
const ALARM_RUSH := 0.21
## Gain d'énergie à menace pleine. Le noyau ne change pas de couleur — il chauffe.
const THREAT_GAIN := 2.4
const ALARM_AMPLITUDE := 0.35

## Décalage de phase distribué d'une instance à l'autre. Un incrément irrationnel
## (le nombre d'or) plutôt qu'un tirage aléatoire : deux coques voisines sont
## toujours déphasées, et la scène reste reproductible d'un lancement à l'autre.
const PHASE_STEP := 1.6180339887
static var _phase_cursor := 0.0

var _material: StandardMaterial3D
var _base_energy: float = 1.0
var _phase: float = 0.0
var _age: float = 0.0


## Prépare les signes vitaux d'une coque. Rend `null` si elle n'a pas d'émissif —
## une coque sans noyau n'a rien à faire respirer, et ce n'est pas une erreur.
static func bind(hull: Node3D) -> EnemyVitals:
	if hull == null:
		return null
	for mesh in _meshes(hull):
		for i in mesh.get_surface_override_material_count():
			var base := mesh.get_active_material(i) as StandardMaterial3D
			if base == null or base.resource_name != "AA_Emissive_Engine":
				continue
			var vitals := EnemyVitals.new()
			vitals._material = base.duplicate()
			vitals._base_energy = vitals._material.emission_energy_multiplier
			vitals._phase = _phase_cursor
			_phase_cursor = fposmod(_phase_cursor + PHASE_STEP * BREATH_PERIOD, BREATH_PERIOD)
			mesh.set_surface_override_material(i, vitals._material)
			return vitals
	return null


static func _meshes(node: Node, out: Array[MeshInstance3D] = []) -> Array[MeshInstance3D]:
	var mesh := node as MeshInstance3D
	if mesh != null:
		out.append(mesh)
	for child in node.get_children():
		_meshes(child, out)
	return out


## Une image de vie. `threat` va de 0 (endormie) à 1 (engagée).
## Zéro allocation : on écrit un flottant (spec §31).
func update(delta: float, threat: float) -> void:
	_age += delta
	var breath := 1.0 + BREATH_AMPLITUDE * sin((_age + _phase) * TAU / BREATH_PERIOD)
	# La période du battement se contracte avec la menace : même geste, tempo qui
	# s'emballe. `lerpf` ne peut pas atteindre zéro, donc pas de division par zéro.
	var alarm_period := BREATH_PERIOD * lerpf(1.0, ALARM_RUSH, threat)
	var alarm := 1.0 + ALARM_AMPLITUDE * threat * sin(_age * TAU / alarm_period)
	_material.emission_energy_multiplier = _base_energy * breath * alarm \
		* lerpf(1.0, THREAT_GAIN, threat)


## Remise au repos. Appelée quand l'instance retourne au pool : une coque recyclée
## qui revient en scène déjà en alerte désignerait une menace qui n'existe pas.
func reset() -> void:
	_age = 0.0
	_material.emission_energy_multiplier = _base_energy
