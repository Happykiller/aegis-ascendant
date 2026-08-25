---
titre: Lisibilité — le contrat de lecture
type: reference
statut: actif
maj: 2026-08-25
---

# Lisibilité

> « Lire les projectiles et faire des esquives précises est le cœur du défi d'un shmup. »
> — [Wikipedia, *Shoot 'em up*](https://en.wikipedia.org/wiki/Shoot_%27em_up)

C'est la page dont tout le reste dépend. Un pattern injuste est presque toujours un pattern
**illisible**, pas un pattern trop dense.

## Ce que le genre dit

### Les couleurs se réservent

Le genre a convergé sur les **rouges, roses et violets** pour les balles ennemies — précisément
parce qu'ils **n'entrent pas en collision** avec le jaune et l'orange des explosions et des items.
Un projectile de la couleur d'une explosion disparaît dans la première explosion venue.

Corollaire : une couleur qui **signifie** quelque chose ne doit servir à rien d'autre. Ni au décor,
ni aux effets.

### Le chunking : grouper, ou ne pas être lu

> « Les balles isolées sont difficiles à lire et donnent souvent un sentiment d'injustice. »

Grouper les balles en **lignes et formes claires** permet au joueur de prédire la trajectoire du
groupe au lieu de suivre chaque projectile. Une trajectoire inhabituelle demande un **renfort
visuel** : traînée, allongement, orientation du sprite selon l'angle.

### La télégraphie rend une attaque juste

> « Un laser a l'air d'une attaque puissante ; le télégraphier avant qu'il parte le rend juste. Même
> une simple ligne d'avertissement fine rend le jeu bien plus jouable. »

Ce n'est pas une aide au joueur faible : c'est ce qui transforme une mort en **erreur du joueur**
plutôt qu'en piège.

### La densité n'est pas la difficulté

Sparen consacre une section entière à ce contresens : **« moins de balles ≠ plus facile »**. Un
pattern clairsemé peut être atroce, et des milliers de projectiles peuvent être faciles s'ils
laissent des **couloirs lisibles**.

Deux densités se distinguent :

- **spatiale** — combien de balles dans une zone ;
- **temporelle** — comment leur apparition est étalée dans le temps.

Et une balle **rapide** réduit la densité perçue mais **élargit la zone à surveiller** ; une balle
**lente** concentre l'attention et autorise l'esquive fine. Enfin, l'**espace négatif** — l'absence
de balles — est une donnée de conception à part entière : il naît du **timing**, et c'est lui qui
guide le joueur.

### Profondeur d'affichage

Les balles ennemies passent **au-dessus** du vaisseau joueur ; les petites balles rapides au-dessus
des grosses lentes. Une balle cachée derrière quoi que ce soit est une balle qui tue injustement.

## Chez nous — état au 2026-08-25

| Point | État réel |
|---|---|
| Couleurs réservées | ✅ **Tenu, et écrit dans le shader.** `shaders/space_background.gdshader` porte la règle : le fond « ne touche jamais au cyan réservé au tir allié ni au corail réservé au tir ennemi ». Elle a été appliquée le jour même sur le bolide d'impact du survol de lune (`ADR-0027`) |
| Zone calme centrale | ✅ Le fond s'assombrit au tiers central (`center_calm`) — « l'art ne doit jamais disputer l'attention au vaisseau et aux balles » |
| Télégraphie | ✅ **Présente et nommée.** `EnemyReaction` donne aux unités réactives un `alert_radius` où elles s'éveillent **et le montrent**, puis un `windup_time` avant de frapper. Le Leviathan télégraphie ses bascules par bannière, secousse et son |
| Chunking | ⚠️ **Implicite.** Les salves (`Fire.FAN`, `RADIAL`, `AIMED`) produisent des groupes, mais rien ne garantit qu'un groupe se **lise** comme un groupe — aucune orientation de sprite selon l'angle, aucune traînée sur les trajectoires inhabituelles |
| Densité | ⚠️ **Jamais mesurée.** Aucune notion de densité dans le code ni dans les Resources. La vague du champ d'astéroïdes borne sa population *instantanée* par échelonnement, mais c'est un raisonnement de rythme, pas de lisibilité |
| Profondeur d'affichage | ⚠️ Non vérifié. Le jeu est en 3D avec un plan logique ; l'ordre de rendu dépend de la géométrie, pas d'une règle explicite |

## L'écart, et ce qu'on en fait

**Ce qui est tenu l'est solidement** : la réserve de couleurs est la plus forte des trois, parce
qu'elle est écrite là où elle s'applique et qu'elle a déjà arbitré une décision.

**Deux écarts méritent d'être regardés**, sans rien engager :

1. **Le chunking n'a pas de support visuel.** Une salve radiale de 14 projectiles (Choir Mine) est
   exactement le cas où le genre demande un renfort — orientation selon l'angle, ou traînée. À
   juger en jouant : si les salves se lisent déjà, il n'y a rien à faire.
2. **La densité n'est pas un outil chez nous.** Le genre en fait un paramètre de conception ; nous
   composons les vagues à l'intuition. La première chose utile ne serait pas un réglage mais une
   **mesure** : combien de projectiles hostiles simultanés, et sur quelle fraction de l'écran.

⚠️ **Aucune de ces deux pistes ne se tranche au journal.** Ce sont des questions de perception, et
`ADR-0019` a montré ce que coûte de croire une mesure automatique sur une question de ressenti.
