# ADR-0025 — On entre dans le noyau : la plongée devient une zone dédiée

- **Date** : 2026-08-25
- **Statut** : accepté (décision du propriétaire, après playtest)
- **Amende / supersede** : `ADR-0021` sur la **mise en scène** de la plongée uniquement. Les
  trois cycles, l'iris de tourelles, le dimensionnement (`ADR-0024`) et la jauge
  (`ADR-0023`) sont inchangés.

## Contexte

`ADR-0021` avait posé le bon geste — *entrer dans le noyau* — pour la bonne raison : le
joueur ne comprenait pas qu'il fallait tirer le cœur. Le playtest du 2026-08-25 dit que le
geste n'a jamais été livré :

> « Il y a un point qui n'est pas jouable : quand le noyau du boss s'ouvre et qu'on plonge.
> Déjà visuellement c'est moche, déjà on n'a pas la sensation que le noyau s'ouvre et qu'on
> rentre dedans — plus qu'il change, et qu'on perd de vue le vaisseau qui est dans la
> sphère. Ce n'est pas ce que j'entendais par rentrer dedans. »

Trois griefs, et le code les confirme **littéralement** :

| Grief | Ce que faisait le code |
|---|---|
| « ça change, ça ne s'ouvre pas » | `Shell_Ring` se **translate en Z** et **grossit de 18 %**. Aucun mécanisme, aucune pièce qui s'écarte |
| « on ne rentre nulle part » | La « chambre » était une `SphereMesh` de **7 m retournée**, bâtie au vol **autour du boss**. Le chasseur ne se déplaçait pas : on dessinait une bulle autour de tout |
| « on perd de vue le vaisseau » | La caméra glissait **à mi-chemin** du boss et y restait — ni le plan de jeu, ni un gros plan. Le chasseur était relevé de `plane_lift = 2.2` pour cesser de disparaître **derrière** sa propre cible ; un commentaire du code consignait déjà le symptôme |

### Ce que la conception avait prévu, et que personne n'avait à l'échelle

`BOSS_PALE_LEVIATHAN.md` **§6 — INTO THE MAW** décrivait déjà un puits vertical avec le cœur
au fond, et la coque **livre les pièces qui en portent les noms** : `Maw_Lip`, `Maw_Center`,
`Core_Center`, `Ring_01..05`, `Tunnel_End`, `Heart`. Aucune n'est référencée dans le jeu.

Mesurées dans le `.glb`, elles ne sont pas jouables :

| Pièce | Mesure |
|---|---|
| `Ring_01..05` — les anneaux « qu'on franchit » | **0,33 → 0,24 m** |
| `Heart` — le cœur du fond | **0,63 × 0,31 × 0,56 m** |
| `Specter-9` — le chasseur censé y passer | **1,29 × 0,65 × 2,41 m** |

⚠️ **Elles existent par le NOM, jamais à l'ÉCHELLE, et rien ne l'a signalé** : ni le compte
de triangles, ni le contrat d'export, ni le rendu. Un contrat de noms respecté n'est pas une
preuve que l'asset fait ce qu'il dit. C'est la leçon centrale de cet ADR.

## Décision

**La plongée bascule vers une ZONE DÉDIÉE** (`CoreInterior`), montée à l'origine du monde et
à l'échelle du plan de jeu (`GameplayPlane.BOUNDS`, 28 × 16 m).

1. **Le zoom d'entrée ne cadre plus la phase, il la couvre.** Il va jusqu'au bout de sa
   course, l'ouverture remplit l'écran, et **la bascule de lieu se fait derrière** — on ne
   voit pas la couture. C'est un rideau, pas un cadrage.
2. **Une fois dedans, la caméra reprend son cadrage NORMAL.** C'est le point décisif, et il
   découle de l'échelle : puisque l'arène fait la taille du plan de jeu, le cadrage habituel
   est le bon. Le grief « on perd de vue le vaisseau » disparaît par construction, et
   `plane_lift` — la rustine qui empêchait le chasseur de passer derrière sa cible — n'a
   plus d'objet.
3. **Le fond spatial et le corps du boss sont masqués.** On n'est plus dans l'espace, on est
   **dans** quelque chose. C'est la moitié de la sensation, et ça ne coûte rien.
4. **La cible suit le lieu** : `LeviathanCombat.dive_anchor` pose le flux sur le réacteur de
   l'arène. Le boss, lui, **reste dehors**.
5. **L'ouverture devient un mécanisme** : six volets qui reculent puis coulissent
   (`BRIEF-0083`), le geste **opposé** aux pétales du Choir Harvester — les deux boss ne
   doivent jamais se confondre.
6. **Le décor est un asset** (`BRIEF-0082`) : passerelle, réacteur central, parois, vu du
   dessus. Une **doublure procédurale** tient le rôle tant qu'il n'a pas livré, et le
   journal l'annonce à chaque montage.

## Conséquences

- ⚠️ **Le boss reste dehors pendant que le joueur est dedans.** C'est ce qui rendait
  `dive_anchor` indispensable : sans lui la cible restait au centre du corps du boss, donc
  hors de l'arène. On tirerait dans le vide — **sans erreur, sans test rouge, et sans que
  rien à l'écran le dise**. Trois tests le gardent.
- Le point de sortie est relevé **avant** l'autopilote : le relever une fois dedans
  mémoriserait le point d'aspiration et non l'endroit d'où le joueur est parti.
- Le fond est **restauré tel qu'il était**, pas « allumé » : `--no-backdrop` doit survivre à
  une plongée, sinon une mesure de silhouette se ferait sur deux images incomparables.
- Nouveau `tests/unit/test_core_interior.gd` : il ne vérifie pas le contrat de noms — il
  vérifie que **le réacteur et le point d'entrée tombent dans les bornes de jeu**. C'est
  précisément ce que le contrat de noms ne prouve pas, et ce que les anneaux à 30 cm ont
  démontré.

## Ce qui reste à juger

Rien de tout cela n'a été joué. La mécanique est vérifiable à l'arrêt ; **la sensation
d'entrer ne l'est pas**. À rejuger en jouant, une fois les deux assets intégrés.
