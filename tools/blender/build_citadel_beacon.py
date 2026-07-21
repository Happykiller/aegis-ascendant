"""build_citadel_beacon.py — balise flottante de l'Aegis Citadel (BRIEF-0032).

    blender45 -b -P tools/blender/build_citadel_beacon.py

Produit `assets/imported/models/structures/citadel_beacon.glb`.

Le script EST la source de l'asset (ADR-0008) : aucun `.blend` n'est versionne.
Deterministe, auto-valide par `ak.export_hull()`.

Reference de design : `assets/reference/concepts/aegis_citadel_concept_sheet.png`.
La planche en montre TROIS, tenues dans un champ hexagonal cyan : une au-dessus
de la proue, deux en retrait de part et d'autre de la poupe. Chacune est une
petite nacelle ivoire facettee, cerclee d'un anneau, avec un oeil cyan tourne
vers l'avant. Le champ hexagonal lui-meme n'est PAS de la geometrie : c'est un
effet, il se fait cote Godot (shader/particules).

CONTRAT D'ANIMATION :
  * **l'origine est au centre de la nacelle** et coincide avec les marqueurs
    `Beacon_01..03` de la coque, qui sont sa position de REPOS. L'animation la
    fait deriver autour de ce point (l'ordre de grandeur prevu cote Godot est
    +/-0,55 m en orbite et +/-0,30 m en vertical) ;
  * l'oeil regarde vers **-Y** (repere d'auteur), donc vers **-Z** cote Godot,
    comme le nez de toutes les unites.

⚠️ LIMITE CONNUE — l'anneau n'est pas une piece separee. Le kit
(`ak.export_hull`) n'exporte QU'UN objet maille : tout est fusionne par
`join_objects()`. L'anneau est donc dans le meme maillage que la nacelle, et
Godot ne peut pas le faire tourner independamment. Le brief prevoyait ce cas :
on livre le marqueur **`Ring_Center`** (centre de l'anneau) et, en plus,
**`Ring_Axis`** — les deux definissent l'axe de rotation de l'anneau, ce qu'un
seul point ne saurait faire. Voir le compte-rendu BRIEF-0032 §limites.
"""

from __future__ import annotations

import os
import sys

import bmesh

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "lib"))
_REPO = os.path.dirname(os.path.dirname(_HERE))

import aegis_kit as ak  # noqa: E402  (doit suivre l'ajout au sys.path)

OUTPUT = os.path.join(_REPO, "assets/imported/models/structures/citadel_beacon.glb")

# Meme densite de texel que la coque et que la tourelle : trois echelles de
# feuille de detail dans un meme plan de camera se verraient.
TEXELS_PER_METER = 0.12

SEGMENTS = 12          # nacelle facettee (la planche ne montre rien de rond)
RING_SEGMENTS = 20
# Anneau MINCE : a 12 cm de large et 7 cm d'epaisseur il pesait plus que la
# nacelle et la balise se rendait comme une bague en or. La planche montre un
# halo fin qui ceinture la nacelle, pas une jante.
RING_R_IN = 0.395
RING_R_OUT = 0.47
RING_HALF_H = 0.026
EYE_Y = -0.30          # avant de la nacelle — fixe la bbox en -Y


def build_pod():
    """Nacelle : pod facette ivoire, collerette bleue, ventre anthracite."""
    bm = bmesh.new()

    bands = ak.add_lathe(
        bm,
        [
            (-0.26, 0.00, "AA_Greeble"),       # pole bas
            (-0.22, 0.12, "AA_Greeble"),
            (-0.12, 0.24, "AA_Greeble"),       # ventre
            (-0.04, 0.29, "AA_Panel"),         # collerette bleue
            (0.03, 0.29, "AA_Hull"),
            (0.12, 0.25, "AA_Hull"),           # ROBE : recoit les plaques
            (0.18, 0.21, "AA_Trim"),           # jonc dore
            # Oeil ANNULAIRE sur le DESSUS, et pas seulement a l'avant : la
            # camera de jeu regarde a 20 deg de la verticale, elle voit le
            # capot de la balise et presque jamais sa face avant. Un feu place
            # uniquement devant n'existerait pas (ADR-0011).
            (0.20, 0.19, "AA_Emissive_Engine"),
            (0.20, 0.10, "AA_Greeble"),        # moyeu
            (0.24, 0.07, "AA_Glass"),
            (0.25, 0.00, "AA_Glass"),          # pole haut
        ],
        SEGMENTS,
        axis="Z",
    )

    # plaques de robe : une facette sur trois enfoncee, joints anthracite
    robe = [f for f in bands[5] if f is not None and f.is_valid]
    for i, face in enumerate(robe):
        if i % 3:
            continue
        ak.set_material(
            ak.inset_panel(bm, [face], "AA_Hull", thickness=0.016, depth=-0.006),
            "AA_Trim",
        )

    # oeil cyan tourne vers -Y, sous une visiere ivoire et un verre sombre
    ak.add_box(bm, (0.0, EYE_Y + 0.10, 0.02), (0.30, 0.22, 0.22), "AA_Greeble")
    ak.add_box(bm, (0.0, EYE_Y + 0.02, 0.02), (0.22, 0.10, 0.16), "AA_Emissive_Engine")
    ak.add_box(bm, (0.0, EYE_Y, 0.02), (0.15, 0.06, 0.10), "AA_Glass")
    ak.add_box(bm, (0.0, EYE_Y + 0.09, 0.15), (0.26, 0.16, 0.05), "AA_Hull")
    ak.add_box(bm, (0.0, EYE_Y + 0.11, 0.18), (0.10, 0.09, 0.03), "AA_Marking_Red")

    # tuyeres de maintien en station, a l'arriere
    for sd in (ak.PORT, ak.STARBOARD):
        ak.add_lathe(
            bm,
            [
                (0.16, 0.00, "AA_Greeble"),
                (0.20, 0.05, "AA_Greeble"),
                (0.29, 0.05, "AA_Greeble"),
                (0.30, 0.075, "AA_Trim"),
                (0.33, 0.075, "AA_Trim"),
                (0.33, 0.04, "AA_Emissive_Engine"),
                (0.28, 0.035, "AA_Emissive_Engine"),
                (0.27, 0.00, "AA_Emissive_Engine"),
            ],
            8,
            center_x=sd * 0.17,
            center_z=0.00,
        )

    return ak.new_object("Beacon_Pod", bm)


def build_ring():
    """Anneau porteur : tore de section rectangulaire, dore, a feux cyan.

    Construit avec `add_lathe(axis="Z")` en refermant le contour sur son premier
    point : deux points de meme z et de rayons differents donnent une couronne
    plate, deux points de meme rayon donnent une paroi. Quatre segments et le
    tore est ferme — le kit n'a pas de primitive de tore, il n'en a pas besoin.
    """
    bm = bmesh.new()
    ak.add_lathe(
        bm,
        [
            (-RING_HALF_H, RING_R_IN, "AA_Greeble"),   # face interne
            (-RING_HALF_H, RING_R_OUT, "AA_Trim"),     # dessous
            (RING_HALF_H, RING_R_OUT, "AA_Trim"),      # tranche externe
            (RING_HALF_H, RING_R_IN, "AA_Trim"),       # dessus
            (-RING_HALF_H, RING_R_IN, "AA_Trim"),      # refermeture
        ],
        RING_SEGMENTS,
        axis="Z",
    )

    # trois feux cyan sur l'anneau (0, 120, 240 deg) + leurs berceaux
    for k in range(3):
        import math

        a = 2.0 * math.pi * k / 3.0 - math.pi * 0.5
        cx, cy = 0.42 * math.cos(a), 0.42 * math.sin(a)
        ak.add_box(bm, (cx, cy, 0.00), (0.10, 0.10, 0.09), "AA_Greeble")
        ak.add_box(bm, (cx, cy, 0.042), (0.065, 0.065, 0.03), "AA_Emissive_Engine")

    # deux bras qui relient l'anneau a la nacelle (sinon il flotte tout seul)
    for sd in (ak.PORT, ak.STARBOARD):
        ak.add_box(bm, (sd * 0.32, 0.00, 0.00), (0.24, 0.09, 0.07), "AA_Greeble")

    return ak.new_object("Beacon_Ring", bm)


def build_markers() -> list:
    """Points d'attache.

    `Ring_Center` + `Ring_Axis` decrivent l'anneau a Godot : centre et direction
    d'axe. `Beacon_Eye` est le temoin ASYMETRIQUE d'orientation — la bbox d'une
    balise, elle, est presque symetrique et ne pourrait pas dire si l'oeil
    regarde a l'endroit.
    """
    return [
        ak.attach_point("Beacon_Center", (0.0, 0.0, 0.0)),
        ak.attach_point("Ring_Center", (0.0, 0.0, 0.0)),
        ak.attach_point("Ring_Axis", (0.0, 0.0, 0.30)),
        ak.attach_point("Beacon_Eye", (0.0, EYE_Y - 0.04, 0.02)),
    ]


CONTRACT = ak.HullContract(
    name="Citadel Beacon",
    width_x=0.96,        # diametre hors tout de l'anneau
    length_z=0.96,
    max_height_y=0.60,
    tri_budget=2_000,
    required_materials=ak.MATERIAL_ORDER,
    required_attach_points=("Beacon_Center", "Ring_Center", "Ring_Axis", "Beacon_Eye"),
    # L'oeil deborde legerement vers l'avant : le centre de bbox n'est pas
    # exactement l'origine. Le pivot qui compte ici est le centre de la NACELLE,
    # sur lequel l'animation orbite.
    pivot_tolerance=0.12,
)


def _triangulate_ngons(obj) -> None:
    """Triangule les seules n-gons : sans elles, pas de `TANGENT` a l'export."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons)
    bm.to_mesh(obj.data)
    bm.free()


def main() -> None:
    ak.reset_scene()
    ak.set_faction(ak.FACTION_VANGUARD)

    beacon = ak.join_objects([build_pod(), build_ring()], "CitadelBeacon")
    ak.cleanup(beacon)
    ak.bevel_sharp_edges(beacon, width=0.008, segments=1, angle_deg=34.0)
    ak.shade_smooth_by_angle(beacon, angle_deg=34.0)
    _triangulate_ngons(beacon)
    ak.box_project_uv(beacon, TEXELS_PER_METER)

    ak.export_hull(beacon, build_markers(), OUTPUT, CONTRACT)


if __name__ == "__main__":
    main()
