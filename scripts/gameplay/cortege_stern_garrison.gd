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
# Format : [échelle, x, y, z]. Un `x` non nul pose la pièce des DEUX bords ; `x = 0` la pose une
# seule fois sur l'axe. Coordonnées LOCALES à la poupe — qui valent le monde en x et y, et
# `z_local = 508 - s` en profondeur.
const POSTS: Array = [
	# --- Les légères, dans le bassin : elles gardent les berceaux -------------
	# ⚠️ ELLES SONT LÀ ET PAS AILLEURS PARCE QUE LEUR FENÊTRE DE TIR FAIT 14 (demi 7). Une
	# légère sur le massif arrière tomberait à `plan_y = 9,2` : visible, tournée vers le joueur,
	# et muette pour toujours. C'est le défaut symétrique de « elle est visible, pourtant je ne
	# la touche pas », et il ne se voit sur aucun journal.
	[CortegeTuning.TurretScale.LIGHT, 13.60, -11.85, 7.00],
	[CortegeTuning.TurretScale.LIGHT, 6.60, -11.85, 7.00],
	[CortegeTuning.TurretScale.LIGHT, 13.60, -11.85, -7.10],
	[CortegeTuning.TurretScale.LIGHT, 10.00, -11.85, 7.00],
	# --- Les moyennes et les lourdes, sur le plateau du massif arrière --------
	#
	# ⚠️ ET ELLES SONT TOUTES LÀ PARCE QUE C'EST LE SEUL ENDROIT QUI PORTE UN SOCLE, mesuré en
	# REGARDANT (ADR-0006). Une première table posait deux moyennes sur les épaulements de proue,
	# à `y = -5,90` : la capture les a montrées **flottant dans le vide**, moitié sur la coque,
	# moitié sur les étoiles. La cause est arithmétique — le gradin de l'épaulement fait **1,40 m
	# de profondeur** (`z ∈ [8,00 ; 9,40]`) et le socle d'une moyenne **3,32 m** (rayon de
	# service 1,66). Elle débordait de 1 m vers l'avant, au-dessus d'un `|x| = 16,70` où le
	# corridor (demi-largeur 12,04) n'a rien.
	#
	# ⚠️ LA CARÈNE N'A PAS ÉTÉ DESSINÉE AVEC DES PLATES-FORMES D'ARMEMENT. Les étagères de rive
	# font 0,40 à 1,20 m, le gradin 1,40 : aucune ne porte une pièce moyenne. Le plateau du
	# massif (`y = -8,40`, `z <= -8,60`) est la seule surface franche de la poupe. Y ajouter des
	# pads à l'avant est un travail de forge, pas de code — noté au plan.
	[CortegeTuning.TurretScale.STANDARD, 17.40, -8.40, -10.20],
	[CortegeTuning.TurretScale.STANDARD, 13.60, -8.40, -10.20],
	# ⚠️ LES « GROSSES TOURS » DE LA DEMANDE EXISTENT DÉJÀ : les deux tours d'échange thermique
	# (`x = ±5,40`, `z = -10,05`) et les quatre pylônes de rive. Les lourdes se posent entre
	# elles, sur le même plateau — ce lot leur donne des voisines armées, il ne les remplace pas.
	[CortegeTuning.TurretScale.HEAVY, 9.20, -8.40, -10.00],
]

## Le plateau du massif arrière, où se posent les pièces de l'escalade (LOT 2).
const AFT_PLATEAU_Y := -8.40

var tuning: CortegeTuning = null

var _turrets: Array[CortegeTurret] = []
var _camera_eye: Vector3 = Vector3.ZERO

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
	for post in posts():
		var echelle: CortegeTuning.TurretScale = int(post.x) as CortegeTuning.TurretScale
		var turret := CortegeTurret.make(tuning, 0, echelle)
		turret.serial = _turrets.size()
		turret.name = "SternTurret_%02d" % _turrets.size()
		turret.position = Vector3(post.y, post.z, post.w)
		turret.setup(bullets, player, vfx)
		turret.destroyed.connect(_on_turret_destroyed)
		add_child(turret)
		_turrets.append(turret)
	print("[Poupe] garnison — %d tourelles (%d légères, %d moyennes, %d lourdes)"
		% [_turrets.size(), count_of(CortegeTuning.TurretScale.LIGHT),
			count_of(CortegeTuning.TurretScale.STANDARD),
			count_of(CortegeTuning.TurretScale.HEAVY)])

func count_of(echelle: CortegeTuning.TurretScale) -> int:
	var total := 0
	for turret in _turrets:
		if turret.turret_scale == echelle:
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
	for turret in _turrets:
		var w := turret.global_position + Vector3(0.0, turret.hit_lift(), 0.0)
		turret.tick(delta, w, GameplayPlane.aim_point_of(w, eye))

func _on_turret_destroyed(turret: CortegeTurret) -> void:
	turret_destroyed.emit(turret)
