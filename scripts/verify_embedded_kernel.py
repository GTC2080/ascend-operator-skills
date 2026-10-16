#!/usr/bin/env python3
"""Read-only ELF64 little-endian audit for one Ascend C generated layout.

Compares fresh/staged/direct/registry resources. This does not establish source
provenance, host tiling deployment, runtime route, precision or safety.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys


def sha(data):
    return hashlib.sha256(data).hexdigest()


def embedded_payloads(path):
    data = Path(path).read_bytes()

    def read(offset, size):
        if offset < 0 or size < 0 or offset + size > len(data):
            raise ValueError('ELF range outside file')
        return data[offset:offset + size]

    if len(data) < 64 or data[:6] != b'\x7fELF\x02\x01':
        raise ValueError('expected ELF64 little-endian library')
    section_offset = struct.unpack_from('<Q', data, 40)[0]
    section_size, section_count = struct.unpack_from('<HH', data, 58)
    if section_size != 64 or section_count == 0:
        raise ValueError('unsupported ELF section table/extended indexing')
    table = read(section_offset, section_size * section_count)
    sections = [struct.unpack_from('<IIQQQQIIQQ', table, i * 64) for i in range(section_count)]
    symbols = {}
    for section in sections:
        if section[1] not in (2, 11):
            continue
        if section[9] != 24 or section[5] % 24 or section[6] >= len(sections):
            raise ValueError('invalid ELF symbol table')
        strings_section = sections[section[6]]
        if strings_section[1] != 3:
            raise ValueError('symbol table does not link a string table')
        strings = read(strings_section[4], strings_section[5])
        entries = read(section[4], section[5])
        for offset in range(0, len(entries), 24):
            name_index, _, _, index, value, _ = struct.unpack_from('<IBBHQQ', entries, offset)
            end = strings.find(b'\0', name_index)
            if name_index >= len(strings) or end < 0:
                raise ValueError('invalid ELF symbol name')
            raw_name = strings[name_index:end]
            if not raw_name.startswith(b'_binary_'):
                continue
            name = raw_name.decode('ascii')
            item = (index, value)
            if name in symbols and symbols[name] != item:
                raise ValueError('ambiguous embedded resource symbol: ' + name)
            symbols[name] = item
    payloads = {}
    for name, (index, value) in symbols.items():
        if not name.endswith('_start'):
            continue
        end_symbol = symbols.get(name[:-6] + '_end')
        if end_symbol is None:
            raise ValueError('missing embedded resource end: ' + name)
        end_index, end = end_symbol
        if index >= len(sections) or index == 0 or end_index not in (index, 0xfff1):
            raise ValueError('unsupported embedded resource section')
        section = sections[index]
        if section[1] == 8:
            raise ValueError('embedded resource in NOBITS section')
        offset = section[4] + value - section[3]
        size = end - value
        if size < 0 or offset < section[4] or offset + size > section[4] + section[5]:
            raise ValueError('payload outside ELF section')
        payloads[name[:-6]] = {'bytes': size, 'sha256': sha(read(offset, size))}
    if not payloads:
        raise ValueError('no supported embedded resource symbols')
    return sha(data), payloads


def verify(build, vendor, kernel_routes=()):
    if not re.fullmatch(r'[A-Za-z0-9_-]+', vendor):
        raise ValueError('unsupported vendor name')
    build = Path(build).resolve(strict=True)
    library_sha, payloads = embedded_payloads(build / 'libcust_opapi.so')
    fresh = build / 'op_kernel/ascendc_kernels/binary'
    staged = build / ('tmp/vendors/' + vendor + '/op_impl/ai_core/tbe/kernel')
    if not fresh.is_dir() or not fresh.resolve().is_relative_to(build):
        raise ValueError('missing or external fresh kernel directory')
    if not staged.is_dir() or not staged.resolve().is_relative_to(build):
        raise ValueError('missing or external staged kernel directory')
    files = sorted(p for p in fresh.rglob('*') if p.is_file() and p.suffix in ('.o', '.json')
                   and 'library' not in p.relative_to(fresh).parts)
    if not any(p.suffix == '.o' for p in files):
        raise ValueError('no fresh kernel objects found')
    rows, flattened_seen = [], set()
    consistent = True
    for path in files:
        relative = path.relative_to(fresh)
        old = staged / relative
        if path.is_symlink() or old.is_symlink() or not old.resolve().is_relative_to(build):
            raise ValueError('unsupported symlink/external resource')
        flattened = relative.as_posix().replace('/', '_').replace('-', '_').replace('.', '_')
        if flattened in flattened_seen:
            raise ValueError('resource symbol-name collision')
        flattened_seen.add(flattened)
        expected = sha(path.read_bytes())
        staged_sha = sha(old.read_bytes()) if old.is_file() else None
        row = {'file': relative.as_posix(), 'fresh_sha256': expected, 'staged_sha256': staged_sha,
               'staged_matches_fresh': staged_sha == expected, 'embedded': {}}
        for kind, prefix in [('direct', '_binary_'),
                             ('registry', '_binary_' + vendor + '_op_impl_ai_core_tbe_kernel_')]:
            payload = payloads.get(prefix + flattened)
            if payload is not None:
                row['embedded'][kind] = dict(payload, matches_fresh=payload['sha256'] == expected,
                                            matches_staged=payload['sha256'] == staged_sha)
                consistent &= payload['sha256'] == expected
        required = set(kernel_routes) if 'config' not in relative.parts else ({'registry'} if kernel_routes else set())
        missing = sorted(required - set(row['embedded']))
        row['missing_expected_routes'] = missing
        consistent &= bool(row['embedded']) and not missing and staged_sha == expected
        rows.append(row)
    return {'build_dir': str(build), 'library_sha256': library_sha,
            'all_packaging_matches_fresh': bool(consistent), 'expected_kernel_routes': list(kernel_routes),
            'artifacts': rows, 'scope': 'packaging consistency only; no runtime or host tiling proof'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build_dirs', nargs='+', type=Path)
    parser.add_argument('--vendor', default='custom')
    parser.add_argument('--require-kernel-routes', nargs='+', choices=('direct', 'registry'), default=())
    args = parser.parse_args()
    try:
        reports = [verify(build, args.vendor, args.require_kernel_routes) for build in args.build_dirs]
    except (OSError, ValueError, UnicodeError, struct.error) as error:
        print(json.dumps({'error': str(error)}), file=sys.stderr)
        return 2
    print(json.dumps(reports, indent=2))
    return 0 if all(r['all_packaging_matches_fresh'] for r in reports) else 1


if __name__ == '__main__':
    raise SystemExit(main())
