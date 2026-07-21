# BRIEF-0015 — Arrière-plans et parallaxe spatiale

- **Statut** : assigné
- **Assigné à** : asset-forge
- **Rédigé par** : concepteur intérimaire (Codex, continuité exceptionnelle)
- **Date** : 2026-07-11

## Objectif

Créer six couches panoramiques originales permettant de composer un arrière-plan spatial en
parallaxe sans gêner la lecture des projectiles.

## Couches

1. fond spatial et étoiles lointaines ;
2. nébuleuse discrète ;
3. planète et petit satellite ;
4. flotte alliée très distante ;
5. croiseurs intermédiaires ;
6. débris et particules de premier plan.

## Contraintes

- SVG `viewBox="0 0 2048 1024"`, sans texte, metadata, filtre ni dégradé.
- La couche 1 est opaque ; les cinq autres restent transparentes.
- Aplats et strokes uniquement ; densité faible au centre du plan de jeu.
- Fond `#070A12`, étoiles `#EDEAE3` et `#3FD9E8` très ponctuelles.
- Nébuleuse sombre `#1C2B5E` / `#452663`, sans magenta lumineux dominant.
- Planète bleu-gris désaturée, flotte Helios lisible mais moins brillante que le joueur.
- Aucun halo corail `#FF5A3D` persistant dans le décor : couleur réservée au danger.
- Création originale, sans vaisseau, planète ou composition issue d'une licence.

## Livrables

| Fichier | Couche |
|---|---|
| `assets/source/backgrounds/parallax/parallax_01_distant_stars.svg` | base opaque |
| `assets/source/backgrounds/parallax/parallax_02_nebula.svg` | nébuleuse |
| `assets/source/backgrounds/parallax/parallax_03_planet.svg` | planète |
| `assets/source/backgrounds/parallax/parallax_04_distant_fleet.svg` | flotte distante |
| `assets/source/backgrounds/parallax/parallax_05_mid_cruisers.svg` | croiseurs |
| `assets/source/backgrounds/parallax/parallax_06_foreground_debris.svg` | débris |
| `docs/forge/output/space_parallax_layers.md` | ordre et vitesses suggérées |

## Critères d'acceptation

- [ ] Six SVG valides et superposables
- [ ] Centre du plan de jeu peu chargé
- [ ] Profondeur croissante et vitesses documentées
- [ ] Aucun élément confondu avec un projectile dangereux
- [ ] Provenance complète

## Hors périmètre

Pas de shader, particules, caméra, scène, ressource ou intégration Godot.
