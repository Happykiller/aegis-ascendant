# Un signal déclaré, un relais écrit, un abonné en face — et rien entre les deux

**2026-09-06.** `CortegeSpineNode` déclarait `signal engaged`. `CortegeHardpoints` écrivait
`_on_node_engaged()` et le relayait par `signal node_engaged`. `CortegeRoot` s'abonnait à
`node_engaged` et y branchait la réplique de Lyra.

**Il manquait `node.engaged.connect(_on_node_engaged)` dans `_add_node()`.** Une ligne.

Conséquence : **`node_seen` — la seule réplique du jeu qui enseigne une mécanique** (« ce bulbe sur
l'axe, c'est un nœud ; abattez-le ») **n'a jamais été jouée une seule fois** depuis qu'elle existe.
Sur la cible la plus difficile du niveau, et la seule dont l'effet demande d'avoir compris le
vaisseau.

## Pourquoi rien ne l'a dit

- Aucune erreur : les trois moitiés compilent, chacune est correcte.
- Aucun test rouge : chaque moitié était testable et testée séparément.
- **Au journal, l'absence d'une ligne ressemble à une ligne qu'on n'a pas déclenchée.** `[Lyra]
  node_seen` manquait ; on lit « le joueur n'a pas encore vu de nœud », pas « le signal est mort ».
- Et le jeu tournait parfaitement : les nœuds mouraient, les tronçons s'éteignaient. Seule la
  branche narrative était coupée.

## Comment il a fini par se voir

Par accident, et c'est le point : un drapeau de debug (`--spine-down`) avait été branché sur ce
même signal, et **il ne faisait rien**. Deux lancements à chercher pourquoi le nœud ne mourait
pas ont mené à la ligne manquante. Sans ce drapeau, la réplique serait encore muette.

## Ce qu'on en tire

- **Un signal se teste par sa CHAÎNE, pas par ses maillons.** Le banc qui manquait tient en dix
  lignes : monter le gestionnaire, s'abonner à son signal relayé, faire vivre la pièce, compter les
  émissions (`test_the_manager_relays_a_node_entering_its_window`). Il est rouge sur l'état d'avant.
- **Quand on ajoute une pièce destructible, on connecte TOUS ses signaux dans le même geste.**
  Sur ce dépôt : `destroyed` ET `engaged`. Le premier était branché, le second non — parce que le
  premier a une conséquence de jeu visible et l'autre seulement une réplique.
- **Une absence attendue est un fait ; une absence inattendue est muette.** Le skill `/jouer` dit
  déjà de signaler ce qui manque au journal. Encore faut-il savoir ce qui aurait dû s'y trouver :
  la liste des répliques d'un niveau est dans son `.tres`, et une réplique jamais vue au journal
  après plusieurs parties complètes mérite qu'on remonte sa chaîne.

## Un cousin, trouvé le même jour

**Un banc qui tue d'un coup ne traverse jamais l'état intermédiaire.** `--stern-cut` retirait toute
la vie d'un ancrage par appel : il ne passait donc **jamais** par l'état ENDOMMAGÉ, ne prouvait
rien de la moitié visuelle du lot, et aucune capture ne pouvait le montrer. Il entame désormais à
55 %. Un outil de vérification doit **traverser** ce qu'il prétend prouver.

## Voir aussi

- [Un test vert peut être mort](pratique-un-test-vert-peut-etre-mort.md)
- [Un indicateur ne voit que ce qu'il compte](pratique-un-indicateur-ne-voit-que-ce-qu-il-compte.md)
