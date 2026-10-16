#!/usr/bin/env python3
"""Hash/verify an exact source-only tree; standard library, no code execution."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys


def relative_name(name):
    p = PurePosixPath(name)
    if (not name or not p.parts or p.is_absolute() or '..' in p.parts or '\\' in name
            or ':' in p.parts[0] or p.as_posix() != name or name == '.'):
        raise ValueError('unsafe or nonportable manifest path: ' + repr(name))
    return p


def snapshot(root):
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError('source root must be a directory')
    files = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError('symlink in source tree: ' + str(path.relative_to(root)))
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError('nonregular source entry: ' + str(path.relative_to(root)))
        name = path.relative_to(root).as_posix()
        relative_name(name)
        before = path.stat()
        h = hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                h.update(chunk)
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError('source changed during hashing: ' + name)
        files[name] = {'bytes': after.st_size, 'sha256': h.hexdigest()}
    if not files:
        raise ValueError('empty source tree')
    return {'schema': 1, 'files': files}


def create(root, output):
    root = Path(root).resolve(strict=True)
    output = Path(output)
    if output.resolve().is_relative_to(root):
        raise ValueError('manifest output must be outside source root')
    document = snapshot(root)
    text = json.dumps(document, indent=2, sort_keys=True) + '\n'
    with output.open('x', encoding='utf-8') as stream:
        stream.write(text)
    return {'created': True, 'files': len(document['files'])}


def verify(root, manifest):
    expected = json.loads(Path(manifest).read_text(encoding='utf-8'))
    if expected.get('schema') != 1 or not isinstance(expected.get('files'), dict) or not expected['files']:
        raise ValueError('unsupported or empty source manifest')
    for name, record in expected['files'].items():
        relative_name(name)
        if (not isinstance(record, dict) or set(record) != {'bytes', 'sha256'}
                or type(record['bytes']) is not int or record['bytes'] < 0
                or not isinstance(record['sha256'], str) or len(record['sha256']) != 64
                or any(c not in '0123456789abcdef' for c in record['sha256'])):
            raise ValueError('invalid source record: ' + name)
    actual = snapshot(root)['files']
    missing = sorted(set(expected['files']) - set(actual))
    extra = sorted(set(actual) - set(expected['files']))
    changed = sorted(n for n in set(actual) & set(expected['files']) if actual[n] != expected['files'][n])
    return {'matches': not (missing or extra or changed), 'missing': missing,
            'extra': extra, 'changed': changed, 'files': len(actual)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('create', 'verify'))
    parser.add_argument('root', type=Path)
    parser.add_argument('manifest', type=Path)
    args = parser.parse_args()
    try:
        report = create(args.root, args.manifest) if args.action == 'create' else verify(args.root, args.manifest)
    except (OSError, ValueError, TypeError, AttributeError) as error:
        print(json.dumps({'error': str(error)}), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return 0 if report.get('created') or report.get('matches') else 1


if __name__ == '__main__':
    raise SystemExit(main())
