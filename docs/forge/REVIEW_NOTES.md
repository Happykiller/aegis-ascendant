# Notes de revue — production forge (audit 2026-07-11)

Suivi des points relevés à la revue du concepteur sur la première grande passe `asset-forge`.
La production est globalement solide (prompts IP-propres, provenance sans trou réel, script
audio déterministe et sans téléchargement, SVG propres et conformes). Points de suivi :

## IP — traité
- 7 planches `reference_*.png` (marques visibles) → d'abord quarantinées hors dépôt (ADR-0005), puis
  **réinstaurées comme références visuelles légitimes** dans `assets/reference/inspiration/` et versionnées
  (**ADR-0009**, projet personnel non commercial). Les 8 planches de concept originales sont conservées.

## À corriger avant modélisation 3D (briefs futurs)
- ~~**Aegis Citadel** : la vue de face lit comme un buste torse+épaules — abaisser/écarter les bras
  pour casser cette lecture humanoïde.~~ **RETIRÉ le 20/07/2026 par ADR-0011.** Le propriétaire
  arbitre en faveur de la fidélité à la planche de concept, laquelle présente elle-même cette
  lecture. La consigne est supprimée plutôt que contournée : la laisser coexister avec « aussi
  proche de la planche que possible » aurait produit des arbitrages opposés d'une session à l'autre.
- **Pale Leviathan** : le noyau magenta est presque centré alors que le canon exige un noyau
  **décentré** (silhouette asymétrique, §15.5). Décentrer réellement à la modélisation.
  ⚠️ Cette dette-ci **tient toujours** : elle vient du canon, pas d'une lecture de planche.

## À arbitrer en Phase 1 (test capture)
- **VFX explosions** : `small/medium/heavy_explosion`, `debris_burst`, `sparks` emploient un
  orange chaud `#FF8A32`. `graybox_palette.md` (§limites) recommande des explosions
  **froides/désaturées** pour préserver la saillance du corail `#FF5A3D` du danger ennemi.
  À vérifier à l'écran (glow + tone mapping) avant de figer.

## Livrable manquant
- **BRIEF-0019 (frégates & batteries externes)** : le prompt de génération est produit
  (`docs/forge/output/frigates_and_batteries_generation_prompt.md`) mais la planche raster
  `assets/reference/concepts/frigates_and_batteries_concept_sheet.png` **n'a jamais été générée**.
  Statut : *prompt livré, image à produire*. À régénérer via l'outil imagegen puis provenancer.

## Cosmétique
- `sparks.svg` : description CSV « froides et or » alors que l'asset contient de l'orange —
  harmoniser la description ou retirer l'orange.
- Écarts palette assumés (non normatifs) : `#8C5BE8` (orbit_drone, violet éclairci),
  bleus-gris de `parallax_03_planet`.

---

# Revue BRIEF-0021 — thème principal (2026-07-12)

Livrable forge : `docs/forge/output/main_theme_spec.md` (spec seule, aucun audio — conforme au
brief). Implémentation : `tools/audio/generate_main_theme.py` (session principale, ADR-0007 §3).

## IP — conforme
Deux références ont été données par le commanditaire : Hans Zimmer, et une playlist de mashups
hypertechno composée de **reprises de titres sous licence**. Le brief les a cadrées comme des
références de *genre et d'énergie*, jamais de matériau, et la spec livrée tient la ligne : aucune
œuvre, aucun artiste, aucun titre n'y figure — pas même en négatif. Le seul matériau mélodique est
la cellule signature du jeu (`+5, −2, +4` → D–G–F–A) ; la grille d'accords en est **dérivée**
(chaque accord est choisi pour la couleur qu'il donne à la note de cellule qu'il porte), et non
empruntée. Le sidechain est le seul emprunt à la production techno : c'est une enveloppe de gain,
pas un matériau. Rien à quarantiner.

## Écart assumé à la table de gains du §6.1
Rendus tels quels, les gains de la spec donnent une crête pré-`tanh` de **3,18** (son assertion
§9-3 exige < 1,6) et un RMS de **0,190** (sa fenêtre §6.5 : [0,14 ; 0,18]). Ce n'est pas une erreur
de la spec : ses gains sont des **rapports entre voix**, et chaque voix sort normalisée à 1,0 par
note isolée (§2) — leur somme dépasse forcément le plein échelle. Deux facteurs explicites, plutôt
qu'une réécriture silencieuse de sa table :
- `MASTER_TRIM = 0.40` — le fader de bus. Préserve **tous** les équilibres relatifs, et règle la
  dynamique : moins on entre fort dans le `tanh`, moins il colle.
- `PERCUSSION_TRIM = 0.85` — le remède que la spec **prescrit elle-même** au §6.5 pour un RMS trop
  haut (« baisser les gains percussifs, ne pas augmenter le drive »).

Résultat : crête pré-`tanh` **1,219**, RMS **0,169**, couture **0,0101**, 3 628 800 frames pile,
SHA-256 identique sur deux rendus. Les huit assertions du §9 passent.

## Intégration — deux écarts à la recommandation §6.5, tous deux dus à l'architecture réelle
La spec a été écrite en supposant un lecteur nu sur le bus `Music`. `AudioManager` en a un autre :
deux decks, un état (`MusicDirector.State`), et un niveau de deck à `_MUSIC_ON_DB = -3 dB`.
- **Niveau** : la spec recommande `volume_db = -7.0`. Dans la chaîne réelle (deck −3 dB, bus
  `Music` −4 dB), la valeur qui reproduit ce niveau net est **`-4.0`** — c'est celle du banc.
- **Sortie de l'écran titre** : la spec recommande un fondu de sortie de 0,4 s sur Entrée. On ne le
  fait pas : le graybox réclame `LAUNCH` à son `_ready()` et `AudioManager` **enchaîne les deux
  pistes**. Couper d'abord vers le silence ne ferait qu'installer un trou là où il y a une passation.

## Points de la spec à conserver tels quels (ne pas « corriger »)
- Le **G sur Dm** des mesures 35–36 (Dm add11) et le **B♭maj7** fugitif de la mesure 30 sont des
  couleurs voulues, signalées par la forge.
- Le **drone est la seule voix du buffer `body`** : ses fréquences sont recalées sur la grille de
  boucle et il ne reçoit **aucune réverbe**. Lui replier une queue le doublerait dans les trois
  premières secondes — c'est le piège principal de l'implémentation (§7.2).
- `pad` et `ostinato` sont **deux** voix de cordes distinctes. Les fusionner ferait sonner
  l'ensemble comme un seul synthé large.

## Suivi
- Les primitives de synthèse (`saw_lp`, `noise_band`, `formant_voice`…) sont pour l'instant
  **dupliquées** entre `generate_music.py` et `generate_main_theme.py`. La factorisation dans un
  `tools/audio/synth.py` est une suggestion de la forge (§10), pas une exigence : à faire au
  troisième script, pas avant.
- Le thème n'a **pas encore été validé à l'oreille** par le commanditaire au moment du commit.
