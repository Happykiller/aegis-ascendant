class_name PlumeTuning
extends Resource
## Réglages d'une plume d'échappement (ADR-0017) — aucune valeur en dur dans le code
## de rendu (règle §31). Une instance par camp : la plume dit à quelle faction
## appartient la coque avant même qu'on distingue sa silhouette.
##
## CE QUE CETTE RESOURCE DÉCRIT, ce n'est pas « une flamme » mais **l'écart entre deux
## régimes** : la dérive et le plein régime. Tout ce que le joueur lit du mouvement de
## son vaisseau tient dans cet écart — une `length_idle` proche de `length_full` rend
## la plume muette, quelle que soit la beauté du shader.

@export_group("Geometrie")
## Longueurs du jet (unités monde) à la dérive et à plein régime. Le rapport EST la
## lisibilité de l'accélération : ×2,5 est le réglage arcade acté avec l'opérateur.
@export var length_idle: float = 0.55
@export var length_full: float = 1.4
## Rayon au col, à plein régime. Au ralenti la section se referme (voir `throat_idle`).
@export var throat_radius: float = 0.085
## Fraction du col conservée à la dérive. Une tuyère qui garde sa pleine section au
## ralenti raconte un moteur bloqué plein gaz.
@export var throat_idle: float = 0.72
## Rayon en queue, rapporté au col.
@export var tail_flare: float = 2.3

@export_group("Disques de Mach")
## ⚠️ Plafond de LISIBILITÉ à 3 : le post rétro rend à 960×540 et écrase le détail fin.
@export var shock_count: float = 3.0
## Amplitude à plein régime.
@export var shock_depth: float = 0.34
## Poussée en deçà de laquelle AUCUN disque n'apparaît. C'est le signal d'accélération
## le plus fort de tout l'effet : les disques ne sont pas un ornement permanent, ils
## sont la preuve que le moteur est ouvert.
@export var shock_threshold: float = 0.55

@export_group("Couleurs et energie")
## Cœur à plein régime (blanc-bleu) — le col d'une tuyère chaude est presque blanc.
@export var core_color: Color = Color(0.85, 0.98, 1.0)
## Corps du jet, la couleur de camp (charte §3 : cyan Helios, magenta Null Choir).
@export var plume_color: Color = Color(0.247, 0.851, 0.91)
## Queue, là où le gaz se refroidit et se dilue.
@export var tail_color: Color = Color(0.11, 0.17, 0.37)
@export var energy: float = 3.2
## Part de l'énergie conservée à la dérive.
@export var energy_idle: float = 0.5
@export var flicker: float = 0.06

@export_group("Maillage")
## Subdivision AXIALE : c'est elle qui permet aux disques de bomber la silhouette. En
## dessous de ~6 segments par cellule de choc les bombements deviennent des facettes.
## C'est aussi LE levier de coût GPU quand une vague entière pousse à l'écran.
@export var rings: int = 22
@export var radial_segments: int = 12

@export_group("Commande")
## Poussée au repos, manche relâché. JAMAIS 0 : un chasseur en vol plané dans un
## shooter vertical avance toujours — un moteur éteint lirait comme une panne.
@export var idle_throttle: float = 0.32
## Gain de la commande « vers le haut de l'écran » — l'accélération franche.
@export var forward_gain: float = 0.62
## Gain de la commande latérale. Plus faible : une embardée n'est pas une accélération.
@export var lateral_gain: float = 0.18
## Gain de la vitesse acquise. Il maintient la plume ouverte tant que le vaisseau file,
## même manche relâché — sinon elle s'effondre à l'instant précis où on lâche.
@export var speed_gain: float = 0.28
## Effondrement quand le pilote retient (commande vers le bas de l'écran).
@export var brake_drop: float = 0.30

@export_group("Reponse")
## Montée en régime, par seconde. Vif : le joueur doit voir sa commande.
@export var attack_rate: float = 10.0
## Extinction, par seconde. LENTE, et c'est le point : une tuyère ne se coupe pas net.
## C'est cette asymétrie qui fait exister le « ralentissement » à l'écran — même
## logique que `ShipFlight.NOZZLE_RESPONSE`, qui ouvre les pétales de la même coque.
@export var decay_rate: float = 3.5

func validate() -> PackedStringArray:
	var errors := PackedStringArray()
	if length_idle <= 0.0 or length_full <= 0.0:
		errors.append("plume lengths must be > 0")
	elif length_full <= length_idle:
		# Sans écart, la plume ne raconte plus rien du mouvement : c'est le seul
		# défaut de cette Resource qui rend l'effet entier inutile.
		errors.append("length_full must exceed length_idle (got %.2f <= %.2f)"
			% [length_full, length_idle])
	if throat_radius <= 0.0:
		errors.append("throat_radius must be > 0")
	if throat_idle <= 0.0 or throat_idle > 1.0:
		errors.append("throat_idle must be in (0, 1]")
	if tail_flare <= 0.0:
		errors.append("tail_flare must be > 0")
	if shock_count < 0.0 or shock_count > 3.0:
		errors.append("shock_count must be in [0, 3] — 960x540 retro post caps readability at 3")
	if shock_depth < 0.0 or shock_depth >= 1.0:
		errors.append("shock_depth must be in [0, 1)")
	if shock_threshold < 0.0 or shock_threshold >= 1.0:
		errors.append("shock_threshold must be in [0, 1)")
	if energy <= 0.0:
		errors.append("energy must be > 0")
	if energy_idle < 0.0 or energy_idle > 1.0:
		errors.append("energy_idle must be in [0, 1]")
	if flicker < 0.0 or flicker > 0.25:
		errors.append("flicker must be in [0, 0.25] — beyond that it reads as a rendering fault")
	if rings < 4:
		errors.append("rings must be >= 4")
	if radial_segments < 3:
		errors.append("radial_segments must be >= 3")
	if idle_throttle <= 0.0 or idle_throttle >= 1.0:
		errors.append("idle_throttle must be in (0, 1) — a dead engine reads as a breakdown")
	if forward_gain < 0.0 or lateral_gain < 0.0 or speed_gain < 0.0 or brake_drop < 0.0:
		errors.append("command gains must be >= 0")
	if attack_rate <= 0.0 or decay_rate <= 0.0:
		errors.append("response rates must be > 0")
	elif decay_rate >= attack_rate:
		# L'asymétrie n'est pas un détail de goût : symétrique, la plume claque à
		# chaque relâchement de touche et l'effet perd son inertie de machine.
		errors.append("decay_rate must stay below attack_rate (a nozzle does not snap shut)")
	return errors
