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

#: 5 nœuds d'arete dorsale, exactement un par troncon, sur l'axe.
#: ⚠️ LA COQUE N'EN CUIT PLUS AUCUN (BRIEF-0094). `build_spine_bulb()` a disparu,
#: comme `build_bay()` (BRIEF-0091) et `build_turret_pad()` (BRIEF-0093) avant
#: elle, et pour une raison qui n'est pas esthetique : le nœud est DESTRUCTIBLE.
#: Une piece cuite dans le troncon ne s'eteint pas sans eteindre les quatre
#: autres, puisque les cinq partagent un seul maillage et un seul jeu de
#: materiaux. La coque porte le MARQUEUR ; `spine_kit.glb` porte le berceau, le
#: cœur et les entretoises, et le moteur ne detruit que le cœur.
SPINES: tuple[float, ...] = (54.1, 151.8, 260.2, 338.5, 458.8)

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
    for sc, hs, side in PITS:
        lo, hi = sc - hs - PIT_KEEPOUT, sc + hs + PIT_KEEPOUT
        x_lo = min(PIT_X[0] * side, PIT_X[1] * side) - PIT_KEEPOUT
        x_hi = max(PIT_X[0] * side, PIT_X[1] * side) + PIT_KEEPOUT
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
    for sc, hs, side in PITS:
        x0 = PIT_X[0] * side
        x1 = PIT_X[1] * side
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
    for sc, hs, side in PITS:
        xc = (PIT_X[0] + PIT_X[1]) * 0.5 * side
        half_x = (PIT_X[1] - PIT_X[0]) * 0.5 + PIT_KEEPOUT
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
    for sc, hs, _ in PITS:
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
    for sc, hs, side in PITS:
        if not (origin <= sc < origin + SECTION_LENGTH):
            continue
        s_lo, s_hi = sc - hs, sc + hs
        stations = [v for v in _stations(index) if s_lo - 1e-6 <= v <= s_hi + 1e-6]
        if len(stations) < 2:
            continue
        # Le fond : sous le point le PLUS BAS de l'emprise, pour qu'il soit
        # partout au moins a `PIT_DEPTH` de la peau.
        floor = min(_surface_y(v, PIT_X[k] * side)
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


def build_plates(bm: bmesh.types.BMesh, index: int, rng: random.Random,
                 aprons: list[tuple[float, float]],
                 busy: list[tuple[float, float]]) -> int:
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
                if _ambry_clash(s, s + length, min(x0, x1), max(x0, x1)):
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
                _surface_box(bm, x0 + inset, x1 - inset, s, s + length,
                             rise, 0.55, "AA_Greeble",
                             "AA_Greeble" if heavy else "AA_Hull",
                             draft=0.055 if not heavy else 0.10)
                busy.append((s, s + length))
                count += 1
                s += cell
    return count


def build_ribs(bm: bmesh.types.BMesh, index: int, rng: random.Random,
               busy: list[tuple[float, float]]) -> int:
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
            posed = False
            for a, b in near:
                for side in sides:
                    lane = _clip_lane(s, min(side * a, side * b),
                                      max(side * a, side * b))
                    if lane is None \
                            or _ambry_clash(s, s + width, lane[0], lane[1]) \
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
                 spans: list[tuple[float, float]]) -> int:
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
            count += _one_graft(bm, index, rng, busy, spans, s, length, side,
                                base_x, width, yaw, (k + slot) % 2 == 0)
    return count


def _one_graft(bm: bmesh.types.BMesh, index: int, rng: random.Random,
               busy: list[tuple[float, float]], spans: list[tuple[float, float]],
               s: float, length: float, side: float, base_x: float,
               width: float, yaw: float, violet: bool) -> int:
    """Une greffe et sa pile de terrasses. Rend le nombre de boites emises."""
    origin = index * SECTION_LENGTH
    count = 0
    x0, x1 = base_x - width * 0.5, base_x + width * 0.5
    lane = _clip_lane(s, min(side * x0, side * x1), max(side * x0, side * x1))
    if lane is None or s + length > origin + SECTION_LENGTH - JOINT_CLEARANCE:
        return count
    if _ambry_clash(s, s + length, lane[0], lane[1]):
        return count
    # Voir `build_plates` : on tire, puis on decide d'emettre.
    blocked = _bay_clash(s, s + length, lane[0], lane[1]) \
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
        if _ambry_clash(ps0, ps1, px0, px1):
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
               busy: list[tuple[float, float]]) -> int:
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
        if lane is None or _ambry_clash(s - 0.5, s + 0.5, lane[0], lane[1]):
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
    grafts = build_grafts(bm, index, rng, busy, graft_spans)
    aprons = list(MARKER_APRONS) + graft_spans
    counts = {
        "cellules_percees": skipped,
        "collerettes": build_bay_flanges(bm, index),
        "fosses": build_pits(bm, index),
        "greffes": grafts,
        "plaques": build_plates(bm, index, rng, aprons, busy),
        "nervures": build_ribs(bm, index, rng, busy),
        "lisses": build_strakes(bm, index),
        "pastilles": build_pips(bm, index, rng, aprons, busy),
    }
    conduits, lit = build_conduits(bm, index, rng)
    counts["conduits"] = conduits
    counts["travees"] = build_canal_braces(bm, index, rng)

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
    counts["marqueurs_tourelle"] = pads
    counts["baies"] = bays
    counts["nœuds"] = spines

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
    total_seen = 0.0
    area_by_material: dict[str, float] = {}
    seen_area: dict[str, float] = {}
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
                  "conduits", "travees", "marqueurs_tourelle", "baies", "nœuds",
                  "fosses", "cellules_percees", "collerettes"):
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
