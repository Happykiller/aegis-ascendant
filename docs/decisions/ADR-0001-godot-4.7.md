# ADR-0001 — Godot 4.7-stable au lieu de 4.6

> **Correctif de version appliqué le 2026-09-05 : le projet tourne désormais sur
> `4.7.2-stable`** (`ed1daf0bf`). Même mineure, donc aucune décision n'est rouverte — seuls
> `scripts/bootstrap.sh` et les chemins de templates changent. Porte de qualité verte au
> premier essai, sans une seule modification de source.
>
> ⚠️ Le passage a révélé un défaut du bootstrap : le cache était indexé par NOM DE FICHIER, et
> `SHA512-SUMS.txt` ne porte pas la version — l'ancien fichier de sommes était donc réutilisé en
> silence, et la vérification échouait en accusant le *format*. Le cache est maintenant rangé
> par version, et un fichier de sommes qui ne parle pas de nos deux archives est refusé
> explicitement.

- **Date** : 2026-07-11
- **Statut** : accepté (décision utilisateur)

## Contexte

La spec (`docs/SPEC_AEGIS_ASCENDANT.md`, §2) a été rédigée pour Godot 4.6, dernière stable à
l'époque. Au démarrage du projet, **Godot 4.7-stable** est disponible (publiée avant le début du
développement). Aucun Godot n'était installé : le choix de version était ouvert.

## Décision

Utiliser **Godot 4.7-stable** pour tout le projet.

## Conséquences

- Toute vérification d'API, de classe ou d'option CLI vise la doc **4.7**
  (https://docs.godotengine.org/en/4.7/) — les liens 4.6 de la spec §39 sont à transposer.
- Binaires officiels vérifiés (SHA512) depuis
  `https://github.com/godotengine/godot/releases/download/4.7-stable/` :
  `Godot_v4.7-stable_linux.x86_64.zip`, `Godot_v4.7-stable_export_templates.tpz`.
- Export templates installés dans `~/.local/share/godot/export_templates/4.7.stable/`.
- `export_presets.cfg` suit le format 4.7 ; si l'éditeur normalise le fichier, committer sa version.
- Avantage notable 4.7 : l'édition des ressources PE (icône, métadonnées) à l'export Windows est
  native — **rcedit n'est pas nécessaire** depuis Linux.
