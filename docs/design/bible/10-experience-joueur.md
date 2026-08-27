---
titre: Expérience joueur — sensation, flow, apprentissage, accessibilité
type: reference
statut: actif
maj: 2026-08-27
---

# Expérience joueur

Ce que le joueur **ressent**, par opposition à ce que le jeu **contient**. Quatre sujets qui n'ont
rien à voir entre eux sauf leur destinataire : la sensation de pilotage, la courbe de flow, la
manière dont on apprend sans qu'on nous explique, et ce qui laisse quelqu'un dehors.

## Ce que le métier dit

### Le *game feel* tient en trois choses qui doivent s'aligner

> Un jeu est agréable quand trois choses s'alignent : **les commandes répondent à l'instant** où
> l'on appuie, **chaque action produit un retour que le joueur peut lire**, et une **couche de
> finition** transforme chaque interaction en quelque chose de satisfaisant.

Les deux premières forment le *game feel* ; la troisième est la *juice*. Distinction utile :

> La *juice* est l'esthétique **non fonctionnelle** : elle **ne change pas les règles** du jeu, elle
> change **l'expérience** du jeu.

⚠️ D'où une règle de priorité que le genre applique sans la dire : on ne « juice » pas un jeu dont
les commandes répondent mal. La finition amplifie la sensation existante, y compris quand elle est
mauvaise.

### Les techniques nommées

| Technique | Ce qu'elle fait | Repère chiffré |
|---|---|---|
| **Hit stop** | fige tout, brièvement, à l'impact — « fait atterrir la conséquence » | **60 à 80 ms** sur une frappe décisive |
| **Screen shake** | traduit la violence sans l'infliger | *The Art of Screenshake* recense une **trentaine** de trucs cumulés |
| **Squash & stretch, anticipation, follow-through** | emprunts directs aux douze principes de l'animation Disney | — |
| **Input buffering** | mémorise une commande envoyée trop tôt | quelques images |
| **Coyote time** | tolère une commande envoyée trop tard | **5 à 10 images** |

Les deux dernières partagent une même idée, et c'est la plus transposable : **le jeu accepte
l'intention du joueur plutôt que la précision de son doigt**.

### Le flow : ni ennui, ni angoisse

Le canal de flow oppose deux échecs symétriques : « les défis montent **trop lentement** par rapport
aux compétences » → **ennui** ; « les défis montent **plus vite** que la compétence ne s'acquiert »
→ **angoisse**. Les deux mènent au même mot, « le pire qu'un concepteur puisse entendre » :
frustration.

### La dent de scie, et l'ordre contre-intuitif

La difficulté ne doit pas monter en ligne droite mais **osciller**. La règle est plus précise qu'on
ne croit :

> Ne jamais donner une nouvelle capacité au joueur sans la lui enseigner, ni sans le laisser s'y
> habituer. On lui donne une capacité ou une arme, **puis on baisse volontairement la difficulté**.
> Une fois qu'on est sûr qu'il est à l'aise, on remonte — pour redescendre plus tard.

Autrement dit : **après un gain de puissance vient une phase de fantasme de puissance**, pas un pic.
Et l'oscillation est **fractale** — elle existe à l'intérieur d'une séquence comme entre deux zones.

### On apprend en jouant, pas en lisant

Le cas d'école reste le premier niveau de *Super Mario Bros.* : quinze écrans qui enseignent tout
sans une ligne de texte. Trois principes en sortent :

1. **Commencer par de l'espace** — de la place pour apprendre à se déplacer avant toute complexité.
2. **Un environnement d'apprentissage sûr** — l'erreur doit être **peu coûteuse** au premier essai.
3. **Progresser ensuite** — n'introduire une nouveauté qu'une fois la précédente acquise.

Le détail le plus cité : le premier trou a **un fond**, on peut s'y tromper sans mourir — et il est
**immédiatement suivi** d'un trou presque identique, celui-là mortel. On a appris, puis on est
évalué, sans jamais avoir été prévenu.

### L'accessibilité de base

Quatre plaintes reviennent plus que toutes les autres : **remappage**, **taille de texte**,
**daltonisme**, **présentation des sous-titres**. Les lignes du niveau « basic » qui concernent un
jeu d'action rapide :

- « Permettre le **remappage / la reconfiguration** des commandes » et « ajuster la **sensibilité** ».
- « S'assurer qu'**aucune information essentielle n'est portée par une couleur seule** ».
- Taille de police lisible par défaut, **fort contraste** texte/fond.
- « Éviter les images clignotantes et les motifs répétitifs » (photosensibilité).
- Offrir un **choix large de difficulté**.

## Chez nous — état au 2026-08-27

### Sensation : la réponse est acquise, la finition l'est presque

| Point | État réel |
|---|---|
| Réponse aux commandes | ✅ `accel_time = 0,18 s`, sous les 0,25 s exigés (spec §7.3), et **`validate()` le fait échouer** au-delà — la sensation est protégée par un test, pas par une intention |
| Tir | ✅ automatique et continu, `fire_interval = 0,12 s` : il n'y a pas de latence de tir puisqu'il n'y a pas d'acte de tir |
| Inclinaison visuelle | ✅ `max_bank_deg = 35` sur `VisualRoot` — **n'affecte jamais la hitbox**, et c'est écrit deux fois dans le code |
| Screen shake | ✅ centralisé, à **trauma** (`CameraDirector.add_trauma()`, intensité en trauma²) |
| Retour d'impact | ✅ gerbe teintée par camp, flash de coque, catégories d'explosion, texte flottant au ramassage, cue audio par type de bonus |
| **Hit stop** | ❌ **absent** — aucune occurrence de `time_scale` dans `scripts/` |
| Input buffering / tolérance | ❌ sans objet : aucune commande n'a de fenêtre (pas de saut, pas de dash, pas de bombe) |

### Flow : la dent de scie existe, mais l'ordre est inversé au moment clé

L'arc alterne bien tension et repos — vagues, mini-boss, traversée, boss, appontage. Mais la règle
« nouvelle puissance **puis** baisse de difficulté » n'est **pas** appliquée : la montée en
puissance est **continue** (un Power Core tous les 12 ennemis, voir
[`08-boucle-de-jeu.md`](08-boucle-de-jeu.md)) et ne provoque aucun palier de respiration. Le joueur
ne vit jamais le moment « je suis devenu fort, et ça se voit ».

### Apprentissage : il n'y a pas d'ouverture

**Les premiers ennemis apparaissent à `time_offset = 0.3`** — trois dixièmes de seconde après le
début de la partie (`resources/encounters/wave_graybox_01.tres`), en deux nuées de quatre.

La spec §5.2 demande pourtant, en premier point de la courbe d'intensité, une **« prise en main
calme »**. Elle n'existe pas. Il n'y a ni tutoriel, ni écran de commandes, ni espace vide initial :
le joueur découvre qu'il se déplace en se faisant tirer dessus.

### Accessibilité : le plus gros écart de la page

| Ligne « basic » | État réel |
|---|---|
| Remappage | ❌ **absent.** `InputBootstrap` déclare les actions en dur ; son propre commentaire dit que l'UI de remappage « viendra plus tard » |
| Manette | ❌ **absente.** Seul `_add_key_action()` existe — **aucun événement joypad n'est enregistré**, alors que la spec §7.2 décrit une disposition Xbox complète |
| Secousse réduite/désactivable | ⚠️ **codée mais injoignable** : `CameraDirector.shake_multiplier` documente « 0 désactive entièrement » (spec §16.3) — et le menu d'options n'expose que **4 volumes + la pixelisation** |
| Information par la couleur seule | ✅ **tenu, et surveillé** : un cue audio par type de bonus, « parce qu'un bonus doit être identifiable sans le regarder » (`graybox_root.gd:253`), et la charte créative l'interdit explicitement |
| Choix de difficulté | ❌ un seul réglage de difficulté, non exposé |
| Clignotement | ⚠️ l'invulnérabilité fait clignoter la coque à **~18 Hz** (`_update_invuln_blink`) — sur le vaisseau seul, pas en plein écran, mais c'est la zone que le joueur fixe |

## L'écart, et ce qu'on en fait

**Le geste le moins cher du projet, tous chantiers confondus** : exposer `shake_multiplier` dans le
menu d'options. Le système existe, le multiplicateur existe, la spec l'exige (§7.3 : « secousse
réduite ou désactivable »), les référentiels d'accessibilité le classent en niveau de base — il
manque **une ligne d'UI** à côté de la case « pixelisation », qui est déjà branchée sur le même
chemin de réglages persistants.

**Tenu, et à ne pas dégrader.** La réponse aux commandes est bonne **et testée** ; la règle « jamais
la couleur seule » est vivante dans le code. Ce sont deux acquis que le genre considère comme
difficiles.

**Piste ouverte, non décidée — l'ouverture calme.** Trois secondes sans ennemi au début de la
partie coûteraient un `time_offset` et donneraient au joueur ce que la spec lui promet. ⚠️ Mais la
démo vise « 2-3 minutes irréprochables » (backlog P0) : trois secondes vides au démarrage sont
aussi trois secondes où un spectateur ne voit rien. C'est un arbitrage d'opérateur, pas une
évidence.

**Piste ouverte — le hit stop.** 60 à 80 ms de gel sur la destruction d'une plaque du boss ou sur
le coup fatal au mini-boss est la technique la plus rentable du game feel. ⚠️ À instruire avant
d'écrire : sous Godot, agir sur `Engine.time_scale` fige **aussi** les VFX, la caméra et l'audio
positionnel, et le projet a un budget GPU par image qu'un gel modifie de manière trompeuse
(cf. `.claude/resources/INDEX.md` sur la mesure de perf).

> **À COMPLÉTER — décision de l'opérateur.** Le support manette est décrit par la spec §7.2 et
> n'existe pas. Pour un shooter montré à un professionnel (spec §1.3), c'est probablement le
> manque le plus visible de cette page. Est-ce **à écrire**, ou **hors périmètre de la démo** ?

## Sources

- [How to Make Your Game Feel Good: A Guide to Game Feel and Juice](https://egmatic.com/blog/how-to-make-your-game-feel-good) — les trois choses qui s'alignent, hit stop 60–80 ms, coyote time, input buffering.
- [The Art of Screenshake](https://www.youtube.com/watch?v=AJdEqssNZ-U) — Jan Willem Nijman (Vlambeer), INDIGO Classes 2013 : la trentaine de trucs cumulés. ⚠️ Conférence vidéo, non transcrite ici.
- [Game Design Theory Applied: The Flow Channel](https://www.gamedeveloper.com/design/game-design-theory-applied-the-flow-channel) — ennui/angoisse, l'oscillation, le caractère fractal.
- [Video Game Level Design and Difficulty](https://stepico.com/blog/video-game-level-design-and-difficulty-how-to-challenge-players-without-losing-them/) — la formulation « tense and release » et l'ordre capacité → baisse de difficulté.
- [Why Super Mario Bros is still a fantastic lesson in game design](https://www.creativebloq.com/3d/video-game-design/why-super-mario-bros-is-still-a-fantastic-lesson-in-game-design) — l'onboarding sans tutoriel, le Goomba préféré au Koopa, le trou sûr avant le trou mortel.
- [Game Accessibility Guidelines — Basic](https://gameaccessibilityguidelines.com/basic/) — remappage, sensibilité, jamais la couleur seule, contraste, clignotement, choix de difficulté.
