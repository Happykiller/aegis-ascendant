---
titre: Lisibilité — le contrat de lecture
type: reference
statut: actif
maj: 2026-08-27
---

# Lisibilité

C'est le domaine dont tous les autres dépendent. Un pattern injuste est presque toujours un pattern
**illisible**, pas un pattern trop dense.

| Loi | Force | Énoncé |
|---|---|---|
| `LOI-LIS-01` | **LOI** | Une couleur qui signifie quelque chose ne sert à rien d'autre |
| `LOI-LIS-02` | **LOI** | Grouper, ou ne pas être lu |
| `LOI-LIS-03` | CONTRAINTE | Une trajectoire inhabituelle exige un renfort visuel |
| `LOI-LIS-04` | **LOI** | Toute attaque qui tue s'annonce avant de partir |
| `LOI-LIS-05` | **LOI** | La densité n'est pas la difficulté |
| `LOI-LIS-06` | INTENTION | L'espace négatif est une donnée de conception |
| `LOI-LIS-07` | CONTRAINTE | La vitesse d'un projectile arbitre entre zone à surveiller et esquive fine |
| `LOI-LIS-08` | **LOI** | Rien de mortel ne passe derrière quoi que ce soit |

---

### `LOI-LIS-01` · Une couleur qui signifie quelque chose ne sert à rien d'autre — **[LOI]**

Le genre a convergé sur les **rouges, roses et violets** pour les projectiles ennemis, précisément
parce qu'ils **n'entrent pas en collision** avec le jaune et l'orange des explosions et des bonus.

Un projectile de la couleur d'une explosion **disparaît dans la première explosion venue**. La
réserve vaut donc pour tout : ni le décor, ni les effets, ni l'interface ne réemploient une couleur
qui porte un sens de gameplay.

### `LOI-LIS-02` · Grouper, ou ne pas être lu — **[LOI]**

> « Les balles isolées sont difficiles à lire et donnent souvent un sentiment d'injustice. »

Grouper les projectiles en **lignes et formes claires** permet de prédire la trajectoire du
**groupe** au lieu de suivre chaque balle. Le joueur ne lit pas des objets : il lit des formes.

### `LOI-LIS-03` · Une trajectoire inhabituelle exige un renfort visuel — [CONTRAINTE]

Traînée, allongement, orientation du sprite selon l'angle : une balle qui ne va pas là où sa forme
le laisse croire doit **dire** où elle va. Le renfort est proportionnel à l'écart avec l'attendu.

### `LOI-LIS-04` · Toute attaque qui tue s'annonce avant de partir — **[LOI]**

> « Un laser a l'air d'une attaque puissante ; le télégraphier avant qu'il parte le **rend juste**.
> Même une simple ligne d'avertissement fine rend le jeu bien plus jouable. »

Ce n'est pas une aide au joueur faible : c'est ce qui transforme une mort en **erreur du joueur**
plutôt qu'en piège. La durée d'annonce est un paramètre de projet — quelques centaines de
millisecondes, croissantes avec la gravité de l'attaque — mais son **existence** n'est pas
négociable.

⚠️ Corollaire, coûteux à apprendre autrement : **une annonce annulable enseigne à ignorer les
annonces**. Si un télégraphe peut être interrompu en reculant, le joueur apprend que les
avertissements ne valent rien.

### `LOI-LIS-05` · La densité n'est pas la difficulté — **[LOI]**

**Moins de balles ≠ plus facile.** Un pattern clairsemé peut être atroce ; des milliers de
projectiles peuvent être faciles s'ils laissent des **couloirs lisibles**.

Deux densités se distinguent et se règlent séparément :

- **spatiale** — combien de balles dans une zone donnée ;
- **temporelle** — comment leur apparition s'étale dans le temps.

### `LOI-LIS-06` · L'espace négatif est une donnée de conception — [INTENTION]

L'absence de balles n'est pas ce qui reste : c'est ce qui **guide**. Elle naît du **timing** avant
de naître de la géométrie, et elle se conçoit aussi délibérément que les projectiles eux-mêmes.

### `LOI-LIS-07` · La vitesse d'un projectile arbitre entre zone à surveiller et esquive fine — [CONTRAINTE]

Une balle **rapide** réduit la densité perçue mais **élargit la zone à surveiller**. Une balle
**lente** concentre l'attention et autorise l'esquive fine. Il n'y a pas de bon réglage dans
l'absolu : il y a un choix, et il doit être conscient.

### `LOI-LIS-08` · Rien de mortel ne passe derrière quoi que ce soit — **[LOI]**

Les projectiles ennemis se dessinent **au-dessus** du vaisseau joueur ; les petites balles rapides
au-dessus des grosses lentes. **Une balle cachée derrière quoi que ce soit est une balle qui tue
injustement.**

## Sources

- [Boghog's bullet hell shmup 101](https://shmups.wiki/library/Boghog%27s_bullet_hell_shmup_101) — Shmups Wiki : réserve des couleurs, chunking, télégraphie, profondeur d'affichage.
- [Sparen's Danmaku Design Studio — A4, densité](https://sparen.github.io/ph3tutorials/ddsga4.html) — densité spatiale/temporelle, espace négatif, « moins de balles ≠ plus facile ».
- [Shoot 'em up](https://en.wikipedia.org/wiki/Shoot_%27em_up) — Wikipedia : lire les projectiles est le cœur du défi.
