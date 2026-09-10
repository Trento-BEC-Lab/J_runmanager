#!/usr/bin/env python3
"""Manage dependencies; editable projects are deliberately managed by the user."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
PREFIX = Path.home() / '.local/share/mamba/envs/labscript_test_v1'
MAMBA = '/usr/local/bin/micromamba'
PARTICIPANTS = ('J_labscript', 'J_labscript-devices', 'J_labscript-utils',
                'J_blacs', 'J_runmanager', 'J_runviewer')
SHARED = ROOT.parent / 'env'
LOCK = SHARED / 'conda-linux-64.lock'
PIP = SHARED / 'pip-requirements.txt'


def run(args, capture=False):
    return subprocess.run([str(a) for a in args], check=True, text=True,
                          stdout=subprocess.PIPE if capture else None).stdout


def export():
    return run([MAMBA, 'env', 'export', '-p', PREFIX, '--explicit'], True)


def urls(text):
    if '@EXPLICIT' not in text.splitlines():
        raise ValueError('Missing @EXPLICIT header in conda lock')
    return {s.strip() for s in text.splitlines() if s.startswith(('https://', 'http://'))}


def inventory():
    code = '''import importlib.metadata as m, json
out = []
for d in m.distributions():
    direct = json.loads(d.read_text('direct_url.json') or '{}')
    out.append(dict(name=d.metadata['Name'], version=d.version,
        pip=(d.read_text('INSTALLER') or '').strip() == 'pip',
        editable=direct.get('dir_info', {}).get('editable', False), direct=direct))
print(json.dumps(out))'''
    return {normal(d['name']): d for d in json.loads(run([PREFIX / 'bin/python', '-c', code], True))}


def normal(name):
    return re.sub(r'[-_.]+', '-', name).lower()


def requirements(path=None):
    result = {}
    for line in (path or PIP).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        match = re.fullmatch(r'([A-Za-z0-9_.-]+)==([^\s;]+)', line)
        if not match:
            raise ValueError(f'Expected a pinned name==version requirement: {line}')
        name, version = match.groups()
        result[normal(name)] = version
    return result


def write_snapshot(directory, conda, pip):
    directory.mkdir(parents=True, exist_ok=True)
    for name, contents in [('conda-linux-64.lock', conda), ('pip-requirements.txt', pip)]:
        with tempfile.NamedTemporaryFile(mode='w', dir=directory, delete=False) as f:
            temporary = Path(f.name)
            f.write(contents)
        try:
            temporary.replace(directory / name)
        finally:
            temporary.unlink(missing_ok=True)


def distribute():
    conda, pip = LOCK.read_text(), PIP.read_text()
    for name in PARTICIPANTS:
        repository = ROOT.parent / name
        if repository.is_dir():
            write_snapshot(repository / 'env', conda, pip)
            print(f'Copied snapshot to {name}/env/', flush=True)


def local_to_shared():
    local = ROOT / 'env'
    conda = (local / LOCK.name).read_text()
    urls(conda)
    requirements(local / PIP.name)
    pip = (local / PIP.name).read_text()
    write_snapshot(SHARED, conda, pip)
    print(f'Updated shared snapshot from {ROOT.name}: {SHARED}', flush=True)
    distribute()


def ensure_shared():
    if not LOCK.exists() and not PIP.exists():
        print('Shared snapshot missing; initializing from this repository.', flush=True)
        local_to_shared()
    elif not LOCK.is_file() or not PIP.is_file():
        raise ValueError('Shared snapshot is incomplete. Run Env: Copy local snapshot to shared to restore it.')


def pip_packages(items):
    return {n: d['version'] for n, d in items.items() if d['pip'] and not d['editable']}


def sync_pip(wanted):
    items = inventory()
    collisions = [n for n in wanted if n in items and (items[n]['editable'] or not items[n]['pip'])]
    if collisions:
        raise ValueError('Pip requirements overlap editable or conda packages: ' + ', '.join(collisions))
    current = pip_packages(items)
    extra = sorted(current.keys() - wanted.keys())
    changed = [f'{n}=={v}' for n, v in wanted.items() if current.get(n) != v]
    if extra:
        run([PREFIX / 'bin/python', '-m', 'pip', 'uninstall', '-y', *extra])
    if changed:
        run([PREFIX / 'bin/python', '-m', 'pip', 'install', '--no-deps', *changed])
    if pip_packages(inventory()) != wanted:
        raise ValueError('Pip inventory does not match snapshot')


def health():
    print('Checking dependency metadata (including manually installed projects):', flush=True)
    result = subprocess.run([str(PREFIX / 'bin/python'), '-m', 'pip', 'check'])
    if result.returncode:
        print('WARNING: pip check reported metadata issues. These are advisory; '
              'dependency inventories were synchronized successfully.', flush=True)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['snapshot', 'sync', 'rebuild', 'local-to-shared'])
    args = parser.parse_args()
    if args.action == 'local-to-shared':
        local_to_shared()
        return 0
    if args.action == 'snapshot':
        items = inventory()
        direct = [n for n, d in items.items() if d['pip'] and not d['editable'] and d['direct']]
        if direct:
            raise ValueError('Cannot represent direct-URL/local non-editable packages as version pins: ' + ', '.join(direct))
        conda = export()
        urls(conda)
        pip = '# Pip dependencies only; editable projects are excluded.\n' + ''.join(
            f'{n}=={v}\n' for n, v in sorted(pip_packages(items).items()))
        write_snapshot(SHARED, conda, pip)
        distribute()
        print('Saved conda lock and pip requirements. Excluded editable projects:',
              ', '.join(n for n, d in items.items() if d['editable']))
        return 0

    ensure_shared()
    print(f'Using shared snapshot: {SHARED}', flush=True)
    desired_conda = urls(LOCK.read_text())
    wanted = requirements()
    if args.action == 'sync':
        current = urls(export())
        if current != desired_conda:
            print(f'Conda differs: {len(desired_conda - current)} missing/changed, '
                  f'{len(current - desired_conda)} extra/changed packages.')
            print('Run Env: Rebuild from lock. Sync has changed nothing; editable installs are preserved.')
            return 2
        before = {n: d for n, d in inventory().items() if d['editable']}
        sync_pip(wanted)
        after = {n: d for n, d in inventory().items() if d['editable']}
        if before != after:
            raise ValueError('Editable registrations changed unexpectedly')
    else:
        print(f'Rebuild will remove {PREFIX}, including editable registrations.\n'
              'Source checkouts remain intact. Install your chosen editable projects manually afterward.')
        if input('Type rebuild to continue: ').strip() != 'rebuild':
            print('Cancelled.')
            return 1
        # Use a disposable prefix for prefetching: create must never target the
        # working prefix before the explicit removal step.
        with tempfile.TemporaryDirectory(prefix='jblacs-rebuild-') as staging:
            run([MAMBA, 'create', '-p', Path(staging) / 'prefetch',
                 '-f', LOCK, '--download-only', '-y'])
            if PREFIX.exists():
                run([MAMBA, 'remove', '-p', PREFIX, '--all', '-y'])
            run([MAMBA, 'create', '-p', PREFIX, '-f', LOCK, '-y'])
            sync_pip(wanted)
    if urls(export()) != desired_conda:
        raise ValueError('Conda inventory does not match snapshot')
    print('Dependency inventories match snapshot; editable projects excluded.', flush=True)
    health()
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        sys.exit(f'ERROR: {exc}')
