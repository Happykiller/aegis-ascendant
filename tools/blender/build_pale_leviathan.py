"""build_pale_leviathan.py — coque 3D du Pale Leviathan, boss final (BRIEF-0040).

    ./scripts/build-hull.sh pale_leviathan        # JAMAIS un `blender45` nu : -t 1

Produit `assets/imported/models/bosses/pale_leviathan.glb`.

Le script EST la source de l'asset (ADR-0008) : aucun `.blend` n'est versionne.
Il est deterministe (tout alea passe par `random.Random(seed)`, jamais par le
module `random` global) et s'auto-valide : `ak.export_hull()` relit le `.glb`
produit et echoue bruyamment si la bounding box, le budget de triangles, les
materiaux, le centrage du pivot ou les points d'attache sortent du contrat.

Reference de design : les trois planches annotees
`assets/reference/concepts/pale_leviathan_parts_sheet.png` (4 vues cotees +
eclate nomme — la reference principale), `..._core_states_sheet.png` (noyau
ferme / vortex / puits a anneaux) et `..._phases_sheet.png` (les 4 etats de
destruction). Deux erreurs de legende connues des planches ne sont PAS
recopiees : le 3e segment d'epine y est note « SPIKE MID » alors que le contrat
dit `Tip`, et les quatre vues sont cotees « 14,0 m » alors que la vue de face
montre les 11 m de largeur.

Repere d'auteur (ADR-0008) : face menacante -Y, dessus +Z, **babord +X**
(cf. l'en-tete d'aegis_kit : le signe de X est contre-intuitif).


CE QUE BRIEF-0040 CHANGE — trois verrous leves d'un coup
========================================================
1. **Rien n'etait animable.** La version precedente livrait des objets separes
   (`Core`, `Shell_Crescent`, `Spike_01..04`) mais **aucun appel a
   `ak.moving_part()`** : chaque piece avait son origine au centre du modele,
   donc tournait autour du boss et non autour de sa charniere. Tout ce qui bouge
   passe desormais par `ak.moving_part()`, qui pose l'origine SUR le pivot et
   accepte un `parent` (chaines articulees). 29 pieces mobiles, 3 niveaux de
   chaine.
2. **Rien n'etait texturable.** Aucun script de boss n'appelait
   `ak.box_project_uv()` : sans UV ni tangentes, le jeu de textures deja livre
   (`assets/source/textures/leviathan/`) n'avait nulle part ou se poser. Chaque
   maillage est desormais deplie a `TEXELS_PER_METER`, dans le meme geste.
3. **Les dimensions** passent a 11,0 x 14,0 m, hauteur <= 3,20 m, budget
   40 000 triangles (ADR-0018).


LE PLAN VIENT DE LA MECANIQUE, PAS SEULEMENT DE LA PLANCHE
==========================================================
La camera de jeu regarde le plan **de dessus** (20 deg d'ecart a la verticale).
Ce que le joueur voit d'un boss de 14 m, c'est sa face +Z d'auteur. Toute la
lecture du combat est donc posee dans ce plan :

  * le **puits** (`Ring_01..05`, `Heart`) descend en -Z d'auteur, et la gueule
    s'ouvre vers le HAUT, face a la camera : la phase 4 se joue dans l'axe de
    vue, le joueur plonge litteralement dans l'ecran ;
  * la coquille (`Shell_Ring`) orbite autour de l'axe **vertical** du noyau, si
    bien que les quatre plaques defilent lateralement face au joueur — la
    fenetre de tir de la phase 1 est une geometrie, pas un minuteur ;
  * la coque est **plate** (3,0 m d'epaisseur pour 14 m de long) : tout ce qui
    compte est visible d'en haut, rien n'est cache sous le ventre.

Consequences directes sur les debattements, et ce sont elles qui ont fixe les
chiffres — pas l'oeil :

  * `Maw_Lip` s'ouvre en se **relevant vers l'arriere** (+90 deg autour de X
    Godot fait monter ce qui est en avant du pivot). Sa charniere est donc
    posee DERRIERE la gueule, hors du puits : a 90 deg la levre se dresse a
    l'exterieur de l'ouverture, et la vue de dessus sur le tunnel est totale.
    Une charniere posee devant, ou au centre, aurait plonge la levre dans la
    coque ou l'aurait laissee en travers du puits ;
  * `Plate_0X` se **souleve vers l'exterieur** (charniere tangentielle sur son
    bord interne). Elle ne peut pas tomber vers le bas : sous elle il y a la
    coquille, puis le pont. Le geste lit comme une ecaille qu'on arrache, ce que
    montre le panneau CORE EXPOSED ;
  * les quatre epines sont montees sur des **mats dorsaux** qui les tiennent
    au-dessus du pont (z >= 0,90) : leur pointage de +/-40 deg balaie l'aplomb
    des lobes avant et arriere, et une epine posee a fleur de coque s'y serait
    enterree des le premier degre.

Chaque debattement est REMESURE a chaque build sur le maillage livre
(`_clearance_table()`, plus bas). La lecon la plus chere du projet est qu'un
contrat de bounding box valide une pose fixe et ne voit RIEN d'un defaut
d'animation (le Specter-9 a coute quatre briefs sur ce seul point).


CONTRAT DE NOMS (le code du combat sera ecrit contre lui)
=========================================================
    Body                                   maillage porteur, statique
    Shell_Ring -> Shell_Crescent -> Plate_01..04     orbite / bascule / chute
    Core -> Maw_Lip -> Node_01..03                   rotation / ouverture / repli
    Core -> Ring_01..05                              tunnel, vitesses distinctes
    Core -> Heart                                    statique, mais noeud a part
    Spike_0X -> Spike_0X_Mid -> Spike_0X_Tip         epaule / coude / pointe

⚠️ `Heart` est declare « statique » au contrat, et il l'est : rien ne l'anime.
Il passe pourtant par `ak.moving_part()`, seule primitive du kit qui sache
poser un `parent`. C'est deliberé, et c'est la meme decision que pour le `Core`
du Choir Harvester.

⚠️ **Piege d'integration a connaitre** : `Maw_Lip`, `Ring_01..05` et `Heart` sont
enfants de `Core`. Cacher le noeud `Core` (`visible = false`) cacherait donc TOUT
le puits avec lui. Pour escamoter le noyau a la phase 4, agir sur son
**maillage** (materiau, echelle) et non sur la visibilite du noeud.
"""

from __future__ import annotations

import math
import os
import random
import sys

import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "lib"))
_REPO = os.path.dirname(os.path.dirname(_HERE))

import aegis_kit as ak  # noqa: E402  (doit suivre l'ajout au sys.path)

# ==========================================================================
# Contrat (ADR-0008, dimensions amendees par ADR-0018)
# ==========================================================================

CONTRACT = ak.HullContract(
    name="Pale Leviathan",
    width_x=11.00,      # Godot X — portee par les pointes de Spike_01 et _03
    length_z=14.00,     # Godot Z — portee a elle seule par `Body` (bec et dard)
    max_height_y=3.20,  # Godot Y — plafond de lisibilite en vue de dessus
    tri_budget=40_000,  # ADR-0018 ; plafond ADR-0011 de la classe boss : 90 000
    required_materials=ak.MATERIAL_ORDER,  # les 7 : la planche les utilise tous
    required_attach_points=(
        "Core_Center",
        "Maw_Center",
        "Tunnel_End",
        "Muzzle_C",
        "Muzzle_L",
        "Muzzle_R",
        "Muzzle_Plate_01",
        "Muzzle_Plate_02",
        "Muzzle_Plate_03",
        "Muzzle_Plate_04",
        "Muzzle_Spike_01",
        "Muzzle_Spike_02",
        "Muzzle_Spike_03",
        "Muzzle_Spike_04",
    ),
)

OUTPUT = os.path.join(_REPO, "assets/imported/models/bosses/pale_leviathan.glb")

#: Graine maitresse. Toute la variation (ecailles, craquelures, greebles) en
#: derive. Rejouer le script est byte-identique.
SEED = 481516

#: Densite du depliage UV : 0,18 tuile/m, soit **une tuile pour 5,5 m**. Sur une
#: coque de 14 m, les ecailles de `leviathan_scales_height` (periode mesuree
#: 0,99 m) lisent a ~1,1 m — l'echelle des planches. Reperes du projet : la
#: citadelle est a 0,12 (une tuile pour 8,33 m), le Specter-9 a 4,0 (25 cm).
TEXELS_PER_METER = 0.18

HALF_L = CONTRACT.length_z / 2.0   # 7,00 — bec en -Y, dard en +Y
HALF_W = CONTRACT.width_x / 2.0    # 5,50 — pointes d'epines

# ==========================================================================
# Le corps — un disque blinde plat, perce d'un puits central
# ==========================================================================

N_SEG = 40   # segments angulaires du disque (multiple de 4 et de 8)

#: Contour de la coque, en coordonnees polaires : (azimut deg, rayon m).
#: L'azimut part de +X (babord) et tourne vers +Y (arriere) ; -Y (l'avant, la
#: face menacante) est donc a 270 deg. Le bec et le dard portent a eux seuls les
#: 14 m de long ; les flancs restent nettement en deca des 11 m de large, que
#: les epines vont chercher. Le contour est volontairement DISSYMETRIQUE :
#: l'epaule babord est pleine vers l'arriere, l'epaule tribord vers l'avant.
#: ⚠️ Le dard est FOURCHU, et les deux pointes tombent sur des azimuts
#: ECHANTILLONNES (81 et 99 deg, multiples des 9 deg du pas angulaire) : c'est
#: la seule facon d'atteindre exactement les 7,00 m de demi-longueur. Une pointe
#: posee entre deux echantillons est rabotee par la discretisation, la longueur
#: tombe a 13,7 m — dans la tolerance — mais le centre derive de 15 cm, sept
#: fois la tolerance de pivot. La premiere version, dard en pointe unique,
#: lisait comme une soucoupe ; la fourche rend la lecture « creature ».
BODY_R: list[tuple[float, float]] = [
    (0.0, 4.78), (25.0, 4.92), (50.0, 5.45), (66.0, 6.30), (72.0, 6.75),
    (81.0, HALF_L / math.sin(math.radians(81.0))), (87.0, 6.55),
    (93.0, 6.30), (99.0, HALF_L / math.sin(math.radians(99.0))),
    (108.0, 6.05), (130.0, 5.05), (155.0, 4.72), (180.0, 4.68), (205.0, 4.90),
    (230.0, 5.40), (255.0, 6.40), (270.0, HALF_L), (285.0, 6.45), (310.0, 5.20),
    (335.0, 4.70), (360.0, 4.78),
]

#: Stations radiales ABSOLUES du pont central (le disque blinde) : levre du
#: puits, gorge de la coquille, contre-levre exterieure. Elles sont absolues et
#: non fractionnaires parce que la coquille orbite dessus : la piste doit etre
#: un solide de revolution, sinon l'orbite raboterait la coque une fois sur deux.
DISC_R = (1.96, 2.06, 2.40, 2.84, 3.18, 3.50, 3.86, 4.14)
DISC_TOP = (0.60, 0.22, 0.18, 0.18, 0.20, 0.36, 0.60, 0.54)
DISC_BOT = (-0.92, -1.02, -1.08, -1.10, -1.08, -1.04, -0.96, -0.90)

#: ⚠️ INVARIANT DE PISTE — (rayon min, rayon max, plafond impose a la COQUE).
#: La coquille orbite au-dessus du disque : tout ce que la coque pose sous elle
#: doit rester sous ce plafond. Un pont d'arme, un mat ou un greeble qui deborde
#: se fait raboter une fois sur deux, et la bounding box au repos n'en dit rien.
#: La premiere version de ce script a perdu la mesure exactement la : ponts
#: d'armes de proue a r = 3,5 (500 triangles en interpenetration avec l'anneau)
#: et mats d'epine a demi-largeur constante (dans les plaques).
SHELL_TRACK = ((2.10, 3.06, 0.24), (3.06, 3.76, 0.88))

#: Jupe exterieure : trois stations en FRACTION de la corde restante
#: (`.claude/resources/pratique-detail-en-fraction-de-corde.md`). Le jour ou le
#: contour bouge, la jupe suit au lieu de flotter.
SKIRT_F = (0.34, 0.68, 1.00)
SKIRT_POW = 1.15          # galbe de la jupe (1 = conique, >1 = creuse)
RIM_HALF = 0.045          # demi-epaisseur de la tranche : jamais un fil de rasoir

#: Paroi INTERIEURE du puits : (z, rayon). Elle part de la levre et descend au
#: coeur. C'est elle qui borne les anneaux — leur rayon en est DERIVE.
SHAFT: tuple[tuple[float, float], ...] = (
    (0.60, 1.96), (0.26, 1.92), (-0.10, 1.84), (-0.44, 1.66),
    (-0.76, 1.42), (-1.04, 1.12), (-1.26, 0.76), (-1.44, 0.32),
)
SHAFT_MATS = ("AA_Greeble", "AA_Panel", "AA_Panel", "AA_Greeble",
              "AA_Panel", "AA_Greeble", "AA_Panel")

#: Ventre : peau exterieure du puits, de la premiere station basse au culot.
BELLY: tuple[tuple[float, float], ...] = (
    (-0.92, 1.96), (-1.14, 1.70), (-1.32, 1.20), (-1.46, 0.70), (-1.54, 0.34),
)

# ==========================================================================
# Le noyau — la cible, et le pivot de tout le puits
# ==========================================================================

CORE_RXY = 1.52           # demi-grand axe du noyau (aplati : la coque est plate)
CORE_RZ = 0.68
CORE_Z = 0.20             # centre du noyau = pivot de `Core`
CORE_SEG = 32             # c'est LA cible du joueur : on la paie ronde
CORE_RINGS = 15
CORE_CRUST_P = 0.78       # part des facettes qui deviennent croute violette
CORE_CRUST_LIFT = 0.030
CORE_CRUST_INSET = 0.030

HEART_Z = -1.24
HEART_R = 0.12

# ==========================================================================
# La levre de la gueule (`Maw_Lip`, legendee OUTER RIM sur la planche)
# ==========================================================================
#
# Secteur arriere de l'ouverture, arque au-dessus du noyau, griffes en surplomb.
# Sa charniere est une droite parallele a X posee DERRIERE l'ouverture : a
# +90 deg (Godot `rotation.x`) toute la piece se dresse a l'exterieur du puits,
# qui se degage entierement en vue de dessus.

LIP_A = 42.0              # azimut de depart (deg)
LIP_B = 138.0             # azimut de fin — 96 deg de secteur, centre sur +Y
LIP_SEG = 14
#: (rayon, z du dessus). L'epaisseur descend de LIP_T sous cette nappe.
LIP_PROFILE: tuple[tuple[float, float], ...] = (
    (2.00, 0.86), (1.86, 0.98), (1.58, 1.06), (1.30, 1.06), (1.10, 1.00),
)
LIP_T = 0.14
LIP_PIVOT = (0.0, 2.14, 0.80)
#: Griffes du surplomb : elles mordent au-dessus du noyau sans le toucher.
LIP_FANGS = (52.0, 70.0, 90.0, 110.0, 128.0)
LIP_FANG_R = (1.12, 0.92)     # (base, pointe) en rayon
LIP_FANG_Z = (0.96, 0.93)

#: Noeuds gravitiques : azimut sur la levre, longueur, inclinaison sortante.
NODE_AZ = (58.0, 92.0, 124.0)
NODE_R = 1.56             # rayon d'implantation, sur la crete de la levre
NODE_Z = 1.05
NODE_LEN = (0.56, 0.60, 0.52)
NODE_TILT = 42.0          # deg au-dessus du plan, penche vers l'exterieur
NODE_W = 0.18             # demi-largeur de l'embase

# ==========================================================================
# Le puits — cinq anneaux a ouverture decalee (« OFFSET GATE »)
# ==========================================================================
#
# (z, azimut du milieu de l'ouverture, largeur radiale). Le rayon externe est
# DERIVE de la paroi du puits (`shaft_radius`), jamais pose a la main : le jour
# ou le puits change de galbe, les anneaux le suivent au lieu de le traverser.
# L'ouverture fait RING_GAP deg et se decale d'un anneau au suivant — c'est ce
# que la planche nomme « OFFSET GATE », et c'est la mecanique de la phase 4.
RINGS: tuple[tuple[float, float, float], ...] = (
    (-0.12, 0.0, 0.24),
    (-0.44, 72.0, 0.24),
    (-0.74, 144.0, 0.22),
    (-0.98, 216.0, 0.20),
    (-1.18, 288.0, 0.18),
)
RING_GAP = 70.0           # deg d'ouverture
RING_CLEAR = 0.20         # jeu radial impose entre l'anneau et la paroi
RING_T = 0.11             # epaisseur
RING_SEG = 26             # segments sur les 290 deg de matiere

# ==========================================================================
# La coquille : anneau porteur, croissant, quatre plaques
# ==========================================================================
#
# Trois niveaux, et c'est delibere (BRIEF-0040) : `Shell_Ring` porte l'orbite,
# `Shell_Crescent` la bascule, `Plate_0X` la chute. Un axe, un noeud, un
# ecrivain — empiler deux de ces mouvements sur le meme noeud produirait, le
# jour ou les deux sont actifs, une composition d'Euler que personne ne sait
# relire.

SHELL_PIVOT = (0.0, 0.0, CORE_Z)   # l'axe du noyau, et rien d'autre

#: Anneau porteur : deux rangees de tuiles tangentielles qui se recouvrent.
#: (rayon interne, rayon externe, z interne, z externe, tuiles, dephasage)
RING_ROWS: tuple[tuple[float, float, float, float, int, float], ...] = (
    (2.20, 2.60, 0.56, 0.62, 18, 0.00),
    (2.54, 2.94, 0.62, 0.52, 15, 0.43),
)
RING_Z_BASE = 0.34        # les tuiles plongent dans la gorge : pas de flottement
RING_OVERLAP = 1.30

#: Croissant : l'anneau INCOMPLET de la charte. Il court de -135 a +95 deg,
#: soit 230 deg ; les 130 deg manquants ouvrent sur le quadrant avant-tribord.
CR_PHI_A = -135.0
CR_PHI_B = 95.0
CR_OVERLAP = 1.26
#: ⚠️ La charniere est posee derriere les PLAQUES (y = 3,66 au plus loin), pas
#: derriere le croissant seul (y = 3,02) : les plaques sont ses enfants, elles
#: basculent avec lui, et une plaque restee en arriere de l'axe plongeait dans
#: la coque des les premiers degres (mesure : morsure a 56 deg de chute).
CR_PIVOT = (0.0, 3.86, 0.94)
#: (rayon interne, rayon externe, tuiles, elevation, dephasage)
CR_ROWS: tuple[tuple[float, float, int, float, float], ...] = (
    (2.26, 2.66, 20, 0.00, 0.00),
    (2.60, 3.02, 16, 0.05, 0.42),
)
CR_Z_BASE = 0.88
CR_TOP = 1.06

#: Tirage des materiaux de tuile. Majorite d'ivoire (« Pale » Leviathan),
#: ponctue d'anthracite et de violet.
PLATE_MATS = (
    "AA_Trim", "AA_Trim", "AA_Trim", "AA_Hull",
    "AA_Trim", "AA_Panel", "AA_Hull", "AA_Trim",
)

#: Les quatre plaques d'armure : azimut du centre, demi-ouverture angulaire.
#: Espacement volontairement irregulier (charte SS4 : le Choeur Nul est
#: asymetrique) — mais toutes dans l'arc du croissant, sinon elles pendraient
#: dans le vide une fois celui-ci bascule.
PLATES: tuple[tuple[float, float], ...] = (
    (-112.0, 25.0), (-46.0, 27.0), (18.0, 24.0), (76.0, 22.0),
)
PLATE_R = (3.10, 3.74)    # (charniere tangentielle, bord externe)
PLATE_Z = (1.12, 1.40, 1.18)   # (charniere, crete, bord externe)
PLATE_T = 0.13
PLATE_SEG = 8

# ==========================================================================
# Les quatre bras-epines
# ==========================================================================
#
# Courbes de Bezier quadratiques (racine, controle, pointe). Aucune paire n'est
# le miroir d'une autre : longueurs, epaisseurs, nombres de vertebres et
# courbures different. Les pointes de `Spike_01` et `Spike_03` fixent a elles
# seules les 11,0 m imposes — l'enveloppe est equilibree, la silhouette ne l'est
# pas.
#
# ⚠️ Les racines sont a z ~ 1,10 et a r >= 4,25 : c'est un mat dorsal qui les
# tient, au-dessus du pont et EN DEHORS de la piste de la coquille. Sans cette
# double condition, le pointage de +/-40 deg enterrerait l'epine dans les lobes
# avant et arriere des le premier degre, et sa rotule se ferait raboter par une
# plaque a chaque tour d'orbite (les deux ont ete mesures).

SPIKES: tuple[dict, ...] = (
    {   # babord-arriere : la plus longue, l'aiguille. Elle porte le +X.
        "name": "Spike_01",
        "root": (4.24, 0.42, 1.12),
        "ctrl": (5.10, 2.25, 1.16),
        "tip": (HALF_W, 4.62, 0.92),
        "r0": 0.385, "sides": 9, "vertebrae": 7, "flat": 0.62, "taper": 1.26,
        "splits": (0.32, 0.64), "port": 0.46,
    },
    {   # tribord-arriere : le bras lourd, trapu, tres segmente
        "name": "Spike_02",
        "root": (-4.02, 1.72, 1.10),
        "ctrl": (-5.05, 3.05, 1.14),
        "tip": (-5.02, 5.26, 0.88),
        "r0": 0.425, "sides": 9, "vertebrae": 6, "flat": 0.66, "taper": 1.10,
        "splits": (0.34, 0.66), "port": 0.50,
    },
    {   # tribord-avant : la faux. Elle porte le -X.
        "name": "Spike_03",
        "root": (-4.14, -1.28, 1.12),
        "ctrl": (-5.25, -2.70, 1.14),
        "tip": (-HALF_W, -4.48, 0.90),
        "r0": 0.400, "sides": 9, "vertebrae": 6, "flat": 0.60, "taper": 1.20,
        "splits": (0.33, 0.65), "port": 0.44,
    },
    {   # babord-avant : la plus courte, la « pince »
        "name": "Spike_04",
        "root": (3.62, -2.62, 1.10),
        "ctrl": (4.62, -4.05, 1.12),
        "tip": (4.72, -5.34, 0.88),
        "r0": 0.355, "sides": 9, "vertebrae": 5, "flat": 0.64, "taper": 1.16,
        "splits": (0.35, 0.67), "port": 0.48,
    },
)

SPIKE_SAMPLES = 4         # stations par vertebre
SPIKE_TIP_R = 0.016
SPIKE_FLARE = 0.18        # relief de vertebre (l'ecaille recouvre la suivante)
SPIKE_GAP = 0.35          # retrait d'un troncon a son articulation, en rayons

# ==========================================================================
# Ponts d'armes fixes de la coque (conserves : le controleur generique les lit
# encore si `external_attacks` retombe a faux)
# ==========================================================================

#: ⚠️ Ils sont poses SUR LE BEC, a r >= 5,1 : c'est l'invariant de piste
#: (`SHELL_TRACK`). La premiere version les avait mis a r = 3,5, ou la coquille
#: passe — et la mesure a trouve 500 triangles en interpenetration.
MUZZLE_C = (0.0, -6.05, 0.40)
MUZZLE_LR = (1.15, -5.55, 0.40)   # (|x|, y, z) — `attach_pair` pose les signes


# ==========================================================================
# Interpolation et geometrie de base
# ==========================================================================


def lerp_table(table, x: float) -> float:
    """Interpolation lineaire d'une table (abscisse, valeur), extremites clampees.

    Lineaire par morceaux, volontairement : une spline arrondirait les cassures
    de plaque qui font justement la silhouette hard-surface.
    """
    if x <= table[0][0]:
        return table[0][1]
    if x >= table[-1][0]:
        return table[-1][1]
    for i in range(len(table) - 1):
        x0, v0 = table[i]
        x1, v1 = table[i + 1]
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0)
            return v0 + (v1 - v0) * t
    return table[-1][1]


def body_radius(deg: float) -> float:
    """Rayon du contour de coque a l'azimut `deg` (periodique)."""
    return lerp_table(BODY_R, deg % 360.0)


def disc_z(table: tuple, r: float) -> float:
    """z du pont a un rayon ABSOLU, dans la zone du disque (r <= DISC_R[-1])."""
    return lerp_table(list(zip(DISC_R, table)), r)


def skirt_z(f: float, z0: float) -> float:
    """z de la jupe a la fraction `f` de la corde restante, depuis `z0`."""
    sign = 1.0 if z0 > 0.0 else -1.0
    edge = sign * RIM_HALF
    return edge + (z0 - edge) * (1.0 - f) ** SKIRT_POW


def track_ceiling(r: float) -> float:
    """Plafond impose a la coque sous la piste de la coquille (`SHELL_TRACK`)."""
    for r0, r1, z in SHELL_TRACK:
        if r0 <= r <= r1:
            return z
    return 9.0


def shaft_radius(z: float) -> float:
    """Rayon INTERIEUR du puits a l'altitude `z` (table lue de haut en bas)."""
    return lerp_table([(-zz, rr) for zz, rr in reversed(SHAFT)], -z)


def ring_radius(index: int) -> float:
    """Rayon externe d'un anneau, DERIVE de la paroi au plus etroit de sa course.

    L'anneau a une epaisseur : c'est son arete BASSE qui frole la paroi, puisque
    le puits se resserre en descendant. Prendre le rayon a l'altitude du milieu
    aurait donne 5 cm de trop, et la mesure l'a effectivement refuse.
    """
    z = RINGS[index][0]
    return shaft_radius(z - RING_T * 0.5) - RING_CLEAR


def hull_top(r: float, deg: float) -> float:
    """Altitude du pont a (rayon, azimut). Sert a poser tout detail EN FRACTION."""
    if r <= DISC_R[-1]:
        return disc_z(DISC_TOP, r)
    span = max(body_radius(deg) - DISC_R[-1], 1e-3)
    return skirt_z(min((r - DISC_R[-1]) / span, 1.0), DISC_TOP[-1])


def _verts_of(faces: list) -> list:
    verts = {v for f in faces if f is not None and f.is_valid for v in f.verts}
    return list(verts)


def oriented_box(bm, center, size, rot, material: str) -> list:
    """Boite orientee : `ak.add_box` ne sait faire qu'aligne sur les axes."""
    faces = ak.add_box(bm, (0.0, 0.0, 0.0), size, material)
    verts = _verts_of(faces)
    if rot is not None:
        bmesh.ops.rotate(bm, cent=(0.0, 0.0, 0.0), matrix=rot, verts=verts)
    bmesh.ops.translate(bm, vec=Vector(center), verts=verts)
    return faces


def _align_y(direction: Vector) -> Matrix:
    """Rotation qui amene l'axe local +Y d'une boite sur `direction`."""
    return Vector((0.0, 1.0, 0.0)).rotation_difference(
        direction.normalized()
    ).to_matrix()


def seg_box(bm, a, b, half_w: float, half_h: float, material: str) -> list:
    """Vertebre : boite tendue du point `a` au point `b`."""
    va, vb = Vector(a), Vector(b)
    delta = vb - va
    length = delta.length
    if length < 1e-6:
        return []
    return oriented_box(
        bm, (va + vb) * 0.5, (2.0 * half_w, length, 2.0 * half_h),
        _align_y(delta), material,
    )


def knuckle(bm, center, radius: float, material: str) -> list:
    """Articulation : icosphere subdivisee une fois (80 faces, angles < 30 deg,
    donc epargnee par le biseau — c'est ce qui la rend abordable).

    Une sphere centree sur un pivot est INVARIANTE par rotation autour de ce
    pivot : c'est elle qui autorise une articulation franche sans que le
    troncon rabote son voisin.
    """
    res = bmesh.ops.create_icosphere(
        bm, subdivisions=1, radius=radius,
        matrix=Matrix.Translation(Vector(center)),
    )
    verts = res["verts"]
    idx = ak.mat_index(material)
    faces = []
    for face in {f for v in verts for f in v.link_faces}:
        if all(v in verts for v in face.verts):
            face.material_index = idx
            faces.append(face)
    return faces


def polar_ring(bm, radius: float, z: float, segments: int, phase: float = 0.0):
    """Boucle horizontale (autour de Z) : la primitive du disque et du puits."""
    return ak.add_ring(
        bm,
        [
            (radius * math.cos(2.0 * math.pi * i / segments + phase),
             radius * math.sin(2.0 * math.pi * i / segments + phase),
             z)
            for i in range(segments)
        ],
    )


def slab(bm, lo, hi, mat_top: str, mat_side: str = "AA_Hull",
         mat_bot: str = "AA_Greeble"):
    """Tuile blindee : deux quads (dessous/dessus) relies par 4 flancs.

    Contrairement a `ak.add_box`, elle n'est pas alignee sur les axes : c'est ce
    qui permet de poser des ecailles sur une surface courbe. Retourne
    `(face du dessus, les 4 flancs)` ; `sides[0]` est le **bord d'attaque**, la
    contremarche qui depasse quand la tuile monte sur sa voisine — c'est elle
    qu'on rend emissive pour obtenir les interstices lumineux de la planche.
    """
    ring_lo = ak.add_ring(bm, lo)
    ring_hi = ak.add_ring(bm, hi)
    sides = ak.bridge_rings(bm, ring_lo, ring_hi, mat_side)
    top = ak.cap_ring(bm, ring_hi, mat_top)
    ak.cap_ring(bm, list(reversed(ring_lo)), mat_bot)
    return top, sides


def tangential_tile(bm, rng, a0: float, a1: float, r_in: float, r_out: float,
                    z_in: float, z_out: float, z_base: float, rise: float):
    """Une ecaille tangentielle : longue le long de l'anneau, courte en radial.

    Des plaques RADIALES pleine largeur donnaient, vues de dessus, une roue a
    rayons — un tournesol, tout sauf une carapace. Des tuiles tangentielles qui
    se recouvrent donnent la lecture « ecailles » des planches.
    """
    lo, hi = [], []
    for a, lift in ((a0, 0.0), (a1, rise)):
        for r, z in ((r_in, z_in), (r_out, z_out)):
            x, y = r * math.cos(a), r * math.sin(a)
            lo.append((x, y, z_base))
            hi.append((x, y, z + lift))
    lo = [lo[0], lo[1], lo[3], lo[2]]
    hi = [hi[0], hi[1], hi[3], hi[2]]
    mat = PLATE_MATS[rng.randrange(len(PLATE_MATS))]
    top, sides = slab(bm, lo, hi, mat, mat_side="AA_Greeble")
    # Une contremarche emissive sur quatre, pas une sur deux : a une sur deux,
    # le magenta se lit comme des confettis semes sur la carapace au lieu d'un
    # reseau de coutures — et il vole la vedette au noyau, qui est LA cible
    # (spec pilier B). Verifie au rendu, pas au chiffre.
    if rng.random() < 0.26:
        ak.set_material([sides[0]], "AA_Emissive_Engine")
    if top is not None and rng.random() < 0.42:
        ak.inset_panel(bm, [top], "AA_Panel", thickness=0.040, depth=-0.026)


def _bezier(p0, p1, p2, t: float) -> Vector:
    u = 1.0 - t
    return Vector(
        (u * u * p0[k] + 2.0 * u * t * p1[k] + t * t * p2[k] for k in range(3))
    )


def _bezier_tangent(p0, p1, p2, t: float) -> Vector:
    u = 1.0 - t
    return Vector(
        (2.0 * u * (p1[k] - p0[k]) + 2.0 * t * (p2[k] - p1[k]) for k in range(3))
    )


def _frame(tangent: Vector) -> tuple[Vector, Vector]:
    """Repere transverse (droite, haut) d'une section perpendiculaire."""
    t = tangent.normalized()
    right = t.cross(Vector((0.0, 0.0, 1.0)))
    if right.length < 1e-5:
        right = Vector((1.0, 0.0, 0.0))
    right.normalize()
    up = right.cross(t).normalized()
    return right, up


# ==========================================================================
# Corps
# ==========================================================================


def build_body() -> object:
    """Le pont blinde : disque perce, puits, ventre, mats d'epines, ponts d'armes."""
    bm = bmesh.new()
    thetas = [2.0 * math.pi * j / N_SEG for j in range(N_SEG)]
    degs = [360.0 * j / N_SEG for j in range(N_SEG)]

    def station(k: int, deg: float) -> tuple[float, float, float]:
        """(rayon, z dessus, z dessous) de la station `k` a l'azimut `deg`."""
        if k < len(DISC_R):
            return DISC_R[k], DISC_TOP[k], DISC_BOT[k]
        f = SKIRT_F[k - len(DISC_R)]
        span = body_radius(deg) - DISC_R[-1]
        return (DISC_R[-1] + span * f,
                skirt_z(f, DISC_TOP[-1]), skirt_z(f, DISC_BOT[-1]))

    n_st = len(DISC_R) + len(SKIRT_F)
    top_rings, bot_rings = [], []
    for k in range(n_st):
        top_rings.append(ak.add_ring(bm, [
            (station(k, d)[0] * math.cos(t), station(k, d)[0] * math.sin(t),
             station(k, d)[1])
            for t, d in zip(thetas, degs)
        ]))
        bot_rings.append(ak.add_ring(bm, [
            (station(k, d)[0] * math.cos(t), station(k, d)[0] * math.sin(t),
             station(k, d)[2])
            for t, d in zip(thetas, degs)
        ]))

    # --- les deux nappes ---------------------------------------------------
    # Fond anthracite tres sombre : ce sont les joints entre plaques. Les
    # plaques elles-memes seront extrudees par-dessus (`inset_panel`).
    top_bands = [ak.bridge_rings(bm, top_rings[k], top_rings[k + 1], "AA_Greeble")
                 for k in range(n_st - 1)]
    bot_bands = [ak.bridge_rings(bm, bot_rings[k + 1], bot_rings[k], "AA_Greeble")
                 for k in range(n_st - 1)]
    ak.bridge_rings(bm, top_rings[-1], bot_rings[-1], "AA_Trim")   # la tranche

    # --- le puits, et le coeur au fond -------------------------------------
    well = [top_rings[0]] + [polar_ring(bm, r, z, N_SEG) for z, r in SHAFT[1:]]
    for i in range(len(well) - 1):
        ak.bridge_rings(bm, well[i + 1], well[i], SHAFT_MATS[i])
    floor = bm.verts.new((0.0, 0.0, SHAFT[-1][0] - 0.04))
    ak.fan_to_point(bm, well[-1], floor, "AA_Greeble")

    # --- le ventre ---------------------------------------------------------
    belly = [bot_rings[0]] + [polar_ring(bm, r, z, N_SEG) for z, r in BELLY[1:]]
    for i in range(len(belly) - 1):
        ak.bridge_rings(bm, belly[i], belly[i + 1], "AA_Hull" if i % 2 else "AA_Panel")
    keel = bm.verts.new((0.0, 0.0, BELLY[-1][0] - 0.03))
    ak.fan_to_point(bm, list(reversed(belly[-1])), keel, "AA_Greeble")

    # --- plaques de pont : couronne, gorge, jupe ---------------------------
    def pick(bands, ks, cols):
        out = []
        for k in ks:
            for j in cols:
                face = bands[k][j % N_SEG]
                if face is not None and face.is_valid:
                    out.append(face)
        return out

    rng = random.Random(SEED + 11)
    for s in range(8):
        cols = range(5 * s, 5 * s + 4)
        ak.inset_panel(bm, pick(top_bands, (5, 6), cols),
                       "AA_Trim" if s % 3 else "AA_Panel",
                       thickness=0.030, depth=0.016)
    for s in range(10):
        cols = range(4 * s, 4 * s + 3)
        ak.inset_panel(bm, pick(top_bands, (8, 9), cols),
                       "AA_Trim" if s % 2 else "AA_Hull",
                       thickness=0.040, depth=0.014)
    for s in range(5):
        cols = range(8 * s + 1, 8 * s + 6)
        ak.inset_panel(bm, pick(bot_bands, (7, 8), cols), "AA_Panel",
                       thickness=0.045, depth=0.012)
    # marquage vert maladif (usage tres limite, charte SS3), a un seul endroit
    ak.inset_panel(bm, pick(top_bands, (6,), range(22, 24)), "AA_Marking_Red",
                   thickness=0.030, depth=0.008)

    # --- veines magenta dans les interstices de la jupe --------------------
    # Fines et confinees : tracees larges et jusqu'au bord, elles voleraient la
    # vedette au noyau — or c'est lui, et lui seul, que le joueur doit voir en
    # premier (spec pilier B).
    for j in (2, 11, 19, 27, 34):
        deg = degs[j]
        a = thetas[j]
        pts = []
        for f in (0.10, 0.34, 0.58, 0.80):
            r = DISC_R[-1] + (body_radius(deg) - DISC_R[-1]) * f
            pts.append(Vector((r * math.cos(a), r * math.sin(a),
                               hull_top(r, deg) + 0.012)))
        for i in range(len(pts) - 1):
            seg_box(bm, pts[i], pts[i + 1], 0.020, 0.011, "AA_Emissive_Engine")

    _build_rim_teeth(bm)
    _build_crest(bm)
    _build_scales(bm)
    _build_masts(bm)
    _build_gun_decks(bm)
    _build_membranes(bm)

    ak.greeble_strip(
        bm, (0.55, 4.10, hull_top(4.15, 82.0)), (-0.35, 5.40, hull_top(5.45, 96.0)),
        count=7, seed=SEED + 21, size_range=(0.070, 0.150),
        height_range=(0.040, 0.090),
    )
    ak.greeble_strip(
        bm, (1.30, -4.30, hull_top(4.50, 287.0)), (0.40, -5.60, hull_top(5.62, 274.0)),
        count=6, seed=SEED + 22, size_range=(0.060, 0.130),
        height_range=(0.035, 0.080),
    )
    return ak.new_object("Body", bm)


def _build_rim_teeth(bm) -> None:
    """Denture fixe de la levre du puits (l'ARMOR RING de la planche).

    ⚠️ Elle mord vers l'INTERIEUR et reste sous z = 0,62 : la levre mobile passe
    au-dessus a 0,72, et le noyau — donc la levre, qui en est l'enfant — tourne.
    Une dent qui depasserait raboterait la levre a chaque tour.
    """
    rng = random.Random(SEED + 31)
    for i in range(18):
        a = 2.0 * math.pi * (i + 0.5) / 18.0
        d = Vector((math.cos(a), math.sin(a), 0.0))
        base = d * 2.02 + Vector((0.0, 0.0, 0.52))
        tip = d * (1.86 + rng.uniform(-0.04, 0.04)) + Vector((0.0, 0.0, 0.58))
        seg_box(bm, base, tip, 0.105, 0.070, "AA_Trim")
        if i % 3 == 0:
            seg_box(bm, d * 2.06 + Vector((0.0, 0.0, 0.60)),
                    d * 1.94 + Vector((0.0, 0.0, 0.62)),
                    0.030, 0.014, "AA_Emissive_Engine")


def _build_crest(bm) -> None:
    """Bec avant et dard arriere : les deux cretes qui portent les 14 m.

    Elles sont posees EN FRACTION de la corde (`hull_top`) : le jour ou le
    contour bouge, elles suivent au lieu de flotter au-dessus du vide.
    """
    for deg, spread, count, mat in ((270.0, 7.0, 6, "AA_Trim"),
                                    (90.0, 5.5, 5, "AA_Trim")):
        a = math.radians(deg)
        d = Vector((math.cos(a), math.sin(a), 0.0))
        side = Vector((-math.sin(a), math.cos(a), 0.0))
        span = body_radius(deg) - DISC_R[-1]
        for k in range(count):
            f0 = 0.12 + 0.86 * k / count
            f1 = 0.12 + 0.86 * (k + 1.25) / count
            r0 = DISC_R[-1] + span * f0
            r1 = DISC_R[-1] + span * min(f1, 1.0)
            w0 = spread * 0.10 * (1.0 - f0) + 0.10
            w1 = spread * 0.10 * (1.0 - f1) + 0.07
            z0 = hull_top(r0, deg)
            z1 = hull_top(r1, deg)
            lo = [tuple(d * r0 + side * w0 + Vector((0.0, 0.0, z0 - 0.10))),
                  tuple(d * r0 - side * w0 + Vector((0.0, 0.0, z0 - 0.10))),
                  tuple(d * r1 - side * w1 + Vector((0.0, 0.0, z1 - 0.10))),
                  tuple(d * r1 + side * w1 + Vector((0.0, 0.0, z1 - 0.10)))]
            hi = [tuple(d * r0 + side * w0 + Vector((0.0, 0.0, z0 + 0.11))),
                  tuple(d * r0 - side * w0 + Vector((0.0, 0.0, z0 + 0.11))),
                  tuple(d * r1 - side * w1 + Vector((0.0, 0.0, z1 + 0.07))),
                  tuple(d * r1 + side * w1 + Vector((0.0, 0.0, z1 + 0.07)))]
            top, sides = slab(bm, lo, hi, mat, mat_side="AA_Panel")
            if k % 2 == 0:
                ak.set_material([sides[0]], "AA_Emissive_Engine")


def _build_scales(bm) -> None:
    """Ecailles dorsales sur la jupe : elles se recouvrent, comme la planche.

    Leur largeur derive du contour a leur azimut, jamais d'une coordonnee
    absolue : une ecaille ne peut donc pas se retrouver a flotter a cote de la
    coque quand le contour change.
    """
    rng = random.Random(SEED + 41)
    for deg0, deg1, count in ((18.0, 74.0, 5), (104.0, 156.0, 5),
                              (196.0, 250.0, 5), (292.0, 344.0, 5)):
        for k in range(count):
            a0 = math.radians(deg0 + (deg1 - deg0) * k / count)
            a1 = math.radians(deg0 + (deg1 - deg0) * (k + 0.86) / count)
            d0, d1 = math.degrees(a0), math.degrees(a1)
            f0 = rng.uniform(0.10, 0.24)
            f1 = f0 + rng.uniform(0.34, 0.52)
            span0 = body_radius(d0) - DISC_R[-1]
            span1 = body_radius(d1) - DISC_R[-1]
            r_in = DISC_R[-1] + span0 * f0
            r_out = DISC_R[-1] + span1 * f1
            z_in = hull_top(r_in, d0)
            z_out = hull_top(r_out, d1)
            lo = [(r_in * math.cos(a0), r_in * math.sin(a0), z_in - 0.14),
                  (r_out * math.cos(a0), r_out * math.sin(a0), z_out - 0.14),
                  (r_out * math.cos(a1), r_out * math.sin(a1), z_out - 0.14),
                  (r_in * math.cos(a1), r_in * math.sin(a1), z_in - 0.14)]
            hi = [(r_in * math.cos(a0), r_in * math.sin(a0), z_in + 0.075),
                  (r_out * math.cos(a0), r_out * math.sin(a0), z_out + 0.030),
                  (r_out * math.cos(a1), r_out * math.sin(a1), z_out + 0.030),
                  (r_in * math.cos(a1), r_in * math.sin(a1), z_in + 0.075)]
            mat = PLATE_MATS[rng.randrange(len(PLATE_MATS))]
            top, sides = slab(bm, lo, hi, mat, mat_side="AA_Panel")
            if rng.random() < 0.24:
                ak.set_material([sides[0]], "AA_Emissive_Engine")
            if top is not None and rng.random() < 0.5:
                ak.inset_panel(bm, [top], "AA_Greeble",
                               thickness=0.050, depth=-0.024)


def _build_masts(bm) -> None:
    """Mats dorsaux des epines : le socle qui porte la rotule d'epaule.

    ⚠️ Le mat est VERTICAL et son axe passe sous le pivot. Ce n'est pas un choix
    de style : un longeron oblique de meme section deborde vers l'axe et vient
    croiser la piste des plaques (mesure), et sa matiere pres de la rotule se
    fait raboter par l'epine des le premier degre de pointage. Vertical, ce qui
    subsiste pres du pivot est un pion centre sur l'axe de rotation.
    """
    for spec in SPIKES:
        root = Vector(spec["root"])
        deg = math.degrees(math.atan2(root.y, root.x))
        r = math.hypot(root.x, root.y)
        d = Vector((math.cos(math.radians(deg)), math.sin(math.radians(deg)), 0.0))
        r_post = r - 0.08
        deck = hull_top(r_post, deg)
        post = d * r_post
        seg_box(bm, tuple(post + Vector((0.0, 0.0, deck - 0.22))),
                tuple(post + Vector((0.0, 0.0, root.z - 0.36))),
                spec["r0"] * 1.05, spec["r0"] * 1.05, "AA_Panel")
        # Le pion final est CENTRE SUR L'AXE DE ROTATION et plus mince que
        # l'epine : il vit a l'interieur d'elle et n'en sort jamais, quel que
        # soit le pointage. C'est le seul moyen de combler le joint sans que le
        # mat se fasse raboter (le corps du mat, lui, s'arrete 36 cm plus bas).
        seg_box(bm, tuple(Vector((root.x, root.y, root.z - 0.32))),
                tuple(Vector((root.x, root.y, root.z))),
                spec["r0"] * 0.34, spec["r0"] * 0.34, "AA_Greeble")
        # embase : large, mais ecrasee sous le plafond de piste
        base_z = min(deck + 0.10, track_ceiling(r_post - 0.42) - 0.02)
        oriented_box(bm, tuple(post + Vector((0.0, 0.0, base_z - 0.16))),
                     (0.96, 0.86, 0.32),
                     Matrix.Rotation(math.radians(deg) + math.pi / 2.0, 3, "Z"),
                     "AA_Greeble")
        seg_box(bm, tuple(post + d * spec["r0"] * 1.05
                          + Vector((0.0, 0.0, deck - 0.10))),
                tuple(post + d * spec["r0"] * 1.05
                      + Vector((0.0, 0.0, root.z - 0.14))),
                0.034, 0.018, "AA_Emissive_Engine")
        # nodule vert maladif au pied du mat : le « bourgeon » d'ou sort le bras
        ak.add_box(bm, tuple(post + d * 0.52 + Vector((0.0, 0.0, deck - 0.02))),
                   (0.19, 0.19, 0.13), "AA_Marking_Red")


def _build_gun_decks(bm) -> None:
    """Les trois ponts d'armes fixes de la proue (Muzzle_C / _L / _R).

    Ils sont conserves parce que le controleur generique les lit encore si
    `external_attacks` retombe a faux : sans eux, un boss non arme par son
    module tirerait depuis son centre geometrique.
    """
    for x, y, z, scale in ((0.0, MUZZLE_C[1], MUZZLE_C[2], 1.0),
                           (MUZZLE_LR[0], MUZZLE_LR[1], MUZZLE_LR[2], 0.82),
                           (-MUZZLE_LR[0], MUZZLE_LR[1], MUZZLE_LR[2], 0.82)):
        # `add_lathe` autour de Y : la premiere coordonnee du contour EST le y
        # absolu, on l'exprime donc par rapport a la bouche.
        ak.add_lathe(
            bm,
            [(y + 0.86, 0.000, "AA_Greeble"),
             (y + 0.74, 0.44 * scale, "AA_Panel"),
             (y + 0.46, 0.46 * scale, "AA_Hull"),
             (y + 0.34, 0.36 * scale, "AA_Trim"),
             (y + 0.14, 0.30 * scale, "AA_Greeble"),
             (y + 0.05, 0.22 * scale, "AA_Emissive_Engine"),
             (y, 0.000, "AA_Emissive_Engine")],
            12, center_x=x, center_z=z, axis="Y",
        )
        ak.add_box(bm, (x, y + 1.05, z - 0.14), (0.94 * scale, 0.80, 0.26),
                   "AA_Greeble")


def _build_membranes(bm) -> None:
    """Membranes sombres (AA_Glass) : les « yeux » morts de la proue.

    Trois, de tailles differentes, deliberement non appairees, posees en
    fraction de corde sur la jupe avant.
    """
    for deg, f, hw, hl in ((248.0, 0.42, 0.30, 0.46),
                           (292.0, 0.30, 0.22, 0.34),
                           (306.0, 0.55, 0.16, 0.26)):
        a = math.radians(deg)
        r = DISC_R[-1] + (body_radius(deg) - DISC_R[-1]) * f
        z = hull_top(r, deg)
        ak.add_box(bm, (r * math.cos(a), r * math.sin(a), z + 0.02),
                   (hw * 2.0, hl * 2.0, 0.12), "AA_Glass")


# ==========================================================================
# Noyau, levre, noeuds, anneaux, coeur
# ==========================================================================


def build_core() -> ak.MovingPart:
    """Noyau : ellipsoide magenta emissive, sillonnee de craquelures.

    La croute (plaques violettes en relief) est *soulevee* facette par facette :
    ce qui reste au niveau de la surface — les interstices et les parois
    d'inset — est emissif. La lumiere sort donc *d'entre* les plaques, comme sur
    le panneau CLOSED CORE. Le tirage est seede : rejouer donne le meme noyau.
    """
    bm = bmesh.new()
    contour = []
    for i in range(CORE_RINGS + 1):
        t = math.pi * i / CORE_RINGS
        contour.append((CORE_Z - CORE_RZ * math.cos(t),
                        CORE_RXY * math.sin(t), "AA_Emissive_Engine"))
    bands = ak.add_lathe(bm, contour, CORE_SEG, axis="Z")

    faces = [f for band in bands for f in band if f is not None and f.is_valid]
    rng = random.Random(SEED + 101)
    for face in faces:
        if rng.random() >= CORE_CRUST_P:
            continue  # facette laissee nue : c'est une craquelure lumineuse
        mat = "AA_Panel" if rng.random() < 0.78 else "AA_Hull"
        ak.inset_panel(bm, [face], mat, thickness=CORE_CRUST_INSET,
                       depth=CORE_CRUST_LIFT * rng.uniform(0.7, 1.25))
    return ak.moving_part("Core", bm, (0.0, 0.0, CORE_Z))


def build_heart() -> ak.MovingPart:
    """Le coeur, au fond du puits : la derniere cible du jeu.

    Statique au contrat — rien ne l'anime — mais noeud a part et enfant de
    `Core`, comme l'exige le contrat de noms. `ak.moving_part()` est la seule
    primitive du kit qui sache poser un parent.
    """
    bm = bmesh.new()
    knuckle(bm, (0.0, 0.0, HEART_Z), HEART_R, "AA_Emissive_Engine")
    knuckle(bm, (0.0, 0.0, HEART_Z), HEART_R * 1.34, "AA_Glass")
    for i in range(6):
        a = 2.0 * math.pi * i / 6.0
        d = Vector((math.cos(a), math.sin(a), 0.0))
        seg_box(bm, tuple(d * HEART_R * 1.2 + Vector((0.0, 0.0, HEART_Z))),
                tuple(d * (HEART_R * 1.2 + 0.16) + Vector((0.0, 0.0, HEART_Z - 0.06))),
                0.030, 0.024, "AA_Trim")
    return ak.moving_part("Heart", bm, (0.0, 0.0, HEART_Z), parent="Core")


def build_maw_lip() -> ak.MovingPart:
    """La levre mobile de la gueule (OUTER RIM sur la planche).

    Sa charniere est posee DERRIERE l'ouverture, et toute sa matiere est en
    avant d'elle : a +90 deg (Godot `rotation.x`) chaque point monte, aucun ne
    plonge, et la piece entiere se retrouve **hors du puits** — le tunnel est
    alors degage en vue de dessus, ce que le rendu de recette verifie.
    """
    bm = bmesh.new()
    angles = [math.radians(LIP_A + (LIP_B - LIP_A) * i / LIP_SEG)
              for i in range(LIP_SEG + 1)]

    tops, bots = [], []
    for r, z in LIP_PROFILE:
        tops.append(ak.add_ring(bm, [(r * math.cos(a), r * math.sin(a), z)
                                     for a in angles]))
        bots.append(ak.add_ring(bm, [(r * math.cos(a), r * math.sin(a), z - LIP_T)
                                     for a in angles]))
    for i in range(len(LIP_PROFILE) - 1):
        band = ak.bridge_rings(bm, tops[i], tops[i + 1], "AA_Trim", closed=False)
        ak.bridge_rings(bm, bots[i + 1], bots[i], "AA_Greeble", closed=False)
        if i == 1:
            ak.inset_panel(bm, band[2:-2], "AA_Panel", thickness=0.050, depth=-0.030)
    for k in (0, -1):
        ak.bridge_rings(bm, bots[k], tops[k], "AA_Panel", closed=False)
    # tranches laterales du secteur
    for j, mat in ((0, "AA_Greeble"), (LIP_SEG, "AA_Greeble")):
        ring = [tops[i][j] for i in range(len(tops))]
        ring += [bots[i][j] for i in reversed(range(len(bots)))]
        ak.cap_ring(bm, ring if j else list(reversed(ring)), mat)

    # --- griffes du surplomb ------------------------------------------------
    for deg in LIP_FANGS:
        a = math.radians(deg)
        d = Vector((math.cos(a), math.sin(a), 0.0))
        seg_box(bm, tuple(d * LIP_FANG_R[0] + Vector((0.0, 0.0, LIP_FANG_Z[0]))),
                tuple(d * LIP_FANG_R[1] + Vector((0.0, 0.0, LIP_FANG_Z[1]))),
                0.085, 0.055, "AA_Trim")
    # couture magenta le long de la crete
    for i in range(LIP_SEG):
        a0, a1 = angles[i], angles[i + 1]
        r = 1.74
        seg_box(bm, (r * math.cos(a0), r * math.sin(a0), 1.035),
                (r * math.cos(a1), r * math.sin(a1), 1.035),
                0.026, 0.014, "AA_Emissive_Engine")
    return ak.moving_part("Maw_Lip", bm, LIP_PIVOT, parent="Core")


def node_base(index: int) -> Vector:
    a = math.radians(NODE_AZ[index])
    return Vector((NODE_R * math.cos(a), NODE_R * math.sin(a), NODE_Z))


def build_node(index: int) -> ak.MovingPart:
    """Un noeud gravitique : fer de lance sur embase articulee.

    Il est plante sur la crete de la levre, penche vers l'exterieur. Sa
    retraction (-60 deg) le rabat vers l'avant, au-dessus de la gueule, ou il
    n'y a que du vide : c'est la seule direction qui degage.
    """
    bm = bmesh.new()
    base = node_base(index)
    a = math.radians(NODE_AZ[index])
    out = Vector((math.cos(a), math.sin(a), 0.0))
    tilt = math.radians(NODE_TILT)
    axis = (out * math.cos(tilt) + Vector((0.0, 0.0, 1.0)) * math.sin(tilt)).normalized()
    side = Vector((-math.sin(a), math.cos(a), 0.0))
    up = side.cross(axis).normalized()
    length = NODE_LEN[index]

    knuckle(bm, tuple(base), NODE_W * 0.95, "AA_Greeble")
    sections = ((0.10, 1.00), (0.34, 0.86), (0.62, 0.58), (0.84, 0.30))
    rings = []
    for s, w in sections:
        c = base + axis * (length * s)
        rings.append(ak.add_ring(bm, [
            tuple(c + side * (NODE_W * w) + up * (NODE_W * w * 0.55)),
            tuple(c - side * (NODE_W * w) + up * (NODE_W * w * 0.55)),
            tuple(c - side * (NODE_W * w * 0.72) - up * (NODE_W * w * 0.62)),
            tuple(c + side * (NODE_W * w * 0.72) - up * (NODE_W * w * 0.62)),
        ]))
    for i in range(len(rings) - 1):
        band = ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Trim")
        ak.set_material([band[2]], "AA_Panel")
        if i == 1:
            ak.set_material([band[1], band[3]], "AA_Emissive_Engine")
    tip = bm.verts.new(tuple(base + axis * length))
    ak.fan_to_point(bm, rings[-1], tip, "AA_Trim")
    ak.cap_ring(bm, list(reversed(rings[0])), "AA_Greeble")
    return ak.moving_part(f"Node_{index + 1:02d}", bm, tuple(base), parent="Maw_Lip")


def build_ring(index: int) -> ak.MovingPart:
    """Un anneau interne du puits, perce de son ouverture (« OFFSET GATE »).

    C'est une bande annulaire incomplete : le joueur, aspire vers le fond, doit
    aligner sa position laterale sur l'ouverture au moment ou il la franchit.
    Le decalage d'un anneau au suivant interdit la descente en ligne droite.
    """
    z, gate, band = RINGS[index]
    r_out = ring_radius(index)
    r_in = r_out - band
    bm = bmesh.new()
    span = 360.0 - RING_GAP
    angles = [math.radians(gate + RING_GAP * 0.5 + span * i / RING_SEG)
              for i in range(RING_SEG + 1)]

    def ring_at(radius: float, dz: float):
        return ak.add_ring(bm, [(radius * math.cos(a), radius * math.sin(a), z + dz)
                                for a in angles])

    out_hi, out_lo = ring_at(r_out, RING_T * 0.5), ring_at(r_out, -RING_T * 0.5)
    in_hi, in_lo = ring_at(r_in, RING_T * 0.5), ring_at(r_in, -RING_T * 0.5)
    ak.bridge_rings(bm, in_hi, out_hi, "AA_Trim", closed=False)
    ak.bridge_rings(bm, out_lo, in_lo, "AA_Greeble", closed=False)
    ak.bridge_rings(bm, out_hi, out_lo, "AA_Panel", closed=False)
    ak.bridge_rings(bm, in_lo, in_hi, "AA_Emissive_Engine", closed=False)
    for j, rev in ((0, True), (RING_SEG, False)):
        ring = [out_hi[j], in_hi[j], in_lo[j], out_lo[j]]
        ak.cap_ring(bm, list(reversed(ring)) if rev else ring, "AA_Emissive_Engine")
    # Nervures : l'anneau lit comme une machine, pas comme un joint torique.
    # ⚠️ Elles saillent vers l'INTERIEUR du puits. Vers l'exterieur, elles
    # mangeaient le jeu radial calcule par `ring_radius()` — et c'est
    # exactement le detail pose « en coordonnee absolue » que le corollaire du
    # Specter-9 interdit.
    for k in range(0, RING_SEG, 4):
        a = angles[k]
        d = Vector((math.cos(a), math.sin(a), 0.0))
        seg_box(bm, tuple(d * (r_in + 0.03) + Vector((0.0, 0.0, z))),
                tuple(d * (r_in - 0.05) + Vector((0.0, 0.0, z))),
                0.040, RING_T * 0.62, "AA_Hull")
    return ak.moving_part(f"Ring_{index + 1:02d}", bm, (0.0, 0.0, z), parent="Core")


# ==========================================================================
# Coquille : anneau porteur, croissant, plaques
# ==========================================================================


def build_shell_ring() -> ak.MovingPart:
    """L'anneau porteur : il ne porte que l'orbite, et rien d'autre.

    Deux rangees de tuiles tangentielles dephasees, posees dans la gorge du
    pont. La nappe emissive sous les tuiles n'est visible que par les fentes :
    la lumiere sort *d'entre* les ecailles, elle n'est pas peinte dessus.
    """
    bm = bmesh.new()
    rng = random.Random(SEED + 201)
    glow_lo = polar_ring(bm, 2.18, RING_Z_BASE + 0.02, 36)
    glow_hi = polar_ring(bm, 2.96, RING_Z_BASE + 0.02, 36)
    ak.bridge_rings(bm, glow_lo, glow_hi, "AA_Emissive_Engine")
    glow_bot_lo = polar_ring(bm, 2.18, RING_Z_BASE - 0.06, 36)
    glow_bot_hi = polar_ring(bm, 2.96, RING_Z_BASE - 0.06, 36)
    ak.bridge_rings(bm, glow_bot_hi, glow_bot_lo, "AA_Greeble")
    ak.bridge_rings(bm, glow_hi, glow_bot_hi, "AA_Greeble")
    ak.bridge_rings(bm, glow_bot_lo, glow_lo, "AA_Greeble")

    for r_in, r_out, z_in, z_out, count, phase in RING_ROWS:
        step = 2.0 * math.pi / count
        for k in range(count):
            a0 = (k + phase) * step
            a1 = a0 + step * RING_OVERLAP
            tangential_tile(
                bm, rng, a0, a1,
                r_in + rng.uniform(-0.02, 0.03), r_out + rng.uniform(-0.05, 0.05),
                z_in + rng.uniform(-0.02, 0.04), z_out + rng.uniform(-0.03, 0.03),
                RING_Z_BASE, 0.030,
            )
    return ak.moving_part("Shell_Ring", bm, SHELL_PIVOT)


def build_crescent() -> ak.MovingPart:
    """Le croissant : l'anneau INCOMPLET de la charte, monte sur l'anneau porteur.

    Sa charniere est tangente a son bord arriere : toute sa matiere est en avant
    d'elle, donc la bascule de fin de phase 1 (0 -> 65 deg) la redresse sans
    qu'un seul point ne plonge vers la coque. Les 130 deg manquants ouvrent sur
    le quadrant avant-tribord — l'anneau est ouvert du cote ou le boss est le
    plus arme.
    """
    bm = bmesh.new()
    rng = random.Random(SEED + 301)
    span = CR_PHI_B - CR_PHI_A

    # nappe emissive continue, sous les tuiles
    a0, a1 = math.radians(CR_PHI_A), math.radians(CR_PHI_B)
    n_glow = 26
    lo_ring, hi_ring = [], []
    for i in range(n_glow + 1):
        a = a0 + (a1 - a0) * i / n_glow
        lo_ring.append((2.24 * math.cos(a), 2.24 * math.sin(a), CR_Z_BASE - 0.03))
        hi_ring.append((3.04 * math.cos(a), 3.04 * math.sin(a), CR_Z_BASE - 0.03))
    lo = ak.add_ring(bm, lo_ring)
    hi = ak.add_ring(bm, hi_ring)
    ak.bridge_rings(bm, lo, hi, "AA_Emissive_Engine", closed=False)
    lo2 = ak.add_ring(bm, [(x, y, z - 0.10) for x, y, z in lo_ring])
    hi2 = ak.add_ring(bm, [(x, y, z - 0.10) for x, y, z in hi_ring])
    ak.bridge_rings(bm, hi2, lo2, "AA_Greeble", closed=False)
    ak.bridge_rings(bm, hi, hi2, "AA_Greeble", closed=False)
    ak.bridge_rings(bm, lo2, lo, "AA_Greeble", closed=False)
    for pair, rev in (((lo[0], hi[0], hi2[0], lo2[0]), True),
                      ((lo[-1], hi[-1], hi2[-1], lo2[-1]), False)):
        ak.cap_ring(bm, list(reversed(pair)) if rev else list(pair), "AA_Greeble")

    for r_in, r_out, count, lift, phase in CR_ROWS:
        step = math.radians(span) / count
        for k in range(-1, count):
            b0 = math.radians(CR_PHI_A) + (k + phase) * step
            b1 = min(b0 + step * CR_OVERLAP, math.radians(CR_PHI_B))
            b0 = max(b0, math.radians(CR_PHI_A))
            if b1 - b0 < step * 0.35:
                continue
            tangential_tile(
                bm, rng, b0, b1,
                r_in + rng.uniform(-0.02, 0.03), r_out + rng.uniform(-0.04, 0.04),
                CR_TOP + lift + rng.uniform(-0.02, 0.02),
                CR_TOP + lift - 0.04 + rng.uniform(-0.02, 0.02),
                CR_Z_BASE, 0.028,
            )

    # cornes : deux pointes qui prolongent les extremites du croissant
    for phi, length in ((CR_PHI_A, -16.0), (CR_PHI_B, 12.0)):
        a = math.radians(phi)
        ring = ak.add_ring(bm, [
            (2.30 * math.cos(a), 2.30 * math.sin(a), CR_Z_BASE + 0.02),
            (3.00 * math.cos(a), 3.00 * math.sin(a), CR_Z_BASE + 0.02),
            (3.00 * math.cos(a), 3.00 * math.sin(a), CR_TOP + 0.02),
            (2.30 * math.cos(a), 2.30 * math.sin(a), CR_TOP + 0.02),
        ])
        b = math.radians(phi + length)
        tip = bm.verts.new((2.66 * math.cos(b), 2.66 * math.sin(b),
                            CR_Z_BASE + 0.08))
        ak.fan_to_point(bm, ring, tip, "AA_Trim")
        ak.cap_ring(bm, list(reversed(ring)), "AA_Greeble")
    return ak.moving_part("Shell_Crescent", bm, CR_PIVOT, parent="Shell_Ring")


def plate_pivot(index: int) -> Vector:
    """Charniere d'une plaque : sur son bord INTERNE, tangente a l'anneau."""
    a = math.radians(PLATES[index][0])
    return Vector((PLATE_R[0] * math.cos(a), PLATE_R[0] * math.sin(a), PLATE_Z[0]))


def build_plate(index: int) -> ak.MovingPart:
    """Une plaque d'armure : ecailles superposees, couture de noyau magenta.

    ⚠️ La charniere est TANGENTIELLE et posee sur le bord INTERNE : a -80 deg
    autour de `UP x radial` (la convention du Choir Harvester pour son iris) la
    plaque se **souleve vers l'exterieur**. Elle ne peut pas tomber vers le bas :
    sous elle il y a la coquille, puis le pont — une chute vers l'interieur
    traverserait les deux. Le geste lit comme une ecaille qu'on arrache, ce que
    montre le panneau CORE EXPOSED.
    """
    center, half = PLATES[index]
    rng = random.Random(SEED + 401 + index)
    bm = bmesh.new()

    def point(f: float, s: float, dz: float) -> tuple[float, float, float]:
        """`f` : 0 a la charniere, 1 au bord externe. `s` : -1..1 en azimut."""
        a = math.radians(center + half * s)
        r = PLATE_R[0] + (PLATE_R[1] - PLATE_R[0]) * f
        z = lerp_table([(0.0, PLATE_Z[0]), (0.55, PLATE_Z[1]), (1.0, PLATE_Z[2])], f)
        # bombement transversal : la plaque est une ecaille, pas une planche
        z += 0.05 * (1.0 - s * s)
        return (r * math.cos(a), r * math.sin(a), z + dz)

    fs = [i / PLATE_SEG for i in range(PLATE_SEG + 1)]
    ss = (-1.0, -0.72, -0.30, 0.30, 0.72, 1.0)
    tops = [ak.add_ring(bm, [point(f, s, 0.0) for s in ss]) for f in fs]
    bots = [ak.add_ring(bm, [point(f, s, -PLATE_T) for s in ss]) for f in fs]
    for i in range(PLATE_SEG):
        band = ak.bridge_rings(bm, tops[i], tops[i + 1], "AA_Trim", closed=False)
        ak.bridge_rings(bm, bots[i + 1], bots[i], "AA_Greeble", closed=False)
        if i in (2, 5) and len(band) > 2:
            ak.inset_panel(bm, [band[1], band[2], band[3]], "AA_Panel",
                           thickness=0.045, depth=-0.028)
        if i % 3 == 1:
            ak.set_material([band[0], band[-1]], "AA_Hull")
    ak.bridge_rings(bm, tops[0], bots[0], "AA_Panel", closed=False)
    ak.bridge_rings(bm, bots[PLATE_SEG], tops[PLATE_SEG], "AA_Trim", closed=False)
    for j, rev in ((0, False), (len(ss) - 1, True)):
        ring = [tops[i][j] for i in range(len(tops))]
        ring += [bots[i][j] for i in reversed(range(len(bots)))]
        ak.cap_ring(bm, list(reversed(ring)) if rev else ring, "AA_Greeble")

    # couture de noyau magenta sur le bord interne (le CORE SEAM de la planche)
    for i in range(0, PLATE_SEG, 2):
        p0 = point(fs[i], -1.0, -PLATE_T * 0.45)
        p1 = point(fs[min(i + 2, PLATE_SEG)], -1.0, -PLATE_T * 0.45)
        seg_box(bm, p0, p1, 0.024, 0.030, "AA_Emissive_Engine")
    # bouche de tir de la plaque
    port = point(0.62, 0.0, 0.04)
    knuckle(bm, port, 0.13, "AA_Emissive_Engine")
    if rng.random() < 0.5:
        knuckle(bm, point(0.30, 0.55, 0.03), 0.09, "AA_Greeble")
    return ak.moving_part(f"Plate_{index + 1:02d}", bm, tuple(plate_pivot(index)),
                          parent="Shell_Crescent")


def plate_muzzle(index: int) -> tuple[float, float, float]:
    center, _ = PLATES[index]
    a = math.radians(center)
    r = PLATE_R[0] + (PLATE_R[1] - PLATE_R[0]) * 0.62
    return (r * math.cos(a), r * math.sin(a), PLATE_Z[1] + 0.14)


# ==========================================================================
# Epines — trois maillons chaines par bras
# ==========================================================================


def spike_radius(spec: dict, t: float) -> float:
    """Rayon a l'abscisse `t` : effilement global + relief de vertebre."""
    base = spec["r0"] * (1.0 - t) ** spec["taper"] + SPIKE_TIP_R
    frac = (t * spec["vertebrae"]) % 1.0
    return base * (1.0 + SPIKE_FLARE * (1.0 - frac) ** 1.6)


def spike_point(spec: dict, t: float) -> Vector:
    return _bezier(spec["root"], spec["ctrl"], spec["tip"], t)


def _spike_section(bm, spec: dict, t: float):
    center = spike_point(spec, t)
    right, up = _frame(_bezier_tangent(spec["root"], spec["ctrl"], spec["tip"], t))
    r = spike_radius(spec, t)
    rx, rz = r, r * spec["flat"]
    pts = []
    for j in range(spec["sides"]):
        a = 2.0 * math.pi * j / spec["sides"]
        pts.append(tuple(center + up * (rz * math.cos(a)) + right * (rx * math.sin(a))))
    return ak.add_ring(bm, pts)


def build_spike_segment(spec: dict, seg: int) -> ak.MovingPart:
    """Un maillon d'epine : sections elliptiques aplaties le long d'une Bezier.

    Le rayon repart en avant a chaque vertebre : chaque segment recouvre le
    suivant comme une ecaille, et l'anneau de jonction — le plus etroit — est
    emissif. C'est la « veine de magenta » de la planche, obtenue par la
    geometrie et non par une texture (ADR-0008).

    Chaque maillon commence par une rotule centree sur SON pivot et laisse un
    jeu (`SPIKE_GAP`) avant sa premiere section : une vertebre qui part du pivot
    balaie un cylindre autour de lui et rabote le maillon precedent des le
    premier degre de flexion.
    """
    t0, t1 = spec["splits"]
    bounds = ((0.0, t0), (t0, t1), (t1, 1.0))[seg]
    pivot = spike_point(spec, bounds[0])
    r_pivot = spike_radius(spec, bounds[0])

    bm = bmesh.new()
    knuckle(bm, tuple(pivot), r_pivot * 0.94, "AA_Greeble")

    length = bounds[1] - bounds[0]
    gap = min(SPIKE_GAP * r_pivot / max(_arc_len(spec), 1e-3), length * 0.30)
    lo = bounds[0] + gap
    hi = bounds[1] - (0.0 if seg == 2 else gap * 0.7)
    n = max(int(round(spec["vertebrae"] * SPIKE_SAMPLES * (hi - lo))), 3)
    rings = [_spike_section(bm, spec, lo + (hi - lo) * i / n) for i in range(n + 1)]

    sides = spec["sides"]
    top_ks = (0, 1, sides - 1)
    side_ks = (2, sides - 2)
    bottom_k = sides // 2
    for i in range(n):
        band = ak.bridge_rings(bm, rings[i], rings[i + 1], "AA_Hull")
        phase = i % SPIKE_SAMPLES
        if phase == SPIKE_SAMPLES - 1:
            ak.set_material(band, "AA_Emissive_Engine")   # jonction de vertebres
            continue
        if phase == 0:
            ak.set_material(band, "AA_Trim")              # collier ivoire
            continue
        ak.set_material([band[k] for k in top_ks], "AA_Trim")
        ak.set_material([band[k] for k in side_ks], "AA_Panel")
        ak.set_material([band[bottom_k]], "AA_Greeble")
    ak.cap_ring(bm, list(reversed(rings[0])), "AA_Greeble")
    if seg == 2:
        tip = bm.verts.new(tuple(Vector(spec["tip"])))
        ak.fan_to_point(bm, rings[-1], tip, "AA_Trim")    # griffe ivoire
    else:
        ak.cap_ring(bm, rings[-1], "AA_Greeble")
        # bouche de tir (le WEAPON PORT de la planche), sur le maillon median
        if seg == 1 and spec["port"] > bounds[0]:
            port = spike_point(spec, spec["port"])
            _, up = _frame(_bezier_tangent(spec["root"], spec["ctrl"],
                                           spec["tip"], spec["port"]))
            knuckle(bm, tuple(port + up * spike_radius(spec, spec["port"]) * 0.55),
                    0.075, "AA_Emissive_Engine")

    name = spec["name"] + ("", "_Mid", "_Tip")[seg]
    parent = None if seg == 0 else spec["name"] + ("", "", "_Mid")[seg]
    return ak.moving_part(name, bm, tuple(pivot), parent=parent)


def _arc_len(spec: dict) -> float:
    """Longueur approchee de la Bezier : sert a convertir un jeu metrique en t."""
    pts = [spike_point(spec, i / 16.0) for i in range(17)]
    return sum((pts[i + 1] - pts[i]).length for i in range(16))


def spike_muzzle(spec: dict) -> tuple[float, float, float]:
    port = spike_point(spec, spec["port"])
    _, up = _frame(_bezier_tangent(spec["root"], spec["ctrl"], spec["tip"],
                                   spec["port"]))
    return tuple(port + up * (spike_radius(spec, spec["port"]) * 0.55 + 0.10))


# ==========================================================================
# Points d'attache
# ==========================================================================


def build_attach_points() -> list:
    """Positions **derivees de la geometrie**, jamais devinees.

    ⚠️ `ak.attach_point()` ne sait pas parenter : ces marqueurs sont des noeuds
    RACINES fixes. Ils donnent un point d'apparition, pas une position suivie —
    une plaque qui bascule n'emmene pas sa bouche avec elle. C'est la meme
    limite que sur le Choir Harvester, et elle est sans consequence tant que le
    combat calcule la direction de tir a part.
    """
    points = [
        ak.attach_point("Core_Center", (0.0, 0.0, CORE_Z)),
        ak.attach_point("Maw_Center", (0.0, 0.0, CORE_Z + CORE_RZ + 0.10)),
        ak.attach_point("Tunnel_End", (0.0, 0.0, HEART_Z + 0.14)),
        ak.attach_point("Muzzle_C", MUZZLE_C),
    ]
    points += list(ak.attach_pair("Muzzle", *MUZZLE_LR))
    for i in range(len(PLATES)):
        points.append(ak.attach_point(f"Muzzle_Plate_{i + 1:02d}", plate_muzzle(i)))
    for spec in SPIKES:
        points.append(
            ak.attach_point(f"Muzzle_{spec['name']}", spike_muzzle(spec))
        )
    return points


# ==========================================================================
# Mesure de degagement — le livrable central de BRIEF-0040
#
# Le contrat d'`export_hull()` ne connait QUE la pose de repos. Une piece qui
# traverse la coque des qu'elle bouge le passe sans un mot : c'est exactement ce
# qui a coute quatre briefs au Specter-9 (un marquage a cheval sur une charniere
# avait fait tomber le debattement d'un volet de 18,5 a 2,8 deg — bounding box
# parfaite, volet dans la coque). On remesure donc a chaque build, sur le
# maillage REELLEMENT livre, en rejouant les rotations que le combat ecrira.
# ==========================================================================

#: Repere d'auteur -> repere Godot : (x, y, z) -> (-x, z, y). Rotation rigide
#: (determinant +1) : un axe se transporte comme un vecteur, un angle est
#: conserve. Toute la mesure se fait DANS LE REPERE GODOT, avec exactement les
#: rotations qu'ecrira le combat — un signe faux valide une piece qui traverse
#: la coque, et personne ne le verrait avant le jeu.
_TO_GODOT = Matrix(((-1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0)))

#: Amplitudes exigees par le gameplay (BRIEF-0040 SS« Debattements »).
ORBIT_STEPS = 12          # echantillons de l'orbite 360 deg de la coquille
CRESCENT_DEG = 65.0
PLATE_DEG = -80.0
LIP_DEG = 90.0
NODE_DEG = -60.0
SPIKE_DEG = 40.0
FLEX_DEG = 25.0

#: Rayon d'exclusion de charniere, par piece. Une articulation reelle
#: s'interpenetre PAR CONSTRUCTION (rotule dans son logement, racine dans son
#: berceau) ; la mesure ecarte donc, des DEUX cotes, la matiere a moins de ce
#: rayon du pivot. C'est licite : une rotation autour d'un axe passant par le
#: pivot conserve la distance au pivot, donc rien de ce qui est exclu ne peut
#: rencontrer ce qui ne l'est pas.
SKIP_LIP = 0.14
SKIP_NODE = 0.24
SKIP_PLATE = 0.16
SKIP_CRESCENT = 0.18


def _godot_euler(x: float, y: float, z: float) -> Matrix:
    """Basis Godot pour `rotation = Vector3(x, y, z)` — ordre YXZ, en radians."""
    return (Matrix.Rotation(y, 4, "Y") @ Matrix.Rotation(x, 4, "X")
            @ Matrix.Rotation(z, 4, "Z"))


def _tangent_axis(pivot: Vector) -> Vector:
    """L'axe `UP x radial` d'une piece posee en couronne, en repere Godot.

    C'est exactement ce que calcule `harvester_combat._bind_iris()` pour l'iris
    du mini-boss : le code deduit l'axe de la POSITION du noeud, sans donnee
    supplementaire. On mesure donc avec le meme axe que celui qui sera ecrit.
    """
    radial = Vector((pivot.x, 0.0, pivot.z))
    if radial.length < 1e-6:
        return Vector((1.0, 0.0, 0.0))
    return Vector((0.0, 1.0, 0.0)).cross(radial.normalized()).normalized()


def _clip_sphere(verts: list, tri: list, pivot: Vector, skip: float,
                 out: list, depth: int = 0) -> None:
    """Garde de `tri` ce qui est HORS de la sphere (`pivot`, `skip`), en coupant.

    Un simple test « tous les sommets dedans ? » ne suffit pas : un longeron
    modelise d'un seul tenant produit des triangles qui enjambent la sphere de
    charniere. Ils seraient conserves ENTIERS, avec la matiere du joint dedans —
    et la mesure crierait sur une interpenetration normale. On coupe donc
    l'arete la plus longue, recursivement.
    """
    d = [(verts[i] - pivot).length for i in tri]
    if min(d) >= skip:
        out.append(list(tri))
        return
    if max(d) <= skip or depth >= 4:
        return
    k = max(range(3), key=lambda i: (verts[tri[i]] - verts[tri[(i + 1) % 3]]).length)
    a, b, c = tri[k], tri[(k + 1) % 3], tri[(k + 2) % 3]
    mid = len(verts)
    verts.append((verts[a] + verts[b]) * 0.5)
    _clip_sphere(verts, [a, mid, c], pivot, skip, out, depth + 1)
    _clip_sphere(verts, [mid, b, c], pivot, skip, out, depth + 1)


def _soup(obj, skips: list | None = None):
    """(sommets, triangles) d'un objet, en repere GODOT, compactes.

    `skips` : liste de (centre, rayon) dont la geometrie est ecartee — une
    charniere reelle s'interpenetre par construction, ce qui doit degager c'est
    tout le reste. Les rayons retenus sont publies au compte-rendu.
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.verts.index_update()
    raw = [_TO_GODOT @ v.co for v in bm.verts]
    tris = [[loop.vert.index for loop in face.loops] for face in bm.faces]
    bm.free()
    for center, radius in (skips or []):
        kept: list = []
        for tri in tris:
            _clip_sphere(raw, tri, center, radius, kept)
        tris = kept
    keep, remap, out = [], {}, []
    for tri in tris:
        row = []
        for i in tri:
            if i not in remap:
                remap[i] = len(keep)
                keep.append(raw[i])
            row.append(remap[i])
        out.append(row)
    return keep, out


class Solid:
    """Soupe de triangles figee, prete a repondre « a quelle distance ? »."""

    def __init__(self, verts: list, tris: list):
        self.verts = verts
        self.tris = tris
        self.tree = BVHTree.FromPolygons(verts, tris, all_triangles=True, epsilon=0.0)

    def distance_to(self, verts: list, tris: list) -> float:
        """Distance minimale a une autre soupe ; 0.0 si elles se mordent.

        Deux sens de requete : un sommet mobile pres d'une face fixe, ET un
        sommet fixe pres d'une face mobile. Un seul sens laisserait passer une
        lame mince qui traverse une grande face sans qu'aucun de ses sommets
        n'en approche.
        """
        if not tris or not self.tris:
            return 9.9
        other = BVHTree.FromPolygons(verts, tris, all_triangles=True, epsilon=0.0)
        if other.overlap(self.tree):
            return 0.0
        best = 2.0
        for v in verts:
            hit = self.tree.find_nearest(v, best)
            if hit[3] is not None:
                best = min(best, hit[3])
        for v in self.verts:
            hit = other.find_nearest(v, best)
            if hit[3] is not None:
                best = min(best, hit[3])
        return best


class Rig:
    """Chaine articulee posable : pivots, parentage, maillages en repere Godot.

    Reproduit exactement ce que Godot fera du `.glb` : origine de la piece sur
    son pivot, position de l'enfant RELATIVE au parent, rotation en euler YXZ
    (ou basis explicite pour les charnieres tangentielles).
    """

    def __init__(self, parts: list, skips: dict | None = None):
        skips = skips or {}
        self.names = [p.obj.name for p in parts]
        self.pivot = {p.obj.name: _TO_GODOT @ Vector(p.pivot) for p in parts}
        self.parent = {p.obj.name: p.parent for p in parts}
        self.verts, self.tris = {}, {}
        for part in parts:
            name = part.obj.name
            verts, tris = _soup(part.obj, skips.get(name))
            self.verts[name] = [v - self.pivot[name] for v in verts]
            self.tris[name] = tris

    def pose(self, angles: dict) -> dict:
        """Sommets monde de chaque piece, pour un jeu de rotations locales."""
        world: dict = {}
        out: dict = {}
        for name in self.names:
            parent = self.parent[name]
            base_pivot = (Vector((0.0, 0.0, 0.0)) if parent not in self.pivot
                          else self.pivot[parent])
            offset = self.pivot[name] - base_pivot
            local = Matrix.Translation(offset)
            base = (Matrix.Identity(4) if parent not in world else world[parent])
            spin = angles.get(name, (0.0, 0.0, 0.0))
            if not isinstance(spin, Matrix):
                spin = _godot_euler(*spin)
            world[name] = base @ local @ spin
            out[name] = [world[name] @ v for v in self.verts[name]]
        return out

    def clearance(self, poses: list, obstacle: Solid, only=None) -> tuple[float, str]:
        """Marge minimale sur toutes les poses, et la pose ou elle est atteinte."""
        best, where = 9.9, "aucune pose"
        for label, angles in poses:
            posed = self.pose(angles)
            for name, verts in posed.items():
                if only is not None and name not in only:
                    continue
                d = obstacle.distance_to(verts, self.tris[name])
                if d < best:
                    best, where = d, f"{label} / {name}"
        return best, where

    def self_clearance(self, poses: list, pairs: list) -> tuple[float, str]:
        """Marge minimale entre deux pieces de la meme chaine."""
        best, where = 9.9, "aucune pose"
        for label, angles in poses:
            posed = self.pose(angles)
            for a, b in pairs:
                solid = Solid(posed[a], self.tris[a])
                d = solid.distance_to(posed[b], self.tris[b])
                if d < best:
                    best, where = d, f"{label} / {a}-{b}"
        return best, where


def _rad(deg: float) -> float:
    return math.radians(deg)


def _orbit_angles(step: int) -> float:
    return 2.0 * math.pi * step / ORBIT_STEPS


def _shell_poses(with_crescent: bool, with_plates: bool, plate_axes: dict) -> list:
    """Poses de la coquille : orbite x bascule x chute, comme le combat les ecrira."""
    poses = []
    tilts = (0.0, 0.35, 0.7, 1.0) if with_crescent else (0.0,)
    drops = (0.0, 0.35, 0.7, 1.0) if with_plates else (0.0,)
    for s in range(ORBIT_STEPS):
        orbit = _orbit_angles(s)
        for tilt in tilts:
            for drop in drops:
                angles = {"Shell_Ring": (0.0, orbit, 0.0)}
                if with_crescent:
                    angles["Shell_Crescent"] = (_rad(CRESCENT_DEG) * tilt, 0.0, 0.0)
                if with_plates:
                    for name, axis in plate_axes.items():
                        angles[name] = Matrix.Rotation(
                            _rad(PLATE_DEG) * drop, 4, axis
                        )
                poses.append((
                    f"orbite {math.degrees(orbit):3.0f} deg / bascule "
                    f"{CRESCENT_DEG * tilt:2.0f} deg / chute "
                    f"{PLATE_DEG * drop:+3.0f} deg", angles))
    return poses


def _maw_poses(with_lip: bool, with_nodes: bool) -> list:
    poses = []
    for s in range(ORBIT_STEPS):
        spin = _orbit_angles(s)
        for lip in ((0.0, 0.3, 0.6, 1.0) if with_lip else (0.0,)):
            for node in ((0.0, 0.5, 1.0) if with_nodes else (0.0,)):
                angles = {"Core": (0.0, spin, 0.0)}
                if with_lip:
                    angles["Maw_Lip"] = (_rad(LIP_DEG) * lip, 0.0, 0.0)
                if with_nodes:
                    for i in range(3):
                        angles[f"Node_{i + 1:02d}"] = (_rad(NODE_DEG) * node, 0.0, 0.0)
                poses.append((
                    f"noyau {math.degrees(spin):3.0f} deg / levre "
                    f"{LIP_DEG * lip:2.0f} deg / noeuds {NODE_DEG * node:+3.0f} deg",
                    angles))
    return poses


def _spike_poses(spec: dict, flex_deg: float = FLEX_DEG,
                 axis: str = "y") -> list:
    """Pointage +/-40 deg (rotation.y) x flexion des deux maillons.

    ⚠️ La flexion du CONTRAT est celle du plan de jeu (`rotation.y`, le meme axe
    que le pointage) : le boss est un objet PLAT vu de dessus, et c'est dans ce
    plan que le fouettement d'une epine se lit. La flexion verticale
    (`rotation.x`) est mesuree a part, et ne va pas jusqu'a 25 deg — il n'y a
    pas un metre de vide sous une epine posee 30 cm au-dessus du pont.
    """
    name = spec["name"]
    poses = []
    for aim in (-1.0, -0.5, 0.0, 0.5, 1.0):
        for flex in (-1.0, -0.5, 0.0, 0.5, 1.0):
            bend = (_rad(flex_deg) * flex if axis == "x" else 0.0,
                    _rad(flex_deg) * flex if axis == "y" else 0.0, 0.0)
            poses.append((
                f"pointage {SPIKE_DEG * aim:+3.0f} deg / flexion "
                f"{flex_deg * flex:+3.0f} deg ({axis})",
                {name: (0.0, _rad(SPIKE_DEG) * aim, 0.0),
                 f"{name}_Mid": bend,
                 f"{name}_Tip": bend},
            ))
    return poses


def _ring_poses() -> list:
    """Les cinq anneaux tournent a des vitesses DISTINCTES : on echantillonne
    des dephasages premiers entre eux plutot qu'une rotation d'ensemble."""
    poses = []
    for s in range(ORBIT_STEPS):
        base = _orbit_angles(s)
        angles = {"Core": (0.0, base, 0.0)}
        for i in range(5):
            angles[f"Ring_{i + 1:02d}"] = (0.0, base * (1.0 + 0.37 * i), 0.0)
        poses.append((f"puits {math.degrees(base):3.0f} deg", angles))
    return poses


def _maw_footprint(rig: Rig, aperture: float) -> tuple[float, str]:
    """Degagement du puits EN VUE DE DESSUS, levre grande ouverte.

    Le critere de recette est visuel (« a `Maw_Lip` 90 deg, le tunnel et `Heart`
    sont entierement degages en vue de dessus »). On le double d'un chiffre : la
    distance horizontale minimale entre la levre ouverte et l'axe du puits,
    moins le rayon de l'ouverture. Positif = aucune matiere au-dessus du tunnel.
    """
    worst, where = 9.9, ""
    for s in range(ORBIT_STEPS):
        spin = _orbit_angles(s)
        posed = rig.pose({"Core": (0.0, spin, 0.0),
                          "Maw_Lip": (_rad(LIP_DEG), 0.0, 0.0),
                          "Node_01": (_rad(NODE_DEG), 0.0, 0.0),
                          "Node_02": (_rad(NODE_DEG), 0.0, 0.0),
                          "Node_03": (_rad(NODE_DEG), 0.0, 0.0)})
        for name, verts in posed.items():
            if name == "Core":
                continue
            for v in verts:
                d = math.hypot(v.x, v.z) - aperture
                if d < worst:
                    worst, where = d, f"{name} a noyau {math.degrees(spin):3.0f} deg"
    return worst, where


def _clearance_table(body, parts: dict) -> list:
    """Le tableau exige par le brief : piece / debattement / marge minimale."""
    rows = []
    body_solid = Solid(*_soup(body))

    def body_around(skips):
        return Solid(*_soup(body, skips))

    # --- 1/2/3 : la coquille -----------------------------------------------
    shell_parts = [parts["Shell_Ring"], parts["Shell_Crescent"]] + \
                  [parts[f"Plate_{i + 1:02d}"] for i in range(4)]
    plate_axes = {}
    for i in range(4):
        name = f"Plate_{i + 1:02d}"
        plate_axes[name] = _tangent_axis(_TO_GODOT @ plate_pivot(i))
    skips = {f"Plate_{i + 1:02d}": [(Vector((0.0, 0.0, 0.0)), SKIP_PLATE)]
             for i in range(4)}
    skips["Shell_Crescent"] = [(Vector((0.0, 0.0, 0.0)), SKIP_CRESCENT)]
    shell = Rig(shell_parts, skips)

    margin, where = shell.clearance(
        _shell_poses(False, False, plate_axes), body_solid, only=("Shell_Ring",))
    rows.append(("Shell_Ring / coque", "orbite 360 deg", margin, where))

    crescent_skip = [(_TO_GODOT @ Vector(CR_PIVOT), SKIP_CRESCENT)]
    margin, where = shell.clearance(
        _shell_poses(True, False, plate_axes), body_around(crescent_skip),
        only=("Shell_Crescent",))
    rows.append(("Shell_Crescent / coque",
                 f"orbite 360 deg x bascule 0 -> {CRESCENT_DEG:.0f} deg",
                 margin, where))

    plate_skip = [(_TO_GODOT @ plate_pivot(i), SKIP_PLATE) for i in range(4)]
    margin, where = shell.clearance(
        _shell_poses(True, True, plate_axes), body_around(plate_skip),
        only=tuple(f"Plate_{i + 1:02d}" for i in range(4)))
    m2, w2 = shell.self_clearance(
        _shell_poses(True, True, plate_axes),
        [(f"Plate_{i + 1:02d}", f"Plate_{j + 1:02d}")
         for i, j in ((0, 1), (1, 2), (2, 3), (3, 0))]
        + [(f"Plate_{i + 1:02d}", "Shell_Ring") for i in range(4)])
    if m2 < margin:
        margin, where = m2, w2 + " (entre pieces)"
    rows.append(("Plate_01..04 / coque, coquille et entre elles",
                 f"chute 0 -> {PLATE_DEG:.0f} deg x orbite x bascule",
                 margin, where))

    # --- 4/5/6 : le noyau, la levre, les noeuds -----------------------------
    maw_parts = [parts["Core"], parts["Maw_Lip"]] + \
                [parts[f"Node_{i + 1:02d}"] for i in range(3)]
    maw_skips = {"Maw_Lip": [(_TO_GODOT @ Vector(LIP_PIVOT), SKIP_LIP)]}
    for i in range(3):
        maw_skips[f"Node_{i + 1:02d}"] = [
            (_TO_GODOT @ node_base(i), SKIP_NODE)]
    maw = Rig(maw_parts, maw_skips)

    margin, where = maw.clearance(_maw_poses(False, False), body_solid,
                                  only=("Core",))
    rows.append(("Core / coque", "rotation 360 deg", margin, where))

    lip_skip = [(_TO_GODOT @ Vector(LIP_PIVOT), SKIP_LIP)]
    margin, where = maw.clearance(_maw_poses(True, False), body_around(lip_skip),
                                  only=("Maw_Lip",))
    m2, w2 = maw.self_clearance(_maw_poses(True, False), [("Maw_Lip", "Core")])
    if m2 < margin:
        margin, where = m2, w2 + " (contre le noyau)"
    rows.append(("Maw_Lip / coque et noyau", f"ouverture 0 -> {LIP_DEG:.0f} deg",
                 margin, where))

    node_skip = [(_TO_GODOT @ node_base(i), SKIP_NODE) for i in range(3)]
    margin, where = maw.clearance(_maw_poses(True, True), body_around(node_skip),
                                  only=tuple(f"Node_{i + 1:02d}" for i in range(3)))
    m2, w2 = maw.self_clearance(
        _maw_poses(True, True),
        [(f"Node_{i + 1:02d}", "Maw_Lip") for i in range(3)]
        + [(f"Node_{i + 1:02d}", "Core") for i in range(3)]
        + [("Node_01", "Node_02"), ("Node_02", "Node_03")])
    if m2 < margin:
        margin, where = m2, w2 + " (contre levre/noyau/voisin)"
    rows.append(("Node_01..03 / levre, noyau, coque",
                 f"retraction 0 -> {NODE_DEG:.0f} deg x levre x noyau",
                 margin, where))

    # --- 7 : les anneaux du puits -------------------------------------------
    ring_parts = [parts["Core"]] + [parts[f"Ring_{i + 1:02d}"] for i in range(5)]
    rings = Rig(ring_parts)
    margin, where = rings.clearance(
        _ring_poses(), body_solid,
        only=tuple(f"Ring_{i + 1:02d}" for i in range(5)))
    m2, w2 = rings.self_clearance(
        _ring_poses(),
        [(f"Ring_{i + 1:02d}", f"Ring_{i + 2:02d}") for i in range(4)])
    if m2 < margin:
        margin, where = m2, w2 + " (entre anneaux)"
    rows.append(("Ring_01..05 / paroi du puits et entre eux",
                 "360 deg continu, vitesses distinctes", margin, where))

    # --- 8/9 : les epines ----------------------------------------------------
    worst_root, where_root = 9.9, ""
    worst_flex, where_flex = 9.9, ""
    vertical_limit, vertical_where = FLEX_DEG, "toute la course"
    for spec in SPIKES:
        name = spec["name"]
        chain = [parts[name], parts[f"{name}_Mid"], parts[f"{name}_Tip"]]
        # Exclusion de charniere : le rayon de l'epine a l'articulation, majore
        # de 20 %. C'est la rotule (invariante par rotation) plus son jeu.
        ts = (0.0,) + spec["splits"]
        skips = {}
        for seg, part in enumerate(chain):
            radius = spike_radius(spec, ts[seg]) * 1.20
            skips[part.obj.name] = [(_TO_GODOT @ Vector(part.pivot), radius)]
            if seg < 2:   # la piece porte aussi le joint de son enfant
                child = chain[seg + 1]
                skips[part.obj.name].append(
                    (_TO_GODOT @ Vector(child.pivot),
                     spike_radius(spec, ts[seg + 1]) * 1.20))
        rig = Rig(chain, skips)
        obstacle = Solid(*_soup(body, [
            (_TO_GODOT @ Vector(parts[name].pivot),
             spike_radius(spec, 0.0) * 1.20)]))
        poses = _spike_poses(spec)
        m, w = rig.clearance(poses, obstacle, only=(name,))
        if m < worst_root:
            worst_root, where_root = m, f"{name} : {w}"
        m, w = rig.clearance(poses, obstacle,
                             only=(f"{name}_Mid", f"{name}_Tip"))
        m2, w2 = rig.self_clearance(
            poses, [(name, f"{name}_Mid"), (f"{name}_Mid", f"{name}_Tip"),
                    (name, f"{name}_Tip")])
        if m2 < m:
            m, w = m2, w2 + " (dans la chaine)"
        if m < worst_flex:
            worst_flex, where_flex = m, f"{name} : {w}"
        # Flexion VERTICALE : on cherche le plafond reel, par pas de 5 deg.
        for deg in range(5, int(FLEX_DEG) + 1, 5):
            mv, wv = rig.clearance(_spike_poses(spec, float(deg), "x"), obstacle)
            if mv <= 0.010 and deg < vertical_limit:
                vertical_limit, vertical_where = deg - 5, f"{name} : {wv}"
                break
    rows.append(("Spike_01..04 / coque", f"pointage +/-{SPIKE_DEG:.0f} deg",
                 worst_root, where_root))
    rows.append(("Spike_0X_Mid et _Tip / coque et chaine",
                 f"flexion +/-{FLEX_DEG:.0f} deg chacun (plan de jeu)",
                 worst_flex, where_flex))
    print(f"  [i  ] flexion VERTICALE (rotation.x) encaissee sans morsure : "
          f"+/-{vertical_limit:.0f} deg  ({vertical_where})")

    # --- recette de la phase 4 : le puits vu de dessus ----------------------
    margin, where = _maw_footprint(maw, SHAFT[0][1])
    rows.append(("Maw_Lip ouverte / aplomb du puits (vue de dessus)",
                 f"levre {LIP_DEG:.0f} deg, noeuds {NODE_DEG:.0f} deg",
                 margin, where))
    return rows


# ==========================================================================
# Assemblage
# ==========================================================================


def _triangulate_ngons(obj) -> None:
    """Coupe les n-gons — sans quoi l'export n'a AUCUNE tangente.

    L'exporteur glTF de Blender refuse le calcul mikktspace des que le maillage
    porte une face de plus de quatre sommets : « Tangent space can only be
    computed for tris/quads, aborting ». Il le dit dans le flot de sortie et
    exporte quand meme — silencieusement, sans l'attribut TANGENT. Une coque
    livree comme ca a des UV, donc l'air texturable, et un shader de relief y
    reste plat. Les `cap_ring` de ce script (culots, tranches de secteur) en
    produisent des dizaines : la passe est obligatoire, pas cosmetique.
    """
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons)
    bm.to_mesh(obj.data)
    bm.free()


def _finish(obj, bevel: float = 0.006, angle: float = 34.0) -> None:
    """Finition commune : soudure, chanfrein, lissage, decoupe, **depliage UV**.

    Le chanfrein a UN segment reste nettement sous la profondeur des panneaux
    (24-30 mm) : la marche reste franche. Le depliage vient en dernier parce que
    le chanfrein et la triangulation creent des faces — les deplier avant les
    laisserait sans UV coherente.
    """
    ak.cleanup(obj)
    if bevel > 0.0:
        ak.bevel_sharp_edges(obj, width=bevel, segments=1, angle_deg=angle)
    ak.shade_smooth_by_angle(obj, angle_deg=angle)
    _triangulate_ngons(obj)
    # UV par projection en boite (ADR-0011 SS2) : le support des feuilles de
    # detail repetables, appliquees cote Godot. Aucune texture n'est embarquee
    # dans le `.glb` — seulement les coordonnees.
    ak.box_project_uv(obj, TEXELS_PER_METER)


def _bounds(objs: list) -> tuple[Vector, Vector]:
    lo = Vector((math.inf,) * 3)
    hi = Vector((-math.inf,) * 3)
    for obj in objs:
        for vert in obj.data.vertices:
            for a in range(3):
                lo[a] = min(lo[a], vert.co[a])
                hi[a] = max(hi[a], vert.co[a])
    return lo, hi


def main() -> None:
    ak.reset_scene()
    ak.set_faction(ak.FACTION_NULL_CHOIR)

    body = build_body()
    parts = [
        build_shell_ring(),
        build_crescent(),
        *[build_plate(i) for i in range(len(PLATES))],
        build_core(),
        build_maw_lip(),
        *[build_node(i) for i in range(3)],
        *[build_ring(i) for i in range(len(RINGS))],
        build_heart(),
    ]
    for spec in SPIKES:
        parts += [build_spike_segment(spec, seg) for seg in range(3)]
    by_name = {p.obj.name: p for p in parts}

    _finish(body)
    for part in parts:
        # Le noyau reste lisse : un chanfrein sur ses ~200 ecailles de croute
        # couterait plus de 4 000 triangles pour un gain nul sur une sphere
        # emissive.
        _finish(part.obj, bevel=0.0 if part.obj.name == "Core" else 0.005,
                angle=30.0 if part.obj.name == "Core" else 34.0)

    # --- controle en repere d'auteur, avant tout export --------------------
    objs = [body] + [p.obj for p in parts]
    lo, hi = _bounds(objs)
    print("--- mesures en repere d'auteur (avant correction d'axe) ---")
    for obj in objs:
        o_lo, o_hi = _bounds([obj])
        print(f"  {obj.name:<16} x[{o_lo.x:+.3f} {o_hi.x:+.3f}] "
              f"y[{o_lo.y:+.3f} {o_hi.y:+.3f}] z[{o_lo.z:+.3f} {o_hi.z:+.3f}] "
              f"{len(obj.data.polygons)} faces")
    print(f"  TOTAL            x[{lo.x:+.3f} {hi.x:+.3f}] y[{lo.y:+.3f} {hi.y:+.3f}] "
          f"z[{lo.z:+.3f} {hi.z:+.3f}]  ->  {hi.x - lo.x:.3f} x {hi.y - lo.y:.3f} "
          f"x {hi.z - lo.z:.3f} m")

    # --- degagement a fond de course (BRIEF-0040) --------------------------
    print("--- degagement des pieces mobiles (maillage livre, poses du combat) ---")
    failures = []
    for name, travel, margin, where in _clearance_table(body, by_name):
        verdict = "OK " if margin > 0.0 else "MORD"
        print(f"  [{verdict}] {name:<44} {travel:<48} {margin * 1000:8.1f} mm  ({where})")
        if margin <= 0.0:
            failures.append(f"{name} : {where}")
    if failures:
        raise ak.ContractError(
            "pieces mobiles qui mordent la coque ou leur voisine :\n"
            + "\n".join(f"  - {f}" for f in failures)
        )

    ak.export_hull(body, build_attach_points(), OUTPUT, CONTRACT, parts=parts)


if __name__ == "__main__":
    main()
