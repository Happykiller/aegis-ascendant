"""build_citadel_kit.py — le kit de la Citadelle de Defense (BRIEF-0096/0097).

    blender-aegis -b -t 1 -P tools/blender/build_citadel_kit.py
    blender-aegis -b -t 1 -P tools/blender/build_citadel_kit.py -- --plate
    ./scripts/build-hull.sh citadel_kit
    ./scripts/build-hull.sh --check citadel_kit      # + controle de determinisme

Produit `assets/imported/models/backgrounds/citadel_kit.glb` et, avec `--plate`,
la planche de recette `docs/forge/output/BRIEF-0097-planche-vantaux.png`.

Le script EST la source (ADR-0008) : aucun `.blend` versionne, aucun alea, deux
executions successives rendent le meme sha256.


CE QUE CE FICHIER EST, ET POURQUOI IL EXISTE
============================================
Neuf pieces, chacune modelisee dans le repere de la CITADELLE, que le moteur
(`CortegeCitadel`) assemble a la station s = 240 du troncon 3 du Long Cortege.

    citadel_leaf      le VANTAIL, 12,90 m — la MOITIE de la porte, qui coulisse
    citadel_housing   le LOGEMENT, un FOURREAU de 4,50 m qui le recoit
    citadel_pylon     le PORTIQUE d'extremite, qui porte le surplomb
    citadel_bastion   la MASSE etagee, dans la tranchee du pont median
    citadel_crown     la COURONNE qui coiffe le bastion
    citadel_relay     le RELAIS, destructible — le BRANCHEMENT
    citadel_conduit   le CONDUIT relais -> artere, la piece qui dit « ceci
                      alimente cela » EN GEOMETRIE
    citadel_core      le NOYAU, destructible — la REVOLUTION, le point le plus haut
    citadel_shield    le PANNEAU de bouclier

⚠️ LA RAISON DU KIT N'EST PAS ESTHETIQUE, ELLE EST MECANIQUE, ET C'EST LA
QUATRIEME FOIS. Les hangars (BRIEF-0091), les affuts (BRIEF-0093) puis les nœuds
d'epine (BRIEF-0094) ont tous quitte `build_long_cortege.py` pour la meme raison :
une piece cuite dans un troncon ne meurt pas sans emporter ses voisines, les cinq
troncons partageant un maillage et un jeu de materiaux. Ici DEUX relais et UN
noyau se detruisent separement, et la porte S'OUVRE (LOT 4 : deux vantaux qui se
retractent dans deux logements, plutot qu'une poutre escamotee d'un bloc).

D'ou la regle dure, reprise mot pour mot du nœud d'epine :
**AUCUN EMISSIF HORS DES PIECES QUI MEURENT** (`citadel_relay`, `citadel_core`).
S'il y en avait sur les vantaux, les bastions ou les couronnes, la mort d'un
relais ne se VERRAIT pas. Le harnais compte l'aire emissive piece par piece et
echoue le build si une autre en porte un millimetre carre.


LE LOT 4 (BRIEF-0097) : LA PORTE S'OUVRE — CE QUI A CHANGE, ET RIEN D'AUTRE
==========================================================================
`citadel_gate`, poutre d'un seul tenant de 34,40 m, est REMPLACEE par deux
pieces miroitees : `citadel_leaf` (le vantail) et `citadel_housing` (le
logement). **Les six autres pieces ne bougent pas d'un micron** — leur code
n'est pas touche, et le compte-rendu le PROUVE par le sha256 des accesseurs de
chaque nœud, pas par une affirmation.

La chaine de cotes du brief tient TROIS choses a la fois, et elle est
arithmetique :

    ferme     le vantail va de x = 0,00 a 12,90 ; le logement de 12,70 a 17,20.
              Recouvrement 0,20 m : AUCUN JOUR au bout.
    ouvert    course de 4,25 m -> le vantail va de 4,25 a 17,15, soit 5 cm SOUS
              le bout exterieur (17,20) : rien ne depasse jamais.
    la passe  |x| < 4,25, donc 8,50 m monde — quatre fois la largeur du corps du
              Specter-9 (1,76 unite, ADR-0034).

⚠️ ET LE SOMMET DU LOGEMENT EST LA COTE QUI PEUT TOUT CASSER EN SILENCE. Un
fourreau est plus grand que ce qu'il recoit ; s'il montait de 30 cm au-dessus du
vantail depuis la meme assise, il franchirait le plafond du decor inerte
(`ADR-0041`, -3,00) sans qu'aucun test ne rougisse. C'est donc son ASSISE qui
descend (-6,90 contre -6,60), et son sommet tombe a -3,00 exactement, comme
celui du vantail. Le harnais compose assise + hauteur mesuree et echoue au
centimetre.


LES QUATRE SILHOUETTES — C'EST LE CRITERE D'ACCEPTATION
=======================================================
« En noir et blanc, emissifs coupes, on identifie bastion != relais != noyau !=
passage sans hesitation. » (consigne 19 du redesign)

Trois familles occupent deja l'espace des formes sur cette coque, et une
quatrieme ne peut pas se poser sur leurs axes sans tomber du cote de l'une :

    hangar        negatif, horizontal, RECTANGULAIRE   un cadre vide
    affut         positif, horizontal, TRAPU           un tambour et deux tubes
    nœud d'epine  positif, VERTICAL, EFFILE            un fut et des DIAGONALES

Les quatre pieces du verrou prennent donc quatre axes NEUFS, et chacun est
MESURE au harnais, pas affirme au commentaire :

  1. la PORTE = la LONGUEUR. 34,40 m assemblee (deux vantaux et deux logements)
     pour 1,20 m d'epaisseur, soit 28,7 : 1. Rien d'autre sur ce vaisseau ne
     traverse le cadre. Et elle se lit en DEUX MOITIES : voir la machoire.
  2. le BASTION = la MASSE ETAGEE. Le seul volume a deux niveaux du vaisseau
     (corps +2,90, couronne +0,60 par-dessus). Il est PLUS LARGE QUE HAUT
     (4,50 m pour 2,90 m), et c'est cela qui l'empeche de se lire comme un affut
     geant : le harnais le verifie sur le binaire.
  3. le RELAIS = le BRANCHEMENT. Court, epais, un COLLIER a mi-hauteur, et un
     CONDUIT qui en sort au ras du pont et court vers le centre sur 4,20 m. Le
     conduit est la piece la plus importante du brief : il dit « ceci alimente
     cela » sans emissif, donc au test noir et blanc.
     ⚠️ IL EST PRISMATIQUE, PAS DE REVOLUTION, et c'est une contrainte et non un
     gout : la revolution est la signature du NOYAU. Un relais en tambour et un
     noyau en tambour, ce sont deux pieces qu'on confond a 23 px/m. Le harnais
     mesure l'ecart a la circularite des deux et exige qu'il diverge.
  4. le NOYAU = la REVOLUTION. Le seul solide de revolution du verrou, sur l'axe,
     et le POINT LE PLUS HAUT (-2,40, soit 60 cm au-dessus des couronnes et de la
     porte). Il monte la PARCE QU'IL SE TIRE DESSUS : le seul volume autorise a
     culminer est celui qu'on peut detruire, et c'est ce qui le designe comme le
     centre sans un mot de HUD.


LES DEUX MACHOIRES — C'EST LE CRITERE D'ACCEPTATION DU LOT 4
===========================================================
« Il manque le vantail : pas de tableau, pas de ligne de refend au milieu, pas
de deux moitiees. » — capture du 2026-09-04, sur la denture du LOT 2.

Cette denture-la etait un PEIGNE POSE SUR LE DESSUS : douze dents alternant le
long de x, dents vers le haut, sans rangee en vis-a-vis. Vue d'en haut elle se
lit comme un creneau de rempart. Trois choses la remplacent, et elles ne sont
pas des gouts :

  1. LES DENTS SONT DANS L'EPAISSEUR. L'epaisseur (1,20 m) est decoupee en SIX
     bandes de 0,20 m ; ce vantail porte les bandes 0, 2 et 4 — TROIS dents, un
     compte IMPAIR — et laisse les trois autres en mortaises.
     ⚠️ CE N'EST PAS UN CHOIX D'AXE, C'EST LE SEUL QUI MARCHE. Le miroir du
     moteur est un yaw de pi : il envoie (x, s) sur (-x, -s). Une denture qui
     alternerait EN HAUTEUR reviendrait donc identique sur l'autre vantail —
     dent contre dent. C'est l'excentricite en `s`, et elle seule, que le yaw
     retourne. La bande k revient en bande 5-k : {0,2,4} devient {5,3,1}, soit
     exactement le complementaire. Chaque dent tombe en face d'une mortaise.
  2. LA LIGNE DE REFEND SE VOIT, et elle se voit D'EN HAUT — la camera plonge a
     70 deg, donc a 20 deg de la VERTICALE, et un joint grave dans la face avant
     ne rendrait aucun pixel (c'est la mesure qui a coute une couronne emissive
     au nœud d'epine). Trois signaux la portent :
       * le TABLEAU : les 2,40 m les plus internes du vantail sont plus EPAIS en
         haut que la poutre (sommet de 0,96 m de large contre 0,60), ce qui pose
         deux lignes transversales a x = +/- 2,40 et double la largeur apparente
         du dessus au centre ;
       * la MACHOIRE : trois dents claires et trois mortaises noires de 0,60 m
         de creux, et la PHASE S'INVERSE en franchissant x = 0. C'est le seul
         endroit du vaisseau ou un motif change de phase sur une ligne : l'œil y
         lit deux pieces, pas une ;
       * le REFEND : les cinq premiers centimetres du vantail rentrent de 5 cm.
         Ferme, les deux rentrants font une gorge en V de 10 cm de large qui
         descend les deux faces et passe sous la porte.
  3. ET LA FERMETURE EST ARITHMETIQUE, PAS ESPEREE. Une denture qui se
     RECOUVRIRAIT vraiment est IMPOSSIBLE ici, et la demonstration tient en deux
     lignes : notons a(s) l'abscisse la plus interne de la matiere du vantail
     dans la bande s. Le vantail babord occupe alors x <= -a(-s). Il n'y a de
     jour nulle part si et seulement si a(s) + a(-s) <= 0 pour toute bande ;
     avec une denture de saillie p (a(s) vaut a et a+p selon la bande), cela
     force a <= -p/2 : le vantail devrait FRANCHIR l'axe de la moitie de sa
     saillie. Il perdrait autant sur la passe (8,50 - p) et sortirait de son
     emprise « x 0 -> 12,90 ». La denture est donc a TENON ET MORTAISE : la face
     de butee reste pleine et plane a x = 0, la dent d'un vantail vient fermer
     la mortaise de l'autre, et le motif s'engrene A L'ŒIL sans qu'aucun metre
     cube ne se chevauche. `_seam_report()` le MESURE au lancer de rayons sur le
     binaire, dans les deux directions, plutot que de le supposer.


LE LOGEMENT — UN FOURREAU, DONC UN VOLUME CREUX, DONC OUVERT PAR LE HAUT
=======================================================================
Le vantail rentre jusqu'a 17,15 et son sommet est DEJA au plafond du decor
(-3,00). Le logement ne peut donc rien avoir au-dessus de lui : c'est un U —
deux joues et une sole — et non une boite. Ce qui se voit d'en haut, porte
fermee, est une FENTE SOMBRE de 1,24 m de large et 4,30 m de long a chaque bout
de la porte ; ouverte, le vantail la remplit. La fente EST l'explication du
mecanisme, et elle ne coute pas un triangle de plus.

Les jeux sont mesures, pas supposes : 2 cm en lateral (joues a 0,62 pour un
vantail a 0,60) et 2 cm sous l'assise (sole a 0,28 pour un vantail assis
0,30 plus haut). `_housing_fit()` les relit sur les sommets du binaire, aux DEUX
positions de la course.


DEUX ECARTS AU TABLEAU DU BRIEF, ASSUMES ET MESURES
===================================================
Ils sont dans le compte-rendu, ils sont ici, et le harnais les nomme un par un
plutot que de les laisser passer en silence (`_EMPRISE_ECARTS`).

  * `citadel_pylon` va jusqu'a x = 13,75 et non 15,60. Le tableau lui donne
    « x 15,60 a 17,20 » ; la MEME page du brief lui demande de « venir s'appuyer
    sur la lisse d'epaule (x ~ 13,88, Y ~ -7,65) ». Les deux sont incompatibles :
    la lisse est INBOARD de l'emprise. Un portique qui s'arrete a 15,60 flotte
    au-dessus du vide — exactement le defaut qu'il existe pour corriger. Le talon
    va donc chercher la coque, et sa penetration est MESUREE contre le profil
    reel (`_flank_x`), taper du troncon 3 compris.
  * `citadel_conduit` culmine a +0,62 et non +0,35. Entre son depart (x 5,40, pont
    interieur a -4,30) et son arrivee (x 1,20, rebord de l'artere a -4,02), la
    peau MONTE de 0,28 m — mesuree sur `cortege._surface_y`, pas estimee. Un
    conduit de 0,35 m assis a -4,30 serait enterre aux quatre cinquiemes a son
    extremite interieure, c'est-a-dire precisement la ou il doit se lire. Son
    dessus est donc HORIZONTAL a -3,72 et c'est son dessous qui suit le terrain :
    il degage 0,58 m au depart et 0,30 m a l'arrivee, et sa ligne pointe le
    noyau.


L'ECHELLE DE DEPLIAGE — LA MEME QUE LE BORDE, ET C'EST OBLIGATOIRE
==================================================================
Le kit partage les slots du borde. Deux echelles de depliage sur un MEME slot,
c'est la faute qu'a corrigee BRIEF-0090 sur Ambry : la carte sortirait au bon
grain sur la coque et au mauvais sur le verrou, cote a cote, sur le seul objet du
niveau qui touche la coque sur 34 m. Le kit est donc deplie a 0,200 tuile/m
(5,00 m par tuile) comme `bay_kit`, `turret_kit` et `spine_kit`.
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
# Meme raison que pour les trois kits precedents : une cote calculee ici et une
# cote calculee la-bas divergeraient en silence. `build_turret_kit` est importe
# pour ses HARNAIS — controle de solidite, controle d'axe, densite de texels y
# sont ecrits, mesures et commentes ; les recopier, c'est se donner deux versions
# a maintenir de la meme preuve.
sys.path.insert(0, _HERE)
import build_long_cortege as cortege   # noqa: E402
import build_bay_kit as baykit         # noqa: E402  (planche : outillage commun)
import build_turret_kit as turretkit   # noqa: E402  (planche + harnais partages)

OUTPUT = os.path.join(_REPO, "assets/imported/models/backgrounds/citadel_kit.glb")
PLATE = os.path.join(_REPO, "docs/forge/output/BRIEF-0097-planche-vantaux.png")
HULL = cortege.OUTPUT
FIGHTER = cortege.FIGHTER

# ==========================================================================
# Le repere, et les deux nombres qui le fixent
# ==========================================================================
# Repere KIT : X lateral (celui de la coque, tel quel), Y haut, Z survol,
# +Z = PROUE. La station `s` d'une piece se lit donc en Z par z = -(s - 240).
#
# ⚠️ CHAQUE PIECE EST CENTREE EN Z SUR SON ORIGINE, ET CE N'EST PAS UN DETAIL DE
# MISE EN PAGE. Le moteur MIROITE sept pieces par un yaw de pi, qui envoie
# (x, z) sur (-x, -z). Une piece dont la boite n'est pas centree en Z se
# retrouverait, a babord, DECALEE LE LONG DU VAISSEAU d'exactement deux fois son
# excentricite — un bastion a s+6 d'un bord et a s-6 de l'autre. Aucune bbox,
# aucun compte de triangles ne le verrait ; il faudrait jouer la sequence et
# regarder les deux bords en meme temps. Le harnais l'exige donc sur les neuf.
#
# En X au contraire, le X DE LA COQUE EST CUIT DANS LA GEOMETRIE (le bastion vit
# a x 6,90..11,40 dans son propre maillage). C'est ce qui permet au moteur de
# poser tribord et babord avec LA MEME translation (0, assise, z_c) et pour seule
# difference le yaw — donc de ne pas pouvoir les desynchroniser.
#
# ⚠️ ET IL Y A DESORMAIS DEUX REGLES DE MIROIR, PAS UNE — LE HARNAIS LES DISTINGUE.
# Six pieces sont FRANCHEMENT TRIBORD : leur matiere commence a x > 0,05, et les
# deux copies ne se touchent jamais. Le VANTAIL, lui, a pour origine SON BOUT
# INTERIEUR (x = 0) et non son centre : c'est ce qui permet au moteur d'ecrire la
# course comme une translation en x — 0 ferme, 4,25 ouvert — sans arithmetique de
# cote. Sa matiere COMMENCE donc a x = 0 exactement, et les deux copies se
# TOUCHENT sur l'axe : c'est meme la definition d'une porte fermee. Une regle
# unique « x > 0,05 » refuserait une piece juste ; une regle unique « x >= 0 »
# laisserait passer un bastion qui deborde. `ORIGIN_AT_INNER_END` nomme la
# difference (voir `_audit`). Le centrage en Z, lui, vaut pour les neuf sans
# exception : c'est l'excentricite en `s` que le yaw retourne, et la boite du
# vantail est bien centree en s (+/- 0,60) — ce qui est EXCENTRE chez lui, c'est
# la matiere de sa machoire dans cette boite, et c'est precisement ce qu'on veut
# retourner.
CITADEL_STATION = 240.0

#: Les neuf noms. Ils sont FIGES PAR LE BRIEF, pas choisis ici : le moteur monte
#: par le NOM et un renommage casse le niveau EN SILENCE — rien n'est trouve,
#: rien n'est dit. Le harnais echoue si l'un manque ou si l'un est en trop.
PART_NAMES = (
    "citadel_leaf", "citadel_housing", "citadel_pylon", "citadel_bastion",
    "citadel_crown", "citadel_relay", "citadel_conduit", "citadel_core",
    "citadel_shield",
)

#: Les pieces que le moteur MIROITE (yaw pi). Elles sont modelees TRIBORD, et
#: aucune version babord n'est livree.
MIRRORED = ("citadel_leaf", "citadel_housing", "citadel_pylon",
            "citadel_bastion", "citadel_crown", "citadel_relay",
            "citadel_conduit")

#: ⚠️ LA PIECE DONT L'ORIGINE EST SON BOUT INTERIEUR, ET NON SON CENTRE. Elle a
#: le droit — le devoir — de commencer a x = 0 : c'est la ou elle rencontre sa
#: jumelle babord quand la porte est fermee. Le harnais lui applique « x >= 0 »
#: au lieu de « x > 0,05 », et rien d'autre ne change.
ORIGIN_AT_INNER_END = ("citadel_leaf",)

#: Ce que le moteur DETRUIT separement — et donc les deux seules pieces qui ont
#: le droit de porter de l'emissif.
DESTRUCTIBLE = ("citadel_relay", "citadel_core")

# ==========================================================================
# LES ASSISES — RELEVEES DU BRIEF, jamais reinventees
# ==========================================================================
# Y de la coque ou tombe le Y = 0 de chaque piece. Elles viennent du profil de
# `build_long_cortege.py` et du LOT 0 du plan ; le brief les redonne en tableau.
# Elles ne servent PAS a modeler (chaque piece est batie sur son propre Y = 0) :
# elles servent a COMPOSER la cote de plafond, ce que le brief exige en toutes
# lettres — « a verifier en composant l'assise du plan avec la hauteur mesuree ».
SEAT: dict[str, float] = {
    "citadel_leaf": -6.60,      # assise ENTERREE — celle de la porte du LOT 2
    "citadel_housing": -6.90,   # 30 cm PLUS BAS : un fourreau descend, il ne
                                # monte pas (le sommet reste a -3,00)
    "citadel_pylon": -7.65,     # la lisse d'epaule
    "citadel_bastion": -6.50,   # le fond de la tranchee de bastion
    "citadel_crown": -3.60,     # le pont du bastion
    "citadel_relay": -4.30,     # le pont interieur
    "citadel_conduit": -4.30,   # le pont interieur
    "citadel_core": -4.58,      # le fond du canal de l'artere
    "citadel_shield": -3.90,    # CENTRE du panneau (decide, voir ci-dessous)
}

#: ⚠️ LE BOUCLIER EST LE SEUL DONT L'ASSISE N'EST PAS DANS LE BRIEF, ET C'EST UNE
#: DECISION, PAS UN RELEVE. Le tableau lui donne « centre du panneau, Y -1,50 a
#: +1,50 » sans dire ou tombe ce centre. Le poser a -3,90 met son ARETE HAUTE a
#: -2,40, c'est-a-dire EXACTEMENT au sommet du noyau qu'il protege : le joueur
#: voit son tir s'arreter au niveau de ce qu'il visait, et pas dix centimetres
#: au-dessus ou en dessous. Son pied plonge alors a -5,40, sous le fond du canal
#: (-4,58) : un champ sort de la coque, il ne se pose pas dessus.
SHIELD_IS_DECIDED = True

#: Z d'assemblage de chaque piece : z_c = -(s_centre - 240). C'est le SECOND et
#: dernier nombre dont le moteur a besoin par piece.
ASSEMBLY_Z: dict[str, float] = {
    "citadel_leaf": 0.00,       # s 240,00 — la face avant du verrou
    "citadel_housing": 0.00,    # s 240,00 — il enserre le bout du vantail
    "citadel_pylon": 0.00,      # s 240,00 — il enserre le bout de la poutre
    "citadel_bastion": -2.80,   # s 242,80 (emprise 239,60 -> 246,00)
    "citadel_crown": -3.50,     # s 243,50 (emprise 241,60 -> 245,40)
    "citadel_relay": -1.40,     # s 241,40 — `CortegeCitadel.RELAY_S`
    "citadel_conduit": -1.40,   # s 241,40 — il sort du relais
    "citadel_core": -3.40,      # s 243,40 — `CortegeCitadel.CORE_S`
    "citadel_shield": -2.10,    # s 242,10 — 1,30 m EN AVANT du noyau
}

#: Combien de fois chaque piece tombe dans le verrou assemble.
ASSEMBLY_COPIES: dict[str, int] = {
    "citadel_leaf": 2, "citadel_housing": 2, "citadel_pylon": 2,
    "citadel_bastion": 2, "citadel_crown": 2, "citadel_relay": 2,
    "citadel_conduit": 2, "citadel_core": 1, "citadel_shield": 1,
}

#: Les deux plafonds d'`ADR-0041`. Ils s'appliquent aux pieces de KIT et non au
#: maillage de coque : `BUILD_CEILING_Y = -3,20` borne la coque et a deja refuse
#: une passerelle a -3,15 ; le kit rend les 20 cm que la coque interdirait.
DECOR_CEILING_Y = cortege.CEILING_Y            # -3,00
GAMEPLAY_CEILING_Y = turretkit.GAMEPLAY_CEILING_Y   # -2,40 (relu dans le moteur)

#: Quel plafond s'applique a quelle piece. Le decor inerte reste sous -3,00 ; ce
#: qui se DETRUIT a le droit d'aller a -2,40. Le bouclier est range du cote du
#: gameplay : il encaisse les tirs et il disparait a `SHIELD_DOWN`.
CEILING_OF: dict[str, float] = {
    name: (GAMEPLAY_CEILING_Y if name in DESTRUCTIBLE or name == "citadel_shield"
           else DECOR_CEILING_Y)
    for name in PART_NAMES
}

#: Meme densite que le borde : voir l'en-tete (deux echelles sur un meme slot).
TEXELS_PER_METER = cortege.HULL_TEXELS_PER_METER

#: Budget du brief : 3 000 triangles pour le KIT ENTIER. La citadelle est
#: instanciee UNE SEULE FOIS par partie — `turret_kit` l'est 38 fois, `bay_kit` 7,
#: `spine_kit` 5 — elle peut donc etre la piece la plus riche du vaisseau. Le
#: budget la borne quand meme.
TRI_BUDGET_KIT = 3_000

#: Couleurs reservees aux TIRS (charte SS3) : interdites ici comme ailleurs.
FORBIDDEN_HEX = cortege.FORBIDDEN_HEX

#: `AA_Trim` : arretes de lecture SEULEMENT. Le brief le chiffre.
TRIM_SHARE_MAX = 0.03

# ==========================================================================
# LE VANTAIL — la MOITIE de la porte, et la MACHOIRE
# ==========================================================================
#: Le bout EXTERIEUR de la porte assemblee. ⚠️ 17,20 ET NON 14,00, ET CE N'EST
#: PAS UN EXCES DE ZELE. La coque fait 28 m bord a bord ; le cadre de la camera,
#: au plan du pont, en fait 41,60. Une barriere arretee au borde laisserait le
#: joueur CONTOURNER le verrou par le vide, et la sequence deviendrait
#: facultative. La valeur est celle du LOT 2, inchangee : c'est elle que le
#: portique va chercher (`PYLON_X1`).
DOOR_HALF_X = 17.20
#: LA CHAINE DE COTES, ET ELLE EST ARITHMETIQUE (voir l'en-tete).
#:      0,00 + 12,90 = 12,90  ferme : le bout entre de 0,20 m dans le logement
#:      4,25 + 12,90 = 17,15  ouvert : 5 cm SOUS le bout exterieur
#:      2 x 4,25     =  8,50  la passe, quatre fois la largeur du chasseur
LEAF_LEN = 12.90
LEAF_TRAVEL = 4.25
LEAF_HALF_S = 0.60
LEAF_H = 3.60
#: Le rentrant du couronnement : la poutre s'amincit de 1,20 a 0,92 m au-dessus
#: de 2,62. C'est cette ligne d'ombre horizontale, filant sur 34 m, qui fait lire
#: la LONGUEUR — une boite lisse de 34 m ne se lit que par ses deux bouts.
LEAF_SILL_Y = 2.34
LEAF_STEP_Y = 2.62
LEAF_HALF_S_TOP = 0.46
LEAF_COPING_Y = 3.30
LEAF_HALF_S_CAP = 0.30

#: LE TABLEAU — les 2,40 m les plus internes, PLUS EPAIS EN HAUT que la poutre.
#: Son dessus fait 0,96 m de large la ou celui de la poutre en fait 0,60 : deux
#: lignes transversales a x = +/- 2,40 encadrent le joint, et la largeur
#: apparente du dessus DOUBLE au centre. C'est le « tableau » que la capture du
#: LOT 2 disait manquant, et il ne coute qu'un jeu de cotes dans la meme section.
JAMB_X = 2.40
JAMB_RAMP = 0.20            # jamais une marche : voir `_leaf_plan`
JAMB_HALF_S_TOP = 0.58
JAMB_HALF_S_CAP = 0.48
JAMB_COPING_Y = 3.46

#: LE REFEND — les 5 premiers centimetres rentrent de 5 cm. Ferme, les deux
#: rentrants font une gorge de 10 cm qui descend les deux faces et passe sous la
#: porte : c'est le « jeu d'ombre » que le brief demande, et le seul signal du
#: joint qui se voie AUTREMENT que d'en haut.
REVEAL_X = 0.05
REVEAL_IN = 0.05

#: LA MACHOIRE — six bandes dans l'EPAISSEUR, trois dents par vantail.
#: ⚠️ COMPTE IMPAIR, ET C'EST LE MIROIR QUI L'EXIGE. Le yaw de pi envoie la bande
#: k sur la bande 5-k : {0,2,4} revient en {5,3,1}, le complementaire exact. Une
#: dent tombe donc toujours en face d'une mortaise. Avec quatre dents (huit
#: bandes) la meme regle donnerait {0,2,4,6} -> {7,5,3,1} : cela marcherait aussi,
#: mais 0,15 m de dent ne portent plus d'ombre a 23 px/m. Trois, donc.
TOOTH_BANDS = 6
TOOTH_MINE = (0, 2, 4)
TOOTH_LEN = 1.25            # la dent avance de x = 0 a x = 1,25
TOOTH_ROOT_X = 1.10         # la ou le tableau reprend sa pleine hauteur
TOOTH_BED_Y = 3.00          # le LIT : fond des mortaises. Plein en dessous —
                            # une mortaise traversante serait un jour.
TOOTH_ROOT_Y = 2.90         # la dent plonge de 10 cm DANS le lit
#: ⚠️ LA DENT S'ARRETE 7 cm AVANT LE PLAN DE JOINT, ET C'EST LA LIGNE DE REFEND.
#: Porte fermee, les deux retraits font au MILIEU EXACT une gorge transversale de
#: 0,14 m de large et 0,60 m de creux qui traverse toute l'epaisseur — un trait
#: NOIR, franc, perpendiculaire a la porte. C'est le seul signal qui dise « ici »
#: plutot que « quelque chose est pose la » : sans lui, la machoire se lisait
#: comme UN bloc clair au centre (premier tirage de la planche), et non comme
#: deux peignes qui se rejoignent. La butee, elle, reste pleine : ce sont les
#: CORPS des deux vantaux qui se touchent a x = 0, pas les dents.
TOOTH_TIP_GAP = 0.07

# ==========================================================================
# LE LOGEMENT — un FOURREAU, donc un U et non une boite
# ==========================================================================
#: Il chevauche le vantail ferme de 0,20 m (12,70 contre 12,90) : c'est ce
#: recouvrement, et rien d'autre, qui interdit un jour au bout de la porte.
HOUSING_X = (12.70, DOOR_HALF_X)
HOUSING_HALF_S = 0.80
HOUSING_H = 3.90
#: LE JEU MECANIQUE, 2 cm sur chaque axe. Les joues laissent passer un vantail de
#: 0,60 ; la sole s'arrete 2 cm sous son assise. Un fourreau qui affleurerait sa
#: piece donnerait deux faces COPLANAIRES entre deux nœuds — et le moteur les
#: fait glisser l'une sur l'autre.
HOUSING_CHEEK_IN = 0.62
HOUSING_SILL_Y = 0.28
#: L'EMBOUCHURE : la joue fait 0,80 sur ses 60 premiers centimetres puis
#: s'amincit a 0,74. Le collier qui en resulte est le seul endroit ou le logement
#: touche l'emprise du brief, et il DIT ou le vantail disparait.
HOUSING_MOUTH_X = 13.30
HOUSING_MOUTH_RAMP = 0.20
HOUSING_CHEEK_OUT = 0.74
HOUSING_CAP_Y = 3.72        # depart du chanfrein de couronnement de la joue
HOUSING_CAP_IN = 0.10
#: Deux cerces par joue : elles debordent de 6 cm, donc elles portent une ombre.
HOUSING_RIBS = (14.60, 16.10)
HOUSING_RIB_HALF_X = 0.16
HOUSING_RIB_IN = 0.68
HOUSING_RIB_Y = 3.60


# ==========================================================================
# LE PORTIQUE — le porte-a-faux, un defaut mesure a corriger
# ==========================================================================
# Vu en capture le 2026-09-04 : « les deux tiers exterieurs de la poutre
# surplombent le vide, etoiles visibles dessous ». Ce n'est pas rattrapable en
# raccourcissant la porte — elle doit couvrir tout le plan de vol.
PYLON_X0 = 15.60
PYLON_X1 = DOOR_HALF_X
PYLON_HALF_S = 0.90
PYLON_LEG_HALF_S = 0.24     # deux jambes, de part et d'autre de la poutre
PYLON_LEG_S = 0.66          # ecart des jambes a l'axe de la poutre
PYLON_H = 3.60
PYLON_HEAD_Y = 3.06         # le chapiteau qui relie les deux jambes
#: LE TALON. Il va CHERCHER la coque : voir les deux ecarts, en tete de fichier.
#: ⚠️ 13,58 ET NON 13,75, ET LA DIFFERENCE EST UNE MESURE. Le flanc de la coque
#: n'est pas vertical : entre Y = -7,65 et Y = -6,35 il rentre de 0,53 m vers
#: l'axe. Au HAUT du talon (Y ~ -6,93) la lisse est donc a 13,75 apres taper —
#: c'est-a-dire exactement a la pointe : le portique effleurait la coque au lieu
#: de s'y appuyer, et `_pylon_bite()` l'a chiffre a 0,002 m. La pointe descend
#: donc de 17 cm : la morsure est de 0,17 a 0,56 m sur toute la hauteur d'appui.
PYLON_HEEL_X = 13.58
PYLON_HEEL_Y0 = 0.12
PYLON_HEEL_Y1 = 1.18
PYLON_HEEL_HALF_S = 0.74
#: La plage de hauteur de la POINTE (et non du talon entier) : c'est elle, et
#: elle seule, qui doit mordre le flanc.
PYLON_HEEL_TIP_Y = (0.30, 0.72)

# ==========================================================================
# LE BASTION — la MASSE ETAGEE
# ==========================================================================
BASTION_X = (6.90, 11.40)
BASTION_S = (-0.40, 6.00)
BASTION_H = 2.90
BASTION_CHAMFER = 0.40
#: LES GORGES : deux creux horizontaux qui font le tour. Un creux porte une ombre
#: qui survit au downscale, une gravure non (mesure de BRIEF-0093).
BASTION_GROOVES = ((1.32, 1.60), (2.14, 2.34))
BASTION_GROOVE_IN = 0.16
#: Le fruit : la masse se retreint en montant. C'est ce qui la fait peser.
BASTION_BATTER = 0.22
#: Le chanfrein de couronnement, sur les quatre aretes hautes.
BASTION_CAP_IN = 0.34
BASTION_CAP_Y = 0.44

# ==========================================================================
# LA COURONNE — le second etage, et lui seul
# ==========================================================================
CROWN_X = (7.40, 10.00)
CROWN_S = (1.60, 5.40)
CROWN_H = 0.60
CROWN_SLAB_Y = 0.30
CROWN_CHAMFER = 0.30
CROWN_MERLONS = 4
CROWN_MERLON_S = 0.52
CROWN_MERLON_IN = 0.24      # les merlons sont en retrait de la dalle

# ==========================================================================
# LE RELAIS — le BRANCHEMENT (destructible)
# ==========================================================================
RELAY_X = 6.20
RELAY_HALF = 0.80           # emprise : x +/- 0,80 autour de 6,20
RELAY_H = 1.90
#: Le COLLIER, a mi-hauteur : c'est lui le signal de branchement. Il DEBORDE le
#: fut de 0,18 m, sans quoi il ne porte pas d'ombre.
RELAY_COLLAR_Y = (0.80, 1.10)
RELAY_BODY_HALF = 0.62
#: La lampe. ⚠️ ELLE REGARDE LA CAMERA, ET C'EST UNE MESURE. La camera plonge a
#: 70 deg, donc a 20 deg de la verticale : un flanc lumineux, meme evase, lui est
#: presente presque de profil et ne rend quasiment aucun pixel. C'est le defaut
#: qui a coute une couronne au nœud d'epine (BRIEF-0094). L'emissif du relais est
#: donc un ANNEAU QUASI-HORIZONTAL, coiffe d'un capot sombre qui l'empeche de
#: baver sur toute la piece.
RELAY_LAMP_Y = (1.50, 1.66)
RELAY_CAP_HALF = 0.34

# ==========================================================================
# LE CONDUIT — la piece la plus importante du brief
# ==========================================================================
CONDUIT_X = (1.20, 5.40)    # du pied du relais au rebord de l'artere
CONDUIT_HALF_S = 0.32
CONDUIT_TOP_Y = 0.58        # dessus HORIZONTAL — voir les deux ecarts
#: ⚠️ CES DEUX ABSCISSES SONT CELLES DU TALUS REEL, PAS UN CHOIX DE DESSIN. Le
#: profil de la coque monte du pont interieur (-4,30) au rebord de l'artere
#: (-4,02) entre x = 2,28 et x = 1,76 a la station du conduit — points 4, 5 et 6
#: de `PROFILE_BASE`, mis a l'echelle du troncon 3. Un talus dessine ailleurs
#: ferait FLOTTER le caisson d'une dizaine de centimetres sur un demi-metre, et
#: rien ne le dirait : `_conduit_ground()` mesure l'ecart sur la peau et le
#: compte-rendu le donne.
CONDUIT_RISE_X = (1.66, 2.44)
CONDUIT_RISE_Y = 0.28       # ce que la peau monte entre x 5,40 et x 1,20
CONDUIT_COLLARS = (2.30, 3.45, 4.60)
CONDUIT_COLLAR_HALF_X = 0.17
CONDUIT_COLLAR_HALF_S = 0.44
CONDUIT_COLLAR_TOP = 0.62

# ==========================================================================
# LE NOYAU — la REVOLUTION (destructible), le point le plus haut
# ==========================================================================
CORE_SEG = 16
CORE_H = 2.18
CORE_MAX_R = 1.20           # brief : rayon <= 1,30
#: (y, rayon) — le profil du tambour. L'emissif est la ceinture ET son anneau
#: quasi-horizontal, meme raison que pour le relais.
CORE_PROFILE: tuple[tuple[float, float], ...] = (
    (0.00, 1.02), (0.24, 1.20), (0.66, 1.08), (0.90, 0.86),
    (1.04, 0.92), (1.24, 1.08), (1.32, 1.20), (1.40, 1.00),
    (1.62, 0.90), (1.94, 0.62), (2.18, 0.28),
)
#: Les bandes emissives, par indice de segment du profil ci-dessus.
CORE_EMISSIVE_BANDS = (4, 5, 6)

# ==========================================================================
# LE BOUCLIER — un panneau, et le seul `AA_Glass` du kit
# ==========================================================================
SHIELD_HALF_X = 1.80
SHIELD_HALF_Y = 1.50
SHIELD_HALF_S = 0.12
SHIELD_BOW = 0.07           # il est BOMBE vers la proue, donc vers le joueur
SHIELD_RAIL_Y = 0.16        # les rails d'emission, en haut et en bas


# ==========================================================================
# Primitives — bobinage CALCULE, jamais suppose
# ==========================================================================


def _new_object(name: str, bm: bmesh.types.BMesh) -> bpy.types.Object:
    """Objet a 7 slots normalises, SANS `recalc_face_normals`.

    Meme raison que sur la coque et sur les trois autres kits : l'heuristique de
    bmesh peut retourner une piece entiere, et une piece retournee DISPARAIT en
    jeu (culling arriere) sans qu'aucune bbox, aucun compte de triangles ni
    aucune mesure d'UV ne le voie.
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


def _face_facing(bm: bmesh.types.BMesh, verts: list, material: str,
                 want: Vector):
    """Une face dont la normale part du cote `want`. DETERMINISTE.

    Le bobinage est CALCULE et non ecrit a la main : la poutre a un rentrant, le
    bastion a un fruit, le noyau a une ceinture evasee, le talon du portique est
    un coin — une regle ecrite serait fausse une fois sur deux, et une face
    retournee ne se voit sur AUCUNE mesure.
    """
    ring = list(verts)
    normal = (ring[1].co - ring[0].co).cross(ring[2].co - ring[0].co)
    if normal.dot(want) < 0.0:
        ring.reverse()
    return _face(bm, ring, material)


def _key(v) -> tuple:
    return (round(v.co.x, 6), round(v.co.y, 6), round(v.co.z, 6))


def _newell(verts: list) -> Vector:
    """Normale de Newell (non normalisee) : sa longueur vaut deux fois l'aire.

    Robuste sur un polygone quelconque, la ou `(v1-v0) x (v2-v0)` rend zero des
    que les trois premiers sommets sont alignes — cas courant sur une marche.
    """
    normal = Vector((0.0, 0.0, 0.0))
    count = len(verts)
    for i in range(count):
        a = verts[i].co
        b = verts[(i + 1) % count].co
        normal.x += (a.y - b.y) * (a.z + b.z)
        normal.y += (a.z - b.z) * (a.x + b.x)
        normal.z += (a.x - b.x) * (a.y + b.y)
    return normal * 0.5


def _loft(bm: bmesh.types.BMesh, rings: list[list[Vector]],
          materials: list, cap_low: str | None, cap_high: str | None,
          axis: int = 1, axial: list | None = None) -> list[list]:
    """Empile des anneaux fermes et les relie. Rend les anneaux de sommets.

    `rings` : des polygones CONVEXES, meme nombre de points, ordonnes autour de
    l'axe. `materials[i]` : le materiau de la bande `i -> i+1`, soit un nom, soit
    une liste d'un nom par arete de section.

    ⚠️ `axial[i]` EXISTE PARCE QU'UNE MARCHE N'A PAS DE NORMALE RADIALE, ET C'EST
    LE PIEGE DE CETTE FAMILLE DE PIECES. Deux anneaux poses a la MEME cote d'axe
    (le rentrant de la poutre, le lit de denture, la gorge du bastion, le
    dessous de collier du relais) forment une couronne dont la normale est
    PARALLELE a l'axe : le `want` radial y est orthogonal a la vraie normale, le
    produit scalaire vaut zero a l'epsilon pres, et le bobinage se decide alors
    au hasard des arrondis. On le DIT donc : +1 la couronne regarde vers +axe,
    -1 vers -axe. `_assert_solid()` verifie ensuite qu'on ne s'est pas trompe.

    Les quads DEGENERES sont ecartes : sur une marche, la moitie des points ne
    bougent pas, et une facette d'aire nulle soudee par `remove_doubles` laisse
    derriere elle une arete a trois faces.
    """
    verts: list[list] = []
    for ring in rings:
        verts.append([bm.verts.new(Vector(p)) for p in ring])
    unit = Vector((1.0 if axis == 0 else 0.0, 1.0 if axis == 1 else 0.0,
                   1.0 if axis == 2 else 0.0))
    for i in range(len(verts) - 1):
        low, high = verts[i], verts[i + 1]
        centre = (sum((v.co for v in low), Vector()) / len(low)
                  + sum((v.co for v in high), Vector()) / len(high)) * 0.5
        band = materials[i]
        hint = None if axial is None else axial[i]
        for k in range(len(low)):
            m = (k + 1) % len(low)
            quad = [low[k], low[m], high[m], high[k]]
            unique: list = []
            for v in quad:
                if not any(_key(v) == _key(u) for u in unique):
                    unique.append(v)
            if len(unique) < 3:
                continue
            material = band if isinstance(band, str) else band[k]
            # ⚠️ LA FACETTE D'AIRE NULLE EST ECARTEE ICI, ET C'EST INDISPENSABLE.
            # Sur une marche, trois des quatre sommets peuvent etre ALIGNES (le
            # flanc d'une dent, dont seul le sommet change) : `faces.new()`
            # accepte le triangle plat, la normale est nulle, le bobinage se
            # decide donc au hasard — et mikktspace produit ensuite une tangente
            # de rattrapage qui casse la byte-identite d'un build a l'autre.
            normal = _newell(unique)
            if normal.length < 2e-9:
                continue
            # ⚠️ ET LE `want` AXIAL NE VAUT QUE POUR LES FACETTES REELLEMENT
            # AXIALES. Sur la marche d'un contrefort, la bande du BAS et celle du
            # HAUT sont couchees dans un plan y = cte : leur normale est
            # verticale, orthogonale a l'axe qu'on leur imposait. Le produit
            # scalaire valait zero, le bobinage tombait a pile ou face, et le
            # controle de solidite rapportait 104 aretes retournees a l'endroit
            # exact ou la geometrie etait juste.
            if hint is not None and abs(normal.normalized()[axis]) > 0.9:
                want = unit * float(hint)
            else:
                mid = (low[k].co + low[m].co + high[m].co + high[k].co) * 0.25
                want = mid - centre
                want[axis] = 0.0
                if want.length < 1e-9:
                    want = unit
            # ⚠️ ON EMET `unique` ET NON `quad`. Sur une marche, deux sommets du
            # quad sont CONFONDUS sans etre le meme objet : `bmesh.faces.new()`
            # les accepte, fabrique une arete de longueur nulle, et le soudage
            # laisse derriere lui une face a sommet double — que le controle de
            # solidite rapporte comme 104 aretes RETOURNEES, ce qui envoie
            # chercher le defaut a l'exact oppose de la ou il est.
            _face_facing(bm, unique, material, want)
    # ⚠️ LE SENS DE L'EMPILEMENT EST MESURE, PAS SUPPOSE. Deux pieces de ce kit
    # se construisent en DESCENDANT leur axe (le talon du portique part de la
    # jambe et va vers la coque, le conduit part du relais et va vers l'axe).
    # Supposer l'ordre croissant retourne LES DEUX BOUCHONS de ces pieces — et
    # une piece retournee disparait en jeu sans qu'aucune bbox ne le voie.
    along = 1.0 if verts[-1][0].co[axis] >= verts[0][0].co[axis] else -1.0
    if cap_low is not None:
        _face_facing(bm, verts[0], cap_low, -unit * along)
    if cap_high is not None:
        _face_facing(bm, verts[-1], cap_high, unit * along)
    return verts


def _octagon(cu: float, cv: float, hu: float, hv: float,
             chamfer: float) -> list[tuple[float, float]]:
    """Rectangle a quatre angles coupes, dans un plan, sens direct."""
    c = min(chamfer, min(hu, hv) * 0.9)
    return [(cu + hu - c, cv + hv), (cu + hu, cv + hv - c),
            (cu + hu, cv - hv + c), (cu + hu - c, cv - hv),
            (cu - hu + c, cv - hv), (cu - hu, cv - hv + c),
            (cu - hu, cv + hv - c), (cu - hu + c, cv + hv)]


def _rect(cu: float, cv: float, hu: float, hv: float) -> list[tuple[float, float]]:
    return [(cu + hu, cv + hv), (cu + hu, cv - hv),
            (cu - hu, cv - hv), (cu - hu, cv + hv)]


def _regular(radius: float, segments: int) -> list[tuple[float, float]]:
    """Polygone regulier dont la DEMI-LARGEUR vaut `radius` : c'est la cote qui
    se mesure sur la bbox, donc la seule qui doive etre juste au harnais."""
    circum = radius / math.cos(math.pi / segments)
    return [(circum * math.sin(2.0 * math.pi * (k + 0.5) / segments),
             circum * math.cos(2.0 * math.pi * (k + 0.5) / segments))
            for k in range(segments)]


def _ring_y(y: float, points: list[tuple[float, float]]) -> list[Vector]:
    """Un anneau horizontal : les points sont des (x, z)."""
    return [Vector((x, y, z)) for x, z in points]


def _ring_x(x: float, points: list[tuple[float, float]]) -> list[Vector]:
    """Un anneau transversal : les points sont des (z, y)."""
    return [Vector((x, y, z)) for z, y in points]


def _box(bm: bmesh.types.BMesh, x0: float, x1: float, y0: float, y1: float,
         z0: float, z1: float, side: str, top: str,
         bottom: str | None = None) -> None:
    """Un pave droit, coque fermee a part entiere."""
    _loft(bm, [_ring_y(y0, _rect((x0 + x1) * 0.5, (z0 + z1) * 0.5,
                                 (x1 - x0) * 0.5, (z1 - z0) * 0.5)),
               _ring_y(y1, _rect((x0 + x1) * 0.5, (z0 + z1) * 0.5,
                                 (x1 - x0) * 0.5, (z1 - z0) * 0.5))],
          [side], cap_low=bottom or side, cap_high=top, axis=1)


# ==========================================================================
# LE VANTAIL — la MOITIE de la porte, et sa MACHOIRE
# ==========================================================================

_HULL = "AA_Hull"
_GREEBLE = "AA_Greeble"
_TRIM = "AA_Trim"
_EMISSIVE = "AA_Emissive_Engine"
_GLASS = "AA_Glass"

#: Les dix aretes de la section de vantail, et leur materiau. `AA_Trim` n'y est
#: PAS : 12,90 m de lisere ivoire suivant une arete CONTINUE occupent plus de
#: pixels que n'importe quelle piece du niveau (lecon de BRIEF-0089, payee deux
#: fois : l'ivoire du borde, puis le violet des facettes). Le trim du verrou est
#: reserve aux DENTS, ou il DIT quelque chose.
_LEAF_BAND = [_GREEBLE, _HULL, _GREEBLE, _HULL, _HULL,
              _HULL, _HULL, _HULL, _GREEBLE, _HULL]
#: Le TABLEAU porte en plus ses deux chanfreins de couronnement en `AA_Greeble` :
#: sous une lumiere qui vient d'en haut, ce sont eux qui dessinent le cadre du
#: joint. Une bande sombre de 0,14 m survit au downscale, une gravure non
#: (mesure de BRIEF-0093).
_JAMB_BAND = [_GREEBLE, _HULL, _GREEBLE, _HULL, _GREEBLE,
              _HULL, _GREEBLE, _HULL, _GREEBLE, _HULL]


def _leaf_section(hs: float, hs_top: float, hs_cap: float, coping: float,
                  top: float) -> list[tuple[float, float]]:
    """La section du vantail, en (z, y). DIX points, toujours les memes.

    ⚠️ LE NOMBRE DE POINTS EST UNE CONTRAINTE, PAS UNE COMMODITE : un loft ne
    relie que des anneaux de meme cardinal. C'est elle qui donne sa forme au
    TABLEAU — on ne peut pas « ajouter » un volume au bout de la poutre, on ne
    peut qu'ecarter les memes dix cotes. Il se trouve que c'est le bon dessin :
    le tableau est la MEME poutre, moins amincie.
    """
    return [(-hs, 0.0), (hs, 0.0), (hs, LEAF_SILL_Y), (hs_top, LEAF_STEP_Y),
            (hs_top, coping), (hs_cap, top), (-hs_cap, top),
            (-hs_top, coping), (-hs_top, LEAF_STEP_Y), (-hs, LEAF_SILL_Y)]


def _tooth_band(k: int) -> tuple[float, float]:
    """Les bornes en `s` de la bande `k`, sur les six de l'epaisseur."""
    width = 2.0 * LEAF_HALF_S / TOOTH_BANDS
    return (-LEAF_HALF_S + k * width, -LEAF_HALF_S + (k + 1) * width)


def build_leaf() -> bpy.types.Object:
    """Le vantail : une poutre de 12,90 m, un tableau, et trois dents.

    ⚠️ SON ORIGINE EST SON BOUT INTERIEUR (x = 0), PAS SON CENTRE. C'est ce qui
    permet au moteur d'ecrire la course comme une simple translation en x — 0
    ferme, 4,25 ouvert — la meme des deux cotes, le yaw de pi faisant le reste.
    Sa boite reste centree en `s` (+/- 0,60), ce qui est la seule chose dont le
    miroir ait besoin.

    ⚠️ ET LA FACE DE BUTEE EST PLEINE ET PLANE. La demonstration est dans
    l'en-tete : une denture qui se recouvrirait vraiment forcerait le vantail a
    franchir l'axe de la moitie de sa saillie, donc a manger la passe et a sortir
    de son emprise. Le tenon d'un vantail ferme la mortaise de l'autre ; les deux
    series s'engrenent A L'ŒIL — la phase du motif s'inverse en franchissant
    x = 0 — sans qu'un metre cube ne se chevauche. `_seam_report()` le mesure au
    lancer de rayons, dans les deux directions, sur le binaire livre.

    Quatre coques : le corps et ses TROIS dents. Une dent separee, enfoncee de
    10 cm dans le lit, n'a ni marche ni jonction en T — la lecon de la denture du
    LOT 2, qui avait coute 63 aretes de bord avant d'etre payee.
    """
    bm = bmesh.new()
    beam = (LEAF_HALF_S, LEAF_HALF_S_TOP, LEAF_HALF_S_CAP, LEAF_COPING_Y,
            LEAF_H)
    jamb = (LEAF_HALF_S, JAMB_HALF_S_TOP, JAMB_HALF_S_CAP, JAMB_COPING_Y,
            LEAF_H)
    bed = (LEAF_HALF_S, JAMB_HALF_S_TOP, JAMB_HALF_S_CAP,
           TOOTH_BED_Y - 0.14, TOOTH_BED_Y)
    # ⚠️ LE REFEND NE MORD QUE LE HAUT DE LA SECTION, ET C'EST MESURE. Applique
    # aussi au pied (hs), il ouvrait sous la porte fermee une encoche de
    # 0,10 x 0,05 m par flanc — traversante, donc un JOUR, que `_seam_report()`
    # a rapportee au premier tirage. Il ne rentre donc qu'au-dessus de la lisse
    # (2,34), la ou la camera voit quelque chose de toute façon.
    reveal = (bed[0], bed[1] - REVEAL_IN, bed[2] - REVEAL_IN, bed[3], bed[4])
    # ⚠️ AUCUNE MARCHE DANS CE PLAN, QUE DES RAMPES DE 0,20 m. Sur une marche —
    # deux anneaux a la meme abscisse — les points qui ne bougent pas fabriquent
    # une facette d'aire nulle : la supprimer ouvre une jonction en T, la garder
    # donne une tangente de rattrapage qui casse la byte-identite d'un build a
    # l'autre. A 23 px/m une rampe de 20 cm se lit comme une marche.
    plan: list[tuple[float, tuple]] = [
        (0.00, reveal),                     # le refend
        (REVEAL_X, bed),
        (TOOTH_ROOT_X, bed),                # le lit de machoire
        (TOOTH_ROOT_X + JAMB_RAMP, jamb),
        (JAMB_X, jamb),                     # le tableau
        (JAMB_X + JAMB_RAMP, beam),
        (LEAF_LEN, beam),                   # la poutre
    ]
    rings = [_ring_x(x, _leaf_section(*sec)) for x, sec in plan]
    bands = [_JAMB_BAND, _JAMB_BAND, _JAMB_BAND, _JAMB_BAND, _LEAF_BAND,
             _LEAF_BAND]
    _loft(bm, rings, bands, cap_low=_HULL, cap_high=_HULL, axis=0)
    for k in TOOTH_MINE:
        z0, z1 = _tooth_band(k)
        _box(bm, TOOTH_TIP_GAP, TOOTH_LEN, TOOTH_ROOT_Y, LEAF_H, z0, z1,
             _GREEBLE, _TRIM, _GREEBLE)
    return _new_object("citadel_leaf", bm)


# ==========================================================================
# LE LOGEMENT — le FOURREAU
# ==========================================================================

#: Les cinq aretes de la section de joue : dessous, flanc exterieur, chanfrein de
#: couronnement, dessus, flanc INTERIEUR (celui qui guide le vantail).
_CHEEK_BAND = [_GREEBLE, _HULL, _GREEBLE, _HULL, _GREEBLE]


def _cheek_section(side: float, outer: float) -> list[tuple[float, float]]:
    """La section d'une joue, en (z, y). Cinq points.

    Elle est ETOILEE autour de son propre centre — c'est ce que `_loft` demande
    pour decider le bobinage, et non la convexite. Un fruit a redent (epaisse en
    bas, mince en haut, avec une marche) rendrait un produit scalaire nul sur le
    flanc et le bobinage tomberait a pile ou face.
    """
    return [(side * HOUSING_CHEEK_IN, 0.0), (side * outer, 0.0),
            (side * outer, HOUSING_CAP_Y),
            (side * (outer - HOUSING_CAP_IN), HOUSING_H),
            (side * HOUSING_CHEEK_IN, HOUSING_H)]


def build_housing() -> bpy.types.Object:
    """Deux joues, quatre cerces, une sole — et RIEN au-dessus du vantail.

    ⚠️ C'EST UN U ET NON UNE BOITE, ET LA COTE L'IMPOSE. Le sommet du vantail est
    DEJA au plafond du decor inerte (-3,00) : il ne reste pas un centimetre pour
    un couvercle. C'est pour cela que le fourreau descend au lieu de monter —
    assise -6,90 contre -6,60 — et c'est ce qui rend le mecanisme LISIBLE : porte
    fermee, le U montre une fente sombre de 1,24 m de large et 4,30 m de long a
    chaque bout de la porte ; porte ouverte, le vantail la remplit. La fente est
    l'explication du mecanisme, et elle ne coute pas un triangle.

    Sept coques : deux joues, quatre cerces, une sole. La sole PENETRE les joues
    de 4 cm et s'arrete 4 cm en deca des bouts : deux volumes qui s'affleurent
    partagent des sommets, `remove_doubles` les soude, et l'arete commune porte
    alors quatre faces — plus rien n'est prouvable sur la piece (lecon du
    chapiteau de portique, BRIEF-0096).
    """
    bm = bmesh.new()
    plan = ((HOUSING_X[0], HOUSING_HALF_S),
            (HOUSING_MOUTH_X, HOUSING_HALF_S),
            (HOUSING_MOUTH_X + HOUSING_MOUTH_RAMP, HOUSING_CHEEK_OUT),
            (HOUSING_X[1], HOUSING_CHEEK_OUT))
    for side in (-1.0, 1.0):
        rings = [_ring_x(x, _cheek_section(side, outer)) for x, outer in plan]
        _loft(bm, rings, [_CHEEK_BAND] * (len(plan) - 1), cap_low=_GREEBLE,
              cap_high=_GREEBLE, axis=0)
        lo = min(side * HOUSING_RIB_IN, side * HOUSING_HALF_S)
        hi = max(side * HOUSING_RIB_IN, side * HOUSING_HALF_S)
        for cx in HOUSING_RIBS:
            _box(bm, cx - HOUSING_RIB_HALF_X, cx + HOUSING_RIB_HALF_X,
                 0.0, HOUSING_RIB_Y, lo, hi, _GREEBLE, _GREEBLE, _GREEBLE)
    _box(bm, HOUSING_X[0] + 0.04, HOUSING_X[1] - 0.04, 0.0, HOUSING_SILL_Y,
         -HOUSING_CHEEK_IN - 0.04, HOUSING_CHEEK_IN + 0.04,
         _GREEBLE, _GREEBLE, _GREEBLE)
    return _new_object("citadel_housing", bm)


# ==========================================================================
# LE PORTIQUE — il rend le surplomb VOULU
# ==========================================================================


def build_pylon() -> bpy.types.Object:
    """Deux jambes qui enserrent le bout de poutre, un chapiteau, un TALON.

    ⚠️ LE TALON VA CHERCHER LA COQUE, ET C'EST L'UN DES DEUX ECARTS ASSUMES AU
    TABLEAU DU BRIEF (voir l'en-tete). Le tableau donne au portique « x 15,60 a
    17,20 » ; la meme page lui demande « de venir s'appuyer sur la lisse d'epaule
    (x ~ 13,88, Y ~ -7,65) ». La lisse est INBOARD de l'emprise : les deux
    enonces ne peuvent pas etre vrais ensemble. Un portique arrete a 15,60
    flotterait au-dessus du vide — le defaut meme qu'il existe pour corriger, et
    « un mur invisible est la meme injustice qu'une tourelle qu'on croit pouvoir
    raser et qui traverse ». Le talon descend donc a x = 13,75, et sa penetration
    dans le bordé est MESUREE contre le profil reel au harnais, taper du troncon
    3 compris.
    """
    bm = bmesh.new()
    for side in (-1.0, 1.0):
        cz = side * PYLON_LEG_S
        plan = ((0.00, PYLON_X0 - 0.08, 0.24), (0.55, PYLON_X0, 0.22),
                (PYLON_HEAD_Y, PYLON_X0 + 0.06, 0.20), (PYLON_H, PYLON_X0, 0.24))
        rings = [_ring_y(y, _rect((x0 + PYLON_X1) * 0.5, cz,
                                  (PYLON_X1 - x0) * 0.5, hs))
                 for y, x0, hs in plan]
        _loft(bm, rings, [_HULL, _HULL, _HULL], cap_low=_GREEBLE,
              cap_high=_HULL, axis=1)
    # Le chapiteau : il relie les deux jambes par-dessus la poutre.
    # ⚠️ IL EST STRICTEMENT PLUS PETIT QUE L'ENVELOPPE DES JAMBES, ET C'EST
    # STRUCTUREL. Cale sur les memes plans (x 15,60 / 17,20, z +/- 0,90,
    # y 3,60), il partageait quatre faces avec elles ; `remove_doubles` soudait
    # les sommets et l'arete commune portait quatre faces — non manifold, donc
    # rien de prouvable sur la piece. Deux coques qui s'interpenetrent doivent
    # se CHEVAUCHER, jamais s'affleurer.
    _box(bm, PYLON_X0 + 0.04, PYLON_X1 - 0.04, PYLON_HEAD_Y - 0.06,
         PYLON_H - 0.06, -PYLON_HALF_S + 0.06, PYLON_HALF_S - 0.06,
         _HULL, _HULL, _GREEBLE)
    # Le talon, en coin : large contre la jambe, mince contre la coque.
    heel = ((PYLON_HEEL_X, 0.38, PYLON_HEEL_TIP_Y[0], PYLON_HEEL_TIP_Y[1]),
            (15.00, 0.60, 0.16, 0.96),
            (16.20, PYLON_HEEL_HALF_S, PYLON_HEEL_Y0, PYLON_HEEL_Y1))
    rings = [_ring_x(x, _rect(0.0, (y0 + y1) * 0.5, hs, (y1 - y0) * 0.5))
             for x, hs, y0, y1 in heel]
    _loft(bm, rings, [_GREEBLE, _GREEBLE], cap_low=_GREEBLE, cap_high=_GREEBLE,
          axis=0)
    return _new_object("citadel_pylon", bm)


# ==========================================================================
# LE BASTION — la MASSE ETAGEE
# ==========================================================================


def build_bastion() -> bpy.types.Object:
    """Une masse a fruit, chanfreinee, gorgee a mi-hauteur.

    ⚠️ PLUS LARGE QUE HAUT, ET C'EST LA REGLE QUI LE SEPARE DE L'AFFUT. 4,50 m
    d'emprise laterale pour 2,90 m de haut : le harnais mesure le rapport sur le
    binaire et echoue s'il s'inverse. Un bastion plus haut que large ne serait
    plus une masse, ce serait un affut geant — et le niveau en porte deja
    trente-huit.

    Rien de vertical, rien d'oblique : le fruit et les chanfreins sont la pente
    de la masse elle-meme, pas des elements ajoutes. Les diagonales appartiennent
    au nœud d'epine, les tubes a l'affut.
    """
    bm = bmesh.new()
    cx = (BASTION_X[0] + BASTION_X[1]) * 0.5
    hx = (BASTION_X[1] - BASTION_X[0]) * 0.5
    hz = (BASTION_S[1] - BASTION_S[0]) * 0.5
    inn = BASTION_GROOVE_IN
    b = BASTION_BATTER
    plan: list[tuple[float, float, float, float, int | None, str]] = [
        # (y, retrait_x, retrait_z, chanfrein, axial de la bande qui FINIT ici,
        #  materiau de cette bande)
        (0.00, 0.00, 0.00, BASTION_CHAMFER, None, ""),
    ]
    # ⚠️ DEUX GORGES ET NON UNE, ET C'EST LE TEST D'ACCEPTATION QUI LES DEMANDE.
    # « Masse ETAGEE » ne se lit pas d'un bloc lisse : ce qui fait l'etage est une
    # ligne horizontale, et il en faut plus d'une pour qu'on lise un rythme
    # plutot qu'un accident. Un creux porte une ombre qui survit au downscale ;
    # une gravure, non (mesure de BRIEF-0093).
    for k, (g0, g1) in enumerate(BASTION_GROOVES):
        share = 0.30 + 0.20 * k
        plan.append((g0, b * share, b * share, BASTION_CHAMFER + 0.04, None,
                     _HULL))
        plan.append((g0, inn, inn, BASTION_CHAMFER + 0.04, 1, _GREEBLE))
        plan.append((g1, inn + 0.02, inn + 0.02, BASTION_CHAMFER + 0.04, None,
                     _GREEBLE))
        plan.append((g1, b * (share + 0.12), b * (share + 0.12),
                     BASTION_CHAMFER + 0.04, -1, _GREEBLE))
    plan.append((BASTION_H - BASTION_CAP_Y, b, b, BASTION_CHAMFER + 0.08, None,
                 _HULL))
    plan.append((BASTION_H, b + BASTION_CAP_IN, b + 0.20,
                 BASTION_CHAMFER + 0.22, None, _HULL))
    rings = [_ring_y(y, _octagon(cx, 0.0, hx - rx, hz - rz, ch))
             for y, rx, rz, ch, _a, _m in plan]
    bands = [row[5] for row in plan[1:]]
    axial = [row[4] for row in plan[1:]]
    _loft(bm, rings, bands, cap_low=_GREEBLE, cap_high=_HULL, axis=1,
          axial=axial)
    return _new_object("citadel_bastion", bm)


# ==========================================================================
# LA COURONNE — le second etage, et lui seul
# ==========================================================================


def build_crown() -> bpy.types.Object:
    """Une dalle chanfreinee et quatre merlons : le SECOND niveau.

    C'est elle qui fait de la citadelle le seul volume a deux etages du
    vaisseau, et donc la seule qui se lise « masse » en une seconde. Les merlons
    portent le seul `AA_Trim` de la piece : quatre traits clairs, transversaux,
    qui disent l'echelle sans une ligne continue.
    """
    bm = bmesh.new()
    cx = (CROWN_X[0] + CROWN_X[1]) * 0.5
    hx = (CROWN_X[1] - CROWN_X[0]) * 0.5
    hz = (CROWN_S[1] - CROWN_S[0]) * 0.5
    rings = [_ring_y(0.00, _octagon(cx, 0.0, hx, hz, CROWN_CHAMFER)),
             _ring_y(CROWN_SLAB_Y - 0.08,
                     _octagon(cx, 0.0, hx, hz, CROWN_CHAMFER)),
             _ring_y(CROWN_SLAB_Y,
                     _octagon(cx, 0.0, hx - 0.14, hz - 0.14,
                              CROWN_CHAMFER + 0.04))]
    _loft(bm, rings, [_HULL, _HULL], cap_low=_GREEBLE, cap_high=_HULL, axis=1)
    span = 2.0 * (hz - 0.24)
    pitch = span / CROWN_MERLONS
    for k in range(CROWN_MERLONS):
        cz = -span * 0.5 + pitch * (k + 0.5)
        hs = CROWN_MERLON_S * 0.5
        mx = hx - CROWN_MERLON_IN
        plan = ((CROWN_SLAB_Y - 0.08, mx, hs),
                (CROWN_H - 0.12, mx, hs),
                (CROWN_H, mx - 0.10, hs - 0.06))
        rings = [_ring_y(y, _rect(cx, cz, rx, rs)) for y, rx, rs in plan]
        _loft(bm, rings, [_HULL, _HULL], cap_low=_GREEBLE, cap_high=_TRIM,
              axis=1)
    return _new_object("citadel_crown", bm)


# ==========================================================================
# LE RELAIS — le BRANCHEMENT (destructible, donc emissif)
# ==========================================================================

#: (y, demi-largeur, chanfrein, marche de la bande QUI FINIT ICI, materiau de la
#: bande qui finit ici). Un seul tableau : la piece se relit d'un coup d'œil, et
#: le harnais mesure ce qu'il y a dedans.
_RELAY_PLAN: tuple[tuple[float, float, float, int | None, str | None], ...] = (
    (0.00, 0.72, 0.26, None, None),
    (0.16, 0.78, 0.28, None, "AA_Greeble"),      # la semelle
    (0.30, 0.66, 0.24, None, "AA_Greeble"),
    (0.80, 0.62, 0.22, None, "AA_Hull"),         # le fut
    (0.80, 0.80, 0.28, -1, "AA_Greeble"),        # DESSOUS du collier
    (1.10, 0.80, 0.28, None, "AA_Greeble"),      # le collier
    (1.10, 0.60, 0.22, 1, "AA_Greeble"),         # DESSUS du collier
    (1.44, 0.64, 0.22, None, "AA_Hull"),
    (1.50, 0.72, 0.26, None, "AA_Greeble"),
    (1.62, 0.74, 0.28, None, "AA_Emissive_Engine"),   # l'evasement de la lampe
    (1.66, 0.52, 0.20, None, "AA_Emissive_Engine"),   # L'ANNEAU quasi-horizontal
    (1.74, 0.44, 0.16, None, "AA_Greeble"),      # le capot, sombre
    (1.90, 0.34, 0.12, None, "AA_Greeble"),
)


def build_relay() -> bpy.types.Object:
    """Un fut PRISMATIQUE court, un collier qui deborde, une lampe coiffee.

    ⚠️ PRISMATIQUE, ET C'EST UNE CONTRAINTE, PAS UN GOUT. La REVOLUTION est la
    signature du noyau — le seul solide de revolution du verrou. Un relais en
    tambour et un noyau en tambour, ce sont deux pieces qu'on confond a 23 px/m,
    et le test d'acceptation demande de les distinguer SANS HESITATION. Le
    harnais mesure l'ecart a la circularite des deux sections et echoue si elles
    se rapprochent.

    ⚠️ L'EMISSIF EST ICI ET SUR LE NOYAU, NULLE PART AILLEURS. Le moteur detruit
    `citadel_relay` SEUL : un emissif sur la porte, un bastion ou une couronne
    resterait allume apres sa mort, et la regle « gauche + droite -> centre » ne
    se verrait plus. C'est le defaut que BRIEF-0094 a corrige sur les cinq bulbes
    de l'epine, et il n'est pas repaye ici.

    Et il REGARDE LA CAMERA : la lampe n'est pas un flanc lumineux mais un anneau
    quasi-horizontal de 22 cm de large (r 0,74 -> 0,52) coiffe d'un capot sombre.
    Sous une camera qui plonge a 70 deg, un flanc ne rend presque rien.
    """
    bm = bmesh.new()
    rings = [_ring_y(y, _octagon(RELAY_X, 0.0, h, h, ch))
             for y, h, ch, _a, _m in _RELAY_PLAN]
    bands = [row[4] for row in _RELAY_PLAN[1:]]
    axial = [row[3] for row in _RELAY_PLAN[1:]]
    # ⚠️ SON CAPOT EST SOMBRE, ET C'EST LE TEST D'ACCEPTATION QUI L'A DECIDE. Il
    # portait `AA_Trim` comme celui du noyau : au premier tirage de la planche,
    # en noir et blanc et emissifs coupes, les deux pieces se presentaient toutes
    # deux comme « un volume sombre coiffe d'une tache claire » — c'est-a-dire la
    # SEULE lecture que le brief interdit (« relais != noyau, sans hesitation »).
    # Le relais est desormais uniformement sombre, prismatique, tenu par l'ombre
    # de son collier ; le noyau reste rond et garde sa pointe claire. Les deux ne
    # partagent plus aucun signal.
    _loft(bm, rings, bands, cap_low=_GREEBLE, cap_high=_GREEBLE, axis=1,
          axial=axial)
    return _new_object("citadel_relay", bm)


# ==========================================================================
# LE CONDUIT — la piece la plus importante du brief
# ==========================================================================


def _conduit_floor(x: float) -> float:
    """Le dessous du conduit : il SUIT LE TERRAIN, le dessus reste horizontal.

    Entre le pied du relais (x 5,40, pont interieur a -4,30) et le rebord de
    l'artere (x 1,20, a -4,02), la peau MONTE de 0,28 m. Mesure sur
    `cortege._surface_y`, pas estimee : `_assert_conduit_clearance()`.
    """
    x0, x1 = CONDUIT_RISE_X
    if x >= x1:
        return 0.0
    if x <= x0:
        return CONDUIT_RISE_Y
    return CONDUIT_RISE_Y * (x1 - x) / (x1 - x0)


def _conduit_section(x: float) -> list[tuple[float, float]]:
    hs = CONDUIT_HALF_S
    yb = _conduit_floor(x)
    top = CONDUIT_TOP_Y
    return [(-hs, yb), (hs, yb), (hs, top - 0.10), (hs - 0.09, top),
            (-(hs - 0.09), top), (-hs, top - 0.10)]


def build_conduit() -> bpy.types.Object:
    """Un caisson bas, trois colliers, et il POINTE le centre.

    C'est lui qui dit « ceci alimente cela » EN GEOMETRIE — donc sans emissif,
    donc au test noir et blanc. Sa ligne de faite est HORIZONTALE et rectiligne
    sur 4,20 m, cap sur l'axe du vaisseau : c'est la seule chose du verrou qui
    aille d'une piece vers une autre.

    ⚠️ NI TUBE LONG, NI DIAGONALE : le nœud d'epine possede les deux (un fut
    effile et quatre entretoises a 24 deg). Un conduit cylindrique ou oblique
    serait un quatrieme axe qui retombe sur le troisieme. D'ou le caisson
    orthogonal a colliers — la plomberie, pas la charpente.

    Il s'arrete a x = 1,20, sur le REBORD de l'artere, et non sur le noyau : les
    quatre conduits lumineux du fond du canal prennent le relais sur les deux
    derniers metres. Le chemin complet se lit « relais -> caisson -> artere ->
    noyau », et le vaisseau en fournit deja le troisieme terme.
    """
    bm = bmesh.new()
    xs = (CONDUIT_X[0], CONDUIT_RISE_X[0], CONDUIT_RISE_X[1], CONDUIT_X[1])
    rings = [_ring_x(x, _conduit_section(x)) for x in xs]
    band = [_GREEBLE, _GREEBLE, _HULL, _HULL, _HULL, _GREEBLE]
    # Le bouchon interieur (x = 1,20, sur le rebord de l'artere) porte le seul
    # `AA_Trim` de la piece : c'est LA qu'elle passe la main aux conduits du fond
    # du canal, et c'est le seul endroit ou un lisere clair dit quelque chose.
    _loft(bm, rings, [band, band, band], cap_low=_TRIM, cap_high=_GREEBLE,
          axis=0)
    for cx in CONDUIT_COLLARS:
        _box(bm, cx - CONDUIT_COLLAR_HALF_X, cx + CONDUIT_COLLAR_HALF_X,
             0.0, CONDUIT_COLLAR_TOP,
             -CONDUIT_COLLAR_HALF_S, CONDUIT_COLLAR_HALF_S,
             _GREEBLE, _HULL, _GREEBLE)
    return _new_object("citadel_conduit", bm)


# ==========================================================================
# LE NOYAU — la REVOLUTION (destructible), le point le plus haut
# ==========================================================================


def build_core() -> bpy.types.Object:
    """Un tambour facette de revolution, ceinture d'emissif, coiffe sombre.

    ⚠️ C'EST LE SEUL SOLIDE DE REVOLUTION DE LA CITADELLE, ET C'EST TOUT LE
    PROPOS. Le reste du verrou est orthogonal — poutre, masses, caissons — donc
    un tambour y est immediatement AUTRE CHOSE, avant toute couleur et avant tout
    emissif. Le harnais mesure la circularite anneau par anneau (rayon max /
    rayon min <= 1,05, un 16-gone en rend 1,0196) et exige que le relais, lui,
    reste franchement non circulaire.

    ⚠️ ET IL EST LE POINT LE PLUS HAUT DU VERROU (-2,40, soit 60 cm au-dessus des
    couronnes et de la porte) PARCE QU'ON PEUT LE DETRUIRE. Le seul volume
    autorise a culminer est celui qu'on tire : c'est ce qui le designe comme le
    centre sans un mot de HUD, et c'est le harnais `_assert_core_culminates()`
    qui le tient, en composant les assises avec les hauteurs mesurees.
    """
    bm = bmesh.new()
    rings = [_ring_y(y, _regular(r, CORE_SEG)) for y, r in CORE_PROFILE]
    bands: list[str] = []
    for i in range(len(CORE_PROFILE) - 1):
        if i in CORE_EMISSIVE_BANDS:
            bands.append(_EMISSIVE)
        elif i in (0, 2, 3):
            bands.append(_GREEBLE)
        else:
            bands.append(_HULL)
    _loft(bm, rings, bands, cap_low=_GREEBLE, cap_high=_TRIM, axis=1)
    return _new_object("citadel_core", bm)


# ==========================================================================
# LE BOUCLIER — un panneau, et le seul `AA_Glass` du kit
# ==========================================================================


def build_shield() -> bpy.types.Object:
    """Un panneau lenticulaire, bombe vers la PROUE — donc vers le joueur.

    ⚠️ IL PORTE `AA_Glass` ET NON `AA_Shield_Field` : le materiau de champ et la
    mise en œuvre de `TEX-0015` appartiennent au LOT 3, le brief le dit en toutes
    lettres. Ce lot ne livre que la surface qui les recevra.

    Il est le seul nœud du kit dont l'origine soit CENTREE en Y (c'est un
    panneau, pas une piece posee), et le seul dont l'assise ne vienne pas du
    brief : voir `SHIELD_IS_DECIDED`.
    """
    bm = bmesh.new()
    lens = [(SHIELD_HALF_X, 0.0), (0.0, SHIELD_HALF_S),
            (-SHIELD_HALF_X, 0.0), (0.0, -SHIELD_HALF_S)]
    ys = (-SHIELD_HALF_Y, -SHIELD_HALF_Y + SHIELD_RAIL_Y,
          SHIELD_HALF_Y - SHIELD_RAIL_Y, SHIELD_HALF_Y)
    rings = [_ring_y(y, lens) for y in ys]
    _loft(bm, rings, [_GREEBLE, _GLASS, _GREEBLE], cap_low=_GREEBLE,
          cap_high=_GREEBLE, axis=1)
    return _new_object("citadel_shield", bm)


# ==========================================================================
# Harnais de scene (avant export)
# ==========================================================================

#: ⚠️ COMBIEN DE COQUES FERMEES PAR PIECE, ET C'EST UN CONTRAT. Un volume qui
#: apparait ou qui disparait est une faute de frappe qui ne se voit sur aucune
#: planche (precedent mesure au BRIEF-0093 : deux colliers de conduite fusionnes
#: en un seul, restes ainsi jusqu'a ce que ce compte soit ECRIT).
SHELL_COUNT: dict[str, int] = {
    "citadel_leaf": 4,          # le corps, et TROIS dents separees
    "citadel_housing": 7,       # deux joues, quatre cerces, une sole
    "citadel_pylon": 4,         # deux jambes, un chapiteau, un talon
    "citadel_bastion": 1,
    "citadel_crown": 5,         # la dalle, quatre merlons
    "citadel_relay": 1,
    "citadel_conduit": 4,       # le caisson, trois colliers
    "citadel_core": 1,
    "citadel_shield": 1,
}


def build_parts() -> list[bpy.types.Object]:
    parts = [build_leaf(), build_housing(), build_pylon(), build_bastion(),
             build_crown(), build_relay(), build_conduit(), build_core(),
             build_shield()]
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
        # ⚠️ APRES le soudage et AVANT la triangulation : c'est le maillage soude
        # qui part a l'export, et c'est la fusion de deux sommets qui ferait
        # apparaitre une arete a trois faces. Le controle doit voir la meme
        # topologie que Godot. `_assert_solid` VIT DANS `build_turret_kit` : sa
        # demonstration (bord, bobinage, volume signe) y est ecrite et mesuree,
        # la recopier donnerait deux versions de la meme preuve.
        turretkit._assert_solid(obj)
        found = len(turretkit._shell_report(obj.data)["volumes"])
        if found != SHELL_COUNT[obj.name]:
            raise ak.ContractError(
                f"{obj.name} : {found} coque(s) fermee(s) au lieu de "
                f"{SHELL_COUNT[obj.name]} — un volume a fusionne avec un autre "
                "ou n'a pas ete emis")
        ak.triangulate(obj)
        ak.shade_smooth_by_angle(obj, angle_deg=26.0)
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

    Le conduit court vers -x et le bastion vit tout entier a x > 0 : une chaine
    fausse d'un demi-tour les mettrait a babord, les deux a la fois, et la
    bounding box du kit serait rigoureusement la meme.
    """
    for probe in (Vector((1.0, 2.0, 3.0)), Vector((6.20, 1.90, -1.40)),
                  Vector((17.20, 3.60, 0.60)), Vector((-1.20, 0.58, 0.32))):
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
    staging = tempfile.mkdtemp(prefix="aegis-citadelkit-")
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
# On lit le BINAIRE et non la scene en memoire : c'est la seule chose que Godot
# chargera. Les trois coques du depot sorties sans UV (ADR-0028) avaient toutes
# une scene Blender parfaite.

#: L'EMPRISE DEMANDEE PAR LE BRIEF, piece par piece, en repere LOCAL de la piece
#: (x de coque, y depuis l'assise, z centre sur l'origine). `None` = le brief ne
#: la fige pas. C'est ce tableau que le harnais confronte au binaire.
EMPRISE: dict[str, tuple] = {
    # nom : (x0, x1, y0, y1, s0, s1) — s relatif a la station 240
    "citadel_leaf": (0.00, 12.90, 0.00, 3.60, -0.60, 0.60),
    "citadel_housing": (12.70, 17.20, 0.00, 3.90, -0.80, 0.80),
    "citadel_pylon": (15.60, 17.20, 0.00, 3.60, -0.90, 0.90),
    "citadel_bastion": (6.90, 11.40, 0.00, 2.90, -0.40, 6.00),
    "citadel_crown": (7.40, 10.00, 0.00, 0.60, 1.60, 5.40),
    "citadel_relay": (5.40, 7.00, 0.00, 1.90, None, None),
    "citadel_conduit": (1.20, 5.40, 0.00, 0.35, None, None),
    # ⚠️ Le brief donne au noyau « rayon <= 1,30 » : un MAXIMUM, pas une cote.
    # Il est verifie a part (`CORE_RADIUS_MAX`), et le rayon retenu est 1,20 —
    # celui de `CortegeCitadel.CORE_SIZE`, deja cable et deja teste.
    "citadel_core": (None, None, 0.00, 2.18, None, None),
    "citadel_shield": (-1.80, 1.80, -1.50, 1.50, 1.98, 2.22),
}

#: LES DEUX ECARTS ASSUMES. Ils sont ECRITS, mesures et redits au compte-rendu —
#: un ecart qu'on tait est un ecart qu'on refera. Clef : (piece, champ) ; valeur :
#: (valeur mesuree attendue, raison courte).
_EMPRISE_ECARTS: dict[tuple[str, str], tuple[float, str]] = {
    ("citadel_pylon", "x0"): (
        PYLON_HEEL_X,
        "le talon va CHERCHER la lisse d'epaule (x ~ 13,88) que le brief lui "
        "demande d'atteindre a la page suivante ; arrete a 15,60 le portique "
        "flotterait au-dessus du vide, defaut qu'il existe pour corriger"),
    ("citadel_conduit", "y1"): (
        CONDUIT_COLLAR_TOP,
        "la peau MONTE de 0,28 m entre le pied du relais et le rebord de "
        "l'artere : un caisson de 0,35 m assis a -4,30 serait enterre aux "
        "quatre cinquiemes la ou il doit justement se lire"),
}

#: Le rayon maximal tolere pour le noyau (brief : « rayon <= 1,30 »).
CORE_RADIUS_MAX = 1.30

#: Plan de reference au-dessus duquel une face est reputee VUE, piece par piece.
#: ⚠️ C'EST UNE APPROXIMATION, ET ELLE EST DITE : la tranchee de bastion n'est pas
#: encore creusee (hors perimetre de ce brief), donc la part enterree du bastion
#: et de la porte est estimee sur la peau ACTUELLE. Elle sert a ne pas compter
#: comme « visible » une jupe qui ne rendra jamais un pixel, pas a decider quoi
#: que ce soit.
VISIBLE_ABOVE: dict[str, float] = {
    # Le vantail garde le plan de la porte du LOT 2 (meme assise, meme station).
    # Le LOGEMENT, lui, vit au-dela du borde (x 12,70 a 17,20, demi-largeur de
    # coque 14,0 a cette station) : il n'a rien d'enterre, et son plan
    # d'emergence est donc sa propre assise.
    "citadel_leaf": -4.99, "citadel_housing": -6.90,
    "citadel_pylon": -9.00, "citadel_bastion": -4.97,
    "citadel_crown": -3.61, "citadel_relay": -4.31, "citadel_conduit": -4.31,
    "citadel_core": -4.02, "citadel_shield": -4.58,
}


def _flank_x(s: float, y: float) -> float | None:
    """Le x du FLANC de la coque a la station `s` et a la hauteur `y`.

    Interroge le profil REEL — taper du troncon 3 compris — et non la table
    nominale : a s = 240 le bordé est deja 2 pct plus large qu'a s = 236, et le
    LOT 0 du plan l'ecrit noir sur blanc (« la fenetre libre est sur une RAMPE,
    pas sur un plateau »). Un talon cale sur 13,88 nominal manquerait la coque.
    """
    profile = cortege._half_profile(s, 1.0)
    for (x0, y0), (x1, y1) in zip(profile, profile[1:]):
        if y0 >= y >= y1 and abs(y0 - y1) > 1e-9:
            t = (y0 - y) / (y0 - y1)
            return x0 + (x1 - x0) * t
    return None


def _conduit_ground() -> tuple[float, float, float]:
    """(garde minimale au-dessus de la peau, flottement max, enterrement max).

    Mesure sur la peau REELLE, sur toute l'emprise du conduit et sur toute sa
    largeur en `s` : le taper fait bouger les abscisses du talus de 1 pct d'un
    bord a l'autre de la piece.
    """
    seat = SEAT["citadel_conduit"]
    s_c = CITADEL_STATION - ASSEMBLY_Z["citadel_conduit"]
    clearance = math.inf
    floating = -math.inf
    buried = -math.inf
    for i in range(41):
        x = CONDUIT_X[0] + (CONDUIT_X[1] - CONDUIT_X[0]) * i / 40.0
        for ds in (-CONDUIT_COLLAR_HALF_S, 0.0, CONDUIT_COLLAR_HALF_S):
            skin = cortege._surface_y(s_c + ds, x)
            clearance = min(clearance, seat + CONDUIT_TOP_Y - skin)
            floor = seat + _conduit_floor(x)
            floating = max(floating, floor - skin)
            buried = max(buried, skin - floor)
    return clearance, floating, buried


def _pylon_bite() -> tuple[float, float]:
    """(morsure minimale du talon dans le flanc, morsure maximale), en metres.

    Positive = le talon est DANS la coque. C'est la mesure qui dit si le
    portique porte quelque chose ou s'il mime un appui.
    """
    seat = SEAT["citadel_pylon"]
    s_c = CITADEL_STATION - ASSEMBLY_Z["citadel_pylon"]
    lo, hi = math.inf, -math.inf
    for i in range(9):
        # Sur la plage de la POINTE. La mesurer sur la hauteur du talon entier
        # (0,12 a 1,18) interrogeait le flanc 18 cm plus haut que la ou la pointe
        # arrive : le flanc y est deja rentre de 7 cm vers l'axe, et le harnais
        # annonçait un manque la ou il n'y en a pas.
        y = seat + PYLON_HEEL_TIP_Y[0] \
            + (PYLON_HEEL_TIP_Y[1] - PYLON_HEEL_TIP_Y[0]) * i / 8.0
        for ds in (-PYLON_HEEL_HALF_S, 0.0, PYLON_HEEL_HALF_S):
            flank = _flank_x(s_c + ds, y)
            if flank is None:
                continue
            lo = min(lo, flank - PYLON_HEEL_X)
            hi = max(hi, flank - PYLON_HEEL_X)
    return lo, hi


def _ray_runs(tris: list, axis: int, u: float, v: float) -> list[tuple]:
    """Les intervalles de MATIERE le long de `axis`, aux deux autres coordonnees.

    ⚠️ PAR NOMBRE D'ENLACEMENT, ET NON PAR PARITE. Le vantail est une union de
    quatre coques qui S'INTERPENETRENT (le corps et ses trois dents, enfoncees de
    10 cm dans le lit). Une parite compterait « dehors » au milieu d'un
    recouvrement, et rapporterait donc un JOUR la ou il y a deux epaisseurs de
    metal — l'exact contraire de ce qu'on mesure. Chaque coque etant fermee et
    orientee vers l'exterieur (`_assert_solid`, avant l'export), la somme des
    signes de traversee vaut le nombre d'enlacement : >= 1 = dans la matiere.

    Les facettes paralleles au rayon sont ecartees (elles ne le traversent pas) ;
    les grilles d'echantillonnage evitent les cotes des sections, ou un rayon
    passerait exactement par une arete.
    """
    a, b = [k for k in range(3) if k != axis]
    # (axis, a, b) doit etre une permutation DIRECTE pour que le determinant de
    # la projection soit la composante axiale de la normale : (0,1,2) et (2,0,1)
    # le sont, (1,0,2) non — d'ou le signe.
    hand = -1.0 if axis == 1 else 1.0
    events: list[tuple[float, int]] = []
    for p0, p1, p2 in tris:
        d1a, d1b = p1[a] - p0[a], p1[b] - p0[b]
        d2a, d2b = p2[a] - p0[a], p2[b] - p0[b]
        det = d1a * d2b - d1b * d2a
        if abs(det) < 1e-12:
            continue
        ra, rb = u - p0[a], v - p0[b]
        s = (ra * d2b - rb * d2a) / det
        t = (rb * d1a - ra * d1b) / det
        if s < 0.0 or t < 0.0 or s + t > 1.0:
            continue
        events.append((p0[axis] + s * (p1[axis] - p0[axis])
                       + t * (p2[axis] - p0[axis]),
                       1 if det * hand < 0.0 else -1))
    events.sort()
    runs: list[tuple[float, float]] = []
    wind = 0
    start = 0.0
    for pos, delta in events:
        before = wind
        wind += delta
        if before <= 0 < wind:
            start = pos
        elif before > 0 >= wind:
            runs.append((start, pos))
    return runs


def _covered(runs: list[tuple], pos: float, tol: float = 1e-6) -> bool:
    return any(lo - tol <= pos <= hi + tol for lo, hi in runs)


def _seam_report(tris: list) -> dict:
    """LA FERMETURE, MESUREE AU LANCER DE RAYONS SUR LE BINAIRE LIVRE.

    Deux vantaux, l'un tel quel, l'autre par le yaw de pi du moteur : la matiere
    du vantail babord en (y, s) est celle du tribord en (y, -s), retournee en x.
    Deux questions, et ce sont les deux seules manieres dont une porte fuit :

      1. LE JOUR D'UNE PORTE — un rayon HORIZONTAL, le long de x. Partout ou la
         porte a de la matiere a cette hauteur et cette bande, le plan de joint
         x = 0 doit etre couvert par l'un des deux vantaux. C'est la que se
         verifie « le tenon ferme la mortaise de l'autre » : dans les bandes 0, 2
         et 4 c'est le vantail tribord qui tient le joint, dans les bandes 1, 3
         et 5 c'est celui de babord. Une seule bande decouverte, et on voit les
         etoiles au travers.
      2. LE JOUR DE LA CAMERA — un rayon VERTICAL, le long de y, sur toute
         l'emprise de la porte fermee. C'est lui qui prouve que les mortaises
         sont des POCHES et non des fentes traversantes : le lit est plein a
         3,00, et la camera qui plonge a 70 deg ne voit jamais la coque a travers
         la machoire.
    """
    bands = TOOTH_BANDS
    width = 2.0 * LEAF_HALF_S / bands
    gap_max = 0.0
    gap_at: tuple[float, float] | None = None
    holder = {"les deux": 0, "gorge": 0, "sans objet": 0}
    tested = 0
    for i in range(bands * 4):
        # quatre hauteurs par bande, decalees pour ne jamais tomber sur une cote
        z = -LEAF_HALF_S + width * (i // 4) + width * (0.17 + 0.22 * (i % 4))
        for j in range(23):
            y = 0.041 + 3.52 * j / 22.0
            here = _ray_runs(tris, 0, y, z)
            there = [(-hi, -lo) for lo, hi in _ray_runs(tris, 0, y, -z)]
            # ⚠️ ON NE TESTE LE JOINT QUE LA OU IL Y A DEUX CHOSES A JOINDRE.
            # Au-dessus du lit, la mortaise d'un vantail est un CANAL OUVERT que
            # rien ne doit fermer — c'est le motif de la machoire, mesure a part
            # (`jaw`). Exiger de la matiere au plan de joint a CETTE hauteur
            # reviendrait a interdire la denture qu'on demande.
            near_here = any(lo < 0.30 for lo, _h in here)
            near_there = any(hi > -0.30 for _l, hi in there)
            if not (near_here and near_there):
                holder["sans objet"] += 1
                continue
            tested += 1
            if _covered(here, 0.0) and _covered(there, 0.0):
                holder["les deux"] += 1
            else:
                # ⚠️ LES DEUX CORPS NE SE TOUCHENT PAS ICI : c'est soit la GORGE
                # DE REFEND — un rentrant de surface, borne par construction a
                # deux fois sa profondeur en x — soit un vrai jour. La seule
                # chose qui les separe est la LARGEUR, et c'est pour cela qu'on
                # la mesure au lieu de compter des echecs.
                holder["gorge"] += 1
                lo = max((hi for _l, hi in there), default=-math.inf)
                hi = min((l for l, _h in here), default=math.inf)
                if hi - lo > gap_max:
                    gap_max, gap_at = hi - lo, (y, z)
    # ⚠️ LA MACHOIRE SE MESURE PAR LE PROFIL DE CRETE, BANDE PAR BANDE, DE PART
    # ET D'AUTRE DU JOINT — c'est la seule chose qui distingue une denture d'un
    # peigne decoratif. A 30 cm du plan de joint, on demande a la matiere jusqu'ou
    # elle monte : dans les bandes de CE vantail elle monte au sommet (dent), dans
    # les autres elle s'arrete au lit (mortaise), et la PHASE S'INVERSE en
    # franchissant l'axe. Le vantail babord etant le tribord par un yaw de pi, sa
    # crete en (x, s) est celle du tribord en (-x, -s).
    jaw: list[tuple[float, float]] = []
    for k in range(bands):
        z = -LEAF_HALF_S + width * (k + 0.5)
        jaw.append((
            max((hi for _l, hi in _ray_runs(tris, 1, 0.30, z)), default=0.0),
            max((hi for _l, hi in _ray_runs(tris, 1, 0.30, -z)), default=0.0)))
    # ⚠️ ET LE JOUR QUI COMPTE VRAIMENT EST VERTICAL. La camera plonge a 70 deg,
    # donc a 20 deg de la verticale : ce qui se verrait au travers d'une mortaise
    # devenue fente, c'est la coque deux metres plus bas. On tire donc a la
    # verticale sur toute la zone du joint, les deux vantaux montes.
    holes: list[tuple[float, float]] = []
    thinnest = math.inf
    for i in range(61):
        x = -3.00 + 6.00 * i / 60.0
        for j in range(bands * 3):
            z = -LEAF_HALF_S + width * (j // 3) + width * (0.21 + 0.29 * (j % 3))
            depth = sum(hi - lo for lo, hi in _ray_runs(tris, 1, x, z)) \
                + sum(hi - lo for lo, hi in _ray_runs(tris, 1, -x, -z))
            if depth <= 1e-6:
                holes.append((x, z))
            else:
                thinnest = min(thinnest, depth)
    return {"seam_tested": tested, "seam_gap": gap_max, "seam_gap_at": gap_at,
            "seam_holder": holder, "jaw": jaw, "vertical_holes": holes,
            "vertical_min": thinnest}


def _housing_fit(leaf: dict, housing: dict, travel: float) -> dict:
    """LE VANTAIL DANS SON FOURREAU — jeux relus sur les SOMMETS du binaire.

    Le fourreau n'est pas decrit par ses constantes mais RETROUVE dans le
    fichier : sa demi-largeur utile est le plus petit |s| de tout ce qui se
    trouve au-dessus de sa sole (donc la face interieure des joues), et le
    dessus de sa sole est le plus haut sommet compris entre ces deux joues. Un
    logement dont on aurait epaissi une joue par megarde rendrait donc un jeu
    negatif, et le build echouerait.
    """
    seat_l, seat_h = SEAT["citadel_leaf"], SEAT["citadel_housing"]
    hpts = housing["points"]
    cavity_s = min((abs(p[2]) for p in hpts
                    if p[1] > HOUSING_SILL_Y + 0.05), default=0.0)
    x0, x1 = housing["min"][0], housing["max"][0]
    # ⚠️ LE FOND DU FOURREAU SE TIRE AU RAYON, IL NE SE LIT PAS SUR LES SOMMETS.
    # La sole DEBORDE dans les joues (de 4 cm, pour ne pas leur affleurer) :
    # aucun de ses sommets n'est donc « dans » la cavite, et un max sur les
    # sommets rendait 0,00 — c'est-a-dire un jeu de 0,30 m annonce la ou il y en
    # a 0,02. On demande donc a la matiere, verticalement, ce qu'elle a de plus
    # haut a l'interieur du U : cela mesure la sole ET tout ce qui viendrait un
    # jour barrer la course.
    sill = 0.0
    for i in range(19):
        px = x0 + (x1 - x0) * (i + 0.5) / 19.0
        for j in range(9):
            pz = -cavity_s + 2.0 * cavity_s * (j + 0.5) / 9.0
            for _lo, hi in _ray_runs(housing["geom"], 1, px, pz):
                sill = max(sill, hi)
    inside = [p for p in leaf["points"] if p[0] + travel >= x0]
    lateral = cavity_s - max((abs(p[2]) for p in inside), default=0.0)
    vertical = (seat_l + min((p[1] for p in inside), default=0.0)) \
        - (seat_h + sill)
    return {
        "travel": travel,
        "cavity_half_s": cavity_s,
        "sill_y": seat_h + sill,
        "leaf_x": (leaf["min"][0] + travel, leaf["max"][0] + travel),
        "overlap": leaf["max"][0] + travel - x0,
        "margin_out": housing["max"][0] - (leaf["max"][0] + travel),
        "passe": 2.0 * (leaf["min"][0] + travel),
        "lateral": lateral,
        "vertical": vertical,
    }


def _frame_width(plane_y: float) -> float:
    """La largeur du cadre de la camera du jeu, au plan `plane_y`.

    Calculee, jamais estimee : c'est elle qui dit si la porte ferme vraiment la
    route ou si le joueur peut la contourner par le bord de l'ecran.
    """
    depth = (cortege.CAM_POS.y - plane_y) / -cortege.CAM_FORWARD.y
    half_v = math.tan(cortege.CAM_FOV_V * 0.5) * depth
    return 2.0 * half_v * cortege.CAM_ASPECT


def _roundness(points: list[tuple], axis: int = 1) -> float:
    """Rayon max / rayon min, mesure ANNEAU PAR ANNEAU autour de l'axe Y.

    ⚠️ C'EST LA MESURE DE « REVOLUTION », ET ELLE NE SE DEDUIT PAS DE LA BOITE.
    Un prisme carre et un tambour ont la meme boite englobante ; ce qui les
    separe est la CONSTANCE DU RAYON a hauteur donnee. Un polygone regulier, de
    n'importe quel ordre, rend donc 1,0000 : tous ses sommets sont sur le meme
    cercle. Un carre chanfreine rend 1,29 (mesure sur le relais), un carre franc
    1,4142. Le seuil est a 1,05, et l'ordre du polygone est dit a part
    (`CORE_SEG` = 16 facettes, soit un ecart circonscrit/inscrit de 1,0196).
    """
    bands: dict[int, list[float]] = {}
    for p in points:
        key = int(round(p[axis] * 100.0))
        radius = math.hypot(*[p[a] for a in range(3) if a != axis])
        if radius > 0.05:
            bands.setdefault(key, []).append(radius)
    worst = 1.0
    for values in bands.values():
        if len(values) < 4:
            continue
        worst = max(worst, max(values) / max(min(values), 1e-9))
    return worst


def _accessor(gltf: dict, blob: bytes, index: int) -> list[tuple]:
    return turretkit._accessor(gltf, blob, index)


def _indices(gltf: dict, blob: bytes, prim: dict) -> list[int]:
    return turretkit._indices(gltf, blob, prim)


def _audit(path: str) -> dict:
    """Relit le `.glb` PRODUIT et verifie tout ce que le brief exige."""
    gltf, blob = _read_glb(path)
    problems: list[str] = []
    materials = [m.get("name", f"#{i}")
                 for i, m in enumerate(gltf.get("materials", []))]
    nodes = gltf.get("nodes", [])
    roots = gltf.get("scenes", [{}])[0].get("nodes", list(range(len(nodes))))
    root_names = [nodes[i].get("name", "?") for i in roots]

    # --- LES NEUF NOMS, ET RIEN D'AUTRE ----------------------------------
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
    built_area: dict[str, float] = {}
    seen_area: dict[str, float] = {}
    emissive_by_part: dict[str, float] = {}
    area_by_part: dict[str, float] = {}
    total_area = total_built = total_seen = 0.0
    density: dict[str, dict] = {}
    roundness: dict[str, float] = {}

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
        copies = ASSEMBLY_COPIES[name]
        floor = VISIBLE_ABOVE[name] - SEAT[name]
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
                normal = (Vector(points[ib]) - pa).cross(Vector(points[ic]) - pa)
                area = normal.length * 0.5
                total_area += area
                area_by_material[material] = \
                    area_by_material.get(material, 0.0) + area
                area_by_part[name] = area_by_part.get(name, 0.0) + area
                built_area[material] = built_area.get(material, 0.0) \
                    + area * copies
                total_built += area * copies
                if material == "AA_Emissive_Engine":
                    emissive_by_part[name] = \
                        emissive_by_part.get(name, 0.0) + area
                # L'aire VUE : au-dessus du plan d'emergence de la piece, et dont
                # la normale ne regarde pas le sol.
                cy = (points[ia][1] + points[ib][1] + points[ic][1]) / 3.0
                downward = normal.length > 1e-12 and \
                    normal.normalized().y < -0.5
                if cy > floor and not downward:
                    seen_area[material] = \
                        seen_area.get(material, 0.0) + area * copies
                    total_seen += area * copies
        if uvs:
            density[name] = turretkit._texel_density(pts, uvs, tris)
        roundness[name] = _roundness(pts)
        triangles_total += triangles
        stats[name] = {"triangles": triangles, "min": tuple(lo),
                       "max": tuple(hi),
                       "size": tuple(hi[a] - lo[a] for a in range(3)),
                       "points": pts,
                       # les triangles en COORDONNEES : c'est sur eux que le
                       # lancer de rayons de `_seam_report()` travaille, donc
                       # sur le binaire et non sur la scene Blender.
                       "geom": [(pts[a], pts[b], pts[c]) for a, b, c in tris]}

    # --- LA REGLE DURE : AUCUN EMISSIF HORS DES PIECES QUI MEURENT --------
    for name in PART_NAMES:
        if name in DESTRUCTIBLE:
            continue
        if emissive_by_part.get(name, 0.0) > 1e-9:
            problems.append(
                f"{name} porte {emissive_by_part[name]:.3f} m2 d'emissif — le "
                "moteur ne detruit QUE `citadel_relay` et `citadel_core` : un "
                "emissif ailleurs resterait allume apres la mort d'un relais, et "
                "la regle « gauche + droite -> centre » ne se verrait plus")
    for name in DESTRUCTIBLE:
        if emissive_by_part.get(name, 0.0) <= 1e-9:
            problems.append(
                f"{name} ne porte aucun emissif : la cible ne s'annoncerait plus")

    # --- L'EMPRISE, RELEVEE SUR LE BINAIRE, ET SES DEUX ECARTS ------------
    ecarts: list[tuple[str, str, float, float, str]] = []
    for name, want in EMPRISE.items():
        got = stats.get(name)
        if got is None:
            continue
        s_c = -ASSEMBLY_Z[name]
        expected = {
            "x0": want[0], "x1": want[1], "y0": want[2], "y1": want[3],  # noqa
            "z0": None if want[5] is None else -(want[5] - s_c),
            "z1": None if want[4] is None else -(want[4] - s_c),
        }
        measured = {"x0": got["min"][0], "x1": got["max"][0],
                    "y0": got["min"][1], "y1": got["max"][1],
                    "z0": got["min"][2], "z1": got["max"][2]}
        for field, target in expected.items():
            if target is None:
                continue
            value = measured[field]
            if abs(value - target) <= 1.5e-3:
                continue
            allowed = _EMPRISE_ECARTS.get((name, field))
            if allowed is not None and abs(value - allowed[0]) <= 1.5e-3:
                ecarts.append((name, field, target, value, allowed[1]))
                continue
            problems.append(
                f"{name}.{field} : {value:+.4f} au lieu de {target:+.4f} "
                "demande par le brief — et aucun ecart n'est declare pour ce "
                "champ (`_EMPRISE_ECARTS`)")

    # --- LE MIROIR : DEUX REGLES, ET LE HARNAIS LES DISTINGUE -------------
    # ⚠️ LE CENTRAGE EN Z VAUT POUR LES NEUF, SANS EXCEPTION : c'est
    # l'excentricite en `s` que le yaw de pi retourne, et une boite qui n'y
    # serait pas centree poserait la copie babord DECALEE LE LONG DU VAISSEAU.
    # La regle de COTE, elle, depend de ce que l'origine de la piece designe :
    # son centre pour six d'entre elles — qui doivent donc rester franchement
    # tribord — son BOUT INTERIEUR pour le vantail, dont la matiere commence a
    # x = 0 tout juste, parce que c'est la que les deux moities se rejoignent.
    # Une regle unique refuserait l'une ou laisserait passer l'autre.
    for name in PART_NAMES:
        got = stats.get(name)
        if got is None:
            continue
        centre_z = (got["min"][2] + got["max"][2]) * 0.5
        if abs(centre_z) > 1e-4:
            problems.append(
                f"{name} : centre en Z a {centre_z:+.5f} au lieu de 0 — le yaw "
                "de pi du moteur enverrait la copie babord a DEUX FOIS cette "
                "excentricite le long du vaisseau, et rien ne le dirait")
        if name in ORIGIN_AT_INNER_END:
            if got["min"][0] < -1e-4:
                problems.append(
                    f"{name} : sa matiere franchit l'axe de "
                    f"{-got['min'][0]:.3f} m — la copie babord recouvrirait la "
                    "sienne, et la passe ouverte perdrait le double")
            elif got["min"][0] > 1e-3:
                problems.append(
                    f"{name} : sa matiere commence a x = {got['min'][0]:+.4f} "
                    f"au lieu de 0 — porte fermee, les deux moities laisseraient "
                    f"un jour de {2 * got['min'][0]:.3f} m au milieu")
        elif name in MIRRORED and got["min"][0] <= 0.05:
            problems.append(
                f"{name} : il atteint x = {got['min'][0]:+.3f} — une piece "
                "miroitee doit rester franchement tribord, sans quoi les deux "
                "copies se chevauchent sur l'axe")
        if name not in MIRRORED:
            turretkit._assert_on_axis(name, got["points"], problems,
                                      revolution=False)

    # --- LES PLAFONDS, COMPOSES ASSISE + HAUTEUR MESUREE ------------------
    crests: dict[str, float] = {}
    for name in PART_NAMES:
        got = stats.get(name)
        if got is None:
            continue
        crest = SEAT[name] + got["max"][1]
        crests[name] = crest
        ceiling = CEILING_OF[name]
        if crest > ceiling + 1e-6:
            problems.append(
                f"{name} : sommet compose a {crest:+.3f} au-dessus du plafond "
                f"{ceiling:+.2f} (assise {SEAT[name]:+.2f} + hauteur mesuree "
                f"{got['max'][1]:.3f})")

    # --- LES QUATRE SILHOUETTES, MESUREES ---------------------------------
    leaf = stats.get("citadel_leaf")
    housing = stats.get("citadel_housing")
    bastion = stats.get("citadel_bastion")
    relay = stats.get("citadel_relay")
    conduit = stats.get("citadel_conduit")
    core = stats.get("citadel_core")
    if leaf is not None:
        ratio = 2.0 * DOOR_HALF_X / leaf["size"][2]
        if ratio < 20.0:
            problems.append(
                f"la porte assemblee : {ratio:.1f} : 1 de rapport "
                "longueur/epaisseur — sa signature est la LONGUEUR, elle doit "
                "rester la seule chose du niveau qui traverse le cadre")
        if leaf["size"][0] <= max(s["size"][0] for n, s in stats.items()
                                  if n != "citadel_leaf"):
            problems.append("citadel_leaf n'est plus la piece la plus longue")
    if leaf is not None and housing is not None:
        # ⚠️ LE FOURREAU EST PLUS GRAND QUE CE QU'IL RECOIT, ET IL LE DEVIENT
        # PAR LE BAS. C'est la cote qui peut tout casser en silence : un
        # logement qui gagnerait sa garde en montant franchirait le plafond du
        # decor inerte (ADR-0041) sans qu'aucun test ne rougisse.
        if housing["size"][2] <= leaf["size"][2] + 1e-6:
            problems.append(
                f"citadel_housing : {housing['size'][2]:.2f} m d'epaisseur pour "
                f"un vantail de {leaf['size'][2]:.2f} m — un fourreau plus mince "
                "que sa piece ne la recoit pas")
        if SEAT["citadel_housing"] >= SEAT["citadel_leaf"] - 1e-6:
            problems.append(
                "citadel_housing : son assise n'est pas SOUS celle du vantail — "
                "un fourreau qui gagne sa garde par le haut franchit le plafond")
        crest_l = SEAT["citadel_leaf"] + leaf["max"][1]
        crest_h = SEAT["citadel_housing"] + housing["max"][1]
        if abs(crest_h - crest_l) > 1.5e-3:
            problems.append(
                f"citadel_housing culmine a {crest_h:+.3f} et le vantail a "
                f"{crest_l:+.3f} : les deux doivent affleurer le plafond du "
                "decor, pas se marcher dessus")
    if bastion is not None:
        if bastion["size"][0] <= bastion["size"][1]:
            problems.append(
                f"citadel_bastion : {bastion['size'][0]:.2f} m de large pour "
                f"{bastion['size'][1]:.2f} m de haut — il doit etre PLUS LARGE "
                "QUE HAUT, sans quoi il se lit comme un affut geant")
    if relay is not None:
        slim = relay["size"][1] / max(relay["size"][0], relay["size"][2])
        if not 0.90 <= slim <= 1.45:
            problems.append(
                f"citadel_relay : rapport hauteur/largeur {slim:.2f} — le brief "
                "demande COURT ET EPAIS (0,90 a 1,45) ; plus haut, il retombe "
                "sur le nœud d'epine")
        if abs(relay["max"][0] - RELAY_X - RELAY_HALF) > 1.5e-3 or \
                RELAY_HALF - RELAY_BODY_HALF < 0.10:
            problems.append(
                "citadel_relay : le collier ne deborde plus assez le fut pour "
                "porter une ombre (il EST le signal de branchement)")
    if conduit is not None:
        length = conduit["size"][0]
        if length < 6.0 * conduit["size"][1]:
            problems.append(
                f"citadel_conduit : {length:.2f} m de long pour "
                f"{conduit['size'][1]:.2f} m de haut — il doit rester une ligne "
                "BASSE et horizontale, pas un tube")
        if abs(conduit["max"][0] - (RELAY_X - RELAY_HALF)) > 1.5e-3:
            problems.append(
                f"citadel_conduit : il part de x = {conduit['max'][0]:.3f} alors "
                f"que le flanc interne du relais est a {RELAY_X - RELAY_HALF:.2f} "
                "— la jonction relais/conduit se verrait ouverte")
        if not cortege.CANAL_HALF <= conduit["min"][0] <= cortege.CANAL_RIM_X:
            problems.append(
                f"citadel_conduit : il finit a x = {conduit['min'][0]:.2f}, hors "
                f"du rebord de l'artere ({cortege.CANAL_HALF:.2f} a "
                f"{cortege.CANAL_RIM_X:.2f}) — c'est l'artere qui prend le relais")
    if core is not None:
        if roundness["citadel_core"] > 1.05:
            problems.append(
                f"citadel_core : circularite {roundness['citadel_core']:.4f} — "
                "la REVOLUTION est sa signature, elle se mesure anneau par "
                "anneau et non a la boite englobante")
        if roundness.get("citadel_relay", 1.0) < 1.10:
            problems.append(
                f"citadel_relay : circularite {roundness['citadel_relay']:.4f} — "
                "il se rapproche du tambour, donc du NOYAU. Le relais est "
                "prismatique, c'est ce qui empeche de les confondre en noir et "
                "blanc")
        if max(abs(core["min"][0]), abs(core["max"][0])) > CORE_RADIUS_MAX:
            problems.append(
                f"citadel_core : rayon {max(abs(core['min'][0]), abs(core['max'][0])):.3f} "
                f"> {CORE_RADIUS_MAX:.2f} demande")
        # ⚠️ LA HIERARCHIE ENTIERE TIENT ICI, ET ELLE NE SE TESTE PAS PAR UN
        # `max()`. Le relais et le bouclier montent EUX AUSSI a -2,40 — c'est le
        # plafond du gameplay, et le LOT 0 le leur donne : chercher « la piece la
        # plus haute » rendait donc un ex aequo tranche par l'ordre d'un
        # dictionnaire. Ce qui est vrai, et ce que la consigne 19 demande, c'est
        # que rien d'INERTE n'atteigne le noyau : il domine le decor de 60 cm.
        inert = max(c for n, c in crests.items()
                    if n not in DESTRUCTIBLE and n != "citadel_shield")
        if crests["citadel_core"] < max(crests.values()) - 1e-6:
            problems.append(
                f"citadel_core plafonne a {crests['citadel_core']:+.3f} alors "
                f"qu'une piece monte a {max(crests.values()):+.3f}")
        if crests["citadel_core"] - inert < 0.30:
            problems.append(
                f"le noyau ne domine le decor inerte que de "
                f"{crests['citadel_core'] - inert:.2f} m — c'est ce surplomb qui "
                "le designe comme le centre sans un mot de HUD")

    # --- LA PORTE FERME-T-ELLE VRAIMENT LA ROUTE ? ------------------------
    frame = _frame_width(-4.30)
    covered = 2.0 * DOOR_HALF_X / frame
    if covered < 0.80:
        problems.append(
            f"la porte ne couvre que {100 * covered:.1f} pct du cadre de la "
            "camera : le joueur contournerait le verrou, et la sequence "
            "deviendrait facultative")
    # --- ET LE SURPLOMB EST-IL PORTE ? ------------------------------------
    hull_half = cortege._half_width(CITADEL_STATION, 1.0)
    overhang = DOOR_HALF_X - hull_half
    bite_lo, bite_hi = _pylon_bite()
    if bite_lo <= 0.02:
        problems.append(
            f"citadel_pylon : le talon manque le flanc de {-bite_lo:.3f} m — il "
            "mimerait un appui au lieu d'en etre un, et « un mur invisible est "
            "la meme injustice qu'une tourelle qu'on croit pouvoir raser »")
    if PYLON_X0 > hull_half + overhang * 0.7:
        problems.append(
            "citadel_pylon : il ne couvre pas assez du surplomb")

    # --- LE CONDUIT REPOSE-T-IL SUR LA PEAU ? -----------------------------
    clearance, floating, buried = _conduit_ground()
    if clearance < 0.24:
        problems.append(
            f"citadel_conduit : il ne degage plus que {clearance:.3f} m au-dessus "
            "de la peau a son extremite interieure — c'est la qu'il doit se lire")
    if floating > 0.03:
        problems.append(
            f"citadel_conduit : il FLOTTE de {floating:.3f} m au-dessus de la "
            "peau — le talus de l'artere n'est pas la ou son dessous le croit")

    # --- LA FERMETURE ET LA COURSE, MESUREES SUR LE BINAIRE ----------------
    seam = _seam_report(leaf["geom"]) if leaf is not None else None
    if seam is not None:
        if seam["seam_gap"] > 2.0 * REVEAL_X + 1e-3:
            y, z = seam["seam_gap_at"]
            problems.append(
                f"le plan de joint est ouvert de {seam['seam_gap']:.3f} m "
                f"(a y = {y:.2f}, s = {z:+.2f}) : c'est plus que la gorge de "
                f"refend ({2 * REVEAL_X:.2f} m), donc un JOUR — porte fermee, "
                "on verrait au travers")
        if seam["vertical_holes"]:
            x, z = seam["vertical_holes"][0]
            problems.append(
                f"{len(seam['vertical_holes'])} echantillon(s) traversent la "
                f"porte fermee VERTICALEMENT (par exemple x = {x:+.2f}, "
                f"s = {z:+.2f}) — une mortaise est devenue une fente, et la "
                "camera plonge a 70 deg")
        step = LEAF_H - TOOTH_BED_Y
        signs = [1 if a > b + 0.5 * step else (-1 if b > a + 0.5 * step else 0)
                 for a, b in seam["jaw"]]
        if 0 in signs:
            problems.append(
                f"profil de crete {['%.2f/%.2f' % ab for ab in seam['jaw']]} : "
                f"une bande au moins ne montre pas de marche de {step:.2f} m "
                "entre les deux vantaux — la machoire ne s'engrene pas, et la "
                "porte se lira comme un mur")
        elif any(signs[k] == signs[k + 1] for k in range(len(signs) - 1)):
            problems.append(
                f"profil de crete {signs} : deux bandes voisines montent du "
                "MEME cote — une dent tombe en face d'une dent, ce que le "
                "compte impair est justement la pour interdire")
        elif signs.count(1) != len(TOOTH_MINE) or signs.count(1) % 2 == 0:
            problems.append(
                f"{signs.count(1)} dent(s) par vantail au lieu de "
                f"{len(TOOTH_MINE)}, et le compte doit rester IMPAIR")
    fits = []
    if leaf is not None and housing is not None:
        for travel in (0.0, LEAF_TRAVEL):
            fit = _housing_fit(leaf, housing, travel)
            fits.append(fit)
            if fit["lateral"] < 0.005:
                problems.append(
                    f"course {travel:.2f} : le vantail ne passe plus dans son "
                    f"fourreau ({fit['lateral']:+.3f} m de jeu lateral)")
            if fit["vertical"] < 0.005:
                problems.append(
                    f"course {travel:.2f} : le vantail touche la sole du "
                    f"fourreau ({fit['vertical']:+.3f} m de jeu)")
            if fit["margin_out"] < -1e-4:
                problems.append(
                    f"course {travel:.2f} : le vantail depasse le bout "
                    f"exterieur de {-fit['margin_out']:.3f} m — rien ne doit "
                    f"sortir de x = {DOOR_HALF_X:.2f}")
        if abs(fits[0]["overlap"] - 0.20) > 1.5e-3:
            problems.append(
                f"ferme, le vantail n'entre dans son logement que de "
                f"{fits[0]['overlap']:.3f} m au lieu de 0,20 — c'est ce "
                "recouvrement qui interdit un jour au bout de la porte")
        if abs(fits[1]["passe"] - 8.50) > 1.5e-3:
            problems.append(
                f"ouverte, la passe fait {fits[1]['passe']:.3f} m au lieu de "
                "8,50 — le corps du Specter-9 en fait 1,76 (ADR-0034), et une "
                "passe qu'il faut enfiler n'est pas une passe")

    # --- UV, materiaux, textures ------------------------------------------
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
    if "AA_Panel" in used_materials or "AA_Marking_Red" in used_materials:
        problems.append(
            "un slot hors des cinq emplois du brief est utilise (AA_Panel ou "
            "AA_Marking_Red)")

    # --- densite de texels -------------------------------------------------
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

    # --- budgets -----------------------------------------------------------
    if triangles_total > TRI_BUDGET_KIT:
        problems.append(
            f"{triangles_total} triangles pour le kit > budget {TRI_BUDGET_KIT}")
    trim_share = area_by_material.get("AA_Trim", 0.0) / max(total_area, 1e-9)
    if trim_share > TRIM_SHARE_MAX:
        problems.append(
            f"AA_Trim occupe {100 * trim_share:.2f} pct de l'aire du kit > "
            f"{100 * TRIM_SHARE_MAX:.0f} pct — c'est un lisere de lecture, pas "
            "une matiere")

    if problems:
        raise ak.ContractError(
            "CONTRAT ROMPU — citadel_kit\n"
            + "\n".join(f"  - {p}" for p in problems))

    for name in stats:
        stats[name].pop("points", None)
        stats[name].pop("geom", None)
    assembled = sum(stats[n]["triangles"] * ASSEMBLY_COPIES[n]
                    for n in PART_NAMES)
    return {
        "parts": stats,
        "primitives": (prims_uv, prims_tan, prims_total),
        "triangles": triangles_total,
        "assembled": assembled,
        "materials": sorted(used_materials),
        "area_by_material": area_by_material,
        "built_by_material": built_area,
        "seen_by_material": seen_area,
        "area_by_part": area_by_part,
        "total_area": total_area,
        "total_built": total_built,
        "total_seen": total_seen,
        "emissive_by_part": emissive_by_part,
        "density": density,
        "roundness": roundness,
        "crests": crests,
        "ecarts": ecarts,
        "frame_width": frame,
        "gate_cover": covered,
        "hull_half": hull_half,
        "overhang": overhang,
        "pylon_bite": (bite_lo, bite_hi),
        "conduit_ground": (clearance, floating, buried),
        "trim_share": trim_share,
        "seam": seam,
        "fits": fits,
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


def _print_report(report: dict) -> None:
    print("\n--- citadel_kit : mesures relevees sur le .glb PRODUIT ---")
    print(f"  {'piece':<17} {'tri':>5} {'x':>2}  "
          f"{'largeur x hauteur x longueur':>30}")
    for name in PART_NAMES:
        s = report["parts"][name]
        print(f"  {name:<17} {s['triangles']:>5} {ASSEMBLY_COPIES[name]:>2}  "
              f"{s['size'][0]:9.2f} x {s['size'][1]:6.2f} x {s['size'][2]:7.2f}")
    print(f"  {'TOTAL (kit)':<17} {report['triangles']:>5}     "
          f"budget {TRI_BUDGET_KIT}")
    print(f"  verrou assemble ({sum(ASSEMBLY_COPIES.values())} instances) : "
          f"{report['assembled']} triangles")

    print("\n  L'EMPRISE MESUREE, PIECE PAR PIECE — c'est elle qui dit au moteur")
    print("  ou poser. Repere local : x de COQUE, y depuis l'ASSISE, s relatif a")
    print(f"  la station {CITADEL_STATION:.0f}.")
    print(f"    {'piece':<17} {'x min':>7} {'x max':>7} {'y min':>7} "
          f"{'y max':>7} {'s min':>7} {'s max':>7}")
    for name in PART_NAMES:
        s = report["parts"][name]
        s_c = -ASSEMBLY_Z[name]
        s0 = s_c - s["max"][2]
        s1 = s_c - s["min"][2]
        print(f"    {name:<17} {s['min'][0]:7.2f} {s['max'][0]:7.2f} "
              f"{s['min'][1]:7.2f} {s['max'][1]:7.2f} {s0:+7.2f} {s1:+7.2f}")

    print("\n  OU LE MOTEUR POSE CHAQUE PIECE — une translation, un yaw, rien de plus")
    print(f"    {'piece':<17} {'translation locale':<26} {'yaw':<12} {'copies'}")
    for name in PART_NAMES:
        yaw = "0 et pi" if name in MIRRORED else "0"
        where = f"(0, {SEAT[name]:+.2f}, {ASSEMBLY_Z[name]:+.2f})"
        note = "  <- DETRUITE" if name in DESTRUCTIBLE else ""
        print(f"    {name:<17} {where:<26} {yaw:<12} "
              f"{ASSEMBLY_COPIES[name]}{note}")
    print("    Le X de la COQUE est cuit dans la geometrie : tribord et babord "
          "recoivent la MEME\n    translation, et pour seule difference le yaw. "
          "Chaque piece est centree en Z sur son\n    origine, ce qui rend le "
          "miroir exact le long du vaisseau.")

    print("\n  LES PLAFONDS, COMPOSES (assise du plan + hauteur mesuree)")
    print(f"    {'piece':<17} {'assise':>8} {'hauteur':>8} {'sommet':>8} "
          f"{'plafond':>8} {'marge':>7}")
    for name in PART_NAMES:
        s = report["parts"][name]
        crest = report["crests"][name]
        ceiling = CEILING_OF[name]
        print(f"    {name:<17} {SEAT[name]:8.2f} {s['max'][1]:8.2f} "
              f"{crest:8.2f} {ceiling:8.2f} {ceiling - crest:7.2f}")
    print(f"    Le noyau culmine a {report['crests']['citadel_core']:+.2f} : "
          f"{report['crests']['citadel_core'] - report['crests']['citadel_leaf']:+.2f} m "
          "au-dessus des vantaux et\n    des couronnes. Le seul volume autorise "
          "a culminer est celui qu'on peut tirer.")
    print(f"    Vantail et logement affleurent le MEME plafond "
          f"({report['crests']['citadel_leaf']:+.2f} et "
          f"{report['crests']['citadel_housing']:+.2f}) : le fourreau a gagne sa "
          "garde\n    par le BAS (assise -6,90 contre -6,60), jamais par le "
          "haut.")

    print("\n  LES QUATRE SILHOUETTES, MESUREES (pas affirmees)")
    leaf = report["parts"]["citadel_leaf"]
    housing = report["parts"]["citadel_housing"]
    bastion = report["parts"]["citadel_bastion"]
    relay = report["parts"]["citadel_relay"]
    conduit = report["parts"]["citadel_conduit"]
    core = report["parts"]["citadel_core"]
    print(f"    porte    LONGUEUR      {2 * DOOR_HALF_X:.2f} m assemblee pour "
          f"{leaf['size'][2]:.2f} m d'epaisseur, soit "
          f"{2 * DOOR_HALF_X / leaf['size'][2]:.1f} : 1 ; DEUX vantaux de "
          f"{leaf['size'][0]:.2f} m, {len(TOOTH_MINE)} dents chacun sur "
          f"{TOOTH_BANDS} bandes")
    print(f"    bastion  MASSE ETAGEE  {bastion['size'][0]:.2f} m de large pour "
          f"{bastion['size'][1]:.2f} m de haut (plus large que haut), deux "
          f"niveaux : {SEAT['citadel_bastion'] + bastion['size'][1]:+.2f} puis "
          f"{report['crests']['citadel_crown']:+.2f}")
    print(f"    relais   BRANCHEMENT   {relay['size'][0]:.2f} x "
          f"{relay['size'][1]:.2f} m (rapport "
          f"{relay['size'][1] / relay['size'][0]:.2f}), collier debordant de "
          f"{RELAY_HALF - RELAY_BODY_HALF:.2f} m ; conduit de "
          f"{conduit['size'][0]:.2f} m de long pour {conduit['size'][1]:.2f} m "
          "de haut")
    print(f"    noyau    REVOLUTION    constance du rayon "
          f"{report['roundness']['citadel_core']:.4f} sur {CORE_SEG} facettes, "
          f"contre {report['roundness']['citadel_relay']:.4f} pour le relais "
          f"prismatique (1,0000 = revolution parfaite) ; rayon "
          f"{core['size'][0] / 2:.2f} m")

    print("\n  LA MACHOIRE ET LA COURSE — MESUREES SUR LE BINAIRE LIVRE")
    seam = report["seam"]
    print(f"    plan de joint : {seam['seam_tested']} echantillons de rayon "
          f"horizontal ; ouverture maximale {seam['seam_gap']:.3f} m, pour une "
          f"gorge de refend de {2 * REVEAL_X:.2f} m")
    print(f"      les deux corps se touchent {seam['seam_holder']['les deux']} "
          f"fois, la gorge de refend en ecarte {seam['seam_holder']['gorge']}, "
          f"et {seam['seam_holder']['sans objet']} echantillons sont hors sujet\n"
          "      (canal de mortaise ouvert : il n'y a rien a joindre a cette "
          "hauteur)")
    print("    PROFIL DE CRETE a 30 cm du joint, bande par bande — c'est la "
          "MACHOIRE, mesuree :")
    for k, (a, b) in enumerate(seam["jaw"]):
        mark = "dent  " if a > b else "mortaise"
        print(f"      bande {k} (s {-LEAF_HALF_S + 2 * LEAF_HALF_S * k / TOOTH_BANDS:+.2f} "
              f"a {-LEAF_HALF_S + 2 * LEAF_HALF_S * (k + 1) / TOOTH_BANDS:+.2f}) : "
              f"tribord {a:.2f}  babord {b:.2f}   -> {mark} a tribord")
    print(f"    traversee verticale : {len(seam['vertical_holes'])} trou(s) ; "
          f"epaisseur minimale rencontree {seam['vertical_min']:.3f} m "
          "(les mortaises sont des POCHES)")
    for fit in report["fits"]:
        print(f"    course {fit['travel']:.2f} m : vantail x "
              f"{fit['leaf_x'][0]:+.2f} a {fit['leaf_x'][1]:+.2f} ; "
              f"engagement dans le logement {fit['overlap']:+.3f} m ; marge sous "
              f"{DOOR_HALF_X:.2f} : {fit['margin_out']:+.3f} m ;\n"
              f"      passe {fit['passe']:.2f} m ; jeux dans le fourreau "
              f"{fit['lateral']:+.3f} m lateral, {fit['vertical']:+.3f} m sous "
              "l'assise")
    print(f"    fourreau relu sur le binaire : demi-largeur utile "
          f"{report['fits'][0]['cavity_half_s']:.2f} m, sole a "
          f"{report['fits'][0]['sill_y']:+.2f}")

    print("\n  LE SURPLOMB, ET CE QUI LE PORTE")
    print(f"    cadre de la camera au plan du pont : "
          f"{report['frame_width']:.2f} m ; porte "
          f"{2 * DOOR_HALF_X:.2f} m, soit {100 * report['gate_cover']:.1f} pct")
    print(f"    demi-largeur de coque a s = {CITADEL_STATION:.0f} : "
          f"{report['hull_half']:.2f} m (taper du troncon 3) -> "
          f"{report['overhang']:.2f} m de poutre en l'air par bord")
    print(f"    le portique occupe x {PYLON_HEEL_X:.2f} a {PYLON_X1:.2f} : il "
          f"couvre le surplomb ENTIER, et son talon\n    mord le flanc de "
          f"{report['pylon_bite'][0]:.2f} a {report['pylon_bite'][1]:.2f} m "
          "(mesure sur le profil reel, taper compris)")

    clearance, floating, buried = report["conduit_ground"]
    print("\n  LE CONDUIT SUR SA PEAU (le talus de l'artere monte de 0,28 m)")
    print(f"    garde minimale au-dessus de la peau {clearance:.3f} m ; "
          f"flottement max {floating:.3f} m ; enterrement max {buried:.3f} m")

    if report["ecarts"]:
        print("\n  LES ECARTS AU TABLEAU DU BRIEF — assumes, mesures, et dits")
        for name, field, want, got, why in report["ecarts"]:
            print(f"    {name}.{field} : {got:+.2f} au lieu de {want:+.2f}")
            print(f"      {why}")

    print("\n  emissif par piece (m2, kit brut) : "
          + ", ".join(f"{n} {report['emissive_by_part'].get(n, 0.0):.2f}"
                      for n in PART_NAMES if report['emissive_by_part'].get(n)))
    for name in DESTRUCTIBLE:
        share = report["emissive_by_part"].get(name, 0.0) \
            / max(report["area_by_part"].get(name, 1.0), 1e-9)
        print(f"    {name} : {100 * share:.1f} pct de sa propre aire "
              "(regle des kits de ce niveau : 25 pct)")
    print("    Aucune autre piece n'en porte : le moteur les detruit SEULES.")

    print(f"\n  primitives : {report['primitives'][0]}/{report['primitives'][2]} "
          f"TEXCOORD_0, {report['primitives'][1]}/{report['primitives'][2]} TANGENT")
    print("  densite de texels (valeurs singulieres, triangle par triangle), "
          f"cible {TEXELS_PER_METER:.3f} tuile/m ({1 / TEXELS_PER_METER:.2f} m/tuile)")
    for name in PART_NAMES:
        d = report["density"].get(name)
        if not d:
            continue
        print(f"    {name:<17} {d['tiles_per_m_min']:.3f} a "
              f"{d['tiles_per_m_max']:.3f}, moyenne {d['tiles_per_m_mean']:.3f} "
              f"t/m ({d['m_per_tile_mean']:.2f} m/tuile), aniso "
              f"{d['anisotropy_max']:.2f}")

    print("\n  repartition en AIRE — kit brut, verrou ASSEMBLE, et ce qui en est VU")
    total = report["total_area"] or 1.0
    built_total = report["total_built"] or 1.0
    seen_total = report["total_seen"] or 1.0
    print(f"    {'materiau':<22} {'kit':>9} {'':>7}  {'assemble':>9} {'':>7}  "
          f"{'vu':>9} {'':>7}")
    for name, area in sorted(report["built_by_material"].items(),
                             key=lambda kv: -kv[1]):
        raw = report["area_by_material"].get(name, 0.0)
        seen = report["seen_by_material"].get(name, 0.0)
        print(f"    {name:<22} {raw:8.2f} m2 {100.0 * raw / total:5.1f} %  "
              f"{area:8.2f} m2 {100.0 * area / built_total:5.1f} %  "
              f"{seen:8.2f} m2 {100.0 * seen / seen_total:5.1f} %")
    print(f"    {'TOTAL':<22} {total:8.2f} m2          {built_total:8.2f} m2"
          f"          {seen_total:8.2f} m2")
    print(f"  octets     : {report['bytes']}")


def main() -> None:
    report = build()
    _print_report(report)
    if "--plate" in sys.argv:
        render_plate(report)


# ==========================================================================
# Planche de recette — `--plate`
# ==========================================================================
# ADR-0006 : un livrable de la forge n'est pas valide tant qu'il n'a pas ete
# rendu et REGARDE. La premiere vignette EST le test d'acceptation du brief —
# « en noir et blanc, emissifs coupes, bastion != relais != noyau != passage » —
# et la planche doit le MONTRER, pas l'affirmer.

TILE_W = 1440
SCENE_H = 660
PLAN_H = 460
CLOSE_H = 620
MOVE_H = 560                # les deux positions ouvertes : le cadre suffit
FRONT_H = 300
UV_H = 420

BACKDROP = baykit.BACKDROP
AMBIENT = baykit.AMBIENT
CAM_POS = cortege.CAM_POS
CAM_FORWARD = cortege.CAM_FORWARD
CAM_UP = cortege.CAM_UP
CAM_FOV_V = cortege.CAM_FOV_V

#: La station visee. La camera du jeu ne voit qu'une FENETRE de 16 m en `s` : de
#: l'aim + 3 m (le bas du cadre, ou vole le chasseur) a l'aim - 13 m. Le verrou
#: occupe s 239,4 a 246,0 ; viser 242,5 les y met tous.
ACCEPTANCE_AIM = 242.5
#: Les deux tourelles legeres de garde, aux stations du moteur
#: (`CortegeCitadel.TURRET_S`), a `TURRET_X` = 9,20 sur le pont du bastion.
GUARD_TURRETS = (0.40, 2.20)
GUARD_TURRET_X = 9.20
GUARD_SCALE = 0.5           # `CortegeTurret.LIGHT_GEOM_SCALE`


def _to_blender(v: Vector) -> Vector:
    return Vector((v.x, -v.z, v.y))


def _place(name: str, position: Vector, yaw: float = 0.0) -> list:
    """Importe UNE piece du kit et la pose. Comme le fera le moteur."""
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=OUTPUT)
    fresh = [o for o in bpy.context.scene.objects if o not in before]
    keep = [o for o in fresh if o.name.split(".")[0] == name]
    for obj in fresh:
        if obj not in keep:
            bpy.data.objects.remove(obj, do_unlink=True)
    for obj in keep:
        obj.location = _to_blender(position)
        # ⚠️ LE MODE DE ROTATION D'ABORD, ET C'EST UN DEFAUT TOTALEMENT SILENCIEUX.
        # L'importateur glTF pose `rotation_mode = 'QUATERNION'` sur tout ce qu'il
        # cree. Ecrire `rotation_euler` sur un objet en mode quaternion n'a AUCUN
        # effet : la valeur est rangee, jamais lue, et Blender ne dit rien. Sur
        # cette planche, le premier tirage a rendu les cinq pieces de BABORD
        # exactement par-dessus celles de tribord — un demi-verrou, et le cote
        # sabote de la vignette « trois quarts » etait le MEME que le cote intact.
        # ⚠️ Les trois kits precedents ecrivent la meme ligne (`build_spine_kit`,
        # `build_turret_kit`, `build_bay_kit`) : leurs yaw de planche — l'azimut
        # des tourelles, le miroir des entretoises d'epine — sont donc ignores
        # eux aussi. Signale au concepteur ; hors perimetre de ce brief.
        obj.rotation_mode = "XYZ"
        obj.rotation_euler = Euler((0.0, 0.0, yaw), "XYZ")
        obj.visible_shadow = False
    return keep


def _assemble(shift: float, travel: float = 0.0,
              relays: tuple[bool, bool] = (True, True),
              core: bool = True, shield: bool = True,
              turrets: bool = True) -> list:
    """Monte LE VERROU ENTIER, comme le fera `CortegeCitadel`.

    C'est la SEULE façon de juger le lot : le kit livre neuf pieces et aucune ne
    prouve quoi que ce soit seule. `relays` et `core` permettent de rendre le
    verrou APRES sabotage ; `travel` est LA COURSE DES VANTAUX — 0 ferme, 4,25
    ouvert — et c'est la seule chose que le moteur ajoutera a la pose.

    ⚠️ LA COURSE EST UNE TRANSLATION EN X, ET SON SIGNE EST CELUI DU BORD. Le
    vantail est modelise tribord, origine au bout interieur ; la copie babord
    subit le yaw de pi, donc sa course s'ecrit -travel dans le repere parent. Le
    moteur n'aura pas d'autre arithmetique de cote a faire.
    """
    placed: list = []
    base = -CITADEL_STATION + shift

    def pose(name: str, yaw: float = 0.0, dx: float = 0.0) -> None:
        placed.extend(_place(name, Vector((dx, SEAT[name],
                                           base + ASSEMBLY_Z[name])), yaw))

    for side, yaw in ((1.0, 0.0), (-1.0, math.pi)):
        pose("citadel_housing", yaw)
        pose("citadel_leaf", yaw, side * travel)
        pose("citadel_pylon", yaw)
        pose("citadel_bastion", yaw)
        pose("citadel_crown", yaw)
        index = 0 if side > 0.0 else 1
        if relays[index]:
            pose("citadel_relay", yaw)
            pose("citadel_conduit", yaw)
        if turrets:
            for ds in GUARD_TURRETS:
                placed += _light_turret(
                    Vector((side * GUARD_TURRET_X,
                            SEAT["citadel_crown"], base - ds)),
                    math.radians(-34.0 if ds < 1.0 else 26.0) * side)
    if core:
        pose("citadel_core")
    if shield and relays[0] and relays[1]:
        pose("citadel_shield")
    return placed


def _light_turret(centre: Vector, aim: float) -> list:
    """Une tourelle de garde a l'echelle LEGERE — celle que le moteur pose deja.

    ⚠️ Elles ne sont PAS modelees par ce brief (« elles existent : `turret_kit` en
    echelle legere »). Elles sont ici parce qu'une couronne rendue sans elles ne
    montrerait pas le conflit d'emprise que le compte-rendu signale.
    """
    pieces = turretkit._assemble_turret(centre, 2, aim=aim)
    anchor = _to_blender(centre)
    for obj in pieces:
        # Le yaw pose par `build_turret_kit` a ete ecrit sur un objet en mode
        # QUATERNION : il est range mais inerte (voir `_place`). On le relit AVANT
        # de changer de mode — apres, Blender l'aurait recalcule depuis le
        # quaternion identite et l'azimut aurait ete perdu pour de bon.
        wanted = tuple(obj.rotation_euler)
        obj.rotation_mode = "XYZ"
        obj.rotation_euler = wanted
        obj.location = anchor + (obj.location - anchor) * GUARD_SCALE
        obj.scale = (GUARD_SCALE, GUARD_SCALE, GUARD_SCALE)
    return pieces


def _tile_acceptance(path: str, report: dict, greyscale: bool,
                     travel: float = 0.0, height: int = SCENE_H) -> None:
    """LE TEST D'ACCEPTATION : le verrou entier, a la camera du jeu.

    ⚠️ EN NOIR ET BLANC ET EMISSIFS COUPES, C'EST LE CRITERE QUI DECIDE DU LOT.
    Une vignette par piece ne prouverait rien : ce qui est demande est qu'on
    distingue bastion, relais, noyau et passage DANS LE MEME CADRE, sans aide de
    couleur. Le chasseur reel est a sa place de jeu — c'est lui qui donne
    l'echelle, et c'est a sa taille que la question se pose.
    """
    baykit._plate_reset()
    shift = baykit._game_shift(ACCEPTANCE_AIM)
    decor = baykit._import(HULL, "Decor", Vector((0.0, 0.0, shift)))
    kits = _assemble(shift, travel)
    fighter = baykit._import(FIGHTER, "Player", Vector((4.6, 0.0, 3.4)))
    if greyscale:
        baykit._to_greyscale(decor + kits + fighter)
    baykit._plate_lights()
    camera = baykit._plate_camera("game", _to_blender(CAM_POS),
                                  _to_blender(CAM_FORWARD),
                                  _to_blender(CAM_UP), CAM_FOV_V)
    passe = 2.0 * travel
    if greyscale and travel <= 0.0:
        baykit._label(
            camera, "TEST D'ACCEPTATION — NOIR ET BLANC, EMISSIFS COUPES : "
            "PORTE FERMEE, ET ON DOIT LIRE « CA S'OUVRE AU MILIEU »",
            -0.97, 0.91, 0.038, TILE_W, height, (1.0, 0.88, 0.55))
        baykit._label(
            camera, "trois signaux, et aucun n'est une couleur. Le TABLEAU : "
            "les 2,40 m internes de chaque vantail sont plus epais EN HAUT — "
            "0,96 m de dessus contre 0,60.\nLa MACHOIRE : trois dents claires, "
            "trois mortaises de 0,60 m de creux, et la PHASE S'INVERSE en "
            "franchissant l'axe.",
            -0.97, 0.845, 0.026, TILE_W, height)
        baykit._label(
            camera, "Le REFEND : au milieu exact, une gorge de 0,14 m sur "
            "0,60 m de creux traverse toute l'epaisseur.\nLes six autres "
            "pieces du kit n'ont pas bouge d'un micron — memes octets.",
            -0.97, 0.725, 0.026, TILE_W, height, (0.72, 0.84, 1.0))
    elif greyscale:
        baykit._label(
            camera, f"COURSE {travel:.2f} m — "
            + ("A MI-CHEMIN" if travel < LEAF_TRAVEL - 1e-6
               else "OUVERTE : LA ROUTE EST LA"),
            -0.97, 0.91, 0.038, TILE_W, height, (1.0, 0.88, 0.55))
        baykit._label(
            camera, f"passe {passe:.2f} m — le corps du Specter-9 en fait 1,76 "
            f"(ADR-0034), soit {passe / 1.76:.1f} fois sa largeur. Les deux "
            f"vantaux vont de {travel:+.2f} a {travel + LEAF_LEN:+.2f} : rien "
            f"ne sort de {DOOR_HALF_X:.2f}.",
            -0.97, 0.845, 0.026, TILE_W, height)
    else:
        baykit._label(
            camera, "LE MEME CADRE, EN COULEUR — ce que l'emissif AJOUTE a une "
            "fonction deja lisible en geometrie",
            -0.97, 0.91, 0.038, TILE_W, height, (1.0, 0.88, 0.55))
        baykit._label(
            camera, "deux lampes de relais et une ceinture de noyau, et RIEN "
            "d'autre n'est emissif : les vantaux, les logements, les bastions, "
            "les couronnes, les portiques et les conduits sont eteints.",
            -0.97, 0.845, 0.026, TILE_W, height)
        baykit._label(
            camera, "Un vantail qui brillerait entrerait en concurrence avec "
            "les deux seuls signaux d'etat du verrou — c'est la regle du "
            "BRIEF-0097, plus dure encore que celle du LOT 2.",
            -0.97, 0.785, 0.026, TILE_W, height, (0.72, 0.84, 1.0))
    baykit._label(
        camera, "camera de graybox.tscn sans retouche (0, 14, 5), FOV 62, "
        "70 deg sous l'horizontale ; Specter-9 reel a sa place de jeu ; "
        "tourelles de garde a l'echelle LEGERE",
        -0.97, -0.93, 0.026, TILE_W, height, (0.72, 0.84, 1.0))
    baykit._render(path, TILE_W, height)


def _tile_plan(path: str, report: dict, travel: float = 0.0) -> None:
    """LES QUATRE AXES, VUS D'EN HAUT, EN NOIR ET BLANC.

    La camera du jeu est a 20 deg de la VERTICALE : le plan est donc, a peu de
    chose pres, ce que le joueur voit. C'est la vue ou les quatre signatures se
    separent le mieux — une ligne qui traverse, deux masses, deux branchements,
    un disque — et c'est aussi celle qui montre la DENTURE, qui n'existe que la.
    """
    baykit._plate_reset()
    decor = baykit._import(HULL, "Decor", Vector((0.0, 0.0, 0.0)))
    kits = _assemble(0.0, travel)
    baykit._to_greyscale(decor + kits)
    baykit._plate_lights()
    centre = -(CITADEL_STATION + 3.1)
    camera = baykit._plate_camera(
        "plan", _to_blender(Vector((0.0, 30.0, centre))),
        _to_blender(Vector((0.0, -1.0, 0.0))),
        _to_blender(Vector((0.0, 0.0, -1.0))),
        math.radians(30.0), ortho=PLAN_H * 42.0 / TILE_W)
    baykit._label(
        camera, "LE PLAN, EN NOIR ET BLANC — proue en bas, 42 m de large "
        f"(course {travel:.2f} m)",
        -0.985, 0.88, 0.048, TILE_W, PLAN_H, (1.0, 0.88, 0.55))
    baykit._label(
        camera, "la camera du jeu est a 20 deg de la VERTICALE : ce plan est, "
        "a peu de chose pres, ce que le joueur voit.\nLa MACHOIRE s'y lit — six "
        "bandes, et la phase change au milieu. Aux deux bouts, la FENTE du "
        "logement dit ou va le vantail.",
        -0.985, -0.80, 0.036, TILE_W, PLAN_H)
    baykit._render(path, TILE_W, PLAN_H)


def _tile_close(path: str, report: dict) -> None:
    """LA MACHOIRE DE PRES — la preuve du LOT 4, en noir et blanc.

    ⚠️ CETTE VIGNETTE EST LE JUGE DU BRIEF, PAS UN PORTRAIT. La capture du LOT 2
    a lu la denture d'alors comme un creneau de rempart : « pas de tableau, pas
    de ligne de refend, pas de deux moities ». On regarde donc le joint a la
    distance ou la question se pose, et sans une couleur : trois dents claires
    d'un cote, trois mortaises noires de l'autre, la phase qui s'inverse sur
    l'axe, et le tableau qui encadre les 4,80 m centraux.

    Le cote babord est rendu SABOTE (relais et conduit retires) : la meme image
    montre donc aussi a quoi sert le partage en neuf nœuds.
    """
    baykit._plate_reset()
    decor = baykit._import(HULL, "Decor", Vector((0.0, 0.0, 0.0)))
    parts = _assemble(0.0, shield=False)
    # ⚠️ LE DECOR AUSSI, ET C'EST UNE ERREUR DE PREMIER TIRAGE. Convertir le seul
    # kit laissait les conduits magenta et la lisse cyan de la COQUE en couleur
    # au milieu d'une vignette annoncee « noir et blanc » : le test perdait sa
    # valeur de preuve la ou il est justement le juge.
    baykit._to_greyscale(decor + parts)
    baykit._plate_lights()
    # ⚠️ CADRE CENTRE SUR L'AXE, ET C'EST LE SUJET QUI L'IMPOSE. Vise a 3,4 m a
    # tribord, la vignette ne montrait qu'un demi-verrou : la comparaison
    # « intact / sabote » qu'elle est censee porter tombait hors champ a gauche.
    target = Vector((0.0, -3.90, -CITADEL_STATION))
    eye = target + Vector((2.6, 6.4, 6.4))
    forward, up = turretkit._look_at(eye, target)
    camera = baykit._plate_camera("close", _to_blender(eye),
                                  _to_blender(forward), _to_blender(up),
                                  math.radians(36.0))
    baykit._label(
        camera, "LA MACHOIRE, EN NOIR ET BLANC — trois dents par vantail, "
        "chacune en face d'une mortaise",
        -0.97, 0.91, 0.036, TILE_W, CLOSE_H, (1.0, 0.88, 0.55))
    baykit._label(
        camera, f"l'epaisseur (1,20 m) est coupee en {TOOTH_BANDS} bandes de "
        f"{2 * LEAF_HALF_S / TOOTH_BANDS:.2f} m ; ce vantail porte les bandes "
        f"{', '.join(str(k) for k in TOOTH_MINE)}, le yaw de pi du moteur les "
        f"renvoie en {', '.join(str(TOOTH_BANDS - 1 - k) for k in TOOTH_MINE)}\n"
        "— le complementaire exact, donc jamais une dent en face d'une dent. "
        "Au milieu, la GORGE DE REFEND : les dents s'arretent 7 cm avant le "
        "plan de joint, les corps s'y touchent.",
        -0.97, 0.83, 0.026, TILE_W, CLOSE_H)
    baykit._label(
        camera, f"mortaise de {LEAF_H - TOOTH_BED_Y:.2f} m de creux sur un lit "
        f"PLEIN a {SEAT['citadel_leaf'] + TOOTH_BED_Y:+.2f} (aucune fente "
        f"traversante) ; gorge de refend {2 * TOOTH_TIP_GAP:.2f} m ; tableau "
        f"sur {JAMB_X:.2f} m ; "
        f"{report['triangles']} triangles pour tout le kit "
        f"(budget {TRI_BUDGET_KIT})",
        -0.97, -0.91, 0.026, TILE_W, CLOSE_H, (0.72, 0.84, 1.0))
    baykit._render(path, TILE_W, CLOSE_H)


def _tile_front(path: str, report: dict, travel: float = 0.0) -> None:
    """LE SURPLOMB, ET CE QUI LE PORTE — elevation de face, a l'echelle du cadre.

    ⚠️ CETTE VIGNETTE EXISTE POUR UN DEFAUT MESURE, PAS POUR FAIRE JOLI. Capture
    du 2026-09-04 : « les deux tiers exterieurs de la poutre surplombent le vide,
    etoiles visibles dessous ». Le cadre est cale sur la LARGEUR REELLE de la
    camera de jeu au plan du pont (41,6 m) : on voit donc d'un coup la coque, le
    surplomb, et le portique qui va chercher la lisse d'epaule.
    """
    baykit._plate_reset()
    baykit._import(HULL, "Decor", Vector((0.0, 0.0, 0.0)))
    _assemble(0.0, travel, turrets=False)
    baykit._plate_lights()
    # ⚠️ LE PLAN DE CAMERA EST A 0,20 m DE LA PORTE, ET NON A 9 m. En
    # orthographique, les rayons partent du PLAN de la camera : neuf metres de
    # bordé s'interposaient entre elle et le verrou, et la vignette censee
    # montrer le surplomb montrait un pont vide. Centre vertical a -6,00 pour que
    # la section de coque tienne dans le cadre sans quatre metres de ciel.
    # Une lumiere de face, POUR CETTE VIGNETTE SEULE : les trois soleils de jeu
    # eclairent d'en haut et de trois quarts arriere, et une elevation frontale
    # d'anthracite sur fond bleu nuit n'y rend aucune arete.
    fill = bpy.data.lights.new("FrontFill", type="SUN")
    fill.energy = 1.9 * math.pi
    fill.color = (1.0, 0.97, 0.93)
    fill.angle = 0.0
    lamp = bpy.data.objects.new("FrontFill", fill)
    lamp.rotation_euler = _to_blender(
        Vector((0.10, -0.35, -1.0)).normalized()).to_track_quat(
            "-Z", "Y").to_euler()
    bpy.context.collection.objects.link(lamp)
    camera = baykit._plate_camera(
        "front", _to_blender(Vector((0.0, -5.6, -(CITADEL_STATION - 0.8)))),
        _to_blender(Vector((0.0, 0.0, -1.0))),
        _to_blender(Vector((0.0, 1.0, 0.0))),
        math.radians(30.0),
        ortho=FRONT_H * report["frame_width"] / TILE_W)
    baykit._label(
        camera, "DE FACE, A LA LARGEUR EXACTE DU CADRE DE JEU "
        f"({report['frame_width']:.1f} m au plan du pont)",
        -0.985, 0.80, 0.058, TILE_W, FRONT_H, (1.0, 0.88, 0.55))
    baykit._label(
        camera, f"coque {2 * report['hull_half']:.2f} m — porte "
        f"{2 * DOOR_HALF_X:.2f} m ({100 * report['gate_cover']:.0f} pct du "
        f"cadre) — donc {report['overhang']:.2f} m en l'air par bord, et le "
        f"portique les couvre en entier (x {PYLON_HEEL_X:.2f} a "
        f"{PYLON_X1:.2f}).",
        -0.985, -0.72, 0.046, TILE_W, FRONT_H)
    baykit._label(
        camera, f"course {travel:.2f} m : chaque vantail va de "
        f"{travel:+.2f} a {travel + LEAF_LEN:+.2f}, son logement de "
        f"{HOUSING_X[0]:.2f} a {HOUSING_X[1]:.2f} — recouvrement "
        f"{report['fits'][0]['overlap']:.2f} m, et rien ne sort de "
        f"{DOOR_HALF_X:.2f}.",
        -0.985, -0.87, 0.046, TILE_W, FRONT_H, (0.72, 0.84, 1.0))
    baykit._render(path, TILE_W, FRONT_H)


def _tile_uv(path: str, report: dict) -> None:
    baykit._plate_reset()
    shift = baykit._game_shift(ACCEPTANCE_AIM)
    decor = baykit._import(HULL, "Decor", Vector((0.0, 0.0, shift)))
    kits = _assemble(shift, LEAF_TRAVEL * 0.5, turrets=False)
    baykit._apply_checker(decor + kits)
    baykit._plate_lights()
    camera = baykit._plate_camera("uv", _to_blender(CAM_POS),
                                  _to_blender(CAM_FORWARD),
                                  _to_blender(CAM_UP), CAM_FOV_V)
    worst = max(report["density"].values(),
                key=lambda d: d.get("anisotropy_max", 0.0))
    baykit._label(
        camera, "DAMIER UV — grande case = 1 tuile de 5,00 m, petite = 62,5 cm ; "
        "la MEME echelle sur la coque et sur les quatre kits",
        -0.97, 0.90, 0.036, TILE_W, UV_H, (1.0, 0.88, 0.55))
    baykit._label(
        camera, f"projection en boite {TEXELS_PER_METER:.3f} tuile/m ; "
        f"anisotropie max mesuree sur le kit {worst['anisotropy_max']:.2f} "
        "(borne theorique de la methode : 1,73)",
        -0.97, 0.82, 0.028, TILE_W, UV_H)
    baykit._render(path, TILE_W, UV_H)


def render_plate(report: dict) -> None:
    ak.reset_scene()
    staging = tempfile.mkdtemp(prefix="aegis-citadelkit-plate-")
    tiles: list[tuple[str, int]] = []
    try:
        # ⚠️ L'ORDRE EST CELUI DE LA DEMONSTRATION, PAS CELUI DU CONFORT. Le
        # brief demande la porte AUX TROIS POSITIONS et le test noir et blanc :
        # ferme d'abord — c'est la seule position ou la question « est-ce que ca
        # s'ouvre au milieu ? » se pose — puis a mi-course, puis ouverte.
        path = os.path.join(staging, "bw_closed.png")
        _tile_acceptance(path, report, greyscale=True, travel=0.0)
        tiles.append((path, SCENE_H))
        path = os.path.join(staging, "bw_half.png")
        _tile_acceptance(path, report, greyscale=True,
                         travel=LEAF_TRAVEL * 0.5, height=MOVE_H)
        tiles.append((path, MOVE_H))
        path = os.path.join(staging, "bw_open.png")
        _tile_acceptance(path, report, greyscale=True, travel=LEAF_TRAVEL,
                         height=MOVE_H)
        tiles.append((path, MOVE_H))
        path = os.path.join(staging, "close.png")
        _tile_close(path, report)
        tiles.append((path, CLOSE_H))
        path = os.path.join(staging, "plan.png")
        _tile_plan(path, report)
        tiles.append((path, PLAN_H))
        path = os.path.join(staging, "front.png")
        _tile_front(path, report)
        tiles.append((path, FRONT_H))
        path = os.path.join(staging, "color.png")
        _tile_acceptance(path, report, greyscale=False, travel=LEAF_TRAVEL,
                         height=MOVE_H)
        tiles.append((path, MOVE_H))
        path = os.path.join(staging, "uv.png")
        _tile_uv(path, report)
        tiles.append((path, UV_H))
        os.makedirs(os.path.dirname(PLATE), exist_ok=True)
        turretkit._compose(tiles, PLATE)
    finally:
        for leftover in os.listdir(staging):
            os.remove(os.path.join(staging, leftover))
        os.rmdir(staging)


if __name__ == "__main__":
    main()
