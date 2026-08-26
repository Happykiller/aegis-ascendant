class_name EnemyReaction
## Machine à états de la menace de proximité — fonction PURE de (état, temps, distance).
##
## C'est la brique qui rend possible un ennemi qui *attend*. Toutes les unités du
## jeu jusqu'ici traversaient le champ selon une courbe indifférente au joueur
## (`EnemyPath`) ; une mine, elle, ne fait rien du tout tant qu'on ne s'approche
## pas — c'est le joueur qui avance, et c'est lui qui décide du moment.
##
## Aucun nœud, aucun état interne : le contrôleur détient l'état courant et le
## temps passé dedans, cette bibliothèque dit seulement ce qui vient après. D'où
## un comportement de proximité entièrement testable en headless, sans arbre de
## scène ni joueur (tests/unit/test_enemy_reaction.gd).
##
##   DORMANT  coque éteinte, inerte. On peut la tuer de loin : la prudence paie.
##   ALERT    elle a senti quelque chose. Son noyau s'allume — l'avertissement est GRATUIT.
##   ARMING   elle a mordu, mais s'accorde un SURSIS : sortir avant l'échéance la referme.
##   WINDUP   l'engagement. Télégraphe de 300 à 800 ms (spec §11.2), sans retour possible.
##   ACTIVE   la charge : couronne de balles, aspiration, aura.
##   SPENT    vidée. Ou bien elle meurt là, ou bien elle se réarme après un temps mort.
##
## ⚠️ WINDUP NE REVIENT PAS EN ARRIÈRE, même si le joueur s'éloigne. Un télégraphe
## qu'on peut annuler en reculant apprend au joueur à ignorer les télégraphes ; et
## une mine qui se rendort à dix centimètres du contact est une promesse rompue.
## Le contrat est : ce qui s'allume part.
##
## ⚠️ ET C'EST PRÉCISÉMENT POURQUOI `ARMING` EXISTE (2026-08-26). Demande de l'opérateur :
## « si on rentre dans cette zone les mines réagissent, mais si on ressort en moins d'1 s
## elle se referme ». Rendre le télégraphe annulable aurait cassé le contrat ci-dessus ; on
## insère donc une étape AVANT lui. La mine réagit — son noyau monte en régime — mais **sa
## coque ne s'ouvre pas** : l'ouverture mécanique reste le signe de l'engagement, et
## l'engagement reste sans retour.
##
## Une unité sans `arm_grace` (toutes sauf la mine) passe directement d'ALERT à WINDUP : le
## comportement d'avant, bit pour bit.

enum State { DORMANT, ALERT, ARMING, WINDUP, ACTIVE, SPENT }

## Marge de sortie de l'éveil, en fraction du rayon d'alerte. Sans elle, un joueur
## posé pile sur le rayon ferait clignoter la coque à chaque image — une hystérésis
## coûte une constante et supprime la catégorie de bug.
const RELEASE_FACTOR := 1.25

## Plafond du régime en simple éveil. Au-delà, l'unité est ENGAGÉE — et ce seuil
## est exposé parce que la coque s'en sert : c'est là qu'elle cesse de monter en
## intensité pour changer de couleur (`EnemyVitals`).
const ALERT_CEILING := 0.6

## Battements par seconde du sursis, au début et à la fin. Il ACCÉLÈRE : c'est ce qui le
## fait lire comme un compte à rebours et non comme une lueur qui monte.
const ARMING_BEATS_MIN := 2.0
const ARMING_BEATS_MAX := 7.0


## Ce qui vient après. `time_in_state` est le temps écoulé DANS l'état courant.
static func next_state(state: int, time_in_state: float, distance: float,
		data: EnemyData) -> int:
	match state:
		State.DORMANT:
			return State.ALERT if distance <= data.alert_radius else State.DORMANT
		State.ALERT:
			if distance <= data.trigger_radius:
				return State.ARMING if data.arm_grace > 0.0 else State.WINDUP
			if distance > data.alert_radius * RELEASE_FACTOR:
				return State.DORMANT
			return State.ALERT
		State.ARMING:
			# ⚠️ LE SURSIS EST TESTÉ EN PREMIER, ET C'EST UN CHOIX. À l'échéance exacte, si
			# le joueur est sorti dans la même image, il s'en tire. L'inverse ferait gagner
			# la mine sur une égalité que le joueur ne peut ni voir ni mesurer — et une
			# règle de faveur qui se joue à l'image près se lit comme de l'injustice.
			if distance > data.trigger_radius:
				return State.ALERT
			if time_in_state >= data.arm_grace:
				return State.WINDUP
			return State.ARMING
		State.WINDUP:
			return State.ACTIVE if time_in_state >= data.windup_time else State.WINDUP
		State.ACTIVE:
			return State.SPENT if time_in_state >= data.active_time else State.ACTIVE
		State.SPENT:
			# Un temps mort nul veut dire « à usage unique » : la mine reste vidée.
			if data.rearm_time > 0.0 and time_in_state >= data.rearm_time:
				return State.DORMANT
			return State.SPENT
		_:
			return State.DORMANT


## Avancement du télégraphe, de 0 à 1. C'est ce que lit l'animation : la coque
## s'ouvre, le noyau monte en régime, et le joueur peut compter les millisecondes.
static func windup_ratio(state: int, time_in_state: float, data: EnemyData) -> float:
	if state != State.WINDUP or data.windup_time <= 0.0:
		return 1.0 if state == State.ACTIVE else 0.0
	return clampf(time_in_state / data.windup_time, 0.0, 1.0)


## Combien l'unité est « réveillée », de 0 à 1 — ce que les signes vitaux montrent.
##
## Le régime monte en trois marches et non continûment : dormante à 0, éveillée à
## la fraction d'approche entre les deux rayons, à fond dès l'engagement. Une rampe
## continue depuis l'infini ferait respirer tout le champ de mines en même temps et
## ne dirait plus laquelle a mordu.
static func threat_ratio(state: int, time_in_state: float, distance: float,
		data: EnemyData) -> float:
	match state:
		State.ALERT:
			var span := maxf(data.alert_radius - data.trigger_radius, 0.001)
			return clampf(1.0 - (distance - data.trigger_radius) / span, 0.0, 1.0) * ALERT_CEILING
		State.ARMING:
			# ⚠️ UN BATTEMENT QUI ACCÉLÈRE, ET NON UNE SIMPLE MONTÉE. Première version : une
			# rampe de 0,6 à 0,9. Verdict de l'opérateur en jouant — « l'activation des mines
			# pendant la phase suspense est trop subtile ». Il avait raison : une valeur qui
			# monte lentement, sur une coque qui reste fermée, ne se voit pas.
			#
			# Le sursis est un COMPTE À REBOURS, et un compte à rebours se lit à sa cadence.
			# `EnemyVitals` accélère déjà son halètement avec le régime ; on lui donne en
			# plus une oscillation propre dont la fréquence monte, et dont l'amplitude croît
			# jusqu'au plein régime. Le joueur voit sa dernière seconde s'épuiser.
			#
			# ⚠️ Et il n'y a PAS de confusion possible avec l'engagement : c'est la COQUE qui
			# le signale, et elle reste fermée pendant tout le sursis (`open_ratio`).
			var grace := maxf(data.arm_grace, 0.001)
			var progress := clampf(time_in_state / grace, 0.0, 1.0)
			var beats := lerpf(ARMING_BEATS_MIN, ARMING_BEATS_MAX, progress)
			var throb := 0.35 + 0.65 * (0.5 + 0.5 * sin(time_in_state * beats * TAU))
			return ALERT_CEILING + (1.0 - ALERT_CEILING) * progress * throb
		State.WINDUP:
			return ALERT_CEILING + (1.0 - ALERT_CEILING) * windup_ratio(state, time_in_state, data)
		State.ACTIVE:
			return 1.0
		_:
			return 0.0


## Ouverture mécanique de la coque, de 0 (fermée) à 1 (grande ouverte).
##
## Elle suit le télégraphe et non la menace : une mine qui bâillerait dès qu'on
## l'approche aurait déjà tout dit, et le joueur n'aurait plus rien à lire dans les
## 700 ms qui décident. Elle s'ouvre pendant le WINDUP, exactement.
##
## Ce qu'elle fait après la charge distingue les deux règles du jeu : une unité à
## usage unique reste ouverte — elle est finie, sa carcasse le montre. Une unité qui
## se réarme se REFERME pendant son temps mort, et c'est ce qui rend visible, de
## loin, le moment où elle redevient dangereuse.
static func open_ratio(state: int, time_in_state: float, data: EnemyData) -> float:
	match state:
		State.WINDUP:
			return windup_ratio(state, time_in_state, data)
		State.ACTIVE:
			return 1.0
		State.SPENT:
			return 1.0 if data.rearm_time <= 0.0 else 0.0
		_:
			return 0.0


## L'unité réagit-elle seulement au joueur ? Une unité sans rayon de déclenchement
## est un ennemi classique : elle suit sa courbe et tire, sans jamais rien attendre.
static func is_reactive(data: EnemyData) -> bool:
	return data.trigger_radius > 0.0
