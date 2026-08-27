class_name MassRules
## Le poids des choses, et ce qu'il autorise : ÉCRASER ou ÊTRE ARRÊTÉ.
##
## ⚠️ IL AMENDE UNE LOI, ET IL EXISTE À CAUSE D'UN PLAYTEST. « Les corps ne se chevauchent
## pas » (2026-08-27) a rendu les vaisseaux ennemis solides ; jouée, la règle a produit
## l'inverse de ce qu'elle promettait : « pendant les vagues d'ennemis ça devient injouable,
## si on ne les tue pas assez vite ils nous empêchent de bouger » (opérateur, 2026-08-27).
## Un chasseur de combat arrêté net par une escorte de reconnaissance n'est pas crédible —
## c'est la MASSE qui manquait, pas la collision.
##
## La loi devient donc : deux corps ne se chevauchent pas **tant qu'ils jouent dans la même
## catégorie de poids**. En dessous d'un certain rapport, le plus lourd passe à travers le
## plus léger — il le DÉTRUIT et le paie en dégâts. Rien n'est jamais traversé gratuitement.
##
## Tout est statique et pur : aucune scène, aucun autoload, aucun nœud (règle du projet).

## Le poids de ce qui ne bouge pas : murs, réacteur, décor, coques de boss.
##
## ⚠️ CE N'EST PAS UN RÉGLAGE À RECOPIER PARTOUT. Tout ce qui est versé dans un
## [PlaneShapes] est, PAR CONSTRUCTION, de masse infinie : c'est la définition d'un obstacle.
## Une forme n'a donc pas de champ de masse — la masse ne se déclare que là où elle décide
## de quelque chose, c'est-à-dire sur les corps qu'on peut espérer bousculer.
const INFINITE := INF

## Une masse est-elle celle d'un inamovible ?
##
## ⚠️ ZÉRO EN FAIT PARTIE, ET C'EST ASYMÉTRIQUE. Sur une CIBLE, l'absence de masse déclarée
## veut dire « obstacle » — c'est le cas de toute forme versée dans un [PlaneShapes], qui
## n'en porte pas. Sur un ÉCRASEUR, zéro veut dire l'inverse : « il n'y a personne pour
## écraser ». [method crushes] tranche donc les deux côtés séparément ; les confondre
## faisait écraser tout le bestiaire par un chasseur absent.
static func is_immovable(mass: float) -> bool:
	return is_inf(mass) or mass <= 0.0

## `crusher` écrase-t-il `target` ?
##
## ⚠️ UN RAPPORT, PAS UNE DIFFÉRENCE. « Plus lourd que » suffirait à faire passer le chasseur
## à travers tout ce qui le vaut presque, et deux vaisseaux de même classe se traverseraient
## pour un kilo d'écart. Le rapport dit ce qu'on veut vraiment dire : « d'une autre catégorie
## de poids ». En deçà, on s'arrête — et c'est ce qui garde les boss et les porteurs de
## bouclier infranchissables.
static func crushes(crusher_mass: float, target_mass: float, ratio: float) -> bool:
	if is_immovable(target_mass) or ratio <= 0.0:
		return false
	if crusher_mass <= 0.0:
		return false # pas d'écraseur du tout — voir [method is_immovable]
	if is_inf(crusher_mass):
		return true
	return target_mass * ratio <= crusher_mass

## Ce que coûte un écrasement, en points de bouclier.
##
## ⚠️ DÉRIVÉ DE LA MASSE, ET NON DÉCLARÉ À CÔTÉ D'ELLE. Un second champ « dégâts de
## collision » sur chaque fiche finirait par contredire le premier : une unité lourde
## réglée douce, une unité légère réglée mortelle, et plus personne pour dire laquelle
## ment. Une seule fiche d'identité, un seul chiffre — le reste se calcule.
static func crush_damage(target_mass: float, damage_per_mass: float) -> float:
	if is_immovable(target_mass) or damage_per_mass <= 0.0:
		return 0.0
	return target_mass * damage_per_mass
