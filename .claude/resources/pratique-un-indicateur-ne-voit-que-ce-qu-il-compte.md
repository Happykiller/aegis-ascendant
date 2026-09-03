# Pratique — un indicateur ne voit que ce qu'il compte

Le projet sait déjà qu'un indicateur maison se valide sur un **témoin connu**
([pratique-juger-une-image-en-la-mesurant](pratique-juger-une-image-en-la-mesurant.md)). Cette page
dit l'autre moitié du piège : un indicateur **juste le jour où il est écrit** devient faux tout seul
dès qu'on ajoute au monde une chose qu'il n'énumère pas. Il ne casse pas, il n'alerte pas — il
continue de rendre un chiffre plausible.

## Ce que ça a coûté, deux fois dans la même session (2026-09-02)

Les deux cas sont sur le même sujet — l'enrichissement géométrique du Long Cortège — et le second
est arrivé **après** que le premier eut été corrigé.

| | Ce que l'indicateur énumérait | Ce qu'on venait d'ajouter | Effet |
|---|---|---|---|
| Tableau des modules (lot B3) | une **liste blanche** de familles | une famille absente de la liste | la pièce existait, le tableau la comptait pour rien |
| Part de bordé **calme** (lot C1) | modules seedés + emprises d'installations | fosses, passerelle, bastions — ni l'un ni l'autre | jusqu'à **36 m** de bordé occupé, **zéro** mètre au compte |

Le second a fait annoncer à l'opérateur **58,6 %** de coque calme, puis **+8,3 points** de gain.
Le compte corrigé donnait **48,2 %** — c'est-à-dire **sous** les 50,3 % d'où le lot était parti — et
le gain réel du lot était de **+1,9 point**. Le détail de ce cas-là vit dans le code qui l'a subi
(`tools/blender/build_long_cortege.py`, la table des bastions) ; ce qui suit est ce qui se transporte.

## Le symptôme, et c'est le seul

> **Un chiffre qui n'a pas bougé alors qu'il aurait dû.**

C'est ce qui a trouvé les deux, et rien d'autre ne les aurait trouvés : les tests étaient verts, le
build déterministe, aucune erreur nulle part. Un indicateur aveugle n'échoue pas, il **rassure**.

Donc, en pratique :

- Après avoir ajouté une famille de pièces, **regarder d'abord le chiffre censé bouger**. S'il n'a
  pas bougé, ce n'est pas « l'ajout est négligeable » : c'est une hypothèse à réfuter avant toute
  autre.
- Se demander **par quoi** l'indicateur énumère : une liste blanche et un ensemble seedé sont les
  deux formes qui ont piégé ici. Les deux se réparent pareil — énumérer la **géométrie posée**,
  pas la liste de ce qu'on croyait poser.
- **Un chiffre annoncé à l'opérateur engage.** Les deux fois, la correction a dû être présentée
  comme un démenti d'un chiffre déjà donné. Vérifier l'indicateur **avant** de le citer coûte une
  minute ; le corriger après coûte la confiance dans tous les autres chiffres de la session.

## Ce que ça ne dit pas

Ça ne dit pas de tout recompter à chaque fois. Ça dit que **l'ajout d'une famille de pièces est
exactement le moment** où un indicateur d'occupation, de couverture ou de densité doit être relu —
c'est le seul instant où le défaut est bon marché à trouver.
