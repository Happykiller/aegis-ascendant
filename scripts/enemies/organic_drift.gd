class_name OrganicDrift
## La dérive qui empêche l'œil de repérer la boucle.
##
## Toutes les trajectoires du jeu — unités et boss — sont des fonctions PURES de l'âge.
## C'est ce qui rend le pooling sûr et les tests possibles (`ADR-0022`), et ce n'est pas
## négociable. Mais la pureté a un prix que le playtest du 2026-08-27 a nommé sans détour :
##
##   « tout est figé, fête foraine »
##
## Deux unités du même type nées au même endroit décrivaient **exactement** la même courbe,
## en même temps ; et chaque courbe, prise seule, se répétait à l'identique.
##
## ⚠️ LE REMÈDE EXISTAIT DÉJÀ DANS CE DÉPÔT, appliqué à la caméra de l'écran d'accueil, avec
## ce commentaire : des périodes « volontairement non harmoniques (11,0 / 7,3 / 17,0 s) : la
## scène ne doit jamais se retrouver deux fois dans la même pose, sinon **l'œil repère la
## boucle** et l'accueil redevient un décor » (`title_stage.gd`). Il n'avait jamais été
## transposé au bestiaire.
##
## Ce module rend un DÉCALAGE à ajouter à une position, jamais une position. Il reste donc
## une fonction pure de `(âge, graine, amplitude)` :
##   - rien ne s'accumule → la forme ne dépend pas du pas de temps ;
##   - une graine fixe rend un chemin déterministe → testable en headless ;
##   - une instance réactivée reçoit une graine neuve → le pooling reste sûr.

## Périodes NON HARMONIQUES, en secondes. Leur rapport (1,62) fait que la somme ne se
## répète pas avant plus de deux minutes — très au-delà de la vie d'une unité.
## ⚠️ Ne jamais les choisir dans un rapport simple (×2, ×3, ÷2) : la somme redeviendrait
## périodique, et l'œil retrouverait la boucle qu'on vient de casser.
const PERIOD_A := 2.9
const PERIOD_B := 4.7

## Part de l'amplitude portée par la seconde période. La première domine : la dérive doit
## rester une respiration, pas une seconde trajectoire.
const SECOND_SHARE := 0.35

## La dérive verticale est une fraction de l'horizontale. Plus haut, une unité semblerait
## hésiter à descendre — et sa vitesse d'approche est une information de jeu.
const VERTICAL_RATIO := 0.30

## Montée en puissance de la dérive, en secondes.
##
## ⚠️ ELLE EXISTE POUR UNE RAISON DURE, PAS POUR L'ESTHÉTIQUE : à l'âge zéro, le décalage
## doit valoir EXACTEMENT zéro. Une unité doit apparaître à son point de spawn — c'est le
## contrat que `test_enemy_path.gd` garde depuis toujours, et c'est lui qui rend le pooling
## observable. Une dérive qui commencerait à pleine amplitude téléporterait chaque
## réapparition d'un demi-mètre.
const RAMP := 0.6

## Décalage à ajouter à une position, pour une unité de graine `seed` et d'âge `age`.
## `amplitude` en unités du plan ; zéro ou moins rend un décalage nul.
static func offset(age: float, seed: float, amplitude: float) -> Vector2:
	if amplitude <= 0.0 or age <= 0.0:
		return Vector2.ZERO
	var ramp := minf(age / RAMP, 1.0)
	var phase_a := seed * TAU
	# Décalée par le nombre d'or : deux graines voisines ne donnent jamais deux dérives
	# voisines, ni sur une période ni sur l'autre.
	var phase_b := seed * TAU * 1.618034 + 1.1
	var wave_a := sin(age * TAU / PERIOD_A + phase_a)
	var wave_b := sin(age * TAU / PERIOD_B + phase_b)
	var reach := amplitude * ramp
	return Vector2(
		reach * (wave_a * (1.0 - SECOND_SHARE) + wave_b * SECOND_SHARE),
		reach * VERTICAL_RATIO * wave_b)

## Graine d'une unité à partir de son rang d'apparition.
##
## Suite à faible discordance (le nombre d'or, modulo 1) : deux ennemis SUCCESSIFS d'une
## même nuée reçoivent les phases les plus éloignées possible. C'est précisément le cas qui
## se voyait — quatre coques nées à 0,7 s d'intervalle et ondulant à l'unisson.
##
## ⚠️ DÉTERMINISTE, ET C'EST UNE DÉCISION. Une graine tirée au hasard rendrait chaque partie
## différente, donc INAPPRENABLE — or la mémorisation est un pilier du genre. On veut varier
## les unités ENTRE ELLES, pas la vague d'une partie à l'autre.
static func seed_for(index: int) -> float:
	return fmod(float(index) * 0.618034, 1.0)
