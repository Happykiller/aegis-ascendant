"""Notre transformation du Specter-9 C — les ailes se DÉPLIENT au lieu de balayer.

    blender-aegis -t 1 -b -P tools/blender/adapt_specter_9_v3.py            # exporte
    blender-aegis -t 1 -b -P tools/blender/adapt_specter_9_v3.py -- --renders  # + planches

⚠️ CE N'EST PAS UN SCRIPT DE COQUE DU KIT, ET IL N'EN SUIT PAS LE CONTRAT. Les coques du
kit se génèrent depuis rien (`ADR-0008` : « le script Python EST la source, aucun `.blend`
n'est versionné »). Celle-ci est un modèle TIERS : sa source est son `.blend`, et le
`.glb` est son livrable. Le script de son auteur — `build_spectre9_v3.py`, conservé à
côté du `.blend` — n'est d'ailleurs pas un générateur non plus : il ouvre un
`spectre9_v2.blend` qu'on n'a pas, en supprime des pièces et les reconstruit. 241 lignes
pour 525 objets : c'est un CHANGEMENT, pas une origine.

Reprendre la main sur ce modèle ne passe donc pas par une rétro-ingénierie — elle
re-dériverait ce que le `.blend` contient déjà, et produirait au mieux un autre vaisseau.
Elle passe par ce fichier : **la source est versionnée, et on écrit la transformation.**
C'est exactement la méthode de son auteur, continuée.

## Ce que cette transformation change, et pourquoi

L'opérateur, après l'avoir vue en jeu : « *il y a une animation où les ailes s'ouvrent
mais je préfère qu'elles se déplient plutôt qu'on se retrouve avec un truc fin qui bouge
seulement* ».

Le modèle livré fait pivoter chaque aile autour de **Z** — donc à plat, dans le plan
horizontal : une flèche variable de F-14. Or la caméra du jeu regarde presque au zénith.
Une aile qui balaie à plat n'y change presque pas de silhouette : elle glisse. Un
dépliage autour de l'axe **longitudinal** (Y) fait au contraire varier la surface vue, ce
qui est la seule chose qu'une vue de dessus sache lire.

## ⚠️ LES QUATRE PILOTES SE TIENNENT, ET C'EST LE PIÈGE DE CE MODÈLE

Le `.blend` porte 44 pilotes, dont 40 pour les pétales de tuyère. Les quatre autres
forment un couple qu'aucune documentation ne signale :

| Pilote | Axe | Rôle |
|---|---|---|
| `CTRL | L/R wing sweep` | Z | l'aile balaie |
| `CTRL | L/R pylon alignment` | Z, **signe opposé** | il DÉFAIT la rotation de l'aile pour garder les canons vers l'avant |

Changer l'aile sans toucher au pylône laisserait celui-ci **compenser une rotation qui
n'existe plus** : les canons partiraient de travers, sans une erreur ni une ligne de
journal. Les quatre se traitent donc ensemble.

## L'angle n'est pas un goût — et mon premier calcul était faux

L'intention à conserver est celle de l'auteur : son balayage ramène l'envergure de
**8,90 m à 5,65 m**. On cherche donc l'angle de dépliage qui produit la même variation de
silhouette vue de dessus.

⚠️ **Le cosinus ne s'applique PAS à l'envergure entière.** Seule la partie EN DEHORS du
pivot tourne : le pivot est à x = 1,99 et le bout d'aile à 4,45, donc le bras vaut 2,46 m
et non 4,45. Mon premier calcul appliquait `cos θ` aux 8,90 m et donnait 51° — mesuré, ce
réglage ne rendait que **7,143 m**, soit 80 % au lieu des 63 % visés, et la différence ne
se voyait pas à l'œil sur la planche.

    envergure(θ) = 2 × (1,99 + 2,46 × cos θ)
    5,651 = 2 × (1,99 + 2,46 × cos θ)   ->   cos θ = 0,340   ->   θ ≈ 70°

**70°**, donc. Vérifié sur le modèle : le bout d'aile s'élève de 2,31 m et l'envergure
tombe bien à celle du balayage d'origine.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "assets/source/models/specter_9_v3/spectre9_v3.blend"
TARGET = ROOT / "assets/imported/models/ships/specter_9_v3.glb"
PLANCHES = ROOT / "assets/source/models/specter_9_v3"

#: Voir « L'angle n'est pas un goût » ci-dessus.
FOLD_DEG = 70.0
#: Le clip du modèle : 180 images, et la pleine vitesse au milieu de la montée.
FRAMES = 180


def _driver_expression(obj: bpy.types.Object, axis: int) -> str | None:
    if obj.animation_data is None:
        return None
    for curve in obj.animation_data.drivers:
        if curve.data_path == "rotation_euler" and curve.array_index == axis:
            return curve.driver.expression
    return None


def refold(scene: bpy.types.Scene) -> None:
    """Déplace les quatre pilotes d'aile de l'axe Z vers l'axe Y."""
    radians = math.radians(FOLD_DEG)
    #: ⚠️ SIGNES MESURÉS, PAS DEVINÉS. Une rotation POSITIVE autour de +Y envoie un point
    #: d'abscisse négative vers le HAUT (z' = −x·sinθ). L'aile bâbord est en x négatif :
    #: elle se relève donc sur un signe positif, tribord sur un signe négatif. C'est
    #: l'inverse des signes du balayage, et les recopier aurait fait plonger une aile
    #: pendant que l'autre monte.
    plan = {
        "CTRL | L wing sweep": +radians,
        "CTRL | R wing sweep": -radians,
        # Le pylône DÉFAIT la rotation de son aile pour que les canons restent pointés
        # vers l'avant. Il suit donc l'aile sur son nouvel axe, à signe opposé.
        "CTRL | L pylon alignment": -radians,
        "CTRL | R pylon alignment": +radians,
    }
    for name, amount in plan.items():
        obj = bpy.data.objects.get(name)
        if obj is None:
            raise SystemExit("[adapt] '%s' introuvable — le .blend n'est pas celui attendu" % name)
        before = _driver_expression(obj, 2)
        if before is None:
            raise SystemExit("[adapt] '%s' n'a pas de pilote sur Z : déjà transformé ?" % name)
        obj.driver_remove("rotation_euler", 2)
        obj.rotation_euler[2] = 0.0
        curve = obj.driver_add("rotation_euler", 1)
        var = curve.driver.variables.new()
        var.name = "speed"
        var.targets[0].id = bpy.data.objects["CTRL | Flight configuration"]
        var.targets[0].data_path = '["speed"]'
        curve.driver.expression = "%.16f * speed" % amount
        print("[adapt] %-26s Z(%s)  ->  Y(%.4f * speed)" % (name, before.split("*")[0].strip(), amount))


def bake_and_export(scene: bpy.types.Scene) -> None:
    """Cuit les pilotes en images clés puis exporte — la recette de l'auteur, reprise.

    ⚠️ UN glTF N'EXÉCUTE PAS LES PILOTES DE BLENDER. Sans cette cuisson, le `.glb`
    sortirait avec une animation vide et la coque serait figée en jeu, sans erreur.
    """
    ship = bpy.data.collections["SPECTRE 9 | assembly"]
    driven = [o for o in ship.objects if o.animation_data and o.animation_data.drivers]
    samples: dict[str, list] = {o.name: [] for o in driven}
    for frame in range(1, FRAMES + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for obj in driven:
            samples[obj.name].append(tuple(obj.rotation_euler))
    for obj in driven:
        for curve in list(obj.animation_data.drivers):
            obj.driver_remove(curve.data_path, curve.array_index)
        for frame, value in enumerate(samples[obj.name], 1):
            obj.rotation_euler = value
            obj.keyframe_insert(data_path="rotation_euler", frame=frame)
    scene.frame_set(1)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in ship.objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects["CTRL | Flight configuration"]
    bpy.ops.export_scene.gltf(
        filepath=str(TARGET), use_selection=True, export_format="GLB", export_apply=True,
        export_animations=True, export_animation_mode="SCENE", export_frame_range=True,
        export_force_sampling=True, export_anim_scene_split_object=False, export_extras=True)
    print("[adapt] ecrit %s (%d objets animes)" % (TARGET, len(driven)))


def renders(scene: bpy.types.Scene) -> None:
    """Deux vues de dessus, ailes dépliées et repliées — la recette de l'auteur."""
    for frame, nom in [(1, "fold_open"), (84, "fold_closed")]:
        scene.camera = bpy.data.objects["Camera | top orthographic"]
        scene.frame_set(frame)
        scene.render.filepath = str(PLANCHES / ("specter_9_v3_%s.png" % nom))
        bpy.ops.render.render(write_still=True)
        print("[adapt] planche %s" % scene.render.filepath)


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    refold(scene)
    veut_planches = "--renders" in sys.argv
    if veut_planches:
        renders(scene)
        bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
        scene = bpy.context.scene
        refold(scene)
    bake_and_export(scene)
    print("[adapt] TERMINE")


main()
