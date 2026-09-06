"""Package a verified, standalone version, including its editable sources."""
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

VERSION = Path(__file__).resolve().parent.parent
manifest = json.loads((VERSION / 'manifest.json').read_text())
required = [manifest[key] for key in ['generator','parameters','exporter','verifier','blender_file',
                                     'glb_file','asset_catalog','reference']]
required += ['README.md','assets/SOURCES.md','reports/verification.json',
             'reports/portability.json','reports/standalone.json','previews/spectre9_d_motion.mp4']
for relative in required:
    if not (VERSION / relative).is_file() or (VERSION / relative).stat().st_size == 0:
        raise FileNotFoundError(f'Missing or empty delivery file: {relative}')
verification = json.loads((VERSION / 'reports/verification.json').read_text())
if verification.get('glb_reimport') != 'OK':
    raise ValueError('Run scripts/verify.py before packaging.')
for relative, expected in verification['verified_file_sha256'].items():
    if hashlib.sha256((VERSION / relative).read_bytes()).hexdigest() != expected:
        raise ValueError(f'Changed since verification: {relative}; rerun scripts/verify.py.')
if manifest['external_dependencies']:
    raise ValueError('This portable pack must include its dependencies.')
files = []
for path in sorted(VERSION.rglob('*')):
    relative = path.relative_to(VERSION)
    if not path.is_file() or {'work','__pycache__'}.intersection(relative.parts):
        continue
    if path.name.endswith(('.blend1','.pyc',':Zone.Identifier')) or relative.as_posix() == 'reports/checksums.json':
        continue
    files.append(path)
inventory = {p.relative_to(VERSION).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
checksum_file = VERSION / 'reports/checksums.json'
checksum_file.write_text(json.dumps(inventory, indent=2, ensure_ascii=False) + '\n')
files.append(checksum_file)
releases = VERSION.parent / 'releases'
releases.mkdir(exist_ok=True)
archive = releases / f"{manifest['object']}_{manifest['version']}.zip"
temporary = archive.with_suffix('.zip.tmp')
with ZipFile(temporary, 'w', ZIP_DEFLATED) as pack:
    for path in files:
        name = Path(manifest['object']) / manifest['version'] / path.relative_to(VERSION)
        pack.write(path, name.as_posix())
with ZipFile(temporary) as pack:
    if pack.testzip() is not None:
        raise RuntimeError('Archive CRC validation failed')
temporary.replace(archive)
print(f'{archive}: {len(files)} files, {archive.stat().st_size / 1024**2:.1f} MiB; verified ZIP')
