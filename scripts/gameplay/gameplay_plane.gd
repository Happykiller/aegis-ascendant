class_name GameplayPlane
## Logical 2D gameplay plane (spec §16.2). Pure static helpers, testable headless.
## Convention: logical plane = world XZ plane at Y = 0.
##   logical +x -> world +X (screen right)
##   logical +y -> world -Z (screen up)
## Logical positions are authoritative for all gameplay collisions; the 3D
## scene is only a projection of them.

## Le plan de vol ordinaire, en unités monde. Avec le champ de vision de 62 degrés de la
## caméra de jeu, il remplit 85 à 90 % du plan visible tout en gardant une marge d'entrée
## pour les ennemis et les projectiles.
const BOUNDS := Rect2(Vector2(-14.0, -8.0), Vector2(28.0, 16.0))

## Le plan de vol DANS LA CHAMBRE DU RÉACTEUR, et il est plus grand.
##
## ⚠️ IL EXISTE PARCE QUE LA CHAMBRE N'EST PAS L'ARÈNE OUVERTE. Le blindage du boss final
## occupe 16,6 unités de diamètre : dans un plan de 16 de haut, le chasseur n'a la place ni
## de tenir entre les deux murs, ni de se poster sous eux. Mesuré, sans joueur : posé
## immobile dans le couloir, il était transporté de 6,6 unités vers la droite et éjecté au
## plafond en neuf secondes — « c'est comme si tout le cercle était un mur pour moi »
## (playtest du 2026-08-27). Un lieu où l'on ne peut pas exister n'est pas un terrain.
##
## Trois contraintes le dimensionnent, et c'est la plus basse qui commande :
##
## - se **poster sous le mur** pour tirer : −10,21 ;
## - **contourner le blindage par le haut** sans être coincé entre lui et le plafond : +12,01
##   (sans quoi un mur qui tourne pousse le chasseur contre une limite invisible, et il
##   vibre entre les deux) ;
## - **naître à l'entrée de plongée** avec son corps entier : **−12,02** — celle-ci décide,
##   parce que l'entrée se déduit du rayon du mur et descend donc avec lui.
##
## Marge de manœuvre : 0,4 au-delà du demi-corps (2,11). Plus généreux coûterait du recul de
## caméra pour rien — le plan passe déjà de 16 à 24 de haut, soit un recul de moitié.
const CHAMBER_BOUNDS := Rect2(Vector2(-14.0, -12.0), Vector2(28.0, 24.0))

## L'enveloppe de TOUTES les phases.
##
## ⚠️ CE QUE LES STRUCTURES DE TAILLE FIXE DOIVENT COUVRIR, et rien d'autre ne doit s'en
## servir. La grille spatiale de [BulletManager] est allouée une seule fois au montage : la
## dimensionner sur les bornes COURANTES la laisserait trop petite dès l'entrée dans la
## chambre, et des balles tomberaient dans des cellules voisines sans qu'aucune erreur ne le
## dise. Elle couvre donc le pire cas une fois pour toutes.
const MAX_BOUNDS := Rect2(Vector2(-14.0, -12.0), Vector2(28.0, 24.0))

## Les bornes en vigueur À CET INSTANT.
##
## ⚠️ C'EST LE SEUL ÉTAT GLOBAL DE CE MODULE, ET IL EST ASSUMÉ. L'alternative — passer les
## bornes en paramètre — traverserait le joueur, les ennemis, les bonus, les projectiles et
## les boss pour une valeur qui ne change qu'à deux instants de la partie. Le contrat est
## donc strict : **qui les change les restaure**, et le niveau le fait sur TOUS les chemins
## de sortie de plongée, y compris la mort et l'abandon de partie.
static var bounds: Rect2 = BOUNDS

## Passe au plan de vol `next`. Rendre l'ancien permet à l'appelant de le reposer sans
## supposer lequel c'était.
static func use_bounds(next: Rect2) -> Rect2:
	var previous := bounds
	bounds = next
	return previous

## Revient au plan de vol ordinaire. À appeler sur tout chemin qui quitte un lieu, y compris
## ceux qu'on n'a pas prévus : une borne oubliée laisserait le joueur voler hors du cadre
## dans la phase suivante, et rien ne le signalerait.
static func reset_bounds() -> void:
	bounds = BOUNDS

## Input vectors come in Godot's screen convention (+y = down); the logical
## plane is up-positive, so the vertical axis must be flipped on the way in.
static func from_input(input_vector: Vector2) -> Vector2:
	return Vector2(input_vector.x, -input_vector.y)

static func to_world(plane_position: Vector2) -> Vector3:
	return Vector3(plane_position.x, 0.0, -plane_position.y)

static func to_plane(world_position: Vector3) -> Vector2:
	return Vector2(world_position.x, -world_position.z)

## Où une chose posée HORS du plan de jeu doit être touchée, vue de cette caméra.
##
## ⚠️ ELLE EXISTE PARCE QUE LA HITBOX N'ÉTAIT PAS SOUS LA PIÈCE, ET QUE PERSONNE NE POUVAIT LE
## DEVINER SANS LES CALQUES DE DEBUG. Tout le jeu se joue à Y = 0 : `to_plane()` laisse tomber
## la hauteur, ce qui est juste pour un chasseur ou un éclaireur, qui y sont. Les pièces du
## niveau 2 n'y sont PAS — elles sont vissées sur une coque à Y = −3,5. Or la caméra plonge à
## 70° : deux points de même X et Z mais de hauteurs différentes ne se projettent pas au même
## endroit à l'écran. La tourelle apparaissait donc à plusieurs mètres de sa propre hitbox, et
## le joueur tirait à côté en visant juste — signalé par l'opérateur, capture à l'appui.
##
## ⚠️ ET LE DÉCALAGE EST GROS : avec la caméra du jeu, une pièce à X = 10 doit être tirée vers
## X = 8. Ce n'est pas un défaut d'un pixel qu'on tolère, c'est deux mètres.
##
## Ce que la fonction rend est le point du plan qui se projette AU MÊME PIXEL que la pièce : le
## rayon caméra → pièce, prolongé jusqu'à Y = 0. Toucher là, c'est toucher ce qu'on voit.
static func aim_point_of(world_position: Vector3, camera_origin: Vector3) -> Vector2:
	var rise := world_position.y - camera_origin.y
	# ⚠️ DEUX CAS DÉGÉNÉRÉS, ET LE SECOND N'EST PAS CELUI QU'ON CROIT. Si la pièce est à la
	# hauteur de la caméra, aucun rayon ne traverse le plan — division par zéro. Mais si la
	# CAMÉRA est dans le plan, le calcul « marche » et rend la position de la caméra : une
	# hitbox téléportée au centre de l'écran, sans erreur. Un banc de test qui poserait sa
	# caméra à Y = 0 verrait donc toutes les cibles au même endroit et n'y comprendrait rien.
	if absf(rise) < 0.0001 or absf(camera_origin.y) < 0.0001:
		return to_plane(world_position)
	var t := -camera_origin.y / rise
	var crossing := camera_origin + (world_position - camera_origin) * t
	return Vector2(crossing.x, -crossing.z)

static func clamp_to_bounds(plane_position: Vector2) -> Vector2:
	return plane_position.clamp(bounds.position, bounds.end)

static func is_inside(plane_position: Vector2, margin: float = 0.0) -> bool:
	return bounds.grow(margin).has_point(plane_position)
