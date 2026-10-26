"""Shared inputs; imported by the platform PyInstaller specs."""
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, copy_metadata


def inputs(root):
    notices = root / 'build/release-licenses'
    if not (notices / 'BUILD-ENVIRONMENT.json').exists():
        raise RuntimeError('Run packaging/collect_licenses.py before building')
    return ([(str(root / 'src/ui/legal'), 'ui/legal'),
             (str(root / 'src/ui/assets'), 'ui/assets'),
             (str(notices), 'licenses')]
            + collect_data_files('mcp') + copy_metadata('mcp', recursive=True))
