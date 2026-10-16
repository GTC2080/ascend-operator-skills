"""Synthetic ELF/resources, not a device build or runtime-validation claim."""
import hashlib
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import verify_embedded_kernel as checker


def synthetic_elf(payloads):
    strings = bytearray(b'\0')
    symbols = bytearray(24)
    resource_data = bytearray()
    for name, raw in sorted(payloads.items()):
        start = len(resource_data)
        resource_data.extend(raw)
        for suffix, value in (('_start', start), ('_end', len(resource_data))):
            name_index = len(strings)
            strings.extend((name + suffix).encode() + b'\0')
            symbols.extend(struct.pack('<IBBHQQ', name_index, 0x10, 0, 1, value, 0))
    data = bytearray(64)
    data[:16] = b'\x7fELF\x02\x01\x01' + b'\0' * 9
    resource_offset = len(data); data.extend(resource_data)
    string_offset = len(data); data.extend(strings)
    symbol_offset = len(data); data.extend(symbols)
    section_offset = len(data)
    data.extend(b'\0' * 64)
    data.extend(struct.pack('<IIQQQQIIQQ', 0, 1, 0, 0, resource_offset, len(resource_data), 0, 0, 1, 0))
    data.extend(struct.pack('<IIQQQQIIQQ', 0, 3, 0, 0, string_offset, len(strings), 0, 0, 1, 0))
    data.extend(struct.pack('<IIQQQQIIQQ', 0, 2, 0, 0, symbol_offset, len(symbols), 2, 1, 8, 24))
    struct.pack_into('<HHIQQQIHHHHHH', data, 16, 3, 183, 1, 0, 0, section_offset, 0, 64, 0, 0, 64, 4, 0)
    return bytes(data)


class EmbeddedKernelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.build = Path(self.temp.name)
        self.fresh = self.build / 'op_kernel/ascendc_kernels/binary'
        self.staged = self.build / 'tmp/vendors/custom/op_impl/ai_core/tbe/kernel'
        self.payloads = {}
        self.add_resource('ascend910b/op/kernel.o', b'current synthetic kernel', ('direct', 'registry'))
        self.add_resource('config/ascend910b/binary_info_config.json', b'{}', ('registry',))
        self.write_library()

    def add_resource(self, name, raw, routes):
        for root in (self.fresh, self.staged):
            path = root / name; path.parent.mkdir(parents=True, exist_ok=True);path.write_bytes(raw)
        name = name.replace('/', '_').replace('-', '_').replace('.', '_')
        for kind in routes:
            prefix = '_binary_' if kind == 'direct' else '_binary_custom_op_impl_ai_core_tbe_kernel_'
            self.payloads[prefix + name] = raw

    def write_library(self):
        (self.build / 'libcust_opapi.so').write_bytes(synthetic_elf(self.payloads))

    def report(self):
        return checker.verify(self.build, 'custom', ('direct', 'registry'))

    def test_real_parser_and_matching_routes(self):
        self.assertTrue(self.report()['all_packaging_matches_fresh'])
        _, payloads = checker.embedded_payloads(self.build / 'libcust_opapi.so')
        for name, raw in self.payloads.items():
            self.assertEqual(payloads[name], {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})

    def test_stale_staged_fails(self):
        (self.staged / 'ascend910b/op/kernel.o').write_bytes(b'old')
        self.assertFalse(self.report()['all_packaging_matches_fresh'])

    def test_stale_embedded_fails(self):
        self.payloads['_binary_ascend910b_op_kernel_o'] = b'old'
        self.write_library()
        self.assertFalse(self.report()['all_packaging_matches_fresh'])

    def test_missing_expected_route_fails(self):
        del self.payloads['_binary_custom_op_impl_ai_core_tbe_kernel_ascend910b_op_kernel_o']
        self.write_library()
        d = self.report()
        self.assertFalse(d['all_packaging_matches_fresh'])
        self.assertEqual(next(x for x in d['artifacts'] if x['file'].endswith('.o'))['missing_expected_routes'], ['registry'])

    def test_missing_staged_fails(self):
        (self.staged / 'ascend910b/op/kernel.o').unlink()
        self.assertFalse(self.report()['all_packaging_matches_fresh'])

    def test_no_device_object_rejected(self):
        (self.fresh / 'ascend910b/op/kernel.o').unlink()
        with self.assertRaisesRegex(ValueError, 'no fresh kernel'):
            self.report()

    def test_truncated_elf_rejected(self):
        p = self.build / 'libcust_opapi.so';p.write_bytes(p.read_bytes()[:70])
        with self.assertRaisesRegex(ValueError, 'outside file'):
            checker.embedded_payloads(p)

    def test_unsupported_format_rejected(self):
        p = self.build / 'libcust_opapi.so';p.write_bytes(b'not an ELF')
        with self.assertRaisesRegex(ValueError, 'ELF64'):
            checker.embedded_payloads(p)

    def test_vendor_traversal_rejected(self):
        with self.assertRaisesRegex(ValueError, 'vendor'):
            checker.verify(self.build, '../other')


if __name__ == '__main__':
    unittest.main()
