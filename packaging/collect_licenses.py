"""Collect installed notices and upstream notices absent from binary wheels.

Runs in the isolated CI build environment; failures stop the package build.
The manifest is a superset (build tools included), not a claim of static linkage.
"""
import hashlib
import importlib.metadata as metadata
import io
import json
from pathlib import Path
import re
import shutil
import sys
import tarfile
import urllib.request
import zipfile

root = Path(__file__).resolve().parents[1]
out = root / 'build/release-licenses'
out.mkdir(parents=True, exist_ok=True)
records, downloads = [], []


def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'FlipperRemote-release/0.2'})
    with urllib.request.urlopen(request, timeout=120) as response:
        data = response.read()
    downloads.append({'url': url, 'sha256': hashlib.sha256(data).hexdigest()})
    return data


def notice(name):
    lower = Path(name).name.lower()
    return (lower.startswith(('license', 'licence', 'copying', 'copyright', 'notice'))
            or lower == 'qt_attribution.json' or lower == 'reuse.toml')


def archive_notices(data, directory, zip_format=False):
    count = 0
    if zip_format:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = [(item.filename, archive.read(item)) for item in archive.infolist()
                       if not item.is_dir() and notice(item.filename)]
    else:
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:*') as archive:
            entries = [(item.name, archive.extractfile(item).read()) for item in archive
                       if item.isfile() and notice(item.name)]
    for name, content in entries:
        path = Path(name)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('Unsafe upstream archive path')
        dest = directory / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        count += 1
    if not count:
        raise RuntimeError(f'No upstream notices found for {directory.name}')


qt_version = metadata.version('PySide6-Essentials')
# The linked Qt Core/Gui/Widgets/Network/Svg plugins come from these modules.
for repo in ('qt/qtbase', 'qt/qtsvg', 'qt/qtimageformats', 'pyside/pyside-setup'):
    url = f'https://codeload.github.com/{repo}/tar.gz/refs/tags/v{qt_version}'
    archive_notices(fetch(url), out / repo.replace('/', '-'))

for distribution in sorted(metadata.distributions(), key=lambda d: d.metadata['Name'].lower()):
    name = distribution.metadata['Name']
    if name.lower() == 'flipper-zero-desktop-remote':
        continue
    directory = out / re.sub(r'[^A-Za-z0-9_.-]', '_', name)
    directory.mkdir(exist_ok=True)
    files = []
    for file in distribution.files or []:
        if notice(str(file)):
            source = Path(distribution.locate_file(file))
            if source.is_file():
                dest = directory / str(file).replace('../', '_')
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
                files.append(str(file))
    (directory / 'METADATA.txt').write_text(distribution.read_text('METADATA') or '', encoding='utf-8')
    # Some older wheels omit their license file; retain it from their exact sdist.
    if not files and name.lower().replace('_', '-') not in {'pyside6-essentials', 'shiboken6'}:
        info = json.loads(fetch(f'https://pypi.org/pypi/{name}/{distribution.version}/json'))
        sdists = [entry for entry in info['urls'] if entry['packagetype'] == 'sdist']
        if not sdists:
            raise RuntimeError(f'No license files or source distribution: {name}')
        source = sdists[0]
        data = fetch(source['url'])
        assert hashlib.sha256(data).hexdigest() == source['digests']['sha256']
        archive_notices(data, directory, source['filename'].endswith('.zip'))
    records.append({'name': name, 'version': distribution.version,
                    'license': distribution.metadata.get('License-Expression') or distribution.metadata.get('License'),
                    'project_urls': distribution.metadata.get_all('Project-URL', [])})

python_version = sys.version.split()[0]
(out / 'Python-LICENSE.txt').write_bytes(fetch(f'https://raw.githubusercontent.com/python/cpython/v{python_version}/LICENSE'))
for name in ('LICENSE', 'THIRD_PARTY_NOTICES.md'):
    shutil.copy2(root / name, out / name)
(out / 'BUILD-ENVIRONMENT.json').write_text(json.dumps({'python': sys.version, 'distributions': records, 'upstream_notices': downloads}, indent=2))
print(f'Collected notices for {len(records)} build-environment distributions and Qt sources')
