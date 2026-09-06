"""All resources belong to this version; no dependency on the working directory."""
from pathlib import Path

VERSION = Path(__file__).resolve().parent.parent
ASSETS = VERSION / 'assets'
BLENDER = VERSION / 'blender'
EXPORTS = VERSION / 'exports'
PREVIEWS = VERSION / 'previews'
REPORTS = VERSION / 'reports'
WORK = VERSION / 'work'
for folder in (BLENDER, EXPORTS, PREVIEWS, REPORTS, WORK):
    folder.mkdir(parents=True, exist_ok=True)
