"""build_specter_9.py — coque 3D du Specter-9, chasseur du joueur.

    ./scripts/build-hull.sh specter_9          (JAMAIS `blender45 -b -P` a la main :
    ./scripts/build-hull.sh --check specter_9   le script force `-t 1`, sans quoi les
                                                tangentes divergent d'un run a l'autre)

Produit `assets/imported/models/ships/specter_9.glb` : une coque + QUATRE pieces
mobiles exportees en nœuds glTF separes (`Flap_L/R`, `Nozzle_L/R`).

Le script EST la source de l'asset (ADR-0008) : aucun `.blend` n'est versionne.
Il est deterministe (aucun alea non seede) et s'auto-valide : `ak.export_hull()`
relit le `.glb` produit et echoue bruyamment si la bounding box, le budget de
triangles, les materiaux, le centrage du pivot ou les points d'attache sortent
du contrat.

Repere d'auteur (ADR-0008) : nez -Y, dessus +Z, **babord +X** (cf. aegis_kit).


PASSE DE PLAN — BRIEF-0034 (lire ADR-0014 d'abord)
==================================================
BRIEF-0033 avait pose comme prealable de **conserver le delta** (« le probleme
est le profil, pas le plan »). C'etait une erreur de diagnostic, tiree d'un
rapport de boite englobante — une statistique qui mesure la boite, jamais la
repartition des masses dedans. ADR-0014 la corrige et autorise la reprise du
PLAN de la planche de reference, derives comprises.

Ce que ce brief change, et rien d'autre : la **vue de dessus**.

1. **L'aile cesse d'etre un delta.** `PLANFORM` avait sa largeur maximale a
   67 % de la longueur puis un culot plein : l'aile remplissait tout l'arriere.
   Le bord d'attaque passe de 52 a **62 deg de fleche**, la largeur maximale
   recule a 73 % (y = 0,580) et le bord de fuite, jusqu'ici droit, est **rake a
   28 deg** : la corde s'effondre en arriere du bout d'aile. L'envergure, elle,
   NE BOUGE PAS (0,875 m) — c'est la corde qui tombe, pas la portee.
2. **Un fuselage central porteur.** `FUSELAGE` retrecit (0,232 -> 0,172 de
   demi-largeur, soit 0,344 m = 20 % de l'envergure, dans la fourchette du
   brief) mais devient un VOLUME : le plan d'aile ne part plus de 0,65 fois
   l'epine mais de **0,34** (`WING_ROOT_FRAC`), ce qui creuse une marche de
   9 cm au flanc du fuselage la ou il n'y avait qu'un bombement continu.
3. **Une rainure, pas une jointure.** `GUTTER_DEPTH` creuse un caniveau de
   30 mm au pied de cette marche : c'est lui qui separe optiquement le
   fuselage des nacelles au lieu de les laisser fondre l'un dans l'autre.
4. **Deux nacelles longues.** Ecartees (0,268 -> 0,352), legerement affinees
   (rayon x 0,915) et surtout **prolongees vers l'avant** par une epaule
   (`SHOULDER`) qui court de y = -0,36 a y = 0,86. Nacelle + epaule = 1,59 m,
   soit **65 % de la longueur** (le brief en demandait 60-75 %).
5. **Deux derives inclinees** a 30 deg vers l'exterieur, sur le dessus des
   nacelles (`FIN`). Elles remplacent les rails verticaux de bout d'aile, qui
   n'existaient que parce que BRIEF-0033 s'interdisait les derives ; il ne
   reste au bout d'aile qu'une **lisse basse** (`RAIL`), qui epaissit la lame.
6. **Une tuyere d'axe** en bout de fuselage (`TAIL_NOZZLE`) : c'est elle qui
   fait lire le fuselage comme porteur jusqu'a la poupe, et non comme une
   arete qui s'arrete.

Ce qui est CONSERVE de BRIEF-0033, sans y toucher : le profil superpose, la
densite de panneautage, les nacelles en volumes propres, les 4 pieces mobiles,
les 10 points d'attache.


PASSE FUSELAGE ET PIECES MOBILES — BRIEF-0033
=============================================
La passe de detail de BRIEF-0031 avait sorti la coque du « jouet » en vue de
dessus, mais la vue de profil restait une **plaque** : 0,516 m de haut pour
2,46 m de long (21 %), aucune structure verticale, des nacelles noyees dans
l'aile. Six leviers, par ordre de rendement :

1. **Profil epaissi ET stratifie.** Le corps passe de 0,315 a 0,380 m
   (CROWN/BELLY), mais surtout la coque cesse d'etre UNE lentille : elle empile
   desormais six couches lisibles de bas en haut — quille ventrale, ecopes de
   nacelle, plan d'aile, corps de fuselage, arete dorsale, verriere. C'est
   l'empilement, pas l'epaisseur brute, qui fait la lecture « appareil ».
2. **Repartition asymetrique de l'epaisseur.** La camera de jeu regarde a 20 deg
   de la verticale : ce qu'on ajoute AU-DESSUS elargit la silhouette vue de
   dessus, ce qu'on ajoute EN DESSOUS est gratuit. 55 % de la hauteur est donc
   sous le plan d'aile, et les volumes dorsaux sont ETROITS (arete de 0,19 m de
   large sur une envergure de 1,75 m).
3. **Nacelles en volumes propres** : ecartees (0,235 -> 0,268), descendues
   (-0,030 -> -0,062), avec col, collier, jonc, et une **ecope ventrale** qui les
   relie a l'aile. Elles saillent de 0,13 m sous l'aile.
4. **Nez plus long** : la verriere recule de 0,13 m, le maitre-couple avant
   s'affine (CROWN et FUSELAGE abaisses en avant de y = -0,80). Le rapport
   longueur/envergure ne bouge pas : c'est la REPARTITION des masses qui change.
5. **Presence verticale sans derive** : deux **rails verticaux de bout d'aile**
   (0,20 m de haut, feux cyan sur l'arete) et une **arete dorsale basse** a
   flancs verticaux. Aucune derive inclinee — voir la note IP ci-dessous.
6. **Pieces mobiles** (`ak.moving_part`, kit etendu pour ce brief) : volets de
   bord de fuite et couronnes de petales de tuyere, chacun avec son origine sur
   son articulation.

Regle de placement inchangee : **si une surface n'est pas visible depuis une
camera a 20 deg de la verticale, ce qu'on y met n'existe pas.**


REFERENCE ET LIMITE IP  (revu par ADR-0014)
===========================================
Cible : `assets/reference/inspiration/reference_specter_9_design_sheet.png`
(planche TIERCE). ADR-0009 l'autorisait comme inspiration ; **ADR-0014 va plus
loin pour CETTE coque seulement** et autorise la reprise de son ARCHITECTURE :
fuselage porteur, nacelles flanquantes, ailes en lames, doubles derives
inclinees. La clause « les assets produits restent originaux » d'ADR-0009 ne
s'applique plus ici — et continue de s'appliquer partout ailleurs dans le jeu.

DEUX traits restent EXCLUS, et ce n'est pas une demi-mesure de prudence :
  * la livree tricolore a bandes rouges -> la palette du kit reste seule
    maitresse (blanc casse, bleu profond, or ; rouge en marquage restreint).
    Un appareil tricolore serait un corps etranger dans une flotte ivoire et
    bleue, independamment de toute question de droits ;
  * tout badge numerote, chiffre, texte, logo ou insigne -> aucun, nulle part.

Si le projet devait etre distribue, ce fichier et le .glb qu'il produit sont
les premiers a refaire (ADR-0014, §Consequence).
"""

from __future__ import annotations

import math
import os
import sys

import bmesh

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "lib"))
_REPO = os.path.dirname(os.path.dirname(_HERE))

import aegis_kit as ak  # noqa: E402  (doit suivre l'ajout au sys.path)

# ==========================================================================
# Contrat (ADR-0008 pour les dimensions, ADR-0011 pour le budget)
# ==========================================================================

#: Fourchette de hauteur imposee par BRIEF-0034 (0,62-0,72 : le plafond monte
#: de 4 cm pour loger les derives). Le contrat du kit ne sait borner qu'un
#: PLAFOND : le plancher est verifie a la main en fin de build, sinon un
#: vaisseau reste plat en toute conformite.
MIN_HEIGHT_Y = 0.62
MAX_HEIGHT_Y = 0.72

CONTRACT = ak.HullContract(
    name="Specter-9",
    width_x=1.75,       # Godot X — INCHANGE (contrat de gameplay : hitbox)
    length_z=2.46,      # Godot Z — INCHANGE
    # BRIEF-0034 : 0,62-0,72 m, soit 25-29 % de la longueur. Cela DEPASSE la
    # fourchette indicative d'ADR-0008 (15-25 %), et c'est explicitement
    # autorise par le brief : le defaut a corriger etait la platitude.
    max_height_y=MAX_HEIGHT_Y,
    tri_budget=60_000,  # ADR-0011 (releve depuis 15 000)
    required_materials=ak.MATERIAL_ORDER,  # les 7 : la planche les utilise tous
    required_attach_points=(
        "Muzzle_L",       # twin de nez, babord   (power 1+)
        "Muzzle_R",       # twin de nez, tribord
        "Muzzle_Wing_L",  # canon d'aile, babord  (power 3)
        "Muzzle_Wing_R",  # canon d'aile, tribord
        "Muzzle_C",       # canon d'axe central   (power 4)
        "Muzzle_Tip_L",   # pod de bout d'aile, babord (power 5)
        "Muzzle_Tip_R",   # pod de bout d'aile, tribord
        "Engine_L",
        "Engine_R",
        "Cockpit",
    ),
)

OUTPUT = os.path.join(_REPO, "assets/imported/models/ships/specter_9.glb")

SEED = 90210  # graine unique du Specter-9 (determinisme des greebles)

#: Echelle de repetition de la feuille de detail (ADR-0011 §2), en tuiles/metre.
#: Validee au rendu par BRIEF-0031 : une tuile couvre 25 cm, soit ~7 tuiles en
#: envergure et ~10 en longueur. Le brief demande de ne pas y toucher.
TEXELS_PER_METER = 4.0

HALF_L = CONTRACT.length_z / 2.0   # 1.230 — nez en -Y, poupe en +Y
HALF_W = CONTRACT.width_x / 2.0    # 0.875 — bout d'aile

# ==========================================================================
# Tables de profil
# ==========================================================================

# Demi-envergure de la coque (planform). BRIEF-0034 : c'est LA table qui change.
#
#   avant (delta)          apres (lame en fleche)
#   ------------------     -----------------------------------------------
#   fleche de 52 deg       fleche de **63,5 deg**, une seule pente de
#                          y = -0,860 au bout d'aile : le bord d'attaque est
#                          droit, comme sur la planche
#   largeur max a 67 %     largeur max a **81 %** (y = 0,760)
#   puis culot plein       bord de fuite quasi transversal derriere le bout
#     jusqu'a 85 %           d'aile : la corde s'effondre en 10 cm
#
# La correction decisive n'est pas la fleche (28 deg de l'axe avant, 27 apres —
# la planche est a 27) mais le **placement longitudinal** : la version
# BRIEF-0033 atteignait sa largeur maximale 0,34 m trop tot et etait donc
# systematiquement plus large que la planche dans toute la moitie avant. Le
# nez, lui, passe de 0,136 a 0,068 de demi-envergure a y = -0,86 — il devient
# l'aiguille que la planche montre, et c'est cette aiguille qui fait lire un
# fuselage porteur plutot qu'une pointe de triangle.
#
# L'envergure ne bouge pas d'un millimetre — 0,875 — parce que c'est un contrat
# de gameplay (hitbox, `Muzzle_Tip_L/R`).
#
# Le bout d'aile tombe DERRIERE la charniere de volet (0,689), il appartient
# donc au volet. Ce n'est pas un probleme pour la boite englobante : le volet
# tourne autour d'un axe parallele a X, transformation qui laisse |x| invariant.
# La largeur du vaisseau ne peut pas changer en animation.
PLANFORM: list[tuple[float, float]] = [
    (-1.2300, 0.0000),   # pointe du nez
    (-1.1500, 0.0147),
    (-1.0800, 0.0276),
    (-0.9800, 0.0459),
    (-0.9000, 0.0607),
    (-0.8600, 0.0680),   # emplanture du bord d'attaque
    (-0.6600, 0.1676),
    (-0.5400, 0.2274),
    (-0.4000, 0.2971),
    (-0.2400, 0.3768),
    (-0.0500, 0.4715),
    (0.1300, 0.5622),
    (0.3100, 0.6519),
    (0.4700, 0.7316),
    (0.6100, 0.8013),
    (0.7600, 0.8750),    # BOUT D'AILE — largeur max, a 81 % de la longueur
    (0.8100, 0.6175),
    (0.8600, 0.3600),    # culot, entre les deux nacelles
]

# Demi-largeur du fuselage central (au-dela : l'aile, mince).
# BRIEF-0034 : 0,232 -> 0,172, soit **0,344 m de large = 20 % de l'envergure**
# (le brief demandait 0,32-0,40 m). Retrecir le fuselage peut sembler contraire
# a « fuselage porteur » ; ce n'est pas la largeur qui le rend porteur mais le
# fait qu'il ait des FLANCS — cf. `WING_ROOT_FRAC` et `GUTTER_DEPTH`. Un
# fuselage large et fondu dans l'aile ne lit pas ; un fuselage etroit a marche
# franche lit de tres loin.
FUSELAGE: list[tuple[float, float]] = [
    (-1.2300, 0.000),
    (-1.1500, 0.020),
    (-1.0800, 0.032),
    (-0.9800, 0.050),
    (-0.8800, 0.070),
    (-0.7800, 0.092),
    (-0.6600, 0.116),
    (-0.5400, 0.136),
    (-0.4000, 0.152),
    (-0.2400, 0.164),
    (-0.0500, 0.170),
    (0.1300, 0.174),
    (0.3100, 0.176),
    (0.4700, 0.176),
    (0.6100, 0.174),
    (0.7550, 0.170),
    (0.8600, 0.164),
]

# Hauteur de l'epine dorsale (z du sommet, sur l'axe).
# BRIEF-0033 : sommet 0.165 -> 0.195, mais surtout la courbe est RECULEE. Le
# maitre-couple etait a y = 0.05 ; il est desormais a y = 0.22, et l'avant est
# abaisse. C'est ce deplacement, plus que le gain de 3 cm, qui allonge le nez.
#: BRIEF-0034 : le sommet gagne 1 cm (0,195 -> 0,205). Le fuselage ayant perdu
#: 6 cm de largeur, sans cela il aurait perdu du volume au lieu d'en gagner.
CROWN: list[tuple[float, float]] = [
    (-1.2300, 0.000),
    (-1.1500, 0.026),
    (-1.0800, 0.040),
    (-0.9250, 0.070),
    (-0.8120, 0.094),
    (-0.6910, 0.122),
    (-0.5510, 0.152),
    (-0.4130, 0.174),
    (-0.2410, 0.192),
    (0.0540, 0.202),
    (0.2190, 0.205),
    (0.4180, 0.203),
    (0.5730, 0.196),
    (0.7450, 0.186),
    (0.8600, 0.178),
]

# Profondeur du ventre (z du bas, sur l'axe ; valeurs negatives).
BELLY: list[tuple[float, float]] = [
    (-1.2300, 0.000),
    (-1.1500, -0.024),
    (-1.0800, -0.036),
    (-0.9250, -0.064),
    (-0.8120, -0.086),
    (-0.6910, -0.110),
    (-0.5510, -0.136),
    (-0.4130, -0.158),
    (-0.2410, -0.172),
    (0.0540, -0.182),
    (0.2190, -0.185),
    (0.4180, -0.183),
    (0.5730, -0.177),
    (0.7450, -0.168),
    (0.8600, -0.160),
]

# ==========================================================================
# Volets de bord de fuite (pieces mobiles)
# ==========================================================================
#
# Un volet ne peut pas etre POSE sur l'aile : il faut que l'aile s'arrete la ou
# il commence, sinon la piece traverse la coque des la premiere image d'anim.
# La coque est donc **echancree** : en arriere de `FLAP_HINGE_Y`, la section
# s'arrete a `FLAP_ROOT_X` au lieu d'aller jusqu'au bord d'attaque. Au repos le
# volet remplit exactement l'echancrure — la silhouette vue de dessus est donc
# celle d'avant, au jeu de charniere pres.

FLAP_HINGE_Y = 0.7600     # station de l'echancrure (deja une station de base)
FLAP_WALL_Y = 0.7570      # station juste devant : les deux forment la cloison
#: BRIEF-0034 : l'emplanture recule de 0,600 a 0,530. Elle doit rester en
#: dehors de la nacelle, dont le bord externe est desormais a 0,502 — 28 mm de
#: garde. Au-dela, le volet traverserait le fuseau des la premiere image.
FLAP_ROOT_X = 0.5300      # abscisse d'emplanture de l'echancrure
FLAP_SIDE_GAP = 0.0020    # jeu lateral volet / cloison d'emplanture

#: Jeu de charniere, en Y. Il n'est pas decoratif : le point du volet le plus
#: eloigne de l'axe de charniere avance de `d * sin(theta)` quand on braque.
#: En deca de ce jeu, le volet mange la cloison. `_flap_travel_limit()` mesure
#: le plafond reel sur le maillage et l'imprime a chaque build — BRIEF-0034 le
#: demande explicitement, `ShipFlight` etant regle dessus.
FLAP_GAP = 0.0130
#: Cote de l'axe de charniere. Compromis : sur la nouvelle lame la mi-epaisseur
#: du volet varie de -0.018 (emplanture) a -0.030 (bout d'aile).
FLAP_HINGE_Z = -0.0240
#: Stations du volet, du bord d'attaque (charniere) au bord de fuite. Elles
#: s'arretent la ou le bord de fuite rake rejoint l'emplanture (y ~ 0,773) :
#: au-dela le volet n'aurait plus de matiere.
FLAP_STATIONS: tuple[float, ...] = (
    0.7730, 0.7850, 0.7980, 0.8110, 0.8240,
)
#: Abscisses echantillonnees en travers du volet (fraction emplanture -> bord).
FLAP_T: tuple[float, ...] = (0.000, 0.180, 0.380, 0.580, 0.780, 1.000)

# ==========================================================================
# Stations longitudinales
# ==========================================================================

#: Stations longitudinales de base (la premiere est la pointe du nez).
#: BRIEF-0034 : la trame arriere est refaite pour poser une station SUR le bout
#: d'aile (0,5800) et suivre le bord de fuite rake (0,6890 / 0,7550 / 0,8000).
BASE_STATIONS: tuple[float, ...] = (
    -1.2300, -1.1900, -1.1400, -1.0800, -1.0200, -0.9600, -0.9000, -0.8400,
    -0.7800, -0.7200, -0.6600, -0.6000, -0.5400, -0.4700, -0.4000, -0.3300,
    -0.2600, -0.2000, -0.1300, -0.0500, 0.0400, 0.1300, 0.2200, 0.3100,
    0.4000, 0.4700, 0.5400, 0.6100, 0.6890, 0.7600, 0.8100, 0.8600,
)

#: Stations ajoutees hors trame reguliere. `FLAP_WALL_Y` est indispensable :
#: sans elle, l'echancrure du volet s'etalerait sur les 7 cm qui separent
#: 0.5400 de 0.6100 et donnerait une rampe au lieu d'une cloison.
EXTRA_STATIONS: tuple[float, ...] = (FLAP_WALL_Y,)

#: Rainures TRANSVERSALES : centre de la bande, et etendue laterale.
#: "fus" = coeur du fuselage seul (l'aile y est trop mince pour porter une
#: rainure sans degenerer), "all" = toute la largeur.
#: Chaque centre est pris au MILIEU d'un intervalle de `BASE_STATIONS` : la
#: paire de stations serrees y decoupe deux bandes residuelles de largeur egale.
#: Decale, un centre laisserait une bande de 8 mm — trop mince pour porter quoi
#: que ce soit, et de la geometrie payee pour rien.
#: Un intervalle de base qui porte une rainure doit mesurer au moins
#: 2 x MIN_BAND + 2 x SEAM_HALF = 49 mm, sans quoi les deux bandes RESIDUELLES
#: passent elles aussi sous le seuil de detection (17,5 mm) et sont prises pour
#: des rainures. Le piege est silencieux : le build reussit, et la coque sort
#: avec trois rainures collees la ou on en voulait une.
#: BRIEF-0033 : 11 -> 19 rainures. BRIEF-0034 : 19, redistribuees sur la
#: nouvelle trame (l'arriere s'est resserre, deux centres ont bouge).
LATERAL_SEAMS: tuple[tuple[float, str], ...] = (
    (-0.9900, "fus"),
    (-0.8700, "fus"),
    (-0.7500, "fus"),
    (-0.6300, "all"),
    (-0.5700, "all"),
    (-0.4350, "all"),
    (-0.3650, "all"),
    (-0.2300, "all"),
    (-0.0900, "all"),
    (-0.0050, "all"),
    (0.0850, "all"),
    (0.1750, "all"),
    (0.2650, "all"),
    (0.3550, "all"),
    (0.4350, "all"),
    (0.5050, "all"),
    (0.5750, "all"),
    (0.6495, "all"),
    (0.7245, "all"),
)

#: Demi-largeur d'une bande de rainure transversale : la bande fait 14 mm.
SEAM_HALF = 0.0070
#: Retrait et profondeur d'une rainure. 5 mm de creux : a 2 mm le chanfrein
#: mangeait la marche et la rainure disparaissait a 20 deg de la verticale.
SEAM_T, SEAM_D = 0.0018, -0.0050

# --- Garde-fou contre l'explosion des insets ------------------------------
# `bmesh.ops.inset_region(use_even_offset=True)` divise le retrait par le sinus
# de l'angle au coin : sur une zone plus etroite que deux fois le retrait, les
# sommets partent a l'infini. Ce n'est pas theorique — la premiere version de
# la passe de detail sortait une coque de 2,44 m de haut, avec des sommets
# projetes a x = 0,75 m sur une aile qui n'en fait que 0,17 a cette station.
#
# Le retrait ne s'applique qu'au CONTOUR de la zone, pas aux aretes interieures :
# la grandeur a controler est donc la largeur d'un TRONCON CONTIGU de cellules,
# jamais celle d'une cellule isolee. `cells()` groupe et filtre pour cela.
#: Rainures (retrait 1,8 mm).
MIN_RUN_SEAM, MIN_EDGE_SEAM, MIN_BAND_SEAM = 0.0060, 0.0060, 0.0100
#: Panneaux (retrait cumule 15 mm).
MIN_RUN_PLATE, MIN_EDGE_PLATE, MIN_BAND_PLATE = 0.0500, 0.0200, 0.0240


def _stations() -> list[float]:
    """Stations = base + extras + une PAIRE serree par rainure transversale.

    Une rainure a besoin d'une bande de faces etroite : on l'obtient en
    inserant deux stations distantes de 14 mm autour de son centre. La bande
    ainsi creee est identifiee plus tard a sa seule largeur (< 20 mm), ce qui
    evite de trimballer des index fragiles.
    """
    out = list(BASE_STATIONS) + list(EXTRA_STATIONS)
    for y, _ in LATERAL_SEAMS:
        out += [y - SEAM_HALF, y + SEAM_HALF]
    return sorted(out)


STATIONS: list[float] = _stations()

EDGE_H = 0.012      # demi-epaisseur du bord d'aile (tranche de 24 mm)
ANHEDRAL = 0.030    # affaissement du bout d'aile (lu sur la vue arriere)
SPINE_HW = 0.072    # demi-largeur du sillon dorsal de nez

# --- Marche de flanc de fuselage et caniveau (BRIEF-0034) -----------------
# C'est ici que se joue « fuselage porteur » plutot que « bande posee sur un
# delta ». Avant, le plan d'aile partait de 0,65 fois la hauteur d'epine, soit
# exactement la cote du fuselage a son bord : les deux surfaces se raccordaient
# sans marche et la vue de dessus ne montrait qu'une lentille continue.
#: Cote du plan d'aile a l'emplanture, en fraction de l'epine. 0,34 laisse une
#: marche de ~9 cm au maitre-couple, franchie sur 4 % de la corde (WING_T[13]) :
#: un flanc a ~75 deg, qui accroche une ombre nette a 20 deg de la verticale.
WING_ROOT_FRAC = 0.34
#: Caniveau creuse au pied de la marche : c'est LUI la « rainure visible » que
#: le brief demande entre le fuselage et les nacelles. Sans lui, la marche seule
#: laissait les deux volumes se toucher.
GUTTER_DEPTH = 0.030
#: Etendue du caniveau, en fraction de corde. Il s'eteint a `GUTTER_T`, soit
#: juste sous la seconde rainure longitudinale (WING_T[12] = 0.194).
GUTTER_T = 0.200

# Verriere : (y, demi-largeur, hauteur au-dessus de son assise).
# BRIEF-0033 : reculee de 0,13 m (le nez lit plus long), enfoncee plus
# profond dans le pont (CANOPY_SINK 18 -> 26 mm, « verriere en retrait ») et
# nettement plus bombee — c'est elle qui donne le point haut de la silhouette.
CANOPY: list[tuple[float, float, float]] = [
    (-0.6600, 0.000, 0.000),
    (-0.6300, 0.034, 0.040),
    (-0.5900, 0.062, 0.076),
    (-0.5400, 0.084, 0.108),
    (-0.4800, 0.098, 0.132),
    (-0.4150, 0.104, 0.142),
    (-0.3500, 0.103, 0.140),
    (-0.2850, 0.098, 0.128),
    (-0.2200, 0.088, 0.104),
    (-0.1700, 0.074, 0.074),
    (-0.1300, 0.054, 0.040),
    (-0.1000, 0.000, 0.000),
]
CANOPY_SINK = 0.026  # assise de la verriere, sous la ligne d'epine

# ==========================================================================
# Nacelles
# ==========================================================================

# BRIEF-0033 : ecartees et descendues pour devenir des VOLUMES PROPRES.
# BRIEF-0034 : ecartees davantage (0.268 -> 0.352) et affinees de 8,5 % (rayon
# maximal 0.164 -> 0.150). L'ecart n'est pas cosmetique : le fuselage a
# desormais des flancs a 0.176 et un caniveau, et le fuseau doit tomber EN
# DEHORS de ce caniveau, sinon les deux masses refusionnent en vue de dessus.
# Bord interne du fuseau (carenage compris) : 0.208 — soit 32 mm d'air.
NACELLE_X = 0.352      # ecartement des axes
NACELLE_Z = -0.062     # axes nettement sous le plan de vol
NACELLE_SEGMENTS = 24  # les tuyeres sont le point focal arriere : on les paie rondes

# Profil de revolution de la nacelle : (y, rayon, materiau du segment sortant).
# Le profil s'arrete au COL (y = 1.048) : au-dela c'est la couronne de petales,
# qui est une piece mobile exportee a part.
# ⚠️ Le dernier rayon (0.095) est repris a l'identique par `NOZZLE_BORE[0]` et
# par `PETAL_SECTIONS[0]` : les trois doivent bouger ENSEMBLE, sinon la vasque
# emissive decroche du col et on voit au travers.
NACELLE_PROFILE: list[tuple[float, float, str]] = [
    (0.470, 0.000, "AA_Hull"),     # pole avant, noye dans l'aile
    (0.510, 0.071, "AA_Hull"),
    (0.570, 0.108, "AA_Hull"),
    (0.650, 0.128, "AA_Hull"),
    (0.730, 0.137, "AA_Hull"),
    (0.780, 0.139, "AA_Panel"),    # bandeau bleu marine du fuseau
    (0.850, 0.140, "AA_Panel"),
    (0.890, 0.141, "AA_Hull"),
    (0.905, 0.141, "AA_Hull"),
    (0.915, 0.147, "AA_Greeble"),  # 1er anneau concentrique
    (0.940, 0.147, "AA_Greeble"),
    (0.948, 0.141, "AA_Hull"),
    (0.962, 0.141, "AA_Greeble"),
    (0.972, 0.150, "AA_Greeble"),  # collier mecanique
    (1.005, 0.150, "AA_Greeble"),
    (1.012, 0.139, "AA_Greeble"),
    (1.018, 0.139, "AA_Trim"),
    (1.023, 0.145, "AA_Trim"),     # jonc dore
    (1.040, 0.145, "AA_Trim"),
    (1.045, 0.137, "AA_Greeble"),
    (1.048, 0.095, "AA_Greeble"),  # levre du COL — raccord des petales
]

#: Buse emissive, EN AVANT du col : (y, rayon, decalage vertical de l'axe).
#: L'axe remonte, de sorte que la vasque lumineuse s'incline VERS LE HAUT.
#: Reponse directe a BRIEF-0026 : a 20 deg de la verticale, une buse purement
#: axiale ne montre rien de son interieur.
NOZZLE_BORE: tuple[tuple[float, float, float], ...] = (
    (1.0480, 0.095, 0.000),   # doit coincider EXACTEMENT avec la fin du lathe
    (1.0300, 0.088, 0.020),
    (1.0000, 0.079, 0.034),
    (0.9700, 0.064, 0.040),
    (0.9550, 0.044, 0.042),
)
NOZZLE_FLOOR_Y = 0.9450  # fond lumineux

# --- Couronne de petales (piece mobile) -----------------------------------
#: 12 petales, celui d'indice 9 centre exactement en bas : c'est lui qui porte
#: la poupe (y = 1.2300) et donc la longueur du contrat.
NOZZLE_PETALS = 12
PETAL_GAP_DEG = 2.4       # jeu angulaire entre deux petales (couronne FERMEE)
PETAL_ARC = 3             # echantillons d'arc par petale
#: Biseau de sortie : les petales du HAUT sont raccourcis de 70 mm, ceux du bas
#: pas du tout. La couronne s'ouvre donc vers le haut et laisse voir la vasque
#: emissive depuis la camera de jeu.
PETAL_SCARF = 0.070
#: (y, rayon interieur, rayon exterieur) — au repos, couronne FERMEE.
PETAL_SECTIONS: tuple[tuple[float, float, float], ...] = (
    (1.0480, 0.095, 0.115),   # col — c'est le PIVOT
    (1.0900, 0.092, 0.121),
    (1.1400, 0.092, 0.126),
    (1.1900, 0.096, 0.131),
    (1.2300, 0.102, 0.135),   # levre de sortie — POUPE (fixe la bbox)
)

# Carenage dorsal de nacelle : le bossage de coque qui noie l'avant de chaque
# fuseau dans l'aile. (y, demi-largeur, hauteur au-dessus de l'axe de nacelle).
# BRIEF-0034 : retreci de 0.176 a 0.144 de demi-largeur. Le carenage etait la
# piece qui refermait le caniveau par le haut — un fuseau bien ecarte ne sert a
# rien si son carenage vient recouvrir le flanc du fuselage.
FAIRING: list[tuple[float, float, float]] = [
    (0.240, 0.000, 0.000),
    (0.340, 0.074, 0.110),
    (0.440, 0.108, 0.148),
    (0.560, 0.132, 0.172),
    (0.700, 0.142, 0.186),
    (0.820, 0.144, 0.190),
    (0.920, 0.138, 0.180),
    (0.980, 0.122, 0.158),
    (1.020, 0.000, 0.000),
]

# Epaule de nacelle : le PROLONGEMENT AVANT du fuseau, pose sur le pont d'aile.
# C'est la piece qui manquait pour que le brief soit tenu a la lettre — il
# demande des nacelles courant sur 60 a 75 % de la longueur, quand fuseau +
# carenage n'en faisaient que 38 %. Avec l'epaule, l'ensemble court de
# y = -0,360 a y = 1,230, soit **1,59 m = 65 % de la longueur**.
# (y, demi-largeur, hauteur au-dessus du pont).
# Chaque demi-largeur est bornee par le bord d'attaque a sa station : a
# y = -0,26 l'aile ne fait que 0,423 de demi-envergure et l'epaule, centree sur
# 0,352, ne peut pas depasser 0,071 sans deborder dans le vide.
SHOULDER: list[tuple[float, float, float]] = [
    (-0.260, 0.000, 0.000),
    (-0.140, 0.052, 0.034),
    (0.020, 0.086, 0.056),
    (0.200, 0.106, 0.070),
    (0.400, 0.120, 0.080),
    (0.580, 0.126, 0.084),
    (0.740, 0.120, 0.078),
    (0.860, 0.000, 0.000),
]
#: Nervures transversales de l'epaule (meme raison que `SPINE_FRAMES`).
SHOULDER_FRAMES: tuple[float, ...] = (-0.060, 0.140, 0.340, 0.540, 0.700)

# --- Derives inclinees (ADR-0014) -----------------------------------------
# BRIEF-0033 se les interdisait et les remplacait par des rails verticaux de
# bout d'aile ; ADR-0014 leve l'interdiction. Elles sont plus rentables que les
# rails a hauteur egale : posees sur les nacelles elles sont AU CENTRE de la
# silhouette, la ou la camera de jeu les voit de trois quarts, tandis qu'un rail
# de bout d'aile ne montre que sa tranche.
#: Inclinaison vers l'exterieur, depuis la verticale. A 30 deg la derive
#: projette 160 mm en vue de dessus (contre 0 pour une derive droite) : c'est
#: cette projection qui la rend lisible dans un shmup vertical.
FIN_CANT_DEG = 34.0
FIN_HEIGHT = 0.300       # envergure de la derive, mesuree dans son propre plan
#: Pied enfonce dans le carenage — mais de 6 cm seulement. A 3 cm (premier
#: essai) 45 % de la derive etait NOYEE dans le carenage et il n'en sortait
#: qu'un moignon : le rendu l'a montre, le calcul ne l'aurait pas dit.
FIN_ROOT_Z = 0.070
#: (fraction d'envergure, y bord d'attaque, y bord de fuite, demi-epaisseur).
FIN: tuple[tuple[float, float, float, float], ...] = (
    (0.00, 0.400, 0.880, 0.026),
    (0.28, 0.492, 0.872, 0.021),
    (0.58, 0.596, 0.862, 0.016),
    (0.82, 0.684, 0.852, 0.011),
    (1.00, 0.756, 0.844, 0.007),
)

# --- Tuyere d'axe ---------------------------------------------------------
# La planche montre TROIS sorties : deux fuseaux et une centrale. Ce n'est pas
# un detail decoratif — c'est ce qui fait lire le fuselage comme porteur
# jusqu'a la poupe. Sans elle, l'arete dorsale s'arretait dans le vide et le
# regard concluait « bande posee », exactement le defaut qu'ADR-0014 pointe.
TAIL_NOZZLE: list[tuple[float, float, str]] = [
    (1.010, 0.000, "AA_Hull"),
    (1.024, 0.062, "AA_Hull"),
    (1.060, 0.072, "AA_Greeble"),
    (1.100, 0.072, "AA_Greeble"),
    (1.108, 0.064, "AA_Trim"),
    (1.130, 0.066, "AA_Trim"),
    (1.150, 0.060, "AA_Greeble"),
    (1.185, 0.056, "AA_Greeble"),
]
TAIL_NOZZLE_Z = 0.014    # axe, entre le dessus et le dessous de l'arete
TAIL_BORE_FLOOR = 1.120  # fond emissif, en avant de la levre

# Ecope ventrale de nacelle : (y, demi-largeur, profondeur SOUS le ventre
# d'aile). C'est la couche qui manquait le plus au profil — sans elle, l'aile
# et le fuseau se touchaient sans transition et la lecture restait « plaque ».
INTAKE: list[tuple[float, float, float]] = [
    (0.030, 0.000, 0.000),
    (0.090, 0.072, -0.062),
    (0.190, 0.098, -0.100),
    (0.340, 0.110, -0.122),
    (0.500, 0.114, -0.130),
    (0.660, 0.112, -0.126),
    (0.780, 0.104, -0.112),
    (0.850, 0.000, 0.000),
]

# ==========================================================================
# Structures dorsale, ventrale et de bout d'aile
# ==========================================================================

# Arete dorsale basse : (y, demi-largeur, z du dessus, z du dessous).
# Flancs VERTICAUX : c'est ce qui la distingue d'un simple bombement de coque
# et la fait lire comme une couche posee sur le pont. Elle prolonge la poutre
# arriere entre les deux fuseaux (au-dela de y = 0.86 la coque s'arrete).
# Elle remplace la « derive » de la planche de reference : elle ne monte qu'a
# 5,5 cm au-dessus du pont et n'a aucune surface inclinee.
#: BRIEF-0034 : la poutre ne se termine plus en lame effilee a y = 1,150 mais
#: en culot rond a y = 1,030, ou vient se poser `TAIL_NOZZLE`.
SPINE: list[tuple[float, float, float, float]] = [
    (-0.1450, 0.010, 0.198, 0.150),
    (-0.0800, 0.060, 0.224, 0.140),
    (0.0200, 0.078, 0.244, 0.130),
    (0.1800, 0.086, 0.260, 0.120),
    (0.3600, 0.088, 0.258, 0.090),
    (0.5600, 0.086, 0.250, 0.020),
    (0.7600, 0.082, 0.236, -0.060),
    (0.9600, 0.076, 0.216, -0.130),
    (1.0300, 0.070, 0.196, -0.156),
]

#: Cadres transversaux de l'arete dorsale. Sans eux, l'arete lit — au rendu de
#: dessus — comme une planche blanche de 1,3 m posee sur le pont : la seule
#: chose que la camera de jeu voit d'elle est son DESSUS, et un dessus lisse
#: n'existe pas. Le defaut ne se voyait pas de profil, ou l'arete est excellente.
SPINE_FRAMES: tuple[float, ...] = (0.060, 0.300, 0.520, 0.720, 0.900)

# Quille ventrale : (y, demi-largeur, z du dessus, z du dessous). Elle loge le
# canon a l'avant et descend a -0.345 au maitre-couple. C'est elle qui porte la
# moitie de la hauteur gagnee — et elle est invisible a 20 deg de la verticale,
# masquee par un fuselage deux fois plus large qu'elle.
#: BRIEF-0034 : les trois premieres stations maigrissent. Le nez etant devenu
#: une aiguille (0,046 de demi-envergure a y = -0,98), une quille de 0,058
#: aurait deborde LATERALEMENT de la coque qu'elle est censee porter.
KEEL: list[tuple[float, float, float, float]] = [
    (-1.0700, 0.030, -0.026, -0.078),
    (-0.9800, 0.044, -0.044, -0.116),
    (-0.8000, 0.062, -0.076, -0.172),
    (-0.5600, 0.086, -0.120, -0.238),
    (-0.3000, 0.098, -0.150, -0.296),
    (-0.0200, 0.106, -0.164, -0.338),
    (0.2200, 0.108, -0.170, -0.345),
    (0.4200, 0.100, -0.168, -0.318),
    (0.6000, 0.088, -0.160, -0.252),
    (0.7600, 0.072, -0.152, -0.186),
    (0.8500, 0.012, -0.156, -0.162),
]

#: Cadres transversaux de la quille (meme raison que `SPINE_FRAMES`, cote
#: profil : sans eux la quille est une grande lentille blanche lisse).
KEEL_FRAMES: tuple[float, ...] = (-0.760, -0.420, -0.100, 0.180, 0.440, 0.660)

#: Nervures de l'ecope ventrale, aux memes fins.
INTAKE_FRAMES: tuple[float, ...] = (0.240, 0.430, 0.620)

#: Stations de la lisse de nez (chine). Elle court a la jonction fuselage/aile
#: et trace, de profil comme de trois quarts, la ligne horizontale qui separe
#: le corps superieur du corps inferieur. C'est la couche la moins couteuse de
#: toute la superposition : deux tubes de 8 sections.
CHINE_Y: tuple[float, ...] = (
    -1.0400, -0.9600, -0.8700, -0.7800, -0.6700, -0.5500, -0.4300, -0.3200,
    -0.2400,
)

# Lisse de bout d'aile. Elle etait, jusqu'a BRIEF-0033, un RAIL de 0,20 m de
# haut qui tenait lieu de derive. Les derives etant desormais admises
# (ADR-0014), la lisse retombe a son role utile : epaissir le bord d'attaque
# externe pour que la lame ne lise pas comme une lame de couteau, et porter le
# feu de bout d'aile. Hauteur divisee par deux — ce qu'on retire ici, la derive
# le rend au centre de la silhouette, ou il compte davantage.
RAIL_X = 0.846        # sous la largeur max (0.875) : ne touche pas la bbox
RAIL_HW = 0.013       # demi-epaisseur de la lame
#: Retrait par rapport au bord d'attaque : la lisse le suit tant qu'il est en
#: deca de `RAIL_X`, puis se redresse. Elle reste ainsi POSEE sur l'aile.
RAIL_INSET = 0.030
#: (y, hauteur au-dessus de l'extrados, profondeur sous l'intrados).
#: Elle s'arrete a y = 0,750, EN AVANT de la charniere de volet (0,760) : au-dela
#: la coque est echancree et la lisse flotterait au-dessus du vide.
RAIL: list[tuple[float, float, float]] = [
    (0.3000, 0.012, 0.006),
    (0.3700, 0.048, 0.026),
    (0.4600, 0.060, 0.032),
    (0.6200, 0.060, 0.032),
    (0.7000, 0.042, 0.022),
    (0.7500, 0.012, 0.006),
]

# Longeron ventral avant : ecartement (a l'axe) des deux tubes du canon.
# La culasse des tubes doit rester SOUS la coque : la demi-envergure du
# planform vaut ~0.104 a y = -0.89, on retranche le rayon de levre du tube.
# Deplacer BARREL_X deplace ENSEMBLE la geometrie des tubes (build_details) et
# les muzzles (build_attach_points) : flash, tube et balle restent alignes.
# BRIEF-0034 : resserres (0.080 -> 0.042) et affines. Le nez ayant maigri de
# moitie, des tubes a 0.080 auraient depasse de 40 mm de chaque cote d'une
# coque qui n'en fait plus que 39 a leur station.
BARREL_X = 0.042        # ecartement des deux tubes du canon ventral
BARREL_R = 0.015
BARREL_TIP = -1.0550    # pointe des tubes
MUZZLE_Y = -1.0700      # bouche de tir : juste devant les tubes

# Canons additionnels montes sur l'aile (positions laterales, a l'axe).
WING_MUZZLE_X = 0.500   # canon d'aile (power 3) : sur le bord d'attaque, a mi-aile
TIP_MUZZLE_X = 0.800    # pod de bout d'aile (power 5) : sous la largeur max 0.875


# ==========================================================================
# Interpolation des tables
# ==========================================================================


def lerp_table(table, y: float) -> float:
    """Interpolation lineaire d'une table (y, valeur), extremites clampees.

    Volontairement lineaire par morceaux : sur une aile delta hard-surface,
    une spline arrondirait les cassures qui font justement la silhouette.
    """
    if y <= table[0][0]:
        return table[0][1]
    if y >= table[-1][0]:
        return table[-1][1]
    for i in range(len(table) - 1):
        y0, v0 = table[i][0], table[i][1]
        y1, v1 = table[i + 1][0], table[i + 1][1]
        if y0 <= y <= y1:
            t = (y - y0) / (y1 - y0)
            return v0 + (v1 - v0) * t
    return table[-1][1]


def lerp_row(table, y: float, column: int) -> float:
    """Comme `lerp_table`, mais sur la colonne `column` d'une table a n colonnes."""
    return lerp_table([(row[0], row[column]) for row in table], y)


def section_params(y: float) -> tuple[float, float, float, float]:
    """(demi-envergure, demi-fuselage, epine, ventre) a la station `y`.

    C'est la GEOMETRIE de la section : elle ignore l'echancrure des volets, qui
    ne coupe que l'etendue laterale (`section_cut`). Les deux doivent rester
    separees, sinon le volet et son logement n'auraient pas le meme profil et
    on verrait une marche au repos.
    """
    w = lerp_table(PLANFORM, y)
    f = min(lerp_table(FUSELAGE, y), w * 0.94)
    return w, f, lerp_table(CROWN, y), lerp_table(BELLY, y)


def section_cut(y: float) -> float:
    """Demi-largeur REELLE de la coque : `section_params` sauf echancrure volet."""
    w = lerp_table(PLANFORM, y)
    if y >= FLAP_HINGE_Y - 1e-9:
        return min(w, FLAP_ROOT_X)
    return w


def _edge_h(crown: float) -> float:
    """Bord d'aile : jamais plus epais que le corps (sinon nez creuse)."""
    return min(EDGE_H, 0.55 * crown) if crown > 1e-6 else 0.0


def _wing_shoulder(crown: float, eh: float) -> float:
    """Cote du plan d'aile a l'emplanture (BRIEF-0034).

    Le `max(..., eh)` n'est pas de la coquetterie : vers la pointe du nez,
    `eh` est lui-meme borne a 0.55 * crown, donc superieur a 0.34 * crown. Sans
    la garde, l'aile serait plus EPAISSE au bord qu'a l'emplanture sur les
    quinze premiers centimetres, et le nez sortirait creuse.
    """
    return max(WING_ROOT_FRAC * crown, eh)


def _gutter(t: float, crown: float) -> float:
    """Creux du caniveau d'emplanture a la fraction de corde `t`.

    L'amplitude est plafonnee par l'epine locale : au nez, ou la coque fait
    4 cm d'epaisseur, un caniveau de 30 mm la traverserait de part en part.
    """
    if t >= GUTTER_T:
        return 0.0
    amp = min(GUTTER_DEPTH, 0.22 * crown)
    return amp * (1.0 - t / GUTTER_T)


def z_top(x: float, w: float, f: float, crown: float, belly: float) -> float:
    """Surface superieure : bombe de fuselage, MARCHE, caniveau, puis aile mince.

    La marche est implicite : la branche fuselage rend 0,65 x crown au bord
    (a = f) tandis que la branche aile part de 0,34 x crown. Les deux sommets
    voisins de la section sont distants de 4 % de corde seulement, donc le pont
    de faces qui les relie EST le flanc du fuselage.
    """
    a = abs(x)
    if f > 1e-6 and a <= f:
        return crown * (1.0 - 0.35 * (a / f) ** 2)
    t = (a - f) / max(w - f, 1e-6)
    t = min(max(t, 0.0), 1.0)
    eh = _edge_h(crown)
    shoulder = _wing_shoulder(crown, eh)
    plane = -ANHEDRAL * t * t + (shoulder - eh) * (1.0 - t) ** 1.4 + eh
    return plane - _gutter(t, crown)


def z_bot(x: float, w: float, f: float, crown: float, belly: float) -> float:
    a = abs(x)
    if f > 1e-6 and a <= f:
        return belly * (1.0 - 0.35 * (a / f) ** 2)
    t = (a - f) / max(w - f, 1e-6)
    t = min(max(t, 0.0), 1.0)
    eh = _edge_h(crown)
    shoulder = 0.65 * (-belly)
    return -ANHEDRAL * t * t - ((shoulder - eh) * (1.0 - t) ** 1.4 + eh)


# --------------------------------------------------------------------------
# Section transversale : 39 abscisses
# --------------------------------------------------------------------------

#: Fractions de la corde d'aile (t = 1 au bord d'aile, t = 0 a l'emplanture).
#: Les PAIRES serrees (0.684/0.652 et 0.226/0.194) delimitent les deux rainures
#: LONGITUDINALES : elles suivent la fleche de l'aile, comme les lignes de
#: panneau rayonnantes de la planche, au lieu de couper droit.
#: BRIEF-0034 : l'avant-derniere fraction passe de 0,100 a 0,040. Le segment 13
#: est le FLANC du fuselage : plus il est etroit, plus la marche est raide. A
#: 0,100 elle tombait a 55 deg (un conge) ; a 0,040 elle est a ~75 deg (un
#: flanc). Le segment 12 (0,194 -> 0,040) porte le caniveau.
WING_T: tuple[float, ...] = (
    1.000, 0.955, 0.900, 0.800, 0.700,
    0.684, 0.652,          # <- bande de rainure longitudinale A (segment 5)
    0.550, 0.440, 0.330, 0.242,
    0.226, 0.194,          # <- bande de rainure longitudinale B (segment 11)
    0.040, 0.000,          # 12 = caniveau, 13 = flanc, 14 = emplanture
)
#: Fractions du trajet emplanture -> sillon dorsal.
FUS_U: tuple[float, ...] = (0.34, 0.67, 1.00)
#: Fractions du sillon dorsal -> axe.
SPINE_U: tuple[float, ...] = (0.55, 0.00)


def section_x(w: float, f: float) -> list[float]:
    """Les 39 abscisses d'une section, de babord (+W) a tribord (-W).

    `w` est ici l'etendue REELLE (`section_cut`), pas la geometrie : c'est ce
    qui echancre proprement le logement des volets sans deformer le profil.
    """
    s = min(SPINE_HW, 0.60 * f)
    d = w - f
    half = [f + t * d for t in WING_T]           # 0..14  (14 = f)
    half += [f + (s - f) * u for u in FUS_U]     # 15..17 (17 = s)
    half += [s * u for u in SPINE_U]             # 18..19 (19 = axe)
    return half + [-v for v in reversed(half[:-1])]


#: Nombre d'abscisses (= sommets de la surface superieure d'une section).
N_TOP = len(section_x(1.0, 0.4))          # 39
#: Nombre de segments par surface (superieure ou inferieure).
N_SEG = N_TOP - 1                          # 38 sommets -> index 0..37
RIM_STARBOARD = N_TOP - 1                  # 38
RIM_PORT = 2 * N_TOP - 1                   # 77

#: Index de segment des deux rainures LONGITUDINALES (cote babord).
LONG_SEAM_SEGS: tuple[int, ...] = (5, 11)
#: Segment du caniveau d'emplanture, et segment du flanc de fuselage.
GUTTER_SEG, FLANK_SEG = 12, 13
#: Segments du sillon dorsal (creuse en tant que tel).
SPINE_SEGS: tuple[int, ...] = (17, 18)
#: Etendue laterale des rainures transversales (voir `LATERAL_SEAMS`).
SEG_SPAN_ALL = tuple(range(1, N_SEG))                 # tout sauf les bords d'aile
SEG_SPAN_FUS = tuple(range(14, N_SEG - 14 + 1))       # coeur du fuselage


def top_face(j: int) -> int:
    """Index de la face du segment `j` sur la surface superieure."""
    return j


def bot_face(j: int) -> int:
    """Index de la face du segment `j` sur la surface inferieure."""
    return 2 * N_TOP - 2 - j


MIRROR = {j: (N_TOP - 2) - j for j in range(N_TOP - 1)}


def both(*js: int) -> set[int]:
    """Un ensemble de segments et leurs symetriques (babord + tribord)."""
    out: set[int] = set()
    for j in js:
        out.add(j)
        out.add(MIRROR[j])
    return out


ALL_LONG_SEAMS: set[int] = both(*LONG_SEAM_SEGS)


def run_width(y: float, first: int, last: int) -> float:
    """Largeur (m) du troncon contigu de segments `first..last` a la station `y`.

    Vers le nez, la corde d'aile tombe a quelques centimetres et une cellule y
    mesure moins d'un millimetre : c'est cette mesure — et non une liste de
    zones ecrite a la main — qui eteint rainures et panneaux la ou la coque est
    trop mince pour les porter.
    """
    _, f, _, _ = section_params(y)
    xs = section_x(section_cut(y), f)
    return abs(xs[first] - xs[last + 1])


def contiguous_runs(js: list[int]) -> list[list[int]]:
    """Decoupe une liste triee de segments en troncons d'index consecutifs."""
    runs: list[list[int]] = []
    for j in sorted(js):
        if runs and j == runs[-1][-1] + 1:
            runs[-1].append(j)
        else:
            runs.append([j])
    return runs


# ==========================================================================
# Coque principale
# ==========================================================================


def build_hull() -> object:
    bm = bmesh.new()

    rings: list[list] = []
    for y in STATIONS[1:]:
        w, f, crown, belly = section_params(y)
        xs = section_x(section_cut(y), f)
        top = [(x, y, z_top(x, w, f, crown, belly)) for x in xs]
        bot = [(x, y, z_bot(x, w, f, crown, belly)) for x in reversed(xs)]
        rings.append(ak.add_ring(bm, top + bot))

    nose = bm.verts.new((0.0, STATIONS[0], 0.0))

    bands: list[list] = []
    band_y: list[float] = []
    band_w: list[float] = []
    ak.fan_to_point(bm, rings[0], nose, "AA_Hull")
    for i in range(len(rings) - 1):
        bands.append(ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Hull"))
        y0, y1 = STATIONS[i + 1], STATIONS[i + 2]
        band_y.append((y0 + y1) * 0.5)
        band_w.append(y1 - y0)
    ak.cap_ring(bm, list(reversed(rings[-1])), "AA_Greeble")

    # Une bande de rainure transversale se reconnait a sa seule largeur (14 mm
    # contre ~35 mm pour une bande courante) : aucun index a maintenir.
    seam_bands = {b for b, wdt in enumerate(band_w) if wdt < SEAM_HALF * 2.5}

    # Cellules deja consommees (materiau pose ou panneau creuse). Une rainure
    # n'ecrase jamais un panneau : elle se faufile entre eux, en plusieurs
    # troncons si besoin — ce qui est exactement la lecture de la planche.
    used: set[tuple[int, int, str]] = set()

    def cells(
        y0: float,
        y1: float,
        js,
        surface: str = "top",
        min_run: float = 0.0,
        min_edge: float = 0.0,
        min_band: float = 0.0,
        skip_seams: bool = False,
    ) -> list:
        """Selectionne des cellules libres en ecartant tout ce qui se replierait.

        Le filtre porte sur le TRONCON contigu (le retrait ne s'applique qu'au
        contour de la zone, pas aux aretes interieures), puis sur ses cellules
        d'extremite, qu'on rogne tant qu'elles sont trop etroites.
        """
        chooser = top_face if surface == "top" else bot_face
        out = []
        for b, ym in enumerate(band_y):
            if not (y0 <= ym <= y1):
                continue
            if skip_seams and b in seam_bands:
                continue
            if min_band > 0.0 and band_w[b] < min_band:
                continue
            free = [
                j for j in js
                if (b, j, surface) not in used
                and bands[b][chooser(j)] is not None
                and bands[b][chooser(j)].is_valid
            ]
            for run in contiguous_runs(free):
                while run and run_width(ym, run[0], run[0]) < min_edge:
                    run = run[1:]
                while run and run_width(ym, run[-1], run[-1]) < min_edge:
                    run = run[:-1]
                if not run or run_width(ym, run[0], run[-1]) < min_run:
                    continue
                for j in run:
                    used.add((b, j, surface))
                    out.append(bands[b][chooser(j)])
        return out

    def pick(y0: float, y1: float, js, surface: str = "top") -> list:
        return cells(y0, y1, js, surface)

    def pick_rim(y0: float, y1: float) -> list:
        out = []
        for b, ym in enumerate(band_y):
            if y0 <= ym <= y1:
                for idx in (RIM_PORT, RIM_STARBOARD):
                    face = bands[b][idx]
                    if face is not None and face.is_valid:
                        out.append(face)
        return out

    def plate(faces: list, material: str) -> None:
        """Panneau a DEUX niveaux (cf. build_crescent_interceptor.py:597).

        Un inset unique laissait un aplat de couleur pleine qui, au rendu,
        « lisait peint ». Le premier inset decoupe une marche restant en coque,
        le second n'accorde au bleu qu'un fond nettement enfonce : la lumiere
        accroche alors deux aretes au lieu d'une, et le panneau existe.
        """
        if not faces:
            return
        ak.inset_panel(bm, faces, "AA_Hull", thickness=0.006, depth=-0.005)
        ak.inset_panel(bm, faces, material, thickness=0.009, depth=-0.006)

    # ---------------------------------------------------------------------
    # 1. Elements identitaires : ils ont priorite sur tout le reste.
    # ---------------------------------------------------------------------

    # --- cloison du logement de volet : la bande 0.6070 -> 0.6100 est la
    #     seule surface presque verticale de l'aile. On la noircit pour que la
    #     ligne d'articulation se lise meme volet ferme.
    wall_segs = both(0, 1, 2, 3, 4, 5, 6, 7, 8, 9)
    ak.set_material(pick(0.6075, 0.6095, wall_segs), "AA_Greeble")
    ak.set_material(pick(0.6075, 0.6095, wall_segs, "bot"), "AA_Greeble")

    # --- caniveau d'emplanture : la « rainure visible » entre le fuselage et
    #     les nacelles. Elle est sombre sur toute la longueur, et l'epaule de
    #     nacelle vient en recouvrir la moitie externe : ce qui reste a l'œil
    #     est une fente de ~22 mm au pied du flanc, sur 1,8 m de long.
    ak.set_material(pick(-0.420, 0.845, both(GUTTER_SEG)), "AA_Greeble")

    # --- flanc de fuselage : peint, jamais creuse. Il ne fait que 4 % de la
    #     corde (24 mm au maitre-couple) — un `plate()`, qui retire 15 mm au
    #     contour, l'effondrerait. C'est la seule surface quasi verticale que
    #     la camera de jeu voit : le bleu profond y trace la ligne de flanc.
    ak.set_material(pick(-0.700, 0.845, both(FLANK_SEG)), "AA_Panel")

    # --- puits de verriere : bordure doree, cuve sombre (cf. planche) -----
    well = pick(-0.680, -0.085, both(15, 16, 17, 18))
    border = ak.inset_panel(bm, well, "AA_Greeble", thickness=0.012, depth=-0.016)
    ak.set_material(border, "AA_Trim")

    # --- sillon dorsal creuse, du nez a la verriere. En arriere, l'arete
    #     dorsale recouvre entierement cette zone : y creuser une rainure
    #     serait payer de la geometrie invisible.
    ak.inset_panel(
        bm, pick(-1.100, -0.700, both(*SPINE_SEGS)),
        "AA_Greeble", thickness=0.005, depth=-0.016,
    )
    ak.set_material(pick(-0.085, 0.845, both(*SPINE_SEGS)), "AA_Greeble")

    # --- bord d'attaque externe : coiffe doree + marquage rouge, en AVANT de
    #     la lisse de bout d'aile (qui commence a y = 0.260) pour que les deux
    #     ne se recouvrent pas, puis tranche doree jusqu'au bout d'aile.
    ak.set_material(pick(0.060, 0.150, both(0)), "AA_Trim")
    ak.set_material(pick(0.150, 0.230, both(0)), "AA_Marking_Red")
    ak.set_material(pick(0.230, 0.300, both(0)), "AA_Trim")
    ak.set_material(pick_rim(0.300, 0.750), "AA_Trim")

    # --- coiffes dorees de bord d'attaque avant (deux marques symetriques).
    #     Reculees par BRIEF-0034 : en avant de y = -0.66 le nouveau nez est si
    #     fin que la corde d'aile n'y fait plus 5 mm.
    ak.set_material(pick(-0.660, -0.480, both(0)), "AA_Trim")
    ak.set_material(pick_rim(-0.660, -0.480), "AA_Trim")

    # --- flancs de nez : PEINTS, pas creuses. Sur l'aiguille du nez la corde
    #     d'aile tombe sous 10 cm et `plate()` — qui retire 15 mm au contour —
    #     s'y effondre. Le bleu y est donc pose a plat, ce qui suffit : a cette
    #     station la coque est vue presque de chant.
    ak.set_material(pick(-1.060, -0.560, both(2, 3, 6, 7)), "AA_Panel")

    # ---------------------------------------------------------------------
    # 2. Rainures LONGITUDINALES. Posees AVANT les panneaux : elles sont la
    #    trame du plaquage, les panneaux viennent s'y appuyer. Le filtre de
    #    largeur les eteint tout seul la ou l'aile est trop mince.
    # ---------------------------------------------------------------------
    for seg in sorted(ALL_LONG_SEAMS):
        ak.inset_panel(
            bm,
            cells(-1.200, 0.845, (seg,), min_run=MIN_RUN_SEAM,
                  min_edge=MIN_EDGE_SEAM, min_band=MIN_BAND_SEAM),
            "AA_Hull",
            thickness=SEAM_T,
            depth=SEAM_D,
        )

    # ---------------------------------------------------------------------
    # 3. Panneaux bleu profond, a deux niveaux (aplats de la planche).
    # ---------------------------------------------------------------------
    # BRIEF-0034 : les segments 12 et 13 sortent de cette liste — ils sont
    # devenus le caniveau et le flanc de fuselage, et ne sont plus du plaquage.
    # Le flanc, lui, recoit son propre panneau bleu : c'est la seule surface
    # quasi verticale visible du dessus, elle merite d'etre lue comme telle.
    # Les bornes tiennent compte de ce que la corde d'aile est devenue : elle
    # ne passe les 25 cm qu'en arriere de y = -0,15, et `MIN_RUN_PLATE` (50 mm)
    # eteint tout seul ce qui serait plus etroit. Inutile d'ecrire des zones
    # avant : elles seraient silencieusement ignorees.
    for y0, y1, js in (
        (-0.500, 0.100, both(2, 3, 6, 7)),          # glove avant
        (-0.150, 0.400, both(8, 9)),                # emplanture, mi-corde
        (0.100, 0.750, both(0, 1, 2)),              # lisere de bord d'attaque
        (0.000, 0.620, both(3, 4, 6, 7)),           # grand chevron d'aile externe
        (0.300, 0.740, both(8, 9)),                 # aile interne arriere
        (0.700, 0.845, both(2, 3, 6, 7)),           # plateau de culot
    ):
        # `skip_seams=True` : un panneau ne mord jamais sur une bande de rainure.
        # Les grandes plaques bleues se retrouvent donc BORDEES de rainures, ce
        # qui est exactement la lecture de la planche (plaques jointoyees).
        plate(
            cells(y0, y1, js, min_run=MIN_RUN_PLATE, min_edge=MIN_EDGE_PLATE,
                  min_band=MIN_BAND_PLATE, skip_seams=True),
            "AA_Panel",
        )

    # ---------------------------------------------------------------------
    # 4. Rainures TRANSVERSALES : elles decoupent les grandes plages blanches
    #    restantes en plaques, et se scindent d'elles-memes autour des
    #    panneaux deja creuses.
    # ---------------------------------------------------------------------
    for b in sorted(seam_bands):
        ym = band_y[b]
        span = None
        for y, kind in LATERAL_SEAMS:
            if abs(y - ym) < SEAM_HALF:
                span = SEG_SPAN_ALL if kind == "all" else SEG_SPAN_FUS
                break
        if span is None:
            continue
        ak.inset_panel(
            bm,
            cells(ym - 1e-4, ym + 1e-4, span, min_run=MIN_RUN_SEAM,
                  min_edge=MIN_EDGE_SEAM),
            "AA_Hull",
            thickness=SEAM_T,
            depth=SEAM_D,
        )

    # ---------------------------------------------------------------------
    # 5. Dessous : quille sombre et deux panneaux. Volontairement pauvre —
    #    a 20 deg de la verticale le ventre n'existe pas (BRIEF-0026), et
    #    chaque triangle qu'on y depense est un triangle perdu.
    # ---------------------------------------------------------------------
    ak.set_material(pick(-1.050, 0.845, both(*SPINE_SEGS), "bot"), "AA_Greeble")
    plate(
        cells(0.000, 0.600, both(3, 4, 7, 8), "bot", min_run=MIN_RUN_PLATE,
              min_edge=MIN_EDGE_PLATE, min_band=MIN_BAND_PLATE, skip_seams=True),
        "AA_Panel",
    )

    return ak.new_object("Specter9_Hull", bm)


# ==========================================================================
# Sous-ensembles (verriere, nacelles, arete, quille, rails, canon, greebles)
# ==========================================================================


def _rect_ring(bm, y: float, hw: float, z_lo: float, z_hi: float, taper: float = 1.0):
    """Section rectangulaire (4 sommets) : brique de base des longerons."""
    return ak.add_ring(
        bm,
        [
            (hw, y, z_hi),
            (-hw, y, z_hi),
            (-hw * taper, y, z_lo),
            (hw * taper, y, z_lo),
        ],
    )


def _beam_ring(bm, y: float, hw: float, z_hi: float, z_lo: float,
               chamfer: float, top_frac: float, center_x: float = 0.0):
    """Section a FLANCS VERTICAUX et arete chanfreinee (arete dorsale, quille).

    Six sommets. Le chanfrein n'est pas cosmetique : il donne au volume deux
    aretes vives paralleles au lieu d'une, et c'est ce doublet qui fait lire une
    couche posee sur le pont plutot qu'un bombement de la coque elle-meme.
    `chamfer > 0` chanfreine le HAUT (arete dorsale), `chamfer < 0` le BAS
    (quille).
    """
    if chamfer >= 0.0:
        za, zb = z_hi - chamfer, z_hi
        zc, zd = z_lo, z_lo
    else:
        za, zb = z_lo - chamfer, z_lo
        zc, zd = z_hi, z_hi
    return ak.add_ring(
        bm,
        [
            (center_x + hw, y, zc),
            (center_x + hw, y, za),
            (center_x + hw * top_frac, y, zb),
            (center_x - hw * top_frac, y, zb),
            (center_x - hw, y, za),
            (center_x - hw, y, zd),
        ],
    )


def _beam(bm, sections, chamfer: float, top_frac: float,
          materials: tuple[str, str, str], center_x: float = 0.0) -> list[list]:
    """Longeron a flancs verticaux loft le long de `sections`.

    `sections` : (y, demi-largeur, z_hi, z_lo). `materials` = (flanc, chanfrein,
    face plate). Retourne les bandes, pour pouvoir y poser des panneaux.
    """
    side, edge, face = materials
    rings = [
        _beam_ring(bm, y, hw, z_hi, z_lo, chamfer, top_frac, center_x)
        for y, hw, z_hi, z_lo in sections
    ]
    bands = []
    for i in range(len(rings) - 1):
        band = ak.bridge_rings(bm, rings[i], rings[i + 1], side)
        ak.set_material([band[1], band[3]], edge)
        ak.set_material([band[2]], face)
        bands.append(band)
    ak.cap_ring(bm, list(reversed(rings[0])), side)
    ak.cap_ring(bm, rings[-1], side)
    return bands


def _strip(bm, samples: list[tuple[float, float, float]], hw: float, material: str,
           center_x: float = 0.0):
    """Bandeau lumineux : petit tube rectangulaire suivant (y, z_bas, z_haut)."""
    rings = [
        ak.add_ring(
            bm,
            [
                (center_x + hw, y, hi),
                (center_x - hw, y, hi),
                (center_x - hw, y, lo),
                (center_x + hw, y, lo),
            ],
        )
        for y, lo, hi in samples
    ]
    for i in range(len(rings) - 1):
        ak.bridge_rings(bm, rings[i], rings[i + 1], material)
    ak.cap_ring(bm, list(reversed(rings[0])), material)
    ak.cap_ring(bm, rings[-1], material)


DOME_ARC = 9  # points d'arc d'une section de dome (verriere, carenage, ecope)


def _dome(bm, sections, center_x, base_z, material: str) -> list[list]:
    """Demi-coque bombee, posee sur une assise plane : verriere, carenage, ecope.

    `sections` : (y, demi-largeur, hauteur au-dessus de l'assise). Une hauteur
    NEGATIVE donne une cloque vers le bas (ecope ventrale). Une section de
    demi-largeur nulle est une pointe. `base_z` : callable(y) -> z d'assise.
    Retourne les bandes de faces, pour pouvoir y poser des panneaux.
    """
    rings: list = []
    tips: list = []
    for y, hw, h in sections:
        z0 = base_z(y)
        if hw <= 1e-6:
            tips.append(bm.verts.new((center_x, y, z0)))
            rings.append(None)
            continue
        pts = [
            (
                center_x + hw * math.cos(math.pi * k / (DOME_ARC - 1)),
                y,
                z0 + h * math.sin(math.pi * k / (DOME_ARC - 1)),
            )
            for k in range(DOME_ARC)
        ]
        rings.append(ak.add_ring(bm, pts))

    solid = [r for r in rings if r is not None]
    bands = []
    ak.fan_to_point(bm, solid[0], tips[0], material)
    for i in range(len(solid) - 1):
        bands.append(ak.bridge_rings(bm, solid[i], solid[i + 1], material))
    ak.fan_to_point(bm, list(reversed(solid[-1])), tips[-1], material)
    return bands


def _circle(bm, y: float, radius: float, cx: float, cz: float,
            segments: int = NACELLE_SEGMENTS):
    """Anneau circulaire dans le plan Y = cste.

    Reproduit EXACTEMENT la formule de `ak.add_lathe(axis="Y")` : c'est ce qui
    permet a `ak.cleanup()` de souder la buse construite a la main sur le
    dernier anneau du solide de revolution, sans couture visible.
    """
    return ak.add_ring(
        bm,
        [
            (
                cx + radius * math.cos(2.0 * math.pi * s / segments),
                y,
                cz + radius * math.sin(2.0 * math.pi * s / segments),
            )
            for s in range(segments)
        ],
    )


def _nozzle_bore(bm, cx: float, cz: float) -> None:
    """Vasque emissive, en avant du col, a axe RELEVE.

    Le probleme resolu ici est de visibilite, pas de style. Une buse coaxiale
    n'expose son emissif que vers l'arriere ; or la camera de jeu regarde a 20
    deg de la verticale et l'ecran d'accueil cadre le vaisseau de trois quarts
    arriere. En remontant l'axe de 42 mm, la couronne emissive devient une
    vasque dont la moitie haute est quasi horizontale — et les petales du haut
    sont raccourcis de 70 mm pour la laisser voir.
    """
    rings = [_circle(bm, y, r, cx, cz + dz) for y, r, dz in NOZZLE_BORE]
    for i in range(len(rings) - 1):
        ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Emissive_Engine")
    floor = bm.verts.new((cx, NOZZLE_FLOOR_Y, cz + NOZZLE_BORE[-1][2]))
    ak.fan_to_point(bm, rings[-1], floor, "AA_Emissive_Engine")


def _deck_z(x: float, y: float) -> float:
    """Cote de la surface superieure de coque au point (x, y)."""
    return z_top(x, *section_params(y))


def _belly_z(x: float, y: float) -> float:
    """Cote de la surface inferieure de coque au point (x, y)."""
    return z_bot(x, *section_params(y))


def _rail_x(y: float) -> float:
    """Abscisse (positive) du rail de bout d'aile a la station `y`.

    Le rail suit le bord d'attaque tant que celui-ci est en deca de `RAIL_X`,
    puis se redresse le long du bout d'aile. Il reste ainsi POSE sur l'aile sur
    toute sa longueur — voir `RAIL_INSET`.
    """
    return min(lerp_table(PLANFORM, y) - RAIL_INSET, RAIL_X)


def _chord_x(y: float, frac: float) -> float:
    """Abscisse a la fraction `frac` de la corde d'aile, a la station `y`.

    Poser un detail a une abscisse ABSOLUE est ce qui a rendu la moitie des
    bandeaux de BRIEF-0033 caducs des que le bord d'attaque a bouge. Exprime en
    fraction de corde, un bandeau suit la fleche de l'aile quoi qu'elle devienne.
    """
    _, f, _, _ = section_params(y)
    return f + frac * (section_cut(y) - f)


def _fin(bm, sx: float) -> None:
    """Derive inclinee, montee sur le dessus d'une nacelle (ADR-0014).

    Elle est loftee dans SON propre plan : chaque section est un rectangle
    mince, translate le long de l'axe de derive (incline de `FIN_CANT_DEG` vers
    l'exterieur) et epaissi perpendiculairement a ce plan. Construire la lame
    droite puis la tourner aurait marche aussi, mais aurait laisse le pied
    dessiner un arc au lieu d'epouser le carenage.
    """
    cant = math.radians(FIN_CANT_DEG)
    # axe d'envergure de la derive, et normale a son plan
    ax, az = math.sin(cant), math.cos(cant)
    nx, nz = math.cos(cant), -math.sin(cant)

    rings = []
    for s, y_le, y_te, th in FIN:
        cx = sx * (NACELLE_X + s * FIN_HEIGHT * ax)
        cz = FIN_ROOT_Z + s * FIN_HEIGHT * az
        # `sx` sur la composante x de la normale : sans cela la derive tribord
        # serait epaissie du mauvais cote et son pied sortirait du carenage.
        dx, dz = sx * nx * th, nz * th
        rings.append(
            ak.add_ring(
                bm,
                [
                    (cx + dx, y_le, cz + dz),
                    (cx + dx, y_te, cz + dz),
                    (cx - dx, y_te, cz - dz),
                    (cx - dx, y_le, cz - dz),
                ],
            )
        )
    for i in range(len(rings) - 1):
        band = ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Hull")
        # 1 = bord de fuite, 3 = bord d'attaque : deux tranches, en sombre,
        # qui donnent a la lame une epaisseur lisible a 20 deg de la verticale.
        ak.set_material([band[1], band[3]], "AA_Greeble")
        # 0 = flanc EXTERNE. Incline de 34 deg, c'est la seule face de la
        # derive que la camera de jeu voit vraiment : la laisser en blanc de
        # coque la faisait disparaitre dans le pont, qui l'est aussi.
        if 1 <= i <= 2:
            ak.set_material([band[0]], "AA_Panel")
        if i >= len(rings) - 2:
            ak.set_material([band[0], band[2]], "AA_Marking_Red")  # coiffe
    ak.cap_ring(bm, list(reversed(rings[0])), "AA_Greeble")
    ak.cap_ring(bm, rings[-1], "AA_Trim")
    # feu de derive, sur la tranche du bord de fuite
    ak.add_box(
        bm,
        (
            sx * (NACELLE_X + 0.86 * FIN_HEIGHT * ax),
            0.848,
            FIN_ROOT_Z + 0.86 * FIN_HEIGHT * az,
        ),
        (0.024, 0.014, 0.048),
        "AA_Emissive_Engine",
    )


def _deck_greebles(bm, x: float, y0: float, y1: float, count: int, seed: int,
                   size_range=(0.016, 0.034), height_range=(0.006, 0.014)) -> None:
    """Bandeau de greebles POSE sur le pont, en suivant sa courbure.

    `greeble_strip` interpole lineairement le z entre depart et arrivee : en lui
    donnant la cote reelle de la coque aux deux extremites, les boites se posent
    au lieu de flotter ou de s'enfoncer.
    """
    ak.greeble_strip(
        bm,
        (x, y0, _deck_z(x, y0) - 0.003),
        (x, y1, _deck_z(x, y1) - 0.003),
        count=count,
        seed=seed,
        size_range=size_range,
        height_range=height_range,
    )


def build_details() -> object:
    bm = bmesh.new()
    rng_seed = SEED

    # ---------------------------------------------------------------- verriere
    canopy_base = lambda y: lerp_table(CROWN, y) - CANOPY_SINK  # noqa: E731
    canopy_bands = _dome(bm, CANOPY, 0.0, canopy_base, "AA_Glass")

    # Montants de verriere : la planche ne montre pas un ovale sombre pose a
    # plat mais une bulle STRUCTUREE — deux rails lateraux et une nervure d'axe.
    # On les prend sur les faces du dome (aucun triangle supplementaire).
    for band in canopy_bands:
        ak.set_material([band[k] for k in (0, DOME_ARC - 2) if band[k]], "AA_Greeble")
    for band in canopy_bands[3:6]:
        ak.set_material([band[k] for k in (3, 4) if band[k]], "AA_Greeble")

    # Cadre en RELIEF autour du puits : deux longerons dores suivant le contour
    # de la verriere, plus une traverse avant (pare-brise) et une arriere. C'est
    # ce bourrelet qui donne au cockpit son epaisseur en vue de dessus, et qui
    # empeche la verriere de lire comme un ovale peint.
    for sx in (ak.PORT, ak.STARBOARD):
        rail = []
        for y, hw, _h in CANOPY[1:-1]:
            z0 = canopy_base(y)
            rail.append((y, hw + 0.014, z0 - 0.006, z0 + 0.026))
        rings = [
            ak.add_ring(
                bm,
                [
                    (sx * (hw + 0.010), y, hi),
                    (sx * (hw - 0.006), y, hi),
                    (sx * (hw - 0.006), y, lo),
                    (sx * (hw + 0.010), y, lo),
                ],
            )
            for y, hw, lo, hi in rail
        ]
        for i in range(len(rings) - 1):
            ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Trim")
        ak.cap_ring(bm, list(reversed(rings[0])), "AA_Trim")
        ak.cap_ring(bm, rings[-1], "AA_Trim")

    for y, hw, tall, mat in (
        (-0.6450, 0.050, 0.028, "AA_Trim"),     # cadre de pare-brise, en relief
        (-0.5950, 0.066, 0.016, "AA_Greeble"),  # arceau
        (-0.1150, 0.064, 0.030, "AA_Trim"),     # dosseret arriere
    ):
        z0 = canopy_base(y)
        ak.add_box(bm, (0.0, y, z0 + tall * 0.5), (hw * 2.0, 0.024, tall), mat)

    # --------------------------------------------------- arete dorsale basse
    # Presence verticale ORIGINALE : une arete a flancs verticaux, jamais une
    # derive. Flancs en bleu profond, chanfreins en coque, dessus en coque :
    # de profil, deux lignes horizontales paralleles se detachent du pont.
    spine_bands = _beam(
        bm, SPINE, chamfer=0.014, top_frac=0.70,
        materials=("AA_Panel", "AA_Hull", "AA_Hull"),
    )
    # jonc dore au droit de la baie technique (accent, pas une livree)
    for b, (y, _, _, _) in enumerate(SPINE[:-1]):
        if 0.02 <= y <= 0.36:
            ak.set_material([spine_bands[b][1], spine_bands[b][3]], "AA_Trim")

    # Canal technique CREUSE dans le dessus, et cadres transversaux en relief.
    # Le dessus de l'arete est la seule de ses faces que la camera de jeu voit :
    # laisse lisse, l'arete lisait comme une planche blanche posee sur le pont.
    # (Un bandeau sombre POSE ne suffisait pas : enferme dans le solide, il
    # etait simplement invisible. Il faut creuser.)
    ak.inset_panel(
        bm, [band[2] for band in spine_bands[1:-1]],
        "AA_Greeble", thickness=0.011, depth=-0.014,
    )
    for y in SPINE_FRAMES:
        hw, z_hi = lerp_row(SPINE, y, 1), lerp_row(SPINE, y, 2)
        ak.add_box(bm, (0.0, y, z_hi - 0.020), (hw * 2.20, 0.020, 0.050),
                   "AA_Greeble")

    # deux bandeaux cyan sur le dessus de l'arete : lisibles a la verticale.
    for sx in (ak.PORT, ak.STARBOARD):
        _strip(
            bm,
            [
                (0.420, lerp_row(SPINE, 0.420, 2) - 0.012, lerp_row(SPINE, 0.420, 2)),
                (0.700, lerp_row(SPINE, 0.700, 2) - 0.012, lerp_row(SPINE, 0.700, 2)),
                (0.980, lerp_row(SPINE, 0.980, 2) - 0.012, lerp_row(SPINE, 0.980, 2)),
            ],
            0.012,
            "AA_Emissive_Engine",
            center_x=sx * 0.048,
        )

    # ------------------------------------------------------- quille ventrale
    # Chanfrein NEGATIF : c'est le bas qui est coupe. Elle porte la moitie de la
    # hauteur gagnee par ce brief, et elle est invisible depuis la camera de jeu.
    keel_bands = _beam(
        bm, KEEL, chamfer=-0.016, top_frac=0.72,
        materials=("AA_Hull", "AA_Greeble", "AA_Greeble"),
    )
    for b, (y, _, _, _) in enumerate(KEEL[:-1]):
        if -0.30 <= y <= 0.42:
            ak.set_material([keel_bands[b][0], keel_bands[b][4]], "AA_Panel")
    for y in KEEL_FRAMES:
        hw = lerp_row(KEEL, y, 1)
        z_hi, z_lo = lerp_row(KEEL, y, 2), lerp_row(KEEL, y, 3)
        ak.add_box(
            bm, (0.0, y, (z_hi + z_lo) * 0.5 + 0.010),
            (hw * 2.14, 0.020, (z_hi - z_lo) * 0.92), "AA_Greeble",
        )

    # -------------------------------------------------- lisse de nez (chine)
    for sx in (ak.PORT, ak.STARBOARD):
        rings = []
        for y in CHINE_Y:
            w, f, crown, belly = section_params(y)
            zt = z_top(f, w, f, crown, belly)
            zb = z_bot(f, w, f, crown, belly)
            zc = zb + (zt - zb) * 0.44
            x0, x1 = f - 0.012, min(f + 0.024, w - 0.006)
            rings.append(
                ak.add_ring(
                    bm,
                    [
                        (sx * x0, y, zc + 0.010),
                        (sx * x1, y, zc + 0.004),
                        (sx * x1, y, zc - 0.004),
                        (sx * x0, y, zc - 0.010),
                    ],
                )
            )
        for i in range(len(rings) - 1):
            ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Greeble")
        ak.cap_ring(bm, list(reversed(rings[0])), "AA_Greeble")
        ak.cap_ring(bm, rings[-1], "AA_Greeble")

    # ------------------------------------------------------- tuyere d'axe
    # Posee au culot de la poutre dorsale. Elle ne rallonge PAS le vaisseau :
    # sa levre est a y = 1.185, en avant de la poupe (1.230, fixee par les
    # petales). C'est un point de mire, pas une dimension.
    ak.add_lathe(bm, TAIL_NOZZLE, 16, center_x=0.0, center_z=TAIL_NOZZLE_Z)
    bore = [
        _circle(bm, y, r, 0.0, TAIL_NOZZLE_Z, segments=16)
        for y, r in ((1.185, 0.056), (1.170, 0.050), (1.150, 0.040))
    ]
    for i in range(len(bore) - 1):
        ak.bridge_rings(bm, bore[i], bore[i + 1], "AA_Emissive_Engine")
    ak.fan_to_point(
        bm, bore[-1], bm.verts.new((0.0, TAIL_BORE_FLOOR, TAIL_NOZZLE_Z)),
        "AA_Emissive_Engine",
    )

    # ---------------------------------------- nacelles : fuseau, carenage, ecope
    for sign in (ak.PORT, ak.STARBOARD):
        ak.add_lathe(
            bm,
            NACELLE_PROFILE,
            NACELLE_SEGMENTS,
            center_x=sign * NACELLE_X,
            center_z=NACELLE_Z,
        )
        _nozzle_bore(bm, sign * NACELLE_X, NACELLE_Z)

        # epaule : le prolongement AVANT du fuseau, pose sur le pont. Sans elle
        # les « nacelles longues » du brief n'auraient couvert que 38 % de la
        # longueur au lieu des 60-75 % demandes.
        shoulder_base = (
            lambda y, s=sign: _deck_z(s * NACELLE_X, y) - 0.008
        )
        shoulder = _dome(bm, SHOULDER, sign * NACELLE_X, shoulder_base, "AA_Hull")
        for b in range(len(shoulder)):
            # flancs sombres (arcs 0 et DOME_ARC-2) : ils bordent le caniveau
            # d'un cote et l'aile de l'autre, et c'est ce doublet d'ombres qui
            # detache le fuseau du fuselage en vue de dessus.
            ak.set_material(
                [shoulder[b][k] for k in (0, DOME_ARC - 2) if shoulder[b][k]],
                "AA_Greeble",
            )
            if 2 <= b <= 5:
                ak.set_material(
                    [shoulder[b][k] for k in (2, 3) if shoulder[b][k]], "AA_Panel"
                )
        for y in SHOULDER_FRAMES:
            hw = lerp_row(SHOULDER, y, 1)
            tall = lerp_row(SHOULDER, y, 2)
            ak.add_box(
                bm,
                (sign * NACELLE_X, y, shoulder_base(y) + tall * 0.46),
                (hw * 2.06, 0.018, tall * 0.94),
                "AA_Greeble",
            )

        bands = _dome(
            bm, FAIRING, sign * NACELLE_X, lambda _y: NACELLE_Z, "AA_Hull"
        )
        # aplat bleu sur le dos du carenage, borde de deux rainures prises sur
        # les arcs voisins.
        for b, (y, _, _) in enumerate(FAIRING[1:-2]):
            if 0.50 <= y <= 0.90:
                ak.set_material(
                    [bands[b][k] for k in (2, 3, 4, 5) if bands[b][k]], "AA_Panel"
                )
            if 0.42 <= y <= 0.94:
                ak.set_material(
                    [bands[b][k] for k in (1, 6) if bands[b][k]], "AA_Greeble"
                )

        # ecope ventrale : la couche qui relie l'aile au fuseau par-dessous.
        intake_base = (
            lambda y, s=sign: z_bot(s * NACELLE_X, *section_params(min(y, 0.840)))
        )
        scoop = _dome(bm, INTAKE, sign * NACELLE_X, intake_base, "AA_Hull")
        # L'ecope est une piece MECANIQUE : laissee en blanc de coque elle lisait
        # de profil comme une grosse cloque lisse. Ventre sombre partout, flancs
        # bleus au milieu, bouche noire — et trois nervures.
        ak.set_material([f for f in scoop[0] if f], "AA_Greeble")  # bouche sombre
        for b in range(len(scoop)):
            ak.set_material(
                [scoop[b][k] for k in (3, 4, 5) if scoop[b][k]], "AA_Greeble"
            )
            if 1 <= b <= 3:
                ak.set_material(
                    [scoop[b][k] for k in (2, 6) if scoop[b][k]], "AA_Panel"
                )
        for y in INTAKE_FRAMES:
            hw = lerp_row(INTAKE, y, 1)
            deep = lerp_row(INTAKE, y, 2)
            ak.add_box(
                bm,
                (sign * NACELLE_X, y, intake_base(y) + deep * 0.42),
                (hw * 2.10, 0.018, abs(deep) * 0.96),
                "AA_Greeble",
            )
        # levre doree de l'ecope
        ak.add_box(
            bm,
            (sign * NACELLE_X, 0.098, intake_base(0.098) - 0.026),
            (0.150, 0.026, 0.020),
            "AA_Trim",
        )

        # bandeau cyan sur le FLANC SUPERIEUR du fuseau : visible du dessus.
        # L'offset (0.064) est la demi-corde du carenage a la hauteur du
        # bandeau, pas un nombre choisi : le carenage ayant maigri de 32 mm,
        # l'ancien 0.104 aurait laisse le bandeau flotter dans le vide.
        _strip(
            bm,
            [(0.620, 0.108, 0.120), (0.780, 0.118, 0.130), (0.920, 0.110, 0.122)],
            0.011,
            "AA_Emissive_Engine",
            center_x=sign * (NACELLE_X + 0.064),
        )
        # couronne emissive posee sur le DOS du collier : deuxieme temoin de
        # poussee lisible a la verticale, independamment de la vasque.
        ak.add_box(
            bm,
            (sign * NACELLE_X, 0.988, NACELLE_Z + 0.144),
            (0.070, 0.028, 0.014),
            "AA_Emissive_Engine",
        )

    # ---------------------------------------------- derives inclinees (ADR-0014)
    for sx in (ak.PORT, ak.STARBOARD):
        _fin(bm, sx)

    # -------------------------------------------- lisses de bout d'aile
    # Ce qui reste des anciens rails verticaux : une lisse basse, dont le seul
    # role est d'empecher la lame de lire comme un tranchant et de porter le
    # feu de bout d'aile.
    for sx in (ak.PORT, ak.STARBOARD):
        rings = []
        for y, up, down in RAIL:
            x = sx * _rail_x(y)
            z_hi = _deck_z(x, y) + up
            z_lo = _belly_z(x, y) - down
            rings.append(
                ak.add_ring(
                    bm,
                    [
                        (x + RAIL_HW, y, z_hi - 0.010),
                        (x + RAIL_HW * 0.35, y, z_hi),
                        (x - RAIL_HW * 0.35, y, z_hi),
                        (x - RAIL_HW, y, z_hi - 0.010),
                        (x - RAIL_HW, y, z_lo),
                        (x + RAIL_HW, y, z_lo),
                    ],
                )
            )
        for i in range(len(rings) - 1):
            # 0/2 = chanfreins d'arete, 1 = arete (jonc dore, vue du dessus),
            # 3/5 = flancs, 4 = dessous.
            band = ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Hull")
            ak.set_material([band[1]], "AA_Trim")
            ak.set_material([band[4]], "AA_Greeble")
            if 1 <= i <= 3:
                ak.set_material([band[3], band[5]], "AA_Panel")
        ak.cap_ring(bm, list(reversed(rings[0])), "AA_Greeble")
        ak.cap_ring(bm, rings[-1], "AA_Greeble")
        # feu de bout d'aile sur l'arete de la lisse (vu de dessus)
        y_mid = 0.480
        x_mid = sx * _rail_x(y_mid)
        z_mid = _deck_z(x_mid, y_mid) + lerp_row(RAIL, y_mid, 1)
        ak.add_box(
            bm, (x_mid, y_mid, z_mid - 0.006), (0.016, 0.140, 0.014),
            "AA_Emissive_Engine",
        )
        # ferrure de pied de lisse
        x_foot = sx * _rail_x(0.350)
        ak.add_box(
            bm, (x_foot, 0.350, _deck_z(x_foot, 0.350) + 0.006),
            (0.044, 0.070, 0.024), "AA_Greeble",
        )

    # ------------------------------------------------ longeron ventral + canon
    # deux tubes debouchant sous le nez, loges dans la quille
    barrel_z = _barrel_z()
    for sx in (ak.PORT, ak.STARBOARD):
        ak.add_lathe(
            bm,
            [
                (-0.900, 0.000, "AA_Greeble"),
                (-0.890, BARREL_R, "AA_Greeble"),
                (-1.020, BARREL_R, "AA_Greeble"),
                (-1.030, BARREL_R * 1.22, "AA_Trim"),
                (BARREL_TIP, BARREL_R * 1.18, "AA_Trim"),
                (BARREL_TIP, BARREL_R * 0.60, "AA_Greeble"),
                (-1.040, BARREL_R * 0.55, "AA_Greeble"),
                (-1.038, 0.000, "AA_Greeble"),
            ],
            12,
            center_x=sx * BARREL_X,
            center_z=barrel_z,
        )

    # platine doree ventrale + marquage rouge, posees sur le flanc de quille
    for sx in (ak.PORT, ak.STARBOARD):
        ak.add_box(
            bm, (sx * (lerp_row(KEEL, 0.150, 1) + 0.004), 0.150, -0.250),
            (0.014, 0.300, 0.060), "AA_Trim",
        )
        ak.add_box(
            bm, (sx * (lerp_row(KEEL, -0.180, 1) + 0.004), -0.180, -0.230),
            (0.014, 0.090, 0.036), "AA_Marking_Red",
        )

    # --------------------------------------- bloc mecanique dorsal (planche)
    # En avant des tuyeres, un bloc technique encastre dans l'arete : platine
    # sombre, deux joues dorees, hublot cyan. C'est le point de mire de la vue
    # de dessus — on le paie en detail.
    bay_z = lerp_row(SPINE, 0.185, 2)
    ak.add_box(bm, (0.0, 0.185, bay_z - 0.008), (0.104, 0.280, 0.044), "AA_Greeble")
    ak.add_box(bm, (0.0, 0.185, bay_z + 0.014), (0.072, 0.236, 0.014), "AA_Greeble")
    for sx in (ak.PORT, ak.STARBOARD):
        ak.add_box(bm, (sx * 0.062, 0.185, bay_z - 0.004),
                   (0.016, 0.300, 0.048), "AA_Trim")
        ak.add_box(bm, (sx * 0.038, 0.072, bay_z + 0.022),
                   (0.018, 0.070, 0.012), "AA_Emissive_Engine")
    ak.add_box(bm, (0.0, 0.150, bay_z + 0.022), (0.026, 0.130, 0.012),
               "AA_Emissive_Engine")
    ak.add_box(bm, (0.0, 0.300, bay_z + 0.018), (0.056, 0.036, 0.020),
               "AA_Marking_Red")

    # --------------------------------------------- petits bandeaux cyan du pont
    # Reperes d'echelle, tous poses sur des faces VUES DU DESSUS.
    # Les abscisses sont donnees en FRACTION DE CORDE et non en metres : le
    # bord d'attaque ayant recule de 10 deg, toute abscisse absolue heritee de
    # BRIEF-0033 tombait desormais hors de l'aile (a y = -0.15, x = 0.470 est
    # dans le vide : la demi-envergure n'y vaut plus que 0.463).
    for sx in (ak.PORT, ak.STARBOARD):
        for y, frac, length in (
            (-0.480, 0.62, 0.070),
            (0.120, 0.86, 0.080),
            (0.360, 0.84, 0.080),
            (0.520, 0.80, 0.070),
        ):
            x = _chord_x(y, frac)
            ak.add_box(
                bm,
                (sx * x, y, _deck_z(sx * x, y) + 0.004),
                (0.016, length, 0.010),
                "AA_Emissive_Engine",
            )

    # ---------------------------------------------------------------- greebles
    # Tous sur le pont, sur le dos des fuseaux ou sur les flancs de l'arete :
    # les faces arriere ne sont pas vues par la camera de jeu, y semer des
    # greebles serait du gaspillage.
    ak.greeble_strip(
        bm, (0.0, -0.150, bay_z - 0.030), (0.0, 0.030, bay_z - 0.030),
        count=5, seed=rng_seed,
        size_range=(0.014, 0.030), height_range=(0.006, 0.014),
    )
    # ⚠️ Toutes les abscisses ci-dessous ont ete REVUES par BRIEF-0034. Le bord
    # d'attaque a recule de 10 deg et le fuselage a maigri de 6 cm : quatre des
    # sept bandeaux tombaient hors de la coque, et deux tombaient sous l'epaule
    # de nacelle, ou ils auraient ete simplement invisibles.
    for k, sx in enumerate((ak.PORT, ak.STARBOARD)):
        base = rng_seed + 17 * (k + 1)
        # lame externe, en arriere (le plus visible en gros plan d'accueil).
        # Borne a y = 0.600 : au-dela commence l'echancrure du volet.
        _deck_greebles(bm, sx * 0.560, 0.440, 0.700, 6, base + 1,
                       size_range=(0.018, 0.038))
        # rampe technique le long de l'arete dorsale, sur le pont de fuselage
        _deck_greebles(bm, sx * 0.128, -0.120, 0.320, 6, base + 2,
                       size_range=(0.014, 0.028), height_range=(0.005, 0.012))
        # lame externe, entre les deux rainures longitudinales
        _deck_greebles(bm, sx * 0.520, 0.080, 0.420, 5, base + 3,
                       size_range=(0.016, 0.032), height_range=(0.005, 0.011))
        # glove avant, en avant de l'epaule de nacelle
        _deck_greebles(bm, sx * 0.155, -0.620, -0.440, 4, base + 4,
                       size_range=(0.013, 0.026), height_range=(0.005, 0.010))
        # flancs de nez
        _deck_greebles(bm, sx * 0.055, -0.880, -0.740, 3, base + 5,
                       size_range=(0.011, 0.021), height_range=(0.004, 0.009))
        # dos du carenage de tuyere
        ak.greeble_strip(
            bm,
            (sx * (NACELLE_X - 0.056), 0.620, 0.118),
            (sx * (NACELLE_X - 0.056), 0.900, 0.118),
            count=5,
            seed=base + 6,
            size_range=(0.016, 0.030),
            height_range=(0.006, 0.014),
        )
        # bout d'aile, en avant de la lisse
        _deck_greebles(bm, sx * 0.590, 0.380, 0.540, 4, base + 7,
                       size_range=(0.014, 0.026), height_range=(0.004, 0.009))

    return ak.new_object("Specter9_Details", bm)


def _barrel_z() -> float:
    """Axe des tubes du canon : centre sur la section de quille sous le nez."""
    y = -1.020
    return (lerp_row(KEEL, y, 2) + lerp_row(KEEL, y, 3)) * 0.5


# ==========================================================================
# Pieces mobiles (ak.moving_part -> nœuds glTF separes)
# ==========================================================================


def build_flap(side: float) -> ak.MovingPart:
    """Volet de bord de fuite : l'aft de l'aile externe, echancre dans la coque.

    ⚠️ Le PIVOT est toute la primitive. L'origine du nœud est posee sur la ligne
    de charniere ; sans cela le volet decrirait un arc de cercle autour du nez
    du vaisseau au lieu de battre sur son axe — et le defaut ne se verrait
    qu'une fois anime.
    """
    tag = "L" if side > 0 else "R"
    bm = bmesh.new()
    x_in = FLAP_ROOT_X + FLAP_SIDE_GAP

    rings = []
    for y in FLAP_STATIONS:
        w, f, crown, belly = section_params(y)
        x_out = w
        if x_out - x_in < 0.004:
            continue
        xs = [x_in + (x_out - x_in) * t for t in reversed(FLAP_T)]
        top = [(side * x, y, z_top(x, w, f, crown, belly)) for x in xs]
        bot = [(side * x, y, z_bot(x, w, f, crown, belly)) for x in reversed(xs)]
        rings.append(ak.add_ring(bm, top + bot))

    n = len(FLAP_T)
    for i in range(len(rings) - 1):
        band = ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Hull")
        # Le ring vaut `top` (n points, du bord d'aile vers l'emplanture) puis
        # `bot` (n points, retour) : le segment n-1 est la tranche d'EMPLANTURE
        # et le segment 2n-1 la tranche de BOUT D'AILE. Les peindre distingue le
        # volet de l'aile meme ferme, sans toucher aux surfaces portantes.
        ak.set_material([band[n - 1]], "AA_Greeble")
        ak.set_material([band[2 * n - 1]], "AA_Trim")
    # face de charniere : sombre, elle EST la ligne d'articulation
    ak.cap_ring(bm, list(reversed(rings[0])), "AA_Greeble")
    ak.cap_ring(bm, rings[-1], "AA_Greeble")

    # marquage de bord de fuite (or) sur le dessus, visible a la verticale
    # ⚠️ Ce marquage doit rester EN ARRIERE du pivot. Pose a cheval sur la
    # charniere, il devient le point le plus contraignant du volet et fait
    # tomber le plafond de debattement a 2,8 deg — mesure faite, pas devinee.
    ak.add_box(
        bm,
        (side * 0.640, 0.795, z_top(0.640, *section_params(0.795)) + 0.003),
        (0.120, 0.020, 0.008),
        "AA_Trim",
    )

    # Le x du pivot ne change RIEN au mouvement (une rotation autour d'un axe
    # parallele a X laisse x invariant) — il place seulement le nœud. On le met
    # au milieu de la section d'emplanture pour qu'il soit dans la piece.
    y0 = FLAP_STATIONS[0]
    pivot = (
        side * (x_in + lerp_table(PLANFORM, y0)) * 0.5,
        y0,
        FLAP_HINGE_Z,
    )
    return ak.moving_part(f"Flap_{tag}", bm, pivot)


def build_nozzle(side: float) -> ak.MovingPart:
    """Couronne de petales de tuyere, FERMEE au repos.

    Elle sera mise a l'ECHELLE cote Godot (pas tournee) : le pivot est donc le
    centre du COL, et la couronne s'ouvre en s'evasant autour de lui.
    Les petales du haut sont raccourcis de `PETAL_SCARF` : c'est ce biseau qui
    laisse voir la vasque emissive depuis une camera a 20 deg de la verticale.
    """
    tag = "L" if side > 0 else "R"
    cx, cz = side * NACELLE_X, NACELLE_Z
    bm = bmesh.new()

    step = 2.0 * math.pi / NOZZLE_PETALS
    gap = math.radians(PETAL_GAP_DEG)
    last = len(PETAL_SECTIONS) - 1
    for p in range(NOZZLE_PETALS):
        mid = p * step
        a0, a1 = mid - step * 0.5 + gap * 0.5, mid + step * 0.5 - gap * 0.5
        scarf = PETAL_SCARF * (0.5 + 0.5 * math.sin(mid))
        angles = [a0 + (a1 - a0) * k / (PETAL_ARC - 1) for k in range(PETAL_ARC)]
        rings = []
        for k, (y, r_in, r_out) in enumerate(PETAL_SECTIONS):
            yy = y - scarf * (k / last)
            outer = [
                (cx + r_out * math.cos(a), yy, cz + r_out * math.sin(a))
                for a in angles
            ]
            inner = [
                (cx + r_in * math.cos(a), yy, cz + r_in * math.sin(a))
                for a in reversed(angles)
            ]
            rings.append(ak.add_ring(bm, outer + inner))
        for i in range(len(rings) - 1):
            mat = "AA_Trim" if i == len(rings) - 2 else "AA_Greeble"
            ak.bridge_rings(bm, rings[i], rings[i + 1], mat)
        ak.cap_ring(bm, list(reversed(rings[0])), "AA_Greeble")
        ak.cap_ring(bm, rings[-1], "AA_Trim")

    pivot = (cx, PETAL_SECTIONS[0][0], cz)
    return ak.moving_part(f"Nozzle_{tag}", bm, pivot)


# ==========================================================================
# Points d'attache
# ==========================================================================


def _leading_edge_station(half_span: float) -> float:
    """Station `y` du **bord d'attaque** ou la demi-envergure vaut `half_span`.

    On ne parcourt que la branche avant du planform : du nez (`y = -1.230`) au
    coin avant du bout d'aile (`y = 0.418`, largeur maximale). Sur cette branche
    la demi-envergure croit de facon monotone, donc l'inversion est unique.
    """
    tip_y = _tip_front_station()
    for i in range(len(PLANFORM) - 1):
        y0, w0 = PLANFORM[i]
        y1, w1 = PLANFORM[i + 1]
        if y1 > tip_y:  # on a atteint le coin avant : au-dela c'est le culot
            break
        if w0 <= half_span <= w1:
            t = (half_span - w0) / (w1 - w0)
            return y0 + (y1 - y0) * t
    raise ak.ContractError(
        f"demi-envergure {half_span} hors du bord d'attaque du planform"
    )


def _tip_front_station() -> float:
    """Station `y` du coin avant du bout d'aile (premiere largeur maximale)."""
    return max(PLANFORM, key=lambda p: p[1])[0]


def build_attach_points() -> list:
    """Positions **derivees de la geometrie**, jamais devinees.

    Les offsets de tir et de trainee du controleur joueur sont lus ici : une
    approximation se verrait a l'ecran. Les sept muzzles mappent l'echelle de
    puissance (spec 9.1) : twin de nez (Muzzle_L/R) des le power 1, canons
    d'aile (Muzzle_Wing_L/R) au power 3, canon d'axe (Muzzle_C) au power 4,
    pods de bout d'aile (Muzzle_Tip_L/R) au power 5.
    """
    points: list = []

    # --- twin de nez : dans l'axe des tubes, juste devant leur pointe. --------
    points += list(ak.attach_pair("Muzzle", BARREL_X, MUZZLE_Y, _barrel_z()))

    # --- canon d'axe central : entre les deux tubes, meme plan de tir. --------
    points.append(ak.attach_point("Muzzle_C", (0.0, MUZZLE_Y, _barrel_z())))

    # --- canons d'aile : sur le bord d'attaque, a la station ou la demi-
    #     envergure vaut WING_MUZZLE_X ; z pris sur la surface superieure d'aile
    #     a cette station (anhedral compris via z_top).
    y_wing = _leading_edge_station(WING_MUZZLE_X)
    z_wing = z_top(WING_MUZZLE_X, *section_params(y_wing))
    points += list(ak.attach_pair("Muzzle_Wing", WING_MUZZLE_X, y_wing, z_wing))

    # --- pods de bout d'aile : sur le bord d'attaque, a la station ou la
    #     demi-envergure vaut TIP_MUZZLE_X. BRIEF-0034 : c'est un changement de
    #     DERIVATION, pas de role — le point reste a |x| = 0.800 comme l'exige
    #     le brief. On ne peut plus le prendre au coin de largeur maximale :
    #     celui-ci est desormais a y = 0.580, au ras de la charniere de volet,
    #     et le muzzle se serait retrouve sur une piece mobile.
    y_tip = _leading_edge_station(TIP_MUZZLE_X)
    z_tip = z_top(TIP_MUZZLE_X, *section_params(y_tip))
    points += list(ak.attach_pair("Muzzle_Tip", TIP_MUZZLE_X, y_tip, z_tip))

    # --- tuyeres : DERRIERE la couronne de petales, sinon la plume de trainee
    #     sortirait du milieu de la tuyere et traverserait les petales. Le z
    #     suit l'axe releve de la vasque.
    exit_y = PETAL_SECTIONS[-1][0] + 0.004
    points += list(
        ak.attach_pair("Engine", NACELLE_X, exit_y, NACELLE_Z + 0.018)
    )

    # --- cockpit : centre du volume de verriere. ------------------------------
    y_mid = (CANOPY[0][0] + CANOPY[-1][0]) * 0.5
    peak = max(CANOPY, key=lambda s: s[2])
    z_mid = lerp_table(CROWN, y_mid) - CANOPY_SINK + peak[2] * 0.45
    points.append(ak.attach_point("Cockpit", (0.0, y_mid, z_mid)))

    return points


# ==========================================================================
# Assemblage
# ==========================================================================


def _triangulate_ngons(obj) -> None:
    """Triangule les seules n-gons (> 4 sommets), en place.

    Sans cela, l'exporteur glTF renonce aux tangentes (« Tangent space can only
    be computed for tris/quads ») et ADR-0011 §2 — qui exige *UV et tangentes*
    pour que les feuilles de detail aient un espace normal — reste inapplique.
    Les n-gons viennent des culots (`ak.cap_ring`), une poignee de faces : on ne
    triangule pas les quads, qui restent lisibles et n'ont aucun probleme.
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons)
    bm.to_mesh(obj.data)
    bm.free()


def _finish(obj, bevel: float, segments: int = 1) -> None:
    """Passe de finition commune a la coque et aux pieces mobiles."""
    ak.cleanup(obj)
    # Chanfrein a UN segment, plus etroit (3,5 mm) que la moitie du creux des
    # rainures (5 mm) et des panneaux (11 mm) : la marche reste franche.
    # ADR-0011 autorise 2 segments ; essaye au rendu, il arrondit les rainures
    # fines au point de les effacer — c'est exactement le defaut « plastique
    # moule » qu'on corrige. On reste donc a 1 segment : choix de LECTURE.
    ak.bevel_sharp_edges(obj, width=bevel, segments=segments, angle_deg=34.0)
    ak.shade_smooth_by_angle(obj, angle_deg=34.0)
    _triangulate_ngons(obj)
    # UV par projection en boite (ADR-0011 §2) : support des feuilles de detail
    # repetables en niveaux de gris, appliquees cote Godot. Aucune texture n'est
    # embarquee dans le .glb — seulement les coordonnees.
    ak.box_project_uv(obj, TEXELS_PER_METER)


def _flap_travel_limit(part: ak.MovingPart) -> float:
    """Plafond de braquage du volet, en degres, MESURE sur le maillage livre.

    Le volet tourne autour d'un axe parallele a X passant par son pivot. Un
    sommet (y, z) va en
        y' = y_p + (y - y_p) cos t - (z - z_p) sin t
    et mord la cloison des que `y' < FLAP_HINGE_Y`. Le plafond est le plus
    petit angle qui fait mordre UN sommet, dans l'un ou l'autre sens.

    Pourquoi le mesurer plutot que le calculer : la valeur depend de la forme
    du volet, donc de la corde de l'aile a l'emplanture, donc du planform. Elle
    change des qu'on touche a la silhouette — et `ShipFlight` est regle dessus.
    """
    _, y_p, z_p = part.pivot
    limit = math.pi * 0.5
    for vert in part.obj.data.vertices:
        # repere d'auteur : le maillage n'a pas encore ete transporte en Godot
        dy, dz = vert.co.y - y_p, vert.co.z - z_p
        for sign in (1.0, -1.0):
            # resout dy*cos(t) - sign*dz*sin(t) = -(y_p - FLAP_HINGE_Y)
            a, b = dy, -sign * dz
            target = FLAP_HINGE_Y - y_p          # negatif (= -FLAP_GAP)
            radius = math.hypot(a, b)
            if radius < 1e-9 or abs(target) > radius:
                continue                          # ce sommet ne mord jamais
            phase = math.atan2(b, a)
            angle = math.acos(target / radius) + phase
            # ramene dans (0, pi/2] : hors de cette plage, ce n'est plus un
            # braquage de volet mais un demi-tour de la piece.
            angle = angle % (2.0 * math.pi)
            if 1e-4 < angle <= math.pi * 0.5:
                limit = min(limit, angle)
    return math.degrees(limit)


def main() -> None:
    ak.reset_scene()
    ak.set_faction(ak.FACTION_VANGUARD)

    ship = ak.join_objects([build_hull(), build_details()], "Specter9")
    _finish(ship, bevel=0.0035)

    parts = [
        build_flap(ak.PORT),
        build_flap(ak.STARBOARD),
        build_nozzle(ak.PORT),
        build_nozzle(ak.STARBOARD),
    ]
    for part in parts:
        _finish(part.obj, bevel=0.0022)

    travel = min(_flap_travel_limit(p) for p in parts if p.obj.name.startswith("Flap"))

    report = ak.export_hull(
        ship, build_attach_points(), OUTPUT, CONTRACT, parts=parts
    )

    # Le contrat du kit ne borne qu'un PLAFOND de hauteur. Le defaut corrige par
    # BRIEF-0033 etait l'inverse : une coque trop PLATE reste conforme. On
    # verifie donc le plancher ici, et on echoue bruyamment.
    if report.size[1] < MIN_HEIGHT_Y:
        raise ak.ContractError(
            f"hauteur Y = {report.size[1]:.4f} m < plancher {MIN_HEIGHT_Y:.2f} m "
            "(BRIEF-0033 : la coque doit cesser de lire comme une plaque)"
        )
    print(
        f"  hauteur/longueur : {report.size[1] / report.size[2]:.1%} "
        f"(cible BRIEF-0034 : 25-29 %)"
    )
    print(f"  volets : plafond de debattement mesure {travel:.1f} deg")
    _print_plan_share()


def _print_plan_share() -> None:
    """Repartition de la surface en PLAN entre corps et aile (ADR-0014).

    ADR-0014 interdit de conclure sur une repartition de formes a partir d'un
    rapport de boite englobante. Voici la mesure qui aurait du etre faite :
    l'aire du plan, integree station par station, et la part qu'y prend l'aile
    au-dela du groupe fuselage + nacelles.
    """
    body_edge = NACELLE_X + max(hw for _, hw, _ in FAIRING)
    step = 0.002
    total = wing = 0.0
    y = -HALF_L
    while y <= 0.860:
        w = section_cut(y)
        total += 2.0 * w * step
        wing += 2.0 * max(w - body_edge, 0.0) * step
        y += step
    print(
        f"  plan : aile hors groupe fuselage+nacelles = {wing / total:.0%} "
        f"de la surface vue de dessus (bord du groupe a |x| = {body_edge:.3f})"
    )


if __name__ == "__main__":
    main()
