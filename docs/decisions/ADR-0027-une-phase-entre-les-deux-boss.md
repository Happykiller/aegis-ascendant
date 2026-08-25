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
5. **Le décor de survol REMPLACERA le fond, il ne s'y ajoutera pas** (lots 2-3, à venir).
   Mesures du 2026-08-25 sur le poste réel (Quadro T1000) : **13,05 ms** par image avec le
   fond complet, **2,73 ms** fond masqué, pour un budget de 16,67 ms. Il ne reste pas 4 ms —
   empiler une lune et des astéroïdes volumétriques par-dessus la nébuleuse ne tient pas. Ce
   que le propriétaire demande (« qu'on n'ait pas le même décor qu'avant le premier boss »)
   et ce que le budget impose désignent la même solution : on échange un poste de dépense
   contre un autre.
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

## Ce qui reste à juger

La phase existe et s'enchaîne ; **son rythme n'a pas été joué à la main.** La composition de
la vague (densité des barrages, superposition puits/sangsues, pic à 32 s) est une hypothèse
de conception, pas une mesure. Elle se juge en jouant — `ADR-0019` a montré ce que coûte de
croire une mesure automatique sur une question de ressenti.
