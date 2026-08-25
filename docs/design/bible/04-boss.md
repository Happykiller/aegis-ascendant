---
titre: Boss — phases, télégraphie, ce qui sépare un pattern d'un tirage au sort
type: reference
statut: actif
maj: 2026-08-25
---

# Boss

## Ce que le genre dit

### Un boss n'est pas un gros ennemi

> Les boss « présentent un défi d'une autre nature : tuer un gros ennemi **pièce par pièce**, ou
> survivre à des attaques difficiles à esquiver en entamant une grande barre de vie ».

### Chaque phase doit être distincte

Plus les attaques varient, mieux c'est — et beaucoup de jeux **découpent visuellement la barre de
vie** pour annoncer où le pattern courant s'arrêtera et où le suivant commencera. Le joueur sait
alors ce qu'il gagne en frappant.

### Des patterns, pas du chaos

> « Éviter les boss dont l'issue tient plus à la chance qu'à l'adresse : pensez patterns, pas chaos. »

Un pattern s'apprend ; un tirage au sort s'endure.

### Télégraphier, c'est enseigner

Chaque attaque doit être annoncée par un signal **reconnaissable**. Apprendre un boss, c'est
apprendre à **lire** ses annonces — sans elles, il n'y a rien à apprendre, seulement à mémoriser.

### Le boss appartient à son niveau

Des attaques sans rapport avec le thème du niveau font un boss **détaché**. La transition compte
autant que le combat.

## Chez nous — état au 2026-08-25

Deux boss, et ils illustrent bien deux des principes.

**Le Choir Harvester** (mini-boss) : carapace blindée tant que l'iris est fermé, avec un retour
explicite quand les tirs sont renvoyés (`deflected` → étincelle blanche et son de bouclier), parce
que « tirer dessus sans rien produire à l'écran se lit comme un défaut, pas comme une armure ». Son
ouverture est **le** moment du combat, et elle est annoncée par explosion, son et bannière
« NOYAU EXPOSE ».

**Le Pale Leviathan** (boss final) : trois cycles, chacun fait de deux phases — armure à démonter
plaque par plaque, puis plongée dans le noyau.

| Principe | État réel |
|---|---|
| Pièce par pièce | ✅ **Exactement ça.** Quatre plaques à abattre, et une de moins à chaque cycle : « le boss se répare de plus en plus mal » |
| Phases distinctes | ✅ Armure et plongée n'ont rien en commun — l'une se joue dehors, l'autre **dans une arène dédiée** (`ADR-0025`) |
| La barre annonce | ✅ **Corrigé le 2026-08-25** (`ADR-0023`). Le HUD recevait `structure_ratio()` — la cible courante, qui se remplit à chaque bascule — au lieu de `fight_ratio()` : six remplissages se lisaient comme une boucle. La mesure juste existait et n'allait qu'à la musique |
| Télégraphie | ✅ Chaque bascule est annoncée : bannière aux mots du design, secousse, son, changement musical |
| Patterns, pas chaos | ✅ **Garanti par construction** (`ADR-0026`) : aucun `flux_health` ne pouvait donner trois cycles, les dégâts par plongée allant de 600 à plus de 1200 pour le même joueur. On plafonne à un tiers par passage — trois cycles sont désormais **vrais par construction et non par calibrage** |
| Le boss appartient au niveau | ⚠️ **L'écart connu.** Ni l'armure démontable, ni la plongée, ni le flux n'ont été enseignés par les phases précédentes |

## L'écart, et ce qu'on en fait

Les boss sont la partie **la mieux tenue** du projet au regard du genre — et pour une raison qui
mérite d'être écrite : chacun de ces points a été **corrigé après un playtest**, pas conçu juste du
premier coup. `ADR-0019` (combat ramené de 3 min à 67 s), `ADR-0023` (la jauge qui bouclait),
`ADR-0024` (le flux dimensionné sur la mauvaise cadence), `ADR-0026` (le plafond) : quatre décisions,
quatre parties jouées.

**La leçon dépasse les boss** : sur ces questions, aucune mesure automatique n'a jamais rien vu. Le
combat « beaucoup beaucoup trop long » et la jauge « en boucle » ont été dits par l'opérateur en
jouant, avec zéro test rouge.

**Une seule piste ouverte** : le boss final n'enseigne rien avant de l'exiger. Elle ne se traite pas
au niveau du boss mais à celui de la progression du niveau — voir
[Niveau et rythme](03-niveau-et-rythme.md).
