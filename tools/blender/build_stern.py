"""build_stern.py — la carene de poupe du Long Cortege (BRIEF-0106, 0107, 0110).

    blender-aegis -t 1 -b -noaudio -P tools/blender/build_stern.py
    STERN_BEFORE_GLB=/chemin/stern_hull_avant.glb \
        blender-aegis -t 1 -b -noaudio -P tools/blender/build_stern.py -- --plate

Produit `assets/imported/models/backgrounds/stern_hull.glb` et, avec `--plate`,
`docs/forge/output/BRIEF-0110-planche.png` — rendue A LA CAMERA DU JEU, avec les
trois groupes propulsifs REELS montes dessus, LEURS TROIS PANACHES, et LES DIX-SEPT
PIECES INSTANCIEES SUR LES REPERES (`ADR-0006` : un asset non rendu et non regarde
n'est pas valide ; ici une planche sans panache montrerait trois rainures, et une
planche de reperes vides ne prouverait rien du tout).

⚠️ `STERN_BEFORE_GLB` EST FACULTATIF ET LA VIGNETTE 1 EN DEPEND. C'est la carene
d'AVANT le lot, extraite de git et construite hors depot, rendue au cadrage exact
de la vignette 2. Sans elle la comparaison avant/apres est simplement OMISE : une
planche qui inventerait son « avant » ne vaudrait rien.


CE QUE LE BRIEF-0110 A CHANGE — LA COQUE DIT OU, ELLE NE FABRIQUE PLUS QUOI
==========================================================================
Cinq familles de decor procedural cedent la place aux pieces tierces reduites au
`BRIEF-0108`, qui ne sont PAS cuites ici : dix-sept nœuds vides `CTRL | ` disent
au code ou les instancier. Une piece dupliquee dans la carene couterait ses
triangles autant de fois qu'elle apparait ; instanciee, elle n'est en memoire
qu'une fois.

    manifold    436 -> 396   le tube devient un PORTIQUE ; 7 pieces dessus
    rim_clamps  312 -> 384   les brides partent ; les filants restent (voir
                             `build_rim_rails`) ; 4 flexibles instancies
    pylons      240 -> 216   deux SOCLES ; 2 `stern_pylon.glb` instancies
    towers      560 -> 1592  regenerees, a la hauteur que le massif permet
    shoulders    96 -> 672   regeneres, au premier plan (45,7 px/m)

⚠️ `-t 1` EST OBLIGATOIRE. Meme raison que `scripts/build-hull.sh` et que
`assets/source/models/stern/reduce_stern.py` : sans lui, deux executions ne
rendent pas le meme fichier. Verifie ici sur trois executions.


CE QUE CETTE PIECE EST, ET CE QU'ELLE REMPLACE
==============================================
Les vingt derniers metres du Cortege, `s in [500, 520]`, sur lesquels sont
boulonnes les trois groupes propulsifs du `BRIEF-0105`. Elle remplace la dalle
grise de 34 x 1,6 x 22 m que `CortegeStern.build()` pose aujourd'hui.

Le nœud `Stern` est pose par `cortege_root.gd` a `z = -508` sous le meme parent
que les cinq troncons : le repere LOCAL de ce fichier est donc

    z_local = 508 - s          (s = distance depuis la pointe de proue)

soit `z = +8` a la jonction (s = 500) et `z = -12` a l'arriere (s = 520).


L'ANNEAU DE JONCTION EST IMPORTE, JAMAIS RECOPIE
================================================
Le premier anneau est `blc._half_profile(500.0, side)`, bord par bord, pris dans
`build_long_cortege` — c'est le critere qui prime au brief. Deux ecritures d'une
meme cote finissent toujours par diverger, et ce niveau en a deja paye deux (le
coaming du hangar, l'emprise du socle de tourelle). `_assert_junction()` relit le
`.glb` PRODUIT et compare les 48 sommets au micron.

⚠️ Et il compare les DEUX bords separement. A `s = 500` la coque se trouve etre
symetrique (`_asym` rend (1, 1)), mais rien ne le garantit demain : si un jour un
bord bouge sans l'autre, le harnais echoue plutot que de livrer une marche.


LA CONTRAINTE QUI A DECIDE DE TOUTE LA FORME : IL N'Y A PAS DE PLACE
====================================================================
Le brief interdit toute geometrie dans l'emprise d'un berceau : 10 x 15 m plus
0,5 m de garde, aux stations `x = 0` et `x = +/-10,28`. Ces trois prismes se
RECOUVRENT — 5,5 + 5,5 = 11,0 m de demi-emprises pour un entraxe de 10,28 — et
leur union est une seule bande :

    |x| <= 15,78   et   |z| <= 8,00     ->  rien au-dessus du pont (-11,85)

Consequences, et aucune n'est un gout :

  * « des masses hautes ENTRE les berceaux » (brief §2) est **geometriquement
    impossible** : il n'y a aucun metre carre libre entre deux berceaux. Le
    relief vertical est donc reporte sur les FLANCS (|x| >= 16,20) et sur le
    MASSIF ARRIERE (z <= -8,60), les deux seules zones libres.
  * la premiere marche d'evasement ne peut pas etre progressive : la coque doit
    passer de 12,04 m de demi-largeur (jonction) a plus de 15,78 m en une seule
    fois, exactement a `s = 500`. Elle le fait par un CHANFREIN de 0,90 m qui
    part vers l'exterieur au-dessus du niveau du pont — les deux marches
    suivantes, elles, sont libres et franches (s = 505,4 et s = 511).
  * l'artere ne peut pas se terminer DANS le bassin : tout ce qui y depasserait
    du pont mordrait un berceau. Son collecteur est donc pose de l'autre cote de
    la jonction, `z in [8,15 ; 9,45]`, a cheval sur la fin du canal du corridor —
    la seule position ou il soit a la fois visible et hors emprise.

⚠️ ET LA PAROI AVANT DU BASSIN NE SE VOIT PAS. On ne voit pas le mur AVANT d'une
fosse quand on la regarde de face et de haut : on en voit le fond et le mur du
FOND. Mesure a la camera du jeu (0 ; 14 ; 5) posee a `z = 11,47` local :
le fond du bassin n'apparait qu'a partir de `z = +6,49`, tout ce qui est plus
avant etant masque par le pont du corridor lui-meme. Le mur du fond (z = -8,60)
est au contraire pleine face : c'est LA surface a habiller, et c'est pour cela
que le massif arriere porte les tours.


CE QUE LES PLANCHES ONT DONNE — TROIS, PAS DIX
==============================================
Le brief en propose dix et previent : « ce n'est pas une liste de courses ».
Trois ont ete retenues, chacune sur UNE installation bornee :

    asset07  pylone spatial      -> les quatre pylones de rive (etagement,
                                    fuseau rectangulaire, socle debordant)
    asset08  bride de moteur     -> la chaine de brides du rebord de bassin
                                    (segments repetes, rails de guidage)
    asset08  conduite d'energie  -> le collecteur d'artere (tube octogonal,
                                    colliers de serrage, section vitree)

Une quatrieme, `asset08` tour d'echange thermique, sert aux deux tours du massif
arriere — socle evase, fut cannele, diffuseur en cone. Les six autres planches
sont laissees : « un module de relief ne se pose que dans l'emprise d'une
installation » (regle issue du `BRIEF-0094`).


L'EMISSIF : UNE SEULE INSTALLATION, ET ELLE S'ETEINT D'UN BLOC
==============================================================
`CortegeStern.blackout()` eteint tout ce qui porte `AA_Emissive_Engine`. Une
veine rangee ailleurs resterait allumee sur un vaisseau mort, sans erreur ni test
rouge. Le slot n'est donc porte QUE par la jonction d'artere, prise comme un tout :
le collecteur (section vitree) et l'anneau de distribution encastre dans le pont
qui en part. Rien d'autre du fichier ne le touche, et `_audit()` le compte sur le
binaire.

⚠️ L'anneau est ENCASTRE, jamais pose : ses rubans sont a `y = -11,99`, sous le
plan du pont. C'est ce qui lui permet d'exister dans l'emprise des berceaux (elle
n'interdit que ce qui DEPASSE) et c'est aussi la lecon du `BRIEF-0094` — une bande
emissive posee sur le point haut vole la lisibilite aux projectiles ; un creux,
non.


TEXTURE : AUCUNE (ADR-0028)
===========================
Zero image dans le `.glb`, PBR par facteurs, comme tout le niveau. Le depliage
est une projection en boite a **0,20 tuile/m** — la densite EXACTE de la peau du
corridor (`blc.HULL_TEXELS_PER_METER`), lue et non recopiee.

⚠️ La projection est calculee dans un repere DECALE de +2,00 m en z. Sans ce
decalage, `v = z_local x 0,20` vaudrait 1,60 a la jonction quand le troncon 5 y
vaut -20,00 : la carte sauterait de 0,6 tuile pile a l'endroit qu'on regarde. Avec
lui, `v = 2,00` — entier, donc en phase. Meme piege que `HULL_TILES_PER_SECTION`,
meme remede.


ANIMATION : AUCUNE (ADR-0046 §6)
================================
La poupe est de la structure. Ce qui bouge — nacelles, berceaux, verrous, bras —
est deja livre et anime par `reduce_stern.py`.


BRIEF-0107 : LE MASSIF ARRIERE EST CREUSE DE TROIS CANAUX
=========================================================
Le `BRIEF-0106` interdisait toute matiere DANS l'emprise des berceaux ; il ne
disait rien de ce qui passe DERRIERE eux. Or les trois panaches d'`ADR-0017`
sortent de la gorge de leur tuyere, filent 14 m vers l'arriere sur l'axe
`y = -8,63`, et rencontraient le plateau du massif (`-8,40`) a `z = -8,60` : leur
moitie basse traversait 3,40 m de coque.

⚠️ CE N'ETAIT PAS UN DEFAUT DE PLACEMENT DU PANACHE. Sa bouche est LUE dans
`stern_engine.glb` (`CTRL | Socket VFX flamme`, `z = -5,980`) et son axe est celui
du contrat de mariage de l'auteur ; les cotes de sa forme sont LUES dans
`plume_cortege.tres`. Rien de tout cela n'est recopie ici : `_plume_axis()` et
`_plume_radius()` les relisent, exactement comme l'anneau de jonction.

CE QUI A CHANGE, ET POURQUOI C'EST LE PLATEAU QUI TOMBE
------------------------------------------------------
Le plateau du massif ne descend PAS par soustraction : `AFT_TOP_Y` pose desormais
le dessus du massif a `CHANNEL_FLOOR_Y` (-10,95) sur les six premiers points de la
demi-section, et LE MASSIF EST REMONTE PAR QUATRE BOSSAGES (`build_channel_walls`)
qui laissent les trois canaux entre eux. C'est l'inverse d'un trou : on ne retire
rien, on ne pose que ce qui doit rester.

⚠️ ET LE POINT 5 DESCEND AVEC LES AUTRES, CE N'EST PAS UN EXCES. Laisse a -7,60,
l'arete 4 -> 5 franchissait la ligne de degagement (-10,90) a |x| = 11,58, soit
0,90 m DANS le canal lateral — un biseau invisible a l'œil, mesure par le harnais.
Le relief du flanc repart donc du point 6 (|x| = 15,78), largement dehors.

⚠️ ET LE CANAL DEBOUCHE. Une encoche dans le plateau laisserait une levre a
`z = -12` que le panache traverserait encore : les quatre bossages s'arretent a
`z = -11,60` et rien ne referme le canal a l'arriere.

⚠️ ET LE BLOC DE VENTILATION CENTRAL A DU PARTIR. Il etait a `|x| <= 2,10`,
`z in [-11,65 ; -8,45]`, `y in [-8,70 ; -6,90]` : au milieu exact du canal central.
Il est remplace par deux blocs poses sur les bossages interieurs, entre le canal et
la tour.

TROIS RAINURES NE SONT PAS UNE INSTALLATION
-------------------------------------------
Un canal d'echappement est une piece : la paroi est EN RETRAIT de 0,26 m et ce sont
des nervures qui viennent rattraper le bord exact du canal ; au-dessus d'elles un
chanfrein de 0,90 m de haut regarde le panache par en dessous — c'est LUI qui
accroche la seule lumiere violette du niveau, et c'est ce qu'une rainure plate
n'aura jamais ; a l'entree, une levre renforcee de 1,10 m encadre la bouche et
monte 0,45 m au-dessus du plateau.

⚠️ RIEN SUR LE FOND DU CANAL, ET C'EST MESURE. Entre le fond retenu (-10,95) et la
ligne de degagement (-10,90) il reste 5 cm : tout relief pose la franchirait. Les
2,55 m de paroi, eux, sont libres — c'est la que va le detail.

⚠️ AUCUN EMISSIF DANS LES CANAUX. `CortegeStern.blackout()` eteint ce qui porte
`AA_Emissive_Engine` ; un canal qui brillerait de lui-meme resterait allume sur un
vaisseau mort sans qu'aucun test ne le dise. La lumiere vient du panache, donc de
la matiere qui la reflechit. `_glow_in_channels()` le compte sur le binaire.
"""

from __future__ import annotations

import json
import math
import os
import re
import struct
import sys
import tempfile

import bmesh
import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "lib"))
_REPO = os.path.dirname(os.path.dirname(_HERE))

import aegis_kit as ak  # noqa: E402
import build_long_cortege as blc  # noqa: E402  (l'anneau de jonction vient de la)

OUTPUT = os.path.join(_REPO, "assets/imported/models/backgrounds/stern_hull.glb")
PLATE = os.path.join(_REPO, "docs/forge/output/BRIEF-0110-planche.png")
TUNING = os.path.join(_REPO, "resources/levels/long_cortege_stern.tres")
#: Le reglage du panache — lu, jamais recopie (BRIEF-0107).
PLUME_TUNING = os.path.join(_REPO, "resources/vfx/plume_cortege.tres")
MODELS = os.path.join(_REPO, "assets/imported/models/backgrounds")

# ==========================================================================
# Les cotes du jeu — LUES, jamais decidees ici
# ==========================================================================


def _game_tuning() -> dict:
    """Relit `long_cortege_stern.tres`. On ne le modifie pas : on s'y plie."""
    text = open(TUNING, encoding="utf-8").read()
    out: dict = {}
    for key, raw in re.findall(r"^(\w+) = (.+)$", text, re.M):
        raw = raw.strip()
        vec = re.match(r"Vector3\(([^)]*)\)", raw)
        if vec:
            out[key] = Vector([float(v) for v in vec.group(1).split(",")])
        else:
            try:
                out[key] = float(raw)
            except ValueError:
                pass
    out.setdefault("anchor_size_y", 1.20)
    out.setdefault("cradle_size", Vector((11.19, 4.64, 14.00)))
    out.setdefault("engine_size", Vector((9.10, 5.49, 11.93)))
    return out


T = _game_tuning()


def _plume_tuning() -> dict:
    """Relit `plume_cortege.tres` : la FORME du panache, telle que le jeu la rend.

    ⚠️ RECOPIER CES COTES ICI SERAIT LA MEME FAUTE QUE RECOPIER L'ANNEAU DE
    JONCTION. Le brief donne « 1,70 m de demi-largeur » ; ce nombre est le produit
    `throat_radius x belly_flare`, et il vit dans la Resource. Le jour ou l'auteur
    ouvre le ventre, la coque doit suivre sans qu'on y pense.
    """
    text = open(PLUME_TUNING, encoding="utf-8").read()
    out: dict = {}
    for key, raw in re.findall(r"^(\w+) = (.+)$", text, re.M):
        raw = raw.strip()
        col = re.match(r"Color\(([^)]*)\)", raw)
        if col:
            out[key] = Vector([float(v) for v in col.group(1).split(",")[:3]])
            continue
        try:
            out[key] = float(raw)
        except ValueError:
            pass
    return out


P = _plume_tuning()

#: La station de la poupe (s, en metres depuis la proue) : l'origine du repere local.
STATION = T["station"]                      # 508,0
#: Le pont qui porte les berceaux.
DECK_Y = T["deck_y"]                        # -11,85
#: L'entraxe des trois groupes.
SPACING = T["engine_spacing"]               # 10,28

#: Le plafond que TOUT le decor du niveau respecte (`blc.BUILD_CEILING_Y`).
CEILING_Y = blc.BUILD_CEILING_Y             # -3,20
#: La quille : la carene du corridor ne descend pas plus bas.
KEEL_Y = -12.60

#: La station de jonction, et son z LOCAL.
JOINT_S = 500.0
JOINT_Z = STATION - JOINT_S                 # +8,0
#: L'arriere de la poupe.
TAIL_Z = -12.0                              # s = 520

#: L'emprise interdite d'un berceau : 10 x 15 m plus 0,5 m de garde, en DEMIES.
KEEPOUT_HALF_X = 0.5 * 10.0 + 0.5           # 5,50
KEEPOUT_HALF_Z = 0.5 * 15.0 + 0.5           # 8,00
#: Les trois stations laterales.
ENGINE_X = (-SPACING, 0.0, SPACING)
#: L'union des trois emprises : elles se RECOUVRENT (voir l'en-tete).
KEEPOUT_X = SPACING + KEEPOUT_HALF_X        # 15,78

#: Budget du brief pour la CARENE seule.
TRI_BUDGET = 20_000
#: Budget de la poupe ENTIERE, pieces instanciees comprises (BRIEF-0110).
STERN_TOTAL_BUDGET = 80_000
#: Ce que la poupe consommait avant ce lot, tout compris (brief §Contexte).
STERN_BEFORE = 64_894
#: Ce que la carene pesait alors, et ce que les cinq familles retirees valaient.
HULL_BEFORE = 3_182
REMOVED_FAMILIES = 1_644

#: La densite de la peau du corridor, LUE dans le module (0,20 tuile/m).
TEXELS_PER_METER = blc.HULL_TEXELS_PER_METER
#: Decalage de projection : sans lui la carte saute a la jonction (voir l'en-tete).
UV_SHIFT_Z = 2.0


# ==========================================================================
# Les trois panaches — LUS eux aussi, jamais decides ici (BRIEF-0107)
# ==========================================================================
#: De combien le panache entre DANS la gorge. ⚠️ LUE, PLUS RECOPIEE. Elle vivait
#: dans `cortege_engine.gd` et ce generateur en avait pris une copie : deux
#: ecritures d'une meme cote, entre un script de jeu et un generateur d'asset, que
#: rien n'aurait rapprochees le jour ou l'une bouge — et cette cote-la decide de
#: l'entree des canaux. Elle est desormais dans `long_cortege_stern.tres`, que les
#: deux lisent. Remarque de la forge au BRIEF-0107, appliquee.
THROAT_BITE = T["throat_bite"]
#: Le nom du repere de l'auteur qui porte la bouche de tuyere.
FLAME_SOCKET = "CTRL | Socket VFX flamme"


def _flame_socket_z() -> float:
    """La bouche de tuyere, RELUE dans `stern_engine.glb`.

    ⚠️ ELLE N'EST PAS UNE CONSTANTE DE CE FICHIER. `cortege_engine.gd` a paye
    l'erreur inverse : il calculait la bouche depuis la boite englobante alors que
    le repere etait dans le binaire depuis le premier jour. On ne la recopie pas
    davantage ici — sinon le jour ou la nacelle change, la coque ne suit pas.
    """
    gltf, _blob = blc._read_glb(os.path.join(MODELS, "stern_engine.glb"))
    for node in gltf.get("nodes", []):
        if node.get("name") == FLAME_SOCKET:
            return float(node.get("translation", (0.0, 0.0, 0.0))[2])
    raise ak.ContractError(
        f"stern_engine.glb : aucun « {FLAME_SOCKET} » — la bouche de tuyere est "
        "introuvable, le creusement du massif n'a plus de cote de reference.")


FLAME_SOCKET_Z = _flame_socket_z()          # -5,980


def _scale_of(central: bool) -> float:
    """Le facteur d'echelle d'un groupe propulsif (`CortegeSternTuning.scale_of`)."""
    return T["asset_scale"] * (T["central_scale"] if central else 1.0)


def _plume_axis(central: bool) -> tuple[float, float, float]:
    """(y de l'axe, z de la bouche, z de la pointe) d'un panache, en cotes de jeu.

    Le panache est fils du corps du moteur : sa POSITION suit l'echelle du groupe,
    sa TAILLE non — `plume_cortege.tres` est en metres de jeu et
    `CortegeFlame.build()` lui passe `flame_length / length_full`, soit 1,0.
    """
    k = _scale_of(central)
    y = DECK_Y + T["engine_seat"].y * k
    z0 = (FLAME_SOCKET_Z + THROAT_BITE) * k
    return y, z0, z0 - P["length_full"]


def _plume_radius(t: float) -> float:
    """Le rayon du panache a l'abscisse `t` (0 au col, 1 en pointe).

    C'est le profil de `shaders/engine_plume.gdshader`, terme pour terme : ventre
    qui s'ouvre tres tot, effilement en racine, et le train de chocs qui PINCE.
    """
    u = min(max(t / 0.08, 0.0), 1.0)
    belly = 1.0 + (P["belly_flare"] - 1.0) * u * u * (3.0 - 2.0 * u)
    taper = math.sqrt(max(0.0, 1.0 - t))
    cell = 1.0 - abs(2.0 * ((t * P["shock_count"]) % 1.0) - 1.0)
    v = min(max(t / 0.12, 0.0), 1.0)
    shock = 1.0 - P["shock_depth"] * (1.0 - cell) * (1.0 - t) * v * v * (3.0 - 2.0 * v)
    return P["throat_radius"] * belly * taper * shock


#: La demi-largeur de reference du brief : `throat_radius x belly_flare` = 1,70 m.
#: Le maillage reel culmine un peu en dessous (l'effilement a deja commence) —
#: la cote du brief est donc CONSERVATRICE, et c'est elle qu'on garde.
PLUME_HALF = P["throat_radius"] * P["belly_flare"]

# ==========================================================================
# La section transversale — 25 points par bord, MEME topologie que le corridor
# ==========================================================================
# Le premier anneau EST celui du corridor ; tous les autres reprennent ses 25
# indices avec d'autres coordonnees. C'est ce qui permet de border la jonction
# sans changer de topologie, donc sans coudre a la main.
#
#   0..8    le fond du bassin, de l'axe au pied de paroi
#   9..12   la paroi du bassin (fruit de 0,60 m sur 5 a 7 m)
#   13      l'arete de rive
#   14..18  les trois terrasses etagees, marches franches
#   19      la facette exterieure : le point le PLUS LARGE
#   20..24  le dessous, jusqu'a la quille

#: Le fond du bassin (la « sole »). L'assise des berceaux est une DALLE posee
#: dessus, a `DECK_Y` : c'est ce qui donne au pourtour son creux sans percer la
#: peau (voir `build_apron()`).
SOLE_Y = -12.00
#: Le pied de paroi le plus INTERIEUR que la coque s'autorise. Il est a 0,62 m de
#: l'union des trois emprises (15,78) : c'est toute la marge disponible.
BASIN_MIN_X = 16.40

#: Les trois bandes de station, et c'est LA le profil d'evasement.
#:
#: ⚠️ LA BOUCHE DU BASSIN S'OUVRE EN MEME TEMPS QUE LA COQUE, et la premiere
#: version ne le faisait pas : le rebord restait a 17,00 dans les trois bandes,
#: seule l'etagere exterieure gagnait 1,7 m. Rendu et regarde de dessus, le
#: resultat etait un rectangle — l'evasement ne se lisait nulle part. Ici les
#: quatre cotes bougent ensemble a chaque marche : pied de paroi, arete de rive,
#: terrasses et bord. De dessus, le bassin S'OUVRE.
#:
#: ⚠️ ET LA RIVE MONTE VERS L'ARRIERE. Les deux vont ensemble : a chaque marche la
#: terrasse change d'altitude en meme temps que de largeur, si bien qu'on voit la
#: face horizontale du gradin et pas seulement le bord de la silhouette. Le brief
#: le dit : « ce qui distingue une marche d'une pente, c'est la face horizontale
#: entre les deux ».
#:
#: (nom, z_avant, z_arriere, rive_y, pied de paroi, arete de rive, bord)
BANDS: tuple[tuple[str, float, float, float, float, float, float], ...] = (
    ("B1", JOINT_Z, 2.72, -6.60, BASIN_MIN_X, 16.60, 17.00),
    ("B2", 2.60, -2.88, -5.60, 17.30, 17.60, 18.40),
    ("B3", -3.00, -8.48, -4.60, 18.20, 18.60, 19.80),
)
#: Le massif arriere : le bassin s'y referme, et ses bossages portent les tours.
AFT_Z = -8.60
AFT_CREST_Y = -4.60
#: L'altitude du massif d'avant le `BRIEF-0107` : elle reste le DESSUS DES BOSSAGES.
AFT_PLATEAU_Y = -8.40

# --------------------------------------------------------------------------
# Les trois canaux d'echappement (BRIEF-0107) — les cotes avant la geometrie,
# parce que c'est `AFT_TOP_Y` qui les ouvre.
# --------------------------------------------------------------------------
#: La demi-largeur du canal : 1,70 m de panache et 0,50 m de garde.
CHANNEL_HALF = 2.20
#: Le fond du canal. ⚠️ IL EST AU MILIEU EXACT DE LA BANDE PERMISE PAR LE BRIEF :
#: 0,05 m sous la ligne de degagement (-10,90) et 1,05 m au-dessus de `SOLE_Y`,
#: pour un plancher qui demande « >= 1,00 m ». Les deux marges sont volontairement
#: egales : rien ici ne merite d'etre serre d'un cote pour rien de l'autre.
CHANNEL_FLOOR_Y = -10.95
#: La ligne que rien ne franchit dans l'emprise d'un panache (0,57 m sous son bord
#: bas, -10,33). C'est le critere du brief, et c'est ce que `_plume_intrusion()`
#: mesure sur le binaire.
CHANNEL_CLEAR_Y = -10.90
#: L'entree du canal : 0,10 m avant la paroi du massif, pour qu'elle soit franche.
CHANNEL_Z0 = -8.50
#: Les trois stations : ce sont les axes des trois groupes, rien d'autre.
CHANNEL_X = ENGINE_X

#: Le dessus du massif, en FRACTIONS du pied de paroi (indices 0..8).
#:
#: ⚠️ LES SIX PREMIERS POINTS SONT AU FOND DU CANAL, ET LE MASSIF EST REMONTE PAR
#: DES BOSSAGES. Creuser par soustraction aurait demande un booleen — non
#: deterministe a la topologie pres, et illisible dans un generateur. Ici la peau
#: est basse par construction et `build_channel_walls()` ne repose QUE ce qui doit
#: rester : l'inverse d'un trou.
#:
#: ⚠️ ET LE POINT 5 (|x| = 14,01) DESCEND AVEC LES QUATRE AUTRES. Laisse a -7,60,
#: l'arete 4 -> 5 traversait la ligne de degagement a |x| = 11,58, soit 0,90 m dans
#: le canal lateral (qui va jusqu'a 12,48). Mesure par `_plume_intrusion()`,
#: invisible autrement.
AFT_TOP_Y = (CHANNEL_FLOOR_Y, CHANNEL_FLOOR_Y, CHANNEL_FLOOR_Y, CHANNEL_FLOOR_Y,
             CHANNEL_FLOOR_Y, CHANNEL_FLOOR_Y, -6.20, -4.90, AFT_CREST_Y)

#: ⚠️ IL N'Y A PAS DE CHANFREIN DE PROUE, ET CE N'EST PAS UN OUBLI. La premiere
#: version en portait un de 0,90 m : la premiere marche partait vers l'arriere en
#: biais, ce qui donnait a la poupe une entree taillee plutot qu'une plaque. Le
#: harnais d'emprise l'a refuse, et il a raison — MESURE : 17,79 m2 de decor
#: au-dessus du pont dans les emprises de berceau.
#:
#: La raison est arithmetique et sans echappatoire. Le bordage du corridor a
#: `s = 500` s'arrete a |x| = 12,04, l'union des trois emprises va jusqu'a
#: |x| = 15,78, et le premier anneau de la poupe est a |x| >= 16,40. Toute face
#: qui relie l'un a l'autre traverse donc la bande interdite. Tant qu'elle est
#: dans le PLAN `z = 8,00` son ombre est un segment d'aire nulle et elle ne mord
#: rien ; des qu'elle prend la moindre epaisseur en z, elle balaie la bande.
#:
#: La face avant de la poupe est donc **rigoureusement plane**, a la limite exacte
#: de l'emprise. Le brief ne laisse pas un centimetre : 508 - 8 = 500. Le relief
#: qui lui manque est repris AVANT elle, par `build_shoulders()`, dans le seul
#: volume libre qui reste : `z >= 8,00`, de part et d'autre du corridor.
FORE_FACE_Z = JOINT_Z

#: Fractions du pied de paroi pour les points 5..8 du fond.
FLOOR_T = (0.000, 0.159, 0.317, 0.476, 0.634, 0.770, 0.867, 0.945, 1.000)
#: Fractions de la paroi (entre pied et arete) aux points 9..12.
WALL_T = (0.28, 0.52, 0.72, 0.88)
WALL_X_T = (0.20, 0.40, 0.62, 0.83)


def _band_of(z: float) -> tuple:
    for band in BANDS:
        if band[2] - 1e-9 <= z <= band[1] + 1e-9:
            return band
    return BANDS[-1]


def _half_stern(z: float, aft: bool = False) -> list[tuple[float, float]]:
    """La demi-section tribord de la poupe a la station `z`, 25 points."""
    _, _, _, crest_y, basin_x, crest_x, wmax = _band_of(z)
    top = list(AFT_TOP_Y) if aft else [SOLE_Y] * 9
    crest = AFT_CREST_Y if aft else crest_y
    shelf = wmax - crest_x
    pts: list[tuple[float, float]] = []
    for i, t in enumerate(FLOOR_T):
        pts.append((basin_x * t, top[i]))
    base = top[8]
    for xt, yt in zip(WALL_X_T, WALL_T):
        pts.append((basin_x + (crest_x - basin_x) * xt, base + (crest - base) * yt))
    pts.append((crest_x, crest))                              # 13 arete de rive
    pts.append((crest_x + shelf / 3.0, crest - 0.10))         # 14 terrasse 1
    pts.append((crest_x + shelf / 3.0 + 0.10, crest - 1.20))  # 15 contremarche
    pts.append((crest_x + 2.0 * shelf / 3.0, crest - 1.30))   # 16 terrasse 2
    pts.append((crest_x + 2.0 * shelf / 3.0 + 0.10, crest - 2.40))
    pts.append((wmax, crest - 2.50))                          # 18 terrasse 3
    pts.append((wmax + 0.10, crest - 3.70))                   # 19 point le + large
    pts.append((wmax - 0.20, -11.30))                         # 20 bord bas
    # ⚠️ LE PLUS PETIT DEFAUT DE CE FICHIER TENAIT DANS CE `max()`. Sans lui, la
    # sous-chine rentrait a `wmax - 1,90` : en bande avant (wmax = 17,00) l'arete
    # 20 -> 21 traversait le plan du pont a |x| = 15,63, soit 15 cm DANS l'union
    # des emprises. 1,57 m2 de dessous de coque au-dessus du pont, sous un
    # berceau lateral, mesures par le harnais. Invisible a l'œil, refuse au
    # micron.
    pts.append((max(wmax - 1.90, BASIN_MIN_X - 0.10), -12.10))  # 21 sous-chine
    pts.append((max(wmax - 6.60, 8.00), -12.45))              # 22 fond
    pts.append((5.00, -12.55))                                # 23 fond
    pts.append((0.00, -12.58))                                # 24 quille
    return pts


#: Materiau du segment `i -> i+1` de la demi-section (24 entrees).
#: ⚠️ AUCUN VIOLET NI AUCUN IVOIRE SUR LA PEAU. Sur 500 m, le `BRIEF-0094` a
#: mesure qu'un materiau qui suit une arete CONTINUE occupe plus de pixels que
#: n'importe quelle piece — et le compte de triangles ne le dit pas. Ici la peau
#: est en deux gris ; la couleur n'appartient qu'aux installations.
HALF_MATERIALS: tuple[str, ...] = (
    "AA_Hull", "AA_Hull", "AA_Hull", "AA_Hull",         # 0-4  fond
    "AA_Hull", "AA_Hull", "AA_Hull", "AA_Hull",         # 4-8  fond
    "AA_Greeble", "AA_Greeble", "AA_Greeble",           # 8-11 paroi du bassin
    "AA_Greeble", "AA_Hull",                            # 11-13
    "AA_Hull", "AA_Hull", "AA_Hull",                    # 13-16 terrasses
    "AA_Hull", "AA_Hull", "AA_Greeble",                 # 16-19
    "AA_Greeble", "AA_Greeble", "AA_Greeble",           # 19-22 dessous
    "AA_Greeble", "AA_Greeble",                         # 22-24
)


def _ring_materials() -> list[str]:
    n = 25
    mats = [HALF_MATERIALS[i] for i in range(n - 1)]
    mats += [HALF_MATERIALS[2 * n - 3 - i] for i in range(n - 1, 2 * n - 2)]
    return mats


RING_MATERIALS = _ring_materials()
RING_SIZE = 48


def _close(tribord: list[tuple[float, float]],
           babord: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Anneau ferme de 48 points, tribord puis babord — meme regle que `blc._ring`."""
    return tribord + [(-x, y) for x, y in reversed(babord[1:-1])]


def _joint_ring() -> list[tuple[float, float]]:
    """L'anneau du corridor a `s = 500`, IMPORTE bord par bord."""
    return _close(blc._half_profile(JOINT_S, 1.0), blc._half_profile(JOINT_S, -1.0))


def _stern_ring(z: float, aft: bool = False) -> list[tuple[float, float]]:
    half = _half_stern(z, aft)
    return _close(half, half)


def _ring_z(ring: list[tuple[float, float]], z: float) -> list[Vector]:
    """Pose un anneau a la station `z`."""
    return [Vector((x, y, z)) for x, y in ring]


# ==========================================================================
# Primitives de maillage — memes principes que `build_long_cortege`
# ==========================================================================


def _new_object(name: str, bm: bmesh.types.BMesh) -> bpy.types.Object:
    """Objet aux 7 slots du kit, SANS `recalc_face_normals`.

    La poupe est une coque fermee mais elle porte un bassin : sur une surface
    concave, l'heuristique de bmesh peut retourner des pans entiers sans qu'aucune
    bounding box ne s'en apercoive. Le bobinage est pose par construction et
    `_orient()` le verifie au VOLUME SIGNE, composant par composant.
    """
    mesh = bpy.data.meshes.new(name)
    ak.apply_material_slots(mesh)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


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
    face.material_index = ak.mat_index(material)
    return face


def _bridge(bm: bmesh.types.BMesh, front: list, back: list,
            materials: list[str]) -> None:
    """Relie deux anneaux fermes. `front` est a plus grand z."""
    n = len(front)
    for i in range(n):
        j = (i + 1) % n
        _face(bm, [front[i], front[j], back[j], back[i]], materials[i])


def _cap(bm: bmesh.types.BMesh, ring: list, material: str, facing_front: bool):
    order = list(reversed(ring)) if facing_front else list(ring)
    return _face(bm, order, material)


def _signed_volume(bm: bmesh.types.BMesh) -> float:
    total = 0.0
    for face in bm.faces:
        verts = [loop.vert.co for loop in face.loops]
        a = verts[0]
        for i in range(1, len(verts) - 1):
            b, c = verts[i], verts[i + 1]
            total += a.dot(b.cross(c)) / 6.0
    return total


def _orient(bm: bmesh.types.BMesh, name: str) -> None:
    """Retourne le composant entier si son volume signe est negatif.

    ⚠️ C'EST LE SEUL CONTROLE QUI VOIE UNE COQUE A L'ENVERS. Une face retournee
    ne produit aucune erreur : elle DISPARAIT en jeu (culling arriere) et le
    journal reste muet. Sur une piece fermee et bobinee de facon coherente, le
    signe du volume tranche pour toutes les faces d'un coup.
    """
    volume = _signed_volume(bm)
    if abs(volume) < 1e-6:
        raise ak.ContractError(f"{name} : volume nul — piece non fermee ?")
    if volume < 0.0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])


def _box(bm: bmesh.types.BMesh, x0: float, x1: float, y0: float, y1: float,
         z0: float, z1: float, side_mat: str, top_mat: str | None = None) -> None:
    """Une boite alignee, faces sortantes.

    ⚠️ LES BORNES SONT TRIEES, ET CE N'EST PAS DU CONFORT. Toute cette poupe se
    construit en miroir (`side * x`), ce qui INVERSE l'ordre des bornes a babord :
    la boite y sortait retournee, invisible en jeu, et son volume signe annulait
    exactement celui de tribord — le controle d'orientation lisait zero et ne
    voyait rien. Un defaut silencieux qui en masquait un autre.
    """
    top_mat = top_mat or side_mat
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    z0, z1 = min(z0, z1), max(z0, z1)
    lo = [Vector((x0, y0, z0)), Vector((x1, y0, z0)),
          Vector((x1, y0, z1)), Vector((x0, y0, z1))]
    hi = [Vector((x0, y1, z0)), Vector((x1, y1, z0)),
          Vector((x1, y1, z1)), Vector((x0, y1, z1))]
    lv = [bm.verts.new(v) for v in lo]
    hv = [bm.verts.new(v) for v in hi]
    _face(bm, [hv[0], hv[3], hv[2], hv[1]], top_mat)
    _face(bm, [lv[0], lv[1], lv[2], lv[3]], side_mat)
    for i in range(4):
        j = (i + 1) % 4
        _face(bm, [lv[i], hv[i], hv[j], lv[j]], side_mat)


def _prism(bm: bmesh.types.BMesh, cx: float, cz: float, radii: list[float],
           y0: float, y1: float, sides: int, side_mat: str, cap_mat: str,
           phase: float = 0.0) -> tuple[list, list]:
    """Un prisme vertical a `sides` cotes, rayon par sommet (cannelures)."""
    lo, hi = [], []
    for i in range(sides):
        a = phase + 2.0 * math.pi * i / sides
        r = radii[i % len(radii)]
        x, z = cx + r * math.cos(a), cz + r * math.sin(a)
        lo.append(bm.verts.new(Vector((x, y0, z))))
        hi.append(bm.verts.new(Vector((x, y1, z))))
    for i in range(sides):
        j = (i + 1) % sides
        _face(bm, [lo[i], lo[j], hi[j], hi[i]], side_mat)
    _face(bm, list(reversed(hi)), cap_mat)
    _face(bm, lo, cap_mat)
    return lo, hi


def _cone(bm: bmesh.types.BMesh, cx: float, cz: float, r0: float, r1: float,
          y0: float, y1: float, sides: int, side_mat: str, cap_mat: str) -> None:
    lo, hi = [], []
    for i in range(sides):
        a = 2.0 * math.pi * i / sides
        lo.append(bm.verts.new(Vector((cx + r0 * math.cos(a), y0,
                                       cz + r0 * math.sin(a)))))
        hi.append(bm.verts.new(Vector((cx + r1 * math.cos(a), y1,
                                       cz + r1 * math.sin(a)))))
    for i in range(sides):
        j = (i + 1) % sides
        _face(bm, [lo[i], lo[j], hi[j], hi[i]], side_mat)
    _face(bm, list(reversed(hi)), cap_mat)
    _face(bm, lo, cap_mat)


def _tube_x(bm: bmesh.types.BMesh, x0: float, x1: float, cy: float, cz: float,
            radius: float, sides: int, material: str) -> tuple[list, list]:
    """Un tube d'axe X, ouvert : les bouts sont fermes par l'appelant."""
    a0, a1 = [], []
    for i in range(sides):
        a = 2.0 * math.pi * (i + 0.5) / sides
        y, z = cy + radius * math.cos(a), cz + radius * math.sin(a)
        a0.append(bm.verts.new(Vector((x0, y, z))))
        a1.append(bm.verts.new(Vector((x1, y, z))))
    for i in range(sides):
        j = (i + 1) % sides
        _face(bm, [a0[i], a1[i], a1[j], a0[j]], material)
    return a0, a1


# ==========================================================================
# 1. LA PEAU — le loft de la jonction au massif arriere
# ==========================================================================


def _stations() -> list[tuple[float, list[tuple[float, float]]]]:
    """(z, anneau) — de l'avant vers l'arriere."""
    rings: list[tuple[float, list]] = []
    rings.append((JOINT_Z, _joint_ring()))
    for _name, z_fore, z_aft, *_ in BANDS:
        rings.append((z_fore, _stern_ring(z_fore)))
        rings.append((z_aft, _stern_ring(z_aft)))
    rings.append((AFT_Z, _stern_ring(AFT_Z, aft=True)))
    rings.append((TAIL_Z + 0.40, _stern_ring(TAIL_Z + 0.40, aft=True)))
    tail = [(x * 0.92, y - (0.50 if y > DECK_Y else 0.0))
            for x, y in _stern_ring(TAIL_Z, aft=True)]
    rings.append((TAIL_Z, tail))
    return rings


def build_skin(bm: bmesh.types.BMesh) -> None:
    """Le loft. Marches FRANCHES : deux anneaux a 0,12 m l'un de l'autre.

    ⚠️ Le premier bridge relie deux anneaux a la MEME station (`z = 8,00`) : c'est
    la face avant, plane par obligation (voir `FORE_FACE_Z`). Les deux suivants
    (`z = 2,72 -> 2,60` et `-2,88 -> -3,00`) sont les deux epaulements, francs a
    0,12 m — assez pour que la contremarche existe, trop peu pour qu'on la lise
    comme une pente.
    """
    previous: list | None = None
    for z, ring in _stations():
        current = [bm.verts.new(v) for v in _ring_z(ring, z)]
        if previous is not None:
            _bridge(bm, previous, current, RING_MATERIALS)
        previous = current
    _cap(bm, previous, "AA_Greeble", facing_front=False)


# ==========================================================================
# 2. L'ASSISE — la dalle plane sur laquelle les trois berceaux se posent
# ==========================================================================
# Le fond du loft est a `SOLE_Y` (-12,00) ; l'assise est une DALLE de 0,15 m
# posee dessus, dont le dessus est a `DECK_Y` (-11,85) EXACTEMENT.
#
# ⚠️ SON DESSUS EST AU NIVEAU DU PONT, PAS AU-DESSUS : elle ne « mord » donc
# aucune emprise de berceau (le brief interdit ce qui DEPASSE). Et c'est ce qui
# donne gratuitement au pourtour son creux de 0,15 m — la gorge ou court l'anneau
# d'artere, et le seul relief de sol qui reste visible entre les nacelles.

APRON_HALF_X = 15.95
APRON_FORE_Z = 7.95
APRON_AFT_Z = -8.20
#: ⚠️ UNE SEULE DALLE, ET C'EST UNE DECISION MESUREE. Une version a trois dalles
#: (une par groupe, joint dans le creux entre deux berceaux) a ete construite puis
#: abandonnee : le creneau disponible est trop etroit pour un joint honnete.
#:
#:   le brief demande 10 m d'assise par berceau      -> central jusqu'a 5,00
#:                                                      lateral a partir de 5,28
#:   le berceau CENTRAL en mesure en fait 10,32       -> il va jusqu'a 5,16
#:   le berceau LATERAL commence a                       5,41
#:
#: Satisfaire a la fois la cote du brief ET l'enveloppe reelle des pieces ne laisse
#: que `[5,16 ; 5,28]`, soit **0,12 m** — un trait, pas un joint, et une assise a
#: 0,00 m de marge sous un berceau lateral. La dalle est donc d'un seul tenant :
#: 31,90 x 16,15 m, 5,95 m de marge laterale sur la cote du brief.
#:
#: Son dessus est a `DECK_Y` EXACTEMENT, pas au-dessus : elle ne mord donc aucune
#: emprise (le brief interdit ce qui DEPASSE du pont) et elle donne gratuitement au
#: pourtour son creux de 0,15 m — la gorge ou court l'anneau d'artere.


def build_apron(bm: bmesh.types.BMesh) -> None:
    _box(bm, -APRON_HALF_X, APRON_HALF_X, SOLE_Y, DECK_Y,
         APRON_AFT_Z, APRON_FORE_Z, "AA_Greeble", "AA_Hull")


# ==========================================================================
# 3. L'ARTERE — collecteur et anneau de distribution (LE SEUL EMISSIF)
# ==========================================================================

#: La gorge de rive : entre le bord de l'assise et le pied de paroi.
GROOVE_X = APRON_HALF_X + 0.22
GLOW_Y = SOLE_Y + 0.01
#: ⚠️ 0,09 ET NON 0,15 DE DEMI-LARGEUR, ET LE RUBAN EST TIRETE. Rendu et regarde :
#: en continu et a 0,30 m de large, l'anneau dessinait un RECTANGLE NEON autour du
#: pont — la chose la plus lumineuse d'un cadre ou le joueur doit lire dix verrous.
#: C'est mot pour mot le defaut que le `BRIEF-0094` a corrige sur l'arete dorsale
#: du corridor. Tirete, il se lit comme une rangee de feux de balisage : on voit
#: qu'il alimente, on ne le regarde plus a la place des cibles. Aire emissive
#: mesuree sur le binaire : voir le compte-rendu.
GLOW_HALF = 0.09
GLOW_DASH = 1.30
GLOW_GAP = 1.45


def _ribbon(bm: bmesh.types.BMesh, x0: float, x1: float,
            z0: float, z1: float) -> None:
    v = [bm.verts.new(Vector((x0, GLOW_Y, z0))),
         bm.verts.new(Vector((x1, GLOW_Y, z0))),
         bm.verts.new(Vector((x1, GLOW_Y, z1))),
         bm.verts.new(Vector((x0, GLOW_Y, z1)))]
    _face(bm, [v[0], v[3], v[2], v[1]], "AA_Emissive_Engine")


def _dashes(bm: bmesh.types.BMesh, x0: float, x1: float,
            a: float, b: float, along_z: bool) -> None:
    """Une file de tirets entre `a` et `b`, le long de z (ou de x)."""
    cursor = a
    while cursor + GLOW_DASH <= b + 1e-9:
        if along_z:
            _ribbon(bm, x0, x1, cursor, cursor + GLOW_DASH)
        else:
            _ribbon(bm, cursor, cursor + GLOW_DASH, x0, x1)
        cursor += GLOW_DASH + GLOW_GAP


def build_glow_ring(bm: bmesh.types.BMesh) -> None:
    """Les tirets encastres : deux files de rive et la traverse arriere.

    ⚠️ ILS SONT DANS LA GORGE, A 0,15 m SOUS LE PONT. Poses a plat sur l'assise,
    les memes tirets seraient au niveau des semelles de berceau ; encastres, la
    geometrie les ombre d'elle-meme et ils ne mordent aucune emprise (le brief
    n'interdit que ce qui DEPASSE du pont).
    """
    for side in (-1.0, 1.0):
        _dashes(bm, side * (GROOVE_X - GLOW_HALF), side * (GROOVE_X + GLOW_HALF),
                APRON_AFT_Z + 0.20, APRON_FORE_Z - 0.60, along_z=True)
    _dashes(bm, AFT_Z + 0.14, APRON_AFT_Z - 0.06,
            -(GROOVE_X + GLOW_HALF), GROOVE_X + GLOW_HALF, along_z=False)


#: LE COLLECTEUR D'ARTERE — DES PIECES INSTANCIEES, PLUS UN TUBE PROCEDURAL
#: =========================================================================
#: (BRIEF-0110 §1) Le tube octogonal de 436 triangles a laisse la place aux
#: pieces livrees au `BRIEF-0108` : `artery_conduit.glb` et
#: `artery_conduit_bend.glb` SONT un collecteur, c'est leur planche d'origine.
#: Ce fichier n'en pose plus la matiere — il pose LE PORTIQUE QUI LES PORTE et
#: les reperes `CTRL | Collecteur NN` / `CTRL | Liaison NN` ou le code les monte.
#:
#: ⚠️ UNE PIECE DUPLIQUEE DANS LA CARENE COUTERAIT SES TRIANGLES AUTANT DE FOIS
#: QU'ELLE APPARAIT. Cinq conduites cuites ici, c'est 3 260 triangles de plus
#: dans un maillage de 4 200 ; instanciees, elles ne sont en memoire qu'une fois.
#:
#: ⚠️ ET C'EST LE MORCEAU LE PLUS REGARDE DU LOT. Mesure a la camera du jeu :
#: le collecteur tombe a **724 px sur 1080** — bas de cadre, au centre — et il y
#: rend a **50,3 px/m**, contre 32,7 sur le pont de poupe. C'est la que le
#: travail va.
MANIFOLD_Z0 = JOINT_Z + 0.15                       # 8,15
MANIFOLD_Z1 = JOINT_Z + 1.45                       # 9,45
#: La station du rail : le milieu de la bande libre, apres l'emprise (z >= 8,00).
MANIFOLD_CZ = 8.95
#: La station des flexibles, en AVANT du rail.
LIAISON_CZ = 9.55

#: ⚠️ LE RAIL EST A DEUX NIVEAUX PARCE QUE LE PONT L'EST. Mesure sur la peau du
#: corridor a `s = 499,05` : le pont interieur culmine a **-4,020** (la levre du
#: canal, a x = 1,0), le pont median a **-4,960**. Un rail d'un seul tenant
#: aurait flotte de 94 cm au-dessus de l'un ou traverse l'autre. Il est donc
#: coupe a la chine, et la marche se VOIT — c'est ce qui raconte que l'artere
#: descend d'un pont a l'autre.
RAIL_IN_Y = -4.00                                  # 0,02 m au-dessus de la levre
RAIL_OUT_Y = -4.70                                 # 0,26 m au-dessus du pont median
#: Les cinq conduites et les deux coudes, du bord babord au bord tribord.
#: (x, y du BAS de la piece, fichier). Le lacet vaut +90 deg pour tout le rail :
#: la piece est modelisee le long de son Z, il faut donc la coucher en travers.
CONDUIT_LEN = 2.78
MANIFOLD_PIECES = (
    (-10.10, RAIL_OUT_Y, "bend"),
    (-7.30, RAIL_OUT_Y, "conduit"),
    (-2.79, RAIL_IN_Y, "conduit"),
    (0.00, RAIL_IN_Y, "conduit"),
    (2.79, RAIL_IN_Y, "conduit"),
    (7.30, RAIL_OUT_Y, "conduit"),
    (10.10, RAIL_OUT_Y, "bend"),
)
#: Les quatre flexibles du collecteur, aux DEUX LATERAUX DE L'ARTERE DU CORRIDOR
#: (`blc.ARTERY_CONDUITS` : 3,60 et 4,40). Ce n'est pas un alignement de gout :
#: c'est la meme ligne qui arrive et qui aboutit, et le joueur l'a suivie sur
#: 500 m.
LIAISON_X = (-4.40, -3.60, 3.60, 4.40)

#: Les pieds du portique, et leur demi-section.
GANTRY_FEET = (5.10, 7.30, 10.30)
GANTRY_FOOT_HALF = 0.36
#: La tete du collecteur : elle siege DERRIERE le rail, jamais dedans.
HEAD_Z0 = MANIFOLD_Z0
HEAD_Z1 = 8.72
HEAD_HALF_X = 1.75
HEAD_TOP = -3.35


def _corridor_y(x: float, z: float) -> float:
    """Le dessus de la peau du corridor sous le point (x, z) LOCAL a la poupe.

    ⚠️ ELLE EST LUE DANS `build_long_cortege`, JAMAIS RECOPIEE — meme regle que
    l'anneau de jonction et que la bouche de tuyere. Le collecteur est a
    `z >= 8,15`, donc de l'AUTRE cote de la jonction : le sol qu'il touche
    appartient au troncon 5 du corridor, pas a cette carene.
    """
    return blc._surface_y(STATION - z, x)


def build_manifold(bm: bmesh.types.BMesh) -> None:
    """Le PORTIQUE du collecteur : tete, pieds, selles, potences.

    Il ne contient plus une seule conduite. Ce qu'il contient, c'est ce sur quoi
    les conduites se posent — et sans quoi elles flotteraient au-dessus du pont
    (« des tuyaux qui flottent au-dessus, ca ressemble a rien », operateur,
    2026-09-08).

    ⚠️ IL EST A `z >= 8,15`, DONC HORS DE L'EMPRISE DES BERCEAUX, et c'est la
    seule position possible. Dans le bassin il mordrait un berceau ; sur la paroi
    avant il serait invisible (voir l'en-tete) ; ici il coiffe la fin du canal
    magenta et il se lit au-dessus du pont du corridor.

    ⚠️ ET IL NE PORTE PLUS D'EMISSIF. Les trois sections vitrees du tube retire
    en portaient ; les conduites instanciees ont le leur (`06 | Energie magenta`
    se replie sur `AA_Emissive_Engine`, `BRIEF-0108`), et `blackout()` les eteint
    par le meme nom de materiau. Doubler la source aurait double la lumiere au
    seul endroit du cadre ou le joueur doit encore lire ses balles.
    """
    # --- La tete : le bloc de jonction, en arriere du rail --------------------
    _box(bm, -HEAD_HALF_X, HEAD_HALF_X, -4.95, HEAD_TOP, HEAD_Z0, HEAD_Z1,
         "AA_Greeble", "AA_Hull")
    # ⚠️ SON CHAPEAU N'EST PAS EN `AA_Trim`. Rendu et regarde au BRIEF-0106 :
    # l'ivoire froid posait un rectangle BLANC de 3,7 x 1,5 m au milieu du cadre,
    # plus clair que tout le reste de l'image. Il n'en reste qu'un bandeau.
    _box(bm, -1.45, 1.45, -3.62, -3.44, HEAD_Z1, HEAD_Z1 + 0.06, "AA_Trim")
    for side in (-1.0, 1.0):
        # Les nervures de la tete.
        for i in range(2):
            xc = side * (0.62 + 0.72 * i)
            _box(bm, xc - 0.14, xc + 0.14, -4.90, HEAD_TOP + 0.10,
                 HEAD_Z1, HEAD_Z1 + 0.16, "AA_Greeble", "AA_Panel")
        # Les deux montants qui encadrent le rail, et leur linteau.
        _box(bm, side * 2.20, side * 2.90, _corridor_y(side * 2.55, HEAD_Z1),
             -3.55, HEAD_Z0 + 0.06, HEAD_Z1, "AA_Greeble", "AA_Hull")
    _box(bm, -2.90, 2.90, -3.52, -3.36, HEAD_Z0 + 0.14, HEAD_Z1 - 0.10,
         "AA_Hull", "AA_Panel")

    # --- Les pieds, poses sur la peau REELLE du corridor ----------------------
    for side in (-1.0, 1.0):
        for fx in GANTRY_FEET:
            x = side * fx
            rail_y = RAIL_IN_Y if fx < 6.0 else RAIL_OUT_Y
            base = _corridor_y(x, MANIFOLD_CZ)
            _box(bm, x - GANTRY_FOOT_HALF, x + GANTRY_FOOT_HALF, base - 0.30,
                 rail_y + 0.04, MANIFOLD_CZ - 0.44, MANIFOLD_CZ + 0.44,
                 "AA_Greeble", "AA_Hull")
            _box(bm, x - GANTRY_FOOT_HALF - 0.12, x + GANTRY_FOOT_HALF + 0.12,
                 rail_y - 0.34, rail_y - 0.16, MANIFOLD_CZ - 0.56,
                 MANIFOLD_CZ + 0.56, "AA_Panel", "AA_Panel")
        # La potence exterieure : le rail depasse le pont median de 1,4 m, et
        # c'est le coude qui s'y termine. Sans elle il pendrait dans le vide.
        _box(bm, side * 10.10, side * 11.46, RAIL_OUT_Y - 0.62, RAIL_OUT_Y - 0.02,
             MANIFOLD_CZ - 0.30, MANIFOLD_CZ + 0.30, "AA_Greeble", "AA_Hull")
        _box(bm, side * 11.10, side * 11.46,
             _corridor_y(side * 11.28, MANIFOLD_CZ) - 0.20, RAIL_OUT_Y - 0.30,
             MANIFOLD_CZ - 0.24, MANIFOLD_CZ + 0.24, "AA_Greeble", "AA_Hull")
        # Les selles : ce sur quoi chaque joint de conduite repose.
        for sx, rail_y in ((1.40, RAIL_IN_Y), (4.24, RAIL_IN_Y),
                           (8.72, RAIL_OUT_Y)):
            x = side * sx
            _box(bm, x - 0.30, x + 0.30, rail_y - 0.26, rail_y + 0.06,
                 MANIFOLD_CZ - 0.34, MANIFOLD_CZ + 0.34, "AA_Greeble", "AA_Panel")
        # La marche de chine : elle rattrape les 0,70 m entre les deux rails et
        # elle est la RAISON pour laquelle la coupure du rail se lit.
        _box(bm, side * 4.30, side * 6.10, RAIL_OUT_Y - 0.22, RAIL_IN_Y - 0.06,
             MANIFOLD_CZ - 0.40, MANIFOLD_CZ + 0.40, "AA_Hull", "AA_Greeble")


# ==========================================================================
# 4. LE REBORD DU BASSIN — des flexibles instancies, et ce qui les tient
# ==========================================================================
#  (BRIEF-0110 §2) La chaine de brides — 312 triangles de colliers identiques —
#  est retiree. `artery_hose.glb` fait le meme geste en mieux : il a ses
#  colliers, ses brins et ses quatre clips. Les flexibles ne sont pas cuits ici :
#  ce sont des reperes `CTRL | Liaison NN`.
#
#  ⚠️ MAIS PAS UN FLEXIBLE PAR BRIDE, ET PAS UN TAPIS NON PLUS. Vingt instances
#  sur 40 m de rebord coutent 6 400 triangles pour un tube de 0,28 m qui rend
#  9 px de large a 32,7 px/m : le rythme se perdrait et le budget avec. Six
#  suffisent, avec de vrais VIDES entre elles (regle du `BRIEF-0094` : « un
#  module de relief ne se pose que dans l'emprise d'une installation »).
#
#  ⚠️ ET LE RAIL DE GUIDAGE RESTE, CONTRE LA LETTRE DU BRIEF. Il n'etait pas un
#  collier : c'etait la SEULE arete horizontale de la paroi du bassin, et le
#  `BRIEF-0106` l'avait ajoutee apres avoir rendu et regarde « deux grands
#  trapezes gris de 7 m de haut, sans un pli, en plein cadre ». Six flexibles de
#  0,28 m ne rendent pas ce pli. Le retirer aurait rouvert un defaut deja mesure,
#  en silence : il est donc CONSERVE et retravaille (deux filants au lieu d'un,
#  plus une platine d'ancrage sous chaque flexible), et c'est dit ici plutot que
#  fait sans le dire.

#: Les stations des flexibles de rebord, par bord. Une piece fait 2,74 m et ne
#: peut pas enjamber une marche de bande : chaque station tient dans SA bande.
#: La bande B2 n'en porte aucune — le socle de pylone y siege (voir plus bas).
HOSE_RIM_Z = (5.90, -5.74)
#: ⚠️ IL N'Y EN A QUE DEUX PAR BORD, ET C'EST MESURE. Une piece de 2,74 m ne
#: peut pas enjamber une marche de bande (les aretes de rive sont a -6,60,
#: -5,60 et -4,60) : chaque station doit tenir dans SA bande, qui fait 5,28 a
#: 5,48 m — donc une seule piece. Et la bande B2 est prise par le socle de
#: pylone, qui occupe `z -2,50..+1,70` : il y reste 0,90 m d'un cote et 0,38 de
#: l'autre. Le fond de gorge, lui, est deja occupe par les tirets de l'anneau
#: d'artere (`GROOVE_X = 16,17`, demi-largeur 0,09) — y poser une platine de
#: 0,68 m les recouvrirait. Quatre flexibles de rebord, donc, et des vides
#: assumes : c'est le compte que la geometrie autorise, pas celui qu'on aurait
#: voulu.


def _rim_seat(z: float) -> tuple[float, float]:
    """(x, y) de l'arete de rive a la station `z` : l'assise d'un flexible."""
    band = _band_of(z)
    return band[5], band[3]


def build_rim_rails(bm: bmesh.types.BMesh) -> None:
    """Ce qui NERVURE la paroi du bassin, et les platines qui tiennent les brins.

    Deux filants horizontaux par bande — un a mi-paroi, un sous l'arete — plus
    une platine d'ancrage a chaque station de flexible. Rien d'autre : les
    brackets sont partis avec la chaine.
    """
    for _name, z_fore, z_aft, crest_y, basin_x, crest_x, _wmax in BANDS:
        z0 = max(z_aft, AFT_Z + 0.10)
        z1 = min(z_fore, APRON_FORE_Z)
        for side in (-1.0, 1.0):
            # Le filant bas, a mi-paroi : l'arete horizontale qui manquait.
            _box(bm, side * (basin_x - 0.30), side * basin_x,
                 crest_y - 3.55, crest_y - 3.05, z0, z1, "AA_Greeble", "AA_Hull")
            # Le filant haut, juste sous l'arete : il souligne le rebord et il
            # donne aux flexibles une ligne a suivre.
            _box(bm, side * (crest_x - 0.34), side * (crest_x + 0.10),
                 crest_y - 0.92, crest_y - 0.58, z0, z1, "AA_Greeble", "AA_Panel")
    # Les platines d'ancrage : une sous chaque flexible de rebord.
    for cz in HOSE_RIM_Z:
        crest_x, crest_y = _rim_seat(cz)
        for side in (-1.0, 1.0):
            _box(bm, side * (crest_x - 0.62), side * (crest_x + 0.34),
                 crest_y - 0.34, crest_y, cz - 1.55, cz + 1.55,
                 "AA_Greeble", "AA_Hull")
            for end in (-1.0, 1.0):
                _box(bm, side * (crest_x - 0.50), side * (crest_x + 0.22),
                     crest_y - 0.30, crest_y + 0.26,
                     cz + end * 1.24, cz + end * 1.52, "AA_Panel", "AA_Panel")
            # La DESCENTE : le flexible ne s'arrete pas au rebord, il plonge
            # dans le bassin. Elle habille la paroi PAR L'INSTALLATION, pas par
            # un tapis de nervures (spec §20) : deux par bord, aux deux seules
            # stations qui portent un flexible, et rien entre elles.
            _box(bm, side * (crest_x - 0.52), side * crest_x,
                 crest_y - 3.40, crest_y - 0.28, cz - 0.34, cz + 0.34,
                 "AA_Greeble", "AA_Hull")
            _box(bm, side * (crest_x - 0.66), side * (crest_x - 0.12),
                 crest_y - 3.72, crest_y - 3.34, cz - 0.46, cz + 0.46,
                 "AA_Greeble", "AA_Panel")


# ==========================================================================
# 4 bis. LES EPAULEMENTS AVANT — le relief que la face plane ne peut pas porter
# ==========================================================================
#  ⚠️ ILS SONT A `z >= 8,00`, DONC HORS EMPRISE, ET C'EST LEUR RAISON D'ETRE. La
#  face avant de la poupe est plane par obligation (voir `FORE_FACE_Z`) : elle
#  n'offre pas un centimetre de relief au moment precis ou le joueur decouvre la
#  poupe. Le seul volume libre est celui qui borde le corridor de part et d'autre,
#  `z in [8,00 ; 9,40]` et `|x| >= 11,4` — la ou le bordage s'arrete a 11,94 m. Ces
#  deux blocs etages y prennent le corridor en tenaille : ce sont eux qui donnent
#  a l'arrivee sa lecture de PORTE, et ils sont volontairement plus bas que le
#  collecteur pour ne pas lui voler l'axe.

SHOULDER_Z0 = JOINT_Z
SHOULDER_Z1 = JOINT_Z + 1.40
#: (x interieur, x exterieur, retrait en z, sommet)
SHOULDER_STAGES = (
    (11.40, 17.00, 0.00, -5.90),
    (12.55, 16.35, 0.22, -4.40),
    (13.60, 15.40, 0.46, CEILING_Y - 0.15),
)


def build_shoulders(bm: bmesh.types.BMesh) -> None:
    """Les deux epaulements de proue — trois boites, devenues une installation.

    (BRIEF-0110 §4) Ils sont AU PREMIER PLAN : mesure a la camera du jeu, ils
    tombent a **732 px sur 1080** et rendent a **45,7 px/m**, la plus forte
    densite de toute la poupe. Trois boites empilees y occupaient une place que
    leur detail ne justifiait pas.

    ⚠️ CE N'EST PAS UN TAPIS DE GREEBLES (spec §20). Le volume ne change pas d'un
    centimetre — memes trois gradins, memes emprises — et tout ce qui s'ajoute
    tient dans QUATRE gestes : la facade se nervure, le gradin bas porte une
    console de service, le gradin haut porte une bache et son collier, et l'arete
    de flanc recoit son bandeau. Rien n'est pose au hasard, rien ne depasse.

    ⚠️ ET RIEN N'EST NEUF AU-DESSUS DE `z = 8,00` VERS L'INTERIEUR : la garnison
    de poupe pose une plate-forme volante a `(14,50 ; -5,60 ; 9,20)`, dont la
    dalle couvre `x 13,16..15,84`. Les nervures de facade s'arretent donc a
    l'exterieur de cette bande ou sous son altitude — mesure par
    `_garrison_clash()`.
    """
    for side in (-1.0, 1.0):
        for i, (xi, xo, inset, top) in enumerate(SHOULDER_STAGES):
            _box(bm, side * xi, side * xo, -11.60, top,
                 SHOULDER_Z0 + inset, SHOULDER_Z1 - inset,
                 "AA_Greeble" if i == 0 else "AA_Hull", "AA_Hull")
        # --- 1. La facade se nervure -------------------------------------
        # Six raidisseurs verticaux sur la face avant du gradin bas : c'est
        # elle que le joueur voit en premier, et elle etait lisse sur 5,60 m.
        for i in range(6):
            xc = side * (11.76 + 1.02 * i)
            _box(bm, xc - 0.19, xc + 0.19, -8.80, -6.05,
                 SHOULDER_Z1 - 0.02, SHOULDER_Z1 + 0.15, "AA_Greeble", "AA_Hull")
        # Le bandeau qui les ceinture, et les deux panneaux qu'il encadre.
        _box(bm, side * 11.44, side * 16.96, -6.02, -5.94,
             SHOULDER_Z1 - 0.02, SHOULDER_Z1 + 0.19, "AA_Panel", "AA_Panel")
        _box(bm, side * 11.44, side * 16.96, -8.94, -8.86,
             SHOULDER_Z1 - 0.02, SHOULDER_Z1 + 0.19, "AA_Panel", "AA_Panel")
        # --- 2. La console de service du gradin bas -----------------------
        _box(bm, side * 15.55, side * 16.90, -5.90, -5.62,
             SHOULDER_Z0 + 0.12, SHOULDER_Z1 - 0.12, "AA_Hull", "AA_Greeble")
        for i in range(3):
            zc = SHOULDER_Z0 + 0.34 + 0.36 * i
            _box(bm, side * 15.70, side * 16.78, -5.62, -5.34,
                 zc - 0.08, zc + 0.08, "AA_Greeble", "AA_Panel")
        # --- 3. La bache du gradin haut, et son collier -------------------
        # ⚠️ LES RAYONS SONT BORNES PAR L'EMPRISE, PAS PAR LE GOUT. La bande
        # interdite s'arrete a `z = 8,00` et la bache siege a `z = 8,70` : un
        # rayon de 0,72 m y faisait redescendre le bord a 7,98, soit 0,0058 m2
        # d'ombre dans le berceau babord — refuse au centimetre carre par
        # `_keepout_bite()`, invisible a l'œil.
        _prism(bm, side * 14.50, SHOULDER_Z0 + 0.70, [0.54],
               -4.40, -3.62, 8, "AA_Hull", "AA_Greeble")
        _prism(bm, side * 14.50, SHOULDER_Z0 + 0.70, [0.62],
               -3.62, -3.44, 8, "AA_Panel", "AA_Panel")
        _cone(bm, side * 14.50, SHOULDER_Z0 + 0.70, 0.62, 0.26,
              -3.44, CEILING_Y - 0.14, 8, "AA_Greeble", "AA_Panel")
        # Les quatre contreforts de la bache.
        for i in range(4):
            ang = (0.25 + 0.5 * i) * math.pi
            bx = side * 14.50 + 0.70 * math.cos(ang)
            bz = SHOULDER_Z0 + 0.70 + 0.70 * math.sin(ang)
            _box(bm, bx - 0.13, bx + 0.13, -4.40, -3.98,
                 bz - 0.13, bz + 0.13, "AA_Greeble", "AA_Hull")
        # --- 4. Le bandeau de flanc, seul accent colore de la piece --------
        _box(bm, side * 17.02, side * 16.86, -8.60, -6.10,
             SHOULDER_Z0 + 0.24, SHOULDER_Z1 - 0.24, "AA_Panel")
        _box(bm, side * 17.02, side * 16.80, -5.72, -5.52,
             SHOULDER_Z0 + 0.10, SHOULDER_Z1 - 0.10, "AA_Greeble", "AA_Hull")


# ==========================================================================
# 5. LES SOCLES DE PYLONE — l'assise que la rive n'a jamais eue
# ==========================================================================
#  (BRIEF-0110 §3) Les quatre fuseaux etages de 60 triangles sont retires. A
#  leur place : DEUX socles, et sur chacun un `stern_pylon.glb` instancie.
#
#  ⚠️ LE PYLONE N'A D'ASSISE NULLE PART SUR LA POUPE, ET C'EST ARITHMETIQUE.
#  Il lui faut 5,30 m de ciel sous `CEILING_Y = -3,20` et 2,06 x 2,89 m de
#  plancher. Inventaire mesure, emplacement par emplacement :
#
#    arete de rive B1  -6,60  ciel 3,40 m   plancher 1,20 m  -> ni l'un ni l'autre
#    arete de rive B2  -5,60  ciel 2,40 m   plancher 2,60 m  -> pas de ciel
#    arete de rive B3  -4,60  ciel 1,40 m   plancher 3,00 m  -> pas de ciel
#    plateau du massif -8,40  ciel 5,20 m   creneau libre 2,54 x 1,78 m
#                                            -> et il rend a 143 px sur 1080,
#                                               c'est-a-dire SOUS le panneau de
#                                               score du HUD
#    sole du bassin   -12,00  ciel 8,80 m   bande libre 0,62 a 2,42 m hors
#                                            emprise de berceau -> trop etroite
#
#  Le `BRIEF-0109` avait pris la moins mauvaise (la paroi, a -8,61) et le pylone
#  y etait enterre de 3 m sur 5,30. La troisieme voie, que le brief ne propose
#  pas, est de LUI CONSTRUIRE SON ASSISE : un socle qui monte de la sole du
#  bassin jusqu'a `CEILING_Y - 5,40`, exactement la cote ou la piece tient
#  entiere sous le plafond avec 0,10 m de garde. Le pylone n'est alors enterre
#  de rien du tout, et le socle n'est pas un decor de plus : c'est la pyramide
#  de 3,40 m que le fuseau retire etait deja, en mieux.
#
#  ⚠️ ET IL RESTE DEUX, PAS QUATRE. Quatre pylones instancies coutent 10 448
#  triangles sur les 16 750 du lot : le collecteur — le morceau que le joueur
#  regarde le plus longtemps — n'aurait plus rien. « Concentrer le travail sur
#  peu de pieces » (spec §20).

#: La station des deux socles : celle de la paire AVANT des fuseaux retires.
PYLON_Z = -0.40
#: Le sommet du socle : le pylone fait 5,30 m, le plafond est a -3,20.
PYLON_SEAT_TOP = CEILING_Y - 5.40                  # -8,60
#: L'emprise du socle. `x0` est a 0,12 m de l'union des emprises de berceau
#: (15,78) et `x1` a 0,00 m du point le plus large de la bande B2 (18,50) :
#: le socle NE DEPASSE PAS de la silhouette, il la remplit.
PYLON_SEAT_X = (15.90, 18.50)
PYLON_SEAT_HZ = 2.10
#: (retrait de part et d'autre, demi-longueur en z, sommet) — trois marches.
PYLON_SEAT_STAGES = ((0.00, PYLON_SEAT_HZ, -10.10),
                     (0.12, PYLON_SEAT_HZ - 0.15, -9.35),
                     (0.24, PYLON_SEAT_HZ - 0.38, PYLON_SEAT_TOP))


def build_pylon_seats(bm: bmesh.types.BMesh) -> None:
    """Les deux socles : trois marches, deux margelles, un bandeau, des nervures.

    ⚠️ LES MARGELLES LAISSENT LE CENTRE LIBRE. Le pylone occupe
    `x 16,17..18,23` et `z -1,85..+1,04` une fois pose sur le repere : tout ce
    qui monte au-dessus de `PYLON_SEAT_TOP` est donc rejete AUX BORDS, sans quoi
    la piece s'y enfoncerait — le defaut exact que le `BRIEF-0109` a paye.
    """
    x0, x1 = PYLON_SEAT_X
    for side in (-1.0, 1.0):
        for i, (inset, hz, top) in enumerate(PYLON_SEAT_STAGES):
            _box(bm, side * (x0 + inset), side * (x1 - inset), SOLE_Y, top,
                 PYLON_Z - hz, PYLON_Z + hz,
                 "AA_Greeble" if i == 0 else "AA_Hull", "AA_Hull")
        # Les deux margelles, de part et d'autre de l'emprise de la piece.
        for a, b in ((x0 + 0.05, x0 + 0.25), (x1 - 0.26, x1 - 0.06)):
            _box(bm, side * a, side * b, PYLON_SEAT_TOP, PYLON_SEAT_TOP + 0.42,
                 PYLON_Z - PYLON_SEAT_HZ + 0.42, PYLON_Z + PYLON_SEAT_HZ - 0.42,
                 "AA_Hull", "AA_Panel")
        # Le bandeau de flanc : le seul accent colore du socle.
        _box(bm, side * (x1 - 0.20), side * (x1 - 0.04), -11.20, -9.60,
             PYLON_Z - 1.30, PYLON_Z + 1.30, "AA_Panel")
        # Les nervures de la face INTERIEURE, celle que la camera voit.
        for i in range(3):
            zc = PYLON_Z + (i - 1) * 1.30
            _box(bm, side * x0, side * (x0 + 0.18), SOLE_Y, -9.60,
                 zc - 0.24, zc + 0.24, "AA_Greeble", "AA_Panel")


# ==========================================================================
# 6. LES TOURS D'ECHANGE THERMIQUE (planche asset08)
# ==========================================================================
#  Elles se dressent sur le plateau du massif arriere, dans les DEUX creneaux
#  libres entre les trois nacelles : c'est la seule facon d'obtenir une masse
#  haute qui se lise entre les moteurs sans mordre un berceau.

TOWER_X = (-5.40, 5.40)
TOWER_Z = -10.05
#: Le ciel au-dessus du plateau du massif : `AFT_PLATEAU_Y` -> `CEILING_Y`.
#: 5,20 m — le seul volume vraiment haut de la poupe, et la tour le prend en
#: entier (socle -8,70, couronne -3,30).
TOWER_SIDES = 16
TOWER_SOCLE_SIDES = 12


def build_towers(bm: bmesh.types.BMesh) -> None:
    """Les deux tours d'echange thermique — la silhouette que 5,20 m permettent.

    (BRIEF-0110 §4) Elles ne changent pas de nature : elles s'enrichissent. Le
    plateau du massif offre **5,20 m** de ciel, contre 1,40 a 3,40 sur les
    aretes de rive — c'est le seul endroit de la poupe ou une masse haute tienne
    debout sans qu'on lui construise une assise.

    Ce qui s'ajoute, et pourquoi :

      * un socle EVASE en tronc de cone, puis un collier — une tour posee a plat
        sur un plateau n'a pas de pied ; celle-ci en a un ;
      * six contreforts au lieu de quatre, au pas de 60 deg : a 31,7 px/m, quatre
        arretes verticales sur un fut de 2 m se comptent, six font une trame ;
      * une GALERIE DE SERVICE a mi-hauteur, avec ses quatre potences — c'est
        elle qui donne l'echelle, et c'est le seul element de la piece dont on
        deduise qu'un humain (ou ce qui en tient lieu) y monte ;
      * huit volets d'evacuation sous la galerie, orientes vers le bas ;
      * un diffuseur en cone, sa grille, et quatre ailerons de couronne.

    ⚠️ ET CE N'EST PAS UN TAPIS DE GREEBLES. Tout tient sur DEUX pieces (spec
    §20) ; le plateau autour d'elles reste nu, les bossages gardent leurs
    nervures de canal et rien n'est pose « pour remplir ».

    ⚠️ ATTENTION AU CADRE : mesure a la camera du jeu au plan de maintien, la
    couronne d'une tour tombe a **-4 px sur 1080**, c'est-a-dire JUSTE HORS DU
    CADRE. Le massif arriere n'est vu en entier que pendant le survol, quelques
    secondes plus tot (vignette 2 de la planche). C'est la raison pour laquelle
    le pylone livre n'y est pas alle.
    """
    for cx in TOWER_X:
        # Socle evase + collier.
        _cone(bm, cx, TOWER_Z, 1.78, 1.52, AFT_PLATEAU_Y - 0.30, -7.95,
              TOWER_SOCLE_SIDES, "AA_Greeble", "AA_Greeble")
        _prism(bm, cx, TOWER_Z, [1.62], -7.95, -7.66, TOWER_SOCLE_SIDES,
               "AA_Hull", "AA_Panel")
        # Six contreforts, au pas de 60 deg.
        for i in range(6):
            ang = (i + 0.5) * math.pi / 3.0
            bx, bz = cx + 1.44 * math.cos(ang), TOWER_Z + 1.44 * math.sin(ang)
            _box(bm, bx - 0.30, bx + 0.30, AFT_PLATEAU_Y - 0.30, -6.55,
                 bz - 0.30, bz + 0.30, "AA_Greeble", "AA_Hull")
        # Fut cannele, en deux courses de part et d'autre de la galerie.
        _prism(bm, cx, TOWER_Z, [1.02, 0.90], -7.66, -6.28, TOWER_SIDES,
               "AA_Hull", "AA_Greeble")
        # Huit volets d'evacuation, sous la galerie.
        for i in range(8):
            ang = (i + 0.5) * math.pi / 4.0
            bx, bz = cx + 1.02 * math.cos(ang), TOWER_Z + 1.02 * math.sin(ang)
            _box(bm, bx - 0.22, bx + 0.22, -6.90, -6.42, bz - 0.22, bz + 0.22,
                 "AA_Greeble", "AA_Panel")
        # La galerie de service : le seul element qui donne l'echelle.
        _prism(bm, cx, TOWER_Z, [1.46], -6.28, -6.06, TOWER_SIDES,
               "AA_Hull", "AA_Panel")
        _prism(bm, cx, TOWER_Z, [1.30], -6.06, -5.72, TOWER_SIDES,
               "AA_Panel", "AA_Greeble")
        for i in range(4):
            ang = (i + 0.25) * math.pi / 2.0
            bx, bz = cx + 1.34 * math.cos(ang), TOWER_Z + 1.34 * math.sin(ang)
            _box(bm, bx - 0.16, bx + 0.16, -6.42, -6.06, bz - 0.16, bz + 0.16,
                 "AA_Greeble", "AA_Hull")
        _prism(bm, cx, TOWER_Z, [0.96, 0.84], -5.72, -4.55, TOWER_SIDES,
               "AA_Hull", "AA_Greeble")
        # Diffuseur, grille, et quatre ailerons de couronne.
        _cone(bm, cx, TOWER_Z, 0.96, 1.58, -4.55, CEILING_Y - 0.34,
              TOWER_SIDES, "AA_Hull", "AA_Panel")
        _prism(bm, cx, TOWER_Z, [1.58], CEILING_Y - 0.34, CEILING_Y - 0.22,
               TOWER_SIDES, "AA_Panel", "AA_Panel")
        _prism(bm, cx, TOWER_Z, [1.34], CEILING_Y - 0.22, CEILING_Y - 0.10,
               TOWER_SIDES, "AA_Greeble", "AA_Panel")
        for i in range(4):
            ang = i * math.pi / 2.0
            bx, bz = cx + 1.44 * math.cos(ang), TOWER_Z + 1.44 * math.sin(ang)
            _box(bm, bx - 0.20, bx + 0.20, CEILING_Y - 0.94, CEILING_Y - 0.30,
                 bz - 0.20, bz + 0.20, "AA_Greeble", "AA_Panel")
    # Les blocs de ventilation. ⚠️ IL Y EN AVAIT UN, AU MILIEU, ET IL ETAIT DANS LE
    # CANAL CENTRAL : `|x| <= 2,10`, `z in [-11,65 ; -8,45]`, sommet a -6,90, soit
    # 4 m de matiere en pleine colonne de poussee du moteur central. Le
    # `BRIEF-0106` avait raison de le vouloir bas ; le `BRIEF-0107` mesure qu'il ne
    # doit pas etre la du tout. Il est donc en DEUX, poses sur les bossages
    # interieurs entre le canal central et chaque tour.
    for side in (-1.0, 1.0):
        _box(bm, side * (CHANNEL_HALF + 0.35), side * (abs(TOWER_X[0]) - 1.65),
             AFT_PLATEAU_Y - 0.30, -7.05, TOWER_Z - 0.80, TOWER_Z + 0.80,
             "AA_Greeble", "AA_Hull")
        _box(bm, side * (CHANNEL_HALF + 0.55), side * (abs(TOWER_X[0]) - 1.85),
             -7.05, -6.85, TOWER_Z - 0.60, TOWER_Z + 0.60, "AA_Panel", "AA_Panel")


# ==========================================================================
# 6 bis. LES REPERES — la coque dit OU les pieces livrees se posent
# ==========================================================================
#  (BRIEF-0110) Vingt-cinq mille triangles de pieces tierces ne sont pas cuits
#  dans cette carene : ils sont INSTANCIES par le code, sur des nœuds vides que
#  ce fichier pose. Une piece dupliquee dans la carene couterait ses triangles
#  autant de fois qu'elle apparait ; instanciee, elle n'est en memoire qu'une
#  fois — et le concepteur peut en changer sans reforger la coque.
#
#  ⚠️ LE REPERE MARQUE LE **BAS** DE LA PIECE, ET SON **CENTRE** EN X ET EN Z.
#  Ce n'est pas une convention choisie ici : c'est celle que le jeu applique
#  deja (`CortegeConduit._seat()`), et elle existe parce que L'ORIGINE DES
#  PIECES N'EST PAS DANS LES PIECES. Les quatre `.glb` de l'artere sont des
#  sous-arbres extraits d'un assemblage plus grand : la racine
#  d'`artery_conduit` porte encore `(-0,36 ; 1,00 ; 1,38)`, sa translation dans
#  le module d'origine. Montee telle quelle sur un pont a -4,30, la geometrie se
#  retrouvait un metre au-dessus de la coque. Le code ne compense donc pas la
#  translation : il MESURE la boite englobante, et il pose son bas.
#
#  ⚠️ ET LE LACET DOIT ETRE UN LACET PUR. La correction d'assise (« centrer en
#  x/z, poser le bas ») commute avec une rotation autour de Y et avec elle
#  seule : un tangage ou un roulis ferait tourner la correction avec la piece et
#  l'assise partirait de travers, sans qu'aucune erreur ne le dise.
#  `_assert_markers()` refuse tout quaternion qui n'est pas un lacet — et il lit
#  le QUATERNION, jamais `to_euler()` : un quart de tour autour de Y tombe
#  exactement sur le blocage de cardan d'une decomposition XYZ.

#: Les pieces montees sur les reperes, et leur fichier.
PIECE_FILES = {
    "pylon": "stern_pylon.glb",
    "conduit": "artery_conduit.glb",
    "bend": "artery_conduit_bend.glb",
    "hose": "artery_hose.glb",
}
#: Le clip « au repos » de chaque piece — celui que la planche rend.
PIECE_REST_CLIP = {"pylon": "Service", "conduit": "Actif", "bend": "Actif",
                   "hose": "Intact"}
_PIECE_BOX: dict[str, tuple[Vector, Vector]] = {}


def _piece_box(kind: str) -> tuple[Vector, Vector]:
    """(min, max) de la piece dans SON repere, transformations de nœuds comprises.

    ⚠️ ON NE CROIT PAS LES COTES ANNONCEES. Le `BRIEF-0109` avait recu « le
    pylone fait 2,75 m en x » : le socle en mesure 2,748, mais les deux
    passerelles debordent de 7 cm de chaque cote — 14 cm d'erreur d'emprise que
    rien n'aurait dite. Le binaire, lui, ne se trompe pas.
    """
    if kind in _PIECE_BOX:
        return _PIECE_BOX[kind]
    gltf, _blob = blc._read_glb(os.path.join(MODELS, PIECE_FILES[kind]))
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))

    def node_matrix(node: dict) -> Matrix:
        if "matrix" in node:
            m = node["matrix"]
            return Matrix([[m[c * 4 + r] for c in range(4)] for r in range(4)])
        t = Vector(node.get("translation", (0.0, 0.0, 0.0)))
        q = node.get("rotation", (0.0, 0.0, 0.0, 1.0))
        sc = Vector(node.get("scale", (1.0, 1.0, 1.0)))
        rot = Quaternion((q[3], q[0], q[1], q[2])).to_matrix().to_4x4()
        return (Matrix.Translation(t) @ rot
                @ Matrix.Diagonal(sc.to_4d()))

    def walk(index: int, parent: Matrix) -> None:
        nonlocal lo, hi
        node = gltf["nodes"][index]
        world = parent @ node_matrix(node)
        if "mesh" in node:
            for prim in gltf["meshes"][node["mesh"]]["primitives"]:
                acc = gltf["accessors"][prim["attributes"]["POSITION"]]
                mn, mx = acc["min"], acc["max"]
                for corner in range(8):
                    v = Vector((mn[0] if corner & 1 else mx[0],
                                mn[1] if corner & 2 else mx[1],
                                mn[2] if corner & 4 else mx[2]))
                    w = world @ v
                    lo = Vector((min(lo[i], w[i]) for i in range(3)))
                    hi = Vector((max(hi[i], w[i]) for i in range(3)))
        for child in node.get("children", []):
            walk(child, world)

    scene = gltf["scenes"][gltf.get("scene", 0)]
    for index in scene["nodes"]:
        walk(index, Matrix.Identity(4))
    _PIECE_BOX[kind] = (lo, hi)
    return lo, hi


def _piece_extent(kind: str, yaw: float) -> tuple[float, float, float]:
    """(demi-emprise x, hauteur, demi-emprise z) de la piece POSEE et pivotee."""
    lo, hi = _piece_box(kind)
    cos_y, sin_y = math.cos(yaw), math.sin(yaw)
    xs, zs = [], []
    for corner in range(4):
        x = lo.x if corner & 1 else hi.x
        z = lo.z if corner & 2 else hi.z
        xs.append(cos_y * x + sin_y * z)
        zs.append(-sin_y * x + cos_y * z)
    return (0.5 * (max(xs) - min(xs)), hi.y - lo.y, 0.5 * (max(zs) - min(zs)))


def _deck_seat(x: float, hx: float, z: float, hz: float) -> float:
    """Le MINIMUM de la peau du corridor sous l'emprise de la piece.

    ⚠️ JAMAIS LA VALEUR AU CENTRE. Sur un bombement, prendre le centre fait
    s'enfoncer les deux bouts ; sur un creux, la piece flotte. Le minimum est la
    seule valeur qui garantisse qu'aucun coin ne passe sous la peau.
    """
    worst = 1e9
    for i in range(13):
        px = x - hx + 2.0 * hx * i / 12.0
        for j in range(13):
            pz = z - hz + 2.0 * hz * j / 12.0
            worst = min(worst, _corridor_y(px, pz))
    return worst


def markers() -> list[tuple[str, Vector, float, str]]:
    """(nom, position LOCALE, lacet, piece) — la table complete, calculee.

    Aucune cote n'y est ecrite deux fois : les x du collecteur viennent de
    `MANIFOLD_PIECES`, les y de rebord de `BANDS`, le sommet du socle de
    `PYLON_SEAT_TOP`, et les y du corridor de `blc._surface_y`.
    """
    out: list[tuple[str, Vector, float, str]] = []
    # --- Les deux pylones, sur leur socle -------------------------------
    seat_x = 0.5 * (PYLON_SEAT_X[0] + PYLON_SEAT_X[1])
    for number, side in enumerate((1.0, -1.0), start=1):
        yaw = -math.pi * 0.5 * side
        out.append((f"CTRL | Pylone {number:02d}",
                    Vector((side * seat_x, PYLON_SEAT_TOP, PYLON_Z)),
                    yaw, "pylon"))
    # --- Le collecteur : cinq conduites et deux coudes ------------------
    for number, (x, rail_y, kind) in enumerate(MANIFOLD_PIECES, start=1):
        yaw = math.pi * 0.5 if x <= 0.0 else -math.pi * 0.5
        out.append((f"CTRL | Collecteur {number:02d}",
                    Vector((x, rail_y, MANIFOLD_CZ)), yaw, kind))
    # --- Les flexibles : quatre au collecteur, quatre au rebord ---------
    number = 0
    hx, _h, hz = _piece_extent("hose", 0.0)
    for x in LIAISON_X:
        number += 1
        out.append((f"CTRL | Liaison {number:02d}",
                    Vector((x, _deck_seat(x, hx, LIAISON_CZ, hz), LIAISON_CZ)),
                    0.0, "hose"))
    for cz in HOSE_RIM_Z:
        crest_x, crest_y = _rim_seat(cz)
        for side in (1.0, -1.0):
            number += 1
            out.append((f"CTRL | Liaison {number:02d}",
                        Vector((side * crest_x, crest_y, cz)), 0.0, "hose"))
    return out


# ==========================================================================
# 7. LES TROIS CANAUX D'ECHAPPEMENT (BRIEF-0107)
# ==========================================================================
#  Le massif est bas par construction (`AFT_TOP_Y`) ; ce qui suit le REMONTE, et
#  laisse entre ses bossages les trois canaux ou passent les panaches. On ne
#  soustrait rien : c'est la seule facon d'obtenir une topologie previsible, un
#  fichier deterministe et un generateur qu'on relise.
#
#  ⚠️ ET CE N'EST PAS UNE RAINURE. « Un trou n'est pas une installation » (brief
#  §3) : la paroi est en retrait, des nervures viennent rattraper le bord exact du
#  canal, un chanfrein de 0,90 m regarde le panache par en dessous, et une levre
#  renforcee encadre la bouche. Le chanfrein est la piece qui compte — c'est lui
#  qui recoit la seule lumiere violette du niveau.

#: Le bord EXTERIEUR d'un canal lateral, 2 cm plus large que le bord interieur.
#:
#: ⚠️ CES 2 CM SONT DE LA QUANTIFICATION, PAS DU GOUT. Le glTF stocke en float32 :
#: 12,48 y devient 12,479999542, soit 4,6e-07 m DANS l'emprise mesuree. Le bord
#: interieur, lui, s'arrondit du bon cote (8,08 -> 8,079999924) et n'a pas besoin
#: de marge — ce qui laisse au socle des tours la cote pleine du brief.
CHANNEL_OUTER_HALF = CHANNEL_HALF + 0.02
#: Le retrait de la paroi ; les nervures le rattrapent jusqu'au bord du canal.
CHANNEL_RIB_DEPTH = 0.26
#: Le chanfrein qui capte la lumiere du panache : 0,70 m de large, 0,90 m de haut.
RIDGE_CHAMFER = 0.70
RIDGE_CHAMFER_RISE = 0.90
#: Le dessus des bossages : l'ancien plateau du massif, inchange.
RIDGE_TOP_Y = AFT_PLATEAU_Y
#: Les trois stations du loft d'un bossage.
RIDGE_Z = (AFT_Z, -11.20, TAIL_Z + 0.40)
#: A l'arriere le bossage s'abaisse et se pince : le canal S'OUVRE en sortant.
RIDGE_TAIL_TOP_Y = -9.25
RIDGE_TAIL_FLARE = 0.25

#: Les deux bossages de tribord — mires ensuite a babord.
#: (bord bas, bord haut, nervures cote bas, nervures cote haut)
#:
#:   2,20 -> 8,08    entre le canal central et le canal lateral ; il porte la tour
#:  12,50 -> 15,30   entre le canal lateral et le flanc ; sa moitie exterieure
#:                   s'enterre sous la rampe de flanc, et c'est voulu : le bossage
#:                   ne doit pas se lire comme une piece POSEE sur la coque.
RIDGES: tuple[tuple[float, float, bool, bool], ...] = (
    (CHANNEL_HALF, SPACING - CHANNEL_HALF, True, True),
    (SPACING + CHANNEL_OUTER_HALF, 15.30, True, False),
)
#: Materiau du segment `i -> i+1` du profil de bossage (6 entrees).
RIDGE_MATERIALS = ("AA_Greeble", "AA_Greeble", "AA_Hull",
                   "AA_Hull", "AA_Hull", "AA_Greeble")

#: Les nervures : pas, largeur, et le retrait de la premiere sur l'entree.
RIB_PITCH = 0.52
RIB_WIDTH = 0.30
RIB_INSET = 0.18
#: La levre d'entree : elle encadre la bouche et monte au-dessus du plateau.
LIP_DEPTH = 0.82
LIP_WIDTH = 1.10
LIP_TOP_Y = -7.95


def _ridge_profile(x_in: float, x_out: float, top_y: float,
                   side: float) -> list[tuple[float, float]]:
    """Le profil d'un bossage : six points, chanfreine des deux cotes.

    ⚠️ A BABORD LA LISTE EST RETOURNEE, ET CE N'EST PAS DU CONFORT. Le miroir
    `x -> -x` inverse le sens de parcours : sans le retournement le bossage
    babord sortirait a l'envers, invisible en jeu, et son volume signe annulerait
    celui de tribord — `_orient()` lirait zero et ne verrait rien. Meme piege que
    `_box()`, meme parade.
    """
    shoulder = top_y - RIDGE_CHAMFER_RISE
    pts = [(x_in, CHANNEL_FLOOR_Y), (x_out, CHANNEL_FLOOR_Y),
           (x_out, shoulder), (x_out - RIDGE_CHAMFER, top_y),
           (x_in + RIDGE_CHAMFER, top_y), (x_in, shoulder)]
    if side < 0.0:
        pts = [(-x, y) for x, y in reversed(pts)]
    return pts


def _ridge_stations(x_in: float, x_out: float, rib_in: bool,
                    rib_out: bool) -> tuple[tuple[float, float, float, float], ...]:
    """(z, bord bas, bord haut, sommet) aux trois anneaux du bossage."""
    a = x_in + (CHANNEL_RIB_DEPTH if rib_in else 0.0)
    b = x_out - (CHANNEL_RIB_DEPTH if rib_out else 0.0)
    fl_in = RIDGE_TAIL_FLARE if rib_in else 0.0
    fl_out = RIDGE_TAIL_FLARE if rib_out else 0.0
    return ((RIDGE_Z[0], a, b, RIDGE_TOP_Y),
            (RIDGE_Z[1], a, b, RIDGE_TOP_Y),
            (RIDGE_Z[2], a + fl_in, b - fl_out, RIDGE_TAIL_TOP_Y))


def build_channel_walls(bm: bmesh.types.BMesh) -> None:
    """Les quatre bossages qui remontent le massif et laissent les trois canaux.

    ⚠️ ILS S'ARRETENT A `z = -11,60` ET RIEN NE LES REFERME. « Le canal s'ouvre
    vers l'arriere, pas vers le haut » (brief) : une encoche dans le plateau
    laisserait a `z = -12` une levre que le panache traverserait encore. Les
    0,40 m qui restent sont le biseau de la peau elle-meme, deja incline.
    """
    for x_in, x_out, rib_in, rib_out in RIDGES:
        for side in (-1.0, 1.0):
            rings = []
            for z, a, b, top in _ridge_stations(x_in, x_out, rib_in, rib_out):
                profile = _ridge_profile(a, b, top, side)
                rings.append([bm.verts.new(Vector((x, y, z))) for x, y in profile])
            _cap(bm, rings[0], "AA_Hull", facing_front=True)
            for i in range(len(rings) - 1):
                _bridge(bm, rings[i], rings[i + 1], list(RIDGE_MATERIALS))
            _cap(bm, rings[-1], "AA_Greeble", facing_front=False)


def build_channel_greebles(bm: bmesh.types.BMesh) -> None:
    """Les nervures et la levre d'entree — ce qui fait du canal une piece.

    ⚠️ TOUT EST DU COTE MATIERE DU BORD, JAMAIS DEDANS. Une nervure qui saillirait
    dans le canal serait la seule chose que le panache toucherait encore : elles
    ne font que RATTRAPER le retrait de 0,26 m de la paroi, et s'arretent au bord
    exact. `_plume_intrusion()` le mesure par decoupe, pas par sommets.
    """
    for x_in, x_out, rib_in, rib_out in RIDGES:
        for side in (-1.0, 1.0):
            for edge, inward, live in ((x_in, 1.0, rib_in), (x_out, -1.0, rib_out)):
                if not live:
                    continue
                z = RIDGE_Z[0] - RIB_INSET
                while z - RIB_WIDTH >= RIDGE_Z[2] - 1e-9:
                    _box(bm, side * edge,
                         side * (edge + inward * CHANNEL_RIB_DEPTH),
                         CHANNEL_FLOOR_Y, RIDGE_TOP_Y - RIDGE_CHAMFER_RISE,
                         z - RIB_WIDTH, z, "AA_Greeble", "AA_Panel")
                    z -= RIB_PITCH
                # La levre renforcee : elle epaissit la bouche et monte 0,45 m
                # au-dessus du plateau, la ou le panache est le plus vif.
                _box(bm, side * edge, side * (edge + inward * LIP_WIDTH),
                     RIDGE_TOP_Y - RIDGE_CHAMFER_RISE, LIP_TOP_Y,
                     AFT_Z - LIP_DEPTH, AFT_Z, "AA_Hull", "AA_Hull")
                _box(bm, side * (edge + inward * 0.14),
                     side * (edge + inward * (LIP_WIDTH - 0.14)),
                     LIP_TOP_Y, LIP_TOP_Y + 0.16,
                     AFT_Z - LIP_DEPTH + 0.14, AFT_Z - 0.14, "AA_Panel", "AA_Panel")


# ==========================================================================
# Assemblage
# ==========================================================================

PARTS = (
    ("skin", build_skin, True),
    ("apron", build_apron, True),
    ("manifold", build_manifold, True),
    ("rim_rails", build_rim_rails, True),
    ("shoulders", build_shoulders, True),
    ("pylon_seats", build_pylon_seats, True),
    ("towers", build_towers, True),
    # ⚠️ LES BOSSAGES SONT UNE FAMILLE A PART, ET C'EST UNE PRECAUTION. `_orient()`
    # retourne un composant ENTIER au signe de son volume : melanger dans un meme
    # BMesh des lofts et des boites de bobinage oppose donnerait une somme
    # positive et laisserait la moitie des faces vers l'interieur — invisibles en
    # jeu, muettes au journal. Chaque famille repond de son propre signe.
    ("channel_walls", build_channel_walls, True),
    ("channel_greebles", build_channel_greebles, True),
    ("glow", build_glow_ring, False),      # rubans plats : pas de volume
)


def build_hull() -> bpy.types.Object:
    ak.set_faction(ak.FACTION_NULL_CHOIR)
    bm = bmesh.new()
    stats: dict[str, int] = {}
    for name, builder, closed in PARTS:
        piece = bmesh.new()
        builder(piece)
        if closed:
            _orient(piece, name)
        stats[name] = sum(len(f.verts) - 2 for f in piece.faces)
        mesh = bpy.data.meshes.new("_tmp_" + name)
        piece.to_mesh(mesh)
        piece.free()
        bm.from_mesh(mesh)
        bpy.data.meshes.remove(mesh)
    obj = _new_object("SternHull", bm)
    _weld(obj)
    ak.triangulate(obj)
    _project_uv(obj)
    obj["parts"] = json.dumps(stats)
    return obj


def _weld(obj: bpy.types.Object, dist: float = 1e-5) -> None:
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=dist)
    bm.to_mesh(obj.data)
    bm.free()


def _project_uv(obj: bpy.types.Object) -> None:
    """Projection en boite a la densite du corridor, dans un repere DECALE.

    Le decalage (`UV_SHIFT_Z`) met `v` en phase avec le troncon 5 a la jonction :
    sans lui, la carte y sauterait de 0,6 tuile. Voir l'en-tete.
    """
    obj.data.transform(Matrix.Translation(Vector((0.0, 0.0, UV_SHIFT_Z))))
    ak.box_project_uv(obj, TEXELS_PER_METER)
    obj.data.transform(Matrix.Translation(Vector((0.0, 0.0, -UV_SHIFT_Z))))
    obj.data.update()


# ==========================================================================
# Export — meme chaine d'axes que `build_long_cortege`, verifiee
# ==========================================================================

_AUTHOR_FIX = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))


def _author(v: Vector) -> Vector:
    return Vector((v.x, -v.z, v.y))


def export(obj: bpy.types.Object, filepath: str) -> dict:
    blc._assert_axis_chain()
    obj.data.transform(_AUTHOR_FIX)
    obj.data.update()
    obj.location = (0.0, 0.0, 0.0)
    # ⚠️ PARENTAGE DIRECT (jamais `parent_set`) : Blender appliquerait sinon
    # l'inverse de la matrice du parent et le repere partirait deux fois.
    # ⚠️ ET LE LACET EST UNE ROTATION AUTOUR DE **Z BLENDER** : le Z de Blender
    # est le Y de Godot (`_to_blender` : (x, y, z) -> (x, -z, y)). Ecrire le
    # lacet autour de Y ici le poserait autour de l'axe de roulis du jeu.
    empties: list[bpy.types.Object] = []
    for name, local, yaw, _kind in markers():
        empty = bpy.data.objects.new(name, None)
        empty.empty_display_type = "PLAIN_AXES"
        empty.empty_display_size = 0.6
        bpy.context.collection.objects.link(empty)
        empty.parent = obj
        empty.matrix_parent_inverse = Matrix.Identity(4)
        empty.location = _author(local)
        empty.rotation_euler = Euler((0.0, 0.0, yaw), "XYZ")
        empties.append(empty)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    for empty in empties:
        empty.select_set(True)
    bpy.context.view_layer.objects.active = obj
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    staging = tempfile.mkdtemp(prefix="aegis-stern-hull-")
    staged = os.path.join(staging, os.path.basename(filepath))
    try:
        bpy.ops.export_scene.gltf(
            filepath=staged, export_format="GLB", export_yup=True,
            export_apply=True, use_selection=True, export_materials="EXPORT",
            export_cameras=False, export_lights=False, export_animations=False,
            export_skins=False, export_extras=False, export_tangents=True,
            export_normals=True, export_texcoords=True)
        report = _audit(staged)
        report["markers"] = _assert_markers(staged)
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


def _clip(poly: list[tuple[float, float]], x0: float, x1: float,
          z0: float, z1: float) -> list[tuple[float, float]]:
    """Sutherland-Hodgman : le polygone (x, z) rogne par le rectangle."""
    def half(pts, keep, coord, value, sign):
        out = []
        n = len(pts)
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            da = sign * (a[coord] - value)
            db = sign * (b[coord] - value)
            if da >= 0.0:
                out.append(a)
            if (da >= 0.0) != (db >= 0.0):
                t = da / (da - db)
                out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
        return out
    poly = half(poly, None, 0, x0, 1.0)
    if not poly:
        return []
    poly = half(poly, None, 0, x1, -1.0)
    if not poly:
        return []
    poly = half(poly, None, 1, z0, 1.0)
    if not poly:
        return []
    return half(poly, None, 1, z1, -1.0)


def _area(poly: list[tuple[float, float]]) -> float:
    total = 0.0
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        total += a[0] * b[1] - b[0] * a[1]
    return abs(total) * 0.5


def _keepout_bite(points: list[tuple], tris: list[tuple[int, int, int]]) -> dict:
    """Quelle aire de decor DEPASSE dans une emprise de berceau ?

    ⚠️ MESURE EXACTE, PAS UN TEST DE SOMMETS. Un triangle peut traverser une
    emprise sans qu'aucun de ses trois sommets n'y soit. On coupe donc chaque
    triangle par le demi-espace `y > pont`, puis on rogne son ombre (x, z) par le
    rectangle : ce qui reste est de l'aire volee a un berceau, en metres carres.
    """
    worst = 0.0
    total = 0.0
    where: tuple | None = None
    for ia, ib, ic in tris:
        tri = [Vector(points[i]) for i in (ia, ib, ic)]
        if max(v.y for v in tri) <= DECK_Y + 1e-4:
            continue
        # Decoupe par y > DECK_Y.
        above: list[Vector] = []
        for i in range(3):
            a, b = tri[i], tri[(i + 1) % 3]
            da, db = a.y - DECK_Y, b.y - DECK_Y
            if da > 1e-4:
                above.append(a)
            if (da > 1e-4) != (db > 1e-4):
                t = da / (da - db)
                above.append(a + (b - a) * t)
        if len(above) < 3:
            continue
        shadow = [(v.x, v.z) for v in above]
        for cx in ENGINE_X:
            piece = _clip(shadow, cx - KEEPOUT_HALF_X, cx + KEEPOUT_HALF_X,
                          -KEEPOUT_HALF_Z, KEEPOUT_HALF_Z)
            if len(piece) < 3:
                continue
            area = _area(piece)
            if area > 1e-6:
                total += area
                if area > worst:
                    worst = area
                    where = (cx, min(v.y for v in above), max(v.y for v in above))
    return {"area": total, "worst": worst, "where": where}


def _above(tri: list, level: float) -> list:
    """La part du triangle qui est au-dessus de `level` en y, decoupee."""
    out: list = []
    for i in range(3):
        a, b = tri[i], tri[(i + 1) % 3]
        da, db = a.y - level, b.y - level
        if da > 0.0:
            out.append(a)
        if (da > 0.0) != (db > 0.0):
            t = da / (da - db)
            out.append(a + (b - a) * t)
    return out


def _plume_intrusion(points: list[tuple], tris: list[tuple[int, int, int]],
                     level: float = CHANNEL_CLEAR_Y,
                     half: float = CHANNEL_HALF) -> dict:
    """Quelle aire de coque reste dans le volume des trois panaches ?

    ⚠️ MESURE EXACTE, PAS UN TEST DE SOMMETS — c'est le harnais d'emprise du
    `BRIEF-0106` §5, applique a un autre volume. Un triangle peut traverser un
    canal sans qu'aucun de ses trois sommets n'y soit, et c'est exactement ce que
    faisait l'arete 4 -> 5 du massif : ses deux sommets etaient dehors, son milieu
    mordait 0,90 m dans le canal lateral.

    On coupe chaque triangle par le demi-espace `y > level`, puis on rogne son
    ombre (x, z) par le rectangle du canal. Ce qui reste est de la matiere volee a
    un panache, en metres carres.
    """
    total = 0.0
    worst = 0.0
    where: tuple | None = None
    for ia, ib, ic in tris:
        tri = [Vector(points[i]) for i in (ia, ib, ic)]
        if max(v.y for v in tri) <= level:
            continue
        above = _above(tri, level)
        if len(above) < 3:
            continue
        shadow = [(v.x, v.z) for v in above]
        for cx in CHANNEL_X:
            piece = _clip(shadow, cx - half, cx + half, TAIL_Z - 40.0, CHANNEL_Z0)
            if len(piece) < 3:
                continue
            area = _area(piece)
            if area > 1e-9:
                total += area
                if area > worst:
                    worst = area
                    where = (cx, min(v.y for v in above), max(v.y for v in above))
    return {"area": total, "worst": worst, "where": where}


def _channel_clearance(points: list[tuple],
                       tris: list[tuple[int, int, int]]) -> list[dict]:
    """Le canal, RELU dans le binaire : demi-largeur libre et fond reel.

    ⚠️ LES DEUX SE MESURENT, ILS NE SE DEDUISENT PAS DE LA TABLE DE COTES. La
    demi-largeur est le plus petit `|x - station|` d'un fragment de matiere reste
    au-dessus de la ligne de degagement ; le fond est trouve par dichotomie sur
    cette meme ligne — le plus bas niveau ou l'emprise est encore vide. Les deux
    voient donc la geometrie APRES triangulation, soudure et quantification
    float32, ce qui est le seul etat qui compte.
    """
    out: list[dict] = []
    for cx in CHANNEL_X:
        widest = 9e9
        for ia, ib, ic in tris:
            tri = [Vector(points[i]) for i in (ia, ib, ic)]
            if max(v.y for v in tri) <= CHANNEL_CLEAR_Y:
                continue
            above = _above(tri, CHANNEL_CLEAR_Y)
            if len(above) < 3:
                continue
            piece = _clip([(v.x, v.z) for v in above], cx - 6.0, cx + 6.0,
                          TAIL_Z - 40.0, CHANNEL_Z0)
            if len(piece) < 3 or _area(piece) <= 1e-9:
                continue
            widest = min(widest, min(abs(px - cx) for px, _ in piece))
        low, high = KEEL_Y, CEILING_Y
        for _ in range(28):
            mid = 0.5 * (low + high)
            if _plume_intrusion(points, tris, mid)["area"] > 1e-9:
                low = mid
            else:
                high = mid
        out.append({"x": cx, "clear_half": widest, "floor": high,
                    "over_sole": high - SOLE_Y})
    return out


def _tower_margin(points: list[tuple]) -> list[dict]:
    """Le socle des deux tours d'echange, RELU, et sa marge aux canaux.

    ⚠️ « VERIFIEZ-LE SUR LE BINAIRE PLUTOT QUE SUR CETTE PHRASE — c'est la cote la
    plus serree du lot » (brief §2). On isole le socle par l'altitude de son
    anneau LE PLUS LARGE, `y = AFT_PLATEAU_Y - 0,30` : le pied evase du
    `BRIEF-0110` y mesure 1,78 m de rayon, contre 1,52 pour le prisme droit qu'il
    remplace. C'est cette cote-la, et pas celle du fut, qui decide de la marge au
    canal.

    ⚠️ ET L'ALTITUDE DE MESURE A CHANGE AVEC LA PIECE. Le harnais interrogeait
    `y = -7,55`, le sommet de l'ancien socle : la tour enrichie n'a plus un seul
    sommet a cette hauteur, et le harnais a echoue le build — comme il devait. Une
    cote de controle qui suit la piece sans qu'on y pense n'existe pas ; celle-ci
    est derivee de `AFT_PLATEAU_Y`, que les deux partagent.
    """
    out: list[dict] = []
    level = AFT_PLATEAU_Y - 0.30
    for cx in TOWER_X:
        ring = [p for p in points
                if abs(p[1] - level) < 1e-3
                and abs(p[0] - cx) < 2.0 and abs(p[2] - TOWER_Z) < 2.0]
        if not ring:
            raise ak.ContractError(
                f"tour x = {cx:+.2f} : plus de socle a y = {level:.2f} dans le "
                "binaire — le creusement du massif l'a emportee.")
        radius = max(abs(p[0] - cx) for p in ring)
        margins = {
            "x": cx,
            "radius": radius,
            "to_side": (SPACING - CHANNEL_HALF) - (abs(cx) + radius),
            "to_middle": (abs(cx) - radius) - CHANNEL_HALF,
        }
        if min(margins["to_side"], margins["to_middle"]) < 0.0:
            raise ak.ContractError(
                f"tour x = {cx:+.2f} : socle de {radius:.3f} m de rayon — marge "
                f"au canal lateral {margins['to_side']:+.3f} m, au canal central "
                f"{margins['to_middle']:+.3f} m ; l'une est NEGATIVE, la tour "
                "entre dans un panache")
        out.append(margins)
    return out


def _glow_in_channels(points: list[tuple], tris: list[tuple[int, int, int]],
                      tri_material: list[str]) -> float:
    """L'aire d'`AA_Emissive_Engine` qui tombe dans un canal — doit valoir zero.

    ⚠️ UN CANAL QUI BRILLE DE LUI-MEME RESTE ALLUME SUR UN VAISSEAU MORT.
    `CortegeStern.blackout()` n'eteint que ce qui porte ce materiau ; l'inverse —
    de l'emissif la ou le panache doit fournir la lumiere — ne produirait ni
    erreur, ni test rouge, seulement trois rainures lumineuses sous une epave.
    """
    total = 0.0
    for (ia, ib, ic), name in zip(tris, tri_material):
        if name != "AA_Emissive_Engine":
            continue
        tri = [Vector(points[i]) for i in (ia, ib, ic)]
        shadow = [(v.x, v.z) for v in tri]
        for cx in CHANNEL_X:
            piece = _clip(shadow, cx - CHANNEL_HALF, cx + CHANNEL_HALF,
                          TAIL_Z - 40.0, CHANNEL_Z0)
            if len(piece) >= 3:
                total += _area(piece)
    return total


def _audit(path: str) -> dict:
    gltf, blob = blc._read_glb(path)
    if gltf.get("images"):
        raise ak.ContractError(
            f"{path} : {len(gltf['images'])} image(s) embarquee(s) — "
            "le regime du niveau est le PBR par facteurs (ADR-0028).")

    report: dict = {"path": path, "bytes": os.path.getsize(path)}
    materials = [m.get("name", "?") for m in gltf.get("materials", [])]
    points: list[tuple] = []
    uvs: list[tuple] = []
    tris: list[tuple[int, int, int]] = []
    tri_material: list[str] = []
    per_material: dict[str, float] = {}
    triangles = 0
    for mesh in gltf.get("meshes", []):
        for prim in mesh.get("primitives", []):
            attrs = prim["attributes"]
            if "TEXCOORD_0" not in attrs:
                raise ak.ContractError(
                    f"{path} : primitive sans TEXCOORD_0 — un maillage sans UV "
                    "est definitivement inhabitable (ADR-0028).")
            base = len(points)
            pos = ak.glb_accessor(gltf, blob, attrs["POSITION"])
            uv = ak.glb_accessor(gltf, blob, attrs["TEXCOORD_0"])
            points.extend(pos)
            uvs.extend(uv)
            idx = ak.glb_accessor(gltf, blob, prim["indices"])
            flat = [i[0] for i in idx]
            name = materials[prim["material"]] if "material" in prim else "?"
            area = 0.0
            for k in range(0, len(flat), 3):
                a, b, c = (base + flat[k + j] for j in range(3))
                tris.append((a, b, c))
                tri_material.append(name)
                va, vb, vc = (Vector(points[i]) for i in (a, b, c))
                area += (vb - va).cross(vc - va).length * 0.5
            triangles += len(flat) // 3
            per_material[name] = per_material.get(name, 0.0) + area

    report["triangles"] = triangles
    report["vertices"] = len(points)
    report["materials"] = per_material
    total_area = sum(per_material.values())
    report["area"] = total_area
    glow = per_material.get("AA_Emissive_Engine", 0.0)
    report["glow_area"] = glow
    report["glow_share"] = glow / total_area if total_area else 0.0
    if glow <= 0.0:
        raise ak.ContractError("aucun AA_Emissive_Engine : l'artere n'arrive nulle part")

    if triangles > TRI_BUDGET:
        raise ak.ContractError(
            f"{triangles} triangles pour un budget de {TRI_BUDGET}")

    ys = [p[1] for p in points]
    report["y_min"], report["y_max"] = min(ys), max(ys)
    if report["y_max"] > CEILING_Y + 1e-6:
        raise ak.ContractError(
            f"plafond creve : y_max = {report['y_max']:.3f} > {CEILING_Y}")
    if report["y_min"] < KEEL_Y - 1e-6:
        raise ak.ContractError(
            f"sous la quille : y_min = {report['y_min']:.3f} < {KEEL_Y}")

    zs = [p[2] for p in points]
    report["z_min"], report["z_max"] = min(zs), max(zs)
    report["half_width"] = max(abs(p[0]) for p in points)
    if report["half_width"] < 18.0:
        raise ak.ContractError(
            f"demi-largeur {report['half_width']:.2f} < 18 m : l'evasement "
            "demande par le brief n'est pas atteint")

    bite = _keepout_bite(points, tris)
    report["keepout"] = bite
    if bite["area"] > 1e-6:
        raise ak.ContractError(
            f"{bite['area']:.4f} m2 de decor dans l'emprise d'un berceau "
            f"(pire triangle {bite['worst']:.4f} m2, {bite['where']})")

    # --- BRIEF-0107 : les trois canaux ------------------------------------
    plume = _plume_intrusion(points, tris)
    report["plume"] = plume
    if plume["area"] > 1e-9:
        raise ak.ContractError(
            f"{plume['area']:.6f} m2 de coque dans le volume d'un panache "
            f"(pire triangle {plume['worst']:.6f} m2, {plume['where']}) — "
            "le massif retraverse la plume.")
    report["channels"] = _channel_clearance(points, tris)
    for chan in report["channels"]:
        if chan["clear_half"] < CHANNEL_HALF - 1e-6:
            raise ak.ContractError(
                f"canal x = {chan['x']:+.2f} : demi-largeur libre "
                f"{chan['clear_half']:.3f} m < {CHANNEL_HALF} m")
        if chan["floor"] > CHANNEL_CLEAR_Y + 1e-6:
            raise ak.ContractError(
                f"canal x = {chan['x']:+.2f} : fond a {chan['floor']:.3f} m, "
                f"au-dessus de la ligne de degagement {CHANNEL_CLEAR_Y}")
        if chan["over_sole"] < 1.0 - 1e-6:
            raise ak.ContractError(
                f"canal x = {chan['x']:+.2f} : {chan['over_sole']:.3f} m de "
                f"matiere au-dessus de SOLE_Y ({SOLE_Y}) — la coque se perce.")
    report["towers"] = _tower_margin(points)
    report["glow_in_channels"] = _glow_in_channels(points, tris, tri_material)
    if report["glow_in_channels"] > 1e-9:
        raise ak.ContractError(
            f"{report['glow_in_channels']:.4f} m2 d'AA_Emissive_Engine dans un "
            "canal : il resterait allume sur un vaisseau mort (blackout).")

    report["junction"] = _assert_junction(points)
    report["uv"] = ak.texel_density(points, uvs, tris)
    report["width_profile"] = _width_profile(points, tris)
    return report


#: L'emprise de la garnison de poupe (`cortege_stern_garrison.gd`), qui n'est
#: PAS dans ce fichier et n'a pas a y etre : on la relit pour MESURER ce qu'on
#: lui prend, pas pour s'y plier. (echelle, x, y, z, plate-forme volante)
GARRISON_POSTS = (
    ("STANDARD", 4.60, -4.34, 12.50, False),
    ("LIGHT", 8.60, -4.94, 13.00, False),
    ("LIGHT", 11.50, -4.20, 10.50, True),
    ("LIGHT", 14.50, -5.60, 9.20, True),
    ("STANDARD", 17.00, -7.20, 2.00, True),
    ("HEAVY", 16.80, -5.20, -4.50, True),
)
#: `CortegeTurret.SERVICE_RADIUS` et les deux facteurs d'echelle geometrique.
GARRISON_RADIUS = {"LIGHT": 1.66 * 0.538, "STANDARD": 1.66, "HEAVY": 1.66 * 1.200}
#: `CortegeSternGarrison`: la dalle vaut `footprint * 2 + 0,9`, epaisseur 0,52,
#: et elle ballotte de +/- 0,22.
GARRISON_PAD_MARGIN = 0.9
GARRISON_PAD_THICK = 0.52
GARRISON_PAD_BOB = 0.22


def _garrison_clash(boxes: list[tuple[str, list, list, list]]) -> list[dict]:
    """Ce que les pieces posees prennent aux plates-formes volantes de la garnison.

    ⚠️ CE N'EST PAS UN HARNAIS BLOQUANT, ET C'EST DELIBERE. La garnison de poupe
    n'appartient pas a ce fichier (`BRIEF-0110` : « le code de jeu est hors
    perimetre ») et le recouvrement PREEXISTE : les quatre fuseaux retires
    etaient deja traverses par les deux dalles de la reserve. On le MESURE et on
    le dit, au lieu de le corriger dans le dos du concepteur ou de le taire.
    """
    out: list[dict] = []
    for scale, px, py, pz, flying in GARRISON_POSTS:
        if not flying:
            continue
        half = GARRISON_RADIUS[scale] + 0.5 * GARRISON_PAD_MARGIN
        for sign in (1.0, -1.0):
            cx = sign * px
            pad = ([cx - half, cx + half],
                   [py - 0.5 * GARRISON_PAD_THICK - GARRISON_PAD_BOB,
                    py + 0.5 * GARRISON_PAD_THICK + GARRISON_PAD_BOB],
                   [pz - half, pz + half])
            for name, bx, by, bz in boxes:
                over = [min(a[1], b[1]) - max(a[0], b[0])
                        for a, b in zip((bx, by, bz), pad)]
                if min(over) <= 0.0:
                    continue
                out.append({"piece": name, "poste": f"{scale} ({cx:+.2f} ; "
                                                    f"{pz:+.2f}) volante",
                            "x": over[0], "y": over[1], "z": over[2],
                            "volume": over[0] * over[1] * over[2]})
    return out


def _assert_markers(path: str) -> dict:
    """Relit les reperes DANS le binaire et verifie chaque piece POSEE.

    Ce que ce harnais refuse, et pourquoi chaque refus est arrive une fois :

      * un repere absent, en trop, ou dont la pose derive du micron ;
      * un quaternion qui n'est pas un lacet pur (l'assise ne commuterait plus) ;
      * une piece qui creve `CEILING_Y` — c'est ce que le `BRIEF-0109` a mesure
        avant de reculer, et c'est ce qui a fait ecrire `PYLON_SEAT_TOP` ;
      * une piece qui mord l'emprise des berceaux (`|x| <= 15,78`,
        `|z| <= 8,00`, au-dessus du pont) ;
      * une piece qui entre dans un canal d'echappement.
    """
    gltf, _blob = blc._read_glb(path)
    found: dict[str, dict] = {}
    for node in gltf.get("nodes", []):
        name = node.get("name", "")
        if not name.startswith("CTRL | "):
            continue
        found[name] = node
    table = markers()
    for name, local, yaw, _kind in table:
        if name not in found:
            raise ak.ContractError(
                f"{path} : repere « {name} » absent du binaire — le code n'a "
                "nulle part ou monter sa piece")
    for name in found:
        if name not in {n for n, _p, _y, _k in table}:
            raise ak.ContractError(f"{path} : repere inattendu « {name} »")

    rows: list[dict] = []
    boxes: list[tuple[str, list, list, list]] = []
    for name, local, yaw, kind in table:
        node = found[name]
        pose = Vector(node.get("translation", (0.0, 0.0, 0.0)))
        drift = (pose - local).length
        if drift > 1e-5:
            raise ak.ContractError(
                f"{name} : pose {tuple(round(v, 4) for v in pose)} au lieu de "
                f"{tuple(round(v, 4) for v in local)} — ecart {drift:.2e} m")
        q = node.get("rotation", (0.0, 0.0, 0.0, 1.0))
        quat = Quaternion((q[3], q[0], q[1], q[2]))
        # ⚠️ LE QUATERNION, JAMAIS `to_euler()` : un quart de tour autour de Y
        # tombe exactement sur le blocage de cardan d'une decomposition XYZ.
        want = Quaternion(Vector((0.0, 1.0, 0.0)), yaw)
        if min((quat - want).magnitude, (quat + want).magnitude) > 1e-5:
            raise ak.ContractError(
                f"{name} : la rotation n'est pas le lacet attendu "
                f"({math.degrees(yaw):+.1f} deg) — l'assise ne commute plus")
        hx, height, hz = _piece_extent(kind, yaw)
        box_x = [pose.x - hx, pose.x + hx]
        box_y = [pose.y, pose.y + height]
        box_z = [pose.z - hz, pose.z + hz]
        if box_y[1] > CEILING_Y + 1e-6:
            raise ak.ContractError(
                f"{name} : la piece culmine a {box_y[1]:.3f} > plafond "
                f"{CEILING_Y} — elle ne rentre pas a cet emplacement")
        if (box_x[0] < KEEPOUT_X - 1e-6 and box_z[0] < KEEPOUT_HALF_Z - 1e-6
                and box_x[1] > -KEEPOUT_X + 1e-6
                and box_z[1] > -KEEPOUT_HALF_Z + 1e-6
                and box_y[1] > DECK_Y + 1e-6):
            raise ak.ContractError(
                f"{name} : la piece mord l'emprise des berceaux "
                f"(x {box_x[0]:.2f}..{box_x[1]:.2f}, z {box_z[0]:.2f}.."
                f"{box_z[1]:.2f})")
        for chan_x in CHANNEL_X:
            if (box_z[0] < CHANNEL_Z0 and box_y[1] > CHANNEL_CLEAR_Y
                    and abs(pose.x - chan_x) < CHANNEL_HALF + hx):
                raise ak.ContractError(
                    f"{name} : la piece entre dans le canal x = {chan_x:+.2f}")
        rows.append({"name": name, "piece": PIECE_FILES[kind], "yaw": yaw,
                     "pos": (pose.x, pose.y, pose.z),
                     "box": (box_x, box_y, box_z),
                     "headroom": CEILING_Y - box_y[1],
                     "triangles": _piece_triangles(kind)})
        boxes.append((name, box_x, box_y, box_z))
    return {"rows": rows, "garrison": _garrison_clash(boxes)}


_PIECE_TRIS: dict[str, int] = {}


def _piece_triangles(kind: str) -> int:
    if kind in _PIECE_TRIS:
        return _PIECE_TRIS[kind]
    gltf, _blob = blc._read_glb(os.path.join(MODELS, PIECE_FILES[kind]))
    total = 0
    for mesh in gltf.get("meshes", []):
        for prim in mesh.get("primitives", []):
            total += gltf["accessors"][prim["indices"]]["count"] // 3
    _PIECE_TRIS[kind] = total
    return total


def _assert_junction(points: list[tuple]) -> dict:
    """Les 48 sommets du corridor doivent etre LA, au micron, des deux bords."""
    wanted = _joint_ring()
    worst = 0.0
    missing: list[str] = []
    fore = [p for p in points if abs(p[2] - JOINT_Z) < 1e-4]
    for i, (x, y) in enumerate(wanted):
        best = min((abs(p[0] - x) + abs(p[1] - y) for p in fore), default=9e9)
        worst = max(worst, best)
        if best > 1e-6:
            missing.append(f"#{i} ({x:+.6f} ; {y:+.6f}) ecart {best:.3e}")
    if missing:
        raise ak.ContractError(
            "l'anneau de jonction n'est pas celui du corridor : "
            + " | ".join(missing[:6]))
    return {"points": len(wanted), "worst": worst, "at_z": JOINT_Z,
            "half_width": max(abs(x) for x, _ in wanted)}


def _width_profile(points: list[tuple], tris: list) -> list[tuple[float, float]]:
    """La demi-largeur station par station, COUPEE dans le binaire.

    ⚠️ ON COUPE, ON NE CHERCHE PAS LES SOMMETS PROCHES. La peau est un loft a dix
    anneaux : entre deux marches il n'y a aucun sommet, et une mesure « sommets a
    moins de 30 cm » y rendait zero — la coque paraissait disparaitre sur six
    stations. On intersecte donc chaque triangle par le plan de la station et on
    prend le |x| maximum du segment obtenu.
    """
    out: list[tuple[float, float]] = []
    z = JOINT_Z
    while z >= TAIL_Z - 1e-9:
        widest = 0.0
        for ia, ib, ic in tris:
            tri = [points[i] for i in (ia, ib, ic)]
            zs = [v[2] for v in tri]
            if min(zs) > z or max(zs) < z:
                continue
            for i in range(3):
                a, b = tri[i], tri[(i + 1) % 3]
                if (a[2] - z) * (b[2] - z) > 0.0:
                    continue
                if abs(b[2] - a[2]) < 1e-12:
                    widest = max(widest, abs(a[0]), abs(b[0]))
                    continue
                t = (z - a[2]) / (b[2] - a[2])
                widest = max(widest, abs(a[0] + (b[0] - a[0]) * t))
        out.append((STATION - z, widest))
        z -= 1.0
    return out


# ==========================================================================
# Orchestration
# ==========================================================================


def build() -> dict:
    ak.reset_scene()
    obj = build_hull()
    parts = json.loads(obj["parts"])
    report = export(obj, OUTPUT)
    report["parts"] = parts
    return report


def _print(report: dict) -> None:
    print("")
    print("=" * 78)
    print("  LA POUPE DU LONG CORTEGE — carene (BRIEF-0106) creusee (BRIEF-0107)")
    print("=" * 78)
    print(f"  {report['path']}")
    print(f"  {report['bytes'] / 1024:.1f} Kio · {report['triangles']} triangles "
          f"/ {TRI_BUDGET} ({100.0 * report['triangles'] / TRI_BUDGET:.1f} %) · "
          f"{report['vertices']} sommets")
    print("")
    print("  Par famille (triangles avant soudure) :")
    for name, count in sorted(report["parts"].items(), key=lambda kv: -kv[1]):
        print(f"    {name:<12} {count:>6}")
    print("")
    print("  Emprise :")
    print(f"    y  {report['y_min']:+8.3f} .. {report['y_max']:+8.3f}   "
          f"(quille {KEEL_Y} · plafond {CEILING_Y})")
    print(f"    z  {report['z_min']:+8.3f} .. {report['z_max']:+8.3f}   "
          f"(s = {STATION - report['z_max']:.2f} .. {STATION - report['z_min']:.2f})")
    print(f"    demi-largeur max {report['half_width']:.3f} m")
    print("")
    j = report["junction"]
    print(f"  Jonction s = {JOINT_S:.0f} (z = {j['at_z']:+.2f}) : {j['points']} "
          f"sommets, ecart max {j['worst']:.2e} m, demi-largeur "
          f"{j['half_width']:.3f} m")
    k = report["keepout"]
    print(f"  Emprise des berceaux : {k['area']:.6f} m2 de decor au-dessus du pont "
          f"(pire {k['worst']:.6f})")
    print("")
    print("  Les trois canaux d'echappement (BRIEF-0107) :")
    print(f"    matiere dans le volume des panaches : {report['plume']['area']:.9f} m2 "
          f"(au-dessus de y = {CHANNEL_CLEAR_Y}, |x - station| <= {CHANNEL_HALF}, "
          f"z <= {CHANNEL_Z0})")
    for chan in report["channels"]:
        central = abs(chan["x"]) < 1e-9
        y_axis, z0, z1 = _plume_axis(central)
        print(f"    x = {chan['x']:+7.2f}  demi-largeur libre "
              f"{chan['clear_half']:6.3f} m (panache {PLUME_HALF:.3f}, garde "
              f"{chan['clear_half'] - PLUME_HALF:.3f})  ·  fond "
              f"{chan['floor']:+7.3f} m ({chan['floor'] - (y_axis - PLUME_HALF):+.3f} "
              f"sous le bord bas du panache, {chan['over_sole']:.3f} m au-dessus "
              f"de SOLE_Y)")
        print(f"              panache : axe y = {y_axis:+.3f}, z de {z0:+.2f} a "
              f"{z1:+.2f}, bande y {y_axis - PLUME_HALF:+.3f} .. "
              f"{y_axis + PLUME_HALF:+.3f}")
    for tower in report["towers"]:
        print(f"    tour x = {tower['x']:+6.2f}  socle r = {tower['radius']:.3f} m  "
              f"·  marge au canal lateral {tower['to_side']:.3f} m  ·  au canal "
              f"central {tower['to_middle']:.3f} m")
    print(f"    AA_Emissive_Engine dans les canaux : "
          f"{report['glow_in_channels']:.6f} m2")
    print("")
    print("  LES REPERES (BRIEF-0110) — position = BAS de la piece, CENTRE en x/z :")
    posed = 0
    for row in report["markers"]["rows"]:
        bx, by, bz = row["box"]
        posed += row["triangles"]
        print(f"    {row['name']:<22} ({row['pos'][0]:+7.3f} ; "
              f"{row['pos'][1]:+7.3f} ; {row['pos'][2]:+7.3f})  lacet "
              f"{math.degrees(row['yaw']):+6.1f} deg  {row['piece']:<24}"
              f"{row['triangles']:>5} tri")
        print(f"      -> x {bx[0]:+7.3f}..{bx[1]:+7.3f}  y {by[0]:+7.3f}.."
              f"{by[1]:+7.3f}  z {bz[0]:+7.3f}..{bz[1]:+7.3f}   ciel restant "
              f"{row['headroom']:+.3f} m")
    total = STERN_BEFORE + (report["triangles"] - HULL_BEFORE) + posed
    print(f"    {len(report['markers']['rows'])} reperes · {posed} triangles "
          f"instancies · carene {report['triangles']} (etait {HULL_BEFORE}, dont "
          f"{REMOVED_FAMILIES} retires)")
    print(f"    TOTAL POUPE {total} / {STERN_TOTAL_BUDGET} — il reste "
          f"{STERN_TOTAL_BUDGET - total}")
    clashes = report["markers"]["garrison"]
    if clashes:
        print("")
        print("  ⚠️ RECOUVREMENT AVEC LA GARNISON DE POUPE (mesure, NON corrige —")
        print("     la garnison est hors perimetre du BRIEF-0110) :")
        for c in clashes:
            print(f"    {c['piece']:<22} x {c['x']:.3f} · y {c['y']:.3f} · z "
                  f"{c['z']:.3f} m  ({c['volume']:.3f} m3) avec {c['poste']}")
    print("")
    uv = report["uv"]
    print(f"  UV — projection en boite {TEXELS_PER_METER:.2f} tuile/m "
          f"({1.0 / TEXELS_PER_METER:.2f} m/tuile), decalage z {UV_SHIFT_Z:+.2f}")
    print(f"    moyenne {uv['tiles_per_m_mean']:.4f} tuile/m "
          f"({uv['m_per_tile_mean']:.3f} m/tuile) · anisotropie max "
          f"{uv['anisotropy_max']:.3f} (borne racine(3) = 1,732)")
    print("")
    print("  Aire par materiau :")
    for name, area in sorted(report["materials"].items(), key=lambda kv: -kv[1]):
        print(f"    {name:<22} {area:9.1f} m2   "
              f"{100.0 * area / report['area']:5.2f} %")
    print("")
    print("  Profil de largeur (s -> demi-largeur) :")
    line = ""
    for s, w in report["width_profile"]:
        line += f"  {s:6.1f}:{w:6.2f}"
        if len(line) > 66:
            print("   " + line)
            line = ""
    if line:
        print("   " + line)
    print("=" * 78)
    print("")


# ==========================================================================
# La planche de recette — A LA CAMERA DU JEU (ADR-0006)
# ==========================================================================
# Tout le rig vient de `build_long_cortege` : camera (0 ; 14 ; 5), FOV 62
# vertical, trois directionnelles, aucune ombre portee. Il n'est pas recopie.
#
# ⚠️ ET LA POUPE EST RENDUE A SA VRAIE PLACE. `cortege_flyby.gd` immobilise le
# defilement a `stop_at() = LEAD_IN + station - hold`, ce qui pose le centre des
# berceaux a `z = -hold` en monde, soit -6,47 — et non a l'origine. Une planche
# cadree a z = 0 rendrait la poupe 6,47 m trop pres.

TILE_W = 1920
TILE_H = 1080
STERN_WORLD_Z = -T["hold_plane_y"]


def _frame_centre_z(altitude: float) -> float:
    """Le z monde que la camera du jeu vise, a l'altitude `altitude`.

    ⚠️ ELLE DEPEND DE L'ALTITUDE, ET C'EST TOUTE L'ASTUCE. La camera plonge a
    20 deg : viser le PONT (-11,85) met le massif (-8,40) trois metres et demi plus
    haut dans le cadre, donc au bord. On vise donc le plateau du massif.
    """
    t = (blc.CAM_POS.y - altitude) / -blc.CAM_FORWARD.y
    return blc.CAM_POS.z + blc.CAM_FORWARD.z * t


#: ⚠️ LA CAMERA DU JEU NE VOIT PAS LE MASSIF AU PLAN DE MAINTIEN, ET C'EST MESURE.
#: `cortege_flyby.gd` immobilise le defilement de facon a poser les berceaux a
#: `z = -6,47` ; le massif arriere est alors a `z = -15` a -18,5 monde, c'est-a-dire
#: AU BORD SUPERIEUR DU CADRE ou hors champ. Une planche cadree la ne montrerait pas
#: ce que le `BRIEF-0107` corrige.
#:
#: Le survol, lui, passe : quelques secondes plus tot le massif est en plein centre.
#: Cette origine-la est celle de cet instant — meme camera, meme champ, meme
#: distance, autre moment. Rien n'y est truque : c'est `_frame_centre_z()` moins la
#: station du milieu du massif.
AFT_MID_Z = 0.5 * (AFT_Z + TAIL_Z)          # -10,30
AFT_WORLD_Z = _frame_centre_z(AFT_PLATEAU_Y) - AFT_MID_Z
#: Meme mecanique pour le collecteur : il siege a `z = +8,95` local, soit 15 m
#: EN AVANT des berceaux. Au plan de maintien il tombe a 724 px sur 1080 (bas de
#: cadre, au centre) ; cette origine-la est l'instant du survol ou il est
#: pleine face.
COLLECTOR_WORLD_Z = _frame_centre_z(-4.30) - MANIFOLD_CZ


def _look(position: Vector, target: Vector) -> tuple[Vector, Vector]:
    """(avant, haut) d'une camera qui vise `target`, verticale monde conservee.

    ⚠️ L'ORDRE DU PRODUIT VECTORIEL EST CELUI DE `_plate_camera` (`droite =
    avant x haut`), verifie sur la camera du jeu : l'inverse rendrait l'image
    retournee sans qu'aucune erreur ne le dise.
    """
    forward = (target - position).normalized()
    right = forward.cross(Vector((0.0, 1.0, 0.0)))
    if right.length < 1e-6:
        right = Vector((1.0, 0.0, 0.0))
    right.normalize()
    return forward, right.cross(forward).normalized()


def _place(path: str, position: Vector, k: float, yaw: float = 0.0) -> list:
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    fresh = [o for o in bpy.context.scene.objects if o not in before]
    holder = bpy.data.objects.new(os.path.basename(path), None)
    bpy.context.collection.objects.link(holder)
    holder.location = blc._to_blender(position)
    holder.rotation_euler = Euler((0.0, 0.0, yaw), "XYZ")
    holder.scale = (k, k, k)
    for obj in fresh:
        if obj.parent is None:
            obj.parent = holder
            obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.visible_shadow = False
    return fresh


def _pose(objects: list, clip: str, frame: int, store: dict) -> None:
    for obj in objects:
        ad = obj.animation_data
        if ad is None:
            continue
        action = None
        for track in ad.nla_tracks:
            for strip in track.strips:
                if strip.action and strip.action.name.split(".")[0] == clip:
                    action = strip.action
        if action is None and ad.action and ad.action.name.split(".")[0] == clip:
            action = ad.action
        if action is None:
            continue
        ad.action = action
        for track in ad.nla_tracks:
            track.mute = True
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    for obj in objects:
        if obj.animation_data is None:
            continue
        store[obj.name] = (Vector(obj.location),
                           obj.rotation_quaternion.copy(), Vector(obj.scale))


def _freeze(store: dict) -> None:
    for name, (loc, quat, scl) in store.items():
        obj = bpy.data.objects.get(name)
        if obj is None:
            continue
        obj.animation_data_clear()
        obj.location = loc
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = quat
        obj.scale = scl
    bpy.context.view_layer.update()


def _mount_groups(origin: Vector) -> None:
    """Les trois groupes, a la place exacte que leur donne `cortege_engine.gd`."""
    store: dict = {}
    for side in (-1.0, 0.0, 1.0):
        central = side == 0.0
        k = _scale_of(central)
        g = origin + Vector((side * SPACING, DECK_Y, 0.0))
        cradle = _place(os.path.join(MODELS, "stern_cradle.glb"), g, k)
        _pose(cradle, "Intact", 12, store)
        seat = g + Vector((0.0, T["engine_seat"].y * k, T["engine_seat"].z * k))
        engine = _place(os.path.join(MODELS, "stern_engine.glb"), seat, k)
        _pose(engine, "Fonctionnement", 12, store)
        total = int(T["central_anchors"] if central else T["lateral_anchors"])
        ay = (T["socket_y"] + T["anchor_size_y"] * 0.5) * k
        for i in range(total):
            if i < 2:
                cote = -1.0 if i == 0 else 1.0
                local = Vector((cote * T["socket_x"] * k, ay,
                                T["socket_z_front"] * k))
            elif total <= 3:
                local = Vector((0.0, ay, T["socket_z_rear"] * k))
            else:
                cote = -1.0 if i == 2 else 1.0
                local = Vector((cote * T["socket_x"] * k, ay,
                                T["socket_z_rear"] * k))
            _pose(_place(os.path.join(MODELS, "stern_anchor.glb"), g + local, k),
                  "Intact", 12, store)
        for cote in (-1.0, 1.0):
            for prof in (T["socket_z_front"], T["socket_z_rear"]):
                name = "stern_arm_mirror" if cote > 0.0 else "stern_arm"
                local = Vector((cote * (T["socket_x"] + 1.15) * k,
                                T["socket_y"] * k * 0.55, prof * k))
                yaw = -math.pi * 0.5 if cote > 0.0 else math.pi * 0.5
                _pose(_place(os.path.join(MODELS, f"{name}.glb"), g + local, k, yaw),
                      "Serre", 12, store)
    _freeze(store)


# --------------------------------------------------------------------------
# Les trois panaches — POUR LA PLANCHE SEULEMENT, jamais dans le `.glb`
# --------------------------------------------------------------------------
#  ⚠️ SANS EUX LA PLANCHE NE PROUVE RIEN. « Une planche sans panache montrerait
#  trois rainures et ne dirait rien du problème qu'on corrige » (brief). Le shader
#  d'`ADR-0017` ne tourne pas dans Blender : on rejoue ici son profil, terme pour
#  terme (`_plume_radius`), et on peint par sommet ce que son `fragment()` calcule.
#  Rien de tout cela ne part dans le binaire : le `.glb` est exporte avant, et
#  `--plate-only` ne le rouvre pas.

PLUME_RINGS = 40
PLUME_SEGMENTS = 20


def _plume_shade(t: float) -> tuple[Vector, float]:
    """(couleur x energie, alpha) a l'abscisse `t` — le `fragment()` du shader."""
    core = P["core_color"].copy()
    body = P["plume_color"].copy()
    tail = P["tail_color"].copy()

    def smooth(a: float, b: float, x: float) -> float:
        u = min(max((x - a) / (b - a), 0.0), 1.0)
        return u * u * (3.0 - 2.0 * u)

    cell = 1.0 - abs(2.0 * ((t * P["shock_count"]) % 1.0) - 1.0)
    node = (1.0 - cell) ** 7.0 * (1.0 - t)
    col = core.lerp(body, smooth(0.0, 0.14, t))
    col = col.lerp(tail, smooth(0.35, 1.0, t))
    col = col.lerp(core, node * 0.85)
    # `shell` depend du regard : a la planche on prend le plancher large (0,6), ce
    # qui SOUS-estime le bord — une plume plus discrete que celle du jeu, jamais
    # plus flatteuse.
    fill = 1.0 - 0.4 * smooth(0.02, 0.4, t)
    alpha = min(1.0, fill * (1.0 - t) ** 0.4 + node * 0.6)
    return col * P["energy"], alpha


def _plume_material() -> bpy.types.Material:
    """Emission peinte par sommet, additive comme le shader (`blend_add`)."""
    mat = bpy.data.materials.new("PlumeWitness")
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.clear()
    attr = tree.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "plume"
    emit = tree.nodes.new("ShaderNodeEmission")
    emit.inputs["Strength"].default_value = 1.0
    clear = tree.nodes.new("ShaderNodeBsdfTransparent")
    add = tree.nodes.new("ShaderNodeAddShader")
    out = tree.nodes.new("ShaderNodeOutputMaterial")
    tree.links.new(attr.outputs["Color"], emit.inputs["Color"])
    tree.links.new(clear.outputs[0], add.inputs[0])
    tree.links.new(emit.outputs[0], add.inputs[1])
    tree.links.new(add.outputs[0], out.inputs[0])
    return mat


def _plume_object(name: str, origin: Vector, central: bool,
                  material: bpy.types.Material, gain: float) -> bpy.types.Object:
    y_axis, z0, _z1 = _plume_axis(central)
    length = P["length_full"]
    bm = bmesh.new()
    rings: list[list] = []
    for i in range(PLUME_RINGS + 1):
        t = i / PLUME_RINGS
        r = _plume_radius(t)
        centre = blc._to_blender(origin + Vector((0.0, y_axis, z0 - t * length)))
        ring = []
        for j in range(PLUME_SEGMENTS):
            a = 2.0 * math.pi * j / PLUME_SEGMENTS
            ring.append(bm.verts.new(centre + Vector((r * math.cos(a), 0.0,
                                                      r * math.sin(a)))))
        rings.append(ring)
    for i in range(PLUME_RINGS):
        for j in range(PLUME_SEGMENTS):
            k = (j + 1) % PLUME_SEGMENTS
            try:
                bm.faces.new([rings[i][j], rings[i][k],
                              rings[i + 1][k], rings[i + 1][j]])
            except ValueError:
                pass
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(material)
    # ⚠️ LA TEINTE SE DEDUIT DE LA POSITION, PAS DU RANG DU SOMMET. `to_mesh()` ne
    # promet pas de garder l'ordre de creation ; une couleur posee par index
    # peindrait la queue au col sans qu'aucune erreur ne le dise.
    layer = mesh.color_attributes.new("plume", "FLOAT_COLOR", "POINT")
    for index, vert in enumerate(mesh.vertices):
        game_z = -vert.co.y - origin.z
        t = min(max((z0 - game_z) / length, 0.0), 1.0)
        col, alpha = _plume_shade(t)
        layer.data[index].color = (col.x * alpha * gain, col.y * alpha * gain,
                                   col.z * alpha * gain, 1.0)
    obj = bpy.data.objects.new(name, mesh)
    obj.visible_shadow = False
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _mount_plumes(origin: Vector, gain: float = 1.0) -> list:
    """Les trois panaches temoins. `gain` est un ATTENUATEUR DE PLANCHE.

    ⚠️ IL NE SERT QUE SUR LA VUE DE DETAIL, ET IL EST DIT DANS LA LEGENDE. A
    pleine energie (2,6) la plume sature en blanc sur ses 40 premiers pour cent :
    c'est ce que le jeu montre, et c'est tres bien pour juger la lecture — mais
    sur la vignette qui doit faire voir une nervure de 0,26 m, elle efface
    exactement ce qu'on vient mesurer. Toutes les vues a la camera du jeu sont a
    gain 1.
    """
    material = _plume_material()
    out = []
    for side in (-1.0, 0.0, 1.0):
        central = side == 0.0
        place = origin + Vector((side * SPACING, 0.0, 0.0))
        out.append(_plume_object("Plume%+d" % int(side), place, central,
                                 material, gain))
    return out


def _mount_markers(origin: Vector, only: tuple[str, ...] | None = None) -> list:
    """Monte sur chaque repere la piece qu'il porte — COMME LE CODE DU JEU.

    ⚠️ UNE PLANCHE DE REPERES VIDES NE PROUVE RIEN (`ADR-0006`, et le critere du
    brief). La seule chose qui dise si le collecteur se lit, c'est le collecteur
    monte. La correction d'assise reproduite ici est mot pour mot celle de
    `CortegeConduit._seat()` : centre en x/z, BAS sur le repere, boite englobante
    mesuree et non origine de fichier.
    """
    fresh: list = []
    store: dict = {}
    for name, local, yaw, kind in markers():
        if only and not name.startswith(only):
            continue
        lo, hi = _piece_box(kind)
        # La correction est ecrite dans le repere LOCAL de la piece : elle
        # commute avec le lacet, et avec lui seul.
        seat = Vector((-0.5 * (lo.x + hi.x), -lo.y, -0.5 * (lo.z + hi.z)))
        cos_y, sin_y = math.cos(yaw), math.sin(yaw)
        turned = Vector((cos_y * seat.x + sin_y * seat.z, seat.y,
                         -sin_y * seat.x + cos_y * seat.z))
        made = _place(os.path.join(MODELS, PIECE_FILES[kind]),
                      origin + local + turned, 1.0, yaw)
        # ⚠️ ON FIGE LE CLIP NOMINAL, comme pour les trois groupes propulsifs :
        # une piece importee sans pose explicite rend la premiere image de
        # l'action que l'importateur lui laisse, qui n'est pas forcement son
        # etat au repos.
        _pose(made, PIECE_REST_CLIP[kind], 1, store)
        fresh += made
    _freeze(store)
    return fresh


def _mount_corridor(origin: Vector) -> list:
    """Le troncon 5 du corridor, pour juger la jonction et le contraste."""
    return blc._import(os.path.join(MODELS, "long_cortege.glb"), "corridor",
                       origin + Vector((0.0, 0.0, STATION)))


#: Les vues cadrees sur le massif : la poupe y est avancee pour que le survol
#: montre ce qu'il montre a ce moment-la (voir `AFT_WORLD_Z`).
AFT_VIEWS = ("aft", "nude", "channel", "top")
#: La carene D'AVANT ce lot, rendue au meme cadrage pour la comparaison.
#: Elle est produite par `tools/blender/build_stern_before.py` (extrait de git,
#: hors depot) et son chemin est passe par `--before=`. Sans elle, la vignette
#: de comparaison est simplement omise : une planche qui inventerait son
#: « avant » ne vaudrait rien.
BEFORE_HULL = os.environ.get("STERN_BEFORE_GLB", "")
#: L'attenuateur de panache, par vue (voir `_mount_plumes`).
PLUME_PLATE_GAIN = {"channel": 0.14}
#: Ce qu'il reste d'eclairage sur la vignette de blackout (voir `_dim_scene`).
BLACKOUT_LIGHT = 0.12


def _dim_scene(gain: float) -> None:
    """Baisse les trois directionnelles ET l'ambiante du monde.

    ⚠️ SANS CA, LA VIGNETTE DE BLACKOUT NE PEUT PAS ECHOUER, ET C'EST MESURE.
    Eteindre `AA_Emissive_Engine` ne noircit que son EMISSION ; sa couleur de base
    reste le magenta `#D93D9C`, dont l'albedo rouge vaut 0,706. Sous les 2,80 de
    puissance cumulee de la planche, le canal rouge sature : les rubans eteints
    rendaient (255 ; 100 ; 250) contre (255 ; 113 ; 252) allumes — 13 niveaux de
    vert d'ecart sur 255, invisibles a l'œil. La vignette validait donc tout, y
    compris un emissif mal range.

    A 12 % la matiere n'est plus qu'une silhouette et le moindre emissif restant
    creve le cadre. C'est le seul reglage sous lequel ce test peut etre rouge.
    """
    for light in bpy.data.lights:
        light.energy *= gain
    world = bpy.context.scene.world
    if world is None or not world.use_nodes:
        return
    for node in world.node_tree.nodes:
        if node.type == "BACKGROUND":
            value = node.inputs[0].default_value
            node.inputs[0].default_value = (value[0] * gain, value[1] * gain,
                                            value[2] * gain, value[3])


def _tile(path: str, view: str, dark: bool = False, checker: bool = False) -> None:
    blc._plate_reset()
    if view in AFT_VIEWS:
        world_z = AFT_WORLD_Z
    elif view == "collecteur":
        world_z = COLLECTOR_WORLD_Z
    else:
        world_z = STERN_WORLD_Z
    origin = Vector((0.0, 0.0, world_z))
    before = view == "avant"
    source = BEFORE_HULL if before else OUTPUT
    hull = blc._import(source, "stern_hull", origin)
    corridor = _mount_corridor(origin)
    groups = view not in ("nude", "channel")
    if groups:
        _mount_groups(origin)
    # ⚠️ LES PIECES INSTANCIEES SONT LA. Le brief l'exige mot pour mot :
    # « rendus AVEC les pieces instanciees sur les reperes ». La vignette
    # « avant » ne les a pas — c'est tout l'objet de la comparaison.
    if not before:
        _mount_markers(origin)
    if checker:
        blc._apply_checker([o for o in bpy.context.scene.objects
                            if o.type == "MESH"])
    # ⚠️ LES PANACHES APRES LE DAMIER, JAMAIS AVANT. `_apply_checker()` remplace le
    # materiau de TOUT maillage de la scene : peints en damier, les trois panaches
    # devenaient trois cones gris opaques poses sur la coque.
    # ⚠️ PAS DE PANACHE SUR LE BLACKOUT. Il se declenche quand la propulsion meurt :
    # trois panaches allumes sur un vaisseau eteint raconteraient le contraire de ce
    # que la vignette verifie.
    plumes = [] if (checker or dark) else _mount_plumes(
        origin, PLUME_PLATE_GAIN.get(view, 1.0))
    if dark:
        for mat in bpy.data.materials:
            if not mat.name.split(".")[0].startswith("AA_Emissive"):
                continue
            if not mat.use_nodes:
                continue
            for node in mat.node_tree.nodes:
                if node.type == "BSDF_PRINCIPLED":
                    node.inputs["Emission Strength"].default_value = 0.0
    blc._plate_lights()
    if dark:
        _dim_scene(BLACKOUT_LIGHT)

    if view == "collecteur":
        # ⚠️ MEME CAMERA, MEME CHAMP, AUTRE INSTANT. Le collecteur est a
        # `z = +8,95` local, c'est-a-dire 15 m devant les berceaux : au plan de
        # maintien il tombe en bas de cadre, a 724 px sur 1080. Ici on avance la
        # poupe de facon a le centrer — c'est ce que le survol montre une
        # seconde plus tot, rien n'y est truque.
        cam_pos = blc.CAM_POS
        forward = blc.CAM_FORWARD
        up = blc.CAM_UP
        fov = math.radians(30.0)
    elif view == "rive":
        # La rive de tribord, de trois-quarts : le socle, le pylone et les deux
        # flexibles de rebord, vus comme le survol les voit en s'approchant.
        # ⚠️ PAS PAR LE FLANC, ET C'EST MESURE. Vue du dehors, la rive presente
        # sa facette exterieure (|x| = 18,50) et le socle masque tout ce qu'il
        # porte : le premier tirage ne montrait pas un centimetre du pylone. La
        # camera est donc AU-DESSUS DU BASSIN, la ou la camera du jeu se tient,
        # et elle regarde la face interieure — la seule que le joueur voie.
        cam_pos = Vector((2.0, 8.5, world_z + 15.0))
        target = Vector((17.20, -6.80, world_z + PYLON_Z))
        forward, up = _look(cam_pos, target)
        fov = math.radians(26.0)
    elif view == "joint":
        cam_pos = Vector((0.0, 9.0, 21.0))
        forward = Vector((0.0, -0.500, -0.866))
        up = Vector((0.0, 0.866, -0.500))
        fov = blc.CAM_FOV_V
    elif view == "channel":
        # ⚠️ RASANTE ET DANS L'AXE DU CANAL LATERAL. Vue de la camera du jeu, une
        # tranchee de 2,55 m est masquee par son propre bord et par le panache : on
        # n'en voit que la levre. Ici on entre dedans — c'est la seule vue qui
        # montre le chanfrein, les nervures et le fond.
        # ⚠️ SANS LES GROUPES, ET CE N'EST PAS UNE FACILITE. Rendue avec eux, la
        # vue ne montrait qu'une nacelle de 10 m et son panache : le canal est
        # DERRIERE le moteur qui le remplit, et rien de ce qui est mesure ici ne
        # s'y voyait. Les trois panaches, eux, restent — c'est le seul objet dont
        # cette vue doit prouver le degagement.
        #
        # ⚠️ ET PAS PAR LE FLANC NON PLUS : les quatre pylones de rive
        # (|x| >= 17,7, jusqu'a y = -3,30) barrent toute visee rasante venue du
        # dehors. La camera est DANS le bassin, entre les deux pylones de tribord
        # (le seul creneau libre en z), et regarde la bouche du canal de
        # trois-quarts.
        cam_pos = Vector((22.0, 2.00, world_z + 1.0))
        target = Vector((4.0, CHANNEL_FLOOR_Y + 1.35, world_z + AFT_MID_Z))
        forward, up = _look(cam_pos, target)
        fov = math.radians(32.0)
    elif view == "top":
        cam_pos = Vector((0.0, 42.0, world_z + AFT_MID_Z))
        forward = Vector((0.0, -1.0, 0.0))
        up = Vector((0.0, 0.0, -1.0))
        fov = math.radians(34.0)
    else:
        cam_pos = blc.CAM_POS
        forward = blc.CAM_FORWARD
        up = blc.CAM_UP
        fov = blc.CAM_FOV_V
    camera = blc._plate_camera("game", blc._to_blender(cam_pos),
                               blc._to_blender(forward), blc._to_blender(up), fov)
    metrics = blc._frame_coverage(DECK_Y)
    px = TILE_W / metrics["frame_width"]
    heads = {
        "avant": ("1 — AVANT  ·  la poupe du BRIEF-0107 : collecteur en tube, "
                  "chaine de brides, quatre fuseaux de 60 tri, tours a 280"),
        "game": ("2 — APRES, MEME CADRAGE  ·  5 conduites + 2 coudes + 8 "
                 "flexibles + 2 pylones INSTANCIES sur les reperes"),
        "collecteur": ("3 — LE COLLECTEUR, pleine face  ·  le morceau le plus "
                       "regarde du lot (50,3 px/m) : rail a deux niveaux, "
                       "coudes de rive, quatre flexibles dans l'axe de l'artere"),
        "rive": ("4 — LA RIVE DE TRIBORD  ·  le socle (216 tri) porte le pylone "
                 "livre (2 612) a -8,60, ou il tient ENTIER sous le plafond"),
        "aft": ("5 — LE MASSIF AU CENTRE DU CADRE  ·  les deux tours d'echange "
                "regenerees : socle evase, galerie de service, diffuseur"),
        "nude": ("6 — LA CARENE SEULE, SOUS LES TROIS PANACHES  ·  sans les "
                 "groupes : les trois canaux et ce qu'ils degagent"),
        "channel": ("7 — LE MASSIF DE TROIS-QUARTS, sans les groupes  ·  panaches "
                    "a 14 % : a pleine energie ils remplissent leur canal"),
        "joint": ("8 — LA JONCTION s = 500, vue rasante  ·  elle n'a pas bouge "
                  "d'un micron (ecart mesure 6,6e-07 m sur 48 sommets)"),
        "top": ("9 — DE DESSUS  ·  les trois canaux alignes sur les trois axes "
                "moteur (x = 0 et +/-10,28), demi-largeur libre 2,20 m"),
    }
    head = heads[view]
    tint = (1.0, 0.88, 0.55)
    if dark:
        head = ("7 — BLACKOUT  ·  emissif eteint, panaches coupes, scene a %d %% "
                "  ·  tout ce qui brille encore est mal range"
                % round(BLACKOUT_LIGHT * 100))
        tint = (1.0, 0.55, 0.55)
    if checker:
        head = ("8 — DAMIER UV a la perspective du jeu  ·  projection en boite "
                "%.2f tuile/m (%.2f m par tuile)"
                % (TEXELS_PER_METER, 1.0 / TEXELS_PER_METER))
        tint = (0.72, 1.0, 0.82)
    blc._label(camera, head, -0.96, 0.90, 0.028, TILE_W, TILE_H, tint)
    if view in ("game", "aft", "nude", "channel", "avant") and not checker:
        y_axis, z0, z1 = _plume_axis(False)
        blc._label(camera,
                   f"panache (ADR-0017) : axe y = {y_axis:.2f}, de z = {z0:.2f} a "
                   f"{z1:.2f}, demi-largeur {PLUME_HALF:.2f} m — canal 2,20 m de "
                   f"demi-largeur, fond {CHANNEL_FLOOR_Y:.2f}, garde 0,50 m",
                   -0.96, 0.84, 0.022, TILE_W, TILE_H, (0.80, 0.62, 1.0))
        if view == "channel":
            blc._label(camera,
                       "paroi -> nervure 0,26 m  ·  chanfrein 0,70 x 0,90 m  ·  "
                       "levre 1,10 x 0,82 m, +0,45 m au-dessus du plateau  ·  "
                       "marge au socle de tour 1,16 m",
                       -0.96, 0.79, 0.022, TILE_W, TILE_H, (0.72, 0.84, 1.0))
    if view in ("game", "aft", "nude", "avant", "collecteur") and not checker:
        blc._label(camera,
                   f"camera du jeu (0 ; 14 ; 5), FOV 62 vertical, pont de poupe "
                   f"y = {DECK_Y:.2f} — cadre {metrics['frame_width']:.2f} m, "
                   f"{px:.1f} px/m en lateral",
                   -0.96, 0.80, 0.022, TILE_W, TILE_H)
        blc._label(camera,
                   "corridor 12,04 m de demi-largeur -> poupe 19,70 : "
                   "trois marches a s = 500 / 505,3 / 511,0",
                   -0.96, 0.75, 0.022, TILE_W, TILE_H, (0.72, 0.84, 1.0))
    blc._render(path, TILE_W, TILE_H)
    del hull, corridor, plumes


def render_plate(only: tuple[str, ...] | None = None, out: str = PLATE) -> None:
    """La planche complete, ou un sous-ensemble (`--views`) pour iterer.

    ⚠️ `--views` N'EST PAS LE LIVRABLE. Sept vignettes Cycles coutent un quart
    d'heure ; juger une correction de silhouette n'en demande que trois. La planche
    livree est toujours celle sans argument.
    """
    staging = tempfile.mkdtemp(prefix="aegis-stern-plate-")
    tiles: list[tuple[str, int]] = []
    order = ("avant", "game", "collecteur", "rive", "aft", "nude", "channel",
             "joint", "top")
    wanted = only or order + ("dark", "checker")
    try:
        for view in order:
            if view not in wanted:
                continue
            if view == "avant" and not os.path.exists(BEFORE_HULL):
                print("  (vignette « avant » omise : STERN_BEFORE_GLB absent)")
                continue
            path = os.path.join(staging, f"{view}.png")
            _tile(path, view)
            tiles.append((path, TILE_H))
        if "dark" in wanted:
            path = os.path.join(staging, "dark.png")
            _tile(path, "aft", dark=True)
            tiles.append((path, TILE_H))
        if "checker" in wanted:
            path = os.path.join(staging, "checker.png")
            _tile(path, "nude", checker=True)  # sans panache : ils masqueraient
            tiles.append((path, TILE_H))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        blc._compose(tiles, out, width=TILE_W)
    finally:
        for leftover in os.listdir(staging):
            os.remove(os.path.join(staging, leftover))
        os.rmdir(staging)


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    only = None
    out = PLATE
    for arg in argv:
        if arg.startswith("--views="):
            only = tuple(arg.split("=", 1)[1].split(","))
        if arg.startswith("--out="):
            out = os.path.abspath(arg.split("=", 1)[1])
    if "--plate-only" in argv:
        render_plate(only, out)
        return
    report = build()
    _print(report)
    if "--plate" in argv:
        render_plate(only, out)


if __name__ == "__main__":
    main()
