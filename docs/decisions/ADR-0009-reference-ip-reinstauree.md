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
dont il assume le risque IP. Il souhaite que `reference_fortress_battle_scene.png` (et la bible
`reference_gameplay_vfx_environment_board.png`) redeviennent **la cible visuelle** du rendu :
shmup vertical dense — flux de tir bleus serrés, explosions/flashs orange chauds, missiles à traînée,
planète + atmosphère au bord de cadre, forteresse massive.

## Décision

- Les planches sont **sorties de quarantaine et versionnées** comme références visuelles légitimes
  du projet, dans **`assets/reference/inspiration/`** (étape source, `.gdignore`é : jamais importées par
  Godot). Le répertoire `/_ip_quarantine/` et son exclusion `.gitignore` sont **supprimés**.
- Elles sont la **cible d'inspiration** du rendu (composition, densité, chaleur, profondeur, codes
  couleur) et sont provenancées dans `assets/licenses/ASSET_PROVENANCE.csv`.
- Les assets **produits restent des créations originales** informées par cette cible (mêmes coques,
  palettes et silhouettes divergentes qu'aujourd'hui) : on transpose l'intention, on ne décalque pas
  une silhouette sous licence ni un logo/texte de marque.
- **Conséquence assumée** (revirement d'ADR-0005) : des images portant des marques tierces visibles
  entrent désormais dans l'historique git/LFS. Acceptable pour ce dépôt **local, personnel, non
  distribué** ; ce serait à revoir en cas de distribution.

## Conséquences

- La spec §0.2/§3 et CHARTE §5 (« interdits absolus ») sont **assouplies par cet ADR** pour ce projet
  personnel : elles restent le garde-fou par défaut, mais ne bloquent plus l'usage des références
  comme inspiration ni un rendu qui s'en rapproche. Renvois ajoutés dans `CLAUDE.md` (§Interdictions)
  et `CHARTE_CREATIVE.md §5`.
- `asset-forge` peut s'appuyer sur ces références pour les briefs de rendu, en produisant de l'original.
- Si le projet devait un jour être distribué ou commercialisé, **cet ADR serait à réviser** (le risque
  IP redeviendrait réel) : il faudrait alors purger `assets/reference/inspiration/` de l'arbre **et** de
  l'historique git/LFS (`git filter-repo` / purge LFS), pas un simple `git rm`.
