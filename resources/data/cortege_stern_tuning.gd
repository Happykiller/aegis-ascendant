class_name CortegeSternTuning
extends Resource
## Les réglages de la phase finale du niveau 2 : l'arrachement des moteurs.
##
## ⚠️ LA POUPE N'EST PAS UN BOSS, ET CE FICHIER DOIT LE RENDRE IMPOSSIBLE À OUBLIER. Il n'y a
## ni barre de vie géante, ni moteur à arroser : **on ne tire pas sur le moteur, on tire sur ses
## attaches**. Le seul point de vie du lot est celui d'un ancrage, et il y en a trois par moteur.
## Un jour où quelqu'un voudra « rendre les moteurs plus durs », c'est ici qu'il faudra le lire.
##
## ⚠️ ET LE PLAFOND DE VOL EST UN INVARIANT, PAS UNE INTENTION. Un groupe moteur livré fait
## 5,49 m de haut et son berceau 4,64 : empilés sur le pont médian du corridor (−4,99), ils
## crèveraient le plan de jeu de plus de cinq mètres. La poupe a donc son PROPRE pont, plus bas
## dans la carène — et `validate()` refuse toute combinaison qui remonterait au-dessus du
## plafond de vol. C'est la décision D5 du plan, fermée par un test plutôt que par un souvenir.

## Où le pont de poupe porte les berceaux, en Y monde. ⚠️ BIEN PLUS BAS QUE LE CORRIDOR : la
## carène descend à −12,60, et c'est cette profondeur-là qui donne la place d'empiler un berceau
## et un moteur sous le plan de vol.
@export var deck_y: float = -11.13

## Les cotes d'un groupe, à l'échelle du jeu. ⚠️ ELLES DÉRIVENT DES BINAIRES LIVRÉS, RÉDUITS.
## Mesuré sur les `.glb` : moteur 9,10 × 5,49 × 11,93 ; berceau 11,19 × 4,64 × 14,00. Le facteur
## est provisoire — il se fixe au LOT 5, sur les repères d'ancrage relevés dans le binaire — et
## il vit ici pour que le jour où il change, une seule ligne change.
@export var asset_scale: float = 0.785
@export var engine_size: Vector3 = Vector3(9.10, 5.49, 11.93)
@export var cradle_size: Vector3 = Vector3(11.19, 4.64, 14.00)
@export var anchor_size: Vector3 = Vector3(2.40, 1.20, 1.40)

## L'entraxe des trois groupes, en unités de plan.
##
## ⚠️ C'EST LA COTE QUI DÉCIDE SI LE JOUEUR PEUT ATTEINDRE LES ANCRAGES EXTÉRIEURS. Il ne va pas
## au-delà de |x| = 14 (`GameplayPlane.BOUNDS`) : trois berceaux livrés à pleine échelle en
## feraient 33,6 de large, et leurs ancrages de bord tomberaient hors de portée — le défaut même
## qu'on vient de fermer sur les tourelles de coque. `validate()` le refuse.
@export var engine_spacing: float = 9.30

## Le moteur central est plus gros (spec §3) — c'est le propulseur principal.
@export var central_scale: float = 1.06

## Où la poupe s'immobilise, en `y` de plan : la station du CENTRE des berceaux.
##
## ⚠️ ELLE EST HORS DE PORTÉE DU JOUEUR, ET C'EST NORMAL. Un groupe fait onze mètres de long
## dans l'axe de poussée, et cet axe pointe vers le HAUT de l'écran : le centre du berceau est
## donc forcément haut, et les moteurs sortent du cadre par le haut — comme sur la planche, où
## les flammes s'échappent hors champ. Ce qui doit être à portée n'est pas le centre du groupe,
## c'est l'ANCRAGE, posé sur sa face avant. C'est `anchor_plane_y()` que `validate()` garde.
@export var hold_plane_y: float = 10.50

## Combien de temps la poupe met à entrer dans le cadre et à s'arrêter.
@export var arrival_time: float = 3.20
## De combien plus haut elle part, en `y` de plan, avant de descendre à `hold_plane_y`.
@export var arrival_rise: float = 22.0

## Les ancrages. ⚠️ TROIS PAR MOTEUR LATÉRAL, QUATRE AU CENTRAL (spec §7).
@export var lateral_anchors: int = 3
@export var central_anchors: int = 4
@export var anchor_health: float = 260.0
@export var anchor_radius: float = 1.10
@export var anchor_score: int = 1400

## Où l'ancrage se pose sur son berceau, en Z local du groupe.
##
## ⚠️ CETTE COTE DÉCIDE S'IL EST ATTEIGNABLE, ET LA PREMIÈRE VALEUR NE L'ÉTAIT PAS. Le berceau
## fait 11 m de profondeur : un ancrage posé au tiers arrière tombe à `y` de plan 9,6, quand le
## joueur ne monte qu'à 8. Il se voyait parfaitement, il était injouable — exactement le défaut
## des tourelles de coque, retrouvé le jour même où on venait de le fermer, sur la SEULE cible
## de la phase. Vu en capture, pas en test : d'où l'invariant ajouté dessous.
@export var anchor_offset_z: float = 5.20

## L'écart entre les DEUX RANGÉES d'ancrages, en `y` de plan.
##
## ⚠️ ILS NE SONT PAS ALIGNÉS, ET LA SPEC LE DESSINE : deux en haut, un (ou deux) en bas. Ce
## n'est pas une coquetterie — sur une seule rangée, les quatre verrous du moteur central se
## touchent (4 × 1,88 m pour un berceau large de 9,31) et se lisent comme UNE barre. Le critère
## d'acceptation n°5 demande qu'on voie « des attaches destructibles », au pluriel. Vu en
## capture : la rangée centrale était une seule barre magenta.
@export var anchor_row_gap: float = 2.20

## La séquence de détachement, en secondes depuis le dernier ancrage abattu (spec §9).
## ⚠️ CE SONT DES INSTANTS, PAS DES DURÉES : ils se lisent dans l'ordre et doivent croître.
@export var detach_shake_at: float = 0.20
@export var detach_burst_at: float = 0.50
@export var detach_tilt_at: float = 0.80
@export var detach_leave_at: float = 1.20
## Quand le moteur cesse d'exister pour le jeu et devient un objet lointain.
@export var detach_gone_at: float = 4.00

## De combien le moteur bascule en quittant son berceau, en degrés (spec §9, « 5 à 10° »).
@export var detach_tilt_degrees: float = 8.0
## Sa vitesse de dérive, en unités de plan par seconde.
@export var drift_speed: float = 7.50

## Le silence final (spec §17). ⚠️ IL PORTE L'AVEU DE LYRA depuis la décision D3 du plan : ce
## n'est plus seulement un contraste visuel, c'est le support de la réplique qui commande tout
## le niveau. `survey_end` dure 5,45 s mesurées et tient 6,5 s à l'écran — d'où le plancher.
@export var silence_time: float = 7.00

@export var engine_score: int = 5200


## L'échelle réelle d'un moteur selon sa place : le central est plus gros.
func scale_of(central: bool) -> float:
	return asset_scale * (central_scale if central else 1.0)

## Combien d'ancrages porte un moteur selon sa place.
func anchors_of(central: bool) -> int:
	return central_anchors if central else lateral_anchors

## Le X de plan du centre d'un groupe : −1 bâbord, 0 centre, +1 tribord.
func slot_x(side: float) -> float:
	return side * engine_spacing

## Le point le plus haut d'un groupe monté, en Y monde. C'est lui qui doit rester sous le plafond.
func stack_top_y(central: bool) -> float:
	var k := scale_of(central)
	return deck_y + cradle_size.y * k + engine_size.y * k

## Le `y` de plan où siègent les ancrages. ⚠️ LE Z LOCAL COMPTE VERS LE BAS DE L'ÉCRAN : un
## ancrage posé en +z est plus PRÈS du joueur que le centre de son berceau.
func anchor_plane_y() -> float:
	return hold_plane_y - anchor_offset_z

## La demi-largeur occupée par les trois groupes, en unités de plan.
func half_span() -> float:
	return engine_spacing + cradle_size.x * scale_of(false) * 0.5


func validate() -> PackedStringArray:
	var errors := PackedStringArray()

	# --- INVARIANT 1 : RIEN NE CRÈVE LE PLAN DE VOL (décision D5) ---------
	#
	# ⚠️ C'EST L'INVARIANT QUI A MOTIVÉ CE FICHIER. Les deux binaires livrés empilent 10,13 m
	# de haut à pleine échelle. Le plafond de jeu est à −2,40 : posés sur le pont du corridor
	# (−4,99), les moteurs traverseraient le plan où vole le joueur — et la seule chose qui
	# l'aurait dit est une capture, prise après coup, si on avait pensé à la prendre là.
	for central in [false, true]:
		var nom := "le moteur central" if central else "un moteur latéral"
		var haut := stack_top_y(central)
		if haut > CortegeFlyby.GAMEPLAY_CEILING_Y:
			errors.append("%s culmine à %.2f alors que le plafond de vol est à %.2f — il traverserait le plan où vole le joueur"
				% [nom, haut, CortegeFlyby.GAMEPLAY_CEILING_Y])

	# --- INVARIANT 2 : TOUS LES ANCRAGES SONT À PORTÉE -------------------
	#
	# ⚠️ « Je vois la pièce, je tire, je ne la touche pas » a déjà coûté une session entière le
	# 2026-09-06 sur les tourelles de coque. Ici le défaut serait pire : les ancrages sont la
	# SEULE cible de la phase. Un ancrage hors de portée, c'est un moteur indétachable.
	var bord := absf(slot_x(1.0)) + cradle_size.x * scale_of(false) * 0.5
	if bord > GameplayPlane.BOUNDS.end.x:
		errors.append("le bord du groupe latéral atteint |x| = %.2f alors que le joueur ne va qu'à %.2f — ses ancrages extérieurs seraient hors de portée"
			% [bord, GameplayPlane.BOUNDS.end.x])
	# ⚠️ ET LE CENTRAL EST PLUS LARGE : sans cette ligne, il entrerait DANS ses voisins. Deux
	# berceaux qui s'interpénètrent ne produisent aucune erreur — ils produisent une capture où
	# l'on ne sait plus quelle attache appartient à quel moteur, sur la seule cible de la phase.
	var jeu := (engine_spacing - cradle_size.x * scale_of(false) * 0.5) \
		- cradle_size.x * scale_of(true) * 0.5
	if jeu < 0.0:
		errors.append("le berceau central mord celui du bord de %.2f m — les ancrages des deux moteurs se mélangeraient"
			% -jeu)
	# ⚠️ ET C'EST L'ANCRAGE QUI DOIT ÊTRE À PORTÉE, PAS LE BERCEAU. Il est posé en avant de son
	# centre ; c'est sa station à lui qui compte, et elle se calcule.
	var y_ancrage := anchor_plane_y()
	if y_ancrage > GameplayPlane.BOUNDS.end.y:
		errors.append("les ancrages sont à y = %.2f alors que le joueur ne monte qu'à %.2f — il les verrait sans pouvoir les atteindre, sur la SEULE cible de la phase"
			% [y_ancrage, GameplayPlane.BOUNDS.end.y])
	# ⚠️ ET IL DOIT ÊTRE DEVANT LE CORPS DU MOTEUR, SINON IL EST ENTERRÉ DESSOUS. Posé sur le
	# berceau mais sous les neuf mètres de moteur, il n'apparaît sur aucune capture — et le
	# joueur cherche une cible qu'il ne peut pas voir. Vu en capture, deux fois de suite.
	var face_moteur := engine_size.z * scale_of(false) * 0.5
	if anchor_offset_z < face_moteur:
		errors.append("l'ancrage est posé à %.2f m du centre alors que le moteur avance jusqu'à %.2f — il serait caché sous sa masse"
			% [anchor_offset_z, face_moteur])
	if y_ancrage - anchor_row_gap < 1.0:
		errors.append("la rangée basse d'ancrages tombe à y = %.2f, dans les jambes du joueur — il n'aurait pas de recul pour viser"
			% (y_ancrage - anchor_row_gap))
	# ⚠️ ET LES DEUX RANGÉES DOIVENT TENIR EN LARGEUR SANS SE TOUCHER. Quatre verrous alignés sur
	# un berceau de neuf mètres se lisent comme une seule barre — vu en capture.
	var par_rangee := int(ceil(float(central_anchors) / 2.0))
	var place := cradle_size.x * scale_of(true) * 0.76
	if float(par_rangee) * anchor_size.x * scale_of(true) * 1.6 > place:
		errors.append("%d ancrages par rangée pour %.2f m utiles : ils se toucheraient et se liraient comme une seule pièce"
			% [par_rangee, place])

	# --- INVARIANT 3 : LA POUPE EST DANS LE CADRE, ET ELLE Y ENTRE -------
	if arrival_rise <= 0.0:
		errors.append("arrival_rise doit être > 0 : la poupe apparaîtrait d'un coup au lieu d'entrer")
	if arrival_time <= 0.0:
		errors.append("arrival_time doit être > 0")

	# --- INVARIANT 4 : LA SÉQUENCE DE DÉTACHEMENT SE LIT DANS L'ORDRE ----
	#
	# ⚠️ ELLE EST ÉCRITE COMME UNE SUITE D'INSTANTS, et deux instants inversés ne produisent
	# aucune erreur : le moteur partirait avant de trembler, et personne ne saurait dire
	# pourquoi la scène « fait bizarre ».
	var etapes: Array = [
		["le tremblement", detach_shake_at], ["la rupture des conduites", detach_burst_at],
		["la bascule", detach_tilt_at], ["le départ du berceau", detach_leave_at],
		["la disparition", detach_gone_at]]
	for i in range(1, etapes.size()):
		var avant: float = etapes[i - 1][1]
		var apres: float = etapes[i][1]
		if apres <= avant:
			errors.append("%s arrive à %.2f s, après %s à %.2f s — la séquence se jouerait à l'envers"
				% [etapes[i][0], apres, etapes[i - 1][0], avant])
	if detach_shake_at <= 0.0:
		errors.append("le tremblement doit commencer après le dernier ancrage, pas avec lui")

	# --- INVARIANT 5 : LES ANCRAGES SONT DES CIBLES, PAS DES CONFETTIS ---
	if lateral_anchors < 2:
		errors.append("un moteur latéral à %d ancrage(s) n'a pas de progression : la spec en demande trois"
			% lateral_anchors)
	if central_anchors < lateral_anchors:
		errors.append("le moteur central porte %d ancrages contre %d au latéral — il doit clore la séquence, pas l'alléger"
			% [central_anchors, lateral_anchors])
	if anchor_health <= 0.0:
		errors.append("anchor_health doit être > 0")
	if anchor_radius <= 0.0:
		errors.append("anchor_radius doit être > 0")

	# --- INVARIANT 6 : LE SILENCE TIENT L'AVEU (décision D3) -------------
	#
	# ⚠️ `survey_end` — l'aveu de Lyra sur le dossier du pilote — se joue DANS ce silence depuis
	# le plan du 2026-09-06. `VOX-0005` mesure la prise à 5,45 s et le `.tres` la tient 6,5 s à
	# l'écran. Un silence plus court couperait la réplique la plus importante du niveau, et le
	# joueur n'aurait aucun moyen de savoir qu'il a manqué quelque chose.
	if silence_time < 6.5:
		errors.append("le silence final dure %.2f s alors que l'aveu de Lyra en tient 6,5 à l'écran — la dernière réplique du niveau serait coupée"
			% silence_time)

	return errors
