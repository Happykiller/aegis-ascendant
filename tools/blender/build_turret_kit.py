"""build_turret_kit.py — le kit d'affut de tourelle du Long Cortege (BRIEF-0100).

    blender-aegis -t 1 -b -P tools/blender/build_turret_kit.py
    blender-aegis -t 1 -b -P tools/blender/build_turret_kit.py -- --plate
    ./scripts/build-hull.sh --check turret_kit       # + controle de determinisme

Produit `assets/imported/models/backgrounds/turret_kit.glb` et, avec `--plate`,
la planche de recette `docs/forge/output/BRIEF-0100-planche-tourelles.png`.

Le script EST la source (ADR-0008) : aucun `.blend` versionne, aucun alea, deux
executions successives rendent le meme sha256.


CE QUE CE FICHIER EST, ET CE QU'IL N'EST PAS
============================================
Ce n'est PAS une tourelle. C'est un KIT de huit pieces, chacune modelisee dans
SON repere, origine au point d'assemblage. Le moteur les instancie et les
compose : c'est lui qui fait DIX-SEPT tourelles differentes a partir d'un seul
kit. La coque, elle, ne porte plus aucun socle cuit (`build_turret_pad()` a
disparu de `build_long_cortege.py`, BRIEF-0093) — elle ne porte que le marqueur.

    turret_pad            socle ancre        origine : centre, Y = assise
    turret_anchor_skirt   jupe d'ancrage     origine : centre, Y = assise
    turret_ring           couronne DE ROTATION  origine : centre, SUR SON AXE
    turret_body           bloc canon blinde  origine : centre, sur l'axe
    turret_barrel         UN tube long       origine : la culasse
    turret_barrel_short   UN tube court      origine : la culasse
    turret_service_box    coffret technique  origine : sa base
    turret_pipe           faisceau de conduites  origine : sa base

⚠️ LES HUIT NOMS N'ONT PAS BOUGE A LA REFORGE DE BRIEF-0100, ET AUCUN NEUF NE
S'EST AJOUTE. Tout le detail porte par la planche cible est FUSIONNE dans ces
huit maillages. C'est une contrainte de cout, pas un gout : le modele tiers qui
sert de recette pose 465 maillages ; a dix-sept tourelles, ce serait 7 905
instances pour un niveau qui en compte aujourd'hui 9 par tourelle.


LES TROIS CLASSES — MEMES BLOCS, TROIS ECHELLES (BRIEF-0100)
============================================================
La planche cible le dit elle-meme : « MODULES PARTAGES — MEMES BLOCS. TROIS
ECHELLES ». Le kit ne livre donc PAS trois geometries : il livre UNE geometrie,
celle de la classe STANDARD, et le moteur la met a l'echelle. C'est deja ce que
fait `cortege_turret.gd::_geom_scale()` — l'echelle s'applique au maillage ET aux
cotes d'assemblage, les deux vont ensemble.

    legere  x 0,538      standard  x 1,000 (NATIVE)      lourde  x 1,200

    longueur   2,88 m       6,50 m                        7,80 m
    hauteur    0,82 m       1,52 m                        1,82 m

Le facteur de la LEGERE est le rapport de longueur de la planche elle-meme
(3,5 / 6,5 = 0,538). Celui de la LOURDE ne l'est PAS : la planche demanderait
1,538 (10,0 / 6,5), et le moteur le porte deja — mais il ne passe pas. Voir le
bloc suivant, qui le mesure.


⛔ LA COTE DE LA PLANCHE NE PASSE PAS, ET C'EST LA VERTICALE QUI L'INTERDIT
==========================================================================
Le brief demandait de mesurer l'EMPRISE. La mesure a designe une autre borne,
plus serree, que personne n'avait relevee : la HAUTEUR.

  * Le plafond des pieces de gameplay est a Y = -2,40 (`BRIEF-0094`, tenu par
    `cortege_flyby.gd` ET par `test_no_turret_ever_reaches_the_flight_plane`).
  * L'assise la plus HAUTE des dix-sept emplacements est Y = -4,270 (Turret_08).
  * Il reste donc **1,870 m** au-dessus de l'assise, au pire emplacement. La
    tourelle d'avant en occupait deja 1,70 : le budget vertical etait SATURE.

Une lourde de 4,2 m culminerait a -0,07, soit SEPT CENTIMETRES sous le plan de
vol du joueur. Ce n'est pas une marge a negocier, c'est la tourelle dans le
cockpit. La classe lourde est donc posee a **1,82 m** — 97 pct du budget
vertical disponible, et **-57 pct par rapport a la planche**.

⚠️ ET LE FACTEUR EN VIGUEUR VIOLE DEJA CE PLAFOND, SANS QUE RIEN NE LE DISE.
`HEAVY_GEOM_SCALE = 1.538` applique au kit d'avant (1,70 m) met les trois
lourdes a -1,655 / -1,661 / -1,669, soit 0,73 a 0,75 m AU-DESSUS du plafond. Le
defaut est muet dans les deux harnais : celui du kit multipliait `TURRET_H` par
1 (il ignorait les echelles), et `test_no_turret_ever_reaches_the_flight_plane`
compose les AABB avec les `LIFT` du moteur SANS jamais appeler `_geom_scale()`.
C'est pour cela que `_audit()` mesure desormais CLASSE PAR CLASSE, et echoue.

Il y a une seconde borne, par le bas, et elle vient aussi de la mesure : la peau
REMONTE vers la crete dorsale au-dela de l'emprise (0,608 m a 3 m de l'axe,
0,679 m a 7 m, 0,898 m a 8 m), et les tubes balayent a 360 deg. Le dessous d'un
tube doit donc passer au-dessus de 0,68 m. La fenetre utile pour la classe
native est ainsi [~1,55 ; 1,870] m — d'ou 1,52 m de hauteur et 1,200 au plus
pour l'echelle lourde.

⚠️ ET C'EST LA MOINS CHERE DES TROIS COTES A PERDRE, parce que la camera plonge
a 70 deg : un metre de HAUTEUR se projette a 0,34 m a l'ecran, un metre de PLAN
a 0,94 m. Le budget a donc ete depense la ou il rend — la longueur et le plan —
et l'ecart de hauteur coute presque trois fois moins qu'un ecart de longueur.

L'EMPRISE, elle, est bornee a **2,08 m de rayon**, et c'est une borne de la
COQUE et non du terrain : c'est le rayon avec lequel `build_long_cortege.py`
echantillonne sa peau pour poser l'assise du marqueur. Une emprise plus large
deborderait sur de la peau que personne n'a mesuree. Le terrain, lui, en
autoriserait 2,60 (le denivele sous l'emprise y reste a 0,729 m) ; a 2,80 il
passe a 0,995 m sur trois emplacements et a 3,20 il atteint 1,914 m. Les 3,62 m
de rayon du modele tiers ne se posent nulle part sur cette coque.


LA REGLE QUI PRIME SUR TOUT LE RESTE
====================================
« La structure doit etre identifiable par sa seule SILHOUETTE, avec au plus 6-8
primitives principales. Les emissifs ne servent qu'a renforcer une fonction deja
lisible en geometrie. »

La tourelle assemblee en compte SIX :

    1. le socle, tambour a vingt-quatre semelles blindees
    2. la couronne, cylindre bas ENFONCE dans la cuvette du socle
    3. le bloc blinde, parallelepipede trapu a chanfreins et plaques rapportees
    4. et 5. les DEUX canons, paralleles, chemises en gradins
    6. l'appareillage — coffrets et conduites, sur le plateau du socle

Le test d'acceptation reste celui de BRIEF-0093, pris a l'autre bout de
BRIEF-0091 : en noir et blanc, emissifs coupes, un HANGAR est un cadre creux et
une TOURELLE est un canon. Ce qui les separe n'est ni la couleur ni la lumiere,
c'est que l'un CREUSE et que l'autre DEPASSE.


⚠️ LE POINT MECANIQUE QUI NE SE VOIT PAS SUR UNE PLANCHE
========================================================
`turret_ring` — et tout ce qui est monte dessus — tourne autour de l'axe Y, EN UN
BLOC, a 42 deg/s (`cortege_turret.gd`). Si l'origine de la couronne n'est pas
exactement sur son axe de rotation, la tourelle balaie en decrivant un cercle au
lieu de pivoter sur place, et ça ne se voit qu'en jeu, EN MOUVEMENT.

Ce n'est donc pas laisse a l'appreciation : `_assert_on_axis()` relit le BINAIRE
et verifie, sur `turret_ring` et sur `turret_body`, que le centroide des sommets
et la boite englobante sont centres sur (0, ·, 0) au micron. Les deux echouent le
build.


OU LE BUDGET EST DEPENSE, ET POURQUOI IL A CHANGE DE JUSTIFICATION
==================================================================
⚠️ CE PARAGRAPHE EN REMPLACE UN QUI ETAIT FAUX, ET QUI PLAFONNAIT CETTE PIECE.
Il justifiait le budget par le filtre de post-traitement retro et par la
resolution logique a laquelle il rendait. `ADR-0045` a SUPPRIME ce filtre du
depot le 2026-09-05 : sa justification est morte avec lui, et elle n'est meme
pas recopiee ici — la laisser, fut-ce entre guillemets, rejustifierait la
platitude au prochain passage. C'est elle qui avait plafonne la tourelle a six
primitives lisses.

Ce qui borne un detail aujourd'hui est mesure sur capture 1920x1080 native
(`docs/forge/textures/README.md`, releve du 2026-09-05) :

    45,8 px/m en travers du vaisseau, 40,0 px/m dans son axe (rapport 0,87 : la
    densite N'EST PAS isotrope) ; ~41 px/m sur le pont de coque.
    Seuil de PRESENCE ~2 px  ->  ~4,4 cm de monde.
    Seuil de FORME    ~3 px  ->  ~6,5 cm de monde : en dessous on voit qu'il y a
    quelque chose, pas ce que c'est.
    Plancher de CONTRASTE ~10 niveaux d'ecart au fond local — et il juge autant
    que la taille : une gorge de 5,9 px qui tranche en noir se lit MIEUX qu'un
    contour de 27 px qui ne module que 4 niveaux.

Le budget va donc a CINQ choses, et la cinquieme est neuve :

  * LES CHANFREINS SUR LES GRANDES ARETES, comme avant. Ils rendent de la
    lumiere cle a toute distance.
  * LA PROFONDEUR REELLE. La couronne est LOGEE dans la cuvette du socle ; les
    canons sont LOGES dans un masque creuse de 16 cm ; la bouche est un vrai
    trou (levre, chemise, alesage sombre en retrait).
  * LA SILHOUETTE — ce qui depasse (les tubes) et ce qui creuse (cuvette,
    masque).
  * LA VARIETE — deux longueurs de canon, une jupe optionnelle, un ecartement et
    des angles d'appareillage libres.
  * ⭐ LE JOINT BORDE D'UNE ARETE CLAIRE, qui est la depense la plus rentable du
    fichier et qui n'existait pas. Toute plaque posee l'est SUR un retrait
    sombre (`AA_Greeble`) et se termine par un LISERE de 3 a 5 cm en `AA_Trim`
    (ivoire froid, metallicite 0,85). C'est le seul detail qui satisfait les
    deux seuils a la fois : 5 cm passent le seuil de presence, et le contraste
    ivoire-sur-anthracite tranche de bien plus de 10 niveaux. La recette est
    portee du modele tiers ; c'est aussi, mot pour mot, l'argument que ce kit
    faisait deja pour ses chanfreins et qu'il n'appliquait qu'aux grandes
    aretes.

Les revolutions montent en revanche : 72 segments pour le socle (24 modules de
trois), 48 pour la couronne, 24 pour les tubes. A 41 px/m un socle de 4,16 m
fait 170 px de large : ses 24 modules y font 7 px chacun, au-dessus du seuil de
forme. A 23 px logiques ils n'en auraient fait que 4.

⚠️ LE BUDGET DE TRIANGLES N'EST PLUS UN CRITERE D'ACCEPTATION (`ADR-0044`, et
BRIEF-0100 le confirme). Les quatre relevés GPU du 2026-09-05 (1,037 / 1,209
puis 1,800 / 0,765 ms sur RTX 4080) sont domines par leur dispersion : ils
n'etablissent aucun surcout et n'en excluent aucun. Les deux constantes
`TRI_BUDGET_*` restent, mais comme GARDE-FOU D'EMBALLEMENT — trois fois le
compte mesure — et non comme cote a tenir. Le compte reel est au rapport.


L'ECHELLE DE DEPLIAGE — POURQUOI 0,200 ET PAS PLUS FIN
======================================================
Le kit partage les slots du borde (`AA_Hull`, `AA_Panel`, `AA_Greeble`,
`AA_Trim`, `AA_Emissive_Engine`). Deux echelles de depliage sur un MEME slot,
c'est la faute qu'a corrigee BRIEF-0090 sur Ambry : la carte sortirait au bon
grain sur la coque et au mauvais sur la tourelle, cote a cote. Le kit est donc
deplie a la densite du borde — 0,200 tuile/m, 5,00 m par tuile — comme
`bay_kit.glb`, en PROJECTION EN BOITE (`ak.box_project_uv()`), ce que BRIEF-0100
demande explicitement.

⛔ ET IL NE PART AUCUNE TEXTURE (`ADR-0028`, section « Texture » du brief). Le
niveau 2 entier est en PBR par facteurs : `long_cortege.glb`, `turret_kit.glb`,
`spine_kit.glb` et `citadel_kit.glb` ne portent pas une seule image, et
`_audit()` echoue le build si l'une apparait. `TEXCOORD_0` est COMPTE sur chaque
primitive du binaire, jamais suppose : trois coques du depot sont sorties sans
UV et le defaut est totalement muet.
"""

from __future__ import annotations

import json
import math
import os
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

# ⚠️ LE KIT LIT SES COTES DANS LE SCRIPT DE LA COQUE, IL NE LES RECOPIE PAS.
# Meme raison que pour `bay_kit` : une assise calculee ici et une assise calculee
# la-bas divergeraient en silence, et aucun harnais separe ne le verrait.
sys.path.insert(0, _HERE)
import build_long_cortege as cortege  # noqa: E402
import build_bay_kit as baykit        # noqa: E402  (planche : le hangar temoin)

OUTPUT = os.path.join(_REPO, "assets/imported/models/backgrounds/turret_kit.glb")
PLATE = os.path.join(_REPO, "docs/forge/output/BRIEF-0100-planche-tourelles.png")
HULL = cortege.OUTPUT
BAY_KIT = baykit.OUTPUT

# ==========================================================================
# Cotes maitresses — repere KIT (X lateral, Y haut, Z survol, +Z = PROUE)
# ==========================================================================
# Y = 0 est le plan d'ASSISE du socle sur la peau, c'est-a-dire le Y que porte
# le marqueur `Turret_NN` de la coque. TOUTES les pieces sont modelisees sur ce
# plan, et TOUTES les cotes ci-dessous sont celles de la classe LOURDE : c'est
# l'echelle native du kit, les deux autres classes en sont des reductions
# appliquees par le moteur (voir `CLASSES`).

#: Emprise hors-tout de l'installation posee sur la peau, jupe comprise.
#: ⚠️ ELLE NE SE CHOISIT PAS ICI : c'est avec ce rayon que `build_long_cortege`
#: echantillonne sa peau pour calculer l'assise du marqueur. Le harnais refuse
#: qu'elles divergent. Le terrain en autoriserait 2,60 (denivele 0,729 m au
#: pire) ; au-dela de 2,80 il decroche (0,995 m, puis 1,914 m a 3,20). Voir
#: l'en-tete et la table des dix-sept emplacements au compte-rendu.
SKIRT_R = cortege.TURRET_FOOTPRINT_R
FOOTPRINT_R = SKIRT_R

#: Le socle. Son tambour est en RETRAIT de la jupe : c'est ce qui fait que la
#: jupe se lit comme un collier ancre et non comme un second disque.
PAD_R = 1.86
#: Profondeur du joint entre deux semelles blindees. 7 cm : au-dessus du seuil
#: de FORME (~6,5 cm de monde a 41 px/m), donc on voit son orientation et pas
#: seulement sa presence.
PAD_JOINT = 0.07
#: 24 modules de 3 segments — deux sommets sur la semelle, un dans le joint.
PAD_MODULES = 24
PAD_SEG = PAD_MODULES * 3
#: Hauteur du dessus des semelles au-dessus de l'assise.
PAD_RIM_H = 0.26
#: Le plateau ou se posent coffrets et conduites.
PAD_SHELF_Y = 0.20
PAD_SHELF_R0 = 1.58
#: ⚠️ PROFONDEUR ENTERREE — ELLE A PLUS QUE DOUBLE, POUR UNE RAISON MESUREE. Le
#: creux sous le socle vaut jusqu'a 0,685 m (les dix-sept emplacements, table au
#: compte-rendu). Mais l'assise est calculee sur un disque de 2,08 m alors que
#: le socle d'une tourelle LEGERE ne fait qu'un metre de rayon : sous elle, le
#: creux vaut encore 0,648 m — et sa jupe, mise a l'echelle, n'en couvrait que
#: 0,85 x 0,5 = 0,425 m. Les tourelles legeres FLOTTAIENT donc jusqu'a 0,22 m,
#: depuis BRIEF-0093, sans qu'aucun harnais le voie : le harnais mesurait le
#: denivele au rayon d'ECHANTILLONNAGE et non au rayon de la CLASSE.
#: `turret_hollow()` le mesure desormais par classe. La jupe est enterree : elle
#: ne coute que des triangles qu'on ne voit jamais.
PAD_BURIED = 2.00
#: La cuvette ou la couronne s'enfonce. Son fond, et son rayon interieur.
PAD_WELL_Y = 0.04
PAD_WELL_R = 1.20

#: Jupe d'ancrage SUPPLEMENTAIRE — la premiere des trois familles de variete.
#: Le moteur la pose ou non ; sans elle le socle est identique.
SKIRT_TOP = 0.08
SKIRT_BURIED = 1.90
SKIRT_MODULES = 12
SKIRT_SEG = SKIRT_MODULES * 3
SKIRT_JOINT = 0.06

#: La couronne de rotation, LOGEE dans la cuvette.
RING_R = 1.14
RING_D = RING_R * 2.0
RING_H = 0.36
RING_MODULES = 16
RING_SEG = RING_MODULES * 3
RING_BASE = PAD_WELL_Y
RING_TOP = RING_BASE + RING_H

#: Le bloc canon blinde — RECTANGULAIRE TRAPU, surtout pas une sphere.
#: ⚠️ SA LARGEUR EST CALCULEE, PAS CHOISIE : le masque doit LOGER les deux
#: tubes, manchons de recul compris, a l'ecartement maximal que la variete
#: autorise. Manchon de 0,26 m de rayon, entraxe maximal 1,00 m -> il faut
#: 0,78 m de demi-facette avant PLATE, donc 0,80 m d'ouverture de masque, donc
#: 1,02 m de demi-largeur hors tout avec le chanfrein de 0,22.
BODY_HX = 1.02
BODY_Z0, BODY_Z1 = -0.92, 0.84
BODY_H = 0.96
BODY_CHAMFER = 0.22
BODY_BASE = RING_TOP
BODY_TOP = BODY_BASE + BODY_H
#: Demi-largeur de la FACETTE AVANT PLATE : c'est l'ouverture du masque.
MANTLET_HX = BODY_HX - BODY_CHAMFER
#: Le viseur : la seule chose qui monte plus haut que le bloc, et elle est
#: etroite. Elle porte la cote de hauteur totale.
SIGHT_H = 0.16
#: Hauteur totale de la tourelle STANDARD (echelle native) au-dessus de l'assise.
#: ⚠️ ELLE EST BORNEE PAR LE PRODUIT `TURRET_H x echelle_lourde`, pas par elle
#: seule : le pire emplacement (Turret_08, assise -4,270) n'offre que 1,870 m
#: sous le plafond des pieces de gameplay (-2,40), et la lourde y monte a
#: 1,52 x 1,200 = 1,824 m. La planche en demandait 2,80 pour la standard et 4,20
#: pour la lourde — voir l'en-tete.
TURRET_H = BODY_TOP + SIGHT_H

#: Le masque : les canons sont LOGES dedans, pas colles devant. Toute la facette
#: avant du bloc est en retrait — pas une plaque posee, un CREUX, qui porte une
#: ombre sur toute sa largeur.
MANTLET_DEPTH = 0.14
#: Draft du creux : le fond est legerement plus petit que la bouche.
MANTLET_DRAFT = 0.04

#: LES CANONS. Leur allonge n'est pas libre non plus, et c'est encore une
#: MESURE : la peau REMONTE vers la crete dorsale au-dela de l'emprise. Sur le
#: disque balaye par un tube, elle monte de 0,608 m a 3 m de l'axe, 0,665 m a
#: 6 m, 0,679 m a 7 m — puis 0,898 m a 8 m (Turret_02, 03 et 10, qui sont
#: assises bas sur la bande exterieure). Le dessous du tube est a
#: BARREL_Y - JACKET_R[0] = 0,745 m : l'allonge tient jusqu'a ~7,5 m, elle
#: laboure la coque a 8. La bouche est a 4,42 m de l'axe a l'echelle native
#: (5,30 m pour la lourde), et `turret_skin_rise()` le reverifie par classe.
BARREL_LEN = 3.72
BARREL_SHORT_LEN = 2.80
BARREL_R = 0.17
#: Rayon du manchon de recul, a la culasse. C'est LUI qui dimensionne le masque.
BARREL_SLEEVE = 0.26
BARREL_SEG = 24
#: Hauteur de l'axe des tubes : au-dessus des coffrets, et assez haut pour que
#: le manchon passe par-dessus quand la tourelle pivote.
BARREL_Y = 0.98
#: Z de la CULASSE : au fond du masque, pas sur la face avant.
BARREL_Z = BODY_Z1 - MANTLET_DEPTH
#: Entraxe des deux tubes, et son maximum (le moteur ecarte pour la variete).
BARREL_GAUGE = 0.92
BARREL_GAUGE_MAX = 1.00

#: L'appareillage.
BOX_W, BOX_D, BOX_H = 0.92, 0.36, 0.42
PIPE_R = 0.08
PIPE_LEN = 1.20
#: Rayon ou l'appareillage se pose sur le plateau du socle.
FITTING_R = 1.66

#: L'ŒIL — reduit a des FENTES (regle 4 de la planche : « le magenta signale
#: l'energie, pas le volume »). Ce n'etait pas le cas avant BRIEF-0100 : une
#: lentille ronde de 0,36 m tenait lieu d'œil. Ici, un trait horizontal de
#: 0,32 m au fond du masque, deux traits verticaux sur les joues, et quatre
#: traits sur vingt-quatre modules du socle — tous de 3 cm d'epaisseur, et
#: l'emissif ne pese plus que 0,2 pct de l'aire vue.
EYE_W = 0.32
EYE_T = 0.03
EYE_RISE = 0.05
#: Les fentes de flanc, sur les plaques rapportees du bloc.
CHEEK_SLIT_H = 0.30
CHEEK_SLIT_T = 0.03

#: Meme densite que le borde : voir l'en-tete (deux echelles sur un meme slot).
TEXELS_PER_METER = cortege.HULL_TEXELS_PER_METER

#: ⚠️ GARDE-FOU D'EMBALLEMENT, PLUS UNE COTE A TENIR (voir l'en-tete). Trois
#: fois le compte mesure : il n'attrape qu'une boucle partie en vrille.
TRI_BUDGET_ASSEMBLED = 21_000
TRI_BUDGET_LEVEL = 360_000

#: Couleurs reservees aux TIRS (charte SS3) : interdites ici comme ailleurs.
FORBIDDEN_HEX = cortege.FORBIDDEN_HEX

#: Les huit noms de nœuds. Le moteur monte par le NOM : le harnais echoue si l'un
#: manque, si l'un est en trop, ou si l'un porte un enfant.
PART_NAMES = (
    "turret_pad", "turret_anchor_skirt", "turret_ring", "turret_body",
    "turret_barrel", "turret_barrel_short", "turret_service_box", "turret_pipe",
)

#: OU CHAQUE PIECE TOMBE DANS LA TOURELLE ASSEMBLEE, et combien de fois.
#: ⚠️ Ce n'est pas une commodite de rapport : sans elle, l'aire par materiau se
#: mesurerait dans le repere de CHAQUE piece, ou la jupe enterree du socle passe
#: pour visible.
ASSEMBLY_OFFSET: dict[str, tuple[float, float, float]] = {
    "turret_pad": (0.0, 0.0, 0.0),
    "turret_anchor_skirt": (0.0, 0.0, 0.0),
    "turret_ring": (0.0, RING_BASE, 0.0),
    "turret_body": (0.0, BODY_BASE, 0.0),
    "turret_barrel": (-BARREL_GAUGE * 0.5, BARREL_Y, BARREL_Z),
    "turret_barrel_short": (BARREL_GAUGE * 0.5, BARREL_Y, BARREL_Z),
    "turret_service_box": (0.0, PAD_SHELF_Y, FITTING_R),
    "turret_pipe": (0.0, PAD_SHELF_Y, -FITTING_R),
}
#: Le tube long est pose DEUX fois (les deux voies) et le coffret deux fois. Le
#: tube court est une ALTERNATIVE : il ne compte pas dans la tourelle assemblee,
#: sans quoi on facturerait quatre canons a une tourelle qui en porte deux.
ASSEMBLY_COPIES: dict[str, int] = {name: 1 for name in PART_NAMES}
ASSEMBLY_COPIES.update({"turret_barrel": 2, "turret_barrel_short": 0,
                        "turret_service_box": 2})

#: LES TROIS CLASSES DE LA PLANCHE — et c'est le moteur qui les fait, par
#: ECHELLE, a partir de ce seul kit. Le facteur s'applique au maillage ET aux
#: offsets d'assemblage (`cortege_turret.gd::_place`).
#:
#: (nom, echelle, jupe, tube, entraxe, angles des coffrets, angle du faisceau)
#:
#: ⚠️ Les deux facteurs viennent des LONGUEURS DE LA PLANCHE (3,5 / 6,5 / 10,0),
#: pas d'un arrondi de confort. Ce qui n'en vient pas, c'est l'echelle absolue :
#: la lourde est bornee par le plafond de gameplay, pas par la planche.
CLASSES: tuple[tuple, ...] = (
    ("legere", 0.538, False, "turret_barrel_short", 0.0, (), None),
    ("standard", 1.000, True, "turret_barrel", 0.92, (118.0, -118.0), 180.0),
    ("lourde", 1.200, True, "turret_barrel", 1.00, (96.0, -142.0), 205.0),
)
#: La legere ne pose QU'UN tube, decale du rang de montage — c'est ce que fait
#: deja `_build_light_head()`. Les coffrets, la conduite et la jupe sont ce qui
#: fait lire « installation » : les retirer est ce qui la distingue en noir et
#: blanc, pas sa seule taille.
LIGHT_BARREL_OFFSET = 0.0

#: LES TROIS FAMILLES DE VARIETE — a l'INTERIEUR d'une classe, et sans reforge.
#: Dix-sept tourelles identiques se liraient comme dix-sept fois la meme.
#: (nom, jupe, tube, entraxe, nb de coffrets, angles, faisceau, angle)
FAMILIES: tuple[tuple, ...] = (
    ("A - avancee", False, "turret_barrel_short", 0.80, 1, (128.0,), False, 0.0),
    ("B - de borde", True, "turret_barrel", 0.92, 2, (118.0, -118.0), True, 180.0),
    ("C - lourde", True, "turret_barrel", 1.00, 2, (96.0, -142.0), True, 205.0),
)


# ==========================================================================
# Primitives — bobinage CALCULE, jamais suppose
# ==========================================================================


def _new_object(name: str, bm: bmesh.types.BMesh) -> bpy.types.Object:
    """Objet a 7 slots normalises, SANS `recalc_face_normals`.

    Meme raison que sur la coque et sur `bay_kit` : l'heuristique de bmesh peut
    retourner une piece entiere, et une piece retournee DISPARAIT en jeu (culling
    arriere) sans qu'aucune bbox, aucun compte de triangles ni aucune mesure d'UV
    ne le voie. Les sens sont poses par calcul, et `_assert_solid()` les relit.
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


def _face_facing(bm: bmesh.types.BMesh, verts: list, material: str, want: Vector):
    """Une face dont la normale part du cote `want`. Deterministe."""
    if len(verts) < 3:
        return None
    normal = (verts[1].co - verts[0].co).cross(verts[2].co - verts[0].co)
    order = list(verts) if normal.dot(want) >= 0.0 else list(reversed(verts))
    return _face(bm, order, material)


def _quad_facing(bm: bmesh.types.BMesh, a, b, c, d, material: str, want: Vector):
    """Un quad dont la normale part du cote `want`. Deterministe."""
    verts = [a, b, c, d]
    normal = (b.co - a.co).cross(c.co - a.co)
    if normal.dot(want) < 0.0:
        verts.reverse()
    return _face(bm, verts, material)


def _module_relief(segments: int, modules: int) -> tuple[float, ...]:
    """1,0 sur une SEMELLE, 0,0 dans un JOINT — un sommet sur trois.

    ⚠️ C'EST LA RECETTE 1 DU BRIEF, ET ELLE NE COUTE PAS UN MAILLAGE DE PLUS.
    Le modele tiers pose vingt-quatre secteurs blindes comme vingt-quatre objets
    (plus leurs panneaux, verrous et boulons : 120 maillages pour le seul socle).
    Ici, le meme decoupage est obtenu en MODULANT LE RAYON du meme anneau de
    revolution : deux sommets au rayon plein, un sommet en retrait. Chaque module
    montre donc une facette plate et une gorge en V, sur toute la hauteur du
    tambour — et le socle reste UNE coque fermee, ce qui est la seule chose que
    `_assert_solid()` sait prouver.

    ⚠️ Et c'est un TUPLE, jamais un `set` : le brief le dit, le script tiers itere
    sur `set(asset.objects)` et ce motif ne se porte pas — l'ordre d'un `set`
    Python n'est pas garanti d'une execution a l'autre, et le `.glb` ne serait
    plus byte-identique (`ADR-0008`, `build-hull.sh --check`).
    """
    per = segments // modules
    return tuple(0.0 if (k % per) == per - 1 else 1.0 for k in range(segments))


def _circle(radius: float, segments: int, phase: float = 0.0,
            relief: tuple[float, ...] | None = None,
            depth: float = 0.0) -> list[tuple[float, float]]:
    """Points (x, z) d'un polygone regulier CENTRE SUR L'ORIGINE.

    `relief`/`depth` creusent le rayon la ou le relief vaut 0 : c'est ainsi que
    le socle porte ses vingt-quatre modules sans une piece de plus.

    ⚠️ Centre sur l'origine, et pas ailleurs : c'est de cette fonction que depend
    le fait que `turret_ring` tourne sur place. `_assert_on_axis()` le reverifie
    sur le binaire, parce qu'une faute ici ne se verrait qu'en jeu, en mouvement.
    """
    points = []
    for k in range(segments):
        a = phase + 2.0 * math.pi * k / segments
        r = radius - (depth * (1.0 - relief[k]) if relief is not None else 0.0)
        points.append((r * math.cos(a), r * math.sin(a)))
    return points


def _levels(base: float, relief: tuple[float, ...], lift: float) -> list[float]:
    """Une hauteur PAR SOMMET : les panneaux d'acces du plateau, en relief."""
    return [base + lift * relief[k] for k in range(len(relief))]


def _octagon(hx: float, hz: float, chamfer: float) -> list[tuple[float, float]]:
    """Rectangle 2hx x 2hz aux quatre coins coupes. Sens trigonometrique.

    ⚠️ LE CHANFREIN EST UNE DES DEUX DEPENSES PRINCIPALES DE CE KIT. Un coin a
    90 deg ne rend aucune lumiere ; un coin coupe de 26 cm porte une bande claire
    sur toute la hauteur du bloc, a n'importe quelle distance. C'est ce qui fait
    qu'un cube gris se lit comme du blindage et non comme une boite.
    """
    return [
        (hx, hz - chamfer), (hx - chamfer, hz),
        (-(hx - chamfer), hz), (-hx, hz - chamfer),
        (-hx, -(hz - chamfer)), (-(hx - chamfer), -hz),
        (hx - chamfer, -hz), (hx, -(hz - chamfer)),
    ]


def _safe_octagon(hx: float, hz: float,
                  chamfer: float) -> list[tuple[float, float]]:
    """Un octogone dont le chanfrein TIENT DANS LA BOITE, quoi qu'on demande.

    ⚠️ CE GARDE-FOU A ETE ECRIT APRES COUP, ET LA FAUTE ETAIT SILENCIEUSE DANS
    LE PIRE SENS. Les fentes magenta font 1,5 cm de demi-largeur ; le chanfrein
    par defaut en faisait 2, ce qui RETOURNE l'octogone — ses coins passent de
    l'autre cote de ses aretes. `_assert_solid()` l'a vu (32 aretes parcourues
    deux fois dans le meme sens), mais aucune bbox, aucun compte de triangles et
    aucune mesure d'UV ne l'aurait vu : trois fentes retournees auraient
    simplement disparu en jeu.

    Le chanfrein est donc borne des deux cotes : jamais plus de la moitie du
    plus petit demi-cote, jamais nul non plus — un chanfrein nul dedoublerait
    les sommets de l'octogone, que le soudage fusionnerait en un maillage non
    manifold.
    """
    limit = min(hx, hz)
    return _octagon(hx, hz, max(min(chamfer, limit * 0.49), limit * 0.15))


def _loft_y(bm: bmesh.types.BMesh,
            rings: list[tuple[list[tuple[float, float]], object]],
            materials: list[str],
            skip: set[tuple[int, int]] | None = None,
            patch: dict[tuple[int, int], str] | None = None) -> list[list]:
    """Relie des anneaux fermes empiles en Y. Rend les sommets, anneau par anneau.

    `rings` : (points (x, z), y), du bas vers le haut, PUIS vers l'interieur si le
    profil rentre (une cuvette, une gorge). `y` est un flottant, ou UNE HAUTEUR
    PAR SOMMET (les panneaux d'acces en relief du plateau).
    `materials` : un par bande. `patch` : le materiau d'un (bande, segment)
    precis — c'est ainsi qu'on pose quatre fentes magenta sur vingt-quatre
    modules sans emettre une seule face de plus.
    `skip` : les (bande, segment) a ne pas emettre — c'est ainsi qu'on PERCE une
    facette pour y creuser un masque, sans jamais supprimer une face apres coup.

    ⚠️ LE SENS DES FACES EST CALCULE PAR PRODUIT VECTORIEL, ET LA REGLE A CHANGE
    LE 2026-08-29. Elle etait « la normale part du cote oppose a l'axe ». C'est
    FAUX partout ou le profil rentre, et c'est mesure, pas suppose : le socle
    sortait avec 41 faces retournees — tout son plateau, toute la paroi de sa
    cuvette et son fond — parce qu'une surface qui regarde vers le haut ou vers
    l'interieur d'un creux ne regarde pas « loin de l'axe ». Elles auraient
    disparu en jeu par culling arriere, sans une ligne au journal.

    La regle juste ne parle pas de l'axe du tout : les anneaux etant ordonnes dans
    le sens trigonometrique, la normale sortante d'un quad vaut

        (montee du profil)  x  (sens de parcours de l'anneau)
    """
    verts = []
    for points, level in rings:
        heights = level if isinstance(level, (list, tuple)) else [level] * len(points)
        verts.append([bm.verts.new(Vector((x, heights[i], z)))
                      for i, (x, z) in enumerate(points)])
    blocked = skip or set()
    tweaks = patch or {}
    for k in range(len(rings) - 1):
        low, high = verts[k], verts[k + 1]
        count = len(low)
        for i in range(count):
            if (k, i) in blocked:
                continue
            j = (i + 1) % count
            climb = (high[i].co + high[j].co - low[i].co - low[j].co) * 0.5
            along = low[j].co - low[i].co
            want = climb.cross(along)
            if want.length < 1e-9:
                want = (high[j].co - high[i].co).cross(climb)
            _quad_facing(bm, low[i], low[j], high[j], high[i],
                         tweaks.get((k, i), materials[k]), want)
    return verts


def _cap_low(bm: bmesh.types.BMesh, ring: list, material: str) -> None:
    """Ferme le PREMIER anneau d'un empilement en Y : la face regarde vers -Y."""
    _face_facing(bm, list(ring), material, Vector((0.0, -1.0, 0.0)))


def _cap_high(bm: bmesh.types.BMesh, ring: list, material: str) -> None:
    """Ferme le DERNIER anneau d'un empilement en Y : la face regarde vers +Y.

    ⚠️ ET C'EST LA QU'ON S'ETAIT TROMPE. Le socle et la jupe fermaient leur
    dernier anneau vers le BAS — le fond de la cuvette regardait le sol. Deux
    faces, invisibles a toute mesure de bbox, de triangles ou d'UV, et le fond de
    la cuvette disparaissait en jeu. Les deux fonctions existent donc separement
    plutot qu'un `want` passe a l'appel : un sens qu'on ECRIT a chaque appel est
    un sens qu'on finit par ecrire a l'envers. `_assert_solid()` le reverifie.
    """
    _face_facing(bm, list(ring), material, Vector((0.0, 1.0, 0.0)))


def _loft_z(bm: bmesh.types.BMesh, stops: list[tuple[float, float]],
            segments: int, materials: list[str],
            cx: float = 0.0, cy: float = 0.0) -> list[list]:
    """Un tube : anneaux circulaires empiles le long de +Z. Normales calculees.

    `stops` : (z, rayon) de la culasse vers la bouche, PUIS vers l'arriere si le
    profil rentre dans l'alesage. Un materiau par bande. Meme regle que
    `_loft_y` — (parcours) x (montee) — et pour la meme raison : la bouche du
    canon est CREUSEE, donc sa chemise regarde vers l'axe. Elle rend le bon cote
    pour une paroi de tube, pour une couronne de levre a z constant et pour un
    alesage qui revient vers la culasse, sans qu'on ait a le declarer nulle part.
    """
    verts = []
    for z, radius in stops:
        ring = []
        for k in range(segments):
            a = 2.0 * math.pi * k / segments
            ring.append(bm.verts.new(
                Vector((cx + radius * math.cos(a), cy + radius * math.sin(a), z))))
        verts.append(ring)
    for k in range(len(stops) - 1):
        low, high = verts[k], verts[k + 1]
        for i in range(segments):
            j = (i + 1) % segments
            climb = (high[i].co + high[j].co - low[i].co - low[j].co) * 0.5
            along = low[j].co - low[i].co
            # ⚠️ `along x climb` et non l'inverse : les anneaux de `_loft_z`
            # tournent dans l'autre sens que ceux de `_loft_y` (l'angle y decrit
            # (x, y), ici (x, z)). Verifie sur un temoin au demarrage.
            want = along.cross(climb)
            if want.length < 1e-9:
                want = Vector((0.0, 0.0, 1.0))
            _quad_facing(bm, low[i], low[j], high[j], high[i], materials[k], want)
    return verts


def _cap_z(bm: bmesh.types.BMesh, ring: list, material: str,
           entering: bool) -> None:
    """Ferme un anneau de `_loft_z` : -Z a l'entree du profil, +Z a sa sortie."""
    _face_facing(bm, list(ring), material,
                 Vector((0.0, 0.0, -1.0 if entering else 1.0)))


def _shift_xz(points: list[tuple[float, float]], dx: float,
              dz: float) -> list[tuple[float, float]]:
    """Decale un profil (x, z)."""
    return [(x + dx, z + dz) for x, z in points]


def _shift(points: list[tuple[float, float]],
           dz: float) -> list[tuple[float, float]]:
    """Decale un profil (x, z) le long de Z."""
    return [(x, z + dz) for x, z in points]


def _chamfered_block(bm: bmesh.types.BMesh, hx: float, hz: float,
                     y0: float, y1: float, chamfer: float, inset: float,
                     side_material: str, top_material: str,
                     cx: float = 0.0, cz: float = 0.0,
                     skip: set[tuple[int, int]] | None = None,
                     bands: list[str] | None = None) -> list[list]:
    """Un pave dont les DOUZE grandes aretes sont coupees. Coque FERMEE.

    Quatre aretes verticales par l'octogone, quatre en haut et quatre en bas par
    un anneau en retrait de `inset`. `bands` permet de donner un materiau par
    bande : c'est ainsi qu'une plaque rapportee porte un RETRAIT sombre a sa base
    et un LISERE clair a son bord superieur — la recette 2 du brief, et la
    depense la plus rentable du fichier.

    ⚠️ Le fond est TOUJOURS ferme, meme enterre dans une autre piece. Un pave
    ouvert par-dessous n'est pas un solide : sa normale de bord ne se verifie pas,
    et le harnais ne peut plus prouver que rien n'est retourne. Deux triangles
    invisibles sont moins chers qu'un controle qu'on ne peut plus faire.
    """
    inset = min(inset, hx * 0.4, hz * 0.4)
    lip = min(inset, (y1 - y0) * 0.35)
    profile = [_shift_xz(_safe_octagon(hx - inset, hz - inset,
                                       chamfer - inset), cx, cz),
               _shift_xz(_safe_octagon(hx, hz, chamfer), cx, cz)]
    rings = [(profile[0], y0), (profile[1], y0 + lip),
             (profile[1], y1 - lip), (profile[0], y1)]
    verts = _loft_y(bm, rings, bands or [side_material] * 3, skip=skip)
    _cap_high(bm, verts[-1], top_material)
    _cap_low(bm, verts[0], "AA_Greeble")
    return verts


def _plate_on(bm: bmesh.types.BMesh, hx: float, hz: float, y0: float, y1: float,
              cx: float = 0.0, cz: float = 0.0, chamfer: float = 0.06,
              inset: float = 0.04, face: str = "AA_Hull") -> list[list]:
    """UNE PLAQUE RAPPORTEE, ET C'EST LA RECETTE 2 DU BRIEF.

    Trois bandes, trois materiaux, et chacune fait un travail que les deux autres
    ne font pas :

        AA_Greeble  le RETRAIT — la plaque ne touche pas la coque, elle laisse un
                    joint sombre de la hauteur du chanfrein bas ;
        AA_Panel    la PLAQUE elle-meme, violet sombre ;
        AA_Trim     le LISERE, ivoire froid, sur le bord superieur.

    ⚠️ C'est le seul detail du kit qui satisfait les DEUX seuils mesures a la
    fois (`docs/forge/textures/README.md`) : le lisere passe le seuil de presence
    (~4,4 cm de monde) ET tranche de bien plus que les dix niveaux du plancher de
    contraste — ivoire 0,85 de metallicite sur anthracite. Un contour de 27 px
    qui ne module que quatre niveaux se lit MOINS bien qu'une gorge de 5,9 px qui
    tranche en noir : la taille ne suffit pas, il faut le contraste.
    """
    return _chamfered_block(bm, hx, hz, y0, y1, chamfer, inset,
                            face, face, cx=cx, cz=cz,
                            bands=["AA_Greeble", face, "AA_Trim"])


# ==========================================================================
# LE SOCLE — vingt-quatre semelles blindees, et non un jeton
# ==========================================================================

#: Les quatre modules sur vingt-quatre qui portent une fente magenta. ⚠️ UN
#: TUPLE, ET IL EST ECRIT : le modele tiers ecrit `if i in [2,8,14,20]`, ce qui
#: se porte ; ce qui ne se porte pas, c'est son `set(asset.objects)`.
PAD_GLOW_MODULES = (2, 8, 14, 20)


def build_pad() -> bpy.types.Object:
    """`turret_pad`. Origine : centre du socle, Y = plan d'assise sur la peau.

    Douze anneaux, onze bandes, et chacune fait un travail :

        -2,00 -> -0,30   la JUPE ENTERREE, en depouille. ⚠️ Deux metres, et non
                         85 cm : l'assise est calculee sur un disque de 2,08 m
                         alors que le socle d'une LEGERE ne fait que 0,73 m de
                         rayon a l'echelle 0,35 — le creux sous elle vaut encore
                         0,643 m, sa jupe n'en couvrait que 0,298, et les
                         tourelles legeres flottaient. C'est enterre : ça ne
                         coute que des triangles qu'on ne voit pas.
        -0,30 -> +0,13   le CHANFREIN d'assise puis le pied des semelles.
        +0,13 -> +0,16   la bande des FENTES : trois centimetres, quatre modules
                         sur vingt-quatre en magenta (regle 4 de la planche).
        +0,16 -> +0,26   le haut des semelles, ferme par un LISERE ivoire.
        +0,26 -> +0,30   le couronnement, puis la retombee vers le plateau.
        +0,30 -> plateau les vingt-quatre PANNEAUX D'ACCES, en relief de 3 cm et
                         en violet sombre, separes par des joints noirs.
        cuvette          la levre claire, puis la paroi ou la couronne se LOGE.

    ⛔ AUCUN EMISSIF DE VOLUME ICI. Le socle de BRIEF-0089 avait un cœur magenta
    plein — un « jeton lumineux ». Ce qui reste tient en quatre traits de 3 cm.
    """
    bm = bmesh.new()
    relief = _module_relief(PAD_SEG, PAD_MODULES)
    shoe = _circle(PAD_R, PAD_SEG, relief=relief, depth=PAD_JOINT)
    rings: list[tuple[list[tuple[float, float]], object]] = [
        (_circle(PAD_R - 0.34, PAD_SEG), -PAD_BURIED),
        (_circle(PAD_R - 0.10, PAD_SEG), -0.26),
        (shoe, -0.10),
        (shoe, 0.11),
        (shoe, 0.14),
        (shoe, 0.19),
        (_circle(PAD_R - 0.03, PAD_SEG, relief=relief, depth=PAD_JOINT), 0.22),
        (_circle(PAD_R - 0.10, PAD_SEG, relief=relief, depth=PAD_JOINT),
         PAD_RIM_H),
        (_circle(PAD_SHELF_R0, PAD_SEG),
         _levels(PAD_SHELF_Y, relief, 0.025)),
        (_circle(PAD_WELL_R + 0.12, PAD_SEG), 0.23),
        (_circle(PAD_WELL_R + 0.08, PAD_SEG), 0.27),
        (_circle(PAD_WELL_R, PAD_SEG), PAD_WELL_Y),
    ]
    materials = [
        "AA_Greeble",   # jupe enterree
        "AA_Hull",      # chanfrein d'assise
        "AA_Hull",      # pied des semelles
        "AA_Hull",      # LA BANDE DES FENTES (patchee ci-dessous)
        "AA_Hull",      # haut des semelles
        "AA_Greeble",   # LE LISERE — pointille, patche semelle par semelle
        "AA_Hull",      # couronnement
        "AA_Hull",      # retombee vers le plateau
        "AA_Panel",     # le plateau et ses panneaux d'acces
        "AA_Hull",      # levre de cuvette
        "AA_Greeble",   # paroi de la cuvette
    ]
    # Les fentes : bande 3, sur la facette PLEINE de quatre modules seulement.
    patch: dict[tuple[int, int], str] = {}
    for module in PAD_GLOW_MODULES:
        patch[(3, module * 3)] = "AA_Emissive_Engine"
    # Les joints entre panneaux d'acces : bande 8, sur le segment de gorge.
    for module in range(PAD_MODULES):
        patch[(8, module * 3 + 2)] = "AA_Greeble"
    # ⚠️ LE LISERE EST POINTILLE, ET C'EST UNE CORRECTION DE RENDU MESUREE SUR
    # LA PLANCHE. Pose en anneau CONTINU au premier jet, il rendait un HALO
    # BLANC autour de chaque tourelle a la camera du jeu — la faute exacte que
    # BRIEF-0089 avait chiffree et que ce fichier documente sur `AA_Hull` de la
    # jupe. Un materiau clair sur une arete continue occupe plus de pixels
    # qu'une piece entiere. Un trait PAR SEMELLE dit la meme chose — « les
    # plaques sont separees, leurs joints sont bordes d'une arete claire » — et
    # ne cerne plus la piece.
    for module in range(PAD_MODULES):
        patch[(5, module * 3)] = "AA_Trim"
    verts = _loft_y(bm, rings, materials, patch=patch)
    # ⚠️ Le dernier anneau est le FOND DE LA CUVETTE, et il regarde le CIEL.
    _cap_high(bm, verts[-1], "AA_Greeble")
    _cap_low(bm, verts[0], "AA_Greeble")
    return _new_object("turret_pad", bm)


def build_anchor_skirt() -> bpy.types.Object:
    """`turret_anchor_skirt` — la jupe d'ancrage SUPPLEMENTAIRE, optionnelle.

    Premiere des trois familles de variete : le moteur la pose ou ne la pose pas.
    C'est un anneau ferme, large, enterre plus profond que le socle ; douze
    modules, un lisere ivoire sur son bandeau.

    ⚠️ Son rayon hors-tout EST l'emprise du kit — la meme valeur que
    `cortege.TURRET_FOOTPRINT_R`, avec laquelle la coque echantillonne sa peau
    pour poser l'assise du marqueur. Le harnais refuse qu'elles divergent.

    ⚠️ UN ANNEAU FERME, PAS UN DISQUE. La jupe se refermait par un couvercle
    plein tout entier sous le socle : des metres carres que rien ne peut voir,
    comptes comme visibles dans la repartition par materiau. Le profil revient
    donc sur lui-meme.

    ⚠️ LA COURONNE VISIBLE EST EN `AA_Hull`, PAS EN `AA_Trim`. L'ivoire froid sur
    un anneau qui fait le TOUR de la piece, c'est la faute que BRIEF-0089 a
    chiffree : un materiau clair pose sur une arete CONTINUE occupe plus de
    pixels qu'une piece entiere, et l'effet etait un halo blanc autour de chaque
    tourelle, qui volait le contraste aux projectiles. L'ivoire ne va que sur ce
    qui est ETROIT : liseres, levre de cuvette, coffrets, conduites.
    """
    bm = bmesh.new()
    relief = _module_relief(SKIRT_SEG, SKIRT_MODULES)
    band = _circle(SKIRT_R, SKIRT_SEG, relief=relief, depth=SKIRT_JOINT)
    low = _circle(SKIRT_R - 0.30, SKIRT_SEG)
    rings: list[tuple[list[tuple[float, float]], object]] = [
        (low, -SKIRT_BURIED),
        (band, -0.30),
        (band, -0.06),
        (_circle(SKIRT_R - 0.03, SKIRT_SEG, relief=relief, depth=SKIRT_JOINT),
         -0.02),
        (_circle(SKIRT_R - 0.12, SKIRT_SEG, relief=relief, depth=SKIRT_JOINT),
         SKIRT_TOP),
        (_circle(PAD_R - 0.04, SKIRT_SEG), SKIRT_TOP),
        (_circle(PAD_R - 0.10, SKIRT_SEG), -0.18),
        (_circle(PAD_R - 0.10, SKIRT_SEG), -SKIRT_BURIED + 0.06),
        (low, -SKIRT_BURIED),
    ]
    _loft_y(bm, rings,
            ["AA_Greeble",   # depouille exterieure, enterree
             "AA_Hull",      # chanfrein d'assise
             "AA_Greeble",   # LE LISERE du bandeau — pointille (voir build_pad)
             "AA_Hull",      # couronnement des modules
             "AA_Hull",      # dessus annulaire, autour du socle
             "AA_Greeble",   # paroi interieure, sous le socle
             "AA_Greeble",
             "AA_Greeble"],  # fond annulaire
            patch={(2, module * 3): "AA_Trim"
                   for module in range(SKIRT_MODULES)})
    return _new_object("turret_anchor_skirt", bm)


# ==========================================================================
# LA COURONNE — c'est ELLE qui tourne, et son origine EST son axe
# ==========================================================================


def build_ring() -> bpy.types.Object:
    """`turret_ring`. Origine : SUR L'AXE DE ROTATION, au fond de la cuvette.

    ⚠️ CETTE PIECE EST LA SEULE DU KIT DONT L'ORIGINE SOIT UN MECANISME ET NON UN
    POINT DE POSE. Le moteur la fait tourner a 42 deg/s autour de son Y ; si son
    maillage n'est pas centre sur cet axe au micron, la tourelle balaie en
    decrivant un cercle au lieu de pivoter sur place — et ça ne se voit qu'en jeu,
    EN MOUVEMENT, donc jamais sur une planche. `_assert_on_axis()` le relit sur le
    binaire produit.

    Huit anneaux : une portee basse en retrait (l'ombre qui dit « logee »), le
    fut, une PISTE SEGMENTEE en seize modules a mi-hauteur — c'est elle qui donne
    un pas de rotation lisible quand la piece tourne, la recette du chemin de
    roulement du modele tiers — son lisere poli, puis la portee ou s'assied le
    bloc.
    """
    bm = bmesh.new()
    relief = _module_relief(RING_SEG, RING_MODULES)
    track = _circle(RING_R - 0.05, RING_SEG, relief=relief, depth=0.05)
    rings: list[tuple[list[tuple[float, float]], object]] = [
        (_circle(RING_R - 0.12, RING_SEG), 0.0),
        (_circle(RING_R, RING_SEG), 0.09),
        (_circle(RING_R, RING_SEG), 0.14),
        (track, 0.17),
        (track, 0.24),
        (_circle(RING_R - 0.02, RING_SEG), 0.27),
        (_circle(RING_R - 0.02, RING_SEG), RING_H - 0.06),
        (_circle(RING_R - 0.16, RING_SEG), RING_H),
    ]
    verts = _loft_y(bm, rings,
                    ["AA_Hull",      # portee basse, en retrait
                     "AA_Hull",      # fut
                     "AA_Greeble",   # entree de la piste
                     "AA_Panel",     # LA PISTE SEGMENTEE
                     "AA_Greeble",   # son lisere poli, pointille
                     "AA_Hull",      # fut haut
                     "AA_Hull"],     # chanfrein de couronnement
                    patch={(4, module * 3): "AA_Trim"
                           for module in range(RING_MODULES)})
    _cap_high(bm, verts[-1], "AA_Hull")
    _cap_low(bm, verts[0], "AA_Greeble")
    return _new_object("turret_ring", bm)


# ==========================================================================
# LE BLOC BLINDE — trapu, plaques rapportees, masque REELLEMENT creuse
# ==========================================================================

#: Le masque occupe TOUTE la facette avant plate de la bande mediane du bloc.
#: L'index 1 est le segment (sommet 1 -> sommet 2) de l'octogone, c'est-a-dire sa
#: face +Z ; la bande 1 est celle qui va de `lip` a `BODY_H - 0,18`.
_MANTLET_BAND = 1
_MANTLET_FACET = 1


def build_body() -> bpy.types.Object:
    """`turret_body`. Origine : sur l'axe de rotation, au sommet de la couronne.

    ⚠️ RECTANGULAIRE TRAPU, SURTOUT PAS UNE SPHERE (planche, module C : « bloc
    canon blinde, geometrie simple »). Un dome se lit comme un jeton vu de dessus
    a 20 deg de la verticale. Un pave chanfreine, lui, montre trois faces de
    valeurs differentes des qu'une lumiere cle l'eclaire : il a un AVANT.

    Dix coques fermees, et chacune est une lecture :

        1. le pave principal, chanfreine sur ses douze aretes, dont la FACETTE
           AVANT EST PERCEE ;
        2. le MASQUE : la facette percee est refermee 16 cm plus loin, en
           depouille. Les canons y sont LOGES — culasse au fond du creux, pas sur
           la face avant ;
        3-4. les DEUX PLAQUES DE FLANC, posees sur un retrait sombre et bordees
           d'un lisere ivoire (recette 2) ;
        5-6. les DEUX DALLES DE TOIT, meme traitement ;
        7. le viseur, etroit, qui porte la cote de hauteur totale ;
        8. le bloc de recul arriere, en surplomb : il donne une POUPE au bloc, ce
           qui fait qu'on lit d'un coup d'œil ou la tourelle regarde, meme
           immobile et meme en noir et blanc ;
        9-10. LES FENTES : un trait horizontal au fond du masque, deux traits
           verticaux sur les joues. C'est tout le magenta du bloc.

    ⚠️ DES COQUES FERMEES, PAS UN AMAS DE FACES. C'est ce qui permet a
    `_assert_solid()` de prouver, composante par composante, que rien n'est
    retourne : une nappe ouverte n'a pas de volume, donc pas de preuve.

    ⚠️ ET LA PLACE DE L'ELEVATION EST GARDEE, SANS ETRE GREEE (BRIEF-0100,
    « Animation »). Le berceau est plat sur toute sa largeur entre les deux
    manchons et le masque est en depouille : un tourillon transversal viendrait
    s'y loger sans toucher a la forme. Rien n'est cuit ici — le kit ne livre
    aucune animation, c'est le moteur qui compose et qui fait tourner.
    """
    bm = bmesh.new()
    hz = (BODY_Z1 - BODY_Z0) * 0.5
    cz = (BODY_Z1 + BODY_Z0) * 0.5
    lip = 0.09
    top_lip = 0.11

    # 1. Le pave, sa facette avant PERCEE (le masque la refermera).
    rings = [
        (_shift(_octagon(BODY_HX - lip, hz - lip, BODY_CHAMFER - lip), cz), 0.0),
        (_shift(_octagon(BODY_HX, hz, BODY_CHAMFER), cz), lip),
        (_shift(_octagon(BODY_HX, hz, BODY_CHAMFER), cz), BODY_H - top_lip),
        (_shift(_octagon(BODY_HX - 0.09, hz - 0.09, BODY_CHAMFER - 0.05), cz),
         BODY_H),
    ]
    # Les deux flancs du pave passent en RETRAIT SOMBRE : c'est sur eux que les
    # plaques rapportees viennent se poser (recette 2).
    verts = _loft_y(bm, rings, ["AA_Hull", "AA_Hull", "AA_Hull"],
                    skip={(_MANTLET_BAND, _MANTLET_FACET)},
                    patch={(1, 3): "AA_Greeble", (1, 7): "AA_Greeble"})
    _cap_high(bm, verts[-1], "AA_Hull")
    _cap_low(bm, verts[0], "AA_Greeble")

    # 2. LE MASQUE. Les quatre sommets du trou, dans l'ordre ou `_loft_y` les
    #    aurait employes, puis le fond en retrait et en depouille.
    lo, hi = verts[_MANTLET_BAND], verts[_MANTLET_BAND + 1]
    i, j = _MANTLET_FACET, _MANTLET_FACET + 1
    rim = [lo[i], lo[j], hi[j], hi[i]]
    floor_z = BODY_Z1 - MANTLET_DEPTH
    d = MANTLET_DRAFT
    deep = [bm.verts.new(Vector((v.co.x - math.copysign(d, v.co.x),
                                 v.co.y + (d if k >= 2 else -d), floor_z)))
            for k, v in enumerate(rim)]
    centre = Vector((0.0, (lo[i].co.y + hi[i].co.y) * 0.5, floor_z))
    for k in range(4):
        m = (k + 1) % 4
        mid = (rim[k].co + rim[m].co + deep[k].co + deep[m].co) * 0.25
        want = centre - mid
        want.z = 0.0
        if want.length < 1e-9:
            want = Vector((0.0, 0.0, 1.0))
        _quad_facing(bm, rim[k], rim[m], deep[m], deep[k], "AA_Trim", want)
    _face_facing(bm, deep, "AA_Greeble", Vector((0.0, 0.0, 1.0)))

    # 3-4. LES PLAQUES DE FLANC. Posees sur le retrait sombre, liseré en haut.
    for side in (-1.0, 1.0):
        _plate_on(bm, 0.07, hz - 0.30, 0.14, 0.70,
                  cx=side * (BODY_HX + 0.01), cz=cz - 0.06,
                  chamfer=0.05, inset=0.035)
    # 5-6. LES DALLES DE TOIT, meme traitement.
    for side in (-1.0, 1.0):
        _plate_on(bm, 0.30, hz - 0.32, BODY_H - 0.04, BODY_H + 0.09,
                  cx=side * 0.58, cz=cz - 0.10, chamfer=0.07, inset=0.045,
                  face="AA_Panel")

    # 7. Le viseur : le seul volume qui monte au-dessus du bloc. Il est ETROIT —
    #    c'est ce qui fait qu'une tourelle n'a pas la meme tete de face et de
    #    profil, donc qu'on lit ou elle regarde meme immobile.
    _chamfered_block(bm, 0.26, 0.34, BODY_H - 0.04, BODY_H + SIGHT_H, 0.09, 0.06,
                     "AA_Hull", "AA_Trim", cz=cz + 0.20,
                     bands=["AA_Greeble", "AA_Hull", "AA_Trim"])
    # 8. Le bloc de recul / radiateur, en surplomb a l'arriere. Il est POSE assez
    #    haut pour que la rotation ne le fasse jamais passer sur un coffret :
    #    le harnais mesure ce degagement, il n'est pas laisse a l'œil.
    _chamfered_block(bm, 0.56, 0.16, 0.28, 0.78, 0.12, 0.08,
                     "AA_Hull", "AA_Trim", cz=BODY_Z0 - 0.14,
                     bands=["AA_Greeble", "AA_Hull", "AA_Trim"])

    # 9-10. LES FENTES. ⚠️ RECETTE 4 DU BRIEF, ET C'EST UN CHANGEMENT DE NATURE :
    # l'œil rond de 0,36 m a disparu. Le magenta ne fait plus de surface, il fait
    # des TRAITS de 3 cm — un au fond du masque, entre les deux tubes, deux sur
    # les joues. Eteints, ils restent lisibles : ce sont des reliefs dans une
    # ombre.
    eye_y = BARREL_Y - BODY_BASE
    _chamfered_block(bm, EYE_W * 0.5, EYE_RISE * 0.5,
                     eye_y - EYE_T * 0.5, eye_y + EYE_T * 0.5,
                     0.02, 0.008, "AA_Emissive_Engine", "AA_Emissive_Engine",
                     cz=floor_z + EYE_RISE * 0.5)
    for side in (-1.0, 1.0):
        _chamfered_block(bm, CHEEK_SLIT_T * 0.5, 0.02,
                         0.26, 0.26 + CHEEK_SLIT_H, 0.008, 0.005,
                         "AA_Emissive_Engine", "AA_Emissive_Engine",
                         cx=side * (BODY_HX + 0.09), cz=cz + hz - 0.46)
    return _new_object("turret_body", bm)


# ==========================================================================
# LES CANONS — chemises en gradins, bouche REELLEMENT creuse
# ==========================================================================

#: Les rayons des trois gradins de chemise, du plus large a la culasse au plus
#: etroit vers la bouche (recette 3). Puis le tube nu.
JACKET_R = (0.235, 0.215, 0.195)
TUBE_R = 0.17


def _barrel(name: str, length: float) -> bpy.types.Object:
    """UN tube ; le moteur en pose deux, paralleles. Origine : LA CULASSE.

    ⚠️ RECETTE 3 DU BRIEF. Le profil d'avant avait cinq paliers et une bouche
    fermee par un disque en retrait. Celui-ci en a vingt et un, et chaque groupe
    est une lecture :

        0,00 -> 0,32     le MANCHON de recul, plus gros que le tube, ferme par un
                         LISERE clair. C'est lui qui dit que le canon sort d'un
                         mecanisme et non d'un trou, et c'est lui qui dimensionne
                         l'ouverture du masque.
        0,32 -> L-0,86   TROIS GRADINS DE CHEMISE, 0,245 -> 0,225 -> 0,205 m de
                         rayon, chacun ferme par un lisere et un epaulement
                         sombre. C'est la difference entre « un tube » et « un
                         canon chemise » : trois ombres portees au lieu d'aucune.
        L-0,86 -> L-0,10 le tube nu, puis le FREIN DE BOUCHE en renflement.
        L-0,10 -> L      la levre claire.
        L      -> L-0,55 L'ALESAGE, ET IL EST REELLEMENT CREUX : couronne de
                         levre, chemise, puis un fond sombre en retrait de 55 cm.
                         Un disque plein se lit comme un bouchon.

    ⚠️ 0,42 m de diametre pour un canon de vaisseau, c'est enorme, et c'est
    delibere : a 41 px/m sur le pont, un tube « juste » de 12 cm ferait 5 px de
    large — le seuil de FORME est a 3 px, on verrait qu'il y a quelque chose sans
    voir quoi. 42 cm en font 17.

    ⚠️ ET LA BOUCHE CREUSEE EST CE QUI A FAIT ECHOUER LE HARNAIS D'ORIENTATION
    D'AVANT. Sa chemise regarde vers l'axe du tube — elle le doit, c'est un trou —
    et la regle « toute face regarde loin de l'axe » la declarait retournee. Voir
    `_assert_solid()`.
    """
    bm = bmesh.new()
    stops: list[tuple[float, float]] = [(0.0, BARREL_SLEEVE),
                                        (0.24, BARREL_SLEEVE),
                                        (0.28, BARREL_SLEEVE)]
    materials = ["AA_Hull",         # le manchon
                 "AA_Trim"]         # son lisere
    stops.append((0.32, JACKET_R[0]))
    materials.append("AA_Greeble")  # l'epaulement d'entree
    step = (length - 0.32 - 0.86) / 3.0
    for k in range(3):
        end = 0.32 + (k + 1) * step
        stops.append((end - 0.12, JACKET_R[k]))
        materials.append("AA_Hull")     # le corps du gradin
        stops.append((end - 0.08, JACKET_R[k]))
        materials.append("AA_Trim")     # son lisere
        stops.append((end, JACKET_R[k + 1] if k < 2 else TUBE_R))
        materials.append("AA_Greeble")  # l'epaulement sombre
    stops.append((length - 0.46, TUBE_R))
    materials.append("AA_Hull")         # le tube nu
    stops.append((length - 0.40, TUBE_R * 1.16))
    materials.append("AA_Greeble")      # l'epaulement du frein
    stops.append((length - 0.14, TUBE_R * 1.16))
    materials.append("AA_Hull")         # le frein de bouche
    stops.append((length - 0.10, TUBE_R * 1.22))
    materials.append("AA_Trim")         # la levre claire
    stops.append((length, TUBE_R * 1.22))
    materials.append("AA_Hull")
    stops.append((length, TUBE_R * 0.82))
    materials.append("AA_Trim")         # la couronne de levre, a z constant
    stops.append((length - 0.06, TUBE_R * 0.78))
    materials.append("AA_Greeble")      # la chemise
    stops.append((length - 0.55, TUBE_R * 0.74))
    materials.append("AA_Greeble")      # L'ALESAGE, en retrait
    verts = _loft_z(bm, stops, BARREL_SEG, materials)
    _cap_z(bm, verts[0], "AA_Greeble", entering=True)
    # Le fond d'alesage regarde VERS LA SORTIE du tube : c'est ce qu'on voit par
    # la bouche, et c'est ce qui la rend noire.
    _cap_z(bm, verts[-1], "AA_Greeble", entering=False)
    return _new_object(name, bm)


def build_barrel() -> bpy.types.Object:
    return _barrel("turret_barrel", BARREL_LEN)


def build_barrel_short() -> bpy.types.Object:
    """Le tube court — la troisieme famille de variete, par assemblage seul."""
    return _barrel("turret_barrel_short", BARREL_SHORT_LEN)


# ==========================================================================
# L'APPAREILLAGE — coffret et conduites, sur le plateau du socle
# ==========================================================================


def build_service_box() -> bpy.types.Object:
    """`turret_service_box`. Origine : sa base, au centre de son empreinte.

    Le moteur en pose 0, 1 ou 2, a l'angle qu'il veut sur le plateau du socle :
    c'est la deuxieme famille de variete. Sa profondeur radiale est calee sur la
    largeur du plateau : pose a `FITTING_R`, il ne deborde ni sur la cuvette ni
    hors du bourrelet.

    ⚠️ SA GORGE EST DANS LE PROFIL, PLUS UN RUBAN POSE DESSUS. Elle etait un
    second loft, entierement a l'interieur du coffret, donc invisible. Un creux
    qui ne creuse pas coute autant qu'un creux et ne rend rien. S'y ajoutent
    depuis BRIEF-0100 le retrait sombre et le lisere clair de la recette 2.
    """
    bm = bmesh.new()
    hx, hz, ch = BOX_W * 0.5, BOX_D * 0.5, 0.11
    body = _octagon(hx, hz, ch)
    foot = _octagon(hx - 0.07, hz - 0.07, 0.04)
    groove = _octagon(hx - 0.06, hz - 0.06, 0.05)
    rings: list[tuple[list[tuple[float, float]], object]] = [
        (foot, 0.0), (body, 0.06), (body, 0.16), (groove, 0.19),
        (groove, 0.27), (body, 0.30), (body, BOX_H - 0.08),
        (body, BOX_H - 0.04), (foot, BOX_H)]
    verts = _loft_y(bm, rings,
                    ["AA_Greeble",  # le retrait du pied
                     "AA_Panel",    # la plaque
                     "AA_Greeble",  # la gorge
                     "AA_Greeble",
                     "AA_Greeble",
                     "AA_Panel",    # la plaque haute
                     "AA_Trim",     # LE LISERE
                     "AA_Hull"])    # le chanfrein de couvercle
    _cap_high(bm, verts[-1], "AA_Hull")
    _cap_low(bm, verts[0], "AA_Greeble")
    return _new_object("turret_service_box", bm)


def build_pipe() -> bpy.types.Object:
    """`turret_pipe` — un FAISCEAU de trois conduites. Origine : sa base.

    Trois tubes de 18 cm de diametre et deux colliers. ⚠️ 18 cm et non 6 : le
    seuil de FORME mesure est a ~6,5 cm de monde ; sous lui, un relief est la
    sans qu'on voie ce que c'est. Trois tubes de 18 cm lisent comme un faisceau ;
    dix tubes de 4 cm lisent comme du bruit, pour quatre fois le budget.

    Il court TANGENTIELLEMENT au socle (le long de X, dans son repere), ce qui
    lui donne une orientation propre : pose a deux angles differents, le meme
    faisceau ne donne pas la meme silhouette.

    ⚠️ LES DEUX COLLIERS SONT A DEUX ENDROITS. Ils etaient tous les deux a x = 0,
    la boucle qui devait les ecarter n'utilisant pas sa variable : le soudage des
    doublons les fusionnait en un seul, au milieu. Un faisceau tenu par un collier
    unique ne se lit pas comme un faisceau.
    """
    bm = bmesh.new()
    for k, offset in enumerate((-0.19, 0.0, 0.19)):
        lift = 0.10 + 0.05 * (1 - abs(k - 1))
        stops = [(-PIPE_LEN * 0.5, PIPE_R * 0.62),
                 (-PIPE_LEN * 0.5 + 0.10, PIPE_R),
                 (PIPE_LEN * 0.5 - 0.10, PIPE_R),
                 (PIPE_LEN * 0.5, PIPE_R * 0.62)]
        # Un tube couche : construit le long de Z, puis bascule sur X. Les
        # anneaux sont ecrits directement dans le repere final — une rotation
        # appliquee apres coup rendrait le sens des faces indemontrable.
        ring_verts = []
        for z, radius in stops:
            ring = []
            for i in range(8):
                a = 2.0 * math.pi * i / 8
                ring.append(bm.verts.new(Vector((
                    z, lift + radius * math.sin(a),
                    offset + radius * math.cos(a)))))
            ring_verts.append(ring)
        for b in range(3):
            low, high = ring_verts[b], ring_verts[b + 1]
            for i in range(8):
                j = (i + 1) % 8
                climb = (high[i].co + high[j].co - low[i].co - low[j].co) * 0.5
                along = low[j].co - low[i].co
                _quad_facing(bm, low[i], low[j], high[j], high[i],
                             "AA_Trim", climb.cross(along))
        _face_facing(bm, list(ring_verts[0]), "AA_Greeble",
                     Vector((-1.0, 0.0, 0.0)))
        _face_facing(bm, list(ring_verts[-1]), "AA_Greeble",
                     Vector((1.0, 0.0, 0.0)))
    # Les deux colliers : ce sont eux qui font du faisceau UNE piece et non trois
    # tuyaux poses cote a cote.
    for cx in (-0.34, 0.34):
        collar = _shift_xz(_octagon(0.08, 0.30, 0.05), cx, 0.0)
        narrow = _shift_xz(_octagon(0.06, 0.27, 0.05), cx, 0.0)
        verts = _loft_y(bm, [(collar, 0.0), (collar, 0.05), (narrow, 0.30)],
                        ["AA_Greeble", "AA_Panel"])
        _cap_high(bm, verts[-1], "AA_Greeble")
        _cap_low(bm, verts[0], "AA_Greeble")
    return _new_object("turret_pipe", bm)


# ==========================================================================
# Harnais de scene (avant export)
# ==========================================================================


def _shell_report(mesh: bpy.types.Mesh) -> dict:
    """Topologie et volume signe de chaque coque connexe d'un maillage.

    Trois mesures, et aucune n'est une opinion :

      * les aretes de BORD (une seule face) — une nappe ouverte n'est pas un
        solide, et on ne peut rien prouver dessus ;
      * les aretes INCOHERENTES (deux faces qui la parcourent dans le meme sens)
        — c'est la signature exacte d'une plaque retournee, ou qu'elle soit ;
      * le VOLUME SIGNE de chaque coque (theoreme de la divergence) — une coque
        entierement retournee est parfaitement coherente avec elle-meme, seul son
        volume la trahit, en devenant negatif.
    """
    use: dict[tuple[int, int], list[int]] = {}
    for poly in mesh.polygons:
        loop = list(poly.vertices)
        for k, a in enumerate(loop):
            b = loop[(k + 1) % len(loop)]
            use.setdefault((min(a, b), max(a, b)), []).append(1 if a < b else -1)
    boundary = [e for e, d in use.items() if len(d) == 1]
    excess = [e for e, d in use.items() if len(d) > 2]
    flipped = [e for e, d in use.items() if len(d) == 2 and d[0] == d[1]]

    parent = list(range(len(mesh.vertices)))

    def root(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for poly in mesh.polygons:
        loop = list(poly.vertices)
        for v in loop[1:]:
            ra, rb = root(loop[0]), root(v)
            if ra != rb:
                parent[rb] = ra
    volumes: dict[int, float] = {}
    for poly in mesh.polygons:
        loop = [mesh.vertices[i].co for i in poly.vertices]
        key = root(poly.vertices[0])
        acc = 0.0
        for k in range(1, len(loop) - 1):
            acc += loop[0].dot(loop[k].cross(loop[k + 1])) / 6.0
        volumes[key] = volumes.get(key, 0.0) + acc
    return {"boundary": boundary, "excess": excess, "flipped": flipped,
            "volumes": volumes}


def _assert_solid(obj: bpy.types.Object) -> None:
    """LA PIECE EST-ELLE UN SOLIDE, ET REGARDE-T-ELLE DEHORS ?

    ⚠️ CE HARNAIS A REMPLACE `_assert_outward()` LE 2026-08-29, ET IL NE L'A PAS
    ASSOUPLI — IL L'A RETOURNE. L'ancien demandait a chaque face de regarder « du
    cote oppose a l'axe ». C'est une bonne question pour un cylindre plein et une
    mauvaise pour toute piece qui CREUSE, ce que ce kit fait partout. Mesure sur
    les huit pieces, avant correction :

        turret_barrel   16 faces REFUSEES et pourtant justes — la bouche est
                        percee, son cone regarde forcement vers l'axe du tube ;
        turret_pad      41 faces ACCEPTEES et pourtant retournees — tout le
                        plateau, toute la paroi de la cuvette et son fond ;
        turret_anchor_skirt  une couronne superieure retournee, idem.

    Le harnais bloquait donc le build sur les faces correctes et laissait passer
    les fausses. Un controle qui se trompe dans les deux sens est pire que pas de
    controle : il fait perdre du temps ET il rassure.

    La question juste ne parle pas de l'axe. Une piece est bonne si :

      1. elle est FERMEE — aucune arete de bord, aucune arete a plus de deux
         faces. Sans cela, « dedans » et « dehors » n'ont pas de sens ;
      2. son bobinage est COHERENT — toute arete interieure est parcourue une
         fois dans chaque sens. Une seule plaque retournee casse cette propriete,
         qu'elle soit sur une bosse, dans un creux ou sur un plafond ;
      3. le volume signe de CHAQUE coque connexe est POSITIF. Les points 1 et 2
         ne distinguent pas un solide d'un solide integralement retourne ; le
         volume, si.

    Les trois ensemble prouvent ce que le brief a besoin de savoir : aucune face
    ne disparaitra par culling arriere. Et le defaut reste totalement silencieux
    sans eux — ni bbox, ni compte de triangles, ni mesure d'UV ne le voit.
    """
    report = _shell_report(obj.data)
    if report["boundary"]:
        raise ak.ContractError(
            f"{obj.name} : {len(report['boundary'])} arete(s) de BORD — la piece "
            "n'est pas une coque fermee, on ne peut pas prouver de quel cote elle "
            "regarde (ex. sommets "
            f"{report['boundary'][0]})")
    if report["excess"]:
        raise ak.ContractError(
            f"{obj.name} : {len(report['excess'])} arete(s) a plus de deux faces "
            "— maillage non manifold")
    if report["flipped"]:
        raise ak.ContractError(
            f"{obj.name} : {len(report['flipped'])} arete(s) parcourue(s) deux "
            "fois dans le meme sens — une plaque est RETOURNEE et disparaitrait "
            "en jeu sans un mot (culling arriere)")
    for key, volume in sorted(report["volumes"].items()):
        if volume <= 1e-6:
            raise ak.ContractError(
                f"{obj.name} : une coque connexe a un volume signe de "
                f"{volume:+.6f} m3 — elle est retournee EN ENTIER, ce qu'un "
                "bobinage coherent ne suffit pas a voir")


#: ⚠️ COMBIEN DE COQUES FERMEES PAR PIECE, ET C'EST UN CONTRAT. Un volume qui
#: apparait ou qui disparait est une faute de frappe qui ne se voit sur aucune
#: planche : deux colliers de conduite fusionnes en un seul ont vecu ainsi
#: jusqu'au 2026-08-29. Le compte est donc ECRIT, et relu apres soudage.

#: ⚠️ COMBIEN DE COQUES FERMEES PAR PIECE, ET C'EST UN CONTRAT. Un volume qui
#: apparait ou qui disparait est une faute de frappe qui ne se voit sur aucune
#: planche : deux colliers de conduite fusionnes en un seul ont vecu ainsi
#: jusqu'au 2026-08-29. Le compte est donc ECRIT, et relu apres soudage.
SHELL_COUNT: dict[str, int] = {
    "turret_pad": 1,
    "turret_anchor_skirt": 1,
    "turret_ring": 1,
    # pave+masque, 2 plaques de flanc, 2 dalles de toit, viseur, bloc de recul,
    # la fente du masque et les deux fentes de joue
    "turret_body": 10,
    "turret_barrel": 1,
    "turret_barrel_short": 1,
    "turret_service_box": 1,
    "turret_pipe": 5,          # trois conduites, deux colliers
}


def _assert_shell_count(obj: bpy.types.Object) -> None:
    found = len(_shell_report(obj.data)["volumes"])
    want = SHELL_COUNT[obj.name]
    if found != want:
        raise ak.ContractError(
            f"{obj.name} : {found} coque(s) fermee(s) au lieu de {want} — un "
            "volume a fusionne avec un autre ou n'a pas ete emis")


def build_parts() -> list[bpy.types.Object]:
    parts = [
        build_pad(), build_anchor_skirt(), build_ring(), build_body(),
        build_barrel(), build_barrel_short(), build_service_box(), build_pipe(),
    ]
    names = [obj.name for obj in parts]
    if names != list(PART_NAMES):
        raise ak.ContractError(
            f"contrat de noms rompu : {names} au lieu de {list(PART_NAMES)}")
    for obj in parts:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
        bm.to_mesh(obj.data)
        bm.free()
        # ⚠️ APRES le soudage et AVANT la triangulation : c'est le maillage
        # soude qui part a l'export, et c'est la fusion de deux sommets qui
        # ferait apparaitre une arete a trois faces. Le controle doit voir la
        # meme topologie que Godot.
        _assert_solid(obj)
        _assert_shell_count(obj)
        ak.triangulate(obj)
        ak.shade_smooth_by_angle(obj, angle_deg=26.0)
        # ⚠️ PROJECTION EN BOITE, ET LE BRIEF LE DEMANDE EXPLICITEMENT : la piece
        # est vue de loin, sous une camera qui plonge, et elle partage ses slots
        # avec le borde. Un depliage continu lui donnerait une densite propre,
        # donc un grain different de celui de la coque a laquelle elle est
        # boulonnee. Densite relue dans `build_long_cortege`, jamais recopiee.
        ak.box_project_uv(obj, TEXELS_PER_METER)
    return parts


# ==========================================================================
# Export — meme chaine d'axes que la coque (ADR-0008)
# ==========================================================================

_YUP = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))
_AUTHOR_FIX = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))


def _author(v: Vector) -> Vector:
    return Vector((v.x, -v.z, v.y))


def _assert_axis_chain() -> None:
    """La chaine complete rend l'identite, sur des temoins ASYMETRIQUES.

    Le kit est fait de pieces dont l'avant et l'arriere ne se ressemblent pas (le
    canon ne sort que d'un cote, le bloc a un masque a l'avant et des joues a
    l'arriere). Une chaine d'axes fausse d'un demi-tour poserait dix-sept
    tourelles retournees, et aucune bounding box ne le dirait.
    """
    for probe in (Vector((1.0, 2.0, 3.0)), Vector((-0.86, 0.72, 2.9)),
                  Vector((1.7, -0.85, -0.94))):
        author = _author(probe)
        if (author - _AUTHOR_FIX.to_3x3() @ probe).length > 1e-9:
            raise ak.ContractError("_author() et _AUTHOR_FIX divergent")
        if (_YUP.to_3x3() @ author - probe).length > 1e-9:
            raise ak.ContractError("chaine d'axes rompue")


def _read_glb(path: str) -> tuple[dict, bytes]:
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


def export(parts: list[bpy.types.Object], filepath: str) -> dict:
    _assert_axis_chain()
    for obj in parts:
        obj.data.transform(_AUTHOR_FIX)
        obj.data.update()
        obj.location = (0.0, 0.0, 0.0)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in parts:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    staging = tempfile.mkdtemp(prefix="aegis-turretkit-")
    staged = os.path.join(staging, os.path.basename(filepath))
    try:
        bpy.ops.export_scene.gltf(
            filepath=staged, export_format="GLB", export_yup=True,
            export_apply=True, use_selection=True, export_materials="EXPORT",
            export_cameras=False, export_lights=False, export_animations=False,
            export_skins=False, export_extras=False, export_tangents=True,
            export_normals=True, export_texcoords=True,
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
    acc = gltf["accessors"][index]
    view = gltf["bufferViews"][acc["bufferView"]]
    counts = {"VEC2": 2, "VEC3": 3, "VEC4": 4, "SCALAR": 1}[acc["type"]]
    fmt = {5126: "f", 5125: "I", 5123: "H", 5121: "B"}[acc["componentType"]]
    size = struct.calcsize("<" + fmt) * counts
    stride = view.get("byteStride", size)
    base = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
    return [struct.unpack_from("<" + fmt * counts, blob, base + i * stride)
            for i in range(acc["count"])]


def _indices(gltf: dict, blob: bytes, prim: dict) -> list[int]:
    return [v[0] for v in _accessor(gltf, blob, prim["indices"])]


def _texel_density(points: list[tuple], uvs: list[tuple],
                   tris: list[tuple[int, int, int]]) -> dict:
    """Densite par VALEURS SINGULIERES de l'application plan -> UV.

    Une moyenne d'aires ne verrait aucun etirement : un triangle deux fois trop
    long dans un sens et deux fois trop court dans l'autre a la bonne aire.
    """
    lo, hi, total, weight = math.inf, 0.0, 0.0, 0.0
    aniso = 0.0
    for ia, ib, ic in tris:
        pa, pb, pc = (Vector(points[i]) for i in (ia, ib, ic))
        ua, ub, uc = (Vector(uvs[i]) for i in (ia, ib, ic))
        e1, e2 = pb - pa, pc - pa
        normal = e1.cross(e2)
        area = normal.length * 0.5
        if area < 1e-9:
            continue
        basis_x = e1.normalized()
        basis_y = normal.normalized().cross(basis_x)
        m11, m21 = e1.dot(basis_x), e1.dot(basis_y)
        m12, m22 = e2.dot(basis_x), e2.dot(basis_y)
        det = m11 * m22 - m12 * m21
        if abs(det) < 1e-12:
            continue
        du1, dv1 = ub - ua, uc - ua
        j = [[(du1.x * m22 - dv1.x * m21) / det, (dv1.x * m11 - du1.x * m12) / det],
             [(du1.y * m22 - dv1.y * m21) / det, (dv1.y * m11 - du1.y * m12) / det]]
        a = j[0][0] ** 2 + j[1][0] ** 2
        b = j[0][0] * j[0][1] + j[1][0] * j[1][1]
        c = j[0][1] ** 2 + j[1][1] ** 2
        trace, diff = a + c, math.sqrt(max((a - c) ** 2 + 4 * b * b, 0.0))
        s_max = math.sqrt(max((trace + diff) * 0.5, 0.0))
        s_min = math.sqrt(max((trace - diff) * 0.5, 0.0))
        if s_min <= 1e-9:
            continue
        lo = min(lo, s_min)
        hi = max(hi, s_max)
        aniso = max(aniso, s_max / s_min)
        total += math.sqrt(s_min * s_max) * area
        weight += area
    if weight <= 0.0:
        return {}
    mean = total / weight
    return {"tiles_per_m_min": lo, "tiles_per_m_max": hi,
            "tiles_per_m_mean": mean, "m_per_tile_mean": 1.0 / mean,
            "anisotropy_max": aniso}


def turret_seat_y(s: float, x: float) -> tuple[float, float]:
    """(Y d'ASSISE du socle, Y du point le plus bas de son emprise).

    ⚠️ CE N'EST PAS UNE COPIE : la fonction VIT DANS `build_long_cortege`, qui
    est le seul endroit ou la peau existe, et c'est elle qui pose le Y du
    marqueur `Turret_NN`. Une assise recalculee ici divergerait en silence de
    celle qui a servi a placer le marqueur, et le socle flotterait — la faute
    exacte que `bay_mouth_y()` a evitee au hangar.
    """
    return cortege.turret_seat_y(s, x)


#: ⚠️ LE PLAFOND DES PIECES DE GAMEPLAY, ET CE N'EST PLUS UN CLIQUET (BRIEF-0094).
#:
#: Ce qui suivait ici etait une valeur d'attente : `CEILING_OVERSHOOT_MAX = 0,43`
#: figeait le depassement MESURE (0,422 m au pire) du plafond du decor -3,00, en
#: disant que l'arbitrage appartenait au concepteur. Il a ete rendu.
#:
#: La regle a ete relue, pas assouplie. Ce que le plafond protege tient en une
#: phrase : « un volume qui masquerait le combat SANS JAMAIS POUVOIR ETRE
#: TOUCHE ». Une tourelle se tire dessus — la seconde moitie ne la concerne pas,
#: et la premiere non plus : a -2,40 elle reste 2,40 unites SOUS le plan de vol,
#: elle ne peut ni masquer le chasseur ni le heurter. Le decor INERTE, lui, reste
#: sous -3,00 (`cortege.CEILING_Y`, harnais de la coque, inchange).
#:
#: La borne est donc la vraie : celle du moteur. Elle est lue dans
#: `scripts/vfx/cortege_flyby.gd` (`GAMEPLAY_CEILING_Y`) et un test moteur la
#: tient de son cote (`test_no_turret_ever_reaches_the_flight_plane`, qui charge
#: le kit, assemble la piece la plus haute et la pose sur le pire marqueur).
#:
#: ⚠️ Elle est RECOPIEE, et c'est le seul endroit du kit ou une valeur du moteur
#: l'est. Blender ne lit pas le GDScript ; le harnais ci-dessous verifie donc que
#: le fichier moteur porte toujours ce nombre, et echoue si les deux ont derive.
GAMEPLAY_CEILING_Y = -2.40
#: Le fichier qui fait foi. Relu a chaque build : deux ecritures d'une meme cote
#: finissent toujours par diverger si rien ne les confronte.
FLYBY_SOURCE = os.path.join(
    _REPO, "scripts/vfx/cortege_flyby.gd")


def _assert_gameplay_ceiling() -> None:
    """Le plafond recopie ici est-il celui que le moteur applique ?"""
    try:
        with open(FLYBY_SOURCE, encoding="utf-8") as handle:
            source = handle.read()
    except OSError:
        return          # hors du depot : on ne peut rien affirmer, on se tait
    marker = "const GAMEPLAY_CEILING_Y := "
    if marker not in source:
        raise ak.ContractError(
            f"{FLYBY_SOURCE} ne declare plus GAMEPLAY_CEILING_Y : le kit ne peut "
            "plus verifier contre quoi il mesure")
    value = source.split(marker, 1)[1].split("\n", 1)[0].strip()
    if abs(float(value) - GAMEPLAY_CEILING_Y) > 1e-9:
        raise ak.ContractError(
            f"plafond de gameplay : {GAMEPLAY_CEILING_Y} ici, {value} dans "
            f"{os.path.basename(FLYBY_SOURCE)} — les deux ont derive")


def _assert_on_axis(name: str, points: list[tuple],
                    problems: list[str], revolution: bool) -> None:
    """LA PIECE TOURNE-T-ELLE SUR PLACE ?

    ⚠️ LE HARNAIS LE PLUS IMPORTANT DE CE FICHIER, ET CELUI QU'AUCUNE PLANCHE NE
    REMPLACE. Le moteur fait tourner `turret_ring` et tout ce qui est monte dessus
    a 42 deg/s autour de Y. Si le maillage n'est pas centre sur cet axe, la
    tourelle BALAIE EN DECRIVANT UN CERCLE au lieu de pivoter — un defaut qui ne
    se voit ni sur un rendu fixe, ni sur une bbox, ni sur un compte de triangles,
    et qui ne se decouvre qu'en jouant.

    Deux mesures, parce qu'une seule se laisse tromper : le CENTROIDE des sommets
    (qu'un maillage asymetrique deplacerait) ET la boite englobante (qu'une
    symetrie de facade laisserait centree). Les deux doivent tenir au micron.
    """
    if not points:
        problems.append(f"{name} : aucun sommet, l'axe ne peut pas etre verifie")
        return
    # ⚠️ SUR LES POSITIONS UNIQUES, ET C'EST INDISPENSABLE. Le tableau de sommets
    # d'un `.glb` est DEDOUBLE — l'exportateur y recopie un sommet autant de fois
    # qu'il porte de normales, d'UV ou de materiaux differents. Un centroide
    # calcule dessus pese donc les coutures et non la matiere : mesure ici,
    # -1,04e-4 sur un maillage rigoureusement symetrique. La boite englobante,
    # elle, ne s'y trompe jamais — d'ou les deux mesures.
    points = sorted({(round(p[0], 6), round(p[1], 6), round(p[2], 6))
                     for p in points})
    measures = [("centroide x", sum(p[0] for p in points) / len(points)),
                ("bbox x", (min(p[0] for p in points)
                            + max(p[0] for p in points)) * 0.5)]
    if revolution:
        # ⚠️ SEULE LA COURONNE EST UN SOLIDE DE REVOLUTION. Le bloc, lui, DOIT
        # etre dissymetrique en Z : il a un masque a l'avant et un bloc de recul
        # a l'arriere, c'est ce qui fait qu'on lit ou il regarde. Lui demander
        # d'etre centre en Z reviendrait a lui interdire d'avoir un avant.
        measures += [("centroide z", sum(p[2] for p in points) / len(points)),
                     ("bbox z", (min(p[2] for p in points)
                                 + max(p[2] for p in points)) * 0.5)]
    for label, value in measures:
        if abs(value) > 1e-4:
            problems.append(
                f"{name} : {label} = {value:+.6f} au lieu de 0 — l'origine n'est "
                "pas sur l'axe de rotation, la tourelle balaierait en decrivant "
                "un cercle au lieu de pivoter sur place")




def turret_skin_rise(s: float, x: float, radius: float) -> float:
    """De combien la PEAU REMONTE au-dessus de l'assise, sur le disque balaye.

    ⚠️ MESURE NEUVE (BRIEF-0100), ET C'EST ELLE QUI BORNE L'ALLONGE DES TUBES.
    Le denivele de `turret_seat_y()` dit ce que la jupe doit ABSORBER sous le
    socle ; il ne dit rien de ce qui se passe plus loin. Or les tubes balayent
    a 360 deg bien au-dela de l'emprise, et la peau REMONTE vers la crete
    dorsale : 0,608 m a 3 m de l'axe, 0,665 m a 6 m, 0,679 m a 7 m, puis 0,898 m
    a 8 m (Turret_02, 03 et 10). Un tube dont le dessous passe sous cette cote
    laboure la coque une fois par tour — et ça ne se voit qu'en jeu, en
    mouvement, comme le balayage en cercle de la couronne.
    """
    seat, _ = turret_seat_y(s, x)
    highest = -math.inf
    steps = 72
    for k in range(steps):
        a = 2.0 * math.pi * k / steps
        for factor in (0.45, 0.7, 0.85, 1.0):
            r = radius * factor
            highest = max(highest,
                          cortege._surface_y(s + r * math.sin(a),
                                             x + r * math.cos(a)))
    return highest - seat


def turret_hollow(s: float, x: float, radius: float) -> float:
    """Le CREUX sous un socle de rayon `radius`, l'assise restant celle de 2,08 m.

    ⚠️ CE N'EST PAS `turret_seat_y()[0] - [1]`, ET LA DIFFERENCE A COUTE. Le
    denivele de `turret_seat_y()` est mesure sur le disque d'echantillonnage de
    la COQUE (2,08 m). Le socle d'une tourelle LEGERE ne fait que 0,73 m de rayon
    — mais son assise reste celle du marqueur, calculee sur 2,08. Le creux sous
    elle vaut donc encore 0,643 m au pire, pour une jupe mise a l'echelle 0,35.
    """
    seat, _ = turret_seat_y(s, x)
    lowest = seat
    for k in range(32):
        a = 2.0 * math.pi * k / 32
        for factor in (0.5, 0.82, 1.0):
            r = radius * factor
            lowest = min(lowest,
                         cortege._surface_y(s + r * math.sin(a),
                                            x + r * math.cos(a)))
    return seat - lowest


def _audit(path: str) -> dict:
    """Relit le `.glb` PRODUIT et verifie tout ce que le brief exige.

    On lit le binaire et non la scene en memoire : c'est la seule chose que Godot
    chargera. Les trois coques du depot sorties sans UV (ADR-0028) avaient toutes
    une scene Blender parfaite.
    """
    gltf, blob = _read_glb(path)
    problems: list[str] = []
    materials = [m.get("name", f"#{i}")
                 for i, m in enumerate(gltf.get("materials", []))]
    nodes = gltf.get("nodes", [])
    roots = gltf.get("scenes", [{}])[0].get("nodes", list(range(len(nodes))))
    root_names = [nodes[i].get("name", "?") for i in roots]

    for name in PART_NAMES:
        if name not in root_names:
            problems.append(f"piece '{name}' absente du kit — le moteur monte "
                            "par le NOM, il ne la trouverait pas")
    for name in root_names:
        if name not in PART_NAMES:
            problems.append(f"nœud inattendu : '{name}'")

    stats: dict[str, dict] = {}
    prims_total = prims_uv = prims_tan = 0
    triangles_total = 0
    used_materials: set[str] = set()
    area_by_material: dict[str, float] = {}
    seen_area: dict[str, float] = {}
    built_area: dict[str, float] = {}
    total_area = 0.0
    total_seen = 0.0
    density: dict[str, dict] = {}
    part_points: dict[str, list[tuple]] = {}

    for index in roots:
        node = nodes[index]
        name = node.get("name", "?")
        if node.get("children"):
            problems.append(f"{name} : une piece de kit n'a pas d'enfant")
        if "mesh" not in node:
            problems.append(f"{name} : nœud sans maillage")
            continue
        if node.get("translation") or node.get("rotation") or node.get("scale"):
            problems.append(
                f"{name} : le nœud doit rester a l'identite — l'origine EST le "
                "point d'assemblage, le moteur pose la transformation")
        triangles = 0
        lo = [math.inf] * 3
        hi = [-math.inf] * 3
        pts: list[tuple] = []
        uvs: list[tuple] = []
        tris: list[tuple[int, int, int]] = []
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
            material = materials[prim["material"]] if "material" in prim \
                else "<aucun>"
            used_materials.add(material)
            base = len(pts)
            pts += points
            if has_uv:
                uvs += _accessor(gltf, blob, attrs["TEXCOORD_0"])
            for axis in range(3):
                lo[axis] = min(lo[axis], acc["min"][axis])
                hi[axis] = max(hi[axis], acc["max"][axis])
            for k in range(0, len(tri_indices) - 2, 3):
                ia, ib, ic = (tri_indices[k], tri_indices[k + 1],
                              tri_indices[k + 2])
                tris.append((base + ia, base + ib, base + ic))
                pa = Vector(points[ia])
                area = (Vector(points[ib]) - pa).cross(
                    Vector(points[ic]) - pa).length * 0.5
                total_area += area
                area_by_material[material] = \
                    area_by_material.get(material, 0.0) + area
                # ⚠️ L'AIRE VUE ET L'AIRE ASSEMBLEE, comptees a part. La jupe
                # enterree du socle pese lourd et ne rend pas un pixel : melangee
                # au reste, elle gonflerait la part « structure ». Est « vue » ce
                # qui est au-dessus du plan d'assise ET ne regarde pas le pont.
                cy = (points[ia][1] + points[ib][1] + points[ic][1]) / 3.0
                oy = ASSEMBLY_OFFSET[name][1]
                copies = ASSEMBLY_COPIES[name]
                built_area[material] = built_area.get(material, 0.0) \
                    + area * copies
                normal = (Vector(points[ib]) - pa).cross(
                    Vector(points[ic]) - pa)
                downward = normal.length > 1e-12 and \
                    normal.normalized().y < -0.5
                if cy + oy > -0.02 and copies and not downward:
                    seen_area[material] = \
                        seen_area.get(material, 0.0) + area * copies
                    total_seen += area * copies
        part_points[name] = pts
        if uvs:
            density[name] = _texel_density(pts, uvs, tris)
        # ⚠️ Le `.glb` est DANS LE REPERE DU KIT : la chaine `_AUTHOR_FIX` puis
        # `export_yup` rend l'identite, et `_assert_axis_chain()` le reverifie sur
        # trois temoins asymetriques.
        if name in ("turret_ring", "turret_body"):
            _assert_on_axis(name, pts, problems,
                            revolution=name == "turret_ring")
        triangles_total += triangles
        stats[name] = {"triangles": triangles,
                       "min": tuple(lo), "max": tuple(hi),
                       "size": tuple(hi[a] - lo[a] for a in range(3))}

    # --- LES COTES MAITRESSES, RELEVEES SUR LE BINAIRE --------------------
    for name, axis, want, label in (
            ("turret_pad", 0, 2.0 * PAD_R, "diametre du socle"),
            ("turret_pad", 2, 2.0 * PAD_R, "diametre du socle (Z)"),
            ("turret_anchor_skirt", 0, 2.0 * SKIRT_R, "diametre de la jupe"),
            ("turret_ring", 0, RING_D, "diametre de la couronne"),
            ("turret_ring", 1, RING_H, "hauteur de la couronne"),
            ("turret_barrel", 2, BARREL_LEN, "longueur de canon"),
            ("turret_barrel_short", 2, BARREL_SHORT_LEN, "longueur du tube court")):
        piece = stats.get(name)
        if piece is None:
            continue
        if abs(piece["size"][axis] - want) > 1e-3:
            problems.append(
                f"{name} : {label} = {piece['size'][axis]:.4f} m au lieu de "
                f"{want:.2f} m")
    body = stats.get("turret_body")
    if body is not None:
        crest = BODY_BASE + body["max"][1]
        if abs(crest - TURRET_H) > 1e-3:
            problems.append(
                f"hauteur totale {crest:.4f} m au lieu de {TURRET_H:.2f} m")
        if body["size"][1] > body["size"][0] or body["size"][1] > body["size"][2]:
            problems.append(
                "turret_body : il est plus haut que large ou que long — la "
                "planche demande un bloc TRAPU, surtout pas une tour")
    # ⚠️ La borne porte sur le MANCHON de recul, pas sur le tube : c'est le
    # manchon qui loge dans le creux du masque. Mesuree sur la largeur du BLOC,
    # elle laissait passer un ecartement ou le manchon traversait la paroi.
    reach = BARREL_GAUGE_MAX * 0.5 + BARREL_SLEEVE
    if reach > MANTLET_HX - 0.02:
        problems.append(
            f"a l'ecartement maximal ({BARREL_GAUGE_MAX:.2f} m) le manchon atteint "
            f"{reach:.3f} m alors que le masque n'ouvre qu'a {MANTLET_HX:.2f} m : "
            "la variete percerait la paroi du creux")
    for label, gauge in ((row[0], row[3]) for row in FAMILIES):
        if gauge > BARREL_GAUGE_MAX + 1e-9:
            problems.append(
                f"la famille « {label} » demande un ecartement de {gauge:.2f} m, "
                f"au-dela du maximum {BARREL_GAUGE_MAX:.2f} m")
    # L'emprise du kit et celle avec laquelle la coque a pose ses marqueurs.
    if abs(FOOTPRINT_R - cortege.TURRET_FOOTPRINT_R) > 1e-9:
        problems.append(
            f"emprise du kit {FOOTPRINT_R:.3f} m contre "
            f"{cortege.TURRET_FOOTPRINT_R:.3f} m echantillonnee par la coque : "
            "l'assise du marqueur est fausse")
    if PAD_R >= SKIRT_R - 0.05:
        problems.append(
            f"le tambour du socle ({PAD_R:.2f} m) n'est plus en retrait de la "
            f"jupe ({SKIRT_R:.2f} m) : la jupe ne se lirait plus comme un collier")
    if FOOTPRINT_R > min(cortege.PAD_RADIUS) - 0.05:
        problems.append(
            f"emprise du kit {FOOTPRINT_R:.2f} m > reservation minimale "
            f"{min(cortege.PAD_RADIUS):.2f} m de la coque — le garde mutuel "
            "tourelle/pont de BRIEF-0092 arbitrerait sur une emprise fausse")
    # Les fentes : la regle 4 de la planche, et la regle DURE des 25 pct.
    slit_gap = BARREL_GAUGE * 0.5 - BARREL_SLEEVE - EYE_W * 0.5
    if slit_gap < 0.01:
        problems.append(
            f"la fente du masque ({EYE_W:.2f} m) touche le manchon du canon : il "
            f"ne reste que {slit_gap:+.3f} m entre les deux au fond du masque")
    slit_ratio = EYE_W / TURRET_H
    if slit_ratio > 0.25:
        problems.append(
            f"la fente fait {100 * slit_ratio:.1f} pct de la tourelle — 25 pct "
            "est une regle dure")
    if EYE_T > 0.05 or CHEEK_SLIT_T > 0.05:
        problems.append(
            "une fente magenta depasse 5 cm d'epaisseur : la regle 4 de la "
            "planche demande des TRAITS, pas des surfaces")

    # --- LA ROTATION PASSE-T-ELLE AU-DESSUS DE L'APPAREILLAGE ? -----------
    # Le bloc TOURNE au-dessus d'un appareillage POSE : les deux se recouvrent
    # forcement en plan, et rien d'autre que leur denivele ne les separe. Un
    # coffret trop haut de 5 cm ne se voit sur aucune planche — il se voit en
    # jeu, une fois par tour, quand le bloc le traverse. La mesure se fait par
    # TRANCHES DE 2 cm : c'est la seule façon de ne pas comparer un rayon a une
    # hauteur qu'il n'atteint jamais.
    clearance, clearance_at = math.inf, ""
    slabs: dict[int, list[float]] = {}
    static: dict[int, list[float]] = {}
    for name, points in part_points.items():
        if name == "turret_barrel_short":
            continue
        rotates = name in ("turret_ring", "turret_body", "turret_barrel")
        offsets = [ASSEMBLY_OFFSET[name]]
        if name == "turret_barrel":
            offsets = [(side * BARREL_GAUGE_MAX * 0.5, BARREL_Y, BARREL_Z)
                       for side in (-1.0, 1.0)]
        for ox, oy, oz in offsets:
            for px, py, pz in points:
                y = py + oy
                if rotates:
                    radius = math.hypot(px + ox, pz + oz)
                else:
                    # Pose a `FITTING_R` : le Z local est radial, le X tangentiel.
                    radius = math.hypot(FITTING_R + pz, px) \
                        if name in ("turret_service_box", "turret_pipe") \
                        else math.hypot(px, pz)
                bucket = int(math.floor(y / 0.02))
                target = slabs if rotates else static
                target.setdefault(bucket, []).append(radius)
    for bucket, radii in sorted(slabs.items()):
        near = static.get(bucket)
        if not near:
            continue
        gap = min(near) - max(radii)
        if gap < clearance:
            clearance = gap
            clearance_at = f"Y = {bucket * 0.02:+.2f} m"
    if clearance < 0.05:
        problems.append(
            f"degagement de rotation {clearance:+.3f} m a {clearance_at} : le "
            "bloc ou un canon passe sur une piece posee sur le socle. Le defaut "
            "ne se voit qu'en jeu, une fois par tour")

    # --- LES DIX-SEPT EMPLACEMENTS, MESURES SUR LA COQUE -------------------
    seats: list[tuple[str, float, float, float, float]] = []
    overshoot = 0.0
    for number, (s, x) in enumerate(cortege.TURRETS, start=1):
        seat, low = turret_seat_y(s, x)
        crest = seat + TURRET_H
        seats.append((f"Turret_{number:02d}", seat, low, seat - low, crest))
        overshoot = max(overshoot, crest - cortege.CEILING_Y)
    _assert_gameplay_ceiling()

    # --- LES TROIS CLASSES, MESUREES CONTRE LA PEAU ------------------------
    # ⚠️ TROIS BORNES PAR CLASSE, ET AUCUNE N'EST UNE HYPOTHESE :
    #   1. le SOMMET sous le plafond des pieces de gameplay, au pire marqueur ;
    #   2. la JUPE ENTERREE plus profonde que le creux sous SON socle a elle ;
    #   3. le DESSOUS DES TUBES au-dessus de la peau qui remonte, sur tout le
    #      disque balaye.
    reach_native = BARREL_Z + BARREL_LEN
    class_rows: list[dict] = []
    for label, scale, skirt, barrel, gauge, boxes, pipe in CLASSES:
        del gauge, boxes, pipe
        span = BARREL_SHORT_LEN if "short" in barrel else BARREL_LEN
        reach = (BARREL_Z + span) * scale
        height = TURRET_H * scale
        # ⚠️ L'EMPRISE DE LA CLASSE EST CELLE DE SA PIECE LA PLUS LARGE : la
        # jupe si elle est posee, le tambour du socle sinon. La legere n'a pas
        # de jupe — lui compter 2,08 m ferait flotter la mesure.
        base_r = SKIRT_R if skirt else PAD_R
        length = (base_r + BARREL_Z + span) * scale
        footprint = base_r * scale
        buried = PAD_BURIED * scale
        under = (BARREL_Y - JACKET_R[0]) * scale
        worst_summit = (-math.inf, "")
        worst_hollow = (0.0, "")
        worst_rise = (-math.inf, "")
        for number, (s, x) in enumerate(cortege.TURRETS, start=1):
            marker = f"Turret_{number:02d}"
            seat, _low = turret_seat_y(s, x)
            summit = seat + height
            if summit > worst_summit[0]:
                worst_summit = (summit, marker)
            hollow = turret_hollow(s, x, footprint)
            if hollow > worst_hollow[0]:
                worst_hollow = (hollow, marker)
            rise = turret_skin_rise(s, x, reach)
            if rise > worst_rise[0]:
                worst_rise = (rise, marker)
        class_rows.append({
            "name": label, "scale": scale, "height": height, "length": length,
            "footprint": footprint, "reach": reach, "buried": buried,
            "under": under, "summit": worst_summit, "hollow": worst_hollow,
            "rise": worst_rise,
        })
        if worst_summit[0] > GAMEPLAY_CEILING_Y:
            problems.append(
                f"classe « {label} » : elle culmine a {worst_summit[0]:.3f} sur "
                f"{worst_summit[1]}, au-dessus du plafond des PIECES DE GAMEPLAY "
                f"({GAMEPLAY_CEILING_Y:.2f}) — un test moteur le tient aussi "
                "(test_no_turret_ever_reaches_the_flight_plane)")
        if buried < worst_hollow[0] + 0.03:
            problems.append(
                f"classe « {label} » : jupe enterree de {buried:.3f} m pour un "
                f"creux de {worst_hollow[0]:.3f} m sous son socle "
                f"({worst_hollow[1]}) — elle FLOTTERAIT, et ça ne se voit que du "
                "cote bas")
        if under < worst_rise[0] + 0.03:
            problems.append(
                f"classe « {label} » : le dessous des tubes est a {under:.3f} m "
                f"de l'assise alors que la peau remonte a {worst_rise[0]:.3f} m "
                f"sur le disque balaye ({worst_rise[1]}, rayon {reach:.2f} m) — "
                "le canon labourerait la coque une fois par tour")

    summit = max(row[4] for row in seats)

    # --- LE BALAYAGE DES CANONS CROISE-T-IL UN HANGAR ? --------------------
    sweep = reach_native
    bay_sweep: list[tuple[str, str, float]] = []
    for number, (ts, tx) in enumerate(cortege.TURRETS, start=1):
        for index, (bs, bx) in enumerate(cortege.BAYS, start=1):
            dx = max(abs(tx - bx) - cortege.BAY_HALF_X - cortege.BAY_COAMING_W, 0.0)
            ds = max(abs(ts - bs) - cortege.BAY_HALF_S - cortege.BAY_COAMING_W, 0.0)
            distance = math.hypot(dx, ds)
            if distance < sweep:
                bay_sweep.append((f"Turret_{number:02d}", f"Bay_{index:02d}",
                                  sweep - distance))

    # --- UV, materiaux, textures -----------------------------------------
    if prims_total == 0 or prims_uv != prims_total:
        problems.append(
            f"{prims_total - prims_uv} primitive(s) sur {prims_total} sans "
            "TEXCOORD_0 — la surface ne pourrait recevoir aucune carte (ADR-0028)")
    if prims_tan != prims_total:
        problems.append(
            f"{prims_total - prims_tan} primitive(s) sur {prims_total} sans TANGENT")
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

    # --- densite de texels -----------------------------------------------
    floor_density = TEXELS_PER_METER / math.sqrt(3.0) * 0.98
    for name, measure in density.items():
        if not measure:
            continue
        if measure["tiles_per_m_min"] < floor_density:
            problems.append(
                f"{name} : densite minimale {measure['tiles_per_m_min']:.4f} "
                f"sous la borne {floor_density:.4f} de la projection en boite")
        if measure["tiles_per_m_max"] > TEXELS_PER_METER * 1.02:
            problems.append(
                f"{name} : densite maximale {measure['tiles_per_m_max']:.4f} "
                f"au-dessus de la cible {TEXELS_PER_METER:.4f}")

    # --- garde-fou d'emballement (ce n'est plus un budget) ----------------
    assembled = sum(stats.get(name, {}).get("triangles", 0) * ASSEMBLY_COPIES[name]
                    for name in PART_NAMES)
    if assembled > TRI_BUDGET_ASSEMBLED:
        problems.append(
            f"{assembled} triangles par tourelle assemblee > garde-fou "
            f"{TRI_BUDGET_ASSEMBLED} — ce n'est plus un budget, c'est un cran "
            "d'arret : quelque chose est parti en boucle")
    level = assembled * len(cortege.TURRETS)
    if level > TRI_BUDGET_LEVEL:
        problems.append(f"{level} triangles pour le niveau > garde-fou "
                        f"{TRI_BUDGET_LEVEL}")

    if problems:
        raise ak.ContractError(
            "CONTRAT ROMPU — turret_kit\n" + "\n".join(f"  - {p}" for p in problems))

    return {
        "parts": stats,
        "primitives": (prims_uv, prims_tan, prims_total),
        "triangles": triangles_total,
        "assembled": assembled,
        "level": level,
        "materials": sorted(used_materials),
        "area_by_material": area_by_material,
        "seen_by_material": seen_area,
        "built_by_material": built_area,
        "total_built": sum(built_area.values()),
        "total_area": total_area,
        "total_seen": total_seen,
        "density": density,
        "seats": seats,
        "classes": class_rows,
        "clearance": (clearance, clearance_at),
        "overshoot": overshoot,
        "summit": summit,
        "bay_sweep": bay_sweep,
        "bytes": os.path.getsize(path),
    }


# ==========================================================================
# Build
# ==========================================================================


def build() -> dict:
    ak.reset_scene()
    ak.set_faction(ak.FACTION_NULL_CHOIR)
    parts = build_parts()
    return export(parts, OUTPUT)


#: Les cotes de la PLANCHE CIBLE, pour que l'ecart soit calcule et non annonce.
#: (longueur, hauteur) en metres, colonnes 1, 2 et 3 de
#: `tourelles_lourdes_concept_sheet_2026-09-05.png`.
PLATE_COTES: dict[str, tuple[float, float]] = {
    "legere": (3.5, 1.6),
    "standard": (6.5, 2.8),
    "lourde": (10.0, 4.2),
}


def _print_report(report: dict) -> None:
    print("\n--- turret_kit : mesures relevees sur le .glb PRODUIT ---")
    print(f"  {'piece':<22} {'tri':>6} {'x':>2}  {'bbox (l x h x L)':>24}")
    for name in PART_NAMES:
        s = report["parts"][name]
        print(f"  {name:<22} {s['triangles']:>6} {ASSEMBLY_COPIES[name]:>2}  "
              f"{s['size'][0]:7.2f} x {s['size'][1]:5.2f} x {s['size'][2]:7.2f}")
    print(f"  {'TOTAL (kit unique)':<22} {report['triangles']:>6}")
    print(f"  tourelle LOURDE assemblee : {report['assembled']} tri ; dix-sept "
          f"tourelles : {report['level']} tri (garde-fou "
          f"{TRI_BUDGET_ASSEMBLED} / {TRI_BUDGET_LEVEL} — ce n'est plus un "
          "budget, voir l'en-tete)")
    print(f"  pieces POSEES par tourelle : "
          f"{sum(ASSEMBLY_COPIES[n] for n in PART_NAMES)} (lourde et standard), "
          "4 pour la legere — inchange depuis BRIEF-0093, aucune piece neuve")

    print("\n  LES TROIS CLASSES — memes blocs, trois echelles (planche : "
          "« MODULES PARTAGES »)")
    print(f"    {'classe':<10} {'x':>5} {'longueur':>19} {'hauteur':>19} "
          f"{'emprise R':>10} {'allonge':>8}")
    for row in report["classes"]:
        want_l, want_h = PLATE_COTES[row["name"]]
        dl = 100.0 * (row["length"] - want_l) / want_l
        dh = 100.0 * (row["height"] - want_h) / want_h
        print(f"    {row['name']:<10} {row['scale']:>5.2f} "
              f"{row['length']:>8.2f} m ({dl:+5.1f} pct) "
              f"{row['height']:>8.2f} m ({dh:+5.1f} pct) "
              f"{row['footprint']:>8.2f} m {row['reach']:>7.2f} m")
    print("    ecart calcule contre la planche "
          "`tourelles_lourdes_concept_sheet_2026-09-05.png` (3,5/1,6 · 6,5/2,8 "
          "· 10,0/4,2)")
    print(f"    ⚠️ LA HAUTEUR EST BORNEE PAR LE PLAFOND DE GAMEPLAY "
          f"({GAMEPLAY_CEILING_Y:+.2f}), PAS PAR LA PLANCHE. L'assise la plus "
          "haute est -4,270 (Turret_08) : il reste 1,870 m. Une lourde de 4,2 m "
          "culminerait a -0,07, sept centimetres sous le plan de vol.")

    print("\n  CE QUE CHAQUE CLASSE MESURE CONTRE LA PEAU, aux dix-sept "
          "emplacements")
    print(f"    {'classe':<10} {'sommet':>18} {'jupe/creux':>22} "
          f"{'dessous des tubes / montee de la peau':>40}")
    for row in report["classes"]:
        summit, where = row["summit"]
        hollow, hwhere = row["hollow"]
        rise, rwhere = row["rise"]
        print(f"    {row['name']:<10} {summit:>8.3f} ({where[-2:]}) "
              f"{row['buried']:>8.3f} / {hollow:.3f} ({hwhere[-2:]}) "
              f"{row['under']:>16.3f} / {rise:.3f} ({rwhere[-2:]})")
    print("    sommet : Y absolu au pire marqueur, a comparer au plafond "
          f"{GAMEPLAY_CEILING_Y:+.2f}")
    print("    jupe/creux : profondeur enterree contre le creux sous SON socle "
          "a elle (une jupe plus courte que le creux FLOTTE)")
    print("    tubes : dessous du tube contre la montee de la peau sur le "
          "disque balaye (sous elle, le canon laboure la coque)")

    print("\n  TABLE DES EMPRISES — c'est elle qui dit au moteur ou poser chaque")
    print("  piece. Repere local du marqueur `Turret_NN` (X lateral, Y haut, "
          "Z survol, +Z = proue).")
    entete = "position d'assemblage"
    print(f"    {'piece':<22} {'parent':<10} {entete:<28} {'copies'}")
    plan = (
        ("turret_pad", "marqueur", "(0, 0, 0)", "1"),
        ("turret_anchor_skirt", "marqueur", "(0, 0, 0)", "0 ou 1"),
        ("turret_service_box", "marqueur",
         f"yaw t, r = {FITTING_R:.2f}, y = {PAD_SHELF_Y:+.2f}", "0, 1 ou 2"),
        ("turret_pipe", "marqueur",
         f"yaw t, r = {FITTING_R:.2f}, y = {PAD_SHELF_Y:+.2f}", "0 ou 1"),
        ("turret_ring", "ROTATEUR", f"(0, {RING_BASE:+.2f}, 0)", "1"),
        ("turret_body", "ROTATEUR", f"(0, {BODY_BASE:+.2f}, 0)", "1"),
        ("turret_barrel*", "ROTATEUR",
         f"(+/-e/2, {BARREL_Y:+.2f}, {BARREL_Z:+.2f})", "1 ou 2"),
    )
    for name, parent, where, copies in plan:
        print(f"    {name:<22} {parent:<10} {where:<28} {copies}")
    print(f"    ROTATEUR : Node3D a (0, 0, 0) du marqueur, rotation Y libre "
          f"(42 deg/s). e = ecartement, {BARREL_GAUGE:.2f} m par defaut, "
          f"{BARREL_GAUGE_MAX:.2f} m au maximum.")
    print("    ⚠️ TOUTES CES COTES SE MULTIPLIENT PAR L'ECHELLE DE LA CLASSE — "
          "le maillage ET l'offset, comme le fait deja `_place()`.")

    print("\n  LES TROIS FAMILLES DE VARIETE — a l'interieur d'une classe, sans "
          "reforge")
    print(f"    {'famille':<14} {'jupe':<5} {'canon':<21} {'ecart':>6} "
          f"{'coffrets':<16} {'conduites'}")
    for name, skirt, barrel, gauge, boxes, angles, pipe, pipe_a in FAMILIES:
        angle_txt = "/".join(f"{a:.0f}" for a in angles[:boxes])
        print(f"    {name:<14} {'oui' if skirt else 'non':<5} {barrel:<21} "
              f"{gauge:>6.2f} {f'{boxes} a {angle_txt} deg':<16} "
              f"{f'1 a {pipe_a:.0f} deg' if pipe else 'aucune'}")

    print(f"\n  cotes maitresses relevees sur le binaire : socle "
          f"{report['parts']['turret_pad']['size'][0]:.2f} m de diametre "
          f"({PAD_MODULES} modules), jupe "
          f"{report['parts']['turret_anchor_skirt']['size'][0]:.2f} m ; "
          f"couronne {report['parts']['turret_ring']['size'][0]:.2f} x "
          f"{report['parts']['turret_ring']['size'][1]:.2f} m ; canon "
          f"{report['parts']['turret_barrel']['size'][2]:.2f} m (court "
          f"{report['parts']['turret_barrel_short']['size'][2]:.2f} m) ; "
          f"hauteur totale {TURRET_H:.2f} m")
    print(f"  la couronne emerge de {RING_TOP - PAD_RIM_H:.2f} m au-dessus du "
          f"couronnement du socle : elle y est LOGEE de "
          f"{RING_H - (RING_TOP - PAD_RIM_H):.2f} m")
    print(f"  les tubes debordent de {BARREL_Z + BARREL_LEN - PAD_R:.2f} m "
          f"au-dela du tambour (rayon {PAD_R:.2f} m) ; portee hors-tout "
          f"{BARREL_Z + BARREL_LEN:.2f} m depuis l'axe ; culasse au FOND du "
          f"masque ({BARREL_Z:+.2f}), pas sur la face avant ({BODY_Z1:+.2f})")
    gap, where = report["clearance"]
    print(f"  degagement de rotation mesure : {gap:+.3f} m au plus serre "
          f"({where}) — bloc et canons a l'ecartement maximal contre coffrets, "
          f"conduites et socle, par tranches de 2 cm")
    print(f"  magenta : une fente de {EYE_W:.2f} x {EYE_T:.2f} m au fond du "
          f"masque et deux de {CHEEK_SLIT_T:.2f} x {CHEEK_SLIT_H:.2f} m sur les "
          f"joues, sur une tourelle de {TURRET_H:.2f} m — la plus large fait "
          f"{100 * EYE_W / TURRET_H:.1f} pct (regle dure : 25 pct), plus une "
          f"fente de 3 cm sur {len(PAD_GLOW_MODULES)} des {PAD_MODULES} modules "
          "du socle")
    print(f"  emprise hors-tout posee sur la peau : {FOOTPRINT_R:.2f} m de "
          f"rayon — c'est celle avec laquelle la coque echantillonne sa peau "
          f"(`cortege.TURRET_FOOTPRINT_R`), dans la reservation minimale "
          f"{min(cortege.PAD_RADIUS):.2f} m")

    print("\n  LES DIX-SEPT EMPLACEMENTS, mesures sur la coque livree")
    print(f"    {'marqueur':<12} {'assise':>8} {'bas':>8} {'denivele':>9} "
          f"{'sommet':>8} {'plafond':>9}")
    for name, seat, low, deniv, crest in report["seats"]:
        flag = "  DEPASSE" if crest > cortege.CEILING_Y else ""
        print(f"    {name:<12} {seat:>8.3f} {low:>8.3f} {deniv:>9.3f} "
              f"{crest:>8.3f} {cortege.CEILING_Y - crest:>9.3f}{flag}")
    over = [n for n, _, _, _, c in report["seats"] if c > cortege.CEILING_Y]
    summit = report["summit"]
    print(f"    denivele max {max(d for _, _, _, d, _ in report['seats']):.3f} m "
          f"sous l'emprise de {FOOTPRINT_R:.2f} m, absorbe par une jupe de "
          f"{PAD_BURIED:.2f} m")
    print(f"    {len(over)} tourelles sur {len(report['seats'])} montent au-dessus "
          f"du plafond du DECOR INERTE ({cortege.CEILING_Y:+.2f}), de "
          f"{report['overshoot']:.3f} m au pire — et c'est ACTE : une tourelle se "
          "tire dessus.")
    print(f"    la LOURDE la plus haute culmine a {summit:+.3f}, soit "
          f"{GAMEPLAY_CEILING_Y - summit:.3f} m sous le plafond des PIECES DE "
          f"GAMEPLAY ({GAMEPLAY_CEILING_Y:+.2f}) et {-summit:.2f} unites sous le "
          "plan de vol")
    if report["bay_sweep"]:
        print("\n  ⚠️ BALAYAGE DES CANONS AU-DELA DU COAMING D'UN PONT D'ENVOL "
              f"(allonge portee a {BARREL_Z + BARREL_LEN:.2f} m par la reforge)")
        for turret, bay, depth in report["bay_sweep"]:
            print(f"    {turret} balaie {depth:.2f} m au-dela du coaming de {bay}")

    print(f"\n  primitives : {report['primitives'][0]}/{report['primitives'][2]} "
          f"TEXCOORD_0, {report['primitives'][1]}/{report['primitives'][2]} TANGENT")
    print("  densite de texels (valeurs singulieres, triangle par triangle), "
          f"cible {TEXELS_PER_METER:.3f} tuile/m ({1 / TEXELS_PER_METER:.2f} m/tuile)")
    for name in PART_NAMES:
        d = report["density"].get(name)
        if not d:
            continue
        print(f"    {name:<22} {d['tiles_per_m_min']:.3f} a "
              f"{d['tiles_per_m_max']:.3f}, moyenne {d['tiles_per_m_mean']:.3f} "
              f"t/m ({d['m_per_tile_mean']:.2f} m/tuile), aniso "
              f"{d['anisotropy_max']:.2f}")

    print("\n  repartition en AIRE, relevee sur le .glb — kit brut, tourelle "
          "ASSEMBLEE, et ce qui en est VU")
    total = report["total_area"] or 1.0
    built_total = report["total_built"] or 1.0
    seen_total = report["total_seen"] or 1.0
    print(f"    {'materiau':<22} {'kit':>8} {'':>7}  {'assemble':>8} {'':>7}  "
          f"{'vu':>8} {'':>7}")
    for name, area in sorted(report["built_by_material"].items(),
                             key=lambda kv: -kv[1]):
        raw = report["area_by_material"].get(name, 0.0)
        seen = report["seen_by_material"].get(name, 0.0)
        print(f"    {name:<22} {raw:7.1f} m2 {100.0 * raw / total:5.1f} %  "
              f"{area:7.1f} m2 {100.0 * area / built_total:5.1f} %  "
              f"{seen:7.1f} m2 {100.0 * seen / seen_total:5.1f} %")
    print(f"    {'TOTAL':<22} {total:7.1f} m2          {built_total:7.1f} m2"
          f"          {seen_total:7.1f} m2")
    print(f"  octets     : {report['bytes']}")


def main() -> None:
    report = build()
    _print_report(report)
    if "--plate" in sys.argv:
        render_plate(report)


# ==========================================================================
# Planche de recette — `--plate`
# ==========================================================================
# ADR-0006 : un livrable de la forge n'est pas valide tant qu'il n'a pas ete rendu
# et REGARDE. Deux vignettes portent des TESTS et non des illustrations :
#
#   * la premiere, en noir et blanc, emissifs coupes : une tourelle et un hangar
#     dans le MEME cadre. C'est la COMPARAISON qui est le test — l'un CREUSE,
#     l'autre DEPASSE (BRIEF-0093, a rejouer a chaque reforge) ;
#   * la sixieme, a 55 px de large : la regle 5 de la planche cible (« une petite
#     tourelle doit rester identifiable en 55 px »), silhouettes seules.

TILE_W = 1440
SCENE_H = 620
CLOSE_H = 660
CLASS_H = 600
SMALL_H = 380
ELEV_H = 420
UV_H = 420
SAMPLES = 32

BACKDROP = baykit.BACKDROP
AMBIENT = baykit.AMBIENT
GAME_LIGHTS = baykit.GAME_LIGHTS
CAM_POS = cortege.CAM_POS
CAM_FORWARD = cortege.CAM_FORWARD
CAM_UP = cortege.CAM_UP
CAM_FOV_V = cortege.CAM_FOV_V

#: La paire qui sert de test d'acceptation — la MEME que BRIEF-0091, prise par
#: l'autre bout. Elles sont a 8 m l'une de l'autre, du meme bord, donc dans le
#: meme cadre a la camera du jeu.
#: ⚠️ LA PAIRE A CHANGE, PARCE QUE L'ANCIENNE ETAIT PERIMEE. Le commentaire
#: disait « Turret_14 (s = 428) et Bay_07 (s = 436), a 8 m l'une de l'autre » ;
#: dans la coque livree aujourd'hui, Turret_14 est a s = 415,2 et Bay_07 a
#: s = 450 — TRENTE-CINQ metres, donc les deux hors cadre, et la vignette
#: rendait une vue generale du vaisseau. C'est le genre de peremption qu'aucune
#: mesure n'attrape : le rendu part sans erreur, il ne montre simplement plus
#: rien. Le couple le plus proche des tables actuelles est Turret_06 / Bay_04 :
#: 8,05 m, meme bord (bebord, x ~ -8,4 et -9,3).
ACCEPTANCE_BAY = 4          # Bay_04, s = 224,6, x = -9,30
ACCEPTANCE_TURRET = 6       # Turret_06, s = 216,6, x = -8,40

#: L'hote de la vignette des trois classes. ⚠️ PAS LE MEME QUE CI-DESSUS, et
#: pour une raison mesurable : les trois classes se posent a 6 m d'ecart dans le
#: survol, et Turret_06 en a une DANS l'ouverture de Bay_04. Turret_13 est a
#: 40 m du hangar le plus proche.
CLASSES_TURRET = 13         # Turret_13, s = 410,0, x = +8,80
#: Ou tombe la legende de chaque classe, en coordonnees de cadre : les trois
#: tourelles sont empilees dans la PROFONDEUR, donc a trois hauteurs d'ecran.
CLASS_LABEL_V = (0.42, -0.02, -0.48)

#: La largeur, EN PIXELS, du test de lisibilite de la planche cible.
SILHOUETTE_PX = 55


def _to_blender(v: Vector) -> Vector:
    return Vector((v.x, -v.z, v.y))


def _plate_reset() -> None:
    baykit._plate_reset()


def _plate_lights() -> None:
    baykit._plate_lights()


def _plate_camera(name, position, forward, up, fov, ortho=None):
    return baykit._plate_camera(name, position, forward, up, fov, ortho)


def _label(*args, **kwargs) -> None:
    baykit._label(*args, **kwargs)


def _render(path: str, width: int, height: int) -> None:
    baykit._render(path, width, height)


def _import(path: str, name: str, position: Vector, yaw: float = 0.0) -> list:
    return baykit._import(path, name, position, yaw)


def _place(name: str, position: Vector, yaw: float = 0.0,
           scale: float = 1.0) -> list:
    """Importe UNE piece du kit et la pose. Comme le fera le moteur.

    ⚠️ L'ECHELLE S'APPLIQUE AU MAILLAGE, ET L'APPELANT L'A DEJA APPLIQUEE A LA
    POSITION. Les deux vont ensemble : reduire la piece en laissant ses cotes
    d'assemblage poserait un tube trop petit a la hauteur d'une grosse tourelle
    — un canon flottant au-dessus de son propre masque. C'est mot pour mot le
    piege que `cortege_turret.gd::_place()` documente.
    """
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=OUTPUT)
    fresh = [o for o in bpy.context.scene.objects if o not in before]
    keep = [o for o in fresh if o.name.split(".")[0] == name]
    for obj in fresh:
        if obj not in keep:
            bpy.data.objects.remove(obj, do_unlink=True)
    for obj in keep:
        obj.location = _to_blender(position)
        obj.rotation_euler = Euler((0.0, 0.0, yaw), "XYZ")
        obj.scale = (scale, scale, scale)
        obj.visible_shadow = False
    return keep


def _assemble_class(centre: Vector, index: int, aim: float = 0.0) -> list:
    """Monte UNE tourelle de la classe `index` a `centre` (Y = assise).

    C'est la SEULE façon de juger le lot : le kit livre huit pieces, et aucune ne
    prouve quoi que ce soit seule. `aim` est l'azimut — c'est lui que le moteur
    anime a 42 deg/s, et il ne fait tourner QUE le rotateur.
    """
    name, scale, skirt, barrel, gauge, angles, pipe_a = CLASSES[index]
    del name
    placed: list = []
    if skirt:
        placed += _place("turret_anchor_skirt", centre, scale=scale)
    placed += _place("turret_pad", centre, scale=scale)
    for angle in angles:
        a = math.radians(angle)
        placed += _place(
            "turret_service_box",
            centre + Vector((FITTING_R * math.sin(a), PAD_SHELF_Y,
                             FITTING_R * math.cos(a))) * scale, -a, scale)
    if pipe_a is not None:
        a = math.radians(pipe_a)
        placed += _place(
            "turret_pipe",
            centre + Vector((FITTING_R * math.sin(a), PAD_SHELF_Y,
                             FITTING_R * math.cos(a))) * scale, -a, scale)
    # Le ROTATEUR : couronne, bloc et tubes tournent en un bloc autour de l'axe Y
    # qui passe par l'origine de la couronne.
    ca, sa = math.cos(aim), math.sin(aim)

    def spin(local: Vector) -> Vector:
        return Vector((local.x * ca + local.z * sa, local.y,
                       -local.x * sa + local.z * ca))

    for part, local in (("turret_ring", Vector((0.0, RING_BASE, 0.0))),
                        ("turret_body", Vector((0.0, BODY_BASE, 0.0)))):
        placed += _place(part, centre + spin(local) * scale, aim, scale)
    sides = (0.0,) if gauge <= 0.0 else (-1.0, 1.0)
    for side in sides:
        placed += _place(
            barrel,
            centre + spin(Vector((side * gauge * 0.5, BARREL_Y, BARREL_Z)))
            * scale, aim, scale)
    return placed


def _assemble_turret(centre: Vector, family: int, aim: float = 0.0) -> list:
    """Monte une tourelle de la classe LOURDE, selon la FAMILLE de variete."""
    name, skirt, barrel, gauge, boxes, angles, pipe, pipe_a = FAMILIES[family]
    del name
    placed: list = []
    if skirt:
        placed += _place("turret_anchor_skirt", centre)
    placed += _place("turret_pad", centre)
    for k in range(boxes):
        a = math.radians(angles[k])
        placed += _place(
            "turret_service_box",
            centre + Vector((FITTING_R * math.sin(a), PAD_SHELF_Y,
                             FITTING_R * math.cos(a))), -a)
    if pipe:
        a = math.radians(pipe_a)
        placed += _place(
            "turret_pipe",
            centre + Vector((FITTING_R * math.sin(a), PAD_SHELF_Y,
                             FITTING_R * math.cos(a))), -a)
    ca, sa = math.cos(aim), math.sin(aim)

    def spin(local: Vector) -> Vector:
        return Vector((local.x * ca + local.z * sa, local.y,
                       -local.x * sa + local.z * ca))

    for part, local in (("turret_ring", Vector((0.0, RING_BASE, 0.0))),
                        ("turret_body", Vector((0.0, BODY_BASE, 0.0)))):
        placed += _place(part, centre + spin(local), aim)
    for side in (-1.0, 1.0):
        placed += _place(
            barrel,
            centre + spin(Vector((side * gauge * 0.5, BARREL_Y, BARREL_Z))),
            aim)
    return placed


def _game_shift(aim_s: float) -> float:
    return baykit._game_shift(aim_s)


def _look_at(eye: Vector, target: Vector) -> tuple[Vector, Vector]:
    """(avant, haut) d'une camera qui vise `target` depuis `eye`, SANS ROULIS.

    ⚠️ LA FORMULE EMPLOYEE JUSQU'AU 2026-08-30 RENDAIT UN « HAUT » HORIZONTAL.
    Elle s'ecrivait `(avant x X) x avant`, ce qui developpe en
    `X - avant (avant . X)` : des que la visee n'a pas de composante en X — le
    cas exact d'une vue alignee sur l'axe — elle rend X, c'est-a-dire une camera
    COUCHEE A 90 deg. Le rendu montrait le socle DEBOUT COMME UN MUR, et il
    fallait le regarder pour s'en apercevoir : aucune mesure de ce fichier ne
    cadre une image (ADR-0006, dans les deux sens).

    Le haut se PROJETTE : on retire de la verticale du monde sa part le long de
    l'axe de visee. Et on verifie qu'il pointe encore vers le haut, sans quoi la
    faute se reinstalle en silence a la prochaine vue.
    """
    forward = (target - eye).normalized()
    world_up = Vector((0.0, 1.0, 0.0))
    up = world_up - forward * forward.dot(world_up)
    if up.length < 1e-6:
        raise ak.ContractError(
            "camera a la verticale : le haut de l'image est indefini")
    up.normalize()
    if up.y <= 0.0:
        raise ak.ContractError("le haut de la camera pointe vers le bas")
    return forward, up


def _silhouette(objects: list) -> None:
    """Tout en BLANC PLAT, emissifs compris — la regle 5 de la planche cible.

    Le test des 55 px ne juge pas une matiere, il juge un CONTOUR : c'est
    pourquoi la vignette coupe la couleur ET la lumiere. Si la tourelle n'est
    plus identifiable en blanc sur noir, aucun emissif ne la sauvera a cette
    taille — c'est deja l'argument du test tourelle/hangar, pousse a l'extreme.
    """
    flat = bpy.data.materials.new("silhouette")
    flat.use_nodes = True
    nodes = flat.node_tree.nodes
    nodes.clear()
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)
    emission.inputs[1].default_value = 1.0
    out = nodes.new("ShaderNodeOutputMaterial")
    flat.node_tree.links.new(emission.outputs[0], out.inputs[0])
    for obj in objects:
        if obj.type != "MESH":
            continue
        obj.data.materials.clear()
        obj.data.materials.append(flat)
    world = bpy.context.scene.world
    for node in world.node_tree.nodes:
        if node.type == "BACKGROUND":
            node.inputs[0].default_value = (0.0, 0.0, 0.0, 1.0)


def _tile_acceptance(path: str, report: dict, greyscale: bool) -> None:
    """LE TEST D'ACCEPTATION : une tourelle et un hangar dans le MEME cadre.

    « En noir et blanc, tous emissifs coupes, on distingue immediatement une
    tourelle d'un hangar. » Le meme cadre est rendu deux fois — en valeurs, puis
    en couleur — pour que l'on voie du meme coup ce que la silhouette fait seule
    et ce que l'emissif AJOUTE. S'il fallait la couleur, la premiere image le
    dirait. C'est le test de BRIEF-0093, rejoue apres reforge.
    """
    _plate_reset()
    ts, tx = cortege.TURRETS[ACCEPTANCE_TURRET - 1]
    bs, _ = cortege.BAYS[ACCEPTANCE_BAY - 1]
    shift = _game_shift(0.5 * (ts + bs))
    decor = _import(HULL, "Decor", Vector((0.0, 0.0, shift)))
    bay = baykit._assemble_bay(ACCEPTANCE_BAY, shift)
    seat, _ = turret_seat_y(ts, tx)
    turret = _assemble_class(Vector((tx, seat, -ts + shift)), 2,
                             aim=math.radians(-28.0))
    fighter = _import(baykit.FIGHTER, "Player", Vector((0.0, 0.0, 3.4)))
    if greyscale:
        baykit._to_greyscale(decor + bay + turret + fighter)
    _plate_lights()
    camera = _plate_camera("game", _to_blender(CAM_POS), _to_blender(CAM_FORWARD),
                           _to_blender(CAM_UP), CAM_FOV_V)
    if greyscale:
        _label(camera, "TEST D'ACCEPTATION — NOIR ET BLANC, EMISSIFS COUPES : "
                       f"tourelle LOURDE (Turret_{ACCEPTANCE_TURRET:02d}) et "
                       f"hangar (Bay_{ACCEPTANCE_BAY:02d}), meme cadre",
               -0.97, 0.88, 0.040, TILE_W, SCENE_H, (1.0, 0.88, 0.55))
        _label(camera, "la silhouette seule doit trancher : le hangar CREUSE "
                       "(un cadre vide), la tourelle DEPASSE — deux tubes a "
                       f"{BARREL_Z + BARREL_LEN:.2f} m de l'axe, soit "
                       f"{BARREL_Z + BARREL_LEN - PAD_R:.2f} m au-dela du tambour",
               -0.97, 0.79, 0.031, TILE_W, SCENE_H)
    else:
        _label(camera, "LE MEME CADRE, EN COULEUR — ce que l'emissif AJOUTE a une "
                       "fonction deja lisible en geometrie",
               -0.97, 0.88, 0.040, TILE_W, SCENE_H, (1.0, 0.88, 0.55))
        _label(camera, "le magenta ne fait plus de surface : une fente de "
                       f"{EYE_W:.2f} x {EYE_T:.2f} m au fond du masque, deux de "
                       f"{CHEEK_SLIT_T:.2f} m sur les joues, quatre de 3 cm sur "
                       f"le socle. Regle 4 de la planche : « le magenta signale "
                       "l'energie, pas le volume ».",
               -0.97, 0.79, 0.031, TILE_W, SCENE_H)
    _label(camera, "camera de graybox.tscn sans retouche (0, 14, 5), FOV 62, "
                   "70 deg sous l'horizontale ; Specter-9 reel a sa place de jeu",
           -0.97, -0.91, 0.029, TILE_W, SCENE_H, (0.72, 0.84, 1.0))
    _render(path, TILE_W, SCENE_H)


def _tile_three_quarter(path: str, report: dict) -> None:
    """LA LOURDE SEULE, DE TROIS QUARTS — ce que la camera du jeu ne montre pas.

    La vue de jeu plonge a 70 deg : elle dit si la piece se LIT, pas comment elle
    est faite. Ce cadrage-ci dit le reste — les vingt-quatre semelles du socle,
    les liseres qui bordent chaque plaque, les gradins de chemise et la bouche
    reellement creuse.
    """
    _plate_reset()
    ts, tx = cortege.TURRETS[ACCEPTANCE_TURRET - 1]
    shift = _game_shift(ts)
    _import(HULL, "Decor", Vector((0.0, 0.0, shift)))
    seat, _ = turret_seat_y(ts, tx)
    centre = Vector((tx, seat, -ts + shift))
    _assemble_turret(centre, 1, aim=math.radians(-34.0))
    _plate_lights()
    eye = centre + Vector((6.4, 4.2, 7.4))
    target = centre + Vector((0.0, 0.85, 1.10))
    forward, up = _look_at(eye, target)
    camera = _plate_camera("tq", _to_blender(eye), _to_blender(forward),
                           _to_blender(up), math.radians(38.0))
    _label(camera, "TROIS QUARTS, TOURELLE LOURDE SEULE (famille B) — un canon, "
                   "pas un jeton",
           -0.97, 0.89, 0.040, TILE_W, CLOSE_H, (1.0, 0.88, 0.55))
    _label(camera, f"socle {2 * PAD_R:.2f} m en {PAD_MODULES} semelles blindees ; "
                   f"jupe {2 * SKIRT_R:.2f} m ; couronne {RING_D:.2f} m LOGEE de "
                   f"{RING_H - (RING_TOP - PAD_RIM_H):.2f} m dans la cuvette ; "
                   f"bloc trapu {2 * BODY_HX:.2f} x {BODY_Z1 - BODY_Z0:.2f} x "
                   f"{BODY_H:.2f} ; tubes de {BARREL_LEN:.2f} m a trois gradins, "
                   f"loges dans un masque creuse de {MANTLET_DEPTH:.2f} m",
           -0.97, 0.80, 0.028, TILE_W, CLOSE_H)
    _label(camera, "la depense neuve : toute plaque est posee sur un RETRAIT "
                   "sombre et bordee d'un LISERE ivoire — le seul detail qui "
                   "passe a la fois le seuil de presence (4,4 cm) et le plancher "
                   f"de contraste (10 niveaux). {report['assembled']} tri "
                   "assembles, aucun rivet.",
           -0.97, -0.90, 0.027, TILE_W, CLOSE_H, (0.72, 0.84, 1.0))
    _render(path, TILE_W, CLOSE_H)


def _tile_classes(path: str, report: dict) -> None:
    """LES TROIS CLASSES COTE A COTE, A LA CAMERA DU JEU.

    ⚠️ A LA CAMERA DU JEU, ET PAS A UNE VUE DE STUDIO : c'est le seul cadrage ou
    la hierarchie des trois se juge. Sous une plongee de 70 deg, la hauteur se
    projette a 0,34 et le plan a 0,94 — une planche vue de face ferait croire a
    une difference de taille que le jeu ne montre pas.
    """
    _plate_reset()
    ts, tx = cortege.TURRETS[CLASSES_TURRET - 1]
    shift = _game_shift(ts)
    _import(HULL, "Decor", Vector((0.0, 0.0, shift)))
    # ⚠️ LE LONG DU SURVOL, ET NON EN TRAVERS. Le pont ne fait que 28 m de bord
    # a bord et les marqueurs sont a |x| >= 5,6 : trois tourelles ecartees en X
    # tombaient hors de la coque ou sur la crete dorsale. Alignees sur l'axe de
    # survol, elles restent toutes sur la meme bande plate — et chacune prend
    # SON assise, mesuree a SA station.
    spacing = 6.0
    for k in range(3):
        station = ts + (1 - k) * spacing
        seat, _low = turret_seat_y(station, tx)
        _assemble_class(Vector((tx, seat, -station + shift)), k,
                        aim=math.radians((-38.0, 16.0, -10.0)[k]))
    _plate_lights()
    camera = _plate_camera("cls", _to_blender(CAM_POS), _to_blender(CAM_FORWARD),
                           _to_blender(CAM_UP), CAM_FOV_V)
    _label(camera, "LES TROIS CLASSES, A LA CAMERA DU JEU — memes blocs, trois "
                   "echelles (planche : « MODULES PARTAGES »)",
           -0.97, 0.90, 0.038, TILE_W, CLASS_H, (1.0, 0.88, 0.55))
    for k, row in enumerate(report["classes"]):
        want_l, want_h = PLATE_COTES[row["name"]]
        # ⚠️ Une legende PAR TOURELLE, a SA hauteur d'ecran : les trois sont
        # empilees dans la profondeur, pas cote a cote, et trois legendes
        # alignees en bas ne diraient plus laquelle est laquelle.
        _label(camera, f"{row['name']}  x{row['scale']:.3f}",
               -0.96, CLASS_LABEL_V[k], 0.034, TILE_W, CLASS_H, (0.72, 0.84, 1.0))
        _label(camera,
               f"L {row['length']:.2f} m ({100 * (row['length'] - want_l) / want_l:+.0f} pct) · "
               f"H {row['height']:.2f} m ({100 * (row['height'] - want_h) / want_h:+.0f} pct)",
               -0.96, CLASS_LABEL_V[k] - 0.09, 0.024, TILE_W, CLASS_H)
    _label(camera, "l'ecart de HAUTEUR n'est pas un choix : l'assise la plus "
                   f"haute est -4,270 et le plafond des pieces de gameplay "
                   f"{GAMEPLAY_CEILING_Y:+.2f} — il reste 1,870 m. Une lourde de "
                   "4,2 m culminerait a -0,07, sous le nez du joueur.",
           -0.97, -0.90, 0.026, TILE_W, CLASS_H)
    _render(path, TILE_W, CLASS_H)


def _render_silhouette(path: str, index: int, row: dict) -> tuple[int, int]:
    """UNE classe, en blanc plat, rendue A 55 PIXELS DE LARGE. Rend (l, h) px."""
    _plate_reset()
    placed = _assemble_class(Vector((0.0, 0.0, 0.0)), index, aim=0.0)
    _silhouette(placed)
    base_r = PAD_R if index == 0 else SKIRT_R
    z0 = -base_r * row["scale"]
    z1 = row["reach"]
    margin = 0.05 * (z1 - z0)
    width_m = (z1 - z0) + 2.0 * margin
    px_h = max(6, int(round(SILHOUETTE_PX * (row["height"] + 2.0 * margin)
                            / width_m)))
    # L'ortho_scale est la hauteur VISIBLE ; on la recale sur le rapport de
    # pixels effectif pour que la largeur tombe juste sur les 55 px du test.
    height_m = width_m * px_h / SILHOUETTE_PX
    centre = Vector((0.0, row["height"] * 0.5, (z0 + z1) * 0.5))
    eye = centre + Vector((-40.0, 0.0, 0.0))
    forward, up = _look_at(eye, centre)
    _plate_camera("sil", _to_blender(eye), _to_blender(forward),
                  _to_blender(up), math.radians(20.0), ortho=height_m)
    _render(path, SILHOUETTE_PX, px_h)
    return SILHOUETTE_PX, px_h


def _tile_labels(path: str, height: int, lines: list[tuple]) -> None:
    """Une vignette de TEXTE SEUL, sur fond noir — le support des silhouettes."""
    _plate_reset()
    world = bpy.context.scene.world
    for node in world.node_tree.nodes:
        if node.type == "BACKGROUND":
            node.inputs[0].default_value = (0.0, 0.0, 0.0, 1.0)
    camera = _plate_camera("lbl", _to_blender(Vector((0.0, 0.0, -10.0))),
                           _to_blender(Vector((0.0, 0.0, 1.0))),
                           _to_blender(Vector((0.0, 1.0, 0.0))),
                           math.radians(40.0))
    for text, u, v, size, color in lines:
        _label(camera, text, u, v, size, TILE_W, height, color)
    _render(path, TILE_W, height)


def _tile_elevation(path: str, report: dict) -> None:
    """LE KIT SEUL, ELEVATION — les trois classes et le plafond qui les borne.

    Trois plans : l'assise (ambre), le plafond du decor (rouge) et le plafond des
    PIECES DE GAMEPLAY (vert). C'est la seule image qui montre le conflit mesure
    entre la hauteur de la planche (4,20 m) et le degagement offert par la coque
    (1,870 m au pire emplacement). L'emplacement montre est celui que la MESURE
    designe comme le plus serre, pas un numero ecrit a la main.
    """
    _plate_reset()
    worst = max(report["seats"], key=lambda row: row[1])
    tightest, seat = worst[0], worst[1]
    over = sum(1 for row in report["seats"] if row[4] > cortege.CEILING_Y)
    # ⚠️ La camera est en +X et regarde vers -X : le « droite » de l'image est
    # donc -Z, c'est-a-dire la POUPE. La legere se pose en +Z pour tomber a
    # gauche et la lourde a droite — ordre de lecture, ordre de masse.
    spacing = 8.6
    for k in range(3):
        _assemble_class(Vector((0.0, 0.0, (1 - k) * spacing)), k, aim=0.0)
    baykit._plane_slab(0.0, 0.02, 13.0, 0.10, (0.95, 0.72, 0.28), 2.0)
    baykit._plane_slab(cortege.CEILING_Y - seat, 0.02, 13.0, 0.10,
                       (0.90, 0.32, 0.26), 2.0)
    baykit._plane_slab(GAMEPLAY_CEILING_Y - seat, 0.02, 13.0, 0.10,
                       (0.72, 0.86, 0.60), 2.0)
    _plate_lights()
    camera = _plate_camera(
        "elev", _to_blender(Vector((36.0, 1.20, 0.0))),
        _to_blender(Vector((-1.0, 0.0, 0.0))), _to_blender(Vector((0.0, 1.0, 0.0))),
        math.radians(30.0), ortho=8.2)
    _label(camera, "ELEVATION DE FLANC, LES TROIS CLASSES (proue a GAUCHE, les "
                   "tubes la designent) — assise (ambre) 0,00 ; DECOR (rouge) "
                   f"{cortege.CEILING_Y - seat:+.2f} ; plafond du GAMEPLAY "
                   f"(vert) {GAMEPLAY_CEILING_Y - seat:+.2f}, sous {tightest}",
           -0.985, 0.90, 0.036, TILE_W, ELEV_H, (1.0, 0.88, 0.55))
    _label(camera, f"{over} des {len(report['seats'])} emplacements montent "
                   f"au-dessus du plafond du DECOR : ACTE au BRIEF-0094, une "
                   f"tourelle se tire dessus. Aucun ne touche le plan vert — "
                   f"c'est lui la borne, et c'est lui qui interdit les 4,20 m de "
                   f"la planche : il ne reste que "
                   f"{GAMEPLAY_CEILING_Y - seat:.3f} m au pire emplacement.",
           -0.985, -0.82, 0.028, TILE_W, ELEV_H)
    _label(camera, "⚠️ tout ce qui est SOUS le trait ambre est ENTERRE dans la "
                   f"coque et invisible en jeu : {PAD_BURIED:.2f} m de jupe a "
                   "l'echelle native, c'est ce qui empeche le socle de flotter "
                   "du cote bas d'une chine (creux mesure jusqu'a 0,685 m).",
           -0.985, -0.90, 0.026, TILE_W, ELEV_H, (0.72, 0.84, 1.0))
    _render(path, TILE_W, ELEV_H)


def _tile_uv(path: str, report: dict) -> None:
    _plate_reset()
    ts, tx = cortege.TURRETS[ACCEPTANCE_TURRET - 1]
    shift = _game_shift(ts)
    decor = _import(HULL, "Decor", Vector((0.0, 0.0, shift)))
    seat, _ = turret_seat_y(ts, tx)
    turret = _assemble_class(Vector((tx, seat, -ts + shift)), 2,
                             aim=math.radians(-28.0))
    baykit._apply_checker(decor + turret)
    _plate_lights()
    # ⚠️ MEME ANGLE QUE LE JEU, MAIS PLUS PRES. A la position exacte de la
    # camera de jeu, la tourelle occupe un quinzieme du cadre et le damier ne
    # s'y lit pas — on ne verifierait rien. L'angle, lui, ne bouge pas d'un
    # degre : c'est lui qui decide de l'etirement qu'on cherche.
    focus = Vector((tx, seat + 0.60, -ts + shift))
    camera = _plate_camera("uv", _to_blender(focus - CAM_FORWARD * 11.0),
                           _to_blender(CAM_FORWARD), _to_blender(CAM_UP),
                           CAM_FOV_V)
    d = report["density"]["turret_body"]
    _label(camera, "DAMIER UV — grande case = 1 tuile de 5,00 m, petite = 62,5 cm ; "
                   "la MEME echelle sur la coque et sur le kit",
           -0.97, 0.88, 0.038, TILE_W, UV_H, (1.0, 0.88, 0.55))
    _label(camera, f"projection en boite {TEXELS_PER_METER:.3f} tuile/m ; "
                   f"anisotropie max mesuree sur le bloc {d['anisotropy_max']:.2f} "
                   f"(borne theorique de la methode : 1,73). Aucune texture ne "
                   "part dans le .glb (ADR-0028) : ce damier n'existe que sur "
                   "cette image.",
           -0.97, 0.78, 0.028, TILE_W, UV_H)
    _render(path, TILE_W, UV_H)


# ==========================================================================
# Composition de la planche
# ==========================================================================


def _load_tile(path: str, width: int, height: int):
    import numpy as np

    image = bpy.data.images.load(path)
    buffer = np.empty(len(image.pixels), dtype=np.float32)
    image.pixels.foreach_get(buffer)
    bpy.data.images.remove(image)
    return buffer.reshape(height, width, 4)


def _blit(sheet, tile, left: int, bottom: int, zoom: int) -> None:
    """Colle une vignette AU PLUS PROCHE VOISIN — jamais interpolee.

    ⚠️ Le test des 55 px ne prouve rien si l'agrandissement lisse : c'est
    exactement le pixel de 55 px qu'il faut voir grossi, pas une version
    reechantillonnee de lui.
    """
    h, w, _ = tile.shape
    big = tile.repeat(zoom, axis=0).repeat(zoom, axis=1)
    sheet[bottom:bottom + h * zoom, left:left + w * zoom, :3] = \
        big[:, :, :3].clip(0.0, 1.0)


def _compose(tiles: list[tuple[str, int]], out: str) -> None:
    import numpy as np

    height = sum(h for _, h in tiles)
    sheet = np.zeros((height, TILE_W, 4), dtype=np.float32)
    sheet[..., 3] = 1.0
    cursor = 0
    for path, tile_h in tiles:
        tile = _load_tile(path, TILE_W, tile_h)
        top = height - cursor - tile_h
        sheet[top:top + tile_h] = tile
        cursor += tile_h
    result = bpy.data.images.new("sheet", width=TILE_W, height=height)
    result.pixels.foreach_set(sheet.reshape(-1))
    result.filepath_raw = out
    result.file_format = "PNG"
    result.save()
    bpy.data.images.remove(result)
    print(f"-> {out}  ({TILE_W} x {height})")


def render_plate(report: dict) -> None:
    staging = tempfile.mkdtemp(prefix="aegis-turretkit-plate-")
    tiles: list[tuple[str, int]] = []
    try:
        path = os.path.join(staging, "bw.png")
        _tile_acceptance(path, report, greyscale=True)
        tiles.append((path, SCENE_H))
        path = os.path.join(staging, "color.png")
        _tile_acceptance(path, report, greyscale=False)
        tiles.append((path, SCENE_H))
        path = os.path.join(staging, "tq.png")
        _tile_three_quarter(path, report)
        tiles.append((path, CLOSE_H))
        path = os.path.join(staging, "cls.png")
        _tile_classes(path, report)
        tiles.append((path, CLASS_H))

        # --- LE TEST DES 55 PIXELS (regle 5 de la planche cible) ----------
        sizes = []
        for index, row in enumerate(report["classes"]):
            small = os.path.join(staging, f"sil{index}.png")
            sizes.append((small,) + _render_silhouette(small, index, row))
        lines = [
            ("TEST DE LISIBILITE A 55 PIXELS — silhouettes seules, emissifs "
             "coupes (regle 5 de la planche)", -0.97, 0.86, 0.052,
             (1.0, 0.88, 0.55)),
            ("a gauche : rendu a 55 px de large, taille reelle. a droite : le "
             "MEME rendu agrandi six fois au plus proche voisin — aucune "
             "interpolation, on regarde les pixels du test.",
             -0.97, 0.74, 0.036, (1.0, 1.0, 1.0)),
        ]
        for k, row in enumerate(report["classes"]):
            lines.append((row["name"], -0.62 + 0.60 * k, -0.62, 0.042,
                          (0.72, 0.84, 1.0)))
            lines.append((f"{sizes[k][1]} x {sizes[k][2]} px",
                          -0.62 + 0.60 * k, -0.72, 0.030, (1.0, 1.0, 1.0)))
        labels = os.path.join(staging, "sil_labels.png")
        _tile_labels(labels, SMALL_H, lines)
        sheet = _load_tile(labels, TILE_W, SMALL_H)
        for k, (small, px_w, px_h) in enumerate(sizes):
            tile = _load_tile(small, px_w, px_h)
            left = 150 + k * 430
            _blit(sheet, tile, left, SMALL_H - 190, 1)
            _blit(sheet, tile, left + 90, SMALL_H - 220, 6)
        composed = os.path.join(staging, "sil.png")
        _save_tile(sheet, composed)
        tiles.append((composed, SMALL_H))

        path = os.path.join(staging, "elev.png")
        _tile_elevation(path, report)
        tiles.append((path, ELEV_H))
        path = os.path.join(staging, "uv.png")
        _tile_uv(path, report)
        tiles.append((path, UV_H))
        os.makedirs(os.path.dirname(PLATE), exist_ok=True)
        _compose(tiles, PLATE)
    finally:
        for leftover in sorted(os.listdir(staging)):
            os.remove(os.path.join(staging, leftover))
        os.rmdir(staging)


def _save_tile(array, path: str) -> None:
    height, width, _ = array.shape
    image = bpy.data.images.new("tile", width=width, height=height)
    image.pixels.foreach_set(array.reshape(-1))
    image.filepath_raw = path
    image.file_format = "PNG"
    image.save()
    bpy.data.images.remove(image)


if __name__ == "__main__":
    main()
