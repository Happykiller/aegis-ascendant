class_name CortegeSternGarrison
extends Node3D
## L'armement de la poupe — ce qui rend la phase finale disputée.
##
## ⚠️ ELLE EXISTE PARCE QUE LA PHASE SE JOUAIT SANS ADVERSAIRE. « Aujourd'hui, il n'y a rien, on
## tire sur les trucs » (opérateur, 2026-09-07, après avoir joué la phase de bout en bout sans
## perdre un point de bouclier). Dix verrous, trois moteurs, et pas une seule chose qui riposte :
## le seul danger était la colonne de poussée, qu'il suffit de ne pas traverser.
##
## ⚠️ ELLE ASSUME UN ÉCART À LA SPEC §19 — « je réduirais énormément les ennemis, pas de
## respawn ». Ce qui en est gardé : **pas de respawn** (une pièce abattue reste abattue), et les
## moteurs restent les protagonistes. Ce qui est levé : le vide. Voir le plan
## `docs/plans/2026-09-07-la-poupe-se-defend.md`.
##
## ⚠️ ELLE FAIT AVANCER SES PIÈCES ELLE-MÊME. Même règle que [CortegeHardpoints] : quatorze
## tourelles qui traiteraient chacune leur image, c'est quatorze appels de script par trame pour
## un travail que rien n'oblige à disperser — et surtout un ordre de passage indéfini, alors
## qu'un palier d'escalade doit pouvoir durcir une pièce AVANT qu'elle ne tire dans la trame.

signal turret_destroyed(turret: CortegeTurret)

# ==========================================================================
# LA TABLE DE PLACEMENT
# ==========================================================================
#
# ⚠️ IL N'Y A QUE DEUX ZONES LIBRES, ET C'EST MESURÉ SUR LE BINAIRE. Les trois emprises de
# berceau se recouvrent (`BRIEF-0106-report.md` §1) et n'en forment qu'une :
#
#     |x| <= 15,78   et   |z| <= 8,00      ->  interdit au-dessus du pont
#
# Restent les flancs (`|x| >= 16,20`), le massif arrière (`z <= -8,60`)… et deux bandes que le
# rapport ne compte pas parce qu'elles sont AU NIVEAU du pont et non au-dessus : la dalle du
# bassin déborde les berceaux de 1,9 m à l'avant (`z` jusqu'à 7,95) et de 2,1 m à l'arrière.
#
# ⚠️ ET UNE PIÈCE POSÉE DANS CES BANDES NE MASQUE RIEN, ce qui n'allait pas de soi. La caméra
# regarde depuis `z = +5` : une pièce en `z` plus grand est plus PRÈS d'elle, donc pourrait
# occulter. Mais elle est aussi plus BAS à l'écran — une légère sur la bande avant tombe à
# `plan_y = -2,6` quand les verrous sont entre `-0,5` et `+3,8`. Elle se lit sous eux, jamais
# devant. Vérifié par capture, pas par ce raisonnement.
#
# Format : [échelle, x, y, z, palier, volante]. Un `x` non nul pose la pièce des DEUX bords ;
# `x = 0` la pose une seule fois sur l'axe. Le PALIER est le moment où elle s'éveille : 0 dès
# l'arrivée, 1 au premier moteur arraché, 2 au second, 3 quand le central s'expose. VOLANTE
# ajoute sous elle une plate-forme qui flotte — voir plus bas.
#
# ⚠️ LA RÉSERVE EST POSÉE DÈS LE DÉBUT, ELLE DORT. Elle n'apparaît pas : elle est là, visible,
# l'œil éteint, et le joueur peut la nettoyer avant qu'elle ne serve — c'est ce qui fait de
# l'escalade une chose qu'on peut PRÉVENIR plutôt qu'une punition.
#
# ⚠️ ET LA PREMIÈRE VERSION SE CHEVAUCHAIT. « On a beaucoup de chevauchement » (opérateur,
# 2026-09-07, capture à l'appui) : six légères alignées sur la lèvre avant du bassin, hitboxes
# jointives, plus quatre pièces empilées sur le massif arrière. Le défaut n'est pas dans les
# cotes prises une à une — chacune passait ses invariants — mais dans leur ENSEMBLE projeté :
# deux pièces distantes de trois mètres sur la coque ne le sont plus à l'écran, où la projection
# les rapproche. C'est désormais un invariant à part entière (`test_no_two_pieces_overlap`).
const POSTS: Array = [
	# --- LA FIN DU CORPS DU VAISSEAU (`z_local >= 11`) ------------------------
	#
	# ⚠️ LE GRAND PONT VIDE DEVANT LA POUPE, et il l'était pour rien. « Tu pourrais mettre des
	# canons sur la fin du corps du vaisseau » (opérateur). La dernière tourelle du corridor est
	# à `s = 478,8` : les vingt derniers mètres de coque — ceux qui remplissent le bas du cadre
	# pendant TOUTE la phase — n'avaient pas une seule pièce. C'est aussi la seule menace du
	# niveau qui tire vers le HAUT de l'écran, donc depuis un endroit que le joueur ne surveille
	# pas.
	[CortegeTuning.TurretScale.STANDARD, 4.60, -4.34, 12.50, 0, false],
	[CortegeTuning.TurretScale.LIGHT, 8.60, -4.94, 13.00, 1, false],
	# --- LES PLATES-FORMES VOLANTES ------------------------------------------
	#
	# ⚠️ ELLES RÉSOLVENT LE PROBLÈME QUE LA CARÈNE POSE. « Pour la profondeur, on pourrait faire
	# des plateformes volantes » (opérateur) — et c'est la réponse à ce qui bloquait le lot
	# depuis le début : la poupe n'a AUCUNE surface plane de plus de 1,40 m hors du massif
	# arrière, si bien que toute pièce moyenne posée sur un gradin flottait à moitié dans le
	# vide. Une plate-forme qui flotte VRAIMENT ne ment plus : elle donne une assise franche à
	# n'importe quelle hauteur, et elle décolle les pièces les unes des autres en profondeur.
	#
	# ⚠️ ET ELLES RESTENT HORS DE L'EMPRISE. Flotter ne dispense de rien : une plate-forme au-
	# dessus du bassin masquerait un verrou exactement comme un pylône. Elles vivent donc sur
	# les flancs (`|x| > 15,78`) ou en avant (`z > 8,00`), comme tout le reste.
	[CortegeTuning.TurretScale.STANDARD, 17.00, -7.20, 2.00, 1, true],
	[CortegeTuning.TurretScale.LIGHT, 6.00, -6.00, 9.50, 0, true],
	# --- LE BASSIN : deux légères qui gardent, et pas six qui se marchent dessus
	[CortegeTuning.TurretScale.LIGHT, 13.60, -11.85, 7.00, 0, false],
	[CortegeTuning.TurretScale.LIGHT, 13.60, -11.85, -7.10, 2, false],
	# --- LE BOUT DU MUR : le plateau du massif arrière ------------------------
	#
	# ⚠️ LES « GROSSES TOURS » DE LA DEMANDE EXISTENT DÉJÀ : les deux tours d'échange thermique
	# (`x = ±5,40`, `z = -10,05`) et les quatre pylônes de rive. Les lourdes se posent entre
	# elles, sur le même plateau — ce lot leur donne des voisines armées, il ne les remplace pas.
	[CortegeTuning.TurretScale.STANDARD, 17.40, -8.40, -10.20, 0, false],
	[CortegeTuning.TurretScale.HEAVY, 9.20, -8.40, -10.00, 3, false],
]

## La plate-forme volante : une dalle, un liseré, et un ballant.
##
## ⚠️ LE BALLANT EST DÉTERMINISTE ET LENT. Déterministe parce qu'un survol se juge en comparant
## deux captures — même règle que la flamme et que le tremblement d'arrachement. Lent parce
## qu'une plate-forme qui oscille vite se lit comme un objet instable, et le joueur cherche à
## anticiper un mouvement au lieu de viser ce qu'elle porte.
const PAD_BOB := 0.22
const PAD_HZ := 0.19
const PAD_THICK := 0.52
const PAD_TINT := Color("d93d9c")

## Le plateau du massif arrière, où se posent les pièces de l'escalade (LOT 2).
const AFT_PLATEAU_Y := -8.40

var tuning: CortegeTuning = null

var _turrets: Array[CortegeTurret] = []
## Le palier d'éveil de chaque pièce, indexé comme `_turrets`.
var _tiers: PackedInt32Array = PackedInt32Array()
var _tier: int = 0
var _camera_eye: Vector3 = Vector3.ZERO
var _pads: Array[Node3D] = []
var _pad_rest: PackedFloat32Array = PackedFloat32Array()
var _pad_clock: float = 0.0

static func make(p_tuning: CortegeTuning) -> CortegeSternGarrison:
	var garrison := CortegeSternGarrison.new()
	garrison.name = "Garrison"
	garrison.tuning = p_tuning
	return garrison

# --- La règle, pure et testable sans arbre -------------------------------------

## Les postes développés : chaque entrée mirroir devient ses deux pièces.
##
## ⚠️ RENDUE STATIQUE PARCE QUE LE BANC EN A BESOIN SANS ARBRE. Vérifier qu'aucune pièce ne sort
## du plan de vol demande de connaître ses quatorze positions ; les faire naître pour les lire
## imposerait un `BulletManager`, un joueur et une caméra — et le banc ne les a pas.
static func posts() -> Array[Vector4]:
	var out: Array[Vector4] = []
	for entry: Array in POSTS:
		var echelle := float(entry[0])
		var x := float(entry[1])
		var y := float(entry[2])
		var z := float(entry[3])
		if is_zero_approx(x):
			out.append(Vector4(echelle, 0.0, y, z))
			continue
		out.append(Vector4(echelle, x, y, z))
		out.append(Vector4(echelle, -x, y, z))
	return out

## Le palier d'éveil de chaque poste, dans le même ordre que [method posts].
##
## ⚠️ RENDU À PART ET NON DANS LE `Vector4`, faute de place : les quatre composantes sont déjà
## prises par l'échelle et la position. Deux tableaux parallèles se désynchronisent — d'où le
## test qui compare leurs tailles, et le fait qu'ils soient produits par la MÊME boucle.
static func tiers() -> PackedInt32Array:
	var out := PackedInt32Array()
	for entry: Array in POSTS:
		out.append(int(entry[4]))
		if not is_zero_approx(float(entry[1])):
			out.append(int(entry[4]))
	return out

## Quelles pièces sont portées par une plate-forme volante, dans l'ordre de [method posts].
static func flying() -> Array[bool]:
	var out: Array[bool] = []
	for entry: Array in POSTS:
		out.append(bool(entry[5]))
		if not is_zero_approx(float(entry[1])):
			out.append(bool(entry[5]))
	return out

## Le rayon d'assise d'une échelle — ce que la pièce OCCUPE, et non ce qu'une balle touche.
## ⚠️ IL DÉCIDE DU CHEVAUCHEMENT, et il n'est pas le rayon de cible : une lourde tient dans un
## disque de deux mètres alors que sa hitbox en fait un et demi.
static func footprint_of(echelle: CortegeTuning.TurretScale) -> float:
	match echelle:
		CortegeTuning.TurretScale.LIGHT:
			return CortegeTurret.SERVICE_RADIUS * CortegeTurret.LIGHT_GEOM_SCALE
		CortegeTuning.TurretScale.HEAVY:
			return CortegeTurret.SERVICE_RADIUS * CortegeTurret.HEAVY_GEOM_SCALE
	return CortegeTurret.SERVICE_RADIUS

## Où la hitbox d'un poste tombe dans le plan de jeu, la poupe étant immobilisée.
##
## ⚠️ C'EST LA FONCTION QUI GARDE TOUT CE LOT, et elle existe parce que le piège a déjà coûté
## deux défauts rapportés en jouant. Une pièce posée sur la coque n'est PAS touchable là où elle
## est : `aim_point_of` la projette, et le facteur `t = -14 / (y - 14)` dépend de sa HAUTEUR.
## Une lourde perchée à `y = -3,30` voit sa hitbox partir à `0,81 × x`, contre `0,54` pour la
## même pièce posée sur le pont — soit deux mètres et demi d'écart sur un flanc.
##
## ⚠️ ET LE RÉGLAGE DE LA POUPE, LUI, RAISONNE EN MONDE 1:1. `hold_plane_y`, `anchor_reach()`,
## `anchor_rows()` traitent `world.xz` comme `plane.xy`. C'est conservateur pour les ancrages —
## leur hitbox réelle est PLUS près du centre que le réglage ne le croit — mais ce serait un
## piège pour tout ce qu'on pose plus haut. Aucune cote de cette table n'est écrite à vue :
## `test_cortege_stern_garrison.gd` les projette toutes et refuse celles qui sortent.
static func plane_post(post: Vector4, lift: float, stern_z: float, eye: Vector3) -> Vector2:
	var world := Vector3(post.y, post.z + lift, stern_z + post.w)
	return GameplayPlane.aim_point_of(world, eye)

## La demi-fenêtre de TIR d'une échelle : au-delà, la pièce vise et ne tire jamais.
static func fire_half_of(p_tuning: CortegeTuning, echelle: CortegeTuning.TurretScale) -> float:
	return p_tuning.turret_fire_span_of(echelle) * 0.5

# --- La pièce ------------------------------------------------------------------

## Monte la garnison. ⚠️ APPELÉE APRÈS QUE LA POUPE EST DANS L'ARBRE : `CortegeTurret._ready()`
## construit sa tête, et une tourelle montée hors de l'arbre resterait sans canon.
func build(bullets: BulletManager, player: PlayerFighterController, vfx: VFXManager) -> void:
	var paliers := tiers()
	var volantes := flying()
	for i in posts().size():
		var post := posts()[i]
		var echelle: CortegeTuning.TurretScale = int(post.x) as CortegeTuning.TurretScale
		var turret := CortegeTurret.make(tuning, 0, echelle)
		turret.serial = _turrets.size()
		turret.name = "SternTurret_%02d" % _turrets.size()
		turret.setup(bullets, player, vfx)
		turret.destroyed.connect(_on_turret_destroyed)
		# ⚠️ LA PIÈCE VOLANTE EST ENFANT DE SA DALLE, PAS DE LA GARNISON. C'est ce qui la fait
		# ballotter AVEC elle sans une ligne d'arithmétique — et donc sans aucune façon de
		# désynchroniser un canon de la plate-forme qui le porte.
		if volantes[i]:
			var pad := _build_pad(Vector3(post.y, post.z, post.w), echelle, i)
			add_child(pad)
			pad.add_child(turret)
		else:
			turret.position = Vector3(post.y, post.z, post.w)
			add_child(turret)
		_turrets.append(turret)
		_tiers.append(paliers[i])
		if paliers[i] > 0:
			turret.sleep_now()
	print("[Poupe] garnison — %d tourelles (%d légères, %d moyennes, %d lourdes), %d en réserve"
		% [_turrets.size(), count_of(CortegeTuning.TurretScale.LIGHT),
			count_of(CortegeTuning.TurretScale.STANDARD),
			count_of(CortegeTuning.TurretScale.HEAVY), asleep_count()])

func count_of(echelle: CortegeTuning.TurretScale) -> int:
	var total := 0
	for turret in _turrets:
		if turret.turret_scale == echelle:
			total += 1
	return total

## Passe au palier `tier` : réveille ce qui l'attendait et durcit tout ce qui vit.
##
## ⚠️ ELLE NE REDESCEND JAMAIS. « Le vaisseau réagit à ce qu'on lui prend » : un palier qui
## retomberait quand une pièce meurt récompenserait le joueur deux fois et rendrait la fin plus
## facile que le début — l'exact inverse de ce que l'escalade raconte.
func set_tier(tier: int, pressure: float) -> int:
	if tier <= _tier:
		return 0
	_tier = tier
	var reveilles := 0
	for i in _turrets.size():
		var turret := _turrets[i]
		if not turret.is_alive():
			continue
		turret.pressure = pressure
		if _tiers[i] <= tier and turret.asleep:
			turret.wake()
			reveilles += 1
	print("[Poupe] palier %d — %d tourelle(s) réveillée(s), cadence ×%.2f"
		% [tier, reveilles, pressure])
	return reveilles

func tier() -> int:
	return _tier

func asleep_count() -> int:
	var total := 0
	for turret in _turrets:
		if turret.asleep and turret.is_alive():
			total += 1
	return total

func turrets() -> Array[CortegeTurret]:
	return _turrets

func alive_count() -> int:
	var total := 0
	for turret in _turrets:
		if turret.is_alive():
			total += 1
	return total

## Un pas. ⚠️ `hit_lift()` ET NON UNE CONSTANTE : les trois échelles n'ont pas la même hauteur de
## masse, et c'est elle qui décide où il faut tirer pour toucher sous une caméra qui plonge à
## 70°. Appliquer la hauteur de la lourde à une légère ferait viser à côté — le défaut exact que
## `aim_point_of` a été écrit pour corriger, réintroduit par la table.
func tick(delta: float, eye: Vector3) -> void:
	_camera_eye = eye
	_pad_clock += delta
	for i in _pads.size():
		var pad := _pads[i]
		pad.position.y = _pad_rest[i] + PAD_BOB * sin((_pad_clock + float(i) * 1.37) * PAD_HZ * TAU)
	for turret in _turrets:
		var w := turret.global_position + Vector3(0.0, turret.hit_lift(), 0.0)
		turret.tick(delta, w, GameplayPlane.aim_point_of(w, eye))

## Bâtit la dalle. Elle porte son canon et rien d'autre.
func _build_pad(where: Vector3, echelle: CortegeTuning.TurretScale, index: int) -> Node3D:
	var pad := Node3D.new()
	pad.name = "Pad_%02d" % index
	pad.position = where
	var large := footprint_of(echelle) * 2.0 + 0.9
	var dalle := MeshInstance3D.new()
	dalle.name = "Slab"
	var box := BoxMesh.new()
	box.size = Vector3(large, PAD_THICK, large)
	dalle.mesh = box
	dalle.position.y = -PAD_THICK * 0.5
	var mat := StandardMaterial3D.new()
	# ⚠️ PLUS CLAIRE QUE LA COQUE, ET C'EST VOULU. Une dalle du même anthracite que le vaisseau,
	# vue de dessus sur fond de vaisseau, se lit comme un trou. Elle doit se DÉTACHER de ce
	# qu'elle survole, sinon elle n'existe pas.
	mat.albedo_color = Color(0.155, 0.150, 0.180)
	mat.metallic = 0.55
	mat.roughness = 0.44
	dalle.material_override = mat
	pad.add_child(dalle)
	# ⚠️ LE LISERÉ DÉBORDE LA DALLE AU LIEU DE SE CACHER DESSOUS, et la première version se
	# cachait dessous. La caméra plonge à 70° : elle ne voit JAMAIS la face inférieure d'une
	# pièce horizontale. Une lueur posée là est un effet qu'on paie et que personne ne verra —
	# et c'est ce que la capture a montré. Débordant de 7 %, elle dessine au contraire un contour
	# lumineux tout autour de la silhouette, vu de dessus : c'est ce contour qui dit « rien ne
	# la tient ».
	var liseré := MeshInstance3D.new()
	liseré.name = "Glow"
	var plaque := BoxMesh.new()
	plaque.size = Vector3(large * 1.16, 0.11, large * 1.16)
	liseré.mesh = plaque
	liseré.position.y = -PAD_THICK * 0.92
	liseré.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var lueur := StandardMaterial3D.new()
	lueur.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	lueur.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	lueur.albedo_color = PAD_TINT
	lueur.emission_enabled = true
	lueur.emission = PAD_TINT
	lueur.emission_energy_multiplier = 3.1
	liseré.material_override = lueur
	pad.add_child(liseré)
	_pads.append(pad)
	_pad_rest.append(where.y)
	return pad

func _on_turret_destroyed(turret: CortegeTurret) -> void:
	turret_destroyed.emit(turret)
