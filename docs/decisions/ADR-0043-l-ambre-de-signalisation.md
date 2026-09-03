# ADR-0043 — L'ambre de signalisation entre dans la palette, et il est **ponctuel**

- **Statut** : accepté
- **Date** : 2026-09-03
- **Décision** : opérateur, sur la planche de la Citadelle de Défense
- **Amende** : la palette **80 / 15 / 5** (`2026-08-29-niveau-2-refonte-geometrie.md` §Palette), et la
  ligne `forbidden: "orange"` que portent les demandes de texture `TEX-0010` à `TEX-0014`
- **Contexte spec** : DA §6 (lisibilité), bible *Lisibilité*

## Contexte

La planche de la Citadelle porte une dizaine de **points lumineux orange chauds** au ras du pont,
disposés comme un balisage de piste. L'opérateur les valide et va plus loin :

> « je trouve que les lumières orange vont bien dans le décor telles des LED de signalement dans un
> env technologique, on pourrait même l'étendre au reste du long parcours »

Jusqu'ici, le niveau n'avait qu'**une** couleur fonctionnelle : le magenta de l'énergie. Toute
l'ambiance reposait dessus, et les cinq demandes de texture livrées interdisent explicitement
l'orange.

## La contrainte qui décide de la teinte

⚠️ **Le corail `#FF5A3D` est le tir ennemi** (`space_background.gdshader`, DA §6, règle 5 du contrat
de texture). Un décor qui l'emploie **vole leur lisibilité aux projectiles** — c'est la règle qui a
déjà coûté une itération sur le bolide d'impact (`ADR-0027`).

Un « orange » posé à l'œil atterrit à 10-20° de teinte du corail. Mesuré :

| | Teinte | Écart au corail |
|---|---|---|
| corail — **tir ennemi** | 9,0° | — |
| cyan — **tir allié** | 185,3° | 176° |
| magenta — artère | 323,5° | 314° |
| **ambre retenu `#FFA92B`** | **35,7°** | **26,7°** |

## Décision

**L'ambre `#FFA92B` entre dans la palette du Long Cortège comme couleur de SIGNALISATION**, distincte
du magenta d'énergie. Trois clauses, et aucune n'est négociable :

1. **Écart de teinte ≥ 25° avec le corail `#FF5A3D`**, mesuré et non jugé à l'œil. `#FFA92B` est à
   26,7°. Toute dérive vers le rouge la rapproche du tir ennemi ; toute dérive vers le jaune la
   rapproche de l'or `#E4B54A`, réservé au commandement (DA §5.1).
2. **Elle est PONCTUELLE, jamais surfacique.** Des points, des filets courts, des cabochons — dizaines
   de pixels, pas des mètres carrés. Elle ne prend **aucune part** des 80/15/5, qui reste le contrat
   des surfaces. ⚠️ Une LED qui s'étale cesse d'être un signal et devient un aplat : c'est exactement
   ce que la refonte a corrigé sur le magenta, et le même défaut se rejouerait en orange.
3. **Elle ne signale jamais une cible.** Le magenta dit « énergie, donc fonction, donc quelque chose
   à détruire ». L'ambre dit « repère technique » — balisage, seuil, circulation. Confondre les deux
   apprendrait au joueur à tirer sur du décor.

## Portée

- **Immédiate** : la Citadelle de Défense (plan du 2026-09-03), servie par `TEX-0016`.
- **Étendue au reste du Long Cortège** — c'est la demande de l'opérateur — mais **après** que la
  citadelle l'ait montrée en jeu. Une couleur neuve se juge sur un écran chargé, pas sur une planche.
- ⚠️ **Les demandes `TEX-0010` à `TEX-0014` gardent `forbidden: "orange"`** et ne sont pas
  régénérées : leurs surfaces ne sont pas de la signalétique. Seule une demande dont l'ambre est le
  **sujet** le retire de sa liste.

## Ce qui rouvrirait cette décision

Une capture en jeu, écran chargé, où l'ambre se confond avec un tir ennemi. C'est le seul test qui
compte, et il ne peut pas être fait avant que la citadelle existe.
