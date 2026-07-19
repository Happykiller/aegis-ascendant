# ADR-0009 — `_ip_quarantine` réinstauré comme référence visuelle (projet personnel)

- **Date** : 2026-07-19
- **Statut** : accepté (décision du propriétaire du projet)
- **Supersede** : ADR-0005 sur le point de l'**exclusion comme source d'inspiration**, et prime
  (au sens « ADR > spec ») sur les interdits spec §0.2 / §3 et CHARTE_CREATIVE §5 dans ce contexte.

## Contexte

L'ADR-0005 avait quarantiné les 7 planches `reference_*.png` (marques « Macross », « Valkyrie »,
« Zentradi », « VF-class » visibles) : hors dépôt et **jamais utilisées**, même comme référence
interne. Cette posture supposait un risque IP à écarter systématiquement.

Le propriétaire acte que **Aegis Ascendant est un projet personnel, non commercial, non distribué**,
dont il assume le risque IP. Il souhaite que `_ip_quarantine/reference_fortress_battle_scene.png` (et
la bible `reference_gameplay_vfx_environment_board.png`) redeviennent **la cible visuelle** du rendu :
shmup vertical dense — flux de tir bleus serrés, explosions/flashs orange chauds, missiles à traînée,
planète + atmosphère au bord de cadre, forteresse massive.

## Décision

- Les planches de `/_ip_quarantine/` sont **réinstaurées comme référence d'inspiration** pour la
  direction artistique du rendu (composition, densité, chaleur, profondeur, codes couleur).
- Les assets **produits restent des créations originales** informées par cette cible (mêmes coques,
  palettes et silhouettes divergentes qu'aujourd'hui) : on transpose l'intention, on ne décalque pas
  une silhouette sous licence ni un logo/texte de marque.
- **Inchangé depuis ADR-0005** : les PNG contaminés restent **gitignorés**, conservés en local pour
  consultation ; aucune marque tierce n'entre dans l'historique git/LFS. La règle « ne jamais
  `git add -f` sous `/_ip_quarantine/` » **tient**.

## Conséquences

- La spec §0.2/§3 et CHARTE §5 (« interdits absolus ») sont **assouplies par cet ADR** pour ce projet
  personnel : elles restent le garde-fou par défaut, mais ne bloquent plus l'usage des références
  comme inspiration ni un rendu qui s'en rapproche. Renvois ajoutés dans `CLAUDE.md` (§Interdictions)
  et `CHARTE_CREATIVE.md §5`.
- `asset-forge` peut s'appuyer sur ces références pour les briefs de rendu, en produisant de l'original.
- Si le projet devait un jour être distribué ou commercialisé, **cet ADR serait à réviser** (le risque
  IP redeviendrait réel) — la quarantaine gitignorée facilite ce retour en arrière.
