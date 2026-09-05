"""Test du kit — depliage en ATLAS (`ak.atlas_unwrap`, `ADR-0046`/`ADR-0047`).

    blender-aegis -t 1 -b -P tools/blender/test_atlas_unwrap.py

Sort en code 0 si tout passe, 1 sinon. Aucun asset n'est publie.

POURQUOI CE TEST — meme raison que `test_moving_parts.py` : `check.sh` tourne sans
Blender et ne couvre donc pas le kit. Ecrit AVANT le premier usage d'`atlas_unwrap()`
dans une coque, il a deja trouve un defaut que la relecture n'avait pas vu — voir
`test_arete_partagee_n_est_pas_un_recouvrement()`.

⚠️ CE QUE CE TEST GARDE VRAIMENT, c'est le DETERMINISME du depliage. `atlas_unwrap()`
enveloppe `bpy.ops.uv.smart_project`, que le kit refusait par principe (docstring de
`box_project_uv`). Le principe a ete remplace par une mesure — mais cette mesure vaut
pour Blender 5.2.1 avec `-t 1` (elle valait deja pour 4.5.11, et a survecu a la
montee de version sans une modification). Le jour ou l'une des deux conditions change, c'est ce
test qui doit rougir en premier, pas une coque livree six semaines plus tard.
"""
from __future__ import annotations

import math
import os
import struct
import sys

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import aegis_kit as ak  # noqa: E402

FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    if condition:
        print("  ok   %s" % message)
    else:
        print("  ECHEC %s" % message)
        FAILURES.append(message)


def _fresh() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def _test_hull() -> bpy.types.Object:
    """Un maillage fixe et volontairement penible : cube, loft oblique, n-gon.

    Pas d'alea, pas de fichier externe : le test doit tourner sur une machine nue.
    """
    _fresh()
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    ring_a = [bm.verts.new((0.6 * (i % 3) - 0.6, 0.4 * (i // 3), 1.2)) for i in range(9)]
    ring_b = [bm.verts.new((0.5 * (i % 3) - 0.5, 0.3 * (i // 3), 2.0)) for i in range(9)]
    for i in range(8):
        bm.faces.new((ring_a[i], ring_a[i + 1], ring_b[i + 1], ring_b[i]))
    bm.faces.new([bm.verts.new((2.0 + 0.7 * i, 0.15 * i * i, 0.3 * i)) for i in range(6)])
    bm.normal_update()
    mesh = bpy.data.meshes.new("atlas_test")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("atlas_test", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def _uv_digest(obj: bpy.types.Object) -> bytes:
    layer = obj.data.uv_layers.active
    return b"".join(struct.pack("<ff", uv.vector[0], uv.vector[1]) for uv in layer.uv)


# --- Le depliage lui-meme ---------------------------------------------------


def test_le_depliage_produit_un_atlas_propre() -> None:
    print("\n[atlas] un depliage propre : dans le carre, sans recouvrement")
    obj = _test_hull()
    report = ak.atlas_unwrap(obj)
    check(report.outside == 0, "aucune boucle UV hors du carre [0, 1]")
    check(report.overlap_texels == 0, "aucun texel couvert deux fois")
    check(report.fill >= 0.30, "remplissage %.1f %% au-dessus du plancher" % (report.fill * 100.0))
    check(report.loops > 0 and report.triangles > 0, "le rapport compte des boucles et des triangles")


def test_le_depliage_est_deterministe() -> None:
    print("\n[atlas] deux depliages successifs donnent les MEMES UV, au bit pres")
    first = _uv_digest(_deplie())
    second = _uv_digest(_deplie())
    check(first == second, "les deux depliages sont byte-identiques (%d octets)" % len(first))


def _deplie() -> bpy.types.Object:
    obj = _test_hull()
    ak.atlas_unwrap(obj)
    return obj


# --- Le garde-fou, verifie en le faisant TOMBER ------------------------------


def test_un_uv_hors_du_carre_est_refuse() -> None:
    print("\n[garde] une boucle UV hors du carre fait echouer le contrat")
    obj = _test_hull()
    ak.atlas_unwrap(obj)
    obj.data.uv_layers.active.uv[0].vector = (1.4, 0.5)
    caught = False
    try:
        _verifie_a_posteriori(obj)
    except ak.ContractError as err:
        caught = "hors du carre" in str(err)
    check(caught, "ContractError levee, et elle nomme le defaut")


def _verifie_a_posteriori(obj: bpy.types.Object) -> None:
    """Rejoue les seules verifications du contrat, sans re-deplier."""
    outside = 0
    for uv in obj.data.uv_layers.active.uv:
        u, v = uv.vector
        if u < -1e-4 or u > 1.0 + 1e-4 or v < -1e-4 or v > 1.0 + 1e-4:
            outside += 1
    if outside:
        raise ak.ContractError(f"{outside} boucles UV hors du carre [0, 1]")


# --- Le rastériseur de recouvrement -----------------------------------------


def test_deux_triangles_superposes_sont_vus() -> None:
    print("\n[rastere] deux triangles qui se superposent VRAIMENT sont comptes")
    tri = ((0.10, 0.10), (0.40, 0.10), (0.10, 0.40))
    count = ak._uv_overlap_texels([tri, tri], 512)
    check(count > 100, "un triangle pose sur lui-meme couvre %d texels deux fois" % count)


def test_arete_partagee_n_est_pas_un_recouvrement() -> None:
    """⚠️ REGRESSION — c'est le defaut que ce test a trouve le 2026-09-05.

    Version naive du rastériseur, deux triangles ADJACENTS partageant une arete
    rapportaient 1 a 4 texels doubles sur un million : un centre de texel tombant
    exactement sur l'arete satisfait `w >= 0` des deux cotes. C'etait un departage
    d'egalite, pas un recouvrement — et ca faisait echouer un packing sain.
    """
    print("\n[rastere] deux triangles qui partagent une arete ne se recouvrent PAS")
    a = ((0.10, 0.10), (0.50, 0.10), (0.10, 0.50))
    b = ((0.50, 0.10), (0.50, 0.50), (0.10, 0.50))
    count = ak._uv_overlap_texels([a, b], 512)
    check(count == 0, "un contact d'arete ne compte pas (%d texels)" % count)


def test_un_carre_plein_ne_se_recouvre_pas() -> None:
    print("\n[rastere] une grille jointive de 200 triangles ne se recouvre pas")
    tris = []
    step = 0.05
    for i in range(10):
        for j in range(10):
            x, y = 0.1 + i * step, 0.1 + j * step
            tris.append(((x, y), (x + step, y), (x, y + step)))
            tris.append(((x + step, y), (x + step, y + step), (x, y + step)))
    check(ak._uv_overlap_texels(tris, 512) == 0, "aucun recouvrement sur 200 triangles jointifs")


def main() -> None:
    print("Kit version %s" % ak.VERSION)
    test_le_depliage_produit_un_atlas_propre()
    test_le_depliage_est_deterministe()
    test_un_uv_hors_du_carre_est_refuse()
    test_deux_triangles_superposes_sont_vus()
    test_arete_partagee_n_est_pas_un_recouvrement()
    test_un_carre_plein_ne_se_recouvre_pas()
    print("\n%s" % ("TOUT PASSE" if not FAILURES else "%d ECHEC(S)" % len(FAILURES)))
    sys.exit(1 if FAILURES else 0)


main()
