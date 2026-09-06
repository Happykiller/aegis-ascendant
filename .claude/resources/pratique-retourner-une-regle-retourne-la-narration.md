# Retourner une règle, c'est retourner tout ce qui l'annonce — voix comprises

**Payé le 2026-09-06.** Un commit (`5288dd4`) a inversé une règle de gameplay : un nœud d'épine
éteignait le tronçon **suivant**, il éteint désormais **le sien**. Code juste, tests verts, porte
verte. Et pendant ce temps le jeu continuait de dire au joueur exactement le contraire :

- Lyra, à la vue d'un nœud : « *il alimente les tourelles du tronçon **suivant*** » ;
- Lyra, à sa mort : « *le tronçon **d'après** vient de s'éteindre* » ;
- l'objectif de mission du briefing « L'ARTÈRE » : « *Un nœud éteint les tourelles du tronçon
  suivant* ».

Trois textes **vus et entendus par le joueur**, tous faux, aucun test rouge. La loi du dépôt dit
que deux règles opposées valent moins que zéro règle ; ici c'est pire — celle que le joueur croit
est celle qu'on lui dit, pas celle que le code applique.

## La règle

**Quand une règle de jeu s'inverse, la liste des lieux à corriger n'est pas le code.** Elle est :

1. **Le dialogue** (`resources/dialogue/*.tres`) — et **la voix** qui va avec.
2. **Les briefings et objectifs** — un `PackedStringArray` d'objectifs ne ressemble pas à du
   texte, et aucun grep sur un nom de fonction ne l'atteint.
3. **Les bannières de HUD** construites par `%` dans un `.gd`.
4. **Le nom des drapeaux** : `node_weakens_next_section` a survécu deux commits à la règle qu'il
   nommait. Un drapeau qui porte le nom de la règle d'avant est pire qu'un drapeau sans
   commentaire — c'est celui qu'on relit dans six mois pour savoir ce que le jeu fait.
5. **Les commentaires qui justifient un choix par la règle** — huit passages annonçaient « une
   récompense qui arrive quarante secondes plus tard, sur un tronçon que le joueur n'a pas encore
   vu ». Vrais au passé, faux au présent ; les mettre au passé suffit, les effacer perd le motif.

## ⚠️ Le sous-titre sans la voix est pire que rien

Réécrire le `.tres` **sans resynthétiser** fait dire à Lyra une phrase pendant qu'on en affiche
une autre. Le lot est indivisible : texte du `.tres` + texte de la demande `VOX-NNNN` (une garde
les compare) + `.ogg` + `hold` recalé sur la durée **mesurée** de la nouvelle prise.

Et **resynthétiser ne veut pas dire rejouer le lot** : piper tire du bruit dans son prédicteur de
durée, donc relancer `VOX-0005` entier pour deux phrases rend huit fichiers différents, dont six
que personne n'a demandés ni ne réécoutera. `tools/voice/forge_voice.py --cue <cue>` restreint au
cue nommé (ajouté ce jour-là, pour ça).

## Comment le trouver

Grep sur la **formule** que la règle employait, pas sur le symbole :

```bash
grep -rni "tronçon suivant\|troncon suivant\|section suivante\|quarante secondes" \
     scripts/ resources/ docs/KB/ tests/ .claude/
```

⚠️ **Balayer la casse ET les accents.** Le docstring de classe disait « tronçon **SUIVANT** » en
capitales : un grep sensible à la casse l'a manqué, et c'était la première ligne du fichier qui
implémente la règle.

## Voir aussi

- [Renommer ce que le joueur lit](pratique-renommer-ce-que-le-joueur-lit.md) — même discipline
  pour un nom de fiction ; là-bas les identifiants ne bougent pas, ici **si** (le drapeau).
- [Un indicateur ne voit que ce qu'il compte](pratique-un-indicateur-ne-voit-que-ce-qu-il-compte.md)
