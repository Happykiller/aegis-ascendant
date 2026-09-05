# Bonne pratique — une cote se lit sur l'asset livré, jamais sur ce qui l'a produit

## La famille

Trois façons, dans ce projet, de travailler sur une cote **fausse** tout en croyant l'avoir
vérifiée. Aucune ne lève d'erreur, aucune ne rougit un test : le nombre est plausible, il vient
d'une source qui a l'air autorisée, et il est faux.

Le réflexe commun : **la vérité d'une pièce est dans le binaire qu'on charge, pas dans le script
qui l'a écrit ni dans la constante qui la recopie.**

---

## 1. La table de forge donne l'INTENTION, le marqueur donne la POSITION

`build_long_cortege.py` déclare ses dix-sept tourelles dans une table `TURRETS` — station et
écart à l'axe. C'est ce que le script *demande*. Ce qu'il *pose* est autre chose : la géométrie
échantillonne la peau, se recale sur la chine, et le marqueur atterrit ailleurs.

Mesuré le 2026-09-05, en relisant `long_cortege.glb` :

| | table | marqueur livré | écart |
|---|---|---|---|
| `Turret_07` | x = 9,80 | **x = 12,05** | 2,25 m |
| `Turret_11` | x = 10,10 | **x = 12,40** | 2,30 m |
| `Turret_14` | x = −9,40 | **x = −10,75** | 1,35 m |
| `Turret_08` | x = −5,60 | **x = −6,74** | 1,14 m |

**Et quatre emplacements sortent des deux paliers de pont** — ils ne sont donc éligibles à rien
de ce qui hérite d'une assise. Une table de batteries entière a été générée sur les valeurs de la
table de forge avant qu'un test ne la refuse.

    # ✅ lire le binaire
    python3 -c "…"  # parcourir les nœuds de long_cortege.glb, cumuler les translations parentes

## 2. Une constante de moteur recopiée d'un asset périme EN SILENCE quand l'asset change

Le moteur assemble les pièces d'un kit à partir de cotes écrites dans son propre code
(`RING_LIFT`, `BODY_LIFT`, `BARREL_SEAT_Z`, `MUZZLE_REACH`…). Elles ont été mesurées un jour sur
un `.glb`, puis figées.

**Une reforge les périme toutes, sans une erreur.** `BRIEF-0100` en a périmé **onze** d'un coup :
sans mise à jour, le moteur posait un bloc 3 cm trop bas, des tubes 8 cm trop bas et 10 cm trop
en arrière, et l'appareillage 20 cm trop près de l'axe. Rien au journal, rien de rouge.

C'est la deuxième occurrence en deux jours : la veille, le recentrage vertical d'une coque
importée avait laissé les plumes 0,106 unité au-dessus des tuyères — 17 % de la hauteur du
vaisseau, trouvé par l'opérateur en jouant.

**Le remède** : quand une reforge est commandée, le brief exige la **table des cotes périmées**
au rapport. `BRIEF-0100` l'a fait, et c'est la seule raison pour laquelle les onze ont été
reposées le jour même.

## 3. Un harnais qui compose des cotes sans appliquer le FACTEUR D'ÉCHELLE mesure toujours la même pièce

`test_no_turret_ever_reaches_the_flight_plane` empile les boîtes englobantes des pièces du kit et
vérifie que le sommet passe sous le plafond de vol. Il était **vert**, et il l'est resté le jour
où une troisième classe de tourelle est née — parce qu'il n'appelait jamais `_geom_scale()`.

Il mesurait donc toujours la classe native. La classe lourde, elle, passait **0,75 m au-dessus du
plan de vol du joueur** sur trois emplacements. Trouvé par la mesure indépendante d'un sous-agent,
jamais par la suite de tests.

⚠️ **Et la borne à laquelle je m'étais fié était la mauvaise.** L'échelle avait été calée sur
l'**emprise au sol** (la plus large plateforme déclarée par le décor). La contrainte qui mord est
**en l'air** : entre l'assise la plus haute (−4,270) et le plafond des pièces de gameplay (−2,40)
il ne reste que **1,870 m**. Une cote plausible, tirée d'un raisonnement juste sur le mauvais axe.

    # ✅ un harnais d'échelle boucle sur les emplacements RÉELS et leur échelle RÉELLE
    for nom in seats:
        var facteur := ... # celui que le moteur appliquera vraiment
        assert(seats[nom] + hauteur * facteur <= plafond)

---

## Ce qui relie les trois

Un nombre juste **à sa source** devient faux dès qu'il traverse une frontière : forge → moteur,
asset → constante, pièce → harnais. Aucune de ces frontières ne lève d'erreur, parce qu'aucune
n'est un appel de fonction — ce sont des recopies.

**La règle** : à chaque frontière, ou bien on relit l'asset, ou bien on écrit le test qui compare
la copie à l'original. Il n'y a pas de troisième option, et « je l'ai vérifié la dernière fois »
n'en est pas une.
