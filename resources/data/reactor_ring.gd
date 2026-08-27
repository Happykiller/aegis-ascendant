class_name ReactorRing
extends Resource
## Un anneau de blindage du réacteur (Reactor Chamber, plan du 2026-08-27).
##
## Il tourne autour du noyau et porte des OUVERTURES régulièrement réparties. Le flux n'est
## atteignable que lorsqu'une ouverture de CHAQUE anneau couvre l'azimut du joueur : c'est
## ce qui transforme une cible fixe en puzzle de positionnement.
##
## ⚠️ LE JOUEUR N'ATTEND JAMAIS. Avec les réglages livrés, un corridor existe **en
## permanence** quelque part sur le cercle — simulé sur deux minutes, verrou le plus long
## 0,00 s. La difficulté est d'y ALLER, pas d'attendre qu'il s'ouvre. Une phase où l'on
## patiente devant un blindage fermé serait le défaut qu'on cherchait à corriger, en pire.

## Nombre d'ouvertures, réparties régulièrement sur le tour.
@export_range(1, 8) var apertures: int = 3
## Largeur angulaire d'une ouverture, en degrés.
@export_range(5.0, 180.0) var aperture_deg: float = 46.0
## Vitesse de rotation, en degrés par seconde. Le SIGNE compte : deux anneaux qui tournent
## dans le même sens gardent leur alignement bien plus longtemps qu'en sens contraires.
@export var speed_deg: float = 26.0
## Décalage initial, en degrés.
@export var phase_deg: float = 0.0

## Rayon de l'anneau, en unités du plan, et épaisseur de son mur.
##
## ⚠️ ILS VIVENT ICI, avec les ouvertures, et pas dans le décor. La collision et l'image
## doivent lire LA MÊME donnée : deux sources auraient fini par diverger, et le joueur se
## serait cogné à un mur qu'il ne voit pas — ou traversé celui qu'il voit.
@export var radius: float = 4.0
@export var thickness: float = 1.0

func validate() -> PackedStringArray:
	var errors := PackedStringArray()
	if apertures < 1:
		errors.append("apertures must be >= 1")
	if aperture_deg <= 0.0:
		errors.append("aperture_deg must be > 0")
	var step := 360.0 / float(maxi(apertures, 1))
	if aperture_deg >= step:
		errors.append("aperture_deg (%.1f) >= l'écart entre deux ouvertures (%.1f) : l'anneau n'est plus un blindage"
			% [aperture_deg, step])
	if radius <= 0.0:
		errors.append("radius must be > 0")
	if thickness <= 0.0 or thickness >= radius * 2.0:
		errors.append("thickness (%.1f) incoherente avec le rayon (%.1f)" % [thickness, radius])
	if is_zero_approx(speed_deg):
		errors.append("speed_deg must not be 0 — un anneau immobile est un mur, pas un puzzle")
	return errors
