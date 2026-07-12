# BRIEF-0021 — Thème principal (écran titre)

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur principal
- **Date** : 2026-07-12

## Objectif

Définir la **direction musicale complète du thème principal** d'Aegis Ascendant — le morceau
qui joue sur l'écran titre — sous la forme d'une spécification exécutable :
`docs/forge/output/main_theme_spec.md`. Le livrable est la **spec**, pas l'audio : la session
principale implémente ensuite le générateur déterministe (`tools/audio/generate_main_theme.py`)
à partir de cette spec, exactement comme `generate_music.py` implémente
`adaptive_music_structure.md` (voir ADR-0007 §3).

## Contexte

L'écran titre (`scenes/boot/boot.tscn`) est actuellement muet. C'est la première chose que le
joueur entend : le thème doit poser le ton du jeu en huit secondes et donner envie d'appuyer
sur Entrée.

Les neuf pistes adaptatives existantes (`adaptive_music_structure.md`) sont le **socle
harmonique** du jeu : ré mineur modal, cellule signature de quatre notes (intervalles
`+5, -2, +4` demi-tons). Le thème principal est le morceau **dont elles dérivent** : il énonce
la cellule signature en clair, dans sa forme la plus large. Un joueur qui a entendu le titre
doit reconnaître le motif quand il ressurgit, dégradé, dans `boss_phase_1` ou `final_charge`.

## Direction musicale (arbitrée avec le commanditaire — normative)

**Hybride orchestral épique posé sur un socle techno.** L'ossature est orchestrale et domine ;
la techno fournit le pouls et l'énergie, jamais la mélodie.

- **Tempo** : ~140 BPM. **Tonalité** : ré mineur (cohérent avec `fleet_battle` / `final_charge`).
- **Couche épique (au premier plan)** : braam de cuivres graves, ostinato de cordes en croches,
  taikos / percussions orchestrales, chœur synthétique abstrait (voyelles, aucune parole).
- **Couche techno (en dessous)** : kick 4/4 saturé, sub-bass, hi-hats en doubles-croches,
  riser de bruit filtré avant le drop, impact au point de bascule.
- **Structure attendue** (indicative, à préciser et justifier) :

  | Section | Rôle |
  |---|---|
  | Intro | drone + braam lointain, kick filtré passe-bas |
  | Montée | ostinato de cordes + taikos, ouverture progressive du filtre, riser |
  | Drop | kick plein + sub + cuivres énonçant la cellule signature |
  | Breakdown | chœur seul, réverbe longue, le pouls disparaît |
  | Reprise | tutti, puis bouclage scellé |

- **Durée** : 60 à 90 s, **bouclable sans couture** (le titre tourne en boucle indéfiniment).
- **Contrainte de boucle** : la fin doit retomber sur le début sans trou ni clic ; prévoir une
  queue de résonance repliée (technique déjà en place dans `generate_music.py`).

## Contraintes

### IP — lire deux fois

Deux références ont été données par le commanditaire. **Toutes deux sont des références de
*genre et d'énergie*, jamais de matériau.**

- **Hans Zimmer** : la direction retenue est celle du **genre** « hybride orchestral »
  (ostinato, braam, percussions massives, harmonie statique). **Interdit** de citer, décalquer
  ou paraphraser un motif, une progression ou un timbre signature d'une œuvre existante de
  Zimmer ou de quiconque. Aucun nom d'œuvre ne doit apparaître dans la spec comme modèle à
  reproduire.
- **Playlist hypertechno fournie** (mashups : *Tainted Love*, *All The Things She Said*,
  *Jenny From The Block*…) : ces morceaux sont des **reprises d'œuvres sous licence**. Ils
  informent **uniquement** la production (densité du kick, traitement de la basse, dramaturgie
  du drop). **Aucune mélodie, aucune ligne de basse, aucune progression d'accords** ne doit en
  être tirée, même transposée ou déguisée.
- Rappels charte : aucun élément identifiable de Macross, Robotech ou d'une autre licence.
- Le seul matériau mélodique autorisé est la **cellule signature du jeu** (`+5, -2, +4`) et ce
  qui en dérive.

### Techniques

- Synthèse **additive/soustractive pure** en numpy : aucun sample, aucune banque externe,
  aucune dépendance nouvelle. Tout timbre décrit doit être **synthétisable** — décrire un
  « braam » comme un empilement de saws désaccordées avec enveloppe et sweep de filtre, pas
  comme « le son de tel film ».
- Déterministe : un RNG à seed fixe, propre au morceau.
- Sortie visée : `assets/source/audio/music/main_theme.wav` (PCM 16 bits, 44 100 Hz, stéréo),
  masterisé et encodé en OGG par `tools/audio/build_audio.py` (déjà en place, rien à modifier).
- Crête sous `-1 dBFS`, aucun clipping. Le morceau du titre ne doit pas écraser les SFX de
  menu : prévoir une marge de niveau.

## Livrables (chemins exacts)

| Fichier | Description |
|---|---|
| `docs/forge/output/main_theme_spec.md` | spec musicale exécutable du thème principal |

La spec doit être **assez précise pour être codée sans deviner** : tempo, nombre de mesures par
section, grille d'accords (degrés), registre de chaque voix, rythmique de chaque percussion,
recette de synthèse de chaque timbre (oscillateurs, désaccords, enveloppes, filtres), niveaux
relatifs, et point de bouclage. Un tableau par section, comme dans
`adaptive_music_structure.md`.

## Provenance

Ligne à ajouter dans `assets/licenses/ASSET_PROVENANCE.csv` :

```
main_theme_spec,docs/forge/output/main_theme_spec.md,audio-spec,asset-forge (Claude),,asset-forge (Claude),proprietary-internal,2026-07-12,docs/forge/briefs/BRIEF-0021-main-theme.md,,"Spec du thème principal (écran titre) — hybride orchestral 140 BPM ré mineur sur socle techno ; matériau mélodique dérivé de la seule cellule signature +5/-2/+4 ; aucune composition citée"
```

## Critères d'acceptation

- [ ] La spec énonce la cellule signature `+5, -2, +4` et l'utilise comme seul matériau mélodique.
- [ ] Chaque timbre est décrit par une recette de synthèse implémentable en numpy (oscillateurs,
      enveloppes, filtres, désaccords), pas par une comparaison à une œuvre existante.
- [ ] Chaque section a une durée en mesures, une grille d'accords et une liste de voix actives.
- [ ] Le mécanisme de bouclage sans couture est explicité.
- [ ] Aucune œuvre, aucun artiste, aucun titre n'est cité comme modèle à reproduire.
- [ ] Ligne de provenance ajoutée au CSV.

## Hors périmètre

- **Ne pas produire d'audio** ni de WAV/OGG : la spec seule.
- **Ne pas écrire ni modifier de code** (`tools/audio/*.py`, `scripts/**`) : la session
  principale implémente le générateur.
- Ne pas toucher aux neuf pistes adaptatives existantes ni à leur structure.
- Pas de musique pour les autres écrans (menu, options, game over) : le titre seulement.
