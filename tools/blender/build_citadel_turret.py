"""build_citadel_turret.py — tourelle secondaire de l'Aegis Citadel (BRIEF-0032).

    blender45 -b -P tools/blender/build_citadel_turret.py

Produit `assets/imported/models/structures/citadel_turret.glb`.

Le script EST la source de l'asset (ADR-0008) : aucun `.blend` n'est versionne.
Deterministe, auto-valide par `ak.export_hull()`.

Reference de design : `assets/reference/concepts/aegis_citadel_concept_sheet.png`,
encart des tourelles (bas droite de la planche) : dome trapu, **lentille cyan
annulaire** cerclee d'or, moyeu central, double tube sortant d'un mantelet, le
tout assis dans une cuvette circulaire du pont.

Cette piece etait jusqu'ici SOUDEE dans la coque de la citadelle, donc incapable
de bouger. Elle en sort (BRIEF-0032 §2) : Godot l'instancie sur les marqueurs
`Turret_01..06` et la fait pivoter.

CONTRAT D'ANIMATION — c'est la seule contrainte forte de ce modele :
  * **l'origine est sur l'axe de rotation**, au ras du pont (z = 0 dans le
    repere d'auteur). Une tourelle dont le pivot n'est pas au centre decrit un
    cercle au lieu de pivoter, et le defaut ne se voit qu'une fois animee ;
  * les tubes pointent vers **-Y** (repere d'auteur), donc vers **-Z** cote
    Godot, c'est-a-dire vers le haut de l'ecran, comme toutes les autres unites.

L'origine coincide exactement avec le marqueur `Turret_NN` de la coque : la
tourelle se pose sans decalage.
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

OUTPUT = os.path.join(_REPO, "assets/imported/models/structures/citadel_turret.glb")

SEED = 30251

# Meme densite de texel que la coque (0,12 tuile/m) et non une densite propre :
# la tourelle est POSEE SUR la coque, et deux echelles de feuille de detail qui
# se touchent se voient immediatement — les plaques changeraient de taille au
# passage du socle. La tourelle ne fait que 1,5 m, elle n'occupe donc qu'un
# fragment de tuile : son detail vient de sa geometrie, la feuille ne fait que
# la salir un peu.
TEXELS_PER_METER = 0.12

SEGMENTS = 16          # facettes du fut : la planche montre un dome facette
DRUM_R = 0.74          # rayon du fut, cale sur la cuvette du pont (0,88)
LENS_INNER = 0.22      # rayon interne de la lentille annulaire
LENS_OUTER = 0.46      # rayon externe
TUBE_X = 0.22          # demi-ecart des deux tubes
TUBE_R = 0.085
TUBE_Z = 0.36          # hauteur de l'axe des tubes
TUBE_TIP = -1.34       # bouche — fixe la bbox en -Y


def build_body():
    """Fut, dome, lentille annulaire, moyeu : le solide de revolution."""
    bm = bmesh.new()

    bands = ak.add_lathe(
        bm,
        [
            (0.00, 0.00, "AA_Greeble"),          # pole bas (fond du fut)
            (0.00, DRUM_R * 0.94, "AA_Greeble"),
            (0.07, DRUM_R, "AA_Greeble"),        # bourrelet de pivot
            (0.13, DRUM_R, "AA_Trim"),           # jonc dore de rotation
            (0.17, DRUM_R * 0.99, "AA_Hull"),
            (0.44, DRUM_R * 0.97, "AA_Hull"),    # ROBE : c'est cette bande
            (0.52, DRUM_R * 0.88, "AA_Hull"),    # qui recoit les plaques
            (0.60, DRUM_R * 0.70, "AA_Hull"),    # epaulement du dome
            (0.64, LENS_OUTER + 0.06, "AA_Trim"),
            (0.66, LENS_OUTER, "AA_Emissive_Engine"),   # LENTILLE ANNULAIRE
            (0.66, LENS_INNER, "AA_Greeble"),
            (0.72, LENS_INNER * 0.92, "AA_Greeble"),    # moyeu
            (0.74, LENS_INNER * 0.60, "AA_Glass"),      # oculus sombre
            (0.75, 0.00, "AA_Glass"),
        ],
        SEGMENTS,
        axis="Z",
    )

    # --- plaques de robe : la planche montre un fut segmente ---------------
    # Une facette sur deux est enfoncee, une sur quatre passe en bleu. C'est le
    # meme parti que sur la coque (plaques a joint visible), a l'echelle de la
    # piece : joints de 2,5 cm, pas de 5.
    robe = [f for f in bands[5] if f is not None and f.is_valid]
    for i, face in enumerate(robe):
        borders = ak.inset_panel(bm, [face], "AA_Hull", thickness=0.025, depth=-0.012)
        ak.set_material(borders, "AA_Trim" if i % 5 == 0 else "AA_Greeble")
        if i % 4 == 1:
            ak.inset_panel(bm, [face], "AA_Panel", thickness=0.03, depth=-0.015)

    # bande de marquage rouge sur le flanc arriere (zone d'ejection)
    ak.add_box(bm, (0.0, 0.60, 0.30), (0.34, 0.10, 0.09), "AA_Marking_Red")
    # ventilations arriere
    for k in range(3):
        ak.add_box(bm, (-0.30 + k * 0.30, 0.66, 0.46), (0.18, 0.16, 0.10), "AA_Greeble")

    return ak.new_object("Turret_Body", bm)


def build_guns():
    """Mantelet et double tube, pointes vers -Y (haut de l'ecran)."""
    bm = bmesh.new()

    # mantelet : bloc etage qui deborde du fut vers l'avant
    ak.add_box(bm, (0.0, -0.46, 0.34), (0.94, 0.60, 0.46), "AA_Greeble")
    ak.add_box(bm, (0.0, -0.52, 0.56), (0.70, 0.44, 0.12), "AA_Hull")
    ak.add_box(bm, (0.0, -0.56, 0.62), (0.40, 0.30, 0.05), "AA_Trim")
    ak.add_box(bm, (0.0, -0.74, 0.50), (0.30, 0.12, 0.10), "AA_Emissive_Engine")
    for sd in (ak.PORT, ak.STARBOARD):
        ak.add_box(bm, (sd * 0.44, -0.40, 0.30), (0.14, 0.46, 0.34), "AA_Hull")

    for sd in (ak.PORT, ak.STARBOARD):
        ak.add_lathe(
            bm,
            [
                (-0.10, 0.00, "AA_Greeble"),
                (-0.14, 0.135, "AA_Greeble"),          # culasse
                (-0.52, 0.135, "AA_Trim"),
                (-0.62, 0.125, "AA_Trim"),             # collier dore
                (-0.66, TUBE_R, "AA_Hull"),
                (TUBE_TIP + 0.30, TUBE_R, "AA_Hull"),  # fut ivoire
                (TUBE_TIP + 0.26, TUBE_R * 1.30, "AA_Greeble"),
                (TUBE_TIP + 0.04, TUBE_R * 1.30, "AA_Greeble"),   # manchon
                (TUBE_TIP, TUBE_R * 1.15, "AA_Greeble"),          # BOUCHE (bbox -Y)
                (TUBE_TIP + 0.03, TUBE_R * 0.55, "AA_Emissive_Engine"),
                (TUBE_TIP + 0.16, TUBE_R * 0.50, "AA_Emissive_Engine"),
                (TUBE_TIP + 0.18, 0.00, "AA_Emissive_Engine"),
            ],
            10,
            center_x=sd * TUBE_X,
            center_z=TUBE_Z,
        )

    return ak.new_object("Turret_Guns", bm)


def build_markers() -> list:
    """Points d'attache. Ils servent aussi de temoins ASYMETRIQUES : la bbox
    d'une tourelle est incapable de dire si elle pointe a l'endroit, les bouches
    de tir le disent."""
    points = [ak.attach_point("Turret_Pivot", (0.0, 0.0, 0.0))]
    points += list(ak.attach_pair("Muzzle", TUBE_X, TUBE_TIP - 0.04, TUBE_Z))
    points.append(ak.attach_point("Turret_Lens", (0.0, 0.0, 0.68)))
    return points


CONTRACT = ak.HullContract(
    name="Citadel Turret",
    width_x=1.48,        # bout a bout des joues de mantelet
    length_z=2.10,       # bouche des tubes au dos du fut
    max_height_y=0.90,
    tri_budget=3_000,
    required_materials=ak.MATERIAL_ORDER,
    required_attach_points=("Turret_Pivot", "Muzzle_L", "Muzzle_R", "Turret_Lens"),
    # ⚠️ Le pivot d'une tourelle N'EST PAS le centre de sa bounding box : il est
    # sur l'axe de rotation, et les tubes debordent d'un metre vers l'avant. Le
    # controle de centrage du kit (concu pour des coques, ou pivot = centre) est
    # donc desserre ici — volontairement, et seulement sur cet axe-la. Le
    # controle qui compte pour cette piece, l'orientation par temoin
    # asymetrique, reste actif.
    pivot_tolerance=0.60,
)


def main() -> None:
    ak.reset_scene()
    ak.set_faction(ak.FACTION_VANGUARD)

    turret = ak.join_objects([build_body(), build_guns()], "CitadelTurret")
    ak.cleanup(turret)
    ak.bevel_sharp_edges(turret, width=0.012, segments=1, angle_deg=34.0)
    ak.shade_smooth_by_angle(turret, angle_deg=34.0)
    _triangulate_ngons(turret)
    ak.box_project_uv(turret, TEXELS_PER_METER)

    ak.export_hull(turret, build_markers(), OUTPUT, CONTRACT)


def _triangulate_ngons(obj) -> None:
    """Triangule les seules n-gons : sans elles, pas de `TANGENT` a l'export."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons)
    bm.to_mesh(obj.data)
    bm.free()


if __name__ == "__main__":
    main()
