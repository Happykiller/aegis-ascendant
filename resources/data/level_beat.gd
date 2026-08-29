class_name LevelBeat
extends Resource
## Un TEMPS d'un niveau : ce qui se déclenche, ce qui l'annonce, et ce qui le clôt.
##
## ⚠️ ELLE EXISTE PARCE QUE L'ARC D'UN NIVEAU ÉTAIT DU CODE. Les six temps du niveau 1
## s'enchaînaient à la main dans `graybox_root.gd`, chacun appelant le suivant depuis son propre
## événement de fin : `_on_wave_cleared` → `_start_mini_boss` → `_on_mini_boss_defeated` →
## `_start_asteroid_field` → … Un arc écrit ainsi ne se lit nulle part d'un seul tenant, ne se
## réordonne pas, et ne se rejoue pas ailleurs. C'est la dernière couche du chantier d'`ADR-0039`.
##
## ⚠️ CE QUI EST DE LA DONNÉE, ET CE QUI RESTE DU SCRIPT. Sont ici : l'ORDRE, l'identité de
## chaque temps, ce qu'on y annonce, ce que Lyra y dit, quelle vague ou quel boss s'y joue.
## Restent au niveau : les décors sur mesure — le survol de lune, le puits qui monte avant le
## boss final, l'appontage de la Citadelle. Prétendre les mettre en données aurait produit une
## Resource avec trente champs dont vingt-huit valent zéro : une façon compliquée d'écrire du
## code, pas une donnée.

## Ce que le directeur sait faire tout seul.
enum Kind {
	## Une vague : le directeur démarre le semeur nommé et attend qu'il soit nettoyé.
	WAVE,
	## Un boss : le directeur monte sa mise en scène et attend sa défaite.
	BOSS,
	## Le niveau prend la main. Le directeur annonce le temps et attend qu'on lui dise
	## `advance()`. ⚠️ C'est la porte de sortie honnête : un enchaînement sur mesure reste du
	## code, mais il reste À SA PLACE DANS L'ARC.
	SCRIPTED,
}

## Comment le niveau nomme ce temps. ⚠️ C'EST AUSSI LA CLÉ DU BRIEFING DE PAUSE : elle doit
## correspondre à une entrée du `BriefingBook`, sinon l'écran de pause reste muet — sans erreur.
@export var id: StringName = &""
@export var kind: Kind = Kind.SCRIPTED

## ⚠️ SOUS UN VOILE. Un temps qui change le DÉCOR le fait à l'écran éteint : la bascule est
## invisible, et la bannière — qui vit sur le HUD, au-dessus du voile — s'inscrit sur l'écran
## noir avant que le nouveau décor n'apparaisse dessous. Sans voile, on voit le décor commuter.
@export var veiled: bool = false

@export var banner_text: String = ""
@export var banner_colour: Color = Color(1, 1, 1)
@export var banner_hold: float = 1.6
## La réplique dite à l'entrée du temps. Vide = rien.
@export var lyra_key: StringName = &""

@export_group("Vague")
## Le nom du nœud `WaveSpawner` dans la scène du niveau.
@export var spawner_name: StringName = &""

@export_group("Boss")
@export var boss_scene: PackedScene
## Quelle mise en scène : `harvester`, `leviathan`, ou vide pour la générique.
@export var boss_stage: StringName = &""
@export var boss_score: int = 0
## ⚠️ L'ORDRE DU BANDEAU N'EST PAS LE MÊME POUR TOUS LES BOSS, et le perdre coûte une rangée de
## pastilles éteintes sur un boss intact — voir `BossStage.show_boss_before_begin`.
@export var boss_banner_first: bool = false

func validate() -> PackedStringArray:
	var errors := PackedStringArray()
	if id == &"":
		errors.append("id est vide — un temps se désigne par son nom, et c'est aussi la clé de son briefing")
	match kind:
		Kind.WAVE:
			if spawner_name == &"":
				errors.append("temps `%s` de type VAGUE sans `spawner_name` : le directeur ne saurait pas quoi démarrer" % id)
		Kind.BOSS:
			if boss_scene == null:
				errors.append("temps `%s` de type BOSS sans scène : rien à monter" % id)
			if boss_score < 0:
				errors.append("temps `%s` : un boss ne rapporte pas un score négatif" % id)
	if banner_text != "" and banner_hold <= 0.0:
		errors.append("temps `%s` annonce « %s » pendant %.1f s — une bannière qui ne tient pas ne s'est pas affichée"
			% [id, banner_text, banner_hold])
	return errors
