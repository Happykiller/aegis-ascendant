"""Les bouchons qui permettent d'executer le `build.py` de l'auteur VERBATIM.

Le `build.py` de chaque livraison importe quatre modules maison : `geometry`,
`materials`, `animation`, `studio`, plus `paths`. On lui rend `geometry` patche
(voir `forge_geometry.py`) et `animation` **inchange** — ce sont les clips, ils
sont un critere. Restent trois modules dont on ne veut RIEN :

* `materials` — il fabrique les atlas PBR de l'auteur en lisant sa planche
  technique. ⛔ `ADR-0028` : la forge ne livre aucune texture, et le harnais du
  Long Cortege echoue le build si une image apparait. Le bouchon rend des
  materiaux PLATS portant les MEMES NOMS (`01 | Anthracite blinde`, ...), ce qui
  suffit : le repli sur les cinq slots du kit se fait par nom, apres coup.
* `studio` — camera, lumieres et reglages de rendu de l'auteur. Sans objet ici :
  nos planches se rendent a la camera du JEU, importee du niveau.
* `paths` — les chemins de SON depot. On les detourne vers un dossier temporaire.

⚠️ Les deux `sample_material()` du pylone et le `braided_material()` du flexible
n'appellent pas `make_materials()` : ils construisent leur materiau a la main a
partir de la planche. On leur rend donc aussi `load_pixels`, `resample`, `rgba`
et `save_map`, en versions creuses — leur produit est un materiau plat au bon
nom, et l'image de 1x1 pixel qu'ils creent est purgee avant l'export.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import bpy
import numpy as np

#: Les neuf familles de l'auteur, et le nom exact de leur slot. Identique dans
#: les trois livraisons (`materials.MATERIAL_NAMES`).
MATERIAL_NAMES = {
    'armor': '01 | Anthracite blinde',
    'panel': '02 | Acier gris use',
    'edge': '03 | Tranches acier brosse',
    'dark': '04 | Cavites graphite',
    'hose': '05 | Conduites noires',
    'magenta': '06 | Energie magenta',
    'hot': '07 | Coeur plasma',
    'red': '08 | Balises rouges',
    'bronze': '09 | Vis et raccords',
}

SAMPLE_BOUNDS = {
    'armor': (1304, 779, 1319, 792), 'panel': (1390, 779, 1404, 792),
    'edge': (1390, 838, 1404, 850), 'energy': (1304, 838, 1319, 850),
    'carbon': (1470, 779, 1484, 792), 'pipe': (1470, 838, 1484, 850),
}


def _materials_module(tmp: Path) -> types.ModuleType:
    mod = types.ModuleType('materials')
    mod.SOURCE = Path('planche technique (non versionnee)')
    mod.SAMPLE_BOUNDS = SAMPLE_BOUNDS
    mod.MATERIAL_NAMES = MATERIAL_NAMES
    mod.CELL_SIZE = 1024

    def make_materials():
        out = {}
        for family, name in MATERIAL_NAMES.items():
            mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
            mat.use_nodes = True
            out[family] = mat
        return out

    def load_pixels(path):
        return np.zeros((1024, 1536, 4), dtype=np.float32)

    def resample(pixels, size):
        return np.zeros((size, size, 4), dtype=np.float32)

    def rgba(rgb):
        return np.concatenate((rgb, np.ones((*rgb.shape[:2], 1))), axis=2)

    def save_map(name, pixels, non_color=False):
        image = bpy.data.images.get(name) or bpy.data.images.new(name, 1, 1)
        return image

    def map_surface(obj):
        return None

    def prepare_atlases():
        return {}

    for fn in (make_materials, load_pixels, resample, rgba, save_map,
               map_surface, prepare_atlases):
        setattr(mod, fn.__name__, fn)
    return mod


def _studio_module() -> types.ModuleType:
    mod = types.ModuleType('studio')
    mod.setup = lambda scene: None
    return mod


def _paths_module(tmp: Path, asset_collection: str,
                  module_collection: str | None) -> types.ModuleType:
    mod = types.ModuleType('paths')
    tmp.mkdir(parents=True, exist_ok=True)
    mod.VERSION = tmp
    mod.ASSETS = tmp / 'assets'
    mod.BLEND = tmp / 'forge.blend'
    mod.GLB = tmp / 'forge.glb'
    mod.STRAIGHT_GLB = tmp / 'straight.glb'
    mod.BENT_GLB = tmp / 'bent.glb'
    mod.MODULES = tmp / 'modules'
    mod.PREVIEWS = tmp / 'previews'
    mod.REPORTS = tmp / 'reports'
    mod.WORK = tmp / 'work'
    mod.ASSET_COLLECTION = asset_collection
    if module_collection:
        mod.MODULE_COLLECTION = module_collection
    for directory in (mod.ASSETS, mod.MODULES, mod.PREVIEWS, mod.REPORTS, mod.WORK):
        directory.mkdir(parents=True, exist_ok=True)
    return mod


def install(geometry, animation_source: Path, tmp: Path,
            asset_collection: str, module_collection: str | None) -> None:
    """Pose les cinq modules dans `sys.modules` avant d'executer le `build.py`."""
    sys.modules['geometry'] = geometry
    sys.modules['materials'] = _materials_module(tmp)
    sys.modules['studio'] = _studio_module()
    sys.modules['paths'] = _paths_module(tmp, asset_collection, module_collection)
    animation = types.ModuleType('animation')
    animation.__file__ = str(animation_source)
    code = compile(animation_source.read_text(encoding='utf-8'),
                   str(animation_source), 'exec')
    exec(code, animation.__dict__)
    sys.modules['animation'] = animation
