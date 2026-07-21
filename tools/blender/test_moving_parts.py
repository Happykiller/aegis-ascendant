"""Test du kit — pieces mobiles exportees en nœuds separes (`ak.moving_part`).

    blender45 -t 1 -b -P tools/blender/test_moving_parts.py

Sort en code 0 si tout passe, 1 sinon. Aucun asset n'est publie : le `.glb`
part dans /tmp.

POURQUOI CE TEST — `check.sh` ne couvre pas le kit Blender (il tourne sans
Blender). La primitive `moving_part()` serait donc restee sans verification
jusqu'a son premier usage reel, c'est-a-dire jusqu'a ce qu'une coque entiere
soit refaite autour d'elle.

Ecrit AVANT le premier usage, il a immediatement trouve un defaut que la
relecture n'avait pas vu : `_validate_glb()` calculait la bounding box depuis
les accesseurs de position, en espace LOCAL. Or une piece mobile a son origine
sur sa charniere — sa position reelle vit dans la translation du nœud. La piece
sortait donc du controle de dimensions, et un volet pouvait depasser de 40 cm
sans que le contrat s'en apercoive.
"""

from __future__ import annotations

import json
import os
import struct
import sys

import bmesh

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "lib"))

import aegis_kit as ak  # noqa: E402

OUT = "/tmp/aegis_test_moving_parts.glb"

#: Charniere d'un volet, dans le repere d'auteur (nez -Y, dessus +Z, babord +X).
HINGE = (0.80, 0.50, 0.00)

#: La meme, attendue dans le repere Godot apres correction d'axe.
#: (x, y, z)_auteur -> rotation pi autour de Z, puis yup -> (-x, z, -y)
HINGE_GODOT = (-0.80, 0.00, 0.50)

_failures: list[str] = []


def check(condition: bool, message: str) -> None:
    print(("  [OK]   " if condition else "  [FAIL] ") + message)
    if not condition:
        _failures.append(message)


def build() -> None:
    ak.reset_scene()
    ak.set_faction(ak.FACTION_VANGUARD)

    bm = bmesh.new()
    ak.add_box(bm, (0.0, 0.0, 0.0), (2.0, 3.0, 0.4), "AA_Hull")
    hull = ak.new_object("TestHull", bm)

    # Deux volets symetriques : une piece d'un seul cote decentrerait la bbox et
    # le contrat le refuserait — ce qui est le comportement voulu.
    parts = []
    for side, tag in ((ak.PORT, "L"), (ak.STARBOARD, "R")):
        bp = bmesh.new()
        ak.add_box(bp, (side * 1.1, 0.5, 0.0), (0.6, 0.5, 0.06), "AA_Panel")
        parts.append(ak.moving_part(f"Flap_{tag}", bp, (side * HINGE[0], HINGE[1], HINGE[2])))

    contract = ak.HullContract(
        name="MovingPartsTest",
        width_x=2.80,      # coque 2,0 + les deux volets qui debordent de 0,4 de chaque cote
        length_z=3.00,
        max_height_y=1.00,
        tri_budget=2000,
        required_materials=("AA_Hull", "AA_Panel"),
        required_attach_points=("Nose",),
    )
    ak.export_hull(hull, [ak.attach_point("Nose", (0.0, -1.5, 0.0))], OUT, contract, parts=parts)


def verify() -> None:
    data = open(OUT, "rb").read()
    length = struct.unpack("<I", data[12:16])[0]
    gltf = json.loads(data[20 : 20 + length])
    nodes = {n["name"]: n for n in gltf["nodes"]}

    check("Flap_L" in nodes and "Flap_R" in nodes, "les deux volets sont des nœuds du .glb")
    check("mesh" in nodes.get("Flap_L", {}), "Flap_L porte son propre maillage")
    check("mesh" not in nodes.get("Nose", {}), "Nose reste un point d'attache sans maillage")

    # LE point du test : l'origine du volet est sa charniere, pas l'origine du
    # vaisseau. Sans ca, `rotation.z` cote Godot ferait decrire au volet un arc de
    # cercle autour du nez au lieu de le faire battre sur son axe.
    got = nodes.get("Flap_L", {}).get("translation", [0.0, 0.0, 0.0])
    ok = all(abs(got[i] - HINGE_GODOT[i]) < 1e-4 for i in range(3))
    check(ok, f"la charniere de Flap_L est l'origine du nœud : {tuple(round(v, 3) for v in got)}")

    # La bbox doit inclure les pieces mobiles MALGRE leur origine deportee.
    lo = [9e9] * 3
    hi = [-9e9] * 3
    for node in gltf["nodes"]:
        if "mesh" not in node:
            continue
        off = node.get("translation", [0.0, 0.0, 0.0])
        for prim in gltf["meshes"][node["mesh"]]["primitives"]:
            acc = gltf["accessors"][prim["attributes"]["POSITION"]]
            for a in range(3):
                lo[a] = min(lo[a], acc["min"][a] + off[a])
                hi[a] = max(hi[a], acc["max"][a] + off[a])
    width = hi[0] - lo[0]
    check(abs(width - 2.80) < 1e-3, f"la bbox englobe les volets : largeur {width:.3f} m")


def main() -> int:
    print("[test_moving_parts]")
    build()
    verify()
    if _failures:
        print(f"[test_moving_parts] {len(_failures)} ECHEC(S)")
        return 1
    print("[test_moving_parts] tout est vert")
    return 0


if __name__ == "__main__":
    sys.exit(main())
