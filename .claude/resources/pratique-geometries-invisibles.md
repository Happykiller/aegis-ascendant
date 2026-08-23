# Bonne pratique — les géométries Godot qui disparaissent sans une erreur

## La famille

Cinq façons, dans ce projet, pour une géométrie parfaitement construite de **ne rien rendre à
l'écran** — ou de tout recouvrir — sans exception, sans `push_error`, sans une ligne au journal. Toutes les trois se
diagnostiquent en capture et **uniquement** en capture : le code se lit juste, les tests passent,
et il n'y a rien à voir.

Le réflexe commun : **quand un effet ne s'affiche pas, ne pas d'abord suspecter son propre calcul.**
Les trois pièges ci-dessous se situent tous *après* le calcul, dans la façon dont Godot consomme
le résultat.

---

## 1. Le billboard jette l'échelle du nœud

`BaseMaterial3D.billboard_mode = BILLBOARD_ENABLED` reconstruit la base du maillage pour le tourner
vers la caméra, et **cette base est orthonormée** : toute échelle posée sur le nœud est purement et
simplement écrasée.

```gdscript
mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
mat.billboard_keep_scale = true   # ⚠️ sans lui, `node.scale` ne sert à rien
```

**Ce que ça a coûté (23/07/2026)** : le flash d'explosion (`vfx_explosion.gd`) est passé d'une
`SphereMesh` à un quad billboard pour supprimer ses facettes. Il animait sa taille par
`_flash.scale`, de 0,2 à 3,6 unités. Sans le drapeau, il est resté à sa taille unitaire — donc
invisible. **Trois captures entièrement vides** avant de comprendre : le code d'animation était
juste, l'effet était bien joué, la mort du joueur ne montrait simplement plus rien.

---

## 2. `GPUParticles3D.emitting` ne dit pas « il reste des particules »

Sur un système `one_shot`, `emitting` retombe à `false` dès que la salve est **ÉMISE**, pas quand
elle s'éteint. S'en servir pour savoir s'il reste quelque chose à l'écran est un contresens.

```gdscript
# ❌ le système a fini d'émettre depuis longtemps, ses particules volent encore
if _elapsed >= (_debris.lifetime if _debris.emitting else 0.0):
# ✅ relever la durée au moment du tir, et s'en souvenir
_debris_life = _debris.lifetime   # dans play()
if _elapsed >= maxf(_sparks.lifetime, _debris_life):
```

**Ce que ça a coûté (23/07/2026)** : les morceaux de coque d'une explosion rendaient l'effet au pool
**en plein vol**. À l'écran, les débris de la mort du joueur disparaissaient d'un coup à mi-course —
un défaut qu'aucun test ne voit (le pool fonctionne, l'effet est bien recyclé) et qui ne se lit que
sur une capture prise à la bonne image.

---

## 3. La boîte englobante ne suit pas un maillage déformé au vertex

Une géométrie allongée ou gonflée **dans le vertex shader** garde l'AABB de son maillage au repos.
Godot la cull dès qu'elle sort de cette boîte, et elle clignote ou disparaît selon l'angle.

La parade est `extra_cull_margin`, et elle est déjà documentée sur place — `beam.gd:37-40` et
`BossController._pad_cull_margin`. Elle est citée ici parce qu'elle appartient à la même famille :
**la géométrie est juste, et rien ne s'affiche.** `EnginePlume.make()` la pose pour la même raison.

⚠️ Contrairement aux deux précédentes, celle-ci n'a **pas** été payée dans la session du 23/07/2026 :
elle a été appliquée d'emblée en reprenant le précédent du faisceau. Elle est listée pour compléter
la famille, pas comme une découverte.

---

## 4. Un nœud posé en coordonnées MONDE hérite quand même de ses ancêtres

`Beam.aim()` calcule sa pose en coordonnées monde (`GameplayPlane.to_world(...)`). Le faisceau
était ajouté comme enfant du module de combat — un `Node` sans transformation — lui-même enfant du
`BossController`. **Godot remonte l'arbre jusqu'au premier ancêtre `Node3D`** : le `Node`
intermédiaire ne protège de rien, et la position du boss s'applique **une seconde fois**.

```gdscript
var beam := Beam.make()
beam.top_level = true   # ⚠️ ignore la transformation des parents
add_child(beam)
```

**Ce que ça a coûté (23/08/2026)** : les tourelles-épines du Leviathan tiraient — timers corrects,
état `FIRING` atteint, dégâts appliqués au joueur — et **aucun laser à l'écran**. Le boss combat à
une douzaine d'unités du centre, donc le faisceau partait au double, hors du cadre. Ni erreur, ni
test rouge : la seule chose visible était une capture sans le moindre trait.

⚠️ **`HarvesterCombat._build_beam()` attache ses deux faisceaux exactement de la même façon** et
n'a pas été vérifié. Si les faisceaux du mini-boss sont décalés, personne ne l'a jamais remarqué —
c'est au backlog.

⚠️ Cousin du même piège, rencontré dans la foulée : **un vaisseau à la même hauteur qu'une grande
coque est *dans* cette coque**, donc masqué par elle. Le chasseur entrant dans le noyau du boss
avait disparu — pas de bug, de la géométrie. La parade est un décalage purement visuel
(`PlayerFighterController.plane_lift`), qui ne touche ni `plane_position`, ni les collisions, ni
les tirs.

---

## 5. Une paroi qu'on regarde de l'intérieur ne doit rendre QUE ses faces internes

Pour une chambre (sphère retournée), `flip_faces = true` ne suffit pas : si le matériau est en
`CULL_DISABLED`, la face avant est rendue elle aussi et **la coque se referme sur le cadre**.

```gdscript
sphere.flip_faces = true                             # on la regarde du dedans
material.cull_mode = BaseMaterial3D.CULL_BACK        # ⚠️ JAMAIS CULL_DISABLED ici
```

**Ce que ça a coûté (23/08/2026)** : l'intérieur du noyau du Pale Leviathan rendait un **disque
bordeaux plein écran** — plus de boss, plus de joueur, plus de flux. Symptôme spectaculaire,
diagnostic instantané *en capture*, invisible partout ailleurs.

---

## Le corollaire de méthode

Ces cinq pièges ont en commun de ne produire **aucun signal** : ni erreur, ni avertissement, ni
test rouge. La seule chose qui les révèle est **une capture prise à la bonne image**, ce qui suppose
de savoir *quand* regarder :

```bash
# le compteur de --capture-after se REARME à chaque chargement de scène
./scripts/deploy-win.sh -- ++ --goto-graybox --defeat-demo --capture --capture-after=780
```

Voir [howto-verifier-un-rendu](howto-verifier-un-rendu.md) pour la procédure, et
[pratique-revue-asset](pratique-revue-asset.md) pour le choix de la vue.
