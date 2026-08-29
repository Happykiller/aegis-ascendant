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
## Gain d'énergie à menace pleine.
const THREAT_GAIN := 2.4
const ALARM_AMPLITUDE := 0.35

## Amplitude du clignotement d'ARMEMENT. Bien plus creusée que le halètement : à 0,35 la
## coque « respire fort », à 0,8 elle CLIGNOTE — et c'est ce qu'un compte à rebours doit
## faire.
const ARMING_AMPLITUDE := 0.80

## Régime d'une coque ENDORMIE, en fraction du nominal. Une mine qui dort doit
## lire comme éteinte : sans cette atténuation, son réveil part du même niveau
## qu'un ennemi ordinaire et n'a plus aucune amplitude pour se faire remarquer.
const DORMANT_DIM := 0.40

## ⚠️ CE QUE LA MESURE A APPRIS. Monter l'énergie d'un émissif DÉJÀ SATURÉ ne fait
## rien : à la première capture en jeu, la mine en plein télégraphe rendait un pic
## de luminance de 236 quand les dormantes rendaient 215 à 227 — l'engagement était
## DANS la dispersion du repos, donc invisible. Les pixels du noyau étaient déjà à
## 244-255, et multiplier par 2,4 une valeur écrêtée est une opération nulle.
##
## Le fond n'aide pas : la nébuleuse est magenta, exactement la teinte de l'Unisson.
## Ce qui se voit sur un fond lumineux n'est pas l'intensité, c'est le CHANGEMENT DE
## TEINTE. Le Leviathan avait déjà tranché pareil pour son halo de cible : « rester
## dans la teinte de coque le faisait lire comme un reflet » (leviathan_combat.gd).
##
## L'engagement vire donc au blanc chaud, et seulement à partir de l'engagement —
## l'éveil, lui, reste magenta : deux signaux distincts pour deux moments distincts.
const COMMIT_TINT := Color(1.0, 0.94, 0.88)

## Décalage de phase distribué d'une instance à l'autre. Un incrément irrationnel
## (le nombre d'or) plutôt qu'un tirage aléatoire : deux coques voisines sont
## toujours déphasées, et la scène reste reproductible d'un lancement à l'autre.
const PHASE_STEP := 1.6180339887
static var _phase_cursor := 0.0

var _material: StandardMaterial3D
var _base_energy: float = 1.0
var _base_emission: Color = Color.WHITE
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
			vitals._base_emission = vitals._material.emission
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
## `beat_hz` : cadence IMPOSÉE, en battements par seconde. Zéro = le halètement ordinaire.
##
## ⚠️ IL EXISTE PARCE QUE LE HALÈTEMENT ORDINAIRE NE SAIT PAS COMPTER UNE SECONDE. Sa période
## se contracte de 7,0 s à 1,47 s au plus affolé : parfait pour dire « elle monte en régime »
## sur la durée d'une rencontre, inutilisable pour un compte à rebours d'une seconde, où le
## joueur n'en verrait pas un battement entier. Le sursis de la mine impose donc le sien.
func update(delta: float, threat: float, beat_hz: float = 0.0) -> void:
	_age += delta
	var breath := 1.0 + BREATH_AMPLITUDE * sin((_age + _phase) * TAU / BREATH_PERIOD)
	# La période du battement se contracte avec la menace : même geste, tempo qui
	# s'emballe. `lerpf` ne peut pas atteindre zéro, donc pas de division par zéro.
	var alarm_period := BREATH_PERIOD * lerpf(1.0, ALARM_RUSH, threat)
	var amplitude := ALARM_AMPLITUDE
	if beat_hz > 0.0:
		alarm_period = 1.0 / beat_hz
		# Plus creusé que le halètement : un compte à rebours doit se voir du premier coup
		# d'œil, pas se deviner en comparant deux images.
		amplitude = ARMING_AMPLITUDE
	var alarm := 1.0 + amplitude * threat * sin(_age * TAU / alarm_period)
	_material.emission_energy_multiplier = _base_energy * breath * alarm \
		* lerpf(DORMANT_DIM, THREAT_GAIN, threat)
	# La teinte ne bouge qu'au-delà du simple éveil : le magenta dit « elle t'a vu »,
	# le blanc dit « c'est parti ». Confondre les deux, c'est n'en avoir qu'un.
	_material.emission = _base_emission.lerp(COMMIT_TINT, commit_ratio(threat))


## Part d'ENGAGEMENT dans une menace, de 0 (au plus simple éveil) à 1 (charge).
## Pure et statique : c'est elle que testent les assertions de teinte.
static func commit_ratio(threat: float) -> float:
	var span := 1.0 - EnemyReaction.ALERT_CEILING
	if span <= 0.0:
		return 0.0
	return clampf((threat - EnemyReaction.ALERT_CEILING) / span, 0.0, 1.0)


## Remise au repos. Appelée quand l'instance retourne au pool : une coque recyclée
## qui revient en scène déjà en alerte désignerait une menace qui n'existe pas.
func reset() -> void:
	_age = 0.0
	_material.emission_energy_multiplier = _base_energy * DORMANT_DIM
	_material.emission = _base_emission
