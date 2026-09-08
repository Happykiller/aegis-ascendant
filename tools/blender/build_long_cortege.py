"""build_long_cortege.py — la coque du Long Cortege, en cinq troncons (BRIEF-0089).

    blender-aegis -b -P tools/blender/build_long_cortege.py
    blender-aegis -b -P tools/blender/build_long_cortege.py -- --plate
    blender-aegis -b -P tools/blender/build_long_cortege.py -- --branches
    blender-aegis -b -P tools/blender/build_long_cortege.py -- --nodes
    blender-aegis -b -t 1 -P tools/blender/build_long_cortege.py -- --complexe \
        --avant <glb_de_reference>        # ⚠️ -t 1 : la planche REBATIT le .glb
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

⚠️ DEUX FAMILLES ONT DISPARU DE CETTE LISTE, ET C'EST LE MEME MOUVEMENT DEUX FOIS :
`baies` (BRIEF-0091) puis `plateformes` (BRIEF-0093). La coque cuisait un socle de
tourelle par marqueur — un disque a cœur magenta que l'operateur a lu comme « un
jeton circulaire ». Elle n'en cuit plus aucun : elle porte le MARQUEUR, et
`turret_kit.glb` porte le socle, la couronne, le bloc et les canons. Un seul kit
fait dix-sept tourelles differentes ; dix-sept copies cuites n'en faisaient qu'une.

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


LE COMPLEXE INDUSTRIEL DU TRONCON 5, ET LE VIDE QU'IL OCCUPE VRAIMENT
====================================================================
Le BRIEF-0111 demande de meubler « 69 m de coque nue » a tribord du troncon 5,
entre les tourelles de s = 410 et s = 478,8. Il y en a **24,5**.

Les 69 m sont mesures sur les MARQUEURS. AMBRY n'en est pas un : c'est une piece
cuite dans la peau, de s = 444,5 a 475,5 sur le meme bord, et aucune table de
marqueurs ne la voit. C'est le meme angle mort qui avait plante une conduite
d'artere dans la Citadelle (`ARTERY_CONDUITS`, station 232) — la Citadelle non
plus n'est pas un marqueur. `_assert_plant_is_clear()` existe pour que ce
constat-la soit desormais fait par une machine, et pas par une capture.

Le complexe occupe donc `s in [418 ; 442,5]`, et c'est la bonne taille : le cadre
de la camera du jeu montre 27 m de pont a la fois, si bien qu'il remplit un ecran
entier dans le sens du defilement.

Trois choses le font lire comme un LIEU plutot que comme de la matiere :
une EMPRISE (un plancher de 0,35 m, un longeron de rive, deux traverses de bout),
deux SEUILS (les portiques, aux deux bouts), et un CŒUR (un bassin de 1,63 m,
declare dans `BASINS` donc creuse par `build_pits()`, avec ses deux bouts clairs).

⚠️ IL NE PASSE PAS PAR `_installation_spans()`, ET C'EST MESURE. Il y a d'abord ete
inscrit — c'est une installation. Mais `MARKER_APRONS` fusionne les emprises SANS
leur x : ouvrir 27,7 m a tribord les ouvre a babord, et le bord d'en face s'est
couvert de quarante-cinq plaques. Le complexe porte donc son propre appareillage,
et les cinq troncons gardent leurs modules semes.


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
# La section transversale — moitie tribord, du CANAL a la quille
# --------------------------------------------------------------------------
# (x, y, materiau du segment qui part de ce point). Le dernier materiau est ignore.
#
# ⚠️ LA CRETE CENTRALE A DISPARU, ET C'EST LE LOT 3 DE BRIEF-0094 EN UNE LIGNE DE
# TABLEAU. Elle culminait a -3,62 et portait sur son arete, EN CONTINU sur 500 m,
# un segment `AA_Emissive_Engine` de 0,28 m double d'un lisere ivoire de 0,64 m.
# Le verdict de l'operateur : « l'artere centrale est beaucoup trop proche d'un
# laser geant ; elle attire davantage l'œil que certaines menaces ». Le defaut
# n'etait pas dans la texture — `TEX-0013` demandait deja « au moins la moitie de
# l'aire sombre » et l'image la respectait — il etait dans la GEOMETRIE, qui
# offrait une bande pleine, posee sur le point le plus haut du vaisseau, a peindre.
#
# La reponse tient en trois cotes, et aucune n'est un gout :
#
#     |x| <= 0,88   FOND du canal a -4,58, plat : 1,76 m de fond utile
#     |x| =  1,00   la paroi, 0,38 m de haut — c'est ce qui fait la TRANCHEE
#     |x| =  1,12   arete interne du rebord, a -4,02
#     |x| <= 1,70   le REBORD mecanique, sombre, 0,58 m de large de chaque bord
#                   -> canal de 2,00 m de large entre les deux rebords
#     |x| =  2,20   pied du bandeau dorsal, sur le pont a -4,26
#
# Le canal est donc ENFONCE de 0,56 m sous l'arete de son rebord et de 0,28 m sous
# le pont : on ne le lit plus comme une bande posee mais comme un creux, et
# l'emissif qu'il porte est au FOND, ou la geometrie l'ombre d'elle-meme.
#
# ⚠️ RIEN NE BOUGE AU-DELA DE x = 2,20, ET C'EST UNE CONTRAINTE DURE. Le brief
# fige les trente marqueurs : « noms, X, Z inchanges ; seul le Y des Spine_NN
# bouge ». Or le Y d'un marqueur de tourelle est ECHANTILLONNE sur la peau
# (`turret_seat_y`, rayon 2,08 m) et celui d'un pont d'envol aussi
# (`bay_mouth_y`). Le marqueur le plus interieur est `Turret_05`/`Turret_08` a
# |x| = 5,60 : son emprise descend a |x| = 3,52. Tant que le profil est IDENTIQUE
# au-dela de 2,20, les vingt-quatre Y de tourelle et de pont sont inchanges au
# micron — verifie sur le binaire, et c'est ce qui permet de ne pas rejouer
# l'arbitrage `ACCEPTED_PAD_BAY_PROXIMITY` ni le cliquet de plafond du kit.
#
# ⚠️ LA FACETTE EXTERIEURE N'EST PLUS VIOLETTE (lot 4). Les deux segments 11 et 12
# faisaient 3,00 m de developpe par bord, EN CONTINU sur 500 m : a eux seuls
# 3 000 m2 d'`AA_Panel`, soit les « gros rectangles violets poses partout » qui
# sabotent la hierarchie. Le violet ne survit plus que sur des VOLUMES — les
# greffes — ou il dit quelque chose. Meme lecon que pour l'ivoire au BRIEF-0089 :
# sur 500 m, un materiau qui suit une arete CONTINUE occupe plus de pixels que
# n'importe quelle piece, et le compte de triangles ne le dit pas.
PROFILE_BASE: tuple[tuple[float, float, str], ...] = (
    (0.00, -4.58, "AA_Greeble"),           # 0  FOND du canal, sur l'axe
    (0.88, -4.58, "AA_Greeble"),           # 1  fond, pied de paroi
    (1.00, -4.20, "AA_Greeble"),           # 2  paroi du canal
    (1.12, -4.02, "AA_Greeble"),           # 3  arete interne du rebord
    (1.70, -4.05, "AA_Greeble"),           # 4  dessus du REBORD, sombre
    (2.05, -4.16, "AA_Hull"),              # 5  talus du bandeau dorsal
    (2.20, -4.26, "AA_Hull"),              # 6  pied, sur le pont — INCHANGE
    (5.10, -4.30, "AA_Hull"),              # 7  pont interieur
    # ⚠️ La contremarche de chine repasse en `AA_Hull` (elle etait `AA_Greeble`).
    # `AA_Greeble` est le noir de CREUX (#141419) : en laisser une bande de 0,81 m
    # de developpe filer sur 500 m le long de la chine mettait deux rubans
    # presque noirs dans le meme cadre — celui de la chine et celui de la
    # tranchee — et la tranchee cessait d'etre LE creux du vaisseau. Un
    # changement de PLAN se lit a la lumiere ; un creux, a sa matiere.
    (6.80, -4.34, "AA_Hull"),              # 8  levre de chine
    (7.35, -4.94, "AA_Hull"),              # 9  pont median (les baies)
    (10.30, -4.99, "AA_Hull"),             # 10 pont median
    (12.35, -5.10, "AA_Hull"),             # 11 facette exterieure (etait AA_Panel)
    (13.35, -6.35, "AA_Hull"),             # 12 facette basse   (etait AA_Panel)
    (13.88, -7.65, "AA_Hull"),             # 13 lisse d'epaule
    (14.00, -8.95, "AA_Greeble"),          # 14 BORD — 14,00 exactement
    (13.30, -10.60, "AA_Greeble"),         # 15 sous-chine
    (10.40, -11.90, "AA_Greeble"),         # 16 pente de fond
    (5.00, -12.40, "AA_Greeble"),          # 17 fond
    (0.00, -12.60, "AA_Greeble"),          # 18 quille
)
#: Indice du bord de pont (x = 14) DANS `PROFILE_BASE`. `PROFILE` et son
#: `DECK_LAST` sont construits plus bas : les ouvertures de baie imposent des
#: points de subdivision supplementaires, et il faut connaitre `BAYS` pour eux.
DECK_LAST_BASE = 14
#: Pivot vertical du fuseau de proue : la section se contracte autour de lui.
Y_PIVOT = -6.9

#: Bandes plates ou l'on a le droit de poser une plateforme de tourelle ou une
#: plaque : (x_min, x_max) en valeur absolue.
#: ⚠️ 2,55 et non 2,30 : le talus du bandeau dorsal descend jusqu'a 2,20, et une
#: pastille de 0,30 m posee dessus se serait couchee sur la pente.
BAND_INNER = (2.55, 6.60)
BAND_MID = (7.50, 12.10)

# --------------------------------------------------------------------------
# L'ARTERE — le canal, son rebord, ses conduits (BRIEF-0094, priorite 1)
# --------------------------------------------------------------------------
# Les cotes ci-dessous DECRIVENT le profil ci-dessus ; elles ne le pilotent pas.
# `_assert_canal()` verifie a chaque build que les deux disent la meme chose : une
# constante qui derive de la table qu'elle est censee resumer est un piege connu
# de ce fichier (voir `BAY_COAMING_W` et le kit de hangar).

#: Demi-largeur du canal, mesuree entre les aretes internes des deux rebords.
CANAL_HALF = 1.00
#: Demi-largeur du FOND PLAT : c'est la seule zone ou un conduit peut se poser
#: sans se coucher sur la paroi.
CANAL_FLOOR_HALF = 0.88
#: Arete externe du rebord. Au-dela, on est sur le bandeau dorsal.
CANAL_RIM_X = 1.70
CANAL_FLOOR_Y = -4.58
CANAL_RIM_Y = -4.02

#: LES BANDES LUMINEUSES DU FOND, en |x| : quatre voies (deux par bord), de 18 et
#: 12 cm. Le brief demande « 3 ou 4 bandes de 10 a 25 cm, jamais sur toute la
#: largeur ». Total eclaire : 4 x 0,15 m moyen = 0,60 m sur 2,00 m de canal, soit
#: 30 pct de sa largeur — et 0 pct de la peau du pont, ou il n'y a plus rien.
CONDUIT_LANES: tuple[tuple[float, float], ...] = ((0.14, 0.32), (0.48, 0.60))
#: Le conduit affleure : 6 cm au-dessus du fond. Il ne DEPASSE pas, il est SERTI.
CONDUIT_RISE = 0.06
#: ⚠️ LES INTERRUPTIONS SONT LE LIVRABLE, PAS LA BANDE. « Une bande continue sur
#: 500 m est une frontiere de terrain, pas une conduite. » Longueur allumee, puis
#: longueur eteinte, tirees dans ces plages : la cadence est reguliere sans etre
#: un metronome, et les quatre voies ne sont jamais en phase (leur depart est
#: decale par voie et par bord).
CONDUIT_RUN = (5.5, 14.0)
CONDUIT_GAP = (1.6, 4.6)
#: Pas de decoupe des conduits DANS LE FUSEAU DE PROUE, et uniquement la.
#: Le fond du canal y monte de 2,2 cm par metre (le fuseau contracte la section
#: autour de `Y_PIVOT`) : une bande de 14 m posee d'un trait sur le point le plus
#: BAS de ses quatre coins — ce que fait `_surface_box` — s'enterrerait de 26 cm a
#: son extremite haute et disparaitrait sans un mot. Ailleurs le fond est
#: rigoureusement plat et la bande sort d'une seule piece.
CONDUIT_TAPER_STEP = 1.6

#: LES TRAVEES SOMBRES — des poutres qui enjambent le canal et le BARRENT.
#: Elles sont la seconde moitie de « coupe-les par des travees sombres » : la
#: premiere est le trou dans la lumiere, celle-ci est la matiere qui le fait.
#: Une poutre enterree de 0,62 m remplit la tranchee au lieu de la survoler.
BRACE_WIDTH = 0.55
BRACE_RISE = 0.06
BRACE_SINK = 0.62
BRACE_SPACING = (16.0, 30.0)

# --------------------------------------------------------------------------
# Le fuseau de proue — troncon 1 seulement
# --------------------------------------------------------------------------
# (s, echelle laterale, echelle verticale), interpole en smoothstep. Le dernier
# nœud est a s = 88 avec (1, 1) : la derivee d'un smoothstep y est NULLE, donc le
# profil est deja plat 12 m avant la jonction a s = 100. C'est ce qui rend la
# jonction 1-2 invisible ET ce qui autorise l'egalite exacte des deux anneaux.
# --------------------------------------------------------------------------
# LA LARGEUR — le fuseau de proue, PUIS le contour du reste de la coque
# --------------------------------------------------------------------------
# ⚠️ IL Y AVAIT 412 M DE BORDS STRICTEMENT PARALLELES, ET C'ETAIT MESURABLE.
# Cette table s'arretait a s = 88 ; au-dela, `_scales()` rendait (1,0 ; 1,0) et
# la demi-largeur valait `HALF_WIDTH` AU MICRON de 88 a 500. Le constat de
# l'operateur — « casser l'effet piste rectangulaire » — ne decrivait pas une
# impression, il decrivait cette table.
#
# ⚠️ SEUL `kx` VARIE AU-DELA DU FUSEAU, JAMAIS `ky`. La hauteur commande les
# PALIERS du pont (peau a -4,30, contremarche de chine, pont median a -4,99) et
# c'est sur eux que les vingt-quatre Y de marqueurs sont echantillonnes. Faire
# respirer la coque en epaisseur les rejouerait tous, et rejouerait avec eux le
# cliquet de plafond du kit et l'arbitrage `ACCEPTED_PAD_BAY_PROXIMITY`. La
# largeur seule donne le contour demande, et ne coute rien de tout cela.
#
# ⚠️ AUCUNE VARIATION SOUS UN PONT D'ENVOL — ET C'EST UNE CONTRAINTE DURE, TENUE
# PAR `_assert_taper_spares_the_bays()`. Les ouvertures ne sont pas percees : la
# peau est GENEREE trouee, et sa grille passe par des points de profil poses a
# `|x_baie| +/- 3,00`, en dur. Ces points supposent la largeur nominale. Faire
# respirer la coque sous une baie decalerait la peau sans decaler l'ouverture —
# un trou aux mauvaises cotes, en silence.
#
# Les variations vivent donc ENTRE les installations, ce qui est aussi ce que le
# rythme demande : zone calme, evenement, respiration.
#
# Amplitude retenue : -20 a +24 pct, dans la fourchette des consignes (15 a 25).
# Le cadre de la camera fait 41,60 m et la coque nominale 28 m (67,3 pct) : a
# +24 pct elle en couvre 83 pct, a -20 pct 54 pct. Le contour entre et sort du
# cadre sans jamais le remplir.
TAPER: tuple[tuple[float, float, float], ...] = (
    # --- le fuseau de proue, compose a la main (inchange) ---
    (0.0, 0.008, 0.16),
    (5.0, 0.100, 0.26),
    (58.0, 0.940, 0.93),
    (88.0, 1.000, 1.00),
    # --- le contour du reste de la coque ---
    (94.0, 1.000, 1.00),
    (106.0, 0.820, 1.00),   # le col, avant le troncon 2
    (118.0, 1.000, 1.00),
    (134.0, 1.000, 1.00),
    (150.0, 1.210, 1.00),   # premier epaulement
    (165.0, 1.000, 1.00),
    (190.0, 1.000, 1.00),
    (205.0, 0.840, 1.00),   # etranglement
    (220.0, 1.000, 1.00),
    (236.0, 1.000, 1.00),
    (258.0, 1.230, 1.00),   # le grand elargissement du troncon 3
    (282.0, 1.000, 1.00),
    (298.0, 1.000, 1.00),
    (313.0, 0.830, 1.00),   # etranglement
    (328.0, 1.000, 1.00),
    (356.0, 1.000, 1.00),
    (378.0, 1.240, 1.00),   # la plateforme d'artillerie — le point le plus large
    (402.0, 1.000, 1.00),
    # ⚠️ RIEN ENTRE 402 ET 482, ET CE N'EST PAS UN OUBLI. Un epaulement etait
    # ecrit a s = 453 ; il tombait sur AMBRY (446 a 474), l'avant-poste humain
    # greffe sur le borde. Elargir la coque sous elle l'etirait avec, et sa
    # densite de texels chutait a 0,141 tuile/m pour 0,396 exigees — le harnais
    # d'UV l'a refuse. Une greffe ne s'etire pas avec ce qui la porte.
    (482.0, 1.000, 1.00),
    (491.0, 0.800, 1.00),   # la poupe se resserre
    (500.0, 0.860, 1.00),
)
# --------------------------------------------------------------------------
# L'ASYMETRIE — un bord peut etre plus large que l'autre
# --------------------------------------------------------------------------
# ⚠️ `_ring()` CONSTRUISAIT LA MOITIE TRIBORD ET LA RECOPIAIT. Le contour pouvait
# donc respirer (`TAPER`), mais toujours des DEUX cotes a la fois : la planche de
# recette montre cinq troncons rigoureusement symetriques. La consigne 14 demande
# l'inverse — « la coque peut elle-meme etre plus large d'un cote pendant quelques
# dizaines de metres ».
#
# Cette table donne un facteur par BORD, multiplie par celui de `TAPER`. La
# topologie de l'anneau ne change pas d'un point : memes indices, memes materiaux,
# memes drapeaux de pont. Seules les abscisses d'un cote bougent.
#
# ⚠️ LES GARDES SONT PAR BORD, ET C'EST CE QUI REND LE LOT POSSIBLE. Une baie a
# babord ne craint rien d'un epaulement a tribord. Les plateaux ou `TAPER` vaut 1
# sont courts (16 a 28 m) une fois les installations protegees — mais « quelques
# dizaines de metres » est exactement ce que la consigne demande, et c'est ce
# qu'ils offrent.
#
# ⚠️ AUCUN CUMUL AVEC UN EVENEMENT DE `TAPER`. Les quatre asymetries sont posees
# sur des plateaux ou `kx` vaut 1 : sans cela, un epaulement de +19 pct sur une
# coque deja elargie de +24 pct sortirait des +25 pct que les consignes bornent,
# et le contrat de largeur le refuserait.
#
# (s, tribord, babord) — tribord = x positif.
ASYMMETRY: tuple[tuple[float, float, float], ...] = (
    (0.0, 1.000, 1.000),
    (165.0, 1.000, 1.000),
    (177.0, 1.000, 0.830),   # babord se pince, tribord ne bouge pas
    (190.0, 1.000, 1.000),
    (328.0, 1.000, 1.000),
    (342.0, 1.190, 1.000),   # tribord s'epaule
    (356.0, 1.000, 1.000),
    (402.0, 1.000, 1.000),
    (413.0, 1.000, 1.160),   # babord bombe...
    (424.0, 1.000, 1.000),
    (426.0, 1.000, 1.000),
    (434.0, 0.850, 1.000),   # ...et tribord se pince juste apres : un decalage
    (442.0, 1.000, 1.000),
    (500.0, 1.000, 1.000),
)

#: Fin du FUSEAU DE PROUE — et non de la table. ⚠️ LES DEUX ONT ETE LE MEME
#: NOMBRE, ET NE LE SONT PLUS. Les X de marqueurs au-dela de cette station ont
#: ete poses a la main sur une coque ou `kx` valait 1 : ils se lisent donc comme
#: des X A LARGEUR NOMINALE, que `_marker_x()` rapporte a la largeur locale. En
#: deca, le fuseau est compose a la main, marqueurs compris — on n'y touche pas.
PROW_TAPER_END = 88.0
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
#:
#: ⚠️ DEUX `s` ONT BOUGE LE 2026-08-29 (BRIEF-0092), ET RIEN D'AUTRE. `Turret_02`
#: passe de 84 a 76, `Turret_05` de 176 a 173 : leurs socles se tenaient dans
#: l'emprise d'un pont d'envol devenu une VRAIE ouverture (BRIEF-0091), le
#: premier avec son centre au-dessus du vide. Le nombre, les noms et l'ordre des
#: 30 marqueurs sont inchanges — le moteur les resout PAR NOM a chaque image, un
#: deplacement est sur, une disparition ou un renommage casserait le niveau en
#: silence. Le `x` ne bouge pas non plus : c'est lui qui met le socle sur une
#: bande plate.
TURRETS: tuple[tuple[float, float], ...] = (
    (68.0, -6.0), (73.3, 9.4),                                     # troncon 1
    (120.7, 9.6), (152.1, -9.2), (173.0, 5.6),                    # troncon 2
    (216.6, -8.4), (258.0, 9.8), (263.0, -5.6),                   # troncon 3
    (323.0, 8.2), (336.0, -9.8), (375.0, 10.1), (380.0, -6.2),    # troncon 4
    (410.0, 8.8), (415.2, -9.4), (463.3, -6.0),                   # troncon 5
    (470.0, -10.2), (478.8, 9.0),
)
#: Rayon hors-tout de la plateforme, par troncon : « de plus en plus massives »
#: (maquette 3). 2,30 m a la proue, 3,20 m au troncon 5.
PAD_RADIUS = (2.30, 2.55, 2.75, 3.00, 3.20)

#: 7 ponts d'envol, vers l'exterieur (pont median + facette). Ce sont des
#: OUVERTURES depuis BRIEF-0091 : la peau n'existe pas a leur emprise.
BAYS: tuple[tuple[float, float], ...] = (
    (86.4, 9.0),                                                  # troncon 1
    (126.0, -9.2), (180.7, 9.2),                                  # troncon 2
    (224.6, -9.3), (290.0, 9.3),                                  # troncon 3
    (344.3, -9.3),                                                # troncon 4
    (450.0, -9.3),                                                # troncon 5
)

# --------------------------------------------------------------------------
# LES OUVERTURES DE PONT D'ENVOL — la peau est GENEREE trouee (BRIEF-0091)
# --------------------------------------------------------------------------
# ⚠️ RETOUR SUR UNE DECISION PRISE DANS CE FICHIER, ET LA RAISON EST CHIFFREE.
# BRIEF-0089 livrait un coaming POSE sur le borde, et l'argumentaire tenait :
# « une VRAIE cavite demanderait de trouer la peau (booleen, donc non
# deterministe, et une peau non manifold) ». Il tenait POUR 0,78 m. La planche
# de consignes demande 1,5 a 2,5 m de profondeur, et il n'y a que 1,1 m entre la
# peau (-4,30) et le plafond du plan de jeu (-3,20) :
#
#     -3,20  plafond du plan de jeu — RIEN ne monte au-dessus
#     -4,30  la peau, a l'emprise des baies
#                    1,80 m de cavite — n'existe qu'ICI, SOUS la peau
#     -6,10  fond du puits
#    -12,60  le bas de la coque : il y a la place
#
# LA REPONSE N'EST PAS UN BOOLEEN. Le determinisme reste une exigence dure
# (`build-hull.sh --check`, 0 octet divergent). On N'EMET PAS les faces de
# l'emprise, et l'on raccorde le bord par une collerette.
#
# Pour que « ne pas emettre » soit exact au millimetre, il faut que la GRILLE de
# la peau passe par les bords de l'ouverture. D'ou deux ajouts :
#
#   * des points de PROFIL a x = |x_baie| +/- 3,00 (voir `PROFILE` plus bas) ;
#   * des STATIONS a s = s_baie +/- 4,25 (voir `_stations`).
#
# ⚠️ Un point insere sur un SEGMENT DROIT du profil ne change pas la coque d'un
# micron : c'est une subdivision, pas une deformation. `_surface_y` interpole sur
# la meme polyligne, les deux anneaux d'une jonction restent egaux point par
# point, et la densite de texels ne bouge pas (une projection en boite est
# calculee par face). Ce que cela coute, c'est des triangles — et c'est mesure au
# compte-rendu. Ce que cela achete, c'est une ouverture aux cotes EXACTES sans
# une seule operation booleenne.
BAY_HALF_X = 3.00        # ouverture de 6,00 m de large
BAY_HALF_S = 4.25        # ouverture de 8,50 m de long, axe long dans le survol
#: Profondeur peau -> fond. La coque ne la modelise pas : elle est TENUE par
#: `bay_kit.glb`, qui ferme le puits. Elle est ici pour que les harnais et le
#: compte-rendu parlent du meme chiffre que le kit.
BAY_WELL_DEPTH = 1.80
#: La collerette : le bord de la peau se replie vers le BAS et vers L'EXTERIEUR.
#: Vers l'exterieur, parce que la face interne du coaming du kit est exactement
#: au plan de l'ouverture — un repli vers l'interieur la traverserait et se
#: verrait en eclat de peau au milieu du puits.
BAY_FLANGE_DROP = 0.25
BAY_FLANGE_OUT = 0.12
#: Zone ou aucun module seede ne se pose : l'ouverture, l'emprise du coaming du
#: kit (0,80 m) et une garde. « Grandes zones calmes entre les installations »
#: est une regle de lisibilite de la planche, pas une politesse.
BAY_KEEPOUT_X = BAY_HALF_X + 1.30
BAY_KEEPOUT_S = BAY_HALF_S + 1.60


def _bay_profile_x() -> tuple[float, ...]:
    """Les x (en valeur absolue) ou le profil DOIT porter un point.

    Toutes les baies les recoivent, pas seulement celles de leur troncon : les
    cinq troncons doivent partager le MEME profil, sans quoi les deux anneaux
    d'une jonction n'auraient plus le meme nombre de points et
    `_assert_joints()` — a raison — refuserait le build.
    """
    xs: set[float] = set()
    for _, x in BAYS:
        xs.add(round(abs(x) - BAY_HALF_X, 6))
        xs.add(round(abs(x) + BAY_HALF_X, 6))
    return tuple(sorted(xs))


def _subdivide_profile(base: tuple, extra: tuple[float, ...]) -> tuple:
    """Insere `extra` dans `base`, sur le segment qui les contient.

    Le point herite du materiau du segment qu'il coupe et de son y interpole :
    la polyligne est inchangee, donc la coque aussi.
    """
    points = list(base)
    for x in extra:
        if any(abs(p[0] - x) < 1e-9 for p in points):
            continue                       # deja un point du profil (p. ex. 6,80)
        for i in range(len(points) - 1):
            x0, y0, m0 = points[i]
            x1, y1, _ = points[i + 1]
            if x0 < x < x1:
                points.insert(i + 1, (x, y0 + (y1 - y0) * (x - x0) / (x1 - x0), m0))
                break
        else:
            raise ak.ContractError(
                f"bord d'ouverture x = {x} hors du pont : le profil ne monte "
                "jamais jusque-la, une baie sortirait de la coque")
    return tuple(points)


#: Le profil REELLEMENT employe : celui du brief, subdivise aux bords des baies.
PROFILE: tuple[tuple[float, float, str], ...] = _subdivide_profile(
    PROFILE_BASE, _bay_profile_x())
#: Indice du dernier point de la moitie SUPERIEURE (le bord, x = 14).
DECK_LAST = next(i for i, p in enumerate(PROFILE)
                 if abs(p[0] - HALF_WIDTH) < 1e-9)

# --------------------------------------------------------------------------
# LES FOSSES — le relief se prend VERS LE BAS
# --------------------------------------------------------------------------
# ⚠️ LE PLAFOND INTERDIT LE RELIEF VERS LE HAUT, ET C'EST MESURE. Le decor inerte
# ne monte pas au-dessus de -3,00 (`ADR-0041`) et le pont est a -4,30 : il reste
# 1,26 m. La consigne 4 demande « de grands volumes de plusieurs metres produisant
# de vraies ombres » — vers le haut, c'est impossible, et une terrasse de 3 m
# masquerait le combat sans jamais pouvoir etre touchee.
#
# La profondeur, elle, est libre : il y a 8 m entre le pont et la quille (-12,60).
# Une fosse de 1,55 m se lit comme un volume de 1,55 m, et ne coute rien au
# plafond. C'est la meme sortie que le lot 1 de la refonte a prise pour les ponts
# d'envol, et pour la meme raison.
#
# ⚠️ ELLES N'AJOUTENT AUCUN POINT DE PROFIL, ET C'EST CE QUI LES REND GRATUITES EN
# TOPOLOGIE. Une fosse occupe tout le pont interieur d'un bord — de |x| = 2,20 a
# 6,80 — et ces deux abscisses sont DEJA des points du profil. Un point neuf
# aurait coute deux segments d'anneau sur TOUTE la longueur du vaisseau, a chaque
# station des cinq troncons : ~600 triangles par point, pour un creux local.
#
# ⚠️ ET ELLES SUIVENT L'ECHELLE TOUTES SEULES. Comme les ouvertures de baie, une
# fosse est definie par des INDICES d'anneau et non par des coordonnees absolues :
# `RING_X` est nominal. Elle se pince donc avec le bord qui se pince, sans qu'une
# ligne de plus soit ecrite — ce qui la rend posable dans une zone de variation.
#
# (s du centre, demi-longueur, bord : +1 tribord / -1 babord)
# ⚠️ DEUX POSITIONS ONT ETE CORRIGEES PAR L'ASSERTION, PAS PAR LE JUGEMENT. Les
# fosses etaient d'abord ecrites a s = 126 et 413 — a huit et trois metres des
# socles de `Turret_03` et `Turret_13`. En x elles ne les touchaient pas (la fosse
# tient sur le pont INTERIEUR, ces deux affuts sont sur le pont median), mais leurs
# gardes se recouvraient : un trou de 1,55 m a 72 cm du bord d'un socle. Rien
# n'aurait produit d'erreur.
PITS: tuple[tuple[float, float, float], ...] = (
    (136.0, 6.0, 1.0),
    (228.0, 6.0, 1.0),
    (292.0, 6.0, -1.0),
    (393.0, 6.0, 1.0),
)
#: Les deux abscisses NOMINALES de l'emprise — deux points existants du profil.
PIT_X = (2.20, 6.80)
#: Profondeur sous la peau. Moins que le puits d'un pont d'envol (1,80 m) : une
#: fosse de maintenance n'a pas a pouvoir contenir un appareil, et un creux plus
#: profond que la baie voisine brouillerait la hierarchie des deux lectures.
PIT_DEPTH = 1.55
#: Garde autour d'une fosse : rien ne s'y pose, et elle ne mord aucune installation.
PIT_KEEPOUT = 2.20

# --------------------------------------------------------------------------
# LES TRANCHEES DE BASTION — le creux qui rend au bastion son PIED
# --------------------------------------------------------------------------
# ⚠️ ELLES EXISTENT PARCE QU'UNE CAPTURE A MONTRE UNE PIECE SANS EMBASE. Le kit
# de la Citadelle (BRIEF-0096) taille son bastion pour une assise a -6,50, soit
# 1,51 m SOUS le pont median. Pose sur une coque plate, il s'y enfonce d'autant :
# sa jupe arrondie est tranchee net par le plan du pont, sans socle, sans conge
# et sans aucun assombrissement de contact. Aucun artefact — ni z-fighting, ni
# flottement : ca ne se lit pas comme faux, ca se lit comme une piece qui a perdu
# sa base. C'est ce creux, et lui seul, qui rend les 1,51 m de jupe VISIBLES et
# qui tient la promesse du LOT 0 (« 2,85 m de hauteur lue pour 1,99 m batie »).
#
# ⚠️ ELLES SONT SUR LE PONT MEDIAN, ET C'EST CE QUI LES REND GRATUITES EN
# TOPOLOGIE. La premiere ecriture du plan les voulait « sous l'emprise de la
# citadelle », donc TRAVERSANTES : il aurait fallu couper l'artere, ses rebords,
# ses conduits et ses travees. Or les bastions ne sont pas sur l'axe, ils sont sur
# le pont median — et `7,35` et `10,30` sont DEJA les points 9 et 10 de
# `PROFILE_BASE`. Comme les fosses avec `2,20` et `6,80`, une tranchee posee sur
# deux points existants ne coute aucun point de profil : un point neuf aurait
# coute deux segments d'anneau sur toute la longueur du vaisseau, a chaque
# station des cinq troncons.
#
# ⚠️ LE BASTION DEBORDE LA TRANCHEE, ET C'EST ASSUME. Il va de 6,90 a 11,40, la
# tranchee de 7,35 a 10,30 : restent 45 cm en dedans et 1,10 m au large ou sa
# jupe reste enterree. Les elargir demanderait deux points de profil neufs, et
# celui de 6,90 tomberait au milieu de la CONTREMARCHE DE CHINE — une rampe, pas
# une bande plate. Le bastion se lit donc comme plante dans un puits, ce qui est
# la lecture voulue.
#: Les deux abscisses NOMINALES, points 9 et 10 du profil.
MOAT_X = (7.35, 10.30)
#: ⚠️ UN FOND ABSOLU, ET NON UNE PROFONDEUR — C'EST L'INVERSE DES FOSSES, POUR UNE
#: RAISON. Une fosse est un creux decoratif : sa profondeur se compte sous la peau,
#: et le fond suit le bord. Ici c'est le MOTEUR qui a besoin d'un nombre — il pose
#: `citadel_bastion` a cette cote exacte (`CortegeCitadel.BASTION_BASE_Y`). Deriver
#: le fond de la peau ferait deriver l'assise du bastion avec elle, et la piece
#: flotterait ou s'enterrerait sans qu'aucune erreur ne le dise.
MOAT_FLOOR_Y = -6.50
#: Ce que la tranchee doit creuser AU MOINS, sous le point le plus bas de son
#: emprise. Le harnais le verifie : si la peau descendait, le fond fixe cesserait
#: d'etre un creux.
MOAT_MIN_DEPTH = 1.40
#: (s du centre, demi-longueur, bord) — une par bastion, donc une par bord.
#: L'emprise deborde celle du bastion (s 239,6 a 246,0) de 40 cm a chaque bout :
#: sans ce jeu, la jupe toucherait les parois et le creux disparaitrait.
MOATS: tuple[tuple[float, float, float], ...] = (
    (242.8, 3.60, 1.0),
    (242.8, 3.60, -1.0),
)


def _hollows():
    """Tous les CREUX du borde : les fosses, les tranchees, puis les bassins.

    Rend `(s centre, demi-longueur, bord, abscisses, fond absolu ou None)`.

    ⚠️ UN SEUL GENERATEUR ET NON DEUX MECANISMES PARALLELES. Six endroits de ce
    fichier interrogent les creux — la peau qui saute ses cellules, les modules
    qui les evitent, les stations qui pavent leur emprise, le trace, et deux
    harnais. Une seconde famille recopiee a cote aurait ete oubliee par l'un des
    six, et un creux sans son saut de peau est un plancher SOUS une peau
    intacte : invisible, et definitif.
    """
    for sc, hs, side in PITS:
        yield sc, hs, side, PIT_X, None
    for sc, hs, side in MOATS:
        yield sc, hs, side, MOAT_X, MOAT_FLOOR_Y
    # ⚠️ FOND DERIVE (None) ET NON ABSOLU, A LA DIFFERENCE DE LA TRANCHEE DE
    # BASTION. Le bassin du complexe ne porte l'assise d'AUCUNE piece de kit :
    # rien dans le moteur n'ecrit sa cote, donc rien n'oblige la peau et lui a
    # se contredire un jour. Il se creuse sous son propre point le plus bas,
    # comme une fosse, et suit le bord quoi qu'il arrive.
    for sc, hs, side in BASINS:
        yield sc, hs, side, BASIN_X, None


# --------------------------------------------------------------------------
# LES BASTIONS — ce qui donne une FONCTION a un troncon
# --------------------------------------------------------------------------
# ⚠️ LA HAUTEUR NE PEUT PAS DIFFERENCIER, ET C'EST LA CONTRAINTE QUI DECIDE DE
# TOUT. La consigne 3 demande des secteurs reconnaissables « uniquement par la
# silhouette et les gros volumes » ; or le plafond de CONSTRUCTION (-3,20) ne
# laisse que 1,10 m au-dessus du pont interieur — soit ce qu'une greffe occupe
# deja. Un « gros volume » ne peut donc pas etre plus HAUT qu'un petit.
#
# Il reste deux dimensions : l'EMPRISE et la PROFONDEUR. Les fosses ont pris la
# seconde ; les bastions prennent la premiere. Et ils vivent sur le pont MEDIAN,
# a -4,99, ou le plafond laisse 1,79 m au lieu de 1,10 — le seul endroit du
# vaisseau ou 1,2 m de relief tiennent.
#
# ⚠️ AUCUN N'EST SOUS UNE TOURELLE, ET CE N'EST PAS UN CHOIX DE COMPOSITION.
# `turret_seat_y()` echantillonne la PEAU, pas les modules : un bastion pose sous
# un socle enfoncerait l'affut de sa propre hauteur, et rien ne le dirait.
#
# (s centre, demi-longueur, x interieur, x exterieur, hauteur au-dessus de la peau)
# ⚠️ ELLE EST VIDE, ET C'EST LA CONSIGNE 16 QUI A TRANCHE CONTRE LA 3. Trois
# bastions ont ete construits, poses et mesures. Ils coutaient 33 m de borde —
# et le compte de calme, corrige au meme moment, a montre que les fosses, la
# passerelle et eux ramenaient le niveau de 58,6 pct a 48,2 pct : SOUS les
# 50,3 pct d'ou le lot B4 etait parti.
#
# La consigne 3 demande des secteurs reconnaissables. Elle l'est deja, et sans
# eux : sept evenements de contour, quatre zones asymetriques, quatre fosses, une
# passerelle et Ambry donnent a chaque troncon son identite. Les bastions
# n'ajoutaient pas une LECTURE, ils ajoutaient du remplissage — et « le
# gigantisme vient aussi du vide ».
#
# Le code qui les construit reste : il est verifie, assertionne, et la table
# suffit a les faire revenir le jour ou une fonction les reclamera pour
# elle-meme, et non pour occuper un troncon.
BASTIONS: tuple[tuple[float, float, float, float, float], ...] = ()

# --------------------------------------------------------------------------
# LE PONT TRANSVERSAL — un seul, et c'est tout l'interet
# --------------------------------------------------------------------------
# ⚠️ C'EST LE GESTE LE PLUS EFFICACE CONTRE L'AXE INFINI, et le plus facile a
# gacher. La consigne 13 le dit elle-meme : « ne pas en abuser — un element
# EXCEPTIONNEL est plus interessant qu'un motif repete ». Il y en a UN.
#
# ⚠️ IL EST BAS, ET CE N'EST PAS UN CHOIX. Le plafond du decor inerte est a -3,00
# et le pont a -4,30 : 1,30 m pour tout. Une passerelle de 0,80 m d'epaisseur ne
# laisserait que 0,50 m de jour et se lirait comme une barre POSEE. A 0,45 m elle
# laisse 0,70 m au-dessus du pont — et surtout 0,98 m au-dessus du FOND DE LA
# TRANCHEE, qui est l'endroit ou le joueur le verra enjamber quelque chose.
#
# ⚠️ ET IL VIT LOIN D'UNE JONCTION DE TRONCON. Les cinq troncons sont des objets
# SEPARES : une piece a cheval sur z = -200 serait coupee en deux maillages, sans
# qu'aucune erreur ne le dise. s = 195 est au cœur de la plus large plage calme
# hors proue (186 a 212) et a cinq metres de la jonction.
CROSS_BRIDGE_S = 195.0
CROSS_BRIDGE_HS = 1.50          # 3,00 m de profondeur : assez pour se lire
# ⚠️ 10,30 ET NON 6,80, CORRIGE EN REGARDANT. La premiere passerelle s'arretait au
# bord du pont INTERIEUR : 13,6 m sur 28, elle se confondait avec les vingt et une
# TRAVEES DE CANAL qui enjambent deja la tranchee. Or la consigne 13 ne demande pas
# d'enjamber l'artere — elle demande de « relier visuellement les DEUX COTES du
# vaisseau ». A 10,30 elle atteint le bord du pont median, la ou vivent les
# tourelles, et ses piles gagnent au passage 1,29 m de hauteur visible : le pont
# median est a -4,99, un demi-metre plus bas que le pont interieur.
CROSS_BRIDGE_X = 10.30
# ⚠️ -3,25 ET NON -3,15 : le plafond qui compte ici n'est pas celui du DECOR
# (-3,00) mais celui de la CONSTRUCTION (-3,20), et la difference est reservee a
# « ce que le jeu posera sur les points d'attache ». La premiere poutre a ete
# refusee a -3,150 par `_assert_build_ceiling`.
CROSS_BRIDGE_TOP = -3.25
CROSS_BRIDGE_BOTTOM = -3.70     # 0,45 m d'epaisseur
CROSS_BRIDGE_PIER = 0.90        # largeur des deux piles, aux extremites

#: 5 nœuds d'arete dorsale, exactement un par troncon, sur l'axe.
#: ⚠️ LA COQUE N'EN CUIT PLUS AUCUN (BRIEF-0094). `build_spine_bulb()` a disparu,
#: comme `build_bay()` (BRIEF-0091) et `build_turret_pad()` (BRIEF-0093) avant
#: elle, et pour une raison qui n'est pas esthetique : le nœud est DESTRUCTIBLE.
#: Une piece cuite dans le troncon ne s'eteint pas sans eteindre les quatre
#: autres, puisque les cinq partagent un seul maillage et un seul jeu de
#: materiaux. La coque porte le MARQUEUR ; `spine_kit.glb` porte le berceau, le
#: cœur et les entretoises, et le moteur ne detruit que le cœur.
#:
#: ⚠️ LES CINQ SIEGENT EN TETE DE TRONCON, PLUS EN SON MILIEU (BRIEF-0104). Ils
#: etaient a 54, 52, 60, 38 et 59 % du debut du leur — une position defendable
#: tant que `weakened_section()` eteignait le troncon SUIVANT, et fatale des
#: qu'elle a ete retournee le 2026-09-06 (commit 5288dd4) pour eteindre le sien :
#: le joueur abattait le nœud a mi-parcours et n'eteignait qu'une moitie de
#: couloir DERRIERE lui. « Quand je detruis un nœud, pas de changement » — il ne
#: pouvait structurellement rien voir. Un nœud en tete alimente donc tout ce que
#: le joueur a encore a traverser, et son extinction se lit dans le cadre meme
#: ou elle se produit.
#:
#: ⚠️ TROIS DES CINQ NE SONT PAS A +3, ET AUCUN ECART N'EST UN ARRONDI DE
#: CONFORT. Chacun est une garde de ce module, mesuree en l'appelant :
#:
#:   * `Spine_01` a 46,0 (+46 du debut) — LE FUSEAU DE PROUE. Le berceau fait
#:     1,32 m et le fond plat du canal est contracte par `_scales()` : sous
#:     s = 44,02 il n'y tient plus et `_audit()` arrete le build. 46,0 laisse
#:     31 mm, la plus mince des cinq marges, et c'est volontaire — car c'est
#:     aussi la BONNE station : `_canal_lane()` n'allume la voie externe qu'a
#:     partir de s = 41,12. L'artere du troncon 1 commence la ; le nœud siege
#:     4,9 m apres le debut de ce qu'il alimente, et il n'a rien en amont a
#:     eteindre.
#:   * `Spine_04` a 305,0 (+5) — LA FOSSE DE MAINTENANCE DE s = 292. Bord
#:     babord, de |x| = 2,20 a 6,80 : son `PIT_KEEPOUT` porte x_hi a exactement
#:     0,0, donc elle ATTEINT l'axe. Avec `APRON_SPINE`, elle interdit tout
#:     l'intervalle 280,0 - 304,0 ; `_assert_pits_are_clear()` refuse 303,0.
#:   * `Spine_05` a 406,0 (+6) — LA FOSSE DE s = 393, bord tribord, meme
#:     mecanisme : intervalle interdit 381,0 - 405,0.
#:
#: ⚠️ NE PAS DEPLACER UNE FOSSE POUR GAGNER DEUX METRES. Deux d'entre elles ont
#: deja ete recalees par cette assertion (voir l'en-tete de `PITS`) ; +5 et +6 m
#: a 2,4 u/s font deux secondes d'entree de troncon, que le jeu ne perd pas et
#: que la coque paierait en arbitrage.
SPINES: tuple[float, ...] = (46.0, 103.0, 203.0, 305.0, 406.0)

#: LES DOUZE CONDUITES DE L'ARTERE (BRIEF-0110) — (station, x SIGNE).
#:
#: ⚠️ C'EST LA DERNIERE COTE DU CHANTIER DE L'ARTERE QUI NE VENAIT PAS DE
#: L'ASSET, ET ELLE S'EST VUE A L'ECRAN. `CortegeArtery.CONDUITS` pose ses douze
#: pieces a `DECK_Y = -4,30` CONSTANT, alors que la peau du corridor respire :
#: `_scales()` etrangle la coque station par station, si bien que le pont
#: interieur descend de plusieurs centimetres entre la proue et la poupe. Le
#: test qui gardait la cote la comparait aux marqueurs VOISINS et laissait
#: passer l'ecart.
#:
#: Ici la coque dit ou les conduites vont, comme elle le fait deja pour les
#: dix-sept tourelles, les sept ponts et les cinq nœuds. Le `y` du repere est
#: `_surface_y(s, x)`, c'est-a-dire le DESSUS DE LA PEAU au lateral exact de la
#: piece — donc le point ou son BAS doit se poser (`CortegeConduit._seat()`
#: assied la boite englobante, pas l'origine du fichier).
#:
#: ⚠️ LE `x` N'EST PAS RAPPORTE A LA LARGEUR LOCALE (`_marker_x`). Les douze
#: stations sont ECRITES dans le code de jeu en cotes absolues (3,60 / 4,40) et
#: le moteur les lit telles quelles : leur appliquer `kx` ici deplacerait le
#: repere sous la piece au lieu de la piece sur le repere. Seul le `y` change.
ARTERY_CONDUITS: tuple[tuple[float, float], ...] = (
    (30.0, 3.60), (58.0, -3.60), (95.0, 4.40), (138.0, -3.60),
    # ⚠️ 232 ET NON 240 : LA CITADELLE OCCUPE 239,6 A 246,0. Elle n'est pas un
    # marqueur de coque — elle est posee par le code depuis `citadel_station` —
    # donc le banc de pose de `CortegeArtery` ne la voyait pas, et le conflit a
    # dormi jusqu'a ce que ce repere le rende visible.
    (163.0, 4.40), (192.0, -3.60), (232.0, 4.40), (277.0, -3.60),
    (314.0, 4.40), (358.0, -3.60), (394.0, 4.40), (435.0, -3.60),
)

#: ⚠️ EMPRISE QUE `spine_kit.glb` POSE DANS LE FOND DU CANAL, berceau compris.
#: Elle vit ICI parce que c'est ici qu'on echantillonne la peau pour calculer
#: l'assise du marqueur, et `build_spine_kit.FOOTPRINT_HX/HS` doivent valoir la
#: meme chose : le kit — qui importe ce module — le reverifie a chaque build,
#: exactement comme `BAY_COAMING_W` et `TURRET_FOOTPRINT_R`.
SPINE_FOOTPRINT_HX = 0.66
SPINE_FOOTPRINT_HS = 1.28

# --------------------------------------------------------------------------
# LES EMPRISES D'INSTALLATION — le rythme calme/installation/calme (priorite 3)
# --------------------------------------------------------------------------
# ⚠️ « LES ZONES CALMES SONT UN LIVRABLE, PAS UN MANQUE. » Le vocabulaire modulaire
# semait ses plaques, ses nervures, ses greffes et ses pastilles sur TOUTE la
# longueur : 1 071 plaques, 384 pastilles, 182 nervures, uniformement. Le resultat
# est celui que l'operateur decrit — « du detail presque partout » — et c'est un
# defaut de GAMEPLAY avant d'etre un defaut d'image : quand un gros equipement
# entre dans le cadre, le joueur doit le remarquer, et sur un fond charge en
# permanence il ne remarque rien.
#
# La regle est donc devenue : UN MODULE DE RELIEF NE SE POSE QUE DANS L'EMPRISE
# D'UNE INSTALLATION. Ailleurs, la tole est nue — et elle n'est pas vide pour
# autant : `TEX-0010` (bordé/plaques) est livree et integree, elle porte les
# joints, les rivets et l'usure que la geometrie faisait a sa place. C'est
# exactement le partage que l'en-tete de ce fichier annonce depuis BRIEF-0089
# (« le detail perçu vient des textures, pas des triangles ») et qui n'avait
# jamais ete applique.
#
# Les demi-emprises ci-dessous sont des cotes de RYTHME, pas de geometrie : elles
# donnent des zones actives de 9 a 14 m autour de chaque installation, separees
# par les 15-20 m calmes que le brief demande. La mesure — part calme, plus longue
# plage nue — est rendue a chaque build.
APRON_TURRET = 4.2
APRON_BAY = 5.4
APRON_SPINE = 3.8
#: Ambry n'est pas un marqueur mais une piece entiere : son emprise est la sienne.
APRON_AMBRY = 2.0
#: Longueur minimale d'une plage nue. Le brief pose « 15-20 m calmes » : une
#: greffe posee dans une plage libre doit donc laisser AU MOINS cette longueur de
#: tole nue de chaque cote, sans quoi elle mange la respiration qu'elle est censee
#: ponctuer.
CALM_MIN = 12.0

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

# --------------------------------------------------------------------------
# LE COMPLEXE INDUSTRIEL DU TRONCON 5 (BRIEF-0111)
# --------------------------------------------------------------------------
# ⚠️ LE BRIEF ANNONCE 69 M DE VIDE TRIBORD ENTRE s = 410 ET s = 479. IL Y EN A 24,5.
# Les 69 m sont mesures sur les MARQUEURS (dix-sept tourelles, sept ponts, cinq
# nœuds) ; AMBRY n'en est pas un — c'est une piece CUITE dans la peau du troncon 5,
# a `s` 446 a 474 et `|x|` 7,60 a 13,60, tribord, colliers de greffe compris de
# 444,5 a 475,5. Le meme angle mort a deja coute une conduite d'artere plantee dans
# la Citadelle (voir `ARTERY_CONDUITS`, station 232) : ce qui n'est pas un marqueur
# ne se voit pas depuis une table de marqueurs.
#
# Le vide REEL de ce bord est donc `s in [418 ; 442,5]` — 8 m de garde a
# `Turret_13` (410,0) d'un cote, 2 m de tole nue avant le premier collier d'Ambry
# de l'autre. Le compte de calme du build le disait deja avant ce lot : « les cinq
# plus larges : ... s 419-444 (25 m) ».
#
# ⚠️ ET C'EST LE BON CHIFFRE POUR CE QU'ON EN FAIT. Le cadre de la camera du jeu
# montre 23,6 m de pont a la fois : un complexe de 24,5 m remplit un ecran entier
# dans le sens du defilement. Meubler 54 m en aurait demande deux et aurait colle
# le complexe a Ambry, dont tout l'interet est d'arriver seule apres du calme.
PLANT_S = (418.0, 442.5)
#: Emprise en x NOMINAL — de la levre de chine (6,80) a la cassure de facette
#: (12,35). Entre ces deux points la coque est plate a 16 cm pres sur 5,5 m de
#: large : c'est la seule bande du vaisseau ou une installation peut s'etendre
#: sans etre coupee par une pente.
PLANT_XN = (6.85, 12.30)
#: ⚠️ LE COMPLEXE EST COUPE EN DEUX DANS LE SENS DE LA LONGUEUR, ET C'EST CE QUI
#: LE REND LISIBLE. Au large, un PLANCHER continu de 2,40 m — la plateforme, ou
#: vivent les cuves, les cheminees et les portiques. Vers l'axe, une ALLEE de
#: 2,55 m laissee au pont nu : c'est par la que passe la ligne de conduite, et
#: c'est le seul endroit du complexe ou l'on voie la coque elle-meme.
#: Un lieu se lit a ses vides autant qu'a ses volumes.
PLANT_FLOOR_XN = (9.90, 12.30)
PLANT_ALLEY_XN = (7.35, 9.90)
#: Le longeron de rive : c'est lui qui dessine L'EMPRISE, donc le LIEU.
PLANT_RAIL_XN = (11.80, 12.30)
#: Le longeron de chine, cote axe.
PLANT_KERB_XN = (6.85, 7.35)
#: ⚠️ LA VOIE DE CONDUITE EST EN X ABSOLU, ET C'EST LA SEULE CHOSE QUI L'EST.
#: Tout le reste du complexe est ecrit en x NOMINAL et suit la largeur locale
#: (`_side_scale`) : le bord tribord se pince de 15 pct a s = 434 (table
#: `ASYMMETRY`), soit 1,5 m qui rentrent et ressortent au milieu de l'emprise.
#: Une conduite, elle, est une piece RIGIDE de 2,78 m que le moteur pose telle
#: quelle sur le repere : lui appliquer `kx` deplacerait le repere sous la piece
#: au lieu de la piece sur le repere — exactement ce que dit deja
#: `ARTERY_CONDUITS`. La voie est donc droite, et c'est le complexe qui s'ecarte.
#:
#: ⚠️ ET IL Y EN A DEUX, PARCE QU'UNE SEULE NE TIENT PAS. A l'entree le bord est
#: a sa largeur nominale et la voie tient a x = 9,20 ; a la sortie il sort a
#: peine du pincement (`_side_scale` = 0,888 a s = 436,6) et la meme voie
#: passerait SOUS le plancher, qui s'est resserre de 1,1 m. La ligne ressort donc
#: un metre plus pres de l'axe — ce qui se lit, du reste, comme un renvoi : le
#: complexe a devie la conduite qu'il traverse.
PLANT_LANE_IN_X = 9.20
PLANT_LANE_OUT_X = 8.20
PLANT_LANE_HALF = 0.35
#: ⚠️ HAUTEUR HORS-TOUT DE LA PIECE LA PLUS HAUTE QUE LE CONCEPTEUR PEUT MONTER
#: SUR CES REPERES, mesuree sur les binaires : `artery_conduit.glb` fait 0,46 m,
#: `artery_conduit_bend.glb` 0,919. On garde la PIRE, parce que rien ici
#: n'interdit la coudee et qu'un repere trop haut ne se verrait qu'en vol.
CONDUIT_PIECE_TOP = 0.92
#: Longueur et hauteur du berceau d'une conduite (la piece fait 2,78 x 0,46).
PLANT_CRADLE_S = 1.45
PLANT_CRADLE_RISE = 0.30
#: LES CINQ CONDUITES — (station, x ABSOLU). Trois a l'entree, deux a la sortie :
#: la ligne entre dans le complexe, disparait dans le cœur, et en ressort.
#:
#: ⚠️ LE REPERE MARQUE LE BAS DE LA PIECE, et son `y` est le dessus du BERCEAU
#: qu'on lui construit — lui-meme echantillonne sur la peau (`_surface_box` prend
#: ses quatre coins dans `_surface_y`). `CortegeConduit._seat()` assied la boite
#: englobante, pas l'origine du fichier : celle d'`artery_conduit.glb` est a
#: (-0,36 ; 1,00 ; 1,38), hors de la piece.
PLANT_CONDUITS: tuple[tuple[float, float], ...] = (
    (419.6, PLANT_LANE_IN_X), (422.4, PLANT_LANE_IN_X), (425.2, PLANT_LANE_IN_X),
    (438.0, PLANT_LANE_OUT_X), (440.8, PLANT_LANE_OUT_X),
)
#: LE BASSIN — le cœur, et le seul volume d'un metre et demi que le plafond
#: autorise. Il se creuse VERS LE BAS (8 m jusqu'a la quille) au lieu de monter
#: dans les 1,79 m de ciel : meme sortie que les fosses et que les puits de pont
#: d'envol, et pour la meme raison. (s du centre, demi-longueur, bord).
BASINS: tuple[tuple[float, float, float], ...] = (
    (431.75, 4.45, 1.0),
)
#: Les deux abscisses NOMINALES du bassin : les points 9 et 10 du profil, comme
#: les tranchees de bastion. Un point neuf aurait coute deux segments d'anneau sur
#: toute la longueur du vaisseau, a chaque station des cinq troncons.
BASIN_X = (7.35, 10.30)
#: Zone interdite aux modules seedes, en x ABSOLU. Elle est plus large que
#: l'emprise batie : une greffe de 1 m posee au ras du longeron de rive
#: passerait sous le plancher sans qu'aucune erreur ne le dise.
PLANT_KEEPOUT_X = (6.20, 12.80)
PLANT_KEEPOUT_S = (416.8, 443.8)
#: Emprise de rythme : le complexe EST une installation, et le compte de calme
#: doit la voir. « Un indicateur qui ne voit pas ce qu'on vient d'ajouter ne
#: mesure plus rien. » ⚠️ Elle ne passe PAS par `_installation_spans()` : voir
#: la note qui s'y trouve — les emprises y sont fusionnees sans leur x, et
#: ouvrir 24 m a tribord les ouvrirait a babord.
APRON_PLANT = 1.6

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
    """Echelles laterale et verticale de la section a la station `s`.

    ⚠️ AU-DELA DE LA DERNIERE STATION, ON REND LA DERNIERE VALEUR ET NON (1, 1).
    Tant que la table s'arretait au fuseau, les deux revenaient au meme ; depuis
    qu'elle va jusqu'a la poupe, rendre (1, 1) ferait sauter la coque de sa
    largeur finale a sa largeur nominale sur la derniere face — une marche de
    deux metres, sur le seul bord que le joueur voit de face en fin de niveau.
    """
    if s >= TAPER_END:
        return TAPER[-1][1], TAPER[-1][2]
    for (s0, kx0, ky0), (s1, kx1, ky1) in zip(TAPER, TAPER[1:]):
        if s <= s1:
            t = _smoothstep((s - s0) / (s1 - s0))
            return kx0 + (kx1 - kx0) * t, ky0 + (ky1 - ky0) * t
    return 1.0, 1.0


def _asym(s: float) -> tuple[float, float]:
    """Facteurs de largeur (tribord, babord) a la station `s`."""
    if s <= ASYMMETRY[0][0]:
        return ASYMMETRY[0][1], ASYMMETRY[0][2]
    if s >= ASYMMETRY[-1][0]:
        return ASYMMETRY[-1][1], ASYMMETRY[-1][2]
    for (s0, t0, b0), (s1, t1, b1) in zip(ASYMMETRY, ASYMMETRY[1:]):
        if s <= s1:
            if s1 - s0 < 1e-9:
                return t1, b1
            t = _smoothstep((s - s0) / (s1 - s0))
            return t0 + (t1 - t0) * t, b0 + (b1 - b0) * t
    return 1.0, 1.0


def _side_scale(s: float, side: float) -> float:
    """L'echelle laterale du bord `side` (+1 tribord, -1 babord) a la station `s`.

    ⚠️ LE FUSEAU DE PROUE RESTE SYMETRIQUE. Il est compose a la main, marqueurs
    compris, et son etrave est le seul endroit du vaisseau que le joueur voit
    de face : une pointe de travers s'y lirait comme un defaut, pas comme une
    intention.
    """
    kx = _scales(s)[0]
    if s <= PROW_TAPER_END:
        return kx
    tri, bab = _asym(s)
    return kx * (tri if side >= 0.0 else bab)


def _half_profile(s: float, side: float = 1.0) -> list[tuple[float, float]]:
    k = _side_scale(s, side)
    ky = _scales(s)[1]
    return [(px * k, Y_PIVOT + (py - Y_PIVOT) * ky) for px, py, _ in PROFILE]


def _half_width(s: float, side: float = 1.0) -> float:
    return HALF_WIDTH * _side_scale(s, side)


def _marker_x(s: float, x: float) -> float:
    """Le X d'un marqueur, rapporte a la largeur LOCALE de la coque.

    ⚠️ SANS CETTE FONCTION, ETRANGLER LA COQUE POSE SES ORGANES DANS LE VIDE. Les
    X de la table sont absolus ; la peau, elle, respire. A `kx = 0,82`, le pont
    median s'arrete a |x| = 8,45 et `Turret_16`, ecrit a 10,20, se retrouverait
    au-dela du bord — un affut flottant a cote de son vaisseau, sans qu'aucune
    assertion ne s'en apercoive.
    ⚠️ ET C'EST AUSSI CE QUI GARDE CHAQUE MARQUEUR SUR SON PALIER. Le pont
    interieur, la contremarche de chine et le pont median s'echelonnent tous
    par `kx` : un marqueur qui suit le meme facteur reste du meme cote de la
    marche PAR CONSTRUCTION, quelle que soit la largeur locale.
    ⚠️ EN DECA DE `PROW_TAPER_END`, ON NE TOUCHE A RIEN : les deux marqueurs du
    fuseau ont ete cales a la main sur la coque retrecie de la proue. Leur
    appliquer `kx` une seconde fois les rentrerait vers l'axe sans raison.
    """
    if s <= PROW_TAPER_END:
        return x
    return x * _side_scale(s, 1.0 if x >= 0.0 else -1.0)


def _surface_y(s: float, x: float) -> float:
    """Hauteur du DESSUS de la coque a la station `s`, au lateral `x`.

    C'est la fonction que tout le vocabulaire modulaire interroge : une plaque, une
    nervure ou un socle prend sa base ici, coin par coin. C'est ce qui lui permet
    d'epouser la chine et la facette sans une seule rotation ecrite a la main.
    """
    # ⚠️ LE PROFIL DEPEND DESORMAIS DU BORD. Prendre `abs(x)` sans dire de quel
    # cote rendrait l'assise de tribord a une piece de babord : sur une coque
    # asymetrique, jusqu'a 19 pct d'ecart de largeur, donc une base posee sur une
    # peau qui n'est pas la sienne. Tout le vocabulaire modulaire interroge cette
    # fonction — plaques, nervures, socles, greffes — et aucun ne l'aurait dit.
    half = _half_profile(s, 1.0 if x >= 0.0 else -1.0)[: DECK_LAST + 1]
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
    """Anneau ferme de 34 points, tribord puis babord.

    ⚠️ IL RECOPIAIT LA MOITIE TRIBORD EN MIROIR, et c'etait toute la symetrie du
    vaisseau. Les deux moities sont desormais calculees separement — meme
    topologie, memes indices, memes materiaux : seules les abscisses d'un bord
    changent. Rien de ce qui indexe l'anneau (`RING_MATERIALS`, `_ring_deck_flags`,
    `_bay_cell`) n'a besoin de le savoir.
    """
    tribord = _half_profile(s, 1.0)
    babord = _half_profile(s, -1.0)
    return tribord + [(-x, y) for x, y in reversed(babord[1:-1])]


def _ring_materials() -> list[str]:
    """Materiau du segment `i -> i+1` de l'anneau ferme."""
    n = len(PROFILE)
    mats = [PROFILE[i][2] for i in range(n - 1)]          # 0..16, tribord
    mats += [PROFILE[2 * n - 3 - i][2] for i in range(n - 1, 2 * n - 2)]
    return mats


RING_MATERIALS = _ring_materials()
RING_SIZE = 2 * len(PROFILE) - 2


def _ring_x() -> list[float]:
    """Le x (NON mis a l'echelle) de chaque point de l'anneau ferme."""
    n = len(PROFILE)
    xs = [PROFILE[i][0] for i in range(n)]
    xs += [-PROFILE[2 * n - 2 - j][0] for j in range(n, 2 * n - 2)]
    return xs


def _ring_deck_flags() -> list[bool]:
    """Le segment `i -> i+1` appartient-il au PONT (la moitie superieure) ?

    ⚠️ Sans ce garde-fou, une ouverture de baie percerait aussi le FOND de la
    coque : le profil repasse par x = 10,40 et x = 5,00 sous la quille, et un
    test qui ne regarderait que le x y trouverait des segments « dans l'emprise ».
    Le defaut serait invisible du dessus et beant vu de dessous.
    """
    n = len(PROFILE)
    flags = [False] * RING_SIZE
    for i in range(DECK_LAST):
        flags[i] = True
    for i in range(2 * n - 2 - DECK_LAST, 2 * n - 2):
        flags[i] = True
    return flags


RING_X = _ring_x()
RING_ON_DECK = _ring_deck_flags()


# --------------------------------------------------------------------------
# L'artere : ce que le profil dit, relu par des constantes nommees
# --------------------------------------------------------------------------


def _assert_taper_spares_the_bays() -> None:
    """La largeur ne respire JAMAIS sous une ouverture de pont d'envol.

    ⚠️ CE QUE CETTE ASSERTION A APPRIS DES SA PREMIERE EXECUTION, ET QUI CORRIGE
    SA PROPRE PREMISSE. Ecrite pour refuser TOUT ecart a 1,0, elle a immediatement
    arrete le build sur `Bay_01` — qui vit a s = 86, dans le fuseau de proue, ou
    `kx` vaut 0,984 depuis toujours. Or cette baie fonctionne, et la raison est
    instructive : l'ouverture est definie par des INDICES D'ANNEAU, pas par des
    coordonnees absolues, si bien qu'elle s'echelonne avec la peau. Le trou suit.

    Ce qui ne suit PAS, c'est le coaming de `bay_kit.glb` : il est modelise a
    cotes fixes et pose sur le marqueur. A 1,6 pct d'ecart (l'existant), les
    10 cm se noient dans la collerette. A 18 pct, ce serait 54 cm de debord de
    chaque cote — la peau et son puits ne se rejoindraient plus, en silence.

    Le seuil porte donc sur l'AMPLEUR et non sur l'egalite : il laisse passer ce
    que la proue impose depuis toujours, et refuse toute respiration deliberee.
    """
    tolerance = 0.03
    guard = BAY_HALF_S + 3.75
    # ⚠️ LA GARDE EST PAR BORD, ET C'EST CE QUI LAISSE DE LA PLACE A L'ASYMETRIE.
    # Une baie a babord ne craint rien d'un epaulement a tribord : la protéger des
    # deux cotes aurait ferme presque toute la coque, et la consigne 14 n'aurait
    # eu nulle part ou vivre. Le quatrieme membre dit quel bord est concerne.
    protected: list[tuple[str, float, float, float]] = [
        (f"le pont d'envol a s = {sc:.0f}", sc - guard, sc + guard,
         1.0 if xc >= 0.0 else -1.0)
        for sc, xc in BAYS
    ]
    # ⚠️ ET AMBRY, POUR UNE AUTRE RAISON. L'avant-poste humain est une GREFFE : il
    # est deplie a 0,700 tuile/m quand le borde est a 0,200, et il n'a aucune
    # contrainte de jonction. Elargir la coque sous lui l'etire, et sa densite de
    # texels tombe sous la borne de la projection en boite — refuse par le harnais
    # d'UV, qui a arrete un epaulement ecrit a s = 453. Une greffe ne s'etire pas
    # avec ce qui la porte.
    # Ambry vit a tribord (AMBRY_X va de 7,60 a 13,60).
    protected.append(("Ambry", AMBRY_S[0] - 3.75, AMBRY_S[1] + 3.75, 1.0))
    for label, low, high, side in protected:
        for s in (low, (low + high) * 0.5, high):
            k = _side_scale(s, side)
            if abs(k - 1.0) > tolerance:
                bord = "tribord" if side >= 0.0 else "babord"
                raise SystemExit(
                    f"[long_cortege] la coque respire a {bord}, s = {s:.1f} "
                    f"(facteur {k:.3f}, ecart {abs(k - 1.0) * 100:.1f} pct pour "
                    f"{tolerance * 100:.0f} pct tolere), dans la garde de {label}. "
                    "La peau bougerait sans que la piece qu'elle porte ne bouge "
                    "avec elle, et rien ne le dirait."
                )


def _assert_bastions_are_clear() -> None:
    """Chaque bastion tient dans SON troncon, et ne mord aucune installation.

    ⚠️ LA JONCTION D'ABORD, ET C'EST ELLE QUI A REFUSE LE PREMIER JET. Un bastion
    est place dans le troncon de son CENTRE, mais sa geometrie s'etend de part et
    d'autre : ecrit a s = 205 avec 6,5 m de demi-longueur, il debordait a 198,5 —
    dans le troncon voisin. Le `.glb` restait valide ; c'est le harnais de
    jonction qui a vu la bbox du troncon 3 depasser de 1,50 m. Meme piege que la
    passerelle, evite pour elle et retombe ici.

    ⚠️ ET AUCUN SOUS UNE TOURELLE : `turret_seat_y()` echantillonne la peau et non
    les modules, donc un affut pose sur un bastion s'y enfoncerait de 1,20 m.
    """
    problems: list[str] = []
    for sc, hs, xi, xo, _h in BASTIONS:
        s0, s1 = sc - hs, sc + hs
        section = int(sc // SECTION_LENGTH)
        low, high = section * SECTION_LENGTH, (section + 1) * SECTION_LENGTH
        if s0 < low + JOINT_CLEARANCE or s1 > high - JOINT_CLEARANCE:
            problems.append(
                f"le bastion a s = {sc:.0f} deborde de son troncon "
                f"({s0:.1f} a {s1:.1f} pour {low:.0f}-{high:.0f}) : il serait "
                "coupe en deux maillages")
        x_lo, x_hi = min(xi, xo), max(xi, xo)
        for number, (ts, tx) in enumerate(TURRETS, start=1):
            r = PAD_RADIUS[min(int(ts // SECTION_LENGTH), SECTION_COUNT - 1)]
            mx = _marker_x(ts, tx)
            if (s0 - r <= ts <= s1 + r) and (x_lo - r <= mx <= x_hi + r):
                problems.append(
                    f"le bastion a s = {sc:.0f} passe sous Turret_{number:02d} "
                    f"(s = {ts:.1f}, x = {mx:+.2f}) : l'affut s'y enfoncerait")
        for number, (bs, bx) in enumerate(BAYS, start=1):
            if (s0 - BAY_HALF_S <= bs <= s1 + BAY_HALF_S) \
                    and (x_lo - BAY_HALF_X <= bx <= x_hi + BAY_HALF_X):
                problems.append(
                    f"le bastion a s = {sc:.0f} recouvre Bay_{number:02d}")
        for pc, ph, pside, pxs, _pfloor in _hollows():
            px_lo = min(pxs[0] * pside, pxs[1] * pside)
            px_hi = max(pxs[0] * pside, pxs[1] * pside)
            if not (s1 < pc - ph or s0 > pc + ph
                    or x_hi < px_lo or x_lo > px_hi):
                problems.append(
                    f"le bastion a s = {sc:.0f} recouvre la fosse a s = {pc:.0f}")
        if x_lo >= 0.0 and not (s1 < AMBRY_S[0] or s0 > AMBRY_S[1]):
            problems.append(f"le bastion a s = {sc:.0f} est sous Ambry")
    if problems:
        raise SystemExit("[long_cortege] BASTIONS MAL POSES\n"
                         + "\n".join(f"  - {p}" for p in problems))


def _assert_plant_is_clear() -> None:
    """Le complexe du BRIEF-0111 tient dans son vide, et sa voie tient sur le pont.

    ⚠️ CE HARNAIS EXISTE PARCE QUE LE BRIEF S'EST TROMPE DE VIDE, ET QU'AUCUNE
    MACHINE NE LE LUI A DIT. Il annonce « tribord, s = 410 a 479 : 69 m » ; il y
    en a 24,5, parce qu'AMBRY occupe 444,5 a 475,5 du meme bord sans etre un
    marqueur. Une emprise ecrite a la main doit donc etre RELUE par une machine,
    exactement comme `_marker_clashes()` relit les trente marqueurs.

    Quatre choses sont verifiees, et chacune est muette si on ne la verifie pas :

      * les 8 m de garde a chaque tourelle voisine (le brief les demande) ;
      * la non-intersection avec Ambry, colliers de greffe compris ;
      * que la VOIE DE CONDUITE — droite, en x absolu — reste entre les deux
        bornes nominales du mobilier ET sur le pont median ou la facette, a
        CHAQUE station que couvre une piece de 2,78 m. C'est la seule chose que
        le pincement de 15 pct du bord peut casser, et il la casserait sans
        erreur : la conduite se poserait a cheval sur la chine ;
      * que rien du complexe n'approche l'axe, ou passe le degagement de tir de
        la conduite d'artere de s = 435.
    """
    problems: list[str] = []
    for number, (ts, tx) in enumerate(TURRETS, start=1):
        if tx < 0.0:
            continue
        gap = min(abs(ts - PLANT_S[0]), abs(ts - PLANT_S[1]))
        if PLANT_S[0] <= ts <= PLANT_S[1]:
            problems.append(
                f"Turret_{number:02d} (s = {ts:.1f}) est DANS l'emprise du complexe")
        elif gap < 8.0:
            problems.append(
                f"Turret_{number:02d} (s = {ts:.1f}) n'a que {gap:.2f} m de garde "
                "au complexe, 8,00 demandes par le brief")
    if not (PLANT_S[1] < AMBRY_S[0] - 1.5 or PLANT_S[0] > AMBRY_S[1] + 1.5):
        problems.append(
            f"le complexe ({PLANT_S[0]:.1f} a {PLANT_S[1]:.1f}) mord AMBRY "
            f"({AMBRY_S[0] - 1.5:.1f} a {AMBRY_S[1] + 1.5:.1f}, colliers compris) "
            "— l'avant-poste humain est CUIT dans la peau, aucun marqueur ne le "
            "declare")
    for number, (cs, cx) in enumerate(PLANT_CONDUITS, start=1):
        if not (PLANT_S[0] <= cs - 1.45 and cs + 1.45 <= PLANT_S[1]):
            problems.append(
                f"la conduite {number:02d} (s = {cs:.1f}) deborde l'emprise "
                f"{PLANT_S[0]:.1f} a {PLANT_S[1]:.1f}")
        for v in (cs - 1.45, cs, cs + 1.45):
            lo, hi = cx - PLANT_LANE_HALF, cx + PLANT_LANE_HALF
            if lo < _pl(v, PLANT_ALLEY_XN[0]) + 0.10:
                problems.append(
                    f"la conduite {number:02d} quitte l'allee vers l'axe a "
                    f"s = {v:.1f} : {lo:.2f} contre une allee qui commence a "
                    f"{_pl(v, PLANT_ALLEY_XN[0]):.2f} (chine)")
            if hi > _pl(v, PLANT_ALLEY_XN[1]) - 0.10:
                problems.append(
                    f"la conduite {number:02d} passe SOUS le plancher a "
                    f"s = {v:.1f} : {hi:.2f} contre un plancher qui commence a "
                    f"{_pl(v, PLANT_FLOOR_XN[0]):.2f}")
    for sc, hs, side in BASINS:
        if side <= 0.0 or not (PLANT_S[0] <= sc - hs and sc + hs <= PLANT_S[1]):
            problems.append(
                f"le bassin (s = {sc:.2f} +/- {hs:.2f}) sort de l'emprise du "
                "complexe")
    inner = min(_pl(v, PLANT_XN[0])
                for v in _plant_stations(PLANT_S[0], PLANT_S[1]))
    if inner < CANAL_RIM_X + 3.0:
        problems.append(
            f"le complexe descend a x = {inner:.2f}, trop pres du canal "
            f"(rebord a {CANAL_RIM_X:.2f}) — le degagement de tir de l'artere "
            "passe par la")
    if problems:
        raise SystemExit("[long_cortege] COMPLEXE MAL POSE\n"
                         + "\n".join(f"  - {p}" for p in problems))


def _assert_moats_are_hollow() -> None:
    """La tranchee de bastion creuse VRAIMENT, et son fond est celui que le moteur ecrit.

    ⚠️ ELLE PORTE UN FOND ABSOLU, ET C'EST CE QUI LA REND FRAGILE. Les fosses se
    creusent sous la peau : elles suivent le bord quoi qu'il arrive. Celle-ci est
    posee a `MOAT_FLOOR_Y` parce que le moteur y assied `citadel_bastion`
    (`CortegeCitadel.BASTION_BASE_Y`) — les deux nombres doivent etre le meme, et
    rien dans ce fichier ne peut lire l'autre.

    Deux choses peuvent donc casser en silence : la peau qui DESCEND sous le fond
    (la tranchee cesse d'etre un creux et devient une bosse), ou la peau qui monte
    tant que le creux devient un puits. Aucune ne produirait d'erreur : le `.glb`
    resterait valide, le build vert, et le bastion se poserait dans une coque qui
    ne l'attend plus.
    """
    problems: list[str] = []
    for sc, hs, side, xs, fond in _hollows():
        if fond is None:
            continue
        stations = [v for v in (sc - hs, sc, sc + hs)]
        for v in stations:
            for k in (0, 1):
                peau = _surface_y(v, xs[k] * side)
                creux = peau - fond
                if creux < MOAT_MIN_DEPTH:
                    problems.append(
                        f"la tranchee a s = {sc:.0f} (bord {side:+.0f}) ne creuse "
                        f"que {creux:.2f} m a s = {v:.1f}, x = {xs[k] * side:+.2f} "
                        f"(peau {peau:.2f}, fond {fond:.2f}) : moins que les "
                        f"{MOAT_MIN_DEPTH:.2f} m attendus")
    if problems:
        raise SystemExit("[long_cortege] TRANCHEES TROP PLATES\n"
                         + "\n".join(f"  - {p}" for p in problems))


def _assert_pits_are_clear() -> None:
    """Aucune fosse ne mord une installation, ni une autre fosse.

    ⚠️ CE QU'ELLE EMPECHE EST INVISIBLE ET DEFINITIF. Une fosse est un TROU dans la
    peau : creusee sous un socle de tourelle, elle laisse l'affut en l'air ; sous
    un noeud d'arete, elle emporte son assise ; sous un pont d'envol, deux
    ouvertures se recouvrent et la collerette de l'une traverse le puits de
    l'autre. Rien de tout cela ne produit d'erreur — le `.glb` reste valide, le
    build reste vert, et le defaut ne se voit qu'en capture, si l'on capture
    justement la.
    """
    problems: list[str] = []
    for sc, hs, side, xs, _floor in _hollows():
        lo, hi = sc - hs - PIT_KEEPOUT, sc + hs + PIT_KEEPOUT
        x_lo = min(xs[0] * side, xs[1] * side) - PIT_KEEPOUT
        x_hi = max(xs[0] * side, xs[1] * side) + PIT_KEEPOUT
        def touches(ps: float, px: float, radius: float) -> bool:
            return (lo - radius <= ps <= hi + radius
                    and x_lo - radius <= px <= x_hi + radius)
        for number, (ts, tx) in enumerate(TURRETS, start=1):
            if touches(ts, _marker_x(ts, tx), TURRET_FOOTPRINT_R):
                problems.append(
                    f"la fosse a s = {sc:.0f} mord le socle de Turret_{number:02d} "
                    f"(s = {ts:.0f}, x = {tx:+.2f}) — l'affut resterait en l'air")
        for number, (bs, bx) in enumerate(BAYS, start=1):
            if touches(bs, bx, max(BAY_HALF_S, BAY_HALF_X)):
                problems.append(
                    f"la fosse a s = {sc:.0f} recouvre l'ouverture de Bay_{number:02d} "
                    f"(s = {bs:.0f}, x = {bx:+.2f}) — deux trous l'un dans l'autre")
        for number, ns in enumerate(SPINES, start=1):
            if lo - APRON_SPINE <= ns <= hi + APRON_SPINE and x_lo <= 0.0 <= x_hi:
                problems.append(
                    f"la fosse a s = {sc:.0f} emporte l'assise de Spine_{number:02d} "
                    f"(s = {ns:.0f})")
        if side > 0.0 and not (hi < AMBRY_S[0] or lo > AMBRY_S[1]):
            problems.append(
                f"la fosse a s = {sc:.0f} est sous Ambry ({AMBRY_S[0]:.0f} a "
                f"{AMBRY_S[1]:.0f}, tribord) — la greffe humaine perdrait son pont")
    for a in range(len(PITS)):
        for b in range(a + 1, len(PITS)):
            sa, ha, _ = PITS[a]
            sb, hb, _ = PITS[b]
            if abs(sa - sb) < ha + hb + PIT_KEEPOUT:
                problems.append(
                    f"les fosses a s = {sa:.0f} et {sb:.0f} se chevauchent")
    if problems:
        raise SystemExit("[long_cortege] FOSSES MAL POSEES\n"
                         + "\n".join(f"  - {p}" for p in problems))


def _assert_canal() -> None:
    """Le canal decrit par `CANAL_*` est-il celui que `PROFILE_BASE` dessine ?

    ⚠️ Deux ecritures d'une meme cote finissent toujours par diverger, et ce
    fichier en a deja paye deux (le coaming du hangar, l'emprise du socle de
    tourelle) : la parade est de ne jamais laisser la copie muette. Ici, les
    constantes servent aux conduits, aux travees, au kit d'epine et au
    compte-rendu ; le profil, lui, fait la peau. S'ils cessent de coincider, le
    conduit se pose sur la paroi et personne ne le voit avant le rendu.
    """
    points = {round(x, 6): y for x, y, _ in PROFILE_BASE[:6]}
    for label, x, y in (("fond du canal", 0.0, CANAL_FLOOR_Y),
                        ("pied de paroi", CANAL_FLOOR_HALF, CANAL_FLOOR_Y),
                        ("arete interne du rebord", CANAL_HALF + 0.12,
                         CANAL_RIM_Y)):
        got = points.get(round(x, 6))
        if got is None or abs(got - y) > 1e-9:
            raise ak.ContractError(
                f"canal : le profil ne porte pas {label} a (x={x}, y={y}) — "
                f"trouve {got}. Les constantes CANAL_* et PROFILE_BASE ont "
                "diverge")
    if abs(PROFILE_BASE[4][0] - CANAL_RIM_X) > 1e-9:
        raise ak.ContractError(
            f"canal : arete externe du rebord a {PROFILE_BASE[4][0]} au lieu de "
            f"{CANAL_RIM_X}")
    for start, stop in CONDUIT_LANES:
        if stop > CANAL_FLOOR_HALF - 0.10:
            raise ak.ContractError(
                f"conduit |x| in [{start}, {stop}] : il mord la paroi du canal "
                f"(fond plat jusqu'a {CANAL_FLOOR_HALF})")
    lit = 2.0 * sum(b - a for a, b in CONDUIT_LANES)
    if lit > 0.5 * 2.0 * CANAL_HALF:
        raise ak.ContractError(
            f"les conduits eclairent {lit:.2f} m sur {2 * CANAL_HALF:.2f} m de "
            "canal : le brief interdit d'occuper toute sa largeur")


def _canal_lane(s: float, x0: float, x1: float) -> tuple[float, float] | None:
    """La voie [x0, x1] tient-elle dans le FOND PLAT du canal a la station `s` ?

    Le fuseau de proue contracte la section : a s = 30 le fond ne fait plus que
    0,9 m de large, a s = 5 il n'existe pas. L'artere s'allume donc la ou le
    vaisseau devient assez large pour la porter, et pas avant — ce qui se lit,
    et ce qui evite d'ecraser quatre conduits sur 20 cm de proue.
    """
    limit = CANAL_FLOOR_HALF * _scales(s)[0] - 0.05
    if min(x0, x1) < -limit or max(x0, x1) > limit:
        return None
    return x0, x1


def spine_seat_y(s: float) -> tuple[float, float]:
    """(Y d'ASSISE du berceau d'epine, Y du point le plus bas de son emprise).

    ⚠️ Meme methode exactement que `bay_mouth_y()` et `turret_seat_y()`, et pour
    la meme raison : l'assise est le point le PLUS HAUT de l'emprise, jamais la
    peau au marqueur. Le fond du canal est plat en travers mais il MONTE dans le
    fuseau de proue (2,2 cm par metre a `Spine_01`) : prendre la peau au centre
    enterrerait le berceau d'un cote et le ferait flotter de l'autre.

    Le marqueur `Spine_NN` porte donc ce maximum : c'est le plan Y = 0 sur lequel
    TOUTES les pieces de `spine_kit.glb` sont modelisees. Le second membre donne
    le creux que la jupe enterree du berceau doit absorber.
    """
    ys: list[float] = []
    for ps in (s - SPINE_FOOTPRINT_HS, s, s + SPINE_FOOTPRINT_HS):
        for px in (-SPINE_FOOTPRINT_HX, -0.31, 0.0, 0.31, SPINE_FOOTPRINT_HX):
            ys.append(_surface_y(ps, px))
    return max(ys), min(ys)


def _merge(spans: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Fusionne des intervalles qui se recouvrent. Deterministe."""
    merged: list[tuple[float, float]] = []
    for a, b in sorted(spans):
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    return merged


def _bay_cell(i: int, s0: float, s1: float) -> tuple[float, float] | None:
    """La cellule (segment `i`, station `s0 -> s1`) est-elle DANS une ouverture ?

    Rend la baie (s, x) concernee, ou `None`. Le test est inclusif aux bords :
    les points de profil et les stations tombent EXACTEMENT dessus (voir le bloc
    des ouvertures), donc les cellules pavent l'emprise sans reste.
    """
    if not RING_ON_DECK[i]:
        return None
    lo = min(RING_X[i], RING_X[(i + 1) % RING_SIZE])
    hi = max(RING_X[i], RING_X[(i + 1) % RING_SIZE])
    for sc, xc in BAYS:
        if (lo >= xc - BAY_HALF_X - 1e-6 and hi <= xc + BAY_HALF_X + 1e-6
                and s0 >= sc - BAY_HALF_S - 1e-6
                and s1 <= sc + BAY_HALF_S + 1e-6):
            return sc, xc
    return None


def _pit_cell(i: int, s0: float, s1: float) -> tuple[float, float, float] | None:
    """La cellule (segment `i`, station `s0 -> s1`) est-elle DANS une fosse ?

    Meme mecanique que `_bay_cell` : on n'emet pas la face, et les parois sont
    posees ensuite. Les bornes sont en x NOMINAL, comme `RING_X`.
    """
    if not RING_ON_DECK[i]:
        return None
    lo = min(RING_X[i], RING_X[(i + 1) % RING_SIZE])
    hi = max(RING_X[i], RING_X[(i + 1) % RING_SIZE])
    for sc, hs, side, xs, _floor in _hollows():
        x0 = xs[0] * side
        x1 = xs[1] * side
        if (lo >= min(x0, x1) - 1e-6 and hi <= max(x0, x1) + 1e-6
                and s0 >= sc - hs - 1e-6 and s1 <= sc + hs + 1e-6):
            return sc, hs, side
    return None


def _pit_clash(s0: float, s1: float, x0: float, x1: float) -> bool:
    """Le module (s0..s1, x0..x1) mord-il l'emprise d'une fosse ?

    ⚠️ MEME DANGER QU'UNE BAIE, ET IL EST PIRE ICI PARCE QU'IL EST DISCRET. Une
    plaque qui enjambe une fosse ne flotte que de 1,55 m : assez pour se voir en
    capture, pas assez pour qu'on la cherche.
    """
    for sc, hs, side, xs, _floor in _hollows():
        xc = (xs[0] + xs[1]) * 0.5 * side
        half_x = (xs[1] - xs[0]) * 0.5 + PIT_KEEPOUT
        if not (s1 < sc - hs - PIT_KEEPOUT or s0 > sc + hs + PIT_KEEPOUT
                or x1 < xc - half_x or x0 > xc + half_x):
            return True
    return False


def _bay_clash(s0: float, s1: float, x0: float, x1: float) -> bool:
    """Le module (s0..s1, x0..x1) mord-il l'emprise d'un pont d'envol ?

    Avant BRIEF-0091 la question ne se posait pas : le coaming etait POSE, une
    plaque qui passait dessous restait cachee. Une plaque qui traverse une
    OUVERTURE, elle, flotte au-dessus du vide.
    """
    for sc, xc in BAYS:
        if not (s1 < sc - BAY_KEEPOUT_S or s0 > sc + BAY_KEEPOUT_S
                or x1 < xc - BAY_KEEPOUT_X or x0 > xc + BAY_KEEPOUT_X):
            return True
    return False


#: ⚠️ RAYON DE DEGAGEMENT D'UN AFFUT — 2,50 m, ET NON `TURRET_FOOTPRINT_R`.
#: `TURRET_FOOTPRINT_R` (2,08) est l'emprise de la classe NATIVE du kit. Le
#: moteur en pose trois depuis BRIEF-0100, et la lourde est a l'echelle 1,200 :
#: son emprise vaut 2,08 x 1,200 = 2,496, arrondi a 2,50.
#:
#: ⚠️ ET ON DEGAGE 2,50 PARTOUT, SANS SAVOIR QUELLE CLASSE VA OU. Le choix de la
#: classe est une decision de gameplay (`cortege_hardpoints.gd`) ; faire lire le
#: moteur par la forge creerait une dependance a l'envers. Prendre la plus grande
#: des trois rend aussi le resultat robuste : re-classer une tourelle demain ne
#: rouvrira pas le defaut.
TURRET_KEEPOUT_R = 2.50

#: (station, x du marqueur, Y d'assise) des dix-sept affuts. Calcule une fois :
#: `turret_seat_y()` coute 41 appels a `_surface_y` et le degagement se teste des
#: milliers de fois par troncon. Pur produit des constantes, donc deterministe.
_TURRET_SEATS: list[tuple[float, float, float]] = []


def _turret_seats() -> list[tuple[float, float, float]]:
    if not _TURRET_SEATS:
        for ts, tx in TURRETS:
            mx = _marker_x(ts, tx)
            _TURRET_SEATS.append((ts, mx, turret_seat_y(ts, mx)[0]))
    return _TURRET_SEATS


#: Largeur d'un casier de recherche, en metres, pour la mesure de degagement du
#: `.glb` : elle depasse `TURRET_KEEPOUT_R`, donc un sommet ne peut appartenir
#: qu'au casier d'un affut ou a l'un de ses deux voisins. Sans ce classement, la
#: mesure comparerait 140 000 sommets a dix-sept disques, un a un.
TURRET_BUCKET = 5.0


def _turret_lookup() -> dict[int, list[tuple[str, float, float, float]]]:
    """Les affuts ranges par casier de `TURRET_BUCKET` metres de station."""
    out: dict[int, list[tuple[str, float, float, float]]] = {}
    for number, (ts, mx, seat) in enumerate(_turret_seats(), start=1):
        out.setdefault(int(math.floor(ts / TURRET_BUCKET)), []).append(
            (f"Turret_{number:02d}", ts, mx, seat))
    return out


def _turret_clash(s0: float, s1: float, x0: float, x1: float,
                  top_y: float = BUILD_CEILING_Y) -> bool:
    """Le module (s0..s1, x0..x1), dessus a `top_y`, monte-t-il SOUS un affut ?

    ⚠️ LE QUATRIEME GARDE, ET IL MANQUAIT DEPUIS TOUJOURS. `_posed_clash`,
    `_bay_clash` et `_pit_clash` protegent trois choses que la peau porte ;
    personne ne protegeait la TOURELLE. Le garde existait pourtant, ecrit dans
    `_assert_bastions_are_clear` — « ⚠️ ET AUCUN SOUS UNE TOURELLE :
    `turret_seat_y()` echantillonne la peau et non les modules, donc un affut
    pose sur un bastion s'y enfoncerait » — et il n'avait jamais ete etendu aux
    familles qui se SEMENT. Resultat mesure sur le binaire du 2026-09-06 : une
    greffe montait 1,010 m au-dessus de l'assise de `Turret_01`, soit le socle
    (+0,27), la couronne (+0,40) et les deux tiers du bloc (+1,52) noyes.

    ⚠️ ET LE CRITERE EST LE PLAN D'ASSISE, PAS LA PEAU. Interdire tout relief
    dans le disque rendrait le borde PLAT autour des dix-sept installations —
    exactement ce que BRIEF-0094 venait de corriger, et son intention est « une
    tourelle, et la machinerie autour ». Ce qui enterre un affut, c'est ce qui
    passe AU-DESSUS du plan sur lequel `turret_kit.glb` est modelise : le kit ne
    montre rien sous ce plan-la. Un massif pose 0,40 m plus bas sur la peau et
    haut de 0,34 reste donc sous le socle — il entoure, il n'enterre pas.
    Le defaut est de toute facon le meme : `top_y` d'un module de ce fichier vaut
    `min(peau aux coins) + rise`, donc une valeur, pas une surface.

    `top_y` vaut par defaut le PLAFOND DE CONSTRUCTION, c'est-a-dire « plus haut
    que tout ce que ce fichier sait batir » : l'appeler sans cet argument, c'est
    interdire l'emprise tout court. C'est ce que font les greffes, qui montent de
    0,70 a 1,05 m et depassent l'assise dans tous les cas.
    """
    r2 = TURRET_KEEPOUT_R * TURRET_KEEPOUT_R
    for ts, mx, seat in _turret_seats():
        if top_y <= seat + 1e-6:
            continue
        dx = max(x0 - mx, 0.0, mx - x1)
        ds = max(s0 - ts, 0.0, ts - s1)
        if dx * dx + ds * ds < r2:
            return True
    return False


def _box_top(x0: float, x1: float, s0: float, s1: float, rise: float) -> float:
    """Le Y du dessus qu'aura `_surface_box(x0, x1, s0, s1, rise, ...)`.

    Meme formule exactement — `min(peau aux quatre coins) + rise` —, mais SANS
    emettre : c'est ce qui permet de decider AVANT de poser. Deux expressions de
    la meme regle qui derivent en silence, c'est un module dont la garde juge une
    hauteur que la geometrie n'a pas.
    """
    return min(_surface_y(s, x)
               for x, s in ((x0, s0), (x1, s0), (x1, s1), (x0, s1))) + rise


def _bay_free_spans(x0: float, x1: float,
                    s0: float, s1: float) -> list[tuple[float, float]]:
    """Decoupe [s0, s1] en morceaux qui n'entrent dans aucune emprise de baie.

    Les lisses sont le seul module CONTINU du decor (jusqu'a 97 m) : les rejeter
    en bloc des qu'ils croisent une baie supprimerait la seule lecture continue
    de la vitesse. On les coupe, on ne les retire pas.
    """
    spans = [(s0, s1)]
    cuts = sorted((sc - BAY_KEEPOUT_S, sc + BAY_KEEPOUT_S) for sc, xc in BAYS
                  if not (x1 < xc - BAY_KEEPOUT_X or x0 > xc + BAY_KEEPOUT_X))
    for a, b in cuts:
        kept: list[tuple[float, float]] = []
        for c, d in spans:
            if b <= c or a >= d:
                kept.append((c, d))
                continue
            if c < a:
                kept.append((c, a))
            if b < d:
                kept.append((b, d))
        spans = kept
    return [(a, b) for a, b in spans if b - a >= 3.0]


#: Largeur du coaming de `bay_kit.glb` autour de l'ouverture. Il n'est pas dans
#: ce maillage-ci, mais il existe VRAIMENT en jeu : un socle qui entre dedans
#: touche une piece posee. ⚠️ `build_bay_kit.COAM_W` doit valoir la meme chose, et
#: le kit — qui importe ce module — le reverifie a chaque build : les deux
#: valeurs ne peuvent plus deriver l'une de l'autre en silence.
BAY_COAMING_W = 0.80

#: ⚠️ PROXIMITES ACCEPTEES — DECIDEES, MESUREES, ET ECRITES ICI POUR QU'ON NE LES
#: « CORRIGE » PAS. Une paire qui figure ci-dessous n'est pas un oubli : c'est un
#: arbitrage. Sans cette table, le prochain lecteur verrait un defaut la ou il y a
#: une intention, et deplacerait un marqueur qui va bien.
#:
#: (tourelle, baie, raison — la raison est obligatoire, c'est tout l'interet)
#: ⚠️ ELLE EST VIDE DEPUIS LE REPOSITIONNEMENT DU 2026-09-03, ET C'EST LE HARNAIS
#: QUI L'A EXIGE. Elle declarait `Turret_14`/`Bay_07` — « la levre du socle
#: effleure le coaming sur 0,25 m », arbitrage du BRIEF-0092. Le backlog notait
#: depuis le 2026-08-30 que ce chiffre etait PERIME : depuis le kit, ce qui
#: depasse n'est plus une levre statique mais un canon qui balaie a ~0,55 m.
#: Le repositionnement a ecarte les deux pieces, et le generateur a refuse de
#: laisser la ligne mentir — « retirer sa ligne plutot que de la laisser
#: mentir ». Une dette du backlog fermee par une assertion, pas par une relecture.
ACCEPTED_PAD_BAY_PROXIMITY: tuple[tuple[str, str, str], ...] = ()


def _pad_bay_clearances() -> list[tuple[str, str, float, float, bool]]:
    """(tourelle, baie, marge a l'OUVERTURE, marge au COAMING, centre sur le vide).

    Distance du centre du socle au RECTANGLE de l'ouverture : c'est la seule
    mesure qui vaille, un socle est un disque et une ouverture un rectangle. Une
    marge NEGATIVE est une penetration.

    Deux seuils et non un, parce que les deux fautes n'ont pas la meme gravite :
    entrer dans l'OUVERTURE, c'est poser une tourelle au-dessus du vide ; toucher
    le COAMING, c'est effleurer une piece voisine — credible tant que c'est
    declare.
    """
    out: list[tuple[str, str, float, float, bool]] = []
    for number, (ts, tx) in enumerate(TURRETS, start=1):
        radius = PAD_RADIUS[int(ts // SECTION_LENGTH)]
        for index, (bs, bx) in enumerate(BAYS, start=1):
            dx = max(abs(tx - bx) - BAY_HALF_X, 0.0)
            ds = max(abs(ts - bs) - BAY_HALF_S, 0.0)
            distance = math.hypot(dx, ds)
            out.append((f"Turret_{number:02d}", f"Bay_{index:02d}",
                        distance - radius,
                        distance - radius - BAY_COAMING_W,
                        dx == 0.0 and ds == 0.0))
    return out


def _marker_clashes() -> list[str]:
    """LE GARDE MUTUEL `TURRETS` / `BAYS`, sur le modele de `JOINT_CLEARANCE`.

    ⚠️ DEUX MARQUEURS POSES A LA MAIN A 2 m L'UN DE L'AUTRE N'AURAIENT JAMAIS DU
    PASSER. Ils sont passes : `Turret_02` avait son centre dans l'ouverture de
    `Bay_01` et `Turret_05` mordait `Bay_03` de 0,70 m, depuis BRIEF-0089 — six
    semaines sans un mot, parce que le coaming POSE de l'epoque recouvrait le
    socle et que deux masses sombres vues a 20 deg de la verticale ne faisaient
    qu'un seul bouton. C'est l'ouverture reelle qui l'a revele, pas un test.

    Ces tables se remplissent a la main, exprès (une position de gameplay se
    decide) ; elles doivent donc etre RELUES par une machine, exactement comme les
    modules le sont par `JOINT_CLEARANCE`. Trois regles :

      * aucun socle dans une OUVERTURE — jamais, sans exception possible ;
      * un socle qui touche un COAMING doit etre declare dans
        `ACCEPTED_PAD_BAY_PROXIMITY`, avec sa raison ;
      * deux socles ne se recouvrent pas, deux ouvertures (coaming compris) non
        plus.

    Et la reciproque : une proximite declaree qui n'existe plus doit disparaitre
    de la table, sans quoi celle-ci se met a mentir.
    """
    problems: list[str] = []
    declared = {(t, b): why for t, b, why in ACCEPTED_PAD_BAY_PROXIMITY}
    seen: set[tuple[str, str]] = set()
    for turret, bay, mouth_gap, coam_gap, centred in _pad_bay_clearances():
        if mouth_gap < 0.0:
            problems.append(
                f"{turret} entre de {-mouth_gap:.2f} m dans l'OUVERTURE de {bay}"
                f"{' — son centre est au-dessus du vide' if centred else ''} : "
                "une tourelle ne se pose pas sur un trou. Corriger le `s` de la "
                "ligne dans TURRETS ou dans BAYS (arbitrage de conception)")
            continue
        if coam_gap < 0.0:
            seen.add((turret, bay))
            if (turret, bay) not in declared:
                problems.append(
                    f"{turret} touche le coaming de {bay} sur {-coam_gap:.2f} m "
                    "sans etre declare : soit on l'ecarte, soit on l'ASSUME dans "
                    "ACCEPTED_PAD_BAY_PROXIMITY avec sa raison")
    for turret, bay in declared:
        if (turret, bay) not in seen:
            problems.append(
                f"la proximite declaree {turret}/{bay} n'existe plus : retirer sa "
                "ligne d'ACCEPTED_PAD_BAY_PROXIMITY plutot que de la laisser "
                "mentir")

    for a in range(len(TURRETS)):
        sa, xa = TURRETS[a]
        ra = PAD_RADIUS[int(sa // SECTION_LENGTH)]
        for b in range(a + 1, len(TURRETS)):
            sb, xb = TURRETS[b]
            rb = PAD_RADIUS[int(sb // SECTION_LENGTH)]
            gap = math.hypot(sa - sb, xa - xb) - (ra + rb)
            if gap < 0.0:
                problems.append(
                    f"les socles Turret_{a + 1:02d} et Turret_{b + 1:02d} se "
                    f"recouvrent de {-gap:.2f} m")
    for a in range(len(BAYS)):
        sa, xa = BAYS[a]
        for b in range(a + 1, len(BAYS)):
            sb, xb = BAYS[b]
            ds = abs(sa - sb) - 2.0 * (BAY_HALF_S + BAY_COAMING_W)
            dx = abs(xa - xb) - 2.0 * (BAY_HALF_X + BAY_COAMING_W)
            if ds < 0.0 and dx < 0.0:
                problems.append(
                    f"les ouvertures Bay_{a + 1:02d} et Bay_{b + 1:02d} se "
                    f"chevauchent (coaming compris) de {-max(ds, dx):.2f} m")
    return problems


def bay_mouth_y(s: float, x: float) -> tuple[float, float]:
    """(Y de la BOUCHE, Y du point le plus bas du pourtour) d'une ouverture.

    ⚠️ La bouche est le point le PLUS HAUT du pourtour, pas la peau au marqueur,
    et ce n'est pas un detail : l'ouverture de 6,00 m enjambe la chine, qui vaut
    0,60 m de denivele. Prendre la peau au centre poserait le coaming du kit
    SOUS le pont interieur d'un cote — le hangar disparaitrait a moitie dans la
    coque. Le marqueur `Bay_NN` porte donc ce maximum : c'est le plan sur lequel
    tout le kit est modelise.
    """
    xs = [x - BAY_HALF_X, x + BAY_HALF_X]
    xs += [xr for xr in RING_X
           if x - BAY_HALF_X < xr < x + BAY_HALF_X]
    ys = [_surface_y(ps, px)
          for px in xs
          for ps in (s - BAY_HALF_S, s, s + BAY_HALF_S)]
    return max(ys), min(ys)


# --------------------------------------------------------------------------
# LE RYTHME — ou l'on a le droit de poser du relief (BRIEF-0094, priorite 3)
# --------------------------------------------------------------------------


def _installation_spans() -> tuple[tuple[float, float, str, float], ...]:
    """Les emprises d'installation, en `s` global : (s0, s1, nom, x).

    C'est la SEULE table qui decide ou le vocabulaire modulaire a le droit de
    poser quelque chose. Elle est derivee des marqueurs, jamais ecrite a la main :
    deplacer une tourelle deplace son ancrage, et une zone calme ne peut pas se
    retrouver a couvrir un hangar par oubli de mise a jour.

    Le `x` en sert autant que le `s` : une nervure d'ancrage se pose du BORD de
    son installation, pas en travers de tout le vaisseau.
    """
    spans: list[tuple[float, float, str, float]] = []
    for number, (s, x) in enumerate(TURRETS, start=1):
        spans.append((s - APRON_TURRET, s + APRON_TURRET,
                      f"Turret_{number:02d}", x))
    for number, (s, x) in enumerate(BAYS, start=1):
        spans.append((s - APRON_BAY, s + APRON_BAY, f"Bay_{number:02d}", x))
    for number, s in enumerate(SPINES, start=1):
        spans.append((s - APRON_SPINE, s + APRON_SPINE,
                      f"Spine_{number:02d}", 0.0))
    spans.append((AMBRY_S[0] - APRON_AMBRY, AMBRY_S[1] + APRON_AMBRY,
                  "Ambry", 0.5 * (AMBRY_X[0] + AMBRY_X[1])))
    # ⚠️ LE COMPLEXE N'Y EST PAS, ET C'EST UNE CORRECTION MESUREE. Il y a d'abord
    # ete inscrit — c'est une installation, et « un module de relief ne se pose
    # que dans l'emprise d'une installation » (BRIEF-0094). La capture a montre
    # le prix : `MARKER_APRONS` est la FUSION des emprises et ne garde AUCUN x,
    # si bien qu'ouvrir 27,7 m a tribord les ouvre aussi a BABORD. Le bord
    # oppose, vide en face du complexe, s'est couvert de quarante-cinq plaques —
    # exactement le « detail presque partout » que BRIEF-0094 avait supprime, et
    # le calme du troncon 5 tombait de 43,8 a 19,2 pct.
    #
    # Le complexe porte donc son propre appareillage (longerons, plots, traverses,
    # berceaux) et ne demande rien au vocabulaire seede. Consequence voulue : les
    # cinq troncons gardent leurs modules seedes AU BIT PRES, et ce lot est une
    # pure addition. Son emprise entre quand meme dans le compte de calme —
    # `build_section()` l'ajoute a `occupied` comme les fosses et la passerelle.
    return tuple(sorted(spans))


INSTALLATION_SPANS = _installation_spans()
#: Les memes, fusionnees : c'est la carte des zones OCCUPEES par les marqueurs.
MARKER_APRONS = _merge([(a, b) for a, b, _n, _x in INSTALLATION_SPANS])


def _free_gaps() -> tuple[tuple[float, float], ...]:
    """Les PLAGES NUES entre deux emprises de marqueur, proue -> poupe.

    ⚠️ Cette table est le livrable « zones calmes » avant meme d'etre un outil :
    elle dit, avant le premier sommet, ou le vaisseau respire. Mesuree sur les
    marqueurs livres, elle rend 21 plages dont plusieurs de 15 a 22 m — la
    sequence exacte que le brief demande (« 15-20 m calmes → une installation →
    zone calme → un hangar »). Le maillage n'a plus qu'a ne pas la detruire.
    """
    gaps: list[tuple[float, float]] = []
    cursor = 0.0
    for a, b in MARKER_APRONS:
        if a > cursor:
            gaps.append((cursor, a))
        cursor = max(cursor, b)
    if cursor < SHIP_LENGTH:
        gaps.append((cursor, SHIP_LENGTH))
    return tuple(gaps)


FREE_GAPS = _free_gaps()


def _inside_zone(s0: float, s1: float) -> bool:
    """Le module (s0..s1) tient-il ENTIEREMENT dans une emprise de marqueur ?

    ⚠️ CONTENANCE, ET SURTOUT PAS INTERSECTION. La premiere version testait
    l'intersection : une greffe de 11 m qui effleurait le bord d'une emprise de
    8,4 m debordait de 10 m sur la plage nue voisine, une plaque acceptee au
    contact debordait de 3, et de proche en proche la part calme mesuree tombait
    a 13 pct pour un plafond theorique de 50. Un module qui deborde ne « depasse »
    pas un peu : il DEPLACE la frontiere, et la frontiere est le livrable.
    """
    for a, b in MARKER_APRONS:
        if a <= s0 and s1 <= b:
            return True
    return False


def _in_apron(s0: float, s1: float, spans: list[tuple[float, float]]) -> bool:
    """Le module (s0..s1) touche-t-il l'emprise d'une installation ?

    ⚠️ `spans` contient les emprises des MARQUEURS *et* celles des GREFFES, qui
    ne sont connues qu'apres tirage. C'est pourquoi les greffes sont maillees en
    premier dans `build_section()` : le brief pose la sequence « 15-20 m calmes →
    une installation → zone calme → un hangar → calme → un groupe de tourelles »,
    et « une installation » y designe justement une masse greffee, distincte du
    hangar et des tourelles. Une greffe est donc un point d'ancrage, pas un
    module a ancrer.
    """
    for a, b in spans:
        if s0 <= b and s1 >= a:
            return True
    return False


#: Marge d'ancrage autour d'une greffe : c'est la que les plaques et les
#: pastilles ont le droit de se poser pour la relier au borde.
APRON_GRAFT = 2.4


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


def _face_towards(bm: bmesh.types.BMesh, verts: list, material: str,
                  target: Vector):
    """Pose une face et GARANTIT que sa normale pointe vers `target`.

    ⚠️ CE FICHIER N'APPELLE PAS `recalc_face_normals`, ET C'EST DELIBERE : les
    troncons 2 a 5 sont des tubes ouverts aux deux bouts, ou l'heuristique se
    trompe et retourne la coque entiere (voir `_assert_skin_outward`). Le sens
    d'une face neuve est donc EXACTEMENT celui de l'ordre de ses sommets — et
    raisonner sur cet ordre marche pour le fond d'une fosse, echoue pour sa paroi
    interieure, remarche pour sa paroi exterieure, et s'inverse a nouveau quand la
    fosse passe a babord. Quatre chances de se tromper par fosse.

    Une face mal orientee ne produit aucune erreur : elle DISPARAIT simplement en
    jeu (culling arriere), et le journal reste muet. Declarer la direction voulue
    plutot que l'ordre des sommets rend l'intention lisible et le defaut impossible.
    """
    face = _face(bm, verts, material)
    if face is None:
        return None
    face.normal_update()
    if face.normal.dot(target) < 0.0:
        face.normal_flip()
    return face


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


def _quad_facing(bm: bmesh.types.BMesh, a, b, c, d, material: str, want: Vector):
    """Un quad dont la normale part du cote `want`. DETERMINISTE.

    Le bobinage est ici CALCULE et non ecrit a la main : la collerette d'une baie
    fait le tour de l'ouverture et son sens change a chaque coin. Une regle
    ecrite a la main y serait fausse une fois sur deux, et une face retournee ne
    se voit sur aucune mesure — elle disparait, simplement.
    """
    verts = [a, b, c, d]
    normal = (b.co - a.co).cross(c.co - a.co)
    if normal.dot(want) < 0.0:
        verts.reverse()
    return _face(bm, verts, material)


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


def _surface_poly(bm: bmesh.types.BMesh, plan: list[tuple[float, float]],
                  rise: float, sink: float,
                  side_material: str, top_material: str,
                  draft: float = 0.0) -> float:
    """`_surface_box` pour une empreinte QUELCONQUE — c'est ce qui donne aux
    greffes une ORIENTATION.

    ⚠️ ELLE EXISTE POUR UNE PHRASE DU BRIEF, ET LA PHRASE EST UNE REGLE DE
    LISIBILITE : « une greffe doit se distinguer par sa HAUTEUR, son ORIENTATION
    et sa SILHOUETTE, pas par sa couleur ». Toutes les primitives de ce fichier
    etaient alignees sur les axes du vaisseau, si bien que la seule chose qui
    distinguait une greffe du borde etait son `AA_Panel` violet — d'ou les
    « decals arbitraires » de l'operateur. Une empreinte tournee de 12 a 22 deg
    se lit comme une piece RAPPORTEE des la premiere image, sans une once de
    couleur.

    `plan` : les sommets (x, s) dans l'ordre qui rend la face du dessus normale
    +Y — c'est-a-dire l'ordre de `_surface_box` (x croissant, puis s croissant),
    conserve par toute rotation appliquee uniformement dans le plan (x, s), une
    rotation preservant l'orientation. Rend le Y du dessus.
    """
    ys = [_surface_y(s, x) for x, s in plan]
    top_y = min(ys) + rise
    bottom_y = min(ys) - sink
    cx = sum(x for x, _ in plan) / len(plan)
    cs = sum(s for _, s in plan) / len(plan)
    inner: list[tuple[float, float]] = []
    for x, s in plan:
        dx, ds = cx - x, cs - s
        length = math.hypot(dx, ds)
        # Le retrait est une DISTANCE, borne a la moitie du rayon : sur une
        # empreinte etroite, un retrait fixe retournerait le polygone.
        step = min(draft, length * 0.45) / length if length > 1e-9 else 0.0
        inner.append((x + dx * step, s + ds * step))
    bv = [bm.verts.new(Vector((x, bottom_y, _z(s)))) for x, s in plan]
    tv = [bm.verts.new(Vector((x, top_y, _z(s)))) for x, s in inner]
    _face(bm, tv, top_material)
    _face(bm, list(reversed(bv)), side_material)
    for i in range(len(plan)):
        j = (i + 1) % len(plan)
        _quad(bm, bv[i], bv[j], tv[j], tv[i], side_material)
    return top_y


def _yawed_plan(cx: float, cs: float, half_x: float, half_s: float,
                yaw: float) -> list[tuple[float, float]]:
    """Empreinte rectangulaire tournee de `yaw` (rad) autour de (cx, cs)."""
    ca, sa = math.cos(yaw), math.sin(yaw)
    corners = ((-half_x, -half_s), (half_x, -half_s),
               (half_x, half_s), (-half_x, half_s))
    return [(cx + dx * ca - ds * sa, cs + dx * sa + ds * ca)
            for dx, ds in corners]


def _plan_bounds(plan: list[tuple[float, float]]) -> tuple[float, float,
                                                           float, float]:
    """(x0, x1, s0, s1) englobants — les gardes travaillent sur des boites."""
    xs = [x for x, _ in plan]
    ss = [s for _, s in plan]
    return min(xs), max(xs), min(ss), max(ss)


# ⚠️ `_lathe()` A DISPARU AVEC `build_spine_bulb()` (BRIEF-0094). C'etait son seul
# appelant : le bulbe d'arete dorsale etait la seule revolution de ce decor. Les
# solides de revolution du niveau vivent maintenant dans les kits — `turret_pad`,
# `turret_ring`, `spine_core` —, ou ils sont modelises par lofts d'anneaux avec un
# bobinage CALCULE piece par piece. Garder ici une primitive que rien n'appelle,
# c'est garder une reponse a une question qu'on ne pose plus.




# ==========================================================================
# La peau — le prisme et son fuseau de proue
# ==========================================================================


def _stations(index: int) -> list[float]:
    """Stations (en `s` global) du troncon `index` (0-base), proue -> poupe.

    ⚠️ Les bords des ouvertures de baie EN SONT (BRIEF-0091). Sans station a
    `s_baie +/- 4,25`, l'emprise ne serait pas pavee par des cellules entieres
    et « ne pas emettre les faces » rendrait un trou aux cotes approchees.
    """
    s0 = index * SECTION_LENGTH
    s1 = s0 + SECTION_LENGTH
    if index > 0:
        steps = 20                       # 5,00 m : le pas de base
        values = [s0 + (s1 - s0) * k / steps for k in range(steps + 1)]
        # ⚠️ ET DES STATIONS EN PLUS LA OU LA LARGEUR BOUGE. Le pas de 5,00 m
        # datait d'une coque a profil CONSTANT au-dela du fuseau ; depuis que
        # `TAPER` va jusqu'a la poupe, une transition de douze metres n'aurait
        # que deux segments pour tourner. Le contour se lirait en facettes — et
        # une facette de six metres sur un vaisseau de 6,8 km se voit.
        # ⚠️ LES DEUX TABLES, ET PAS SEULEMENT `TAPER`. Une transition d'asymetrie
        # fait douze metres comme les autres : la laisser au pas de 5,00 m
        # donnerait deux segments pour tourner, et le bord qui se pince se
        # lirait en facettes — precisement sur le cote que la consigne 14 veut
        # faire remarquer.
        edges: list[tuple[float, float]] = []
        for a, b in zip(TAPER, TAPER[1:]):
            if abs(a[1] - b[1]) > 1e-6:
                edges.append((a[0], b[0]))
        for a, b in zip(ASYMMETRY, ASYMMETRY[1:]):
            if abs(a[1] - b[1]) > 1e-6 or abs(a[2] - b[2]) > 1e-6:
                edges.append((a[0], b[0]))
        for lo, hi in edges:
            v = max(lo, s0)
            stop = min(hi, s1)
            while v < stop - 1e-6:
                values.append(v)
                v += 1.25
            if s0 <= stop <= s1:
                values.append(stop)
    else:
        # Troncon 1 : le fuseau demande de la finesse la ou il tourne.
        values = [0.0, 0.8, 1.8, 3.0, 4.2]
        v = 6.0
        while v < 58.0 - 1e-6:
            values.append(v)
            v += 3.0
        # ⚠️ `PROW_TAPER_END` ET NON `TAPER_END`, ET LA CONFUSION A ETE PAYEE. Les
        # deux ont longtemps valu 88,0 : la table s'arretait au fuseau. Depuis
        # qu'elle va jusqu'a la poupe, `TAPER_END` vaut 500 — et cette boucle,
        # inchangee, a seme le TRONCON 1 de stations jusqu'a z = -500. Le `.glb`
        # restait valide ; c'est le harnais de jonction qui l'a vu, en annoncant
        # 400 m d'ecart entre deux troncons voisins. Ce qui borne cette boucle
        # est la fin du FUSEAU, pas la fin de la table.
        v = 58.0
        while v < PROW_TAPER_END - 1e-6:
            values.append(v)
            v += 3.75
        values.append(PROW_TAPER_END)
        values += [91.0, 94.0, 97.0, 100.0]
    for sc, _ in BAYS:
        if s0 <= sc < s1:
            values += [sc - BAY_HALF_S, sc + BAY_HALF_S]
    # ⚠️ ET LES BORDS DES FOSSES, POUR LA MEME RAISON QUE LES BAIES. Sans station a
    # `sc +/- hs`, l'emprise n'est pas pavee par des cellules entieres et « ne pas
    # emettre les faces » rend un creux aux cotes approchees — plus large ou plus
    # court que ses parois, avec un jour tout autour.
    for sc, hs, _side, _xs, _floor in _hollows():
        if s0 <= sc < s1:
            values += [sc - hs, sc + hs]
    return sorted({round(v, 6) for v in values})


def build_skin(bm: bmesh.types.BMesh, index: int) -> int:
    """Le prisme du troncon, en coordonnees LOCALES (z de 0 a -100).

    ⚠️ IL EST GENERE AVEC SES OUVERTURES (BRIEF-0091). Aucun booleen : la
    cellule qui tombe dans l'emprise d'un pont d'envol n'est simplement PAS
    emise. Rend le nombre de cellules sautees — imprime a chaque build, parce
    qu'une famille de faces qui disparait en silence est deja arrivee ici
    (`_clip_lane`, BRIEF-0089).
    """
    stations = _stations(index)
    rings: list[list] = []
    for s in stations:
        ring = [bm.verts.new(Vector((x, y, _z(s)))) for x, y in _ring(s)]
        rings.append(ring)
    skipped = 0
    for k in range(len(stations) - 1):
        front, back = rings[k], rings[k + 1]
        s0, s1 = stations[k], stations[k + 1]
        for i in range(RING_SIZE):
            if _bay_cell(i, s0, s1) is not None or _pit_cell(i, s0, s1) is not None:
                skipped += 1
                continue
            j = (i + 1) % RING_SIZE
            _face(bm, [front[i], front[j], back[j], back[i]], RING_MATERIALS[i])
    if index == 0:
        # La pointe : 22 cm de large, fermee pour que la proue ne soit pas un tube.
        _cap(bm, rings[0], "AA_Trim", facing_front=True)
    if index == SECTION_COUNT - 1:
        # La coupe de poupe : les troncons 6 et 7 appartiennent au niveau 3, mais
        # ce bord-la EST vu a la fin du niveau. On le ferme.
        _cap(bm, rings[-1], "AA_Greeble", facing_front=False)
    return skipped


def build_pits(bm: bmesh.types.BMesh, index: int) -> int:
    """Creuse les fosses du troncon : quatre parois et un fond.

    ⚠️ LE FOND EST PLAT, LES PAROIS EPOUSENT LA PEAU. Le pont descend de 8 cm entre
    |x| = 2,20 et 6,80 ; un fond qui suivrait cette pente ferait une fosse dont on
    ne lit pas le niveau. Un fond plat, lui, donne une horizontale franche au creux
    — et c'est ce qui le fait lire comme un volume plutot que comme une tache
    sombre.

    ⚠️ LES ABSCISSES SONT MISES A L'ECHELLE DU BORD, comme la peau. Prendre les x
    nominaux poserait les parois a cote du trou partout ou la coque respire.

    Rend le nombre de quads poses.
    """
    origin = index * SECTION_LENGTH
    quads = 0
    for sc, hs, side, PIT_X, fond in _hollows():
        if not (origin <= sc < origin + SECTION_LENGTH):
            continue
        s_lo, s_hi = sc - hs, sc + hs
        stations = [v for v in _stations(index) if s_lo - 1e-6 <= v <= s_hi + 1e-6]
        if len(stations) < 2:
            continue
        # Le fond : sous le point le PLUS BAS de l'emprise, pour qu'il soit
        # partout au moins a `PIT_DEPTH` de la peau.
        # ⚠️ UN FOND ABSOLU QUAND LE MOTEUR EN DEPEND, DERIVE SINON. Les fosses
        # se creusent SOUS la peau (leur fond suit le bord) ; les tranchees de
        # bastion, elles, portent l'assise d'une piece de kit posee a une cote
        # ECRITE — la faire deriver ferait flotter le bastion sans un mot.
        floor = fond if fond is not None else min(
            _surface_y(v, PIT_X[k] * side)
            for v in stations for k in (0, 1)) - PIT_DEPTH

        def edge(v: float, k: int) -> float:
            return PIT_X[k] * side * _side_scale(v, side)

        # ⚠️ LE FOND EST EN MATIERE DE COQUE, LES PAROIS EN NOIR DE CREUX — ET
        # C'EST L'INVERSE DE LA PREMIERE ECRITURE, CORRIGE EN REGARDANT. Un fond
        # `AA_Greeble` (#141419) rendait la fosse comme un APLAT NOIR : le meme
        # defaut que `BRIEF-0094` reprochait aux greffes, « des aplats, pas des
        # volumes ». Pire, il mettait un second grand noir dans le cadre, alors que
        # l'artere doit rester LE creux du vaisseau — la raison meme pour laquelle
        # la contremarche de chine est repassee en `AA_Hull`.
        # Le creux se lit desormais par ses PAROIS sombres et l'ombre qu'elles
        # portent, et son fond reste de la matiere de coque : un plancher plus bas,
        # et non un trou.
        #
        # ⚠️ CHAQUE FACE DECLARE OU ELLE REGARDE. Toutes les normales d'une fosse
        # pointent vers son INTERIEUR : le fond vers le haut, les deux parois
        # longues l'une vers l'autre, les bouts l'un vers l'autre. C'est la seule
        # formulation qui reste juste quand la fosse passe a babord — ou tous les
        # signes en x s'inversent.
        # --- le fond ---------------------------------------------------------
        for a, b in zip(stations, stations[1:]):
            _face_towards(bm, [
                bm.verts.new(Vector((edge(a, 0), floor, _z(a)))),
                bm.verts.new(Vector((edge(a, 1), floor, _z(a)))),
                bm.verts.new(Vector((edge(b, 1), floor, _z(b)))),
                bm.verts.new(Vector((edge(b, 0), floor, _z(b)))),
            ], "AA_Hull", Vector((0.0, 1.0, 0.0)))
            quads += 1
        # --- les deux parois longues -----------------------------------------
        # La paroi interieure (k = 0) regarde vers le large, l'exterieure (k = 1)
        # regarde vers l'axe : les deux vers le creux.
        for k, inward in ((0, 1.0), (1, -1.0)):
            for a, b in zip(stations, stations[1:]):
                ya = _surface_y(a, PIT_X[k] * side)
                yb = _surface_y(b, PIT_X[k] * side)
                _face_towards(bm, [
                    bm.verts.new(Vector((edge(a, k), ya, _z(a)))),
                    bm.verts.new(Vector((edge(b, k), yb, _z(b)))),
                    bm.verts.new(Vector((edge(b, k), floor, _z(b)))),
                    bm.verts.new(Vector((edge(a, k), floor, _z(a)))),
                ], "AA_Greeble", Vector((inward * side, 0.0, 0.0)))
                quads += 1
        # --- les deux parois de bout ------------------------------------------
        # ⚠️ ELLES SONT CLAIRES, ET C'EST LA CORRECTION QUI A RENDU LA FOSSE
        # LISIBLE. Fond anthracite et parois noires, le creux existait dans le
        # `.glb` — sondee, mesuree, rendue — et restait INVISIBLE en jeu : a 23
        # px/m sous une camera qui plonge a 70°, il se confondait avec les bandes
        # sombres du borde. Le pont d'envol voisin, lui, se lit d'un coup d'œil :
        # il a un coaming CLAIR. Sans arete claire, un creux n'est pas un volume,
        # c'est une tache.
        #
        # ⚠️ SEULEMENT LES DEUX BOUTS, ET NON TOUT LE POURTOUR. `BRIEF-0089` a
        # mesure qu'« un materiau clair sur une arete CONTINUE occupe plus de
        # pixels qu'une piece entiere ». Deux plans de 4,6 m accrochent la lumiere
        # et disent « ca descend » ; un ruban de douze metres aurait redessine la
        # coque.
        #
        # `s` croit vers la poupe et `z` decroit : le bout amont regarde vers -z.
        for v, face_z in ((s_lo, -1.0), (s_hi, 1.0)):
            _face_towards(bm, [
                bm.verts.new(Vector((edge(v, 0), _surface_y(v, PIT_X[0] * side), _z(v)))),
                bm.verts.new(Vector((edge(v, 1), _surface_y(v, PIT_X[1] * side), _z(v)))),
                bm.verts.new(Vector((edge(v, 1), floor, _z(v)))),
                bm.verts.new(Vector((edge(v, 0), floor, _z(v)))),
            ], "AA_Trim", Vector((0.0, 0.0, face_z)))
            quads += 1
    return quads


def _box_outward(bm: bmesh.types.BMesh, x0: float, x1: float, y0: float,
                 y1: float, s0: float, s1: float, material: str) -> int:
    """Un pave dont les six faces regardent DEHORS. Rend le nombre de quads.

    ⚠️ `_face_towards` ET NON `_face` : ce fichier n'appelle pas
    `recalc_face_normals` (voir `_assert_skin_outward`), et une face de module
    retournee DISPARAIT en jeu sans un mot. Les fosses ont paye cette lecon.
    """
    xa, xb = min(x0, x1), max(x0, x1)
    ya, yb = min(y0, y1), max(y0, y1)
    za, zb = _z(min(s0, s1)), _z(max(s0, s1))
    v = lambda x, y, z: bm.verts.new(Vector((x, y, z)))
    faces = (
        ([(xa, yb, za), (xb, yb, za), (xb, yb, zb), (xa, yb, zb)], (0, 1, 0)),
        ([(xa, ya, za), (xb, ya, za), (xb, ya, zb), (xa, ya, zb)], (0, -1, 0)),
        ([(xb, ya, za), (xb, yb, za), (xb, yb, zb), (xb, ya, zb)], (1, 0, 0)),
        ([(xa, ya, za), (xa, yb, za), (xa, yb, zb), (xa, ya, zb)], (-1, 0, 0)),
        ([(xa, ya, za), (xb, ya, za), (xb, yb, za), (xa, yb, za)], (0, 0, 1)),
        ([(xa, ya, zb), (xb, ya, zb), (xb, yb, zb), (xa, yb, zb)], (0, 0, -1)),
    )
    for pts, n in faces:
        _face_towards(bm, [v(*p) for p in pts], material, Vector(n))
    return len(faces)


def build_bastions(bm: bmesh.types.BMesh, index: int) -> int:
    """Les bastions : de grandes masses basses, sur le pont median.

    ⚠️ LEUR ASSISE SUIT LA PEAU, COIN PAR COIN. Le pont median descend de 5 cm sur
    sa largeur et la coque respire : une base posee a une hauteur unique
    flotterait d'un cote et s'enfoncerait de l'autre. On prend le point le plus
    BAS de l'emprise et on s'y enterre de 10 cm — le meme geste que la jupe des
    modules.
    """
    origin = index * SECTION_LENGTH
    quads = 0
    for sc, hs, xi, xo, height in BASTIONS:
        if not (origin <= sc < origin + SECTION_LENGTH):
            continue
        side = 1.0 if xi >= 0.0 else -1.0
        s0, s1 = sc - hs, sc + hs
        corners = [_surface_y(v, x) for v in (s0, sc, s1) for x in (xi, xo)]
        foot = min(corners) - 0.10
        k0 = _side_scale(s0, side)
        k1 = _side_scale(s1, side)
        # Les deux bouts suivent chacun la largeur locale : sur un bord qui se
        # pince, un bastion droit sortirait de la coque a une extremite.
        quads += _box_outward(bm, xi * k0, xo * k0, foot, foot + height,
                              s0, sc, "AA_Hull")
        quads += _box_outward(bm, xi * k1, xo * k1, foot, foot + height,
                              sc, s1, "AA_Hull")
    return quads


def build_cross_bridge(bm: bmesh.types.BMesh, index: int) -> int:
    """La passerelle transversale : une poutre et ses deux piles.

    ⚠️ CHAQUE EXTREMITE SUIT SON PROPRE BORD. La coque est asymetrique depuis le
    lot B2 : prendre `CROSS_BRIDGE_X` des deux cotes poserait une poutre qui
    depasse d'un bord et s'arrete avant l'autre.
    """
    origin = index * SECTION_LENGTH
    if not (origin <= CROSS_BRIDGE_S < origin + SECTION_LENGTH):
        return 0
    s0 = CROSS_BRIDGE_S - CROSS_BRIDGE_HS
    s1 = CROSS_BRIDGE_S + CROSS_BRIDGE_HS
    x_star = CROSS_BRIDGE_X * _side_scale(CROSS_BRIDGE_S, 1.0)
    x_port = -CROSS_BRIDGE_X * _side_scale(CROSS_BRIDGE_S, -1.0)
    quads = _box_outward(bm, x_port, x_star, CROSS_BRIDGE_BOTTOM,
                         CROSS_BRIDGE_TOP, s0, s1, "AA_Hull")
    # Les piles : sans elles la poutre flotte, et le regard le voit avant de
    # savoir pourquoi.
    for x_end, inward in ((x_star, -1.0), (x_port, 1.0)):
        foot = _surface_y(CROSS_BRIDGE_S, x_end) - 0.10
        quads += _box_outward(bm, x_end, x_end + inward * CROSS_BRIDGE_PIER,
                              foot, CROSS_BRIDGE_BOTTOM, s0, s1, "AA_Greeble")
    return quads


def build_bay_flanges(bm: bmesh.types.BMesh, index: int) -> int:
    """La collerette : le bord de l'ouverture se replie, il ne reste pas cru.

    ⚠️ POSEE APRES `_assert_skin_outward()`, ET C'EST OBLIGATOIRE. Ses faces
    regardent VERS le puits ; sur le flanc exterieur d'une baie, cela veut dire
    une normale dirigee vers l'axe du vaisseau. Le harnais d'orientation de la
    peau — qui a raison — la lirait comme une face retournee.

    Elle descend de 25 cm et s'ecarte de 12 cm : vers l'EXTERIEUR, parce que la
    face interne du coaming de `bay_kit.glb` est exactement au plan de
    l'ouverture. Un repli vers l'interieur la traverserait.

    Rend le nombre de quads poses.
    """
    origin = index * SECTION_LENGTH
    stations = _stations(index)
    quads = 0
    for sc, xc in BAYS:
        if not (origin <= sc < origin + SECTION_LENGTH):
            continue
        cells = [(i, k) for k in range(len(stations) - 1)
                 for i in range(RING_SIZE)
                 if _bay_cell(i, stations[k], stations[k + 1]) == (sc, xc)]
        if not cells:
            raise ak.ContractError(
                f"baie (s={sc}, x={xc}) : aucune cellule de peau dans son "
                "emprise — l'ouverture n'existe pas")
        i_lo = min(i for i, _ in cells)
        i_hi = max(i for i, _ in cells) + 1
        k_lo = min(k for _, k in cells)
        k_hi = max(k for _, k in cells) + 1
        # Le tour de l'ouverture, en (point d'anneau, station), sens unique.
        loop = [(i, k_lo) for i in range(i_lo, i_hi + 1)]
        loop += [(i_hi, k) for k in range(k_lo + 1, k_hi + 1)]
        loop += [(i, k_hi) for i in range(i_hi - 1, i_lo - 1, -1)]
        loop += [(i_lo, k) for k in range(k_hi - 1, k_lo, -1)]
        top: list = []
        bottom: list = []
        for i, k in loop:
            s = stations[k]
            px, py = _ring(s)[i]
            top.append(bm.verts.new(Vector((px, py, _z(s)))))
            ox = BAY_FLANGE_OUT if i == i_hi else (-BAY_FLANGE_OUT if i == i_lo
                                                   else 0.0)
            if RING_X[i_hi] < RING_X[i_lo]:          # anneau parcouru a l'envers
                ox = -ox
            os_ = BAY_FLANGE_OUT if k == k_hi else (-BAY_FLANGE_OUT if k == k_lo
                                                    else 0.0)
            bottom.append(bm.verts.new(Vector(
                (px + ox, py - BAY_FLANGE_DROP, _z(s + os_)))))
        centre = Vector((xc, 0.0, _z(sc)))
        for m in range(len(loop)):
            n = (m + 1) % len(loop)
            a, b = top[m], top[n]
            if (a.co - b.co).length < 1e-6:
                continue
            mid = (a.co + b.co) * 0.5
            want = Vector((centre.x - mid.x, 0.0, centre.z - mid.z))
            _quad_facing(bm, a, b, bottom[n], bottom[m], "AA_Greeble", want)
            quads += 1
    return quads


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
    # ⚠️ UNE LIMITE PAR BORD DEPUIS QUE LA COQUE EST ASYMETRIQUE. Une voie rabattue
    # sur la demi-largeur TRIBORD deborderait a babord la ou ce bord est pince —
    # une lisse en porte-a-faux au-dessus du vide, que rien ne signalerait.
    lo, hi = x0, x1
    limit_port = _half_width(s, -1.0) - 0.45
    limit_star = _half_width(s, 1.0) - 0.45
    if lo < -limit_port:
        lo = -limit_port
    if hi > limit_star:
        hi = limit_star
    if hi - lo < minimum:
        return None
    return lo, hi


#: Les emprises des pieces POSEES a la main sur le borde — celles qu'aucun
#: marqueur ne declare et qu'aucune table de marqueurs ne peut donc voir.
#: (nom, (x0, x1) absolus, (s0, s1)).
POSED_FOOTPRINTS: tuple[tuple[str, tuple[float, float], tuple[float, float]], ...] = (
    ("Ambry", AMBRY_KEEPOUT_X, AMBRY_KEEPOUT_S),
    ("Complexe", PLANT_KEEPOUT_X, PLANT_KEEPOUT_S),
)


def _posed_clash(s0: float, s1: float, x0: float, x1: float) -> bool:
    """Le module (s0..s1, x0..x1) mord-il une piece POSEE sur le borde ?

    Sans ce garde-fou, une greffe seedee du troncon 5 traverserait le radeau
    d'Ambry par en dessous : elle est POSEE sur le borde, elle n'est pas
    encastree dedans. Le complexe industriel du BRIEF-0111 est dans le meme cas.

    ⚠️ ELLE S'APPELAIT `_ambry_clash`, ET LE NOM ETAIT LE PIEGE. Neuf familles de
    modules l'appellent ; une seconde fonction recopiee a cote pour le complexe
    aurait ete oubliee par l'une des neuf, et un module qui traverse un volume
    pose ne produit aucune erreur — il se voit en capture, si l'on capture juste
    la. Une seule fonction, une seule table.
    """
    for _name, xs, ss in POSED_FOOTPRINTS:
        if not (s1 < ss[0] or s0 > ss[1] or x1 < xs[0] or x0 > xs[1]):
            return True
    return False


#: Voies de plaques : (x_min, x_max) en absolu, sur les deux bandes plates.
PLATE_LANES = ((2.35, 3.95), (4.05, 5.35), (5.45, 6.55),
               (7.55, 8.95), (9.05, 10.35), (10.45, 11.60))


def build_plates(bm: bmesh.types.BMesh, index: int, rng: random.Random,
                 aprons: list[tuple[float, float]],
                 busy: list[tuple[float, float]],
                 keepout: dict[str, int]) -> int:
    """Les plaques — desormais l'APPAREILLAGE des installations, plus un champ.

    ⚠️ CETTE FAMILLE A CHANGE DE METIER AU BRIEF-0094. Elle semait 1 071 plaques
    sur toute la longueur pour porter « le borde fait de modules qui se
    repetent » ; c'etait le travail de la texture, et `TEX-0010` le fait
    maintenant. Ce qui reste ici, c'est ce qu'une image plate ne peut pas faire :
    du RELIEF, et il n'a de sens qu'autour de quelque chose. Les plaques ne se
    posent donc plus que dans l'emprise d'une installation, ou elles l'ancrent.

    Deux hauteurs et non plus deux : 0,16 m pour les tôles, 0,34 m pour les
    massifs de machinerie qui entourent un socle ou un coaming — c'est la strate
    « Z + 0,5 autour des installations » que le brief demande. Aucune n'est
    violette : le violet est monte d'un cran, sur les greffes, ou il est porte
    par un VOLUME.
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
                if _posed_clash(s, s + length, min(x0, x1), max(x0, x1)):
                    s += cell
                    continue
                inset = rng.uniform(0.06, 0.20)
                # ⚠️ LE TEST DE BAIE VIENT APRES LE TIRAGE, ET C'EST DELIBERE.
                # `rng` est un flux : sauter un tirage decale TOUT ce qui suit,
                # et le decor entier se re-seede — 1084 plaques, 380 pastilles et
                # 117 greffes deplacees pour sept ouvertures. La regle vaut pour
                # les quatre familles qui tirent APRES un rejet (plaques,
                # nervures, greffes, pastilles) : on tire, puis on decide
                # d'emettre. Le filtre d'emprise obeit a la meme regle.
                if _bay_clash(s, s + length, min(x0, x1), max(x0, x1)) \
                        or _pit_clash(s, s + length, min(x0, x1), max(x0, x1)):
                    s += cell
                    continue
                if not _in_apron(s, s + length, aprons):
                    s += cell
                    continue
                if not _inside_zone(s, s + length):
                    s += cell
                    continue
                # Un tiers de massifs : c'est ce qui donne du volume au pied
                # d'une tourelle ou d'un hangar sans rien ajouter en couleur.
                heavy = roll > 0.74
                rise = 0.34 if heavy else 0.16
                # ⚠️ LA GARDE D'AFFUT, ET ELLE EST MESUREE PIECE PAR PIECE. Le
                # brief demandait d'arbitrer les tôles de 0,16 « sur mesure, pas
                # d'office » : c'est fait, et par la seule mesure qui compte —
                # `_turret_clash` compare le DESSUS de cette plaque-ci au plan
                # d'assise de l'affut. Une tôle posee sur une peau qui plonge de
                # 0,40 m sous l'assise reste dessous et vit ; un massif de 0,34
                # pose au point haut du disque passe au-dessus et s'ecarte. La
                # meme regle sert les deux hauteurs, sans en exempter aucune.
                seat = _plate_place(origin, side, a, b, s, length, inset,
                                    rise, aprons)
                if seat is None:
                    keepout["plaques_perdues"] = \
                        keepout.get("plaques_perdues", 0) + 1
                    s += cell
                    continue
                ps, x0, x1 = seat
                if abs(ps - s) > 1e-9:
                    keepout["plaques_ecartees"] = \
                        keepout.get("plaques_ecartees", 0) + 1
                _surface_box(bm, x0 + inset, x1 - inset, ps, ps + length,
                             rise, 0.55, "AA_Greeble",
                             "AA_Greeble" if heavy else "AA_Hull",
                             draft=0.055 if not heavy else 0.10)
                busy.append((ps, ps + length))
                count += 1
                s += cell
    return count


#: Les stations de repli d'une plaque, en metres depuis celle qui a ete tiree.
#: ⚠️ BORNEES A LA MOITIE DE LA MAILLE (`cell` = 3,2). Au-dela, la plaque
#: deplacee viendrait se poser sur celle de la cellule voisine : deux boites
#: imbriquees, une arete qui scintille, et un compte qui ment sur ce qu'on voit.
PLATE_NUDGES = (0.0, 0.5, -0.5, 1.0, -1.0, 1.5, -1.5)


def _plate_place(origin: float, side: float, a: float, b: float, s: float,
                 length: float, inset: float, rise: float,
                 aprons: list[tuple[float, float]]
                 ) -> tuple[float, float, float] | None:
    """Ou poser la plaque : (s retenu, x0, x1 de sa voie), ou None si nulle part.

    ⚠️ LA PREMIERE STATION ESSAYEE EST CELLE QUI A ETE TIREE, et les tests qu'elle
    subit ici sont EXACTEMENT ceux que l'appelant vient de passer, plus la garde
    d'affut. Une plaque qui ne genait personne rend donc le meme resultat qu'avant
    ce brief, au bit pres. Les stations de repli, elles, sont re-clippees sur la
    largeur locale : deplacer une plaque de 1,5 m sur le fuseau de proue la
    poserait a cote de la coque.
    """
    for ds in PLATE_NUDGES:
        ps = s + ds
        if ps < origin + 1.9 or ps + length > origin + SECTION_LENGTH - 1.9:
            continue
        lane = _clip_lane(ps, side * b, side * a) if side < 0 else \
            _clip_lane(ps, side * a, side * b)
        if lane is None:
            continue
        x0, x1 = lane
        lo, hi = min(x0, x1), max(x0, x1)
        if _posed_clash(ps, ps + length, lo, hi) \
                or _bay_clash(ps, ps + length, lo, hi) \
                or _pit_clash(ps, ps + length, lo, hi) \
                or not _in_apron(ps, ps + length, aprons) \
                or not _inside_zone(ps, ps + length):
            continue
        top = _box_top(x0 + inset, x1 - inset, ps, ps + length, rise)
        if _turret_clash(ps, ps + length, min(x0 + inset, x1 - inset),
                         max(x0 + inset, x1 - inset), top):
            continue
        # ⚠️ ET LA GARDE DE BRANCHE (BRIEF-0103), au meme endroit et pour la
        # meme raison : une tôle de 0,16 m posee a la station d'un affut
        # recouvrirait la veine de 0,15 qui l'alimente. La plaque se DEPLACE
        # (c'est la boucle des replis), elle n'est pas perdue.
        if _branch_clash(ps, ps + length, min(x0 + inset, x1 - inset),
                         max(x0 + inset, x1 - inset)):
            continue
        return ps, x0, x1
    return None


def build_ribs(bm: bmesh.types.BMesh, index: int, rng: random.Random,
               busy: list[tuple[float, float]],
               keepout: dict[str, int]) -> int:
    """Nervures transversales — desormais L'ANCRAGE d'une installation.

    Elles etaient reparties tous les 12 m sur toute la longueur : c'est ce qui
    faisait lire le Cortege « segmente » et, au brief suivant, « charge partout ».
    Le brief tranche : « quelques nervures et masses en Z + 0,5 AUTOUR des
    installations, pour les ancrer. Rien ailleurs. » Elles se posent donc a la
    station d'une installation, pas sur une grille — et leur nombre suit celui
    des installations du troncon, pas un compte ecrit a la main.

    ⚠️ 1,95 et non 1,75 comme bord interieur : la nervure s'arretait autrefois au
    pied de la crete ; le pied du REBORD du canal est a 1,70, et une nervure qui
    l'enjamberait ferait un pont par-dessus la tranchee — exactement ce que les
    travees du canal font deja, et mieux.
    """
    origin = index * SECTION_LENGTH
    bands = ((1.95, 6.60), (7.50, 12.10), (12.45, 13.85))
    count = 0
    stations = [(0.5 * (a + b), x) for a, b, _n, x in INSTALLATION_SPANS
                if origin + JOINT_CLEARANCE < 0.5 * (a + b)
                < origin + SECTION_LENGTH - JOINT_CLEARANCE]
    for k, (centre, cx) in enumerate(stations):
        # ⚠️ ELLES SONT LOCALES A LEUR INSTALLATION, EN X COMME EN S. Une nervure
        # qui traverserait les 28 m de large pour ancrer une tourelle de bord
        # serait exactement le « detail presque partout » que le brief corrige :
        # elle ancrerait aussi bien la peau nue d'en face. On ne retient donc que
        # les bandes que l'installation TOUCHE, et son seul bord — sauf le nœud
        # d'epine, sur l'axe, qui prend les deux.
        sides = (1.0, -1.0) if abs(cx) < 1.0 else (1.0 if cx > 0 else -1.0,)
        near = [(a, b) for a, b in bands if a - 3.2 <= abs(cx) <= b + 3.2] \
            or [bands[0]]
        # Deux nervures par installation, de part et d'autre : c'est ce qui la
        # fait lire POSEE SUR une structure et non collee dessus.
        for lead in (-1.0, 1.0):
            offset = rng.uniform(2.0, 3.2)
            s = centre + lead * offset
            width = rng.uniform(0.85, 1.45)
            rise = 0.45 if k % 2 == 0 else 0.32
            if not (origin + JOINT_CLEARANCE < s
                    < origin + SECTION_LENGTH - JOINT_CLEARANCE - width) \
                    or not _inside_zone(s, s + width):
                continue
            # ⚠️ L'IVOIRE A QUITTE LES NERVURES (BRIEF-0094). BRIEF-0089 l'avait
            # deja rationne — « une nervure sur trois seulement », les autres
            # lisaient comme des passages pietons — et c'etait encore trop : une
            # nervure fait 4,65 m de long sur la bande interieure, et quatre
            # barres ivoire de cette taille tombaient dans un seul cadre du
            # rendu d'acceptation. Elles alternent maintenant deux valeurs
            # SOMBRES : la variation se lit a la lumiere rasante, pas a la
            # valeur. L'ivoire ne subsiste plus que sur des pieces de moins de
            # 2 m2 (echines de greffe, sole du berceau d'epine).
            top = "AA_Greeble" if k % 3 == 1 else "AA_Hull"
            # ⚠️ LA GARDE D'AFFUT DEPLACE LA NERVURE ENTIERE, JAMAIS UNE SEULE
            # DE SES BANDES. Une nervure est une barre TRANSVERSALE : ecarter la
            # bande interieure en laissant celle de chine a sa station ferait
            # deux troncons de barre decales de 1,20 m — l'ancrage cesserait de
            # se lire comme une piece. On cherche donc UNE station qui degage
            # tous les disques, en s'eloignant de l'installation dans le sens ou
            # la nervure a ete tiree (`lead`), et l'on renonce si aucune ne tient.
            ps = None
            for step in RIB_NUDGES:
                cs = s + lead * step
                if not (origin + JOINT_CLEARANCE < cs
                        < origin + SECTION_LENGTH - JOINT_CLEARANCE - width) \
                        or not _inside_zone(cs, cs + width):
                    continue
                if not any(
                        _turret_clash(
                            cs, cs + width, lane[0], lane[1],
                            _box_top(lane[0], lane[1], cs, cs + width, rise))
                        or _branch_clash(cs, cs + width, lane[0], lane[1])
                        for a, b in near for side in sides
                        for lane in (_clip_lane(cs, min(side * a, side * b),
                                                max(side * a, side * b)),)
                        if lane is not None):
                    ps = cs
                    break
            if ps is None:
                keepout["nervures_perdues"] = \
                    keepout.get("nervures_perdues", 0) + 1
                continue
            if abs(ps - s) > 1e-9:
                keepout["nervures_ecartees"] = \
                    keepout.get("nervures_ecartees", 0) + 1
            s = ps
            posed = False
            for a, b in near:
                for side in sides:
                    lane = _clip_lane(s, min(side * a, side * b),
                                      max(side * a, side * b))
                    if lane is None \
                            or _posed_clash(s, s + width, lane[0], lane[1]) \
                            or _bay_clash(s, s + width, lane[0], lane[1]) \
                            or _pit_clash(s, s + width, lane[0], lane[1]):
                        continue
                    _surface_box(bm, lane[0], lane[1], s, s + width,
                                 rise, 0.60, "AA_Greeble", top, draft=0.10)
                    count += 1
                    posed = True
            if posed:
                busy.append((s, s + width))
    return count


#: L'eloignement d'une nervure, en metres, dans le sens ou elle a ete tiree.
#: ⚠️ ELLE NE SE RAPPROCHE JAMAIS de son installation : une nervure tiree a 2,0 m
#: du centre d'un affut est deja dans le disque de 2,50, et l'y enfoncer
#: davantage ne ferait que l'y enterrer mieux.
RIB_NUDGES = (0.0, 0.4, 0.8, 1.2, 1.6, 2.0)


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
        # ⚠️ La lisse interieure passe de |x| 1,66-2,02 a 2,42-2,78 : a l'ancienne
        # place elle chevauchait le talus du bandeau dorsal et le rebord du canal,
        # qu'elle aurait redessines en double. Elle longe maintenant le pied du
        # bandeau, ou elle en souligne l'arete.
        # ⚠️ LA LISSE DE CHINE PERD SON IVOIRE (BRIEF-0094), ET C'EST LA MEME
        # LEÇON QUE BRIEF-0089 A DEJA PAYEE UNE FOIS. Elle etait la DERNIERE
        # arete continue en `AA_Trim` : 0,36 m de large sur 97 m, deux fois. Au
        # rendu d'acceptation, en noir et blanc comme en couleur, elle donnait
        # deux traits blancs pleins du haut au bas du cadre — les « rubans
        # blancs » que le premier rendu du Cortege avait deja values, revenus
        # par la seule piece qu'on avait laissee claire. Le brief demande une
        # masse anthracite ou l'ivoire est RARE : il ne reste plus sur aucune
        # arete continue, seulement sur des pieces (chapeaux de nervure,
        # echines de greffe, sole de berceau).
        for a, b, rise, material in ((6.62, 6.98, 0.16, "AA_Greeble"),
                                     (12.15, 12.45, 0.14, "AA_Hull"),
                                     (2.42, 2.78, 0.12, "AA_Greeble")):
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
            # ⚠️ COUPEES, JAMAIS SUPPRIMEES (BRIEF-0091). La lisse de chine
            # (|x| 6,62-6,98) traverse les sept ouvertures : la rejeter en bloc
            # oterait au joueur la seule lecture CONTINUE de sa vitesse. Elle
            # est donc decoupee autour des baies, et reprend apres.
            for a0, a1 in _bay_free_spans(lane[0], lane[1], start, s1):
                _surface_box(bm, lane[0], lane[1], a0, a1, rise, 0.50,
                             "AA_Greeble", material, draft=0.03)
                count += 1
    return count


def build_grafts(bm: bmesh.types.BMesh, index: int, rng: random.Random,
                 busy: list[tuple[float, float]],
                 spans: list[tuple[float, float]],
                 keepout: dict[str, int]) -> int:
    """Les greffes : ce que le Cortege EMPORTE, empile sur son borde.

    ⚠️ TROIS CHOSES CHANGENT AU BRIEF-0094, ET C'EST LA MEME CORRECTION TROIS
    FOIS. « Les gros rectangles violets se lisent comme des decals arbitraires :
    ce sont des aplats, pas des volumes. Reduire le violet ET relever ces masses
    est la meme correction, pas deux. »

      1. LA HAUTEUR. Les couches montaient de 0,28 a 0,42 m et s'arretaient sous
         la crete, qui ne laissait que 0,4 m de degagement au centre. La crete a
         disparu : le pont offre 1,04 a 1,10 m sous le plafond de construction,
         et les couches montent maintenant de 0,34 a 0,54 m. Une greffe fait donc
         0,7 a 1,05 m de haut au lieu de 0,3 a 0,8.
      2. L'ORIENTATION. Toutes les empreintes etaient alignees sur les axes du
         vaisseau — donc indiscernables du borde autrement que par leur couleur.
         Elles sont maintenant tournees de 7 a 23 deg (`_surface_poly`), et le
         sens de rotation change d'une greffe a l'autre.
      3. LA COULEUR, EN DERNIER. `AA_Panel` ne couvre plus la premiere couche de
         chaque greffe mais une greffe sur quatre environ, sur sa couche haute —
         la ou elle designe un volume au lieu de tapisser une surface.

    Leur enveloppe grandit du troncon 1 au 5 : c'est ainsi que la silhouette
    s'epaissit vers la poupe sans jamais depasser les 28 m ni le plafond.
    """
    origin = index * SECTION_LENGTH
    count = 0
    growth = 0.80 + 0.10 * index
    # ⚠️ LES GREFFES SE SEMENT SUR LES EMPRISES, PLUS SUR UNE GRILLE. La version
    # d'avant les repartissait tous les 10 m sur toute la longueur : sous la
    # regle de contenance, quatre sur cinq tombaient dans une plage nue et
    # etaient rejetees — 27 greffes livrees au lieu de 100, un borde plat.
    # On parcourt donc les emprises, et chacune heberge deux ou trois masses.
    # C'est ce qui fait le groupe : « une tourelle, et la machinerie autour ».
    zones = [(max(a, origin + JOINT_CLEARANCE),
              min(b, origin + SECTION_LENGTH - JOINT_CLEARANCE))
             for a, b in MARKER_APRONS]
    zones = [(a, b) for a, b in zones if b - a > 4.0]
    for k, (za, zb) in enumerate(zones):
        for slot in range(2 + (k + index) % 2):
            side = 1.0 if (k + slot + index) % 2 == 0 else -1.0
            base_x = rng.uniform(3.2, 11.4)
            width = rng.uniform(2.4, 4.6) * growth
            length = min(rng.uniform(4.0, 9.5) * growth, zb - za - 0.4)
            s = za + rng.uniform(0.0, max(zb - za - length, 0.0))
            yaw = rng.uniform(0.12, 0.40) * (1.0 if rng.random() < 0.5 else -1.0)
            # ⚠️ UNE GREFFE SUR DEUX SEULEMENT EST VIOLETTE, ET LE CHOIX N'EST
            # PAS TIRE AU SORT : il alterne. Une couleur portee par TOUTES les
            # greffes redevient ce que le brief refuse — « une greffe doit se
            # distinguer par sa hauteur, son orientation et sa silhouette, PAS
            # par sa couleur ». Si le violet les designe toutes, c'est lui qui
            # les designe. Une sur deux, il ne designe plus rien : il accentue.
            count += _one_graft(bm, index, rng, busy, spans, keepout, s, length,
                                side, base_x, width, yaw, (k + slot) % 2 == 0)
    return count


def _graft_nudges() -> tuple[tuple[float, float], ...]:
    """L'echelle des places de repli d'une greffe, du plus proche au plus loin.

    ⚠️ ELLE COMMENCE PAR (0, 0), ET C'EST TOUT L'INTERET. La premiere place
    essayee est CELLE QUI A ETE TIREE : une greffe qui ne genait personne ne
    bouge pas d'un millimetre, et le troncon reste celui d'avant partout ou le
    defaut n'existait pas. On ne re-seede pas un vaisseau pour dix-sept disques.

    ⚠️ ET LE LATERAL PASSE AVANT LE LONGITUDINAL. Une greffe est HEBERGEE par
    l'emprise d'un marqueur (8,4 m pour une tourelle seule) et fait jusqu'a
    11,4 m de long : la reculer de 2,50 m la ferait sortir de son emprise, donc
    la perdrait. La largeur, elle, offre 28 m. C'est le seul axe ou une masse de
    9 m peut vraiment s'ecarter d'un affut sans quitter le groupe qu'elle forme
    avec lui — « une tourelle, et la machinerie autour ».
    """
    out = [(0.0, 0.0)]
    for reach in (0.9, 1.8, 2.7, 3.6, 4.5, 5.4):
        for dx in (reach, -reach):
            out.append((dx, 0.0))
        for ds in (reach, -reach):
            out.append((0.0, ds))
        for dx in (reach, -reach):
            for ds in (reach, -reach):
                out.append((dx, ds))
    return tuple(out)


GRAFT_NUDGES = _graft_nudges()

#: Bord interieur qu'une greffe DEPLACEE ne franchit pas : celui de la premiere
#: voie de plaques. Le canal et ses rebords vivent en deca (|x| <= 1,70) et une
#: masse de 1 m de haut posee dessus ferait un pont par-dessus l'artere. La place
#: TIREE, elle, n'est pas soumise a cette borne : on ne durcit pas en passant une
#: regle qui n'a rien a voir avec ce brief.
GRAFT_INNER_X = 2.35


def _graft_place(origin: float, s: float, length: float, side: float,
                 base_x: float, width: float,
                 yaw: float) -> tuple[float, tuple[float, float], bool, bool]:
    """Ou poser la greffe : (s retenu, voie, deplacee ?, barree ?).

    ⚠️ UNE GREFFE REJETEE EST UNE GREFFE PERDUE — ON LA DEPLACE. Vider l'emprise
    des marqueurs rendrait le borde plat, ce que BRIEF-0094 avait justement
    corrige en semant les greffes SUR les emprises. La garde d'affut n'est donc
    pas un rejet mais un ecart : on parcourt `GRAFT_NUDGES` et l'on prend la
    premiere place qui degage les dix-sept disques.

    « Barree » veut dire : la place tiree tombait sous un affut et aucune place
    de repli ne tenait. La greffe n'est alors pas emise — exactement comme une
    greffe qui tombe sur une baie —, mais elle CONSOMME ses tirages : c'est la
    regle de ce fichier (« on tire, puis on decide d'emettre »), et c'est elle
    qui empeche dix-sept disques de re-seeder les cinq troncons.
    """
    def seat(ps: float, px: float) -> tuple[tuple[float, float], tuple] | None:
        """La voie et la boite englobante de l'empreinte TOURNEE, ou None."""
        x0, x1 = px - width * 0.5, px + width * 0.5
        lane = _clip_lane(ps, min(side * x0, side * x1),
                          max(side * x0, side * x1))
        if lane is None or ps < origin + JOINT_CLEARANCE \
                or ps + length > origin + SECTION_LENGTH - JOINT_CLEARANCE \
                or _posed_clash(ps, ps + length, lane[0], lane[1]) \
                or not _inside_zone(ps, ps + length):
            return None
        # L'empreinte tournee deborde de la voie : on la majore par sa boite,
        # comme la boucle des couches le fait ensuite contre le bord du borde.
        return lane, _plan_bounds(_yawed_plan(
            (lane[0] + lane[1]) * 0.5, ps + length * 0.5,
            (lane[1] - lane[0]) * 0.5, length * 0.5, yaw))

    # ⚠️ LA PLACE TIREE EST JUGEE EXACTEMENT COMME AVANT CE BRIEF, plus la garde
    # d'affut — et si elle echoue pour une AUTRE raison (hors emprise, hors
    # coque), on ne cherche pas de repli. Une garde n'a pas le droit de repecher
    # ce que les regles d'avant refusaient : elle corrigerait un defaut qu'on ne
    # lui a pas demande de voir, et le compte de greffes mentirait sur sa cause.
    drawn = seat(s, base_x)
    if drawn is None:
        return s, (0.0, 0.0), False, False
    lane, (px0, px1, ps0, ps1) = drawn
    if not _turret_clash(ps0, ps1, px0, px1) \
            and not _branch_clash(ps0, ps1, px0, px1):
        return s, lane, False, False

    for dx, ds in GRAFT_NUDGES[1:]:
        ps, px = s + ds, base_x + dx
        # ⚠️ UNE PLACE DE REPLI EST JUGEE PLUS SEVEREMENT QUE LA PLACE TIREE, et
        # c'est delibere : deplacer une greffe pour la poser sur une ouverture de
        # hangar, au-dessus d'une fosse, par-dessus l'artere ou en porte-a-faux
        # au bord du borde serait remplacer un defaut par un autre.
        if px < GRAFT_INNER_X + width * 0.5:
            continue
        found = seat(ps, px)
        if found is None:
            continue
        lane_here, (qx0, qx1, qs0, qs1) = found
        centre_s = ps + length * 0.5
        if _turret_clash(qs0, qs1, qx0, qx1) \
                or _branch_clash(qs0, qs1, qx0, qx1) \
                or qx0 < -(_half_width(centre_s, -1.0) - 0.45) \
                or qx1 > _half_width(centre_s, 1.0) - 0.45 \
                or _bay_clash(qs0, qs1, qx0, qx1) \
                or _pit_clash(qs0, qs1, qx0, qx1):
            continue
        return ps, lane_here, True, False

    # Rien n'a tenu : on rend la place TIREE, marquee barree. Les tirages seront
    # consommes et rien ne sera emis — comme une greffe qui tombe sur une baie.
    return s, lane, False, True


def _one_graft(bm: bmesh.types.BMesh, index: int, rng: random.Random,
               busy: list[tuple[float, float]], spans: list[tuple[float, float]],
               keepout: dict[str, int], s: float, length: float, side: float,
               base_x: float, width: float, yaw: float, violet: bool) -> int:
    """Une greffe et sa pile de terrasses. Rend le nombre de boites emises."""
    origin = index * SECTION_LENGTH
    count = 0
    x0, x1 = base_x - width * 0.5, base_x + width * 0.5
    lane = _clip_lane(s, min(side * x0, side * x1), max(side * x0, side * x1))
    if lane is None or s + length > origin + SECTION_LENGTH - JOINT_CLEARANCE:
        return count
    if _posed_clash(s, s + length, lane[0], lane[1]):
        return count
    # ⚠️ LA GARDE D'AFFUT SE POSE ICI, avec les trois autres — et elle ECARTE au
    # lieu de rejeter (voir `_graft_place`).
    s, lane, moved, barred = _graft_place(origin, s, length, side,
                                          base_x, width, yaw)
    if moved:
        keepout["greffes_ecartees"] = keepout.get("greffes_ecartees", 0) + 1
    if barred:
        keepout["greffes_perdues"] = keepout.get("greffes_perdues", 0) + 1
    # Voir `build_plates` : on tire, puis on decide d'emettre.
    blocked = barred or _bay_clash(s, s + length, lane[0], lane[1]) \
        or _pit_clash(s, s + length, lane[0], lane[1])
    # ⚠️ LA REGLE DE RYTHME, ET C'EST ELLE QUI FAIT LE LIVRABLE « ZONES
    # CALMES ». Une greffe est HEBERGEE par une emprise de marqueur : elle
    # doit y tenir tout entiere. Elle n'a donc pas le droit de s'installer
    # dans une plage nue, et c'est une decision MESUREE, pas un gout — voir
    # `FREE_GAPS` et le compte-rendu : la plus large des vingt et une plages
    # laissees par les trente marqueurs fait 24 m, et une greffe de 8 m qui
    # s'y poserait ne laisserait que 8 m de tole de chaque cote, quand le
    # brief en demande 15 a 20. Deplacer des marqueurs pour ouvrir la place
    # est un arbitrage de conception, pas de forge.
    if not _inside_zone(s, s + length):
        return count
    x0, x1 = lane
    # ⚠️ La largeur EFFECTIVE, apres rabattement sur le fuseau. L'ancienne
    # version retranchait `width * shrink` d'une voie deja rabattue : sur le
    # troncon 1 les couches hautes debordaient de la couche basse.
    width = x1 - x0
    centre_x = (x0 + x1) * 0.5
    centre_s = s + length * 0.5
    wanted = rng.randint(2, 3)
    rise = 0.0
    layers = 0
    for layer in range(wanted):
        shrink = 0.20 * layer
        step = rng.uniform(0.34, 0.54)
        # ⚠️ On verifie AVANT de poser, jamais apres : une version precedente
        # posait la couche puis sortait de la boucle, et deux troncons
        # culminaient a -3,14 pour un plafond de construction de -3,20.
        headroom = BUILD_CEILING_Y - _surface_y(centre_s, centre_x)
        if rise + step > headroom:
            break
        plan = _yawed_plan(centre_x, centre_s,
                           width * (0.5 - shrink), length * (0.5 - shrink),
                           yaw)
        px0, px1, ps0, ps1 = _plan_bounds(plan)
        # ⚠️ L'empreinte TOURNEE deborde de la voie que `_clip_lane` a
        # validee — jusqu'a 0,8 m sur une greffe de 9 m tournee de 23 deg. On
        # la reverifie donc sur sa boite englobante, qui majore, contre la
        # meme demi-largeur utile que `_clip_lane`. Sans cela, une greffe de
        # bord passerait par-dessus l'arete du borde a la premiere rotation.
        if px0 < -(_half_width(centre_s, -1.0) - 0.45) \
                or px1 > _half_width(centre_s, 1.0) - 0.45:
            break
        if _posed_clash(ps0, ps1, px0, px1):
            break
        if not blocked:
            _surface_poly(
                bm, plan, rise + step, 0.70 + rise, "AA_Greeble",
                # ⚠️ LE VIOLET NE SURVIT QUE LA, ET SEULEMENT SUR LA
                # TERRASSE LA PLUS HAUTE — donc la plus PETITE. C'est la regle
                # de tout le niveau apres BRIEF-0094 : `AA_Panel` designe le
                # sommet d'une greffe et rien d'autre — plus une facette de
                # borde, plus une plaque, plus un socle.
                #
                # ⚠️ ET LE CHOIX DE LA COUCHE A ETE FAIT AU RENDU, PAS AU
                # RAISONNEMENT. Poser le violet sur toutes les couches sauf la
                # premiere donnait, vu de la camera du jeu (70 deg de plongee),
                # un parallelogramme violet plein sur chaque greffe : le
                # « gros rectangle violet pose » que le brief demande de
                # supprimer, simplement tourne. Sur la seule terrasse haute, il
                # ne couvre plus que ~10 pct de l'empreinte, et il se lit comme
                # ce qu'il est : un couronnement. Le brief : « la couleur ne
                # fait que confirmer » ce que la hauteur, l'orientation et la
                # silhouette ont deja dit.
                "AA_Panel" if (violet and layer == wanted - 1)
                    else "AA_Hull",
                draft=0.09)
        rise += step
        layers += 1
    if layers == 0:
        return count
    if not blocked:
        count += layers
        busy.append((s, s + length))
        spans.append((s - APRON_GRAFT, s + length + APRON_GRAFT))

    # L'echine : une lame etroite sur le dessus, qui casse le profil plat.
    if rng.random() < 0.55 and not blocked:
        spine = _yawed_plan(centre_x, centre_s, 0.30, length * 0.28, yaw)
        _surface_poly(bm, spine,
                      min(rise + 0.34,
                          BUILD_CEILING_Y - _surface_y(centre_s, centre_x)),
                      0.90 + rise, "AA_Greeble", "AA_Trim", draft=0.04)
        count += 1
    return count


def build_pips(bm: bmesh.types.BMesh, index: int, rng: random.Random,
               aprons: list[tuple[float, float]],
               busy: list[tuple[float, float]],
               keepout: dict[str, int]) -> int:
    """Les petits feux magenta des maquettes : 12 triangles piece.

    Ils sont ce qui, sur les trois planches, dit le plus vite « c'est vivant ».
    ⚠️ Ils sont volontairement PETITS (0,30 a 0,55 m) et poses a plat : leur aire
    emissive totale est mesuree et rapportee, parce que le magenta est aussi une
    couleur de tir ennemi (charte SS3) et qu'un decor ne doit jamais lui disputer
    la lisibilite.

    ⚠️ ILS NE SE SEMENT PLUS SUR TOUTE LA LONGUEUR (BRIEF-0094). 384 feux
    repartis uniformement, c'etait 384 raisons de regarder ailleurs que
    l'installation qui entre dans le cadre. Un feu allume DIT quelque chose : il
    dit qu'une machine tourne. Il se pose donc la ou il y en a une.
    """
    origin = index * SECTION_LENGTH
    count = 0
    for _ in range(44 + index * 4):
        s = origin + rng.uniform(JOINT_CLEARANCE + 1.0,
                                 SECTION_LENGTH - JOINT_CLEARANCE - 1.0)
        band = BAND_INNER if rng.random() < 0.5 else BAND_MID
        x = rng.uniform(*band) * (1.0 if rng.random() < 0.5 else -1.0)
        lane = _clip_lane(s, x - 0.28, x + 0.28, minimum=0.45)
        if lane is None or _posed_clash(s - 0.5, s + 0.5, lane[0], lane[1]):
            continue
        long_pip = rng.random() < 0.45
        half_x = 0.15 if long_pip else 0.26
        half_s = 0.44 if long_pip else 0.24
        # Voir `build_plates` : on tire, puis on decide d'emettre.
        if _bay_clash(s - 0.5, s + 0.5, lane[0], lane[1]) \
                or _pit_clash(s - 0.5, s + 0.5, lane[0], lane[1]):
            continue
        if not _in_apron(s - half_s, s + half_s, aprons) \
                or not _inside_zone(s - half_s, s + half_s):
            continue
        # ⚠️ UN FEU AUSSI PEUT PASSER SOUS UN AFFUT, ET IL NE SE DEPLACE PAS. Il
        # ne monte que de 0,05 m : sur une peau qui plonge sous l'assise, il
        # reste dessous et vit — c'est le cas de la plupart. Pose au point haut
        # du disque, il repasse au-dessus du plan sur lequel le kit est modelise,
        # et un feu magenta qui affleure la jupe d'un socle ne se lit plus comme
        # une machine qui tourne : il se lit comme un defaut d'assise. Il n'a pas
        # de station de repli parce qu'il n'a pas de groupe a tenir — 0,50 m de
        # long, tire au hasard dans le troncon, le suivant tombera ailleurs.
        if _turret_clash(s - half_s, s + half_s, x - half_x, x + half_x,
                         _box_top(x - half_x, x + half_x,
                                  s - half_s, s + half_s, 0.05)):
            keepout["pastilles_perdues"] = \
                keepout.get("pastilles_perdues", 0) + 1
            continue
        # ⚠️ ET IL NE SE POSE PAS SUR UNE BRANCHE (BRIEF-0103). Un feu magenta
        # a cheval sur une veine magenta ne se lit plus comme une machine qui
        # tourne : il se lit comme un renflement de la conduite. Il n'a pas de
        # station de repli, ici non plus — le suivant tombera ailleurs.
        if _branch_clash(s - half_s, s + half_s, x - half_x, x + half_x):
            keepout["pastilles_perdues"] = \
                keepout.get("pastilles_perdues", 0) + 1
            continue
        _surface_box(bm, x - half_x, x + half_x, s - half_s, s + half_s,
                     0.05, 0.35, "AA_Greeble", "AA_Emissive_Engine")
        busy.append((s - half_s, s + half_s))
        count += 1
    return count


# ==========================================================================
# L'ARTERE — conduits et travees (BRIEF-0094, priorite 1)
# ==========================================================================


def _spine_gap(s0: float, s1: float, margin: float) -> bool:
    """L'intervalle (s0, s1) tombe-t-il sur un nœud d'epine ?

    Le kit d'epine occupe le fond du canal a `SPINES` : un conduit qui passerait
    dessous serait cache, une travee le traverserait. Les conduits s'arretent
    donc AVANT le nœud et reprennent apres — ce qui donne, gratuitement, la
    lecture « le nœud est sur la conduite » plutot que « posee a cote ».
    """
    for centre in SPINES:
        if s0 < centre + margin and s1 > centre - margin:
            return True
    return False


def build_conduits(bm: bmesh.types.BMesh, index: int,
                   rng: random.Random) -> tuple[int, float]:
    """Les bandes lumineuses SERTIES DANS LE FOND du canal, avec leurs coupures.

    ⚠️ C'EST LA PRIORITE 1 DU BRIEF, ET ELLE TIENT DANS LA DIFFERENCE ENTRE UNE
    BANDE ET UNE CONDUITE. « Une bande continue sur 500 m est une frontiere de
    terrain, pas une conduite. » Quatre voies etroites, chacune avec sa propre
    cadence d'allumage et sa propre phase, dans un creux de 0,56 m : la lumiere
    ne peut plus faire une ligne pleine d'un bout a l'autre du cadre, et ce n'est
    pas un reglage d'emission — c'est de la geometrie.

    Rend (nombre de segments, longueur cumulee eclairee).
    """
    origin = index * SECTION_LENGTH
    end = origin + SECTION_LENGTH - JOINT_CLEARANCE
    count = 0
    lit = 0.0
    for side in (1.0, -1.0):
        for lane_index, (a, b) in enumerate(CONDUIT_LANES):
            x0, x1 = sorted((side * a, side * b))
            # La phase de depart differe par voie ET par bord : sans cela les
            # quatre coupures tombent au meme `s` et la conduite se lit comme
            # une seule barre pointillee.
            s = origin + JOINT_CLEARANCE + rng.uniform(0.0, 9.0) \
                + lane_index * 3.7 + (0.0 if side > 0 else 5.3)
            while s < end - 2.0:
                stop = min(s + rng.uniform(*CONDUIT_RUN), end)
                gap = rng.uniform(*CONDUIT_GAP)
                if stop - s >= 2.0 and not _spine_gap(s, stop, 2.0):
                    # ⚠️ Decoupe UNIQUEMENT dans le fuseau : voir
                    # `CONDUIT_TAPER_STEP`. Ailleurs le fond est plat et la
                    # bande sort d'une seule piece, a 12 triangles.
                    step = CONDUIT_TAPER_STEP if index == 0 else stop - s
                    piece = s
                    while piece < stop - 1e-6:
                        tail = min(piece + step, stop)
                        if _canal_lane(piece, x0, x1) is not None \
                                and _canal_lane(tail, x0, x1) is not None:
                            _surface_box(bm, x0, x1, piece, tail,
                                         CONDUIT_RISE, 0.30, "AA_Greeble",
                                         "AA_Emissive_Engine")
                            count += 1
                            lit += tail - piece
                        piece = tail
                s = stop + gap
    return count, lit


def build_canal_braces(bm: bmesh.types.BMesh, index: int,
                       rng: random.Random) -> int:
    """Les TRAVEES SOMBRES qui barrent le canal — la matiere des interruptions.

    Le brief demande de couper les bandes « par des travees sombres,
    regulierement mais sans metronome ». Un trou dans la lumiere y suffirait a
    moitie : il laisserait un canal vide, et un canal vide sur 4 m se lit comme
    une panne. Une poutre qui l'enjambe et l'obture donne la meme coupure ET une
    raison mecanique — c'est une conduite qui passe sous une structure.

    Elle est enterree de 0,62 m : elle REMPLIT la tranchee au lieu de la
    survoler, et l'on ne voit pas la lumiere passer dessous.
    """
    origin = index * SECTION_LENGTH
    end = origin + SECTION_LENGTH - JOINT_CLEARANCE
    count = 0
    s = origin + JOINT_CLEARANCE + rng.uniform(3.0, 12.0)
    while s < end - BRACE_WIDTH:
        # ⚠️ La travee va de REBORD A REBORD, pas de fond a fond : elle est donc
        # bornee par `CANAL_RIM_X` mis a l'echelle du fuseau, et non par
        # `_canal_lane()`, qui ne connait que le fond plat. Le seuil de 0,80
        # ecarte la proue, ou la tranchee n'existe pas encore.
        scale = _scales(s)[0]
        if scale >= 0.80 and not _spine_gap(s, s + BRACE_WIDTH, 2.6):
            half = CANAL_RIM_X * scale
            _surface_box(bm, -half, half, s, s + BRACE_WIDTH,
                         BRACE_RISE, BRACE_SINK, "AA_Greeble", "AA_Hull",
                         draft=0.06)
            count += 1
        s += rng.uniform(*BRACE_SPACING)
    return count


# ==========================================================================
# LES BRANCHES — le courant sort du canal et va jusqu'aux affuts (BRIEF-0103)
# ==========================================================================
# ⚠️ CE LOT NE LIVRE QUE DE LA GEOMETRIE, ET LA MECANIQUE EXISTE DEJA EN ENTIER.
# Abattre un nœud d'epine fait deja tomber les tourelles du troncon suivant a
# 45 pct de vitesse de rotation et 2,6 fois plus lentes a tirer, et `CortegeSkin`
# eteint deja la veine du troncon concerne. Ce qui manquait, c'est l'IMAGE : le
# canal brillait, les tourelles tiraient, et rien ne disait que les deux etaient
# branches.
#
# ⚠️ ELLES SONT LE PROLONGEMENT DES CONDUITS DU CANAL, PAS UNE FAMILLE ETRANGERE.
# Meme partage exactement que `build_conduits()` : une gaine sombre en
# `AA_Greeble` et, sertie dedans, une VEINE en `AA_Emissive_Engine` — et rien
# d'autre dans ce slot-la. C'est ce nom, et lui seul, que `CortegeSkin` reconnait
# pour donner a chaque troncon SA copie du materiau ; une veine peinte ailleurs
# resterait allumee sur un vaisseau mort, sans erreur ni test rouge. Le harnais
# `_audit()` compte donc les triangles emissifs DANS le couloir de chaque branche,
# sur le binaire, et echoue le build s'il en manque une.
#
# ⚠️ ET UNE BRANCHE SE JUGE A LA CAMERA DU JEU, PAS SUR UNE VUE DE DESSUS. Le
# cadre fait 41,60 m de large au plan du pont : a 1920 px, 46,2 px/m en lateral
# et 43,4 px/m en profondeur (le regard plonge de 70 deg, donc sin 70 = 0,940 de
# raccourci). La veine d'une branche court en LATERAL : sa largeur se lit dans la
# profondeur, a 43,4 px/m. D'ou les cotes ci-dessous, choisies contre l'ecran :
#
#     veine standard  0,22 m ->  9,5 px      gaine standard  0,52 m -> 22,6 px
#     veine lourde    0,40 m -> 17,4 px      gaine lourde    0,86 m -> 37,3 px
#
# Un trait d'un pixel n'existe pas ; 9,5 px est la plus fine chose du decor qui
# reste une LIGNE et non un pointille. Les trois emplacements lourds
# (`Turret_08`, `Turret_12`, `Turret_15` — la meme table que
# `cortege_hardpoints.gd`, recopiee ici parce que la forge ne lit pas le moteur)
# recoivent presque le double : c'est ce qui fait lire une hierarchie
# d'alimentation, et c'est le « au moins les grosses tours » de la demande.

#: Depart de la branche : l'ARETE INTERNE DU REBORD, pas son bord externe.
#: ⚠️ 1,12 et non 1,70 : a 1,70 la veine commencerait sur le bandeau dorsal, a
#: 58 cm de la tranchee, et l'on ne lirait pas qu'elle en SORT. A 1,12 elle
#: demarre sur la levre meme du canal, au contact de la lumiere du fond. C'est le
#: point 3 de `PROFILE_BASE`, et il est verifie par `_assert_canal()`.
BRANCH_ROOT_X = 1.12
#: Ou la branche S'ARRETE : au bord du disque de degagement de l'affut, plus
#: 10 cm de garde. ⚠️ C'est la garde de `BRIEF-0101` (`_turret_clash`), et ce
#: n'est pas une contrainte subie : le courant arrive A LA PLATEFORME, il ne
#: passe pas sous la tourelle. Une branche qui entrerait dans le disque
#: disparaitrait sous le socle du kit sans qu'aucune erreur ne le dise.
BRANCH_STOP = TURRET_KEEPOUT_R + 0.10
#: Largeurs, en metres. Voir le calcul en pixels ci-dessus.
BRANCH_TROUGH_W = 0.52
BRANCH_TROUGH_W_HEAVY = 0.86
BRANCH_VEIN_W = 0.22
BRANCH_VEIN_W_HEAVY = 0.40
#: La gaine affleure (9 cm), la veine est sertie dedans et depasse de 6 cm : ce
#: sont ces 6 cm de joue sombre qui empechent la veine de se lire comme un
#: autocollant pose a plat. Meme parti que le conduit du canal, qui est SERTI.
BRANCH_TROUGH_RISE = 0.09
BRANCH_VEIN_RISE = 0.15
BRANCH_TROUGH_SINK = 0.45
BRANCH_VEIN_SINK = 0.06
#: En deca, la branche n'est plus une conduite mais un bouton : on la declare
#: non desservie plutot que d'en poser un moignon.
BRANCH_MIN_LENGTH = 1.20
#: Les trois emplacements LOURDS. ⚠️ Recopie de `cortege_hardpoints.gd`
#: (`HEAVY_TURRETS`), et c'est assume : faire lire le moteur par la forge
#: creerait une dependance a l'envers (meme argument que `TURRET_KEEPOUT_R`).
#: Si la table du jeu change, celle-ci doit changer avec elle — la seule chose
#: qu'on y perdrait est la hierarchie visuelle, jamais une collision.
BRANCH_HEAVY = (8, 12, 15)


def _branch_routes() -> list[dict]:
    """Le trace des dix-sept branches, ou la raison pour laquelle il n'y en a pas.

    ⚠️ LES COTES SE LISENT SUR LE MARQUEUR, JAMAIS SUR LA TABLE `TURRETS`. Les
    deux different jusqu'a 2,30 m — `Turret_11` est ecrit a 10,10 et pose a
    12,40 — parce que `_marker_x()` rapporte le X de la table a la largeur LOCALE
    de la coque, qui respire (`TAPER`, `ASYMMETRY`). Une branche tiree sur la
    table arriverait a cote de son affut, et sur quatre emplacements elle
    finirait meme hors du palier de pont ou la tourelle est posee.

    Rend, par tourelle : le bord, les deux abscisses, la station, les largeurs,
    et — si elle n'a pas pu etre tiree — la raison, en clair, pour le rapport.
    """
    routes: list[dict] = []
    for number, (ts, tx) in enumerate(TURRETS, start=1):
        name = f"Turret_{number:02d}"
        mx = _marker_x(ts, tx)
        side = 1.0 if mx >= 0.0 else -1.0
        heavy = number in BRANCH_HEAVY
        trough = BRANCH_TROUGH_W_HEAVY if heavy else BRANCH_TROUGH_W
        vein = BRANCH_VEIN_W_HEAVY if heavy else BRANCH_VEIN_W
        # Le rebord suit la largeur locale comme tout le profil : la racine
        # est donc a 1,12 x l'echelle du bord, pas a 1,12 tout court.
        x_in = BRANCH_ROOT_X * _side_scale(ts, side)
        x_out = abs(mx) - BRANCH_STOP
        half_s = trough * 0.5
        route = {
            "name": name, "number": number, "station": ts, "side": side,
            "marker_x": mx, "table_x": tx, "heavy": heavy,
            "x_in": x_in, "x_out": x_out, "length": x_out - x_in,
            "trough": trough, "vein": vein,
            "s0": ts - half_s, "s1": ts + half_s,
            "reason": None,
        }
        lo, hi = min(side * x_in, side * x_out), max(side * x_in, side * x_out)
        # ⚠️ ON TESTE LES QUATRE GARDES DU FICHIER, PAS UNE SEULE. Un couloir de
        # 8 m traverse tout le pont : il croise potentiellement une ouverture de
        # hangar, une fosse, une tranchee de bastion, le radeau d'Ambry et le
        # disque d'un AUTRE affut. Un emplacement non desservi est un RESULTAT ;
        # une branche posee au travers d'une ouverture est un defaut muet.
        if route["length"] < BRANCH_MIN_LENGTH:
            route["reason"] = (
                f"l'affut est a {abs(mx):.2f} m de l'axe : entre le rebord du "
                f"canal ({x_in:.2f}) et le disque de degagement ({x_out:.2f}) il "
                f"ne reste que {route['length']:.2f} m, moins que les "
                f"{BRANCH_MIN_LENGTH:.2f} m qu'il faut pour lire une conduite")
        elif _bay_clash(route["s0"], route["s1"], lo, hi):
            route["reason"] = "le couloir traverse l'emprise d'un pont d'envol"
        elif _pit_clash(route["s0"], route["s1"], lo, hi):
            route["reason"] = "le couloir traverse une fosse ou une tranchee"
        elif _posed_clash(route["s0"], route["s1"], lo, hi):
            route["reason"] = "le couloir passe sous le radeau d'Ambry"
        elif _turret_clash(route["s0"], route["s1"], lo, hi):
            route["reason"] = "le couloir entre dans le disque d'un autre affut"
        routes.append(route)
    return routes


#: Calcule une fois : `_branch_clash()` est interroge des milliers de fois par
#: troncon par les familles seedees. Pur produit des constantes, donc deterministe.
_BRANCH_ROUTES: list[dict] = []


def branch_routes() -> list[dict]:
    if not _BRANCH_ROUTES:
        _BRANCH_ROUTES.extend(_branch_routes())
    return _BRANCH_ROUTES


#: Garde autour d'une branche : 12 cm de tole nue de chaque cote. Sans elle, une
#: plaque de 0,16 m posee au contact recouvrirait la joue de la veine.
BRANCH_KEEPOUT = 0.12


def _branch_clash(s0: float, s1: float, x0: float, x1: float) -> bool:
    """Le module (s0..s1, x0..x1) recouvre-t-il une branche ?

    ⚠️ LE CINQUIEME GARDE, ET IL EST DU MEME METIER QUE LES QUATRE AUTRES. Une
    plaque monte de 0,16 a 0,34 m, la veine de 0,15 : une tôle posee a la station
    d'un affut noierait la conduite qu'on vient de poser, et le defaut serait
    exactement aussi muet que celui de `BRIEF-0101` — aucune erreur d'import,
    aucun test rouge, une veine qui disparait sous une plaque.

    Il est interroge APRES le tirage, comme les quatre autres (« on tire, puis on
    decide d'emettre ») : le flux `rng` ne bouge pas d'un cran.
    """
    for route in branch_routes():
        if route["reason"] is not None:
            continue
        side = route["side"]
        lo = min(side * route["x_in"], side * route["x_out"]) - BRANCH_KEEPOUT
        hi = max(side * route["x_in"], side * route["x_out"]) + BRANCH_KEEPOUT
        if not (s1 < route["s0"] - BRANCH_KEEPOUT
                or s0 > route["s1"] + BRANCH_KEEPOUT
                or x1 < lo or x0 > hi):
            return True
    return False


def _drape_samples(s: float, side: float, x_in: float, x_out: float) -> list[float]:
    """Les abscisses ou le ruban doit porter un sommet, du canal vers le bord.

    ⚠️ UNE BOITE PLATE S'ENTERRERAIT, ET C'EST LA SEULE DIFFICULTE DE CE LOT.
    `_surface_box()` pose ses quatre coins au point le PLUS BAS de l'empreinte :
    c'est ce qu'il faut pour une plaque de 3 m sur une bande plate, et c'est faux
    pour un ruban de 8 m qui part du rebord du canal (-4,02), franchit le talus
    (-4,26), descend le pont interieur (-4,30) puis TOMBE de 60 cm dans la
    contremarche de chine (-4,94). D'un bout a l'autre la denivelee atteint
    0,92 m : la branche disparaitrait sous la coque sur les trois quarts de sa
    longueur, sans une erreur ni une ligne de journal.

    Le ruban est donc DRAPE : chaque sommet prend sa propre hauteur. Et comme
    `_surface_y()` est lineaire par morceaux en x, il suffit d'echantillonner aux
    points de rupture du profil — la peau est alors suivie EXACTEMENT, sans un
    triangle de plus qu'il n'en faut.
    """
    k = _side_scale(s, side)
    xs = [x_in]
    for px, _py, _m in PROFILE[: DECK_LAST + 1]:
        sx = px * k
        if x_in + 1e-4 < sx < x_out - 1e-4:
            xs.append(sx)
    xs.append(x_out)
    return xs


def _drape_ribbon(bm: bmesh.types.BMesh, xs: list[float], side: float,
                  s0: float, s1: float, rise: float, sink: float,
                  side_material: str, top_material: str) -> float:
    """Un ruban pose SUR la peau, sommet par sommet. Rend le Y le plus haut.

    ⚠️ AUCUNE FACE INTERIEURE, et ce n'est pas de l'economie : une suite de
    boites accolees poserait a chaque couture deux faces coplanaires en sens
    contraire. Le ruban est un SEUL solide — dessus, dessous, deux joues, deux
    bouchons — et son bobinage est DECLARE (`_face_towards`) plutot qu'ecrit :
    l'ordre des sommets s'inverse quand le ruban passe a babord, et une face
    retournee ne produit aucune erreur, elle DISPARAIT (voir `_face_towards`).
    """
    signed = [side * x for x in xs]
    top0 = [bm.verts.new(Vector((x, _surface_y(s0, x) + rise, _z(s0))))
            for x in signed]
    top1 = [bm.verts.new(Vector((x, _surface_y(s1, x) + rise, _z(s1))))
            for x in signed]
    bot0 = [bm.verts.new(Vector((x, _surface_y(s0, x) - sink, _z(s0))))
            for x in signed]
    bot1 = [bm.verts.new(Vector((x, _surface_y(s1, x) - sink, _z(s1))))
            for x in signed]
    up = Vector((0.0, 1.0, 0.0))
    down = Vector((0.0, -1.0, 0.0))
    fore = Vector((0.0, 0.0, 1.0))
    aft = Vector((0.0, 0.0, -1.0))
    for i in range(len(signed) - 1):
        _face_towards(bm, [top0[i], top0[i + 1], top1[i + 1], top1[i]],
                      top_material, up)
        _face_towards(bm, [bot0[i], bot0[i + 1], bot1[i + 1], bot1[i]],
                      side_material, down)
        _face_towards(bm, [bot0[i], bot0[i + 1], top0[i + 1], top0[i]],
                      side_material, fore)
        _face_towards(bm, [bot1[i], bot1[i + 1], top1[i + 1], top1[i]],
                      side_material, aft)
    inward = Vector((-side, 0.0, 0.0))
    outward = Vector((side, 0.0, 0.0))
    _face_towards(bm, [bot0[0], top0[0], top1[0], bot1[0]],
                  side_material, inward)
    _face_towards(bm, [bot0[-1], top0[-1], top1[-1], bot1[-1]],
                  side_material, outward)
    return max(v.co.y for v in top0 + top1)


def build_branches(bm: bmesh.types.BMesh, index: int) -> tuple[int, float, float]:
    """Une branche par affut : la gaine sombre, puis la VEINE emissive dedans.

    Rend (nombre de branches, longueur cumulee, aire de veine).

    ⚠️ AUCUN TIRAGE. Une branche relie deux points de gameplay poses a la main ;
    elle n'a rien a decider. Elle ne touche donc pas au flux `rng` du troncon, et
    les cinq familles semees restent au bit pres celles d'avant ce lot — a ceci
    pres qu'elles ecartent desormais les couloirs (`_branch_clash`).
    """
    origin = index * SECTION_LENGTH
    count = 0
    length = 0.0
    area = 0.0
    for route in branch_routes():
        ts = route["station"]
        if not (origin <= ts < origin + SECTION_LENGTH):
            continue
        if route["reason"] is not None:
            continue
        side = route["side"]
        xs = _drape_samples(ts, side, route["x_in"], route["x_out"])
        half = route["trough"] * 0.5
        _drape_ribbon(bm, xs, side, ts - half, ts + half,
                      BRANCH_TROUGH_RISE, BRANCH_TROUGH_SINK,
                      "AA_Greeble", "AA_Greeble")
        half = route["vein"] * 0.5
        _drape_ribbon(bm, xs, side, ts - half, ts + half,
                      BRANCH_VEIN_RISE, BRANCH_VEIN_SINK,
                      "AA_Greeble", "AA_Emissive_Engine")
        count += 1
        length += route["length"]
        area += route["length"] * route["vein"]
    return count, length, area


# ⚠️ `build_turret_pad()` A DISPARU (BRIEF-0093), ET AVEC ELLE 17 x 260
# TRIANGLES DE SOCLE CUIT — la coque passe de 40 446 a 36 026 triangles. C'est exactement le mouvement de BRIEF-0091 sur les hangars,
# refait pour les tourelles, et pour la meme raison chiffree : elle posait des
# anneaux concentriques a cœur magenta, que l'operateur a lus comme « des jetons
# circulaires — pas de canon, pas de mecanisme, pas de connexion physique ».
#
# La tourelle est desormais faite de deux choses qui ne vivent plus dans le meme
# fichier :
#
#   * le MARQUEUR, ici : `Turret_NN` ne bouge ni en X ni en Z, et son Y devient
#     le PLAN D'ASSISE du socle (`turret_seat_y()`), comme le Y de `Bay_NN` est
#     devenu celui de la bouche ;
#   * l'AFFUT, dans `turret_kit.glb` : socle, jupe, couronne, bloc blinde, deux
#     canons, coffrets et conduites. Le moteur monte les huit pieces sur le
#     marqueur, et il en varie l'assemblage.
#
# Le partage n'est pas un gout : dix-sept tourelles cuites a l'identique se
# lisaient comme dix-sept fois la meme, et un seul kit en fait trois familles.


#: ⚠️ RAYON DE L'EMPRISE QUE `turret_kit.glb` POSE SUR LA PEAU (jupe d'ancrage
#: comprise). Il vit ICI parce que c'est ici qu'on echantillonne la peau pour
#: calculer l'assise du marqueur, et `build_turret_kit.FOOTPRINT_R` doit valoir
#: la meme chose : le kit — qui importe ce module — le reverifie a chaque build,
#: exactement comme `BAY_COAMING_W`. Deux valeurs qui derivent en silence, c'est
#: un socle qui flotte d'un cote et s'enterre de l'autre.
TURRET_FOOTPRINT_R = 2.08


def turret_seat_y(s: float, x: float) -> tuple[float, float]:
    """(Y d'ASSISE du socle de tourelle, Y du point le plus bas de son emprise).

    ⚠️ L'assise est le point le PLUS HAUT de l'emprise, pas la peau au marqueur.
    Meme raison exactement que pour `bay_mouth_y()` : l'emprise de 4,16 m de
    diametre enjambe la chine, et le pourtour accuse jusqu'a 0,683 m de denivele
    (mesure sur les dix-sept emplacements ; le minimum est 0,121 m).
    Prendre la peau au centre enfoncerait le socle dans la coque d'un cote et le
    ferait flotter de l'autre — le defaut que BRIEF-0091 a corrige sur le coaming.

    Le marqueur `Turret_NN` porte donc ce maximum : c'est le plan Y = 0 sur lequel
    TOUTES les pieces de `turret_kit.glb` sont modelisees. Le second membre du
    couple donne le creux a rattraper, que la jupe enterree du kit doit absorber.
    """
    ys = [_surface_y(s, x)]
    for radius, steps in ((TURRET_FOOTPRINT_R * 0.5, 8),
                          (TURRET_FOOTPRINT_R * 0.82, 16),
                          (TURRET_FOOTPRINT_R, 16)):
        for k in range(steps):
            a = 2.0 * math.pi * k / steps
            ys.append(_surface_y(s + radius * math.sin(a),
                                 x + radius * math.cos(a)))
    return max(ys), min(ys)


# ⚠️ `build_bay()` A DISPARU (BRIEF-0091), ET AVEC ELLE 7 x ~230 TRIANGLES.
# Elle posait un coaming hexagonal SUR le borde — la « baie » etait un bouton,
# pas un trou. Le pont d'envol est maintenant fait de deux choses qui ne vivent
# plus dans le meme fichier :
#
#   * l'OUVERTURE, ici : `build_skin()` n'emet pas les faces de l'emprise et
#     `build_bay_flanges()` replie le bord (voir le bloc des ouvertures) ;
#   * le HANGAR, dans `bay_kit.glb` : coaming, parois, fond, rails. Le moteur
#     l'instancie sur le marqueur `Bay_NN`, qui porte desormais le Y de la
#     BOUCHE et non celui d'une levre posee.
#
# Ce partage n'est pas un gout : sept hangars differents se composent a partir
# d'un seul kit (rotation, largeur, presence des blocs), et la coque n'a pas a
# porter sept copies de la meme geometrie.


# ⚠️ `build_spine_bulb()` A DISPARU (BRIEF-0094), ET C'EST LE TROISIEME MOUVEMENT
# IDENTIQUE DE CE FICHIER — apres les hangars (BRIEF-0091) et les socles de
# tourelle (BRIEF-0093). Elle posait un bulbe de revolution a cœur emissif, cale
# sur le plafond de construction, sur la crete dorsale ; elle coutait ~250
# triangles par nœud et, surtout, elle etait CUITE DANS LE TRONCON.
#
# Or le nœud est DESTRUCTIBLE, et c'est ce qui tranche : cinq bulbes cuits dans
# cinq maillages qui partagent un jeu de materiaux ne s'eteignent pas un par un.
# `CortegeSpineNode` devait donc superposer son propre volume au bulbe livre pour
# porter l'etat de la piece — deux geometries pour un seul objet.
#
# Le nœud est maintenant fait de deux choses qui ne vivent plus dans le meme
# fichier :
#
#   * le MARQUEUR, ici : `Spine_NN` ne bouge ni en X ni en Z, et son Y devient le
#     PLAN D'ASSISE DANS LE FOND DU CANAL (`spine_seat_y()`), comme le Y de
#     `Bay_NN` est devenu la bouche et celui de `Turret_NN` l'assise du socle ;
#   * le NŒUD, dans `spine_kit.glb` : `spine_cradle` (le berceau), `spine_core`
#     (le cœur — la seule piece qui meurt, donc la seule qui porte un emissif) et
#     `spine_brace` (l'entretoise, posee deux ou quatre fois en miroir). Le moteur
#     detruit `spine_core` SEUL : le berceau et les entretoises restent, et un
#     nœud abattu laisse une carcasse.
#
# ⚠️ ET LE NŒUD A CHANGE DE PLACE EN MEME TEMPS QUE DE NATURE. Il siegeait au
# SOMMET de la crete dorsale ; la crete n'existe plus, le canal l'a remplacee. Il
# siege maintenant AU FOND de la tranchee, sur la conduite qu'il alimente — ce qui
# le rend, comme le brief le voulait, plus dur a atteindre qu'a tuer.


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
       l'anthracite `#24252B` de l'Unisson partout ailleurs — contraste 12,7:1
       (WCAG), contre 11,1:1 auparavant. AVANT, ces memes faces etaient en
       `AA_Trim` (l'ivoire froid `#DDDCD2` de l'Unisson) : la valeur y etait
       deja, mais la MATIERE etait celle de l'ennemi, et une carte propre a
       Ambry etait impossible.
       ⚠️ Le gain n'est qu'a un quart une affaire de COULEUR (+16 pct de
       luminance de base) : le reste vient du FINI. `AA_Trim` est metallic 0,85
       — une carapace polie, qui rend peu en diffus ; `AA_Hull_Ambry` herite du
       0,05 des coques Vanguard, une tole PEINTE. Mesure sur la vignette
       d'elevation, meme eclairage, avant/apres : 0,547 -> 0,720 de luminance
       a l'ecran.
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
# LE COMPLEXE INDUSTRIEL DU TRONCON 5 (BRIEF-0111)
# ==========================================================================
# Ce n'est pas un tapis de greebles : c'est un LIEU, et un lieu se lit par trois
# choses que la caméra du jeu voit a 45,8 px/m et 70 deg de plongee —
#
#   une EMPRISE      un longeron de rive et deux traverses de bout, fermes : le
#                    complexe a un bord, donc un dedans et un dehors ;
#   des SEUILS       deux portiques, un a chaque bout, sous lesquels la ligne de
#                    conduite passe. On ENTRE et on SORT ;
#   un CŒUR          un bassin de 1,55 m creuse dans le pont median, enjambe par
#                    trois passerelles. C'est le seul endroit ou l'on voit
#                    DEDANS quelque chose.
#
# ⚠️ LA HAUTEUR NE PEUT PAS PORTER CE LOT, ET C'EST MESURE. Le pont median est a
# -4,99 et le plafond de construction a -3,20 : 1,79 m. Le `stern_pylon.glb` en
# demande 5,30 — il ne rentre pas, et ce n'est pas une affaire de cout, c'est le
# plafond de vol. De surcroit, a la perspective du jeu, une hauteur ne rend que
# 34 pct de sa longueur a l'ecran quand un plan horizontal en rend 94 (mesure au
# BRIEF-0110). Tout le travail va donc au PLAN et aux ARETES, et la profondeur —
# libre, il y a 8 m jusqu'a la quille — porte le seul vrai volume du lot.
#
# ⚠️ ET LE COMPLEXE EPOUSE LA TAILLE DE LA COQUE. `ASYMMETRY` pince le bord
# tribord de 15 pct a s = 434, en plein milieu de l'emprise : 1,5 m qui rentrent
# et ressortent sur 16 m. Tout le mobilier est donc ecrit en x NOMINAL et
# multiplie par `_side_scale`, comme la peau elle-meme — il se resserre avec elle
# au lieu de sortir dans le vide. La seule exception est la VOIE DE CONDUITE,
# droite parce que les pieces qu'elle porte sont rigides.


def _pl(s: float, xn: float) -> float:
    """x NOMINAL -> x absolu, a la largeur locale du bord tribord."""
    return xn * _side_scale(s, 1.0)


def _plant_stations(s0: float, s1: float, step: float = 1.25) -> list[float]:
    """Les stations d'une piece longue du complexe, bornes comprises.

    ⚠️ 1,25 m, LE MEME PAS QUE `_stations()` DANS UNE TRANSITION D'ASYMETRIE. Un
    longeron de 24,5 m decoupe en deux tronces suivrait la corde du pincement et
    non le pincement : il flotterait de 60 cm au-dessus du pont a mi-transition,
    ou s'y enterrerait. La peau tourne en 1,25 m ; ce qui est pose dessus aussi.
    """
    values = [s0]
    v = s0 + step
    while v < s1 - 1e-6:
        values.append(v)
        v += step
    values.append(s1)
    return values


def _plant_strip(bm: bmesh.types.BMesh, xn0: float, xn1: float,
                 s0: float, s1: float, rise: float, sink: float,
                 side_material: str, top_material: str) -> float:
    """Une bande LONGUE du complexe, qui suit la largeur locale du bord.

    C'est `_surface_box` pour une piece qui traverse un pincement : le plan n'est
    plus un quadrilatere mais un ruban de `2 x n` sommets, chacun a son x
    nominal rapporte a la station ou il se trouve. Le dessus reste PLAN — a x
    nominal constant, la peau garde exactement la meme hauteur d'un bout a
    l'autre du vaisseau (`ky` vaut 1 au-dela du fuseau de proue), si bien qu'un
    plan horizontal EST la bonne reponse et non une approximation.

    Rend le Y du dessus.
    """
    stations = _plant_stations(s0, s1)
    plan = [(_pl(s, xn1), s) for s in stations]
    plan += [(_pl(s, xn0), s) for s in reversed(stations)]
    return _surface_poly(bm, plan, rise, sink, side_material, top_material)


def _plant_prism(bm: bmesh.types.BMesh, cx: float, cs: float,
                 r_bottom: float, r_top: float, y0: float, y1: float,
                 sides: int, side_material: str, top_material: str) -> None:
    """Un volume de REVOLUTION approche — cuve, silo, cheminee.

    ⚠️ C'EST LA SEULE FORME DU COMPLEXE QUI NE SOIT PAS ORTHOGONALE, ET C'EST
    TOUT SON ROLE. Le borde de l'Unisson est fait de boites alignees sur deux
    axes sur 500 m ; a 45,8 px/m, une silhouette RONDE vue de dessus est le seul
    signal qui ne se confond avec rien d'autre du niveau. Six a huit cotes
    suffisent : au-dela, le contour ne gagne plus un pixel.

    Le bobinage est CALCULE (`_face_towards`, `_quad_facing`) et jamais ecrit a
    la main : ce fichier n'appelle pas `recalc_face_normals`, et une face
    retournee ne produit aucune erreur — elle disparait.
    """
    angles = [2.0 * math.pi * k / sides for k in range(sides)]
    bottom = [bm.verts.new(Vector((cx + r_bottom * math.cos(a), y0,
                                   _z(cs + r_bottom * math.sin(a)))))
              for a in angles]
    top = [bm.verts.new(Vector((cx + r_top * math.cos(a), y1,
                                _z(cs + r_top * math.sin(a)))))
           for a in angles]
    _face_towards(bm, top, top_material, Vector((0.0, 1.0, 0.0)))
    _face_towards(bm, list(bottom), side_material, Vector((0.0, -1.0, 0.0)))
    for i in range(sides):
        j = (i + 1) % sides
        a = 0.5 * (angles[i] + angles[j])
        _quad_facing(bm, bottom[i], bottom[j], top[j], top[i], side_material,
                     Vector((math.cos(a), 0.0, -math.sin(a))))


def _plant_gate(bm: bmesh.types.BMesh, s_centre: float, xn_in: float,
                xn_out: float, top: float) -> None:
    """UN SEUIL — deux pieds, un linteau, deux feux.

    ⚠️ C'EST LA PIECE QUI FAIT « ON ENTRE QUELQUE PART », et elle ne coute que
    trois boites. Le lot precedent l'a mesure a l'envers : un pylone de 5,30 m ne
    rentre pas sous un plafond de 1,79. Un portique de 1,50 m rentre, et il dit
    la meme chose — parce que ce qui se lit n'est pas sa hauteur, c'est le fait
    qu'il ENJAMBE quelque chose.

    ⚠️ IL ENJAMBE LE PLANCHER, PAS L'ALLEE, ET C'EST UNE CONTRAINTE MESUREE. Le
    linteau se tient a -3,90 ; une conduite COUDEE assise sur son berceau culmine
    a -3,76, donc 14 cm PLUS HAUT. Un portique a cheval sur la voie serait
    traverse par la piece que le concepteur a le droit d'y monter, et rien ne le
    dirait — ni erreur d'import, ni test rouge. Les deux seuils tiennent donc au
    large de la voie, et deux bornes leur repondent de l'autre cote de l'allee.
    """
    s0, s1 = s_centre - 0.45, s_centre + 0.45
    x_in0, x_in1 = _pl(s_centre, xn_in), _pl(s_centre, xn_in + 0.85)
    x_out0, x_out1 = _pl(s_centre, xn_out - 0.85), _pl(s_centre, xn_out)
    for a, b in ((x_in0, x_in1), (x_out0, x_out1)):
        foot = min(_surface_y(s_centre, a), _surface_y(s_centre, b)) - 0.45
        _box_outward(bm, a, b, foot, top - 0.40, s0, s1, "AA_Greeble")
    _box_outward(bm, x_in0, x_out1, top - 0.40, top, s0 + 0.06, s1 - 0.06,
                 "AA_Hull")
    # Les deux feux du seuil. ⚠️ `AA_Emissive_Engine` SEULEMENT ICI ET SUR LES
    # TROIS BARRES DU BASSIN : c'est le slot que `CortegeSkin.extinguish()`
    # eteint au blackout de la fin. Une veine peinte sur une piece qui n'a pas de
    # raison de s'eteindre resterait allumee sur un vaisseau mort.
    for base in (x_in1 + 0.30, x_out0 - 0.56):
        _box_outward(bm, base, base + 0.26, top, top + 0.03,
                     s_centre - 0.26, s_centre + 0.26, "AA_Emissive_Engine")


def build_plant(bm: bmesh.types.BMesh, index: int
                ) -> tuple[list[tuple[str, Vector]], dict]:
    """Le complexe et ses cinq reperes de conduite. Rend `(ancres, mesures)`."""
    stats: dict = {}
    anchors: list[tuple[str, Vector]] = []
    seats: list[tuple[int, float]] = []
    origin = index * SECTION_LENGTH
    if not (origin <= PLANT_S[0] < origin + SECTION_LENGTH):
        return anchors, stats
    s0, s1 = PLANT_S
    fx0, fx1 = PLANT_FLOOR_XN
    basin_s0 = BASINS[0][0] - BASINS[0][1]
    basin_s1 = BASINS[0][0] + BASINS[0][1]
    tops: list[float] = []
    counts: dict[str, int] = {}

    # ======================================================================
    # 1. LE PLANCHER — l'emprise au sol, et c'est elle qui fait le LIEU
    # ======================================================================
    # ⚠️ C'EST LE PREMIER LIVRABLE, PAS UN CADRE DECORATIF. « Le critere n'est pas
    # qu'il y ait de la matiere, c'est qu'on voie une installation. » Ce qui
    # separe les deux, sur 24,5 m de tole nue, est un SOL DIFFERENT du pont : une
    # marche de 0,35 m qui court sur 24,5 m donne au complexe un dedans et un
    # dehors avant qu'aucun volume n'y soit pose. Et c'est ce qui paie le mieux
    # a cette camera : une hauteur ne rend que 34 pct de sa longueur a l'ecran,
    # un plan horizontal 94 (mesure au BRIEF-0110).
    #
    # Trois segments et non un : le bassin coupe le plancher au milieu, et son
    # bord interieur EST le point 10 du profil (10,30) — donc le bord du bassin.
    for a, b, inner in ((s0, basin_s0, fx0),
                        (basin_s0, basin_s1, BASIN_X[1]),
                        (basin_s1, s1, fx0)):
        tops.append(_plant_strip(bm, inner, fx1, a, b, 0.35, 1.00,
                                 "AA_Greeble", "AA_Hull"))
    floor = tops[0]

    # --- Le longeron de rive, et le longeron de chine ------------------------
    tops.append(_plant_strip(bm, PLANT_RAIL_XN[0], PLANT_RAIL_XN[1], s0, s1,
                             0.62, 1.20, "AA_Greeble", "AA_Hull"))
    rail = tops[-1]
    tops.append(_plant_strip(bm, PLANT_KERB_XN[0], PLANT_KERB_XN[1], s0, s1,
                             0.30, 1.00, "AA_Greeble", "AA_Hull"))

    # --- Les deux traverses de bout, EN DEUX PIECES chacune ------------------
    # La voie de conduite passe entre elles : une traverse d'un seul tenant
    # serait traversee par la piece du bout de ligne, a 0,3 m pres.
    for a, b in ((s0, s0 + 0.80), (s1 - 0.80, s1)):
        tops.append(_plant_strip(bm, PLANT_KERB_XN[0], 7.60, a, b,
                                 0.55, 1.00, "AA_Greeble", "AA_Hull"))
        tops.append(_plant_strip(bm, 9.80, PLANT_RAIL_XN[1], a, b,
                                 0.62, 1.05, "AA_Greeble", "AA_Hull"))

    # ======================================================================
    # 2. LE RYTHME — plots de rive et traverses de plancher
    # ======================================================================
    # A 45,8 px/m, un plot de 0,60 x 0,70 m rend 27 x 32 px EN PLAN ; ses 0,55 m
    # de haut n'en rendent que 9. C'est sa surface HORIZONTALE qui le fait
    # exister. Douze plots reguliers donnent au bord une CADENCE, et une cadence
    # est ce qui distingue une installation d'un tas.
    plots = ribs = 0
    ps = s0 + 1.7
    while ps <= s1 - 1.7 + 1e-6:
        base = _surface_y(ps, _pl(ps, PLANT_RAIL_XN[1]))
        _plant_strip(bm, PLANT_RAIL_XN[0] - 0.08, PLANT_RAIL_XN[1] + 0.05,
                     ps - 0.35, ps + 0.35, rail + 0.52 - base, 0.70,
                     "AA_Greeble", "AA_Hull")
        plots += 1
        ps += 2.0
    for a, b in ((s0 + 1.2, basin_s0 - 0.9), (basin_s1 + 0.9, s1 - 1.2)):
        rs = a
        while rs <= b - 0.35:
            base = _surface_y(rs, _pl(rs, fx1))
            _plant_strip(bm, fx0 + 0.10, PLANT_RAIL_XN[0] - 0.05,
                         rs - 0.14, rs + 0.14, floor + 0.17 - base, 0.55,
                         "AA_Greeble", "AA_Greeble")
            ribs += 1
            rs += 1.55
    counts["plots"] = plots
    counts["traverses"] = ribs

    # ======================================================================
    # 3. LES CINQ CONDUITES, SUR LEUR BERCEAU
    # ======================================================================
    # ⚠️ LE REPERE PORTE LE DESSUS DU BERCEAU, ET LE BERCEAU EST ECHANTILLONNE
    # SUR LA PEAU : `_surface_box` prend ses quatre coins dans `_surface_y` et
    # rend le Y de son dessus. Une cote ecrite a la main aurait fait replaner les
    # cinq pieces le jour ou le profil bouge — c'est exactement la dette que le
    # BRIEF-0110 a payee sur `CortegeArtery.DECK_Y`.
    for number, (cs, cx) in enumerate(PLANT_CONDUITS, start=1):
        seat = _surface_box(bm, cx - PLANT_LANE_HALF, cx + PLANT_LANE_HALF,
                            cs - PLANT_CRADLE_S, cs + PLANT_CRADLE_S,
                            PLANT_CRADLE_RISE, 0.55, "AA_Greeble", "AA_Hull",
                            draft=0.06)
        # Deux selles sombres sous la piece : elles disent qu'elle est POSEE, et
        # ce sont elles qu'on voit sous le tube a cette plongee.
        for ds in (-0.95, 0.95):
            _surface_box(bm, cx - PLANT_LANE_HALF - 0.10,
                         cx + PLANT_LANE_HALF + 0.10, cs + ds - 0.13,
                         cs + ds + 0.13, PLANT_CRADLE_RISE + 0.16, 0.45,
                         "AA_Greeble", "AA_Greeble")
        tops.append(seat + 0.16)
        seats.append((number, seat))
        anchors.append((f"CTRL | Complexe {number:02d}",
                        Vector((cx, seat, _z(cs)))))

    # ======================================================================
    # 4. L'ENTREE — le seuil, la ferme de cuves, le massif d'allee
    # ======================================================================
    _plant_gate(bm, 419.30, fx0 - 0.05, PLANT_RAIL_XN[1], -3.90)
    tops.append(-3.90)
    for cs in (418.9, 441.4):
        # Les deux bornes qui repondent au seuil de l'autre cote de l'allee.
        for bx in (7.05, 7.05):
            _plant_strip(bm, bx, bx + 0.50, cs - 0.30, cs + 0.30,
                         1.05, 0.80, "AA_Greeble", "AA_Hull")
    tops.append(_surface_y(418.9, 7.30) + 1.05)
    tanks = 0
    for cs in (420.8, 422.4, 424.0, 425.6):
        _plant_prism(bm, _pl(cs, 10.95), cs, 0.55, 0.50,
                     _surface_y(cs, _pl(cs, 11.50)) - 0.35, -3.94, 8,
                     "AA_Hull", "AA_Panel")
        tanks += 1
    tops.append(-3.94)
    _plant_strip(bm, 7.45, 8.55, 420.9, 425.5, 0.78, 0.95,
                 "AA_Greeble", "AA_Hull")
    _plant_strip(bm, 7.70, 8.30, 421.7, 424.7,
                 0.78 + 0.34, 0.60, "AA_Greeble", "AA_Greeble")
    tops.append(_surface_y(423.2, 8.55) + 1.12)

    # ======================================================================
    # 5. LE CŒUR — le bassin, son coaming clair, ses passerelles
    # ======================================================================
    # Le bassin lui-meme est creuse par `build_pits()` : il est declare dans
    # `BASINS`, donc dans `_hollows()`, donc la peau saute ses cellules, les
    # stations pavent son emprise, les modules semes l'evitent et deux harnais le
    # relisent. « Un creux sans son saut de peau est un plancher SOUS une peau
    # intacte : invisible, et definitif. »
    #
    # ⚠️ ET IL LUI FAUT UNE ARETE CLAIRE, SANS QUOI CE N'EST PAS UN VOLUME MAIS
    # UNE TACHE. Ce fichier l'a deja paye sur les fosses : « le creux existait
    # dans le `.glb` — sondee, mesuree, rendue — et restait INVISIBLE en jeu ; le
    # pont d'envol voisin, lui, se lit d'un coup d'œil : il a un coaming CLAIR ».
    # Le bassin porte donc son cadre, `AA_Trim`, sur ses quatre bords.
    # ⚠️ SEULEMENT LES DEUX BOUTS EN IVOIRE, ET NON TOUT LE POURTOUR. C'est
    # exactement la regle que `build_pits()` a payee : « deux plans accrochent la
    # lumiere et disent CA DESCEND ; un ruban de douze metres aurait redessine la
    # coque ». Un cadre entierement clair volait de surcroit la lecture a AMBRY,
    # qui arrive quatre metres plus loin et dont TOUT l'interet est d'etre la
    # seule chose claire des 500 m.
    for a, b in ((basin_s0 - 0.62, basin_s0), (basin_s1, basin_s1 + 0.62)):
        tops.append(_plant_strip(bm, 6.95, 10.75, a, b, 0.50, 1.10,
                                 "AA_Greeble", "AA_Trim"))
    tops.append(_plant_strip(bm, 6.95, 7.35, basin_s0, basin_s1, 0.46, 1.10,
                             "AA_Greeble", "AA_Hull"))
    tops.append(_plant_strip(bm, BASIN_X[1], 10.75, basin_s0, basin_s1,
                             0.46, 1.10, "AA_Greeble", "AA_Hull"))
    bars = 0
    for cs in (429.4, 431.75, 434.1):
        # ⚠️ AU-DESSUS DU COAMING (-4,52) ET NON DEDANS : une passerelle noyee
        # dans le cadre disparait dans l'ombre du creux, et le bassin redevient
        # une tache noire au lieu d'un volume enjambe.
        _box_outward(bm, _pl(cs, 6.95), _pl(cs, 10.75), -5.20, -4.46,
                     cs - 0.32, cs + 0.32, "AA_Hull")
        _box_outward(bm, _pl(cs, 7.75), _pl(cs, 9.95), -4.46, -4.425,
                     cs - 0.05, cs + 0.05, "AA_Emissive_Engine")
        bars += 1
    tops.append(-4.425)
    counts["passerelles"] = bars
    for cs in (429.0, 434.5):
        _plant_prism(bm, _pl(cs, 11.35), cs, 0.60, 0.38,
                     _surface_y(cs, _pl(cs, 11.95)) - 0.30, -3.46, 8,
                     "AA_Greeble", "AA_Panel")
    tops.append(-3.46)
    counts["cuves"] = tanks + 2

    # ======================================================================
    # 6. LA SORTIE — le massif, la passerelle transversale, le seuil
    # ======================================================================
    out_block = _plant_strip(bm, fx0 + 0.15, 11.70, 437.2, 440.4, 0.92, 1.05,
                             "AA_Greeble", "AA_Hull")
    tops.append(out_block)
    _plant_strip(bm, fx0 + 0.45, 11.35, 437.9, 439.7,
                 0.92 + 0.38, 0.60, "AA_Greeble", "AA_Hull")
    tops.append(out_block + 0.38)
    # Deux cuves de sortie, plus petites : la ligne se recompose avant de
    # quitter le complexe.
    for cs in (438.6, 440.2):
        _plant_prism(bm, _pl(cs, 11.05), cs, 0.44, 0.40,
                     _surface_y(cs, _pl(cs, 11.49)) - 0.35, -4.02, 8,
                     "AA_Hull", "AA_Hull")
    tops.append(-4.02)
    # Trois caisses posees dans l'allee : elles disent qu'on y travaille, et
    # elles coutent douze triangles chacune.
    crates = 0
    for cs, cxn, w in ((437.0, 7.45, 0.85), (439.3, 7.30, 1.00),
                       (441.0, 7.55, 0.75)):
        _plant_strip(bm, cxn, cxn + w, cs - 0.42, cs + 0.42, 0.52, 0.60,
                     "AA_Greeble", "AA_Hull")
        crates += 1
    counts["caisses"] = crates
    # La passerelle qui enjambe l'allee et rejoint le massif : c'est elle qui
    # relie les deux moities du complexe, et elle passe AU-DESSUS de la voie.
    _box_outward(bm, _pl(437.6, 7.15), _pl(437.6, 10.30), -4.05, -3.83,
                 437.35, 437.95, "AA_Hull")
    tops.append(-3.83)
    _plant_gate(bm, 441.35, fx0 - 0.05, PLANT_RAIL_XN[1], -3.90)

    top = max(tops)
    if top > BUILD_CEILING_Y + 1e-6:
        raise ak.ContractError(
            f"le complexe culmine a {top:.3f} > plafond de construction "
            f"{BUILD_CEILING_Y} — c'est le plafond de VOL, le chasseur entrerait "
            "dedans")
    stats.update(counts)
    stats["top"] = top
    stats["ciel"] = BUILD_CEILING_Y - top
    stats["plancher"] = floor
    stats["emprise"] = (PLANT_S, PLANT_XN)
    stats["conduites"] = len(anchors)
    stats["sieges"] = seats
    return anchors, stats


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


# ⚠️ `_triangulate_ngons()` A DISPARU (BRIEF-0092) : `ak.triangulate()` triangule
# TOUT, et c'est `ak.box_project_uv()` qui l'appelle desormais. Ne decouper que
# les n-gons suffisait aux TANGENTES, pas aux UV : sur un quad GAUCHE, la
# projection en boite est calculee pour une normale moyenne qui n'est celle
# d'aucun des deux triangles exportes, et l'un des deux peut sortir projete selon
# un axe qui n'est pas le sien. Mesure sur CE fichier, avant/apres : 20 triangles
# de la Section_01 sortaient hors de leur axe dominant — 0 apres. Le detail est
# dans `aegis_kit.triangulate()`.


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
    skipped = build_skin(bm, index)
    # ⚠️ L'ORIENTATION DE LA PEAU SE VERIFIE ICI, entre la peau et la collerette.
    # Apres, les faces de collerette regardent vers l'axe du vaisseau et le
    # harnais les lirait — a raison — comme retournees.
    _assert_skin_outward(bm, name)

    # ⚠️ L'ORDRE DE CES SEPT APPELS EST UNE DECISION, PAS UNE HABITUDE. Les
    # GREFFES sont maillees en premier parce qu'elles sont elles-memes des
    # installations au sens du rythme du brief (« calme → une installation →
    # calme → un hangar ») : ce sont donc elles, avec les marqueurs, qui
    # definissent ou les plaques et les pastilles ont le droit de se poser.
    # Aucune n'est deduite d'une autre a l'execution : chaque famille lit la
    # table `aprons` deja constituee, et le flux `rng` reste un flux unique —
    # deterministe et reproductible au sha256.
    busy: list[tuple[float, float]] = []
    graft_spans: list[tuple[float, float]] = []
    # ⚠️ LE JOURNAL DE LA GARDE D'AFFUT (BRIEF-0101), et il est rendu au rapport
    # troncon par troncon. « Une greffe rejetee est une greffe perdue » : sans ces
    # deux colonnes, la difference entre un borde qui s'ecarte d'un socle et un
    # borde qui redevient plat autour de dix-sept installations ne se verrait que
    # dans le total des modules, ou elle se confondrait avec le hasard du tirage.
    keepout: dict[str, int] = {}
    grafts = build_grafts(bm, index, rng, busy, graft_spans, keepout)
    aprons = list(MARKER_APRONS) + graft_spans
    counts = {
        "cellules_percees": skipped,
        "collerettes": build_bay_flanges(bm, index),
        "fosses": build_pits(bm, index),
        "passerelle": build_cross_bridge(bm, index),
        "bastions": build_bastions(bm, index),
        "greffes": grafts,
        "plaques": build_plates(bm, index, rng, aprons, busy, keepout),
        "nervures": build_ribs(bm, index, rng, busy, keepout),
        "lisses": build_strakes(bm, index),
        "pastilles": build_pips(bm, index, rng, aprons, busy, keepout),
    }
    for label in ("greffes_ecartees", "greffes_perdues",
                  "plaques_ecartees", "plaques_perdues",
                  "nervures_ecartees", "nervures_perdues",
                  "pastilles_perdues"):
        counts[label] = keepout.get(label, 0)
    conduits, lit = build_conduits(bm, index, rng)
    counts["conduits"] = conduits
    counts["travees"] = build_canal_braces(bm, index, rng)
    # ⚠️ APRES LES DEUX FAMILLES SEEDEES DU CANAL, ET SANS TOUCHER AU FLUX. Une
    # branche ne tire rien (voir `build_branches`) : la poser ici ou ailleurs ne
    # change pas un sommet des autres familles. Elle vient en dernier parce que
    # c'est l'ordre de LECTURE du decor — le canal, puis ce qui en sort.
    branches, branch_length, branch_area = build_branches(bm, index)
    counts["branches"] = branches
    counts["branches_longueur"] = branch_length
    counts["branches_veine_m2"] = branch_area

    # --- LES ZONES CALMES, MESUREES ICI ET RENDUES AU RAPPORT --------------
    # ⚠️ « Les zones calmes sont un livrable, pas un manque — a mesurer et a
    # rendre. » La definition est donc ECRITE, sans quoi le chiffre ne veut rien
    # dire : est CALME un metre de longueur du troncon dont le BORDE ne porte
    # aucun module en relief. Sont exclus du compte, et pour la meme raison —
    # ils sont continus PAR CONSTRUCTION et n'ont donc pas de rythme a rompre :
    #
    #   * l'ARTERE et tout ce qui vit entre ses rebords (|x| <= 1,70) : conduits,
    #     travees, nœuds. Elle est un organe qui file d'un bout a l'autre du
    #     vaisseau, pas un accident de bordé ;
    #   * les LISSES longitudinales, qui courent sur 97 m et donnent au joueur sa
    #     seule lecture continue de la vitesse (BRIEF-0089).
    #
    # Ce qui est compte, c'est ce que le brief nomme : plaques, nervures,
    # greffes, pastilles — et l'emprise des installations elles-memes.
    occupied = list(busy)
    # ⚠️ LES RELIEFS POSES A LA MAIN COMPTENT AUSSI, ET ILS MANQUAIENT. Le calme se
    # calculait sur `busy` (les modules SEEDES) plus les emprises d'installations.
    # Les fosses, la passerelle et les bastions ne sont ni l'un ni l'autre : ils
    # occupaient jusqu'a 36 m de borde sans qu'un metre ne sorte du compte, et le
    # chiffre annonce SURESTIMAIT le calme. Un indicateur qui ne voit pas ce qu'on
    # vient d'ajouter ne mesure plus rien — c'est la meme classe de defaut que la
    # liste blanche du tableau des modules.
    # ⚠️ ET LES TRANCHEES DE BASTION COMPTENT AVEC LES FOSSES — d'ou `_hollows()`.
    # Elles portent en plus, GRATUITEMENT, l'emprise de la Citadelle : le verrou
    # occupe s 239,6 a 246,0 en pieces de KIT, que ce fichier ne voit pas, et la
    # tranchee qui l'assied va de 239,2 a 246,4. La compter, c'est compter le
    # verrou. Sans quoi le chiffre de calme surestimerait de six metres de borde
    # le plus charge du vaisseau — exactement le defaut que la ligne du dessus
    # decrit, reproduit sur ce qu'on vient d'ajouter.
    for pc, ph, _side, _xs, _floor in _hollows():
        occupied.append((pc - ph, pc + ph))
    for bc, bh, _xi, _xo, _h in BASTIONS:
        occupied.append((bc - bh, bc + bh))
    occupied.append((CROSS_BRIDGE_S - CROSS_BRIDGE_HS,
                     CROSS_BRIDGE_S + CROSS_BRIDGE_HS))
    # ⚠️ ET LE COMPLEXE DU BRIEF-0111, POUR LA MEME RAISON QUE LES DEUX LIGNES
    # DU DESSUS : il occupe 24,5 m de borde sans etre un marqueur ni un module
    # seede. Sans cette ligne, le calme annonce surestimerait de 24 m.
    occupied.append((PLANT_S[0] - APRON_PLANT, PLANT_S[1] + APRON_PLANT))
    for a, b, _n, _x in INSTALLATION_SPANS:
        lo = max(a, origin)
        hi = min(b, origin + SECTION_LENGTH)
        if hi > lo:
            occupied.append((lo, hi))
    merged = _merge([(max(a, origin), min(b, origin + SECTION_LENGTH))
                     for a, b in occupied
                     if min(b, origin + SECTION_LENGTH)
                     > max(a, origin)])
    calm: list[tuple[float, float]] = []
    cursor = origin
    for a, b in merged:
        if a > cursor:
            calm.append((cursor, a))
        cursor = max(cursor, b)
    if cursor < origin + SECTION_LENGTH:
        calm.append((cursor, origin + SECTION_LENGTH))
    counts["calme_total"] = sum(b - a for a, b in calm)
    counts["calme_max"] = max((b - a for a, b in calm), default=0.0)
    counts["calme_plages"] = len([1 for a, b in calm if b - a >= 8.0])
    counts["artere_allumee"] = lit

    anchors: list[tuple[str, Vector]] = []
    pads = 0
    for number, (s, x) in enumerate(TURRETS, start=1):
        if not (origin <= s < origin + SECTION_LENGTH):
            continue
        # ⚠️ Le marqueur ne bouge NI EN X NI EN Z (BRIEF-0093) : le moteur monte
        # le kit dessus par son nom exact. Seul son Y change — il passe de la
        # levre du socle cuit (peau + 0,65) au PLAN D'ASSISE, c'est-a-dire au
        # point le plus haut de l'emprise du kit. C'est ce plan-la, et lui seul,
        # sur lequel `turret_kit.glb` est modelise.
        mx = _marker_x(s, x)
        seat, _ = turret_seat_y(s, mx)
        anchors.append((f"Turret_{number:02d}", Vector((mx, seat, _z(s)))))
        pads += 1
    bays = 0
    for number, (s, x) in enumerate(BAYS, start=1):
        if not (origin <= s < origin + SECTION_LENGTH):
            continue
        # ⚠️ Le marqueur ne bouge NI EN X NI EN Z — le moteur monte ses ponts
        # dessus par leur nom exact, et un deplacement casserait le niveau en
        # silence. Seul son Y change : il passe de la levre du coaming pose
        # (-3,460) au plan de la BOUCHE, c'est-a-dire au point le plus haut du
        # pourtour de l'ouverture. C'est ce plan-la, et lui seul, sur lequel
        # `bay_kit.glb` est modelise.
        mouth, _ = bay_mouth_y(s, x)
        anchors.append((f"Bay_{number:02d}", Vector((x, mouth, _z(s)))))
        bays += 1
    spines = 0
    for number, s in enumerate(SPINES, start=1):
        if not (origin <= s < origin + SECTION_LENGTH):
            continue
        # ⚠️ Le marqueur ne bouge NI EN X NI EN Z (le brief le fige) : seul son Y
        # change, et il change beaucoup — il passe du SOMMET du bulbe cuit
        # (-3,160) au PLAN D'ASSISE DANS LE FOND DU CANAL. C'est ce plan-la, et
        # lui seul, sur lequel `spine_kit.glb` est modelise.
        seat, _ = spine_seat_y(s)
        anchors.append((f"Spine_{number:02d}", Vector((0.0, seat, _z(s)))))
        spines += 1
    conduites = 0
    for number, (s, x) in enumerate(ARTERY_CONDUITS, start=1):
        if not (origin <= s < origin + SECTION_LENGTH):
            continue
        anchors.append((f"CTRL | Conduite {number:02d}",
                        Vector((x, _surface_y(s, x), _z(s)))))
        conduites += 1
    counts["marqueurs_tourelle"] = pads
    counts["baies"] = bays
    counts["nœuds"] = spines
    counts["conduites_reperes"] = conduites

    # ⚠️ LE COMPLEXE EST MAILLE DANS LE BMESH DU TRONCON, ET NON A COTE COMME
    # AMBRY. Ambry a son propre objet parce qu'elle a sa propre ECHELLE D'UV
    # (0,700 tuile/m contre 0,200) : c'est une greffe humaine vue de plus pres,
    # avec son propre huitieme slot. Le complexe, lui, est de la matiere de
    # l'Unisson, aux memes quatre slots que le borde et a la meme distance de
    # vue : lui donner un depliage a part le ferait recevoir des cartes d'une
    # autre finesse que la tole sur laquelle il est pose, et la couture se
    # verrait au premier metre.
    # ⚠️ ON COMPTE DES TRIANGLES, PAS DES FACES. Le complexe pose des n-gones —
    # un longeron de 24,5 m est un ruban de 42 sommets — et `ak.triangulate()`
    # ne passera qu'apres. Un compte de faces annoncerait 688 la ou le `.glb`
    # en portera 2 060 : le brief demande de RAPPORTER le cout, pas de le
    # sous-estimer.
    before = set(bm.faces)
    plant_anchors, plant_stats = build_plant(bm, index)
    counts["complexe"] = sum(len(f.verts) - 2 for f in bm.faces
                             if f not in before)
    counts["complexe_reperes"] = len(plant_anchors)
    anchors += plant_anchors
    if plant_stats:
        counts["complexe_stats"] = plant_stats

    hull = _new_object(name, bm)
    _weld(hull)
    # ⚠️ TRIANGULER AVANT DE LISSER ET AVANT DE DEPLIER (BRIEF-0092). Le kit le
    # referait au depliage, mais l'ordre compte : un quad gauche lisse avant
    # d'etre coupe ne porte pas la meme arete que coupe puis lisse, et la mesure
    # d'UV doit se faire sur les faces REELLEMENT exportees.
    ak.triangulate(hull)
    ak.shade_smooth_by_angle(hull, angle_deg=26.0)
    ak.box_project_uv(hull, HULL_TEXELS_PER_METER)

    if index == SECTION_COUNT - 1:
        abm = bmesh.new()
        anchor, ambry_stats = build_ambry(abm)
        ambry = _new_object(name + "_Ambry", abm)
        _weld(ambry)
        ak.triangulate(ambry)
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
    names += [f"CTRL | Conduite {i:02d}"
              for i in range(1, len(ARTERY_CONDUITS) + 1)]
    names += [f"CTRL | Complexe {i:02d}"
              for i in range(1, len(PLANT_CONDUITS) + 1)]
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

    # ⚠️ LES DOUZE CONDUITES SONT RELUES DANS LE BINAIRE, ET LEUR `y` DOIT
    # DIFFERER D'UNE STATION A L'AUTRE. C'est la seule preuve qu'il est
    # ECHANTILLONNE et non constant : une constante recopiee passerait toutes
    # les autres verifications sans un mot (c'est exactement ce qui s'est
    # produit avec `CortegeArtery.DECK_Y = -4,30`).
    conduit_y: list[float] = []
    for number, (s, x) in enumerate(ARTERY_CONDUITS, start=1):
        marker = f"CTRL | Conduite {number:02d}"
        if marker not in found:
            continue
        translation = found[marker][1]
        want = _surface_y(s, x)
        conduit_y.append(translation[1])
        if abs(translation[0] - x) > 1e-4 or abs(translation[1] - want) > 1e-4:
            problems.append(
                f"{marker} : ({translation[0]:.4f}, {translation[1]:.4f}) au lieu "
                f"de ({x:.4f}, {want:.4f}) — le repere ne tombe pas sur la peau")
    if len(set(round(v, 4) for v in conduit_y)) < 2:
        problems.append(
            "les douze CTRL | Conduite portent le MEME y : le repere n'est pas "
            "echantillonne sur la peau, il est constant — c'est la dette que ce "
            "lot devait supprimer")

    # ⚠️ LES CINQ REPERES DU COMPLEXE SONT RELUS DE LA MEME FACON, ET AVEC UNE
    # VERIFICATION DE PLUS : LE CIEL. Un repere de conduite marque le BAS de la
    # piece ; ce qui doit tenir sous le plafond de vol, c'est le HAUT. La piece
    # droite mesure 0,46 m, la coudee 0,92 (mesure sur les `.glb`) — on prend la
    # pire, parce que le concepteur peut monter l'une ou l'autre et que rien
    # dans ce fichier ne le lui interdit.
    plant_y: list[float] = []
    for number, (s, x) in enumerate(PLANT_CONDUITS, start=1):
        marker = f"CTRL | Complexe {number:02d}"
        if marker not in found:
            continue
        translation = found[marker][1]
        plant_y.append(translation[1])
        if abs(translation[0] - x) > 1e-4:
            problems.append(
                f"{marker} : x = {translation[0]:.4f} au lieu de {x:.4f}")
        local_z = -(s - SECTION_LENGTH * int(s // SECTION_LENGTH))
        if abs(translation[2] - local_z) > 1e-4:
            problems.append(
                f"{marker} : z = {translation[2]:.4f} au lieu de "
                f"{local_z:.4f}")
        seat = translation[1]
        if seat <= _surface_y(s, x) + 1e-4:
            problems.append(
                f"{marker} : assise {seat:.4f} au niveau de la peau "
                f"({_surface_y(s, x):.4f}) — le berceau n'a pas ete pose")
        if seat + CONDUIT_PIECE_TOP > BUILD_CEILING_Y:
            problems.append(
                f"{marker} : une conduite coudee y culminerait a "
                f"{seat + CONDUIT_PIECE_TOP:.3f} > plafond de construction "
                f"{BUILD_CEILING_Y}")
    if plant_y and len(set(round(v, 4) for v in plant_y)) < 2:
        problems.append(
            "les cinq CTRL | Complexe portent le MEME y : leur berceau n'est pas "
            "echantillonne sur la peau")

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
    total_seen = 0.0
    area_by_material: dict[str, float] = {}
    seen_area: dict[str, float] = {}
    ambry_slot_strays = 0
    ambry_slot_tris = 0

    # --- LE DEGAGEMENT DES AFFUTS, MESURE SUR LE BINAIRE (BRIEF-0101) --------
    # ⚠️ « LE REJET EST EN PLACE » N'EST PAS UNE REPONSE. C'est exactement ce que
    # `turret_seat_y()` croyait deja : elle echantillonne la PEAU, se croit juste,
    # et laissait une greffe de 1,01 m se poser par-dessus son propre disque. Une
    # garde qui ne se mesure pas sur le fichier livre est une intention. On
    # echantillonne donc la hauteur du maillage dans le disque de 2,50 m autour
    # de chacun des dix-sept marqueurs, et on la compare a l'assise.
    #
    # ⚠️ ET ON DISTINGUE LA PEAU DES MODULES, sans quoi la mesure serait fausse
    # dans les deux sens. L'assise est le point le plus haut de l'emprise du KIT
    # (2,08 m) : au-dela, la peau elle-meme remonte jusqu'a +0,010 m sur le
    # binaire — elle ne se deplace pas, elle EST le vaisseau. Un sommet compte
    # donc comme module s'il depasse `_surface_y()` de plus de 2 cm ; la peau,
    # elle, ne s'en ecarte que du bruit du float32.
    keepout_lookup = _turret_lookup()
    keepout_worst: dict[str, list[float]] = {
        f"Turret_{n:02d}": [-math.inf, -math.inf, 0]
        for n in range(1, len(TURRETS) + 1)}

    # --- LA VEINE DE CHAQUE BRANCHE, COMPTEE SUR LE BINAIRE (BRIEF-0103) ----
    # ⚠️ C'EST LE SEUL CONTROLE QUI RENDE L'EXTINCTION SURE, ET IL NE PEUT PAS SE
    # FAIRE AUTREMENT QUE SUR LE FICHIER. `CortegeSkin` reconnait le slot
    # `AA_Emissive_Engine` PAR SON NOM et donne a chaque troncon SA copie du
    # materiau ; c'est cette copie que le moteur baisse quand le nœud tombe. Une
    # veine posee dans un autre slot resterait allumee sur un vaisseau mort — et
    # rien ne le dirait : ni erreur d'import, ni test rouge, ni compte de
    # triangles. On compte donc, par branche et par troncon, les triangles
    # REELLEMENT emissifs dans le couloir de la branche, et l'on compare leur
    # aire a celle que le trace annonce.
    branch_vein: dict[str, list] = {
        r["name"]: [0, 0.0, ""] for r in branch_routes()}
    emissive_by_section: dict[str, list] = {}

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
                here = -(pz + translation[2])
                bucket = int(math.floor(here / TURRET_BUCKET))
                for probe in (bucket - 1, bucket, bucket + 1):
                    for tname, ts, mx, seat in keepout_lookup.get(probe, ()):
                        if (px - mx) ** 2 + (here - ts) ** 2 \
                                > TURRET_KEEPOUT_R * TURRET_KEEPOUT_R:
                            continue
                        worst = keepout_worst[tname]
                        worst[2] += 1
                        slot = 0 if py > _surface_y(here, px) + 0.02 else 1
                        worst[slot] = max(worst[slot], py - seat)
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
    # ⚠️ LA LARGEUR N'EST PLUS CONSTANTE, ET CE CONTRAT A DU APPRENDRE A LIRE
    # `TAPER`. Il comparait la demi-largeur mesuree a `HALF_WIDTH` : une coque de
    # 28 m au micron, ce qui etait vrai tant que 412 m de bordes etaient
    # paralleles. Il compare desormais au MAXIMUM que la table annonce — le
    # garde-fou reste entier (une coque plus large que son propre profil reste
    # refusee), et il refuse en plus une table qui deraperait au-dela des +25 pct
    # que les consignes autorisent.
    expected = HALF_WIDTH * max(k for _, k, _ in TAPER)
    if abs(widest - expected) > 1e-3:
        problems.append(
            f"largeur hors-tout {2 * widest:.4f} m au lieu de {2 * expected:.4f} "
            f"annoncee par TAPER (nominal {2 * HALF_WIDTH})")
    if expected > HALF_WIDTH * 1.25 + 1e-6:
        problems.append(
            f"TAPER elargit la coque de {(expected / HALF_WIDTH - 1) * 100:.0f} pct, "
            "au-dela des 25 pct que les consignes de silhouette autorisent")

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

    # --- LES SEPT OUVERTURES SONT REELLEMENT PERCEES (BRIEF-0091) -------------
    # ⚠️ Le controle porte sur le BINAIRE, triangle par triangle, et il est
    # bloquant. Une ouverture qui se refermerait — un point de profil perdu, une
    # station arrondie autrement, un module seede qui repasse dessus — ne se
    # verrait sur AUCUN autre chiffre : ni le compte de triangles, ni la bbox,
    # ni les UV, ni le budget. C'est exactement le defaut que BRIEF-0089 a livre
    # et que seul le regard a attrape ; cette fois il a un harnais.
    section_bays: dict[str, list[tuple[float, float, float]]] = {}
    for number, (bs, bx) in enumerate(BAYS, start=1):
        section_index = int(bs // SECTION_LENGTH)
        mouth, _ = bay_mouth_y(bs, bx)
        section_bays.setdefault(f"Section_{section_index + 1:02d}", []).append(
            (-(bs - section_index * SECTION_LENGTH), bx, mouth))
    bay_intruders = 0

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
            # `s` global de ce troncon : les sommets sont en coordonnees LOCALES
            # et `_surface_y` raisonne en `s` global (le fuseau de proue).
            section_origin = (int(name.split("_")[1]) - 1) * SECTION_LENGTH
            for ia, ib, ic in triangles:
                cx = (points[ia][0] + points[ib][0] + points[ic][0]) / 3.0
                cy = (points[ia][1] + points[ib][1] + points[ic][1]) / 3.0
                cz = (points[ia][2] + points[ib][2] + points[ic][2]) / 3.0
                for bz, bx, mouth in section_bays.get(name, ()):
                    if not (abs(cx - bx) <= BAY_HALF_X - 0.05
                            and abs(cz - bz) <= BAY_HALF_S - 0.05
                            and cy > mouth - 2.0):
                        continue
                    # ⚠️ LA DISTINCTION « SOCLE » / « INTRUS » A DISPARU AVEC LES
                    # SOCLES (BRIEF-0093). Elle existait parce que deux socles
                    # cuits se tenaient legitimement dans une emprise de baie et
                    # que les melanger aux intrus aurait rendu le harnais
                    # inutilisable. La coque ne cuit plus aucun socle : tout
                    # triangle trouve ici est une PEAU QUI S'EST REFERMEE, et
                    # `_marker_clashes()` garde a lui seul l'arbitrage des
                    # positions de marqueurs.
                    bay_intruders += 1
                    break
                in_keepout = last and keep_x[0] <= cx <= keep_x[1] \
                    and keep_z[0] <= cz <= keep_z[1]
                if in_keepout:
                    if cy >= ambry_floor and ambry_x[0] <= cx <= ambry_x[1]:
                        ambry_tris.append((abase + ia, abase + ib, abase + ic))
                else:
                    tris.append((base + ia, base + ib, base + ic))
                pa = Vector(points[ia])
                normal = (Vector(points[ib]) - pa).cross(Vector(points[ic]) - pa)
                area = normal.length
                total_area += area * 0.5
                area_by_material[material] = \
                    area_by_material.get(material, 0.0) + area * 0.5
                if material == "AA_Emissive_Engine":
                    emissive_area += area * 0.5
                    tally = emissive_by_section.setdefault(name, [0, 0.0])
                    tally[0] += 1
                    tally[1] += area * 0.5
                    here = section_origin - cz
                    for route in branch_routes():
                        if route["reason"] is not None:
                            continue
                        if abs(here - route["station"]) > route["vein"] * 0.5:
                            continue
                        side = route["side"]
                        lo = min(side * route["x_in"], side * route["x_out"])
                        hi = max(side * route["x_in"], side * route["x_out"])
                        if not (lo - 0.02 <= cx <= hi + 0.02):
                            continue
                        seen_vein = branch_vein[route["name"]]
                        seen_vein[0] += 1
                        seen_vein[1] += area * 0.5
                        seen_vein[2] = name
                        break
                # ⚠️ L'AIRE VUE, ET ELLE EST LA SEULE QUI PARLE DE L'ECRAN.
                # La repartition 80/15/5 du brief decrit des PIXELS ; l'aire
                # totale d'une coque de 500 m est aux deux tiers son VENTRE, que
                # la camera du jeu — qui plonge a 70 deg — ne voit jamais.
                # Mesure : `AA_Greeble` pese 64,8 pct de l'aire totale et
                # l'essentiel n'en est que le fond de la coque. Comparer ce
                # chiffre a la cible du brief n'aurait aucun sens.
                #
                # Est VUE une face qui satisfait DEUX conditions, et il en
                # fallait bien deux :
                #
                #   * elle regarde la camera (produit scalaire avec -CAM_FORWARD
                #     au-dessus de 0,05) ;
                #   * elle est AU-DESSUS DE LA PEAU a son propre (x, s). Sans ce
                #     second filtre, les jupes ENTERREES du vocabulaire
                #     modulaire — 0,55 a 0,70 m sous la surface, sur mille
                #     plaques — entraient dans le compte : 6 000 m2 de faces
                #     qui ne rendent pas un pixel, toutes en `AA_Greeble`, et la
                #     repartition annoncait 44 pct de machinerie pour un decor
                #     qui n'en montre pas la moitie.
                #
                # C'est une APPROXIMATION — elle ignore les occultations entre
                # pieces — et elle est declaree comme telle au compte-rendu.
                skin = _surface_y(section_origin - cz, cx)
                if area > 1e-12 and \
                        (normal / area).dot(_VIEW_DIR) > 0.05 and \
                        cy > skin - 0.03:
                    seen_area[material] = \
                        seen_area.get(material, 0.0) + area * 0.5
                    total_seen += area * 0.5
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

    problems += _marker_clashes()

    # ⚠️ LE VERDICT DU DEGAGEMENT, ET IL EST BLOQUANT. Un module au-dessus de
    # l'assise, c'est le socle (+0,27), la couronne (+0,40) ou le bloc (+1,52)
    # du kit qui disparaissent dedans — sans une erreur d'import, sans un test
    # rouge, et sans que rien ne change dans le code du jeu. La mesure ci-dessous
    # est la seule chose qui empeche ce defaut de revenir au prochain reglage de
    # semis, et elle est faite sur le fichier qui part dans Godot.
    turret_clearances: list[tuple[str, float, float, int]] = []
    for number in range(1, len(TURRETS) + 1):
        tname = f"Turret_{number:02d}"
        module, skin, seen = keepout_worst[tname]
        turret_clearances.append((tname, module, skin, seen))
        if module > 1e-3:
            problems.append(
                f"{tname} : un module monte {module:.3f} m AU-DESSUS de l'assise "
                f"dans le disque de {TURRET_KEEPOUT_R:.2f} m — l'affut s'y "
                "enfoncerait d'autant. C'est le defaut de BRIEF-0101 : une "
                "famille de relief a repris le droit de se poser sur une emprise "
                "de tourelle (voir `_turret_clash`)")
    # ⚠️ LE VERDICT DE LA VEINE, ET IL EST BLOQUANT (BRIEF-0103). Zero triangle
    # emissif dans le couloir d'une branche, c'est une branche qui ne s'eteindra
    # jamais ; une aire trop courte, c'est une veine mangee par un module qui a
    # repris le droit de se poser dessus (`_branch_clash`).
    for route in branch_routes():
        if route["reason"] is not None:
            continue
        tris, vein_area, owner = branch_vein[route["name"]]
        wanted = route["length"] * route["vein"]
        if tris == 0:
            problems.append(
                f"{route['name']} : AUCUN triangle '{'AA_Emissive_Engine'}' dans "
                "le couloir de sa branche — la veine a change de slot, et une "
                "veine hors de ce slot reste ALLUMEE sur un vaisseau mort "
                "(CortegeSkin la reconnait par ce nom, BRIEF-0103)")
        elif vein_area < wanted * 0.98:
            problems.append(
                f"{route['name']} : la veine ne fait que {vein_area:.2f} m2 pour "
                f"{wanted:.2f} m2 traces — un module s'est repose dessus "
                "(voir `_branch_clash`)")
        elif vein_area > wanted * 1.35:
            problems.append(
                f"{route['name']} : la veine fait {vein_area:.2f} m2 pour "
                f"{wanted:.2f} m2 traces — le couloir compte de l'emissif qui "
                "n'est pas le sien")

    if bay_intruders:
        problems.append(
            f"{bay_intruders} triangle(s) DANS l'emprise d'un pont d'envol — "
            "l'ouverture s'est refermee, le hangar redeviendrait un bouton")
    for number, (bs, bx) in enumerate(BAYS, start=1):
        mouth, low = bay_mouth_y(bs, bx)
        marker = f"Bay_{number:02d}"
        if marker not in found:
            continue
        translation = found[marker][1]
        if abs(translation[0] - bx) > 1e-4 or abs(translation[1] - mouth) > 1e-4:
            problems.append(
                f"{marker} : ({translation[0]:.4f}, {translation[1]:.4f}) au lieu "
                f"de ({bx:.4f}, {mouth:.4f}) — le marqueur doit rester en X et "
                "passer au plan de la bouche")
        if mouth - low > BAY_WELL_DEPTH:
            problems.append(
                f"{marker} : le pourtour de l'ouverture accuse {mouth - low:.2f} m "
                f"de denivele, plus que la profondeur du puits ({BAY_WELL_DEPTH} m)")

    # --- LES NŒUDS D'EPINE : sur l'axe, DANS le canal ------------------------
    # ⚠️ Harnais neuf (BRIEF-0094). Le marqueur a change de plan — du sommet du
    # bulbe cuit au fond de la tranchee — et `spine_kit.glb` est modelise sur ce
    # plan-la. S'ils divergeaient, le nœud flotterait au-dessus du canal ou s'y
    # enterrerait, et rien d'autre ne le verrait : c'est exactement la faute que
    # `bay_mouth_y()` a evitee au hangar et `turret_seat_y()` au socle.
    spine_seats: list[tuple[str, float, float, float]] = []
    for number, s in enumerate(SPINES, start=1):
        seat, low = spine_seat_y(s)
        scale = _scales(s)[0]
        rim = _surface_y(s, CANAL_RIM_X * scale)
        spine_seats.append((f"Spine_{number:02d}", seat, low, rim))
        marker = f"Spine_{number:02d}"
        if marker not in found:
            continue
        translation = found[marker][1]
        if abs(translation[0]) > 1e-6 or abs(translation[1] - seat) > 1e-4:
            problems.append(
                f"{marker} : ({translation[0]:.4f}, {translation[1]:.4f}) au lieu "
                f"de (0, {seat:.4f}) — le marqueur reste sur l'axe et passe au "
                "plan d'assise du fond de canal")
        if rim - seat < 0.35:
            problems.append(
                f"{marker} : le rebord n'est qu'a {rim - seat:.3f} m au-dessus de "
                "l'assise — le nœud ne siegerait plus dans une tranchee")
        if SPINE_FOOTPRINT_HX > CANAL_FLOOR_HALF * scale - 0.04:
            problems.append(
                f"{marker} : le berceau ({2 * SPINE_FOOTPRINT_HX:.2f} m) ne tient "
                f"pas dans le fond plat du canal "
                f"({2 * CANAL_FLOOR_HALF * scale:.2f} m) a cette station")

    if ambry_slot_strays:
        problems.append(
            f"{ambry_slot_strays} triangle(s) en '{AMBRY_HULL}' hors de l'emprise "
            "d'Ambry — ce slot lui est reserve (BRIEF-0090)")

    # --- LA PALETTE ET LES ZONES CALMES : deux cliquets, pas deux opinions ---
    # ⚠️ Ce sont des LIVRABLES du brief (« aire par materiau en pourcentage »,
    # « part de longueur calme »), et un livrable qui n'est pas tenu par un
    # harnais redevient une intention au premier module qu'on rajoutera. Les
    # bornes sont larges : elles n'imposent pas la valeur retenue, elles
    # interdisent le retour a l'etat d'avant. Le chiffre exact est imprime.
    # ⚠️ ET LA CARTE DES PLAGES NUES EST TENUE, ELLE AUSSI. Les vingt et une
    # plages que les trente marqueurs laissent sont le PLAFOND de ce que la forge
    # peut rendre calme : le maillage ne peut que les manger. Ce controle fige
    # leur nombre utile — deplacer un marqueur de gameplay peut legitimement le
    # changer, mais alors on le voit, au lieu de perdre la respiration du niveau
    # module par module.
    wide = [(a, b) for a, b in FREE_GAPS if b - a >= CALM_MIN]
    if len(wide) < 8:
        problems.append(
            f"seulement {len(wide)} plages nues de {CALM_MIN:.0f} m ou plus entre "
            "les emprises de marqueur : le rythme « 15-20 m calmes → une "
            "installation » n'a plus de place ou exister (arbitrage de "
            "conception : ce sont les marqueurs qu'il faut ecarter)")

    violet = (seen_area.get("AA_Panel", 0.0)
              + seen_area.get("AA_Emissive_Engine", 0.0))
    seen_ratio = violet / total_seen if total_seen else 0.0
    if seen_ratio > 0.09:
        problems.append(
            f"violet + magenta = {100 * seen_ratio:.2f} pct de l'aire VUE : le "
            "brief pose 5 pct, le cliquet 9. C'est la hierarchie du niveau qui "
            "se joue la (joueur > ennemi > decor)")
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
        "seen_by_material": seen_area,
        "total_area": total_area,
        "total_seen": total_seen,
        "ambry_slot_triangles": ambry_slot_tris,
        "bays": [(f"Bay_{n:02d}", bs, bx, *bay_mouth_y(bs, bx))
                 for n, (bs, bx) in enumerate(BAYS, start=1)],
        "pad_clearances": _pad_bay_clearances(),
        "turret_clearances": turret_clearances,
        "branch_routes": branch_routes(),
        "branch_vein": branch_vein,
        "emissive_by_section": emissive_by_section,
        "spine_seats": spine_seats,
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
#: La direction OPPOSEE au regard : une face la regarde si son produit
#: scalaire avec elle est positif. Sert a la seule mesure d'aire VUE
#: (voir `_audit`), et elle est derivee de la camera du jeu, jamais recopiee.
_VIEW_DIR = -CAM_FORWARD
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
    # ⚠️ LE GARDE MUTUEL PASSE AVANT LE PREMIER SOMMET. Une faute de table est une
    # faute de DONNEE : la laisser traverser huit minutes de maillage pour sortir
    # a l'audit, c'est huit minutes payees pour apprendre qu'on a mal tape un
    # nombre.
    clashes = _marker_clashes()
    if clashes:
        raise ak.ContractError(
            "TABLES DE MARQUEURS ROMPUES — long_cortege\n"
            + "\n".join(f"  - {p}" for p in clashes))
    _assert_canal()
    _assert_taper_spares_the_bays()
    _assert_pits_are_clear()
    _assert_moats_are_hollow()
    _assert_bastions_are_clear()
    _assert_plant_is_clear()
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
    # ⚠️ CETTE LISTE EST BLANCHE, ET C'EST UN PIEGE QUE CE FICHIER DOCUMENTE DEJA :
    # « le compte de modules imprime a chaque build a montre deux colonnes a zero ».
    # Une famille absente d'ici ne se compte pas, donc ne se surveille pas — les
    # fosses ont ete construites un build entier sans qu'aucune ligne ne les
    # mentionne, et l'on a cherche dans le rendu ce qu'il fallait chercher ici.
    for label in ("plaques", "nervures", "lisses", "greffes", "pastilles",
                  "conduits", "travees", "branches",
                  "marqueurs_tourelle", "baies", "nœuds",
                  "fosses", "passerelle", "bastions", "cellules_percees",
                  "collerettes", "complexe", "complexe_reperes",
                  # BRIEF-0101 — la garde d'affut, ecartees puis perdues.
                  "greffes_ecartees", "greffes_perdues",
                  "plaques_ecartees", "plaques_perdues",
                  "nervures_ecartees", "nervures_perdues",
                  "pastilles_perdues"):
        line = " ".join(f"{c.get(label, 0):>5}" for c in report["counts"])
        total = sum(c.get(label, 0) for c in report["counts"])
        print(f"  modules {label:<18} {line}   = {total}")

    # ⚠️ PRIORITE 3 : « quelle est la plus longue plage nue, et quelle part de la
    # longueur est calme ? » — c'est une question du brief, elle a donc une
    # reponse chiffree a chaque build. Definition dans `build_section()`.
    print("\n  ZONES CALMES (bordé nu : ni plaque, ni nervure, ni greffe, ni "
          "pastille,\n  ni emprise d'installation ; l'artere et les lisses sont "
          "continues par construction)")
    calm_total = sum(c["calme_total"] for c in report["counts"])
    print(f"    {'troncon':<12} {'calme':>8} {'part':>7} {'plage max':>11} "
          f"{'plages >= 8 m':>14}")
    for number in range(1, SECTION_COUNT + 1):
        c = report["counts"][number - 1]
        print(f"    Section_{number:02d}   {c['calme_total']:>7.1f} m "
              f"{100.0 * c['calme_total'] / SECTION_LENGTH:>6.1f}% "
              f"{c['calme_max']:>10.1f} m {c['calme_plages']:>14}")
    print(f"    {'TOTAL':<12} {calm_total:>7.1f} m "
          f"{100.0 * calm_total / SHIP_LENGTH:>6.1f}% "
          f"{max(c['calme_max'] for c in report['counts']):>10.1f} m "
          f"{sum(c['calme_plages'] for c in report['counts']):>14}")

    wide = [(a, b) for a, b in FREE_GAPS if b - a >= CALM_MIN]
    print(f"    ⚠️ PLAFOND THEORIQUE : les 30 marqueurs occupent "
          f"{SHIP_LENGTH - sum(b - a for a, b in FREE_GAPS):.1f} m d'emprises "
          f"fusionnees, ils laissent {sum(b - a for a, b in FREE_GAPS):.1f} m en "
          f"{len(FREE_GAPS)} plages dont {len(wide)} de {CALM_MIN:.0f} m ou plus.")
    print(f"    La forge ne peut pas faire mieux sans deplacer un marqueur : "
          "elle atteint ce plafond exactement.")
    print("    les cinq plus larges : " + ", ".join(
        f"s {a:.0f}-{b:.0f} ({b - a:.0f} m)"
        for a, b in sorted(FREE_GAPS, key=lambda g: g[0] - g[1])[:5]))

    lit = sum(c["artere_allumee"] for c in report["counts"])
    print(f"\n  ARTERE — canal de {2 * CANAL_HALF:.2f} m enfonce de "
          f"{CANAL_RIM_Y - CANAL_FLOOR_Y:.2f} m sous son rebord et de "
          f"{-4.26 - CANAL_FLOOR_Y:.2f} m sous le pont")
    print(f"    {len(CONDUIT_LANES) * 2} bandes de "
          f"{100 * (CONDUIT_LANES[0][1] - CONDUIT_LANES[0][0]):.0f} et "
          f"{100 * (CONDUIT_LANES[1][1] - CONDUIT_LANES[1][0]):.0f} cm, soit "
          f"{2 * sum(b - a for a, b in CONDUIT_LANES):.2f} m eclaires sur "
          f"{2 * CANAL_HALF:.2f} m de canal "
          f"({100 * sum(b - a for a, b in CONDUIT_LANES) / CANAL_HALF:.0f} pct "
          "de sa largeur)")
    print(f"    longueur cumulee allumee {lit:.0f} m pour "
          f"{len(CONDUIT_LANES) * 2 * SHIP_LENGTH:.0f} m de voies possibles "
          f"({100 * lit / (len(CONDUIT_LANES) * 2 * SHIP_LENGTH):.0f} pct) — "
          "le reste est coupe")
    print(f"    {sum(c['travees'] for c in report['counts'])} travees sombres "
          f"({BRACE_WIDTH:.2f} m, enterrees de {BRACE_SINK:.2f} m) barrent la "
          "tranchee")

    # --- LES BRANCHES (BRIEF-0103) -----------------------------------------
    # ⚠️ TROIS COLONNES ET PAS UNE : le trace (ce que la forge a voulu), la
    # veine relevee sur le BINAIRE (ce que Godot chargera) et le troncon qui la
    # porte (ce que `CortegeSkin` eteindra). Les trois doivent dire la meme
    # chose ; c'est quand elles divergent qu'une branche reste allumee sur un
    # vaisseau mort.
    served = [r for r in report["branch_routes"] if r["reason"] is None]
    px_lat = 1920.0 / _frame_coverage(-4.30)["frame_width"]
    px_depth = px_lat * 0.940                 # sin(70 deg) : le regard plonge
    print(f"\n  BRANCHES (BRIEF-0103) — {len(served)} affuts desservis sur "
          f"{len(TURRETS)} ; la veine est en 'AA_Emissive_Engine' et RIEN "
          "d'autre ne l'est\n"
          f"  a la camera du jeu : {px_lat:.1f} px/m en lateral, "
          f"{px_depth:.1f} px/m en profondeur (1920 px pour "
          f"{_frame_coverage(-4.30)['frame_width']:.2f} m de cadre)\n"
          f"    veine standard {BRANCH_VEIN_W:.2f} m -> "
          f"{BRANCH_VEIN_W * px_depth:.1f} px | "
          f"veine lourde {BRANCH_VEIN_W_HEAVY:.2f} m -> "
          f"{BRANCH_VEIN_W_HEAVY * px_depth:.1f} px | "
          f"gaine {BRANCH_TROUGH_W:.2f}/{BRANCH_TROUGH_W_HEAVY:.2f} m -> "
          f"{BRANCH_TROUGH_W * px_depth:.1f}/"
          f"{BRANCH_TROUGH_W_HEAVY * px_depth:.1f} px")
    print(f"    {'affut':<10} {'classe':>8} {'x table':>8} {'x .glb':>8} "
          f"{'du x':>6} {'au x':>6} {'long':>6} {'veine':>6} "
          f"{'tri':>5} {'m2 releve':>10}  troncon")
    for route in report["branch_routes"]:
        tris, area, owner = report["branch_vein"][route["name"]]
        if route["reason"] is not None:
            print(f"    {route['name']:<10} {'—':>8} "
                  f"{route['table_x']:8.2f} {route['marker_x']:8.2f} "
                  f"{'NON DESSERVI':>44}  {route['reason']}")
            continue
        print(f"    {route['name']:<10} "
              f"{'LOURDE' if route['heavy'] else 'standard':>8} "
              f"{route['table_x']:8.2f} {route['marker_x']:8.2f} "
              f"{route['side'] * route['x_in']:6.2f} "
              f"{route['side'] * route['x_out']:6.2f} "
              f"{route['length']:6.2f} {route['vein']:6.2f} "
              f"{tris:5d} {area:10.3f}  {owner}")
    print(f"    {'':<10} par troncon (releve sur le .glb) : " + " ".join(
        f"S{n}={sum(1 for r in served if int(r['station'] // SECTION_LENGTH) == n - 1)}"
        for n in range(1, SECTION_COUNT + 1)))
    print("    emissif TOTAL par troncon (tous usages : conduits, pastilles, "
          "veines de branche)")
    for n in range(1, SECTION_COUNT + 1):
        name = f"Section_{n:02d}"
        tris, area = report["emissive_by_section"].get(name, (0, 0.0))
        vein_tris = sum(report["branch_vein"][r["name"]][0] for r in served
                        if int(r["station"] // SECTION_LENGTH) == n - 1)
        vein_area = sum(report["branch_vein"][r["name"]][1] for r in served
                        if int(r["station"] // SECTION_LENGTH) == n - 1)
        print(f"      {name}  {tris:5d} triangles / {area:8.2f} m2  dont "
              f"branches {vein_tris:4d} / {vein_area:6.2f} m2")

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
    print(f"\n  repartition en AIRE des {len(report['materials'])} materiaux "
          "assignes (relevee sur le .glb)")
    print("  ⚠️ deux colonnes, et c'est la seconde qui parle de l'ECRAN : l'aire "
          "TOTALE\n     d'une coque de 500 m est aux deux tiers son ventre, que "
          "la camera du jeu\n     (70 deg de plongee) ne voit jamais. La cible "
          "80/15/5 du brief decrit des pixels.")
    total = report["total_area"] or 1.0
    seen_total = report["total_seen"] or 1.0
    print(f"    {'materiau':<20} {'aire totale':>12} {'':>7}   "
          f"{'aire VUE':>10} {'':>7}")
    for name, area in sorted(report["area_by_material"].items(),
                             key=lambda kv: -kv[1]):
        seen = report["seen_by_material"].get(name, 0.0)
        flag = "   <- propre a Ambry" if name == AMBRY_HULL else ""
        print(f"    {name:<20} {area:9.1f} m2 {100.0 * area / total:6.2f} %   "
              f"{seen:7.1f} m2 {100.0 * seen / seen_total:6.2f} %{flag}")
    print(f"    {'TOTAL':<20} {total:9.1f} m2            "
          f"{seen_total:7.1f} m2")
    structure = sum(report["seen_by_material"].get(n, 0.0)
                    for n in ("AA_Hull", "AA_Hull_Ambry"))
    gear = sum(report["seen_by_material"].get(n, 0.0)
               for n in ("AA_Greeble", "AA_Trim", "AA_Glass", "AA_Marking_Red"))
    accent = sum(report["seen_by_material"].get(n, 0.0)
                 for n in ("AA_Panel", "AA_Emissive_Engine"))
    print(f"\n  contre la cible 80 / 15 / 5 du brief, sur l'aire VUE :")
    print(f"    structure  (AA_Hull + Ambry)              "
          f"{100.0 * structure / seen_total:6.2f} %   cible 80")
    print(f"    appareillage (AA_Greeble/Trim/Glass/Rouge) "
          f"{100.0 * gear / seen_total:6.2f} %   cible 15")
    print(f"    violet + magenta (AA_Panel + emissif)     "
          f"{100.0 * accent / seen_total:6.2f} %   cible  5  (cliquet 9)")
    print(f"  emissif seul : {100.0 * report['emissive_ratio']:.2f} % de l'aire "
          "totale, "
          f"{100.0 * report['seen_by_material'].get('AA_Emissive_Engine', 0.0) / seen_total:.2f} "
          "% de l'aire vue")
    print(f"  octets     : {report['bytes']}")

    print("\n  ouvertures de pont d'envol (BRIEF-0091) — "
          f"{2 * BAY_HALF_X:.2f} x {2 * BAY_HALF_S:.2f} m, puits de "
          f"{BAY_WELL_DEPTH:.2f} m tenu par bay_kit.glb")
    for name, bs, bx, mouth, low in report["bays"]:
        print(f"    {name}  s {bs:6.1f}  x {bx:+6.2f}  bouche Y {mouth:+7.4f}  "
              f"pourtour bas {low:+7.4f} (denivele {mouth - low:4.2f} m)  "
              f"fond {mouth - BAY_WELL_DEPTH:+7.3f}  "
              f"coaming {mouth + 0.60:+7.3f} (plafond {CEILING_Y:+.2f})")

    print("\n  nœuds d'epine (BRIEF-0094) — le marqueur porte le plan d'assise "
          "DANS le canal ;\n  spine_kit.glb y est modelise, la coque n'en cuit "
          "plus aucun")
    for name, seat, low, rim in report["spine_seats"]:
        print(f"    {name}  assise Y {seat:+7.4f}  bas d'emprise {low:+7.4f} "
              f"(denivele {seat - low:4.3f} m)  rebord {rim:+7.4f} "
              f"(tranchee {rim - seat:4.2f} m)")

    # ⚠️ Les cinq paires les plus SERREES, imprimees a chaque build meme quand
    # tout va bien. Un garde-fou qui ne parle que le jour ou il echoue ne dit
    # jamais de combien on est passe pres — et c'est cette marge-la qui a manque
    # pendant six semaines.
    print("\n  marges socle / pont d'envol (les 5 paires les plus serrees ; "
          f"coaming du kit {BAY_COAMING_W:.2f} m)")
    declared = {(t, b): why for t, b, why in ACCEPTED_PAD_BAY_PROXIMITY}
    for turret, bay, mouth_gap, coam_gap, _ in sorted(
            report["pad_clearances"], key=lambda row: row[3])[:5]:
        note = ""
        if (turret, bay) in declared:
            note = "   <- PROXIMITE ACCEPTEE : " + declared[(turret, bay)]
        print(f"    {turret} / {bay} : {mouth_gap:+6.2f} m de l'ouverture, "
              f"{coam_gap:+6.2f} m du coaming{note}")

    # ⚠️ MESURE, PAS INTENTION (BRIEF-0101). Le tableau ci-dessous est releve sur
    # le `.glb` : hauteur du maillage dans le disque de 2,50 m autour de chaque
    # marqueur, comparee a l'assise. La colonne « module » doit rester NEGATIVE —
    # c'est le degagement reel sous le socle. La colonne « peau » peut etre
    # legerement positive : l'assise est le point haut de l'emprise du KIT
    # (2,08 m), et au-dela la coque elle-meme remonte un peu ; elle n'est pas un
    # module, elle ne se deplace pas. La derniere colonne dit que le borde n'est
    # pas redevenu plat : un disque a zero sommet serait une tourelle sur une
    # dalle nue.
    print(f"\n  degagement des affuts — disque de {TURRET_KEEPOUT_R:.2f} m "
          "(emprise de la classe LOURDE, echelle 1,200), releve sur le .glb")
    print(f"    {'marqueur':<12} {'module / assise':>16} {'peau / assise':>15} "
          f"{'sommets dans le disque':>24}")
    for name, module, skin, seen in report["turret_clearances"]:
        top = "aucun module" if module == -math.inf else f"{module:+.4f} m"
        print(f"    {name:<12} {top:>16} {skin:+14.4f} m {seen:>24}")

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
    plant = report["counts"][-1].get("complexe_stats")
    if plant:
        print(f"\n  COMPLEXE INDUSTRIEL (BRIEF-0111) : "
              f"{report['counts'][-1]['complexe']} triangles, "
              f"{plant['conduites']} reperes de conduite, "
              f"{plant.get('cuves', 0)} cuves, {plant.get('plots', 0)} plots de "
              f"rive, {plant.get('traverses', 0)} traverses, "
              f"{plant.get('passerelles', 0)} passerelles, "
              f"{plant.get('caisses', 0)} caisses")
        print(f"    emprise s {plant['emprise'][0][0]:.1f} a "
              f"{plant['emprise'][0][1]:.1f} ({plant['emprise'][0][1] - plant['emprise'][0][0]:.1f} m), "
              f"x NOMINAL {plant['emprise'][1][0]:.2f} a {plant['emprise'][1][1]:.2f} "
              f"(absolu {_pl(PLANT_S[0], PLANT_XN[0]):.2f} a "
              f"{_pl(PLANT_S[0], PLANT_XN[1]):.2f} au large, "
              f"{_pl(434.0, PLANT_XN[0]):.2f} a {_pl(434.0, PLANT_XN[1]):.2f} au "
              f"pincement de s = 434)")
        print(f"    sommet {plant['top']:+.3f}, ciel restant {plant['ciel']:.3f} m "
              f"sous le plafond de construction {BUILD_CEILING_Y:+.2f} "
              f"(plafond de vol {CEILING_Y:+.2f})")
        for number, (cs, cx) in enumerate(PLANT_CONDUITS, start=1):
            seat = next(a for n, a in plant["sieges"] if n == number)
            print(f"    CTRL | Complexe {number:02d}  s {cs:7.1f}  x {cx:+6.2f}  "
                  f"bas {seat:+.4f}  (peau {_surface_y(cs, cx):+.4f}, "
                  f"berceau +{seat - _surface_y(cs, cx):.3f}, coudee jusqu'a "
                  f"{seat + CONDUIT_PIECE_TOP:+.3f})")
        basin = BASINS[0]
        floor = min(_surface_y(v, BASIN_X[k])
                    for v in (basin[0] - basin[1], basin[0], basin[0] + basin[1])
                    for k in (0, 1)) - PIT_DEPTH
        print(f"    bassin : s {basin[0] - basin[1]:.1f} a {basin[0] + basin[1]:.1f}, "
              f"x nominal {BASIN_X[0]:.2f} a {BASIN_X[1]:.2f}, fond {floor:+.2f} "
              f"({-4.99 - floor:.2f} m sous le pont median)")

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
    if "--branches" in sys.argv:
        render_branch_plate(report)
    if "--nodes" in sys.argv:
        render_node_plate(report)
    if "--complexe" in sys.argv:
        render_plant_plate(report)


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
                       f"= {report['triangles'] / (SHIP_LENGTH * 28.0):.1f} tri/m2 "
                       f"— les 7 ponts d'envol sont des TROUS dans la peau ; le "
                       f"hangar qui les borde vit dans bay_kit.glb",
               -0.96, -0.90, 0.030, TILE_W, height, (0.72, 0.84, 1.0))
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
                   f"{counts['marqueurs_tourelle']} marqueur(s) de tourelle · "
                   f"{counts['baies']} pont(s) d'envol — la coque ne cuit plus ni "
                   f"socle ni hangar : bay_kit.glb et turret_kit.glb",
           -0.985, -0.86, 0.052, TILE_W, TOP_H)
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


def _compose(tiles: list[tuple[str, int]], out: str,
             width: int = TILE_W) -> None:
    """Empile les vignettes. Pas de PIL dans le Python de Blender : numpy."""
    import numpy as np

    height = sum(h for _, h in tiles)
    sheet = np.zeros((height, width, 4), dtype=np.float32)
    sheet[..., 3] = 1.0
    cursor = 0
    for path, tile_h in tiles:
        image = bpy.data.images.load(path)
        buffer = np.empty(len(image.pixels), dtype=np.float32)
        image.pixels.foreach_get(buffer)
        tile = buffer.reshape(tile_h, width, 4)
        # Les images Blender sont stockees de bas en haut : ligne 0 = bas.
        top = height - cursor - tile_h
        sheet[top:top + tile_h] = tile
        cursor += tile_h
        bpy.data.images.remove(image)
    result = bpy.data.images.new("sheet", width=width, height=height)
    result.pixels.foreach_set(sheet.reshape(-1))
    result.filepath_raw = out
    result.file_format = "PNG"
    result.save()
    bpy.data.images.remove(result)
    print(f"-> {out}  ({width} x {height})")


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


# ==========================================================================
# Planche des branches — `--branches` (BRIEF-0103)
# ==========================================================================
# ⚠️ UNE BRANCHE SE JUGE A LA CAMERA DU JEU, PAS SUR UNE VUE DE DESSUS, ET CE
# N'EST PAS UN PRINCIPE : c'est une lecon payee deux fois le 2026-09-06. De
# dessus, en orthographique, un ruban de 22 cm est un ruban de 22 cm ; a l'ecran,
# c'est neuf pixels et demi, et neuf pixels et demi peuvent tres bien ne pas
# exister. La planche rend donc a 1920 x 1080 — la resolution du jeu — et non aux
# 1440 de la planche de sections : ce qu'on regarde est ce que le joueur verra.
#
# ⚠️ ET ELLE REND L'ETAT ETEINT, QUE PERSONNE NE PENSE A REGARDER. C'est
# pourtant celui que le joueur verra apres avoir abattu un nœud, et le lot rate
# son but si la branche DISPARAIT une fois eteinte : il faut lire « ce circuit
# est mort », pas « il n'y a rien ici ». Le facteur applique est celui du moteur
# — `CortegeSkin.EMISSIVE_DEAD / EMISSIVE_ENERGY` = 0,06 / 0,45 — recopie ici
# avec sa source, parce que la forge ne lit pas le code du jeu.
BRANCH_PLATE = os.path.join(_REPO, "docs/forge/output/BRIEF-0103-planche-branches.png")
BRANCH_TILE_W = 1920
BRANCH_TILE_H = 1080
#: LES DEUX REGLAGES DU MOTEUR, ET IL FAUT LES DEUX.
#: ⚠️ LA PREMIERE PLANCHE MENTAIT, ET DANS LE SENS FLATTEUR. Elle rendait le
#: `.glb` tel quel — l'emissif y sort a 1,735 en force — puis multipliait cette
#: valeur par le rapport mort/vif. Or le moteur ne multiplie pas : il ECRASE.
#: `CortegeSkin._skin_emissive()` POSE `emission_energy_multiplier = 0,45`, et
#: l'extinction POSE 0,06. Le vif du jeu est donc 3,9 fois plus sobre que celui
#: du `.glb` brut, et l'ecart vif/mort est de 7,5 — pas de 1,1 comme la premiere
#: mesure le donnait. Rendre le `.glb` brut, c'etait juger une veine que
#: personne ne verra jamais.
EMISSIVE_ENERGY_LIT = 0.45
EMISSIVE_ENERGY_DEAD = 0.06

#: ⚠️ LA CARTE DE L'OPERATEUR, POUR LE SEUL RENDU. Elle n'entre dans aucun
#: `.glb` (`ADR-0028` : la forge ne livre pas de texture) ; elle est LUE ici
#: parce que sans elle la planche ment sur l'etat eteint. `CortegeSkin` pose
#: `cortege_emissive` en ALBEDO *et* en emission ; cette image est sombre
#: (moyenne 0,22), quand le facteur du `.glb` est un magenta plein a 0,69. Rendre
#: la couleur unie donnerait une veine quatre fois trop claire ALLUMEE et une
#: veine encore magenta ETEINTE — c'est-a-dire aucun ecart a regarder, alors que
#: le jeu en montre un franc. Le fichier absent est un cas normal : on rend a
#: plat et la legende le dit.
CORTEGE_EMISSIVE_MAP = os.path.join(
    _REPO, "assets/imported/textures/cortege/cortege_emissive.png")
#: `CortegeSkin.HULL_UV_SCALE` — `uv1_scale` MULTIPLIE les UV : 0,5 fait couvrir
#: deux fois plus de monde a la meme image (0,100 tuile/m au lieu de 0,200).
CORTEGE_UV_SCALE = 0.5

TURRET_KIT = os.path.join(_REPO, "assets/imported/models/backgrounds/turret_kit.glb")
SPINE_KIT = os.path.join(_REPO, "assets/imported/models/backgrounds/spine_kit.glb")

#: L'assemblage de `cortege_turret.gd`, recopie ici pour la seule planche.
#: ⚠️ AUCUNE DE CES COTES NE PART DANS LE `.glb` : elles servent a REGARDER la
#: branche avec la piece qu'elle alimente, et rien d'autre. Le jour ou le moteur
#: change son assemblage, la planche vieillit — la coque, elle, ne bouge pas.
KIT_RING_LIFT = 0.04
KIT_BODY_LIFT = 0.40
KIT_BARREL_LIFT = 0.98
KIT_BARREL_SEAT_Z = 0.70
KIT_SERVICE_RADIUS = 1.66
KIT_SERVICE_LIFT = 0.20
KIT_HEAVY_SCALE = 1.200
KIT_FAMILIES = (
    (False, "turret_barrel_short", 0.80, (128.0,), -1.0),
    (True, "turret_barrel", 0.92, (118.0, -118.0), 180.0),
    (True, "turret_barrel", 1.00, (96.0, -142.0), 205.0),
)


def _kit_sources(path: str) -> dict:
    """Importe un kit UNE fois et rend ses maillages par nom, hors camera."""
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    fresh = [o for o in bpy.context.scene.objects if o not in before]
    out: dict = {}
    for obj in fresh:
        if obj.type == "MESH":
            out[obj.name.split(".")[0]] = obj
        obj.hide_render = True
    return out


def _kit_piece(sources: dict, part: str, position: Vector, yaw: float,
               scale: float) -> None:
    """Une copie d'une piece de kit, posee en coordonnees GODOT."""
    source = sources.get(part)
    if source is None:
        print(f"  ⚠️ piece de kit absente : {part}")
        return
    piece = bpy.data.objects.new(part, source.data)
    piece.location = _to_blender(position)
    piece.rotation_euler = Euler((0.0, 0.0, yaw), "XYZ")
    piece.scale = Vector((scale, scale, scale))
    piece.visible_shadow = False
    bpy.context.collection.objects.link(piece)


def _mount_turret(sources: dict, number: int, base: Vector, heavy: bool) -> None:
    """L'affut complet sur son marqueur — socle, appareillage, couronne, tubes.

    ⚠️ LA FAMILLE EST APPROCHEE, ET C'EST DECLARE. Le moteur la tire de
    `(serial + section) % 3` ; la forge n'a ni l'un ni l'autre. On prend
    `(numero + troncon) % 3`, qui donne la meme VARIETE sans pretendre a la meme
    repartition — une planche sert a juger une branche sous un affut, pas a
    valider l'assemblage du moteur, qui a son propre harnais.
    """
    section = int(base.z // -SECTION_LENGTH) + 1
    family = KIT_FAMILIES[(number + section) % len(KIT_FAMILIES)]
    k = KIT_HEAVY_SCALE if heavy else 1.0
    _kit_piece(sources, "turret_pad", base, 0.0, k)
    if family[0]:
        _kit_piece(sources, "turret_anchor_skirt", base, 0.0, k)
    angles = list(family[3]) + ([family[4]] if family[4] >= 0.0 else [])
    parts = ["turret_service_box"] * len(family[3])
    parts += ["turret_pipe"] if family[4] >= 0.0 else []
    for part, degrees in zip(parts, angles):
        a = math.radians(degrees)
        _kit_piece(sources, part,
                   base + Vector((math.cos(a) * KIT_SERVICE_RADIUS * k,
                                  KIT_SERVICE_LIFT * k,
                                  math.sin(a) * KIT_SERVICE_RADIUS * k)),
                   -a, k)
    _kit_piece(sources, "turret_ring",
               base + Vector((0.0, KIT_RING_LIFT * k, 0.0)), 0.0, k)
    _kit_piece(sources, "turret_body",
               base + Vector((0.0, KIT_BODY_LIFT * k, 0.0)), 0.0, k)
    for side in (-1.0, 1.0):
        _kit_piece(sources, str(family[1]),
                   base + Vector((side * family[2] * 0.5 * k,
                                  KIT_BARREL_LIFT * k,
                                  KIT_BARREL_SEAT_Z * k)), 0.0, k)


def _set_emissive_energy(objects: list, energy: float) -> int:
    """Pose l'energie d'emission du slot `AA_Emissive_Engine` — et de lui SEUL.

    ⚠️ C'EST EXACTEMENT CE QUE FAIT LE MOTEUR, ET C'EST LA TOUT L'ENJEU DU LOT.
    `CortegeSkin` reconnait ce nom, duplique le materiau PAR MAILLAGE et pose
    l'energie de la copie du troncon dont le nœud est tombe. Si une veine etait
    peinte ailleurs, cette fonction ne la trouverait pas — et la planche eteinte
    montrerait une branche encore allumee. C'est le controle le plus direct qu'on
    puisse faire de la promesse du brief : on le fait EN REGARDANT.

    ⚠️ ON POSE, ON NE MULTIPLIE PAS — voir `EMISSIVE_ENERGY_LIT`. Rendre le
    `.glb` brut donnerait une veine quatre fois plus vive que celle du jeu, donc
    une planche qui valide ce que personne ne verra.

    ⚠️ ET L'ALBEDO RESTE CELUI DU `.glb`. En jeu, `cortege_emissive` le remplace
    (la meme image sert d'albedo et d'emission, regle 2 du contrat de texture) :
    la planche montre donc la veine SANS sa carte, c'est-a-dire dans son etat le
    plus plat. C'est une approximation, et elle va dans le sens severe.
    """
    image = None
    if os.path.exists(CORTEGE_EMISSIVE_MAP):
        image = bpy.data.images.load(CORTEGE_EMISSIVE_MAP, check_existing=True)
    touched = 0
    seen: set = set()
    for obj in objects:
        if obj.type != "MESH":
            continue
        for slot in obj.data.materials:
            if slot is None or not slot.name.startswith("AA_Emissive_Engine"):
                continue
            if slot.name in seen:
                continue
            seen.add(slot.name)
            for node in slot.node_tree.nodes:
                if "Emission Strength" not in getattr(node, "inputs", {}):
                    continue
                node.inputs["Emission Strength"].default_value = energy
                touched += 1
                if image is None:
                    continue
                tree = slot.node_tree
                coord = tree.nodes.new("ShaderNodeTexCoord")
                mapping = tree.nodes.new("ShaderNodeMapping")
                mapping.inputs["Scale"].default_value = (
                    CORTEGE_UV_SCALE, CORTEGE_UV_SCALE, 1.0)
                tex = tree.nodes.new("ShaderNodeTexImage")
                tex.image = image
                tree.links.new(coord.outputs["UV"], mapping.inputs["Vector"])
                tree.links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
                tree.links.new(tex.outputs["Color"], node.inputs["Base Color"])
                tree.links.new(tex.outputs["Color"],
                               node.inputs["Emission Color"])
    return touched


def _tile_branches(path: str, report: dict, centre: float, dead: bool,
                   caption: str) -> None:
    """La perspective du jeu sur deux branches, affuts REELS montes dessus."""
    _plate_reset()
    decor = _import(OUTPUT, "Decor", Vector((0.0, 0.0, centre)))
    turret_src = _kit_sources(TURRET_KIT)
    spine_src = _kit_sources(SPINE_KIT)
    mounted: list[str] = []
    for route in report["branch_routes"]:
        ts = route["station"]
        if abs(ts - centre) > 22.0:
            continue
        seat, _low = turret_seat_y(ts, route["marker_x"])
        _mount_turret(turret_src, route["number"],
                      Vector((route["marker_x"], seat, -(ts - centre))),
                      route["heavy"])
        mounted.append(f"{route['name']}{' LOURDE' if route['heavy'] else ''}")
    for number, s in enumerate(SPINES, start=1):
        if abs(s - centre) > 22.0:
            continue
        seat, _low = spine_seat_y(s)
        base = Vector((0.0, seat, -(s - centre)))
        for part in ("spine_cradle", "spine_core"):
            _kit_piece(spine_src, part, base, 0.0, 1.0)
        for side in (-1.0, 1.0):
            _kit_piece(spine_src, "spine_brace",
                       base + Vector((side * 0.52, 0.0, 0.0)),
                       0.0 if side > 0 else math.pi, 1.0)
    fighter = _import(FIGHTER, "Player", Vector((0.0, 0.0, 3.4)))
    # ⚠️ LE DECOR SEUL, DANS LES DEUX ETATS. Un nœud abattu AFFAIBLIT les
    # tourelles du troncon suivant, il ne les tue pas : leur œil reste allume, et
    # c'est ce contraste — la conduite morte sous une tourelle vivante — qui dit
    # au joueur ce que son tir a fait.
    energy = EMISSIVE_ENERGY_DEAD if dead else EMISSIVE_ENERGY_LIT
    touched = _set_emissive_energy(decor, energy)
    print(f"  [branches] {'ETEINT' if dead else 'ALIMENTE'} : "
          f"{touched} materiau(x) emissif(s) a {energy:.2f} "
          f"(reglage de CortegeSkin), carte "
          f"{'cortege_emissive' if os.path.exists(CORTEGE_EMISSIVE_MAP) else 'ABSENTE'}")
    _plate_lights()
    camera = _plate_camera("game", _to_blender(CAM_POS), _to_blender(CAM_FORWARD),
                           _to_blender(CAM_UP), CAM_FOV_V)
    px = BRANCH_TILE_W / _frame_coverage(-4.30)["frame_width"]
    tint = (1.0, 0.62, 0.55) if dead else (1.0, 0.88, 0.55)
    _label(camera, caption, -0.96, 0.90, 0.026, BRANCH_TILE_W, BRANCH_TILE_H, tint)
    _label(camera, "  ·  ".join(mounted) + "  —  affuts REELS de turret_kit.glb",
           -0.96, 0.84, 0.026, BRANCH_TILE_W, BRANCH_TILE_H)
    _label(camera,
           f"veine {BRANCH_VEIN_W:.2f} m = {BRANCH_VEIN_W * px * 0.940:.1f} px  ·  "
           f"veine lourde {BRANCH_VEIN_W_HEAVY:.2f} m = "
           f"{BRANCH_VEIN_W_HEAVY * px * 0.940:.1f} px  ·  "
           f"gaine {BRANCH_TROUGH_W:.2f}/{BRANCH_TROUGH_W_HEAVY:.2f} m = "
           f"{BRANCH_TROUGH_W * px * 0.940:.1f}/"
           f"{BRANCH_TROUGH_W_HEAVY * px * 0.940:.1f} px "
           f"({px:.1f} px/m lateral, x sin 70 deg en profondeur)",
           -0.96, -0.88, 0.024, BRANCH_TILE_W, BRANCH_TILE_H, (0.72, 0.84, 1.0))
    _label(camera,
           f"veine en AA_Emissive_Engine a {EMISSIVE_ENERGY_LIT:.2f} "
           "(CortegeSkin.EMISSIVE_ENERGY) — le seul slot que le moteur eteint"
           if not dead else
           f"ETEINTE : AA_Emissive_Engine du troncon a {EMISSIVE_ENERGY_DEAD:.2f} "
           "(CortegeSkin.EMISSIVE_DEAD) — la veine doit rester LISIBLE",
           -0.96, -0.94, 0.024, BRANCH_TILE_W, BRANCH_TILE_H,
           (0.72, 0.84, 1.0) if not dead else (1.0, 0.62, 0.55))
    _render(path, BRANCH_TILE_W, BRANCH_TILE_H)


#: Les deux stations regardees, et pourquoi.
#: ⚠️ ELLES NE SONT PAS PRISES AU HASARD : chacune met une LOURDE et une
#: STANDARD dans le meme cadre, ce qui est la seule facon de juger la hierarchie
#: de largeur que le brief demande. La seconde porte en plus `Spine_03`, donc le
#: nœud, le canal et deux branches d'un seul regard.
BRANCH_VIEWS = (
    (377.5, "CAMERA DU JEU, s 377 — Turret_12 LOURDE (pont interieur, en haut) "
            "et Turret_11 standard (pont median, en bas)"),
    (260.8, "CAMERA DU JEU, s 261 — Spine_03 dans le canal, Turret_08 LOURDE "
            "(en haut) et Turret_07 standard (en bas)"),
)


def render_branch_plate(report: dict) -> None:
    staging = tempfile.mkdtemp(prefix="aegis-cortege-branches-")
    tiles: list[tuple[str, int]] = []
    try:
        for index, (centre, caption) in enumerate(BRANCH_VIEWS):
            for dead in (False, True):
                path = os.path.join(
                    staging, f"branch{index}{'_dead' if dead else '_lit'}.png")
                _tile_branches(path, report, centre, dead,
                               caption + ("  ·  NŒUD ABATTU"
                                          if dead else "  ·  ALIMENTE"))
                tiles.append((path, BRANCH_TILE_H))
        os.makedirs(os.path.dirname(BRANCH_PLATE), exist_ok=True)
        _compose(tiles, BRANCH_PLATE, width=BRANCH_TILE_W)
    finally:
        for leftover in os.listdir(staging):
            os.remove(os.path.join(staging, leftover))
        os.rmdir(staging)


# ==========================================================================
# Planche des nœuds en tete de troncon — `--nodes` (BRIEF-0104)
# ==========================================================================
# ⚠️ CE QUE CETTE PLANCHE PROUVE NE SE VOIT SUR AUCUNE VUE DE DESSUS. La question
# du lot n'est pas « ou est le nœud sur les 500 m » — un plan y repond — c'est
# « le joueur le voit-il DANS LE CADRE au moment ou il franchit la frontiere du
# troncon ». Ca ne se lit qu'a la camera du jeu, au FOV du jeu, avec le chasseur
# pose a sa place : le cadre ne couvre que 26 m de pont, et 26 m sur 500 sont
# exactement ce qui separe une mecanique lisible d'une mecanique invisible.
#
# ⚠️ ET ELLE ETEINT LE TRONCON DU NŒUD, PAS TOUTE LA COQUE. `weakened_section()`
# rend desormais `section_index` : le nœud abattu eteint LE SIEN. A l'entree d'un
# troncon, les deux etats sont donc dans le meme cadre — le couloir devant soi
# mort, le troncon precedent encore vif sous la frontiere. C'est la demande de
# l'operateur mot pour mot, et une extinction globale l'aurait masquee.
NODE_PLATE = os.path.join(_REPO, "docs/forge/output/BRIEF-0104-planche-noeuds.png")
NODE_TILE_W = 1920
NODE_TILE_H = 1080
#: Position du chasseur dans le cadre, recopiee de la planche des branches.
NODE_PLAYER_Z = 3.4
#: L'assemblage de `cortege_spine_node.gd`, recopie ici pour la seule planche
#: (comme `KIT_*` pour les affuts). ⚠️ Aucune de ces cotes ne part dans le `.glb`.
SPINE_CORE_LIFT = 0.21
SPINE_BRACE_LIFT = 0.30
SPINE_BRACE_GAUGE = 0.50
SPINE_BRACE_SPREAD = 0.78
SPINE_BRACE_COUNT = (2, 4)

#: Les trois vues, et pourquoi celles-la. (troncon, station du chasseur, titre)
#: ⚠️ LE CHASSEUR EST POSE SUR LA FRONTIERE, PAS « VERS LE DEBUT ». C'est la seule
#: pose qui reponde a la question : si le nœud n'etait pas dans ce cadre-la, il
#: serait deja trop tard quand il y entrerait.
NODE_VIEWS = (
    (2, 100.0, "ENTREE DU TRONCON 2 — le chasseur est EXACTEMENT sur la "
               "frontiere s = 100"),
    (4, 300.0, "ENTREE DU TRONCON 4 — le chasseur est EXACTEMENT sur la "
               "frontiere s = 300 (nœud repousse a +5 par la fosse de s = 292)"),
    # ⚠️ LE CHASSEUR EST A s = 36, ET C'EST UNE CORRECTION MESUREE. Pose a 39, sa
    # silhouette recouvre le pont de s = 38 a 41,5 — donc exactement le debut de
    # l'artere que cette vue doit montrer. Un cadrage qui cache sa propre preuve
    # ne prouve rien ; a 36, les 41,1 m sortent de derriere l'aile.
    # ⚠️ ET LE TITRE TIENT DANS LE CADRE : a 0,024 de hauteur, la legende passe
    # ~170 caracteres sur 1920 px. Au-dela elle est COUPEE au bord droit, sans
    # que rien ne le signale — la premiere version de cette vue y a perdu ses
    # deux derniers chiffres.
    (1, 36.0, "TRONCON 1 — le fuseau de proue interdit mieux que +46, et la "
              "voie EXTERNE ne s'allume qu'a s = 41,1 (l'interne des s = 27,3)"),
)


def _visible_deck_span(centre: float, deck_y: float = -4.30) -> tuple[float, float]:
    """(s le plus proche, s le plus lointain) que la camera du jeu montre du pont.

    Mesure et non estimation : les deux rayons de bord de cadre sont intersectes
    avec le plan du pont. C'est ce nombre — 26 m sur 500 — qui dit si un
    marqueur est visible a un instant donne.
    """
    out: list[float] = []
    tan_v = math.tan(CAM_FOV_V * 0.5)
    for sign in (+1.0, -1.0):
        ray = (CAM_FORWARD + CAM_UP * (sign * tan_v)).normalized()
        t = (CAM_POS.y - deck_y) / -ray.y
        out.append(centre - (CAM_POS.z + ray.z * t))
    return min(out), max(out)


def _screen_v(point: Vector) -> float:
    """Hauteur d'ecran d'un point, en fraction : -1 = bas du cadre, +1 = haut."""
    rel = point - CAM_POS
    forward = rel.dot(CAM_FORWARD)
    if forward <= 0.0:
        return math.nan
    return (rel.dot(CAM_UP) / forward) / math.tan(CAM_FOV_V * 0.5)


def _mount_spine(sources: dict, number: int, base: Vector, dead: bool) -> None:
    """Le nœud complet sur son marqueur — berceau, entretoises, et le cœur.

    ⚠️ LE CŒUR DISPARAIT QUAND LE NŒUD TOMBE, LE BERCEAU RESTE : c'est
    `_take_damage()` de `cortege_spine_node.gd`, et c'est ce qui distingue a
    l'ecran un nœud abattu d'un nœud jamais touche. Une planche qui garderait le
    cœur allume ou eteint mentirait dans les deux sens.
    """
    _kit_piece(sources, "spine_cradle", base, 0.0, 1.0)
    if not dead:
        _kit_piece(sources, "spine_core",
                   base + Vector((0.0, SPINE_CORE_LIFT, 0.0)), 0.0, 1.0)
    braces = SPINE_BRACE_COUNT[number % len(SPINE_BRACE_COUNT)]
    offsets = (0.0,) if braces == 2 else (-SPINE_BRACE_SPREAD, SPINE_BRACE_SPREAD)
    for side in (-1.0, 1.0):
        for offset in offsets:
            _kit_piece(sources, "spine_brace",
                       base + Vector((side * SPINE_BRACE_GAUGE,
                                      SPINE_BRACE_LIFT, offset)),
                       0.0 if side > 0.0 else math.pi, 1.0)


def _extinguish_section(decor: list, section: int) -> int:
    """Eteint `AA_Emissive_Engine` du SEUL troncon `section`, comme le moteur.

    `CortegeSkin` duplique le materiau par maillage avant de poser l'energie ;
    sans cette copie, les cinq troncons partagent un slot et l'extinction les
    emporterait tous — la planche montrerait alors une coque entierement morte,
    c'est-a-dire l'inverse de ce que le lot veut prouver.
    """
    prefix = f"Section_{section:02d}"
    touched = 0
    for obj in decor:
        if obj.type != "MESH" or not obj.name.startswith(prefix):
            continue
        for index, slot in enumerate(obj.data.materials):
            if slot is not None and slot.name.startswith("AA_Emissive_Engine"):
                obj.data.materials[index] = slot.copy()
        touched += _set_emissive_energy([obj], EMISSIVE_ENERGY_DEAD)
    return touched


def _tile_nodes(path: str, report: dict, view: tuple, dead: bool) -> None:
    """Une entree de troncon a la camera du jeu, alimentee ou nœud abattu."""
    section, player_s, title = view
    centre = player_s + NODE_PLAYER_Z
    station = SPINES[section - 1]
    frontier = (section - 1) * SECTION_LENGTH
    near, far = _visible_deck_span(centre)
    _plate_reset()
    decor = _import(OUTPUT, "Decor", Vector((0.0, 0.0, centre)))
    turret_src = _kit_sources(TURRET_KIT)
    spine_src = _kit_sources(SPINE_KIT)
    seen: list[str] = []
    for route in report["branch_routes"]:
        ts = route["station"]
        if not (near - 2.0 <= ts <= far + 2.0):
            continue
        seat, _low = turret_seat_y(ts, route["marker_x"])
        _mount_turret(turret_src, route["number"],
                      Vector((route["marker_x"], seat, -(ts - centre))),
                      route["heavy"])
        seen.append(f"{route['name']}{' LOURDE' if route['heavy'] else ''}")
    for number, s in enumerate(SPINES, start=1):
        if not (near - 2.0 <= s <= far + 2.0):
            continue
        seat, _low = spine_seat_y(s)
        _mount_spine(spine_src, number, Vector((0.0, seat, -(s - centre))),
                     dead and number == section)
        seen.append(f"Spine_{number:02d}")
    _import(FIGHTER, "Player", Vector((0.0, 0.0, NODE_PLAYER_Z)))
    lit = _set_emissive_energy(decor, EMISSIVE_ENERGY_LIT)
    killed = _extinguish_section(decor, section) if dead else 0
    print(f"  [nœuds] troncon {section}, chasseur a s = {player_s:.1f}, "
          f"cadre s {near:.1f} a {far:.1f} : {lit} materiau(x) a "
          f"{EMISSIVE_ENERGY_LIT:.2f}"
          + (f", {killed} eteint(s) a {EMISSIVE_ENERGY_DEAD:.2f} sur "
             f"Section_{section:02d}" if dead else ""))
    _plate_lights()
    seat, _low = spine_seat_y(station)
    v = _screen_v(Vector((0.0, seat, -(station - centre))))
    camera = _plate_camera("game", _to_blender(CAM_POS), _to_blender(CAM_FORWARD),
                           _to_blender(CAM_UP), CAM_FOV_V)
    tint = (1.0, 0.62, 0.55) if dead else (1.0, 0.88, 0.55)
    _label(camera, "CAMERA DU JEU  ·  " + title
           + ("  ·  NŒUD ABATTU" if dead else "  ·  ALIMENTE"),
           -0.96, 0.90, 0.024, NODE_TILE_W, NODE_TILE_H, tint)
    _label(camera,
           f"Spine_{section:02d} a s = {station:.1f} (+{station - frontier:.1f} m "
           f"du debut du troncon)  ·  cadre sur le pont : s {near:.1f} a "
           f"{far:.1f} ({far - near:.1f} m)  ·  le nœud est a "
           f"{50.0 * (v + 1.0):.0f} % de la hauteur d'ecran",
           -0.96, 0.84, 0.024, NODE_TILE_W, NODE_TILE_H)
    _label(camera, "  ·  ".join(seen) + "  —  pieces REELLES de spine_kit.glb "
           "et turret_kit.glb", -0.96, 0.78, 0.022, NODE_TILE_W, NODE_TILE_H,
           (0.72, 0.84, 1.0))
    _label(camera,
           (f"ETEINT : Section_{section:02d} a {EMISSIVE_ENERGY_DEAD:.2f} "
            "(CortegeSkin.EMISSIVE_DEAD) et cœur retire "
            "(cortege_spine_node._take_damage) — ce qui reste doit se LIRE"
            if dead else
            f"ALIMENTE : AA_Emissive_Engine a {EMISSIVE_ENERGY_LIT:.2f} "
            "(CortegeSkin.EMISSIVE_ENERGY), le seul slot que le moteur eteint"),
           -0.96, -0.94, 0.022, NODE_TILE_W, NODE_TILE_H,
           (1.0, 0.62, 0.55) if dead else (0.72, 0.84, 1.0))
    _render(path, NODE_TILE_W, NODE_TILE_H)


def render_node_plate(report: dict) -> None:
    staging = tempfile.mkdtemp(prefix="aegis-cortege-nodes-")
    tiles: list[tuple[str, int]] = []
    try:
        for index, view in enumerate(NODE_VIEWS):
            for dead in (False, True):
                path = os.path.join(
                    staging, f"node{index}{'_dead' if dead else '_lit'}.png")
                _tile_nodes(path, report, view, dead)
                tiles.append((path, NODE_TILE_H))
        os.makedirs(os.path.dirname(NODE_PLATE), exist_ok=True)
        _compose(tiles, NODE_PLATE, width=NODE_TILE_W)
    finally:
        for leftover in os.listdir(staging):
            os.remove(os.path.join(staging, leftover))
        os.rmdir(staging)


# ==========================================================================
# Planche du complexe — `--complexe` (BRIEF-0111)
# ==========================================================================
# ⚠️ LE CRITERE DU LOT N'EST PAS « IL Y A DE LA MATIERE », C'EST « ON VOIT UNE
# INSTALLATION ». Un chiffre ne peut pas y repondre : deux vignettes au MEME
# cadrage, a la camera du jeu, avec les conduites REELLEMENT instanciees, le
# peuvent. Le BRIEF-0109 a ete rendu parce que la piece posee se lisait moins
# bien que ce qu'elle remplacait ; ici il n'y a rien a remplacer, donc la seule
# preuve possible est la comparaison avant / apres.

PLANT_PLATE = os.path.join(_REPO, "docs/forge/output/BRIEF-0111-planche.png")
CONDUIT_GLB = os.path.join(
    _REPO, "assets/imported/models/backgrounds/artery_conduit.glb")
HOSE_GLB = os.path.join(
    _REPO, "assets/imported/models/backgrounds/artery_hose.glb")
PLANT_TILE_W = 1920
PLANT_TILE_H = 1080
PLANT_TOP_H = 900
PLANT_ELEV_H = 460
#: Le chasseur, a sa place de jeu, sur la vignette « apres ».
PLANT_PLAYER_Z = 3.4


def _plant_frame_centre() -> float:
    """La station que la camera du jeu doit viser pour cadrer tout le complexe.

    Mesure et non estimation : `_visible_deck_span()` intersecte les deux rayons
    de bord de cadre avec le plan du pont median. Le complexe fait 24,5 m, le
    cadre en montre 23,6 : il n'y a qu'un centrage possible, et il se calcule.
    """
    centre = 0.5 * (PLANT_S[0] + PLANT_S[1])
    for _ in range(24):
        near, far = _visible_deck_span(centre, -4.95)
        centre += 0.5 * (PLANT_S[0] + PLANT_S[1]) - 0.5 * (near + far)
    return centre


def _godot_bounds(objects: list) -> tuple[Vector, Vector]:
    """Boite englobante d'objets Blender, RENDUE EN REPERE GODOT.

    C'est la mesure que `CortegeConduit._seat()` fait au moteur : elle assied la
    boite, jamais l'origine du fichier. Les quatre `.glb` de l'artere sont des
    sous-arbres extraits d'un assemblage plus grand, et leur racine porte encore
    sa translation d'origine — (-0,36 ; 1,00 ; 1,38) pour la conduite droite.
    """
    bpy.context.view_layer.update()
    lo = Vector((math.inf, math.inf, math.inf))
    hi = Vector((-math.inf, -math.inf, -math.inf))
    for obj in objects:
        if obj.type != "MESH":
            continue
        for corner in obj.bound_box:
            w = obj.matrix_world @ Vector(corner)
            g = Vector((w.x, w.z, -w.y))
            for k in range(3):
                lo[k] = min(lo[k], g[k])
                hi[k] = max(hi[k], g[k])
    return lo, hi


def _mount_conduit(path: str, name: str, marker: Vector) -> list:
    """Une piece d'artere assise sur son repere EXACTEMENT comme le moteur.

    Le repere marque le BAS : `y` du marqueur = `min.y` de la boite, `x` et `z`
    du marqueur = son CENTRE. Une planche qui poserait l'origine du fichier sur
    le repere ferait planer la piece d'un metre — c'est le defaut que le
    BRIEF-0110 a corrige dans le moteur, et une planche qui ne le reproduit pas
    ne prouve rien de ce que le joueur verra.
    """
    fresh = _import(path, name, Vector((0.0, 0.0, 0.0)))
    lo, hi = _godot_bounds(fresh)
    seat = Vector((marker.x - 0.5 * (lo.x + hi.x),
                   marker.y - lo.y,
                   marker.z - 0.5 * (lo.z + hi.z)))
    bpy.data.objects[name].location = _to_blender(seat)
    return fresh


def _mount_plant_conduits(centre: float) -> list:
    """Les cinq conduites du complexe, sur leurs cinq reperes."""
    out: list = []
    for number, (s, x) in enumerate(PLANT_CONDUITS, start=1):
        seat = _plant_seat(s, x)
        marker = Vector((x, seat, -(s - centre)))
        out += _mount_conduit(CONDUIT_GLB, f"Conduit_{number:02d}", marker)
        out += _mount_conduit(HOSE_GLB, f"Hose_{number:02d}", marker)
    return out


def _plant_seat(s: float, x: float) -> float:
    """Le Y d'assise d'une conduite du complexe, recalcule comme au maillage.

    ⚠️ RECALCULE ET NON RECOPIE : c'est `_surface_box()` qui decide, et elle
    prend le MINIMUM de ses quatre coins. Reprendre ici une constante ferait
    diverger la planche du binaire au premier changement de profil — la classe
    de defaut que ce fichier documente sous `BAY_COAMING_W`.
    """
    ys = [_surface_y(v, px)
          for v in (s - PLANT_CRADLE_S, s + PLANT_CRADLE_S)
          for px in (x - PLANT_LANE_HALF, x + PLANT_LANE_HALF)]
    return min(ys) + PLANT_CRADLE_RISE


def _tile_plant_game(path: str, glb: str, centre: float, after: bool,
                     report: dict | None, checker: bool = False) -> None:
    """La camera du jeu sur le complexe, avant ou apres."""
    _plate_reset()
    decor = _import(glb, "Decor", Vector((0.0, 0.0, centre)))
    pieces: list = []
    if after:
        pieces = _mount_plant_conduits(centre)
        _import(FIGHTER, "Player", Vector((0.0, 0.0, PLANT_PLAYER_Z)))
    if checker:
        _apply_checker(decor + pieces)
    _set_emissive_energy(decor + pieces, EMISSIVE_ENERGY_LIT)
    _plate_lights()
    near, far = _visible_deck_span(centre, -4.95)
    camera = _plate_camera("game", _to_blender(CAM_POS), _to_blender(CAM_FORWARD),
                           _to_blender(CAM_UP), CAM_FOV_V)
    tint = (1.0, 0.88, 0.55) if after else (0.72, 0.84, 1.0)
    head = ("APRES — le complexe industriel, ses cinq conduites REELLEMENT "
            "instanciees" if after else
            "AVANT — 24,5 m de tole nue entre Turret_13 et Ambry")
    if checker:
        # ⚠️ Sur un damier clair, une legende blanche disparait. Elle passe au
        # bleu de nuit du fond — la seule valeur qui contraste des deux cotes.
        tint = (0.05, 0.06, 0.16)
        head = (f"DAMIER UV sur le complexe — grande case = 1 tuile de "
                f"{1.0 / HULL_TEXELS_PER_METER:.2f} m, petite = "
                f"{100.0 / HULL_TEXELS_PER_METER / 8.0:.1f} cm")
    _label(camera, "CAMERA DU JEU (0 ; 14 ; 5), FOV 62  ·  " + head,
           -0.96, 0.90, 0.026, PLANT_TILE_W, PLANT_TILE_H, tint)
    _label(camera, f"cadre sur le pont median : s {near:.1f} a {far:.1f} "
                   f"({far - near:.1f} m)  ·  emprise du complexe s "
                   f"{PLANT_S[0]:.1f} a {PLANT_S[1]:.1f}  ·  45,8 px/m",
           -0.96, 0.845, 0.024, PLANT_TILE_W, PLANT_TILE_H,
           (0.05, 0.06, 0.16) if checker else (1.0, 1.0, 1.0))
    if checker and report is not None:
        d = report["density"]["Section_05"]
        _label(camera,
               f"projection en boite a {HULL_TEXELS_PER_METER:.3f} tuile/m, LA "
               f"MEME QUE LE BORDE  ·  mesure du troncon 5 : "
               f"{d['tiles_per_m_min']:.3f} a {d['tiles_per_m_max']:.3f} t/m, "
               f"moyenne {d['tiles_per_m_mean']:.3f}, anisotropie max "
               f"{d['anisotropy_max']:.2f}  ·  aucune image dans le .glb "
               f"(ADR-0028)",
               -0.96, -0.90, 0.022, PLANT_TILE_W, PLANT_TILE_H,
               (0.05, 0.06, 0.16))
    elif after and report is not None:
        plant = report["counts"][-1]
        _label(camera,
               f"{plant['complexe']} triangles poses  ·  troncon 5 : "
               f"{report['sections']['Section_05']['triangles']} tri  ·  "
               f"corridor : {report['triangles']} tri  ·  sommet du complexe "
               f"{plant['complexe_stats']['top']:+.2f} pour un plafond de vol "
               f"{CEILING_Y:+.2f}",
               -0.96, -0.90, 0.022, PLANT_TILE_W, PLANT_TILE_H, (0.72, 0.84, 1.0))
    else:
        _label(camera, "aucune installation : le joueur traverse 10 s de coque "
                       "sans rien a viser ni a lire",
               -0.96, -0.90, 0.022, PLANT_TILE_W, PLANT_TILE_H, (0.72, 0.84, 1.0))
    _render(path, PLANT_TILE_W, PLANT_TILE_H)


def _tile_plant_top(path: str, report: dict) -> None:
    """Le complexe de dessus, orthographique — le PLAN, qui est le livrable."""
    _plate_reset()
    centre = 0.5 * (PLANT_S[0] + PLANT_S[1])
    _import(OUTPUT, "Decor", Vector((0.0, 0.0, centre)))
    _mount_plant_conduits(centre)
    _plate_lights()
    # ⚠️ `sensor_fit` est VERTICAL : `ortho_scale` donne l'etendue en X (la
    # verticale de cette vue, tribord vers le BAS), et la longueur vue en `s`
    # vaut `ortho x largeur / hauteur`. 22 m sur 1920 x 900 en montrent 47 —
    # le complexe, la tourelle qui le precede et le premier collier d'Ambry.
    ortho = 22.0
    camera = _plate_camera(
        "top", _to_blender(Vector((8.0, 60.0, 0.0))),
        _to_blender(Vector((0.0, -1.0, 0.0))), _to_blender(Vector((-1.0, 0.0, 0.0))),
        math.radians(30.0), ortho=ortho)
    plant = report["counts"][-1]["complexe_stats"]
    _label(camera, f"DE DESSUS ({ortho:.0f} m) — proue a GAUCHE. Entree s "
                   f"{PLANT_S[0]:.0f}, cœur s {BASINS[0][0] - BASINS[0][1]:.0f}-"
                   f"{BASINS[0][0] + BASINS[0][1]:.0f}, sortie s {PLANT_S[1]:.0f}",
           -0.985, 0.91, 0.036, PLANT_TILE_W, PLANT_TOP_H, (1.0, 0.88, 0.55))
    _label(camera, f"x NOMINAL {PLANT_XN[0]:.2f}-{PLANT_XN[1]:.2f} : absolu "
                   f"{_pl(418.0, PLANT_XN[0]):.2f}-{_pl(418.0, PLANT_XN[1]):.2f} "
                   f"au large, {_pl(434.0, PLANT_XN[0]):.2f}-"
                   f"{_pl(434.0, PLANT_XN[1]):.2f} au pincement de s = 434 "
                   f"— le complexe SUIT la taille du bord",
           -0.985, 0.83, 0.030, PLANT_TILE_W, PLANT_TOP_H)
    _label(camera, f"bassin 1,63 m sous le pont  ·  {plant['plots']} plots  ·  "
                   f"{plant['traverses']} traverses  ·  {plant['passerelles']} "
                   f"passerelles  ·  voie DROITE : x {PLANT_LANE_IN_X:+.2f} a "
                   f"l'entree, {PLANT_LANE_OUT_X:+.2f} a la sortie",
           -0.985, -0.90, 0.030, PLANT_TILE_W, PLANT_TOP_H, (0.72, 0.84, 1.0))
    _render(path, PLANT_TILE_W, PLANT_TOP_H)


def _tile_plant_elevation(path: str, report: dict) -> None:
    """Tribord, avec la dalle du plafond de vol. Le seul critere DUR du lot."""
    _plate_reset()
    _import(OUTPUT, "Decor", Vector((0.0, 0.0, 0.0)))
    _mount_plant_conduits(0.0)
    _ceiling_slab(-460.0, -410.0)
    _plate_lights()
    ortho = 5.2
    centre = -0.5 * (PLANT_S[0] + PLANT_S[1])
    camera = _plate_camera(
        "elev", _to_blender(Vector((90.0, -5.05, centre))),
        _to_blender(Vector((-1.0, 0.0, 0.0))), _to_blender(Vector((0.0, 1.0, 0.0))),
        math.radians(30.0), ortho=ortho)
    plant = report["counts"][-1]["complexe_stats"]
    _label(camera, f"ELEVATION TRIBORD (26 m) — la dalle ambre EST le plafond "
                   f"de vol Y = {CEILING_Y:.0f}",
           -0.985, 0.84, 0.050, PLANT_TILE_W, PLANT_ELEV_H, (1.0, 0.88, 0.55))
    _label(camera, f"sommet du complexe {plant['top']:+.3f} "
                   f"(plafond de construction {BUILD_CEILING_Y:+.2f}, marge "
                   f"{plant['ciel']:.3f} m) — conduites comprises, la piece la "
                   f"plus haute qu'on puisse monter culmine a "
                   f"{max(a for _n, a in plant['sieges']) + CONDUIT_PIECE_TOP:+.3f}",
           -0.985, -0.90, 0.042, PLANT_TILE_W, PLANT_ELEV_H)
    _render(path, PLANT_TILE_W, PLANT_ELEV_H)


def render_plant_plate(report: dict) -> None:
    before = None
    if "--avant" in sys.argv:
        before = sys.argv[sys.argv.index("--avant") + 1]
    centre = _plant_frame_centre()
    staging = tempfile.mkdtemp(prefix="aegis-cortege-plant-")
    tiles: list[tuple[str, int]] = []
    try:
        if before and os.path.exists(before):
            path = os.path.join(staging, "avant.png")
            _tile_plant_game(path, before, centre, False, None)
            tiles.append((path, PLANT_TILE_H))
        else:
            print("  ⚠️ pas de `--avant <glb>` : la planche n'aura pas sa "
                  "vignette AVANT, et le lot ne prouve alors rien")
        path = os.path.join(staging, "apres.png")
        _tile_plant_game(path, OUTPUT, centre, True, report)
        tiles.append((path, PLANT_TILE_H))
        path = os.path.join(staging, "uv.png")
        _tile_plant_game(path, OUTPUT, centre, True, report, checker=True)
        tiles.append((path, PLANT_TILE_H))
        path = os.path.join(staging, "top.png")
        _tile_plant_top(path, report)
        tiles.append((path, PLANT_TOP_H))
        path = os.path.join(staging, "elev.png")
        _tile_plant_elevation(path, report)
        tiles.append((path, PLANT_ELEV_H))
        os.makedirs(os.path.dirname(PLANT_PLATE), exist_ok=True)
        _compose(tiles, PLANT_PLATE, width=PLANT_TILE_W)
    finally:
        for leftover in os.listdir(staging):
            os.remove(os.path.join(staging, leftover))
        os.rmdir(staging)


if __name__ == "__main__":
    main()
