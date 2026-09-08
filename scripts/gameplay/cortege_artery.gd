class_name CortegeArtery
extends Node3D
## Les conduites posées le long de l'artère — et rien d'autre.
##
## ⚠️ ELLE EST SÉPARÉE DE [CortegeHardpoints] PARCE QU'ELLE NE POSE PAS SUR DES MARQUEURS. Les
## dix-sept tourelles, les sept ponts et les cinq nœuds sont enfants d'un repère que la coque
## livre ; l'artère n'en a aucun. Les conduites se posent donc par STATION, comme les batteries
## légères se posent par décalage — et c'est la seule chose que ce fichier fait de différent.
##
## ⚠️ ET ELLE FAIT AVANCER SES PIÈCES ELLE-MÊME, même règle que la garnison de poupe : douze
## conduites qui traiteraient chacune leur image, c'est douze appels de script par trame pour un
## travail que rien n'oblige à disperser.

signal conduit_severed(conduit: CortegeConduit)

# ==========================================================================
# LA TABLE DE POSE
# ==========================================================================
#
# Format : [station, |x|, bord, coudée]. `bord` vaut +1 (tribord) ou −1 (bâbord).
#
# ⚠️ AUCUNE NE TOMBE SUR UNE STATION DÉJÀ OCCUPÉE, et ce n'est pas de la courtoisie. Les cinq
# nœuds d'épine (46, 103, 203, 305, 406) sont le SUJET de leur tronçon : une conduite dans leur
# fenêtre volerait le tir qui leur est destiné, et le joueur ne saurait plus laquelle des deux
# lui a rendu quoi. Les dix-sept tourelles et les sept ponts occupent le reste. Le banc mesure
# les écarts sur les tables du générateur, il ne les croit pas sur parole.
#
# ⚠️ ET LE PAS N'EST PAS RÉGULIER. Un métronome se sent, et le niveau en a déjà un — un nœud tous
# les cent mètres. Les écarts vont de 21 à 44 m, et deux tronçons en portent trois quand un autre
# n'en porte que deux.
#
# ⚠️ ELLES ALTERNENT LES BORDS. Douze conduites du même côté feraient de la moitié du cadre une
# zone morte, et le joueur prendrait l'habitude de ne regarder qu'un bord — celui-là même où les
# tourelles ne sont pas.
const CONDUITS: Array = [
	[30.0, 3.60, 1.0, false],
	[58.0, 3.60, -1.0, true],
	[95.0, 4.40, 1.0, false],
	[138.0, 3.60, -1.0, false],
	[163.0, 4.40, 1.0, true],
	[192.0, 3.60, -1.0, false],
	[240.0, 4.40, 1.0, false],
	[277.0, 3.60, -1.0, true],
	[314.0, 4.40, 1.0, false],
	[358.0, 3.60, -1.0, false],
	[394.0, 4.40, 1.0, true],
	[435.0, 3.60, -1.0, false],
]

## L'assise : le pont intérieur, qui borde le canal magenta.
##
## ⚠️ C'EST UNE COTE QUE LA COQUE NE NOUS DONNE PAS. Les marqueurs de tourelle portent leur `y`
## échantillonné sur la peau ; l'artère n'a pas de marqueur, donc celle-ci est POSÉE — et
## `test_cortege_artery.gd` la compare au `y` des marqueurs voisins. Si la peau bouge, le banc le
## dit au lieu de laisser douze conduites flotter.
const DECK_Y := -4.30
## La hauteur de masse : où il faut tirer pour toucher, sous une caméra qui plonge à 70°.
const HIT_LIFT := 0.30
## Longueur d'un tronçon, en mètres de station.
const SECTION_LENGTH := 100.0

var tuning: CortegeTuning = null

var _conduits: Array[CortegeConduit] = []
var _camera: Node3D = null
var _cut: int = 0

# --- La règle, pure et testable sans arbre -------------------------------------

## Les stations, dans l'ordre de la table.
static func stations() -> PackedFloat32Array:
	var out := PackedFloat32Array()
	for entry: Array in CONDUITS:
		out.append(float(entry[0]))
	return out

## Le tronçon qui porte une station, et le `z` local d'un marqueur qui y siège.
##
## ⚠️ LA CONVENTION VIENT DU BINAIRE, PAS D'UNE SUPPOSITION : `Turret_17` est à la station 478,8
## et sa translation vaut `z = −78,8`. Un marqueur porte donc `−(s − 100 × tronçon)`.
static func section_of(station: float) -> int:
	return int(station / SECTION_LENGTH)

static func local_z_of(station: float) -> float:
	return -(station - float(section_of(station)) * SECTION_LENGTH)

## Combien de conduites ont été coupées. ⚠️ LE NIVEAU LIT CE COMPTEUR, LA PIÈCE NE LE TIENT PAS :
## c'est ce qui permet de figer la charge à l'entrée de la poupe sans que la conduite sache qu'une
## poupe existe.
func cut_count() -> int:
	return _cut

func conduits() -> Array[CortegeConduit]:
	return _conduits

# --- La pièce ------------------------------------------------------------------

func build(sections: Array[Node3D], p_tuning: CortegeTuning,
		bullets: BulletManager, vfx: VFXManager, camera: Node3D = null) -> void:
	tuning = p_tuning
	_camera = camera
	for i in CONDUITS.size():
		var entry: Array = CONDUITS[i]
		var station := float(entry[0])
		var index := section_of(station)
		if index < 0 or index >= sections.size():
			continue
		var conduit := CortegeConduit.make(tuning.conduit_health, tuning.conduit_radius,
			tuning.conduit_score)
		conduit.name = "Conduit_%02d" % (i + 1)
		conduit.serial = i
		conduit.section = index
		conduit.damaged_at = tuning.conduit_damaged_at
		conduit.leak_interval = tuning.conduit_leak_interval
		conduit.sever_time = tuning.conduit_sever_time
		conduit.setup(bullets, vfx)
		conduit.position = Vector3(float(entry[1]) * float(entry[2]), DECK_Y,
			local_z_of(station))
		conduit.severed.connect(_on_severed)
		# ⚠️ ENFANT DU TRONÇON, comme tout ce qui vit sur la coque : le défilement l'emmène sans
		# une ligne d'arithmétique, et donc sans aucune façon de désynchroniser une conduite de
		# la peau qu'elle borde.
		sections[index].add_child(conduit)
		conduit.build(bool(entry[3]))
		_conduits.append(conduit)
	print("[Cortege] artère — %d conduites posées sur %d tronçons"
		% [_conduits.size(), sections.size()])

## ⚠️ L'ORDRE EST CELUI DES HARDPOINTS : la pièce est visée par sa MASSE, pas par son assise, et
## la fenêtre de ciblage est `target_span` comme tout le reste du niveau.
func _process(delta: float) -> void:
	var eye := _camera.global_position if is_instance_valid(_camera) else Vector3.ZERO
	var demi := tuning.target_span * 0.5 if tuning != null else 13.0
	for conduit in _conduits:
		var w := conduit.global_position + Vector3(0.0, HIT_LIFT, 0.0)
		var here := GameplayPlane.aim_point_of(w, eye)
		conduit.engage(absf(here.y) <= demi)
		conduit.tick(delta, w, here)

func _on_severed(conduit: CortegeConduit) -> void:
	_cut += 1
	print("[Cortege] conduite %02d coupée — %d/%d sur l'artère"
		% [conduit.serial + 1, _cut, _conduits.size()])
	conduit_severed.emit(conduit)
