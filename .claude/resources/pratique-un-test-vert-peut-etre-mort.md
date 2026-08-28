# Bonne pratique — un test vert peut être mort, et il ne le dira pas

## La règle

**GDScript n'a pas d'exception.** Sur un appel invalide, il journalise `SCRIPT ERROR` et
**abandonne la méthode en cours**. Les assertions restantes ne tournent jamais, le tableau des
échecs reste vide — et un harnais qui ne regarde que ce tableau annonce **`[PASS]`**.

Un test mort à sa première ligne se déclare donc **vert**, pour toujours, sans que rien ne le dise.

Deux filets, et il faut **les deux** :

1. **Zéro assertion = échec.** Le symptôme d'une méthode interrompue à sa première ligne est
   qu'elle n'a rien mesuré. `tests/test_runner.gd` le refuse.
2. **`SCRIPT ERROR` dans la sortie = porte rouge.** Une méthode interrompue *après* quelques
   assertions vertes garde un compte non nul : le premier filet ne la voit pas. `scripts/check.sh`
   filtre la sortie du runner.

⚠️ Ne filtrer que `SCRIPT ERROR:`, jamais `ERROR:` : les tests provoquent exprès des `push_error`
(transitions d'état invalides) et les annoncent par `[test] expected error below`.

## Cas vécu (28/08/2026) — deux gardes qui n'ont jamais rien gardé

`test_hud_layout.gd` construisait son HUD ainsi :

```gdscript
var hud: Control = track(FighterHudScript.new()) as Control   # FighterHud extends CanvasLayer
hud._ready()                                                  # SCRIPT ERROR, méthode abandonnée
```

`as Control` sur un `CanvasLayer` rend **`null`**. Les deux méthodes mouraient à leur deuxième
ligne — et rapportaient vert **depuis leur écriture**. Ce sont exactement les tests écrits pour
tenir le défaut « quand l'une d'elles est 100 % rechargée, TOUTES passent à 100 % ».

Le même trou avait laissé passer, le matin même, la disparition d'un membre (`_shield_target`)
qu'un test interrogeait encore : erreur au journal, `[PASS]` à l'écran.

Réparés, **les deux passent** : le comportement gardé était juste. **C'était la garde qui était
morte, pas le code.** C'est le pire cas — on croit couvert ce qui ne l'est pas.

## Le réflexe qui va avec

Après avoir supprimé ou renommé un membre, **relire la sortie des tests**, pas seulement leur
verdict. Un `SCRIPT ERROR` juste au-dessus d'un `[PASS]` désigne la méthode qui vient de mourir.

Et pour poser un garde de ce genre : **le vérifier en le faisant tomber**. Injecter l'erreur qu'il
doit attraper, constater la porte rouge, retirer l'injection. Un garde jamais vu rougir n'est pas
un garde — c'est exactement ce que ce cas démontre.

## Voisin

Un banc de mesure a le même défaut sous une autre forme : il peut être **structurellement faux**
sans erreur. Le 28/08/2026, un modèle headless annonçait que 100 % des positions de joueur
faisaient naître un projectile hors du plan ; le jeu instrumenté en a compté **zéro**. Le modèle
montait le boss **sans coque**, donc sur des angles de plaque de repli, pas ceux du jeu.
Cf. [dessiner avant de raisonner](pratique-dessiner-avant-de-raisonner.md) : quand le banc et le
jeu se contredisent, **c'est le jeu qui a raison**.
