"""build_long_cortege.py — la coque du Long Cortege, en cinq troncons (BRIEF-0089).

    blender45 -b -P tools/blender/build_long_cortege.py
    blender45 -b -P tools/blender/build_long_cortege.py -- --plate
    ./scripts/build-hull.sh --check long_cortege      # + controle de determinisme

Produit `assets/imported/models/backgrounds/long_cortege.glb` et, avec `--plate`,
la planche de recette `docs/forge/output/BRIEF-0089-planche-sections.png`.

Le script EST la source de l'asset (ADR-0008) : aucun `.blend` versionne, aucun alea
non seede, deux executions successives rendent le meme sha256. Onze harnais de mesure
tournent a chaque build (plafond, jonctions, contrat de noms, marqueurs, UV, budgets,
largeur, couleurs reservees, textures, emissifs, orientation) et **tous echouent le
build** — voir `_audit()` et les `_assert_*`.


CE QUI DECIDE DE CE DECOR : 500 METRES POUR 90 000 TRIANGLES
============================================================
Le brief disait « ~34 unites par troncon ». Le concepteur a corrige avant la forge :
a 34 unites, la vitesse de defilement tombe a 0,8 u/s et un point fixe met 20 s a
traverser l'ecran — une derive, pas un survol. Les bonnes cotes sont **100 unites par
troncon**, soit 500 au total, a 2,4 u/s (6,7 s de traversee).

Cette correction change tout le metier de ce fichier. A 500 x 28 unites d'emprise,
90 000 triangles font **6,4 tri/m2**. Les reperes du depot :

    Pale Leviathan     195 tri/m2      coque de boss, vue de pres
    core_interior       36 tri/m2      arene de 30 x 18 m
    long_cortege       6,4 tri/m2      <- ici, trente fois moins que le boss

Une coque modelee piece par piece n'y entre pas. La reponse est donc un **vocabulaire
modulaire** — huit familles de pieces, instanciees le long du troncon avec des
variations seedees — et non un modelage unique :

    peau              le prisme, 34 points de profil x 20 stations par troncon
    plaques           `_surface_box`, 12 tri, posee sur une GRILLE de voies et de
                      cellules ; c'est elle qui porte le « borde fait de modules »
    nervures          bandeaux transversaux, six boites par nervure
    lisses            longerons de 60 a 90 m le long des chines
    greffes           blocs empiles, 3 a 5 boites, ce que le Cortege EMPORTE
    pastilles         les petits feux magenta des maquettes, 12 tri piece
    plateformes       les socles de tourelle (revolution)
    baies             les hexagones de pont d'envol (coaming + puits emissif)

Le detail percu vient des **textures** (LOT C du plan de niveau 2), pas des triangles.
C'est pour cela que le depliage compte davantage que le nombre de faces, et c'est
pour cela que ce fichier consacre plus de lignes a l'echelle des UV qu'a la peau.

⚠️ Le budget n'est pas rogne en silence : le total livre est imprime a chaque build,
par troncon, avec son pourcentage. Voir le compte-rendu pour le chiffre retenu et sa
justification.


CE QUE LE DEPLIAGE DOIT AU BRIEF, ET LA CONTRAINTE QUE PERSONNE N'AVAIT VUE
===========================================================================
Le brief demande `ak.box_project_uv()` pour le borde, echelle a annoncer en tuiles/m.
Mais les cinq troncons sont **cinq objets separes**, chacun deplie dans SON repere
local. La projection en boite ecrit `v = z_local * tuiles_par_metre` sur toutes les
faces dont la normale est dominante en X ou en Y — c'est-a-dire le pont et les flancs,
donc tout ce qu'on voit. A la jonction, le troncon amont finit a
`v = -L x tuiles_par_metre` et le troncon aval repart de `v = 0`.

    => si `L x tuiles_par_metre` n'est pas un ENTIER, la carte fait un saut de
       demi-tuile a chaque jonction, tous les 100 m, quatre fois dans le niveau.

D'ou la constante n'est pas « 0,2 tuile/m » mais **`HULL_TILES_PER_SECTION = 20`**,
dont on DEDUIT 0,20 tuile/m (5,00 m par tuile). Le chiffre est choisi dans la plage
du depot — `pale_leviathan` 0,18, `aegis_citadel` 0,12, `core_interior` 0,55 — du cote
grossier, parce que le Cortege est vu de loin et qu'il mesure un demi-kilometre.

Ambry, l'avant-poste humain, est deplie **plus fin** (0,70 tuile/m, 1,43 m par tuile)
comme le brief le demande : c'est une structure a l'echelle de la main, vue de plus
pres que le borde. Elle n'a pas de contrainte de jonction (elle ne touche aucun bord
de troncon), donc pas de contrainte d'entier.


LE PLAFOND Y = -3, ET POURQUOI IL DECIDE DE LA SILHOUETTE
=========================================================
Rien de la coque ne monte au-dessus de `Y = -3`. Ce n'est pas une marge de confort :
un volume qui franchirait ce plan masquerait le combat sans jamais pouvoir etre
touche. Le harnais est **bloquant** et il lit le `.glb` PRODUIT, translation comprise.

Consequence concrete, qui se voit sur la planche : la coque n'a que **0,62 m** entre
la crete de l'arete dorsale (-3,62) et le plafond. Tout le vocabulaire est donc
DE FAIBLE RELIEF — plaques a 0,22 m, nervures a 0,45, greffes a 1,0 au plus — et ce
qui donne du volume, c'est la **section transversale** : une crete centrale, un pont
interieur, une chine, un pont median, une facette exterieure, une epaule. Le decor se
lit par ses pentes, jamais par sa hauteur.

C'est aussi ce qui borne Ambry : son antenne s'arrete a -3,22, et c'est pourtant la
chose la plus haute des 500 m.


LES MARQUEURS SONT DES ENFANTS, ET C'EST DELIBERE
=================================================
Le brief dit « cinq nœuds racines, **sans enfants mailles** ». Le mot MAILLES fait le
partage : les trente points d'attache sont des Empties **parentes a leur troncon**.

La raison est mecanique. Le moteur fait defiler le decor en translatant les nœuds de
troncon (c'est ce que « chaque troncon porte sa translation » veut dire). Si les
tourelles etaient des racines a coordonnees absolues, elles resteraient sur place
pendant que la coque glisse dessous — un bug livre par la forge, invisible a
l'import. Enfants, elles suivent. `_audit()` verifie qu'aucun enfant ne porte de
maillage, et que les trente noms exacts sont la.


CE QUE CE SCRIPT N'UTILISE PAS DU KIT, ET POURQUOI
==================================================
`aegis_kit` est utilise SANS AUCUNE MODIFICATION, mais trois de ses fonctions sont
refaites ici. Ce n'est pas du confort, ce sont des incompatibilites de contrat,
verifiees dans le code du kit et deja documentees par `build_moon_flyby.py` :

  * `export_hull()` exporte **une** coque dont le nœud reste a l'origine ; ici chaque
    troncon porte une translation que le moteur relit. Son controle d'orientation
    compare le Y d'auteur des sommets LOCAUX au Z du glTF translation comprise : il
    n'est vrai que si le nœud est a l'origine. Il impose en outre un pivot centre a
    2 cm et une bbox largeur x longueur — deux notions sans objet pour un decor de
    500 m. Export et validation sont donc refaits ici, a l'identique sur le fond :
    meme correction d'axe, meme relecture du `.glb` PRODUIT, meme regle « au moindre
    ecart, on echoue ».
  * `new_object()` appelle `recalc_face_normals`. Les troncons 2 a 5 sont des tubes
    OUVERTS aux deux bouts (voir `_cap`) : sur une surface ouverte, l'heuristique de
    bmesh peut retourner toute la piece, et une coque a l'envers ne se voit sur
    aucune bbox. Le bobinage est donc pose a la main, et `_assert_outward()` le
    verifie face par face.
  * `cleanup()` fait la meme chose. `_weld()` ne soude que les doubles.

Le kit fournit le reste sans modification : `set_faction()`, `material()`,
`apply_material_slots()`, `mat_index()`, `add_lathe()`, `box_project_uv()`,
`srgb_hex_to_linear()`, `ContractError`.


REPERE DE TRAVAIL
=================
Tout ce fichier raisonne dans le repere **Godot** (X lateral, Y haut, Z profondeur,
« haut de l'ecran » = -Z), parce que c'est celui du brief, du code et des mesures.
La conversion vers le repere d'auteur de l'ADR-0008 se fait au dernier moment, dans
`_author()`, une seule fois par sommet ; composee avec la correction d'axe et le `yup`
de l'exporteur, elle rend l'identite (`_assert_axis_chain()`).

Le Cortege pointe vers **+Z** : la pointe de proue est a `z = 0`, la poupe des cinq
troncons livres a `z = -500`. Le troncon `n` occupe `z in [-100n, -100(n-1)]` et son
nœud porte `translation.z = -100 (n-1)`. La variable `s` employee partout est la
**distance depuis la pointe**, en metres : `s = -z_monde`.
"""

from __future__ import annotations

import json
import math
import os
import random
import struct
import sys
import tempfile

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "lib"))
_REPO = os.path.dirname(os.path.dirname(_HERE))

import aegis_kit as ak  # noqa: E402  (doit suivre l'ajout au sys.path)

OUTPUT = os.path.join(_REPO, "assets/imported/models/backgrounds/long_cortege.glb")
PLATE = os.path.join(_REPO, "docs/forge/output/BRIEF-0089-planche-sections.png")
FIGHTER = os.path.join(_REPO, "assets/imported/models/ships/specter_9.glb")

# ==========================================================================
# Cotes maitresses — repere GODOT (X lateral, Y haut, Z profondeur)
# ==========================================================================

#: Plafond absolu du decor. Rien ne monte au-dessus : ce serait un volume qui
#: masque le combat sans pouvoir etre touche. Harnais bloquant, `_audit()`.
CEILING_Y = -3.0
#: Marge que le script s'impose a lui-meme sur tout ce qu'il pose (0,20 m).
BUILD_CEILING_Y = -3.20

SECTION_COUNT = 5
#: ⚠️ 100 et non 34 : correction du concepteur du 2026-08-29, voir l'en-tete.
SECTION_LENGTH = 100.0
SHIP_LENGTH = SECTION_LENGTH * SECTION_COUNT      # 500 m
HALF_WIDTH = 14.0                                  # -> 28 m bord a bord

#: Budgets du brief. 18 000 x 5 = 90 000 : les deux bornes sont coherentes.
TRI_BUDGET_TOTAL = 90_000
TRI_BUDGET_SECTION = 18_000

#: ⚠️ On declare des TUILES PAR TRONCON, pas une densite. Voir l'en-tete : si
#: `SECTION_LENGTH x densite` n'est pas entier, la carte saute d'une demi-tuile a
#: chaque jonction. 20 tuiles sur 100 m = 0,20 tuile/m = 5,00 m par tuile.
HULL_TILES_PER_SECTION = 20
HULL_TEXELS_PER_METER = HULL_TILES_PER_SECTION / SECTION_LENGTH
#: Ambry est vue de plus pres : 1,43 m par tuile. Aucune contrainte d'entier (elle
#: ne touche aucun bord de troncon).
AMBRY_TEXELS_PER_METER = 0.70

# --------------------------------------------------------------------------
# LE HUITIEME SLOT — declare ICI, et pas dans le kit (BRIEF-0090)
# --------------------------------------------------------------------------
# Le kit fige SEPT slots (`ak.MATERIAL_ORDER`) et une seule faction par coque :
# `ak.material()` refuse tout nom hors de sa table et `set_faction()` refuse de
# melanger deux palettes. Sous la palette de l'Unisson, `AA_Hull` EST l'anthracite
# `#24252B` : Ambry, l'avant-poste HUMAIN, sortait donc de la matiere meme de ce
# qui l'a emporte, et son contraste ne tenait qu'a `AA_Trim` (2,29 pct de l'aire).
#
# ⚠️ ECART AU KIT, ASSUME ET ECRIT : ce fichier declare LOCALEMENT un huitieme
# materiau, sur le precedent de `build_moon_flyby.py` qui refait son export sans
# passer par `ak.export_hull()`. Le kit n'est PAS modifie — les sept slots gardent
# leurs index, le nouveau vient en huitieme position, et rien d'autre au depot ne
# le voit. La raison de ne pas l'y remonter : « une coque = une faction » est une
# bonne regle, et Ambry est le seul endroit du jeu ou une greffe humaine vit sur
# une coque ennemie. Une exception ne fait pas une regle de kit.
#
# La vraie raison technique du slot separe n'est pas la couleur, c'est L'ECHELLE :
# Ambry est depliee a 0,700 tuile/m quand le borde est a 0,200. Toute face d'Ambry
# qui resterait sur un slot du borde recevrait sa carte 3,5 fois trop fine.
AMBRY_HULL = "AA_Hull_Ambry"
#: Les 7 slots du kit, PUIS celui d'Ambry : aucun index du kit ne bouge.
MATERIAL_ORDER: tuple[str, ...] = ak.MATERIAL_ORDER + (AMBRY_HULL,)
#: Le gris-ivoire des coques Helios Vanguard, lu dans la palette du kit et non
#: recopie a la main : si la charte change, ce slot change avec elle.
AMBRY_HULL_HEX = ak.PALETTES[ak.FACTION_VANGUARD]["hull"]      # #EDEAE3

# --------------------------------------------------------------------------
# La section transversale — moitie tribord, de la crete a la quille
# --------------------------------------------------------------------------
# (x, y, materiau du segment qui part de ce point). Le dernier materiau est ignore.
# Lue sur les trois maquettes : crete centrale lumineuse, pont interieur, chine
# franche, pont median (ou vivent les baies), facette exterieure, epaule, bord.
#
# ⚠️ La crete culmine a -3,62 et non a -3,40 : il faut laisser passer les bulbes de
# l'arete dorsale (+0,40) SOUS le plafond de construction -3,20. Le decor a
# 0,62 m de relief utile, tout le vocabulaire en decoule.

# ⚠️ La repartition des materiaux a ete REFAITE apres le premier rendu, et c'est
# la correction la plus lourde du chantier. Premiere version : crete ivoire sur
# 1,64 m, arete lumineuse de 0,52 m, lisse d'epaule ivoire sur 500 m. A la
# perspective du jeu, le Cortege lisait comme une piste d'aeroport — trois rubans
# blancs et un neon magenta plein cadre — quand les trois maquettes montrent une
# masse anthracite ou l'ivoire et le magenta sont RARES. La lecon vaut au-dela de
# ce fichier : sur 500 m, un materiau clair applique a une arete CONTINUE occupe
# plus de pixels qu'une piece entiere, et le compte de triangles ne le dit pas.
PROFILE: tuple[tuple[float, float, str], ...] = (
    (0.00, -3.62, "AA_Emissive_Engine"),   # 0  la ligne lumineuse : 0,28 m au TOTAL
    (0.14, -3.63, "AA_Trim"),              # 1  son liseré ivoire, 0,64 m
    (0.46, -3.68, "AA_Greeble"),           # 2  dessus de crete, sombre
    (0.95, -3.78, "AA_Hull"),              # 3  epaule de crete
    (1.28, -4.06, "AA_Greeble"),           # 4  flanc de crete, dans l'ombre
    (1.62, -4.21, "AA_Hull"),              # 5  pied de crete
    (2.20, -4.26, "AA_Hull"),              # 6  pont interieur
    (5.10, -4.30, "AA_Hull"),              # 7  pont interieur
    (6.80, -4.34, "AA_Greeble"),           # 8  levre de chine
    (7.35, -4.94, "AA_Hull"),              # 9  pont median (les baies)
    (10.30, -4.99, "AA_Hull"),             # 10 pont median
    (12.35, -5.10, "AA_Panel"),            # 11 facette exterieure
    (13.35, -6.35, "AA_Panel"),            # 12 facette exterieure
    (13.88, -7.65, "AA_Hull"),             # 13 lisse d'epaule
    (14.00, -8.95, "AA_Greeble"),          # 14 BORD — 14,00 exactement
    (13.30, -10.60, "AA_Greeble"),         # 15 sous-chine
    (10.40, -11.90, "AA_Greeble"),         # 16 pente de fond
    (5.00, -12.40, "AA_Greeble"),          # 17 fond
    (0.00, -12.60, "AA_Greeble"),          # 18 quille
)
#: Indice du dernier point de la moitie SUPERIEURE (le bord, x = 14).
DECK_LAST = 14
#: Pivot vertical du fuseau de proue : la section se contracte autour de lui.
Y_PIVOT = -6.9

#: Bandes plates ou l'on a le droit de poser une plateforme de tourelle ou une
#: plaque : (x_min, x_max) en valeur absolue.
BAND_INNER = (2.30, 6.60)
BAND_MID = (7.50, 12.10)

# --------------------------------------------------------------------------
# Le fuseau de proue — troncon 1 seulement
# --------------------------------------------------------------------------
# (s, echelle laterale, echelle verticale), interpole en smoothstep. Le dernier
# nœud est a s = 88 avec (1, 1) : la derivee d'un smoothstep y est NULLE, donc le
# profil est deja plat 12 m avant la jonction a s = 100. C'est ce qui rend la
# jonction 1-2 invisible ET ce qui autorise l'egalite exacte des deux anneaux.
TAPER: tuple[tuple[float, float, float], ...] = (
    (0.0, 0.008, 0.16),
    (5.0, 0.100, 0.26),
    (58.0, 0.940, 0.93),
    (88.0, 1.000, 1.00),
)
TAPER_END = TAPER[-1][0]

# --------------------------------------------------------------------------
# Les marqueurs — poses A LA MAIN, jamais tires au sort
# --------------------------------------------------------------------------
# Le jeu instancie ses propres scenes dessus (tourelles, ponts d'envol, nœuds
# d'arete) comme `CitadelLife` le fait pour l'Aegis Citadel. Une position de
# gameplay ne se seede pas : elle se decide, elle se relit et elle se corrige.
#
# `s` = distance depuis la pointe de proue ; `x` = lateral (+ = tribord).

#: 17 tourelles, densite croissante : 2, 3, 3, 4, 5 du troncon 1 au 5.
#: Jamais sur l'axe (|x| >= 5,4), toujours sur une bande plate.
TURRETS: tuple[tuple[float, float], ...] = (
    (68.0, -6.00), (84.0, 9.40),                                    # troncon 1
    (118.0, 9.60), (140.0, -9.20), (176.0, 5.60),                   # troncon 2
    (214.0, -8.40), (246.0, 9.80), (278.0, -5.60),                  # troncon 3
    (312.0, 8.20), (336.0, -9.80), (360.0, 10.10), (386.0, -6.20),  # troncon 4
    (410.0, 8.80), (428.0, -9.40), (452.0, -6.00),                  # troncon 5
    (470.0, -10.20), (488.0, 9.00),
)
#: Rayon hors-tout de la plateforme, par troncon : « de plus en plus massives »
#: (maquette 3). 2,30 m a la proue, 3,20 m au troncon 5.
PAD_RADIUS = (2.30, 2.55, 2.75, 3.00, 3.20)

#: 7 baies hexagonales, vers l'exterieur (pont median + facette).
BAYS: tuple[tuple[float, float], ...] = (
    (86.0, 9.00),                                                   # troncon 1
    (126.0, -9.20), (182.0, 9.20),                                  # troncon 2
    (228.0, -9.30), (290.0, 9.30),                                  # troncon 3
    (348.0, -9.30),                                                 # troncon 4
    (436.0, -9.30),                                                 # troncon 5
)

#: 5 bulbes d'arete dorsale, exactement un par troncon, sur l'axe.
SPINES: tuple[float, ...] = (50.0, 150.0, 250.0, 350.0, 450.0)

#: Ambry : l'avant-poste humain greffe sur le borde tribord du troncon 5.
AMBRY_S = (446.0, 474.0)      # de la proue vers la poupe
AMBRY_X = (7.60, 13.60)
#: Le radeau. ⚠️ Sa hauteur n'est pas un gout : le pont median est a -4,95 et le
#: plafond de construction a -3,20 ; il reste 1,75 m. Le radeau en prend 0,36 et
#: laisse 1,28 m d'elevation a un avant-poste de quatre-vingts personnes. C'est
#: peu, et c'est pourtant la plus haute chose des 500 m.
AMBRY_RAFT_Y = -4.48
AMBRY_RAFT_THICK = 0.36
#: Zone interdite aux modules seedes du troncon 5 : sans elle, une greffe de
#: l'Unisson traverserait le radeau par en dessous.
AMBRY_KEEPOUT_X = (6.90, 14.10)
AMBRY_KEEPOUT_S = (443.5, 476.5)

#: Distance minimale entre un module et un plan de jonction. En dessous, un module
#: poserait des sommets sur le plan et `_assert_joints()` ne pourrait plus comparer
#: les deux anneaux de peau.
JOINT_CLEARANCE = 1.5

#: Couleurs reservees aux TIRS (charte SS3) : interdites sur cette coque.
FORBIDDEN_HEX = ("#3FD9E8", "#FF5A3D")


#: Origine du troncon en cours de construction, en `s`. ⚠️ TOUT le vocabulaire
#: raisonne en `s` GLOBAL (distance depuis la pointe de proue), parce que c'est
#: `s` qui donne la forme de la section a travers le fuseau de proue. Mais les
#: sommets doivent sortir en coordonnees LOCALES au troncon, puisque c'est le nœud
#: qui porte la translation. `_z()` fait la conversion, en un seul endroit.
#: Le defaut a ete paye : les cinq familles de modules ecrivaient `-s` directement,
#: si bien que le troncon 5 posait ses plaques 400 m derriere lui — le `.glb` etait
#: parfaitement valide, la bbox de chaque troncon faisait cinq fois la bonne
#: longueur, et rien d'autre que le harnais de jonction ne l'a vu.
_ORIGIN = 0.0


def _z(s: float) -> float:
    """`s` global (depuis la proue) -> z LOCAL au troncon en cours."""
    return -(s - _ORIGIN)


def _smoothstep(t: float) -> float:
    t = min(1.0, max(0.0, t))
    return t * t * (3.0 - 2.0 * t)


def _scales(s: float) -> tuple[float, float]:
    """Echelles laterale et verticale de la section a la station `s`."""
    if s >= TAPER_END:
        return 1.0, 1.0
    for (s0, kx0, ky0), (s1, kx1, ky1) in zip(TAPER, TAPER[1:]):
        if s <= s1:
            t = _smoothstep((s - s0) / (s1 - s0))
            return kx0 + (kx1 - kx0) * t, ky0 + (ky1 - ky0) * t
    return 1.0, 1.0


def _half_profile(s: float) -> list[tuple[float, float]]:
    kx, ky = _scales(s)
    return [(px * kx, Y_PIVOT + (py - Y_PIVOT) * ky) for px, py, _ in PROFILE]


def _half_width(s: float) -> float:
    return HALF_WIDTH * _scales(s)[0]


def _surface_y(s: float, x: float) -> float:
    """Hauteur du DESSUS de la coque a la station `s`, au lateral `x`.

    C'est la fonction que tout le vocabulaire modulaire interroge : une plaque, une
    nervure ou un socle prend sa base ici, coin par coin. C'est ce qui lui permet
    d'epouser la chine et la facette sans une seule rotation ecrite a la main.
    """
    half = _half_profile(s)[: DECK_LAST + 1]
    ax = abs(x)
    if ax >= half[-1][0]:
        return half[-1][1]
    for (x0, y0), (x1, y1) in zip(half, half[1:]):
        if ax <= x1:
            if x1 - x0 < 1e-9:
                return y1
            t = (ax - x0) / (x1 - x0)
            return y0 + (y1 - y0) * t
    return half[-1][1]


def _ring(s: float) -> list[tuple[float, float]]:
    """Anneau ferme de 34 points, tribord puis babord."""
    half = _half_profile(s)
    return half + [(-x, y) for x, y in reversed(half[1:-1])]


def _ring_materials() -> list[str]:
    """Materiau du segment `i -> i+1` de l'anneau ferme."""
    n = len(PROFILE)
    mats = [PROFILE[i][2] for i in range(n - 1)]          # 0..16, tribord
    mats += [PROFILE[2 * n - 3 - i][2] for i in range(n - 1, 2 * n - 2)]
    return mats


RING_MATERIALS = _ring_materials()
RING_SIZE = 2 * len(PROFILE) - 2


# ==========================================================================
# Primitives locales — bobinage pose a la main (voir l'en-tete)
# ==========================================================================


def _ambry_material() -> bpy.types.Material:
    """Le materiau propre a Ambry — COPIE d'`AA_Hull`, recolorise en Vanguard.

    Une copie et non une declaration a la main : `AA_Hull` porte deja le rendu
    d'une coque du kit (metallic 0,05, roughness 0,45 — une tole PEINTE, quand
    `AA_Trim` est a 0,85/0,28, une carapace POLIE). Ambry doit sortir de la meme
    famille de surface que les coques d'Helios Vanguard, pas de la carapace de
    l'Unisson : la difference de speculaire est un quatrieme signal, gratuit et
    independant de toute texture, apres l'orthogonalite, la valeur et l'absence
    de magenta.

    ⚠️ Memoise par le nom, comme `ak.material()` : deux appels rendent le meme
    datablock, sans quoi les cinq troncons porteraient cinq materiaux differents
    et l'exporteur en sortirait cinq copies.
    """
    existing = bpy.data.materials.get(AMBRY_HULL)
    if existing is not None:
        return existing
    mat = ak.material("AA_Hull").copy()
    mat.name = AMBRY_HULL
    color = ak.srgb_hex_to_linear(AMBRY_HULL_HEX)
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = color
    mat.diffuse_color = color
    return mat


def _mat_index(name: str) -> int:
    """Index de slot dans `MATERIAL_ORDER` — les 7 du kit, plus Ambry.

    Remplace `ak.mat_index()`, qui ne connait que les sept. Les sept gardent
    exactement leur index : seul le huitieme est nouveau.
    """
    try:
        return MATERIAL_ORDER.index(name)
    except ValueError as exc:
        raise ak.ContractError(
            f"materiau inconnu de ce decor : {name!r} "
            f"(attendus : {list(MATERIAL_ORDER)})") from exc


def _new_object(name: str, bm: bmesh.types.BMesh) -> bpy.types.Object:
    """Objet a 8 slots (les 7 du kit + celui d'Ambry), SANS `recalc_face_normals`.

    ⚠️ Difference volontaire avec `ak.new_object()`. Les troncons 2 a 5 sont des
    tubes ouverts aux deux bouts : l'heuristique de bmesh peut y retourner toute la
    piece, et une coque a l'envers ne se voit sur aucune bounding box. Le bobinage
    est pose a la main partout, et `_assert_outward()` le verifie.
    """
    mesh = bpy.data.meshes.new(name)
    ak.apply_material_slots(mesh)
    # ⚠️ APRES le kit, jamais avant : `apply_material_slots()` refuse d'ecraser
    # des slots existants, et un `materials.clear()` remettrait a zero le
    # `material_index` de TOUS les polygones, en silence. Les cinq troncons
    # portent les huit slots meme si quatre d'entre eux n'utilisent pas le
    # huitieme : ainsi la fusion d'Ambry dans le troncon 5 n'a aucun index a
    # remapper, et `_mat_index()` reste vrai partout.
    mesh.materials.append(_ambry_material())
    if [m.name for m in mesh.materials] != list(MATERIAL_ORDER):
        raise ak.ContractError(
            f"{name} : slots {[m.name for m in mesh.materials]} au lieu de "
            f"{list(MATERIAL_ORDER)}")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _weld(obj: bpy.types.Object, dist: float = 1e-5) -> None:
    """Soude les doubles. Ne touche PAS aux normales (voir `_new_object`)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=dist)
    bm.to_mesh(obj.data)
    bm.free()


def _face(bm: bmesh.types.BMesh, verts: list, material: str):
    clean: list = []
    for v in verts:
        if v not in clean:
            clean.append(v)
    if len(clean) < 3:
        return None
    try:
        face = bm.faces.new(clean)
    except ValueError:
        return None
    face.material_index = _mat_index(material)
    return face


def _bridge(bm: bmesh.types.BMesh, front: list, back: list,
            materials: list[str]) -> None:
    """Relie deux anneaux fermes, `front` a plus grand Z que `back`.

    Le sens (front -> back) EST ce qui rend les normales sortantes ; il est verifie
    analytiquement dans le commentaire de `_assert_outward()`.
    """
    n = len(front)
    for i in range(n):
        j = (i + 1) % n
        _face(bm, [front[i], front[j], back[j], back[i]], materials[i])


def _cap(bm: bmesh.types.BMesh, ring: list, material: str, facing_front: bool):
    """Ferme un anneau. `facing_front` : la normale regarde +Z."""
    order = list(reversed(ring)) if facing_front else list(ring)
    return _face(bm, order, material)


def _quad(bm: bmesh.types.BMesh, a, b, c, d, material: str):
    return _face(bm, [a, b, c, d], material)


def _box_from_corners(bm: bmesh.types.BMesh,
                      bottom: list[Vector], top: list[Vector],
                      side_material: str, top_material: str) -> None:
    """Boite a 8 sommets libres. `bottom`/`top` dans l'ordre (x0z0, x1z0, x1z1, x0z1)
    avec x1 > x0 et z1 < z0 : cet ordre rend la face du dessus normale +Y."""
    bv = [bm.verts.new(v) for v in bottom]
    tv = [bm.verts.new(v) for v in top]
    _face(bm, tv, top_material)
    _face(bm, list(reversed(bv)), side_material)
    for i in range(4):
        j = (i + 1) % 4
        _quad(bm, bv[i], bv[j], tv[j], tv[i], side_material)


def _surface_box(bm: bmesh.types.BMesh, x0: float, x1: float,
                 s0: float, s1: float, rise: float, sink: float,
                 side_material: str, top_material: str,
                 draft: float = 0.0) -> float:
    """LA primitive du vocabulaire : une plaque posee SUR la surface de coque.

    Chaque coin prend sa propre hauteur dans `_surface_y`, si bien que la meme
    fonction produit une plaque de pont, une nervure qui franchit la chine et un
    contrefort couche sur la facette exterieure — sans une seule rotation ecrite.

    `sink` enterre la face du dessous DANS la coque : elle n'est jamais vue et
    aucune face coplanaire ne peut donc scintiller contre le pont.
    `draft` retreint la face du dessus : ce sont ces flancs en depouille qui
    accrochent la lumiere rasante et font lire les plaques a 20 deg de la verticale.

    Retourne le Y du dessus (le plus haut des quatre coins).
    """
    # (x, s) dans l'ordre qui rend la face du dessus normale +Y : x croissant
    # d'abord, puis z decroissant (z = -s, donc s croissant).
    plan = ((x0, s0), (x1, s0), (x1, s1), (x0, s1))
    inner = ((x0 + draft, s0 + draft), (x1 - draft, s0 + draft),
             (x1 - draft, s1 - draft), (x0 + draft, s1 - draft))
    ys = [_surface_y(s, x) for x, s in plan]
    top_y = min(ys) + rise
    bottom_y = min(ys) - sink
    bottom = [Vector((x, bottom_y, _z(s))) for x, s in plan]
    top = [Vector((x, top_y, _z(s))) for x, s in inner]
    _box_from_corners(bm, bottom, top, side_material, top_material)
    return top_y


def _lathe(bm: bmesh.types.BMesh, cx: float, cs: float,
           contour: list[tuple[float, float, str]], segments: int) -> None:
    """Solide de revolution autour de l'axe vertical passant par (cx, -cs).

    `contour` : (y, rayon, materiau du segment montant). Un rayon nul est un pole.
    Meme convention que `ak.add_lathe(axis="Y")`, refaite ici pour poser les
    materiaux segment par segment et garantir le bobinage sortant.
    """
    cz = _z(cs)
    rings: list = []
    for y, r, _ in contour:
        if r <= 1e-6:
            rings.append(bm.verts.new(Vector((cx, y, cz))))
            continue
        pts = []
        for k in range(segments):
            a = 2.0 * math.pi * k / segments
            pts.append(bm.verts.new(
                Vector((cx + r * math.cos(a), y, cz + r * math.sin(a)))))
        rings.append(pts)
    for i in range(len(contour) - 1):
        material = contour[i][2]
        low, high = rings[i], rings[i + 1]
        if isinstance(low, list) and isinstance(high, list):
            for k in range(segments):
                m = (k + 1) % segments
                _quad(bm, low[k], high[k], high[m], low[m], material)
        elif isinstance(high, bmesh.types.BMVert) and isinstance(low, list):
            for k in range(segments):
                m = (k + 1) % segments
                _face(bm, [low[k], high, low[m]], material)
        elif isinstance(low, bmesh.types.BMVert) and isinstance(high, list):
            for k in range(segments):
                m = (k + 1) % segments
                _face(bm, [high[m], low, high[k]], material)


# ==========================================================================
# La peau — le prisme et son fuseau de proue
# ==========================================================================


def _stations(index: int) -> list[float]:
    """Stations (en `s` global) du troncon `index` (0-base), proue -> poupe."""
    s0 = index * SECTION_LENGTH
    s1 = s0 + SECTION_LENGTH
    if index > 0:
        steps = 20                       # 5,00 m : le profil y est constant
        return [s0 + (s1 - s0) * k / steps for k in range(steps + 1)]
    # Troncon 1 : le fuseau demande de la finesse la ou il tourne.
    values = [0.0, 0.8, 1.8, 3.0, 4.2]
    v = 6.0
    while v < 58.0 - 1e-6:
        values.append(v)
        v += 3.0
    v = 58.0
    while v < TAPER_END - 1e-6:
        values.append(v)
        v += 3.75
    values.append(TAPER_END)
    values += [91.0, 94.0, 97.0, 100.0]
    return values


def build_skin(bm: bmesh.types.BMesh, index: int) -> None:
    """Le prisme du troncon, en coordonnees LOCALES (z de 0 a -100)."""
    rings: list[list] = []
    for s in _stations(index):
        ring = [bm.verts.new(Vector((x, y, _z(s)))) for x, y in _ring(s)]
        rings.append(ring)
    for front, back in zip(rings, rings[1:]):
        _bridge(bm, front, back, RING_MATERIALS)
    if index == 0:
        # La pointe : 22 cm de large, fermee pour que la proue ne soit pas un tube.
        _cap(bm, rings[0], "AA_Trim", facing_front=True)
    if index == SECTION_COUNT - 1:
        # La coupe de poupe : les troncons 6 et 7 appartiennent au niveau 3, mais
        # ce bord-la EST vu a la fin du niveau. On le ferme.
        _cap(bm, rings[-1], "AA_Greeble", facing_front=False)


# ==========================================================================
# Le vocabulaire modulaire
# ==========================================================================


def _clip_lane(s: float, x0: float, x1: float,
               minimum: float = 0.9) -> tuple[float, float] | None:
    """Rabat une voie sur la demi-largeur reelle a la station `s` (fuseau).

    ⚠️ `minimum` n'a pas de valeur unique. Il a d'abord ete cable a 0,9 m, ce qui
    a fait DISPARAITRE EN SILENCE les lisses (0,36 m de large) et les 400
    pastilles (0,56 m) : le build restait vert, le contrat aussi, et seul le
    compte de modules imprime a chaque build a montre deux colonnes a zero.
    C'est pourquoi ce compte est imprime.
    """
    limit = _half_width(s) - 0.45
    lo, hi = x0, x1
    if lo < -limit:
        lo = -limit
    if hi > limit:
        hi = limit
    if hi - lo < minimum:
        return None
    return lo, hi


def _ambry_clash(s0: float, s1: float, x0: float, x1: float) -> bool:
    """Le module (s0..s1, x0..x1) mord-il l'emprise d'Ambry ?

    Sans ce garde-fou, une greffe seedee du troncon 5 traverserait le radeau par
    en dessous : Ambry est POSEE sur le borde, elle n'est pas encastree dedans.
    """
    return not (s1 < AMBRY_KEEPOUT_S[0] or s0 > AMBRY_KEEPOUT_S[1]
                or x1 < AMBRY_KEEPOUT_X[0] or x0 > AMBRY_KEEPOUT_X[1])


#: Voies de plaques : (x_min, x_max) en absolu, sur les deux bandes plates.
PLATE_LANES = ((2.35, 3.95), (4.05, 5.35), (5.45, 6.55),
               (7.55, 8.95), (9.05, 10.35), (10.45, 11.60))


def build_plates(bm: bmesh.types.BMesh, index: int, rng: random.Random) -> int:
    """Le champ de plaques : une GRILLE de voies x cellules, semee de variations.

    C'est la piece la plus rentable du fichier — 12 triangles pour une arete vive,
    une depouille eclairee et une ombre portee par la seule orientation des faces.
    Elle porte a elle seule le « borde fait de modules qui se repetent » des trois
    maquettes ; les joints, les rivets et l'usure viendront de la texture.
    """
    origin = index * SECTION_LENGTH
    cell = 3.2
    count = 0
    for side in (1.0, -1.0):
        for lane_index, (a, b) in enumerate(PLATE_LANES):
            k = 0
            s = origin + 1.9 + lane_index * 0.7
            while s + cell < origin + SECTION_LENGTH - 1.9:
                k += 1
                length = cell * rng.choice((0.55, 0.7, 0.7, 0.85, 1.0))
                roll = rng.random()
                if roll < 0.26:
                    s += cell
                    continue
                lane = _clip_lane(s, side * b, side * a) if side < 0 else \
                    _clip_lane(s, side * a, side * b)
                if lane is None:
                    s += cell
                    continue
                x0, x1 = lane
                if _ambry_clash(s, s + length, min(x0, x1), max(x0, x1)):
                    s += cell
                    continue
                inset = rng.uniform(0.06, 0.20)
                rise = 0.14 if roll < 0.62 else 0.22
                # 12 pct de violet et non 20 : au premier rendu, une plaque sur
                # cinq en `AA_Panel` faisait un confetti visible d'un bout a
                # l'autre du troncon.
                material = "AA_Hull" if roll < 0.88 else "AA_Panel"
                _surface_box(bm, x0 + inset, x1 - inset, s, s + length,
                             rise, 0.55, "AA_Greeble", material, draft=0.055)
                count += 1
                s += cell
    return count


def build_ribs(bm: bmesh.types.BMesh, index: int, rng: random.Random) -> int:
    """Nervures transversales : ce qui donne au Cortege sa segmentation.

    Six boites par nervure (crete, pont interieur, pont median, facette — en
    miroir). Chacune epouse sa bande par `_surface_box`, y compris la facette
    exterieure inclinee a 51 deg.
    """
    origin = index * SECTION_LENGTH
    spans = ((1.75, 6.60), (7.50, 12.10), (12.45, 13.85))
    count = 0
    # Le nombre varie d'un troncon a l'autre : sinon les cinq vues de dessus sont
    # des copies, la peau etant identique de la section 2 a la 5.
    ribs = (6, 7, 8, 7, 9)[index]
    for k in range(ribs):
        s = origin + JOINT_CLEARANCE + 3.0 + (SECTION_LENGTH - 12.0) * k / (ribs - 1)
        s += rng.uniform(-1.4, 1.4)
        width = rng.uniform(0.85, 1.45)
        rise = 0.45 if k % 2 == 0 else 0.32
        # ⚠️ Une nervure sur trois seulement recoit l'ivoire. Toutes en `AA_Trim`,
        # elles lisaient comme des passages pietons en travers de la coque.
        top = "AA_Trim" if k % 3 == 1 else "AA_Hull"
        for side in (1.0, -1.0):
            for a, b in spans:
                lane = _clip_lane(s, min(side * a, side * b), max(side * a, side * b))
                if lane is None or _ambry_clash(s, s + width, lane[0], lane[1]):
                    continue
                _surface_box(bm, lane[0], lane[1], s, s + width,
                             rise, 0.60, "AA_Greeble", top, draft=0.10)
                count += 1
    return count


def build_strakes(bm: bmesh.types.BMesh, index: int) -> int:
    """Lisses longitudinales : de longues aretes qui filent avec le defilement.

    Elles coutent 12 triangles pour 80 m et sont la seule chose du decor qui donne
    au joueur une lecture CONTINUE de sa vitesse — une plaque isolee ne la donne pas.
    """
    origin = index * SECTION_LENGTH
    s0 = origin + JOINT_CLEARANCE + 1.0
    s1 = origin + SECTION_LENGTH - JOINT_CLEARANCE - 1.0
    count = 0
    for side in (1.0, -1.0):
        # ⚠️ UNE SEULE des trois lisses est claire. Une lisse fait 97 m de long :
        # trois lignes ivoire par flanc, c'etait six rubans blancs d'un bout a
        # l'autre du vaisseau.
        for a, b, rise, material in ((6.62, 6.98, 0.16, "AA_Trim"),
                                     (12.15, 12.45, 0.14, "AA_Hull"),
                                     (1.66, 2.02, 0.12, "AA_Greeble")):
            lane = _clip_lane(s1, min(side * a, side * b), max(side * a, side * b),
                              minimum=0.25)
            if lane is None:
                continue
            start = s0
            if index == 0:
                # Sur le fuseau, la lisse ne commence que la ou la bande existe.
                while start < s1 and _clip_lane(
                        start, min(side * a, side * b), max(side * a, side * b),
                        minimum=0.25) is None:
                    start += 2.0
            if s1 - start < 8.0:
                continue
            _surface_box(bm, lane[0], lane[1], start, s1, rise, 0.50,
                         "AA_Greeble", material, draft=0.03)
            count += 1
    return count


def build_grafts(bm: bmesh.types.BMesh, index: int, rng: random.Random) -> int:
    """Les greffes : ce que le Cortege EMPORTE, empile sur son borde.

    Trois a quatre boites decroissantes, plus une echine verticale. Leur enveloppe
    grandit du troncon 1 au 5 — c'est ainsi que la silhouette s'epaissit vers la
    poupe sans jamais depasser les 28 m de large ni le plafond.
    """
    origin = index * SECTION_LENGTH
    count = 0
    grafts = 8 + index
    growth = 0.80 + 0.10 * index
    for k in range(grafts):
        s = origin + 7.0 + (SECTION_LENGTH - 20.0) * k / (grafts - 1)
        s += rng.uniform(-1.6, 1.6)
        side = 1.0 if (k + index) % 2 == 0 else -1.0
        base_x = rng.uniform(3.2, 11.4)
        width = rng.uniform(2.4, 4.6) * growth
        length = rng.uniform(4.0, 9.5) * growth
        x0, x1 = base_x - width * 0.5, base_x + width * 0.5
        lane = _clip_lane(s, min(side * x0, side * x1), max(side * x0, side * x1))
        if lane is None or s + length > origin + SECTION_LENGTH - JOINT_CLEARANCE:
            continue
        if _ambry_clash(s, s + length, lane[0], lane[1]):
            continue
        x0, x1 = lane
        wanted = rng.randint(2, 3)
        rise = 0.0
        layers = 0
        for layer in range(wanted):
            shrink = 0.22 * layer
            step = rng.uniform(0.28, 0.42)
            # ⚠️ On verifie AVANT de poser, jamais apres : une version precedente
            # posait la couche puis sortait de la boucle, et deux troncons
            # culminaient a -3,14 pour un plafond de construction de -3,20.
            headroom = BUILD_CEILING_Y - _surface_y(s + length * 0.5, (x0 + x1) * 0.5)
            if rise + step > headroom:
                break
            _surface_box(
                bm,
                x0 + width * shrink, x1 - width * shrink,
                s + length * shrink * 0.55, s + length * (1.0 - shrink * 0.55),
                rise + step, 0.70 + rise,
                "AA_Greeble", "AA_Panel" if layer == 0 else "AA_Hull", draft=0.09)
            rise += step
            layers += 1
        if layers == 0:
            continue
        count += layers
        # L'echine : une lame etroite sur le dessus, qui casse le profil plat.
        if rng.random() < 0.55:
            cx = (x0 + x1) * 0.5
            _surface_box(bm, cx - 0.30, cx + 0.30,
                         s + length * 0.22, s + length * 0.78,
                         min(rise + 0.34, BUILD_CEILING_Y - _surface_y(s, cx)),
                         0.90 + rise, "AA_Greeble", "AA_Trim", draft=0.04)
            count += 1
    return count


def build_pips(bm: bmesh.types.BMesh, index: int, rng: random.Random) -> int:
    """Les petits feux magenta des maquettes : 12 triangles piece.

    Ils sont ce qui, sur les trois planches, dit le plus vite « c'est vivant ».
    ⚠️ Ils sont volontairement PETITS (0,30 a 0,55 m) et poses a plat : leur aire
    emissive totale est mesuree et rapportee, parce que le magenta est aussi une
    couleur de tir ennemi (charte SS3) et qu'un decor ne doit jamais lui disputer
    la lisibilite.
    """
    origin = index * SECTION_LENGTH
    count = 0
    for _ in range(78 + index * 6):
        s = origin + rng.uniform(JOINT_CLEARANCE + 1.0,
                                 SECTION_LENGTH - JOINT_CLEARANCE - 1.0)
        band = BAND_INNER if rng.random() < 0.5 else BAND_MID
        x = rng.uniform(*band) * (1.0 if rng.random() < 0.5 else -1.0)
        lane = _clip_lane(s, x - 0.28, x + 0.28, minimum=0.45)
        if lane is None or _ambry_clash(s - 0.5, s + 0.5, lane[0], lane[1]):
            continue
        long_pip = rng.random() < 0.45
        half_x = 0.15 if long_pip else 0.26
        half_s = 0.44 if long_pip else 0.24
        _surface_box(bm, x - half_x, x + half_x, s - half_s, s + half_s,
                     0.05, 0.35, "AA_Greeble", "AA_Emissive_Engine")
        count += 1
    return count


def build_turret_pad(bm: bmesh.types.BMesh, s: float, x: float,
                     radius: float) -> tuple[float, float]:
    """Le socle d'une tourelle : anneaux concentriques et cœur lumineux.

    Le maillage NE PORTE PAS de tourelle (hors perimetre du brief) : le jeu
    instancie sa scene sur le point d'attache. Le socle existe pour que le point
    d'attache soit LU comme un emplacement et non comme une coordonnee.

    Retourne (y du plan de pose, y de la base enterree).
    """
    around = [(_surface_y(s + radius * math.sin(a), x + radius * math.cos(a)), 0)
              for a in [2.0 * math.pi * k / 12 for k in range(12)]]
    deep = min(y for y, _ in around) - 0.55
    rim = _surface_y(s, x) + 0.55
    contour = [
        (deep, radius, "AA_Greeble"),          # mur exterieur, enterre
        (rim - 0.16, radius, "AA_Hull"),       # chanfrein
        (rim, radius * 0.95, "AA_Trim"),       # liseré ivoire, 5 pct du rayon
        (rim, radius * 0.88, "AA_Hull"),       # couronne sombre
        (rim - 0.36, radius * 0.66, "AA_Greeble"),   # cuvette
        (rim - 0.36, radius * 0.36, "AA_Emissive_Engine"),  # cœur
        (rim - 0.24, radius * 0.26, "AA_Emissive_Engine"),
        (rim - 0.18, 0.0, "AA_Emissive_Engine"),
    ]
    _lathe(bm, x, s, contour, 20)
    return rim, deep


#: Hexagone allonge dans l'axe du survol, comme sur les maquettes 1 a 3.
_HEX = ((0.00, 1.00), (0.87, 0.50), (0.87, -0.50),
        (0.00, -1.00), (-0.87, -0.50), (-0.87, 0.50))


def build_bay(bm: bmesh.types.BMesh, s: float, x: float) -> float:
    """Une baie hexagonale de pont d'envol : coaming, puits, sol emissif.

    ⚠️ Choix de methode. Une VRAIE cavite demanderait de trouer la peau (booleen,
    donc non deterministe, et une peau non manifold). Ici la baie est un coaming
    POSE sur le borde : depuis la camera du jeu — 20 deg de la verticale — un puits
    de 1,75 m borde de parois sombres et fonde de magenta se lit exactement comme
    une baie creusee, pour un dixieme des triangles et sans booleen.

    Retourne le Y de la bouche (ou le jeu fera sortir ses chasseurs).
    """
    hx, hz = 3.40, 3.20
    # ⚠️ LE DEFAUT QUE LA PLANCHE A ATTRAPE, ET QU'AUCUN HARNAIS N'AURAIT VU.
    # Premiere version : levre a -3,90 et sol a -5,65, « un puits de 1,75 m ».
    # Sauf que la peau n'est PAS trouee (voir plus haut : pas de booleen) et
    # qu'elle court a -4,30 sous la bouche. Le pont occultait donc entierement le
    # sol emissif : les sept baies rendaient en hexagones VIDES, contrat vert,
    # UV vertes, budget vert. C'est exactement le genre de faute que l'ADR-0006
    # existe pour attraper — elle ne se voit qu'en regardant.
    # Le sol passe donc AU-DESSUS du pont le plus haut de l'emprise (-4,30) et la
    # levre monte d'autant : puits de 0,78 m, entierement visible du dessus.
    rim = -3.42
    floor = -4.20
    outer = [(x + dx * hx * 1.30, s + dz * hz * 1.30) for dx, dz in _HEX]
    lip = [(x + dx * hx * 1.12, s + dz * hz * 1.12) for dx, dz in _HEX]
    mouth = [(x + dx * hx, s + dz * hz) for dx, dz in _HEX]
    # ⚠️ Le sol n'est PAS emissif de bord a bord. Premiere version : hexagone plein
    # de 6,8 x 6,4 m en `AA_Emissive_Engine`, sept fois dans le niveau. Le magenta
    # est aussi une couleur de TIR ennemi (charte SS3) : une nappe de 35 m2 par
    # baie disputerait la lisibilite aux balles. Le cœur emissif est rentre a 66 pct
    # et cercle d'un `AA_Panel` sombre — 44 pct de l'aire, et un puits qui se lit
    # mieux parce qu'il a maintenant un bord.
    core = [(x + dx * hx * 0.66, s + dz * hz * 0.66) for dx, dz in _HEX]

    base_v = [bm.verts.new(Vector((px, _surface_y(ps, px) - 0.60, _z(ps))))
              for px, ps in outer]
    rim_out = [bm.verts.new(Vector((px, rim, _z(ps)))) for px, ps in outer]
    rim_in = [bm.verts.new(Vector((px, rim, _z(ps)))) for px, ps in lip]
    mouth_v = [bm.verts.new(Vector((px, rim - 0.20, _z(ps)))) for px, ps in mouth]
    floor_v = [bm.verts.new(Vector((px, floor, _z(ps)))) for px, ps in mouth]
    core_v = [bm.verts.new(Vector((px, floor, _z(ps)))) for px, ps in core]

    n = len(_HEX)
    for i in range(n):
        j = (i + 1) % n
        # ⚠️ Le sens : l'hexagone `_HEX` tourne dans le sens ou (dx, dz) croit en
        # angle, donc (x, -z) tourne dans l'autre sens. Les murs exterieurs se
        # bobinent donc bas -> haut avec i puis j inverses.
        _quad(bm, base_v[j], base_v[i], rim_out[i], rim_out[j], "AA_Hull")
        _quad(bm, rim_out[j], rim_out[i], rim_in[i], rim_in[j], "AA_Trim")
        _quad(bm, rim_in[j], rim_in[i], mouth_v[i], mouth_v[j], "AA_Greeble")
        _quad(bm, mouth_v[j], mouth_v[i], floor_v[i], floor_v[j], "AA_Panel")
        _quad(bm, core_v[i], core_v[j], floor_v[j], floor_v[i], "AA_Panel")
    _face(bm, list(reversed(core_v)), "AA_Emissive_Engine")

    # Deux rails de lancement au fond : ils donnent l'echelle du puits.
    for offset in (-1.15, 1.15):
        _box_from_corners(
            bm,
            [Vector((x + offset - 0.24, floor, _z(s - hz * 0.52))),
             Vector((x + offset + 0.24, floor, _z(s - hz * 0.52))),
             Vector((x + offset + 0.24, floor, _z(s + hz * 0.52))),
             Vector((x + offset - 0.24, floor, _z(s + hz * 0.52)))],
            [Vector((x + offset - 0.18, floor + 0.22, _z(s - hz * 0.48))),
             Vector((x + offset + 0.18, floor + 0.22, _z(s - hz * 0.48))),
             Vector((x + offset + 0.18, floor + 0.22, _z(s + hz * 0.48))),
             Vector((x + offset - 0.18, floor + 0.22, _z(s + hz * 0.48)))],
            "AA_Greeble", "AA_Trim")
    # Six taquets sur la levre : la baie doit lire comme un ouvrage, pas un trou.
    for i in range(n):
        px, ps = outer[i]
        cx = x + (px - x) * 1.02
        cs = s + (ps - s) * 1.02
        _surface_box(bm, cx - 0.34, cx + 0.34, cs - 0.34, cs + 0.34,
                     max(0.10, rim - _surface_y(cs, cx) + 0.12), 0.30,
                     "AA_Greeble", "AA_Trim", draft=0.06)
    return rim - 0.04


def build_spine_bulb(bm: bmesh.types.BMesh, s: float) -> float:
    """Un bulbe de l'arete dorsale : le nœud que le joueur devra abattre.

    Il est ce que la coque a de plus haut apres Ambry, et c'est voulu : la
    mecanique doit se VOIR de loin. Son sommet est cale sur le plafond de
    construction, pas choisi a l'œil.
    """
    crest = _surface_y(s, 0.0)
    top = min(crest + 0.40, BUILD_CEILING_Y)
    contour = [
        (crest - 0.95, 1.34, "AA_Greeble"),
        (crest - 0.30, 1.28, "AA_Trim"),
        (crest + 0.02, 1.06, "AA_Trim"),
        (crest + 0.14, 0.86, "AA_Greeble"),
        (top - 0.20, 0.70, "AA_Emissive_Engine"),
        (top - 0.05, 0.40, "AA_Emissive_Engine"),
        (top, 0.0, "AA_Emissive_Engine"),
    ]
    _lathe(bm, 0.0, s, contour, 22)
    # Deux colliers lateraux : ils ancrent le bulbe dans l'arete au lieu de le
    # poser dessus, et ils cassent la revolution parfaite.
    for side in (1.0, -1.0):
        _surface_box(bm, min(side * 1.05, side * 2.05), max(side * 1.05, side * 2.05),
                     s - 1.05, s + 1.05, 0.24, 0.60, "AA_Greeble", "AA_Trim",
                     draft=0.08)
    return top


# ==========================================================================
# Ambry — la seule chose de ce vaisseau qui ne lui appartient pas
# ==========================================================================


def build_ambry(bm: bmesh.types.BMesh) -> tuple[Vector, dict]:
    """Un avant-poste humain de quatre-vingts personnes, greffe sur le borde.

    Il doit JURER, et il jure par trois moyens qui ne dependent d'aucune texture :

    1. **L'orthogonalite.** Tout est aligne sur deux axes et sur un radeau PLAN,
       quand la coque dessous est faite de facettes inclinees. Le radeau est en
       porte-a-faux au-dessus de la facette exterieure, tenu par douze bequilles
       de longueurs toutes differentes — c'est le « re-plombe » du brief, et c'est
       ce qui dit qu'on a POSE cela sur un vaisseau qui n'etait pas fait pour le
       recevoir.
    2. **La valeur, et depuis BRIEF-0090 elle a son propre slot.** Ambry est
       dominee par `AA_Hull_Ambry`, huitieme materiau declare en tete de ce
       fichier : le gris-ivoire `#EDEAE3` des coques Helios Vanguard, contre
       l'anthracite `#24252B` de l'Unisson partout ailleurs — 1 a 15 en
       luminance. AVANT, ces memes faces etaient en `AA_Trim` (l'ivoire froid
       `#DDDCD2` de l'Unisson) : la valeur y etait deja, mais la MATIERE etait
       celle de l'ennemi, et une carte propre a Ambry etait impossible.
       ⚠️ Deux endroits gardent volontairement `AA_Hull` anthracite : les deux
       colliers de greffe (ils appartiennent au vaisseau, pas a l'avant-poste)
       et le pas d'appontage (un pont clair de plus effacerait le pas ; c'est sa
       valeur SOMBRE qui le fait lire comme un pas). Voir le compte-rendu §6.
    3. **L'absence de magenta.** Aucune face `AA_Emissive_Engine` sur Ambry. La
       seule couleur y est le vert maladif `#7C9E52` (`AA_Marking_Red` sous cette
       palette) de la serre — le seul emploi de cette couleur des 500 m.

    Il est INTACT : modules alignes, passerelle continue d'un bout a l'autre, serre
    entiere, antenne debout. C'est ce qui doit rendre la decouverte insoutenable ;
    une ruine ne dirait rien de plus qu'une ruine.

    ⚠️ CONTRAINTE QUI A DECIDE DE TOUT LE PLAN : il reste 1,28 m entre le radeau et
    le plafond de construction. Ambry est donc un RUBAN de 27 x 5,5 m pose le long
    du borde, jamais un bourg en hauteur. Les zones se suivent dans l'axe du
    survol : greffe, habitation, serre, antenne — le joueur les decouvre dans cet
    ordre parce qu'il les survole dans cet ordre.
    """
    s0, s1 = AMBRY_S            # ⚠️ en `s` GLOBAL, comme tout le vocabulaire
    x0, x1 = AMBRY_X
    raft = AMBRY_RAFT_Y
    under = raft - AMBRY_RAFT_THICK
    stats: dict = {}
    tops: list[float] = []

    def slab(ax0, ax1, as0, as1, y_bottom, y_top, side_mat, top_mat, draft=0.0):
        plan = ((ax0, as0), (ax1, as0), (ax1, as1), (ax0, as1))
        inner = ((ax0 + draft, as0 + draft), (ax1 - draft, as0 + draft),
                 (ax1 - draft, as1 - draft), (ax0 + draft, as1 - draft))
        _box_from_corners(
            bm,
            [Vector((x, y_bottom, _z(s))) for x, s in plan],
            [Vector((x, y_top, _z(s))) for x, s in inner],
            side_mat, top_mat)
        tops.append(y_top)

    # --- le radeau, ses douze bequilles et ses deux colliers de greffe --------
    rx0, rx1 = x0 + 0.30, x1 - 0.20
    rs0, rs1 = s0 + 0.5, s1 - 0.5
    slab(rx0, rx1, rs0, rs1, under, raft, "AA_Greeble", AMBRY_HULL)
    for sx in (rx0 + 0.5, (rx0 + rx1) * 0.5, rx1 - 0.5):
        for ss in (rs0 + 2.0, rs0 + 9.0, rs0 + 18.0, rs1 - 1.5):
            foot = _surface_y(ss, sx) - 0.35
            # ⚠️ +0,14 et non `under` : une face du dessus coplanaire avec le
            # dessous du radeau scintillerait. Toutes les pieces empilees
            # d'Ambry sont enfoncees dans leur support pour la meme raison.
            slab(sx - 0.26, sx + 0.26, ss - 0.26, ss + 0.26,
                 foot, under + 0.14, "AA_Greeble", "AA_Greeble")
    for cs0, cs1 in ((s0 - 1.5, s0 + 0.6), (s1 - 0.6, s1 + 1.5)):
        _surface_box(bm, x0 - 0.20, x1 - 0.10, cs0, cs1, 0.26, 0.75,
                     "AA_Greeble", "AA_Hull", draft=0.12)

    # --- quatre modules d'habitation, alignes dans l'axe du survol -----------
    module_top = raft + 0.95
    for k in range(4):
        ms = rs0 + 1.0 + k * 4.6
        slab(rx0 + 0.25, rx0 + 3.35, ms, ms + 4.0, raft - 0.14, module_top,
             AMBRY_HULL, AMBRY_HULL, draft=0.12)
        # Capot technique. Sa base est ENFONCEE de 28 cm dans le module : posee
        # a fleur, elle serait coplanaire avec le toit et scintillerait.
        slab(rx0 + 0.85, rx0 + 2.75, ms + 0.75, ms + 3.25,
             module_top - 0.28, module_top + 0.24, "AA_Greeble", "AA_Panel",
             draft=0.08)
    stats["module_top"] = module_top + 0.24

    # --- la passerelle, continue d'un bout a l'autre, et son pas d'appontage --
    slab(rx0 + 3.65, rx0 + 5.05, rs0 + 0.4, rs1 - 0.4, raft - 0.12, raft + 0.22,
         "AA_Greeble", AMBRY_HULL)
    slab(rx0 + 3.65, rx1 - 0.05, rs0 + 3.2, rs0 + 8.2, raft - 0.12, raft + 0.22,
         "AA_Greeble", "AA_Hull")
    for k in range(11):
        rs = rs0 + 0.9 + k * 2.4
        if rs > rs1 - 1.0:
            break
        for px in (rx0 + 3.68, rx0 + 5.01):
            slab(px - 0.09, px + 0.09, rs, rs + 0.18,
                 raft + 0.10, raft + 0.72, "AA_Greeble", "AA_Greeble")

    # --- la serre : le seul vert des 500 m -----------------------------------
    gs0, gs1 = rs0 + 20.0, rs0 + 26.0
    gx0, gx1 = rx0 + 0.25, rx0 + 3.85
    slab(gx0, gx1, gs0, gs1, raft - 0.12, raft + 0.30,
         "AA_Greeble", "AA_Marking_Red")
    cx = (gx0 + gx1) * 0.5
    rx = (gx1 - gx0) * 0.5
    vault = 0.85
    ribs = 7
    arc = [(math.cos(math.pi * k / 6), math.sin(math.pi * k / 6)) for k in range(7)]
    for k in range(ribs - 1):
        ga = gs0 + (gs1 - gs0) * k / (ribs - 1)
        gb = gs0 + (gs1 - gs0) * (k + 1) / (ribs - 1)
        for i in range(len(arc) - 1):
            c0, v0 = arc[i]
            c1, v1 = arc[i + 1]
            a = bm.verts.new(Vector((cx + rx * c0, raft + 0.30 + vault * v0, _z(ga))))
            b = bm.verts.new(Vector((cx + rx * c1, raft + 0.30 + vault * v1, _z(ga))))
            c = bm.verts.new(Vector((cx + rx * c1, raft + 0.30 + vault * v1, _z(gb))))
            d = bm.verts.new(Vector((cx + rx * c0, raft + 0.30 + vault * v0, _z(gb))))
            # ⚠️ (a, d, c, b) et non (a, b, c, d) : l'arc parcourt les angles
            # CROISSANTS, donc x DECROISSANT, et l'ordre naif rentre la voute a
            # l'envers. Verifie par `_assert_outward()`.
            _quad(bm, a, d, c, b, "AA_Glass")
    for k in range(ribs):
        gs = gs0 + (gs1 - gs0) * k / (ribs - 1)
        slab(cx - rx * 1.03, cx + rx * 1.03, gs - 0.08, gs + 0.08,
             raft + 0.18, raft + 0.30 + vault + 0.06,
             "AA_Marking_Red", "AA_Marking_Red")
    stats["greenhouse_top"] = raft + 0.30 + vault + 0.06

    # --- le mat d'antenne : la chose la plus haute des 500 m ------------------
    ax = rx1 - 0.85
    asx = rs1 - 1.9
    # Exactement le plafond que le script s'impose : le mat est, par
    # construction, la chose la plus haute des 500 m — 2 cm au-dessus
    # des bulbes de l'arete dorsale, et 20 cm sous le plafond du jeu.
    mast_top = BUILD_CEILING_Y
    slab(ax - 0.62, ax + 0.62, asx - 0.72, asx + 0.72, raft - 0.12, raft + 0.30,
         "AA_Greeble", AMBRY_HULL)
    slab(ax - 0.17, ax + 0.17, asx - 0.17, asx + 0.17, raft + 0.16, mast_top,
         "AA_Greeble", "AA_Greeble")
    for span, y in ((1.05, mast_top - 1.02), (0.76, mast_top - 0.72),
                    (0.48, mast_top - 0.46)):
        slab(ax - span, ax + span, asx - 0.08, asx + 0.08, y, y + 0.11,
             AMBRY_HULL, AMBRY_HULL)
        slab(ax - 0.08, ax + 0.08, asx - span, asx + span, y, y + 0.11,
             AMBRY_HULL, AMBRY_HULL)
    stats["mast_top"] = mast_top

    top = max(tops)
    if top > BUILD_CEILING_Y + 1e-6:
        raise ak.ContractError(
            f"Ambry culmine a {top:.3f} > plafond de construction {BUILD_CEILING_Y}")
    stats["top"] = top
    stats["footprint"] = (AMBRY_X, AMBRY_S)
    anchor = Vector(((rx0 + rx1) * 0.5, raft + 0.28, _z((rs0 + rs1) * 0.5)))
    return anchor, stats


# ==========================================================================
# Assemblage d'un troncon
# ==========================================================================


def _object_density(obj: bpy.types.Object) -> dict:
    """Densite de texels d'un objet Blender, sur la TOTALITE de ses faces.

    Sert au seul cas d'Ambry : fusionnee dans le troncon 5, elle ne peut etre
    isolee du `.glb` que par une boite, qui laisse ses bequilles dehors. Cette
    mesure-ci est complete, et elle sert de recoupement a celle du binaire.
    """
    # ⚠️ Une UV appartient a une BOUCLE, jamais a un sommet. Une premiere version
    # indexait les UV par `loop.vertex_index` : sur une projection en boite, ou
    # chaque changement d'axe dominant coupe la carte, presque tous les sommets
    # portent deux ou trois UV differentes, et le dernier ecrit gagnait. La mesure
    # sortait « 0,007 a 381 tuiles/m, anisotropie 44 150 » — un chiffre assez
    # absurde pour se voir, ce qui n'est pas toujours le cas.
    mesh = obj.data
    uv_layer = mesh.uv_layers.active
    mesh.calc_loop_triangles()
    points: list[tuple] = []
    uvs: list[tuple] = []
    tris: list[tuple[int, int, int]] = []
    for triangle in mesh.loop_triangles:
        base = len(points)
        for loop_index in triangle.loops:
            points.append(tuple(mesh.vertices[mesh.loops[loop_index].vertex_index].co))
            uvs.append(tuple(uv_layer.data[loop_index].uv))
        tris.append((base, base + 1, base + 2))
    return _texel_density(points, uvs, tris)


def _triangulate_ngons(obj: bpy.types.Object) -> None:
    """Decoupe les seules faces de plus de 4 sommets.

    Sans cela l'exporteur renonce aux TANGENTES (« tangent space can only be
    computed for tris/quads ») et ADR-0011 devient inoperant.
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons)
    bm.to_mesh(obj.data)
    bm.free()


def _assert_skin_outward(bm: bmesh.types.BMesh, name: str) -> None:
    """Les normales de la PEAU sortent — verifie face par face, jamais suppose.

    ⚠️ Le harnais qui justifie de ne pas appeler `ak.new_object()` (voir l'en-tete).
    Les troncons 2 a 5 sont des tubes OUVERTS aux deux bouts : `recalc_face_normals`
    y decide par une heuristique, et si elle se trompe la coque entiere est
    retournee. Aucune bounding box, aucun compte de triangles, aucune mesure d'UV ne
    le verrait ; en jeu, le decor disparaitrait purement et simplement (culling
    arriere), et le journal resterait muet.

    Il s'applique a la peau SEULE et il est appele avant que le moindre module ne
    soit pose : une boite a legitimement une face du dessous tournee vers le bas,
    la peau non. Trois familles sont controlees — le pont, le fond et les flancs —
    parce qu'un retournement autour d'un seul axe existe aussi.
    """
    bm.normal_update()
    checked = 0
    problems: list[str] = []
    for face in bm.faces:
        centre = face.calc_center_median()
        n = face.normal
        if centre.y > Y_PIVOT and abs(n.y) > 0.55:
            checked += 1
            if n.y < 0.0:
                problems.append(f"pont {tuple(round(c, 2) for c in centre)}")
        elif centre.y < Y_PIVOT and abs(n.y) > 0.55:
            checked += 1
            if n.y > 0.0:
                problems.append(f"fond {tuple(round(c, 2) for c in centre)}")
        elif abs(centre.x) > 3.0 and abs(n.x) > 0.7:
            checked += 1
            if n.x * centre.x < 0.0:
                problems.append(f"flanc {tuple(round(c, 2) for c in centre)}")
    if checked < 100:
        raise ak.ContractError(f"{name} : peau trop pauvre pour etre controlee "
                               f"({checked} faces)")
    if problems:
        raise ak.ContractError(
            f"{name} : {len(problems)} faces de peau sur {checked} sont retournees, "
            f"la coque serait invisible en jeu — p.ex. {problems[0]}")


def _assert_build_ceiling(obj: bpy.types.Object) -> float:
    """Le plafond du JEU est -3,00 ; celui que le script s'impose est -3,20.

    Les deux sont bloquants, et c'est volontaire : la marge de 20 cm n'est pas une
    politesse, c'est la place que le concepteur aura pour poser des tourelles, des
    nœuds et des ponts SUR les points d'attache. Une coque qui mangerait cette
    marge obligerait a reforger.
    """
    top = max(v.co.y for v in obj.data.vertices)
    if top > CEILING_Y:
        raise ak.ContractError(
            f"{obj.name} : culmine a Y = {top:.3f} > plafond du jeu {CEILING_Y}")
    if top > BUILD_CEILING_Y + 1e-6:
        raise ak.ContractError(
            f"{obj.name} : culmine a Y = {top:.3f} > plafond de construction "
            f"{BUILD_CEILING_Y} — la marge est reservee a ce que le jeu posera "
            "sur les points d'attache")
    return top


def build_section(index: int) -> tuple[bpy.types.Object, list, dict]:
    """Un troncon complet et ses points d'attache, en coordonnees LOCALES."""
    global _ORIGIN
    origin = index * SECTION_LENGTH
    _ORIGIN = origin
    name = f"Section_{index + 1:02d}"
    rng = random.Random(0xC0F1 + index * 977)

    bm = bmesh.new()
    build_skin(bm, index)
    _assert_skin_outward(bm, name)
    counts = {
        "plaques": build_plates(bm, index, rng),
        "nervures": build_ribs(bm, index, rng),
        "lisses": build_strakes(bm, index),
        "greffes": build_grafts(bm, index, rng),
        "pastilles": build_pips(bm, index, rng),
    }

    anchors: list[tuple[str, Vector]] = []
    pads = 0
    for number, (s, x) in enumerate(TURRETS, start=1):
        if not (origin <= s < origin + SECTION_LENGTH):
            continue
        rim, _ = build_turret_pad(bm, s, x, PAD_RADIUS[index])
        anchors.append((f"Turret_{number:02d}", Vector((x, rim + 0.10, _z(s)))))
        pads += 1
    bays = 0
    for number, (s, x) in enumerate(BAYS, start=1):
        if not (origin <= s < origin + SECTION_LENGTH):
            continue
        mouth = build_bay(bm, s, x)
        anchors.append((f"Bay_{number:02d}", Vector((x, mouth, _z(s)))))
        bays += 1
    for number, s in enumerate(SPINES, start=1):
        if not (origin <= s < origin + SECTION_LENGTH):
            continue
        top = build_spine_bulb(bm, s)
        anchors.append((f"Spine_{number:02d}", Vector((0.0, top + 0.06, _z(s)))))
    counts["plateformes"] = pads
    counts["baies"] = bays

    hull = _new_object(name, bm)
    _weld(hull)
    _triangulate_ngons(hull)
    ak.shade_smooth_by_angle(hull, angle_deg=26.0)
    ak.box_project_uv(hull, HULL_TEXELS_PER_METER)

    if index == SECTION_COUNT - 1:
        abm = bmesh.new()
        anchor, ambry_stats = build_ambry(abm)
        ambry = _new_object(name + "_Ambry", abm)
        _weld(ambry)
        _triangulate_ngons(ambry)
        ak.shade_smooth_by_angle(ambry, angle_deg=26.0)
        # ⚠️ Depliage PROPRE a Ambry, applique AVANT la fusion : `box_project_uv`
        # travaille sur tout l'objet, il n'y a donc pas d'autre moment ou les deux
        # echelles peuvent coexister. La fusion conserve la couche UV (meme nom).
        ak.box_project_uv(ambry, AMBRY_TEXELS_PER_METER)
        counts["ambry"] = len(ambry.data.polygons)
        counts["ambry_density"] = _object_density(ambry)
        hull = ak.join_objects([hull, ambry], name)
        anchors.append(("Ambry", anchor))
        counts["ambry_stats"] = ambry_stats

    counts["top"] = _assert_build_ceiling(hull)
    return hull, anchors, counts


# ==========================================================================
# Export — meme chaine d'axes que le kit, refaite ici (voir l'en-tete)
# ==========================================================================

_YUP = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))

#: Repere GODOT -> repere d'auteur ADR-0008, correction d'axe COMPRISE, en une
#: seule matrice a coefficients ENTIERS : (x, y, z) -> (x, -z, y).
#:
#: ⚠️ Elle vaut exactement `_AXIS_FIX @ _TO_AUTHOR` du kit (rotation d'un demi-tour
#: autour de Z composee avec (x, y, z) -> (-x, z, y)) — c'est la meme chaine, et
#: `_assert_axis_chain()` le reverifie. Mais le kit la compose a partir de
#: `Matrix.Rotation(pi, 4, "Z")`, dont Blender calcule `cos(pi) = -0.99999976` en
#: simple precision. A 78 m (le survol de lune) l'erreur vaut 7 µm et personne ne
#: la voit ; a 400 m (le troncon 5) elle vaut 35 µm et elle sort dans la
#: TRANSLATION DU NŒUD, que le moteur relit. On la refuse a la source : ces
#: coefficients-la sont exacts, et deux executions donnent le meme binaire.
_AUTHOR_FIX = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))


def _author(v: Vector) -> Vector:
    """Repere Godot -> repere d'auteur, correction d'axe comprise. Exact."""
    return Vector((v.x, -v.z, v.y))


def _assert_axis_chain() -> None:
    """La chaine complete doit rendre l'identite, sur des temoins ASYMETRIQUES.

    Si quelqu'un « simplifie » `_AUTHOR_FIX` en identite, tout le Cortege part a
    180 deg : la proue arriverait par le bas de l'ecran et Ambry passerait a
    babord. La bounding box ne le verrait pas — elle est presque symetrique. Ceci
    le voit, et il verifie en plus l'EQUIVALENCE avec la chaine du kit.
    """
    kit = Matrix.Rotation(math.pi, 4, "Z") @ \
        Matrix(((-1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    for probe in (Vector((1.0, 2.0, 3.0)), Vector((-9.3, -4.9, -436.0)),
                  Vector((0.0, -3.62, -500.0))):
        author = _author(probe)
        if (author - _AUTHOR_FIX.to_3x3() @ probe).length > 1e-9:
            raise ak.ContractError("_author() et _AUTHOR_FIX divergent")
        if (author - kit.to_3x3() @ probe).length > 1e-3:
            raise ak.ContractError(
                "la chaine d'axes n'est plus celle du kit : "
                f"{tuple(author)} vs {tuple(kit.to_3x3() @ probe)}")
        got = _YUP.to_3x3() @ author
        if (got - probe).length > 1e-9:
            raise ak.ContractError(
                f"chaine d'axes rompue : {tuple(probe)} -> {tuple(got)}")


def _read_glb(path: str) -> tuple[dict, bytes]:
    """Relit le `.glb` produit : on valide le livrable, pas nos intentions."""
    with open(path, "rb") as handle:
        data = handle.read()
    if data[:4] != b"glTF":
        raise ak.ContractError(f"{path} : ce n'est pas un glTF binaire")
    gltf: dict | None = None
    blob = b""
    offset = 12
    while offset < len(data):
        length, kind = struct.unpack_from("<II", data, offset)
        offset += 8
        chunk = data[offset:offset + length]
        offset += length
        if kind == 0x4E4F534A:
            gltf = json.loads(chunk)
        elif kind == 0x004E4942:
            blob = chunk
    if gltf is None:
        raise ak.ContractError(f"{path} : chunk JSON absent")
    return gltf, blob


def export(sections: list[tuple[bpy.types.Object, list]], filepath: str) -> dict:
    """Corrige les axes, parente les marqueurs, exporte, puis relit et valide."""
    _assert_axis_chain()
    empties: list[bpy.types.Object] = []
    for index, (obj, anchors) in enumerate(sections):
        obj.data.transform(_AUTHOR_FIX)
        obj.data.update()
        obj.location = _author(Vector((0.0, 0.0, -index * SECTION_LENGTH)))
        for name, local in anchors:
            empty = bpy.data.objects.new(name, None)
            empty.empty_display_type = "PLAIN_AXES"
            empty.empty_display_size = 0.6
            bpy.context.scene.collection.objects.link(empty)
            # ⚠️ Parentage DIRECT (pas `parent_set`) : Blender appliquerait sinon
            # l'inverse de la matrice du parent et le marqueur partirait deux fois.
            empty.parent = obj
            empty.matrix_parent_inverse = Matrix.Identity(4)
            empty.location = _author(local)
            empties.append(empty)

    bpy.ops.object.select_all(action="DESELECT")
    for obj, _ in sections:
        obj.select_set(True)
    for empty in empties:
        empty.select_set(True)
    bpy.context.view_layer.objects.active = sections[0][0]

    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    staging = tempfile.mkdtemp(prefix="aegis-cortege-")
    staged = os.path.join(staging, os.path.basename(filepath))
    try:
        bpy.ops.export_scene.gltf(
            filepath=staged,
            export_format="GLB",
            export_yup=True,
            export_apply=True,
            use_selection=True,
            export_materials="EXPORT",
            export_cameras=False,
            export_lights=False,
            export_animations=False,
            export_skins=False,
            export_extras=False,
            export_tangents=True,
            export_normals=True,
            export_texcoords=True,
        )
        report = _audit(staged)
        os.replace(staged, filepath)
    finally:
        if os.path.isdir(staging):
            for leftover in os.listdir(staging):
                os.remove(os.path.join(staging, leftover))
            os.rmdir(staging)
    return report


# ==========================================================================
# Les harnais — tout ce qui suit ECHOUE le build
# ==========================================================================


def _accessor(gltf: dict, blob: bytes, index: int) -> list[tuple]:
    comp = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2), 5123: ("H", 2),
            5125: ("I", 4), 5126: ("f", 4)}
    counts = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}
    acc = gltf["accessors"][index]
    fmt, size = comp[acc["componentType"]]
    n = counts[acc["type"]]
    view = gltf["bufferViews"][acc["bufferView"]]
    base = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
    stride = view.get("byteStride") or (size * n)
    return [struct.unpack_from("<" + fmt * n, blob, base + i * stride)
            for i in range(acc["count"])]


def _indices(gltf: dict, blob: bytes, prim: dict) -> list[int]:
    if "indices" in prim:
        return [i[0] for i in _accessor(gltf, blob, prim["indices"])]
    count = gltf["accessors"][prim["attributes"]["POSITION"]]["count"]
    return list(range(count))


def _expected_markers() -> list[str]:
    names = [f"Turret_{i:02d}" for i in range(1, len(TURRETS) + 1)]
    names += [f"Bay_{i:02d}" for i in range(1, len(BAYS) + 1)]
    names += [f"Spine_{i:02d}" for i in range(1, len(SPINES) + 1)]
    names.append("Ambry")
    return names


def _texel_density(points: list[tuple], uvs: list[tuple],
                   tris: list[tuple[int, int, int]]) -> dict:
    """Densite de texels, triangle par triangle, par valeurs singulieres.

    ⚠️ Une moyenne d'aires ne verrait AUCUN etirement : un triangle deux fois trop
    long dans un sens et deux fois trop court dans l'autre a la bonne aire. Ce qui
    se mesure ici, ce sont les deux valeurs singulieres de l'application
    plan-du-triangle -> UV : leur inverse donne les metres par tuile dans les deux
    directions principales, et leur rapport donne l'anisotropie.
    """
    lo, hi, total, weight = math.inf, 0.0, 0.0, 0.0
    aniso = 1.0
    for ia, ib, ic in tris:
        pa, pb, pc = (Vector(points[i]) for i in (ia, ib, ic))
        ua, ub, uc = (Vector(uvs[i][:2]) for i in (ia, ib, ic))
        e1, e2 = pb - pa, pc - pa
        area = e1.cross(e2).length * 0.5
        if area < 1e-9:
            continue
        # Base orthonormee du plan du triangle.
        bx = e1.normalized()
        bz = e1.cross(e2).normalized()
        by = bz.cross(bx)
        a11, a21 = e1.dot(bx), e1.dot(by)
        a12, a22 = e2.dot(bx), e2.dot(by)
        det = a11 * a22 - a12 * a21
        if abs(det) < 1e-12:
            continue
        # M = J * A^-1, ou J = [ub-ua, uc-ua] en colonnes.
        j11, j21 = ub.x - ua.x, ub.y - ua.y
        j12, j22 = uc.x - ua.x, uc.y - ua.y
        i11, i12 = a22 / det, -a12 / det
        i21, i22 = -a21 / det, a11 / det
        m11 = j11 * i11 + j12 * i21
        m12 = j11 * i12 + j12 * i22
        m21 = j21 * i11 + j22 * i21
        m22 = j21 * i12 + j22 * i22
        # Valeurs singulieres d'une 2x2 par la forme fermee.
        e = (m11 + m22) * 0.5
        f = (m11 - m22) * 0.5
        g = (m21 + m12) * 0.5
        h = (m21 - m12) * 0.5
        q = math.hypot(e, h)
        r = math.hypot(f, g)
        s1, s2 = q + r, abs(q - r)
        if s2 < 1e-9:
            continue
        lo = min(lo, s2)
        hi = max(hi, s1)
        aniso = max(aniso, s1 / s2)
        total += (s1 + s2) * 0.5 * area
        weight += area
    if weight == 0.0:
        return {}
    mean = total / weight
    return {
        "tiles_per_m_min": lo, "tiles_per_m_max": hi, "tiles_per_m_mean": mean,
        "m_per_tile_min": 1.0 / hi, "m_per_tile_max": 1.0 / lo,
        "m_per_tile_mean": 1.0 / mean, "anisotropy_max": aniso,
    }


def _audit(path: str) -> dict:
    """Relit le `.glb` PRODUIT et verifie tout ce que le brief exige.

    On lit le fichier binaire et non la scene en memoire : c'est la seule chose que
    Godot chargera. Les trois coques du depot sorties sans UV (ADR-0028) avaient
    toutes une scene Blender parfaite.
    """
    gltf, blob = _read_glb(path)
    problems: list[str] = []
    materials = [m.get("name", f"#{i}") for i, m in enumerate(gltf.get("materials", []))]
    nodes = gltf.get("nodes", [])
    roots = gltf.get("scenes", [{}])[0].get("nodes", list(range(len(nodes))))
    root_names = [nodes[i].get("name", "?") for i in roots]

    # --- contrat de noms : cinq racines, et rien d'autre -----------------------
    expected_roots = [f"Section_{i:02d}" for i in range(1, SECTION_COUNT + 1)]
    for name in expected_roots:
        if name not in root_names:
            problems.append(f"contrat de noms rompu : '{name}' absent de {root_names}")
    for name in root_names:
        if name not in expected_roots:
            problems.append(f"racine inattendue : '{name}' (le decor a cinq troncons)")

    # --- les marqueurs : Empties, enfants, aux noms exacts ---------------------
    found: dict[str, tuple[str, tuple]] = {}
    for index in roots:
        node = nodes[index]
        owner = node.get("name", "?")
        for child_index in node.get("children", []):
            child = nodes[child_index]
            child_name = child.get("name", "?")
            if "mesh" in child:
                problems.append(
                    f"{owner} : l'enfant '{child_name}' porte un maillage — le brief "
                    "exige des troncons sans enfants mailles")
            if child.get("children"):
                problems.append(f"{child_name} : un marqueur n'a pas d'enfant")
            if child_name in found:
                problems.append(f"marqueur en double : '{child_name}'")
            found[child_name] = (owner, tuple(child.get("translation", (0.0, 0.0, 0.0))))
    for name in _expected_markers():
        if name not in found:
            problems.append(f"MARQUEUR MANQUANT : '{name}' — le jeu ne peut pas y "
                            "instancier sa scene")
    for name in found:
        if name not in _expected_markers():
            problems.append(f"marqueur inattendu : '{name}'")

    # --- geometrie, budgets, plafond, jonctions --------------------------------
    stats: dict[str, dict] = {}
    prims_total = prims_uv = prims_tan = 0
    triangles_total = 0
    top_of_decor = -math.inf
    widest = 0.0
    used_materials: set[str] = set()
    boundary: dict[str, dict[str, list[tuple[float, float]]]] = {}
    density_source: dict[str, list] = {}
    emissive_area = 0.0
    total_area = 0.0
    area_by_material: dict[str, float] = {}
    ambry_slot_strays = 0
    ambry_slot_tris = 0

    for index in roots:
        node = nodes[index]
        name = node.get("name", "?")
        if "mesh" not in node:
            problems.append(f"{name} : noeud sans maillage")
            continue
        translation = node.get("translation", [0.0, 0.0, 0.0])
        section_number = int(name.split("_")[1])
        expect_z = -(section_number - 1) * SECTION_LENGTH
        if abs(translation[0]) > 1e-5 or abs(translation[1]) > 1e-5 or \
                abs(translation[2] - expect_z) > 1e-4:
            problems.append(
                f"{name} : translation {tuple(translation)} au lieu de "
                f"(0, 0, {expect_z}) — le moteur en deduit le placement")
        if node.get("rotation") or node.get("scale"):
            problems.append(f"{name} : le noeud doit rester sans rotation ni echelle")

        triangles = 0
        lo = [math.inf] * 3
        hi = [-math.inf] * 3
        front: list[tuple[float, float]] = []
        back: list[tuple[float, float]] = []
        per_section: list = []
        for prim in gltf["meshes"][node["mesh"]]["primitives"]:
            prims_total += 1
            attrs = prim["attributes"]
            has_uv = "TEXCOORD_0" in attrs
            prims_uv += 1 if has_uv else 0
            prims_tan += 1 if "TANGENT" in attrs else 0
            acc = gltf["accessors"][attrs["POSITION"]]
            points = _accessor(gltf, blob, attrs["POSITION"])
            tri_indices = _indices(gltf, blob, prim)
            triangles += len(tri_indices) // 3
            material = materials[prim["material"]] if "material" in prim else "<aucun>"
            used_materials.add(material)
            if has_uv:
                uvs = _accessor(gltf, blob, attrs["TEXCOORD_0"])
                tris = [(tri_indices[k], tri_indices[k + 1], tri_indices[k + 2])
                        for k in range(0, len(tri_indices) - 2, 3)]
                per_section.append((points, uvs, tris, material))
            for axis in range(3):
                lo[axis] = min(lo[axis], acc["min"][axis] + translation[axis])
                hi[axis] = max(hi[axis], acc["max"][axis] + translation[axis])
            for px, py, pz in points:
                widest = max(widest, abs(px))
                if abs(pz) < 1e-4:
                    front.append((round(px, 4), round(py, 4)))
                if abs(pz + SECTION_LENGTH) < 1e-4:
                    back.append((round(px, 4), round(py, 4)))
        density_source[name] = per_section
        boundary[name] = {"front": sorted(set(front)), "back": sorted(set(back))}
        triangles_total += triangles
        if triangles > TRI_BUDGET_SECTION:
            problems.append(
                f"{name} : {triangles} triangles > budget {TRI_BUDGET_SECTION}")
        top_of_decor = max(top_of_decor, hi[1])
        if hi[1] > CEILING_Y:
            problems.append(
                f"{name} : culmine a Y = {hi[1]:.3f} > plafond {CEILING_Y} — un volume "
                "qui masque le combat sans pouvoir etre touche")
        stats[name] = {
            "triangles": triangles,
            "translation": tuple(translation),
            "min": tuple(lo), "max": tuple(hi),
            "size": tuple(hi[a] - lo[a] for a in range(3)),
        }

    if triangles_total > TRI_BUDGET_TOTAL:
        problems.append(
            f"{triangles_total} triangles au total > budget {TRI_BUDGET_TOTAL}")
    if abs(widest - HALF_WIDTH) > 1e-3:
        problems.append(
            f"largeur hors-tout {2 * widest:.4f} m au lieu de {2 * HALF_WIDTH}")

    # --- jonctions : bout a bout, sans trou ni recouvrement --------------------
    for number in range(1, SECTION_COUNT):
        upstream = stats.get(f"Section_{number:02d}")
        downstream = stats.get(f"Section_{number + 1:02d}")
        if not upstream or not downstream:
            continue
        gap = upstream["min"][2] - downstream["max"][2]
        if abs(gap) > 1e-4:
            problems.append(
                f"jonction {number}-{number + 1} : ecart de {gap:+.5f} m entre "
                f"z = {upstream['min'][2]:.4f} et z = {downstream['max'][2]:.4f}")
        # Et surtout : les DEUX ANNEAUX de peau doivent etre identiques, sinon la
        # jonction se voit comme une marche meme sans trou.
        a = boundary.get(f"Section_{number:02d}", {}).get("back", [])
        b = boundary.get(f"Section_{number + 1:02d}", {}).get("front", [])
        if not a or not b:
            problems.append(f"jonction {number}-{number + 1} : anneau de bord absent")
        elif a != b:
            problems.append(
                f"jonction {number}-{number + 1} : profils differents "
                f"({len(a)} vs {len(b)} points, {len(set(a) ^ set(b))} ecarts)")

    # --- UV : 100 pct des primitives, compte dans le binaire -------------------
    if prims_total == 0 or prims_uv != prims_total:
        problems.append(
            f"{prims_total - prims_uv} primitive(s) sur {prims_total} sans "
            "TEXCOORD_0 — la surface ne pourrait recevoir aucune carte (ADR-0028)")
    if prims_tan != prims_total:
        problems.append(
            f"{prims_total - prims_tan} primitive(s) sur {prims_total} sans TANGENT")

    # --- materiaux : les 8 AA_*, aucune couleur de tir, aucune texture ---------
    # ⚠️ HUIT depuis BRIEF-0090 : les sept du kit plus `AA_Hull_Ambry`, declare
    # localement (voir la tete du fichier). Ce harnais est ce qui empeche le
    # huitieme de disparaitre en silence le jour ou l'on retouchera Ambry.
    for name in MATERIAL_ORDER:
        if name not in materials:
            problems.append(f"materiau '{name}' absent du .glb (les 8 sont requis)")
        elif name not in used_materials:
            problems.append(f"materiau '{name}' present mais assigne a aucune face")
    forbidden = [ak.srgb_hex_to_linear(h)[:3] for h in FORBIDDEN_HEX]
    for material in gltf.get("materials", []):
        pbr = material.get("pbrMetallicRoughness", {})
        colors = [tuple(pbr.get("baseColorFactor", [0, 0, 0, 1])[:3]),
                  tuple(material.get("emissiveFactor", [0, 0, 0]))]
        for color in colors:
            for banned, hexa in zip(forbidden, FORBIDDEN_HEX):
                if max(abs(c - b) for c, b in zip(color, banned)) < 0.02:
                    problems.append(
                        f"materiau {material.get('name')} : couleur {hexa} — elle "
                        "appartient aux tirs (charte SS3)")
        if "baseColorTexture" in pbr or "metallicRoughnessTexture" in pbr or \
                "normalTexture" in material or "occlusionTexture" in material or \
                "emissiveTexture" in material:
            problems.append(
                f"materiau {material.get('name')} : TEXTURE dans le .glb — la "
                "matiere vient de l'operateur (ADR-0028)")
    if gltf.get("images"):
        problems.append("le .glb embarque des images : interdit par ADR-0028")

    # --- densite de texels, par piece ------------------------------------------
    # ⚠️ Ambry est FUSIONNEE dans le maillage du troncon 5 (le brief exige cinq
    # racines et aucun enfant maille) : rien dans le `.glb` ne la nomme. On la
    # separe donc geometriquement, et en DEUX TEMPS, parce qu'un seul seuil ne
    # peut pas faire les deux travaux a la fois :
    #
    #   * l'emprise (x, z) sort du calcul du BORDE tout ce qui est sous Ambry —
    #     y compris le pont qu'elle couvre. C'est ce qui garantit qu'aucun de ses
    #     triangles a 0,70 tuile/m ne contamine la mesure a 0,20 ;
    #   * un plancher en Y, 5 cm sous le dessous du radeau, decide de ce qui entre
    #     dans la mesure d'AMBRY. Il laisse dehors les douze bequilles, qui
    #     plongent jusqu'au borde — elles portent la meme echelle, et la mesure
    #     complete est faite en plus cote Blender (`ambry_density`).
    origin = (SECTION_COUNT - 1) * SECTION_LENGTH
    keep_x = AMBRY_KEEPOUT_X
    keep_z = (-(AMBRY_KEEPOUT_S[1] - origin), -(AMBRY_KEEPOUT_S[0] - origin))
    ambry_floor = AMBRY_RAFT_Y - AMBRY_RAFT_THICK - 0.05
    # ⚠️ Le bord inboard de la fenetre d'Ambry est a 7,40 et non a 6,90 : la
    # CONTREMARCHE DE CHINE monte de -4,94 a -4,34 entre x = 6,80 et x = 7,35,
    # donc au-dessus du plancher. Avec la borne large, elle etait comptee comme
    # ambryenne et tirait la densite minimale d'Ambry a 0,147.
    ambry_x = (AMBRY_X[0] - 0.20, HALF_WIDTH + 0.05)

    density: dict[str, dict] = {}
    for name, packs in density_source.items():
        pts: list[tuple] = []
        uvs: list[tuple] = []
        tris: list[tuple[int, int, int]] = []
        ambry_pts: list[tuple] = []
        ambry_uvs: list[tuple] = []
        ambry_tris: list[tuple[int, int, int]] = []
        for points, uv, triangles, material in packs:
            base = len(pts)
            pts += points
            uvs += uv
            abase = len(ambry_pts)
            ambry_pts += points
            ambry_uvs += uv
            last = name == f"Section_{SECTION_COUNT:02d}"
            for ia, ib, ic in triangles:
                cx = (points[ia][0] + points[ib][0] + points[ic][0]) / 3.0
                cy = (points[ia][1] + points[ib][1] + points[ic][1]) / 3.0
                cz = (points[ia][2] + points[ib][2] + points[ic][2]) / 3.0
                in_keepout = last and keep_x[0] <= cx <= keep_x[1] \
                    and keep_z[0] <= cz <= keep_z[1]
                if in_keepout:
                    if cy >= ambry_floor and ambry_x[0] <= cx <= ambry_x[1]:
                        ambry_tris.append((abase + ia, abase + ib, abase + ic))
                else:
                    tris.append((base + ia, base + ib, base + ic))
                pa = Vector(points[ia])
                area = (Vector(points[ib]) - pa).cross(Vector(points[ic]) - pa).length
                total_area += area * 0.5
                area_by_material[material] = \
                    area_by_material.get(material, 0.0) + area * 0.5
                if material == "AA_Emissive_Engine":
                    emissive_area += area * 0.5
                # ⚠️ LE HUITIEME SLOT NE SORT PAS D'AMBRY (BRIEF-0090). Un
                # gris-ivoire qui deborderait sur le borde de l'Unisson volerait
                # la lecture a tout le niveau — c'est la lecon mesuree du rendu
                # precedent : sur 500 m, un materiau clair pose sur une arete
                # CONTINUE occupe plus de pixels qu'une piece entiere. Le
                # controle est triangle par triangle, sur le binaire, et il
                # echoue le build.
                if material == AMBRY_HULL:
                    ambry_slot_tris += 1
                    if not in_keepout:
                        ambry_slot_strays += 1
        density[name] = _texel_density(pts, uvs, tris)
        if ambry_tris:
            density["Ambry"] = _texel_density(ambry_pts, ambry_uvs, ambry_tris)

    if ambry_slot_strays:
        problems.append(
            f"{ambry_slot_strays} triangle(s) en '{AMBRY_HULL}' hors de l'emprise "
            "d'Ambry — ce slot lui est reserve (BRIEF-0090)")
    if ambry_slot_tris == 0:
        problems.append(f"aucun triangle en '{AMBRY_HULL}' : le slot propre a "
                        "Ambry a disparu")

    # ⚠️ Le plancher n'est pas la cible : une projection EN BOITE etire par
    # 1/cos(angle a l'axe dominant), et le pire cas geometrique est la normale
    # (1,1,1)/sqrt(3), a 54,74 deg de son axe dominant, soit sqrt(3) = 1,732. Une
    # densite minimale de cible/1,73 n'est donc pas un defaut de depliage : c'est
    # la BORNE de la methode que le brief a choisie. Exiger la cible partout
    # reviendrait a exiger un depliage continu, que le brief n'a pas demande.
    # Ce qui doit tenir, en revanche, c'est la MOYENNE (l'echelle annoncee) et le
    # fait qu'aucune face ne descende SOUS la borne theorique.
    for name, measure in density.items():
        if not measure:
            continue
        target = AMBRY_TEXELS_PER_METER if name == "Ambry" else HULL_TEXELS_PER_METER
        floor = target / math.sqrt(3.0) * 0.98
        if measure["tiles_per_m_min"] < floor:
            problems.append(
                f"{name} : densite minimale {measure['tiles_per_m_min']:.4f} "
                f"tuile/m, sous la borne {floor:.4f} de la projection en boite")
        if measure["tiles_per_m_max"] > target * 1.02:
            problems.append(
                f"{name} : densite maximale {measure['tiles_per_m_max']:.4f} "
                f"tuile/m, au-dessus de la cible {target:.4f} — echelle fausse")
        if abs(measure["tiles_per_m_mean"] - target) > target * 0.14:
            problems.append(
                f"{name} : densite moyenne {measure['tiles_per_m_mean']:.4f} "
                f"tuile/m, a plus de 14 pct de la cible {target:.4f}")

    if problems:
        raise ak.ContractError(
            "CONTRAT ROMPU — long_cortege\n" + "\n".join(f"  - {p}" for p in problems))

    return {
        "sections": stats,
        "markers": found,
        "density": density,
        "primitives": (prims_uv, prims_tan, prims_total),
        "triangles": triangles_total,
        "materials": sorted(used_materials),
        "area_by_material": area_by_material,
        "total_area": total_area,
        "ambry_slot_triangles": ambry_slot_tris,
        "top": top_of_decor,
        "width": 2 * widest,
        "emissive_ratio": emissive_area / total_area if total_area else 0.0,
        "bytes": os.path.getsize(path),
    }


# ==========================================================================
# Mesures de cadrage — ce que la camera du jeu voit reellement de la coque
# ==========================================================================

CAM_POS = Vector((0.0, 14.0, 5.0))
CAM_FORWARD = Vector((0.0, -0.940, -0.342)).normalized()
CAM_UP = Vector((0.0, 0.342, -0.940)).normalized()
CAM_FOV_V = math.radians(62.0)
CAM_ASPECT = 16.0 / 9.0


def _frame_coverage(deck_y: float) -> dict:
    """Quelle FRACTION de la largeur du cadre la coque de 28 m occupe-t-elle ?

    Le brief pose 28 m « le plan de jeu fait 28 : la coque emplit l'ecran ». Les
    28 m emplissent le plan de jeu a Y = 0 ; le pont de la coque est 4,3 m PLUS BAS,
    donc plus loin de la camera, donc dans un cadre plus large. Ce calcul le mesure
    au lieu de l'esperer, et il donne au concepteur les deux reglages qui le
    corrigeraient s'il le souhaite. Il n'echoue pas le build : la largeur de 28 m
    est une exigence du brief, pas une variable de la forge.
    """
    tan_v = math.tan(CAM_FOV_V * 0.5)
    tan_h = tan_v * CAM_ASPECT
    t = (CAM_POS.y - deck_y) / -CAM_FORWARD.y
    half_frame = tan_h * t
    return {
        "depth": t,
        "frame_width": 2.0 * half_frame,
        "coverage": HALF_WIDTH / half_frame,
        "fov_for_full": 2.0 * math.degrees(
            math.atan(math.atan2(HALF_WIDTH, t) and
                      (HALF_WIDTH / t) / CAM_ASPECT)),
        "cam_y_for_full": (HALF_WIDTH / tan_h) * -CAM_FORWARD.y + deck_y,
    }


# ==========================================================================
# Orchestration
# ==========================================================================


def build() -> dict:
    ak.reset_scene()
    ak.set_faction(ak.FACTION_NULL_CHOIR)
    sections: list[tuple[bpy.types.Object, list]] = []
    counts: list[dict] = []
    for index in range(SECTION_COUNT):
        obj, anchors, count = build_section(index)
        sections.append((obj, anchors))
        counts.append(count)
    report = export(sections, OUTPUT)
    report["counts"] = counts
    return report


def _print_report(report: dict) -> None:
    print("\n--- long_cortege : mesures relevees sur le .glb PRODUIT ---")
    print(f"  {'troncon':<12} {'tri':>7} {'%budget':>8}  "
          f"{'z monde':>18}  {'bbox (l x h x L)':>24}  sommet")
    for number in range(1, SECTION_COUNT + 1):
        name = f"Section_{number:02d}"
        s = report["sections"][name]
        print(f"  {name:<12} {s['triangles']:>7} "
              f"{100.0 * s['triangles'] / TRI_BUDGET_SECTION:>7.1f}%  "
              f"[{s['min'][2]:+9.2f} {s['max'][2]:+7.2f}]  "
              f"{s['size'][0]:7.2f} x {s['size'][1]:5.2f} x {s['size'][2]:7.2f}  "
              f"{s['max'][1]:+7.3f}")
    print(f"  {'TOTAL':<12} {report['triangles']:>7} "
          f"{100.0 * report['triangles'] / TRI_BUDGET_TOTAL:>7.1f}%   "
          f"largeur {report['width']:.4f} m, sommet {report['top']:+.3f} "
          f"(plafond {CEILING_Y})")
    for label in ("plaques", "nervures", "lisses", "greffes", "pastilles",
                  "plateformes", "baies"):
        line = " ".join(f"{c.get(label, 0):>5}" for c in report["counts"])
        total = sum(c.get(label, 0) for c in report["counts"])
        print(f"  modules {label:<12} {line}   = {total}")

    print("\n  densite de texels (valeurs singulieres, triangle par triangle)")
    for name in sorted(report["density"]):
        d = report["density"][name]
        if not d:
            continue
        target = AMBRY_TEXELS_PER_METER if name == "Ambry" else HULL_TEXELS_PER_METER
        print(f"    {name:<12} cible {target:.3f} t/m ({1 / target:5.2f} m/tuile) | "
              f"mesure {d['tiles_per_m_min']:.3f} a {d['tiles_per_m_max']:.3f}, "
              f"moyenne {d['tiles_per_m_mean']:.3f} t/m "
              f"({d['m_per_tile_mean']:.2f} m/tuile), "
              f"anisotropie max {d['anisotropy_max']:.2f}")

    print(f"\n  primitives : {report['primitives'][0]}/{report['primitives'][2]} "
          f"TEXCOORD_0, {report['primitives'][1]}/{report['primitives'][2]} TANGENT")

    # ⚠️ La repartition en AIRE, et non en triangles : c'est elle qui dit combien
    # de PIXELS un materiau prendra. Le rendu precedent l'a prouve a ses depens —
    # `AA_Trim` faisait moins de 6 pct de l'aire dans la version qui lisait comme
    # une piste d'aeroport. Un chiffre imprime a chaque build est ce qui permet de
    # comparer deux forges au lieu de les regarder l'une apres l'autre.
    print(f"\n  repartition en aire des {len(report['materials'])} materiaux "
          "assignes (relevee sur le .glb)")
    total = report["total_area"] or 1.0
    for name, area in sorted(report["area_by_material"].items(),
                             key=lambda kv: -kv[1]):
        flag = "   <- propre a Ambry" if name == AMBRY_HULL else ""
        print(f"    {name:<20} {area:10.1f} m2   {100.0 * area / total:6.2f} %{flag}")
    print(f"    {'TOTAL':<20} {total:10.1f} m2")
    print(f"  emissif    : {100.0 * report['emissive_ratio']:.2f} % de l'aire totale")
    print(f"  octets     : {report['bytes']}")

    print("\n  marqueurs (position LOCALE au troncon, repere Godot)")
    for name in _expected_markers():
        owner, translation = report["markers"][name]
        print(f"    {name:<11} {owner}  "
              f"({translation[0]:+7.2f}, {translation[1]:+7.3f}, {translation[2]:+8.2f})")

    ambry = report["counts"][-1]
    marks = ambry["ambry_stats"]
    d = ambry["ambry_density"]
    print(f"\n  Ambry : {ambry['ambry']} faces avant fusion, emprise "
          f"x {marks['footprint'][0]}, s {marks['footprint'][1]}")
    print(f"    sommets : modules {marks['module_top']:+.3f}, serre "
          f"{marks['greenhouse_top']:+.3f}, mat {marks['mast_top']:+.3f}")
    print(f"    densite COMPLETE (mesure Blender, bequilles comprises) : "
          f"{d['tiles_per_m_min']:.3f} a {d['tiles_per_m_max']:.3f}, moyenne "
          f"{d['tiles_per_m_mean']:.3f} tuile/m, anisotropie {d['anisotropy_max']:.2f}")
    frame = _frame_coverage(-4.30)
    print(f"\n  cadrage a la camera du jeu (0, 14, 5) / FOV 62 :")
    print(f"    pont a Y = -4.30, profondeur {frame['depth']:.2f} m, "
          f"cadre {frame['frame_width']:.2f} m de large")
    print(f"    la coque de 28 m en couvre {100.0 * frame['coverage']:.1f} % — "
          f"bord a bord demanderait FOV {frame['fov_for_full']:.1f} deg "
          f"ou une camera a Y = {frame['cam_y_for_full']:.2f}")


def main() -> None:
    report = build()
    _print_report(report)
    if "--plate" in sys.argv:
        render_plate(report)


# ==========================================================================
# Planche de recette — `--plate`
# ==========================================================================
# Un livrable de la forge n'est pas un asset valide tant qu'il n'a pas ete rendu et
# REGARDE (ADR-0006). NEUF vignettes : la perspective du jeu avec le Specter-9 reel a
# l'echelle, les cinq troncons de dessus a la MEME echelle, une elevation du troncon
# 5 ou le plafond Y = -3 est materialise, LE CONTRASTE D'AMBRY (BRIEF-0090 : elle et
# le borde dans le MEME cadre, sans quoi rien n'est prouve), et le damier UV.

TILE_W = 1440
SCENE_H = 600
TOP_H = 404          # 1440 / 404 = 3,564 -> 100 m sur 28,05 m
ELEV_H = 340
UV_H = 404
SAMPLES = 28

BACKDROP = (0.012, 0.016, 0.035, 1.0)
AMBIENT = tuple(c * 0.8 for c in (0.55, 0.62, 0.78))
GAME_LIGHTS = (
    ("Key", Vector((0.329, -0.8192, -0.4698)), 1.55, (1.0, 0.976, 0.925)),
    ("Rim", Vector((-0.0819, -0.342, 0.9361)), 0.70, (0.596, 0.855, 1.0)),
    ("Fill", Vector((-0.4, -0.449, -0.799)), 0.55, (0.85, 0.91, 1.0)),
)


def _to_blender(v: Vector) -> Vector:
    """Repere Godot -> repere Blender apres import glTF : (x, y, z) -> (x, -z, y)."""
    return Vector((v.x, -v.z, v.y))


def _plate_reset() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    world = bpy.data.worlds.new("plate")
    world.use_nodes = True
    tree = world.node_tree
    tree.nodes.clear()
    output = tree.nodes.new("ShaderNodeOutputWorld")
    mix = tree.nodes.new("ShaderNodeMixShader")
    path = tree.nodes.new("ShaderNodeLightPath")
    sky = tree.nodes.new("ShaderNodeBackground")
    ambient = tree.nodes.new("ShaderNodeBackground")
    sky.inputs[0].default_value = BACKDROP
    ambient.inputs[0].default_value = (*AMBIENT, 1.0)
    tree.links.new(path.outputs["Is Camera Ray"], mix.inputs[0])
    tree.links.new(ambient.outputs[0], mix.inputs[1])
    tree.links.new(sky.outputs[0], mix.inputs[2])
    tree.links.new(mix.outputs[0], output.inputs[0])
    scene = bpy.context.scene
    scene.world = world
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = SAMPLES
    scene.cycles.use_denoising = True
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    # AgX desature violemment les hautes lumieres : le magenta de l'arete
    # ressortirait blanc et la planche mentirait dans le sens flatteur.
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"


def _plate_lights() -> None:
    """Les trois directionnelles du jeu, et AUCUNE ombre portee.

    En jeu `directional_shadow_max_distance` vaut 40 : une coque de 500 m ne recoit
    d'ombre que sur sa portion la plus proche. Laisser Cycles en projeter validerait
    un relief qui ne se lit QUE par ses ombres — exactement le piege a eviter.
    """
    for name, direction, energy, color in GAME_LIGHTS:
        data = bpy.data.lights.new(name, type="SUN")
        # Godot : L = albedo * energie * N.L. Cycles : L = albedo * force * N.L / pi.
        data.energy = energy * math.pi
        data.color = color
        data.angle = 0.0
        light = bpy.data.objects.new(name, data)
        light.rotation_euler = _to_blender(direction).to_track_quat("-Z", "Y").to_euler()
        bpy.context.collection.objects.link(light)


def _ceiling_slab(z0: float, z1: float) -> None:
    """Le plafond `CEILING_Y`, materialise POUR LA SEULE PLANCHE.

    Une dalle de 30 cm et non un plan : vue de tribord, un plan d'epaisseur nulle ne
    rend aucun pixel. Rien de tout cela ne part dans le `.glb`.
    """
    bm = bmesh.new()
    corners = ((-16.0, z0), (16.0, z0), (16.0, z1), (-16.0, z1))
    rings = []
    for y in (CEILING_Y - 0.30, CEILING_Y):
        rings.append([bm.verts.new(_to_blender(Vector((x, y, z)))) for x, z in corners])
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[1])))
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((rings[0][i], rings[0][j], rings[1][j], rings[1][i]))
    mesh = bpy.data.meshes.new("Ceiling")
    material = bpy.data.materials.new("Ceiling")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs[0].default_value = (0.90, 0.72, 0.30, 1.0)
    emission.inputs[1].default_value = 2.2
    out = nodes.new("ShaderNodeOutputMaterial")
    material.node_tree.links.new(emission.outputs[0], out.inputs[0])
    mesh.materials.append(material)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("Ceiling", mesh)
    # ⚠️ Elle ne doit ni ombrer NI ECLAIRER : sur le premier tirage, ses 2,2 unites
    # d'emission doraient toute la partie haute d'Ambry et la planche mentait sur
    # la couleur du seul element clair du decor.
    obj.visible_shadow = False
    obj.visible_diffuse = False
    obj.visible_glossy = False
    obj.visible_transmission = False
    bpy.context.collection.objects.link(obj)


def _plate_camera(name: str, position: Vector, forward: Vector, up: Vector,
                  fov: float, ortho: float | None = None) -> bpy.types.Object:
    data = bpy.data.cameras.new(name)
    data.lens_unit = "FOV"
    data.sensor_fit = "VERTICAL"
    data.angle_y = fov
    if ortho is not None:
        data.type = "ORTHO"
        data.ortho_scale = ortho
    # ⚠️ Le decor fait 500 m : le clip_end par defaut (100 m) le couperait en
    # deux, proprement et sans le dire.
    data.clip_start = 0.05
    data.clip_end = 1600.0
    camera = bpy.data.objects.new(name, data)
    right = forward.cross(up).normalized()
    camera.matrix_world = Matrix((
        (right.x, up.x, -forward.x, position.x),
        (right.y, up.y, -forward.y, position.y),
        (right.z, up.z, -forward.z, position.z),
        (0.0, 0.0, 0.0, 1.0),
    ))
    bpy.context.collection.objects.link(camera)
    bpy.context.scene.camera = camera
    return camera


def _import(path: str, name: str, position: Vector, yaw: float = 0.0) -> list:
    """Importe un `.glb` et le suspend a un porteur pose a la position DE JEU.

    On ne renomme ni ne deplace les objets importes : ce decor a cinq racines et
    trente marqueurs ; les ramener a la meme position les empilerait a l'origine.
    """
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    fresh = [o for o in bpy.context.scene.objects if o not in before]
    holder = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(holder)
    holder.location = _to_blender(position)
    holder.rotation_euler = Euler((0.0, 0.0, yaw), "XYZ")
    for obj in fresh:
        if obj.parent is None:
            obj.parent = holder
            obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.visible_shadow = False
    return fresh


def _label(camera, text: str, u: float, v: float, height: float,
           width: int, tile_height: int, color=(1.0, 1.0, 1.0)) -> None:
    """Une legende parentee a la camera : pas de projection a calculer.

    `u`, `v` et `height` sont en FRACTION du cadre, jamais en metres : les huit
    cameras de cette planche vont de 62 deg de champ a une orthographique de 106 m,
    et une taille en metres aurait donne un texte illisible sur les unes et
    debordant sur les autres.
    """
    curve = bpy.data.curves.new(text, type="FONT")
    curve.body = text
    obj = bpy.data.objects.new("label_" + text[:14], curve)
    material = bpy.data.materials.new("label_" + text[:14])
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs[0].default_value = (*color, 1.0)
    emission.inputs[1].default_value = 4.0
    out = nodes.new("ShaderNodeOutputMaterial")
    material.node_tree.links.new(emission.outputs[0], out.inputs[0])
    obj.data.materials.append(material)
    obj.parent = camera
    depth = 1.0
    if camera.data.type == "ORTHO":
        half_h = camera.data.ortho_scale * 0.5
    else:
        half_h = math.tan(camera.data.angle_y * 0.5) * depth
    half_w = half_h * width / tile_height
    curve.size = height * 2.0 * half_h
    obj.location = (u * half_w, v * half_h, -depth)
    obj.visible_shadow = False
    bpy.context.collection.objects.link(obj)


def _render(path: str, width: int, height: int) -> None:
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def _checker_material() -> bpy.types.Material:
    """Damier UV : grande case = UNE tuile de 5 m, petite case = 1/8 de tuile.

    Sans lui, un etirement ne se decouvre qu'apres la texture generee, donc trop
    tard. Le damier n'existe QUE dans ce rendu : le `.glb` ne porte aucune texture.
    """
    mat = bpy.data.materials.new("UV_Checker")
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()
    coord = tree.nodes.new("ShaderNodeTexCoord")
    fine = tree.nodes.new("ShaderNodeTexChecker")
    fine.inputs["Scale"].default_value = 16.0
    fine.inputs["Color1"].default_value = (0.62, 0.62, 0.64, 1.0)
    fine.inputs["Color2"].default_value = (0.16, 0.16, 0.18, 1.0)
    coarse = tree.nodes.new("ShaderNodeTexChecker")
    coarse.inputs["Scale"].default_value = 1.0
    coarse.inputs["Color1"].default_value = (1.0, 0.86, 0.55, 1.0)
    coarse.inputs["Color2"].default_value = (0.55, 0.72, 1.0, 1.0)
    mix = tree.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    mix.inputs["Fac"].default_value = 1.0
    bsdf = tree.nodes.new("ShaderNodeBsdfDiffuse")
    out = tree.nodes.new("ShaderNodeOutputMaterial")
    tree.links.new(coord.outputs["UV"], fine.inputs["Vector"])
    tree.links.new(coord.outputs["UV"], coarse.inputs["Vector"])
    tree.links.new(fine.outputs["Color"], mix.inputs["Color1"])
    tree.links.new(coarse.outputs["Color"], mix.inputs["Color2"])
    tree.links.new(mix.outputs["Color"], bsdf.inputs["Color"])
    tree.links.new(bsdf.outputs[0], out.inputs[0])
    return mat


def _apply_checker(objects: list) -> None:
    checker = _checker_material()
    for obj in objects:
        if obj.type != "MESH":
            continue
        obj.data.materials.clear()
        obj.data.materials.append(checker)


def _tile_scene(path: str, report: dict, checker: bool) -> None:
    """La perspective du jeu, au-dessus du troncon 3, avec le Specter-9 reel."""
    _plate_reset()
    # Le decor est importe DECALE pour que le milieu du troncon 3 (z = -250) tombe
    # a z = 0, la ou la camera du jeu regarde.
    decor = _import(OUTPUT, "Decor", Vector((0.0, 0.0, 250.0)))
    fighter = _import(FIGHTER, "Player", Vector((0.0, 0.0, 3.4)))
    if checker:
        _apply_checker(decor + fighter)
    _plate_lights()
    camera = _plate_camera("game", _to_blender(CAM_POS), _to_blender(CAM_FORWARD),
                           _to_blender(CAM_UP), CAM_FOV_V)
    height = UV_H if checker else SCENE_H
    if checker:
        _label(camera, "DAMIER UV — grande case = 1 tuile de 5,00 m, petite = 62,5 cm",
               -0.96, 0.86, 0.048, TILE_W, height, (1.0, 0.88, 0.55))
        _label(camera, f"projection en boite {HULL_TEXELS_PER_METER:.2f} tuile/m ; "
                       f"anisotropie max mesuree "
                       f"{report['density']['Section_03']['anisotropy_max']:.2f}",
               -0.96, 0.74, 0.036, TILE_W, height)
    else:
        _label(camera, "PERSPECTIVE DU JEU — camera (0, 14, 5), FOV 62, "
                       "troncon 3 au milieu du cadre",
               -0.96, 0.86, 0.045, TILE_W, height, (1.0, 0.88, 0.55))
        frame = _frame_coverage(-4.30)
        _label(camera, f"Specter-9 REEL a l'echelle ; la coque de 28 m couvre "
                       f"{100.0 * frame['coverage']:.0f} % de la largeur du cadre",
               -0.96, 0.76, 0.034, TILE_W, height)
        _label(camera, f"{report['triangles']} triangles pour 500 x 28 m "
                       f"= {report['triangles'] / (SHIP_LENGTH * 28.0):.1f} tri/m2",
               -0.96, -0.90, 0.032, TILE_W, height, (0.72, 0.84, 1.0))
    _render(path, TILE_W, height)


def _tile_top(path: str, report: dict, index: int) -> None:
    """Un troncon vu de dessus, orthographique, proue a GAUCHE, tribord en BAS."""
    _plate_reset()
    _import(OUTPUT, "Decor", Vector((0.0, 0.0, 0.0)))
    _plate_lights()
    centre = -(index + 0.5) * SECTION_LENGTH
    ortho = 28.05
    camera = _plate_camera(
        f"top{index}", _to_blender(Vector((0.0, 60.0, centre))),
        _to_blender(Vector((0.0, -1.0, 0.0))), _to_blender(Vector((-1.0, 0.0, 0.0))),
        math.radians(30.0), ortho=ortho)
    name = f"Section_{index + 1:02d}"
    s = report["sections"][name]
    counts = report["counts"][index]
    _label(camera, f"{name}  ·  z monde [{s['min'][2]:+.0f} , {s['max'][2]:+.0f}]  ·  "
                   f"{s['triangles']} tri  ·  sommet Y {s['max'][1]:+.2f}",
           -0.985, 0.80, 0.075, TILE_W, TOP_H, (1.0, 0.88, 0.55))
    _label(camera, f"{counts['plaques']} plaques · {counts['nervures']} nervures · "
                   f"{counts['greffes']} greffes · {counts['pastilles']} pastilles · "
                   f"{counts['plateformes']} tourelles · {counts['baies']} baie(s)",
           -0.985, -0.86, 0.058, TILE_W, TOP_H)
    _label(camera, "proue", -0.985, 0.52, 0.06, TILE_W, TOP_H, (0.72, 0.84, 1.0))
    _label(camera, "poupe", 0.90, 0.52, 0.06, TILE_W, TOP_H, (0.72, 0.84, 1.0))
    _render(path, TILE_W, TOP_H)


def _tile_elevation(path: str, report: dict) -> None:
    """Le troncon 5 de tribord, avec la dalle du plafond Y = -3.

    C'est la seule facon de repondre a « rien ne monte dans le plan de jeu »
    autrement que par un chiffre : on voit la dalle, et on voit que rien ne la
    touche — pas meme l'antenne d'Ambry, qui est ce que la coque a de plus haut.
    """
    _plate_reset()
    _import(OUTPUT, "Decor", Vector((0.0, 0.0, 0.0)))
    _ceiling_slab(-500.0, -400.0)
    _plate_lights()
    # ⚠️ Cadre serre sur Ambry (43 m sur 500) et non sur le troncon entier : a
    # 100 m de large pour 9 m de haut, l'elevation rendait un trait, et la seule
    # chose qu'elle devait prouver — que RIEN ne touche la dalle — y etait
    # illisible.
    # 8,0 m de haut et non 7,6, cadres a -6,10 : la dalle doit tomber DANS le
    # cadre et non sous la legende, sinon la planche ne prouve plus rien.
    ortho = 8.0
    centre = -(AMBRY_S[0] + AMBRY_S[1]) * 0.5
    camera = _plate_camera(
        "elev", _to_blender(Vector((90.0, -6.10, centre))),
        _to_blender(Vector((-1.0, 0.0, 0.0))), _to_blender(Vector((0.0, 1.0, 0.0))),
        math.radians(30.0), ortho=ortho)
    _label(camera, f"ELEVATION TRIBORD SUR AMBRY (34 m) — la dalle ambre EST le "
                   f"plafond du jeu Y = {CEILING_Y:.0f}",
           -0.985, 0.88, 0.062, TILE_W, ELEV_H, (1.0, 0.88, 0.55))
    _label(camera, f"sommet de la coque entiere Y = {report['top']:+.3f} "
                   f"(marge {CEILING_Y - report['top']:.3f} m) — le mat d'antenne "
                   f"est le point le plus haut des 500 m",
           -0.985, -0.90, 0.055, TILE_W, ELEV_H)
    _render(path, TILE_W, ELEV_H)


def _tile_ambry(path: str, report: dict) -> None:
    """AMBRY ET LE BORDE SUR LA MEME VIGNETTE — l'exigence de BRIEF-0090.

    Deux vignettes separees ne prouveraient rien : ce qui est en jeu, c'est un
    CONTRASTE, et un contraste ne se juge que dans un seul cadre, a l'eclairage
    du jeu et a la perspective du jeu. On prend donc EXACTEMENT la camera de
    `graybox.tscn` — pas un cadrage flatteur — et l'on decale le decor pour
    qu'Ambry tombe au centre du champ. Le borde de l'Unisson occupe alors toute
    la moitie babord du cadre, la crete lumineuse passe au milieu, et l'on voit
    du meme coup les deux choses qui comptent :

      * Ambry se detache-t-elle de la masse anthracite ? (c'est l'objet du brief)
      * son gris-ivoire vole-t-il la lecture au reste ? (c'est le piege du brief)

    Le Specter-9 REEL y est a sa taille et a sa place de jeu (ADR-0025) : si les
    344 m2 d'Ambry passaient devant le chasseur, cela se verrait ici.
    """
    _plate_reset()
    # Le decor est decale pour que le CENTRE d'Ambry tombe la ou la camera du jeu
    # regarde le pont — calcule, jamais approche a l'œil.
    deck = -4.30
    aim_z = CAM_POS.z + CAM_FORWARD.z * _frame_coverage(deck)["depth"]
    shift = 0.5 * (AMBRY_S[0] + AMBRY_S[1]) + aim_z
    decor = _import(OUTPUT, "Decor", Vector((0.0, 0.0, shift)))
    _import(FIGHTER, "Player", Vector((0.0, 0.0, 3.4)))
    _plate_lights()
    camera = _plate_camera("ambry", _to_blender(CAM_POS), _to_blender(CAM_FORWARD),
                           _to_blender(CAM_UP), CAM_FOV_V)
    area = report["area_by_material"].get(AMBRY_HULL, 0.0)
    share = 100.0 * area / (report["total_area"] or 1.0)
    _label(camera, "AMBRY ET LE BORDE DANS LE MEME CADRE — perspective du jeu, "
                   "tribord a droite",
           -0.96, 0.86, 0.045, TILE_W, SCENE_H, (1.0, 0.88, 0.55))
    _label(camera, f"{AMBRY_HULL} {AMBRY_HULL_HEX} (coques Helios Vanguard) = "
                   f"{area:.0f} m2, soit {share:.2f} % de l'aire — le borde reste "
                   f"anthracite {ak.PALETTES[ak.FACTION_NULL_CHOIR]['hull'].upper()}",
           -0.96, 0.76, 0.032, TILE_W, SCENE_H)
    _label(camera, f"depliage propre : {AMBRY_TEXELS_PER_METER:.3f} tuile/m sur "
                   f"Ambry ({1 / AMBRY_TEXELS_PER_METER:.2f} m/tuile) contre "
                   f"{HULL_TEXELS_PER_METER:.3f} sur le borde "
                   f"({1 / HULL_TEXELS_PER_METER:.2f} m/tuile)",
           -0.96, -0.84, 0.032, TILE_W, SCENE_H, (0.72, 0.84, 1.0))
    _label(camera, "Specter-9 reel a sa place de jeu : les balles doivent se lire "
                   "par-dessus (ADR-0006)",
           -0.96, -0.91, 0.030, TILE_W, SCENE_H, (0.72, 0.84, 1.0))
    _render(path, TILE_W, SCENE_H)


def _compose(tiles: list[tuple[str, int]], out: str) -> None:
    """Empile les vignettes. Pas de PIL dans le Python de Blender : numpy."""
    import numpy as np

    height = sum(h for _, h in tiles)
    sheet = np.zeros((height, TILE_W, 4), dtype=np.float32)
    sheet[..., 3] = 1.0
    cursor = 0
    for path, tile_h in tiles:
        image = bpy.data.images.load(path)
        buffer = np.empty(len(image.pixels), dtype=np.float32)
        image.pixels.foreach_get(buffer)
        tile = buffer.reshape(tile_h, TILE_W, 4)
        # Les images Blender sont stockees de bas en haut : ligne 0 = bas.
        top = height - cursor - tile_h
        sheet[top:top + tile_h] = tile
        cursor += tile_h
        bpy.data.images.remove(image)
    result = bpy.data.images.new("sheet", width=TILE_W, height=height)
    result.pixels.foreach_set(sheet.reshape(-1))
    result.filepath_raw = out
    result.file_format = "PNG"
    result.save()
    bpy.data.images.remove(result)
    print(f"-> {out}  ({TILE_W} x {height})")


def render_plate(report: dict) -> None:
    staging = tempfile.mkdtemp(prefix="aegis-cortege-plate-")
    tiles: list[tuple[str, int]] = []
    try:
        path = os.path.join(staging, "scene.png")
        _tile_scene(path, report, checker=False)
        tiles.append((path, SCENE_H))
        for index in range(SECTION_COUNT):
            path = os.path.join(staging, f"top{index}.png")
            _tile_top(path, report, index)
            tiles.append((path, TOP_H))
        path = os.path.join(staging, "elev.png")
        _tile_elevation(path, report)
        tiles.append((path, ELEV_H))
        path = os.path.join(staging, "ambry.png")
        _tile_ambry(path, report)
        tiles.append((path, SCENE_H))
        path = os.path.join(staging, "uv.png")
        _tile_scene(path, report, checker=True)
        tiles.append((path, UV_H))
        os.makedirs(os.path.dirname(PLATE), exist_ok=True)
        _compose(tiles, PLATE)
    finally:
        for leftover in os.listdir(staging):
            os.remove(os.path.join(staging, leftover))
        os.rmdir(staging)


if __name__ == "__main__":
    main()
