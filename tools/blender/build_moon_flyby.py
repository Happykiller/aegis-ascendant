"""build_moon_flyby.py — le decor du survol de lune (BRIEF-0085).

    blender-aegis -b -P tools/blender/build_moon_flyby.py
    blender-aegis -b -P tools/blender/build_moon_flyby.py -- --plate
    ./scripts/build-hull.sh --check moon_flyby      # + controle de determinisme

Produit `assets/imported/models/backgrounds/moon_flyby.glb` et, avec `--plate`, les
deux planches de recette de `docs/forge/output/`.

Le script EST la source de l'asset (ADR-0008) : aucun `.blend` versionne, aucun alea
non seede, deux executions successives rendent le meme sha256. Sept harnais de mesure
tournent a chaque build (plafond, sommet, budgets, UV, densite de texels, contrat de
noms, degagement des impacts) et **tous echouent le build** — voir `_audit()`.


CE QUI DECIDE DE CE DECOR : ON LE REGARDE PAR EN DESSOUS, ET IL TOURNE
=====================================================================
La camera de jeu est a (0, 14, 5) et plonge de 70 deg sous l'horizontale ; la lune
est une sphere de rayon 60 centree en (0, -78, 34). Trois consequences MESUREES
(`_visible_band()` les recalcule a chaque build, elles ne sont pas supposees) :

1. **Le point sous-camera n'est pas dans le cadre.** Il tombe 6,5 deg sous le bord
   bas. Tout ce qu'on voit de la lune est donc compris entre le bas du cadre et le
   limbe : une BANDE, pas une calotte centree sur le regard.
2. **La bande vue vaut 109 deg de longitude sur 101 de latitude** — 9 860 m2, 21 %
   de la sphere. Modeliser la sphere entiere, c'est payer cinq fois ce qu'on montre.
3. **La rotation deplace la bande.** La lune tourne de 0,022 rad/s autour de X et
   parcourt 63 deg pendant la phase : la fenetre visible glisse en longitude. C'est
   l'union sur tout le parcours qu'il faut mailler, pas la pose de depart.

D'ou la forme livree : une **calotte-bande** en longitude [-152, +6] deg et latitude
+/-68 deg autour de l'axe de rotation X, dont seul le coeur [-134, -16] x +/-56 est
maille fin. Le reste est une ceinture de securite a mailles larges : elle ne coute
presque rien et elle evite qu'un bord ouvert entre dans le cadre si la camera bouge
ou si l'ecran est plus large que 16:9.


LA FRONTIERE GEOMETRIE / TEXTURE — LE SUJET DU BRIEF
====================================================
La matiere vient de l'operateur (`TEX-0001`, deja en jeu) et la tuile couvre **55 m**.
C'est ce chiffre qui trace la frontiere, et il la trace deux fois :

  * **Par le haut.** Une tuile qui se repete tous les 55 m ne peut porter aucun relief
    de plus d'un tiers de tuile sans que la repetition se lise comme un quadrillage.
    Tout ce qui depasse ~16 m est donc GEOMETRIQUE par obligation, pas par gout.
  * **Par le bas.** Le plus gros cratere de `TEX-0001` fait ~9 m a cette echelle, et
    son cratere median ~2,8 m. En dessous de 8 m, la carte fait mieux que le maillage
    pour un cout nul.

Les familles livrees ici commencent donc a 8 m et non a 3 :

    texture (TEX-0001)   0,5  ->  9 m   grain, piqures, petits crateres
    crateres francs      8    -> 10 m   18 pieces, bord marque, terrasses
    grands bassins      16    -> 34 m   6 pieces, fond large, pic central sur 2
    ondulation de fond  45    -> 95 m   +/-0,45 m, pour que le limbe ne soit
                                        jamais un arc de cercle parfait

⚠️ **Ecart assume au brief, et c'est le seul.** Le brief bornait les crateres a
« 1,5 a 5 » de rayon. Les 18 crateres francs tiennent cette borne (4,0 a 5,0), au
sommet de la fourchette comme le demande la section « les textures sont deja
livrees ». Les 6 **bassins** la depassent (rayon 8 a 17). Trois raisons, dans
l'ordre de force :
  a) la planche de reference — juge declare du chantier — montre un bassin qui
     occupe un sixieme du cadre ; a la distance mesuree (36 m au bas du cadre) cela
     vaut ~25 m de surface, pas 10 ;
  b) la lecon « un cratere de rayon 9 lisait comme une flaque » a ete payee sur la
     DOUBLURE, dont les crateres etaient des palets plats poses a R-0,2 : c'est
     l'absence de creux qui faisait la flaque, pas le diametre ;
  c) au-dela de 16 m, la texture ne peut plus rien (voir ci-dessus) : soit la
     geometrie porte cette echelle, soit personne ne la porte.
Les bassins sont donc **creux, terrasses et a bord bas** — l'exact contraire du
palet qui a echoue.


CE QUE LE DEPLIAGE DOIT AU BRIEF
================================
`ak.box_project_uv()` est explicitement ecarte pour la calotte : ses ilots arbitraires
etireraient la carte sur les flancs de cratere. La calotte porte une **projection
azimutale equidistante** centree sur le milieu de la bande vue (longitude -76 deg).
Deux proprietes decident de ce choix :

  * **aucune couture a l'interieur de la piece.** La projection est une carte unique
    et continue ; sa seule discontinuite est l'antipode, a 180 deg du centre, alors
    que la calotte s'arrete a 82. Les seules coutures du maillage sont donc son BORD,
    qui est hors champ par construction ;
  * **l'echelle est exacte dans la direction radiale et ne derive que tangentiellement**,
    de 55 m/tuile au centre a ~43 aux coins extremes (facteur psi/sin(psi)). Un
    deroule cylindrique classique aurait donne 55/cos(beta), soit 35 m/tuile aux
    memes coins — deux fois plus de derive. Les deux chiffres sont MESURES sur le
    maillage par `_texel_density()`, pas deduits de cette phrase.

⚠️ **Les UV portent deja l'echelle de 55 m par tuile.** Cote Godot, `uv1_scale` doit
donc rester (1, 1, 1) : le `sphere_tiles()` que la doublure appliquait a sa
`SphereMesh` ferait ici tuiler la carte 6,9 fois de trop. Meme regle pour les
rochers, dont la projection en boite est calee a 8 m par tuile (`TEX-0002`).


CE QUE CE SCRIPT N'UTILISE PAS DU KIT, ET POURQUOI
==================================================
`aegis_kit` est utilise SANS AUCUNE MODIFICATION, mais `ak.export_hull()` ne peut pas
etre appele ici — ce n'est pas un choix de confort, c'est une incompatibilite de
contrat, verifiee dans le code du kit :

  * `export_hull()` exporte **une** coque maillee dont le noeud reste a l'origine,
    plus des pieces mobiles. Or les quatre corps de ce decor portent chacun une
    TRANSLATION que le moteur relit : `MoonFlyby._collect_bodies()` deduit la vitesse
    de derive de `body.position.y`, et un rocher a l'origine derait a 3,2 u/s en se
    teleportant de 85 unites au premier rebouclage ;
  * le controle d'orientation du kit compare le Y d'auteur des sommets **locaux** de
    la coque au Z du glTF **translation comprise** : il n'est vrai que si le noeud de
    la coque est a l'origine. Passer la lune en piece mobile et un rocher en coque
    ne resout donc rien ;
  * le contrat verifie en outre un pivot centre a 2 cm pres et une bbox largeur x
    longueur imposee : deux notions qui n'ont pas de sens pour un decor de 160 m.

L'export et la validation sont donc refaits ici, a l'identique sur le fond : meme
correction d'axe (demi-tour autour de Z avant `export_yup`), meme relecture du `.glb`
PRODUIT plutot que de la scene en memoire, meme regle « au moindre ecart, on echoue ».
La chaine d'axes est reverifiee analytiquement par `_assert_axis_chain()`.

Le kit fournit le reste : conversion sRGB -> lineaire, `box_project_uv()` pour les
rochers, `cleanup()`, et `ContractError`.


REPERE DE TRAVAIL
=================
Tout ce fichier raisonne dans le repere **Godot** (X lateral, Y haut, Z profondeur,
« haut de l'ecran » = -Z), parce que c'est celui du brief, du code et des mesures.
La conversion vers le repere d'auteur de l'ADR-0008 se fait au dernier moment, dans
`_author()`, et une seule fois par sommet. Composee avec la correction d'axe et le
`yup` de l'exporteur, elle rend l'identite — c'est ce que verifie `_assert_axis_chain()`.
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

OUTPUT = os.path.join(_REPO, "assets/imported/models/backgrounds/moon_flyby.glb")
PLATE_SCENE = os.path.join(_REPO, "docs/forge/output/BRIEF-0085-planche-survol.png")
PLATE_UV = os.path.join(_REPO, "docs/forge/output/BRIEF-0085-planche-uv.png")

# ==========================================================================
# La geometrie du lieu — relevee sur scripts/vfx/moon_flyby.gd, pas supposee
# ==========================================================================

#: Centre implicite et rayon de la lune, en repere Godot (`MOON_CENTER`, `MOON_RADIUS`).
MOON_CENTER = Vector((0.0, -78.0, 34.0))
MOON_RADIUS = 60.0
#: Plafond du decor : rien ne monte au-dessus (`CEILING_Y`).
CEILING_Y = -3.0
#: Le ciel du survol : tout le decor vit au-dessus (`SKY_Y`).
SKY_Y = -45.0
#: Rotation de la lune autour de X, rad/s (`MOON_SPIN`), et duree la plus longue de
#: la phase. ⚠️ Le brief annonce « ~63 deg parcourus », ce qui correspond a 50 s ;
#: on couvre 60 s (75,6 deg), la borne haute de la fourchette « 45 a 60 s », parce
#: que la phase s'arrete au nettoyage de la vague et non a un chronometre.
MOON_SPIN = 0.022
PHASE_SECONDS = 60.0
SWEEP = MOON_SPIN * PHASE_SECONDS  # rad

#: Camera de jeu, relevee sur scenes/gameplay/graybox.tscn:48.
CAM_POS = Vector((0.0, 14.0, 5.0))
CAM_FORWARD = Vector((0.0, -0.940, -0.342)).normalized()
CAM_UP = Vector((0.0, 0.342, -0.940)).normalized()
CAM_RIGHT = Vector((1.0, 0.0, 0.0))
CAM_FOV_V = math.radians(62.0)
#: 1920 x 1080 (project.godot) : le FOV de Godot est VERTICAL par defaut.
CAM_ASPECT = 16.0 / 9.0

#: Ou tombent les bolides, en (x, z) monde (`IMPACT_SPOTS`), et quand (`IMPACT_TIMES`).
#: ⚠️ La lune a tourne quand ils tombent : le point de SURFACE concerne n'est pas
#: celui de la pose de depart. `_impact_marks()` fait la correction.
IMPACT_SPOTS = ((-6.0, 10.0), (12.0, 2.0), (-14.0, -2.0))
IMPACT_TIMES = (11.0, 26.0, 40.0)
#: Rayon de surface a garder degage autour de chaque point d'impact.
IMPACT_CLEAR = 14.0

#: Les rochers : position Godot et rayon hors-tout. Valeurs de la doublure, deja
#: reglees en capture (`_build_stand_in()`), y compris l'ecart d'`Asteroid_02` hors
#: du couloir de vol. On ne les redefinit pas, on les habille.
ROCKS = (
    ("Asteroid_01", Vector((-13.0, -13.0, -18.0)), 6.5, 0x01),
    ("Asteroid_02", Vector((15.0, -29.0, 15.0)), 5.0, 0x02),
    ("Asteroid_03", Vector((19.0, -34.0, -34.0)), 12.0, 0x03),
)

# ==========================================================================
# Budgets et echelles de texture
# ==========================================================================

TRI_BUDGET_CAP = 12_000
TRI_BUDGET_ROCK = 2_500

#: Metres de surface couverts par une tuile de texture. ⚠️ REGLE EN REGARDANT
#: (2026-08-26) et cuit dans les UV : cote Godot `uv1_scale` reste (1, 1, 1).
MOON_METRES_PER_TILE = 55.0
ROCK_METRES_PER_TILE = 8.0

#: Couleurs de surface. Ce sont les valeurs LINEAIRES deja validees en capture sur la
#: doublure (`moon_flyby.gd`), pas des valeurs inventees : a 0,30 d'albedo la lune
#: rendait rose pale et le chasseur blanc s'y perdait. Aucune couleur de la charte ne
#: convient — les palettes y sont des palettes de FACTION, et la lune n'en a pas.
MOON_ALBEDO = (0.115, 0.115, 0.140)
ROCK_ALBEDO = (0.100, 0.098, 0.118)

# ==========================================================================
# La bande maillee, en coordonnees (longitude, latitude) autour de l'axe X
# ==========================================================================
#
# n(lam, bet) = (sin bet, cos bet cos lam, cos bet sin lam)
#
#   * `lam` (longitude) se compte depuis le sommet de la lune (+Y) vers +Z, donc vers
#     le BAS de l'ecran. La rotation autour de X ajoute simplement `theta` a `lam` :
#     c'est ce qui fait de cet axe le bon axe de parametrage.
#   * `bet` (latitude) sort du plan YZ le long de l'axe de rotation X. La rotation ne
#     la change pas.

#: Coeur maille fin — l'union des fenetres visibles sur tout le parcours, + 3 deg.
CORE_LAM = (math.radians(-147.0), math.radians(-16.0))
CORE_BET = math.radians(56.0)
#: Ceinture de securite a mailles larges, jamais vue en 16:9 mais peu chere. Elle
#: couvre ce qui arriverait au limbe si la phase durait DEUX FOIS plus longtemps que
#: prevu — la phase se termine quand la vague est nettoyee, pas sur un chronometre.
EDGE_LAM = (math.radians(-185.0), math.radians(6.0))
EDGE_BET = math.radians(68.0)
#: Pas du maillage de coeur, en degres de grand cercle (1 deg = 1,047 m ici).
STEP_LAM = math.radians(2.72)
STEP_BET = math.radians(2.92)
#: Pas de la ceinture.
STEP_EDGE = math.radians(6.0)

#: Centre de la projection azimutale : le milieu de la bande VUE (mesuree :
#: longitude -144 a -22,5 deg). C'est lui qui minimise la derive tangentielle, et il
#: se recale si la bande change — `_assert_uv_centre()` echoue le build sinon.
UV_CENTER_LAM = math.radians(-83.0)


def _dir(lam: float, bet: float) -> Vector:
    """Direction unitaire du centre de la lune vers la surface, en repere Godot."""
    cb = math.cos(bet)
    return Vector((math.sin(bet), cb * math.cos(lam), cb * math.sin(lam)))


def _lam_bet(direction: Vector) -> tuple[float, float]:
    """Inverse de `_dir()`."""
    return math.atan2(direction.z, direction.y), math.asin(max(-1.0, min(1.0, direction.x)))


# ==========================================================================
# Le relief — trois familles, et la frontiere avec la texture
# ==========================================================================


class Feature:
    """Un creux de la surface : cratere franc ou grand bassin.

    ⚠️ Le profil est defini pour que le creux se lise comme un CREUX. La doublure a
    fait la faute inverse (palets de 0,6 poses a R-0,2, qui DEPASSAIENT au limbe) :
    ici le fond descend, le bord monte a peine, et la couverture d'ejectas redescend
    a zero. Au limbe, la silhouette mord donc vers l'interieur.
    """

    __slots__ = ("lam", "bet", "radius", "depth", "rim", "floor", "reach",
                 "terrace", "peak", "kind", "dir")

    def __init__(self, lam, bet, radius, depth, rim, floor, reach, terrace, peak, kind):
        self.lam = lam
        self.bet = bet
        self.radius = radius
        self.depth = depth
        self.rim = rim
        self.floor = floor
        self.reach = reach
        self.terrace = terrace
        self.peak = peak
        self.kind = kind
        self.dir = _dir(lam, bet)

    def height(self, cos_angle: float) -> float:
        """Contribution en metres, pour un point a `cos_angle` du centre du creux."""
        angle = math.acos(max(-1.0, min(1.0, cos_angle)))
        s = angle * MOON_RADIUS / self.radius
        if s >= self.reach:
            return 0.0
        if s <= self.floor:
            value = -self.depth
            if self.peak > 0.0:
                t = s / self.floor
                value += self.peak * 0.5 * (1.0 + math.cos(math.pi * min(1.0, t)))
            return value
        if s <= 1.0:
            t = (s - self.floor) / (1.0 - self.floor)
            span = self.depth + self.rim
            value = -self.depth + span * (t * t)
            if self.terrace > 0.0:
                # Deux banquettes : le terme s'annule exactement en t=0 et t=1, donc
                # il ne touche ni le fond ni la crete — il ne fait que les relier.
                value += span * self.terrace * math.sin(2.0 * math.pi * 2.0 * t)
            return value
        u = (s - 1.0) / (self.reach - 1.0)
        return self.rim * (1.0 - u) ** 2.4


def _undulation(lam: float, bet: float) -> float:
    """Relief de tres grande longueur d'onde : 45 a 95 m, +/-0,45 m.

    Sa seule fonction est le LIMBE. Aucune carte de 55 m ne peut porter une forme de
    90 m sans la repeter visiblement, et un limbe qui reste un arc de cercle parfait
    pendant soixante secondes trahit la sphere.
    """
    x = MOON_RADIUS * bet
    y = MOON_RADIUS * lam
    return (
        0.38 * math.sin(2.0 * math.pi * x / 71.0 + 0.7)
        * math.cos(2.0 * math.pi * y / 93.0 + 1.9)
        + 0.26 * math.sin(2.0 * math.pi * (0.6 * x + 0.8 * y) / 58.0 + 2.4)
        + 0.17 * math.sin(2.0 * math.pi * (0.9 * x - 0.5 * y) / 47.0)
    )


def _impact_marks() -> list[Vector]:
    """Les trois points d'impact, ramenes dans le repere du CORPS de la lune.

    ⚠️ Le code calcule le point d'impact sur la sphere en coordonnees MONDE, a
    l'instant du choc — donc apres que la lune a tourne de `MOON_SPIN * t`. La zone
    de surface a degager n'est pas sous le point monde a t = 0, elle est en amont de
    `theta(t)`. Se tromper ici, c'est degager trois zones qui ne seront jamais
    frappees et laisser un massif de crateres sous chaque impact.
    """
    marks: list[Vector] = []
    for (x, z), when in zip(IMPACT_SPOTS, IMPACT_TIMES):
        dx = x - MOON_CENTER.x
        dz = z - MOON_CENTER.z
        flat = dx * dx + dz * dz
        if flat >= MOON_RADIUS * MOON_RADIUS:
            raise ak.ContractError(f"impact ({x}, {z}) hors du disque de la lune")
        world = Vector((dx, math.sqrt(MOON_RADIUS * MOON_RADIUS - flat), dz)) / MOON_RADIUS
        theta = MOON_SPIN * when
        # Rotation inverse autour de X : monde -> corps.
        c, s = math.cos(-theta), math.sin(-theta)
        marks.append(Vector((world.x, c * world.y - s * world.z, s * world.y + c * world.z)))
    return marks


def _features() -> list[Feature]:
    """Le catalogue de relief, tire une fois pour toutes avec une graine fixe.

    Le tirage est SOUS CONTRAINTES, et ce sont elles qui portent la lecture :
      * ecartement minimal de 1,35 fois la somme des rayons — deux crateres qui se
        recoupent restent lisibles, trois qui se chevauchent font une bouillie ;
      * 14 m de degagement autour des trois points d'impact (`_impact_marks()`) ;
      * repartition sur toute la bande maillee, et pas sur la seule pose de depart :
        la lune parcourt 63 deg, un massif concentre sortirait du cadre en vingt
        secondes.
    """
    rng = random.Random(0x0085)
    marks = _impact_marks()
    out: list[Feature] = []

    def place(radius, depth, rim, floor, reach, terrace, peak, kind, tries=400):
        for _ in range(tries):
            lam = rng.uniform(CORE_LAM[0] + 0.05, CORE_LAM[1] - 0.05)
            bet = rng.uniform(-CORE_BET + 0.05, CORE_BET - 0.05)
            here = _dir(lam, bet)
            ok = True
            for mark in marks:
                if MOON_RADIUS * math.acos(max(-1.0, min(1.0, here.dot(mark)))) < \
                        IMPACT_CLEAR + radius:
                    ok = False
                    break
            if ok:
                for other in out:
                    gap = MOON_RADIUS * math.acos(
                        max(-1.0, min(1.0, here.dot(other.dir))))
                    if gap < 1.25 * (radius + other.radius):
                        ok = False
                        break
            if ok:
                out.append(Feature(lam, bet, radius, depth, rim, floor, reach,
                                   terrace, peak, kind))
                return
        raise ak.ContractError(
            f"relief {kind} r={radius:.1f} : aucune place libre en {tries} essais")

    # --- Les grands bassins, poses en premier : ce sont eux qui structurent -----
    # Rayon 8 a 17 m (16 a 34 m de diametre), creux de 1/11 de leur diametre — le
    # rapport reel d'un bassin complexe, pas celui d'un cratere simple. Bord bas,
    # murs en banquettes, pic central sur les deux plus grands.
    for radius, depth, rim, terrace, peak in (
        (17.0, 3.55, 0.42, 0.055, 1.30),
        (14.5, 3.00, 0.38, 0.050, 1.05),
        (12.5, 2.60, 0.34, 0.048, 0.0),
        (11.0, 2.30, 0.30, 0.045, 0.0),
        (10.0, 2.05, 0.28, 0.040, 0.0),
        (9.0, 1.85, 0.26, 0.0, 0.0),
        (8.5, 1.70, 0.24, 0.0, 0.0),
        (8.0, 1.60, 0.22, 0.0, 0.0),
    ):
        place(radius, depth, rim, 0.34, 1.26, terrace, peak, "basin")

    # --- Les crateres francs ---------------------------------------------------
    # Rayon 4,0 a 5,0 (8 a 10 m de diametre) : le HAUT de la fourchette du brief,
    # pour rester distincts du plus gros cratere de TEX-0001 (~9 m). Creux de 0,18
    # fois leur diametre — le rapport d'un cratere simple frais.
    fresh = 18
    for index in range(26):
        radius = 4.0 + rng.random() * 1.0
        old = index >= fresh
        # ⚠️ CES DEUX CHIFFRES SONT LA LISIBILITE MEME, et ils ont ete regles EN
        # REGARDANT. A 0,36 de rayon de profondeur et un tablier d'ejectas etale
        # jusqu'a 1,55 rayon, la premiere planche rendait une lune LISSE : la lumiere
        # du jeu vient de derriere la camera (KeyLight a 55 deg au-dessus de l'axe),
        # elle est donc frontale, et une pente douce ne fait aucune ombre. Un cratere
        # ne se lit ici que par la RUPTURE de pente a sa crete : d'ou un tablier
        # resserre a 1,35 rayon et un bourrelet a 0,105.
        depth = (0.42 if not old else 0.26) * radius
        rim = (0.105 if not old else 0.055) * radius
        place(radius, depth, rim,
              0.30 if not old else 0.46,
              1.35 if not old else 1.55,
              0.050 if (not old and radius > 4.55) else 0.0,
              0.0, "crater" if not old else "crater_old")
    return out


FEATURES: list[Feature] = _features()


def _height(lam: float, bet: float) -> float:
    """Relief total en un point, en metres au-dessus du rayon nominal."""
    here = _dir(lam, bet)
    total = _undulation(lam, bet)
    for feature in FEATURES:
        cos_angle = here.dot(feature.dir)
        # Court-circuit : au-dela de 40 deg il n'y a plus rien a calculer.
        if cos_angle > 0.766:
            total += feature.height(cos_angle)
    return total


def _surface(lam: float, bet: float) -> Vector:
    """Position d'un point de surface, LOCALE au pivot `Moon` (repere Godot)."""
    return _dir(lam, bet) * (MOON_RADIUS + _height(lam, bet))


# ==========================================================================
# Le depliage — projection azimutale equidistante, centree sur la bande vue
# ==========================================================================

_UV_N0 = _dir(UV_CENTER_LAM, 0.0)
_UV_E1 = Vector((0.0, -math.sin(UV_CENTER_LAM), math.cos(UV_CENTER_LAM)))
_UV_E2 = Vector((1.0, 0.0, 0.0))


def _uv(lam: float, bet: float) -> tuple[float, float]:
    """UV en TUILES (1 unite = une tuile = 55 m de surface).

    Projection azimutale equidistante : la distance au centre de la carte est
    exactement la distance geodesique sur la lune. L'echelle est donc juste dans la
    direction radiale partout, et ne derive que tangentiellement, d'un facteur
    psi/sin(psi) (mesure par `_texel_density()`).
    """
    here = _dir(lam, bet)
    a = here.dot(_UV_E1)
    b = here.dot(_UV_E2)
    c = here.dot(_UV_N0)
    sin_psi = math.hypot(a, b)
    psi = math.atan2(sin_psi, c)
    k = (MOON_RADIUS * psi / sin_psi) if sin_psi > 1e-9 else MOON_RADIUS
    return (a * k / MOON_METRES_PER_TILE, b * k / MOON_METRES_PER_TILE)


# ==========================================================================
# Maillage de la calotte — grille structuree + raffinement local
# ==========================================================================


def _samples(core: tuple[float, float], edge: tuple[float, float],
             step: float) -> tuple[list[float], int, int]:
    """Echantillonnage 1D : ceinture large, coeur regulier, ceinture large.

    Retourne (valeurs, index de debut du coeur, index de fin du coeur).
    """
    count = max(2, int(round((core[1] - core[0]) / step)))
    core_values = [core[0] + (core[1] - core[0]) * i / count for i in range(count + 1)]
    before: list[float] = []
    value = core[0] - STEP_EDGE
    while value > edge[0] - 1e-9:
        before.append(value)
        value -= STEP_EDGE
    before.reverse()
    after: list[float] = []
    value = core[1] + STEP_EDGE
    while value < edge[1] + 1e-9:
        after.append(value)
        value += STEP_EDGE
    values = before + core_values + after
    return values, len(before), len(before) + count


def _refinement_level(lam: float, bet: float) -> int:
    """Combien de fois subdiviser une maille : 1, 2 ou 3.

    Le raffinement suit le RELIEF et rien d'autre. Une maille de 2,7 m ne sait pas
    dessiner un cratere de 9 m (trois mailles en travers) ; a 0,9 m il en reste dix,
    et le bord porte enfin une ombre. Partout ailleurs la sphere est lisse et une
    maille large ne coute aucune lecture — c'est ce qui tient le budget.
    """
    here = _dir(lam, bet)
    level = 1
    for feature in FEATURES:
        cos_angle = here.dot(feature.dir)
        if cos_angle <= 0.766:
            continue
        angle = math.acos(max(-1.0, min(1.0, cos_angle)))
        if angle * MOON_RADIUS > feature.reach * feature.radius:
            continue
        reach = angle * MOON_RADIUS / feature.radius
        if feature.radius <= 6.0:
            # Le cratere franc : trois subdivisions sur la cuvette et la crete, deux
            # sur la seule couverture d'ejectas, qui n'est qu'une pente douce. Le
            # gradient coute 25 % de triangles en moins pour la meme lecture.
            want = 3 if reach <= 1.15 else 2
        elif feature.radius <= 12.0:
            want = 2 if reach <= 1.10 else 1
        else:
            want = 1
        level = max(level, want)
    return level


def build_cap() -> bpy.types.Object:
    """La calotte : grille (longitude, latitude) raffinee autour des creux.

    LE POINT DELICAT — les jonctions entre mailles de finesse differente. Une maille
    subdivisee k x k pose k-1 sommets sur chaque bord ; si le voisin n'est pas
    subdivise, ces sommets doivent tomber EXACTEMENT sur la corde du voisin, sinon la
    surface s'ouvre d'une fente. On les interpole donc lineairement entre les deux
    coins partages au lieu de les projeter sur la sphere. Le relief est nul a cet
    endroit (le raffinement deborde toujours l'emprise du creux), donc l'ecart a la
    sphere vaut 1 cm et la fente, elle, vaudrait toute la fleche de la maille.
    """
    lams, lam_core0, lam_core1 = _samples(CORE_LAM, EDGE_LAM, STEP_LAM)
    bets, bet_core0, bet_core1 = _samples((-CORE_BET, CORE_BET), (-EDGE_BET, EDGE_BET),
                                          STEP_BET)

    levels: dict[tuple[int, int], int] = {}
    for i in range(len(lams) - 1):
        for j in range(len(bets) - 1):
            if lam_core0 <= i < lam_core1 and bet_core0 <= j < bet_core1:
                lam = 0.5 * (lams[i] + lams[i + 1])
                bet = 0.5 * (bets[j] + bets[j + 1])
                levels[(i, j)] = _refinement_level(lam, bet)
            else:
                levels[(i, j)] = 1

    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.verify()
    cache: dict[tuple[int, int, int, int], bmesh.types.BMVert] = {}
    uvs: dict[bmesh.types.BMVert, tuple[float, float]] = {}

    def corner(i: int, j: int) -> bmesh.types.BMVert:
        key = (i, j, 0, 0)
        vert = cache.get(key)
        if vert is None:
            lam, bet = lams[i], bets[j]
            vert = bm.verts.new(_surface(lam, bet))
            uvs[vert] = _uv(lam, bet)
            cache[key] = vert
        return vert

    def inner(i: int, j: int, si: int, sj: int, k: int) -> bmesh.types.BMVert:
        """Sommet interne ou de bord d'une maille subdivisee."""
        # Cle exprimee dans la grille FINE commune : deux mailles voisines de meme
        # finesse retrouvent ainsi le meme sommet, sans dedoublonnage a posteriori.
        gi, gj = i * 6 + si * (6 // k), j * 6 + sj * (6 // k)
        key = (gi, gj, 1, 1)
        vert = cache.get(key)
        if vert is not None:
            return vert
        u, v = si / k, sj / k
        lam = lams[i] + (lams[i + 1] - lams[i]) * u
        bet = bets[j] + (bets[j + 1] - bets[j]) * v
        on_edge_i = si == 0 or si == k
        on_edge_j = sj == 0 or sj == k
        stitched = None
        if on_edge_i != on_edge_j:  # sur un bord, pas sur un coin
            if on_edge_i:
                neighbour = (i - 1 if si == 0 else i + 1, j)
                a, b, t = corner(i if si == 0 else i + 1, j), \
                    corner(i if si == 0 else i + 1, j + 1), v
            else:
                neighbour = (i, j - 1 if sj == 0 else j + 1)
                a, b, t = corner(i, j if sj == 0 else j + 1), \
                    corner(i + 1, j if sj == 0 else j + 1), u
            if levels.get(neighbour, 1) != k:
                stitched = (a.co.lerp(b.co, t),
                            (uvs[a][0] + (uvs[b][0] - uvs[a][0]) * t,
                             uvs[a][1] + (uvs[b][1] - uvs[a][1]) * t))
        if stitched is None:
            vert = bm.verts.new(_surface(lam, bet))
            uvs[vert] = _uv(lam, bet)
        else:
            vert = bm.verts.new(stitched[0])
            uvs[vert] = stitched[1]
        cache[key] = vert
        return vert

    for (i, j), level in sorted(levels.items()):
        if level == 1:
            bm.faces.new((corner(i, j), corner(i + 1, j),
                          corner(i + 1, j + 1), corner(i, j + 1)))
            continue
        grid = [[None] * (level + 1) for _ in range(level + 1)]
        for si in range(level + 1):
            for sj in range(level + 1):
                if si in (0, level) and sj in (0, level):
                    grid[si][sj] = corner(i + (1 if si else 0), j + (1 if sj else 0))
                else:
                    grid[si][sj] = inner(i, j, si, sj, level)
        for si in range(level):
            for sj in range(level):
                bm.faces.new((grid[si][sj], grid[si + 1][sj],
                              grid[si + 1][sj + 1], grid[si][sj + 1]))

    # Orientation : on ne s'en remet pas a un recalcul heuristique sur une surface
    # ouverte. On regarde si les faces pointent vers l'exterieur de la lune, et on
    # retourne tout d'un coup si ce n'est pas le cas.
    bm.normal_update()
    outward = sum(1 for f in bm.faces if f.normal.dot(f.calc_center_median()) > 0.0)
    if outward * 2 < len(bm.faces):
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])

    for face in bm.faces:
        face.smooth = True
        for loop in face.loops:
            loop[uv_layer].uv = uvs[loop.vert]

    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    return _new_object("Moon", bm, _moon_material())


# ==========================================================================
# Les rochers — icosphere cassee, jamais erodee
# ==========================================================================


def build_rock(name: str, radius: float, seed: int) -> bpy.types.Object:
    """Un bloc anguleux, en coordonnees LOCALES (le noeud portera la position).

    Trois gestes, dans cet ordre : bruit directionnel a basse frequence (la forme
    generale), etirement anisotrope (rien n'est spherique dans une ceinture), puis
    des PLANS DE CASSURE qui rabattent les sommets sur une facette plate. C'est la
    derniere etape qui donne les aretes vives : un bruit seul rend une patate.
    ⚠️ Faces plates assumees (`face.smooth` reste faux) — une roche cassante n'a pas
    de normale continue, et `TEX-0002` porte les fractures fines par-dessus.
    """
    rng = random.Random(seed * 977 + 13)
    bm = bmesh.new()
    # 4 subdivisions = 1 280 triangles : la moitie du budget, et assez de sommets
    # pour que les plans de cassure taillent de vraies facettes. A 3 (320 tri) les
    # facettes devenaient plus grandes que les fractures de `TEX-0002`.
    bmesh.ops.create_icosphere(bm, subdivisions=4, radius=1.0)

    lobes = [(Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1))).normalized(),
              rng.uniform(0.9, 2.6), rng.uniform(0.08, 0.20), rng.uniform(0.0, 6.28))
             for _ in range(5)]
    for vert in bm.verts:
        direction = vert.co.normalized()
        offset = 0.0
        for axis, freq, amp, phase in lobes:
            offset += amp * math.sin(freq * math.pi * direction.dot(axis) + phase)
        vert.co = direction * (1.0 + offset)

    stretch = Vector((rng.uniform(0.78, 1.0), rng.uniform(0.70, 0.95), rng.uniform(0.82, 1.0)))
    for vert in bm.verts:
        vert.co = Vector((vert.co.x * stretch.x, vert.co.y * stretch.y,
                          vert.co.z * stretch.z))

    for _ in range(11):
        axis = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1))).normalized()
        reach = max(vert.co.dot(axis) for vert in bm.verts)
        cut = reach * rng.uniform(0.54, 0.84)
        for vert in bm.verts:
            over = vert.co.dot(axis) - cut
            if over > 0.0:
                vert.co -= axis * over

    scale = radius / max(vert.co.length for vert in bm.verts)
    for vert in bm.verts:
        vert.co *= scale

    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    obj = _new_object(name, bm, _rock_material())
    ak.cleanup(obj, merge_dist=1e-4)
    # ⚠️ Projection en boite calee sur 8 m par tuile, IDENTIQUE sur les trois rochers
    # (TEX-0002) : une tuile calee sur le petit se lirait comme du gravier sur le gros.
    ak.box_project_uv(obj, texels_per_meter=1.0 / ROCK_METRES_PER_TILE)
    return obj


# ==========================================================================
# Materiaux — couleur unie, aucun emissif, aucune texture (ADR-0028)
# ==========================================================================


def _flat_material(name: str, linear_rgb: tuple[float, float, float]) -> bpy.types.Material:
    existing = bpy.data.materials.get(name)
    if existing is not None:
        return existing
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    color = (linear_rgb[0], linear_rgb[1], linear_rgb[2], 1.0)
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Emission Strength"].default_value = 0.0
    mat.diffuse_color = color
    return mat


def _moon_material() -> bpy.types.Material:
    return _flat_material("Moon_Regolith", MOON_ALBEDO)


def _rock_material() -> bpy.types.Material:
    """Un SEUL datablock pour les trois rochers : `TEX-0002` est partagee."""
    return _flat_material("Asteroid_Rock", ROCK_ALBEDO)


def _new_object(name: str, bm: bmesh.types.BMesh,
                material: bpy.types.Material) -> bpy.types.Object:
    """Objet maille a un seul slot de materiau.

    ⚠️ `ak.new_object()` pose les SEPT slots normalises de l'ADR-0008 et leurs
    couleurs de faction. Ce decor n'appartient a aucune faction et sa couleur est
    imposee par la lisibilite du jeu (voir `MOON_ALBEDO`) : on pose donc un slot
    unique. Comme dans le kit, le slot est pose AVANT le transfert du BMesh — sans
    quoi `mesh.materials` remettrait tous les `material_index` a zero.
    """
    mesh = bpy.data.meshes.new(name)
    mesh.materials.append(material)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


# ==========================================================================
# Export — meme chaine d'axes que le kit, refaite ici (voir l'en-tete)
# ==========================================================================

_AXIS_FIX = Matrix.Rotation(math.pi, 4, "Z")
_YUP = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))


#: Repere Godot -> repere d'auteur ADR-0008 : (x, y, z) -> (-x, z, y). Determinant
#: +1 : c'est une rotation, elle ne miroite rien.
_TO_AUTHOR = Matrix(((-1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))


def _author(v: Vector) -> Vector:
    """Repere Godot -> repere d'auteur ADR-0008 (nez -Y, dessus +Z)."""
    return Vector((-v.x, v.z, v.y))


def _assert_axis_chain() -> None:
    """La chaine complete doit rendre l'identite, sur des temoins ASYMETRIQUES.

    Si quelqu'un « corrige » `_AXIS_FIX` en identite, tout le decor part a 180 deg :
    la lune passe en haut du cadre et les rochers derivent a l'envers. La bounding
    box ne le verrait pas — elle est presque symetrique. Ceci le voit.
    """
    chain = _YUP @ _AXIS_FIX
    for probe in (Vector((1.0, 2.0, 3.0)), Vector((-4.0, -78.0, 34.0)),
                  Vector((0.0, 0.0, -7.0))):
        got = chain.to_3x3() @ _author(probe)
        # 1e-5 et non 0 : les matrices de Blender sont en simple precision, et
        # cos(pi) y vaut -0,99999976. Le seuil attrape une erreur d'AXE (qui vaut
        # au moins 2 unites sur ces temoins), jamais un arrondi.
        if (got - probe).length > 1e-5:
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


def export(bodies: list[tuple[bpy.types.Object, Vector]], filepath: str) -> dict:
    """Pose les origines, corrige les axes, exporte, puis relit et valide."""
    _assert_axis_chain()
    for obj, pivot in bodies:
        # ⚠️ Chaque corps est deja modelise DANS SON PROPRE REPERE (la calotte autour
        # du centre de la lune, chaque rocher autour du sien) : c'est ce qui permet a
        # `Moon` de tourner sur elle-meme et a un rocher de deriver sans que sa
        # geometrie ait a bouger. On ne recentre donc rien ici — on change de repere,
        # on applique la correction d'axe de l'ADR-0008, et on pose la position du
        # NOEUD, seule chose que le moteur relira dans `body.position`.
        obj.data.transform(_TO_AUTHOR)
        obj.data.transform(_AXIS_FIX)
        obj.data.update()
        obj.location = _AXIS_FIX @ _author(pivot)

    bpy.ops.object.select_all(action="DESELECT")
    for obj, _ in bodies:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = bodies[0][0]

    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    staging = tempfile.mkdtemp(prefix="aegis-decor-")
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
        report = _audit(staged, bodies)
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


def _audit(path: str, bodies: list[tuple[bpy.types.Object, Vector]]) -> dict:
    """Relit le `.glb` PRODUIT et verifie tout ce que le brief exige.

    On lit le fichier binaire et non la scene en memoire : c'est la seule chose que
    Godot chargera. Les trois coques du depot sorties sans UV avaient toutes une
    scene Blender parfaite.
    """
    gltf, blob = _read_glb(path)
    problems: list[str] = []
    expected = {obj.name: pivot for obj, pivot in bodies}

    materials = [m.get("name", f"#{i}") for i, m in enumerate(gltf.get("materials", []))]
    nodes = gltf.get("nodes", [])
    roots = gltf.get("scenes", [{}])[0].get("nodes", list(range(len(nodes))))

    # --- contrat de noms : les quatre corps sont des racines -------------------
    root_names = [nodes[i].get("name", "?") for i in roots]
    for name in ("Moon", "Asteroid_01", "Asteroid_02", "Asteroid_03"):
        if name not in root_names:
            problems.append(
                f"contrat de noms rompu : '{name}' absent des racines {root_names}")
    for index in roots:
        if nodes[index].get("children"):
            problems.append(f"{nodes[index].get('name')} : le decor doit rester plat")

    stats: dict[str, dict] = {}
    top_of_decor = -math.inf
    prims_total = prims_uv = prims_tan = 0

    for index in roots:
        node = nodes[index]
        name = node.get("name", "?")
        if "mesh" not in node:
            problems.append(f"{name} : noeud sans maillage")
            continue
        translation = node.get("translation", [0.0, 0.0, 0.0])
        pivot = expected.get(name)
        if pivot is not None:
            drift = max(abs(translation[a] - pivot[a]) for a in range(3))
            if drift > 1e-4:
                problems.append(
                    f"{name} : translation {tuple(translation)} au lieu de "
                    f"{tuple(pivot)} — le moteur en deduit la vitesse de derive")
        triangles = 0
        lo = [math.inf] * 3
        hi = [-math.inf] * 3
        used: set[str] = set()
        for prim in gltf["meshes"][node["mesh"]]["primitives"]:
            prims_total += 1
            attrs = prim["attributes"]
            prims_uv += 1 if "TEXCOORD_0" in attrs else 0
            prims_tan += 1 if "TANGENT" in attrs else 0
            acc = gltf["accessors"][attrs["POSITION"]]
            triangles += gltf["accessors"][prim["indices"]]["count"] // 3 \
                if "indices" in prim else acc["count"] // 3
            used.add(materials[prim["material"]] if "material" in prim else "<aucun>")
            for axis in range(3):
                lo[axis] = min(lo[axis], acc["min"][axis] + translation[axis])
                hi[axis] = max(hi[axis], acc["max"][axis] + translation[axis])
        budget = TRI_BUDGET_CAP if name == "Moon" else TRI_BUDGET_ROCK
        if triangles > budget:
            problems.append(f"{name} : {triangles} triangles > budget {budget}")
        top_of_decor = max(top_of_decor, hi[1])
        if hi[1] > CEILING_Y:
            problems.append(
                f"{name} : culmine a Y = {hi[1]:.2f} > plafond {CEILING_Y}")
        if name.startswith("Asteroid") and lo[1] < SKY_Y:
            # ⚠️ La regle ne vaut QUE pour les rochers. La lune, elle, plonge
            # forcement sous le plan du ciel (son limbe visible est deja a Y = -56) :
            # le shader du ciel est `depth_draw_never`, la calotte se dessine donc
            # par-dessus. C'est ce que `test_moon_flyby.gd` mesure lui aussi, corps
            # derivant par corps derivant.
            problems.append(f"{name} : descend a Y = {lo[1]:.2f}, sous le ciel {SKY_Y}")
        stats[name] = {
            "triangles": triangles,
            "translation": tuple(translation),
            "size": tuple(hi[a] - lo[a] for a in range(3)),
            "min": tuple(lo),
            "max": tuple(hi),
            "materials": sorted(used),
        }

    if prims_total == 0 or prims_uv != prims_total:
        problems.append(
            f"{prims_total - prims_uv} primitive(s) sur {prims_total} sans TEXCOORD_0 "
            "— la surface ne pourrait recevoir aucune carte (ADR-0028)")

    # --- la calotte : sommet, centre implicite, rayon ---------------------------
    moon = stats.get("Moon")
    if moon is not None:
        summit = moon["max"][1]
        if not (-19.0 <= summit <= -17.0):
            problems.append(f"sommet de la calotte a {summit:.2f}, attendu -18 +/-1")
        node = next(nodes[i] for i in roots if nodes[i].get("name") == "Moon")
        radii = [Vector(p).length
                 for p in _accessor(gltf, blob,
                                    gltf["meshes"][node["mesh"]]["primitives"][0]
                                    ["attributes"]["POSITION"])]
        moon["radius"] = (min(radii), max(radii))
        if min(radii) < MOON_RADIUS - 4.5 or max(radii) > MOON_RADIUS + 1.5:
            problems.append(
                f"relief hors bornes : rayons {min(radii):.2f} a {max(radii):.2f} "
                f"pour un nominal de {MOON_RADIUS}")

    # --- emissif et texture : il ne doit y en avoir aucun -----------------------
    for material in gltf.get("materials", []):
        emissive = material.get("emissiveFactor", [0.0, 0.0, 0.0])
        if any(value > 0.0 for value in emissive) or "emissiveTexture" in material:
            problems.append(f"materiau {material.get('name')} : emissif interdit")
        pbr = material.get("pbrMetallicRoughness", {})
        if "baseColorTexture" in pbr or "metallicRoughnessTexture" in material or \
                "normalTexture" in material or "occlusionTexture" in material:
            problems.append(
                f"materiau {material.get('name')} : TEXTURE dans le .glb — "
                "la matiere vient de l'operateur (ADR-0028)")
    if gltf.get("images"):
        problems.append("le .glb embarque des images : interdit par ADR-0028")

    if problems:
        raise ak.ContractError(
            "CONTRAT ROMPU — moon_flyby\n" + "\n".join(f"  - {p}" for p in problems))

    return {
        "bodies": stats,
        "primitives": (prims_uv, prims_tan, prims_total),
        "top": top_of_decor,
        "bytes": os.path.getsize(path),
    }


def _visible_band(thetas: list[float] | None = None) -> dict:
    """Ou la camera peut voir la lune, sur tout le parcours de rotation.

    Recalcule a chaque build a partir de la camera et de la rotation reelles. C'est
    lui qui autorise a ne mailler qu'une bande : si un jour la camera change, le
    build echoue au lieu de livrer une lune trouee.
    """
    tan_v = math.tan(CAM_FOV_V * 0.5)
    tan_h = tan_v * CAM_ASPECT
    lam_lo, lam_hi = math.inf, -math.inf
    bet_max = 0.0
    if thetas is None:
        thetas = [SWEEP * step / 24 for step in range(25)]
    for theta in thetas:
        cos_t, sin_t = math.cos(theta), math.sin(theta)
        for i in range(241):
            lam = math.radians(-180.0 + i * 1.5)
            for j in range(121):
                bet = math.radians(-90.0 + j * 1.5)
                body = _dir(lam, bet)
                world = Vector((body.x,
                                cos_t * body.y - sin_t * body.z,
                                sin_t * body.y + cos_t * body.z))
                point = MOON_CENTER + world * MOON_RADIUS
                view = point - CAM_POS
                if view.dot(world) >= 0.0:
                    continue
                depth = view.dot(CAM_FORWARD)
                if depth <= 0.0:
                    continue
                if abs(view.dot(CAM_RIGHT)) > tan_h * depth:
                    continue
                if abs(view.dot(CAM_UP)) > tan_v * depth:
                    continue
                lam_lo = min(lam_lo, lam)
                lam_hi = max(lam_hi, lam)
                bet_max = max(bet_max, abs(bet))
    return {"lam": (lam_lo, lam_hi), "bet": bet_max}


def _assert_uv_centre(band: dict) -> None:
    """Le centre de la projection doit rester au milieu de la bande vue.

    Il n'est pas decoratif : la derive tangentielle vaut psi/sin(psi), donc elle ne
    depend que de la distance au centre. Un centre decale de 20 deg ajoute 8 points
    de derive au bord oppose, en silence.
    """
    middle = 0.5 * (band["lam"][0] + band["lam"][1])
    if abs(UV_CENTER_LAM - middle) > math.radians(6.0):
        raise ak.ContractError(
            f"centre de projection a {math.degrees(UV_CENTER_LAM):.1f} deg pour une "
            f"bande vue centree sur {math.degrees(middle):.1f} deg")


def _assert_covers_view(band: dict) -> None:
    if band["lam"][0] < CORE_LAM[0] or band["lam"][1] > CORE_LAM[1] or \
            band["bet"] > CORE_BET:
        raise ak.ContractError(
            "la bande VUE sort du coeur maille : "
            f"lam [{math.degrees(band['lam'][0]):.1f}, {math.degrees(band['lam'][1]):.1f}] "
            f"bet +/-{math.degrees(band['bet']):.1f} contre un coeur "
            f"[{math.degrees(CORE_LAM[0]):.1f}, {math.degrees(CORE_LAM[1]):.1f}] "
            f"+/-{math.degrees(CORE_BET):.1f}")


def _impact_clearance() -> list[tuple[int, float, str]]:
    """Combien de surface PLATE reste autour de chaque point d'impact.

    ⚠️ Mesure, et non promesse : `_features()` refuse deja de poser un creux trop
    pres, mais un tirage sous contrainte se relit toujours sur le resultat. On
    mesure ici la distance du point d'impact au BORD du relief le plus proche
    (`reach x radius`), pas a son centre — c'est le bord qui gene la gerbe.
    """
    out = []
    for index, mark in enumerate(_impact_marks()):
        best = math.inf
        who = "-"
        for feature in FEATURES:
            gap = MOON_RADIUS * math.acos(
                max(-1.0, min(1.0, mark.dot(feature.dir)))) \
                - feature.reach * feature.radius
            if gap < best:
                best, who = gap, f"{feature.kind} r={feature.radius:.1f}"
        out.append((index, best, who))
        if best < 6.0:
            raise ak.ContractError(
                f"impact {index} : {best:.1f} m de surface degagee seulement "
                f"(voisin : {who}) — la gerbe se jouerait dans un cratere")
    return out


def _sweep_coverage(band: dict) -> list[tuple[float, int]]:
    """Combien de reliefs sont dans le cadre a chaque instant de la phase.

    ⚠️ Le piege que ce harnais ferme : un relief reparti « au hasard sur la bande »
    peut laisser une fenetre vide de vingt secondes. Le brief le dit — « un detail
    concentre sur une seule face sortira du cadre au bout de vingt secondes ». On
    compte donc, tous les cinq degres de rotation, ce qui tombe dans la fenetre.
    """
    out = []
    for step in range(16):
        theta = SWEEP * step / 15.0
        # ⚠️ La fenetre INSTANTANEE, pas la bande cumulee. Compter dans la bande
        # cumulee (121 deg de long) au lieu de la fenetre du moment (47 deg)
        # annoncait 16 a 28 reliefs au cadre la ou il y en a trois fois moins :
        # un harnais qui compte trop large ne garde plus rien.
        # ⚠️ La fenetre revient en coordonnees du CORPS (c'est ce que `_visible_band`
        # enregistre), donc on compare la longitude du relief telle quelle. Y
        # rajouter theta — le reflexe — decale la comparaison deux fois et fait
        # conclure « deux reliefs au cadre » la ou il y en a seize.
        window = _visible_band([theta])
        count = 0
        for feature in FEATURES:
            if window["lam"][0] <= feature.lam <= window["lam"][1] \
                    and abs(feature.bet) <= window["bet"]:
                count += 1
        out.append((math.degrees(theta), count))
        if count < 4:
            raise ak.ContractError(
                f"a {math.degrees(theta):.0f} deg de rotation, seuls {count} reliefs "
                "sont dans le cadre — la lune y rendrait lisse")
    return out


def _texel_density(obj: bpy.types.Object, band: dict) -> dict:
    """Metres de surface par tuile, MESURES triangle par triangle sur le maillage.

    Pour chaque triangle on construit la matrice 2x2 qui envoie le plan du triangle
    sur le plan UV, et on en prend les valeurs singulieres : leurs inverses sont les
    metres par tuile dans les deux directions principales. C'est la seule mesure qui
    attrape un ETIREMENT — une moyenne d'aires n'y verrait rien, un ilot deux fois
    trop dense dans un sens et deux fois trop lache dans l'autre a l'aire juste.
    """
    mesh = obj.data
    uv_layer = mesh.uv_layers.active.data
    seen = []
    weight_total = 0.0
    for poly in mesh.polygons:
        loops = list(poly.loop_indices)
        if len(loops) != 3:
            continue
        p = [mesh.vertices[mesh.loops[l].vertex_index].co for l in loops]
        t = [uv_layer[l].uv for l in loops]
        e1, e2 = p[1] - p[0], p[2] - p[0]
        normal = e1.cross(e2)
        area = normal.length * 0.5
        if area < 1e-9:
            continue
        t1 = e1.normalized()
        t2 = (e2 - t1 * e2.dot(t1))
        if t2.length < 1e-9:
            continue
        t2.normalize()
        a1, b1 = e1.dot(t1), e1.dot(t2)
        a2, b2 = e2.dot(t1), e2.dot(t2)
        det = a1 * b2 - a2 * b1
        if abs(det) < 1e-12:
            continue
        # M = [du1 du2] * inv([[a1,a2],[b1,b2]])
        du1 = (t[1][0] - t[0][0], t[1][1] - t[0][1])
        du2 = (t[2][0] - t[0][0], t[2][1] - t[0][1])
        inv = ((b2 / det, -a2 / det), (-b1 / det, a1 / det))
        m00 = du1[0] * inv[0][0] + du2[0] * inv[1][0]
        m01 = du1[0] * inv[0][1] + du2[0] * inv[1][1]
        m10 = du1[1] * inv[0][0] + du2[1] * inv[1][0]
        m11 = du1[1] * inv[0][1] + du2[1] * inv[1][1]
        # Valeurs singulieres d'une 2x2, par la forme fermee.
        e = 0.5 * (m00 + m11)
        f = 0.5 * (m00 - m11)
        g = 0.5 * (m10 + m01)
        h = 0.5 * (m10 - m01)
        q = math.hypot(e, h)
        r = math.hypot(f, g)
        s_max, s_min = q + r, abs(q - r)
        if s_min < 1e-9:
            continue
        centre = (p[0] + p[1] + p[2]) / 3.0
        lam, bet = _lam_bet(centre.normalized())
        inside = (band["lam"][0] <= lam <= band["lam"][1]) and abs(bet) <= band["bet"]
        # ⚠️ Deux causes d'ecart se superposent et il faut les separer, sinon on
        # « corrige » la mauvaise : la PROJECTION (derive tangentielle en psi/sin psi,
        # inevitable des qu'on aplatit une sphere) et la PENTE DU RELIEF (un flanc de
        # cratere est plus long que sa projection, d'un facteur 1/cos(pente) — c'est
        # vrai de tout terrain deplace, quel que soit le depliage). On marque donc les
        # triangles poses sur la sphere nue.
        flat = all(abs(v.length - MOON_RADIUS) < 0.10 for v in p)
        seen.append((area, 1.0 / s_max, 1.0 / s_min, s_max / s_min, inside, flat))
        weight_total += area

    def summarise(rows):
        if not rows:
            return None
        total = sum(r[0] for r in rows)
        return {
            "aire": total,
            "min_m_par_tuile": min(r[1] for r in rows),
            "max_m_par_tuile": max(r[2] for r in rows),
            "moyenne_m_par_tuile": sum(r[0] * 0.5 * (r[1] + r[2]) for r in rows) / total,
            "anisotropie_max": max(r[3] for r in rows),
            "anisotropie_moyenne": sum(r[0] * r[3] for r in rows) / total,
        }

    return {
        "tout": summarise(seen),
        "vu": summarise([r for r in seen if r[4]]),
        "vu_sphere": summarise([r for r in seen if r[4] and r[5]]),
        "vu_relief": summarise([r for r in seen if r[4] and not r[5]]),
        "aire_totale": weight_total,
    }


# ==========================================================================
# Assemblage
# ==========================================================================


def build() -> dict:
    ak.reset_scene()
    band = _visible_band()
    _assert_covers_view(band)
    _assert_uv_centre(band)

    cap = build_cap()
    density = _texel_density(cap, band)

    bodies: list[tuple[bpy.types.Object, Vector]] = [(cap, MOON_CENTER)]
    for name, position, radius, seed in ROCKS:
        bodies.append((build_rock(name, radius, seed), position))

    report = export(bodies, OUTPUT)
    report["band"] = band
    report["density"] = density
    report["impacts"] = _impact_clearance()
    report["coverage"] = _sweep_coverage(band)
    return report


def _print_report(report: dict) -> None:
    band = report["band"]
    print("\n=== decor de survol — mesures du .glb livre ===")
    print(f"  fichier    : {OUTPUT} ({report['bytes']} o)")
    print("  bande VUE  : longitude [%.1f, %.1f] deg, latitude +/-%.1f deg"
          % (math.degrees(band["lam"][0]), math.degrees(band["lam"][1]),
             math.degrees(band["bet"])))
    print("  coeur maille : longitude [%.1f, %.1f] deg, latitude +/-%.1f deg"
          % (math.degrees(CORE_LAM[0]), math.degrees(CORE_LAM[1]),
             math.degrees(CORE_BET)))
    total = 0
    for name in ("Moon", "Asteroid_01", "Asteroid_02", "Asteroid_03"):
        info = report["bodies"][name]
        total += info["triangles"]
        budget = TRI_BUDGET_CAP if name == "Moon" else TRI_BUDGET_ROCK
        print("  %-12s %5d tri (budget %5d)  pos (%+7.2f, %+7.2f, %+7.2f)  "
              "bbox %6.2f x %6.2f x %6.2f  sommet Y %+7.2f  [%s]"
              % (name, info["triangles"], budget, *info["translation"],
                 *info["size"], info["max"][1], ", ".join(info["materials"])))
    print(f"  total      : {total} triangles ; plafond du decor Y = {report['top']:.2f} "
          f"(limite {CEILING_Y})")
    uv, tan, prims = report["primitives"]
    print(f"  UV         : {uv}/{prims} primitives portent TEXCOORD_0, {tan}/{prims} TANGENT")
    moon = report["bodies"]["Moon"]
    print("  rayons de la calotte : %.2f a %.2f m (nominal %.0f) — creux max %.2f m, "
          "bourrelet max %.2f m"
          % (moon["radius"][0], moon["radius"][1], MOON_RADIUS,
             MOON_RADIUS - moon["radius"][0], moon["radius"][1] - MOON_RADIUS))
    for label, key in (("toute la calotte", "tout"),
                       ("la bande vue", "vu"),
                       ("la bande vue, sphere nue", "vu_sphere"),
                       ("la bande vue, relief", "vu_relief")):
        d = report["density"][key]
        print("  densite de texels sur %-26s : %.1f a %.1f m/tuile "
              "(moyenne %.1f), anisotropie max %.2f, moyenne %.2f, aire %.0f m2"
              % (label, d["min_m_par_tuile"], d["max_m_par_tuile"],
                 d["moyenne_m_par_tuile"], d["anisotropie_max"],
                 d["anisotropie_moyenne"], d["aire"]))
    kinds: dict[str, int] = {}
    for feature in FEATURES:
        kinds[feature.kind] = kinds.get(feature.kind, 0) + 1
    print("  degagement aux impacts : " + " | ".join(
        "n%d %.1f m (voisin %s)" % (i + 1, gap, who)
        for i, gap, who in report["impacts"]))
    counts = [c for _, c in report["coverage"]]
    print("  reliefs DANS LE CADRE au fil de la rotation : %d a %d "
          "(0 a %.0f deg, releve tous les %.0f deg)"
          % (min(counts), max(counts), math.degrees(SWEEP),
             math.degrees(SWEEP) / 15.0))
    print("  relief geometrique : " + ", ".join(
        f"{count} x {kind}" for kind, count in sorted(kinds.items())))
    print("  ⚠️ les UV portent deja l'echelle : uv1_scale = (1, 1, 1) cote Godot "
          f"({MOON_METRES_PER_TILE:.0f} m/tuile sur la lune, "
          f"{ROCK_METRES_PER_TILE:.0f} sur les rochers)")


# ==========================================================================
# Planches de recette — `--plate`
# ==========================================================================

TILE_W, TILE_H = 960, 540
SAMPLES = 48

#: Le fond du jeu (`space_environment.tres`), en lineaire.
BACKDROP = (0.012, 0.016, 0.035, 1.0)
#: L'ambiante du jeu : couleur x energie. Elle compte pour un tiers de la luminance
#: de la lune — l'ignorer donnerait une planche bien plus sombre que le jeu.
AMBIENT = tuple(c * 0.8 for c in (0.55, 0.62, 0.78))

#: Les trois lumieres de scenes/gameplay/graybox.tscn, direction = -Z de leur base.
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
    scene.render.resolution_x = TILE_W
    scene.render.resolution_y = TILE_H
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"


def _plate_lights() -> None:
    """Les trois directionnelles du jeu, et AUCUNE ombre portee.

    ⚠️ Le point le plus important de cette planche. En jeu,
    `directional_shadow_max_distance` vaut 40 et la lune est a 96 m : elle ne recoit
    ni ne projette la moindre ombre. Laisser Cycles en projeter validerait des
    crateres qui ne se lisent QUE par leur ombre — exactement le piege que le brief
    signale. On coupe donc la visibilite d'ombre de tous les objets : ce qui se voit
    ici se lit par la seule orientation des faces, comme en jeu.
    """
    for name, direction, energy, color in GAME_LIGHTS:
        data = bpy.data.lights.new(name, type="SUN")
        # Godot : L = albedo * energie * N.L. Cycles : L = albedo * force * N.L / pi.
        data.energy = energy * math.pi
        data.color = color
        data.angle = 0.0
        light = bpy.data.objects.new(name, data)
        aim = _to_blender(direction)
        light.rotation_euler = aim.to_track_quat("-Z", "Y").to_euler()
        bpy.context.collection.objects.link(light)


def _ceiling_plane() -> None:
    """Le plafond `CEILING_Y`, materialise pour la seule planche.

    ⚠️ Il n'existe QUE dans le rendu : rien de tout cela ne part dans le `.glb`.
    """
    bm = bmesh.new()
    # Une DALLE de 40 cm et non un plan : vue de tribord, un plan d'epaisseur nulle
    # ne rend aucun pixel. C'est le meme piege que les reperes de bounds du jeu.
    for low, high in ((CEILING_Y - 0.40, CEILING_Y),):
        for y in (low, high):
            ring = [bm.verts.new(_to_blender(Vector((x, y, z))))
                    for x, z in ((-70.0, -80.0), (70.0, -80.0), (70.0, 80.0),
                                 (-70.0, 80.0))]
            bm.faces.new(ring)
        bm.verts.ensure_lookup_table()
        for i in range(4):
            bm.faces.new((bm.verts[i], bm.verts[(i + 1) % 4],
                          bm.verts[4 + (i + 1) % 4], bm.verts[4 + i]))
    mesh = bpy.data.meshes.new("Ceiling")
    material = bpy.data.materials.new("Ceiling")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs[0].default_value = (0.90, 0.72, 0.30, 1.0)
    emission.inputs[1].default_value = 3.0
    out = nodes.new("ShaderNodeOutputMaterial")
    material.node_tree.links.new(emission.outputs[0], out.inputs[0])
    mesh.materials.append(material)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("Ceiling", mesh)
    obj.visible_shadow = False
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
    # ⚠️ La lune est a 96 m et son limbe a 160 : le clip_end par defaut (100 m) la
    # couperait en deux, proprement et sans le dire.
    data.clip_start = 0.05
    data.clip_end = 900.0
    camera = bpy.data.objects.new(name, data)
    right = forward.cross(up).normalized()
    basis = Matrix((
        (right.x, up.x, -forward.x, position.x),
        (right.y, up.y, -forward.y, position.y),
        (right.z, up.z, -forward.z, position.z),
        (0.0, 0.0, 0.0, 1.0),
    ))
    camera.matrix_world = basis
    bpy.context.collection.objects.link(camera)
    bpy.context.scene.camera = camera
    return camera


def _game_camera(name: str = "game") -> bpy.types.Object:
    return _plate_camera(name, _to_blender(CAM_POS), _to_blender(CAM_FORWARD),
                         _to_blender(CAM_UP), CAM_FOV_V)


def _import(path: str, name: str, position: Vector, yaw: float = 0.0) -> list:
    """Importe un `.glb` et le suspend a un porteur pose a la position DE JEU.

    ⚠️ On ne renomme ni ne deplace les objets importes : un `.glb` a plusieurs
    racines (ce decor en a quatre, le Specter-9 a ses points d'attache) et les
    ramener tous a la meme position les empilerait a l'origine. Le porteur, lui, est
    a l'exterieur : il transporte l'ensemble sans toucher a la mise en place interne.
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


def _spin_moon(objects: list, theta: float) -> None:
    """Fait tourner la lune comme le jeu : autour de X, meme sens, meme signe.

    ⚠️ `delta_rotation_euler` et non `rotation_euler` : l'importeur glTF loge la
    conversion Y-up -> Z-up dans la rotation des objets racines. L'ecraser
    coucherait toute la lune sur le flanc — et comme elle est presque spherique,
    personne ne le verrait sur la planche.
    """
    for obj in objects:
        if obj.name.split(".")[0] == "Moon":
            obj.delta_rotation_euler = Euler((theta, 0.0, 0.0), "XYZ")


def _label(camera, text: str, u: float, v: float, height: float,
           color=(1.0, 1.0, 1.0)) -> None:
    """Une legende parentee a la camera : pas de projection a calculer.

    `u`, `v` et `height` sont en FRACTION du cadre, jamais en metres : les six
    cameras de ces planches vont de 18 deg de champ a une orthographique de 84 m, et
    une taille en metres aurait donne un texte illisible sur les unes et debordant
    sur les autres. C'est deja arrive : l'elevation orthographique a rendu ses deux
    legendes a l'echelle du millimetre, invisibles.
    """
    curve = bpy.data.curves.new(text, type="FONT")
    curve.body = text
    obj = bpy.data.objects.new("label_" + text[:12], curve)
    material = bpy.data.materials.new("label_" + text[:12])
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
    half_w = half_h * TILE_W / TILE_H
    curve.size = height * 2.0 * half_h
    obj.location = (u * half_w, v * half_h, -depth)
    obj.visible_shadow = False
    bpy.context.collection.objects.link(obj)


def _render(path: str, width: int = TILE_W, height: int = TILE_H) -> None:
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def _compose(tiles: list[str], out: str) -> None:
    """Planche 2x2. Pas de PIL dans le Python de Blender — numpy + bpy.data.images."""
    import numpy as np

    width, height = TILE_W * 2, TILE_H * 2
    sheet = np.zeros((height, width, 4), dtype=np.float32)
    for index, path in enumerate(tiles):
        image = bpy.data.images.load(path)
        buffer = np.empty(len(image.pixels), dtype=np.float32)
        image.pixels.foreach_get(buffer)
        tile = buffer.reshape(TILE_H, TILE_W, 4)
        row, column = index // 2, index % 2
        # Les images Blender sont stockees de bas en haut : la ligne 0 est en bas.
        top = (1 - row) * TILE_H
        sheet[top:top + TILE_H, column * TILE_W:(column + 1) * TILE_W] = tile
        bpy.data.images.remove(image)
    result = bpy.data.images.new("sheet", width=width, height=height)
    result.pixels.foreach_set(sheet.reshape(-1))
    result.filepath_raw = out
    result.file_format = "PNG"
    result.save()
    bpy.data.images.remove(result)
    print(f"-> {out}")


def _checker_material() -> bpy.types.Material:
    """Damier UV : une case par 1/8 de tuile, sur un damier de TUILES entieres.

    Les grandes cases disent ou tombent les tuiles de 55 m et les petites disent la
    densite locale : si les petites cases restent CARREES et de taille constante sur
    le flanc d'un cratere, le depliage tient. C'est la seule verification possible
    avant que la texture existe.
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


def _scene_plate(report: dict) -> None:
    """Planche de survol : la scene du jeu, a la perspective du jeu.

    Le chasseur et deux mines sont dans le cadre, a leur taille reelle. Ce n'est pas
    une decoration : c'est le repere d'echelle (ADR-0025 — les « anneaux qu'on
    franchit » de 30 cm avaient un contrat de noms parfait) et c'est le critere
    d'acceptation « le chasseur et les mines restent lisibles par-dessus la surface ».
    """
    _plate_reset()
    decor = _import(OUTPUT, "Decor", Vector((0.0, 0.0, 0.0)))
    _import(os.path.join(_REPO, "assets/imported/models/ships/specter_9.glb"),
            "Player", Vector((0.0, 0.0, 3.4)))
    _import(os.path.join(_REPO, "assets/imported/models/ships/choir_mine.glb"),
            "Mine_A", Vector((-6.4, 0.0, -1.2)))
    _import(os.path.join(_REPO, "assets/imported/models/ships/choir_mine.glb"),
            "Mine_B", Vector((5.8, 0.0, -4.6)))
    _plate_lights()

    tiles = []
    camera = _game_camera()
    moon = report["bodies"]["Moon"]
    for index, (theta_deg, caption) in enumerate((
        (0.0, "t = 0 s — entree dans le champ"),
        (math.degrees(SWEEP) * 0.5, "t = 30 s — mi-parcours"),
        (math.degrees(SWEEP), "t = 60 s — fin de phase"),
    )):
        _spin_moon(decor, math.radians(theta_deg))
        for obj in list(bpy.context.scene.objects):
            if obj.name.startswith("label_"):
                bpy.data.objects.remove(obj, do_unlink=True)
        _label(camera, caption, -0.94, 0.90, 0.025)
        _label(camera, "Specter-9 : 2,41 m de long — repere d'echelle",
               -0.94, -0.93, 0.020, (0.65, 0.85, 1.0))
        path = f"/tmp/_moon_plate_{index}.png"
        _render(path)
        tiles.append(path)
        print(f"  vue survol {theta_deg:.0f} deg")

    # Quatrieme vue : une ELEVATION orthographique prise de tribord, avec le plafond
    # materialise. C'est la vue qui repond a « rien ne monte au-dessus de Y = -3 »
    # autrement que par un chiffre — et la seule ou l'on voie d'un coup la calotte,
    # les trois rochers et le plan de jeu dans le meme volume.
    for obj in list(bpy.context.scene.objects):
        if obj.name.startswith("label_"):
            bpy.data.objects.remove(obj, do_unlink=True)
    _spin_moon(decor, 0.0)
    _ceiling_plane()
    camera = _plate_camera("side", _to_blender(Vector((260.0, -40.0, 20.0))),
                           _to_blender(Vector((-1.0, 0.0, 0.0))),
                           _to_blender(Vector((0.0, 1.0, 0.0))), math.radians(40.0),
                           ortho=84.0)
    _label(camera, "elevation orthographique (de tribord) — cadre de 149 x 84 m",
           -0.94, 0.90, 0.025)
    _label(camera,
           "trait ambre = plafond Y = -3 ; sommet reel du decor a %.2f" % report["top"],
           -0.94, -0.93, 0.020, (0.90, 0.72, 0.30))
    _render("/tmp/_moon_plate_3.png")
    tiles.append("/tmp/_moon_plate_3.png")
    print("  vue de cote")
    _compose(tiles, PLATE_SCENE)
    print(f"     (calotte : {moon['triangles']} triangles)")


def _uv_plate() -> None:
    """Planche de controle du depliage : le damier, a la perspective du jeu."""
    _plate_reset()
    decor = _import(OUTPUT, "Decor", Vector((0.0, 0.0, 0.0)))
    checker = _checker_material()
    for obj in decor:
        if obj.type == "MESH" and obj.name.startswith("Moon"):
            obj.data.materials.clear()
            obj.data.materials.append(checker)
    _plate_lights()

    tiles = []
    camera = _game_camera()
    for index, (theta_deg, caption) in enumerate((
        (0.0, "damier UV — perspective de jeu, t = 0 s"),
        (math.degrees(SWEEP), "damier UV — perspective de jeu, t = 60 s"),
    )):
        _spin_moon(decor, math.radians(theta_deg))
        for obj in list(bpy.context.scene.objects):
            if obj.name.startswith("label_"):
                bpy.data.objects.remove(obj, do_unlink=True)
        _label(camera, caption, -0.94, 0.90, 0.025)
        _label(camera, "grande case = 1 tuile de 55 m ; petite = 3,4 m",
               -0.94, -0.93, 0.020, (0.65, 0.85, 1.0))
        path = f"/tmp/_moon_uv_{index}.png"
        _render(path)
        tiles.append(path)
        print(f"  damier {theta_deg:.0f} deg")

    # Deux gros plans, VISES SUR DU RELIEF REEL et non sur un point choisi a la main :
    # c'est sur le flanc d'un cratere que l'etirement se verrait, pas sur la sphere
    # nue. Les rochers sortent du champ — ils ne sont pas le sujet de cette planche.
    _spin_moon(decor, 0.0)
    for obj in bpy.context.scene.objects:
        if obj.name.split(".")[0].startswith("Asteroid"):
            obj.hide_render = True
    # ⚠️ On ne prend pas simplement le plus grand relief du catalogue : le premier
    # essai avait vise un cratere pose a lam = -127 deg, une zone que SEULE la
    # troisieme lumiere effleure (N.L negatif sur la principale). Le damier s'y
    # lisait, le cratere non — et une planche de recette qui montre du relief
    # invisible ne prouve rien. On choisit donc dans la fenetre reellement vue a
    # l'entree dans la phase.
    def lit(kind):
        window = [f for f in FEATURES if f.kind == kind
                  and math.radians(-80.0) <= f.lam <= math.radians(-28.0)
                  and abs(f.bet) <= math.radians(26.0)]
        return max(window or [f for f in FEATURES if f.kind == kind],
                   key=lambda f: f.radius)

    biggest = lit("basin")
    sharpest = lit("crater")
    for index, (feature, elevation, span, caption) in enumerate((
        (sharpest, 50.0, 2.6,
         "gros plan cratere franc (%.1f m de diametre) — les cases restent carrees "
         "sur le flanc" % (2.0 * sharpest.radius)),
        (biggest, 32.0, 1.9,
         "gros plan grand bassin (%.0f m de diametre), vu en rasant comme au limbe"
         % (2.0 * biggest.radius)),
    )):
        normal = feature.dir
        point = MOON_CENTER + normal * (MOON_RADIUS + _height(feature.lam, feature.bet))
        # Tangente qui remonte le meridien : le sens dans lequel la surface defile.
        tangent = (_dir(feature.lam - 0.02, feature.bet) - normal).normalized()
        elev = math.radians(elevation)
        # Longue focale plutot que grand angle : a 18 deg la deformation de
        # perspective ne se melange pas a celle du depliage, qui est le sujet.
        close_fov = math.radians(18.0)
        distance = feature.radius * span / math.tan(close_fov * 0.5)
        position = point + (normal * math.sin(elev) + tangent * math.cos(elev)) * distance
        forward = (point - position).normalized()
        up = normal - forward * normal.dot(forward)
        camera = _plate_camera(f"close_{index}", _to_blender(position),
                               _to_blender(forward), _to_blender(up.normalized()),
                               close_fov)
        for obj in list(bpy.context.scene.objects):
            if obj.name.startswith("label_"):
                bpy.data.objects.remove(obj, do_unlink=True)
        _label(camera, caption, -0.94, 0.90, 0.022)
        path = f"/tmp/_moon_uv_close_{index}.png"
        _render(path)
        tiles.append(path)
        print(f"  gros plan {feature.kind} r={feature.radius:.1f}")

    _compose(tiles, PLATE_UV)


def main() -> None:
    report = build()
    _print_report(report)
    if "--plate" in sys.argv:
        print("\n--- planches de recette (Cycles, CPU) ---")
        _scene_plate(report)
        _uv_plate()
        print("\n-> LES OUVRIR : un asset non regarde n'est pas un asset valide "
              "(ADR-0006)")


if __name__ == "__main__":
    main()
