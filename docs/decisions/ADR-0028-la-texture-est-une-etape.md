# ADR-0028 — La texture est une étape du process, plus une permission

- **Date** : 2026-08-26
- **Statut** : accepté (demande du propriétaire : « on doit intégrer à notre processus de création
  les textures, c'est obligatoire, une grosse plus-value »)
- **Amende** : `ADR-0013` (qui autorisait sans instituer). Ne revient sur aucune de ses
  autorisations.
- **Applique** : `docs/forge/textures/README.md` (contrat), `docs/forge/BRIEF_TEMPLATE.md`,
  `docs/forge/CHARTE_CREATIVE.md` §6, `.claude/skills/asset-image/`, `.claude/agents/asset-forge.md`

## Contexte

La texture a une histoire en trois temps dans ce projet, et le troisième est resté inachevé.

| ADR | Ce qu'il a fait |
|---|---|
| `ADR-0008` | **Interdit** les textures : « le détail vient de la géométrie », PBR par facteurs |
| `ADR-0011` | **Autorise** les feuilles de détail répétables en niveaux de gris |
| `ADR-0013` | **Lève tous les interdits** : « on ne veut plus d'interdit sur les textures » |

⚠️ **`ADR-0013` a donné la permission et s'est arrêté là.** Il n'a institué aucune étape. Le
constat, fait le 2026-08-26 en cherchant où brancher la demande de textures du survol de lune :

- le mot « texture » n'apparaît **nulle part** dans `docs/forge/CHARTE_CREATIVE.md` ;
- il n'apparaît **nulle part** dans `docs/forge/BRIEF_TEMPLATE.md` ;
- il n'apparaît **nulle part** dans la définition de l'agent `asset-forge`.

Trois ADR sur le sujet, et le gabarit qui commande chaque production créative n'en dit pas un mot.

**La conséquence était visible et personne ne l'avait nommée.** `BRIEF-0085` a dû inventer sur le
moment un partage en trois mains — « l'opérateur génère les textures, la forge livre la géométrie et
les UV, le concepteur intègre » — et écrire en majuscules « ⚠️ **PAS DE TEXTURES** » à la forge pour
que la frontière tienne. Ce partage est bon ; le problème est qu'il a été réinventé dans un brief au
lieu d'être porté par le process. Le brief suivant l'aurait réinventé autrement, ou pas du tout.

⚠️ **Et un défaut totalement silencieux en découlait** : `ADR-0013` relève déjà que « la citadelle
n'a **aucune** texture possible : son `.glb` n'a ni UV ni tangentes ». Trois coques du dépôt sont
sorties sans `TEXCOORD_0`. Rien ne l'a signalé — ni erreur d'import, ni test rouge. Une coque sans
UV est une coque qu'aucune texture ne pourra jamais habiller, et on ne l'apprend qu'en essayant.

## Décision

**Tout brief d'asset porte une section `Texture` obligatoire, et les UV cessent d'être optionnelles.**

### 1. La porte : une section, deux issues, jamais de silence

Chaque `BRIEF-NNNN` porte une section **`## Texture`** qui tranche explicitement, et ne peut pas
être omise :

- **soit** elle nomme la ou les demandes dont l'asset dépend — `docs/forge/textures/TEX-NNNN-*.json` ;
- **soit** elle déclare qu'il n'en faut aucune, **et écrit pourquoi**.

⚠️ **L'absence de section vaut brief incomplet**, au même titre qu'un livrable sans chemin. Ce n'est
pas une case à cocher : c'est le moment où l'on décide si l'asset a une matière, et ce moment
n'existait pas.

### 2. Les UV et `TEXCOORD_0` deviennent non négociables

Tout maillage livré porte des UV et **compte** `TEXCOORD_0` dans le `.glb` — compté, pas supposé.
Un asset sans UV n'est pas « sans texture pour l'instant », c'est un asset **définitivement**
inhabitable sans reforge.

Le dépliage suit l'usage, et le brief le dit : projection en boîte pour une pièce vue de loin,
dépliage continu à densité de texels homogène pour une surface qui portera une carte de détail
(cf. `BRIEF-0085` §« Ce que ça change pour tes UV »).

### 3. Le contrat d'expression de besoin

Une demande de texture est un **fichier JSON normalisé**, une par fichier, au format de
`docs/forge/textures/README.md` : schéma fixe, six règles de validation, échelle monde déclarée
`measured` ou `decided`. Le JSON est le contrat **stable** ; le prompt en est **dérivé** et jetable.

Le skill `/asset-image` est l'étage de transformation : sa sortie est désormais un fichier
`TEX-NNNN`, plus un bloc de conversation.

### 4. Le partage en trois mains est institué

Ce que `BRIEF-0085` a inventé devient la règle :

| Qui | Quoi |
|---|---|
| **L'opérateur** | génère les images, hors du dépôt, et les dépose dans `assets/source/` |
| **La forge** | la géométrie et **les UV qui accueillent la texture** — jamais la texture elle-même |
| **Le concepteur** | rédige le `TEX-NNNN`, dérive les cartes, câble le matériau, mesure et intègre |

### 5. Ce qui ne change PAS

- **Aucune campagne de rattrapage.** Les 13 coques déjà livrées restent en l'état ; elles ne sont
  reprises qu'à l'occasion d'une **reforge**, jamais pour elles-mêmes. Arbitré par le propriétaire
  le 2026-08-26 contre les deux options plus larges.
- **Aucune autorisation d'`ADR-0013` n'est retirée.** Couleur motivée, jeux dédiés à une unité,
  décalques : toujours permis.
- **Le PBR par facteurs reste valide** là où la section `Texture` conclut qu'aucune carte n'est
  nécessaire — à condition que ce soit **écrit**, pas subi.
- **La réserve de couleurs prime toujours** : cyan `#3FD9E8` au tir allié, corail `#FF5A3D` au tir
  ennemi. Une texture qui les emploie vole leur lisibilité aux projectiles.

## Conséquences

**Ce que ça coûte** : une section de plus par brief, et des UV soignées là où une projection en
boîte suffisait. Le coût réel est sur les dépliages continus, qui demandent une planche de contrôle
(damier UV) — sans elle, un étirement ne se découvre qu'après la texture générée, donc trop tard.

**Ce que ça rapporte** : la « grosse plus-value » du propriétaire est un fait mesurable, pas un avis
— `ADR-0011` l'a établi sur les coques. Le détail géométrique se paie en triangles et en temps GPU ;
une carte de détail répétable le rend à coût quasi constant. Et à 960×540 après post-process rétro,
c'est la **fréquence spatiale** du grain qui fait la matière, pas le nombre de facettes.

**Le risque à surveiller** : la texture ne doit jamais faire avancer le décor au détriment du jeu.
Le critère qui tranche n'est pas la beauté de la surface mais une capture regardée — *le chasseur et
les balles se lisent-ils encore par-dessus ?* (`ADR-0006`). Une texture qui gagne le concours de
matière et fait perdre le vaisseau est à refaire, pas à ajuster.

**Effet de bord assumé** : le parc restera hétérogène un moment — des coques texturées à côté de
coques en aplats. C'est le prix de l'option retenue, et il est préféré à une campagne de reforge
dont plusieurs coques sortiraient sans UV de toute façon.
