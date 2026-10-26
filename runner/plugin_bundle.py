"""Build a clean, reproducible native plugin. No credentials or models involved."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import re
from pathlib import Path, PurePosixPath
import sys
import zipfile

if __package__ in {None, ''}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runner.filesystem import REPO_ROOT
from runner.distribution import _is_link

FIXED = (
    'plugin.json', '.codex-plugin/plugin.json', '.claude-plugin/plugin.json',
    '.claude-plugin/marketplace.json', '.agents/plugins/marketplace.json',
    'package.json', 'LICENSE', 'distribution/portable-suite.json',
    'distribution/deepseek/index.mjs', 'assets/plugin/icon.svg', 'docs/plugins.md',
    'skills/book-genesis/scripts/data/iana-timezones.zip',
    'skills/book-genesis/scripts/data/tzdata-LICENSE',
    'skills/book-genesis/scripts/data/tzdata-licenses-LICENSE_APACHE',
    'cordis.patch.yml', 'distribution/plugin-files.json',
)
RECEIPT = 'bundle-receipt.json'


def _json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def _check_path(path: Path, root: Path) -> None:
    current = path
    while True:
        if _is_link(current):
            raise ValueError(f'Linked paths are not packaged: {path}')
        if current == root:
            break
        if current == current.parent:
            raise ValueError(f'Path outside source root: {path}')
        current = current.parent
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f'Path outside source root: {path}')


def _payload(repo: Path) -> dict[str, bytes]:
    _check_path(repo / 'distribution/plugin-files.json', repo)
    entries = _json(repo / 'distribution/plugin-files.json')
    if (not isinstance(entries, list) or not entries
            or not all(isinstance(name, str) for name in entries)
            or len(entries) != len(set(entries))):
        raise ValueError('Invalid plugin file allowlist')
    for name in entries:
        relative = PurePosixPath(name)
        if not name or '\\' in name or ':' in name or relative.is_absolute() or '..' in relative.parts or relative.as_posix() != name:
            raise ValueError(f'Invalid plugin file path: {name}')
    if not set(FIXED).issubset(entries):
        raise ValueError('Plugin file allowlist omits required resources')
    # Each resource is explicitly reviewed, including extensionless licenses and data.
    # New or untracked notes inside skill/agent folders are not silently distributed.
    files = [repo / name for name in entries]
    for path in files:
        _check_path(path, repo)
    names = _json(repo / 'distribution/portable-suite.json')['skills']
    for name in names:
        if not isinstance(name, str) or not name or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in name):
            raise ValueError('Invalid skill directory name')
    result = {}
    for path in files:
        _check_path(path, repo)
        result[path.relative_to(repo).as_posix()] = path.read_bytes()
    for name in names:
        if f'skills/{name}/SKILL.md' not in result:
            raise ValueError(f'Missing skill: {name}')
    versions = {_json(repo / p)['version'] for p in ('plugin.json', '.codex-plugin/plugin.json', '.claude-plugin/plugin.json', 'package.json')}
    if len(versions) != 1:
        raise ValueError('Plugin manifest versions disagree')
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?', next(iter(versions))):
        raise ValueError('Invalid plugin version')
    return result


def build_bundle(destination: Path, repo_root: Path = REPO_ROOT) -> dict[str, str]:
    destination = Path(destination).absolute()
    # Validate all input before creating anything. Existing builds are immutable.
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f'Choose a new build directory: {destination}')
    for parent in destination.parents:
        if _is_link(parent):
            raise ValueError('Build destination must not pass through a linked directory')
    payload = _payload(Path(repo_root).absolute())
    version = json.loads(payload['plugin.json'])['version']
    receipt = {'schema_version': 1, 'name': 'book-genesis', 'version': version,
               'files': {name: sha256(data).hexdigest() for name, data in sorted(payload.items())}}
    payload[RECEIPT] = (json.dumps(receipt, indent=2, sort_keys=True) + '\n').encode()
    destination.mkdir(parents=True, exist_ok=False)
    plugin = destination / 'book-genesis'
    for name, data in sorted(payload.items()):
        path = plugin / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    archive_path = destination / f'book-genesis-{version}.zip'
    with zipfile.ZipFile(archive_path, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    return {'plugin': str(plugin), 'archive': str(archive_path), 'version': version,
            'archive_sha256': sha256(archive_path.read_bytes()).hexdigest()}


def verify_bundle(root: Path) -> dict[str, object]:
    root = Path(root).absolute()
    errors = []
    try:
        receipt = _json(root / RECEIPT)
        if receipt.get('schema_version') != 1 or not isinstance(receipt.get('files'), dict):
            raise ValueError('Invalid receipt schema')
        for name, digest in receipt['files'].items():
            parts = PurePosixPath(name)
            if not name or '\\' in name or ':' in name or parts.is_absolute() or '..' in parts.parts or parts.as_posix() != name:
                errors.append(f'unsafe receipt path: {name}')
                continue
            path = root / name
            _check_path(path, root)
            if not path.is_file():
                errors.append(f'missing: {name}')
            elif sha256(path.read_bytes()).hexdigest() != digest:
                errors.append(f'changed: {name}')
        for path in root.rglob('*'):
            _check_path(path, root)
            if path.is_file():
                name = path.relative_to(root).as_posix()
                # Running Python helpers creates caches; they are never release inputs.
                if '__pycache__' not in path.parts and name != RECEIPT and name not in receipt['files']:
                    errors.append(f'unexpected: {name}')
    except (OSError, ValueError, TypeError, KeyError) as exc:
        errors.append(str(exc))
    return {'ok': not errors, 'errors': errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    build = sub.add_parser('build')
    build.add_argument('--output', type=Path, required=True)
    verify = sub.add_parser('verify')
    verify.add_argument('path', type=Path)
    args = parser.parse_args()
    try:
        result = build_bundle(args.output) if args.command == 'build' else verify_bundle(args.path)
    except (OSError, ValueError, KeyError) as exc:
        print(f'Plugin build failed: {exc}', file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0 if result.get('ok', True) else 1


if __name__ == '__main__':
    raise SystemExit(main())
