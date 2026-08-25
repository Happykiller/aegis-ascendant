# ADR-0027 — Une phase entre les deux boss : le champ d'astéroïdes

- **Date** : 2026-08-25
- **Statut** : accepté (demande du propriétaire ; durée et statut du décor arbitrés par lui)
- **Amende / supersede** : `ADR-0010` sur le **découpage de l'arc** uniquement. Le vaisseau
  unique, l'absence de transformation en forteresse et l'appontage final sont inchangés.
- **Applique** : `docs/plans/2026-08-25-phase-inter-boss-survol-de-lune.md`, lot 1.

## Contexte

Deux manques distincts se rejoignaient sur la même absence :

1. **Le bestiaire n'était jouable qu'au banc d'essai.** Choir Mine, Null Maw et Leech Drone
   étaient livrées, réglées, testées et au codex — et n'apparaissaient dans **aucune
   rencontre**. L'arc n'avait qu'une vague, `wave_graybox_01.tres`, composée de Needle Scout
   et de Crescent Interceptor. Trois unités de bestiaire qui ne se jouent nulle part sont du
   travail payé et non livré.
2. **Le P0 du backlog** disait la même chose depuis le début : « une seule vague de ~10
   Needle Scouts puis mini-boss ; ajouter 1-2 vagues pour 2-3 min de jeu ».

Et l'arc lui-même enchaînait **deux boss dos à dos** : le Harvester tombait, le Leviathan
arrivait dans la seconde. Aucune respiration entre les deux pics.

⚠️ `ADR-0010` avait **supprimé** une phase de milieu de niveau (la transformation en
forteresse). En rajouter une revient sur ce découpage : c'est la raison d'être de cet ADR.

## Décision

**Une phase `ASTEROID_FIELD` s'insère entre `MINI_BOSS` et `FINAL_BOSS`.**

1. **Elle se joue avec les trois unités inemployées, et rien d'autre.** C'est ce qui la
   distingue de la section de chasseurs : on n'y affronte pas des appareils qui manœuvrent,
   on **traverse** un champ. La mine est posée, le puits ne blesse pas, la sangsue freine —
   trois menaces qu'aucune des neuf familles de Needle Scout n'imite.
2. **Elle dure 45 à 60 s**, arbitré avec le propriétaire le 2026-08-25 contre les ~40 s du
   boss final. ⚠️ Cette durée n'est **pas** celle du dernier spawn : les unités qui dérivent
   mettent 17,3 s à traverser le champ à 1,1 u/s. C'est ce trajet qui borne la phase, et
   `test_asteroid_field_wave.gd` le calcule depuis les données réelles plutôt que de faire
   confiance à un commentaire.
3. **Un SECOND `WaveSpawner`, monté en veille.** `WaveSpawner` construit tout son pool dans
   `_ready()` depuis une seule `@export var wave` ; la spec §26.1 interdit tout
   `instantiate()` en cours de partie. Un second nœud avec `autostart = false` préalloue son
   pool au même instant que le premier et dort jusqu'à `begin()`. **Aucune allocation en
   jeu, et la classe qui marche n'est pas touchée** — seulement étendue par un drapeau.
4. **La musique réemploie `FORTRESS_AWAKENING`.** Ce lit était rendu, bouclé et payé depuis
   le 2026-07-12, et **plus aucune phase ne le réclamait** depuis qu'`ADR-0010` a supprimé
   la forteresse. Ses « impacts espacés » à 108 BPM disent exactement ce que la phase
   raconte : on traverse, on ne charge pas. La pression remonte sur la fin de vague, au même
   seuil que la section de chasseurs — le boss final ne doit pas s'ouvrir sur un calme.
5. **Le décor de survol REMPLACE le fond, il ne s'y ajoute pas** (lot 2 livré, lot 3 à venir).
   Mesures du 2026-08-25 sur le poste réel (Quadro T1000) : **13,05 ms** par image avec le
   fond complet, **2,73 ms** fond masqué, pour un budget de 16,67 ms. Il ne reste pas 4 ms —
   empiler une lune et des astéroïdes volumétriques par-dessus la nébuleuse ne tient pas. Ce
   que le propriétaire demande (« qu'on n'ait pas le même décor qu'avant le premier boss »)
   et ce que le budget impose désignent la même solution : on échange un poste de dépense
   contre un autre.

   ✅ **Mesuré le 2026-08-25**, une fois le survol monté — même phase, même instant
   (t = 30 s), même machine, seul le décor change (`--no-flyby` garde le fond habituel) :

   | Décor pendant la phase | GPU / image |
   |---|---|
   | Survol de lune | **0,738 ms** |
   | Fond spatial habituel | **0,938 ms** |
   | **Différentiel** | **−0,200 ms (−21 %)** |

   L'échange est donc gagnant, et pas seulement neutre. ⚠️ **Ces chiffres viennent de la
   RTX 4080, pas du poste qui contraint.** Le budget qui a dicté la décision a été relevé
   sur une **Quadro T1000**, où le même build coûte plus de dix fois plus. Le SIGNE du
   différentiel se transpose (on remplace un shader de nébuleuse plein écran par un ciel
   étoilé allégé plus un peu de géométrie), **son ampleur non** : la mesure qui autorisera
   le budget du lot 3 doit être refaite là-bas.
6. **Les astéroïdes seront solides, la lune restera du décor** (arbitrage du propriétaire).
   Quelques rochers proches deviendront des obstacles ; la surface survolée n'aura ni
   collision ni hitbox. Un survol dont on peut heurter le relief est un autre jeu.

## Conséquences

- ⚠️ **`Phase` et `MusicContext.LevelPhase` se modifient ENSEMBLE.** Le second reflète le
  premier **par valeur** ; insérer `ASTEROID_FIELD` au milieu décale `FINAL_BOSS`, `DOCKING`
  et `VICTORY`. `test_music_director.gd` garde l'alignement — c'est le seul garde-fou, et il
  est là depuis l'origine pour cette raison exacte.
- Aucune de ces valeurs n'est sérialisée dans une Resource : contrairement aux enums
  d'`EnemyData`, l'insertion au milieu est sans danger ici. La règle d'append ne s'applique
  pas.
- `--skip-to-field` rejoint les drapeaux de saut existants ; `--no-wave` coupe désormais
  **les deux** vagues et laisse l'arc passer au boss final, faute de quoi une bissection de
  perf resterait bloquée sur une phase qui ne se termine jamais.
- Un test neuf, `test_every_musical_bed_is_reachable_from_a_phase`, refuse qu'un cue rendu
  n'ait plus aucune phase pour l'atteindre. Fortress Awakening avait dormi six semaines sans
  que rien ne le signale : **un cue orphelin ne casse rien, il ne joue simplement jamais.**

## Le décor, tel qu'il est livré au lot 2

`MoonFlyby` (`scripts/vfx/moon_flyby.gd`) est monté **au montage du niveau** et caché —
contrairement à `CoreInterior`, qui se construit à la plongée : un survol se monte une fois
pour toutes, et la spec §26.1 n'aime pas plus les décors alloués en jeu que les ennemis.
Une **doublure procédurale** tient le rôle tant que la forge n'a pas livré, et le journal
l'annonce à chaque montage.

Trois choses ont été corrigées **parce qu'on a regardé** (ADR-0006), et aucune n'aurait
produit d'erreur :

| Vu en capture | Cause | Correctif |
|---|---|---|
| La lune rendait **rose pâle**, le chasseur blanc s'y perdait | trois lumières chaudes plus `warmth`/`saturation` du post-traitement : un gris neutre ressort rosé | albédo descendu de 0,30 à 0,115, teinte refroidie |
| Les cratères **flottaient au-dessus** de la surface, et se détachaient franchement au limbe | des palets de 0,6 d'épaisseur posés à `R − 0,2` dépassaient de la sphère | pastilles de 0,12, tangentes, rayons divisés par deux |
| Un rocher **frôlait le chasseur** | placé dans le couloir de vol | écarté — au lot 2 le décor est pur, il ne doit rien promettre qu'il ne tienne |

⚠️ **Et un défaut que le TEST a trouvé avant le rendu** : à la première écriture, le ciel du
survol était posé à la hauteur du fond habituel (−5) et les rochers en dessous. Ils auraient
tous été masqués par leur propre ciel, en silence. `test_moon_flyby.gd` mesure désormais
que chaque corps vit **entre le ciel et le plan de jeu**, et que rien ne monte dans le champ.

## Le ciel du survol ne coûte plus ce qu'il ne montre pas

⚠️ **Un uniforme à 0,12 n'économise RIEN.** Le premier survol réglait `nebula_strength` à
0,12, `dust_strength` à 0,08 et `accent_strength` à 0 — en croyant éteindre la nébuleuse.
Le shader calcule ses cinq champs de bruit **inconditionnellement** (trois `warped_fbm`,
plus deux `fbm`) et ne fait que multiplier le résultat par ces facteurs : on payait
intégralement un décor qu'on venait de retirer. Les 0,2 ms gagnés alors ne venaient pas du
ciel mais des **quatre sprites de repères** masqués avec lui.

`space_background.gdshader` porte désormais un **chemin** et non un réglage : l'uniforme
`deep_sky` saute les champs de bruit et ne garde que les étoiles, qui sont factorisées dans
un `starfield()` commun aux deux ciels. Le chemin par défaut est inchangé.

| Décor pendant la phase 2 | GPU / image |
|---|---|
| Survol, chemin `deep_sky` | **0,323 ms** |
| Fond spatial habituel | **0,945 ms** |
| **Différentiel** | **−0,622 ms (−66 %)** |

Trois tirs de chaque, alternés, dispersion **± 0,003 ms**. ⚠️ Un quatrième tir isolé du
témoin avait donné **1,535 ms** — une valeur aberrante qui, prise seule, aurait fait
conclure n'importe quoi. **Une mesure unique ne vaut rien tant qu'on ne connaît pas sa
dispersion.**

## Les impacts, livrés au lot 3

Trois bolides percutent la lune à des instants fixes de la traversée (11 s, 26 s, 40 s).
C'est du **VFX scripté sur des jalons**, pas de la simulation : la scène se joue à
l'identique à chaque partie, sans quoi aucune capture ne se comparerait à la précédente.

⚠️ **Ils n'empruntent pas `VFXManager`.** Celui-ci est dimensionné pour le combat au
premier plan : tailles fixes par catégorie, aucune échelle. Un impact se produit sur une
lune de 60 unités de rayon, à trois fois la distance du plan de jeu — la même explosion y
serait un point. Le décor porte ses propres effets, à sa propre échelle, tous préalloués.

Deux corrections **de charte**, pas de goût :

- Le bolide était d'abord un caillou du décor : **invisible** à trente unités sur fond noir.
  Il s'allume désormais — le joueur doit voir venir le coup.
- Mais **pas en corail** : le premier essai reprenait l'orange des explosions, et un objet
  de cette teinte qui DESCEND se lit comme un projectile ennemi à esquiver — alors qu'il
  appartient au décor et que rien ne peut être fait contre lui. Le fond « ne touche jamais
  au cyan réservé au tir allié ni au corail réservé au tir ennemi » : bolide et flash sont
  **dorés**.

## Ce qui reste à juger

La phase existe et s'enchaîne ; **son rythme n'a pas été joué à la main.** La composition de
la vague (densité des barrages, superposition puits/sangsues, pic à 32 s) est une hypothèse
de conception, pas une mesure. Elle se juge en jouant — `ADR-0019` a montré ce que coûte de
croire une mesure automatique sur une question de ressenti.

Et **le décor n'est qu'une doublure** : la lune est une sphère grise à cuvettes, les rochers
des ellipsoïdes, et **l'intensité de la gerbe d'impact se juge en MOUVEMENT** — une capture
fige la seule chose qui fait lire des débris qui s'envolent. Ce qui est acquis, c'est la
**mécanique** — la bascule aller-retour (vérifiée
en capture : à t = 64 s le boss final se joue sous la nébuleuse revenue, sans résidu), la
parallaxe, et le coût. La beauté est le lot 3.

⚠️ **Un sujet de conception ouvert par l'arbitrage, à trancher au lot 3** : des astéroïdes
solides et des astéroïdes décoratifs partageront le même cadre. Rien ne les distinguera à
l'œil si on n'y pourvoit pas — et le joueur qui essaie d'éviter un rocher qui le traverse,
ou qui traverse un rocher qui le tue, subira la même injustice dans les deux sens.
