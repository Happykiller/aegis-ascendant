extends "res://tests/test_case.gd"
## `BulletManager` — la reentrance du garde-fou anti-mort-en-chaine.
##
## ⚠️ CE FICHIER EXISTE PARCE QUE LE DEFAUT S'EST PRODUIT EN JEU, une fois, dans un run de
## demo du 2026-08-26 :
##
##   SCRIPT ERROR: Out of bounds set index '600' (on base: 'PackedInt32Array')
##      at: _release (res://scripts/projectiles/bullet_manager.gd:188)
##
## LA CHAINE, et elle est entierement synchrone :
##   1. `_resolve_hits` trouve qu'un tir ennemi atteint le joueur ;
##   2. `target.hit_callback.call(...)` — le joueur encaisse et MEURT ;
##   3. la mort declenche `graybox_root._on_player_destroyed`, qui appelle
##      `clear_team(ENEMY)` — le garde-fou contre la mort en chaine, voulu et documente ;
##   4. `clear_team` libere TOUS les tirs ennemis vivants, dont celui qu'on est en train de
##      traiter : son `_alive` valait encore 1 ;
##   5. retour dans `_resolve_hits`, qui appelle `_release(i)` sur un index DEJA libere.
##
## Le meme index se retrouve deux fois sur la pile libre. `_free_top` depasse alors le
## nombre de projectiles et l'ecriture sort du tableau. Le compte par equipe est decremente
## deux fois lui aussi — donc il derive vers le NEGATIF, et le budget d'equipe cesse de
## borner quoi que ce soit, en silence et bien apres l'erreur visible.
##
## Rien de tout cela ne demande le jeu : le garde-fou est declenche depuis le rappel de
## degats, exactement comme le niveau le fait.

const ManagerScript := preload("res://scripts/projectiles/bullet_manager.gd")

var _manager: BulletManager

func _make() -> BulletManager:
	var manager := track(ManagerScript.new()) as BulletManager
	# `_ready` ne tourne pas hors de l'arbre : on initialise a la main, comme MoonFlyby.
	manager._ready()
	return manager

## La cible qui se vide l'ecran en encaissant — le joueur qui meurt, en une ligne.
func _suicidal_target(manager: BulletManager) -> BulletTarget:
	var target := BulletTarget.make(BulletManager.Team.PLAYER, 0.6,
		func(_damage: float) -> void:
			manager.clear_team(BulletManager.Team.ENEMY))
	target.position = Vector2.ZERO
	return target

func test_a_hit_callback_that_clears_the_screen_does_not_corrupt_the_pool() -> void:
	var manager := _make()
	var target := _suicidal_target(manager)
	manager.register_target(target)
	# Plusieurs tirs sur la cible : le premier tue, les autres sont balayes par le
	# garde-fou pendant qu'on traite le premier.
	for i in 5:
		manager.spawn_bullet(BulletManager.Team.ENEMY, Vector2(0.0, 0.05 * float(i)),
			Vector2.ZERO, 0.2, 1.0, 5.0)
	assert_eq(manager.active_count(), 5, "cinq tirs en vol avant la passe")
	manager.step(0.016)
	assert_eq(manager.active_count(), 0, "l'ecran est vide apres le garde-fou")
	assert_true(manager.active_count() >= 0,
		"et le compte n'est jamais negatif — un index libere deux fois le ferait deriver")

## La preuve directe : la pile libre ne doit jamais contenir plus d'entrees qu'il n'y a de
## projectiles. C'est CETTE borne que l'erreur en jeu a franchie.
func test_the_free_stack_never_overflows() -> void:
	var manager := _make()
	var target := _suicidal_target(manager)
	manager.register_target(target)
	for i in 5:
		manager.spawn_bullet(BulletManager.Team.ENEMY, Vector2(0.0, 0.05 * float(i)),
			Vector2.ZERO, 0.2, 1.0, 5.0)
	manager.step(0.016)
	assert_true(manager._free_top <= BulletManager.MAX_BULLETS,
		"la pile libre tient dans son tableau (%d / %d)"
			% [manager._free_top, BulletManager.MAX_BULLETS])
	# ⚠️ LA BORNE SEULE NE SUFFIT PAS, et c'est le piege que ce fichier a failli poser :
	# l'ecriture hors bornes INTERROMPT `_release` avant `_free_top += 1`, si bien que le
	# compteur reste juste et qu'un test qui ne regarde que lui PASSE sur du code casse.
	# Ce qu'il faut verifier, c'est qu'aucun index ne figure DEUX FOIS sur la pile.
	assert_eq(manager.active_count(), 0, "tout est libere : la pile est pleine")
	var seen := {}
	for k in manager._free_top:
		var index: int = manager._free_stack[k]
		assert_false(seen.has(index),
			"l'index %d n'est sur la pile libre qu'une fois" % index)
		seen[index] = true

## Le degat silencieux, et le plus durable : deux decrementations pour une allocation font
## deriver le compte d'equipe vers le negatif. Le budget d'equipe cesse alors de borner
## quoi que ce soit — longtemps apres que l'erreur visible a defile.
func test_the_team_count_stays_truthful() -> void:
	var manager := _make()
	var target := _suicidal_target(manager)
	manager.register_target(target)
	for i in 5:
		manager.spawn_bullet(BulletManager.Team.ENEMY, Vector2(0.0, 0.05 * float(i)),
			Vector2.ZERO, 0.2, 1.0, 5.0)
	manager.step(0.016)
	assert_eq(manager.team_count(BulletManager.Team.ENEMY), 0,
		"aucun tir ennemi ne reste compte")
	assert_true(manager.team_count(BulletManager.Team.ENEMY) >= 0,
		"et le compte n'a pas plonge sous zero")

## Le pool reste utilisable apres l'incident : c'est ce qui distingue une erreur journalisee
## d'une corruption. Sans la garde, un index apparait deux fois sur la pile et se retrouve
## alloue a DEUX projectiles a la fois.
func test_the_pool_is_still_sane_afterwards() -> void:
	var manager := _make()
	var target := _suicidal_target(manager)
	manager.register_target(target)
	manager.spawn_bullet(BulletManager.Team.ENEMY, Vector2.ZERO, Vector2.ZERO, 0.2, 1.0, 5.0)
	manager.step(0.016)
	var seen := {}
	for i in 12:
		var index := manager.spawn_bullet(BulletManager.Team.ENEMY,
			Vector2(20.0, 0.0), Vector2.ZERO, 0.2, 1.0, 5.0)
		assert_true(index >= 0, "le pool alloue encore")
		assert_false(seen.has(index),
			"l'index %d n'est alloue qu'une fois — deux le seraient si la pile le portait en double" % index)
		seen[index] = true
