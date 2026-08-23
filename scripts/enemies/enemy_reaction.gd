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
##   WINDUP   l'engagement. Télégraphe de 300 à 800 ms (spec §11.2), sans retour possible.
##   ACTIVE   la charge : couronne de balles, aspiration, aura.
##   SPENT    vidée. Ou bien elle meurt là, ou bien elle se réarme après un temps mort.
##
## ⚠️ WINDUP NE REVIENT PAS EN ARRIÈRE, même si le joueur s'éloigne. Un télégraphe
## qu'on peut annuler en reculant apprend au joueur à ignorer les télégraphes ; et
## une mine qui se rendort à dix centimètres du contact est une promesse rompue.
## Le contrat est : ce qui s'allume part.

enum State { DORMANT, ALERT, WINDUP, ACTIVE, SPENT }

## Marge de sortie de l'éveil, en fraction du rayon d'alerte. Sans elle, un joueur
## posé pile sur le rayon ferait clignoter la coque à chaque image — une hystérésis
## coûte une constante et supprime la catégorie de bug.
const RELEASE_FACTOR := 1.25


## Ce qui vient après. `time_in_state` est le temps écoulé DANS l'état courant.
static func next_state(state: int, time_in_state: float, distance: float,
		data: EnemyData) -> int:
	match state:
		State.DORMANT:
			return State.ALERT if distance <= data.alert_radius else State.DORMANT
		State.ALERT:
			if distance <= data.trigger_radius:
				return State.WINDUP
			if distance > data.alert_radius * RELEASE_FACTOR:
				return State.DORMANT
			return State.ALERT
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
			return clampf(1.0 - (distance - data.trigger_radius) / span, 0.0, 1.0) * 0.6
		State.WINDUP:
			return 0.6 + 0.4 * windup_ratio(state, time_in_state, data)
		State.ACTIVE:
			return 1.0
		_:
			return 0.0


## L'unité réagit-elle seulement au joueur ? Une unité sans rayon de déclenchement
## est un ennemi classique : elle suit sa courbe et tire, sans jamais rien attendre.
static func is_reactive(data: EnemyData) -> bool:
	return data.trigger_radius > 0.0
