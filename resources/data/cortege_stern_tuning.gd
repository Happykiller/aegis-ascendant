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
## ⚠️ L'ORDRE DES AXES VIENT DU BINAIRE, PAS DE LA PLANCHE. La planche cote « 2,40 × 1,40 × 1,20
## (L × l × h) » ; le `.glb`, en Y-up, mesure 1,40 × 1,21 × 2,40 — la LONGUEUR est en Z. Recopier
## la planche mettait 2,40 en X : le bandeau d'état sortait de la pièce et sa hitbox se comparait
## à la mauvaise cote.
@export var anchor_size: Vector3 = Vector3(1.40, 1.21, 2.40)

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

## En dessous de cette part de vie, l'ancrage passe en ENDOMMAGÉ : plaques ouvertes, cœur à nu,
## étincelles. ⚠️ IL BRILLE ALORS PLUS FORT QU'INTACT, ce qui est contre-intuitif et voulu : la
## planche le dessine ouvert, et un état qui s'assombrit se lirait comme un état qui s'éteint —
## c'est-à-dire comme un verrou déjà rompu.
@export var anchor_damaged_at: float = 0.45
## Entre deux gerbes d'un ancrage endommagé. ⚠️ C'EST LE SEUL SIGNAL QUI PORTE À DISTANCE : le
## battement se voit quand on regarde la pièce, l'étincelle se voit du coin de l'œil.
@export var anchor_spark_interval: float = 0.55

## --- LES SOCKETS D'ANCRAGE, RELEVÉS DANS LE BINAIRE LIVRÉ (LOT 5) -------------
##
## ⚠️ CE NE SONT PLUS DES COTES INVENTÉES. `berceau_moteur.glb` porte un contrat de repères en
## clair — `CTRL | Socket ancrage AV/AR D/G`, des nœuds sans maillage — et ce sont eux qui
## disent où un verrou se pose. Relevés (glTF, Y-up, mètres à l'échelle 1) :
##
##   AV D (+3,700 ; +2,650 ; −3,950)     AR D (+3,700 ; +2,450 ; +4,480)
##   AV G (−3,700 ; +2,650 ; −3,950)     AR G (−3,700 ; +2,450 ; +4,480)
##
## ⚠️ ET LE LATÉRAL DE L'ANCRAGE N'EST PAS CELUI DU BERCEAU : 3,700 contre 5,595 de demi-largeur.
## Le berceau déborde de deux mètres au-delà de ses propres verrous — toute la contrainte de
## portée du LOT 1 portait donc sur la mauvaise cote, et c'est ce qui la rendait si serrée.
@export var socket_x: float = 3.700
@export var socket_y: float = 2.550
## Profondeur des deux rangées, en Z glTF. ⚠️ LE SIGNE COMPTE : la sortie du moteur va vers −Z
## (Blender +Y à l'export), donc la rangée AVANT est plus HAUT à l'écran que la rangée ARRIÈRE.
@export var socket_z_front: float = -3.950
@export var socket_z_rear: float = 4.480

## Où le moteur se pose DANS le berceau — le contrat de mariage écrit par l'auteur du berceau :
## « placer le moteur 01 v2 sans rotation à (0 ; 1 ; 3,7) m », semelles à Z = 0,89.
## ⚠️ CONVERTI EN Y-UP : Blender (x, y, z) devient glTF (x, z, −y), donc (0 ; 3,7 ; −1,0).
@export var engine_seat: Vector3 = Vector3(0.0, 3.70, -1.00)

## La séquence de détachement, en secondes depuis le dernier ancrage abattu (spec §9).
## ⚠️ CE SONT DES INSTANTS, PAS DES DURÉES : ils se lisent dans l'ordre et doivent croître.
@export var detach_shake_at: float = 0.20
@export var detach_burst_at: float = 0.50
@export var detach_tilt_at: float = 0.80
@export var detach_leave_at: float = 1.20
## Quand le moteur cesse d'exister pour le jeu et devient un objet lointain.
@export var detach_gone_at: float = 4.00

## Les conduites qui relient le moteur à sa coque. ⚠️ ELLES NE SONT PAS DÉCORATIVES : ce sont
## elles qui rendent l'arrachement lisible AVANT que quoi que ce soit ne bouge. Entre le dernier
## verrou et le départ il s'écoule 1,2 s ; sans une rupture visible à 0,5 s, cette seconde est un
## temps mort où le joueur croit que rien ne s'est passé.
@export var conduit_count: int = 3
@export var conduit_width: float = 0.34

## De combien le moteur TREMBLE avant de partir, en unités de plan (spec §9, T+0,2 s).
## ⚠️ IL TREMBLE, IL NE GLISSE PAS. Le tremblement dit « ça cède » ; un glissement dirait
## « ça tombe », et la pièce ne serait plus arrachée, elle serait lâchée.
@export var detach_shake_amplitude: float = 0.16
@export var detach_shake_hz: float = 21.0

## De combien le moteur bascule en quittant son berceau, en degrés (spec §9, « 5 à 10° »).
@export var detach_tilt_degrees: float = 8.0
## Sa vitesse de dérive, en unités de plan par seconde.
@export var drift_speed: float = 7.50

## La rotation propre du moteur CENTRAL pendant sa dérive, en degrés par seconde.
##
## ⚠️ ELLE N'APPARTIENT QU'À LUI (spec §10). Les deux latéraux partent chacun de leur côté : leur
## direction suffit à les distinguer l'un de l'autre. Le central part droit vers le haut — sans
## rotation, il serait le seul dont le départ ne raconte rien de particulier, alors que c'est
## celui qui clôt la séquence.
@export var central_spin_deg: float = 34.0

## La secousse rendue au joueur quand un groupe s'arrache (spec §13 : « le vaisseau doit
## réagir »). ⚠️ ELLE EST PLUS FORTE POUR LE CENTRAL, qui coupe la dernière propulsion.
@export var detach_trauma: float = 0.42
@export var detach_trauma_central: float = 0.75

## Le silence final (spec §17). ⚠️ IL PORTE L'AVEU DE LYRA depuis la décision D3 du plan : ce
## n'est plus seulement un contraste visuel, c'est le support de la réplique qui commande tout
## le niveau. `survey_end` dure 5,45 s mesurées et tient 6,5 s à l'écran — d'où le plancher.
@export var silence_time: float = 7.00

## --- La flamme et la poussée (spec §5 et §6) ---------------------------------

## La longueur et la largeur du panache au repos, en unités de plan.
## ⚠️ IL SORT DU CADRE PAR LE HAUT, ET C'EST VOULU — comme sur la planche, où les flammes
## s'échappent hors champ. Ce que le joueur doit voir, c'est sa BASE : un panache entièrement
## contenu dans l'écran ferait paraître les moteurs petits.
@export var flame_length: float = 9.0
@export var flame_width: float = 2.4

## Le cycle de poussée (spec §6 et §15) : calme, charge annoncée, souffle, puis — pour le
## central seul — une extinction pendant laquelle le joueur a la voie libre.
##
## ⚠️ LE PRÉAVIS N'EST PAS UNE POLITESSE, C'EST LA MÉCANIQUE. Sans lui, une poussée qui blesse
## est une taxe et non une difficulté (spec §11.2) : le joueur ne peut pas apprendre ce qu'il ne
## voit pas venir. La spec chiffre 300 à 500 ms — assez pour sortir de la voie, trop peu pour
## flâner.
@export var surge_period: float = 4.60
@export var surge_warning: float = 0.42
@export var surge_blast: float = 0.95
## L'extinction du central après la perte des deux latéraux (spec §15) : une fenêtre très
## confortable pour attaquer. Elle n'appartient qu'à lui.
@export var surge_vent: float = 1.00

## De combien la flamme enfle pendant la charge, puis pendant le souffle.
@export var surge_charge_gain: float = 1.35
@export var surge_blast_gain: float = 2.30

## Ce que coûte UN CONTACT avec le souffle.
##
## ⚠️ CE N'EST PAS UN TAUX PAR SECONDE, ET LA PREMIÈRE VERSION EN ÉTAIT UN. Elle infligeait
## `46 × delta` à chaque image — sauf que `PlayerShield.take_hit()` accorde **1,2 s
## d'invulnérabilité** après tout coup encaissé. Sur un souffle de 0,95 s, le joueur prenait
## donc EXACTEMENT une image de dégâts, soit 0,77 point sur 100 : mesuré en jeu, le bouclier
## affichait 99. La zone était décorative, et rien ne le disait — le code se lisait comme s'il
## infligeait cinquante fois plus.
##
## Le vrai modèle est donc une MORSURE par contact, cadencée par l'invulnérabilité du bouclier
## et non par notre horloge. À 26 sur 100, tenir dans une voie coûte un quart de réserve par
## souffle : assez pour ne jamais y rester, pas assez pour qu'une erreur coûte une vie. La spec
## demande « du mouvement », pas un bullet hell.
@export var surge_bite: float = 26.0

## De combien le souffle déborde le panache visible. ⚠️ AU-DESSUS DE 1 PARCE QU'UN SOUFFLE
## CHAUFFE PLUS LARGE QU'IL N'ÉCLAIRE — mais pas de beaucoup : une zone nettement plus large que
## ce qu'on voit brûler se lit comme une hitbox injuste, et c'est le grief le plus difficile à
## rattraper une fois qu'un joueur l'a formulé.
@export var danger_spread: float = 1.60

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
	# ⚠️ LE MOTEUR NE SE POSE PAS SUR LE BERCEAU, IL S'Y ENCASTRE. Le contrat de mariage le met
	# à 3,70 m de hauteur dans un berceau qui en fait 4,64 : empiler les deux hauteurs, comme le
	# faisait le LOT 1, surestimait la pile d'un mètre entier — et coûtait de l'échelle pour rien.
	return deck_y + (engine_seat.y + engine_size.y * 0.5) * k

## Le `y` de plan des deux rangées d'ancrages : (basse, haute).
##
## ⚠️ LE Z LOCAL COMPTE VERS LE BAS DE L'ÉCRAN : un socket en +z est plus PRÈS du joueur que le
## centre de son berceau. La rangée ARRIÈRE (+4,480) est donc la BASSE et l'AVANT (−3,950) la
## HAUTE — contre-intuitif tant qu'on lit « avant » comme « en bas de l'écran ».
func anchor_rows() -> Vector2:
	var k := scale_of(false)
	return Vector2(hold_plane_y - socket_z_rear * k, hold_plane_y - socket_z_front * k)

## La demi-largeur de la colonne dangereuse d'un moteur, en unités de plan.
##
## ⚠️ LA COLONNE EST AU-DESSUS DU MOTEUR ET DONC SUR SES PROPRES ANCRAGES — c'est exactement ce
## qui la rend intéressante. Le joueur doit se poster devant un moteur pour travailler ses
## verrous ; la poussée l'en chasse périodiquement. C'est le « crée du mouvement sans bullet
## hell supplémentaire » de la spec §6, obtenu sans une seule balle de plus.
##
## ⚠️ ET LE JOUEUR EST BIEN DANS L'AXE : la tuyère pointe vers le haut de l'écran, il est en
## dessous, sur la même verticale. Le prolongement de l'axe passe par lui.
## ⚠️ ELLE SUIT LA FLAMME, PAS LA NACELLE — et la première version suivait la nacelle. Un
## moteur fait 7,14 m de large, son panache 2,4 : prendre la largeur de la coque laissait
## 1,94 m entre deux colonnes, moins que l'envergure du chasseur. L'invariant 7 l'a refusé
## avant qu'une seule capture ne soit prise. Et c'est aussi la version HONNÊTE : la zone qui
## blesse a exactement la forme de ce que le joueur voit brûler.
func danger_half_width(central: bool) -> float:
	return flame_width * 0.5 * danger_spread * (central_scale if central else 1.0)

## La demi-largeur occupée par les trois groupes, en unités de plan. ⚠️ ELLE PEUT DÉPASSER LA
## ZONE DE VOL : c'est du décor, et le cadre en montre jusqu'à |x| = 20,37. Ce qui doit tenir
## dans le champ du joueur, c'est l'ANCRAGE — voir `anchor_reach()`.
func half_span() -> float:
	return engine_spacing + cradle_size.x * scale_of(false) * 0.5

## Le |x| de l'ancrage le plus au large — la seule cote de la poupe qui doit rester à portée.
func anchor_reach() -> float:
	return absf(slot_x(1.0)) + socket_x * scale_of(false)


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
	# ⚠️ LE BERCEAU, LUI, A LE DROIT DE DÉBORDER — et le LOT 1 le lui interdisait. Ce n'est pas
	# une cible : c'est du décor, et le cadre le montre jusqu'à |x| = 20,37. Contraindre sa
	# largeur a coûté 10 % d'échelle à toute la poupe pour rien.
	# ⚠️ ET LE CENTRAL EST PLUS LARGE : sans cette ligne, il entrerait DANS ses voisins. Deux
	# berceaux qui s'interpénètrent ne produisent aucune erreur — ils produisent une capture où
	# l'on ne sait plus quelle attache appartient à quel moteur, sur la seule cible de la phase.
	var jeu := (engine_spacing - cradle_size.x * scale_of(false) * 0.5) \
		- cradle_size.x * scale_of(true) * 0.5
	if jeu < 0.0:
		errors.append("le berceau central mord celui du bord de %.2f m — les ancrages des deux moteurs se mélangeraient"
			% -jeu)
	# ⚠️ ET C'EST L'ANCRAGE QUI DOIT ÊTRE À PORTÉE, PAS LE BERCEAU. Relevé sur le binaire, le
	# socket est à |x| = 3,700 quand le berceau fait 5,595 de demi-largeur : il déborde de deux
	# mètres au-delà de ses propres verrous.
	var x_ancrage := absf(slot_x(1.0)) + socket_x * scale_of(false)
	if x_ancrage > GameplayPlane.BOUNDS.end.x - 0.4:
		errors.append("l'ancrage extérieur est à |x| = %.2f alors que le joueur ne va qu'à %.2f — sur la SEULE cible de la phase"
			% [x_ancrage, GameplayPlane.BOUNDS.end.x])
	# ⚠️ ET LA BORNE VERTICALE EST LE CADRE, PAS LE PLAN DE VOL — LE LOT 1 SE TROMPAIT. Il
	# refusait tout ancrage au-dessus de `y = 8` « parce que le joueur ne monte pas plus haut ».
	# Le chasseur ne monte pas, mais SES BALLES montent jusqu'à 15,5 : un verrou à 9,9 est
	# parfaitement tirable. Ce qui compte est qu'il soit VU, donc qu'il tienne dans le cadre,
	# dont le bord haut est à +12,28.
	var rangees := anchor_rows()
	if rangees.y > 11.5:
		errors.append("la rangée haute d'ancrages est à y = %.2f, au bord du cadre (+12,28) — un verrou coupé par le haut de l'écran ne se lit plus comme une cible"
			% rangees.y)
	if rangees.x < 1.0:
		errors.append("la rangée basse d'ancrages tombe à y = %.2f, dans les jambes du joueur — il n'aurait pas de recul pour viser"
			% rangees.x)
	# ⚠️ ET LES DEUX VERROUS D'UNE RANGÉE NE DOIVENT PAS SE TOUCHER : alignés et jointifs, ils se
	# lisent comme une seule barre. Vu en capture au LOT 1.
	if socket_x * 2.0 < anchor_size.x * 1.6:
		errors.append("les deux verrous d'une rangée sont à %.2f m l'un de l'autre pour %.2f m de large : ils se liraient comme une seule pièce"
			% [socket_x * 2.0, anchor_size.x])

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
	# ⚠️ LE TREMBLEMENT NE DOIT PAS SORTIR LE MOTEUR DE SON BERCEAU. C'est ce qui distingue « ça
	# cède » de « ça tombe » : au-delà de son propre débattement, la pièce se lit comme déjà
	# partie, et la bascule qui suit n'a plus rien à annoncer.
	if detach_shake_amplitude > cradle_size.y * scale_of(false) * 0.25:
		errors.append("le tremblement fait %.2f m pour un berceau haut de %.2f — le moteur en sortirait avant de s'arracher"
			% [detach_shake_amplitude, cradle_size.y * scale_of(false)])
	# --- INVARIANT 7 : LE JOUEUR PEUT TOUJOURS SORTIR D'UNE POUSSÉE --------
	#
	# ⚠️ TROIS COLONNES QUI SE TOUCHERAIENT NE LAISSERAIENT NULLE PART OÙ ALLER, et la poussée
	# cesserait d'être une menace pour devenir une taxe. Il doit rester un couloir entre deux
	# moteurs voisins, au moins aussi large que le chasseur.
	var couloir := engine_spacing - danger_half_width(false) - danger_half_width(true)
	if couloir < 2.5:
		errors.append("il ne reste que %.2f m entre deux colonnes de poussée — le joueur n'aurait nulle part où s'écarter, et le souffle deviendrait une taxe au lieu d'une menace"
			% couloir)
	if surge_warning < 0.30 or surge_warning > 0.60:
		errors.append("le préavis de poussée vaut %.2f s : la spec en demande 0,30 à 0,50 — en dessous le joueur ne peut pas apprendre ce qu'il ne voit pas venir, au-dessus il a le temps de flâner"
			% surge_warning)
	# ⚠️ LA MORSURE SE MESURE CONTRE LE BOUCLIER DU JOUEUR (100 par défaut, `player_stats.gd`).
	# Au-delà du tiers, une seule inattention coûte trop cher pour une phase qui n'a pas de
	# vagues ; en dessous du dixième, on peut camper dans une voie et le souffle ne chasse plus
	# personne — ce qui était exactement le cas avant qu'on le mesure.
	if surge_bite > 34.0:
		errors.append("le souffle mord %.0f points sur les 100 du bouclier — une inattention coûterait une vie dans une phase sans vagues"
			% surge_bite)
	if surge_bite < 10.0:
		errors.append("le souffle ne mord que %.0f points : le joueur peut camper dans une voie, et la poussée ne chasse plus personne"
			% surge_bite)
	if surge_blast <= 0.0 or surge_period <= surge_warning + surge_blast:
		errors.append("le cycle de poussée ne laisse aucun temps calme : période %.2f pour %.2f de charge et %.2f de souffle"
			% [surge_period, surge_warning, surge_blast])
	if conduit_count < 1:
		errors.append("sans conduite, la seconde qui sépare le dernier verrou du départ est un temps mort : rien ne se rompt")

	# --- INVARIANT 5 : LES ANCRAGES SONT DES CIBLES, PAS DES CONFETTIS ---
	if lateral_anchors < 2:
		errors.append("un moteur latéral à %d ancrage(s) n'a pas de progression : la spec en demande trois"
			% lateral_anchors)
	if central_anchors < lateral_anchors:
		errors.append("le moteur central porte %d ancrages contre %d au latéral — il doit clore la séquence, pas l'alléger"
			% [central_anchors, lateral_anchors])
	# ⚠️ UN SEUIL A ZERO OU A UN SUPPRIME UN ÉTAT ENTIER, SANS RIEN CASSER. À 0, l'ancrage passe
	# d'intact à rompu sans jamais s'ouvrir ; à 1, il naît endommagé et le joueur ne sait plus
	# lesquels il a déjà travaillés. Ni l'un ni l'autre ne produit d'erreur — seulement une
	# phase où l'on ne lit plus sa propre progression.
	if anchor_damaged_at <= 0.05 or anchor_damaged_at >= 0.95:
		errors.append("le seuil d'endommagement vaut %.2f : l'état ENDOMMAGÉ n'existerait plus, et le joueur perdrait la trace des verrous qu'il a déjà travaillés"
			% anchor_damaged_at)
	if anchor_spark_interval <= 0.0:
		errors.append("anchor_spark_interval doit être > 0")
	if anchor_health <= 0.0:
		errors.append("anchor_health doit être > 0")
	if anchor_radius <= 0.0:
		errors.append("anchor_radius doit être > 0")
	# ⚠️ LA ZONE DE TOUCHE VIENT DE LA RESOURCE, JAMAIS DU MAILLAGE (`ADR-0034`) — mais elle ne
	# doit pas pour autant être plus PETITE que ce qu'on dessine. Une hitbox en retrait de la
	# silhouette produit le pire retour possible sur la seule cible de la phase : le joueur voit
	# son tir passer sur la pièce et rien ne se passe. Il conclut qu'elle est invulnérable.
	elif anchor_radius < anchor_size.x * scale_of(false) * 0.5:
		errors.append("la zone de touche fait %.2f m de rayon pour un ancrage large de %.2f — un tir sur ses bords passerait à travers"
			% [anchor_radius, anchor_size.x * scale_of(false)])

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
