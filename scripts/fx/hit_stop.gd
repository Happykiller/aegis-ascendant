class_name HitStop
extends Node
## Le gel bref de l'impact décisif (`LOI-EXP-03`) : quelques dizaines de millisecondes
## pendant lesquelles TOUT s'arrête, pour « faire atterrir la conséquence ».
##
## ⚠️ TOUT, y compris l'explosion — et c'est le principe, pas un effet de bord. Un hit stop
## TIENT l'image de l'impact ; exempter l'explosion reviendrait à geler le décor autour
## d'une gerbe qui continue, ce qui n'est plus un hit stop mais un ralenti raté. Le son,
## lui, n'est pas concerné : `Engine.time_scale` ne touche pas la lecture audio, si bien
## que le coup s'entend en plein pendant que l'image est suspendue.
##
## La logique de comptage est PURE (`request` / `advance`) : elle se teste en headless,
## sans arbre ni horloge. Le nœud n'est qu'un applicateur.

## Échelle de temps pendant le gel. Pas zéro : un vrai zéro fige aussi les mécanismes qui
## se réveillent au temps, et rend le retour dépendant d'une division qu'on ne veut pas
## avoir à protéger.
const SCALE := 0.04

## Une plaque qui cède. La source du genre donne 60 à 80 ms « sur une frappe décisive » ;
## on reste dans le bas de la fourchette pour un événement qui se répète neuf fois.
const PLATE := 0.06
## Une défaite de boss — deux fois par partie. Haut de la fourchette.
const BOSS := 0.08

## Plafond dur. Un gel qui dépasse cesse d'être une ponctuation et devient une saccade ;
## et c'est la seule valeur qui protège d'un appelant qui passerait une durée absurde.
const MAX_DURATION := 0.15

var _left: float = 0.0

## Demande un gel. Deux demandes qui se chevauchent ne s'ADDITIONNENT pas — on garde la
## plus longue. Additionner ferait qu'une salve sur trois plaques immobiliserait le jeu.
func request(duration: float) -> void:
	if duration <= 0.0:
		return
	_left = maxf(_left, minf(duration, MAX_DURATION))

## Avance le gel de `real_delta` secondes RÉELLES et rend l'échelle de temps à appliquer.
## Rend toujours 1.0 quand il n'y a plus rien à geler : c'est ce qui garantit qu'on ne
## reste pas au ralenti, et c'est le seul mode d'échec qui compte ici.
func advance(real_delta: float) -> float:
	if _left <= 0.0:
		return 1.0
	_left = maxf(0.0, _left - real_delta)
	return SCALE if _left > 0.0 else 1.0

func is_frozen() -> bool:
	return _left > 0.0

## Gèle DÈS CETTE IMAGE. Poser l'échelle depuis `_process` la retarderait d'une image —
## soit exactement l'image de l'impact, la seule qu'on cherchait à tenir.
func freeze(duration: float) -> void:
	var was := _left
	request(duration)
	if _left > was or not is_equal_approx(Engine.time_scale, SCALE):
		Engine.time_scale = SCALE

func _process(delta: float) -> void:
	if _left <= 0.0:
		return
	# ⚠️ `delta` arrive DÉJÀ multiplié par l'échelle de temps : on le redivise pour
	# compter du temps réel. Sans cette division, un gel de 60 ms à l'échelle 0,04
	# durerait une seconde et demie.
	Engine.time_scale = advance(delta / maxf(Engine.time_scale, 0.0001))

## Un changement de scène pendant un gel laisserait le jeu au ralenti, sans la moindre
## erreur — le mode d'échec le plus coûteux de ce fichier.
func _exit_tree() -> void:
	if _left > 0.0:
		_left = 0.0
		Engine.time_scale = 1.0
