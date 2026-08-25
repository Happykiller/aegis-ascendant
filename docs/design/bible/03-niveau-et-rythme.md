---
titre: Niveau et rythme — structure, introduction, respiration
type: reference
statut: actif
maj: 2026-08-25
---

# Niveau et rythme

## Ce que le genre dit

### Un niveau se construit comme une vague, en plus grand

Game Developer décrit une structure **fractale** : le niveau reprend la forme de ses propres vagues.
On pose un **thème**, puis :

1. **Ouvrir** sur une vague intéressante mais **pas difficile** — elle présente le thème et laisse
   pratiquer.
2. **Développer** — plus d'unités, des variantes, l'unité thématique maintenue pour que le joueur
   **détecte un motif commun**.
3. **Intensifier** — mélanger les mécaniques.
4. **Le mid-boss au milieu**, comme **climax récompensant la maîtrise** du mécanisme introduit.
5. **Ralentir avant la fin** — « donner un défi intéressant » qui construit l'élan et l'attente, et
   laisse **souffler** avant l'affrontement final.
6. **Le boss final résume tout ce qui a été appris.**

### Un mécanisme à la fois

Ne pas introduire plusieurs nouveautés en même temps. Chacune s'installe **avant** d'être combinée
aux précédentes.

### Garder le joueur occupé — mais varier l'intensité

Deux conseils qui se tiennent : « garder le joueur occupé en permanence », et **varier l'intensité**
— certaines phases doivent peser moins. Le repos n'est pas du vide : c'est ce qui rend le pic
lisible comme un pic.

### Des repères

Boghog parle de **landmark uniqueness** : un mid-boss, un événement de décor, un changement de fond.
Ce sont eux qui donnent au joueur une carte mentale du niveau.

### Le décor ne doit pas mentir

Une règle simple et coûteuse à découvrir tard : **rien dans le décor ne doit ressembler à un
obstacle** s'il n'en est pas un — ni l'inverse.

## Chez nous — état au 2026-08-25

L'arc du niveau 1, dans le vocabulaire de l'opérateur : **phase 1** (vagues de chasseurs, close par
le mini-boss) puis **phase 2** (le champ d'astéroïdes), avant le boss final et l'appontage.

| Étape du genre | Chez nous |
|---|---|
| Ouvrir doucement | ✅ `wave_graybox_01.tres` ouvre sur un V de Needle Scout à 0,3 s, quatre unités espacées de 0,7 s |
| Développer | ✅ La vague introduit ses familles par blocs — arcs, serpents, piqués, spirales, lanciers — sur ~50 s |
| Intensifier | ✅ Finale en tenaille : raiders des deux côtés, strafe, piqué central |
| Mid-boss au milieu | ⚠️ **Il est à la FIN de la phase 1**, pas au milieu du niveau. Le Choir Harvester clôt les vagues au lieu de couronner l'apprentissage d'un mécanisme |
| Ralentir avant la fin | ❌ **Non tenu.** Le boss final arrive après le champ d'astéroïdes, sans respiration |
| Le boss final résume | ⚠️ Partiellement : le Leviathan a ses propres mécaniques (plaques, plongée, flux) qui **n'ont pas été enseignées** par les phases précédentes |
| Un mécanisme à la fois | ✅ **Tenu par construction** dans le champ d'astéroïdes : trois colonnes de mines seules d'abord (« on apprend la mine avant d'en subir un rideau »), puis les puits, puis les sangsues, puis tout ensemble |
| Varier l'intensité | ✅ La phase 2 est conçue comme une **respiration** entre deux boss (`ADR-0027`), et sa musique le dit — Fortress Awakening à 108 BPM au lieu de Fleet Battle à 132 |
| Repères | ✅ Deux boss, un changement complet de décor à la phase 2, des bannières |
| Le décor ne ment pas | ⚠️ **Point de vigilance actif.** Au lot 2, un astéroïde décoratif frôlait le chasseur ; il a été écarté du couloir de vol. ⚠️ L'arbitrage « astéroïdes solides, lune décor » va **rouvrir exactement ce problème** : solides et décoratifs partageront le cadre |

## L'écart, et ce qu'on en fait

**Le plus net est la marche finale.** Le genre est explicite : on **ralentit avant le boss final**.
Chez nous, le champ d'astéroïdes se termine et le Leviathan arrive. La phase 2 fait déjà office de
respiration à l'échelle de l'arc — mais entre elle et le boss, il n'y a rien.

⚠️ C'est une piste, pas une correction : la durée de l'arc est déjà à sa cible (2-3 min de jeu), et
ajouter du temps mort peut coûter plus que ça ne rapporte. **À juger en jouant l'arc entier.**

**Le mid-boss mal placé est un faux problème** : notre « mid-boss » clôt la première section d'un
niveau qui en compte deux — il est donc *au milieu* de l'arc, ce qui est exactement sa fonction. Le
manque réel est ailleurs : il ne **couronne l'apprentissage de rien**, faute de mécanisme introduit
pendant la phase 1.

**Le boss final qui ne résume rien** est le vrai écart de fond, et il est structurel : le Leviathan
enseigne ses mécaniques pendant qu'on le combat. Rien à corriger tant que le combat tourne
(`ADR-0026` : trois cycles par construction, vérifié en partie) — mais c'est à savoir si un jour la
progression du niveau est retravaillée.
